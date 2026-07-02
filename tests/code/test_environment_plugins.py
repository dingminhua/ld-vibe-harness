from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SHIM = ROOT / "code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"


def _run_shim(payload: dict, *, check: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["LDVH_ROOT"] = ROOT.as_posix()
    return subprocess.run(
        [sys.executable, SHIM.as_posix()],
        cwd=ROOT,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=check,
        env=env,
        timeout=60,
    )


def _diagnostic_codes(result: dict) -> set[str]:
    return {diagnostic["code"] for diagnostic in result.get("diagnostics", [])}


def test_codex_sample_shim_passes_session_payload_to_runtime_adapter() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "SessionStart",
            "sessionId": "shim-session",
            "cwd": ROOT.as_posix(),
            "prompt": "进入 LDVH v3 工作",
            "targetPath": "README.md",
        },
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "session_start"
    assert payload["payload"]["session_id"] == "shim-session"
    assert payload["payload"]["target_path"] == "README.md"
    assert payload["payload"]["task"] == "进入 LDVH v3 工作"
    assert payload["payload"]["trigger_source"] == "codex.ldvh-plugin"
    assert payload["dispatch"]["summary"]["integration_scope"] == "manual.session_start"
    assert payload["dispatch"]["metadata"]["environment_integrated"] is False


def test_codex_sample_shim_blocks_pre_tool_use_without_read_plan_ack() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "tests/code/test_environment_plugins.py"},
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["event"] == "pre_tool_use"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in _diagnostic_codes(payload)


def test_codex_sample_shim_allows_pre_tool_use_with_acknowledged_paths() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-ok",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "toolInput": {"file_path": "tests/code/test_environment_plugins.py"},
            "acknowledgedPaths": [
                "specs/00-理念与构成.md",
                "specs/01-保障与衔接.md",
                "specs/02-AI行为规范.md",
            ],
        },
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["event"] == "pre_tool_use"
    assert payload["dispatch"]["receipt"]["acknowledged_paths"] == [
        "specs/00-理念与构成.md",
        "specs/01-保障与衔接.md",
        "specs/02-AI行为规范.md",
    ]
    assert payload["dispatch"]["preflight"]["summary"]["target_type"] == "tests"


def test_codex_sample_shim_degrades_completion_claim_to_non_blocking_stop() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "Stop",
            "sessionId": "shim-stop",
            "cwd": ROOT.as_posix(),
            "targetPath": "README.md",
        },
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["summary"]["status"] == "blocked"
    assert payload["summary"]["event"] == "completion_claim"
    assert "RUNTIME_COMPLETION_VERIFICATION_MISSING" in _diagnostic_codes(payload)
    assert payload["metadata"]["environment_integrated"] is False
