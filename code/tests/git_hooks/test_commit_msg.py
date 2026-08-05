from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from ldvh.git_hooks import commit_msg
from ldvh.git_hooks.commit_msg import (
    bootstrap_commit_msg_hook,
    inspect_commit_msg_hook,
    install_commit_msg_hook,
    render_commit_msg_hook,
    uninstall_commit_msg_hook,
)
from ldvh.hooks import commit_msg as commit_msg_gate
from ldvh.hooks.commit_msg import CommitMsgGateResult

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_LAUNCHER = REPOSITORY_ROOT / "ldvh"


@pytest.fixture(autouse=True)
def _isolated_git_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for key in tuple(os.environ):
        if key in {"GIT_CONFIG_COUNT", "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"} or key.startswith(
            ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
        ):
            monkeypatch.delenv(key, raising=False)


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": "LDVH Test",
            "GIT_AUTHOR_EMAIL": "ldvh@example.invalid",
            "GIT_COMMITTER_NAME": "LDVH Test",
            "GIT_COMMITTER_EMAIL": "ldvh@example.invalid",
        }
    )
    return environment


def _git(path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", "-C", str(path), *arguments),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        env=_environment(),
    )


def _checked_git(path: Path, *arguments: str) -> str:
    completed = _git(path, *arguments)
    assert completed.returncode == 0, (arguments, completed.stdout, completed.stderr)
    return completed.stdout


def _signed(message: str) -> str:
    return (
        message
        + "\n\n关键变更:\n- 验证 common-dir Hook 对目标工作树生效"
        + "\n\nSession-ID: test-session\nAgent-ID: test-agent\nHost-Environment: test-environment"
    )


def _managed_project(tmp_path: Path, *, governed: bool = True) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _checked_git(project, "init", "-q")
    _checked_git(project, "config", "user.name", "LDVH Test")
    _checked_git(project, "config", "user.email", "ldvh@example.invalid")
    (project / "initial.txt").write_text("initial\n", encoding="utf-8")
    _checked_git(project, "add", "initial.txt")
    _checked_git(project, "commit", "-qm", "initial")
    projects = (
        ("projects:", "  - id: sample", f"    path: {project}", "    name: Sample", "    description: Hook test.")
        if governed
        else ("projects: []",)
    )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(("product_name: Hook Tests", "product_description: Common-dir Hook tests.", *projects, "")),
        encoding="utf-8",
    )
    return workspace, project


def _linked(main: Path, path: Path, branch: str) -> Path:
    _checked_git(main, "branch", branch)
    _checked_git(main, "worktree", "add", "-q", str(path), branch)
    return path


def _install(workspace: Path, project: Path):
    return install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(SOURCE_LAUNCHER),
        human_gate_confirmed=True,
    )


def _invoke_hook(worktree: Path, hook: Path, message: str, name: str) -> subprocess.CompletedProcess[str]:
    changed = worktree / f"{name}.txt"
    changed.write_text(f"{name}\n", encoding="utf-8")
    _checked_git(worktree, "add", changed.name)
    message_file = worktree.parent / f"{name}.message"
    message_file.write_text(message, encoding="utf-8")
    return subprocess.run(
        (str(hook), str(message_file)),
        cwd=worktree,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        env=_environment(),
    )


def test_install_uses_common_dir_and_covers_existing_and_future_linked_worktrees(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path)
    existing = _linked(main, tmp_path / "existing", "existing")

    installed = _install(workspace, main)

    assert installed.state == "managed", installed
    common_dir = Path(_checked_git(main, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    hook = common_dir / "hooks" / "commit-msg"
    assert installed.hook_path == str(hook)
    assert set(installed.worktree_roots) == {str(main), str(existing)}
    assert _checked_git(main, "rev-parse", "--path-format=absolute", "--git-path", "hooks").strip() == str(hook.parent)
    assert _checked_git(existing, "rev-parse", "--path-format=absolute", "--git-path", "hooks").strip() == str(
        hook.parent
    )

    assert _invoke_hook(main, hook, "docs: invalid", "main-invalid").returncode == 1
    assert _invoke_hook(existing, hook, _signed("docs: 验证既有工作树"), "existing-valid").returncode == 0

    future = _linked(main, tmp_path / "future", "future")
    assert _checked_git(future, "rev-parse", "--path-format=absolute", "--git-path", "hooks").strip() == str(
        hook.parent
    )
    assert _invoke_hook(future, hook, "docs: invalid", "future-invalid").returncode == 1
    assert _invoke_hook(future, hook, _signed("docs: 验证后续工作树"), "future-valid").returncode == 0


def test_real_git_commit_is_blocked_and_allowed_by_installed_commit_msg_hook(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path)
    installed = _install(workspace, project)
    assert installed.state == "managed", installed

    before = _checked_git(project, "rev-parse", "HEAD").strip()
    changed = project / "change.txt"
    changed.write_text("real hook event\n", encoding="utf-8")
    _checked_git(project, "add", changed.name)

    missing_body = (
        "docs: 验证单文件正文闸门\n\nSession-ID: test-session\nAgent-ID: test-agent\nHost-Environment: test-environment"
    )
    blocked = _git(project, "commit", "-m", missing_body)

    assert blocked.returncode == 1
    assert "validation/body_required" in blocked.stderr
    assert "validation/key_changes_required" in blocked.stderr
    assert "关键变更" in blocked.stderr
    assert _checked_git(project, "rev-parse", "HEAD").strip() == before
    assert _checked_git(project, "diff", "--cached", "--name-only").splitlines() == [changed.name]

    message = _signed("docs: 验证真实提交事件")
    allowed = _git(project, "commit", "-m", message)

    assert allowed.returncode == 0, (allowed.stdout, allowed.stderr)
    assert len(allowed.stderr.splitlines()) == 1
    assert re.fullmatch(
        r"LDVH Git Gate \(commit-msg\) passed: "
        r"source_fingerprint=[0-9a-f]{64} snapshot_identity=sha256:[0-9a-f]{64}",
        allowed.stderr.strip(),
    )
    after = _checked_git(project, "rev-parse", "HEAD").strip()
    assert after != before
    assert _checked_git(project, "show", "--format=", "--name-only", "HEAD").splitlines() == [changed.name]
    assert _checked_git(project, "log", "-1", "--format=%B").strip() == message
    assert _checked_git(project, "diff", "--cached", "--name-only") == ""


def test_passed_gate_without_binding_evidence_fails_closed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        commit_msg_gate,
        "run_commit_msg_gate",
        lambda **_: CommitMsgGateResult("passed", ()),
    )

    exit_code = commit_msg_gate.main(
        [
            "--workspace-root",
            "/unused-workspace",
            "--worktree",
            "/unused-worktree",
            "--message-file",
            "/unused-message",
        ]
    )

    assert exit_code == 1
    assert capsys.readouterr().err == (
        "LDVH Git Gate (commit-msg) unavailable: passed result lacks source_fingerprint or snapshot_identity\n"
    )


def test_independent_clone_does_not_inherit_common_dir_hook(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path)
    installed = _install(workspace, main)
    assert installed.state == "managed"

    clone = tmp_path / "clone"
    _checked_git(tmp_path, "clone", "-q", str(main), str(clone))
    clone_common = Path(_checked_git(clone, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())

    assert clone_common != Path(installed.git_common_dir or "")
    assert not (clone_common / "hooks" / "commit-msg").exists()


def test_git_marked_prunable_worktree_does_not_block_live_common_dir_coverage(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path)
    stale = _linked(main, tmp_path / "stale", "stale")
    shutil.rmtree(stale)
    inventory = _checked_git(main, "worktree", "list", "--porcelain")
    assert str(stale) in inventory
    assert "prunable" in inventory

    installed = _install(workspace, main)

    assert installed.state == "managed"
    assert installed.worktree_roots == (str(main),)


def test_unknown_common_hook_or_hooks_path_conflict_has_zero_writes(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path / "common")
    common = Path(_checked_git(main, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    user_hook = common / "hooks" / "commit-msg"
    original = b"#!/bin/sh\necho user >&2\n"
    user_hook.write_bytes(original)
    user_hook.chmod(0o755)

    blocked = _install(workspace, main)

    assert blocked.state == "conflict"
    assert user_hook.read_bytes() == original

    workspace2, main2 = _managed_project(tmp_path / "override")
    linked = _linked(main2, tmp_path / "override-linked", "override")
    _checked_git(main2, "config", "extensions.worktreeConfig", "true")
    custom = linked / ".custom-hooks"
    custom.mkdir()
    custom_hook = custom / "commit-msg"
    custom_hook.write_bytes(original)
    custom_hook.chmod(0o755)
    _checked_git(linked, "config", "--worktree", "core.hooksPath", ".custom-hooks")
    common2 = Path(_checked_git(main2, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())

    blocked_override = _install(workspace2, main2)

    assert blocked_override.state == "conflict"
    assert "unknown" in blocked_override.detail
    assert not (common2 / "hooks" / "commit-msg").exists()
    assert custom_hook.read_bytes() == original
    assert _checked_git(linked, "config", "--worktree", "--get", "core.hooksPath").strip() == ".custom-hooks"


def test_migrates_only_intact_ldvh_legacy_override_after_common_hook_is_prepared(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path)
    linked = _linked(main, tmp_path / "linked", "linked")
    _checked_git(main, "config", "extensions.worktreeConfig", "true")
    legacy_dir = linked / ".githooks-v4"
    legacy_dir.mkdir()
    legacy_hook = legacy_dir / "commit-msg"
    legacy_hook.write_text(
        render_commit_msg_hook(commit_msg_runner=SOURCE_LAUNCHER, workspace_root=workspace),
        encoding="utf-8",
    )
    legacy_hook.chmod(0o755)
    _checked_git(linked, "config", "--worktree", "core.hooksPath", ".githooks-v4")

    migrated = bootstrap_commit_msg_hook(
        worktree=str(main),
        workspace_root=str(workspace),
        commit_msg_runner=str(SOURCE_LAUNCHER),
        human_gate_confirmed=True,
    )

    assert migrated.state == "managed", migrated
    assert "migrated 1 legacy override" in migrated.detail
    assert _git(linked, "config", "--worktree", "--get", "core.hooksPath").returncode == 1
    assert not legacy_dir.exists()
    assert Path(migrated.hook_path or "").is_file()
    assert _invoke_hook(linked, Path(migrated.hook_path or ""), "docs: invalid", "migrated-invalid").returncode == 1


def test_preflight_failure_keeps_legacy_gate_and_configuration_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, main = _managed_project(tmp_path)
    linked = _linked(main, tmp_path / "linked", "linked")
    _checked_git(main, "config", "extensions.worktreeConfig", "true")
    legacy_dir = linked / ".githooks-v4"
    legacy_dir.mkdir()
    legacy_hook = legacy_dir / "commit-msg"
    original = render_commit_msg_hook(commit_msg_runner=SOURCE_LAUNCHER, workspace_root=workspace)
    legacy_hook.write_text(original, encoding="utf-8")
    legacy_hook.chmod(0o755)
    _checked_git(linked, "config", "--worktree", "core.hooksPath", ".githooks-v4")
    common = Path(_checked_git(main, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    monkeypatch.setattr(commit_msg, "_preflight_rendered_hook", lambda *_: "simulated preflight failure")

    blocked = _install(workspace, main)

    assert blocked.state == "unavailable"
    assert "simulated preflight failure" in blocked.detail
    assert _checked_git(linked, "config", "--worktree", "--get", "core.hooksPath").strip() == ".githooks-v4"
    assert legacy_hook.read_text(encoding="utf-8") == original
    assert not (common / "hooks" / "commit-msg").exists()


def test_second_legacy_unset_failure_restores_first_override_and_removes_common_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, main = _managed_project(tmp_path)
    linked = _linked(main, tmp_path / "linked", "linked")
    _checked_git(main, "config", "extensions.worktreeConfig", "true")
    for worktree in (main, linked):
        legacy_dir = worktree / ".githooks-v4"
        legacy_dir.mkdir()
        legacy_hook = legacy_dir / "commit-msg"
        legacy_hook.write_text(
            render_commit_msg_hook(commit_msg_runner=SOURCE_LAUNCHER, workspace_root=workspace),
            encoding="utf-8",
        )
        legacy_hook.chmod(0o755)
        _checked_git(worktree, "config", "--worktree", "core.hooksPath", ".githooks-v4")
    common = Path(_checked_git(main, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    original_run_git = commit_msg._run_git

    def fail_second_unset(worktree: Path, *arguments: str, **kwargs: object):
        if worktree == linked and arguments == ("config", "--worktree", "--unset-all", "core.hooksPath"):
            return None, "simulated second unset failure"
        return original_run_git(worktree, *arguments, **kwargs)

    monkeypatch.setattr(commit_msg, "_run_git", fail_second_unset)

    blocked = _install(workspace, main)

    assert blocked.state == "unavailable"
    assert "simulated second unset failure" in blocked.detail
    for worktree in (main, linked):
        assert _checked_git(worktree, "config", "--worktree", "--get", "core.hooksPath").strip() == ".githooks-v4"
        assert (worktree / ".githooks-v4/commit-msg").is_file()
    assert not (common / "hooks" / "commit-msg").exists()


def test_effective_directory_failure_restores_legacy_override_and_removes_common_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, main = _managed_project(tmp_path)
    linked = _linked(main, tmp_path / "linked", "linked")
    _checked_git(main, "config", "extensions.worktreeConfig", "true")
    legacy_dir = linked / ".githooks-v4"
    legacy_dir.mkdir()
    legacy_hook = legacy_dir / "commit-msg"
    legacy_hook.write_text(
        render_commit_msg_hook(commit_msg_runner=SOURCE_LAUNCHER, workspace_root=workspace),
        encoding="utf-8",
    )
    legacy_hook.chmod(0o755)
    _checked_git(linked, "config", "--worktree", "core.hooksPath", ".githooks-v4")
    common = Path(_checked_git(main, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    original_effective = commit_msg._effective_hooks_directory

    def fail_linked_effective(worktree: Path):
        if worktree == linked:
            return common / "unexpected-hooks", None
        return original_effective(worktree)

    monkeypatch.setattr(commit_msg, "_effective_hooks_directory", fail_linked_effective)

    blocked = _install(workspace, main)

    assert blocked.state == "unavailable"
    assert "did not become the effective Hook directory" in blocked.detail
    assert _checked_git(linked, "config", "--worktree", "--get", "core.hooksPath").strip() == ".githooks-v4"
    assert legacy_hook.is_file()
    assert not (common / "hooks" / "commit-msg").exists()


def test_invalid_legacy_ownership_blocks_without_touching_config(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path)
    linked = _linked(main, tmp_path / "linked", "linked")
    _checked_git(main, "config", "extensions.worktreeConfig", "true")
    legacy_dir = linked / ".githooks-v4"
    legacy_dir.mkdir()
    legacy_hook = legacy_dir / "commit-msg"
    legacy_hook.write_text("#!/bin/sh\necho unknown\n", encoding="utf-8")
    legacy_hook.chmod(0o755)
    _checked_git(linked, "config", "--worktree", "core.hooksPath", ".githooks-v4")

    blocked = _install(workspace, main)

    assert blocked.state == "conflict"
    assert _checked_git(linked, "config", "--worktree", "--get", "core.hooksPath").strip() == ".githooks-v4"
    assert legacy_hook.read_text(encoding="utf-8") == "#!/bin/sh\necho unknown\n"


def test_deployment_requires_governance_human_gate_and_no_runtime_injection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, main = _managed_project(tmp_path / "ungoverned", governed=False)
    ungovened = _install(workspace, main)
    assert ungovened.state == "conflict"
    assert "governed_single" in ungovened.detail

    workspace2, main2 = _managed_project(tmp_path / "gate")
    no_gate = install_commit_msg_hook(
        worktree=str(main2),
        workspace_root=str(workspace2),
        commit_msg_runner=str(SOURCE_LAUNCHER),
        human_gate_confirmed=False,
    )
    assert no_gate.state == "unavailable"

    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    injected = _install(workspace2, main2)
    assert injected.state == "conflict"
    monkeypatch.delenv("GIT_CONFIG_COUNT")
    common = Path(_checked_git(main2, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    assert not (common / "hooks" / "commit-msg").exists()


def test_inspect_and_uninstall_bind_exact_common_dir_deployment(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path)
    installed = _install(workspace, main)
    assert installed.state == "managed"

    inspected = inspect_commit_msg_hook(worktree=str(main))
    assert inspected.state == "managed"
    assert inspected.git_common_dir == installed.git_common_dir

    wrong_workspace = tmp_path / "wrong-workspace"
    wrong_workspace.mkdir()
    conflict = uninstall_commit_msg_hook(
        worktree=str(main),
        workspace_root=str(wrong_workspace),
        commit_msg_runner=str(SOURCE_LAUNCHER),
        human_gate_confirmed=True,
    )
    assert conflict.state == "conflict"
    assert Path(installed.hook_path or "").is_file()

    removed = uninstall_commit_msg_hook(
        worktree=str(main),
        workspace_root=str(workspace),
        commit_msg_runner=str(SOURCE_LAUNCHER),
        human_gate_confirmed=True,
    )
    assert removed.state == "absent"
    assert not Path(installed.hook_path or "").exists()


def test_installation_environment_rejects_injection_but_preserves_declared_global_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/tmp/declared-global-config")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.hooksPath")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "/tmp/injected")

    environment = commit_msg._installation_environment()

    assert environment["GIT_CONFIG_GLOBAL"] == "/tmp/declared-global-config"
    assert "GIT_CONFIG_COUNT" not in environment
    assert "GIT_CONFIG_KEY_0" not in environment
    assert "GIT_CONFIG_VALUE_0" not in environment
