"""Helper-independent application transaction for controlled fact creation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    AllocationCommitResult,
    CreationBoundary,
    allocation_lock,
    atomic_create_text,
    commit_object_id_locked,
    preview_object_id_locked,
    rollback_created_text,
    serialize_fact_object,
)
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex, validate_project_relations
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import validate_fact_object
from ldvh.filesystem import AtomicWriteResult, durable_writes_enabled

CreationStatus = Literal[
    "candidate_rejected",
    "candidate_unavailable",
    "durability_unavailable",
    "final_rejected",
    "final_unavailable",
    "allocation_stale",
    "allocation_unavailable",
    "creation_conflict",
    "creation_unavailable",
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
    allocation_consumed: bool | None = False
    creation_result: AtomicWriteResult | None = None
    rollback_result: AtomicWriteResult | None = None
    residual_readback: FactReadResult | None = None
    allocation_status: str | None = None
    allocation_result: AllocationCommitResult | None = None
    coordination_release_uncertain: bool = False


@dataclass(frozen=True, slots=True)
class PreparedFactCreation:
    command: FactCreationCommand
    observed_at: str


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


def _creation_context_issues(fact_type_key: str, fields: Mapping[str, Any]) -> tuple[FactIssue, ...]:
    if fact_type_key != "workcase":
        return ()
    issues: list[FactIssue] = []
    if fields.get("status") != "open":
        issues.append(FactIssue("schema", "新建 WorkCase 的初始 status 必须是 open", "status"))
    if fields.get("phase") != "human_plan_confirming":
        issues.append(FactIssue("schema", "新建 WorkCase 的初始 phase 必须是 human_plan_confirming", "phase"))
    if fields.get("plan_version") != 1:
        issues.append(FactIssue("schema", "新建 WorkCase 的初始 plan_version 必须是 1", "plan_version"))
    work_items = fields.get("work_items")
    if isinstance(work_items, list) and any(
        not isinstance(item, Mapping) or item.get("status") != "pending" for item in work_items
    ):
        issues.append(FactIssue("schema", "新建 WorkCase 的全部 work item 必须是 pending", "work_items"))
    if "execution_approval" in fields:
        issues.append(FactIssue("schema", "新建 WorkCase 禁止预置 execution_approval", "execution_approval"))
    return tuple(issues)


def _stabilized_project_relation_check(
    command: FactCreationCommand,
    object_id: str,
    read: FactReadResult,
) -> tuple[tuple[FactIssue, ...], bool]:
    """Validate the candidate and its relation closure against one stable project view.

    Stabilization is required before accepting the candidate: a direct target can
    be locally schema-valid while becoming project-invalid because one of its own
    required targets is missing or invalid.  A mechanically-valid candidate after
    stabilization therefore also confirms that every direct target consumed by
    its relation checks is mechanically valid in that same project view.
    """

    index = ProjectFactIndex(
        command.boundary.worktree_root,
        command.boundary.governed_project_id,
        command.schemas,
        command.boundary.git_common_dir,
    )
    key = (command.fact_type_key, object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index, (key,))
    stabilized = index.cache.get(key)
    if stabilized is None:
        return (FactIssue("reference", "项目级关系检查未返回当前候选的稳定检查结果"),), True
    if stabilized.check_status == "unavailable":
        return stabilized.issues, True
    if stabilized.check_status != "mechanically_valid":
        return stabilized.issues, False

    # Re-run the direct-edge check against the stabilized cache.  This makes the
    # acceptance condition explicit instead of relying only on an earlier
    # iteration in which a target may still have looked locally valid.
    return validate_project_relations(index, command.fact_type_key, object_id, stabilized)


def _project_read(command: FactCreationCommand, object_id: str) -> FactReadResult:
    """Read one created identity through the current project-level mechanical boundary."""

    layout = LAYOUTS[command.fact_type_key]
    read = read_fact_object(
        command.boundary.worktree_root,
        layout,
        command.schema,
        object_id,
        expected_common_dir=command.boundary.git_common_dir,
    )
    if read.check_status != "mechanically_valid" or read.fields is None:
        return read
    relation_issues, relation_unavailable = _stabilized_project_relation_check(
        command,
        object_id,
        read,
    )
    if relation_unavailable:
        return replace(
            read,
            check_status="unavailable",
            issues=(*read.issues, *relation_issues),
        )
    if relation_issues:
        return replace(
            read,
            check_status="invalid",
            issues=(*read.issues, *relation_issues),
        )
    return read


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
    issues.extend(_creation_context_issues(command.fact_type_key, parsed.fields))
    if issues:
        return fields, text, tuple(issues), False
    read = FactReadResult(
        layout.canonical_path(object_id), layout.carrier, "mechanically_valid", parsed.fields, parsed.body, ()
    )
    relation_issues, relation_unavailable = _stabilized_project_relation_check(command, object_id, read)
    return fields, text, relation_issues, relation_unavailable


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


def _complete_created_fact(
    prepared: PreparedFactCreation,
    actual_id: str,
    actual_fields: dict[str, Any],
    actual_text: str,
    allocation_result: AllocationCommitResult,
    creation_result: AtomicWriteResult,
) -> FactCreationResult:
    command = prepared.command
    layout = LAYOUTS[command.fact_type_key]
    read = _project_read(command, actual_id)
    readback_issues = read.issues
    if read.check_status == "mechanically_valid" and read.raw_text != actual_text:
        readback_issues = (*readback_issues, FactIssue("parse", "写后回读 bytes 与本次创建 payload 不一致"))
    if read.check_status != "mechanically_valid" or read.fields is None or read.raw_text != actual_text:
        rollback = rollback_created_text(command.boundary.worktree_root, layout, actual_id, actual_text)
        rolled_back = rollback.outcome == "removed" and rollback.namespace_state == "committed"
        residual_readback = None if rolled_back else _project_read(command, actual_id)
        return FactCreationResult(
            "readback_failed",
            issues=readback_issues,
            actual_id=actual_id,
            actual_fields=actual_fields,
            actual_text=actual_text,
            read=read,
            allocation_consumed=True,
            creation_result=creation_result,
            rollback_result=rollback,
            residual_readback=residual_readback,
            allocation_status="committed",
            allocation_result=allocation_result,
        )
    return FactCreationResult(
        "created",
        actual_id=actual_id,
        actual_fields=actual_fields,
        actual_text=actual_text,
        read=read,
        allocation_consumed=True,
        creation_result=creation_result,
        allocation_status="committed",
        allocation_result=allocation_result,
    )


def create_fact_object_locked(prepared: PreparedFactCreation, counter_path: Path) -> FactCreationResult:
    """Perform the public creation call's single allocation and target attempt."""

    command = prepared.command
    now = prepared.observed_at
    layout = LAYOUTS[command.fact_type_key]
    preview = preview_object_id_locked(command.boundary, layout, counter_path)
    if preview is None:
        return FactCreationResult(
            "allocation_unavailable",
            allocation_status="unavailable",
        )

    allocation = commit_object_id_locked(command.boundary, layout, preview)
    if allocation.status in {"stale", "unavailable"} and allocation.write_result is None:
        return FactCreationResult(
            "allocation_stale" if allocation.status == "stale" else "allocation_unavailable",
            allocation_consumed=False,
            allocation_status=allocation.status,
            allocation_result=allocation,
        )
    if allocation.status == "stale":
        return FactCreationResult(
            "allocation_stale",
            actual_id=preview.object_id,
            allocation_consumed=False,
            allocation_status="stale",
            allocation_result=allocation,
        )
    if allocation.status == "committed" and allocation.object_id != preview.object_id:
        allocation = AllocationCommitResult("uncertain", None, allocation.write_result)
    if allocation.status != "committed":
        residual_readback = _project_read(command, preview.object_id) if allocation.status == "uncertain" else None
        return FactCreationResult(
            "allocation_unavailable",
            actual_id=preview.object_id,
            allocation_consumed=None if allocation.status == "uncertain" else False,
            residual_readback=residual_readback,
            allocation_status=allocation.status,
            allocation_result=allocation,
        )

    actual_id = allocation.object_id
    actual_fields, actual_text, issues, unavailable = _preflight(command, actual_id, now)
    if issues or unavailable:
        return FactCreationResult(
            "final_unavailable" if unavailable else "final_rejected",
            issues=issues,
            actual_id=actual_id,
            actual_fields=actual_fields,
            actual_text=actual_text,
            allocation_consumed=True,
            allocation_status="committed",
            allocation_result=allocation,
        )

    creation_result = atomic_create_text(command.boundary.worktree_root, layout, actual_id, actual_text)
    if creation_result.outcome == "created" and creation_result.namespace_state == "committed":
        return _complete_created_fact(
            prepared,
            actual_id,
            actual_fields,
            actual_text,
            allocation,
            creation_result,
        )

    residual_readback = _project_read(command, actual_id)
    return FactCreationResult(
        "creation_conflict"
        if creation_result.outcome == "conflict" and creation_result.namespace_state == "not_committed"
        else "creation_unavailable",
        actual_id=actual_id,
        actual_fields=actual_fields,
        actual_text=actual_text,
        allocation_consumed=True,
        creation_result=creation_result,
        residual_readback=residual_readback,
        allocation_status="committed",
        allocation_result=allocation,
    )


def create_fact_object(command: FactCreationCommand, *, observed_at: str | None = None) -> FactCreationResult:
    """Validate, allocate, create, read back, and conditionally roll back one fact."""

    prepared = prepare_fact_creation(command, observed_at=observed_at)
    if isinstance(prepared, FactCreationResult):
        return prepared
    layout = LAYOUTS[command.fact_type_key]
    completed: FactCreationResult | None = None
    try:
        with allocation_lock(command.boundary, layout) as counter_path:
            completed = create_fact_object_locked(prepared, counter_path)
    except OSError:
        if completed is None:
            raise
        return replace(completed, coordination_release_uncertain=True)
    assert completed is not None
    return completed


__all__ = [
    "CreationStatus",
    "FactCreationCommand",
    "FactCreationResult",
    "PreparedFactCreation",
    "create_fact_object",
    "create_fact_object_locked",
    "prepare_fact_creation",
]
