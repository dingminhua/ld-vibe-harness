from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = ROOT / "hooks/environment-plugins/codex-ldvh-v3"
SHIM = ROOT / "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"
PLUGIN_JSON = PLUGIN_ROOT / ".codex-plugin/plugin.json"


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


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


def test_codex_sample_plugin_manifest_consumes_package_icons() -> None:
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
