"""Source-defined, environment-neutral context recovery for Hook adapters."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ldvh.helper.responses import CONTRACT, EXIT_CODES

GOVERNANCE_OPERATION = "resolve-governance-scope"
FACT_CANDIDATE_OPERATION = "find-fact-object-candidates"


class ContextRecoveryError(ValueError):
    """The recovery runner could not faithfully form its raw exchange sequence."""


def _absolute_path(value: str, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ContextRecoveryError(f"{field} must be a non-empty absolute path")
    path = Path(value)
    if not path.is_absolute():
        raise ContextRecoveryError(f"{field} must be an absolute path")
    return path


def _executable_path(value: str, field: str) -> Path:
    path = _absolute_path(value, field)
    if not path.is_file():
        raise ContextRecoveryError(f"{field} does not identify a current file")
    if not os.access(path, os.X_OK):
        raise ContextRecoveryError(f"{field} is not executable")
    return path


def _directory_path(value: str, field: str) -> Path:
    path = _absolute_path(value, field)
    if not path.is_dir():
        raise ContextRecoveryError(f"{field} does not identify a current directory")
    return path


def _work_object_locator(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextRecoveryError("work_object_locator must be a non-empty path string")
    return value


def _validate_helper_response(
    value: Any,
    *,
    exit_code: int,
    operation_key: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContextRecoveryError("Helper response must be a JSON object")
    if value.get("contract") != CONTRACT:
        raise ContextRecoveryError(f"Helper response contract must be {CONTRACT}")
    if value.get("request_kind") != "call":
        raise ContextRecoveryError("Helper response request_kind must be call")
    if value.get("operation_key") != operation_key:
        raise ContextRecoveryError(f"Helper response operation_key must be {operation_key}")
    outcome = value.get("outcome")
    expected_exit_code = EXIT_CODES.get(outcome)
    if expected_exit_code is None:
        raise ContextRecoveryError("Helper response outcome is not supported by the current contract")
    if exit_code != expected_exit_code:
        raise ContextRecoveryError("Helper response outcome and process exit code do not match the current contract")
    return value


def _run_helper(
    helper_executable: Path,
    *,
    helper_cwd: Path,
    operation_key: str,
    request: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        [str(helper_executable), "call", operation_key],
        cwd=helper_cwd,
        input=json.dumps(request, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=20,
        check=False,
    )
    try:
        parsed_response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ContextRecoveryError("Helper did not return one JSON response") from error
    return completed.returncode, _validate_helper_response(
        parsed_response,
        exit_code=completed.returncode,
        operation_key=operation_key,
    )


def _governed_project_id(response: dict[str, Any]) -> str | None:
    if response["outcome"] != "ok":
        return None
    result = response.get("result")
    if not isinstance(result, dict) or result.get("scope_status") != "governed_single":
        return None
    resolutions = result.get("object_resolutions")
    if not isinstance(resolutions, list) or not resolutions:
        return None

    project_ids: set[str] = set()
    for resolution in resolutions:
        if not isinstance(resolution, dict) or resolution.get("status") != "governed":
            return None
        project_id = resolution.get("governed_project_id")
        if not isinstance(project_id, str) or not project_id:
            return None
        project_ids.add(project_id)
    return next(iter(project_ids)) if len(project_ids) == 1 else None


def recover_context(
    *,
    helper_executable: str,
    workspace_root: str,
    work_object_locator: str,
    helper_cwd: str,
) -> tuple[dict[str, Any], ...]:
    helper = _executable_path(helper_executable, "helper_executable")
    workspace = _directory_path(workspace_root, "workspace_root")
    locator = _work_object_locator(work_object_locator)
    cwd = _directory_path(helper_cwd, "helper_cwd")
    governance_request = {
        "work_object_locators": [locator],
        "arguments": {"workspace_root": str(workspace)},
        "response_profile": "compact",
    }
    governance_exit_code, governance_response = _run_helper(
        helper,
        helper_cwd=cwd,
        operation_key=GOVERNANCE_OPERATION,
        request=governance_request,
    )
    exchanges: tuple[dict[str, Any], ...] = (
        {
            "operation_key": GOVERNANCE_OPERATION,
            "request": governance_request,
            "exit_code": governance_exit_code,
            "response": governance_response,
        },
    )
    project_id = _governed_project_id(governance_response)
    if project_id is None:
        return exchanges

    fact_request = {
        "work_object_locators": [locator],
        "arguments": {
            "workspace_root": str(workspace),
            "governed_project_id": project_id,
            "card_layer": "F1",
        },
        "response_profile": "compact",
    }
    fact_exit_code, fact_response = _run_helper(
        helper,
        helper_cwd=cwd,
        operation_key=FACT_CANDIDATE_OPERATION,
        request=fact_request,
    )
    return exchanges + (
        {
            "operation_key": FACT_CANDIDATE_OPERATION,
            "request": fact_request,
            "exit_code": fact_exit_code,
            "response": fact_response,
        },
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run source-defined LDVH context recovery")
    parser.add_argument("--helper-executable", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--work-object-locator", required=True)
    parser.add_argument("--helper-cwd", required=True)
    return parser


def main(arguments: list[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    try:
        exchanges = recover_context(
            helper_executable=parsed.helper_executable,
            workspace_root=parsed.workspace_root,
            work_object_locator=parsed.work_object_locator,
            helper_cwd=parsed.helper_cwd,
        )
    except (ContextRecoveryError, OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        sys.stderr.write(f"LDVH context recovery unavailable: {error}\n")
        return 1
    payload = json.dumps(list(exchanges), ensure_ascii=False, separators=(",", ":")) + "\n"
    sys.stdout.buffer.write(payload.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
