"""Deterministically construct one current-profile WorkCase update candidate.

This module owns only the mechanical delta and managed-record rules declared by
the WorkCase fact source.  Lifecycle choices remain explicit caller fields and
the existing schema/transition validators remain the authority for the final
candidate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ldvh.facts.workcase_projection import workcase_subject_fingerprint

CURRENT_PROFILE = "control-contract-v1"
PLAN_RESET_FIELDS = frozenset(
    {
        "execution_approval",
        "result_version",
        "success_criterion_results",
        "controller_check_summary",
        "result_reviews",
        "improvement_observations",
        "residual_responsibilities",
        "nonbinding_followups",
        "closure_approval",
        "validation_summary",
        "closure_outcome",
        "disposition_summary",
    }
)
RESULT_RESET_FIELDS = frozenset({"result_reviews", "closure_approval"})


@dataclass(frozen=True, slots=True)
class WorkCaseUpdateConstruction:
    supplied: dict[str, Any] | None
    receipts: tuple[dict[str, Any], ...] = ()
    problems: tuple[str, ...] = ()


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _managed_actions(managed: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(key for key, value in managed.items() if value is not None)


def _has_audit(
    fields: Mapping[str, Any], subject_kind: str, subject_version: int
) -> bool:
    values = fields.get("audit_summary")
    return any(
        isinstance(item, Mapping)
        and item.get("subject_kind") == subject_kind
        and item.get("subject_version") == subject_version
        for item in (values if isinstance(values, list) else [])
    )


def _same_approval(existing: object, submitted: Mapping[str, Any], version: int) -> bool:
    if not isinstance(existing, Mapping) or existing.get("subject_version") != version:
        return False
    caller_owned = {key: existing[key] for key in ("summary", "source_refs") if key in existing}
    return caller_owned == dict(submitted)


def _review_record(
    submitted: Mapping[str, Any],
    *,
    event_at: str,
    version: int,
    projection_key: str,
    fingerprint: str,
    include_resolution: bool,
) -> dict[str, Any]:
    record = {
        "reviewer": submitted["reviewer"],
        "reviewed_at": event_at,
        "subject_version": version,
        "scope": submitted["scope"],
        "conclusion": submitted["conclusion"],
        "feedback": submitted["feedback"],
        "review_basis": {
            "projection_key": projection_key,
            "subject_fingerprint": fingerprint,
        },
    }
    if include_resolution:
        record["controller_resolution"] = submitted["controller_resolution"]
    return record


def _receipt(
    action: str,
    version: int,
    *,
    index: int | None = None,
    projection_key: str | None = None,
    fingerprint: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {"action": action, "subject_version": version}
    if index is not None:
        value["review_index"] = index
    if projection_key is not None:
        value["projection_key"] = projection_key
    if fingerprint is not None:
        value["subject_fingerprint"] = fingerprint
    return value


def _sequence(value: object) -> Sequence[Any]:
    return value if isinstance(value, list) else ()


def construct_workcase_update(
    before: Mapping[str, Any],
    *,
    set_fields: Mapping[str, Any],
    remove_fields: Sequence[str],
    managed_records: Mapping[str, Any],
    event_at: str,
) -> WorkCaseUpdateConstruction:
    """Apply the source-defined construction order without deciding lifecycle semantics."""

    problems: list[str] = []
    if before.get("fact_type_key") != "workcase" or before.get("workcase_profile") != CURRENT_PROFILE:
        return WorkCaseUpdateConstruction(None, problems=("对象不是 current-profile WorkCase",))

    after = dict(before)
    for key, value in set_fields.items():
        after[key] = value
    for key in remove_fields:
        after.pop(key, None)

    actions = _managed_actions(managed_records)
    plan_before = before.get("plan_version")
    plan_target = set_fields.get("plan_version")
    plan_bump = "plan_version" in set_fields
    if plan_bump:
        if not _positive_integer(plan_before) or plan_target != plan_before + 1:
            problems.append("set.plan_version 必须精确等于 before plan_version + 1")
        if set_fields.get("phase") != "human_plan_confirming":
            problems.append("计划升版必须显式 set.phase=human_plan_confirming")
        if managed_records.get("replace_creation_reviews") is None:
            problems.append("计划升版必须同次 replace_creation_reviews")
        if any(key in set_fields for key in PLAN_RESET_FIELDS):
            problems.append("计划升版时 set 不得包含固定 reset 字段")
        if any(action != "replace_creation_reviews" for action in actions):
            problems.append("计划升版后同次托管动作只允许 replace_creation_reviews")
        if _positive_integer(plan_before) and not _has_audit(after, "superseded_plan", plan_before):
            problems.append("计划升版必须提供 superseded_plan audit continuity")
        if workcase_subject_fingerprint(before, "plan_current") == workcase_subject_fingerprint(
            after, "plan_current"
        ):
            problems.append("计划内容未变化时不得递增 plan_version")
        for key in PLAN_RESET_FIELDS:
            after.pop(key, None)
    elif managed_records.get("replace_creation_reviews") is not None:
        problems.append("replace_creation_reviews 只能与计划升版同次出现")

    result_before = before.get("result_version")
    result_bump = "result_version" in set_fields
    result_target = set_fields.get("result_version")
    if result_bump:
        expected = 1 if result_before is None else result_before + 1 if _positive_integer(result_before) else None
        if result_target != expected:
            problems.append("set.result_version 必须首次建立为 1 或精确递增 1")
        if result_before is not None:
            if any(key in set_fields for key in RESULT_RESET_FIELDS):
                problems.append("结果升版时 set 不得包含固定 reset 字段")
            if any(
                action in {"append_result_reviews", "resolve_result_reviews", "closure_approval"}
                for action in actions
            ):
                problems.append("结果升版不得同次追加、处置结果审核或形成关闭批准")
            if before.get("result_reviews") and _positive_integer(result_before) and not _has_audit(
                after, "superseded_result", result_before
            ):
                problems.append("结果升版必须提供 superseded_result audit continuity")
            for key in RESULT_RESET_FIELDS:
                after.pop(key, None)

    if managed_records.get("append_result_reviews") is not None and managed_records.get(
        "resolve_result_reviews"
    ) is not None:
        problems.append("append_result_reviews 与 resolve_result_reviews 不得同次出现")
    if "execution_approval" in actions and len(actions) != 1:
        problems.append("execution_approval 不得与其它托管动作同次出现")
    if "closure_approval" in actions and len(actions) != 1:
        problems.append("closure_approval 不得与其它托管动作同次出现")
    if "closure_approval" in actions:
        if set_fields.get("status") != "closed" or set_fields.get("phase") != "closed":
            problems.append("关闭批准必须显式 set status=closed 且 phase=closed")
        terminal_forbidden = {"priority", "blocking_summary", "resume_from", "waiting_on"}
        remaining = terminal_forbidden & set(after)
        if remaining:
            problems.append("关闭批准必须同次移除终态禁止字段: " + ", ".join(sorted(remaining)))

    if problems:
        return WorkCaseUpdateConstruction(None, problems=tuple(problems))

    receipts: list[dict[str, Any]] = []
    creation_inputs = managed_records.get("replace_creation_reviews")
    if creation_inputs is not None:
        assert _positive_integer(after.get("plan_version"))
        plan_version = after["plan_version"]
        fingerprint = workcase_subject_fingerprint(after, "plan_current")
        reviews = [
            _review_record(
                item,
                event_at=event_at,
                version=plan_version,
                projection_key="plan_current",
                fingerprint=fingerprint,
                include_resolution=True,
            )
            for item in _sequence(creation_inputs)
        ]
        after["creation_reviews"] = reviews
        receipts.extend(
            _receipt(
                "creation_review_replaced",
                plan_version,
                index=index,
                projection_key="plan_current",
                fingerprint=fingerprint,
            )
            for index in range(len(reviews))
        )

    append_inputs = managed_records.get("append_result_reviews")
    if append_inputs is not None:
        result_version = after.get("result_version")
        if not _positive_integer(result_version):
            return WorkCaseUpdateConstruction(None, problems=("追加结果审核要求有效 result_version",))
        reviews = list(_sequence(after.get("result_reviews")))
        for item in _sequence(append_inputs):
            projection_key = item["projection_key"]
            before_fingerprint = workcase_subject_fingerprint(before, projection_key)
            fingerprint = workcase_subject_fingerprint(after, projection_key)
            if fingerprint != before_fingerprint:
                return WorkCaseUpdateConstruction(
                    None,
                    problems=("新增 result review 的同次 delta 不得改变其 subject projection",),
                )
            review = _review_record(
                item,
                event_at=event_at,
                version=result_version,
                projection_key=projection_key,
                fingerprint=fingerprint,
                include_resolution=False,
            )
            reviews.append(review)
            receipts.append(
                _receipt(
                    "result_review_appended",
                    result_version,
                    index=len(reviews) - 1,
                    projection_key=projection_key,
                    fingerprint=fingerprint,
                )
            )
        if reviews != list(_sequence(after.get("result_reviews"))):
            after["result_reviews"] = reviews

    resolution_inputs = managed_records.get("resolve_result_reviews")
    if resolution_inputs is not None:
        result_version = after.get("result_version")
        if not _positive_integer(result_version):
            return WorkCaseUpdateConstruction(None, problems=("处置结果审核要求有效 result_version",))
        reviews = [
            dict(item) if isinstance(item, Mapping) else item
            for item in _sequence(before.get("result_reviews"))
        ]
        for item in _sequence(resolution_inputs):
            index = item["review_index"]
            if index >= len(reviews) or not isinstance(reviews[index], dict):
                return WorkCaseUpdateConstruction(None, problems=(f"review_index {index} 不存在",))
            if reviews[index].get("controller_resolution") == item["controller_resolution"]:
                continue
            reviews[index]["controller_resolution"] = item["controller_resolution"]
            receipts.append(_receipt("result_review_resolved", result_version, index=index))
        if reviews != list(_sequence(before.get("result_reviews"))):
            after["result_reviews"] = reviews

    approval_input = managed_records.get("execution_approval")
    if approval_input is not None:
        plan_version = after.get("plan_version")
        if not _positive_integer(plan_version):
            return WorkCaseUpdateConstruction(None, problems=("执行批准要求有效 plan_version",))
        if not _same_approval(after.get("execution_approval"), approval_input, plan_version):
            after["execution_approval"] = {
                "subject_version": plan_version,
                "approved_at": event_at,
                **dict(approval_input),
            }
            receipts.append(_receipt("execution_approval_recorded", plan_version))

    closure_input = managed_records.get("closure_approval")
    if closure_input is not None:
        result_version = after.get("result_version")
        if not _positive_integer(result_version):
            return WorkCaseUpdateConstruction(None, problems=("关闭批准要求有效 result_version",))
        after["closure_approval"] = {
            "subject_version": result_version,
            "approved_at": event_at,
            **dict(closure_input),
        }
        after["closed_at"] = event_at
        receipts.append(_receipt("closure_approval_recorded", result_version))

    supplied = {
        key: value
        for key, value in after.items()
        if key not in {"object_id", "fact_type_key", "created_at", "updated_at"}
    }
    return WorkCaseUpdateConstruction(supplied, tuple(receipts))


__all__ = [
    "CURRENT_PROFILE",
    "PLAN_RESET_FIELDS",
    "RESULT_RESET_FIELDS",
    "WorkCaseUpdateConstruction",
    "construct_workcase_update",
]
