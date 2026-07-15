"""Platform-selected filesystem primitives shared by LDVH production modules."""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol


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
