from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from install_git_hooks import HookStatus, inspect_status, install, uninstall
from ldvh_specs import (
    GOVERNED_PROJECTS_CONFIG_PATH,
    ROOT,
    find_governed_projects_config,
    parse_governed_projects_config,
    resolve_governed_subject,
    validate_governed_projects_config,
)


AUTHORIZATION = "human_gate_required_for_write"
VERIFY_VALID_MESSAGE = "docs(docs): 验证ldvh hook\n"
VERIFY_INVALID_MESSAGE = "invalid header\n"


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


def _output_field(text: str, field: str) -> str:
    prefix = f"{field}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def _excerpt(text: str, limit: int = 1200) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _run_hook_verification_case(
    *,
    repo: Path,
    active_hook: Path,
    case_id: str,
    message: str,
    expect_blocking: bool,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ldvh-hook-verify-") as tmp:
        env = dict(os.environ)
        env["GIT_INDEX_FILE"] = (Path(tmp) / "index").as_posix()
        read_tree = subprocess.run(
            ["git", "read-tree", "HEAD"],
            cwd=repo,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        if read_tree.returncode != 0:
            subprocess.run(
                ["git", "read-tree", "--empty"],
                cwd=repo,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
            )
        message_file = Path(tmp) / f"{case_id}-message.txt"
        message_file.write_text(message, encoding="utf-8")
        completed = subprocess.run(
            [active_hook.as_posix(), message_file.as_posix()],
            cwd=repo,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )

    combined = completed.stdout + completed.stderr
    passed = completed.returncode != 0 if expect_blocking else completed.returncode == 0
    return {
        "case": case_id,
        "expect_blocking": expect_blocking,
        "passed": passed,
        "exit_code": completed.returncode,
        "validator_status": _output_field(completed.stdout, "status"),
        "blocking_code_found": "COMMIT_HEADER_INVALID" in combined,
        "stdout_excerpt": _excerpt(completed.stdout),
        "stderr_excerpt": _excerpt(completed.stderr),
    }


def _verify_commit_msg_hook(repo: Path, governance_root: Path, ldvh_root: Path, status: HookStatus) -> dict[str, Any]:
    diagnostics: list[dict[str, str]] = []
    if not status.installed:
        diagnostics.append(_diagnostic(
            "blocking",
            "GOVERNED_HOOK_VERIFY_NOT_INSTALLED",
            repo.as_posix(),
            "未检测到可执行且带 V3 managed marker 的 active commit-msg Hook。",
        ))
        return {
            "status": "blocked",
            "positive_case": {},
            "negative_case": {},
            "rollback_command": "",
            "diagnostics": diagnostics,
            "blocking": 1,
        }

    positive = _run_hook_verification_case(
        repo=repo,
        active_hook=status.active_hook,
        case_id="valid_commit_message",
        message=VERIFY_VALID_MESSAGE,
        expect_blocking=False,
    )
    negative = _run_hook_verification_case(
        repo=repo,
        active_hook=status.active_hook,
        case_id="invalid_commit_message",
        message=VERIFY_INVALID_MESSAGE,
        expect_blocking=True,
    )

    if not positive["passed"]:
        diagnostics.append(_diagnostic(
            "blocking",
            "GOVERNED_HOOK_VERIFY_POSITIVE_FAILED",
            status.active_hook.as_posix(),
            "有效 commit message 未被 active commit-msg Hook 放行。",
        ))
    if not negative["passed"] or not negative["blocking_code_found"]:
        diagnostics.append(_diagnostic(
            "blocking",
            "GOVERNED_HOOK_VERIFY_NEGATIVE_FAILED",
            status.active_hook.as_posix(),
            "无效 commit message 未被 active commit-msg Hook 阻断，或未返回 COMMIT_HEADER_INVALID 证据。",
        ))

    blocking = sum(1 for item in diagnostics if item["level"] in {"blocking", "error"})
    return {
        "status": "blocked" if blocking else "ok",
        "positive_case": positive,
        "negative_case": negative,
        "rollback_command": (
            "python3 "
            f"{(ldvh_root / 'code/governed_hook_adapter.py').as_posix()} uninstall "
            f"--repo {repo.as_posix()} --governance-root {governance_root.as_posix()} "
            f"--ldvh-root {ldvh_root.as_posix()} --confirm-human-gate"
        ),
        "diagnostics": diagnostics,
        "blocking": blocking,
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
    hook_status_object: HookStatus | None = None
    if not any(item["level"] in {"blocking", "error"} for item in diagnostics):
        try:
            if command == "install":
                hook_status_object = install(resolved_repo, resolved_ldvh_root, embed_ldvh_root=True)
            elif command == "uninstall":
                hook_status_object = uninstall(resolved_repo, resolved_ldvh_root)
            else:
                hook_status_object = inspect_status(resolved_repo, resolved_ldvh_root)
            hook_status = _hook_status_dict(hook_status_object)
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

    verification: dict[str, Any] = {}
    if command == "verify" and hook_status_object is not None and not any(
        item["level"] in {"blocking", "error"} for item in diagnostics
    ):
        verification = _verify_commit_msg_hook(
            resolved_repo,
            resolved_governance_root,
            resolved_ldvh_root,
            hook_status_object,
        )
        diagnostics.extend(verification["diagnostics"])

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
            "authorization": AUTHORIZATION if write_command else "none",
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
            "scope_status": resolution.get("scope_status", ""),
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
        "verification": verification,
        "source_refs": [
            {"path": "specs/10-安装与配置规范.md", "role": "governed_project_config_boundary"},
            {"path": "specs/01-保障与衔接.md", "role": "environment_adapter_boundary"},
            {"path": "code/install_git_hooks.py", "role": "hook_install_backend"},
        ],
        "diagnostics": diagnostics,
    }


def _resolve_config_project_path(project: dict[str, Any], config_path: Path | None, fallback_root: Path) -> Path | None:
    raw_path = project.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    project_path = Path(raw_path).expanduser()
    if project_path.is_absolute():
        return project_path.resolve()
    base = config_path.parent if config_path is not None else fallback_root
    return (base / project_path).resolve()


def build_governed_hook_verify_all(
    *,
    governance_root: Path = ROOT,
    ldvh_root: Path = ROOT,
) -> dict[str, Any]:
    resolved_governance_root = governance_root.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    config_path = find_governed_projects_config(
        resolved_governance_root,
        resolved_governance_root,
        [resolved_governance_root],
    )
    diagnostics = [
        diagnostic.to_dict()
        for diagnostic in validate_governed_projects_config(resolved_governance_root, config_path)
    ]
    config = parse_governed_projects_config(resolved_governance_root, config_path)
    project_results: list[dict[str, Any]] = []

    for project in config["projects"]:
        if not isinstance(project, dict):
            continue
        project_path = _resolve_config_project_path(project, config_path, resolved_governance_root)
        if project_path is None:
            continue
        project_results.append(build_governed_hook_adapter(
            command="verify",
            repo=project_path,
            governance_root=resolved_governance_root,
            ldvh_root=resolved_ldvh_root,
        ))

    blocking = sum(1 for item in diagnostics if item["level"] in {"blocking", "error"})
    blocking += sum(result["summary"]["blocking"] for result in project_results)
    verified = sum(1 for result in project_results if result["summary"]["status"] == "ok")
    return {
        "metadata": {
            "authority": "governed_project_hook_adapter",
            "authorization": "none",
            "command": "verify",
            "all_projects": True,
            "ldvh_root": resolved_ldvh_root.as_posix(),
            "governance_root": resolved_governance_root.as_posix(),
            "config_path": config_path.as_posix() if config_path else "",
            "read_only": True,
        },
        "summary": {
            "status": "blocked" if blocking else "ok",
            "command": "verify",
            "projects": len(project_results),
            "verified": verified,
            "blocking": blocking,
            "diagnostics": len(diagnostics) + sum(len(result["diagnostics"]) for result in project_results),
        },
        "config": {
            "path": config_path.as_posix() if config_path else GOVERNED_PROJECTS_CONFIG_PATH,
            "projects": len(config["projects"]),
        },
        "projects": project_results,
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
    if result["metadata"]["command"] == "verify" and result.get("verification"):
        verification = result["verification"]
        positive = verification.get("positive_case", {})
        negative = verification.get("negative_case", {})
        print(f"- verify_status: {verification['status']}")
        print(f"- positive_case: {'passed' if positive.get('passed') else 'failed'} exit={positive.get('exit_code')}")
        print(f"- negative_case: {'passed' if negative.get('passed') else 'failed'} exit={negative.get('exit_code')}")
    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")


def _print_verify_all_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 governed hook verification")
    print(f"- status: {summary['status']}")
    print(f"- projects: {summary['projects']}")
    print(f"- verified: {summary['verified']}")
    print(f"- blocking: {summary['blocking']}")
    print("")
    for project in result["projects"]:
        project_summary = project["summary"]
        verification = project.get("verification", {})
        positive = verification.get("positive_case", {})
        negative = verification.get("negative_case", {})
        print(f"- {project_summary['governed_project_id'] or project['metadata']['repo']}")
        print(f"  status: {project_summary['status']}")
        print(f"  hook_installed: {project_summary['hook_installed']}")
        print(f"  positive_case: {'passed' if positive.get('passed') else 'failed'} exit={positive.get('exit_code')}")
        print(f"  negative_case: {'passed' if negative.get('passed') else 'failed'} exit={negative.get('exit_code')}")
    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install or inspect LDVH v3 commit-msg hooks for governed projects.")
    parser.add_argument("command", choices=["status", "install", "uninstall", "verify"])
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
    parser.add_argument("--all-projects", action="store_true", help="verify every project in LDVH-GOVERNED-PROJECTS.yaml")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.all_projects:
        if args.command != "verify":
            raise SystemExit("--all-projects is only supported by verify")
        result = build_governed_hook_verify_all(
            governance_root=Path(args.governance_root),
            ldvh_root=Path(args.ldvh_root),
        )
    else:
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
    elif args.all_projects:
        _print_verify_all_text(result)
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
