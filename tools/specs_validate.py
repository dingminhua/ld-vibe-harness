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


# ── 通用常量 ──

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = PROJECT_ROOT / "specs"
SPECS_V2_DIR = PROJECT_ROOT / "specs-v2"
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
    for path in iter_markdown_files(scan_paths):
        documents[path.resolve()] = Document(path.resolve(), refs_extract_sections(path))
    return documents


def refs_resolve_markdown_path(raw_path, current_path):
    if raw_path.startswith("specs/") or raw_path.startswith("specs-v2/"):
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


def landing_default_check_paths():
    if SPECS_V2_DIR.exists():
        return [str(path) for path in sorted(SPECS_V2_DIR.glob("*.md"))]
    return []


def landing_is_formal_spec(path):
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(PROJECT_ROOT)
    except ValueError:
        return False
    return len(rel.parts) == 2 and rel.parts[0] == "specs-v2" and path.suffix == ".md"


def landing_strip_section_number(title):
    return DOC_NUMBERED_HEADING_RE.sub("", title, count=1).strip()


def landing_split_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def landing_is_separator(cells):
    return all(set(cell) <= {"-", ":", " "} for cell in cells)


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
# env-init — 根目录 LDVH 环境初始化记录检查
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
    "用户当前项目",
    "用户当前开发平台",
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
                f"项目根目录缺少环境初始化记录: {ENV_INIT_FILENAME}；请先按 04.03 模板创建并完成当前项目与当前开发平台适配",
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
                issues.append(Issue(path, index, f"环境初始化记录仍使用英文旧章节名: {clean_title}", code="ENV_INIT_LEGACY_HEADING"))

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
# index — 生成索引
# ══════════════════════════════════════════════════════════════════════

INDEX_INPUT_PATTERNS = ("*.md",)
INDEX_NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
INDEX_HEADER_FIELD_RE = re.compile(r"^>\s*([^：:]+)[：:]\s*(.*)\s*$")
INDEX_BACKTICK_MD_RE = re.compile(r"`([^`]+\.md)`")
INDEX_PLAIN_SPECS_MD_RE = re.compile(r"(?<![`\w./-])((?:specs|specs-v2)/(?:evals/|refs/)?[^\s`，。；、)）]+\.md)")
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
        if raw.startswith("specs/") or raw.startswith("specs-v2/"):
            return (self.root / raw).resolve()
        if raw.startswith("./") or raw.startswith("../"):
            return (current_path.parent / raw).resolve()
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
        if len(parts) >= 3 and parts[1] == "evals":
            return "evals"
        if len(parts) >= 3 and parts[1] == "refs":
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
        return "specs"
    resolved_dirs = []
    for raw_path in paths:
        path = Path(raw_path)
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if rel.parts:
            resolved_dirs.append(rel.parts[0])
    if resolved_dirs and all(item == "specs-v2" for item in resolved_dirs):
        return "specs-v2"
    return "specs"


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

def build_parser():
    parser = argparse.ArgumentParser(description="Specs 文档结构、引用完整性和派生索引统一检查工具。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # doc
    doc_parser = subparsers.add_parser("doc", help="检查 specs Markdown 文档是否符合 03 文档基础规范的章节编号要求。")
    doc_parser.add_argument("paths", nargs="*", default=[str(SPECS_DIR)], help="要检查的 Markdown 文件或目录，默认检查 specs/。")

    # refs
    refs_parser = subparsers.add_parser("refs", help="检查 specs Markdown 文档中的 § 引用是否存在。")
    refs_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")

    # landing
    landing_parser = subparsers.add_parser("landing", help="检查 specs-v2 正式规范的规范落地要求表。")
    landing_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs-v2/ 根目录正式规范。")

    # env-init
    env_init_parser = subparsers.add_parser("env-init", help="检查项目根目录 LDVH 环境初始化记录的中文模板结构。")
    env_init_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")

    # index
    index_parser = subparsers.add_parser("index", help="生成 specs 文档派生索引和诊断结果（03.01 规范文档剖面）。")
    index_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")
    index_parser.add_argument("--specs-dir", default="specs", help="要生成索引的规范目录，默认 specs；v2 可传 specs-v2。")
    index_parser.add_argument("--out", default=None, help="输出目录；未提供时将完整索引输出到 stdout。")
    index_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态。")

    # all
    all_parser = subparsers.add_parser("all", help="运行所有检查（doc + refs + landing + index）。")
    all_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/，landing 默认检查 specs-v2/。")
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

    if command == "env-init":
        return env_init_main(args.root)

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
        # env-init
        if env_init_main(args.root) != 0:
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
