from __future__ import annotations

import json
import subprocess
from typing import Any

from configuration import ConfigurationError
from helper_protocol import validate_helper_response

GOVERNANCE_OPERATION = "resolve-governance-scope"
FACT_CANDIDATE_OPERATION = "find-fact-object-candidates"


def _run_helper(
    helper_executable: str,
    *,
    cwd: str,
    operation_key: str,
    request: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        [helper_executable, "call", operation_key],
        cwd=cwd,
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
        raise ConfigurationError("Helper did not return one JSON response") from error
    return completed.returncode, validate_helper_response(
        parsed_response,
        exit_code=completed.returncode,
        request_kind="call",
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
    cwd: str,
) -> tuple[dict[str, Any], ...]:
    governance_request = {
        "work_object_locators": [cwd],
        "arguments": {"workspace_root": workspace_root},
        "response_profile": "compact",
    }
    governance_exit_code, governance_response = _run_helper(
        helper_executable,
        cwd=cwd,
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
        "work_object_locators": [cwd],
        "arguments": {
            "workspace_root": workspace_root,
            "governed_project_id": project_id,
            "card_layer": "F1",
        },
        "response_profile": "compact",
    }
    fact_exit_code, fact_response = _run_helper(
        helper_executable,
        cwd=cwd,
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
