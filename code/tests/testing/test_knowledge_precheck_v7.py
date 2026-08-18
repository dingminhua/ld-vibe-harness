"""Focused tests for the v7 per-family differentiated trigger gateway.

These tests pin the v7 gateway contract: Study is always a fixed no-trigger
mechanism; ADR applies signal + light exclusion (A4 pure-fixture / A5
historical-ADR excluded, A6 f2-no-f3 stays triggered); Pitfall applies
signal + symptom/risk anchor (observed symptom or risk-execution triggers,
pure-hypothetical P5 and explicit-negation P4 do not).  The trigger response
shape is closed and any drift / tampering is rejected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.testing.knowledge_precheck_v7 import (
    CONDITIONS,
    KnowledgePrecheckV7Error,
    evaluate_v7_trigger,
    read_frozen_protocol,
    validate_v7_trigger_response,
)
from ldvh.testing.knowledge_precheck_v7_trial import (
    evaluate_all_triggers,
    judge_trigger_metrics,
)

_PROTOCOL_PATH = Path("docs/metrics/knowledge-precheck-v7/protocol.json")


def _protocol() -> dict:
    return read_frozen_protocol(_PROTOCOL_PATH)


def _task_by_id(protocol: dict, pair_id: str) -> dict:
    return next(task for task in protocol["tasks"] if task["pair_id"] == pair_id)


# --- Study fixed no-trigger mechanism ---------------------------------------


def test_study_always_no_trigger():
    """Study never triggers in either condition, regardless of task text."""
    protocol = _protocol()
    for cond in CONDITIONS:
        for task in protocol["tasks"]:
            if task["family"] != "study":
                continue
            response = evaluate_v7_trigger("study", task["user_task"], cond)
            assert response["triggered"] is False
            assert response["trigger_family"] is None


def test_study_trigger_trace_binds():
    protocol = _protocol()
    task = _task_by_id(protocol, "S1")
    response = evaluate_v7_trigger("study", task["user_task"], "calibration-enhanced")
    validate_v7_trigger_response(response, "study")


# --- ADR signal + light exclusion -------------------------------------------


def test_adr_a4_pure_fixture_light_excluded():
    """A4 (pure fixture deviation, no rule gap) is light-excluded in enhanced."""
    protocol = _protocol()
    task = _task_by_id(protocol, "A4")
    response = evaluate_v7_trigger("adr", task["user_task"], "calibration-enhanced")
    assert response["triggered"] is False
    assert "pure-fixture-deviation" in response["veto_condition_codes"]


def test_adr_a5_historical_not_authority_excluded():
    """A5 (historical ADR not current contract authority) is excluded."""
    protocol = _protocol()
    task = _task_by_id(protocol, "A5")
    response = evaluate_v7_trigger("adr", task["user_task"], "calibration-enhanced")
    assert response["triggered"] is False


def test_adr_a6_f2_no_f3_stays_triggered():
    """A6 (future possible interface change, no concrete decision) stays
    triggered so the F2 index check is preserved (f2-no-f3 fix)."""
    protocol = _protocol()
    task = _task_by_id(protocol, "A6")
    response = evaluate_v7_trigger("adr", task["user_task"], "calibration-enhanced")
    assert response["triggered"] is True
    assert response["veto_condition_codes"] == []


def test_adr_applicable_triggered():
    """ADR applicable tasks (A1) remain triggered under the enhanced boundary."""
    protocol = _protocol()
    task = _task_by_id(protocol, "A1")
    response = evaluate_v7_trigger("adr", task["user_task"], "calibration-enhanced")
    assert response["triggered"] is True


# --- Pitfall signal + symptom/risk anchor -----------------------------------


def test_pitfall_p1_observed_symptom_triggered():
    protocol = _protocol()
    task = _task_by_id(protocol, "P1")
    response = evaluate_v7_trigger("pitfall", task["user_task"], "calibration-enhanced")
    assert response["triggered"] is True
    assert "observed-symptom" in response["positive_condition_codes"]


def test_pitfall_p4_explicit_negation_not_triggered():
    """P4 (explicit 'no ... symptom' with only contract/test checking) does
    not trigger under the enhanced boundary."""
    protocol = _protocol()
    task = _task_by_id(protocol, "P4")
    response = evaluate_v7_trigger("pitfall", task["user_task"], "calibration-enhanced")
    assert response["triggered"] is False


def test_pitfall_p5_hypothetical_not_triggered():
    """P5 (pure hypothetical future adoption, no current executable step)
    does not trigger."""
    protocol = _protocol()
    task = _task_by_id(protocol, "P5")
    response = evaluate_v7_trigger("pitfall", task["user_task"], "calibration-enhanced")
    assert response["triggered"] is False


# --- response shape / drift rejection ---------------------------------------


def test_trigger_response_closed_shape():
    response = evaluate_v7_trigger("adr", "任务提及规则决策", "calibration-enhanced")
    assert set(response) == {
        "triggered",
        "trigger_family",
        "positive_condition_codes",
        "veto_condition_codes",
    }


def test_tampered_triggered_field_rejected():
    response = evaluate_v7_trigger("adr", "任务提及规则决策", "calibration-enhanced")
    response["triggered"] = "yes"  # wrong type
    with pytest.raises(KnowledgePrecheckV7Error):
        validate_v7_trigger_response(response, "adr")


def test_trigger_family_inconsistency_rejected():
    response = evaluate_v7_trigger("adr", "任务提及规则决策", "calibration-enhanced")
    response["trigger_family"] = "pitfall"
    with pytest.raises(KnowledgePrecheckV7Error):
        validate_v7_trigger_response(response, "adr")


def test_unknown_family_rejected():
    with pytest.raises(KnowledgePrecheckV7Error):
        evaluate_v7_trigger("workcase", "x", "calibration-baseline")


def test_unknown_condition_rejected():
    with pytest.raises(KnowledgePrecheckV7Error):
        evaluate_v7_trigger("adr", "x", "calibration-v7")


# --- deterministic reference metrics (gateway skeleton) ---------------------


def test_reference_metrics_overall_enhanced_reaches_thresholds():
    """The deterministic gateway skeleton must reach the frozen overall
    thresholds on the enhanced arm: trigger_correct >= 12, unnecessary_f2
    <= 6.  (Real member/scorer subagent runs remain the authoritative source
    for the final report; this pins the mechanism skeleton, not the report.)"""
    protocol = _protocol()
    traces = evaluate_all_triggers(protocol, "calibration-enhanced")
    metrics = judge_trigger_metrics(traces, protocol)
    overall = metrics["overall"]
    correct, total = overall["trigger_correct"].split("/")
    assert int(correct) >= 12 and int(total) == 18
    assert overall["unnecessary_f2"] <= 6


def test_reference_metrics_study_never_triggered():
    protocol = _protocol()
    for cond in CONDITIONS:
        traces = evaluate_all_triggers(protocol, cond)
        for trace in traces:
            if trace["family"] == "study":
                assert trace["triggered"] is False
