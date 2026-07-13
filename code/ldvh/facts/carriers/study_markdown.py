"""Deterministic parsing of the Study Markdown carrier."""

from __future__ import annotations

import re

from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.models import CarrierParseResult, FactIssue

STUDY_H2_TITLES = (
    "研究问题",
    "输入、方法与观察边界",
    "关键发现",
    "结论与限制",
    "建议",
    "后续分流",
)

_ATX_HEADING = re.compile(r" {0,3}(?P<marks>#{1,6})(?:[ \t]+(?P<title>.*?))?[ \t]*$")
_FENCE_OPEN = re.compile(r" {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


def parse_study_markdown(text: str) -> CarrierParseResult:
    """Parse frontmatter and mechanically validate the Study report skeleton."""

    frontmatter_text, body, split_issue = _split_frontmatter(text)
    if split_issue is not None:
        return CarrierParseResult(fields=None, body=None, issues=(split_issue,))

    fields, yaml_issue = _load_frontmatter(frontmatter_text)
    if yaml_issue is not None:
        return CarrierParseResult(fields=None, body=body, issues=(yaml_issue,))

    body_issues = _validate_body(body)
    return CarrierParseResult(fields=fields, body=body, issues=tuple(body_issues))


def _split_frontmatter(text: str) -> tuple[str, str | None, FactIssue | None]:
    lines = text.splitlines(keepends=True)
    if not lines or _line_content(lines[0]) != "---":
        return "", None, FactIssue("parse", "Study Markdown 必须以唯一 YAML frontmatter 开始")

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if _line_content(line) == "---"),
        None,
    )
    if closing_index is None:
        return "", None, FactIssue("parse", "Study Markdown 开头的 YAML frontmatter 未闭合")

    frontmatter_text = "".join(lines[1:closing_index])
    body = "".join(lines[closing_index + 1 :])
    return frontmatter_text, body, None


def _line_content(line: str) -> str:
    return line.removesuffix("\n").removesuffix("\r")


def _load_frontmatter(source: str) -> tuple[dict[str, object] | None, FactIssue | None]:
    parsed = parse_yaml_object(source)
    if parsed.fields is None:
        category = "schema" if parsed.issues and "顶层" in parsed.issues[0].summary else "parse"
        summary = (
            "Study frontmatter 顶层必须是 mapping"
            if category == "schema"
            else "Study frontmatter 无法形成唯一 YAML mapping"
        )
        return None, FactIssue(category, summary)
    return parsed.fields, None


def _validate_body(body: str) -> list[FactIssue]:
    headings = _body_headings(body)
    h2_headings = [(index, title) for index, level, title in headings if level == 2]
    issues: list[FactIssue] = []

    for _, title in h2_headings:
        if title not in STUDY_H2_TITLES:
            issues.append(
                FactIssue(
                    "schema",
                    f"Study 正文不允许固定骨架之外的 H2 {title!r}；需要展开时使用 H3",
                    field_path="body",
                )
            )

    for title in STUDY_H2_TITLES:
        count = sum(actual_title == title for _, actual_title in h2_headings)
        if count != 1:
            issues.append(
                FactIssue(
                    "schema",
                    f"Study 正文 H2 {title!r} 必须精确出现一次，实际为 {count} 次",
                    field_path="body",
                )
            )

    actual_fixed_order = [title for _, title in h2_headings if title in STUDY_H2_TITLES]
    if actual_fixed_order != list(STUDY_H2_TITLES):
        issues.append(FactIssue("schema", "Study 正文六个固定 H2 顺序不正确", field_path="body"))

    if any(issue.summary.startswith("Study 正文 H2") for issue in issues):
        return issues

    lines = body.splitlines()
    fixed_positions = {title: index for index, title in h2_headings if title in STUDY_H2_TITLES}
    all_h2_positions = [index for index, _ in h2_headings]
    for title in STUDY_H2_TITLES:
        start = fixed_positions[title] + 1
        end = next((index for index in all_h2_positions if index >= start), len(lines))
        if not _has_nonempty_section_content(lines[start:end]):
            issues.append(FactIssue("schema", f"Study 正文 H2 {title!r} 内容不得为空", field_path="body"))
    return issues


def _body_headings(body: str) -> list[tuple[int, int, str]]:
    headings: list[tuple[int, int, str]] = []
    open_fence: tuple[str, int] | None = None
    for index, line in enumerate(body.splitlines()):
        if open_fence is not None:
            marker, minimum_length = open_fence
            if re.fullmatch(rf" {{0,3}}{re.escape(marker)}{{{minimum_length},}}[ \t]*", line):
                open_fence = None
            continue

        fence = _FENCE_OPEN.fullmatch(line)
        if fence is not None:
            marks = fence.group("fence")
            open_fence = (marks[0], len(marks))
            continue

        match = _ATX_HEADING.fullmatch(line)
        if match is None:
            continue
        title = match.group("title") or ""
        title = re.sub(r"[ \t]+#+[ \t]*$", "", title).strip()
        headings.append((index, len(match.group("marks")), title))
    return headings


def _has_nonempty_section_content(lines: list[str]) -> bool:
    open_fence: tuple[str, int] | None = None
    for line in lines:
        if open_fence is not None:
            marker, minimum_length = open_fence
            if re.fullmatch(rf" {{0,3}}{re.escape(marker)}{{{minimum_length},}}[ \t]*", line):
                open_fence = None
            elif line.strip():
                return True
            continue

        fence = _FENCE_OPEN.fullmatch(line)
        if fence is not None:
            marks = fence.group("fence")
            open_fence = (marks[0], len(marks))
            continue
        if line.strip() and _ATX_HEADING.fullmatch(line) is None:
            return True
    return False
