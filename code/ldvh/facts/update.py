"""Atomic conditional replacement for one existing fact carrier."""

from __future__ import annotations

import errno
import os
import secrets
import stat
from pathlib import Path
from typing import Literal

from ldvh.facts.contracts import FactTypeLayout

ReplaceOutcome = Literal["replaced", "conflict", "unavailable"]


def _open_existing_directory(root: Path, layout: FactTypeLayout) -> int:
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for segment in Path(layout.directory).parts:
            next_descriptor = os.open(
                segment,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _read_regular(directory_fd: int, target_name: str, maximum_bytes: int) -> tuple[bytes, int] | None:
    descriptor = os.open(target_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            return None
        chunks: list[bytes] = []
        observed = 0
        while observed <= maximum_bytes:
            chunk = os.read(descriptor, min(64 * 1024, maximum_bytes + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
        after = os.fstat(descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if before_identity != after_identity:
            return None
        return b"".join(chunks), stat.S_IMODE(before.st_mode)
    finally:
        os.close(descriptor)


def atomic_replace_text_if_unchanged(
    root: Path,
    layout: FactTypeLayout,
    object_id: str,
    expected_text: str,
    replacement_text: str,
) -> ReplaceOutcome:
    """Replace one regular file only while it still equals the expected bytes."""

    expected = expected_text.encode("utf-8")
    replacement = replacement_text.encode("utf-8")
    directory_fd: int | None = None
    temporary_fd: int | None = None
    temporary_name = f".ldvh-update-{secrets.token_hex(12)}.tmp"
    target_name = f"{object_id}{layout.suffix}"
    try:
        directory_fd = _open_existing_directory(root, layout)
        observed = _read_regular(directory_fd, target_name, len(expected))
        if observed is None:
            return "unavailable"
        current, mode = observed
        if current != expected:
            return "conflict"

        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            mode,
            dir_fd=directory_fd,
        )
        offset = 0
        while offset < len(replacement):
            offset += os.write(temporary_fd, replacement[offset:])
        os.fsync(temporary_fd)
        os.close(temporary_fd)
        temporary_fd = None

        observed_again = _read_regular(directory_fd, target_name, len(expected))
        if observed_again is None:
            return "unavailable"
        if observed_again[0] != expected:
            return "conflict"
        os.replace(
            temporary_name,
            target_name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
        return "replaced"
    except OSError as error:
        if error.errno in {errno.ENOENT, errno.ELOOP, errno.ENOTDIR}:
            return "conflict"
        return "unavailable"
    finally:
        if temporary_fd is not None:
            os.close(temporary_fd)
        if directory_fd is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError:
                pass
            os.close(directory_fd)


__all__ = ["ReplaceOutcome", "atomic_replace_text_if_unchanged"]
