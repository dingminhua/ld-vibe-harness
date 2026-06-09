#!/usr/bin/env python3
"""Specs 文档结构、引用完整性和派生索引统一检查工具。"""

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml


# ── 通用常量 ──

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = PROJECT_ROOT / "docs" / "specs"
LEGACY_SPECS_DIR = PROJECT_ROOT / "specs"
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_SPECS_DIR = DOCS_DIR / "specs"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


# ── 通用数据结构 ──

@dataclass
class Issue:
    path: Path
    line: int
    message: str
    code: str = None

    def format(self, root=None):
        display_path = self.path
        if root:
            try:
                display_path = self.path.relative_to(root)
            except ValueError:
                display_path = self.path
        if self.code:
            return f"{display_path}:{self.line}: [{self.code}] {self.message}"
        return f"{display_path}:{self.line}: {self.message}"


def iter_markdown_files(paths):
    files = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
    return sorted(set(files))


# ══════════════════════════════════════════════════════════════════════
# doc — 文档编号/标题规范检查
# ══════════════════════════════════════════════════════════════════════

DOC_NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
DOC_CHINESE_HEADING_RE = re.compile(r"^[一二三四五六七八九十百千万]+[、，.．]\s*")
DOC_ROMAN_HEADING_RE = re.compile(r"^[IVXLCDM]+[、.．]\s+", re.IGNORECASE)
DOC_UNNUMBERED_ALLOWED_HEADINGS = {"章节索引"}


@dataclass
class Heading:
    path: Path
    line: int
    level: int
    title: str
    numbers: tuple


class HeadingNumberState:
    def __init__(self):
        self.current = {}
        self.seen = set()

    def check(self, heading):
        issues = []
        structural_level = heading.level - 1
        number_depth = len(heading.numbers)
        number_text = ".".join(str(part) for part in heading.numbers)

        if heading.level == 1:
            return issues

        if heading.level > 4:
            issues.append(Issue(heading.path, heading.line, f"不支持超过四级的正文章节标题: {'#' * heading.level}"))
            return issues

        if number_depth != structural_level:
            issues.append(
                Issue(
                    heading.path,
                    heading.line,
                    f"标题层级与编号层级不一致: {'#' * heading.level} 应使用 {structural_level} 段编号，实际为 {number_text}",
                )
            )
            return issues

        if heading.numbers in self.seen:
            issues.append(Issue(heading.path, heading.line, f"章节编号重复: §{number_text}"))
        self.seen.add(heading.numbers)

        parent = heading.numbers[:-1]
        if structural_level > 1:
            expected_parent = self.current.get(structural_level - 1)
            if expected_parent != parent:
                expected_text = ".".join(str(part) for part in expected_parent) if expected_parent else "无父章节"
                parent_text = ".".join(str(part) for part in parent)
                issues.append(
                    Issue(
                        heading.path,
                        heading.line,
                        f"章节父级不一致: §{number_text} 的父级应为 §{expected_text}，实际编号父级为 §{parent_text}",
                    )
                )

        previous = self.current.get(structural_level)
        if previous and previous[:-1] == parent:
            expected_last = previous[-1] + 1
            expected = parent + (expected_last,)
        elif structural_level > 1:
            expected_parent = self.current.get(structural_level - 1) or parent
            expected = expected_parent + (1,)
        else:
            expected = (1,)
        if heading.numbers != expected:
            expected_text = ".".join(str(part) for part in expected)
            issues.append(Issue(heading.path, heading.line, f"章节编号不连续: 期望 §{expected_text}，实际 §{number_text}"))

        self.current[structural_level] = heading.numbers
        for level in list(self.current):
            if level > structural_level:
                del self.current[level]
        return issues


def doc_parse_heading_number(title):
    match = DOC_NUMBERED_HEADING_RE.match(title)
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def doc_check_file(path):
    issues = []
    state = HeadingNumberState()
    in_code_block = False

    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        match = HEADING_RE.match(line)
        if not match:
            continue

        level = len(match.group(1))
        title = match.group(2).strip()
        if level == 1:
            continue

        if DOC_CHINESE_HEADING_RE.match(title):
            issues.append(Issue(path, index, f"章节标题使用中文大写编号: {title}"))
            continue
        if DOC_ROMAN_HEADING_RE.match(title):
            issues.append(Issue(path, index, f"章节标题使用罗马数字编号: {title}"))
            continue

        numbers = doc_parse_heading_number(title)
        if numbers is None:
            if title in DOC_UNNUMBERED_ALLOWED_HEADINGS:
                continue
            issues.append(Issue(path, index, f"章节标题缺少阿拉伯数字编号: {title}"))
            continue

        issues.extend(state.check(Heading(path, index, level, title, numbers)))

    return issues


def doc_check_paths(paths):
    issues = []
    for path in iter_markdown_files(paths):
        issues.extend(doc_check_file(path))
    return issues


def doc_main(paths):
    issues = doc_check_paths(paths)
    if issues:
        print(f"03 文档基础规范检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("03 文档基础规范检查通过。")
    return 0


# ══════════════════════════════════════════════════════════════════════
# refs — 引用完整性检查
# ══════════════════════════════════════════════════════════════════════

REFS_SECTION_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
REFS_SECTION_REF_RE = re.compile(r"§([一二三四五六七八九十百千万\d]+(?:\.\d+)*)")
REFS_EXPLICIT_PATH_RE = re.compile(r"`([^`]+\.md)`\s*$")
REFS_SHORTHAND_RE = re.compile(r"(\d+(?:\.\d+)?)\s*$")
REFS_CHINESE_SECTION_RE = re.compile(r"^[一二三四五六七八九十百千万]+(?:\.\d+)*$")


@dataclass
class Document:
    path: Path
    sections: set


def refs_extract_sections(path):
    sections = set()
    in_code_block = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = match.group(2).strip()
        section_match = REFS_SECTION_HEADING_RE.match(title)
        if section_match:
            sections.add(section_match.group(1))
    return sections


def refs_build_document_map(paths):
    documents = {}
    scan_paths = list(paths)
    if SPECS_DIR.exists():
        scan_paths.append(SPECS_DIR)
    if LEGACY_SPECS_DIR.exists():
        scan_paths.append(LEGACY_SPECS_DIR)
    for path in iter_markdown_files(scan_paths):
        documents[path.resolve()] = Document(path.resolve(), refs_extract_sections(path))
    return documents


def refs_resolve_markdown_path(raw_path, current_path):
    if raw_path.startswith("specs/") or raw_path.startswith("docs/"):
        return (PROJECT_ROOT / raw_path).resolve()
    if raw_path.startswith("./") or raw_path.startswith("../"):
        return (current_path.parent / raw_path).resolve()
    return (SPECS_DIR / raw_path).resolve()


def refs_resolve_shorthand(prefix, documents):
    candidates = sorted(documents)
    exact_prefix = f"{prefix}-"
    sub_prefix = f"{prefix}."
    for path in candidates:
        if path.parent == SPECS_DIR.resolve() and path.name.startswith(exact_prefix):
            return path
    for path in candidates:
        if path.parent == SPECS_DIR.resolve() and path.name.startswith(sub_prefix):
            return path
    return None


def refs_resolve_parent_document(path, documents):
    match = re.match(r"^(\d+)\.\d+-", path.name)
    if not match:
        return None
    return refs_resolve_shorthand(match.group(1), documents)


def refs_default_check_paths():
    return [str(path) for path in sorted(SPECS_DIR.glob("*.md"))]


def refs_check_section_target(issues, source_path, line_number, target_path, section, documents, code):
    document = documents.get(target_path)
    if document is None:
        issues.append(Issue(source_path, line_number, f"引用文件不存在: {target_path}", code="FILE_NOT_FOUND"))
        return
    if section not in document.sections:
        try:
            display_target = target_path.relative_to(PROJECT_ROOT)
        except ValueError:
            display_target = target_path
        issues.append(Issue(source_path, line_number, f"引用章节不存在: {display_target} §{section}", code=code))


def refs_check_file(path, documents):
    issues = []
    source_path = path.resolve()
    source_document = documents.get(source_path, Document(source_path, refs_extract_sections(source_path)))
    in_code_block = False

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        for match in REFS_SECTION_REF_RE.finditer(line):
            section = match.group(1)
            original = match.group(0)
            if REFS_CHINESE_SECTION_RE.match(section):
                issues.append(Issue(source_path, line_number, f"§ 引用应使用阿拉伯数字: {original}", code="CHINESE_SECTION_REF"))
                continue

            before = line[: match.start()]
            explicit_match = REFS_EXPLICIT_PATH_RE.search(before)
            if explicit_match:
                target_path = refs_resolve_markdown_path(explicit_match.group(1), source_path)
                refs_check_section_target(issues, source_path, line_number, target_path, section, documents, "MISSING_EXTERNAL_SECTION")
                continue

            shorthand_match = REFS_SHORTHAND_RE.search(before)
            if shorthand_match:
                prefix = shorthand_match.group(1)
                target_path = refs_resolve_shorthand(prefix, documents)
                if target_path is None:
                    issues.append(Issue(source_path, line_number, f"速记引用无法解析目标文件: {prefix} §{section}", code="SHORTHAND_UNRESOLVED"))
                    continue
                refs_check_section_target(issues, source_path, line_number, target_path, section, documents, "MISSING_SHORTHAND_SECTION")
                continue

            parent_path = refs_resolve_parent_document(source_path, documents)
            if parent_path and section in documents[parent_path].sections:
                continue

            if section not in source_document.sections:
                issues.append(Issue(source_path, line_number, f"内部引用章节不存在: §{section}", code="MISSING_INTERNAL_SECTION"))

    return issues


def refs_check_paths(paths):
    documents = refs_build_document_map(paths)
    issues = []
    for path in iter_markdown_files(paths):
        issues.extend(refs_check_file(path, documents))
    return issues


def refs_main(paths):
    issues = refs_check_paths(paths)
    if issues:
        print(f"Specs § 引用检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("Specs § 引用检查通过。")
    return 0


# ══════════════════════════════════════════════════════════════════════
# landing — 规范落地要求表检查
# ══════════════════════════════════════════════════════════════════════

LANDING_SECTION_TITLE = "规范落地要求"
LANDING_REQUIRED_COLUMNS = ["落地要求", "要求内容", "保障机制", "同步类型", "触发条件"]
LANDING_ALLOWED_TYPES = {
    "上位约束承接要求",
    "入口可见要求",
    "流程复用要求",
    "子 Agent 思考要求",
    "确定性执行要求",
    "Human 交互要求",
    "生命周期触发要求",
}
LANDING_REPORT_OWNER_AREAS = {
    "上位约束承接要求": "specs",
    "入口可见要求": "runtime_projection",
    "流程复用要求": "workflow",
    "子 Agent 思考要求": "agent",
    "确定性执行要求": "code",
    "Human 交互要求": "human_gate",
    "生命周期触发要求": "runtime_projection",
}
LANDING_REPORT_WRITEBACK_AREAS = {
    "specs": "specs",
    "runtime_projection": "runtime_projection_or_env_record",
    "workflow": "workflow_or_skill_candidate",
    "agent": "agent_or_44",
    "code": "code_request_or_test",
    "human_gate": "human_gate_or_task",
}
LANDING_REPORT_DEGRADED_MARKERS = [
    "open-degraded",
    "degraded",
    "人工降级",
    "降级原因",
    "降级说明",
    "降级方式",
    "记录降级",
]
LANDING_REPORT_OPEN_MARKERS = [
    "TODO",
    "待补齐",
    "待创建",
    "待讨论",
    "待实现",
    "尚未",
    "未稳定",
    "未完成",
    "后续 Code",
    "open item",
]
LANDING_REPORT_OPEN_PATTERNS = [
    re.compile(r"后续[^|。；;]*?(补齐|扩展|创建|讨论|稳定|校准|补充|形成|沉淀)"),
    re.compile(r"(需要|需|应)[^|。；;]*?(补齐|扩展|创建|讨论|稳定|校准|形成缺口)"),
    re.compile(r"缺口[^|。；;]*?(待|未|open)"),
]
LANDING_REPORT_HUMAN_GATE_PATTERNS = [
    re.compile(r"(必须|应|需|需要|触发|进入|经|通过|完成)[^|。；;]*?Human Gate"),
    re.compile(r"Human Gate[^|。；;]*?(确认|前|后|授权|暂停|等待)"),
]


def landing_default_check_paths():
    if DOCS_SPECS_DIR.exists():
        return [str(path) for path in sorted(DOCS_SPECS_DIR.glob("*.md"))]
    return []


def landing_is_formal_spec(path):
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(PROJECT_ROOT)
    except ValueError:
        return False
    return len(rel.parts) == 3 and rel.parts[:2] == ("docs", "specs") and path.suffix == ".md"


def landing_strip_section_number(title):
    return DOC_NUMBERED_HEADING_RE.sub("", title, count=1).strip()


def landing_split_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def landing_is_separator(cells):
    return all(set(cell) <= {"-", ":", " "} for cell in cells)


def landing_clean_cell(value):
    text = str(value).strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        return text[1:-1]
    return text


def landing_relative_path(path):
    try:
        return str(Path(path).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def landing_extract_requirements_file(path):
    requirements = []
    if not landing_is_formal_spec(path):
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
            title = landing_strip_section_number(heading.group(2).strip())
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

        cells = landing_split_cells(stripped)
        if landing_is_separator(cells):
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
                "requirement_type": landing_clean_cell(cells[0]),
                "content": landing_clean_cell(cells[1]),
                "guarantee_mechanism": landing_clean_cell(cells[2]),
                "sync_type": landing_clean_cell(cells[3]),
                "trigger": landing_clean_cell(cells[4]),
            }
        )

    return requirements


def landing_report_match_marker(text, markers):
    for marker in markers:
        if marker in text:
            return marker
    return None


def landing_report_infer_status(requirement):
    text = " | ".join(
        [
            requirement.get("requirement_type", ""),
            requirement.get("content", ""),
            requirement.get("guarantee_mechanism", ""),
            requirement.get("sync_type", ""),
            requirement.get("trigger", ""),
        ]
    )

    marker = landing_report_match_marker(text, LANDING_REPORT_DEGRADED_MARKERS)
    if marker:
        return "degraded", f"matched degraded marker: {marker}"

    marker = landing_report_match_marker(text, LANDING_REPORT_OPEN_MARKERS)
    if marker:
        return "open", f"matched open marker: {marker}"

    for pattern in LANDING_REPORT_OPEN_PATTERNS:
        match = pattern.search(text)
        if match:
            return "open", f"matched open pattern: {match.group(0)}"

    for pattern in LANDING_REPORT_HUMAN_GATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return "needs_human_gate", f"matched Human Gate pattern: {match.group(0)}"

    return "closed", "no open/degraded/Human Gate marker matched"


def landing_report_count_by(requirements, key):
    counts = {}
    for requirement in requirements:
        value = requirement.get(key) or "(empty)"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def landing_report_build(paths=None):
    check_paths = paths if paths else landing_default_check_paths()
    markdown_files = iter_markdown_files(check_paths)
    formal_files = [path for path in markdown_files if landing_is_formal_spec(path)]
    requirements = []
    for path in formal_files:
        requirements.extend(landing_extract_requirements_file(path))

    for requirement in requirements:
        status, reason = landing_report_infer_status(requirement)
        owner_area = LANDING_REPORT_OWNER_AREAS.get(requirement["requirement_type"], "unknown")
        requirement["status"] = status
        requirement["status_reason"] = reason
        requirement["owner_area"] = owner_area
        requirement["suggested_writeback"] = LANDING_REPORT_WRITEBACK_AREAS.get(owner_area, "manual_review")

    source_files = sorted({requirement["source"] for requirement in requirements})
    return {
        "metadata": {
            "tool": "tools/specs_validate.py",
            "report": "landing-report",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "checked_file_count": len(formal_files),
            "source_count": len(source_files),
            "requirement_count": len(requirements),
        },
        "summary": {
            "by_status": landing_report_count_by(requirements, "status"),
            "by_type": landing_report_count_by(requirements, "requirement_type"),
            "by_sync_type": landing_report_count_by(requirements, "sync_type"),
            "by_owner_area": landing_report_count_by(requirements, "owner_area"),
        },
        "requirements": requirements,
    }


def landing_report_shorten(text, limit=96):
    text = str(text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def landing_report_format_text(report):
    lines = ["规范落地要求聚合报告"]
    metadata = report["metadata"]
    lines.append(f"- 检查文件数: {metadata['checked_file_count']}")
    lines.append(f"- 来源文件数: {metadata['source_count']}")
    lines.append(f"- 要求数: {metadata['requirement_count']}")
    lines.append("- 状态判断: Code 派生启发式，非事实源")

    for title, key in [
        ("按状态", "by_status"),
        ("按落地要求类型", "by_type"),
        ("按同步类型", "by_sync_type"),
        ("按承接区域", "by_owner_area"),
    ]:
        lines.append("")
        lines.append(f"{title}:")
        counts = report["summary"][key]
        if not counts:
            lines.append("- 无")
            continue
        for name, count in counts.items():
            lines.append(f"- {name}: {count}")

    actionable = [item for item in report["requirements"] if item["status"] != "closed"]
    lines.append("")
    lines.append("需关注项:")
    if not actionable:
        lines.append("- 无")
    else:
        for item in actionable:
            content = landing_report_shorten(item["content"])
            lines.append(
                f"- {item['source']}:{item['line']} "
                f"[{item['status']}/{item['requirement_type']}/{item['owner_area']}] "
                f"{content} -> {item['status_reason']}; suggested_writeback: {item['suggested_writeback']}"
            )

    return "\n".join(lines)


def landing_report_main(paths=None, output_format="text"):
    report = landing_report_build(paths)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(landing_report_format_text(report))
    return 0


def landing_check_file(path):
    issues = []
    if not landing_is_formal_spec(path):
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
            title = landing_strip_section_number(heading.group(2).strip())
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

        cells = landing_split_cells(stripped)
        if landing_is_separator(cells):
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
        len(match.group(1)) == 2 and landing_strip_section_number(match.group(2).strip()) == LANDING_SECTION_TITLE
        for match in (HEADING_RE.match(line) for line in lines)
        if match
    ):
        issues.append(Issue(path, 1, "正式规范文档缺少规范落地要求章节", code="LANDING_SECTION_MISSING"))

    return issues


def landing_check_paths(paths):
    issues = []
    for path in iter_markdown_files(paths):
        issues.extend(landing_check_file(path))
    return issues


def landing_main(paths):
    check_paths = paths if paths else landing_default_check_paths()
    issues = landing_check_paths(check_paths)
    if issues:
        print(f"规范落地要求检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("规范落地要求检查通过。")
    return 0


# ══════════════════════════════════════════════════════════════════════
# human-gate — Human Gate 最小证据结构检查
# ══════════════════════════════════════════════════════════════════════

HUMAN_GATE_HEADER_RE = re.compile(r"^Human Gate\s*记录[:：]\s*$", re.IGNORECASE)
HUMAN_GATE_FIELD_RE = re.compile(r"^\s*[-*]\s*(?P<label>[^:：]+?)\s*[:：]\s*(?P<value>.*)$")
HUMAN_GATE_REQUIRED_FIELDS = [
    ("触发原因", ["触发原因", "Gate 触发原因"]),
    ("确认事项", ["确认事项", "确认对象", "确认对象或确认事项"]),
    ("影响范围", ["影响范围"]),
    ("确认依据", ["确认依据", "确认上下文", "依据"]),
    ("Human 决策", ["Human 决策", "Human 选择", "确认结果", "用户选择"]),
    ("确认人/时间", ["确认人/时间", "确认人和时间", "确认来源和时间", "确认人及时间"]),
    ("后续动作", ["后续动作", "后续执行动作", "确认后的执行动作"]),
    ("验证方式", ["验证方式", "验证结果", "验证方式或结果"]),
    ("回写位置", ["回写位置"]),
    ("残留风险", ["残留风险", "残留风险或后续 Task"]),
]


def human_gate_default_check_paths():
    paths = []
    for path in [DOCS_DIR, PROJECT_ROOT / "ldvh-base"]:
        if path.exists():
            paths.append(str(path))
    return paths


def human_gate_normalize_label(label):
    return label.strip().strip("*").strip("`").strip()


def human_gate_alias_map():
    aliases = {}
    for canonical, labels in HUMAN_GATE_REQUIRED_FIELDS:
        for label in labels:
            aliases[label] = canonical
    return aliases


def human_gate_parse_field_line(line):
    match = HUMAN_GATE_FIELD_RE.match(line)
    if not match:
        return None
    label = human_gate_normalize_label(match.group("label"))
    value = match.group("value").strip().strip("*").strip()
    return label, value


def human_gate_collect_record(lines, start_index):
    block = []
    for index in range(start_index + 1, len(lines)):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            if block:
                break
            continue
        if HEADING_RE.match(line) or stripped == "---" or HUMAN_GATE_HEADER_RE.match(stripped):
            break
        if block and not stripped.startswith(("-", "*")) and not line.startswith((" ", "\t")):
            break
        block.append((index + 1, line))
    return block


def human_gate_record_fields(block):
    aliases = human_gate_alias_map()
    fields = {}
    field_lines = {}

    for position, (line_number, line) in enumerate(block):
        parsed = human_gate_parse_field_line(line)
        if not parsed:
            continue
        label, value = parsed
        canonical = aliases.get(label)
        if not canonical:
            continue

        continuation = []
        for _, next_line in block[position + 1 :]:
            next_parsed = human_gate_parse_field_line(next_line)
            if next_parsed and aliases.get(next_parsed[0]):
                break
            if next_line.strip():
                continuation.append(next_line.strip())

        text = "\n".join(item for item in [value, *continuation] if item).strip()
        fields[canonical] = text
        field_lines[canonical] = line_number

    return fields, field_lines


def human_gate_check_file(path):
    issues = []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_code_block = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if not HUMAN_GATE_HEADER_RE.match(stripped):
            continue

        block = human_gate_collect_record(lines, index)
        fields, field_lines = human_gate_record_fields(block)
        if not fields:
            issues.append(Issue(path, index + 1, "Human Gate 记录缺少可识别字段", code="HUMAN_GATE_RECORD_EMPTY"))

        for canonical, _ in HUMAN_GATE_REQUIRED_FIELDS:
            if canonical not in fields:
                issues.append(
                    Issue(path, index + 1, f"Human Gate 记录缺少字段: {canonical}", code="HUMAN_GATE_FIELD_MISSING")
                )
            elif not fields[canonical]:
                issues.append(
                    Issue(path, field_lines[canonical], f"Human Gate 记录字段为空: {canonical}", code="HUMAN_GATE_FIELD_EMPTY")
                )

    return issues


def human_gate_check_paths(paths):
    issues = []
    for path in iter_markdown_files(paths):
        issues.extend(human_gate_check_file(path))
    return issues


def human_gate_main(paths):
    check_paths = paths if paths else human_gate_default_check_paths()
    issues = human_gate_check_paths(check_paths)
    if issues:
        print(f"Human Gate 最小证据结构检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("Human Gate 最小证据结构检查通过。")
    return 0


# ══════════════════════════════════════════════════════════════════════
# env-init — LDVH 自身项目根目录环境初始化记录检查
# ══════════════════════════════════════════════════════════════════════

ENV_INIT_FILENAME = "LDVH-ENVIRONMENT-INITIALIZATION.md"
ENV_INIT_REQUIRED_TITLE = "LDVH 环境初始化记录"
ENV_INIT_REQUIRED_SECTIONS = [
    "这个文件是什么",
    "适配状态与持续提醒",
    "初始化摘要",
    "能力核验来源",
    "环境适配映射",
    "当前运行投影状态",
    "初始化动作",
    "更新规则",
    "Human Gate 与检查",
    "未决限制与后续事项",
]
ENV_INIT_REQUIRED_STATUS_FIELDS = [
    "记录适用项目",
    "记录适用环境",
    "LDVH 当前项目",
    "当前开发环境",
    "权限边界",
    "Human 授权状态",
    "适配状态",
    "最近 Human 确认",
]
ENV_INIT_FORBIDDEN_LEGACY_HEADINGS = [
    "What This File Is",
    "Initialization Summary",
    "Capability Verification Source",
    "Environment Adaptation Mapping",
    "Current Runtime Projection Status",
    "Initialization Actions",
    "Update Rules",
    "Human Gate And Checks",
    "Open Limits And Follow-ups",
]


def env_init_strip_section_number(title):
    return DOC_NUMBERED_HEADING_RE.sub("", title, count=1).strip()


def env_init_table_fields_under_heading(lines, heading_title):
    fields = set()
    in_code_block = False
    in_section = False
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        heading = HEADING_RE.match(line)
        if heading:
            title = env_init_strip_section_number(heading.group(2).strip())
            if in_section and in_table:
                break
            in_section = title == heading_title
            in_table = False
            continue
        if not in_section:
            continue
        if not stripped:
            continue
        if not stripped.startswith("|"):
            if in_table:
                break
            continue
        cells = landing_split_cells(stripped)
        if landing_is_separator(cells):
            continue
        if cells and cells[0] in {"检查项", "字段"}:
            in_table = True
            continue
        if len(cells) >= 2:
            in_table = True
            fields.add(cells[0])
    return fields


def env_init_check_root(root):
    root = Path(root)
    path = root / ENV_INIT_FILENAME
    issues = []
    if not path.exists():
        return [
            Issue(
                path,
                1,
                f"LDVH 项目根目录缺少环境初始化记录: {ENV_INIT_FILENAME}；请先按 04.03 模板创建并完成 LDVH 自身项目与当前开发环境适配",
                code="ENV_INIT_MISSING",
            )
        ]
    if not path.is_file():
        return [Issue(path, 1, f"环境初始化记录不是文件: {ENV_INIT_FILENAME}", code="ENV_INIT_NOT_FILE")]

    lines = path.read_text(encoding="utf-8").splitlines()
    title = None
    headings = set()
    in_code_block = False
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        raw_title = match.group(2).strip()
        clean_title = env_init_strip_section_number(raw_title)
        if level == 1 and title is None:
            title = raw_title
        if level == 2:
            headings.add(clean_title)
            if clean_title in ENV_INIT_FORBIDDEN_LEGACY_HEADINGS:
                issues.append(Issue(path, index, f"环境初始化记录仍使用过期英文章节名: {clean_title}", code="ENV_INIT_LEGACY_HEADING"))

    if title != ENV_INIT_REQUIRED_TITLE:
        issues.append(Issue(path, 1, f"环境初始化记录一级标题应为: {ENV_INIT_REQUIRED_TITLE}", code="ENV_INIT_TITLE_INVALID"))

    for section in ENV_INIT_REQUIRED_SECTIONS:
        if section not in headings:
            issues.append(Issue(path, 1, f"环境初始化记录缺少必备章节: {section}", code="ENV_INIT_SECTION_MISSING"))

    status_fields = env_init_table_fields_under_heading(lines, "适配状态与持续提醒")
    for field in ENV_INIT_REQUIRED_STATUS_FIELDS:
        if field not in status_fields:
            issues.append(Issue(path, 1, f"适配状态与持续提醒章节缺少字段: {field}", code="ENV_INIT_STATUS_FIELD_MISSING"))

    return issues


def env_init_main(root):
    issues = env_init_check_root(root)
    if issues:
        print(f"环境初始化记录检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("环境初始化记录检查通过。")
    return 0


# ══════════════════════════════════════════════════════════════════════
# governed-projects — 根目录管辖项目配置检查
# ══════════════════════════════════════════════════════════════════════

GOVERNED_PROJECTS_FILENAME = "LDVH-GOVERNED-PROJECTS.yaml"
GOVERNED_PROJECTS_ROOT_FIELDS = {"product_name", "product_description", "projects"}
GOVERNED_PROJECTS_ITEM_FIELDS = {"id", "name", "description", "path"}
GOVERNED_PROJECTS_REQUIRED_ITEM_FIELDS = {"id", "path"}


def governed_projects_check_root(root):
    root = Path(root)
    path = root / GOVERNED_PROJECTS_FILENAME
    issues = []
    if not path.exists():
        return [
            Issue(
                path,
                1,
                f"LDVH 项目根目录缺少管辖项目配置: {GOVERNED_PROJECTS_FILENAME}",
                code="GOVERNED_PROJECTS_MISSING",
            )
        ]
    if not path.is_file():
        return [Issue(path, 1, f"管辖项目配置不是文件: {GOVERNED_PROJECTS_FILENAME}", code="GOVERNED_PROJECTS_NOT_FILE")]

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [Issue(path, 1, f"管辖项目配置 YAML 解析失败: {exc}", code="GOVERNED_PROJECTS_YAML_INVALID")]

    if not isinstance(data, dict):
        return [Issue(path, 1, "管辖项目配置根对象必须是 mapping，且只包含 product_name、product_description、projects 字段", code="GOVERNED_PROJECTS_ROOT_INVALID")]

    root_fields = set(data)
    extra_root_fields = sorted(root_fields - GOVERNED_PROJECTS_ROOT_FIELDS)
    missing_root_fields = sorted(GOVERNED_PROJECTS_ROOT_FIELDS - root_fields)
    for field in missing_root_fields:
        issues.append(Issue(path, 1, f"管辖项目配置缺少根字段: {field}", code="GOVERNED_PROJECTS_ROOT_FIELD_MISSING"))
    for field in extra_root_fields:
        issues.append(Issue(path, 1, f"管辖项目配置不得包含根字段: {field}", code="GOVERNED_PROJECTS_ROOT_FIELD_FORBIDDEN"))
    for field in sorted({"product_name", "product_description"} & root_fields):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(Issue(path, 1, f"管辖项目配置根字段 {field} 必须是非空字符串", code="GOVERNED_PROJECTS_ROOT_FIELD_INVALID"))

    projects = data.get("projects")
    if not isinstance(projects, list):
        issues.append(Issue(path, 1, "projects 必须是列表；没有管辖项目时使用空列表", code="GOVERNED_PROJECTS_LIST_INVALID"))
        return issues

    seen_ids = {}
    for index, project in enumerate(projects, start=1):
        if not isinstance(project, dict):
            issues.append(Issue(path, 1, f"projects[{index}] 必须是对象", code="GOVERNED_PROJECT_ITEM_INVALID"))
            continue
        item_fields = set(project)
        missing_fields = sorted(GOVERNED_PROJECTS_REQUIRED_ITEM_FIELDS - item_fields)
        extra_fields = sorted(item_fields - GOVERNED_PROJECTS_ITEM_FIELDS)
        for field in missing_fields:
            issues.append(Issue(path, 1, f"projects[{index}] 缺少字段: {field}", code="GOVERNED_PROJECT_FIELD_MISSING"))
        for field in extra_fields:
            issues.append(Issue(path, 1, f"projects[{index}] 不得包含字段: {field}", code="GOVERNED_PROJECT_FIELD_FORBIDDEN"))
        for field in sorted(GOVERNED_PROJECTS_ITEM_FIELDS & item_fields):
            value = project.get(field)
            if not isinstance(value, str) or not value.strip():
                issues.append(Issue(path, 1, f"projects[{index}].{field} 必须是非空字符串", code="GOVERNED_PROJECT_FIELD_INVALID"))
        project_id = project.get("id")
        if isinstance(project_id, str) and project_id.strip():
            normalized_id = project_id.strip()
            if normalized_id in seen_ids:
                first_index = seen_ids[normalized_id]
                issues.append(Issue(path, 1, f"管辖项目 id 重复: {normalized_id}（projects[{first_index}] 与 projects[{index}]）", code="GOVERNED_PROJECT_ID_DUPLICATE"))
            else:
                seen_ids[normalized_id] = index

    return issues


def governed_projects_main(root):
    issues = governed_projects_check_root(root)
    if issues:
        print(f"管辖项目配置检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("管辖项目配置检查通过。")
    return 0


# ══════════════════════════════════════════════════════════════════════
# index — 生成索引
# ══════════════════════════════════════════════════════════════════════

INDEX_INPUT_PATTERNS = ("*.md",)
INDEX_NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
INDEX_HEADER_FIELD_RE = re.compile(r"^>\s*([^：:]+)[：:]\s*(.*)\s*$")
INDEX_BACKTICK_MD_RE = re.compile(r"`([^`]+\.md)`")
INDEX_PLAIN_SPECS_MD_RE = re.compile(
    r"(?<![`\w./-])((?:specs/(?:evals/|refs/)?|docs/(?:specs|evals|refs)/)[^\s`，。；、)）]+\.md)"
)
INDEX_SECTION_REF_RE = re.compile(r"§([一二三四五六七八九十百千万\d]+(?:\.\d+)*)")
INDEX_DOC_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)?)-")


class SpecsIndexError(Exception):
    pass


class SpecsChecker:
    def __init__(self, root, specs_dir="specs"):
        self.root = Path(root).resolve()
        raw_specs_dir = Path(specs_dir)
        self.specs_dir = raw_specs_dir.resolve() if raw_specs_dir.is_absolute() else (self.root / raw_specs_dir).resolve()

    def scan_files(self):
        files = []
        for pattern in INDEX_INPUT_PATTERNS:
            files.extend(self.specs_dir.glob(pattern))
        return sorted(path.resolve() for path in files if path.is_file())

    def build(self):
        files = self.scan_files()
        docs = []
        sections = []
        relations = []
        mechanisms = []
        diagnostics = []
        for path in files:
            parsed = self.parse_file(path)
            docs.append(parsed["doc"])
            sections.extend(parsed["sections"])
            relations.extend(parsed["relations"])
            mechanisms.extend(parsed["mechanisms"])
            diagnostics.extend(parsed["diagnostics"])
        return {
            "metadata": {
                "derived": True,
                "source_of_truth": False,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "tool": "tools/specs_validate.py",
                "input_patterns": list(INDEX_INPUT_PATTERNS),
                "root": str(self.root),
            },
            "docs": docs,
            "sections": sections,
            "relations": relations,
            "mechanisms": mechanisms,
            "diagnostics": diagnostics,
        }

    def parse_file(self, path):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        rel_path = self.relative_path(path)
        content_hash = self.sha256(text)
        headings = self.extract_headings(path, lines, content_hash)
        header = self.extract_header(lines)
        title = self.extract_title(lines)
        doc_number = self.extract_doc_number(path)
        doc_kind = self.infer_doc_kind(path, title, header)
        diagnostics = self.diagnose_document(path, lines, title, header, headings, doc_kind)
        return {
            "doc": {
                "path": rel_path,
                "title": title,
                "doc_number": doc_number,
                "doc_kind": doc_kind,
                "created_at": header.get("创建日期"),
                "updated_at": header.get("更新日期"),
                "positioning": header.get("定位"),
                "scope": header.get("适用范围"),
                "parent_doc": header.get("所属主文档"),
                "relation": header.get("关系"),
                "basis": self.extract_paths_from_value(header.get("上位依据")),
                "related_specs": self.extract_paths_from_value(header.get("相关规范")),
                "index_scope": header.get("索引范围"),
                "header": header,
                "content_hash": content_hash,
                "parse_status": "ok" if not any(item["severity"] == "error" for item in diagnostics) else "error",
            },
            "sections": headings,
            "relations": self.extract_relations(path, lines, header, content_hash),
            "mechanisms": self.extract_mechanisms(path, lines, content_hash),
            "diagnostics": diagnostics,
        }

    def extract_title(self, lines):
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) == 1:
                return match.group(2).strip()
        return None

    def extract_header(self, lines):
        header = {}
        for line in lines[:80]:
            stripped = line.strip()
            if stripped == "---" and header:
                break
            match = INDEX_HEADER_FIELD_RE.match(line)
            if match:
                header[match.group(1).strip()] = match.group(2).strip()
        return header

    def extract_headings(self, path, lines, content_hash):
        raw = []
        in_code = False
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            match = HEADING_RE.match(line)
            if not match:
                continue
            level = len(match.group(1))
            if level == 1:
                continue
            title = match.group(2).strip()
            raw.append({"level": level, "title": title, "line_start": line_number})
        sections = []
        stack = []
        for index, item in enumerate(raw):
            line_end = len(lines)
            for later in raw[index + 1 :]:
                if later["level"] <= item["level"]:
                    line_end = later["line_start"] - 1
                    break
            while stack and stack[-1]["level"] >= item["level"]:
                stack.pop()
            parent = stack[-1]["section_number"] if stack else None
            section_number = self.extract_section_number(item["title"])
            record = {
                "path": self.relative_path(path),
                "heading_level": item["level"],
                "section_number": section_number,
                "title": self.strip_section_number(item["title"]),
                "raw_title": item["title"],
                "line_start": item["line_start"],
                "line_end": line_end,
                "parent_section": parent,
                "content_hash": content_hash,
            }
            sections.append(record)
            stack.append({"level": item["level"], "section_number": section_number})
        return sections

    def extract_relations(self, path, lines, header, content_hash):
        relations = []
        for field, relation_kind in (("上位依据", "basis"), ("相关规范", "related_spec"), ("所属主文档", "parent_doc")):
            value = header.get(field)
            if value:
                for target in self.extract_paths_from_value(value):
                    relations.append(self.relation_record(path, 0, relation_kind, target, content_hash, "header_field"))
        in_code = False
        seen_line_refs = set()
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            for target in self.extract_markdown_paths(line):
                key = (line_number, "path", target)
                if key not in seen_line_refs:
                    relations.append(self.relation_record(path, line_number, "path_ref", target, content_hash, "body_path"))
                    seen_line_refs.add(key)
            for match in INDEX_SECTION_REF_RE.finditer(line):
                section = match.group(1)
                key = (line_number, "section", section)
                if key not in seen_line_refs:
                    relations.append(
                        {
                            "source_path": self.relative_path(path),
                            "source_line": line_number,
                            "relation_kind": "section_ref",
                            "target_ref": f"§{section}",
                            "target_path": None,
                            "target_exists": None,
                            "target_section": section,
                            "parse_method": "body_section",
                            "content_hash": content_hash,
                        }
                    )
                    seen_line_refs.add(key)
        return relations

    def extract_mechanisms(self, path, lines, content_hash):
        mechanisms = []
        in_section = False
        in_table = False
        header_seen = False
        in_code = False
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            heading = HEADING_RE.match(line)
            if heading:
                title = heading.group(2).strip()
                in_section = (
                    "规范落地要求" in title
                    or "机制承接关系" in title
                    or "机制落地关系" in title
                    or "机制关系声明" in title
                )
                in_table = False
                header_seen = False
                continue
            if not in_section:
                continue
            if not stripped:
                if in_table:
                    break
                continue
            if not stripped.startswith("|"):
                if in_table:
                    break
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) < 4:
                continue
            if all(set(cell) <= {"-", ":", " "} for cell in cells):
                continue
            if not header_seen:
                header_seen = True
                in_table = True
                continue
            mechanisms.append(
                {
                    "source_doc": self.relative_path(path),
                    "source_line": line_number,
                    "mechanism": self.clean_cell(cells[0]),
                    "entity": self.clean_cell(cells[1]),
                    "relation_type": self.clean_cell(cells[2]),
                    "sync_trigger": self.clean_cell(cells[3]),
                    "landing_requirement": self.clean_cell(cells[0]) if len(cells) >= 5 else None,
                    "requirement_content": self.clean_cell(cells[1]) if len(cells) >= 5 else None,
                    "guarantee_mechanism": self.clean_cell(cells[2]) if len(cells) >= 5 else None,
                    "sync_type": self.clean_cell(cells[3]) if len(cells) >= 5 else None,
                    "landing_trigger": self.clean_cell(cells[4]) if len(cells) >= 5 else None,
                    "content_hash": content_hash,
                }
            )
        return mechanisms

    def diagnose_document(self, path, lines, title, header, sections, doc_kind):
        diagnostics = []
        rel_path = self.relative_path(path)
        if not title:
            diagnostics.append(self.diagnostic(rel_path, 1, "error", "MISSING_TITLE", "文档缺少一级标题"))
        required = self.required_header_fields(doc_kind)
        if self.extract_doc_number(path) == "00":
            required = [field for field in required if field != "上位依据"]
        for field in required:
            if not header.get(field):
                diagnostics.append(self.diagnostic(rel_path, 1, "warning", "MISSING_HEADER_FIELD", f"头部字段缺失: {field}"))
        numbers = {}
        for section in sections:
            number = section["section_number"]
            if not number:
                continue
            if number in numbers:
                diagnostics.append(
                    self.diagnostic(rel_path, section["line_start"], "warning", "DUPLICATE_SECTION_NUMBER", f"章节编号重复: §{number}")
                )
            numbers[number] = section["line_start"]
        in_code = False
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            for target in self.extract_markdown_paths(line):
                resolved = self.resolve_target_path(target, path)
                if not resolved.exists():
                    diagnostics.append(
                        self.diagnostic(rel_path, line_number, "warning", "BROKEN_MARKDOWN_PATH", f"Markdown 路径引用不存在: {target}")
                    )
        return diagnostics

    def relation_record(self, path, line_number, relation_kind, target, content_hash, parse_method):
        resolved = self.resolve_target_path(target, path)
        return {
            "source_path": self.relative_path(path),
            "source_line": line_number,
            "relation_kind": relation_kind,
            "target_ref": target,
            "target_path": self.relative_path(resolved) if self.is_inside_root(resolved) else str(resolved),
            "target_exists": resolved.exists(),
            "target_section": None,
            "parse_method": parse_method,
            "content_hash": content_hash,
        }

    def extract_markdown_paths(self, text):
        paths = []
        for match in INDEX_BACKTICK_MD_RE.finditer(text):
            paths.append(match.group(1))
        for match in INDEX_PLAIN_SPECS_MD_RE.finditer(text):
            paths.append(match.group(1))
        return sorted(set(paths), key=paths.index)

    def extract_paths_from_value(self, value):
        if not value:
            return []
        return self.extract_markdown_paths(value)

    def clean_cell(self, value):
        text = str(value).strip()
        if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
            return text[1:-1]
        return text

    def resolve_target_path(self, raw_path, current_path):
        raw = str(raw_path)
        if raw.startswith("specs/") or raw.startswith("docs/"):
            return (self.root / raw).resolve()
        if raw.startswith("./") or raw.startswith("../"):
            return (current_path.parent / raw).resolve()
        if raw in {ENV_INIT_FILENAME, "README.md"}:
            return (self.root / raw).resolve()
        return (self.specs_dir / raw).resolve()

    def required_header_fields(self, doc_kind):
        if doc_kind == "evals":
            return ["创建日期", "定位", "调研边界", "执行效力", "编号归属"]
        if doc_kind == "refs":
            return ["创建日期", "来源", "定位"]
        if doc_kind == "subdocument":
            return ["创建日期", "所属主文档", "关系", "适用范围", "上位依据"]
        return ["创建日期", "定位", "适用范围", "上位依据"]

    def infer_doc_kind(self, path, title, header):
        rel = path.relative_to(self.root)
        parts = rel.parts
        if len(parts) >= 2 and parts[0] == "docs" and parts[1] == "evals":
            return "evals"
        if len(parts) >= 2 and parts[0] == "docs" and parts[1] == "refs":
            return "refs"
        if len(parts) >= 2 and parts[0] == "specs" and parts[1] == "evals":
            return "evals"
        if len(parts) >= 2 and parts[0] == "specs" and parts[1] == "refs":
            return "refs"
        if header.get("所属主文档"):
            return "subdocument"
        if title and "集合索引" in title:
            return "collection_index"
        return "formal_spec"

    def extract_doc_number(self, path):
        match = INDEX_DOC_NUMBER_RE.match(path.name)
        return match.group(1) if match else None

    def extract_section_number(self, title):
        match = INDEX_NUMBERED_HEADING_RE.match(title)
        return match.group(1) if match else None

    def strip_section_number(self, title):
        return INDEX_NUMBERED_HEADING_RE.sub("", title, count=1).strip()

    def relative_path(self, path):
        try:
            return str(Path(path).resolve().relative_to(self.root))
        except ValueError:
            return str(path)

    def is_inside_root(self, path):
        try:
            Path(path).resolve().relative_to(self.root)
            return True
        except ValueError:
            return False

    def sha256(self, text):
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    def diagnostic(self, path, line, severity, code, message):
        return {"severity": severity, "path": path, "line": line, "code": code, "message": message}


def write_outputs(indexes, out_dir):
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    metadata = indexes["metadata"]
    outputs = {
        "specs-docs-index.json": {"metadata": metadata, "docs": indexes["docs"]},
        "specs-sections-index.json": {"metadata": metadata, "sections": indexes["sections"]},
        "specs-relations-index.json": {"metadata": metadata, "relations": indexes["relations"]},
        "specs-mechanism-index.json": {"metadata": metadata, "mechanisms": indexes["mechanisms"]},
        "specs-diagnostics.json": {"metadata": metadata, "diagnostics": indexes["diagnostics"]},
    }
    for name, payload in outputs.items():
        (out_path / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return sorted(outputs)


def index_main(root, out=None, fail_on_diagnostics=False, specs_dir="specs"):
    checker = SpecsChecker(root, specs_dir)
    if not checker.specs_dir.exists() and specs_dir == "docs/specs":
        legacy_checker = SpecsChecker(root, "specs")
        if legacy_checker.specs_dir.exists():
            checker = legacy_checker
    if not checker.specs_dir.exists():
        raise SpecsIndexError(f"规范目录不存在: {checker.specs_dir}")
    indexes = checker.build()
    if out:
        written = write_outputs(indexes, out)
        print(f"已生成 specs 文档派生索引与诊断结果: {out}")
        for name in written:
            print(f"- {name}")
    else:
        print(json.dumps(indexes, ensure_ascii=False, indent=2))
    if fail_on_diagnostics and indexes["diagnostics"]:
        return 1
    return 0


def infer_specs_dir_from_paths(paths):
    if not paths:
        return "docs/specs"
    resolved_dirs = []
    for raw_path in paths:
        path = Path(raw_path)
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if rel.parts[:2] == ("docs", "specs"):
            resolved_dirs.append("docs/specs")
        elif rel.parts:
            resolved_dirs.append(rel.parts[0])
    if resolved_dirs and all(item == "docs/specs" for item in resolved_dirs):
        return "docs/specs"
    return "specs"


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

def build_parser():
    parser = argparse.ArgumentParser(description="Specs 文档结构、引用完整性和派生索引统一检查工具。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # doc
    doc_parser = subparsers.add_parser("doc", help="检查 specs Markdown 文档是否符合 03 文档基础规范的章节编号要求。")
    doc_parser.add_argument("paths", nargs="*", default=[str(SPECS_DIR)], help="要检查的 Markdown 文件或目录，默认检查 docs/specs/。")

    # refs
    refs_parser = subparsers.add_parser("refs", help="检查 specs Markdown 文档中的 § 引用是否存在。")
    refs_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/specs/ 根目录正式规范。")

    # landing
    landing_parser = subparsers.add_parser("landing", help="检查 docs/specs 正式规范的规范落地要求表。")
    landing_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/specs/ 根目录正式规范。")

    # landing-report
    landing_report_parser = subparsers.add_parser("landing-report", help="生成 docs/specs 规范落地要求聚合报告。")
    landing_report_parser.add_argument("paths", nargs="*", default=None, help="要聚合的 Markdown 文件或目录，默认检查 docs/specs/ 根目录正式规范。")
    landing_report_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # human-gate
    human_gate_parser = subparsers.add_parser("human-gate", help="检查 Markdown 中的 Human Gate 记录是否符合 06 最小证据结构。")
    human_gate_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/ 和 ldvh-base/。")

    # env-init
    env_init_parser = subparsers.add_parser("env-init", help="检查 LDVH 自身项目根目录环境初始化记录的中文模板结构。")
    env_init_parser.add_argument("--root", default=str(PROJECT_ROOT), help="LDVH 项目根目录，默认使用当前工具所在项目。")

    # governed-projects
    governed_projects_parser = subparsers.add_parser("governed-projects", help="检查 LDVH 根目录管辖项目配置。")
    governed_projects_parser.add_argument("--root", default=str(PROJECT_ROOT), help="LDVH 项目根目录，默认使用当前工具所在项目。")

    # index
    index_parser = subparsers.add_parser("index", help="生成 specs 文档派生索引和诊断结果（03.01 规范文档剖面）。")
    index_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")
    index_parser.add_argument("--specs-dir", default="docs/specs", help="要生成索引的规范目录，默认 docs/specs。")
    index_parser.add_argument("--out", default=None, help="输出目录；未提供时将完整索引输出到 stdout。")
    index_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态。")

    # all
    all_parser = subparsers.add_parser("all", help="运行所有检查（doc + refs + landing + human-gate + index）。")
    all_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/specs/。")
    all_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录（用于 index 子命令）。")
    all_parser.add_argument("--specs-dir", default=None, help="要生成索引的规范目录；未提供时根据 paths 推断，默认 specs。")
    all_parser.add_argument("--out", default=None, help="输出目录（用于 index 子命令）；未提供时将完整索引输出到 stdout。")
    all_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态（用于 index 子命令）。")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    command = args.command

    if command == "doc":
        return doc_main(args.paths)

    if command == "refs":
        paths = args.paths if args.paths is not None else refs_default_check_paths()
        return refs_main(paths)

    if command == "landing":
        return landing_main(args.paths)

    if command == "landing-report":
        return landing_report_main(args.paths, args.format)

    if command == "human-gate":
        return human_gate_main(args.paths)

    if command == "env-init":
        return env_init_main(args.root)

    if command == "governed-projects":
        return governed_projects_main(args.root)

    if command == "index":
        try:
            return index_main(args.root, args.out, args.fail_on_diagnostics, args.specs_dir)
        except SpecsIndexError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    if command == "all":
        exit_code = 0
        doc_paths = args.paths if args.paths else [str(SPECS_DIR)]
        # doc
        if doc_main(doc_paths) != 0:
            exit_code = 1
        # refs
        refs_paths = args.paths if args.paths else refs_default_check_paths()
        if refs_main(refs_paths) != 0:
            exit_code = 1
        # landing
        landing_paths = args.paths if args.paths else landing_default_check_paths()
        if landing_main(landing_paths) != 0:
            exit_code = 1
        # human-gate
        human_gate_paths = args.paths if args.paths else human_gate_default_check_paths()
        if human_gate_main(human_gate_paths) != 0:
            exit_code = 1
        # env-init
        if env_init_main(args.root) != 0:
            exit_code = 1
        # governed-projects
        if governed_projects_main(args.root) != 0:
            exit_code = 1
        # index
        try:
            index_specs_dir = args.specs_dir or infer_specs_dir_from_paths(args.paths)
            if index_main(args.root, args.out, args.fail_on_diagnostics, index_specs_dir) != 0:
                exit_code = 1
        except SpecsIndexError as exc:
            print(str(exc), file=sys.stderr)
            exit_code = 2
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
