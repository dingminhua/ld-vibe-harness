"""Helper-independent application transaction for controlled fact creation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    AllocationPreview,
    CreationBoundary,
    allocate_object_id_locked,
    allocation_lock,
    atomic_create_text,
    commit_object_id_locked,
    preview_object_id_locked,
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
    "attempt_rejected",
    "attempt_unavailable",
    "allocation_stale",
    "allocation_unavailable",
    "creation_conflict",
    "readback_failed",
    "created",
]


@dataclass(frozen=True, slots=True)
class FactCreationCommand:
    boundary: CreationBoundary
    fact_type_key: str
    schemas: Mapping[str, FactSchema]
    schema: FactSchema
    requested_candidate_id: str
    supplied: Mapping[str, Any]
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
    allocation_status: str | None = None


@dataclass(frozen=True, slots=True)
class PreparedFactCreation:
    command: FactCreationCommand
    observed_at: str


@dataclass(frozen=True, slots=True)
class PreparedFactCreationAttempt:
    prepared: PreparedFactCreation
    allocation: AllocationPreview
    fields: Mapping[str, Any]
    text: str
    payload: bytes


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("fact mapping keys must be strings")
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("fact float values must be finite")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported fact value: {type(value).__name__}")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _preflight(
    command: FactCreationCommand,
    object_id: str,
    now: str,
) -> tuple[dict[str, Any], str, tuple[FactIssue, ...], bool]:
    layout = LAYOUTS[command.fact_type_key]
    fields = {
        **_thaw_json(command.supplied),
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


def prepare_fact_creation(
    command: FactCreationCommand,
    *,
    observed_at: str | None = None,
) -> PreparedFactCreation | FactCreationResult:
    """Perform side-effect-free checks required before taking the allocation lock."""

    try:
        supplied = _freeze_json(command.supplied)
    except (TypeError, ValueError):
        return FactCreationResult(
            "candidate_rejected",
            issues=(FactIssue("schema", "事实对象包含不可冻结的非 JSON/YAML 值"),),
        )
    snapshot = FactCreationCommand(
        boundary=command.boundary,
        fact_type_key=command.fact_type_key,
        schemas=MappingProxyType(dict(command.schemas)),
        schema=command.schema,
        requested_candidate_id=command.requested_candidate_id,
        supplied=supplied,
        body=command.body,
    )
    now = observed_at if observed_at is not None else datetime.now().astimezone().isoformat()
    _, _, candidate_issues, candidate_unavailable = _preflight(snapshot, snapshot.requested_candidate_id, now)
    if candidate_unavailable:
        return FactCreationResult("candidate_unavailable", issues=candidate_issues)
    if candidate_issues:
        return FactCreationResult("candidate_rejected", issues=candidate_issues)
    if not durable_writes_enabled():
        return FactCreationResult("durability_unavailable")
    return PreparedFactCreation(snapshot, now)


def preview_fact_creation_locked(
    prepared: PreparedFactCreation,
    counter_path: Path,
) -> PreparedFactCreationAttempt | FactCreationResult:
    """Preview the exact final identity and bytes without mutating allocator or fact state."""

    command = prepared.command
    allocation = preview_object_id_locked(command.boundary, LAYOUTS[command.fact_type_key], counter_path)
    if allocation is None:
        return FactCreationResult("allocation_unavailable", allocation_status="unavailable")
    fields, text, issues, unavailable = _preflight(command, allocation.object_id, prepared.observed_at)
    if issues or unavailable:
        return FactCreationResult(
            "attempt_unavailable" if unavailable else "attempt_rejected",
            issues=issues,
            actual_id=allocation.object_id,
        )
    return PreparedFactCreationAttempt(
        prepared,
        allocation,
        _freeze_json(fields),
        text,
        text.encode("utf-8"),
    )


def _complete_created_fact(
    prepared: PreparedFactCreation,
    actual_id: str,
    actual_fields: dict[str, Any],
    actual_text: str,
    creation_result: AtomicWriteResult,
) -> FactCreationResult:
    command = prepared.command
    layout = LAYOUTS[command.fact_type_key]
    read = read_fact_object(
        command.boundary.worktree_root,
        layout,
        command.schema,
        actual_id,
        expected_common_dir=command.boundary.git_common_dir,
    )
    post_issues: tuple[FactIssue, ...] = ()
    post_unavailable = False
    if read.check_status == "mechanically_valid" and read.fields is not None and read.raw_text == actual_text:
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
    elif read.check_status == "mechanically_valid":
        post_issues = (FactIssue("parse", "写后回读 bytes 与本次创建 payload 不一致"),)
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


def commit_fact_creation_attempt_locked(attempt: PreparedFactCreationAttempt) -> FactCreationResult:
    """Commit one exact preview, publish it no-overwrite, and verify its exact bytes."""

    command = attempt.prepared.command
    layout = LAYOUTS[command.fact_type_key]
    allocation = commit_object_id_locked(command.boundary, layout, attempt.allocation)
    if allocation.status == "stale":
        return FactCreationResult("allocation_stale", allocation_status="stale")
    if allocation.status != "committed" or allocation.object_id != attempt.allocation.object_id:
        return FactCreationResult("allocation_unavailable", allocation_status=allocation.status)
    created = atomic_create_text(command.boundary.worktree_root, layout, allocation.object_id, attempt.text)
    if created.outcome == "conflict" and created.namespace_state == "not_committed":
        return FactCreationResult(
            "creation_conflict",
            actual_id=allocation.object_id,
            allocation_consumed=True,
            creation_result=created,
        )
    if created.outcome != "created" or created.namespace_state != "committed":
        return FactCreationResult(
            "allocation_unavailable",
            actual_id=allocation.object_id,
            allocation_consumed=True,
            creation_result=created,
            allocation_status=("uncertain" if created.namespace_state == "uncertain" else "unavailable"),
        )
    return _complete_created_fact(
        attempt.prepared,
        allocation.object_id,
        _thaw_json(attempt.fields),
        attempt.text,
        created,
    )


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

    assert creation_result is not None
    return _complete_created_fact(prepared, actual_id, actual_fields, actual_text, creation_result)


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
    "PreparedFactCreationAttempt",
    "commit_fact_creation_attempt_locked",
    "create_fact_object",
    "create_fact_object_locked",
    "preview_fact_creation_locked",
    "prepare_fact_creation",
]
