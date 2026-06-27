from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from migration_gate import classify_candidate, load_candidate  # noqa: E402


FIXTURES = ROOT / "fixtures"


def classify(name: str) -> dict:
    return classify_candidate(load_candidate(FIXTURES / name))


def test_parent_spec_candidate_migrates_to_specs() -> None:
    decision = classify("parent_spec_candidate.yaml")

    assert decision["decision"] == "migrate"
    assert decision["role"] == "parent_spec"
    assert decision["target_path"] == "specs/code-determinism.yaml"


def test_child_spec_requires_parent_and_migrates() -> None:
    decision = classify("child_spec_candidate.yaml")

    assert decision["decision"] == "migrate"
    assert decision["target_path"] == "specs/actions/git-commit.yaml"


def test_schema_and_fixture_go_to_expected_areas() -> None:
    schema_decision = classify("schema_candidate.yaml")
    fixture_decision = classify("fixture_candidate.yaml")

    assert schema_decision["decision"] == "migrate"
    assert schema_decision["target_path"].startswith("specs/schemas/")
    assert fixture_decision["decision"] == "migrate"
    assert fixture_decision["target_path"].startswith("tests/fixtures/")


def test_derived_checklist_is_not_migrated() -> None:
    decision = classify("derived_checklist_candidate.yaml")

    assert decision["decision"] == "do_not_migrate"
    assert decision["next_action"] == "encode_as_schema_code_or_test"


def test_runtime_strategy_is_deferred_for_human_confirmation() -> None:
    decision = classify("runtime_strategy_candidate.yaml")

    assert decision["decision"] == "defer"
    assert "runtime" in decision["reason"]


def test_missing_authority_is_invalid() -> None:
    decision = classify("invalid_missing_authority.yaml")

    assert decision["decision"] == "invalid"
    assert "missing_or_empty:authority_source" in decision["reason"]


def test_cli_outputs_json_decision() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "migration_gate_cli.py"),
            str(FIXTURES / "parent_spec_candidate.yaml"),
        ],
        cwd=ROOT.parent,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["decision"] == "migrate"
