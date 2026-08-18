"""Focused tests for the v5 activation-layers paired trial runner.

The v5 gateway compares live F2 cards byte-exactly against the frozen card
sets.  The live Helper stamps a fresh ``source_refs[].observed_at`` on every
call, so a real subprocess F2 lookup always drifts.  These tests therefore
drive the positive F2/F3 paths by replaying the frozen ``source-observations``
fixtures (read-only inputs) through :class:`ReadOnlyKnowledgeGateway`, while
the runner-owned orchestration steps (prepare / trigger / exclude / finalize /
blind / score) are exercised through the trial module directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ldvh.testing.knowledge_precheck_v2 import bytes_sha256
from ldvh.testing.knowledge_precheck_v5 import (
    MAX_MEMBER_LAUNCHES,
    MAX_PAIR_ATTEMPTS,
    MAX_REPLACEMENTS,
    MAX_SCORER_CONTEXTS,
    RETAINED_PAIR_TARGET,
    RUN_TIMEOUT_SECONDS,
    TOTAL_TIMEOUT_SECONDS,
    ReadOnlyKnowledgeGateway,
    validate_protocol,
)
from ldvh.testing.knowledge_precheck_v5_trial import (
    TrialRunnerError,
    build_attempt_blind_packet,
    exclude_pair,
    finalize_output,
    helper_call,
    initialize_bundle,
    prepare_attempt,
    record_score,
    record_trigger,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = PROJECT_ROOT / "docs/metrics/knowledge-precheck-v5"
OBJECT_SET_FINGERPRINT = "f8f26823704af0f7986c2f97b0e8b09e6a8631150532d307ee254f5026545c42"


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


def _minimal_response() -> dict[str, object]:
    return {
        "decision": "wait",
        "selected_refs": [],
        "first_legal_action": "wait",
        "rationale_codes": ["none"],
        "refusal_reason_codes": [],
    }


def _minimal_scorer_response(action_bridge_score: int = 2) -> dict[str, object]:
    return {
        "condition_blind_attested": True,
        "knowledge_adjusted_first_legal_action_correct": True,
        "action_changed": True,
        "strong_reuse": True,
        "correct_non_use": False,
        "action_bridge_score": action_bridge_score,
        "scoring_notes": "test scorer notes",
    }


def _f2_request(family: str) -> dict[str, object]:
    return {
        "arguments": {
            "governed_project_id": "ldvh",
            "card_layer": "F2",
            "fact_type_keys": [family],
            "statuses": ["active"],
        }
    }


# ---------------------------------------------------------------------------
# Bundle initialization and frozen protocol
# ---------------------------------------------------------------------------


def test_v5_trial_init_creates_bundle(tmp_path: Path) -> None:
    """initialize_bundle must copy protocol, snapshot, and source-observations."""
    root = _bundle(tmp_path)
    assert (root / "protocol.json").is_file()
    assert (root / "source-snapshot.json").is_file()
    assert (root / "source-observations").is_dir()
    assert (root / "source-observations" / "adr-f2.response.json").is_file()
    assert (root / "source-observations" / "pitfall-f2.response.json").is_file()
    assert (root / "source-observations" / "study-f2.response.json").is_file()
    assert (root / "source-observations" / "f3-fingerprints.response.json").is_file()
    assert (root / "attempt-ledger.json").is_file()
    assert (root / "adjudication.json").is_file()


def test_v5_trial_bundle_protocol_valid(tmp_path: Path) -> None:
    """The initialized bundle's protocol must pass v5 validation."""
    root = _bundle(tmp_path)
    protocol = json.loads((root / "protocol.json").read_bytes())
    problems = validate_protocol(protocol)
    assert not problems, f"protocol problems: {problems}"


# ---------------------------------------------------------------------------
# Cross-arm card set correctness
# ---------------------------------------------------------------------------


def test_v5_trial_snapshot_dual_card_sets(tmp_path: Path) -> None:
    """Snapshot must have both baseline and activation card sets covering all 3 families."""
    root = _bundle(tmp_path)
    snapshot = json.loads((root / "source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]
    for family in ("adr", "pitfall", "study"):
        assert family in baseline, f"baseline missing {family}"
        assert family in activation, f"activation missing {family}"
        # Both arms have the same number of cards per family
        assert len(baseline[family]) == len(activation[family])
        # Baseline cards are whole Helper cards with original fields (no projection keys)
        for card in baseline[family]:
            assert "fields" in card
            assert "object_uid" in card["fields"]
            assert "object_id" in card["fields"]
            assert "activation_means" not in card
            assert "suggested_action" not in card
        # Activation cards have projection structure with knowledge_body.fields
        for card in activation[family]:
            assert "activation_means" in card
            assert "suggested_action" in card
            assert "knowledge_body" in card
            assert "fields" in card["knowledge_body"]
            assert "object_uid" in card["knowledge_body"]["fields"]
        # Activation projection preserves the frozen object identity
        baseline_uids = sorted(card["fields"]["object_uid"] for card in baseline[family])
        activation_uids = sorted(card["knowledge_body"]["fields"]["object_uid"] for card in activation[family])
        assert baseline_uids == activation_uids, f"{family} activation projection must bind the frozen set"


# ---------------------------------------------------------------------------
# Ledger ceilings
# ---------------------------------------------------------------------------


def test_v5_trial_ledger_ceilings(tmp_path: Path) -> None:
    """Ledger ceilings must match the v5 constants."""
    root = _bundle(tmp_path)
    protocol = json.loads((root / "protocol.json").read_bytes())
    ceilings = protocol["ceilings"]
    assert ceilings["maximum_member_launches"] == MAX_MEMBER_LAUNCHES == 42
    assert ceilings["maximum_scorer_contexts"] == MAX_SCORER_CONTEXTS == 42
    assert ceilings["run_timeout_seconds"] == RUN_TIMEOUT_SECONDS == 600
    assert ceilings["total_timeout_seconds"] == TOTAL_TIMEOUT_SECONDS == 21600  # 6h
    assert ceilings["maximum_replacements"] == MAX_REPLACEMENTS == 3
    assert ceilings["maximum_pair_attempts"] == MAX_PAIR_ATTEMPTS == 21
    assert ceilings["retained_pair_target"] == RETAINED_PAIR_TARGET == 18
    assert ceilings["same_arm_retries"] == 0


# ---------------------------------------------------------------------------
# Fresh context / scorer uniqueness
# ---------------------------------------------------------------------------


def test_v5_trial_prepare_requires_fresh_member_context(tmp_path: Path) -> None:
    """prepare_attempt must reject duplicate fresh_context_id_hash."""
    root = _bundle(tmp_path)
    ctx = bytes_sha256(b"member-context")
    prepare_attempt(root=root, pair_id="A1", condition="activation-baseline", fresh_context_id_hash=ctx)
    with pytest.raises(TrialRunnerError, match="fresh context"):
        prepare_attempt(root=root, pair_id="A1", condition="activation-enhanced", fresh_context_id_hash=ctx)


def test_v5_trial_prepare_enforces_frozen_arm_order(tmp_path: Path) -> None:
    """prepare_attempt must enforce the frozen condition order."""
    root = _bundle(tmp_path)
    prepare_attempt(
        root=root,
        pair_id="A1",
        condition="activation-baseline",
        fresh_context_id_hash=bytes_sha256(b"order-a1"),
    )
    # Second arm of A1 must be activation-enhanced (from the protocol order)
    with pytest.raises(TrialRunnerError, match="condition order"):
        prepare_attempt(
            root=root,
            pair_id="A1",
            condition="activation-baseline",
            fresh_context_id_hash=bytes_sha256(b"order-a1-wrong"),
        )


# ---------------------------------------------------------------------------
# Runner-owned orchestration guards (fail before any Helper lookup)
# ---------------------------------------------------------------------------


def test_v5_trial_helper_requires_pre_f2_trace(tmp_path: Path) -> None:
    """helper_call must reject a call without a pre-F2 trigger trace."""
    root = _bundle(tmp_path)
    packet = prepare_attempt(
        root=root,
        pair_id="A1",
        condition="activation-baseline",
        fresh_context_id_hash=bytes_sha256(b"member-a1"),
    )
    request = tmp_path / "request.json"
    _write(request, _f2_request("adr"))
    with pytest.raises(TrialRunnerError, match="pre-F2"):
        helper_call(
            root=root,
            repository_root=PROJECT_ROOT,
            ldvh_executable=PROJECT_ROOT / "ldvh",
            attempt_id=str(packet["attempt_id"]),
            operation="find-fact-object-candidates",
            request_file=request,
        )


def test_v5_trial_negative_trigger_forbids_helper(tmp_path: Path) -> None:
    """A negative trigger decision must forbid Helper lookup."""
    root = _bundle(tmp_path)
    packet = prepare_attempt(
        root=root,
        pair_id="A1",
        condition="activation-baseline",
        fresh_context_id_hash=bytes_sha256(b"member-a1-neg"),
    )
    trace_file = tmp_path / "trace.json"
    _write(trace_file, _trace(packet, "activation-baseline", False))
    record_trigger(root=root, attempt_id=str(packet["attempt_id"]), trace_file=trace_file)
    request = tmp_path / "f2.json"
    _write(request, _f2_request("adr"))
    with pytest.raises(TrialRunnerError, match="negative trigger"):
        helper_call(
            root=root,
            repository_root=PROJECT_ROOT,
            ldvh_executable=PROJECT_ROOT / "ldvh",
            attempt_id=str(packet["attempt_id"]),
            operation="find-fact-object-candidates",
            request_file=request,
        )


def test_v5_trial_cross_family_f2_rejected(tmp_path: Path) -> None:
    """Cross-family F2 must be rejected."""
    root = _bundle(tmp_path)
    packet = prepare_attempt(
        root=root,
        pair_id="S1",
        condition="activation-baseline",
        fresh_context_id_hash=bytes_sha256(b"member-s1-cross"),
    )
    attempt_id = str(packet["attempt_id"])
    trace_file = tmp_path / "trace.json"
    _write(trace_file, _trace(packet, "activation-baseline", True))
    record_trigger(root=root, attempt_id=attempt_id, trace_file=trace_file)
    cross_family_f2 = tmp_path / "cross-family-f2.json"
    _write(cross_family_f2, _f2_request("adr"))
    with pytest.raises(TrialRunnerError, match="family"):
        helper_call(
            root=root,
            repository_root=PROJECT_ROOT,
            ldvh_executable=PROJECT_ROOT / "ldvh",
            attempt_id=attempt_id,
            operation="find-fact-object-candidates",
            request_file=cross_family_f2,
        )


def test_v5_trial_f3_before_f2_rejected(tmp_path: Path) -> None:
    """F3 call before F2 must be rejected."""
    root = _bundle(tmp_path)
    packet = prepare_attempt(
        root=root,
        pair_id="S1",
        condition="activation-baseline",
        fresh_context_id_hash=bytes_sha256(b"member-s1-f3first"),
    )
    attempt_id = str(packet["attempt_id"])
    trace_file = tmp_path / "trace.json"
    _write(trace_file, _trace(packet, "activation-baseline", True))
    record_trigger(root=root, attempt_id=attempt_id, trace_file=trace_file)
    snapshot = json.loads((root / "source-snapshot.json").read_bytes())
    adr_uid = next(uid for uid, family in snapshot["knowledge_ref_families"].items() if family == "adr")
    f3_request = tmp_path / "f3-first.json"
    _write(f3_request, {"arguments": {"fact_refs": [{"object_uid": adr_uid}]}})
    with pytest.raises(TrialRunnerError, match="only after"):
        helper_call(
            root=root,
            repository_root=PROJECT_ROOT,
            ldvh_executable=PROJECT_ROOT / "ldvh",
            attempt_id=attempt_id,
            operation="read-fact-objects",
            request_file=f3_request,
        )


# ---------------------------------------------------------------------------
# Real readonly F2/F3 fixtures replayed through the gateway
# ---------------------------------------------------------------------------


def test_v5_trial_gateway_replay_frozen_f2_baseline(tmp_path: Path) -> None:
    """The frozen adr F2 response must replay cleanly on the baseline arm."""
    root = _bundle(tmp_path)
    snapshot = json.loads((root / "source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]
    frozen = json.loads((root / "source-observations" / "adr-f2.response.json").read_bytes())

    def dispatch(operation: str, request_bytes: bytes) -> bytes:
        del operation
        del request_bytes
        return json.dumps(frozen).encode("utf-8")

    gateway = ReadOnlyKnowledgeGateway(
        dispatch,
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        _f2_request("adr"),
        exchange_id="e1",
        attempt_id="a1",
        card_layer="activation-baseline",
    )
    observed = json.loads(exchange["raw_response_utf8"])["result"]["cards"]
    # Byte/field assertion: baseline arm serves the original attribute card fields
    assert [card["fields"] for card in observed] == [card["fields"] for card in baseline["adr"]]
    assert "activation_means" not in observed[0]["fields"]
    assert "knowledge_body" not in observed[0]["fields"]


def test_v5_trial_gateway_replay_frozen_f2_enhanced(tmp_path: Path) -> None:
    """The activation arm must project the activation card set at runtime."""
    root = _bundle(tmp_path)
    snapshot = json.loads((root / "source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]
    frozen = json.loads((root / "source-observations" / "adr-f2.response.json").read_bytes())

    def dispatch(operation: str, request_bytes: bytes) -> bytes:
        del operation
        del request_bytes
        # The live Helper always returns the baseline (knowledge-body) shape;
        # the gateway projects to the activation shape for the enhanced arm.
        return json.dumps(frozen).encode("utf-8")

    gateway = ReadOnlyKnowledgeGateway(
        dispatch,
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        _f2_request("adr"),
        exchange_id="e1",
        attempt_id="a1",
        card_layer="activation-enhanced",
    )
    observed = exchange["served_cards"]
    # Byte/field assertion: activation arm serves the projected card fields
    assert [card["fields"] for card in observed] == activation["adr"]
    for card in observed:
        assert "activation_means" in card["fields"]
        assert "suggested_action" in card["fields"]
        assert "knowledge_body" in card["fields"]


def test_v5_trial_gateway_replay_frozen_f3(tmp_path: Path) -> None:
    """A frozen F3 fingerprint item must replay cleanly through the gateway."""
    root = _bundle(tmp_path)
    snapshot = json.loads((root / "source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]
    fingerprints = snapshot["knowledge_ref_fingerprints"]
    frozen = json.loads((root / "source-observations" / "f3-fingerprints.response.json").read_bytes())
    uid = "019ffb52-ebb5-724c-881f-4f0f7d97038f"
    item = next(it for it in frozen["result"]["items"] if it["resolved_ref"]["object_uid"] == uid)
    assert uid in fingerprints

    def dispatch(operation: str, request_bytes: bytes) -> bytes:
        del operation
        del request_bytes
        return json.dumps(
            {
                "operation_key": "read-fact-objects",
                "outcome": "ok",
                "changes": [],
                "result": {"items": [item]},
            }
        ).encode("utf-8")

    gateway = ReadOnlyKnowledgeGateway(
        dispatch,
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
        expected_f3_fingerprints=fingerprints,
    )
    exchange = gateway.call(
        "read-fact-objects",
        {"arguments": {"fact_refs": [{"object_uid": uid}]}},
        exchange_id="e1",
        attempt_id="a1",
    )
    assert [obj["object_uid"] for obj in exchange["f3_objects"]] == [uid]


def test_v5_trial_gateway_enhanced_projects_from_baseline(tmp_path: Path) -> None:
    """The activation arm must project the frozen activation set from a live baseline response."""
    root = _bundle(tmp_path)
    snapshot = json.loads((root / "source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]
    frozen = json.loads((root / "source-observations" / "adr-f2.response.json").read_bytes())

    def dispatch(operation: str, request_bytes: bytes) -> bytes:
        del operation
        del request_bytes
        return json.dumps(frozen).encode("utf-8")

    gateway = ReadOnlyKnowledgeGateway(
        dispatch,
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        _f2_request("adr"),
        exchange_id="e1",
        attempt_id="a1",
        card_layer="activation-enhanced",
    )
    observed = exchange["served_cards"]
    # The live Helper returns baseline cards; the gateway projects them to the
    # activation shape for the enhanced arm instead of failing closed.
    assert [card["fields"] for card in observed] == activation["adr"]
    for card in observed:
        assert "activation_means" in card["fields"]
        assert "suggested_action" in card["fields"]
    assert [card["fields"] for card in observed] != baseline["adr"]


# ---------------------------------------------------------------------------
# Technical failure: exclude and rerun a whole pair
# ---------------------------------------------------------------------------


def test_v5_trial_technical_failure_exclude_and_rerun(tmp_path: Path) -> None:
    """Technical failure must exclude both arms and allow a rerun."""
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
    assert replacement["excluded_attempt_ids"] == [str(p["attempt_id"]) for p in packets]

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


# ---------------------------------------------------------------------------
# Non-trigger full flow: prepare -> trigger -> finalize -> blind -> score
# ---------------------------------------------------------------------------


def _complete_non_trigger_pair(root: Path, tmp_path: Path, pair_id: str, index: int) -> str:
    """Complete a full non-trigger member run and return its attempt id."""
    protocol = json.loads((root / "protocol.json").read_bytes())
    task_index = [task["pair_id"] for task in protocol["tasks"]].index(pair_id)
    condition = protocol["condition_orders"][task_index][0]
    packet = prepare_attempt(
        root=root,
        pair_id=pair_id,
        condition=condition,
        fresh_context_id_hash=bytes_sha256(f"{pair_id}-member-{index}".encode()),
    )
    attempt_id = str(packet["attempt_id"])
    trace = tmp_path / f"{attempt_id}-trace.json"
    _write(trace, _trace(packet, condition, False))
    record_trigger(root=root, attempt_id=attempt_id, trace_file=trace)
    response = tmp_path / f"{attempt_id}-response.json"
    _write(response, _minimal_response())
    finalize_output(root=root, attempt_id=attempt_id, response_file=response)
    build_attempt_blind_packet(root=root, attempt_id=attempt_id)
    return attempt_id


def test_v5_trial_non_trigger_full_flow(tmp_path: Path) -> None:
    """A full non-trigger member run (enhanced arm) must complete without errors."""
    root = _bundle(tmp_path)
    attempt_id = _complete_non_trigger_pair(root, tmp_path, "A4", 1)
    score_file = tmp_path / f"{attempt_id}-score.json"
    _write(score_file, _minimal_scorer_response(2))
    score = record_score(
        root=root,
        attempt_id=attempt_id,
        score_file=score_file,
        fresh_scorer_context_id_hash=bytes_sha256(b"scorer-a4"),
    )
    assert score["attempt_id"] == attempt_id
    # The finalized output must have been recorded
    assert (root / "model-outputs" / f"{attempt_id}.json").is_file()
    assert (root / "blind-packets" / f"{attempt_id}.json").is_file()
    assert (root / "scores" / f"{attempt_id}.json").is_file()


def test_v5_trial_scorer_context_unique(tmp_path: Path) -> None:
    """record_score must reject a reused fresh_scorer_context_id_hash."""
    root = _bundle(tmp_path)
    first = _complete_non_trigger_pair(root, tmp_path, "A4", 1)
    second = _complete_non_trigger_pair(root, tmp_path, "A5", 2)
    first_score = tmp_path / f"{first}-score.json"
    _write(first_score, _minimal_scorer_response(2))
    record_score(
        root=root,
        attempt_id=first,
        score_file=first_score,
        fresh_scorer_context_id_hash=bytes_sha256(b"scorer-shared"),
    )
    second_score = tmp_path / f"{second}-score.json"
    _write(second_score, _minimal_scorer_response(2))
    with pytest.raises(TrialRunnerError, match="fresh scorer context"):
        record_score(
            root=root,
            attempt_id=second,
            score_file=second_score,
            fresh_scorer_context_id_hash=bytes_sha256(b"scorer-shared"),
        )


if __name__ == "__main__":
    print("trial tests are exercised through pytest only")
