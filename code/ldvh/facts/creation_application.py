"""Helper-independent application transaction for controlled fact creation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    CreationBoundary,
    allocate_object_id_locked,
    allocation_lock,
    atomic_create_text,
    rollback_created_text,
    serialize_fact_object,
)
from ldvh.facts.models import FactIssue
from ldvh.facts.relations import ProjectFactIndex, validate_project_relations
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.source_validation import validate_study_sources
from ldvh.facts.validation import validate_fact_object
from ldvh.filesystem import AtomicWriteResult, durable_writes_enabled

CreationStatus = Literal[
    "candidate_rejected",
    "candidate_unavailable",
    "durability_unavailable",
    "final_rejected",
    "final_unavailable",
    "allocation_unavailable",
    "readback_failed",
    "created",
]


@dataclass(frozen=True, slots=True)
class FactCreationCommand:
    boundary: CreationBoundary
    fact_type_key: str
    schemas: dict[str, FactSchema]
    schema: FactSchema
    requested_candidate_id: str
    supplied: dict[str, Any]
    body: str | None


@dataclass(frozen=True, slots=True)
class FactCreationResult:
    status: CreationStatus
    issues: tuple[FactIssue, ...] = ()
    actual_id: str | None = None
    actual_fields: dict[str, Any] | None = None
    actual_text: str | None = None
    read: FactReadResult | None = None
    allocation_consumed: bool = False
    creation_result: AtomicWriteResult | None = None
    rollback_result: AtomicWriteResult | None = None


@dataclass(frozen=True, slots=True)
class PreparedFactCreation:
    command: FactCreationCommand
    observed_at: str


def _preflight(
    command: FactCreationCommand,
    object_id: str,
    now: str,
) -> tuple[dict[str, Any], str, tuple[FactIssue, ...], bool]:
    layout = LAYOUTS[command.fact_type_key]
    fields = {
        **command.supplied,
        "object_id": object_id,
        "fact_type_key": command.fact_type_key,
        "created_at": now,
        "updated_at": now,
    }
    text = serialize_fact_object(layout, fields, command.body)
    parsed = parse_study_markdown(text) if layout.carrier == "markdown" else parse_yaml_object(text)
    issues = list(parsed.issues)
    if parsed.fields is None:
        return fields, text, tuple(issues), False
    issues.extend(validate_fact_object(command.fact_type_key, parsed.fields, command.schema))
    if issues:
        return fields, text, tuple(issues), False
    read = FactReadResult(
        layout.canonical_path(object_id), layout.carrier, "mechanically_valid", parsed.fields, parsed.body, ()
    )
    index = ProjectFactIndex(
        command.boundary.worktree_root,
        command.boundary.governed_project_id,
        command.schemas,
        command.boundary.git_common_dir,
    )
    index.cache[(command.fact_type_key, object_id)] = read
    index.base_cache[(command.fact_type_key, object_id)] = read
    relation_issues, relation_unavailable = validate_project_relations(
        index,
        command.fact_type_key,
        object_id,
        read,
    )
    source_issues: tuple[FactIssue, ...] = ()
    source_unavailable = False
    if command.fact_type_key == "study":
        source_issues, source_unavailable = validate_study_sources(index, read)
    return fields, text, (*relation_issues, *source_issues), relation_unavailable or source_unavailable


def prepare_fact_creation(command: FactCreationCommand) -> PreparedFactCreation | FactCreationResult:
    """Perform side-effect-free checks required before taking the allocation lock."""

    now = datetime.now().astimezone().isoformat()
    _, _, candidate_issues, candidate_unavailable = _preflight(command, command.requested_candidate_id, now)
    if candidate_unavailable:
        return FactCreationResult("candidate_unavailable", issues=candidate_issues)
    if candidate_issues:
        return FactCreationResult("candidate_rejected", issues=candidate_issues)
    if not durable_writes_enabled():
        return FactCreationResult("durability_unavailable")
    return PreparedFactCreation(command, now)


def create_fact_object_locked(prepared: PreparedFactCreation, counter_path: Path) -> FactCreationResult:
    """Allocate and create while the caller holds the fact type's allocation lock."""

    command = prepared.command
    now = prepared.observed_at
    layout = LAYOUTS[command.fact_type_key]
    allocation_consumed = False
    actual_id: str | None = None
    actual_fields: dict[str, Any] | None = None
    actual_text: str | None = None
    creation_result: AtomicWriteResult | None = None
    for _ in range(16):
        actual_id = allocate_object_id_locked(command.boundary, layout, counter_path)
        if actual_id is None:
            break
        allocation_consumed = True
        actual_fields, actual_text, issues, unavailable = _preflight(command, actual_id, now)
        if issues or unavailable:
            return FactCreationResult(
                "final_unavailable" if unavailable else "final_rejected",
                issues=issues,
                actual_id=actual_id,
                actual_fields=actual_fields,
                actual_text=actual_text,
                allocation_consumed=True,
            )
        creation_result = atomic_create_text(command.boundary.worktree_root, layout, actual_id, actual_text)
        if creation_result.outcome == "created" and creation_result.namespace_state == "committed":
            break
        if creation_result.outcome != "conflict":
            actual_id = None
            break
        actual_id = None
    if actual_id is None or actual_fields is None or actual_text is None:
        return FactCreationResult(
            "allocation_unavailable",
            allocation_consumed=allocation_consumed,
            creation_result=creation_result,
        )

    read = read_fact_object(
        command.boundary.worktree_root,
        layout,
        command.schema,
        actual_id,
        expected_common_dir=command.boundary.git_common_dir,
    )
    post_issues: tuple[FactIssue, ...] = ()
    post_unavailable = False
    if read.check_status == "mechanically_valid" and read.fields is not None:
        index = ProjectFactIndex(
            command.boundary.worktree_root,
            command.boundary.governed_project_id,
            command.schemas,
            command.boundary.git_common_dir,
        )
        index.cache[(command.fact_type_key, actual_id)] = read
        index.base_cache[(command.fact_type_key, actual_id)] = read
        post_issues, post_unavailable = validate_project_relations(index, command.fact_type_key, actual_id, read)
        if command.fact_type_key == "study":
            source_issues, source_unavailable = validate_study_sources(index, read)
            post_issues = (*post_issues, *source_issues)
            post_unavailable = post_unavailable or source_unavailable
    if read.check_status != "mechanically_valid" or post_issues or post_unavailable:
        rollback = rollback_created_text(command.boundary.worktree_root, layout, actual_id, actual_text)
        return FactCreationResult(
            "readback_failed",
            issues=(*read.issues, *post_issues),
            actual_id=actual_id,
            actual_fields=actual_fields,
            actual_text=actual_text,
            read=read,
            allocation_consumed=True,
            creation_result=creation_result,
            rollback_result=rollback,
        )

    return FactCreationResult(
        "created",
        actual_id=actual_id,
        actual_fields=actual_fields,
        actual_text=actual_text,
        read=read,
        allocation_consumed=True,
        creation_result=creation_result,
    )


def create_fact_object(command: FactCreationCommand) -> FactCreationResult:
    """Validate, allocate, create, read back, and conditionally roll back one fact."""

    prepared = prepare_fact_creation(command)
    if isinstance(prepared, FactCreationResult):
        return prepared
    layout = LAYOUTS[command.fact_type_key]
    with allocation_lock(command.boundary, layout) as counter_path:
        return create_fact_object_locked(prepared, counter_path)


__all__ = [
    "CreationStatus",
    "FactCreationCommand",
    "FactCreationResult",
    "PreparedFactCreation",
    "create_fact_object",
    "create_fact_object_locked",
    "prepare_fact_creation",
]
