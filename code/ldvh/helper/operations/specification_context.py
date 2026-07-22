"""Compose progressive specification context from one inspected rule snapshot."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from ldvh.helper.operations.specification_content import (
    SpecificationContentReadResult,
    SpecificationContentSelectionError,
    read_specification_content,
)
from ldvh.helper.operations.specification_content_request import (
    SpecificationContentRequest,
    SpecificationContentSelection,
)
from ldvh.helper.operations.specification_context_request import (
    SpecificationContextRequest,
    SpecificationContextSelection,
)
from ldvh.helper.responses import source_reference
from ldvh.helper.source_refs import GeneratedSourceReference, RuleReferenceBinder
from ldvh.specs.identity import FormalDocument
from ldvh.specs.repository import RepositoryInspection
from ldvh.specs.structure import FIXED_TAIL, NUMBERED_H2

type JsonObject = dict[str, object]
SuggestedOutcome = Literal["ok", "partial", "rejected", "unavailable", "error"]

_ROLE_BY_TITLE = {
    "适用范围": "applicability_scope",
    "验证要求": "verification",
    "Human Gate": "human_gate",
    "Stop Conditions": "stop_conditions",
}
_REASON_BY_ROLE = {
    "applicability_scope": "applicability-scope-companion",
    "verification": "verification-companion",
    "human_gate": "human-gate-companion",
    "stop_conditions": "stop-conditions-companion",
}
_QUALIFICATION_LOCATOR = "specs/01-规范模型基础规范.md#6.2-进入当前规则源的条件"


class SpecificationContextSelectionError(ValueError):
    """The exact context request is invalid after inspecting its source identity."""

    def __init__(self, problems: tuple[str, ...], *, sources: tuple[JsonObject, ...] = ()) -> None:
        super().__init__("specification context selection is invalid")
        self.problems = problems
        self.sources = sources


class _ContextCompositionFailure(RuntimeError):
    def __init__(self, summary: str, *, sources: tuple[JsonObject, ...]) -> None:
        super().__init__(summary)
        self.summary = summary
        self.sources = sources


@dataclass(frozen=True, slots=True)
class SpecificationContextReadResult:
    items: tuple[JsonObject, ...] | None
    requested_scope: tuple[JsonObject, ...]
    completed_scope: tuple[JsonObject, ...]
    not_completed_scope: tuple[JsonObject, ...]
    sources: tuple[JsonObject, ...]
    disclosure_parts: tuple[JsonObject, ...]
    verification: tuple[JsonObject, ...]
    gaps: tuple[JsonObject, ...]
    diagnostics: tuple[JsonObject, ...]
    suggested_outcome: SuggestedOutcome


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _deduplicate(objects: list[JsonObject]) -> tuple[JsonObject, ...]:
    results: list[JsonObject] = []
    seen: set[str] = set()
    for item in objects:
        identity = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if identity not in seen:
            seen.add(identity)
            results.append(item)
    return tuple(results)


def _document_for_key(repository: RepositoryInspection, key: str) -> FormalDocument | None:
    matches = [
        document
        for document in repository.active_documents_passing_implemented_checks
        if document.key == key
    ]
    return matches[0] if len(matches) == 1 else None


def _source_for_scope(document: FormalDocument, repository: RepositoryInspection) -> JsonObject:
    assert repository.source_identity is not None
    location = document.field_locations.get("scope")
    if location is None or location.line is None or document.scope is None:
        raise _ContextCompositionFailure(
            f"职责标识符 {document.key!r} 缺少可精确回指的 YAML scope 字段",
            sources=(source_reference("rule", document.canonical_path),),
        )
    observed_at = document.markdown.observed_at
    if observed_at is None:
        raise _ContextCompositionFailure(
            f"职责标识符 {document.key!r} 缺少同一规则源快照的观察时间",
            sources=(source_reference("rule", document.canonical_path),),
        )
    generated = source_reference(
        "rule",
        f"{document.canonical_path}#L{location.line}-L{location.line}",
        responsibility_key=document.key,
        path=document.canonical_path,
        heading_path=None,
        start_line=location.line,
        end_line=location.line,
    )
    generated["observed_at"] = observed_at
    assert isinstance(generated, GeneratedSourceReference)
    return RuleReferenceBinder(repository.source_identity, (document,)).bind(generated)


def _structural_role(title: str) -> str | None:
    match = NUMBERED_H2.fullmatch(title)
    return None if match is None else _ROLE_BY_TITLE.get(match.group("title"))


def _heading_outline(document: FormalDocument) -> list[JsonObject]:
    headings = document.markdown.headings
    results: list[JsonObject] = []
    current_h2: str | None = None
    for heading in headings:
        if heading.level == 2:
            current_h2 = heading.title
            path = [heading.title]
        else:
            if current_h2 is None:
                continue
            path = [current_h2, heading.title]
        end_line = min(
            (
                candidate.line - 1
                for candidate in headings
                if candidate.line > heading.line and candidate.level <= heading.level
            ),
            default=len(document.markdown.raw_lines),
        )
        results.append(
            {
                "heading_path": path,
                "start_line": heading.line,
                "end_line": end_line,
                "structural_role": (
                    None
                    if heading.level != 2
                    or (document.kind == "root" and _structural_role(heading.title) == "applicability_scope")
                    else _structural_role(heading.title)
                ),
            }
        )
    return results


def _companion_paths(document: FormalDocument) -> dict[tuple[str, ...], str]:
    required_titles = (("适用范围",) if document.kind == "spec" else ()) + FIXED_TAIL
    results: dict[tuple[str, ...], str] = {}
    for required_title in required_titles:
        matches = [
            heading
            for heading in document.markdown.headings
            if heading.level == 2 and _structural_role(heading.title) == _ROLE_BY_TITLE[required_title]
        ]
        if len(matches) != 1:
            raise _ContextCompositionFailure(
                f"职责标识符 {document.key!r} 的结构角色 {required_title!r} 无法精确唯一匹配",
                sources=(source_reference("rule", document.canonical_path),),
            )
        results[(matches[0].title,)] = _ROLE_BY_TITLE[required_title]
    return results


def _qualification_probe(
    repository: RepositoryInspection,
    selection: SpecificationContextSelection,
    *,
    response_profile: Literal["compact", "diagnostic"],
) -> SpecificationContentReadResult:
    try:
        return read_specification_content(
            repository,
            request=SpecificationContentRequest(
                selections=(SpecificationContentSelection(selection.responsibility_key, None),),
                disclosure="L4",
            ),
            response_profile=response_profile,
        )
    except SpecificationContentSelectionError as error:
        raise SpecificationContextSelectionError(error.problems, sources=error.sources) from error


def _unfinished_from_probe(
    probe: SpecificationContentReadResult,
    scope: JsonObject,
) -> tuple[SuggestedOutcome, list[JsonObject], list[JsonObject]]:
    outcome = probe.suggested_outcome
    assert outcome in {"rejected", "unavailable", "error"}
    gaps = [{**gap, "scope": [scope]} for gap in probe.gaps]
    return outcome, gaps, list(probe.diagnostics)


def _mapped_content_gap(
    gap: JsonObject,
    scope: JsonObject,
    *,
    qualification_member_count: int | None,
) -> JsonObject:
    mapped = {**gap, "scope": [scope]}
    source_refs = gap.get("source_refs", [])
    if isinstance(source_refs, list) and any(
        isinstance(source, dict) and source.get("locator") == _QUALIFICATION_LOCATOR
        for source in source_refs
    ):
        mapped["code"] = "qualification_unproven"
        if qualification_member_count is not None:
            mapped["member_count"] = qualification_member_count
    return mapped


def _parts_for_context(
    repository: RepositoryInspection,
    document: FormalDocument,
    selection: SpecificationContextSelection,
    companion_paths: dict[tuple[str, ...], str],
    *,
    response_profile: Literal["compact", "diagnostic"],
) -> tuple[list[JsonObject], SpecificationContentReadResult]:
    selected: list[tuple[tuple[str, ...], str]] = []
    for path in selection.primary_heading_paths:
        companion = next(
            (
                role
                for companion_path, role in companion_paths.items()
                if path[: len(companion_path)] == companion_path
            ),
            None,
        )
        if companion is None:
            selected.append((path, "explicit-primary"))
    selected.extend((path, _REASON_BY_ROLE[role]) for path, role in companion_paths.items())

    content_request = SpecificationContentRequest(
        selections=tuple(SpecificationContentSelection(document.key, path) for path, _reason in selected),
        disclosure="L3",
    )
    try:
        content = read_specification_content(repository, request=content_request, response_profile=response_profile)
    except SpecificationContentSelectionError as error:
        raise SpecificationContextSelectionError(error.problems, sources=error.sources) from error
    except ValueError as error:
        raise _ContextCompositionFailure(
            f"职责标识符 {document.key!r} 无法证明组合内容来自同一规则源快照",
            sources=(source_reference("rule", document.canonical_path),),
        ) from error
    if content.items is None or len(content.completed_scope) != len(content_request.selections):
        return [], content

    parts_by_range: dict[tuple[int, int], JsonObject] = {}
    for item, (_path, inclusion_reason) in zip(content.items, selected, strict=True):
        raw_parts = item["parts"]
        assert isinstance(raw_parts, list)
        for raw_part in raw_parts:
            assert isinstance(raw_part, dict)
            part = {**raw_part, "inclusion_reason": inclusion_reason}
            part["content_sha256"] = _sha256(str(part["content"]))
            identity = (int(part["start_line"]), int(part["end_line"]))
            existing = parts_by_range.get(identity)
            if existing is None or inclusion_reason != "explicit-primary":
                parts_by_range[identity] = part
    return sorted(parts_by_range.values(), key=lambda part: (int(part["start_line"]), int(part["end_line"]))), content


def _failure_outcome(outcomes: list[SuggestedOutcome]) -> SuggestedOutcome:
    if "error" in outcomes:
        return "error"
    if "rejected" in outcomes:
        return "rejected"
    return "unavailable"


def read_specification_context(
    repository: RepositoryInspection,
    *,
    request: SpecificationContextRequest,
    response_profile: Literal["compact", "diagnostic"] = "compact",
) -> SpecificationContextReadResult:
    """Return atomic context items without making semantic applicability decisions."""

    requested_scope = tuple(selection.as_scope() for selection in request.contexts)
    completed_scope: list[JsonObject] = []
    not_completed_scope: list[JsonObject] = []
    items: list[JsonObject] = []
    sources: list[JsonObject] = []
    disclosure_parts: list[JsonObject] = []
    verification: list[JsonObject] = []
    gaps: list[JsonObject] = []
    diagnostics: list[JsonObject] = []
    failed_outcomes: list[SuggestedOutcome] = []

    for selection in request.contexts:
        scope = selection.as_scope()
        parsed_matches = [
            document for document in repository.parsed_documents if document.key == selection.responsibility_key
        ]
        if len(parsed_matches) == 1 and parsed_matches[0].kind == "attachment":
            attachment = parsed_matches[0]
            raise SpecificationContextSelectionError(
                (f"职责标识符 {attachment.key!r} 是附件；本操作只接受根规范或普通规范",),
                sources=(source_reference("rule", attachment.canonical_path),),
            )
        document = _document_for_key(repository, selection.responsibility_key)
        if document is None:
            outcome, failure_gaps, failure_diagnostics = _unfinished_from_probe(
                _qualification_probe(repository, selection, response_profile=response_profile),
                scope,
            )
            failed_outcomes.append(outcome)
            not_completed_scope.append(scope)
            gaps.extend(failure_gaps)
            diagnostics.extend(failure_diagnostics)
            continue
        assert document.kind != "attachment"

        try:
            companion_paths = _companion_paths(document)
            parts, content = _parts_for_context(
                repository,
                document,
                selection,
                companion_paths,
                response_profile=response_profile,
            )
            scope_source = _source_for_scope(document, repository)
        except _ContextCompositionFailure as error:
            failed_outcomes.append("error")
            not_completed_scope.append(scope)
            gaps.append(
                {
                    "summary": error.summary,
                    "scope": [scope],
                    "source_refs": list(error.sources),
                }
            )
            diagnostics.append(
                {
                    "summary": "规范上下文组合所需的同源结构无法完整形成",
                    "details": {"responsibility_key": document.key},
                    "source_refs": list(error.sources),
                }
            )
            continue
        if not parts:
            outcome, failure_gaps, failure_diagnostics = _unfinished_from_probe(content, scope)
            failed_outcomes.append(outcome)
            not_completed_scope.append(scope)
            gaps.extend(failure_gaps)
            diagnostics.extend(failure_diagnostics)
            continue

        item_sources = [scope_source]
        for part in parts:
            part_source = part["source"]
            assert isinstance(part_source, dict)
            item_sources.append(part_source)
        sources.extend(item_sources)
        disclosure_parts.append(
            {
                "level": "L1",
                "source_refs": [scope_source],
                "reason": "返回当前载体 YAML scope 的概览，不替代正文适用范围",
            }
        )
        disclosure_parts.extend(
            {
                "level": "L3",
                "source_refs": [part["source"]],
                "reason": "按精确标题机械边界返回主规则或同源边界伴随原文",
            }
            for part in parts
        )
        coverage = {
            "applicability_scope": "returned" if document.kind == "spec" else "not_applicable",
            "verification": "returned",
            "human_gate": "returned",
            "stop_conditions": "returned",
        }
        items.append(
            {
                "responsibility_key": document.key,
                "kind": document.kind,
                "id": document.current_id,
                "title": document.title,
                "path": document.canonical_path,
                "overview_scope": document.scope,
                "heading_outline": _heading_outline(document),
                "primary_heading_paths": [list(path) for path in selection.primary_heading_paths],
                "parts": parts,
                "guard_coverage": coverage,
                "source_content_sha256": _sha256(document.markdown.raw_text),
            }
        )
        completed_scope.append(scope)
        qualification_member_count = (
            len(tuple(dict.fromkeys(repository.unchecked_conditions)))
            if response_profile == "compact" and repository.unchecked_conditions
            else None
        )
        gaps.extend(
            _mapped_content_gap(
                gap,
                scope,
                qualification_member_count=qualification_member_count,
            )
            for gap in content.gaps
        )
        if response_profile == "diagnostic":
            verification.append(
                {
                    "check": f"{document.key} 的身份、结构、标题边界、同源组合与内容摘要机械检查已执行并通过",
                    "status": "passed",
                    "scope": [scope],
                    "evidence": item_sources,
                }
            )

    if completed_scope and response_profile == "compact":
        verification.append(
                {
                    "check": (
                        f"{len(completed_scope)} 个规范上下文的同源结构、标题边界与摘要"
                        "机械检查已执行并通过（集合结果）"
                    ),
                "status": "passed",
                "scope": list(completed_scope),
                "evidence": list(_deduplicate(sources)),
            }
        )

    if completed_scope and not_completed_scope:
        outcome: SuggestedOutcome = "partial"
    elif completed_scope:
        outcome = "ok"
    else:
        outcome = _failure_outcome(failed_outcomes)

    return SpecificationContextReadResult(
        items=tuple(items) if items else None,
        requested_scope=requested_scope,
        completed_scope=tuple(completed_scope),
        not_completed_scope=tuple(not_completed_scope),
        sources=_deduplicate(sources),
        disclosure_parts=tuple(disclosure_parts),
        verification=tuple(verification),
        gaps=tuple(gaps),
        diagnostics=tuple(diagnostics),
        suggested_outcome=outcome,
    )


__all__ = [
    "SpecificationContextReadResult",
    "SpecificationContextSelectionError",
    "read_specification_context",
]
