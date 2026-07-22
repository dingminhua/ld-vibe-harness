from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from configuration import ConfigurationError, configure_utf8_standard_streams, load_rule_orientation_configuration

SESSION_START_SOURCES = frozenset({"startup", "resume", "clear", "compact"})
SUPPORTED_EVENTS = frozenset({"SessionStart", "SubagentStart"})
HELPER_CONTRACT = "ldvh-helper-cli/2"
RULE_ORIENTATION_PROFILE = "work-context-rule-orientation"
RULE_ORIENTATION_OPERATION = "read-specification-content"
RULE_ORIENTATION_SELECTIONS = (
    {
        "responsibility_key": "ldvh-root",
        "heading_path": ["8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"],
    },
)
HELPER_EXIT_CODES = {
    "ok": 0,
    "no_change": 0,
    "partial": 3,
    "rejected": 4,
    "unavailable": 5,
    "invalid_request": 2,
    "error": 1,
}


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
        "The work-context rule orientation was not delivered; facts remain not requested. "
        "Read the current rule sources directly instead of inferring that any rule or project fact is absent."
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


def _rule_orientation_request() -> dict[str, Any]:
    return {
        "arguments": {"selections": list(RULE_ORIENTATION_SELECTIONS)},
        "requested_disclosure": "L3",
        "response_profile": "compact",
        "observed_context": {},
    }


def _rule_parts(response: dict[str, Any]) -> list[dict[str, Any]]:
    result = response.get("result")
    if result is None:
        return []
    if not isinstance(result, dict) or not isinstance(result.get("items"), list):
        raise ConfigurationError("rule orientation Helper result has no valid items")
    parts: list[dict[str, Any]] = []
    for item in result["items"]:
        if not isinstance(item, dict) or not isinstance(item.get("parts"), list):
            raise ConfigurationError("rule orientation Helper item has no valid parts")
        for part in item["parts"]:
            if not isinstance(part, dict):
                raise ConfigurationError("rule orientation Helper part must be an object")
            content = part.get("content")
            heading_path = part.get("heading_path")
            source = part.get("source")
            if (
                not isinstance(content, str)
                or not content
                or not isinstance(heading_path, list)
                or not all(isinstance(value, str) and value for value in heading_path)
                or not isinstance(source, dict)
                or not isinstance(source.get("locator"), str)
                or not source["locator"]
            ):
                raise ConfigurationError("rule orientation Helper part does not preserve source content")
            parts.append(
                {
                    "heading_path": heading_path,
                    "locator": source["locator"],
                    "content": content,
                }
            )
    return parts


def _render_rule_orientation_context(
    response: dict[str, Any],
    *,
    helper_executable: str,
    native_trigger: str,
) -> str:
    outcome = response["outcome"]
    parts = _rule_parts(response)
    delivered = "\n\n".join(
        f"Source: {part['locator']}\nHeading: {' / '.join(part['heading_path'])}\n{part['content']}"
        for part in parts
    )
    gaps = response.get("gaps")
    if not isinstance(gaps, list):
        raise ConfigurationError("rule orientation Helper response has no valid gaps list")
    scope = response.get("scope")
    if (
        not isinstance(scope, dict)
        or not isinstance(scope.get("completed"), list)
        or not isinstance(scope.get("not_completed"), list)
    ):
        raise ConfigurationError("rule orientation Helper response has no valid delivery scope")
    follow_up = response.get("follow_up")
    if not isinstance(follow_up, dict):
        raise ConfigurationError("rule orientation Helper response has no valid follow-up")
    delivery_state = {
        "completed": scope["completed"],
        "not_completed": scope["not_completed"],
        "gaps": gaps,
        "follow_up": follow_up,
    }
    delivery_state_text = json.dumps(delivery_state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        f"LDVH work-context rule orientation ({RULE_ORIENTATION_PROFILE}) was invoked for {native_trigger}. "
        f"Helper executable: {helper_executable}. Rule delivery outcome: {outcome}. Facts: not_requested.\n\n"
        "The following are the exact rule-source parts delivered by the profile:\n\n"
        + (delivered if delivered else "No rule part was completed by the Helper.")
        + "\n\nDelivery scope, gaps, and follow-up: "
        + delivery_state_text
        + "\n\nThe adapter did not perform governance resolution, fact discovery, fact reading, rule-applicability, "
        "authorization, or completion judgment. Its cwd only supplied the Helper process environment and did not "
        "select these rules. After understanding the Human goal, continue with the relevant Helper rule or fact reads."
    )


def _run_rule_orientation(configuration: dict[str, Any], *, cwd: str) -> dict[str, Any]:
    completed = subprocess.run(
        [
            configuration["helper_executable"],
            "call",
            RULE_ORIENTATION_OPERATION,
        ],
        cwd=cwd,
        input=json.dumps(_rule_orientation_request(), ensure_ascii=False, separators=(",", ":")),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=30,
        check=False,
    )
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ConfigurationError("Helper did not return a JSON rule orientation response") from error
    if (
        not isinstance(response, dict)
        or response.get("contract") != HELPER_CONTRACT
        or response.get("request_kind") != "call"
        or response.get("operation_key") != RULE_ORIENTATION_OPERATION
        or response.get("outcome") not in HELPER_EXIT_CODES
    ):
        raise ConfigurationError("Helper did not return a valid rule orientation response")
    if completed.returncode != HELPER_EXIT_CODES[response["outcome"]]:
        raise ConfigurationError("Helper exit code does not match the rule orientation outcome")
    return response


def _run(value: Any) -> dict[str, Any]:
    event_name, cwd, source = _validate_hook_input(value)
    configuration = load_rule_orientation_configuration(_plugin_data())
    native_trigger = event_name if source is None else f"{event_name}/{source}"
    response = _run_rule_orientation(configuration, cwd=cwd)
    context = (
        f"LDVH Codex thin adapter mapped {native_trigger} to the source-defined rule orientation profile. "
        + _render_rule_orientation_context(
            response,
            helper_executable=configuration["helper_executable"],
            native_trigger=native_trigger,
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
