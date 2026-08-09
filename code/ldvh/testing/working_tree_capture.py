"""Policy-aware filesystem observations for full-v4 Working Tree evidence.

This module is the side-effect boundary: it resolves the governed worktree and
reads its files.  It does not form the final evidence DTO, write run records,
execute tests, or decide a run's top-level status.
"""

from __future__ import annotations

import hashlib
import os
import stat
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ldvh.filesystem import (
    PathChangedError,
    UnsafePathError,
    UnstableIdentityError,
    is_link_or_reparse,
    safe_read_relative,
)
from ldvh.governance.models import ConfigStatus, ObjectStatus, ScopeStatus, explicit_scope
from ldvh.governance.resolver import resolve_governance_scope
from ldvh.testing.working_tree_evidence import (
    current_complete_coverage,
    manifest_fingerprint,
    normalize_relative_path,
    policy_excludes_relative_path,
    validate_coverage,
    validate_manifest,
)
from ldvh.time import utc_now_iso

CaptureStage = Literal["before", "after"]
BoundaryCode = Literal[
    "governance_incomplete",
    "scope_not_governed_single",
    "resolution_not_unique",
    "identity_incomplete",
    "workspace_identity_mismatch",
]


@dataclass(frozen=True, slots=True)
class GovernedWorktreeBoundary:
    """The unique governance and Git-worktree identity accepted for capture."""

    governed_project_id: str
    git_worktree_root: Path
    git_common_dir: Path

    def to_json(self) -> dict[str, str]:
        return {
            "governed_project_id": self.governed_project_id,
            "git_worktree_root": str(self.git_worktree_root),
            "git_common_dir": str(self.git_common_dir),
        }


@dataclass(frozen=True, slots=True)
class BoundaryDiagnostic:
    """A closed, content-free reason that governance identity was not accepted."""

    code: BoundaryCode
    summary: str

    def to_json(self) -> dict[str, str]:
        return {"stage": "identity", "code": self.code, "summary": self.summary}


@dataclass(frozen=True, slots=True)
class BoundaryResolution:
    boundary: GovernedWorktreeBoundary | None
    diagnostics: tuple[BoundaryDiagnostic, ...]


@dataclass(frozen=True, slots=True)
class CaptureDiagnostic:
    """A content-free capture diagnostic kept outside the evidence DTO."""

    stage: CaptureStage
    path: str | None
    code: str
    system_error_category: Literal[
        "none",
        "filesystem_unavailable",
        "path_changed",
        "unsafe_topology",
        "unstable_identity",
        "unsupported_type",
        "normalization_failure",
    ]

    def to_json(self) -> dict[str, str | None]:
        return {
            "stage": self.stage,
            "path": self.path,
            "code": self.code,
            "system_error_category": self.system_error_category,
        }


@dataclass(frozen=True, slots=True)
class ManifestCapture:
    """One manifest fragment, its coverage observation, and run diagnostics."""

    manifest: dict[str, Any]
    coverage: dict[str, Any]
    diagnostics: tuple[CaptureDiagnostic, ...]


@dataclass(frozen=True, slots=True)
class _ObservedDirectory:
    absolute_path: Path
    normalized_path: str | None
    signature: tuple[int, ...]


def resolve_capture_boundary(workspace: Path) -> BoundaryResolution:
    """Resolve and accept exactly one governed identity for ``workspace``.

    The acceptance matrix intentionally has no Git-state or path-name fallback.
    """

    try:
        actual_workspace = workspace.resolve(strict=True)
    except OSError:
        return _boundary_failure("governance_incomplete", "workspace identity could not be resolved")
    requested = explicit_scope([str(actual_workspace)])
    run = resolve_governance_scope(requested, base=actual_workspace)
    if run.technical_non_completions or run.requested_scope != run.completed_scope or run.result is None:
        return _boundary_failure("governance_incomplete", "governance resolution did not complete the requested scope")
    result = run.result
    if result.config_status is not ConfigStatus.VALID or result.scope_status is not ScopeStatus.GOVERNED_SINGLE:
        return _boundary_failure("scope_not_governed_single", "governance scope is not one valid governed project")
    governed = tuple(item for item in result.object_resolutions if item.status is ObjectStatus.GOVERNED)
    if len(governed) != 1 or len(result.object_resolutions) != 1:
        return _boundary_failure("resolution_not_unique", "governance did not return exactly one governed resolution")
    resolution = governed[0]
    if not resolution.governed_project_id or not resolution.git_worktree_root or not resolution.git_common_dir:
        return _boundary_failure("identity_incomplete", "governance identity fields are incomplete")
    worktree_root = Path(resolution.git_worktree_root)
    common_dir = Path(resolution.git_common_dir)
    if actual_workspace != worktree_root:
        return _boundary_failure(
            "workspace_identity_mismatch",
            "requested workspace does not equal the governed Git worktree root",
        )
    return BoundaryResolution(
        boundary=GovernedWorktreeBoundary(
            governed_project_id=resolution.governed_project_id,
            git_worktree_root=worktree_root,
            git_common_dir=common_dir,
        ),
        diagnostics=(),
    )


def same_capture_boundary(before: GovernedWorktreeBoundary, after: GovernedWorktreeBoundary) -> bool:
    """Return the exact project/worktree/common-dir identity comparison."""

    return before == after


def capture_manifest(boundary: GovernedWorktreeBoundary, stage: CaptureStage) -> ManifestCapture:
    """Capture all policy-included regular-file bytes below one worktree root."""

    if stage not in {"before", "after"}:
        raise ValueError("stage must be 'before' or 'after'")
    root = boundary.git_worktree_root
    files: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    diagnostics: list[CaptureDiagnostic] = []
    observed_directories: list[_ObservedDirectory] = []

    try:
        root_observation = root.lstat()
        if is_link_or_reparse(root_observation) or not stat.S_ISDIR(root_observation.st_mode):
            _add_gap(
                gaps,
                diagnostics,
                stage=stage,
                path=None,
                code="unsafe_entry",
                summary="worktree root is not a stable non-reparse directory",
                category="unsafe_topology",
            )
        else:
            root_signature = _stable_signature(root_observation)
            observed_directories.append(_ObservedDirectory(root, None, root_signature))
            _scan_directory(
                root=root,
                relative_parts=(),
                stage=stage,
                files=files,
                gaps=gaps,
                diagnostics=diagnostics,
                observed_directories=observed_directories,
            )
            _verify_directories(observed_directories, stage, gaps, diagnostics)
    except (UnsafePathError, UnstableIdentityError):
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=None,
            code="unsafe_entry",
            summary="worktree root identity could not be confirmed safely",
            category="unstable_identity",
        )
    except (FileNotFoundError, PathChangedError):
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=None,
            code="path_changed",
            summary="worktree root changed during capture",
            category="path_changed",
        )
    except OSError:
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=None,
            code="traversal_unavailable",
            summary="worktree root could not be enumerated",
            category="filesystem_unavailable",
        )

    files.sort(key=lambda item: item["path"].encode("utf-8"))
    coverage = current_complete_coverage()
    if gaps:
        coverage["status"] = "incomplete"
        coverage["gaps"] = gaps
    complete = not gaps
    policy_fingerprint = coverage["policy_fingerprint"]
    manifest = {
        "observed_at": utc_now_iso(),
        "status": "complete" if complete else "incomplete",
        "manifest_fingerprint": manifest_fingerprint(files, policy_fingerprint) if complete else None,
        "file_count": len(files),
        "byte_count": sum(item["size_bytes"] for item in files),
        "files": files,
    }
    validate_coverage(coverage)
    validate_manifest(manifest, policy_fingerprint)
    return ManifestCapture(manifest=manifest, coverage=coverage, diagnostics=tuple(diagnostics))


def _scan_directory(
    *,
    root: Path,
    relative_parts: tuple[str, ...],
    stage: CaptureStage,
    files: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    diagnostics: list[CaptureDiagnostic],
    observed_directories: list[_ObservedDirectory],
) -> None:
    directory = root.joinpath(*relative_parts)
    normalized_directory = _normalize_parts(relative_parts)
    try:
        before_observation = directory.lstat()
        if is_link_or_reparse(before_observation) or not stat.S_ISDIR(before_observation.st_mode):
            raise UnsafePathError("capture directory is not a non-reparse directory")
        before = _stable_signature(before_observation)
        with os.scandir(directory) as iterator:
            entries = tuple(iterator)
        after_observation = directory.lstat()
        if is_link_or_reparse(after_observation) or not stat.S_ISDIR(after_observation.st_mode):
            raise PathChangedError("capture directory changed type while it was enumerated")
        after = _stable_signature(after_observation)
    except (FileNotFoundError, PathChangedError):
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=normalized_directory,
            code="path_changed",
            summary="directory changed while it was enumerated",
            category="path_changed",
        )
        return
    except (UnsafePathError, UnstableIdentityError):
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=normalized_directory,
            code="unsafe_entry",
            summary="directory identity could not be confirmed safely",
            category="unstable_identity",
        )
        return
    except OSError:
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=normalized_directory,
            code="traversal_unavailable",
            summary="directory could not be completely enumerated",
            category="filesystem_unavailable",
        )
        return
    if before != after:
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=normalized_directory,
            code="path_changed",
            summary="directory changed while it was enumerated",
            category="path_changed",
        )
        return

    normalized_entries: dict[str, list[tuple[os.DirEntry[str], tuple[str, ...]]]] = defaultdict(list)
    invalid_entries: list[os.DirEntry[str]] = []
    for entry in entries:
        child_parts = (*relative_parts, entry.name)
        normalized = _normalize_parts(child_parts)
        if normalized is None:
            invalid_entries.append(entry)
        else:
            normalized_entries[normalized].append((entry, child_parts))
    for _entry in invalid_entries:
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=normalized_directory,
            code="unsafe_entry",
            summary="an entry path could not be represented by the normalized path contract",
            category="normalization_failure",
        )

    for normalized_path in sorted(normalized_entries, key=lambda item: item.encode("utf-8")):
        grouped = normalized_entries[normalized_path]
        if len(grouped) > 1:
            _add_gap(
                gaps,
                diagnostics,
                stage=stage,
                path=normalized_path,
                code="normalization_collision",
                summary="multiple observed paths collide after NFC normalization",
                category="normalization_failure",
            )
            continue
        entry, child_parts = grouped[0]
        if all(
            policy_excludes_relative_path(normalized_path, entry_kind=kind)
            for kind in ("directory", "regular_file", "other")
        ):
            continue
        try:
            observation = os.lstat(entry.path)
        except FileNotFoundError:
            _add_gap(
                gaps,
                diagnostics,
                stage=stage,
                path=normalized_path,
                code="path_changed",
                summary="entry changed before its type could be observed",
                category="path_changed",
            )
            continue
        except OSError:
            _add_gap(
                gaps,
                diagnostics,
                stage=stage,
                path=normalized_path,
                code="traversal_unavailable",
                summary="entry type could not be observed",
                category="filesystem_unavailable",
            )
            continue
        if is_link_or_reparse(observation):
            _add_gap(
                gaps,
                diagnostics,
                stage=stage,
                path=normalized_path,
                code="unsafe_entry",
                summary="included path is a symbolic link or reparse point",
                category="unsafe_topology",
            )
            continue
        if stat.S_ISDIR(observation.st_mode):
            if policy_excludes_relative_path(normalized_path, entry_kind="directory"):
                continue
            try:
                signature = _stable_signature(observation)
            except UnstableIdentityError:
                _add_gap(
                    gaps,
                    diagnostics,
                    stage=stage,
                    path=normalized_path,
                    code="unsafe_entry",
                    summary="directory identity could not be confirmed safely",
                    category="unstable_identity",
                )
                continue
            observed_directories.append(_ObservedDirectory(Path(entry.path), normalized_path, signature))
            _scan_directory(
                root=root,
                relative_parts=child_parts,
                stage=stage,
                files=files,
                gaps=gaps,
                diagnostics=diagnostics,
                observed_directories=observed_directories,
            )
            continue
        if not stat.S_ISREG(observation.st_mode):
            _add_gap(
                gaps,
                diagnostics,
                stage=stage,
                path=normalized_path,
                code="unsupported_entry",
                summary="included path is neither a directory nor a regular file",
                category="unsupported_type",
            )
            continue
        if policy_excludes_relative_path(normalized_path, entry_kind="regular_file"):
            continue
        _read_file(root, child_parts, normalized_path, stage, files, gaps, diagnostics)


def _read_file(
    root: Path,
    relative_parts: tuple[str, ...],
    normalized_path: str,
    stage: CaptureStage,
    files: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    diagnostics: list[CaptureDiagnostic],
) -> None:
    try:
        raw = safe_read_relative(root, Path(*relative_parts))
    except PathChangedError:
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=normalized_path,
            code="path_changed",
            summary="regular file path changed while it was read",
            category="path_changed",
        )
        return
    except UnsafePathError:
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=normalized_path,
            code="unsafe_entry",
            summary="regular file topology could not be confirmed safely",
            category="unsafe_topology",
        )
        return
    except UnstableIdentityError:
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=normalized_path,
            code="unsafe_entry",
            summary="regular file identity could not be confirmed safely",
            category="unstable_identity",
        )
        return
    except OSError:
        _add_gap(
            gaps,
            diagnostics,
            stage=stage,
            path=normalized_path,
            code="read_unavailable",
            summary="regular file bytes could not be read completely",
            category="filesystem_unavailable",
        )
        return
    files.append({"path": normalized_path, "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})


def _verify_directories(
    observations: list[_ObservedDirectory],
    stage: CaptureStage,
    gaps: list[dict[str, Any]],
    diagnostics: list[CaptureDiagnostic],
) -> None:
    for observed in observations:
        try:
            current = observed.absolute_path.lstat()
            if is_link_or_reparse(current) or not stat.S_ISDIR(current.st_mode):
                raise PathChangedError
            if _stable_signature(current) != observed.signature:
                raise PathChangedError
        except (FileNotFoundError, PathChangedError):
            _add_gap(
                gaps,
                diagnostics,
                stage=stage,
                path=observed.normalized_path,
                code="path_changed",
                summary="directory changed during capture",
                category="path_changed",
            )
        except (UnsafePathError, UnstableIdentityError):
            _add_gap(
                gaps,
                diagnostics,
                stage=stage,
                path=observed.normalized_path,
                code="unsafe_entry",
                summary="directory identity could not be confirmed safely",
                category="unstable_identity",
            )
        except OSError:
            _add_gap(
                gaps,
                diagnostics,
                stage=stage,
                path=observed.normalized_path,
                code="traversal_unavailable",
                summary="directory could not be re-observed after capture",
                category="filesystem_unavailable",
            )


def _stable_signature(observation: os.stat_result) -> tuple[int, ...]:
    identity: list[int] = []
    for field in ("st_dev", "st_ino"):
        value = getattr(observation, field, None)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise UnstableIdentityError(f"filesystem identity field {field} is unavailable")
        identity.append(value)
    metadata: list[int] = []
    for field in ("st_size", "st_mtime_ns", "st_ctime_ns"):
        value = getattr(observation, field, None)
        if not isinstance(value, int) or isinstance(value, bool):
            raise UnstableIdentityError(f"filesystem metadata field {field} is unavailable")
        metadata.append(value)
    return (
        stat.S_IFMT(observation.st_mode),
        *identity,
        *metadata,
        getattr(observation, "st_nlink", 0),
        getattr(observation, "st_file_attributes", 0),
    )


def _normalize_parts(parts: tuple[str, ...]) -> str | None:
    if not parts:
        return None
    try:
        normalized = normalize_relative_path("/".join(parts))
        normalized.encode("utf-8")
    except (UnicodeError, ValueError):
        return None
    return normalized


def _add_gap(
    gaps: list[dict[str, Any]],
    diagnostics: list[CaptureDiagnostic],
    *,
    stage: CaptureStage,
    path: str | None,
    code: str,
    summary: str,
    category: Literal[
        "none",
        "filesystem_unavailable",
        "path_changed",
        "unsafe_topology",
        "unstable_identity",
        "unsupported_type",
        "normalization_failure",
    ],
) -> None:
    gap = {"stage": stage, "path": path, "code": code, "summary": summary}
    if gap not in gaps:
        gaps.append(gap)
        diagnostics.append(CaptureDiagnostic(stage, path, code, category))


def _boundary_failure(code: BoundaryCode, summary: str) -> BoundaryResolution:
    return BoundaryResolution(boundary=None, diagnostics=(BoundaryDiagnostic(code, summary),))


__all__ = [
    "BoundaryDiagnostic",
    "BoundaryResolution",
    "CaptureDiagnostic",
    "GovernedWorktreeBoundary",
    "ManifestCapture",
    "capture_manifest",
    "resolve_capture_boundary",
    "same_capture_boundary",
]
