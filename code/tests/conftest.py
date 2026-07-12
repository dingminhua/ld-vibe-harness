from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
