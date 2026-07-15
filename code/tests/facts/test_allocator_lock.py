from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    CreationBoundary,
    _allocator_paths,
    allocate_object_id_locked,
    allocation_lock,
)

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
    project, common_dir = _repository(tmp_path)
    marker = project / "tracked.txt"
    marker.write_text("tracked\n", encoding="utf-8")
    _git(project, "add", "tracked.txt")
    _git(project, "-c", "user.name=LDVH Test", "-c", "user.email=ldvh@example.invalid", "commit", "-qm", "initial")
    linked = tmp_path / "linked"
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

    with allocation_lock(boundary, layout) as locked_counter:
        assert locked_counter == counter_path
        assert allocate_object_id_locked(boundary, layout, locked_counter) is None
    with allocation_lock(boundary, layout):
        pass

    assert lock_path.is_file()
    assert counter_path.read_text(encoding="ascii") == "corrupt\n"


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
