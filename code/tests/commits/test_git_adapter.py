from __future__ import annotations

import os
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ldvh.commits import git_adapter
from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.validation import validate_commit
from ldvh.facts.identity import locator_from_object_uid
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


def test_git_gate_classifies_uid_locator_and_rejects_non_crockford_path() -> None:
    locator = locator_from_object_uid("spark", "0198f1c7-8a2b-7c3d-9e4f-123456789abc")

    assert git_adapter._classify_fact_path(f"ldvh-base/sparks/{locator}.yaml") == ("spark", locator)
    assert git_adapter._classify_fact_path("ldvh-base/sparks/spark-01KZXN5TXNEBSRC6HHGTBQKAI4.yaml") == ("spark", None)


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
        mechanical_triggers=("all-commits-minimum-body", "breaking-marker"),
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
        locator=".",
        base=repository,
        message=_signed("feat: 增加文件"),
        contract=_contract(),
        governance=_governance(repository),
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


def test_modified_copy_source_is_reported_once() -> None:
    paths, issue = git_adapter._parse_name_status(b"M\0source.txt\0C100\0source.txt\0extracted.txt\0")

    assert issue is None
    assert paths == ("source.txt", "extracted.txt")


def test_rename_source_map_keeps_only_rename_before_images() -> None:
    sources = git_adapter._parse_rename_source_map(
        b"R097\0old.yaml\0new.yaml\0C100\0source.yaml\0copy.yaml\0M\0other.yaml\0"
    )

    assert sources == {"new.yaml": "old.yaml"}


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


# -- specs 03 §9.9 staged fact-candidate observation ------------------------

_SPARK_PATH = "ldvh-base/sparks/spark-0001.yaml"
_SPARK_BYTES = (
    "object_id: spark-0001\n"
    "fact_type_key: spark\n"
    "title: 测试火花\n"
    "status: open\n"
    "priority: P1\n"
    "created_at: 2026-07-01T00:00:00+08:00\n"
    "updated_at: 2026-07-01T00:00:00+08:00\n"
).encode()


def _stage_file(repository: Path, path: str, content: bytes = _SPARK_BYTES) -> None:
    target = repository / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    _git(repository, "add", path)


def _signed(message: str) -> str:
    return (
        message
        + "\n\n关键变更:\n- 覆盖当前 Git adapter 测试变化"
        + "\n\nLDVH-Product-Name: Cindy\nLDVH-Model-Name: gpt-5.6-luna\nLDVH-Agent-Runtime-Name: pytest"
    )


def _observe(repository: Path, message: str = "feat: 观察事实候选") -> git_adapter.CommitCandidateObservation:
    return git_adapter.observe_commit_candidate(
        locator=".", base=repository, message=_signed(message), contract=_contract(), governance=_governance(repository)
    )


def test_snapshot_identity_changes_when_head_commit_changes_with_the_same_tree(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    before, _, before_issue = git_adapter._snapshot(repository)
    _git(repository, "commit", "--allow-empty", "-qm", "test: same tree new commit")
    after, _, after_issue = git_adapter._snapshot(repository)

    assert before_issue is None and after_issue is None
    assert before != after


def test_staged_fact_candidate_blob_is_read_by_index_oid(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    _stage_file(repository, _SPARK_PATH)
    (repository / _SPARK_PATH).write_bytes(b"tampered working tree content\n")

    observed = _observe(repository)

    assert observed.outcome == "observed"
    assert len(observed.fact_candidates) == 1
    candidate = observed.fact_candidates[0]
    assert candidate.path == _SPARK_PATH
    assert candidate.fact_type_key == "spark"
    assert candidate.object_id == "spark-0001"
    assert candidate.data == _SPARK_BYTES
    assert candidate.observation_issue is None
    assert observed.validation_input is not None
    assert observed.validation_input.fact_candidates == observed.fact_candidates


def test_deleted_fact_path_is_skipped_without_false_positive(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    _stage_file(repository, _SPARK_PATH)
    _git(repository, "commit", "-qm", "test: 建立事实基线")
    _git(repository, "rm", "-q", _SPARK_PATH)

    observed = _observe(repository)

    assert observed.outcome == "observed"
    assert observed.candidate_paths == (_SPARK_PATH,)
    assert observed.fact_candidates == ()


def test_rename_out_of_layout_is_not_a_fact_candidate(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    _stage_file(repository, _SPARK_PATH)
    _git(repository, "commit", "-qm", "test: 建立事实基线")
    _git(repository, "mv", _SPARK_PATH, "spark-0001.yaml")

    observed = _observe(repository)

    assert observed.outcome == "observed"
    assert set(observed.candidate_paths) == {_SPARK_PATH, "spark-0001.yaml"}
    assert observed.fact_candidates == ()


def test_rename_into_layout_is_observed_through_new_path(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository")
    _stage_file(repository, "drafts/spark-0001.yaml")
    _git(repository, "commit", "-qm", "test: 建立布局外基线")
    (repository / "ldvh-base/sparks").mkdir(parents=True)
    _git(repository, "mv", "drafts/spark-0001.yaml", _SPARK_PATH)

    observed = _observe(repository)

    assert observed.outcome == "observed"
    assert len(observed.fact_candidates) == 1
    candidate = observed.fact_candidates[0]
    assert candidate.path == _SPARK_PATH
    assert candidate.object_id == "spark-0001"
    assert candidate.data == _SPARK_BYTES


def test_no_fact_candidate_means_no_blob_read_and_no_index_map(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path / "repository")
    _stage_file(repository, "plain.txt", b"plain\n")
    monkeypatch.setattr(
        git_adapter, "_index_blob_map", lambda *args, **kwargs: pytest.fail("无事实候选不得解析 Index blob 映射")
    )
    monkeypatch.setattr(
        git_adapter, "_read_staged_blob", lambda *args, **kwargs: pytest.fail("无事实候选不得读取暂存 blob")
    )

    observed = _observe(repository)

    assert observed.outcome == "observed"
    assert observed.fact_candidates == ()
