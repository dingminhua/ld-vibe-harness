from __future__ import annotations

import os
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

import ldvh.commits.candidate_index as candidate_index
import ldvh.commits.git_adapter as git_adapter
from ldvh.commits.candidate_index import discard_prepared_candidate, prepare_commit_candidate
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


def _prepare(repository: Path, paths: tuple[str, ...], *, message: str = "feat: 增加候选文件"):
    return prepare_commit_candidate(
        locator=".",
        base=repository,
        message=message,
        selected_paths=paths,
        contract=_contract(),
        governance=_governance(repository),
    )


def test_prepares_exact_candidate_without_changing_real_index(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "added.txt").write_text("added\n", encoding="utf-8")
    status_before = _git(repository, "status", "--porcelain=v2", "-z")
    index_before = _git(repository, "ls-files", "--stage", "-z")

    result = _prepare(repository, ("added.txt",))

    assert result.outcome == "prepared"
    assert result.candidate is not None
    assert result.candidate_paths == ("added.txt",)
    assert validate_commit(_contract(), result.candidate.validation_input).outcome == "passed"
    assert Path(result.candidate.candidate_index_path).is_file()
    assert _git(repository, "status", "--porcelain=v2", "-z") == status_before
    assert _git(repository, "ls-files", "--stage", "-z") == index_before
    assert discard_prepared_candidate(result.candidate).outcome == "discarded"
    assert not Path(result.candidate.candidate_directory).exists()
    assert discard_prepared_candidate(result.candidate).outcome == "already_absent"


def test_unicode_space_paths_and_temporary_index_remain_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "候选 仓库")
    directory = repository / "目录 with space"
    directory.mkdir()
    target = directory / "文件 中文.txt"
    target.write_text("candidate\n", encoding="utf-8")
    candidates = tmp_path / "临时 Index 目录"
    candidates.mkdir()
    monkeypatch.setattr(candidate_index.tempfile, "tempdir", str(candidates))

    result = _prepare(repository, ("目录 with space/文件 中文.txt",))

    assert result.outcome == "prepared"
    assert result.candidate is not None
    assert result.candidate_paths == ("目录 with space/文件 中文.txt",)
    assert Path(result.candidate.candidate_directory).parent == candidates
    assert _git(repository, "diff", "--cached", "--name-only") == ""
    assert discard_prepared_candidate(result.candidate).outcome == "discarded"
    assert tuple(candidates.iterdir()) == ()


def test_preserves_unrelated_existing_staged_content(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
    _git(repository, "add", "unrelated.txt")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    index_before = _git(repository, "ls-files", "--stage", "-z")

    result = _prepare(repository, ("target.txt",))

    assert result.outcome == "prepared"
    assert result.candidate is not None
    assert result.candidate_paths == ("target.txt",)
    assert _git(repository, "diff", "--cached", "--name-only") == "unrelated.txt\n"
    assert _git(repository, "ls-files", "--stage", "-z") == index_before
    assert discard_prepared_candidate(result.candidate).outcome == "discarded"


def test_rejects_target_that_overlaps_existing_staged_content(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")
    _git(repository, "add", "tracked.txt")
    index_before = _git(repository, "ls-files", "--stage", "-z")

    result = _prepare(repository, ("tracked.txt",))

    assert result.outcome == "blocked"
    assert result.candidate is None
    assert result.issues[0].stage == "overlap"
    assert _git(repository, "ls-files", "--stage", "-z") == index_before


def test_rejects_directory_expansion_and_cleans_candidate_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "repository")
    target_directory = repository / "directory"
    target_directory.mkdir()
    (target_directory / "one.txt").write_text("one\n", encoding="utf-8")
    candidates = tmp_path / "candidates"
    candidates.mkdir()
    monkeypatch.setattr(candidate_index.tempfile, "tempdir", str(candidates))

    result = _prepare(repository, ("directory",))

    assert result.outcome == "blocked"
    assert result.candidate is None
    assert result.candidate_paths == ("directory/one.txt",)
    assert result.issues[0].stage == "candidate"
    assert tuple(candidates.iterdir()) == ()


def test_unborn_repository_uses_an_empty_tree_baseline(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository", commit=False)
    (repository / "first.txt").write_text("first\n", encoding="utf-8")

    result = _prepare(repository, ("first.txt",))

    assert result.outcome == "prepared"
    assert result.candidate is not None
    assert result.candidate.baseline_head_tree == "UNBORN"
    assert result.candidate_paths == ("first.txt",)
    assert discard_prepared_candidate(result.candidate).outcome == "discarded"


def test_delete_and_rename_form_one_exact_multi_path_candidate(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "delete.txt").write_text("delete\n", encoding="utf-8")
    _git(repository, "add", "delete.txt")
    _git(repository, "commit", "-qm", "add delete target")
    (repository / "tracked.txt").rename(repository / "renamed.txt")
    (repository / "delete.txt").unlink()
    message = "refactor: 调整候选文件\n\n关键变更:\n- 重命名并删除旧文件"

    result = _prepare(repository, ("delete.txt", "tracked.txt", "renamed.txt"), message=message)

    assert result.outcome == "prepared"
    assert result.candidate is not None
    assert result.candidate_paths == ("delete.txt", "tracked.txt", "renamed.txt")
    assert validate_commit(_contract(), result.candidate.validation_input).outcome == "passed"
    assert discard_prepared_candidate(result.candidate).outcome == "discarded"


def test_real_index_drift_blocks_preparation_and_cleans_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    (repository / "external.txt").write_text("external\n", encoding="utf-8")
    original = candidate_index._observe_index

    def mutate(**arguments):
        observed = original(**arguments)
        _git(repository, "add", "external.txt")
        return observed

    monkeypatch.setattr(candidate_index, "_observe_index", mutate)
    result = _prepare(repository, ("target.txt",))

    assert result.outcome == "blocked"
    assert result.candidate is None
    assert result.issues[0].stage == "drift"
    assert _git(repository, "diff", "--cached", "--name-only") == "external.txt\n"


def test_cleanup_refuses_a_mismatched_ownership_marker(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    result = _prepare(repository, ("target.txt",))
    assert result.candidate is not None
    marker = Path(result.candidate.candidate_directory) / ".ldvh-candidate-owner"
    marker.write_text("different", encoding="ascii")

    cleanup = discard_prepared_candidate(result.candidate)

    assert cleanup.outcome == "unsafe"
    assert Path(result.candidate.candidate_directory).exists()
    marker.write_text(result.candidate.ownership_token, encoding="ascii")
    assert discard_prepared_candidate(result.candidate).outcome == "discarded"


def test_environment_cannot_redirect_candidate_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _repository(tmp_path / "target")
    contaminant = _repository(tmp_path / "contaminant")
    (target / "target.txt").write_text("target\n", encoding="utf-8")
    monkeypatch.setenv("GIT_DIR", str(contaminant / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(contaminant))
    monkeypatch.setenv("GIT_INDEX_FILE", str(contaminant / ".git/index"))

    result = _prepare(target, ("target.txt",))

    assert result.outcome == "prepared"
    assert result.candidate is not None
    assert result.candidate.worktree_root == str(target.resolve())
    assert result.candidate_paths == ("target.txt",)
    assert discard_prepared_candidate(result.candidate).outcome == "discarded"


@pytest.mark.parametrize("path", ("", ".", "../outside", "/absolute", "a\\b"))
def test_invalid_target_path_is_blocked_before_assets_are_created(tmp_path: Path, path: str) -> None:
    repository = _repository(tmp_path / "repository")

    result = _prepare(repository, (path,))

    assert result.outcome == "blocked"
    assert result.candidate is None
    assert result.issues[0].stage == "input"


def test_unsupported_windows_git_path_does_not_start_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(candidate_index, "windows_path_problem", lambda _path: "UNC is unsupported")
    monkeypatch.setattr(
        candidate_index.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("unsupported candidate path must not start Git"),
    )

    result = candidate_index._run_git(tmp_path, ("status",))

    assert isinstance(result, candidate_index.CandidatePreparationIssue)
    assert result.stage == "temporary_index"
    assert "unsupported" in result.message


def test_public_prepare_rejects_unsupported_governance_path_before_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "repository")
    governance = _governance(repository)
    unsafe_resolution = replace(
        governance.object_resolutions[0],
        git_worktree_root=str(tmp_path / "policy-rejected-worktree"),
    )
    unsafe_governance = replace(governance, object_resolutions=(unsafe_resolution,))
    monkeypatch.setattr(git_adapter, "windows_path_problem", lambda _path: "UNC is unsupported")
    monkeypatch.setattr(
        candidate_index,
        "_create_candidate_assets",
        lambda: pytest.fail("unsupported governance path must fail before candidate assets"),
    )

    result = prepare_commit_candidate(
        locator=".",
        base=repository,
        message="feat: test",
        selected_paths=("target.txt",),
        contract=_contract(),
        governance=unsafe_governance,
    )

    assert result.outcome == "unverifiable"
    assert result.issues[0].stage == "baseline"


def test_unsupported_windows_temp_environment_fails_before_gettempdir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEMP", r"\\server\share\temp")
    monkeypatch.setattr(
        candidate_index,
        "windows_path_problem",
        lambda path: "UNC is unsupported" if str(path).startswith("\\\\") else None,
    )
    monkeypatch.setattr(
        candidate_index.tempfile,
        "gettempdir",
        lambda: pytest.fail("unsupported TEMP must fail before tempfile probing"),
    )

    directory, index, token, issue = candidate_index._create_candidate_assets()

    assert (directory, index, token) == (Path(), Path(), "")
    assert issue is not None and issue.stage == "temporary_index"


def test_unsupported_windows_cleanup_path_is_rejected_before_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(candidate_index, "windows_path_problem", lambda _path: "UNC is unsupported")

    result = candidate_index._discard_assets(Path("unused"), Path("unused/index"), "token")

    assert result is not None
    assert result.stage == "cleanup"
    assert "unsupported" in result.message


def test_public_discard_rejects_unsupported_windows_path_before_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    result = _prepare(repository, ("target.txt",))
    assert result.candidate is not None
    unsafe = replace(
        result.candidate,
        candidate_directory=r"\\server\share\candidate",
        candidate_index_path=r"\\server\share\candidate\index",
    )

    with monkeypatch.context() as context:
        context.setattr(
            candidate_index,
            "windows_path_problem",
            lambda path: "UNC is unsupported" if str(path).startswith("\\\\") else None,
        )
        context.setattr(Path, "exists", lambda _self: pytest.fail("unsupported path must not be observed"))
        cleanup = discard_prepared_candidate(unsafe)

    assert cleanup.outcome == "unsafe"
    assert cleanup.issues[0].stage == "cleanup"
    assert discard_prepared_candidate(result.candidate).outcome == "discarded"
