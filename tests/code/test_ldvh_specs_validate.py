from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import ldvh_specs


ROOT = Path(__file__).resolve().parents[2]


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


def _run_cli(args: list[str], *, cwd: Path, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess:
    """运行 CLI 子进程，超时时打印 stdout/stderr 再抛出，避免调试信息丢失。"""
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=check,
            timeout=timeout,
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
    assert "git_commit_action_template" in contracts["06"]["code_consumption"]
    assert "ldvh_install_initialization_action_template" in contracts["06"]["code_consumption"]
    assert "workcase_minimal_action_template" in contracts["06"]["code_consumption"]
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
    assert "8. Code 变更纪律" in contracts["07"]["rule_body_sections"]
    assert any("测试输出" in item for item in contracts["09"]["human_gate"])
    for contract in contracts.values():
        assert contract["source_refs"]
        assert contract["assurance_measures"]
        assert contract["verification_checks"]
        assert contract["human_gate"]
        assert contract["stop_conditions"]


def test_readme_indexes_action_template_spec_30() -> None:
    raw = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "`30`：LDVH 安装初始化管辖项目配置行动模板" in raw


def test_migration_33a_marks_formal_review_hash_gate_superseded() -> None:
    raw = (ROOT / "_migration/33A-action-template-30-admission.md").read_text(encoding="utf-8")

    assert "formal review hash gate 的描述只保留为历史迁移记录" in raw
    assert "formal review 机制后续已废弃" in raw
    assert "`reviews/formal/30-formal-review.yaml` 不再是当前仓库应存在的产物" in raw


def test_assurance_spec_registers_environment_entry_status_and_payload_contracts(validation_result: dict) -> None:
    result = validation_result
    specs = {spec["object_id"]: spec for spec in result["specs"]}
    attachments = {attachment["object_id"]: attachment for attachment in result["attachments"]}

    spec_01 = specs["01"]
    assert spec_01["path"] == "specs/01-保障与衔接.md"
    assert spec_01["status"] == "active"
    assert spec_01["metadata"]["authority"] == "active"
    assert set(spec_01["metadata"]["code_consumption"]) >= {
        "environment_entry_type_contract",
        "environment_integration_status_contract",
        "runtime_protocol_hook_entry",
        "runtime_payload_contract",
        "install_rollback_contract",
        "manual_ready_boundary",
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
    rollback = (ROOT / "specs/attachments/01.Att.06-环境安装回滚检查表.md").read_text(encoding="utf-8")
    runtime_protocol_entry = (ROOT / "hooks/LDVH-RUNTIME-PROTOCOL.md").read_text(encoding="utf-8")
    thin_reference_template = (ROOT / "hooks/LDVH-THIN-REFERENCE-TEMPLATE.md").read_text(encoding="utf-8")

    assert "V3 当前 Hook 分为两类" in spec_01
    assert "hooks/LDVH-RUNTIME-PROTOCOL.md" in spec_01
    assert "hooks/LDVH-THIN-REFERENCE-TEMPLATE.md" in spec_01
    assert "hook_protocol_entry" in spec_01
    assert "只允许写入口身份、权威回指和当前 Code 入口" in spec_01
    assert "不得写接入状态" in spec_01
    assert "接入状态由 `01.Att.04` 和 Code 环境审计承接" in spec_01
    assert "不恢复 V2 persistent session receipt 存储" in spec_01
    assert "不作为环境 adapter 的独立 lifecycle event" in spec_01
    assert "Git Hook" in spec_01
    assert "环境 Hook" in spec_01
    assert "只能定位并调用 LDVH" in spec_01
    assert "核心逻辑都必须留在 LDVH Code 中" in spec_01
    assert "所有支持 Hook 的协作环境" in spec_01
    assert "LDVH 插件、扩展包或 package" in spec_01
    assert "非管辖项目必须 no-op" in spec_01
    assert "卸载时必须移除或禁用该 repo 的 shim" in spec_01
    assert "验证环境不再自动触发 LDVH" in spec_01

    assert "| `git_hook_shim` |" in entry_types
    assert "| `hook_protocol_entry` |" in entry_types
    assert "hooks/LDVH-RUNTIME-PROTOCOL.md" in entry_types
    assert "不写接入状态" in entry_types
    assert "| `environment_hook` |" in entry_types
    assert "LDVH 环境插件" in entry_types
    assert "Codex plugin" in entry_types
    assert "只调用 LDVH" in entry_types
    assert "只指向 LDVH runtime / adapter" in entry_types

    assert "| `entry_kind` |" in rollback
    assert "| `shim_boundary` |" in rollback
    assert "| `rollback_state` |" in rollback
    assert "插件或扩展 manifest" in rollback
    assert "恢复或保留原有用户 Hook / 环境配置" in rollback

    assert "文件状态：hook protocol entry" in runtime_protocol_entry
    assert "本文只写三类内容" in runtime_protocol_entry
    assert "入口身份" in runtime_protocol_entry
    assert "权威回指" in runtime_protocol_entry
    assert "当前 Code 入口" in runtime_protocol_entry
    assert "接入状态" not in runtime_protocol_entry
    assert "python3 code/runtime_adapter.py session-start --format json" in runtime_protocol_entry

    assert "文件状态：thin reference template" in thin_reference_template
    assert "<LDVH_ROOT>/hooks/LDVH-RUNTIME-PROTOCOL.md" in thin_reference_template
    assert "<LDVH_ROOT>/specs/01-保障与衔接.md" in thin_reference_template
    assert "<LDVH_ROOT>/specs/10-管辖项目配置规范.md" in thin_reference_template
    assert "不恢复 `rules/` 目录或 Rules registry" in thin_reference_template
    assert "不声明任何环境已经 integrated" in thin_reference_template


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
        "| Gate 显式要求 | 模板必须写出暂停、分流和 Human Gate 条件 | 本文、01、02 | 门禁治理 | 模板涉及写入、提交、验收或风险接受时 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "FOUNDATION_ASSURANCE_ROW_MISSING" in _diagnostic_codes(result)
    assert any("Gate 显式要求" in diagnostic["message"] for diagnostic in result["diagnostics"])


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
        "specs/10-管辖项目配置规范.md",
        "V3 判定管辖项目必须采用 target-first；只有缺少明确 target 时，才允许使用 cwd fallback。",
        "V3 判定管辖项目必须优先使用工作对象。",
    )

    result = ldvh_specs.build_validation(root)

    assert "GOVERNED_PROJECT_TARGET_FIRST_MISSING" in _diagnostic_codes(result)


def test_governed_project_spec_requires_config_hierarchy_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/10-管辖项目配置规范.md",
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
        "specs/10-管辖项目配置规范.md",
        "管辖项目必须是 Git 管理的项目",
        "",
    )

    result = ldvh_specs.build_validation(root)

    assert "GOVERNED_PROJECT_CONFIG_BOUNDARY_MISSING" in _diagnostic_codes(result)
    assert any("管辖项目必须是 Git 管理的项目" in diagnostic["message"] for diagnostic in result["diagnostics"])


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
        "`_migration` 迁移材料不得被写成事实实例；它只作为迁移证据或历史来源。",
    )

    result = ldvh_specs.build_validation(root)

    assert "FACT_INSTANCE_MIGRATION_BOUNDARY_MISSING" in _diagnostic_codes(result)


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


def test_git_commit_action_template_is_code_consumable(validation_result: dict) -> None:
    result = validation_result
    rows = {row["结构"]: row["最小要求"] for row in result["git_commit_action_template"]}

    assert set(rows) == {"Context", "Scenario", "Gate", "执行", "验证", "回写", "交还"}
    assert "Git 工作区摘要" in rows["Context"]
    assert "diff" in rows["执行"]
    assert "Human Gate" in rows["Gate"]
    assert "09.Att.01" in rows["验证"]
    assert "commit hash" in rows["交还"]


def test_git_commit_action_template_reports_missing_status_context(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "Git 工作区摘要、",
    )

    result = ldvh_specs.build_validation(root)

    assert "GIT_COMMIT_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("Git 工作区摘要" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_git_commit_action_template_reports_missing_split_gate(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "提交拆分边界不清、",
    )

    result = ldvh_specs.build_validation(root)

    assert "GIT_COMMIT_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("提交拆分边界不清" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_git_commit_action_template_reports_missing_verification_evidence(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "和证据回指",
    )

    result = ldvh_specs.build_validation(root)

    assert "GIT_COMMIT_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("证据回指" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_git_commit_action_template_reports_missing_handoff_fields(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "commit hash、",
    )

    result = ldvh_specs.build_validation(root)

    assert "GIT_COMMIT_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("commit hash" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_action_guide_does_not_replace_main_ai_judgment_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "但 Action Guide 不替代主控 AI 判断、事实源、Human Gate、验证声明或行动模板执行结果。",
    )

    result = ldvh_specs.build_validation(root)

    assert "GIT_COMMIT_ACTION_TEMPLATE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_git_commit_action_template_reports_missing_skill_execution_modes(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "、`manual_equivalent_execution`",
    )

    result = ldvh_specs.build_validation(root)

    assert "GIT_COMMIT_ACTION_TEMPLATE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_workcase_action_template_is_code_consumable(validation_result: dict) -> None:
    result = validation_result
    rows = {row["结构"]: row["最小要求"] for row in result["workcase_action_template"]}

    assert set(rows) == {"Context", "Scenario", "Gate", "执行", "验证", "回写", "交还"}
    assert "WorkCase ID" in rows["Context"]
    assert "创建 WorkCase" in rows["Scenario"]
    assert "`human_closure_confirming`" in rows["Gate"]
    assert "`closed`" in rows["执行"]
    assert "09.Att.01" in rows["验证"]
    assert "正式 WorkCase 事实实例" in rows["回写"]
    assert "下一步 Human Gate" in rows["交还"]


def test_ldvh_install_action_template_is_code_consumable(validation_result: dict) -> None:
    result = validation_result
    rows = {row["结构"]: row["最小要求"] for row in result["ldvh_install_action_template"]}
    contract = result["ldvh_install_spec_contract"]

    assert set(rows) == {"Context", "Scenario", "Gate", "执行", "验证", "回写", "交还"}
    assert contract["spec_id"] == "30"
    assert set(contract["code_consumption"]) == set(ldvh_specs.LDVH_INSTALL_REQUIRED_CODE_CONSUMPTION)
    assert contract["action_template"]
    assert contract["stop_conditions"]
    assert contract["source_refs"]
    assert "目标环境" in rows["Context"]
    assert "LDVH 本体路径" in rows["Context"]
    assert "目标工作区根目录" in rows["Context"]
    assert "LDVH-GOVERNED-PROJECTS.yaml" in rows["Context"]
    assert "Git Hook 状态" in rows["Context"]
    assert "code/docs/03-LDVH-Install-Wizard-Practice.md" in rows["Context"]
    assert "安装 LDVH" in rows["Scenario"]
    assert "LDVH 本体路径" in rows["Gate"]
    assert "目标工作区根目录" in rows["Gate"]
    assert "配置层级冲突" in rows["Gate"]
    assert "管辖项目 Git Hook" in rows["Gate"]
    assert "有效 Git worktree" in rows["Gate"]
    assert "安装方案预览" in rows["Gate"]
    assert "最终确认" in rows["Gate"]
    assert "bootstrap discovery" in rows["执行"]
    assert "有限、只读、有证据" in rows["执行"]
    assert "LDVH_ROOT" in rows["执行"]
    assert "候选路径和证据" in rows["执行"]
    assert "不直接写入环境 Hook 系统文件" in rows["执行"]
    assert "安装方案预览" in rows["执行"]
    assert "目标工作区根目录" in rows["执行"]
    assert "配置文件完整路径" in rows["执行"]
    assert "项目根目录、用户级目录和 LDVH 本体目录不得作为主选项" in rows["执行"]
    assert "配置层级检查" in rows["执行"]
    assert "目标项目内已存在配置" in rows["执行"]
    assert "target-first resolver" in rows["执行"]
    assert "AI 环境 Hook" in rows["执行"]
    assert "Git `commit-msg` Hook" in rows["执行"]
    assert "governed_hook_adapter.py status" in rows["验证"]
    assert "install_verification.py" in rows["验证"]
    assert "governed_hook_adapter.py verify" in rows["验证"]
    assert "managed `commit-msg` hook" in rows["验证"]
    assert "正反样例" in rows["验证"]
    assert "安装状态可复现" in rows["验证"]
    assert "不得把 runtime receipt" in rows["回写"]
    assert "integrated / manual_ready / deferred / removed_top_level" in rows["交还"]


def test_ldvh_install_action_template_defines_wizard_state_machine(validation_result: dict) -> None:
    raw = (ROOT / "specs/30-LDVH安装初始化管辖项目配置行动模板.md").read_text(encoding="utf-8")

    assert "安装向导状态机" in raw
    assert "路径确认" in raw
    assert "安装前检查" in raw
    assert "安装选项" in raw
    assert "安装方案预览" in raw
    assert "最终确认" in raw
    assert "决策 / 结果" in raw
    assert "状态、步骤、决策 / 结果三列" in raw
    assert "👉" in raw
    assert "✅" in raw
    assert "尚未发生的步骤保持空白" in raw
    assert "用户视角摘要" in raw
    assert "本步目的" in raw
    assert "不会做什么" in raw
    assert "需要决定什么" in raw
    assert "进度安全提示" in raw
    assert "当前已完成几步" in raw
    assert "选择框 / 单选控件" in raw
    assert "每次只问一个问题" in raw
    assert "选项表必须给出选项、说明和结果" in raw
    assert "不得把“返回修改”写成第三个主选项" in raw
    assert "方案确认和执行确认" in raw
    assert "4/5 安装方案预览只能询问“是否进入最终确认”" in raw
    assert "该选择不是执行授权" in raw
    assert "不得用“执行方案”或其它会让 Human 误以为已经授权写入的措辞" in raw
    assert "5/5 最终确认必须直接询问“执行方案”或“不执行，停止安装”" in raw
    assert "不得再次要求 Human 确认只读检查" in raw
    assert "不得继续解释流程或再次索要同一授权" in raw
    assert "📍 路径确认" in raw
    assert "🔎 安装前检查" in raw
    assert "⚙️ 安装选项" in raw
    assert "🔒 安装方案预览" in raw
    assert "🛠️ 最终确认" in raw
    assert "📦 LDVH 本体路径" in raw
    assert "🗂️ 目标工作区根目录" in raw
    assert "🧾 配置文件完整路径" in raw
    assert "✅ 通过" in raw
    assert "⚠️ 注意" in raw
    assert "⚠️ 需安装" in raw
    assert "⚠️ 需升级" in raw
    assert "⛔ 阻断" in raw
    assert "➖ 不适用" in raw
    assert "下一步处理" in raw
    assert "状态图例" in raw
    assert "是否阻断" in raw
    assert "`⚠️ 注意` 只表示需知情或需关注，不自动阻断" in raw
    assert "`⚠️ 需安装` 和 `⚠️ 需升级` 必须进入安装方案预览" in raw
    assert "🔌 环境入口" in raw
    assert "🪝 Git Hook" in raw
    assert "🪝 管辖项目 Git Hook" in raw
    assert "🗑️ 项目内旧配置" in raw
    assert "🧪 验证" in raw
    assert "↩️ 回滚" in raw
    assert "需授权动作" in raw
    assert "不得把事实伪装成 Human 选项" in raw
    assert "环境插件未安装时必须标为 `⚠️ 需安装` 并安排安装方案" in raw
    assert "环境插件已安装但指向旧路径、旧版本或 stale V2 path 时必须标为 `⚠️ 需升级` 并安排升级方案" in raw
    assert "每个已选择管辖项目都必须检查 Git `commit-msg` Hook 状态" in raw
    assert "非 Git 目录必须标为 `⛔ 阻断` 并说明管辖项目必须是 Git 仓库" in raw
    assert "不得把这类情况表达成“不安装插件”“不处理插件”或“Git Hook 后置可不做”" in raw
    assert "完整安装方案必须同时覆盖 AI 环境 Hook 和管辖项目 Git Hook" in raw
    assert "`core.hooksPath` / active hook 状态" in raw
    assert "验证命令和卸载 / rollback 命令" in raw
    assert "主界面只展示普通用户作出下一步判断所需的信息" in raw
    assert "会改变什么" in raw
    assert "不会改变什么" in raw
    assert "执行后还需要验证什么" in raw
    assert "技术明细" in raw
    assert "净变化" in raw
    assert "将新增" in raw
    assert "将修改或升级" in raw
    assert "将保持不变" in raw
    assert "不会执行" in raw
    assert "需后置确认" in raw
    assert "不可验证范围" in raw
    assert "不得混入“验证通过”" in raw
    assert "环境 Hook 或插件提示必须按当前目标环境命名" in raw
    assert "当前 AI 运行环境名称" in raw
    assert "不得沿用示例环境名称" in raw
    assert "只有当前运行环境、环境审计或 Human 明确目标环境为 Codex" in raw
    assert "目标环境插件 / 工具入口插件" in raw
    assert "插件 / 扩展页面或入口位置" in raw
    assert "授权 / trust" in raw
    assert "新开窗口或新会话" in raw
    assert "未真实写入插件包、未进入插件页面或未获得授权证据前，不得写成“插件已安装”" in raw
    assert "`待用户安装`" in raw
    assert "`需授权`" in raw
    assert "`可见 / 需验证`" in raw
    assert "`已写入但待用户授权`" in raw
    assert "安装方案预览必须停止为 blocking" in raw
    assert "管辖项目必须是 Git 仓库" in raw
    assert "当前配置项目清单" in raw
    assert "不得只写“保留工作区配置”" in raw
    assert "product_name" in raw
    assert "product_description" in raw
    assert "编号" in raw
    assert "项目 ID" in raw
    assert "项目路径" in raw
    assert "Git common-dir" in raw
    assert "是否已设置为管辖项目" in raw
    assert "不得展示“当前目标”列" in raw
    assert "1 不改管辖项目配置" in raw
    assert "2 按编号设置管辖项目" in raw
    assert "编号列表" in raw
    assert "配置正确性结论" in raw
    assert "字段闭集" in raw
    assert "项目 ID 唯一" in raw
    assert "target-first 解析结论" in raw
    assert "拟写入项目清单" in raw
    assert "bootstrap discovery" in raw
    assert "有限、只读、有证据" in raw
    assert "找不到时必须要求 Human 提供 LDVH 本体路径" in raw
    assert "配置位置不是选项，只能是目标工作区根目录" in raw
    assert "项目根目录、用户级目录和 LDVH 本体目录都不是支持位置" in raw
    assert "说明、限制和建议" in raw
    assert "可复制路径块" in raw
    assert "LDVH_ROOT=<ldvh-root>" in raw
    assert "WORKSPACE_ROOT=<workspace-root>" in raw
    assert "GOVERNED_CONFIG=<workspace-root>/LDVH-GOVERNED-PROJECTS.yaml" in raw
    assert "配置层级冲突" in raw
    assert "先删除、迁移或明确保留其中一个配置文件" in raw
    assert "最终确认只展示两个主选项" in raw
    assert "1 执行方案" in raw
    assert "2 不执行，停止安装" in raw
    assert "选择执行后才会开始写入" in raw
    assert "最终确认摘要只列出将写入对象和不写入对象" in raw
    assert "不得重复安装前检查表" in raw
    assert "写入后执行验证" in raw
    assert "不得把返回修改作为第三个主选项" in raw
    assert "最终确认前" in raw
    assert "不得写入配置" in raw


def test_ldvh_install_action_template_reports_missing_code_consumption(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
        '    - "install_user_disclosure_checklist"\n',
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_CODE_CONSUMPTION_MISSING" in _diagnostic_codes(result)
    assert any("install_user_disclosure_checklist" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_unsupported_code_consumption(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
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
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
        "、目标工作区根目录",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("目标工作区根目录" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_bootstrap_discovery(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
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
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
        "不直接写入用户环境 Hook 系统文件",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_ACTION_TEMPLATE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_ldvh_install_action_template_reports_missing_unsupported_config_locations(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
        "项目根目录、用户级目录和 LDVH 本体目录都不是支持位置",
        "",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("项目根目录、用户级目录和 LDVH 本体目录都不是支持位置" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_workspace_config_location(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
        "配置位置不是选项，只能是目标工作区根目录",
        "配置文件位置可在执行时说明",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("配置位置不是选项，只能是目标工作区根目录" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_wizard_state_machine(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
        "尚未发生的步骤保持空白",
        "尚未发生的步骤写入待办状态",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("尚未发生的步骤保持空白" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_user_summary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
        "用户视角摘要",
        "步骤摘要",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("用户视角摘要" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_final_confirmation_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
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
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
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
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
        "环境 Hook 或插件提示必须按当前目标环境命名",
        "环境 Hook 或插件提示可以沿用当前示例环境名称",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("环境 Hook 或插件提示必须按当前目标环境命名" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_ldvh_install_action_template_reports_missing_current_environment_name_rule(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/30-LDVH安装初始化管辖项目配置行动模板.md",
        "当前 AI 运行环境名称",
        "目标环境名称",
    )

    result = ldvh_specs.build_validation(root)

    assert "LDVH_INSTALL_WIZARD_TERM_MISSING" in _diagnostic_codes(result)
    assert any("当前 AI 运行环境名称" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_workcase_action_template_reports_missing_human_gate(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "、从 `human_closure_confirming` 关闭",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("human_closure_confirming" in diagnostic["message"] for diagnostic in result["diagnostics"])


def test_workcase_action_template_reports_missing_closure_handoff(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "| 交还 | 交还 WorkCase ID、当前状态、变更摘要、验证摘要、残留风险、下一步 Human Gate、source_refs 和未完成分流；阻断时交还阻断原因、缺少证据和建议的下一步。 |\n",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_ACTION_TEMPLATE_ROW_MISSING" in _diagnostic_codes(result)


def test_workcase_action_template_reports_missing_manual_boundary(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "`manual_equivalent_execution`",
        "`manual_execution`",
    )

    result = ldvh_specs.build_validation(root)

    assert "WORKCASE_ACTION_TEMPLATE_BOUNDARY_MISSING" in _diagnostic_codes(result)


def test_workcase_member_contract_is_code_consumable(validation_result: dict) -> None:
    result = validation_result
    contract = result["workcase_member_contract"]

    assert contract["path"] == "specs/21-WorkCase-工作项.md"
    assert set(contract["code_consumption"]) >= {
        "fact_model_member_identity",
        "workcase_source_boundaries",
        "workcase_state_boundaries",
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
            "specs/10-管辖项目配置规范.md",
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


def test_session_start_cli_exports_manual_read_plan_json() -> None:
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
    assert payload["summary"]["event"] == "session_start"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["summary"]["integration_scope"] == "manual.session_start"
    assert payload["metadata"]["integration_scope"] == "manual.session_start"
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
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "acknowledge_read_plan"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["summary"]["integration_scope"] == "manual.acknowledge_read_plan"
    assert payload["metadata"]["integration_scope"] == "manual.acknowledge_read_plan"
    assert payload["receipt"]["storage"] == "stdout_only"
    assert payload["receipt"]["persistent"] is False
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
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["integration_scope"] == "manual.acknowledge_read_plan"
    assert "RUNTIME_ACK_REQUIRED_PATHS_EMPTY" in _diagnostic_codes(payload)


def test_runtime_pre_tool_use_includes_preflight(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path="code/ldvh_specs.py",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
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


def test_pre_tool_use_cli_accepts_manual_preflight_json() -> None:
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
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "pre_tool_use"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["summary"]["integration_scope"] == "manual.pre_tool_use"
    assert payload["summary"]["preflight_status"] == "diagnostic_clear"
    assert payload["metadata"]["integration_scope"] == "manual.pre_tool_use"
    assert payload["receipt"]["storage"] == "stdout_only"
    assert payload["receipt"]["acknowledged_paths"] == [
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    ]
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
    assert payload["summary"]["integration_scope"] == "manual.pre_tool_use"


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
    message = """docs(docs): 对齐阶段9主线切换范围

关键变更:
- 新增阶段9范围和9A审计

验证结论:
- python3 -m pytest tests/code _migration/tests -q 通过
"""

    gate = ldvh_specs.build_commit_gate(
        ROOT,
        message=message,
        changed_paths=[
            "_migration/9-v3-mainline-transition-scope.md",
            "_migration/9A-migration-layer-dependency-audit.md",
        ],
    )

    assert gate["metadata"]["authorization"] == "none"
    assert gate["metadata"]["environment_integrated"] is False
    assert gate["metadata"]["hook_integrated"] is False
    assert gate["summary"]["status"] == "ok"
    assert gate["summary"]["body_required"] is True
    assert gate["summary"]["read_plan_required"] is False
    assert gate["summary"]["read_plan_consumed"] is True
    assert gate["body_required_reasons"] == ["多文件范围", "边界变化"]
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
        message="docs(migration): 对齐阶段9主线切换范围",
        changed_paths=["_migration/9-v3-mainline-transition-scope.md"],
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
    )

    assert gate["summary"]["status"] == "blocked"
    assert "COMMIT_SCOPE_NOT_ALLOWED" in _diagnostic_codes(gate)


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
            "_migration/9-v3-mainline-transition-scope.md",
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


def test_environment_status_reports_commit_hook_and_manual_entries(tmp_path: Path) -> None:
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
    assert set(payload["summary"]["manual_entrypoints"]) == {
        "manual.runtime_adapter",
        "manual.session_start",
        "manual.acknowledge_read_plan",
        "manual.pre_tool_use",
        "manual.completion_claim",
    }
    assert payload["summary"]["manual_entries_available"] is True
    assert entrypoints["git.commit-msg"]["integrated"] is True
    assert entrypoints["manual.runtime_adapter"]["available"] is True
    assert entrypoints["manual.runtime_adapter"]["integrated"] is False
    assert entrypoints["manual.acknowledge_read_plan"]["available"] is True
    assert entrypoints["manual.acknowledge_read_plan"]["integrated"] is False
    assert entrypoints["manual.pre_tool_use"]["details"]["automatic_trigger"] is False
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
    assert payload["summary"]["manual_entries_available"] is True
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
    assert candidates["hooks.runtime-protocol"]["status"] == "available"
    assert candidates["hooks.runtime-protocol"]["integrated"] is False
    assert candidates["hooks.runtime-protocol"]["category"] == "hook_protocol_entry"
    assert candidates["hooks.thin-reference-template"]["status"] == "available"
    assert candidates["hooks.thin-reference-template"]["integrated"] is False
    assert candidates["hooks.thin-reference-template"]["category"] == "repo_instruction_candidate"
    assert candidates["runtime.pre_tool_use.auto"]["status"] == "deferred"
    assert candidates["runtime.pre_tool_use.auto"]["manual_fallback"] == "code/pre_tool_use.py"
    assert candidates["codex.ldvh-plugin"]["status"] == "absent"
    assert candidates["codex.ldvh-plugin"]["decision"] == "install_plugin_before_claiming"
    assert candidates["rules.top_level_mechanism"]["status"] == "removed_top_level"
    assert candidates["rules.top_level_mechanism"]["decision"] == "removed_top_level"
    assert candidates["skills.top_level_mechanism"]["status"] == "removed_top_level"
    assert candidates["skills.top_level_mechanism"]["decision"] == "removed_top_level"
    assert candidates["codex.repo-instructions"]["status"] == "absent"
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
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}
    assert payload["summary"]["integrated_entrypoints"] == ["git.commit-msg"]
    assert candidates["hooks.runtime-protocol"]["status"] == "available"
    assert candidates["hooks.runtime-protocol"]["integrated"] is False
    assert candidates["hooks.thin-reference-template"]["status"] == "available"
    assert candidates["hooks.thin-reference-template"]["integrated"] is False
    assert candidates["codex.repo-instructions"]["status"] == "available"
    assert candidates["codex.repo-instructions"]["integrated"] is False
    assert candidates["codex.ldvh-plugin"]["status"] == "absent"
    assert candidates["rules.top_level_mechanism"]["status"] == "removed_top_level"
    assert candidates["skills.top_level_mechanism"]["status"] == "removed_top_level"
    assert payload["summary"]["codex_environment_entry_integrated"] is False
    assert "ENV_CODEX_ENTRY_FILES_NOT_INTEGRATED" in _diagnostic_codes(payload)


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
    assert str(v3_shim) in "\n".join(candidates["codex.ldvh-plugin"]["details"]["commands"])


def test_runtime_completion_claim_requires_verification_evidence(validation_result: dict) -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="completion_claim",
        validation=validation_result,
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_COMPLETION_VERIFICATION_MISSING"


def test_completion_claim_cli_accepts_manual_evidence_json() -> None:
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
    assert payload["summary"]["event"] == "completion_claim"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["summary"]["integration_scope"] == "manual.completion_claim"
    assert payload["summary"]["verification_evidence"] == 2
    assert payload["metadata"]["integration_scope"] == "manual.completion_claim"
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
    assert payload["summary"]["integration_scope"] == "manual.completion_claim"
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
    assert payload["summary"]["event"] == "session_start"
    assert payload["summary"]["adapter_integrated"] is False
    assert payload["metadata"]["integration_scope"] == "manual.runtime_adapter"
    assert payload["dispatch"]["summary"]["integration_scope"] == "manual.session_start"
    assert {
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    }.issubset(read_paths)


def test_runtime_adapter_dispatches_pre_tool_use_cli_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "pre-tool-use",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
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
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "pre_tool_use"
    assert payload["dispatch"]["summary"]["integration_scope"] == "manual.pre_tool_use"
    assert payload["dispatch"]["preflight"]["summary"]["target_type"] == "tests"
    assert payload["diagnostics"] == []


def test_runtime_adapter_dispatches_completion_claim_cli_json() -> None:
    completed = _run_cli(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "completion-claim",
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
    assert payload["summary"]["event"] == "completion_claim"
    assert payload["dispatch"]["summary"]["integration_scope"] == "manual.completion_claim"
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
        "acknowledged_paths": [
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
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
        assert runtime["summary"]["event"] == event
        assert runtime["receipt"]["canonical_event"] == event


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
