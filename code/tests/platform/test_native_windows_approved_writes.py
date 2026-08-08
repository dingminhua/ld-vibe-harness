from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from ldvh.filesystem import (
    atomic_create_relative,
    native_atomic_fact_writes_supported,
    safe_read_relative,
)

CODE_ROOT = str(Path(__file__).resolve().parents[2])

pytestmark = [
    pytest.mark.native_windows,
    pytest.mark.skipif(sys.platform != "win32" or os.name != "nt", reason="requires native Windows"),
    pytest.mark.skipif(
        not native_atomic_fact_writes_supported(),
        reason="Windows native atomic fact-write backend has not been enabled",
    ),
]

# Worker script: acquire the shared lock, read an integer counter file, increment
# it, write it back atomically, and print the assigned sequence.  This exercises
# the full msvcrt.locking + atomic replace path under real multi-process contention.
_COUNTER_WORKER = r"""
import sys
from pathlib import Path
from ldvh.filesystem import (
    exclusive_relative_file_lock,
    safe_read_relative,
    atomic_replace_relative_if_equal,
    atomic_create_relative,
)

root = Path(sys.argv[1])
relative = sys.argv[2]
with exclusive_relative_file_lock(root, relative + ".lock"):
    try:
        current = int(safe_read_relative(root, relative).decode("ascii").strip())
        prior = f"{current}\n".encode("ascii")
    except FileNotFoundError:
        current = 0
        prior = None
    nxt = current + 1
    payload = f"{nxt}\n".encode("ascii")
    if prior is None:
        result = atomic_create_relative(root, relative, payload)
    else:
        result = atomic_replace_relative_if_equal(root, relative, prior, payload)
    if result.namespace_state != "committed":
        print(f"FAIL:{result.outcome}:{result.namespace_state}", file=sys.stderr)
        sys.exit(1)
    print(nxt)
"""

# Worker script: try a conditional replace of a known file.  The first process to
# acquire the lock wins; losers must see conflict and not corrupt the target.
_CONDITIONAL_WORKER = r"""
import sys
from pathlib import Path
from ldvh.filesystem import exclusive_relative_file_lock, atomic_replace_relative_if_equal

root = Path(sys.argv[1])
relative = sys.argv[2]
expected = sys.argv[3].encode("ascii")
replacement = sys.argv[4].encode("ascii")
with exclusive_relative_file_lock(root, relative + ".lock"):
    result = atomic_replace_relative_if_equal(root, relative, expected, replacement)
    print(result.outcome)
    print(result.namespace_state)
"""


def _child_environment() -> dict[str, str]:
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = CODE_ROOT if not existing else f"{CODE_ROOT}{os.pathsep}{existing}"
    return environment


def _launch_workers(script: str, root: Path, relative: str, count: int, *extra: str) -> list[subprocess.Popen[str]]:
    environment = _child_environment()
    processes: list[subprocess.Popen[str]] = []
    for _ in range(count):
        proc = subprocess.Popen(
            [sys.executable, "-c", script, str(root), relative, *extra],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(root),
            env=environment,
        )
        processes.append(proc)
    return processes


def _collect(processes: list[subprocess.Popen[str]]) -> list[tuple[int, str, str]]:
    results: list[tuple[int, str, str]] = []
    for proc in processes:
        try:
            stdout, stderr = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate(timeout=5)
            results.append((proc.returncode, stdout.strip(), f"TIMEOUT: {stderr.strip()}"))
        else:
            results.append((proc.returncode, stdout.strip(), stderr.strip()))
    return results


def test_native_six_process_allocator_contiguous_ids(tmp_path: Path) -> None:
    root = tmp_path / "allocator-root"
    root.mkdir()
    relative = "ldvh/fact-id-allocators/test-spark.counter"

    workers = _launch_workers(_COUNTER_WORKER, root, relative, 6)
    results = _collect(workers)

    # All workers must succeed.
    failures = [(rc, out, err) for rc, out, err in results if rc != 0]
    assert not failures, f"worker failures: {failures}"

    # Each worker prints its assigned sequence.
    sequences = sorted(int(out) for rc, out, _ in results)
    assert sequences == [1, 2, 3, 4, 5, 6], f"non-contiguous or duplicate IDs: {sequences}"

    # Final counter on disk must be exactly 6.
    final = int(safe_read_relative(root, relative).decode("ascii").strip())
    assert final == 6


def test_native_linked_worktree_shared_counter(tmp_path: Path) -> None:
    """The counter lives in git_common_dir/ldvh/ and is shared across linked worktrees."""
    repository = tmp_path / "repo"
    linked = tmp_path / "linked"
    repository.mkdir()
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(["git", "-C", str(repository), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(repository), "config", "user.email", "test@example.invalid"], check=True)
    (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "seed.txt"], check=True)
    subprocess.run(["git", "-C", str(repository), "commit", "-qm", "seed"], check=True)
    subprocess.run(["git", "-C", str(repository), "worktree", "add", "-qb", "linked-branch", str(linked)], check=True)

    common_dir = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    common_path = Path(common_dir)
    if not common_path.is_absolute():
        common_path = repository / common_path
    common_path = common_path.resolve()

    # Both worktrees must resolve to the same common dir.
    linked_common = subprocess.run(
        ["git", "-C", str(linked), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    linked_common_path = Path(linked_common)
    if not linked_common_path.is_absolute():
        linked_common_path = linked / linked_common_path
    linked_common_path = linked_common_path.resolve()
    assert common_path == linked_common_path

    relative = "ldvh/fact-id-allocators/test-spark.counter"

    # Launch 3 workers targeting the main repo common dir and 3 targeting linked.
    workers_main = _launch_workers(_COUNTER_WORKER, common_path, relative, 3)
    workers_linked = _launch_workers(_COUNTER_WORKER, linked_common_path, relative, 3)
    results = _collect(workers_main) + _collect(workers_linked)

    failures = [(rc, out, err) for rc, out, err in results if rc != 0]
    assert not failures, f"worker failures: {failures}"

    sequences = sorted(int(out) for rc, out, _ in results)
    assert sequences == [1, 2, 3, 4, 5, 6], f"cross-worktree counter diverged: {sequences}"

    final = int(safe_read_relative(common_path, relative).decode("ascii").strip())
    assert final == 6


def test_native_conditional_update_single_winner(tmp_path: Path) -> None:
    root = tmp_path / "cas-root"
    root.mkdir()
    relative = "ldvh-base/sparks/spark-0001.yaml"

    # Seed the target file.
    initial = b"version-1\n"
    created = atomic_create_relative(root, relative, initial)
    assert created.namespace_state == "committed"

    # Four processes all try to replace version-1 with version-2.
    workers = _launch_workers(
        _CONDITIONAL_WORKER, root, relative, 4, "version-1\n", "version-2\n"
    )
    results = _collect(workers)

    failures = [(rc, out, err) for rc, out, err in results if rc != 0]
    assert not failures, f"worker failures: {failures}"

    outcomes = [out.splitlines()[0] for _, out, _ in results]
    states = [out.splitlines()[1] for _, out, _ in results]

    # Exactly one winner (replaced + committed); the rest must see conflict or
    # unavailable, and none must report uncertain (which would mean corruption).
    replaced = sum(1 for o, s in zip(outcomes, states, strict=True) if o == "replaced" and s == "committed")
    uncertain = sum(1 for s in states if s == "uncertain")
    assert replaced == 1, f"expected exactly one winner, got {replaced}: {outcomes}"
    corrupted = [pair for pair in zip(outcomes, states, strict=True) if pair[1] == "uncertain"]
    assert uncertain == 0, f"uncertain result indicates potential corruption: {corrupted}"

    # Target must be exactly version-2 (no torn write).
    assert (root / relative).read_bytes() == b"version-2\n"
