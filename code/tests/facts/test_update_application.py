from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from ldvh.facts import update_application
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.update_application import FactUpdateCommand, apply_fact_update
from ldvh.specs.repository import inspect_repository


def _git(project: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _command(current_specs_repository: Path, tmp_path: Path) -> tuple[FactUpdateCommand, Path]:
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    common_dir = Path(_git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    fact = project / "ldvh-base/sparks/spark-0001.yaml"
    fact.parent.mkdir(parents=True)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Application update
created_at: 2026-07-20T09:00:00+08:00
updated_at: 2026-07-20T10:00:00+08:00
status: open
summary: Before update
priority: P2
""",
        encoding="utf-8",
    )
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    current = update_application._project_read(
        FactUpdateCommand(
            boundary=CreationBoundary("sample", project, common_dir),
            fact_type_key="spark",
            object_id="spark-0001",
            schemas=schemas,
            schema=schemas["spark"],
            expected_content_fingerprint="0" * 64,
            supplied={},
            body=None,
            event_at="2026-07-20T11:00:00+08:00",
        )
    )
    assert current.fields is not None and current.content_fingerprint is not None
    supplied = {key: value for key, value in current.fields.items() if key not in update_application.MANAGED_FIELDS}
    supplied["summary"] = "After update"
    return (
        FactUpdateCommand(
            boundary=CreationBoundary("sample", project, common_dir),
            fact_type_key="spark",
            object_id="spark-0001",
            schemas=schemas,
            schema=schemas["spark"],
            expected_content_fingerprint=current.content_fingerprint,
            supplied=supplied,
            body=None,
            event_at="2026-07-20T11:00:00+08:00",
        ),
        fact,
    )


def test_application_module_has_no_helper_dependency() -> None:
    module = Path(__file__).resolve().parents[2] / "ldvh/facts/update_application.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names} | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any(name == "ldvh.helper" or name.startswith("ldvh.helper.") for name in imports)


def test_application_binds_managed_timestamp_and_verifies_exact_readback(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)

    result = apply_fact_update(command)

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["updated_at"] == command.event_at
    assert result.readback.fields["summary"] == "After update"
    assert result.readback.raw_text == result.candidate_text
    assert fact.read_text(encoding="utf-8") == result.candidate_text


def test_no_change_does_not_require_successor_or_rewrite(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)
    current = update_application._project_read(command)
    assert current.fields is not None
    supplied = {key: value for key, value in current.fields.items() if key not in update_application.MANAGED_FIELDS}
    no_change = FactUpdateCommand(
        boundary=command.boundary,
        fact_type_key=command.fact_type_key,
        object_id=command.object_id,
        schemas=command.schemas,
        schema=command.schema,
        expected_content_fingerprint=command.expected_content_fingerprint,
        supplied=supplied,
        body=None,
        event_at="2026-07-20T08:00:00+08:00",
    )
    original = fact.read_bytes()
    inode = fact.stat().st_ino

    result = apply_fact_update(no_change)

    assert result.status == "no_change"
    assert fact.read_bytes() == original
    assert fact.stat().st_ino == inode


def test_open_spark_can_enter_implemented_without_a_routed_to_target(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, _fact = _command(current_specs_repository, tmp_path)
    supplied = dict(command.supplied)
    supplied.update(
        {
            "status": "implemented",
            "disposition_summary": (
                "The bounded Spark content was directly implemented with no residual fact responsibility."
            ),
            "closed_at": command.event_at,
        }
    )
    supplied.pop("priority")

    result = apply_fact_update(
        FactUpdateCommand(
            boundary=command.boundary,
            fact_type_key=command.fact_type_key,
            object_id=command.object_id,
            schemas=command.schemas,
            schema=command.schema,
            expected_content_fingerprint=command.expected_content_fingerprint,
            supplied=supplied,
            body=None,
            event_at=command.event_at,
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["status"] == "implemented"


def test_parseable_invalid_spark_can_be_repaired_to_implemented_with_exact_cas(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Application update
created_at: 2026-07-20T09:00:00+08:00
updated_at: 2026-07-20T10:00:00+08:00
status: routed
summary: Before update
disposition_summary: Incorrectly recorded as routed without a fact target.
closed_at: 2026-07-20T10:00:00+08:00
""",
        encoding="utf-8",
    )
    current = update_application._project_read(command)
    assert current.check_status == "invalid"
    assert current.fields is not None and current.content_fingerprint is not None
    supplied = {key: value for key, value in current.fields.items() if key not in update_application.MANAGED_FIELDS}
    supplied.update(
        {
            "status": "implemented",
            "disposition_summary": (
                "The bounded Spark content was directly implemented with no residual fact responsibility."
            ),
            "closed_at": command.event_at,
        }
    )

    result = apply_fact_update(
        FactUpdateCommand(
            boundary=command.boundary,
            fact_type_key=command.fact_type_key,
            object_id=command.object_id,
            schemas=command.schemas,
            schema=command.schema,
            expected_content_fingerprint=current.content_fingerprint,
            supplied=supplied,
            body=None,
            event_at=command.event_at,
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.check_status == "mechanically_valid"
    assert result.readback.fields is not None and result.readback.fields["status"] == "implemented"


def test_non_successor_event_time_and_stale_fingerprint_have_zero_writes(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)
    original = fact.read_bytes()
    non_successor = FactUpdateCommand(
        boundary=command.boundary,
        fact_type_key=command.fact_type_key,
        object_id=command.object_id,
        schemas=command.schemas,
        schema=command.schema,
        expected_content_fingerprint=command.expected_content_fingerprint,
        supplied=command.supplied,
        body=None,
        event_at="2026-07-20T10:00:00+08:00",
    )

    assert apply_fact_update(non_successor).status == "event_time_not_successor"
    assert fact.read_bytes() == original
    stale = FactUpdateCommand(
        boundary=command.boundary,
        fact_type_key=command.fact_type_key,
        object_id=command.object_id,
        schemas=command.schemas,
        schema=command.schema,
        expected_content_fingerprint="0" * 64,
        supplied=command.supplied,
        body=None,
        event_at=command.event_at,
    )
    assert apply_fact_update(stale).status == "fingerprint_stale"
    assert fact.read_bytes() == original


def test_failed_exact_readback_rolls_back_only_matching_replacement(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)
    original = fact.read_bytes()
    actual_project_read = update_application._project_read
    calls = 0

    def failing_readback(application_command: FactUpdateCommand) -> FactReadResult:
        nonlocal calls
        calls += 1
        if calls == 2:
            return FactReadResult(
                "ldvh-base/sparks/spark-0001.yaml",
                "yaml",
                "invalid",
                None,
                None,
                (FactIssue("schema", "simulated write-back failure"),),
            )
        return actual_project_read(application_command)

    monkeypatch.setattr(update_application, "_project_read", failing_readback)

    result = apply_fact_update(command)

    assert result.status == "readback_failed"
    assert result.rollback_result is not None
    assert result.rollback_result.outcome == "replaced"
    assert result.rollback_result.namespace_state == "committed"
    assert fact.read_bytes() == original
