"""Controlled bootstrap of a trusted change-log entry for one legacy object."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, allocation_lock, serialize_fact_object
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.transitions import validate_fact_transition
from ldvh.facts.update import atomic_replace_text_if_unchanged
from ldvh.facts.validation import parse_rfc3339, validate_fact_object
from ldvh.filesystem import AtomicWriteResult, native_atomic_fact_writes_supported
from ldvh.time import canonicalize_new_timestamp_fields

MigrationStatus = Literal[
    "current_unavailable",
    "current_rejected",
    "fingerprint_stale",
    "change_log_present",
    "candidate_rejected",
    "replacement_conflict",
    "replacement_unavailable",
    "readback_failed",
    "updated",
]

MANAGED_FIELDS = frozenset({"object_id", "fact_type_key", "created_at", "updated_at"})


@dataclass(frozen=True, slots=True)
class LegacyChangeLogMigrationCommand:
    boundary: CreationBoundary
    fact_type_key: str
    object_id: str
    schemas: Mapping[str, FactSchema]
    schema: FactSchema
    expected_content_fingerprint: str
    migration_signature: Mapping[str, str]
    migration_summary: str
    event_at: str


@dataclass(frozen=True, slots=True)
class LegacyChangeLogMigrationResult:
    status: MigrationStatus
    event_at: str
    issues: tuple[FactIssue, ...] = ()
    current: FactReadResult | None = None
    readback: FactReadResult | None = None
    candidate: FactReadResult | None = None
    candidate_text: str | None = None
    replacement_result: AtomicWriteResult | None = None
    rollback_result: AtomicWriteResult | None = None
    residual_readback: FactReadResult | None = None


def _project_read(command: LegacyChangeLogMigrationCommand) -> FactReadResult:
    layout = LAYOUTS[command.fact_type_key]
    read = read_fact_object(
        command.boundary.worktree_root,
        layout,
        command.schema,
        command.object_id,
        expected_common_dir=command.boundary.git_common_dir,
    )
    if read.check_status != "mechanically_valid" or read.fields is None:
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
    stabilize_project_index(index, (key,))
    return index.cache.get(key, read)


def _event_time_issue(current: FactReadResult, event_at: str) -> FactIssue | None:
    assert current.fields is not None
    before = parse_rfc3339(current.fields.get("updated_at"))
    event = parse_rfc3339(event_at)
    if before is None or event is None or event <= before:
        return FactIssue("schema", "migration event_at 必须严格晚于当前 updated_at", "updated_at")
    return None


def _candidate(
    command: LegacyChangeLogMigrationCommand,
    current_read: FactReadResult,
) -> tuple[FactReadResult, str]:
    assert current_read.fields is not None
    layout = LAYOUTS[command.fact_type_key]
    current = current_read.fields
    fields = dict(current)
    fields["updated_at"] = command.event_at
    fields["change_log"] = [
        {
            "signature": {
                "agent_id": command.migration_signature["agent_id"],
                "host_environment": command.migration_signature["host_environment"],
            },
            "session_id": command.migration_signature["session_id"],
            "at": command.event_at,
            "summary": command.migration_summary,
        }
    ]
    fields = canonicalize_new_timestamp_fields(fields, before=current)
    text = serialize_fact_object(
        layout,
        fields,
        current_read.body if layout.carrier == "markdown" else None,
    )
    parsed = parse_study_markdown(text) if layout.carrier == "markdown" else parse_yaml_object(text)
    issues = list(parsed.issues)
    if parsed.fields is not None:
        issues.extend(validate_fact_object(command.fact_type_key, parsed.fields, command.schema))
        issues.extend(validate_fact_transition(command.fact_type_key, dict(current), parsed.fields))
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
    stabilize_project_index(index, (key,))
    return index.cache.get(key, read), text


def apply_legacy_change_log_migration_locked(
    command: LegacyChangeLogMigrationCommand,
) -> LegacyChangeLogMigrationResult:
    current = _project_read(command)
    if current.check_status != "mechanically_valid" or current.fields is None:
        status: MigrationStatus = "current_unavailable" if current.check_status == "unavailable" else "current_rejected"
        return LegacyChangeLogMigrationResult(status, command.event_at, issues=current.issues, current=current)
    if current.content_fingerprint != command.expected_content_fingerprint or current.raw_text is None:
        return LegacyChangeLogMigrationResult("fingerprint_stale", command.event_at, current=current)
    if "change_log" in current.fields:
        return LegacyChangeLogMigrationResult("change_log_present", command.event_at, current=current)
    event_issue = _event_time_issue(current, command.event_at)
    if event_issue is not None:
        return LegacyChangeLogMigrationResult(
            "candidate_rejected", command.event_at, issues=(event_issue,), current=current
        )

    candidate, candidate_text = _candidate(command, current)
    if candidate.check_status != "mechanically_valid":
        return LegacyChangeLogMigrationResult(
            "candidate_rejected",
            command.event_at,
            issues=candidate.issues,
            current=current,
            candidate=candidate,
            candidate_text=candidate_text,
        )
    replacement = atomic_replace_text_if_unchanged(
        command.boundary.worktree_root,
        LAYOUTS[command.fact_type_key],
        command.object_id,
        current.raw_text,
        candidate_text,
    )
    if replacement.namespace_state != "committed" or replacement.outcome != "replaced":
        status = "replacement_conflict" if replacement.outcome == "conflict" else "replacement_unavailable"
        return LegacyChangeLogMigrationResult(
            status,
            command.event_at,
            current=current,
            candidate=candidate,
            candidate_text=candidate_text,
            replacement_result=replacement,
        )

    readback = _project_read(command)
    if readback.check_status == "mechanically_valid" and readback.raw_text == candidate_text:
        return LegacyChangeLogMigrationResult(
            "updated",
            command.event_at,
            current=current,
            candidate=candidate,
            candidate_text=candidate_text,
            replacement_result=replacement,
            readback=readback,
        )

    rollback = atomic_replace_text_if_unchanged(
        command.boundary.worktree_root,
        LAYOUTS[command.fact_type_key],
        command.object_id,
        candidate_text,
        current.raw_text,
    )
    residual = (
        None if rollback.outcome == "replaced" and rollback.namespace_state == "committed" else _project_read(command)
    )
    return LegacyChangeLogMigrationResult(
        "readback_failed",
        command.event_at,
        issues=readback.issues,
        current=current,
        candidate=candidate,
        candidate_text=candidate_text,
        replacement_result=replacement,
        rollback_result=rollback,
        residual_readback=residual,
        readback=readback,
    )


def apply_legacy_change_log_migration(
    command: LegacyChangeLogMigrationCommand,
) -> LegacyChangeLogMigrationResult:
    if not native_atomic_fact_writes_supported():
        return LegacyChangeLogMigrationResult("replacement_unavailable", command.event_at)
    try:
        with allocation_lock(command.boundary, LAYOUTS[command.fact_type_key]):
            return apply_legacy_change_log_migration_locked(command)
    except OSError:
        return LegacyChangeLogMigrationResult("replacement_unavailable", command.event_at)


__all__ = [
    "LegacyChangeLogMigrationCommand",
    "LegacyChangeLogMigrationResult",
    "apply_legacy_change_log_migration",
    "apply_legacy_change_log_migration_locked",
]
