"""Specs semantic consistency checks for LDVH."""

import re
from pathlib import Path

from .common import HEADING_RE, Issue, iter_markdown_files
from . import assurance as assurance_checks
from .index import SpecsChecker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = PROJECT_ROOT / "specs"


def sync_assurance_config():
    assurance_checks.PROJECT_ROOT = PROJECT_ROOT
    assurance_checks.FORMAL_SPECS_DIR = SPECS_DIR


def assurance_is_formal_spec(path):
    sync_assurance_config()
    return assurance_checks.is_formal_spec(path)


CONSISTENCY_WORK_MODEL_REQUIRED_SECTIONS = {
    "1": "对象定位与准入条件",
    "2": "事实源边界",
    "3": "状态机",
    "4": "对象关系",
    "5": "Human Gate",
    "6": "字段契约",
    "7": "事实源回写与证据留存",
    "8": "适配边界",
    "9": "规范保障要求",
    "10": "检查要求",
    "11": "待补齐事项",
}
CONSISTENCY_NEGATIVE_TERMS = ("不得", "不应", "不能", "不可", "不是", "不具备", "不再", "已退回", "候选", "历史", "removed", "取消", "不作为", "待重新设计")
CONSISTENCY_DANGEROUS_TERMS = ("active", "统一流程", "默认流程", "默认保障机制", "可执行入口", "默认对象", "独立工作模型", "当前权威工作流程入口")
CONSISTENCY_RETIRED_REFERENCE_RULES = (
    {
        "aliases": ("42 LDVH 部署与适配检查", "42 LDVH部署与适配检查", "42 检查流程", "LDVH部署与适配检查"),
        "dangerous_terms": ("上位口径", "流程消费", "消费", "应读取", "读取本文", "输入", "默认保障机制", "可执行入口"),
        "code": "RETIRED_WORKFLOW_CONSUMPTION",
        "message": "已退回工作流程疑似仍被作为当前消费入口、输入或上位口径",
    },
    {
        "aliases": ("运行闭环测试机制", "11 定义"),
        "dangerous_terms": ("测试事实源", "测试用例事实源", "11 定义", "正式规范", "前置约束"),
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
    "04-规范保障与环境适配基础规范.md": "规范保障与环境适配基础规范",
    "04.01-规范保障声明规范.md": "规范保障声明规范",
    "04.02-LDVH能力资产与保障机制规范.md": "LDVH 能力资产与保障机制规范",
    "04.03-环境入口适配与部署规范.md": "环境入口适配与部署规范",
}
CONSISTENCY_04_SERIES_ORDER = list(CONSISTENCY_04_SERIES_FILES.keys())
CONSISTENCY_04_REQUIRED_TAIL = ["规范保障要求", "Human Gate 与检查要求", "待补齐事项"]
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
                    "04 系列章节尾部应依次为：规范保障要求、Human Gate 与检查要求、待补齐事项",
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
    "13": "规范保障要求",
    "14": "检查要求",
    "15": "待补齐事项",
}

# 索引文档的强制章节（来自原 03.02-索引文档规范 §7，不得省略的章节；该规范已由 ADR-0007 删除，但索引文档如存在仍需满足此骨架）
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
    "机制混同关系": "规范保障要求 + LDVH 能力保障 + 环境适配",
    "机制承接关系": "规范保障要求 + LDVH 能力保障 + 环境适配",
    "输入材料": "参考与研究材料",
    "待补齐项": "待补齐事项",
}

CONSISTENCY_INDEX_OVERRUN_KEYWORDS = ("字段契约", "状态机", "Scenario", "Gate 触发条件", "执行流程", "事实源回写", "对象关系")
CONSISTENCY_INDEX_FILE_RE = re.compile(r"^(20-事实模型集合索引|40-行动编排集合索引)\.md$")
CONSISTENCY_DEPRECATED_INDEX_FILE_NAMES = {"20-事实模型集合索引.md", "40-行动编排集合索引.md"}
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
        if consistency_is_current_deprecated_index(path):
            continue
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
        if number < 20 or number > 39:
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
                issues.append(Issue(path, 1, f"工作模型缺少 03.02 强制章节: ## {section_number}. {expected_title}", code="WORK_MODEL_SECTION_MISSING"))
            elif actual["title"] != expected_title:
                issues.append(
                    Issue(
                        path,
                        actual["line"],
                        f"工作模型章节标题不符合 03.02: ## {section_number}. {actual['title']}，应为 ## {section_number}. {expected_title}",
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
        if path.name in {"20-事实模型集合索引.md", "40-行动编排集合索引.md"}:
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
    """检查工作流程文档是否覆盖 03.03 规定的强制章节"""
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
                issues.append(Issue(path, 1, f"工作流程缺少 03.03 强制章节: ## {section_number}. {expected_title}", code="WORKFLOW_SECTION_MISSING"))
            elif actual["title"] != expected_title:
                issues.append(
                    Issue(
                        path,
                        actual["line"],
                        f"工作流程章节标题不符合 03.03: ## {section_number}. {actual['title']}，应为 ## {section_number}. {expected_title}",
                        code="WORKFLOW_SECTION_TITLE_MISMATCH",
                    )
                )
    return issues


def consistency_index_skeleton_issues(paths):
    """检查旧 20 和 40 索引文档是否覆盖原 03.02 规定的强制章节"""
    issues = []
    # 从传入路径中查找索引文档，同时保留 SPECS_DIR 作为后备
    index_files = []
    for p in iter_markdown_files(paths):
        if consistency_is_current_deprecated_index(p):
            continue
        if CONSISTENCY_INDEX_FILE_RE.match(Path(p).name):
            index_files.append(Path(p))
    # 也检查 SPECS_DIR
    for f in SPECS_DIR.glob("*.md"):
        if consistency_is_current_deprecated_index(f):
            continue
        if CONSISTENCY_INDEX_FILE_RE.match(f.name) and f not in index_files:
            index_files.append(f)
    for path in index_files:
        sections = consistency_h2_sections(path)
        for section_number, expected_title in CONSISTENCY_INDEX_REQUIRED_SECTIONS.items():
            actual = sections.get(section_number)
            if actual is None:
                issues.append(Issue(path, 1, f"索引文档缺少原 03.02 强制章节: ## {section_number}. {expected_title}", code="INDEX_SECTION_MISSING"))
    return issues


def consistency_is_current_deprecated_index(path):
    path = Path(path)
    if path.name not in CONSISTENCY_DEPRECATED_INDEX_FILE_NAMES or path.parent.resolve() != SPECS_DIR.resolve():
        return False
    title = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return "迁移待删除" in title


def consistency_human_gate_check_section_issues(paths):
    issues = []
    for path in iter_markdown_files(paths):
        if not assurance_is_formal_spec(path):
            continue
        sections = consistency_h2_sections(path)
        titles = {section["title"] for section in sections.values()}
        if "规范保障要求" not in titles:
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
    issues = []
    checker = SpecsChecker(PROJECT_ROOT)
    model_entries = checker.members_as_collection_entries("work_model")
    workflow_entries = checker.members_as_collection_entries("work_process")
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
