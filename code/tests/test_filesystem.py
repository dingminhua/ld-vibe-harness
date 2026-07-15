from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ldvh.filesystem import _exclusive_file_lock, is_link_or_reparse, is_reparse_point


class _RecordingLockApi:
    def __init__(self, *, fail_lock: bool = False) -> None:
        self.fail_lock = fail_lock
        self.locked: list[int] = []
        self.unlocked: list[int] = []

    def lock(self, descriptor: int) -> None:
        self.locked.append(descriptor)
        if self.fail_lock:
            raise OSError("lock failed")

    def unlock(self, descriptor: int) -> None:
        self.unlocked.append(descriptor)


def test_exclusive_file_lock_unlocks_and_closes_after_body_failure(tmp_path: Path) -> None:
    api = _RecordingLockApi()
    descriptor = -1

    with pytest.raises(RuntimeError, match="body failed"):
        with _exclusive_file_lock(tmp_path / "state" / "allocator.lock", api):
            descriptor = api.locked[0]
            raise RuntimeError("body failed")

    assert api.unlocked == [descriptor]
    with pytest.raises(OSError):
        os.fstat(descriptor)


def test_exclusive_file_lock_closes_without_unlock_after_acquisition_failure(tmp_path: Path) -> None:
    api = _RecordingLockApi(fail_lock=True)

    with pytest.raises(OSError, match="lock failed"):
        with _exclusive_file_lock(tmp_path / "allocator.lock", api):
            pytest.fail("lock body must not run")

    descriptor = api.locked[0]
    assert api.unlocked == []
    with pytest.raises(OSError):
        os.fstat(descriptor)


def test_link_or_reparse_detection_covers_both_platform_signals() -> None:
    reparse = SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
    symlink = SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
    regular = SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0)

    assert is_reparse_point(reparse) is True
    assert is_link_or_reparse(reparse) is True
    assert is_link_or_reparse(symlink) is True
    assert is_link_or_reparse(regular) is False


def test_cli_import_does_not_require_fcntl() -> None:
    project_root = Path(__file__).resolve().parents[2]
    script = """
import builtins

real_import = builtins.__import__

def guarded_import(name, *args, **kwargs):
    if name == "fcntl":
        raise ImportError("fcntl is unavailable")
    return real_import(name, *args, **kwargs)

builtins.__import__ = guarded_import
import ldvh.cli
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "code")
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
