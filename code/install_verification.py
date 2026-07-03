from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

from environment_entry_audit import build_environment_entry_audit
from governed_hook_adapter import build_governed_hook_adapter
from ldvh_specs import GOVERNED_PROJECTS_CONFIG_PATH, ROOT


AUTHORIZATION = "none"
CODEX_SHIM = "code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"


def _diagnostic(level: str, code: str, path: str, message: str, disposition: str = "blocking") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "path": path,
        "message": message,
        "disposition": disposition,
    }


def _find_config_root(start: Path) -> Path:
    resolved = start.resolve()
    candidates = [resolved, *resolved.parents]
    for candidate in candidates:
        if (candidate / GOVERNED_PROJECTS_CONFIG_PATH).is_file():
            return candidate
    return resolved


def _load_projects(config_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    config_path = config_root / GOVERNED_PROJECTS_CONFIG_PATH
    if not config_path.is_file():
        return [], [
            _diagnostic(
                "blocking",
                "INSTALL_VERIFY_GOVERNED_CONFIG_MISSING",
                config_path.as_posix(),
                "缺少管辖项目配置，无法验证管辖项目 Git Hook。",
            )
        ]
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [], [
            _diagnostic(
                "blocking",
                "INSTALL_VERIFY_GOVERNED_CONFIG_INVALID",
                config_path.as_posix(),
                f"管辖项目配置 YAML 解析失败: {exc}",
            )
        ]
    if not isinstance(data, dict) or not isinstance(data.get("projects"), list):
        return [], [
            _diagnostic(
                "blocking",
                "INSTALL_VERIFY_GOVERNED_PROJECTS_INVALID",
                config_path.as_posix(),
                "管辖项目配置必须包含 projects 列表。",
            )
        ]
    projects: list[dict[str, Any]] = []
    for index, project in enumerate(data["projects"], start=1):
        if not isinstance(project, dict):
            continue
        project_path = project.get("path")
        if not isinstance(project_path, str) or not project_path.strip():
            continue
        raw_path = Path(project_path).expanduser()
        resolved_path = raw_path if raw_path.is_absolute() else config_root / raw_path
        projects.append(
            {
                "index": index,
                "id": str(project.get("id") or f"project-{index}"),
                "name": str(project.get("name") or project.get("id") or f"project-{index}"),
                "path": resolved_path.resolve(),
            }
        )
    return projects, []


def _verify_git_hook(project: dict[str, Any], governance_root: Path, ldvh_root: Path) -> dict[str, Any]:
    repo = project["path"]
    adapter = build_governed_hook_adapter(
        command="verify",
        repo=repo,
        governance_root=governance_root,
        ldvh_root=ldvh_root,
    )
    hook_status = adapter.get("hook_status", {})
    diagnostics: list[dict[str, str]] = list(adapter.get("diagnostics", []))
    verification = adapter.get("verification", {})
    positive = verification.get("positive_case", {})
    negative = verification.get("negative_case", {})
    tests = {
        "positive_commit_message": {
            "status": "passed" if positive.get("passed") else "failed" if positive else "not_run",
            "returncode": positive.get("exit_code"),
            "expected": "exit 0",
            "stdout_excerpt": positive.get("stdout_excerpt", ""),
            "stderr_excerpt": positive.get("stderr_excerpt", ""),
        },
        "negative_commit_message": {
            "status": "passed" if negative.get("passed") else "failed" if negative else "not_run",
            "returncode": negative.get("exit_code"),
            "expected": "non-zero exit with COMMIT_HEADER_INVALID",
            "stdout_excerpt": negative.get("stdout_excerpt", ""),
            "stderr_excerpt": negative.get("stderr_excerpt", ""),
        },
    }

    if not hook_status.get("installed") and not any(
        diagnostic["code"] == "INSTALL_VERIFY_GIT_HOOK_NOT_READY" for diagnostic in diagnostics
    ):
        diagnostics.append(
            _diagnostic(
                "blocking",
                "INSTALL_VERIFY_GIT_HOOK_NOT_READY",
                repo.as_posix(),
                "Git Hook 未处于可验证 installed 状态，跳过正反例直接执行。",
            )
        )

    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    return {
        "project": {
            "index": project["index"],
            "id": project["id"],
            "name": project["name"],
            "path": repo.as_posix(),
        },
        "summary": {
            "status": "blocked" if blocking else "ok",
            "hook_installed": bool(hook_status.get("installed")),
            "hook_integrated": adapter["summary"].get("hook_integrated", "none"),
            "managed_hook": bool(hook_status.get("active_hook_managed")),
            "active_hook_executable": bool(hook_status.get("active_hook_executable")),
            "positive_passed": tests["positive_commit_message"]["status"] == "passed",
            "negative_blocked": tests["negative_commit_message"]["status"] == "passed",
            "blocking": blocking,
        },
        "adapter": adapter,
        "tests": tests,
        "diagnostics": diagnostics,
    }


def _run_shim(ldvh_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    shim = ldvh_root / CODEX_SHIM
    if not shim.is_file():
        return {
            "status": "not_run",
            "returncode": None,
            "diagnostics": [
                _diagnostic(
                    "blocking",
                    "INSTALL_VERIFY_CODEX_SHIM_MISSING",
                    shim.as_posix(),
                    "缺少 Codex 环境插件 shim，无法运行 repo-local 直测。",
                )
            ],
        }
    env = dict(os.environ)
    env["LDVH_ROOT"] = ldvh_root.as_posix()
    completed = subprocess.run(
        [sys.executable, shim.as_posix()],
        cwd=ldvh_root,
        env=env,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    parsed: Any = {}
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = {}
    return {
        "status": "completed",
        "returncode": completed.returncode,
        "stdout_excerpt": completed.stdout[:1000],
        "stderr_excerpt": completed.stderr[:1000],
        "payload": parsed,
        "diagnostics": [],
    }


def _verify_environment(ldvh_root: Path, repo: Path, codex_home: Path | None, environment_name: str) -> dict[str, Any]:
    audit = build_environment_entry_audit(repo=repo, ldvh_root=ldvh_root, codex_home=codex_home)
    candidates = {candidate["id"]: candidate for candidate in audit["candidates"]}
    codex_plugin = candidates.get("codex.ldvh-plugin", {})
    diagnostics: list[dict[str, str]] = []

    session = _run_shim(
        ldvh_root,
        {
            "hook_event_name": "SessionStart",
            "sessionId": "install-verify-session",
            "cwd": repo.as_posix(),
            "prompt": "验证 LDVH 安装入口",
            "targetPath": "README.md",
        },
    )
    pretool = _run_shim(
        ldvh_root,
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "install-verify-pretool",
            "cwd": repo.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "README.md"},
        },
    )
    stop = _run_shim(
        ldvh_root,
        {
            "hook_event_name": "Stop",
            "sessionId": "install-verify-stop",
            "cwd": repo.as_posix(),
            "targetPath": "README.md",
        },
    )
    for result in (session, pretool, stop):
        diagnostics.extend(result.get("diagnostics", []))

    session_payload = session.get("payload") if isinstance(session.get("payload"), dict) else {}
    pretool_payload = pretool.get("payload") if isinstance(pretool.get("payload"), dict) else {}
    stop_payload = stop.get("payload") if isinstance(stop.get("payload"), dict) else {}
    shim_tests = {
        "session_start_direct": {
            "status": "passed"
            if session.get("returncode") == 0 and session_payload.get("summary", {}).get("event") == "session_start"
            else "failed",
            "returncode": session.get("returncode"),
        },
        "pre_tool_use_direct_block": {
            "status": "passed"
            if pretool.get("returncode") != 0 and pretool_payload.get("summary", {}).get("event") == "pre_tool_use"
            else "failed",
            "returncode": pretool.get("returncode"),
        },
        "completion_claim_direct_degrade": {
            "status": "passed"
            if stop.get("returncode") == 0 and stop_payload.get("summary", {}).get("event") == "completion_claim"
            else "failed",
            "returncode": stop.get("returncode"),
        },
    }
    if any(item["status"] != "passed" for item in shim_tests.values()):
        diagnostics.append(
            _diagnostic(
                "blocking",
                "INSTALL_VERIFY_ENVIRONMENT_SHIM_DIRECT_TEST_FAILED",
                CODEX_SHIM,
                "环境插件 repo-local shim 正反测未全部通过。",
            )
        )

    environment_integrated = bool(audit["summary"].get("codex_environment_entry_integrated"))
    codex_plugin_integrated = bool(audit["summary"].get("codex_plugin_entry_integrated"))
    human_acceptance_required = not environment_integrated
    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    status = "blocked" if blocking else "ok" if environment_integrated else "review_required"

    return {
        "summary": {
            "status": status,
            "environment_name": environment_name,
            "environment_integrated": environment_integrated,
            "plugin_integrated": codex_plugin_integrated,
            "plugin_status": codex_plugin.get("status", "unknown"),
            "plugin_decision": codex_plugin.get("decision", "unknown"),
            "human_acceptance_required": human_acceptance_required,
            "blocking": blocking,
        },
        "audit": audit,
        "shim_direct_tests": shim_tests,
        "human_acceptance": {
            "required": human_acceptance_required,
            "reason": "真实 lifecycle、授权 / trust、payload、失败处理或卸载后自动触发状态尚未由当前回合证明。"
            if human_acceptance_required
            else "",
            "steps": [
                f"在 {environment_name} 插件 / 扩展页面确认 LDVH 插件已安装、启用且 trusted。",
                f"新开一个 {environment_name} 窗口或会话，确认 SessionStart 能看到 LDVH 提示或诊断输出。",
                "触发一次受控写入类工具，确认 PreToolUse 负例会阻断，正例会放行。",
                "若卸载或禁用插件，重新打开窗口确认不再自动触发 LDVH。",
                "失败时返回插件页面状态、错误文本、截图或本命令 JSON 输出。",
            ],
        },
        "diagnostics": diagnostics,
    }


def build_install_verification(
    *,
    governance_root: Path,
    ldvh_root: Path,
    repo: Path,
    codex_home: Path | None = None,
    environment_name: str = "Codex",
    require_environment_integrated: bool = False,
) -> dict[str, Any]:
    resolved_governance_root = governance_root.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    resolved_repo = repo.resolve()
    projects, config_diagnostics = _load_projects(resolved_governance_root)
    git_results = [
        _verify_git_hook(project, resolved_governance_root, resolved_ldvh_root)
        for project in projects
    ] if not config_diagnostics else []
    environment = _verify_environment(resolved_ldvh_root, resolved_repo, codex_home, environment_name)

    diagnostics: list[dict[str, str]] = list(config_diagnostics)
    for result in git_results:
        diagnostics.extend(result["diagnostics"])
    diagnostics.extend(environment["diagnostics"])

    if require_environment_integrated and not environment["summary"]["environment_integrated"]:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "INSTALL_VERIFY_ENVIRONMENT_NOT_INTEGRATED",
                environment_name,
                "要求环境 Hook integrated，但当前仍缺真实触发、授权或失败处理证据。",
            )
        )

    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    git_ok = bool(git_results) and all(result["summary"]["status"] == "ok" for result in git_results)
    environment_ok = environment["summary"]["environment_integrated"]
    install_complete = git_ok and environment_ok and blocking == 0
    return {
        "metadata": {
            "read_only": True,
            "authority": "install_verification",
            "authorization": AUTHORIZATION,
            "governance_root": resolved_governance_root.as_posix(),
            "ldvh_root": resolved_ldvh_root.as_posix(),
            "repo": resolved_repo.as_posix(),
            "environment_name": environment_name,
        },
        "summary": {
            "status": "blocked" if blocking else "complete" if install_complete else "review_required",
            "install_complete": install_complete,
            "projects": len(projects),
            "git_hooks_ok": git_ok,
            "environment_hook_integrated": environment_ok,
            "environment_human_acceptance_required": environment["summary"]["human_acceptance_required"],
            "blocking": blocking,
            "diagnostics": len(diagnostics),
        },
        "git_hooks": git_results,
        "environment": environment,
        "diagnostics": diagnostics,
        "source_refs": [
            {"path": "specs/30-LDVH安装初始化管辖项目配置行动模板.md", "role": "install_handoff_contract"},
            {"path": "code/governed_hook_adapter.py", "role": "git_hook_status_backend"},
            {"path": "code/environment_entry_audit.py", "role": "environment_hook_audit"},
            {"path": "code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py", "role": "environment_shim_direct_test"},
        ],
    }


def _mark(value: bool) -> str:
    return "✅" if value else "⛔"


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 installation verification")
    print(f"- status: {summary['status']}")
    print(f"- install_complete: {summary['install_complete']}")
    print(f"- git_hooks_ok: {summary['git_hooks_ok']}")
    print(f"- environment_hook_integrated: {summary['environment_hook_integrated']}")
    print(f"- environment_human_acceptance_required: {summary['environment_human_acceptance_required']}")
    print(f"- diagnostics: {summary['diagnostics']}")

    print("\nGit Hook tests:")
    for result_item in result["git_hooks"]:
        project = result_item["project"]
        item_summary = result_item["summary"]
        print(
            f"- {project['id']} ({project['path']}): "
            f"installed={item_summary['hook_installed']}, "
            f"managed={item_summary['managed_hook']}, "
            f"positive={_mark(item_summary['positive_passed'])}, "
            f"negative={_mark(item_summary['negative_blocked'])}"
        )

    env = result["environment"]
    env_summary = env["summary"]
    print("\nEnvironment Hook:")
    print(f"- environment_name: {env_summary['environment_name']}")
    print(f"- plugin_status: {env_summary['plugin_status']}")
    print(f"- plugin_decision: {env_summary['plugin_decision']}")
    print(f"- environment_integrated: {env_summary['environment_integrated']}")
    print("- shim_direct_tests:")
    for test_name, test_result in env["shim_direct_tests"].items():
        print(f"  - {test_name}: {test_result['status']} (returncode={test_result['returncode']})")

    if env["human_acceptance"]["required"]:
        print("\nHuman acceptance still required:")
        print(f"- reason: {env['human_acceptance']['reason']}")
        for step in env["human_acceptance"]["steps"]:
            print(f"- {step}")

    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")

    print("\nAuthorization: none")


def build_parser() -> argparse.ArgumentParser:
    default_config_root = _find_config_root(ROOT)
    parser = argparse.ArgumentParser(description="Verify LDVH installation handoff state without writing user environment.")
    parser.add_argument("--governance-root", default=default_config_root.as_posix(), help="root containing LDVH-GOVERNED-PROJECTS.yaml")
    parser.add_argument("--ldvh-root", default=ROOT.as_posix(), help="LDVH v3 root")
    parser.add_argument("--repo", default=ROOT.as_posix(), help="repo used for environment entry audit")
    parser.add_argument("--codex-home", default="", help="Codex home for read-only plugin audit")
    parser.add_argument("--environment-name", default="Codex", help="current AI environment name for Human-facing output")
    parser.add_argument("--require-environment-integrated", action="store_true", help="treat missing real environment integration as blocking")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_install_verification(
        governance_root=Path(args.governance_root),
        ldvh_root=Path(args.ldvh_root),
        repo=Path(args.repo),
        codex_home=Path(args.codex_home).resolve() if args.codex_home else None,
        environment_name=args.environment_name,
        require_environment_integrated=args.require_environment_integrated,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
