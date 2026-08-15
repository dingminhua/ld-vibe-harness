from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from ldvh.testing.prepare_update_replay import (
    BRANCHES,
    CALIBER,
    FACT_TYPES,
    RETAINED_RECORD_FIELDS,
    STRATEGIES,
    TASK_COUNT,
    canonical_sha256,
    record_problems,
    regenerate,
    render_report,
    run_replay,
    validate_protocol,
)

ROOT = Path(__file__).parents[3]
PROTOCOL_PATH = ROOT / "docs/metrics/prepare-update-protocol-v1.json"
RESULTS_PATH = ROOT / "docs/metrics/prepare-update-results-v1.json"
REPORT_PATH = ROOT / "docs/metrics/prepare-update-report-v1.md"


def _protocol() -> dict[str, object]:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, member in value.items():
            keys.add(str(key))
            keys.update(_all_keys(member))
    elif isinstance(value, list):
        for member in value:
            keys.update(_all_keys(member))
    return keys


def test_frozen_protocol_has_exact_twelve_task_coverage_and_hash() -> None:
    protocol = _protocol()
    tasks = protocol["tasks"]

    assert validate_protocol(protocol) == ()
    assert protocol["caliber"] == CALIBER
    assert len(tasks) == TASK_COUNT
    assert {task["fact_type_key"] for task in tasks} == FACT_TYPES
    assert {task["branch"] for task in tasks} == BRANCHES
    assert protocol["task_package_sha256"] == canonical_sha256(tasks)


def test_protocol_changes_fail_closed_without_versioned_restart() -> None:
    protocol = _protocol()
    protocol["tasks"][0]["branch"] = "no-op"

    assert "task-package-hash" in validate_protocol(protocol)


def test_replay_records_are_balanced_private_and_mechanically_exact() -> None:
    protocol = _protocol()
    results = run_replay(protocol)
    records = results["records"]
    summary = results["summary"]

    assert record_problems(records, protocol) == ()
    assert len(records) == TASK_COUNT * len(STRATEGIES)
    assert all(set(record) == RETAINED_RECORD_FIELDS for record in records)
    assert summary["all_expected_outcomes_met"] is True
    assert summary["all_failure_branches_zero_write"] is True
    assert summary["minimal_known_contract_helper_calls"] == {
        "baseline": 2.0,
        "prepare": 2.0,
        "difference": 0.0,
        "interpretation": "parity-only",
    }
    assert summary["cold_discovery_helper_calls"] == {
        "baseline": 3.0,
        "prepare": 2.0,
        "difference": -1.0,
        "interpretation": "one-mechanical-call-reduction",
    }
    assert all(record["shell_invocations"] == 0 for record in records)
    assert all(record["host_receipt"] == "unavailable" for record in records)


def test_record_privacy_and_expected_outcome_tampering_fail_closed() -> None:
    protocol = _protocol()
    records = run_replay(protocol)["records"]
    leaked = deepcopy(records)
    leaked[0]["signature"] = {"product_name": "must-not-retain"}
    failed = deepcopy(records)
    failed[0]["expected_outcome_met"] = False

    assert "record-fields" in record_problems(leaked, protocol)
    assert "record-privacy" in record_problems(leaked, protocol)
    assert "unexpected-outcome" in record_problems(failed, protocol)


def test_committed_results_and_report_are_exactly_regenerable() -> None:
    protocol = _protocol()
    expected_results, expected_report = regenerate(protocol)
    stored_results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    stored_report = REPORT_PATH.read_text(encoding="utf-8")

    assert stored_results == expected_results
    assert stored_report == expected_report
    assert render_report(stored_results) == stored_report


def test_artifacts_retain_no_denied_payload_classes() -> None:
    protocol = _protocol()
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    denied = set(protocol["privacy"]["denylist"])

    assert not (_all_keys(results) & denied)
    assert all(
        marker not in RESULTS_PATH.read_text(encoding="utf-8")
        for marker in ("/Users/", "session-", "BEGIN PRIVATE", "api_key")
    )
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "parity only" in report
    assert "one mechanical Helper call fewer" in report
    assert "fresh temporary Git repository" in report
    assert "does not exercise a linked worktree" in report
    assert "strategy-specific named workflow steps" in report
    assert "not a normalized unit of work or cognitive effort" in report
    assert "not real-task or representative evidence" in report
    assert "supports no causal or broad service-quality conclusion" in report
