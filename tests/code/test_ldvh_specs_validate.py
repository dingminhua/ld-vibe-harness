from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys

import ldvh_specs
import runtime_receipt_cache


ROOT = Path(__file__).resolve().parents[2]
ENTRY_ACK_PATHS = [
    "specs/00-理念与构成.md",
    "specs/01-保障与衔接.md",
    "specs/02-AI行为规范.md",
]
CODE_TARGET_ACK_PATHS = [
    *ENTRY_ACK_PATHS,
    "specs/03-事实源与Git溯源规范.md",
    "specs/04-Specs基础规范.md",
    "specs/07-Code确定性执行规范.md",
    "specs/09-测试与验证规范.md",
]
TEST_TARGET_ACK_PATHS = [
    *ENTRY_ACK_PATHS,
    "specs/03-事实源与Git溯源规范.md",
    "specs/04-Specs基础规范.md",
    "specs/09-测试与验证规范.md",
    "specs/07-Code确定性执行规范.md",
]
ACCEPTANCE_SCRATCH_ACK_PATHS = [
    *ENTRY_ACK_PATHS,
    "specs/03-事实源与Git溯源规范.md",
    "specs/04-Specs基础规范.md",
    "specs/30-安装配置与验证行动模板.md",
    "code/docs/02-Environment-Plugin-Practice.md",
]
WORKCASE_TARGET = "ldvh-base/workcases/workcase-0024-v2-deletion-readiness-closure.yaml"
WORKCASE_ACK_PATHS = [
    *ENTRY_ACK_PATHS,
    "specs/03-事实源与Git溯源规范.md",
    "specs/04-Specs基础规范.md",
    "specs/05-事实模型基础规范.md",
    "specs/09-测试与验证规范.md",
    "specs/21-WorkCase-工作项.md",
    WORKCASE_TARGET,
]


def _ack_args(paths: list[str]) -> list[str]:
    args: list[str] = []
    for path in paths:
        args.extend(["--acknowledged-path", path])
    return args


def _copy_specs_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "specs", root / "specs")
    return root


def _copy_specs_and_facts_root(tmp_path: Path) -> Path:
    root = _copy_specs_root(tmp_path)
    shutil.copytree(ROOT / "ldvh-base", root / "ldvh-base")
    return root


def _replace_in_temp(root: Path, rel_path: str, old: str, new: str = "") -> None:
    path = root / rel_path
    raw = path.read_text(encoding="utf-8")
    assert old in raw
    path.write_text(raw.replace(old, new), encoding="utf-8")


def _write_governed_config(root: Path, content: str) -> Path:
    path = root / "LDVH-GOVERNED-PROJECTS.yaml"
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def _diagnostic_codes(result: dict) -> set[str]:
    return {diagnostic["code"] for diagnostic in result["diagnostics"]}


def _run_cli(
    args: list[str],
    *,
    cwd: Path,
    timeout: int = 60,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """运行 CLI 子进程，超时时打印 stdout/stderr 再抛出，避免调试信息丢失。"""
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=check,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        print(f"\n[TIMEOUT] {' '.join(args)} exceeded {timeout}s", flush=True)
        if stdout:
            print(f"[TIMEOUT stdout]\n{stdout}", flush=True)
        if stderr:
            print(f"[TIMEOUT stderr]\n{stderr}", flush=True)
        raise


def test_current_specs_validate_without_diagnostics(validation_result: dict) -> None:
    result = validation_result

    assert result["summary"]["status"] == "ok"
    assert result["diagnostics"] == []


def test_foundation_specs_contracts_are_code_consumable(validation_result: dict) -> None:
    result = validation_result
    contracts = {contract["spec_id"]: contract for contract in result["foundation_spec_contracts"]}

    assert set(contracts) == {"03", "05", "06", "07", "08", "09"}
    assert "commit_contract_boundaries" in contracts["03"]["code_consumption"]
    assert "commit_message_contract_fields" in contracts["03"]["code_consumption"]
    assert "fact_object_admission" in contracts["05"]["code_consumption"]
    assert "field_registry_contract" in contracts["05"]["code_consumption"]
    assert "context_scenario_gate" in contracts["06"]["code_consumption"]
    assert "capability_output_boundary" in contracts["06"]["code_consumption"]
    assert "action_evidence_requirements" in contracts["06"]["code_consumption"]
    assert "git_commit_action_template" not in contracts["06"]["code_consumption"]
    assert "workcase_minimal_action_template" not in contracts["06"]["code_consumption"]
    assert "runtime_facade_contracts" in contracts["07"]["code_consumption"]
    assert "web_code_separation_boundaries" in contracts["08"]["code_consumption"]
    assert "source_ref_display_requirements" in contracts["08"]["code_consumption"]
    assert "verification_claim_fields" in contracts["09"]["code_consumption"]
    assert "failure_blocking_rules" in contracts["09"]["code_consumption"]

    assert [row["requirement"] for row in contracts["06"]["assurance_measures"]] == [
        "来源回指要求",
        "Gate 显式要求",
        "验证要求",
        "能力输出边界",
    ]
    assert all(row["field_style"] == "authorized" for row in contracts["06"]["assurance_measures"])
    assert all(row["evidence"] and row["gap_handling"] for row in contracts["06"]["assurance_measures"])
    assert "8. Code 变更纪律" in contracts["07"]["rule_body_sections"]
    assert any("测试输出" in item for item in contracts["09"]["human_gate"])
    for contract in contracts.values():
        assert contract["source_refs"]
        assert contract["assurance_measures"]
        assert contract["verification_checks"]
        assert contract["human_gate"]
        assert contract["stop_conditions"]


def test_readme_indexes_action_template_specs() -> None:
    raw = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "`30`：安装配置与验证行动模板" in raw
    assert "`31`：Git 提交行动模板" in raw
    assert "`31`：环境 Hook 接入后验收行动模板" not in raw


def test_install_action_template_discloses_runtime_cache_boundary() -> None:
    raw = (ROOT / "specs/30-安装配置与验证行动模板.md").read_text(encoding="utf-8")

    assert "session-scoped runtime receipt cache" in raw
    assert "OS runtime / temporary / cache 目录" in raw
    assert "cache 不能作为事实源或完成证据" in raw
    assert "runtime cache 状态" in raw


def test_assurance_spec_registers_environment_entry_classification_and_payload_contracts(validation_result: dict) -> None:
    result = validation_result
    specs = {spec["object_id"]: spec for spec in result["specs"]}
    attachments = {attachment["object_id"]: attachment for attachment in result["attachments"]}

    spec_01 = specs["01"]
    assert spec_01["path"] == "specs/01-保障与衔接.md"
    assert spec_01["status"] == "active"
    assert spec_01["metadata"]["authority"] == "active"
    assert set(spec_01["metadata"]["code_consumption"]) >= {
        "environment_entry_type_contract",
        "environment_access_classification_contract",
        "runtime_protocol_contract",
        "runtime_payload_contract",
        "install_rollback_contract",
        "removed_top_level_boundary",
        "authorization_none_boundary",
    }
    assert spec_01["metadata"]["parent_spec"] == "specs/00-理念与构成.md"
    assert {
        "01.Att.03",
        "01.Att.04",
        "01.Att.05",
        "01.Att.06",
    }.issubset(attachments)
    assert attachments["01.Att.03"]["metadata"]["parent_spec"] == "specs/01-保障与衔接.md"
    assert attachments["01.Att.05"]["metadata"]["parent_spec"] == "specs/01-保障与衔接.md"


def test_assurance_spec_defines_git_and_environment_hook_boundaries() -> None:
    spec_01 = (ROOT / "specs/01-保障与衔接.md").read_text(encoding="utf-8")
    entry_types = (ROOT / "specs/attachments/01.Att.03-环境入口类型表.md").read_text(encoding="utf-8")
    runtime_payload = (ROOT / "specs/attachments/01.Att.05-runtime-payload字段表.md").read_text(encoding="utf-8")
    rollback = (ROOT / "specs/attachments/01.Att.06-环境安装回滚检查表.md").read_text(encoding="utf-8")

    assert "V3 当前 Hook 分为两类" in spec_01
    assert "V3 不保留独立的 Runtime Protocol 可见入口文件" in spec_01
    assert "任何环境入口只能指向 LDVH Code" in spec_01
    assert "不得通过仓库内的独立协议文件证明安装、接入或自动触发生效" in spec_01
    assert "接入判定分类由 `01.Att.04` 和 Code 环境审计承接" in spec_01
    assert "不恢复 V2 persistent session receipt 存储" in spec_01
    assert "不得被要求为任何目标环境的原生 Hook 时机" in spec_01
    assert "运行态 receipt cache 是 receipt 的短期桥接形态" in spec_01
    assert "不得写入项目 repo、`specs/`、`ldvh-base/`、Spark、受管项目或工作树隐藏目录" in spec_01
    assert "receipt 是过程输出和证据候选" in spec_01
    assert "runtime cache 只能作为过程输出" in spec_01
    assert "Git Hook" in spec_01
    assert "环境 Hook" in spec_01
    assert "只能定位并调用 LDVH" in spec_01
    assert "核心逻辑都必须留在 LDVH Code 中" in spec_01
    assert "LDVH 仅支持具备 AI lifecycle Hook 的协作环境" in spec_01
    assert "LDVH 插件、扩展包或 package" in spec_01
    assert "非管辖项目必须静默 no-op" in spec_01
    assert "不得输出 stdout、systemMessage、additionalContext、deny 决策、read_plan 或完成声明 warning" in spec_01
    assert "卸载时必须移除或禁用该 repo 的 shim" in spec_01
    assert "验证环境不再自动触发 LDVH" in spec_01

    assert "| `git_hook_shim` |" in entry_types
    assert "| `environment_hook` |" in entry_types
    assert "目标环境 LDVH 插件" in entry_types
    assert "Codex 目标环境" in entry_types
    assert "只调用 LDVH" in entry_types
    assert "只指向 LDVH runtime / adapter" in entry_types

    assert "| `cwd` |" in runtime_payload
    assert "| `config_root` |" in runtime_payload
    assert "| `target_paths` |" in runtime_payload
    assert "不得用 LDVH 本体根目录替代外部项目 cwd" in runtime_payload
    assert "runtime receipt cache 字段" in runtime_payload
    assert "$XDG_RUNTIME_DIR/ldvh/codex-hook/receipts/" in runtime_payload
    assert "$TMPDIR/ldvh-codex-hook/receipts/" in runtime_payload
    assert "%LOCALAPPDATA%\\LDVH\\CodexHook\\receipts\\" in runtime_payload
    assert "`expires_at`" in runtime_payload
    assert "默认 TTL 不得超过 30 分钟" in runtime_payload

    assert "| `entry_kind` |" in rollback
    assert "| `runtime_cache_disclosure` |" in rollback
    assert "| `shim_boundary` |" in rollback
    assert "| `rollback_evidence` |" in rollback
    assert "插件或扩展 manifest" in rollback
    assert "恢复或保留原有用户 Hook / 环境配置" in rollback
    assert "清理或说明已过期的 LDVH runtime receipt cache" in rollback


def test_foundation_validator_reports_missing_code_consumption(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/03-事实源与Git溯源规范.md",
        '    - "commit_contract_boundaries"\n',
    )

    result = ldvh_specs.build_validation(root)

    assert "FOUNDATION_CODE_CONSUMPTION_MISSING" in _diagnostic_codes(result)
    assert any(
        diagnostic["path"] == "specs/03-事实源与Git溯源规范.md"
        and "commit_contract_boundaries" in diagnostic["message"]
        for diagnostic in result["diagnostics"]
    )


def test_foundation_validator_reports_missing_assurance_row(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "| Gate 显式要求 | 模板必须写出暂停、分流和 Human Gate 条件；由本文、01、02 保障 | 模板涉及写入、提交、验收或风险接受时 | Gate、Human Gate、Stop Conditions 和交还中的阻断说明 | 缺少 Gate 时停止执行，回到来源规范补齐 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FOUNDATION_ASSURANCE_ROW_MISSING" in _diagnostic_codes(result)
    assert any("Gate 显式要求" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_spec_relation_must_use_authorized_closed_set(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        '  relation: "refines"\n',
        '  relation: "action_template_member"\n',
    )

    result = ldvh_specs.build_validation(root)

    assert "SPEC_RELATION_UNSUPPORTED" in _diagnostic_codes(result)
    assert any("action_template_member" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_foundation_validator_reports_missing_human_gate_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/08-Web信息同步规范.md",
        "4. 将 Web 状态、缓存、筛选或按钮点击升级为事实源或 Human Gate 完成；\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FOUNDATION_HUMAN_GATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("Web 状态" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_web_sync_validator_requires_independent_data_path_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/08-Web信息同步规范.md",
        "Web 和 Code 是同源的并列实现，不是上下游数据依赖。Web 页面/API 的数据路径必须由 Web 自行从 Git 文件事实源、正式 specs、正式事实对象或 Web 自有 API 聚合读取；不得把 Code 输出、Code DTO、validator 内部对象、preflight/action-guide/runtime receipt 作为页面数据源或长期缓存基础。\n\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WEB_CODE_SEPARATION_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_web_sync_validator_rejects_code_output_as_page_data_source(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/08-Web信息同步规范.md",
        "Web 派生状态必须满足：\n",
        "Web 可以使用 Code 输出实现展示。\n\nWeb 派生状态必须满足：\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WEB_CODE_DATA_DEPENDENCY_FORBIDDEN" in _diagnostic_codes(result)


def test_web_sync_validator_requires_diagnostic_reference_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/08-Web信息同步规范.md",
        "Web 可以在测试、审计、调试或不可验证提示中引用 Code 诊断、验证摘要或 source_refs，只能用于对照显示和缺口定位；该引用不得驱动页面字段契约、状态机、排序筛选语义或事实判断。\n\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WEB_DIAGNOSTIC_REFERENCE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_web_sync_validator_requires_native_source_refs_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/08-Web信息同步规范.md",
        "Web 原生实现可以读取、解析、筛选、排序、聚合、缓存和提供 API；这些实现必须使用正式 specs、正式附件和事实对象中的字段与状态契约，保留 source_refs，不得新增第二套字段契约、状态机、规则判断或事实源归口。\n\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WEB_NATIVE_IMPLEMENTATION_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_governed_project_spec_requires_target_first_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/10-安装与配置规范.md",
        "V3 判定管辖项目必须采用 target-first；只有缺少明确 target 时，才允许使用 cwd fallback。",
        "V3 判定管辖项目必须优先使用工作对象。",
    )

    result = ldvh_specs.build_validation(root)

    assert "GOVERNED_PROJECT_TARGET_FIRST_MISSING" in _diagnostic_codes(result)


def test_governed_project_spec_requires_config_hierarchy_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/10-安装与配置规范.md",
        "同一路径链上只能存在一个 active `LDVH-GOVERNED-PROJECTS.yaml`。",
        "",
    )

    result = ldvh_specs.build_validation(root)

    assert "GOVERNED_PROJECT_CONFIG_BOUNDARY_MISSING" in _diagnostic_codes(result)
    assert any("同一路径链" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_governed_project_spec_requires_git_project_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/10-安装与配置规范.md",
        "管辖项目必须是 Git 管理的项目",
        "",
    )

    result = ldvh_specs.build_validation(root)

    assert "GOVERNED_PROJECT_CONFIG_BOUNDARY_MISSING" in _diagnostic_codes(result)
    assert any("管辖项目必须是 Git 管理的项目" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_install_config_spec_requires_install_plan_contract(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/10-安装与配置规范.md",
        "install_plan",
        "installation plan",
    )

    result = ldvh_specs.build_validation(root)

    assert "INSTALL_CONFIG_CONTRACT_MISSING" in _diagnostic_codes(result)
    assert any("install_plan" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_install_config_spec_requires_apply_gate_contract(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/10-安装与配置规范.md",
        "`apply` 是唯一可以写入",
        "`apply` 可以执行安装",
    )

    result = ldvh_specs.build_validation(root)

    assert "INSTALL_CONFIG_CONTRACT_MISSING" in _diagnostic_codes(result)
    assert any("`apply` 是唯一可以写入" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_install_config_spec_requires_environment_strategy_contract(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/10-安装与配置规范.md",
        "environment_strategy",
        "environment mode",
    )

    result = ldvh_specs.build_validation(root)

    assert "INSTALL_ENVIRONMENT_STRATEGY_MISSING" in _diagnostic_codes(result)
    assert any("environment_strategy" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_governed_project_contract_reports_missing_resolution_field(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/attachments/10.Att.01-管辖项目配置字段表.md",
        "| `unknown_reason` | 条件字符串 | 未命中或不确定时说明原因 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "GOVERNED_PROJECT_RESOLUTION_FIELD_CONTRACT_MISSING" in _diagnostic_codes(result)


def test_fact_model_validator_reports_instance_rule_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/05-事实模型基础规范.md",
        "事实实例不得定义、重写或授权任何事实模型规则、字段闭集、状态机、验证口径或 Human Gate。",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_INSTANCE_RULE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_fact_model_validator_reports_fixture_as_instance_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/05-事实模型基础规范.md",
        "测试夹具不得被写成事实实例；它只能提供验证输入或负例样例。",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_INSTANCE_FIXTURE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_fact_model_validator_reports_migration_as_instance_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/05-事实模型基础规范.md",
        "已从工作树删除的迁移材料不得被写成事实实例；历史迁移记录只可在审计追溯、争议复核或历史取证时查询，不作为当前 V3 规则、实例字段或验收依据。",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_INSTANCE_MIGRATION_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_v2_deletion_readiness_forbids_git_history_as_migration_exit(tmp_path: Path) -> None:
    root = _copy_specs_and_facts_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "V2 30-59 成员全文不在当前工作树保留，未进入当前 V3 specs、事实对象或明确 WorkCase 待办的内容不得视为已承接。",
        "V2 30-59 成员全文不在当前工作树保留，需要时通过 Git history 追溯。",
    )

    result = ldvh_specs.build_validation(root)

    assert "V2_DELETION_HISTORY_FALLBACK_FORBIDDEN" in _diagnostic_codes(result)


def test_fact_model_validator_reports_missing_field_term_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/05-事实模型基础规范.md",
        "6. 字段名不得与 `specs/attachments/04.Att.06-术语表.md` 中的术语含义冲突；确需复用术语时，必须说明字段语义和术语边界。\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_FIELD_TERM_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_migrated_attachment_contracts_are_code_consumable(validation_result: dict) -> None:
    result = validation_result
    contracts = result["attachment_contracts"]

    assert {row["type"].strip("`") for row in contracts["commit_message_contract"]["types"]} >= {"feat", "fix", "docs", "test"}
    assert {row["scope"].strip("`") for row in contracts["commit_message_contract"]["scopes"]} >= {"specs", "code", "tests"}
    assert {row["列"].strip("`") for row in contracts["field_registry_contract"]["columns"]} >= {"field_path", "scope", "meaning", "status"}
    assert {row["字段"] for row in contracts["verification_claim_fields"]["fields"]} == {
        "验证目标",
        "验证方式",
        "验证入口",
        "输入范围",
        "关键输出",
        "结论",
        "残留风险",
        "证据回指",
    }
    assert {row["根字段"].strip("`") for row in contracts["governed_project_config_contract"]["root_fields"]} == {
        "product_name",
        "product_description",
        "projects",
    }
    assert {row["项目字段"].strip("`") for row in contracts["governed_project_config_contract"]["project_fields"]} >= {"id", "path", "git"}
    assert {row["resolution字段"].strip("`") for row in contracts["governed_project_config_contract"]["resolution_fields"]} >= {
        "target",
        "normalized_path",
        "status",
        "governed_project_id",
        "unknown_reason",
    }


def test_governed_projects_config_is_code_consumable(validation_result: dict) -> None:
    result = validation_result
    config = result["governed_projects_config"]
    resolution = result["governed_project_resolution"]
    project_ids = [project["id"] for project in config["projects"]]

    assert config["exists"] is True
    assert config["product_name"].strip()
    assert "ldvh-v3" in project_ids
    assert resolution["governed"] is True
    assert resolution["governed_project_id"] == "ldvh-v3"
    assert resolution["governed_via"] == "path"


def test_governed_projects_config_defaults_to_workspace_parent(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    root = workspace / "ldvh"
    root.mkdir(parents=True)
    _write_governed_config(
        workspace,
        f"""
product_name: Test
product_description: Test workspace registry
projects:
  - id: ldvh
    path: {root}
""",
    )

    config = ldvh_specs.parse_governed_projects_config(root)
    diagnostics = ldvh_specs.validate_governed_projects_config(root)

    assert config["config_path"] == (workspace / "LDVH-GOVERNED-PROJECTS.yaml").as_posix()
    assert [project["id"] for project in config["projects"]] == ["ldvh"]
    assert diagnostics == []


def test_governed_projects_config_missing_defaults_to_workspace_parent_path(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    root = workspace / "ldvh"
    root.mkdir(parents=True)

    config = ldvh_specs.parse_governed_projects_config(root)

    assert config["exists"] is False
    assert config["config_path"] == (workspace / "LDVH-GOVERNED-PROJECTS.yaml").as_posix()


def test_governed_projects_config_prefers_workspace_parent_over_legacy_root_config(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    root = workspace / "ldvh"
    root.mkdir(parents=True)
    _write_governed_config(
        workspace,
        f"""
product_name: Test
product_description: Test workspace registry
projects:
  - id: workspace-project
    path: {root}
""",
    )
    _write_governed_config(
        root,
        f"""
product_name: Legacy
product_description: Legacy registry
projects:
  - id: legacy-root-project
    path: {root}
""",
    )

    config = ldvh_specs.parse_governed_projects_config(root)

    assert config["config_path"] == (workspace / "LDVH-GOVERNED-PROJECTS.yaml").as_posix()
    assert [project["id"] for project in config["projects"]] == ["workspace-project"]


def test_governed_projects_config_reports_duplicate_id(tmp_path: Path) -> None:
    _write_governed_config(
        tmp_path,
        """
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: app-one
  - id: app
    path: app-two
""",
    )

    codes = {diagnostic.code for diagnostic in ldvh_specs.validate_governed_projects_config(tmp_path)}

    assert "GOVERNED_PROJECT_ID_DUPLICATE" in codes


def test_governed_projects_config_reports_forbidden_fields(tmp_path: Path) -> None:
    _write_governed_config(
        tmp_path,
        """
product_name: Test
product_description: Test registry
version: 1
projects:
  - id: app
    path: app
    type: service
    git:
      common_dir: /tmp/app/.git
      status: active
""",
    )

    codes = {diagnostic.code for diagnostic in ldvh_specs.validate_governed_projects_config(tmp_path)}

    assert "GOVERNED_PROJECTS_ROOT_FIELD_FORBIDDEN" in codes
    assert "GOVERNED_PROJECT_FIELD_FORBIDDEN" in codes
    assert "GOVERNED_PROJECT_GIT_FIELD_FORBIDDEN" in codes


def test_governed_project_resolver_uses_target_before_cwd(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    project = root / "governed-app"
    project.mkdir()
    _write_governed_config(
        root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {project}
""",
    )

    report = ldvh_specs.build_governed_projects_report(
        root,
        cwd=root,
        target_paths=[project / "README.md"],
    )

    assert report["summary"]["status"] == "ok"
    assert report["resolution"]["governed"] is True
    assert report["resolution"]["subject_source"] == "target"
    assert report["resolution"]["governed_project_id"] == "app"
    assert report["resolution"]["target_resolutions"][0]["status"] == "governed"


def test_governed_project_resolver_blocks_nested_config_when_config_root_selected(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    project = root / "governed-app"
    project.mkdir()
    _write_governed_config(
        root,
        """
product_name: Test
product_description: Test workspace registry
projects:
  - id: app
    path: governed-app
""",
    )
    _write_governed_config(
        project,
        """
product_name: Test App
product_description: Test app local registry
projects:
  - id: app-local
    path: .
""",
    )

    report = ldvh_specs.build_governed_projects_report(
        root,
        cwd=root,
        target_paths=[project / "README.md"],
        config_root=root,
    )

    assert report["summary"]["status"] == "blocked"
    assert report["resolution"]["blocked"] is True
    assert report["resolution"]["blocked_reason"] == "nested_governed_projects_config"
    assert [item["path"] for item in report["resolution"]["config_hierarchy"]["configs"]] == [
        "LDVH-GOVERNED-PROJECTS.yaml",
        "governed-app/LDVH-GOVERNED-PROJECTS.yaml",
    ]
    assert "GOVERNED_PROJECT_CONFIG_HIERARCHY_CONFLICT" in _diagnostic_codes(report)


def test_governed_project_resolver_project_scope_ignores_parent_config_without_config_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "governed-app"
    project.mkdir(parents=True)
    _write_governed_config(
        workspace,
        """
product_name: Test
product_description: Test workspace registry
projects:
  - id: workspace-app
    path: governed-app
""",
    )
    _write_governed_config(
        project,
        """
product_name: Test App
product_description: Test app local registry
projects:
  - id: app-local
    path: .
""",
    )

    resolution = ldvh_specs.resolve_governed_subject(
        project,
        cwd=project,
        target_paths=[project / "README.md"],
    )

    assert resolution["blocked"] is False
    assert resolution["governed"] is True
    assert resolution["governed_project_id"] == "app-local"
    assert resolution["config_path"] == "LDVH-GOVERNED-PROJECTS.yaml"


def test_governed_project_resolver_noops_for_outside_target(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    project = root / "governed-app"
    outside = root / "outside"
    project.mkdir()
    outside.mkdir()
    _write_governed_config(
        root,
        """
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: governed-app
""",
    )

    resolution = ldvh_specs.resolve_governed_subject(root, cwd=root, target_paths=[outside / "README.md"])

    assert resolution["governed"] is False
    assert resolution["blocked"] is False
    assert resolution["target_resolutions"][0]["status"] == "not_governed"


def test_governed_project_resolver_blocks_mixed_write_targets(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    project = root / "governed-app"
    outside = root / "outside"
    project.mkdir()
    outside.mkdir()
    _write_governed_config(
        root,
        """
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: governed-app
""",
    )

    resolution = ldvh_specs.resolve_governed_subject(
        root,
        cwd=root,
        target_paths=[project / "a.txt", outside / "b.txt"],
        read_write_kind="write",
    )

    assert resolution["blocked"] is True
    assert resolution["blocked_reason"] == "mixed_governed_and_ungoverned_targets"


def test_governed_project_resolver_matches_git_worktree_common_dir(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    repo = root / "repo"
    worktree = root / "repo-worktree"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "ldvh@example.test"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "LDVH Test"], cwd=repo, check=True, timeout=30)
    (repo / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "test: init"], cwd=repo, check=True, capture_output=True, text=True, timeout=30)
    subprocess.run(["git", "worktree", "add", str(worktree)], cwd=repo, check=True, capture_output=True, text=True, timeout=30)
    common_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()
    _write_governed_config(
        root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
    git:
      common_dir: {common_dir}
""",
    )

    resolution = ldvh_specs.resolve_governed_subject(root, cwd=root, target_paths=[worktree / "README.md"])

    assert resolution["governed"] is True
    assert resolution["governed_via"] == "git.common_dir"
    assert resolution["governed_project_id"] == "app"


def test_commit_contract_attachment_reports_missing_required_field(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/attachments/03.Att.01-Commit-Message契约字段表.md",
        "| `description` | 必填 | 简体中文简短说明 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "COMMIT_CONTRACT_FIELD_MISSING" in _diagnostic_codes(result)


def test_field_registry_attachment_reports_missing_registered_column(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/attachments/05.Att.01-字段注册表结构.md",
        "| `field_path` | 字段名或重要嵌套字段路径 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FIELD_REGISTRY_COLUMN_MISSING" in _diagnostic_codes(result)


def test_verification_claim_attachment_reports_missing_evidence_ref(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/attachments/09.Att.01-验证声明字段表.md",
        "| 证据回指 | 回指命令输出、测试入口、事实源、截图说明、Human 记录或提交记录 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "VERIFICATION_CLAIM_FIELD_MISSING" in _diagnostic_codes(result)


def test_attachment_parent_reference_is_required(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/03-事实源与Git溯源规范.md",
        '    - "specs/attachments/03.Att.01-Commit-Message契约字段表.md"\n',
    )

    result = ldvh_specs.build_validation(root)

    assert "ATTACHMENT_PARENT_REFERENCE_MISSING" in _diagnostic_codes(result)


def test_all_attachments_must_be_listed_by_parent_related_specs(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/10-安装与配置规范.md",
        '    - "specs/attachments/10.Att.02-路径语义与规范化规则.md"\n',
    )

    result = ldvh_specs.build_validation(root)

    assert "ATTACHMENT_PARENT_REFERENCE_MISSING" in _diagnostic_codes(result)
    assert any("10.Att.02" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_fact_source_validator_reports_chat_as_fact_source_gap(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/03-事实源与Git溯源规范.md",
        "| 聊天和 AI 推理 | 只能作为当前上下文或候选判断，稳定结论必须回写。 |\n",
        "| AI 推理 | 只能作为当前上下文或候选判断，稳定结论必须回写。 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "NON_FACT_SOURCE_EXCLUSION_MISSING" in _diagnostic_codes(result)


def test_fact_source_validator_reports_process_output_without_ai_qualification(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/03-事实源与Git溯源规范.md",
        "过程输出必须先被 AI 定性，再决定是否记录为证据或回写。",
        "过程输出再决定是否记录为证据或回写。",
    )

    result = ldvh_specs.build_validation(root)

    assert "PROCESS_OUTPUT_QUALIFICATION_MISSING" in _diagnostic_codes(result)


def test_fact_source_validator_reports_process_output_without_writeback_fields(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/03-事实源与Git溯源规范.md",
        "回写必须说明目标事实源、来源证据、采纳范围和验证方式。",
        "回写必须说明来源证据和验证方式。",
    )

    result = ldvh_specs.build_validation(root)

    assert "PROCESS_OUTPUT_WRITEBACK_REQUIREMENT_MISSING" in _diagnostic_codes(result)


def test_verification_validator_reports_test_output_as_fact_source_gap(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/09-测试与验证规范.md",
        "测试证据用于支持判断，不成为事实源。测试输出、覆盖率、截图、trace、缓存、Mock 数据和临时报告不得替代 specs、事实对象、Git 记录或 Human Gate。\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "TEST_OUTPUT_FACT_SOURCE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_verification_validator_reports_missing_failure_blocking_rule(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/09-测试与验证规范.md",
        "2. 关键验证未运行且没有等价验证；\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FAILURE_BLOCKING_RULE_MISSING" in _diagnostic_codes(result)


def test_implementation_domain_boundaries_are_code_consumable(validation_result: dict) -> None:
    result = validation_result

    assert "SPECS_IMPLEMENTATION_DOMAIN_BOUNDARY_MISSING" not in _diagnostic_codes(result)
    assert "SPECS_STATE_OWNERSHIP_BOUNDARY_MISSING" not in _diagnostic_codes(result)
    assert "CODE_IMPLEMENTATION_PRACTICE_BOUNDARY_MISSING" not in _diagnostic_codes(result)
    assert "WEB_IMPLEMENTATION_PRACTICE_BOUNDARY_MISSING" not in _diagnostic_codes(result)
    assert "TEST_IMPLEMENTATION_PRACTICE_BOUNDARY_MISSING" not in _diagnostic_codes(result)


def test_specs_validator_reports_missing_implementation_domain_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/04-Specs基础规范.md",
        "实现域实践细节由对应实现域承接",
        "实践细节由对应位置承接",
    )

    result = ldvh_specs.build_validation(root)

    assert "SPECS_IMPLEMENTATION_DOMAIN_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_specs_validator_reports_missing_state_ownership_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/04-Specs基础规范.md",
        "只有两类对象可以拥有可记录、可迁移、可校验的状态",
        "多类对象可以拥有可记录、可迁移、可校验的状态",
    )

    result = ldvh_specs.build_validation(root)

    assert "SPECS_STATE_OWNERSHIP_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_code_validator_reports_missing_code_practice_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/07-Code确定性执行规范.md",
        "Code 实践由 `code/` 和 `code/docs/` 承接",
        "Code 实践由实现域承接",
    )

    result = ldvh_specs.build_validation(root)

    assert "CODE_IMPLEMENTATION_PRACTICE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_code_validator_reports_missing_web_practice_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/08-Web信息同步规范.md",
        "Web 实践由 `web/` 和 `web/docs/` 承接",
        "Web 实践由实现域承接",
    )

    result = ldvh_specs.build_validation(root)

    assert "WEB_IMPLEMENTATION_PRACTICE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_code_validator_reports_missing_test_practice_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/09-测试与验证规范.md",
        "V3 不强制要求 `tests/docs/` 作为固定目录。",
        "V3 不设置固定测试文档目录。",
    )

    result = ldvh_specs.build_validation(root)

    assert "TEST_IMPLEMENTATION_PRACTICE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_action_template_foundation_rules_are_code_consumable(validation_result: dict) -> None:
    result = validation_result
    raw = (ROOT / "specs/06-行动模板基础规范.md").read_text(encoding="utf-8")

    assert "git_commit_action_template" in result
    assert "workcase_action_template" not in result
    assert "引用与复制的判断标准" in raw
    assert "七结构粒度要求" in raw
    assert "本文不承载具体模板示范" in raw
    assert "字段闭集、字段定义、枚举完整列表" in raw
    assert "不展开来源 spec" in raw
    assert "不重述来源 spec" in raw


def test_git_commit_action_template_is_code_consumable(validation_result: dict) -> None:
    result = validation_result
    raw = (ROOT / "specs/31-Git提交行动模板.md").read_text(encoding="utf-8")
    rows = {row["结构"]: row["最小要求"] for row in result["git_commit_action_template"]}
    contract = result["git_commit_spec_contract"]

    assert set(rows) == {"Context", "Scenario", "Gate", "执行", "验证", "回写", "交还"}
    assert contract["spec_id"] == "31"
    assert set(contract["code_consumption"]) == set(ldvh_specs.GIT_COMMIT_REQUIRED_CODE_CONSUMPTION)
    assert contract["action_template"]
    assert contract["stop_conditions"]
    assert contract["source_refs"]
    assert 'relation: "refines"' in raw
    assert "不定义 commit message 字段闭集" in raw
    assert "不复制 type / scope 枚举" in raw
    assert "不得安装、升级、禁用或卸载 Git Hook" in raw

    assert "用户提交目标" in rows["Context"]
    assert "staged / unstaged / untracked" in rows["Context"]
    assert "03.Att.01" in rows["Context"]
    assert "09.Att.01" in rows["Context"]
    assert "用户明确要求提交" in rows["Scenario"]
    assert "提交门禁阻断分流" in rows["Scenario"]
    assert "已暂存变更与用户目标不一致" in rows["Gate"]
    assert "提交拆分边界不清" in rows["Gate"]
    assert "Hook / commit gate / 环境入口" in rows["Gate"]
    assert "只 stage 本次范围内文件" in rows["执行"]
    assert "commit validator" in rows["执行"]
    assert "不安装 Hook" in rows["执行"]
    assert "验证目标" in rows["验证"]
    assert "残留风险" in rows["验证"]
    assert "Git commit records" in rows["回写"]
    assert "commit hash" in rows["交还"]
    assert "剩余 Git 工作区摘要" in rows["交还"]


def test_git_commit_action_template_reports_missing_commit_contract_reference(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/31-Git提交行动模板.md",
        "    - \"commit_message_contract_reference\"\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "GIT_COMMIT_CODE_CONSUMPTION_MISSING" in _diagnostic_codes(result)
    assert any("commit_message_contract_reference" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_git_commit_action_template_reports_missing_scope_gate(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/31-Git提交行动模板.md",
        "已暂存变更与用户目标不一致、",
    )

    result = ldvh_specs.build_validation(root)

    assert "GIT_COMMIT_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("已暂存变更与用户目标不一致" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_action_template_foundation_reports_missing_copy_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "| 来源 spec 的字段闭集、字段定义、枚举值完整列表 | 否 | 是 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "ACTION_TEMPLATE_REFERENCE_COPY_BOUNDARY_MISSING" in _diagnostic_codes(result)
    assert any("来源 spec 的字段闭集、字段定义、枚举值完整列表" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_action_template_foundation_reports_missing_granularity_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "七结构粒度要求",
        "结构粒度要求",
    )

    result = ldvh_specs.build_validation(root)

    assert "ACTION_TEMPLATE_GRANULARITY_RULE_MISSING" in _diagnostic_codes(result)
    assert any("七结构粒度要求" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_action_template_foundation_reports_missing_concrete_example_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "本文不承载具体模板示范",
    )

    result = ldvh_specs.build_validation(root)

    assert "ACTION_TEMPLATE_CONCRETE_EXAMPLE_BOUNDARY_MISSING" in _diagnostic_codes(result)
    assert any("本文不承载具体模板示范" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_is_code_consumable(validation_result: dict) -> None:
    result = validation_result
    raw = (ROOT / "specs/30-安装配置与验证行动模板.md").read_text(encoding="utf-8")
    rows = {row["结构"]: row["最小要求"] for row in result["ldvh_install_action_template"]}
    contract = result["ldvh_install_spec_contract"]

    assert set(rows) == {"Context", "Scenario", "Gate", "执行", "验证", "回写", "交还"}
    assert contract["spec_id"] == "30"
    assert set(contract["code_consumption"]) == set(ldvh_specs.LDVH_INSTALL_REQUIRED_CODE_CONSUMPTION)
    assert contract["action_template"]
    assert contract["stop_conditions"]
    assert contract["source_refs"]
    assert 'relation: "refines"' in raw
    assert "specs/31-环境Hook接入后验收行动模板.md" not in raw
    assert "环境Hook接入后验收" not in raw

    assert "目标环境" in rows["Context"]
    assert "LDVH 本体路径" in rows["Context"]
    assert "目标工作区根目录" in rows["Context"]
    assert "默认值是 LDVH 本体路径的父目录" in raw
    assert "不得把目标工作区根目录写成“待确认”" in raw
    assert "目标工作区配置" in rows["Context"]
    assert "事实源目录状态" in rows["Context"]
    assert "Git Hook 状态" in rows["Context"]
    assert "Runtime Protocol" in rows["Context"]
    assert "安装 LDVH" in rows["Scenario"]
    assert "配置层级冲突" in rows["Gate"]
    assert "最终确认" in rows["Gate"]
    assert "bootstrap discovery" in rows["执行"]
    assert "五阶段" in rows["执行"]
    assert "环境入口按 01" in rows["执行"]
    assert "配置和事实源按 10" in rows["执行"]
    assert "验证按 09" in rows["执行"]
    assert "具体命令、输出字段和实现入口" in rows["执行"]
    assert "验证入口" in rows["验证"]
    assert "09.Att.01" in rows["验证"]
    assert "断点后 lifecycle 验证" in rows["验证"]
    assert "通过标准" in rows["验证"]
    assert "不得把 runtime receipt" in rows["回写"]
    assert "管辖项目配置事实源" in rows["回写"]
    assert "环境适配缺口" in rows["回写"]
    assert "断点恢复入口语" in rows["交还"]
    assert "可复制只读可见性探针" in rows["交还"]
    assert "真实工作流验证清单" in rows["交还"]
    assert "失败信息包" in rows["交还"]
    assert "环境接入判定来源" in rows["交还"]


def test_ldvh_install_action_template_defines_action_stage_contract(validation_result: dict) -> None:
    raw = (ROOT / "specs/30-安装配置与验证行动模板.md").read_text(encoding="utf-8")

    assert "安装行动阶段与 Human Gate" in raw
    assert "行动阶段与交互边界" in raw
    assert "用户告知、用户选择与检查事实" in raw
    assert "路径发现、配置位置与管辖项目清单" in raw
    assert "安装方案预览与最终确认" in raw
    assert "环境入口承接与统一验证边界" in raw
    assert "写入完成后的断点引导与 lifecycle 验证" in raw
    assert "写入完成交还、断点恢复与失败信息包" in raw
    assert "五个阶段" in raw
    assert "路径确认" in raw
    assert "安装前检查" in raw
    assert "安装选项" in raw
    assert "安装方案预览" in raw
    assert "最终确认" in raw
    assert "不得新增安装运行时状态闭集" in raw
    assert "回答组织分为两层" in raw
    assert "场景复杂度精简呈现" in raw
    assert "用户告知清单必须作为 4/5 安装方案预览的必含内容交给 Human 确认" in raw
    assert "每次只问一个问题" in raw
    assert "该选择不是执行授权" in raw
    assert "5/5 最终确认必须直接询问“执行方案”或“不执行，停止安装”" in raw
    assert "不得继续解释流程或再次索要同一授权" in raw
    assert "当前配置摘要" in raw
    assert "管辖项目配置位置" in raw
    assert "项目内 / 用户级 / LDVH 本体目录边界" in raw
    assert "目标环境入口承接" in raw
    assert "30 只支持目标 AI 环境通过可安装、可验证、可阻断的 lifecycle Hook 接入 LDVH" in raw
    assert "Runtime Protocol" in raw
    assert "目标环境暂不属于 LDVH 支持范围" in raw
    assert "需先实现目标环境插件" in raw
    assert "目标环境插件缺口提示" in raw
    assert "不会执行任何替代环境写入" in raw
    assert "按 spec 33 编写目标环境 LDVH 插件 / adapter" in raw
    assert "统一验证标准" in raw
    assert "runtime 循环在真实 AI lifecycle 里产出可复核的当次可观察依据" in raw
    assert "断点后 lifecycle 验收必须先明确 AI 与 Human 的职责分工" in raw
    assert "Human 不负责理解 integrated 分类" in raw
    assert "不得作为环境 Hook integrated 的替代验收" in raw
    assert "自然语言触发任务" in raw
    assert "可复制的只读可见性探针与最小 Human 验收卡" in raw
    assert "断点恢复协议" in raw
    assert "恢复入口语" in raw
    assert "运行时入口" in raw
    assert "授权 / trust 检查" in raw
    assert "必须先提示用户确认插件已授权、已信任或无待处理授权" in raw
    assert "Hook 触发依据检查" in raw
    assert "未取得 Hook 触发依据" in raw
    assert "不得用手动探针替代真实 Hook 触发依据" in raw
    assert "环境 PreToolUse 映射出的 `ldvh.pre_tool_use` 阻断" in raw
    assert "若出现 PreToolUse 阻断" not in raw
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in raw
    assert "PREFLIGHT_TARGET_UNKNOWN" in raw
    assert "Hook 已触发，但 read_plan 消费依据链路未通过" in raw
    assert "不得继续写成 lifecycle 未触发" in raw
    assert "真实工作流验证清单" in raw
    assert "本次验证通过" in raw
    assert "本次验证失败" in raw
    assert "本次未验证" in raw
    assert "用户主结论必须明确写入是否完成" in raw
    assert "Runtime 入口与 lifecycle 验证" in raw
    assert "提交消息检查" in raw
    assert "授权 / trust 确认必须排在重启或新开会话之前" in raw
    assert "Hook 触发依据检查排在手动 runtime 探针之前" in raw
    assert "手动 runtime 探针只能由 AI 作为技术对照或失败定位使用" in raw
    assert "不能写成 Human 验收动作" in raw
    assert "失败信息包" in raw
    assert "最终确认只展示两个主选项" in raw
    assert "1 执行方案" in raw
    assert "2 不执行，停止安装" in raw
    assert "选择执行后才会开始写入" in raw
    assert "自动接入待验收" not in raw
    assert "进入 31" not in raw
    assert "specs/31" not in raw
    assert "环境Hook接入后验收" not in raw


def test_environment_lifecycle_docs_use_ldvh_canonical_event_direction() -> None:
    documents = {
        "spec30": ROOT / "specs/30-安装配置与验证行动模板.md",
        "spec33": ROOT / "specs/33-环境插件编写与更新行动模板.md",
        "practice02": ROOT / "code/docs/02-Environment-Plugin-Practice.md",
        "practice03": ROOT / "code/docs/03-LDVH-Install-Wizard-Practice.md",
    }
    contents = {name: path.read_text(encoding="utf-8") for name, path in documents.items()}

    assert "环境 PreToolUse 映射出的 `ldvh.pre_tool_use` 阻断" in contents["spec30"]
    assert "目标环境 lifecycle event 映射到 LDVH canonical event" in contents["spec33"]
    assert "解析环境原生事件名并映射到 LDVH canonical event" in contents["spec33"]
    assert "`ldvh.session_start`" in contents["spec33"]
    assert "`ldvh.pre_tool_use`" in contents["spec33"]
    assert "`ldvh.completion_claim`" in contents["spec33"]
    assert "映射目标环境 lifecycle event 到 LDVH canonical event" in contents["practice02"]
    assert "LDVH canonical event 是否由目标环境真实触发" in contents["practice02"]
    assert "`ldvh.pre_tool_use` 阻断" in contents["practice02"]
    assert "| 环境 `SessionStart` -> `ldvh.session_start` |" in contents["practice02"]
    assert "| 环境 `PreToolUse` -> `ldvh.pre_tool_use` 负例 |" in contents["practice02"]
    assert "| 环境 `Stop` / completion -> `ldvh.completion_claim` |" in contents["practice02"]
    assert "观察映射后的 `ldvh.session_start`、`ldvh.pre_tool_use` 负例" in contents["practice02"]
    assert "环境 PreToolUse 映射到 `ldvh.pre_tool_use` 后的阻断" in contents["practice03"]

    assert "| `SessionStart` |" not in contents["practice02"]
    assert "| `PreToolUse` 负例 |" not in contents["practice02"]
    assert "| `PreToolUse` 正例 |" not in contents["practice02"]
    assert "逐项触发 Git `commit-msg` 正反例、`SessionStart`、`PreToolUse` 负例" not in contents["practice02"]

    combined = "\n".join(contents.values())
    assert "V3 runtime event" not in combined
    assert "若出现 PreToolUse 阻断" not in combined
    assert "PreToolUse 阻断 |" not in combined
    assert "`session_start`（映射到目标环境 SessionStart" not in combined
    assert "到 V3 runtime event" not in combined


def test_install_wizard_practice_defaults_workspace_root_to_ldvh_parent() -> None:
    raw = (ROOT / "code/docs/03-LDVH-Install-Wizard-Practice.md").read_text(encoding="utf-8")

    assert "未显式指定时默认使用 LDVH 本体路径的父目录" in raw
    assert "由 LDVH 本体父目录推导" in raw
    assert "不要把该值写成“待确认”" in raw
    assert "断点后 lifecycle 验收不得把 Human 变成技术执行者" in raw
    assert "按自然语言验收卡观察新会话真实 lifecycle 输出" in raw
    assert "新开目标环境窗口或会话，按自然语言验收卡观察真实 lifecycle 输出" in raw
    assert "状态牌固定包含" not in raw
    assert "安装向导状态机" not in raw


def test_environment_plugin_practice_defines_human_lifecycle_card_boundary() -> None:
    raw = (ROOT / "code/docs/02-Environment-Plugin-Practice.md").read_text(encoding="utf-8")

    assert "断点后验收卡必须区分 AI 和 Human 职责" in raw
    assert "Human 只负责在目标环境里确认插件页面状态" in raw
    assert "按自然语言任务触发真实 lifecycle" in raw
    assert "不得要求 Human 手动运行 `runtime_adapter.py` 或 shim 命令来证明 integrated" in raw
    assert "只能作为安装检测或失败定位对照" in raw


def test_ldvh_install_action_template_reports_missing_code_consumption(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        '    - "install_user_disclosure_checklist"\n',
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_CODE_CONSUMPTION_MISSING" in _diagnostic_codes(result)
    assert any("install_user_disclosure_checklist" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_unsupported_code_consumption(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        '    - "stop_conditions"\n',
        '    - "stop_conditions"\n    - "phantom_install_capability"\n',
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_CODE_CONSUMPTION_UNSUPPORTED" in _diagnostic_codes(result)
    assert any("phantom_install_capability" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_target_workspace_gate(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "、目标工作区根目录",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("目标工作区根目录" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_bootstrap_discovery(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "bootstrap discovery",
        "",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("bootstrap discovery" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_plugin_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "不直接写入用户环境 Hook 系统文件",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_ACTION_TEMPLATE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_ldvh_install_action_template_reports_missing_cli_does_not_replace_template_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "CLI 不替代本文",
        "CLI 已替代本文",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_ACTION_TEMPLATE_BOUNDARY_MISSING" in _diagnostic_codes(result)
    assert any("CLI 不替代本文" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_second_rule_source_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "不得复制 CLI、10、01 或 07 的机器规则形成第二规则源",
        "可以按需要复制机器规则",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_ACTION_TEMPLATE_BOUNDARY_MISSING" in _diagnostic_codes(result)
    assert any("第二规则源" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_unsupported_config_locations(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "项目内 / 用户级 / LDVH 本体目录边界",
        "",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_CODE_CONSUMPTION_SUPPORT_MISSING" in _diagnostic_codes(result)
    assert any("项目内 / 用户级 / LDVH 本体目录边界" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_workspace_config_location(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "管辖项目配置位置",
        "配置文件位置可在执行时说明",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_CODE_CONSUMPTION_SUPPORT_MISSING" in _diagnostic_codes(result)
    assert any("管辖项目配置位置" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_action_stage_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "不得新增安装运行时状态闭集",
        "可以按安装过程新增临时状态闭集",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("不得新增安装运行时状态闭集" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_internal_summary_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "回答组织分为两层",
        "步骤摘要",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("回答组织分为两层" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_final_confirmation_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "最终确认前",
        "执行前",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("最终确认前" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_ambiguous_preview_execution_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "该选择不是执行授权",
        "该选择可作为执行授权",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("该选择不是执行授权" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_environment_specific_prompt(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "环境 Hook 或插件提示必须按当前目标环境命名",
        "环境 Hook 或插件提示可以沿用当前示例环境名称",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("环境 Hook 或插件提示必须按当前目标环境命名" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_runtime_adapter_rule(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "运行时入口",
        "运行时适配器",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("运行时入口" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_plugin_acceptance_standard(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "安装检测通过",
        "验收判断",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_CODE_CONSUMPTION_SUPPORT_MISSING" in _diagnostic_codes(result)
    assert any("安装检测通过" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_unified_flow_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "30 只支持目标 AI 环境通过可安装、可验证、可阻断的 lifecycle Hook 接入 LDVH",
        "可以按 Hook 支持能力拆成两套写入完成流程",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("30 只支持目标 AI 环境通过可安装、可验证、可阻断的 lifecycle Hook 接入 LDVH" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_breakpoint_recovery_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "断点恢复协议",
        "恢复流程",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("断点恢复协议" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_breakpoint_recovery_protocol(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "断点恢复协议",
        "恢复说明",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("断点恢复协议" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_wizard_subsection_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "用户告知、用户选择与检查事实",
        "用户提示",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("用户告知、用户选择与检查事实" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_disclosure_handoff_timing(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-安装配置与验证行动模板.md",
        "用户告知清单必须作为 4/5 安装方案预览的必含内容交给 Human 确认",
        "用户告知清单在执行前说明",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("用户告知清单必须作为 4/5 安装方案预览的必含内容交给 Human 确认" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_workcase_member_contract_is_code_consumable(validation_result: dict) -> None:
    result = validation_result
    contract = result["workcase_member_contract"]

    assert contract["path"] == "specs/21-WorkCase-工作项.md"
    assert set(contract["code_consumption"]) >= {
        "fact_model_member_identity",
        "workcase_source_boundaries",
        "workcase_state_boundaries",
        "workcase_field_contract",
        "workcase_orchestration_contract",
        "workcase_state_required_fields",
        "workcase_closure_boundaries",
        "workcase_human_gate_boundaries",
        "workcase_instance_checks",
    }
    assert [row["status"] for row in contract["statuses"]] == [
        "subagents_plan_reviewing",
        "human_plan_confirming",
        "executing",
        "result_self_checking",
        "subagents_result_reviewing",
        "human_closure_confirming",
        "closed",
    ]
    assert any(item["path"] == "specs/05-事实模型基础规范.md" for item in contract["source_refs"])
    assert any(item["path"] == "specs/attachments/21.Att.01-orchestration字段契约表.md" for item in contract["source_refs"])

    field_contract = contract["field_contract"]
    assert field_contract["path"] == "specs/attachments/21.Att.01-orchestration字段契约表.md"
    registered_paths = {ldvh_specs.strip_inline_code(row["field_path"]) for row in field_contract["fields"]}
    required_fields = {ldvh_specs.strip_inline_code(row["字段"]) for row in field_contract["required_fields"]}
    status_rows = {ldvh_specs.strip_inline_code(row["状态"]): row for row in field_contract["status_requirements"]}

    assert "orchestration.execution_items.status" in registered_paths
    assert "orchestration.plan_review.controller_resolution" in registered_paths
    assert "orchestration.result_review.human_closure_confirmation" in registered_paths
    assert "closure_evidence" in required_fields
    assert "orchestration.result_review.controller_resolution" in status_rows["human_closure_confirming"]["条件必填字段"]
    assert "orchestration.result_review.human_closure_confirmation" in status_rows["closed"]["条件必填字段"]


def test_workcase_member_validator_reports_missing_state(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/21-WorkCase-工作项.md",
        "| `result_self_checking` | 结果自检中；主控正在检查成功标准、验证证据、关闭证据和残留风险 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_STATUS_MISSING" in _diagnostic_codes(result)
    assert any("result_self_checking" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_workcase_member_validator_reports_missing_source_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/21-WorkCase-工作项.md",
        "执行项只能作为 WorkCase 内部字段存在，不得形成独立事实对象、独立编号段、一级 Web 入口或长期被其它对象引用的事实源。",
        "执行项作为 WorkCase 的执行信息存在。",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_SOURCE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_workcase_member_validator_reports_missing_closure_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/21-WorkCase-工作项.md",
        "关闭证据必须包含可读取的 `后续分流 / 收口结果` 段落。",
        "关闭证据必须包含可读取的段落。",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_CLOSURE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_workcase_member_validator_reports_missing_human_gate_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/21-WorkCase-工作项.md",
        "2. 从 `human_plan_confirming` 进入 `executing`，即确认目标、范围、成功标准、执行颗粒度和约束；\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_HUMAN_GATE_BOUNDARY_MISSING" in _diagnostic_codes(result)
    assert any("human_plan_confirming" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_workcase_member_validator_reports_missing_legacy_status_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/21-WorkCase-工作项.md",
        "新增或重写 WorkCase 不得使用 V2 legacy 状态 `draft`、`active`、`review_needed`。历史材料出现这些状态时，只能作为迁移诊断输入，不能作为 V3 状态闭集。\n\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_LEGACY_STATUS_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_workcase_member_validator_reports_missing_field_contract_attachment(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    (root / "specs/attachments/21.Att.01-orchestration字段契约表.md").unlink()

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_FIELD_CONTRACT_MISSING" in _diagnostic_codes(result)


def test_workcase_member_validator_reports_missing_field_contract_tables(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    path = root / "specs/attachments/21.Att.01-orchestration字段契约表.md"
    raw = path.read_text(encoding="utf-8")
    raw = raw.replace(
        "| field_path | scope | meaning | format_kind | value_shape | ref_kind | enum_owner | schema_owner | code_check_kind | web_render_kind | status | replacement |",
        "| path | scope | meaning | format_kind | value_shape | ref_kind | enum_owner | schema_owner | code_check_kind | web_render_kind | status | replacement |",
    )
    raw = raw.replace("| 字段 | 必填口径 |", "| 字段名 | 必填口径 |")
    raw = raw.replace("| 状态 | 条件必填字段 | 说明 |", "| 状态名 | 条件必填字段 | 说明 |")
    path.write_text(raw, encoding="utf-8")

    result = ldvh_specs.build_validation(root)
    codes = _diagnostic_codes(result)

    assert "WORKCASE_FIELD_CONTRACT_TABLE_MISSING" in codes
    assert "WORKCASE_REQUIRED_FIELD_TABLE_MISSING" in codes
    assert "WORKCASE_STATUS_REQUIRED_TABLE_MISSING" in codes


def test_workcase_member_validator_reports_missing_field_contract_top_level_field(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/attachments/21.Att.01-orchestration字段契约表.md",
        "| `followup_refs` | WorkCase | 后续承接对象、文档或提交引用 | reference | list_string | mixed_ref | none | 21 | ref | mixed_ref | active | none |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_FIELD_CONTRACT_FIELD_MISSING" in _diagnostic_codes(result)
    assert any("followup_refs" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_workcase_member_validator_reports_missing_orchestration_contract_field(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/attachments/21.Att.01-orchestration字段契约表.md",
        "| `orchestration.result_review.human_closure_confirmation` | WorkCase.result_review | Human 对关闭判断、残留风险和后续分流的确认 | decision | object | none | none | 21 | owner_state | structured_area | active | none |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_ORCHESTRATION_CONTRACT_FIELD_MISSING" in _diagnostic_codes(result)
    assert any("orchestration.result_review.human_closure_confirmation" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_workcase_member_validator_reports_missing_status_required_row(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/attachments/21.Att.01-orchestration字段契约表.md",
        "| `subagents_result_reviewing` | `verification_evidence`; `orchestration.result_review.review_items` | 独立视角正在复查结果与关闭材料 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_STATUS_REQUIRED_ROW_MISSING" in _diagnostic_codes(result)
    assert any("subagents_result_reviewing" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_workcase_member_validator_reports_missing_status_required_field(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/attachments/21.Att.01-orchestration字段契约表.md",
        "`closed_at`; `closure_outcome`; `closure_evidence`; `orchestration.result_review.human_closure_confirmation`; `human_closure_confirmation`",
        "`closed_at`; `closure_outcome`; `closure_evidence`; `human_closure_confirmation`",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_STATUS_REQUIRED_FIELD_MISSING" in _diagnostic_codes(result)
    assert any("orchestration.result_review.human_closure_confirmation" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_fact_model_member_contracts_are_code_consumable(validation_result: dict) -> None:
    result = validation_result
    contracts = {contract["spec_id"]: contract for contract in result["fact_model_member_contracts"]}

    assert set(contracts) == {"20", "21", "22", "23", "24"}
    assert [row["status"] for row in contracts["20"]["statuses"]] == ["pending", "resolved", "discarded"]
    assert [row["status"] for row in contracts["21"]["statuses"]] == [
        "subagents_plan_reviewing",
        "human_plan_confirming",
        "executing",
        "result_self_checking",
        "subagents_result_reviewing",
        "human_closure_confirming",
        "closed",
    ]
    assert [row["status"] for row in contracts["22"]["statuses"]] == ["active", "archived", "deprecated"]
    assert [row["status"] for row in contracts["23"]["statuses"]] == ["active", "archived"]
    assert [row["status"] for row in contracts["24"]["statuses"]] == ["active", "archived"]

    assert contracts["20"]["instance_root"] == "ldvh-base/sparks/"
    assert contracts["22"]["instance_root"] == "ldvh-base/adrs/"
    assert contracts["23"]["instance_root"] == "ldvh-base/pitfalls/"
    assert contracts["24"]["instance_root"] == "ldvh-base/studies/"
    assert "spark_state_boundaries" in contracts["20"]["code_consumption"]
    assert "adr_decision_boundaries" in contracts["22"]["code_consumption"]
    assert "pitfall_evidence_boundaries" in contracts["23"]["code_consumption"]
    assert "study_markdown_body_boundaries" in contracts["24"]["code_consumption"]


def test_fact_instances_are_migrated_and_code_consumable(validation_result: dict) -> None:
    result = validation_result
    instances = result["fact_instances"]
    paths = {instance["path"] for instance in instances}

    assert result["summary"]["fact_instances"] == len(instances)
    assert {instance["kind"] for instance in instances} <= {"spark", "workcase", "adr", "pitfall", "study"}
    assert "ldvh-base/sparks/spark-0001-session-start-user-input-boundary.yaml" in paths
    assert "ldvh-base/sparks/spark-0002-subdocument-status-gap.yaml" in paths
    assert "ldvh-base/workcases/workcase-0002-knowledge-map-entry-navigation.yaml" in paths
    assert "ldvh-base/studies/study-0001-workcase-orchestration-evolution.md" in paths


def test_fact_instance_validator_reports_id_filename_mismatch(tmp_path: Path) -> None:
    root = _copy_specs_and_facts_root(tmp_path)
    _replace_in_temp(
        root,
        "ldvh-base/sparks/spark-0002-subdocument-status-gap.yaml",
        "id: spark-0002",
        "id: spark-9999",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_INSTANCE_ID_FILENAME_MISMATCH" in _diagnostic_codes(result)


def test_fact_instance_validator_reports_unknown_field(tmp_path: Path) -> None:
    root = _copy_specs_and_facts_root(tmp_path)
    path = root / "ldvh-base/sparks/spark-0002-subdocument-status-gap.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\nunknown_v2_field: true\n", encoding="utf-8")

    result = ldvh_specs.build_validation(root)

    assert "FACT_INSTANCE_FIELD_UNKNOWN" in _diagnostic_codes(result)


def test_fact_instance_validator_reports_missing_required_field(tmp_path: Path) -> None:
    root = _copy_specs_and_facts_root(tmp_path)
    _replace_in_temp(root, "ldvh-base/sparks/spark-0002-subdocument-status-gap.yaml", "priority: P1\n")

    result = ldvh_specs.build_validation(root)

    assert "FACT_INSTANCE_REQUIRED_FIELD_MISSING" in _diagnostic_codes(result)


def test_fact_instance_validator_reports_legacy_field(tmp_path: Path) -> None:
    root = _copy_specs_and_facts_root(tmp_path)
    path = root / "ldvh-base/pitfalls/pitfall-0001-workcase-closure-tail-routing.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\nseverity: high\n", encoding="utf-8")

    result = ldvh_specs.build_validation(root)

    assert "FACT_INSTANCE_LEGACY_FIELD_FORBIDDEN" in _diagnostic_codes(result)


def test_fact_instance_validator_reports_missing_related_object(tmp_path: Path) -> None:
    root = _copy_specs_and_facts_root(tmp_path)
    _replace_in_temp(
        root,
        "ldvh-base/pitfalls/pitfall-0001-workcase-closure-tail-routing.yaml",
        "spark-0032",
        "spark-9999",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_INSTANCE_REFERENCE_MISSING" in _diagnostic_codes(result)


def test_fact_instance_validator_reports_missing_study_body_heading(tmp_path: Path) -> None:
    root = _copy_specs_and_facts_root(tmp_path)
    _replace_in_temp(
        root,
        "ldvh-base/studies/study-0001-workcase-orchestration-evolution.md",
        "## 后续分流",
    )

    result = ldvh_specs.build_validation(root)

    assert "STUDY_BODY_HEADING_MISSING" in _diagnostic_codes(result)


def test_fact_member_validator_reports_missing_spark_state(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/20-Spark-火花.md",
        "| `resolved` | 已完整分流到 WorkCase、ADR、Pitfall、docs、管辖项目配置更新或其它非 Study 事实源，或已明确处理 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_MEMBER_STATUS_MISSING" in _diagnostic_codes(result)
    assert any("resolved" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_fact_member_validator_reports_missing_adr_legacy_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/22-ADR-决策.md",
        "新增或重写 ADR 不得使用 V2 legacy 状态 `proposed`、`accepted`、`rejected`、`superseded`，也不得使用旧字段 `superseded_by`、`alternatives` 或 `affects` 作为新写入字段。\n\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_MEMBER_LEGACY_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_fact_member_validator_reports_missing_pitfall_human_gate(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/23-Pitfall-踩坑经验.md",
        "6. 将未解决或未验证问题写成 `active` Pitfall；\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_MEMBER_HUMAN_GATE_BOUNDARY_MISSING" in _diagnostic_codes(result)
    assert any("未解决或未验证问题" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_fact_member_validator_reports_missing_study_markdown_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/24-Study-研究报告.md",
        "| `## 后续分流` |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_MEMBER_SPECIAL_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_fact_member_validator_reports_missing_study_source_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/24-Study-研究报告.md",
        "ldvh-base/studies/",
        "study-store/",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_MEMBER_SOURCE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_formal_identity_and_role_sections_are_parseable() -> None:
    objects = {obj.object_id: obj for obj in ldvh_specs.load_formal_objects(ROOT)}

    assert objects["01"].metadata["role_sections"]["rule_body"] == [
        "5. 内部保障",
        "6. 外部衔接",
        "7. 行动指南",
    ]
    assert "assurance_requirements" in objects["01"].metadata["code_consumption"]
    assert "ai_behavior_assurance_requirements" in objects["02"].metadata["code_consumption"]


def test_consumption_timing_registry_is_closed_set() -> None:
    timings = ldvh_specs.parse_consumption_timings(ROOT)

    assert [row["consumption_timing"] for row in timings] == [
        "session_start",
        "acknowledge_read_plan",
        "pre_tool_use",
        "git_commit_msg",
        "human_facing_output",
        "external_output_intake",
        "diagnostic_disposition",
        "completion_claim",
    ]


def test_ai_behavior_requirements_reference_allowed_timings(validation_result: dict) -> None:
    result = validation_result
    timing_set = {row["consumption_timing"] for row in result["consumption_timings"]}
    requirements = result["ai_behavior_requirements"]

    assert [row["requirement_id"] for row in requirements] == [
        "AI-BEH-001",
        "AI-BEH-002",
        "AI-BEH-003",
        "AI-BEH-004",
        "AI-BEH-005",
        "AI-BEH-006",
        "AI-BEH-007",
        "AI-BEH-008",
    ]
    assert {row["consumption_timing"] for row in requirements} == timing_set
    for row in requirements:
        assert row["required_capability"]
        assert row["completion_evidence"]
        assert row["blocking_conditions"]
        assert row["gap_disposition"]


def test_takeover_matrix_covers_ai_behavior_requirements(validation_result: dict) -> None:
    result = validation_result
    requirement_ids = {row["requirement_id"] for row in result["ai_behavior_requirements"]}
    matrix_ids = {row["requirement_id"] for row in result["takeover_matrix"]}

    assert matrix_ids == requirement_ids


def test_specs_validate_cli_json_all() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/specs_validate.py",
            "all",
            "--format",
            "json",
            "--fail-on-diagnostics",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["metadata"]["read_only"] is True
    assert payload["summary"]["status"] == "ok"
    assert payload["diagnostics"] == []


def test_specs_validate_cli_governed_projects_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/specs_validate.py",
            "governed-projects",
            "--target-path",
            "specs/10-安装与配置规范.md",
            "--format",
            "json",
            "--fail-on-diagnostics",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["metadata"]["read_only"] is True
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["governed"] is True
    assert payload["resolution"]["governed_project_id"] == "ldvh-v3"
    assert payload["resolution"]["governed_via"] == "path"


def test_specs_validate_cli_governed_projects_reports_config_hierarchy_conflict(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    project = root / "governed-app"
    project.mkdir()
    _write_governed_config(
        root,
        """
product_name: Test
product_description: Test workspace registry
projects:
  - id: app
    path: governed-app
""",
    )
    _write_governed_config(
        project,
        """
product_name: Test App
product_description: Test app local registry
projects:
  - id: app-local
    path: .
""",
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/specs_validate.py",
            "governed-projects",
            "--root",
            str(root),
            "--config-root",
            str(root),
            "--target-path",
            str(project / "README.md"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "blocked"
    assert payload["resolution"]["blocked_reason"] == "nested_governed_projects_config"
    assert "GOVERNED_PROJECT_CONFIG_HIERARCHY_CONFLICT" in _diagnostic_codes(payload)


def test_e2e_rehearsal_covers_static_workflow(e2e_rehearsal_result: dict) -> None:
    result = e2e_rehearsal_result

    assert result["metadata"]["read_only"] is True
    assert result["metadata"]["authorization"] == "none"
    assert result["metadata"]["environment_integrated"] is False
    assert result["summary"]["status"] == "ok"
    assert result["summary"]["governed"] is True
    assert result["summary"]["validation_status"] == "ok"
    assert result["summary"]["blocking"] == 0
    assert [stage["stage"] for stage in result["workflow"]] == [
        "governed_project_resolution",
        "session_start",
        "acknowledge_read_plan",
        "pre_tool_use",
        "validation",
        "git_commit_msg",
        "completion_claim",
    ]
    assert {stage["status"] for stage in result["workflow"]} == {"ok"}
    assert result["governed_project"]["governed_project_id"] == "ldvh-v3"
    assert result["preflight"]["summary"]["status"] == "diagnostic_clear"
    assert result["git_commit_msg"]["summary"]["status"] == "ok"
    assert result["completion_claim"]["summary"]["status"] == "ok"
    assert result["closure_assessment"]["static_rehearsal_complete"] is True
    assert result["closure_assessment"]["authorization"] == "none"
    assert any("Hook" in item for item in result["closure_assessment"]["postponed_boundaries"])


def test_e2e_rehearsal_output_has_no_authorization_terms(e2e_rehearsal_result: dict) -> None:
    result = e2e_rehearsal_result
    serialized = json.dumps(result, ensure_ascii=False)

    assert "approved" not in serialized
    assert "allowed" not in serialized
    assert "human_gate_passed" not in serialized


def test_specs_validate_cli_e2e_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/specs_validate.py",
            "e2e",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--format",
            "json",
            "--fail-on-diagnostics",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["metadata"]["read_only"] is True
    assert payload["summary"]["status"] == "ok"


def test_action_guide_session_start_read_plan() -> None:
    guide = ldvh_specs.build_action_guide(
        ROOT,
        consumption_timing="session_start",
        task="进入 LDVH v3 工作",
        trigger_source="manual",
    )

    assert guide["metadata"]["read_only"] is True
    assert guide["metadata"]["authorization"] == "none"
    assert guide["summary"]["status"] == "ok"
    assert guide["summary"]["consumption_timing"] == "session_start"
    assert guide["summary"]["requirements"] == 1
    assert guide["missing_fields"] == []
    read_paths = {item["path"] for item in guide["task_read_plan"] if item["path"]}
    assert {
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    }.issubset(read_paths)
    assert guide["stop_conditions"]
    assert guide["validation_guard"][0]["requirement_id"] == "AI-BEH-001"
    assert any(gap["requirement_id"] == "AI-BEH-001" for gap in guide["capability_gap"])


def test_action_guide_pre_tool_use_reports_missing_target(validation_result: dict) -> None:
    guide = ldvh_specs.build_action_guide(
        ROOT,
        consumption_timing="pre_tool_use",
        validation=validation_result,
    )

    assert guide["summary"]["status"] == "ok"
    assert "允许写入" not in guide["next_action"]
    assert guide["missing_fields"] == [
        {
            "field": "target_path",
            "reason": "写入或提交前需要明确 target/staged paths，当前输入未提供。",
        }
    ]
    assert "补齐 missing_fields" in guide["next_action"]
    assert any(item["requirement_id"] == "AI-BEH-003" for item in guide["stop_conditions"])


def test_action_guide_pre_tool_use_next_action_has_no_write_authorization(validation_result: dict) -> None:
    guide = ldvh_specs.build_action_guide(
        ROOT,
        consumption_timing="pre_tool_use",
        target_path="tests/code/test_ldvh_specs_validate.py",
        validation=validation_result,
    )

    assert guide["summary"]["status"] == "ok"
    assert "允许写入" not in guide["next_action"]
    assert "需交还 Human" in guide["next_action"]


def test_action_guide_unknown_timing_diagnostic(validation_result: dict) -> None:
    guide = ldvh_specs.build_action_guide(
        ROOT,
        consumption_timing="unknown_event",
        validation=validation_result,
    )

    assert guide["summary"]["status"] == "failed"
    assert guide["missing_fields"][0]["field"] == "consumption_timing"
    assert guide["diagnostics"][0]["code"] == "ACTION_GUIDE_TIMING_UNKNOWN"


def test_specs_validate_cli_action_guide_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/specs_validate.py",
            "action-guide",
            "--timing",
            "session_start",
            "--format",
            "json",
            "--fail-on-diagnostics",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["metadata"]["read_only"] is True
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["task_read_plan"] >= 3
    assert payload["source_refs"]


def test_preflight_core_spec_marks_human_gate_risk() -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="specs/01-保障与衔接.md",
        operation="write",
        task="修改保障规则",
    )

    assert preflight["metadata"]["read_only"] is True
    assert preflight["metadata"]["authorization"] == "none"
    assert preflight["summary"]["status"] == "review_required"
    assert preflight["summary"]["target_type"] == "core_spec"
    assert preflight["summary"]["human_gate_risks"] == 1
    assert any(item["path"] == "specs/01-保障与衔接.md" for item in preflight["required_read_plan"])


def test_preflight_code_target_is_unverifiable_not_authorization(validation_result: dict) -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="code/ldvh_specs.py",
        operation="write",
        validation=validation_result,
    )

    assert preflight["summary"]["target_type"] == "code"
    assert preflight["summary"]["status"] == "review_required"
    assert preflight["summary"]["unverifiable"] == 1
    assert preflight["diagnostics"][0]["code"] == "PREFLIGHT_CODE_OUTPUT_NOT_AUTHORIZATION"
    read_paths = {item["path"] for item in preflight["required_read_plan"]}
    assert {
        "specs/07-Code确定性执行规范.md",
        "specs/09-测试与验证规范.md",
    }.issubset(read_paths)


def test_preflight_attachment_keeps_boundary_warning(validation_result: dict) -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="specs/attachments/01.Att.01-保障消费时机表.md",
        operation="write",
        validation=validation_result,
    )

    assert preflight["summary"]["target_type"] == "attachment"
    assert preflight["summary"]["warnings"] == 1
    assert preflight["diagnostics"][0]["code"] == "PREFLIGHT_ATTACHMENT_BOUNDARY"


def test_preflight_known_tests_target_uses_diagnostic_clear_status(validation_result: dict) -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="tests/code/test_ldvh_specs_validate.py",
        operation="write",
        validation=validation_result,
    )

    assert preflight["summary"]["status"] == "diagnostic_clear"
    assert preflight["diagnostics"] == []
    read_paths = {item["path"] for item in preflight["required_read_plan"]}
    assert {
        "specs/07-Code确定性执行规范.md",
        "specs/09-测试与验证规范.md",
    }.issubset(read_paths)


def test_preflight_workcase_fact_instance_target_is_recognized(validation_result: dict) -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="ldvh-base/workcases/workcase-0024-v2-deletion-readiness-closure.yaml",
        operation="write",
        validation=validation_result,
    )

    assert preflight["summary"]["status"] == "diagnostic_clear"
    assert preflight["summary"]["target_type"] == "fact_instance"
    assert preflight["target"]["fact_kind"] == "workcase"
    assert preflight["target"]["member_spec"] == "specs/21-WorkCase-工作项.md"
    assert preflight["diagnostics"] == []
    read_paths = {item["path"] for item in preflight["required_read_plan"]}
    assert {
        "specs/05-事实模型基础规范.md",
        "specs/21-WorkCase-工作项.md",
        "ldvh-base/workcases/workcase-0024-v2-deletion-readiness-closure.yaml",
    }.issubset(read_paths)


def test_preflight_recognizes_common_ldvh_target_domains(validation_result: dict) -> None:
    cases = {
        "README.md": ("project_doc", "diagnostic_clear"),
        "docs/skills/readme.md": ("project_doc", "diagnostic_clear"),
        "LDVH-GOVERNED-PROJECTS.yaml": ("config", "review_required"),
        "package.json": ("config", "review_required"),
        "pyproject.toml": ("config", "review_required"),
        "web/api/app.ts": ("web", "diagnostic_clear"),
        "web/package.json": ("web", "diagnostic_clear"),
        "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py": ("hook", "review_required"),
        "hooks/environment-plugins/workbuddy-ldvh-v3/hooks/ldvh_runtime_shim.py": ("hook", "review_required"),
        "icons/ldvh-plugin-icon-128.png": ("asset", "diagnostic_clear"),
    }

    for target, (target_type, status) in cases.items():
        preflight = ldvh_specs.build_preflight(
            ROOT,
            target_path=target,
            operation="write",
            validation=validation_result,
        )
        codes = _diagnostic_codes(preflight)
        read_paths = {item["path"] for item in preflight["required_read_plan"]}

        assert preflight["summary"]["target_type"] == target_type, target
        assert preflight["summary"]["status"] == status, target
        assert "PREFLIGHT_TARGET_UNKNOWN" not in codes, target
        assert target in read_paths, target

    config_preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="LDVH-GOVERNED-PROJECTS.yaml",
        operation="write",
        validation=validation_result,
    )
    hook_preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py",
        operation="write",
        validation=validation_result,
    )
    assert "PREFLIGHT_CONFIG_BOUNDARY" in _diagnostic_codes(config_preflight)
    assert "PREFLIGHT_HOOK_ENTRY_BOUNDARY" in _diagnostic_codes(hook_preflight)


def test_preflight_acceptance_scratch_target_is_diagnostic_clear(validation_result: dict) -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path=".ldvh-runtime/acceptance-probe/allowed.txt",
        operation="write",
        validation=validation_result,
    )

    assert preflight["summary"]["status"] == "diagnostic_clear"
    assert preflight["summary"]["target_type"] == "acceptance_scratch"
    assert preflight["input"]["target_path"] == ".ldvh-runtime/acceptance-probe/allowed.txt"
    assert preflight["diagnostics"] == []
    read_paths = {item["path"] for item in preflight["required_read_plan"]}
    assert {
        "specs/30-安装配置与验证行动模板.md",
        "code/docs/02-Environment-Plugin-Practice.md",
    }.issubset(read_paths)


def test_preflight_other_hidden_runtime_target_still_blocks(validation_result: dict) -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path=".ldvh-runtime/other.txt",
        operation="write",
        validation=validation_result,
    )

    assert preflight["summary"]["status"] == "blocked"
    assert preflight["summary"]["target_type"] == "unknown"
    assert preflight["input"]["target_path"] == ".ldvh-runtime/other.txt"
    assert preflight["diagnostics"][0]["code"] == "PREFLIGHT_TARGET_UNKNOWN"


def test_preflight_unknown_target_blocks(validation_result: dict) -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="",
        operation="write",
        validation=validation_result,
    )

    assert preflight["summary"]["status"] == "blocked"
    assert preflight["summary"]["blocking"] == 1
    assert preflight["diagnostics"][0]["code"] == "PREFLIGHT_TARGET_UNKNOWN"


def test_preflight_external_nongoverned_target_is_silent_noop(tmp_path: Path, validation_result: dict) -> None:
    outside = tmp_path / "outside-project"
    outside.mkdir()

    preflight = ldvh_specs.build_preflight(
        ROOT,
        cwd=outside,
        target_path="notes.txt",
        operation="write",
        validation=validation_result,
    )

    assert preflight["summary"]["status"] == "no_op"
    assert preflight["summary"]["target_type"] == "non_governed"
    assert preflight["summary"]["blocking"] == 0
    assert preflight["required_read_plan"] == []
    assert preflight["validation_guard"] == []
    assert preflight["diagnostics"] == []
    assert preflight["governed_project"]["governed"] is False


def test_specs_validate_cli_preflight_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/specs_validate.py",
            "preflight",
            "--target-path",
            "code/ldvh_specs.py",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["metadata"]["read_only"] is True
    assert payload["metadata"]["authorization"] == "none"
    assert payload["summary"]["target_type"] == "code"
    assert payload["required_read_plan"]


def test_runtime_session_start_generates_stdout_receipt() -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="session_start",
        trigger_source="manual",
        session_id="test-session",
    )

    assert runtime["metadata"]["read_only"] is True
    assert runtime["metadata"]["environment_integrated"] is False
    assert runtime["metadata"]["authorization"] == "none"
    assert runtime["summary"]["status"] == "ok"
    assert runtime["receipt"]["persistent"] is False
    assert runtime["receipt"]["storage"] == "stdout_only"
    assert "不是事实源" in runtime["receipt"]["boundary"]
    read_paths = {item["path"] for item in runtime["action_guide"]["task_read_plan"] if item["path"]}
    assert {
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    }.issubset(read_paths)


def test_runtime_external_session_start_is_noop_without_read_plan(tmp_path: Path, validation_result: dict) -> None:
    outside = tmp_path / "outside-session"
    outside.mkdir()

    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="session_start",
        trigger_source="codex.ldvh-plugin",
        session_id="outside-session",
        cwd=outside,
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "no_op"
    assert runtime["summary"]["blocking"] == 0
    assert runtime["action_guide"] is None
    assert runtime["preflight"]["required_read_plan"] == []
    assert runtime["diagnostics"] == []


def test_session_start_cli_exports_hook_read_plan_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/session_start.py",
            "--session-id",
            "test-session-start",
            "--task",
            "进入 LDVH v3 工作",
            "--target-path",
            "README.md",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    read_paths = {item["path"] for item in payload["action_guide"]["task_read_plan"] if item["path"]}
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "ldvh.session_start"
    assert payload["summary"]["internal_event"] == "session_start"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["summary"]["integration_scope"] == "hook.session_start"
    assert payload["metadata"]["integration_scope"] == "hook.session_start"
    assert payload["receipt"]["storage"] == "stdout_only"
    assert payload["receipt"]["persistent"] is False
    assert {
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    }.issubset(read_paths)
    assert payload["diagnostics"] == []


def test_runtime_unknown_event_blocks(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="unknown_event",
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["summary"]["blocking"] == 1
    assert runtime["receipt"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_EVENT_UNKNOWN"


def test_runtime_acknowledge_read_plan_requires_paths(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="acknowledge_read_plan",
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_ACK_REQUIRED_PATHS_EMPTY"


def test_runtime_acknowledge_read_plan_accepts_entry_paths(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="acknowledge_read_plan",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "ok"
    assert runtime["receipt"]["acknowledged_paths"] == [
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    ]
    assert runtime["diagnostics"] == []


def test_acknowledge_read_plan_cli_accepts_entry_paths() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/acknowledge_read_plan.py",
            "--session-id",
            "test-ack",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--acknowledged-path",
            "specs/00-理念与构成.md",
            "--acknowledged-path",
            "specs/01-保障与衔接.md",
            "--acknowledged-path",
            "specs/02-AI行为规范.md",
            "--no-runtime-cache",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "ldvh.acknowledge_read_plan"
    assert payload["summary"]["internal_event"] == "acknowledge_read_plan"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["summary"]["integration_scope"] == "hook.acknowledge_read_plan"
    assert payload["metadata"]["integration_scope"] == "hook.acknowledge_read_plan"
    assert payload["receipt"]["storage"] == "stdout_only"
    assert payload["receipt"]["persistent"] is False
    assert payload["summary"]["runtime_cache"] == "disabled"
    assert payload["receipt"]["acknowledged_paths"] == [
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    ]
    assert payload["diagnostics"] == []


def test_acknowledge_read_plan_cli_blocks_missing_paths() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/acknowledge_read_plan.py",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--no-runtime-cache",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["integration_scope"] == "hook.acknowledge_read_plan"
    assert "RUNTIME_ACK_REQUIRED_PATHS_EMPTY" in _diagnostic_codes(payload)


def test_acknowledge_read_plan_cli_writes_runtime_cache(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "LDVH_RUNTIME_CACHE_DIR": (tmp_path / "receipt-cache").as_posix(),
    }
    completed = _run_cli(
        [
            sys.executable,
            "code/acknowledge_read_plan.py",
            "--session-id",
            "test-runtime-cache",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            *_ack_args(TEST_TARGET_ACK_PATHS),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        env=env,
    )

    payload = json.loads(completed.stdout)
    cache_path = Path(payload["runtime_cache"]["path"])
    assert payload["summary"]["runtime_cache"] == "written"
    assert cache_path.is_file()
    assert cache_path.is_relative_to(tmp_path)


def test_runtime_pre_tool_use_includes_preflight(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path="code/ldvh_specs.py",
        acknowledged_paths=CODE_TARGET_ACK_PATHS,
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "review_required"
    assert runtime["summary"]["has_preflight"] is True
    assert runtime["preflight"]["summary"]["target_type"] == "code"
    assert runtime["diagnostics"][0]["code"] == "PREFLIGHT_CODE_OUTPUT_NOT_AUTHORIZATION"


def test_runtime_pre_tool_use_blocks_without_read_plan_consumption(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path="tests/code/test_ldvh_specs_validate.py",
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_READ_PLAN_CONSUMED_EMPTY"


def test_runtime_pre_tool_use_workcase_target_without_ack_is_not_target_unknown(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path=WORKCASE_TARGET,
        validation=validation_result,
    )

    codes = _diagnostic_codes(runtime)
    assert runtime["summary"]["status"] == "blocked"
    assert runtime["preflight"]["summary"]["target_type"] == "fact_instance"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in codes
    assert "PREFLIGHT_TARGET_UNKNOWN" not in codes


def test_runtime_pre_tool_use_workcase_target_requires_target_read_plan(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path=WORKCASE_TARGET,
        acknowledged_paths=ENTRY_ACK_PATHS,
        validation=validation_result,
    )

    codes = _diagnostic_codes(runtime)
    assert runtime["summary"]["status"] == "blocked"
    assert runtime["preflight"]["summary"]["target_type"] == "fact_instance"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_READ_PLAN_CONSUMED_INCOMPLETE"
    assert "specs/21-WorkCase-工作项.md" in runtime["diagnostics"][0]["message"]
    assert WORKCASE_TARGET in runtime["diagnostics"][0]["message"]
    assert "PREFLIGHT_TARGET_UNKNOWN" not in codes


def test_runtime_external_pre_tool_use_noops_before_read_plan_ack(tmp_path: Path, validation_result: dict) -> None:
    outside = tmp_path / "outside-pretool"
    outside.mkdir()

    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path="notes.txt",
        cwd=outside,
        operation="write",
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "no_op"
    assert runtime["summary"]["blocking"] == 0
    assert runtime["action_guide"] is None
    assert runtime["preflight"]["summary"]["status"] == "no_op"
    assert runtime["preflight"]["required_read_plan"] == []
    assert runtime["diagnostics"] == []


def test_runtime_config_root_governed_target_does_not_noop_before_ack(tmp_path: Path, validation_result: dict) -> None:
    governance_root = tmp_path / "governance"
    project = tmp_path / "project"
    governance_root.mkdir()
    project.mkdir()
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {project}
""",
    )

    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path="README.md",
        cwd=project,
        config_root=governance_root,
        operation="write",
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["preflight"]["summary"]["status"] == "blocked"
    assert runtime["preflight"]["governed_project"]["governed"] is True
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_READ_PLAN_CONSUMED_EMPTY"


def test_runtime_config_root_unregistered_target_noops(tmp_path: Path, validation_result: dict) -> None:
    governance_root = tmp_path / "governance"
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    governance_root.mkdir()
    project.mkdir()
    outside.mkdir()
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {project}
""",
    )

    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path="notes.txt",
        cwd=outside,
        config_root=governance_root,
        operation="write",
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "no_op"
    assert runtime["preflight"]["governed_project"]["config_path_absolute"] == (governance_root / "LDVH-GOVERNED-PROJECTS.yaml").as_posix()
    assert runtime["diagnostics"] == []


def test_runtime_ldvh_root_unknown_target_still_blocks_with_external_config_root(tmp_path: Path, validation_result: dict) -> None:
    governance_root = tmp_path / "governance"
    outside = tmp_path / "outside"
    governance_root.mkdir()
    outside.mkdir()
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: external
    path: {outside}
""",
    )

    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path="tool-test.txt",
        cwd=ROOT,
        config_root=governance_root,
        operation="write",
        acknowledged_paths=ENTRY_ACK_PATHS,
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["preflight"]["summary"]["target_type"] == "unknown"
    assert "PREFLIGHT_TARGET_UNKNOWN" in _diagnostic_codes(runtime)


def test_pre_tool_use_cli_accepts_hook_preflight_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/pre_tool_use.py",
            "--session-id",
            "test-pre-tool-use",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--operation",
            "write",
            *_ack_args(TEST_TARGET_ACK_PATHS),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "ldvh.pre_tool_use"
    assert payload["summary"]["internal_event"] == "pre_tool_use"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["summary"]["integration_scope"] == "hook.pre_tool_use"
    assert payload["summary"]["preflight_status"] == "diagnostic_clear"
    assert payload["metadata"]["integration_scope"] == "hook.pre_tool_use"
    assert payload["receipt"]["storage"] == "stdout_only"
    assert payload["receipt"]["acknowledged_paths"] == TEST_TARGET_ACK_PATHS
    assert payload["preflight"]["summary"]["target_type"] == "tests"
    assert payload["diagnostics"] == []


def test_pre_tool_use_cli_blocks_missing_read_plan_consumption() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/pre_tool_use.py",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in _diagnostic_codes(payload)
    assert payload["summary"]["integration_scope"] == "hook.pre_tool_use"


def test_pre_tool_use_cli_consumes_runtime_cache(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "LDVH_RUNTIME_CACHE_DIR": (tmp_path / "receipt-cache").as_posix(),
    }
    _run_cli(
        [
            sys.executable,
            "code/acknowledge_read_plan.py",
            "--session-id",
            "test-pre-tool-cache",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            *_ack_args(TEST_TARGET_ACK_PATHS),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        env=env,
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/pre_tool_use.py",
            "--session-id",
            "test-pre-tool-cache",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        env=env,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["runtime_cache"] == "hit"
    assert payload["receipt"]["acknowledged_paths"] == TEST_TARGET_ACK_PATHS


def test_lifecycle_smoke_cli_checks_ldvh_canonical_same_chain(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "LDVH_RUNTIME_CACHE_DIR": (tmp_path / "receipt-cache").as_posix(),
    }
    completed = _run_cli(
        [
            sys.executable,
            "code/lifecycle_smoke.py",
            "--session-id",
            "test-lifecycle-smoke",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        env=env,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["summary"]["events"] == [
        "ldvh.session_start",
        "ldvh.acknowledge_read_plan",
        "ldvh.pre_tool_use",
        "ldvh.completion_claim",
    ]
    assert payload["runtime_cache"]["acknowledge_status"] == "written"
    assert payload["runtime_cache"]["pre_tool_use_status"] == "hit"
    assert payload["results"]["pre_tool_use"]["summary"]["event"] == "ldvh.pre_tool_use"
    assert payload["results"]["pre_tool_use"]["summary"]["internal_event"] == "pre_tool_use"
    assert payload["results"]["pre_tool_use"]["summary"]["runtime_cache"] == "hit"
    assert payload["diagnostics"] == []


def test_runtime_cache_refuses_repo_local_directory(monkeypatch) -> None:
    monkeypatch.setenv("LDVH_RUNTIME_CACHE_DIR", (ROOT / ".ldvh-runtime-cache-test").as_posix())

    result = runtime_receipt_cache.write_ack_receipt(
        ROOT,
        session_id="repo-local-cache",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
        trigger_source="test",
    )

    assert result.status == "blocked"
    assert "must not be inside the LDVH repo" in result.reason
    assert not (ROOT / ".ldvh-runtime-cache-test").exists()


def test_runtime_cache_handles_invalid_payload_without_crashing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LDVH_RUNTIME_CACHE_DIR", (tmp_path / "receipt-cache").as_posix())
    cache_dir = runtime_receipt_cache.runtime_cache_dir()
    cache_dir.mkdir(parents=True)
    path = runtime_receipt_cache.receipt_cache_path(ROOT, "bad-cache")
    path.write_text("[]\n", encoding="utf-8")

    result = runtime_receipt_cache.read_ack_receipt(ROOT, session_id="bad-cache")

    assert result.status in {"invalid", "miss"}
    assert not path.exists()


def test_runtime_cache_removes_structured_invalid_payload(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LDVH_RUNTIME_CACHE_DIR", (tmp_path / "receipt-cache").as_posix())
    write_result = runtime_receipt_cache.write_ack_receipt(
        ROOT,
        session_id="structured-invalid",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
        trigger_source="test",
    )
    path = Path(write_result.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = 999
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = runtime_receipt_cache.read_ack_receipt(ROOT, session_id="structured-invalid")

    assert result.status == "invalid"
    assert not path.exists()


def test_runtime_cache_rejects_session_mismatch(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LDVH_RUNTIME_CACHE_DIR", (tmp_path / "receipt-cache").as_posix())
    write_result = runtime_receipt_cache.write_ack_receipt(
        ROOT,
        session_id="session-a",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
        trigger_source="test",
    )

    read_result = runtime_receipt_cache.read_ack_receipt(ROOT, session_id="session-b")

    assert write_result.status == "written"
    assert read_result.status == "miss"


def test_runtime_cache_clamps_ttl(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LDVH_RUNTIME_CACHE_DIR", (tmp_path / "receipt-cache").as_posix())
    write_result = runtime_receipt_cache.write_ack_receipt(
        ROOT,
        session_id="expired-cache",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
        trigger_source="test",
        ttl_seconds=-1,
    )

    assert write_result.status == "written"
    payload = json.loads(Path(write_result.path).read_text(encoding="utf-8"))
    assert payload["expires_at"] > payload["created_at"]


def test_runtime_cache_clamps_large_ttl_to_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LDVH_RUNTIME_CACHE_DIR", (tmp_path / "receipt-cache").as_posix())
    write_result = runtime_receipt_cache.write_ack_receipt(
        ROOT,
        session_id="large-ttl-cache",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
        trigger_source="test",
        ttl_seconds=999999,
    )

    payload = json.loads(Path(write_result.path).read_text(encoding="utf-8"))
    created_at = datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00"))
    expires_at = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
    assert (expires_at - created_at).total_seconds() == runtime_receipt_cache.DEFAULT_TTL_SECONDS


def test_runtime_cache_rejects_expired_payload(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LDVH_RUNTIME_CACHE_DIR", (tmp_path / "receipt-cache").as_posix())
    write_result = runtime_receipt_cache.write_ack_receipt(
        ROOT,
        session_id="expired-cache",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
        trigger_source="test",
    )
    path = Path(write_result.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["expires_at"] = "2000-01-01T00:00:00Z"
    path.write_text(json.dumps(payload), encoding="utf-8")

    read_result = runtime_receipt_cache.read_ack_receipt(ROOT, session_id="expired-cache")

    assert read_result.status in {"expired", "miss"}
    assert not path.exists()


def test_runtime_cache_uses_private_posix_modes(tmp_path: Path, monkeypatch) -> None:
    if os.name == "nt":
        return
    monkeypatch.setenv("LDVH_RUNTIME_CACHE_DIR", (tmp_path / "receipt-cache").as_posix())
    write_result = runtime_receipt_cache.write_ack_receipt(
        ROOT,
        session_id="mode-cache",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
        trigger_source="test",
    )
    path = Path(write_result.path)

    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert path.stat().st_mode & 0o777 == 0o600


def test_pre_tool_use_cli_blocks_missing_target() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/pre_tool_use.py",
            "--acknowledged-path",
            "specs/00-理念与构成.md",
            "--acknowledged-path",
            "specs/01-保障与衔接.md",
            "--acknowledged-path",
            "specs/02-AI行为规范.md",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert "PREFLIGHT_TARGET_UNKNOWN" in _diagnostic_codes(payload)
    assert payload["preflight"]["summary"]["target_type"] == "unknown"


def test_pre_tool_use_cli_external_nongoverned_noops_without_ack(tmp_path: Path) -> None:
    outside = tmp_path / "outside-cli"
    outside.mkdir()

    completed = _run_cli(
        [
            sys.executable,
            "code/pre_tool_use.py",
            "--cwd",
            outside.as_posix(),
            "--target-path",
            "notes.txt",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["summary"]["status"] == "no_op"
    assert payload["summary"]["blocking"] == 0
    assert payload["summary"]["preflight_status"] == "no_op"
    assert payload["diagnostics"] == []


def test_pre_tool_use_cli_allows_acceptance_probe_scratch_target() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/pre_tool_use.py",
            "--target-path",
            ".ldvh-runtime/acceptance-probe/allowed.txt",
            *_ack_args(ACCEPTANCE_SCRATCH_ACK_PATHS),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["preflight_status"] == "diagnostic_clear"
    assert payload["receipt"]["target_path"] == ".ldvh-runtime/acceptance-probe/allowed.txt"
    assert payload["preflight"]["summary"]["target_type"] == "acceptance_scratch"
    assert payload["diagnostics"] == []


def test_pre_tool_use_cli_recognizes_workcase_fact_instance_target() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/pre_tool_use.py",
            "--target-path",
            WORKCASE_TARGET,
            *_ack_args(WORKCASE_ACK_PATHS),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["preflight_status"] == "diagnostic_clear"
    assert payload["preflight"]["summary"]["target_type"] == "fact_instance"
    assert payload["preflight"]["target"]["fact_kind"] == "workcase"
    assert "PREFLIGHT_TARGET_UNKNOWN" not in _diagnostic_codes(payload)
    assert payload["diagnostics"] == []


def test_runtime_git_commit_msg_blocks_incomplete_read_plan_consumption(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="git_commit_msg",
        target_path="tests/code/test_ldvh_specs_validate.py",
        acknowledged_paths=["specs/00-理念与构成.md"],
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_READ_PLAN_CONSUMED_INCOMPLETE"


def test_commit_gate_accepts_v2_commit_body_without_read_plan() -> None:
    message = """test(tests): 对齐当前测试回归范围

关键变更:
- 更新当前测试回归范围说明

验证结论:
- python3 -m pytest tests/code -q 通过
"""

    gate = ldvh_specs.build_commit_gate(
        ROOT,
        message=message,
        changed_paths=[
            "tests/code/test_ldvh_specs_validate.py",
            "tests/code/test_ldvh_test_runner.py",
        ],
    )

    assert gate["metadata"]["authorization"] == "none"
    assert gate["metadata"]["environment_integrated"] is False
    assert gate["metadata"]["hook_integrated"] is False
    assert gate["summary"]["status"] == "ok"
    assert gate["summary"]["body_required"] is True
    assert gate["summary"]["read_plan_required"] is False
    assert gate["summary"]["read_plan_consumed"] is True
    assert gate["body_required_reasons"] == ["高影响文件", "多文件范围"]
    assert gate["diagnostics"] == []


def test_commit_gate_does_not_use_message_body_as_read_plan_evidence() -> None:
    message = """feat(runtime): 接入最小提交 Hook

读取依据:
- specs/00-理念与构成.md
- `specs/01-保障与衔接.md`
- specs/02-AI行为规范.md

关键变更:
- 新增 worktree-local commit-msg hook 接入。
"""

    gate = ldvh_specs.build_commit_gate(
        ROOT,
        message=message,
        changed_paths=["hooks/commit-msg", "code/commit_validate.py"],
        require_read_plan=True,
    )

    assert gate["summary"]["status"] == "blocked"
    assert gate["summary"]["read_plan_required"] is True
    assert gate["summary"]["read_plan_consumed"] is False
    assert gate["acknowledged_paths"] == []
    assert gate["message_acknowledged_paths"] == []
    assert "COMMIT_READ_PLAN_CONSUMED_EMPTY" in _diagnostic_codes(gate)


def test_commit_gate_rejects_unknown_scope() -> None:
    gate = ldvh_specs.build_commit_gate(
        ROOT,
        message="docs(migration): 对齐历史迁移说明",
        changed_paths=["README.md"],
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
    )

    assert gate["summary"]["status"] == "blocked"
    assert "COMMIT_SCOPE_NOT_ALLOWED" in _diagnostic_codes(gate)


def test_commit_gate_requires_chinese_description() -> None:
    gate = ldvh_specs.build_commit_gate(
        ROOT,
        message="""docs(specs): clarify spec system consumption chain

关键变更:
- 澄清规范体系消费链路。
""",
        changed_paths=["specs/00-理念与构成.md"],
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
    )

    assert gate["summary"]["status"] == "blocked"
    assert "COMMIT_DESCRIPTION_NOT_CHINESE" in _diagnostic_codes(gate)


def test_commit_gate_requires_body_for_high_impact_changes() -> None:
    gate = ldvh_specs.build_commit_gate(
        ROOT,
        message="docs(specs): 调整事实源边界",
        changed_paths=["specs/03-事实源与Git溯源规范.md"],
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
    )

    assert gate["summary"]["status"] == "blocked"
    assert gate["body_required_reasons"] == ["高影响文件", "边界变化"]
    assert "COMMIT_BODY_REQUIRED" in _diagnostic_codes(gate)


def test_commit_gate_requires_read_plan_evidence() -> None:
    message = """test(tests): 增加提交校验测试

关键变更:
- 增加 commit gate 测试
"""

    gate = ldvh_specs.build_commit_gate(
        ROOT,
        message=message,
        changed_paths=["tests/code/test_ldvh_specs_validate.py"],
        require_read_plan=True,
    )

    assert gate["summary"]["status"] == "blocked"
    assert "COMMIT_READ_PLAN_CONSUMED_EMPTY" in _diagnostic_codes(gate)


def test_specs_validate_cli_commit_gate_json(tmp_path: Path) -> None:
    message_file = tmp_path / "message.txt"
    message_file.write_text(
        """test(tests): 增加提交校验测试

关键变更:
- 增加 commit gate CLI 测试
""",
        encoding="utf-8",
    )
    completed = _run_cli(
        [
            sys.executable,
            "code/specs_validate.py",
            "commit-gate",
            "--message-file",
            str(message_file),
            "--changed-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--format",
            "json",
            "--fail-on-diagnostics",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["read_plan_required"] is False
    assert payload["summary"]["environment_integrated"] is False
    assert payload["diagnostics"] == []


def test_commit_validate_wrapper_blocks_invalid_message(tmp_path: Path) -> None:
    message_file = tmp_path / "message.txt"
    message_file.write_text("docs(migration): 无效 scope\n", encoding="utf-8")

    completed = _run_cli(
        [
            sys.executable,
            "code/commit_validate.py",
            "--check-message-file",
            str(message_file),
            "--repo",
            str(ROOT),
            "--changed-path",
            "README.md",
            "--acknowledged-path",
            "specs/00-理念与构成.md",
            "--acknowledged-path",
            "specs/01-保障与衔接.md",
            "--acknowledged-path",
            "specs/02-AI行为规范.md",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "blocked"
    assert "COMMIT_SCOPE_NOT_ALLOWED" in _diagnostic_codes(payload)


def test_commit_validate_wrapper_marks_hook_integration(tmp_path: Path) -> None:
    message_file = tmp_path / "message.txt"
    message_file.write_text(
        """feat(runtime): 接入最小提交 Hook

关键变更:
- 接入 worktree-local commit-msg hook。
""",
        encoding="utf-8",
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/commit_validate.py",
            "--check-message-file",
            str(message_file),
            "--repo",
            str(ROOT),
            "--changed-path",
            "hooks/commit-msg",
            "--changed-path",
            "code/commit_validate.py",
            "--hook-integrated",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["metadata"]["hook_integrated"] is True
    assert payload["metadata"]["environment_integrated"] is True
    assert payload["metadata"]["integration_scope"] == "git.commit-msg"


def test_install_git_hooks_uses_git_local_hooks_path_for_external_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)

    completed = _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--backend-allow-external",
        ],
        cwd=ROOT,
        check=True,
    )

    hook = repo / ".git" / "ldvh-hooks" / "commit-msg"
    config = subprocess.run(
        ["git", "config", "--show-origin", "--get", "core.hooksPath"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )

    assert "- installed: True" in completed.stdout
    assert "config.worktree" in config.stdout
    assert config.stdout.rstrip().endswith(f"\t{repo / '.git' / 'ldvh-hooks'}")
    assert hook.is_file()
    assert os.access(hook, os.X_OK)
    assert "# LDVH v3 managed commit-msg hook" in hook.read_text(encoding="utf-8")
    assert not (repo / "hooks" / "commit-msg").exists()
    assert not (repo / ".git" / "hooks" / "commit-msg").exists()


def test_install_git_hooks_uses_common_dir_for_external_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    worktree = tmp_path / "repo-worktree"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "ldvh@example.test"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "LDVH Test"], cwd=repo, check=True, timeout=30)
    (repo / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "test: init"], cwd=repo, check=True, capture_output=True, text=True, timeout=30)
    subprocess.run(["git", "worktree", "add", "--detach", str(worktree), "HEAD"], cwd=repo, check=True, capture_output=True, text=True, timeout=30)

    completed = _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(worktree),
            "--backend-allow-external",
        ],
        cwd=ROOT,
        check=True,
    )
    common_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=worktree,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout.strip()
    config = subprocess.run(
        ["git", "config", "--show-origin", "--get", "core.hooksPath"],
        cwd=worktree,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    hook = Path(common_dir) / "ldvh-hooks" / "commit-msg"

    assert "- installed: True" in completed.stdout
    assert "config.worktree" in config.stdout
    assert config.stdout.rstrip().endswith(f"\t{Path(common_dir) / 'ldvh-hooks'}")
    assert hook.is_file()
    assert os.access(hook, os.X_OK)
    assert "# LDVH v3 managed commit-msg hook" in hook.read_text(encoding="utf-8")
    assert not (worktree / "ldvh-hooks" / "commit-msg").exists()
    assert not (worktree / "hooks" / "commit-msg").exists()


def test_install_git_hooks_blocks_direct_external_repo_write(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)

    completed = _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
        ],
        cwd=ROOT,
        check=False,
    )

    assert completed.returncode == 1
    assert "governed_hook_adapter.py" in completed.stdout
    assert "confirm-human-gate" in completed.stdout
    assert not (repo / "hooks" / "commit-msg").exists()


def test_governed_hook_adapter_installs_for_confirmed_governed_repo(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "ldvh@example.test"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "LDVH Test"], cwd=repo, check=True, timeout=30)
    (repo / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "test: init"], cwd=repo, check=True, capture_output=True, text=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "install",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--confirm-human-gate",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["governed"] is True
    assert payload["summary"]["governed_project_id"] == "app"
    assert payload["summary"]["hook_integrated"] == "git.commit-msg"
    assert payload["metadata"]["human_gate_confirmed"] is True
    hook = Path(payload["hook_status"]["active_hook"])
    assert hook == repo / ".git" / "ldvh-hooks" / "commit-msg"
    assert hook.is_file()
    assert os.access(hook, os.X_OK)
    assert not (repo / "hooks" / "commit-msg").exists()
    hook_text = hook.read_text(encoding="utf-8")
    assert "# LDVH v3 managed commit-msg hook" in hook_text
    assert ROOT.as_posix() in hook_text
    assert '--ldvh-root "$LDVH_ROOT"' in hook_text

    (repo / "README.md").write_text("# app\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, timeout=30)
    valid_message = tmp_path / "valid-message.txt"
    valid_message.write_text("docs(docs): 验证外部hook\n", encoding="utf-8")
    valid_run = subprocess.run(
        [str(hook), str(valid_message)],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert valid_run.returncode == 0, valid_run.stdout + valid_run.stderr
    assert "FileNotFoundError" not in valid_run.stdout + valid_run.stderr

    invalid_message = tmp_path / "invalid-message.txt"
    invalid_message.write_text("invalid header\n", encoding="utf-8")
    invalid_run = subprocess.run(
        [str(hook), str(invalid_message)],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert invalid_run.returncode == 1
    assert "COMMIT_HEADER_INVALID" in invalid_run.stdout
    assert "FileNotFoundError" not in invalid_run.stdout + invalid_run.stderr

    rollback = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "uninstall",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--confirm-human-gate",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )
    rollback_payload = json.loads(rollback.stdout)
    hooks_path = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert rollback_payload["summary"]["status"] == "ok"
    assert rollback_payload["summary"]["hook_integrated"] == "none"
    assert hooks_path.returncode != 0
    assert not hook.exists()
    assert not hook.parent.exists()
    assert not (repo / "hooks").exists()


def test_governed_hook_adapter_verifies_installed_governed_repo(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "install",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--confirm-human-gate",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )
    (repo / "code").mkdir()
    (repo / "code" / "example.py").write_text("print('changed')\n", encoding="utf-8")
    subprocess.run(["git", "add", "code/example.py"], cwd=repo, check=True, timeout=30)
    before_status = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout

    completed = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "verify",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    after_status = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    payload = json.loads(completed.stdout)
    verification = payload["verification"]
    assert payload["summary"]["status"] == "ok"
    assert payload["metadata"]["authorization"] == "none"
    assert payload["summary"]["hook_integrated"] == "git.commit-msg"
    assert verification["status"] == "ok"
    assert verification["positive_case"]["passed"] is True
    assert verification["positive_case"]["exit_code"] == 0
    assert verification["negative_case"]["passed"] is True
    assert verification["negative_case"]["exit_code"] == 1
    assert verification["negative_case"]["blocking_code_found"] is True
    assert "governed_hook_adapter.py uninstall" in verification["rollback_command"]
    assert after_status == before_status


def test_governed_hook_adapter_verifies_all_configured_projects(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    governance_root.mkdir()
    repo_a.mkdir()
    repo_b.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo_a, check=True, timeout=30)
    subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app-a
    path: {repo_a}
  - id: app-b
    path: {repo_b}
""",
    )
    for repo in [repo_a, repo_b]:
        _run_cli(
            [
                sys.executable,
                "code/governed_hook_adapter.py",
                "install",
                "--repo",
                str(repo),
                "--governance-root",
                str(governance_root),
                "--ldvh-root",
                str(ROOT),
                "--confirm-human-gate",
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=True,
        )

    completed = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "verify",
            "--all-projects",
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["projects"] == 2
    assert payload["summary"]["verified"] == 2
    assert {project["summary"]["governed_project_id"] for project in payload["projects"]} == {"app-a", "app-b"}
    assert all(project["verification"]["positive_case"]["passed"] for project in payload["projects"])
    assert all(project["verification"]["negative_case"]["passed"] for project in payload["projects"])


def test_governed_hook_adapter_verify_blocks_missing_hook(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "verify",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["verification"]["status"] == "blocked"
    assert "GOVERNED_HOOK_VERIFY_NOT_INSTALLED" in _diagnostic_codes(payload)


def test_governed_hook_adapter_install_backs_up_existing_non_managed_hook(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    hook_dir = repo / ".git" / "ldvh-hooks"
    hook_dir.mkdir(parents=True)
    hook = hook_dir / "commit-msg"
    hook.write_text("#!/bin/sh\necho custom hook\n", encoding="utf-8")
    hook.chmod(0o755)
    subprocess.run(["git", "config", "extensions.worktreeConfig", "true"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "--worktree", "core.hooksPath", str(hook_dir)], cwd=repo, check=True, timeout=30)

    completed = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "install",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--confirm-human-gate",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    backups = list(hook_dir.glob("commit-msg.ldvh-backup-*"))
    assert payload["summary"]["status"] == "ok"
    assert "# LDVH v3 managed commit-msg hook" in hook.read_text(encoding="utf-8")
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "#!/bin/sh\necho custom hook\n"


def test_governed_hook_adapter_uninstall_preserves_non_managed_active_hook(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    hook_dir = repo / ".git" / "custom-hooks"
    hook_dir.mkdir(parents=True)
    hook = hook_dir / "commit-msg"
    hook.write_text("#!/bin/sh\necho custom hook\n", encoding="utf-8")
    hook.chmod(0o755)
    subprocess.run(["git", "config", "extensions.worktreeConfig", "true"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "--worktree", "core.hooksPath", str(hook_dir)], cwd=repo, check=True, timeout=30)

    completed = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "uninstall",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--confirm-human-gate",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    hooks_path = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["hook_integrated"] == "none"
    assert hooks_path.stdout.strip() == str(hook_dir)
    assert hook.read_text(encoding="utf-8") == "#!/bin/sh\necho custom hook\n"


def test_governed_hook_adapter_requires_human_gate_for_install(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "install",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["hook_integrated"] == "none"
    assert "GOVERNED_HOOK_HUMAN_GATE_REQUIRED" in _diagnostic_codes(payload)
    assert not (repo / "hooks" / "commit-msg").exists()


def test_governed_hook_adapter_blocks_non_git_governed_project_install(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    repo.mkdir()
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "install",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--confirm-human-gate",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["governed"] is True
    assert payload["summary"]["hook_integrated"] == "none"
    assert "GOVERNED_HOOK_TARGET_NOT_GIT_REPO" in _diagnostic_codes(payload)
    assert "管辖项目必须是 Git 仓库" in payload["diagnostics"][0]["message"]
    assert payload["hook_status"]["installed"] is False
    assert not (repo / ".git").exists()


def test_governed_hook_adapter_blocks_ungoverned_repo_install(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    other = tmp_path / "other"
    governance_root.mkdir()
    repo.mkdir()
    other.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: other
    path: {other}
""",
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/governed_hook_adapter.py",
            "install",
            "--repo",
            str(repo),
            "--governance-root",
            str(governance_root),
            "--ldvh-root",
            str(ROOT),
            "--confirm-human-gate",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["governed"] is False
    assert "GOVERNED_HOOK_TARGET_NOT_GOVERNED" in _diagnostic_codes(payload)
    assert not (repo / "hooks" / "commit-msg").exists()


def test_environment_status_reports_commit_hook_without_manual_entries(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--backend-allow-external",
            "--ldvh-root",
            str(ROOT),
        ],
        cwd=ROOT,
        check=True,
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/environment_status.py",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    entrypoints = {entry["id"]: entry for entry in payload["entrypoints"]}
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["environment_integrated"] == "partial"
    assert payload["summary"]["hook_integrated"] == "git.commit-msg"
    assert payload["summary"]["automated_entrypoints"] == ["git.commit-msg"]
    assert entrypoints["git.commit-msg"]["integrated"] is True
    assert set(entrypoints) == {"git.commit-msg"}
    assert payload["metadata"]["authorization"] == "none"
    assert payload["diagnostics"] == []


def test_environment_status_blocks_missing_commit_hook(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)

    completed = _run_cli(
        [
            sys.executable,
            "code/environment_status.py",
            "--repo",
            str(repo),
            "--backend-allow-external",
            "--ldvh-root",
            str(ROOT),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["environment_integrated"] == "false"
    assert payload["summary"]["hook_integrated"] == "none"
    assert payload["summary"]["automated_entrypoints"] == []
    assert "ENV_COMMIT_MSG_HOOK_NOT_INSTALLED" in _diagnostic_codes(payload)


def test_environment_entry_audit_marks_rules_and_skills_removed_top_level(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    (repo / "rules").mkdir()
    (repo / "rules" / ".gitkeep").write_text("", encoding="utf-8")
    (repo / "skills").mkdir()
    (repo / "skills" / ".gitkeep").write_text("", encoding="utf-8")
    _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--backend-allow-external",
            "--ldvh-root",
            str(ROOT),
        ],
        cwd=ROOT,
        check=True,
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/environment_entry_audit.py",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
            "--codex-home",
            str(codex_home),
            "--environment-name",
            "Codex",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["integrated_entrypoints"] == ["git.commit-msg"]
    assert payload["summary"]["rules_entry_integrated"] is False
    assert payload["summary"]["skill_entry_integrated"] is False
    assert payload["summary"]["tool_hook_integrated"] is False
    assert payload["summary"]["completion_hook_integrated"] is False
    assert payload["summary"]["codex_plugin_entry_integrated"] is False
    assert payload["summary"]["codex_environment_entry_integrated"] is False
    assert "rules.top_level_mechanism" in payload["summary"]["removed_top_level_entrypoints"]
    assert "skills.top_level_mechanism" in payload["summary"]["removed_top_level_entrypoints"]
    assert candidates["git.commit-msg"]["status"] == "integrated"
    assert candidates["runtime.pre_tool_use.auto"]["status"] == "deferred"
    assert candidates["runtime.pre_tool_use.auto"]["hook_entry"] == "code/runtime_adapter.py"
    assert candidates["codex.ldvh-plugin"]["status"] == "absent"
    assert candidates["codex.ldvh-plugin"]["decision"] == "install_plugin_before_claiming"
    assert candidates["rules.top_level_mechanism"]["status"] == "removed_top_level"
    assert candidates["rules.top_level_mechanism"]["decision"] == "removed_top_level"
    assert candidates["skills.top_level_mechanism"]["status"] == "removed_top_level"
    assert candidates["skills.top_level_mechanism"]["decision"] == "removed_top_level"
    assert payload["decision"]["next_step"] == "install_or_upgrade_ldvh_environment_plugin_before_auto_runtime_claim"
    assert payload["diagnostics"] == []


def test_environment_entry_audit_does_not_treat_agent_file_as_integration(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    (repo / "AGENTS.md").write_text("# Repo instructions\n", encoding="utf-8")
    _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--backend-allow-external",
            "--ldvh-root",
            str(ROOT),
        ],
        cwd=ROOT,
        check=True,
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/environment_entry_audit.py",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
            "--codex-home",
            str(codex_home),
            "--environment-name",
            "Codex",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}
    assert payload["summary"]["integrated_entrypoints"] == ["git.commit-msg"]
    assert "codex.repo-instructions" not in candidates
    assert candidates["codex.ldvh-plugin"]["status"] == "absent"
    assert candidates["rules.top_level_mechanism"]["status"] == "removed_top_level"
    assert candidates["skills.top_level_mechanism"]["status"] == "removed_top_level"
    assert payload["summary"]["codex_environment_entry_integrated"] is False
    assert "ENV_CODEX_ENTRY_FILES_NOT_INTEGRATED" not in _diagnostic_codes(payload)


def test_environment_entry_audit_scopes_plugin_candidate_to_target_environment(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    (codex_home / "config.toml").write_text(
        """
[plugins."ldvh@personal"]
enabled = true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--backend-allow-external",
            "--ldvh-root",
            str(ROOT),
        ],
        cwd=ROOT,
        check=True,
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/environment_entry_audit.py",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
            "--codex-home",
            str(codex_home),
            "--environment-name",
            "WorkBuddy",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}
    assert payload["metadata"]["environment_name"] == "WorkBuddy"
    assert "codex_home" not in payload["metadata"]
    assert "codex.ldvh-plugin" not in candidates
    assert candidates["workbuddy.ldvh-plugin"]["status"] == "absent"
    assert candidates["workbuddy.ldvh-plugin"]["decision"] == "create_target_environment_plugin_before_claiming"
    assert candidates["runtime.pre_tool_use.auto"]["trigger"] == "WorkBuddy tool-call-before-write lifecycle hook"
    assert payload["summary"]["absent_entrypoints"] == ["workbuddy.ldvh-plugin"]
    assert payload["summary"]["target_environment_plugin_entry_integrated"] is False
    assert "codex_plugin_entry_integrated" not in payload["summary"]
    assert "codex_environment_entry_integrated" not in payload["summary"]
    assert "Codex" not in json.dumps(payload["candidates"], ensure_ascii=False)


def test_environment_entry_audit_reports_stale_ldvh_codex_plugin(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    hook_dir = codex_home / "plugins" / "cache" / "personal" / "ldvh" / "0.1.0" / "hooks"
    repo.mkdir()
    hook_dir.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    (codex_home / "config.toml").write_text(
        """
[plugins."ldvh@personal"]
enabled = true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (hook_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup|resume",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python3 /Users/example/poker_hud_projects/ld-vibe-harness/code/hook_adapter.py session-start",
                                }
                            ],
                        }
                    ],
                    "PreToolUse": [
                        {
                            "matcher": "Bash|Edit|Write",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python3 /Users/example/poker_hud_projects/ld-vibe-harness/code/hook_adapter.py pre-tool-use",
                                }
                            ],
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--backend-allow-external",
            "--ldvh-root",
            str(ROOT),
        ],
        cwd=ROOT,
        check=True,
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/environment_entry_audit.py",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
            "--codex-home",
            str(codex_home),
            "--environment-name",
            "Codex",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}
    assert payload["summary"]["integrated_entrypoints"] == ["git.commit-msg"]
    assert "codex.ldvh-plugin" in payload["summary"]["available_unintegrated_entrypoints"]
    assert payload["summary"]["codex_plugin_entry_integrated"] is False
    assert candidates["codex.ldvh-plugin"]["status"] == "available"
    assert candidates["codex.ldvh-plugin"]["decision"] == "reinstall_for_v3"
    assert candidates["codex.ldvh-plugin"]["details"]["stale_commands"]
    assert candidates["runtime.session_start.auto"]["status"] == "deferred"
    assert "LDVH 插件" in candidates["runtime.session_start.auto"]["reason"]
    assert "ENV_CODEX_LDVH_PLUGIN_STALE" in _diagnostic_codes(payload)


def test_environment_entry_audit_reports_stale_repo_environment_plugin_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    hook_dir = codex_home / "plugins" / "cache" / "personal" / "ldvh" / "0.1.0" / "hooks"
    repo.mkdir()
    hook_dir.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    (codex_home / "config.toml").write_text(
        """
[plugins."ldvh@personal"]
enabled = true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    stale_shim = ROOT / "code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"
    (hook_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup|resume",
                            "hooks": [{"type": "command", "command": f"{sys.executable} {stale_shim}"}],
                        }
                    ]
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--backend-allow-external",
            "--ldvh-root",
            str(ROOT),
        ],
        cwd=ROOT,
        check=True,
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/environment_entry_audit.py",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
            "--codex-home",
            str(codex_home),
            "--environment-name",
            "Codex",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}
    assert candidates["codex.ldvh-plugin"]["status"] == "available"
    assert candidates["codex.ldvh-plugin"]["decision"] == "reinstall_for_v3"
    assert candidates["codex.ldvh-plugin"]["details"]["stale_asset_commands"] == [
        f"{sys.executable} {stale_shim}"
    ]
    assert "ENV_CODEX_LDVH_PLUGIN_STALE" in _diagnostic_codes(payload)


def test_environment_entry_audit_recognizes_v3_codex_shim_without_integration(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    hook_dir = codex_home / "plugins" / "cache" / "personal" / "ldvh" / "0.1.0" / "hooks"
    repo.mkdir()
    hook_dir.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    (codex_home / "config.toml").write_text(
        """
[plugins."ldvh@personal"]
enabled = true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    v3_shim = ROOT / "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"
    (hook_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup|resume",
                            "hooks": [{"type": "command", "command": f"{sys.executable} {v3_shim}"}],
                        }
                    ],
                    "PreToolUse": [
                        {
                            "matcher": "Write|Edit|apply_patch",
                            "hooks": [{"type": "command", "command": f"{sys.executable} {v3_shim}"}],
                        }
                    ],
                    "Stop": [
                        {
                            "matcher": "*",
                            "hooks": [{"type": "command", "command": f"{sys.executable} {v3_shim}"}],
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _run_cli(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--backend-allow-external",
            "--ldvh-root",
            str(ROOT),
        ],
        cwd=ROOT,
        check=True,
    )

    completed = _run_cli(
        [
            sys.executable,
            "code/environment_entry_audit.py",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
            "--codex-home",
            str(codex_home),
            "--environment-name",
            "Codex",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}
    assert "ENV_CODEX_LDVH_PLUGIN_STALE" not in _diagnostic_codes(payload)
    assert candidates["codex.ldvh-plugin"]["status"] == "available"
    assert candidates["codex.ldvh-plugin"]["integrated"] is False
    assert candidates["codex.ldvh-plugin"]["decision"] == "verify_trust_and_runtime_before_integration"
    assert candidates["codex.ldvh-plugin"]["details"]["required_events_ok"] is True
    assert str(v3_shim) in "\n".join(candidates["codex.ldvh-plugin"]["details"]["commands"])


def test_runtime_completion_claim_requires_verification_evidence(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="completion_claim",
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_COMPLETION_VERIFICATION_MISSING"


def test_completion_claim_cli_accepts_hook_evidence_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/completion_claim.py",
            "--session-id",
            "test-completion-claim",
            "--target-path",
            "README.md",
            "--task",
            "完成 10D",
            "--acknowledged-path",
            "specs/00-理念与构成.md",
            "--verification-evidence",
            "python3 code/specs_validate.py all --format text --fail-on-diagnostics",
            "--verification-evidence",
            "python3 -m pytest tests/code/test_formal_specs.py -q",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "ldvh.completion_claim"
    assert payload["summary"]["internal_event"] == "completion_claim"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["summary"]["integration_scope"] == "hook.completion_claim"
    assert payload["summary"]["verification_evidence"] == 2
    assert payload["metadata"]["integration_scope"] == "hook.completion_claim"
    assert payload["metadata"]["authorization"] == "none"
    assert payload["receipt"]["storage"] == "stdout_only"
    assert payload["receipt"]["verification_evidence"] == [
        "python3 code/specs_validate.py all --format text --fail-on-diagnostics",
        "python3 -m pytest tests/code/test_formal_specs.py -q",
    ]
    assert payload["diagnostics"] == []


def test_completion_claim_cli_blocks_missing_verification_evidence() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/completion_claim.py",
            "--target-path",
            "README.md",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["integration_scope"] == "hook.completion_claim"
    assert payload["receipt"]["storage"] == "stdout_only"
    assert "RUNTIME_COMPLETION_VERIFICATION_MISSING" in _diagnostic_codes(payload)


def test_runtime_adapter_dispatches_session_start_payload_json() -> None:
    adapter_payload = {
        "event": "session_start",
        "session_id": "test-runtime-adapter",
        "target_path": "README.md",
        "operation": "read",
        "task": "进入 LDVH v3 工作",
        "acknowledged_paths": [],
        "verification_evidence": [],
    }

    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "--payload-json",
            json.dumps(adapter_payload, ensure_ascii=False),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    read_paths = {item["path"] for item in payload["dispatch"]["action_guide"]["task_read_plan"] if item["path"]}
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "ldvh.session_start"
    assert payload["summary"]["internal_event"] == "session_start"
    assert payload["summary"]["adapter_integrated"] is False
    assert payload["metadata"]["integration_scope"] == "hook.runtime_adapter"
    assert payload["dispatch"]["summary"]["integration_scope"] == "hook.session_start"
    assert {
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    }.issubset(read_paths)


def test_runtime_adapter_text_output_prints_internal_event() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "session-start",
            "--cwd",
            str(ROOT),
            "--target-path",
            "README.md",
            "--operation",
            "read",
            "--format",
            "text",
        ],
        cwd=ROOT,
        check=True,
    )

    assert "- event: ldvh.session_start" in completed.stdout
    assert "- internal_event: session_start" in completed.stdout


def test_runtime_adapter_dispatches_pre_tool_use_cli_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "pre-tool-use",
            "--cwd",
            str(ROOT),
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            *_ack_args(TEST_TARGET_ACK_PATHS),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "ldvh.pre_tool_use"
    assert payload["summary"]["internal_event"] == "pre_tool_use"
    assert payload["dispatch"]["summary"]["integration_scope"] == "hook.pre_tool_use"
    assert payload["dispatch"]["preflight"]["summary"]["target_type"] == "tests"
    assert payload["diagnostics"] == []


def test_runtime_adapter_external_pre_tool_payload_noops_without_ack(tmp_path: Path) -> None:
    outside = tmp_path / "adapter-outside"
    outside.mkdir()
    adapter_payload = {
        "event": "pre_tool_use",
        "session_id": "test-runtime-adapter-noop",
        "cwd": outside.as_posix(),
        "target_path": "notes.txt",
        "target_paths": ["notes.txt"],
        "operation": "write",
        "task": "外部项目写入",
        "acknowledged_paths": [],
        "verification_evidence": [],
    }

    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "--payload-json",
            json.dumps(adapter_payload, ensure_ascii=False),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "no_op"
    assert payload["summary"]["blocking"] == 0
    assert payload["dispatch"]["summary"]["status"] == "no_op"
    assert payload["dispatch"]["diagnostics"] == []
    assert payload["diagnostics"] == []


def test_runtime_adapter_external_relative_target_requires_cwd() -> None:
    adapter_payload = {
        "event": "pre_tool_use",
        "session_id": "test-runtime-adapter-missing-cwd",
        "target_path": "notes.txt",
        "operation": "write",
        "task": "外部项目写入",
        "acknowledged_paths": [],
        "verification_evidence": [],
        "trigger_source": "codex.ldvh-plugin",
    }

    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "--payload-json",
            json.dumps(adapter_payload, ensure_ascii=False),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert "RUNTIME_ADAPTER_CWD_REQUIRED_FOR_RELATIVE_TARGET" in _diagnostic_codes(payload)


def test_runtime_adapter_external_empty_cwd_or_target_paths_only_requires_cwd() -> None:
    payloads = [
        {
            "event": "pre_tool_use",
            "session_id": "test-runtime-adapter-empty-cwd",
            "cwd": "",
            "target_path": "notes.txt",
            "operation": "write",
            "task": "外部项目写入",
            "acknowledged_paths": [],
            "verification_evidence": [],
            "trigger_source": "codex.ldvh-plugin",
        },
        {
            "event": "pre_tool_use",
            "session_id": "test-runtime-adapter-target-paths-only",
            "target_path": "",
            "target_paths": ["notes.txt"],
            "operation": "write",
            "task": "外部项目写入",
            "acknowledged_paths": [],
            "verification_evidence": [],
            "trigger_source": "codex.ldvh-plugin",
        },
    ]

    for adapter_payload in payloads:
        completed = _run_cli(
            [
                sys.executable,
                "code/runtime_adapter.py",
                "--payload-json",
                json.dumps(adapter_payload, ensure_ascii=False),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
        )

        payload = json.loads(completed.stdout)
        assert completed.returncode == 1
        assert payload["summary"]["status"] == "blocked"
        assert "RUNTIME_ADAPTER_CWD_REQUIRED_FOR_RELATIVE_TARGET" in _diagnostic_codes(payload)


def test_runtime_adapter_dispatches_completion_claim_cli_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "completion-claim",
            "--cwd",
            str(ROOT),
            "--target-path",
            "README.md",
            "--verification-evidence",
            "python3 code/specs_validate.py all --format text --fail-on-diagnostics",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "ldvh.completion_claim"
    assert payload["summary"]["internal_event"] == "completion_claim"
    assert payload["dispatch"]["summary"]["integration_scope"] == "hook.completion_claim"
    assert payload["dispatch"]["receipt"]["verification_evidence"] == [
        "python3 code/specs_validate.py all --format text --fail-on-diagnostics",
    ]


def test_runtime_adapter_blocks_unknown_event_payload() -> None:
    adapter_payload = {
        "event": "unknown_event",
        "session_id": "test-runtime-adapter",
        "target_path": "README.md",
        "operation": "read",
        "task": "进入 LDVH v3 工作",
        "acknowledged_paths": [],
        "verification_evidence": [],
    }

    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "--payload-json",
            json.dumps(adapter_payload, ensure_ascii=False),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["dispatch"] is None
    assert "RUNTIME_ADAPTER_EVENT_UNKNOWN" in _diagnostic_codes(payload)


def test_runtime_adapter_does_not_expose_acknowledge_read_plan_payload() -> None:
    adapter_payload = {
        "event": "acknowledge_read_plan",
        "session_id": "test-runtime-adapter",
        "target_path": "README.md",
        "operation": "read",
        "task": "确认读取计划",
        "acknowledged_paths": [
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
        "verification_evidence": [],
    }

    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "--payload-json",
            json.dumps(adapter_payload, ensure_ascii=False),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["dispatch"] is None
    assert "RUNTIME_ADAPTER_EVENT_UNKNOWN" in _diagnostic_codes(payload)


def test_runtime_adapter_blocks_missing_payload_fields() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "--payload-json",
            json.dumps({"event": "session_start"}, ensure_ascii=False),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["dispatch"] is None
    assert "RUNTIME_ADAPTER_PAYLOAD_FIELD_MISSING" in _diagnostic_codes(payload)


def test_runtime_supports_all_consumption_timings(validation_result: dict) -> None:
    events = [row["consumption_timing"] for row in validation_result["consumption_timings"]]
    common_kwargs = {
        "acknowledged_paths": TEST_TARGET_ACK_PATHS,
        "target_path": "tests/code/test_ldvh_specs_validate.py",
        "verification_evidence": ["python3 -m pytest tests/code"],
    }

    for event in events:
        runtime = ldvh_specs.build_runtime_event(
            ROOT,
            event=event,
            validation=validation_result,
            **common_kwargs,
        )
        assert runtime["summary"]["event"] == f"ldvh.{event}"
        assert runtime["summary"]["internal_event"] == event
        assert runtime["receipt"]["canonical_event"] == f"ldvh.{event}"
        assert runtime["receipt"]["internal_event"] == event


def test_specs_validate_cli_runtime_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/specs_validate.py",
            "runtime",
            "--event",
            "session_start",
            "--session-id",
            "cli-session",
            "--format",
            "json",
            "--fail-on-diagnostics",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["metadata"]["read_only"] is True
    assert payload["metadata"]["environment_integrated"] is False
    assert payload["summary"]["status"] == "ok"
    assert payload["receipt"]["receipt_type"] == "runtime_event"
    assert payload["receipt"]["storage"] == "stdout_only"
