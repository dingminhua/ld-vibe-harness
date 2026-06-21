"""Field registry checks for specs/05.03."""

import re
from pathlib import Path

from .common import HEADING_RE, Issue
from .index import SpecsChecker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = PROJECT_ROOT / "specs"
FIELD_REGISTRY_SPEC_NAME = "05.03-字段注册与消费规范.md"
WORKCASE_SPEC_NAME = "21-WorkCase-工作项.md"
REQUIRED_REGISTRY_SECTION_TITLES = {"通用字段注册", "对象特有字段注册"}
REGISTRY_SECTION_TITLES = {*REQUIRED_REGISTRY_SECTION_TITLES, "WorkCase 试点字段注册"}

REGISTRY_REQUIRED_COLUMNS = [
    "field_path",
    "scope",
    "meaning",
    "format_kind",
    "value_shape",
    "ref_kind",
    "enum_owner",
    "schema_owner",
    "code_check_kind",
    "web_render_kind",
    "status",
    "replacement",
]
ALLOWED_FORMAT_KINDS = {"narrative", "checklist", "evidence", "decision", "reference", "log", "structured"}
ALLOWED_VALUE_SHAPES = {
    "string",
    "markdown",
    "checklist_markdown",
    "evidence_markdown",
    "boolean",
    "date",
    "datetime",
    "object",
    "list_object",
    "list_string",
    "list_mixed",
}
ALLOWED_REF_KINDS = {
    "none",
    "object_ref",
    "workcase_ref",
    "commit_ref",
    "doc_path",
    "mixed_ref",
    "url_ref",
    "local_id",
    "enum",
}
ALLOWED_CODE_CHECK_KINDS = {"none", "format", "ref", "enum", "structured", "deprecated", "owner_state"}
ALLOWED_WEB_RENDER_KINDS = {
    "summary",
    "checklist",
    "evidence",
    "object_ref",
    "doc_link",
    "commit_ref",
    "mixed_ref",
    "url_ref",
    "structured_area",
    "status_signal",
    "enum_signal",
    "metadata",
    "deprecated",
}
ALLOWED_REGISTRY_STATUSES = {"active", "deprecated", "removed", "alias"}
OWNER_RE = re.compile(r"^(none|05\.0[1-3]|20-39|2[0-9]|3[0-9])$")
DOC_NUMBERED_HEADING_RE = re.compile(r"^\d+(?:\.\d+)*\.?(?:\s+|$)")


def strip_section_number(title):
    return DOC_NUMBERED_HEADING_RE.sub("", title, count=1).strip()


def clean_cell(value):
    text = str(value).strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        return text[1:-1]
    return text


def split_cells(line):
    return [clean_cell(cell) for cell in line.strip().strip("|").split("|")]


def is_separator(cells):
    return bool(cells) and all(set(cell) <= {"-", ":", " "} for cell in cells)


def default_spec_path():
    return SPECS_DIR / FIELD_REGISTRY_SPEC_NAME


def workcase_spec_path():
    return SPECS_DIR / WORKCASE_SPEC_NAME


def active_work_model_scope_owners():
    owners = {}
    try:
        index = SpecsChecker(PROJECT_ROOT, SPECS_DIR).build()
    except Exception:
        return owners
    for member in index.get("members", []):
        if member.get("kind") != "work_model" or member.get("collection_status") != "active":
            continue
        scope = str(member.get("name_en") or "").lower()
        spec_id = str(member.get("spec_id") or "")
        if scope and spec_id:
            owners[scope] = spec_id
    return owners


def selected_spec_paths(paths=None):
    if not paths:
        return [default_spec_path()]
    selected = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file() and path.name == FIELD_REGISTRY_SPEC_NAME:
            selected.append(path)
        elif path.is_dir():
            selected.extend(sorted(path.rglob(FIELD_REGISTRY_SPEC_NAME)))
    return sorted(set(selected))


def extract_tables(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    tables = {}
    current_section = None
    in_code_block = False
    header = None
    rows = []
    start_line = None
    table_active = False

    def flush_table():
        nonlocal header, rows, start_line, table_active
        if current_section and header:
            tables[current_section] = {"header": header, "rows": rows, "line": start_line}
        header = None
        rows = []
        start_line = None
        table_active = False

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        heading = HEADING_RE.match(line)
        if heading:
            flush_table()
            title = strip_section_number(heading.group(2).strip())
            current_section = title if title in REGISTRY_SECTION_TITLES else None
            continue

        if not current_section:
            continue

        if not stripped:
            if table_active:
                flush_table()
            continue
        if not stripped.startswith("|"):
            if table_active:
                flush_table()
            continue

        cells = split_cells(stripped)
        if is_separator(cells):
            continue
        if header is None:
            header = cells
            start_line = index
            table_active = True
            continue
        rows.append({"line": index, "cells": cells})

    flush_table()
    return tables


def extract_markdown_tables(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    tables = []
    current_heading = None
    in_code_block = False
    header = None
    rows = []
    start_line = None
    table_context = None
    last_text = None

    def flush_table():
        nonlocal header, rows, start_line, table_context
        if header:
            tables.append(
                {
                    "heading": current_heading,
                    "context": table_context,
                    "header": header,
                    "rows": rows,
                    "line": start_line,
                }
            )
        header = None
        rows = []
        start_line = None
        table_context = None

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        heading = HEADING_RE.match(line)
        if heading:
            flush_table()
            current_heading = strip_section_number(heading.group(2).strip())
            last_text = None
            continue

        if not stripped:
            flush_table()
            continue

        if stripped.startswith("|"):
            cells = split_cells(stripped)
            if is_separator(cells):
                continue
            if header is None:
                header = cells
                start_line = index
                table_context = last_text
                continue
            rows.append({"line": index, "cells": cells})
            continue

        flush_table()
        last_text = stripped

    flush_table()
    return tables


def extract_workcase_field_paths(path):
    field_paths = set()
    for table in extract_markdown_tables(path):
        header = table.get("header") or []
        rows = table.get("rows") or []
        heading = table.get("heading")
        context = table.get("context") or ""
        if not header or not rows:
            continue

        first_column = header[0]
        prefix = None
        if heading == "字段契约" and first_column == "字段名":
            prefix = ""
        elif heading == "orchestration 最小结构" and first_column == "字段名":
            prefix = "orchestration."
        elif heading == "orchestration 最小结构" and first_column == "字段路径":
            if "orchestration.execution_items" in context:
                prefix = "orchestration.execution_items."
            elif "orchestration.review" in context:
                prefix = "orchestration.review."

        if prefix is None:
            continue

        for row in rows:
            cells = row["cells"]
            if not cells:
                continue
            field_name = clean_cell(cells[0])
            if field_name:
                field_paths.add(f"{prefix}{field_name}")
    return field_paths


def row_dict(header, row):
    values = list(row["cells"])
    if len(values) < len(header):
        values.extend([""] * (len(header) - len(values)))
    return dict(zip(header, values))


def registered_field_paths(tables):
    field_paths = set()
    for section_title in REGISTRY_SECTION_TITLES:
        table = tables.get(section_title)
        if not table:
            continue
        header = table.get("header") or []
        for row in table.get("rows") or []:
            data = row_dict(header, row)
            field_path = data.get("field_path")
            if field_path:
                field_paths.add(field_path)
    return field_paths


def check_registry_table(path, section_title, table, seen_keys, scope_owners=None):
    issues = []
    scope_owners = scope_owners or {}
    header = table.get("header") or []
    if header[: len(REGISTRY_REQUIRED_COLUMNS)] != REGISTRY_REQUIRED_COLUMNS:
        expected = " | ".join(REGISTRY_REQUIRED_COLUMNS)
        actual = " | ".join(header)
        issues.append(
            Issue(
                path,
                table.get("line") or 1,
                f"{section_title} registry 表头不符合 05.03 注册列: 期望 {expected}，实际 {actual}",
                code="FIELD_REGISTRY_HEADER_INVALID",
            )
        )
        return issues

    if not table.get("rows"):
        issues.append(Issue(path, table.get("line") or 1, f"{section_title} registry 表缺少数据行", code="FIELD_REGISTRY_ROW_MISSING"))
        return issues

    enum_checks = [
        ("format_kind", ALLOWED_FORMAT_KINDS, "FIELD_REGISTRY_FORMAT_INVALID"),
        ("value_shape", ALLOWED_VALUE_SHAPES, "FIELD_REGISTRY_VALUE_SHAPE_INVALID"),
        ("ref_kind", ALLOWED_REF_KINDS, "FIELD_REGISTRY_REF_KIND_INVALID"),
        ("code_check_kind", ALLOWED_CODE_CHECK_KINDS, "FIELD_REGISTRY_CODE_CHECK_INVALID"),
        ("web_render_kind", ALLOWED_WEB_RENDER_KINDS, "FIELD_REGISTRY_WEB_RENDER_INVALID"),
        ("status", ALLOWED_REGISTRY_STATUSES, "FIELD_REGISTRY_STATUS_INVALID"),
    ]

    for row in table["rows"]:
        cells = row["cells"]
        if len(cells) < len(REGISTRY_REQUIRED_COLUMNS):
            issues.append(Issue(path, row["line"], f"{section_title} registry 行缺少必填列", code="FIELD_REGISTRY_ROW_TOO_SHORT"))
            continue
        data = row_dict(header, row)
        for column in REGISTRY_REQUIRED_COLUMNS:
            if not data.get(column):
                issues.append(Issue(path, row["line"], f"{section_title} registry 字段为空: {column}", code="FIELD_REGISTRY_FIELD_EMPTY"))

        key = (data.get("scope"), data.get("field_path"))
        if all(key):
            if key in seen_keys:
                issues.append(
                    Issue(
                        path,
                        row["line"],
                        f"字段注册重复: scope={key[0]} field_path={key[1]}",
                        code="FIELD_REGISTRY_DUPLICATE",
                    )
                )
            seen_keys.add(key)

        for column, allowed, code in enum_checks:
            value = data.get(column)
            if value and value not in allowed:
                allowed_text = "、".join(sorted(allowed))
                issues.append(Issue(path, row["line"], f"{column} 枚举值无效: {value}；允许值: {allowed_text}", code=code))

        for column in ("enum_owner", "schema_owner"):
            value = data.get(column)
            if value and not OWNER_RE.match(value):
                issues.append(Issue(path, row["line"], f"{column} 归属值无效: {value}", code="FIELD_REGISTRY_OWNER_INVALID"))

        expected_owner = scope_owners.get(data.get("scope"))
        schema_owner = data.get("schema_owner")
        if expected_owner and schema_owner not in {"", "none", "20-39", expected_owner}:
            issues.append(
                Issue(
                    path,
                    row["line"],
                    f"schema_owner 与 scope 当前工作模型编号不一致: scope={data.get('scope')} schema_owner={schema_owner} expected={expected_owner}",
                    code="FIELD_REGISTRY_OWNER_SCOPE_MISMATCH",
                )
            )

        status = data.get("status")
        replacement = data.get("replacement")
        if status == "active" and replacement != "none":
            issues.append(Issue(path, row["line"], "active 字段 replacement 必须为 none", code="FIELD_REGISTRY_REPLACEMENT_INVALID"))
        if status in {"deprecated", "removed", "alias"} and replacement in {"", "none"}:
            issues.append(Issue(path, row["line"], f"{status} 字段必须声明 replacement", code="FIELD_REGISTRY_REPLACEMENT_MISSING"))

    return issues


def check_workcase_coverage(path, tables):
    issues = []
    workcase_path = path.parent / WORKCASE_SPEC_NAME
    if not workcase_path.exists():
        return issues

    registered_paths = registered_field_paths(tables)
    workcase_paths = extract_workcase_field_paths(workcase_path)
    for field_path in sorted(workcase_paths - registered_paths):
        issues.append(
            Issue(
                path,
                1,
                f"WorkCase 字段未在 05.03 注册: {field_path}",
                code="FIELD_REGISTRY_WORKCASE_FIELD_MISSING",
            )
        )
    return issues


def check_file(path):
    issues = []
    if not path.exists():
        return [Issue(path, 1, "05.03 字段注册规范文件不存在", code="FIELD_REGISTRY_SPEC_MISSING")]

    tables = extract_tables(path)
    seen_keys = set()
    scope_owners = active_work_model_scope_owners()
    for section_title in sorted(REQUIRED_REGISTRY_SECTION_TITLES):
        table = tables.get(section_title)
        if not table:
            issues.append(Issue(path, 1, f"缺少 registry 表章节或表格: {section_title}", code="FIELD_REGISTRY_TABLE_MISSING"))
            continue
        issues.extend(check_registry_table(path, section_title, table, seen_keys, scope_owners))

    issues.extend(check_workcase_coverage(path, tables))
    return issues


def check_paths(paths=None):
    issues = []
    selected_paths = selected_spec_paths(paths)
    if not selected_paths:
        selected_paths = [default_spec_path()]
    for path in selected_paths:
        issues.extend(check_file(path))
    return issues


def main(paths=None):
    issues = check_paths(paths)
    if issues:
        print(f"字段注册表检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("字段注册表检查通过。")
    return 0
