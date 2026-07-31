"""Safely read one canonical FileAsset directory carrier."""

from __future__ import annotations

import errno
import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import FactTypeLayout
from ldvh.facts.models import FactIssue, IssueCategory
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import validate_fact_object
from ldvh.filesystem import ReadBudgetExceeded, UnsafePathError

FileAssetStatus = Literal["mechanically_valid", "invalid", "not_found", "unavailable"]
CoverageCheck = Literal[
    "manifest-read",
    "members-closed",
    "payload-size-read",
    "payload-sha256-computed",
]
DEFAULT_MANIFEST_BUDGET = 256 * 1024
DEFAULT_PAYLOAD_BUDGET = 4 * 1024 * 1024

_EXPECTED_MEMBERS = frozenset({"file-asset.yaml", "payload"})


@dataclass(frozen=True, slots=True)
class FileAssetRead:
    """Bounded observation of one canonical FileAsset directory."""

    object_directory: str
    check_status: FileAssetStatus
    coverage: tuple[CoverageCheck, ...]
    fields: dict[str, Any] | None
    issues: tuple[FactIssue, ...]
    observed_size_bytes: int | None
    observed_content_sha256: str | None
    payload_matches_manifest: bool | None
    current_bytes_confirmed: bool
    default_candidate: bool
    payload_canonical_path: str
    content_fingerprint: str | None
    manifest_raw_text: str | None
    manifest_byte_count: int | None


@dataclass(frozen=True, slots=True)
class FileAssetSnapshotValidation:
    """Pure validation of one complete manifest/payload directory after-image."""

    check_status: Literal["mechanically_valid", "invalid", "unavailable"]
    fields: dict[str, Any] | None
    issues: tuple[FactIssue, ...]
    observed_size_bytes: int | None
    observed_content_sha256: str | None
    payload_matches_manifest: bool | None
    current_bytes_confirmed: bool
    content_fingerprint: str | None
    manifest_raw_text: str | None


def _issue(
    category: IssueCategory,
    summary: str,
    field_path: str | None = None,
) -> FactIssue:
    return FactIssue(category, summary, field_path)


def _coverage(*, manifest: bool, members: bool, size: bool, digest: bool) -> tuple[CoverageCheck, ...]:
    checks: list[CoverageCheck] = []
    if manifest:
        checks.append("manifest-read")
    if members:
        checks.append("members-closed")
    if size:
        checks.append("payload-size-read")
    if digest:
        checks.append("payload-sha256-computed")
    return tuple(checks)


def _empty_result(
    object_directory: str,
    payload_path: str,
    status: FileAssetStatus,
    issue: FactIssue,
) -> FileAssetRead:
    return FileAssetRead(
        object_directory,
        status,
        (),
        None,
        (issue,),
        None,
        None,
        None,
        False,
        False,
        payload_path,
        None,
        None,
        None,
    )


def _stat_signature(observed: os.stat_result, *, directory: bool = False) -> tuple[int, ...]:
    expected = stat.S_ISDIR(observed.st_mode) if directory else stat.S_ISREG(observed.st_mode)
    if not expected:
        raise UnsafePathError("FileAsset member has the wrong filesystem type")
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


def _topology_signature(observed: os.stat_result, *, directory: bool = False) -> tuple[int, ...]:
    signature = _stat_signature(observed, directory=directory)
    return signature[0], signature[1], signature[2], signature[-1]


def _open_relative_directory(
    root_descriptor: int,
    components: tuple[str, ...],
    *,
    no_follow: int,
    directory_flag: int,
) -> int:
    descriptor = os.dup(root_descriptor)
    try:
        for component in components:
            next_descriptor = os.open(
                component,
                os.O_RDONLY | directory_flag | no_follow,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _read_regular_member(
    directory_descriptor: int,
    name: str,
    *,
    max_bytes: int,
    no_follow: int,
) -> bytes:
    descriptor = os.open(name, os.O_RDONLY | no_follow, dir_fd=directory_descriptor)
    try:
        before = os.fstat(descriptor)
        _stat_signature(before)
        if before.st_size > max_bytes:
            raise ReadBudgetExceeded("FileAsset member exceeds the bounded-read budget")
        chunks: list[bytes] = []
        observed_size = 0
        while observed_size <= max_bytes:
            chunk = os.read(descriptor, min(64 * 1024, max_bytes + 1 - observed_size))
            if not chunk:
                break
            chunks.append(chunk)
            observed_size += len(chunk)
        if observed_size > max_bytes:
            raise ReadBudgetExceeded("FileAsset member exceeds the bounded-read budget")
        after = os.fstat(descriptor)
        if _stat_signature(before) != _stat_signature(after):
            raise OSError("FileAsset member changed while it was read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _bounded_member_names(directory_descriptor: int) -> tuple[set[str], bool]:
    """Observe at most one member beyond the two-name closed carrier."""

    names: set[str] = set()
    with os.scandir(directory_descriptor) as entries:
        for entry in entries:
            names.add(entry.name)
            if len(names) > len(_EXPECTED_MEMBERS):
                return names, False
    return names, True


def validate_file_asset_snapshot(
    schema: FactSchema,
    object_id: str,
    manifest_bytes: bytes | None,
    payload_bytes: bytes | None,
    *,
    member_names: tuple[str, ...] = ("file-asset.yaml", "payload"),
    manifest_budget: int = DEFAULT_MANIFEST_BUDGET,
    payload_budget: int = DEFAULT_PAYLOAD_BUDGET,
) -> FileAssetSnapshotValidation:
    """Validate supplied bytes without reading Git or the filesystem."""

    issues: list[FactIssue] = []
    unavailable = False
    names = tuple(sorted(member_names))
    if len(set(names)) != len(names):
        issues.append(_issue("location", "FileAsset after-image 成员名不得重复"))
    for name in sorted(_EXPECTED_MEMBERS - set(names)):
        issues.append(_issue("location", "FileAsset 目录缺少固定成员", name))
    for name in sorted(set(names) - _EXPECTED_MEMBERS):
        issues.append(_issue("location", "FileAsset 目录包含未知成员", name))
    if manifest_bytes is None and "file-asset.yaml" in names:
        issues.append(_issue("location", "FileAsset after-image 缺少可观察 manifest", "file-asset.yaml"))
        unavailable = True
    elif manifest_bytes is not None and len(manifest_bytes) > manifest_budget:
        issues.append(_issue("resource", f"manifest 超过 {manifest_budget} bytes 读取预算"))
        unavailable = True
    if payload_bytes is None and "payload" in names:
        issues.append(_issue("location", "FileAsset after-image 缺少可观察 payload", "payload"))
        unavailable = True
    elif payload_bytes is not None and len(payload_bytes) > payload_budget:
        issues.append(_issue("resource", f"payload 超过 {payload_budget} bytes 读取预算"))
        unavailable = True

    fields: dict[str, Any] | None = None
    manifest_text: str | None = None
    if manifest_bytes is not None and len(manifest_bytes) <= manifest_budget:
        try:
            manifest_text = manifest_bytes.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(_issue("parse", "manifest 必须是 UTF-8 YAML"))
        else:
            parsed = parse_yaml_object(manifest_text)
            if parsed.fields is None or parsed.issues:
                issues.extend(parsed.issues or (_issue("parse", "manifest 无法按 YAML 1.2 唯一解析为 mapping"),))
            else:
                fields = parsed.fields
                issues.extend(validate_fact_object("file-asset", fields, schema))
                if fields.get("object_id") != object_id:
                    issues.append(_issue("identity", "object_id 与对象目录名不一致", "object_id"))

    observed_size = None if payload_bytes is None else len(payload_bytes)
    observed_digest = None if payload_bytes is None else hashlib.sha256(payload_bytes).hexdigest()
    payload_matches: bool | None = None
    if fields is not None and observed_size is not None and observed_digest is not None:
        declared_size = fields.get("size_bytes")
        declared_digest = fields.get("content_sha256")
        if (
            isinstance(declared_size, int)
            and not isinstance(declared_size, bool)
            and declared_size >= 0
            and isinstance(declared_digest, str)
            and len(declared_digest) == 64
            and all(character in "0123456789abcdef" for character in declared_digest)
        ):
            size_matches = observed_size == declared_size
            digest_matches = observed_digest == declared_digest
            payload_matches = size_matches and digest_matches
            if not size_matches:
                issues.append(_issue("integrity", "payload 实际字节数与 manifest 不一致", "size_bytes"))
            if not digest_matches:
                issues.append(_issue("integrity", "payload 实际 SHA-256 与 manifest 不一致", "content_sha256"))

    if unavailable:
        status: Literal["mechanically_valid", "invalid", "unavailable"] = "unavailable"
    elif issues:
        status = "invalid"
    else:
        status = "mechanically_valid"
    current_bytes_confirmed = (
        status == "mechanically_valid" and set(names) == _EXPECTED_MEMBERS and payload_matches is True
    )
    content_fingerprint: str | None = None
    if not unavailable and manifest_bytes is not None and observed_size is not None and observed_digest is not None:
        fingerprint = hashlib.sha256()
        fingerprint.update(b"ldvh:file-asset:v1\0")
        fingerprint.update(len(manifest_bytes).to_bytes(8, "big"))
        fingerprint.update(manifest_bytes)
        fingerprint.update(observed_size.to_bytes(8, "big"))
        fingerprint.update(bytes.fromhex(observed_digest))
        content_fingerprint = fingerprint.hexdigest()
    return FileAssetSnapshotValidation(
        status,
        fields,
        tuple(issues),
        observed_size,
        observed_digest,
        payload_matches,
        current_bytes_confirmed,
        content_fingerprint,
        manifest_text,
    )


def read_file_asset(
    root: Path,
    layout: FactTypeLayout,
    schema: FactSchema,
    object_id: str,
    *,
    manifest_budget: int = DEFAULT_MANIFEST_BUDGET,
    payload_budget: int = DEFAULT_PAYLOAD_BUDGET,
) -> FileAssetRead:
    """Read one source-selected canonical directory without following links."""

    directory_text = layout.canonical_path(object_id)
    payload_path = layout.canonical_payload_path(object_id) or f"{directory_text}/payload"
    relative_directory = Path(directory_text)

    def empty(status: FileAssetStatus, issue: FactIssue) -> FileAssetRead:
        return _empty_result(directory_text, payload_path, status, issue)

    if manifest_budget <= 0 or payload_budget < 0:
        return empty(
            "unavailable",
            _issue("resource", "FileAsset 读取预算必须为正 manifest budget 和非负 payload budget"),
        )
    if (
        layout.fact_type_key != "file-asset"
        or layout.carrier != "file-asset-directory"
        or not root.is_absolute()
        or relative_directory.is_absolute()
        or len(relative_directory.parts) != 3
        or relative_directory.parts[:2] != ("ldvh-base", "file-assets")
        or layout.object_id_pattern.fullmatch(object_id) is None
        or relative_directory.name != object_id
    ):
        return empty(
            "invalid",
            _issue("location", "FileAsset 只允许绝对 worktree 下的 canonical 对象目录"),
        )
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if os.name != "posix" or no_follow is None or directory_flag is None:
        return empty(
            "unavailable",
            _issue("location", "当前平台没有完成 FileAsset 所需的同目录 no-follow descriptor 读取验证"),
        )

    root_descriptor: int | None = None
    directory_descriptor: int | None = None
    try:
        root_descriptor = os.open(root, os.O_RDONLY | directory_flag | no_follow)
    except FileNotFoundError:
        return empty("unavailable", _issue("location", "Git Working Tree root 不存在"))
    except OSError as error:
        status: FileAssetStatus = "invalid" if error.errno in {errno.ELOOP, errno.ENOTDIR} else "unavailable"
        return empty(
            status,
            _issue("location", "Git Working Tree root 必须是可稳定打开的非 symlink 普通目录"),
        )
    try:
        try:
            _stat_signature(os.fstat(root_descriptor), directory=True)
            directory_descriptor = _open_relative_directory(
                root_descriptor,
                relative_directory.parts,
                no_follow=no_follow,
                directory_flag=directory_flag,
            )
        except FileNotFoundError:
            return empty("not_found", _issue("location", "FileAsset canonical 目录不存在"))
        except OSError as error:
            status = "invalid" if error.errno in {errno.ELOOP, errno.ENOTDIR} else "unavailable"
            return empty(
                status,
                _issue("location", "FileAsset canonical 目录必须是可稳定打开的非 symlink 普通目录"),
            )

        issues: list[FactIssue] = []
        unavailable = False
        closure_stable = True
        manifest_read = False
        size_read = False
        digest_computed = False
        initial_signatures: dict[str, tuple[int, ...]] = {}
        try:
            before_list = _stat_signature(os.fstat(directory_descriptor), directory=True)
            member_names, initial_enumeration_complete = _bounded_member_names(directory_descriptor)
            after_list = _stat_signature(os.fstat(directory_descriptor), directory=True)
            if before_list != after_list:
                unavailable = True
                closure_stable = False
                issues.append(_issue("location", "FileAsset 目录在成员枚举期间发生变化"))
            initial_signatures["directory"] = after_list
        except OSError:
            unavailable = True
            closure_stable = False
            initial_enumeration_complete = False
            member_names = set()
            issues.append(_issue("location", "FileAsset 目录无法从同一 descriptor 稳定枚举"))
        missing = sorted(_EXPECTED_MEMBERS - member_names)
        unknown = sorted(member_names - _EXPECTED_MEMBERS)
        for name in missing:
            issues.append(_issue("location", "FileAsset 目录缺少固定成员", name))
        for name in unknown:
            issues.append(_issue("location", "FileAsset 目录包含未知成员", name))
        if not initial_enumeration_complete:
            issues.append(_issue("resource", "FileAsset 目录至少出现第三个成员，枚举已按闭集上限停止"))

        for name in sorted(_EXPECTED_MEMBERS & member_names):
            try:
                observed = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
                initial_signatures[name] = _stat_signature(observed)
            except UnsafePathError:
                issues.append(_issue("location", "固定成员必须是非 symlink 普通文件", name))
            except OSError:
                unavailable = True
                issues.append(_issue("location", "固定成员在读取前不可稳定观察", name))

        fields: dict[str, Any] | None = None
        manifest_bytes: bytes | None = None
        manifest_text: str | None = None
        if "file-asset.yaml" in initial_signatures:
            try:
                manifest_bytes = _read_regular_member(
                    directory_descriptor,
                    "file-asset.yaml",
                    max_bytes=manifest_budget,
                    no_follow=no_follow,
                )
                manifest_read = True
            except ReadBudgetExceeded:
                unavailable = True
                issues.append(_issue("resource", f"manifest 超过 {manifest_budget} bytes 读取预算"))
            except OSError:
                unavailable = True
                issues.append(_issue("location", "manifest 在同一目录 descriptor 读取时发生变化或不可访问"))
            else:
                try:
                    manifest_text = manifest_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    issues.append(_issue("parse", "manifest 必须是 UTF-8 YAML"))
                else:
                    parsed = parse_yaml_object(manifest_text)
                    if parsed.fields is None or parsed.issues:
                        issues.extend(
                            parsed.issues or (_issue("parse", "manifest 无法按 YAML 1.2 唯一解析为 mapping"),)
                        )
                    else:
                        fields = parsed.fields
                        issues.extend(validate_fact_object("file-asset", fields, schema))
                        if fields.get("object_id") != object_id:
                            issues.append(
                                _issue("identity", "object_id 与请求引用及对象目录名不一致", "object_id")
                            )

        payload_bytes: bytes | None = None
        observed_size: int | None = None
        observed_digest: str | None = None
        if "payload" in initial_signatures:
            try:
                payload_bytes = _read_regular_member(
                    directory_descriptor,
                    "payload",
                    max_bytes=payload_budget,
                    no_follow=no_follow,
                )
            except ReadBudgetExceeded:
                unavailable = True
                issues.append(_issue("resource", f"payload 超过 {payload_budget} bytes 读取预算"))
            except OSError:
                unavailable = True
                issues.append(_issue("location", "payload 在同一目录 descriptor 读取时发生变化或不可访问"))
            else:
                observed_size = len(payload_bytes)
                size_read = True
                observed_digest = hashlib.sha256(payload_bytes).hexdigest()
                digest_computed = True

        members_closed = closure_stable and initial_enumeration_complete and member_names == _EXPECTED_MEMBERS
        try:
            before_final_list = _stat_signature(os.fstat(directory_descriptor), directory=True)
            final_names, final_enumeration_complete = _bounded_member_names(directory_descriptor)
            after_final_list = _stat_signature(os.fstat(directory_descriptor), directory=True)
            if before_final_list != after_final_list:
                unavailable = True
                closure_stable = False
                members_closed = False
                issues.append(_issue("location", "FileAsset 目录在读取后枚举期间发生变化"))
            if initial_enumeration_complete and final_enumeration_complete and final_names != member_names:
                unavailable = True
                closure_stable = False
                members_closed = False
                issues.append(_issue("location", "FileAsset 目录成员在本次读取期间发生变化"))
            if not final_enumeration_complete:
                members_closed = False
                issues.append(_issue("resource", "读取后 FileAsset 目录至少出现第三个成员，闭集复核未完成"))
            if initial_signatures.get("directory") != after_final_list:
                unavailable = True
                closure_stable = False
                members_closed = False
                issues.append(_issue("location", "FileAsset 目录元数据在本次读取期间发生变化"))
            for name in sorted(_EXPECTED_MEMBERS & member_names):
                if name not in initial_signatures:
                    continue
                after = _stat_signature(os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False))
                if initial_signatures[name] != after:
                    unavailable = True
                    closure_stable = False
                    members_closed = False
                    issues.append(_issue("location", "固定成员在本次读取期间发生变化", name))

            current_descriptor = _open_relative_directory(
                root_descriptor,
                relative_directory.parts,
                no_follow=no_follow,
                directory_flag=directory_flag,
            )
            try:
                if _topology_signature(os.fstat(current_descriptor), directory=True) != _topology_signature(
                    os.fstat(directory_descriptor), directory=True
                ):
                    unavailable = True
                    closure_stable = False
                    members_closed = False
                    issues.append(_issue("location", "canonical path 不再指向本次读取持有的 FileAsset 目录"))
            finally:
                os.close(current_descriptor)
            if _topology_signature(root.lstat(), directory=True) != _topology_signature(
                os.fstat(root_descriptor), directory=True
            ):
                unavailable = True
                closure_stable = False
                members_closed = False
                issues.append(_issue("location", "root 路径不再指向本次读取持有的目录"))
        except (OSError, UnsafePathError):
            unavailable = True
            closure_stable = False
            members_closed = False
            issues.append(_issue("location", "FileAsset 目录无法完成同一 descriptor 的读取后稳定性复核"))
    finally:
        if directory_descriptor is not None:
            os.close(directory_descriptor)
        if root_descriptor is not None:
            os.close(root_descriptor)

    payload_matches: bool | None = None
    if fields is not None and size_read and digest_computed:
        declared_size = fields.get("size_bytes")
        declared_digest = fields.get("content_sha256")
        if (
            isinstance(declared_size, int)
            and not isinstance(declared_size, bool)
            and declared_size >= 0
            and isinstance(declared_digest, str)
            and len(declared_digest) == 64
            and all(character in "0123456789abcdef" for character in declared_digest)
        ):
            size_matches = observed_size == declared_size
            digest_matches = observed_digest == declared_digest
            payload_matches = size_matches and digest_matches
            if not size_matches:
                issues.append(_issue("integrity", "payload 实际字节数与 manifest 不一致", "size_bytes"))
            if not digest_matches:
                issues.append(_issue("integrity", "payload 实际 SHA-256 与 manifest 不一致", "content_sha256"))

    coverage = _coverage(
        manifest=manifest_read,
        members=members_closed,
        size=size_read,
        digest=digest_computed,
    )
    if unavailable:
        status: FileAssetStatus = "unavailable"
    elif issues:
        status = "invalid"
    else:
        status = "mechanically_valid"
    current_bytes_confirmed = status == "mechanically_valid" and members_closed and payload_matches is True
    default_candidate = current_bytes_confirmed and fields is not None and fields.get("status") == "active"
    content_fingerprint: str | None = None
    if not unavailable and manifest_bytes is not None and observed_size is not None and observed_digest is not None:
        fingerprint = hashlib.sha256()
        fingerprint.update(b"ldvh:file-asset:v1\0")
        fingerprint.update(len(manifest_bytes).to_bytes(8, "big"))
        fingerprint.update(manifest_bytes)
        fingerprint.update(observed_size.to_bytes(8, "big"))
        fingerprint.update(bytes.fromhex(observed_digest))
        content_fingerprint = fingerprint.hexdigest()
    return FileAssetRead(
        directory_text,
        status,
        coverage,
        fields,
        tuple(issues),
        observed_size,
        observed_digest,
        payload_matches,
        current_bytes_confirmed,
        default_candidate,
        payload_path,
        content_fingerprint,
        manifest_text,
        len(manifest_bytes) if manifest_bytes is not None else None,
    )


__all__ = [
    "DEFAULT_MANIFEST_BUDGET",
    "DEFAULT_PAYLOAD_BUDGET",
    "FileAssetRead",
    "FileAssetSnapshotValidation",
    "read_file_asset",
    "validate_file_asset_snapshot",
]
