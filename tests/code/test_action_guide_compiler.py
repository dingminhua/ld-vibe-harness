from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from action_guide import ActionGuideError, compile_action_guide, load_formatted_source  # noqa: E402


FIXTURES = ROOT / "tests" / "fixtures" / "action_guide"


def test_active_spec_compiles_to_usable_action_guide() -> None:
    source = load_formatted_source(FIXTURES / "active_spec.yaml")

    guide = compile_action_guide(source)

    assert guide["guide_type"] == "action_guide"
    assert guide["result_status"] == "usable"
    assert guide["target"]["id"] == "SPEC-ACTION-GUIDE-BASE"
    assert guide["not_authorized"] == []
    assert [item["order"] for item in guide["read_plan"]] == [1, 2]
    assert guide["source_refs"][0]["path"] == "specs/schemas/formatted-source.schema.yaml"


def test_active_action_member_compiles_after_contract_first_read_plan() -> None:
    source = load_formatted_source(FIXTURES / "active_action_member.yaml")

    guide = compile_action_guide(source)

    assert guide["result_status"] == "usable"
    assert guide["target"]["kind"] == "skill"
    assert guide["read_plan"][0]["target"] == "specs/schemas/action-guide.schema.yaml"
    assert guide["relationships"][0]["type"] == "consumes"


@pytest.mark.parametrize(
    ("fixture_name", "expected_status"),
    [
        ("candidate_action_member.yaml", "candidate"),
        ("deprecated_attachment.yaml", "deprecated"),
    ],
)
def test_limited_sources_are_inspection_only(fixture_name: str, expected_status: str) -> None:
    source = load_formatted_source(FIXTURES / fixture_name)

    guide = compile_action_guide(source)

    assert guide["result_status"] == "limited"
    assert guide["target"]["status"] == expected_status
    assert guide["not_authorized"]
    assert "allowed" not in guide
    assert "approved" not in guide


def test_missing_source_refs_blocks_compilation() -> None:
    source = load_formatted_source(FIXTURES / "invalid_missing_source_refs.yaml")

    with pytest.raises(ActionGuideError, match="source_refs"):
        compile_action_guide(source)


def test_cli_outputs_json_action_guide() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "code/action_guide_cli.py",
            "action-guide",
            "--source",
            str(FIXTURES / "active_spec.yaml"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["guide_type"] == "action_guide"
    assert payload["result_status"] == "usable"
