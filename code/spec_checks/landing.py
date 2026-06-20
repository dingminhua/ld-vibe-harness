"""Landing requirement table checks for LDVH specs."""

import re
from pathlib import Path

from .common import HEADING_RE, Issue, iter_markdown_files, relative_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORMAL_SPECS_DIR = PROJECT_ROOT / "specs"
DOC_NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
LANDING_SECTION_TITLE = "规范落地要求"
LANDING_REQUIRED_COLUMNS = ["落地要求", "要求内容", "保障机制", "同步类型", "触发条件"]
LANDING_ALLOWED_TYPES = {
    "上位约束承接要求",
    "入口可见要求",
    "流程复用要求",
    "工作流程接管要求",
    "子 Agent 思考要求",
    "确定性执行要求",
    "Human 交互要求",
    "生命周期触发要求",
}


def default_check_paths():
    if FORMAL_SPECS_DIR.exists():
        return [str(path) for path in sorted(FORMAL_SPECS_DIR.glob("*.md"))]
    return []


def is_formal_spec(path):
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(PROJECT_ROOT)
    except ValueError:
        return False
    if len(rel.parts) != 2 or rel.parts[0] != "specs" or path.suffix != ".md":
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return "迁移待删除" not in line
    return True


def strip_section_number(title):
    return DOC_NUMBERED_HEADING_RE.sub("", title, count=1).strip()


def split_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(cells):
    return all(set(cell) <= {"-", ":", " "} for cell in cells)


def clean_cell(value):
    text = str(value).strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        return text[1:-1]
    return text


def landing_relative_path(path):
    return relative_path(path, PROJECT_ROOT)


def extract_requirements_file(path):
    requirements = []
    if not is_formal_spec(path):
        return requirements

    lines = path.read_text(encoding="utf-8").splitlines()
    in_code_block = False
    in_landing_section = False
    header_seen = False
    in_table = False

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = strip_section_number(heading.group(2).strip())
            in_landing_section = level == 2 and title == LANDING_SECTION_TITLE
            header_seen = False
            in_table = False
            continue

        if not in_landing_section:
            continue
        if not stripped:
            if in_table:
                break
            continue
        if not stripped.startswith("|"):
            if in_table:
                break
            continue

        cells = split_cells(stripped)
        if is_separator(cells):
            continue
        if not header_seen:
            header_seen = True
            in_table = True
            continue
        if len(cells) < len(LANDING_REQUIRED_COLUMNS):
            continue

        requirements.append(
            {
                "source": landing_relative_path(path),
                "line": index,
                "requirement_type": clean_cell(cells[0]),
                "content": clean_cell(cells[1]),
                "guarantee_mechanism": clean_cell(cells[2]),
                "sync_type": clean_cell(cells[3]),
                "trigger": clean_cell(cells[4]),
            }
        )

    return requirements


def check_file(path):
    issues = []
    if not is_formal_spec(path):
        return issues

    lines = path.read_text(encoding="utf-8").splitlines()
    in_code_block = False
    in_landing_section = False
    section_line = None
    header_seen = False
    table_seen = False
    row_seen = False

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = strip_section_number(heading.group(2).strip())
            if in_landing_section and not table_seen:
                issues.append(Issue(path, section_line, "规范落地要求章节缺少表格", code="LANDING_TABLE_MISSING"))
            elif in_landing_section and table_seen and not row_seen:
                issues.append(Issue(path, section_line, "规范落地要求表格缺少数据行", code="LANDING_ROW_MISSING"))
            in_landing_section = level == 2 and title == LANDING_SECTION_TITLE
            section_line = index if in_landing_section else None
            header_seen = False
            table_seen = False
            row_seen = False
            continue

        if not in_landing_section:
            continue

        if not stripped:
            continue
        if not stripped.startswith("|"):
            if table_seen:
                break
            continue

        cells = split_cells(stripped)
        if is_separator(cells):
            continue

        if not header_seen:
            header_seen = True
            table_seen = True
            if cells[: len(LANDING_REQUIRED_COLUMNS)] != LANDING_REQUIRED_COLUMNS:
                expected = " | ".join(LANDING_REQUIRED_COLUMNS)
                actual = " | ".join(cells)
                issues.append(
                    Issue(
                        path,
                        index,
                        f"规范落地要求表头不符合 04.01 要求: 期望 {expected}，实际 {actual}",
                        code="LANDING_HEADER_INVALID",
                    )
                )
            continue

        row_seen = True
        if len(cells) < len(LANDING_REQUIRED_COLUMNS):
            issues.append(Issue(path, index, "规范落地要求表格行缺少必填字段", code="LANDING_ROW_TOO_SHORT"))
            continue

        required_values = cells[: len(LANDING_REQUIRED_COLUMNS)]
        for column, value in zip(LANDING_REQUIRED_COLUMNS, required_values):
            if not value:
                issues.append(Issue(path, index, f"规范落地要求表格字段为空: {column}", code="LANDING_FIELD_EMPTY"))

        requirement_type = required_values[0]
        if requirement_type and requirement_type not in LANDING_ALLOWED_TYPES:
            allowed = "、".join(sorted(LANDING_ALLOWED_TYPES))
            issues.append(
                Issue(
                    path,
                    index,
                    f"规范落地要求类型未在 04.01 中定义: {requirement_type}；允许值: {allowed}",
                    code="LANDING_TYPE_INVALID",
                )
            )

    if in_landing_section and not table_seen:
        issues.append(Issue(path, section_line, "规范落地要求章节缺少表格", code="LANDING_TABLE_MISSING"))
    elif in_landing_section and table_seen and not row_seen:
        issues.append(Issue(path, section_line, "规范落地要求表格缺少数据行", code="LANDING_ROW_MISSING"))

    if not any(
        len(match.group(1)) == 2 and strip_section_number(match.group(2).strip()) == LANDING_SECTION_TITLE
        for match in (HEADING_RE.match(line) for line in lines)
        if match
    ):
        issues.append(Issue(path, 1, "正式规范文档缺少规范落地要求章节", code="LANDING_SECTION_MISSING"))

    return issues


def check_paths(paths):
    issues = []
    for path in iter_markdown_files(paths):
        issues.extend(check_file(path))
    return issues


def main(paths):
    selected_paths = paths if paths else default_check_paths()
    issues = check_paths(selected_paths)
    if issues:
        print(f"规范落地要求检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("规范落地要求检查通过。")
    return 0
