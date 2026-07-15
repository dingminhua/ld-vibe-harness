from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from configuration import ConfigurationError, load_configuration
from helper_protocol import validate_helper_response


def _is_supported_session_start(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("hook_event_name") == "SessionStart"
        and value.get("source") in {"startup", "resume"}
    )


def _message(summary: str, *, include_session_context: bool) -> dict[str, Any]:
    message = (
        f"LDVH Codex adapter unavailable: {summary}. "
        "No LDVH governance result was injected; treat governance scope as unresolved "
        "and use explicit inspection or recovery instead of inferring that governance is absent."
    )
    response: dict[str, Any] = {
        "continue": True,
        "systemMessage": message,
    }
    if include_session_context:
        response["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": message,
        }
    return response


def _validate_hook_input(value: Any) -> tuple[str, str]:
    if not isinstance(value, dict):
        raise ConfigurationError("hook input must be a JSON object")
    if value.get("hook_event_name") != "SessionStart":
        raise ConfigurationError("hook_event_name must be SessionStart")
    source = value.get("source")
    if source not in {"startup", "resume"}:
        raise ConfigurationError("SessionStart source must be startup or resume")
    cwd = value.get("cwd")
    if not isinstance(cwd, str) or not cwd.strip() or not Path(cwd).is_absolute():
        raise ConfigurationError("cwd must be a non-empty absolute path")
    if not Path(cwd).is_dir():
        raise ConfigurationError("cwd does not identify a current directory")
    return cwd, source


def _plugin_data() -> Path:
    value = os.environ.get("PLUGIN_DATA")
    if not value:
        raise ConfigurationError("PLUGIN_DATA is not available")
    path = Path(value)
    if not path.is_absolute():
        raise ConfigurationError("PLUGIN_DATA must be an absolute path")
    return path


def _run(value: Any) -> dict[str, Any]:
    cwd, source = _validate_hook_input(value)
    configuration = load_configuration(_plugin_data())
    request = json.dumps(
        {
            "work_object_locators": [cwd],
            "arguments": {"workspace_root": configuration["workspace_root"]},
            "response_profile": "compact",
        }
    )
    completed = subprocess.run(
        [configuration["helper_executable"], "call", "resolve-governance-scope"],
        cwd=cwd,
        input=request,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    try:
        parsed_response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ConfigurationError("Helper did not return one JSON response") from error
    helper_response = validate_helper_response(
        parsed_response,
        exit_code=completed.returncode,
        request_kind="call",
        operation_key="resolve-governance-scope",
    )
    compact_request = json.dumps(json.loads(request), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    compact = json.dumps(helper_response, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    context = (
        "LDVH Helper mechanical governance result from the Codex "
        f"SessionStart/{source} adapter. The adapter did not decide semantic applicability or authorization. "
        f"Helper executable: {configuration['helper_executable']}. "
        f"Adapter request: {compact_request}. "
        f"Helper exit code: {completed.returncode}. Result: {compact}"
    )
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        },
    }


def main() -> int:
    value: Any = None
    try:
        value = json.load(sys.stdin)
        response = _run(value)
    except (ConfigurationError, OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        response = _message(
            str(error),
            include_session_context=_is_supported_session_start(value),
        )
    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
