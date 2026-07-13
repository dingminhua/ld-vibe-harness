"""Safely read one exact fact-object path from the current Git working tree."""

from __future__ import annotations

import errno
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import FactTypeLayout
from ldvh.facts.models import FactIssue
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import validate_fact_object
from ldvh.governance.git import isolated_git_environment

CheckStatus = Literal["mechanically_valid", "invalid", "not_found", "unavailable"]
MAX_FACT_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class FactReadResult:
    canonical_path: str
    carrier: str
    check_status: CheckStatus
    fields: dict[str, Any] | None
    body: str | None
    issues: tuple[FactIssue, ...]


def _safe_regular_file(root: Path, relative_path: str) -> tuple[Path, FactIssue | None, CheckStatus | None]:
    candidate = root / relative_path
    current = root
    for segment in Path(relative_path).parts:
        current = current / segment
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return candidate, FactIssue("location", "事实对象预期位置不存在"), "not_found"
        except OSError:
            return candidate, FactIssue("location", "无法安全读取事实对象路径"), "unavailable"
        if stat.S_ISLNK(mode):
            return candidate, FactIssue("location", "事实对象 canonical path 不得包含符号链接"), "invalid"
    try:
        mode = candidate.stat().st_mode
    except OSError:
        return candidate, FactIssue("location", "无法读取事实对象文件状态"), "unavailable"
    if not stat.S_ISREG(mode):
        return candidate, FactIssue("location", "事实对象 canonical path 必须是普通文件"), "invalid"
    return candidate, None, None


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ("git", "-C", os.fspath(root), *arguments),
            check=False,
            capture_output=True,
            env=isolated_git_environment(),
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_identity(root: Path) -> tuple[Path, Path] | None:
    result = _git(root, "rev-parse", "--path-format=absolute", "--show-toplevel", "--git-common-dir")
    if result is None or result.returncode != 0:
        return None
    lines = result.stdout.splitlines()
    if len(lines) != 2:
        return None
    return Path(lines[0]).resolve(), Path(lines[1]).resolve()


def _identity_issue(
    root: Path,
    expected_common_dir: Path | None,
) -> tuple[FactIssue | None, CheckStatus | None]:
    identity = _git_identity(root)
    if identity is None:
        return FactIssue("git-traceability", "无法确认事实对象所在 Git Working Tree 身份"), "unavailable"
    worktree_root, common_dir = identity
    if worktree_root != root.resolve() or (
        expected_common_dir is not None and common_dir != expected_common_dir.resolve()
    ):
        return FactIssue("git-traceability", "事实对象读取边界与已解析 Git 身份不一致"), "unavailable"
    return None, None


def _traceability(root: Path, relative_path: str) -> tuple[FactIssue | None, CheckStatus | None]:
    tracked = _git(root, "ls-files", "--error-unmatch", "--", relative_path)
    if tracked is None:
        return FactIssue("git-traceability", "无法执行必需的 Git 可追踪性检查"), "unavailable"
    if tracked.returncode == 0:
        return None, None
    ignored = _git(root, "check-ignore", "--quiet", "--no-index", "--", relative_path)
    if ignored is None:
        return FactIssue("git-traceability", "无法执行必需的 Git ignore 检查"), "unavailable"
    if ignored.returncode == 0:
        return FactIssue("git-traceability", "untracked 且 ignored 的文件不能成为稳定事实"), "invalid"
    if ignored.returncode == 1:
        return None, None
    return FactIssue("git-traceability", "Git ignore 检查没有形成可信结果"), "unavailable"


def _read_utf8_without_symlinks(
    root: Path,
    relative_path: str,
) -> tuple[str | None, FactIssue | None, CheckStatus | None]:
    directory_fd: int | None = None
    file_fd: int | None = None
    try:
        directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        parts = Path(relative_path).parts
        for segment in parts[:-1]:
            next_fd = os.open(
                segment,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            return None, FactIssue("location", "事实对象 canonical path 必须是普通文件"), "invalid"
        if before.st_size > MAX_FACT_BYTES:
            return None, FactIssue("parse", "事实对象载体超过 4 MiB 读取预算"), "unavailable"
        chunks: list[bytes] = []
        observed = 0
        while observed <= MAX_FACT_BYTES:
            chunk = os.read(file_fd, min(64 * 1024, MAX_FACT_BYTES + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
        if observed > MAX_FACT_BYTES:
            return None, FactIssue("parse", "事实对象载体超过 4 MiB 读取预算"), "unavailable"
        after = os.fstat(file_fd)
        fingerprint_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        fingerprint_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        if fingerprint_before != fingerprint_after:
            return None, FactIssue("location", "事实对象在安全读取期间发生变化"), "unavailable"
        return b"".join(chunks).decode("utf-8"), None, None
    except UnicodeDecodeError:
        return None, FactIssue("parse", "事实对象无法作为 UTF-8 普通文件读取"), "invalid"
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.ENOTDIR}:
            return None, FactIssue("location", "事实对象 canonical path 不得包含符号链接"), "invalid"
        return None, FactIssue("location", "事实对象文件在安全读取时发生变化或不可访问"), "unavailable"
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)


def read_fact_object(
    root: Path,
    layout: FactTypeLayout,
    schema: FactSchema,
    object_id: str,
    *,
    expected_common_dir: Path | None = None,
) -> FactReadResult:
    """Read and mechanically validate one source-selected fact object."""

    relative_path = layout.canonical_path(object_id)
    identity_issue, identity_status = _identity_issue(root, expected_common_dir)
    if identity_issue is not None:
        return FactReadResult(
            relative_path,
            layout.carrier,
            identity_status or "unavailable",
            None,
            None,
            (identity_issue,),
        )
    _, location_issue, location_status = _safe_regular_file(root, relative_path)
    if location_issue is not None:
        return FactReadResult(
            relative_path, layout.carrier, location_status or "invalid", None, None, (location_issue,)
        )
    trace_issue, trace_status = _traceability(root, relative_path)
    if trace_issue is not None:
        return FactReadResult(relative_path, layout.carrier, trace_status or "invalid", None, None, (trace_issue,))
    text, read_issue, read_status = _read_utf8_without_symlinks(root, relative_path)
    if read_issue is not None or text is None:
        issue = read_issue or FactIssue("location", "事实对象文件无法安全读取")
        return FactReadResult(relative_path, layout.carrier, read_status or "unavailable", None, None, (issue,))
    identity_issue, identity_status = _identity_issue(root, expected_common_dir)
    if identity_issue is not None:
        return FactReadResult(
            relative_path,
            layout.carrier,
            identity_status or "unavailable",
            None,
            None,
            (identity_issue,),
        )

    parsed = parse_study_markdown(text) if layout.carrier == "markdown" else parse_yaml_object(text)
    if parsed.fields is None or parsed.issues:
        return FactReadResult(relative_path, layout.carrier, "invalid", parsed.fields, parsed.body, parsed.issues)

    issues = list(validate_fact_object(layout.fact_type_key, parsed.fields, schema))
    if parsed.fields.get("object_id") != object_id:
        issues.append(FactIssue("identity", "object_id 与请求引用及文件名不一致", "object_id"))
    status: CheckStatus = "invalid" if issues else "mechanically_valid"
    return FactReadResult(relative_path, layout.carrier, status, parsed.fields, parsed.body, tuple(issues))


__all__ = ["CheckStatus", "FactReadResult", "read_fact_object"]
