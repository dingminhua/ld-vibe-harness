from __future__ import annotations

from pathlib import Path
import subprocess

from install_verification import build_install_verification


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


def test_install_verification_runs_git_hook_positive_negative_and_marks_environment_review_required(tmp_path: Path) -> None:
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
    assert result["summary"]["git_hooks_ok"] is True
    assert result["summary"]["install_complete"] is False
    assert result["summary"]["environment_human_acceptance_required"] is True
    assert result["git_hooks"][0]["summary"]["hook_installed"] is True
    assert result["git_hooks"][0]["summary"]["positive_passed"] is True
    assert result["git_hooks"][0]["summary"]["negative_blocked"] is True
    assert result["environment"]["shim_direct_tests"]["session_start_direct"]["status"] == "passed"
    assert result["environment"]["shim_direct_tests"]["pre_tool_use_direct_block"]["status"] == "passed"
    assert result["environment"]["shim_direct_tests"]["completion_claim_direct_degrade"]["status"] == "passed"
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
