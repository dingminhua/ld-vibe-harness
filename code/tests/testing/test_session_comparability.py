from __future__ import annotations

import json
from dataclasses import asdict

import pytest

from ldvh.testing.session_comparability import (
    REQUEST_HEADER,
    STEP_END,
    STEP_START,
    TOOL_CALL,
    TOOL_RESULT,
    TURN_END,
    TURN_START,
    RequestHeaderFingerprint,
    SessionFingerprint,
    SessionLogError,
    audit_events,
    audit_session,
    iter_events,
    judge_comparability,
)


def _event(event_type: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {"type": event_type}
    payload.update(extra)
    return payload


def _request_header(provider: str, model: str, reason: str = "initial", seq: int = 11) -> dict[str, object]:
    return _event(
        REQUEST_HEADER,
        data={"header": {"config": {"provider": provider, "model": model}}, "reason": reason},
        seq=seq,
    )


def _tool_call(name: str) -> dict[str, object]:
    return _event(TOOL_CALL, data={"name": name, "turn": 1, "step": 1, "callId": f"call-{name}"})


def _tool_result() -> dict[str, object]:
    return _event(TOOL_RESULT, data={"content": "opaque - never read by the audit"})


def _lines(payload: str) -> list[str]:
    return [line for line in payload.splitlines() if line.strip()]


def _complete_single_model_events() -> list[dict[str, object]]:
    return [
        _request_header("aixforge", "glm-5.2", reason="initial"),
        _event(TURN_START, data={"turn": 1}),
        _event(STEP_START, data={"turn": 1, "step": 1}),
        _tool_call("bash"),
        _tool_result(),
        _event(STEP_END, data={"turn": 1, "step": 1}),
        _event(TURN_END, data={"turn": 1}),
    ]


def _multi_model_events() -> list[dict[str, object]]:
    events = _complete_single_model_events()
    events.append(_request_header("deepseek-official", "deepseek-v4-flash", reason="change", seq=99))
    return events


def _no_header_events() -> list[dict[str, object]]:
    return [_event(TURN_START, data={"turn": 1}), _event(TURN_END, data={"turn": 1})]


def _unpaired_events() -> list[dict[str, object]]:
    return [
        _request_header("aixforge", "glm-5.2", reason="initial"),
        _event(TURN_START, data={"turn": 1}),
        _tool_call("bash"),
        _tool_result(),
    ]


def test_single_model_complete_session_is_comparable() -> None:
    fingerprint, verdict = audit_session(_lines(_jsonl(_complete_single_model_events())))
    assert verdict.verdict == "comparable"
    assert verdict.reasons == ()
    assert fingerprint.distinct_entries == (("aixforge", "glm-5.2"),)
    assert fingerprint.pairing_ok is True


def test_multi_model_session_is_not_comparable() -> None:
    fingerprint, verdict = audit_session(_lines(_jsonl(_multi_model_events())))
    assert verdict.verdict == "not_comparable"
    assert any("multi-model entry" in reason for reason in verdict.reasons)
    assert len(fingerprint.distinct_entries) == 2


def test_session_without_request_header_is_inconclusive() -> None:
    _fingerprint, verdict = audit_session(_lines(_jsonl(_no_header_events())))
    assert verdict.verdict == "inconclusive"
    assert any("no request/header" in reason for reason in verdict.reasons)


def test_unpaired_turn_detected_as_not_comparable() -> None:
    _fingerprint, verdict = audit_session(_lines(_jsonl(_unpaired_events())))
    assert verdict.verdict == "not_comparable"
    assert any("turn unpaired" in reason for reason in verdict.reasons)


def test_tool_name_and_pairing_counts_are_structural_only() -> None:
    fingerprint, verdict = audit_session(_lines(_jsonl(_complete_single_model_events())))
    assert fingerprint.tool_names == ("bash",)
    assert fingerprint.tool_call == 1
    assert fingerprint.tool_result == 1
    assert verdict.verdict == "comparable"


def test_opaque_event_payloads_are_never_inspected() -> None:
    events = [
        _request_header("aixforge", "glm-5.2", reason="initial"),
        _event("user/message", data={"content": [{"type": "text", "text": "secret user body"}]}),
        _tool_call("read"),
        _event("tool/result", data={"content": "secret tool body"}),
        _event("assistant/message", data={"content": [{"type": "text", "text": "secret assistant body"}]}),
    ]
    fingerprint, verdict = audit_session(_lines(_jsonl(events)))
    assert verdict.verdict == "comparable"
    # The fingerprint carries no content-bearing material at all.
    rendered = json.dumps(
        {
            "headers": [asdict(h) for h in fingerprint.headers],
            "tools": fingerprint.tool_names,
            "flags": fingerprint.flags,
        },
        ensure_ascii=False,
    )
    assert "secret" not in rendered


def test_flag_events_are_recorded_by_name_only() -> None:
    events = [
        _request_header("aixforge", "glm-5.2", reason="initial"),
        _event("approval/asked", data={"question": "opaque"}),
        _event("approval/decided", data={"answer": "opaque"}),
        _event("permission/preset", data={"preset": "opaque"}),
    ]
    fingerprint, _verdict = audit_session(_lines(_jsonl(events)))
    assert ("approval/asked", 1) in fingerprint.flags
    assert ("approval/decided", 1) in fingerprint.flags
    assert ("permission/preset", 1) in fingerprint.flags


def test_unknown_structured_event_type_is_counted_not_dropped() -> None:
    events = [
        _request_header("aixforge", "glm-5.2", reason="initial"),
        _event("some/future-event", data={"payload": "opaque"}),
    ]
    fingerprint, _verdict = audit_session(_lines(_jsonl(events)))
    assert ("event/some/future-event", 1) in fingerprint.flags


def test_iter_events_rejects_malformed_json_line() -> None:
    with pytest.raises(SessionLogError, match="valid JSON"):
        list(iter_events(['{"unfinished":']))
    with pytest.raises(SessionLogError, match="valid JSON"):
        list(iter_events(["not json at all"]))


def test_iter_events_rejects_non_object_line() -> None:
    with pytest.raises(SessionLogError, match="JSON object"):
        list(iter_events(["[1,2,3]"]))


def test_iter_events_accepts_plain_text_bytes() -> None:
    events = list(iter_events(_jsonl(_complete_single_model_events()).encode("utf-8")))
    assert len(events) >= 7


def test_audit_rejects_event_without_type() -> None:
    with pytest.raises(SessionLogError, match="type"):
        audit_events([{"seq": 1}])


def test_audit_rejects_request_header_without_config() -> None:
    with pytest.raises(SessionLogError, match="config"):
        audit_events([_event(REQUEST_HEADER, data={"header": {}})])


def test_audit_rejects_tool_call_without_name() -> None:
    with pytest.raises(SessionLogError, match="name"):
        audit_events([_event(TOOL_CALL, data={})])


def test_audit_rejects_missing_zstd_file() -> None:
    with pytest.raises(SessionLogError, match="not readable"):
        audit_session("/nonexistent/session.jsonl.zstd")


def test_audit_rejects_undecodable_zstd_bytes() -> None:
    # Bytes beginning with the Zstandard magic but not a valid frame.
    fake_zstd = b"\x28\xb5\x2f\xfd" + b"\x00" * 16
    with pytest.raises(SessionLogError):
        audit_session(fake_zstd)


def test_judge_comparability_rejects_unpaired_step_directly() -> None:
    fingerprint = SessionFingerprint(
        headers=(RequestHeaderFingerprint(provider="aixforge", model="glm-5.2", reason="initial", seq=11),),
        turn_start=1,
        turn_end=1,
        step_start=2,
        step_end=1,
        tool_call=1,
        tool_result=1,
    )
    verdict = judge_comparability(fingerprint)
    assert verdict.verdict == "not_comparable"
    assert any("step unpaired" in reason for reason in verdict.reasons)


def test_reason_field_is_preserved_in_fingerprint() -> None:
    events = [
        _request_header("aixforge", "glm-5.2", reason="initial", seq=11),
        _request_header("deepseek-official", "deepseek-v4-flash", reason="change", seq=99),
    ]
    fingerprint, _verdict = audit_session(_lines(_jsonl(events)))
    assert [h.reason for h in fingerprint.headers] == ["initial", "change"]


def _jsonl(events: list[dict[str, object]]) -> str:
    return "\n".join(json.dumps(event, ensure_ascii=False) for event in events)
