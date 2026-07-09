from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
from typing import Any, Optional

from environment_status import build_environment_status
from ldvh_specs import ROOT


AUTHORIZATION = "none"
PLACEHOLDER_FILES = {".gitkeep", ".DS_Store"}
LEGACY_LDVH_PLUGIN_COMMAND_RE = re.compile(
    r"/ld-vibe-harness(?:-[^/\s]+)?/code/(hook_adapter|hook_dispatch)\.py"
)
STALE_REPO_ENVIRONMENT_PLUGIN_COMMAND_RE = re.compile(
    r"/ld-vibe-harness(?:-[^/\s]+)?/code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim\.py"
)
CODEX_REQUIRED_HOOK_EVENTS = ("SessionStart", "PreToolUse", "Stop")
CODEX_ENVIRONMENT_NAME = "Codex"
WORKBUDDY_ENVIRONMENT_NAME = "WorkBuddy"
UNKNOWN_ENVIRONMENT_NAME = "未知环境"
PLUGIN_ROOT_TOKENS = (
    "$PLUGIN_ROOT",
    "${PLUGIN_ROOT}",
    "%PLUGIN_ROOT%",
    "$CODEBUDDY_PLUGIN_ROOT",
    "${CODEBUDDY_PLUGIN_ROOT}",
    "%CODEBUDDY_PLUGIN_ROOT%",
)
TARGET_PROJECTION_DELEGATION_SNIPPETS = (
    "return action_classifier_module().target_path_from_command(payload)",
    "return action_classifier_module().target_paths_from_patch(payload)",
    "return action_classifier_module().target_path_values(payload, cwd)",
)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _environment_name(value: str) -> str:
    stripped = value.strip()
    return stripped or UNKNOWN_ENVIRONMENT_NAME


def _is_codex_environment(value: str) -> bool:
    return _environment_name(value).lower() == CODEX_ENVIRONMENT_NAME.lower()


def _is_workbuddy_environment(value: str) -> bool:
    return _environment_name(value).lower() == WORKBUDDY_ENVIRONMENT_NAME.lower()


def _environment_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _environment_name(value).lower()).strip("-")
    return slug or "target-environment"


def _diagnostic(level: str, code: str, path: str, message: str, disposition: str = "follow_up") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "path": path,
        "message": message,
        "disposition": disposition,
    }


def _repo_files(repo: Path, rel_paths: list[str]) -> list[Path]:
    return [repo / rel_path for rel_path in rel_paths if (repo / rel_path).is_file()]


def _repo_dirs(repo: Path, rel_paths: list[str]) -> list[Path]:
    return [repo / rel_path for rel_path in rel_paths if (repo / rel_path).is_dir()]


def _non_placeholder_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(item for item in path.rglob("*") if item.is_file() and item.name not in PLACEHOLDER_FILES)


def _as_posix(paths: list[Path]) -> list[str]:
    return [path.as_posix() for path in paths]


def _candidate(
    *,
    entry_id: str,
    category: str,
    status: str,
    trigger: str,
    evidence: list[str],
    decision: str,
    reason: str,
    integrated: bool = False,
    automatic: bool = False,
    hook_entry: str = "",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": entry_id,
        "category": category,
        "status": status,
        "integrated": integrated,
        "automatic": automatic,
        "trigger": trigger,
        "evidence": evidence,
        "hook_entry": hook_entry,
        "decision": decision,
        "reason": reason,
        "details": details or {},
    }


def _removed_top_level_candidate(
    repo: Path,
    diagnostics: list[dict[str, str]],
    *,
    entry_id: str,
    category: str,
    legacy_dir: str,
    source_name: str,
    reason: str,
) -> dict[str, Any]:
    legacy_path = repo / legacy_dir
    files = _non_placeholder_files(legacy_path)
    evidence = [legacy_path.as_posix()] if legacy_path.exists() else []
    evidence.extend(_as_posix(files))
    if files:
        diagnostics.append(
            _diagnostic(
                "warning",
                "ENV_REMOVED_TOP_LEVEL_FILES_PRESENT",
                legacy_path.as_posix(),
                f"检测到 {legacy_dir}/ 内容，但 {source_name} 已取消为 V3 顶层机制；这些文件不能证明环境入口已接入。",
            )
        )
    return _candidate(
        entry_id=entry_id,
        category=category,
        status="removed_top_level",
        trigger="none",
        evidence=evidence,
        decision="removed_top_level",
        reason=reason,
    )


def _toml_section(raw: str, section_header: str) -> str:
    lines: list[str] = []
    in_section = False
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_section:
                break
            in_section = stripped == section_header
            continue
        if in_section:
            lines.append(line)
    return "\n".join(lines)


def _ldvh_plugin_enabled(config_path: Path) -> bool:
    if not config_path.is_file():
        return False
    section = _toml_section(config_path.read_text(encoding="utf-8"), '[plugins."ldvh@personal"]')
    if not section:
        return False
    return not re.search(r"(?m)^\s*enabled\s*=\s*false\s*$", section)


def _ldvh_plugin_hook_files(codex_home: Path) -> list[Path]:
    cache_root = codex_home / "plugins" / "cache" / "personal" / "ldvh"
    if not cache_root.is_dir():
        return []
    return sorted(cache_root.glob("*/hooks/hooks.json"))


def _workbuddy_ldvh_plugin_hook_files(workbuddy_home: Path) -> list[Path]:
    plugin_root = workbuddy_home / "plugins" / "marketplaces" / "ldvh-local" / "plugins" / "ldvh"
    marketplace_matches = sorted(
        (workbuddy_home / "plugins" / "marketplaces").glob("*/plugins/ldvh/hooks/hooks.json")
    )
    direct = plugin_root / "hooks" / "hooks.json"
    candidates = [direct, *marketplace_matches]
    seen: set[str] = set()
    result: list[Path] = []
    for path in candidates:
        normalized = path.resolve().as_posix()
        if path.is_file() and normalized not in seen:
            seen.add(normalized)
            result.append(path)
    return result


def _hook_file_plugin_root(hook_file: Path) -> Path:
    return hook_file.parent.parent


def _hook_entries(hook_files: list[Path]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for hook_file in hook_files:
        plugin_root = _hook_file_plugin_root(hook_file)
        try:
            data = json.loads(hook_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        hooks = data.get("hooks", {})
        if not isinstance(hooks, dict):
            continue
        for event, groups in hooks.items():
            if not isinstance(groups, list):
                continue
            for group in groups:
                if not isinstance(group, dict):
                    continue
                matcher = group.get("matcher", "")
                for item in group.get("hooks", []):
                    if isinstance(item, dict) and isinstance(item.get("command"), str):
                        entries.append(
                            {
                                "file": hook_file.as_posix(),
                                "plugin_root": plugin_root.as_posix(),
                                "event": str(event),
                                "matcher": str(matcher) if matcher is not None else "",
                                "type": str(item.get("type", "")),
                                "command": item["command"],
                            }
                        )
    return entries


def _hook_commands(hook_files: list[Path]) -> list[str]:
    commands: list[str] = []
    for entry in _hook_entries(hook_files):
        commands.append(entry["command"])
    return commands


def _expand_plugin_root_tokens(command: str, plugin_root: str = "") -> str:
    if not plugin_root:
        return command
    expanded = command
    for token in PLUGIN_ROOT_TOKENS:
        expanded = expanded.replace(token, plugin_root)
    return expanded


def _command_targets_any_path(command: str, paths: set[str], *, plugin_root: str = "") -> bool:
    command = _expand_plugin_root_tokens(command, plugin_root)
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    if not parts:
        return False
    executable = Path(parts[0]).name.lower()
    return parts[0] in paths or (
        executable.startswith("python") and any(part in paths for part in parts[1:])
    )


def _entry_targets_any_path(entry: dict[str, str], paths: set[str]) -> bool:
    return _command_targets_any_path(entry["command"], paths, plugin_root=entry.get("plugin_root", ""))


def _installed_shim_paths(hook_files: list[Path]) -> list[Path]:
    roots = sorted({_hook_file_plugin_root(hook_file) for hook_file in hook_files})
    return [root / "hooks" / "ldvh_runtime_shim.py" for root in roots]


def _plugin_manifest_paths(plugin_root: Path) -> list[Path]:
    return [
        plugin_root / ".codex-plugin" / "plugin.json",
        plugin_root / "plugin.json",
        plugin_root / ".codebuddy-plugin" / "plugin.json",
    ]


def _plugin_manifest_status(plugin_root: Path) -> dict[str, Any]:
    manifests = [path for path in _plugin_manifest_paths(plugin_root) if path.is_file()]
    result: dict[str, Any] = {
        "plugin_root": plugin_root.as_posix(),
        "manifest_paths": _as_posix(manifests),
        "non_hook_capability_keys": [],
    }
    for manifest in manifests:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for key in ("skills", "rules", "mcpServers", "apps"):
            if key in data:
                result["non_hook_capability_keys"].append(key)
        interface = data.get("interface")
        if isinstance(interface, dict):
            capabilities = interface.get("capabilities")
            if isinstance(capabilities, list):
                result["interface_capabilities"] = [str(item) for item in capabilities]
    return result


def _shim_static_status(shim_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": shim_path.as_posix(),
        "exists": shim_path.is_file(),
        "thin_target_projection": False,
        "uses_runtime_adapter": False,
        "uses_shared_classifier": False,
        "spark_capture_requires_explicit_dir": False,
        "contains_spark_capture": False,
    }
    if not shim_path.is_file():
        return result
    try:
        raw = shim_path.read_text(encoding="utf-8")
    except OSError:
        return result
    result["thin_target_projection"] = all(snippet in raw for snippet in TARGET_PROJECTION_DELEGATION_SNIPPETS)
    result["uses_runtime_adapter"] = "runtime_adapter.py" in raw
    result["uses_shared_classifier"] = "action_classifier_module()" in raw or "action_classifier.py" in raw
    result["contains_spark_capture"] = "LDVH_HOOK_SPARK_CAPTURE" in raw
    result["spark_capture_requires_explicit_dir"] = (
        "LDVH_HOOK_SPARK_DIR" in raw and 'return ldvh_root / "ldvh-base" / "sparks"' not in raw
    )
    result["thin_reference_ok"] = bool(
        result["thin_target_projection"] and result["uses_runtime_adapter"] and result["uses_shared_classifier"]
    )
    return result


def _installed_package_status(hook_files: list[Path]) -> dict[str, Any]:
    plugin_roots = sorted({_hook_file_plugin_root(hook_file) for hook_file in hook_files})
    shim_status = [_shim_static_status(root / "hooks" / "ldvh_runtime_shim.py") for root in plugin_roots]
    manifest_status = [_plugin_manifest_status(root) for root in plugin_roots]
    thin_reference_ok = bool(shim_status) and all(item.get("thin_reference_ok") for item in shim_status)
    return {
        "plugin_roots": _as_posix(plugin_roots),
        "shim_paths": [item["path"] for item in shim_status],
        "shim_static": shim_status,
        "manifest_static": manifest_status,
        "thin_reference_ok": thin_reference_ok,
    }


def _required_hook_event_status(entries: list[dict[str, str]], v3_paths: set[str]) -> dict[str, Any]:
    by_event: dict[str, list[dict[str, str]]] = {event: [] for event in CODEX_REQUIRED_HOOK_EVENTS}
    for entry in entries:
        if entry["event"] in by_event:
            by_event[entry["event"]].append(entry)
    satisfied = {
        event: any(
            entry["type"] == "command" and _entry_targets_any_path(entry, v3_paths)
            for entry in event_entries
        )
        for event, event_entries in by_event.items()
    }
    return {
        "required_events": list(CODEX_REQUIRED_HOOK_EVENTS),
        "satisfied_events": [event for event, ok in satisfied.items() if ok],
        "missing_required_events": [event for event, ok in satisfied.items() if not ok],
        "required_events_ok": all(satisfied.values()),
    }


def _codex_ldvh_plugin_candidate(
    ldvh_root: Path,
    codex_home: Path,
    diagnostics: list[dict[str, str]],
) -> dict[str, Any]:
    config_path = codex_home / "config.toml"
    hook_files = _ldvh_plugin_hook_files(codex_home)
    evidence = [config_path.as_posix()] if config_path.is_file() else []
    evidence.extend(_as_posix(hook_files))
    enabled = _ldvh_plugin_enabled(config_path)
    hook_entries = _hook_entries(hook_files)
    commands = [entry["command"] for entry in hook_entries]
    command_blob = "\n".join(commands)
    installed_package = _installed_package_status(hook_files)
    v3_adapter = (ldvh_root / "code" / "runtime_adapter.py").as_posix()
    v3_codex_shim = (ldvh_root / "hooks" / "environment-plugins" / "codex-ldvh-v3" / "hooks" / "ldvh_runtime_shim.py").as_posix()
    v3_paths = {v3_adapter, v3_codex_shim, *installed_package["shim_paths"]}
    required_hook_status = _required_hook_event_status(hook_entries, v3_paths)
    points_to_v3 = any(
        entry["type"] == "command" and _entry_targets_any_path(entry, v3_paths)
        for entry in hook_entries
    )
    installed_shim_exists = any(item.get("exists") for item in installed_package["shim_static"])
    legacy_commands = [command for command in commands if LEGACY_LDVH_PLUGIN_COMMAND_RE.search(command)]
    stale_asset_commands = [
        command for command in commands if STALE_REPO_ENVIRONMENT_PLUGIN_COMMAND_RE.search(command)
    ]
    stale_commands = [*legacy_commands, *stale_asset_commands]
    points_to_legacy = bool(stale_commands)

    if not evidence:
        return _candidate(
            entry_id="codex.ldvh-plugin",
            category="environment_hook",
            status="absent",
            trigger="Codex lifecycle hooks via LDVH plugin",
            evidence=[],
            hook_entry="code/runtime_adapter.py",
            decision="install_plugin_before_claiming",
            reason="未发现 Codex 用户配置或 LDVH Codex plugin hook manifest；Codex 只是当前可审计的环境插件样例。",
        )
    if not enabled:
        return _candidate(
            entry_id="codex.ldvh-plugin",
            category="environment_hook",
            status="available",
            trigger="Codex lifecycle hooks via LDVH plugin",
            evidence=evidence,
            hook_entry="code/runtime_adapter.py",
            decision="enable_or_install_v3_plugin",
            reason="检测到 Codex LDVH 插件相关文件，但插件未在 Codex config 中启用。",
            details={"commands": commands, "hook_entries": hook_entries, "installed_package": installed_package, **required_hook_status},
        )
    if points_to_legacy:
        diagnostics.append(
            _diagnostic(
                "warning",
                "ENV_CODEX_LDVH_PLUGIN_STALE",
                hook_files[0].as_posix() if hook_files else config_path.as_posix(),
                "检测到已启用的 LDVH Codex 插件，但 Hook 命令指向旧 ld-vibe-harness 路径或已废弃的 code/environment_plugins 资产路径，不能声明为 V3 环境入口；环境 Hook 正式安装必须通过对应 LDVH 插件或扩展包完成。",
            )
        )
        return _candidate(
            entry_id="codex.ldvh-plugin",
            category="environment_hook",
            status="available",
            trigger="Codex lifecycle hooks via LDVH plugin",
            evidence=evidence,
            hook_entry="code/runtime_adapter.py",
            decision="reinstall_for_v3",
            reason="LDVH 插件已启用但指向旧 V2/旧仓库路径或已废弃的 repo-local 插件资产路径；需要 V3 插件包重新安装或升级后才可继续验收。",
            details={
                "commands": commands,
                "hook_entries": hook_entries,
                "stale_commands": stale_commands,
                "legacy_commands": legacy_commands,
                "stale_asset_commands": stale_asset_commands,
                "installed_package": installed_package,
                **required_hook_status,
            },
        )
    if installed_shim_exists and not installed_package["thin_reference_ok"]:
        diagnostics.append(
            _diagnostic(
                "warning",
                "ENV_CODEX_LDVH_PLUGIN_STALE_CACHE",
                installed_package["shim_paths"][0] if installed_package["shim_paths"] else hook_files[0].as_posix(),
                "检测到已启用的 LDVH Codex 插件 cache，但 installed shim 未满足薄引用边界；需要通过插件升级 / 重装同步到共享 classifier / runtime adapter。",
            )
        )
        return _candidate(
            entry_id="codex.ldvh-plugin",
            category="environment_hook",
            status="available",
            trigger="Codex lifecycle hooks via LDVH plugin",
            evidence=evidence,
            hook_entry="code/runtime_adapter.py",
            decision="reinstall_for_v3",
            reason="Codex 插件已启用但真实安装包 / cache 中的 shim 未满足薄引用边界；不能把 repo-local 样例通过写成真实环境入口已对齐。",
            details={"commands": commands, "hook_entries": hook_entries, "installed_package": installed_package, **required_hook_status},
        )
    if points_to_v3 and required_hook_status["required_events_ok"]:
        return _candidate(
            entry_id="codex.ldvh-plugin",
            category="environment_hook",
            status="available",
            trigger="Codex lifecycle hooks via LDVH plugin",
            evidence=evidence,
            hook_entry="code/runtime_adapter.py",
            decision="verify_trust_and_runtime_before_integration",
            reason="检测到指向当前 V3 的 LDVH 插件 Hook 配置，且 SessionStart、PreToolUse、Stop 三类必需事件齐全；仍需真实触发、payload 和失败处理当次依据后才能声明 integrated。",
            details={"commands": commands, "hook_entries": hook_entries, "installed_package": installed_package, **required_hook_status},
        )
    if points_to_v3:
        return _candidate(
            entry_id="codex.ldvh-plugin",
            category="environment_hook",
            status="available",
            trigger="Codex lifecycle hooks via LDVH plugin",
            evidence=evidence,
            hook_entry="code/runtime_adapter.py",
            decision="complete_v3_hook_manifest_before_install_verified",
            reason="检测到部分 Codex LDVH Hook 指向当前 V3，但 SessionStart、PreToolUse、Stop 必需事件尚未齐全，不能把安装检测写成通过。",
            details={"commands": commands, "hook_entries": hook_entries, "installed_package": installed_package, **required_hook_status},
        )
    return _candidate(
        entry_id="codex.ldvh-plugin",
        category="environment_hook",
        status="available",
        trigger="Codex lifecycle hooks via LDVH plugin",
        evidence=evidence,
        hook_entry="code/runtime_adapter.py",
        decision="audit_plugin_hook_target",
        reason="检测到 LDVH 插件配置或缓存，但 Hook 指向无法归属到当前 V3；不得声明环境入口已接入。",
        details={"commands": commands, "hook_entries": hook_entries, "installed_package": installed_package, **required_hook_status},
    )


def _workbuddy_ldvh_plugin_candidate(
    ldvh_root: Path,
    workbuddy_home: Path,
    diagnostics: list[dict[str, str]],
) -> dict[str, Any]:
    hook_files = _workbuddy_ldvh_plugin_hook_files(workbuddy_home)
    evidence = _as_posix(hook_files)
    hook_entries = _hook_entries(hook_files)
    commands = [entry["command"] for entry in hook_entries]
    installed_package = _installed_package_status(hook_files)
    v3_adapter = (ldvh_root / "code" / "runtime_adapter.py").as_posix()
    v3_workbuddy_shim = (
        ldvh_root / "hooks" / "environment-plugins" / "workbuddy-ldvh-v3" / "hooks" / "ldvh_runtime_shim.py"
    ).as_posix()
    v3_paths = {v3_adapter, v3_workbuddy_shim, *installed_package["shim_paths"]}
    required_hook_status = _required_hook_event_status(hook_entries, v3_paths)
    points_to_v3 = any(
        entry["type"] == "command" and _entry_targets_any_path(entry, v3_paths)
        for entry in hook_entries
    )

    if not evidence:
        return _candidate(
            entry_id="workbuddy.ldvh-plugin",
            category="environment_hook",
            status="absent",
            trigger="WorkBuddy lifecycle hooks via LDVH plugin, extension package, or adapter",
            evidence=[],
            hook_entry="code/runtime_adapter.py",
            decision="create_target_environment_plugin_before_claiming",
            reason="未发现 WorkBuddy LDVH lifecycle Hook 插件、扩展包或 adapter 实装依据；Codex 会话不能引用自身插件状态替代 WorkBuddy 入口。",
            details={
                "environment_name": WORKBUDDY_ENVIRONMENT_NAME,
                "target_environment_supported": False,
                "required_capability": "installable_verifiable_blocking_lifecycle_hook",
            },
        )
    if not installed_package["thin_reference_ok"]:
        diagnostics.append(
            _diagnostic(
                "warning",
                "ENV_WORKBUDDY_LDVH_PLUGIN_STALE_CACHE",
                installed_package["shim_paths"][0] if installed_package["shim_paths"] else hook_files[0].as_posix(),
                "检测到 WorkBuddy LDVH 插件安装目录，但 installed shim 未满足薄引用边界；需要按 33 更新插件并经 30 验收。",
            )
        )
        return _candidate(
            entry_id="workbuddy.ldvh-plugin",
            category="environment_hook",
            status="available",
            trigger="WorkBuddy lifecycle hooks via LDVH plugin, extension package, or adapter",
            evidence=evidence,
            hook_entry="code/runtime_adapter.py",
            decision="upgrade_workbuddy_plugin_before_claiming",
            reason="WorkBuddy 插件安装目录存在，但真实 shim 未满足薄引用边界；只能作为待升级入口，不能在 Codex 会话中声明 WorkBuddy lifecycle integrated。",
            details={"commands": commands, "hook_entries": hook_entries, "installed_package": installed_package, **required_hook_status},
        )
    if points_to_v3 and required_hook_status["required_events_ok"]:
        return _candidate(
            entry_id="workbuddy.ldvh-plugin",
            category="environment_hook",
            status="available",
            trigger="WorkBuddy lifecycle hooks via LDVH plugin, extension package, or adapter",
            evidence=evidence,
            hook_entry="code/runtime_adapter.py",
            decision="collect_workbuddy_runtime_evidence_before_integration",
            reason="检测到 WorkBuddy 插件安装目录和薄引用 shim；仍需 WorkBuddy 当前环境真实 lifecycle 输出、payload、阻断和回滚依据后才能声明 integrated。",
            details={"commands": commands, "hook_entries": hook_entries, "installed_package": installed_package, **required_hook_status},
        )
    return _candidate(
        entry_id="workbuddy.ldvh-plugin",
        category="environment_hook",
        status="available",
        trigger="WorkBuddy lifecycle hooks via LDVH plugin, extension package, or adapter",
        evidence=evidence,
        hook_entry="code/runtime_adapter.py",
        decision="audit_workbuddy_plugin_hook_target",
        reason="检测到 WorkBuddy 插件安装目录，但 Hook 指向或核心事件覆盖无法归属到当前 V3；不得声明 WorkBuddy lifecycle integrated。",
        details={"commands": commands, "hook_entries": hook_entries, "installed_package": installed_package, **required_hook_status},
    )


def _target_environment_ldvh_plugin_candidate(environment_name: str) -> dict[str, Any]:
    name = _environment_name(environment_name)
    slug = _environment_slug(name)
    return _candidate(
        entry_id=f"{slug}.ldvh-plugin",
        category="environment_hook",
        status="absent",
        trigger=f"{name} lifecycle hooks via LDVH plugin, extension package, or adapter",
        evidence=[],
        hook_entry="code/runtime_adapter.py",
        decision="create_target_environment_plugin_before_claiming",
        reason=(
            f"未发现 {name} 的 LDVH lifecycle Hook 插件、扩展包或 adapter 实装依据；"
            "不得引用其他环境插件状态作为目标环境入口。"
        ),
        details={
            "environment_name": name,
            "target_environment_supported": False,
            "required_capability": "installable_verifiable_blocking_lifecycle_hook",
        },
    )


def build_environment_entry_audit(
    repo: Path = ROOT,
    ldvh_root: Path = ROOT,
    codex_home: Optional[Path] = None,
    workbuddy_home: Optional[Path] = None,
    environment_name: str = "",
) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    resolved_codex_home = Path(codex_home or os.environ.get("CODEX_HOME") or (Path.home() / ".codex")).resolve()
    resolved_workbuddy_home = Path(
        workbuddy_home or os.environ.get("WORKBUDDY_HOME") or (Path.home() / ".workbuddy")
    ).resolve()
    target_environment = _environment_name(environment_name)
    is_codex = _is_codex_environment(target_environment)
    is_workbuddy = _is_workbuddy_environment(target_environment)
    environment = build_environment_status(resolved_repo, resolved_ldvh_root)
    diagnostics: list[dict[str, str]] = list(environment["diagnostics"])

    env_entrypoints = {entry["id"]: entry for entry in environment["entrypoints"]}
    commit_entry = env_entrypoints.get("git.commit-msg", {})
    if is_codex:
        environment_plugin = _codex_ldvh_plugin_candidate(resolved_ldvh_root, resolved_codex_home, diagnostics)
    elif is_workbuddy:
        environment_plugin = _workbuddy_ldvh_plugin_candidate(resolved_ldvh_root, resolved_workbuddy_home, diagnostics)
    else:
        environment_plugin = _target_environment_ldvh_plugin_candidate(target_environment)
    candidates: list[dict[str, Any]] = [
        _candidate(
            entry_id="git.commit-msg",
            category="git_hook",
            status="integrated" if commit_entry.get("integrated") else "deferred",
            trigger="git commit",
            evidence=[commit_entry["path"]] if commit_entry.get("path") else [],
            decision="keep_integrated" if commit_entry.get("integrated") else "install_before_claiming",
            reason="当前唯一已验证的自动阻断入口。" if commit_entry.get("integrated") else "目标 repo 未安装 V3 managed commit-msg Hook。",
            integrated=bool(commit_entry.get("integrated")),
            automatic=bool(commit_entry.get("integrated")),
        ),
        environment_plugin,
        _candidate(
            entry_id="runtime.session_start.auto",
            category="runtime_event",
            status="deferred",
            trigger=f"{target_environment} session start lifecycle hook",
            evidence=environment_plugin["evidence"],
            hook_entry="code/runtime_adapter.py",
            decision="defer",
            reason=(
                f"{target_environment} 的 session start 自动入口必须由对应 LDVH 插件、扩展包或 adapter 安装并验证；"
                "当前未证明目标环境插件已接入。"
            ),
        ),
        _candidate(
            entry_id="runtime.pre_tool_use.auto",
            category="runtime_event",
            status="deferred",
            trigger=f"{target_environment} tool-call-before-write lifecycle hook",
            evidence=environment_plugin["evidence"],
            hook_entry="code/runtime_adapter.py",
            decision="defer",
            reason=(
                f"{target_environment} 的写入前自动入口必须由对应 LDVH 插件、扩展包或 adapter 安装并验证；"
                "当前未证明目标环境插件已接入。"
            ),
        ),
        _candidate(
            entry_id="runtime.completion_claim.auto",
            category="runtime_event",
            status="deferred",
            trigger=f"{target_environment} completion-adjacent lifecycle hook",
            evidence=environment_plugin["evidence"],
            hook_entry="code/runtime_adapter.py",
            decision="defer",
            reason=(
                f"{target_environment} 的完成声明邻近自动入口必须由对应 LDVH 插件、扩展包或 adapter 定义、安装并验证；"
                "当前未证明目标环境 completion_claim 自动入口已接入。"
            ),
        ),
        _candidate(
            entry_id="runtime.adapter.auto",
            category="runtime_adapter",
            status="deferred",
            trigger=f"{target_environment} runtime adapter or environment plugin adapter",
            evidence=environment_plugin["evidence"],
            hook_entry="code/runtime_adapter.py",
            decision="defer",
            reason=(
                "统一 adapter 已有；支持 Hook 的环境应以对应 LDVH 插件、扩展包或 adapter 作为正式安装载体，"
                f"但当前还没有 {target_environment} 插件的真实触发、失败处理和回滚当次依据。"
            ),
        ),
        _removed_top_level_candidate(
            resolved_repo,
            diagnostics,
            entry_id="rules.top_level_mechanism",
            category="removed_top_level",
            legacy_dir="rules",
            source_name="Rules",
            reason="V3 已取消 Rules 资产体系和独立规则权威；不得把 Rules 恢复为环境入口。",
        ),
        _removed_top_level_candidate(
            resolved_repo,
            diagnostics,
            entry_id="skills.top_level_mechanism",
            category="removed_top_level",
            legacy_dir="skills",
            source_name="Skill",
            reason="V3 已取消 Skill 顶层机制、Skill registry 和 Skill 执行闭环；可复用工作流能力只能进入行动模板、Action Guide 或外部包装候选。",
        ),
    ]

    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    integrated = [candidate["id"] for candidate in candidates if candidate["integrated"]]
    available = [candidate["id"] for candidate in candidates if candidate["status"] == "available"]
    deferred = [candidate["id"] for candidate in candidates if candidate["status"] == "deferred"]
    absent = [candidate["id"] for candidate in candidates if candidate["status"] == "absent"]
    removed_top_level = [candidate["id"] for candidate in candidates if candidate["status"] == "removed_top_level"]

    metadata = {
        "read_only": True,
        "authority": "environment_entry_audit",
        "authorization": AUTHORIZATION,
        "root": resolved_ldvh_root.as_posix(),
        "repo": resolved_repo.as_posix(),
        "environment_name": target_environment,
    }
    if is_codex:
        metadata["codex_home"] = resolved_codex_home.as_posix()
    if is_workbuddy:
        metadata["workbuddy_home"] = resolved_workbuddy_home.as_posix()

    summary = {
        "status": "blocked" if blocking else "ok",
        "environment_name": target_environment,
        "integrated_entrypoints": integrated,
        "available_unintegrated_entrypoints": available,
        "deferred_entrypoints": deferred,
        "absent_entrypoints": absent,
        "removed_top_level_entrypoints": removed_top_level,
        "rules_entry_integrated": False,
        "skill_entry_integrated": False,
        "tool_hook_integrated": False,
        "completion_hook_integrated": False,
        "session_start_integrated": False,
        "target_environment_plugin_entry_integrated": bool(environment_plugin["integrated"]),
        "diagnostics": len(diagnostics),
        "blocking": blocking,
        "authorization": AUTHORIZATION,
    }
    if is_codex:
        summary["codex_plugin_entry_integrated"] = bool(environment_plugin["integrated"])
        summary["codex_environment_entry_integrated"] = False
    if is_workbuddy:
        summary["workbuddy_plugin_entry_integrated"] = bool(environment_plugin["integrated"])
        summary["workbuddy_environment_entry_integrated"] = False

    return {
        "metadata": metadata,
        "summary": summary,
        "candidates": candidates,
        "decision": {
            "next_step": "install_or_upgrade_ldvh_environment_plugin_before_auto_runtime_claim",
            "reason": (
                "所有支持 Hook 的协作环境都必须通过对应 LDVH 插件、扩展包或 package 安装环境 Hook，而不是直接写入环境 Hook 系统文件；"
                f"当前目标环境是 {target_environment}，未验证目标环境插件安装、trust、payload 和失败处理前，"
                "除 git.commit-msg 外不得声明自动入口 integrated。"
            ),
        },
        "diagnostics": diagnostics,
    }


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 environment entry audit")
    print(f"- status: {summary['status']}")
    print(f"- integrated_entrypoints: {', '.join(summary['integrated_entrypoints']) or 'none'}")
    print(f"- available_unintegrated_entrypoints: {', '.join(summary['available_unintegrated_entrypoints']) or 'none'}")
    print(f"- deferred_entrypoints: {', '.join(summary['deferred_entrypoints']) or 'none'}")
    print(f"- absent_entrypoints: {', '.join(summary['absent_entrypoints']) or 'none'}")
    print(f"- removed_top_level_entrypoints: {', '.join(summary['removed_top_level_entrypoints']) or 'none'}")
    print(f"- rules_entry_integrated: {_bool_text(summary['rules_entry_integrated'])}")
    print(f"- skill_entry_integrated: {_bool_text(summary['skill_entry_integrated'])}")
    print(f"- tool_hook_integrated: {_bool_text(summary['tool_hook_integrated'])}")
    print(f"- completion_hook_integrated: {_bool_text(summary['completion_hook_integrated'])}")
    print(f"- target_environment_plugin_entry_integrated: {_bool_text(summary['target_environment_plugin_entry_integrated'])}")
    if "codex_plugin_entry_integrated" in summary:
        print(f"- codex_plugin_entry_integrated: {_bool_text(summary['codex_plugin_entry_integrated'])}")
    if "codex_environment_entry_integrated" in summary:
        print(f"- codex_environment_entry_integrated: {_bool_text(summary['codex_environment_entry_integrated'])}")
    if "workbuddy_plugin_entry_integrated" in summary:
        print(f"- workbuddy_plugin_entry_integrated: {_bool_text(summary['workbuddy_plugin_entry_integrated'])}")
    if "workbuddy_environment_entry_integrated" in summary:
        print(f"- workbuddy_environment_entry_integrated: {_bool_text(summary['workbuddy_environment_entry_integrated'])}")

    print("\nCandidates:")
    for candidate in result["candidates"]:
        print(
            f"- {candidate['id']}: status={candidate['status']}, "
            f"integrated={_bool_text(candidate['integrated'])}, decision={candidate['decision']}"
        )
        print(f"  reason: {candidate['reason']}")

    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")

    print("\nDecision:")
    print(f"- next_step: {result['decision']['next_step']}")
    print(f"- reason: {result['decision']['reason']}")
    print("\nAuthorization: none")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit LDVH v3 hook and Codex environment entry candidates.")
    parser.add_argument("--repo", default=ROOT.as_posix(), help="target repository root")
    parser.add_argument("--ldvh-root", default=ROOT.as_posix(), help="LDVH v3 root containing code/ and hooks/")
    parser.add_argument("--codex-home", default="", help="Codex home containing config.toml and plugin cache")
    parser.add_argument("--workbuddy-home", default="", help="WorkBuddy home containing local marketplace plugins")
    parser.add_argument("--environment-name", default="", help="target AI environment name, for example Codex or WorkBuddy")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    codex_home = Path(args.codex_home).resolve() if args.codex_home else None
    workbuddy_home = Path(args.workbuddy_home).resolve() if args.workbuddy_home else None
    result = build_environment_entry_audit(
        Path(args.repo),
        Path(args.ldvh_root),
        codex_home,
        workbuddy_home,
        environment_name=args.environment_name,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
