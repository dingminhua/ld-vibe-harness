"""Helper-independent transaction for one generic fact-object replacement.

WorkCase deliberately does not enter this generic path.  Its active update,
atomic close, and closed correction use the type-owned transaction in
``ldvh.facts.workcase_update``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any, Literal

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS, is_legacy_spark_object
from ldvh.facts.creation import CreationBoundary, fact_write_lock, serialize_fact_object
from ldvh.facts.head_change_log import head_change_log_state
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.transitions import validate_fact_transition
from ldvh.facts.update import atomic_replace_text_if_unchanged
from ldvh.facts.validation import (
    parse_rfc3339,
    study_report_creation_issues,
    timestamp_appended_change_log,
    validate_change_log_transition,
    validate_fact_object,
)
from ldvh.filesystem import AtomicWriteResult, native_atomic_fact_writes_supported
from ldvh.time import canonicalize_new_timestamp_fields

UpdateStatus = Literal[
    "invalid_request",
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

MANAGED_FIELDS = frozenset({"object_uid", "object_id", "fact_type_key", "created_at", "updated_at"})
STUDY_REPORT_CONTENT_FIELDS = frozenset({
    "report_kind",
    "input_refs",
    "urls",
    "relations",
    "research_question",
    "research_intent",
    "abstract",
    "recommendation_summary",
})


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
    allow_legacy_routed_spark_migration: bool = False


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
    residual_readback: FactReadResult | None = None
    coordination_release_uncertain: bool = False


def _workcase_rejection(event_at: str) -> FactUpdateResult:
    return FactUpdateResult(
        "invalid_request",
        event_at,
        issues=(
            FactIssue(
                "schema",
                ("通用 update-fact-object 不接受 WorkCase；活动期更新、关闭与终态更正必须分别使用 WorkCase 专属操作"),
                "fact_type_key",
            ),
        ),
    )


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
    stabilize_project_index(index, (key,))
    return index.cache.get(key, read)


def _candidate(
    command: FactUpdateCommand,
    before: dict[str, Any],
    *,
    repairing_invalid_before: bool,
    require_study_report_metadata: bool = False,
) -> tuple[FactReadResult, str]:
    layout = LAYOUTS[command.fact_type_key]
    fields = {
        **dict(command.supplied),
        **({"object_uid": before["object_uid"]} if "object_uid" in before else {}),
        "object_id": before["object_id"],
        "fact_type_key": before["fact_type_key"],
        "created_at": before["created_at"],
        "updated_at": command.event_at,
    }
    change_log = fields.get("change_log")
    if isinstance(change_log, list):
        # Stamp on a private copy so the caller-supplied mapping is never
        # mutated through the shallow spread above.
        fields["change_log"] = [dict(entry) if isinstance(entry, dict) else entry for entry in change_log]
    timestamp_appended_change_log(fields, command.event_at)
    fields = canonicalize_new_timestamp_fields(fields, before=before)
    text = serialize_fact_object(layout, fields, command.body)
    parsed = parse_study_markdown(text) if layout.carrier == "markdown" else parse_yaml_object(text)
    issues = list(parsed.issues)
    if parsed.fields is not None:
        issues.extend(validate_fact_object(command.fact_type_key, parsed.fields, command.schema))
        if command.fact_type_key == "study" and require_study_report_metadata:
            issues.extend(study_report_creation_issues(parsed.fields))
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
    stabilize_project_index(index, (key,))
    return index.cache.get(key, read), text


def _event_time_issue(current: FactReadResult, event_at: str) -> FactIssue | None:
    assert current.fields is not None
    before = parse_rfc3339(current.fields.get("updated_at"))
    event = parse_rfc3339(event_at)
    if before is None or event is None or event <= before:
        return FactIssue("schema", "event_at 必须严格晚于当前 updated_at", "updated_at")
    return None


def _normalized_mutable(fields: dict[str, Any]) -> dict[str, Any]:
    """Keep comparisons byte-semantic; historical signatures are read-only."""
    return fields


def apply_fact_update_locked(command: FactUpdateCommand) -> FactUpdateResult:
    """Apply one generic update while the caller holds the type lock."""

    if command.fact_type_key == "workcase":
        return _workcase_rejection(command.event_at)
    current = _project_read(command)
    if current.check_status == "unavailable" or current.fields is None:
        status: UpdateStatus = "current_unavailable" if current.check_status == "unavailable" else "current_rejected"
        return FactUpdateResult(status, command.event_at, issues=current.issues, current=current)
    if current.check_status != "mechanically_valid" and current.content_fingerprint is None:
        return FactUpdateResult("current_rejected", command.event_at, issues=current.issues, current=current)
    if (
        command.fact_type_key == "spark"
        and is_legacy_spark_object(command.object_id)
        and not command.allow_legacy_routed_spark_migration
        and current.fields is not None
        and current.fields.get("status") == "routed"
    ):
        return FactUpdateResult(
            "invalid_request",
            command.event_at,
            issues=(FactIssue("schema", "历史 routed Spark 仅允许只读审计，禁止 canonical write", "object_id"),),
            current=current,
        )
    if current.content_fingerprint != command.expected_content_fingerprint or current.raw_text is None:
        return FactUpdateResult("fingerprint_stale", command.event_at, current=current)

    layout = LAYOUTS[command.fact_type_key]
    mutable_current = {key: value for key, value in current.fields.items() if key not in MANAGED_FIELDS}
    repairing_invalid_before = current.check_status != "mechanically_valid"
    if (
        not repairing_invalid_before
        and _normalized_mutable(mutable_current) == _normalized_mutable(dict(command.supplied))
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

    allow_first_log = False
    if "change_log" not in current.fields:
        state = head_change_log_state(
            command.boundary.worktree_root,
            LAYOUTS[command.fact_type_key],
            command.schema,
            command.object_id,
        )
        if state != "absent":
            return FactUpdateResult(
                "candidate_rejected",
                command.event_at,
                issues=(
                    FactIssue(
                        "schema",
                        "HEAD 基线不是同样缺少 change_log 的机械有效 before；"
                        "历史被删除、新对象或不可用 HEAD 均不得首写",
                        "change_log",
                    ),
                ),
                current=current,
            )
        allow_first_log = True

    proposed = {
        **dict(command.supplied),
        **({"object_uid": current.fields["object_uid"]} if "object_uid" in current.fields else {}),
        "object_id": current.fields["object_id"],
        "fact_type_key": current.fields["fact_type_key"],
        "created_at": current.fields["created_at"],
        "updated_at": command.event_at,
    }
    timestamp_appended_change_log(proposed, command.event_at)
    change_log_issues = (
        () if command.allow_legacy_routed_spark_migration
        else validate_change_log_transition(current.fields, proposed, allow_first_log=allow_first_log)
    )
    if change_log_issues:
        return FactUpdateResult(
            "candidate_rejected",
            command.event_at,
            issues=change_log_issues,
            current=current,
        )

    require_study_report_metadata = False
    if command.fact_type_key == "study":
        changed_report_fields = {
            field
            for field in STUDY_REPORT_CONTENT_FIELDS
            if current.fields.get(field) != command.supplied.get(field)
        }
        content_changed = bool(changed_report_fields) or (
            (current.body or "") != (command.body or "")
        )
        require_study_report_metadata = repairing_invalid_before or content_changed

    candidate, candidate_text = _candidate(
        command,
        current.fields,
        repairing_invalid_before=repairing_invalid_before,
        require_study_report_metadata=require_study_report_metadata,
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
        rolled_back = rollback.outcome == "replaced" and rollback.namespace_state == "committed"
        residual_readback = None if rolled_back else _project_read(command)
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
            residual_readback=residual_readback,
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

    if command.fact_type_key == "workcase":
        return _workcase_rejection(command.event_at)
    if not native_atomic_fact_writes_supported():
        return FactUpdateResult("durability_unavailable", command.event_at)
    layout = LAYOUTS[command.fact_type_key]
    completed: FactUpdateResult | None = None
    try:
        with fact_write_lock(command.boundary, layout):
            completed = apply_fact_update_locked(command)
    except OSError:
        if completed is None:
            raise
        return replace(completed, coordination_release_uncertain=True)
    assert completed is not None
    return completed


__all__ = [
    "MANAGED_FIELDS",
    "FactUpdateCommand",
    "FactUpdateResult",
    "UpdateStatus",
    "apply_fact_update",
    "apply_fact_update_locked",
]
