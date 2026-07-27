from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts import candidate_discovery, relations
from ldvh.facts.candidate_discovery import discover_fact_candidates
from ldvh.facts.relations import ProjectFactIndex
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
    assert all(
        "符号链接或重解析点" in item["issues"][0]["summary"] and "安全、完整地枚举" in item["issues"][0]["summary"]
        for item in snapshot.structural_problems
    )


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


def test_missing_type_directories_are_incomplete_for_discovery_and_negative_relation_proofs(tmp_path: Path) -> None:
    snapshot = discover_fact_candidates(tmp_path, "sample", tmp_path / ".git", {})
    index = ProjectFactIndex(tmp_path, "sample", {})

    reads, complete = index.scan_valid_objects("workcase", require_all_canonical_valid=True)

    assert snapshot.complete is False
    assert len(snapshot.structural_problems) == 5
    assert all(item["check_status"] == "unavailable" for item in snapshot.structural_problems)
    assert reads == ()
    assert complete is False


def test_candidate_discovery_reports_noncanonical_carriers_as_incomplete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "ldvh-base/sparks/legacy.yaml"
    monkeypatch.setattr(
        candidate_discovery,
        "safe_list_directory",
        lambda _root, directory: (path,) if directory == "ldvh-base/sparks" else (),
    )

    snapshot = discover_fact_candidates(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
    )

    assert snapshot.complete is False
    assert snapshot.keys == ()
    assert snapshot.structural_problems == (
        {
            "fact_type_key": "spark",
            "canonical_path": "ldvh-base/sparks/legacy.yaml",
            "check_status": "unavailable",
            "issues": [
                {
                    "category": "location",
                    "field_path": None,
                    "summary": "该载体不符合当前事实类型的权威文件路径与对象身份规则",
                }
            ],
        },
    )


def test_candidate_discovery_reports_wrong_suffix_without_consuming_canonical_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrong_suffix = tmp_path / "ldvh-base/sparks/spark-0001.yml"
    canonical = tmp_path / "ldvh-base/sparks/spark-0001.yaml"
    canonical.parent.mkdir(parents=True)
    canonical.write_text(
        "object_id: spark-0001\nfact_type_key: spark\nsummary: carrier\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(candidate_discovery, "MAX_GRAPH_OBJECTS", 1)
    monkeypatch.setattr(
        candidate_discovery,
        "safe_list_directory",
        lambda _root, directory: (wrong_suffix, canonical) if directory == "ldvh-base/sparks" else (),
    )

    snapshot = discover_fact_candidates(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
    )

    assert snapshot.complete is False
    assert snapshot.keys == (("spark", "spark-0001"),)
    assert snapshot.structural_problems == (
        {
            "fact_type_key": "spark",
            "canonical_path": "ldvh-base/sparks/spark-0001.yml",
            "check_status": "unavailable",
            "issues": [
                {
                    "category": "location",
                    "field_path": None,
                    "summary": "该载体不符合当前事实类型的权威文件路径与对象身份规则",
                }
            ],
        },
    )
