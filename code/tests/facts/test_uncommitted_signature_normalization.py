from __future__ import annotations

from copy import deepcopy

from ldvh.facts.uncommitted_signature_normalization import _candidate_fields


def _entry(field: str, value: str, *, summary: str) -> dict[str, object]:
    return {
        "signature": {"model_id": "gpt-5.6", field: value},
        "session_id": "session",
        "at": "2026-08-09T00:00:00Z",
        "summary": summary,
    }


def test_normalizes_only_entries_after_the_exact_head_prefix() -> None:
    committed = _entry("host_name", "Cindy", summary="committed")
    first = _entry("host_name", "Cindy", summary="first")
    second = _entry("host_name", "Cindy", summary="second")
    head = {"status": "closed", "change_log": [deepcopy(committed)]}
    current = {"status": "closed", "change_log": [deepcopy(committed), first, second]}

    candidate, count, issue = _candidate_fields(current, head)

    assert issue is None
    assert count == 2
    assert candidate is not None
    assert candidate["change_log"][0] == committed  # type: ignore[index]
    assert candidate["change_log"][1]["signature"] == {  # type: ignore[index]
        "model_id": "gpt-5.6",
        "agent_workbench": "Cindy",
    }
    assert current["change_log"][1]["signature"] == {  # type: ignore[index]
        "model_id": "gpt-5.6",
        "host_name": "Cindy",
    }


def test_rejects_a_non_prefix_head_history() -> None:
    head = {"change_log": [_entry("host_name", "Cindy", summary="HEAD")]}
    current = {"change_log": [_entry("host_name", "Cindy", summary="changed")]}

    candidate, count, issue = _candidate_fields(current, head)

    assert candidate is None
    assert count == 0
    assert issue is not None


def test_rejects_mixed_or_already_canonical_uncommitted_suffixes() -> None:
    committed = _entry("host_name", "Cindy", summary="committed")
    head = {"change_log": [deepcopy(committed)]}
    current = {
        "change_log": [
            deepcopy(committed),
            _entry("agent_workbench", "Cindy", summary="already-current"),
        ]
    }

    candidate, count, issue = _candidate_fields(current, head)

    assert candidate is None
    assert count == 0
    assert issue is not None
