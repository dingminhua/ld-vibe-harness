from __future__ import annotations

import errno
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from ldvh import filesystem
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    CreationBoundary,
    FactCoordinationUnavailable,
    _allocator_paths,
    allocate_object_id_locked,
    allocation_lock,
    candidate_object_id,
    commit_object_id_locked,
    preview_object_id_locked,
)
from ldvh.filesystem import exclusive_relative_file_lock

CODE_ROOT = Path(__file__).resolve().parents[2]

_POSIX_ALLOCATOR_ONLY = pytest.mark.skipif(
    os.name == "nt",
    reason="native Windows counter persistence awaits the atomic filesystem backend",
)

_LOCK_WORKER = """
import os
import sys
import time
from pathlib import Path
from ldvh.filesystem import exclusive_file_lock

lock_path = Path(sys.argv[1])
result_path = Path(sys.argv[2])
mode = sys.argv[3]
hold_seconds = float(sys.argv[4])
with exclusive_file_lock(lock_path):
    started = time.monotonic_ns()
    if mode == "hold":
        print("locked", flush=True)
        time.sleep(hold_seconds)
    else:
        time.sleep(hold_seconds)
    ended = time.monotonic_ns()
    result_path.write_text(f"{started} {ended}\\n", encoding="ascii")
"""

_ALLOCATOR_WORKER = """
import sys
from pathlib import Path
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, allocate_object_id_locked, allocation_lock

boundary = CreationBoundary(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
layout = LAYOUTS[sys.argv[4]]
with allocation_lock(boundary, layout) as counter_path:
    object_id = allocate_object_id_locked(boundary, layout, counter_path)
if object_id is None:
    raise SystemExit(3)
print(object_id, flush=True)
"""


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(CODE_ROOT) if not existing else f"{CODE_ROOT}{os.pathsep}{existing}"
    return environment


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "project"
    root.mkdir()
    _git(root, "init", "-q")
    common = Path(_git(root, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = root / common
    return root, common.resolve()


def _allocator_process(worktree: Path, common_dir: Path, fact_type_key: str = "spark") -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            "-c",
            _ALLOCATOR_WORKER,
            "sample",
            str(worktree),
            str(common_dir),
            fact_type_key,
        ],
        cwd=worktree,
        env=_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _allocated_ids(processes: list[subprocess.Popen[str]]) -> list[str]:
    allocated: list[str] = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, stderr
        assert stderr == ""
        allocated.append(stdout.strip())
    return allocated


def test_file_lock_serializes_independent_processes(tmp_path: Path) -> None:
    lock_path = tmp_path / "allocator.lock"
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _LOCK_WORKER, str(lock_path), str(tmp_path / f"result-{index}"), "probe", "0.1"],
            env=_environment(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for index in range(4)
    ]
    for process in processes:
        _, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stderr
        assert stderr == ""

    intervals = sorted(
        tuple(map(int, (tmp_path / f"result-{index}").read_text(encoding="ascii").split())) for index in range(4)
    )
    assert all(next_started >= ended for (_, ended), (next_started, _) in zip(intervals, intervals[1:], strict=False))
    assert lock_path.is_file()


def test_file_lock_is_released_when_holding_process_is_killed(tmp_path: Path) -> None:
    lock_path = tmp_path / "allocator.lock"
    holding = subprocess.Popen(
        [sys.executable, "-c", _LOCK_WORKER, str(lock_path), str(tmp_path / "holding"), "hold", "60"],
        env=_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert holding.stdout is not None
    assert holding.stdout.readline().strip() == "locked"
    holding.kill()
    holding.wait(timeout=5)

    probe = subprocess.run(
        [sys.executable, "-c", _LOCK_WORKER, str(lock_path), str(tmp_path / "probe"), "probe", "0"],
        env=_environment(),
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert probe.returncode == 0
    assert probe.stderr == ""
    assert (tmp_path / "probe").is_file()


@_POSIX_ALLOCATOR_ONLY
def test_allocator_assigns_contiguous_ids_across_independent_processes(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)

    allocated = _allocated_ids([_allocator_process(project, common_dir) for _ in range(6)])

    assert sorted(allocated) == [f"spark-{index:04d}" for index in range(1, 7)]
    boundary = CreationBoundary("sample", project, common_dir)
    _, counter_path = _allocator_paths(boundary, LAYOUTS["spark"])
    assert counter_path.read_text(encoding="ascii") == "6\n"


@_POSIX_ALLOCATOR_ONLY
def test_main_and_linked_worktree_allocate_from_one_common_counter(tmp_path: Path) -> None:
    unicode_root = tmp_path / "allocator 根目录"
    unicode_root.mkdir()
    project, common_dir = _repository(unicode_root)
    marker = project / "tracked.txt"
    marker.write_text("tracked\n", encoding="utf-8")
    _git(project, "add", "tracked.txt")
    _git(project, "-c", "user.name=LDVH Test", "-c", "user.email=ldvh@example.invalid", "commit", "-qm", "initial")
    linked = tmp_path / "linked 工作树"
    _git(project, "worktree", "add", "-qb", "linked-allocator", str(linked))

    allocated = _allocated_ids(
        [
            _allocator_process(project, common_dir),
            _allocator_process(linked, common_dir),
        ]
    )

    assert sorted(allocated) == ["spark-0001", "spark-0002"]


@_POSIX_ALLOCATOR_ONLY
def test_corrupt_counter_fails_closed_without_leaving_the_lock_held(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    boundary = CreationBoundary("sample", project, common_dir)
    layout = LAYOUTS["spark"]
    lock_path, counter_path = _allocator_paths(boundary, layout)
    counter_path.parent.mkdir(parents=True)
    counter_path.write_text("corrupt\n", encoding="ascii")
    relative_counter = counter_path.relative_to(common_dir)

    with allocation_lock(boundary, layout) as locked_counter:
        assert locked_counter == relative_counter
        assert allocate_object_id_locked(boundary, layout, locked_counter) is None
    with allocation_lock(boundary, layout):
        pass

    assert lock_path.is_file()
    assert counter_path.read_text(encoding="ascii") == "corrupt\n"


@_POSIX_ALLOCATOR_ONLY
def test_allocator_preview_is_read_only_and_missing_counter_commit_is_no_overwrite(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    boundary = CreationBoundary("sample", project, common_dir)
    layout = LAYOUTS["spark"]
    _, counter = _allocator_paths(boundary, layout)

    with allocation_lock(boundary, layout) as counter_path:
        preview = preview_object_id_locked(boundary, layout, counter_path)
        assert preview is not None and preview.object_id == "spark-0001"
        assert not counter.exists()
        committed = commit_object_id_locked(boundary, layout, preview)

    assert committed.status == "committed"
    assert committed.object_id == "spark-0001"
    assert counter.read_bytes() == b"1\n"


@_POSIX_ALLOCATOR_ONLY
def test_allocator_commit_rejects_stale_preview_without_overwriting_counter(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    boundary = CreationBoundary("sample", project, common_dir)
    layout = LAYOUTS["spark"]
    _, counter = _allocator_paths(boundary, layout)

    with allocation_lock(boundary, layout) as counter_path:
        preview = preview_object_id_locked(boundary, layout, counter_path)
        assert preview is not None
        counter.parent.mkdir(parents=True, exist_ok=True)
        counter.write_bytes(b"7\n")
        committed = commit_object_id_locked(boundary, layout, preview)

    assert committed.status == "stale"
    assert committed.object_id is None
    assert counter.read_bytes() == b"7\n"


def test_excessive_numeric_counter_fails_closed_instead_of_raising(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    boundary = CreationBoundary("sample", project, common_dir)
    layout = LAYOUTS["spark"]
    _, counter = _allocator_paths(boundary, layout)
    counter.parent.mkdir(parents=True)
    counter.write_text("9" * 5000, encoding="ascii")

    assert candidate_object_id(boundary, layout) is None
    with allocation_lock(boundary, layout) as counter_path:
        assert preview_object_id_locked(boundary, layout, counter_path) is None


def test_allocator_lock_rejects_linked_state_directory(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    outside = tmp_path / "outside-state"
    outside.mkdir()
    try:
        (common_dir / "ldvh").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")
    boundary = CreationBoundary("sample", project, common_dir)

    with pytest.raises(OSError):
        with allocation_lock(boundary, LAYOUTS["spark"]):
            pytest.fail("unsafe allocator state must not be locked")

    assert tuple(outside.iterdir()) == ()


def test_allocator_lock_rejects_linked_final_lock_file(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    boundary = CreationBoundary("sample", project, common_dir)
    lock_path, _ = _allocator_paths(boundary, LAYOUTS["spark"])
    lock_path.parent.mkdir(parents=True)
    outside = tmp_path / "outside.lock"
    outside.write_bytes(b"outside")
    try:
        lock_path.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(OSError):
        with allocation_lock(boundary, LAYOUTS["spark"]):
            pytest.fail("unsafe lock file must not be opened")

    assert outside.read_bytes() == b"outside"


@pytest.mark.parametrize(
    ("error", "category"),
    [
        (PermissionError(), "permission_denied"),
        (OSError(errno.EROFS, "read-only filesystem"), "read_only_filesystem"),
    ],
)
def test_allocator_lock_classifies_only_entry_permission_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: OSError,
    category: str,
) -> None:
    project, common_dir = _repository(tmp_path)
    boundary = CreationBoundary("sample", project, common_dir)

    class FailingLock:
        def __enter__(self) -> None:
            raise error

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr("ldvh.facts.creation.exclusive_relative_file_lock", lambda *_args: FailingLock())

    with pytest.raises(FactCoordinationUnavailable) as observed:
        with allocation_lock(boundary, LAYOUTS["spark"]):
            pytest.fail("the lock body must not run")

    assert observed.value.system_error_category == category
    assert observed.value.stage == "common_dir_lock"


def test_allocator_lock_does_not_reclassify_permission_failure_inside_body(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    boundary = CreationBoundary("sample", project, common_dir)

    with pytest.raises(PermissionError):
        with allocation_lock(boundary, LAYOUTS["spark"]):
            raise PermissionError("target write failed after lock entry")


def test_relative_lock_closes_descriptor_when_fstat_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_open = os.open
    real_fstat = os.fstat
    lock_descriptor: int | None = None

    def recording_open(path: str | bytes | Path, *args: object, **kwargs: object) -> int:
        nonlocal lock_descriptor
        descriptor = real_open(path, *args, **kwargs)
        if os.fsdecode(path) == "sample.lock":
            lock_descriptor = descriptor
        return descriptor

    def fail_lock_fstat(descriptor: int) -> os.stat_result:
        if descriptor == lock_descriptor:
            raise OSError("simulated fstat failure")
        return real_fstat(descriptor)

    monkeypatch.setattr(filesystem.os, "open", recording_open)
    monkeypatch.setattr(filesystem.os, "fstat", fail_lock_fstat)

    with pytest.raises(OSError, match="simulated fstat failure"):
        with exclusive_relative_file_lock(tmp_path, "ldvh/locks/sample.lock"):
            pytest.fail("lock must not be acquired")

    assert lock_descriptor is not None
    with pytest.raises(OSError):
        real_fstat(lock_descriptor)


def test_relative_lock_builds_api_before_opening_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_api(platform_name: str) -> filesystem._LockingApi:
        raise OSError(f"{platform_name} locking unavailable")

    monkeypatch.setattr(filesystem, "_locking_api", fail_api)
    monkeypatch.setattr(
        filesystem.os,
        "open",
        lambda *args, **kwargs: pytest.fail("lock descriptor must not be opened before API construction"),
    )

    with pytest.raises(OSError, match="locking unavailable"):
        with exclusive_relative_file_lock(tmp_path, "ldvh/locks/sample.lock"):
            pytest.fail("lock must not be acquired")

    assert not (tmp_path / "ldvh").exists()


def test_relative_lock_retries_one_transient_create_enoent_with_identical_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_open = os.open
    attempts: list[tuple[int, int | None]] = []

    def transient_open(path: str | bytes | Path, flags: int, *args: object, **kwargs: object) -> int:
        if os.fsdecode(path) == "sample.lock":
            attempts.append((flags, kwargs.get("dir_fd")))
            if len(attempts) == 1:
                raise FileNotFoundError("simulated concurrent O_CREAT race")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(filesystem.os, "open", transient_open)

    with exclusive_relative_file_lock(tmp_path, "ldvh/locks/sample.lock"):
        pass

    assert len(attempts) == 2
    assert attempts[0] == attempts[1]
    assert attempts[0][1] is not None
    assert (tmp_path / "ldvh/locks/sample.lock").is_file()


def test_allocator_private_state_directories_use_owner_only_mode(tmp_path: Path) -> None:
    previous_umask = os.umask(0)
    try:
        with exclusive_relative_file_lock(tmp_path, "ldvh/locks/sample.lock"):
            pass
    finally:
        os.umask(previous_umask)

    assert stat.S_IMODE((tmp_path / "ldvh").stat().st_mode) == 0o700
    assert stat.S_IMODE((tmp_path / "ldvh/locks").stat().st_mode) == 0o700


@_POSIX_ALLOCATOR_ONLY
def test_allocator_keys_separate_projects_and_fact_types(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    first = CreationBoundary("first", project, common_dir)
    second = CreationBoundary("second", project, common_dir)

    first_spark = _allocator_paths(first, LAYOUTS["spark"])
    second_spark = _allocator_paths(second, LAYOUTS["spark"])
    first_adr = _allocator_paths(first, LAYOUTS["adr"])

    assert len({first_spark[0], second_spark[0], first_adr[0]}) == 3
    assert len({first_spark[1], second_spark[1], first_adr[1]}) == 3
