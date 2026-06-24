"""Assurance requirement aggregate report checks for LDVH specs."""

import json
import re
from datetime import datetime
from pathlib import Path

from .common import iter_markdown_files
from . import human_gate as human_gate_checks
from . import assurance as assurance_checks
from . import runtime_projection as runtime_projection_checks


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORMAL_SPECS_DIR = PROJECT_ROOT / "specs"
DOCS_DIR = PROJECT_ROOT / "docs"
RUNTIME_PROJECTION_DEFAULT_PATHS = list(runtime_projection_checks.RUNTIME_PROJECTION_DEFAULT_PATHS)


def sync_runtime_projection_config():
    runtime_projection_checks.PROJECT_ROOT = PROJECT_ROOT
    runtime_projection_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    runtime_projection_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def runtime_projection_report_build(paths=None):
    sync_runtime_projection_config()
    return runtime_projection_checks.report_build(paths)


def sync_human_gate_config():
    human_gate_checks.PROJECT_ROOT = PROJECT_ROOT
    human_gate_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    human_gate_checks.DOCS_DIR = DOCS_DIR


def human_gate_report_build(paths=None):
    sync_human_gate_config()
    return human_gate_checks.report_build(paths)


ASSURANCE_SECTION_TITLE = assurance_checks.ASSURANCE_SECTION_TITLE
ASSURANCE_REQUIRED_COLUMNS = assurance_checks.ASSURANCE_REQUIRED_COLUMNS
ASSURANCE_ALLOWED_TYPES = assurance_checks.ASSURANCE_ALLOWED_TYPES


def sync_assurance_config():
    assurance_checks.PROJECT_ROOT = PROJECT_ROOT
    assurance_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR


ASSURANCE_REPORT_OWNER_AREAS = {
    "上位约束承接要求": "specs",
    "入口可见要求": "runtime_projection",
    "流程复用要求": "workflow",
    "工作流程接管要求": "workflow",
    "子 Agent 思考要求": "agent",
    "确定性执行要求": "code",
    "Human 交互要求": "human_gate",
    "生命周期触发要求": "runtime_projection",
}
ASSURANCE_REPORT_AREA_LABELS = {
    "agent": "Agent",
    "code": "Code / Test",
    "human_gate": "Human Gate",
    "runtime_projection": "运行投影",
    "specs": "Specs",
    "unknown": "未知",
    "workflow": "Workflow / Skill",
}
ASSURANCE_REPORT_WRITEBACK_AREAS = {
    "specs": "specs",
    "runtime_projection": "runtime_projection_or_env_record",
    "workflow": "workflow_or_skill_candidate",
    "agent": "agent_or_44",
    "code": "code_request_or_test",
    "human_gate": "human_gate_record",
}
ASSURANCE_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS = {
    "decision_record_required": "必须人类决策记录",
    "policy_clarification": "规范口径说明",
    "implementation_support": "承接实现支持",
    "diagnostic_coverage": "Code 覆盖诊断",
}
ASSURANCE_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS = {
    "current_record_required": "当前需要记录",
    "future_trigger_record": "未来触发时记录",
    "rule_condition_only": "只保留为规则条件",
}
ASSURANCE_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS = {
    "future_evaluation": "未来触发时评估",
    "workflow_design_discussion": "流程创建前讨论",
}
ASSURANCE_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS = {
    "web_human_facing_support": "Web / Human-facing 承接",
}
ASSURANCE_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS = {
    "coverage_limited": "覆盖范围受限",
}
ASSURANCE_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS = {
    "lifecycle_trigger_sync": "生命周期触发同步",
    "platform_capability_sync": "平台能力承接同步",
    "projection_coverage_diagnostic": "投影覆盖诊断受限",
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
ASSURANCE_REPORT_HUMAN_GATE_DECISION_TERMS = [
    "接受长期风险",
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
    "受限",
]
ASSURANCE_REPORT_HUMAN_GATE_POLICY_TERMS = [
    "评估 Human Gate",
    "应评估 Human Gate",
    "应先讨论",
    "讨论是否",
]
ASSURANCE_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS = [
    "应先讨论",
    "讨论是否",
]
ASSURANCE_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS = [
    "Human Gate UI",
    "展示确认对象",
    "承接 06 §6.3.1",
]
ASSURANCE_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS = [
    "当前已",
    "本次已",
    "已现场确认",
    "已接受长期风险",
    "已判定 LDVH部署与适配检查闭环",
    "已声明 Human",
]
ASSURANCE_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS = [
    "前",
    "时",
    "发生",
    "变化",
    "用户请求",
    "任一",
    "§",
    "从候选项创建",
]
ASSURANCE_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS = [
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
ASSURANCE_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS = [
    "第三方 Skill",
    "包装 Skill",
]
ASSURANCE_REPORT_LEGACY_DEGRADED_MARKERS = [
    "open-degraded",
    "degraded",
    "人工降级",
    "降级原因",
    "降级说明",
    "降级方式",
    "记录降级",
]
ASSURANCE_REPORT_LIMITED_MARKERS = [
    "受限说明",
    "受限方式",
    "输出受限",
    "能力受限",
    "覆盖受限",
]
ASSURANCE_REPORT_OPEN_MARKERS = [
    "TODO",
    "待补齐",
    "待创建",
    "待讨论",
    "待实现",
    "尚未",
    "未稳定",
    "未完成",
    "open item",
]
ASSURANCE_REPORT_OPEN_PATTERNS = [
    re.compile(r"后续[^|。；;]*?(补齐|扩展|创建|讨论|稳定|校准|补充|形成|沉淀)"),
    re.compile(r"(需要|需|应)[^|。；;]*?(补齐|扩展|创建|讨论|稳定|校准|形成缺口)"),
    re.compile(r"缺口[^|。；;]*?(待|未|open)"),
]
ASSURANCE_REPORT_HUMAN_GATE_PATTERNS = [
    re.compile(r"(必须|应|需|需要|触发|进入|经|通过|完成)[^|。；;]*?Human Gate"),
    re.compile(r"Human Gate[^|。；;]*?(确认|前|后|授权|暂停|等待)"),
]
ASSURANCE_REPORT_CAPABILITY_CHECKS = [
    {
        "id": "41_trigger_safeguard",
        "capability": "41 触发保障",
        "status": "capability_gap",
        "owner_area": "code",
        "required_terms": ["41", "触发保障"],
        "missing_reason": "assurance-report 未发现 41 触发保障声明，无法判断正式规范或运行投影变化是否应进入 41",
        "limited_reason": "assurance-report 只能聚合 41 触发保障要求，尚不能验证所有触发场景是否实际进入 41",
        "suggested_writeback": "code_request_or_test",
    },
    {
        "id": "42_consumes_41",
        "capability": "42 消费 41 触发状态",
        "status": "capability_gap",
        "owner_area": "workflow",
        "required_terms": ["42", "41", "消费"],
        "missing_reason": "assurance-report 未发现 42 消费 41 触发状态声明，无法作为 LDVH部署与适配检查输入",
        "limited_reason": "assurance-report 能暴露 41/42 联动要求，但尚不能证明 42 现场检查已经消费本次报告",
        "suggested_writeback": "workflow_or_skill_candidate",
    },
    {
        "id": "runtime_projection_drift_check",
        "capability": "运行投影漂移检查",
        "status": "open",
        "owner_area": "runtime_projection",
        "required_terms": ["运行投影", "漂移检查"],
        "missing_reason": "assurance-report 未发现运行投影漂移检查声明，无法诊断入口、Skill、Hook、CI、Web 或 Code 投影漂移",
        "limited_reason": "assurance-report 只能识别运行投影漂移检查要求，尚不能读取真实运行投影并比对正式规范",
        "suggested_writeback": "runtime_projection_or_env_record",
    },
    {
        "id": "human_gate_evidence_consumption",
        "capability": "Human Gate 证据消费",
        "status": "evidence_gap",
        "owner_area": "human_gate",
        "required_terms": ["Human Gate", "证据"],
        "missing_reason": "assurance-report 未发现 Human Gate 证据消费声明，无法支持关闭或通过声明",
        "limited_reason": "assurance-report 能识别 Human Gate 证据消费要求，但尚未把 Human Gate 记录校验结果并入状态判断",
        "suggested_writeback": "human_gate_record",
    },
]


def assurance_default_check_paths():
    sync_assurance_config()
    return assurance_checks.default_check_paths()


def assurance_is_formal_spec(path):
    sync_assurance_config()
    return assurance_checks.is_formal_spec(path)


def assurance_strip_section_number(title):
    return assurance_checks.strip_section_number(title)


def assurance_split_cells(line):
    return assurance_checks.split_cells(line)


def assurance_is_separator(cells):
    return assurance_checks.is_separator(cells)


def assurance_clean_cell(value):
    return assurance_checks.clean_cell(value)


def assurance_relative_path(path):
    sync_assurance_config()
    return assurance_checks.assurance_relative_path(path)


def assurance_extract_requirements_file(path):
    sync_assurance_config()
    return assurance_checks.extract_requirements_file(path)


def assurance_report_match_marker(text, markers):
    for marker in markers:
        if marker in text:
            return marker
    return None


def assurance_report_infer_status(requirement):
    text = " | ".join(
        [
            requirement.get("requirement_type", ""),
            requirement.get("content", ""),
            requirement.get("guarantee_mechanism", ""),
            requirement.get("sync_type", ""),
            requirement.get("trigger", ""),
        ]
    )

    marker = assurance_report_match_marker(text, ASSURANCE_REPORT_LIMITED_MARKERS)
    if marker:
        return "limited", f"matched limited marker: {marker}"

    marker = assurance_report_match_marker(text, ASSURANCE_REPORT_LEGACY_DEGRADED_MARKERS)
    if marker:
        return "limited", f"matched legacy compatibility marker: {marker}"

    marker = assurance_report_match_marker(text, ASSURANCE_REPORT_OPEN_MARKERS)
    if marker:
        return "open", f"matched open marker: {marker}"

    for pattern in ASSURANCE_REPORT_OPEN_PATTERNS:
        match = pattern.search(text)
        if match:
            return "open", f"matched open pattern: {match.group(0)}"

    for pattern in ASSURANCE_REPORT_HUMAN_GATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return "needs_human_gate", f"matched Human Gate pattern: {match.group(0)}"

    return "closed", "no open/legacy limited/Human Gate marker matched"


def assurance_report_count_by(requirements, key):
    counts = {}
    for requirement in requirements:
        value = requirement.get(key) or "(empty)"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def assurance_report_is_gap(item):
    return item.get("status") != "closed"


def assurance_report_human_gate_subcategory(item):
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
    if any(term in text for term in ASSURANCE_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS):
        return "implementation_support"
    if any(term in text for term in ASSURANCE_REPORT_HUMAN_GATE_POLICY_TERMS):
        return "policy_clarification"
    if any(term in text for term in ASSURANCE_REPORT_HUMAN_GATE_DECISION_TERMS):
        return "decision_record_required"
    return "policy_clarification"


def assurance_report_human_gate_decision_flow(item):
    text = " | ".join(
        [
            item.get("content", ""),
            item.get("guarantee_mechanism", ""),
            item.get("sync_type", ""),
            item.get("trigger", ""),
            item.get("status_reason", ""),
        ]
    )
    if any(term in text for term in ASSURANCE_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS):
        return "current_record_required"
    if any(term in text for term in ASSURANCE_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS):
        return "future_trigger_record"
    return "rule_condition_only"


def assurance_report_human_gate_policy_flow(item):
    text = " | ".join(
        [
            item.get("content", ""),
            item.get("guarantee_mechanism", ""),
            item.get("sync_type", ""),
            item.get("trigger", ""),
            item.get("status_reason", ""),
        ]
    )
    if any(term in text for term in ASSURANCE_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS):
        return "workflow_design_discussion"
    return "future_evaluation"


def assurance_report_human_gate_support_flow(item):
    return "web_human_facing_support"


def assurance_report_human_gate_diagnostic_flow(item):
    return "coverage_limited"


def assurance_report_runtime_projection_subcategory(item):
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
    if any(term in text for term in ASSURANCE_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS):
        return "third_party_skill_projection"
    if any(term in text for term in ASSURANCE_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS):
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


def assurance_report_build_gap_categories(requirements, capability_gaps):
    categories = {}
    for item in list(requirements) + list(capability_gaps):
        if not assurance_report_is_gap(item):
            continue
        owner_area = item.get("owner_area") or "unknown"
        if owner_area not in categories:
            categories[owner_area] = {
                "owner_area": owner_area,
                "label": ASSURANCE_REPORT_AREA_LABELS.get(owner_area, owner_area),
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
            "title": assurance_report_shorten(title, 120),
            "suggested_writeback": suggested_writeback,
        }
        if len(category["examples"]) < 3:
            category["examples"].append(example)
        if owner_area == "human_gate":
            subcategory_key = assurance_report_human_gate_subcategory(item)
            subcategories = category["subcategories"]
            if subcategory_key not in subcategories:
                subcategories[subcategory_key] = {
                    "id": subcategory_key,
                    "label": ASSURANCE_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS.get(subcategory_key, subcategory_key),
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
                flow_key = assurance_report_human_gate_decision_flow(item)
                decision_flows = subcategory["decision_flows"]
                if flow_key not in decision_flows:
                    decision_flows[flow_key] = {
                        "id": flow_key,
                        "label": ASSURANCE_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS.get(flow_key, flow_key),
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
                flow_key = assurance_report_human_gate_policy_flow(item)
                policy_flows = subcategory["policy_flows"]
                if flow_key not in policy_flows:
                    policy_flows[flow_key] = {
                        "id": flow_key,
                        "label": ASSURANCE_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS.get(flow_key, flow_key),
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
                flow_key = assurance_report_human_gate_support_flow(item)
                support_flows = subcategory["support_flows"]
                if flow_key not in support_flows:
                    support_flows[flow_key] = {
                        "id": flow_key,
                        "label": ASSURANCE_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS.get(flow_key, flow_key),
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
                flow_key = assurance_report_human_gate_diagnostic_flow(item)
                diagnostic_flows = subcategory["diagnostic_flows"]
                if flow_key not in diagnostic_flows:
                    diagnostic_flows[flow_key] = {
                        "id": flow_key,
                        "label": ASSURANCE_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS.get(flow_key, flow_key),
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
            subcategory_key = assurance_report_runtime_projection_subcategory(item)
            subcategories = category["subcategories"]
            if subcategory_key not in subcategories:
                subcategories[subcategory_key] = {
                    "id": subcategory_key,
                    "label": ASSURANCE_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS.get(subcategory_key, subcategory_key),
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


def assurance_report_document_text(paths):
    parts = []
    for path in paths:
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def assurance_report_terms_present(text, terms):
    return all(term in text for term in terms)


def assurance_report_member_status(text, spec_id, kind):
    for match in re.finditer(r"```ya?ml\s*\n(.*?\n)```", text, re.DOTALL):
        block = match.group(1)
        if "ldvh_member:" not in block:
            continue
        if not re.search(rf"^\s*spec_id:\s*[\"']?{re.escape(spec_id)}[\"']?\s*$", block, re.MULTILINE):
            continue
        if not re.search(rf"^\s*kind:\s*{re.escape(kind)}\s*$", block, re.MULTILINE):
            continue
        status_match = re.search(r"^\s*collection_status:\s*([A-Za-z0-9_-]+)\s*$", block, re.MULTILINE)
        return status_match.group(1) if status_match else ""
    return None


def assurance_report_build_capability_gaps(formal_files, runtime_projection_report=None, human_gate_report=None):
    text = assurance_report_document_text(formal_files)
    gaps = []

    for check in ASSURANCE_REPORT_CAPABILITY_CHECKS:
        terms_present = assurance_report_terms_present(text, check["required_terms"])
        status = check["status"] if terms_present else "open"
        reason = check["limited_reason"] if terms_present else check["missing_reason"]
        evidence = "matched formal spec terms" if terms_present else "required terms missing from formal specs"
        if check["id"] == "41_trigger_safeguard":
            status_40 = assurance_report_member_status(text, "40", "work_process")
            status_41 = assurance_report_member_status(text, "41", "work_process")
            evidence = f"workflow 40 status={status_40 or 'missing'}; workflow 41 status={status_41 or 'missing'}"
            if status_41 == "active":
                status = "capability_gap" if terms_present else "open"
                reason = "41 已是 active 工作流程，但 assurance-report 仍只能诊断成员状态，尚不能验证所有触发场景是否实际进入 41"
            elif status_41:
                status = "capability_gap"
                reason = f"41 当前 collection_status={status_41}，assurance-report 已接入成员状态诊断，但候选流程仍不得被当作 active 触发保障"
            else:
                status = "open"
                reason = "assurance-report 未发现 41 工作流程成员自描述，无法提供 41 触发保障成员状态诊断"
        if check["id"] == "runtime_projection_drift_check" and runtime_projection_report is not None:
            runtime_status = runtime_projection_report["summary"]["status"]
            runtime_issue_count = runtime_projection_report["metadata"]["issue_count"]
            runtime_file_count = runtime_projection_report["metadata"]["checked_file_count"]
            evidence = f"runtime-projection checked {runtime_file_count} project-local files, issues: {runtime_issue_count}, status: {runtime_status}"
            if runtime_status == "open":
                status = "open"
                reason = "runtime-projection 检查发现 open 漂移问题，assurance-report 已接入该诊断"
            elif runtime_status in {"limited", "evidence_gap", "fact_conflict"}:
                status = runtime_status
                reason = f"runtime-projection 检查发现 {runtime_status} 受限或证据问题，assurance-report 已接入该诊断"
            elif terms_present:
                status = "evidence_gap"
                reason = "runtime-projection 检查当前未发现项目内问题，但仍是项目局部启发式，尚不能证明所有运行投影完整覆盖"
        if check["id"] == "human_gate_evidence_consumption" and human_gate_report is not None:
            gate_status = human_gate_report["summary"]["status"]
            gate_issue_count = human_gate_report["metadata"]["issue_count"]
            gate_record_count = human_gate_report["metadata"]["record_count"]
            gate_file_count = human_gate_report["metadata"]["checked_file_count"]
            evidence = f"human-gate checked {gate_file_count} project-local files, records: {gate_record_count}, issues: {gate_issue_count}, status: {gate_status}"
            if gate_status == "open":
                status = "open"
                reason = "human-gate 检查发现 open 证据结构问题，assurance-report 已接入该诊断"
            elif gate_status in {"evidence_gap", "needs_human_gate"}:
                status = gate_status
                reason = f"human-gate 检查发现 {gate_status} 证据状态，assurance-report 已接入该诊断"
            elif terms_present:
                status = "evidence_gap"
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


def assurance_report_build(paths=None):
    check_paths = paths if paths else assurance_default_check_paths()
    markdown_files = iter_markdown_files(check_paths)
    formal_files = [path for path in markdown_files if assurance_is_formal_spec(path)]
    requirements = []
    for path in formal_files:
        requirements.extend(assurance_extract_requirements_file(path))
    runtime_projection_report = runtime_projection_report_build()
    human_gate_report = human_gate_report_build()
    capability_gaps = assurance_report_build_capability_gaps(formal_files, runtime_projection_report, human_gate_report)

    for requirement in requirements:
        status, reason = assurance_report_infer_status(requirement)
        owner_area = ASSURANCE_REPORT_OWNER_AREAS.get(requirement["requirement_type"], "unknown")
        requirement["status"] = status
        requirement["status_reason"] = reason
        requirement["owner_area"] = owner_area
        requirement["suggested_writeback"] = ASSURANCE_REPORT_WRITEBACK_AREAS.get(owner_area, "manual_review")

    source_files = sorted({requirement["source"] for requirement in requirements})
    gap_categories = assurance_report_build_gap_categories(requirements, capability_gaps)
    return {
        "metadata": {
            "tool": "code/specs_validate.py",
            "report": "assurance-report",
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
            "by_status": assurance_report_count_by(requirements, "status"),
            "by_capability_status": assurance_report_count_by(capability_gaps, "status"),
            "gap_total": sum(category["total"] for category in gap_categories.values()),
            "gap_by_owner_area": {area: category["total"] for area, category in gap_categories.items()},
            "runtime_projection_status": runtime_projection_report["summary"]["status"],
            "runtime_projection_by_status": runtime_projection_report["summary"]["by_status"],
            "human_gate_status": human_gate_report["summary"]["status"],
            "human_gate_by_status": human_gate_report["summary"]["by_status"],
            "by_type": assurance_report_count_by(requirements, "requirement_type"),
            "by_sync_type": assurance_report_count_by(requirements, "sync_type"),
            "by_owner_area": assurance_report_count_by(requirements, "owner_area"),
        },
        "requirements": requirements,
        "capability_gaps": capability_gaps,
        "gap_categories": gap_categories,
        "runtime_projection": runtime_projection_report,
        "human_gate": human_gate_report,
    }


def assurance_report_shorten(text, limit=96):
    text = str(text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def assurance_report_format_text(report):
    lines = ["规范保障要求聚合报告"]
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
        ("按保障要求类型", "by_type"),
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
            content = assurance_report_shorten(item["content"])
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


def assurance_report_main(paths=None, output_format="text"):
    report = assurance_report_build(paths)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(assurance_report_format_text(report))
    return 0
