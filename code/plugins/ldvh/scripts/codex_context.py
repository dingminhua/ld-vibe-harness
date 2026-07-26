from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from configuration import ConfigurationError, configure_utf8_standard_streams, load_work_context_configuration

WORK_CONTEXT_CONTRACT = "ldvh-work-context/1"
WORK_CONTEXT_OUTCOMES = frozenset({"ok", "no_change", "partial", "rejected", "unavailable", "invalid_request", "error"})


def _plugin_data() -> Path:
    value = os.environ.get("PLUGIN_DATA")
    if not value:
        raise ConfigurationError("PLUGIN_DATA is not available")
    path = Path(value)
    if not path.is_absolute():
        raise ConfigurationError("PLUGIN_DATA must be an absolute path")
    return path


def _core_result(value: Any, *, native_event: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError("work-context core did not return a JSON object")
    event_name = value.get("event_name")
    context = value.get("additional_context")
    outcome = value.get("outcome")
    native_event_name = native_event.get("hook_event_name") if isinstance(native_event, dict) else None
    if value.get("contract") != WORK_CONTEXT_CONTRACT:
        raise ConfigurationError("work-context core did not return a valid result")
    if outcome not in WORK_CONTEXT_OUTCOMES:
        raise ConfigurationError("work-context core did not return a valid result")
    if value.get("facts") != "not_requested":
        raise ConfigurationError("work-context core did not return a valid result")
    if outcome == "unavailable":
        if not isinstance(context, str) or not context:
            raise ConfigurationError("work-context core did not return a valid result")
    else:
        if not isinstance(event_name, str) or not event_name or event_name != native_event_name:
            raise ConfigurationError("work-context core did not return a valid result")
        if not isinstance(context, str) or not context:
            raise ConfigurationError("work-context core did not return a valid result")
    return value


def _run_core(native_event: Any, configuration: dict[str, Any]) -> dict[str, Any]:
    completed = subprocess.run(
        [
            configuration["work_context_executable"],
            "--helper-executable",
            configuration["helper_executable"],
        ],
        cwd=_plugin_data(),
        input=json.dumps(native_event, ensure_ascii=False, separators=(",", ":")),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise ConfigurationError("work-context core process did not complete successfully")
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ConfigurationError("work-context core did not return JSON") from error
    return _core_result(response, native_event=native_event)


def _connection_failure(summary: str) -> dict[str, Any]:
    return {
        "continue": True,
        "systemMessage": (
            f"LDVH Codex thin adapter could not connect to its work-context core: {summary}. "
            "No LDVH work-context result was delivered."
        ),
    }


def _run(native_event: Any) -> dict[str, Any]:
    configuration = load_work_context_configuration(_plugin_data())
    result = _run_core(native_event, configuration)
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": result["event_name"],
            "additionalContext": result["additional_context"],
        },
    }


def main() -> int:
    configure_utf8_standard_streams()
    try:
        response = _run(json.load(sys.stdin))
    except (ConfigurationError, OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        response = _connection_failure(str(error))
    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
