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
CAPABILITY_BOUNDARY_STATEMENTS = (
    "薄 Skill 对事实写入的保护仅为劝告级：它只能将 AI 路由到 Helper 与行动模板，不能在模型之外机械阻断对 `ldvh-base/` 的直写。",
    "Git Gate 的每一安装实例只覆盖一个实际 Git worktree 中真正触发该 Gate 的 Git 事件；其它 worktree、clone，以及未触发或绕过该 Gate 的行动不在其覆盖范围。",
    "机械检查能够发现来源已定义的机械不合格，不能据此判断事实内容的语义真实性；即使 Schema 合法，语义污染风险仍然存在，未提交污染窗口只能压缩、不能消除。",
)


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
    for statement in CAPABILITY_BOUNDARY_STATEMENTS:
        assert statement in context


def test_subagent_start_delivers_rule_orientation_without_facts_or_authorization() -> None:
    result = work_context.run(
        {
            "hook_event_name": "SubagentStart",
            "cwd": str(REPOSITORY_ROOT),
        },
        helper_executable=str(HELPER_EXECUTABLE),
    )

    assert result["event_name"] == "SubagentStart"
    assert result["outcome"] == "ok"
    assert result["facts"] == "not_requested"
    context = result["additional_context"]
    assert "ran for SubagentStart" in context
    assert "Facts: not_requested." in context
    assert "did not perform governance resolution, fact discovery, fact reading, " in context
    assert "authorization, or completion judgment." in context
