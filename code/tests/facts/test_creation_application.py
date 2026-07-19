from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, allocation_lock
from ldvh.facts.creation_application import (
    FactCreationCommand,
    FactCreationResult,
    PreparedFactCreation,
    create_fact_object_locked,
    prepare_fact_creation,
)
from ldvh.facts.schema import project_fact_schemas
from ldvh.filesystem import AtomicWriteResult
from ldvh.specs.repository import inspect_repository


def _git(project: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _command(current_specs_repository: Path, tmp_path: Path) -> FactCreationCommand:
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    common_dir = Path(_git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    return FactCreationCommand(
        boundary=CreationBoundary("sample", project, common_dir),
        fact_type_key="spark",
        schemas=schemas,
        schema=schemas["spark"],
        requested_candidate_id="spark-0001",
        supplied={
            "title": "Application boundary",
            "status": "open",
            "source_refs": [{"kind": "repository-path", "locator": "docs/input.md"}],
            "summary": "The application layer owns the complete creation transaction.",
            "priority": "P2",
        },
        body=None,
    )


def test_application_module_has_no_helper_dependency() -> None:
    module = Path(__file__).resolve().parents[2] / "ldvh/facts/creation_application.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names} | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any(name == "ldvh.helper" or name.startswith("ldvh.helper.") for name in imports)


def test_prepared_creation_can_run_under_one_external_allocation_lock(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    prepared = prepare_fact_creation(command)

    assert isinstance(prepared, PreparedFactCreation)
    assert not (command.boundary.git_common_dir / "ldvh").exists()
    with allocation_lock(command.boundary, LAYOUTS["spark"]) as counter_path:
        result = create_fact_object_locked(prepared, counter_path)

    assert result.status == "created"
    assert result.actual_id == "spark-0001"
    assert result.read is not None and result.read.check_status == "mechanically_valid"
    assert (command.boundary.worktree_root / "ldvh-base/sparks/spark-0001.yaml").is_file()


def test_prepared_creation_defensively_freezes_nested_supplied_values(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    command.supplied["source_refs"] = [{"kind": "repository-path", "locator": "docs/original.md"}]
    prepared = prepare_fact_creation(command)
    assert isinstance(prepared, PreparedFactCreation)

    command.supplied["title"] = "mutated"
    command.supplied["source_refs"][0]["locator"] = "docs/mutated.md"
    with allocation_lock(command.boundary, LAYOUTS["spark"]) as counter_path:
        result = create_fact_object_locked(prepared, counter_path)

    assert result.status == "created"
    assert result.read is not None and result.read.fields is not None
    assert result.read.fields["title"] == "Application boundary"
    assert result.read.fields["source_refs"][0]["locator"] == "docs/original.md"


def test_caller_supplied_observation_time_binds_both_managed_timestamps(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    observed_at = "2026-07-15T16:00:00+08:00"

    prepared = prepare_fact_creation(command, observed_at=observed_at)

    assert isinstance(prepared, PreparedFactCreation)
    assert prepared.observed_at == observed_at
    with allocation_lock(command.boundary, LAYOUTS["spark"]) as counter_path:
        result = create_fact_object_locked(prepared, counter_path)
    assert result.status == "created"
    assert result.read is not None and result.read.fields is not None
    assert result.read.fields["created_at"] == observed_at
    assert result.read.fields["updated_at"] == observed_at


def test_candidate_rejection_has_no_allocator_or_fact_side_effect(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    command.supplied.pop("title")

    result = prepare_fact_creation(command)

    assert isinstance(result, FactCreationResult)
    assert result.status == "candidate_rejected"
    assert not (command.boundary.git_common_dir / "ldvh").exists()
    assert not (command.boundary.worktree_root / "facts").exists()


def test_durability_rejection_precedes_allocation_lock(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    monkeypatch.setattr("ldvh.facts.creation_application.durable_writes_enabled", lambda: False)

    result = prepare_fact_creation(command)

    assert isinstance(result, FactCreationResult)
    assert result.status == "durability_unavailable"
    assert not (command.boundary.git_common_dir / "ldvh").exists()
    assert not (command.boundary.worktree_root / "facts").exists()


def test_locked_creation_preserves_sixteen_conflict_limit_and_consumed_ids(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    prepared = prepare_fact_creation(command)
    assert isinstance(prepared, PreparedFactCreation)
    monkeypatch.setattr(
        "ldvh.facts.creation_application.atomic_create_text",
        lambda *args, **kwargs: AtomicWriteResult("conflict", "not_committed", "unknown", "clean"),
    )

    with allocation_lock(command.boundary, LAYOUTS["spark"]) as counter_path:
        result = create_fact_object_locked(prepared, counter_path)

    assert result.status == "allocation_unavailable"
    assert result.allocation_consumed is True
    counters = tuple((command.boundary.git_common_dir / "ldvh/fact-id-allocators").glob("*.counter"))
    assert len(counters) == 1
    assert counters[0].read_text(encoding="ascii") == "16\n"
    assert not (command.boundary.worktree_root / "facts").exists()
