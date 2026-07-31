"""Helper-independent controlled intake and creation transaction for FileAsset."""

from __future__ import annotations

import hashlib
import stat
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    AllocationCommitResult,
    CreationBoundary,
    allocation_lock,
    commit_object_id_locked,
    preview_object_id_locked,
    serialize_fact_object,
)
from ldvh.facts.file_asset import DEFAULT_PAYLOAD_BUDGET, validate_file_asset_snapshot
from ldvh.facts.models import FactIssue, IssueCategory
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.filesystem import (
    AtomicWriteResult,
    PathChangedError,
    ReadBudgetExceeded,
    UnsafePathError,
    atomic_create_directory_relative,
    durable_writes_enabled,
    is_link_or_reparse,
    remove_directory_relative_if_members_equal,
    safe_read_relative,
)

FileAssetCreationStatus = Literal[
    "source_unavailable",
    "source_stale",
    "candidate_rejected",
    "durability_unavailable",
    "allocation_stale",
    "allocation_unavailable",
    "creation_conflict",
    "creation_unavailable",
    "readback_failed",
    "created",
]


@dataclass(frozen=True, slots=True)
class FileAssetSourceObservation:
    source_path: str
    source_size_bytes: int
    source_content_sha256: str
    source_fingerprint: str
    payload: bytes


@dataclass(frozen=True, slots=True)
class FileAssetCreationCommand:
    boundary: CreationBoundary
    schema: FactSchema
    requested_candidate_id: str
    expected_source_path: str
    expected_source_size_bytes: int
    expected_source_content_sha256: str
    expected_source_fingerprint: str
    supplied: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class FileAssetCreationResult:
    status: FileAssetCreationStatus
    issues: tuple[FactIssue, ...] = ()
    actual_id: str | None = None
    actual_fields: dict[str, Any] | None = None
    manifest_text: str | None = None
    source_observation: FileAssetSourceObservation | None = None
    read: FactReadResult | None = None
    allocation_consumed: bool | None = False
    allocation_status: str | None = None
    allocation_result: AllocationCommitResult | None = None
    creation_result: AtomicWriteResult | None = None
    rollback_result: AtomicWriteResult | None = None
    residual_readback: FactReadResult | None = None
    coordination_release_uncertain: bool = False


def _source_identity(source_path: Path) -> tuple[int, ...]:
    observed = source_path.stat(follow_symlinks=False)
    if is_link_or_reparse(observed) or not stat.S_ISREG(observed.st_mode):
        raise UnsafePathError("FileAsset source_path must be a non-link regular file")
    return (
        stat.S_IFMT(observed.st_mode),
        observed.st_dev,
        observed.st_ino,
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_ctime_ns,
        getattr(observed, "st_nlink", 0),
        getattr(observed, "st_file_attributes", 0),
    )


def _source_fingerprint(source_path: Path, identity: tuple[int, ...], digest: str) -> str:
    fingerprint = hashlib.sha256()
    fingerprint.update(b"ldvh:file-asset-source:v1\0")
    fingerprint.update(source_path.as_posix().encode("utf-8"))
    fingerprint.update(b"\0")
    fingerprint.update("\0".join(str(value) for value in identity).encode("ascii"))
    fingerprint.update(b"\0")
    fingerprint.update(bytes.fromhex(digest))
    return fingerprint.hexdigest()


def observe_file_asset_source(source_path: Path) -> FileAssetSourceObservation:
    """Safely bind one absolute regular source file within the public payload budget."""

    if not source_path.is_absolute() or source_path.name in {"", ".", ".."}:
        raise UnsafePathError("FileAsset source_path must be one absolute regular-file path")
    identity_before = _source_identity(source_path)
    payload = safe_read_relative(
        source_path.parent,
        source_path.name,
        max_bytes=DEFAULT_PAYLOAD_BUDGET,
    )
    identity_after = _source_identity(source_path)
    if identity_before != identity_after or identity_after[3] != len(payload):
        raise PathChangedError("FileAsset source identity changed while it was observed")
    digest = hashlib.sha256(payload).hexdigest()
    return FileAssetSourceObservation(
        source_path.as_posix(),
        len(payload),
        digest,
        _source_fingerprint(source_path, identity_after, digest),
        payload,
    )


def _issue(category: IssueCategory, summary: str, field_path: str | None = None) -> FactIssue:
    return FactIssue(category, summary, field_path)


def _manifest(
    command: FileAssetCreationCommand,
    object_id: str,
    observed_at: str,
    source: FileAssetSourceObservation,
) -> tuple[dict[str, Any], str, tuple[FactIssue, ...]]:
    layout = LAYOUTS["file-asset"]
    fields = {
        **dict(command.supplied),
        "object_id": object_id,
        "fact_type_key": "file-asset",
        "created_at": observed_at,
        "updated_at": observed_at,
        "status": "active",
        "size_bytes": source.source_size_bytes,
        "content_sha256": source.source_content_sha256,
    }
    filename_issues: tuple[FactIssue, ...] = ()
    if fields.get("filename") != Path(source.source_path).name:
        filename_issues = (
            _issue("schema", "filename 必须等于本次实际摄取来源文件的 basename", "filename"),
        )
    manifest_text = serialize_fact_object(layout, fields, None)
    validation = validate_file_asset_snapshot(
        command.schema,
        object_id,
        manifest_text.encode("utf-8"),
        source.payload,
    )
    return fields, manifest_text, (*filename_issues, *validation.issues)


def _source_matches(command: FileAssetCreationCommand, source: FileAssetSourceObservation) -> bool:
    return (
        source.source_path == command.expected_source_path
        and source.source_size_bytes == command.expected_source_size_bytes
        and source.source_content_sha256 == command.expected_source_content_sha256
        and source.source_fingerprint == command.expected_source_fingerprint
    )


def _readback(command: FileAssetCreationCommand, object_id: str) -> FactReadResult:
    return read_fact_object(
        command.boundary.worktree_root,
        LAYOUTS["file-asset"],
        command.schema,
        object_id,
        expected_common_dir=command.boundary.git_common_dir,
    )


def create_file_asset(
    command: FileAssetCreationCommand,
    *,
    observed_at: str,
) -> FileAssetCreationResult:
    """Re-observe, validate, allocate, atomically publish, and read back one FileAsset."""

    try:
        source = observe_file_asset_source(Path(command.expected_source_path))
    except ReadBudgetExceeded:
        return FileAssetCreationResult(
            "source_unavailable",
            issues=(_issue("resource", f"来源文件超过 {DEFAULT_PAYLOAD_BUDGET} bytes 摄取上限"),),
        )
    except (OSError, UnsafePathError):
        return FileAssetCreationResult(
            "source_unavailable",
            issues=(_issue("location", "来源文件不能作为稳定、非 symlink 的普通文件安全读取"),),
        )
    if not _source_matches(command, source):
        return FileAssetCreationResult(
            "source_stale",
            issues=(_issue("integrity", "来源文件已不匹配 prepare-file-asset-intake 绑定的 size/hash"),),
            source_observation=source,
        )
    _, _, candidate_issues = _manifest(command, command.requested_candidate_id, observed_at, source)
    if candidate_issues:
        return FileAssetCreationResult(
            "candidate_rejected",
            issues=candidate_issues,
            source_observation=source,
        )
    if not durable_writes_enabled():
        return FileAssetCreationResult("durability_unavailable", source_observation=source)

    layout = LAYOUTS["file-asset"]
    completed: FileAssetCreationResult | None = None
    try:
        with allocation_lock(command.boundary, layout) as counter_path:
            preview = preview_object_id_locked(command.boundary, layout, counter_path)
            if preview is None:
                completed = FileAssetCreationResult(
                    "allocation_unavailable",
                    source_observation=source,
                    allocation_status="unavailable",
                )
            else:
                allocation = commit_object_id_locked(command.boundary, layout, preview)
                if allocation.status != "committed" or allocation.object_id is None:
                    completed = FileAssetCreationResult(
                        "allocation_stale" if allocation.status == "stale" else "allocation_unavailable",
                        actual_id=preview.object_id,
                        source_observation=source,
                        allocation_consumed=None if allocation.status == "uncertain" else False,
                        allocation_status=allocation.status,
                        allocation_result=allocation,
                    )
                else:
                    actual_id = allocation.object_id
                    fields, manifest_text, final_issues = _manifest(command, actual_id, observed_at, source)
                    if final_issues:
                        completed = FileAssetCreationResult(
                            "candidate_rejected",
                            issues=final_issues,
                            actual_id=actual_id,
                            actual_fields=fields,
                            manifest_text=manifest_text,
                            source_observation=source,
                            allocation_consumed=True,
                            allocation_status="committed",
                            allocation_result=allocation,
                        )
                    else:
                        members = {
                            "file-asset.yaml": manifest_text.encode("utf-8"),
                            "payload": source.payload,
                        }
                        created = atomic_create_directory_relative(
                            command.boundary.worktree_root,
                            layout.canonical_path(actual_id),
                            members,
                        )
                        if (
                            created.outcome != "created"
                            or created.namespace_state != "committed"
                            or created.durability != "file_and_directory"
                        ):
                            completed = FileAssetCreationResult(
                                "creation_conflict"
                                if created.outcome == "conflict" and created.namespace_state == "not_committed"
                                else "creation_unavailable",
                                actual_id=actual_id,
                                actual_fields=fields,
                                manifest_text=manifest_text,
                                source_observation=source,
                                allocation_consumed=True,
                                allocation_status="committed",
                                allocation_result=allocation,
                                creation_result=created,
                                residual_readback=_readback(command, actual_id),
                            )
                        else:
                            read = _readback(command, actual_id)
                            readback_ok = (
                                read.check_status == "mechanically_valid"
                                and read.fields == fields
                                and read.raw_text == manifest_text
                                and read.observed_size_bytes == source.source_size_bytes
                                and read.observed_content_sha256 == source.source_content_sha256
                                and read.payload_matches_manifest is True
                            )
                            if readback_ok:
                                completed = FileAssetCreationResult(
                                    "created",
                                    actual_id=actual_id,
                                    actual_fields=fields,
                                    manifest_text=manifest_text,
                                    source_observation=source,
                                    read=read,
                                    allocation_consumed=True,
                                    allocation_status="committed",
                                    allocation_result=allocation,
                                    creation_result=created,
                                )
                            else:
                                rollback = remove_directory_relative_if_members_equal(
                                    command.boundary.worktree_root,
                                    layout.canonical_path(actual_id),
                                    members,
                                )
                                rolled_back = rollback.outcome == "removed" and rollback.namespace_state == "committed"
                                completed = FileAssetCreationResult(
                                    "readback_failed",
                                    issues=read.issues,
                                    actual_id=actual_id,
                                    actual_fields=fields,
                                    manifest_text=manifest_text,
                                    source_observation=source,
                                    read=read,
                                    allocation_consumed=True,
                                    allocation_status="committed",
                                    allocation_result=allocation,
                                    creation_result=created,
                                    rollback_result=rollback,
                                    residual_readback=None if rolled_back else _readback(command, actual_id),
                                )
    except OSError:
        if completed is None:
            raise
        return replace(completed, coordination_release_uncertain=True)
    assert completed is not None
    return completed


__all__ = [
    "FileAssetCreationCommand",
    "FileAssetCreationResult",
    "FileAssetCreationStatus",
    "FileAssetSourceObservation",
    "create_file_asset",
    "observe_file_asset_source",
]
