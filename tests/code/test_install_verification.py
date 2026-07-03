from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

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
    v3_shim = ROOT / CODEX_SHIM
    (hook_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup|resume",
                            "hooks": [{"type": "command", "command": f"{sys.executable} {v3_shim}"}],
                        }
                    ],
                    "PreToolUse": [
                        {
                            "matcher": "Write|Edit|apply_patch",
                            "hooks": [{"type": "command", "command": f"{sys.executable} {v3_shim}"}],
                        }
                    ],
                    "Stop": [
                        {
                            "matcher": "*",
                            "hooks": [{"type": "command", "command": f"{sys.executable} {v3_shim}"}],
                        }
                    ],
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
    assert result["summary"]["install_complete"] is True
    assert result["summary"]["environment_human_acceptance_required"] is False
    assert result["summary"]["environment_user_smoke_check_recommended"] is True
    assert result["git_hooks"][0]["summary"]["hook_installed"] is True
    assert result["git_hooks"][0]["summary"]["positive_passed"] is True
    assert result["git_hooks"][0]["summary"]["negative_blocked"] is True
    assert result["environment"]["shim_direct_tests"]["session_start_direct"]["status"] == "passed"
    assert result["environment"]["shim_direct_tests"]["pre_tool_use_direct_block"]["status"] == "passed"
    assert result["environment"]["shim_direct_tests"]["completion_claim_direct_degrade"]["status"] == "passed"
    assert result["environment"]["summary"]["environment_adapter"] == "codex_sample"
    assert result["environment"]["summary"]["target_environment_supported"] is True
    assert result["environment"]["summary"]["install_verified"] is True
    assert result["environment"]["summary"]["environment_integrated"] is False
    human_acceptance = result["environment"]["human_acceptance"]
    assert any("插件页面" in step for step in human_acceptance["steps"])
    assert any("重启 App" in step for step in human_acceptance["steps"])
    assert any("授权 / trust" in step for step in human_acceptance["steps"])
    assert any("SessionStart" in step for step in human_acceptance["steps"])
    assert any("当前 V3 shim" in criterion for criterion in human_acceptance["acceptance_criteria"])
    assert any("install_complete=true" in criterion for criterion in human_acceptance["acceptance_criteria"])
    assert any("PreToolUse 负例被阻断，正例被放行" in criterion for criterion in human_acceptance["acceptance_criteria"])
    assert result["diagnostics"] == []


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
    assert any("Trae 插件页面" in step for step in human_acceptance["steps"])
    assert any("重启 App" in step for step in human_acceptance["steps"])
    assert any("授权 / trust" in step for step in human_acceptance["steps"])
    assert any("插件命令、manifest 或入口" in criterion for criterion in human_acceptance["acceptance_criteria"])
