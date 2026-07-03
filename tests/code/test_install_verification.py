from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import install_verification
from environment_lifecycle_acceptance import (
    build_lifecycle_acceptance_status,
    record_lifecycle_acceptance,
)
from install_verification import CODEX_SHIM, build_install_verification


ROOT = Path(__file__).resolve().parents[2]


def _write_governed_config(root: Path, content: str) -> Path:
    path = root / "LDVH-GOVERNED-PROJECTS.yaml"
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def _install_backend_hook(repo: Path) -> None:
    subprocess.run(
        [
            "python3",
            "code/install_git_hooks.py",
            "install",
            "--repo",
            repo.as_posix(),
            "--ldvh-root",
            ROOT.as_posix(),
            "--backend-allow-external",
            "--embed-ldvh-root",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
        timeout=60,
    )


def _install_codex_v3_plugin(
    codex_home: Path,
    *,
    events: tuple[str, ...] = ("SessionStart", "PreToolUse", "Stop"),
    command_path: Path | None = None,
    command: str | None = None,
    enabled: bool = True,
) -> None:
    hook_dir = codex_home / "plugins" / "cache" / "personal" / "ldvh" / "0.1.0" / "hooks"
    hook_dir.mkdir(parents=True)
    (codex_home / "config.toml").write_text(
        f"""
[plugins."ldvh@personal"]
enabled = {str(enabled).lower()}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    v3_shim = command_path or ROOT / CODEX_SHIM
    hook_command = command or f"{sys.executable} {v3_shim}"
    matchers = {
        "SessionStart": "startup|resume",
        "PreToolUse": "Write|Edit|apply_patch",
        "Stop": "*",
    }
    (hook_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    event: [
                        {
                            "matcher": matchers[event],
                            "hooks": [{"type": "command", "command": hook_command}],
                        }
                    ]
                    for event in events
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_install_verification_runs_git_hook_positive_negative_and_marks_install_complete_without_integrated(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _install_backend_hook(repo)
    _install_codex_v3_plugin(codex_home)

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
    )

    assert result["summary"]["status"] == "complete"
    assert result["summary"]["governed_config_ok"] is True
    assert result["summary"]["git_hooks_ok"] is True
    assert result["summary"]["environment_hook_install_verified"] is True
    assert result["summary"]["environment_hook_integrated"] is False
    assert result["summary"]["environment_lifecycle_acceptance_valid"] is False
    assert result["summary"]["install_complete"] is True
    assert result["summary"]["environment_human_acceptance_required"] is False
    assert result["summary"]["environment_user_smoke_check_recommended"] is True
    assert result["git_hooks"][0]["summary"]["hook_installed"] is True
    assert result["git_hooks"][0]["summary"]["positive_passed"] is True
    assert result["git_hooks"][0]["summary"]["negative_blocked"] is True
    assert result["environment"]["shim_direct_tests"]["session_start_direct"]["status"] == "passed"
    assert result["environment"]["shim_direct_tests"]["pre_tool_use_direct_block"]["status"] == "passed"
    assert result["environment"]["shim_direct_tests"]["completion_claim_direct_nonblocking"]["status"] == "passed"
    assert result["environment"]["summary"]["environment_adapter"] == "codex_sample"
    assert result["environment"]["summary"]["target_environment_supported"] is True
    assert result["environment"]["summary"]["install_verified"] is True
    assert result["environment"]["summary"]["environment_integrated"] is False
    assert result["environment"]["summary"]["lifecycle_acceptance_valid"] is False
    human_acceptance = result["environment"]["human_acceptance"]
    assert any("插件页面" in step for step in human_acceptance["steps"])
    assert any("重启 App" in step for step in human_acceptance["steps"])
    assert any("授权 / trust" in step for step in human_acceptance["steps"])
    assert any("LDVH 提示或诊断输出" in step for step in human_acceptance["steps"])
    assert any("specs/31-环境Hook接入后验收行动模板.md" in step for step in human_acceptance["steps"])
    assert any("当前 V3 shim" in criterion for criterion in human_acceptance["acceptance_criteria"])
    assert any("install_complete=true" in criterion for criterion in human_acceptance["acceptance_criteria"])
    assert any("写入前检查负例被阻断，正例被放行" in criterion for criterion in human_acceptance["acceptance_criteria"])
    handoff = result["user_handoff"]
    status_card = {row["item"]: row["value"] for row in handoff["status_card"]}
    assert status_card["安装完成"] == "是"
    assert status_card["环境自动拦截"] == "自动接入待验收"
    assert status_card["提交消息检查"] == "通过"
    assert "31" in status_card["下一步"]
    assert [block["name"] for block in handoff["hook_status_blocks"]] == ["环境自动拦截", "提交消息检查"]
    assert any("插件页面" in step for step in handoff["user_next_steps"])
    assert any("目标环境名称和版本" in item for item in handoff["failure_info_package"])
    assert result["diagnostics"] == []


def test_lifecycle_acceptance_requires_human_gate_confirmation(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"

    result = record_lifecycle_acceptance(
        ldvh_root=ROOT,
        environment_name="Codex",
        path=acceptance,
        confirm_human_gate=False,
    )

    assert result["summary"]["valid"] is False
    assert result["summary"]["blocking"] == 1
    assert result["diagnostics"][0]["code"] == "ENV_LIFECYCLE_ACCEPTANCE_CONFIRMATION_REQUIRED"
    assert not acceptance.exists()


def test_lifecycle_acceptance_records_human_confirmed_smoke_check(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"

    recorded = record_lifecycle_acceptance(
        ldvh_root=ROOT,
        environment_name="Codex",
        path=acceptance,
        confirm_human_gate=True,
        source_note="插件页面启用，重启后 SessionStart 可见，PreToolUse 正反例符合预期。",
    )
    status = build_lifecycle_acceptance_status(
        ldvh_root=ROOT,
        environment_name="Codex",
        path=acceptance,
    )

    assert recorded["summary"]["valid"] is True
    assert status["summary"]["valid"] is True
    assert status["record"]["human_gate_confirmed"] is True
    assert status["record"]["plugin_page_ok"] is True
    assert status["record"]["blocking_observed"] is True
    assert status["diagnostics"] == []


def test_install_verification_can_close_environment_integrated_after_lifecycle_acceptance(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    acceptance = tmp_path / "acceptance.json"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _install_backend_hook(repo)
    _install_codex_v3_plugin(codex_home)
    record_lifecycle_acceptance(
        ldvh_root=ROOT,
        environment_name="Codex",
        path=acceptance,
        confirm_human_gate=True,
        source_note="Human confirmed post-restart lifecycle smoke check.",
    )

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
        lifecycle_acceptance_path=acceptance,
        require_environment_integrated=True,
    )

    assert result["summary"]["status"] == "complete"
    assert result["summary"]["install_complete"] is True
    assert result["summary"]["environment_hook_install_verified"] is True
    assert result["summary"]["environment_hook_integrated"] is True
    assert result["summary"]["environment_lifecycle_acceptance_valid"] is True
    assert result["summary"]["environment_user_smoke_check_recommended"] is False
    assert result["environment"]["summary"]["lifecycle_acceptance_valid"] is True
    assert result["environment"]["lifecycle_acceptance"]["summary"]["valid"] is True
    status_card = {row["item"]: row["value"] for row in result["user_handoff"]["status_card"]}
    assert status_card["安装完成"] == "是"
    assert status_card["环境自动拦截"] == "已 integrated"
    assert status_card["提交消息检查"] == "通过"
    assert "INSTALL_VERIFY_ENVIRONMENT_NOT_INTEGRATED" not in {
        diagnostic["code"] for diagnostic in result["diagnostics"]
    }
    assert result["diagnostics"] == []


def test_install_verification_requires_complete_codex_hook_manifest(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _install_backend_hook(repo)
    _install_codex_v3_plugin(codex_home, events=("SessionStart",))

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
    )

    assert result["summary"]["status"] == "review_required"
    assert result["summary"]["install_complete"] is False
    assert result["summary"]["environment_hook_install_verified"] is False
    assert result["environment"]["summary"]["install_verified"] is False
    assert result["environment"]["summary"]["plugin_decision"] == "complete_v3_hook_manifest_before_install_verified"
    codex_plugin = {
        candidate["id"]: candidate for candidate in result["environment"]["audit"]["candidates"]
    }["codex.ldvh-plugin"]
    assert codex_plugin["details"]["required_events_ok"] is False
    assert codex_plugin["details"]["missing_required_events"] == ["PreToolUse", "Stop"]


def test_install_verification_rejects_codex_hook_command_that_only_mentions_v3_path(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _install_backend_hook(repo)
    _install_codex_v3_plugin(codex_home, command=f"echo {ROOT / CODEX_SHIM}")

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
    )

    assert result["summary"]["status"] == "review_required"
    assert result["summary"]["install_complete"] is False
    assert result["summary"]["environment_hook_install_verified"] is False
    assert result["environment"]["summary"]["plugin_decision"] == "audit_plugin_hook_target"


def test_install_verification_keeps_absent_codex_plugin_review_required(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _install_backend_hook(repo)

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
    )

    assert result["summary"]["status"] == "review_required"
    assert result["summary"]["install_complete"] is False
    assert result["summary"]["environment_hook_install_verified"] is False
    assert result["environment"]["summary"]["plugin_decision"] == "install_plugin_before_claiming"


def test_install_verification_blocks_when_governed_git_hook_missing(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
    )

    assert result["summary"]["status"] == "blocked"
    assert result["summary"]["git_hooks_ok"] is False
    assert result["git_hooks"][0]["summary"]["hook_installed"] is False
    assert result["git_hooks"][0]["tests"]["positive_commit_message"]["status"] == "not_run"
    assert {diagnostic["code"] for diagnostic in result["diagnostics"]} >= {
        "INSTALL_VERIFY_GIT_HOOK_NOT_READY"
    }


def test_install_verification_blocks_invalid_governed_config_before_git_hook_checks(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
unsupported: true
projects:
  - id: app
    path: {repo}
""",
    )

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
    )

    assert result["summary"]["status"] == "blocked"
    assert result["summary"]["governed_config_ok"] is False
    assert result["summary"]["git_hooks_ok"] is False
    assert result["git_hooks"] == []
    assert result["governed_config"]["validation_status"] == "blocked"
    assert "GOVERNED_PROJECTS_ROOT_FIELD_FORBIDDEN" in {
        diagnostic["code"] for diagnostic in result["diagnostics"]
    }


def test_install_verification_keeps_non_codex_environment_gated(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _install_backend_hook(repo)

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Trae",
    )

    assert result["summary"]["status"] == "review_required"
    assert result["summary"]["git_hooks_ok"] is True
    assert result["summary"]["environment_hook_integrated"] is False
    assert result["environment"]["summary"]["environment_adapter"] == "unsupported_target_environment"
    assert result["environment"]["summary"]["target_environment_supported"] is False
    assert result["environment"]["summary"]["plugin_decision"] == "create_target_environment_plugin_before_verification"
    assert result["environment"]["shim_direct_tests"]["session_start_direct"]["status"] == "not_run"
    human_acceptance = result["environment"]["human_acceptance"]
    assert any("Trae 是否支持插件 / 扩展包 / package 形态的 Hook 入口" in step for step in human_acceptance["steps"])
    assert any("30 无 Hook 环境分支" in step for step in human_acceptance["steps"])
    assert any("thin-reference-ready" in step for step in human_acceptance["steps"])
    assert not any("specs/31-环境Hook接入后验收行动模板.md" in step for step in human_acceptance["steps"])
    assert any("manual-ready" in criterion for criterion in human_acceptance["acceptance_criteria"])
    assert any("不会自动阻断写入或完成声明" in criterion for criterion in human_acceptance["acceptance_criteria"])
    handoff = result["user_handoff"]
    status_card = {row["item"]: row["value"] for row in handoff["status_card"]}
    assert status_card["安装完成"] == "否"
    assert status_card["环境自动拦截"] == "手动可用"
    assert status_card["提交消息检查"] == "通过"
    assert "30" in status_card["下一步"]
    assert any("手动可用分支" in step for step in handoff["user_next_steps"])


def test_install_verification_keeps_disabled_codex_plugin_review_required(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _install_backend_hook(repo)
    _install_codex_v3_plugin(codex_home, enabled=False)

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
    )

    assert result["summary"]["status"] == "review_required"
    assert result["summary"]["install_complete"] is False
    assert result["summary"]["environment_hook_install_verified"] is False
    assert result["environment"]["summary"]["plugin_decision"] == "enable_or_install_v3_plugin"


def test_install_verification_keeps_stale_codex_plugin_review_required(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _install_backend_hook(repo)
    stale_shim = ROOT / "code/environment_plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"
    _install_codex_v3_plugin(codex_home, command_path=stale_shim)

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
    )

    assert result["summary"]["status"] == "review_required"
    assert result["summary"]["install_complete"] is False
    assert result["summary"]["environment_hook_install_verified"] is False
    assert result["environment"]["summary"]["plugin_decision"] == "reinstall_for_v3"
    assert "ENV_CODEX_LDVH_PLUGIN_STALE" in {diagnostic["code"] for diagnostic in result["diagnostics"]}


def test_install_verification_require_environment_integrated_blocks_after_install_verified(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    repo.mkdir()
    codex_home.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)
    _write_governed_config(
        governance_root,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {repo}
""",
    )
    _install_backend_hook(repo)
    _install_codex_v3_plugin(codex_home)

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
        require_environment_integrated=True,
    )

    assert result["summary"]["status"] == "blocked"
    assert result["summary"]["install_complete"] is False
    assert result["summary"]["environment_hook_install_verified"] is True
    assert result["summary"]["environment_hook_integrated"] is False
    assert "INSTALL_VERIFY_ENVIRONMENT_NOT_INTEGRATED" in {
        diagnostic["code"] for diagnostic in result["diagnostics"]
    }


def test_run_shim_timeout_returns_blocking_diagnostic(monkeypatch) -> None:
    def timeout_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout", 60))

    monkeypatch.setattr(install_verification.subprocess, "run", timeout_run)

    result = install_verification._run_shim(
        ROOT,
        {"hook_event_name": "SessionStart", "sessionId": "timeout-test", "cwd": ROOT.as_posix()},
    )

    assert result["status"] == "failed"
    assert result["returncode"] is None
    assert result["diagnostics"][0]["code"] == "INSTALL_VERIFY_CODEX_SHIM_DIRECT_TEST_TIMEOUT"
