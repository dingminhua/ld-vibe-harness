from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from ldvh.testing.representative_task_retrial import (
    EXPECTED_SCHEDULE_COUNT,
    RepresentativeRetrialError,
    assert_current_fact_fingerprint_unchanged,
    assess_runner_preflight,
    build_results,
    create_isolated_trial_root,
    guard_state_changing_target,
    load_protocol,
    make_session_record,
    protocol_sha256,
    render_report,
    task_package_hash,
    validate_attempt_ledger,
    validate_protocol,
    validate_results,
    write_new_json_artifact,
    write_new_text_artifact,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_PATH = PROJECT_ROOT / "docs/metrics/representative-task-retrial-protocol-v1.json"
PROTOCOL_V2_PATH = PROJECT_ROOT / "docs/metrics/representative-task-retrial-protocol-v2.json"
PROTOCOL_SHA256 = "c597455d20cbb894f42c2571959ddc23ad375b6cd7360ba697d858f158b3db37"
PROTOCOL_V2_SHA256 = "42a8e371b652d89938021084afc96ed232adbc6f47a6f1708e1251e7791c207d"


def _protocol() -> dict[str, object]:
    return load_protocol(PROTOCOL_PATH)


def _protocol_v2() -> dict[str, object]:
    return load_protocol(PROTOCOL_V2_PATH)


def _observation(**changes: object) -> dict[str, object]:
    observation: dict[str, object] = {
        "provider": "provider-v1",
        "model": "model-v1",
        "runner_identity": "runner-v1",
        "tool_entry": "collaboration.spawn_agent",
        "entrypoint": "Cindy collaboration spawn_agent with inherited configuration",
        "permission_profile": "inherited-session-profile-v1",
        "prompt_layout": "frozen-task-envelope-v1",
        "identity_source": "harness-request-header",
    }
    observation.update(changes)
    return observation


def _event_lines(provider: str = "provider-v1", model: str = "model-v1") -> list[str]:
    events = [
        {
            "type": "request/header",
            "data": {
                "header": {"config": {"provider": provider, "model": model}},
                "reason": "initial",
            },
            "seq": 1,
        },
        {"type": "turn/start", "data": {"turn": 1}},
        {"type": "step/start", "data": {"turn": 1, "step": 1}},
        {
            "type": "tool/call",
            "data": {"name": "ldvh", "turn": 1, "step": 1, "callId": "call-1"},
        },
        {"type": "tool/result", "data": {"content": "opaque"}},
        {"type": "step/end", "data": {"turn": 1, "step": 1}},
        {"type": "turn/end", "data": {"turn": 1}},
    ]
    return [json.dumps(event, ensure_ascii=False) for event in events]


def _metrics(*, burden: bool = True) -> dict[str, object]:
    return {
        "helper_call_count": 2 if burden else 1,
        "gold_call_count": 1,
        "helper_request_chars": 800 if burden else 300,
        "gold_request_chars": 300,
        "helper_request_bytes": 900,
        "helper_response_bytes": 450,
        "invalid_request_count": 0,
        "first_legal_action": True,
        "extra_rule_reads": 0,
        "repair_count": 0,
        "fallback_count": 0,
        "duration_ms": 2500,
        "extra_duration_ms": 500 if burden else 0,
        "duration_unavailable_reason": None,
        "cache_observation": "miss",
        "cache_unavailable_reason": None,
    }


def _attempt_entry(
    protocol: dict[str, object],
    *,
    attempt_index: int = 1,
    status: str = "completed",
    exclusion_reason: str = "model_identity_unavailable",
    facts_after: str | None = None,
    replacement_for_attempt_index: int | None = None,
) -> dict[str, object]:
    schedule = protocol["schedule"][attempt_index - 1]  # type: ignore[index]
    frame = next(
        frame
        for frame in protocol["task_frames"]  # type: ignore[union-attr]
        if frame["task_id"] == schedule["task_id"]
    )
    facts_before = "a" * 64
    return {
        "attempt_index": attempt_index,
        "scheduled_session_slot": attempt_index,
        "task_id": schedule["task_id"],
        "replicate": schedule["replicate"],
        "family": frame["family"],
        "status": status,
        "target_reached": status == "completed",
        "started_at": "2026-08-16T15:40:00Z",
        "completed_at": "2026-08-16T15:40:01Z",
        "retained": False,
        "exclusion_reason": exclusion_reason,
        "evidence_unavailable": ["fixed_model_identity", "raw_session_trace"],
        "runner_receipt_sha256": "b" * 64,
        "facts_fingerprint_before": facts_before,
        "facts_fingerprint_after": facts_before if facts_after is None else facts_after,
        "state_change_guard_passed": True,
        "replacement_for_attempt_index": replacement_for_attempt_index,
    }


def _record(
    protocol: dict[str, object],
    *,
    task_id: str,
    replicate: int,
    attempt_index: int,
    burden: bool = True,
    observed_carrier_fingerprint: str | None = None,
) -> dict[str, object]:
    preflight = assess_runner_preflight(protocol, _observation())
    frame = next(frame for frame in protocol["task_frames"] if frame["task_id"] == task_id)  # type: ignore[index,union-attr]
    fixture_identity = f"fixture:{task_id}:{replicate}"
    return make_session_record(
        protocol=protocol,
        preflight=preflight,
        trial_id=f"trial-{attempt_index:02d}",
        attempt_index=attempt_index,
        task_id=task_id,
        replicate=replicate,
        task_package_sha256=task_package_hash(frame),
        expected_fixture_identity=fixture_identity,
        actual_fixture_identity=fixture_identity,
        observed_carrier_fingerprint=(
            preflight.carrier_fingerprint
            if observed_carrier_fingerprint is None
            else observed_carrier_fingerprint
        ),
        event_lines=_event_lines(),
        metrics=_metrics(burden=burden),
    )


def test_frozen_protocol_is_closed_and_hash_bound() -> None:
    protocol = _protocol()
    assert protocol_sha256(protocol) == PROTOCOL_SHA256
    assert len(protocol["task_frames"]) == 18  # type: ignore[arg-type]
    assert len(protocol["schedule"]) == EXPECTED_SCHEDULE_COUNT  # type: ignore[arg-type]

    protocol_v2 = _protocol_v2()
    assert protocol_sha256(protocol_v2) == PROTOCOL_V2_SHA256
    assert protocol_v2["runner_binding"]["controller_declared_product_name"] == "Cindy"  # type: ignore[index]


@pytest.mark.parametrize("mutation", ["missing_frame", "read_state_change"])
def test_protocol_rejects_sample_or_legality_drift(mutation: str) -> None:
    protocol = _protocol()
    if mutation == "missing_frame":
        protocol["task_frames"].pop()  # type: ignore[union-attr]
    else:
        read_frame = next(
            frame for frame in protocol["task_frames"] if frame["family"] == "read"  # type: ignore[index,union-attr]
        )
        read_frame["gold_legal_trace"][0]["state_changing"] = True
    with pytest.raises(RepresentativeRetrialError):
        validate_protocol(protocol)


def test_runner_preflight_fails_closed_without_auditable_model_identity() -> None:
    preflight = assess_runner_preflight(
        _protocol(),
        _observation(provider=None, model=None, identity_source=None),
    )
    assert preflight.status == "not_comparable"
    assert preflight.reasons[0] == "runner_model_identity_unavailable"
    assert preflight.carrier_fingerprint is None


def test_runner_preflight_binds_complete_carrier() -> None:
    first = assess_runner_preflight(_protocol(), _observation())
    second = assess_runner_preflight(_protocol(), _observation())
    assert first.status == "comparable"
    assert first.reasons == ()
    assert first.carrier_fingerprint == second.carrier_fingerprint
    assert first.carrier_fingerprint is not None


def test_v2_runner_preflight_allows_product_bound_when_only_model_is_unavailable() -> None:
    preflight = assess_runner_preflight(
        _protocol_v2(),
        _observation(provider=None, model=None, identity_source=None),
    )
    assert preflight.status == "product_bound"
    assert preflight.identity_scope == "product_bound"
    assert preflight.product_name == "Cindy"
    assert preflight.reasons == ()
    assert "fixed_model_comparability_unavailable" in preflight.disclosures
    assert preflight.carrier_fingerprint is not None


def test_v2_runner_preflight_stops_only_when_product_and_model_are_both_unavailable() -> None:
    protocol = _protocol_v2()
    protocol["runner_binding"]["controller_declared_product_name"] = None  # type: ignore[index]
    protocol["runner_binding"]["controller_declared_model_name"] = None  # type: ignore[index]
    preflight = assess_runner_preflight(
        protocol,
        _observation(provider=None, model=None, identity_source=None),
    )
    assert preflight.status == "not_comparable"
    assert preflight.reasons[0] == "controller_identity_unavailable"
    assert preflight.carrier_fingerprint is None


def test_isolated_root_and_current_fact_guards_fail_closed(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    trial_root = create_isolated_trial_root(repository_root=repository)
    assert repository not in trial_root.root.parents
    allowed = trial_root.root / "fixture" / "fact.yaml"
    guard_state_changing_target(
        repository_root=repository,
        trial_root=trial_root,
        target=allowed,
    )
    with pytest.raises(RepresentativeRetrialError, match="inside the repository"):
        guard_state_changing_target(
            repository_root=repository,
            trial_root=trial_root,
            target=repository / "ldvh-base/fact.yaml",
        )
    assert_current_fact_fingerprint_unchanged(before="a" * 64, after="a" * 64)
    with pytest.raises(RepresentativeRetrialError, match="fingerprint changed"):
        assert_current_fact_fingerprint_unchanged(before="a" * 64, after="b" * 64)


def test_session_record_is_comparable_privacy_safe_and_scored() -> None:
    protocol = _protocol()
    task_id = protocol["schedule"][0]["task_id"]  # type: ignore[index]
    record = _record(protocol, task_id=task_id, replicate=1, attempt_index=1)
    assert record["retained"] is True
    assert record["comparability"] == "comparable"
    assert record["burden_points"] == 3.25
    rendered = json.dumps(record, ensure_ascii=False)
    assert "event_lines" not in record
    assert "opaque" not in rendered


def test_session_record_excludes_runner_drift() -> None:
    protocol = _protocol()
    task_id = protocol["schedule"][0]["task_id"]  # type: ignore[index]
    record = _record(
        protocol,
        task_id=task_id,
        replicate=1,
        attempt_index=1,
        observed_carrier_fingerprint="f" * 64,
    )
    assert record["retained"] is False
    assert record["exclusion_reason"] == "runner_identity_drift"


def test_failed_preflight_produces_zero_attempt_not_comparable_results() -> None:
    protocol = _protocol()
    preflight = assess_runner_preflight(
        protocol,
        _observation(provider=None, model=None, identity_source=None),
    )
    results = build_results(
        protocol=protocol,
        preflight=preflight,
        records=[],
        generated_at="2026-08-16T15:00:00Z",
    )
    validate_results(results, protocol)
    assert results["result"]["batch_status"] == "not_comparable"
    assert results["result"]["attempt_count"] == 0
    assert all(
        item["status"] == "not_comparable"
        for item in results["result"]["family_results"]
    )
    report = render_report(
        protocol=protocol,
        results=results,
        results_file_sha256="1" * 64,
    )
    assert "no trial was attempted" in report
    assert PROTOCOL_SHA256 in report


def test_v2_product_bound_attempts_are_descriptive_and_never_scored() -> None:
    protocol = _protocol_v2()
    preflight = assess_runner_preflight(
        protocol,
        _observation(provider=None, model=None, identity_source=None),
    )
    ledger = [_attempt_entry(protocol)]
    results = build_results(
        protocol=protocol,
        preflight=preflight,
        records=[],
        attempt_ledger=ledger,
        generated_at="2026-08-16T15:41:00Z",
    )
    validate_results(results, protocol)
    assert results["result"]["batch_status"] == "model_unverified"
    assert results["result"]["attempt_count"] == 1
    assert results["result"]["retained_session_count"] == 0
    assert results["result"]["unavailable_semantics"]["go_no_go"] == "prohibited"
    for family in results["result"]["family_results"]:
        assert family["status"] == "model_unverified"
        assert family["positive_frames"] is None
        assert family["median_frame_burden_points"] is None
        assert family["bootstrap_median_ci_95"] is None
    report = render_report(
        protocol=protocol,
        results=results,
        results_file_sha256="1" * 64,
    )
    assert "no fixed-model comparison" in report
    assert "no trial was attempted" not in report
    assert "## Attempt ledger" in report
    assert "| 1 | 1 | read-01 | read | completed | True | False |" in report
    assert "model_identity_unavailable" in report
    assert "fixed_model_identity" in report


def test_v2_attempt_ledger_rejects_fact_drift_and_invalid_replacement() -> None:
    protocol = _protocol_v2()
    with pytest.raises(RepresentativeRetrialError, match="fingerprint changed"):
        validate_attempt_ledger([_attempt_entry(protocol, facts_after="c" * 64)], protocol)

    invalid_replacement = _attempt_entry(
        protocol,
        attempt_index=1,
        replacement_for_attempt_index=1,
    )
    with pytest.raises(RepresentativeRetrialError, match="replacement must point"):
        validate_attempt_ledger([invalid_replacement], protocol)


def test_complete_schedule_aggregates_only_operation_level_go() -> None:
    protocol = _protocol()
    records = []
    for attempt_index, entry in enumerate(protocol["schedule"], start=1):  # type: ignore[union-attr]
        records.append(
            _record(
                protocol,
                task_id=entry["task_id"],
                replicate=entry["replicate"],
                attempt_index=attempt_index,
            )
        )
    preflight = assess_runner_preflight(protocol, _observation())
    results = build_results(
        protocol=protocol,
        preflight=preflight,
        records=records,
        generated_at="2026-08-16T15:00:00Z",
    )
    assert results["result"]["batch_status"] == "complete"
    assert results["result"]["retained_session_count"] == 36
    assert all(
        item["status"] == "go-to-narrow-design-workcase"
        for item in results["result"]["family_results"]
    )
    assert results["result"]["unavailable_semantics"]["causal_effect"] == "not_measured"


def test_duplicate_retained_frame_cannot_yield_complete_batch() -> None:
    protocol = _protocol()
    records = []
    for attempt_index, entry in enumerate(protocol["schedule"], start=1):  # type: ignore[union-attr]
        records.append(
            _record(
                protocol,
                task_id=entry["task_id"],
                replicate=entry["replicate"],
                attempt_index=attempt_index,
            )
        )
    duplicate = copy.deepcopy(records[0])
    duplicate["attempt_index"] = 36
    records[-1] = duplicate
    results = build_results(
        protocol=protocol,
        preflight=assess_runner_preflight(protocol, _observation()),
        records=records,
        generated_at="2026-08-16T15:00:00Z",
    )
    assert results["result"]["retained_session_count"] == 36
    assert results["result"]["batch_status"] == "partial"
    assert any(
        item["status"] == "not_comparable"
        for item in results["result"]["family_results"]
    )


def test_artifact_writers_create_once_and_refuse_overwrite(tmp_path: Path) -> None:
    json_path = tmp_path / "nested/result.json"
    text_path = tmp_path / "nested/report.md"
    write_new_json_artifact(json_path, {"ok": True})
    write_new_text_artifact(text_path, "report\n")
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"ok": True}
    assert hashlib.sha256(text_path.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        write_new_json_artifact(json_path, {"ok": False})
    with pytest.raises(FileExistsError):
        write_new_text_artifact(text_path, "changed\n")
