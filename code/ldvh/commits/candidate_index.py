"""Prepare an isolated, explicitly owned Git Index for one commit candidate."""

from __future__ import annotations

import hashlib
import os
import secrets
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.git_adapter import _observe_index, observe_commit_candidate
from ldvh.commits.validation import CommitValidationInput
from ldvh.governance.git import isolated_git_environment, windows_path_problem
from ldvh.governance.models import GovernanceScopeResult

_GIT_TIMEOUT_SECONDS = 30
_CANDIDATE_PREFIX = "ldvh-commit-candidate-"
_INDEX_NAME = "index"
_OWNER_MARKER = ".ldvh-candidate-owner"
_UNBORN_HEAD = "UNBORN"

CandidatePreparationStage = Literal[
    "input",
    "baseline",
    "overlap",
    "temporary_index",
    "candidate",
    "drift",
    "cleanup",
]


@dataclass(frozen=True, slots=True)
class CandidatePreparationIssue:
    stage: CandidatePreparationStage
    message: str


@dataclass(frozen=True, slots=True)
class PreparedCommitCandidate:
    worktree_root: str
    selected_paths: tuple[str, ...]
    candidate_paths: tuple[str, ...]
    baseline_snapshot_identity: str
    baseline_index_identity: str
    candidate_snapshot_identity: str
    candidate_tree: str
    baseline_head_commit: str
    baseline_head_tree: str
    validation_input: CommitValidationInput
    candidate_directory: str
    candidate_index_path: str
    ownership_token: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class CandidatePreparationResult:
    outcome: Literal["prepared", "blocked", "unverifiable"]
    candidate: PreparedCommitCandidate | None
    issues: tuple[CandidatePreparationIssue, ...]
    selected_paths: tuple[str, ...]
    candidate_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CandidateCleanupResult:
    outcome: Literal["discarded", "already_absent", "unsafe"]
    issues: tuple[CandidatePreparationIssue, ...]


@dataclass(frozen=True, slots=True)
class _GitResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def _issue(stage: CandidatePreparationStage, message: str) -> CandidatePreparationIssue:
    return CandidatePreparationIssue(stage, message)


def _run_git(
    worktree: Path,
    arguments: tuple[str, ...],
    *,
    index_file: Path | None = None,
    literal_paths: bool = False,
) -> _GitResult | CandidatePreparationIssue:
    path_problem = windows_path_problem(worktree)
    if path_problem is None and index_file is not None:
        path_problem = windows_path_problem(index_file)
    if path_problem is not None:
        return _issue("temporary_index", f"Git path is unsupported on Windows: {path_problem}")
    environment = isolated_git_environment()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    if index_file is not None:
        environment["GIT_INDEX_FILE"] = str(index_file)
    if literal_paths:
        environment["GIT_LITERAL_PATHSPECS"] = "1"
    try:
        completed = subprocess.run(
            ("git", "--no-optional-locks", "-C", str(worktree), *arguments),
            check=False,
            capture_output=True,
            env=environment,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        return _issue("temporary_index", f"Git executable is unavailable: {error}")
    except OSError as error:
        return _issue("temporary_index", f"Git process could not be started: {error}")
    except subprocess.TimeoutExpired:
        return _issue("temporary_index", f"Git candidate operation exceeded {_GIT_TIMEOUT_SECONDS} seconds")
    return _GitResult(completed.returncode, completed.stdout, completed.stderr)


def _git_failure(result: _GitResult | CandidatePreparationIssue, operation: str) -> CandidatePreparationIssue | None:
    if isinstance(result, CandidatePreparationIssue):
        return result
    if result.returncode == 0:
        return None
    details = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
    return _issue("temporary_index", f"Git {operation} failed: {details or result.returncode}")


def _validated_paths(paths: tuple[str, ...]) -> tuple[tuple[str, ...], CandidatePreparationIssue | None]:
    if not paths:
        return (), _issue("input", "At least one explicit target path is required")
    if len(set(paths)) != len(paths):
        return (), _issue("input", "Target paths must be unique")
    for path in paths:
        parts = path.split("/")
        if (
            not path
            or path.startswith("/")
            or "\\" in path
            or "\0" in path
            or any(part in {"", ".", ".."} for part in parts)
        ):
            return (), _issue("input", f"Target path is not a normalized worktree-relative path: {path!r}")
    return paths, None


def _head_identity(worktree: Path) -> tuple[str, str, CandidatePreparationIssue | None]:
    commit_result = _run_git(worktree, ("rev-parse", "--verify", "-q", "HEAD^{commit}"))
    if isinstance(commit_result, CandidatePreparationIssue):
        return "", "", commit_result
    if commit_result.returncode == 1 and not commit_result.stdout and not commit_result.stderr:
        return _UNBORN_HEAD, _UNBORN_HEAD, None
    if commit_result.returncode != 0:
        details = (commit_result.stderr or commit_result.stdout).decode("utf-8", errors="replace").strip()
        return "", "", _issue("baseline", f"Git HEAD commit read failed: {details or commit_result.returncode}")
    tree_result = _run_git(worktree, ("rev-parse", "--verify", "-q", "HEAD^{tree}"))
    if isinstance(tree_result, CandidatePreparationIssue):
        return "", "", tree_result
    if tree_result.returncode != 0:
        details = (tree_result.stderr or tree_result.stdout).decode("utf-8", errors="replace").strip()
        return "", "", _issue("baseline", f"Git HEAD tree read failed: {details or tree_result.returncode}")
    try:
        commit = commit_result.stdout.decode("ascii").strip()
        tree = tree_result.stdout.decode("ascii").strip()
    except UnicodeDecodeError:
        return "", "", _issue("baseline", "Git returned a non-ASCII HEAD identity")
    if not commit or not tree:
        return "", "", _issue("baseline", "Git returned an empty HEAD identity")
    return commit, tree, None


def _index_identity(worktree: Path) -> tuple[str, CandidatePreparationIssue | None]:
    result = _run_git(worktree, ("ls-files", "--stage", "-z"))
    if isinstance(result, CandidatePreparationIssue):
        return "", result
    if result.returncode != 0:
        details = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        return "", _issue("baseline", f"Git real Index read failed: {details or result.returncode}")
    return f"sha256:{hashlib.sha256(result.stdout).hexdigest()}", None


def _create_candidate_assets() -> tuple[Path, Path, str, CandidatePreparationIssue | None]:
    token = secrets.token_hex(32)
    directory: Path | None = None
    for variable in ("TMPDIR", "TEMP", "TMP"):
        raw_root = os.environ.get(variable)
        if raw_root is None:
            continue
        path_problem = windows_path_problem(raw_root)
        if path_problem is not None:
            return (
                Path(),
                Path(),
                "",
                _issue(
                    "temporary_index",
                    f"{variable} is unsupported on Windows: {path_problem}",
                ),
            )
    temporary_root = Path(tempfile.gettempdir())
    path_problem = windows_path_problem(temporary_root)
    if path_problem is not None:
        return (
            Path(),
            Path(),
            "",
            _issue(
                "temporary_index",
                f"Temporary directory is unsupported on Windows: {path_problem}",
            ),
        )
    try:
        directory = Path(tempfile.mkdtemp(prefix=_CANDIDATE_PREFIX)).resolve()
        index_path = directory / _INDEX_NAME
        (directory / _OWNER_MARKER).write_text(token, encoding="ascii", newline="\n")
    except OSError as error:
        if directory is not None:
            try:
                for child in directory.iterdir():
                    child.unlink()
                directory.rmdir()
            except OSError:
                pass
        return Path(), Path(), "", _issue("temporary_index", f"Candidate assets could not be created: {error}")
    return directory, index_path, token, None


def _discard_assets(directory: Path, index_path: Path, token: str) -> CandidatePreparationIssue | None:
    path_problem = windows_path_problem(directory) or windows_path_problem(index_path)
    if path_problem is not None:
        return _issue("cleanup", f"Candidate asset path is unsupported on Windows: {path_problem}")
    if not directory.exists():
        return None
    marker = directory / _OWNER_MARKER
    if (
        not directory.is_dir()
        or directory.name.startswith(_CANDIDATE_PREFIX) is False
        or directory.parent != Path(tempfile.gettempdir()).resolve()
        or index_path != directory / _INDEX_NAME
        or not marker.is_file()
    ):
        return _issue("cleanup", "Candidate asset ownership could not be established")
    try:
        if marker.read_text(encoding="ascii") != token:
            return _issue("cleanup", "Candidate ownership marker does not match")
        children = tuple(directory.iterdir())
        if any(child.is_dir() and not child.is_symlink() for child in children):
            return _issue("cleanup", "Candidate directory contains an unexpected subdirectory")
        for child in children:
            child.unlink()
        directory.rmdir()
    except OSError as error:
        return _issue("cleanup", f"Candidate assets could not be removed safely: {error}")
    return None


def _failed_result(
    outcome: Literal["blocked", "unverifiable"],
    issue: CandidatePreparationIssue,
    selected_paths: tuple[str, ...],
    *,
    candidate_paths: tuple[str, ...] = (),
    assets: tuple[Path, Path, str] | None = None,
) -> CandidatePreparationResult:
    issues = [issue]
    if assets is not None:
        cleanup_issue = _discard_assets(*assets)
        if cleanup_issue is not None:
            issues.append(cleanup_issue)
            outcome = "unverifiable"
    return CandidatePreparationResult(outcome, None, tuple(issues), selected_paths, candidate_paths)


def prepare_commit_candidate(
    *,
    locator: str,
    base: str | Path,
    message: str | None,
    selected_paths: tuple[str, ...],
    contract: CommitContractProjection,
    governance: GovernanceScopeResult,
) -> CandidatePreparationResult:
    """Assemble one exact candidate in an owned temporary Index without changing the real Index."""

    selected, failure = _validated_paths(selected_paths)
    if failure is not None:
        return _failed_result("blocked", failure, selected_paths)

    baseline = observe_commit_candidate(
        locator=locator,
        base=base,
        message=message,
        contract=contract,
        governance=governance,
    )
    if baseline.outcome != "observed" or baseline.validation_input is None or baseline.snapshot_identity is None:
        details = "; ".join(f"{issue.stage}: {issue.message}" for issue in baseline.issues) or baseline.outcome
        return _failed_result(
            "unverifiable",
            _issue("baseline", f"Real Index baseline could not be observed: {details}"),
            selected,
        )
    overlap = tuple(path for path in selected if path in set(baseline.candidate_paths))
    if overlap:
        return _failed_result(
            "blocked",
            _issue("overlap", f"Target paths overlap existing staged content: {', '.join(overlap)}"),
            selected,
        )

    worktree = Path(baseline.validation_input.git_worktree_root or "").resolve()
    baseline_index_identity, failure = _index_identity(worktree)
    if failure is not None:
        return _failed_result("unverifiable", failure, selected)
    head_commit, head_tree, failure = _head_identity(worktree)
    if failure is not None:
        return _failed_result("unverifiable", failure, selected)
    directory, index_path, token, failure = _create_candidate_assets()
    if failure is not None:
        return _failed_result("unverifiable", failure, selected)
    assets = (directory, index_path, token)

    seed_arguments = ("read-tree", "--empty") if head_tree == _UNBORN_HEAD else ("read-tree", head_tree)
    failure = _git_failure(_run_git(worktree, seed_arguments, index_file=index_path), "candidate seed")
    if failure is not None:
        return _failed_result("unverifiable", failure, selected, assets=assets)
    failure = _git_failure(
        _run_git(
            worktree,
            ("add", "-A", "--", *selected),
            index_file=index_path,
            literal_paths=True,
        ),
        "candidate assembly",
    )
    if failure is not None:
        return _failed_result("blocked", failure, selected, assets=assets)

    tree_result = _run_git(worktree, ("write-tree",), index_file=index_path)
    failure = _git_failure(tree_result, "candidate tree write")
    if failure is not None:
        return _failed_result("unverifiable", failure, selected, assets=assets)
    assert isinstance(tree_result, _GitResult)
    try:
        candidate_tree = tree_result.stdout.decode("ascii").strip()
    except UnicodeDecodeError:
        return _failed_result(
            "unverifiable",
            _issue("candidate", "Git returned a non-ASCII candidate tree identity"),
            selected,
            assets=assets,
        )
    if not candidate_tree:
        return _failed_result(
            "unverifiable",
            _issue("candidate", "Git returned an empty candidate tree identity"),
            selected,
            assets=assets,
        )

    candidate = _observe_index(
        worktree=worktree,
        message=message,
        contract=contract,
        governance=governance,
        index_file=index_path,
    )
    if candidate.outcome != "observed" or candidate.validation_input is None or candidate.snapshot_identity is None:
        details = "; ".join(f"{issue.stage}: {issue.message}" for issue in candidate.issues) or candidate.outcome
        return _failed_result(
            "unverifiable",
            _issue("candidate", f"Temporary candidate could not be observed: {details}"),
            selected,
            candidate_paths=candidate.candidate_paths,
            assets=assets,
        )
    if len(candidate.candidate_paths) != len(selected) or set(candidate.candidate_paths) != set(selected):
        return _failed_result(
            "blocked",
            _issue("candidate", "Temporary candidate paths do not exactly match the explicit target paths"),
            selected,
            candidate_paths=candidate.candidate_paths,
            assets=assets,
        )

    baseline_after = observe_commit_candidate(
        locator=locator,
        base=base,
        message=message,
        contract=contract,
        governance=governance,
    )
    if baseline_after.outcome != "observed" or baseline_after.snapshot_identity != baseline.snapshot_identity:
        return _failed_result(
            "blocked",
            _issue("drift", "HEAD or the real Index changed while the temporary candidate was assembled"),
            selected,
            candidate_paths=candidate.candidate_paths,
            assets=assets,
        )
    index_identity_after, failure = _index_identity(worktree)
    if failure is not None or index_identity_after != baseline_index_identity:
        return _failed_result(
            "blocked" if failure is None else "unverifiable",
            failure or _issue("drift", "The real Index changed while the temporary candidate was assembled"),
            selected,
            candidate_paths=candidate.candidate_paths,
            assets=assets,
        )

    prepared = PreparedCommitCandidate(
        worktree_root=str(worktree),
        selected_paths=selected,
        candidate_paths=candidate.candidate_paths,
        baseline_snapshot_identity=baseline.snapshot_identity,
        baseline_index_identity=baseline_index_identity,
        candidate_snapshot_identity=candidate.snapshot_identity,
        candidate_tree=candidate_tree,
        baseline_head_commit=head_commit,
        baseline_head_tree=head_tree,
        validation_input=candidate.validation_input,
        candidate_directory=str(directory),
        candidate_index_path=str(index_path),
        ownership_token=token,
    )
    return CandidatePreparationResult("prepared", prepared, (), selected, candidate.candidate_paths)


def discard_prepared_candidate(candidate: PreparedCommitCandidate) -> CandidateCleanupResult:
    """Remove only assets whose ownership marker matches the prepared candidate."""

    directory = Path(candidate.candidate_directory)
    index_path = Path(candidate.candidate_index_path)
    path_problem = windows_path_problem(directory) or windows_path_problem(index_path)
    if path_problem is not None:
        failure = _issue("cleanup", f"Candidate asset path is unsupported on Windows: {path_problem}")
        return CandidateCleanupResult("unsafe", (failure,))
    if not directory.exists():
        return CandidateCleanupResult("already_absent", ())
    failure = _discard_assets(directory, index_path, candidate.ownership_token)
    if failure is not None:
        return CandidateCleanupResult("unsafe", (failure,))
    return CandidateCleanupResult("discarded", ())


__all__ = [
    "CandidateCleanupResult",
    "CandidatePreparationIssue",
    "CandidatePreparationResult",
    "PreparedCommitCandidate",
    "discard_prepared_candidate",
    "prepare_commit_candidate",
]
