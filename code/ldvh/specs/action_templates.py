"""Deterministic inspection of action-template declaration sources.

The declaration table is only a machine-readable discovery candidate.  This
module does not decide semantic applicability, authorization, executability,
or whether the admission conditions in the action-template foundation hold.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.identity import KEY_PATTERN, FormalDocument
from ldvh.specs.markdown import Heading, MarkdownTable, parse_table_after_heading
from ldvh.specs.repository import RepositoryInspection

DECLARATION_HEADING = "行动模板声明"
DECLARATION_HEADERS = ("template_key", "summary", "activation_hint", "definition_ref")
ACTION_TEMPLATE_UNCHECKED_CONDITIONS = ("行动模板的重复价值、稳定剩余结构、承载位置、独立失败和净价值是否满足准入条件",)


@dataclass(frozen=True, slots=True)
class ActionTemplateDeclaration:
    """One mechanically valid declaration with its exact source range."""

    template_key: str
    summary: str
    activation_hint: str
    source_key: str
    definition_heading: Heading
    definition_start_line: int
    definition_end_line: int
    document: FormalDocument
    source: SourceLocation


@dataclass(frozen=True, slots=True)
class _ObservedTemplateKey:
    template_key: str
    source_key: str
    source: SourceLocation


@dataclass(frozen=True, slots=True)
class ActionTemplateSourceInspection:
    """Mechanically accepted candidates plus incomplete-source diagnostics."""

    candidate_declarations: tuple[ActionTemplateDeclaration, ...]
    issues: tuple[Issue, ...]
    incomplete_sources: tuple[str, ...]
    unchecked_conditions: tuple[str, ...]


def _issue(document: FormalDocument, summary: str, *, line: int | None = None) -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(document.canonical_path, line),
        affected=(document.key,),
    )


def _definition_range(document: FormalDocument, heading: Heading) -> tuple[int, int]:
    following_boundaries = (
        candidate.line
        for candidate in document.markdown.headings
        if candidate.line > heading.line and candidate.level <= heading.level
    )
    end_line = min(following_boundaries, default=len(document.markdown.raw_lines) + 1) - 1
    return heading.line, end_line


def _definition_heading(
    document: FormalDocument,
    template_key: str,
    definition_ref: str,
    issues: list[Issue],
    line: int,
) -> Heading | None:
    parts = definition_ref.split("::")
    if len(parts) != 2 or parts[0] != document.key or not parts[1]:
        issues.append(_issue(document, f"行动模板 {template_key!r} 的 definition_ref 无效", line=line))
        return None
    target_title = parts[1]
    matches = tuple(
        heading for heading in document.markdown.headings if heading.level in {2, 3} and heading.title == target_title
    )
    if len(matches) != 1:
        issues.append(
            _issue(document, f"行动模板 {template_key!r} 的 definition_ref 必须唯一指向同来源 H2 或 H3", line=line)
        )
        return None
    if matches[0].level == 3 and matches[0].title == DECLARATION_HEADING:
        issues.append(_issue(document, f"行动模板 {template_key!r} 的 definition_ref 不得指向声明 H3 自身", line=line))
        return None
    return matches[0]


def _source_declarations(
    document: FormalDocument,
) -> tuple[list[ActionTemplateDeclaration], list[_ObservedTemplateKey], list[Issue], bool]:
    headings = document.markdown.find_headings(DECLARATION_HEADING, level=3)
    if not headings:
        return [], [], [], True
    if document.kind != "spec":
        return [], [], [_issue(document, "只有普通 spec 可以包含行动模板声明", line=headings[0].line)], False
    if len(headings) != 1:
        return [], [], [_issue(document, "同一来源至多包含一个精确的行动模板声明 H3", line=headings[1].line)], False

    heading = headings[0]
    table: MarkdownTable | None = parse_table_after_heading(document.markdown, heading)
    if table is None:
        return [], [], [_issue(document, "行动模板声明 H3 后必须紧接固定 Markdown 表格", line=heading.line)], False
    if table.headers != DECLARATION_HEADERS:
        return [], [], [_issue(document, "行动模板声明表头与固定字段不一致", line=table.line)], False
    if not table.rows:
        return [], [], [_issue(document, "行动模板声明表至少包含一个数据行", line=table.line)], False

    following_heading_lines = [item.line for item in document.markdown.headings if item.line > heading.line]
    section_end = min(following_heading_lines, default=len(document.markdown.raw_lines) + 1)
    table_last_line = table.line + 1 + len(table.rows)
    trailing_content = tuple(
        line.strip() for line in document.markdown.raw_lines[table_last_line : section_end - 1] if line.strip()
    )
    if trailing_content:
        return [], [], [_issue(document, "行动模板声明 H3 只能包含唯一声明表", line=table_last_line + 1)], False

    declarations: list[ActionTemplateDeclaration] = []
    observed_keys: list[_ObservedTemplateKey] = []
    issues: list[Issue] = []
    complete = True
    for row_index, row in enumerate(table.rows, start=2):
        line = table.line + row_index
        if len(row) == len(DECLARATION_HEADERS) and row[0]:
            observed_keys.append(
                _ObservedTemplateKey(
                    template_key=row[0],
                    source_key=document.key,
                    source=SourceLocation(document.canonical_path, line, DECLARATION_HEADING),
                )
            )
        if len(row) != len(DECLARATION_HEADERS) or any(not cell for cell in row):
            issues.append(_issue(document, "行动模板声明行必须恰有四个非空单元格", line=line))
            complete = False
            continue
        template_key, summary, activation_hint, definition_ref = row
        row_valid = True
        if KEY_PATTERN.fullmatch(template_key) is None:
            issues.append(_issue(document, f"template_key {template_key!r} 格式无效", line=line))
            row_valid = False
        definition_heading = _definition_heading(document, template_key, definition_ref, issues, line)
        if definition_heading is None:
            row_valid = False
        if not row_valid:
            complete = False
            continue
        assert definition_heading is not None
        definition_start_line, definition_end_line = _definition_range(document, definition_heading)
        declarations.append(
            ActionTemplateDeclaration(
                template_key=template_key,
                summary=summary,
                activation_hint=activation_hint,
                source_key=document.key,
                definition_heading=definition_heading,
                definition_start_line=definition_start_line,
                definition_end_line=definition_end_line,
                document=document,
                source=SourceLocation(document.canonical_path, line, DECLARATION_HEADING),
            )
        )
    return declarations, observed_keys, issues, complete


def _duplicate_template_keys(observed_keys: Iterable[_ObservedTemplateKey]) -> set[str]:
    return {key for key, count in Counter(item.template_key for item in observed_keys).items() if count > 1}


def inspect_action_template_sources(repository: RepositoryInspection) -> ActionTemplateSourceInspection:
    """Inspect active declaration sources without claiming semantic admission."""

    declarations: list[ActionTemplateDeclaration] = []
    observed_keys: list[_ObservedTemplateKey] = []
    issues: list[Issue] = list(repository.issues)
    incomplete: set[str] = set(repository.incomplete_scope)
    for document in repository.active_documents_passing_implemented_checks:
        source_declarations, source_observed_keys, source_issues, complete = _source_declarations(document)
        declarations.extend(source_declarations)
        observed_keys.extend(source_observed_keys)
        issues.extend(source_issues)
        if not complete:
            incomplete.add(document.key)

    duplicate_keys = _duplicate_template_keys(observed_keys)
    if duplicate_keys:
        declarations = [item for item in declarations if item.template_key not in duplicate_keys]
        for observed in observed_keys:
            if observed.template_key not in duplicate_keys:
                continue
            issues.append(
                Issue(
                    summary=f"template_key {observed.template_key!r} 在本次声明候选中重复",
                    location=observed.source,
                    affected=(observed.source_key, observed.template_key),
                )
            )
            incomplete.add(observed.source_key)

    return ActionTemplateSourceInspection(
        candidate_declarations=tuple(sorted(declarations, key=lambda item: item.template_key)),
        issues=tuple(issues),
        incomplete_sources=tuple(sorted(incomplete)),
        unchecked_conditions=repository.unchecked_conditions + ACTION_TEMPLATE_UNCHECKED_CONDITIONS,
    )
