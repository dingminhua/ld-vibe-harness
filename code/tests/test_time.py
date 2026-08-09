from __future__ import annotations

from datetime import datetime

from ldvh.time import canonical_utc_timestamp, canonicalize_new_timestamp_fields, utc_now_iso


def test_new_runtime_timestamp_is_canonical_utc() -> None:
    value = utc_now_iso()

    assert value.endswith("Z")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.utcoffset().total_seconds() == 0


def test_second_precision_is_available_for_observation_records() -> None:
    value = utc_now_iso(timespec="seconds")

    assert value.endswith("Z")
    assert "." not in value


def test_canonical_utc_timestamp_preserves_fractional_precision() -> None:
    assert canonical_utc_timestamp("2026-08-09T13:45:09.272123456+08:00") == "2026-08-09T05:45:09.272123456Z"


def test_changed_nested_timestamps_are_canonical_without_rewriting_history() -> None:
    before = {
        "created_at": "2026-08-01T08:00:00+08:00",
        "updated_at": "2026-08-02T08:00:00+08:00",
        "result_reviews": [{"reviewed_at": "2026-08-02T08:00:00+08:00"}],
    }
    after = {
        **before,
        "updated_at": "2026-08-03T08:00:00+08:00",
        "execution_approval": {"approved_at": "2026-08-03T08:00:00+08:00"},
        "result_reviews": [
            *before["result_reviews"],
            {"reviewed_at": "2026-08-03T08:00:00+08:00"},
        ],
    }

    normalized = canonicalize_new_timestamp_fields(after, before=before)

    assert normalized["created_at"] == "2026-08-01T08:00:00+08:00"
    assert normalized["updated_at"] == "2026-08-03T00:00:00Z"
    assert normalized["result_reviews"][0]["reviewed_at"] == "2026-08-02T08:00:00+08:00"
    assert normalized["result_reviews"][1]["reviewed_at"] == "2026-08-03T00:00:00Z"
    assert normalized["execution_approval"]["approved_at"] == "2026-08-03T00:00:00Z"
