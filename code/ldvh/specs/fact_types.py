"""Deterministic discovery of fact-type declarations and definition ranges."""

from __future__ import annotations

from dataclasses import dataclass

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.identity import KEY_PATTERN, FormalDocument
from ldvh.specs.markdown import Heading, parse_table_after_heading

DECLARATION_HEADING = "事实类型声明"
DECLARATION_HEADERS = ("fact_type_key", "summary", "definition_ref")


@dataclass(frozen=True, slots=True)
class FactTypeDefinition:
    fact_type_key: str
    summary: str
    source_key: str
    definition_heading: Heading
    document: FormalDocument
    source: SourceLocation


@dataclass(frozen=True, slots=True)
class FactTypeInspection:
    definitions: tuple[FactTypeDefinition, ...]
    issues: tuple[Issue, ...]

    @property
    def complete(self) -> bool:
        return not self.issues


def _issue(document: FormalDocument, summary: str, *, line: int | None = None) -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(document.canonical_path, line=line),
        affected=(document.key,),
    )


def inspect_fact_types(documents: tuple[FormalDocument, ...]) -> FactTypeInspection:
    """Read exact declaration tables without inferring types from names or Code."""

    definitions: list[FactTypeDefinition] = []
    issues: list[Issue] = []
    for document in documents:
        headings = document.markdown.find_headings(DECLARATION_HEADING, level=3)
        if len(headings) > 1:
            issues.append(_issue(document, "事实类型声明 H3 在同一来源中至多出现一次", line=headings[1].line))
            continue
        if not headings:
            continue
        if document.kind != "spec":
            issues.append(_issue(document, "只有普通 spec 可以包含事实类型声明", line=headings[0].line))
            continue
        table = parse_table_after_heading(document.markdown, headings[0])
        if table is None or table.headers != DECLARATION_HEADERS:
            issues.append(_issue(document, "事实类型声明必须紧接固定三列表头", line=headings[0].line))
            continue
        if not table.rows:
            issues.append(_issue(document, "事实类型声明表至少包含一个数据行", line=table.line))
            continue
        following_heading_lines = [item.line for item in document.markdown.headings if item.line > headings[0].line]
        section_end = min(following_heading_lines, default=len(document.markdown.raw_lines) + 1)
        table_last_line = table.line + 1 + len(table.rows)
        trailing_content = tuple(
            line.strip() for line in document.markdown.raw_lines[table_last_line : section_end - 1] if line.strip()
        )
        if trailing_content:
            issues.append(_issue(document, "事实类型声明 H3 只能包含唯一声明表", line=table_last_line + 1))
        seen_in_source: set[str] = set()
        for offset, row in enumerate(table.rows, start=2):
            line = table.line + offset
            if len(row) != len(DECLARATION_HEADERS) or any(not value for value in row):
                issues.append(_issue(document, "事实类型声明行必须包含三个非空单元格", line=line))
                continue
            fact_type_key, summary, definition_ref = row
            if KEY_PATTERN.fullmatch(fact_type_key) is None:
                issues.append(_issue(document, f"非法 fact_type_key {fact_type_key!r}", line=line))
            if fact_type_key in seen_in_source:
                issues.append(_issue(document, f"同一来源重复 fact_type_key {fact_type_key!r}", line=line))
            seen_in_source.add(fact_type_key)
            reference_parts = definition_ref.split("::")
            if len(reference_parts) != 2 or reference_parts[0] != document.key or not reference_parts[1]:
                issues.append(_issue(document, f"事实类型 {fact_type_key!r} 的 definition_ref 无效", line=line))
                continue
            target_headings = document.markdown.find_headings(reference_parts[1], level=2)
            if len(target_headings) != 1:
                issues.append(
                    _issue(document, f"事实类型 {fact_type_key!r} 的 definition_ref 必须唯一指向同来源 H2", line=line)
                )
                continue
            definitions.append(
                FactTypeDefinition(
                    fact_type_key=fact_type_key,
                    summary=summary,
                    source_key=document.key,
                    definition_heading=target_headings[0],
                    document=document,
                    source=SourceLocation(document.canonical_path, line=line),
                )
            )

    by_key: dict[str, list[FactTypeDefinition]] = {}
    for definition in definitions:
        by_key.setdefault(definition.fact_type_key, []).append(definition)
    duplicated = {key for key, matches in by_key.items() if len(matches) > 1}
    for key in sorted(duplicated):
        for definition in by_key[key]:
            issues.append(
                _issue(definition.document, f"当前来源之间重复 fact_type_key {key!r}", line=definition.source.line)
            )
    accepted = tuple(definition for definition in definitions if definition.fact_type_key not in duplicated)
    return FactTypeInspection(accepted, tuple(issues))
