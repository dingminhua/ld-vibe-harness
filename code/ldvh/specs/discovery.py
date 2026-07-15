"""Discover specification candidates from an explicit Git worktree root."""

from __future__ import annotations

import os
import re
import stat
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.filesystem import is_link_or_reparse

_SPEC_NAME = re.compile(r"[0-9]{2,}-.+\.md")
_ATTACHMENT_NAME = re.compile(r"[0-9]{2,}\.Att\.[0-9]{2,}-.+\.md")
_GIT_TIMEOUT_SECONDS = 10
_GIT_REPOSITORY_OVERRIDES = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_IMPLICIT_WORK_TREE",
)


@dataclass(frozen=True, slots=True)
class Candidate:
    """A regular, non-ignored file at one of the two candidate path shapes."""

    relative_path: str
    absolute_path: Path
    kind: Literal["spec", "attachment"]


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """The trusted discovery result and any boundary failures."""

    repository_root: Path
    candidates: tuple[Candidate, ...]
    issues: tuple[Issue, ...]
    complete: bool


@dataclass(frozen=True, slots=True)
class _FileObservation:
    candidate: Candidate
    device: int
    inode: int


@dataclass(frozen=True, slots=True)
class _EntryObservation:
    relative_path: str
    file_type: int
    device: int
    inode: int


@dataclass(frozen=True, slots=True)
class _DirectoryObservation:
    relative_path: str
    absolute_path: Path
    kind: Literal["spec", "attachment"]
    file_type: int | None
    device: int | None
    inode: int | None
    entries: tuple[_EntryObservation, ...] = ()


def validate_non_ignored_git_path(root: Path, relative_path: str) -> Issue | None:
    """Require a fixed evidence path to remain eligible under Git ignore rules."""

    encoded = os.fsencode(relative_path)
    try:
        completed = _run_git(root, "check-ignore", "-z", "--stdin", stdin_data=encoded + b"\0")
    except (OSError, subprocess.SubprocessError) as exc:
        return _issue(
            "Cannot determine whether the required Git evidence path is ignored",
            cause=str(exc),
            affected=(relative_path,),
        )
    if completed.returncode == 1 and not completed.stdout:
        return None
    if completed.returncode == 0 and completed.stdout == encoded + b"\0":
        return _issue(
            "Required Git evidence path is ignored by Git",
            affected=(relative_path,),
        )
    return _issue(
        "Cannot determine whether the required Git evidence path is ignored",
        cause=_git_failure_cause(completed),
        affected=(relative_path,),
    )


def validate_exact_worktree_root(root: Path) -> Issue | None:
    """Validate one already-selected path as the exact Git worktree root."""

    normalised, issue = _normalise_repository_root(root)
    if issue is not None:
        return issue
    return _validate_worktree_root(normalised)


def discover_candidates(repository_root: Path) -> DiscoveryResult:
    """Discover candidates from the current filesystem without consulting ``HEAD``.

    The supplied path must be the Git worktree root itself. Files are scanned only
    from the two direct candidate directories and then filtered through Git's
    ignore rules. A failed Git query never defaults to treating files as
    non-ignored.
    """

    root, root_issue = _normalise_repository_root(repository_root)
    if root_issue is not None:
        return DiscoveryResult(root, (), (root_issue,), complete=False)

    directory_issue = _require_directory(root)
    if directory_issue is not None:
        return DiscoveryResult(root, (), (directory_issue,), complete=False)

    worktree_issue = _validate_worktree_root(root)
    if worktree_issue is not None:
        return DiscoveryResult(root, (), (worktree_issue,), complete=False)

    observations, directories, scan_issues = _scan_candidate_files(root)
    observations = tuple(sorted(observations, key=lambda item: item.candidate.relative_path))

    observations, before_query_issues = _revalidate_observations(
        observations,
        directories,
        phase="before the Git ignore query",
    )

    query_performed = bool(observations)
    ignored_paths, ignore_issue = _query_ignored(root, observations)
    issues = list(scan_issues)
    issues.extend(before_query_issues)
    if ignore_issue is not None:
        issues.append(ignore_issue)

    if query_performed:
        observations, after_query_issues = _revalidate_observations(
            observations,
            directories,
            phase="after the Git ignore query",
        )
    else:
        after_query_issues = []
    issues.extend(after_query_issues)

    filtered = (
        tuple(item for item in observations if os.fsencode(item.candidate.relative_path) not in ignored_paths)
        if ignore_issue is None
        else ()
    )

    return DiscoveryResult(
        repository_root=root,
        candidates=tuple(item.candidate for item in filtered),
        issues=tuple(issues),
        complete=not issues,
    )


def _normalise_repository_root(repository_root: Path) -> tuple[Path, Issue | None]:
    requested = Path(repository_root).expanduser()
    try:
        requested_observation = requested.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        return requested.absolute(), _issue(
            "Cannot inspect the explicit repository root",
            cause=str(exc),
            affected=(".",),
        )
    else:
        if is_link_or_reparse(requested_observation):
            return requested.absolute(), _issue(
                "The explicit repository root must not be a link or reparse point",
                affected=(".",),
            )
    try:
        return requested.resolve(strict=False), None
    except (OSError, RuntimeError) as exc:
        fallback = requested.absolute()
        return fallback, _issue(
            "Cannot resolve the explicit repository root",
            cause=str(exc),
            affected=(".",),
        )


def _require_directory(root: Path) -> Issue | None:
    try:
        observation = root.lstat()
    except OSError as exc:
        return _issue(
            "The explicit repository root is not readable",
            cause=str(exc),
            affected=(".",),
        )

    if stat.S_ISDIR(observation.st_mode) and not is_link_or_reparse(observation):
        return None

    return _issue(
        "The explicit repository root is not a directory",
        affected=(".",),
    )


def _validate_worktree_root(root: Path) -> Issue | None:
    try:
        completed = _run_git(root, "rev-parse", "--show-toplevel")
    except (OSError, subprocess.SubprocessError) as exc:
        return _issue(
            "Cannot determine the Git worktree root",
            cause=str(exc),
            affected=(".",),
        )

    if completed.returncode != 0:
        return _issue(
            "The explicit repository root is not a Git worktree root",
            cause=_git_failure_cause(completed),
            affected=(".",),
        )

    reported = completed.stdout.rstrip(b"\r\n")
    if not reported:
        return _issue(
            "Git returned no worktree root",
            cause="git rev-parse --show-toplevel produced empty output",
            affected=(".",),
        )

    try:
        actual_root = Path(os.fsdecode(reported)).resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        return _issue(
            "Cannot resolve the worktree root reported by Git",
            cause=str(exc),
            affected=(".",),
        )

    if actual_root == root:
        return None

    return _issue(
        "The explicit repository root is inside a worktree but is not its root",
        cause=f"Git reported worktree root {actual_root}",
        affected=(".",),
    )


def _scan_candidate_files(
    root: Path,
) -> tuple[list[_FileObservation], tuple[_DirectoryObservation, ...], list[Issue]]:
    candidates: list[_FileObservation] = []
    directories: list[_DirectoryObservation] = []
    issues: list[Issue] = []
    specs_directory = root / "specs"

    specs_observation, specs_issue = _real_directory(
        specs_directory,
        "specs",
        kind="spec",
    )
    if specs_issue is not None:
        issues.append(specs_issue)
    if specs_observation is None:
        return candidates, tuple(directories), issues
    if specs_observation.file_type != stat.S_IFDIR:
        directories.append(specs_observation)
        return candidates, tuple(directories), issues

    direct_specs, spec_entries, direct_issues = _scan_direct_directory(
        specs_directory,
        relative_directory="specs",
        pattern=_SPEC_NAME,
        kind="spec",
    )
    candidates.extend(direct_specs)
    issues.extend(direct_issues)
    directories.append(replace(specs_observation, entries=spec_entries))

    attachments_directory = specs_directory / "attachments"
    attachments_observation, attachments_issue = _real_directory(
        attachments_directory,
        "specs/attachments",
        kind="attachment",
    )
    if attachments_issue is not None:
        issues.append(attachments_issue)
    if attachments_observation is None:
        return candidates, tuple(directories), issues
    if attachments_observation.file_type != stat.S_IFDIR:
        directories.append(attachments_observation)
        return candidates, tuple(directories), issues

    attachments, attachment_entries, attachment_issues = _scan_direct_directory(
        attachments_directory,
        relative_directory="specs/attachments",
        pattern=_ATTACHMENT_NAME,
        kind="attachment",
    )
    candidates.extend(attachments)
    issues.extend(attachment_issues)
    directories.append(replace(attachments_observation, entries=attachment_entries))
    return candidates, tuple(directories), issues


def _real_directory(
    directory: Path,
    relative_path: str,
    *,
    kind: Literal["spec", "attachment"],
) -> tuple[_DirectoryObservation | None, Issue | None]:
    try:
        current = directory.lstat()
    except FileNotFoundError:
        return (
            _DirectoryObservation(
                relative_path=relative_path,
                absolute_path=directory,
                kind=kind,
                file_type=None,
                device=None,
                inode=None,
            ),
            None,
        )
    except OSError as exc:
        return None, _issue(
            "Cannot inspect a specification candidate directory",
            path=relative_path,
            cause=str(exc),
            affected=(relative_path,),
        )

    identity = _stable_identity(current)
    if identity is None:
        return None, _issue(
            "Cannot prove a stable specification candidate directory identity",
            path=relative_path,
            affected=(relative_path,),
        )
    device, inode = identity
    return (
        _DirectoryObservation(
            relative_path=relative_path,
            absolute_path=directory,
            kind=kind,
            file_type=_safe_file_type(current),
            device=device,
            inode=inode,
        ),
        None,
    )


def _scan_direct_directory(
    directory: Path,
    *,
    relative_directory: str,
    pattern: re.Pattern[str],
    kind: Literal["spec", "attachment"],
) -> tuple[list[_FileObservation], tuple[_EntryObservation, ...], list[Issue]]:
    entries, cause = _matching_entry_snapshot(
        directory,
        relative_directory=relative_directory,
        pattern=pattern,
    )
    if entries is None:
        return (
            [],
            (),
            [
                _issue(
                    "Cannot scan a specification candidate directory",
                    path=relative_directory,
                    cause=cause,
                    affected=(relative_directory,),
                )
            ],
        )

    candidates = [
        _FileObservation(
            candidate=Candidate(
                relative_path=entry.relative_path,
                absolute_path=directory / Path(entry.relative_path).name,
                kind=kind,
            ),
            device=entry.device,
            inode=entry.inode,
        )
        for entry in entries
        if entry.file_type == stat.S_IFREG
    ]
    return candidates, entries, []


def _matching_entry_snapshot(
    directory: Path,
    *,
    relative_directory: str,
    pattern: re.Pattern[str],
) -> tuple[tuple[_EntryObservation, ...] | None, str | None]:
    observed: list[_EntryObservation] = []
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if pattern.fullmatch(entry.name) is None:
                    continue
                current = entry.stat(follow_symlinks=False)
                identity = _stable_identity(current)
                if identity is None:
                    return None, f"filesystem identity is unavailable for {entry.name}"
                device, inode = identity
                observed.append(
                    _EntryObservation(
                        relative_path=f"{relative_directory}/{entry.name}",
                        file_type=_safe_file_type(current),
                        device=device,
                        inode=inode,
                    )
                )
    except OSError as exc:
        return None, str(exc)

    return tuple(sorted(observed, key=lambda item: item.relative_path)), None


def _revalidate_observations(
    observations: tuple[_FileObservation, ...],
    directories: tuple[_DirectoryObservation, ...],
    *,
    phase: str,
) -> tuple[tuple[_FileObservation, ...], list[Issue]]:
    remaining = list(observations)
    issues: list[Issue] = []

    for directory in directories:
        unchanged, cause = _same_directory_topology(directory)
        if not unchanged:
            relevant = (
                tuple(remaining)
                if directory.kind == "spec"
                else tuple(item for item in remaining if item.candidate.kind == directory.kind)
            )
            affected = _affected_directory_paths(directory, relevant)
            issues.append(
                _issue(
                    "A specification candidate directory changed during discovery",
                    path=directory.relative_path,
                    cause=f"{phase}: {cause}",
                    affected=affected,
                )
            )
            affected_set = set(affected)
            remaining = [item for item in remaining if item.candidate.relative_path not in affected_set]
            if directory.kind == "spec":
                break
            continue

        if directory.file_type != stat.S_IFDIR:
            continue

        current_entries, snapshot_cause = _matching_entry_snapshot(
            directory.absolute_path,
            relative_directory=directory.relative_path,
            pattern=(_SPEC_NAME if directory.kind == "spec" else _ATTACHMENT_NAME),
        )
        if current_entries == directory.entries:
            continue

        relevant = tuple(item for item in remaining if item.candidate.kind == directory.kind)
        affected = _affected_directory_paths(
            directory,
            relevant,
            current_entries=current_entries,
        )
        issues.append(
            _issue(
                "The matching entries in a specification candidate directory changed during discovery",
                path=directory.relative_path,
                cause=(
                    f"{phase}: {snapshot_cause}"
                    if current_entries is None
                    else f"{phase}: matching entry names, types, or filesystem identities changed"
                ),
                affected=affected,
            )
        )
        affected_set = set(affected)
        remaining = [item for item in remaining if item.candidate.relative_path not in affected_set]

    validated: list[_FileObservation] = []
    for item in remaining:
        unchanged, cause = _same_filesystem_identity(
            item.candidate.absolute_path,
            device=item.device,
            inode=item.inode,
            expected="regular file",
        )
        if unchanged:
            validated.append(item)
            continue

        issues.append(
            _issue(
                "A specification candidate changed during discovery",
                path=item.candidate.relative_path,
                cause=f"{phase}: {cause}",
                affected=(item.candidate.relative_path,),
            )
        )

    return tuple(validated), issues


def _affected_directory_paths(
    directory: _DirectoryObservation,
    observations: tuple[_FileObservation, ...],
    *,
    current_entries: tuple[_EntryObservation, ...] | None = None,
) -> tuple[str, ...]:
    affected = {item.candidate.relative_path for item in observations}
    affected.update(entry.relative_path for entry in directory.entries)
    if current_entries is not None:
        affected.update(entry.relative_path for entry in current_entries)
    return tuple(sorted(affected)) or (directory.relative_path,)


def _same_filesystem_identity(
    path: Path,
    *,
    device: int,
    inode: int,
    expected: Literal["regular file"],
) -> tuple[bool, str | None]:
    try:
        current = path.lstat()
    except OSError as exc:
        return False, str(exc)

    has_expected_type = stat.S_ISREG(current.st_mode) and not is_link_or_reparse(current)
    if not has_expected_type:
        return False, f"the path is no longer the same {expected}"
    identity = _stable_identity(current)
    if identity is None:
        return False, f"the {expected} has no stable filesystem identity"
    if identity != (device, inode):
        return False, f"the {expected} has a different filesystem identity"
    return True, None


def _same_directory_topology(
    observation: _DirectoryObservation,
) -> tuple[bool, str | None]:
    try:
        current = observation.absolute_path.lstat()
    except FileNotFoundError:
        if observation.file_type is None:
            return True, None
        return False, "the candidate directory path no longer exists"
    except OSError as exc:
        return False, str(exc)

    if observation.file_type is None:
        return False, "the previously absent candidate directory path now exists"
    stable_identity = _stable_identity(current)
    if stable_identity is None:
        return False, "the candidate directory has no stable filesystem identity"
    current_identity = (_safe_file_type(current), *stable_identity)
    expected_identity = (
        observation.file_type,
        observation.device,
        observation.inode,
    )
    if current_identity != expected_identity:
        return False, "the candidate directory path has a different type or filesystem identity"
    return True, None


def _safe_file_type(observation: os.stat_result) -> int:
    return stat.S_IFLNK if is_link_or_reparse(observation) else stat.S_IFMT(observation.st_mode)


def _stable_identity(observation: os.stat_result) -> tuple[int, int] | None:
    device = getattr(observation, "st_dev", None)
    inode = getattr(observation, "st_ino", None)
    if not isinstance(device, int) or isinstance(device, bool) or device <= 0:
        return None
    if not isinstance(inode, int) or isinstance(inode, bool) or inode <= 0:
        return None
    return device, inode


def _query_ignored(
    root: Path,
    observations: tuple[_FileObservation, ...],
) -> tuple[frozenset[bytes], Issue | None]:
    if not observations:
        return frozenset(), None

    encoded_paths = {os.fsencode(item.candidate.relative_path): item for item in observations}
    payload = b"".join(path + b"\0" for path in encoded_paths)

    try:
        completed = _run_git(
            root,
            "check-ignore",
            "-z",
            "--stdin",
            stdin_data=payload,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return frozenset(), _ignore_issue(observations, str(exc))

    if completed.returncode not in (0, 1):
        return frozenset(), _ignore_issue(
            observations,
            _git_failure_cause(completed),
        )

    output = completed.stdout
    if output and not output.endswith(b"\0"):
        return frozenset(), _ignore_issue(
            observations,
            "git check-ignore returned malformed non-NUL output",
        )

    ignored_paths = set(output[:-1].split(b"\0")) if output else set()
    output_is_consistent = (completed.returncode == 0) == bool(ignored_paths)
    if not output_is_consistent:
        return frozenset(), _ignore_issue(
            observations,
            f"git check-ignore returned status {completed.returncode} with inconsistent output",
        )

    unknown_paths = ignored_paths.difference(encoded_paths)
    if unknown_paths:
        return frozenset(), _ignore_issue(
            observations,
            "git check-ignore returned a path that was not queried",
        )

    return frozenset(ignored_paths), None


def _ignore_issue(observations: tuple[_FileObservation, ...], cause: str) -> Issue:
    return _issue(
        "Cannot determine which specification candidates are ignored by Git",
        cause=cause,
        affected=tuple(item.candidate.relative_path for item in observations),
    )


def _run_git(
    root: Path,
    *arguments: str,
    stdin_data: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", os.fspath(root), *arguments],
        input=stdin_data,
        capture_output=True,
        check=False,
        timeout=_GIT_TIMEOUT_SECONDS,
        env=_git_environment(),
    )


def _git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for variable in _GIT_REPOSITORY_OVERRIDES:
        environment.pop(variable, None)
    return environment


def _git_failure_cause(completed: subprocess.CompletedProcess[bytes]) -> str:
    stderr = completed.stderr.decode("utf-8", errors="replace").strip()
    if stderr:
        return stderr
    return f"git exited with status {completed.returncode}"


def _issue(
    summary: str,
    *,
    path: str = ".",
    cause: str | None = None,
    affected: tuple[str, ...] = (),
) -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(path=path),
        affected=affected,
        cause=cause,
    )
