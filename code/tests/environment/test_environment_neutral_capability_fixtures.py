from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).with_name("fixtures") / "environment_neutral_capability_scenarios.json"
ACCEPTED_ABSENCE_AUTHORITIES = {"authoritative_material", "range_matched_observation"}


def _scenarios() -> list[dict[str, Any]]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert all(isinstance(item, dict) for item in payload)
    return payload


def _capability_state(evidence: dict[str, Any]) -> str:
    """Test only the deterministic boundary already defined by specification 09 §5.3."""

    if (
        evidence.get("authority_kind") in ACCEPTED_ABSENCE_AUTHORITIES
        and evidence.get("scope_matches_target") is True
        and evidence.get("affirmative_absence") is True
    ):
        return "unsupported"
    return "unverified"


def test_simulated_hook_success_proves_only_the_fixture_call() -> None:
    scenario = next(item for item in _scenarios() if item["scenario_kind"] == "simulated_hook_success")
    evidence = scenario["evidence"]

    fixture_call = "success" if all(
        (
            evidence["automatic_trigger_observed"],
            evidence["required_input_observed"],
            evidence["feedback_observed"],
            evidence["helper_outcome"] == "ok",
        )
    ) else "failed"

    assert scenario["maps_to_real_environment"] is False
    assert evidence["real_environment_event"] is False
    assert fixture_call == scenario["expected"]["fixture_call"] == "success"
    assert scenario["expected"]["complete_integration"] == "unverified"


def test_unknown_capability_evidence_stays_unverified() -> None:
    scenario = next(item for item in _scenarios() if item["scenario_id"] == "synthetic-unknown-capability")

    assert scenario["maps_to_real_environment"] is False
    assert _capability_state(scenario["evidence"]) == scenario["expected"]["capability_state"] == "unverified"


def test_affirmative_scope_matched_absence_is_classified_unsupported() -> None:
    scenario = next(item for item in _scenarios() if item["scenario_id"] == "synthetic-confirmed-no-capability")

    assert scenario["maps_to_real_environment"] is False
    assert _capability_state(scenario["evidence"]) == scenario["expected"]["capability_state"] == "unsupported"


@pytest.mark.parametrize("missing_basis", ("authority_kind", "scope_matches_target", "affirmative_absence"))
def test_confirmed_no_capability_requires_every_affirmative_basis(missing_basis: str) -> None:
    scenario = next(item for item in _scenarios() if item["scenario_id"] == "synthetic-confirmed-no-capability")
    evidence = copy.deepcopy(scenario["evidence"])
    evidence[missing_basis] = None if missing_basis == "authority_kind" else False

    assert _capability_state(evidence) == "unverified"


def test_fixtures_never_identify_a_real_ai_development_environment() -> None:
    scenarios = _scenarios()

    assert {item["scenario_id"] for item in scenarios} == {
        "synthetic-hook-success",
        "synthetic-unknown-capability",
        "synthetic-confirmed-no-capability",
    }
    assert all(item["maps_to_real_environment"] is False for item in scenarios)
