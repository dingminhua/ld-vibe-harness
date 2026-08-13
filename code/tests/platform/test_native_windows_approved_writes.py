from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from ldvh.filesystem import (
    atomic_create_relative,
    native_atomic_fact_writes_supported,
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
