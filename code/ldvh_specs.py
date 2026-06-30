from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]

TIMING_TABLE_PATH = "specs/attachments/01.Att.01-保障消费时机表.md"
TAKEOVER_MATRIX_PATH = "specs/attachments/01.Att.06-保障机制承接矩阵.md"
AI_BEHAVIOR_SPEC_PATH = "specs/02-AI行为规范.md"
COMMIT_MESSAGE_CONTRACT_PATH = "specs/attachments/03.Att.01-Commit-Message契约字段表.md"
FIELD_REGISTRY_CONTRACT_PATH = "specs/attachments/05.Att.01-字段注册表结构.md"
VERIFICATION_CLAIM_FIELDS_PATH = "specs/attachments/09.Att.01-验证声明字段表.md"

SHORT_SPEC_REFS = {
    "00": "specs/00-理念与构成.md",
    "01": "specs/01-保障与衔接.md",
    "02": "specs/02-AI行为规范.md",
    "03": "specs/03-事实源与Git溯源规范.md",
    "04": "specs/04-Specs基础规范.md",
    "05": "specs/05-事实模型基础规范.md",
    "06": "specs/06-行动模板基础规范.md",
    "07": "specs/07-Code确定性执行规范.md",
    "08": "specs/08-Web信息同步规范.md",
    "09": "specs/09-测试与验证规范.md",
    "21": "specs/21-WorkCase-工作项.md",
}
BASE_ACTION_GUIDE_SOURCE_REFS = [
    {"path": "specs/00-理念与构成.md", "role": "value_anchor"},
    {"path": "specs/01-保障与衔接.md", "role": "action_guide_contract"},
    {"path": "specs/02-AI行为规范.md", "role": "ai_behavior_requirements"},
    {"path": TIMING_TABLE_PATH, "role": "consumption_timing_registry"},
    {"path": TAKEOVER_MATRIX_PATH, "role": "takeover_matrix"},
]
PREFLIGHT_BASE_READ_PATHS = [
    "specs/00-理念与构成.md",
    "specs/01-保障与衔接.md",
    "specs/02-AI行为规范.md",
    "specs/03-事实源与Git溯源规范.md",
    "specs/04-Specs基础规范.md",
]
PREFLIGHT_TYPE_READ_PATHS = {
    "code": [
        "specs/07-Code确定性执行规范.md",
        "specs/09-测试与验证规范.md",
    ],
    "tests": [
        "specs/09-测试与验证规范.md",
        "specs/07-Code确定性执行规范.md",
    ],
}
HIGH_IMPACT_SPEC_PATHS = {
    "specs/00-理念与构成.md",
    "specs/01-保障与衔接.md",
    "specs/02-AI行为规范.md",
    "specs/03-事实源与Git溯源规范.md",
    "specs/04-Specs基础规范.md",
}
RUNTIME_REQUIRED_ENTRY_PATHS = [
    "specs/00-理念与构成.md",
    "specs/01-保障与衔接.md",
    "specs/02-AI行为规范.md",
]

SPEC_REQUIRED_KEYS = {
    "spec_id",
    "spec_kind",
    "title",
    "status",
    "authority",
    "canonical_path",
    "parent_spec",
    "relation",
    "positioning",
    "scope",
    "basis",
    "related_specs",
    "code_consumption",
}
ATTACHMENT_REQUIRED_KEYS = {
    "attachment_id",
    "title",
    "status",
    "canonical_path",
    "parent_spec",
    "relation",
}
AI_BEHAVIOR_COLUMNS = [
    "需求ID",
    "保障需求",
    "消费时机",
    "必读依据",
    "所需能力",
    "完成证据",
    "阻断条件",
    "缺口分流",
]
TIMING_COLUMNS = ["消费时机", "触发点", "消费主体", "用途"]
TAKEOVER_COLUMNS = ["需求ID", "触发消费时机", "行动指南承接", "Hook 承接"]
COMMIT_MESSAGE_FIELD_COLUMNS = ["字段", "要求", "说明"]
COMMIT_TYPE_COLUMNS = ["type", "简体中文", "English", "含义"]
COMMIT_SCOPE_COLUMNS = ["scope", "简体中文", "English", "含义"]
COMMIT_BODY_CONDITION_COLUMNS = ["条件类型", "条件"]
FIELD_REGISTRY_COLUMNS = ["列", "含义"]
FIELD_REGISTRY_ALLOWED_COLUMNS = ["注册列", "允许值或写法"]
FIELD_REGISTRY_CODE_CHECK_COLUMNS = ["code_check_kind", "可机械消费维度", "边界"]
VERIFICATION_CLAIM_COLUMNS = ["字段", "要求"]
VERIFICATION_COMPLETE_CONDITION_COLUMNS = ["条件", "内容"]
VERIFICATION_FORBIDDEN_COLUMNS = ["写法", "边界"]
ACTION_TEMPLATE_COLUMNS = ["结构", "最小要求"]
FOUNDATION_SPEC_IDS = ("03", "05", "06", "07", "08", "09")
ASSURANCE_COLUMNS = ["保障要求", "要求内容", "保障机制", "同步类型", "触发条件"]
VERIFICATION_COLUMNS = ["检查类别", "检查内容", "不满足时"]
FACT_MODEL_BOUNDARY_REQUIREMENTS = [
    {
        "code": "FACT_INSTANCE_RULE_BOUNDARY_MISSING",
        "section": "事实模型与事实实例",
        "message": "05 必须声明事实实例不得定义或重写事实模型规则",
        "terms": ["事实实例不得定义", "事实模型规则", "Human Gate"],
    },
    {
        "code": "FACT_INSTANCE_FIXTURE_BOUNDARY_MISSING",
        "section": "事实模型与事实实例",
        "message": "05 必须声明测试夹具不得被写成事实实例",
        "terms": ["测试夹具不得被写成事实实例"],
    },
    {
        "code": "FACT_INSTANCE_MIGRATION_BOUNDARY_MISSING",
        "section": "事实模型与事实实例",
        "message": "05 必须声明迁移材料不得被写成事实实例",
        "terms": ["`_migration` 迁移材料不得被写成事实实例"],
    },
    {
        "code": "FACT_OBJECT_ADMISSION_VALUE_MISSING",
        "section": "事实对象准入与分流",
        "message": "05 必须声明事实对象准入判断说明对象化价值和减少的 AI 负担",
        "terms": ["对象化价值", "减少的 AI 负担"],
    },
    {
        "code": "FACT_FIELD_TERM_BOUNDARY_MISSING",
        "section": "字段、状态与证据边界",
        "message": "05 必须声明字段名不得与术语表冲突",
        "terms": ["字段名不得", "术语表", "字段语义和术语边界"],
    },
    {
        "code": "FACT_MEMBER_MIGRATION_BOUNDARY_MISSING",
        "section": "待补齐事项",
        "message": "05 必须声明 Spark/WorkCase/ADR/Pitfall/Study 成员规范迁移判断条件",
        "terms": ["Spark", "WorkCase", "ADR", "Pitfall", "Study", "对象化价值", "Code/tests 闭环"],
    },
]
FACT_SOURCE_EVIDENCE_REQUIREMENTS = [
    {
        "code": "NON_FACT_SOURCE_EXCLUSION_MISSING",
        "path": SHORT_SPEC_REFS["03"],
        "section": "事实源边界",
        "message": "03 必须列出非事实源排除项",
        "terms": ["聊天", "Code 输出", "测试输出", "Web 页面状态", "runtime receipt", "`_migration` 材料", "Git commit records"],
    },
    {
        "code": "PROCESS_OUTPUT_QUALIFICATION_MISSING",
        "path": SHORT_SPEC_REFS["03"],
        "section": "过程输出、证据与回写",
        "message": "03 必须声明过程输出先由 AI 定性",
        "terms": ["过程输出必须先被 AI 定性"],
    },
    {
        "code": "PROCESS_OUTPUT_WRITEBACK_REQUIREMENT_MISSING",
        "path": SHORT_SPEC_REFS["03"],
        "section": "过程输出、证据与回写",
        "message": "03 必须声明过程输出回写所需字段",
        "terms": ["目标事实源", "来源证据", "采纳范围", "验证方式"],
    },
    {
        "code": "TEST_OUTPUT_FACT_SOURCE_BOUNDARY_MISSING",
        "path": SHORT_SPEC_REFS["09"],
        "section": "测试证据与同步触发",
        "message": "09 必须声明测试输出不得替代事实源",
        "terms": ["测试输出", "覆盖率", "截图", "trace", "缓存", "Mock 数据", "临时报告", "不得替代 specs、事实对象、Git 记录或 Human Gate"],
    },
    {
        "code": "FAILURE_BLOCKING_RULE_MISSING",
        "path": SHORT_SPEC_REFS["09"],
        "section": "验证声明与失败阻断",
        "message": "09 必须声明失败阻断边界",
        "terms": ["必须运行的测试失败", "关键验证未运行", "证据无法回指", "Human 验收尚未发生", "仅有工具成功输出"],
    },
]
GIT_COMMIT_ACTION_TEMPLATE_REQUIRED_ROWS = {
    "Context": ["git status", "staged", "diff", "source_refs", "03.Att.01", "09.Att.01"],
    "Scenario": ["用户明确要求提交", "修复提交消息", "拆分 staged changes", "只回答 03/09 边界"],
    "Gate": ["staged changes", "提交拆分边界不清", "destructive Git", "commit validator", "失败测试", "Human Gate", "Hook/commit gate/环境入口"],
    "执行": ["status", "diff", "拆分", "03.Att.01", "单一 type", "scope", "关键变更", "commit validator", "不安装 Hook"],
    "验证": ["测试或命令", "09.Att.01", "验证目标", "验证入口", "残留风险", "证据回指", "不得声明完整验证"],
    "回写": ["过程输出", "事实源", "事实对象", "Git commit records", "不替代事实对象或验证声明"],
    "交还": ["commit hash", "验证摘要", "残留风险", "git status", "source_refs", "执行方式", "阻断原因"],
}
GIT_COMMIT_ACTION_TEMPLATE_BOUNDARY_TERMS = [
    "Action Guide",
    "V2 知识地图",
    "不替代主控 AI 判断",
    "skill_runtime_invoked",
    "manual_equivalent_execution",
    "skill_unavailable",
    "不得恢复 Skill 顶层机制",
]
WEB_SYNC_BOUNDARY_REQUIREMENTS = [
    {
        "code": "WEB_CODE_SEPARATION_BOUNDARY_MISSING",
        "section": "同源独立读取与派生状态",
        "message": "08 必须声明 Web 和 Code 分开实现，且 Web 数据路径不依赖 Code 输出",
        "terms": ["并列实现", "不是上下游数据依赖", "页面/API 的数据路径", "不得把 Code 输出", "Code DTO", "validator 内部对象", "作为页面数据源"],
    },
    {
        "code": "WEB_DIAGNOSTIC_REFERENCE_BOUNDARY_MISSING",
        "section": "同源独立读取与派生状态",
        "message": "08 必须声明 Code 诊断只能作为 Web 对照显示和缺口定位",
        "terms": ["Code 诊断", "只能用于对照显示和缺口定位", "不得驱动页面字段契约、状态机、排序筛选语义或事实判断"],
    },
    {
        "code": "WEB_NATIVE_IMPLEMENTATION_BOUNDARY_MISSING",
        "section": "同源独立读取与派生状态",
        "message": "08 必须声明 Web 原生实现可独立读取和聚合，但必须保留来源并服从正式契约",
        "terms": ["Web 原生实现", "读取、解析、筛选、排序、聚合、缓存和提供 API", "source_refs", "不得新增第二套字段契约、状态机、规则判断或事实源归口"],
    },
]
WEB_SYNC_FORBIDDEN_PHRASES = [
    "Web 可以使用 Code 输出",
    "Code 输出作为展示辅助",
    "Code 输出喂页面数据",
]
WORKCASE_STATUS_COLUMNS = ["状态", "含义"]
WORKCASE_REQUIRED_CODE_CONSUMPTION = [
    "ldvh_spec_metadata",
    "fact_model_member_identity",
    "workcase_admission_rules",
    "workcase_source_boundaries",
    "workcase_state_boundaries",
    "workcase_closure_boundaries",
    "workcase_human_gate_boundaries",
    "workcase_instance_checks",
    "stop_conditions",
]
WORKCASE_REQUIRED_STATUSES = [
    "subagents_plan_reviewing",
    "human_plan_confirming",
    "executing",
    "result_self_checking",
    "subagents_result_reviewing",
    "human_closure_confirming",
    "closed",
]
WORKCASE_SOURCE_BOUNDARY_TERMS = [
    "ldvh-base/workcases/",
    "执行项只能作为 WorkCase 内部字段存在",
    "不得形成独立事实对象",
]
WORKCASE_CLOSURE_BOUNDARY_TERMS = [
    "执行完成",
    "可提交关闭确认",
    "已关闭",
    "已提交",
    "后续分流 / 收口结果",
]
WORKCASE_HUMAN_GATE_TERMS = [
    "创建 WorkCase",
    "human_plan_confirming",
    "human_closure_confirming",
    "跳过未验证执行项",
]
WORKCASE_LEGACY_STATUSES = ["draft", "active", "review_needed"]
FOUNDATION_SPEC_CONTRACTS = {
    "03": {
        "path": SHORT_SPEC_REFS["03"],
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "fact_source_boundaries",
            "process_evidence_boundaries",
            "git_traceability_rules",
            "commit_contract_boundaries",
            "commit_message_contract_fields",
            "source_ref_requirements",
            "stop_conditions",
        ],
        "required_rule_body_sections": [
            "5. 事实源边界",
            "6. 过程输出、证据与回写",
            "7. Git 溯源与提交契约",
        ],
        "required_assurance_rows": [
            "事实源回指要求",
            "非事实源排除要求",
            "Git 溯源要求",
            "commit 契约要求",
        ],
        "required_verification_rows": [
            "事实源边界检查",
            "非事实源排除检查",
            "回写检查",
            "Git 溯源检查",
        ],
        "human_gate_terms": ["非 Git 文件", "过程输出", "commit 契约", "Git commit records", "事实源冲突"],
        "stop_condition_terms": ["权威事实源", "过程输出", "聊天、缓存、测试输出", "commit message", "事实源不一致"],
    },
    "05": {
        "path": SHORT_SPEC_REFS["05"],
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "fact_model_boundaries",
            "fact_object_admission",
            "fact_instance_boundaries",
            "evidence_routing",
            "field_state_boundary",
            "field_registry_contract",
            "stop_conditions",
        ],
        "required_rule_body_sections": [
            "5. 事实模型与事实实例",
            "6. 事实对象准入与分流",
            "7. 字段、状态与证据边界",
        ],
        "required_assurance_rows": [
            "对象准入要求",
            "实例边界要求",
            "证据分流要求",
            "字段状态同步要求",
        ],
        "required_verification_rows": ["准入检查", "边界检查", "证据检查", "同步检查"],
        "human_gate_terms": ["事实对象类型", "状态机", "事实实例", "测试夹具", "V2 20-24"],
        "stop_condition_terms": ["对象化", "事实实例", "字段或状态规则", "实例事实或证据", "blocker", "旧 TaskPlan"],
    },
    "06": {
        "path": SHORT_SPEC_REFS["06"],
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "action_template_boundaries",
            "context_scenario_gate",
            "git_commit_action_template",
            "capability_output_boundary",
            "action_evidence_requirements",
            "gap_disposition_rules",
            "stop_conditions",
        ],
        "required_rule_body_sections": [
            "5. 行动模板结构",
            "6. 能力输出与主控责任",
            "7. 模板候选与迁移边界",
        ],
        "required_assurance_rows": [
            "来源回指要求",
            "Gate 显式要求",
            "验证要求",
            "能力输出边界",
        ],
        "required_verification_rows": ["结构检查", "来源检查", "能力边界检查", "验证检查"],
        "human_gate_terms": ["正式可执行模板", "模板 Gate", "Hook、Rules、Skill", "能力输出", "验证、回写"],
        "stop_condition_terms": ["来源规则", "第二事实源", "顶层机制", "Human Gate", "验证证据"],
    },
    "07": {
        "path": SHORT_SPEC_REFS["07"],
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "code_determinism_rules",
            "diagnostic_boundaries",
            "action_guide_contracts",
            "preflight_contracts",
            "runtime_facade_contracts",
            "adapter_dispatcher_boundaries",
            "stop_conditions",
        ],
        "required_rule_body_sections": [
            "5. Code 能力边界",
            "6. 结构化输出与诊断",
            "7. Runtime facade 与环境适配实现边界",
            "8. Code 变更纪律",
        ],
        "required_assurance_rows": [
            "来源回指要求",
            "授权边界要求",
            "诊断分流要求",
            "测试前置要求",
        ],
        "required_verification_rows": ["结构检查", "诊断检查", "授权边界检查", "runtime 检查", "回归检查"],
        "human_gate_terms": ["授权、放行、验收", "安装 Hook", "不可验证", "Code 规则覆盖", "持久派生索引"],
        "stop_condition_terms": ["正式规则来源", "事实源、Human Gate", "parser、validator", "unknown event", "无法验证"],
    },
    "08": {
        "path": SHORT_SPEC_REFS["08"],
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "web_sync_boundaries",
            "web_code_separation_boundaries",
            "human_facing_display_rules",
            "source_ref_display_requirements",
            "controlled_interaction_boundaries",
            "web_cache_boundaries",
            "stop_conditions",
        ],
        "required_rule_body_sections": [
            "5. Human-facing 展示边界",
            "6. 同源独立读取与派生状态",
            "7. 受控交互与 Confirm UI",
        ],
        "required_assurance_rows": [
            "来源呈现要求",
            "Web/Code 分离要求",
            "非事实源要求",
            "Confirm UI 要求",
            "受控写入要求",
        ],
        "required_verification_rows": ["来源检查", "分离检查", "边界检查", "交互检查", "回归检查"],
        "human_gate_terms": ["Web 写入能力", "Confirm UI", "关键风险", "Web 状态", "Code 输出", "Web 回归线"],
        "stop_condition_terms": ["回指来源", "Web 状态", "Confirm UI", "Web 写入", "Code 输出", "暂未实现"],
    },
    "09": {
        "path": SHORT_SPEC_REFS["09"],
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "verification_rules",
            "verification_claim_fields",
            "test_evidence_boundaries",
            "failure_blocking_rules",
            "equivalent_verification_rules",
            "sync_trigger_rules",
            "stop_conditions",
        ],
        "required_rule_body_sections": [
            "5. 验证方式分层",
            "6. 验证声明与失败阻断",
            "7. 测试证据与同步触发",
        ],
        "required_assurance_rows": [
            "完成声明验证要求",
            "失败阻断要求",
            "证据边界要求",
            "同步触发要求",
        ],
        "required_verification_rows": ["声明检查", "失败检查", "证据检查", "同步检查"],
        "human_gate_terms": ["声明标准", "高价值测试", "关键验证", "测试输出", "测试通过"],
        "stop_condition_terms": ["无验证证据", "关键测试失败", "测试结果", "测试代码", "未验证范围"],
    },
}


@dataclass(frozen=True)
class Diagnostic:
    level: str
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class FormalObject:
    object_id: str
    object_type: str
    path: str
    title: str
    status: str
    metadata: dict[str, Any]
    h2_titles: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "path": self.path,
            "title": self.title,
            "status": self.status,
            "metadata": self.metadata,
            "h2_titles": self.h2_titles,
        }


def markdown_files(root: Path = ROOT) -> list[Path]:
    specs_dir = root / "specs"
    return sorted(path for path in specs_dir.glob("**/*.md") if path.name != ".gitkeep")


def first_yaml_block(raw: str, path: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(.*?)\n```", raw, re.S)
    if not match:
        raise ValueError(f"{path} missing first yaml block")
    loaded = yaml.safe_load(match.group(1))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} yaml block is not a mapping")
    return loaded


def h2_titles(raw: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"^##\s+(.+?)\s*$", raw, re.M)]


def normalize_h2_title(title: str) -> str:
    return re.sub(r"^\d+[.、]\s*", "", title.strip())


def h2_sections(raw: str) -> dict[str, dict[str, str]]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", raw, re.M))
    sections: dict[str, dict[str, str]] = {}
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        sections[normalize_h2_title(title)] = {
            "title": title,
            "body": raw[match.end() : end],
        }
    return sections


def load_formal_object(path: Path, root: Path = ROOT) -> FormalObject:
    rel_path = path.relative_to(root).as_posix()
    raw = path.read_text(encoding="utf-8")
    metadata_block = first_yaml_block(raw, rel_path)

    if "ldvh_spec" in metadata_block:
        metadata = metadata_block["ldvh_spec"]
        object_type = "spec"
        object_id = metadata.get("spec_id", "")
    elif "ldvh_attachment" in metadata_block:
        metadata = metadata_block["ldvh_attachment"]
        object_type = "attachment"
        object_id = metadata.get("attachment_id", "")
    else:
        raise ValueError(f"{rel_path} missing ldvh_spec or ldvh_attachment")

    if not isinstance(metadata, dict):
        raise ValueError(f"{rel_path} identity block is not a mapping")

    return FormalObject(
        object_id=object_id,
        object_type=object_type,
        path=rel_path,
        title=metadata.get("title", ""),
        status=metadata.get("status", ""),
        metadata=metadata,
        h2_titles=h2_titles(raw),
    )


def load_formal_objects(root: Path = ROOT) -> list[FormalObject]:
    return [load_formal_object(path, root) for path in markdown_files(root)]


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def markdown_tables(raw: str) -> list[list[dict[str, str]]]:
    lines = raw.splitlines()
    tables: list[list[dict[str, str]]] = []
    index = 0
    while index < len(lines) - 1:
        header_line = lines[index]
        separator_line = lines[index + 1]
        if not header_line.strip().startswith("|") or not separator_line.strip().startswith("|"):
            index += 1
            continue

        headers = split_markdown_row(header_line)
        separator = split_markdown_row(separator_line)
        if not is_separator_row(separator):
            index += 1
            continue

        rows: list[dict[str, str]] = []
        row_index = index + 2
        while row_index < len(lines) and lines[row_index].strip().startswith("|"):
            cells = split_markdown_row(lines[row_index])
            if len(cells) < len(headers):
                cells.extend([""] * (len(headers) - len(cells)))
            rows.append({headers[column]: cells[column] for column in range(len(headers))})
            row_index += 1
        tables.append(rows)
        index = row_index
    return tables


def find_table(raw: str, required_columns: list[str]) -> list[dict[str, str]]:
    for table in markdown_tables(raw):
        if not table:
            continue
        columns = set(table[0])
        if all(column in columns for column in required_columns):
            return table
    return []


def numbered_list_items(raw: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"^\s*\d+\.\s+(.+?)\s*$", raw, re.M)]


def strip_inline_code(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and value.count("`") == 2:
        return value[1:-1].strip()
    return value.replace("`", "").strip()


def split_semicolon_list(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[；;]", value) if part.strip()]


def normalize_required_source_ref(value: str, source_path: str) -> dict[str, str]:
    stripped = strip_inline_code(value).strip()
    if stripped in SHORT_SPEC_REFS:
        return {"type": "spec", "path": SHORT_SPEC_REFS[stripped], "label": stripped}
    refs = extract_spec_path_refs(stripped)
    if refs:
        return {"type": "spec", "path": refs[0], "label": stripped}
    if stripped.startswith("本文"):
        return {"type": "spec_section", "path": source_path, "label": stripped}
    return {"type": "process_evidence", "path": "", "label": stripped}


def parse_consumption_timings(root: Path = ROOT) -> list[dict[str, str]]:
    path = root / TIMING_TABLE_PATH
    raw = path.read_text(encoding="utf-8")
    rows = find_table(raw, TIMING_COLUMNS)
    return [
        {
            "consumption_timing": strip_inline_code(row["消费时机"]),
            "trigger": row["触发点"],
            "consumer": row["消费主体"],
            "usage": row["用途"],
            "source_path": TIMING_TABLE_PATH,
        }
        for row in rows
    ]


def parse_ai_behavior_requirements(root: Path = ROOT) -> list[dict[str, Any]]:
    path = root / AI_BEHAVIOR_SPEC_PATH
    raw = path.read_text(encoding="utf-8")
    rows = find_table(raw, AI_BEHAVIOR_COLUMNS)
    requirements: list[dict[str, Any]] = []
    for row in rows:
        requirements.append(
            {
                "requirement_id": row["需求ID"],
                "requirement": row["保障需求"],
                "consumption_timing": strip_inline_code(row["消费时机"]),
                "required_sources": split_semicolon_list(row["必读依据"]),
                "required_capability": row["所需能力"],
                "completion_evidence": row["完成证据"],
                "blocking_conditions": split_semicolon_list(row["阻断条件"]),
                "gap_disposition": split_semicolon_list(row["缺口分流"]),
                "source_path": AI_BEHAVIOR_SPEC_PATH,
            }
        )
    return requirements


def parse_takeover_matrix(root: Path = ROOT) -> list[dict[str, str]]:
    path = root / TAKEOVER_MATRIX_PATH
    raw = path.read_text(encoding="utf-8")
    rows = find_table(raw, TAKEOVER_COLUMNS)
    return [
        {
            "requirement_id": row["需求ID"],
            "consumption_timing": strip_inline_code(row["触发消费时机"]),
            "action_guide_takeover": row["行动指南承接"],
            "hook_takeover": row["Hook 承接"],
            "source_path": TAKEOVER_MATRIX_PATH,
        }
        for row in rows
    ]


def parse_commit_message_contract(root: Path = ROOT) -> dict[str, list[dict[str, str]]]:
    raw = (root / COMMIT_MESSAGE_CONTRACT_PATH).read_text(encoding="utf-8")
    return {
        "fields": find_table(raw, COMMIT_MESSAGE_FIELD_COLUMNS),
        "types": find_table(raw, COMMIT_TYPE_COLUMNS),
        "scopes": find_table(raw, COMMIT_SCOPE_COLUMNS),
        "body_conditions": find_table(raw, COMMIT_BODY_CONDITION_COLUMNS),
    }


def parse_field_registry_contract(root: Path = ROOT) -> dict[str, list[dict[str, str]]]:
    raw = (root / FIELD_REGISTRY_CONTRACT_PATH).read_text(encoding="utf-8")
    return {
        "columns": find_table(raw, FIELD_REGISTRY_COLUMNS),
        "allowed_values": find_table(raw, FIELD_REGISTRY_ALLOWED_COLUMNS),
        "code_check_kinds": find_table(raw, FIELD_REGISTRY_CODE_CHECK_COLUMNS),
    }


def parse_verification_claim_fields(root: Path = ROOT) -> dict[str, list[dict[str, str]]]:
    raw = (root / VERIFICATION_CLAIM_FIELDS_PATH).read_text(encoding="utf-8")
    return {
        "fields": find_table(raw, VERIFICATION_CLAIM_COLUMNS),
        "complete_conditions": find_table(raw, VERIFICATION_COMPLETE_CONDITION_COLUMNS),
        "forbidden_writings": find_table(raw, VERIFICATION_FORBIDDEN_COLUMNS),
    }


def parse_git_commit_action_template(root: Path = ROOT) -> list[dict[str, str]]:
    raw = (root / SHORT_SPEC_REFS["06"]).read_text(encoding="utf-8")
    sections = h2_sections(raw)
    section = sections.get("模板候选与迁移边界")
    if not section:
        return []
    return find_table(section["body"], ACTION_TEMPLATE_COLUMNS)


def parse_workcase_member_contract(root: Path = ROOT) -> dict[str, Any]:
    path = SHORT_SPEC_REFS["21"]
    full_path = root / path
    if not full_path.exists():
        return {
            "path": path,
            "code_consumption": [],
            "statuses": [],
            "source_refs": [],
        }

    raw = full_path.read_text(encoding="utf-8")
    metadata = first_yaml_block(raw, path).get("ldvh_spec", {})
    sections = h2_sections(raw)
    status_rows = _table_rows_for_section(sections, "状态、证据与关闭边界", WORKCASE_STATUS_COLUMNS)

    return {
        "path": path,
        "code_consumption": metadata.get("code_consumption", []),
        "statuses": [
            {
                "status": strip_inline_code(row["状态"]),
                "meaning": row["含义"],
            }
            for row in status_rows
        ],
        "source_refs": [
            {"path": SHORT_SPEC_REFS["05"], "role": "parent_fact_model_spec"},
            {"path": path, "role": "workcase_member_spec"},
            {"path": "specs/03-事实源与Git溯源规范.md", "role": "fact_source_boundary"},
            {"path": "specs/09-测试与验证规范.md", "role": "verification_boundary"},
        ],
    }


def _table_rows_for_section(sections: dict[str, dict[str, str]], section_name: str, columns: list[str]) -> list[dict[str, str]]:
    section = sections.get(section_name)
    if not section:
        return []
    return find_table(section["body"], columns)


def _section_numbered_items(sections: dict[str, dict[str, str]], section_name: str) -> list[str]:
    section = sections.get(section_name)
    if not section:
        return []
    return numbered_list_items(section["body"])


def parse_foundation_spec_contracts(
    objects: list[FormalObject],
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    objects_by_id = {obj.object_id: obj for obj in objects if obj.object_type == "spec"}
    contracts: list[dict[str, Any]] = []
    for spec_id in FOUNDATION_SPEC_IDS:
        obj = objects_by_id.get(spec_id)
        if not obj:
            continue
        raw = (root / obj.path).read_text(encoding="utf-8")
        sections = h2_sections(raw)
        role_sections = obj.metadata.get("role_sections", {})
        rule_body_sections = []
        if isinstance(role_sections, dict):
            rule_body_sections = flatten_role_sections(role_sections.get("rule_body", []))

        assurance_rows = _table_rows_for_section(sections, "保障措施", ASSURANCE_COLUMNS)
        verification_rows = _table_rows_for_section(sections, "验证方法", VERIFICATION_COLUMNS)
        contracts.append(
            {
                "spec_id": spec_id,
                "path": obj.path,
                "title": obj.title,
                "status": obj.status,
                "authority": obj.metadata.get("authority", ""),
                "code_consumption": obj.metadata.get("code_consumption", []),
                "rule_body_sections": rule_body_sections,
                "assurance_measures": [
                    {
                        "requirement": row["保障要求"],
                        "content": row["要求内容"],
                        "mechanism": row["保障机制"],
                        "sync_type": row["同步类型"],
                        "trigger": row["触发条件"],
                    }
                    for row in assurance_rows
                ],
                "verification_checks": [
                    {
                        "check_type": row["检查类别"],
                        "content": row["检查内容"],
                        "failure_disposition": row["不满足时"],
                    }
                    for row in verification_rows
                ],
                "human_gate": _section_numbered_items(sections, "Human Gate"),
                "stop_conditions": _section_numbered_items(sections, "Stop Conditions"),
                "source_refs": [
                    {"path": obj.path, "role": "foundation_spec"},
                    {"path": "specs/00-理念与构成.md", "role": "value_anchor"},
                    {"path": "specs/01-保障与衔接.md", "role": "assurance_boundary"},
                    {"path": "specs/03-事实源与Git溯源规范.md", "role": "fact_source_boundary"},
                    {"path": "specs/07-Code确定性执行规范.md", "role": "code_boundary"},
                    {"path": "specs/09-测试与验证规范.md", "role": "verification_boundary"},
                ],
            }
        )
    return contracts


def flatten_role_sections(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        titles: list[str] = []
        for item in value:
            titles.extend(flatten_role_sections(item))
        return titles
    if isinstance(value, dict):
        titles = []
        for item in value.values():
            titles.extend(flatten_role_sections(item))
        return titles
    return []


def extract_spec_path_refs(text: str) -> list[str]:
    return re.findall(r"`?(specs/[^\s`；;，,。]+?\.md)`?", text)


def unique_dicts(items: list[dict[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        key = tuple(item.get(field) for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def path_exists(root: Path, rel_path: str) -> bool:
    return (root / rel_path).exists()


def validate_formal_objects(
    objects: list[FormalObject],
    root: Path = ROOT,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen_ids: set[str] = set()
    seen_paths = {obj.path for obj in objects}

    for obj in objects:
        if obj.object_id in seen_ids:
            diagnostics.append(Diagnostic("error", "DUPLICATE_OBJECT_ID", obj.path, f"重复对象 ID: {obj.object_id}"))
        seen_ids.add(obj.object_id)

        metadata = obj.metadata
        required = SPEC_REQUIRED_KEYS if obj.object_type == "spec" else ATTACHMENT_REQUIRED_KEYS
        missing = sorted(key for key in required if key not in metadata)
        for key in missing:
            diagnostics.append(Diagnostic("error", "MISSING_IDENTITY_FIELD", obj.path, f"缺少身份字段: {key}"))

        if metadata.get("canonical_path") != obj.path:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "CANONICAL_PATH_MISMATCH",
                    obj.path,
                    f"canonical_path 应为 {obj.path}",
                )
            )

        if obj.object_type == "attachment":
            if metadata.get("relation") != "authorizes_attachment":
                diagnostics.append(Diagnostic("error", "ATTACHMENT_RELATION", obj.path, "附件 relation 必须为 authorizes_attachment"))
            parent = metadata.get("parent_spec", "")
            if parent and parent not in seen_paths:
                diagnostics.append(Diagnostic("error", "MISSING_PARENT_SPEC", obj.path, f"父规范不存在: {parent}"))
            continue

        code_consumption = metadata.get("code_consumption", [])
        if not isinstance(code_consumption, list) or not code_consumption:
            diagnostics.append(Diagnostic("error", "CODE_CONSUMPTION_MISSING", obj.path, "spec 必须声明 code_consumption"))

        if obj.object_id != "00":
            role_sections = metadata.get("role_sections")
            if not isinstance(role_sections, dict):
                diagnostics.append(Diagnostic("error", "ROLE_SECTIONS_MISSING", obj.path, "非根 spec 必须声明 role_sections"))
            else:
                for title in flatten_role_sections(role_sections):
                    if title not in obj.h2_titles:
                        diagnostics.append(Diagnostic("error", "ROLE_SECTION_NOT_FOUND", obj.path, f"role_sections 指向不存在的 H2: {title}"))

        for field in ("basis", "related_specs", "active_fact_source"):
            refs = metadata.get(field, [])
            if refs is None:
                continue
            if not isinstance(refs, list):
                diagnostics.append(Diagnostic("error", "REFERENCE_FIELD_NOT_LIST", obj.path, f"{field} 必须是列表"))
                continue
            for ref in refs:
                if isinstance(ref, str) and ref.startswith("specs/") and not path_exists(root, ref):
                    diagnostics.append(Diagnostic("error", "REFERENCE_NOT_FOUND", obj.path, f"{field} 引用不存在: {ref}"))

    return diagnostics


def validate_consumption_timings(timings: list[dict[str, str]]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen: set[str] = set()
    if not timings:
        diagnostics.append(Diagnostic("error", "TIMING_TABLE_NOT_FOUND", TIMING_TABLE_PATH, "未找到消费时机表"))
        return diagnostics
    for row in timings:
        timing = row["consumption_timing"]
        if not timing:
            diagnostics.append(Diagnostic("error", "TIMING_EMPTY", TIMING_TABLE_PATH, "消费时机为空"))
        if timing in seen:
            diagnostics.append(Diagnostic("error", "TIMING_DUPLICATE", TIMING_TABLE_PATH, f"重复消费时机: {timing}"))
        seen.add(timing)
    return diagnostics


def validate_ai_behavior_requirements(
    requirements: list[dict[str, Any]],
    timings: list[dict[str, str]],
    objects: list[FormalObject],
    root: Path = ROOT,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    allowed_timings = {row["consumption_timing"] for row in timings}
    seen_ids: set[str] = set()
    spec_03 = next((obj for obj in objects if obj.path == AI_BEHAVIOR_SPEC_PATH), None)
    if spec_03 and "ai_behavior_assurance_requirements" not in spec_03.metadata.get("code_consumption", []):
        diagnostics.append(
            Diagnostic(
                "error",
                "AI_BEHAVIOR_CODE_CONSUMPTION_MISSING",
                AI_BEHAVIOR_SPEC_PATH,
                "02 必须声明 ai_behavior_assurance_requirements",
            )
        )

    if not requirements:
        diagnostics.append(Diagnostic("error", "AI_BEHAVIOR_TABLE_NOT_FOUND", AI_BEHAVIOR_SPEC_PATH, "未找到 AI 行为保障需求表"))
        return diagnostics

    for row in requirements:
        requirement_id = row["requirement_id"]
        if not re.fullmatch(r"AI-BEH-\d{3}", requirement_id):
            diagnostics.append(Diagnostic("error", "AI_BEHAVIOR_ID_FORMAT", AI_BEHAVIOR_SPEC_PATH, f"需求ID 格式不正确: {requirement_id}"))
        if requirement_id in seen_ids:
            diagnostics.append(Diagnostic("error", "AI_BEHAVIOR_ID_DUPLICATE", AI_BEHAVIOR_SPEC_PATH, f"重复需求ID: {requirement_id}"))
        seen_ids.add(requirement_id)

        if row["consumption_timing"] not in allowed_timings:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "AI_BEHAVIOR_TIMING_NOT_ALLOWED",
                    AI_BEHAVIOR_SPEC_PATH,
                    f"{requirement_id} 使用未授权消费时机: {row['consumption_timing']}",
                )
            )

        for key in (
            "requirement",
            "required_sources",
            "required_capability",
            "completion_evidence",
            "blocking_conditions",
            "gap_disposition",
        ):
            if not row[key]:
                diagnostics.append(Diagnostic("error", "AI_BEHAVIOR_FIELD_EMPTY", AI_BEHAVIOR_SPEC_PATH, f"{requirement_id} 字段为空: {key}"))

        for source in row["required_sources"]:
            for ref in extract_spec_path_refs(source):
                if not path_exists(root, ref):
                    diagnostics.append(Diagnostic("error", "AI_BEHAVIOR_SOURCE_NOT_FOUND", AI_BEHAVIOR_SPEC_PATH, f"{requirement_id} 必读依据不存在: {ref}"))

    return diagnostics


def validate_takeover_matrix(
    matrix: list[dict[str, str]],
    requirements: list[dict[str, Any]],
    timings: list[dict[str, str]],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    allowed_ids = {row["requirement_id"] for row in requirements}
    allowed_timings = {row["consumption_timing"] for row in timings}
    seen_ids: set[str] = set()

    if not matrix:
        diagnostics.append(Diagnostic("error", "TAKEOVER_MATRIX_NOT_FOUND", TAKEOVER_MATRIX_PATH, "未找到保障机制承接矩阵"))
        return diagnostics

    for row in matrix:
        requirement_id = row["requirement_id"]
        if requirement_id in seen_ids:
            diagnostics.append(Diagnostic("error", "TAKEOVER_ID_DUPLICATE", TAKEOVER_MATRIX_PATH, f"重复需求ID: {requirement_id}"))
        seen_ids.add(requirement_id)
        if requirement_id not in allowed_ids:
            diagnostics.append(Diagnostic("error", "TAKEOVER_REQUIREMENT_UNKNOWN", TAKEOVER_MATRIX_PATH, f"承接矩阵引用未知需求ID: {requirement_id}"))
        if row["consumption_timing"] not in allowed_timings:
            diagnostics.append(Diagnostic("error", "TAKEOVER_TIMING_NOT_ALLOWED", TAKEOVER_MATRIX_PATH, f"{requirement_id} 使用未授权消费时机: {row['consumption_timing']}"))

    missing_ids = sorted(allowed_ids - seen_ids)
    for requirement_id in missing_ids:
        diagnostics.append(Diagnostic("error", "TAKEOVER_REQUIREMENT_MISSING", TAKEOVER_MATRIX_PATH, f"承接矩阵缺少需求ID: {requirement_id}"))

    return diagnostics


def _missing_exact_values(expected: list[str], actual: list[str]) -> list[str]:
    actual_set = set(actual)
    return [item for item in expected if item not in actual_set]


def _missing_contained_terms(expected: list[str], actual_items: list[str]) -> list[str]:
    return [term for term in expected if not any(term in item for item in actual_items)]


def validate_foundation_spec_contracts(contracts: list[dict[str, Any]]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    contracts_by_id = {contract["spec_id"]: contract for contract in contracts}

    for spec_id in FOUNDATION_SPEC_IDS:
        expected = FOUNDATION_SPEC_CONTRACTS[spec_id]
        path = expected["path"]
        contract = contracts_by_id.get(spec_id)
        if not contract:
            diagnostics.append(Diagnostic("error", "FOUNDATION_SPEC_MISSING", path, f"{spec_id} 基础规范缺失"))
            continue

        code_consumption = contract["code_consumption"]
        if not isinstance(code_consumption, list):
            diagnostics.append(Diagnostic("error", "FOUNDATION_CODE_CONSUMPTION_INVALID", path, "code_consumption 必须是列表"))
            code_consumption = []
        for item in _missing_exact_values(expected["required_code_consumption"], code_consumption):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "FOUNDATION_CODE_CONSUMPTION_MISSING",
                    path,
                    f"{spec_id} 缺少 Code 消费入口: {item}",
                )
            )

        for title in _missing_exact_values(expected["required_rule_body_sections"], contract["rule_body_sections"]):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "FOUNDATION_RULE_BODY_SECTION_MISSING",
                    path,
                    f"{spec_id} role_sections.rule_body 缺少主体规则区: {title}",
                )
            )

        assurance_rows = contract["assurance_measures"]
        if not assurance_rows:
            diagnostics.append(Diagnostic("error", "FOUNDATION_ASSURANCE_TABLE_MISSING", path, f"{spec_id} 缺少可解析保障措施表"))
        else:
            assurance_names = [row["requirement"] for row in assurance_rows]
            for item in _missing_exact_values(expected["required_assurance_rows"], assurance_names):
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "FOUNDATION_ASSURANCE_ROW_MISSING",
                        path,
                        f"{spec_id} 缺少保障要求: {item}",
                    )
                )
            for row in assurance_rows:
                for key in ("requirement", "content", "mechanism", "sync_type", "trigger"):
                    if not row[key]:
                        diagnostics.append(
                            Diagnostic(
                                "error",
                                "FOUNDATION_ASSURANCE_FIELD_EMPTY",
                                path,
                                f"{spec_id} 保障措施字段为空: {key}",
                            )
                        )

        verification_rows = contract["verification_checks"]
        if not verification_rows:
            diagnostics.append(Diagnostic("error", "FOUNDATION_VERIFICATION_TABLE_MISSING", path, f"{spec_id} 缺少可解析验证方法表"))
        else:
            verification_names = [row["check_type"] for row in verification_rows]
            for item in _missing_exact_values(expected["required_verification_rows"], verification_names):
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "FOUNDATION_VERIFICATION_ROW_MISSING",
                        path,
                        f"{spec_id} 缺少验证检查: {item}",
                    )
                )
            for row in verification_rows:
                for key in ("check_type", "content", "failure_disposition"):
                    if not row[key]:
                        diagnostics.append(
                            Diagnostic(
                                "error",
                                "FOUNDATION_VERIFICATION_FIELD_EMPTY",
                                path,
                                f"{spec_id} 验证方法字段为空: {key}",
                            )
                        )

        if not contract["human_gate"]:
            diagnostics.append(Diagnostic("error", "FOUNDATION_HUMAN_GATE_MISSING", path, f"{spec_id} 缺少 Human Gate 条目"))
        for term in _missing_contained_terms(expected["human_gate_terms"], contract["human_gate"]):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "FOUNDATION_HUMAN_GATE_TERM_MISSING",
                    path,
                    f"{spec_id} Human Gate 缺少关键边界: {term}",
                )
            )

        if not contract["stop_conditions"]:
            diagnostics.append(Diagnostic("error", "FOUNDATION_STOP_CONDITION_MISSING", path, f"{spec_id} 缺少 Stop Conditions 条目"))
        for term in _missing_contained_terms(expected["stop_condition_terms"], contract["stop_conditions"]):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "FOUNDATION_STOP_CONDITION_TERM_MISSING",
                    path,
                    f"{spec_id} Stop Conditions 缺少关键边界: {term}",
                )
            )

    return diagnostics


def validate_fact_model_boundaries(root: Path = ROOT) -> list[Diagnostic]:
    path = SHORT_SPEC_REFS["05"]
    raw = (root / path).read_text(encoding="utf-8")
    sections = h2_sections(raw)
    diagnostics: list[Diagnostic] = []

    for requirement in FACT_MODEL_BOUNDARY_REQUIREMENTS:
        section = sections.get(requirement["section"])
        if not section:
            diagnostics.append(
                Diagnostic(
                    "error",
                    requirement["code"],
                    path,
                    f"05 缺少可消费章节: {requirement['section']}",
                )
            )
            continue
        body = section["body"]
        missing_terms = [term for term in requirement["terms"] if term not in body]
        if missing_terms:
            diagnostics.append(
                Diagnostic(
                    "error",
                    requirement["code"],
                    path,
                    f"{requirement['message']}: {', '.join(missing_terms)}",
                )
            )

    return diagnostics


def validate_fact_source_and_verification_boundaries(root: Path = ROOT) -> list[Diagnostic]:
    raw_by_path: dict[str, str] = {}
    sections_by_path: dict[str, dict[str, dict[str, str]]] = {}
    diagnostics: list[Diagnostic] = []

    for requirement in FACT_SOURCE_EVIDENCE_REQUIREMENTS:
        path = requirement["path"]
        if path not in raw_by_path:
            raw_by_path[path] = (root / path).read_text(encoding="utf-8")
            sections_by_path[path] = h2_sections(raw_by_path[path])
        section = sections_by_path[path].get(requirement["section"])
        if not section:
            diagnostics.append(
                Diagnostic(
                    "error",
                    requirement["code"],
                    path,
                    f"缺少可消费章节: {requirement['section']}",
                )
            )
            continue
        missing_terms = [term for term in requirement["terms"] if term not in section["body"]]
        if missing_terms:
            diagnostics.append(
                Diagnostic(
                    "error",
                    requirement["code"],
                    path,
                    f"{requirement['message']}: {', '.join(missing_terms)}",
                )
            )

    return diagnostics


def validate_web_sync_boundaries(root: Path = ROOT) -> list[Diagnostic]:
    path = SHORT_SPEC_REFS["08"]
    raw = (root / path).read_text(encoding="utf-8")
    sections = h2_sections(raw)
    diagnostics: list[Diagnostic] = []

    for phrase in WEB_SYNC_FORBIDDEN_PHRASES:
        if phrase in raw:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "WEB_CODE_DATA_DEPENDENCY_FORBIDDEN",
                    path,
                    f"08 禁止恢复 Web 依赖 Code 输出的数据路径表述: {phrase}",
                )
            )

    for requirement in WEB_SYNC_BOUNDARY_REQUIREMENTS:
        section = sections.get(requirement["section"])
        if not section:
            diagnostics.append(
                Diagnostic(
                    "error",
                    requirement["code"],
                    path,
                    f"08 缺少可消费章节: {requirement['section']}",
                )
            )
            continue
        missing_terms = [term for term in requirement["terms"] if term not in section["body"]]
        if missing_terms:
            diagnostics.append(
                Diagnostic(
                    "error",
                    requirement["code"],
                    path,
                    f"{requirement['message']}: {', '.join(missing_terms)}",
                )
            )

    return diagnostics


def _table_has_values(rows: list[dict[str, str]], column: str, expected_values: list[str]) -> list[str]:
    actual = {strip_inline_code(row.get(column, "")) for row in rows}
    return [value for value in expected_values if value not in actual]


def _validate_attachment_authorized_by_parent(
    root: Path,
    attachment_path: str,
    parent_path: str,
) -> list[Diagnostic]:
    raw = (root / parent_path).read_text(encoding="utf-8")
    metadata = first_yaml_block(raw, parent_path)["ldvh_spec"]
    related_specs = metadata.get("related_specs", [])
    if attachment_path in related_specs:
        return []
    return [
        Diagnostic(
            "error",
            "ATTACHMENT_PARENT_REFERENCE_MISSING",
            parent_path,
            f"父规范 related_specs 缺少授权附件: {attachment_path}",
        )
    ]


def validate_attachment_contracts(root: Path = ROOT) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_validate_attachment_authorized_by_parent(root, COMMIT_MESSAGE_CONTRACT_PATH, SHORT_SPEC_REFS["03"]))
    diagnostics.extend(_validate_attachment_authorized_by_parent(root, FIELD_REGISTRY_CONTRACT_PATH, SHORT_SPEC_REFS["05"]))
    diagnostics.extend(_validate_attachment_authorized_by_parent(root, VERIFICATION_CLAIM_FIELDS_PATH, SHORT_SPEC_REFS["09"]))

    commit_contract = parse_commit_message_contract(root)
    if not commit_contract["fields"]:
        diagnostics.append(Diagnostic("error", "COMMIT_CONTRACT_FIELD_TABLE_MISSING", COMMIT_MESSAGE_CONTRACT_PATH, "commit message 字段表缺失"))
    for value in _table_has_values(commit_contract["fields"], "字段", ["type", "scope", "description", "body", "footer"]):
        diagnostics.append(Diagnostic("error", "COMMIT_CONTRACT_FIELD_MISSING", COMMIT_MESSAGE_CONTRACT_PATH, f"commit message 字段缺失: {value}"))
    for value in _table_has_values(commit_contract["types"], "type", ["feat", "fix", "docs", "test", "chore", "revert"]):
        diagnostics.append(Diagnostic("error", "COMMIT_TYPE_ENUM_MISSING", COMMIT_MESSAGE_CONTRACT_PATH, f"commit type 缺失: {value}"))
    for value in _table_has_values(commit_contract["scopes"], "scope", ["specs", "code", "web", "tests", "workcase", "spark"]):
        diagnostics.append(Diagnostic("error", "COMMIT_SCOPE_ENUM_MISSING", COMMIT_MESSAGE_CONTRACT_PATH, f"commit scope 缺失: {value}"))
    for value in _table_has_values(commit_contract["body_conditions"], "条件类型", ["高影响文件", "事实对象字段", "多文件范围", "边界变化"]):
        diagnostics.append(Diagnostic("error", "COMMIT_BODY_CONDITION_MISSING", COMMIT_MESSAGE_CONTRACT_PATH, f"commit body 条件缺失: {value}"))

    field_registry = parse_field_registry_contract(root)
    if not field_registry["columns"]:
        diagnostics.append(Diagnostic("error", "FIELD_REGISTRY_TABLE_MISSING", FIELD_REGISTRY_CONTRACT_PATH, "字段注册表结构缺失"))
    for value in _table_has_values(field_registry["columns"], "列", ["field_path", "scope", "meaning", "format_kind", "value_shape", "code_check_kind", "status", "replacement"]):
        diagnostics.append(Diagnostic("error", "FIELD_REGISTRY_COLUMN_MISSING", FIELD_REGISTRY_CONTRACT_PATH, f"字段注册列缺失: {value}"))
    for value in _table_has_values(field_registry["allowed_values"], "注册列", ["format_kind", "value_shape", "ref_kind", "code_check_kind", "web_render_kind", "status"]):
        diagnostics.append(Diagnostic("error", "FIELD_REGISTRY_ALLOWED_VALUE_MISSING", FIELD_REGISTRY_CONTRACT_PATH, f"字段注册闭集缺失: {value}"))
    for value in _table_has_values(field_registry["code_check_kinds"], "code_check_kind", ["none", "format", "ref", "enum", "structured", "deprecated", "owner_state"]):
        diagnostics.append(Diagnostic("error", "FIELD_REGISTRY_CODE_CHECK_KIND_MISSING", FIELD_REGISTRY_CONTRACT_PATH, f"字段注册 Code 校验维度缺失: {value}"))

    verification_claims = parse_verification_claim_fields(root)
    if not verification_claims["fields"]:
        diagnostics.append(Diagnostic("error", "VERIFICATION_CLAIM_FIELD_TABLE_MISSING", VERIFICATION_CLAIM_FIELDS_PATH, "验证声明字段表缺失"))
    for value in _table_has_values(verification_claims["fields"], "字段", ["验证目标", "验证方式", "验证入口", "输入范围", "关键输出", "结论", "残留风险", "证据回指"]):
        diagnostics.append(Diagnostic("error", "VERIFICATION_CLAIM_FIELD_MISSING", VERIFICATION_CLAIM_FIELDS_PATH, f"验证声明字段缺失: {value}"))
    for value in _table_has_values(verification_claims["complete_conditions"], "条件", ["目标匹配", "入口可复现", "输入明确", "输出明确", "风险记录", "证据回指"]):
        diagnostics.append(Diagnostic("error", "VERIFICATION_COMPLETE_CONDITION_MISSING", VERIFICATION_CLAIM_FIELDS_PATH, f"完整验证条件缺失: {value}"))
    for value in _table_has_values(verification_claims["forbidden_writings"], "写法", ["只列命令", "未运行测试但暗示已验证", "局部测试通过写成完整验证", "工具无报错写成 Human 已确认", "看起来正确"]):
        diagnostics.append(Diagnostic("error", "VERIFICATION_FORBIDDEN_WRITING_MISSING", VERIFICATION_CLAIM_FIELDS_PATH, f"验证声明禁止写法缺失: {value}"))

    return diagnostics


def validate_git_commit_action_template(root: Path = ROOT) -> list[Diagnostic]:
    path = SHORT_SPEC_REFS["06"]
    raw = (root / path).read_text(encoding="utf-8")
    rows = parse_git_commit_action_template(root)
    diagnostics: list[Diagnostic] = []

    if not rows:
        return [
            Diagnostic(
                "error",
                "GIT_COMMIT_ACTION_TEMPLATE_MISSING",
                path,
                "06 缺少 Git 提交行动模板结构表",
            )
        ]

    rows_by_structure = {row["结构"]: row for row in rows}
    for structure, terms in GIT_COMMIT_ACTION_TEMPLATE_REQUIRED_ROWS.items():
        row = rows_by_structure.get(structure)
        if not row:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "GIT_COMMIT_ACTION_TEMPLATE_ROW_MISSING",
                    path,
                    f"Git 提交行动模板缺少结构: {structure}",
                )
            )
            continue
        missing_terms = [term for term in terms if term not in row["最小要求"]]
        for term in missing_terms:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "GIT_COMMIT_ACTION_TEMPLATE_TERM_MISSING",
                    path,
                    f"{structure} 缺少关键要求: {term}",
                )
            )

    missing_boundary_terms = [term for term in GIT_COMMIT_ACTION_TEMPLATE_BOUNDARY_TERMS if term not in raw]
    for term in missing_boundary_terms:
        diagnostics.append(
            Diagnostic(
                "error",
                "GIT_COMMIT_ACTION_TEMPLATE_BOUNDARY_MISSING",
                path,
                f"Git 提交行动模板缺少边界声明: {term}",
            )
        )

    return diagnostics


def validate_workcase_member_contract(root: Path = ROOT) -> list[Diagnostic]:
    path = SHORT_SPEC_REFS["21"]
    full_path = root / path
    diagnostics: list[Diagnostic] = []
    if not full_path.exists():
        return [Diagnostic("error", "WORKCASE_MEMBER_SPEC_MISSING", path, "21 WorkCase 成员规范缺失")]

    raw = full_path.read_text(encoding="utf-8")
    sections = h2_sections(raw)
    contract = parse_workcase_member_contract(root)

    code_consumption = contract["code_consumption"]
    if not isinstance(code_consumption, list):
        diagnostics.append(Diagnostic("error", "WORKCASE_CODE_CONSUMPTION_INVALID", path, "21 code_consumption 必须是列表"))
        code_consumption = []
    for item in _missing_exact_values(WORKCASE_REQUIRED_CODE_CONSUMPTION, code_consumption):
        diagnostics.append(
            Diagnostic(
                "error",
                "WORKCASE_CODE_CONSUMPTION_MISSING",
                path,
                f"21 缺少 Code 消费入口: {item}",
            )
        )

    status_values = [row["status"] for row in contract["statuses"]]
    for status in _missing_exact_values(WORKCASE_REQUIRED_STATUSES, status_values):
        diagnostics.append(
            Diagnostic(
                "error",
                "WORKCASE_STATUS_MISSING",
                path,
                f"WorkCase 状态闭集缺少: {status}",
            )
        )

    source_section = sections.get("事实源与实例边界")
    if not source_section:
        diagnostics.append(Diagnostic("error", "WORKCASE_SOURCE_BOUNDARY_MISSING", path, "21 缺少事实源与实例边界章节"))
    else:
        for term in [term for term in WORKCASE_SOURCE_BOUNDARY_TERMS if term not in source_section["body"]]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "WORKCASE_SOURCE_BOUNDARY_MISSING",
                    path,
                    f"WorkCase 事实源边界缺少: {term}",
                )
            )

    state_section = sections.get("状态、证据与关闭边界")
    if not state_section:
        diagnostics.append(Diagnostic("error", "WORKCASE_CLOSURE_BOUNDARY_MISSING", path, "21 缺少状态、证据与关闭边界章节"))
    else:
        for term in [term for term in WORKCASE_CLOSURE_BOUNDARY_TERMS if term not in state_section["body"]]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "WORKCASE_CLOSURE_BOUNDARY_MISSING",
                    path,
                    f"WorkCase 关闭口径缺少: {term}",
                )
            )
        for status in [status for status in WORKCASE_LEGACY_STATUSES if status not in state_section["body"]]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "WORKCASE_LEGACY_STATUS_BOUNDARY_MISSING",
                    path,
                    f"WorkCase legacy 状态边界缺少: {status}",
                )
            )

    human_gate_section = sections.get("Human Gate")
    if not human_gate_section:
        diagnostics.append(Diagnostic("error", "WORKCASE_HUMAN_GATE_BOUNDARY_MISSING", path, "21 缺少 Human Gate 章节"))
    else:
        for term in [term for term in WORKCASE_HUMAN_GATE_TERMS if term not in human_gate_section["body"]]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "WORKCASE_HUMAN_GATE_BOUNDARY_MISSING",
                    path,
                    f"WorkCase Human Gate 缺少: {term}",
                )
            )

    return diagnostics


def build_validation(root: Path = ROOT) -> dict[str, Any]:
    objects = load_formal_objects(root)
    specs = [obj for obj in objects if obj.object_type == "spec"]
    attachments = [obj for obj in objects if obj.object_type == "attachment"]
    timings = parse_consumption_timings(root)
    requirements = parse_ai_behavior_requirements(root)
    takeover_matrix = parse_takeover_matrix(root)
    foundation_spec_contracts = parse_foundation_spec_contracts(objects, root)
    git_commit_action_template = parse_git_commit_action_template(root)
    workcase_member_contract = parse_workcase_member_contract(root)
    attachment_contracts = {
        "commit_message_contract": parse_commit_message_contract(root),
        "field_registry_contract": parse_field_registry_contract(root),
        "verification_claim_fields": parse_verification_claim_fields(root),
    }

    diagnostics: list[Diagnostic] = []
    diagnostics.extend(validate_formal_objects(objects, root))
    diagnostics.extend(validate_consumption_timings(timings))
    diagnostics.extend(validate_ai_behavior_requirements(requirements, timings, objects, root))
    diagnostics.extend(validate_takeover_matrix(takeover_matrix, requirements, timings))
    diagnostics.extend(validate_foundation_spec_contracts(foundation_spec_contracts))
    diagnostics.extend(validate_fact_model_boundaries(root))
    diagnostics.extend(validate_fact_source_and_verification_boundaries(root))
    diagnostics.extend(validate_web_sync_boundaries(root))
    diagnostics.extend(validate_attachment_contracts(root))
    diagnostics.extend(validate_git_commit_action_template(root))
    diagnostics.extend(validate_workcase_member_contract(root))

    diagnostic_dicts = [diagnostic.to_dict() for diagnostic in diagnostics]
    status = "ok" if not diagnostic_dicts else "failed"

    return {
        "metadata": {
            "read_only": True,
            "authority": "specs_markdown",
            "root": root.as_posix(),
        },
        "summary": {
            "status": status,
            "specs": len(specs),
            "attachments": len(attachments),
            "formal_objects": len(objects),
            "consumption_timings": len(timings),
            "ai_behavior_requirements": len(requirements),
            "takeover_matrix_rows": len(takeover_matrix),
            "foundation_spec_contracts": len(foundation_spec_contracts),
            "diagnostics": len(diagnostic_dicts),
            "errors": sum(1 for diagnostic in diagnostics if diagnostic.level == "error"),
            "warnings": sum(1 for diagnostic in diagnostics if diagnostic.level == "warning"),
        },
        "source_refs": [
            {"path": "specs/00-理念与构成.md", "role": "value_anchor"},
            {"path": "specs/01-保障与衔接.md", "role": "assurance_boundary"},
            {"path": "specs/02-AI行为规范.md", "role": "ai_behavior_requirements"},
            {"path": "specs/03-事实源与Git溯源规范.md", "role": "fact_source_traceability"},
            {"path": "specs/04-Specs基础规范.md", "role": "specs_structure"},
            {"path": "specs/05-事实模型基础规范.md", "role": "fact_model_foundation"},
            {"path": "specs/06-行动模板基础规范.md", "role": "action_template_foundation"},
            {"path": "specs/07-Code确定性执行规范.md", "role": "code_determinism"},
            {"path": "specs/08-Web信息同步规范.md", "role": "web_sync"},
            {"path": "specs/09-测试与验证规范.md", "role": "test_verification"},
            {"path": "specs/21-WorkCase-工作项.md", "role": "workcase_member_spec"},
            {"path": TIMING_TABLE_PATH, "role": "consumption_timing_registry"},
            {"path": TAKEOVER_MATRIX_PATH, "role": "takeover_matrix"},
        ],
        "specs": [obj.to_dict() for obj in specs],
        "attachments": [obj.to_dict() for obj in attachments],
        "consumption_timings": timings,
        "ai_behavior_requirements": requirements,
        "takeover_matrix": takeover_matrix,
        "foundation_spec_contracts": foundation_spec_contracts,
        "git_commit_action_template": git_commit_action_template,
        "workcase_member_contract": workcase_member_contract,
        "attachment_contracts": attachment_contracts,
        "diagnostics": diagnostic_dicts,
    }


def priority_for_ref(path: str, requirement_id: str) -> str:
    if path in {"specs/00-理念与构成.md", "specs/01-保障与衔接.md", "specs/02-AI行为规范.md"}:
        return "P0"
    if requirement_id in {"AI-BEH-001", "AI-BEH-002", "AI-BEH-003", "AI-BEH-004"}:
        return "P1"
    return "P2"


def action_guide_next_action(timing: str, missing_fields: list[dict[str, str]]) -> str:
    if missing_fields:
        return "先补齐 missing_fields；影响写入、提交或完成声明时暂停并分流。"
    if timing == "session_start":
        return "先读取 P0/P1 task_read_plan，再进入实质行动。"
    if timing == "pre_tool_use":
        return "确认 target、读取证据和阻断条件后，输出阻断、分流或需交还 Human 的判断。"
    if timing == "git_commit_msg":
        return "确认 read_plan 消费证据、staged paths 和提交说明后，再提交。"
    if timing == "completion_claim":
        return "先完成 validation_guard，说明未验证范围和残留风险后再声明完成。"
    return "按 task_read_plan 读取来源，处理 stop_conditions，再执行当前行动。"


def capability_gaps_for_requirement(requirement: dict[str, Any]) -> list[dict[str, str]]:
    raw_capability = requirement["required_capability"]
    gap_markers = ("Hook", "dispatcher", "receipt", "环境入口", "Git hook", "pre-tool-use", "commit validator")
    if any(marker in raw_capability for marker in gap_markers):
        return [
            {
                "requirement_id": requirement["requirement_id"],
                "required_capability": raw_capability,
                "current_gap": "当前阶段仅生成只读 Action Guide；运行时拦截、receipt 写入、Hook 和提交门禁由后续阶段承接。",
                "disposition": "保留为 capability_gap，不得声称对应运行时能力已经生效。",
            }
        ]
    return []


def build_action_guide(
    root: Path = ROOT,
    consumption_timing: str = "session_start",
    task: str = "",
    target_path: str = "",
    trigger_source: str = "manual",
) -> dict[str, Any]:
    validation = build_validation(root)
    allowed_timings = {row["consumption_timing"] for row in validation["consumption_timings"]}
    all_requirements = validation["ai_behavior_requirements"]
    requirements = [
        requirement
        for requirement in all_requirements
        if requirement["consumption_timing"] == consumption_timing
    ]

    missing_fields: list[dict[str, str]] = []
    guide_diagnostics: list[dict[str, str]] = []
    if consumption_timing not in allowed_timings:
        missing_fields.append({
            "field": "consumption_timing",
            "reason": f"消费时机不在 01.Att.01 闭集内: {consumption_timing}",
        })
        guide_diagnostics.append(
            Diagnostic(
                "error",
                "ACTION_GUIDE_TIMING_UNKNOWN",
                TIMING_TABLE_PATH,
                f"未知消费时机: {consumption_timing}",
            ).to_dict()
        )
        requirements = []

    if consumption_timing in {"pre_tool_use", "git_commit_msg"} and not target_path:
        missing_fields.append({
            "field": "target_path",
            "reason": "写入或提交前需要明确 target/staged paths，当前输入未提供。",
        })

    task_read_plan: list[dict[str, Any]] = []
    source_refs = [dict(ref) for ref in BASE_ACTION_GUIDE_SOURCE_REFS]
    stop_conditions: list[dict[str, str]] = []
    validation_guard: list[dict[str, str]] = []
    capability_gap: list[dict[str, str]] = []

    for requirement in requirements:
        requirement_id = requirement["requirement_id"]
        source_refs.append({
            "path": requirement["source_path"],
            "role": "requirement_source",
            "requirement_id": requirement_id,
        })

        for source in requirement["required_sources"]:
            normalized = normalize_required_source_ref(source, requirement["source_path"])
            path = normalized["path"]
            if path:
                source_refs.append({
                    "path": path,
                    "role": "required_source",
                    "requirement_id": requirement_id,
                })
            task_read_plan.append({
                "priority": priority_for_ref(path, requirement_id),
                "role": "required_source",
                "source_type": normalized["type"],
                "path": path,
                "label": normalized["label"],
                "requirement_id": requirement_id,
                "reason": requirement["requirement"],
            })

        for condition in requirement["blocking_conditions"]:
            stop_conditions.append({
                "requirement_id": requirement_id,
                "condition": condition,
                "disposition": "触发时暂停、分流或进入 Human Gate，不得声明完成。",
            })

        validation_guard.append({
            "requirement_id": requirement_id,
            "guard": requirement["completion_evidence"],
            "source_path": requirement["source_path"],
        })
        capability_gap.extend(capability_gaps_for_requirement(requirement))

    if not task_read_plan and consumption_timing in allowed_timings:
        for path in ("specs/00-理念与构成.md", "specs/01-保障与衔接.md", "specs/02-AI行为规范.md"):
            task_read_plan.append({
                "priority": "P0",
                "role": "fallback_source",
                "source_type": "spec",
                "path": path,
                "label": path,
                "requirement_id": "",
                "reason": "未定位到匹配保障需求时的 fallback read_plan。",
            })
        capability_gap.append({
            "requirement_id": "",
            "required_capability": "Action Guide requirement matching",
            "current_gap": "未定位到匹配保障需求，已降级为 00/01/02 fallback read_plan。",
            "disposition": "不得确认空 read_plan；后续应补齐对应保障需求。",
        })

    next_queries: list[dict[str, str]] = []
    if target_path:
        next_queries.append({
            "query": "target_impact",
            "target_path": target_path,
            "reason": "后续阶段用于定位 target 对 specs、Code、事实源或环境入口的影响。",
        })
    else:
        next_queries.append({
            "query": "provide_target",
            "reason": "若当前行动涉及写入、提交或完成声明，应补充 target/staged paths。",
        })

    impact_paths = sorted(
        {
            item["path"]
            for item in task_read_plan
            if item.get("path")
        }
    )
    diagnostics = validation["diagnostics"] + guide_diagnostics
    status = "ok" if not diagnostics else "failed"

    return {
        "metadata": {
            "read_only": True,
            "authority": "derived_from_specs_markdown",
            "authorization": "none",
            "root": root.as_posix(),
        },
        "summary": {
            "status": status,
            "consumption_timing": consumption_timing,
            "requirements": len(requirements),
            "task_read_plan": len(task_read_plan),
            "missing_fields": len(missing_fields),
            "capability_gap": len(capability_gap),
            "diagnostics": len(diagnostics),
        },
        "input": {
            "task": task,
            "target_path": target_path,
            "trigger_source": trigger_source,
            "consumption_timing": consumption_timing,
        },
        "requirements": requirements,
        "task_read_plan": unique_dicts(task_read_plan, ("priority", "role", "source_type", "path", "label", "requirement_id")),
        "next_queries": next_queries,
        "stop_conditions": unique_dicts(stop_conditions, ("requirement_id", "condition")),
        "validation_guard": validation_guard,
        "next_action": action_guide_next_action(consumption_timing, missing_fields),
        "missing_fields": missing_fields,
        "capability_gap": unique_dicts(capability_gap, ("requirement_id", "required_capability")),
        "impact_summary": {
            "affected_paths": impact_paths,
            "affected_path_count": len(impact_paths),
            "requirement_ids": [requirement["requirement_id"] for requirement in requirements],
        },
        "source_refs": unique_dicts(source_refs, ("path", "role", "requirement_id")),
        "diagnostics": diagnostics,
    }


def classify_target_path(target_path: str) -> dict[str, str]:
    normalized = target_path.strip().lstrip("./")
    if not normalized:
        return {
            "target_path": "",
            "target_type": "unknown",
            "impact": "unknown",
            "reason": "未提供 target_path，无法判断写入对象。",
        }
    if normalized in HIGH_IMPACT_SPEC_PATHS:
        return {
            "target_path": normalized,
            "target_type": "core_spec",
            "impact": "high",
            "reason": "目标属于 00/01/02/03/04 核心规范，可能影响上位价值、保障、事实源、结构或 AI 行为边界。",
        }
    if normalized.startswith("specs/attachments/"):
        return {
            "target_path": normalized,
            "target_type": "attachment",
            "impact": "medium",
            "reason": "目标属于授权附件，必须保持从属边界，不得承载上位规则或行动流程。",
        }
    if normalized.startswith("specs/") and normalized.endswith(".md"):
        return {
            "target_path": normalized,
            "target_type": "spec",
            "impact": "medium",
            "reason": "目标属于正式 specs，需要检查价值、权威、归口、保障和验证边界。",
        }
    if normalized.startswith("code/"):
        return {
            "target_path": normalized,
            "target_type": "code",
            "impact": "medium",
            "reason": "目标属于正式 Code，输出不得替代 specs、Human Gate 或事实源。",
        }
    if normalized.startswith("tests/"):
        return {
            "target_path": normalized,
            "target_type": "tests",
            "impact": "low",
            "reason": "目标属于测试，提供验证证据但不得替代 Human Gate。",
        }
    if normalized.startswith("_migration/"):
        return {
            "target_path": normalized,
            "target_type": "migration",
            "impact": "low",
            "reason": "目标属于迁移材料，只能作为临时证据，不授权正式规则或 Code 行为。",
        }
    return {
        "target_path": normalized,
        "target_type": "unknown",
        "impact": "unknown",
        "reason": "目标不在当前 preflight 已知归口内，需要 AI 判断归口或进入 Human Gate。",
    }


def preflight_read_plan_for_target(classification: dict[str, str]) -> list[dict[str, str]]:
    target_path = classification["target_path"]
    target_type = classification["target_type"]
    read_paths = list(PREFLIGHT_BASE_READ_PATHS)
    read_paths.extend(PREFLIGHT_TYPE_READ_PATHS.get(target_type, []))
    if target_type in {"spec", "core_spec", "attachment"} and target_path:
        read_paths.append(target_path)
    if target_type == "migration":
        read_paths.append("_migration/v3-migration-execution-plan.md")
    return [
        {
            "priority": "P0" if path in PREFLIGHT_BASE_READ_PATHS else "P1",
            "path": path,
            "role": "preflight_required_source",
        }
        for path in dict.fromkeys(read_paths)
    ]


def build_preflight(
    root: Path = ROOT,
    target_path: str = "",
    operation: str = "write",
    task: str = "",
    trigger_source: str = "manual",
    high_impact: bool = False,
) -> dict[str, Any]:
    validation = build_validation(root)
    classification = classify_target_path(target_path)
    action_guide = build_action_guide(
        root,
        consumption_timing="pre_tool_use",
        task=task,
        target_path=classification["target_path"],
        trigger_source=trigger_source,
    )

    diagnostics: list[dict[str, str]] = list(validation["diagnostics"])
    target_type = classification["target_type"]
    impact = classification["impact"]
    normalized_target = classification["target_path"]

    if target_type == "unknown":
        diagnostics.append({
            "level": "blocking",
            "code": "PREFLIGHT_TARGET_UNKNOWN",
            "path": normalized_target,
            "message": "无法判断 target 归口；写入前必须补充明确 target 或交还 Human 判断。",
            "disposition": "blocking",
        })

    if target_type == "core_spec" or high_impact:
        diagnostics.append({
            "level": "warning",
            "code": "PREFLIGHT_HUMAN_GATE_RISK",
            "path": normalized_target,
            "message": "目标可能改变 00/01/02/03/04 的上位结构、保障、事实源、规格或 AI 行为边界；需要评估 Human Gate。",
            "disposition": "human_gate_review",
        })

    if target_type == "attachment":
        diagnostics.append({
            "level": "warning",
            "code": "PREFLIGHT_ATTACHMENT_BOUNDARY",
            "path": normalized_target,
            "message": "附件只能承载正文授权的表格、字段闭集或枚举，不得承载核心规则、行动流程或 Human Gate。",
            "disposition": "boundary_review",
        })

    if target_type == "code":
        diagnostics.append({
            "level": "unverifiable",
            "code": "PREFLIGHT_CODE_OUTPUT_NOT_AUTHORIZATION",
            "path": normalized_target,
            "message": "当前 preflight 只能诊断 Code 写入风险，不能授权、放行或替代 Human Gate。",
            "disposition": "keep_ai_judgment",
        })

    if target_type == "migration":
        diagnostics.append({
            "level": "follow_up",
            "code": "PREFLIGHT_MIGRATION_NOT_AUTHORITY",
            "path": normalized_target,
            "message": "迁移材料是临时证据；有效决定必须由正式 specs、Code 或 tests 承接。",
            "disposition": "track_absorption",
        })

    required_read_plan = preflight_read_plan_for_target(classification)
    source_refs = unique_dicts(
        [
            {"path": item["path"], "role": item["role"]}
            for item in required_read_plan
        ]
        + [
            {"path": "specs/01-保障与衔接.md", "role": "preflight_assurance_boundary"},
            {"path": "specs/04-Specs基础规范.md", "role": "preflight_structure_boundary"},
            {"path": "specs/02-AI行为规范.md", "role": "preflight_ai_behavior_boundary"},
        ],
        ("path", "role"),
    )

    blocking_count = sum(1 for diagnostic in diagnostics if diagnostic["level"] == "blocking")
    human_gate_risks = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic.get("disposition") == "human_gate_review"
    ]
    status = "blocked" if blocking_count else "review_required" if diagnostics else "diagnostic_clear"

    return {
        "metadata": {
            "read_only": True,
            "authority": "derived_from_specs_markdown",
            "authorization": "none",
            "root": root.as_posix(),
        },
        "summary": {
            "status": status,
            "operation": operation,
            "target_type": target_type,
            "impact": impact,
            "diagnostics": len(diagnostics),
            "blocking": blocking_count,
            "warnings": sum(1 for diagnostic in diagnostics if diagnostic["level"] == "warning"),
            "follow_up": sum(1 for diagnostic in diagnostics if diagnostic["level"] == "follow_up"),
            "unverifiable": sum(1 for diagnostic in diagnostics if diagnostic["level"] == "unverifiable"),
            "human_gate_risks": len(human_gate_risks),
        },
        "input": {
            "target_path": normalized_target,
            "operation": operation,
            "task": task,
            "trigger_source": trigger_source,
            "high_impact": high_impact,
        },
        "target": classification,
        "required_read_plan": required_read_plan,
        "action_guide": {
            "summary": action_guide["summary"],
            "task_read_plan": action_guide["task_read_plan"],
            "stop_conditions": action_guide["stop_conditions"],
            "missing_fields": action_guide["missing_fields"],
            "capability_gap": action_guide["capability_gap"],
        },
        "validation_guard": [
            {
                "guard": "确认价值门、权威依据、归口边界、保障需求、验证方法和 Stop Conditions。",
                "source_path": "specs/01-保障与衔接.md",
            },
            {
                "guard": "确认 Code、测试、review 或行动指南没有替代 Human Gate 或事实源。",
                "source_path": "specs/02-AI行为规范.md",
            },
        ],
        "human_gate_risks": human_gate_risks,
        "source_refs": source_refs,
        "diagnostics": diagnostics,
    }


def normalize_path_list(paths: list[str] | None) -> list[str]:
    if not paths:
        return []
    normalized: list[str] = []
    for value in paths:
        for part in re.split(r"[,，]", value):
            stripped = part.strip().lstrip("./")
            if stripped:
                normalized.append(stripped)
    return list(dict.fromkeys(normalized))


def receipt_id_for(
    event: str,
    trigger_source: str,
    session_id: str,
    target_path: str,
    acknowledged_paths: list[str],
    verification_evidence: list[str],
) -> str:
    raw = "\0".join([
        event,
        trigger_source,
        session_id,
        target_path,
        "|".join(acknowledged_paths),
        "|".join(verification_evidence),
    ])
    return "ldvh-rt-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def runtime_status_from_diagnostics(
    diagnostics: list[dict[str, str]],
    preflight: dict[str, Any] | None,
) -> str:
    if any(diagnostic["level"] in {"error", "blocking"} for diagnostic in diagnostics):
        return "blocked"
    if preflight and preflight["summary"]["status"] in {"blocked", "review_required"}:
        return preflight["summary"]["status"]
    if diagnostics:
        return "review_required"
    return "ok"


def build_runtime_event(
    root: Path = ROOT,
    event: str = "session_start",
    trigger_source: str = "manual",
    session_id: str = "",
    target_path: str = "",
    task: str = "",
    operation: str = "write",
    acknowledged_paths: list[str] | None = None,
    verification_evidence: list[str] | None = None,
) -> dict[str, Any]:
    validation = build_validation(root)
    allowed_events = {row["consumption_timing"] for row in validation["consumption_timings"]}
    normalized_event = event.strip()
    normalized_target = target_path.strip().lstrip("./")
    normalized_ack_paths = normalize_path_list(acknowledged_paths)
    normalized_verification_evidence = normalize_path_list(verification_evidence)

    diagnostics: list[dict[str, str]] = list(validation["diagnostics"])
    action_guide: dict[str, Any] | None = None
    preflight: dict[str, Any] | None = None

    if normalized_event not in allowed_events:
        diagnostics.append({
            "level": "blocking",
            "code": "RUNTIME_EVENT_UNKNOWN",
            "path": TIMING_TABLE_PATH,
            "message": f"runtime event 不在消费时机闭集内: {normalized_event}",
            "disposition": "blocking",
        })
    else:
        action_guide = build_action_guide(
            root,
            consumption_timing=normalized_event,
            task=task,
            target_path=normalized_target,
            trigger_source=trigger_source,
        )
        diagnostics.extend(action_guide["diagnostics"])

        if normalized_event == "acknowledge_read_plan":
            missing_required = [
                path
                for path in RUNTIME_REQUIRED_ENTRY_PATHS
                if path not in normalized_ack_paths
            ]
            if not normalized_ack_paths:
                diagnostics.append({
                    "level": "blocking",
                    "code": "RUNTIME_ACK_REQUIRED_PATHS_EMPTY",
                    "path": "runtime://acknowledge_read_plan",
                    "message": "acknowledge_read_plan 必须提供已消费的 required paths。",
                    "disposition": "blocking",
                })
            elif missing_required:
                diagnostics.append({
                    "level": "blocking",
                    "code": "RUNTIME_ACK_REQUIRED_PATHS_INCOMPLETE",
                    "path": "runtime://acknowledge_read_plan",
                    "message": "acknowledge_read_plan 缺少入口必读路径: " + "；".join(missing_required),
                    "disposition": "blocking",
                })

        if normalized_event in {"pre_tool_use", "git_commit_msg"}:
            missing_required = [
                path
                for path in RUNTIME_REQUIRED_ENTRY_PATHS
                if path not in normalized_ack_paths
            ]
            if not normalized_ack_paths:
                diagnostics.append({
                    "level": "blocking",
                    "code": "RUNTIME_READ_PLAN_CONSUMED_EMPTY",
                    "path": f"runtime://{normalized_event}",
                    "message": f"{normalized_event} 必须提供 read_plan 消费证据。",
                    "disposition": "blocking",
                })
            elif missing_required:
                diagnostics.append({
                    "level": "blocking",
                    "code": "RUNTIME_READ_PLAN_CONSUMED_INCOMPLETE",
                    "path": f"runtime://{normalized_event}",
                    "message": f"{normalized_event} 缺少入口必读路径: " + "；".join(missing_required),
                    "disposition": "blocking",
                })
            preflight = build_preflight(
                root,
                target_path=normalized_target,
                operation="commit" if normalized_event == "git_commit_msg" else operation,
                task=task,
                trigger_source=trigger_source,
            )
            diagnostics.extend(preflight["diagnostics"])

        if normalized_event == "completion_claim" and not normalized_verification_evidence:
            diagnostics.append({
                "level": "blocking",
                "code": "RUNTIME_COMPLETION_VERIFICATION_MISSING",
                "path": "runtime://completion_claim",
                "message": "completion_claim 必须提供验证证据、未验证范围或残留风险说明。",
                "disposition": "blocking",
            })

    status = runtime_status_from_diagnostics(diagnostics, preflight)
    receipt_status = "blocked" if status == "blocked" else "generated"
    source_refs = [
        {"path": "specs/01-保障与衔接.md", "role": "runtime_protocol_boundary"},
        {"path": "specs/02-AI行为规范.md", "role": "runtime_behavior_requirement"},
        {"path": TIMING_TABLE_PATH, "role": "canonical_event_registry"},
    ]
    if action_guide:
        source_refs.extend(action_guide["source_refs"])
    if preflight:
        source_refs.extend(preflight["source_refs"])

    receipt = {
        "receipt_id": receipt_id_for(
            normalized_event,
            trigger_source,
            session_id,
            normalized_target,
            normalized_ack_paths,
            normalized_verification_evidence,
        ),
        "receipt_type": "runtime_event",
        "status": receipt_status,
        "persistent": False,
        "storage": "stdout_only",
        "canonical_event": normalized_event,
        "trigger_source": trigger_source,
        "session_id": session_id,
        "target_path": normalized_target,
        "acknowledged_paths": normalized_ack_paths,
        "verification_evidence": normalized_verification_evidence,
        "boundary": "receipt 是过程输出，不是事实源、授权、放行、Human Gate 或完成证明。",
    }

    return {
        "metadata": {
            "read_only": True,
            "authority": "derived_from_specs_markdown",
            "environment_integrated": False,
            "authorization": "none",
            "root": root.as_posix(),
        },
        "summary": {
            "status": status,
            "event": normalized_event,
            "trigger_source": trigger_source,
            "diagnostics": len(diagnostics),
            "blocking": sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"error", "blocking"}),
            "receipt_status": receipt_status,
            "has_action_guide": action_guide is not None,
            "has_preflight": preflight is not None,
        },
        "input": {
            "event": normalized_event,
            "trigger_source": trigger_source,
            "session_id": session_id,
            "target_path": normalized_target,
            "task": task,
            "operation": operation,
            "acknowledged_paths": normalized_ack_paths,
            "verification_evidence": normalized_verification_evidence,
        },
        "receipt": receipt,
        "action_guide": action_guide,
        "preflight": preflight,
        "source_refs": unique_dicts(source_refs, ("path", "role", "requirement_id")),
        "diagnostics": diagnostics,
    }
