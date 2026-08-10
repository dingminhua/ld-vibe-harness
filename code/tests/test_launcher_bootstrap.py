from __future__ import annotations

import json
import os
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = PROJECT_ROOT / "ldvh"
VENV_BIN = PROJECT_ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin")
VENV_PYTHON = VENV_BIN / "python.exe" if os.name == "nt" else VENV_BIN / "python"

CAPABILITIES_REQUEST = json.dumps({"response_profile": "compact"})


def _run_capabilities(python: Path, *, clean_env: bool = False) -> subprocess.CompletedProcess[str]:
    env: dict[str, str] | None = None
    if clean_env:
        # Scrub PYTHONPATH/PYTHONHOME and the venv from PATH so the target interpreter
        # cannot see the venv's site-packages; the launcher must fall back on its own.
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": os.environ.get("HOME", ""),
            "TMPDIR": os.environ.get("TMPDIR", ""),
        }
    return subprocess.run(
        [str(python), str(LAUNCHER), "capabilities"],
        input=CAPABILITIES_REQUEST,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
        env=env,
    )


def _assert_capabilities_response(completed: subprocess.CompletedProcess[str]) -> None:
    assert completed.returncode == 0, f"launcher failed: {completed.stderr}"
    response = json.loads(completed.stdout)
    assert response["contract"] == "ldvh-helper-cli/2"
    assert response["outcome"] == "ok"
    assert response["result"]["mode"] == "discovery"
    assert len(response["result"]["operations"]) > 0


def test_launcher_runs_directly_on_venv_python() -> None:
    # The venv interpreter has ruamel.yaml, so the launcher runs directly without
    # falling back. This is the normal developer/CI path.
    assert VENV_PYTHON.exists(), f"venv python missing at {VENV_PYTHON}"
    completed = _run_capabilities(VENV_PYTHON)
    _assert_capabilities_response(completed)


def test_launcher_falls_back_to_its_local_venv_when_ruamel_yaml_absent() -> None:
    # ``-S`` deterministically hides the invoking interpreter's site-packages. The
    # launcher must then hand off only to its own local .venv, regardless of whether
    # /usr/bin/python3 happens to have ruamel.yaml on the test machine.
    system_python = Path("/usr/bin/python3")
    assert system_python.exists(), "system Python is required for the fallback fixture"
    completed = subprocess.run(
        [str(system_python), "-S", str(LAUNCHER), "capabilities"],
        input=CAPABILITIES_REQUEST,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    _assert_capabilities_response(completed)
    assert "Traceback" not in completed.stderr


def test_launcher_reports_unsupported_python_without_false_missing_package(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = runpy.run_path(str(LAUNCHER), run_name="ldvh_launcher_test")
    message_builder = launcher["_runtime_unavailable_message"]
    monkeypatch.setitem(message_builder.__globals__, "_runtime_typing_compatible", lambda: False)
    monkeypatch.setitem(message_builder.__globals__, "_ruamel_yaml_available", lambda: True)

    message = message_builder()

    assert "python_requirement: Python 3.11+" in message
    assert "runtime_issue: unsupported Python typing runtime" in message
    assert "missing_package: ruamel.yaml" not in message
    assert "requirements_file: requirements.txt" not in message


def test_worktree_preflight_starts_before_runtime_dependencies(tmp_path: Path) -> None:
    assert VENV_PYTHON.exists(), f"venv python missing at {VENV_PYTHON}"
    isolated_launcher = tmp_path / "ldvh"
    isolated_code = tmp_path / "code" / "ldvh"
    isolated_code.mkdir(parents=True)
    shutil.copy2(LAUNCHER, isolated_launcher)
    shutil.copy2(PROJECT_ROOT / "code" / "ldvh" / "__init__.py", isolated_code / "__init__.py")
    shutil.copy2(
        PROJECT_ROOT / "code" / "ldvh" / "worktree_bootstrap.py",
        isolated_code / "worktree_bootstrap.py",
    )
    (tmp_path / "requirements.txt").write_text("ruamel.yaml>=0.18.10,<0.19\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("-r requirements.txt\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)

    completed = subprocess.run(
        [str(VENV_PYTHON), "-S", str(isolated_launcher), "worktree-bootstrap", "--check"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    response = json.loads(completed.stdout)
    assert response["contract"] == "ldvh-worktree-bootstrap/1"
    assert response["status"] == "not_ready"
    assert {item["package"] for item in response["missing_packages"]} == {"ruamel.yaml"}


def test_launcher_reports_preflight_when_doctor_cannot_import_runtime(tmp_path: Path) -> None:
    assert VENV_PYTHON.exists(), f"venv python missing at {VENV_PYTHON}"
    isolated_launcher = tmp_path / "ldvh"
    isolated_launcher.write_text(LAUNCHER.read_text(encoding="utf-8"), encoding="utf-8")
    isolated_launcher.chmod(0o755)

    completed = subprocess.run(
        [str(VENV_PYTHON), "-S", str(isolated_launcher), "doctor"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "LDVH source runtime is unavailable" in completed.stderr
    assert f"worktree: {tmp_path}" in completed.stderr
    assert "missing_package: ruamel.yaml" in completed.stderr
    assert "requirements_file: requirements.txt" in completed.stderr
    assert "status: unavailable" in completed.stderr
    assert "./ldvh worktree-bootstrap --check" in completed.stderr
