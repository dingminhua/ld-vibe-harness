#!/usr/bin/env python3
"""Thin Codex hook shim for the repo-local LDVH V3 sample package.

This shim intentionally keeps all LDVH decisions in code/runtime_adapter.py.
It is not installed by this repository.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT_MARKERS = ("code/runtime_adapter.py", "specs/00-理念与构成.md")
TRIGGER_SOURCE = "codex.ldvh-plugin"
EVENT_MAP = {
    "sessionstart": "session_start",
    "session_start": "session_start",
    "pretooluse": "pre_tool_use",
    "pre_tool_use": "pre_tool_use",
    "stop": "completion_claim",
    "completion_claim": "completion_claim",
}
BLOCKING_EVENTS = {"pre_tool_use"}


def read_payload(raw: str) -> dict[str, Any]:
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def list_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return [str(value)]


def normalize_event(payload: dict[str, Any]) -> str:
    raw = first_text(
        payload.get("event"),
        payload.get("hook_event_name"),
        payload.get("hookEventName"),
        payload.get("hook_event"),
        payload.get("hookEvent"),
        payload.get("event_name"),
        payload.get("eventName"),
    )
    key = raw.replace("-", "_").replace(" ", "").lower()
    return EVENT_MAP.get(key, "")


def is_ldvh_root(path: Path) -> bool:
    return all((path / marker).is_file() for marker in ROOT_MARKERS)


def candidate_roots(payload: dict[str, Any], cwd: Path, shim_path: Path) -> list[Path]:
    roots: list[Path] = []
    for raw in (os.environ.get("LDVH_ROOT"), payload.get("ldvh_root"), payload.get("ldvhRoot")):
        if isinstance(raw, str) and raw.strip():
            roots.append(Path(raw).expanduser())
    roots.extend([cwd, *cwd.parents])
    roots.extend([shim_path.parent, *shim_path.parents])
    return roots


def find_ldvh_root(payload: dict[str, Any], cwd: Path) -> Path | None:
    shim_path = Path(__file__).resolve()
    for root in candidate_roots(payload, cwd, shim_path):
        resolved = root.resolve()
        if is_ldvh_root(resolved):
            return resolved
    return None


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_input") or payload.get("toolInput") or {}
    return value if isinstance(value, dict) else {}


def target_path(payload: dict[str, Any], cwd: Path) -> str:
    tool = tool_input(payload)
    candidates = [
        payload.get("target_path"),
        payload.get("targetPath"),
        tool.get("file_path"),
        tool.get("path"),
        tool.get("target_path"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    target_paths = payload.get("target_paths") or payload.get("targetPaths")
    if isinstance(target_paths, list):
        for candidate in target_paths:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return cwd.as_posix()


def task_text(payload: dict[str, Any]) -> str:
    return first_text(
        payload.get("task"),
        payload.get("prompt"),
        payload.get("user_prompt"),
        payload.get("userPrompt"),
        payload.get("message"),
    )


def operation(payload: dict[str, Any]) -> str:
    tool_name = first_text(payload.get("tool_name"), payload.get("toolName")).lower()
    if tool_name in {"read", "grep", "glob", "ls"}:
        return "read"
    return first_text(payload.get("operation"), "write")


def adapter_payload(payload: dict[str, Any], event: str, cwd: Path) -> dict[str, Any]:
    return {
        "event": event,
        "session_id": first_text(payload.get("session_id"), payload.get("sessionId"), "codex-hook"),
        "target_path": target_path(payload, cwd),
        "operation": operation(payload),
        "task": task_text(payload),
        "acknowledged_paths": list_text(payload.get("acknowledged_paths") or payload.get("acknowledgedPaths")),
        "verification_evidence": list_text(payload.get("verification_evidence") or payload.get("verificationEvidence")),
        "trigger_source": TRIGGER_SOURCE,
    }


def emit_diagnostic(code: str, message: str, *, blocked: bool = False) -> int:
    print(
        json.dumps(
            {
                "summary": {
                    "status": "blocked" if blocked else "ok",
                    "adapter_integrated": False,
                    "environment_integrated": False,
                    "trigger_source": TRIGGER_SOURCE,
                },
                "diagnostics": [
                    {
                        "level": "blocking" if blocked else "warning",
                        "code": code,
                        "path": "runtime://codex-ldvh-v3-shim",
                        "message": message,
                    }
                ],
            },
            ensure_ascii=False,
        )
    )
    return 1 if blocked else 0


def main() -> int:
    raw = sys.stdin.read()
    payload = read_payload(raw)
    cwd = Path(first_text(payload.get("cwd"), os.getcwd())).expanduser()
    event = normalize_event(payload)
    if not event:
        return emit_diagnostic(
            "LDVH_CODEX_SHIM_EVENT_UNKNOWN",
            "Codex hook payload did not contain a supported SessionStart, PreToolUse, Stop, or completion_claim event.",
        )

    ldvh_root = find_ldvh_root(payload, cwd)
    if ldvh_root is None:
        return emit_diagnostic(
            "LDVH_CODEX_SHIM_ROOT_NOT_FOUND",
            "LDVH root was not found from LDVH_ROOT, payload, cwd, or shim path; hook shim allowed the event.",
        )

    runtime_adapter = ldvh_root / "code" / "runtime_adapter.py"
    adapter_json = json.dumps(adapter_payload(payload, event, cwd), ensure_ascii=False)
    command = [
        sys.executable,
        runtime_adapter.as_posix(),
        "--root",
        ldvh_root.as_posix(),
        "--payload-json",
        adapter_json,
        "--format",
        "json",
    ]
    result = subprocess.run(command, text=True)
    if event in BLOCKING_EVENTS:
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
