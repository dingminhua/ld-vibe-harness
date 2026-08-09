"""Core transaction tests for legacy change-log migration."""

from __future__ import annotations

import subprocess
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.legacy_change_log_migration import (
    LegacyChangeLogMigrationCommand,
    apply_legacy_change_log_migration,
)
from ldvh.facts.schema import FactSchema
from ldvh.time import canonical_utc_timestamp


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _boundary(tmp_path: Path) -> CreationBoundary:
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    fact = project / "ldvh-base" / "sparks" / "spark-0001.yaml"
    fact.parent.mkdir(parents=True)
    for directory in ("adrs", "pitfalls", "studies", "workcases"):
        (project / "ldvh-base" / directory).mkdir(parents=True)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Legacy object
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: open
summary: Before migration
priority: P2
""",
        encoding="utf-8",
    )
    return CreationBoundary("sample", project, project / ".git")


def _command(
    current_fact_schemas: Mapping[str, FactSchema],
    boundary: CreationBoundary,
    fingerprint: str,
    *,
    event_at: str = "2026-07-14T11:00:00+08:00",
) -> LegacyChangeLogMigrationCommand:
    schemas = current_fact_schemas
    return LegacyChangeLogMigrationCommand(
        boundary=boundary,
        fact_type_key="spark",
        object_id="spark-0001",
        schemas=schemas,
        schema=schemas["spark"],
        expected_content_fingerprint=fingerprint,
        migration_signature={
            "agent_id": "test-agent",
            "host_environment": "test",
            "session_id": "test-session",
        },
        migration_summary="受 Human 授权建立历史不可得时的可信迁移起点。",
        event_at=event_at,
    )


def _fingerprint(boundary: CreationBoundary, current_fact_schemas: Mapping[str, FactSchema]) -> str:
    from ldvh.facts.repository import read_fact_object

    schema = current_fact_schemas["spark"]
    read = read_fact_object(
        boundary.worktree_root,
        LAYOUTS["spark"],
        schema,
        "spark-0001",
        expected_common_dir=boundary.git_common_dir,
    )
    assert read.content_fingerprint is not None
    return read.content_fingerprint


def test_migration_preserves_all_non_managed_fields(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    boundary = _boundary(tmp_path)
    fingerprint = _fingerprint(boundary, current_fact_schemas)

    result = apply_legacy_change_log_migration(_command(current_fact_schemas, boundary, fingerprint))

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    fields = result.readback.fields
    assert fields["created_at"] == "2026-07-14T09:00:00+08:00"
    assert fields["updated_at"] == canonical_utc_timestamp("2026-07-14T11:00:00+08:00")
    assert fields["status"] == "open"
    assert fields["priority"] == "P2"
    assert fields["summary"] == "Before migration"
    change_log = fields["change_log"]
    assert len(change_log) == 1
    assert change_log[0]["at"] == fields["updated_at"]
    assert set(change_log[0]["signature"]) == {"agent_id", "host_environment"}


def test_migration_rejects_existing_change_log(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    boundary = _boundary(tmp_path)
    fingerprint = _fingerprint(boundary, current_fact_schemas)
    first = apply_legacy_change_log_migration(_command(current_fact_schemas, boundary, fingerprint))
    assert first.status == "updated"
    migrated = _fingerprint(boundary, current_fact_schemas)

    replay = apply_legacy_change_log_migration(_command(current_fact_schemas, boundary, migrated))

    assert replay.status == "change_log_present"


def test_migration_rejects_stale_fingerprint(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    boundary = _boundary(tmp_path)
    result = apply_legacy_change_log_migration(_command(current_fact_schemas, boundary, "0" * 64))
    assert result.status == "fingerprint_stale"


def test_migration_rejects_non_successor_event_time(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    boundary = _boundary(tmp_path)
    fingerprint = _fingerprint(boundary, current_fact_schemas)
    result = apply_legacy_change_log_migration(
        _command(
            current_fact_schemas,
            boundary,
            fingerprint,
            event_at="2026-07-14T10:00:00+08:00",
        )
    )
    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "updated_at" for issue in result.issues)


def test_concurrent_migrations_leave_a_single_winner(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    boundary = _boundary(tmp_path)
    fingerprint = _fingerprint(boundary, current_fact_schemas)

    def run_one() -> str:
        return apply_legacy_change_log_migration(_command(current_fact_schemas, boundary, fingerprint)).status

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(lambda _index: run_one(), range(2)))

    assert outcomes.count("updated") == 1
    assert outcomes.count("fingerprint_stale") + outcomes.count("change_log_present") == 1
