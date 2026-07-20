"""Create and read back one local commit from an approved prepared candidate."""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from ldvh.commits.candidate_index import (
    PreparedCommitCandidate,
    _head_identity,
    _index_identity,
    _run_git,
    discard_prepared_candidate,
)
from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.git_adapter import _observe_index, _parse_name_status, observe_commit_candidate
from ldvh.commits.validation import validate_commit
from ldvh.governance.git import windows_path_problem
from ldvh.governance.models import GovernanceScopeResult

_GIT_TIMEOUT_SECONDS = 120
_OWNER_MARKER = ".ldvh-candidate-owner"
_MESSAGE_NAME = "message"

ExecutionStage = Literal[
    "approval",
    "ownership",
    "preflight",
    "mechanical_validation",
    "commit",
    "readback",
    "index_alignment",
    "cleanup",
]


@dataclass(frozen=True, slots=True)
class CallerCommitApproval:
    """Caller assertions used only as execution guards, never as authorization evidence."""

    human_authorization_confirmed: bool
    semantic_review_confirmed: bool
    validation_coverage_confirmed: bool


@dataclass(frozen=True, slots=True)
class CommitExecutionIssue:
    stage: ExecutionStage
    message: str


@dataclass(frozen=True, slots=True)
class CommitExecutionResult:
    outcome: Literal["blocked", "not_created", "created", "partial"]
    commit_id: str | None
    actual_tree: str | None
    actual_parents: tuple[str, ...]
    actual_message: str | None
    actual_paths: tuple[str, ...]
    real_index_before: str
    real_index_after: str | None
    remaining_staged_paths: tuple[str, ...]
    remaining_unstaged_paths: tuple[str, ...]
    remaining_untracked_paths: tuple[str, ...]
    cleanup_outcome: Literal["discarded", "already_absent", "unsafe"]
    issues: tuple[CommitExecutionIssue, ...]


@dataclass(frozen=True, slots=True)
class _GitResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def _issue(stage: ExecutionStage, message: str) -> CommitExecutionIssue:
    return CommitExecutionIssue(stage, message)


def _commit_environment(index_path: Path) -> dict[str, str]:
    blocked = {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_DIR",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_WORK_TREE",
    }
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in blocked
        and key != "GIT_CONFIG_COUNT"
        and not key.startswith("GIT_CONFIG_KEY_")
        and not key.startswith("GIT_CONFIG_VALUE_")
    }
    environment.update(
        {
            "GIT_INDEX_FILE": str(index_path),
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        }
    )
    return environment


def _run_commit(worktree: Path, index_path: Path, message_path: Path) -> _GitResult | CommitExecutionIssue:
    path_problem = next(
        (
            problem
            for path in (worktree, index_path, message_path)
            if (problem := windows_path_problem(path)) is not None
        ),
        None,
    )
    if path_problem is not None:
        return _issue("commit", f"Git path is unsupported on Windows: {path_problem}")
    try:
        completed = subprocess.run(
            (
                "git",
                "--no-optional-locks",
                "-C",
                str(worktree),
                "commit",
                "--file",
                str(message_path),
                "--cleanup=verbatim",
                "--no-status",
            ),
            check=False,
            capture_output=True,
            env=_commit_environment(index_path),
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        return _issue("commit", f"Git executable is unavailable: {error}")
    except OSError as error:
        return _issue("commit", f"Git commit process could not be started: {error}")
    except subprocess.TimeoutExpired:
        return _issue("commit", f"Git commit exceeded {_GIT_TIMEOUT_SECONDS} seconds")
    return _GitResult(completed.returncode, completed.stdout, completed.stderr)


def _assets_owned(candidate: PreparedCommitCandidate) -> CommitExecutionIssue | None:
    directory = Path(candidate.candidate_directory)
    index_path = Path(candidate.candidate_index_path)
    path_problem = (
        windows_path_problem(candidate.worktree_root)
        or windows_path_problem(directory)
        or windows_path_problem(index_path)
    )
    if path_problem is not None:
        return _issue("ownership", f"Prepared candidate path is unsupported on Windows: {path_problem}")
    marker = directory / _OWNER_MARKER
    try:
        if (
            not directory.is_dir()
            or not directory.name.startswith("ldvh-commit-candidate-")
            or directory.parent != Path(tempfile.gettempdir()).resolve()
            or index_path != directory / "index"
            or not index_path.is_file()
            or not marker.is_file()
            or marker.read_text(encoding="ascii") != candidate.ownership_token
        ):
            return _issue("ownership", "Prepared candidate assets or ownership marker do not match")
    except OSError as error:
        return _issue("ownership", f"Prepared candidate ownership could not be read: {error}")
    return None


def _path_records(worktree: Path) -> tuple[tuple[bytes, ...], CommitExecutionIssue | None]:
    result = _run_git(worktree, ("ls-files", "--stage", "-z"))
    if not hasattr(result, "returncode"):
        return (), _issue("index_alignment", "The real Index could not be read")
    if result.returncode != 0:
        details = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        return (), _issue("index_alignment", f"The real Index read failed: {details or result.returncode}")
    records = tuple(record for record in result.stdout.split(b"\0") if record)
    if any(b"\t" not in record for record in records):
        return (), _issue("index_alignment", "The real Index returned malformed stage records")
    return records, None


def _without_selected(records: tuple[bytes, ...], selected_paths: tuple[str, ...]) -> tuple[bytes, ...]:
    selected = {path.encode("utf-8") for path in selected_paths}
    return tuple(record for record in records if record.split(b"\t", 1)[1] not in selected)


def _read_commit(
    worktree: Path,
    commit_id: str,
) -> tuple[str | None, tuple[str, ...], str | None, tuple[CommitExecutionIssue, ...]]:
    result = _run_git(worktree, ("cat-file", "commit", commit_id))
    if not hasattr(result, "returncode"):
        return None, (), None, (_issue("readback", "The created commit could not be read"),)
    if result.returncode != 0:
        details = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        return None, (), None, (_issue("readback", f"Commit read failed: {details or result.returncode}"),)
    if b"\n\n" not in result.stdout:
        return None, (), None, (_issue("readback", "Commit object does not contain a message boundary"),)
    header, raw_message = result.stdout.split(b"\n\n", 1)
    tree: str | None = None
    parents: list[str] = []
    try:
        for line in header.decode("ascii").splitlines():
            if line.startswith("tree "):
                tree = line.removeprefix("tree ")
            elif line.startswith("parent "):
                parents.append(line.removeprefix("parent "))
        message = raw_message.decode("utf-8")
    except UnicodeDecodeError:
        return tree, tuple(parents), None, (_issue("readback", "Commit metadata or message is not decodable"),)
    if tree is None:
        return None, tuple(parents), message, (_issue("readback", "Commit object does not identify its tree"),)
    return tree, tuple(parents), message, ()


def _commit_paths(worktree: Path, commit_id: str) -> tuple[tuple[str, ...], CommitExecutionIssue | None]:
    result = _run_git(
        worktree,
        ("diff-tree", "--root", "--no-commit-id", "--name-status", "-z", "-r", "-M", "-C", commit_id),
    )
    if not hasattr(result, "returncode"):
        return (), _issue("readback", "Created commit paths could not be read")
    if result.returncode != 0:
        details = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        return (), _issue("readback", f"Created commit path read failed: {details or result.returncode}")
    paths, failure = _parse_name_status(result.stdout)
    if failure is not None:
        return (), _issue("readback", failure.message)
    return paths, None


def _path_list(worktree: Path, arguments: tuple[str, ...]) -> tuple[tuple[str, ...], CommitExecutionIssue | None]:
    result = _run_git(worktree, arguments)
    if not hasattr(result, "returncode"):
        return (), _issue("readback", "Remaining Git paths could not be read")
    if result.returncode != 0:
        details = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        return (), _issue("readback", f"Remaining Git path read failed: {details or result.returncode}")
    try:
        paths = tuple(path for path in result.stdout.decode("utf-8").split("\0") if path)
    except UnicodeDecodeError:
        return (), _issue("readback", "Remaining Git paths are not valid UTF-8")
    return paths, None


def _remaining_paths(
    worktree: Path,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[CommitExecutionIssue, ...]]:
    staged, staged_issue = _path_list(worktree, ("diff", "--cached", "--name-only", "-z", "--no-ext-diff"))
    unstaged, unstaged_issue = _path_list(worktree, ("diff", "--name-only", "-z", "--no-ext-diff"))
    untracked, untracked_issue = _path_list(worktree, ("ls-files", "--others", "--exclude-standard", "-z"))
    issues = tuple(issue for issue in (staged_issue, unstaged_issue, untracked_issue) if issue is not None)
    return staged, unstaged, untracked, issues


def _finish(
    *,
    outcome: Literal["blocked", "not_created", "created", "partial"],
    candidate: PreparedCommitCandidate,
    issues: list[CommitExecutionIssue],
    commit_id: str | None = None,
    actual_tree: str | None = None,
    actual_parents: tuple[str, ...] = (),
    actual_message: str | None = None,
    actual_paths: tuple[str, ...] = (),
    real_index_after: str | None = None,
) -> CommitExecutionResult:
    worktree = Path(candidate.worktree_root)
    staged, unstaged, untracked, remaining_issues = _remaining_paths(worktree)
    issues.extend(remaining_issues)
    cleanup = discard_prepared_candidate(candidate)
    if cleanup.outcome == "unsafe":
        issues.extend(_issue("cleanup", issue.message) for issue in cleanup.issues)
        if outcome == "created":
            outcome = "partial"
    return CommitExecutionResult(
        outcome=outcome,
        commit_id=commit_id,
        actual_tree=actual_tree,
        actual_parents=actual_parents,
        actual_message=actual_message,
        actual_paths=actual_paths,
        real_index_before=candidate.baseline_index_identity,
        real_index_after=real_index_after,
        remaining_staged_paths=staged,
        remaining_unstaged_paths=unstaged,
        remaining_untracked_paths=untracked,
        cleanup_outcome=cleanup.outcome,
        issues=tuple(issues),
    )


def execute_prepared_commit(
    *,
    candidate: PreparedCommitCandidate,
    contract: CommitContractProjection,
    governance: GovernanceScopeResult,
    approval: CallerCommitApproval,
) -> CommitExecutionResult:
    """Create one commit after rechecking all mechanical inputs and caller assertions."""

    issues: list[CommitExecutionIssue] = []
    if not all(
        (
            approval.human_authorization_confirmed,
            approval.semantic_review_confirmed,
            approval.validation_coverage_confirmed,
        )
    ):
        issues.append(_issue("approval", "All caller approval guards must be explicitly confirmed"))
        return _finish(outcome="blocked", candidate=candidate, issues=issues)
    ownership_issue = _assets_owned(candidate)
    if ownership_issue is not None:
        issues.append(ownership_issue)
        return _finish(outcome="blocked", candidate=candidate, issues=issues)

    mechanical = validate_commit(contract, candidate.validation_input)
    if mechanical.outcome != "passed":
        details = "; ".join(f"{item.code}: {item.message}" for item in mechanical.issues)
        issues.append(_issue("mechanical_validation", f"Commit contract did not pass: {details or mechanical.outcome}"))
        return _finish(outcome="blocked", candidate=candidate, issues=issues)

    worktree = Path(candidate.worktree_root)
    index_path = Path(candidate.candidate_index_path)
    candidate_now = _observe_index(
        worktree=worktree,
        message=candidate.validation_input.message,
        contract=contract,
        governance=governance,
        index_file=index_path,
    )
    if (
        candidate_now.outcome != "observed"
        or candidate_now.validation_input != candidate.validation_input
        or candidate_now.snapshot_identity != candidate.candidate_snapshot_identity
        or candidate_now.candidate_paths != candidate.candidate_paths
    ):
        issues.append(_issue("preflight", "Prepared candidate identity changed before commit"))
        return _finish(outcome="blocked", candidate=candidate, issues=issues)

    baseline_now = observe_commit_candidate(
        locator=".",
        base=worktree,
        message=candidate.validation_input.message,
        contract=contract,
        governance=governance,
    )
    head_commit, head_tree, head_failure = _head_identity(worktree)
    index_identity, index_failure = _index_identity(worktree)
    if (
        baseline_now.outcome != "observed"
        or baseline_now.snapshot_identity != candidate.baseline_snapshot_identity
        or head_failure is not None
        or head_commit != candidate.baseline_head_commit
        or head_tree != candidate.baseline_head_tree
        or index_failure is not None
        or index_identity != candidate.baseline_index_identity
    ):
        issues.append(_issue("preflight", "HEAD or the real Index changed after candidate preparation"))
        return _finish(outcome="blocked", candidate=candidate, issues=issues, real_index_after=index_identity or None)

    worktree_diff = _run_git(
        worktree,
        ("diff", "--quiet", "--no-ext-diff", "--", *candidate.selected_paths),
        index_file=index_path,
        literal_paths=True,
    )
    if not hasattr(worktree_diff, "returncode") or worktree_diff.returncode != 0:
        message = "Selected Working Tree paths changed after candidate preparation"
        if hasattr(worktree_diff, "returncode") and worktree_diff.returncode not in {0, 1}:
            details = (worktree_diff.stderr or worktree_diff.stdout).decode("utf-8", errors="replace").strip()
            message = f"Selected Working Tree comparison failed: {details or worktree_diff.returncode}"
        issues.append(_issue("preflight", message))
        return _finish(outcome="blocked", candidate=candidate, issues=issues, real_index_after=index_identity)

    tree_result = _run_git(worktree, ("write-tree",), index_file=index_path)
    if not hasattr(tree_result, "returncode") or tree_result.returncode != 0:
        issues.append(_issue("preflight", "Prepared candidate tree could not be re-read"))
        return _finish(outcome="blocked", candidate=candidate, issues=issues, real_index_after=index_identity)
    try:
        tree_now = tree_result.stdout.decode("ascii").strip()
    except UnicodeDecodeError:
        tree_now = ""
    if tree_now != candidate.candidate_tree:
        issues.append(_issue("preflight", "Prepared candidate tree changed before commit"))
        return _finish(outcome="blocked", candidate=candidate, issues=issues, real_index_after=index_identity)

    message = candidate.validation_input.message
    assert message is not None
    message_path = Path(candidate.candidate_directory) / _MESSAGE_NAME
    try:
        message_path.write_text(message, encoding="utf-8", newline="\n")
    except OSError as error:
        issues.append(_issue("commit", f"Commit message file could not be written: {error}"))
        return _finish(outcome="not_created", candidate=candidate, issues=issues, real_index_after=index_identity)

    commit_result = _run_commit(worktree, index_path, message_path)
    new_head, _, new_head_failure = _head_identity(worktree)
    if new_head_failure is not None or new_head in {candidate.baseline_head_commit, "UNBORN", ""}:
        if isinstance(commit_result, CommitExecutionIssue):
            issues.append(commit_result)
        else:
            details = (commit_result.stderr or commit_result.stdout).decode("utf-8", errors="replace").strip()
            issues.append(_issue("commit", f"Git did not create a new commit: {details or commit_result.returncode}"))
        current_index, _ = _index_identity(worktree)
        return _finish(
            outcome="not_created",
            candidate=candidate,
            issues=issues,
            real_index_after=current_index or None,
        )

    commit_id = new_head
    if isinstance(commit_result, CommitExecutionIssue):
        issues.append(commit_result)
    elif commit_result.returncode != 0:
        details = (commit_result.stderr or commit_result.stdout).decode("utf-8", errors="replace").strip()
        issues.append(
            _issue("commit", f"Git returned failure after HEAD changed: {details or commit_result.returncode}")
        )

    actual_tree, actual_parents, actual_message, read_issues = _read_commit(worktree, commit_id)
    issues.extend(read_issues)
    actual_paths, path_issue = _commit_paths(worktree, commit_id)
    if path_issue is not None:
        issues.append(path_issue)
    expected_parents = () if candidate.baseline_head_commit == "UNBORN" else (candidate.baseline_head_commit,)
    tree_matches = actual_tree == candidate.candidate_tree
    paths_match = len(actual_paths) == len(candidate.candidate_paths) and set(actual_paths) == set(
        candidate.candidate_paths
    )
    message_matches = False
    if actual_message is not None:
        actual_input = replace(candidate.validation_input, message=actual_message, candidate_paths=actual_paths)
        actual_validation = validate_commit(contract, actual_input)
        message_matches = (
            actual_validation.outcome == "passed"
            and actual_validation.normalized_message == mechanical.normalized_message
        )
    if not tree_matches:
        issues.append(_issue("readback", "Created commit tree differs from the approved candidate tree"))
    if actual_parents != expected_parents:
        issues.append(_issue("readback", "Created commit parent differs from the prepared HEAD"))
    if not paths_match:
        issues.append(_issue("readback", "Created commit paths differ from the approved candidate paths"))
    if not message_matches:
        issues.append(_issue("readback", "Created commit message differs from the approved normalized message"))

    index_before_alignment, index_read_issue = _index_identity(worktree)
    if index_read_issue is not None:
        issues.append(_issue("index_alignment", index_read_issue.message))
    index_records_before, record_issue = _path_records(worktree)
    if record_issue is not None:
        issues.append(record_issue)
    can_align = (
        tree_matches
        and paths_match
        and index_read_issue is None
        and index_before_alignment == candidate.baseline_index_identity
        and record_issue is None
    )
    index_after_alignment = index_before_alignment or None
    if can_align:
        unaffected_before = _without_selected(index_records_before, candidate.selected_paths)
        alignment = _run_git(
            worktree,
            ("reset", "-q", "HEAD", "--", *candidate.selected_paths),
            literal_paths=True,
        )
        if not hasattr(alignment, "returncode") or alignment.returncode != 0:
            issues.append(_issue("index_alignment", "The real Index could not be aligned to the created commit"))
        else:
            records_after, after_issue = _path_records(worktree)
            if after_issue is not None:
                issues.append(after_issue)
            elif _without_selected(records_after, candidate.selected_paths) != unaffected_before:
                issues.append(_issue("index_alignment", "Unrelated staged entries changed during Index alignment"))
            index_after_alignment, after_identity_issue = _index_identity(worktree)
            if after_identity_issue is not None:
                issues.append(_issue("index_alignment", after_identity_issue.message))
    else:
        issues.append(_issue("index_alignment", "The real Index was not aligned because safe preconditions failed"))

    complete = (
        not issues
        and tree_matches
        and actual_parents == expected_parents
        and paths_match
        and message_matches
        and index_after_alignment is not None
    )
    return _finish(
        outcome="created" if complete else "partial",
        candidate=candidate,
        issues=issues,
        commit_id=commit_id,
        actual_tree=actual_tree,
        actual_parents=actual_parents,
        actual_message=actual_message,
        actual_paths=actual_paths,
        real_index_after=index_after_alignment,
    )


__all__ = [
    "CallerCommitApproval",
    "CommitExecutionIssue",
    "CommitExecutionResult",
    "execute_prepared_commit",
]
