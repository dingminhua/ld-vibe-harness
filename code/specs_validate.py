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

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from spec_checks import doc_structure as doc_structure_checks
from spec_checks import governed_projects as governed_projects_checks
from spec_checks import human_gate as human_gate_checks
from spec_checks import landing as landing_checks
from spec_checks import landing_report as landing_report_checks
from spec_checks import refs as refs_checks
from spec_checks import runtime_projection as runtime_projection_checks


# ── 通用常量 ──

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = PROJECT_ROOT / "specs"
LEGACY_SPECS_DIR = PROJECT_ROOT / "docs" / "specs"
DOCS_DIR = PROJECT_ROOT / "docs"
FORMAL_SPECS_DIR = SPECS_DIR
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


RUNTIME_PROJECTION_DEFAULT_PATHS = list(runtime_projection_checks.RUNTIME_PROJECTION_DEFAULT_PATHS)


def sync_runtime_projection_config():
    runtime_projection_checks.PROJECT_ROOT = PROJECT_ROOT
    runtime_projection_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    runtime_projection_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def runtime_projection_is_project_local(path):
    sync_runtime_projection_config()
    return runtime_projection_checks.is_project_local(path)


def runtime_projection_report_build(paths=None):
    sync_runtime_projection_config()
    return runtime_projection_checks.report_build(paths)


def runtime_projection_main(paths=None, output_format="text"):
    sync_runtime_projection_config()
    return runtime_projection_checks.main(paths, output_format)


DEPLOYMENT_ENTRIES_AI_ENTRY_PATH = "rules/LDVH-AI-ENTRY.md"
DEPLOYMENT_ENTRIES_SPEC_PATH = "specs/04.02-LDVH能力资产与落地保障规范.md"
DEPLOYMENT_ENTRIES_REQUIRED_ASSETS = {
    "Rules": "rules/LDVH-AI-ENTRY.md",
    "Skill": "skills/ldvh-spec-change-check/SKILL.md",
    "Agent": "agents/ldvh-spec-semantic-review.md",
    "Hook": "hooks/ldvh-lifecycle-check.md",
}
DEPLOYMENT_ENTRIES_FORBIDDEN_TYPES = {"Code", "Web", "CLI", "MCP", "Command", "CI", "文档"}


def deployment_entries_fixed_asset_section(text):
    marker = "## 2. LDVH 能力资产"
    start = text.find(marker)
    if start < 0:
        return ""
    lines = text[start:].splitlines()
    section = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            in_table = True
            section.append(line)
            continue
        if in_table:
            break
        section.append(line)
    return "\n".join(section)


def deployment_entries_check(root=None):
    root = Path(root) if root is not None else PROJECT_ROOT
    spec_path = root / DEPLOYMENT_ENTRIES_SPEC_PATH
    ai_entry_path = root / DEPLOYMENT_ENTRIES_AI_ENTRY_PATH
    issues = []

    if not spec_path.exists():
        issues.append(Issue(spec_path, 1, f"缺少 LDVH 能力资产定义规范: {DEPLOYMENT_ENTRIES_SPEC_PATH}", code="DEPLOYMENT_ENTRIES_SPEC_MISSING"))
        spec_text = ""
    else:
        spec_text = spec_path.read_text(encoding="utf-8")

    for entry_type, expected_path in DEPLOYMENT_ENTRIES_REQUIRED_ASSETS.items():
        if spec_text and entry_type not in spec_text:
            issues.append(Issue(spec_path, 1, f"LDVH 能力资产定义缺少必备资产类型: {entry_type}", code="DEPLOYMENT_ENTRIES_REQUIRED_TYPE_MISSING"))
        if spec_text and expected_path not in spec_text:
            issues.append(Issue(spec_path, 1, f"LDVH 能力资产定义缺少必备资产路径: {expected_path}", code="DEPLOYMENT_ENTRIES_REQUIRED_ASSET_MISMATCH"))
        if not (root / expected_path).exists():
            issues.append(Issue(root / expected_path, 1, f"缺少必备 LDVH 能力资产: {expected_path}", code="DEPLOYMENT_ENTRIES_REQUIRED_ASSET_MISSING"))

    fixed_asset_section = deployment_entries_fixed_asset_section(spec_text)
    for forbidden_type in DEPLOYMENT_ENTRIES_FORBIDDEN_TYPES:
        forbidden_pattern = f"| {forbidden_type} |"
        if fixed_asset_section and forbidden_pattern in fixed_asset_section:
            issues.append(Issue(spec_path, 1, f"不得将支撑能力写成 Rules、Skill、Agent、Hook 同级文本能力资产类型: {forbidden_type}", code="DEPLOYMENT_ENTRIES_FORBIDDEN_TYPE"))

    if not ai_entry_path.exists():
        issues.append(Issue(ai_entry_path, 1, f"缺少 Rules 统一入口: {DEPLOYMENT_ENTRIES_AI_ENTRY_PATH}", code="DEPLOYMENT_ENTRIES_AI_ENTRY_MISSING"))
    else:
        ai_entry_text = ai_entry_path.read_text(encoding="utf-8")
        if DEPLOYMENT_ENTRIES_SPEC_PATH not in ai_entry_text:
            issues.append(Issue(ai_entry_path, 1, f"Rules 统一入口未引用 LDVH 能力资产定义规范: {DEPLOYMENT_ENTRIES_SPEC_PATH}", code="DEPLOYMENT_ENTRIES_AI_ENTRY_REF_MISSING"))

    return issues


def deployment_entries_main(root=None):
    issues = deployment_entries_check(root)
    if issues:
        print(f"LDVH 能力资产检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("LDVH 能力资产检查通过。")
    return 0


CONSISTENCY_WORK_MODEL_REQUIRED_SECTIONS = {
    "1": "对象定位与准入条件",
    "2": "事实源边界",
    "3": "状态机",
    "4": "对象关系",
    "5": "Human Gate",
    "6": "字段契约",
    "7": "事实源回写与证据留存",
    "8": "适配边界",
    "9": "规范落地要求",
    "10": "检查要求",
    "11": "待补齐事项",
}
CONSISTENCY_NEGATIVE_TERMS = ("不得", "不应", "不能", "不可", "不是", "不具备", "不再", "已退回", "候选", "历史", "removed", "取消", "不作为", "待重新设计")
CONSISTENCY_DANGEROUS_TERMS = ("active", "统一流程", "默认流程", "默认保障机制", "可执行入口", "默认对象", "独立工作模型", "当前权威工作流程入口")
CONSISTENCY_RETIRED_REFERENCE_RULES = (
    {
        "aliases": ("42 LDVH 落地与检查", "42 LDVH落地与检查", "42 检查流程", "LDVH落地与检查"),
        "dangerous_terms": ("上位口径", "流程消费", "消费", "应读取", "读取本文", "输入", "默认保障机制", "可执行入口"),
        "code": "RETIRED_WORKFLOW_CONSUMPTION",
        "message": "已退回工作流程疑似仍被作为当前消费入口、输入或上位口径",
    },
    {
        "aliases": ("运行闭环测试机制", "10 定义", "specs/10"),
        "dangerous_terms": ("测试事实源", "测试用例事实源", "10 定义", "正式规范", "前置约束"),
        "code": "RETIRED_TEST_SOURCE_CONSUMPTION",
        "message": "已退回运行闭环测试机制疑似仍被作为当前测试事实源或正式约束",
    },
)
CONSISTENCY_FORBIDDEN_TEXT_RULES = (
    {
        "pattern": re.compile(r"04\.01-04\.05|04\.04|04\.05"),
        "code": "FORBIDDEN_04_SERIES_RANGE",
        "message": "04 系列只包含 04.01-04.03，不得引用 04.04、04.05 或 04.01-04.05 范围",
    },
    {
        "pattern": re.compile(r"\.trae-cn/rules/"),
        "code": "FORBIDDEN_TRAE_CN_RULES_DIR_PATH",
        "message": "Trae CN 用户级 Rules 入口不得使用 rules 目录，应使用 .trae-cn/user_rules/ldvh_rules.md",
    },
    {
        "pattern": re.compile(r"research\s*(入口|结论|吸收|资料)|refs\s*(摘要|入口)|`research`|`refs`"),
        "code": "FORBIDDEN_RESEARCH_REFS_TERMS",
        "message": "不得使用 research/refs 旧口径，应使用 docs/studies 或 docs/sources",
    },
    {
        "pattern": re.compile(r"机制入口|机制事实源|机制适配|固定机制子文档|机制子文档|环境适配映射"),
        "code": "FORBIDDEN_LEGACY_MECHANISM_TERMS",
        "message": "不得使用旧机制口径，应使用环境入口、适配措施、固定能力子文档或环境适配项",
    },
    {
        "pattern": re.compile(r"Agent\s*是|Agent 是"),
        "code": "FORBIDDEN_AGENT_SECOND_DEFINITION",
        "message": "Agent 定义应以 02 术语为准，其他文档不得使用二次定义式表达",
    },
)

# 04 系列文件预期清单（文件名 → 预期标题，包含实际空格）
CONSISTENCY_04_SERIES_FILES = {
    "04-规范落地与环境适配基础规范.md": "规范落地与环境适配基础规范",
    "04.01-规范落地声明规范.md": "规范落地声明规范",
    "04.02-LDVH能力资产与落地保障规范.md": "LDVH 能力资产与落地保障规范",
    "04.03-环境入口适配与部署规范.md": "环境入口适配与部署规范",
}
CONSISTENCY_04_SERIES_ORDER = list(CONSISTENCY_04_SERIES_FILES.keys())
CONSISTENCY_04_REQUIRED_TAIL = ["规范落地要求", "Human Gate 与检查要求", "待补齐事项"]
CONSISTENCY_04_RETIRED_FILES = {
    "04.04-个人环境特别要求规范.md": "个人环境特别要求已并入 04.03",
}


def consistency_04_series_issues():
    """检查 04 系列文件是否存在、标题和章节骨架是否符合预期"""
    issues = []
    actual_files = sorted(path.name for path in SPECS_DIR.glob("04*.md"))
    unexpected_files = [name for name in actual_files if name not in CONSISTENCY_04_SERIES_FILES and name not in CONSISTENCY_04_RETIRED_FILES]
    if unexpected_files:
        issues.append(Issue(SPECS_DIR, 1, f"04 系列存在未登记文件: {unexpected_files}", code="04_SERIES_UNEXPECTED_FILE"))
    active_files = [name for name in actual_files if name in CONSISTENCY_04_SERIES_FILES]
    if active_files != CONSISTENCY_04_SERIES_ORDER:
        issues.append(
            Issue(SPECS_DIR, 1, f"04 系列 active 文件顺序不符合预期: {active_files}", code="04_SERIES_ORDER_MISMATCH")
        )
    for filename, expected_title in CONSISTENCY_04_SERIES_FILES.items():
        path = SPECS_DIR / filename
        if not path.exists():
            issues.append(Issue(path, 1, f"04 系列文件缺失: {filename}", code="04_SERIES_FILE_MISSING"))
            continue
        # 检查标题是否匹配
        first_line = path.read_text(encoding="utf-8").splitlines()[0].strip()
        if not first_line.startswith("# ") or expected_title not in first_line:
            issues.append(
                Issue(path, 1, f"04 系列文件标题不符合预期: {first_line}，应包含 '{expected_title}'", code="04_SERIES_TITLE_MISMATCH")
            )
        sections = consistency_h2_sections(path)
        ordered_titles = [sections[key]["title"] for key in sorted(sections, key=int)]
        if len(ordered_titles) < len(CONSISTENCY_04_REQUIRED_TAIL) or ordered_titles[-3:] != CONSISTENCY_04_REQUIRED_TAIL:
            issues.append(
                Issue(
                    path,
                    1,
                    "04 系列章节尾部应依次为：规范落地要求、Human Gate 与检查要求、待补齐事项",
                    code="04_SERIES_SECTION_TAIL_MISMATCH",
                )
            )
    for filename, reason in CONSISTENCY_04_RETIRED_FILES.items():
        path = SPECS_DIR / filename
        if path.exists():
            issues.append(Issue(path, 1, f"04 系列已退役文件不应存在: {filename}（{reason}）", code="04_SERIES_RETIRED_FILE_PRESENT"))
    return issues


def consistency_forbidden_text_issues(paths):
    issues = []
    for path in iter_markdown_files(paths):
        in_code = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if Path(path).name.startswith("02-") and "不推荐表达" in stripped:
                continue
            for rule in CONSISTENCY_FORBIDDEN_TEXT_RULES:
                if rule["pattern"].search(stripped):
                    issues.append(Issue(path, line_number, rule["message"], code=rule["code"]))
            if ".trae-cn/" in stripped and "Rules" in stripped and "user_rules/ldvh_rules.md" not in stripped:
                issues.append(
                    Issue(
                        path,
                        line_number,
                        "Trae CN Rules 路径必须使用 .trae-cn/user_rules/ldvh_rules.md",
                        code="BAD_TRAE_CN_RULES_PATH",
                    )
                )
            if ".trae/" in stripped and "rules" in stripped and ".md" in stripped and "ldvh_rules.md" not in stripped:
                issues.append(
                    Issue(
                        path,
                        line_number,
                        "Trae 国际版 Rules 路径必须使用 .trae/rules/ldvh_rules.md",
                        code="BAD_TRAE_GLOBAL_RULES_PATH",
                    )
                )
    return issues


CONSISTENCY_WORKFLOW_REQUIRED_SECTIONS = {
    "1": "行动定位与适用场景",
    "2": "准入条件",
    "3": "事实源边界",
    "4": "Context 要求",
    "5": "Scenario 识别",
    "6": "执行流程",
    "7": "Gate 触发条件",
    "8": "Skill 和 Agent 调度",
    "9": "Code 与命令入口协作适配",
    "10": "事实源回写与证据留存",
    "11": "环境适配边界",
    "12": "行动特有可测试性锚点",
    "13": "规范落地要求",
    "14": "检查要求",
    "15": "待补齐事项",
}

# 索引文档的强制章节（来自 03.02-索引文档规范 §7，不得省略的章节）
CONSISTENCY_INDEX_REQUIRED_SECTIONS = {
    "3": "索引范围",
    "4": "文档清单",
    "5": "维护边界",
    "8": "集合一致性检查",
    "10": "Human Gate 与检查要求",
    "11": "待补齐事项",
}
CONSISTENCY_COLLECTION_NUMBER_RANGES = {
    "model": (20, 39, "工作模型集合索引条目编号应位于 20-39 区段"),
    "workflow": (40, 59, "工作流程集合索引条目编号应位于 40-59 区段"),
}
CONSISTENCY_HUMAN_GATE_CHECK_TITLES = {
    "Human Gate 与检查要求",
    "Human Gate 与总纲一致性检查",
    "检查要求",
}

# 来自 02-术语规范 §11 的不推荐裸词列表
CONSISTENCY_BARE_TERMS = ("规则", "技能", "代理", "智能体", "工具", "程序", "展示", "机制")

# 来自 02-术语规范 §12 的不推荐表达
CONSISTENCY_DEPRECATED_EXPRESSIONS = {
    "工作闭环": "运行闭环",
    "平台能力": "环境能力",
    "能力项": "环境能力 / 适配项 / 适配措施",
    "承接项": "适配项",
    "承接类型": "适配状态",
    "承接检查": "适配检查",
    "承接降级": "适配降级",
    "承接机制": "保障机制 / 适配方式 / 适配措施",
    "机制落地关系": "规范落地要求 + LDVH 能力保障 + 环境适配",
    "机制承接关系": "规范落地要求 + LDVH 能力保障 + 环境适配",
    "输入材料": "参考与研究材料",
    "待补齐项": "待补齐事项",
}

CONSISTENCY_INDEX_OVERRUN_KEYWORDS = ("字段契约", "状态机", "Scenario", "Gate 触发条件", "执行流程", "事实源回写", "对象关系")
CONSISTENCY_INDEX_FILE_RE = re.compile(r"^(20|40)-")
CONSISTENCY_INDEX_BOUNDARY_TERMS = (
    "本文不定义",
    "不定义",
    "未定义",
    "不替代",
    "只提供",
    "只说明",
    "不承载",
    "未承载",
    "边界",
    "检查",
    "讨论",
    "候选",
    "是否",
    "是什么",
    "应至少确认",
    "让本文定义",
)


def consistency_line_is_index_boundary_context(line):
    return consistency_line_is_negative(line) or any(term in line for term in CONSISTENCY_INDEX_BOUNDARY_TERMS)


def consistency_index_overrun_issues(paths):
    issues = []
    for path in iter_markdown_files(paths):
        if not CONSISTENCY_INDEX_FILE_RE.match(Path(path).name):
            continue
        in_code = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if stripped.startswith("#") or stripped.startswith("|") or stripped.startswith(">"):
                continue
            if consistency_line_is_index_boundary_context(stripped):
                continue
            for keyword in CONSISTENCY_INDEX_OVERRUN_KEYWORDS:
                if keyword in stripped:
                    issues.append(Issue(path, line_number, f"索引文档疑似越界包含具体工作模型/流程内容关键词: {keyword}", code="INDEX_OVERRUN_KEYWORD"))
                    break
    return issues


def consistency_clean_cell(value):
    text = str(value).strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        return text[1:-1]
    return text


def consistency_table_rows(path, heading_title):
    rows = []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    header_seen = False
    for line_number, line in enumerate(lines, start=1):
        heading = HEADING_RE.match(line)
        if heading:
            title = heading.group(2).strip()
            in_section = heading_title in title
            header_seen = False
            continue
        if not in_section:
            continue
        stripped = line.strip()
        if not stripped:
            if header_seen:
                break
            continue
        if not stripped.startswith("|"):
            if header_seen:
                break
            continue
        cells = [consistency_clean_cell(cell) for cell in stripped.strip("|").split("|")]
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        if not header_seen:
            header_seen = True
            continue
        rows.append((line_number, cells))
    return rows


def consistency_collection_entries(path, collection_kind):
    entries = []
    for line_number, cells in consistency_table_rows(path, "文档清单"):
        if collection_kind == "model" and len(cells) >= 5:
            number, title, item_type, status, position = cells[:5]
            source = None
        elif collection_kind == "workflow" and len(cells) >= 6:
            number, title, item_type, status, source, position = cells[:6]
        else:
            continue
        entries.append(
            {
                "path": path,
                "line": line_number,
                "number": number,
                "title": title,
                "type": item_type,
                "status": status,
                "source": source,
                "position": position,
                "aliases": consistency_entry_aliases(number, title, position),
            }
        )
    return entries


def consistency_collection_range_issues(entries, collection_kind):
    issues = []
    lower, upper, message = CONSISTENCY_COLLECTION_NUMBER_RANGES[collection_kind]
    for entry in entries:
        try:
            number = int(entry["number"])
        except ValueError:
            issues.append(Issue(entry["path"], entry["line"], f"集合索引条目编号不可解析: {entry['number']}", code="COLLECTION_INDEX_NUMBER_INVALID"))
            continue
        if number < lower or number > upper:
            issues.append(Issue(entry["path"], entry["line"], f"{message}: {entry['number']} {entry['title']}", code="COLLECTION_INDEX_RANGE_MISMATCH"))
    return issues


def consistency_entry_aliases(number, title, position):
    aliases = {str(number).strip()}
    for text in (title, position):
        cleaned = re.sub(r"（不建文档）", "", text)
        cleaned = re.sub(r"^\d+\s*", "", cleaned)
        cleaned = re.sub(r"^\d+\s*已退回\s*", "", cleaned)
        cleaned = re.sub(r"^\d+\s*已取消\s*", "", cleaned)
        cleaned = cleaned.strip()
        if cleaned and not cleaned.startswith("待定") and cleaned != "待占用":
            aliases.add(cleaned)
        for part in re.split(r"\s*/\s*| / |、|，|,|\(|（", cleaned):
            part = part.strip(" )）")
            if len(part) >= 2 and not part.startswith("已") and part not in {"不建文档"}:
                aliases.add(part)
    return sorted(aliases, key=len, reverse=True)


def consistency_h2_sections(path):
    sections = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = re.match(r"^##\s+(\d+)\.\s*(.+?)\s*$", line)
        if match:
            sections[match.group(1)] = {"title": match.group(2).strip(), "line": line_number}
    return sections


def consistency_work_model_skeleton_issues(entries):
    issues = []
    for entry in entries:
        if entry["status"] != "active" or "具体工作模型规范" not in entry["type"]:
            continue
        try:
            number = int(entry["number"])
        except ValueError:
            continue
        if number < 21 or number > 39:
            continue
        doc_name = entry["title"]
        path = SPECS_DIR / doc_name
        # 如果 SPECS_DIR 下找不到，尝试使用 entry 中的 path
        if not path.exists() and "path" in entry:
            alt_path = Path(entry["path"]) if not isinstance(entry["path"], Path) else entry["path"]
            if alt_path.exists():
                path = alt_path
        if not path.exists():
            issues.append(Issue(entry["path"], entry["line"], f"active 工作模型主文档不存在: {doc_name}", code="WORK_MODEL_DOC_MISSING"))
            continue
        sections = consistency_h2_sections(path)
        for section_number, expected_title in CONSISTENCY_WORK_MODEL_REQUIRED_SECTIONS.items():
            actual = sections.get(section_number)
            if actual is None:
                issues.append(Issue(path, 1, f"工作模型缺少 03.03 强制章节: ## {section_number}. {expected_title}", code="WORK_MODEL_SECTION_MISSING"))
            elif actual["title"] != expected_title:
                issues.append(
                    Issue(
                        path,
                        actual["line"],
                        f"工作模型章节标题不符合 03.03: ## {section_number}. {actual['title']}，应为 ## {section_number}. {expected_title}",
                        code="WORK_MODEL_SECTION_TITLE_MISMATCH",
                    )
                )
    return issues


def consistency_line_has_removed_alias(line, aliases):
    for alias in aliases:
        if not alias:
            continue
        if alias.isdigit():
            if re.search(rf"(?<![\d-]){re.escape(alias)}(?![\d-])", line):
                return True
            continue
        if alias in line:
            return True
    return False


def consistency_line_is_negative(line):
    return any(term in line for term in CONSISTENCY_NEGATIVE_TERMS)


def consistency_line_is_dangerous(line):
    if "active 时" in line or "`active` 时" in line:
        return False
    return any(term in line for term in CONSISTENCY_DANGEROUS_TERMS)


def consistency_removed_consumption_issues(entries, paths, code):
    issues = []
    removed = [entry for entry in entries if entry["status"] == "removed"]
    for path in iter_markdown_files(paths):
        if path.name in {"20-工作模型集合索引.md", "40-工作流程集合索引.md"}:
            continue
        in_code = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code or consistency_line_is_negative(stripped) or not consistency_line_is_dangerous(stripped):
                continue
            for entry in removed:
                if consistency_line_has_removed_alias(stripped, entry["aliases"]):
                    issues.append(Issue(path, line_number, f"removed 集合项疑似被当作当前生效项消费: {entry['number']} {entry['title']}", code=code))
    return issues


def consistency_terminology_status_issues(model_entries, workflow_entries):
    path = SPECS_DIR / "02-术语规范.md"
    if not path.exists():
        return [Issue(path, 1, "02 术语规范不存在，无法检查术语与集合状态一致性", code="TERMINOLOGY_DOC_MISSING")]
    entries = [entry for entry in model_entries + workflow_entries if entry["status"] == "removed"]
    issues = []
    in_code = False
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code or consistency_line_is_negative(stripped) or not consistency_line_is_dangerous(stripped):
            continue
        for entry in entries:
            if consistency_line_has_removed_alias(stripped, entry["aliases"]):
                issues.append(Issue(path, line_number, f"02 术语疑似把 removed 集合项定义为当前生效概念: {entry['number']} {entry['title']}", code="TERMINOLOGY_REMOVED_STATUS_CONFLICT"))
    return issues


def consistency_retired_semantic_issues(paths):
    issues = []
    for path in iter_markdown_files(paths):
        in_code = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code or consistency_line_is_negative(stripped):
                continue
            for rule in CONSISTENCY_RETIRED_REFERENCE_RULES:
                if not any(alias in stripped for alias in rule["aliases"]):
                    continue
                if not any(term in stripped for term in rule["dangerous_terms"]):
                    continue
                issues.append(Issue(path, line_number, rule["message"], code=rule["code"]))
    return issues


def consistency_workflow_skeleton_issues(workflow_entries):
    """检查工作流程文档是否覆盖 03.04 规定的强制章节"""
    issues = []
    for entry in workflow_entries:
        if entry["status"] != "active" or "具体工作流程规范" not in entry["type"]:
            continue
        try:
            number = int(entry["number"])
        except ValueError:
            continue
        if number < 41 or number > 59:
            continue
        doc_name = entry["title"]
        path = SPECS_DIR / doc_name
        # 如果 SPECS_DIR 下找不到，尝试使用 entry 中的 path
        if not path.exists() and "path" in entry:
            alt_path = Path(entry["path"]) if not isinstance(entry["path"], Path) else entry["path"]
            if alt_path.exists():
                path = alt_path
        if not path.exists():
            issues.append(Issue(entry["path"], entry["line"], f"active 工作流程主文档不存在: {doc_name}", code="WORKFLOW_DOC_MISSING"))
            continue
        sections = consistency_h2_sections(path)
        for section_number, expected_title in CONSISTENCY_WORKFLOW_REQUIRED_SECTIONS.items():
            actual = sections.get(section_number)
            if actual is None:
                issues.append(Issue(path, 1, f"工作流程缺少 03.04 强制章节: ## {section_number}. {expected_title}", code="WORKFLOW_SECTION_MISSING"))
            elif actual["title"] != expected_title:
                issues.append(
                    Issue(
                        path,
                        actual["line"],
                        f"工作流程章节标题不符合 03.04: ## {section_number}. {actual['title']}，应为 ## {section_number}. {expected_title}",
                        code="WORKFLOW_SECTION_TITLE_MISMATCH",
                    )
                )
    return issues


def consistency_index_skeleton_issues(paths):
    """检查 20 和 40 索引文档是否覆盖 03.02 规定的强制章节"""
    issues = []
    # 从传入路径中查找索引文档，同时保留 SPECS_DIR 作为后备
    index_files = []
    for p in iter_markdown_files(paths):
        if re.match(r"^(20|40)-", Path(p).name):
            index_files.append(Path(p))
    # 也检查 SPECS_DIR
    for f in SPECS_DIR.glob("*.md"):
        if re.match(r"^(20|40)-", f.name) and f not in index_files:
            index_files.append(f)
    for path in index_files:
        sections = consistency_h2_sections(path)
        for section_number, expected_title in CONSISTENCY_INDEX_REQUIRED_SECTIONS.items():
            actual = sections.get(section_number)
            if actual is None:
                issues.append(Issue(path, 1, f"索引文档缺少 03.02 强制章节: ## {section_number}. {expected_title}", code="INDEX_SECTION_MISSING"))
    return issues


def consistency_human_gate_check_section_issues(paths):
    issues = []
    for path in iter_markdown_files(paths):
        if not landing_is_formal_spec(path):
            continue
        sections = consistency_h2_sections(path)
        titles = {section["title"] for section in sections.values()}
        if "规范落地要求" not in titles:
            continue
        if titles & CONSISTENCY_HUMAN_GATE_CHECK_TITLES:
            continue
        if "Human Gate" in titles and "检查要求" in titles:
            continue
        issues.append(Issue(path, 1, "正式规范文档缺少 Human Gate / 检查要求兼容章节", code="HUMAN_GATE_CHECK_SECTION_MISSING"))
    return issues


def consistency_bare_term_issues(paths):
    """检查 specs 中是否存在不推荐裸词的未限定使用"""
    issues = []
    for path in iter_markdown_files(paths):
        # 跳过 02 术语规范自身
        if Path(path).name.startswith("02-"):
            continue
        in_code = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            # 跳过标题行和表格行
            if stripped.startswith("#") or stripped.startswith("|"):
                continue
            # 跳过负面上下文
            if consistency_line_is_negative(stripped):
                continue
            # 检查裸词：要求裸词前后不是中文字符（即没有定语修饰）
            for term in CONSISTENCY_BARE_TERMS:
                for match in re.finditer(re.escape(term), stripped):
                    start = match.start()
                    end = match.end()
                    prefix = stripped[:start].rstrip()
                    suffix = stripped[end:].lstrip()
                    has_prefix_modifier = bool(prefix) and re.match(r"[A-Za-z0-9_/\-\u4e00-\u9fff]", prefix[-1])
                    has_suffix_modifier = bool(suffix) and re.match(r"[A-Za-z0-9_/\-\u4e00-\u9fff]", suffix[0])
                    if has_prefix_modifier or has_suffix_modifier:
                        continue
                    issues.append(Issue(path, line_number, f"疑似不推荐裸词: '{term}'（02 §11 要求中文术语不得裸用）", code="BARE_TERM_USAGE"))
    return issues


def consistency_deprecated_expression_issues(paths):
    """检查 specs 中是否使用了 02 §12 的不推荐表达"""
    issues = []
    for path in iter_markdown_files(paths):
        # 跳过 02 术语规范自身
        if Path(path).name.startswith("02-"):
            continue
        in_code = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if stripped.startswith("#") or stripped.startswith("|"):
                continue
            if consistency_line_is_negative(stripped):
                continue
            for deprecated, recommended in CONSISTENCY_DEPRECATED_EXPRESSIONS.items():
                if deprecated in stripped:
                    issues.append(Issue(path, line_number, f"不推荐表达: '{deprecated}'，推荐: '{recommended}'（02 §12）", code="DEPRECATED_EXPRESSION"))
    return issues


def consistency_check(paths=None):
    check_paths = paths if paths else [str(SPECS_DIR)]
    model_index = SPECS_DIR / "20-工作模型集合索引.md"
    workflow_index = SPECS_DIR / "40-工作流程集合索引.md"
    issues = []
    model_entries = consistency_collection_entries(model_index, "model") if model_index.exists() else []
    workflow_entries = consistency_collection_entries(workflow_index, "workflow") if workflow_index.exists() else []
    issues.extend(consistency_collection_range_issues(model_entries, "model"))
    issues.extend(consistency_collection_range_issues(workflow_entries, "workflow"))
    issues.extend(consistency_work_model_skeleton_issues(model_entries))
    issues.extend(consistency_removed_consumption_issues(model_entries, check_paths, "MODEL_REMOVED_CONSUMPTION"))
    issues.extend(consistency_removed_consumption_issues(workflow_entries, check_paths, "WORKFLOW_REMOVED_CONSUMPTION"))
    issues.extend(consistency_terminology_status_issues(model_entries, workflow_entries))
    issues.extend(consistency_retired_semantic_issues(check_paths))
    issues.extend(consistency_workflow_skeleton_issues(workflow_entries))
    issues.extend(consistency_index_skeleton_issues(check_paths))
    issues.extend(consistency_human_gate_check_section_issues(check_paths))
    issues.extend(consistency_bare_term_issues(check_paths))
    issues.extend(consistency_deprecated_expression_issues(check_paths))
    issues.extend(consistency_forbidden_text_issues(check_paths))
    issues.extend(consistency_04_series_issues())
    issues.extend(consistency_index_overrun_issues(check_paths))
    return issues


def consistency_main(paths=None):
    issues = consistency_check(paths)
    if issues:
        print(f"一致性检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("一致性检查通过。")
    return 0


# ══════════════════════════════════════════════════════════════════════
# doc — 文档编号/标题规范检查
# ══════════════════════════════════════════════════════════════════════

DOC_NUMBERED_HEADING_RE = doc_structure_checks.DOC_NUMBERED_HEADING_RE
DOC_CHINESE_HEADING_RE = doc_structure_checks.DOC_CHINESE_HEADING_RE
DOC_ROMAN_HEADING_RE = doc_structure_checks.DOC_ROMAN_HEADING_RE
DOC_UNNUMBERED_ALLOWED_HEADINGS = doc_structure_checks.DOC_UNNUMBERED_ALLOWED_HEADINGS
Heading = doc_structure_checks.Heading
HeadingNumberState = doc_structure_checks.HeadingNumberState


def sync_doc_structure_config():
    doc_structure_checks.PROJECT_ROOT = PROJECT_ROOT


def doc_parse_heading_number(title):
    return doc_structure_checks.parse_heading_number(title)


def doc_check_file(path):
    return doc_structure_checks.check_file(path)


def doc_check_paths(paths):
    return doc_structure_checks.check_paths(paths)


def doc_main(paths):
    sync_doc_structure_config()
    return doc_structure_checks.main(paths)


# ══════════════════════════════════════════════════════════════════════
# refs — 引用完整性检查
# ══════════════════════════════════════════════════════════════════════

REFS_SECTION_HEADING_RE = refs_checks.REFS_SECTION_HEADING_RE
REFS_SECTION_REF_RE = refs_checks.REFS_SECTION_REF_RE
REFS_EXPLICIT_PATH_RE = refs_checks.REFS_EXPLICIT_PATH_RE
REFS_SHORTHAND_RE = refs_checks.REFS_SHORTHAND_RE
REFS_CHINESE_SECTION_RE = refs_checks.REFS_CHINESE_SECTION_RE
Document = refs_checks.Document


def sync_refs_config():
    refs_checks.PROJECT_ROOT = PROJECT_ROOT
    refs_checks.SPECS_DIR = SPECS_DIR
    refs_checks.LEGACY_SPECS_DIR = LEGACY_SPECS_DIR


def refs_extract_sections(path):
    return refs_checks.extract_sections(path)


def refs_build_document_map(paths):
    sync_refs_config()
    return refs_checks.build_document_map(paths)


def refs_resolve_markdown_path(raw_path, current_path):
    sync_refs_config()
    return refs_checks.resolve_markdown_path(raw_path, current_path)


def refs_resolve_shorthand(prefix, documents):
    sync_refs_config()
    return refs_checks.resolve_shorthand(prefix, documents)


def refs_resolve_parent_document(path, documents):
    sync_refs_config()
    return refs_checks.resolve_parent_document(path, documents)


def refs_default_check_paths():
    sync_refs_config()
    return refs_checks.default_check_paths()


def refs_check_section_target(issues, source_path, line_number, target_path, section, documents, code):
    sync_refs_config()
    refs_checks.check_section_target(issues, source_path, line_number, target_path, section, documents, code)


def refs_check_file(path, documents):
    sync_refs_config()
    return refs_checks.check_file(path, documents)


def refs_check_paths(paths):
    sync_refs_config()
    return refs_checks.check_paths(paths)


def refs_main(paths):
    sync_refs_config()
    return refs_checks.main(paths)


# ══════════════════════════════════════════════════════════════════════
# landing — 规范落地要求表检查
# ══════════════════════════════════════════════════════════════════════

LANDING_SECTION_TITLE = landing_checks.LANDING_SECTION_TITLE
LANDING_REQUIRED_COLUMNS = landing_checks.LANDING_REQUIRED_COLUMNS
LANDING_ALLOWED_TYPES = landing_checks.LANDING_ALLOWED_TYPES
LANDING_REPORT_OWNER_AREAS = landing_report_checks.LANDING_REPORT_OWNER_AREAS
LANDING_REPORT_AREA_LABELS = landing_report_checks.LANDING_REPORT_AREA_LABELS
LANDING_REPORT_WRITEBACK_AREAS = landing_report_checks.LANDING_REPORT_WRITEBACK_AREAS
LANDING_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS
LANDING_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS
LANDING_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS
LANDING_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS
LANDING_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS
LANDING_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS = landing_report_checks.LANDING_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS
RUNTIME_PROJECTION_REMEDIATION_LABELS = landing_report_checks.RUNTIME_PROJECTION_REMEDIATION_LABELS
RUNTIME_PROJECTION_REMEDIATION_TERMS = landing_report_checks.RUNTIME_PROJECTION_REMEDIATION_TERMS
LANDING_REPORT_HUMAN_GATE_DECISION_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_DECISION_TERMS
LANDING_REPORT_HUMAN_GATE_POLICY_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_POLICY_TERMS
LANDING_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS
LANDING_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS
LANDING_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS
LANDING_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS
LANDING_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS = landing_report_checks.LANDING_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS
LANDING_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS = landing_report_checks.LANDING_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS
LANDING_REPORT_DEGRADED_MARKERS = landing_report_checks.LANDING_REPORT_DEGRADED_MARKERS
LANDING_REPORT_OPEN_MARKERS = landing_report_checks.LANDING_REPORT_OPEN_MARKERS
LANDING_REPORT_OPEN_PATTERNS = landing_report_checks.LANDING_REPORT_OPEN_PATTERNS
LANDING_REPORT_HUMAN_GATE_PATTERNS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_PATTERNS
LANDING_REPORT_CAPABILITY_CHECKS = landing_report_checks.LANDING_REPORT_CAPABILITY_CHECKS


def sync_landing_config():
    landing_checks.PROJECT_ROOT = PROJECT_ROOT
    landing_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR


def sync_landing_report_config():
    landing_report_checks.PROJECT_ROOT = PROJECT_ROOT
    landing_report_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    landing_report_checks.DOCS_DIR = DOCS_DIR
    landing_report_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def landing_default_check_paths():
    sync_landing_config()
    return landing_checks.default_check_paths()


def landing_is_formal_spec(path):
    sync_landing_config()
    return landing_checks.is_formal_spec(path)


def landing_strip_section_number(title):
    return landing_checks.strip_section_number(title)


def landing_split_cells(line):
    return landing_checks.split_cells(line)


def landing_is_separator(cells):
    return landing_checks.is_separator(cells)


def landing_clean_cell(value):
    return landing_checks.clean_cell(value)


def landing_relative_path(path):
    sync_landing_config()
    return landing_checks.landing_relative_path(path)


def landing_extract_requirements_file(path):
    sync_landing_config()
    return landing_checks.extract_requirements_file(path)


def landing_report_match_marker(text, markers):
    return landing_report_checks.landing_report_match_marker(text, markers)


def landing_report_infer_status(requirement):
    return landing_report_checks.landing_report_infer_status(requirement)


def landing_report_count_by(requirements, key):
    return landing_report_checks.landing_report_count_by(requirements, key)


def landing_report_is_gap(item):
    return landing_report_checks.landing_report_is_gap(item)


def landing_report_human_gate_subcategory(item):
    return landing_report_checks.landing_report_human_gate_subcategory(item)


def landing_report_human_gate_decision_flow(item):
    return landing_report_checks.landing_report_human_gate_decision_flow(item)


def landing_report_human_gate_policy_flow(item):
    return landing_report_checks.landing_report_human_gate_policy_flow(item)


def landing_report_human_gate_support_flow(item):
    return landing_report_checks.landing_report_human_gate_support_flow(item)


def landing_report_human_gate_diagnostic_flow(item):
    return landing_report_checks.landing_report_human_gate_diagnostic_flow(item)


def landing_report_runtime_projection_subcategory(item):
    return landing_report_checks.landing_report_runtime_projection_subcategory(item)


def _classify_runtime_projection_remediation(item):
    return landing_report_checks._classify_runtime_projection_remediation(item)


def landing_report_build_gap_categories(requirements, capability_gaps):
    return landing_report_checks.landing_report_build_gap_categories(requirements, capability_gaps)


def landing_report_document_text(paths):
    return landing_report_checks.landing_report_document_text(paths)


def landing_report_terms_present(text, terms):
    return landing_report_checks.landing_report_terms_present(text, terms)


def landing_report_build_capability_gaps(formal_files, runtime_projection_report=None, human_gate_report=None):
    return landing_report_checks.landing_report_build_capability_gaps(formal_files, runtime_projection_report, human_gate_report)


def landing_report_build(paths=None):
    sync_landing_report_config()
    return landing_report_checks.landing_report_build(paths)


def landing_report_shorten(text, limit=96):
    return landing_report_checks.landing_report_shorten(text, limit)


def landing_report_format_text(report):
    return landing_report_checks.landing_report_format_text(report)


def landing_report_main(paths=None, output_format="text"):
    sync_landing_report_config()
    return landing_report_checks.landing_report_main(paths, output_format)


def landing_check_file(path):
    sync_landing_config()
    return landing_checks.check_file(path)


def landing_check_paths(paths):
    sync_landing_config()
    return landing_checks.check_paths(paths)


def landing_main(paths):
    sync_landing_config()
    return landing_checks.main(paths)


# ══════════════════════════════════════════════════════════════════════
# human-gate — Human Gate 轻量人类决策记录结构检查
# ══════════════════════════════════════════════════════════════════════

HUMAN_GATE_HEADER_RE = human_gate_checks.HUMAN_GATE_HEADER_RE
HUMAN_GATE_FIELD_RE = human_gate_checks.HUMAN_GATE_FIELD_RE
HUMAN_GATE_FILE_SUFFIXES = human_gate_checks.HUMAN_GATE_FILE_SUFFIXES
HUMAN_GATE_REQUIRED_FIELDS = human_gate_checks.HUMAN_GATE_REQUIRED_FIELDS
HUMAN_GATE_YAML_KEYS = human_gate_checks.HUMAN_GATE_YAML_KEYS


def sync_human_gate_config():
    human_gate_checks.PROJECT_ROOT = PROJECT_ROOT
    human_gate_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    human_gate_checks.DOCS_DIR = DOCS_DIR


def human_gate_default_check_paths():
    sync_human_gate_config()
    return human_gate_checks.default_check_paths()


def human_gate_iter_files(paths):
    sync_human_gate_config()
    return human_gate_checks.iter_files(paths)


def human_gate_normalize_label(label):
    return human_gate_checks.normalize_label(label)


def human_gate_alias_map():
    return human_gate_checks.alias_map()


def human_gate_parse_field_line(line):
    return human_gate_checks.parse_field_line(line)


def human_gate_collect_record(lines, start_index):
    return human_gate_checks.collect_record(lines, start_index)


def human_gate_record_fields(block):
    return human_gate_checks.record_fields(block)


def human_gate_check_record_fields(path, line, fields, field_lines):
    return human_gate_checks.check_record_fields(path, line, fields, field_lines)


def human_gate_check_markdown_file(path):
    return human_gate_checks.check_markdown_file(path)


def human_gate_yaml_records(data):
    return human_gate_checks.yaml_records(data)


def human_gate_yaml_line_map(text):
    return human_gate_checks.yaml_line_map(text)


def human_gate_yaml_record_fields(record):
    return human_gate_checks.yaml_record_fields(record)


def human_gate_check_yaml_file(path):
    return human_gate_checks.check_yaml_file(path)


def human_gate_check_file(path):
    return human_gate_checks.check_file(path)


def human_gate_check_paths(paths):
    return human_gate_checks.check_paths(paths)


def human_gate_count_markdown_records_file(path):
    return human_gate_checks.count_markdown_records_file(path)


def human_gate_count_yaml_records_file(path):
    return human_gate_checks.count_yaml_records_file(path)


def human_gate_count_records_file(path):
    return human_gate_checks.count_records_file(path)


def human_gate_report_build(paths=None):
    sync_human_gate_config()
    return human_gate_checks.report_build(paths)


def human_gate_report_format_text(report):
    return human_gate_checks.report_format_text(report)


def human_gate_report_main(paths=None, output_format="text"):
    sync_human_gate_config()
    return human_gate_checks.report_main(paths, output_format)


def human_gate_main(paths):
    sync_human_gate_config()
    return human_gate_checks.main(paths)


# ══════════════════════════════════════════════════════════════════════
# governed-projects — 工作区根目录管辖项目配置检查
# ══════════════════════════════════════════════════════════════════════

GOVERNED_PROJECTS_FILENAME = governed_projects_checks.GOVERNED_PROJECTS_FILENAME


def governed_projects_check_root(root):
    return governed_projects_checks.check_root(root)


def governed_projects_main(root):
    governed_projects_checks.PROJECT_ROOT = PROJECT_ROOT
    return governed_projects_checks.main(root)


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
    ("environment_matrix", "环境入口与能力资产检查"),
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
        (PROJECT_ROOT / "specs", "规范资产", "规范"),
        (PROJECT_ROOT / "code", "Code 能力资产", "Code"),
        (PROJECT_ROOT / "tests", "测试证明", "Code"),
        (PROJECT_ROOT / "web", "Web 能力资产", "Web"),
        (PROJECT_ROOT / "ldvh-base", "工作对象事实源", "事实源"),
        (PROJECT_ROOT / "rules" / "LDVH-AI-ENTRY.md", "运行投影入口", "环境承接"),
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

    index_paths = [SPECS_DIR / "20-工作模型集合索引.md", SPECS_DIR / "40-工作流程集合索引.md"]
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

    capability_path = SPECS_DIR / "04.02-LDVH能力资产与落地保障规范.md"
    environment_path = SPECS_DIR / "04.03-环境入口适配与部署规范.md"
    matrix_issues = []
    if not capability_path.exists():
        matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_CAPABILITY_SPEC_MISSING", "缺少 LDVH 能力资产规范文件", capability_path, "环境承接"))
    else:
        capability_text = capability_path.read_text(encoding="utf-8")
        for asset_type in ["Rules 资产", "Skill 资产", "Agent 资产", "Hook 资产"]:
            if asset_type not in capability_text:
                matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_CAPABILITY_ASSET_MISSING", f"能力资产规范缺少固定资产类型: {asset_type}", capability_path, "环境承接"))
    if not environment_path.exists():
        matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_ENV_ENTRY_SPEC_MISSING", "缺少环境入口适配与部署规范文件", environment_path, "环境承接"))
    else:
        environment_text = environment_path.read_text(encoding="utf-8")
        for environment in ["Trae CN", "Trae 国际版", "Codex App"]:
            if environment not in environment_text:
                matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_ENV_ENTRY_MISSING", f"环境入口适配规范缺少入口: {environment}", environment_path, "环境承接"))
    items.append(ldvh_bootstrap_baseline_item(
        "environment_matrix",
        "环境入口与能力资产检查",
        "open" if matrix_issues else "closed",
        "checked 04.02 capability assets and 04.03 environment entries",
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

    code_paths = [PROJECT_ROOT / "code" / "specs_validate.py", PROJECT_ROOT / "tests" / "code" / "test_specs_validate.py"]
    code_issues = [
        ldvh_bootstrap_issue("BOOTSTRAP_CODE_SELF_CHECK_MISSING", f"缺少 Code 自检关键文件: {landing_relative_path(path)}", path, "Code")
        for path in code_paths
        if not path.exists()
    ]
    items.append(ldvh_bootstrap_baseline_item(
        "code_self_check",
        "Code 自检",
        "open" if code_issues else "closed",
        "checked specs_validate.py and tests/code/test_specs_validate.py presence",
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
            "tool": "code/specs_validate.py",
            "report": "ldvh-landing-check",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "project_root": str(PROJECT_ROOT),
            "workspace_root": str(workspace_root),
            "scope": "project-local Git facts plus explicit workspace governed-projects config",
            "bootstrap_baseline_source": "docs/studies/42-ldvh-landing-check-LDVH落地与检查.md (已退回 studies，待重新设计)",
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
            "tool": "code/specs_validate.py",
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
    r"(?<![`\w./-])((?:specs/[^\s`，。；、)）]+\.md|code/docs/[^\s`，。；、)）]+\.md|docs/(?:studies|sources|research|refs)/[^\s`，。；、)）]+\.md|docs/[^/\s`，。；、)）]+\.md))"
)
INDEX_RESEARCH_REF_RE = re.compile(r"(?<![`\w./-])(?:`)?((?:specs/research/|docs/research/)[^`\s，。；、)）]+\.md)(?:`)?")
INDEX_DOCS_MATERIAL_REF_RE = re.compile(r"(?<![`\w./-])(?:`)?((?:docs/(?:studies|sources|research|refs)/)[^`\s，。；、)）]+\.md)(?:`)?")
INDEX_DOCS_ROOT_ASSET_REF_RE = re.compile(r"(?<![`\w./-])(?:`)?(docs/[^/`\s，。；、)）]+\.md)(?:`)?")
INDEX_EXTERNAL_URL_RE = re.compile(r"https?://[^\s`，。；、)）]+")
INDEX_SECTION_REF_RE = re.compile(r"§([一二三四五六七八九十百千万\d]+(?:\.\d+)*)")
INDEX_DOC_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)?)-")
INDEX_DEFINITION_SENTENCE_RE = re.compile(r"^(?:(?:在本文|在本规范|在本文档)中[，,]?\s*)?(?:(?:[-*]|\d+[.、])\s*)?(?:\*\*)?([^|。；;，,\s`*是]{2,24})(?:\*\*)?\s*(?:是指|定义为|包括且仅包括|指(?!向|引|标|回|令|定|派|出|控|责|南|针|纹|挥|数|甲|望)|是(?!否))")
INDEX_FOOTNOTE_RE = re.compile(r"^\[\^[^\]]+\]:\s*(.+)$")
INDEX_FORBIDDEN_DEFINITION_SECTION_TITLES = {"术语定义", "概念定义", "名词解释"}
INDEX_GOVERNED_TERMS = {
    "LDVH 自身项目", "管辖项目", "管辖项目配置", "LDVH 文档工作区", "规范正文区", "管辖项目文档工作区", "正文区", "studies", "sources",
    "来源", "吸收", "参考与研究材料", "待补齐事项", "正式规范", "资产", "规范资产", "文本能力资产", "Code 能力资产", "Web 能力资产",
    "工作对象事实源", "用户资产", "可变资料区", "候选事项", "索引文档", "说明性索引", "规范型集合索引", "规范落地要求", "能力保障",
    "LDVH 能力资产", "保障机制", "环境入口", "环境适配", "环境能力清单", "适配措施", "适配措施状态", "环境", "AI 开发环境",
    "环境实体", "环境能力", "适配边界", "适配检查", "适配降级", "工作区级入口", "项目级入口", "AI 统一入口", "LDVH 项目事实源",
    "项目接入说明", "能力缺口", "环境缺口", "漂移", "LDVH 运行纪律", "启用", "薄引用", "开发环境", "工作模型", "工作对象", "工作字段",
    "字段内容格式", "对象状态", "集合状态", "检查过程状态", "派生状态", "Change commit", "工作流程", "Code", "Web", "受控写入", "受控轻写入",
    "Rules / Instructions", "Skill", "LDVH 自建 Skill", "LDVH 包装 Skill", "Agent", "Hook / 自动触发", "MCP / 模型上下文协议", "运行闭环", "具体工作流程",
    "行动", "Scenario 识别条件", "适用场景", "步骤", "阶段标签", "Apply", "Verify", "Review", "Recheck", "Gate", "Human Gate 记录", "LDVH落地",
    "环境确认", "LDVH落地与检查", "落地检查报告", "检查", "校验", "验证", "审计", "审阅", "审核", "写入", "回写", "事实源回写",
}
INDEX_DEFINITION_WHITELIST_TERMS = {"本文", "本规范", "00", "02", "Code", "Web", "Human Gate", "Rules", "Skill", "Agent", "Hook", "MCP"}
INDEX_ALLOWED_DEFINITION_OWNERS = {
    "开发环境": {"00"},
    "工作模型": {"00", "05"},
    "字段内容格式": {"00", "05.01"},
    "管辖项目配置": {"03.05"},
    "工作流程": {"00", "06"},
    "Gate": {"06"},
    "事实源回写": {"06", "09"},
}
INDEX_REVERSE_RELATED_TERMS = ("反向", "被下游", "被引用", "谁引用", "可发现性", "追溯", "影响面")


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
        diagnostics.extend(self.diagnose_cross_document(docs, relations))
        return {
            "metadata": {
                "derived": True,
                "source_of_truth": False,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "tool": "code/specs_validate.py",
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
            if stripped.startswith(">"):
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
                    self.diagnostic(rel_path, line_number, "warning", "RESEARCH_REFERENCE_IN_SPEC", f"正式规范不得引用 studies 文档路径: {target}")
                )
            for match in INDEX_DOCS_MATERIAL_REF_RE.finditer(line):
                target = match.group(1)
                diagnostics.append(
                    self.diagnostic(rel_path, line_number, "warning", "DOCS_PATH_REFERENCE_IN_SPEC", f"正式规范不得引用 docs 可变资料路径: {target}")
                )
            for match in INDEX_DOCS_ROOT_ASSET_REF_RE.finditer(line):
                target = match.group(1)
                diagnostics.append(
                    self.diagnostic(rel_path, line_number, "warning", "DOCS_ROOT_ASSET_REFERENCE_IN_SPEC", f"正式规范不得引用 docs 根目录用户资产路径: {target}")
                )
            for match in INDEX_EXTERNAL_URL_RE.finditer(line):
                target = match.group(0)
                diagnostics.append(
                    self.diagnostic(rel_path, line_number, "warning", "EXTERNAL_REFERENCE_IN_SPEC", f"正式规范不得引用外部 URL: {target}")
                )
            if doc_kind in {"formal_spec", "subdocument"} and not path.name.startswith("02-"):
                diagnostics.extend(self.diagnose_definition_section_heading(rel_path, line_number, stripped))
                diagnostics.extend(self.diagnose_definition_sentences(rel_path, line_number, stripped))
        return diagnostics


    def diagnose_definition_section_heading(self, rel_path, line_number, stripped):
        diagnostics = []
        match = HEADING_RE.match(stripped)
        if not match:
            return diagnostics
        title = self.strip_section_number(match.group(2).strip())
        if title not in INDEX_FORBIDDEN_DEFINITION_SECTION_TITLES:
            return diagnostics
        diagnostics.append(
            self.diagnostic(
                rel_path,
                line_number,
                "warning",
                "FORBIDDEN_TERM_DEFINITION_SECTION",
                f"非 02 术语规范不得设置二次术语定义章节: {title}",
            )
        )
        return diagnostics


    def diagnose_definition_sentences(self, rel_path, line_number, stripped):
        diagnostics = []
        if not stripped or stripped.startswith("#"):
            return diagnostics
        doc_number = self.extract_doc_number(Path(rel_path))
        reported_terms = set()
        for candidate in self.definition_sentence_candidates(stripped):
            for match in INDEX_DEFINITION_SENTENCE_RE.finditer(candidate):
                term = match.group(1).strip("`：:、（）() ")
                if term in reported_terms:
                    continue
                if not term or term in INDEX_DEFINITION_WHITELIST_TERMS or term not in INDEX_GOVERNED_TERMS:
                    continue
                if doc_number in INDEX_ALLOWED_DEFINITION_OWNERS.get(term, set()):
                    continue
                reported_terms.add(term)
                diagnostics.append(
                    self.diagnostic(
                        rel_path,
                        line_number,
                        "warning",
                        "POSSIBLE_DUPLICATE_TERM_DEFINITION",
                        f"非 02 术语规范疑似使用定义句式: {term}",
                    )
                )
        return diagnostics


    def definition_sentence_candidates(self, stripped):
        if not stripped:
            return []
        if stripped.startswith(">"):
            match = INDEX_HEADER_FIELD_RE.match(stripped)
            if match:
                return [match.group(2).strip()]
            return [stripped.lstrip("> ").strip()]
        if stripped.startswith("|"):
            cells = [self.clean_cell(cell) for cell in stripped.strip("|").split("|")]
            return [cell for cell in cells if cell and not all(char in "-: " for char in cell)]
        footnote = INDEX_FOOTNOTE_RE.match(stripped)
        if footnote:
            return [footnote.group(1).strip()]
        return [stripped]


    def diagnose_cross_document(self, docs, relations):
        diagnostics = []
        docs_by_path = {doc["path"]: doc for doc in docs}
        for doc in docs:
            related_specs = doc.get("related_specs") or []
            rel_path = doc.get("path")
            for target in related_specs:
                target_path = self.relative_path(self.resolve_target_path(target, self.root / rel_path))
                header_text = " | ".join(str(doc.get("header", {}).get(field, "")) for field in ("定位", "适用范围", "相关规范"))
                if target_path in docs_by_path and any(term in header_text for term in INDEX_REVERSE_RELATED_TERMS) and not self.has_body_reference(relations, rel_path, target_path):
                    diagnostics.append(
                        self.diagnostic(
                            rel_path,
                            1,
                            "warning",
                            "POSSIBLE_REVERSE_RELATED_SPEC",
                            f"相关规范可能基于反向、追溯或可发现性理由登记: {target_path}",
                        )
                    )
        return diagnostics


    def has_body_reference(self, relations, source_path, target_path):
        for relation in relations:
            if relation.get("source_path") != source_path:
                continue
            if relation.get("target_path") != target_path:
                continue
            if relation.get("relation_kind") == "path_ref" and relation.get("parse_method") == "body_path":
                return True
        return False

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
            target = match.group(1)
            if not self.is_environment_or_template_path(target):
                paths.append(target)
        for match in INDEX_PLAIN_SPECS_MD_RE.finditer(text):
            target = match.group(1)
            if not self.is_environment_or_template_path(target):
                paths.append(target)
        return sorted(set(paths), key=paths.index)

    def is_environment_or_template_path(self, raw_path):
        raw = str(raw_path).strip()
        return raw.startswith(("~/", "<", ".trae", ".codex")) or raw in {"AGENTS.md", "CLAUDE.md"}

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
        if raw.startswith("specs/") or raw.startswith("docs/") or raw.startswith("code/docs/"):
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
        doc_number = self.extract_doc_number(path)
        if header.get("所属主文档") or (doc_number and "." in doc_number and parts[0] == "specs"):
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
    if not checker.specs_dir.exists() and specs_dir == "specs":
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
        return "specs"
    resolved_dirs = []
    for raw_path in paths:
        path = Path(raw_path)
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if rel.parts[:2] == ("docs", "specs"):
            resolved_dirs.append("specs")
        elif rel.parts:
            resolved_dirs.append(rel.parts[0])
    if resolved_dirs and all(item == "specs" for item in resolved_dirs):
        return "specs"
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
    landing_parser = subparsers.add_parser("landing", help="检查 specs 正式规范的规范落地要求表。")
    landing_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")

    # landing-report
    landing_report_parser = subparsers.add_parser("landing-report", help="生成 specs 规范落地要求聚合报告。")
    landing_report_parser.add_argument("paths", nargs="*", default=None, help="要聚合的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")
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

    # deployment-entries
    deployment_entries_parser = subparsers.add_parser("deployment-entries", help="检查 LDVH 能力资产与 04.02 定义是否一致。")
    deployment_entries_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")

    # human-gate
    human_gate_parser = subparsers.add_parser("human-gate", help="检查 Markdown 中的 Human Gate 记录是否符合 06 最小证据结构。")
    human_gate_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/ 和 ldvh-base/。")

    # human-gate-report
    human_gate_report_parser = subparsers.add_parser("human-gate-report", help="生成 Human Gate 证据结构派生报告。")
    human_gate_report_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/ 和 ldvh-base/。")
    human_gate_report_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # consistency
    consistency_parser = subparsers.add_parser("consistency", help="检查集合状态消费、工作模型骨架和 02 术语状态一致性。")
    consistency_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/。")

    # governed-projects
    governed_projects_parser = subparsers.add_parser("governed-projects", help="检查工作区根目录管辖项目配置。")
    governed_projects_parser.add_argument("--root", default=str(PROJECT_ROOT), help="工作区根目录，默认使用当前工具所在项目。")

    # index
    index_parser = subparsers.add_parser("index", help="生成 specs 文档派生索引和诊断结果（03.01 规范文档剖面）。")
    index_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")
    index_parser.add_argument("--specs-dir", default="specs", help="要生成索引的规范目录，默认 specs。")
    index_parser.add_argument("--out", default=None, help="输出目录；未提供时将完整索引输出到 stdout。")
    index_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态。")

    # all
    all_parser = subparsers.add_parser("all", help="运行所有检查（doc + refs + landing + human-gate + index）。")
    all_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/。")
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

    if command == "deployment-entries":
        return deployment_entries_main(args.root)

    if command == "human-gate":
        return human_gate_main(args.paths)

    if command == "human-gate-report":
        return human_gate_report_main(args.paths, args.format)

    if command == "consistency":
        return consistency_main(args.paths)

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
        # deployment-entries
        if deployment_entries_main(args.root) != 0:
            exit_code = 1
        # consistency
        consistency_paths = args.paths if args.paths else [str(SPECS_DIR)]
        if consistency_main(consistency_paths) != 0:
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
