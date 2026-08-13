from __future__ import annotations

import errno
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, FactCoordinationUnavailable, fact_write_lock

CODE_ROOT = Path(__file__).resolve().parents[2]

_LOCK_WORKER = """
import sys
import time
from pathlib import Path
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, fact_write_lock

boundary = CreationBoundary("sample", Path(sys.argv[1]), Path(sys.argv[2]))
result_path = Path(sys.argv[3])
with fact_write_lock(boundary, LAYOUTS["spark"]):
    started = time.monotonic_ns()
    time.sleep(0.1)
    ended = time.monotonic_ns()
result_path.write_text(f"{started} {ended}\\n", encoding="ascii")
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


def _lock_path(boundary: CreationBoundary) -> Path:
    project_hash = hashlib.sha256(boundary.governed_project_id.encode()).hexdigest()[:24]
    return boundary.git_common_dir / "ldvh" / "fact-creation-locks" / f"{project_hash}-spark.lock"


def test_fact_write_lock_serializes_linked_worktrees_without_creating_counter(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    marker = project / "tracked.txt"
    marker.write_text("tracked\n", encoding="utf-8")
    _git(project, "add", "tracked.txt")
    _git(project, "-c", "user.name=LDVH Test", "-c", "user.email=ldvh@example.invalid", "commit", "-qm", "initial")
    linked = tmp_path / "linked"
    _git(project, "worktree", "add", "-qb", "linked-lock", str(linked))
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _LOCK_WORKER, str(root), str(common_dir), str(tmp_path / f"result-{index}")],
            cwd=root,
            env=_environment(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for index, root in enumerate((project, linked))
    ]
    for process in processes:
        _, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stderr

    intervals = sorted(
        tuple(map(int, (tmp_path / f"result-{index}").read_text(encoding="ascii").split())) for index in range(2)
    )
    assert intervals[1][0] >= intervals[0][1]
    assert not (common_dir / "ldvh/fact-id-allocators").exists()


def test_fact_write_lock_rejects_linked_state_directory(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    outside = tmp_path / "outside-state"
    outside.mkdir()
    try:
        (common_dir / "ldvh").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(OSError):
        with fact_write_lock(CreationBoundary("sample", project, common_dir), LAYOUTS["spark"]):
            pytest.fail("unsafe state must not be locked")
    assert tuple(outside.iterdir()) == ()


def test_fact_write_lock_rejects_linked_final_lock_file(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    boundary = CreationBoundary("sample", project, common_dir)
    lock_path = _lock_path(boundary)
    lock_path.parent.mkdir(parents=True)
    outside = tmp_path / "outside.lock"
    outside.write_bytes(b"outside")
    try:
        lock_path.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(OSError):
        with fact_write_lock(boundary, LAYOUTS["spark"]):
            pytest.fail("unsafe lock file must not be opened")
    assert outside.read_bytes() == b"outside"


@pytest.mark.parametrize(
    ("error", "category"),
    [
        (PermissionError(), "permission_denied"),
        (OSError(errno.EROFS, "read-only filesystem"), "read_only_filesystem"),
    ],
)
def test_fact_write_lock_classifies_only_entry_permission_failures(
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
        with fact_write_lock(boundary, LAYOUTS["spark"]):
            pytest.fail("the lock body must not run")
    assert observed.value.system_error_category == category


def test_fact_write_lock_does_not_reclassify_permission_failure_inside_body(tmp_path: Path) -> None:
    project, common_dir = _repository(tmp_path)
    boundary = CreationBoundary("sample", project, common_dir)

    with pytest.raises(PermissionError):
        with fact_write_lock(boundary, LAYOUTS["spark"]):
            raise PermissionError("target write failed after lock entry")
