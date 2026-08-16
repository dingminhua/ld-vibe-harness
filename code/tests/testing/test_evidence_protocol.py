from __future__ import annotations

from ldvh.testing.evidence_protocol import (
    EVIDENCE_PROTOCOL_VERSION,
    IDENTITY_TYPES,
    SOURCE_LEVEL_BEHAVIOR_CONSISTENT,
    SOURCE_LEVEL_CAUSAL_EFFECT,
    SOURCE_LEVEL_HARNESS_DELIVERED,
    SOURCE_LEVEL_HOST_RECEIVED,
    SOURCE_LEVEL_LDVH_PREPARED,
    SOURCE_LEVELS,
    IdentityFingerprintSet,
    check_pre_scoring_threshold,
    classify_event_type,
    classify_event_types,
    classify_session_events,
    extract_session_identity,
    extract_trial_identity,
    is_out_of_protocol,
    judge_protocol_comparability,
)
from ldvh.testing.session_comparability import (
    SessionFingerprint,
)


def _make_session_fingerprint(
    *,
    headers: int = 1,
    paired: bool = True,
    flags: tuple[tuple[str, int], ...] = (),
) -> SessionFingerprint:
    """Build a minimal session fingerprint for testing."""
    from ldvh.testing.session_comparability import RequestHeaderFingerprint

    header = RequestHeaderFingerprint(provider="aixforge", model="glm-5.2", reason="initial", seq=10)
    if paired:
        return SessionFingerprint(
            headers=(header,) * headers,
            tool_names=("read",),
            turn_start=1,
            turn_end=1,
            step_start=1,
            step_end=1,
            tool_call=1,
            tool_result=1,
            flags=flags,
        )
    return SessionFingerprint(
        headers=(header,) * headers,
        tool_names=("read",),
        turn_start=1,
        turn_end=0,
        step_start=1,
        step_end=0,
        tool_call=1,
        tool_result=0,
        flags=flags,
    )


# ---------------------------------------------------------------------------
# Protocol version and constants
# ---------------------------------------------------------------------------


def test_protocol_version_is_stable() -> None:
    assert EVIDENCE_PROTOCOL_VERSION == "ldvh-evidence-protocol/1"


def test_identity_types_are_closed() -> None:
    assert IDENTITY_TYPES == ("task", "contract", "payload", "runner")


def test_source_levels_are_closed() -> None:
    assert SOURCE_LEVELS == (
        SOURCE_LEVEL_LDVH_PREPARED,
        SOURCE_LEVEL_HARNESS_DELIVERED,
        SOURCE_LEVEL_HOST_RECEIVED,
        SOURCE_LEVEL_BEHAVIOR_CONSISTENT,
        SOURCE_LEVEL_CAUSAL_EFFECT,
    )


# ---------------------------------------------------------------------------
# Identity fingerprint set
# ---------------------------------------------------------------------------


def test_identity_fingerprint_set_round_trip() -> None:
    identity = IdentityFingerprintSet(
        task_identity="a" * 64,
        contract_identity="b" * 64,
        payload_identity="c" * 64,
        runner_identity="d" * 64,
    )
    assert len(identity.task_identity) == 64
    assert len(identity.fingerprint()) == 64
    assert identity.fully_matches(identity) is True


def test_identity_fingerprint_set_detects_mismatch() -> None:
    a = IdentityFingerprintSet(
        task_identity="a" * 64,
        contract_identity="b" * 64,
        payload_identity="c" * 64,
        runner_identity="d" * 64,
    )
    b = IdentityFingerprintSet(
        task_identity="x" * 64,
        contract_identity="b" * 64,
        payload_identity="c" * 64,
        runner_identity="d" * 64,
    )
    mismatch = a.identity_mismatch(b)
    assert mismatch["task"] is False
    assert mismatch["contract"] is True
    assert a.fully_matches(b) is False


def test_extract_trial_identity_uses_structural_fields() -> None:
    identity = extract_trial_identity(
        task_id="task-01",
        task_package_hash="a" * 64,
        contract_sha256="b" * 64,
        payload={"key": "value"},
        carrier_fingerprint="c" * 64,
    )
    assert len(identity.task_identity) == 64
    assert len(identity.contract_identity) == 64
    assert len(identity.payload_identity) == 64
    assert len(identity.runner_identity) == 64
    # Same inputs produce the same fingerprints.
    identity2 = extract_trial_identity(
        task_id="task-01",
        task_package_hash="a" * 64,
        contract_sha256="b" * 64,
        payload={"key": "value"},
        carrier_fingerprint="c" * 64,
    )
    assert identity.fully_matches(identity2) is True


def test_extract_trial_identity_different_payload_different_fingerprint() -> None:
    a = extract_trial_identity(
        task_id="task-01",
        task_package_hash="a" * 64,
        contract_sha256="b" * 64,
        payload={"x": 1},
        carrier_fingerprint="c" * 64,
    )
    b = extract_trial_identity(
        task_id="task-01",
        task_package_hash="a" * 64,
        contract_sha256="b" * 64,
        payload={"x": 2},
        carrier_fingerprint="c" * 64,
    )
    assert a.payload_identity != b.payload_identity
    assert a.fully_matches(b) is False


def test_extract_session_identity_derives_runner_identity() -> None:
    fp = _make_session_fingerprint()
    identity = extract_session_identity(fp)
    assert len(identity.task_identity) == 64
    assert len(identity.runner_identity) == 64
    # Session-only task/contract/payload are placeholders.
    assert identity.task_identity == identity.contract_identity == identity.payload_identity


# ---------------------------------------------------------------------------
# Event source classification
# ---------------------------------------------------------------------------


def test_classify_event_type_known_types() -> None:
    assert classify_event_type("request/header") == SOURCE_LEVEL_HARNESS_DELIVERED
    assert classify_event_type("tool/call") == SOURCE_LEVEL_HARNESS_DELIVERED
    assert classify_event_type("approval/asked") == SOURCE_LEVEL_LDVH_PREPARED
    assert classify_event_type("sandbox/mode") == SOURCE_LEVEL_LDVH_PREPARED


def test_classify_event_type_opaque_types_return_none() -> None:
    assert classify_event_type("user/message") is None
    assert classify_event_type("assistant/message") is None
    assert classify_event_type("session/title") is None


def test_classify_event_type_unknown_type_returns_none() -> None:
    assert classify_event_type("nonexistent/event") is None


def test_classify_event_types_maps_known_only() -> None:
    result = classify_event_types(["request/header", "user/message", "tool/call", "unknown/type"])
    assert result == {
        "request/header": SOURCE_LEVEL_HARNESS_DELIVERED,
        "tool/call": SOURCE_LEVEL_HARNESS_DELIVERED,
    }


def test_classify_session_events_counts_by_level() -> None:
    fp = _make_session_fingerprint(
        flags=(("approval/asked", 2), ("sandbox/mode", 1))
    )
    counts = classify_session_events(fp)
    assert counts[SOURCE_LEVEL_LDVH_PREPARED] == 3  # 2 + 1
    assert counts[SOURCE_LEVEL_HARNESS_DELIVERED] == 6  # turn 2 + step 2 + tool 2


def test_classify_session_events_no_flags() -> None:
    fp = _make_session_fingerprint()
    counts = classify_session_events(fp)
    assert SOURCE_LEVEL_LDVH_PREPARED not in counts
    assert counts[SOURCE_LEVEL_HARNESS_DELIVERED] == 6


# ---------------------------------------------------------------------------
# Protocol comparability
# ---------------------------------------------------------------------------


def test_judge_protocol_comparability_comparable_session() -> None:
    fp = _make_session_fingerprint()
    result = judge_protocol_comparability(fp)
    assert result.session_verdict.verdict == "comparable"
    assert result.protocol_verdict == "comparable"
    assert result.effective_verdict == "comparable"


def test_judge_protocol_comparability_none_missing() -> None:
    fp = _make_session_fingerprint(headers=0)
    result = judge_protocol_comparability(fp)
    assert result.session_verdict.verdict == "inconclusive"
    assert result.effective_verdict == "inconclusive"


def test_judge_protocol_comparability_unpaired_graph() -> None:
    fp = _make_session_fingerprint(paired=False)
    result = judge_protocol_comparability(fp)
    assert result.session_verdict.verdict == "not_comparable"
    assert result.protocol_verdict == "not_comparable"
    assert "event_graph_pairing_incomplete" in result.protocol_reasons
    assert result.effective_verdict == "not_comparable"


def test_judge_protocol_comparability_identity_mismatch() -> None:
    fp = _make_session_fingerprint()
    trial = extract_trial_identity(
        task_id="task-01",
        task_package_hash="a" * 64,
        contract_sha256="b" * 64,
        payload={"x": 1},
        carrier_fingerprint="c" * 64,
    )
    reference = extract_trial_identity(
        task_id="task-02",
        task_package_hash="a" * 64,
        contract_sha256="b" * 64,
        payload={"x": 1},
        carrier_fingerprint="c" * 64,
    )
    result = judge_protocol_comparability(fp, trial_identity=trial, reference_identity=reference)
    assert result.protocol_verdict == "not_comparable"
    assert "out_of_protocol" in " ".join(result.protocol_reasons)
    assert is_out_of_protocol(result) is True


def test_judge_protocol_comparability_full_match() -> None:
    fp = _make_session_fingerprint()
    identity = extract_trial_identity(
        task_id="task-01",
        task_package_hash="a" * 64,
        contract_sha256="b" * 64,
        payload={"x": 1},
        carrier_fingerprint="c" * 64,
    )
    result = judge_protocol_comparability(
        fp, trial_identity=identity, reference_identity=identity
    )
    assert result.protocol_verdict == "comparable"
    assert is_out_of_protocol(result) is False


# ---------------------------------------------------------------------------
# Pre-scoring threshold
# ---------------------------------------------------------------------------


def test_check_pre_scoring_threshold_passes_comparable() -> None:
    fp = _make_session_fingerprint()
    pc = judge_protocol_comparability(fp)
    passed, reason = check_pre_scoring_threshold(pc)
    assert passed is True
    assert reason == "comparable"


def test_check_pre_scoring_threshold_blocks_out_of_protocol() -> None:
    fp = _make_session_fingerprint()
    trial = extract_trial_identity(
        task_id="task-01",
        task_package_hash="a" * 64,
        contract_sha256="b" * 64,
        payload={"x": 1},
        carrier_fingerprint="c" * 64,
    )
    reference = extract_trial_identity(
        task_id="task-02",
        task_package_hash="a" * 64,
        contract_sha256="b" * 64,
        payload={"x": 1},
        carrier_fingerprint="c" * 64,
    )
    pc = judge_protocol_comparability(fp, trial_identity=trial, reference_identity=reference)
    passed, reason = check_pre_scoring_threshold(pc)
    assert passed is False
    assert reason == "out_of_protocol"


def test_check_pre_scoring_threshold_blocks_unpaired() -> None:
    fp = _make_session_fingerprint(paired=False)
    pc = judge_protocol_comparability(fp)
    passed, reason = check_pre_scoring_threshold(pc)
    assert passed is False


def test_is_out_of_protocol_false_for_comparable() -> None:
    fp = _make_session_fingerprint()
    pc = judge_protocol_comparability(fp)
    assert is_out_of_protocol(pc) is False