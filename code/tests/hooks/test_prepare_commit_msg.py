"""Tests for the single-snapshot commit signature injector."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ldvh.hooks.prepare_commit_msg import (
    _strip_signature_trailers,
    inject_environment_signature,
    run_prepare_commit_msg,
)


def _signature(**overrides: str | None) -> str:
    return json.dumps(
        {
            "product_name": "Cindy",
            "model_name": "GLM-5.2",
            "agent_runtime_name": "Codex CLI",
            **overrides,
        }
    )


@pytest.fixture
def signature_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LDVH_SIGNATURE", _signature())


def test_strips_retired_and_new_signature_trailers() -> None:
    lines = ["fix: test", "", "Session-ID: old", "Model-ID: old", "LDVH-Model-Name: new"]
    assert _strip_signature_trailers(lines) == ["fix: test"]


def test_environment_snapshot_replaces_self_reported_trailers(signature_env: None) -> None:
    message = "fix: test\n\n关键变更:\n- change\n\nModel-ID: self-reported\nWorkbench-Name: fake"
    result = inject_environment_signature(message)
    assert "Model-ID:" not in result
    assert "LDVH-Product-Name: Cindy" in result
    assert "LDVH-Model-Name: glm-5.2" in result
    assert "LDVH-Agent-Runtime-Name: codex-cli" in result


def test_partial_snapshot_omits_unavailable_trailer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LDVH_SIGNATURE", _signature(model_name=None, agent_runtime_name=None))
    result = inject_environment_signature("fix: test\n\nLDVH-Model-Name: fabricated")
    assert "LDVH-Product-Name: Cindy" in result
    assert "LDVH-Model-Name:" not in result


def test_empty_or_invalid_snapshot_cannot_preserve_self_report(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LDVH_SIGNATURE", _signature(product_name=None, model_name=None, agent_runtime_name=None))
    assert inject_environment_signature("fix: test\n\nLDVH-Product-Name: fabricated") == "fix: test"


def test_run_prepare_commit_msg_rewrites_file(signature_env: None, tmp_path: Path) -> None:
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text("fix: test\n\n关键变更:\n- change\n\nSession-ID: old", encoding="utf-8")
    assert run_prepare_commit_msg(str(message)) is None
    content = message.read_text(encoding="utf-8")
    assert "Session-ID:" not in content
    assert "LDVH-Product-Name: Cindy" in content
