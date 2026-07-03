from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from typing import Any, Optional

from environment_status import build_environment_status
from ldvh_specs import ROOT


AUTHORIZATION = "none"
PLACEHOLDER_FILES = {".gitkeep", ".DS_Store"}
RUNTIME_PROTOCOL_ENTRY = "hooks/LDVH-RUNTIME-PROTOCOL.md"
THIN_REFERENCE_TEMPLATE = "hooks/LDVH-THIN-REFERENCE-TEMPLATE.md"
LEGACY_LDVH_PLUGIN_COMMAND_RE = re.compile(
    r"/ld-vibe-harness(?:-[^/\s]+)?/code/(hook_adapter|hook_dispatch)\.py"
)


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
    manual_fallback: str = "",
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
        "manual_fallback": manual_fallback,
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


def _hook_commands(hook_files: list[Path]) -> list[str]:
    commands: list[str] = []
    for hook_file in hook_files:
        try:
            data = json.loads(hook_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        hooks = data.get("hooks", {})
        if not isinstance(hooks, dict):
            continue
        for groups in hooks.values():
            if not isinstance(groups, list):
                continue
            for group in groups:
                if not isinstance(group, dict):
                    continue
                for item in group.get("hooks", []):
                    if isinstance(item, dict) and isinstance(item.get("command"), str):
                        commands.append(item["command"])
    return commands


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
    commands = _hook_commands(hook_files)
    command_blob = "\n".join(commands)
    v3_adapter = (ldvh_root / "code" / "runtime_adapter.py").as_posix()
    v3_codex_shim = (ldvh_root / "hooks" / "environment-plugins" / "codex-ldvh-v3" / "hooks" / "ldvh_runtime_shim.py").as_posix()
    points_to_v3 = v3_adapter in command_blob or v3_codex_shim in command_blob
    stale_commands = [command for command in commands if LEGACY_LDVH_PLUGIN_COMMAND_RE.search(command)]
    points_to_legacy = bool(stale_commands)

    if not evidence:
        return _candidate(
            entry_id="codex.ldvh-plugin",
            category="environment_hook",
            status="absent",
            trigger="Codex lifecycle hooks via LDVH plugin",
            evidence=[],
            manual_fallback="code/runtime_adapter.py",
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
            manual_fallback="code/runtime_adapter.py",
            decision="enable_or_install_v3_plugin",
            reason="检测到 Codex LDVH 插件相关文件，但插件未在 Codex config 中启用。",
            details={"commands": commands},
        )
    if points_to_legacy:
        diagnostics.append(
            _diagnostic(
                "warning",
                "ENV_CODEX_LDVH_PLUGIN_STALE",
                hook_files[0].as_posix() if hook_files else config_path.as_posix(),
                "检测到已启用的 LDVH Codex 插件，但 Hook 命令指向旧 ld-vibe-harness 路径，不能声明为 V3 环境入口；环境 Hook 正式安装必须通过对应 LDVH 插件或扩展包完成。",
            )
        )
        return _candidate(
            entry_id="codex.ldvh-plugin",
            category="environment_hook",
            status="available",
            trigger="Codex lifecycle hooks via LDVH plugin",
            evidence=evidence,
            manual_fallback="code/runtime_adapter.py",
            decision="reinstall_for_v3",
            reason="LDVH 插件已启用但指向旧 V2/旧仓库路径；需要 V3 插件包重新安装或升级后才可声明接入。",
            details={"commands": commands, "stale_commands": stale_commands},
        )
    if points_to_v3:
        return _candidate(
            entry_id="codex.ldvh-plugin",
            category="environment_hook",
            status="available",
            trigger="Codex lifecycle hooks via LDVH plugin",
            evidence=evidence,
            manual_fallback="code/runtime_adapter.py",
            decision="verify_trust_and_runtime_before_integration",
            reason="检测到指向当前 V3 的 LDVH 插件 Hook 配置，但仍需验证 Codex trust、真实触发、payload 和失败处理后才能声明 integrated。",
            details={"commands": commands},
        )
    return _candidate(
        entry_id="codex.ldvh-plugin",
        category="environment_hook",
        status="available",
        trigger="Codex lifecycle hooks via LDVH plugin",
        evidence=evidence,
        manual_fallback="code/runtime_adapter.py",
        decision="audit_plugin_hook_target",
        reason="检测到 LDVH 插件配置或缓存，但 Hook 指向无法归属到当前 V3；不得声明环境入口已接入。",
        details={"commands": commands},
    )


def _codex_candidate(repo: Path, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    instruction_files = _repo_files(
        repo,
        [
            "AGENTS.md",
            ".codex/config.toml",
            ".codex/settings.json",
            ".codex/rules.md",
            ".codex/AGENTS.md",
        ],
    )
    instruction_dirs = _repo_dirs(repo, [".codex"])
    if instruction_files:
        diagnostics.append(
            _diagnostic(
                "warning",
                "ENV_CODEX_ENTRY_FILES_NOT_INTEGRATED",
                repo.as_posix(),
                "检测到 Codex/agent 指令文件，但当前审计只能确认文件存在，不能证明 session/tool/completion 生命周期已自动接入。",
            )
        )
        return _candidate(
            entry_id="codex.repo-instructions",
            category="codex_environment",
            status="available",
            trigger="codex repo instruction loader",
            evidence=_as_posix(instruction_files),
            decision="audit_before_integration",
            reason="repo 指令文件可能影响 AI 行为，但不能替代 V3 runtime Hook、payload 或失败处理审计。",
        )
    if instruction_dirs:
        return _candidate(
            entry_id="codex.repo-instructions",
            category="codex_environment",
            status="deferred",
            trigger="codex repo instruction loader",
            evidence=_as_posix(instruction_dirs),
            decision="defer",
            reason="检测到 Codex 目录但没有可识别入口文件。",
        )
    return _candidate(
        entry_id="codex.repo-instructions",
        category="codex_environment",
        status="absent",
        trigger="codex repo instruction loader",
        evidence=[],
        decision="defer",
        reason="未发现 AGENTS.md 或 .codex repo-local Codex 配置入口。",
    )


def _runtime_protocol_entry_candidate(ldvh_root: Path) -> dict[str, Any]:
    entry_path = ldvh_root / RUNTIME_PROTOCOL_ENTRY
    if entry_path.is_file():
        return _candidate(
            entry_id="hooks.runtime-protocol",
            category="hook_protocol_entry",
            status="available",
            trigger="environment hook, plugin, external adapter, repo instruction, or manual wrapper",
            evidence=[entry_path.as_posix()],
            manual_fallback="code/runtime_adapter.py",
            decision="reference_from_environment_entry_without_claiming_integration",
            reason="检测到 V3 Runtime Protocol 可见入口；该文件只提供入口指向，不能证明环境 Hook、插件或手动包装已 integrated。",
        )
    return _candidate(
        entry_id="hooks.runtime-protocol",
        category="hook_protocol_entry",
        status="absent",
        trigger="environment hook, plugin, external adapter, repo instruction, or manual wrapper",
        evidence=[],
        manual_fallback="code/runtime_adapter.py",
        decision="create_hook_protocol_entry_before_reference",
        reason="未发现 hooks/LDVH-RUNTIME-PROTOCOL.md；环境入口缺少统一 Runtime Protocol 可见入口资产。",
    )


def _thin_reference_template_candidate(ldvh_root: Path) -> dict[str, Any]:
    template_path = ldvh_root / THIN_REFERENCE_TEMPLATE
    if template_path.is_file():
        return _candidate(
            entry_id="hooks.thin-reference-template",
            category="repo_instruction_candidate",
            status="available",
            trigger="repo instruction, agent instruction, or manual thin reference",
            evidence=[template_path.as_posix()],
            manual_fallback=RUNTIME_PROTOCOL_ENTRY,
            decision="reference_only_without_claiming_integration",
            reason="检测到 V3 薄引用模板；该模板只用于无 Hook 或只支持指令入口的环境引用 V3 Runtime Protocol 和 specs，不能证明环境已自动接入。",
        )
    return _candidate(
        entry_id="hooks.thin-reference-template",
        category="repo_instruction_candidate",
        status="absent",
        trigger="repo instruction, agent instruction, or manual thin reference",
        evidence=[],
        manual_fallback=RUNTIME_PROTOCOL_ENTRY,
        decision="create_template_before_reference",
        reason="未发现 V3 薄引用模板；无 Hook 环境缺少可复制的最小 repo instruction 引用资产。",
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
    thin_reference_template = _thin_reference_template_candidate(resolved_ldvh_root)
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
        thin_reference_template,
        codex_plugin,
        _candidate(
            entry_id="runtime.session_start.auto",
            category="runtime_event",
            status="deferred",
            trigger="Codex SessionStart or equivalent session start",
            evidence=codex_plugin["evidence"],
            manual_fallback="code/session_start.py",
            decision="defer",
            reason="Codex 提供 SessionStart 生命周期 Hook 机制；按通用环境 Hook 口径，V3 要通过对应 LDVH 插件或扩展包安装并验证，当前未证明 V3 插件已接入。",
        ),
        _candidate(
            entry_id="runtime.pre_tool_use.auto",
            category="runtime_event",
            status="deferred",
            trigger="Codex PreToolUse or equivalent tool call before write/edit/apply_patch",
            evidence=codex_plugin["evidence"],
            manual_fallback="code/pre_tool_use.py",
            decision="defer",
            reason="Codex 提供 PreToolUse 生命周期 Hook 机制；按通用环境 Hook 口径，V3 要通过对应 LDVH 插件或扩展包安装并验证，当前未证明 V3 插件已接入。",
        ),
        _candidate(
            entry_id="runtime.completion_claim.auto",
            category="runtime_event",
            status="deferred",
            trigger="Codex Stop or equivalent completion-adjacent event",
            evidence=codex_plugin["evidence"],
            manual_fallback="code/completion_claim.py",
            decision="defer",
            reason="Codex 提供 Stop 生命周期 Hook 可作为完成声明邻近候选；V3 尚未通过对应 LDVH 插件或扩展包定义、安装和验证 completion_claim 自动入口。",
        ),
        _candidate(
            entry_id="runtime.adapter.auto",
            category="runtime_adapter",
            status="deferred",
            trigger="external runtime adapter or Codex plugin adapter",
            evidence=codex_plugin["evidence"],
            manual_fallback="code/runtime_adapter.py",
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
            reason="V3 已取消 Rules 资产体系和独立规则权威；无 Hook fallback 只能归为环境薄引用或 repo instruction，不恢复 rules/ 目录机制。",
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
        _codex_candidate(resolved_repo, diagnostics),
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
