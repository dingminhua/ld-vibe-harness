from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import install_wizard
from install_wizard import build_install_apply, build_install_check, build_install_plan, build_install_verify


ROOT = Path(__file__).resolve().parents[2]


def _write_governed_config(root: Path, repo: Path) -> None:
    (root / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        f"""
product_name: Test
product_description: Test registry
projects:
  - id: app
    name: App
    path: {repo}
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _init_git_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, timeout=30)


def _install_codex_v3_plugin(codex_home: Path) -> None:
    hook_dir = codex_home / "plugins" / "cache" / "personal" / "ldvh" / "0.1.0" / "hooks"
    hook_dir.mkdir(parents=True)
    (codex_home / "config.toml").write_text(
        """
[plugins."ldvh@personal"]
enabled = true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    shim = ROOT / "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"
    (hook_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [{"matcher": "startup|resume", "hooks": [{"type": "command", "command": f"{sys.executable} {shim}"}]}],
                    "PreToolUse": [{"matcher": "Write|Edit|apply_patch", "hooks": [{"type": "command", "command": f"{sys.executable} {shim}"}]}],
                    "Stop": [{"matcher": "*", "hooks": [{"type": "command", "command": f"{sys.executable} {shim}"}]}],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_install_wizard_parser_defaults_workspace_to_ldvh_parent(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    ldvh_root = workspace / "ldvh"
    ldvh_root.mkdir(parents=True)
    (ldvh_root / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "product_name: Wrong scope\nproduct_description: Should not define default workspace\nprojects: []\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(install_wizard, "ROOT", ldvh_root)

    args = install_wizard.build_parser().parse_args(["check"])

    assert args.governance_root == workspace.as_posix()
    assert args.repo == workspace.as_posix()
    assert args.ldvh_root == ldvh_root.as_posix()


def test_install_wizard_check_and_plan_are_read_only(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    codex_home.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    _install_codex_v3_plugin(codex_home)
    hook_path = repo / ".git/hooks/commit-msg"

    check = build_install_check(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
        environment_strategy="plugin_hook",
    )
    plan = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
        environment_strategy="plugin_hook",
    )

    assert check["metadata"]["read_only"] is True
    assert check["summary"]["status"] == "ok"
    assert plan["metadata"]["read_only"] is True
    assert plan["install_plan"]["environment_strategy"] == "plugin_hook"
    hook_write = next(item for item in plan["install_plan"]["planned_writes"] if item["kind"] == "git_commit_msg_hook")
    config_write = next(item for item in plan["install_plan"]["planned_writes"] if item["kind"] == "git_config")
    assert hook_write["current_active_hook"] == check["hook_status"]["hook_status"]["active_hook"]
    assert hook_write["path"] != hook_write["current_active_hook"]
    assert hook_write["path"].endswith(".git/ldvh-hooks/commit-msg")
    assert config_write["operation"] == "set_worktree_core_hooks_path"
    assert config_write["current_core_hooks_path"] == ""
    assert config_write["planned_core_hooks_path"].endswith(".git/ldvh-hooks")
    assert plan["install_plan"]["human_gate_required"] is True
    assert plan["interaction_handoff"]["template"] == "specs/30-安装配置与验证行动模板.md"
    assert plan["interaction_handoff"]["status"] == "requires_final_confirmation"
    assert plan["interaction_handoff"]["human_gate_required"] is True
    assert plan["interaction_handoff"]["planned_writes"] == 2
    assert plan["interaction_handoff"]["result_cards"][1]["id"] == "commit_message_check"
    assert plan["interaction_handoff"]["result_cards"][1]["status"] == "需安装或需升级"
    assert not hook_path.exists()


def test_install_wizard_auto_detect_unknown_environment_blocks_without_codex_default(tmp_path: Path, monkeypatch) -> None:
    for key in list(os.environ):
        if key.upper().startswith("TRAE_"):
            monkeypatch.delenv(key, raising=False)
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)

    result = build_install_check(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
    )

    assert result["metadata"]["environment_name"] == "未知环境"
    assert result["summary"]["environment_strategy"] == "unsupported"
    assert result["summary"]["status"] == "blocked"
    assert "目标环境插件缺口提示" in result["interaction_handoff"]["next_actions"][0]
    assert any("不要生成替代环境写入" in item for item in result["interaction_handoff"]["next_actions"])
    assert any(
        diagnostic["code"] == "INSTALL_WIZARD_ENVIRONMENT_HOOK_UNSUPPORTED"
        for diagnostic in result["diagnostics"]
    )


def test_install_wizard_apply_requires_human_gate_and_does_not_write(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    codex_home.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    _install_codex_v3_plugin(codex_home)
    hook_path = repo / ".git/hooks/commit-msg"

    result = build_install_apply(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
        environment_strategy="plugin_hook",
        confirm_human_gate=False,
    )

    assert result["summary"]["status"] == "blocked"
    assert any(diagnostic["code"] == "INSTALL_WIZARD_HUMAN_GATE_REQUIRED" for diagnostic in result["diagnostics"])
    assert result["interaction_handoff"]["status"] == "blocked"
    assert result["interaction_handoff"]["human_gate_confirmed"] is False
    assert not hook_path.exists()


def test_install_wizard_apply_plugin_hook_uses_governed_hook_backend(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    codex_home.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    _install_codex_v3_plugin(codex_home)

    result = build_install_apply(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_name="Codex",
        environment_strategy="plugin_hook",
        confirm_human_gate=True,
    )

    assert result["apply_results"][0]["metadata"]["authority"] == "governed_project_hook_adapter"
    assert result["apply_results"][0]["summary"]["hook_installed"] is True
    hook_status = result["apply_results"][0]["hook_status"]
    assert Path(hook_status["active_hook"]).is_file()
    assert result["verification"]["metadata"]["authority"] == "install_verification"
    assert result["interaction_handoff"]["status"] == "write_completed_verified"
    assert result["interaction_handoff"]["human_gate_confirmed"] is True
    assert result["interaction_handoff"]["result_cards"][0]["status"] == "断点后验证"
    assert result["interaction_handoff"]["result_cards"][1]["status"] == "通过"
    assert any("写入完成总结和验证结果" in action for action in result["interaction_handoff"]["next_actions"])


def test_install_wizard_blocks_non_git_repo(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    repo.mkdir()
    _write_governed_config(governance_root, repo)

    result = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_strategy="plugin_hook",
    )

    assert result["summary"]["status"] == "blocked"
    assert any(diagnostic["code"] == "GOVERNED_HOOK_TARGET_NOT_GIT_REPO" for diagnostic in result["diagnostics"])


def test_install_wizard_blocks_non_governed_repo(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    governed_repo = tmp_path / "governed"
    other_repo = tmp_path / "other"
    governance_root.mkdir()
    _init_git_repo(governed_repo)
    _init_git_repo(other_repo)
    _write_governed_config(governance_root, governed_repo)

    result = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=other_repo,
        environment_strategy="plugin_hook",
    )

    assert result["summary"]["status"] == "blocked"
    assert any(diagnostic["code"] == "INSTALL_WIZARD_TARGET_NOT_GOVERNED" for diagnostic in result["diagnostics"])


def test_install_wizard_blocks_non_hook_environment_strategies_without_alternative_writes(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)

    external_plan = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_name="WorkBuddy",
        environment_strategy="external_adapter_candidate",
    )
    unsupported_plan = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_name="WorkBuddy",
        environment_strategy="unsupported",
    )
    requested_plugin_hook_plan = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_name="WorkBuddy",
        environment_strategy="plugin_hook",
    )

    assert external_plan["summary"]["status"] == "blocked"
    assert unsupported_plan["summary"]["status"] == "blocked"
    assert requested_plugin_hook_plan["summary"]["status"] == "blocked"
    assert external_plan["install_plan"]["environment_strategy"] == "external_adapter_candidate"
    assert external_plan["install_plan"]["planned_writes"] == []
    assert external_plan["install_plan"]["handoff_candidates"][0]["kind"] == "external_adapter_candidate"
    assert external_plan["install_plan"]["skipped_writes"][0]["kind"] == "external_adapter_candidate"
    assert unsupported_plan["install_plan"]["environment_strategy"] == "unsupported"
    assert unsupported_plan["install_plan"]["planned_writes"] == []
    assert unsupported_plan["install_plan"]["handoff_candidates"][0]["kind"] == "unsupported"
    assert unsupported_plan["install_plan"]["skipped_writes"][0]["kind"] == "unsupported"
    assert requested_plugin_hook_plan["install_plan"]["environment_strategy"] == "unsupported"
    assert requested_plugin_hook_plan["install_plan"]["planned_writes"] == []
    assert "目标环境插件缺口提示" in external_plan["interaction_handoff"]["next_actions"][0]
    assert any("不要生成替代环境写入" in item for item in unsupported_plan["interaction_handoff"]["next_actions"])
    assert "目标环境插件缺口提示" in requested_plugin_hook_plan["interaction_handoff"]["next_actions"][0]
    assert any(
        diagnostic["code"] == "INSTALL_WIZARD_ENVIRONMENT_HOOK_UNSUPPORTED"
        for diagnostic in external_plan["diagnostics"]
    )
    assert any(
        diagnostic["code"] == "INSTALL_WIZARD_ENVIRONMENT_HOOK_UNSUPPORTED"
        for diagnostic in unsupported_plan["diagnostics"]
    )
    assert any(
        diagnostic["code"] == "INSTALL_WIZARD_ENVIRONMENT_HOOK_UNSUPPORTED"
        for diagnostic in requested_plugin_hook_plan["diagnostics"]
    )
    assert external_plan["install_plan"]["checks"]["environment_audit"]["environment_name"] == "WorkBuddy"
    assert "codex_plugin_entry_integrated" not in external_plan["install_plan"]["checks"]["environment_audit"]
    assert external_plan["install_plan"]["checks"]["environment_audit"]["absent_entrypoints"] == ["workbuddy.ldvh-plugin"]


def test_install_wizard_apply_blocks_non_hook_strategies(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    agent_file = repo / "AGENTS.md"

    external_result = build_install_apply(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_strategy="external_adapter_candidate",
        confirm_human_gate=True,
    )
    unsupported_result = build_install_apply(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_strategy="unsupported",
        confirm_human_gate=True,
    )

    assert external_result["summary"]["status"] == "blocked"
    assert unsupported_result["summary"]["status"] == "blocked"
    assert any(
        diagnostic["code"] == "INSTALL_WIZARD_ENVIRONMENT_HOOK_UNSUPPORTED"
        for diagnostic in external_result["diagnostics"]
    )
    assert any(
        diagnostic["code"] == "INSTALL_WIZARD_ENVIRONMENT_HOOK_UNSUPPORTED"
        for diagnostic in unsupported_result["diagnostics"]
    )
    assert not agent_file.exists()


def test_install_wizard_verify_wraps_install_verification(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    codex_home.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)

    result = build_install_verify(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
    )

    assert result["metadata"]["command"] == "verify"
    assert result["verification"]["metadata"]["authority"] == "install_verification"
    assert result["interaction_handoff"]["command"] == "verify"
    assert result["interaction_handoff"]["result_cards"][0]["id"] == "runtime_entry_lifecycle"
    assert result["interaction_handoff"]["result_cards"][1]["id"] == "commit_message_check"


def test_install_wizard_cli_plan_json(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    codex_home.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    _install_codex_v3_plugin(codex_home)

    completed = subprocess.run(
        [
            sys.executable,
            "code/install_wizard.py",
            "plan",
            "--governance-root",
            governance_root.as_posix(),
            "--ldvh-root",
            ROOT.as_posix(),
            "--repo",
            repo.as_posix(),
            "--codex-home",
            codex_home.as_posix(),
            "--environment-name",
            "Codex",
            "--environment-strategy",
            "plugin_hook",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )
    result = json.loads(completed.stdout)

    assert result["metadata"]["command"] == "plan"
    assert result["install_plan"]["environment_strategy"] == "plugin_hook"


def test_install_wizard_cli_text_includes_interaction_handoff(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    codex_home.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    _install_codex_v3_plugin(codex_home)

    completed = subprocess.run(
        [
            sys.executable,
            "code/install_wizard.py",
            "plan",
            "--governance-root",
            governance_root.as_posix(),
            "--ldvh-root",
            ROOT.as_posix(),
            "--repo",
            repo.as_posix(),
            "--codex-home",
            codex_home.as_posix(),
            "--environment-name",
            "Codex",
            "--environment-strategy",
            "plugin_hook",
            "--format",
            "text",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )

    assert "Interaction handoff:" in completed.stdout
    assert "Runtime 入口与 lifecycle 验证" in completed.stdout
    assert "提交消息检查" in completed.stdout
    assert "requires_final_confirmation" in completed.stdout


def test_install_wizard_cli_check_verify_and_apply_gate_json(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    codex_home.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    _install_codex_v3_plugin(codex_home)

    common_args = [
        "--governance-root",
        governance_root.as_posix(),
        "--ldvh-root",
        ROOT.as_posix(),
        "--repo",
        repo.as_posix(),
        "--codex-home",
        codex_home.as_posix(),
        "--environment-name",
        "Codex",
        "--environment-strategy",
        "plugin_hook",
        "--format",
        "json",
    ]
    check_completed = subprocess.run(
        [sys.executable, "code/install_wizard.py", "check", *common_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )
    verify_completed = subprocess.run(
        [
            sys.executable,
            "code/install_wizard.py",
            "verify",
            "--governance-root",
            governance_root.as_posix(),
            "--ldvh-root",
            ROOT.as_posix(),
            "--repo",
            repo.as_posix(),
            "--codex-home",
            codex_home.as_posix(),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    apply_completed = subprocess.run(
        [sys.executable, "code/install_wizard.py", "apply", *common_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )

    check_result = json.loads(check_completed.stdout)
    verify_result = json.loads(verify_completed.stdout)
    apply_result = json.loads(apply_completed.stdout)

    assert check_result["metadata"]["command"] == "check"
    assert verify_result["metadata"]["command"] == "verify"
    assert verify_completed.returncode != 0
    assert apply_completed.returncode != 0
    assert any(diagnostic["code"] == "INSTALL_WIZARD_HUMAN_GATE_REQUIRED" for diagnostic in apply_result["diagnostics"])


def test_install_wizard_cli_unknown_strategy_returns_json_diagnostic(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)

    completed = subprocess.run(
        [
            sys.executable,
            "code/install_wizard.py",
            "plan",
            "--governance-root",
            governance_root.as_posix(),
            "--ldvh-root",
            ROOT.as_posix(),
            "--repo",
            repo.as_posix(),
            "--environment-strategy",
            "surprise",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    result = json.loads(completed.stdout)

    assert completed.returncode == 1
    assert result["summary"]["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "INSTALL_WIZARD_UNKNOWN_ENVIRONMENT_STRATEGY"
    assert result["interaction_handoff"]["status"] == "blocked"
    assert result["interaction_handoff"]["machine_contract"] == "specs/10-安装与配置规范.md"


def test_install_wizard_cli_apply_reports_verification_blocking_exit_nonzero(tmp_path: Path, monkeypatch, capsys) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    codex_home = tmp_path / "codex-home"
    governance_root.mkdir()
    codex_home.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    _install_codex_v3_plugin(codex_home)

    def fake_build_install_verification(**_kwargs):
        return {
            "metadata": {"authority": "install_verification"},
            "summary": {"status": "blocked", "blocking": 1},
            "diagnostics": [
                {
                    "level": "blocking",
                    "code": "INSTALL_VERIFY_FAKE_BLOCKED",
                    "path": repo.as_posix(),
                    "message": "fake verification block",
                    "disposition": "blocking",
                }
            ],
            "source_refs": [],
        }

    monkeypatch.setattr(install_wizard, "build_install_verification", fake_build_install_verification)

    exit_code = install_wizard.main(
        [
            "apply",
            "--governance-root",
            governance_root.as_posix(),
            "--ldvh-root",
            ROOT.as_posix(),
            "--repo",
            repo.as_posix(),
            "--codex-home",
            codex_home.as_posix(),
            "--environment-name",
            "Codex",
            "--environment-strategy",
            "plugin_hook",
            "--confirm-human-gate",
            "--format",
            "json",
        ]
    )
    result = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert result["summary"]["verification_status"] == "blocked"
    assert result["summary"]["blocking"] > 0
