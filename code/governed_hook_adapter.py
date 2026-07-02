from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

from install_git_hooks import HookStatus, inspect_status, install, uninstall
from ldvh_specs import ROOT, resolve_governed_subject, validate_governed_projects_config


AUTHORIZATION = "human_gate_required_for_write"


def _diagnostic(level: str, code: str, path: str, message: str, disposition: str = "blocking") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "path": path,
        "message": message,
        "disposition": disposition,
    }


def _hook_status_dict(status: HookStatus) -> dict[str, Any]:
    return {
        "repo": status.repo.as_posix(),
        "core_hooks_path": status.hooks_path,
        "active_hook": status.active_hook.as_posix(),
        "active_hook_exists": status.active_hook_exists,
        "active_hook_executable": status.active_hook_executable,
        "active_hook_managed": status.active_hook_managed,
        "common_hook": status.common_hook.as_posix(),
        "common_hook_exists": status.common_hook_exists,
        "installed": status.installed,
    }


def _target_paths(repo: Path, target_paths: list[str] | None) -> list[Path]:
    if target_paths:
        return [Path(path) for path in target_paths if path.strip()]
    return [repo]


def _is_git_worktree(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "-C", path.as_posix(), "rev-parse", "--is-inside-work-tree"],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def build_governed_hook_adapter(
    *,
    command: str,
    repo: Path,
    governance_root: Path = ROOT,
    ldvh_root: Path = ROOT,
    target_paths: list[str] | None = None,
    confirm_human_gate: bool = False,
) -> dict[str, Any]:
    resolved_repo = repo.resolve()
    resolved_governance_root = governance_root.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    effective_targets = _target_paths(resolved_repo, target_paths)
    repo_is_git_worktree = _is_git_worktree(resolved_repo)
    resolution = resolve_governed_subject(
        resolved_governance_root,
        cwd=resolved_repo,
        target_paths=effective_targets,
        read_write_kind="commit",
    )
    diagnostics: list[dict[str, str]] = [
        diagnostic.to_dict() for diagnostic in validate_governed_projects_config(resolved_governance_root)
    ]

    if resolution["blocked"]:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "GOVERNED_HOOK_TARGET_BLOCKED",
                ",".join(resolution["target_paths"]),
                resolution["message"] or "管辖项目 target 解析被阻断。",
            )
        )
    elif not resolution["governed"]:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "GOVERNED_HOOK_TARGET_NOT_GOVERNED",
                ",".join(resolution["target_paths"]),
                "目标 repo 未命中 LDVH 管辖项目；adapter 不安装或卸载 Hook。",
            )
        )
    elif not repo_is_git_worktree:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "GOVERNED_HOOK_TARGET_NOT_GIT_REPO",
                resolved_repo.as_posix(),
                "管辖项目必须是 Git 仓库；当前目标不是有效 Git worktree，停止安装 Git Hook。",
            )
        )

    write_command = command in {"install", "uninstall"}
    if write_command and not confirm_human_gate:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "GOVERNED_HOOK_HUMAN_GATE_REQUIRED",
                resolved_repo.as_posix(),
                "安装或回滚外部管辖项目 Hook 前必须显式提供 Human Gate 确认。",
            )
        )

    hook_status: dict[str, Any] = {}
    if not any(item["level"] in {"blocking", "error"} for item in diagnostics):
        try:
            if command == "install":
                status = install(resolved_repo, resolved_ldvh_root, embed_ldvh_root=True)
            elif command == "uninstall":
                status = uninstall(resolved_repo, resolved_ldvh_root)
            else:
                status = inspect_status(resolved_repo, resolved_ldvh_root)
            hook_status = _hook_status_dict(status)
        except Exception as exc:
            diagnostics.append(
                _diagnostic(
                    "blocking",
                    "GOVERNED_HOOK_OPERATION_FAILED",
                    resolved_repo.as_posix(),
                    f"Hook {command} 操作失败: {exc}",
                )
            )
    else:
        if repo_is_git_worktree:
            try:
                hook_status = _hook_status_dict(inspect_status(resolved_repo, resolved_ldvh_root))
            except Exception as exc:
                hook_status = {"error": str(exc), "installed": False}
        else:
            hook_status = {
                "repo": resolved_repo.as_posix(),
                "installed": False,
                "error": "not_a_git_worktree",
            }

    blocking = sum(1 for item in diagnostics if item["level"] in {"blocking", "error"})
    installed = bool(hook_status.get("installed"))
    status = "blocked" if blocking else "ok"
    if command == "install" and status == "ok" and not installed:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "GOVERNED_HOOK_INSTALL_NOT_VERIFIED",
                resolved_repo.as_posix(),
                "安装命令完成后未能验证 V3 managed commit-msg Hook 已接入。",
            )
        )
        blocking += 1
        status = "blocked"
    if command == "uninstall" and status == "ok" and installed:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "GOVERNED_HOOK_UNINSTALL_NOT_VERIFIED",
                resolved_repo.as_posix(),
                "回滚命令完成后仍检测到 V3 managed commit-msg Hook 已接入。",
            )
        )
        blocking += 1
        status = "blocked"

    return {
        "metadata": {
            "authority": "governed_project_hook_adapter",
            "authorization": AUTHORIZATION,
            "command": command,
            "repo": resolved_repo.as_posix(),
            "ldvh_root": resolved_ldvh_root.as_posix(),
            "governance_root": resolved_governance_root.as_posix(),
            "human_gate_confirmed": confirm_human_gate,
        },
        "summary": {
            "status": status,
            "command": command,
            "governed": bool(resolution["governed"]),
            "governed_project_id": resolution["governed_project_id"],
            "governed_via": resolution["governed_via"],
            "hook_installed": installed,
            "hook_integrated": "git.commit-msg" if installed else "none",
            "environment_integrated": "partial" if installed else "false",
            "diagnostics": len(diagnostics),
            "blocking": blocking,
        },
        "governed_project": resolution,
        "hook_status": hook_status,
        "source_refs": [
            {"path": "specs/10-管辖项目配置规范.md", "role": "governed_project_config_boundary"},
            {"path": "specs/01-保障与衔接.md", "role": "environment_adapter_boundary"},
            {"path": "code/install_git_hooks.py", "role": "hook_install_backend"},
        ],
        "diagnostics": diagnostics,
    }


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 governed hook adapter")
    print(f"- status: {summary['status']}")
    print(f"- command: {summary['command']}")
    print(f"- governed: {summary['governed']}")
    print(f"- governed_project_id: {summary['governed_project_id'] or '<none>'}")
    print(f"- governed_via: {summary['governed_via'] or '<none>'}")
    print(f"- hook_installed: {summary['hook_installed']}")
    print(f"- hook_integrated: {summary['hook_integrated']}")
    print(f"- human_gate_confirmed: {result['metadata']['human_gate_confirmed']}")
    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install or inspect LDVH v3 commit-msg hooks for governed projects.")
    parser.add_argument("command", choices=["status", "install", "uninstall"])
    parser.add_argument("--repo", default=ROOT.as_posix(), help="target repository root")
    parser.add_argument(
        "--governance-root",
        default=ROOT.as_posix(),
        help="root containing LDVH-GOVERNED-PROJECTS.yaml",
    )
    parser.add_argument("--ldvh-root", default=ROOT.as_posix(), help="LDVH v3 root containing code/ and hooks/")
    parser.add_argument("--target-path", action="append", default=[], help="explicit target path for target-first resolution")
    parser.add_argument(
        "--confirm-human-gate",
        action="store_true",
        help="required for install/uninstall; records that Human Gate authorized the scope change",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_governed_hook_adapter(
        command=args.command,
        repo=Path(args.repo),
        governance_root=Path(args.governance_root),
        ldvh_root=Path(args.ldvh_root),
        target_paths=args.target_path,
        confirm_human_gate=args.confirm_human_gate,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
