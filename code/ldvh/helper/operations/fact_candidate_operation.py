"""Directly scan current fact objects and return source-defined F0/F1/F2 projections."""

from __future__ import annotations

import base64
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from ldvh.facts.candidate_discovery import discover_fact_candidates
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactReference
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
from ldvh.helper.operations.fact_operation_support import plain, reading_boundary
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "find-fact-object-candidates"
_INPUT_CONTRACT = source_reference("rule", "fact-model-foundation::11.5 事实对象候选发现输入字段")
_RESULT_CONTRACT = source_reference("rule", "fact-model-foundation::11.6 事实对象候选发现结果字段")
_IMPLEMENTATION_EVIDENCE = (
    source_reference("implementation", "code/ldvh/helper/operations/fact_candidate_operation.py"),
)
_TYPE_SOURCES = {
    "spark": "specs/20-Spark-火花.md",
    "workcase": "specs/21-WorkCase-工作项.md",
    "adr": "specs/22-ADR-决策.md",
    "pitfall": "specs/23-Pitfall-踩坑经验.md",
    "study": "specs/24-Study-研究报告.md",
}
_DEFAULT_STATUSES = {
    "spark": frozenset({"open"}),
    "workcase": frozenset({"open", "blocked"}),
    "adr": frozenset({"active"}),
    "pitfall": frozenset({"active"}),
    "study": frozenset({"active"}),
}
_F1_FIELDS = {
    "adr": ("object_id", "title", "decision_question", "decision", "applicability", "updated_at"),
    "workcase": (
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
_F2_FIELDS = {
    "spark": ("object_id", "title", "status", "priority", "updated_at"),
    "workcase": _F1_FIELDS["workcase"],
    "adr": ("object_id", "title", "status", "decision_question", "decision", "applicability", "updated_at"),
    "pitfall": (
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
        "object_id",
        "title",
        "status",
        "research_question",
        "abstract",
        "applicability",
        "validation_summary",
        "updated_at",
    ),
}
_EXCERPT_LIMIT = 512


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


def _problem_item(
    project_id: str,
    fact_type_key: str,
    object_id: str,
    read: FactReadResult,
) -> dict[str, object]:
    return {
        "fact_ref": FactReference(project_id, fact_type_key, object_id).to_json(),
        "canonical_path": read.canonical_path,
        "check_status": read.check_status,
        "issues": [
            {"category": issue.category, "field_path": issue.field_path, "summary": issue.summary}
            for issue in read.issues
        ],
    }


def _references(value: tuple[FactReference, ...]) -> set[tuple[str, str, str]]:
    return {(item.governed_project_id, item.fact_type_key, item.object_id) for item in value}


def _relations(fields: dict[str, Any]) -> set[tuple[object, object, object]]:
    result: set[tuple[object, object, object]] = set()
    raw = fields.get("relations")
    if not isinstance(raw, list):
        return result
    for relation in raw:
        if not isinstance(relation, dict) or not isinstance(relation.get("target"), dict):
            continue
        target = relation["target"]
        result.add((target.get("governed_project_id"), target.get("fact_type_key"), target.get("object_id")))
    return result


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


def _reasons(domain: FactCandidateRequest, fields: dict[str, Any]) -> list[dict[str, object]] | None:
    fact_type_key = fields["fact_type_key"]
    object_id = fields["object_id"]
    status = fields.get("status")
    if domain.card_layer == "F1":
        if fact_type_key not in _F1_FIELDS:
            return None
        expected = status == "active" if fact_type_key == "adr" else status in {"open", "blocked"}
        return [{"kind": "recovery-baseline", "field_path": "status"}] if expected else None
    if fact_type_key not in domain.fact_type_keys:
        return None
    reasons: list[dict[str, object]] = []
    if domain.statuses is not None:
        if status not in set(domain.statuses):
            return None
        reasons.append({"kind": "status", "field_path": "status"})
    elif not domain.exact_refs:
        if status not in _DEFAULT_STATUSES[fact_type_key]:
            return None
        reasons.append({"kind": "default-status", "field_path": "status"})
    identity = (domain.governed_project_id, fact_type_key, object_id)
    if domain.exact_refs:
        if identity not in _references(domain.exact_refs):
            return None
        reasons.append({"kind": "exact-ref", "field_path": "object_id"})
    if domain.relation_targets:
        targets = _references(domain.relation_targets)
        if not (_relations(fields) & targets):
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
    object_id = read.fields["object_id"]
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
    if fact_type_key == "workcase":
        counts = Counter(
            item.get("status")
            for item in read.fields.get("work_items", [])
            if isinstance(item, dict) and isinstance(item.get("status"), str)
        )
        fields["work_item_counts"] = {
            status: counts.get(status, 0) for status in ("pending", "in_progress", "blocked", "completed", "cancelled")
        }
    observed_at = datetime.now().astimezone().isoformat()
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
        "fact_ref": FactReference(project_id, fact_type_key, object_id).to_json(),
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

    snapshot = discover_fact_candidates(root, project_id, common_dir, schemas)
    structural = list(snapshot.structural_problems)
    reads = [
        (fact_type, object_id, snapshot.index.cache[(fact_type, object_id)]) for fact_type, object_id in snapshot.keys
    ]
    object_fingerprint = snapshot.object_set_fingerprint
    invalid = [
        _problem_item(project_id, fact_type, object_id, read)
        for fact_type, object_id, read in reads
        if read.check_status == "invalid"
    ]
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
    cards: list[dict[str, object]] = []
    for fact_type, _, read in valid:
        assert read.fields is not None
        reasons = _reasons(domain, read.fields)
        if reasons is not None:
            cards.append(_card(domain, project_id, root, fact_type, read, reasons))
    cards.sort(key=lambda item: (item["fact_ref"]["fact_type_key"], item["fact_ref"]["object_id"]))  # type: ignore[index]

    query_fingerprint = _query_fingerprint(domain, root, common_dir)
    try:
        offset = _cursor_offset(domain.cursor, query_fingerprint, object_fingerprint, len(cards))
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
    page = cards[offset : offset + domain.page_size]
    next_offset = offset + len(page)
    next_cursor = (
        _encode_cursor(query_fingerprint, object_fingerprint, next_offset) if next_offset < len(cards) else None
    )
    partial = bool(invalid or unavailable or not snapshot.complete)
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
        "cards": page,
        "coverage": {
            "status": coverage_status,
            "total_matching": len(cards),
            "returned": len(page),
            "offset": offset,
            "next_cursor": next_cursor,
            "object_set_fingerprint": object_fingerprint,
        },
    }
    sources = tuple(plain(source) for source in run.sources) + (_RESULT_CONTRACT, *_IMPLEMENTATION_EVIDENCE)
    gaps: tuple[dict[str, Any], ...] = ()
    if partial:
        gaps = (
            {
                "summary": "部分事实对象无效、不可读或扫描范围未完成；F1 恢复基线不得视为完整",
                "scope": [*invalid, *unavailable],
                "source_refs": [_RESULT_CONTRACT],
            },
        )
    incomplete_types = {
        item["fact_ref"]["fact_type_key"] for item in [*invalid, *unavailable] if isinstance(item.get("fact_ref"), dict)
    }
    incomplete_types.update(item["fact_type_key"] for item in structural if isinstance(item.get("fact_type_key"), str))
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
)

__all__ = ["FACT_CANDIDATE_IMPLEMENTATION", "OPERATION_KEY"]
