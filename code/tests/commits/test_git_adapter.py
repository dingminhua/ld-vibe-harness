from __future__ import annotations

import os
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ldvh.commits import git_adapter
from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.validation import validate_commit
from ldvh.governance.git import resolve_git_identity
from ldvh.governance.models import (
    ConfigStatus,
    GovernanceScopeResult,
    GovernedVia,
    LocatorSource,
    ObjectResolution,
    ObjectStatus,
)


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
    if commit:
        (path / "tracked.txt").write_text("initial\n", encoding="utf-8")
        _git(path, "add", "tracked.txt")
        _git(path, "commit", "-qm", "initial")
    return path


def test_unsupported_windows_worktree_does_not_start_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(git_adapter, "windows_path_problem", lambda _path: "UNC is unsupported")
    monkeypatch.setattr(
        git_adapter.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("unsupported worktree must not start Git"),
    )

    result = git_adapter._run_git(tmp_path, ("status",))

    assert isinstance(result, git_adapter.CommitCandidateObservationIssue)
    assert result.stage == "git_process"
    assert "unsupported" in result.message


def test_public_observe_rejects_unsupported_governance_path_before_resolve(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "repository")
    governance = _governance(repository)
    resolution = replace(
        governance.object_resolutions[0],
        git_worktree_root=str(tmp_path / "policy-rejected-worktree"),
    )
    unsafe_governance = replace(governance, object_resolutions=(resolution,))
    monkeypatch.setattr(git_adapter, "windows_path_problem", lambda _path: "UNC is unsupported")
    monkeypatch.setattr(
        git_adapter,
        "resolve_git_identity",
        lambda *args, **kwargs: pytest.fail("unsupported governance path must fail before identity resolution"),
    )

    result = git_adapter.observe_commit_candidate(
        locator=".",
        base=repository,
        message="feat: test",
        contract=_contract(),
        governance=unsafe_governance,
    )

    assert result.outcome == "unverifiable"
    assert result.issues[0].stage == "identity"
    assert "unsupported" in result.issues[0].message


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


def _governance(repository: Path, *, resolved_root: Path | None = None) -> GovernanceScopeResult:
    identity = resolve_git_identity(".", base=repository).identity
    assert identity is not None
    root = (resolved_root or identity.worktree_root).resolve()
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


def test_observes_staged_add_without_mutating_repository(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "added.txt").write_text("added\n", encoding="utf-8")
    _git(repository, "add", "added.txt")
    before_status = _git(repository, "status", "--porcelain=v2", "-z")
    before_index = _git(repository, "ls-files", "--stage", "-z")

    observed = git_adapter.observe_commit_candidate(
        locator=".", base=repository, message="feat: 增加文件", contract=_contract(), governance=_governance(repository)
    )

    assert observed.outcome == "observed"
    assert observed.candidate_paths == ("added.txt",)
    assert observed.snapshot_identity is not None and observed.snapshot_identity.startswith("sha256:")
    assert observed.validation_input is not None
    assert validate_commit(_contract(), observed.validation_input).outcome == "passed"
    assert _git(repository, "status", "--porcelain=v2", "-z") == before_status
    assert _git(repository, "ls-files", "--stage", "-z") == before_index


def test_unborn_repository_and_empty_candidate_are_observed_explicitly(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository", commit=False)
    empty = git_adapter.observe_commit_candidate(
        locator=".", base=repository, message="feat: 初始提交", contract=_contract(), governance=_governance(repository)
    )
    assert empty.outcome == "observed"
    assert empty.candidate_paths == ()
    assert empty.validation_input is not None
    assert validate_commit(_contract(), empty.validation_input).outcome == "unverifiable"

    (repository / "first.txt").write_text("first\n", encoding="utf-8")
    _git(repository, "add", "first.txt")
    staged = git_adapter.observe_commit_candidate(
        locator=".", base=repository, message="feat: 初始提交", contract=_contract(), governance=_governance(repository)
    )
    assert staged.outcome == "observed"
    assert staged.candidate_paths == ("first.txt",)


def test_rename_and_delete_preserve_actual_candidate_paths(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "delete.txt").write_text("delete\n", encoding="utf-8")
    _git(repository, "add", "delete.txt")
    _git(repository, "commit", "-qm", "add delete target")
    _git(repository, "mv", "tracked.txt", "renamed.txt")
    _git(repository, "rm", "-q", "delete.txt")

    observed = git_adapter.observe_commit_candidate(
        locator=".",
        base=repository,
        message="refactor: 调整文件\n\n关键变更:\n- 重命名并删除旧文件",
        contract=_contract(),
        governance=_governance(repository),
    )

    assert observed.outcome == "observed"
    assert observed.candidate_paths == ("delete.txt", "tracked.txt", "renamed.txt")


def test_linked_worktree_stays_bound_to_its_own_index(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    linked = tmp_path / "linked"
    _git(repository, "worktree", "add", "-qb", "linked-test", str(linked))
    (linked / "linked.txt").write_text("linked\n", encoding="utf-8")
    _git(linked, "add", "linked.txt")

    observed = git_adapter.observe_commit_candidate(
        locator=".",
        base=linked,
        message="feat: 增加链接工作树文件",
        contract=_contract(),
        governance=_governance(linked),
    )

    assert observed.outcome == "observed"
    assert observed.validation_input is not None
    assert observed.validation_input.git_worktree_root == str(linked.resolve())
    assert observed.candidate_paths == ("linked.txt",)
    assert _git(repository, "diff", "--cached", "--name-only") == ""


def test_environment_cannot_redirect_target_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _repository(tmp_path / "target")
    contaminant = _repository(tmp_path / "contaminant")
    (target / "target.txt").write_text("target\n", encoding="utf-8")
    _git(target, "add", "target.txt")
    (contaminant / "other.txt").write_text("other\n", encoding="utf-8")
    _git(contaminant, "add", "other.txt")
    monkeypatch.setenv("GIT_DIR", str(contaminant / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(contaminant))
    monkeypatch.setenv("GIT_INDEX_FILE", str(contaminant / ".git/index"))

    observed = git_adapter.observe_commit_candidate(
        locator=".", base=target, message="feat: 增加目标文件", contract=_contract(), governance=_governance(target)
    )

    assert observed.outcome == "observed"
    assert observed.candidate_paths == ("target.txt",)


def test_governance_worktree_mismatch_is_unverifiable(tmp_path: Path) -> None:
    target = _repository(tmp_path / "target")
    other = _repository(tmp_path / "other")

    observed = git_adapter.observe_commit_candidate(
        locator=".",
        base=target,
        message="feat: 修改文件",
        contract=_contract(),
        governance=_governance(target, resolved_root=other),
    )

    assert observed.outcome == "unverifiable"
    assert observed.validation_input is None
    assert observed.issues[0].stage == "governance"


def test_index_drift_during_observation_is_not_validated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "first.txt").write_text("first\n", encoding="utf-8")
    _git(repository, "add", "first.txt")
    original = git_adapter._candidate_paths

    def mutate(worktree: Path) -> tuple[tuple[str, ...], git_adapter.CommitCandidateObservationIssue | None]:
        (worktree / "second.txt").write_text("second\n", encoding="utf-8")
        _git(worktree, "add", "second.txt")
        return original(worktree)

    monkeypatch.setattr(git_adapter, "_candidate_paths", mutate)
    observed = git_adapter.observe_commit_candidate(
        locator=".", base=repository, message="feat: 增加文件", contract=_contract(), governance=_governance(repository)
    )

    assert observed.outcome == "drifted"
    assert observed.validation_input is None
    assert observed.issues[0].stage == "drift"


def test_git_read_failure_is_unverifiable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repository = _repository(tmp_path / "repository")

    def fail(worktree: Path, arguments: tuple[str, ...]) -> git_adapter.CommitCandidateObservationIssue:
        return git_adapter.CommitCandidateObservationIssue("git_process", "denied")

    monkeypatch.setattr(git_adapter, "_run_git", fail)
    observed = git_adapter.observe_commit_candidate(
        locator=".", base=repository, message="feat: 修改文件", contract=_contract(), governance=_governance(repository)
    )

    assert observed.outcome == "unverifiable"
    assert observed.validation_input is None
    assert observed.issues[0].stage == "git_process"
