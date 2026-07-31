"""Safely read one exact fact-object path from the current Git working tree."""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ldvh.facts.content import MAX_FACT_BYTES, validate_fact_content
from ldvh.facts.contracts import FactTypeLayout
from ldvh.facts.file_asset import DEFAULT_PAYLOAD_BUDGET, read_file_asset
from ldvh.facts.models import FactIssue
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import parse_rfc3339
from ldvh.filesystem import ReadBudgetExceeded, UnsafePathError, safe_read_relative, validate_relative_regular_file
from ldvh.governance.git import isolated_git_environment, windows_path_problem

CheckStatus = Literal["mechanically_valid", "invalid", "not_found", "unavailable"]

# One scan's memo of Git worktree identity per root; the identity cannot change
# within a single scan, so repeat rev-parse subprocesses are redundant.
GitIdentityCache = dict[str, tuple[Path, Path] | None]


@dataclass(frozen=True, slots=True)
class FactReadResult:
    canonical_path: str
    carrier: str
    check_status: CheckStatus
    fields: dict[str, Any] | None
    body: str | None
    issues: tuple[FactIssue, ...]
    content_fingerprint: str | None = None
    raw_text: str | None = None
    raw_byte_count: int | None = None
    integrity_coverage: tuple[str, ...] = ()
    payload_canonical_path: str | None = None
    observed_size_bytes: int | None = None
    observed_content_sha256: str | None = None
    payload_matches_manifest: bool | None = None
    current_bytes_confirmed: bool | None = None


def _safe_regular_file(root: Path, relative_path: str) -> tuple[Path, FactIssue | None, CheckStatus | None]:
    candidate = root / relative_path
    try:
        validate_relative_regular_file(root, relative_path)
    except FileNotFoundError:
        return candidate, FactIssue("location", "事实对象预期位置不存在"), "not_found"
    except UnsafePathError:
        return candidate, FactIssue("location", "事实对象 canonical path 必须是非 link/reparse 普通文件"), "invalid"
    except OSError:
        return candidate, FactIssue("location", "无法安全读取事实对象路径"), "unavailable"
    return candidate, None, None


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes] | None:
    if windows_path_problem(root) is not None:
        return None
    try:
        return subprocess.run(
            ("git", "-C", os.fspath(root), *arguments),
            check=False,
            capture_output=True,
            env=isolated_git_environment(),
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_identity(root: Path, cache: GitIdentityCache | None = None) -> tuple[Path, Path] | None:
    key = os.fspath(root)
    if cache is not None and key in cache:
        return cache[key]
    result = _git(root, "rev-parse", "--path-format=absolute", "--show-toplevel", "--git-common-dir")
    identity: tuple[Path, Path] | None = None
    if result is not None and result.returncode == 0:
        try:
            lines = result.stdout.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            lines = []
        if len(lines) == 2:
            identity = Path(lines[0]).resolve(), Path(lines[1]).resolve()
    if cache is not None:
        cache[key] = identity
    return identity


def _identity_issue(
    root: Path,
    expected_common_dir: Path | None,
    cache: GitIdentityCache | None = None,
) -> tuple[FactIssue | None, CheckStatus | None]:
    identity = _git_identity(root, cache)
    if identity is None:
        return FactIssue("git-traceability", "无法确认事实对象所在 Git Working Tree 身份"), "unavailable"
    worktree_root, common_dir = identity
    if worktree_root != root.resolve() or (
        expected_common_dir is not None and common_dir != expected_common_dir.resolve()
    ):
        return FactIssue("git-traceability", "事实对象读取边界与已解析 Git 身份不一致"), "unavailable"
    return None, None


def read_fact_object(
    root: Path,
    layout: FactTypeLayout,
    schema: FactSchema,
    object_id: str,
    *,
    expected_common_dir: Path | None = None,
    max_bytes: int = MAX_FACT_BYTES,
    git_identity_cache: GitIdentityCache | None = None,
) -> FactReadResult:
    """Read and mechanically validate one source-selected fact object."""

    relative_path = layout.canonical_path(object_id)
    identity_issue, identity_status = _identity_issue(root, expected_common_dir, git_identity_cache)
    if identity_issue is not None:
        return FactReadResult(
            relative_path,
            layout.carrier,
            identity_status or "unavailable",
            None,
            None,
            (identity_issue,),
        )
    if layout.carrier == "file-asset-directory":
        file_asset = read_file_asset(
            root,
            layout,
            schema,
            object_id,
            payload_budget=min(DEFAULT_PAYLOAD_BUDGET, max_bytes),
        )
        identity_issue, identity_status = _identity_issue(root, expected_common_dir, git_identity_cache)
        if identity_issue is not None:
            return FactReadResult(
                relative_path,
                layout.carrier,
                identity_status or "unavailable",
                None,
                None,
                (identity_issue,),
            )
        return FactReadResult(
            relative_path,
            layout.carrier,
            file_asset.check_status,
            file_asset.fields,
            None,
            file_asset.issues,
            file_asset.content_fingerprint,
            file_asset.manifest_raw_text,
            file_asset.manifest_byte_count,
            file_asset.coverage,
            file_asset.payload_canonical_path,
            file_asset.observed_size_bytes,
            file_asset.observed_content_sha256,
            file_asset.payload_matches_manifest,
            file_asset.current_bytes_confirmed,
        )
    _, location_issue, location_status = _safe_regular_file(root, relative_path)
    if location_issue is not None:
        return FactReadResult(
            relative_path, layout.carrier, location_status or "invalid", None, None, (location_issue,)
        )
    effective_max_bytes = min(MAX_FACT_BYTES, max_bytes)
    if effective_max_bytes <= 0:
        return FactReadResult(
            relative_path, layout.carrier, "unavailable", None, None,
            (FactIssue("reference", "事实对象聚合读取预算已耗尽"),),
        )
    try:
        raw_bytes = safe_read_relative(root, relative_path, max_bytes=effective_max_bytes)
    except ReadBudgetExceeded:
        return FactReadResult(
            relative_path, layout.carrier, "unavailable", None, None,
            (FactIssue("parse", f"事实对象载体超过 {effective_max_bytes} bytes 读取预算"),),
            raw_byte_count=effective_max_bytes,
        )
    except UnsafePathError:
        return FactReadResult(
            relative_path, layout.carrier, "invalid", None, None,
            (FactIssue("location", "事实对象 canonical path 必须是非 link/reparse 普通文件"),),
        )
    except OSError:
        return FactReadResult(
            relative_path, layout.carrier, "unavailable", None, None,
            (FactIssue("location", "事实对象文件在安全读取时发生变化或不可访问"),),
        )
    identity_issue, identity_status = _identity_issue(root, expected_common_dir, git_identity_cache)
    if identity_issue is not None:
        return FactReadResult(
            relative_path,
            layout.carrier,
            identity_status or "unavailable",
            None,
            None,
            (identity_issue,),
        )

    validation = validate_fact_content(layout, schema, object_id, raw_bytes, max_bytes=effective_max_bytes)
    fingerprint = validation.content_fingerprint
    if validation.check_status == "invalid":
        fingerprint = _repair_fingerprint(validation.fields, layout, object_id, validation.raw_text or "")
    return FactReadResult(
        relative_path,
        layout.carrier,
        validation.check_status,
        validation.fields,
        validation.body,
        validation.issues,
        fingerprint,
        validation.raw_text,
        validation.raw_byte_count,
    )


def _repair_fingerprint(
    fields: dict[str, Any] | None,
    layout: FactTypeLayout,
    object_id: str,
    text: str,
) -> str | None:
    """Return a CAS fingerprint only for a parseable historical repair target."""

    if fields is None:
        return None
    if fields.get("object_id") != object_id or fields.get("fact_type_key") != layout.fact_type_key:
        return None
    if parse_rfc3339(fields.get("created_at")) is None or parse_rfc3339(fields.get("updated_at")) is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = ["CheckStatus", "FactReadResult", "read_fact_object"]
