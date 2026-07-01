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


def _rules_candidate(repo: Path, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    rules_dir = repo / "rules"
    rule_files = _non_placeholder_files(rules_dir)
    if rule_files:
        diagnostics.append(
            _diagnostic(
                "warning",
                "ENV_RULES_FILES_NOT_INTEGRATED",
                rules_dir.as_posix(),
                "检测到 rules/ 文件，但当前没有 repo-local 证据证明它们会被环境自动加载或阻断。",
            )
        )
        return _candidate(
            entry_id="rules.thin-reference",
            category="rules",
            status="available",
            trigger="environment rules loader",
            evidence=_as_posix(rule_files),
            decision="audit_before_integration",
            reason="rules 文件存在，但不能仅凭文件存在声明环境已自动加载。",
        )
    if rules_dir.is_dir():
        return _candidate(
            entry_id="rules.thin-reference",
            category="rules",
            status="deferred",
            trigger="environment rules loader",
            evidence=[rules_dir.as_posix()],
            decision="defer",
            reason="rules/ 仅是占位目录，没有可加载规则文件，也没有安装状态证据。",
        )
    return _candidate(
        entry_id="rules.thin-reference",
        category="rules",
        status="absent",
        trigger="environment rules loader",
        evidence=[],
        decision="defer",
        reason="未发现 repo-local rules 入口。",
    )


def _skills_candidate(repo: Path, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    skills_dir = repo / "skills"
    skill_files = sorted(item for item in skills_dir.rglob("SKILL.md")) if skills_dir.is_dir() else []
    other_files = [item for item in _non_placeholder_files(skills_dir) if item.name != "SKILL.md"]
    if skill_files or other_files:
        diagnostics.append(
            _diagnostic(
                "warning",
                "ENV_SKILL_FILES_NOT_INTEGRATED",
                skills_dir.as_posix(),
                "检测到 skills/ 内容，但 V3 不把 Skill 作为顶层机制；若要使用，只能作为外部包装候选另行审计。",
            )
        )
        return _candidate(
            entry_id="skills.external-wrapper",
            category="skill",
            status="available",
            trigger="external skill loader",
            evidence=_as_posix(skill_files + other_files),
            decision="defer",
            reason="Skill 内容不能直接成为 V3 规则入口或行动模板实例。",
        )
    if skills_dir.is_dir():
        return _candidate(
            entry_id="skills.external-wrapper",
            category="skill",
            status="deferred",
            trigger="external skill loader",
            evidence=[skills_dir.as_posix()],
            decision="defer",
            reason="skills/ 仅是占位目录，没有可安装 Skill 内容。",
        )
    return _candidate(
        entry_id="skills.external-wrapper",
        category="skill",
        status="absent",
        trigger="external skill loader",
        evidence=[],
        decision="defer",
        reason="未发现 repo-local Skill 包装入口。",
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
        _rules_candidate(resolved_repo, diagnostics),
        _skills_candidate(resolved_repo, diagnostics),
        _codex_candidate(resolved_repo, diagnostics),
    ]

    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    integrated = [candidate["id"] for candidate in candidates if candidate["integrated"]]
    available = [candidate["id"] for candidate in candidates if candidate["status"] == "available"]
    deferred = [candidate["id"] for candidate in candidates if candidate["status"] == "deferred"]
    absent = [candidate["id"] for candidate in candidates if candidate["status"] == "absent"]

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
            "rules_entry_integrated": False,
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
            "next_step": "defer_auto_runtime_and_rules_until_real_trigger_exists",
            "reason": "除 git.commit-msg 外，当前 repo 没有可复现证据证明 Rules、tool hook、completion hook 或 Codex 生命周期入口已自动触发。",
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
    print(f"- rules_entry_integrated: {_bool_text(summary['rules_entry_integrated'])}")
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
    parser = argparse.ArgumentParser(description="Audit LDVH v3 Rules, hook, and Codex environment entry candidates.")
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
