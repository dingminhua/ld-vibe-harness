from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from ldvh.governance.git import resolve_git_identity


def _git(path: Path, *arguments: str) -> str:
    environment = os.environ.copy()
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
    completed = subprocess.run(
        ["git", "-C", str(path), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return completed.stdout.strip()


def _repository(path: Path) -> Path:
    path.mkdir()
    _git(path, "init", "-q")
    (path / "tracked.txt").write_text("initial\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-qm", "initial")
    return path


def test_resolves_files_directories_and_uncreated_paths_without_losing_locator(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    untracked = repository / "untracked.txt"
    untracked.write_text("working tree\n", encoding="utf-8")

    tracked = resolve_git_identity("tracked.txt", base=str(repository))
    uncreated = resolve_git_identity("future/nested/file.txt", base=repository)
    untracked_result = resolve_git_identity(str(untracked), base="ignored-for-absolute-path")

    assert tracked.status == untracked_result.status == uncreated.status == "git_worktree"
    assert tracked.path.original_locator == "tracked.txt"
    assert tracked.path.original_base == str(repository)
    assert tracked.path.probe_path == repository.resolve()
    assert uncreated.path.absolute_path == repository / "future/nested/file.txt"
    assert uncreated.path.real_path == repository / "future/nested/file.txt"
    assert uncreated.path.probe_path == repository.resolve()
    assert uncreated.path.exists is False
    assert uncreated.path.probe_uses_existing_ancestor is True
    assert tracked.identity is not None
    assert tracked.identity.worktree_root == repository.resolve()


def test_main_and_linked_worktrees_share_common_dir_but_keep_distinct_roots(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    linked = tmp_path / "linked"
    _git(repository, "worktree", "add", "-qb", "linked-test", str(linked))

    main_result = resolve_git_identity(".", base=repository)
    linked_result = resolve_git_identity(".", base=linked)

    assert main_result.identity is not None
    assert linked_result.identity is not None
    assert main_result.identity.common_dir == linked_result.identity.common_dir
    assert main_result.identity.worktree_root == repository.resolve()
    assert linked_result.identity.worktree_root == linked.resolve()
    assert main_result.identity.git_dir != linked_result.identity.git_dir


def test_branch_switch_and_detached_head_do_not_change_identity(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    initial = resolve_git_identity(".", base=repository)
    _git(repository, "switch", "-qc", "other")
    switched = resolve_git_identity(".", base=repository)
    _git(repository, "checkout", "-q", "--detach", "HEAD")
    detached = resolve_git_identity(".", base=repository)

    assert initial.identity == switched.identity == detached.identity


def test_independent_clone_with_same_remote_has_different_common_dir(tmp_path: Path) -> None:
    source = _repository(tmp_path / "source")
    first_clone = tmp_path / "first-clone"
    second_clone = tmp_path / "second-clone"
    _git(tmp_path, "clone", "-q", str(source), str(first_clone))
    _git(tmp_path, "clone", "-q", str(source), str(second_clone))

    first_result = resolve_git_identity(".", base=first_clone)
    second_result = resolve_git_identity(".", base=second_clone)

    assert first_result.identity is not None
    assert second_result.identity is not None
    assert _git(first_clone, "remote", "get-url", "origin") == _git(second_clone, "remote", "get-url", "origin")
    assert first_result.identity.common_dir != second_result.identity.common_dir


def test_submodule_uses_its_own_git_boundary(tmp_path: Path) -> None:
    child = _repository(tmp_path / "child")
    parent = _repository(tmp_path / "parent")
    _git(parent, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(child), "vendor/child")
    submodule = parent / "vendor/child"

    parent_result = resolve_git_identity(".", base=parent)
    child_result = resolve_git_identity(".", base=submodule)

    assert parent_result.identity is not None
    assert child_result.identity is not None
    assert child_result.identity.worktree_root == submodule.resolve()
    assert child_result.identity.common_dir != parent_result.identity.common_dir


def test_bare_repository_and_plain_directory_are_deterministic_non_worktrees(tmp_path: Path) -> None:
    bare = tmp_path / "bare.git"
    bare.mkdir()
    _git(bare, "init", "--bare", "-q")
    plain = tmp_path / "plain"
    plain.mkdir()

    bare_result = resolve_git_identity(".", base=bare)
    plain_result = resolve_git_identity(".", base=plain)

    assert bare_result.status == "not_git_worktree"
    assert bare_result.non_worktree_reason == "bare_repository"
    assert plain_result.status == "not_git_worktree"
    assert plain_result.non_worktree_reason == "not_a_git_repository"


def test_symlinks_are_resolved_before_git_observation(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    plain = tmp_path / "plain"
    plain.mkdir()
    link_in = tmp_path / "link-in"
    link_out = repository / "link-out"
    link_in.symlink_to(repository, target_is_directory=True)
    link_out.symlink_to(plain, target_is_directory=True)

    inward = resolve_git_identity(".", base=link_in)
    outward = resolve_git_identity("link-out", base=repository)

    assert inward.status == "git_worktree"
    assert inward.path.real_path == repository.resolve()
    assert outward.status == "not_git_worktree"
    assert outward.path.real_path == plain.resolve()


def test_symlink_loop_is_a_technical_failure(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.symlink_to(second)
    second.symlink_to(first)

    result = resolve_git_identity(str(first), base=tmp_path)

    assert result.status == "technical_failure"
    assert result.failure is not None
    assert result.failure.stage == "path"


def test_git_identity_environment_does_not_override_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _repository(tmp_path / "target")
    contaminant = _repository(tmp_path / "contaminant")
    monkeypatch.setenv("GIT_DIR", str(contaminant / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(contaminant))
    monkeypatch.setenv("GIT_COMMON_DIR", str(contaminant / ".git"))

    result = resolve_git_identity(".", base=target)

    assert result.status == "git_worktree"
    assert result.identity is not None
    assert result.identity.worktree_root == target.resolve()
    assert result.identity.common_dir == (target / ".git").resolve()


@pytest.mark.parametrize("error", [FileNotFoundError("missing git"), PermissionError("denied")])
def test_process_start_failures_are_technical_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: OSError,
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise error

    monkeypatch.setattr(subprocess, "run", fail)

    result = resolve_git_identity(".", base=tmp_path)

    assert result.status == "technical_failure"
    assert result.failure is not None
    assert result.failure.stage in {"git_dependency", "git_process"}


def test_unrecognized_git_failure_is_not_reported_as_non_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=[],
            returncode=128,
            stdout="",
            stderr="fatal: detected dubious ownership",
        )

    monkeypatch.setattr(subprocess, "run", fail)

    result = resolve_git_identity(".", base=tmp_path)

    assert result.status == "technical_failure"
    assert result.failure is not None
    assert result.failure.stage == "git_process"


def test_git_probe_timeout_is_a_bounded_technical_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        assert kwargs["timeout"] == 10
        raise subprocess.TimeoutExpired(cmd="git", timeout=10)

    monkeypatch.setattr(subprocess, "run", timeout)

    result = resolve_git_identity(".", base=tmp_path)

    assert result.status == "technical_failure"
    assert result.failure is not None
    assert result.failure.stage == "git_process"
    assert result.failure.summary == "Git identity probe timed out"
