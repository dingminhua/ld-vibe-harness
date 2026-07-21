"""Read-only diagnostics for the environment-neutral LDVH installation surface."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ldvh.helper.responses import CONTRACT as HELPER_CONTRACT
from ldvh.helper.responses import EXIT_CODES

CONTRACT = "ldvh-doctor/1"
HELPER_TIMEOUT_SECONDS = 20.0
_DISTRIBUTION_NAME = "ld-vibe-harness"
_USER_DOCUMENT_DIRECTORY = "_user_docs"
_USER_DOCUMENTS = ("LDVH接入面.md", "启用与AI环境接入.md")

type JsonObject = dict[str, Any]


class DoctorError(ValueError):
    """The doctor could not form a trustworthy read-only result."""


_SURFACES = (
    (
        "helper-cli",
        "ldvh",
        "Helper 公开能力发现与调用",
        "specs/04-Helper CLI 服务规范.md",
    ),
    (
        "context-recovery",
        "ldvh-context-recovery",
        "环境无关的有界上下文恢复",
        "specs/09-环境接入规范.md",
    ),
    (
        "git-commit-msg-gate",
        "ldvh-git-commit-msg",
        "原生 Git commit-msg 机械 Gate 核心",
        "specs/03-事实源与信息溯源规范.md",
    ),
    (
        "git-hook-manager",
        "ldvh-git-hook",
        "单个实际 worktree 的 Git Hook 检查与受控安装管理",
        "specs/09-环境接入规范.md",
    ),
)


def _absolute_directory(value: str, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise DoctorError(f"{field} must be a non-empty absolute directory path")
    path = Path(value)
    if not path.is_absolute():
        raise DoctorError(f"{field} must be an absolute directory path")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise DoctorError(f"{field} could not be resolved: {error}") from error
    if not resolved.is_dir():
        raise DoctorError(f"{field} does not identify a current directory")
    return resolved


def _absolute_executable(value: str, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise DoctorError(f"{field} must be a non-empty absolute executable path")
    path = Path(value)
    if not path.is_absolute():
        raise DoctorError(f"{field} must be an absolute executable path")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise DoctorError(f"{field} could not be resolved: {error}") from error
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise DoctorError(f"{field} does not identify a current executable file")
    return resolved


def _work_object_locator(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DoctorError("work_object_locator must be a non-empty path string")
    return value


def _invoke_helper(
    helper: Path,
    *,
    cwd: Path,
    arguments: list[str],
    request: JsonObject,
) -> JsonObject:
    try:
        completed = subprocess.run(
            [str(helper), *arguments],
            cwd=cwd,
            input=json.dumps(request, ensure_ascii=False),
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            timeout=HELPER_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise DoctorError(f"Helper invocation failed: {error}") from error
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise DoctorError("Helper did not return one JSON response") from error
    if not isinstance(response, dict) or response.get("contract") != HELPER_CONTRACT:
        raise DoctorError(f"Helper response contract must be {HELPER_CONTRACT}")
    outcome = response.get("outcome")
    if not isinstance(outcome, str) or EXIT_CODES.get(outcome) != completed.returncode:
        raise DoctorError("Helper response outcome and process exit code do not match")
    expected_kind = arguments[0]
    expected_operation = None if len(arguments) == 1 else arguments[1]
    if response.get("request_kind") != expected_kind or response.get("operation_key") != expected_operation:
        raise DoctorError("Helper response identity does not match the requested operation")
    return response


def _distribution() -> JsonObject:
    try:
        distribution = importlib.metadata.distribution(_DISTRIBUTION_NAME)
    except importlib.metadata.PackageNotFoundError as error:
        raise DoctorError(f"installed distribution {_DISTRIBUTION_NAME} is unavailable") from error
    return {"name": _DISTRIBUTION_NAME, "version": distribution.version}


def _entry_point_path(directory: Path, name: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return directory / f"{name}{suffix}"


def _integration_surfaces(helper: Path) -> list[JsonObject]:
    surfaces: list[JsonObject] = []
    for surface_key, entry_point, role, source in _SURFACES:
        path = helper if entry_point == "ldvh" else _entry_point_path(helper.parent, entry_point)
        available = path.is_file() and os.access(path, os.X_OK)
        surfaces.append(
            {
                "surface_key": surface_key,
                "entry_point": entry_point,
                "role": role,
                "state": "available" if available else "missing",
                "executable": str(path),
                "source_ref": source,
            }
        )
    return surfaces


def _documentation() -> list[JsonObject]:
    package = Path(__file__).resolve().parent
    installed = package / _USER_DOCUMENT_DIRECTORY
    colocated_source = package.parents[1] / "docs"
    directory = installed if installed.is_dir() else colocated_source
    return [
        {
            "name": name,
            "path": str(directory / name),
            "state": "available" if (directory / name).is_file() else "missing",
        }
        for name in _USER_DOCUMENTS
    ]


def _governance_summary(response: JsonObject, workspace: Path, locator: str) -> JsonObject:
    result = response.get("result")
    result = result if isinstance(result, dict) else {}
    resolutions = result.get("object_resolutions")
    project_ids = set()
    if isinstance(resolutions, list):
        project_ids = {
            item.get("governed_project_id")
            for item in resolutions
            if isinstance(item, dict) and item.get("status") == "governed"
        }
    project_ids.discard(None)
    return {
        "workspace_root": str(workspace),
        "work_object_locator": locator,
        "helper_outcome": response["outcome"],
        "config_status": result.get("config_status"),
        "scope_status": result.get("scope_status"),
        "governed_project_id": next(iter(project_ids)) if len(project_ids) == 1 else None,
    }


def run_doctor(*, workspace_root: str, work_object_locator: str, helper_executable: str) -> JsonObject:
    """Observe only explicit LDVH inputs and installed entry points."""

    workspace = _absolute_directory(workspace_root, "workspace_root")
    locator = _work_object_locator(work_object_locator)
    helper = _absolute_executable(helper_executable, "helper_executable")
    distribution = _distribution()
    capabilities = _invoke_helper(
        helper,
        cwd=workspace,
        arguments=["capabilities"],
        request={"response_profile": "compact"},
    )
    if capabilities["outcome"] != "ok":
        raise DoctorError(f"Helper capabilities are unavailable: {capabilities['outcome']}")
    governance = _invoke_helper(
        helper,
        cwd=workspace,
        arguments=["call", "resolve-governance-scope"],
        request={
            "work_object_locators": [locator],
            "arguments": {"workspace_root": str(workspace)},
            "response_profile": "compact",
        },
    )
    configuration = _governance_summary(governance, workspace, locator)
    surfaces = _integration_surfaces(helper)
    documentation = _documentation()
    operations = capabilities.get("result", {}).get("operations")
    operation_count = len(operations) if isinstance(operations, list) else 0
    checks: list[JsonObject] = [
        {
            "check": "helper_capabilities",
            "status": "passed",
            "summary": f"Helper returned {operation_count} current operations",
        },
        {
            "check": "configuration",
            "status": (
                "passed"
                if configuration["helper_outcome"] == "ok" and configuration["config_status"] == "valid"
                else "attention"
            ),
            "summary": (
                f"Helper outcome is {configuration['helper_outcome']}; "
                f"configuration status is {configuration['config_status'] or 'unavailable'}"
            ),
        },
        {
            "check": "governance",
            "status": (
                "passed"
                if configuration["helper_outcome"] == "ok" and configuration["scope_status"] == "governed_single"
                else "attention"
            ),
            "summary": (
                f"Helper outcome is {configuration['helper_outcome']}; "
                f"governance scope is {configuration['scope_status'] or 'unavailable'}"
            ),
        },
        {
            "check": "integration_surfaces",
            "status": "passed" if all(item["state"] == "available" for item in surfaces) else "attention",
            "summary": f"{sum(item['state'] == 'available' for item in surfaces)}/{len(surfaces)} surfaces are present",
        },
        {
            "check": "user_documentation",
            "status": "passed" if all(item["state"] == "available" for item in documentation) else "attention",
            "summary": (
                f"{sum(item['state'] == 'available' for item in documentation)}/{len(documentation)} "
                "user documents are present"
            ),
        },
    ]
    status = "ready" if all(item["status"] == "passed" for item in checks) else "attention"
    return {
        "contract": CONTRACT,
        "status": status,
        "distribution": distribution,
        "helper": {
            "executable": str(helper),
            "contract": HELPER_CONTRACT,
            "capabilities_outcome": capabilities["outcome"],
            "operation_count": operation_count,
        },
        "configuration": configuration,
        "integration_surfaces": surfaces,
        "documentation": documentation,
        "checks": checks,
        "limitations": [
            "doctor did not inspect or modify any target AI development environment",
            (
                "static entry points do not prove installation into, automatic triggering by, "
                "or verification of an environment"
            ),
        ],
        "diagnostics": [],
    }


def _unavailable(error: Exception) -> JsonObject:
    return {
        "contract": CONTRACT,
        "status": "unavailable",
        "distribution": None,
        "helper": None,
        "configuration": None,
        "integration_surfaces": [],
        "documentation": [],
        "checks": [],
        "limitations": ["doctor did not change any configuration or environment"],
        "diagnostics": [{"summary": str(error), "exception_type": type(error).__name__}],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run read-only LDVH installation diagnostics")
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--work-object-locator", required=True)
    parser.add_argument("--helper-executable", required=True)
    return parser


def main(arguments: list[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    try:
        response = run_doctor(
            workspace_root=parsed.workspace_root,
            work_object_locator=parsed.work_object_locator,
            helper_executable=parsed.helper_executable,
        )
    except (DoctorError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        response = _unavailable(error)
    payload = json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n"
    sys.stdout.buffer.write(payload.encode("utf-8"))
    return 1 if response["status"] == "unavailable" else 0


if __name__ == "__main__":
    raise SystemExit(main())
