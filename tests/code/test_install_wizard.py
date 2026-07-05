from __future__ import annotations

import json
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


def test_install_wizard_check_and_plan_are_read_only(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    hook_path = repo / ".git/hooks/commit-msg"

    check = build_install_check(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_strategy="plugin_hook",
    )
    plan = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
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
    assert plan["interaction_handoff"]["template"] == "specs/30-LDVH安装初始化管辖项目配置行动模板.md"
    assert plan["interaction_handoff"]["status"] == "requires_final_confirmation"
    assert plan["interaction_handoff"]["human_gate_required"] is True
    assert plan["interaction_handoff"]["planned_writes"] == 2
    assert plan["interaction_handoff"]["result_cards"][1]["id"] == "commit_message_check"
    assert plan["interaction_handoff"]["result_cards"][1]["status"] == "需安装或需升级"
    assert not hook_path.exists()


def test_install_wizard_apply_requires_human_gate_and_does_not_write(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    hook_path = repo / ".git/hooks/commit-msg"

    result = build_install_apply(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
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

    result = build_install_apply(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        codex_home=codex_home,
        environment_strategy="plugin_hook",
        confirm_human_gate=True,
    )

    assert result["apply_results"][0]["metadata"]["authority"] == "governed_project_hook_adapter"
    assert result["apply_results"][0]["summary"]["hook_installed"] is True
    hook_status = result["apply_results"][0]["hook_status"]
    assert Path(hook_status["active_hook"]).is_file()
    assert result["verification"]["metadata"]["authority"] == "install_verification"
    assert result["interaction_handoff"]["status"] == "write_completed_handoff_required"
    assert result["interaction_handoff"]["human_gate_confirmed"] is True
    assert result["interaction_handoff"]["result_cards"][0]["status"] == "需用户侧验证"
    assert result["interaction_handoff"]["result_cards"][1]["status"] == "通过"
    assert any("断点后 lifecycle 验证" in action for action in result["interaction_handoff"]["next_actions"])


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


def test_install_wizard_outputs_non_hook_environment_strategies_without_integrated_claim(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)

    thin_plan = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_strategy="thin_reference",
    )
    manual_plan = build_install_plan(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_strategy="manual_entrypoint",
    )

    assert thin_plan["install_plan"]["environment_strategy"] == "thin_reference"
    assert thin_plan["install_plan"]["planned_writes"] == []
    assert thin_plan["install_plan"]["handoff_candidates"][0]["kind"] == "thin_reference"
    assert thin_plan["install_plan"]["handoff_candidates"][0]["non_executable_in_v1"] is True
    assert thin_plan["install_plan"]["skipped_writes"][0]["kind"] == "thin_reference"
    assert manual_plan["install_plan"]["environment_strategy"] == "manual_entrypoint"
    assert manual_plan["install_plan"]["planned_writes"] == []
    assert manual_plan["install_plan"]["handoff_candidates"][0]["kind"] == "manual_entrypoint"
    assert manual_plan["install_plan"]["handoff_candidates"][0]["non_executable_in_v1"] is True
    assert manual_plan["install_plan"]["skipped_writes"][0]["kind"] == "manual_entrypoint"
    assert thin_plan["install_plan"]["checks"]["environment_audit"]["codex_plugin_entry_integrated"] is False


def test_install_wizard_apply_blocks_thin_and_manual_strategies(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    repo = tmp_path / "repo"
    governance_root.mkdir()
    _init_git_repo(repo)
    _write_governed_config(governance_root, repo)
    agent_file = repo / "AGENTS.md"

    thin_result = build_install_apply(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_strategy="thin_reference",
        confirm_human_gate=True,
    )
    manual_result = build_install_apply(
        governance_root=governance_root,
        ldvh_root=ROOT,
        repo=repo,
        environment_strategy="manual_entrypoint",
        confirm_human_gate=True,
    )

    assert thin_result["summary"]["status"] == "blocked"
    assert manual_result["summary"]["status"] == "blocked"
    assert any(
        diagnostic["code"] == "INSTALL_WIZARD_STRATEGY_APPLY_NOT_IMPLEMENTED"
        for diagnostic in thin_result["diagnostics"]
    )
    assert any(
        diagnostic["code"] == "INSTALL_WIZARD_STRATEGY_APPLY_NOT_IMPLEMENTED"
        for diagnostic in manual_result["diagnostics"]
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

    common_args = [
        "--governance-root",
        governance_root.as_posix(),
        "--ldvh-root",
        ROOT.as_posix(),
        "--repo",
        repo.as_posix(),
        "--codex-home",
        codex_home.as_posix(),
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
