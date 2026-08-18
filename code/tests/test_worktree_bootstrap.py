from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ldvh import worktree_bootstrap

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def _committed_worktree(tmp_path: Path) -> Path:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    _git(worktree, "init", "-q")
    (worktree / "ldvh-base").mkdir()
    (worktree / "ldvh-base" / "fact.yaml").write_text("fact: unchanged\n", encoding="utf-8")
    (worktree / "requirements.txt").write_text("ruamel.yaml>=0.18.10,<0.19\n", encoding="utf-8")
    (worktree / "requirements-dev.txt").write_text("-r requirements.txt\n", encoding="utf-8")
    _git(worktree, "add", ".")
    _git(
        worktree,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "fixture",
    )
    return worktree


def _response(capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    return json.loads(capsys.readouterr().out)


def test_check_reports_ready_for_the_current_local_venv(monkeypatch, capsys) -> None:
    monkeypatch.chdir(PROJECT_ROOT)

    assert worktree_bootstrap.run(PROJECT_ROOT, ["--check"]) == 0

    response = _response(capsys)
    assert response["contract"] == "ldvh-worktree-bootstrap/1"
    assert response["status"] == "ready"
    assert response["worktree"] == str(PROJECT_ROOT)
    assert response["python"]["path"] == str(PROJECT_ROOT / ".venv" / "bin" / "python")
    assert {item["check"] for item in response["checks"]} >= {
        "local_venv",
        "python",
        "requirements",
        "capabilities",
    }


def test_check_reports_missing_ruamel_yaml_with_its_requirement_file(monkeypatch) -> None:
    monkeypatch.setattr(worktree_bootstrap, "_venv_python", lambda _: Path(sys.executable))
    monkeypatch.setattr(
        worktree_bootstrap,
        "_dependency_availability",
        lambda _python, requirements: {package: package != "ruamel.yaml" for package, _ in requirements},
    )

    response = worktree_bootstrap._check(PROJECT_ROOT)

    assert response["status"] == "not_ready"
    assert {item["package"] for item in response["missing_packages"]} == {"ruamel.yaml"}
    assert response["missing_packages"][0]["requirements_file"] == "requirements.txt"
    assert {item["status"] for item in response["checks"]} >= {"not_ready"}
    assert response["recovery"]["available"] is True
    assert response["recovery"]["kind"] == "bootstrap"
    assert response["recovery"]["command"] == "./ldvh worktree-bootstrap"
    assert response["recovery"]["verification_command"] == "./ldvh worktree-bootstrap --check"
    assert response["recovery"]["requires_human"] is False


def test_check_discovers_missing_ruamel_yaml_in_a_real_isolated_venv(tmp_path: Path) -> None:
    worktree = _committed_worktree(tmp_path)
    local_venv = worktree / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(local_venv)], check=True)

    response = worktree_bootstrap._check(worktree)

    assert response["status"] == "not_ready"
    assert {item["package"] for item in response["missing_packages"]} == {"ruamel.yaml"}
    assert response["missing_packages"][0]["requirements_file"] == "requirements.txt"
    assert response["recovery"]["available"] is True
    assert response["recovery"]["kind"] == "bootstrap"
    assert response["recovery"]["command"] == "./ldvh worktree-bootstrap"
    assert response["recovery"]["verification_command"] == "./ldvh worktree-bootstrap --check"
    assert response["recovery"]["requires_human"] is False


def test_check_never_uses_an_adjacent_worktree_venv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    worktree = _committed_worktree(tmp_path)
    sibling = tmp_path / "sibling-worktree" / ".venv" / "bin"
    sibling.mkdir(parents=True)
    sibling_marker = tmp_path / "sibling-was-invoked"
    sibling_python = sibling / "python"
    sibling_python.write_text(f"#!/bin/sh\ntouch {sibling_marker}\nexit 99\n", encoding="utf-8")
    sibling_python.chmod(0o755)
    monkeypatch.chdir(worktree)

    assert worktree_bootstrap.run(worktree, ["--check"]) == 1

    response = _response(capsys)
    assert response["status"] == "not_ready"
    assert response["python"]["path"] == str(worktree / ".venv" / "bin" / "python")
    assert {item["package"] for item in response["missing_packages"]} >= {"ruamel.yaml"}
    assert response["recovery"]["available"] is True
    assert response["recovery"]["kind"] == "bootstrap"
    assert response["recovery"]["command"] == "./ldvh worktree-bootstrap"
    assert response["recovery"]["verification_command"] == "./ldvh worktree-bootstrap --check"
    assert response["recovery"]["requires_human"] is False
    assert str(sibling) not in json.dumps(response)
    assert not sibling_marker.exists()


def test_repeated_check_is_idempotent(monkeypatch, capsys) -> None:
    monkeypatch.chdir(PROJECT_ROOT)

    assert worktree_bootstrap.run(PROJECT_ROOT, ["--check"]) == 0
    first = _response(capsys)
    assert worktree_bootstrap.run(PROJECT_ROOT, ["--check"]) == 0
    second = _response(capsys)

    assert first == second


def test_bootstrap_reuses_an_existing_local_venv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = tmp_path / "worktree"
    local_python = worktree / ".venv" / "bin" / "python"
    local_python.parent.mkdir(parents=True)
    local_python.write_text("local venv marker\n", encoding="utf-8")
    calls: list[list[str]] = []
    monkeypatch.setattr(worktree_bootstrap, "_venv_python", lambda _: local_python)
    monkeypatch.setattr(
        worktree_bootstrap,
        "_python_identity",
        lambda _: ({"path": str(sys.executable), "version": [3, 12, 0]}, None),
    )

    def successful_run(arguments: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        calls.append(arguments)
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr(worktree_bootstrap, "_run", successful_run)

    assert worktree_bootstrap._bootstrap(worktree, Path(sys.executable)) is None
    assert worktree_bootstrap._bootstrap(worktree, Path(sys.executable)) is None

    assert calls == [
        [str(local_python), "-m", "pip", "--version"],
        [str(local_python), "-m", "pip", "install", "--requirement", "requirements-dev.txt"],
        [str(local_python), "-m", "pip", "--version"],
        [str(local_python), "-m", "pip", "install", "--requirement", "requirements-dev.txt"],
    ]


def test_bootstrap_prefers_existing_supported_local_venv_over_old_requested_python(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = tmp_path / "worktree"
    local_python = worktree / ".venv" / "bin" / "python"
    local_python.parent.mkdir(parents=True)
    local_python.write_text("local venv marker\n", encoding="utf-8")
    calls: list[list[str]] = []

    def identity(python: Path):
        if python == local_python:
            return {"path": str(local_python), "version": [3, 12, 0]}, None
        return {"path": str(python), "version": [3, 9, 0]}, None

    monkeypatch.setattr(worktree_bootstrap, "_venv_python", lambda _: local_python)
    monkeypatch.setattr(worktree_bootstrap, "_python_identity", identity)

    def successful_run(arguments: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        calls.append(arguments)
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr(worktree_bootstrap, "_run", successful_run)

    assert worktree_bootstrap._bootstrap(worktree, Path("/old/python3.9")) is None
    assert calls == [
        [str(local_python), "-m", "pip", "--version"],
        [str(local_python), "-m", "pip", "install", "--requirement", "requirements-dev.txt"],
    ]


@pytest.mark.skipif(os.name == "nt", reason="fixture capabilities launcher is POSIX-only")
def test_bootstrap_is_repeatable_without_changing_facts_or_git_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    worktree = _committed_worktree(tmp_path)
    (worktree / "requirements.txt").write_text("", encoding="utf-8")
    (worktree / "requirements-dev.txt").write_text("", encoding="utf-8")
    (worktree / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    launcher = worktree / "ldvh"
    launcher.write_text("#!/bin/sh\nprintf '%s\\n' '{\"outcome\":\"ok\"}'\n", encoding="utf-8")
    launcher.chmod(0o755)
    _git(worktree, "add", ".")
    _git(
        worktree,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "bootstrap fixture",
    )
    fact = worktree / "ldvh-base" / "fact.yaml"
    before_head = _git(worktree, "rev-parse", "HEAD")
    before_status = _git(worktree, "status", "--porcelain=v1")
    before_fact = fact.read_bytes()
    monkeypatch.chdir(worktree)

    assert worktree_bootstrap.run(worktree, []) == 0
    first = _response(capsys)
    assert worktree_bootstrap.run(worktree, []) == 0
    second = _response(capsys)

    assert first["status"] == second["status"] == "ready"
    assert (worktree / ".venv" / "bin" / "python").is_file()
    assert _git(worktree, "rev-parse", "HEAD") == before_head
    assert _git(worktree, "status", "--porcelain=v1") == before_status
    assert fact.read_bytes() == before_fact


@pytest.mark.skipif(os.name == "nt", reason="fixture capabilities launcher is POSIX-only")
def test_bootstrap_reports_a_real_pip_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    worktree = _committed_worktree(tmp_path)
    (worktree / "requirements-dev.txt").write_text("--not-a-pip-option\n", encoding="utf-8")
    monkeypatch.chdir(worktree)

    assert worktree_bootstrap.run(worktree, []) == 1

    response = _response(capsys)
    assert response["status"] == "unavailable"
    assert any("not-a-pip-option" in item for item in response["diagnostics"])


def test_check_does_not_change_facts_or_git_history(tmp_path: Path, monkeypatch, capsys) -> None:
    worktree = _committed_worktree(tmp_path)
    fact = worktree / "ldvh-base" / "fact.yaml"
    before_head = _git(worktree, "rev-parse", "HEAD")
    before_status = _git(worktree, "status", "--porcelain=v1")
    before_fact = fact.read_bytes()
    monkeypatch.chdir(worktree)

    assert worktree_bootstrap.run(worktree, ["--check"]) == 1

    response = _response(capsys)
    assert response["status"] == "not_ready"
    assert response["recovery"]["available"] is True
    assert response["recovery"]["kind"] == "bootstrap"
    assert response["recovery"]["command"] == "./ldvh worktree-bootstrap"
    assert response["recovery"]["verification_command"] == "./ldvh worktree-bootstrap --check"
    assert response["recovery"]["requires_human"] is False
    assert _git(worktree, "rev-parse", "HEAD") == before_head
    assert _git(worktree, "status", "--porcelain=v1") == before_status
    assert fact.read_bytes() == before_fact
