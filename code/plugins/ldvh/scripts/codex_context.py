from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from configuration import ConfigurationError, configure_utf8_standard_streams, load_configuration
from context_recovery import recover_context

SESSION_START_SOURCES = frozenset({"startup", "resume", "clear", "compact"})
SUPPORTED_EVENTS = frozenset({"SessionStart", "SubagentStart"})


def _supported_event_for_error_context(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    event_name = value.get("hook_event_name")
    if event_name == "SessionStart" and value.get("source") in SESSION_START_SOURCES:
        return event_name
    return event_name if event_name == "SubagentStart" else None


def _message(summary: str, *, event_name: str | None) -> dict[str, Any]:
    message = (
        f"LDVH Codex adapter unavailable: {summary}. "
        "Shared context recovery did not produce a usable Helper result; treat LDVH context as unresolved "
        "and recover from the current sources instead of inferring that governance or facts are absent."
    )
    response: dict[str, Any] = {
        "continue": True,
        "systemMessage": message,
    }
    if event_name is not None:
        response["hookSpecificOutput"] = {
            "hookEventName": event_name,
            "additionalContext": message,
        }
    return response


def _validate_hook_input(value: Any) -> tuple[str, str, str | None]:
    if not isinstance(value, dict):
        raise ConfigurationError("hook input must be a JSON object")
    event_name = value.get("hook_event_name")
    if event_name not in SUPPORTED_EVENTS:
        raise ConfigurationError("hook_event_name must be SessionStart or SubagentStart")
    source: str | None = None
    if event_name == "SessionStart":
        source = value.get("source")
        if source not in SESSION_START_SOURCES:
            raise ConfigurationError("SessionStart source must be startup, resume, clear, or compact")
    cwd = value.get("cwd")
    if not isinstance(cwd, str) or not cwd.strip() or not Path(cwd).is_absolute():
        raise ConfigurationError("cwd must be a non-empty absolute path")
    if not Path(cwd).is_dir():
        raise ConfigurationError("cwd does not identify a current directory")
    return event_name, cwd, source


def _plugin_data() -> Path:
    value = os.environ.get("PLUGIN_DATA")
    if not value:
        raise ConfigurationError("PLUGIN_DATA is not available")
    path = Path(value)
    if not path.is_absolute():
        raise ConfigurationError("PLUGIN_DATA must be an absolute path")
    return path


def _render_recovery_context(
    exchanges: tuple[dict[str, Any], ...],
    *,
    helper_executable: str,
    cwd: str,
) -> str:
    return (
        "LDVH shared context recovery executed only source-defined read operations. "
        f"Helper executable: {helper_executable}. Work object: {cwd}. "
        "Helper exchanges contain each actual request, process exit code, and unmodified Helper response: "
        + json.dumps(exchanges, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + ". Code did not interpret fact applicability, current WorkCase, authorization, semantic sufficiency, "
        "or task completion."
    )


def _run(value: Any) -> dict[str, Any]:
    event_name, cwd, source = _validate_hook_input(value)
    configuration = load_configuration(_plugin_data())
    exchanges = recover_context(
        helper_executable=configuration["helper_executable"],
        workspace_root=configuration["workspace_root"],
        cwd=cwd,
    )
    native_trigger = event_name if source is None else f"{event_name}/{source}"
    context = (
        f"LDVH Codex thin adapter mapped {native_trigger} to shared context recovery. "
        + _render_recovery_context(
            exchanges,
            helper_executable=configuration["helper_executable"],
            cwd=cwd,
        )
    )
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        },
    }


def main() -> int:
    configure_utf8_standard_streams()
    value: Any = None
    try:
        value = json.load(sys.stdin)
        response = _run(value)
    except (ConfigurationError, OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        response = _message(str(error), event_name=_supported_event_for_error_context(value))
    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
