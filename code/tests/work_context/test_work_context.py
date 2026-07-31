"""Behavioral tests for the ldvh-work-context entry degradation messages."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from conftest import HELPER_EXECUTABLE
from ldvh import work_context

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


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


def test_rule_orientation_delivers_helper_only_write_and_integrity_route() -> None:
    result = work_context.run(
        {
            "hook_event_name": "SessionStart",
            "source": "startup",
            "cwd": str(REPOSITORY_ROOT),
        },
        helper_executable=str(HELPER_EXECUTABLE),
    )

    assert result["outcome"] == "ok"
    assert result["facts"] == "not_requested"
    context = result["additional_context"]
    assert "不得绕过 Helper 直接写入 `ldvh-base/`" in context
    assert "先精确回读受影响对象" in context
    assert "独立事实完整性审计入口" in context
    assert "提交前预检互不替代" in context
