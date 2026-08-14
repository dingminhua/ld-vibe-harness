"""Directly scan current fact objects and return source-defined F0/F1/F2 projections."""

from __future__ import annotations

import base64
import hashlib
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

from ldvh.facts.candidate_discovery import discover_fact_candidates
from ldvh.facts.configuration_index import ConfigurationFactEntry, ConfigurationFactIndex
from ldvh.facts.contracts import ACTIVE_STATUSES, LAYOUTS
from ldvh.facts.identity import canonical_object_uid
from ldvh.facts.models import FactReference, StableFactReference, UIDFactReference
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import project_fact_schemas
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_candidate_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    FactCandidateRequest,
    parse_fact_candidate_request,
)
from ldvh.helper.operations.fact_operation_support import configuration_reading_boundaries, plain, reading_boundary
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection
from ldvh.time import utc_now_iso

OPERATION_KEY = "find-fact-object-candidates"
_INPUT_CONTRACT = source_reference("rule", "fact-model-foundation::11.5 事实对象候选发现输入字段")
_RESULT_CONTRACT = source_reference("rule", "fact-model-foundation::11.6 事实对象候选发现结果字段")
_IMPLEMENTATION_EVIDENCE = (
    source_reference("implementation", "code/ldvh/helper/operations/fact_candidate_operation.py"),
)
_INPUT_EXAMPLES = (
    {
        "summary": "按 Spark 标题进行 F2 文本筛选",
        "arguments_fragment": {
            "card_layer": "F2",
            "fact_type_keys": ["spark"],
            "text_match": {"text": "text", "field_paths": ["title"]},
        },
        "source_refs": (_INPUT_CONTRACT,),
        "composition_note": (
            "这是可组合输入片段，不是完整请求；调用者仍须加入当前实际 governed_project_id，"
            "并可按所选类型当前允许的 F2 字段替换 text 与 field_paths。"
        ),
    },
    {
        "summary": "按关系目标反向查询：找出所有引用指定对象的同类或异类事实",
        "arguments_fragment": {
            "card_layer": "F2",
            "fact_type_keys": ["spark", "workcase"],
            "relation_targets": [
                {"governed_project_id": "sample", "fact_type_key": "adr", "object_id": "adr-0001"}
            ],
        },
        "source_refs": (_INPUT_CONTRACT,),
        "composition_note": (
            "这是可组合输入片段，不是完整请求；调用者仍须加入当前实际 governed_project_id，"
            "并按实际目标替换 relation_targets 各项的 fact_type_key 与 object_id。"
            "relation_targets、relation_source_refs 和 relation_keys 分别支持以目标、来源和关系键反向查询。"
        ),
    },
)
_TYPE_SOURCES = {
    "spark": "specs/20-Spark-火花.md",
    "workcase": "specs/21-WorkCase-工作项.md",
    "adr": "specs/22-ADR-决策.md",
    "pitfall": "specs/23-Pitfall-踩坑经验.md",
    "study": "specs/24-Study-研究报告.md",
}
_RELATION_DEFINITION_LOCATORS = {
    "spark": "spark-fact-type::7. 外部资料、关系与处置",
    "workcase": "workcase-fact-type::8. 来源、外部资料与关系",
    "adr": "adr-fact-type::7. 形成边界、取舍说明与替代关系",
    "pitfall": "pitfall-fact-type::7. 形成边界、验证说明与替代关系",
    "study": "study-fact-type::7. 外部网址、研究边界、关系与时效",
}
_DEFAULT_STATUSES = {
    "spark": frozenset({"open"}),
    "workcase": ACTIVE_STATUSES,
    "adr": frozenset({"active"}),
    "pitfall": frozenset({"active"}),
    "study": frozenset({"active"}),
}
_F1_FIELDS = {
    "adr": ("object_uid", "object_id", "title", "decision_question", "decision", "applicability", "updated_at"),
    "workcase": (
        "object_uid",
        "object_id",
        "title",
        "status",
        "phase",
        "goal",
        "scope",
        "summary",
        "priority",
        "blocking_summary",
        "updated_at",
    ),
}
_WORKCASE_F2_CLOSED_FIELDS = (
    "object_uid",
    "object_id",
    "title",
    "status",
    "goal",
    "scope",
    "result_summary",
    "closure_outcome",
    "disposition_summary",
    "spark_suggestions",
    "updated_at",
)
_F2_FIELDS = {
    "spark": ("object_uid", "object_id", "title", "status", "priority", "updated_at"),
    "adr": (
        "object_uid",
        "object_id",
        "title",
        "status",
        "decision_question",
        "decision",
        "applicability",
        "updated_at",
    ),
    "pitfall": (
        "object_uid",
        "object_id",
        "title",
        "status",
        "symptoms",
        "trigger_conditions",
        "applicability",
        "validation_summary",
        "updated_at",
    ),
    "study": (
        "object_uid",
        "object_id",
        "title",
        "status",
        "research_question",
        "abstract",
        "research_intent",
        "recommendation_summary",
        "relations",
        "updated_at",
    ),
}
_EXCERPT_LIMIT = 512
_EDGE_REASON_ORDER = (
    "relation-key-filter",
    "fact-type-filter",
    "explicit-status-filter",
    "exact-ref-filter",
    "relation-target-filter",
    "locator-filter",
    "field-text-filter",
)


class CursorRejected(ValueError):
    pass


def _validated_request(request: CommonRequest, context: OperationExecutionContext) -> FactCandidateRequest:
    parsed = parse_fact_candidate_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_INPUT_CONTRACT,))
    return parsed.request


def _governance(domain: FactCandidateRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: object) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _stable_ref(project_id: str, fact_type_key: str, fields: dict[str, Any]) -> dict[str, str]:
    object_uid = fields.get("object_uid")
    if isinstance(object_uid, str):
        return {"object_uid": object_uid}
    return FactReference(project_id, fact_type_key, str(fields["object_id"])).to_json()


def _ref_sort_key(value: object) -> tuple[str, ...]:
    if isinstance(value, dict) and isinstance(value.get("object_uid"), str):
        return ("uid", str(value["object_uid"]))
    if isinstance(value, dict):
        return (
            "legacy",
            str(value.get("governed_project_id", "")),
            str(value.get("fact_type_key", "")),
            str(value.get("object_id", "")),
        )
    return ("legacy", "", "", "")


def _problem_item(
    project_id: str,
    fact_type_key: str,
    object_id: str,
    read: FactReadResult,
) -> dict[str, object]:
    item: dict[str, object] = {
        "canonical_path": read.canonical_path,
        "check_status": read.check_status,
        "issues": [
            {"category": issue.category, "field_path": issue.field_path, "summary": issue.summary}
            for issue in read.issues
        ],
    }
    if read.fields is None or "object_uid" not in read.fields:
        item["fact_ref"] = FactReference(project_id, fact_type_key, object_id).to_json()
    else:
        object_uid = canonical_object_uid(read.fields.get("object_uid"))
        if object_uid is None:
            item["fact_type_key"] = fact_type_key
        else:
            item["fact_ref"] = UIDFactReference(object_uid).to_json()
    return item


def _reference_identity(value: StableFactReference) -> tuple[object, ...]:
    if isinstance(value, UIDFactReference):
        return ("uid", value.object_uid)
    return ("legacy", value.governed_project_id, value.fact_type_key, value.object_id)


def _object_identity(project_id: str, fact_type_key: str, fields: dict[str, Any]) -> tuple[object, ...]:
    object_uid = fields.get("object_uid")
    if isinstance(object_uid, str):
        return ("uid", object_uid)
    return ("legacy", project_id, fact_type_key, fields.get("object_id"))


def _references(value: tuple[StableFactReference, ...]) -> set[tuple[object, ...]]:
    return {_reference_identity(item) for item in value}


def _relations(
    fields: dict[str, Any],
    configuration_index: ConfigurationFactIndex | None = None,
) -> set[tuple[object, ...]]:
    result: set[tuple[object, ...]] = set()
    raw = fields.get("relations")
    if not isinstance(raw, list):
        return result
    for relation in raw:
        if not isinstance(relation, dict) or not isinstance(relation.get("target"), dict):
            continue
        target = relation["target"]
        reference: StableFactReference | None = None
        if isinstance(target.get("object_uid"), str):
            reference = UIDFactReference(str(target["object_uid"]))
        elif all(
            isinstance(target.get(name), str)
            for name in ("governed_project_id", "fact_type_key", "object_id")
        ):
            reference = FactReference(
                str(target["governed_project_id"]),
                str(target["fact_type_key"]),
                str(target["object_id"]),
            )
        if reference is None:
            continue
        if configuration_index is not None:
            authority, _entry, _status = _resolve_authority_reference(configuration_index, reference)
            if authority is not None:
                reference = authority
        result.add(_reference_identity(reference))
    return result


def _source_refs(root: Path, fact_type_key: str, read: FactReadResult) -> list[dict[str, object]]:
    return [
        source_reference("rule", _TYPE_SOURCES[fact_type_key]),
        {
            "kind": "working_tree",
            "locator": (root / read.canonical_path).as_posix(),
            "observed_at": utc_now_iso(),
            "details": {"view": "Working Tree", "check_status": read.check_status},
        },
    ]


def _source_result(
    source: FactReference,
    root: Path,
    read: FactReadResult,
) -> dict[str, object]:
    return {
        "source_ref": (
            _stable_ref(source.governed_project_id, source.fact_type_key, read.fields)
            if read.fields is not None
            else source.to_json()
        ),
        "check_status": read.check_status,
        "canonical_path": read.canonical_path,
        "issues": [
            {"category": issue.category, "field_path": issue.field_path, "summary": issue.summary}
            for issue in read.issues
        ],
        "source_refs": _source_refs(root, source.fact_type_key, read),
    }


def _declared_relations(read: FactReadResult) -> tuple[tuple[int, str, StableFactReference], ...]:
    """Return only schema-shaped direct declarations from a safely parsed source."""

    if read.fields is None or not isinstance(read.fields.get("relations"), list):
        return ()
    result: list[tuple[int, str, StableFactReference]] = []
    for index, relation in enumerate(read.fields["relations"]):
        if not isinstance(relation, dict):
            continue
        relation_key = relation.get("relation_key")
        target = relation.get("target")
        if not isinstance(relation_key, str) or not isinstance(target, dict):
            continue
        if set(target) == {"object_uid"} and isinstance(target.get("object_uid"), str):
            result.append((index, relation_key, UIDFactReference(target["object_uid"])))
            continue
        project_id = target.get("governed_project_id")
        fact_type_key = target.get("fact_type_key")
        object_id = target.get("object_id")
        if not all(isinstance(value, str) and value for value in (project_id, fact_type_key, object_id)):
            continue
        result.append((index, relation_key, FactReference(project_id, fact_type_key, object_id)))
    return tuple(result)


def _resolve_authority_reference(
    configuration_index: ConfigurationFactIndex,
    reference: StableFactReference,
) -> tuple[StableFactReference | None, ConfigurationFactEntry | None, str]:
    if isinstance(reference, UIDFactReference):
        entry, status = configuration_index.resolve_uid(reference.object_uid)
        return (reference if entry is not None else None), entry, status
    match = next(
        (
            (project_id, root, common_dir, index)
            for project_id, root, common_dir, index in configuration_index.project_indexes
            if project_id == reference.governed_project_id
        ),
        None,
    )
    if match is None:
        return None, None, "not_found"
    project_id, root, common_dir, index = match
    read = index.read(reference.fact_type_key, reference.object_id)
    if read is None or read.check_status == "not_found":
        return None, None, "not_found"
    if read.check_status == "unavailable":
        return None, None, "unavailable"
    entry = ConfigurationFactEntry(
        project_id,
        root,
        common_dir,
        reference.fact_type_key,
        reference.object_id,
        read,
        index,
    )
    object_uid = None if read.fields is None else read.fields.get("object_uid")
    authority: StableFactReference = (
        UIDFactReference(object_uid) if isinstance(object_uid, str) else reference
    )
    return authority, entry, "resolved"


def _source_edge_failure(
    source_read: FactReadResult,
    *,
    target_status: str | None,
) -> tuple[str, str] | None:
    """Keep a source-level mechanical failure from being emitted as a usable edge."""

    if source_read.check_status == "mechanically_valid":
        return None
    if source_read.check_status not in {"invalid", "unavailable"}:
        return "unavailable", "source-unavailable"
    target_failure = target_status in {"not_found", "invalid", "unavailable"}
    only_target_resolution_failures = source_read.issues and all(
        (
            isinstance(issue.field_path, str)
            and issue.field_path.startswith("relations[")
            and issue.field_path.endswith("].target")
            and issue.code == "TARGET_NOT_EXIST"
        )
        or issue.code == "RELATION_CHECK_UNAVAILABLE"
        for issue in source_read.issues
    )
    if target_failure and only_target_resolution_failures:
        return None
    reason = "source-invalid" if source_read.check_status == "invalid" else "source-unavailable"
    return source_read.check_status, reason


def _source_filter_reasons(
    domain: FactCandidateRequest,
    fields: dict[str, Any],
    configuration_index: ConfigurationFactIndex | None = None,
) -> tuple[list[str], list[dict[str, object]]]:
    """Evaluate all post-resolution F2 conditions for one source-edge target."""

    fact_type_key = fields["fact_type_key"]
    status = fields.get("status")
    filtered: list[str] = []
    matched: list[dict[str, object]] = []
    if fact_type_key not in domain.fact_type_keys:
        filtered.append("fact-type-filter")
    if domain.statuses is not None:
        if status not in set(domain.statuses):
            filtered.append("explicit-status-filter")
        else:
            matched.append({"kind": "status", "field_path": "status"})
    identity = _object_identity(domain.governed_project_id, fact_type_key, fields)
    if domain.exact_refs:
        if identity not in _references(domain.exact_refs):
            filtered.append("exact-ref-filter")
        else:
            matched.append({"kind": "exact-ref", "field_path": "object_id"})
    if domain.relation_targets:
        targets = _references(domain.relation_targets)
        if not (_relations(fields, configuration_index) & targets):
            filtered.append("relation-target-filter")
        else:
            matched.append({"kind": "relation-target", "field_path": "relations[].target"})
    if domain.locator_text is not None:
        locator = _locator_match(fields, domain.locator_text)
        if locator is None:
            filtered.append("locator-filter")
        else:
            matched.append({"kind": "locator", "field_path": "urls[].ref", "matched_text": locator})
    if domain.text_match is not None:
        text = _field_match(fields, domain.text_match.field_paths, domain.text_match.text)
        if text is None:
            filtered.append("field-text-filter")
        else:
            matched.append({"kind": "field-text", "field_path": text[0], "matched_text": text[1]})
    return [reason for reason in _EDGE_REASON_ORDER if reason in filtered], matched


def _locator_match(fields: dict[str, Any], needle: str) -> str | None:
    raw = fields.get("urls")
    if not isinstance(raw, list):
        return None
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("ref"), str) and needle in item["ref"]:
            return item["ref"]
    return None


def _field_match(fields: dict[str, Any], paths: tuple[str, ...], needle: str) -> tuple[str, str] | None:
    for path in paths:
        value = fields.get(path)
        candidates = [value] if isinstance(value, str) else value if isinstance(value, list) else []
        for candidate in candidates:
            if isinstance(candidate, str) and needle in candidate:
                return path, needle
    return None


def _source_navigation(
    domain: FactCandidateRequest,
    *,
    project_id: str,
    configuration_index: ConfigurationFactIndex,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    dict[tuple[object, ...], tuple[str, Path, str, FactReadResult]],
]:
    """Organize only source-declared direct fact edges for one F2 request."""

    source_results: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []
    card_reads: dict[tuple[object, ...], tuple[str, Path, str, FactReadResult]] = {}
    source_refs = sorted(
        domain.relation_source_refs,
        key=lambda item: _ref_sort_key(item.to_json()),
    )
    for requested_source in source_refs:
        source_authority, source_entry, source_status = _resolve_authority_reference(
            configuration_index, requested_source
        )
        if source_entry is None or source_authority is None:
            source_results.append(
                {
                    "source_ref": requested_source.to_json(),
                    "check_status": (
                        "invalid" if source_status in {"duplicate", "invalid"}
                        else "not_found" if source_status == "not_found"
                        else "unavailable"
                    ),
                    "canonical_path": None,
                    "issues": [
                        {
                            "category": "reference",
                            "field_path": None,
                            "summary": f"关系来源引用解析状态为 {source_status}",
                        }
                    ],
                    "source_refs": [],
                }
            )
            continue
        source = FactReference(
            source_entry.governed_project_id,
            source_entry.fact_type_key,
            source_entry.object_id,
        )
        index = source_entry.project_index
        stabilize_project_index(index, ((source.fact_type_key, source.object_id),))
        source_read = index.read(source.fact_type_key, source.object_id)
        source_base = index.base_read(source.fact_type_key, source.object_id)
        if source_read is None or source_base is None:
            continue
        root = source_entry.root
        source_results.append(_source_result(source, root, source_read))
        if source_base.check_status != "mechanically_valid" or source_base.fields is None:
            continue
        source_evidence = _source_refs(root, source.fact_type_key, source_read)
        source_ref = _stable_ref(source.governed_project_id, source.fact_type_key, source_base.fields)
        for relation_index, relation_key, target in _declared_relations(source_base):
            edge: dict[str, object] = {
                "source_ref": source_ref,
                "relation_index": relation_index,
                "relation_key": relation_key,
                "target_ref": target.to_json(),
                "relation_definition_refs": [
                    source_reference("rule", _RELATION_DEFINITION_LOCATORS[source.fact_type_key])
                ],
                "source_refs": source_evidence,
            }
            if domain.relation_keys and relation_key not in set(domain.relation_keys):
                edge.update(edge_status="filtered", reasons=["relation-key-filter"])
                edges.append(edge)
                continue
            target_authority, target_entry, target_resolution = _resolve_authority_reference(
                configuration_index, target
            )
            target_read = None if target_entry is None else target_entry.read
            if target_entry is not None:
                stabilize_project_index(
                    target_entry.project_index,
                    ((target_entry.fact_type_key, target_entry.object_id),),
                )
                target_read = target_entry.project_index.read(target_entry.fact_type_key, target_entry.object_id)
            target_status = (
                "invalid" if target_resolution in {"duplicate", "invalid"}
                else "not_found" if target_resolution == "not_found"
                else "unavailable" if target_resolution == "unavailable"
                else target_read.check_status if target_read is not None else "unavailable"
            )
            if target_authority is not None:
                edge["target_ref"] = target_authority.to_json()
            source_failure = _source_edge_failure(
                source_read,
                target_status=target_status,
            )
            if source_failure is not None:
                edge.update(edge_status=source_failure[0], reasons=[source_failure[1]])
                edges.append(edge)
                continue
            if target_status == "not_found":
                edge.update(edge_status="not_found", reasons=["target-not-found"])
                edges.append(edge)
                continue
            if target_status == "invalid":
                edge.update(edge_status="invalid", reasons=["target-invalid"])
                edges.append(edge)
                continue
            if target_status == "unavailable" or target_read is None or target_read.fields is None:
                edge.update(edge_status="unavailable", reasons=["target-unavailable"])
                edges.append(edge)
                continue
            filtered, _ = _source_filter_reasons(domain, target_read.fields, configuration_index)
            if filtered:
                edge.update(edge_status="filtered", reasons=filtered)
                edges.append(edge)
                continue
            edge.update(edge_status="returned", reasons=["relation-source"])
            edges.append(edge)
            identity = _reference_identity(target_authority) if target_authority is not None else ()
            assert target_entry is not None
            card_reads.setdefault(
                identity,
                (
                    target_entry.governed_project_id,
                    target_entry.root,
                    target_entry.fact_type_key,
                    target_read,
                ),
            )
    edges.sort(
        key=lambda item: (
            _ref_sort_key(item.get("source_ref")),
            item["relation_key"],
            _ref_sort_key(item.get("target_ref")),
            item["relation_index"],
        )
    )
    return source_results, edges, card_reads


def _reasons(
    domain: FactCandidateRequest,
    fields: dict[str, Any],
    configuration_index: ConfigurationFactIndex | None = None,
) -> list[dict[str, object]] | None:
    fact_type_key = fields["fact_type_key"]
    status = fields.get("status")
    if domain.card_layer == "F1":
        if fact_type_key not in _F1_FIELDS:
            return None
        expected = status == "active" if fact_type_key == "adr" else status in ACTIVE_STATUSES
        return [{"kind": "recovery-baseline", "field_path": "status"}] if expected else None
    if fact_type_key not in domain.fact_type_keys:
        return None
    identity = _object_identity(domain.governed_project_id, fact_type_key, fields)
    reasons: list[dict[str, object]] = []
    if domain.statuses is not None:
        if status not in set(domain.statuses):
            return None
        reasons.append({"kind": "status", "field_path": "status"})
    elif not domain.exact_refs:
        if status not in _DEFAULT_STATUSES[fact_type_key]:
            return None
        reasons.append({"kind": "default-status", "field_path": "status"})
    if domain.exact_refs:
        if identity not in _references(domain.exact_refs):
            return None
        reasons.append({"kind": "exact-ref", "field_path": "object_id"})
    if domain.relation_targets:
        targets = _references(domain.relation_targets)
        if not (_relations(fields, configuration_index) & targets):
            return None
        reasons.append({"kind": "relation-target", "field_path": "relations[].target"})
    if domain.locator_text is not None:
        matched = _locator_match(fields, domain.locator_text)
        if matched is None:
            return None
        reasons.append(
            {
                "kind": "locator",
                "field_path": "urls[].ref",
                "matched_text": matched,
            }
        )
    if domain.text_match is not None:
        matched = _field_match(fields, domain.text_match.field_paths, domain.text_match.text)
        if matched is None:
            return None
        reasons.append({"kind": "field-text", "field_path": matched[0], "matched_text": matched[1]})
    return reasons


def _card(
    domain: FactCandidateRequest,
    project_id: str,
    root: Path,
    fact_type_key: str,
    read: FactReadResult,
    reasons: list[dict[str, object]],
) -> dict[str, object]:
    assert read.fields is not None
    if fact_type_key == "workcase":
        projection = (
            _WORKCASE_F2_CLOSED_FIELDS
            if domain.card_layer == "F2" and read.fields.get("status") == "closed"
            else _F1_FIELDS["workcase"]
        )
    else:
        projection = _F1_FIELDS[fact_type_key] if domain.card_layer == "F1" else _F2_FIELDS[fact_type_key]
    fields = {field: read.fields[field] for field in projection if field in read.fields}
    excerpts: list[dict[str, object]] = []
    if domain.card_layer == "F2" and fact_type_key == "spark":
        for field_path in ("intent", "summary"):
            value = read.fields.get(field_path)
            if not isinstance(value, str):
                continue
            excerpts.append(
                {
                    "field_path": field_path,
                    "text": value[:_EXCERPT_LIMIT],
                    "complete": len(value) <= _EXCERPT_LIMIT,
                }
            )
    if fact_type_key == "workcase" and read.fields.get("status") in ACTIVE_STATUSES:
        counts = Counter(
            item.get("status")
            for item in read.fields.get("work_items", [])
            if isinstance(item, dict) and isinstance(item.get("status"), str)
        )
        fields["work_item_counts"] = {
            status: counts.get(status, 0) for status in ("pending", "in_progress", "blocked", "completed", "cancelled")
        }
    observed_at = utc_now_iso()
    sources = [
        source_reference("rule", _TYPE_SOURCES[fact_type_key]),
        {
            "kind": "working_tree",
            "locator": (root / read.canonical_path).as_posix(),
            "observed_at": observed_at,
            "details": {"view": "Working Tree"},
        },
    ]
    return {
        "fact_ref": _stable_ref(project_id, fact_type_key, read.fields),
        "card_layer": domain.card_layer,
        "fields": fields,
        "excerpts": excerpts,
        "match_reasons": reasons,
        "source_refs": sources,
    }


def _query_fingerprint(domain: FactCandidateRequest, root: Path, common_dir: Path) -> str:
    return _digest(
        {
            "project": domain.governed_project_id,
            "worktree": root.as_posix(),
            "common_dir": common_dir.as_posix(),
            "layer": domain.card_layer,
            "types": domain.fact_type_keys,
            "statuses": domain.statuses,
            "exact_refs": [item.to_json() for item in domain.exact_refs],
            "relation_targets": [item.to_json() for item in domain.relation_targets],
            "relation_source_refs": [
                item.to_json()
                for item in sorted(
                    domain.relation_source_refs,
                    key=lambda item: _ref_sort_key(item.to_json()),
                )
            ],
            "relation_keys": sorted(domain.relation_keys),
            "current_workcase_ref": (
                None if domain.current_workcase_ref is None else domain.current_workcase_ref.to_json()
            ),
            "selected_fact_refs": [item.to_json() for item in domain.selected_fact_refs],
            "locator_text": domain.locator_text,
            "text_match": None
            if domain.text_match is None
            else {"text": domain.text_match.text, "field_paths": domain.text_match.field_paths},
            "page_size": domain.page_size,
        }
    )


def _encode_cursor(query: str, objects: str, offset: int) -> str:
    payload = _stable_json({"v": 1, "query": query, "objects": objects, "offset": offset}).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"{encoded}.{hashlib.sha256(payload).hexdigest()}"


def _cursor_offset(cursor: str | None, query: str, objects: str, total: int) -> int:
    if cursor is None:
        return 0
    try:
        encoded, checksum = cursor.split(".", 1)
        payload = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        if hashlib.sha256(payload).hexdigest() != checksum:
            raise CursorRejected
        decoded = json.loads(payload)
        if set(decoded) != {"v", "query", "objects", "offset"} or decoded["v"] != 1:
            raise CursorRejected
        offset = decoded["offset"]
        if decoded["query"] != query or decoded["objects"] != objects:
            raise CursorRejected
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or offset >= total:
            raise CursorRejected
        return offset
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise CursorRejected from error


def _requested_scope(domain: FactCandidateRequest) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "governed_project_id": domain.governed_project_id,
            "card_layer": domain.card_layer,
            "fact_type_key": fact_type_key,
        }
        for fact_type_key in sorted(LAYOUTS)
    )


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_request(request, context)
    requested = _requested_scope(domain)
    run = _governance(domain)
    governance_json = None if run.result is None else run.result.to_json()
    boundary = reading_boundary(run)
    if boundary is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成唯一事实对象候选扫描边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + _IMPLEMENTATION_EVIDENCE,
            gaps=(
                {
                    "summary": "管辖输入未形成同一项目、同一实际 worktree 和 common-dir 的唯一边界",
                    "scope": list(requested),
                    "source_refs": [plain(source) for source in run.sources],
                },
            ),
        )
    project_id, root, common_dir = boundary
    if project_id != domain.governed_project_id:
        return OperationExecution(
            outcome="rejected",
            summary="请求项目与实际管辖项目不一致",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + (_INPUT_CONTRACT,),
            gaps=(
                {
                    "summary": "governed_project_id 与实际管辖结果不一致",
                    "scope": list(requested),
                    "source_refs": [_INPUT_CONTRACT],
                },
            ),
        )
    schemas = project_fact_schemas(repository)
    if set(schemas) != set(LAYOUTS):
        return OperationExecution(
            outcome="unavailable",
            summary="当前规则源不能形成五类型完整派生 Schema",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + (_RESULT_CONTRACT,),
            gaps=(
                {
                    "summary": "五类型派生 Schema 不完整，不能形成可信 F0",
                    "scope": list(requested),
                    "source_refs": [_RESULT_CONTRACT],
                },
            ),
        )
    configuration_boundaries = configuration_reading_boundaries(run)
    if configuration_boundaries is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成配置级 UID 引用解析边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + (_RESULT_CONTRACT,),
        )
    configuration_index = ConfigurationFactIndex(configuration_boundaries, schemas)
    if not configuration_index.prepare():
        return OperationExecution(
            outcome="unavailable",
            summary="配置级 UID 全扫描未能完整形成",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + (_RESULT_CONTRACT,),
        )
    reference_failures: list[dict[str, object]] = []

    def resolved_filter_refs(
        values: tuple[StableFactReference, ...],
        field_path: str,
    ) -> tuple[StableFactReference, ...]:
        resolved: list[StableFactReference] = []
        for value in values:
            authority, _entry, status = _resolve_authority_reference(configuration_index, value)
            if authority is None:
                reference_failures.append(
                    {
                        "fact_ref": value.to_json(),
                        "canonical_path": None,
                        "check_status": "invalid" if status in {"duplicate", "invalid"} else status,
                        "issues": [
                            {
                                "category": "reference",
                                "field_path": field_path,
                                "summary": f"引用解析状态为 {status}",
                            }
                        ],
                    }
                )
            else:
                resolved.append(authority)
        return tuple(resolved)

    filter_domain = replace(
        domain,
        exact_refs=resolved_filter_refs(domain.exact_refs, "exact_refs"),
        relation_targets=resolved_filter_refs(domain.relation_targets, "relation_targets"),
    )
    if domain.current_workcase_ref is not None:
        _authority, current_entry, current_status = _resolve_authority_reference(
            configuration_index, domain.current_workcase_ref
        )
        if current_entry is not None and current_entry.fact_type_key != "workcase":
            raise OperationRequestError(
                ("arguments.current_workcase_ref 解析后的类型必须为 workcase",),
                sources=(_INPUT_CONTRACT,),
            )
        if current_entry is None:
            reference_failures.append(
                {
                    "fact_ref": domain.current_workcase_ref.to_json(),
                    "canonical_path": None,
                    "check_status": "invalid" if current_status in {"duplicate", "invalid"} else current_status,
                    "issues": [
                        {
                            "category": "reference",
                            "field_path": "current_workcase_ref",
                            "summary": f"引用解析状态为 {current_status}",
                        }
                    ],
                }
            )
    selected_index = next(
        (
            candidate_index
            for candidate_project_id, _candidate_root, _candidate_common, candidate_index
            in configuration_index.project_indexes
            if candidate_project_id == project_id
        ),
        None,
    )
    if selected_index is None:
        return OperationExecution(
            outcome="unavailable",
            summary="请求项目未形成配置级事实索引",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + (_RESULT_CONTRACT,),
        )
    snapshot = discover_fact_candidates(root, project_id, common_dir, schemas, index=selected_index)
    structural = list(snapshot.structural_problems)
    reads = [
        (fact_type, object_id, snapshot.index.cache[(fact_type, object_id)]) for fact_type, object_id in snapshot.keys
    ]
    object_fingerprint = snapshot.object_set_fingerprint
    invalid = [
        _problem_item(project_id, fact_type, object_id, read)
        for fact_type, object_id, read in reads
        if read.check_status == "invalid"
    ] + reference_failures
    unavailable = [
        _problem_item(project_id, fact_type, object_id, read)
        for fact_type, object_id, read in reads
        if read.check_status == "unavailable"
    ] + structural
    valid = [item for item in reads if item[2].check_status == "mechanically_valid" and item[2].fields is not None]
    counts = Counter((fact_type, str(read.fields["status"])) for fact_type, _, read in valid if read.fields)
    count_rows = [
        {"fact_type_key": fact_type, "status": status, "count": counts[(fact_type, status)]}
        for fact_type, layout in sorted(LAYOUTS.items())
        for status in sorted(layout.statuses)
    ]
    source_results: list[dict[str, object]] = []
    all_edges: list[dict[str, object]] = []
    edge_card_reads: dict[tuple[object, ...], tuple[str, Path, str, FactReadResult]] = {}
    cards: list[dict[str, object]] = []
    if domain.relation_source_refs:
        source_results, all_edges, edge_card_reads = _source_navigation(
            filter_domain,
            project_id=project_id,
            configuration_index=configuration_index,
        )
    else:
        for fact_type, _, read in valid:
            assert read.fields is not None
            reasons = _reasons(filter_domain, read.fields, configuration_index)
            if reasons is not None:
                cards.append(_card(domain, project_id, root, fact_type, read, reasons))
        cards.sort(key=lambda item: _ref_sort_key(item.get("fact_ref")))

    query_fingerprint = _query_fingerprint(domain, root, common_dir)
    paginated = all_edges if domain.relation_source_refs else cards
    try:
        offset = _cursor_offset(domain.cursor, query_fingerprint, object_fingerprint, len(paginated))
    except CursorRejected:
        return OperationExecution(
            outcome="rejected",
            summary="cursor 与当前查询或对象集合不一致，必须从第一页重启",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + (_INPUT_CONTRACT,),
            gaps=(
                {
                    "summary": "cursor 已失效、损坏或越界；不得合并旧页与当前对象集",
                    "scope": list(requested),
                    "source_refs": [_INPUT_CONTRACT],
                    "code": "stale_cursor",
                },
            ),
        )
    page_members = paginated[offset : offset + domain.page_size]
    if domain.relation_source_refs:
        page_edges = page_members
        page_card_reasons: dict[tuple[object, ...], list[dict[str, object]]] = {}
        for edge in page_edges:
            if edge["edge_status"] != "returned":
                continue
            target = edge["target_ref"]
            assert isinstance(target, dict)
            identity = (
                ("uid", str(target["object_uid"]))
                if isinstance(target.get("object_uid"), str)
                else (
                    "legacy",
                    str(target["governed_project_id"]),
                    str(target["fact_type_key"]),
                    str(target["object_id"]),
                )
            )
            _card_project, _card_root, _card_type, read = edge_card_reads[identity]
            assert read.fields is not None
            _, matched = _source_filter_reasons(filter_domain, read.fields, configuration_index)
            reasons = page_card_reasons.setdefault(identity, [])
            for reason in [
                *matched,
                {"kind": "relation-source", "field_path": f"relations[{edge['relation_index']}].target"},
            ]:
                if reason not in reasons:
                    reasons.append(reason)
        cards = [
            _card(domain, card_project_id, card_root, fact_type_key, read, reasons)
            for identity, reasons in page_card_reasons.items()
            for card_project_id, card_root, fact_type_key, read in (edge_card_reads[identity],)
        ]
        cards.sort(key=lambda item: _ref_sort_key(item.get("fact_ref")))
    else:
        page_edges = []
        cards = page_members
    next_offset = offset + len(page_members)
    next_cursor = (
        _encode_cursor(query_fingerprint, object_fingerprint, next_offset) if next_offset < len(paginated) else None
    )
    failed_edges = [edge for edge in all_edges if edge["edge_status"] in {"not_found", "invalid", "unavailable"}]
    incomplete_sources = [item for item in source_results if item["check_status"] != "mechanically_valid"]
    partial = bool(invalid or unavailable or not snapshot.complete or incomplete_sources or failed_edges)
    coverage_status: Literal["complete", "partial"] = "partial" if partial else "complete"
    manifest = {
        "governed_project_id": project_id,
        "git_worktree_root": root.as_posix(),
        "git_common_dir": common_dir.as_posix(),
        "schema_fingerprint": snapshot.schema_fingerprint,
        "object_set_fingerprint": object_fingerprint,
        "counts": count_rows,
        "current_workcase_ref": (
            None if domain.current_workcase_ref is None else domain.current_workcase_ref.to_json()
        ),
        "selected_fact_refs": [item.to_json() for item in domain.selected_fact_refs],
        "invalid_objects": invalid,
        "unavailable_objects": unavailable,
    }
    result = {
        "recovery_manifest": manifest,
        "cards": cards,
        "coverage": {
            "status": coverage_status,
            "total_matching": len(paginated),
            "returned": len(page_members),
            "offset": offset,
            "next_cursor": next_cursor,
            "object_set_fingerprint": object_fingerprint,
        },
    }
    if domain.relation_source_refs:
        result["relation_navigation"] = {"source_results": source_results, "edges": page_edges}
    sources = tuple(plain(source) for source in run.sources) + (_RESULT_CONTRACT, *_IMPLEMENTATION_EVIDENCE)
    gaps: tuple[dict[str, Any], ...] = ()
    delivered_failed_edges = [
        edge for edge in page_edges if edge["edge_status"] in {"not_found", "invalid", "unavailable"}
    ]
    relation_scope = [
        *incomplete_sources,
        *[
            {
                "source_ref": edge["source_ref"],
                "relation_key": edge["relation_key"],
                "target_ref": edge["target_ref"],
                "edge_status": edge["edge_status"],
                "reasons": edge["reasons"],
            }
            for edge in delivered_failed_edges
        ],
    ]
    if partial:
        gaps = (
            {
                "summary": (
                    "部分事实对象无效、不可读、关系来源未观察或直接边未解析；F1 恢复基线不得视为完整"
                    if domain.relation_source_refs
                    else "部分事实对象无效、不可读或扫描范围未完成；F1 恢复基线不得视为完整"
                ),
                "scope": [*invalid, *unavailable, *relation_scope],
                "source_refs": [_RESULT_CONTRACT],
            },
        )
    incomplete_types = {
        item["fact_ref"]["fact_type_key"]
        for item in [*invalid, *unavailable]
        if isinstance(item.get("fact_ref"), dict) and isinstance(item["fact_ref"].get("fact_type_key"), str)
    }
    incomplete_types.update(item["fact_type_key"] for item in structural if isinstance(item.get("fact_type_key"), str))
    if incomplete_sources or failed_edges:
        incomplete_types.update(domain.fact_type_keys)
    completed_scope = tuple(scope for scope in requested if scope["fact_type_key"] not in incomplete_types)
    not_completed_scope = tuple(scope for scope in requested if scope["fact_type_key"] in incomplete_types)
    return OperationExecution(
        outcome="partial" if partial else "ok",
        summary=(
            "已形成部分事实恢复清单与候选卡，并保留未完成范围" if partial else "已形成当前事实恢复清单与确定性候选卡"
        ),
        result=result,
        requested_scope=requested,
        completed_scope=completed_scope,
        not_completed_scope=not_completed_scope,
        governance_resolution=governance_json,
        sources=sources,
        gaps=gaps,
        verification=(
            {
                "check": "当前 Working Tree 直接扫描、机械检查、类型化投影、排序和分页已执行",
                "status": "partial" if partial else "passed",
                "scope": list(requested),
                "evidence": list(sources),
            },
        ),
    )


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    execution = _execute(request, repository, context)
    if execution.completed_scope and execution.not_completed_scope:
        availability = "partially_available"
    elif execution.not_completed_scope:
        availability = "unavailable_for_request"
    else:
        availability = "available_for_request"
    return AvailabilityEvaluation(
        availability=availability,
        available_scope=execution.completed_scope,
        unavailable_scope=execution.not_completed_scope,
        gaps=execution.gaps,
    )


FACT_CANDIDATE_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(*_IMPLEMENTATION_EVIDENCE, _RESULT_CONTRACT),
    check_availability=_check_availability,
    call=_execute,
    input_examples=_INPUT_EXAMPLES,
)

__all__ = ["FACT_CANDIDATE_IMPLEMENTATION", "OPERATION_KEY"]
