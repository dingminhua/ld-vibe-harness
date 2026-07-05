from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from environment_entry_audit import build_environment_entry_audit
from governed_hook_adapter import build_governed_hook_adapter
from install_git_hooks import COMMIT_MSG_HOOK, planned_install_target
from install_verification import build_install_verification
from ldvh_specs import (
    GOVERNED_PROJECTS_CONFIG_PATH,
    ROOT,
    parse_governed_projects_config,
    resolve_governed_subject,
    validate_governed_projects_config,
)


AUTHORIZATION = "human_gate_required_for_apply"
ENVIRONMENT_STRATEGIES = {
    "plugin_hook",
    "thin_reference",
    "manual_entrypoint",
    "external_adapter_candidate",
    "unsupported",
}


def _diagnostic(level: str, code: str, path: str, message: str, disposition: str = "blocking") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "path": path,
        "message": message,
        "disposition": disposition,
    }


def _spec_diagnostics(config_root: Path) -> list[dict[str, str]]:
    return [
        {**diagnostic.to_dict(), "disposition": "blocking"}
        for diagnostic in validate_governed_projects_config(config_root)
    ]


def _install_context_diagnostic(diagnostic: dict[str, str]) -> dict[str, str]:
    if diagnostic.get("code") == "ENV_COMMIT_MSG_HOOK_NOT_INSTALLED":
        return {
            **diagnostic,
            "level": "warning",
            "disposition": "planned_write",
            "message": "目标 repo 尚未安装 V3 managed commit-msg hook；安装向导将其作为 planned_writes 处理。",
        }
    return diagnostic


def _project_path(config_root: Path, project: dict[str, Any]) -> Path | None:
    raw_path = project.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = config_root / path
    return path.resolve()


def _is_git_worktree(path: Path) -> bool:
    return (path / ".git").exists() or _git_common_dir(path) != ""


def _git_common_dir(path: Path) -> str:
    import subprocess

    completed = subprocess.run(
        ["git", "-C", path.as_posix(), "rev-parse", "--git-common-dir"],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        return ""
    common_dir = Path(completed.stdout.strip())
    if not common_dir.is_absolute():
        common_dir = path / common_dir
    return common_dir.resolve().as_posix()


def _infer_environment_strategy(
    *,
    requested: str,
    environment_name: str,
    environment_audit: dict[str, Any],
) -> str:
    if requested:
        return requested
    if environment_name.lower() != "codex":
        return "manual_entrypoint"
    candidates = {candidate["id"]: candidate for candidate in environment_audit.get("candidates", [])}
    codex_plugin = candidates.get("codex.ldvh-plugin", {})
    if codex_plugin.get("status") == "available":
        return "plugin_hook"
    runtime_protocol = candidates.get("hooks.runtime-protocol", {})
    if runtime_protocol.get("status") == "available":
        return "thin_reference"
    return "manual_entrypoint"


def _strategy_is_valid(strategy: str) -> bool:
    return strategy in ENVIRONMENT_STRATEGIES


def _selected_projects(config_root: Path, resolution: dict[str, Any]) -> list[dict[str, Any]]:
    config = parse_governed_projects_config(config_root)
    selected_id = resolution.get("governed_project_id")
    projects: list[dict[str, Any]] = []
    for project in config.get("projects", []):
        if not isinstance(project, dict):
            continue
        project_id = str(project.get("id") or "")
        if selected_id and project_id != selected_id:
            continue
        path = _project_path(config_root, project)
        if path is None:
            continue
        projects.append(
            {
                "id": project_id,
                "name": str(project.get("name") or project_id),
                "path": path.as_posix(),
                "git_common_dir": _git_common_dir(path),
                "git_worktree": _is_git_worktree(path),
            }
        )
    return projects


def _planned_writes(
    strategy: str,
    target_projects: list[dict[str, Any]],
    ldvh_root: Path,
    repo: Path,
    hook_status: dict[str, Any],
) -> list[dict[str, Any]]:
    if strategy == "plugin_hook":
        status = hook_status.get("hook_status", {})
        writes: list[dict[str, Any]] = []
        for project in target_projects:
            target_dir, hooks_path_value = planned_install_target(Path(project["path"]), ldvh_root)
            target_hook = target_dir / COMMIT_MSG_HOOK
            writes.extend([
                {
                    "kind": "git_config",
                    "path": project["path"],
                    "backend": "code/install_git_hooks.py",
                    "operation": "set_worktree_core_hooks_path",
                    "project_id": project["id"],
                    "current_core_hooks_path": status.get("core_hooks_path", ""),
                    "planned_core_hooks_path": hooks_path_value,
                },
                {
                    "kind": "git_commit_msg_hook",
                    "path": target_hook.as_posix(),
                    "current_active_hook": status.get("active_hook", ""),
                    "common_hook": status.get("common_hook", ""),
                    "backend": "code/governed_hook_adapter.py",
                    "operation": "install_or_upgrade",
                    "project_id": project["id"],
                },
            ])
        return writes
    return []


def _handoff_candidates(strategy: str, ldvh_root: Path, repo: Path) -> list[dict[str, Any]]:
    if strategy == "thin_reference":
        return [
            {
                "kind": "thin_reference",
                "path": (repo / "AGENTS.md").resolve().as_posix(),
                "operation": "handoff_candidate_only",
                "non_executable_in_v1": True,
                "reference": (ldvh_root / "hooks/LDVH-RUNTIME-PROTOCOL.md").as_posix(),
            }
        ]
    if strategy == "manual_entrypoint":
        return [
            {
                "kind": "manual_entrypoint",
                "path": (ldvh_root / "code/runtime_adapter.py").as_posix(),
                "operation": "handoff_command_only",
                "non_executable_in_v1": True,
            }
        ]
    if strategy == "external_adapter_candidate":
        return [
            {
                "kind": "external_adapter_candidate",
                "operation": "handoff_candidate_only",
                "non_executable_in_v1": True,
            }
        ]
    if strategy == "unsupported":
        return [
            {
                "kind": "unsupported",
                "operation": "blocked_handoff",
                "non_executable_in_v1": True,
            }
        ]
    return []


def _skipped_writes(strategy: str) -> list[dict[str, Any]]:
    if strategy != "plugin_hook":
        return [
            {
                "kind": strategy,
                "reason": "install_wizard v1 只生成薄引用 / manual entrypoint 承接计划，不执行写入。",
                "non_executable_in_v1": True,
            }
        ]
    return []


def _unknown_strategy_result(
    *,
    command: str,
    governance_root: Path,
    ldvh_root: Path,
    repo: Path,
    environment_name: str,
    environment_strategy: str,
) -> dict[str, Any]:
    diagnostic = _diagnostic(
        "blocking",
        "INSTALL_WIZARD_UNKNOWN_ENVIRONMENT_STRATEGY",
        environment_strategy,
        "environment_strategy 必须是 10 允许的枚举值。",
    )
    return {
        "metadata": {
            "read_only": command in {"check", "plan", "verify"},
            "authority": "install_wizard",
            "authorization": "none",
            "command": command,
            "ldvh_root": ldvh_root.resolve().as_posix(),
            "governance_root": governance_root.resolve().as_posix(),
            "repo": repo.resolve().as_posix(),
            "environment_name": environment_name,
        },
        "summary": {
            "status": "blocked",
            "blocking": 1,
            "diagnostics": 1,
            "environment_strategy": environment_strategy,
        },
        "diagnostics": [diagnostic],
        "source_refs": [
            {"path": "specs/10-安装与配置规范.md", "role": "environment_strategy_contract"},
        ],
    }


def build_install_check(
    *,
    governance_root: Path,
    ldvh_root: Path = ROOT,
    repo: Path,
    codex_home: Path | None = None,
    environment_name: str = "Codex",
    environment_strategy: str = "",
) -> dict[str, Any]:
    resolved_governance_root = governance_root.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    resolved_repo = repo.resolve()
    diagnostics = _spec_diagnostics(resolved_governance_root)
    if environment_strategy and not _strategy_is_valid(environment_strategy):
        return _unknown_strategy_result(
            command="check",
            governance_root=governance_root,
            ldvh_root=ldvh_root,
            repo=repo,
            environment_name=environment_name,
            environment_strategy=environment_strategy,
        )

    resolution = resolve_governed_subject(
        resolved_governance_root,
        cwd=resolved_repo,
        target_paths=[resolved_repo],
        read_write_kind="write",
    )
    if resolution["blocked"]:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "INSTALL_WIZARD_TARGET_BLOCKED",
                ",".join(resolution["target_paths"]),
                resolution["message"] or "目标项目解析被阻断。",
            )
        )
    elif not resolution["governed"]:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "INSTALL_WIZARD_TARGET_NOT_GOVERNED",
                resolved_repo.as_posix(),
                "目标项目未命中 LDVH 管辖配置，停止安装计划生成。",
            )
        )

    hook_status = build_governed_hook_adapter(
        command="status",
        repo=resolved_repo,
        governance_root=resolved_governance_root,
        ldvh_root=resolved_ldvh_root,
    )
    for diagnostic in hook_status.get("diagnostics", []):
        if diagnostic["code"] not in {
            "GOVERNED_HOOK_TARGET_NOT_GOVERNED",
            "GOVERNED_HOOK_TARGET_BLOCKED",
        }:
            diagnostics.append(diagnostic)

    environment_audit = build_environment_entry_audit(
        resolved_repo,
        resolved_ldvh_root,
        codex_home,
    )
    diagnostics.extend(_install_context_diagnostic(diagnostic) for diagnostic in environment_audit.get("diagnostics", []))
    strategy = _infer_environment_strategy(
        requested=environment_strategy,
        environment_name=environment_name,
        environment_audit=environment_audit,
    )
    target_projects = _selected_projects(resolved_governance_root, resolution)
    if not target_projects and resolution["governed"]:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "INSTALL_WIZARD_TARGET_PROJECT_NOT_FOUND",
                resolved_repo.as_posix(),
                "目标项目已解析为受管，但无法从配置中取回项目记录。",
            )
        )

    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    return {
        "metadata": {
            "read_only": True,
            "authority": "install_wizard",
            "authorization": "none",
            "command": "check",
            "ldvh_root": resolved_ldvh_root.as_posix(),
            "governance_root": resolved_governance_root.as_posix(),
            "repo": resolved_repo.as_posix(),
            "environment_name": environment_name,
        },
        "summary": {
            "status": "blocked" if blocking else "ok",
            "blocking": blocking,
            "diagnostics": len(diagnostics),
            "governed": bool(resolution["governed"]),
            "governed_project_id": resolution["governed_project_id"],
            "environment_strategy": strategy,
        },
        "governed_project": resolution,
        "target_projects": target_projects,
        "hook_status": hook_status,
        "environment_audit": environment_audit,
        "diagnostics": diagnostics,
        "source_refs": [
            {"path": "specs/10-安装与配置规范.md", "role": "install_config_contract"},
            {"path": "specs/01-保障与衔接.md", "role": "environment_boundary"},
            {"path": "specs/07-Code确定性执行规范.md", "role": "code_determinism"},
            {"path": "specs/09-测试与验证规范.md", "role": "verification_boundary"},
            {"path": "code/governed_hook_adapter.py", "role": "hook_backend"},
            {"path": "code/environment_entry_audit.py", "role": "environment_audit"},
        ],
    }


def build_install_plan(
    *,
    governance_root: Path,
    ldvh_root: Path = ROOT,
    repo: Path,
    codex_home: Path | None = None,
    environment_name: str = "Codex",
    environment_strategy: str = "",
) -> dict[str, Any]:
    check = build_install_check(
        governance_root=governance_root,
        ldvh_root=ldvh_root,
        repo=repo,
        codex_home=codex_home,
        environment_name=environment_name,
        environment_strategy=environment_strategy,
    )
    resolved_governance_root = governance_root.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    resolved_repo = repo.resolve()
    strategy = check["summary"]["environment_strategy"]
    if environment_strategy and not _strategy_is_valid(environment_strategy):
        unknown = _unknown_strategy_result(
            command="plan",
            governance_root=governance_root,
            ldvh_root=ldvh_root,
            repo=repo,
            environment_name=environment_name,
            environment_strategy=environment_strategy,
        )
        return {**unknown, "install_plan": {}}
    planned_writes = []
    if not check["summary"]["blocking"]:
        planned_writes = _planned_writes(
            strategy,
            check["target_projects"],
            resolved_ldvh_root,
            resolved_repo,
            check["hook_status"],
        )
    handoff_candidates = _handoff_candidates(strategy, resolved_ldvh_root, resolved_repo)
    skipped_writes = _skipped_writes(strategy)

    plan = {
        "ldvh_root": resolved_ldvh_root.as_posix(),
        "workspace_root": resolved_governance_root.as_posix(),
        "governed_config": (resolved_governance_root / GOVERNED_PROJECTS_CONFIG_PATH).as_posix(),
        "target_projects": check["target_projects"],
        "environment_strategy": strategy,
        "checks": {
            "governed_project": check["governed_project"],
            "hook_status": check["hook_status"]["summary"],
            "environment_audit": check["environment_audit"]["summary"],
        },
        "planned_writes": planned_writes,
        "handoff_candidates": handoff_candidates,
        "skipped_writes": skipped_writes,
        "human_gate_required": bool(planned_writes),
        "rollback": [
            {
                "kind": "git_commit_msg_hook",
                "command": (
                    f"python3 {(resolved_ldvh_root / 'code/governed_hook_adapter.py').as_posix()} uninstall "
                    f"--repo {project['path']} --governance-root {resolved_governance_root.as_posix()} "
                    f"--ldvh-root {resolved_ldvh_root.as_posix()} --confirm-human-gate"
                ),
                "project_id": project["id"],
            }
            for project in check["target_projects"]
            if strategy == "plugin_hook"
        ],
        "verification": {
            "command": (
                f"python3 {(resolved_ldvh_root / 'code/install_verification.py').as_posix()} "
                f"--governance-root {resolved_governance_root.as_posix()} "
                f"--ldvh-root {resolved_ldvh_root.as_posix()} --repo {resolved_repo.as_posix()}"
            ),
            "expected": "summary.status is complete or review_required with explicit Human handoff",
            "unverifiable": [
                "environment integrated requires真实自动触发、payload、失败处理、trust 和重启后证据"
            ],
        },
        "source_refs": check["source_refs"],
    }
    return {
        "metadata": {**check["metadata"], "command": "plan"},
        "summary": check["summary"],
        "install_plan": plan,
        "diagnostics": check["diagnostics"],
        "source_refs": check["source_refs"],
    }


def build_install_apply(
    *,
    governance_root: Path,
    ldvh_root: Path = ROOT,
    repo: Path,
    codex_home: Path | None = None,
    environment_name: str = "Codex",
    environment_strategy: str = "",
    confirm_human_gate: bool = False,
) -> dict[str, Any]:
    plan = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ldvh_root,
        repo=repo,
        codex_home=codex_home,
        environment_name=environment_name,
        environment_strategy=environment_strategy,
    )
    if environment_strategy and not _strategy_is_valid(environment_strategy):
        unknown = _unknown_strategy_result(
            command="apply",
            governance_root=governance_root,
            ldvh_root=ldvh_root,
            repo=repo,
            environment_name=environment_name,
            environment_strategy=environment_strategy,
        )
        return {**unknown, "install_plan": {}, "apply_results": [], "verification": {}}
    diagnostics = list(plan["diagnostics"])
    if plan["summary"]["blocking"]:
        return {
            "metadata": {**plan["metadata"], "command": "apply", "human_gate_confirmed": confirm_human_gate},
            "summary": {"status": "blocked", "blocking": plan["summary"]["blocking"], "diagnostics": len(diagnostics)},
            "install_plan": plan["install_plan"],
            "apply_results": [],
            "verification": {},
            "diagnostics": diagnostics,
            "source_refs": plan["source_refs"],
        }
    if not confirm_human_gate:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "INSTALL_WIZARD_HUMAN_GATE_REQUIRED",
                repo.resolve().as_posix(),
                "执行 apply 前必须显式提供 --confirm-human-gate。",
            )
        )
        return {
            "metadata": {**plan["metadata"], "command": "apply", "human_gate_confirmed": False},
            "summary": {"status": "blocked", "blocking": 1, "diagnostics": len(diagnostics)},
            "install_plan": plan["install_plan"],
            "apply_results": [],
            "verification": {},
            "diagnostics": diagnostics,
            "source_refs": plan["source_refs"],
        }

    strategy = plan["install_plan"]["environment_strategy"]
    if strategy != "plugin_hook":
        diagnostics.append(
            _diagnostic(
                "blocking",
                "INSTALL_WIZARD_STRATEGY_APPLY_NOT_IMPLEMENTED",
                strategy,
                "install_wizard v1 不自动写入薄引用或 manual entrypoint；请按 plan 交还 Human 处理。",
            )
        )
        return {
            "metadata": {**plan["metadata"], "command": "apply", "human_gate_confirmed": True},
            "summary": {"status": "blocked", "blocking": 1, "diagnostics": len(diagnostics)},
            "install_plan": plan["install_plan"],
            "apply_results": [],
            "verification": {},
            "diagnostics": diagnostics,
            "source_refs": plan["source_refs"],
        }

    apply_results = [
        build_governed_hook_adapter(
            command="install",
            repo=Path(project["path"]),
            governance_root=governance_root,
            ldvh_root=ldvh_root,
            confirm_human_gate=True,
        )
        for project in plan["install_plan"]["target_projects"]
    ]
    for result in apply_results:
        diagnostics.extend(result.get("diagnostics", []))
    verification = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ldvh_root,
        repo=repo,
        codex_home=codex_home,
        environment_name=environment_name,
    )
    for diagnostic in verification.get("diagnostics", []):
        if diagnostic["level"] in {"blocking", "error"}:
            diagnostics.append(diagnostic)
    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    status = "blocked" if blocking else "ok"
    return {
        "metadata": {**plan["metadata"], "command": "apply", "human_gate_confirmed": True},
        "summary": {
            "status": status,
            "blocking": blocking,
            "diagnostics": len(diagnostics),
            "verification_status": verification["summary"]["status"],
        },
        "install_plan": plan["install_plan"],
        "apply_results": apply_results,
        "verification": verification,
        "diagnostics": diagnostics,
        "source_refs": plan["source_refs"],
    }


def build_install_verify(
    *,
    governance_root: Path,
    ldvh_root: Path = ROOT,
    repo: Path,
    codex_home: Path | None = None,
    environment_name: str = "Codex",
) -> dict[str, Any]:
    verification = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ldvh_root,
        repo=repo,
        codex_home=codex_home,
        environment_name=environment_name,
    )
    return {
        "metadata": {
            "read_only": True,
            "authority": "install_wizard",
            "authorization": "none",
            "command": "verify",
        },
        "summary": verification["summary"],
        "verification": verification,
        "diagnostics": verification["diagnostics"],
        "source_refs": verification["source_refs"],
    }


def _print_text(result: dict[str, Any]) -> None:
    summary = result.get("summary", {})
    print("LDVH v3 install wizard")
    print(f"- command: {result.get('metadata', {}).get('command')}")
    print(f"- status: {summary.get('status')}")
    print(f"- blocking: {summary.get('blocking', 0)}")
    if "environment_strategy" in summary:
        print(f"- environment_strategy: {summary['environment_strategy']}")
    plan = result.get("install_plan")
    if plan:
        print(f"- planned_writes: {len(plan.get('planned_writes', []))}")
        print(f"- handoff_candidates: {len(plan.get('handoff_candidates', []))}")
        print(f"- skipped_writes: {len(plan.get('skipped_writes', []))}")
        print(f"- human_gate_required: {plan.get('human_gate_required')}")
    if result.get("diagnostics"):
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LDVH v3 install/config wizard facade.")
    parser.add_argument("command", choices=["check", "plan", "apply", "verify"])
    parser.add_argument("--governance-root", default=ROOT.as_posix(), help="workspace root containing LDVH-GOVERNED-PROJECTS.yaml")
    parser.add_argument("--ldvh-root", default=ROOT.as_posix(), help="LDVH root")
    parser.add_argument("--repo", default=ROOT.as_posix(), help="target governed project repository")
    parser.add_argument("--codex-home", default="", help="Codex home for environment plugin audit")
    parser.add_argument("--environment-name", default="Codex", help="target environment name")
    parser.add_argument("--environment-strategy", default="")
    parser.add_argument("--confirm-human-gate", action="store_true", help="required for apply")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    codex_home = Path(args.codex_home).resolve() if args.codex_home else None
    common = {
        "governance_root": Path(args.governance_root),
        "ldvh_root": Path(args.ldvh_root),
        "repo": Path(args.repo),
        "codex_home": codex_home,
        "environment_name": args.environment_name,
    }
    if args.command == "check":
        result = build_install_check(**common, environment_strategy=args.environment_strategy)
    elif args.command == "plan":
        result = build_install_plan(**common, environment_strategy=args.environment_strategy)
    elif args.command == "apply":
        result = build_install_apply(
            **common,
            environment_strategy=args.environment_strategy,
            confirm_human_gate=args.confirm_human_gate,
        )
    else:
        result = build_install_verify(**common)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result.get("summary", {}).get("blocking") else 0


if __name__ == "__main__":
    raise SystemExit(main())
