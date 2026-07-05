from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import install_verification
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


def _symlink_temp_ldvh_root(tmp_path: Path) -> Path:
    ldvh_root = tmp_path / "ldvh-root"
    ldvh_root.mkdir()
    for name in ("code", "hooks", "specs"):
        (ldvh_root / name).symlink_to(ROOT / name, target_is_directory=True)
    return ldvh_root


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
    assert result["summary"]["ldvh_impact_verified"] is True
    assert result["summary"]["ldvh_impact_integrated"] is False
    assert result["summary"]["environment_hook_install_verified"] is True
    assert result["summary"]["environment_hook_integrated"] is False
    assert "environment_lifecycle_acceptance_valid" not in result["summary"]
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
    impact = result["ldvh_impact"]
    assert impact["verified"] is True
    assert impact["integrated"] is False
    assert impact["side_effects"]["formal_fact_source_writes"] is False
    assert impact["side_effects"]["spark_0046_writes"] is False
    assert impact["side_effects"]["scratch_writes"] is False
    assert impact["current_environment"] == "Codex"
    assert impact["current_install_mode"] == "插件 Hook"
    assert impact["primary_access_mode"] == "plugin_hook"
    assert impact["fallback_access_modes"] == []
    assert impact["verification_mode"] == "插件安装检测直测"
    assert impact["real_hook_observed"] is False
    assert impact["human_conclusion"]["environment"] == "Codex"
    assert impact["human_conclusion"]["install_mode"] == "插件 Hook"
    assert impact["human_conclusion"]["verified_as"] == "插件安装检测直测"
    assert impact["human_conclusion"]["fallback_checked"] == []
    assert "未声明真实自动 Hook integrated" in impact["human_conclusion"]["not_claimed"]
    assert impact["access_modes"]["plugin_hook"]["verified"] is True
    assert impact["access_modes"]["plugin_hook"]["integrated"] is False
    assert impact["access_modes"]["plugin_hook"]["verification_method"] == "repo_local_shim_direct_test"
    assert impact["access_modes"]["plugin_hook"]["real_hook_observed"] is False
    assert "尚未取得 Codex 生命周期真实触发证据" in impact["access_modes"]["plugin_hook"]["user_status"]
    assert impact["access_modes"]["thin_reference"]["available"] is True
    assert impact["access_modes"]["thin_reference"]["verified"] is False
    assert impact["access_modes"]["thin_reference"]["verification_method"] == "not_run_current_mode"
    assert impact["access_modes"]["thin_reference"]["real_hook_observed"] is False
    assert "未按薄引用方式验证" in impact["access_modes"]["thin_reference"]["user_status"]
    assert {effect["trigger"] for effect in impact["effects"]} >= {
        "SessionStart",
        "PreToolUse write-class tool",
        "Stop",
    }
    assert "Runtime Protocol read" not in {effect["trigger"] for effect in impact["effects"]}
    assert all(effect["writes"] is False for effect in impact["effects"])
    assert "lifecycle_acceptance_valid" not in result["environment"]["summary"]
    assert "lifecycle_acceptance" not in result["environment"]
    human_acceptance = result["environment"]["human_acceptance"]
    assert any("插件页面" in step for step in human_acceptance["steps"])
    assert any("重启 App" in step for step in human_acceptance["steps"])
    assert any("授权 / trust" in step for step in human_acceptance["steps"])
    assert any("只读 LDVH 可见性探针" in step for step in human_acceptance["steps"])
    assert any("specs/10-安装与配置规范.md" in step for step in human_acceptance["steps"])
    assert "runtime_adapter.py" in human_acceptance["visible_probe_command"]
    assert "session-start" in human_acceptance["visible_probe_command"]
    assert "manual.lifecycle-verify-probe" in human_acceptance["visible_probe_command"]
    assert any("当前 V3 shim" in criterion for criterion in human_acceptance["acceptance_criteria"])
    assert any("install_complete=true" in criterion for criterion in human_acceptance["acceptance_criteria"])
    assert any("写入前检查负例被阻断，正例被放行" in criterion for criterion in human_acceptance["acceptance_criteria"])
    handoff = result["user_handoff"]
    status_card = {row["item"]: row["value"] for row in handoff["status_card"]}
    assert status_card["当前环境"] == "Codex"
    assert status_card["当前安装方式"] == "插件 Hook"
    assert status_card["验收目标"] == "真实触发验收"
    assert status_card["验收结果"] == "未完成"
    assert "Git 提交消息 Hook 正例放行、反例阻断" in status_card["已真实触发"]
    assert "Codex 生命周期真实触发" in status_card["未完成触发项"]
    assert status_card["技术安装状态"] == "是"
    assert "真实" in status_card["下一步"]
    assert "授权 / trust" in status_card["下一步"]
    assert any("当前环境是 Codex" in item for item in handoff["plain_conclusion"])
    assert any("当前安装方式是插件 Hook" in item for item in handoff["plain_conclusion"])
    assert any("本次真实触发验收未完成" in item for item in handoff["plain_conclusion"])
    assert any("已真实触发：Git 提交消息 Hook 正例放行、反例阻断" in item for item in handoff["plain_conclusion"])
    assert any("未完成触发项：Codex 生命周期真实触发" in item for item in handoff["plain_conclusion"])
    assert any("真实触发验收未完成" in item for item in handoff["plain_conclusion"])
    assert not any("不等于已经打开或观察到真实自动 Hook" in item for item in handoff["plain_conclusion"])
    assert [block["name"] for block in handoff["impact_status_blocks"]] == [
        "真实触发验收",
        "提交消息检查",
    ]
    assert handoff["hook_status_blocks"] == handoff["impact_status_blocks"]
    assert any("插件页面" in step for step in handoff["user_next_steps"])
    assert any("授权 / trust" in step for step in handoff["user_next_steps"])
    assert any("只读 LDVH 可见性检查" in step for step in handoff["user_next_steps"])
    assert handoff["real_trigger_acceptance"]["result"] == "未完成"
    assert handoff["real_trigger_acceptance"]["complete"] is False
    assert handoff["real_trigger_acceptance"]["passed_items"] == [
        "Git 提交消息 Hook 正例放行、反例阻断"
    ]
    assert handoff["real_trigger_acceptance"]["pending_items"] == [
        "Codex 生命周期真实触发"
    ]
    assert "manual.lifecycle-verify-probe" in handoff["visible_probe_command"]
    assert any("目标环境名称和版本" in item for item in handoff["failure_info_package"])
    assert result["diagnostics"] == []


def test_install_verification_shim_direct_tests_force_spark_capture_off(tmp_path: Path, monkeypatch) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    spark_dir = tmp_path / "spark-capture"
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
    monkeypatch.setenv("LDVH_HOOK_SPARK_CAPTURE", "1")
    monkeypatch.setenv("LDVH_HOOK_SPARK_DIR", spark_dir.as_posix())

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
    )

    assert result["summary"]["ldvh_impact_verified"] is True
    assert result["ldvh_impact"]["side_effects"]["spark_0046_writes"] is False
    assert not spark_dir.exists()


def test_install_verification_parser_defaults_to_workspace_parent_without_config(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    ldvh_root = workspace / "ldvh"
    ldvh_root.mkdir(parents=True)
    monkeypatch.setattr(install_verification, "ROOT", ldvh_root)

    parser = install_verification.build_parser()
    args = parser.parse_args([])

    assert args.governance_root == workspace.as_posix()
    assert args.repo == workspace.as_posix()
    assert args.ldvh_root == ldvh_root.as_posix()


def test_install_verification_parser_defaults_to_existing_workspace_config(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    ldvh_root = workspace / "ldvh"
    ldvh_root.mkdir(parents=True)
    _write_governed_config(
        workspace,
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    path: {ldvh_root}
""",
    )
    monkeypatch.setattr(install_verification, "ROOT", ldvh_root)

    parser = install_verification.build_parser()
    args = parser.parse_args([])

    assert args.governance_root == workspace.as_posix()
    assert args.repo == workspace.as_posix()
    assert args.ldvh_root == ldvh_root.as_posix()


def test_install_verification_ignores_legacy_lifecycle_acceptance_json(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    ldvh_root = _symlink_temp_ldvh_root(tmp_path)
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
    _install_codex_v3_plugin(codex_home, command_path=ldvh_root / CODEX_SHIM)
    legacy_acceptance = ldvh_root / ".ldvh-runtime" / "environment-lifecycle-acceptance.json"
    legacy_acceptance.parent.mkdir(parents=True, exist_ok=True)
    legacy_acceptance.write_text(
        json.dumps(
            {
                "environment_name": "Codex",
                "human_gate_confirmed": True,
                "plugin_page_ok": True,
                "app_restarted": True,
                "authorization_ok": True,
                "session_start_observed": True,
                "pre_tool_use_observed": True,
                "blocking_observed": True,
                "positive_observed": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = build_install_verification(
        governance_root=governance_root,
        ldvh_root=ldvh_root,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
        require_environment_integrated=True,
    )

    assert result["summary"]["status"] == "blocked"
    assert result["summary"]["install_complete"] is False
    assert result["summary"]["environment_hook_install_verified"] is True
    assert result["summary"]["environment_hook_integrated"] is False
    assert "environment_lifecycle_acceptance_valid" not in result["summary"]
    assert "lifecycle_acceptance_valid" not in result["environment"]["summary"]
    assert "lifecycle_acceptance" not in result["environment"]
    assert "INSTALL_VERIFY_ENVIRONMENT_NOT_INTEGRATED" in {
        diagnostic["code"] for diagnostic in result["diagnostics"]
    }


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
    assert result["summary"]["ldvh_impact_verified"] is True
    assert result["summary"]["install_complete"] is False
    assert result["summary"]["environment_hook_install_verified"] is False
    assert result["summary"]["environment_hook_integrated"] is False
    impact = result["ldvh_impact"]
    assert impact["verified"] is True
    assert impact["integrated"] is False
    assert impact["current_environment"] == "Trae"
    assert impact["current_install_mode"] == "薄引用"
    assert impact["primary_access_mode"] == "thin_reference"
    assert impact["fallback_access_modes"] == []
    assert impact["verification_mode"] == "薄引用可读"
    assert impact["real_hook_observed"] is False
    assert impact["human_conclusion"]["environment"] == "Trae"
    assert impact["human_conclusion"]["install_mode"] == "薄引用"
    assert impact["human_conclusion"]["verified_as"] == "薄引用可读"
    assert impact["human_conclusion"]["fallback_checked"] == []
    assert impact["access_modes"]["plugin_hook"]["verified"] is False
    assert impact["access_modes"]["plugin_hook"]["verification_method"] == "not_run"
    assert impact["access_modes"]["plugin_hook"]["real_hook_observed"] is False
    assert impact["access_modes"]["thin_reference"]["available"] is True
    assert impact["access_modes"]["thin_reference"]["verified"] is True
    assert impact["access_modes"]["thin_reference"]["verification_method"] == "runtime_protocol_read"
    assert impact["access_modes"]["thin_reference"]["real_hook_observed"] is False
    assert impact["side_effects"]["formal_fact_source_writes"] is False
    assert impact["side_effects"]["spark_0046_writes"] is False
    assert impact["side_effects"]["scratch_writes"] is False
    assert impact["effects"] == [
        {
            "access_mode": "thin_reference",
            "trigger": "Runtime Protocol read",
            "expected_result": "AI 可读取统一入口并转入 runtime adapter / manual entrypoint",
            "observed": True,
            "writes": False,
        }
    ]
    assert result["environment"]["summary"]["environment_adapter"] == "unsupported_target_environment"
    assert result["environment"]["summary"]["target_environment_supported"] is False
    assert result["environment"]["summary"]["plugin_decision"] == "create_target_environment_plugin_before_verification"
    assert result["environment"]["shim_direct_tests"]["session_start_direct"]["status"] == "not_run"
    human_acceptance = result["environment"]["human_acceptance"]
    assert any("Trae 是否支持插件 / 扩展包 / package 形态的 Hook 入口" in step for step in human_acceptance["steps"])
    assert any("薄引用 / manual entrypoint" in step for step in human_acceptance["steps"])
    assert any("薄引用文本" in step for step in human_acceptance["steps"])
    assert not any("specs/31-环境Hook接入后验收行动模板.md" in step for step in human_acceptance["steps"])
    assert any("manual_ready" in criterion for criterion in human_acceptance["acceptance_criteria"])
    assert any("断点后验证方式" in criterion for criterion in human_acceptance["acceptance_criteria"])
    handoff = result["user_handoff"]
    status_card = {row["item"]: row["value"] for row in handoff["status_card"]}
    assert status_card["当前环境"] == "Trae"
    assert status_card["当前安装方式"] == "薄引用"
    assert status_card["验收目标"] == "真实触发验收"
    assert status_card["验收结果"] == "通过"
    assert "Git 提交消息 Hook 正例放行、反例阻断" in status_card["已真实触发"]
    assert "Runtime 入口可读" in status_card["已真实触发"]
    assert status_card["未完成触发项"] == "无"
    assert status_card["技术安装状态"] == "否"
    assert "30" in status_card["下一步"]
    assert any("当前环境是 Trae" in item for item in handoff["plain_conclusion"])
    assert any("本次真实触发验收通过" in item for item in handoff["plain_conclusion"])
    assert any("已真实触发：Git 提交消息 Hook 正例放行、反例阻断；Runtime 入口可读" in item for item in handoff["plain_conclusion"])
    assert [block["name"] for block in handoff["impact_status_blocks"]] == [
        "真实触发验收",
        "提交消息检查",
    ]
    assert handoff["hook_status_blocks"] == handoff["impact_status_blocks"]
    assert any("薄引用 / manual entrypoint" in step for step in handoff["user_next_steps"])


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


def test_find_config_root_defaults_to_ldvh_parent_when_config_missing(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    ldvh_root = workspace / "ldvh"
    ldvh_root.mkdir(parents=True)

    assert install_verification._find_config_root(ldvh_root) == workspace


def test_build_parser_defaults_governance_and_repo_to_workspace_parent_when_config_missing(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    ldvh_root = workspace / "ldvh"
    ldvh_root.mkdir(parents=True)
    monkeypatch.setattr(install_verification, "ROOT", ldvh_root)

    args = install_verification.build_parser().parse_args([])

    assert args.governance_root == workspace.as_posix()
    assert args.repo == workspace.as_posix()
    assert args.ldvh_root == ldvh_root.as_posix()


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
