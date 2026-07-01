from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from environment_status import build_environment_status
from ldvh_specs import ROOT


AUTHORIZATION = "none"
PLACEHOLDER_FILES = {".gitkeep", ".DS_Store"}


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


def _codex_candidate(repo: Path, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    instruction_files = _repo_files(
        repo,
        [
            "AGENTS.md",
            ".codex/config.toml",
            ".codex/settings.json",
            ".codex/rules.md",
            ".codex/AGENTS.md",
            ".codex-plugin/plugin.json",
        ],
    )
    instruction_dirs = _repo_dirs(repo, [".codex", ".codex-plugin"])
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
        reason="未发现 AGENTS.md、.codex 或 repo-local Codex 配置入口。",
    )


def build_environment_entry_audit(repo: Path = ROOT, ldvh_root: Path = ROOT) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    environment = build_environment_status(resolved_repo, resolved_ldvh_root)
    diagnostics: list[dict[str, str]] = list(environment["diagnostics"])

    env_entrypoints = {entry["id"]: entry for entry in environment["entrypoints"]}
    commit_entry = env_entrypoints.get("git.commit-msg", {})
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
        _candidate(
            entry_id="runtime.session_start.auto",
            category="runtime_event",
            status="deferred",
            trigger="session start",
            evidence=[],
            manual_fallback="code/session_start.py",
            decision="defer",
            reason="未发现可安装的真实 session start 触发点；当前仅有 manual.session_start。",
        ),
        _candidate(
            entry_id="runtime.pre_tool_use.auto",
            category="runtime_event",
            status="deferred",
            trigger="tool call before write/edit/apply_patch",
            evidence=[],
            manual_fallback="code/pre_tool_use.py",
            decision="defer",
            reason="未发现工具调用前置 Hook 或可阻断 payload 通道；当前仅有 manual.pre_tool_use。",
        ),
        _candidate(
            entry_id="runtime.completion_claim.auto",
            category="runtime_event",
            status="deferred",
            trigger="completion claim",
            evidence=[],
            manual_fallback="code/completion_claim.py",
            decision="defer",
            reason="未发现完成声明前置 Hook；当前仅有 manual.completion_claim。",
        ),
        _candidate(
            entry_id="runtime.adapter.auto",
            category="runtime_adapter",
            status="deferred",
            trigger="external runtime adapter",
            evidence=[],
            manual_fallback="code/runtime_adapter.py",
            decision="defer",
            reason="统一 adapter 已有，但没有真实外部事件源、安装状态、失败处理和回滚证据。",
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
            "codex_environment_entry_integrated": False,
            "diagnostics": len(diagnostics),
            "blocking": blocking,
            "authorization": AUTHORIZATION,
        },
        "candidates": candidates,
        "decision": {
            "next_step": "defer_auto_runtime_until_real_trigger_exists",
            "reason": "除 git.commit-msg 外，当前 repo 没有可复现证据证明 tool hook、completion hook 或 Codex 生命周期入口已自动触发；Rules/Skill 顶层机制已取消，不作为待启用入口。",
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
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_environment_entry_audit(Path(args.repo), Path(args.ldvh_root))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
