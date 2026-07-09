from __future__ import annotations

import json
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode


READ_ONLY_TOOLS = {
    "read",
    "grep",
    "glob",
    "ls",
    "read_thread",
    "read_thread_terminal",
    "list_projects",
    "codex_app.read_thread",
    "codex_app.read_thread_terminal",
    "codex_app.list_threads",
    "codex_app.list_projects",
    "codex_appread_thread",
    "codex_appread_thread_terminal",
    "codex_applist_threads",
    "codex_applist_projects",
    "functions.update_plan",
    "update_plan",
    "close_agent",
    "multi_agent.close_agent",
    "multi_agent_v1.close_agent",
    "multi_agent_v1close_agent",
    "wait_agent",
    "multi_agent.wait_agent",
    "multi_agent_v1.wait_agent",
    "multi_agent_v1wait_agent",
}
COMMAND_EXECUTION_TOOLS = {
    "bash",
    "exec_command",
    "functions.exec_command",
    "mcp__functions__exec_command",
    "mcp__developer__exec_command",
    "shell",
}
WRITE_TOOLS = {"write", "edit", "multiedit", "multi_edit", "apply_patch", "functions.apply_patch"}
READ_OPERATIONS = {"read", "inspect", "search", "grep", "list", "audit", "review", "diagnose"}
WRITE_OPERATIONS = {"write", "edit", "apply_patch", "commit", "delete", "move", "install", "update", "git_push"}
COLLABORATION_TOOL_NAMES = {
    "spawn_agent",
    "multi_agent.spawn_agent",
    "multi_agent_v1.spawn_agent",
    "send_input",
    "multi_agent.send_input",
    "multi_agent_v1.send_input",
    "multi_agent_v1send_input",
    "codex_app.create_thread",
    "codex_app.send_message_to_thread",
    "codex_appcreate_thread",
    "codex_appsend_message_to_thread",
}
READ_ONLY_INTENT_MARKERS = (
    "read-only",
    "readonly",
    "只读",
    "不要修改",
    "不要写",
    "不要提交",
    "do not modify",
    "do not edit",
    "do not commit",
)
READ_ONLY_COMMANDS = {"cat", "find", "grep", "head", "ls", "nl", "pwd", "rg", "sed", "sleep", "sort", "tail", "wc"}
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
GIT_GLOBAL_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--namespace", "--work-tree"}
GIT_PUSH_OPTIONS_WITH_VALUE = {
    "--exec",
    "--push-option",
    "--receive-pack",
    "--repo",
    "-o",
}
GIT_PUSH_FLAGS = {
    "--all": "all",
    "--delete": "delete",
    "-d": "delete",
    "--force": "force",
    "-f": "force",
    "--force-if-includes": "force_if_includes",
    "--force-with-lease": "force_with_lease",
    "--follow-tags": "follow_tags",
    "--mirror": "mirror",
    "--prune": "prune",
    "--set-upstream": "set_upstream",
    "-u": "set_upstream",
    "--tags": "tags",
}
READ_ONLY_SHELL_PIPE_COMMANDS = READ_ONLY_COMMANDS | {"xargs"}
READ_ONLY_PYTHON_SCRIPT_EVENTS = {
    "code/environment_entry_audit.py": None,
    "code/install_verification.py": None,
    "code/session_start.py": None,
    "code/runtime_adapter.py": {"session-start", "session_start", "--help", "-h"},
}
CONTROLLED_BOOTSTRAP_PYTHON_SCRIPTS = {"code/acknowledge_read_plan.py"}
TOOL_INPUT_KEYS = ("tool_input", "toolInput", "input", "arguments", "parameters")
TOOL_OBJECT_KEYS = ("tool", "tool_call", "toolCall", "function_call", "functionCall")
FIND_WRITE_PRIMARIES = {"-delete", "-exec", "-execdir", "-fprint", "-fprint0", "-fprintf", "-fls", "-ok", "-okdir"}
XARGS_OPTIONS_WITH_VALUE = {
    "-a",
    "--arg-file",
    "-d",
    "--delimiter",
    "-E",
    "-e",
    "-I",
    "-i",
    "-L",
    "-l",
    "-n",
    "--max-args",
    "-P",
    "--max-procs",
    "-s",
    "--max-chars",
}
SED_SCRIPT_FILE_OPTIONS = {"-f", "--file"}
SED_EXPRESSION_OPTIONS = {"-e", "--expression"}


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
    aliases: tuple[str, ...]


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


def object_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip().startswith("{"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def nested_tool_objects(payload: dict[str, Any]) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for key in TOOL_OBJECT_KEYS:
        tool = object_mapping(payload.get(key))
        if not tool:
            continue
        objects.append(tool)
        function = object_mapping(tool.get("function"))
        if function:
            objects.append(function)
    return objects


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    for key in TOOL_INPUT_KEYS:
        value = object_mapping(payload.get(key))
        if value:
            return value
    for tool in nested_tool_objects(payload):
        for key in TOOL_INPUT_KEYS:
            value = object_mapping(tool.get(key))
            if value:
                return value
        if any(
            key in tool
            for key in (
                "cmd",
                "command",
                "file_path",
                "filePath",
                "path",
                "target_path",
                "targetPath",
                "patch",
            )
        ):
            return tool
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
    return _split_unquoted_token(command, "|")


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


def _split_unquoted_token(command: str, token: str) -> list[str]:
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
        if char == token:
            segments.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    segments.append("".join(current).strip())
    return segments


def has_unquoted_background_operator(command: str) -> bool:
    quote = ""
    escaped = False
    index = 0
    while index < len(command):
        char = command[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if char == "\\":
            escaped = True
            index += 1
            continue
        if quote:
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "&":
            if index + 1 < len(command) and command[index + 1] == "&":
                index += 2
                continue
            return True
        index += 1
    return False


def is_likely_read_only_command(command: str) -> bool:
    stripped = command.strip()
    if not stripped or re.search(r"[;><`$()\n\r]", stripped):
        return False
    if has_unquoted_background_operator(stripped):
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
    if executable == "find" and any(part in FIND_WRITE_PRIMARIES for part in parts[1:]):
        return False
    if executable == "sed":
        return is_likely_read_only_sed(parts)
    if executable == "git":
        return git_subcommand(parts) in READ_ONLY_GIT_SUBCOMMANDS
    if executable == "xargs":
        return is_likely_read_only_xargs(parts)
    if executable in {"python", "python3"} and len(parts) > 1:
        return is_allowed_read_only_python(parts)
    return executable in READ_ONLY_SHELL_PIPE_COMMANDS


def git_subcommand(parts: list[str]) -> str:
    result = git_subcommand_with_index(parts)
    return result[0]


def git_subcommand_with_index(parts: list[str]) -> tuple[str, int]:
    index = 1
    while index < len(parts):
        part = parts[index]
        lowered = part.lower()
        if lowered in GIT_GLOBAL_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if lowered.startswith("-c") and lowered != "-c":
            index += 1
            continue
        if lowered.startswith("--git-dir=") or lowered.startswith("--work-tree="):
            index += 1
            continue
        if lowered.startswith("--namespace="):
            index += 1
            continue
        if lowered.startswith("-"):
            index += 1
            continue
        return lowered, index
    return "", -1


def is_git_push_command(command: str) -> bool:
    parts = command_parts(command.strip())
    return bool(parts) and Path(parts[0]).name.lower() == "git" and git_subcommand(parts) == "push"


def normalize_git_push_flag(part: str) -> str:
    if part.startswith("--force-with-lease="):
        return "force_with_lease"
    if part.startswith("--push-option="):
        return "push_option"
    if part.startswith("--repo="):
        return "repo"
    return GIT_PUSH_FLAGS.get(part, "")


def _resolve_command_path(path: str, base: Path | None) -> str:
    if not path:
        return ""
    candidate = Path(path).expanduser()
    if not candidate.is_absolute() and base is not None:
        candidate = base / candidate
    try:
        return candidate.resolve().as_posix()
    except OSError:
        return candidate.absolute().as_posix()


def git_command_repo_hints(parts: list[str], cwd: Path | None = None) -> tuple[str, str, list[str]]:
    base = cwd.expanduser() if cwd is not None else None
    git_dir = ""
    flags: list[str] = []
    index = 1
    while index < len(parts):
        part = parts[index]
        lowered = part.lower()
        if part == "-C":
            value = parts[index + 1] if index + 1 < len(parts) else ""
            if value:
                base = Path(_resolve_command_path(value, base))
            index += 2
            continue
        if lowered == "-c":
            index += 2
            continue
        if lowered in {"--work-tree"}:
            value = parts[index + 1] if index + 1 < len(parts) else ""
            if value:
                base = Path(_resolve_command_path(value, base))
            index += 2
            continue
        if lowered.startswith("--work-tree="):
            base = Path(_resolve_command_path(parts[index].split("=", 1)[1], base))
            index += 1
            continue
        if lowered == "--git-dir":
            value = parts[index + 1] if index + 1 < len(parts) else ""
            if value:
                git_dir = _resolve_command_path(value, base)
                flags.append("git_dir")
            index += 2
            continue
        if lowered.startswith("--git-dir="):
            git_dir = _resolve_command_path(parts[index].split("=", 1)[1], base)
            flags.append("git_dir")
            index += 1
            continue
        if lowered.startswith("-"):
            index += 1
            continue
        break
    return _resolve_command_path(base.as_posix(), None) if base is not None else "", git_dir, flags


def git_command_repo_hint(parts: list[str], cwd: Path | None = None) -> str:
    repo, _, _ = git_command_repo_hints(parts, cwd)
    return repo


def _git_output(repo_hint: str, args: list[str]) -> str:
    if not repo_hint:
        return ""
    try:
        completed = subprocess.run(
            ["git", "-C", repo_hint, *args],
            text=True,
            capture_output=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def git_common_dir_hint(repo_hint: str) -> str:
    return _git_output(repo_hint, ["rev-parse", "--path-format=absolute", "--git-common-dir"])


def git_remote_url_hint(repo_hint: str, remote: str) -> str:
    if re.match(r"^[a-z][a-z0-9+.-]*://", remote, flags=re.IGNORECASE) or remote.startswith(("git@", "ssh://")):
        return remote
    return _git_output(repo_hint, ["remote", "get-url", remote])


def git_push_remote_ref_target(command: str, cwd: Path | None = None) -> str:
    parts = command_parts(command.strip())
    if not parts or Path(parts[0]).name.lower() != "git":
        return ""
    subcommand, subcommand_index = git_subcommand_with_index(parts)
    if subcommand != "push" or subcommand_index < 0:
        return ""

    flags: list[str] = []
    positional: list[str] = []
    repo_option = ""
    index = subcommand_index + 1
    while index < len(parts):
        part = parts[index]
        if part == "--":
            positional.extend(parts[index + 1 :])
            break
        if part in GIT_PUSH_OPTIONS_WITH_VALUE:
            value = parts[index + 1] if index + 1 < len(parts) else ""
            flag = normalize_git_push_flag(part)
            if flag:
                flags.append(flag)
            if part == "--repo":
                repo_option = value.strip()
            index += 2
            continue
        if any(part.startswith(option + "=") for option in GIT_PUSH_OPTIONS_WITH_VALUE if option.startswith("--")):
            flag = normalize_git_push_flag(part)
            if flag:
                flags.append(flag)
            if part.startswith("--repo="):
                repo_option = part.split("=", 1)[1].strip()
            index += 1
            continue
        flag = normalize_git_push_flag(part)
        if flag:
            flags.append(flag)
            index += 1
            continue
        if part.startswith("-"):
            index += 1
            continue
        positional.append(part)
        index += 1

    if repo_option:
        positional = [repo_option, *positional]
    remote = positional[0].strip() if positional else ""
    refspec = positional[1].strip() if len(positional) > 1 else ""
    if len(positional) > 2 and refspec != "tag":
        flags.append("multi_refspec")
    if refspec == "tag" and len(positional) > 2:
        flags.append("tags")
        refspec = f"refs/tags/{positional[2].strip()}"
    if not refspec:
        if "mirror" in flags:
            refspec = "*"
        elif "tags" in flags:
            refspec = "refs/tags/*"
        elif "all" in flags:
            refspec = "refs/heads/*"
    if not remote:
        flags.append("missing_remote")
        remote = "unknown"
    if not refspec:
        flags.append("missing_ref")
        refspec = "unknown"

    if refspec.startswith("+"):
        flags.append("force")
        refspec = refspec[1:]
    if ":" in refspec:
        local_ref, remote_ref = refspec.split(":", 1)
        if not local_ref:
            flags.append("delete")
        refspec = remote_ref or refspec
    if refspec.startswith("+"):
        flags.append("force")
        refspec = refspec[1:]
    if not refspec:
        flags.append("missing_ref")
        refspec = "unknown"

    repo_hint, git_dir_hint, global_flags = git_command_repo_hints(parts, cwd)
    flags.extend(global_flags)
    common_dir = git_dir_hint or git_common_dir_hint(repo_hint)
    remote_url = "" if git_dir_hint else git_remote_url_hint(repo_hint, remote)
    unique_flags = sorted(set(flag for flag in flags if flag))
    query = {
        "flags": ",".join(unique_flags),
        "repo": repo_hint,
        "git_dir": git_dir_hint,
        "common_dir": common_dir,
        "remote_url": remote_url,
    }
    suffix = "?" + urlencode({key: value for key, value in query.items() if value}) if any(query.values()) else ""
    return f"git-remote-ref:{quote(remote, safe='')}/{quote(refspec, safe='')}{suffix}"


def codex_plugin_environment_target(command: str) -> str:
    parts = command_parts(command.strip())
    if len(parts) < 4:
        return ""
    executable = Path(parts[0]).name.lower()
    if executable != "codex" or parts[1:3] != ["plugin", "add"]:
        return ""
    plugin_name = parts[3].strip().lower().split("@", 1)[0]
    if plugin_name != "ldvh":
        return ""
    return "hooks/environment-plugins/codex-ldvh-v3"


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


def is_likely_read_only_sed(parts: list[str]) -> bool:
    scripts: list[str] = []
    index = 1
    while index < len(parts):
        part = parts[index]
        if part == "--":
            index += 1
            break
        if part == "-i" or part.startswith("-i") or part == "--in-place" or part.startswith("--in-place="):
            return False
        if part in SED_SCRIPT_FILE_OPTIONS or any(
            part.startswith(option + "=") for option in SED_SCRIPT_FILE_OPTIONS if option.startswith("--")
        ):
            return False
        if part in SED_EXPRESSION_OPTIONS:
            if index + 1 >= len(parts):
                return False
            scripts.append(parts[index + 1])
            index += 2
            continue
        if part.startswith("-e") and part != "-e":
            scripts.append(part[2:])
            index += 1
            continue
        if part.startswith("--expression="):
            scripts.append(part.split("=", 1)[1])
            index += 1
            continue
        if part.startswith("-"):
            index += 1
            continue
        scripts.append(part)
        break
    return not any(sed_script_has_side_effect(script) for script in scripts)


def sed_script_has_side_effect(script: str) -> bool:
    return bool(
        re.search(r"(^|[;{}\n])\s*(?:\d+(?:,\d+)?\s*)?(?:/[^/\n]*/\s*)?[we]\s+\S", script)
        or re.search(r"(^|[;{}\n])\s*(?:\d+(?:,\d+)?\s*)?s[^;{}\n]*\bw\s+\S", script)
        or re.search(
            r"(^|[;{}\n])\s*(?:\d+(?:,\d+)?\s*)?(?:/[^/\n]*/\s*)?"
            r"s(?P<delimiter>[^A-Za-z0-9\s\\])[^;{}\n]*(?P=delimiter)[^;{}\n]*(?P=delimiter)[A-Za-z]*e",
            script,
        )
    )


def is_likely_read_only_xargs(parts: list[str]) -> bool:
    index = 1
    while index < len(parts):
        part = parts[index]
        if part == "--":
            index += 1
            break
        if part in XARGS_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if any(part.startswith(option + "=") for option in XARGS_OPTIONS_WITH_VALUE if option.startswith("--")):
            index += 1
            continue
        if part.startswith("-"):
            index += 1
            continue
        break
    if index >= len(parts):
        return True
    command = " ".join(shlex.quote(part) for part in parts[index:])
    return is_likely_read_only_command_segment(command)


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


def target_path_from_command(payload: dict[str, Any], cwd: Path | None = None) -> str:
    command = command_text(payload)
    if not command:
        return ""
    git_remote_ref_target = git_push_remote_ref_target(command, cwd)
    if git_remote_ref_target:
        return git_remote_ref_target
    codex_plugin_target = codex_plugin_environment_target(command)
    if codex_plugin_target:
        return codex_plugin_target
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


def target_path_values(payload: dict[str, Any], cwd: Path | None = None) -> list[str]:
    _ = cwd
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
        for candidate in list_text(target_paths):
            if isinstance(candidate, str) and candidate.strip():
                values.append(candidate.strip())
    values.extend(target_paths_from_patch(payload))
    command_target = target_path_from_command(payload, cwd)
    if command_target:
        values.append(command_target)
    return list(dict.fromkeys(values))


def explicit_operation(payload: dict[str, Any]) -> str:
    tool = tool_input(payload)
    raw = first_text(payload.get("operation"), payload.get("op"), tool.get("operation"), tool.get("op"))
    return raw.replace("-", "_").lower()


def normalize_tool_call(payload: dict[str, Any]) -> ToolCall:
    arguments = tool_input(payload)
    tool_objects = nested_tool_objects(payload)
    raw_namespace = first_text(
        payload.get("namespace"),
        payload.get("tool_namespace"),
        payload.get("toolNamespace"),
        *(tool.get("namespace") for tool in tool_objects),
        *(tool.get("tool_namespace") for tool in tool_objects),
        *(tool.get("toolNamespace") for tool in tool_objects),
    )
    raw_name = first_text(
        payload.get("tool_name"),
        payload.get("toolName"),
        payload.get("name"),
        *(tool.get("tool_name") for tool in tool_objects),
        *(tool.get("toolName") for tool in tool_objects),
        *(tool.get("name") for tool in tool_objects),
    ).lower()
    if not raw_name:
        raw_name = first_text(
            payload.get("tool"),
            payload.get("toolName"),
            payload.get("name"),
            *(tool.get("tool") for tool in tool_objects),
        ).lower()
    if "." in raw_name and not raw_namespace:
        namespace, name = raw_name.rsplit(".", 1)
    else:
        namespace, name = raw_namespace.lower(), raw_name
    full_name = f"{namespace}.{name}" if namespace and name else name or raw_name
    aliases = [alias for alias in (name, full_name, raw_name) if alias]
    aliases.extend(alias.replace("__", ".") for alias in aliases if "__" in alias)
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
        aliases=tuple(dict.fromkeys(aliases)),
    )


def tool_matches(tool: ToolCall, names: set[str]) -> bool:
    return any(alias in names for alias in tool.aliases)


def is_command_execution_tool(payload: dict[str, Any]) -> bool:
    return tool_matches(normalize_tool_call(payload), COMMAND_EXECUTION_TOOLS)


def has_read_only_intent(tool: ToolCall) -> bool:
    return any(marker in tool.intent_text for marker in READ_ONLY_INTENT_MARKERS)


def classify_action(payload: dict[str, Any], cwd: Path | None = None) -> ActionClassification:
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

    if tool_matches(tool, COMMAND_EXECUTION_TOOLS):
        if is_likely_read_only_command(command):
            return ActionClassification(
                operation="read",
                side_effect_class="none",
                requires_preflight=False,
                reason="read_only_command",
            )
        if is_git_push_command(command):
            return ActionClassification(
                operation="git_push",
                side_effect_class="git_remote_ref_write",
                requires_preflight=True,
                reason="git_push_remote_ref_write",
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
    return classify_action(payload, cwd).operation
