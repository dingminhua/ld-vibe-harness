from __future__ import annotations

import json
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


def _replace_in_temp(root: Path, rel_path: str, old: str, new: str = "") -> None:
    path = root / rel_path
    raw = path.read_text(encoding="utf-8")
    assert old in raw
    path.write_text(raw.replace(old, new), encoding="utf-8")


def _diagnostic_codes(result: dict) -> set[str]:
    return {diagnostic["code"] for diagnostic in result["diagnostics"]}


def test_current_specs_validate_without_diagnostics() -> None:
    result = ldvh_specs.build_validation(ROOT)

    assert result["summary"]["status"] == "ok"
    assert result["summary"]["specs"] == 10
    assert result["summary"]["attachments"] == 11
    assert result["summary"]["foundation_spec_contracts"] == 6
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
    assert "runtime_facade_contracts" in contracts["07"]["code_consumption"]
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


def test_git_commit_action_template_is_code_consumable() -> None:
    result = ldvh_specs.build_validation(ROOT)
    rows = {row["结构"]: row["最小要求"] for row in result["git_commit_action_template"]}

    assert set(rows) == {"Context", "Scenario", "Gate", "执行", "验证", "回写", "交还"}
    assert "git status" in rows["Context"]
    assert "diff" in rows["执行"]
    assert "Human Gate" in rows["Gate"]
    assert "09.Att.01" in rows["验证"]
    assert "commit hash" in rows["交还"]


def test_git_commit_action_template_reports_missing_status_context(tmp_path: Path) -> None:
    root = _copy_specs_root(tmp_path)
    _replace_in_temp(
        root,
        "specs/06-行动模板基础规范.md",
        "`git status --short --untracked-files=all`、",
    )

    result = ldvh_specs.build_validation(root)

    assert "GIT_COMMIT_ACTION_TEMPLATE_TERM_MISSING" in _diagnostic_codes(result)
    assert any("git status" in diagnostic["message"] for diagnostic in result["diagnostics"])


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


def test_formal_identity_and_role_sections_are_parseable() -> None:
    objects = {obj.object_id: obj for obj in ldvh_specs.load_formal_objects(ROOT)}

    assert set(objects) == {
        "00",
        "01",
        "01.Att.01",
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


def test_runtime_git_commit_msg_blocks_incomplete_read_plan_consumption() -> None:
    runtime = ldvh_specs.build_runtime_event(
        ROOT,
        event="git_commit_msg",
        target_path="tests/code/test_ldvh_specs_validate.py",
        acknowledged_paths=["specs/00-理念与构成.md"],
    )

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_READ_PLAN_CONSUMED_INCOMPLETE"


def test_runtime_completion_claim_requires_verification_evidence() -> None:
    runtime = ldvh_specs.build_runtime_event(ROOT, event="completion_claim")

    assert runtime["summary"]["status"] == "blocked"
    assert runtime["diagnostics"][0]["code"] == "RUNTIME_COMPLETION_VERIFICATION_MISSING"


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
