"""Source-defined work-context delivery core for environment thin adapters."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from ldvh.helper.responses import CONTRACT as HELPER_CONTRACT
from ldvh.helper.responses import EXIT_CODES

WORK_CONTEXT_CONTRACT = "ldvh-work-context/1"
RULE_ORIENTATION_PROFILE = "work-context-rule-orientation"
RULE_ORIENTATION_OPERATION = "read-specification-content"
SESSION_START_SOURCES = frozenset({"startup", "resume", "clear", "compact"})
SUPPORTED_EVENTS = frozenset({"SessionStart", "SubagentStart"})
RULE_ORIENTATION_SELECTIONS = (
    {
        "responsibility_key": "ldvh-root",
        "heading_path": ["8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"],
    },
    {
        "responsibility_key": "ldvh-root",
        "heading_path": ["8. 系统级运行架构", "8.2 环境 Hook 的薄引用与核心职责边界"],
    },
)

type JsonObject = dict[str, Any]


class WorkContextError(ValueError):
    """The work-context core could not form a faithful result."""


def _helper_executable(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or not path.is_file() or not path.stat().st_mode:
        raise WorkContextError("helper_executable must identify an executable absolute file")
    if not path.stat().st_mode & 0o111:
        raise WorkContextError("helper_executable must identify an executable absolute file")
    return path


def _native_trigger(value: Any) -> tuple[str, Path, str]:
    if not isinstance(value, dict):
        raise WorkContextError("native event must be a JSON object")
    event_name = value.get("hook_event_name")
    if event_name not in SUPPORTED_EVENTS:
        raise WorkContextError("hook_event_name is not supported by the current work-context core")
    source = value.get("source")
    if event_name == "SessionStart":
        if source not in SESSION_START_SOURCES:
            raise WorkContextError("SessionStart source is not supported by the current work-context core")
        trigger = f"{event_name}/{source}"
    else:
        trigger = event_name
    cwd = value.get("cwd")
    if not isinstance(cwd, str) or not cwd.strip():
        raise WorkContextError("native event does not provide a current directory")
    directory = Path(cwd)
    if not directory.is_absolute() or not directory.is_dir():
        raise WorkContextError("native event current directory is not usable")
    return event_name, directory, trigger


def _request() -> JsonObject:
    return {
        "arguments": {"selections": list(RULE_ORIENTATION_SELECTIONS)},
        "requested_disclosure": "L3",
        "response_profile": "compact",
        "observed_context": {},
    }


def _run_helper(helper_executable: Path, *, cwd: Path) -> JsonObject:
    completed = subprocess.run(
        [str(helper_executable), "call", RULE_ORIENTATION_OPERATION],
        cwd=cwd,
        input=json.dumps(_request(), ensure_ascii=False, separators=(",", ":")),
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
        raise WorkContextError("Helper did not return a JSON work-context response") from error
    if (
        not isinstance(response, dict)
        or response.get("contract") != HELPER_CONTRACT
        or response.get("request_kind") != "call"
        or response.get("operation_key") != RULE_ORIENTATION_OPERATION
        or response.get("outcome") not in EXIT_CODES
    ):
        raise WorkContextError("Helper did not return a valid work-context response")
    if completed.returncode != EXIT_CODES[response["outcome"]]:
        raise WorkContextError("Helper exit code does not match the work-context outcome")
    return response


def _rule_parts(response: JsonObject) -> list[JsonObject]:
    result = response.get("result")
    if result is None:
        return []
    if not isinstance(result, dict) or not isinstance(result.get("items"), list):
        raise WorkContextError("Helper result has no valid work-context items")
    parts: list[JsonObject] = []
    delivered_identities: set[tuple[str, tuple[str, ...], str]] = set()
    for item in result["items"]:
        if not isinstance(item, dict) or not isinstance(item.get("parts"), list):
            raise WorkContextError("Helper work-context item has no valid parts")
        for part in item["parts"]:
            if not isinstance(part, dict):
                raise WorkContextError("Helper work-context part must be an object")
            content = part.get("content")
            heading_path = part.get("heading_path")
            source = part.get("source")
            if (
                not isinstance(content, str)
                or not content
                or not isinstance(heading_path, list)
                or not all(isinstance(item, str) and item for item in heading_path)
                or not isinstance(source, dict)
                or not isinstance(source.get("locator"), str)
                or not source["locator"]
            ):
                raise WorkContextError("Helper work-context part does not preserve source content")
            identity = (source["locator"], tuple(heading_path), content)
            if identity not in delivered_identities:
                delivered_identities.add(identity)
                parts.append(
                    {
                        "heading_path": heading_path,
                        "locator": source["locator"],
                        "content": content,
                    }
                )
    return parts


def _context(response: JsonObject, *, helper_executable: Path, native_trigger: str) -> str:
    parts = _rule_parts(response)
    delivered = "\n\n".join(
        f"Source: {part['locator']}\nHeading: {' / '.join(part['heading_path'])}\n{part['content']}"
        for part in parts
    )
    gaps = response.get("gaps")
    scope = response.get("scope")
    follow_up = response.get("follow_up")
    if (
        not isinstance(gaps, list)
        or not isinstance(scope, dict)
        or not isinstance(scope.get("completed"), list)
        or not isinstance(scope.get("not_completed"), list)
        or not isinstance(follow_up, dict)
    ):
        raise WorkContextError("Helper response does not preserve work-context delivery state")
    delivery_state = json.dumps(
        {
            "completed": scope["completed"],
            "not_completed": scope["not_completed"],
            "gaps": gaps,
            "follow_up": follow_up,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        f"LDVH work-context core ({RULE_ORIENTATION_PROFILE}) ran for {native_trigger}. "
        f"Helper executable: {helper_executable}. Rule delivery outcome: {response['outcome']}. "
        "Facts: not_requested.\n\n"
        "The following are the exact rule-source parts delivered by the profile:\n\n"
        + (delivered if delivered else "No rule part was completed by the core.")
        + "\n\nDelivery scope, gaps, and follow-up: "
        + delivery_state
        + "\n\nThe environment thin reference did not perform governance resolution, fact discovery, fact reading, "
        "rule-applicability, authorization, or completion judgment. After understanding the Human goal, continue "
        "with the relevant Helper rule or fact reads."
    )


def _unavailable_context(summary: str) -> str:
    return (
        f"LDVH work-context core unavailable: {summary}. "
        "The work-context rule orientation was not delivered; facts remain not_requested. "
        "Read the current rule sources directly instead of inferring that any rule or project fact is absent."
    )


def run(native_event: Any, *, helper_executable: str) -> JsonObject:
    event_name, cwd, trigger = _native_trigger(native_event)
    helper = _helper_executable(helper_executable)
    response = _run_helper(helper, cwd=cwd)
    return {
        "contract": WORK_CONTEXT_CONTRACT,
        "event_name": event_name,
        "outcome": response["outcome"],
        "facts": "not_requested",
        "additional_context": _context(response, helper_executable=helper, native_trigger=trigger),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the LDVH work-context core")
    parser.add_argument("--helper-executable", required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    event_name: str | None = None
    try:
        native_event = json.load(sys.stdin)
        event_name, _, _ = _native_trigger(native_event)
        result = run(native_event, helper_executable=arguments.helper_executable)
    except (WorkContextError, OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        result = {
            "contract": WORK_CONTEXT_CONTRACT,
            "event_name": event_name,
            "outcome": "unavailable",
            "facts": "not_requested",
            "additional_context": _unavailable_context(str(error)),
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
