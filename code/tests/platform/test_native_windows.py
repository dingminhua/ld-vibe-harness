from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from ldvh.filesystem import (
    UnsafePathError,
    UnstableIdentityError,
    atomic_create_relative,
    atomic_replace_relative_if_equal,
    exclusive_file_lock,
    is_reparse_point,
    safe_read_relative,
)

pytestmark = [
    pytest.mark.native_windows,
    pytest.mark.skipif(sys.platform != "win32" or os.name != "nt", reason="requires native Windows"),
]

OPERATIONS = {
    "create-fact-object",
    "find-fact-object-candidates",
    "precheck-git-commit",
    "prepare-fact-object-draft",
    "read-action-template-candidates",
    "read-action-template-content",
    "read-fact-objects",
    "read-specification-candidates",
    "read-specification-content",
    "resolve-governance-scope",
    "update-fact-object",
}

LOCK_WORKER = r"""
import sys
import time
from pathlib import Path
from ldvh.filesystem import exclusive_file_lock

with exclusive_file_lock(Path(sys.argv[1])):
    Path(sys.argv[3]).write_text("locked\n", encoding="ascii")
    time.sleep(float(sys.argv[2]))
"""


def _run(argv: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, check=False, timeout=30)


def _git(root: Path, *arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    return _run(["git", "-C", str(root), *arguments], cwd=root, env=env)


def _volume_filesystem(path: Path) -> str:
    volume_path = ctypes.create_unicode_buffer(261)
    assert ctypes.windll.kernel32.GetVolumePathNameW(str(path), volume_path, len(volume_path))
    filesystem = ctypes.create_unicode_buffer(261)
    assert ctypes.windll.kernel32.GetVolumeInformationW(
        volume_path.value,
        None,
        0,
        None,
        None,
        None,
        filesystem,
        len(filesystem),
    )
    return filesystem.value


def _cli(
    helper: Path, cwd: Path, command: str, operation: str | None, request: dict[str, Any] | None
) -> tuple[int, dict[str, Any]]:
    argv = [str(helper), command]
    if operation:
        argv.append(operation)
    payload = b"" if request is None else json.dumps(request, ensure_ascii=False).encode("utf-8")
    completed = subprocess.run(argv, cwd=cwd, input=payload, capture_output=True, check=False, timeout=30)
    assert completed.stderr == b""
    return completed.returncode, json.loads(completed.stdout.decode("utf-8"))


def test_native_environment_is_windows_ntfs_with_installed_console_script(tmp_path: Path) -> None:
    assert sys.platform == "win32"
    assert os.name == "nt"
    assert _volume_filesystem(tmp_path).upper() == "NTFS"
    assert _volume_filesystem(Path(os.environ["TEMP"])).upper() == "NTFS"
    assert shutil.which("git")
    helper = Path(sys.executable).with_name("ldvh.exe")
    assert helper.is_file()

    exit_code, response = _cli(helper, tmp_path, "capabilities", None, None)

    assert exit_code == 0
    assert response["outcome"] == "ok"
    assert {item["operation_key"] for item in response["result"]["operations"]} == OPERATIONS


def test_native_junction_is_rejected_before_read(tmp_path: Path) -> None:
    root = tmp_path / "root with spaces"
    outside = tmp_path / "外部 target"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("outside\n", encoding="utf-8")
    junction = root / "junction"
    created = _run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(outside)], cwd=tmp_path)
    assert created.returncode == 0, created.stderr.decode(errors="replace")
    assert is_reparse_point(junction.lstat())
    with pytest.raises(UnsafePathError):
        safe_read_relative(root, "junction/secret.txt")


def test_native_symlink_is_rejected_when_privilege_is_available(tmp_path: Path) -> None:
    root = tmp_path / "root with spaces"
    outside = tmp_path / "外部 target"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("outside\n", encoding="utf-8")
    symlink = root / "symlink"
    try:
        symlink.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink privilege is unavailable: {error}")
    assert is_reparse_point(symlink.lstat())
    with pytest.raises(UnsafePathError):
        safe_read_relative(root, "symlink/secret.txt")


def test_native_msvcrt_lock_serializes_and_recovers_after_kill(tmp_path: Path) -> None:
    lock_path = tmp_path / "锁 state" / "allocator.lock"
    ready_path = tmp_path / "holder.ready"
    holding = subprocess.Popen(
        [sys.executable, "-c", LOCK_WORKER, str(lock_path), "60", str(ready_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.monotonic() + 10
    while not ready_path.is_file() and holding.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    try:
        assert ready_path.read_text(encoding="ascii") == "locked\n"
    finally:
        holding.kill()
        holding.wait(timeout=10)

    probe_ready = tmp_path / "probe.ready"
    probe = _run([sys.executable, "-c", LOCK_WORKER, str(lock_path), "0", str(probe_ready)], cwd=tmp_path)

    assert probe.returncode == 0, probe.stderr.decode(errors="replace")
    assert probe_ready.read_text(encoding="ascii") == "locked\n"
    with exclusive_file_lock(lock_path):
        pass


def test_native_file_only_create_and_replace_report_exact_boundaries(tmp_path: Path) -> None:
    root = tmp_path / "原子 root with spaces"
    root.mkdir()
    relative = Path("facts/sparks/spark-0001.yaml")

    created = atomic_create_relative(root, relative, b"first\n", allow_file_only=True)
    conflict = atomic_create_relative(root, relative, b"second\n", allow_file_only=True)

    assert (created.outcome, created.namespace_state, created.durability, created.cleanup) == (
        "created",
        "committed",
        "file_only",
        "clean",
    )
    assert conflict.outcome == "conflict"
    assert (root / relative).read_bytes() == b"first\n"

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    kernel32.CreateFileW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.CreateFileW(
        str(root / relative),
        0x80000000,
        0x00000001,
        None,
        3,
        0x00000080,
        None,
    )
    assert handle not in {None, ctypes.c_void_p(-1).value}
    try:
        blocked = atomic_replace_relative_if_equal(
            root,
            relative,
            b"first\n",
            b"replacement\n",
            allow_file_only=True,
        )
    finally:
        assert kernel32.CloseHandle(handle)
    assert blocked.outcome == "unavailable"
    assert blocked.namespace_state == "not_committed"
    assert (root / relative).read_bytes() == b"first\n"
    assert not tuple((root / relative.parent).glob(".ldvh-update-*.tmp"))

    replaced = atomic_replace_relative_if_equal(
        root,
        relative,
        b"first\n",
        b"replacement\n",
        allow_file_only=True,
    )
    assert (replaced.outcome, replaced.namespace_state, replaced.durability, replaced.cleanup) == (
        "replaced",
        "committed",
        "file_only",
        "clean",
    )


def test_native_git_linked_worktree_and_temporary_index_are_isolated(tmp_path: Path) -> None:
    repository = tmp_path / "Git 根 with spaces"
    linked = tmp_path / "linked 工作树"
    repository.mkdir()
    assert _git(repository, "init", "-q").returncode == 0
    assert _git(repository, "config", "user.name", "LDVH Native Test").returncode == 0
    assert _git(repository, "config", "user.email", "ldvh@example.invalid").returncode == 0
    (repository / "tracked.txt").write_text("base\n", encoding="utf-8")
    assert _git(repository, "add", "tracked.txt").returncode == 0
    assert _git(repository, "commit", "-qm", "initial").returncode == 0
    added = _git(repository, "worktree", "add", "-qb", "native-linked", str(linked))
    assert added.returncode == 0, added.stderr.decode(errors="replace")

    common_main = _git(repository, "rev-parse", "--git-common-dir").stdout.decode("utf-8").strip()
    common_linked = _git(linked, "rev-parse", "--git-common-dir").stdout.decode("utf-8").strip()
    assert Path(repository, common_main).resolve() == Path(linked, common_linked).resolve()

    temporary_index = tmp_path / "临时 index"
    environment = os.environ.copy()
    environment["GIT_INDEX_FILE"] = str(temporary_index)
    assert _git(linked, "read-tree", "HEAD", env=environment).returncode == 0
    (linked / "tracked.txt").write_text("changed\n", encoding="utf-8")
    assert _git(linked, "add", "tracked.txt", env=environment).returncode == 0
    assert _git(linked, "diff", "--cached", "--quiet").returncode == 0
    assert _git(linked, "diff", "--cached", "--quiet", env=environment).returncode == 1


def test_native_drive_letter_case_alias_reads_the_same_file(tmp_path: Path) -> None:
    root = tmp_path / "Drive Case 根"
    root.mkdir()
    (root / "observed.txt").write_text("same identity\n", encoding="utf-8")
    value = str(root)
    assert len(value) >= 3 and value[1:3] == ":\\"
    alias = Path(value[0].swapcase() + value[1:])

    assert safe_read_relative(alias, "observed.txt") == b"same identity\n"


def test_native_unc_read_is_rejected_before_filesystem_access() -> None:
    with pytest.raises(UnstableIdentityError, match="UNC"):
        safe_read_relative(Path(r"\\nonexistent.invalid\ldvh-native-probe"), "observed.txt")
