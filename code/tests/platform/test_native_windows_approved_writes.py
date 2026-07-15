from __future__ import annotations

import os
import sys

import pytest

from ldvh.filesystem import durable_writes_enabled

pytestmark = [
    pytest.mark.native_windows,
    pytest.mark.skipif(sys.platform != "win32" or os.name != "nt", reason="requires native Windows"),
    pytest.mark.skipif(not durable_writes_enabled(), reason="Windows file_only durability has not been accepted"),
]


def test_approved_native_write_matrix_must_be_implemented_after_the_human_gate() -> None:
    pytest.fail(
        "the approved six-process allocator, shared linked-worktree counter and conditional-update "
        "single-winner probes must replace this fail-closed sentinel when Windows writes are authorized"
    )
