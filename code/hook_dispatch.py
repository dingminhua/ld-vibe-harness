#!/usr/bin/env python3
"""LDVH unified hook dispatcher — dual-path entry for lifecycle protocol events.

Two calling conventions, one handler per event:

  Hook path (AI Hook env: WorkBuddy / Codex / Claude Code):
    echo '{"event":"SessionStart","cwd":"/path/to/project"}' | python3 code/hook_dispatch.py

  Rules path (no AI Hook env: Trae etc.):
    python3 code/hook_dispatch.py run session-start --cwd /path/to/project

Both paths execute the same handler logic.  The dispatcher does not pretend
that a CLI call came from an environment Hook.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = PROJECT_ROOT / "hooks" / "ldvh-hooks.yaml"


def _receipt_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    home = Path(codex_home) if codex_home else Path.home() / ".codex"
    return home / "ldvh" / "session-receipts"


def _safe_receipt_name(session_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in session_id)
    return safe or "unknown"


def _receipt_path(session_id: str) -> Optional[Path]:
    if not session_id:
        return None
    return _receipt_root() / f"{_safe_receipt_name(session_id)}.json"


def _write_session_receipt(session_id: str, event: str, result: dict[str, Any]) -> None:
    path = _receipt_path(session_id)
    if path is None:
        return
    payload = {
        "session_id": session_id,
        "event": event,
        "written_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def _read_session_receipt(session_id: str) -> Optional[dict[str, Any]]:
    path = _receipt_path(session_id)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _find_governed_config(cwd: Path) -> Optional[Path]:
    """Walk upward from *cwd* looking for LDVH-GOVERNED-PROJECTS.yaml."""
    for parent in [cwd, *cwd.parents]:
        config = parent / "LDVH-GOVERNED-PROJECTS.yaml"
        if config.is_file():
            return config
    return None


def _cwd_in_governed_project(cwd: Path, config_path: Path) -> bool:
    """Return True when *cwd* is inside a directory listed in the config."""
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return False
    projects = data.get("projects", [])
    if not isinstance(projects, list):
        return False
    cwd_resolved = cwd.resolve()
    for entry in projects:
        if not isinstance(entry, dict):
            continue
        proj_path = entry.get("path", "")
        if not proj_path:
            continue
        resolved = (config_path.parent / proj_path).resolve()
        if cwd_resolved == resolved or str(cwd_resolved).startswith(str(resolved) + os.sep):
            return True
    return False


def _run_knowledge_map(start_node: str, task_type: str) -> dict[str, Any]:
    """Run knowledge-map for the given start node and return the JSON receipt."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "code" / "specs_validate.py"),
        "knowledge-map",
        "--input-scope", "entry_navigation",
        "--layer", "neighbors",
        "--start-node", start_node,
        "--task-type", task_type,
        "--format", "json",
    ]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        return {"status": "error", "stderr": result.stderr.strip()}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "raw_stdout": result.stdout[:500]}


# ---------------------------------------------------------------------------
# registry helpers (for git.commit-msg and extensible events)
# ---------------------------------------------------------------------------


def load_registry(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise RuntimeError(f"读取 Hook registry 失败: {exc}") from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(f"解析 Hook registry 失败: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Hook registry 顶层必须是 YAML object")
    return data


def hooks_for_event(registry: dict[str, Any], event: str) -> list[dict[str, Any]]:
    hooks = registry.get("hooks", [])
    if not isinstance(hooks, list):
        raise RuntimeError("Hook registry 的 hooks 字段必须是 list")
    matched = []
    for hook in hooks:
        if not isinstance(hook, dict):
            continue
        if hook.get("event") == event and hook.get("status", "active") == "active":
            matched.append(hook)
    return matched


def render_arg(value: str, context: dict[str, str]) -> str:
    rendered = value
    for key, replacement in context.items():
        rendered = rendered.replace("{" + key + "}", replacement)
    if "{" in rendered or "}" in rendered:
        raise RuntimeError(f"Hook command 包含未知占位符: {value}")
    return rendered


def render_command(raw_command: Any, context: dict[str, str]) -> list[str]:
    if not isinstance(raw_command, list) or not raw_command:
        raise RuntimeError("Hook command 必须是非空 list")
    command = []
    for part in raw_command:
        if not isinstance(part, str):
            raise RuntimeError("Hook command 的每个参数都必须是 string")
        command.append(render_arg(part, context))
    return command


# ---------------------------------------------------------------------------
# built-in lifecycle protocol handlers
# ---------------------------------------------------------------------------


def _build_session_start_result(cwd: Path, *, trigger_source: str = "rules") -> dict[str, Any]:
    config = _find_governed_config(cwd)
    if config is None:
        return {
            "governed": False,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "message": "未找到 LDVH-GOVERNED-PROJECTS.yaml，no-op",
        }

    governed = _cwd_in_governed_project(cwd, config)
    result = {
        "governed": governed,
        "cwd": str(cwd),
        "config_path": str(config),
        "trigger_source": trigger_source,
    }
    if not governed:
        result["message"] = "当前 cwd 未命中管辖项目，no-op"
        return result

    # Run knowledge-map to get the entry chain receipt
    km = _run_knowledge_map("rules/LDVH-RUNTIME-PROTOCOL.md", "rules_entry")
    result["receipt"] = km.get("result_status", "unknown")
    result["diagnostics"] = km.get("diagnostics", 0)

    # Extract read_plan and stop_conditions for AI consumption
    read_plan = km.get("read_plan", [])
    stop_conditions = km.get("stop_conditions", [])
    if read_plan:
        result["read_plan"] = read_plan[:8]  # top entries only
    if stop_conditions:
        result["stop_conditions"] = stop_conditions

    diags = km.get("diagnostics")
    has_diagnostics = bool(diags) if isinstance(diags, list) else bool(diags)
    if has_diagnostics:
        result["action_policy"] = "continue_with_limited_receipt"
        result["fallback"] = (
            "知识地图或事实源投影受限；入口握手不阻断行动。AI 应回读 Runtime Protocol、"
            "active specs 和相关事实源原文，并优先修复 diagnostics 指向的问题。"
        )

    return result


def handle_session_start(cwd: Path, *, trigger_source: str = "rules", session_id: str = "") -> int:
    """SessionStart / session-start handler.

    Determine whether *cwd* falls inside an LDVH-governed project.
    If yes, run knowledge-map and return a receipt so the AI can consume
    the full entry chain.
    """
    result = _build_session_start_result(cwd, trigger_source=trigger_source)
    _write_session_receipt(session_id, "session-start", result)
    print(json.dumps(result, ensure_ascii=False))
    return 0


def handle_pre_tool_use(cwd: Path, *, trigger_source: str = "rules", tool_name: str = "", session_id: str = "") -> int:
    """PreToolUse / pre-tool-use handler.

    Check whether the current session has completed the session-start
    handshake before allowing Write/Edit tools.
    """
    config = _find_governed_config(cwd)
    if config is None:
        # No governed config at all — no LDVH project, allow
        print(json.dumps({"blocked": False, "reason": "非管辖项目，no-op",
                          "cwd": str(cwd), "trigger_source": trigger_source}))
        return 0

    governed = _cwd_in_governed_project(cwd, config)
    if not governed:
        print(json.dumps({"blocked": False, "reason": "当前 cwd 未命中管辖项目，no-op",
                          "cwd": str(cwd), "trigger_source": trigger_source}))
        return 0

    # In governed projects, keep the hook non-blocking while making the receipt
    # state queryable. Codex may not surface SessionStart stdout in the thread,
    # so PreToolUse can create the same receipt when a session_id is present.
    result = {
        "blocked": False,
        "cwd": str(cwd),
        "governed": True,
        "trigger_source": trigger_source,
    }
    receipt = _read_session_receipt(session_id)
    if receipt:
        receipt_result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
        result["session_receipt"] = "found"
        if isinstance(receipt_result, dict):
            result["receipt"] = receipt_result.get("receipt", "unknown")
            result["receipt_event"] = receipt.get("event", "")
    elif session_id:
        session_result = _build_session_start_result(cwd, trigger_source=trigger_source)
        _write_session_receipt(session_id, "pre-tool-use-implicit-session-start", session_result)
        result["session_receipt"] = "created_by_pre_tool_use"
        result["receipt"] = session_result.get("receipt", "unknown")
        result["action_policy"] = "continue_with_implicit_receipt"
    else:
        result["session_receipt"] = "unavailable"
        result["warning"] = "管辖项目中，hook payload 未提供 session_id；请确认本会话已完成 session-start。"
    if tool_name:
        result["tool"] = tool_name
    print(json.dumps(result, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# registry-based execution (git.commit-msg and future events)
# ---------------------------------------------------------------------------


def run_event(event: str, registry_path: Path, context: dict[str, str],
              dry_run: bool = False) -> int:
    registry = load_registry(registry_path)
    matched = hooks_for_event(registry, event)
    if not matched:
        print(f"未找到 active Hook event: {event}", file=sys.stderr)
        return 2

    exit_code = 0
    for hook in matched:
        hook_id = hook.get("id", "<unknown>")
        command = render_command(hook.get("command"), context)
        print(f"LDVH Hook {hook_id}: {' '.join(command)}")
        if dry_run:
            continue
        result = subprocess.run(command, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            exit_code = result.returncode
            if hook.get("blocking", True):
                break
    return exit_code


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_stdin() -> Optional[dict[str, Any]]:
    """Try to read a JSON object from stdin (Hook path).  Returns None when
    stdin is not a pipe / empty / unparseable (Rules path)."""
    if sys.stdin.isatty():
        return None
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return None
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None


def _stdin_event(payload: dict[str, Any]) -> str:
    """Return the hook event name from known Codex/AI hook payload shapes."""
    for key in ("event", "hook_event", "hookEvent", "hook_event_name", "hookEventName", "event_name", "eventName"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _stdin_tool_name(payload: dict[str, Any]) -> str:
    """Return the tool name from known hook payload shapes when present."""
    for key in ("tool_name", "toolName", "tool"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _stdin_session_id(payload: dict[str, Any]) -> str:
    """Return the Codex session id from hook payloads when present."""
    for key in ("session_id", "sessionId"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def main(argv: Optional[list[str]] = None) -> int:
    # --- Hook path: stdin JSON ------------------------------------------------
    stdin_payload = _parse_stdin()
    cli_args = list(sys.argv[1:] if argv is None else argv)
    cli_has_explicit_event = len(cli_args) >= 2 and cli_args[0] == "run"
    # Codex command hooks pass JSON on stdin. Plugin-bundled hooks also carry the
    # event in argv (`run pre-tool-use`). If stdin has no event field, keep the
    # explicit CLI event instead of treating it as an unknown empty event.
    if stdin_payload is not None and not cli_has_explicit_event:
        event = _stdin_event(stdin_payload)
        cwd_raw = stdin_payload.get("cwd", os.getcwd())
        cwd = Path(cwd_raw)
        trigger_source = stdin_payload.get("trigger_source", "hook")
        session_id = _stdin_session_id(stdin_payload)

        # Normalize event name: both "SessionStart" (Hook) and "session-start" (CLI) accepted
        normalized = event.replace("_", "-").lower().lstrip("-")

        if normalized in ("session-start", "sessionstart"):
            return handle_session_start(cwd, trigger_source=trigger_source, session_id=session_id)
        if normalized in ("pre-tool-use", "pretooluse"):
            tool = _stdin_tool_name(stdin_payload)
            return handle_pre_tool_use(cwd, trigger_source=trigger_source, tool_name=tool, session_id=session_id)
        if normalized in ("git-commit-msg", "git.commit-msg"):
            context: dict[str, str] = {"cwd": str(cwd)}
            if stdin_payload.get("message_file"):
                context["message_file"] = stdin_payload["message_file"]
            return run_event("git.commit-msg", DEFAULT_REGISTRY, context)

        # Unknown event — try registry lookup
        context = {"cwd": str(cwd)}
        for key, val in stdin_payload.items():
            if isinstance(val, str) and key not in ("event",):
                context[key] = val
        return run_event(event, DEFAULT_REGISTRY, context)

    # --- Rules path: CLI subcommands ------------------------------------------
    parser = argparse.ArgumentParser(
        description="LDVH lifecycle protocol dispatcher — Hook path (stdin) or Rules path (CLI)."
    )
    subparsers = parser.add_subparsers(dest="command")

    # run <event>
    run_parser = subparsers.add_parser("run", help="Execute a lifecycle protocol event.")
    run_parser.add_argument("event", help="Event: session-start | pre-tool-use | git.commit-msg")
    run_parser.add_argument("--cwd", type=Path, default=Path(os.getcwd()),
                            help="Current working directory for the event.")
    run_parser.add_argument("--trigger-source", type=str, choices=["hook", "rules"],
                            default="rules",
                            help="Trigger source: hook (environment) or rules (AI self-trigger).")
    run_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY,
                            help="Hook registry YAML path.")
    run_parser.add_argument("--message-file", type=Path, default=None,
                            help="Commit message file (git.commit-msg only).")
    run_parser.add_argument("--tool-name", type=str, default="",
                            help="Tool name being invoked (pre-tool-use only).")
    run_parser.add_argument("--dry-run", action="store_true",
                            help="Print commands without executing (git.commit-msg only).")

    args = parser.parse_args(cli_args)

    if args.command == "run":
        event = args.event
        cwd = args.cwd.resolve()
        trigger_source = args.trigger_source

        try:
            # --- built-in lifecycle handlers ---
            if event in ("session-start", "SessionStart"):
                return handle_session_start(cwd, trigger_source=trigger_source)

            if event in ("pre-tool-use", "PreToolUse"):
                return handle_pre_tool_use(cwd, trigger_source=trigger_source, tool_name=args.tool_name)

            if event == "git.commit-msg":
                context: dict[str, str] = {}
                if args.message_file is not None:
                    context["message_file"] = str(args.message_file)
                return run_event(event, args.registry, context, dry_run=args.dry_run)

            # --- fallback: registry lookup for unknown events ---
            context: dict[str, str] = {}
            return run_event(event, args.registry, context, dry_run=args.dry_run)

        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    return 2


if __name__ == "__main__":
    sys.exit(main())
