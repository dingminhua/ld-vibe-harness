from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = ROOT / "hooks/environment-plugins/codex-ldvh-v3"
SHIM = ROOT / "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"
PLUGIN_JSON = PLUGIN_ROOT / "plugin.json"


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def _run_shim(payload: dict, *, check: bool = True, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["LDVH_ROOT"] = ROOT.as_posix()
    env["LDVH_HOOK_SPARK_CAPTURE"] = "0"
    if extra_env:
        env.update(extra_env)
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


def _hook_output(payload: dict) -> dict:
    value = payload.get("hookSpecificOutput")
    return value if isinstance(value, dict) else {}


def test_codex_sample_plugin_manifest_consumes_package_icons() -> None:
    assert not (PLUGIN_ROOT / ".codex-plugin").exists()

    manifest = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    interface = manifest["interface"]

    assert interface["composerIcon"] == "./assets/ldvh-plugin-icon-128.png"
    assert interface["logo"] == "./assets/ldvh-plugin-icon-512.png"

    for field in ("composerIcon", "logo"):
        rel_path = interface[field]
        assert rel_path.startswith("./assets/")
        asset_path = (PLUGIN_ROOT / rel_path[2:]).resolve()
        assert PLUGIN_ROOT.resolve() in asset_path.parents
        assert asset_path.is_file()


def test_codex_sample_plugin_hooks_do_not_emit_status_messages() -> None:
    hooks = json.loads((PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
    raw = json.dumps(hooks, ensure_ascii=False)

    assert "statusMessage" not in raw


def test_codex_sample_plugin_declares_six_research_hook_events() -> None:
    hooks = json.loads((PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]

    assert set(hooks) == {
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
        "UserPromptSubmit",
        "Stop",
        "Notification",
    }
    for event_name, entries in hooks.items():
        assert entries
        assert all(
            hook["command"] == 'python3 "$PLUGIN_ROOT/hooks/ldvh_runtime_shim.py"'
            for entry in entries
            for hook in entry["hooks"]
        ), event_name


def test_v2_absorbed_icon_assets_have_expected_png_sizes() -> None:
    expected_sizes = {
        "ldvh-plugin-icon-16.png": (16, 16),
        "ldvh-plugin-icon-32.png": (32, 32),
        "ldvh-plugin-icon-48.png": (48, 48),
        "ldvh-plugin-icon-64.png": (64, 64),
        "ldvh-plugin-icon-128.png": (128, 128),
        "ldvh-plugin-icon-180.png": (180, 180),
        "ldvh-plugin-icon-192.png": (192, 192),
        "ldvh-plugin-icon-256.png": (256, 256),
        "ldvh-plugin-icon-512.png": (512, 512),
        "ldvh-plugin-icon.png": (512, 512),
    }

    for filename, dimensions in expected_sizes.items():
        assert _png_dimensions(ROOT / "icons" / filename) == dimensions

    assert _png_dimensions(PLUGIN_ROOT / "assets/ldvh-plugin-icon-128.png") == (128, 128)
    assert _png_dimensions(PLUGIN_ROOT / "assets/ldvh-plugin-icon-512.png") == (512, 512)


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
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "SessionStart"
    assert "LDVH V3 session read plan is active" in hook_output["additionalContext"]
    assert "specs/00-理念与构成.md" in hook_output["additionalContext"]
    assert "specs/01-保障与衔接.md" in hook_output["additionalContext"]
    assert "specs/02-AI行为规范.md" in hook_output["additionalContext"]


def test_codex_sample_shim_silent_noops_for_non_governed_events(tmp_path: Path) -> None:
    outside = tmp_path / "outside-project"
    outside.mkdir()
    payloads = [
        {
            "hook_event_name": "SessionStart",
            "sessionId": "shim-outside-session",
            "cwd": outside.as_posix(),
            "prompt": "外部项目工作",
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-outside-pretool",
            "cwd": outside.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "notes.txt"},
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-outside-edit",
            "cwd": outside.as_posix(),
            "toolName": "Edit",
            "toolInput": {"filePath": "notes.txt"},
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-outside-multipath",
            "cwd": outside.as_posix(),
            "toolName": "MultiEdit",
            "tool_input": {"file_paths": ["notes.txt", "docs/todo.md"]},
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-outside-camel-multipath",
            "cwd": outside.as_posix(),
            "toolName": "MultiEdit",
            "toolInput": {"filePaths": ["notes.txt", "docs/todo.md"]},
        },
        {
            "hook_event_name": "Stop",
            "sessionId": "shim-outside-stop",
            "cwd": outside.as_posix(),
        },
    ]

    for payload in payloads:
        completed = _run_shim(payload)
        assert completed.returncode == 0
        assert completed.stdout == ""
        assert completed.stderr == ""


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
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_allows_read_only_bash_probe_without_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-read",
            "cwd": ROOT.as_posix(),
            "toolName": "Bash",
            "tool_input": {"command": "pwd"},
        },
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


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
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["additionalContext"].startswith("LDVH V3 pre-tool check passed.")
    assert "specs/00-理念与构成.md" in hook_output["additionalContext"]


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
    assert payload["continue"] is True
    assert "LDVH V3 completion check warning" in payload["systemMessage"]
    assert "RUNTIME_COMPLETION_VERIFICATION_MISSING" in payload["systemMessage"]


def test_codex_sample_shim_does_not_capture_research_spark_by_default(tmp_path: Path) -> None:
    spark_dir = tmp_path / "sparks"
    completed = _run_shim(
        {"hook_event_name": "SessionStart", "sessionId": "shim-no-capture", "cwd": ROOT.as_posix()},
        extra_env={
            "LDVH_HOOK_SPARK_CAPTURE": "",
            "LDVH_HOOK_SPARK_DIR": spark_dir.as_posix(),
        },
    )

    assert completed.returncode == 0
    assert not spark_dir.exists()


def test_codex_sample_shim_opt_in_records_six_hook_events_to_temp_research_spark(tmp_path: Path) -> None:
    spark_dir = tmp_path / "sparks"
    env = {
        "LDVH_HOOK_SPARK_CAPTURE": "1",
        "LDVH_HOOK_SPARK_DIR": spark_dir.as_posix(),
    }
    payloads = [
        {"hook_event_name": "SessionStart", "sessionId": "shim-research", "cwd": ROOT.as_posix()},
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-research",
            "cwd": ROOT.as_posix(),
            "toolName": "Read",
            "tool_input": {"file_path": "README.md"},
        },
        {
            "hook_event_name": "PostToolUse",
            "sessionId": "shim-research",
            "cwd": ROOT.as_posix(),
            "toolName": "Read",
            "tool_input": {"file_path": "README.md"},
        },
        {"hook_event_name": "UserPromptSubmit", "sessionId": "shim-research", "cwd": ROOT.as_posix()},
        {"hook_event_name": "Stop", "sessionId": "shim-research", "cwd": ROOT.as_posix()},
        {"hook_event_name": "Notification", "sessionId": "shim-research", "cwd": ROOT.as_posix()},
    ]

    for payload in payloads:
        completed = _run_shim(payload, extra_env=env)
        assert completed.returncode == 0

    files = list(spark_dir.glob("spark-0001-codex-hook-six-event-research-capture.yaml"))
    assert len(files) == 1
    raw = files[0].read_text(encoding="utf-8")

    for event_name in ("SessionStart", "PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop", "Notification"):
        assert f"event={event_name}" in raw
    assert "title: Codex Hook 六类事件研究采样" in raw
    assert "source: codex_hook" in raw
