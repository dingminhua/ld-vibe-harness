from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

from environment_entry_audit import build_environment_entry_audit
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


def _detect_current_environment() -> str:
    for key, _ in os.environ.items():
        upper_key = key.upper()
        if upper_key.startswith("TRAE_"):
            return "Trae"
    return CODEX_ENVIRONMENT_NAME


def _visible_probe_command(ldvh_root: Path, repo: Path, governance_root: Path | None = None) -> str:
    parts = [
        "python3",
        (ldvh_root / "code/runtime_adapter.py").as_posix(),
        "session-start",
        "--root",
        ldvh_root.as_posix(),
    ]
    if governance_root is not None:
        parts.extend(["--config-root", governance_root.as_posix()])
    parts.extend([
        "--session-id",
        "lifecycle-verify-probe",
        "--target-path",
        repo.as_posix(),
        "--task",
        "LDVH lifecycle verification probe",
        "--operation",
        "read",
        "--trigger-source",
        "manual.lifecycle-verify-probe",
        "--format",
        "text",
    ])
    return " ".join(shlex.quote(part) for part in parts)


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
    return resolved.parent


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
        "completion_claim_direct_nonblocking": {"status": "not_run", "returncode": None, "reason": reason},
    }


def _is_codex_environment(environment_name: str) -> bool:
    return environment_name.strip().lower() == CODEX_ENVIRONMENT_NAME.lower()


def _shim_tests_passed(shim_tests: dict[str, dict[str, Any]]) -> bool:
    return bool(shim_tests) and all(item.get("status") == "passed" for item in shim_tests.values())


def _hook_specific_output(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("hookSpecificOutput")
    return value if isinstance(value, dict) else {}


def _hook_event_name(payload: dict[str, Any]) -> str:
    return str(_hook_specific_output(payload).get("hookEventName") or "")


def _pre_tool_denied(payload: dict[str, Any]) -> bool:
    hook_output = _hook_specific_output(payload)
    return (
        hook_output.get("hookEventName") == "PreToolUse"
        and hook_output.get("permissionDecision") == "deny"
        and bool(hook_output.get("permissionDecisionReason"))
    )


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


def _verify_environment(
    ldvh_root: Path,
    repo: Path,
    codex_home: Path | None,
    environment_name: str,
    governance_root: Path | None = None,
) -> dict[str, Any]:
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
                "reason": f"{environment_name} 目标环境尚无当前验收入口可识别的 LDVH 插件 / 扩展包实装、授权、payload、失败处理和回滚证据；目标环境没有自动 Hook 入口时，仍按 30 交还薄引用 / manual entrypoint，并继续断点后 lifecycle 验证。",
                "steps": [
                    f"先确认 {environment_name} 是否支持插件 / 扩展包 / package 形态的 Hook 入口。",
                    "若支持 Hook，必须先实装目标环境插件 / 扩展包并让安装检测通过；写入完成后按 30 的断点恢复协议继续 lifecycle 验证。",
                    "若 01 或环境审计确认没有自动 Hook 入口，按 specs/10-安装与配置规范.md 选择薄引用 / manual entrypoint 承接，并按 specs/30 的交互外壳交还恢复入口。",
                    "薄引用 / manual entrypoint 承接必须基于 hooks/LDVH-RUNTIME-PROTOCOL.md 生成已替换 LDVH 本体绝对路径的薄引用文本，给出可复制内容和写入路径，不得只列承接形态表。",
                    "薄引用 / manual entrypoint 承接不得声明环境自动接入已完成；断点后验证仍按 30 的统一 lifecycle 验证执行。",
                ],
                "acceptance_criteria": [
                    "目标环境支持 Hook 时，必须能提供插件 / 扩展包实装、入口指向、授权、payload、失败处理和回滚证据。",
                    "目标环境确认没有自动 Hook 入口时，30 仍交还 01.Att.04 的 manual_ready / available / deferred / absent 等分类，并补充承接形态说明。",
                    "薄引用 / manual entrypoint 承接的验证标准是 V3 specs 可找到、Runtime Protocol 可读、manual CLI 可运行、runtime adapter 产出 receipt、Git Hook 正反例通过。",
                    "Human 已理解当前目标环境的触发来源、不可验证范围和断点后验证方式。",
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
            "configRoot": governance_root.as_posix() if governance_root is not None else "",
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
            "configRoot": governance_root.as_posix() if governance_root is not None else "",
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
            "configRoot": governance_root.as_posix() if governance_root is not None else "",
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
            if session.get("returncode") == 0 and _hook_event_name(session_payload) == "SessionStart"
            else "failed",
            "returncode": session.get("returncode"),
        },
        "pre_tool_use_direct_block": {
            "status": "passed"
            if pretool.get("returncode") == 0 and _pre_tool_denied(pretool_payload)
            else "failed",
            "returncode": pretool.get("returncode"),
        },
        "completion_claim_direct_nonblocking": {
            "status": "passed"
            if stop.get("returncode") == 0
            and stop_payload.get("continue") is True
            and "LDVH V3 completion check" in str(stop_payload.get("systemMessage") or "")
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

    visible_probe_command = _visible_probe_command(ldvh_root, repo, governance_root)
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
            "visible_probe_command": visible_probe_command,
            "reason": "环境插件安装检测尚未通过。"
            if human_acceptance_required
            else "安装检测已通过；以下为用户侧冒烟检查，不阻断安装完成。",
            "steps": [
                f"打开 {environment_name} 插件页面 / 扩展页面 / 插件管理器，确认 LDVH 插件已安装。",
                f"按 {environment_name} 要求重启 App 或重载插件宿主；重启后回到插件页面确认插件仍启用且无错误。",
                f"完成 {environment_name} 的授权 / trust；没有授权提示时，记录插件页面无待处理授权。",
                f"新开一个 {environment_name} 窗口或会话，让 AI 运行只读 LDVH 可见性探针并返回结果表。",
                "触发一次受控写入类工具，确认写入前检查负例会阻断，正例会放行。",
                "如需确认 lifecycle 生效，按 specs/10-安装与配置规范.md 的验证契约和 specs/30 的断点恢复话术继续验证。",
                "若卸载或禁用插件，重新打开窗口确认不再自动触发 LDVH。",
                "失败时返回插件页面结果、错误文本、截图或本命令 JSON 输出。",
            ],
            "acceptance_criteria": [
                f"{environment_name} 插件页面显示 LDVH 插件已启用、已授权或无待处理授权，且无错误。",
                f"插件 Hook 命令指向当前 V3 shim: {CODEX_SHIM}。",
                "重启 App 或重载插件宿主后，插件页面仍保持启用且无错误。",
                "新会话只读可见性探针输出 status=ok、event=session_start、receipt_id，且 Diagnostics: none；若目标环境提供真实触发证据，应一并回读。",
                "写入前检查负例被阻断，正例被放行。",
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
    environment_name: str | None = None,
    require_environment_integrated: bool = False,
) -> dict[str, Any]:
    if environment_name is None:
        environment_name = _detect_current_environment()
    resolved_governance_root = governance_root.resolve()
    resolved_ldvh_root = ldvh_root.resolve()
    resolved_repo = repo.resolve()
    projects, config_diagnostics, governed_config = _load_projects(resolved_governance_root)
    git_results = [
        _verify_git_hook(project, resolved_governance_root, resolved_ldvh_root)
        for project in projects
    ] if not config_diagnostics else []
    environment = _verify_environment(
        resolved_ldvh_root,
        resolved_repo,
        codex_home,
        environment_name,
        resolved_governance_root,
    )

    diagnostics: list[dict[str, str]] = list(config_diagnostics)
    for result in git_results:
        diagnostics.extend(result["diagnostics"])
    diagnostics.extend(environment["diagnostics"])

    environment_install_verified = environment["summary"]["install_verified"]
    environment_integrated = bool(environment["summary"]["environment_integrated"])
    environment["summary"]["environment_integrated"] = environment_integrated
    environment["summary"]["post_install_smoke_check_recommended"] = (
        environment_install_verified and not environment_integrated
    )

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
    result = {
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
            {"path": "specs/10-安装与配置规范.md", "role": "install_config_contract"},
            {"path": "specs/30-LDVH安装初始化管辖项目配置行动模板.md", "role": "install_interaction_handoff"},
            {"path": "code/governed_hook_adapter.py", "role": "git_hook_status_backend"},
            {"path": "code/environment_entry_audit.py", "role": "environment_hook_audit"},
            {"path": "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py", "role": "environment_shim_direct_test"},
        ],
    }
    result["user_handoff"] = _build_user_handoff(result)
    return result


def _mark(value: bool) -> str:
    return "✅" if value else "⛔"


def _git_hook_user_status(git_results: list[dict[str, Any]]) -> str:
    if not git_results:
        return "未检查"
    if all(result["summary"]["status"] == "ok" for result in git_results):
        return "通过"
    if any(not result["summary"]["hook_installed"] for result in git_results):
        return "需安装 / 需升级"
    return "阻断"


def _environment_user_status(env_summary: dict[str, Any]) -> str:
    if not env_summary.get("target_environment_supported"):
        return "薄引用 / manual entrypoint"
    if env_summary.get("blocking"):
        return "阻断"
    if env_summary.get("environment_integrated"):
        return "已自动接入"
    if env_summary.get("install_verified"):
        return "入口已检测，断点后验证"
    return "需安装 / 需升级"


def _build_user_handoff(result: dict[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    env = result["environment"]
    env_summary = env["summary"]
    environment_name = env_summary["environment_name"]
    git_status = _git_hook_user_status(result["git_hooks"])
    env_status = _environment_user_status(env_summary)
    visible_probe_command = env.get("human_acceptance", {}).get("visible_probe_command", "")

    if summary["blocking"]:
        install_status = "阻断"
        next_step = "先处理阻断项，再复跑安装验证"
    elif summary["install_complete"]:
        install_status = "是"
        if env_status == "已自动接入":
            next_step = "可停止；保留验证输出作为交还证据"
        elif env_status == "入口已检测，断点后验证":
            next_step = "继续 30 断点后 lifecycle 验证"
        else:
            next_step = "交还当前状态和残留限制"
    else:
        install_status = "否"
        if not env_summary.get("target_environment_supported"):
            next_step = "按 30 确认目标环境入口；无自动 Hook 时交还薄引用 / manual entrypoint 并继续断点后验证"
        elif git_status != "通过":
            next_step = "先安装或修复管辖项目 Git commit-msg Hook"
        else:
            next_step = "先安装、升级或授权目标环境插件"

    if env_status == "入口已检测，断点后验证":
        user_next_steps = [
            f"打开 {environment_name} 插件页面 / 扩展页面 / 插件管理器。",
            "重启 App 或重载插件宿主后确认插件仍启用且无错误。",
            "完成授权 / trust；没有授权提示时记录无待处理授权。",
            f"新开 {environment_name} 窗口或会话，让 AI 运行只读 LDVH 可见性探针并返回结果表。",
            "需要确认 lifecycle 生效时，按 30 恢复入口继续断点后验证。",
        ]
    elif env_status == "薄引用 / manual entrypoint":
        user_next_steps = [
            "确认目标环境当前没有可用 Hook 接入，或先补目标环境插件方案。",
            "若确认无可用 Hook，按 30 薄引用 / manual entrypoint 安装交还完成交还。",
            "确认薄引用文件已写入并可被 AI 读取到 Runtime Protocol 入口。",
            "复核每个管辖项目 Git commit-msg Hook 的正反例结果。",
            "以后目标环境支持 Hook 时，再升级为环境插件并进入安装检测。",
        ]
    elif env_status == "已自动接入":
        user_next_steps = [
            "保留本次验证输出。",
            "后续变更插件、授权或 Hook 后重新运行安装验证。",
        ]
    else:
        user_next_steps = [
            "按 diagnostics 修复环境插件、授权、旧路径或 manifest 问题。",
            "修复后重新运行 install_verification.py。",
            "仍失败时复制失败信息包交给 AI 诊断。",
        ]

    return {
        "status_card": [
            {"item": "安装完成", "value": install_status},
            {"item": "环境自动拦截", "value": env_status},
            {"item": "提交消息检查", "value": git_status},
            {"item": "下一步", "value": next_step},
        ],
        "hook_status_blocks": [
            {
                "name": "环境自动拦截",
                "status": env_status,
                "normal": "当前检测为已自动接入时无需处理；否则写入完成后按 30 恢复入口继续 lifecycle 验证。",
                "next_step": next_step if env_status != "已自动接入" else "无需断点后验证。",
            },
            {
                "name": "提交消息检查",
                "status": git_status,
                "normal": "每个管辖项目 Git commit-msg Hook 已安装、managed、正例放行、反例阻断。",
                "next_step": "失败项目先安装或修复 Git Hook。" if git_status != "通过" else "无需处理。",
            },
        ],
        "user_next_steps": user_next_steps,
        "visible_probe_command": visible_probe_command,
        "failure_info_package": [
            "目标环境名称和版本",
            "插件页面结果截图或文字",
            "install_verification.py --format json 完整输出",
            "environment_entry_audit.py --format text 输出",
            "失败步骤编号",
            "是否发生实际写入",
            "scratch target 路径和文件状态",
            "相关错误文本",
        ],
    }


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 installation verification")
    handoff = result.get("user_handoff", {})
    status_card = handoff.get("status_card", [])
    if status_card:
        print("\nUser-facing status:")
        for row in status_card:
            print(f"- {row['item']}: {row['value']}")
    hook_blocks = handoff.get("hook_status_blocks", [])
    if hook_blocks:
        print("\nHook status blocks:")
        for block in hook_blocks:
            print(f"- {block['name']}: {block['status']}")
            print(f"  normal: {block['normal']}")
            print(f"  next: {block['next_step']}")
    next_steps = handoff.get("user_next_steps", [])
    if next_steps:
        print("\nUser next steps:")
        for step in next_steps:
            print(f"- {step}")
    visible_probe_command = handoff.get("visible_probe_command")
    if visible_probe_command:
        print("\nVisible probe command:")
        print(visible_probe_command)
    if result["diagnostics"] or summary["status"] != "complete":
        failure_items = handoff.get("failure_info_package", [])
        if failure_items:
            print("\nFailure info package:")
            for item in failure_items:
                print(f"- {item}")

    print("\nTechnical summary:")
    print(f"- status: {summary['status']}")
    print(f"- install_complete: {summary['install_complete']}")
    print(f"- governed_config_ok: {summary['governed_config_ok']}")
    print(f"- git_hooks_ok: {summary['git_hooks_ok']}")
    print(f"- environment_hook_install_verified: {summary['environment_hook_install_verified']}")
    print(f"- environment_hook_integrated: {summary['environment_hook_integrated']}")
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
    parser.add_argument("--governance-root", default=default_config_root.as_posix(), help="root containing LDVH-GOVERNED-PROJECTS.yaml; defaults to the discovered config root or LDVH root parent")
    parser.add_argument("--ldvh-root", default=ROOT.as_posix(), help="LDVH v3 root")
    parser.add_argument("--repo", default=default_config_root.as_posix(), help="repo used for environment entry audit; defaults to the workspace root")
    parser.add_argument("--codex-home", default="", help="Codex home for read-only plugin audit")
    parser.add_argument(
        "--environment-name",
        default=_detect_current_environment(),
        help="current AI environment name for Human-facing output; repo-local shim direct tests currently cover the Codex sample only",
    )
    parser.add_argument(
        "--require-environment-integrated",
        action="store_true",
        help="strict technical audit only; do not use as the 30 breakpoint lifecycle handoff condition",
    )
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
