"""Resolve local paths to Git worktree identity without consulting Git history."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

GitResolutionStatus = Literal["git_worktree", "not_git_worktree", "technical_failure"]

_GIT_IDENTITY_ENVIRONMENT = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR")
_GIT_PROBE_TIMEOUT_SECONDS = 10


@dataclass(frozen=True, slots=True)
class TechnicalFailure:
    """A failure that prevents a trustworthy Git identity decision."""

    stage: Literal["path", "git_dependency", "git_process", "git_output"]
    summary: str
    details: str


@dataclass(frozen=True, slots=True)
class PathObservation:
    """The caller's locator plus the filesystem paths used for observation."""

    original_locator: str
    original_base: str
    absolute_path: Path
    real_path: Path | None
    probe_path: Path | None
    exists: bool
    probe_uses_existing_ancestor: bool


@dataclass(frozen=True, slots=True)
class GitWorktreeIdentity:
    """Stable local Git identity and the actual worktree content boundary."""

    worktree_root: Path
    common_dir: Path
    git_dir: Path


@dataclass(frozen=True, slots=True)
class GitIdentityResolution:
    """A three-way Git identity result; technical failure is never non-membership."""

    status: GitResolutionStatus
    path: PathObservation
    identity: GitWorktreeIdentity | None = None
    non_worktree_reason: Literal["not_a_git_repository", "bare_repository", "not_inside_work_tree"] | None = None
    failure: TechnicalFailure | None = None


def resolve_git_identity(locator: str, *, base: str | Path) -> GitIdentityResolution:
    """Resolve ``locator`` against ``base`` and observe its local Git worktree.

    Existing files are probed through their parent directory.  A path that does
    not exist is probed through its nearest existing ancestor, while its intended
    absolute and real paths remain in the returned observation.
    """

    path, path_failure = _observe_path(locator, base)
    if path_failure is not None:
        return GitIdentityResolution(status="technical_failure", path=path, failure=path_failure)

    assert path.probe_path is not None
    environment = os.environ.copy()
    for name in _GIT_IDENTITY_ENVIRONMENT:
        environment.pop(name, None)
    # Keep Git's deterministic "not a git repository" diagnostic available to
    # the three-way classifier instead of depending on the host locale.
    environment["LC_ALL"] = "C"

    classification = _run_git(
        path.probe_path,
        ("rev-parse", "--is-inside-work-tree", "--is-bare-repository"),
        environment,
    )
    if isinstance(classification, TechnicalFailure):
        if "not a git repository" in classification.details.casefold():
            return GitIdentityResolution(
                status="not_git_worktree",
                path=path,
                non_worktree_reason="not_a_git_repository",
            )
        return GitIdentityResolution(status="technical_failure", path=path, failure=classification)

    classification_lines = classification.splitlines()
    if len(classification_lines) != 2 or any(value not in {"true", "false"} for value in classification_lines):
        return _output_failure(path, "Git returned an invalid worktree classification", classification)
    inside_worktree = classification_lines[0] == "true"
    bare_repository = classification_lines[1] == "true"
    if bare_repository:
        return GitIdentityResolution(
            status="not_git_worktree",
            path=path,
            non_worktree_reason="bare_repository",
        )
    if not inside_worktree:
        return GitIdentityResolution(
            status="not_git_worktree",
            path=path,
            non_worktree_reason="not_inside_work_tree",
        )

    identity_output = _run_git(
        path.probe_path,
        ("rev-parse", "--show-toplevel", "--git-common-dir", "--git-dir"),
        environment,
    )
    if isinstance(identity_output, TechnicalFailure):
        return GitIdentityResolution(status="technical_failure", path=path, failure=identity_output)
    identity_lines = identity_output.splitlines()
    if len(identity_lines) != 3 or any(not value for value in identity_lines):
        return _output_failure(path, "Git returned an invalid worktree identity", identity_output)

    try:
        identity = GitWorktreeIdentity(
            worktree_root=_normalize_git_path(identity_lines[0], path.probe_path),
            common_dir=_normalize_git_path(identity_lines[1], path.probe_path),
            git_dir=_normalize_git_path(identity_lines[2], path.probe_path),
        )
    except (OSError, RuntimeError) as error:
        return GitIdentityResolution(
            status="technical_failure",
            path=path,
            failure=TechnicalFailure(
                stage="path",
                summary="Git identity paths could not be resolved",
                details=str(error),
            ),
        )
    return GitIdentityResolution(status="git_worktree", path=path, identity=identity)


def _observe_path(locator: str, base: str | Path) -> tuple[PathObservation, TechnicalFailure | None]:
    original_base = os.fspath(base)
    base_path = Path(original_base).expanduser()
    if not base_path.is_absolute():
        base_path = Path.cwd() / base_path
    locator_path = Path(locator).expanduser()
    absolute_path = Path(os.path.abspath(locator_path if locator_path.is_absolute() else base_path / locator_path))
    empty = PathObservation(locator, original_base, absolute_path, None, None, False, False)

    try:
        lexical_exists = absolute_path.exists()
        lexical_is_symlink = absolute_path.is_symlink()
        if lexical_is_symlink:
            # strict resolution makes dangling links and symlink loops explicit.
            real_path = absolute_path.resolve(strict=True)
            exists = True
        else:
            real_path = absolute_path.resolve(strict=lexical_exists)
            exists = lexical_exists

        if exists:
            probe_path = real_path if real_path.is_dir() else real_path.parent
            uses_ancestor = False
        else:
            probe_path = real_path
            while not probe_path.exists():
                parent = probe_path.parent
                if parent == probe_path:
                    break
                probe_path = parent
            if not probe_path.exists():
                raise FileNotFoundError(f"no existing ancestor for {absolute_path}")
            if not probe_path.is_dir():
                probe_path = probe_path.parent
            probe_path = probe_path.resolve(strict=True)
            uses_ancestor = True
    except (OSError, RuntimeError) as error:
        return empty, TechnicalFailure(
            stage="path",
            summary="Work object path could not be observed",
            details=str(error),
        )

    return (
        PathObservation(
            original_locator=locator,
            original_base=original_base,
            absolute_path=absolute_path,
            real_path=real_path,
            probe_path=probe_path,
            exists=exists,
            probe_uses_existing_ancestor=uses_ancestor,
        ),
        None,
    )


def _run_git(probe: Path, arguments: tuple[str, ...], environment: dict[str, str]) -> str | TechnicalFailure:
    command = ("git", "-C", str(probe), *arguments)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=_GIT_PROBE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        return TechnicalFailure("git_dependency", "Git executable is unavailable", str(error))
    except OSError as error:
        return TechnicalFailure("git_process", "Git process could not be started", str(error))
    except subprocess.TimeoutExpired:
        return TechnicalFailure(
            "git_process",
            "Git identity probe timed out",
            f"Git probe exceeded {_GIT_PROBE_TIMEOUT_SECONDS} seconds",
        )
    if completed.returncode != 0:
        details = (
            completed.stderr.strip() or completed.stdout.strip() or f"Git exited with status {completed.returncode}"
        )
        return TechnicalFailure("git_process", "Git could not inspect the work object", details)
    return completed.stdout.strip()


def _normalize_git_path(value: str, probe: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = probe / path
    return path.resolve(strict=True)


def _output_failure(path: PathObservation, summary: str, output: str) -> GitIdentityResolution:
    return GitIdentityResolution(
        status="technical_failure",
        path=path,
        failure=TechnicalFailure(
            stage="git_output",
            summary=summary,
            details=output,
        ),
    )
