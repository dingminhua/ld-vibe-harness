"""Helper-independent application transaction for controlled fact creation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.configuration_index import ConfigurationFactIndex
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    CreationBoundary,
    atomic_create_text,
    fact_write_lock,
    rollback_created_text,
    serialize_fact_object,
)
from ldvh.facts.identity import generate_object_uid, locator_from_object_uid
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex, validate_project_relations
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import (
    change_log_creation_issues,
    study_report_creation_issues,
    timestamp_initial_change_log,
    validate_fact_object,
)
from ldvh.facts.workcase_validation import required_quality_gate_issues
from ldvh.filesystem import AtomicWriteResult, native_atomic_fact_writes_supported
from ldvh.time import canonical_utc_timestamp, canonicalize_new_timestamp_fields, utc_now_iso

CreationStatus = Literal[
    "candidate_rejected",
    "candidate_unavailable",
    "durability_unavailable",
    "final_rejected",
    "final_unavailable",
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
    supplied: Mapping[str, Any]
    body: str | None
    configuration_boundaries: tuple[tuple[str, Path, Path], ...] = ()


@dataclass(frozen=True, slots=True)
class FactCreationResult:
    status: CreationStatus
    issues: tuple[FactIssue, ...] = ()
    actual_id: str | None = None
    actual_fields: dict[str, Any] | None = None
    actual_text: str | None = None
    read: FactReadResult | None = None
    creation_result: AtomicWriteResult | None = None
    rollback_result: AtomicWriteResult | None = None
    residual_readback: FactReadResult | None = None
    coordination_release_uncertain: bool = False
    attempted_object_uid: str | None = None


@dataclass(frozen=True, slots=True)
class PreparedFactCreation:
    command: FactCreationCommand
    observed_at: str
    object_uid: str


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
    change_log_issues = change_log_creation_issues(fields)
    if fact_type_key == "study":
        return (*change_log_issues, *study_report_creation_issues(fields))
    if fact_type_key != "workcase":
        return change_log_issues
    issues: list[FactIssue] = [*change_log_issues]
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
    issues.extend(required_quality_gate_issues(fields))
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
    object_uid: str,
) -> tuple[dict[str, Any], str, tuple[FactIssue, ...], bool]:
    layout = LAYOUTS[command.fact_type_key]
    fields = {
        **_thaw_json(command.supplied),
        "object_uid": object_uid,
        "object_id": object_id,
        "fact_type_key": command.fact_type_key,
        "created_at": now,
        "updated_at": now,
    }
    timestamp_initial_change_log(fields, now)
    fields = canonicalize_new_timestamp_fields(fields)
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
    """Perform side-effect-free checks required before taking the creation lock."""

    try:
        supplied = _freeze_json(command.supplied)
    except (TypeError, ValueError):
        return FactCreationResult(
            "candidate_rejected",
            issues=(FactIssue("schema", "事实对象包含不可冻结的非 JSON/YAML 值"),),
        )
    managed = sorted(set(supplied) & {"object_uid", "object_id", "fact_type_key", "created_at", "updated_at"})
    if managed:
        return FactCreationResult(
            "candidate_rejected",
            issues=(FactIssue("schema", f"调用方不得填写 Code 托管字段: {', '.join(managed)}"),),
        )
    snapshot = FactCreationCommand(
        boundary=command.boundary,
        fact_type_key=command.fact_type_key,
        schemas=MappingProxyType(dict(command.schemas)),
        schema=command.schema,
        supplied=supplied,
        body=command.body,
        configuration_boundaries=command.configuration_boundaries,
    )
    now = utc_now_iso() if observed_at is None else canonical_utc_timestamp(observed_at) or observed_at
    boundaries = snapshot.configuration_boundaries or (
        (
            snapshot.boundary.governed_project_id,
            snapshot.boundary.worktree_root,
            snapshot.boundary.git_common_dir,
        ),
    )
    uid_index = ConfigurationFactIndex(boundaries, dict(snapshot.schemas))
    object_uid: str | None = None
    for _attempt in range(3):
        try:
            candidate_uid = generate_object_uid()
        except (OSError, RuntimeError, ValueError):
            return FactCreationResult(
                "candidate_unavailable",
                issues=(FactIssue("resource", "无法生成 UUIDv7 object_uid", "object_uid"),),
            )
        _existing, uid_status = uid_index.resolve_uid(candidate_uid)
        if uid_status == "not_found":
            object_uid = candidate_uid
            break
        if uid_status == "unavailable":
            return FactCreationResult(
                "candidate_unavailable",
                issues=(FactIssue("resource", "配置级 UID 全扫描未能完整形成", "object_uid"),),
            )
        if uid_status not in {"resolved", "duplicate"}:
            return FactCreationResult(
                "candidate_unavailable",
                issues=(FactIssue("identity", "生成的 object_uid 未形成合法配置级唯一性候选", "object_uid"),),
            )
    if object_uid is None:
        return FactCreationResult(
            "candidate_unavailable",
            issues=(FactIssue("identity", "连续三次生成的 object_uid 均与配置内既有对象重复", "object_uid"),),
        )
    candidate_id = locator_from_object_uid(snapshot.fact_type_key, object_uid)
    _, _, candidate_issues, candidate_unavailable = _preflight(
        snapshot,
        candidate_id,
        now,
        object_uid,
    )
    if candidate_unavailable:
        return FactCreationResult("candidate_unavailable", issues=candidate_issues)
    if candidate_issues:
        return FactCreationResult("candidate_rejected", issues=candidate_issues)
    if not native_atomic_fact_writes_supported():
        return FactCreationResult("durability_unavailable")
    return PreparedFactCreation(snapshot, now, object_uid)


def _complete_created_fact(
    prepared: PreparedFactCreation,
    actual_id: str,
    actual_fields: dict[str, Any],
    actual_text: str,
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
            creation_result=creation_result,
            rollback_result=rollback,
            residual_readback=residual_readback,
        )
    return FactCreationResult(
        "created",
        actual_id=actual_id,
        actual_fields=actual_fields,
        actual_text=actual_text,
        read=read,
        creation_result=creation_result,
    )


def create_fact_object_locked(prepared: PreparedFactCreation) -> FactCreationResult:
    """Perform one UID-locator creation and one target no-overwrite attempt."""

    command = prepared.command
    now = prepared.observed_at
    layout = LAYOUTS[command.fact_type_key]
    actual_id = locator_from_object_uid(command.fact_type_key, prepared.object_uid)
    actual_fields, actual_text, issues, unavailable = _preflight(
        command,
        actual_id,
        now,
        prepared.object_uid,
    )
    if issues or unavailable:
        return FactCreationResult(
            "final_unavailable" if unavailable else "final_rejected",
            issues=issues,
            actual_id=actual_id,
            actual_fields=actual_fields,
            actual_text=actual_text,
        )

    creation_result = atomic_create_text(command.boundary.worktree_root, layout, actual_id, actual_text)
    if creation_result.outcome == "created" and creation_result.namespace_state == "committed":
        return _complete_created_fact(
            prepared,
            actual_id,
            actual_fields,
            actual_text,
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
        creation_result=creation_result,
        residual_readback=residual_readback,
    )


def create_fact_object(command: FactCreationCommand, *, observed_at: str | None = None) -> FactCreationResult:
    """Validate, create, read back, and conditionally roll back one fact."""

    prepared = prepare_fact_creation(command, observed_at=observed_at)
    if isinstance(prepared, FactCreationResult):
        return prepared
    layout = LAYOUTS[command.fact_type_key]
    completed: FactCreationResult | None = None
    try:
        with fact_write_lock(command.boundary, layout):
            completed = create_fact_object_locked(prepared)
    except OSError:
        if completed is None:
            raise
        return replace(
            completed,
            coordination_release_uncertain=True,
            attempted_object_uid=prepared.object_uid,
        )
    assert completed is not None
    return replace(completed, attempted_object_uid=prepared.object_uid)


__all__ = [
    "CreationStatus",
    "FactCreationCommand",
    "FactCreationResult",
    "PreparedFactCreation",
    "create_fact_object",
    "create_fact_object_locked",
    "prepare_fact_creation",
]
