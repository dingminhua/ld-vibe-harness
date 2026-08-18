"""Focused closed-set tests for the frozen v7 protocol.

These tests fix the v7 protocol (schema_version=ldvh-knowledge-precheck-v7/1)
closed-set shape so that tampering, drift, or structural regression is
mechanically rejected.  They cover the two-phase structure, the per-family
differentiated adoption thresholds, the calibration conditions, and the
policy ceilings shared with the v6 experiment.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from ldvh.testing.knowledge_precheck_v7 import (
    CONDITIONS,
    SCHEMA_VERSION,
    validate_v7_protocol,
)

_PROTOCOL_PATH = Path("docs/metrics/knowledge-precheck-v7/protocol.json")


def _protocol() -> dict:
    return json.loads(_PROTOCOL_PATH.read_text(encoding="utf-8"))


def test_v7_protocol_closed():
    """The frozen v7 protocol must validate without problems."""
    problems = validate_v7_protocol(_protocol())
    assert not problems, f"protocol problems: {problems}"


def test_v7_protocol_schema_version():
    protocol = _protocol()
    assert protocol["schema_version"] == SCHEMA_VERSION


def test_v7_protocol_conditions():
    protocol = _protocol()
    assert protocol["conditions"] == list(CONDITIONS)


def test_v7_protocol_two_phases():
    protocol = _protocol()
    assert set(protocol["phases"]) == {"phase1_study_evaluation", "phase2_adr_pitfall_differentiation"}
    assert set(protocol["phases"]["phase1_study_evaluation"]["metrics"]) == {
        "study_discovery_rate",
        "study_application_rate",
        "study_interference_rate",
    }


def test_v7_protocol_schema_version_tampered():
    tampered = deepcopy(_protocol())
    tampered["schema_version"] = "ldvh-knowledge-precheck-v7/999"
    problems = validate_v7_protocol(tampered)
    assert "schema-version" in problems


def test_v7_protocol_conditions_tampered():
    tampered = deepcopy(_protocol())
    tampered["conditions"] = ["calibration-baseline"]
    problems = validate_v7_protocol(tampered)
    assert "conditions" in problems


def test_v7_protocol_policies_keys_tampered():
    protocol = _protocol()
    tampered = deepcopy(protocol)
    tampered["policies"] = {"calibration-baseline": protocol["policies"]["calibration-baseline"]}
    problems = validate_v7_protocol(tampered)
    assert "policies" in problems


def test_v7_protocol_policy_hash_tampered():
    tampered = deepcopy(_protocol())
    content = tampered["policies"]["calibration-enhanced"]["content"]
    tampered["policies"]["calibration-enhanced"]["content"] = content + "\n"
    problems = validate_v7_protocol(tampered)
    assert any(p.startswith("policy-") for p in problems)


def test_v7_protocol_ceilings_tampered():
    tampered = deepcopy(_protocol())
    tampered["ceilings"]["maximum_member_launches"] = 999
    problems = validate_v7_protocol(tampered)
    assert "ceilings" in problems


def test_v7_protocol_task_count():
    protocol = _protocol()
    assert len(protocol["tasks"]) == 18
    pair_ids = [task["pair_id"] for task in protocol["tasks"]]
    assert len(pair_ids) == len(set(pair_ids))


def test_v7_protocol_phase1_thresholds_present():
    protocol = _protocol()
    phase1 = protocol["phases"]["phase1_study_evaluation"]["metrics"]
    assert ">= 4/6" in phase1["study_discovery_rate"]
    assert ">= 3" in phase1["study_application_rate"]
    assert "<= 1" in phase1["study_interference_rate"]


def test_v7_protocol_per_family_thresholds_present():
    protocol = _protocol()
    thresholds = protocol["adoption_thresholds"]
    assert thresholds["adr_missed_detection"] == "<= 2 (absolute count)"
    assert thresholds["adr_correct_activation"] == ">= 3/3 (v5 activation-enhanced archived on ADR applicable)"
    assert thresholds["pitfall_trigger_correct_per_family"] == ">= 4/6 (v6 baseline per-family archived)"
    assert thresholds["pitfall_unnecessary_f2_per_family"] == "<= 2 (v6 baseline per-family archived)"


def test_v7_protocol_overall_thresholds_present():
    protocol = _protocol()
    thresholds = protocol["adoption_thresholds"]
    assert thresholds["trigger_correct"] == "enhanced >= 12 (overall; v6 baseline archived = 12/18)"
    assert thresholds["unnecessary_f2"] == "enhanced <= 6 (overall; v6 baseline archived = 6)"
    assert thresholds["correct_activation_rate"] == "enhanced >= 6/9 (v6 baseline archived = 6/9)"
