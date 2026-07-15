from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts import candidate_discovery, relations
from ldvh.facts.candidate_discovery import discover_fact_candidates
from ldvh.facts.relations import ProjectFactIndex
from ldvh.filesystem import UnsafePathError


def _reparse_rejected(*args: object, **kwargs: object) -> tuple[Path, ...]:
    raise UnsafePathError("simulated reparse directory")


def test_candidate_discovery_marks_reparse_directories_incomplete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(candidate_discovery, "safe_list_directory", _reparse_rejected)

    snapshot = discover_fact_candidates(tmp_path, "sample", tmp_path / ".git", {})

    assert snapshot.complete is False
    assert snapshot.keys == ()
    assert len(snapshot.structural_problems) == 5
    assert all("link/reparse" in item["issues"][0]["summary"] for item in snapshot.structural_problems)


def test_relation_scan_marks_reparse_directory_incomplete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(relations, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(relations, "safe_list_directory", _reparse_rejected)
    index = ProjectFactIndex(tmp_path, "sample", {})

    reads, complete = index.scan_valid_objects("spark")

    assert reads == ()
    assert complete is False
