"""Helper-independent transaction for one controlled fact-object replacement."""

from __future__ import annotations

from collections import Counter
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
from ldvh.facts.transitions import validate_fact_transition
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
    allow_workcase_managed_record_mutation: bool = False


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


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _version_bumped(before: Mapping[str, Any], after: Mapping[str, Any], key: str) -> bool:
    previous = before.get(key)
    current = after.get(key)
    return _positive_integer(previous) and _positive_integer(current) and current > previous


def _review_identity(review: object) -> tuple[str, str, int] | None:
    if not isinstance(review, Mapping):
        return None
    reviewer = review.get("reviewer")
    reviewed_at = review.get("reviewed_at")
    subject_version = review.get("subject_version")
    if (
        not isinstance(reviewer, str)
        or not reviewer
        or not isinstance(reviewed_at, str)
        or not reviewed_at
        or not _positive_integer(subject_version)
    ):
        return None
    return reviewer, reviewed_at, subject_version


def _review_records(value: object) -> list[Mapping[str, Any]]:
    return [item for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _is_same_event_correction_requiring_resolution(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    field_name: str,
) -> bool:
    """Allow an atomic valid-before correction only when its corrected review now requires a resolution."""

    if field_name == "result_reviews" and after.get("phase") == "independent_reviewing":
        return False
    existing = _review_records(before.get(field_name))
    supplied = _review_records(after.get(field_name))
    if len(existing) != len(supplied):
        return False
    resolution_formed = False
    for existing_review, supplied_review in zip(existing, supplied, strict=True):
        formed_here = "controller_resolution" not in existing_review and "controller_resolution" in supplied_review
        if not formed_here:
            continue
        resolution_formed = True
        if _review_identity(existing_review) != _review_identity(supplied_review):
            return False
        if not any(
            existing_review.get(key) != supplied_review.get(key)
            for key in ("scope", "conclusion", "feedback")
        ):
            return False
    return resolution_formed


def _is_resolution_only_invalid_repair(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> bool:
    """Recognize the one invalid-before exception that may form Controller resolutions."""

    review_fields = {"creation_reviews", "result_reviews"}
    before_top = {
        key: value for key, value in before.items() if key != "updated_at" and key not in review_fields
    }
    after_top = {
        key: value for key, value in after.items() if key != "updated_at" and key not in review_fields
    }
    if before_top != after_top:
        return False

    missing = object()
    resolutions_added = 0
    for field_name in sorted(review_fields):
        existing = before.get(field_name, missing)
        supplied = after.get(field_name, missing)
        if existing is missing or supplied is missing:
            if existing is not supplied:
                return False
            continue
        if not isinstance(existing, list) or not isinstance(supplied, list) or len(existing) != len(supplied):
            return False
        for existing_review, supplied_review in zip(existing, supplied, strict=True):
            if existing_review == supplied_review:
                continue
            if not isinstance(existing_review, Mapping) or not isinstance(supplied_review, Mapping):
                return False
            if "controller_resolution" in existing_review:
                return False
            supplied_without_resolution = dict(supplied_review)
            if "controller_resolution" not in supplied_without_resolution:
                return False
            supplied_without_resolution.pop("controller_resolution")
            if supplied_without_resolution != dict(existing_review):
                return False
            resolutions_added += 1
    return resolutions_added == 1


def _generic_workcase_managed_record_issues(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    repairing_invalid_before: bool = False,
) -> tuple[FactIssue, ...]:
    """Reject new managed events; authorized same-event fact correction remains governed by 05/32."""

    if after.get("workcase_profile") != "control-contract-v2":
        return ()
    # V1 migration has its own stricter preservation checks in transitions.py,
    # including review/approval identity locks. It must remain able to apply an
    # explicitly authorized Controller-resolution calibration while dropping
    # V1-only structure. Every other path that ends at V2 enters this gate so
    # an invalid or unknown before profile cannot bypass managed-event checks.
    if before.get("workcase_profile") == "control-contract-v1":
        return ()

    issues: list[FactIssue] = []
    plan_bumped = _version_bumped(before, after, "plan_version")
    result_bumped = _version_bumped(before, after, "result_version")
    lifecycle_position_changed = any(before.get(key) != after.get(key) for key in ("status", "phase"))
    resolution_only_invalid_repair = repairing_invalid_before and _is_resolution_only_invalid_repair(before, after)
    if repairing_invalid_before and not resolution_only_invalid_repair:
        for field_name in (
            "creation_reviews",
            "result_reviews",
            "execution_approval",
            "closure_approval",
        ):
            if (field_name in before) != (field_name in after) or before.get(field_name) != after.get(field_name):
                issues.append(
                    FactIssue(
                        "schema",
                        (
                            "invalid-before 修复必须原样保留 WorkCase 托管 review/approval；"
                            "唯一窄例外只能原样保留其它内容并补缺失的 Controller 处置"
                        ),
                        field_name,
                    )
                )
    for field_name in ("creation_reviews", "result_reviews"):
        existing = _review_records(before.get(field_name))
        supplied = _review_records(after.get(field_name))
        existing_sequence = [
            identity for item in existing if (identity := _review_identity(item)) is not None
        ]
        supplied_sequence = [
            identity for item in supplied if (identity := _review_identity(item)) is not None
        ]
        existing_ids = Counter(existing_sequence)
        supplied_ids = Counter(supplied_sequence)
        reset_allowed = plan_bumped or (field_name == "result_reviews" and result_bumped)
        if any(count > existing_ids[identity] for identity, count in supplied_ids.items()):
            issues.append(
                FactIssue(
                    "schema",
                    "新增或替换 WorkCase review 必须使用 update-workcase 托管记录",
                    field_name,
                )
            )
            continue
        if not reset_allowed and any(count > supplied_ids[identity] for identity, count in existing_ids.items()):
            issues.append(
                FactIssue(
                    "schema",
                    "移除 WorkCase review 事件必须使用来源定义的受控 reset 或迁移",
                    field_name,
                )
            )
        elif not reset_allowed and existing_sequence != supplied_sequence:
            issues.append(
                FactIssue(
                    "schema",
                    "WorkCase 同一事件事实更正必须保持 review 事件身份与顺序不变",
                    field_name,
                )
            )
        existing_resolutions = Counter(
            identity
            for item in existing
            if "controller_resolution" in item and (identity := _review_identity(item)) is not None
        )
        supplied_resolutions = Counter(
            identity
            for item in supplied
            if "controller_resolution" in item and (identity := _review_identity(item)) is not None
        )
        resolution_formed = any(
            count > existing_resolutions[identity] for identity, count in supplied_resolutions.items()
        )
        same_event_correction_requiring_resolution = (
            not repairing_invalid_before
            and not lifecycle_position_changed
            and _is_same_event_correction_requiring_resolution(before, after, field_name)
        )
        if (
            resolution_formed
            and not resolution_only_invalid_repair
            and not same_event_correction_requiring_resolution
        ):
            issues.append(
                FactIssue(
                    "schema",
                    (
                        "新增 WorkCase review 的 Controller 处置必须使用 update-workcase 托管记录；"
                        "invalid-before 窄修复只能原样保留其它内容并补缺失处置"
                    ),
                    field_name,
                )
            )
        if lifecycle_position_changed and not reset_allowed and existing != supplied:
            issues.append(
                FactIssue(
                    "schema",
                    "WorkCase lifecycle 位置变化时不得同时修正既有 review 事件内容",
                    field_name,
                )
            )

    approval_rules = (
        ("execution_approval", plan_bumped),
        ("closure_approval", plan_bumped or result_bumped),
    )
    for field_name, reset_allowed in approval_rules:
        existing = before.get(field_name)
        supplied = after.get(field_name)
        existing_record = isinstance(existing, Mapping)
        supplied_record = isinstance(supplied, Mapping)
        if not existing_record and supplied_record:
            issues.append(
                FactIssue(
                    "schema",
                    "形成 WorkCase Human approval 必须使用 update-workcase 托管记录",
                    field_name,
                )
            )
        elif (
            existing_record
            and supplied_record
            and (
                existing.get("subject_version"),
                existing.get("approved_at"),
            )
            != (
                supplied.get("subject_version"),
                supplied.get("approved_at"),
            )
        ):
            issues.append(
                FactIssue(
                    "schema",
                    "替换 WorkCase Human approval 事件必须使用形成该事件的受控路径；通用修正只能保留事件身份",
                    field_name,
                )
            )
        elif existing_record and supplied_record and lifecycle_position_changed and dict(existing) != dict(supplied):
            issues.append(
                FactIssue(
                    "schema",
                    "WorkCase lifecycle 位置变化时必须原样保留既有 Human approval 事件内容",
                    field_name,
                )
            )
        elif existing_record and not supplied_record and not reset_allowed:
            issues.append(
                FactIssue(
                    "schema",
                    "移除 WorkCase Human approval 必须使用 update-workcase 托管记录",
                    field_name,
                )
            )
    return tuple(issues)


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
        if command.fact_type_key == "workcase" and not command.allow_workcase_managed_record_mutation:
            issues.extend(
                _generic_workcase_managed_record_issues(
                    before,
                    parsed.fields,
                    repairing_invalid_before=repairing_invalid_before,
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
