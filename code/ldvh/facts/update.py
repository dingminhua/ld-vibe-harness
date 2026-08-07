"""Atomic conditional replacement for one existing fact carrier."""

from __future__ import annotations

from pathlib import Path

from ldvh.facts.contracts import FactTypeLayout
from ldvh.filesystem import AtomicWriteResult, atomic_replace_relative_if_equal


def atomic_replace_text_if_unchanged(
    root: Path,
    layout: FactTypeLayout,
    object_id: str,
    expected_text: str,
    replacement_text: str,
) -> AtomicWriteResult:
    """Replace one regular file inside the caller's LDVH common-dir type lock."""

    return atomic_replace_relative_if_equal(
        root,
        layout.canonical_path(object_id),
        expected_text.encode("utf-8"),
        replacement_text.encode("utf-8"),
    )


__all__ = ["atomic_replace_text_if_unchanged"]
