from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from environment_entry_audit import build_environment_entry_audit
from environment_lifecycle_acceptance import build_lifecycle_acceptance_status
from governed_hook_adapter import build_governed_hook_adapter
from ldvh_specs import (
    GOVERNED_PROJECTS_CONFIG_PATH,
    ROOT,
    parse_governed_projects_config,
    validate_governed_projects_config,
)


AUTHORIZATION = "none"
CODEX_SHIM = "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"
CODEX_ENVIRONMENT_NAME = "Codex"


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


def _spec_diagnostic_to_install(diagnostic: Any) -> dict[str, str]:
    item = diagnostic.to_dict()
    item.setdefault("disposition", "blocking")
    return item


def _load_projects(config_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, Any]]:
    config_path = config_root / GOVERNED_PROJECTS_CONFIG_PATH
    validation_diagnostics = [
        _spec_diagnostic_to_install(diagnostic)
        for diagnostic in validate_governed_projects_config(config_root, config_path)
    ]
    config = parse_governed_projects_config(config_root, config_path)
    config_summary = {
        "path": config_path.as_posix(),
        "exists": bool(config.get("exists")),
        "product_name": config.get("product_name", ""),
        "product_description": config.get("product_description", ""),
        "projects": len(config.get("projects", [])),
        "validation_status": "blocked" if validation_diagnostics else "ok",
        "diagnostics": len(validation_diagnostics),
    }
    if validation_diagnostics:
        return [], validation_diagnostics, config_summary

    projects: list[dict[str, Any]] = []
    for index, project in enumerate(config["projects"], start=1):
        if not isinstance(project, dict):
            continue
        project_path = project.get("path")
        if not isinstance(project_path, str) or not project_path.strip():
            continue
        raw_path = Path(project_path).expanduser()
        resolved_path = raw_path if raw_path.is_absolute() else config_path.parent / raw_path
        projects.append(
            {
                "index": index,
                "id": str(project.get("id") or f"project-{index}"),
                "name": str(project.get("name") or project.get("id") or f"project-{index}"),
                "path": resolved_path.resolve(),
            }
        )
    if not projects:
        validation_diagnostics.append(
            _diagnostic(
                "blocking",
                "INSTALL_VERIFY_GOVERNED_PROJECTS_EMPTY",
                config_path.as_posix(),
                "管辖项目配置没有可验证项目，无法验证管辖项目 Git Hook。",
            )
        )
        config_summary["validation_status"] = "blocked"
        config_summary["diagnostics"] = len(validation_diagnostics)
    return projects, validation_diagnostics, config_summary


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
    try:
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
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "failed",
            "returncode": None,
            "stdout_excerpt": (exc.stdout or "")[:1000] if isinstance(exc.stdout, str) else "",
            "stderr_excerpt": (exc.stderr or "")[:1000] if isinstance(exc.stderr, str) else "",
            "payload": {},
            "diagnostics": [
                _diagnostic(
                    "blocking",
                    "INSTALL_VERIFY_CODEX_SHIM_DIRECT_TEST_TIMEOUT",
                    shim.as_posix(),
                    "环境插件 repo-local shim 直测超时，无法确认安装检测通过。",
                )
            ],
        }
    except OSError as exc:
        return {
            "status": "failed",
            "returncode": None,
            "stdout_excerpt": "",
            "stderr_excerpt": str(exc)[:1000],
            "payload": {},
            "diagnostics": [
                _diagnostic(
                    "blocking",
                    "INSTALL_VERIFY_CODEX_SHIM_DIRECT_TEST_FAILED_TO_START",
                    shim.as_posix(),
                    f"环境插件 repo-local shim 直测无法启动: {exc}",
                )
            ],
        }
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


def _not_run_shim_tests(reason: str) -> dict[str, dict[str, Any]]:
    return {
        "session_start_direct": {"status": "not_run", "returncode": None, "reason": reason},
        "pre_tool_use_direct_block": {"status": "not_run", "returncode": None, "reason": reason},
        "completion_claim_direct_degrade": {"status": "not_run", "returncode": None, "reason": reason},
    }


def _is_codex_environment(environment_name: str) -> bool:
    return environment_name.strip().lower() == CODEX_ENVIRONMENT_NAME.lower()


def _shim_tests_passed(shim_tests: dict[str, dict[str, Any]]) -> bool:
    return bool(shim_tests) and all(item.get("status") == "passed" for item in shim_tests.values())


def _codex_plugin_install_detected(codex_plugin: dict[str, Any]) -> bool:
    details = codex_plugin.get("details", {})
    if not isinstance(details, dict):
        details = {}
    return (
        codex_plugin.get("status") == "available"
        and codex_plugin.get("decision") == "verify_trust_and_runtime_before_integration"
        and details.get("required_events_ok") is True
        and bool(details.get("commands"))
    )


def _verify_environment(ldvh_root: Path, repo: Path, codex_home: Path | None, environment_name: str) -> dict[str, Any]:
    if not _is_codex_environment(environment_name):
        return {
            "summary": {
                "status": "review_required",
                "environment_name": environment_name,
                "environment_adapter": "unsupported_target_environment",
                "target_environment_supported": False,
                "install_verified": False,
                "environment_integrated": False,
                "plugin_integrated": False,
                "plugin_status": "unsupported_target_environment",
                "plugin_decision": "create_target_environment_plugin_before_verification",
                "human_acceptance_required": True,
                "post_install_smoke_check_recommended": False,
                "blocking": 0,
            },
            "audit": {},
            "shim_direct_tests": _not_run_shim_tests(
                "当前统一验收入口只内置 Codex 样例 shim 直测；目标环境需要对应插件 / 扩展包实装后再验收。"
            ),
            "human_acceptance": {
                "required": True,
                "reason": f"{environment_name} 目标环境尚无当前验收入口可识别的 LDVH 插件 / 扩展包实装、授权、payload、失败处理和回滚证据。",
                "steps": [
                    f"打开 {environment_name} 插件页面 / 扩展页面 / 插件管理器，确认存在 LDVH 插件或扩展包。",
                    f"按 {environment_name} 要求重启 App 或重载插件宿主；重启后回到插件页面确认插件仍启用且无错误。",
                    f"完成 {environment_name} 的授权 / trust；没有授权提示时，记录插件页面无待处理授权。",
                    f"新开一个 {environment_name} 窗口或会话，确认启动事件能看到 LDVH 提示或诊断输出。",
                    "触发一次受控写入类工具，确认负例会阻断，正例会放行。",
                    "安装检测通过后，如需声明 integrated，进入 specs/31-环境Hook接入后验收行动模板.md 逐项验收并记录 lifecycle 验收。",
                    "若卸载或禁用插件，重新打开窗口确认不再自动触发 LDVH。",
                    "失败时返回插件页面状态、错误文本、截图或本命令 JSON 输出。",
                ],
                "acceptance_criteria": [
                    f"{environment_name} 插件页面显示 LDVH 插件或扩展包已启用、已授权或无待处理授权，且无错误。",
                    "插件命令、manifest 或入口指向当前 V3 LDVH root / V3 入口。",
                    "重启 App 或重载插件宿主后，插件页面状态保持启用且无错误。",
                    "新窗口或新会话能看到 LDVH 启动提示、诊断输出或可回读的真实触发证据。",
                    "受控写入负例被阻断，正例被放行。",
                    "统一安装验证显示 install_complete=true，并列出插件状态、shim 或目标入口直测结果，以及 Git Hook 正反例结果。",
                ],
            },
            "diagnostics": [],
        }

    audit = build_environment_entry_audit(repo=repo, ldvh_root=ldvh_root, codex_home=codex_home)
    candidates = {candidate["id"]: candidate for candidate in audit["candidates"]}
    codex_plugin = candidates.get("codex.ldvh-plugin", {})
    diagnostics: list[dict[str, str]] = list(audit.get("diagnostics", []))

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
    environment_install_verified = (
        environment_integrated
        or (
            _codex_plugin_install_detected(codex_plugin)
            and _shim_tests_passed(shim_tests)
        )
    )
    human_acceptance_required = not environment_install_verified
    post_install_smoke_check_recommended = environment_install_verified and not environment_integrated
    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    status = "blocked" if blocking else "ok" if environment_install_verified else "review_required"

    return {
        "summary": {
            "status": status,
            "environment_name": environment_name,
            "environment_adapter": "codex_sample",
            "target_environment_supported": True,
            "install_verified": environment_install_verified,
            "environment_integrated": environment_integrated,
            "plugin_integrated": codex_plugin_integrated,
            "plugin_status": codex_plugin.get("status", "unknown"),
            "plugin_decision": codex_plugin.get("decision", "unknown"),
            "human_acceptance_required": human_acceptance_required,
            "post_install_smoke_check_recommended": post_install_smoke_check_recommended,
            "blocking": blocking,
        },
        "audit": audit,
        "shim_direct_tests": shim_tests,
        "human_acceptance": {
            "required": human_acceptance_required,
            "reason": "环境插件安装检测尚未通过。"
            if human_acceptance_required
            else "安装检测已通过；以下为用户侧冒烟检查，不阻断安装完成。",
            "steps": [
                f"打开 {environment_name} 插件页面 / 扩展页面 / 插件管理器，确认 LDVH 插件已安装。",
                f"按 {environment_name} 要求重启 App 或重载插件宿主；重启后回到插件页面确认插件仍启用且无错误。",
                f"完成 {environment_name} 的授权 / trust；没有授权提示时，记录插件页面无待处理授权。",
                f"新开一个 {environment_name} 窗口或会话，确认 SessionStart 能看到 LDVH 提示或诊断输出。",
                "触发一次受控写入类工具，确认 PreToolUse 负例会阻断，正例会放行。",
                "如需把 environment_hook_integrated 转为 true，进入 specs/31-环境Hook接入后验收行动模板.md 逐项验收并记录 lifecycle 验收。",
                "若卸载或禁用插件，重新打开窗口确认不再自动触发 LDVH。",
                "失败时返回插件页面状态、错误文本、截图或本命令 JSON 输出。",
            ],
            "acceptance_criteria": [
                f"{environment_name} 插件页面显示 LDVH 插件已启用、已授权或无待处理授权，且无错误。",
                f"插件 Hook 命令指向当前 V3 shim: {CODEX_SHIM}。",
                "重启 App 或重载插件宿主后，插件页面状态保持启用且无错误。",
                "新窗口或新会话能看到 LDVH SessionStart 提示、诊断输出或可回读的真实触发证据。",
                "PreToolUse 负例被阻断，正例被放行。",
                "install_verification.py 显示 install_complete=true、插件可见、shim 直测通过，并列出 Git Hook 正反例结果。",
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
    lifecycle_acceptance_path: Path | None = None,
    require_environment_integrated: bool = False,
) -> dict[str, Any]:
    resolved_governance_root = governance_root.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    resolved_repo = repo.resolve()
    projects, config_diagnostics, governed_config = _load_projects(resolved_governance_root)
    git_results = [
        _verify_git_hook(project, resolved_governance_root, resolved_ldvh_root)
        for project in projects
    ] if not config_diagnostics else []
    environment = _verify_environment(resolved_ldvh_root, resolved_repo, codex_home, environment_name)
    lifecycle_acceptance = build_lifecycle_acceptance_status(
        ldvh_root=resolved_ldvh_root,
        environment_name=environment_name,
        path=lifecycle_acceptance_path,
    )

    diagnostics: list[dict[str, str]] = list(config_diagnostics)
    for result in git_results:
        diagnostics.extend(result["diagnostics"])
    diagnostics.extend(environment["diagnostics"])
    diagnostics.extend(lifecycle_acceptance["diagnostics"])

    environment_install_verified = environment["summary"]["install_verified"]
    base_environment_integrated = environment["summary"]["environment_integrated"]
    lifecycle_acceptance_valid = lifecycle_acceptance["summary"]["valid"]
    environment_integrated = bool(
        base_environment_integrated or (environment_install_verified and lifecycle_acceptance_valid)
    )
    environment["summary"]["environment_integrated"] = environment_integrated
    environment["summary"]["lifecycle_acceptance_valid"] = lifecycle_acceptance_valid
    environment["summary"]["post_install_smoke_check_recommended"] = (
        environment_install_verified and not environment_integrated
    )
    environment["lifecycle_acceptance"] = lifecycle_acceptance

    if require_environment_integrated and not environment_integrated:
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
    install_complete = git_ok and environment_install_verified and blocking == 0
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
            "governed_config_ok": not config_diagnostics,
            "git_hooks_ok": git_ok,
            "environment_hook_install_verified": environment_install_verified,
            "environment_hook_integrated": environment_integrated,
            "environment_lifecycle_acceptance_valid": lifecycle_acceptance_valid,
            "environment_human_acceptance_required": environment["summary"]["human_acceptance_required"],
            "environment_user_smoke_check_recommended": environment["summary"]["post_install_smoke_check_recommended"],
            "blocking": blocking,
            "diagnostics": len(diagnostics),
        },
        "governed_config": governed_config,
        "git_hooks": git_results,
        "environment": environment,
        "diagnostics": diagnostics,
        "source_refs": [
            {"path": "specs/30-LDVH安装初始化管辖项目配置行动模板.md", "role": "install_handoff_contract"},
            {"path": "specs/31-环境Hook接入后验收行动模板.md", "role": "environment_hook_acceptance_handoff"},
            {"path": "code/governed_hook_adapter.py", "role": "git_hook_status_backend"},
            {"path": "code/environment_entry_audit.py", "role": "environment_hook_audit"},
            {"path": "code/environment_lifecycle_acceptance.py", "role": "environment_lifecycle_acceptance"},
            {"path": "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py", "role": "environment_shim_direct_test"},
        ],
    }


def _mark(value: bool) -> str:
    return "✅" if value else "⛔"


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 installation verification")
    print(f"- status: {summary['status']}")
    print(f"- install_complete: {summary['install_complete']}")
    print(f"- governed_config_ok: {summary['governed_config_ok']}")
    print(f"- git_hooks_ok: {summary['git_hooks_ok']}")
    print(f"- environment_hook_install_verified: {summary['environment_hook_install_verified']}")
    print(f"- environment_hook_integrated: {summary['environment_hook_integrated']}")
    print(f"- environment_lifecycle_acceptance_valid: {summary['environment_lifecycle_acceptance_valid']}")
    print(f"- environment_human_acceptance_required: {summary['environment_human_acceptance_required']}")
    print(f"- environment_user_smoke_check_recommended: {summary['environment_user_smoke_check_recommended']}")
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
    print(f"- environment_adapter: {env_summary['environment_adapter']}")
    print(f"- target_environment_supported: {env_summary['target_environment_supported']}")
    print(f"- plugin_status: {env_summary['plugin_status']}")
    print(f"- plugin_decision: {env_summary['plugin_decision']}")
    print(f"- install_verified: {env_summary['install_verified']}")
    print(f"- environment_integrated: {env_summary['environment_integrated']}")
    print(f"- lifecycle_acceptance_valid: {env_summary['lifecycle_acceptance_valid']}")
    print("- shim_direct_tests:")
    for test_name, test_result in env["shim_direct_tests"].items():
        print(f"  - {test_name}: {test_result['status']} (returncode={test_result['returncode']})")

    if env["human_acceptance"]["required"] or env_summary.get("post_install_smoke_check_recommended"):
        if env["human_acceptance"]["required"]:
            print("\nHuman acceptance required before install can complete:")
        else:
            print("\nPost-install user smoke check (not blocking install_complete):")
        print(f"- reason: {env['human_acceptance']['reason']}")
        for step in env["human_acceptance"]["steps"]:
            print(f"- {step}")
        criteria = env["human_acceptance"].get("acceptance_criteria", [])
        if criteria:
            print("\nNormal criteria:")
            for item in criteria:
                print(f"- {item}")

    lifecycle = env.get("lifecycle_acceptance", {})
    lifecycle_summary = lifecycle.get("summary", {})
    if lifecycle_summary.get("valid"):
        record = lifecycle.get("record", {})
        print("\nEnvironment lifecycle acceptance:")
        print(f"- path: {lifecycle_summary.get('path', '')}")
        print(f"- environment_name: {record.get('environment_name', '')}")
        print(f"- recorded_at: {record.get('recorded_at', '')}")

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
    parser.add_argument(
        "--environment-name",
        default=CODEX_ENVIRONMENT_NAME,
        help="current AI environment name for Human-facing output; repo-local shim direct tests currently cover the Codex sample only",
    )
    parser.add_argument("--require-environment-integrated", action="store_true", help="treat missing real environment integration as blocking")
    parser.add_argument("--lifecycle-acceptance-path", default="", help="override environment lifecycle acceptance evidence path")
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
        lifecycle_acceptance_path=Path(args.lifecycle_acceptance_path).resolve() if args.lifecycle_acceptance_path else None,
        require_environment_integrated=args.require_environment_integrated,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
