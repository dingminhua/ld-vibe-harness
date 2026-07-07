#!/usr/bin/env python3
"""Thin WorkBuddy hook shim for the repo-local LDVH V3 sample package.

This shim intentionally keeps all LDVH decisions in code/runtime_adapter.py.
It is not installed by this repository.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_MARKERS = ("code/runtime_adapter.py", "specs/00-理念与构成.md")


TRIGGER_SOURCE = "workbuddy.ldvh-plugin"
RESEARCH_SPARK_SLUG = "workbuddy-hook-three-event-research-capture"
RESEARCH_SPARK_TITLE = "WorkBuddy Hook 三类事件研究采样"
REQUIRED_ENTRY_PATHS = (
    "specs/00-理念与构成.md",
    "specs/01-保障与衔接.md",
    "specs/02-AI行为规范.md",
)
EVENT_MAP = {
    "sessionstart": "SessionStart",
    "session_start": "SessionStart",
    "pretooluse": "PreToolUse",
    "pre_tool_use": "PreToolUse",
    "stop": "Stop",
}
ADAPTER_EVENT_MAP = {
    "SessionStart": "ldvh.session_start",
    "PreToolUse": "ldvh.pre_tool_use",
    "Stop": "ldvh.completion_claim",
}
READ_ONLY_TOOLS = {"read", "grep", "glob", "ls"}
COMMAND_EXECUTION_TOOLS = {
    "bash",
    "exec_command",
    "functions.exec_command",
    "mcp__functions__exec_command",
    "mcp__developer__exec_command",
    "shell",
}
READ_ONLY_COMMANDS = {"cat", "find", "grep", "head", "ls", "nl", "pwd", "rg", "sed", "tail", "wc"}
READ_ONLY_GIT_SUBCOMMANDS = {
    "branch",
    "diff",
    "grep",
    "log",
    "ls-files",
    "remote",
    "rev-parse",
    "show",
    "status",
}
READ_ONLY_SHELL_PIPE_COMMANDS = READ_ONLY_COMMANDS | {"xargs"}
CONTROLLED_BOOTSTRAP_PYTHON_SCRIPTS = {"code/acknowledge_read_plan.py"}


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


def adapter_event(event: str) -> str:
    return ADAPTER_EVENT_MAP.get(event, "")


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
    for key in ("tool_input", "toolInput", "input", "arguments", "parameters"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip().startswith("{"):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    return {}


def command_text(payload: dict[str, Any]) -> str:
    tool = tool_input(payload)
    return first_text(tool.get("command"), tool.get("cmd"), payload.get("command"), payload.get("cmd"))


def command_parts(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def split_unquoted_pipes(command: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    quote = ""
    escaped = False
    for char in command:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            current.append(char)
            quote = char
            continue
        if char == "|":
            segments.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    segments.append("".join(current).strip())
    return segments


def is_likely_read_only_command(command: str) -> bool:
    stripped = command.strip()
    if not stripped or re.search(r"[;&><`$()\n\r]", stripped):
        return False
    segments = split_unquoted_pipes(stripped)
    if len(segments) > 1:
        return all(is_likely_read_only_command_segment(segment) for segment in segments)
    return is_likely_read_only_command_segment(stripped)


def is_likely_read_only_command_segment(command: str) -> bool:
    stripped = command.strip()
    if not stripped:
        return False
    parts = command_parts(stripped)
    if not parts:
        return False
    executable = Path(parts[0]).name.lower()
    if executable == "find" and "-exec" in parts:
        return False
    if executable == "sed" and any(part == "-i" or part.startswith("-i") or part == "--in-place" or part.startswith("--in-place=") for part in parts[1:]):
        return False
    if executable == "git":
        return len(parts) > 1 and parts[1].lower() in READ_ONLY_GIT_SUBCOMMANDS
    return executable in READ_ONLY_SHELL_PIPE_COMMANDS


def is_controlled_read_plan_bootstrap_command(command: str, cwd: Path, ldvh_root: Path) -> bool:
    stripped = command.strip()
    if not stripped or re.search(r"[;&|><`$()\n\r]", stripped):
        return False
    parts = command_parts(stripped)
    if len(parts) < 2:
        return False
    executable = Path(parts[0]).name.lower()
    if executable not in {"python", "python3"}:
        return False
    script = Path(parts[1].strip()).expanduser()
    resolved_script = script if script.is_absolute() else cwd / script
    expected_scripts = {
        (ldvh_root / script_path).resolve(strict=False)
        for script_path in CONTROLLED_BOOTSTRAP_PYTHON_SCRIPTS
    }
    return resolved_script.resolve(strict=False) in expected_scripts


def is_command_execution_tool(payload: dict[str, Any]) -> bool:
    return any(name in COMMAND_EXECUTION_TOOLS for name in tool_name_candidates(payload))


def tool_name_candidates(payload: dict[str, Any]) -> list[str]:
    raw_names = [
        payload.get("tool_name"),
        payload.get("toolName"),
        payload.get("name"),
        payload.get("tool"),
    ]
    names: list[str] = []
    for raw in raw_names:
        if not isinstance(raw, str) or not raw.strip():
            continue
        lowered = raw.strip().lower()
        names.append(lowered)
        if "__" in lowered:
            names.append(lowered.replace("__", "."))
    return list(dict.fromkeys(names))


def command_from_record(record: dict[str, Any]) -> str:
    candidates: list[Any] = []
    item = record.get("payload") if isinstance(record.get("payload"), dict) else record
    if isinstance(item, dict):
        candidates.extend([item.get("arguments"), item.get("input"), item.get("tool_input"), item.get("toolInput")])
    for candidate in candidates:
        if isinstance(candidate, str):
            try:
                candidate = json.loads(candidate)
            except json.JSONDecodeError:
                return first_text(candidate)
        if isinstance(candidate, dict):
            command = first_text(candidate.get("cmd"), candidate.get("command"))
            if command:
                return command
    return first_text(record.get("cmd"), record.get("command"))


def transcript_read_commands(payload: dict[str, Any]) -> list[str]:
    raw_path = first_text(payload.get("transcript_path"), payload.get("transcriptPath"))
    if not raw_path:
        return []
    transcript_path = Path(raw_path).expanduser()
    if not transcript_path.is_file():
        return []
    commands: list[str] = []
    try:
        lines = transcript_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = record.get("payload") if isinstance(record, dict) else {}
        if not isinstance(item, dict):
            continue
        record_type = str(item.get("type") or record.get("type") or "")
        if record_type and record_type not in {"function_call", "tool_call"}:
            continue
        command = command_from_record(record)
        if command and is_likely_read_only_command(command):
            commands.append(command)
    return commands


def normalize_read_path_candidate(raw: str) -> str:
    candidate = raw.strip().strip("'\"").rstrip(",")
    while candidate.startswith("./"):
        candidate = candidate[2:]
    if not candidate or candidate.startswith(("-", "/", "~")):
        return ""
    if candidate.startswith(("specs/", "code/docs/", "ldvh-base/", "hooks/", "code/", "tests/")):
        return candidate
    if candidate.endswith((".md", ".py", ".json", ".toml", ".yaml", ".yml", ".txt")) and "/" in candidate:
        return candidate
    return ""


def transcript_read_paths(payload: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for command in transcript_read_commands(payload):
        for part in command_parts(command):
            candidate = normalize_read_path_candidate(part)
            if candidate:
                paths.append(candidate)
    return list(dict.fromkeys(paths))


def acknowledged_paths(payload: dict[str, Any]) -> list[str]:
    explicit = list_text(payload.get("acknowledged_paths") or payload.get("acknowledgedPaths"))
    return list(dict.fromkeys([*explicit, *transcript_read_paths(payload)]))


def target_path_from_command(payload: dict[str, Any]) -> str:
    command = command_text(payload)
    if not command:
        return ""
    for pattern in (
        r"^\*\*\* Update File: (.+)$",
        r"^\*\*\* Add File: (.+)$",
        r"^\*\*\* Delete File: (.+)$",
    ):
        match = re.search(pattern, command, re.MULTILINE)
        if match:
            return match.group(1).strip()
    for part in reversed(command_parts(command)):
        candidate = part.strip().strip("'\"")
        if not candidate or candidate.startswith("-"):
            continue
        if candidate in {"python", "python3", "pytest", "py_compile"}:
            continue
        if "/" in candidate or candidate.endswith((".md", ".py", ".json", ".toml", ".yaml", ".yml", ".txt")):
            return candidate
    return ""


def patch_text(payload: dict[str, Any]) -> str:
    tool = tool_input(payload)
    return first_text(
        payload.get("patch"),
        payload.get("input"),
        payload.get("command"),
        tool.get("patch"),
        tool.get("input"),
        tool.get("command"),
        tool.get("cmd"),
    )


def target_paths_from_patch(payload: dict[str, Any]) -> list[str]:
    raw = patch_text(payload)
    if not raw:
        return []
    values: list[str] = []
    for pattern in (
        r"^\*\*\* Update File: (.+)$",
        r"^\*\*\* Add File: (.+)$",
        r"^\*\*\* Delete File: (.+)$",
    ):
        values.extend(match.strip() for match in re.findall(pattern, raw, flags=re.MULTILINE))
    return values


def target_path_values(payload: dict[str, Any], cwd: Path) -> list[str]:
    tool = tool_input(payload)
    candidates = [
        payload.get("target_path"),
        payload.get("targetPath"),
        payload.get("file_path"),
        payload.get("filePath"),
        payload.get("path"),
        tool.get("file_path"),
        tool.get("filePath"),
        tool.get("path"),
        tool.get("target_path"),
        tool.get("targetPath"),
    ]
    values: list[str] = []
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            values.append(candidate.strip())
    for target_paths in (
        payload.get("target_paths"),
        payload.get("targetPaths"),
        tool.get("target_paths"),
        tool.get("targetPaths"),
        payload.get("file_paths"),
        payload.get("filePaths"),
        payload.get("paths"),
        tool.get("file_paths"),
        tool.get("filePaths"),
        tool.get("paths"),
    ):
        target_paths = list_text(target_paths)
        for candidate in target_paths:
            if isinstance(candidate, str) and candidate.strip():
                values.append(candidate.strip())
    values.extend(target_paths_from_patch(payload))
    command_target = target_path_from_command(payload)
    if command_target:
        values.append(command_target)
    return list(dict.fromkeys(values))


def target_path(payload: dict[str, Any], cwd: Path) -> str:
    values = target_path_values(payload, cwd)
    return values[0] if values else ""


def task_text(payload: dict[str, Any]) -> str:
    return first_text(
        payload.get("task"),
        payload.get("prompt"),
        payload.get("user_prompt"),
        payload.get("userPrompt"),
        payload.get("message"),
    )


def operation(payload: dict[str, Any]) -> str:
    tool_names = tool_name_candidates(payload)
    if any(name in READ_ONLY_TOOLS for name in tool_names):
        return "read"
    if any(name in COMMAND_EXECUTION_TOOLS for name in tool_names) and is_likely_read_only_command(command_text(payload)):
        return "read"
    return first_text(payload.get("operation"), "write")


def adapter_payload(payload: dict[str, Any], event: str, cwd: Path) -> dict[str, Any]:
    session_id = first_text(payload.get("session_id"), payload.get("sessionId"), "workbuddy-hook")
    return {
        "event": event,
        "session_id": session_id,
        "cwd": cwd.as_posix(),
        "config_root": first_text(payload.get("config_root"), payload.get("configRoot"), os.environ.get("LDVH_CONFIG_ROOT")),
        "target_path": target_path(payload, cwd),
        "target_paths": target_path_values(payload, cwd),
        "operation": operation(payload),
        "task": task_text(payload),
        "acknowledged_paths": acknowledged_paths(payload),
        "verification_evidence": list_text(payload.get("verification_evidence") or payload.get("verificationEvidence")),
        "trigger_source": TRIGGER_SOURCE,
    }



def emit_json(data: dict[str, Any]) -> int:
    print(json.dumps(data, ensure_ascii=False))
    return 0


def emit_warning(message: str) -> int:
    return emit_json({"systemMessage": message})


def hook_spark_capture_enabled() -> bool:
    raw = os.environ.get("LDVH_HOOK_SPARK_CAPTURE", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def local_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def yaml_scalar(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def yaml_block(value: str, indent: int = 2) -> str:
    prefix = " " * indent
    lines = value.splitlines() or [""]
    return "\n".join(prefix + line for line in lines)


def spark_dir(ldvh_root: Path) -> Path:
    override = first_text(os.environ.get("LDVH_HOOK_SPARK_DIR"))
    if override:
        return Path(override).expanduser().resolve()
    return ldvh_root / "ldvh-base" / "sparks"


def next_spark_id(directory: Path) -> str:
    max_num = 0
    if directory.exists():
        for path in directory.glob("spark-[0-9][0-9][0-9][0-9]-*.yaml"):
            match = re.match(r"spark-(\d{4})-", path.name)
            if match:
                max_num = max(max_num, int(match.group(1)))
    return f"spark-{max_num + 1:04d}"


def research_spark_path(ldvh_root: Path) -> Path:
    directory = spark_dir(ldvh_root)
    matches = sorted(directory.glob(f"spark-[0-9][0-9][0-9][0-9]-{RESEARCH_SPARK_SLUG}.yaml"))
    if matches:
        return matches[0]
    return directory / f"{next_spark_id(directory)}-{RESEARCH_SPARK_SLUG}.yaml"


def create_research_spark(path: Path, now: str, summary: str) -> None:
    spark_id = path.name.split("-", 2)
    object_id = "-".join(spark_id[:2]) if len(spark_id) >= 2 else "spark-0000"
    text = f"""id: {object_id}
type: spark
title: {RESEARCH_SPARK_TITLE}
status: pending
created: {yaml_scalar(now)}
updated: {yaml_scalar(now)}
description: |
  本 Spark 作为 WorkBuddy 环境插件三类 lifecycle hook 的研究采样入口。它记录 SessionStart、PreToolUse 和 Stop 在真实会话中的触发样本，用于后续判断哪些事件适合承载治理提醒、工具前置阻断和完成声明检查。

  本 Spark 不定义 hook 规则、payload schema、阻断策略或安装完成声明；这些仍由 specs、Code 和环境插件边界承接。自动追加的 evolution 只作为研究线索，后续若要形成稳定规则，应分流到 WorkCase、ADR、Study、docs 或 specs。
source: workbuddy_hook
source_detail: |
  WorkBuddy LDVH v3 环境插件 `hooks/ldvh_runtime_shim.py` 自动捕获 lifecycle event 元数据。默认只写事件名、session、cwd、工具名、目标路径和 payload key 摘要，不写完整用户提示或完整工具参数。
priority: P1
input_refs:
  - specs/01-保障与衔接.md
  - specs/10-安装与配置规范.md
  - specs/33-环境插件编写与更新行动模板.md
  - hooks/environment-plugins/workbuddy-ldvh-v3/hooks/hooks.json
resolved_to: ''
resolved_at: ''
discard_reason: ''
related_sparks: []
related_workcases: []
related_adrs: []
related_studies: []
related_docs:
  - specs/01-保障与衔接.md
  - specs/10-安装与配置规范.md
  - specs/33-环境插件编写与更新行动模板.md
  - hooks/environment-plugins/workbuddy-ldvh-v3/hooks/hooks.json
  - hooks/environment-plugins/workbuddy-ldvh-v3/hooks/ldvh_runtime_shim.py
evolution:
  - at: {yaml_scalar(now)}
    summary: |
{yaml_block(summary, 6)}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_research_spark(path: Path, now: str, summary: str) -> None:
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"^updated: .*$", f"updated: {yaml_scalar(now)}", raw, count=1, flags=re.MULTILINE)
    if "\nevolution:\n" not in raw:
        raw = raw.rstrip() + "\nevolution:\n"
    entry = f"  - at: {yaml_scalar(now)}\n    summary: |\n{yaml_block(summary, 6)}\n"
    path.write_text(raw.rstrip() + "\n" + entry, encoding="utf-8")


def research_summary(payload: dict[str, Any], event: str, cwd: Path) -> str:
    tool_name = first_text(payload.get("tool_name"), payload.get("toolName"))
    session_id = first_text(payload.get("session_id"), payload.get("sessionId"), "workbuddy-hook")
    target = target_path(payload, cwd)
    keys = ", ".join(sorted(str(key) for key in payload.keys())[:20])
    lines = [
        f"event={event}",
        f"session_id={session_id}",
        f"cwd={cwd.as_posix()}",
    ]
    if tool_name:
        lines.append(f"tool_name={tool_name}")
    if target:
        lines.append(f"target_path={target}")
    if keys:
        lines.append(f"payload_keys={keys}")
    return "\n".join(lines)


def record_hook_event_to_spark(ldvh_root: Path, payload: dict[str, Any], event: str, cwd: Path) -> None:
    if not hook_spark_capture_enabled():
        return
    now = local_timestamp()
    path = research_spark_path(ldvh_root)
    summary = research_summary(payload, event, cwd)
    try:
        if path.exists():
            append_research_spark(path, now, summary)
        else:
            create_research_spark(path, now, summary)
    except OSError:
        return


def read_adapter_json(stdout: str) -> dict[str, Any]:
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def diagnostics(result: dict[str, Any]) -> list[dict[str, Any]]:
    value = result.get("diagnostics")
    return value if isinstance(value, list) else []


def summary_status(result: dict[str, Any]) -> str:
    summary = result.get("summary")
    if not isinstance(summary, dict):
        return ""
    return str(summary.get("status") or "")


def is_blocking_result(result: dict[str, Any]) -> bool:
    summary = result.get("summary")
    if isinstance(summary, dict) and int(summary.get("blocking") or 0) > 0:
        return True
    return summary_status(result) == "blocked"


def has_runtime_diagnostics(result: dict[str, Any]) -> bool:
    return bool(diagnostics(result)) or summary_status(result) not in {"", "ok", "no_op"}


def should_deny_pre_tool(result: dict[str, Any]) -> bool:
    return is_blocking_result(result)


def diagnostic_reason(result: dict[str, Any]) -> str:
    items = diagnostics(result)
    if not items:
        return "LDVH V3 runtime adapter returned a blocking result."
    parts = []
    for item in items[:3]:
        code = str(item.get("code") or "LDVH_RUNTIME_CHECK")
        message = str(item.get("message") or "").strip()
        parts.append(f"{code}: {message}" if message else code)
    if len(items) > 3:
        parts.append(f"... plus {len(items) - 3} more")
    return "；".join(parts)


def adapter_dispatch(result: dict[str, Any]) -> dict[str, Any]:
    value = result.get("dispatch")
    return value if isinstance(value, dict) else {}


def session_additional_context(result: dict[str, Any]) -> str:
    guide = adapter_dispatch(result).get("action_guide")
    guide = guide if isinstance(guide, dict) else {}
    read_plan = guide.get("task_read_plan")
    read_plan = read_plan if isinstance(read_plan, list) else []
    paths = [
        str(item.get("path") or item.get("label") or "").strip()
        for item in read_plan
        if isinstance(item, dict) and str(item.get("path") or item.get("label") or "").strip()
    ]
    if not paths:
        return "LDVH V3 session hook ran. Before substantive edits, identify the applicable LDVH read plan and stop conditions."
    return (
        "LDVH V3 session read plan is active. Before substantive edits, read: "
        + ", ".join(paths[:5])
        + ". Treat this hook output as guidance, not authorization or completion evidence."
    )


def pre_tool_context(result: dict[str, Any]) -> str:
    dispatch = adapter_dispatch(result)
    preflight = dispatch.get("preflight")
    preflight = preflight if isinstance(preflight, dict) else {}
    required = preflight.get("required_read_plan")
    required = required if isinstance(required, list) else []
    paths = [
        str(item.get("path") or "").strip()
        for item in required
        if isinstance(item, dict) and str(item.get("path") or "").strip()
    ]
    if paths:
        return "LDVH V3 pre-tool check passed. Relevant read plan: " + ", ".join(paths[:9])
    return "LDVH V3 pre-tool check passed."


def pre_tool_deny(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": diagnostic_reason(result),
        }
    }


def workbuddy_protocol_output(event: str, result: dict[str, Any]) -> dict[str, Any]:
    if event == "SessionStart":
        if is_blocking_result(result):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": "LDVH V3 session hook returned a blocking diagnostic: " + diagnostic_reason(result),
                }
            }
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": session_additional_context(result),
            }
        }

    if event == "PreToolUse":
        if should_deny_pre_tool(result):
            return pre_tool_deny(result)
        if is_blocking_result(result):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": "LDVH V3 pre-tool warning: " + diagnostic_reason(result),
                }
            }
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": pre_tool_context(result),
            }
        }

    if event == "Stop":
        message = "LDVH V3 completion check passed."
        if has_runtime_diagnostics(result):
            message = "LDVH V3 completion check warning: " + diagnostic_reason(result)
        return {"continue": True, "systemMessage": message}

    return {"systemMessage": "LDVH V3 hook ran for unsupported event mapping."}


def main() -> int:
    raw = sys.stdin.read()
    payload = read_payload(raw)
    cwd = Path(first_text(payload.get("cwd"), os.getcwd())).expanduser()
    event = normalize_event(payload)
    if not event:
        return emit_warning(
            "LDVH_WORKBUDDY_SHIM_EVENT_UNKNOWN: WorkBuddy hook payload did not contain a supported SessionStart, PreToolUse, or Stop event."
        )

    ldvh_root = find_ldvh_root(payload, cwd)
    if ldvh_root is None:
        return emit_warning(
            "LDVH_WORKBUDDY_SHIM_ROOT_NOT_FOUND: LDVH root was not found from LDVH_ROOT, payload, cwd, or shim path; hook shim allowed the event."
        )

    record_hook_event_to_spark(ldvh_root, payload, event, cwd)
    runtime_event = adapter_event(event)
    if not runtime_event:
        return 0

    if (
        event == "PreToolUse"
        and is_command_execution_tool(payload)
        and is_controlled_read_plan_bootstrap_command(command_text(payload), cwd, ldvh_root)
    ):
        return 0

    if event == "PreToolUse" and operation(payload) == "read":
        return 0

    runtime_adapter = ldvh_root / "code" / "runtime_adapter.py"
    adapter_json = json.dumps(adapter_payload(payload, runtime_event, cwd), ensure_ascii=False)
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
    completed = subprocess.run(command, text=True, capture_output=True)
    parsed = read_adapter_json(completed.stdout)
    if not parsed:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit={completed.returncode}"
        return emit_warning("LDVH_WORKBUDDY_SHIM_ADAPTER_OUTPUT_INVALID: " + detail[:500])
    if summary_status(parsed) == "no_op":
        return 0
    return emit_json(workbuddy_protocol_output(event, parsed))


if __name__ == "__main__":
    raise SystemExit(main())
