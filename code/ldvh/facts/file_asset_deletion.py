"""Controlled active-to-deleted FileAsset directory transaction."""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    CreationBoundary,
    allocation_lock,
    relation_write_lock,
    serialize_fact_object,
)
from ldvh.facts.file_asset import DEFAULT_PAYLOAD_BUDGET, validate_file_asset_snapshot
from ldvh.facts.models import FactIssue, IssueCategory
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import parse_rfc3339
from ldvh.filesystem import (
    AtomicWriteResult,
    ReadBudgetExceeded,
    UnsafePathError,
    atomic_replace_directory_relative_if_members_equal,
    durable_writes_enabled,
    safe_read_relative,
)
from ldvh.governance.git import isolated_git_environment, windows_path_problem

FileAssetDeletionStatus = Literal[
    "candidate_unavailable",
    "candidate_rejected",
    "conflict",
    "git_anchor_unavailable",
    "git_anchor_mismatch",
    "incoming_scan_unavailable",
    "incoming_reference",
    "durability_unavailable",
    "replacement_unavailable",
    "deleted_with_residue",
    "readback_failed",
    "deleted",
]
_GIT_OID = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")


@dataclass(frozen=True, slots=True)
class FileAssetRecoveryAnchor:
    commit: str
    path: str
    blob_oid: str

    def to_json(self) -> dict[str, str]:
        return {"commit": self.commit, "path": self.path, "blob_oid": self.blob_oid}


@dataclass(frozen=True, slots=True)
class FileAssetDeletionCommand:
    boundary: CreationBoundary
    schemas: Mapping[str, FactSchema]
    object_id: str
    expected_content_fingerprint: str
    deletion_summary: str


@dataclass(frozen=True, slots=True)
class FileAssetDeletionResult:
    status: FileAssetDeletionStatus
    issues: tuple[FactIssue, ...] = ()
    current: FactReadResult | None = None
    readback: FactReadResult | None = None
    previous_content_fingerprint: str | None = None
    content_fingerprint: str | None = None
    fields: dict[str, Any] | None = None
    recovery: FileAssetRecoveryAnchor | None = None
    incoming_scan_complete: bool = False
    incoming_refs: tuple[str, ...] = ()
    replacement_result: AtomicWriteResult | None = None
    coordination_release_uncertain: bool = False


def _issue(category: IssueCategory, summary: str, field_path: str | None = None) -> FactIssue:
    return FactIssue(category, summary, field_path)


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes] | None:
    if windows_path_problem(root) is not None:
        return None
    environment = isolated_git_environment()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        return subprocess.run(
            ("git", "--no-optional-locks", "-C", os.fspath(root), *arguments),
            check=False,
            capture_output=True,
            env=environment,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _head_entry(root: Path, commit: str, path: str) -> tuple[str, bytes] | None:
    listing = _git(root, "ls-tree", "-z", commit, "--", path)
    if listing is None or listing.returncode != 0:
        return None
    entries = tuple(item for item in listing.stdout.split(b"\0") if item)
    if len(entries) != 1:
        return None
    meta, separator, observed_path = entries[0].partition(b"\t")
    parts = meta.split(b" ")
    if separator != b"\t" or len(parts) != 3 or parts[0] not in {b"100644", b"100755"} or parts[1] != b"blob":
        return None
    try:
        decoded_path = observed_path.decode("utf-8")
        oid = parts[2].decode("ascii")
    except UnicodeDecodeError:
        return None
    if decoded_path != path or _GIT_OID.fullmatch(oid) is None:
        return None
    content = _git(root, "cat-file", "blob", oid)
    if content is None or content.returncode != 0:
        return None
    return oid, content.stdout


def _recovery_anchor(
    root: Path,
    object_id: str,
    manifest: bytes,
    payload: bytes,
) -> tuple[FileAssetRecoveryAnchor | None, str | None]:
    head = _git(root, "rev-parse", "--verify", "-q", "HEAD^{commit}")
    if head is None or head.returncode != 0:
        return None, "当前 HEAD commit 无法可信读取"
    try:
        commit = head.stdout.decode("ascii").strip()
    except UnicodeDecodeError:
        return None, "当前 HEAD commit 不是 ASCII object id"
    if _GIT_OID.fullmatch(commit) is None:
        return None, "当前 HEAD commit object id 格式无法确认"
    layout = LAYOUTS["file-asset"]
    manifest_path = f"{layout.canonical_path(object_id)}/file-asset.yaml"
    payload_path = layout.canonical_payload_path(object_id)
    assert payload_path is not None
    manifest_entry = _head_entry(root, commit, manifest_path)
    payload_entry = _head_entry(root, commit, payload_path)
    if manifest_entry is None or payload_entry is None:
        return None, "当前 HEAD 未完整保存该 FileAsset active carrier"
    if manifest_entry[1] != manifest or payload_entry[1] != payload:
        return None, "当前 Working Tree FileAsset 不等于 HEAD 中已提交 carrier"
    return FileAssetRecoveryAnchor(commit, payload_path, payload_entry[0]), None


def _incoming_references(command: FileAssetDeletionCommand) -> tuple[tuple[str, ...], bool]:
    index = ProjectFactIndex(
        command.boundary.worktree_root,
        command.boundary.governed_project_id,
        dict(command.schemas),
        command.boundary.git_common_dir,
    )
    reads, complete = index.scan_valid_objects("workcase", require_all_canonical_valid=True)
    incoming: list[str] = []
    for read in reads:
        fields = read.fields
        if fields is None:
            continue
        relations = fields.get("relations")
        for relation in relations if isinstance(relations, list) else []:
            if not isinstance(relation, Mapping) or relation.get("relation_key") != "has-file-asset":
                continue
            target = relation.get("target")
            if not isinstance(target, Mapping):
                continue
            if (
                target.get("governed_project_id") == command.boundary.governed_project_id
                and target.get("fact_type_key") == "file-asset"
                and target.get("object_id") == command.object_id
            ):
                incoming.append(str(fields.get("object_id")))
    return tuple(sorted(set(incoming))), complete


def _read(command: FileAssetDeletionCommand) -> FactReadResult:
    return read_fact_object(
        command.boundary.worktree_root,
        LAYOUTS["file-asset"],
        command.schemas["file-asset"],
        command.object_id,
        expected_common_dir=command.boundary.git_common_dir,
    )


def _locked_delete(command: FileAssetDeletionCommand, *, observed_at: str) -> FileAssetDeletionResult:
    current = _read(command)
    if current.check_status == "unavailable":
        return FileAssetDeletionResult("candidate_unavailable", issues=current.issues, current=current)
    if (
        current.check_status != "mechanically_valid"
        or current.fields is None
        or current.raw_text is None
        or current.current_bytes_confirmed is not True
        or current.fields.get("status") != "active"
    ):
        return FileAssetDeletionResult("candidate_rejected", issues=current.issues, current=current)
    if current.content_fingerprint != command.expected_content_fingerprint:
        return FileAssetDeletionResult(
            "conflict",
            issues=(_issue("integrity", "FileAsset 当前内容指纹与删除请求基线不一致"),),
            current=current,
            previous_content_fingerprint=current.content_fingerprint,
        )
    updated_before = parse_rfc3339(current.fields.get("updated_at"))
    deleted_at = parse_rfc3339(observed_at)
    if updated_before is None or deleted_at is None or deleted_at <= updated_before:
        return FileAssetDeletionResult(
            "candidate_rejected",
            issues=(_issue("schema", "删除事件时点必须晚于当前 updated_at", "deleted_at"),),
            current=current,
            previous_content_fingerprint=current.content_fingerprint,
        )

    incoming, scan_complete = _incoming_references(command)
    if not scan_complete:
        return FileAssetDeletionResult(
            "incoming_scan_unavailable",
            current=current,
            previous_content_fingerprint=current.content_fingerprint,
            incoming_scan_complete=False,
        )
    if incoming:
        return FileAssetDeletionResult(
            "incoming_reference",
            issues=(_issue("relation", "FileAsset 仍存在受保护的入向 has-file-asset 引用"),),
            current=current,
            previous_content_fingerprint=current.content_fingerprint,
            incoming_scan_complete=True,
            incoming_refs=incoming,
        )

    layout = LAYOUTS["file-asset"]
    payload_path = layout.canonical_payload_path(command.object_id)
    assert payload_path is not None
    try:
        manifest = safe_read_relative(
            command.boundary.worktree_root,
            f"{layout.canonical_path(command.object_id)}/file-asset.yaml",
        )
        payload = safe_read_relative(
            command.boundary.worktree_root,
            payload_path,
            max_bytes=DEFAULT_PAYLOAD_BUDGET,
        )
    except (OSError, ReadBudgetExceeded, UnsafePathError):
        return FileAssetDeletionResult(
            "candidate_unavailable",
            current=current,
            previous_content_fingerprint=current.content_fingerprint,
            incoming_scan_complete=True,
        )
    rebound = validate_file_asset_snapshot(
        command.schemas["file-asset"],
        command.object_id,
        manifest,
        payload,
        member_names=("file-asset.yaml", "payload"),
    )
    if (
        rebound.check_status != "mechanically_valid"
        or rebound.fields is None
        or rebound.fields.get("status") != "active"
        or rebound.current_bytes_confirmed is not True
        or rebound.content_fingerprint != command.expected_content_fingerprint
        or rebound.fields != current.fields
    ):
        return FileAssetDeletionResult(
            "conflict",
            issues=(_issue("integrity", "FileAsset 关系扫描后的载体不再匹配删除请求 CAS"),),
            current=current,
            previous_content_fingerprint=current.content_fingerprint,
            incoming_scan_complete=True,
        )
    anchor, anchor_problem = _recovery_anchor(
        command.boundary.worktree_root,
        command.object_id,
        manifest,
        payload,
    )
    if anchor is None:
        return FileAssetDeletionResult(
            "git_anchor_unavailable" if "无法" in (anchor_problem or "") else "git_anchor_mismatch",
            issues=(_issue("git-traceability", anchor_problem or "Git 恢复锚点未形成"),),
            current=current,
            previous_content_fingerprint=current.content_fingerprint,
            incoming_scan_complete=True,
        )

    fields = {
        **rebound.fields,
        "updated_at": observed_at,
        "status": "deleted",
        "disposition_summary": command.deletion_summary,
        "deleted_at": observed_at,
        "recovery": anchor.to_json(),
    }
    manifest_text = serialize_fact_object(layout, fields, None)
    snapshot = validate_file_asset_snapshot(
        command.schemas["file-asset"],
        command.object_id,
        manifest_text.encode("utf-8"),
        None,
        member_names=("file-asset.yaml",),
    )
    if snapshot.check_status != "mechanically_valid":
        return FileAssetDeletionResult(
            "candidate_rejected",
            issues=snapshot.issues,
            current=current,
            previous_content_fingerprint=current.content_fingerprint,
            fields=fields,
            recovery=anchor,
            incoming_scan_complete=True,
        )
    replacement = atomic_replace_directory_relative_if_members_equal(
        command.boundary.worktree_root,
        layout.canonical_path(command.object_id),
        {"file-asset.yaml": manifest, "payload": payload},
        {"file-asset.yaml": manifest_text.encode("utf-8")},
    )
    if replacement.namespace_state != "committed":
        return FileAssetDeletionResult(
            "conflict" if replacement.outcome == "conflict" else "replacement_unavailable",
            current=current,
            previous_content_fingerprint=current.content_fingerprint,
            fields=fields,
            recovery=anchor,
            incoming_scan_complete=True,
            replacement_result=replacement,
        )
    readback = _read(command)
    readback_ok = (
        readback.check_status == "mechanically_valid"
        and readback.fields == fields
        and readback.raw_text == manifest_text
        and readback.payload_canonical_path is None
        and readback.current_bytes_confirmed is False
    )
    replacement_complete = (
        replacement.durability == "file_and_directory" and replacement.cleanup == "clean"
    )
    status: FileAssetDeletionStatus
    if not readback_ok:
        status = "readback_failed"
    elif not replacement_complete:
        status = "deleted_with_residue"
    else:
        status = "deleted"
    return FileAssetDeletionResult(
        status,
        issues=() if readback_ok else readback.issues,
        current=current,
        readback=readback,
        previous_content_fingerprint=current.content_fingerprint,
        content_fingerprint=readback.content_fingerprint,
        fields=fields,
        recovery=anchor,
        incoming_scan_complete=True,
        replacement_result=replacement,
    )


def delete_file_asset(
    command: FileAssetDeletionCommand,
    *,
    observed_at: str,
) -> FileAssetDeletionResult:
    if not durable_writes_enabled():
        return FileAssetDeletionResult("durability_unavailable")
    if "file-asset" not in command.schemas or "workcase" not in command.schemas:
        return FileAssetDeletionResult("candidate_unavailable")
    completed: FileAssetDeletionResult | None = None
    try:
        with relation_write_lock(command.boundary):
            with allocation_lock(command.boundary, LAYOUTS["file-asset"]):
                completed = _locked_delete(command, observed_at=observed_at)
    except OSError:
        if completed is None:
            raise
        return replace(completed, coordination_release_uncertain=True)
    assert completed is not None
    return completed


__all__ = [
    "FileAssetDeletionCommand",
    "FileAssetDeletionResult",
    "FileAssetDeletionStatus",
    "FileAssetRecoveryAnchor",
    "delete_file_asset",
]
