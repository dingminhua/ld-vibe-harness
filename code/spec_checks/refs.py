"""Markdown section reference checks for LDVH specs."""

import re
from dataclasses import dataclass
from pathlib import Path

from .common import HEADING_RE, Issue, iter_markdown_files, relative_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = PROJECT_ROOT / "specs"
LEGACY_SPECS_DIR = PROJECT_ROOT / "docs" / "specs"
REFS_SECTION_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
REFS_SECTION_REF_RE = re.compile(r"§([一二三四五六七八九十百千万\d]+(?:\.\d+)*)")
REFS_EXPLICIT_PATH_RE = re.compile(r"`([^`]+\.md)`\s*$")
REFS_SHORTHAND_RE = re.compile(r"(\d+(?:\.\d+)?)\s*$")
REFS_CHINESE_SECTION_RE = re.compile(r"^[一二三四五六七八九十百千万]+(?:\.\d+)*$")


@dataclass
class Document:
    path: Path
    sections: set


def extract_sections(path):
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


def build_document_map(paths):
    documents = {}
    scan_paths = list(paths)
    if SPECS_DIR.exists():
        scan_paths.append(SPECS_DIR)
    if LEGACY_SPECS_DIR.exists():
        scan_paths.append(LEGACY_SPECS_DIR)
    for path in iter_markdown_files(scan_paths):
        documents[path.resolve()] = Document(path.resolve(), extract_sections(path))
    return documents


def resolve_markdown_path(raw_path, current_path):
    if raw_path.startswith("specs/") or raw_path.startswith("docs/"):
        return (PROJECT_ROOT / raw_path).resolve()
    if raw_path.startswith("./") or raw_path.startswith("../"):
        return (current_path.parent / raw_path).resolve()
    return (SPECS_DIR / raw_path).resolve()


def resolve_shorthand(prefix, documents):
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


def resolve_parent_document(path, documents):
    match = re.match(r"^(\d+)\.\d+-", path.name)
    if not match:
        return None
    return resolve_shorthand(match.group(1), documents)


def default_check_paths():
    return [str(path) for path in sorted(SPECS_DIR.glob("*.md"))]


def check_section_target(issues, source_path, line_number, target_path, section, documents, code):
    document = documents.get(target_path)
    if document is None:
        issues.append(Issue(source_path, line_number, f"引用文件不存在: {target_path}", code="FILE_NOT_FOUND"))
        return
    if section not in document.sections:
        issues.append(Issue(source_path, line_number, f"引用章节不存在: {relative_path(target_path, PROJECT_ROOT)} §{section}", code=code))


def check_file(path, documents):
    issues = []
    source_path = path.resolve()
    source_document = documents.get(source_path, Document(source_path, extract_sections(source_path)))
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
                target_path = resolve_markdown_path(explicit_match.group(1), source_path)
                check_section_target(issues, source_path, line_number, target_path, section, documents, "MISSING_EXTERNAL_SECTION")
                continue

            shorthand_match = REFS_SHORTHAND_RE.search(before)
            if shorthand_match:
                prefix = shorthand_match.group(1)
                target_path = resolve_shorthand(prefix, documents)
                if target_path is None:
                    issues.append(Issue(source_path, line_number, f"速记引用无法解析目标文件: {prefix} §{section}", code="SHORTHAND_UNRESOLVED"))
                    continue
                check_section_target(issues, source_path, line_number, target_path, section, documents, "MISSING_SHORTHAND_SECTION")
                continue

            parent_path = resolve_parent_document(source_path, documents)
            if parent_path and section in documents[parent_path].sections:
                continue

            if section not in source_document.sections:
                issues.append(Issue(source_path, line_number, f"内部引用章节不存在: §{section}", code="MISSING_INTERNAL_SECTION"))

    return issues


def check_paths(paths):
    documents = build_document_map(paths)
    issues = []
    for path in iter_markdown_files(paths):
        issues.extend(check_file(path, documents))
    return issues


def main(paths):
    issues = check_paths(paths)
    if issues:
        print(f"Specs § 引用检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("Specs § 引用检查通过。")
    return 0
