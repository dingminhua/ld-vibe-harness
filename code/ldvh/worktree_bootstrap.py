"""Prepare and verify an LDVH source worktree's local Python runtime.

This module intentionally uses only the Python standard library.  The root launcher
must be able to invoke it before ``ruamel.yaml`` or any other LDVH runtime dependency
is importable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

CONTRACT = "ldvh-worktree-bootstrap/1"
PROJECT_PYTHON = (3, 11)
REQUIREMENT_IMPORTS = {
    "pytest-xdist": "xdist",
}
_REQUIREMENT_NAME = re.compile(r"^([A-Za-z0-9_.-]+)")


def _venv_python(worktree: Path) -> Path:
    if os.name == "nt":
        return worktree / ".venv" / "Scripts" / "python.exe"
    return worktree / ".venv" / "bin" / "python"


def _venv_bin(worktree: Path) -> Path:
    return _venv_python(worktree).parent


def _run(arguments: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def _git(worktree: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", "-C", str(worktree), *arguments])


def _requirement_import(name: str) -> str:
    return REQUIREMENT_IMPORTS.get(name.lower(), name.replace("-", "_").replace(".", "."))


def _requirements(worktree: Path, filename: str, visited: set[Path] | None = None) -> list[tuple[str, str]]:
    """Read the project requirement files without invoking pip or importing packages."""

    visited = set() if visited is None else visited
    path = (worktree / filename).resolve()
    if path in visited:
        return []
    visited.add(path)
    if not path.is_file():
        return []

    declared: list[tuple[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r ") or line.startswith("--requirement "):
            included = line.split(maxsplit=1)[1]
            declared.extend(_requirements(worktree, included, visited))
            continue
        match = _REQUIREMENT_NAME.match(line)
        if match:
            declared.append((match.group(1), filename))
    return declared


def _python_identity(python: Path) -> tuple[dict[str, Any] | None, str | None]:
    completed = _run(
        [
            str(python),
            "-c",
            "import json, sys; print(json.dumps({'path': sys.executable, 'version': list(sys.version_info[:3])}))",
        ]
    )
    if completed.returncode != 0:
        return None, completed.stderr.strip() or "the interpreter could not start"
    try:
        identity = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, "the interpreter did not report a JSON identity"
    if not isinstance(identity, dict) or not isinstance(identity.get("version"), list):
        return None, "the interpreter reported an invalid identity"
    return identity, None


def _python_meets_requirement(identity: dict[str, Any] | None) -> bool:
    return identity is not None and tuple(identity["version"]) >= PROJECT_PYTHON


def _select_bootstrap_python(worktree: Path, requested: Path) -> Path:
    """Prefer a supported interpreter already provisioned for this worktree.

    A linked worktree may be invoked by an older system ``python3`` while its local
    virtualenv already contains the supported runtime. Reusing that local interpreter
    keeps bootstrap self-contained and never reaches into a sibling worktree.
    """
    local = _venv_python(worktree)
    if local.is_file():
        identity, _ = _python_identity(local)
        if _python_meets_requirement(identity):
            return local
    if _python_meets_requirement(_python_identity(requested)[0]):
        return requested
    for name in ("python3.13", "python3.12", "python3.11"):
        candidate = shutil.which(name)
        if candidate is None:
            continue
        path = Path(candidate)
        if _python_meets_requirement(_python_identity(path)[0]):
            return path
    return requested


def _dependency_availability(python: Path, requirements: list[tuple[str, str]]) -> dict[str, bool]:
    imports = {package: _requirement_import(package) for package, _ in requirements}
    script = """
import importlib.util
import json
import sys
imports = json.loads(sys.argv[1])
availability = {}
for package, module in imports.items():
    try:
        availability[package] = importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        availability[package] = False
print(json.dumps(availability))
"""
    completed = _run([str(python), "-c", script, json.dumps(imports)])
    if completed.returncode != 0:
        return {package: False for package in imports}
    try:
        availability = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {package: False for package in imports}
    if not isinstance(availability, dict):
        return {package: False for package in imports}
    return {package: availability.get(package) is True for package in imports}


def _worktree_identity(source_root: Path) -> tuple[Path | None, str | None]:
    current = Path.cwd().resolve()
    top_level = _git(current, "rev-parse", "--show-toplevel")
    if top_level.returncode != 0:
        return None, "the current path is not inside a Git worktree"
    worktree = Path(top_level.stdout.strip()).resolve()
    if current != worktree:
        return None, f"run this command from the target worktree root: {worktree}"
    if worktree != source_root:
        return None, f"the current worktree {worktree} does not match this LDVH source root {source_root}"
    listed = _git(worktree, "worktree", "list", "--porcelain")
    if listed.returncode != 0 or f"worktree {worktree}" not in listed.stdout:
        return None, "Git did not confirm the target in its registered worktree list"
    return worktree, None


def _check(worktree: Path) -> dict[str, Any]:
    requirements = _requirements(worktree, "requirements-dev.txt")
    requirement_files = sorted({filename for _, filename in requirements})
    checks: list[dict[str, str]] = [{"check": "git_worktree", "status": "passed"}]
    diagnostics: list[str] = []
    python = _venv_python(worktree)
    python_identity: dict[str, Any] | None = None
    missing: list[dict[str, str]] = []

    if not python.is_file() or not os.access(python, os.X_OK):
        checks.append({"check": "local_venv", "status": "not_ready"})
        missing.extend(
            {"package": package, "requirements_file": requirement_file}
            for package, requirement_file in requirements
        )
        diagnostics.append(f"local venv interpreter is missing: {python}")
    else:
        checks.append({"check": "local_venv", "status": "passed"})
        python_identity, error = _python_identity(python)
        if error is not None:
            checks.append({"check": "python", "status": "unavailable"})
            diagnostics.append(f"local venv interpreter is unavailable: {error}")
        else:
            version = tuple(python_identity["version"])
            if version < PROJECT_PYTHON:
                checks.append({"check": "python", "status": "not_ready"})
                diagnostics.append(
                    f"Python {'.'.join(str(part) for part in version)} does not meet the required "
                    f"{PROJECT_PYTHON[0]}.{PROJECT_PYTHON[1]}+"
                )
            else:
                checks.append({"check": "python", "status": "passed"})
                availability = _dependency_availability(python, requirements)
                for package, requirement_file in requirements:
                    if not availability.get(package, False):
                        missing.append({"package": package, "requirements_file": requirement_file})
                if missing:
                    checks.append({"check": "requirements", "status": "not_ready"})
                    diagnostics.append("declared dependencies are unavailable in the local venv")
                else:
                    checks.append({"check": "requirements", "status": "passed"})
                    environment = os.environ.copy()
                    environment["PATH"] = os.pathsep.join((str(_venv_bin(worktree)), environment.get("PATH", "")))
                    completed = subprocess.run(
                        [str(worktree / "ldvh"), "capabilities"],
                        cwd=worktree,
                        stdin=subprocess.DEVNULL,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        check=False,
                        env=environment,
                    )
                    try:
                        response = json.loads(completed.stdout)
                    except json.JSONDecodeError:
                        response = None
                    if completed.returncode == 0 and isinstance(response, dict) and response.get("outcome") == "ok":
                        checks.append({"check": "capabilities", "status": "passed"})
                    else:
                        checks.append({"check": "capabilities", "status": "unavailable"})
                        diagnostics.append(
                            "./ldvh capabilities </dev/null did not return a successful Helper response"
                        )

    statuses = {item["status"] for item in checks}
    status = "ready"
    if "unavailable" in statuses:
        status = "unavailable"
    elif "not_ready" in statuses:
        status = "not_ready"
    return {
        "contract": CONTRACT,
        "status": status,
        "worktree": str(worktree),
        "python": python_identity
        if python_identity is not None
        else {"path": str(python), "version": None},
        "requirements_files": requirement_files or ["requirements.txt", "requirements-dev.txt"],
        "missing_packages": missing,
        "checks": checks,
        "diagnostics": diagnostics,
    }


def _bootstrap(worktree: Path, bootstrap_python: Path) -> str | None:
    venv = _venv_python(worktree)
    bootstrap_python = _select_bootstrap_python(worktree, bootstrap_python)
    identity, error = _python_identity(bootstrap_python)
    if error is not None:
        return f"bootstrap interpreter is unavailable: {error}"
    if not _python_meets_requirement(identity):
        actual_version = ".".join(str(part) for part in identity["version"])
        required_version = f"{PROJECT_PYTHON[0]}.{PROJECT_PYTHON[1]}+"
        return (
            f"bootstrap interpreter {identity['path']} is Python {actual_version}; "
            f"Python {required_version} is required; pass --python with a supported interpreter"
        )
    if not venv.is_file():
        created = _run([str(bootstrap_python), "-m", "venv", str(worktree / ".venv")])
        if created.returncode != 0:
            return created.stderr.strip() or "creating the local .venv failed"
    pip_probe = _run([str(venv), "-m", "pip", "--version"])
    if pip_probe.returncode != 0:
        seeded = _run([str(venv), "-m", "ensurepip", "--upgrade"])
        if seeded.returncode != 0:
            return seeded.stderr.strip() or "seeding pip in the local .venv failed"
    installed = _run([str(venv), "-m", "pip", "install", "--requirement", "requirements-dev.txt"], cwd=worktree)
    if installed.returncode != 0:
        return installed.stderr.strip() or "preparing declared third-party dependencies failed"
    return None


def run(source_root: Path, arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare or check this LDVH worktree's local runtime")
    parser.add_argument(
        "--check",
        action="store_true",
        help="only report worktree readiness; do not modify the environment",
    )
    parser.add_argument(
        "--python",
        type=Path,
        default=Path(sys.executable),
        help="Python 3.11+ used to create .venv",
    )
    parsed = parser.parse_args(arguments)

    worktree, error = _worktree_identity(source_root.resolve())
    if error is not None:
        response = {
            "contract": CONTRACT,
            "status": "unavailable",
            "worktree": str(Path.cwd().resolve()),
            "python": {"path": str(_venv_python(source_root)), "version": None},
            "requirements_files": ["requirements.txt", "requirements-dev.txt"],
            "missing_packages": [],
            "checks": [{"check": "git_worktree", "status": "unavailable"}],
            "diagnostics": [error],
        }
    else:
        if not parsed.check:
            bootstrap_error = _bootstrap(worktree, parsed.python.resolve())
            if bootstrap_error is not None:
                response = _check(worktree)
                response["status"] = "unavailable"
                response["diagnostics"].append(bootstrap_error)
            else:
                response = _check(worktree)
        else:
            response = _check(worktree)
    sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0 if response["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(run(Path(__file__).resolve().parents[2]))
