"""Focused tests for the v7 trial surface and experiment ceilings.

These tests pin the v7 trial CLI compile surface, the experiment ceilings
shared with v6 (42 launches / 42 scorer / 600s / 6h / 3 replacements / 21
attempts / 18 retained pairs), and the technical-exclusion closed set so that
drift in the running contract is mechanically rejected.
"""

from __future__ import annotations

from pathlib import Path

from ldvh.testing.knowledge_precheck_v7 import (
    MAX_MEMBER_LAUNCHES,
    MAX_PAIR_ATTEMPTS,
    MAX_REPLACEMENTS,
    MAX_SCORER_CONTEXTS,
    RETAINED_PAIR_TARGET,
    RUN_TIMEOUT_SECONDS,
    TECHNICAL_EXCLUSION_CODES,
    TOTAL_TIMEOUT_SECONDS,
    read_frozen_protocol,
)
from ldvh.testing.knowledge_precheck_v7_trial import (
    V7TrialError,
    compile_trigger_evidence,
    evaluate_all_triggers,
    judge_trigger_metrics,
)

_PROTOCOL_PATH = Path("docs/metrics/knowledge-precheck-v7/protocol.json")
_SNAPSHOT_PATH = Path("docs/metrics/knowledge-precheck-v7/source-snapshot.json")


def _protocol() -> dict:
    return read_frozen_protocol(_PROTOCOL_PATH)


# --- Ceilings ----------------------------------------------------------------


def test_v7_ledger_ceilings():
    """v7 ledger ceilings must match the frozen constants (shared with v6)."""
    protocol = _protocol()
    ceilings = protocol["ceilings"]
    assert ceilings["maximum_member_launches"] == MAX_MEMBER_LAUNCHES == 42
    assert ceilings["maximum_scorer_contexts"] == MAX_SCORER_CONTEXTS == 42
    assert ceilings["run_timeout_seconds"] == RUN_TIMEOUT_SECONDS == 600
    assert ceilings["total_timeout_seconds"] == TOTAL_TIMEOUT_SECONDS == 21600  # 6h
    assert ceilings["maximum_replacements"] == MAX_REPLACEMENTS == 3
    assert ceilings["maximum_pair_attempts"] == MAX_PAIR_ATTEMPTS == 21
    assert ceilings["retained_pair_target"] == RETAINED_PAIR_TARGET == 18
    assert ceilings["same_arm_retries"] == 0


def test_v7_technical_exclusion_closed_set():
    """The technical-exclusion closed set must be present and non-empty."""
    assert len(TECHNICAL_EXCLUSION_CODES) >= 1
    assert "missing_structured_output" in TECHNICAL_EXCLUSION_CODES
    assert "cross_condition_leakage" in TECHNICAL_EXCLUSION_CODES


# --- Trial surface -----------------------------------------------------------


def test_v7_trial_evaluate_all_triggers(tmp_path: Path) -> None:
    """evaluate_all_triggers covers every frozen task with a closed trace."""
    protocol = _protocol()
    traces = evaluate_all_triggers(protocol, "calibration-enhanced")
    assert len(traces) == RETAINED_PAIR_TARGET
    pair_ids = {task["pair_id"] for task in protocol["tasks"]}
    assert {trace["pair_id"] for trace in traces} == pair_ids
    for trace in traces:
        assert set(trace) == {
            "schema_version",
            "attempt_id",
            "pair_id",
            "condition",
            "family",
            "triggered",
            "trigger_family",
            "positive_condition_codes",
            "veto_condition_codes",
        }


def test_v7_trial_judge_metrics_shape(tmp_path: Path) -> None:
    protocol = _protocol()
    traces = evaluate_all_triggers(protocol, "calibration-enhanced")
    metrics = judge_trigger_metrics(traces, protocol)
    assert set(metrics) == {"overall", "per_family"}
    assert set(metrics["overall"]) == {"trigger_correct", "unnecessary_f2", "missed_detection"}
    assert set(metrics["per_family"]) == {"adr", "pitfall", "study"}


def test_v7_trial_compile_trigger_evidence(tmp_path: Path) -> None:
    """compile-trigger-evidence produces a non-empty bundle without replacing."""
    out = tmp_path / "evidence"
    bundle = compile_trigger_evidence(_PROTOCOL_PATH, _SNAPSHOT_PATH, out)
    assert bundle["schema_version"] == "ldvh-knowledge-precheck-v7-evidence/1"
    assert bundle["retained_pairs"] == RETAINED_PAIR_TARGET
    assert set(bundle["conditions"]) == {"calibration-baseline", "calibration-enhanced"}
    assert (out / "trigger-evidence.json").exists()


def test_v7_trial_compile_refuses_replace(tmp_path: Path) -> None:
    out = tmp_path / "evidence"
    compile_trigger_evidence(_PROTOCOL_PATH, _SNAPSHOT_PATH, out)
    try:
        compile_trigger_evidence(_PROTOCOL_PATH, _SNAPSHOT_PATH, out)
    except V7TrialError:
        pass
    else:
        raise AssertionError("compile must refuse to replace existing evidence")
