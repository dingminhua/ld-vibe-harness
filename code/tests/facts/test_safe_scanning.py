from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts import candidate_discovery, relations
from ldvh.facts.candidate_discovery import discover_fact_candidates, discover_fact_type_raw
from ldvh.facts.models import FactIssue
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema
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


def test_raw_type_scan_detects_listing_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def changing_listing(*args: object, **kwargs: object) -> tuple[Path, ...]:
        nonlocal calls
        calls += 1
        return () if calls == 1 else (tmp_path / "ldvh-base/sparks/spark-0001.yaml",)

    monkeypatch.setattr(candidate_discovery, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(candidate_discovery, "safe_list_directory", changing_listing)

    snapshot = discover_fact_type_raw(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
        "spark",
    )

    assert snapshot.coverage_complete is False
    assert snapshot.objects == ()
    assert "扫描期间发生变化" in snapshot.structural_problems[-1]["issues"][0]["summary"]


def test_raw_type_scan_marks_unsafe_directory_incomplete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(candidate_discovery, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(candidate_discovery, "safe_list_directory", _reparse_rejected)

    snapshot = discover_fact_type_raw(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
        "spark",
    )

    assert snapshot.coverage_complete is False
    assert snapshot.objects == ()
    assert "无法安全完整枚举" in snapshot.structural_problems[0]["issues"][0]["summary"]


def test_raw_type_scan_counts_noncanonical_carriers_toward_coverage_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = tuple(tmp_path / f"legacy-{index}.yaml" for index in range(relations.MAX_GRAPH_OBJECTS + 1))
    monkeypatch.setattr(candidate_discovery, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(candidate_discovery, "safe_list_directory", lambda *args, **kwargs: paths)

    snapshot = discover_fact_type_raw(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
        "spark",
    )

    assert snapshot.coverage_complete is False
    assert snapshot.objects == ()
    assert "10,000" in snapshot.structural_problems[0]["issues"][0]["summary"]


def test_raw_type_scan_preserves_invalid_read_instead_of_filtering_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "ldvh-base/sparks/spark-0001.yaml"
    monkeypatch.setattr(candidate_discovery, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(candidate_discovery, "safe_list_directory", lambda *args, **kwargs: (path,))
    monkeypatch.setattr(
        ProjectFactIndex,
        "read",
        lambda *args, **kwargs: FactReadResult(
            "ldvh-base/sparks/spark-0001.yaml",
            "yaml",
            "invalid",
            None,
            None,
            (FactIssue("schema", "forced invalid"),),
        ),
    )

    snapshot = discover_fact_type_raw(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
        "spark",
    )

    assert snapshot.coverage_complete is True
    assert snapshot.objects[0][1].check_status == "invalid"
