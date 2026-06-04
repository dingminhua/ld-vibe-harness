#!/usr/bin/env python3
"""Specs 文档规范、引用完整性和索引生成统一检查工具。"""

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
        print(f"03 Specs 文档规范检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("03 Specs 文档规范检查通过。")
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
    if raw_path.startswith("specs/"):
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
# index — 生成索引
# ══════════════════════════════════════════════════════════════════════

INDEX_INPUT_PATTERNS = ("*.md",)
INDEX_NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
INDEX_HEADER_FIELD_RE = re.compile(r"^>\s*([^：:]+)[：:]\s*(.*)\s*$")
INDEX_BACKTICK_MD_RE = re.compile(r"`([^`]+\.md)`")
INDEX_PLAIN_SPECS_MD_RE = re.compile(r"(?<![`\w./-])(specs/(?:evals/|refs/)?[^\s`，。；、)）]+\.md)")
INDEX_SECTION_REF_RE = re.compile(r"§([一二三四五六七八九十百千万\d]+(?:\.\d+)*)")
INDEX_DOC_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)?)-")


class SpecsIndexError(Exception):
    pass


class SpecsChecker:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.specs_dir = self.root / "specs"

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
                in_section = "机制关系声明" in title
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
        if raw.startswith("specs/"):
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


def index_main(root, out=None, fail_on_diagnostics=False):
    checker = SpecsChecker(root)
    if not checker.specs_dir.exists():
        raise SpecsIndexError(f"specs 目录不存在: {checker.specs_dir}")
    indexes = checker.build()
    if out:
        written = write_outputs(indexes, out)
        print(f"已生成 03.01 specs 文档检查结果: {out}")
        for name in written:
            print(f"- {name}")
    else:
        print(json.dumps(indexes, ensure_ascii=False, indent=2))
    if fail_on_diagnostics and indexes["diagnostics"]:
        return 1
    return 0


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

def build_parser():
    parser = argparse.ArgumentParser(description="Specs 文档规范、引用完整性和索引生成统一检查工具。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # doc
    doc_parser = subparsers.add_parser("doc", help="检查 specs Markdown 文档是否符合 03-Specs 文档规范的章节编号要求。")
    doc_parser.add_argument("paths", nargs="*", default=[str(SPECS_DIR)], help="要检查的 Markdown 文件或目录，默认检查 specs/。")

    # refs
    refs_parser = subparsers.add_parser("refs", help="检查 specs Markdown 文档中的 § 引用是否存在。")
    refs_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")

    # index
    index_parser = subparsers.add_parser("index", help="检查 03.01 specs 文档质量，输出派生索引和诊断结果。")
    index_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")
    index_parser.add_argument("--out", default=None, help="输出目录；未提供时将完整索引输出到 stdout。")
    index_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态。")

    # all
    all_parser = subparsers.add_parser("all", help="运行所有检查（doc + refs + index）。")
    all_parser.add_argument("paths", nargs="*", default=[str(SPECS_DIR)], help="要检查的 Markdown 文件或目录，默认检查 specs/。")
    all_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录（用于 index 子命令）。")
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

    if command == "index":
        try:
            return index_main(args.root, args.out, args.fail_on_diagnostics)
        except SpecsIndexError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    if command == "all":
        exit_code = 0
        # doc
        if doc_main(args.paths) != 0:
            exit_code = 1
        # refs
        refs_paths = args.paths if args.paths else refs_default_check_paths()
        if refs_main(refs_paths) != 0:
            exit_code = 1
        # index
        try:
            if index_main(args.root, args.out, args.fail_on_diagnostics) != 0:
                exit_code = 1
        except SpecsIndexError as exc:
            print(str(exc), file=sys.stderr)
            exit_code = 2
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
