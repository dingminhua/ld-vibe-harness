"""Read-only diagnostics for the source-native LDVH integration surface."""

from __future__ import annotations

import argparse
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
type JsonObject = dict[str, Any]


class DoctorError(ValueError):
    """The doctor could not form a trustworthy read-only result."""


_SURFACES = (
    (
        "helper-cli",
        None,
        "Helper 公开能力发现与调用",
        "specs/04-Helper CLI 服务规范.md",
        "code/ldvh/cli.py",
    ),
    (
        "work-context-core",
        "work-context",
        "环境无关的工作上下文规则引导核心",
        "specs/09-环境接入规范.md",
        "code/ldvh/work_context.py",
    ),
    (
        "context-recovery",
        "context-recovery",
        "环境无关的有界上下文恢复",
        "specs/09-环境接入规范.md",
        "code/ldvh/hooks/context_recovery.py",
    ),
    (
        "git-commit-msg-gate",
        "git-commit-msg",
        "原生 Git Gate（commit-msg）机械检查核心",
        "specs/03-事实源与信息溯源规范.md",
        "code/ldvh/hooks/commit_msg.py",
    ),
    (
        "git-hook-manager",
        "git-hook",
        "Git common-dir 级 Hook 检查与受控部署管理",
        "specs/09-环境接入规范.md",
        "code/ldvh/git_hooks/commit_msg.py",
    ),
    (
        "doctor",
        "doctor",
        "源码仓库身份、管辖与交付面只读诊断",
        "specs/09-环境接入规范.md",
        "code/ldvh/doctor.py",
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
    # On Windows (os.name == "nt") a shell-script launcher without .bat/.cmd extension
    # is not a valid Win32 PE — Python's subprocess.CreateProcess raises WinError 193.
    # Wrap via POSIX sh (Git Bash/MSYS) so the shebang resolves to a usable interpreter.
    argv = [str(helper), *arguments]
    command = argv if os.name != "nt" else ["sh", "-c", "exec \"$@\"", "--", *argv]
    try:
        completed = subprocess.run(
            command,
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


def _git(source_root: Path, *arguments: str, allow_failure: bool = False) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(source_root), *arguments],
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        if allow_failure:
            return None
        raise DoctorError(f"Git source identity failed: {completed.stderr.strip() or 'unknown error'}")
    return completed.stdout.strip()


def _source_repository(helper: Path) -> JsonObject:
    source_root = helper.parent.resolve()
    expected_launcher = source_root / "ldvh"
    if helper != expected_launcher or not (source_root / "code/ldvh/__init__.py").is_file():
        raise DoctorError("helper_executable must be the stable launcher in an LDVH source repository root")
    git_root = _git(source_root, "rev-parse", "--show-toplevel")
    if git_root is None or Path(git_root).resolve() != source_root:
        raise DoctorError("helper_executable source root does not match the actual Git worktree")
    revision = _git(source_root, "rev-parse", "HEAD")
    status = _git(source_root, "status", "--porcelain=v1")
    remote = _git(source_root, "config", "--get", "remote.origin.url", allow_failure=True)
    return {
        "root": str(source_root),
        "revision": revision,
        "working_tree_status": "clean" if not status else "dirty",
        "remote": remote,
    }


def _integration_surfaces(helper: Path, source_root: Path) -> list[JsonObject]:
    surfaces: list[JsonObject] = []
    launcher_available = helper == source_root / "ldvh" and helper.is_file() and os.access(helper, os.X_OK)
    for surface_key, subcommand, role, source, implementation in _SURFACES:
        implementation_path = source_root / implementation
        available = launcher_available and implementation_path.is_file()
        surfaces.append(
            {
                "surface_key": surface_key,
                "entry_point": "ldvh" if subcommand is None else f"ldvh {subcommand}",
                "role": role,
                "state": "available" if available else "missing",
                "executable": str(helper),
                "implementation": implementation,
                "source_ref": source,
            }
        )
    return surfaces


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
    """Observe only explicit inputs and the confirmed LDVH source repository."""

    workspace = _absolute_directory(workspace_root, "workspace_root")
    locator = _work_object_locator(work_object_locator)
    helper = _absolute_executable(helper_executable, "helper_executable")
    source_repository = _source_repository(helper)
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
    surfaces = _integration_surfaces(helper, Path(source_repository["root"]))
    operations = capabilities.get("result", {}).get("operations")
    operation_count = len(operations) if isinstance(operations, list) else 0
    checks: list[JsonObject] = [
        {
            "check": "source_repository",
            "status": "passed",
            "summary": f"LDVH source repository is {source_repository['root']} at {source_repository['revision']}",
        },
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
    ]
    status = "ready" if all(item["status"] == "passed" for item in checks) else "attention"
    return {
        "contract": CONTRACT,
        "status": status,
        "source_repository": source_repository,
        "helper": {
            "executable": str(helper),
            "contract": HELPER_CONTRACT,
            "capabilities_outcome": capabilities["outcome"],
            "operation_count": operation_count,
        },
        "configuration": configuration,
        "integration_surfaces": surfaces,
        "checks": checks,
        "limitations": [
            "doctor did not inspect or modify any target AI development environment",
            (
                "static source surfaces do not prove deployment into, automatic triggering by, "
                "or verification of an environment"
            ),
        ],
        "diagnostics": [],
    }


def _unavailable(error: Exception) -> JsonObject:
    return {
        "contract": CONTRACT,
        "status": "unavailable",
        "source_repository": None,
        "helper": None,
        "configuration": None,
        "integration_surfaces": [],
        "checks": [],
        "limitations": ["doctor did not change any configuration or environment"],
        "diagnostics": [{"summary": str(error), "exception_type": type(error).__name__}],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run read-only LDVH source integration diagnostics")
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
