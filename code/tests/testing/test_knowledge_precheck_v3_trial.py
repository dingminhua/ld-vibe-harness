from __future__ import annotations

import json
from pathlib import Path

import pytest

from ldvh.testing.knowledge_precheck_v3 import bytes_sha256
from ldvh.testing.knowledge_precheck_v3_trial import (
    TrialRunnerError,
    exclude_pair,
    finalize_output,
    helper_call,
    initialize_bundle,
    prepare_attempt,
    record_f3_decision,
    record_trigger,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = PROJECT_ROOT / "docs/metrics/knowledge-precheck-v3"


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _bundle(tmp_path: Path) -> Path:
    root = tmp_path / "bundle"
    initialize_bundle(artifact_root=ARTIFACT_ROOT, bundle_root=root)
    return root


def _trace(packet: dict[str, object], condition: str, triggered: bool) -> dict[str, object]:
    del condition
    return {
        "triggered": triggered,
        "trigger_family": packet["family"] if triggered else None,
        "positive_condition_codes": ["observed-signal"] if triggered else [],
        "veto_condition_codes": [],
    }


def test_helper_requires_pre_f2_trace_and_f3_requires_f2(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    packet = prepare_attempt(
        root=root,
        pair_id="A1",
        condition="l1-baseline",
        fresh_context_id_hash=bytes_sha256(b"member-a1"),
    )
    request = tmp_path / "request.json"
    _write(
        request,
        {
            "arguments": {
                "governed_project_id": "ldvh",
                "card_layer": "F2",
                "fact_type_keys": ["adr"],
                "statuses": ["active"],
            }
        },
    )
    with pytest.raises(TrialRunnerError, match="pre-F2"):
        helper_call(
            root=root,
            repository_root=PROJECT_ROOT,
            ldvh_executable=PROJECT_ROOT / "ldvh",
            attempt_id=str(packet["attempt_id"]),
            operation="find-fact-object-candidates",
            request_file=request,
        )
    trace_file = tmp_path / "trace.json"
    _write(trace_file, _trace(packet, "l1-baseline", False))
    record_trigger(root=root, attempt_id=str(packet["attempt_id"]), trace_file=trace_file)
    with pytest.raises(TrialRunnerError, match="negative trigger"):
        helper_call(
            root=root,
            repository_root=PROJECT_ROOT,
            ldvh_executable=PROJECT_ROOT / "ldvh",
            attempt_id=str(packet["attempt_id"]),
            operation="find-fact-object-candidates",
            request_file=request,
        )


def test_real_readonly_f2_is_captured_after_positive_trace(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    packet = prepare_attempt(
        root=root,
        pair_id="P1",
        condition="l1-baseline",
        fresh_context_id_hash=bytes_sha256(b"member-p1"),
    )
    trace_file = tmp_path / "trace.json"
    _write(trace_file, _trace(packet, "l1-baseline", True))
    record_trigger(root=root, attempt_id=str(packet["attempt_id"]), trace_file=trace_file)
    request = tmp_path / "f2.json"
    _write(
        request,
        {
            "arguments": {
                "governed_project_id": "ldvh",
                "card_layer": "F2",
                "fact_type_keys": ["pitfall"],
                "statuses": ["active"],
            }
        },
    )
    result = helper_call(
        root=root,
        repository_root=PROJECT_ROOT,
        ldvh_executable=PROJECT_ROOT / "ldvh",
        attempt_id=str(packet["attempt_id"]),
        operation="find-fact-object-candidates",
        request_file=request,
    )
    assert result["helper_response"]["outcome"] == "ok"
    exchange = next((root / "helper-exchanges").glob("*.json"))
    evidence = json.loads(exchange.read_bytes())
    assert evidence["state_changing_calls"] == 0
    assert evidence["coverage"]["status"] == "complete"
    snapshot = json.loads((root / "source-snapshot.json").read_bytes())
    uid = next(uid for uid, family in snapshot["knowledge_ref_families"].items() if family == "pitfall")
    decision = tmp_path / "f3-decision.json"
    _write(decision, {"read_f3_refs": [uid]})
    record_f3_decision(root=root, attempt_id=str(packet["attempt_id"]), decision_file=decision)
    f3_request = tmp_path / "f3.json"
    _write(f3_request, {"arguments": {"fact_refs": [{"object_uid": uid}]}})
    result = helper_call(
        root=root,
        repository_root=PROJECT_ROOT,
        ldvh_executable=PROJECT_ROOT / "ldvh",
        attempt_id=str(packet["attempt_id"]),
        operation="read-fact-objects",
        request_file=f3_request,
    )
    assert result["helper_response"]["outcome"] == "ok"


def test_cross_family_f2_and_output_without_required_trace_fail(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    packet = prepare_attempt(
        root=root,
        pair_id="S1",
        condition="l1-baseline",
        fresh_context_id_hash=bytes_sha256(b"member-s1"),
    )
    wrong_trace = tmp_path / "wrong-trace.json"
    trace = _trace(packet, "l1-baseline", True)
    trace["trigger_family"] = "adr"
    _write(wrong_trace, trace)
    with pytest.raises(ValueError, match="family"):
        record_trigger(root=root, attempt_id=str(packet["attempt_id"]), trace_file=wrong_trace)
    response = tmp_path / "response.json"
    _write(
        response,
        {
            "decision": "wait",
            "selected_refs": [],
            "first_legal_action": "wait",
            "rationale_codes": ["none"],
            "refusal_reason_codes": [],
        },
    )
    with pytest.raises(TrialRunnerError, match="trigger trace"):
        finalize_output(root=root, attempt_id=str(packet["attempt_id"]), response_file=response)


def test_positive_trace_still_enforces_f2_before_f3_and_same_family(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    packet = prepare_attempt(
        root=root,
        pair_id="S1",
        condition="l1-baseline",
        fresh_context_id_hash=bytes_sha256(b"member-s1-positive"),
    )
    attempt_id = str(packet["attempt_id"])
    trace_file = tmp_path / "positive-trace.json"
    _write(trace_file, _trace(packet, "l1-baseline", True))
    record_trigger(root=root, attempt_id=attempt_id, trace_file=trace_file)

    cross_family_f2 = tmp_path / "cross-family-f2.json"
    _write(
        cross_family_f2,
        {
            "arguments": {
                "governed_project_id": "ldvh",
                "card_layer": "F2",
                "fact_type_keys": ["adr"],
                "statuses": ["active"],
            }
        },
    )
    with pytest.raises(TrialRunnerError, match="family"):
        helper_call(
            root=root,
            repository_root=PROJECT_ROOT,
            ldvh_executable=PROJECT_ROOT / "ldvh",
            attempt_id=attempt_id,
            operation="find-fact-object-candidates",
            request_file=cross_family_f2,
        )

    snapshot = json.loads((root / "source-snapshot.json").read_bytes())
    uid = next(uid for uid, family in snapshot["knowledge_ref_families"].items() if family == "study")
    f3_request = tmp_path / "f3-first.json"
    _write(f3_request, {"arguments": {"fact_refs": [{"object_uid": uid}]}})
    with pytest.raises(TrialRunnerError, match="only after"):
        helper_call(
            root=root,
            repository_root=PROJECT_ROOT,
            ldvh_executable=PROJECT_ROOT / "ldvh",
            attempt_id=attempt_id,
            operation="read-fact-objects",
            request_file=f3_request,
        )

    study_f2 = tmp_path / "study-f2.json"
    _write(
        study_f2,
        {
            "arguments": {
                "governed_project_id": "ldvh",
                "card_layer": "F2",
                "fact_type_keys": ["study"],
                "statuses": ["active"],
            }
        },
    )
    helper_call(
        root=root,
        repository_root=PROJECT_ROOT,
        ldvh_executable=PROJECT_ROOT / "ldvh",
        attempt_id=attempt_id,
        operation="find-fact-object-candidates",
        request_file=study_f2,
    )
    cross_family_uid = next(uid for uid, family in snapshot["knowledge_ref_families"].items() if family == "adr")
    cross_family_decision = tmp_path / "cross-family-f3-decision.json"
    _write(cross_family_decision, {"read_f3_refs": [cross_family_uid]})
    with pytest.raises(ValueError, match="crossed"):
        record_f3_decision(root=root, attempt_id=attempt_id, decision_file=cross_family_decision)


def test_prepare_requires_fresh_member_context_and_frozen_arm_order(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    context_hash = bytes_sha256(b"one-member-context")
    prepare_attempt(root=root, pair_id="A1", condition="l1-baseline", fresh_context_id_hash=context_hash)
    with pytest.raises(TrialRunnerError, match="fresh context"):
        prepare_attempt(root=root, pair_id="A1", condition="l1-specific", fresh_context_id_hash=context_hash)
    with pytest.raises(TrialRunnerError, match="condition order"):
        prepare_attempt(
            root=root,
            pair_id="A2",
            condition="l1-baseline",
            fresh_context_id_hash=bytes_sha256(b"wrong-arm-order"),
        )


def test_technical_failure_excludes_and_reruns_only_a_whole_pair(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    protocol = json.loads((root / "protocol.json").read_bytes())
    order = protocol["condition_orders"][0]
    packets = []
    failures: dict[str, Path] = {}
    for index, condition in enumerate(order):
        packet = prepare_attempt(
            root=root,
            pair_id="A1",
            condition=condition,
            fresh_context_id_hash=bytes_sha256(f"failed-a1-{index}".encode()),
        )
        packets.append(packet)
        attempt_id = str(packet["attempt_id"])
        trace = tmp_path / f"{attempt_id}-trace.json"
        _write(trace, _trace(packet, condition, False))
        record_trigger(root=root, attempt_id=attempt_id, trace_file=trace)
        failure = tmp_path / f"{attempt_id}-invalid.json"
        _write(failure, {"decision": "not-a-closed-response"})
        failures[attempt_id] = failure

    with pytest.raises(TrialRunnerError, match="recorded technical exclusion"):
        prepare_attempt(
            root=root,
            pair_id="A1",
            condition=order[0],
            fresh_context_id_hash=bytes_sha256(b"forbidden-single-arm-retry"),
        )
    replacement = exclude_pair(
        root=root,
        pair_id="A1",
        exclusion_code="missing_structured_output",
        failure_files=failures,
    )
    assert replacement["excluded_attempt_ids"] == [str(packet["attempt_id"]) for packet in packets]
    rerun_first = prepare_attempt(
        root=root,
        pair_id="A1",
        condition=order[0],
        fresh_context_id_hash=bytes_sha256(b"rerun-a1-0"),
    )
    with pytest.raises(TrialRunnerError, match="condition order"):
        prepare_attempt(
            root=root,
            pair_id="A1",
            condition=order[0],
            fresh_context_id_hash=bytes_sha256(b"rerun-a1-wrong-second"),
        )
    rerun_second = prepare_attempt(
        root=root,
        pair_id="A1",
        condition=order[1],
        fresh_context_id_hash=bytes_sha256(b"rerun-a1-1"),
    )
    assert rerun_first["attempt_id"] != rerun_second["attempt_id"]
    ledger = json.loads((root / "attempt-ledger.json").read_bytes())
    assert ledger["pair_attempts"] == 2
    assert ledger["process_launches"] == 4
