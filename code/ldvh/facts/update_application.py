"""Helper-independent transaction for one controlled fact-object replacement."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, allocation_lock, serialize_fact_object
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.transitions import is_workcase_progress_correction, validate_fact_transition
from ldvh.facts.update import atomic_replace_text_if_unchanged
from ldvh.facts.validation import parse_rfc3339, validate_fact_object
from ldvh.filesystem import AtomicWriteResult, durable_writes_enabled

UpdateStatus = Literal[
    "durability_unavailable",
    "current_rejected",
    "current_unavailable",
    "fingerprint_stale",
    "no_change",
    "event_time_not_successor",
    "candidate_rejected",
    "candidate_unavailable",
    "replacement_conflict",
    "replacement_unavailable",
    "readback_failed",
    "updated",
]

MANAGED_FIELDS = frozenset({"object_id", "fact_type_key", "created_at", "updated_at"})


@dataclass(frozen=True, slots=True)
class FactUpdateCommand:
    """One exact desired state bound to a previously observed fact snapshot."""

    boundary: CreationBoundary
    fact_type_key: str
    object_id: str
    schemas: Mapping[str, FactSchema]
    schema: FactSchema
    expected_content_fingerprint: str
    supplied: Mapping[str, Any]
    body: str | None
    event_at: str
    allow_workcase_progress_mutation: bool = False


@dataclass(frozen=True, slots=True)
class FactUpdateResult:
    status: UpdateStatus
    event_at: str
    issues: tuple[FactIssue, ...] = ()
    current: FactReadResult | None = None
    candidate: FactReadResult | None = None
    readback: FactReadResult | None = None
    candidate_text: str | None = None
    replacement_result: AtomicWriteResult | None = None
    rollback_result: AtomicWriteResult | None = None


def _project_read(command: FactUpdateCommand) -> FactReadResult:
    layout = LAYOUTS[command.fact_type_key]
    read = read_fact_object(
        command.boundary.worktree_root,
        layout,
        command.schema,
        command.object_id,
        expected_common_dir=command.boundary.git_common_dir,
    )
    if read.check_status == "unavailable" or read.fields is None:
        return read
    if read.check_status != "mechanically_valid":
        return read
    index = ProjectFactIndex(
        command.boundary.worktree_root,
        command.boundary.governed_project_id,
        dict(command.schemas),
        command.boundary.git_common_dir,
    )
    key = (command.fact_type_key, command.object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index)
    return index.cache.get(key, read)


def _candidate(
    command: FactUpdateCommand,
    before: dict[str, Any],
    *,
    repairing_invalid_before: bool,
) -> tuple[FactReadResult, str]:
    layout = LAYOUTS[command.fact_type_key]
    fields = {
        **dict(command.supplied),
        "object_id": before["object_id"],
        "fact_type_key": before["fact_type_key"],
        "created_at": before["created_at"],
        "updated_at": command.event_at,
    }
    text = serialize_fact_object(layout, fields, command.body)
    parsed = parse_study_markdown(text) if layout.carrier == "markdown" else parse_yaml_object(text)
    issues = list(parsed.issues)
    if parsed.fields is not None:
        issues.extend(validate_fact_object(command.fact_type_key, parsed.fields, command.schema))
        if (
            command.fact_type_key == "workcase"
            and before.get("workcase_profile") == "control-contract-v1"
            and before.get("progress_history") != parsed.fields.get("progress_history")
            and not command.allow_workcase_progress_mutation
            and not is_workcase_progress_correction(before, parsed.fields)
        ):
            issues.append(
                FactIssue(
                    "schema",
                    "current WorkCase 的 progress_history 只能由 update-workcase 托管追加，或按稳定 event_id 原位更正",
                    "progress_history",
                )
            )
        issues.extend(
            validate_fact_transition(
                command.fact_type_key,
                before,
                parsed.fields,
                repairing_invalid_before=repairing_invalid_before,
            )
        )
    read = FactReadResult(
        layout.canonical_path(command.object_id),
        layout.carrier,
        "invalid" if issues or parsed.fields is None else "mechanically_valid",
        parsed.fields,
        parsed.body,
        tuple(issues),
        raw_text=text,
        raw_byte_count=len(text.encode("utf-8")),
    )
    if read.check_status != "mechanically_valid" or read.fields is None:
        return read, text
    index = ProjectFactIndex(
        command.boundary.worktree_root,
        command.boundary.governed_project_id,
        dict(command.schemas),
        command.boundary.git_common_dir,
    )
    key = (command.fact_type_key, command.object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index)
    return index.cache.get(key, read), text


def _event_time_issue(current: FactReadResult, event_at: str) -> FactIssue | None:
    assert current.fields is not None
    before = parse_rfc3339(current.fields.get("updated_at"))
    event = parse_rfc3339(event_at)
    if before is None or event is None or event <= before:
        return FactIssue("schema", "event_at 必须严格晚于当前 updated_at", "updated_at")
    return None


def apply_fact_update_locked(command: FactUpdateCommand) -> FactUpdateResult:
    """Apply one update while the caller holds the fact type's common-dir lock."""

    current = _project_read(command)
    if current.check_status == "unavailable" or current.fields is None:
        status: UpdateStatus = "current_unavailable" if current.check_status == "unavailable" else "current_rejected"
        return FactUpdateResult(status, command.event_at, issues=current.issues, current=current)
    if current.check_status != "mechanically_valid" and current.content_fingerprint is None:
        return FactUpdateResult("current_rejected", command.event_at, issues=current.issues, current=current)
    if current.content_fingerprint != command.expected_content_fingerprint or current.raw_text is None:
        return FactUpdateResult("fingerprint_stale", command.event_at, current=current)

    layout = LAYOUTS[command.fact_type_key]
    mutable_current = {key: value for key, value in current.fields.items() if key not in MANAGED_FIELDS}
    repairing_invalid_before = current.check_status != "mechanically_valid"
    if (
        not repairing_invalid_before
        and mutable_current == dict(command.supplied)
        and (layout.carrier != "markdown" or (current.body or "") == command.body)
    ):
        return FactUpdateResult("no_change", command.event_at, current=current, readback=current)

    time_issue = _event_time_issue(current, command.event_at)
    if time_issue is not None:
        return FactUpdateResult(
            "event_time_not_successor",
            command.event_at,
            issues=(time_issue,),
            current=current,
        )

    candidate, candidate_text = _candidate(
        command,
        current.fields,
        repairing_invalid_before=repairing_invalid_before,
    )
    if candidate.check_status != "mechanically_valid":
        status = "candidate_unavailable" if candidate.check_status == "unavailable" else "candidate_rejected"
        return FactUpdateResult(
            status,
            command.event_at,
            issues=candidate.issues,
            current=current,
            candidate=candidate,
            candidate_text=candidate_text,
        )

    replacement = atomic_replace_text_if_unchanged(
        command.boundary.worktree_root,
        layout,
        command.object_id,
        current.raw_text,
        candidate_text,
    )
    if replacement.outcome != "replaced" or replacement.namespace_state != "committed":
        status = "replacement_conflict" if replacement.outcome == "conflict" else "replacement_unavailable"
        return FactUpdateResult(
            status,
            command.event_at,
            current=current,
            candidate=candidate,
            candidate_text=candidate_text,
            replacement_result=replacement,
        )

    readback = _project_read(command)
    readback_issues = readback.issues
    if readback.check_status == "mechanically_valid" and readback.raw_text != candidate_text:
        readback_issues = (*readback_issues, FactIssue("parse", "写后回读 bytes 与本次更新 payload 不一致"))
    if readback.check_status != "mechanically_valid" or readback.fields is None or readback.raw_text != candidate_text:
        rollback = atomic_replace_text_if_unchanged(
            command.boundary.worktree_root,
            layout,
            command.object_id,
            candidate_text,
            current.raw_text,
        )
        return FactUpdateResult(
            "readback_failed",
            command.event_at,
            issues=readback_issues,
            current=current,
            candidate=candidate,
            readback=readback,
            candidate_text=candidate_text,
            replacement_result=replacement,
            rollback_result=rollback,
        )
    return FactUpdateResult(
        "updated",
        command.event_at,
        current=current,
        candidate=candidate,
        readback=readback,
        candidate_text=candidate_text,
        replacement_result=replacement,
    )


def apply_fact_update(command: FactUpdateCommand) -> FactUpdateResult:
    """Validate, lock, CAS-replace, read back, and conditionally roll back one fact."""

    if not durable_writes_enabled():
        return FactUpdateResult("durability_unavailable", command.event_at)
    layout = LAYOUTS[command.fact_type_key]
    with allocation_lock(command.boundary, layout):
        return apply_fact_update_locked(command)


__all__ = [
    "MANAGED_FIELDS",
    "FactUpdateCommand",
    "FactUpdateResult",
    "UpdateStatus",
    "apply_fact_update",
    "apply_fact_update_locked",
]
