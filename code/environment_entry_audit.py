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
RUNTIME_PROTOCOL_ENTRY = "hooks/LDVH-RUNTIME-PROTOCOL.md"
LEGACY_LDVH_PLUGIN_COMMAND_RE = re.compile(
    r"/ld-vibe-harness(?:-[^/\s]+)?/code/(hook_adapter|hook_dispatch)\.py"
)
STALE_REPO_ENVIRONMENT_PLUGIN_COMMAND_RE = re.compile(
    r"/ld-vibe-harness(?:-[^/\s]+)?/code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim\.py"
)
CODEX_REQUIRED_HOOK_EVENTS = ("SessionStart", "PreToolUse", "Stop")


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


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


def _hook_entries(hook_files: list[Path]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for hook_file in hook_files:
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


def _command_targets_any_path(command: str, paths: set[str]) -> bool:
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


def _required_hook_event_status(entries: list[dict[str, str]], v3_paths: set[str]) -> dict[str, Any]:
    by_event: dict[str, list[dict[str, str]]] = {event: [] for event in CODEX_REQUIRED_HOOK_EVENTS}
    for entry in entries:
        if entry["event"] in by_event:
            by_event[entry["event"]].append(entry)
    satisfied = {
        event: any(
            entry["type"] == "command" and _command_targets_any_path(entry["command"], v3_paths)
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
    v3_adapter = (ldvh_root / "code" / "runtime_adapter.py").as_posix()
    v3_codex_shim = (ldvh_root / "hooks" / "environment-plugins" / "codex-ldvh-v3" / "hooks" / "ldvh_runtime_shim.py").as_posix()
    v3_paths = {v3_adapter, v3_codex_shim}
    required_hook_status = _required_hook_event_status(hook_entries, v3_paths)
    points_to_v3 = any(
        entry["type"] == "command" and _command_targets_any_path(entry["command"], v3_paths)
        for entry in hook_entries
    )
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
            details={"commands": commands, "hook_entries": hook_entries, **required_hook_status},
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
                **required_hook_status,
            },
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
            reason="检测到指向当前 V3 的 LDVH 插件 Hook 配置，且 SessionStart、PreToolUse、Stop 三类必需事件齐全；仍需真实触发、payload 和失败处理证据后才能声明 integrated。",
            details={"commands": commands, "hook_entries": hook_entries, **required_hook_status},
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
            details={"commands": commands, "hook_entries": hook_entries, **required_hook_status},
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
        details={"commands": commands, "hook_entries": hook_entries, **required_hook_status},
    )


def _runtime_protocol_entry_candidate(ldvh_root: Path) -> dict[str, Any]:
    entry_path = ldvh_root / RUNTIME_PROTOCOL_ENTRY
    if entry_path.is_file():
        return _candidate(
            entry_id="hooks.runtime-protocol",
            category="hook_protocol_entry",
            status="available",
            trigger="environment hook, plugin, extension package, or runtime adapter",
            evidence=[entry_path.as_posix()],
            hook_entry="code/runtime_adapter.py",
            decision="reference_from_environment_entry_without_claiming_integration",
            reason="检测到 V3 Runtime Protocol 可见入口；该文件只提供 Hook 入口指向，不能证明环境 Hook、插件或 adapter 已 integrated。",
        )
    return _candidate(
        entry_id="hooks.runtime-protocol",
        category="hook_protocol_entry",
        status="absent",
        trigger="environment hook, plugin, extension package, or runtime adapter",
        evidence=[],
        hook_entry="code/runtime_adapter.py",
        decision="create_hook_protocol_entry_before_reference",
        reason="未发现 hooks/LDVH-RUNTIME-PROTOCOL.md；环境入口缺少统一 Runtime Protocol 可见入口资产。",
    )


def build_environment_entry_audit(
    repo: Path = ROOT,
    ldvh_root: Path = ROOT,
    codex_home: Optional[Path] = None,
) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    resolved_codex_home = Path(codex_home or os.environ.get("CODEX_HOME") or (Path.home() / ".codex")).resolve()
    environment = build_environment_status(resolved_repo, resolved_ldvh_root)
    diagnostics: list[dict[str, str]] = list(environment["diagnostics"])

    env_entrypoints = {entry["id"]: entry for entry in environment["entrypoints"]}
    commit_entry = env_entrypoints.get("git.commit-msg", {})
    codex_plugin = _codex_ldvh_plugin_candidate(resolved_ldvh_root, resolved_codex_home, diagnostics)
    runtime_protocol_entry = _runtime_protocol_entry_candidate(resolved_ldvh_root)
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
        runtime_protocol_entry,
        codex_plugin,
        _candidate(
            entry_id="runtime.session_start.auto",
            category="runtime_event",
            status="deferred",
            trigger="Codex SessionStart or equivalent session start",
            evidence=codex_plugin["evidence"],
            hook_entry="code/runtime_adapter.py",
            decision="defer",
            reason="Codex 提供 SessionStart 生命周期 Hook 机制；按通用环境 Hook 口径，V3 要通过对应 LDVH 插件或扩展包安装并验证，当前未证明 V3 插件已接入。",
        ),
        _candidate(
            entry_id="runtime.pre_tool_use.auto",
            category="runtime_event",
            status="deferred",
            trigger="Codex PreToolUse or equivalent tool call before write/edit/apply_patch",
            evidence=codex_plugin["evidence"],
            hook_entry="code/runtime_adapter.py",
            decision="defer",
            reason="Codex 提供 PreToolUse 生命周期 Hook 机制；按通用环境 Hook 口径，V3 要通过对应 LDVH 插件或扩展包安装并验证，当前未证明 V3 插件已接入。",
        ),
        _candidate(
            entry_id="runtime.completion_claim.auto",
            category="runtime_event",
            status="deferred",
            trigger="Codex Stop or equivalent completion-adjacent event",
            evidence=codex_plugin["evidence"],
            hook_entry="code/runtime_adapter.py",
            decision="defer",
            reason="Codex 提供 Stop 生命周期 Hook 可作为完成声明邻近候选；V3 尚未通过对应 LDVH 插件或扩展包定义、安装和验证 completion_claim 自动入口。",
        ),
        _candidate(
            entry_id="runtime.adapter.auto",
            category="runtime_adapter",
            status="deferred",
            trigger="external runtime adapter or Codex plugin adapter",
            evidence=codex_plugin["evidence"],
            hook_entry="code/runtime_adapter.py",
            decision="defer",
            reason="统一 adapter 已有；支持 Hook 的环境应以对应 LDVH 插件或扩展包作为正式安装载体，但当前还没有 V3 插件的真实触发、失败处理和回滚证据。",
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

    return {
        "metadata": {
            "read_only": True,
            "authority": "environment_entry_audit",
            "authorization": AUTHORIZATION,
            "root": resolved_ldvh_root.as_posix(),
            "repo": resolved_repo.as_posix(),
            "codex_home": resolved_codex_home.as_posix(),
        },
        "summary": {
            "status": "blocked" if blocking else "ok",
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
            "codex_plugin_entry_integrated": bool(codex_plugin["integrated"]),
            "codex_environment_entry_integrated": False,
            "diagnostics": len(diagnostics),
            "blocking": blocking,
            "authorization": AUTHORIZATION,
        },
        "candidates": candidates,
        "decision": {
            "next_step": "install_or_upgrade_ldvh_environment_plugin_before_auto_runtime_claim",
            "reason": "所有支持 Hook 的协作环境都必须通过对应 LDVH 插件、扩展包或 package 安装环境 Hook，而不是直接写入环境 Hook 系统文件；当前已审计到 Codex lifecycle Hook 机制，但未验证 V3 插件安装、trust、payload 和失败处理前，除 git.commit-msg 外不得声明自动入口 integrated。",
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
    print(f"- codex_plugin_entry_integrated: {_bool_text(summary['codex_plugin_entry_integrated'])}")
    print(f"- codex_environment_entry_integrated: {_bool_text(summary['codex_environment_entry_integrated'])}")

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
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    codex_home = Path(args.codex_home).resolve() if args.codex_home else None
    result = build_environment_entry_audit(Path(args.repo), Path(args.ldvh_root), codex_home)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
