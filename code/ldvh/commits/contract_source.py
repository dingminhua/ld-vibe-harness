"""Derive the mechanical commit contract from the active 03 source."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.identity import FormalDocument

SOURCE_KEY = "source-of-truth-traceability"
ATTACHMENT_KEY = "source-reference-enumerations"
ATTACHMENT_ID = "03.Att.01"
TYPE_HEADERS = ("type", "语义")
SCOPE_HEADERS = ("scope", "语义")
TRIGGER_HEADERS = ("trigger_key", "mechanical", "成立条件", "必需结构")
REQUIRED_TRIGGER_KEYS = (
    "all-commits-minimum-body",
    "breaking-marker",
    "high-impact",
    "insufficient-header",
    "project-required",
)
REQUIRED_MECHANICAL_TRIGGERS = ("all-commits-minimum-body", "breaking-marker")


@dataclass(frozen=True, slots=True)
class CommitContractProjection:
    type_tokens: tuple[str, ...]
    scope_tokens: tuple[str, ...]
    mechanical_triggers: tuple[str, ...]
    source_key: str
    source_path: str
    observed_at: str | None
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class CommitContractSourceResult:
    projection: CommitContractProjection | None
    issues: tuple[Issue, ...]


def _issue(document: FormalDocument, summary: str, line: int | None = None) -> Issue:
    return Issue(summary=summary, location=SourceLocation(document.canonical_path, line), affected=(document.key,))


def _cells(line: str) -> tuple[str, ...]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return ()
    return tuple(cell.strip().strip("`") for cell in stripped[1:-1].split("|"))


def _tables(
    document: FormalDocument,
    start_line: int,
    end_line: int,
) -> tuple[tuple[tuple[str, ...], tuple[tuple[str, ...], ...], int], ...]:
    lines = document.markdown.raw_lines
    found: list[tuple[tuple[str, ...], tuple[tuple[str, ...], ...], int]] = []
    index = start_line - 1
    while index + 1 < end_line - 1:
        headers = _cells(lines[index])
        delimiter = _cells(lines[index + 1])
        valid_delimiter = all(cell and set(cell.replace(":", "")) == {"-"} for cell in delimiter)
        if headers and len(headers) == len(delimiter) and valid_delimiter:
            rows: list[tuple[str, ...]] = []
            cursor = index + 2
            while cursor < end_line - 1:
                row = _cells(lines[cursor])
                if len(row) != len(headers):
                    break
                rows.append(row)
                cursor += 1
            found.append((headers, tuple(rows), index + 1))
            index = cursor
            continue
        index += 1
    return tuple(found)


def project_commit_contract(
    document: FormalDocument,
    attachment: FormalDocument | None,
) -> CommitContractSourceResult:
    """Project commit tables from active 03 and its explicitly authorized 03.Att.01."""

    issues: list[Issue] = []
    if document.key != SOURCE_KEY or document.status != "active":
        return CommitContractSourceResult(None, (_issue(document, "提交契约只能从 active 的 03 来源派生"),))
    if attachment is None:
        return CommitContractSourceResult(
            None,
            (_issue(document, f"03 授权附件 {ATTACHMENT_KEY} 不可用"),),
        )
    if ATTACHMENT_KEY not in document.authorized_attachments:
        return CommitContractSourceResult(
            None,
            (_issue(document, f"03 未授权提交契约附件 {ATTACHMENT_KEY}"),),
        )
    if (
        attachment.kind != "attachment"
        or attachment.key != ATTACHMENT_KEY
        or attachment.current_id != ATTACHMENT_ID
        or attachment.status != "active"
    ):
        return CommitContractSourceResult(
            None,
            (_issue(attachment, f"提交契约附件必须是 active 的 {ATTACHMENT_ID}/{ATTACHMENT_KEY}"),),
        )
    section = document.markdown.find_headings("9. Git 溯源边界", level=2)
    if len(section) != 1:
        return CommitContractSourceResult(None, (_issue(document, "03 必须唯一包含 Git 溯源边界 H2"),))
    grouped: dict[tuple[str, ...], list[tuple[tuple[tuple[str, ...], ...], int]]] = {}
    for headers, rows, line in _tables(attachment, 1, len(attachment.markdown.raw_lines) + 1):
        grouped.setdefault(headers, []).append((rows, line))
    required = (TYPE_HEADERS, SCOPE_HEADERS, TRIGGER_HEADERS)
    for headers in required:
        if len(grouped.get(headers, ())) != 1:
            issues.append(_issue(attachment, f"提交契约表 {headers!r} 必须唯一存在"))
    if issues:
        return CommitContractSourceResult(None, tuple(issues))

    type_rows = grouped[TYPE_HEADERS][0][0]
    scope_rows = grouped[SCOPE_HEADERS][0][0]
    trigger_rows = grouped[TRIGGER_HEADERS][0][0]
    type_tokens = tuple(row[0] for row in type_rows if len(row) == 2 and row[0] and row[1])
    scope_tokens = tuple(row[0] for row in scope_rows if len(row) == 2 and row[0] and row[1])
    trigger_keys = tuple(row[0] for row in trigger_rows if len(row) == 4 and all(row))
    mechanical = tuple(row[0] for row in trigger_rows if len(row) == 4 and row[1] == "true")
    if len(type_tokens) != len(type_rows) or len(type_tokens) != len(set(type_tokens)):
        issues.append(_issue(attachment, "type 表必须包含非空且唯一的 token 与语义"))
    if len(scope_tokens) != len(scope_rows) or len(scope_tokens) != len(set(scope_tokens)):
        issues.append(_issue(attachment, "scope 表必须包含非空且唯一的 token 与语义"))
    if trigger_keys != REQUIRED_TRIGGER_KEYS:
        issues.append(_issue(attachment, "trigger 表必须按来源固定顺序完整声明且不得包含未知或重复成员"))
    if any(len(row) != 4 or any(not cell for cell in row) or row[1] not in {"true", "false"} for row in trigger_rows):
        issues.append(_issue(attachment, "trigger 表每行必须完整且 mechanical 只能是 true 或 false"))
    if mechanical != REQUIRED_MECHANICAL_TRIGGERS:
        issues.append(_issue(attachment, "机械 trigger 必须按来源固定顺序完整声明"))
    if issues:
        return CommitContractSourceResult(None, tuple(issues))
    fingerprint = hashlib.sha256(
        "\x00".join(
            (
                document.canonical_path,
                document.markdown.raw_text,
                attachment.canonical_path,
                attachment.markdown.raw_text,
            )
        ).encode("utf-8")
    ).hexdigest()
    return CommitContractSourceResult(
        CommitContractProjection(
            type_tokens=type_tokens,
            scope_tokens=scope_tokens,
            mechanical_triggers=mechanical,
            source_key=document.key,
            source_path=document.canonical_path,
            observed_at=document.markdown.observed_at,
            content_fingerprint=fingerprint,
        ),
        (),
    )


__all__ = [
    "ATTACHMENT_KEY",
    "CommitContractProjection",
    "CommitContractSourceResult",
    "project_commit_contract",
]
