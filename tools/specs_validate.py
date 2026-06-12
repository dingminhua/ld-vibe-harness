#!/usr/bin/env python3
"""Specs 文档结构、引用完整性和派生索引统一检查工具。"""

import argparse
import hashlib
import json
import re
import subprocess
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


RUNTIME_PROJECTION_DEFAULT_PATHS = [
    "LDVH-AI-ENTRY.md",
    ".trae/rules",
    ".trae/skills",
]
RUNTIME_PROJECTION_SPEC_REF_RE = re.compile(r"docs/specs/[^`\s，。；、)）]+\.md")
RUNTIME_PROJECTION_AUTHORITY_TERMS = ["docs/specs/", "规范来源", "权威来源", "上位依据", "相关规范"]
RUNTIME_PROJECTION_DEGRADATION_TERMS = ["降级", "人工降级", "degradation"]
RUNTIME_PROJECTION_AUTHORITY_RE = re.compile(r"(docs/specs/|规范来源|权威来源|上位依据|相关规范|降级|人工降级|degradation)")
RUNTIME_PROJECTION_NEGATIVE_AUTHORITY_RE = re.compile(r"(无|没有|缺少|未).{0,8}(权威来源|规范来源|上位依据|相关规范|docs/specs/|降级)")


def runtime_projection_default_paths():
    paths = []
    for raw_path in RUNTIME_PROJECTION_DEFAULT_PATHS:
        path = PROJECT_ROOT / raw_path
        if path.exists():
            paths.append(str(path))
    return paths


def runtime_projection_is_project_local(path):
    try:
        Path(path).resolve().relative_to(PROJECT_ROOT.resolve())
        return True
    except ValueError:
        return False


def runtime_projection_iter_files(paths):
    files = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            continue
        if not runtime_projection_is_project_local(path):
            continue
        if path.is_file() and path.suffix in {".md", ".yaml", ".yml", ".json", ".toml"}:
            files.append(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix in {".md", ".yaml", ".yml", ".json", ".toml"}:
                    files.append(child)
    return sorted(set(files))


def runtime_projection_has_authority(text):
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if RUNTIME_PROJECTION_NEGATIVE_AUTHORITY_RE.search(stripped):
            continue
        if RUNTIME_PROJECTION_AUTHORITY_RE.search(stripped):
            return True
    return False


def runtime_projection_spec_refs(text):
    return sorted(set(RUNTIME_PROJECTION_SPEC_REF_RE.findall(text)))


def runtime_projection_spec_path_exists(ref):
    return (PROJECT_ROOT / ref).exists()


def runtime_projection_formal_spec_lines():
    lines = {}
    if not DOCS_SPECS_DIR.exists():
        return lines
    for spec_path in sorted(DOCS_SPECS_DIR.glob("*.md")):
        for line in spec_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if len(stripped) < 32:
                continue
            if stripped.startswith("|") or stripped.startswith(">") or stripped.startswith("#"):
                continue
            lines.setdefault(stripped, landing_relative_path(spec_path))
    return lines


def runtime_projection_detect_copied_formal_lines(text, formal_lines):
    matches = []
    for line in text.splitlines():
        stripped = line.strip()
        source = formal_lines.get(stripped)
        if source:
            matches.append({"source": source, "text": stripped})
    return matches[:5]


def runtime_projection_check_file(path, formal_lines=None):
    formal_lines = formal_lines if formal_lines is not None else runtime_projection_formal_spec_lines()
    text = path.read_text(encoding="utf-8")
    issues = []
    if not runtime_projection_has_authority(text):
        issues.append(Issue(path, 1, "运行投影缺少 docs/specs 权威来源引用或明确降级来源", code="RUNTIME_PROJECTION_AUTHORITY_MISSING"))
    for ref in runtime_projection_spec_refs(text):
        if not runtime_projection_spec_path_exists(ref):
            issues.append(Issue(path, 1, f"运行投影引用的正式规范不存在: {ref}", code="RUNTIME_PROJECTION_SPEC_REF_MISSING"))
    copied = runtime_projection_detect_copied_formal_lines(text, formal_lines)
    if len(copied) >= 3:
        sources = ", ".join(sorted({item["source"] for item in copied}))
        issues.append(Issue(path, 1, f"运行投影疑似复制正式规范正文，可能产生漂移: {sources}", code="RUNTIME_PROJECTION_BODY_COPIED"))
    return issues


def runtime_projection_issue_status(issue):
    if issue.code == "RUNTIME_PROJECTION_BODY_COPIED":
        return "degraded"
    return "open"


def runtime_projection_report_build(paths=None):
    check_paths = paths if paths is not None else runtime_projection_default_paths()
    files = runtime_projection_iter_files(check_paths)
    formal_lines = runtime_projection_formal_spec_lines()
    issues = []
    for file_path in files:
        issues.extend(runtime_projection_check_file(file_path, formal_lines))
    issue_items = []
    for issue in issues:
        issue_items.append(
            {
                "source": landing_relative_path(issue.path),
                "line": issue.line,
                "code": issue.code,
                "status": runtime_projection_issue_status(issue),
                "message": issue.message,
            }
        )
    status = "closed"
    if any(item["status"] == "open" for item in issue_items):
        status = "open"
    elif any(item["status"] == "degraded" for item in issue_items):
        status = "degraded"
    elif not files:
        status = "open"
    return {
        "metadata": {
            "tool": "tools/specs_validate.py",
            "report": "runtime-projection",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "checked_file_count": len(files),
            "issue_count": len(issue_items),
            "scope": "project-local runtime projections only",
        },
        "summary": {
            "status": status,
            "by_status": landing_report_count_by(issue_items, "status"),
            "by_code": landing_report_count_by(issue_items, "code"),
        },
        "issues": issue_items,
    }


def runtime_projection_format_text(report):
    lines = ["运行投影漂移检查"]
    metadata = report["metadata"]
    lines.append(f"- 检查文件数: {metadata['checked_file_count']}")
    lines.append(f"- 问题数: {metadata['issue_count']}")
    lines.append(f"- 状态: {report['summary']['status']}")
    lines.append("- 状态判断: Code 派生启发式，非事实源")
    lines.append("")
    lines.append("问题:")
    if not report["issues"]:
        lines.append("- 无")
    else:
        for item in report["issues"]:
            lines.append(f"- {item['source']}:{item['line']} [{item['status']}/{item['code']}] {item['message']}")
    return "\n".join(lines)


def runtime_projection_main(paths=None, output_format="text"):
    report = runtime_projection_report_build(paths if paths else None)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(runtime_projection_format_text(report))
    return 0 if report["summary"]["status"] == "closed" else 1


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
LANDING_REPORT_AREA_LABELS = {
    "agent": "Agent",
    "code": "Code / Test",
    "human_gate": "Human Gate",
    "runtime_projection": "运行投影",
    "specs": "Specs",
    "unknown": "未知",
    "workflow": "Workflow / Skill",
}
LANDING_REPORT_WRITEBACK_AREAS = {
    "specs": "specs",
    "runtime_projection": "runtime_projection_or_env_record",
    "workflow": "workflow_or_skill_candidate",
    "agent": "agent_or_44",
    "code": "code_request_or_test",
    "human_gate": "human_gate_record",
}
LANDING_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS = {
    "decision_record_required": "必须人类决策记录",
    "policy_clarification": "规范口径说明",
    "implementation_support": "承接实现支持",
    "diagnostic_coverage": "Code 降级提示/覆盖",
}
LANDING_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS = {
    "current_record_required": "当前需要记录",
    "future_trigger_record": "未来触发时记录",
    "rule_condition_only": "只保留为规则条件",
}
LANDING_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS = {
    "future_evaluation": "未来触发时评估",
    "workflow_design_discussion": "流程创建前讨论",
}
LANDING_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS = {
    "web_human_facing_support": "Web / Human-facing 承接",
}
LANDING_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS = {
    "coverage_degraded": "覆盖范围降级",
}
LANDING_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS = {
    "lifecycle_trigger_sync": "生命周期触发同步",
    "platform_capability_sync": "平台能力承接同步",
    "projection_coverage_diagnostic": "投影覆盖诊断降级",
    "third_party_skill_projection": "第三方 Skill 投影",
}

RUNTIME_PROJECTION_REMEDIATION_LABELS = {
    "doc_crossref_check": "文档交叉引用检查",
    "entry_sync_check": "入口/配置同步检查",
    "platform_mapping_check": "平台能力映射检查",
    "drift_diagnostic": "漂移诊断",
    "skill_projection_check": "Skill 投影检查",
}

RUNTIME_PROJECTION_REMEDIATION_TERMS = {
    "drift_diagnostic": [
        "漂移", "drift",
    ],
    "skill_projection_check": [
        "第三方 Skill", "包装 Skill", "third_party_skill",
    ],
    "platform_mapping_check": [
        "平台清单", "适配清单", "平台适配", "platform_capability",
    ],
    "entry_sync_check": [
        "入口", "Hook", "配置", "Rules", "Agent", "Command",
        "MCP", "AGENTS.md", "config.toml", "sandbox", "approval",
    ],
}
LANDING_REPORT_HUMAN_GATE_DECISION_TERMS = [
    "接受长期降级",
    "关闭",
    "创建",
    "删除",
    "修改",
    "写入",
    "改变",
    "状态流转",
    "事实源",
    "高影响",
    "授权",
    "权限",
    "危险权限",
    "宣称",
    "完整支持",
    "通过",
    "闭环",
    "核心",
    "降级",
]
LANDING_REPORT_HUMAN_GATE_POLICY_TERMS = [
    "评估 Human Gate",
    "应评估 Human Gate",
    "应先讨论",
    "讨论是否",
]
LANDING_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS = [
    "应先讨论",
    "讨论是否",
]
LANDING_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS = [
    "Human Gate UI",
    "展示确认对象",
    "承接 06 §6.3.1",
]
LANDING_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS = [
    "当前已",
    "本次已",
    "已现场确认",
    "已接受长期降级",
    "已判定 LDVH落地与检查闭环",
    "已声明 Human",
]
LANDING_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS = [
    "前",
    "时",
    "发生",
    "变化",
    "用户请求",
    "任一",
    "§",
    "从候选项创建",
]
LANDING_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS = [
    "平台清单",
    "平台能力",
    "Trae Solo",
    "Codex",
    "AGENTS.md",
    "config.toml",
    "sandbox",
    "approval",
    "MCP",
    "refs",
]
LANDING_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS = [
    "第三方 Skill",
    "包装 Skill",
]
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
LANDING_REPORT_CAPABILITY_CHECKS = [
    {
        "id": "41_trigger_safeguard",
        "capability": "41 触发保障",
        "status": "degraded",
        "owner_area": "code",
        "required_terms": ["41", "触发保障"],
        "missing_reason": "landing-report 未发现 41 触发保障声明，无法判断正式规范或运行投影变化是否应进入 41",
        "degraded_reason": "landing-report 只能聚合 41 触发保障要求，尚不能验证所有触发场景是否实际进入 41",
        "suggested_writeback": "code_request_or_test",
    },
    {
        "id": "42_consumes_41",
        "capability": "42 消费 41 触发状态",
        "status": "degraded",
        "owner_area": "workflow",
        "required_terms": ["42", "41", "消费"],
        "missing_reason": "landing-report 未发现 42 消费 41 触发状态声明，无法作为 LDVH落地与检查输入",
        "degraded_reason": "landing-report 能暴露 41/42 联动要求，但尚不能证明 42 现场检查已经消费本次报告",
        "suggested_writeback": "workflow_or_skill_candidate",
    },
    {
        "id": "runtime_projection_drift_check",
        "capability": "运行投影漂移检查",
        "status": "open",
        "owner_area": "runtime_projection",
        "required_terms": ["运行投影", "漂移检查"],
        "missing_reason": "landing-report 未发现运行投影漂移检查声明，无法诊断入口、Skill、Hook、CI、Web 或 Code 投影漂移",
        "degraded_reason": "landing-report 只能识别运行投影漂移检查要求，尚不能读取真实运行投影并比对正式规范",
        "suggested_writeback": "runtime_projection_or_env_record",
    },
    {
        "id": "human_gate_evidence_consumption",
        "capability": "Human Gate 证据消费",
        "status": "degraded",
        "owner_area": "human_gate",
        "required_terms": ["Human Gate", "证据"],
        "missing_reason": "landing-report 未发现 Human Gate 证据消费声明，无法支持降级、关闭或通过声明",
        "degraded_reason": "landing-report 能识别 Human Gate 证据消费要求，但尚未把 Human Gate 记录校验结果并入状态判断",
        "suggested_writeback": "human_gate_record",
    },
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


def landing_report_is_gap(item):
    return item.get("status") != "closed"


def landing_report_human_gate_subcategory(item):
    if "capability" in item:
        return "diagnostic_coverage"
    text = " | ".join(
        [
            item.get("content", ""),
            item.get("guarantee_mechanism", ""),
            item.get("sync_type", ""),
            item.get("trigger", ""),
            item.get("status_reason", ""),
        ]
    )
    if any(term in text for term in LANDING_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS):
        return "implementation_support"
    if any(term in text for term in LANDING_REPORT_HUMAN_GATE_POLICY_TERMS):
        return "policy_clarification"
    if any(term in text for term in LANDING_REPORT_HUMAN_GATE_DECISION_TERMS):
        return "decision_record_required"
    return "policy_clarification"


def landing_report_human_gate_decision_flow(item):
    text = " | ".join(
        [
            item.get("content", ""),
            item.get("guarantee_mechanism", ""),
            item.get("sync_type", ""),
            item.get("trigger", ""),
            item.get("status_reason", ""),
        ]
    )
    if any(term in text for term in LANDING_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS):
        return "current_record_required"
    if any(term in text for term in LANDING_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS):
        return "future_trigger_record"
    return "rule_condition_only"


def landing_report_human_gate_policy_flow(item):
    text = " | ".join(
        [
            item.get("content", ""),
            item.get("guarantee_mechanism", ""),
            item.get("sync_type", ""),
            item.get("trigger", ""),
            item.get("status_reason", ""),
        ]
    )
    if any(term in text for term in LANDING_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS):
        return "workflow_design_discussion"
    return "future_evaluation"


def landing_report_human_gate_support_flow(item):
    return "web_human_facing_support"


def landing_report_human_gate_diagnostic_flow(item):
    return "coverage_degraded"


def landing_report_runtime_projection_subcategory(item):
    if "capability" in item:
        return "projection_coverage_diagnostic"
    text = " | ".join(
        [
            item.get("content", ""),
            item.get("guarantee_mechanism", ""),
            item.get("sync_type", ""),
            item.get("trigger", ""),
            item.get("status_reason", ""),
        ]
    )
    if any(term in text for term in LANDING_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS):
        return "third_party_skill_projection"
    if any(term in text for term in LANDING_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS):
        return "platform_capability_sync"
    return "lifecycle_trigger_sync"


def _classify_runtime_projection_remediation(item):
    text = " ".join([
        str(item.get("content", "")),
        str(item.get("title", "")),
        str(item.get("id", "")),
    ])
    for remediation_type, terms in RUNTIME_PROJECTION_REMEDIATION_TERMS.items():
        if any(term in text for term in terms):
            return remediation_type
    return "doc_crossref_check"


def landing_report_build_gap_categories(requirements, capability_gaps):
    categories = {}
    for item in list(requirements) + list(capability_gaps):
        if not landing_report_is_gap(item):
            continue
        owner_area = item.get("owner_area") or "unknown"
        if owner_area not in categories:
            categories[owner_area] = {
                "owner_area": owner_area,
                "label": LANDING_REPORT_AREA_LABELS.get(owner_area, owner_area),
                "total": 0,
                "by_status": {},
                "by_suggested_writeback": {},
                "requirement_count": 0,
                "capability_gap_count": 0,
                "examples": [],
            }
            if owner_area == "human_gate":
                categories[owner_area]["subcategories"] = {}
            if owner_area == "runtime_projection":
                categories[owner_area]["subcategories"] = {}
        category = categories[owner_area]
        status = item.get("status") or "unknown"
        suggested_writeback = item.get("suggested_writeback") or "manual_review"
        category["total"] += 1
        category["by_status"][status] = category["by_status"].get(status, 0) + 1
        category["by_suggested_writeback"][suggested_writeback] = category["by_suggested_writeback"].get(suggested_writeback, 0) + 1
        if "capability" in item:
            category["capability_gap_count"] += 1
            title = item.get("capability", "")
            source = "capability_gaps"
        else:
            category["requirement_count"] += 1
            title = item.get("content", "")
            source = f"{item.get('source')}:{item.get('line')}"
        example = {
            "source": source,
            "status": status,
            "title": landing_report_shorten(title, 120),
            "suggested_writeback": suggested_writeback,
        }
        if len(category["examples"]) < 3:
            category["examples"].append(example)
        if owner_area == "human_gate":
            subcategory_key = landing_report_human_gate_subcategory(item)
            subcategories = category["subcategories"]
            if subcategory_key not in subcategories:
                subcategories[subcategory_key] = {
                    "id": subcategory_key,
                    "label": LANDING_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS.get(subcategory_key, subcategory_key),
                    "total": 0,
                    "by_status": {},
                    "examples": [],
                }
                if subcategory_key == "decision_record_required":
                    subcategories[subcategory_key]["decision_flows"] = {}
                if subcategory_key == "policy_clarification":
                    subcategories[subcategory_key]["policy_flows"] = {}
                if subcategory_key == "implementation_support":
                    subcategories[subcategory_key]["support_flows"] = {}
                if subcategory_key == "diagnostic_coverage":
                    subcategories[subcategory_key]["diagnostic_flows"] = {}
            subcategory = subcategories[subcategory_key]
            subcategory["total"] += 1
            subcategory["by_status"][status] = subcategory["by_status"].get(status, 0) + 1
            if len(subcategory["examples"]) < 3:
                subcategory["examples"].append(example)
            if subcategory_key == "decision_record_required":
                flow_key = landing_report_human_gate_decision_flow(item)
                decision_flows = subcategory["decision_flows"]
                if flow_key not in decision_flows:
                    decision_flows[flow_key] = {
                        "id": flow_key,
                        "label": LANDING_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS.get(flow_key, flow_key),
                        "total": 0,
                        "by_status": {},
                        "examples": [],
                    }
                flow = decision_flows[flow_key]
                flow["total"] += 1
                flow["by_status"][status] = flow["by_status"].get(status, 0) + 1
                if len(flow["examples"]) < 3:
                    flow["examples"].append(example)
            if subcategory_key == "policy_clarification":
                flow_key = landing_report_human_gate_policy_flow(item)
                policy_flows = subcategory["policy_flows"]
                if flow_key not in policy_flows:
                    policy_flows[flow_key] = {
                        "id": flow_key,
                        "label": LANDING_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS.get(flow_key, flow_key),
                        "total": 0,
                        "by_status": {},
                        "examples": [],
                    }
                flow = policy_flows[flow_key]
                flow["total"] += 1
                flow["by_status"][status] = flow["by_status"].get(status, 0) + 1
                if len(flow["examples"]) < 3:
                    flow["examples"].append(example)
            if subcategory_key == "implementation_support":
                flow_key = landing_report_human_gate_support_flow(item)
                support_flows = subcategory["support_flows"]
                if flow_key not in support_flows:
                    support_flows[flow_key] = {
                        "id": flow_key,
                        "label": LANDING_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS.get(flow_key, flow_key),
                        "total": 0,
                        "by_status": {},
                        "examples": [],
                    }
                flow = support_flows[flow_key]
                flow["total"] += 1
                flow["by_status"][status] = flow["by_status"].get(status, 0) + 1
                if len(flow["examples"]) < 3:
                    flow["examples"].append(example)
            if subcategory_key == "diagnostic_coverage":
                flow_key = landing_report_human_gate_diagnostic_flow(item)
                diagnostic_flows = subcategory["diagnostic_flows"]
                if flow_key not in diagnostic_flows:
                    diagnostic_flows[flow_key] = {
                        "id": flow_key,
                        "label": LANDING_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS.get(flow_key, flow_key),
                        "total": 0,
                        "by_status": {},
                        "examples": [],
                    }
                flow = diagnostic_flows[flow_key]
                flow["total"] += 1
                flow["by_status"][status] = flow["by_status"].get(status, 0) + 1
                if len(flow["examples"]) < 3:
                    flow["examples"].append(example)
        if owner_area == "runtime_projection":
            subcategory_key = landing_report_runtime_projection_subcategory(item)
            subcategories = category["subcategories"]
            if subcategory_key not in subcategories:
                subcategories[subcategory_key] = {
                    "id": subcategory_key,
                    "label": LANDING_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS.get(subcategory_key, subcategory_key),
                    "total": 0,
                    "by_status": {},
                    "examples": [],
                }
            subcategory = subcategories[subcategory_key]
            subcategory["total"] += 1
            subcategory["by_status"][status] = subcategory["by_status"].get(status, 0) + 1
            if len(subcategory["examples"]) < 3:
                subcategory["examples"].append(example)
    for category in categories.values():
        category["by_status"] = dict(sorted(category["by_status"].items(), key=lambda item: item[0]))
        category["by_suggested_writeback"] = dict(
            sorted(category["by_suggested_writeback"].items(), key=lambda item: item[0])
        )
        if category.get("subcategories"):
            for subcategory in category["subcategories"].values():
                subcategory["by_status"] = dict(sorted(subcategory["by_status"].items(), key=lambda item: item[0]))
                if subcategory.get("decision_flows"):
                    for flow in subcategory["decision_flows"].values():
                        flow["by_status"] = dict(sorted(flow["by_status"].items(), key=lambda item: item[0]))
                    subcategory["decision_flows"] = dict(sorted(subcategory["decision_flows"].items(), key=lambda item: item[0]))
                if subcategory.get("policy_flows"):
                    for flow in subcategory["policy_flows"].values():
                        flow["by_status"] = dict(sorted(flow["by_status"].items(), key=lambda item: item[0]))
                    subcategory["policy_flows"] = dict(sorted(subcategory["policy_flows"].items(), key=lambda item: item[0]))
                if subcategory.get("support_flows"):
                    for flow in subcategory["support_flows"].values():
                        flow["by_status"] = dict(sorted(flow["by_status"].items(), key=lambda item: item[0]))
                    subcategory["support_flows"] = dict(sorted(subcategory["support_flows"].items(), key=lambda item: item[0]))
                if subcategory.get("diagnostic_flows"):
                    for flow in subcategory["diagnostic_flows"].values():
                        flow["by_status"] = dict(sorted(flow["by_status"].items(), key=lambda item: item[0]))
                    subcategory["diagnostic_flows"] = dict(sorted(subcategory["diagnostic_flows"].items(), key=lambda item: item[0]))
            category["subcategories"] = dict(sorted(category["subcategories"].items(), key=lambda item: item[0]))
    return dict(sorted(categories.items(), key=lambda item: item[0]))


def landing_report_document_text(paths):
    parts = []
    for path in paths:
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def landing_report_terms_present(text, terms):
    return all(term in text for term in terms)


def landing_report_build_capability_gaps(formal_files, runtime_projection_report=None, human_gate_report=None):
    text = landing_report_document_text(formal_files)
    gaps = []

    for check in LANDING_REPORT_CAPABILITY_CHECKS:
        terms_present = landing_report_terms_present(text, check["required_terms"])
        status = check["status"] if terms_present else "open"
        reason = check["degraded_reason"] if terms_present else check["missing_reason"]
        evidence = "matched formal spec terms" if terms_present else "required terms missing from formal specs"
        if check["id"] == "runtime_projection_drift_check" and runtime_projection_report is not None:
            runtime_status = runtime_projection_report["summary"]["status"]
            runtime_issue_count = runtime_projection_report["metadata"]["issue_count"]
            runtime_file_count = runtime_projection_report["metadata"]["checked_file_count"]
            evidence = f"runtime-projection checked {runtime_file_count} project-local files, issues: {runtime_issue_count}, status: {runtime_status}"
            if runtime_status == "open":
                status = "open"
                reason = "runtime-projection 检查发现 open 漂移问题，landing-report 已接入该诊断"
            elif runtime_status == "degraded":
                status = "degraded"
                reason = "runtime-projection 检查发现 degraded 漂移风险，landing-report 已接入该诊断"
            elif terms_present:
                status = "degraded"
                reason = "runtime-projection 检查当前未发现项目内问题，但仍是项目局部启发式，尚不能证明所有运行投影完整覆盖"
        if check["id"] == "human_gate_evidence_consumption" and human_gate_report is not None:
            gate_status = human_gate_report["summary"]["status"]
            gate_issue_count = human_gate_report["metadata"]["issue_count"]
            gate_record_count = human_gate_report["metadata"]["record_count"]
            gate_file_count = human_gate_report["metadata"]["checked_file_count"]
            evidence = f"human-gate checked {gate_file_count} project-local files, records: {gate_record_count}, issues: {gate_issue_count}, status: {gate_status}"
            if gate_status == "open":
                status = "open"
                reason = "human-gate 检查发现 open 证据结构问题，landing-report 已接入该诊断"
            elif terms_present:
                status = "degraded"
                reason = "human-gate 检查已接入，但仍是项目局部结构检查，尚不能证明所有 Human Gate 触发与 42 现场消费均已覆盖"
        gaps.append(
            {
                "id": check["id"],
                "capability": check["capability"],
                "status": status,
                "status_reason": reason,
                "owner_area": check["owner_area"],
                "suggested_writeback": check["suggested_writeback"],
                "evidence": evidence,
            }
        )

    return gaps


def landing_report_build(paths=None):
    check_paths = paths if paths else landing_default_check_paths()
    markdown_files = iter_markdown_files(check_paths)
    formal_files = [path for path in markdown_files if landing_is_formal_spec(path)]
    requirements = []
    for path in formal_files:
        requirements.extend(landing_extract_requirements_file(path))
    runtime_projection_report = runtime_projection_report_build()
    human_gate_report = human_gate_report_build()
    capability_gaps = landing_report_build_capability_gaps(formal_files, runtime_projection_report, human_gate_report)

    for requirement in requirements:
        status, reason = landing_report_infer_status(requirement)
        owner_area = LANDING_REPORT_OWNER_AREAS.get(requirement["requirement_type"], "unknown")
        requirement["status"] = status
        requirement["status_reason"] = reason
        requirement["owner_area"] = owner_area
        requirement["suggested_writeback"] = LANDING_REPORT_WRITEBACK_AREAS.get(owner_area, "manual_review")

    source_files = sorted({requirement["source"] for requirement in requirements})
    gap_categories = landing_report_build_gap_categories(requirements, capability_gaps)
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
            "runtime_projection_checked_file_count": runtime_projection_report["metadata"]["checked_file_count"],
            "runtime_projection_issue_count": runtime_projection_report["metadata"]["issue_count"],
            "human_gate_checked_file_count": human_gate_report["metadata"]["checked_file_count"],
            "human_gate_record_count": human_gate_report["metadata"]["record_count"],
            "human_gate_issue_count": human_gate_report["metadata"]["issue_count"],
        },
        "summary": {
            "by_status": landing_report_count_by(requirements, "status"),
            "by_capability_status": landing_report_count_by(capability_gaps, "status"),
            "gap_total": sum(category["total"] for category in gap_categories.values()),
            "gap_by_owner_area": {area: category["total"] for area, category in gap_categories.items()},
            "runtime_projection_status": runtime_projection_report["summary"]["status"],
            "runtime_projection_by_status": runtime_projection_report["summary"]["by_status"],
            "human_gate_status": human_gate_report["summary"]["status"],
            "human_gate_by_status": human_gate_report["summary"]["by_status"],
            "by_type": landing_report_count_by(requirements, "requirement_type"),
            "by_sync_type": landing_report_count_by(requirements, "sync_type"),
            "by_owner_area": landing_report_count_by(requirements, "owner_area"),
        },
        "requirements": requirements,
        "capability_gaps": capability_gaps,
        "gap_categories": gap_categories,
        "runtime_projection": runtime_projection_report,
        "human_gate": human_gate_report,
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
    lines.append(f"- 运行投影检查文件数: {metadata['runtime_projection_checked_file_count']}")
    lines.append(f"- 运行投影问题数: {metadata['runtime_projection_issue_count']}")
    lines.append(f"- Human Gate 检查文件数: {metadata['human_gate_checked_file_count']}")
    lines.append(f"- Human Gate 记录数: {metadata['human_gate_record_count']}")
    lines.append(f"- Human Gate 问题数: {metadata['human_gate_issue_count']}")
    lines.append("- 状态判断: Code 派生启发式，非事实源")

    for title, key in [
        ("按状态", "by_status"),
        ("按落地要求类型", "by_type"),
        ("按同步类型", "by_sync_type"),
        ("按承接区域", "by_owner_area"),
        ("运行投影问题状态", "runtime_projection_by_status"),
        ("Human Gate 问题状态", "human_gate_by_status"),
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

    lines.append("")
    lines.append("能力缺口:")
    capability_gaps = report.get("capability_gaps", [])
    if not capability_gaps:
        lines.append("- 无")
    else:
        for item in capability_gaps:
            lines.append(
                f"- [{item['status']}/{item['owner_area']}] {item['capability']} -> "
                f"{item['status_reason']}; evidence: {item['evidence']}; suggested_writeback: {item['suggested_writeback']}"
            )

    lines.append("")
    lines.append("缺口分类:")
    gap_categories = report.get("gap_categories", {})
    if not gap_categories:
        lines.append("- 无")
    else:
        for category in gap_categories.values():
            lines.append(
                f"- {category['label']} ({category['owner_area']}): "
                f"total={category['total']}; requirements={category['requirement_count']}; "
                f"capabilities={category['capability_gap_count']}; status={category['by_status']}"
            )
            for example in category.get("examples", []):
                lines.append(
                    f"  - [{example['status']}] {example['title']} -> {example['suggested_writeback']}"
                )
            for subcategory in category.get("subcategories", {}).values():
                lines.append(
                    f"  - {subcategory['label']} ({subcategory['id']}): "
                    f"total={subcategory['total']}; status={subcategory['by_status']}"
                )
                for example in subcategory.get("examples", []):
                    lines.append(
                        f"    - [{example['status']}] {example['title']} -> {example['suggested_writeback']}"
                    )
                for flow in subcategory.get("decision_flows", {}).values():
                    lines.append(
                        f"    - {flow['label']} ({flow['id']}): "
                        f"total={flow['total']}; status={flow['by_status']}"
                    )
                    for example in flow.get("examples", []):
                        lines.append(
                            f"      - [{example['status']}] {example['title']} -> {example['suggested_writeback']}"
                        )
                for flow in subcategory.get("policy_flows", {}).values():
                    lines.append(
                        f"    - {flow['label']} ({flow['id']}): "
                        f"total={flow['total']}; status={flow['by_status']}"
                    )
                    for example in flow.get("examples", []):
                        lines.append(
                            f"      - [{example['status']}] {example['title']} -> {example['suggested_writeback']}"
                        )
                for flow in subcategory.get("support_flows", {}).values():
                    lines.append(
                        f"    - {flow['label']} ({flow['id']}): "
                        f"total={flow['total']}; status={flow['by_status']}"
                    )
                    for example in flow.get("examples", []):
                        lines.append(
                            f"      - [{example['status']}] {example['title']} -> {example['suggested_writeback']}"
                        )
                for flow in subcategory.get("diagnostic_flows", {}).values():
                    lines.append(
                        f"    - {flow['label']} ({flow['id']}): "
                        f"total={flow['total']}; status={flow['by_status']}"
                    )
                    for example in flow.get("examples", []):
                        lines.append(
                            f"      - [{example['status']}] {example['title']} -> {example['suggested_writeback']}"
                        )
            for subcategory in category.get("subcategories", {}).values():
                if category["owner_area"] != "runtime_projection":
                    continue
                lines.append(
                    f"  - {subcategory['label']} ({subcategory['id']}): "
                    f"total={subcategory['total']}; status={subcategory['by_status']}"
                )
                for example in subcategory.get("examples", []):
                    lines.append(
                        f"    - [{example['status']}] {example['title']} -> {example['suggested_writeback']}"
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
# human-gate — Human Gate 轻量人类决策记录结构检查
# ══════════════════════════════════════════════════════════════════════

HUMAN_GATE_HEADER_RE = re.compile(r"^Human Gate\s*记录[:：]\s*$", re.IGNORECASE)
HUMAN_GATE_FIELD_RE = re.compile(r"^\s*[-*]\s*(?P<label>[^:：]+?)\s*[:：]\s*(?P<value>.*)$")
HUMAN_GATE_FILE_SUFFIXES = {".md", ".yaml", ".yml"}
HUMAN_GATE_REQUIRED_FIELDS = [
    ("时间", ["时间", "确认人/时间", "确认人和时间", "确认来源和时间", "确认人及时间", "time", "date", "confirmed_at"]),
    ("决策", ["决策", "Human 决策", "Human 选择", "确认结果", "用户选择", "decision", "result"]),
    ("范围", ["范围", "影响范围", "确认事项", "确认对象", "确认对象或确认事项", "scope"]),
    ("约束", ["约束", "确认依据", "依据", "确认上下文", "后续动作", "后续执行动作", "确认后的执行动作", "验证方式", "验证结果", "验证方式或结果", "回写位置", "残留风险", "残留风险或后续 Task", "constraints"]),
]
HUMAN_GATE_YAML_KEYS = {"human_gate", "human_gates", "human_gate_records"}


def human_gate_default_check_paths():
    paths = []
    for path in [DOCS_DIR, PROJECT_ROOT / "ldvh-base"]:
        if path.exists():
            paths.append(str(path))
    return paths


def human_gate_iter_files(paths):
    files = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix in HUMAN_GATE_FILE_SUFFIXES:
            files.append(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix in HUMAN_GATE_FILE_SUFFIXES:
                    files.append(child)
    return sorted(set(files))


def human_gate_normalize_label(label):
    return str(label).strip().strip("*").strip("`").strip()


def human_gate_alias_map():
    aliases = {}
    for canonical, labels in HUMAN_GATE_REQUIRED_FIELDS:
        for label in labels:
            aliases[human_gate_normalize_label(label)] = canonical
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

        text = "\n".join(item for item in [fields.get(canonical, ""), value, *continuation] if item).strip()
        fields[canonical] = text
        field_lines.setdefault(canonical, line_number)

    return fields, field_lines


def human_gate_check_record_fields(path, line, fields, field_lines):
    issues = []
    if not fields:
        issues.append(Issue(path, line, "Human Gate 记录缺少可识别字段", code="HUMAN_GATE_RECORD_EMPTY"))

    for canonical, _ in HUMAN_GATE_REQUIRED_FIELDS:
        if canonical not in fields:
            issues.append(Issue(path, line, f"Human Gate 记录缺少字段: {canonical}", code="HUMAN_GATE_FIELD_MISSING"))
        elif not str(fields[canonical]).strip():
            issues.append(Issue(path, field_lines.get(canonical, line), f"Human Gate 记录字段为空: {canonical}", code="HUMAN_GATE_FIELD_EMPTY"))
    return issues


def human_gate_check_markdown_file(path):
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
        issues.extend(human_gate_check_record_fields(path, index + 1, fields, field_lines))

    return issues


def human_gate_yaml_records(data):
    records = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in HUMAN_GATE_YAML_KEYS:
                if isinstance(value, list):
                    records.extend(item for item in value if isinstance(item, dict))
                elif isinstance(value, dict):
                    records.append(value)
            elif isinstance(value, (dict, list)):
                records.extend(human_gate_yaml_records(value))
    elif isinstance(data, list):
        for item in data:
            records.extend(human_gate_yaml_records(item))
    return records


def human_gate_yaml_line_map(text):
    aliases = human_gate_alias_map()
    lines = {}
    for index, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^\s*([A-Za-z_\-/\u4e00-\u9fff ]+)\s*:", line)
        if not match:
            continue
        canonical = aliases.get(human_gate_normalize_label(match.group(1)))
        if canonical and canonical not in lines:
            lines[canonical] = index
    return lines


def human_gate_yaml_record_fields(record):
    aliases = human_gate_alias_map()
    fields = {}
    for key, value in record.items():
        canonical = aliases.get(human_gate_normalize_label(key))
        if not canonical:
            continue
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False)
        elif value is None:
            text = ""
        else:
            text = str(value).strip()
        fields[canonical] = "\n".join(item for item in [fields.get(canonical, ""), text] if item).strip()
    return fields


def human_gate_check_yaml_file(path):
    text = path.read_text(encoding="utf-8")
    if not any(key in text for key in HUMAN_GATE_YAML_KEYS):
        return []
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [Issue(path, 1, f"Human Gate YAML 解析失败: {exc}", code="HUMAN_GATE_YAML_INVALID")]
    records = human_gate_yaml_records(data)
    line_map = human_gate_yaml_line_map(text)
    issues = []
    for record in records:
        fields = human_gate_yaml_record_fields(record)
        issues.extend(human_gate_check_record_fields(path, 1, fields, line_map))
    return issues


def human_gate_check_file(path):
    if path.suffix == ".md":
        return human_gate_check_markdown_file(path)
    if path.suffix in {".yaml", ".yml"}:
        return human_gate_check_yaml_file(path)
    return []


def human_gate_check_paths(paths):
    issues = []
    for path in human_gate_iter_files(paths):
        issues.extend(human_gate_check_file(path))
    return issues


def human_gate_count_markdown_records_file(path):
    count = 0
    lines = path.read_text(encoding="utf-8").splitlines()
    in_code_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if HUMAN_GATE_HEADER_RE.match(stripped):
            count += 1
    return count


def human_gate_count_yaml_records_file(path):
    text = path.read_text(encoding="utf-8")
    if not any(key in text for key in HUMAN_GATE_YAML_KEYS):
        return 0
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return 0
    return len(human_gate_yaml_records(data))


def human_gate_count_records_file(path):
    if path.suffix == ".md":
        return human_gate_count_markdown_records_file(path)
    if path.suffix in {".yaml", ".yml"}:
        return human_gate_count_yaml_records_file(path)
    return 0


def human_gate_report_build(paths=None):
    check_paths = paths if paths is not None else human_gate_default_check_paths()
    files = [path for path in human_gate_iter_files(check_paths) if runtime_projection_is_project_local(path)]
    issues = []
    record_count = 0
    for file_path in files:
        record_count += human_gate_count_records_file(file_path)
        issues.extend(human_gate_check_file(file_path))
    issue_items = []
    for issue in issues:
        issue_items.append(
            {
                "source": landing_relative_path(issue.path),
                "line": issue.line,
                "code": issue.code,
                "status": "open",
                "message": issue.message,
            }
        )
    status = "closed"
    if issue_items:
        status = "open"
    elif record_count == 0:
        status = "degraded"
    return {
        "metadata": {
            "tool": "tools/specs_validate.py",
            "report": "human-gate",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "checked_file_count": len(files),
            "record_count": record_count,
            "issue_count": len(issue_items),
            "scope": "project-local Markdown/YAML facts only",
        },
        "summary": {
            "status": status,
            "by_status": landing_report_count_by(issue_items, "status"),
            "by_code": landing_report_count_by(issue_items, "code"),
        },
        "issues": issue_items,
    }


def human_gate_report_format_text(report):
    lines = ["Human Gate 证据结构检查"]
    metadata = report["metadata"]
    lines.append(f"- 检查文件数: {metadata['checked_file_count']}")
    lines.append(f"- 记录数: {metadata['record_count']}")
    lines.append(f"- 问题数: {metadata['issue_count']}")
    lines.append(f"- 状态: {report['summary']['status']}")
    lines.append("- 状态判断: Code 派生启发式，非事实源")
    lines.append("")
    lines.append("问题:")
    if not report["issues"]:
        lines.append("- 无")
    else:
        for item in report["issues"]:
            lines.append(f"- {item['source']}:{item['line']} [{item['status']}/{item['code']}] {item['message']}")
    return "\n".join(lines)


def human_gate_report_main(paths=None, output_format="text"):
    report = human_gate_report_build(paths if paths else None)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(human_gate_report_format_text(report))
    return 0 if report["summary"]["status"] == "closed" else 1


def human_gate_main(paths):
    check_paths = paths if paths else human_gate_default_check_paths()
    issues = human_gate_check_paths(check_paths)
    if issues:
        print(f"Human Gate 轻量人类决策记录结构检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("Human Gate 最小证据结构检查通过。")
    return 0


# ══════════════════════════════════════════════════════════════════════
# governed-projects — 工作区根目录管辖项目配置检查
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
                f"工作区根目录缺少管辖项目配置: {GOVERNED_PROJECTS_FILENAME}",
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


LDVH_LANDING_CHECK_STATUS_ORDER = {"closed": 0, "degraded": 1, "open": 2, "blocked": 3}


def ldvh_landing_check_status(items):
    status = "closed"
    for item in items:
        item_status = item.get("status", "closed")
        if LDVH_LANDING_CHECK_STATUS_ORDER.get(item_status, 0) > LDVH_LANDING_CHECK_STATUS_ORDER.get(status, 0):
            status = item_status
    return status


def ldvh_landing_check_fact_files():
    facts_dir = PROJECT_ROOT / "ldvh-base"
    if not facts_dir.exists():
        return []
    return sorted(facts_dir.rglob("*.yaml"))


def ldvh_landing_check_fact_validate():
    fact_files = ldvh_landing_check_fact_files()
    if not fact_files:
        return {
            "status": "degraded",
            "issue_count": 0,
            "error_count": 0,
            "warning_count": 0,
            "checked_file_count": 0,
            "evidence": "no ldvh-base YAML fact files found in project scope",
            "issues": [],
        }
    command = [
        sys.executable,
        str(Path(__file__).resolve().parent / "fact_validate.py"),
        *[str(path) for path in fact_files],
        "--format",
        "json",
    ]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    try:
        payload = json.loads(completed.stdout)
        summary = payload.get("summary", {})
        issues = payload.get("issues", [])
        errors = int(summary.get("errors", 0))
        warnings = int(summary.get("warnings", 0))
        status = "closed"
        if errors or completed.returncode in {1, 2}:
            status = "open"
        elif warnings:
            status = "degraded"
        return {
            "status": status,
            "issue_count": len(issues),
            "error_count": errors,
            "warning_count": warnings,
            "checked_file_count": int(summary.get("files", len(fact_files))),
            "evidence": f"fact_validate checked {summary.get('files', len(fact_files))} fact files, errors: {errors}, warnings: {warnings}",
            "issues": issues,
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        return {
            "status": "open",
            "issue_count": 1,
            "error_count": 1,
            "warning_count": 0,
            "checked_file_count": len(fact_files),
            "evidence": "fact_validate output could not be parsed as JSON",
            "issues": [
                {
                    "level": "error",
                    "code": "FACT_VALIDATE_OUTPUT_INVALID",
                    "message": completed.stderr.strip() or completed.stdout.strip() or "fact_validate failed without parseable output",
                    "path": str(PROJECT_ROOT / "ldvh-base"),
                }
            ],
        }


def ldvh_landing_check_spec_validate():
    doc_issues = doc_check_paths([str(SPECS_DIR)])
    refs_issues = refs_check_paths(refs_default_check_paths())
    landing_issues = landing_check_paths(landing_default_check_paths())
    issues = doc_issues + refs_issues + landing_issues
    return {
        "status": "open" if issues else "closed",
        "issue_count": len(issues),
        "doc_issue_count": len(doc_issues),
        "refs_issue_count": len(refs_issues),
        "landing_issue_count": len(landing_issues),
        "checked_file_count": len(iter_markdown_files([str(SPECS_DIR)])),
        "evidence": f"spec checks found doc={len(doc_issues)}, refs={len(refs_issues)}, landing={len(landing_issues)} issues",
        "issues": [
            {
                "source": landing_relative_path(issue.path),
                "line": issue.line,
                "code": issue.code,
                "message": issue.message,
            }
            for issue in issues
        ],
    }


BOOTSTRAP_BASELINE_DEFINITIONS = [
    ("specs_integrity", "specs 完整性检查"),
    ("asset_directories", "资产目录检查"),
    ("governed_projects_config", "管辖项目配置检查"),
    ("work_model_workflow_indexes", "工作模型和工作流程索引检查"),
    ("environment_matrix", "环境承接矩阵检查"),
    ("runtime_projection_entry", "运行投影入口检查"),
    ("code_self_check", "Code 自检"),
    ("web_asset", "Web 资产检查"),
    ("report_structure", "42 报告结构输出"),
    ("gap_classification_routing", "缺口分类与分流"),
]


def ldvh_bootstrap_issue(code, message, path=None, category="Code"):
    return {
        "code": code,
        "message": message,
        "path": landing_relative_path(path) if path else None,
        "category": category,
    }


def ldvh_bootstrap_baseline_item(item_id, label, status, evidence, categories=None, issues=None):
    issues = issues or []
    return {
        "id": item_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "issue_count": len(issues),
        "gap_categories": sorted(set(categories or [issue.get("category") for issue in issues if issue.get("category")])) or [],
        "issues": issues,
    }


def ldvh_bootstrap_baseline_build(workspace_root, checks, governed_issues, runtime_report, spec_report, remaining_gaps):
    workspace_root = Path(workspace_root)
    items = []

    items.append(ldvh_bootstrap_baseline_item(
        "specs_integrity",
        "specs 完整性检查",
        spec_report["status"],
        spec_report["evidence"],
        ["规范"] if spec_report["status"] != "closed" else [],
        spec_report.get("issues", []),
    ))

    required_assets = [
        (PROJECT_ROOT / "docs" / "specs", "规范资产", "规范"),
        (PROJECT_ROOT / "tools", "Code 能力资产", "Code"),
        (PROJECT_ROOT / "tests", "测试证明", "Code"),
        (PROJECT_ROOT / "web", "Web 能力资产", "Web"),
        (PROJECT_ROOT / "ldvh-base", "工作对象事实源", "事实源"),
        (PROJECT_ROOT / "LDVH-AI-ENTRY.md", "运行投影入口", "环境承接"),
    ]
    asset_issues = [
        ldvh_bootstrap_issue("BOOTSTRAP_ASSET_MISSING", f"缺少{label}: {landing_relative_path(path)}", path, category)
        for path, label, category in required_assets
        if not path.exists()
    ]
    items.append(ldvh_bootstrap_baseline_item(
        "asset_directories",
        "资产目录检查",
        "open" if asset_issues else "closed",
        f"checked {len(required_assets)} required asset paths",
        None,
        asset_issues,
    ))

    items.append(ldvh_bootstrap_baseline_item(
        "governed_projects_config",
        "管辖项目配置检查",
        "open" if governed_issues else "closed",
        f"checked {landing_relative_path(workspace_root / GOVERNED_PROJECTS_FILENAME)}",
        ["事实源"] if governed_issues else [],
        [
            ldvh_bootstrap_issue(issue.code, issue.message, issue.path, "事实源")
            for issue in governed_issues
        ],
    ))

    index_paths = [PROJECT_ROOT / "docs" / "specs" / "20-工作模型集合索引.md", PROJECT_ROOT / "docs" / "specs" / "40-工作流程集合索引.md"]
    index_issues = [
        ldvh_bootstrap_issue("BOOTSTRAP_INDEX_MISSING", f"缺少索引文件: {landing_relative_path(path)}", path, "规范")
        for path in index_paths
        if not path.exists()
    ]
    items.append(ldvh_bootstrap_baseline_item(
        "work_model_workflow_indexes",
        "工作模型和工作流程索引检查",
        "open" if index_issues else "closed",
        "checked 20/40 index files",
        None,
        index_issues,
    ))

    matrix_path = PROJECT_ROOT / "docs" / "specs" / "04.06-平台适配清单规范.md"
    matrix_issues = []
    if not matrix_path.exists():
        matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_ENV_MATRIX_MISSING", "缺少环境承接矩阵规范文件", matrix_path, "环境承接"))
    else:
        matrix_text = matrix_path.read_text(encoding="utf-8")
        for environment in ["Trae Work CN", "Codex App", "Claude Code CLI"]:
            if environment not in matrix_text:
                matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_ENV_MATRIX_ENV_MISSING", f"环境承接矩阵缺少环境: {environment}", matrix_path, "环境承接"))
    items.append(ldvh_bootstrap_baseline_item(
        "environment_matrix",
        "环境承接矩阵检查",
        "open" if matrix_issues else "closed",
        "checked 04.06 for three-environment承接矩阵",
        None,
        matrix_issues,
    ))

    items.append(ldvh_bootstrap_baseline_item(
        "runtime_projection_entry",
        "运行投影入口检查",
        runtime_report["summary"]["status"],
        f"runtime-projection checked {runtime_report['metadata']['checked_file_count']} project-local files",
        ["环境承接"] if runtime_report["summary"]["status"] != "closed" else [],
        runtime_report.get("issues", []),
    ))

    code_paths = [PROJECT_ROOT / "tools" / "specs_validate.py", PROJECT_ROOT / "tests" / "test_specs_validate.py"]
    code_issues = [
        ldvh_bootstrap_issue("BOOTSTRAP_CODE_SELF_CHECK_MISSING", f"缺少 Code 自检关键文件: {landing_relative_path(path)}", path, "Code")
        for path in code_paths
        if not path.exists()
    ]
    items.append(ldvh_bootstrap_baseline_item(
        "code_self_check",
        "Code 自检",
        "open" if code_issues else "closed",
        "checked specs_validate.py and test_specs_validate.py presence",
        None,
        code_issues,
    ))

    web_paths = [PROJECT_ROOT / "web", PROJECT_ROOT / "web" / "api", PROJECT_ROOT / "web" / "src"]
    web_issues = [
        ldvh_bootstrap_issue("BOOTSTRAP_WEB_ASSET_MISSING", f"缺少 Web 资产路径: {landing_relative_path(path)}", path, "Web")
        for path in web_paths
        if not path.exists()
    ]
    items.append(ldvh_bootstrap_baseline_item(
        "web_asset",
        "Web 资产检查",
        "open" if web_issues else "closed",
        "checked Web asset paths without requiring Web runtime",
        None,
        web_issues,
    ))

    required_report_keys = {"metadata", "summary", "checks", "remaining_gaps"}
    present_report_keys = {"metadata", "summary", "checks", "remaining_gaps"}
    report_issues = [] if required_report_keys <= present_report_keys else [ldvh_bootstrap_issue("BOOTSTRAP_REPORT_STRUCTURE_MISSING", "42 报告结构缺少必需字段", category="Code")]
    items.append(ldvh_bootstrap_baseline_item(
        "report_structure",
        "42 报告结构输出",
        "open" if report_issues else "closed",
        "checked ldvh-landing-check report structure contract",
        None,
        report_issues,
    ))

    allowed_categories = {"规范", "Code", "Web", "Task", "事实源", "环境承接", "Human Gate"}
    routing_issues = []
    for gap in remaining_gaps:
        if not gap.get("suggested_writeback"):
            routing_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_GAP_ROUTING_MISSING", f"缺口缺少分流建议: {gap.get('id')}", category="Task"))
    routed_categories = set()
    for item in items:
        routed_categories.update(item.get("gap_categories", []))
    unknown_categories = sorted(routed_categories - allowed_categories)
    for category in unknown_categories:
        routing_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_GAP_CATEGORY_UNKNOWN", f"未知缺口分类: {category}", category="Task"))
    items.append(ldvh_bootstrap_baseline_item(
        "gap_classification_routing",
        "缺口分类与分流",
        "open" if routing_issues else "closed",
        f"checked {len(remaining_gaps)} remaining gaps for routing metadata",
        sorted(routed_categories & allowed_categories),
        routing_issues,
    ))

    return {
        "definitions": [{"id": item_id, "label": label} for item_id, label in BOOTSTRAP_BASELINE_DEFINITIONS],
        "items": items,
        "summary": {
            "status": ldvh_landing_check_status(items),
            "by_status": landing_report_count_by(items, "status"),
            "item_count": len(items),
            "open_item_count": len([item for item in items if item["status"] != "closed"]),
            "gap_categories": sorted({category for item in items for category in item.get("gap_categories", [])}),
        },
    }


def ldvh_landing_check_build(workspace_root=None):
    workspace_root = Path(workspace_root) if workspace_root else PROJECT_ROOT
    governed_issues = governed_projects_check_root(workspace_root)
    landing_report = landing_report_build()
    runtime_report = landing_report["runtime_projection"]
    human_gate_report = landing_report["human_gate"]
    fact_report = ldvh_landing_check_fact_validate()
    spec_report = ldvh_landing_check_spec_validate()
    capability_status = ldvh_landing_check_status(landing_report.get("capability_gaps", []))
    requirement_status = ldvh_landing_check_status(landing_report.get("requirements", []))
    checks = [
        {
            "id": "governed_projects",
            "source_area": "governed-projects",
            "status": "open" if governed_issues else "closed",
            "issue_count": len(governed_issues),
            "evidence": f"governed-projects checked at {landing_relative_path(workspace_root / GOVERNED_PROJECTS_FILENAME)}",
            "suggested_writeback": "governed_projects_config",
            "issues": [
                {"source": landing_relative_path(issue.path), "line": issue.line, "code": issue.code, "message": issue.message}
                for issue in governed_issues
            ],
        },
        {
            "id": "landing_report",
            "source_area": "landing-report",
            "status": ldvh_landing_check_status([{"status": capability_status}, {"status": requirement_status}]),
            "issue_count": len([item for item in landing_report.get("requirements", []) if item.get("status") != "closed"]) + len([item for item in landing_report.get("capability_gaps", []) if item.get("status") != "closed"]),
            "evidence": f"landing-report consumed {landing_report['metadata']['requirement_count']} requirements and {len(landing_report.get('capability_gaps', []))} capability checks",
            "suggested_writeback": "landing_report_followup",
            "issues": [],
        },
        {
            "id": "runtime_projection",
            "source_area": "runtime-projection",
            "status": runtime_report["summary"]["status"],
            "issue_count": runtime_report["metadata"]["issue_count"],
            "evidence": f"runtime-projection checked {runtime_report['metadata']['checked_file_count']} project-local files",
            "suggested_writeback": "runtime_projection_or_env_record",
            "issues": runtime_report.get("issues", []),
        },
        {
            "id": "human_gate",
            "source_area": "human-gate",
            "status": human_gate_report["summary"]["status"],
            "issue_count": human_gate_report["metadata"]["issue_count"],
            "evidence": f"human-gate checked {human_gate_report['metadata']['checked_file_count']} project-local files and {human_gate_report['metadata']['record_count']} records",
            "suggested_writeback": "human_gate_record",
            "issues": human_gate_report.get("issues", []),
        },
        {
            "id": "fact_validate",
            "source_area": "fact/spec",
            "status": fact_report["status"],
            "issue_count": fact_report["issue_count"],
            "evidence": fact_report["evidence"],
            "suggested_writeback": "fact_yaml_fix_or_task",
            "issues": fact_report["issues"],
        },
        {
            "id": "spec_validate",
            "source_area": "fact/spec",
            "status": spec_report["status"],
            "issue_count": spec_report["issue_count"],
            "evidence": spec_report["evidence"],
            "suggested_writeback": "spec_fix_or_task",
            "issues": spec_report["issues"],
        },
    ]
    remaining_gaps = []
    for check in checks:
        if check["status"] == "closed":
            continue
        remaining_gaps.append(
            {
                "id": check["id"],
                "status": check["status"],
                "source_area": check["source_area"],
                "message": check["evidence"],
                "suggested_writeback": check["suggested_writeback"],
            }
        )
    bootstrap_baseline = ldvh_bootstrap_baseline_build(
        workspace_root,
        checks,
        governed_issues,
        runtime_report,
        spec_report,
        remaining_gaps,
    )
    return {
        "metadata": {
            "tool": "tools/specs_validate.py",
            "report": "ldvh-landing-check",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "project_root": str(PROJECT_ROOT),
            "workspace_root": str(workspace_root),
            "scope": "project-local Git facts plus explicit workspace governed-projects config",
            "bootstrap_baseline_source": "docs/specs/42-ldvh-landing-check-LDVH落地与检查.md",
        },
        "summary": {
            "status": ldvh_landing_check_status(checks),
            "by_status": landing_report_count_by(checks, "status"),
            "remaining_gap_count": len(remaining_gaps),
            "bootstrap_baseline_status": bootstrap_baseline["summary"]["status"],
            "bootstrap_baseline_open_item_count": bootstrap_baseline["summary"]["open_item_count"],
        },
        "checks": checks,
        "bootstrap_baseline": bootstrap_baseline,
        "remaining_gaps": remaining_gaps,
    }


def landing_plan_build(workspace_root=None):
    workspace_root = Path(workspace_root) if workspace_root else PROJECT_ROOT
    landing_report = landing_report_build()
    ldvh_check = ldvh_landing_check_build(workspace_root)
    gap_categories = landing_report.get("gap_categories", {})

    facts_read = []
    for req in landing_report.get("requirements", []):
        src = req.get("source", "")
        if src and src not in [f["path"] for f in facts_read]:
            facts_read.append({"path": src, "type": "spec"})
    for cap in landing_report.get("capability_gaps", []):
        src = cap.get("source", "capability_gaps")
        if src and src not in [f["path"] for f in facts_read]:
            facts_read.append({"path": src, "type": "capability"})

    capabilities = []
    for check in ldvh_check.get("checks", []):
        capabilities.append({
            "id": check["id"],
            "source_area": check["source_area"],
            "status": check["status"],
            "issue_count": check["issue_count"],
            "evidence": check["evidence"],
        })

    proposed_actions = []
    for area, category in gap_categories.items():
        action = {
            "owner_area": area,
            "label": category.get("label", area),
            "gap_count": category["total"],
            "by_status": category.get("by_status", {}),
            "suggested_writebacks": list(category.get("by_suggested_writeback", {}).keys()),
        }
        if area == "human_gate" and "subcategories" in category:
            action["subcategories"] = {
                k: {"label": v["label"], "total": v["total"]}
                for k, v in category["subcategories"].items()
            }
        if area == "runtime_projection" and "subcategories" in category:
            action["subcategories"] = {
                k: {"label": v["label"], "total": v["total"]}
                for k, v in category["subcategories"].items()
            }
            # remediation aggregation for runtime projection gaps
            rp_items = [
                r for r in landing_report.get("requirements", [])
                if r.get("owner_area") == "runtime_projection" and landing_report_is_gap(r)
            ] + [
                c for c in landing_report.get("capability_gaps", [])
                if c.get("owner_area") == "runtime_projection" and landing_report_is_gap(c)
            ]
            remediation_counts = {}
            for item in rp_items:
                rtype = _classify_runtime_projection_remediation(item)
                remediation_counts[rtype] = remediation_counts.get(rtype, 0) + 1
            action["remediation"] = {
                rtype: {
                    "label": RUNTIME_PROJECTION_REMEDIATION_LABELS.get(rtype, rtype),
                    "total": count,
                }
                for rtype, count in sorted(remediation_counts.items(), key=lambda x: -x[1])
            }
        proposed_actions.append(action)

    writes_required = {
        "required": any(
            cat.get("by_suggested_writeback", {})
            for cat in gap_categories.values()
            if any(k not in ("manual_review", "none") for k in cat.get("by_suggested_writeback", {}))
        ),
        "targets": sorted(set(
            wb
            for cat in gap_categories.values()
            for wb in cat.get("by_suggested_writeback", {})
            if wb not in ("manual_review", "none")
        )),
    }

    human_gate = {
        "total_gaps": gap_categories.get("human_gate", {}).get("total", 0),
        "subcategories": {},
    }
    hg_cat = gap_categories.get("human_gate", {})
    if "subcategories" in hg_cat:
        for sk, sv in hg_cat["subcategories"].items():
            entry = {"label": sv["label"], "total": sv["total"], "by_status": sv.get("by_status", {})}
            if "decision_flows" in sv:
                entry["decision_flows"] = {fk: {"label": fv["label"], "total": fv["total"]} for fk, fv in sv["decision_flows"].items()}
            if "policy_flows" in sv:
                entry["policy_flows"] = {fk: {"label": fv["label"], "total": fv["total"]} for fk, fv in sv["policy_flows"].items()}
            if "support_flows" in sv:
                entry["support_flows"] = {fk: {"label": fv["label"], "total": fv["total"]} for fk, fv in sv["support_flows"].items()}
            if "diagnostic_flows" in sv:
                entry["diagnostic_flows"] = {fk: {"label": fv["label"], "total": fv["total"]} for fk, fv in sv["diagnostic_flows"].items()}
            human_gate["subcategories"][sk] = entry

    validation_plan = {
        "spec_validate_status": ldvh_check.get("checks", [{}])[5].get("status", "unknown") if len(ldvh_check.get("checks", [])) > 5 else "unknown",
        "fact_validate_status": ldvh_check.get("checks", [{}])[4].get("status", "unknown") if len(ldvh_check.get("checks", [])) > 4 else "unknown",
        "runtime_projection_status": ldvh_check.get("checks", [{}])[2].get("status", "unknown") if len(ldvh_check.get("checks", [])) > 2 else "unknown",
        "human_gate_status": ldvh_check.get("checks", [{}])[3].get("status", "unknown") if len(ldvh_check.get("checks", [])) > 3 else "unknown",
    }

    writeback_targets = sorted(set(
        wb
        for cat in gap_categories.values()
        for wb in cat.get("by_suggested_writeback", {})
        if wb not in ("manual_review", "none")
    ))

    return {
        "metadata": {
            "tool": "tools/specs_validate.py",
            "report": "landing-plan",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "read_only": True,
        },
        "scope": {
            "project_root": str(PROJECT_ROOT),
            "workspace_root": str(workspace_root),
            "landing_report_sources": landing_report["metadata"]["source_count"],
            "landing_report_requirements": landing_report["metadata"]["requirement_count"],
        },
        "facts_read": facts_read,
        "capabilities": capabilities,
        "requirements": {
            "total": landing_report["metadata"]["requirement_count"],
            "by_status": landing_report["summary"]["by_status"],
            "gap_total": landing_report["summary"]["gap_total"],
            "gap_by_owner_area": landing_report["summary"]["gap_by_owner_area"],
        },
        "gaps": {
            "by_owner_area": {area: cat["total"] for area, cat in gap_categories.items()},
            "categories": gap_categories,
        },
        "proposed_actions": proposed_actions,
        "writes_required": writes_required,
        "human_gate": human_gate,
        "validation_plan": validation_plan,
        "writeback_targets": writeback_targets,
    }


def landing_plan_format_text(plan):
    lines = []
    lines.append("# Landing Plan (只读)")
    lines.append("")
    scope = plan.get("scope", {})
    lines.append(f"项目: {scope.get('project_root', '')}")
    lines.append(f"规范来源: {scope.get('landing_report_sources', 0)} 篇")
    lines.append(f"规范落地要求: {scope.get('landing_report_requirements', 0)} 条")
    req = plan.get("requirements", {})
    lines.append(f"未关闭缺口: {req.get('gap_total', 0)}")
    lines.append(f"缺口分布: {req.get('gap_by_owner_area', {})}")
    lines.append("")

    lines.append("## 能力状态")
    for cap in plan.get("capabilities", []):
        lines.append(f"- {cap['id']}: {cap['status']} (issues: {cap['issue_count']})")
    lines.append("")

    lines.append("## 建议行动")
    for action in plan.get("proposed_actions", []):
        lines.append(f"- {action['label']} ({action['owner_area']}): {action['gap_count']} 缺口, status={action['by_status']}")
        if "subcategories" in action:
            for sk, sv in action["subcategories"].items():
                lines.append(f"  - {sv['label']} ({sk}): {sv['total']}")
        if "remediation" in action:
            for rk, rv in action["remediation"].items():
                lines.append(f"  - {rv['label']} ({rk}): {rv['total']}")
    lines.append("")

    lines.append("## 写入需求")
    wr = plan.get("writes_required", {})
    lines.append(f"需要写入: {'是' if wr.get('required') else '否'}")
    if wr.get("targets"):
        lines.append(f"写入目标: {', '.join(wr['targets'])}")
    lines.append("")

    lines.append("## Human Gate")
    hg = plan.get("human_gate", {})
    lines.append(f"总缺口: {hg.get('total_gaps', 0)}")
    for sk, sv in hg.get("subcategories", {}).items():
        lines.append(f"- {sv['label']} ({sk}): {sv['total']}, status={sv.get('by_status', {})}")
    lines.append("")

    lines.append("## 验证计划")
    vp = plan.get("validation_plan", {})
    for k, v in vp.items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## 回写目标")
    for target in plan.get("writeback_targets", []):
        lines.append(f"- {target}")

    return "\n".join(lines)


def landing_plan_main(workspace_root=None, output_format="text"):
    plan = landing_plan_build(workspace_root)
    if output_format == "json":
        json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    else:
        print(landing_plan_format_text(plan))
    has_open = plan.get("requirements", {}).get("gap_total", 0) > 0
    return 1 if has_open else 0


def ldvh_landing_check_format_text(report):
    lines = ["LDVH落地与检查派生报告"]
    lines.append(f"- 状态: {report['summary']['status']}")
    lines.append(f"- 剩余缺口数: {report['summary']['remaining_gap_count']}")
    lines.append(f"- Bootstrap Code 基线状态: {report['summary'].get('bootstrap_baseline_status')}")
    lines.append(f"- Bootstrap Code 基线未关闭项: {report['summary'].get('bootstrap_baseline_open_item_count')}")
    lines.append("- 状态判断: Code 派生启发式，非事实源")
    lines.append("")
    lines.append("Bootstrap Code 基线能力:")
    for item in report.get("bootstrap_baseline", {}).get("items", []):
        categories = ",".join(item.get("gap_categories", [])) or "none"
        lines.append(f"- [{item['status']}] {item['id']} ({item['label']}) -> {item['evidence']}; issues: {item['issue_count']}; categories: {categories}")
    lines.append("")
    lines.append("检查项:")
    for item in report["checks"]:
        lines.append(f"- [{item['status']}/{item['source_area']}] {item['id']} -> {item['evidence']}; issues: {item['issue_count']}; suggested_writeback: {item['suggested_writeback']}")
    lines.append("")
    lines.append("剩余缺口:")
    if not report["remaining_gaps"]:
        lines.append("- 无")
    else:
        for item in report["remaining_gaps"]:
            lines.append(f"- [{item['status']}/{item['source_area']}] {item['id']} -> {item['message']}; suggested_writeback: {item['suggested_writeback']}")
    return "\n".join(lines)


def ldvh_landing_check_main(workspace_root=None, output_format="text"):
    report = ldvh_landing_check_build(workspace_root)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(ldvh_landing_check_format_text(report))
    return 0 if report["summary"]["status"] in {"closed", "degraded"} else 1


# ══════════════════════════════════════════════════════════════════════
# web-validate — Web Validate 页面只读数据合同
# ══════════════════════════════════════════════════════════════════════

def web_validate_compact_landing_check(report):
    return {
        "metadata": {
            "generated_at": report.get("metadata", {}).get("generated_at"),
            "status_source": report.get("metadata", {}).get("status_source"),
            "scope": report.get("metadata", {}).get("scope"),
        },
        "summary": {
            "status": report.get("summary", {}).get("status"),
            "remaining_gap_count": report.get("summary", {}).get("remaining_gap_count", 0),
            "by_status": report.get("summary", {}).get("by_status", {}),
        },
        "checks": [
            {
                "id": item.get("id"),
                "status": item.get("status"),
                "issue_count": item.get("issue_count", 0),
                "evidence": item.get("evidence"),
                "suggested_writeback": item.get("suggested_writeback"),
            }
            for item in report.get("checks", [])
        ],
        "remaining_gaps": [
            {
                "id": item.get("id"),
                "status": item.get("status"),
                "message": item.get("message"),
                "suggested_writeback": item.get("suggested_writeback"),
            }
            for item in report.get("remaining_gaps", [])
        ],
    }


def web_validate_compact_landing_report(report):
    return {
        "metadata": {
            "generated_at": report.get("metadata", {}).get("generated_at"),
            "requirement_count": report.get("metadata", {}).get("requirement_count", 0),
            "human_gate_record_count": report.get("metadata", {}).get("human_gate_record_count", 0),
            "runtime_projection_issue_count": report.get("metadata", {}).get("runtime_projection_issue_count", 0),
            "human_gate_issue_count": report.get("metadata", {}).get("human_gate_issue_count", 0),
            "status_source": report.get("metadata", {}).get("status_source"),
        },
        "summary": {
            "by_status": report.get("summary", {}).get("by_status", {}),
            "gap_total": report.get("summary", {}).get("gap_total", 0),
            "runtime_projection_status": report.get("summary", {}).get("runtime_projection_status"),
            "human_gate_status": report.get("summary", {}).get("human_gate_status"),
            "gap_by_owner_area": report.get("summary", {}).get("gap_by_owner_area", {}),
        },
        "capability_gaps": [
            {
                "id": item.get("id"),
                "capability": item.get("capability"),
                "status": item.get("status"),
                "owner_area": item.get("owner_area"),
                "suggested_writeback": item.get("suggested_writeback"),
                "evidence": item.get("evidence"),
            }
            for item in report.get("capability_gaps", [])
        ],
        "gap_categories": [
            {
                "key": key,
                "label": category.get("label"),
                "total": category.get("total", 0),
                "by_status": category.get("by_status", {}),
                "examples": [
                    {
                        "source": example.get("source"),
                        "status": example.get("status"),
                        "title": example.get("title"),
                        "suggested_writeback": example.get("suggested_writeback"),
                    }
                    for example in category.get("examples", [])
                ],
            }
            for key, category in report.get("gap_categories", {}).items()
        ],
    }


def web_validate_compact_human_gate_report(report):
    return {
        "metadata": {
            "generated_at": report.get("metadata", {}).get("generated_at"),
            "checked_file_count": report.get("metadata", {}).get("checked_file_count", 0),
            "record_count": report.get("metadata", {}).get("record_count", 0),
            "issue_count": report.get("metadata", {}).get("issue_count", 0),
            "status_source": report.get("metadata", {}).get("status_source"),
            "scope": report.get("metadata", {}).get("scope"),
        },
        "summary": {
            "status": report.get("summary", {}).get("status"),
        },
        "issues": report.get("issues", []),
    }


def web_validate_build(workspace_root=None):
    fact_report = ldvh_landing_check_fact_validate()
    landing_check = ldvh_landing_check_build(workspace_root)
    landing_report = landing_report_build()
    human_gate_report = landing_report.get("human_gate")
    if human_gate_report is None:
        human_gate_report = human_gate_report_build()

    return {
        "ok": fact_report.get("error_count", 0) == 0,
        "command": "web_validate",
        "action": "validate",
        "target": "ldvh-base",
        "summary": {
            "files": fact_report.get("checked_file_count", 0),
            "errors": fact_report.get("error_count", 0),
            "warnings": fact_report.get("warning_count", 0),
        },
        "issues": fact_report.get("issues", []),
        "reports": {
            "landingCheck": web_validate_compact_landing_check(landing_check),
            "landingReport": web_validate_compact_landing_report(landing_report),
            "humanGateReport": web_validate_compact_human_gate_report(human_gate_report),
        },
    }


def web_validate_format_text(report):
    landing = report.get("reports", {}).get("landingCheck", {})
    landing_report = report.get("reports", {}).get("landingReport", {})
    human_gate = report.get("reports", {}).get("humanGateReport", {})
    lines = ["Web Validate 派生报告"]
    lines.append(f"- fact files: {report.get('summary', {}).get('files', 0)}")
    lines.append(f"- fact errors: {report.get('summary', {}).get('errors', 0)}")
    lines.append(f"- fact warnings: {report.get('summary', {}).get('warnings', 0)}")
    lines.append(f"- 42 status: {landing.get('summary', {}).get('status')}")
    lines.append(f"- landing gaps: {landing_report.get('summary', {}).get('gap_total', 0)}")
    lines.append(f"- Human Gate records: {human_gate.get('metadata', {}).get('record_count', 0)}")
    return "\n".join(lines)


def web_validate_main(workspace_root=None, output_format="text"):
    report = web_validate_build(workspace_root)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(web_validate_format_text(report))
    return 0


# ══════════════════════════════════════════════════════════════════════
# index — 生成索引
# ══════════════════════════════════════════════════════════════════════

INDEX_INPUT_PATTERNS = ("*.md",)
INDEX_NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
INDEX_HEADER_FIELD_RE = re.compile(r"^>\s*([^：:]+)[：:]\s*(.*)\s*$")
INDEX_BACKTICK_MD_RE = re.compile(r"`([^`]+\.md)`")
INDEX_PLAIN_SPECS_MD_RE = re.compile(
    r"(?<![`\w./-])((?:specs/(?:research/|refs/)?|docs/(?:specs|research|refs)/)[^\s`，。；、)）]+\.md)"
)
INDEX_RESEARCH_REF_RE = re.compile(r"(?<![`\w./-])(?:`)?((?:specs/research/|docs/research/)[^`\s，。；、)）]+\.md)(?:`)?")
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
            for match in INDEX_RESEARCH_REF_RE.finditer(line):
                target = match.group(1)
                diagnostics.append(
                    self.diagnostic(rel_path, line_number, "warning", "RESEARCH_REFERENCE_IN_SPEC", f"正式规范不得引用 research 文档路径: {target}")
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
        if raw == "README.md":
            return (self.root / raw).resolve()
        return (self.specs_dir / raw).resolve()

    def required_header_fields(self, doc_kind):
        if doc_kind == "research":
            return ["创建日期", "定位", "调研边界", "执行效力", "编号归属"]
        if doc_kind == "refs":
            return ["创建日期", "来源", "定位"]
        if doc_kind == "subdocument":
            return ["创建日期", "所属主文档", "关系", "适用范围", "上位依据"]
        return ["创建日期", "定位", "适用范围", "上位依据"]

    def infer_doc_kind(self, path, title, header):
        rel = path.relative_to(self.root)
        parts = rel.parts
        if len(parts) >= 2 and parts[0] == "docs" and parts[1] == "research":
            return "research"
        if len(parts) >= 2 and parts[0] == "docs" and parts[1] == "refs":
            return "refs"
        if len(parts) >= 2 and parts[0] == "specs" and parts[1] == "research":
            return "research"
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

    # ldvh-landing-check
    ldvh_landing_check_parser = subparsers.add_parser("ldvh-landing-check", help="生成 42 LDVH落地与检查派生报告。")
    ldvh_landing_check_parser.add_argument("--workspace-root", default=str(PROJECT_ROOT), help="包含 LDVH-GOVERNED-PROJECTS.yaml 的工作区根目录，默认项目根。")
    ldvh_landing_check_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # landing-plan
    landing_plan_parser = subparsers.add_parser("landing-plan", help="生成只读 landing-plan 聚合计划视图。")
    landing_plan_parser.add_argument("--workspace-root", default=str(PROJECT_ROOT), help="工作区根目录，默认项目根。")
    landing_plan_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # web-validate
    web_validate_parser = subparsers.add_parser("web-validate", help="生成 Web Validate 页面只读数据合同。")
    web_validate_parser.add_argument("--workspace-root", default=str(PROJECT_ROOT), help="工作区根目录，默认项目根。")
    web_validate_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # runtime-projection
    runtime_projection_parser = subparsers.add_parser("runtime-projection", help="检查项目内运行投影是否存在漂移风险。")
    runtime_projection_parser.add_argument("paths", nargs="*", default=None, help="要检查的运行投影文件或目录，默认检查项目内授权运行投影。")
    runtime_projection_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # human-gate
    human_gate_parser = subparsers.add_parser("human-gate", help="检查 Markdown 中的 Human Gate 记录是否符合 06 最小证据结构。")
    human_gate_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/ 和 ldvh-base/。")

    # human-gate-report
    human_gate_report_parser = subparsers.add_parser("human-gate-report", help="生成 Human Gate 证据结构派生报告。")
    human_gate_report_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/ 和 ldvh-base/。")
    human_gate_report_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # governed-projects
    governed_projects_parser = subparsers.add_parser("governed-projects", help="检查工作区根目录管辖项目配置。")
    governed_projects_parser.add_argument("--root", default=str(PROJECT_ROOT), help="工作区根目录，默认使用当前工具所在项目。")

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

    if command == "ldvh-landing-check":
        return ldvh_landing_check_main(args.workspace_root, args.format)

    if command == "landing-plan":
        return landing_plan_main(args.workspace_root, args.format)

    if command == "web-validate":
        return web_validate_main(args.workspace_root, args.format)

    if command == "runtime-projection":
        return runtime_projection_main(args.paths, args.format)

    if command == "human-gate":
        return human_gate_main(args.paths)

    if command == "human-gate-report":
        return human_gate_report_main(args.paths, args.format)

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
        # runtime-projection
        if runtime_projection_main(None) != 0:
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
