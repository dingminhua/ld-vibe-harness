from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]

TIMING_TABLE_PATH = "specs/attachments/01.Att.01-保障消费时机表.md"
TAKEOVER_MATRIX_PATH = "specs/attachments/01.Att.02-保障机制承接矩阵.md"
AI_BEHAVIOR_SPEC_PATH = "specs/02-AI行为规范.md"
COMMIT_MESSAGE_CONTRACT_PATH = "specs/attachments/03.Att.01-Commit-Message契约字段表.md"
FIELD_REGISTRY_CONTRACT_PATH = "specs/attachments/05.Att.01-字段注册表结构.md"
VERIFICATION_CLAIM_FIELDS_PATH = "specs/attachments/09.Att.01-验证声明字段表.md"
GOVERNED_PROJECTS_CONFIG_PATH = "LDVH-GOVERNED-PROJECTS.yaml"
GOVERNED_PROJECTS_CONTRACT_PATH = "specs/attachments/10.Att.01-管辖项目配置字段表.md"

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
    "10": "specs/10-管辖项目配置规范.md",
    "30": "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
    "31": "specs/31-环境Hook接入后验收行动模板.md",
    "20": "specs/20-Spark-火花.md",
    "21": "specs/21-WorkCase-工作项.md",
    "22": "specs/22-ADR-决策.md",
    "23": "specs/23-Pitfall-踩坑经验.md",
    "24": "specs/24-Study-研究报告.md",
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
COMMIT_HEADER_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z0-9_-]+)\))?(?P<breaking>!)?: (?P<description>.+)$"
)
COMMIT_REQUIRED_BODY_HEADING = "关键变更"
FIELD_REGISTRY_COLUMNS = ["列", "含义"]
FIELD_REGISTRY_ALLOWED_COLUMNS = ["注册列", "允许值或写法"]
FIELD_REGISTRY_CODE_CHECK_COLUMNS = ["code_check_kind", "可机械消费维度", "边界"]
VERIFICATION_CLAIM_COLUMNS = ["字段", "要求"]
VERIFICATION_COMPLETE_CONDITION_COLUMNS = ["条件", "内容"]
VERIFICATION_FORBIDDEN_COLUMNS = ["写法", "边界"]
GOVERNED_PROJECT_ROOT_COLUMNS = ["根字段", "要求", "说明"]
GOVERNED_PROJECT_ITEM_COLUMNS = ["项目字段", "要求", "说明"]
GOVERNED_PROJECT_GIT_COLUMNS = ["Git字段", "要求", "说明"]
GOVERNED_PROJECT_RESOLUTION_COLUMNS = ["resolution字段", "要求", "说明"]
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
    "Context": ["Git 工作区摘要", "staged", "diff", "source_refs", "03.Att.01", "09.Att.01"],
    "Scenario": ["用户明确要求提交", "修复提交消息", "拆分已暂存变更", "只回答 03/09 边界"],
    "Gate": ["已暂存变更", "提交拆分边界不清", "破坏性 Git", "commit validator", "失败测试", "Human Gate", "Hook/commit gate/环境入口"],
    "执行": ["Git 工作区摘要", "diff", "拆分", "03.Att.01", "单一 type", "scope", "关键变更", "commit validator", "不安装 Hook"],
    "验证": ["测试或命令", "09.Att.01", "验证目标", "验证入口", "残留风险", "证据回指", "不得声明完整验证"],
    "回写": ["过程输出", "事实源", "事实对象", "Git commit records", "不替代事实对象或验证声明"],
    "交还": ["commit hash", "验证摘要", "残留风险", "Git 工作区摘要", "source_refs", "执行方式", "阻断原因"],
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
LDVH_INSTALL_ACTION_TEMPLATE_REQUIRED_ROWS = {
    "Context": ["用户目标", "目标环境", "LDVH 本体路径", "目标工作区根目录", "管辖项目候选", "LDVH-GOVERNED-PROJECTS.yaml", "ldvh-base/", "workcases/adrs/pitfalls/sparks/studies", "环境入口审计结果", "Git Hook 状态", "source_refs", "specs/10-管辖项目配置规范.md", "code/docs/03-LDVH-Install-Wizard-Practice.md"],
    "Scenario": ["安装 LDVH", "接入 LDVH", "初始化 LDVH", "配置管辖项目", "旧插件 / 旧路径", "只回答 01/06/10 边界"],
    "Gate": ["Human Gate", "环境入口", "LDVH 插件 / 扩展包", "管辖项目 Git Hook", "有效 Git worktree", "LDVH-GOVERNED-PROJECTS.yaml", "ldvh-base/", "事实源子目录", "LDVH 本体路径", "目标工作区根目录", "配置层级冲突", "授权 / trust", "记录 lifecycle 验收", "integrated", "多项目", "用户告知清单", "安装方案预览", "最终确认"],
    "执行": ["bootstrap discovery", "有限、只读、有证据", "LDVH_ROOT", "候选路径和证据", "01", "支持 Hook", "LDVH 插件 / 扩展包 / package", "不直接写入环境 Hook 系统文件", "用户告知清单", "安装方案预览", "workcases/adrs/pitfalls/sparks/studies", "AI 环境 Hook", "Git `commit-msg` Hook", "无 Hook 环境分支", "repo instruction", "manual entrypoint", "thin-reference-ready", "外部 adapter 候选", "不进入 31", "不恢复 Rules 顶层机制", "目标工作区根目录", "配置文件完整路径", "项目根目录、用户级目录和 LDVH 本体目录不得作为主选项", "配置层级检查", "目标项目内已存在配置", "10", "Git common-dir", "target-first resolver"],
    "验证": ["install_verification.py", "environment_lifecycle_acceptance.py", "environment_status.py", "environment_entry_audit.py", "specs_validate.py governed-projects", "target-first resolution", "ldvh-base/", "governed_hook_adapter.py status", "governed_hook_adapter.py verify", "managed `commit-msg` hook", "正反样例", "runtime adapter", "AI 环境 Hook 安装检测通过", "插件页面状态", "重启 App", "授权 / trust", "用户侧冒烟检查", "lifecycle 验收", "真实 lifecycle 触发", "正常判断标准", "09 验证声明字段", "真实自动触发", "失败可阻断", "安装状态可复现", "environment_lifecycle_acceptance_valid", "integrated"],
    "回写": ["过程输出", "Human 确认", "LDVH-GOVERNED-PROJECTS.yaml", "10 字段契约", "事实源目录创建", "不创建事实实例", "旧插件", "用户级配置目录候选", "Spark", "ADR", "Pitfall", "WorkCase", "Git commit records", "不得把 runtime receipt"],
    "交还": ["安装方式", "配置位置选择", "管辖项目 ID", "Git common-dir", "ldvh-base/", "事实源子目录状态", "环境入口状态", "integrated / manual_ready / repo-instruction-ready / thin-reference-ready / external-adapter-candidate / deferred / removed_top_level", "无 Hook 环境分支", "不会自动阻断", "不得交还进入 31", "用户告知清单", "验证摘要", "回滚或卸载入口", "下一步 Human Gate", "source_refs"],
}
LDVH_INSTALL_REQUIRED_CODE_CONSUMPTION = [
    "ldvh_spec_metadata",
    "ldvh_install_initialization_action_template",
    "install_wizard_state_machine",
    "install_user_disclosure_checklist",
    "environment_plugin_install_boundary",
    "governed_project_config_location_gate",
    "install_verification_handoff",
    "stop_conditions",
]
LDVH_INSTALL_WIZARD_TERMS = [
    "安装向导状态机",
    "五步",
    "路径确认",
    "安装前检查",
    "安装选项",
    "安装方案预览",
    "最终确认",
    "决策 / 结果",
    "状态、步骤、决策 / 结果三列",
    "👉",
    "✅",
    "尚未发生的步骤保持空白",
    "不写“待进行 / 待选择 / 待确认”",
    "用户视角摘要",
    "用户验收卡片",
    "本步目的",
    "不会做什么",
    "需要决定什么",
    "你需要确认什么",
    "为什么需要你确认",
    "选择后会发生什么",
    "看到什么算正常",
    "失败时把什么发给 AI",
    "主界面不得裸露 raw diagnostic",
    "进度安全提示",
    "当前已完成几步",
    "选择框 / 单选控件",
    "每次只问一个问题",
    "选项表必须给出选项、说明和结果",
    "不得把“返回修改”写成第三个主选项",
    "方案确认和执行确认",
    "4/5 安装方案预览只能询问“是否进入最终确认”",
    "该选择不是执行授权",
    "不得用“执行方案”或其它会让 Human 误以为已经授权写入的措辞",
    "5/5 最终确认必须直接询问“执行方案”或“不执行，停止安装”",
    "不得再次要求 Human 确认只读检查",
    "不得继续解释流程或再次索要同一授权",
    "📍 路径确认",
    "🔎 安装前检查",
    "⚙️ 安装选项",
    "🔒 安装方案预览",
    "🛠️ 最终确认",
    "📦 LDVH 本体路径",
    "🗂️ 目标工作区根目录",
    "🧾 配置文件完整路径",
    "✅ 通过",
    "⚠️ 注意",
    "⚠️ 需安装",
    "⚠️ 需升级",
    "⛔ 阻断",
    "➖ 不适用",
    "下一步处理",
    "状态图例",
    "是否阻断",
    "`⚠️ 注意` 只表示需知情或需关注，不自动阻断",
    "`⚠️ 需安装` 和 `⚠️ 需升级` 必须进入安装方案预览",
    "🔌 环境入口",
    "🪝 Git Hook",
    "🗑️ 项目内旧配置",
    "🪝 管辖项目 Git Hook",
    "🧪 验证",
    "↩️ 回滚",
    "系统已检查事实",
    "需授权动作",
    "不得把事实伪装成 Human 选项",
    "环境插件未安装时必须标为 `⚠️ 需安装` 并安排安装方案",
    "环境插件已安装但指向旧路径、旧版本或 stale V2 path 时必须标为 `⚠️ 需升级` 并安排升级方案",
    "每个已选择管辖项目都必须检查 Git `commit-msg` Hook 状态",
    "非 Git 目录必须标为 `⛔ 阻断` 并说明管辖项目必须是 Git 仓库",
    "不得把这类情况表达成“不安装插件”“不处理插件”或“Git Hook 后置可不做”",
    "当前配置项目清单",
    "不得只写“保留工作区配置”",
    "product_name",
    "product_description",
    "编号",
    "项目 ID",
    "项目路径",
    "Git common-dir",
    "是否已设置为管辖项目",
    "不得展示“当前目标”列",
    "1 不改管辖项目配置",
    "2 按编号设置管辖项目",
    "编号列表",
    "配置正确性结论",
    "字段闭集",
    "项目 ID 唯一",
    "target-first 解析结论",
    "拟写入项目清单",
    "LDVH 本体路径",
    "目标工作区路径",
    "bootstrap discovery",
    "有限、只读、有证据",
    "找不到时必须要求 Human 提供 LDVH 本体路径",
    "工作区根目录",
    "配置位置不是选项，只能是目标工作区根目录",
    "项目根目录、用户级目录和 LDVH 本体目录都不是支持位置",
    "AI 必须用表格展示 LDVH 本体路径、目标工作区根目录、配置文件完整路径、说明、限制和建议",
    "可复制路径块",
    "LDVH_ROOT=<ldvh-root>",
    "WORKSPACE_ROOT=<workspace-root>",
    "GOVERNED_CONFIG=<workspace-root>/LDVH-GOVERNED-PROJECTS.yaml",
    "配置层级冲突",
    "先删除、迁移或明确保留其中一个配置文件",
    "完整安装方案必须同时覆盖 AI 环境 Hook 和管辖项目 Git Hook",
    "repo 路径",
    "`core.hooksPath` / active hook 状态",
    "install_verification.py",
    "验证命令和卸载 / rollback 命令",
    "主界面只展示普通用户作出下一步判断所需的信息",
    "会改变什么",
    "不会改变什么",
    "执行后还需要验证什么",
    "技术明细",
    "净变化",
    "将新增",
    "将修改或升级",
    "将保持不变",
    "不会执行",
    "需后置确认",
    "不可验证范围",
    "不得混入“验证通过”",
    "环境 Hook 或插件提示必须按当前目标环境命名",
    "目标环境确认不支持 Hook",
    "30 必须走无 Hook 环境分支",
    "该分支不是降级",
    "不单独开 32",
    "也不得交给 31",
    "可用但不自动拦截",
    "手动可用",
    "AI 可以读取 LDVH 规则",
    "你或 AI 可以手动运行检查命令",
    "当前目标环境不会在写入前自动拦截",
    "1 按手动可用方式完成安装交还",
    "2 暂停，等目标环境 Hook 支持",
    "repo-instruction-ready",
    "thin-reference-ready",
    "external-adapter-candidate",
    "不会自动阻断写入或完成声明",
    "当前 AI 运行环境名称",
    "不得沿用示例环境名称",
    "只有当前运行环境、环境审计或 Human 明确目标环境为 Codex",
    "目标环境插件 / 工具入口插件",
    "插件页面 / 扩展页面或插件管理器入口",
    "重启 App",
    "授权 / trust",
    "新开窗口或新会话",
    "安装检测标准",
    "安装检测通过",
    "lifecycle 验收",
    "environment_lifecycle_acceptance.py",
    "environment_lifecycle_acceptance_valid",
    "自动接入待验收",
    "安装完成；自动接入待验收，可进入 31",
    "安装完成；当前环境为手动可用，不会自动拦截",
    "状态牌",
    "安装完成",
    "环境自动拦截",
    "提交消息检查",
    "下一步",
    "已 integrated",
    "状态块",
    "用户下一步待办",
    "失败信息包",
    "目标环境名称和版本",
    "install_verification.py --format json",
    "environment_entry_audit.py --format text",
    "失败步骤编号",
    "scratch target 路径和文件状态",
    "必需 lifecycle Hook manifest",
    "用户侧冒烟检查",
    "不阻断安装完成",
    "正常判断标准",
    "插件页面状态",
    "V3 shim",
    "未真实写入插件包、未进入插件页面或未获得授权证据前，不得写成“插件已安装”",
    "`待用户安装`",
    "`需授权`",
    "`可见 / 需验证`",
    "`已写入但待用户授权`",
    "安装方案预览必须停止为 blocking",
    "管辖项目必须是 Git 仓库",
    "最终确认只展示两个主选项",
    "1 执行方案",
    "2 不执行，停止安装",
    "选择执行后才会开始写入",
    "最终确认摘要只列出将写入对象和不写入对象",
    "不得重复安装前检查表",
    "写入后执行验证",
    "不得把返回修改作为第三个主选项",
    "最终确认前",
    "不得写入配置",
]
LDVH_INSTALL_ACTION_TEMPLATE_BOUNDARY_TERMS = [
    "V2 `33-ldvh-install-action`",
    "受 V3 01",
    "V3 01、06、10",
    "安装、部署、初始化、配置或卸载前",
    "用户告知清单",
    "ldvh-base/workcases/",
    "ldvh-base/adrs/",
    "ldvh-base/pitfalls/",
    "ldvh-base/sparks/",
    "ldvh-base/studies/",
    "不越过 Human Gate 直接安装或升级环境插件",
    "不直接写入用户环境 Hook 系统文件",
    "不声明 integrated",
    "不恢复 Rules / Skill 顶层机制",
    "V2 `32-environment-entry-adaptation`",
]
LDVH_INSTALL_CODE_CONSUMPTION_SUPPORT_TERMS = {
    "install_user_disclosure_checklist": [
        "用户告知清单",
        "写入位置",
        "受影响项目",
        "验证命令",
        "回滚或卸载入口",
        "残留风险",
    ],
    "environment_plugin_install_boundary": [
        "环境插件",
        "stale V2 path",
        "`⚠️ 需安装`",
        "`⚠️ 需升级`",
        "插件页面状态",
        "重启 App",
        "授权 / trust",
        "安装检测通过",
        "environment_lifecycle_acceptance.py",
        "environment_lifecycle_acceptance_valid",
        "lifecycle 验收",
        "必需 Hook manifest 不完整",
        "用户侧冒烟检查",
        "不声明 integrated",
        "目标环境确认不支持 Hook",
        "无 Hook 环境分支",
        "thin-reference-ready",
        "不得交还进入 31",
    ],
    "governed_project_config_location_gate": [
        "配置位置不是选项，只能是目标工作区根目录",
        "项目根目录、用户级目录和 LDVH 本体目录都不是支持位置",
        "配置层级冲突",
    ],
    "install_verification_handoff": [
        "验证摘要",
        "Hook 接入后测试",
        "install_verification.py",
        "environment_lifecycle_acceptance.py",
        "environment_lifecycle_acceptance_valid",
        "governed_hook_adapter.py verify",
        "安装检测通过",
        "用户侧冒烟检查",
        "正常判断标准",
        "回滚或卸载入口",
        "残留风险",
        "source_refs",
    ],
}
ENV_HOOK_ACCEPTANCE_ACTION_TEMPLATE_REQUIRED_ROWS = {
    "Context": ["目标环境", "30 交还结果", "install_verification.py", "environment_hook_integrated=false", "插件页面", "Human 授权", "source_refs", "specs/30-LDVH安装初始化管辖项目配置行动模板.md"],
    "Scenario": ["30 安装检测通过", "环境 Hook 接入后验收", "lifecycle 冒烟", "只回答 01/06/09/30/31 边界"],
    "Gate": ["开始验收", "受控负例阻断", "受控正例放行", "记录 lifecycle 验收", "授权 / trust", "environment_hook_integrated", "Human Gate"],
    "执行": ["测试组状态机", "一次只判断一项", "通过 / 失败", "重启 App", "新窗口或新会话", "受控 scratch target", "不得安装", "不得升级", "不得修改用户环境", "失败即停止"],
    "验证": ["install_verification.py", "environment_lifecycle_acceptance.py", "SessionStart", "PreToolUse", "Git Hook 正反例", "environment_lifecycle_acceptance_valid=true", "environment_hook_integrated=true", "失败"],
    "回写": [".ldvh-runtime/environment-lifecycle-acceptance.json", "--confirm-human-gate", "逐项验收摘要", "不得写事实源", "不得写 specs", "不替代插件页面"],
    "交还": ["验收结果表", "通过项", "失败项", "未验证项", "environment_hook_integrated", "environment_lifecycle_acceptance_valid", "回滚或诊断入口", "source_refs"],
}
ENV_HOOK_ACCEPTANCE_REQUIRED_CODE_CONSUMPTION = [
    "ldvh_spec_metadata",
    "environment_hook_acceptance_action_template",
    "post_install_lifecycle_acceptance_flow",
    "environment_hook_acceptance_test_matrix",
    "lifecycle_acceptance_record_handoff",
    "stop_conditions",
]
ENV_HOOK_ACCEPTANCE_FLOW_TERMS = [
    "31 由 30 交接调用",
    "不安装、不升级、不禁用、不卸载",
    "测试组状态机",
    "用户验收卡片",
    "用户要做什么",
    "正常表现",
    "失败时给 AI 什么",
    "主界面不得裸露 raw diagnostic",
    "尚未发生的步骤保持空白",
    "每一步只问一个判断",
    "主界面不得要求 Human 自行理解专业“通过 / 失败”",
    "你是否看到 X",
    "AI 根据本文判断通过、失败或暂停诊断",
    "1 通过",
    "2 失败，停止验收",
    "🧭 验收授权",
    "🔌 插件页面状态",
    "🔁 重启后状态",
    "💬 新会话触发",
    "⛔ 受控负例阻断",
    "✅ 受控正例放行",
    "🧪 统一安装验证",
    "🧾 记录验收与复核",
    "harmless scratch target",
    ".ldvh-runtime/acceptance-probe/",
    "自动接入待验收",
    "当前目标环境没有可用 Hook 接入，返回 30 手动可用分支",
    "写入前检查",
    "AI 运行命令，用户只看结论",
    ".ldvh-runtime/acceptance-probe/blocked.txt",
    ".ldvh-runtime/acceptance-probe/allowed.txt",
    "测试后清理 scratch 文件",
    "失败信息包",
    "目标环境名称和版本",
    "install_verification.py --format json",
    "environment_entry_audit.py --format text",
    "失败步骤编号",
    "是否发生实际写入",
    "scratch target 路径和文件状态",
    "不得把“用户还没做完测试”写成失败",
    "不得把“用户看到了部分提示”写成全部通过",
    "失败即停止",
    "目标环境确认不支持 Hook",
    "target_environment_supported=false",
    "unsupported_target_environment",
    "返回 30 无 Hook 环境分支",
    "不得用正式 specs、事实对象、外部用户文件、管辖项目业务文件、用户环境配置或插件系统文件做正反例写入目标",
]
ENV_HOOK_ACCEPTANCE_CODE_CONSUMPTION_SUPPORT_TERMS = {
    "post_install_lifecycle_acceptance_flow": [
        "30 安装检测通过",
        "install_complete=true",
        "environment_hook_install_verified=true",
        "environment_hook_integrated=false",
        "environment_hook_integrated=true",
    ],
    "environment_hook_acceptance_test_matrix": [
        "插件页面状态",
        "重启 App",
        "新窗口或新会话",
        "SessionStart",
        "PreToolUse",
        "受控负例阻断",
        "受控正例放行",
        "统一安装验证",
    ],
    "lifecycle_acceptance_record_handoff": [
        "environment_lifecycle_acceptance.py record --confirm-human-gate",
        "environment_lifecycle_acceptance_valid=true",
        "install_verification.py --require-environment-integrated",
        ".ldvh-runtime/environment-lifecycle-acceptance.json",
    ],
}
WORKCASE_ACTION_TEMPLATE_REQUIRED_ROWS = {
    "Context": ["WorkCase ID", "对象化价值", "成功标准", "source_refs", "specs/21-WorkCase-工作项.md"],
    "Scenario": ["创建 WorkCase", "执行推进", "结果复核", "关闭确认", "只回答 21/06/09 边界"],
    "Gate": ["Human Gate", "`human_plan_confirming`", "`human_closure_confirming`", "缺少验证证据", "Web 写入", "Hook", "runtime 自动触发"],
    "执行": ["`subagents_plan_reviewing`", "`executing`", "`result_self_checking`", "`subagents_result_reviewing`", "`human_closure_confirming`", "`closed`"],
    "验证": ["09.Att.01", "状态闭集", "成功标准", "后续分流 / 收口结果", "未验证"],
    "回写": ["正式 WorkCase 事实实例", "verification_evidence", "closure_evidence", "human_closure_confirmation", "followup_refs", "Git commit records"],
    "交还": ["WorkCase ID", "当前状态", "验证摘要", "残留风险", "下一步 Human Gate", "source_refs"],
}
WORKCASE_ACTION_TEMPLATE_BOUNDARY_TERMS = [
    "manual_equivalent_execution",
    "不启用 Web 写入",
    "不安装 Hook",
    "不声明 runtime 自动触发",
    "不得替代 Human Gate",
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
IMPLEMENTATION_DOMAIN_BOUNDARY_REQUIREMENTS = [
    {
        "code": "SPECS_IMPLEMENTATION_DOMAIN_BOUNDARY_MISSING",
        "path": SHORT_SPEC_REFS["04"],
        "section": "Specs正文结构",
        "message": "04 必须声明 specs 只定义需求、规则、契约和边界，实践细节由实现域承接",
        "terms": [
            "需求、规则、契约、边界",
            "实现域实践细节",
            "`code/`",
            "`web/`",
            "`tests/`",
            "不得由实现域文档、代码、测试、review 或迁移材料反向改写 specs",
        ],
    },
    {
        "code": "CODE_IMPLEMENTATION_PRACTICE_BOUNDARY_MISSING",
        "path": SHORT_SPEC_REFS["07"],
        "section": "归口边界",
        "message": "07 必须声明 Code 实践由 code/ 和 code/docs/ 承接",
        "terms": [
            "能力契约、输入输出、诊断、source_refs、验证和越界条件",
            "具体实现语言、框架、内部模块结构",
            "`code/` 和 `code/docs/`",
            "不得反向改写 specs、事实源、Human Gate、Web 契约或测试治理",
        ],
    },
    {
        "code": "WEB_IMPLEMENTATION_PRACTICE_BOUNDARY_MISSING",
        "path": SHORT_SPEC_REFS["08"],
        "section": "归口边界",
        "message": "08 必须声明 Web 实践由 web/ 和 web/docs/ 承接",
        "terms": [
            "展示契约、来源回指、同源独立读取、受控交互、缓存和写入边界",
            "具体页面、组件、API 路由",
            "`web/` 和 `web/docs/`",
            "不得反向改写 specs、事实源、Human Gate、Code 契约或测试治理",
        ],
    },
    {
        "code": "TEST_IMPLEMENTATION_PRACTICE_BOUNDARY_MISSING",
        "path": SHORT_SPEC_REFS["09"],
        "section": "归口边界",
        "message": "09 必须声明测试实践由 tests/ 承接且不强制 tests/docs",
        "terms": [
            "验证要求、测试治理、证据边界、失败阻断、Human 验收和同步触发",
            "`tests/`",
            "fixtures、正反例、回归样例",
            "不得反向改写 specs、事实源、Human Gate、Code/Web 契约或完成声明",
            "不强制要求 `tests/docs/`",
        ],
    },
]
GOVERNED_PROJECTS_ROOT_FIELDS = {"product_name", "product_description", "projects"}
GOVERNED_PROJECTS_ITEM_FIELDS = {"id", "path", "name", "description", "git"}
GOVERNED_PROJECTS_REQUIRED_ITEM_FIELDS = {"id", "path"}
GOVERNED_PROJECTS_GIT_FIELDS = {"common_dir", "remote_url", "default_branch"}
GOVERNED_PROJECT_REQUIRED_ROOT_FIELDS = ["product_name", "product_description", "projects"]
GOVERNED_PROJECT_REQUIRED_ITEM_FIELDS = ["id", "path", "name", "description", "git"]
GOVERNED_PROJECT_REQUIRED_GIT_FIELDS = ["common_dir", "remote_url", "default_branch"]
GOVERNED_PROJECT_REQUIRED_RESOLUTION_FIELDS = [
    "target",
    "normalized_path",
    "source",
    "status",
    "governed_project_id",
    "governed_project_path",
    "governed_via",
    "git_common_dir",
    "unknown_reason",
]
GOVERNED_PROJECT_SPEC_REQUIREMENTS = [
    {
        "code": "GOVERNED_PROJECT_CONFIG_BOUNDARY_MISSING",
        "section": "管辖项目配置契约",
        "message": "10 必须定义管辖项目配置契约和事实源边界",
        "terms": [
            "LDVH-GOVERNED-PROJECTS.yaml",
            "product_name",
            "projects",
            "10.Att.01",
            "事实源",
            "不得替代事实对象",
            "只能位于目标工作区根目录",
            "项目根目录、用户级目录、LDVH 本体目录或事实源目录下的同名文件都不是 V3 支持的配置位置",
            "管辖项目必须是 Git 管理的项目",
            "项目本身不能是非 Git 目录",
            "同一路径链",
            "从根目录向深层路径",
            "多个 active `LDVH-GOVERNED-PROJECTS.yaml`",
            "先删除、迁移或明确保留其中一个",
        ],
    },
    {
        "code": "GOVERNED_PROJECT_TARGET_FIRST_MISSING",
        "section": "工作对象与判定顺序",
        "message": "10 必须定义 target-first、cwd fallback 和 Git common-dir 判定顺序",
        "terms": ["target-first", "cwd fallback", "Git common-dir", "target_resolutions", "AI 不得依据路径相似"],
    },
    {
        "code": "GOVERNED_PROJECT_MULTI_TARGET_BOUNDARY_MISSING",
        "section": "多目标与 no-op 边界",
        "message": "10 必须定义多目标、混合目标和 no-op 边界",
        "terms": ["同一管辖项目", "跨管辖项目", "管辖/非管辖混合", "no-op", "阻断"],
    },
    {
        "code": "GOVERNED_PROJECT_ENVIRONMENT_BOUNDARY_MISSING",
        "section": "事实源入口与环境引用边界",
        "message": "10 必须定义事实源入口和环境引用边界",
        "terms": [
            "ldvh-base/",
            "ldvh-base/workcases/",
            "ldvh-base/adrs/",
            "ldvh-base/pitfalls/",
            "ldvh-base/sparks/",
            "ldvh-base/studies/",
            "项目索引不得替代事实源",
            "Hook",
            "安装授权",
        ],
    },
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
FACT_MODEL_MEMBER_CONTRACTS = {
    "20": {
        "member": "Spark",
        "instance_root": "ldvh-base/sparks/",
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "fact_model_member_identity",
            "spark_admission_rules",
            "spark_source_boundaries",
            "spark_state_boundaries",
            "spark_resolution_boundaries",
            "spark_human_gate_boundaries",
            "spark_instance_checks",
            "stop_conditions",
        ],
        "required_statuses": ["pending", "resolved", "discarded"],
        "source_terms": ["ldvh-base/sparks/", "不得定义、重写或授权", "Web、Code、测试输出"],
        "closure_terms": ["resolved_to", "resolved_at", "discard_reason", "Study", "Git commit records"],
        "human_gate_terms": ["创建 Spark", "分流为 WorkCase", "标记为 `discarded`", "修改 `resolved_to`"],
        "legacy_terms": [],
        "special_terms": [],
    },
    "21": {
        "member": "WorkCase",
        "instance_root": "ldvh-base/workcases/",
        "required_code_consumption": WORKCASE_REQUIRED_CODE_CONSUMPTION,
        "required_statuses": WORKCASE_REQUIRED_STATUSES,
        "source_terms": WORKCASE_SOURCE_BOUNDARY_TERMS,
        "closure_terms": WORKCASE_CLOSURE_BOUNDARY_TERMS,
        "human_gate_terms": WORKCASE_HUMAN_GATE_TERMS,
        "legacy_terms": WORKCASE_LEGACY_STATUSES,
        "special_terms": [],
    },
    "22": {
        "member": "ADR",
        "instance_root": "ldvh-base/adrs/",
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "fact_model_member_identity",
            "adr_admission_rules",
            "adr_source_boundaries",
            "adr_state_boundaries",
            "adr_decision_boundaries",
            "adr_human_gate_boundaries",
            "adr_instance_checks",
            "stop_conditions",
        ],
        "required_statuses": ["active", "archived", "deprecated"],
        "source_terms": ["ldvh-base/adrs/", "不得定义、重写或授权", "Web、Code、测试输出"],
        "closure_terms": ["archive_reason", "deprecated_reason", "正式 specs", "Git commit records"],
        "human_gate_terms": ["创建 ADR", "创建 `active` ADR", "标记为 `archived` 或 `deprecated`", "修改 `active` ADR"],
        "legacy_terms": ["proposed", "accepted", "rejected", "superseded"],
        "special_terms": [],
    },
    "23": {
        "member": "Pitfall",
        "instance_root": "ldvh-base/pitfalls/",
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "fact_model_member_identity",
            "pitfall_admission_rules",
            "pitfall_source_boundaries",
            "pitfall_state_boundaries",
            "pitfall_evidence_boundaries",
            "pitfall_human_gate_boundaries",
            "pitfall_instance_checks",
            "stop_conditions",
        ],
        "required_statuses": ["active", "archived"],
        "source_terms": ["ldvh-base/pitfalls/", "不得定义、重写或授权", "Web、Code、测试输出"],
        "closure_terms": ["已解决", "验证证据", "archive_reason", "规避策略", "Git commit records"],
        "human_gate_terms": ["创建 Pitfall", "标记为 `archived`", "未解决或未验证问题", "删除原 Pitfall"],
        "legacy_terms": ["repeatability", "severity", "superseded_by"],
        "special_terms": [],
    },
    "24": {
        "member": "Study",
        "instance_root": "ldvh-base/studies/",
        "required_code_consumption": [
            "ldvh_spec_metadata",
            "fact_model_member_identity",
            "study_admission_rules",
            "study_source_boundaries",
            "study_state_boundaries",
            "study_markdown_body_boundaries",
            "study_human_gate_boundaries",
            "study_instance_checks",
            "stop_conditions",
        ],
        "required_statuses": ["active", "archived"],
        "source_terms": ["ldvh-base/studies/", "不得定义、重写或授权", "frontmatter", "Markdown 正文"],
        "closure_terms": ["archive_reason", "Git commit records", "urls", "ref", "summary"],
        "human_gate_terms": ["创建 Study", "标记为 `archived`", "大幅改写", "关键依据"],
        "legacy_terms": [],
        "special_terms": ["## 研究问题", "## 输入与边界", "## 关键发现", "## 建议", "## 后续分流"],
    },
}
FACT_INSTANCE_LAYOUT = {
    "spark": {"spec_id": "20", "directory": "sparks", "suffix": ".yaml"},
    "workcase": {"spec_id": "21", "directory": "workcases", "suffix": ".yaml"},
    "adr": {"spec_id": "22", "directory": "adrs", "suffix": ".yaml"},
    "pitfall": {"spec_id": "23", "directory": "pitfalls", "suffix": ".yaml"},
    "study": {"spec_id": "24", "directory": "studies", "suffix": ".md"},
}
FACT_INSTANCE_FIELD_SCHEMAS = {
    "spark": {
        "required": {
            "id",
            "type",
            "title",
            "status",
            "created",
            "updated",
            "description",
            "source",
            "priority",
            "evolution",
            "related_adrs",
            "related_studies",
            "related_workcases",
            "related_docs",
        },
        "allowed": {
            "id",
            "type",
            "title",
            "status",
            "created",
            "updated",
            "description",
            "source",
            "source_detail",
            "priority",
            "priority_detail",
            "evolution",
            "input_refs",
            "resolved_to",
            "resolved_at",
            "discard_reason",
            "related_sparks",
            "related_adrs",
            "related_studies",
            "related_workcases",
            "related_docs",
            "key_findings",
            "owner",
            "human_gate_records",
        },
        "forbidden": {"规范10"},
    },
    "workcase": {
        "required": {
            "id",
            "type",
            "title",
            "goal",
            "status",
            "created",
            "updated",
            "priority",
            "description",
            "success_criteria",
            "source",
            "orchestration",
            "verification_evidence",
            "closure_evidence",
            "closure_requested_at",
            "closed_at",
            "closure_outcome",
            "residual_risks",
        },
        "allowed": {
            "id",
            "type",
            "title",
            "goal",
            "status",
            "created",
            "updated",
            "priority",
            "description",
            "success_criteria",
            "source",
            "input_refs",
            "orchestration",
            "plan_confirmed_at",
            "review_requested_at",
            "verification_evidence",
            "closure_evidence",
            "closure_requested_at",
            "closed_at",
            "closure_outcome",
            "human_closure_confirmation",
            "residual_risks",
            "followup_refs",
            "revision_history",
            "related_docs",
            "related_adrs",
            "related_sparks",
            "related_pitfalls",
            "related_workcases",
        },
        "forbidden": {"draft", "active", "review_needed"},
    },
    "adr": {
        "required": {"id", "type", "title", "status", "created", "updated", "context", "decision", "consequences"},
        "allowed": {
            "id",
            "type",
            "title",
            "status",
            "created",
            "updated",
            "context",
            "decision",
            "consequences",
            "source",
            "verification",
            "related_docs",
            "related_sparks",
            "related_workcases",
            "related_pitfalls",
            "related_studies",
            "related_adrs",
        },
        "forbidden": {"superseded_by", "alternatives", "affects"},
    },
    "pitfall": {
        "required": {
            "id",
            "type",
            "title",
            "status",
            "created",
            "updated",
            "symptoms",
            "trigger_conditions",
            "root_cause",
            "resolution",
            "verification",
            "avoidance",
            "applicability",
            "tags",
            "source_objects",
            "related_workcases",
            "related_adrs",
            "related_docs",
            "related_rules",
            "source_sparks",
        },
        "allowed": {
            "id",
            "type",
            "title",
            "status",
            "created",
            "updated",
            "symptoms",
            "trigger_conditions",
            "root_cause",
            "resolution",
            "verification",
            "avoidance",
            "applicability",
            "tags",
            "source_objects",
            "related_workcases",
            "related_adrs",
            "related_docs",
            "related_rules",
            "source_sparks",
        },
        "forbidden": {"repeatability", "severity", "superseded_by"},
    },
    "study": {
        "required": {
            "id",
            "type",
            "title",
            "status",
            "created",
            "updated",
            "summary",
            "user_intent",
            "conclusion",
            "input_refs",
            "related_sparks",
            "related_workcases",
            "related_adrs",
            "related_pitfalls",
            "related_docs",
            "archive_reason",
        },
        "allowed": {
            "id",
            "type",
            "title",
            "status",
            "created",
            "updated",
            "summary",
            "user_intent",
            "conclusion",
            "urls",
            "input_refs",
            "related_sparks",
            "related_workcases",
            "related_adrs",
            "related_pitfalls",
            "related_docs",
            "archive_reason",
        },
        "forbidden": set(),
    },
}
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
            "ldvh_install_initialization_action_template",
            "workcase_minimal_action_template",
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


def parse_governed_project_config_contract(root: Path = ROOT) -> dict[str, list[dict[str, str]]]:
    raw = (root / GOVERNED_PROJECTS_CONTRACT_PATH).read_text(encoding="utf-8")
    return {
        "root_fields": find_table(raw, GOVERNED_PROJECT_ROOT_COLUMNS),
        "project_fields": find_table(raw, GOVERNED_PROJECT_ITEM_COLUMNS),
        "git_fields": find_table(raw, GOVERNED_PROJECT_GIT_COLUMNS),
        "resolution_fields": find_table(raw, GOVERNED_PROJECT_RESOLUTION_COLUMNS),
    }


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _default_governed_projects_config_path(root: Path) -> Path:
    return find_governed_projects_config(root, root, [root]) or root / GOVERNED_PROJECTS_CONFIG_PATH


def parse_governed_projects_config(root: Path = ROOT, config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or _default_governed_projects_config_path(root)
    display_path = _display_path(path, root)
    if not path.exists() or not path.is_file():
        return {
            "config_path": display_path,
            "exists": path.exists(),
            "product_name": "",
            "product_description": "",
            "projects": [],
            "source_refs": [],
        }
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        data = {}
    projects = data.get("projects", []) if isinstance(data, dict) else []
    return {
        "config_path": display_path,
        "exists": True,
        "product_name": data.get("product_name", "") if isinstance(data, dict) else "",
        "product_description": data.get("product_description", "") if isinstance(data, dict) else "",
        "projects": projects if isinstance(projects, list) else [],
        "source_refs": [
            {"path": display_path, "role": "governed_project_config"},
            {"path": SHORT_SPEC_REFS["10"], "role": "governed_project_spec"},
            {"path": GOVERNED_PROJECTS_CONTRACT_PATH, "role": "governed_project_config_contract"},
        ],
    }


def parse_git_commit_action_template(root: Path = ROOT) -> list[dict[str, str]]:
    raw = (root / SHORT_SPEC_REFS["06"]).read_text(encoding="utf-8")
    sections = h2_sections(raw)
    section = sections.get("模板候选与迁移边界")
    if not section:
        return []
    return find_table(section["body"], ACTION_TEMPLATE_COLUMNS)


def parse_workcase_action_template(root: Path = ROOT) -> list[dict[str, str]]:
    raw = (root / SHORT_SPEC_REFS["06"]).read_text(encoding="utf-8")
    sections = h2_sections(raw)
    section = sections.get("模板候选与迁移边界")
    if not section:
        return []
    marker = "### WorkCase 最小行动模板"
    marker_index = section["body"].find(marker)
    if marker_index == -1:
        return []
    return find_table(section["body"][marker_index:], ACTION_TEMPLATE_COLUMNS)


def parse_ldvh_install_action_template(root: Path = ROOT) -> list[dict[str, str]]:
    raw = (root / SHORT_SPEC_REFS["30"]).read_text(encoding="utf-8")
    sections = h2_sections(raw)
    section = sections.get("Context、Scenario、Gate 与交还")
    if not section:
        return []
    return find_table(section["body"], ACTION_TEMPLATE_COLUMNS)


def parse_ldvh_install_spec_contract(root: Path = ROOT) -> dict[str, Any]:
    path = SHORT_SPEC_REFS["30"]
    full_path = root / path
    if not full_path.exists():
        return {
            "spec_id": "30",
            "path": path,
            "code_consumption": [],
            "action_template": [],
            "stop_conditions": [],
            "source_refs": [],
        }

    raw = full_path.read_text(encoding="utf-8")
    metadata = first_yaml_block(raw, path).get("ldvh_spec", {})
    sections = h2_sections(raw)

    return {
        "spec_id": "30",
        "path": path,
        "code_consumption": metadata.get("code_consumption", []),
        "action_template": parse_ldvh_install_action_template(root),
        "stop_conditions": _section_numbered_items(sections, "Stop Conditions"),
        "source_refs": [
            {"path": path, "role": "ldvh_install_action_template"},
            {"path": SHORT_SPEC_REFS["06"], "role": "action_template_parent_spec"},
            {"path": SHORT_SPEC_REFS["10"], "role": "governed_project_config_spec"},
        ],
    }


def parse_environment_hook_acceptance_action_template(root: Path = ROOT) -> list[dict[str, str]]:
    raw = (root / SHORT_SPEC_REFS["31"]).read_text(encoding="utf-8")
    sections = h2_sections(raw)
    section = sections.get("Context、Scenario、Gate 与交还")
    if not section:
        return []
    return find_table(section["body"], ACTION_TEMPLATE_COLUMNS)


def parse_environment_hook_acceptance_spec_contract(root: Path = ROOT) -> dict[str, Any]:
    path = SHORT_SPEC_REFS["31"]
    full_path = root / path
    if not full_path.exists():
        return {
            "spec_id": "31",
            "path": path,
            "code_consumption": [],
            "action_template": [],
            "stop_conditions": [],
            "source_refs": [],
        }

    raw = full_path.read_text(encoding="utf-8")
    metadata = first_yaml_block(raw, path).get("ldvh_spec", {})
    sections = h2_sections(raw)

    return {
        "spec_id": "31",
        "path": path,
        "code_consumption": metadata.get("code_consumption", []),
        "action_template": parse_environment_hook_acceptance_action_template(root),
        "stop_conditions": _section_numbered_items(sections, "Stop Conditions"),
        "source_refs": [
            {"path": path, "role": "environment_hook_acceptance_action_template"},
            {"path": SHORT_SPEC_REFS["06"], "role": "action_template_parent_spec"},
            {"path": SHORT_SPEC_REFS["30"], "role": "install_handoff_action_template"},
            {"path": SHORT_SPEC_REFS["01"], "role": "environment_entry_boundary"},
        ],
    }


def parse_fact_model_member_contract(spec_id: str, root: Path = ROOT) -> dict[str, Any]:
    expected = FACT_MODEL_MEMBER_CONTRACTS[spec_id]
    path = SHORT_SPEC_REFS[spec_id]
    full_path = root / path
    if not full_path.exists():
        return {
            "spec_id": spec_id,
            "member": expected["member"],
            "path": path,
            "code_consumption": [],
            "instance_root": expected["instance_root"],
            "statuses": [],
            "source_refs": [],
        }

    raw = full_path.read_text(encoding="utf-8")
    metadata = first_yaml_block(raw, path).get("ldvh_spec", {})
    sections = h2_sections(raw)
    status_rows = _table_rows_for_section(sections, "状态、证据与关闭边界", WORKCASE_STATUS_COLUMNS)

    return {
        "spec_id": spec_id,
        "member": expected["member"],
        "path": path,
        "code_consumption": metadata.get("code_consumption", []),
        "instance_root": expected["instance_root"],
        "statuses": [
            {
                "status": strip_inline_code(row["状态"]),
                "meaning": row["含义"],
            }
            for row in status_rows
        ],
        "source_refs": [
            {"path": SHORT_SPEC_REFS["05"], "role": "parent_fact_model_spec"},
            {"path": path, "role": "fact_model_member_spec"},
            {"path": "specs/03-事实源与Git溯源规范.md", "role": "fact_source_boundary"},
            {"path": "specs/09-测试与验证规范.md", "role": "verification_boundary"},
        ],
    }


def parse_fact_model_member_contracts(root: Path = ROOT) -> list[dict[str, Any]]:
    return [
        parse_fact_model_member_contract(spec_id, root)
        for spec_id in sorted(FACT_MODEL_MEMBER_CONTRACTS)
    ]


def parse_workcase_member_contract(root: Path = ROOT) -> dict[str, Any]:
    return parse_fact_model_member_contract("21", root)


def _fact_instance_id_from_filename(path: Path) -> str:
    match = re.match(r"^([a-z]+-\d{4})-", path.name)
    return match.group(1) if match else ""


def _parse_study_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    frontmatter = raw[3:end].strip()
    body = raw[end + 4 :]
    try:
        data = yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError:
        data = {}
    return data if isinstance(data, dict) else {}, body


def _parse_fact_instance_data(path: Path, kind: str) -> tuple[dict[str, Any], str]:
    if kind == "study":
        return _parse_study_frontmatter(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        data = {}
    return data if isinstance(data, dict) else {}, ""


def parse_fact_instances(root: Path = ROOT) -> list[dict[str, Any]]:
    instances: list[dict[str, Any]] = []
    for kind, layout in FACT_INSTANCE_LAYOUT.items():
        directory = root / "ldvh-base" / layout["directory"]
        if not directory.exists():
            continue
        for path in sorted(directory.glob(f"*{layout['suffix']}")):
            data, body = _parse_fact_instance_data(path, kind)
            rel_path = path.relative_to(root).as_posix()
            instances.append({
                "kind": kind,
                "spec_id": layout["spec_id"],
                "path": rel_path,
                "filename_id": _fact_instance_id_from_filename(path),
                "id": str(data.get("id", "")),
                "type": str(data.get("type", "")),
                "status": str(data.get("status", "")),
                "data": data,
                "body": body,
            })
    return instances


def _fact_reference_ids(value: Any) -> list[str]:
    ids: list[str] = []
    if isinstance(value, str):
        ids.extend(re.findall(r"\b(?:spark|workcase|adr|pitfall|study)-\d{4}\b", value))
    elif isinstance(value, list):
        for item in value:
            ids.extend(_fact_reference_ids(item))
    elif isinstance(value, dict):
        for item in value.values():
            ids.extend(_fact_reference_ids(item))
    return ids


def _fact_relation_values(data: dict[str, Any]) -> list[str]:
    relation_keys = {
        "related_sparks",
        "related_workcases",
        "related_adrs",
        "related_pitfalls",
        "related_studies",
        "source_sparks",
        "source_objects",
        "input_refs",
        "followup_refs",
    }
    values: list[str] = []
    for key, value in data.items():
        if key in relation_keys:
            values.extend(_fact_reference_ids(value))
    return values


def _fact_statuses_by_kind(root: Path = ROOT) -> dict[str, set[str]]:
    statuses: dict[str, set[str]] = {}
    contracts = {contract["spec_id"]: contract for contract in parse_fact_model_member_contracts(root)}
    for kind, layout in FACT_INSTANCE_LAYOUT.items():
        contract = contracts.get(layout["spec_id"], {})
        statuses[kind] = {row["status"] for row in contract.get("statuses", []) if row.get("status")}
    return statuses


def validate_fact_instances(root: Path = ROOT) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not (root / "ldvh-base").exists():
        return diagnostics
    statuses_by_kind = _fact_statuses_by_kind(root)
    instances = parse_fact_instances(root)
    ids: dict[str, str] = {}

    for kind, layout in FACT_INSTANCE_LAYOUT.items():
        directory = root / "ldvh-base" / layout["directory"]
        if not directory.exists():
            diagnostics.append(Diagnostic(
                "error",
                "FACT_INSTANCE_DIRECTORY_MISSING",
                f"ldvh-base/{layout['directory']}/",
                f"{kind} 实例目录缺失",
            ))

    for instance in instances:
        path = instance["path"]
        expected_kind = instance["kind"]
        instance_id = instance["id"]
        filename_id = instance["filename_id"]
        if not instance["data"]:
            diagnostics.append(Diagnostic("error", "FACT_INSTANCE_PARSE_FAILED", path, "事实实例无法解析为结构化数据"))
            continue
        schema = FACT_INSTANCE_FIELD_SCHEMAS.get(expected_kind, {})
        fields = set(instance["data"])
        missing_fields = sorted(schema.get("required", set()) - fields)
        if missing_fields:
            diagnostics.append(Diagnostic(
                "error",
                "FACT_INSTANCE_REQUIRED_FIELD_MISSING",
                path,
                f"{instance_id or filename_id} 缺少必填字段: {', '.join(missing_fields)}",
            ))
        forbidden_fields = sorted(fields & schema.get("forbidden", set()))
        if forbidden_fields:
            diagnostics.append(Diagnostic(
                "error",
                "FACT_INSTANCE_LEGACY_FIELD_FORBIDDEN",
                path,
                f"{instance_id or filename_id} 使用了 V3 禁用字段: {', '.join(forbidden_fields)}",
            ))
        unknown_fields = sorted(fields - schema.get("allowed", set()) - schema.get("forbidden", set()))
        if unknown_fields:
            diagnostics.append(Diagnostic(
                "error",
                "FACT_INSTANCE_FIELD_UNKNOWN",
                path,
                f"{instance_id or filename_id} 包含未登记字段: {', '.join(unknown_fields)}",
            ))
        if not instance_id:
            diagnostics.append(Diagnostic("error", "FACT_INSTANCE_ID_MISSING", path, "事实实例缺少 id"))
        elif instance_id != filename_id:
            diagnostics.append(Diagnostic(
                "error",
                "FACT_INSTANCE_ID_FILENAME_MISMATCH",
                path,
                f"事实实例 id 与文件名不一致: id={instance_id}, filename={filename_id}",
            ))
        if instance_id in ids:
            diagnostics.append(Diagnostic(
                "error",
                "FACT_INSTANCE_ID_DUPLICATE",
                path,
                f"事实实例 id 重复: {instance_id}，已见于 {ids[instance_id]}",
            ))
        elif instance_id:
            ids[instance_id] = path
        if instance["type"] != expected_kind:
            diagnostics.append(Diagnostic(
                "error",
                "FACT_INSTANCE_TYPE_MISMATCH",
                path,
                f"事实实例 type 应为 {expected_kind}，实际为 {instance['type']}",
            ))
        allowed_statuses = statuses_by_kind.get(expected_kind, set())
        if instance["status"] not in allowed_statuses:
            diagnostics.append(Diagnostic(
                "error",
                "FACT_INSTANCE_STATUS_INVALID",
                path,
                f"{instance_id} status 不在 {expected_kind} 闭集内: {instance['status']}",
            ))
        if expected_kind == "study":
            for heading in FACT_MODEL_MEMBER_CONTRACTS["24"]["special_terms"]:
                if heading not in instance["body"]:
                    diagnostics.append(Diagnostic(
                        "error",
                        "STUDY_BODY_HEADING_MISSING",
                        path,
                        f"Study 正文缺少固定标题: {heading}",
                    ))

    known_ids = set(ids)
    for instance in instances:
        for ref_id in _fact_relation_values(instance["data"]):
            if ref_id not in known_ids:
                diagnostics.append(Diagnostic(
                    "error",
                    "FACT_INSTANCE_REFERENCE_MISSING",
                    instance["path"],
                    f"{instance['id']} 引用不存在的事实对象: {ref_id}",
                ))
    return diagnostics


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


def _resolve_path(path: Path, base: Path) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = base / expanded
    return expanded.resolve(strict=False)


def _git_lookup_cwd(path: Path) -> Path:
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.is_file():
        return candidate.parent
    if candidate.is_dir():
        return candidate
    for parent in [candidate.parent, *candidate.parents]:
        if parent.exists() and parent.is_dir():
            return parent
    return candidate.parent


def _git_text(cwd: Path, args: list[str]) -> str:
    command = ["git", "-C", str(_git_lookup_cwd(cwd)), *args]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _git_common_dir(cwd: Path) -> str:
    return _git_text(cwd, ["rev-parse", "--path-format=absolute", "--git-common-dir"])


def _resolved_common_dir(raw: str) -> str:
    if not raw:
        return ""
    return str(Path(raw).expanduser().resolve(strict=False))


def _walk_for_governed_config(candidate: Path) -> Path | None:
    current = candidate.expanduser()
    if not current.is_absolute():
        current = Path.cwd() / current
    if current.is_file():
        current = current.parent
    for parent in [current, *current.parents]:
        config = parent / GOVERNED_PROJECTS_CONFIG_PATH
        if config.is_file():
            return config
    return None


def _config_search_dir(path: Path, base: Path) -> Path:
    current = _resolve_path(path, base)
    return current.parent if current.is_file() else current


def _governed_config_chain(config_root: Path, candidate: Path, base: Path) -> list[Path]:
    root = _resolve_path(config_root, base)
    current = _config_search_dir(candidate, base)
    try:
        relative = current.relative_to(root)
    except ValueError:
        return []

    chain = [root]
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        chain.append(cursor)

    configs: list[Path] = []
    for directory in chain:
        config = directory / GOVERNED_PROJECTS_CONFIG_PATH
        if config.is_file():
            configs.append(config)
    return configs


def inspect_governed_config_hierarchy(
    root: Path = ROOT,
    *,
    config_root: str | Path | None = None,
    cwd: str | Path | None = None,
    target_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    base_cwd = _resolve_path(Path(cwd) if cwd is not None else root, root)
    search_root = _resolve_path(Path(config_root) if config_root is not None else root, root)
    raw_targets = [Path(path) for path in (target_paths or []) if str(path).strip()]
    effective_targets = raw_targets if raw_targets else [base_cwd]

    configs: list[Path] = []
    target_records: list[dict[str, Any]] = []
    for target in effective_targets:
        normalized = _resolve_path(target, base_cwd)
        chain = _governed_config_chain(search_root, target, base_cwd)
        configs.extend(chain)
        target_records.append({
            "target": target.as_posix(),
            "normalized_path": normalized.as_posix(),
            "config_chain": [
                {
                    "path": _display_path(config, root),
                    "absolute_path": config.as_posix(),
                }
                for config in chain
            ],
        })

    unique_configs = list(dict.fromkeys(configs))
    conflict = len(unique_configs) > 1
    return {
        "config_root": search_root.as_posix(),
        "target_paths": [record["normalized_path"] for record in target_records],
        "targets": target_records,
        "configs": [
            {
                "path": _display_path(config, root),
                "absolute_path": config.as_posix(),
            }
            for config in unique_configs
        ],
        "conflict": conflict,
        "blocked_reason": "nested_governed_projects_config" if conflict else "",
        "message": (
            "同一路径链上存在多个 LDVH-GOVERNED-PROJECTS.yaml，必须先删除、迁移或明确保留其中一个。"
            if conflict else ""
        ),
    }


def find_governed_projects_config(root: Path = ROOT, cwd: Path | None = None, targets: list[Path] | None = None) -> Path | None:
    search_targets = list(targets or [])
    if cwd is not None:
        search_targets.append(cwd)
    for candidate in search_targets:
        config = _walk_for_governed_config(candidate)
        if config is not None:
            return config
    fallback = root / GOVERNED_PROJECTS_CONFIG_PATH
    return fallback if fallback.is_file() else None


def _load_governed_projects_from_config(config_path: Path) -> list[dict[str, Any]]:
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    if not isinstance(data, dict):
        return []
    projects = data.get("projects", [])
    return projects if isinstance(projects, list) else []


def _project_git_value(project: dict[str, Any], key: str) -> str:
    git = project.get("git")
    if not isinstance(git, dict):
        return ""
    value = git.get(key, "")
    return value.strip() if isinstance(value, str) else ""


def _project_key(project: dict[str, Any], project_path: Path) -> str:
    project_id = project.get("id", "")
    if isinstance(project_id, str) and project_id.strip():
        return project_id.strip()
    return project_path.as_posix()


def _match_governed_project(path: Path, config_path: Path, base: Path) -> dict[str, Any]:
    current = _resolve_path(path, base)
    current_common_dir = _resolved_common_dir(_git_common_dir(current))
    base_result: dict[str, Any] = {
        "governed": False,
        "governed_via": "",
        "governed_project_id": "",
        "governed_project_path": "",
        "project_key": "",
        "git_common_dir": current_common_dir,
    }

    matches: list[dict[str, Any]] = []
    for project in _load_governed_projects_from_config(config_path):
        if not isinstance(project, dict):
            continue
        raw_project_path = project.get("path", "")
        if not isinstance(raw_project_path, str) or not raw_project_path.strip():
            continue
        project_path = _resolve_path(Path(raw_project_path), config_path.parent)
        project_id = project.get("id", "")
        result = {
            **base_result,
            "governed": True,
            "governed_project_id": project_id.strip() if isinstance(project_id, str) else "",
            "governed_project_path": project_path.as_posix(),
            "project_key": _project_key(project, project_path),
        }
        if current == project_path or current.as_posix().startswith(project_path.as_posix() + os.sep):
            matches.append({**result, "governed_via": "path"})
            continue

        registered_common_dir = _resolved_common_dir(_project_git_value(project, "common_dir"))
        if current_common_dir and registered_common_dir and current_common_dir == registered_common_dir:
            matches.append({**result, "governed_via": "git.common_dir"})
            continue

        project_common_dir = _resolved_common_dir(_git_common_dir(project_path))
        if current_common_dir and project_common_dir and current_common_dir == project_common_dir:
            matches.append({**result, "governed_via": "git.common_dir"})

    project_keys = {match["project_key"] for match in matches}
    if len(project_keys) > 1:
        return {
            **base_result,
            "blocked": True,
            "blocked_reason": "ambiguous_governed_project",
            "ambiguous_project_ids": sorted(project_keys),
        }
    if matches:
        return matches[0]
    return base_result


def _target_resolution(path: Path, config_path: Path, base: Path, source: str) -> dict[str, Any]:
    match = _match_governed_project(path, config_path, base)
    normalized = _resolve_path(path, base)
    status = "governed" if match.get("governed") else "not_governed"
    if match.get("blocked"):
        status = "ambiguous"
    return {
        "target": path.as_posix(),
        "normalized_path": normalized.as_posix(),
        "source": source,
        "status": status,
        "governed": bool(match.get("governed")),
        "governed_via": match.get("governed_via", ""),
        "governed_project_id": match.get("governed_project_id", ""),
        "governed_project_path": match.get("governed_project_path", ""),
        "project_key": match.get("project_key", ""),
        "git_common_dir": match.get("git_common_dir", ""),
        "unknown_reason": "" if match.get("governed") else match.get("blocked_reason", "not_in_governed_project"),
    }


def resolve_governed_subject(
    root: Path = ROOT,
    cwd: str | Path | None = None,
    target_paths: list[str | Path] | None = None,
    read_write_kind: str = "write",
    config_root: str | Path | None = None,
) -> dict[str, Any]:
    base_cwd = _resolve_path(Path(cwd) if cwd is not None else root, root)
    raw_targets = [Path(path) for path in (target_paths or []) if str(path).strip()]
    explicit_targets = bool(raw_targets)
    effective_targets = raw_targets if explicit_targets else [base_cwd]
    config_hierarchy = inspect_governed_config_hierarchy(
        root,
        config_root=config_root,
        cwd=base_cwd,
        target_paths=effective_targets,
    )
    if config_root is not None:
        hierarchy_configs = [Path(item["absolute_path"]) for item in config_hierarchy["configs"]]
        config = hierarchy_configs[0] if hierarchy_configs else None
    else:
        config = find_governed_projects_config(root, base_cwd, effective_targets)
    result: dict[str, Any] = {
        "governed": False,
        "blocked": False,
        "blocked_reason": "",
        "cwd": base_cwd.as_posix(),
        "target_paths": [_resolve_path(path, base_cwd).as_posix() for path in effective_targets],
        "target_resolutions": [],
        "governed_subject": "",
        "governed_via": "",
        "governed_project_id": "",
        "governed_project_path": "",
        "config_path": config.relative_to(root).as_posix() if config and config.is_relative_to(root) else config.as_posix() if config else "",
        "config_path_absolute": config.as_posix() if config else "",
        "config_hierarchy": config_hierarchy,
        "subject_source": "target" if explicit_targets else "cwd-fallback",
        "read_write_kind": read_write_kind,
        "message": "",
    }
    if config_hierarchy["conflict"]:
        result.update({
            "blocked": True,
            "blocked_reason": config_hierarchy["blocked_reason"],
            "message": config_hierarchy["message"],
        })
        return result
    if config is None:
        result["message"] = "未找到 LDVH-GOVERNED-PROJECTS.yaml，no-op"
        return result

    source = "target" if explicit_targets else "cwd-fallback"
    resolutions = [_target_resolution(path, config, base_cwd, source) for path in effective_targets]
    result["target_resolutions"] = resolutions

    ambiguous = [item for item in resolutions if item["status"] == "ambiguous"]
    if ambiguous:
        result.update({
            "blocked": True,
            "blocked_reason": "ambiguous_governed_project",
            "message": "Git identity 命中多个管辖项目，必须拆分或进入 Human Gate。",
        })
        return result

    governed = [item for item in resolutions if item["governed"]]
    nongoverned = [item for item in resolutions if not item["governed"]]
    governed_keys = {item["project_key"] or item["governed_project_path"] for item in governed}
    if len(governed_keys) > 1:
        result.update({
            "blocked": True,
            "blocked_reason": "multiple_governed_projects",
            "message": "一次操作命中多个管辖项目，必须拆分或进入 Human Gate。",
        })
        return result
    if governed and nongoverned and explicit_targets and read_write_kind in {"write", "commit"}:
        result.update({
            "blocked": True,
            "blocked_reason": "mixed_governed_and_ungoverned_targets",
            "message": "一次写入操作混合管辖与非管辖 target，必须拆分或进入 Human Gate。",
        })
        return result
    if not governed:
        result["message"] = "工作对象未命中管辖项目，no-op"
        return result

    subject = governed[0]
    result.update({
        "governed": True,
        "governed_subject": subject["normalized_path"],
        "governed_via": subject["governed_via"],
        "governed_project_id": subject["governed_project_id"],
        "governed_project_path": subject["governed_project_path"],
        "message": "工作对象命中管辖项目。",
    })
    return result


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


def validate_implementation_domain_boundaries(root: Path = ROOT) -> list[Diagnostic]:
    raw_by_path: dict[str, str] = {}
    sections_by_path: dict[str, dict[str, dict[str, str]]] = {}
    diagnostics: list[Diagnostic] = []

    for requirement in IMPLEMENTATION_DOMAIN_BOUNDARY_REQUIREMENTS:
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


def validate_governed_project_spec_boundaries(root: Path = ROOT) -> list[Diagnostic]:
    path = SHORT_SPEC_REFS["10"]
    raw = (root / path).read_text(encoding="utf-8")
    sections = h2_sections(raw)
    diagnostics: list[Diagnostic] = []

    for requirement in GOVERNED_PROJECT_SPEC_REQUIREMENTS:
        section = sections.get(requirement["section"])
        if not section:
            diagnostics.append(
                Diagnostic(
                    "error",
                    requirement["code"],
                    path,
                    f"10 缺少可消费章节: {requirement['section']}",
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


def validate_governed_project_config_contract(root: Path = ROOT) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    contract = parse_governed_project_config_contract(root)
    if not contract["root_fields"]:
        diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_ROOT_FIELD_TABLE_MISSING", GOVERNED_PROJECTS_CONTRACT_PATH, "管辖项目根字段表缺失"))
    for value in _table_has_values(contract["root_fields"], "根字段", GOVERNED_PROJECT_REQUIRED_ROOT_FIELDS):
        diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_ROOT_FIELD_CONTRACT_MISSING", GOVERNED_PROJECTS_CONTRACT_PATH, f"管辖项目根字段缺失: {value}"))
    for value in _table_has_values(contract["project_fields"], "项目字段", GOVERNED_PROJECT_REQUIRED_ITEM_FIELDS):
        diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_ITEM_FIELD_CONTRACT_MISSING", GOVERNED_PROJECTS_CONTRACT_PATH, f"管辖项目项目字段缺失: {value}"))
    for value in _table_has_values(contract["git_fields"], "Git字段", GOVERNED_PROJECT_REQUIRED_GIT_FIELDS):
        diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_GIT_FIELD_CONTRACT_MISSING", GOVERNED_PROJECTS_CONTRACT_PATH, f"管辖项目 Git 字段缺失: {value}"))
    for value in _table_has_values(contract["resolution_fields"], "resolution字段", GOVERNED_PROJECT_REQUIRED_RESOLUTION_FIELDS):
        diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_RESOLUTION_FIELD_CONTRACT_MISSING", GOVERNED_PROJECTS_CONTRACT_PATH, f"管辖项目 resolution 字段缺失: {value}"))
    return diagnostics


def validate_governed_projects_config(root: Path = ROOT, config_path: Path | None = None) -> list[Diagnostic]:
    path = config_path or _default_governed_projects_config_path(root)
    display_path = _display_path(path, root)
    diagnostics: list[Diagnostic] = []
    if not path.exists():
        return [Diagnostic("error", "GOVERNED_PROJECTS_CONFIG_MISSING", display_path, "缺少管辖项目配置: LDVH-GOVERNED-PROJECTS.yaml")]
    if not path.is_file():
        return [Diagnostic("error", "GOVERNED_PROJECTS_CONFIG_NOT_FILE", display_path, "管辖项目配置不是文件")]

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [Diagnostic("error", "GOVERNED_PROJECTS_CONFIG_YAML_INVALID", display_path, f"管辖项目配置 YAML 解析失败: {exc}")]

    if not isinstance(data, dict):
        return [Diagnostic("error", "GOVERNED_PROJECTS_CONFIG_ROOT_INVALID", display_path, "管辖项目配置根对象必须是 mapping")]

    root_fields = set(data)
    for field in sorted(GOVERNED_PROJECTS_ROOT_FIELDS - root_fields):
        diagnostics.append(Diagnostic("error", "GOVERNED_PROJECTS_ROOT_FIELD_MISSING", display_path, f"管辖项目配置缺少根字段: {field}"))
    for field in sorted(root_fields - GOVERNED_PROJECTS_ROOT_FIELDS):
        diagnostics.append(Diagnostic("error", "GOVERNED_PROJECTS_ROOT_FIELD_FORBIDDEN", display_path, f"管辖项目配置不得包含根字段: {field}"))
    for field in sorted({"product_name", "product_description"} & root_fields):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            diagnostics.append(Diagnostic("error", "GOVERNED_PROJECTS_ROOT_FIELD_INVALID", display_path, f"{field} 必须是非空字符串"))

    projects = data.get("projects")
    if not isinstance(projects, list):
        diagnostics.append(Diagnostic("error", "GOVERNED_PROJECTS_LIST_INVALID", display_path, "projects 必须是列表"))
        return diagnostics

    seen_ids: dict[str, int] = {}
    seen_paths: dict[str, int] = {}
    for index, project in enumerate(projects, start=1):
        if not isinstance(project, dict):
            diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_ITEM_INVALID", display_path, f"projects[{index}] 必须是对象"))
            continue
        fields = set(project)
        for field in sorted(GOVERNED_PROJECTS_REQUIRED_ITEM_FIELDS - fields):
            diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_FIELD_MISSING", display_path, f"projects[{index}] 缺少字段: {field}"))
        for field in sorted(fields - GOVERNED_PROJECTS_ITEM_FIELDS):
            diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_FIELD_FORBIDDEN", display_path, f"projects[{index}] 不得包含字段: {field}"))
        for field in sorted((GOVERNED_PROJECTS_ITEM_FIELDS - {"git"}) & fields):
            value = project.get(field)
            if not isinstance(value, str) or not value.strip():
                diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_FIELD_INVALID", display_path, f"projects[{index}].{field} 必须是非空字符串"))

        project_id = project.get("id")
        if isinstance(project_id, str) and project_id.strip():
            normalized_id = project_id.strip()
            if normalized_id in seen_ids:
                diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_ID_DUPLICATE", display_path, f"管辖项目 id 重复: {normalized_id}"))
            seen_ids[normalized_id] = index

        project_path = project.get("path")
        if isinstance(project_path, str) and project_path.strip():
            normalized_path = _resolve_path(Path(project_path), path.parent).as_posix()
            if normalized_path in seen_paths:
                diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_PATH_DUPLICATE", display_path, f"管辖项目 path 重复: {project_path}"))
            seen_paths[normalized_path] = index

        git = project.get("git")
        if "git" in fields:
            if not isinstance(git, dict):
                diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_GIT_INVALID", display_path, f"projects[{index}].git 必须是对象"))
            else:
                git_fields = set(git)
                for field in sorted(git_fields - GOVERNED_PROJECTS_GIT_FIELDS):
                    diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_GIT_FIELD_FORBIDDEN", display_path, f"projects[{index}].git 不得包含字段: {field}"))
                for field in sorted(GOVERNED_PROJECTS_GIT_FIELDS & git_fields):
                    value = git.get(field)
                    if not isinstance(value, str) or not value.strip():
                        diagnostics.append(Diagnostic("error", "GOVERNED_PROJECT_GIT_FIELD_INVALID", display_path, f"projects[{index}].git.{field} 必须是非空字符串"))

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
    diagnostics.extend(_validate_attachment_authorized_by_parent(root, GOVERNED_PROJECTS_CONTRACT_PATH, SHORT_SPEC_REFS["10"]))

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

    diagnostics.extend(validate_governed_project_config_contract(root))

    return diagnostics


def validate_git_commit_action_template(root: Path = ROOT) -> list[Diagnostic]:
    path = SHORT_SPEC_REFS["06"]
    raw = (root / path).read_text(encoding="utf-8")
    sections = h2_sections(raw)
    action_section_body = sections.get("模板候选与迁移边界", {}).get("body", raw)
    git_template_body = action_section_body.split("### WorkCase 最小行动模板", 1)[0]
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

    missing_boundary_terms = [term for term in GIT_COMMIT_ACTION_TEMPLATE_BOUNDARY_TERMS if term not in git_template_body]
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


def validate_workcase_action_template(root: Path = ROOT) -> list[Diagnostic]:
    path = SHORT_SPEC_REFS["06"]
    raw = (root / path).read_text(encoding="utf-8")
    rows = parse_workcase_action_template(root)
    diagnostics: list[Diagnostic] = []

    if not rows:
        return [
            Diagnostic(
                "error",
                "WORKCASE_ACTION_TEMPLATE_MISSING",
                path,
                "06 缺少 WorkCase 最小行动模板结构表",
            )
        ]

    rows_by_structure = {row["结构"]: row for row in rows}
    for structure, terms in WORKCASE_ACTION_TEMPLATE_REQUIRED_ROWS.items():
        row = rows_by_structure.get(structure)
        if not row:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "WORKCASE_ACTION_TEMPLATE_ROW_MISSING",
                    path,
                    f"WorkCase 最小行动模板缺少结构: {structure}",
                )
            )
            continue
        missing_terms = [term for term in terms if term not in row["最小要求"]]
        for term in missing_terms:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "WORKCASE_ACTION_TEMPLATE_TERM_MISSING",
                    path,
                    f"{structure} 缺少关键要求: {term}",
                )
            )

    missing_boundary_terms = [term for term in WORKCASE_ACTION_TEMPLATE_BOUNDARY_TERMS if term not in raw]
    for term in missing_boundary_terms:
        diagnostics.append(
            Diagnostic(
                "error",
                "WORKCASE_ACTION_TEMPLATE_BOUNDARY_MISSING",
                path,
                f"WorkCase 最小行动模板缺少边界声明: {term}",
            )
        )

    return diagnostics


def validate_ldvh_install_action_template(root: Path = ROOT) -> list[Diagnostic]:
    path = SHORT_SPEC_REFS["30"]
    raw = (root / path).read_text(encoding="utf-8")
    rows = parse_ldvh_install_action_template(root)
    contract = parse_ldvh_install_spec_contract(root)
    diagnostics: list[Diagnostic] = []

    code_consumption = contract["code_consumption"]
    if not isinstance(code_consumption, list) or not all(isinstance(item, str) for item in code_consumption):
        diagnostics.append(Diagnostic("error", "LDVH_INSTALL_CODE_CONSUMPTION_INVALID", path, "30 code_consumption 必须是字符串列表"))
        code_consumption = [item for item in code_consumption if isinstance(item, str)] if isinstance(code_consumption, list) else []
    for item in _missing_exact_values(LDVH_INSTALL_REQUIRED_CODE_CONSUMPTION, code_consumption):
        diagnostics.append(
            Diagnostic(
                "error",
                "LDVH_INSTALL_CODE_CONSUMPTION_MISSING",
                path,
                f"30 缺少 Code 消费入口: {item}",
            )
        )
    expected_code_consumption = set(LDVH_INSTALL_REQUIRED_CODE_CONSUMPTION)
    for item in code_consumption:
        if item not in expected_code_consumption:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "LDVH_INSTALL_CODE_CONSUMPTION_UNSUPPORTED",
                    path,
                    f"30 声明了未被 Code 契约消费的入口: {item}",
                )
            )

    if not rows:
        return diagnostics + [
            Diagnostic(
                "error",
                "LDVH_INSTALL_ACTION_TEMPLATE_MISSING",
                path,
                "30 缺少 LDVH 安装、初始化与管辖项目配置行动模板结构表",
            )
        ]

    if not contract["stop_conditions"]:
        diagnostics.append(Diagnostic("error", "LDVH_INSTALL_STOP_CONDITIONS_MISSING", path, "30 必须声明可消费 Stop Conditions"))

    rows_by_structure = {row["结构"]: row for row in rows}
    for structure, terms in LDVH_INSTALL_ACTION_TEMPLATE_REQUIRED_ROWS.items():
        row = rows_by_structure.get(structure)
        if not row:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "LDVH_INSTALL_ACTION_TEMPLATE_ROW_MISSING",
                    path,
                    f"LDVH 安装初始化配置行动模板缺少结构: {structure}",
                )
            )
            continue
        missing_terms = [term for term in terms if term not in row["最小要求"]]
        for term in missing_terms:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "LDVH_INSTALL_ACTION_TEMPLATE_TERM_MISSING",
                    path,
                    f"{structure} 缺少关键要求: {term}",
                )
            )

    missing_boundary_terms = [term for term in LDVH_INSTALL_ACTION_TEMPLATE_BOUNDARY_TERMS if term not in raw]
    for term in missing_boundary_terms:
        diagnostics.append(
            Diagnostic(
                "error",
                "LDVH_INSTALL_ACTION_TEMPLATE_BOUNDARY_MISSING",
                path,
                f"LDVH 安装初始化配置行动模板缺少边界声明: {term}",
            )
        )

    missing_wizard_terms = [term for term in LDVH_INSTALL_WIZARD_TERMS if term not in raw]
    for term in missing_wizard_terms:
        diagnostics.append(
            Diagnostic(
                "error",
                "LDVH_INSTALL_WIZARD_TERM_MISSING",
                path,
                f"LDVH 安装向导状态机缺少关键要求: {term}",
            )
        )

    for item, terms in LDVH_INSTALL_CODE_CONSUMPTION_SUPPORT_TERMS.items():
        for term in [term for term in terms if term not in raw]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "LDVH_INSTALL_CODE_CONSUMPTION_SUPPORT_MISSING",
                    path,
                    f"{item} 缺少可消费支撑声明: {term}",
                )
            )

    return diagnostics


def validate_environment_hook_acceptance_action_template(root: Path = ROOT) -> list[Diagnostic]:
    path = SHORT_SPEC_REFS["31"]
    full_path = root / path
    if not full_path.exists():
        return [Diagnostic("error", "ENV_HOOK_ACCEPTANCE_SPEC_MISSING", path, "31 环境 Hook 接入后验收行动模板缺失")]

    raw = full_path.read_text(encoding="utf-8")
    rows = parse_environment_hook_acceptance_action_template(root)
    contract = parse_environment_hook_acceptance_spec_contract(root)
    diagnostics: list[Diagnostic] = []

    code_consumption = contract["code_consumption"]
    if not isinstance(code_consumption, list) or not all(isinstance(item, str) for item in code_consumption):
        diagnostics.append(Diagnostic("error", "ENV_HOOK_ACCEPTANCE_CODE_CONSUMPTION_INVALID", path, "31 code_consumption 必须是字符串列表"))
        code_consumption = [item for item in code_consumption if isinstance(item, str)] if isinstance(code_consumption, list) else []
    for item in _missing_exact_values(ENV_HOOK_ACCEPTANCE_REQUIRED_CODE_CONSUMPTION, code_consumption):
        diagnostics.append(
            Diagnostic(
                "error",
                "ENV_HOOK_ACCEPTANCE_CODE_CONSUMPTION_MISSING",
                path,
                f"31 缺少 Code 消费入口: {item}",
            )
        )
    expected_code_consumption = set(ENV_HOOK_ACCEPTANCE_REQUIRED_CODE_CONSUMPTION)
    for item in code_consumption:
        if item not in expected_code_consumption:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "ENV_HOOK_ACCEPTANCE_CODE_CONSUMPTION_UNSUPPORTED",
                    path,
                    f"31 声明了未被 Code 契约消费的入口: {item}",
                )
            )

    if not rows:
        return diagnostics + [
            Diagnostic(
                "error",
                "ENV_HOOK_ACCEPTANCE_ACTION_TEMPLATE_MISSING",
                path,
                "31 缺少环境 Hook 接入后验收行动模板结构表",
            )
        ]

    if not contract["stop_conditions"]:
        diagnostics.append(Diagnostic("error", "ENV_HOOK_ACCEPTANCE_STOP_CONDITIONS_MISSING", path, "31 必须声明可消费 Stop Conditions"))

    rows_by_structure = {row["结构"]: row for row in rows}
    for structure, terms in ENV_HOOK_ACCEPTANCE_ACTION_TEMPLATE_REQUIRED_ROWS.items():
        row = rows_by_structure.get(structure)
        if not row:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "ENV_HOOK_ACCEPTANCE_ACTION_TEMPLATE_ROW_MISSING",
                    path,
                    f"环境 Hook 接入后验收行动模板缺少结构: {structure}",
                )
            )
            continue
        missing_terms = [term for term in terms if term not in row["最小要求"]]
        for term in missing_terms:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "ENV_HOOK_ACCEPTANCE_ACTION_TEMPLATE_TERM_MISSING",
                    path,
                    f"{structure} 缺少关键要求: {term}",
                )
            )

    missing_flow_terms = [term for term in ENV_HOOK_ACCEPTANCE_FLOW_TERMS if term not in raw]
    for term in missing_flow_terms:
        diagnostics.append(
            Diagnostic(
                "error",
                "ENV_HOOK_ACCEPTANCE_FLOW_TERM_MISSING",
                path,
                f"环境 Hook 接入后验收流程缺少关键要求: {term}",
            )
        )

    for item, terms in ENV_HOOK_ACCEPTANCE_CODE_CONSUMPTION_SUPPORT_TERMS.items():
        for term in [term for term in terms if term not in raw]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "ENV_HOOK_ACCEPTANCE_CODE_CONSUMPTION_SUPPORT_MISSING",
                    path,
                    f"{item} 缺少可消费支撑声明: {term}",
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


def validate_fact_model_member_contract(root: Path, spec_id: str) -> list[Diagnostic]:
    expected = FACT_MODEL_MEMBER_CONTRACTS[spec_id]
    path = SHORT_SPEC_REFS[spec_id]
    full_path = root / path
    diagnostics: list[Diagnostic] = []
    if not full_path.exists():
        return [Diagnostic("error", "FACT_MEMBER_SPEC_MISSING", path, f"{spec_id} {expected['member']} 成员规范缺失")]

    raw = full_path.read_text(encoding="utf-8")
    sections = h2_sections(raw)
    contract = parse_fact_model_member_contract(spec_id, root)
    member = expected["member"]

    code_consumption = contract["code_consumption"]
    if not isinstance(code_consumption, list):
        diagnostics.append(Diagnostic("error", "FACT_MEMBER_CODE_CONSUMPTION_INVALID", path, f"{spec_id} code_consumption 必须是列表"))
        code_consumption = []
    for item in _missing_exact_values(expected["required_code_consumption"], code_consumption):
        diagnostics.append(
            Diagnostic(
                "error",
                "FACT_MEMBER_CODE_CONSUMPTION_MISSING",
                path,
                f"{spec_id} {member} 缺少 Code 消费入口: {item}",
            )
        )

    status_values = [row["status"] for row in contract["statuses"]]
    for status in _missing_exact_values(expected["required_statuses"], status_values):
        diagnostics.append(
            Diagnostic(
                "error",
                "FACT_MEMBER_STATUS_MISSING",
                path,
                f"{member} 状态闭集缺少: {status}",
            )
        )

    source_section = sections.get("事实源与实例边界")
    if not source_section:
        diagnostics.append(Diagnostic("error", "FACT_MEMBER_SOURCE_BOUNDARY_MISSING", path, f"{member} 缺少事实源与实例边界章节"))
    else:
        for term in [term for term in expected["source_terms"] if term not in source_section["body"]]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "FACT_MEMBER_SOURCE_BOUNDARY_MISSING",
                    path,
                    f"{member} 事实源边界缺少: {term}",
                )
            )

    state_section = sections.get("状态、证据与关闭边界")
    if not state_section:
        diagnostics.append(Diagnostic("error", "FACT_MEMBER_CLOSURE_BOUNDARY_MISSING", path, f"{member} 缺少状态、证据与关闭边界章节"))
    else:
        for term in [term for term in expected["closure_terms"] if term not in state_section["body"]]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "FACT_MEMBER_CLOSURE_BOUNDARY_MISSING",
                    path,
                    f"{member} 收口边界缺少: {term}",
                )
            )
        for term in [term for term in expected["legacy_terms"] if term not in state_section["body"]]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "FACT_MEMBER_LEGACY_BOUNDARY_MISSING",
                    path,
                    f"{member} legacy 边界缺少: {term}",
                )
            )
        for term in [term for term in expected["special_terms"] if term not in state_section["body"]]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "FACT_MEMBER_SPECIAL_BOUNDARY_MISSING",
                    path,
                    f"{member} 特有边界缺少: {term}",
                )
            )

    human_gate_section = sections.get("Human Gate")
    if not human_gate_section:
        diagnostics.append(Diagnostic("error", "FACT_MEMBER_HUMAN_GATE_BOUNDARY_MISSING", path, f"{member} 缺少 Human Gate 章节"))
    else:
        for term in [term for term in expected["human_gate_terms"] if term not in human_gate_section["body"]]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "FACT_MEMBER_HUMAN_GATE_BOUNDARY_MISSING",
                    path,
                    f"{member} Human Gate 缺少: {term}",
                )
            )

    return diagnostics


def validate_fact_model_member_contracts(root: Path = ROOT) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for spec_id in ("20", "22", "23", "24"):
        diagnostics.extend(validate_fact_model_member_contract(root, spec_id))
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
    ldvh_install_action_template = parse_ldvh_install_action_template(root)
    ldvh_install_spec_contract = parse_ldvh_install_spec_contract(root)
    environment_hook_acceptance_action_template = parse_environment_hook_acceptance_action_template(root)
    environment_hook_acceptance_spec_contract = parse_environment_hook_acceptance_spec_contract(root)
    workcase_action_template = parse_workcase_action_template(root)
    workcase_member_contract = parse_workcase_member_contract(root)
    fact_model_member_contracts = parse_fact_model_member_contracts(root)
    fact_instances = parse_fact_instances(root)
    governed_projects_config = parse_governed_projects_config(root)
    governed_project_config_contract = parse_governed_project_config_contract(root)
    governed_project_resolution = resolve_governed_subject(root, cwd=root, target_paths=[])
    attachment_contracts = {
        "commit_message_contract": parse_commit_message_contract(root),
        "field_registry_contract": parse_field_registry_contract(root),
        "verification_claim_fields": parse_verification_claim_fields(root),
        "governed_project_config_contract": governed_project_config_contract,
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
    diagnostics.extend(validate_implementation_domain_boundaries(root))
    diagnostics.extend(validate_governed_project_spec_boundaries(root))
    diagnostics.extend(validate_governed_projects_config(root))
    diagnostics.extend(validate_attachment_contracts(root))
    diagnostics.extend(validate_git_commit_action_template(root))
    diagnostics.extend(validate_ldvh_install_action_template(root))
    diagnostics.extend(validate_environment_hook_acceptance_action_template(root))
    diagnostics.extend(validate_workcase_action_template(root))
    diagnostics.extend(validate_workcase_member_contract(root))
    diagnostics.extend(validate_fact_model_member_contracts(root))
    diagnostics.extend(validate_fact_instances(root))

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
            "fact_instances": len(fact_instances),
            "governed_projects": len(governed_projects_config["projects"]),
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
            {"path": "specs/30-LDVH安装初始化管辖项目配置行动模板.md", "role": "ldvh_install_action_template"},
            {"path": "specs/31-环境Hook接入后验收行动模板.md", "role": "environment_hook_acceptance_action_template"},
            {"path": "specs/07-Code确定性执行规范.md", "role": "code_determinism"},
            {"path": "specs/08-Web信息同步规范.md", "role": "web_sync"},
            {"path": "specs/09-测试与验证规范.md", "role": "test_verification"},
            {"path": "specs/10-管辖项目配置规范.md", "role": "governed_project_config"},
            {"path": "specs/01-保障与衔接.md", "role": "environment_adaptation"},
            {"path": "specs/20-Spark-火花.md", "role": "fact_model_member_spec"},
            {"path": "specs/21-WorkCase-工作项.md", "role": "workcase_member_spec"},
            {"path": "specs/22-ADR-决策.md", "role": "fact_model_member_spec"},
            {"path": "specs/23-Pitfall-踩坑经验.md", "role": "fact_model_member_spec"},
            {"path": "specs/24-Study-研究报告.md", "role": "fact_model_member_spec"},
            {"path": "ldvh-base/", "role": "fact_instances_root"},
            {"path": TIMING_TABLE_PATH, "role": "consumption_timing_registry"},
            {"path": TAKEOVER_MATRIX_PATH, "role": "takeover_matrix"},
            {"path": governed_projects_config["config_path"], "role": "governed_project_config"},
            {"path": GOVERNED_PROJECTS_CONTRACT_PATH, "role": "governed_project_config_contract"},
        ],
        "specs": [obj.to_dict() for obj in specs],
        "attachments": [obj.to_dict() for obj in attachments],
        "consumption_timings": timings,
        "ai_behavior_requirements": requirements,
        "takeover_matrix": takeover_matrix,
        "foundation_spec_contracts": foundation_spec_contracts,
        "git_commit_action_template": git_commit_action_template,
        "ldvh_install_action_template": ldvh_install_action_template,
        "ldvh_install_spec_contract": ldvh_install_spec_contract,
        "environment_hook_acceptance_action_template": environment_hook_acceptance_action_template,
        "environment_hook_acceptance_spec_contract": environment_hook_acceptance_spec_contract,
        "workcase_action_template": workcase_action_template,
        "workcase_member_contract": workcase_member_contract,
        "fact_model_member_contracts": fact_model_member_contracts,
        "fact_instances": [
            {
                "kind": instance["kind"],
                "spec_id": instance["spec_id"],
                "path": instance["path"],
                "id": instance["id"],
                "type": instance["type"],
                "status": instance["status"],
            }
            for instance in fact_instances
        ],
        "governed_projects_config": governed_projects_config,
        "governed_project_resolution": governed_project_resolution,
        "attachment_contracts": attachment_contracts,
        "diagnostics": diagnostic_dicts,
    }


def build_governed_projects_report(
    root: Path = ROOT,
    cwd: str | Path | None = None,
    target_paths: list[str | Path] | None = None,
    read_write_kind: str = "write",
    config_root: str | Path | None = None,
) -> dict[str, Any]:
    resolution = resolve_governed_subject(
        root,
        cwd=cwd or root,
        target_paths=target_paths or [],
        read_write_kind=read_write_kind,
        config_root=config_root,
    )
    selected_config_path = Path(resolution["config_path_absolute"]) if resolution["config_path_absolute"] else None
    config = parse_governed_projects_config(root, selected_config_path)
    contract = parse_governed_project_config_contract(root)
    diagnostics = [
        diagnostic.to_dict()
        for diagnostic in validate_governed_projects_config(root, selected_config_path)
    ]
    if resolution["blocked"]:
        code = (
            "GOVERNED_PROJECT_CONFIG_HIERARCHY_CONFLICT"
            if resolution["blocked_reason"] == "nested_governed_projects_config"
            else "GOVERNED_PROJECT_BOUNDARY_BLOCKED"
        )
        diagnostics.append({
            "level": "blocking",
            "code": code,
            "path": resolution["governed_subject"] or ",".join(resolution["target_paths"]),
            "message": resolution["message"],
        })
    status = "blocked" if any(item["level"] in {"error", "blocking"} for item in diagnostics) else "ok"
    return {
        "metadata": {
            "read_only": True,
            "authority": "derived_from_governed_project_config",
            "authorization": "none",
            "root": root.as_posix(),
        },
        "summary": {
            "status": status,
            "projects": len(config["projects"]),
            "governed": resolution["governed"],
            "blocked": resolution["blocked"],
            "diagnostics": len(diagnostics),
        },
        "config": config,
        "contract": contract,
        "resolution": resolution,
        "source_refs": unique_dicts(
            config["source_refs"]
            + [
                {"path": SHORT_SPEC_REFS["10"], "role": "governed_project_spec"},
                {"path": GOVERNED_PROJECTS_CONTRACT_PATH, "role": "governed_project_config_contract"},
            ],
            ("path", "role"),
        ),
        "diagnostics": diagnostics,
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
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation = validation if validation is not None else build_validation(root)
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
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation = validation if validation is not None else build_validation(root)
    classification = classify_target_path(target_path)
    action_guide = build_action_guide(
        root,
        consumption_timing="pre_tool_use",
        task=task,
        target_path=classification["target_path"],
        trigger_source=trigger_source,
        validation=validation,
    )

    diagnostics: list[dict[str, str]] = list(validation["diagnostics"])
    target_type = classification["target_type"]
    impact = classification["impact"]
    normalized_target = classification["target_path"]
    governed_project = resolve_governed_subject(
        root,
        cwd=root,
        target_paths=[normalized_target] if normalized_target else [],
        read_write_kind="commit" if operation == "commit" else "write",
    )

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

    if governed_project["blocked"]:
        diagnostics.append({
            "level": "blocking",
            "code": "PREFLIGHT_GOVERNED_PROJECT_BOUNDARY",
            "path": normalized_target,
            "message": governed_project["message"],
            "disposition": governed_project["blocked_reason"],
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
        "governed_project": governed_project,
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


def _commit_gate_diagnostic(level: str, code: str, path: str, message: str, disposition: str = "blocking") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "path": path,
        "message": message,
        "disposition": disposition,
    }


def _commit_message_without_comments(message: str) -> str:
    lines = []
    for line in message.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.lstrip().startswith("#"):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def parse_commit_message(message: str) -> dict[str, Any]:
    cleaned = _commit_message_without_comments(message)
    lines = cleaned.split("\n") if cleaned else []
    header = lines[0].strip() if lines else ""
    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    match = COMMIT_HEADER_RE.match(header)
    parsed: dict[str, Any] = {
        "raw": cleaned,
        "header": header,
        "body": body,
        "type": "",
        "scope": "",
        "breaking": False,
        "description": "",
        "header_valid": False,
        "body_headings": [],
    }
    if match:
        parsed.update({
            "type": match.group("type"),
            "scope": match.group("scope") or "",
            "breaking": bool(match.group("breaking")),
            "description": match.group("description").strip(),
            "header_valid": True,
        })
    parsed["body_headings"] = [
        line.strip().removesuffix(":")
        for line in body.splitlines()
        if line.strip().endswith(":") and len(line.strip()) <= 40
    ]
    return parsed


def commit_contract_values(root: Path = ROOT) -> dict[str, set[str]]:
    def cell_token(value: str) -> str:
        return value.strip().strip("`").strip()

    contract = parse_commit_message_contract(root)
    return {
        "types": {cell_token(row["type"]) for row in contract["types"] if row.get("type")},
        "scopes": {cell_token(row["scope"]) for row in contract["scopes"] if row.get("scope")},
        "body_conditions": {row["条件类型"] for row in contract["body_conditions"] if row.get("条件类型")},
    }


def _commit_scope_for_path(path: str) -> str:
    normalized = path.strip().lstrip("./")
    if normalized.startswith("specs/"):
        return "specs"
    if normalized.startswith("code/"):
        return "code"
    if normalized.startswith("tests/"):
        return "tests"
    if normalized.startswith("web/"):
        return "web"
    if normalized.startswith("rules/"):
        return "rules"
    if normalized.startswith("docs/"):
        return "docs"
    if normalized.startswith("_migration/"):
        return "docs"
    if normalized.startswith(".github/") or normalized.endswith((".yaml", ".yml", ".toml", ".json")):
        return "config"
    if normalized.startswith("ldvh-base/sparks/"):
        return "spark"
    if normalized.startswith("ldvh-base/workcases/"):
        return "workcase"
    if normalized.startswith("ldvh-base/adrs/"):
        return "adr"
    if normalized.startswith("ldvh-base/pitfalls/"):
        return "pitfall"
    if normalized.startswith("ldvh-base/studies/"):
        return "study"
    if normalized.startswith("ldvh-base/"):
        return "workcase"
    return ""


def _commit_path_is_high_impact(path: str) -> bool:
    normalized = path.strip().lstrip("./")
    return (
        normalized.startswith(("specs/", "code/", "tests/", "web/", "rules/", ".github/", "skills/"))
        or normalized in {GOVERNED_PROJECTS_CONFIG_PATH, "pyproject.toml", "package.json", "package-lock.json"}
    )


def _commit_path_changes_boundary(path: str) -> bool:
    normalized = path.strip().lstrip("./")
    return (
        normalized in HIGH_IMPACT_SPEC_PATHS
        or normalized in {
            SHORT_SPEC_REFS["06"],
            SHORT_SPEC_REFS["07"],
            SHORT_SPEC_REFS["08"],
            SHORT_SPEC_REFS["09"],
            COMMIT_MESSAGE_CONTRACT_PATH,
            VERIFICATION_CLAIM_FIELDS_PATH,
            TAKEOVER_MATRIX_PATH,
            GOVERNED_PROJECTS_CONFIG_PATH,
            "_migration/v3-migration-execution-plan.md",
            "_migration/9-v3-mainline-transition-scope.md",
        }
        or normalized.startswith("code/")
        or normalized.startswith("rules/")
    )


def commit_body_required_reasons(changed_paths: list[str]) -> list[str]:
    paths = normalize_path_list(changed_paths)
    reasons: list[str] = []
    scopes = {scope for scope in (_commit_scope_for_path(path) for path in paths) if scope}
    if any(_commit_path_is_high_impact(path) for path in paths):
        reasons.append("高影响文件")
    if any(path.startswith("ldvh-base/") for path in paths):
        reasons.append("事实对象字段")
    if len(paths) >= 2 or len(scopes) >= 2:
        reasons.append("多文件范围")
    if any(_commit_path_changes_boundary(path) for path in paths):
        reasons.append("边界变化")
    return list(dict.fromkeys(reasons))


def build_commit_gate(
    root: Path = ROOT,
    message: str = "",
    changed_paths: list[str] | None = None,
    acknowledged_paths: list[str] | None = None,
    require_read_plan: bool = False,
    hook_integrated: bool = False,
    environment_integrated: bool | None = None,
) -> dict[str, Any]:
    normalized_changed_paths = normalize_path_list(changed_paths)
    normalized_ack_paths = normalize_path_list(acknowledged_paths or [])
    parsed = parse_commit_message(message)
    contract = commit_contract_values(root)
    body_reasons = commit_body_required_reasons(normalized_changed_paths)
    diagnostics: list[dict[str, str]] = []
    effective_environment_integrated = hook_integrated if environment_integrated is None else environment_integrated

    if not parsed["header_valid"]:
        diagnostics.append(_commit_gate_diagnostic(
            "blocking",
            "COMMIT_HEADER_INVALID",
            COMMIT_MESSAGE_CONTRACT_PATH,
            "commit header 必须符合 type(scope): description 或 type: description。",
        ))
    else:
        if parsed["type"] not in contract["types"]:
            diagnostics.append(_commit_gate_diagnostic(
                "blocking",
                "COMMIT_TYPE_NOT_ALLOWED",
                COMMIT_MESSAGE_CONTRACT_PATH,
                f"commit type 不在 03.Att.01 闭集内: {parsed['type']}",
            ))
        if parsed["scope"] and parsed["scope"] not in contract["scopes"]:
            diagnostics.append(_commit_gate_diagnostic(
                "blocking",
                "COMMIT_SCOPE_NOT_ALLOWED",
                COMMIT_MESSAGE_CONTRACT_PATH,
                f"commit scope 不在 03.Att.01 允许枚举内: {parsed['scope']}",
            ))
        if not parsed["description"]:
            diagnostics.append(_commit_gate_diagnostic(
                "blocking",
                "COMMIT_DESCRIPTION_MISSING",
                COMMIT_MESSAGE_CONTRACT_PATH,
                "commit description 不能为空。",
            ))

    if not normalized_changed_paths:
        diagnostics.append(_commit_gate_diagnostic(
            "warning",
            "COMMIT_CHANGED_PATHS_MISSING",
            "git://staged-paths",
            "未提供 changed paths，无法判断 body 条件和影响范围。",
            "follow_up",
        ))

    if body_reasons and not parsed["body"]:
        diagnostics.append(_commit_gate_diagnostic(
            "blocking",
            "COMMIT_BODY_REQUIRED",
            COMMIT_MESSAGE_CONTRACT_PATH,
            "本次提交触发 body 必填条件: " + "；".join(body_reasons),
        ))
    elif body_reasons and COMMIT_REQUIRED_BODY_HEADING not in parsed["body_headings"]:
        diagnostics.append(_commit_gate_diagnostic(
            "blocking",
            "COMMIT_BODY_REQUIRED_HEADING_MISSING",
            COMMIT_MESSAGE_CONTRACT_PATH,
            f"本次提交 body 必须包含 `{COMMIT_REQUIRED_BODY_HEADING}:` 小标题。",
        ))

    if require_read_plan:
        missing_required = [
            path
            for path in RUNTIME_REQUIRED_ENTRY_PATHS
            if path not in normalized_ack_paths
        ]
        if not normalized_ack_paths:
            diagnostics.append(_commit_gate_diagnostic(
                "blocking",
                "COMMIT_READ_PLAN_CONSUMED_EMPTY",
                "runtime://git_commit_msg",
                "commit gate 必须提供 read_plan 消费证据。",
            ))
        elif missing_required:
            diagnostics.append(_commit_gate_diagnostic(
                "blocking",
                "COMMIT_READ_PLAN_CONSUMED_INCOMPLETE",
                "runtime://git_commit_msg",
                "commit gate 缺少入口必读路径: " + "；".join(missing_required),
            ))

    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"error", "blocking"})
    status = "blocked" if blocking else "review_required" if diagnostics else "ok"
    changed_scopes = sorted({scope for scope in (_commit_scope_for_path(path) for path in normalized_changed_paths) if scope})

    return {
        "metadata": {
            "read_only": True,
            "authority": "derived_from_v3_commit_contract",
            "authorization": "none",
            "environment_integrated": effective_environment_integrated,
            "hook_integrated": hook_integrated,
            "integration_scope": "git.commit-msg" if hook_integrated else "none",
            "root": root.as_posix(),
        },
        "summary": {
            "status": status,
            "diagnostics": len(diagnostics),
            "blocking": blocking,
            "message_type": parsed["type"],
            "message_scope": parsed["scope"],
            "changed_paths": len(normalized_changed_paths),
            "changed_scopes": len(changed_scopes),
            "body_required": bool(body_reasons),
            "read_plan_required": require_read_plan,
            "read_plan_consumed": not require_read_plan or not any(
                path for path in RUNTIME_REQUIRED_ENTRY_PATHS if path not in normalized_ack_paths
            ),
            "environment_integrated": effective_environment_integrated,
        },
        "message": parsed,
        "changed_paths": normalized_changed_paths,
        "changed_scopes": changed_scopes,
        "body_required_reasons": body_reasons,
        "acknowledged_paths": normalized_ack_paths,
        "message_acknowledged_paths": [],
        "source_refs": [
            {"path": SHORT_SPEC_REFS["03"], "role": "commit_traceability_rule"},
            {"path": COMMIT_MESSAGE_CONTRACT_PATH, "role": "commit_message_contract"},
            {"path": SHORT_SPEC_REFS["06"], "role": "git_commit_action_template"},
            {"path": SHORT_SPEC_REFS["09"], "role": "verification_boundary"},
            {"path": VERIFICATION_CLAIM_FIELDS_PATH, "role": "verification_claim_fields"},
            {"path": TAKEOVER_MATRIX_PATH, "role": "hook_takeover_mapping"},
        ],
        "diagnostics": diagnostics,
    }


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
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation = validation if validation is not None else build_validation(root)
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
            validation=validation,
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
                validation=validation,
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


def _workflow_stage(
    name: str,
    result: dict[str, Any],
    *,
    status_path: str = "summary.status",
) -> dict[str, Any]:
    summary = result.get("summary", {})
    status = summary.get("status", "")
    diagnostics = result.get("diagnostics", [])
    return {
        "stage": name,
        "status": status,
        "diagnostics": len(diagnostics),
        "blocking": sum(1 for diagnostic in diagnostics if diagnostic.get("level") in {"error", "blocking"}),
        "authorization": result.get("metadata", {}).get("authorization", "none"),
        "status_source": status_path,
    }


def build_e2e_rehearsal(
    root: Path = ROOT,
    target_path: str = "tests/code/test_ldvh_specs_validate.py",
    task: str = "LDVH v3 stage 8 end-to-end rehearsal",
    operation: str = "write",
    trigger_source: str = "manual",
    verification_evidence: list[str] | None = None,
) -> dict[str, Any]:
    normalized_target = target_path.strip().lstrip("./")
    ack_paths = list(RUNTIME_REQUIRED_ENTRY_PATHS)
    evidence = verification_evidence or [
        "python3 -m pytest tests/code _migration/tests -q",
        "python3 code/specs_validate.py all --format text --fail-on-diagnostics",
    ]
    validation = build_validation(root)

    governed = build_governed_projects_report(
        root,
        cwd=root,
        target_paths=[normalized_target] if normalized_target else [],
        read_write_kind="commit" if operation == "commit" else "write",
    )
    session_start = build_runtime_event(
        root,
        event="session_start",
        trigger_source=trigger_source,
        session_id="stage-8-e2e",
        target_path=normalized_target,
        task=task,
        operation=operation,
        validation=validation,
    )
    acknowledge = build_runtime_event(
        root,
        event="acknowledge_read_plan",
        trigger_source=trigger_source,
        session_id="stage-8-e2e",
        target_path=normalized_target,
        task=task,
        operation=operation,
        acknowledged_paths=ack_paths,
        validation=validation,
    )
    pre_tool_use = build_runtime_event(
        root,
        event="pre_tool_use",
        trigger_source=trigger_source,
        session_id="stage-8-e2e",
        target_path=normalized_target,
        task=task,
        operation=operation,
        acknowledged_paths=ack_paths,
        validation=validation,
    )
    git_commit_msg = build_runtime_event(
        root,
        event="git_commit_msg",
        trigger_source=trigger_source,
        session_id="stage-8-e2e",
        target_path=normalized_target,
        task=task,
        operation="commit",
        acknowledged_paths=ack_paths,
        validation=validation,
    )
    completion_claim = build_runtime_event(
        root,
        event="completion_claim",
        trigger_source=trigger_source,
        session_id="stage-8-e2e",
        target_path=normalized_target,
        task=task,
        operation=operation,
        acknowledged_paths=ack_paths,
        verification_evidence=evidence,
        validation=validation,
    )

    stages = [
        _workflow_stage("governed_project_resolution", governed),
        _workflow_stage("session_start", session_start),
        _workflow_stage("acknowledge_read_plan", acknowledge),
        _workflow_stage("pre_tool_use", pre_tool_use),
        _workflow_stage("validation", validation),
        _workflow_stage("git_commit_msg", git_commit_msg),
        _workflow_stage("completion_claim", completion_claim),
    ]
    diagnostics: list[dict[str, str]] = []
    for origin, result in [
        ("governed_project_resolution", governed),
        ("session_start", session_start),
        ("acknowledge_read_plan", acknowledge),
        ("pre_tool_use", pre_tool_use),
        ("validation", validation),
        ("git_commit_msg", git_commit_msg),
        ("completion_claim", completion_claim),
    ]:
        for diagnostic in result.get("diagnostics", []):
            diagnostics.append({**diagnostic, "origin": origin})

    blocking = sum(1 for diagnostic in diagnostics if diagnostic.get("level") in {"error", "blocking"})
    review_required = any(stage["status"] == "review_required" for stage in stages)
    status = "blocked" if blocking else "review_required" if review_required else "ok"

    return {
        "metadata": {
            "read_only": True,
            "authority": "derived_from_existing_v3_runtime_surfaces",
            "authorization": "none",
            "environment_integrated": False,
            "root": root.as_posix(),
        },
        "summary": {
            "status": status,
            "target_path": normalized_target,
            "stages": len(stages),
            "diagnostics": len(diagnostics),
            "blocking": blocking,
            "governed": governed["summary"]["governed"],
            "validation_status": validation["summary"]["status"],
            "environment_integrated": False,
        },
        "input": {
            "target_path": normalized_target,
            "task": task,
            "operation": operation,
            "trigger_source": trigger_source,
            "acknowledged_paths": ack_paths,
            "verification_evidence": evidence,
        },
        "workflow": stages,
        "governed_project": governed["resolution"],
        "read_plan": session_start["action_guide"]["task_read_plan"] if session_start.get("action_guide") else [],
        "preflight": pre_tool_use["preflight"],
        "validation": {
            "summary": validation["summary"],
            "source_refs": validation["source_refs"],
        },
        "git_commit_msg": {
            "summary": git_commit_msg["summary"],
            "receipt": git_commit_msg["receipt"],
        },
        "completion_claim": {
            "summary": completion_claim["summary"],
            "receipt": completion_claim["receipt"],
        },
        "closure_assessment": {
            "static_rehearsal_complete": status == "ok",
            "reduces_ai_burden": [
                "target 归属由 governed project resolver 输出，不靠 AI 记忆判断",
                "session_start 生成 read_plan，pre_tool_use 复用 acknowledged paths",
                "preflight 在写入前给出目标归口、Human Gate 风险和管辖项目边界",
                "completion_claim 必须携带验证证据，不能空口声明完成",
            ],
            "postponed_boundaries": [
                "Hook / Rules / commit gate 尚未接入真实环境",
                "receipt 仍是 stdout-only 过程输出，不是事实源",
                "真实 `ldvh-base/` 实例迁移、Web 写入和正式行动模板实例仍后置",
                "CLI 不创建提交；实际提交仍由主控 AI 按 06 Git 提交行动模板执行",
            ],
            "authorization": "none",
        },
        "source_refs": unique_dicts(
            governed["source_refs"]
            + session_start["source_refs"]
            + acknowledge["source_refs"]
            + pre_tool_use["source_refs"]
            + git_commit_msg["source_refs"]
            + completion_claim["source_refs"]
            + [
                {"path": "_migration/v3-migration-execution-plan.md", "role": "stage_8_plan"},
                {"path": SHORT_SPEC_REFS["06"], "role": "git_commit_action_boundary"},
                {"path": SHORT_SPEC_REFS["10"], "role": "governed_project_boundary"},
            ],
            ("path", "role", "requirement_id"),
        ),
        "diagnostics": diagnostics,
    }
