from __future__ import annotations

import os
import sys

import pytest

from ldvh.filesystem import native_atomic_fact_writes_supported

pytestmark = [
    pytest.mark.native_windows,
    pytest.mark.skipif(sys.platform != "win32" or os.name != "nt", reason="requires native Windows"),
    pytest.mark.skipif(
        not native_atomic_fact_writes_supported(),
        reason="Windows native atomic fact-write backend has not been enabled",
    ),
]


def test_approved_native_write_matrix_must_be_implemented_after_the_human_gate() -> None:
    pytest.fail(
        "the approved six-process allocator, shared linked-worktree counter and conditional-update "
        "single-winner probes must replace this fail-closed sentinel when Windows writes are authorized"
    )
