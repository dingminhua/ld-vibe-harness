"""Read exact specification content from one already-inspected rule source."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from ldvh.diagnostics import Issue
from ldvh.helper.operations.specification_content_request import (
    SpecificationContentRequest,
    SpecificationContentSelection,
)
from ldvh.helper.responses import source_reference
from ldvh.helper.source_refs import GeneratedSourceReference, RuleReferenceBinder
from ldvh.specs.identity import FormalDocument
from ldvh.specs.repository import RepositoryInspection
from ldvh.specs.source import RuleSourceIdentity

type JsonObject = dict[str, object]
SuggestedOutcome = Literal["ok", "partial", "rejected", "unavailable", "error"]
FailureKind = Literal["rejected", "unavailable", "error"]

_QUALIFICATION_SOURCE: JsonObject = source_reference(
    "rule",
    "specs/01-规范模型基础规范.md#6.2-进入当前规则源的条件",
)


class SpecificationContentSelectionError(ValueError):
    """The exact selection cannot be established after its source is known."""

    def __init__(self, problems: tuple[str, ...], *, sources: tuple[JsonObject, ...] = ()) -> None:
        super().__init__("specification content selection is invalid")
        self.problems = problems
        self.sources = sources


@dataclass(frozen=True, slots=True)
class SpecificationContentReadResult:
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


@dataclass(frozen=True, slots=True)
class _UnfinishedSelection:
    selection: SpecificationContentSelection
    kind: FailureKind
    summary: str
    sources: tuple[JsonObject, ...] = ()
    issues: tuple[Issue, ...] = ()


def _simple_source(path: str, *, line: int | None = None) -> JsonObject:
    locator = path if line is None else f"{path}#L{line}"
    return source_reference("rule", locator)


def _fixed_source(document: FormalDocument, identity: RuleSourceIdentity) -> JsonObject:
    end_line = len(document.markdown.raw_lines)
    path = document.canonical_path
    observed_at = document.markdown.observed_at
    if observed_at is None:
        raise ValueError("inspected Markdown source is missing its observation time")
    source = source_reference(
        "rule",
        f"{path}#L1-L{end_line}",
        responsibility_key=document.key,
        path=path,
        heading_path=None,
        start_line=1,
        end_line=end_line,
    )
    source["observed_at"] = observed_at
    assert isinstance(source, GeneratedSourceReference)
    return RuleReferenceBinder(identity, (document,)).bind(source)


def _full_part(
    document: FormalDocument,
    *,
    identity: RuleSourceIdentity,
    inclusion_reason: str,
) -> JsonObject:
    source = _fixed_source(document, identity)
    return {
        "level": "L4",
        "heading_path": None,
        "start_line": 1,
        "end_line": len(document.markdown.raw_lines),
        "content": document.markdown.raw_text,
        "inclusion_reason": inclusion_reason,
        "source": source,
    }


def _section_part(
    document: FormalDocument,
    *,
    identity: RuleSourceIdentity,
    heading_path: tuple[str, ...],
) -> tuple[JsonObject, ...]:
    headings = document.markdown.headings
    h2 = next(heading for heading in headings if heading.level == 2 and heading.title == heading_path[0])
    next_h2 = min(
        (heading.line for heading in headings if heading.level == 2 and heading.line > h2.line),
        default=len(document.markdown.raw_lines) + 1,
    )

    ranges: list[tuple[tuple[str, ...], int, int, str]] = []
    if len(heading_path) == 1:
        ranges.append((heading_path, h2.line, next_h2 - 1, "按精确 H2 机械边界返回所选原文切片"))
    else:
        h3s = [heading for heading in headings if heading.level == 3 and h2.line < heading.line < next_h2]
        target = next(heading for heading in h3s if heading.title == heading_path[1])
        first_h3_line = min(heading.line for heading in h3s)
        ranges.append(
            (
                (heading_path[0],),
                h2.line,
                first_h3_line - 1,
                "返回所属 H2 标题及首个 H3 前对各子节共同适用的原文",
            )
        )
        next_peer = min(
            (heading.line for heading in headings if heading.line > target.line and heading.level in (2, 3)),
            default=len(document.markdown.raw_lines) + 1,
        )
        ranges.append(
            (
                heading_path,
                target.line,
                next_peer - 1,
                "按精确 H3 机械边界返回所选原文切片",
            )
        )

    raw_lines = document.markdown.raw_text.splitlines(keepends=True)
    observed_at = document.markdown.observed_at
    if observed_at is None:
        raise ValueError("inspected Markdown source is missing its observation time")
    parts: list[JsonObject] = []
    for path, start_line, end_line, reason in ranges:
        source: JsonObject = source_reference(
            "rule",
            f"{document.canonical_path}#L{start_line}-L{end_line}",
            responsibility_key=document.key,
            path=document.canonical_path,
            heading_path=list(path),
            start_line=start_line,
            end_line=end_line,
        )
        source["observed_at"] = observed_at
        assert isinstance(source, GeneratedSourceReference)
        source = RuleReferenceBinder(identity, (document,)).bind(source)
        parts.append(
            {
                "level": "L3",
                "heading_path": list(path),
                "start_line": start_line,
                "end_line": end_line,
                "content": "".join(raw_lines[start_line - 1 : end_line]),
                "inclusion_reason": reason,
                "source": source,
            }
        )
    return tuple(parts)


def _deduplicate_sources(sources: list[JsonObject]) -> tuple[JsonObject, ...]:
    results: list[JsonObject] = []
    seen: set[str] = set()
    for source in sources:
        identity = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if identity not in seen:
            seen.add(identity)
            results.append(source)
    return tuple(results)


def _issue_source(issue: Issue) -> JsonObject:
    return _simple_source(issue.location.path, line=issue.location.line)


def _relevant_issues(repository: RepositoryInspection, key: str, paths: set[str]) -> tuple[Issue, ...]:
    return tuple(
        issue
        for issue in repository.issues
        if key in issue.affected or issue.location.path in paths or issue.location.path == key
    )


def _validate_heading_path(document: FormalDocument, selection: SpecificationContentSelection) -> None:
    assert selection.heading_path is not None
    path = selection.heading_path
    h2_matches = tuple(
        heading for heading in document.markdown.headings if heading.level == 2 and heading.title == path[0]
    )
    source = _simple_source(document.canonical_path)
    if len(h2_matches) != 1:
        raise SpecificationContentSelectionError(
            (f"职责标识符 {selection.responsibility_key!r} 中的 H2 无法精确唯一匹配: {path[0]!r}",),
            sources=(source,),
        )
    if len(path) == 1:
        return

    h2 = h2_matches[0]
    following_h2_lines = [
        heading.line for heading in document.markdown.headings if heading.level == 2 and heading.line > h2.line
    ]
    h2_end = min(following_h2_lines, default=len(document.markdown.raw_lines) + 1)
    h3_matches = tuple(
        heading
        for heading in document.markdown.headings
        if heading.level == 3 and h2.line < heading.line < h2_end and heading.title == path[1]
    )
    if len(h3_matches) != 1:
        raise SpecificationContentSelectionError(
            (f"职责标识符 {selection.responsibility_key!r} 的 H2 {path[0]!r} 中 H3 无法精确唯一匹配: {path[1]!r}",),
            sources=(source,),
        )


def _selection_target(
    repository: RepositoryInspection,
    selection: SpecificationContentSelection,
) -> FormalDocument | _UnfinishedSelection:
    passing = [
        document
        for document in repository.active_documents_passing_implemented_checks
        if document.key == selection.responsibility_key
    ]
    if len(passing) == 1:
        document = passing[0]
        if selection.heading_path is not None:
            _validate_heading_path(document, selection)
        return document
    if len(passing) > 1:
        return _UnfinishedSelection(
            selection,
            "error",
            "当前规则源中职责标识符不唯一，无法按契约确定目标来源身份与范围",
        )

    parsed = [document for document in repository.parsed_documents if document.key == selection.responsibility_key]
    if parsed:
        paths = {document.canonical_path for document in parsed}
        issues = _relevant_issues(repository, selection.responsibility_key, paths)
        sources = tuple(_simple_source(path) for path in sorted(paths))
        if len(parsed) > 1:
            return _UnfinishedSelection(
                selection,
                "error",
                "当前规则源中存在重复职责标识符，无法按契约确定目标来源身份与范围",
                sources=sources,
                issues=issues,
            )
        if parsed[0].status != "active":
            raise SpecificationContentSelectionError(
                (
                    f"职责标识符 {selection.responsibility_key!r} 当前声明为 "
                    f"{parsed[0].status!r}，无法在允许选择的 active 载体集合中精确匹配",
                ),
                sources=sources,
            )
        return _UnfinishedSelection(
            selection,
            "rejected",
            "active 目标载体已解析，但适用的已实现关系或授权检查未通过，Stop Conditions 禁止读取",
            sources=sources,
            issues=issues,
        )

    if repository.issues or repository.incomplete_scope:
        issues = tuple(repository.issues)
        return _UnfinishedSelection(
            selection,
            "error",
            "当前规则源存在未完成范围，无法确定请求的职责标识符是否因来源失败而未被识别",
            sources=tuple(_issue_source(issue) for issue in issues),
            issues=issues,
        )

    raise SpecificationContentSelectionError((f"未精确匹配职责标识符 {selection.responsibility_key!r}",))


def _parts_for_document(
    document: FormalDocument,
    *,
    repository: RepositoryInspection,
    selection: SpecificationContentSelection,
    disclosure: Literal["L3", "L4"],
) -> tuple[JsonObject, ...] | _UnfinishedSelection:
    assert repository.source_identity is not None
    identity = repository.source_identity
    if document.kind != "attachment" and disclosure == "L3":
        assert selection.heading_path is not None
        return _section_part(
            document,
            identity=identity,
            heading_path=selection.heading_path,
        )
    if document.kind != "attachment":
        return (
            _full_part(
                document,
                identity=identity,
                inclusion_reason="请求 L4，纳入完整来源",
            ),
        )

    parents = tuple(
        candidate
        for candidate in repository.active_documents_passing_implemented_checks
        if document.key in candidate.authorized_attachments
    )
    if len(parents) != 1:
        source = _simple_source(document.canonical_path)
        return _UnfinishedSelection(
            SpecificationContentSelection(document.key, None),
            "rejected",
            "授权附件缺少通过适用已实现检查的当前唯一父规范，Stop Conditions 禁止完整读取",
            sources=(source,),
        )
    parent = parents[0]
    if disclosure == "L3":
        assert selection.heading_path is not None
        return _section_part(
            document,
            identity=identity,
            heading_path=selection.heading_path,
        )
    return (
        _full_part(
            document,
            identity=identity,
            inclusion_reason="请求 L4，纳入授权附件完整来源",
        ),
        _full_part(
            parent,
            identity=identity,
            inclusion_reason="请求 L4，纳入授权该附件的当前唯一父规范完整来源",
        ),
    )


def _failure_outcome(failures: list[_UnfinishedSelection]) -> SuggestedOutcome:
    kinds = {failure.kind for failure in failures}
    if "error" in kinds:
        return "error"
    if "rejected" in kinds:
        return "rejected"
    return "unavailable"


def read_specification_content(
    repository: RepositoryInspection,
    *,
    request: SpecificationContentRequest,
    response_profile: Literal["compact", "diagnostic"] = "compact",
) -> SpecificationContentReadResult:
    """Read an exact L3 mechanical slice or the complete L4 source."""

    targets = [_selection_target(repository, selection) for selection in request.selections]
    requested_scope = tuple(selection.as_scope() for selection in request.selections)
    completed_scope: list[JsonObject] = []
    not_completed_scope: list[JsonObject] = []
    items: list[JsonObject] = []
    sources: list[JsonObject] = []
    disclosure_parts: list[JsonObject] = []
    verification: list[JsonObject] = []
    gaps: list[JsonObject] = []
    diagnostics: list[JsonObject] = []
    failures: list[_UnfinishedSelection] = []

    for selection, target in zip(request.selections, targets, strict=True):
        if isinstance(target, _UnfinishedSelection):
            failures.append(target)
            not_completed_scope.append(selection.as_scope())
            gaps.append(
                {
                    "summary": target.summary,
                    "scope": [selection.as_scope()],
                    "source_refs": list(_deduplicate_sources(list(target.sources))),
                }
            )
            diagnostics.extend(
                {
                    "summary": issue.summary,
                    "details": {
                        "path": issue.location.path,
                        "line": issue.location.line,
                        "affected": list(issue.affected),
                    },
                    "source_refs": [_issue_source(issue)],
                }
                for issue in target.issues
            )
            continue

        parts = _parts_for_document(
            target,
            repository=repository,
            selection=selection,
            disclosure=request.disclosure,
        )
        if isinstance(parts, _UnfinishedSelection):
            failure = _UnfinishedSelection(
                selection,
                parts.kind,
                parts.summary,
                sources=parts.sources,
                issues=parts.issues,
            )
            failures.append(failure)
            not_completed_scope.append(selection.as_scope())
            gaps.append(
                {
                    "summary": failure.summary,
                    "scope": [selection.as_scope()],
                    "source_refs": list(failure.sources),
                }
            )
            continue

        part_list = list(parts)
        item = {
            "selection": selection.as_scope(),
            "kind": target.kind,
            "key": target.key,
            "id": target.current_id,
            "title": target.title,
            "status": target.status,
            "path": target.canonical_path,
            "requested_disclosure": request.disclosure,
            "actual_disclosure": request.disclosure,
            "parts": part_list,
        }
        items.append(item)
        completed_scope.append(selection.as_scope())
        for part in part_list:
            source = part["source"]
            assert isinstance(source, dict)
            sources.append(source)
            reason = (
                "请求 L3，按精确标题机械边界返回原文切片"
                if request.disclosure == "L3"
                else "请求 L4，按契约返回完整来源"
            )
            disclosure_parts.append({"level": request.disclosure, "source_refs": [source], "reason": reason})
        if response_profile == "diagnostic":
            verification.append(
                {
                    "check": f"当前实现中适用于 {target.key} 的身份、结构、授权和读取检查已执行并通过",
                    "status": "passed",
                    "scope": [selection.as_scope()],
                    "evidence": [part["source"] for part in part_list],
                }
            )

    if completed_scope:
        unchecked = tuple(dict.fromkeys(repository.unchecked_conditions))
        if unchecked and response_profile in {"compact", "lean"}:
            gaps.append(
                {
                    "summary": (
                        f"尚未由 Code 机械证明 {len(unchecked)} 项当前规则源资格条件；请求 diagnostic 档可读取逐项明细"
                    ),
                    "scope": list(completed_scope),
                    "source_refs": [_QUALIFICATION_SOURCE.copy()],
                }
            )
        else:
            gaps.extend(
                {
                    "summary": f"尚未由 Code 机械证明当前规则源资格条件：{condition}",
                    "scope": list(completed_scope),
                    "source_refs": [_QUALIFICATION_SOURCE.copy()],
                }
                for condition in unchecked
            )
        if response_profile in {"compact", "lean"}:
            verification.append(
                {
                    "check": (
                        f"当前实现中适用于 {len(completed_scope)} 个完成选择的身份、结构、授权和读取检查"
                        "已执行并通过（集合结果）"
                    ),
                    "status": "passed",
                    "scope": list(completed_scope),
                    "evidence": list(_deduplicate_sources(sources)),
                }
            )

    if completed_scope and failures:
        outcome: SuggestedOutcome = "partial"
    elif completed_scope:
        outcome = "ok"
    else:
        outcome = _failure_outcome(failures)

    return SpecificationContentReadResult(
        items=tuple(items) if items else None,
        requested_scope=requested_scope,
        completed_scope=tuple(completed_scope),
        not_completed_scope=tuple(not_completed_scope),
        sources=_deduplicate_sources(sources),
        disclosure_parts=tuple(disclosure_parts),
        verification=tuple(verification),
        gaps=tuple(gaps),
        diagnostics=tuple(diagnostics),
        suggested_outcome=outcome,
    )


__all__ = [
    "SpecificationContentReadResult",
    "SpecificationContentSelectionError",
    "read_specification_content",
]
