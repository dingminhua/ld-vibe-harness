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


def test_current_specs_validate_without_diagnostics() -> None:
    result = ldvh_specs.build_validation(ROOT)

    assert result["summary"]["status"] == "ok"
    assert result["summary"]["specs"] == 16
    assert result["summary"]["attachments"] == 16
    assert result["summary"]["foundation_spec_contracts"] == 6
    assert result["summary"]["governed_projects"] == 1
    assert result["diagnostics"] == []


def test_foundation_specs_contracts_are_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)
    contracts = {contract["spec_id"]: contract for contract in result["foundation_spec_contracts"]}

    assert set(contracts) == {"03", "05", "06", "07", "08", "09"}
    assert "commit_contract_boundaries" in contracts["03"]["code_consumption"]
    assert "commit_message_contract_fields" in contracts["03"]["code_consumption"]
    assert "fact_object_admission" in contracts["05"]["code_consumption"]
    assert "field_registry_contract" in contracts["05"]["code_consumption"]
    assert "context_scenario_gate" in contracts["06"]["code_consumption"]
    assert "git_commit_action_template" in contracts["06"]["code_consumption"]
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


def test_assurance_spec_registers_environment_entry_status_and_payload_contracts() -> None:
    result = ldvh_specs.build_validation(ROOT)
    specs = {spec["object_id"]: spec for spec in result["specs"]}
    attachments = {attachment["object_id"]: attachment for attachment in result["attachments"]}

    spec_01 = specs["01"]
    assert spec_01["path"] == "specs/01-保障与衔接.md"
    assert spec_01["status"] == "active"
    assert spec_01["metadata"]["authority"] == "active"
    assert set(spec_01["metadata"]["code_consumption"]) >= {
        "environment_entry_type_contract",
        "environment_integration_status_contract",
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


def test_migrated_attachment_contracts_are_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)
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


def test_governed_projects_config_is_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)
    config = result["governed_projects_config"]
    resolution = result["governed_project_resolution"]

    assert config["product_name"] == "LD Vibe Harness v3"
    assert [project["id"] for project in config["projects"]] == ["ldvh-v3"]
    assert resolution["governed"] is True
    assert resolution["governed_project_id"] == "ldvh-v3"
    assert resolution["governed_via"] == "path"


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
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "ldvh@example.test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "LDVH Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "test: init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "worktree", "add", str(worktree)], cwd=repo, check=True, capture_output=True, text=True)
    common_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
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


def test_implementation_domain_boundaries_are_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)

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


def test_git_commit_action_template_is_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)
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


def test_workcase_action_template_is_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)
    rows = {row["结构"]: row["最小要求"] for row in result["workcase_action_template"]}

    assert set(rows) == {"Context", "Scenario", "Gate", "执行", "验证", "回写", "交还"}
    assert "WorkCase ID" in rows["Context"]
    assert "创建 WorkCase" in rows["Scenario"]
    assert "`human_closure_confirming`" in rows["Gate"]
    assert "`closed`" in rows["执行"]
    assert "09.Att.01" in rows["验证"]
    assert "正式 WorkCase 事实实例" in rows["回写"]
    assert "下一步 Human Gate" in rows["交还"]


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


def test_workcase_member_contract_is_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)
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


def test_fact_model_member_contracts_are_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)
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


def test_fact_instances_are_migrated_and_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)
    instances = result["fact_instances"]
    counts: dict[str, int] = {}
    for instance in instances:
        counts[instance["kind"]] = counts.get(instance["kind"], 0) + 1

    assert result["summary"]["fact_instances"] == 77
    assert counts == {
        "spark": 40,
        "workcase": 22,
        "pitfall": 1,
        "study": 14,
    }
    assert any(instance["path"] == "ldvh-base/sparks/spark-0001-session-start-user-input-boundary.yaml" for instance in instances)
    assert any(instance["path"] == "ldvh-base/sparks/spark-0002-subdocument-status-gap.yaml" for instance in instances)
    assert any(instance["path"] == "ldvh-base/workcases/workcase-0002-knowledge-map-entry-navigation.yaml" for instance in instances)
    assert any(instance["path"] == "ldvh-base/studies/study-0001-workcase-orchestration-evolution.md" for instance in instances)


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

    assert set(objects) == {
        "00",
        "01",
        "01.Att.01",
        "01.Att.02",
        "01.Att.03",
        "01.Att.04",
        "01.Att.05",
        "01.Att.06",
        "02",
        "03",
        "03.Att.01",
        "04",
        "04.Att.01",
        "04.Att.02",
        "04.Att.03",
        "04.Att.04",
        "04.Att.05",
        "04.Att.06",
        "05",
        "05.Att.01",
        "06",
        "07",
        "08",
        "09",
        "09.Att.01",
        "10",
        "10.Att.01",
        "20",
        "21",
        "22",
        "23",
        "24",
    }
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


def test_ai_behavior_requirements_reference_allowed_timings() -> None:
    result = ldvh_specs.build_validation(ROOT)
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


def test_takeover_matrix_covers_ai_behavior_requirements() -> None:
    result = ldvh_specs.build_validation(ROOT)
    requirement_ids = {row["requirement_id"] for row in result["ai_behavior_requirements"]}
    matrix_ids = {row["requirement_id"] for row in result["takeover_matrix"]}

    assert matrix_ids == requirement_ids


def test_specs_validate_cli_json_all() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "code/specs_validate.py",
            "all",
            "--format",
            "json",
            "--fail-on-diagnostics",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["metadata"]["read_only"] is True
    assert payload["summary"]["status"] == "ok"
    assert payload["diagnostics"] == []


def test_specs_validate_cli_governed_projects_json() -> None:
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["metadata"]["read_only"] is True
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["governed"] is True
    assert payload["resolution"]["governed_project_id"] == "ldvh-v3"
    assert payload["resolution"]["governed_via"] == "path"


def test_e2e_rehearsal_covers_static_workflow() -> None:
    result = ldvh_specs.build_e2e_rehearsal(
        ROOT,
        target_path="tests/code/test_ldvh_specs_validate.py",
        task="阶段 8 端到端闭环测试",
    )

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


def test_e2e_rehearsal_output_has_no_authorization_terms() -> None:
    result = ldvh_specs.build_e2e_rehearsal(
        ROOT,
        target_path="tests/code/test_ldvh_specs_validate.py",
    )
    serialized = json.dumps(result, ensure_ascii=False)

    assert "approved" not in serialized
    assert "allowed" not in serialized
    assert "human_gate_passed" not in serialized


def test_specs_validate_cli_e2e_json() -> None:
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["stages"] == 7
    assert payload["summary"]["environment_integrated"] is False
    assert payload["closure_assessment"]["static_rehearsal_complete"] is True


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


def test_action_guide_pre_tool_use_reports_missing_target() -> None:
    guide = ldvh_specs.build_action_guide(ROOT, consumption_timing="pre_tool_use")

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


def test_action_guide_pre_tool_use_next_action_has_no_write_authorization() -> None:
    guide = ldvh_specs.build_action_guide(
        ROOT,
        consumption_timing="pre_tool_use",
        target_path="tests/code/test_ldvh_specs_validate.py",
    )

    assert guide["summary"]["status"] == "ok"
    assert "允许写入" not in guide["next_action"]
    assert "需交还 Human" in guide["next_action"]


def test_action_guide_unknown_timing_diagnostic() -> None:
    guide = ldvh_specs.build_action_guide(ROOT, consumption_timing="unknown_event")

    assert guide["summary"]["status"] == "failed"
    assert guide["missing_fields"][0]["field"] == "consumption_timing"
    assert guide["diagnostics"][0]["code"] == "ACTION_GUIDE_TIMING_UNKNOWN"


def test_specs_validate_cli_action_guide_json() -> None:
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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


def test_preflight_code_target_is_unverifiable_not_authorization() -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="code/ldvh_specs.py",
        operation="write",
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


def test_preflight_attachment_keeps_boundary_warning() -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="specs/attachments/01.Att.01-保障消费时机表.md",
        operation="write",
    )

    assert preflight["summary"]["target_type"] == "attachment"
    assert preflight["summary"]["warnings"] == 1
    assert preflight["diagnostics"][0]["code"] == "PREFLIGHT_ATTACHMENT_BOUNDARY"


def test_preflight_known_tests_target_uses_diagnostic_clear_status() -> None:
    preflight = ldvh_specs.build_preflight(
        ROOT,
        target_path="tests/code/test_ldvh_specs_validate.py",
        operation="write",
    )

    assert preflight["summary"]["status"] == "diagnostic_clear"
    assert preflight["diagnostics"] == []
    read_paths = {item["path"] for item in preflight["required_read_plan"]}
    assert {
        "specs/07-Code确定性执行规范.md",
        "specs/09-测试与验证规范.md",
    }.issubset(read_paths)


def test_preflight_unknown_target_blocks() -> None:
    preflight = ldvh_specs.build_preflight(ROOT, target_path="", operation="write")

    assert preflight["summary"]["status"] == "blocked"
    assert preflight["summary"]["blocking"] == 1
    assert preflight["diagnostics"][0]["code"] == "PREFLIGHT_TARGET_UNKNOWN"


def test_specs_validate_cli_preflight_json() -> None:
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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


def test_runtime_unknown_event_blocks() -> None:
    runtime = ldvh_specs.build_runtime_event(ROOT, event="unknown_event")

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["summary"]["blocking"] == 1
    assert runtime["receipt"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_EVENT_UNKNOWN"


def test_runtime_acknowledge_read_plan_requires_paths() -> None:
    runtime = ldvh_specs.build_runtime_event(ROOT, event="acknowledge_read_plan")

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_ACK_REQUIRED_PATHS_EMPTY"


def test_runtime_acknowledge_read_plan_accepts_entry_paths() -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="acknowledge_read_plan",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
    )

    assert runtime["summary"]["status"] == "ok"
    assert runtime["receipt"]["acknowledged_paths"] == [
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    ]
    assert runtime["diagnostics"] == []


def test_runtime_pre_tool_use_includes_preflight() -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path="code/ldvh_specs.py",
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
    )

    assert runtime["summary"]["status"] == "review_required"
    assert runtime["summary"]["has_preflight"] is True
    assert runtime["preflight"]["summary"]["target_type"] == "code"
    assert runtime["diagnostics"][0]["code"] == "PREFLIGHT_CODE_OUTPUT_NOT_AUTHORIZATION"


def test_runtime_pre_tool_use_blocks_without_read_plan_consumption() -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="pre_tool_use",
        target_path="tests/code/test_ldvh_specs_validate.py",
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_READ_PLAN_CONSUMED_EMPTY"


def test_pre_tool_use_cli_accepts_manual_preflight_json() -> None:
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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
    completed = subprocess.run(
        [
            sys.executable,
            "code/pre_tool_use.py",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in _diagnostic_codes(payload)
    assert payload["summary"]["integration_scope"] == "manual.pre_tool_use"


def test_pre_tool_use_cli_blocks_missing_target() -> None:
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert "PREFLIGHT_TARGET_UNKNOWN" in _diagnostic_codes(payload)
    assert payload["preflight"]["summary"]["target_type"] == "unknown"


def test_runtime_git_commit_msg_blocks_incomplete_read_plan_consumption() -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="git_commit_msg",
        target_path="tests/code/test_ldvh_specs_validate.py",
        acknowledged_paths=["specs/00-理念与构成.md"],
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_READ_PLAN_CONSUMED_INCOMPLETE"


def test_commit_gate_accepts_valid_message_with_read_plan_body() -> None:
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
        acknowledged_paths=[
            "specs/00-理念与构成.md",
            "specs/01-保障与衔接.md",
            "specs/02-AI行为规范.md",
        ],
    )

    assert gate["metadata"]["authorization"] == "none"
    assert gate["metadata"]["environment_integrated"] is False
    assert gate["metadata"]["hook_integrated"] is False
    assert gate["summary"]["status"] == "ok"
    assert gate["summary"]["body_required"] is True
    assert gate["summary"]["read_plan_consumed"] is True
    assert gate["body_required_reasons"] == ["多文件范围", "边界变化"]
    assert gate["diagnostics"] == []


def test_commit_gate_extracts_read_plan_from_message_body() -> None:
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
    )

    assert gate["summary"]["status"] == "ok"
    assert gate["summary"]["read_plan_consumed"] is True
    assert gate["acknowledged_paths"] == [
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    ]
    assert gate["message_acknowledged_paths"] == gate["acknowledged_paths"]
    assert gate["diagnostics"] == []


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
    completed = subprocess.run(
        [
            sys.executable,
            "code/specs_validate.py",
            "commit-gate",
            "--message-file",
            str(message_file),
            "--changed-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--acknowledged-path",
            "specs/00-理念与构成.md",
            "--acknowledged-path",
            "specs/01-保障与衔接.md",
            "--acknowledged-path",
            "specs/02-AI行为规范.md",
            "--format",
            "json",
            "--fail-on-diagnostics",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["environment_integrated"] is False
    assert payload["diagnostics"] == []


def test_commit_validate_wrapper_blocks_invalid_message(tmp_path: Path) -> None:
    message_file = tmp_path / "message.txt"
    message_file.write_text("docs(migration): 无效 scope\n", encoding="utf-8")

    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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

读取依据:
- specs/00-理念与构成.md
- specs/01-保障与衔接.md
- specs/02-AI行为规范.md

关键变更:
- 接入 worktree-local commit-msg hook。
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["metadata"]["hook_integrated"] is True
    assert payload["metadata"]["environment_integrated"] is True
    assert payload["metadata"]["integration_scope"] == "git.commit-msg"


def test_install_git_hooks_uses_worktree_local_hooks_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    completed = subprocess.run(
        [
            sys.executable,
            "code/install_git_hooks.py",
            "install",
            "--repo",
            str(repo),
            "--backend-allow-external",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    hook = repo / "hooks" / "commit-msg"
    config = subprocess.run(
        ["git", "config", "--show-origin", "--get", "core.hooksPath"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "- installed: True" in completed.stdout
    assert "config.worktree" in config.stdout
    assert config.stdout.rstrip().endswith("\thooks")
    assert hook.is_file()
    assert os.access(hook, os.X_OK)
    assert "# LDVH v3 managed commit-msg hook" in hook.read_text(encoding="utf-8")
    assert not (repo / ".git" / "hooks" / "commit-msg").exists()


def test_install_git_hooks_blocks_direct_external_repo_write(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
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

    completed = subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    hook = repo / "hooks" / "commit-msg"
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["governed"] is True
    assert payload["summary"]["governed_project_id"] == "app"
    assert payload["summary"]["hook_integrated"] == "git.commit-msg"
    assert payload["metadata"]["human_gate_confirmed"] is True
    assert hook.is_file()
    assert os.access(hook, os.X_OK)
    hook_text = hook.read_text(encoding="utf-8")
    assert "# LDVH v3 managed commit-msg hook" in hook_text
    assert ROOT.as_posix() in hook_text

    rollback = subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )
    rollback_payload = json.loads(rollback.stdout)
    hooks_path = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert rollback_payload["summary"]["status"] == "ok"
    assert rollback_payload["summary"]["hook_integrated"] == "none"
    assert hooks_path.returncode != 0


def test_governed_hook_adapter_requires_human_gate_for_install(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
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

    completed = subprocess.run(
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
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["hook_integrated"] == "none"
    assert "GOVERNED_HOOK_HUMAN_GATE_REQUIRED" in _diagnostic_codes(payload)
    assert not (repo / "hooks" / "commit-msg").exists()


def test_governed_hook_adapter_blocks_ungoverned_repo_install(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    other = tmp_path / "other"
    governance_root.mkdir()
    repo.mkdir()
    other.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
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

    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )

    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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
        "manual.pre_tool_use",
        "manual.completion_claim",
    }
    assert payload["summary"]["manual_entries_available"] is True
    assert entrypoints["git.commit-msg"]["integrated"] is True
    assert entrypoints["manual.runtime_adapter"]["available"] is True
    assert entrypoints["manual.runtime_adapter"]["integrated"] is False
    assert entrypoints["manual.pre_tool_use"]["details"]["automatic_trigger"] is False
    assert payload["metadata"]["authorization"] == "none"
    assert payload["diagnostics"] == []


def test_environment_status_blocks_missing_commit_hook(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "rules").mkdir()
    (repo / "rules" / ".gitkeep").write_text("", encoding="utf-8")
    (repo / "skills").mkdir()
    (repo / "skills" / ".gitkeep").write_text("", encoding="utf-8")
    subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )

    completed = subprocess.run(
        [
            sys.executable,
            "code/environment_entry_audit.py",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
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
    assert payload["summary"]["codex_environment_entry_integrated"] is False
    assert "rules.top_level_mechanism" in payload["summary"]["removed_top_level_entrypoints"]
    assert "skills.top_level_mechanism" in payload["summary"]["removed_top_level_entrypoints"]
    assert candidates["git.commit-msg"]["status"] == "integrated"
    assert candidates["runtime.pre_tool_use.auto"]["status"] == "deferred"
    assert candidates["runtime.pre_tool_use.auto"]["manual_fallback"] == "code/pre_tool_use.py"
    assert candidates["rules.top_level_mechanism"]["status"] == "removed_top_level"
    assert candidates["rules.top_level_mechanism"]["decision"] == "removed_top_level"
    assert candidates["skills.top_level_mechanism"]["status"] == "removed_top_level"
    assert candidates["skills.top_level_mechanism"]["decision"] == "removed_top_level"
    assert candidates["codex.repo-instructions"]["status"] == "absent"
    assert payload["decision"]["next_step"] == "defer_auto_runtime_until_real_trigger_exists"
    assert payload["diagnostics"] == []


def test_environment_entry_audit_does_not_treat_agent_file_as_integration(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "AGENTS.md").write_text("# Repo instructions\n", encoding="utf-8")
    subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )

    completed = subprocess.run(
        [
            sys.executable,
            "code/environment_entry_audit.py",
            "--repo",
            str(repo),
            "--ldvh-root",
            str(ROOT),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}
    assert payload["summary"]["integrated_entrypoints"] == ["git.commit-msg"]
    assert candidates["codex.repo-instructions"]["status"] == "available"
    assert candidates["codex.repo-instructions"]["integrated"] is False
    assert candidates["rules.top_level_mechanism"]["status"] == "removed_top_level"
    assert candidates["skills.top_level_mechanism"]["status"] == "removed_top_level"
    assert payload["summary"]["codex_environment_entry_integrated"] is False
    assert "ENV_CODEX_ENTRY_FILES_NOT_INTEGRATED" in _diagnostic_codes(payload)


def test_runtime_completion_claim_requires_verification_evidence() -> None:
    runtime = ldvh_specs.build_runtime_event(ROOT, event="completion_claim")

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_COMPLETION_VERIFICATION_MISSING"


def test_completion_claim_cli_accepts_manual_evidence_json() -> None:
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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
    completed = subprocess.run(
        [
            sys.executable,
            "code/completion_claim.py",
            "--target-path",
            "README.md",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
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

    completed = subprocess.run(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "--payload-json",
            json.dumps(adapter_payload, ensure_ascii=False),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
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
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "pre_tool_use"
    assert payload["dispatch"]["summary"]["integration_scope"] == "manual.pre_tool_use"
    assert payload["dispatch"]["preflight"]["summary"]["target_type"] == "tests"
    assert payload["diagnostics"] == []


def test_runtime_adapter_dispatches_completion_claim_cli_json() -> None:
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
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

    completed = subprocess.run(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "--payload-json",
            json.dumps(adapter_payload, ensure_ascii=False),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["dispatch"] is None
    assert "RUNTIME_ADAPTER_EVENT_UNKNOWN" in _diagnostic_codes(payload)


def test_runtime_adapter_blocks_missing_payload_fields() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "code/runtime_adapter.py",
            "--payload-json",
            json.dumps({"event": "session_start"}, ensure_ascii=False),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["dispatch"] is None
    assert "RUNTIME_ADAPTER_PAYLOAD_FIELD_MISSING" in _diagnostic_codes(payload)


def test_runtime_supports_all_consumption_timings() -> None:
    events = [row["consumption_timing"] for row in ldvh_specs.parse_consumption_timings(ROOT)]
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
        runtime = ldvh_specs.build_runtime_event(ROOT, event=event, **common_kwargs)
        assert runtime["summary"]["event"] == event
        assert runtime["summary"]["has_action_guide"] is True
        assert runtime["receipt"]["canonical_event"] == event
        assert runtime["diagnostics"] == []


def test_specs_validate_cli_runtime_json() -> None:
    completed = subprocess.run(
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
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["metadata"]["read_only"] is True
    assert payload["metadata"]["environment_integrated"] is False
    assert payload["summary"]["status"] == "ok"
    assert payload["receipt"]["receipt_type"] == "runtime_event"
    assert payload["receipt"]["storage"] == "stdout_only"
