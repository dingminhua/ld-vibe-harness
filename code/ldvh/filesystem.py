"""Platform-selected filesystem primitives shared by LDVH production modules."""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol


class UnsafePathError(OSError):
    """A path has a forbidden type or link/reparse topology."""


class PathChangedError(OSError):
    """A path or open handle changed during one observation."""


class UnstableIdentityError(OSError):
    """The platform did not expose a stable filesystem identity."""


class ReadBudgetExceeded(OSError):
    """A regular file exceeded the caller's bounded-read budget."""


class _LockingApi(Protocol):
    def lock(self, descriptor: int) -> None: ...

    def unlock(self, descriptor: int) -> None: ...


class _PosixLockingApi:
    def __init__(self) -> None:
        import fcntl

        self._fcntl = fcntl

    def lock(self, descriptor: int) -> None:
        self._fcntl.flock(descriptor, self._fcntl.LOCK_EX)

    def unlock(self, descriptor: int) -> None:
        self._fcntl.flock(descriptor, self._fcntl.LOCK_UN)


class _WindowsLockingApi:
    def __init__(self) -> None:
        import msvcrt

        self._msvcrt = msvcrt

    def lock(self, descriptor: int) -> None:
        os.lseek(descriptor, 0, os.SEEK_SET)
        self._msvcrt.locking(descriptor, self._msvcrt.LK_LOCK, 1)

    def unlock(self, descriptor: int) -> None:
        os.lseek(descriptor, 0, os.SEEK_SET)
        self._msvcrt.locking(descriptor, self._msvcrt.LK_UNLCK, 1)


def _locking_api(platform_name: str) -> _LockingApi:
    if platform_name == "posix":
        return _PosixLockingApi()
    if platform_name == "nt":
        return _WindowsLockingApi()
    raise OSError(f"unsupported operating system: {platform_name}")


@contextmanager
def _exclusive_file_lock(path: Path, api: _LockingApi) -> Iterator[None]:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    locked = False
    try:
        api.lock(descriptor)
        locked = True
        yield
    finally:
        if locked:
            try:
                api.unlock(descriptor)
            finally:
                os.close(descriptor)
        else:
            os.close(descriptor)


@contextmanager
def exclusive_file_lock(path: Path) -> Iterator[None]:
    """Hold the platform-native exclusive lock associated with ``path``."""

    with _exclusive_file_lock(path, _locking_api(os.name)):
        yield


def is_reparse_point(observation: os.stat_result) -> bool:
    """Return whether a stat observation carries the Windows reparse attribute."""

    attributes = getattr(observation, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def is_link_or_reparse(observation: os.stat_result) -> bool:
    """Return whether an observation is a symbolic link or Windows reparse point."""

    return stat.S_ISLNK(observation.st_mode) or is_reparse_point(observation)


def _normal_relative_path(relative_path: str | Path) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise UnsafePathError("path must be normalized and relative")
    return relative


def _windows_unc_path(path: Path) -> bool:
    value = os.fspath(path)
    return value.startswith(("\\\\", "//"))


def _portable_signature(observation: os.stat_result) -> tuple[int, ...]:
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


def _observe_relative_path(
    root: Path,
    relative_path: Path,
    *,
    final_type: str,
) -> tuple[tuple[Path, tuple[int, ...]], ...]:
    observations: list[tuple[Path, tuple[int, ...]]] = []
    paths = [root]
    current = root
    for component in relative_path.parts:
        current = current / component
        paths.append(current)
    for index, path in enumerate(paths):
        observed = path.lstat()
        if is_link_or_reparse(observed):
            raise UnsafePathError("path contains a symbolic link or reparse point")
        is_final = index == len(paths) - 1
        if not is_final and not stat.S_ISDIR(observed.st_mode):
            raise UnsafePathError("path component is not a directory")
        if is_final and final_type == "regular" and not stat.S_ISREG(observed.st_mode):
            raise UnsafePathError("path is not a regular file")
        if is_final and final_type == "directory" and not stat.S_ISDIR(observed.st_mode):
            raise UnsafePathError("path is not a directory")
        observations.append((path, _portable_signature(observed)))
    return tuple(observations)


def validate_relative_regular_file(root: Path, relative_path: str | Path) -> Path:
    """Validate a relative regular-file topology without following link/reparse paths."""

    relative = _normal_relative_path(relative_path)
    _observe_relative_path(root, relative, final_type="regular")
    return root / relative


def safe_list_directory(root: Path, relative_path: str | Path) -> tuple[Path, ...]:
    """List one relative directory only if its complete topology stays stable."""

    relative = _normal_relative_path(relative_path)
    before = _observe_relative_path(root, relative, final_type="directory")
    entries = tuple((root / relative).iterdir())
    after = _observe_relative_path(root, relative, final_type="directory")
    if before != after:
        raise PathChangedError("directory topology changed while it was listed")
    return entries


def _read_descriptor(descriptor: int, *, max_bytes: int | None) -> bytes:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or is_reparse_point(before):
        raise UnsafePathError("opened handle is not a regular non-reparse file")
    if max_bytes is not None and before.st_size > max_bytes:
        raise ReadBudgetExceeded("file exceeds the bounded-read budget")
    chunks: list[bytes] = []
    observed = 0
    while max_bytes is None or observed <= max_bytes:
        budget = 64 * 1024 if max_bytes is None else min(64 * 1024, max_bytes + 1 - observed)
        chunk = os.read(descriptor, budget)
        if not chunk:
            break
        chunks.append(chunk)
        observed += len(chunk)
    if max_bytes is not None and observed > max_bytes:
        raise ReadBudgetExceeded("file exceeds the bounded-read budget")
    after = os.fstat(descriptor)
    if _portable_signature(before) != _portable_signature(after):
        raise PathChangedError("opened file changed while it was read")
    return b"".join(chunks)


def _read_bytes_posix(
    root: Path,
    relative_path: Path,
    *,
    no_follow: int,
    directory_flag: int,
    max_bytes: int | None,
) -> bytes:
    directory_fd = os.open(root, os.O_RDONLY | directory_flag | no_follow)
    file_fd: int | None = None
    try:
        for component in relative_path.parts[:-1]:
            next_fd = os.open(component, os.O_RDONLY | directory_flag | no_follow, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(relative_path.parts[-1], os.O_RDONLY | no_follow, dir_fd=directory_fd)
        return _read_descriptor(file_fd, max_bytes=max_bytes)
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(directory_fd)


def _read_bytes_portable(
    root: Path,
    relative_path: Path,
    *,
    max_bytes: int | None,
) -> bytes:
    absolute_path = root / relative_path
    before_components = _observe_relative_path(root, relative_path, final_type="regular")
    with absolute_path.open("rb", buffering=0) as source:
        before_handle = os.fstat(source.fileno())
        if before_components[-1][1] != _portable_signature(before_handle):
            raise PathChangedError("opened file does not match the observed path")
        raw_bytes = _read_descriptor(source.fileno(), max_bytes=max_bytes)
        after_handle = os.fstat(source.fileno())
    after_components = _observe_relative_path(root, relative_path, final_type="regular")
    if _portable_signature(before_handle) != _portable_signature(after_handle):
        raise PathChangedError("opened file changed while it was read")
    if before_components != after_components:
        raise PathChangedError("path topology changed while the file was read")
    if after_components[-1][1] != _portable_signature(after_handle):
        raise PathChangedError("opened file no longer matches the observed path")
    return raw_bytes


def safe_read_relative(
    root: Path,
    relative_path: str | Path,
    *,
    max_bytes: int | None = None,
    platform_name: str | None = None,
) -> bytes:
    """Read one relative regular file through the strongest available platform path."""

    relative = _normal_relative_path(relative_path)
    selected_platform = os.name if platform_name is None else platform_name
    if selected_platform == "nt" and _windows_unc_path(root):
        raise UnstableIdentityError("UNC paths are unsupported without native verification")
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if selected_platform != "nt" and no_follow is not None and directory_flag is not None:
        return _read_bytes_posix(
            root,
            relative,
            no_follow=no_follow,
            directory_flag=directory_flag,
            max_bytes=max_bytes,
        )
    return _read_bytes_portable(root, relative, max_bytes=max_bytes)


def walk_regular_files(root: Path) -> tuple[Path, ...]:
    """Walk a directory tree without descending through link/reparse entries."""

    root_observation = root.lstat()
    if is_link_or_reparse(root_observation) or not stat.S_ISDIR(root_observation.st_mode):
        raise UnsafePathError("walk root must be a non-reparse directory")
    root_signature = _portable_signature(root_observation)
    files: list[Path] = []
    pending = [(root, root_signature)]
    while pending:
        directory, expected_signature = pending.pop()
        before = directory.lstat()
        if is_link_or_reparse(before) or not stat.S_ISDIR(before.st_mode):
            raise UnsafePathError("walk path contains an unsafe directory")
        before_signature = _portable_signature(before)
        if before_signature != expected_signature:
            raise PathChangedError("directory changed before it was enumerated")
        with os.scandir(directory) as entries:
            current_entries = tuple(entries)
        after = directory.lstat()
        if before_signature != _portable_signature(after):
            raise PathChangedError("directory changed while it was enumerated")
        for entry in current_entries:
            observation = entry.stat(follow_symlinks=False)
            if is_link_or_reparse(observation):
                raise UnsafePathError("walk path contains a symbolic link or reparse point")
            path = Path(entry.path)
            if stat.S_ISDIR(observation.st_mode):
                pending.append((path, _portable_signature(observation)))
            elif stat.S_ISREG(observation.st_mode):
                files.append(path)
            else:
                raise UnsafePathError("walk path contains an unsupported file type")
    if root_signature != _portable_signature(root.lstat()):
        raise PathChangedError("walk root changed while it was enumerated")
    return tuple(sorted(files, key=lambda path: path.relative_to(root).as_posix()))
