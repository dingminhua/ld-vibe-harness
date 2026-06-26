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
import re
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


def _mark_pre_tool_use_receipt(session_id: str, result: dict[str, Any]) -> None:
    path = _receipt_path(session_id)
    if path is None:
        return
    receipt = _read_session_receipt(session_id)
    if receipt is None:
        return
    observed_at = datetime.now(timezone.utc).isoformat()
    observation = {
        "event": "pre-tool-use",
        "observed_at": observed_at,
        "cwd": result.get("cwd", ""),
        "trigger_source": result.get("trigger_source", ""),
        "session_receipt": result.get("session_receipt", ""),
    }
    if result.get("tool"):
        observation["tool"] = result["tool"]
    if result.get("receipt"):
        observation["receipt"] = result["receipt"]

    events = receipt.get("events")
    if not isinstance(events, list):
        events = []
    events.append(observation)
    receipt["events"] = events[-20:]
    receipt["last_pre_tool_use"] = observation
    receipt["updated_at"] = observed_at
    try:
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
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


def _receipt_matches_cwd(receipt: dict[str, Any], cwd: Path) -> bool:
    result = receipt.get("result")
    if not isinstance(result, dict) or result.get("governed") is not True:
        return False
    candidates = []
    for key in ("cwd", "governed_project_path"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            candidates.append(value)
    for raw in candidates:
        try:
            path = Path(raw).expanduser().resolve()
        except OSError:
            path = Path(raw).expanduser()
        try:
            cwd_resolved = cwd.resolve()
        except OSError:
            cwd_resolved = cwd
        if cwd_resolved == path or str(cwd_resolved).startswith(str(path) + os.sep):
            return True
    return False


def _latest_session_receipt(cwd: Path) -> Optional[dict[str, Any]]:
    root = _receipt_root()
    try:
        paths = sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    except OSError:
        return None
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and _receipt_matches_cwd(data, cwd):
            return data
    return None


def _receipt_read_plan_consumed(receipt: Optional[dict[str, Any]]) -> bool:
    if not receipt:
        return False
    consumed = receipt.get("read_plan_consumed")
    return isinstance(consumed, dict) and consumed.get("status") == "acknowledged"


def _required_read_plan_paths(receipt: dict[str, Any]) -> list[str]:
    result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
    read_plan = result.get("read_plan") if isinstance(result, dict) else []
    required = []
    if isinstance(read_plan, list):
        for item in read_plan:
            if not isinstance(item, dict):
                continue
            if item.get("priority") not in {"P0", "P1"}:
                continue
            path = item.get("path")
            if isinstance(path, str) and path.strip():
                required.append(path.strip())
    return required


def _acknowledge_read_plan(session_id: str, cwd: Path, *, trigger_source: str = "rules") -> dict[str, Any]:
    receipt = _read_session_receipt(session_id) if session_id else _latest_session_receipt(cwd)
    if not receipt:
        return {
            "acknowledged": False,
            "blocked": True,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "reason": "未找到可确认的 session receipt；必须先完成 session-start。",
        }
    ack = {
        "status": "acknowledged",
        "acknowledged_at": datetime.now(timezone.utc).isoformat(),
        "trigger_source": trigger_source,
        "cwd": str(cwd),
        "required_paths": _required_read_plan_paths(receipt),
    }
    receipt["read_plan_consumed"] = ack
    receipt["updated_at"] = ack["acknowledged_at"]
    path = _receipt_path(str(receipt.get("session_id", "")))
    if path is None:
        return {
            "acknowledged": False,
            "blocked": True,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "reason": "receipt 缺少 session_id，无法写入 read_plan 消费证据。",
        }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        return {
            "acknowledged": False,
            "blocked": True,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "reason": f"写入 read_plan 消费证据失败: {exc}",
        }
    return {
        "acknowledged": True,
        "blocked": False,
        "cwd": str(cwd),
        "trigger_source": trigger_source,
        "session_id": receipt.get("session_id", ""),
        "required_paths": ack["required_paths"],
        "receipt": "read_plan_consumed",
    }

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _find_governed_config(cwd: Path) -> Optional[Path]:
    """Find LDVH-GOVERNED-PROJECTS.yaml from cwd or related Git worktrees."""
    direct = _walk_for_governed_config(cwd)
    if direct is not None:
        return direct
    for worktree_root in _git_worktree_roots(cwd):
        config = _walk_for_governed_config(worktree_root)
        if config is not None:
            return config
    return None


def _walk_for_governed_config(cwd: Path) -> Optional[Path]:
    for parent in [cwd, *cwd.parents]:
        config = parent / "LDVH-GOVERNED-PROJECTS.yaml"
        if config.is_file():
            return config
    return None


def _git_text(cwd: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _git_common_dir(cwd: Path) -> str:
    return _git_text(cwd, ["rev-parse", "--path-format=absolute", "--git-common-dir"])


def _git_remote_url(cwd: Path) -> str:
    return _git_text(cwd, ["remote", "get-url", "origin"])


def _git_worktree_roots(cwd: Path) -> list[Path]:
    output = _git_text(cwd, ["worktree", "list", "--porcelain"])
    roots: list[Path] = []
    for line in output.splitlines():
        if not line.startswith("worktree "):
            continue
        raw = line.removeprefix("worktree ").strip()
        if raw:
            roots.append(Path(raw))
    return roots


def _project_git_value(entry: dict[str, Any], key: str) -> str:
    git_info = entry.get("git")
    if not isinstance(git_info, dict):
        return ""
    value = git_info.get(key, "")
    return value.strip() if isinstance(value, str) else ""


def _governed_project_match(cwd: Path, config_path: Path) -> dict[str, Any]:
    """Return deterministic governed-project match metadata for *cwd*."""
    base = {
        "governed": False,
        "governed_via": "",
        "governed_project_id": "",
        "governed_project_path": "",
        "git_common_dir": "",
        "git_remote_url": "",
    }
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return base
    projects = data.get("projects", [])
    if not isinstance(projects, list):
        return base

    try:
        cwd_resolved = cwd.resolve()
    except OSError:
        cwd_resolved = cwd
    current_common_dir = _git_common_dir(cwd_resolved)
    current_remote_url = _git_remote_url(cwd_resolved)
    base["git_common_dir"] = current_common_dir
    base["git_remote_url"] = current_remote_url

    for entry in projects:
        if not isinstance(entry, dict):
            continue
        proj_path = entry.get("path", "")
        if not isinstance(proj_path, str) or not proj_path.strip():
            continue
        resolved = (config_path.parent / proj_path).resolve()
        project_id = entry.get("id", "")
        match = {
            **base,
            "governed": True,
            "governed_project_id": project_id.strip() if isinstance(project_id, str) else "",
            "governed_project_path": str(resolved),
        }
        if cwd_resolved == resolved or str(cwd_resolved).startswith(str(resolved) + os.sep):
            match["governed_via"] = "path"
            return match

        registered_common_dir = _project_git_value(entry, "common_dir")
        if current_common_dir and registered_common_dir and Path(current_common_dir) == Path(registered_common_dir).expanduser():
            match["governed_via"] = "git.common_dir"
            return match

        project_common_dir = _git_common_dir(resolved)
        if current_common_dir and project_common_dir and Path(current_common_dir) == Path(project_common_dir):
            match["governed_via"] = "git.common_dir"
            return match

    return base


def _cwd_in_governed_project(cwd: Path, config_path: Path) -> bool:
    """Return True when *cwd* is inside a directory listed in the config."""
    return bool(_governed_project_match(cwd, config_path).get("governed"))


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

    project_match = _governed_project_match(cwd, config)
    governed = bool(project_match.get("governed"))
    result = {
        "governed": governed,
        "cwd": str(cwd),
        "config_path": str(config),
        "trigger_source": trigger_source,
    }
    if not governed:
        result["message"] = "当前 cwd 未命中管辖项目，no-op"
        return result
    for key in ("governed_via", "governed_project_id", "governed_project_path", "git_common_dir", "git_remote_url"):
        value = project_match.get(key)
        if value:
            result[key] = value

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


def handle_acknowledge_read_plan(cwd: Path, *, trigger_source: str = "rules", session_id: str = "") -> int:
    """Record that the AI consumed the current receipt read_plan P0/P1 entries."""
    result = _acknowledge_read_plan(session_id, cwd, trigger_source=trigger_source)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("acknowledged") else 1


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


MUTATING_SHELL_PATTERNS = [
    re.compile(r"(^|[;&|]\s*)apply_patch\b"),
    re.compile(r"(^|\s)cat\s+>"),
    re.compile(r"(^|\s)tee\s+"),
    re.compile(r"(^|\s)(rm|mv|cp)\s+"),
    re.compile(r"(^|\s)git\s+(commit|reset|checkout|merge|rebase|push)\b"),
    re.compile(r"(^|\s)npm\s+version\b"),
    re.compile(r"python3?\s+.*\b(write_text|open\([^)]*['\"]w|unlink|remove|rmtree)\b"),
]


def _stdin_tool_command(payload: dict[str, Any]) -> str:
    for key in ("command", "cmd"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    for key in ("tool_input", "toolInput", "input", "args", "arguments"):
        value = payload.get(key)
        if isinstance(value, dict):
            for nested_key in ("command", "cmd"):
                nested = value.get(nested_key)
                if isinstance(nested, str):
                    return nested
        if isinstance(value, str):
            return value
    return ""


def _tool_requires_read_plan_consumed(tool_name: str, command: str = "") -> bool:
    normalized = tool_name.strip().lower()
    if normalized in {"write", "edit", "multiedit", "multi_edit", "apply_patch"}:
        return True
    if normalized == "bash" and command and any(pattern.search(command) for pattern in MUTATING_SHELL_PATTERNS):
        return True
    return False


def _read_plan_guard_result(cwd: Path, receipt: Optional[dict[str, Any]], *, trigger_source: str,
                            tool_name: str, command: str, action: str) -> Optional[dict[str, Any]]:
    if _receipt_read_plan_consumed(receipt):
        return None
    required_paths = _required_read_plan_paths(receipt) if receipt else []
    return {
        "blocked": True,
        "cwd": str(cwd),
        "governed": True,
        "trigger_source": trigger_source,
        "tool": tool_name,
        "action": action,
        "reason": "管辖项目写入/提交前必须先消费 session-start receipt 的 P0/P1 read_plan，并记录 read_plan_consumed 证据。",
        "required_paths": required_paths,
        "next_action": "读取 required_paths 后运行 `python3 code/hook_dispatch.py run acknowledge-read-plan --cwd <cwd>`；支持 session_id 的 Hook 环境应传入同一 session_id。",
        "command_observed": command[:200] if command else "",
    }


def handle_pre_tool_use(cwd: Path, *, trigger_source: str = "rules", tool_name: str = "",
                        session_id: str = "", tool_command: str = "") -> int:
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

    project_match = _governed_project_match(cwd, config)
    governed = bool(project_match.get("governed"))
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
    for key in ("governed_via", "governed_project_id", "governed_project_path", "git_common_dir", "git_remote_url"):
        value = project_match.get(key)
        if value:
            result[key] = value
    receipt = _read_session_receipt(session_id) if session_id else _latest_session_receipt(cwd)
    if receipt:
        receipt_result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
        result["session_receipt"] = "found"
        if isinstance(receipt_result, dict):
            result["receipt"] = receipt_result.get("receipt", "unknown")
            result["receipt_event"] = receipt.get("event", "")
        if _receipt_read_plan_consumed(receipt):
            result["read_plan_consumed"] = "acknowledged"
    elif session_id:
        session_result = _build_session_start_result(cwd, trigger_source=trigger_source)
        _write_session_receipt(session_id, "pre-tool-use-implicit-session-start", session_result)
        receipt = _read_session_receipt(session_id)
        result["session_receipt"] = "created_by_pre_tool_use"
        result["receipt"] = session_result.get("receipt", "unknown")
        result["action_policy"] = "read_plan_ack_required_before_write"
    else:
        result["session_receipt"] = "unavailable"
        result["warning"] = "管辖项目中，hook payload 未提供 session_id；请确认本会话已完成 session-start。"
    if tool_name:
        result["tool"] = tool_name
    if tool_command:
        result["command_observed"] = tool_command[:200]
    if _tool_requires_read_plan_consumed(tool_name, tool_command):
        blocked = _read_plan_guard_result(
            cwd,
            receipt,
            trigger_source=trigger_source,
            tool_name=tool_name,
            command=tool_command,
            action="pre-tool-use",
        )
        if blocked:
            print(json.dumps(blocked, ensure_ascii=False))
            return 1
    if receipt and session_id:
        _mark_pre_tool_use_receipt(session_id, result)
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


def _guard_git_commit_msg(cwd: Path, *, trigger_source: str) -> Optional[dict[str, Any]]:
    config = _find_governed_config(cwd)
    if config is None:
        return None
    project_match = _governed_project_match(cwd, config)
    if not project_match.get("governed"):
        return None
    return _read_plan_guard_result(
        cwd,
        _latest_session_receipt(cwd),
        trigger_source=trigger_source,
        tool_name="git.commit-msg",
        command="git commit",
        action="git.commit-msg",
    )


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
        if normalized in ("acknowledge-read-plan", "acknowledgereadplan"):
            return handle_acknowledge_read_plan(cwd, trigger_source=trigger_source, session_id=session_id)
        if normalized in ("pre-tool-use", "pretooluse"):
            tool = _stdin_tool_name(stdin_payload)
            command = _stdin_tool_command(stdin_payload)
            return handle_pre_tool_use(
                cwd,
                trigger_source=trigger_source,
                tool_name=tool,
                session_id=session_id,
                tool_command=command,
            )
        if normalized in ("git-commit-msg", "git.commit-msg"):
            blocked = _guard_git_commit_msg(cwd, trigger_source=trigger_source)
            if blocked:
                print(json.dumps(blocked, ensure_ascii=False))
                return 1
            context: dict[str, str] = {"cwd": str(cwd), "repo_root": str(cwd)}
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
    run_parser.add_argument("event", help="Event: session-start | acknowledge-read-plan | pre-tool-use | git.commit-msg")
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
    run_parser.add_argument("--tool-command", type=str, default="",
                            help="Tool command or payload summary (pre-tool-use only).")
    run_parser.add_argument("--session-id", type=str, default="",
                            help="Session id for receipt lookup or acknowledgement.")
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
                return handle_session_start(cwd, trigger_source=trigger_source, session_id=args.session_id)

            if event in ("acknowledge-read-plan", "AcknowledgeReadPlan"):
                return handle_acknowledge_read_plan(cwd, trigger_source=trigger_source, session_id=args.session_id)

            if event in ("pre-tool-use", "PreToolUse"):
                return handle_pre_tool_use(
                    cwd,
                    trigger_source=trigger_source,
                    tool_name=args.tool_name,
                    session_id=args.session_id,
                    tool_command=args.tool_command,
                )

            if event == "git.commit-msg":
                blocked = _guard_git_commit_msg(cwd, trigger_source=trigger_source)
                if blocked:
                    print(json.dumps(blocked, ensure_ascii=False))
                    return 1
                context: dict[str, str] = {"cwd": str(cwd), "repo_root": str(cwd)}
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
