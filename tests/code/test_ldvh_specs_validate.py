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
    assert result["summary"]["specs"] == 4
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
        "02.Att.01",
        "02.Att.02",
        "02.Att.03",
        "02.Att.04",
        "02.Att.05",
        "02.Att.06",
        "03",
    }
    assert objects["01"].metadata["role_sections"]["rule_body"] == [
        "5. 内部保障",
        "6. 外部衔接",
        "7. 行动指南",
    ]
    assert "assurance_requirements" in objects["01"].metadata["code_consumption"]
    assert "ai_behavior_assurance_requirements" in objects["03"].metadata["code_consumption"]


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
