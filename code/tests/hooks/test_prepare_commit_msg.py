"""Tests for environment-injected commit message signature trailers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from ldvh.hooks.prepare_commit_msg import (
    _strip_signature_trailers,
    inject_environment_signature,
    run_prepare_commit_msg,
)


@pytest.fixture
def env_signature(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    values = {
        "LDVH_MODEL_ID": "glm-5.2",
        "LDVH_WORKBENCH_NAME": "WorkBuddy",
        "LDVH_SESSION_ID": "test-session-abc123",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return values


class TestStripSignatureTrailers:
    def test_strips_all_three_trailers(self) -> None:
        lines = [
            "fix: test commit",
            "",
            "关键变更:",
            "- something changed",
            "",
            "Session-ID: fake-id",
            "Model-ID: gpt-5",
            "Workbench-Name: FakeBench",
        ]
        result = _strip_signature_trailers(lines)
        assert result == [
            "fix: test commit",
            "",
            "关键变更:",
            "- something changed",
        ]

    def test_preserves_non_signature_trailers(self) -> None:
        lines = [
            "fix: test commit",
            "",
            "BREAKING CHANGE: something broke",
            "Session-ID: fake-id",
            "Model-ID: gpt-5",
            "Workbench-Name: FakeBench",
        ]
        result = _strip_signature_trailers(lines)
        assert result == [
            "fix: test commit",
            "",
            "BREAKING CHANGE: something broke",
        ]

    def test_no_trailers_returns_unchanged(self) -> None:
        lines = ["fix: test commit", "", "关键变更:", "- something"]
        result = _strip_signature_trailers(lines)
        assert result == lines

    def test_strips_trailing_blank_lines_before_trailers(self) -> None:
        lines = [
            "fix: test commit",
            "",
            "",
            "",
            "Session-ID: fake-id",
        ]
        result = _strip_signature_trailers(lines)
        assert result == ["fix: test commit"]

    def test_empty_message(self) -> None:
        assert _strip_signature_trailers([]) == []


class TestInjectEnvironmentSignature:
    def test_injects_when_env_vars_set(self, env_signature: dict[str, str]) -> None:
        message = "fix: test\n\n关键变更:\n- change\n\nSession-ID: wrong\nModel-ID: gpt-5\nWorkbench-Name: FakeBench\n"
        result = inject_environment_signature(message)
        assert "Session-ID: test-session-abc123" in result
        assert "Model-ID: glm-5.2" in result
        assert "Workbench-Name: WorkBuddy" in result
        assert "wrong" not in result
        assert "gpt-5" not in result
        assert "FakeBench" not in result

    def test_no_env_vars_returns_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for key in ("LDVH_MODEL_ID", "LDVH_WORKBENCH_NAME", "LDVH_SESSION_ID"):
            monkeypatch.delenv(key, raising=False)
        message = "fix: test\n\nSession-ID: original\n"
        assert inject_environment_signature(message) == message

    def test_partial_env_vars_injects_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LDVH_MODEL_ID", "glm-5.2")
        monkeypatch.delenv("LDVH_WORKBENCH_NAME", raising=False)
        monkeypatch.delenv("LDVH_SESSION_ID", raising=False)
        message = "fix: test\n\n关键变更:\n- change\n"
        result = inject_environment_signature(message)
        assert "Model-ID: glm-5.2" in result
        assert "Workbench-Name:" not in result
        assert "Session-ID:" not in result

    def test_strips_ai_trailers_and_appends_env(self, env_signature: dict[str, str]) -> None:
        message = "fix: test\n\n关键变更:\n- change\n\nSession-ID: ai-fake\nModel-ID: gpt-5\nWorkbench-Name: Cindy\n"
        result = inject_environment_signature(message)
        lines = result.split("\n")
        # Last three non-empty lines should be the env-injected trailers
        trailers = [l for l in lines if l.strip()][-3:]
        assert trailers == [
            "Session-ID: test-session-abc123",
            "Model-ID: glm-5.2",
            "Workbench-Name: WorkBuddy",
        ]

    def test_preserves_body_content(self, env_signature: dict[str, str]) -> None:
        message = "fix: test\n\n动机:\n- reason here\n\n关键变更:\n- change\n\nSession-ID: fake\n"
        result = inject_environment_signature(message)
        assert "动机:" in result
        assert "- reason here" in result
        assert "关键变更:" in result
        assert "- change" in result

    def test_blank_line_separates_body_from_trailers(self, env_signature: dict[str, str]) -> None:
        message = "fix: test\n\n关键变更:\n- change\n"
        result = inject_environment_signature(message)
        assert "\n\nSession-ID:" in result


class TestRunPrepareCommitMsg:
    def test_overwrites_file_in_place(self, env_signature: dict[str, str], tmp_path: Path) -> None:
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text(
            "fix: test\n\n关键变更:\n- change\n\nSession-ID: wrong\nModel-ID: gpt-5\n",
            encoding="utf-8",
        )
        error = run_prepare_commit_msg(str(msg_file))
        assert error is None
        content = msg_file.read_text(encoding="utf-8")
        assert "Session-ID: test-session-abc123" in content
        assert "Model-ID: glm-5.2" in content
        assert "wrong" not in content
        assert "gpt-5" not in content

    def test_no_env_vars_leaves_file_unchanged(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        for key in ("LDVH_MODEL_ID", "LDVH_WORKBENCH_NAME", "LDVH_SESSION_ID"):
            monkeypatch.delenv(key, raising=False)
        msg_file = tmp_path / "COMMIT_EDITMSG"
        original = "fix: test\n\n关键变更:\n- change\n"
        msg_file.write_text(original, encoding="utf-8")
        error = run_prepare_commit_msg(str(msg_file))
        assert error is None
        assert msg_file.read_text(encoding="utf-8") == original

    def test_nonexistent_file_returns_error(self, tmp_path: Path) -> None:
        error = run_prepare_commit_msg(str(tmp_path / "nonexistent"))
        assert error is not None
        assert "could not be resolved" in error
