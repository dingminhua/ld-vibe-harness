from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

from ldvh.commits.candidate_index import prepare_commit_candidate
from ldvh.commits.contract_source import CommitContractProjection, project_commit_contract
from ldvh.commits.execution import CallerCommitApproval, execute_prepared_commit
from ldvh.git_hooks.commit_msg import (
    inspect_commit_msg_hook,
    install_commit_msg_hook,
    uninstall_commit_msg_hook,
)
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.governance.resolver import resolve_governance_scope
from ldvh.specs.repository import inspect_repository

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in (
        "GIT_COMMON_DIR",
        "GIT_CONFIG_COUNT",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_WORK_TREE",
    ):
        environment.pop(key, None)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
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
        (
            "projects:",
            "  - id: sample",
            f"    path: {project}",
            "    name: Sample",
            "    description: Temporary governed project.",
        )
        if governed
        else ("projects: []",)
    )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            (
                "product_name: Native Hook Tests",
                "product_description: Isolated native Git lifecycle tests.",
                *projects,
                "",
            )
        ),
        encoding="utf-8",
    )
    return workspace, project


def _runner(tmp_path: Path) -> Path:
    runner = tmp_path / "ldvh-git-commit-msg"
    source = shlex.quote(str(REPOSITORY_ROOT / "code"))
    executable = shlex.quote(sys.executable)
    runner.write_text(
        "\n".join(
            (
                "#!/bin/sh",
                f"PYTHONPATH={source}${{PYTHONPATH:+:$PYTHONPATH}}",
                "export PYTHONPATH",
                f'exec {executable} -X utf8 -m ldvh.hooks.commit_msg "$@"',
                "",
            )
        ),
        encoding="utf-8",
    )
    runner.chmod(0o755)
    return runner


def _install(tmp_path: Path, workspace: Path, project: Path) -> Path:
    runner = _runner(tmp_path)
    installed = install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )
    assert installed.state == "managed", installed
    assert installed.hook_path is not None
    return Path(installed.hook_path)


def _contract() -> CommitContractProjection:
    inspected = inspect_repository(REPOSITORY_ROOT)
    document = inspected.document_passing_implemented_checks_by_key("source-of-truth-traceability")
    assert document is not None
    projected = project_commit_contract(document)
    assert projected.projection is not None, projected.issues
    return projected.projection


def test_native_commit_msg_hook_blocks_invalid_message_and_allows_valid_message(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path)
    hooks_config_before = _git(project, "config", "--get-all", "core.hooksPath")
    hook = _install(tmp_path, workspace, project)

    assert hook.is_file()
    assert os.access(hook, os.X_OK)
    hooks_config_after = _git(project, "config", "--get-all", "core.hooksPath")
    assert (hooks_config_after.returncode, hooks_config_after.stdout, hooks_config_after.stderr) == (
        hooks_config_before.returncode,
        hooks_config_before.stdout,
        hooks_config_before.stderr,
    )

    (project / "change.txt").write_text("change\n", encoding="utf-8")
    _checked_git(project, "add", "change.txt")
    before = _checked_git(project, "rev-parse", "HEAD").strip()
    rejected = _git(project, "commit", "-m", "docs: invalid")

    assert rejected.returncode != 0
    assert "description_cjk_missing" in rejected.stderr
    assert _checked_git(project, "rev-parse", "HEAD").strip() == before
    assert _checked_git(project, "diff", "--cached", "--name-only") == "change.txt\n"

    accepted = _git(project, "commit", "-m", "docs: 增加提交校验")

    assert accepted.returncode == 0, accepted.stderr
    assert _checked_git(project, "rev-parse", "HEAD").strip() != before
    assert _checked_git(project, "log", "-1", "--format=%B") == "docs: 增加提交校验\n\n"


def test_native_hook_observes_the_temporary_index_used_by_internal_commit_execution(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path)
    _install(tmp_path, workspace, project)
    (project / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    governance_run = resolve_governance_scope(
        (ScopeDescriptor(0, str(project), LocatorSource.EXPLICIT_LOCATOR),),
        base=project,
        explicit_workspace_root=workspace,
    )
    assert governance_run.result is not None
    candidate = prepare_commit_candidate(
        locator=str(project),
        base=project,
        message="feat: 增加临时候选提交",
        selected_paths=("candidate.txt",),
        contract=_contract(),
        governance=governance_run.result,
    )
    assert candidate.outcome == "prepared", candidate.issues
    assert candidate.candidate is not None

    result = execute_prepared_commit(
        candidate=candidate.candidate,
        contract=_contract(),
        governance=governance_run.result,
        approval=CallerCommitApproval(True, True, True),
    )

    assert result.outcome == "created", result.issues
    assert result.actual_paths == ("candidate.txt",)


def test_native_hook_fails_closed_when_the_actual_worktree_is_not_governed(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path, governed=False)
    _install(tmp_path, workspace, project)
    (project / "change.txt").write_text("change\n", encoding="utf-8")
    _checked_git(project, "add", "change.txt")
    before = _checked_git(project, "rev-parse", "HEAD").strip()

    rejected = _git(project, "commit", "-m", "docs: 增加提交校验")

    assert rejected.returncode != 0
    assert "governance" in rejected.stderr
    assert _checked_git(project, "rev-parse", "HEAD").strip() == before


def test_install_refuses_user_hook_configured_hooks_path_and_shared_linked_worktree(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path / "user-hook")
    runner = _runner(tmp_path)
    user_hook = project / ".git" / "hooks" / "commit-msg"
    original = b"#!/bin/sh\necho user hook >&2\n"
    user_hook.write_bytes(original)
    user_hook.chmod(0o755)

    conflict = install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert conflict.state == "conflict"
    assert user_hook.read_bytes() == original

    owned_workspace, owned_project = _managed_project(tmp_path / "changed-owned-hook")
    owned_hook = _install(tmp_path, owned_workspace, owned_project)
    changed = owned_hook.read_bytes() + b"# user changed this file\n"
    owned_hook.write_bytes(changed)
    modified = install_commit_msg_hook(
        worktree=str(owned_project),
        workspace_root=str(owned_workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert modified.state == "conflict"
    assert owned_hook.read_bytes() == changed

    configured_workspace, configured_project = _managed_project(tmp_path / "configured-hooks")
    configured_directory = configured_project / ".githooks"
    configured_directory.mkdir()
    _checked_git(configured_project, "config", "core.hooksPath", ".githooks")
    configured_before = _git(configured_project, "config", "--get-all", "core.hooksPath")
    configured = install_commit_msg_hook(
        worktree=str(configured_project),
        workspace_root=str(configured_workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert configured.state == "conflict"
    assert not (configured_directory / "commit-msg").exists()
    configured_after = _git(configured_project, "config", "--get-all", "core.hooksPath")
    assert (configured_after.returncode, configured_after.stdout, configured_after.stderr) == (
        configured_before.returncode,
        configured_before.stdout,
        configured_before.stderr,
    )

    linked_workspace, main = _managed_project(tmp_path / "linked-worktree")
    linked = tmp_path / "linked-worktree" / "linked"
    _checked_git(main, "branch", "linked")
    _checked_git(main, "worktree", "add", "-q", str(linked), "linked")
    shared = install_commit_msg_hook(
        worktree=str(linked),
        workspace_root=str(linked_workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert shared.state == "conflict"
    assert not (main / ".git" / "hooks" / "commit-msg").exists()


def test_uninstall_requires_human_gate_and_only_removes_owned_hook(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path)
    hook = _install(tmp_path, workspace, project)
    pre_commit = project / ".git" / "hooks" / "pre-commit"
    pre_commit_contents = b"#!/bin/sh\nexit 0\n"
    pre_commit.write_bytes(pre_commit_contents)
    pre_commit.chmod(0o755)
    hooks_config_before = _git(project, "config", "--get-all", "core.hooksPath")

    blocked = uninstall_commit_msg_hook(worktree=str(project), human_gate_confirmed=False)

    assert blocked.state == "unavailable"
    assert hook.is_file()

    removed = uninstall_commit_msg_hook(worktree=str(project), human_gate_confirmed=True)

    assert removed.state == "absent", removed
    assert not hook.exists()
    assert pre_commit.read_bytes() == pre_commit_contents
    hooks_config_after = _git(project, "config", "--get-all", "core.hooksPath")
    assert (hooks_config_after.returncode, hooks_config_after.stdout, hooks_config_after.stderr) == (
        hooks_config_before.returncode,
        hooks_config_before.stdout,
        hooks_config_before.stderr,
    )
    assert inspect_commit_msg_hook(worktree=str(project)).state == "absent"
