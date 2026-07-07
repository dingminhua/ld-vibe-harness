#!/usr/bin/env python3
"""Thin Codex hook shim for the repo-local LDVH V3 sample package.

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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_MARKERS = ("code/runtime_adapter.py", "specs/00-理念与构成.md")
TRIGGER_SOURCE = "codex.ldvh-plugin"
RESEARCH_SPARK_SLUG = "codex-hook-six-event-research-capture"
RESEARCH_SPARK_TITLE = "Codex Hook 六类事件研究采样"
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
    "posttooluse": "PostToolUse",
    "post_tool_use": "PostToolUse",
    "userpromptsubmit": "UserPromptSubmit",
    "user_prompt_submit": "UserPromptSubmit",
    "stop": "Stop",
    "notification": "Notification",
}
ADAPTER_EVENT_MAP = {
    "SessionStart": "ldvh.session_start",
    "PreToolUse": "ldvh.pre_tool_use",
    "Stop": "ldvh.completion_claim",
}
READ_ONLY_TOOLS = {
    "read",
    "grep",
    "glob",
    "ls",
    "read_thread",
    "read_thread_terminal",
    "codex_app.read_thread",
    "codex_app.read_thread_terminal",
    "codex_appread_thread",
    "codex_appread_thread_terminal",
    "wait_agent",
    "multi_agent.wait_agent",
    "multi_agent_v1.wait_agent",
    "multi_agent_v1wait_agent",
}
WRITE_TOOLS = {"write", "edit", "multiedit", "multi_edit", "apply_patch", "functions.apply_patch"}
READ_OPERATIONS = {"read", "inspect", "search", "grep", "list", "audit", "review", "diagnose"}
WRITE_OPERATIONS = {"write", "edit", "apply_patch", "commit", "delete", "move", "install", "update"}
COLLABORATION_TOOL_NAMES = {
    "spawn_agent",
    "multi_agent.spawn_agent",
    "multi_agent_v1.spawn_agent",
    "send_input",
    "multi_agent.send_input",
    "multi_agent_v1.send_input",
    "multi_agent_v1send_input",
}
READ_ONLY_INTENT_MARKERS = ("read-only", "readonly", "只读", "不要修改", "不要写", "不要提交", "do not modify", "do not edit", "do not commit")
READ_ONLY_COMMANDS = {"cat", "find", "grep", "head", "ls", "nl", "pwd", "rg", "sed", "sleep", "tail", "wc"}
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
READ_ONLY_PYTHON_SCRIPT_EVENTS = {
    "code/session_start.py": None,
    "code/runtime_adapter.py": {"session-start", "session_start", "--help", "-h"},
}


@dataclass(frozen=True)
class ActionClassification:
    operation: str
    side_effect_class: str
    requires_preflight: bool
    reason: str


@dataclass(frozen=True)
class ToolCall:
    namespace: str
    name: str
    full_name: str
    arguments: dict[str, Any]
    intent_text: str


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


def split_unquoted_and_chains(command: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    quote = ""
    escaped = False
    index = 0
    while index < len(command):
        char = command[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            index += 1
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            current.append(char)
            quote = char
            index += 1
            continue
        if char == "&" and index + 1 < len(command) and command[index + 1] == "&":
            segments.append("".join(current).strip())
            current = []
            index += 2
            continue
        current.append(char)
        index += 1
    segments.append("".join(current).strip())
    return segments


def is_likely_read_only_command(command: str) -> bool:
    stripped = command.strip()
    if not stripped or re.search(r"[;><`$()\n\r]", stripped):
        return False
    chain_segments = split_unquoted_and_chains(stripped)
    if len(chain_segments) > 1:
        return all(is_likely_read_only_command(segment) for segment in chain_segments)
    pipe_segments = split_unquoted_pipes(stripped)
    if len(pipe_segments) > 1:
        return all(is_likely_read_only_command_segment(segment) for segment in pipe_segments)
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
        return git_subcommand(parts) in READ_ONLY_GIT_SUBCOMMANDS
    if executable in {"python", "python3"} and len(parts) > 1:
        return is_allowed_read_only_python(parts)
    return executable in READ_ONLY_SHELL_PIPE_COMMANDS


def git_subcommand(parts: list[str]) -> str:
    index = 1
    while index < len(parts):
        part = parts[index]
        lowered = part.lower()
        if lowered in {"-c", "--git-dir", "--work-tree"}:
            index += 2
            continue
        if lowered.startswith("-c") and lowered != "-c":
            index += 1
            continue
        if lowered.startswith("--git-dir=") or lowered.startswith("--work-tree="):
            index += 1
            continue
        if lowered.startswith("-"):
            index += 1
            continue
        return lowered
    return ""


def is_allowed_read_only_python(parts: list[str]) -> bool:
    script = parts[1].strip()
    normalized_script = script.replace("\\", "/")
    for allowed_script, allowed_events in READ_ONLY_PYTHON_SCRIPT_EVENTS.items():
        if normalized_script != allowed_script and not normalized_script.endswith("/" + allowed_script):
            continue
        if allowed_events is None:
            return True
        event = parts[2].strip() if len(parts) > 2 else ""
        return event in allowed_events
    return False


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


def explicit_operation(payload: dict[str, Any]) -> str:
    tool = tool_input(payload)
    raw = first_text(payload.get("operation"), payload.get("op"), tool.get("operation"), tool.get("op"))
    return raw.replace("-", "_").lower()


def tool_name(payload: dict[str, Any]) -> str:
    return first_text(payload.get("tool_name"), payload.get("toolName"), payload.get("name")).lower()


def normalize_tool_call(payload: dict[str, Any]) -> ToolCall:
    arguments = tool_input(payload)
    raw_namespace = first_text(payload.get("namespace"), payload.get("tool_namespace"), payload.get("toolNamespace"))
    raw_name = tool_name(payload)
    if not raw_name:
        raw_name = first_text(payload.get("tool"), payload.get("toolName"), payload.get("name")).lower()
    if "." in raw_name and not raw_namespace:
        namespace, name = raw_name.rsplit(".", 1)
    else:
        namespace, name = raw_namespace.lower(), raw_name
    full_name = f"{namespace}.{name}" if namespace and name else name or raw_name
    intent_values = [
        payload.get("operation"),
        payload.get("task"),
        payload.get("prompt"),
        payload.get("message"),
        arguments.get("operation"),
        arguments.get("task"),
        arguments.get("prompt"),
        arguments.get("message"),
        arguments.get("question"),
    ]
    return ToolCall(
        namespace=namespace,
        name=name,
        full_name=full_name,
        arguments=arguments,
        intent_text=" ".join(str(value) for value in intent_values if isinstance(value, str)).lower(),
    )


def tool_matches(tool: ToolCall, names: set[str]) -> bool:
    return tool.name in names or tool.full_name in names


def has_read_only_intent(tool: ToolCall) -> bool:
    return any(marker in tool.intent_text for marker in READ_ONLY_INTENT_MARKERS)


def classify_action(payload: dict[str, Any], cwd: Path) -> ActionClassification:
    operation_hint = explicit_operation(payload)
    tool = normalize_tool_call(payload)
    command = command_text(payload)
    targets = target_path_values(payload, cwd)

    if tool_matches(tool, WRITE_TOOLS) or target_paths_from_patch(payload):
        return ActionClassification(
            operation=operation_hint if operation_hint in WRITE_OPERATIONS else "write",
            side_effect_class="file_write",
            requires_preflight=True,
            reason="write_tool_or_patch_payload",
        )

    if tool_matches(tool, READ_ONLY_TOOLS):
        return ActionClassification(
            operation="read",
            side_effect_class="none",
            requires_preflight=False,
            reason="read_only_tool",
        )

    if tool_matches(tool, {"bash", "exec_command", "functions.exec_command", "shell"}):
        if is_likely_read_only_command(command):
            return ActionClassification(
                operation="read",
                side_effect_class="none",
                requires_preflight=False,
                reason="read_only_command",
            )
        return ActionClassification(
            operation=operation_hint if operation_hint else "write",
            side_effect_class="external_state_or_file_write",
            requires_preflight=True,
            reason="command_not_classified_read_only",
        )

    if tool_matches(tool, COLLABORATION_TOOL_NAMES) and has_read_only_intent(tool):
        return ActionClassification(
            operation=operation_hint if operation_hint in READ_OPERATIONS else "review",
            side_effect_class="process_output",
            requires_preflight=False,
            reason="collaboration_read_only_intent",
        )

    if operation_hint in READ_OPERATIONS and not targets:
        return ActionClassification(
            operation=operation_hint,
            side_effect_class="none",
            requires_preflight=False,
            reason="explicit_read_operation_without_targets",
        )

    if operation_hint in READ_OPERATIONS and tool_matches(tool, COLLABORATION_TOOL_NAMES):
        return ActionClassification(
            operation=operation_hint,
            side_effect_class="process_output",
            requires_preflight=False,
            reason="collaboration_read_process_output",
        )

    if operation_hint in WRITE_OPERATIONS:
        return ActionClassification(
            operation=operation_hint,
            side_effect_class="file_write_or_external_state",
            requires_preflight=True,
            reason="explicit_write_operation",
        )

    return ActionClassification(
        operation=operation_hint or "write",
        side_effect_class="unknown",
        requires_preflight=True,
        reason="default_preflight_for_unknown_action",
    )


def operation(payload: dict[str, Any], cwd: Path | None = None) -> str:
    if cwd is not None:
        return classify_action(payload, cwd).operation
    tool_name = first_text(payload.get("tool_name"), payload.get("toolName"), payload.get("name")).lower()
    if tool_name in READ_ONLY_TOOLS:
        return "read"
    if tool_name in {"bash", "exec_command", "functions.exec_command", "shell"} and is_likely_read_only_command(command_text(payload)):
        return "read"
    return first_text(payload.get("operation"), "write")


def adapter_payload(payload: dict[str, Any], event: str, cwd: Path) -> dict[str, Any]:
    return {
        "event": event,
        "session_id": first_text(payload.get("session_id"), payload.get("sessionId"), "codex-hook"),
        "cwd": cwd.as_posix(),
        "config_root": first_text(payload.get("config_root"), payload.get("configRoot"), os.environ.get("LDVH_CONFIG_ROOT")),
        "target_path": target_path(payload, cwd),
        "target_paths": target_path_values(payload, cwd),
        "operation": operation(payload, cwd),
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
  本 Spark 作为 Codex 环境插件六类 lifecycle hook 的研究采样入口。它记录 SessionStart、PreToolUse、PostToolUse、UserPromptSubmit、Stop 和 Notification 在真实会话中的触发样本，用于后续判断哪些事件适合承载治理提醒、读计划提示、工具前置阻断、工具后置审计、用户输入分流或通知研究。

  本 Spark 不定义 hook 规则、payload schema、阻断策略或安装完成声明；这些仍由 specs、Code 和环境插件边界承接。自动追加的 evolution 只作为研究线索，后续若要形成稳定规则，应分流到 WorkCase、ADR、Study、docs 或 specs。
source: codex_hook
source_detail: |
  Codex LDVH v3 环境插件 `hooks/ldvh_runtime_shim.py` 自动捕获 lifecycle event 元数据。默认只写事件名、session、cwd、工具名、目标路径和 payload key 摘要，不写完整用户提示或完整工具参数。
priority: P1
input_refs:
  - spark-0032
  - spark-0033
  - workcase-0012
  - specs/01-保障与衔接.md
  - specs/10-安装与配置规范.md
  - hooks/environment-plugins/codex-ldvh-v3/hooks/hooks.json
resolved_to: ''
resolved_at: ''
discard_reason: ''
related_sparks:
  - spark-0032
  - spark-0033
related_workcases:
  - workcase-0012
related_adrs: []
related_studies: []
related_docs:
  - specs/01-保障与衔接.md
  - specs/10-安装与配置规范.md
  - hooks/environment-plugins/codex-ldvh-v3/hooks/hooks.json
  - hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py
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
    tool = first_text(payload.get("tool_name"), payload.get("toolName"))
    session_id = first_text(payload.get("session_id"), payload.get("sessionId"), "codex-hook")
    target = target_path(payload, cwd)
    action = classify_action(payload, cwd) if event == "PreToolUse" else None
    keys = ", ".join(sorted(str(key) for key in payload.keys())[:20])
    lines = [
        f"event={event}",
        f"session_id={session_id}",
        f"cwd={cwd.as_posix()}",
    ]
    if tool:
        lines.append(f"tool_name={tool}")
    if target:
        lines.append(f"target_path={target}")
    if action:
        lines.append(f"operation={action.operation}")
        lines.append(f"side_effect_class={action.side_effect_class}")
        lines.append(f"requires_preflight={str(action.requires_preflight).lower()}")
        lines.append(f"classification_reason={action.reason}")
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


def diagnostic_codes(result: dict[str, Any]) -> set[str]:
    return {str(item.get("code") or "") for item in diagnostics(result) if isinstance(item, dict)}


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


def codex_protocol_output(event: str, result: dict[str, Any]) -> dict[str, Any]:
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
        if is_blocking_result(result):
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
            "LDVH_CODEX_SHIM_EVENT_UNKNOWN: Codex hook payload did not contain a supported SessionStart, PreToolUse, PostToolUse, UserPromptSubmit, Stop, or Notification event."
        )

    ldvh_root = find_ldvh_root(payload, cwd)
    if ldvh_root is None:
        return emit_warning(
            "LDVH_CODEX_SHIM_ROOT_NOT_FOUND: LDVH root was not found from LDVH_ROOT, payload, cwd, or shim path; hook shim allowed the event."
        )

    record_hook_event_to_spark(ldvh_root, payload, event, cwd)

    runtime_event = adapter_event(event)
    if not runtime_event:
        return 0

    action = classify_action(payload, cwd) if event == "PreToolUse" else None
    if action and not action.requires_preflight:
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
        return emit_warning("LDVH_CODEX_SHIM_ADAPTER_OUTPUT_INVALID: " + detail[:500])
    if summary_status(parsed) == "no_op":
        return 0
    return emit_json(codex_protocol_output(event, parsed))


if __name__ == "__main__":
    raise SystemExit(main())
