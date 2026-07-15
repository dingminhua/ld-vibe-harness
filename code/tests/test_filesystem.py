from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ldvh.filesystem import (
    UnsafePathError,
    UnstableIdentityError,
    _exclusive_file_lock,
    is_link_or_reparse,
    is_reparse_point,
    safe_read_relative,
    walk_regular_files,
)


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


def _stat_view(observation: os.stat_result, **overrides: int) -> SimpleNamespace:
    values = {
        field: getattr(observation, field)
        for field in ("st_mode", "st_dev", "st_ino", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
    }
    values["st_file_attributes"] = getattr(observation, "st_file_attributes", 0)
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.parametrize("reparse_part", ("root", "parent", "file"))
def test_portable_reader_rejects_reparse_at_every_path_level(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reparse_part: str,
) -> None:
    root = tmp_path / "root"
    parent = root / "nested"
    parent.mkdir(parents=True)
    file = parent / "fact.yaml"
    file.write_text("object_id: spark-0001\n", encoding="utf-8")
    targets = {"root": root, "parent": parent, "file": file}
    target = targets[reparse_part]
    real_lstat = Path.lstat

    def reparse_lstat(path: Path) -> os.stat_result | SimpleNamespace:
        observed = real_lstat(path)
        return _stat_view(observed, st_file_attributes=0x400) if path == target else observed

    monkeypatch.setattr(Path, "lstat", reparse_lstat)

    with pytest.raises(UnsafePathError, match="reparse"):
        safe_read_relative(root, "nested/fact.yaml", platform_name="nt")


def test_portable_reader_fails_closed_without_stable_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    file = root / "fact.yaml"
    file.write_text("object_id: spark-0001\n", encoding="utf-8")
    real_lstat = Path.lstat

    def unstable_lstat(path: Path) -> os.stat_result | SimpleNamespace:
        observed = real_lstat(path)
        return _stat_view(observed, st_ino=0) if path == file else observed

    monkeypatch.setattr(Path, "lstat", unstable_lstat)

    with pytest.raises(UnstableIdentityError, match="st_ino"):
        safe_read_relative(root, "fact.yaml", platform_name="nt")


def test_reader_rejects_a_linked_root_on_posix_and_portable_paths(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    real_root.mkdir()
    (real_root / "fact.yaml").write_text("object_id: spark-0001\n", encoding="utf-8")
    linked_root = tmp_path / "linked"
    try:
        linked_root.symlink_to(real_root, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(OSError):
        safe_read_relative(linked_root, "fact.yaml")
    with pytest.raises(UnsafePathError, match="reparse"):
        safe_read_relative(linked_root, "fact.yaml", platform_name="nt")


def test_windows_candidate_reader_rejects_unc_without_native_evidence() -> None:
    with pytest.raises(UnstableIdentityError, match="UNC"):
        safe_read_relative(Path(r"\\server\share"), "fact.yaml", platform_name="nt")


def test_safe_walk_rejects_link_before_descending(tmp_path: Path) -> None:
    root = tmp_path / "snapshot"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("outside", encoding="utf-8")
    link = root / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(UnsafePathError, match="symbolic link or reparse"):
        walk_regular_files(root)


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
