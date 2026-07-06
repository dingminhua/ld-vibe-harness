from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from install_git_hooks import inspect_status
from ldvh_specs import ROOT


SWITCH_MODE = "commit_msg_hard_switch_minimal"
AUTHORIZATION = "none"

def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _diagnostic(level: str, code: str, path: str, message: str, disposition: str = "blocking") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "path": path,
        "message": message,
        "disposition": disposition,
    }


def _entrypoint(
    *,
    entry_id: str,
    mode: str,
    available: bool,
    integrated: bool,
    path: Path,
    purpose: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": entry_id,
        "mode": mode,
        "available": available,
        "integrated": integrated,
        "path": path.as_posix(),
        "purpose": purpose,
        "details": details or {},
    }


def build_environment_status(repo: Path = ROOT, ldvh_root: Path = ROOT) -> dict[str, Any]:
    resolved_ldvh_root = ldvh_root.resolve()
    diagnostics: list[dict[str, str]] = []

    try:
        hook_status = inspect_status(repo.resolve(), resolved_ldvh_root)
        hook_details = {
            "repo": hook_status.repo.as_posix(),
            "core_hooks_path": hook_status.hooks_path,
            "active_hook": hook_status.active_hook.as_posix(),
            "active_hook_exists": hook_status.active_hook_exists,
            "active_hook_executable": hook_status.active_hook_executable,
            "active_hook_managed": hook_status.active_hook_managed,
            "common_hook": hook_status.common_hook.as_posix(),
            "common_hook_exists": hook_status.common_hook_exists,
            "installed": hook_status.installed,
        }
        repo_root = hook_status.repo
        active_hook = hook_status.active_hook
        commit_hook_integrated = hook_status.installed
        commit_hook_available = hook_status.active_hook_exists
    except Exception as exc:  # pragma: no cover - exercised through CLI failure shape when git is unavailable.
        repo_root = repo.resolve()
        active_hook = repo_root / "hooks" / "commit-msg"
        hook_details = {"error": str(exc)}
        commit_hook_integrated = False
        commit_hook_available = active_hook.is_file()
        diagnostics.append(
            _diagnostic(
                "blocking",
                "ENV_GIT_HOOK_STATUS_UNAVAILABLE",
                repo_root.as_posix(),
                f"无法读取目标 repo 的 Git Hook 状态: {exc}",
            )
        )

    if not commit_hook_integrated:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "ENV_COMMIT_MSG_HOOK_NOT_INSTALLED",
                active_hook.as_posix(),
                "当前最小 hard switch 期望 git.commit-msg 自动入口已启用，但目标 repo 未安装 V3 managed commit-msg hook。",
            )
        )

    entrypoints = [
        _entrypoint(
            entry_id="git.commit-msg",
            mode="automated_hook",
            available=commit_hook_available,
            integrated=commit_hook_integrated,
            path=active_hook,
            purpose="real Git commit message validation",
            details=hook_details,
        ),
    ]

    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    automated_entrypoints = [entry["id"] for entry in entrypoints if entry["integrated"]]

    return {
        "metadata": {
            "read_only": True,
            "authority": "environment_integration_status",
            "authorization": AUTHORIZATION,
            "root": resolved_ldvh_root.as_posix(),
            "repo": repo_root.as_posix(),
        },
        "summary": {
            "status": "blocked" if blocking else "ok",
            "switch_mode": SWITCH_MODE,
            "environment_integrated": "partial" if commit_hook_integrated else "false",
            "hook_integrated": "git.commit-msg" if commit_hook_integrated else "none",
            "runtime_adapter_integrated": False,
            "session_start_integrated": False,
            "acknowledge_read_plan_integrated": False,
            "pre_tool_use_integrated": False,
            "completion_claim_integrated": False,
            "automated_entrypoints": automated_entrypoints,
            "diagnostics": len(diagnostics),
            "blocking": blocking,
            "authorization": AUTHORIZATION,
        },
        "entrypoints": entrypoints,
        "unresolved_boundaries": [
            "session_start has no integrated AI lifecycle Hook trigger",
            "acknowledge_read_plan is a runtime receipt bridge, not persistent environment state",
            "pre_tool_use has no integrated AI lifecycle tool-call trigger",
            "completion_claim has no integrated AI lifecycle completion trigger",
            "runtime_adapter requires a verified environment Hook, plugin, extension package, or adapter",
            "generic Web writes and non-commit action templates are not enabled",
            "Rules and Skill top-level mechanisms are removed, not pending entrypoints",
        ],
        "diagnostics": diagnostics,
    }


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 environment status")
    print(f"- status: {summary['status']}")
    print(f"- switch_mode: {summary['switch_mode']}")
    print(f"- environment_integrated: {summary['environment_integrated']}")
    print(f"- hook_integrated: {summary['hook_integrated']}")
    print(f"- automated_entrypoints: {', '.join(summary['automated_entrypoints']) or 'none'}")

    print("\nEntrypoints:")
    for entry in result["entrypoints"]:
        print(
            f"- {entry['id']}: mode={entry['mode']}, "
            f"available={_bool_text(entry['available'])}, integrated={_bool_text(entry['integrated'])}"
        )

    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")

    print("\nUnresolved boundaries:")
    for item in result["unresolved_boundaries"]:
        print(f"- {item}")
    print("\nAuthorization: none")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect LDVH v3 environment integration status.")
    parser.add_argument("--repo", default=ROOT.as_posix(), help="target repository root")
    parser.add_argument("--ldvh-root", default=ROOT.as_posix(), help="LDVH v3 root containing code/ and hooks/")
    parser.add_argument("--backend-allow-external", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_environment_status(Path(args.repo), Path(args.ldvh_root))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
