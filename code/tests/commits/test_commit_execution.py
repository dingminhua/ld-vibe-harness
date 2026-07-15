from __future__ import annotations

import os
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

import ldvh.commits.candidate_index as candidate_index
import ldvh.commits.execution as execution
from ldvh.commits.candidate_index import prepare_commit_candidate
from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.execution import CallerCommitApproval, execute_prepared_commit
from ldvh.governance.git import resolve_git_identity
from ldvh.governance.models import (
    ConfigStatus,
    GovernanceScopeResult,
    GovernedVia,
    LocatorSource,
    ObjectResolution,
    ObjectStatus,
)

APPROVED = CallerCommitApproval(True, True, True)


def _git(path: Path, *arguments: str) -> str:
    environment = os.environ.copy()
    for key in ("GIT_COMMON_DIR", "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
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
    completed = subprocess.run(
        ("git", "-C", str(path), *arguments),
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return completed.stdout


def _repository(path: Path, *, commit: bool = True) -> Path:
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.name", "LDVH Test")
    _git(path, "config", "user.email", "ldvh@example.invalid")
    if commit:
        (path / "tracked.txt").write_text("initial\n", encoding="utf-8")
        _git(path, "add", "tracked.txt")
        _git(path, "commit", "-qm", "initial")
    return path


def _contract() -> CommitContractProjection:
    return CommitContractProjection(
        type_tokens=("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"),
        scope_tokens=("specs", "docs", "rules", "runtime", "code", "web", "tests", "config"),
        mechanical_triggers=("multiple-paths", "breaking-marker", "revert-type"),
        source_key="source-of-truth-traceability",
        source_path="specs/03-事实源与信息溯源规范.md",
        observed_at="2026-07-15T00:00:00+08:00",
        content_fingerprint="a" * 64,
    )


def _governance(repository: Path) -> GovernanceScopeResult:
    identity = resolve_git_identity(".", base=repository).identity
    assert identity is not None
    root = identity.worktree_root.resolve()
    resolution = ObjectResolution(
        locator_index=0,
        locator=".",
        resolved_identity=str(root),
        identity_evidence=({"kind": "working_tree", "locator": str(root)},),
        source=LocatorSource.EXPLICIT_LOCATOR,
        status=ObjectStatus.GOVERNED,
        governed_project_id="project",
        registered_project_path=str(repository.resolve()),
        governed_via=GovernedVia.GIT_COMMON_DIR,
        git_worktree_root=str(root),
        git_common_dir=str(identity.common_dir),
        source_refs=({"kind": "rule", "locator": "LDVH-GOVERNED-PROJECTS.yaml"},),
        unknown_reason=None,
    )
    return GovernanceScopeResult(
        workspace_root=str(repository.parent.resolve()),
        config_path=str((repository.parent / "LDVH-GOVERNED-PROJECTS.yaml").resolve()),
        config_status=ConfigStatus.VALID,
        object_resolutions=(resolution,),
        source_refs=({"kind": "rule", "locator": "LDVH-GOVERNED-PROJECTS.yaml"},),
    )


def _prepared(repository: Path, paths: tuple[str, ...], *, message: str = "feat: 增加提交文件"):
    governance = _governance(repository)
    result = prepare_commit_candidate(
        locator=".",
        base=repository,
        message=message,
        selected_paths=paths,
        contract=_contract(),
        governance=governance,
    )
    assert result.outcome == "prepared"
    assert result.candidate is not None
    return result.candidate, governance


def _execute(candidate, governance, *, approval: CallerCommitApproval = APPROVED):
    return execute_prepared_commit(
        candidate=candidate,
        contract=_contract(),
        governance=governance,
        approval=approval,
    )


def _hook(repository: Path, name: str, body: str) -> None:
    source = repository / ".git/hooks" / name
    source.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    source.chmod(0o755)


def test_unsupported_windows_commit_path_does_not_start_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(execution, "windows_path_problem", lambda _path: "UNC is unsupported")
    monkeypatch.setattr(
        execution.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("unsupported commit path must not start Git"),
    )

    result = execution._run_commit(tmp_path, tmp_path / "index", tmp_path / "message")

    assert isinstance(result, execution.CommitExecutionIssue)
    assert result.stage == "commit"
    assert "unsupported" in result.message


def test_unsupported_windows_index_is_rejected_before_ownership_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    candidate, _ = _prepared(repository, ("target.txt",))
    unsafe = replace(candidate, candidate_index_path=r"\\server\share\index")
    monkeypatch.setattr(
        execution,
        "windows_path_problem",
        lambda path: "UNC is unsupported" if str(path).startswith("\\\\") else None,
    )

    issue = execution._assets_owned(unsafe)

    assert issue is not None
    assert issue.stage == "ownership"
    assert "unsupported" in issue.message
    assert candidate_index.discard_prepared_candidate(candidate).outcome == "discarded"


def test_creates_and_reads_back_commit_then_aligns_real_index(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    old_head = _git(repository, "rev-parse", "HEAD").strip()
    (repository / "added.txt").write_text("added\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("added.txt",))

    result = _execute(candidate, governance)

    assert result.outcome == "created"
    assert result.commit_id == _git(repository, "rev-parse", "HEAD").strip()
    assert result.commit_id != old_head
    assert result.actual_parents == (old_head,)
    assert result.actual_tree == candidate.candidate_tree
    assert result.actual_paths == ("added.txt",)
    assert result.remaining_staged_paths == ()
    assert result.remaining_unstaged_paths == ()
    assert result.remaining_untracked_paths == ()
    assert result.cleanup_outcome == "discarded"
    assert _git(repository, "status", "--porcelain") == ""


def test_preserves_unrelated_staged_entries_after_commit(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
    _git(repository, "add", "unrelated.txt")
    unrelated_before = _git(repository, "ls-files", "--stage", "unrelated.txt")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("target.txt",))

    result = _execute(candidate, governance)

    assert result.outcome == "created"
    assert result.remaining_staged_paths == ("unrelated.txt",)
    assert _git(repository, "ls-files", "--stage", "unrelated.txt") == unrelated_before
    assert _git(repository, "diff", "--cached", "--name-only") == "unrelated.txt\n"


def test_missing_caller_approval_blocks_without_creating_commit(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    old_head = _git(repository, "rev-parse", "HEAD").strip()
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("target.txt",))

    result = _execute(candidate, governance, approval=CallerCommitApproval(True, False, True))

    assert result.outcome == "blocked"
    assert result.commit_id is None
    assert _git(repository, "rev-parse", "HEAD").strip() == old_head
    assert result.remaining_untracked_paths == ("target.txt",)
    assert result.cleanup_outcome == "discarded"


def test_worktree_drift_blocks_before_commit(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    old_head = _git(repository, "rev-parse", "HEAD").strip()
    target = repository / "tracked.txt"
    target.write_text("candidate\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("tracked.txt",), message="fix: 修正跟踪文件")
    target.write_text("changed later\n", encoding="utf-8")

    result = _execute(candidate, governance)

    assert result.outcome == "blocked"
    assert _git(repository, "rev-parse", "HEAD").strip() == old_head
    assert any(issue.stage == "preflight" for issue in result.issues)


def test_real_index_drift_blocks_and_preserves_external_stage(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    old_head = _git(repository, "rev-parse", "HEAD").strip()
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("target.txt",))
    (repository / "external.txt").write_text("external\n", encoding="utf-8")
    _git(repository, "add", "external.txt")

    result = _execute(candidate, governance)

    assert result.outcome == "blocked"
    assert _git(repository, "rev-parse", "HEAD").strip() == old_head
    assert _git(repository, "diff", "--cached", "--name-only") == "external.txt\n"


def test_rejecting_pre_commit_hook_returns_not_created(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    old_head = _git(repository, "rev-parse", "HEAD").strip()
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("target.txt",))
    _hook(repository, "pre-commit", "exit 1")

    result = _execute(candidate, governance)

    assert result.outcome == "not_created"
    assert result.commit_id is None
    assert _git(repository, "rev-parse", "HEAD").strip() == old_head
    assert result.remaining_untracked_paths == ("target.txt",)


def test_commit_message_hook_change_is_reported_as_partial(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("target.txt",))
    _hook(repository, "commit-msg", "printf '\\nHook changed message\\n' >> \"$1\"")

    result = _execute(candidate, governance)

    assert result.outcome == "partial"
    assert result.commit_id == _git(repository, "rev-parse", "HEAD").strip()
    assert result.actual_message is not None and "Hook changed message" in result.actual_message
    assert any(issue.stage == "readback" and "message" in issue.message for issue in result.issues)
    assert result.remaining_staged_paths == ()


def test_hook_candidate_expansion_is_partial_and_not_silently_aligned(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    (repository / "extra.txt").write_text("extra\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("target.txt",))
    _hook(repository, "pre-commit", "git add extra.txt")

    result = _execute(candidate, governance)

    assert result.outcome == "partial"
    assert set(result.actual_paths) == {"target.txt", "extra.txt"}
    assert any(issue.stage == "readback" and "paths" in issue.message for issue in result.issues)
    assert any(issue.stage == "index_alignment" for issue in result.issues)


def test_unborn_repository_creates_a_root_commit(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository", commit=False)
    (repository / "first.txt").write_text("first\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("first.txt",), message="feat: 建立初始提交")

    result = _execute(candidate, governance)

    assert result.outcome == "created"
    assert result.actual_parents == ()
    assert result.actual_paths == ("first.txt",)
    assert _git(repository, "status", "--porcelain") == ""


def test_linked_worktree_commit_uses_its_own_branch_and_index(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "主 repository")
    main_head = _git(repository, "rev-parse", "HEAD").strip()
    linked = tmp_path / "linked 工作树"
    _git(repository, "worktree", "add", "-qb", "linked-test", str(linked))
    (linked / "linked 中文.txt").write_text("linked\n", encoding="utf-8")
    candidate, governance = _prepared(linked, ("linked 中文.txt",))

    result = _execute(candidate, governance)

    assert result.outcome == "created"
    assert result.commit_id == _git(linked, "rev-parse", "HEAD").strip()
    assert _git(repository, "rev-parse", "HEAD").strip() == main_head
    assert _git(repository, "diff", "--cached", "--name-only") == ""
    assert _git(linked, "status", "--porcelain") == ""


def test_delete_and_rename_commit_reads_back_all_candidate_paths(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "delete.txt").write_text("delete\n", encoding="utf-8")
    _git(repository, "add", "delete.txt")
    _git(repository, "commit", "-qm", "add delete target")
    (repository / "tracked.txt").rename(repository / "renamed.txt")
    (repository / "delete.txt").unlink()
    message = "refactor: 调整提交文件\n\n关键变更:\n- 重命名并删除旧文件"
    candidate, governance = _prepared(
        repository,
        ("delete.txt", "tracked.txt", "renamed.txt"),
        message=message,
    )

    result = _execute(candidate, governance)

    assert result.outcome == "created"
    assert result.actual_paths == ("delete.txt", "tracked.txt", "renamed.txt")
    assert _git(repository, "status", "--porcelain") == ""


def test_index_alignment_failure_is_a_partial_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    candidate, governance = _prepared(repository, ("target.txt",))
    original = execution._run_git

    def fail_reset(worktree: Path, arguments: tuple[str, ...], **kwargs):
        if arguments and arguments[0] == "reset":
            return candidate_index._GitResult(1, b"", b"denied")
        return original(worktree, arguments, **kwargs)

    monkeypatch.setattr(execution, "_run_git", fail_reset)
    result = _execute(candidate, governance)

    assert result.outcome == "partial"
    assert result.commit_id == _git(repository, "rev-parse", "HEAD").strip()
    assert any(issue.stage == "index_alignment" for issue in result.issues)


def test_environment_redirects_do_not_change_commit_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _repository(tmp_path / "target")
    contaminant = _repository(tmp_path / "contaminant")
    contaminant_head = _git(contaminant, "rev-parse", "HEAD").strip()
    (target / "target.txt").write_text("target\n", encoding="utf-8")
    candidate, governance = _prepared(target, ("target.txt",))
    monkeypatch.setenv("GIT_DIR", str(contaminant / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(contaminant))
    monkeypatch.setenv("GIT_INDEX_FILE", str(contaminant / ".git/index"))

    result = _execute(candidate, governance)

    assert result.outcome == "created"
    assert _git(contaminant, "rev-parse", "HEAD").strip() == contaminant_head
    assert result.commit_id == _git(target, "rev-parse", "HEAD").strip()
