from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ldvh.facts import web_read_application
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.web_direct_capture import create_web_spark_direct_capture
from ldvh.facts.web_read_application import read_web_spark_detail, read_web_spark_list
from ldvh.specs.repository import inspect_repository


def _git(project: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _fixture(current_specs_repository: Path, tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    common = Path(_git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    return CreationBoundary("sample", project, common), schemas


def test_list_and_detail_preserve_complete_empty_and_valid_objects(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)

    assert read_web_spark_list(boundary, schemas).status == "complete"
    assert read_web_spark_detail(boundary, schemas, "spark-9999").status == "not_found"
    created = create_web_spark_direct_capture(
        boundary,
        schemas,
        {"title": "Reader", "description": "Read one Spark", "priority": "P2"},
    )
    assert created.status == "created"

    listed = read_web_spark_list(boundary, schemas)
    detail = read_web_spark_detail(boundary, schemas, "spark-0001")

    assert listed.status == "complete"
    assert len(listed.items) == 1
    assert listed.items[0]["object_ref"]["object_id"] == "spark-0001"
    assert listed.items[0]["fact_object"]["title"] == "Reader"
    assert detail.status == "ok"
    assert detail.item == listed.items[0]
    assert detail.coverage_status == "complete"


def test_list_and_detail_accept_ignored_current_spark(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    (boundary.worktree_root / ".gitignore").write_text("ldvh-base/\n", encoding="utf-8")
    created = create_web_spark_direct_capture(
        boundary,
        schemas,
        {"title": "Ignored reader", "description": "Read ignored current Spark", "priority": "P2"},
    )
    assert created.status == "created"

    listed = read_web_spark_list(boundary, schemas)
    detail = read_web_spark_detail(boundary, schemas, "spark-0001")

    assert listed.status == "complete"
    assert len(listed.items) == 1
    assert detail.status == "ok"
    assert detail.item == listed.items[0]


def test_invalid_object_is_partial_and_exact_detail_is_invalid(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    assert (
        create_web_spark_direct_capture(
            boundary,
            schemas,
            {"title": "Reader", "description": "Read one Spark", "priority": "P2"},
        ).status
        == "created"
    )
    carrier = boundary.worktree_root / "ldvh-base/sparks/spark-0001.yaml"
    carrier.write_text(carrier.read_text(encoding="utf-8").replace("title: Reader\n", ""), encoding="utf-8")

    listed = read_web_spark_list(boundary, schemas)
    detail = read_web_spark_detail(boundary, schemas, "spark-0001")

    assert listed.status == "partial"
    assert listed.items == ()
    assert len(listed.object_problems) == 1
    assert detail.status == "invalid"
    assert detail.item is None
    assert detail.problems == listed.object_problems
    assert detail.coverage_status == "partial"


def test_noncanonical_carrier_blocks_absence_claim_as_integrity_conflict(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    directory = boundary.worktree_root / "ldvh-base/sparks"
    directory.mkdir(parents=True)
    (directory / "renamed.yaml").write_text("not: canonical\n", encoding="utf-8")

    listed = read_web_spark_list(boundary, schemas)
    missing = read_web_spark_detail(boundary, schemas, "spark-9999")

    assert listed.status == "integrity_conflict"
    assert listed.structural_problems
    assert missing.status == "unavailable"
    assert missing.coverage_status == "integrity_conflict"
    assert missing.problems == listed.structural_problems


def test_raw_and_projected_aggregate_budgets_fail_typed_instead_of_accumulating(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    assert (
        create_web_spark_direct_capture(
            boundary,
            schemas,
            {"title": "Budget", "description": "Bound aggregate memory", "priority": "P2"},
        ).status
        == "created"
    )

    monkeypatch.setattr(web_read_application, "MAX_WEB_SPARK_RAW_BYTES", 1)
    raw_limited = read_web_spark_list(boundary, schemas)
    assert raw_limited.status == "unavailable"
    assert raw_limited.items == ()
    assert "聚合预算" in raw_limited.structural_problems[0]["issues"][0]["summary"]

    monkeypatch.setattr(web_read_application, "MAX_WEB_SPARK_RAW_BYTES", 16 * 1024 * 1024)
    monkeypatch.setattr(web_read_application, "MAX_WEB_SPARK_PROJECTED_BYTES", 1)
    projected_limited = read_web_spark_list(boundary, schemas)
    assert projected_limited.status == "unavailable"
    assert projected_limited.items == ()
    assert "聚合预算" in projected_limited.structural_problems[0]["issues"][0]["summary"]
