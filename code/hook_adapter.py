#!/usr/bin/env python3
"""LDVH hook adapter — unified bridge between environment hooks and hook_dispatch.py.

Works on any platform that can pipe stdin JSON to a Python script
(WorkBuddy, Codex, and any future environment with hook support).

Does NOT contain hardcoded paths.  Discovers the dispatcher from the adapter
installation first; the payload cwd belongs to operation-target governance.

Installation on each platform:
  - Point the environment hook configuration at this script.
  - Pass the canonical event as argv[1] (e.g. ``session-start``).
  - Ensure the hook system forwards its stdin payload to this script.

Codex example (hooks.json):
  { "type": "command", "command": "python3 <repo>/code/hook_adapter.py session-start" }

WorkBuddy example (settings.json hook command):
  "command": "python3 <repo>/code/hook_adapter.py session-start"

If the dispatcher cannot be found the adapter returns a no-op receipt
(governed=false) so the environment never blocks due to a missing
LDVH installation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_payload(raw: str) -> dict[str, Any]:
    """Parse stdin as JSON; return empty dict on failure."""
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def find_dispatcher(cwd: Path) -> Path | None:
    """Find hook_dispatch.py without confusing runtime location with target cwd."""
    local_dispatcher = Path(__file__).resolve().with_name("hook_dispatch.py")
    if local_dispatcher.is_file():
        return local_dispatcher

    roots: list[Path] = []
    ldvh_root = os.environ.get("LDVH_ROOT")
    if ldvh_root:
        roots.append(Path(ldvh_root).expanduser())
    roots.extend([cwd, *cwd.parents])

    for root in roots:
        dispatcher = root / "code" / "hook_dispatch.py"
        if dispatcher.is_file():
            return dispatcher
    return None


def main() -> int:
    raw = sys.stdin.read()
    payload = read_payload(raw)
    cwd = Path(payload.get("cwd") or os.getcwd()).expanduser()

    dispatcher = find_dispatcher(cwd)
    if dispatcher is None:
        print(
            json.dumps(
                {
                    "blocked": False,
                    "governed": False,
                    "trigger_source": "hook",
                    "receipt": "adapter_no_dispatcher",
                    "cwd": str(cwd),
                    "message": "LDVH dispatcher not found from cwd; adapter allowed tool call.",
                },
                ensure_ascii=False,
            )
        )
        return 0

    event = sys.argv[1] if len(sys.argv) > 1 else "session-start"
    result = subprocess.run(
        [sys.executable, str(dispatcher), "run", event, "--trigger-source", "hook"],
        input=raw,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
