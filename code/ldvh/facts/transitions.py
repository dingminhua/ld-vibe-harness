"""Mechanical transition checks for one-object fact updates."""

from __future__ import annotations

import json
from collections.abc import Iterable

from ldvh.facts.models import FactIssue
from ldvh.facts.validation import parse_rfc3339

_STATUS_EDGES = {
    "spark": {("open", "routed"), ("open", "discarded")},
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

_PLAN_TOP_FIELDS = ("goal", "scope", "success_criteria")
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
    "controller_check_summary",
    "result_reviews",
    "closure_approval",
    "validation_summary",
    "closure_outcome",
    "disposition_summary",
)
_RESULT_CONTEXT_FIELDS = (
    "result_version",
    "controller_check_summary",
    "result_reviews",
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


def _supersedes(fields: dict[str, object]) -> str:
    relations = fields.get("relations")
    edges = [
        relation
        for relation in (relations if isinstance(relations, list) else [])
        if isinstance(relation, dict) and relation.get("relation_key") == "supersedes"
    ]
    return _stable(edges)


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


def _workcase_transition(before: dict[str, object], after: dict[str, object]) -> list[FactIssue]:
    issues: list[FactIssue] = []
    before_phase = before.get("phase")
    after_phase = after.get("phase")
    before_plan = _version(before, "plan_version")
    after_plan = _version(after, "plan_version")
    plan_bumped = before_plan is not None and after_plan is not None and after_plan > before_plan
    plan_reset = before_phase != after_phase and after_phase == "human_plan_confirming" and plan_bumped
    if before_phase != after_phase and (before_phase, after_phase) not in _WORKCASE_PHASE_EDGES and not plan_reset:
        issues.append(FactIssue("schema", "WorkCase phase 转换不在当前允许边中", "phase"))

    before_status = before.get("status")
    after_status = after.get("status")
    if before_status != after_status and after_status != "closed" and before_phase != after_phase:
        issues.append(FactIssue("schema", "open/blocked 状态变化不得同时改变 phase", "phase"))
    if after_status == "closed" and (before_phase != "human_closure_confirming" or after_phase != "closed"):
        issues.append(
            FactIssue(
                "schema",
                "WorkCase 只能从 human_closure_confirming 在同一更新中进入 closed",
                "phase",
            )
        )

    plan_changed = _projection(before, _PLAN_TOP_FIELDS, _PLAN_ITEM_FIELDS) != _projection(
        after, _PLAN_TOP_FIELDS, _PLAN_ITEM_FIELDS
    )
    if before_plan is not None and (after_plan is None or after_plan < before_plan):
        issues.append(FactIssue("schema", "plan_version 不得减少或移除", "plan_version"))
    if plan_changed and not plan_bumped:
        issues.append(FactIssue("schema", "计划覆盖内容变化必须递增 plan_version", "plan_version"))
    if not plan_changed and plan_bumped:
        issues.append(FactIssue("schema", "计划内容未变化时不得递增 plan_version", "plan_version"))
    if plan_bumped:
        if after_phase != "human_plan_confirming":
            issues.append(FactIssue("schema", "plan_version 递增后必须回到 human_plan_confirming", "phase"))
        for key in _PLAN_RESET_FIELDS:
            if key in after:
                issues.append(FactIssue("schema", "plan_version 递增后旧批准和结果包必须移除", key))

    before_result = _version(before, "result_version")
    after_result = _version(after, "result_version")
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

    before_reviews = _reviewer_records(before)
    after_reviews = _reviewer_records(after)
    review_records_changed = before_reviews != after_reviews
    review_reset_for_new_version = result_bumped and not after_reviews
    if (
        not plan_bumped
        and review_records_changed
        and before_phase != "independent_reviewing"
        and not review_reset_for_new_version
    ):
        issues.append(
            FactIssue(
                "schema",
                "result review 只能在 independent_reviewing 形成；离开后 Reviewer 自有字段不得改写",
                "result_reviews",
            )
        )
    if (before_phase, after_phase) == ("controller_checking", "closure_preparing"):
        if not before_reviews or before_reviews != after_reviews:
            issues.append(
                FactIssue(
                    "schema",
                    "controller_checking 进入 closure_preparing 必须保留转换前已形成的当前版本 review",
                    "result_reviews",
                )
            )
    return issues


def validate_fact_transition(
    fact_type_key: str,
    before: dict[str, object],
    after: dict[str, object],
) -> tuple[FactIssue, ...]:
    """Validate the mechanically observable edge between two full snapshots."""

    issues: list[FactIssue] = []
    before_updated = parse_rfc3339(before.get("updated_at"))
    after_updated = parse_rfc3339(after.get("updated_at"))
    if before_updated is not None and after_updated is not None and after_updated <= before_updated:
        issues.append(FactIssue("schema", "实际更新的 updated_at 必须晚于当前值", "updated_at"))
    before_status = before.get("status")
    after_status = after.get("status")
    if before_status != after_status and (before_status, after_status) not in _STATUS_EDGES[fact_type_key]:
        issues.append(FactIssue("schema", "status 转换不在当前单对象更新允许边中", "status"))
    if after_status == "superseded":
        issues.append(FactIssue("schema", "进入 superseded 要求多对象原子变更", "status"))
    if _supersedes(before) != _supersedes(after):
        issues.append(FactIssue("relation", "supersedes 边只能由多对象原子变更维护", "relations"))
    if fact_type_key == "workcase":
        issues.extend(_workcase_transition(before, after))
    return tuple(issues)


__all__ = ["validate_fact_transition"]
