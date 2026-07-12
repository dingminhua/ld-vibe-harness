from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def assert_common_response(response: dict[str, Any]) -> None:
    assert set(response) == {
        "contract",
        "request_kind",
        "operation_key",
        "outcome",
        "summary",
        "result",
        "scope",
        "sources",
        "disclosure",
        "gaps",
        "changes",
        "verification",
        "diagnostics",
        "follow_up",
    }
    assert response["contract"] == "ldvh-helper-cli/1"
    assert response["request_kind"] in {"capabilities", "call"}
    assert response["outcome"] in {
        "ok",
        "no_change",
        "partial",
        "rejected",
        "unavailable",
        "invalid_request",
        "error",
    }
    assert isinstance(response["summary"], str) and response["summary"]
    assert set(response["scope"]) == {"requested", "completed", "not_completed", "governance_resolution"}
    assert isinstance(response["scope"]["requested"], list)
    assert isinstance(response["scope"]["completed"], list)
    assert isinstance(response["scope"]["not_completed"], list)
    assert response["scope"]["governance_resolution"] is None
    assert isinstance(response["sources"], list)
    assert response["disclosure"] is None
    assert isinstance(response["gaps"], list)
    assert response["changes"] == []
    assert response["verification"] == []
    assert isinstance(response["diagnostics"], list)
    assert set(response["follow_up"]) == {
        "summary",
        "required_inputs",
        "required_human_decisions",
        "resume_conditions",
        "suggested_operations",
    }
    assert response["follow_up"]["summary"]
    for field in (
        "required_inputs",
        "required_human_decisions",
        "resume_conditions",
        "suggested_operations",
    ):
        assert response["follow_up"][field] == []


@pytest.fixture
def current_specs_repository(tmp_path: Path) -> Path:
    """Copy the current V4 specification files into an isolated Git worktree."""

    repository = tmp_path / "repository"
    repository.mkdir()
    shutil.copytree(PROJECT_ROOT / "specs", repository / "specs")
    _git(repository, "init", "-q")
    return repository


def commit_all(repository: Path, message: str = "test fixture") -> None:
    _git(repository, "add", ".")
    _git(
        repository,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        message,
    )


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
    )
