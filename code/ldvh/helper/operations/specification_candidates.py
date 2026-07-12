"""Assemble specification-candidate L0-L2 results from one repository inspection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.projection import DisclosureLayer, ProjectionItem
from ldvh.specs.repository import RepositoryInspection

SuggestedOutcome = Literal["ok", "partial", "unavailable"]
type JsonObject = dict[str, object]

_LAYERS: tuple[DisclosureLayer, ...] = ("L0", "L1", "L2")
_QUALIFICATION_SOURCE = {
    "kind": "rule",
    "locator": "specs/01-规范模型基础规范.md#6.2-进入当前规则源的条件",
}


@dataclass(frozen=True, slots=True)
class SpecificationCandidateReadResult:
    """Domain result fragments; the Helper service owns the common envelope.

    ``RepositoryInspection`` records aggregate membership after implemented
    checks, not a per-check execution ledger.  Verification below therefore
    reports one aggregate passed result per completed key and points back to
    that key's actual Working Tree projection sources.
    """

    items: tuple[JsonObject, ...] | None
    requested_scope: tuple[str, ...]
    completed_scope: tuple[str, ...]
    not_completed_scope: tuple[str, ...]
    sources: tuple[JsonObject, ...]
    disclosure_parts: tuple[JsonObject, ...]
    verification: tuple[JsonObject, ...]
    gaps: tuple[JsonObject, ...]
    diagnostics: tuple[JsonObject, ...]
    suggested_outcome: SuggestedOutcome


class _ProjectionProblem(ValueError):
    pass


def _location_reference(location: SourceLocation) -> JsonObject:
    locator = location.path if location.line is None else f"{location.path}:{location.line}"
    result: JsonObject = {"kind": "rule", "locator": locator}
    if location.heading is not None:
        result["details"] = {"heading": location.heading}
    return result


def _deduplicate_references(references: Sequence[JsonObject]) -> tuple[JsonObject, ...]:
    results: list[JsonObject] = []
    seen: set[tuple[str, str, str]] = set()
    for reference in references:
        identity = (
            str(reference["kind"]),
            str(reference["locator"]),
            repr(reference.get("details", {})),
        )
        if identity not in seen:
            seen.add(identity)
            results.append(reference)
    return tuple(results)


def _projection_sources(projection: ProjectionItem) -> tuple[JsonObject, ...]:
    locations = [location for field_sources in projection.source_references.values() for location in field_sources]
    if not locations:
        locations = [projection.source]
    return _deduplicate_references([_location_reference(location) for location in locations])


def _as_target(value: object, *, field: str) -> JsonObject:
    if not isinstance(value, Mapping):
        raise _ProjectionProblem(f"{field} 关系目标不是对象")
    if set(value) != {"key", "path"}:
        raise _ProjectionProblem(f"{field} 关系目标字段不完整")
    key = value.get("key")
    path = value.get("path")
    if not isinstance(key, str) or not key or not isinstance(path, str) or not path:
        raise _ProjectionProblem(f"{field} 关系目标无法精确映射")
    return {"key": key, "path": path}


def _as_targets(value: object, *, field: str) -> list[JsonObject]:
    if not isinstance(value, (tuple, list)):
        raise _ProjectionProblem(f"{field} 关系列表结构不成立")
    return [_as_target(target, field=field) for target in value]


def _relationship_object(projection: ProjectionItem) -> JsonObject:
    content = projection.content
    if projection.kind == "attachment":
        if set(content) != {"parent_spec", "supersedes"}:
            raise _ProjectionProblem("附件关系投影字段不完整")
        parent = content["parent_spec"]
        if parent is None:
            raise _ProjectionProblem("授权附件缺少可精确映射的父规范")
        return {
            "basis": [],
            "parent_spec": _as_target(parent, field="parent_spec"),
            "relation": None,
            "authorized_attachments": [],
            "supersedes": _as_targets(content["supersedes"], field="supersedes"),
        }

    required = {"basis", "parent_spec", "relation", "authorized_attachments", "supersedes"}
    if set(content) != required:
        raise _ProjectionProblem("规范关系投影字段不完整")
    parent_value = content["parent_spec"]
    relation = content["relation"]
    if relation is not None and not isinstance(relation, str):
        raise _ProjectionProblem("relation 不是 string 或 null")
    return {
        "basis": _as_targets(content["basis"], field="basis"),
        "parent_spec": None if parent_value is None else _as_target(parent_value, field="parent_spec"),
        "relation": relation,
        "authorized_attachments": _as_targets(content["authorized_attachments"], field="authorized_attachments"),
        "supersedes": _as_targets(content["supersedes"], field="supersedes"),
    }


def _build_item(projections: Mapping[DisclosureLayer, ProjectionItem], disclosure: DisclosureLayer) -> JsonObject:
    needed_layers = _LAYERS[: _LAYERS.index(disclosure) + 1]
    if any(layer not in projections for layer in needed_layers):
        raise _ProjectionProblem(f"缺少 {disclosure} 累积返回所需的投影")

    l0 = projections["L0"]
    l0_content = l0.content
    required_l0 = {"key", "id", "title", "status", "path"}
    if set(l0_content) != required_l0 or l0_content["status"] != "active":
        raise _ProjectionProblem("L0 身份投影字段不完整或状态不是 active")
    item: JsonObject = {
        "kind": l0.kind,
        "key": l0_content["key"],
        "id": l0_content["id"],
        "title": l0_content["title"],
        "status": l0_content["status"],
        "path": l0_content["path"],
        "overview": None,
        "relationships": None,
    }

    if disclosure in ("L1", "L2"):
        l1 = projections["L1"]
        if "positioning" not in l1.content or not isinstance(l1.content["positioning"], str):
            raise _ProjectionProblem("L1 概览缺少 positioning")
        scope = l1.content.get("scope")
        if l1.kind == "attachment":
            scope = None
        elif not isinstance(scope, str) or not scope:
            raise _ProjectionProblem("规范或根规范的 L1 概览缺少 scope")
        item["overview"] = {"positioning": l1.content["positioning"], "scope": scope}
    if disclosure == "L2":
        item["relationships"] = _relationship_object(projections["L2"])
    return item


def _issue_references(issue: Issue) -> list[JsonObject]:
    return [_location_reference(issue.location)]


def _relevant_issue(issue: Issue, scopes: set[str], paths: set[str]) -> bool:
    return bool(set(issue.affected) & scopes) or issue.location.path in scopes or issue.location.path in paths


def read_specification_candidates(
    repository: RepositoryInspection,
    *,
    responsibility_keys: tuple[str, ...],
    disclosure: Literal["L0", "L1", "L2"],
) -> SpecificationCandidateReadResult:
    """Read candidate projections without touching the repository filesystem."""

    documents = {document.key: document for document in repository.active_documents_passing_implemented_checks}
    projection_groups: dict[str, dict[DisclosureLayer, ProjectionItem]] = {}
    for projection in repository.projections:
        projection_groups.setdefault(projection.key, {})[projection.layer] = projection

    eligible_keys = tuple(
        document.key
        for document in sorted(
            repository.active_documents_passing_implemented_checks,
            key=lambda item: (item.canonical_path, item.key),
        )
    )
    requested_scope = responsibility_keys or eligible_keys
    selection = responsibility_keys or eligible_keys
    completed: list[str] = []
    not_completed: list[str] = []
    items: list[JsonObject] = []
    gaps: list[JsonObject] = []
    diagnostics: list[JsonObject] = []
    item_sources: list[JsonObject] = []
    level_sources: dict[DisclosureLayer, list[JsonObject]] = {layer: [] for layer in _LAYERS}

    parsed_by_key = {document.key: document for document in repository.parsed_documents}
    incomplete_set = set(repository.incomplete_scope)
    candidate_paths = {candidate.relative_path for candidate in repository.candidates}

    for key in selection:
        document = documents.get(key)
        if document is None:
            not_completed.append(key)
            parsed = parsed_by_key.get(key)
            relevant = [
                issue
                for issue in repository.issues
                if _relevant_issue(
                    issue,
                    {key},
                    {parsed.canonical_path} if parsed is not None else set(),
                )
            ]
            if parsed is not None and parsed.status != "active":
                summary = f"职责标识符 {key} 当前声明状态为 {parsed.status}，不在本操作候选集合中"
            elif relevant or key in incomplete_set:
                summary = f"职责标识符 {key} 未通过全部适用的已实现机械检查"
            else:
                summary = f"未精确匹配职责标识符 {key}"
            sources = [source for issue in relevant for source in _issue_references(issue)]
            gaps.append({"summary": summary, "scope": [key], "source_refs": list(_deduplicate_references(sources))})
            diagnostics.extend(
                {
                    "summary": issue.summary,
                    "details": {
                        "path": issue.location.path,
                        "line": issue.location.line,
                        "affected": list(issue.affected),
                        **({"cause": issue.cause} if issue.cause is not None else {}),
                    },
                    "source_refs": _issue_references(issue),
                }
                for issue in relevant
            )
            continue

        projections = projection_groups.get(key, {})
        try:
            item = _build_item(projections, disclosure)
        except _ProjectionProblem as exc:
            not_completed.append(key)
            key_field = "attachment_key" if document.kind == "attachment" else "spec_key"
            source = _location_reference(
                document.field_locations.get(
                    key_field,
                    SourceLocation(document.canonical_path, document.markdown.yaml_line),
                )
            )
            gaps.append(
                {
                    "summary": f"职责标识符 {key} 的投影或关系无法形成完整 {disclosure} 结果",
                    "scope": [key],
                    "source_refs": [source],
                }
            )
            diagnostics.append(
                {
                    "summary": str(exc),
                    "details": {"responsibility_key": key},
                    "source_refs": [source],
                }
            )
            continue

        items.append(item)
        completed.append(key)
        for layer in _LAYERS[: _LAYERS.index(disclosure) + 1]:
            references = _projection_sources(projections[layer])
            level_sources[layer].extend(references)
            item_sources.extend(references)

    if not responsibility_keys:
        extra_incomplete = [scope for scope in repository.incomplete_scope if scope not in completed]
        relevant_issues = [
            issue
            for issue in repository.issues
            if _relevant_issue(issue, set(extra_incomplete), candidate_paths) or issue.location.path in candidate_paths
        ]
        for scope in extra_incomplete:
            scoped_issues = [issue for issue in relevant_issues if _relevant_issue(issue, {scope}, set())]
            references = [source for issue in scoped_issues for source in _issue_references(issue)]
            gaps.append(
                {
                    "summary": f"候选范围 {scope} 未通过全部适用的已实现机械检查",
                    "scope": [scope],
                    "source_refs": list(_deduplicate_references(references)),
                }
            )
        diagnostics.extend(
            {
                "summary": issue.summary,
                "details": {
                    "path": issue.location.path,
                    "line": issue.location.line,
                    "affected": list(issue.affected),
                    **({"cause": issue.cause} if issue.cause is not None else {}),
                },
                "source_refs": _issue_references(issue),
            }
            for issue in relevant_issues
        )

    qualification_scope = list(completed)
    if qualification_scope:
        gaps.extend(
            {
                "summary": f"尚未由 Code 机械证明当前规则源资格条件：{condition}",
                "scope": qualification_scope,
                "source_refs": [_QUALIFICATION_SOURCE.copy()],
            }
            for condition in repository.unchecked_conditions
        )
        gaps.extend(
            {
                "summary": (
                    f"{overlap.spec_key} 的直接 basis {overlap.direct_basis} 已可经由 "
                    f"{overlap.reachable_via} 到达，其直接必要性需语义复核"
                ),
                "scope": [overlap.spec_key],
                "source_refs": [_QUALIFICATION_SOURCE.copy()],
            }
            for overlap in repository.basis_reachability_overlaps
            if overlap.spec_key in completed
        )

    verification = tuple(
        {
            "check": f"当前实现中适用于 {key} 的全部机械检查已执行并通过（整体结果）",
            "status": "passed",
            "scope": [key],
            "evidence": list(_projection_sources(projection_groups[key]["L0"])),
        }
        for key in completed
    )
    disclosure_parts = tuple(
        {
            "level": layer,
            "source_refs": list(_deduplicate_references(level_sources[layer])),
            "reason": f"请求 {disclosure} 时累积返回 {layer} 信息",
        }
        for layer in _LAYERS[: _LAYERS.index(disclosure) + 1]
        if level_sources[layer]
    )

    completed_scope = tuple(dict.fromkeys(completed))
    not_completed_scope = tuple(dict.fromkeys(not_completed))
    if completed_scope and not_completed_scope:
        outcome: SuggestedOutcome = "partial"
    elif completed_scope:
        outcome = "ok"
    else:
        outcome = "unavailable"

    return SpecificationCandidateReadResult(
        items=tuple(items) if items else None,
        requested_scope=tuple(requested_scope),
        completed_scope=completed_scope,
        not_completed_scope=not_completed_scope,
        sources=_deduplicate_references(item_sources),
        disclosure_parts=disclosure_parts,
        verification=verification,
        gaps=tuple(gaps),
        diagnostics=tuple(diagnostics),
        suggested_outcome=outcome,
    )
