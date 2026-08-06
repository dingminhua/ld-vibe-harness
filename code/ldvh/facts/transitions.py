"""Mechanical transition checks for fact-object writes.

WorkCase has one current contract.  This module compares two complete parsed
snapshots; single-snapshot shape and presence are validated by
``workcase_validation`` before this layer is called.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from ldvh.facts.contracts import ACTIVE_STATUSES
from ldvh.facts.models import FactIssue
from ldvh.facts.validation import parse_rfc3339
from ldvh.facts.workcase_projection import (
    all_terminal,
    no_execution_facts,
    plan_delta,
    pre_execution_stop_shape,
    result_delta,
    result_projection_complete,
    safe_convergence_shape,
)
from ldvh.facts.workcase_validation import required_quality_gate_issues

WorkCaseOperation = Literal["update", "close", "correct"]

_STATUS_EDGES = {
    "spark": {("open", "routed"), ("open", "implemented"), ("open", "discarded")},
    "adr": {("active", "retired")},
    "pitfall": {("draft", "active"), ("draft", "discarded"), ("active", "discarded")},
    "study": {("active", "retired")},
}

_ACTIVE_PHASES = frozenset(
    {
        "human_plan_confirming",
        "plan_revising",
        "executing",
        "controller_checking",
        "independent_reviewing",
        "closure_preparing",
        "human_closure_confirming",
    }
)
_WORKCASE_PHASE_EDGES = frozenset(
    {
        ("human_plan_confirming", "plan_revising"),
        ("human_plan_confirming", "executing"),
        ("human_plan_confirming", "controller_checking"),
        ("plan_revising", "human_plan_confirming"),
        ("plan_revising", "executing"),
        ("plan_revising", "controller_checking"),
        ("executing", "plan_revising"),
        ("executing", "controller_checking"),
        ("controller_checking", "executing"),
        ("controller_checking", "plan_revising"),
        ("controller_checking", "independent_reviewing"),
        ("controller_checking", "closure_preparing"),
        ("independent_reviewing", "controller_checking"),
        ("independent_reviewing", "plan_revising"),
        ("independent_reviewing", "closure_preparing"),
        ("closure_preparing", "controller_checking"),
        ("closure_preparing", "plan_revising"),
        ("closure_preparing", "human_closure_confirming"),
    }
)
_GATE_WAITING_EXIT_EDGES = frozenset(
    {
        ("human_plan_confirming", "plan_revising"),
        ("human_plan_confirming", "executing"),
        ("human_plan_confirming", "controller_checking"),
        ("independent_reviewing", "controller_checking"),
        ("independent_reviewing", "plan_revising"),
        ("independent_reviewing", "closure_preparing"),
    }
)

_PLAN_REPLACEMENT_RESET_FIELDS = (
    "result_version",
    "success_criterion_results",
    "result_summary",
    "controller_check_summary",
    "validation_summary",
    "result_reviews",
    "closure_proposal",
)
_RESULT_PROJECTION_FIELDS = (
    "success_criterion_results",
    "result_summary",
    "controller_check_summary",
    "validation_summary",
)
_RESULT_STATE_FIELDS = ("result_version", *_RESULT_PROJECTION_FIELDS, "result_reviews")
_ITEM_RUNTIME_FIELDS = ("status", "current_summary", "resume_from", "blocking_summary", "result_summary")
_REVIEWER_FIELDS = (
    "reviewer",
    "reviewed_at",
    "subject_version",
    "scope",
    "conclusion",
    "feedback",
    "actual_method",
    "capability_limitation_id",
    "capability_evidence",
    "assurance_gap",
    "stop_condition_assessment",
)
# ``change_log`` is not a second lifecycle mutation: the shared write core
# appends its one Code-timestamped trace entry to every accepted transaction.
# A blocked-status checkpoint must therefore permit that invariant-preserving
# append while continuing to freeze every semantic domain field.
_BLOCKED_OVERLAY_FIELDS = frozenset({"status", "blocking_summary", "waiting_on", "updated_at", "change_log"})
_BLOCKED_FACT_CORRECTION_FIELDS = frozenset({"title", "priority", "urls"})


def _issue(summary: str, field_path: str) -> FactIssue:
    return FactIssue("schema", summary, field_path)


def _version(fields: Mapping[str, object], key: str) -> int | None:
    value = fields.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _nonblank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _changed_fields(before: Mapping[str, object], after: Mapping[str, object]) -> set[str]:
    return {key for key in before.keys() | after.keys() if not _same_presence_and_value(before, after, key)}


def _same_presence_and_value(before: Mapping[str, object], after: Mapping[str, object], key: str) -> bool:
    if (key in before) != (key in after):
        return False
    if key == "work_items":
        return _normalized_items(before) == _normalized_items(after)
    if key in {"creation_reviews", "result_reviews"}:
        return _reviews(before, key) == _reviews(after, key)
    if key == "success_criterion_definitions":
        return _objects_by_identity(before.get(key), "criterion_id") == _objects_by_identity(
            after.get(key), "criterion_id"
        )
    if key == "success_criterion_results":
        return _objects_by_identity(before.get(key), "criterion_id") == _objects_by_identity(
            after.get(key), "criterion_id"
        )
    if key == "closure_proposal":
        return _normalized_proposal(before.get(key)) == _normalized_proposal(after.get(key))
    if key == "relations":
        return _normalized_relations(before.get(key)) == _normalized_relations(after.get(key))
    return before.get(key) == after.get(key)


def _require_equal(
    before: Mapping[str, object],
    after: Mapping[str, object],
    keys: tuple[str, ...],
    summary: str,
) -> list[FactIssue]:
    return [_issue(summary, key) for key in keys if not _same_presence_and_value(before, after, key)]


def _items(fields: Mapping[str, object]) -> dict[str, dict[str, object]]:
    raw = fields.get("work_items")
    if not isinstance(raw, list):
        return {}
    return {
        str(item["item_id"]): item for item in raw if isinstance(item, dict) and isinstance(item.get("item_id"), str)
    }


def _objects_by_identity(value: object, identity_key: str) -> dict[str, dict[str, object]]:
    if not isinstance(value, list):
        return {}
    return {
        str(member[identity_key]): member
        for member in value
        if isinstance(member, dict) and isinstance(member.get(identity_key), str)
    }


def _normalized_items(fields: Mapping[str, object]) -> dict[str, dict[str, object]]:
    normalized: dict[str, dict[str, object]] = {}
    for item_id, item in _items(fields).items():
        member = dict(item)
        for key in ("depends_on", "template_keys"):
            raw = member.get(key)
            if isinstance(raw, list):
                member[key] = sorted(raw, key=str)
        normalized[item_id] = member
    return normalized


def _normalized_proposal(value: object) -> object:
    if not isinstance(value, dict):
        return value
    normalized = dict(value)
    decisions = normalized.get("residual_decisions")
    if isinstance(decisions, list):
        normalized["residual_decisions"] = sorted(
            (decision for decision in decisions if isinstance(decision, dict)),
            key=lambda decision: str(decision.get("residual_id", "")),
        )
    suggestions = normalized.get("spark_suggestions")
    if isinstance(suggestions, list):
        normalized["spark_suggestions"] = sorted(
            (suggestion for suggestion in suggestions if isinstance(suggestion, dict)),
            key=lambda suggestion: str(suggestion.get("suggestion_id", "")),
        )
    return normalized


def _normalized_relations(value: object) -> dict[tuple[object, object, object, object], dict[str, object]]:
    if not isinstance(value, list):
        return {}
    normalized: dict[tuple[object, object, object, object], dict[str, object]] = {}
    for relation in value:
        if not isinstance(relation, dict):
            continue
        target = relation.get("target")
        target_mapping = target if isinstance(target, dict) else {}
        relation_key = relation.get("relation_key")
        governed_project_id = target_mapping.get("governed_project_id")
        fact_type_key = target_mapping.get("fact_type_key")
        object_id = target_mapping.get("object_id")
        if not all(isinstance(member, str) for member in (relation_key, governed_project_id, fact_type_key, object_id)):
            continue
        identity = (
            relation_key,
            governed_project_id,
            fact_type_key,
            object_id,
        )
        normalized[identity] = relation
    return normalized


def _item_runtime(item: Mapping[str, object]) -> dict[str, object]:
    return {key: item[key] for key in _ITEM_RUNTIME_FIELDS if key in item}


def _item_has_execution_facts(item: Mapping[str, object]) -> bool:
    return item.get("status") in {"in_progress", "blocked", "completed", "cancelled"} or any(
        key in item for key in ("current_summary", "resume_from", "blocking_summary", "result_summary")
    )


def _plan_replacement_carrier_updated(
    before: Mapping[str, object],
    after: Mapping[str, object],
) -> bool:
    after_summary = after.get("summary")
    return _nonblank_string(after_summary) and after_summary != before.get("summary")


def _dependencies_completed(item: Mapping[str, object], all_items: Mapping[str, Mapping[str, object]]) -> bool:
    raw = item.get("depends_on")
    if raw is None:
        return True
    if not isinstance(raw, list):
        return False
    return all(
        isinstance(item_id, str) and item_id in all_items and all_items[item_id].get("status") == "completed"
        for item_id in raw
    )


def _review_identity(review: Mapping[str, object]) -> tuple[str, str, int] | None:
    reviewer = review.get("reviewer")
    reviewed_at = review.get("reviewed_at")
    subject_version = review.get("subject_version")
    if (
        not isinstance(reviewer, str)
        or not isinstance(reviewed_at, str)
        or not isinstance(subject_version, int)
        or isinstance(subject_version, bool)
    ):
        return None
    return reviewer, reviewed_at, subject_version


def _reviews(fields: Mapping[str, object], key: str) -> dict[tuple[object, object, object], dict[str, object]]:
    raw = fields.get(key)
    if not isinstance(raw, list):
        return {}
    reviews: dict[tuple[object, object, object], dict[str, object]] = {}
    for review in raw:
        if not isinstance(review, dict):
            continue
        identity = _review_identity(review)
        if identity is not None:
            reviews[identity] = review
    return reviews


def _reviewed(fields: Mapping[str, object]) -> bool:
    raw = fields.get("result_reviews")
    return isinstance(raw, list) and bool(raw)


def _result_projection_changed(before: Mapping[str, object], after: Mapping[str, object]) -> bool:
    """Compare full ResultΔ when possible and transient result state otherwise."""

    before_complete = result_projection_complete(before)
    after_complete = result_projection_complete(after)
    if before_complete and after_complete:
        return result_delta(before, after)
    # Formal ResultΔ is defined only for complete projections.  Crossing the
    # completeness boundary matters for entering/leaving the result chain;
    # two incomplete snapshots are governed by their phase/item rules and are
    # not mislabeled as ResultΔ merely because an executing item progressed.
    return before_complete != after_complete


def _reviews_resolved(fields: Mapping[str, object]) -> bool:
    raw = fields.get("result_reviews")
    if not isinstance(raw, list) or not raw:
        return False
    for review in raw:
        if not isinstance(review, dict):
            return False
        feedback = review.get("feedback")
        if isinstance(feedback, list) and feedback:
            resolution = review.get("controller_resolution")
            if not isinstance(resolution, str) or not resolution.strip():
                return False
    return True


def _validate_review_ownership(
    before: Mapping[str, object],
    after: Mapping[str, object],
    *,
    plan_changed: bool,
    result_invalidated: bool,
) -> list[FactIssue]:
    issues: list[FactIssue] = []
    same_position = before.get("status") == after.get("status") and before.get("phase") == after.get("phase")
    before_phase = before.get("phase")
    after_phase = after.get("phase")

    for key in ("creation_reviews", "result_reviews"):
        old = _reviews(before, key)
        new = _reviews(after, key)
        removed = old.keys() - new.keys()
        added = new.keys() - old.keys()
        shared = old.keys() & new.keys()

        correction = any(
            any(old[event].get(field) != new[event].get(field) for field in _REVIEWER_FIELDS) for event in shared
        )
        if correction and not same_position:
            issues.append(
                _issue(
                    "Reviewer 自有字段的同事件事实更正不得与 status 或 phase 转换合并",
                    key,
                )
            )

        if key == "creation_reviews":
            correction_position = same_position and after_phase in {"human_plan_confirming", "plan_revising"}
            safe_convergence_removal = bool(removed) and not added and safe_convergence_shape(after)
            pre_gate_candidate_exit = (
                (before_phase, after_phase) == ("plan_revising", "human_plan_confirming")
                and "execution_approval" not in before
                and "execution_approval" not in after
            )
            if (
                (added or removed)
                and not plan_changed
                and not safe_convergence_removal
                and not pre_gate_candidate_exit
            ):
                issues.append(_issue("current plan reviews 只能随 PlanΔ 或 Gate1 前完整候选整体替换", key))
            if correction and not correction_position:
                issues.append(_issue("current plan review 同事件更正只允许停留在计划判断或自动修订位置", key))
        else:
            formation = same_position and after_phase == "independent_reviewing"
            if added and not formation:
                issues.append(_issue("result review 新事件只能在 independent_reviewing 同 phase 形成", key))
            if removed and not (plan_changed or result_invalidated):
                issues.append(_issue("result review 只能在 PlanΔ 或 ResultΔ 失效时整体清除", key))
            if correction and not (same_position and after_phase == "independent_reviewing"):
                issues.append(_issue("result review 同事件更正只允许停留在独立复核位置", key))

        for event in shared:
            old_resolution = old[event].get("controller_resolution")
            new_resolution = new[event].get("controller_resolution")
            if old_resolution == new_resolution:
                continue
            if key == "creation_reviews":
                allowed_resolution = same_position and after_phase in {"human_plan_confirming", "plan_revising"}
            else:
                allowed_resolution = before_phase == "independent_reviewing" and after_phase in {
                    "independent_reviewing",
                    "controller_checking",
                    "plan_revising",
                    "closure_preparing",
                }
            if not allowed_resolution:
                issues.append(_issue("Controller resolution 只能在对应 review 的处置边界内更新", key))
    return issues


def _validate_approval_ownership(
    before: Mapping[str, object],
    after: Mapping[str, object],
    *,
    plan_changed: bool,
) -> list[FactIssue]:
    if _same_presence_and_value(before, after, "execution_approval"):
        return []

    before_phase = before.get("phase")
    after_phase = after.get("phase")
    old = before.get("execution_approval")
    new = after.get("execution_approval")
    allowed = False

    if (before_phase, after_phase) in {
        ("human_plan_confirming", "executing"),
        ("human_plan_confirming", "controller_checking"),
    }:
        allowed = old is None and isinstance(new, dict)

    issues: list[FactIssue] = []
    if not allowed:
        issues.append(
            _issue("execution approval 只能由首次 Human 计划确认边形成，Gate1 后必须保持原样", "execution_approval")
        )
    if isinstance(new, dict) and new.get("subject_version") != after.get("plan_version") and old is None:
        issues.append(_issue("首次 execution approval 必须记录 Gate1 当时 plan_version", "execution_approval.subject_version"))
    return issues


def _validate_plan_replacement(before: Mapping[str, object], after: Mapping[str, object]) -> list[FactIssue]:
    issues: list[FactIssue] = []
    old_items = _items(before)
    new_items = _items(after)

    removed_execution_items = sorted(
        item_id for item_id in old_items.keys() - new_items.keys() if _item_has_execution_facts(old_items[item_id])
    )
    if removed_execution_items and not _plan_replacement_carrier_updated(before, after):
        issues.append(
            _issue(
                "PlanΔ 删除已有执行事实的旧 item 时，必须当次更新非空顶层 summary 作为可回读承接载体；"
                "此机械检查不证明自然语言已无损吸收旧事实",
                "work_items",
            )
        )

    for item_id in new_items.keys() - old_items.keys():
        if new_items[item_id].get("status") != "pending":
            issues.append(_issue("PlanΔ 中新 item 只能以 pending 建立", f"work_items[{item_id}].status"))

    for item_id in old_items.keys() & new_items.keys():
        old = old_items[item_id]
        new = new_items[item_id]
        old_status = old.get("status")
        new_status = new.get("status")
        if old_status != "pending" and new_status == "pending":
            issues.append(_issue("PlanΔ 不得把已有执行事实重置为 pending", f"work_items[{item_id}].status"))
        if old_status == new_status and old_status != "pending" and _item_runtime(old) != _item_runtime(new):
            issues.append(_issue("PlanΔ 保留的已有 item 执行快照必须原样保留", f"work_items[{item_id}]"))
        allowed_settlement = {
            "pending": {"pending", "blocked", "cancelled"},
            "in_progress": {"in_progress", "blocked", "cancelled"},
            "blocked": {"blocked", "cancelled"},
            "completed": {"completed", "cancelled"},
            "cancelled": {"cancelled"},
        }
        if isinstance(old_status, str) and new_status not in allowed_settlement.get(old_status, set()):
            issues.append(_issue("PlanΔ 中既有 item 的执行事实只能保留或据实收敛", f"work_items[{item_id}].status"))
    return issues


def _validate_executing_item_edges(
    before: Mapping[str, object],
    after: Mapping[str, object],
    *,
    entering_controller_check: bool,
) -> list[FactIssue]:
    issues: list[FactIssue] = []
    old_items = _items(before)
    new_items = _items(after)
    if old_items.keys() != new_items.keys():
        return [_issue("非 PlanΔ 的执行更新不得增加或删除 work item", "work_items")]

    edges = {
        ("pending", "in_progress"),
        ("pending", "blocked"),
        ("pending", "completed"),
        ("pending", "cancelled"),
        ("in_progress", "blocked"),
        ("in_progress", "completed"),
        ("in_progress", "cancelled"),
        ("blocked", "in_progress"),
        ("blocked", "completed"),
        ("blocked", "cancelled"),
    }
    dependency_gated = {
        ("pending", "in_progress"),
        ("pending", "blocked"),
        ("pending", "completed"),
        ("blocked", "in_progress"),
    }
    for item_id, old in old_items.items():
        new = new_items[item_id]
        edge = old.get("status"), new.get("status")
        if edge[0] != edge[1] and edge not in edges:
            issues.append(_issue("work item 状态转换不在当前允许边中", f"work_items[{item_id}].status"))
        if edge in dependency_gated and not _dependencies_completed(new, new_items):
            issues.append(
                _issue(
                    "item 开始、解阻或直接完成前，全部 depends_on 目标必须为 completed",
                    f"work_items[{item_id}].depends_on",
                )
            )

    if entering_controller_check:
        if not all_terminal(after):
            issues.append(_issue("executing 进入 controller_checking 时全部 item 必须 terminal", "work_items"))
    elif all_terminal(after):
        issues.append(
            _issue(
                "最后一个 item 进入 terminal 必须同事务转入 controller_checking，禁止 executing + AllTerminal",
                "phase",
            )
        )
    return issues


def _validate_blocked_status_edge(before: Mapping[str, object], after: Mapping[str, object]) -> list[FactIssue]:
    """Validate the narrow same-phase block/unblock checkpoint."""

    issues: list[FactIssue] = []
    before_status = before.get("status")
    after_status = after.get("status")
    changed = _changed_fields(before, after)
    work_items_changed = _normalized_items(before) != _normalized_items(after)
    if "work_items" in changed and not work_items_changed:
        changed.remove("work_items")

    if before_status == after_status == "blocked":
        allowed = _BLOCKED_OVERLAY_FIELDS | _BLOCKED_FACT_CORRECTION_FIELDS
        for key in sorted(changed - allowed):
            issues.append(
                _issue(
                    "blocked 同 phase 只允许更新顶层阻塞/等待快照及不改变判断对象的事实更正",
                    key,
                )
            )
        return issues

    executing_edge = before.get("phase") == after.get("phase") == "executing"
    approval_recovery = executing_edge and before_status == "blocked" and after_status == "open"
    allowed = set(_BLOCKED_OVERLAY_FIELDS)
    if executing_edge:
        allowed.add("work_items")
    if approval_recovery:
        allowed.add("execution_approval")
    for key in sorted(changed - allowed):
        issues.append(_issue("阻塞或解阻事务不得夹带其它领域变化", key))
    if plan_delta(before, after):
        issues.append(_issue("阻塞或解阻必须保持 canonical plan projection 不变", "work_items"))

    if "execution_approval" in changed:
        old_approval = before.get("execution_approval")
        new_approval = after.get("execution_approval")
        if (
            not approval_recovery
            or not isinstance(old_approval, dict)
            or not isinstance(new_approval, dict)
            or new_approval.get("subject_version") != after.get("plan_version")
        ):
            issues.append(
                _issue(
                    "只有 executing 解阻恢复同一计划时才能原子替换同版 execution approval",
                    "execution_approval",
                )
            )

    if not executing_edge:
        if work_items_changed:
            issues.append(_issue("非 executing phase 的阻塞或解阻必须保持 work items 不变", "work_items"))
        return issues

    old_items = _items(before)
    new_items = _items(after)
    if old_items.keys() != new_items.keys():
        issues.append(_issue("阻塞或解阻不得增加或删除 work item", "work_items"))
        return issues

    entering = before_status == "open" and after_status == "blocked"
    allowed_edges = {("pending", "blocked"), ("in_progress", "blocked")} if entering else {("blocked", "in_progress")}
    for item_id, old in old_items.items():
        new = new_items[item_id]
        edge = old.get("status"), new.get("status")
        if edge[0] == edge[1]:
            if _normalized_items({"work_items": [old]}) != _normalized_items({"work_items": [new]}):
                issues.append(_issue("未受阻塞边影响的 item 必须原样保留", f"work_items[{item_id}]"))
            continue
        if edge not in allowed_edges:
            direction = "进入整体阻塞" if entering else "解除整体阻塞"
            issues.append(_issue(f"{direction}时 item 状态边不在当前闭集中", f"work_items[{item_id}].status"))
            continue
        if edge in {("pending", "blocked"), ("blocked", "in_progress")} and not _dependencies_completed(new, new_items):
            issues.append(
                _issue(
                    "item 进入 blocked 或实际解阻前，全部 depends_on 目标必须为 completed",
                    f"work_items[{item_id}].depends_on",
                )
            )
    return issues


def _validate_controller_return_to_execution(
    before: Mapping[str, object], after: Mapping[str, object]
) -> list[FactIssue]:
    issues: list[FactIssue] = []
    old_items = _items(before)
    new_items = _items(after)
    if old_items.keys() != new_items.keys():
        issues.append(_issue("返回 executing 不得增加或删除 work item", "work_items"))
        return issues

    reopened = False
    for item_id, old in old_items.items():
        new = new_items[item_id]
        edge = old.get("status"), new.get("status")
        if edge[0] == edge[1]:
            if _item_runtime(old) != _item_runtime(new):
                issues.append(_issue("未返工的 terminal item 必须保持原样", f"work_items[{item_id}]"))
            continue
        if edge not in {
            ("completed", "in_progress"),
            ("completed", "blocked"),
            ("cancelled", "in_progress"),
            ("cancelled", "blocked"),
        }:
            issues.append(
                _issue(
                    "controller_checking 返工只能把 terminal item 重开为 in_progress 或 blocked",
                    f"work_items[{item_id}].status",
                )
            )
        else:
            reopened = True
    if not reopened:
        issues.append(_issue("返回 executing 必须重开至少一个实际返工 item", "work_items"))
    if all_terminal(after):
        issues.append(_issue("返回 executing 后必须至少存在一个非 terminal item", "work_items"))
    for key in (*_RESULT_PROJECTION_FIELDS, "result_reviews", "closure_proposal"):
        if key in after:
            issues.append(_issue("返回 executing 必须移除旧 projection、review 与 proposal", key))
    return issues


def _validate_result_versions(
    before: Mapping[str, object],
    after: Mapping[str, object],
    *,
    plan_changed: bool,
) -> tuple[list[FactIssue], bool]:
    issues: list[FactIssue] = []
    if plan_changed:
        return issues, False

    before_version = _version(before, "result_version")
    after_version = _version(after, "result_version")
    changed = _result_projection_changed(before, after)
    edge = before.get("phase"), after.get("phase")
    first_result_edges = {
        ("human_plan_confirming", "controller_checking"),
        ("plan_revising", "controller_checking"),
        ("executing", "controller_checking"),
    }

    if before_version is None and after_version is not None:
        if edge not in first_result_edges or after_version != 1:
            issues.append(_issue("result_version 首次只能在列明的结果入口建立为 1", "result_version"))
    elif before_version is not None and after_version is None:
        issues.append(_issue("同一 plan_version 下不得删除已分配的 result_version", "result_version"))
    elif before_version is not None and after_version is not None:
        if after_version < before_version:
            issues.append(_issue("result_version 不得减少", "result_version"))
        elif after_version > before_version:
            if after_version != before_version + 1:
                issues.append(_issue("ResultΔ 只能使 result_version 精确加 1", "result_version"))
            if not _reviewed(before) or not changed:
                issues.append(_issue("只有首条 review 后实际发生 ResultΔ 才能递增 result_version", "result_version"))
            if "result_reviews" in after or "closure_proposal" in after:
                issues.append(_issue("ResultΔ 升版必须同事务清除旧 review 与 proposal", "result_reviews"))
        elif changed and _reviewed(before):
            issues.append(_issue("首条 result review 后发生 ResultΔ 必须精确升版并清旧 review", "result_version"))

        if after_version > before_version and not changed:
            issues.append(_issue("canonical result projection 未变化时不得递增 result_version", "result_version"))
    return issues, changed


def _validate_plan_versions(before: Mapping[str, object], after: Mapping[str, object]) -> tuple[list[FactIssue], bool]:
    issues: list[FactIssue] = []
    changed = plan_delta(before, after)
    before_version = _version(before, "plan_version")
    after_version = _version(after, "plan_version")
    if changed:
        edge = before.get("phase"), after.get("phase")
        approved = isinstance(before.get("execution_approval"), dict)
        allowed_approved_edges = {
            ("executing", "plan_revising"),
            ("controller_checking", "plan_revising"),
            ("independent_reviewing", "plan_revising"),
            ("closure_preparing", "plan_revising"),
            ("plan_revising", "executing"),
            ("plan_revising", "controller_checking"),
        }
        pre_gate_candidate_exit = (
            not approved
            and "execution_approval" not in after
            and edge == ("plan_revising", "human_plan_confirming")
        )
        if approved and edge not in allowed_approved_edges:
            issues.append(_issue("Gate1 后 PlanΔ 只能经 Controller 自动修订边形成", "phase"))
        elif not approved and not pre_gate_candidate_exit:
            issues.append(_issue("Gate1 前 PlanΔ 只能在 plan_revising 返回 Human Gate1 时形成", "phase"))
        if before_version is None or after_version != before_version + 1:
            issues.append(_issue("PlanΔ 必须使 plan_version 精确加 1", "plan_version"))
        for key in _PLAN_REPLACEMENT_RESET_FIELDS:
            if key in after:
                issues.append(_issue("PlanΔ 必须清除旧 result、result review 与 proposal", key))
        reviews = after.get("creation_reviews")
        if not isinstance(reviews, list) or not reviews:
            issues.append(_issue("PlanΔ 必须同事务形成 fresh current plan reviews", "creation_reviews"))
        if approved:
            if not _same_presence_and_value(before, after, "execution_authorization"):
                issues.append(_issue("Gate1 后 PlanΔ 必须保持 execution_authorization 原样", "execution_authorization"))
            if not _same_presence_and_value(before, after, "execution_approval"):
                issues.append(_issue("Gate1 后 PlanΔ 必须保持 execution_approval 原样", "execution_approval"))
        issues.extend(_validate_plan_replacement(before, after))
    else:
        if before_version != after_version:
            issues.append(_issue("canonical plan projection 未变化时 plan_version 必须保持不变", "plan_version"))
    return issues, changed


def _validate_same_phase(
    before: Mapping[str, object],
    after: Mapping[str, object],
    *,
    result_changed: bool,
) -> list[FactIssue]:
    phase = after.get("phase")
    issues: list[FactIssue] = []
    if phase == "human_plan_confirming":
        issues.extend(
            _require_equal(
                before,
                after,
                (
                    "work_items",
                    "execution_authorization",
                    *_RESULT_STATE_FIELDS,
                    "execution_approval",
                    "closure_proposal",
                ),
                "方案待确认时该字段不属于同 phase 更新边界",
            )
        )
    elif phase == "plan_revising":
        issues.extend(
            _require_equal(
                before,
                after,
                (
                    "work_items",
                    "execution_authorization",
                    "execution_approval",
                    "creation_reviews",
                    *_RESULT_STATE_FIELDS,
                    "closure_proposal",
                ),
                "plan_revising 必须冻结原计划、item、结果与 review",
            )
        )
    elif phase == "executing":
        issues.extend(
            _require_equal(before, after, _RESULT_STATE_FIELDS + ("closure_proposal",), "executing 不得改写结果上下文")
        )
        issues.extend(_validate_executing_item_edges(before, after, entering_controller_check=False))
    elif phase == "controller_checking":
        issues.extend(_require_equal(before, after, ("closure_proposal",), "controller_checking 不得形成 proposal"))
        old_items = _items(before)
        new_items = _items(after)
        for item_id in old_items.keys() & new_items.keys():
            old_status = old_items[item_id].get("status")
            new_status = new_items[item_id].get("status")
            if old_status != new_status and {old_status, new_status} != {"completed", "cancelled"}:
                issues.append(
                    _issue(
                        "controller_checking 内只允许 completed/cancelled 终态分类更正", f"work_items[{item_id}].status"
                    )
                )
            elif old_status != new_status and old_items[item_id].get("result_summary") == new_items[item_id].get(
                "result_summary"
            ):
                issues.append(
                    _issue(
                        "completed/cancelled 终态分类更正必须同时更新实际 result_summary",
                        f"work_items[{item_id}].result_summary",
                    )
                )
        if not all_terminal(after):
            issues.append(_issue("controller_checking 必须保持全部 item terminal", "work_items"))
    elif phase == "independent_reviewing":
        issues.extend(
            _require_equal(
                before,
                after,
                ("work_items", "result_version", *_RESULT_PROJECTION_FIELDS, "closure_proposal"),
                "independent_reviewing 必须冻结被审 result projection",
            )
        )
    elif phase == "closure_preparing":
        issues.extend(
            _require_equal(
                before, after, ("work_items", *_RESULT_STATE_FIELDS), "closure_preparing 必须冻结结果、版本与 reviews"
            )
        )
        if (
            "closure_proposal" in before
            and "closure_proposal" in after
            and not _same_presence_and_value(before, after, "closure_proposal")
        ):
            issues.append(
                _issue(
                    "已有 closure proposal 必须先整体移除，不能在同一稳定快照直接改写为另一份 proposal",
                    "closure_proposal",
                )
            )
    elif phase == "human_closure_confirming":
        issues.extend(
            _require_equal(
                before,
                after,
                ("work_items", *_RESULT_STATE_FIELDS, "closure_proposal", "relations"),
                "Human 关闭判断对象在同 phase 必须冻结",
            )
        )
    if phase not in _ACTIVE_PHASES:
        issues.append(_issue("WorkCase phase 不在当前闭集中", "phase"))
    if result_changed and phase not in {"controller_checking"}:
        issues.append(_issue("ResultΔ 只能在 controller_checking 形成", "phase"))
    return issues


def _validate_phase_edge(
    before: Mapping[str, object],
    after: Mapping[str, object],
    *,
    plan_changed: bool,
    result_changed: bool,
) -> list[FactIssue]:
    issues: list[FactIssue] = []
    edge = before.get("phase"), after.get("phase")
    if edge not in _WORKCASE_PHASE_EDGES:
        return [_issue("WorkCase phase 转换不在当前允许边中", "phase")]

    # Only these source phases give waiting_on one unambiguous Human Gate owner.  Exact
    # equality rejects a definitely stale Human Gate snapshot.  A changed string is only
    # structurally admissible; it does not prove the new waiting is semantically true.
    if (
        edge in _GATE_WAITING_EXIT_EDGES
        and "waiting_on" in before
        and _same_presence_and_value(before, after, "waiting_on")
    ):
        issues.append(
            _issue(
                "离开 Human/Reviewer 关口时，原关口 waiting_on 不得原样滞留",
                "waiting_on",
            )
        )

    if edge == ("human_plan_confirming", "plan_revising"):
        issues.extend(
            _require_equal(
                before,
                after,
                ("work_items", "execution_authorization", "creation_reviews", *_RESULT_STATE_FIELDS),
                "Gate1 前进入 plan_revising 必须冻结原 authorization、plan、items 与 reviews",
            )
        )
        if "execution_approval" in after:
            issues.append(_issue("Gate1 前 plan_revising 禁止形成 execution approval", "execution_approval"))

    elif edge == ("human_plan_confirming", "executing"):
        issues.extend(_require_equal(before, after, ("work_items",), "批准当前计划进入执行时 work items 必须保持不变"))
        if not isinstance(after.get("execution_approval"), dict):
            issues.append(_issue("进入 executing 必须同事务写当前计划 execution approval", "execution_approval"))
        issues.extend(required_quality_gate_issues(after))
        if any(key in after for key in _RESULT_STATE_FIELDS):
            issues.append(_issue("首次进入 executing 不得携带结果上下文", "result_version"))
        if all_terminal(after):
            issues.append(_issue("进入 executing 必须至少存在一个非 terminal item", "work_items"))

    elif edge == ("human_plan_confirming", "controller_checking"):
        if no_execution_facts(before):
            old_items = _items(before)
            new_items = _items(after)
            if old_items.keys() != new_items.keys() or any(
                old_items[item_id].get("status") != "pending" or new_items[item_id].get("status") != "cancelled"
                for item_id in old_items.keys() & new_items.keys()
            ):
                issues.append(_issue("前置执行终止必须把全部 pending item 精确收敛为 cancelled", "work_items"))
            if "execution_approval" in after:
                issues.append(_issue("前置执行终止链禁止补造 execution approval", "execution_approval"))
        else:
            issues.extend(
                _require_equal(before, after, ("work_items",), "已 terminal 计划获批进入结果链时 item 必须保持不变")
            )
            if not isinstance(after.get("execution_approval"), dict):
                issues.append(_issue("正常进入结果链必须写当前计划 execution approval", "execution_approval"))
            else:
                issues.extend(required_quality_gate_issues(after))
        if not all_terminal(after):
            issues.append(_issue("进入 controller_checking 必须全部 item terminal", "work_items"))

    elif edge == ("plan_revising", "human_plan_confirming"):
        if "execution_approval" in before or "execution_approval" in after:
            issues.append(_issue("Gate1 后不得返回 human_plan_confirming", "execution_approval"))
        if not plan_changed:
            issues.extend(
                _require_equal(
                    before,
                    after,
                    ("work_items", *_RESULT_STATE_FIELDS),
                    "无 PlanΔ 返回 Gate1 时必须保持 plan、items 与结果形状",
                )
            )
        old_review_times = {
            review.get("reviewed_at")
            for review in _reviews(before, "creation_reviews").values()
            if isinstance(review.get("reviewed_at"), str)
        }
        new_review_times = {
            review.get("reviewed_at")
            for review in _reviews(after, "creation_reviews").values()
            if isinstance(review.get("reviewed_at"), str)
        }
        if not (new_review_times - old_review_times):
            issues.append(_issue("返回 Gate1 必须形成 fresh current plan review", "creation_reviews"))
        if not isinstance(after.get("waiting_on"), str):
            issues.append(_issue("返回 human_plan_confirming 必须写 Gate1 waiting", "waiting_on"))

    elif edge == ("plan_revising", "executing"):
        if not plan_changed:
            issues.extend(
                _require_equal(
                    before,
                    after,
                    ("work_items", *_RESULT_STATE_FIELDS),
                    "同计划自动调整返回 executing 必须保留 item 与已分配 result_version",
                )
            )
        if not isinstance(after.get("execution_approval"), dict):
            issues.append(_issue("返回 executing 必须有当前计划授权", "execution_approval"))
        if all_terminal(after):
            issues.append(_issue("返回 executing 必须至少一项 item 非 terminal", "work_items"))

    elif edge == ("plan_revising", "controller_checking"):
        if no_execution_facts(before) and "execution_approval" not in before:
            old_items = _items(before)
            new_items = _items(after)
            if old_items.keys() != new_items.keys() or any(
                old_items[item_id].get("status") != "pending" or new_items[item_id].get("status") != "cancelled"
                for item_id in old_items.keys() & new_items.keys()
            ):
                issues.append(_issue("前置执行终止必须把全部 pending item 精确收敛为 cancelled", "work_items"))
            if "execution_approval" in after:
                issues.append(_issue("前置执行终止链必须保持 approval 缺失", "execution_approval"))
        else:
            issues.extend(_validate_executing_item_edges(before, after, entering_controller_check=True))
            if not isinstance(after.get("execution_approval"), dict):
                issues.append(_issue("非前置终止结果链必须保留当前计划 approval", "execution_approval"))
            if "result_version" in before:
                issues.extend(
                    _require_equal(
                        before, after, _RESULT_STATE_FIELDS, "已有结果快照返回 controller_checking 时必须原样保留"
                    )
                )
        if not all_terminal(after):
            issues.append(_issue("进入 controller_checking 必须全部 item terminal", "work_items"))

    elif edge == ("executing", "plan_revising"):
        if not plan_changed:
            issues.extend(
                _require_equal(
                    before,
                    after,
                    ("work_items", *_RESULT_STATE_FIELDS, "execution_approval"),
                    "进入计划自动调整时无 PlanΔ 必须冻结 item、结果版本与既有 approval",
                )
            )

    elif edge == ("executing", "controller_checking"):
        issues.extend(_validate_executing_item_edges(before, after, entering_controller_check=True))

    elif edge == ("controller_checking", "executing"):
        issues.extend(_validate_controller_return_to_execution(before, after))

    elif edge == ("controller_checking", "plan_revising"):
        if not plan_changed:
            issues.extend(
                _require_equal(
                    before,
                    after,
                    ("work_items", *_RESULT_STATE_FIELDS, "execution_approval"),
                    "进入计划自动调整时无 PlanΔ 必须冻结当前计划和结果快照",
                )
            )
        if "closure_proposal" in after:
            issues.append(_issue("进入 plan_revising 必须移除 closure proposal", "closure_proposal"))

    elif edge == ("controller_checking", "independent_reviewing"):
        issues.extend(
            _require_equal(
                before, after, ("work_items", *_RESULT_STATE_FIELDS), "进入独立复核时完整 result projection 必须冻结"
            )
        )
        if not result_projection_complete(after):
            issues.append(
                _issue("进入 independent_reviewing 前 canonical result projection 必须完整", "result_version")
            )

    elif edge == ("controller_checking", "closure_preparing"):
        issues.extend(
            _require_equal(
                before, after, ("work_items", *_RESULT_STATE_FIELDS), "进入关闭准备必须保留已复核结果与 reviews"
            )
        )
        if not _reviews_resolved(before):
            issues.append(_issue("进入 closure_preparing 前至少一项 review 的 feedback 必须全部处置", "result_reviews"))

    elif edge in {
        ("independent_reviewing", "controller_checking"),
        ("independent_reviewing", "plan_revising"),
    }:
        if not (edge[1] == "plan_revising" and plan_changed):
            issues.extend(
                _require_equal(
                    before,
                    after,
                    ("work_items", "result_version", *_RESULT_PROJECTION_FIELDS),
                    "离开独立复核时先原样冻结被审 projection",
                )
            )
        if edge[1] == "plan_revising" and "closure_proposal" in after:
            issues.append(_issue("进入 plan_revising 时 proposal 必须缺失", "closure_proposal"))

    elif edge == ("independent_reviewing", "closure_preparing"):
        issues.extend(
            _require_equal(
                before,
                after,
                ("work_items", "result_version", *_RESULT_PROJECTION_FIELDS),
                "进入关闭准备必须保持被审 projection 不变",
            )
        )
        if not _reviews_resolved(after):
            issues.append(_issue("进入 closure_preparing 前至少一项 review 的 feedback 必须全部处置", "result_reviews"))

    elif edge in {
        ("closure_preparing", "controller_checking"),
        ("closure_preparing", "plan_revising"),
    }:
        if not (edge[1] == "plan_revising" and plan_changed):
            issues.extend(
                _require_equal(
                    before, after, ("work_items", *_RESULT_STATE_FIELDS), "退出关闭准备时先冻结当前结果与 reviews"
                )
            )
        if "closure_proposal" in after:
            issues.append(_issue("退出 closure_preparing 必须移除旧 proposal", "closure_proposal"))

    elif edge == ("closure_preparing", "human_closure_confirming"):
        issues.extend(
            _require_equal(
                before,
                after,
                ("work_items", *_RESULT_STATE_FIELDS, "closure_proposal", "relations"),
                "进入 Human 关闭判断时完整质量链和 proposal 必须冻结",
            )
        )
        if "closure_proposal" not in after:
            issues.append(_issue("进入 human_closure_confirming 必须已有完整 closure proposal", "closure_proposal"))
        if not isinstance(after.get("waiting_on"), str):
            issues.append(_issue("进入 human_closure_confirming 必须写 Human waiting", "waiting_on"))

    elif edge in {
        ("human_closure_confirming", "closure_preparing"),
        ("human_closure_confirming", "controller_checking"),
        ("human_closure_confirming", "plan_revising"),
    }:
        issues.extend(
            _require_equal(
                before, after, ("work_items", *_RESULT_STATE_FIELDS), "Human 退回时必须先冻结当前结果与 reviews"
            )
        )
        if "closure_proposal" in after:
            issues.append(_issue("Human 判断对象退回后必须移除旧 closure proposal", "closure_proposal"))

    result_change_edges = {
        ("human_plan_confirming", "controller_checking"),
        ("plan_revising", "controller_checking"),
        ("executing", "controller_checking"),
        ("controller_checking", "executing"),
    }
    if result_changed and edge not in result_change_edges:
        issues.append(
            _issue("phase 转换时 result projection 必须冻结；实际 ResultΔ 先进入 controller_checking", "phase")
        )
    return issues


def validate_workcase_transition(
    before: dict[str, object],
    after: dict[str, object],
    *,
    operation: WorkCaseOperation = "update",
    repairing_invalid_before: bool = False,
) -> tuple[FactIssue, ...]:
    """Validate one current-contract WorkCase edge.

    WorkCase专属操作不接受 invalid-before；调用方必须先提供一个完全符合
    当前唯一契约的 before。
    """

    issues: list[FactIssue] = []
    before_status = before.get("status")
    after_status = after.get("status")
    before_phase = before.get("phase")
    after_phase = after.get("phase")

    if repairing_invalid_before:
        return (_issue("当前 WorkCase 专属操作不接受 invalid-before 修复", "status"),)

    if operation == "close":
        if before_status != "open" or before_phase != "human_closure_confirming":
            issues.append(_issue("close-workcase 只能消费 open/human_closure_confirming before", "phase"))
        if after_status != "closed" or "phase" in after:
            issues.append(_issue("close-workcase after 必须为无 phase 的 closed 终态", "status"))
        return tuple(issues)

    if operation == "correct":
        if before_status != "closed" or after_status != "closed":
            issues.append(_issue("correct-closed-workcase 只允许 closed → closed", "status"))
        if "phase" in before or "phase" in after:
            issues.append(_issue("closed WorkCase 不得恢复或保存 phase", "phase"))
        return tuple(issues)

    if before_status not in ACTIVE_STATUSES or after_status not in ACTIVE_STATUSES:
        issues.append(_issue("update-workcase 只接受活动期 WorkCase，不能形成或更正 closed", "status"))
        return tuple(issues)
    if before_phase == "human_closure_confirming":
        return (_issue("human_closure_confirming 只能由 close-workcase 消费，禁止 update-workcase", "phase"),)
    if before_phase not in _ACTIVE_PHASES or after_phase not in _ACTIVE_PHASES:
        issues.append(_issue("活动期 WorkCase phase 不在当前七项闭集中", "phase"))
    if safe_convergence_shape(before) and after_phase in {"executing", "plan_revising"}:
        issues.append(
            _issue("SafeConvergenceShape 只能沿结果、复核与关闭链向后收敛", "phase")
        )
    if isinstance(before.get("execution_approval"), dict) and not _same_presence_and_value(
        before, after, "execution_authorization"
    ):
        issues.append(
            _issue("Gate1 后 execution_authorization 必须保持原样", "execution_authorization")
        )

    status_changed = before_status != after_status
    if status_changed:
        if (before_status, after_status) not in {("open", "blocked"), ("blocked", "open")}:
            issues.append(_issue("WorkCase status 转换不在 open/blocked 当前闭集中", "status"))
        if before_phase != after_phase:
            issues.append(_issue("阻塞或解阻不得与 phase 推进合并", "phase"))
    if before_status == "blocked" or after_status == "blocked":
        issues.extend(_validate_blocked_status_edge(before, after))
        return tuple(issues)

    plan_issues, plan_changed = _validate_plan_versions(before, after)
    issues.extend(plan_issues)
    result_issues, result_changed = _validate_result_versions(before, after, plan_changed=plan_changed)
    issues.extend(result_issues)
    result_invalidated = plan_changed or (
        _reviewed(before)
        and result_changed
        and _version(after, "result_version") == (_version(before, "result_version") or 0) + 1
        and "result_reviews" not in after
    )
    issues.extend(
        _validate_review_ownership(
            before,
            after,
            plan_changed=plan_changed,
            result_invalidated=result_invalidated,
        )
    )
    issues.extend(_validate_approval_ownership(before, after, plan_changed=plan_changed))

    if before_phase == after_phase:
        issues.extend(_validate_same_phase(before, after, result_changed=result_changed))
    else:
        issues.extend(
            _validate_phase_edge(
                before,
                after,
                plan_changed=plan_changed,
                result_changed=result_changed,
            )
        )
    return tuple(issues)


def validate_fact_transition(
    fact_type_key: str,
    before: dict[str, object],
    after: dict[str, object],
    *,
    repairing_invalid_before: bool = False,
    workcase_operation: WorkCaseOperation = "update",
) -> tuple[FactIssue, ...]:
    """Validate the mechanically observable edge between two full snapshots."""

    issues: list[FactIssue] = []
    before_updated = parse_rfc3339(before.get("updated_at"))
    after_updated = parse_rfc3339(after.get("updated_at"))
    if before_updated is not None and after_updated is not None and after_updated <= before_updated:
        issues.append(_issue("实际更新的 updated_at 必须晚于当前值", "updated_at"))

    if fact_type_key == "workcase":
        issues.extend(
            validate_workcase_transition(
                before,
                after,
                operation=workcase_operation,
                repairing_invalid_before=repairing_invalid_before,
            )
        )
        return tuple(issues)

    before_status = before.get("status")
    after_status = after.get("status")
    if fact_type_key == "pitfall" and repairing_invalid_before and before_status == "retired":
        if after_status != "discarded":
            issues.append(
                _issue(
                    "legacy retired Pitfall 只能修复为 discarded",
                    "status",
                )
            )
        legacy_changed = _changed_fields(before, after) - {"updated_at", "status", "change_log"}
        if legacy_changed:
            issues.append(
                _issue(
                    "legacy retired Pitfall 修复必须保留正文、关系与处置不变",
                    sorted(legacy_changed)[0],
                )
            )
    if (
        not repairing_invalid_before
        and before_status != after_status
        and (before_status, after_status) not in _STATUS_EDGES[fact_type_key]
    ):
        issues.append(_issue("status 转换不在当前单对象更新允许边中", "status"))
    if fact_type_key == "pitfall" and before_status != after_status:
        changed = _changed_fields(before, after) - {"updated_at", "change_log"}
        allowed = {"status"}
        if (before_status, after_status) in {("draft", "discarded"), ("active", "discarded")}:
            allowed.add("disposition_summary")
        if changed - allowed:
            issues.append(_issue("Pitfall 生命周期转换不得夹带正文或引用更正", sorted(changed - allowed)[0]))
        if (before_status, after_status) == ("draft", "active") and "disposition_summary" in after:
            issues.append(_issue("Pitfall promote 只执行 draft → active", "disposition_summary"))
    return tuple(issues)


__all__ = ["WorkCaseOperation", "validate_fact_transition", "validate_workcase_transition"]
