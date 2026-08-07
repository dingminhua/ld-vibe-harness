"""Normative H2 structure and verification-table checks."""

from __future__ import annotations

import re

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.identity import FormalDocument
from ldvh.specs.markdown import Heading, MarkdownTable, find_setext_headings, parse_table_after_heading

REGULAR_HEAD = ("价值判断", "规范依据", "职责边界", "适用范围")
FIXED_TAIL = ("验证要求", "Human Gate", "Stop Conditions")
VERIFICATION_HEADERS = ("验证对象", "验证时机", "成立条件", "可接受依据", "验证入口", "可证明范围", "未满足时的处理")
NUMBERED_H2 = re.compile(r"(?P<number>[0-9]+)\. (?P<title>.+)\Z")


def _issue(document: FormalDocument, summary: str, *, line: int | None = None) -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(document.canonical_path, line),
        affected=(document.key,),
    )


def _verification_table(document: FormalDocument, heading: Heading, next_h2_line: int) -> MarkdownTable | None:
    lines = document.markdown.raw_lines
    for one_based_line in range(heading.line + 1, next_h2_line):
        if not lines[one_based_line - 1].lstrip().startswith("|"):
            continue
        pseudo_heading = Heading(level=3, title="verification-table-anchor", line=one_based_line - 1)
        table = parse_table_after_heading(document.markdown, pseudo_heading)
        if table is not None and table.line < next_h2_line:
            return table
    return None


def validate_structure(document: FormalDocument) -> tuple[Issue, ...]:
    """Check the root or regular-spec H2 profile and verification table."""

    if document.kind == "attachment":
        return ()

    h2s = tuple(heading for heading in document.markdown.headings if heading.level == 2)
    issues: list[Issue] = []
    for heading in find_setext_headings(document.markdown):
        issues.append(
            _issue(
                document,
                f"规范正文不得使用 Setext H{heading.level}；必须使用 ATX 标题",
                line=heading.line,
            )
        )
    numbered: list[tuple[int, str, Heading]] = []
    for heading in h2s:
        match = NUMBERED_H2.fullmatch(heading.title)
        if match is None:
            issues.append(_issue(document, "全部 H2 必须使用连续阿拉伯数字编号", line=heading.line))
            continue
        numbered.append((int(match.group("number")), match.group("title"), heading))

    if not h2s:
        return (_issue(document, "规范正文必须包含 H2 章节"),)
    if len(numbered) != len(h2s):
        return tuple(issues)
    expected_numbers = list(range(1, len(numbered) + 1))
    actual_numbers = [number for number, _, _ in numbered]
    if actual_numbers != expected_numbers:
        issues.append(_issue(document, "H2 编号必须从 1 开始连续递增"))

    titles = tuple(title for _, title, _ in numbered)
    if document.kind == "spec" and titles[:4] != REGULAR_HEAD:
        issues.append(_issue(document, "普通规范的前四个 H2 必须依次为价值判断、规范依据、职责边界、适用范围"))
    fixed_tail_valid = len(titles) >= 3 and titles[-3:] == FIXED_TAIL
    if not fixed_tail_valid:
        issues.append(_issue(document, "规范固定尾部必须依次为验证要求、Human Gate、Stop Conditions"))
        if "验证要求" not in titles:
            issues.append(_issue(document, "规范缺少验证要求章节"))
        return tuple(issues)

    index = len(numbered) - len(FIXED_TAIL)
    verification_heading = numbered[index][2]
    next_h2_line = numbered[index + 1][2].line if index + 1 < len(numbered) else len(document.markdown.raw_lines) + 1
    table = _verification_table(document, verification_heading, next_h2_line)
    if table is None or table.headers != VERIFICATION_HEADERS:
        issues.append(
            _issue(
                document,
                "验证要求章节必须包含顺序精确的固定七列表格",
                line=verification_heading.line,
            )
        )
    elif not table.rows:
        issues.append(
            _issue(
                document,
                "验证要求固定七列表格必须至少包含一行",
                line=table.line,
            )
        )
    elif any(len(row) != len(VERIFICATION_HEADERS) for row in table.rows):
        issues.append(
            _issue(
                document,
                "验证要求固定七列表格的每一行都必须恰好包含七列",
                line=table.line,
            )
        )
    return tuple(issues)
