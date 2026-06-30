from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import ldvh_specs


ROOT = Path(__file__).resolve().parents[2]


def test_current_specs_validate_without_diagnostics() -> None:
    result = ldvh_specs.build_validation(ROOT)

    assert result["summary"]["status"] == "ok"
    assert result["summary"]["specs"] == 10
    assert result["summary"]["attachments"] == 8
    assert result["diagnostics"] == []


def test_formal_identity_and_role_sections_are_parseable() -> None:
    objects = {obj.object_id: obj for obj in ldvh_specs.load_formal_objects(ROOT)}

    assert set(objects) == {
        "00",
        "01",
        "01.Att.01",
        "01.Att.06",
        "02",
        "03",
        "04",
        "04.Att.01",
        "04.Att.02",
        "04.Att.03",
        "04.Att.04",
        "04.Att.05",
        "04.Att.06",
        "05",
        "06",
        "07",
        "08",
        "09",
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
    assert "不是最终事实源" in runtime["receipt"]["boundary"]
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
