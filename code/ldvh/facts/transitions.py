"""Mechanical transition checks for one-object fact updates."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable

from ldvh.facts.models import FactIssue
from ldvh.facts.validation import parse_rfc3339
from ldvh.facts.workcase_projection import (
    PROJECTION_KEYS,
    project_workcase_subject,
    workcase_subject_fingerprint,
)

_STATUS_EDGES = {
    "spark": {("open", "routed"), ("open", "implemented"), ("open", "discarded")},
    "workcase": {
        ("open", "blocked"),
        ("blocked", "open"),
        ("open", "closed"),
        ("blocked", "closed"),
    },
    "adr": {("active", "retired")},
    "pitfall": {("active", "retired")},
    "study": {("active", "retired")},
}

_WORKCASE_PHASE_EDGES = {
    ("human_plan_confirming", "executing"),
    ("executing", "human_plan_confirming"),
    ("executing", "controller_checking"),
    ("controller_checking", "executing"),
    ("controller_checking", "independent_reviewing"),
    ("controller_checking", "closure_preparing"),
    ("independent_reviewing", "controller_checking"),
    ("independent_reviewing", "executing"),
    ("independent_reviewing", "closure_preparing"),
    ("closure_preparing", "independent_reviewing"),
    ("closure_preparing", "human_closure_confirming"),
    ("human_closure_confirming", "executing"),
    ("human_closure_confirming", "controller_checking"),
    ("human_closure_confirming", "independent_reviewing"),
    ("human_closure_confirming", "closure_preparing"),
    ("human_closure_confirming", "closed"),
}

_V1_PROFILE = "control-contract-v1"
_V2_PROFILE = "control-contract-v2"
_V1_BOUNDARY = parse_rfc3339("2026-07-20T07:30:00+08:00")
_V2_BOUNDARY = parse_rfc3339("2026-07-26T12:45:00+08:00")
_PLAN_TOP_FIELDS = (
    "goal",
    "scope",
    "success_criteria",
    "success_criterion_definitions",
)
_PLAN_ITEM_FIELDS = (
    "item_id",
    "goal",
    "expected_result",
    "depends_on",
    "approach_summary",
    "template_keys",
    "template_deviation_summary",
)
_PLAN_RESET_FIELDS = (
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
)
_RESULT_CONTEXT_FIELDS = (
    "result_version",
    "success_criterion_results",
    "controller_check_summary",
    "result_reviews",
    "improvement_observations",
    "residual_responsibilities",
    "nonbinding_followups",
    "validation_summary",
    "closure_outcome",
    "disposition_summary",
)
_REVIEWER_OWNED_FIELDS = (
    "reviewer",
    "reviewed_at",
    "subject_version",
    "scope",
    "conclusion",
    "feedback",
    "review_basis",
)


def _stable(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _projection(fields: dict[str, object], top: Iterable[str], item: Iterable[str]) -> str:
    projected: dict[str, object] = {key: fields.get(key) for key in top}
    raw_items = fields.get("work_items")
    projected["work_items"] = [
        {key: raw.get(key) for key in item}
        for raw in (raw_items if isinstance(raw_items, list) else [])
        if isinstance(raw, dict)
    ]
    return _stable(projected)


def _plan_projection(fields: dict[str, object]) -> str:
    if _is_control_profile(fields):
        return _stable(project_workcase_subject(fields, "plan_current"))
    return _projection(fields, _PLAN_TOP_FIELDS, _PLAN_ITEM_FIELDS)


def _cancelled_item_status_changed(before: dict[str, object], after: dict[str, object]) -> bool:
    def statuses(fields: dict[str, object]) -> dict[str, object]:
        items = fields.get("work_items")
        return {
            str(item.get("item_id")): item.get("status")
            for item in (items if isinstance(items, list) else [])
            if isinstance(item, dict) and isinstance(item.get("item_id"), str)
        }

    existing = statuses(before)
    supplied = statuses(after)
    return any(
        existing[item_id] != supplied[item_id] and "cancelled" in {existing[item_id], supplied[item_id]}
        for item_id in existing.keys() & supplied.keys()
    )


def _version(fields: dict[str, object], key: str) -> int | None:
    value = fields.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _reviewer_records(fields: dict[str, object]) -> tuple[str, ...]:
    values = fields.get("result_reviews")
    return tuple(
        _stable({key: review.get(key) for key in _REVIEWER_OWNED_FIELDS})
        for review in (values if isinstance(values, list) else [])
        if isinstance(review, dict)
    )


def _new_reviewer_record_issues(before: dict[str, object], after: dict[str, object]) -> list[FactIssue]:
    """Check only Reviewer records formed or changed by this transition."""

    if not _is_v1(after):
        return []
    remaining = Counter(_reviewer_records(before))
    values = after.get("result_reviews")
    issues: list[FactIssue] = []
    for index, review in enumerate(values if isinstance(values, list) else []):
        if not isinstance(review, dict):
            continue
        record = _stable({key: review.get(key) for key in _REVIEWER_OWNED_FIELDS})
        if remaining[record] > 0:
            remaining[record] -= 1
            continue
        basis = review.get("review_basis")
        if not isinstance(basis, dict):
            continue
        projection_key = basis.get("projection_key")
        if projection_key not in PROJECTION_KEYS:
            continue
        expected = workcase_subject_fingerprint(after, projection_key)
        if basis.get("subject_fingerprint") != expected:
            issues.append(
                FactIssue(
                    "schema",
                    "新形成或更新的 result review 必须绑定当次 after snapshot",
                    f"result_reviews[{index}].review_basis.subject_fingerprint",
                )
            )
    return issues


def _creation_reviewer_records(fields: dict[str, object]) -> tuple[str, ...]:
    values = fields.get("creation_reviews")
    return tuple(
        _stable({key: review.get(key) for key in _REVIEWER_OWNED_FIELDS})
        for review in (values if isinstance(values, list) else [])
        if isinstance(review, dict)
    )


def _review_event_identities(fields: dict[str, object], array_name: str) -> Counter[str]:
    values = fields.get(array_name)
    return Counter(
        _stable({key: review.get(key) for key in ("reviewer", "reviewed_at", "subject_version")})
        for review in (values if isinstance(values, list) else [])
        if isinstance(review, dict)
    )


def _forms_review_event(before: dict[str, object], after: dict[str, object], array_name: str) -> bool:
    existing = _review_event_identities(before, array_name)
    supplied = _review_event_identities(after, array_name)
    return any(count > existing[identity] for identity, count in supplied.items())


def _audit_entries(fields: dict[str, object]) -> dict[str, str]:
    values = fields.get("audit_summary")
    return {
        str(entry.get("audit_id")): _stable(entry)
        for entry in (values if isinstance(values, list) else [])
        if isinstance(entry, dict) and isinstance(entry.get("audit_id"), str)
    }


def _matching_audit_entry(
    fields: dict[str, object], subject_kind: str, subject_version: int | None
) -> dict[str, object] | None:
    values = fields.get("audit_summary")
    for entry in values if isinstance(values, list) else []:
        if (
            isinstance(entry, dict)
            and entry.get("subject_kind") == subject_kind
            and entry.get("subject_version") == subject_version
        ):
            return entry
    return None


def _profile(fields: dict[str, object]) -> str:
    value = fields.get("workcase_profile")
    if value == _V1_PROFILE:
        return "v1"
    if value == _V2_PROFILE:
        return "v2"
    return "legacy" if value is None else "invalid"


def _is_v1(fields: dict[str, object]) -> bool:
    return _profile(fields) == "v1"


def _is_control_profile(fields: dict[str, object]) -> bool:
    return _profile(fields) in {"v1", "v2"}


def _required_profile_for_missing_value(fields: dict[str, object]) -> str | None:
    created = parse_rfc3339(fields.get("created_at"))
    if created is None or _V1_BOUNDARY is None or _V2_BOUNDARY is None or created < _V1_BOUNDARY:
        return None
    return "v2" if created >= _V2_BOUNDARY else "v1"


def _is_profile_only_repair(
    before: dict[str, object],
    after: dict[str, object],
    required_profile: str,
) -> bool:
    before_content = {key: value for key, value in before.items() if key != "updated_at"}
    after_content = {key: value for key, value in after.items() if key not in {"updated_at", "workcase_profile"}}
    return (
        after.get("workcase_profile") == (_V2_PROFILE if required_profile == "v2" else _V1_PROFILE)
        and before_content == after_content
    )


def _migration_locked_reviews(fields: dict[str, object], array_name: str) -> tuple[str, ...]:
    values = fields.get(array_name)
    normalized: list[str] = []
    for review in values if isinstance(values, list) else []:
        if not isinstance(review, dict):
            continue
        member = dict(review)
        member.pop("review_basis", None)
        member.pop("controller_resolution", None)
        normalized.append(_stable(member))
    return tuple(normalized)


def _reviews_are_preserved_subset(
    before: dict[str, object],
    after: dict[str, object],
    array_name: str,
) -> bool:
    """Check only ordered record preservation; sources, not Code, decide whether any removal is warranted."""

    existing = _migration_locked_reviews(before, array_name)
    retained = _migration_locked_reviews(after, array_name)
    if existing and not retained:
        return False
    cursor = iter(existing)
    return all(any(candidate == review for candidate in cursor) for review in retained)


def _approval_event_identity(fields: dict[str, object], key: str) -> tuple[object, object] | None:
    value = fields.get(key)
    if not isinstance(value, dict):
        return None
    return value.get("subject_version"), value.get("approved_at")


def _all_work_items_pending(fields: dict[str, object]) -> bool:
    items = fields.get("work_items")
    return (
        isinstance(items, list)
        and bool(items)
        and all(isinstance(item, dict) and item.get("status") == "pending" for item in items)
    )


def _workcase_transition(
    before: dict[str, object],
    after: dict[str, object],
    *,
    repairing_invalid_before: bool,
) -> list[FactIssue]:
    issues: list[FactIssue] = []
    before_profile = _profile(before)
    after_profile = _profile(after)
    before_control = _is_control_profile(before)
    v1_to_v2 = before_profile == "v1" and after_profile == "v2"
    before_phase = before.get("phase")
    after_phase = after.get("phase")
    before_status = before.get("status")
    after_status = after.get("status")
    lifecycle_position_changed = before_status != after_status or before_phase != after_phase
    before_plan = _version(before, "plan_version")
    after_plan = _version(after, "plan_version")
    plan_bumped = before_plan is not None and after_plan is not None and after_plan > before_plan
    plan_reset = before_phase != after_phase and after_phase == "human_plan_confirming" and plan_bumped
    required_missing_profile = _required_profile_for_missing_value(before)
    missing_profile_repair_attempt = (
        repairing_invalid_before
        and before.get("workcase_profile") is None
        and required_missing_profile is not None
        and after_profile == required_missing_profile
    )
    missing_profile_repair = missing_profile_repair_attempt and _is_profile_only_repair(
        before,
        after,
        required_missing_profile,
    )

    if missing_profile_repair_attempt and not missing_profile_repair:
        issues.append(
            FactIssue(
                "schema",
                "缺失 workcase_profile 的修复只允许补入 created_at 对应 profile，不得同次改变其它领域内容",
                "workcase_profile",
            )
        )

    if (
        repairing_invalid_before
        and before.get("workcase_profile") is None
        and required_missing_profile is not None
        and after_profile != required_missing_profile
    ):
        required_value = _V2_PROFILE if required_missing_profile == "v2" else _V1_PROFILE
        issues.append(
            FactIssue(
                "schema",
                f"缺失 workcase_profile 的修复必须按 created_at 补为 {required_value}",
                "workcase_profile",
            )
        )

    if before_profile == "v2" and after_profile != "v2":
        issues.append(FactIssue("schema", "V2 WorkCase profile 不得移除或降级", "workcase_profile"))
    if before_profile == "v1" and after_profile == "v1":
        issues.append(FactIssue("schema", "V1 WorkCase 只允许显式迁移到 V2，不再接受普通更新", "workcase_profile"))
        return issues
    if before_profile == "v1" and after_profile not in {"v1", "v2"}:
        issues.append(FactIssue("schema", "V1 WorkCase profile 不得移除或降级", "workcase_profile"))
    if before_profile == "legacy" and after_profile == "v2" and not missing_profile_repair:
        issues.append(FactIssue("schema", "legacy WorkCase 不得借 V2 简化直接升级", "workcase_profile"))
    if (
        before_profile == "legacy"
        and after_profile in {"v1", "v2"}
        and before_status == "closed"
        and not missing_profile_repair
    ):
        issues.append(FactIssue("schema", "closed legacy WorkCase 禁止升级 profile", "workcase_profile"))

    if v1_to_v2:
        if before_status != after_status or before_phase != after_phase:
            issues.append(FactIssue("schema", "V1→V2 迁移必须保持 status 与 phase 不变", "workcase_profile"))
        for key in ("plan_version", "result_version"):
            if before.get(key) != after.get(key) or (key in before) != (key in after):
                issues.append(FactIssue("schema", f"V1→V2 迁移不得改变 {key}", key))
        for key in ("execution_approval", "closure_approval"):
            if (key in before) != (key in after) or _approval_event_identity(before, key) != _approval_event_identity(
                after, key
            ):
                issues.append(FactIssue("schema", f"V1→V2 迁移不得改变 {key} 的版本或形成时点", key))
        if before_status == "closed":
            if before.get("closure_outcome") != after.get("closure_outcome") or ("closure_outcome" in before) != (
                "closure_outcome" in after
            ):
                issues.append(FactIssue("schema", "closed V1→V2 迁移不得改变 closure_outcome", "closure_outcome"))
        for array_name in ("creation_reviews", "result_reviews"):
            if not _reviews_are_preserved_subset(before, after, array_name):
                issues.append(
                    FactIssue(
                        "schema",
                        (
                            "V1→V2 review 对 before 已存在的同类记录必须在移除 review_basis 与"
                            " controller_resolution 后保持 Reviewer 自有字段的非空有序子序列；"
                            "before 未形成该类记录时不得新增"
                        ),
                        array_name,
                    )
                )

    if before_phase != after_phase and (before_phase, after_phase) not in _WORKCASE_PHASE_EDGES and not plan_reset:
        issues.append(FactIssue("schema", "WorkCase phase 转换不在当前允许边中", "phase"))

    if before_status != after_status and after_status != "closed" and before_phase != after_phase:
        issues.append(FactIssue("schema", "open/blocked 状态变化不得同时改变 phase", "phase"))
    if (
        before_status != "closed"
        and after_status == "closed"
        and (before_phase != "human_closure_confirming" or after_phase != "closed")
    ):
        issues.append(
            FactIssue(
                "schema",
                "WorkCase 只能从 human_closure_confirming 在同一更新中进入 closed",
                "phase",
            )
        )

    approval_withdrawal = (before_phase, after_phase) == ("executing", "human_plan_confirming") and not plan_bumped
    if approval_withdrawal:
        if not before_control or not isinstance(before.get("execution_approval"), dict):
            issues.append(FactIssue("schema", "撤回执行批准要求当前对象已有 execution_approval", "execution_approval"))
        if "execution_approval" in after:
            issues.append(FactIssue("schema", "撤回执行批准后 execution_approval 必须移除", "execution_approval"))
        if any(key in before for key in _PLAN_RESET_FIELDS if key != "execution_approval"):
            issues.append(FactIssue("schema", "撤回执行批准只适用于尚未形成结果包的计划", "phase"))
        if not _all_work_items_pending(after):
            issues.append(FactIssue("schema", "撤回执行批准后所有 work_items 必须恢复为 pending", "work_items"))

    plan_changed = not missing_profile_repair and (
        _plan_projection(before) != _plan_projection(after)
        or (plan_bumped and _cancelled_item_status_changed(before, after))
    )
    if before_plan is not None and (after_plan is None or after_plan < before_plan):
        issues.append(FactIssue("schema", "plan_version 不得减少或移除", "plan_version"))
    if plan_changed and not plan_bumped and not v1_to_v2:
        issues.append(FactIssue("schema", "计划覆盖内容变化必须递增 plan_version", "plan_version"))
    if not plan_changed and plan_bumped:
        issues.append(FactIssue("schema", "计划内容未变化时不得递增 plan_version", "plan_version"))
    if plan_bumped:
        if after_phase != "human_plan_confirming":
            issues.append(FactIssue("schema", "plan_version 递增后必须回到 human_plan_confirming", "phase"))
        for key in _PLAN_RESET_FIELDS:
            if key in after:
                issues.append(FactIssue("schema", "plan_version 递增后旧批准和结果包必须移除", key))
        if after_profile == "v1":
            audit_entry = _matching_audit_entry(after, "superseded_plan", before_plan)
            if audit_entry is None:
                issues.append(
                    FactIssue(
                        "schema",
                        "V1 plan_version 递增必须保留被替代计划的 audit continuity",
                        "audit_summary",
                    )
                )
            elif audit_entry.get("review_count") != len(before.get("creation_reviews", [])):
                issues.append(
                    FactIssue(
                        "schema",
                        "superseded_plan audit review_count 必须等于被替代详细审核数",
                        "audit_summary",
                    )
                )
    if before_profile == "legacy" and after_profile in {"v1", "v2"} and not plan_bumped and not missing_profile_repair:
        issues.append(
            FactIssue("schema", "legacy 显式升级到 control-contract-v1 必须递增 plan_version", "plan_version")
        )

    before_creation_reviews = _creation_reviewer_records(before)
    after_creation_reviews = _creation_reviewer_records(after)
    creation_reviews_changed = before_creation_reviews != after_creation_reviews
    creation_review_formed = _forms_review_event(before, after, "creation_reviews")
    if (
        not v1_to_v2
        and not plan_bumped
        and creation_reviews_changed
        and (after_profile != "v2" or creation_review_formed or lifecycle_position_changed)
    ):
        if after_profile != "v2":
            summary = "creation review 的 Reviewer 自有字段只能随计划升版替换"
        elif creation_review_formed:
            summary = "creation review 新事件只能随计划升版形成"
        else:
            summary = "creation review 同事件事实修正必须保持 status 与 phase 不变"
        issues.append(
            FactIssue(
                "schema",
                summary,
                "creation_reviews",
            )
        )

    before_result = _version(before, "result_version")
    after_result = _version(after, "result_version")
    before_reviews = _reviewer_records(before)
    after_reviews = _reviewer_records(after)
    result_bumped = before_result is not None and after_result is not None and after_result > before_result
    if not plan_bumped and before_result is not None and (after_result is None or after_result < before_result):
        issues.append(FactIssue("schema", "result_version 不得减少或移除", "result_version"))
    if not plan_bumped and before_result is None and after_result is not None:
        if (before_phase, after_phase) != ("executing", "controller_checking") or after_result != 1:
            issues.append(
                FactIssue(
                    "schema",
                    "result_version 只能在首次 executing 进入 controller_checking 时建立为 1",
                    "result_version",
                )
            )
    if (before_phase, after_phase) == ("human_plan_confirming", "executing"):
        for key in _RESULT_CONTEXT_FIELDS:
            if key in after:
                issues.append(FactIssue("schema", "首次进入 executing 不得携带结果上下文", key))
    if result_bumped:
        for key in ("result_reviews", "closure_approval"):
            if key in after:
                issues.append(FactIssue("schema", "result_version 递增后必须重新形成审核且旧关闭批准失效", key))
        if after_profile == "v1" and before_reviews:
            audit_entry = _matching_audit_entry(after, "superseded_result", before_result)
            if audit_entry is None:
                issues.append(
                    FactIssue(
                        "schema",
                        "V1 result_version 递增并移除旧审核时必须保留 audit continuity",
                        "audit_summary",
                    )
                )
            elif audit_entry.get("review_count") != len(before_reviews):
                issues.append(
                    FactIssue(
                        "schema",
                        "superseded_result audit review_count 必须等于被替代详细审核数",
                        "audit_summary",
                    )
                )

    review_records_changed = before_reviews != after_reviews
    result_review_formed = _forms_review_event(before, after, "result_reviews")
    review_reset_for_new_version = result_bumped and not after_reviews
    if (
        not v1_to_v2
        and not plan_bumped
        and review_records_changed
        and (after_profile != "v2" or result_review_formed)
        and before_phase != "independent_reviewing"
        and not review_reset_for_new_version
    ):
        summary = (
            "result review 新事件只能在 independent_reviewing 形成；既有事件的获授权事实修正不在此机械规则裁决"
            if after_profile == "v2"
            else "result review 只能在 independent_reviewing 形成；离开后 Reviewer 自有字段不得改写"
        )
        issues.append(
            FactIssue(
                "schema",
                summary,
                "result_reviews",
            )
        )
    if not v1_to_v2 and review_records_changed and not review_reset_for_new_version:
        issues.extend(_new_reviewer_record_issues(before, after))
    if (
        after_profile == "v2"
        and not v1_to_v2
        and not plan_bumped
        and not result_bumped
        and review_records_changed
        and not result_review_formed
        and lifecycle_position_changed
    ):
        issues.append(
            FactIssue(
                "schema",
                "result review 同事件事实修正必须保持 status 与 phase 不变",
                "result_reviews",
            )
        )
    if (before_phase, after_phase) == ("controller_checking", "closure_preparing"):
        v2_reviews_preserved = after_profile == "v2" and bool(after_reviews) and not result_review_formed
        if (
            not before_reviews
            or (after_profile == "v2" and not v2_reviews_preserved)
            or (after_profile != "v2" and before_reviews != after_reviews)
        ):
            issues.append(
                FactIssue(
                    "schema",
                    "controller_checking 进入 closure_preparing 必须保留转换前已形成的当前版本 review",
                    "result_reviews",
                )
            )

    if after_profile == "v1":
        before_audit = _audit_entries(before)
        after_audit = _audit_entries(after)
        for audit_id, before_entry in before_audit.items():
            if audit_id not in after_audit:
                issues.append(FactIssue("schema", "既有 audit_summary 条目不得移除", "audit_summary"))
            elif after_audit[audit_id] != before_entry:
                issues.append(FactIssue("schema", "既有 audit_summary 条目不得改写", "audit_summary"))
    return issues


def validate_fact_transition(
    fact_type_key: str,
    before: dict[str, object],
    after: dict[str, object],
    *,
    repairing_invalid_before: bool = False,
) -> tuple[FactIssue, ...]:
    """Validate the mechanically observable edge between two full snapshots."""

    issues: list[FactIssue] = []
    before_updated = parse_rfc3339(before.get("updated_at"))
    after_updated = parse_rfc3339(after.get("updated_at"))
    if before_updated is not None and after_updated is not None and after_updated <= before_updated:
        issues.append(FactIssue("schema", "实际更新的 updated_at 必须晚于当前值", "updated_at"))
    before_status = before.get("status")
    after_status = after.get("status")
    if (
        not repairing_invalid_before
        and before_status != after_status
        and (before_status, after_status) not in _STATUS_EDGES[fact_type_key]
    ):
        issues.append(FactIssue("schema", "status 转换不在当前单对象更新允许边中", "status"))
    if fact_type_key == "workcase":
        issues.extend(
            _workcase_transition(
                before,
                after,
                repairing_invalid_before=repairing_invalid_before,
            )
        )
    return tuple(issues)


__all__ = ["validate_fact_transition"]
