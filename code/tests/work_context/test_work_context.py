"""Behavioral tests for the ldvh-work-context entry degradation messages."""

from __future__ import annotations

import io
import json
import sys

import pytest

from ldvh import work_context


def _run_main(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stdin_text: str,
) -> dict:
    monkeypatch.setattr(
        sys,
        "argv",
        ["ldvh-work-context", "--helper-executable", "/nonexistent-helper"],
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
    exit_code = work_context.main()
    assert exit_code == 0
    return json.loads(capsys.readouterr().out)


def test_empty_stdin_reports_clear_gap(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = _run_main(monkeypatch, capsys, "")
    assert result["contract"] == "ldvh-work-context/1"
    assert result["outcome"] == "unavailable"
    assert result["facts"] == "not_requested"
    assert "UTF-8 JSON object" in result["additional_context"]
    assert "Expecting value" not in result["additional_context"]


def test_invalid_json_stdin_reports_clear_gap(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = _run_main(monkeypatch, capsys, "not-json")
    assert result["outcome"] == "unavailable"
    assert "UTF-8 JSON object" in result["additional_context"]
    assert "Expecting value" not in result["additional_context"]


def test_non_object_event_reports_clear_gap(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = _run_main(monkeypatch, capsys, "[]")
    assert result["outcome"] == "unavailable"
    assert "must be a JSON object" in result["additional_context"]
