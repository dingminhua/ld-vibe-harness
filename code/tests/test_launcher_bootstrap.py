from __future__ import annotations

import json
import os
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


def _system_python_without_ruamel_yaml() -> Path | None:
    """Return an interpreter that cannot import ruamel.yaml, so the launcher must fall back.

    Returns None when no such interpreter is available (e.g. /usr/bin/python3 is missing
    or happens to have ruamel.yaml installed), in which case the fallback test is skipped
    rather than forced to pass.
    """
    candidate = Path("/usr/bin/python3")
    if not candidate.exists():
        return None
    probe = subprocess.run(
        [str(candidate), "-c", "import ruamel.yaml"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode == 0:
        return None
    return candidate


_SYSTEM_PYTHON = _system_python_without_ruamel_yaml()


@pytest.mark.skipif(
    _SYSTEM_PYTHON is None,
    reason="No /usr/bin/python3 lacking ruamel.yaml available to exercise the fallback path",
)
def test_launcher_falls_back_to_venv_when_ruamel_yaml_absent() -> None:
    # Regression test: when the launching interpreter lacks ruamel.yaml (and, as on
    # macOS, may be Python 3.9 that cannot even parse the 3.10+ codebase), the launcher
    # must detect this and exec .venv/bin/python instead of crashing with a
    # ModuleNotFoundError/SyntaxError. This was the root cause behind the broken
    # commit-msg Git Gate and doctor subprocess failures.
    assert _SYSTEM_PYTHON is not None
    completed = _run_capabilities(_SYSTEM_PYTHON, clean_env=True)
    _assert_capabilities_response(completed)
    assert "Traceback" not in completed.stderr
