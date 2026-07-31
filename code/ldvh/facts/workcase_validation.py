"""Mechanical single-snapshot validation for the current WorkCase contract."""

from __future__ import annotations

import re
from collections import deque
from collections.abc import Mapping, Sequence

from ldvh.facts.contracts import ACTIVE_STATUSES, LAYOUTS
from ldvh.facts.models import FactIssue
from ldvh.facts.workcase_projection import (
    all_terminal,
    approval_baseline_fingerprint,
    no_execution_facts,
    result_projection_complete,
    safe_convergence_shape,
)

ACTIVE_PHASES = frozenset(
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
ITEM_STATUSES = frozenset({"pending", "in_progress", "blocked", "completed", "cancelled"})
REVIEW_CONCLUSIONS = frozenset({"pass", "pass_with_followups", "changes_required", "blocked"})
CRITERION_OUTCOMES = frozenset({"satisfied", "not_satisfied", "not_verified"})
CLOSURE_OUTCOMES = frozenset({"completed", "partial", "not-achieved", "cancelled"})

_ITEM_ID = re.compile(r"item-[a-z0-9][a-z0-9-]*\Z")
_CRITERION_ID = re.compile(r"criterion-[a-z0-9][a-z0-9-]*\Z")
_RESIDUAL_ID = re.compile(r"residual-[a-z0-9][a-z0-9-]*\Z")
_SUGGESTION_ID = re.compile(r"suggestion-[a-z0-9][a-z0-9-]*\Z")
_WORKCASE_ID = re.compile(r"workcase-[0-9]{4,}\Z")
_AUTHORIZATION_ID = re.compile(r"authorization-[a-z0-9][a-z0-9-]*\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")

_RESULT_PROJECTION_FIELDS = frozenset(
    {"success_criterion_results", "result_summary", "controller_check_summary", "validation_summary"}
)
_RESULT_CHAIN_FIELDS = frozenset(
    {"result_version", *_RESULT_PROJECTION_FIELDS, "result_reviews", "closure_proposal"}
)
_TERMINAL_FIELDS = frozenset(
    {"closure_outcome", "disposition_summary", "residual_responsibilities", "spark_suggestions"}
)
_CLOSED_REQUIRED = frozenset(
    {
        "object_id",
        "fact_type_key",
        "title",
        "created_at",
        "updated_at",
        "status",
        "goal",
        "scope",
        "success_criterion_definitions",
        "success_criterion_results",
        "result_summary",
        "validation_summary",
        "closure_outcome",
        "disposition_summary",
    }
)
_CLOSED_ALLOWED = frozenset(
    {*_CLOSED_REQUIRED, "residual_responsibilities", "spark_suggestions", "relations", "urls"}
)


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _issue(issues: list[FactIssue], summary: str, path: str) -> None:
    issues.append(FactIssue("schema", summary, path))


def _require(
    fields: Mapping[str, object],
    names: Sequence[str] | set[str] | frozenset[str],
    issues: list[FactIssue],
    *,
    context: str,
) -> None:
    for name in sorted(names):
        if name not in fields:
            _issue(issues, f"{context}要求该字段", name)


def _forbid(
    fields: Mapping[str, object],
    names: Sequence[str] | set[str] | frozenset[str],
    issues: list[FactIssue],
    *,
    context: str,
) -> None:
    for name in sorted(names):
        if name in fields:
            _issue(issues, f"{context}禁止该字段", name)


def _validate_unique_strings(value: object, path: str, issues: list[FactIssue]) -> list[str]:
    if not isinstance(value, list) or not value:
        _issue(issues, "字段出现时必须是非空 array", path)
        return []
    strings: list[str] = []
    for index, member in enumerate(value):
        member_path = f"{path}[{index}]"
        if not _nonempty_string(member):
            _issue(issues, "array 成员必须是非空 string", member_path)
            continue
        strings.append(member)
    if len(strings) != len(set(strings)):
        _issue(issues, "array 成员不得重复", path)
    return strings


def _validate_criteria(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    definitions = fields.get("success_criterion_definitions")
    definition_ids: list[str] = []
    if definitions is not None and (not isinstance(definitions, list) or not definitions):
        _issue(issues, "success_criterion_definitions 必须是非空 array", "success_criterion_definitions")
    if isinstance(definitions, list):
        for index, definition in enumerate(definitions):
            path = f"success_criterion_definitions[{index}]"
            if not isinstance(definition, Mapping):
                continue
            criterion_id = definition.get("criterion_id")
            if isinstance(criterion_id, str):
                definition_ids.append(criterion_id)
                if _CRITERION_ID.fullmatch(criterion_id) is None:
                    _issue(issues, "criterion_id 格式不符合当前闭集", f"{path}.criterion_id")
            if not _nonempty_string(definition.get("statement")):
                _issue(issues, "成功标准 statement 必须是非空 string", f"{path}.statement")
        if len(definition_ids) != len(set(definition_ids)):
            _issue(issues, "criterion_id 在同一 WorkCase 内不得重复", "success_criterion_definitions")

    results = fields.get("success_criterion_results")
    if results is not None and (not isinstance(results, list) or not results):
        _issue(issues, "success_criterion_results 出现时必须是非空 array", "success_criterion_results")
    if not isinstance(results, list):
        return
    result_ids: list[str] = []
    for index, result in enumerate(results):
        path = f"success_criterion_results[{index}]"
        if not isinstance(result, Mapping):
            continue
        criterion_id = result.get("criterion_id")
        if isinstance(criterion_id, str):
            result_ids.append(criterion_id)
            if _CRITERION_ID.fullmatch(criterion_id) is None:
                _issue(issues, "criterion_id 格式不符合当前闭集", f"{path}.criterion_id")
        if result.get("outcome") not in CRITERION_OUTCOMES:
            _issue(issues, "criterion outcome 不在当前闭集中", f"{path}.outcome")
        if not _nonempty_string(result.get("summary")):
            _issue(issues, "成功标准结果 summary 必须是非空 string", f"{path}.summary")
    if len(result_ids) != len(set(result_ids)):
        _issue(issues, "criterion_id 在结果数组中不得重复", "success_criterion_results")
    if definitions is not None and (
        len(definition_ids) != len(definitions)
        or len(result_ids) != len(results)
        or set(result_ids) != set(definition_ids)
    ):
        _issue(
            issues,
            "success_criterion_results 必须按 criterion_id 精确覆盖全部当前成功标准",
            "success_criterion_results",
        )


def _validate_items(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    raw_items = fields.get("work_items")
    if raw_items is not None and (not isinstance(raw_items, list) or not raw_items):
        _issue(issues, "work_items 必须是非空 array", "work_items")
    if not isinstance(raw_items, list):
        return

    item_ids: list[str] = []
    statuses: dict[str, object] = {}
    for index, item in enumerate(raw_items):
        if not isinstance(item, Mapping):
            continue
        item_id = item.get("item_id")
        if isinstance(item_id, str):
            item_ids.append(item_id)
            statuses[item_id] = item.get("status")
            if _ITEM_ID.fullmatch(item_id) is None:
                _issue(issues, "item_id 格式不符合当前闭集", f"work_items[{index}].item_id")
    if len(item_ids) != len(set(item_ids)):
        _issue(issues, "work_items.item_id 不得重复", "work_items")

    known = set(item_ids)
    graph: dict[str, set[str]] = {item_id: set() for item_id in known}
    for index, item in enumerate(raw_items):
        if not isinstance(item, Mapping):
            continue
        path = f"work_items[{index}]"
        item_id = item.get("item_id")
        status = item.get("status")
        if status not in ITEM_STATUSES:
            _issue(issues, "work item status 不在当前闭集中", f"{path}.status")
            continue

        conditional = {"current_summary", "resume_from", "blocking_summary", "result_summary"}
        if status == "pending":
            required: set[str] = set()
            allowed: set[str] = set()
        elif status == "in_progress":
            required = {"current_summary", "resume_from"}
            allowed = set(required)
        elif status == "blocked":
            required = {"current_summary", "blocking_summary"}
            allowed = {"current_summary", "blocking_summary", "resume_from"}
        else:
            required = {"result_summary"}
            allowed = set(required)
        _require(item, required, issues, context=f"{status} work item ")
        for name in sorted((conditional - allowed) & set(item)):
            _issue(issues, f"{status} work item 禁止该字段", f"{path}.{name}")

        template_keys = item.get("template_keys")
        if template_keys is not None:
            _validate_unique_strings(template_keys, f"{path}.template_keys", issues)
        if "template_deviation_summary" in item and "template_keys" not in item:
            _issue(
                issues,
                "template_deviation_summary 只可与实际选择的 template_keys 同时出现",
                f"{path}.template_deviation_summary",
            )

        dependencies = item.get("depends_on")
        if dependencies is None:
            continue
        dependency_ids = _validate_unique_strings(dependencies, f"{path}.depends_on", issues)
        for target_index, target in enumerate(dependency_ids):
            target_path = f"{path}.depends_on[{target_index}]"
            if target not in known:
                _issue(issues, "depends_on 目标不存在", target_path)
                continue
            if target == item_id:
                _issue(issues, "work item 不得依赖自身", target_path)
                continue
            if isinstance(item_id, str):
                graph[item_id].add(target)
            if status in {"in_progress", "blocked", "completed"} and statuses.get(target) != "completed":
                _issue(issues, "已开始或完成的 work item 只能依赖 completed item", target_path)

    indegree = {node: 0 for node in graph}
    for targets in graph.values():
        for target in targets:
            indegree[target] += 1
    ready = deque(node for node, degree in indegree.items() if degree == 0)
    removed = 0
    while ready:
        node = ready.popleft()
        removed += 1
        for target in graph[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)

    if removed != len(graph):
        _issue(issues, "work item depends_on 有向图不得成环", "work_items")


def _validate_reviews(
    fields: Mapping[str, object],
    array_name: str,
    version_name: str,
    issues: list[FactIssue],
) -> None:
    values = fields.get(array_name)
    if values is None:
        return
    if not isinstance(values, list) or not values:
        _issue(issues, "review 数组出现时必须非空", array_name)
        return
    version = fields.get(version_name)
    phase = fields.get("phase")
    event_keys: list[tuple[str, str, int]] = []
    for index, review in enumerate(values):
        path = f"{array_name}[{index}]"
        if not isinstance(review, Mapping):
            continue
        reviewer = review.get("reviewer")
        reviewed_at = review.get("reviewed_at")
        subject_version = review.get("subject_version")
        if not _nonempty_string(reviewer):
            _issue(issues, "reviewer 必须是非空 string", f"{path}.reviewer")
        if not _nonempty_string(reviewed_at):
            _issue(issues, "reviewed_at 必须是非空 RFC 3339 string", f"{path}.reviewed_at")
        if not _positive_integer(subject_version):
            _issue(issues, "review subject_version 必须是正整数", f"{path}.subject_version")
        if not _nonempty_string(review.get("scope")):
            _issue(issues, "review scope 必须是非空 string", f"{path}.scope")
        if isinstance(reviewer, str) and isinstance(reviewed_at, str) and _positive_integer(subject_version):
            event_keys.append((reviewer, reviewed_at, subject_version))
        if _positive_integer(version) and review.get("subject_version") != version:
            _issue(issues, f"review 必须绑定当前 {version_name}", f"{path}.subject_version")
        conclusion = review.get("conclusion")
        if conclusion not in REVIEW_CONCLUSIONS:
            _issue(issues, "review conclusion 不在当前闭集中", f"{path}.conclusion")
        feedback = review.get("feedback")
        feedback_values: list[str] = []
        if feedback is not None:
            feedback_values = _validate_unique_strings(feedback, f"{path}.feedback", issues)
        if conclusion in {"pass_with_followups", "changes_required", "blocked"} and not feedback_values:
            _issue(issues, "非 pass review 必须包含实际 feedback", f"{path}.feedback")
        resolution = review.get("controller_resolution")
        if resolution is not None and not _nonempty_string(resolution):
            _issue(issues, "controller_resolution 出现时必须是非空 string", f"{path}.controller_resolution")
        if resolution is not None and not feedback_values:
            _issue(issues, "没有 feedback 的 review 禁止 Controller resolution", f"{path}.controller_resolution")
        needs_resolution = array_name == "creation_reviews" or phase != "independent_reviewing"
        if feedback_values and needs_resolution and not _nonempty_string(resolution):
            _issue(issues, "离开独立复核前必须处置全部 feedback", f"{path}.controller_resolution")
    if len(event_keys) != len(set(event_keys)):
        _issue(issues, "同一 review 事件三元组不得重复", array_name)


def _validate_execution_approval(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    approval = fields.get("execution_approval")
    if approval is None:
        return
    if not isinstance(approval, Mapping):
        return
    if not _positive_integer(approval.get("subject_version")):
        _issue(issues, "execution approval subject_version 必须是正整数", "execution_approval.subject_version")
    if not _nonempty_string(approval.get("approved_at")):
        _issue(issues, "execution approval approved_at 必须是非空 RFC 3339 string", "execution_approval.approved_at")
    if not _nonempty_string(approval.get("summary")):
        _issue(issues, "execution approval summary 必须是非空 string", "execution_approval.summary")
    if (
        _positive_integer(fields.get("plan_version"))
        and _positive_integer(approval.get("subject_version"))
        and approval.get("subject_version") > fields.get("plan_version")
    ):
        _issue(issues, "execution approval subject_version 不得晚于当前 plan_version", "execution_approval.subject_version")
    baseline = approval.get("baseline_fingerprint")
    if not isinstance(baseline, str) or _SHA256.fullmatch(baseline) is None:
        _issue(issues, "execution approval baseline_fingerprint 必须是 64 位小写 SHA-256", "execution_approval.baseline_fingerprint")
    elif baseline != approval_baseline_fingerprint(fields):
        _issue(issues, "execution approval baseline_fingerprint 与当前批准基线不一致", "execution_approval.baseline_fingerprint")
    source_refs = approval.get("source_refs")
    _validate_unique_strings(source_refs, "execution_approval.source_refs", issues)


def _validate_execution_authorization(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    value = fields.get("execution_authorization")
    if not isinstance(value, Mapping):
        return
    actions = value.get("authorized_actions")
    action_ids: list[str] = []
    if not isinstance(actions, list) or not actions:
        _issue(issues, "authorized_actions 必须是非空 array", "execution_authorization.authorized_actions")
    else:
        required = {
            "action_id",
            "summary",
            "target_scope",
            "effect_scope",
            "risk_summary",
            "rollback_summary",
            "rule_refs",
        }
        for index, action in enumerate(actions):
            path = f"execution_authorization.authorized_actions[{index}]"
            if not isinstance(action, Mapping):
                continue
            _require(action, required, issues, context="authorized action ")
            action_id = action.get("action_id")
            if _nonempty_string(action_id):
                action_ids.append(str(action_id))
                if _AUTHORIZATION_ID.fullmatch(str(action_id)) is None:
                    _issue(issues, "action_id 格式不符合当前闭集", f"{path}.action_id")
            for name in required - {"action_id", "rule_refs"}:
                if not _nonempty_string(action.get(name)):
                    _issue(issues, "authorized action 文本成员必须是非空 string", f"{path}.{name}")
            rule_refs = action.get("rule_refs")
            _validate_unique_strings(rule_refs, f"{path}.rule_refs", issues)
        if len(action_ids) != len(set(action_ids)):
            _issue(issues, "authorized action_id 不得重复", "execution_authorization.authorized_actions")
    for name in (
        "action_ceiling",
        "allowed_adjustments",
        "verification_and_rollback",
        "out_of_bounds_handling",
    ):
        if not _nonempty_string(value.get(name)):
            _issue(issues, "execution authorization 文本成员必须是非空 string", f"execution_authorization.{name}")
    for name in ("prohibited_actions", "human_prerequisites"):
        if name in value:
            _validate_unique_strings(value.get(name), f"execution_authorization.{name}", issues)


def _result_outcomes(fields: Mapping[str, object]) -> list[str]:
    values = fields.get("success_criterion_results")
    if not isinstance(values, list):
        return []
    return [
        str(value["outcome"])
        for value in values
        if isinstance(value, Mapping) and value.get("outcome") in CRITERION_OUTCOMES
    ]


def _validate_outcome(
    outcome: object,
    fields: Mapping[str, object],
    path: str,
    issues: list[FactIssue],
) -> None:
    if outcome not in CLOSURE_OUTCOMES:
        _issue(issues, "closure outcome 不在当前闭集中", path)
        return
    outcomes = _result_outcomes(fields)
    if not outcomes:
        return
    satisfied = sum(value == "satisfied" for value in outcomes)
    not_satisfied = sum(value == "not_satisfied" for value in outcomes)
    not_verified = sum(value == "not_verified" for value in outcomes)
    incomplete = not_satisfied + not_verified
    if outcome == "completed" and incomplete:
        _issue(issues, "completed 要求全部成功标准均为 satisfied", path)
    elif outcome == "partial" and not (satisfied and incomplete):
        _issue(issues, "partial 要求同时存在 satisfied 与未满足或未验证标准", path)
    elif satisfied == len(outcomes) and outcome != "completed":
        _issue(issues, "全部成功标准 satisfied 时只能形成 completed", path)
    elif satisfied and incomplete and outcome != "partial":
        _issue(issues, "部分标准 satisfied 时只能形成 partial", path)
    elif not satisfied and not_verified and outcome != "cancelled":
        _issue(issues, "没有 satisfied 且仍有 not_verified 时只能形成 cancelled", path)
    elif not satisfied and not_verified == 0 and not_satisfied and outcome != "not-achieved":
        _issue(issues, "没有 satisfied 且全部标准均为 not_satisfied 时只能形成 not-achieved", path)


def _validate_suggestions(value: object, path: str, issues: list[FactIssue]) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, list) or not value:
        _issue(issues, "spark_suggestions 出现时必须是非空 array", path)
        return {}
    kinds: dict[str, str] = {}
    for index, suggestion in enumerate(value):
        member_path = f"{path}[{index}]"
        if not isinstance(suggestion, Mapping):
            continue
        allowed_fields = {
            "suggestion_id",
            "suggestion_kind",
            "summary",
            "restriction_reason",
            "impact_summary",
            "resume_condition",
            "follow_up_summary",
        }
        for name in set(suggestion) - allowed_fields:
            _issue(issues, "spark suggestion 包含未登记字段", f"{member_path}.{name}")
        suggestion_id = suggestion.get("suggestion_id")
        if not isinstance(suggestion_id, str) or _SUGGESTION_ID.fullmatch(suggestion_id) is None:
            _issue(issues, "suggestion_id 格式不符合当前闭集", f"{member_path}.suggestion_id")
        elif suggestion_id in kinds:
            _issue(issues, "suggestion_id 不得重复", f"{member_path}.suggestion_id")
        kind = suggestion.get("suggestion_kind")
        if kind not in {"constrained_responsibility", "follow_up_opportunity"}:
            _issue(issues, "suggestion_kind 不在当前闭集中", f"{member_path}.suggestion_kind")
        if isinstance(suggestion_id, str) and isinstance(kind, str):
            kinds[suggestion_id] = kind
        for name in ("summary", "follow_up_summary"):
            if not _nonempty_string(suggestion.get(name)):
                _issue(issues, f"{name} 必须是非空 string", f"{member_path}.{name}")
        constrained = {"restriction_reason", "impact_summary", "resume_condition"}
        if kind == "constrained_responsibility":
            for name in constrained:
                if not _nonempty_string(suggestion.get(name)):
                    _issue(issues, f"受限责任建议要求非空 {name}", f"{member_path}.{name}")
        elif kind == "follow_up_opportunity":
            for name in constrained:
                if name in suggestion:
                    _issue(issues, f"后续机会建议禁止 {name}", f"{member_path}.{name}")
    return kinds


def _validate_proposal(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    proposal = fields.get("closure_proposal")
    if proposal is None or not isinstance(proposal, Mapping):
        return
    outcome = proposal.get("proposed_outcome")
    _validate_outcome(outcome, fields, "closure_proposal.proposed_outcome", issues)
    if not _nonempty_string(proposal.get("proposed_disposition_summary")):
        _issue(
            issues,
            "proposed_disposition_summary 必须是非空 string",
            "closure_proposal.proposed_disposition_summary",
        )
    suggestion_kinds = _validate_suggestions(
        proposal.get("spark_suggestions"),
        "closure_proposal.spark_suggestions",
        issues,
    )
    decisions = proposal.get("residual_decisions")
    if outcome == "completed" and decisions is not None:
        _issue(issues, "completed proposal 必须省略 residual_decisions", "closure_proposal.residual_decisions")
    if outcome == "completed" and any(
        kind == "constrained_responsibility" for kind in suggestion_kinds.values()
    ):
        _issue(
            issues,
            "completed proposal 只允许 follow_up_opportunity suggestion",
            "closure_proposal.spark_suggestions",
        )
    if outcome in CLOSURE_OUTCOMES - {"completed"} and (not isinstance(decisions, list) or not decisions):
        _issue(issues, "非 completed proposal 必须处置剩余责任", "closure_proposal.residual_decisions")
    if not isinstance(decisions, list):
        return

    residual_ids: list[str] = []
    for index, decision in enumerate(decisions):
        path = f"closure_proposal.residual_decisions[{index}]"
        if not isinstance(decision, Mapping):
            continue
        residual_id = decision.get("residual_id")
        if isinstance(residual_id, str):
            residual_ids.append(residual_id)
            if _RESIDUAL_ID.fullmatch(residual_id) is None:
                _issue(issues, "residual_id 格式不符合当前闭集", f"{path}.residual_id")
        if not _nonempty_string(decision.get("summary")):
            _issue(issues, "residual decision summary 必须是非空 string", f"{path}.summary")
        disposition = decision.get("proposed_disposition")
        if disposition not in {"route_existing", "suggest_spark", "accept_stop"}:
            _issue(issues, "proposed_disposition 不在当前闭集中", f"{path}.proposed_disposition")
        route_target = decision.get("route_target")
        suggestion_id = decision.get("spark_suggestion_id")
        if disposition == "route_existing" and not isinstance(route_target, Mapping):
            _issue(issues, "route_existing decision 必须包含 route_target", f"{path}.route_target")
        if disposition != "route_existing" and route_target is not None:
            _issue(issues, "非 route_existing decision 禁止 route_target", f"{path}.route_target")
        if disposition == "suggest_spark":
            if not isinstance(suggestion_id, str) or suggestion_kinds.get(suggestion_id) != "constrained_responsibility":
                _issue(
                    issues,
                    "suggest_spark 必须引用同一 proposal 的 constrained_responsibility suggestion",
                    f"{path}.spark_suggestion_id",
                )
        elif suggestion_id is not None:
            _issue(issues, "非 suggest_spark decision 禁止 spark_suggestion_id", f"{path}.spark_suggestion_id")
        if isinstance(route_target, Mapping):
            if not _nonempty_string(route_target.get("governed_project_id")):
                _issue(
                    issues,
                    "route_target.governed_project_id 必须是非空 string",
                    f"{path}.route_target.governed_project_id",
                )
            target_type = route_target.get("fact_type_key")
            if target_type not in {"workcase", "spark"}:
                _issue(
                    issues,
                    "route_target.fact_type_key 必须为 workcase 或 spark",
                    f"{path}.route_target.fact_type_key",
                )
            target_id = route_target.get("object_id")
            layout = LAYOUTS.get(target_type) if isinstance(target_type, str) else None
            if not isinstance(target_id, str) or layout is None or layout.object_id_pattern.fullmatch(target_id) is None:
                _issue(issues, "route_target.object_id 必须匹配目标类型稳定身份", f"{path}.route_target.object_id")
            elif target_id == fields.get("object_id"):
                _issue(issues, "route_target 禁止指向当前 WorkCase 自身", f"{path}.route_target.object_id")
            fingerprint = route_target.get("content_fingerprint")
            if not isinstance(fingerprint, str) or _SHA256.fullmatch(fingerprint) is None:
                _issue(
                    issues,
                    "route_target.content_fingerprint 必须是 64 位小写 SHA-256",
                    f"{path}.route_target.content_fingerprint",
                )
    if len(residual_ids) != len(set(residual_ids)):
        _issue(issues, "proposal residual_id 不得重复", "closure_proposal.residual_decisions")


def _validate_terminal_residuals(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    values = fields.get("residual_responsibilities")
    if values is not None and (not isinstance(values, list) or not values):
        _issue(issues, "residual_responsibilities 出现时必须是非空 array", "residual_responsibilities")
    if not isinstance(values, list):
        return
    residual_ids: list[str] = []
    for index, value in enumerate(values):
        path = f"residual_responsibilities[{index}]"
        if not isinstance(value, Mapping):
            continue
        residual_id = value.get("residual_id")
        if isinstance(residual_id, str):
            residual_ids.append(residual_id)
            if _RESIDUAL_ID.fullmatch(residual_id) is None:
                _issue(issues, "residual_id 格式不符合当前闭集", f"{path}.residual_id")
        if not _nonempty_string(value.get("summary")):
            _issue(issues, "terminal residual summary 必须是非空 string", f"{path}.summary")
    if len(residual_ids) != len(set(residual_ids)):
        _issue(issues, "terminal residual_id 不得重复", "residual_responsibilities")


def _validate_relations(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    relations = fields.get("relations")
    if not isinstance(relations, list):
        return
    status = fields.get("status")
    phase = fields.get("phase")
    source_id = fields.get("object_id")
    allowed = (
        {"routed-to", "contributed-to", "has-file-asset", "related-to"}
        if status == "closed"
        else {"depends-on", "contributed-to", "has-file-asset", "related-to"}
    )
    observed: list[tuple[object, object, object, object]] = []
    for index, relation in enumerate(relations):
        path = f"relations[{index}]"
        if not isinstance(relation, Mapping):
            continue
        relation_key = relation.get("relation_key")
        if relation_key == "depends-on" and phase == "human_closure_confirming":
            _issue(issues, "human_closure_confirming 禁止 depends-on relation", f"{path}.relation_key")
        elif relation_key not in allowed:
            _issue(issues, f"当前 WorkCase 只允许 {'/'.join(sorted(allowed))} relation", f"{path}.relation_key")
        target = relation.get("target")
        if not isinstance(target, Mapping):
            continue
        target_id = target.get("object_id")
        if relation_key == "contributed-to":
            target_type = target.get("fact_type_key")
            if target_type != "pitfall":
                _issue(
                    issues,
                    "contributed-to relation target 必须为 pitfall",
                    f"{path}.target.fact_type_key",
                )
            layout = LAYOUTS.get(target_type) if isinstance(target_type, str) else None
            if (
                not isinstance(target_id, str)
                or layout is None
                or layout.object_id_pattern.fullmatch(target_id) is None
            ):
                _issue(
                    issues,
                    "contributed-to relation target.object_id 必须是目标类型稳定身份",
                    f"{path}.target.object_id",
                )
        elif relation_key == "has-file-asset":
            target_type = target.get("fact_type_key")
            if target_type != "file-asset":
                _issue(
                    issues,
                    "has-file-asset relation target 必须为 file-asset",
                    f"{path}.target.fact_type_key",
                )
            layout = LAYOUTS.get(target_type) if isinstance(target_type, str) else None
            if (
                not isinstance(target_id, str)
                or layout is None
                or layout.object_id_pattern.fullmatch(target_id) is None
            ):
                _issue(
                    issues,
                    "has-file-asset target.object_id 必须是 FileAsset 稳定身份",
                    f"{path}.target.object_id",
                )
        elif relation_key == "related-to":
            target_type = target.get("fact_type_key")
            layout = LAYOUTS.get(target_type) if isinstance(target_type, str) else None
            if (
                target_type == "file-asset"
                or not isinstance(target_id, str)
                or layout is None
                or layout.object_id_pattern.fullmatch(target_id) is None
            ):
                _issue(
                    issues,
                    "related-to target 必须是除 FileAsset 外的当前事实类型稳定身份",
                    f"{path}.target.object_id",
                )
        else:
            target_type = target.get("fact_type_key")
            if relation_key == "routed-to" and target_type not in {"workcase", "spark"}:
                _issue(issues, "routed-to target 必须为 workcase 或 spark", f"{path}.target.fact_type_key")
            elif relation_key == "depends-on" and target_type != "workcase":
                _issue(issues, "depends-on target 必须为 workcase", f"{path}.target.fact_type_key")
            layout = LAYOUTS.get(target_type) if isinstance(target_type, str) else None
            if not isinstance(target_id, str) or layout is None or layout.object_id_pattern.fullmatch(target_id) is None:
                _issue(issues, "relation target.object_id 必须匹配目标类型稳定身份", f"{path}.target.object_id")
            elif target_id == source_id:
                _issue(issues, "WorkCase relation 禁止自指", f"{path}.target.object_id")
        identity = (relation_key, target.get("governed_project_id"), target.get("fact_type_key"), target_id)
        observed.append(identity)
    if len(observed) != len(set(observed)):
        _issue(issues, "同一 relation_key 与 target 不得重复", "relations")
    keys_by_target: dict[tuple[object, object, object], set[object]] = {}
    for relation_key, project_id, target_type, target_id in observed:
        target_identity = (project_id, target_type, target_id)
        keys_by_target.setdefault(target_identity, set()).add(relation_key)
    if any("related-to" in keys and len(keys) > 1 for keys in keys_by_target.values()):
        _issue(issues, "related-to 不得与同一 target 的强关系重叠", "relations")


def _require_complete_result(fields: Mapping[str, object], issues: list[FactIssue], *, context: str) -> None:
    _require(fields, _RESULT_PROJECTION_FIELDS, issues, context=context)
    if not all_terminal(fields):
        _issue(issues, "完整结果投影要求全部 work item terminal", "work_items")
    elif all(name in fields for name in _RESULT_PROJECTION_FIELDS) and not result_projection_complete(fields):
        _issue(issues, "canonical result projection 结构不完整", "success_criterion_results")


def _validate_active_presence(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    _require(
        fields,
        {
            "priority",
            "phase",
            "plan_version",
            "work_items",
            "goal",
            "scope",
            "success_criterion_definitions",
        },
        issues,
        context="活动期 WorkCase ",
    )
    _forbid(fields, _TERMINAL_FIELDS, issues, context="活动期 WorkCase ")
    status = fields.get("status")
    if status == "open":
        _forbid(fields, {"blocking_summary"}, issues, context="open WorkCase ")
    elif status == "blocked":
        _require(fields, {"blocking_summary"}, issues, context="blocked WorkCase ")

    phase = fields.get("phase")
    if phase not in ACTIVE_PHASES:
        _issue(issues, "phase 不在当前 WorkCase 活动阶段闭集中", "phase")
        return
    if not _positive_integer(fields.get("plan_version")):
        _issue(issues, "plan_version 必须是正整数", "plan_version")
    if "result_version" in fields and not _positive_integer(fields.get("result_version")):
        _issue(issues, "result_version 必须是正整数", "result_version")

    if phase == "human_plan_confirming":
        _require(
            fields,
            {"execution_authorization", "creation_reviews", "waiting_on"},
            issues,
            context="human_plan_confirming ",
        )
        _forbid(
            fields,
            {"execution_approval", *_RESULT_CHAIN_FIELDS},
            issues,
            context="human_plan_confirming ",
        )
        return

    if phase == "plan_revising":
        _require(
            fields,
            {"execution_authorization", "creation_reviews"},
            issues,
            context="plan_revising ",
        )
        _forbid(fields, {"closure_proposal"}, issues, context="plan_revising ")
        has_version = "result_version" in fields
        projection_members = _RESULT_PROJECTION_FIELDS & set(fields)
        if not has_version:
            _forbid(
                fields,
                {*_RESULT_PROJECTION_FIELDS, "result_reviews"},
                issues,
                context="plan_revising 无结果版本时 ",
            )
            if "execution_approval" not in fields and not no_execution_facts(fields):
                _issue(issues, "Gate1 前 plan_revising 必须保持 NoExec", "execution_approval")
        elif not projection_members:
            _forbid(fields, {"result_reviews"}, issues, context="plan_revising version-only 形状 ")
            if "execution_approval" in fields and all_terminal(fields):
                _issue(issues, "正常 version-only 返工快照必须仍有非 terminal item", "work_items")
            if "execution_approval" not in fields:
                _issue(issues, "Gate1 前 plan_revising 禁止结果版本与结果形状", "execution_approval")
        else:
            if not all_terminal(fields):
                _issue(issues, "冻结的部分或完整结果投影要求 AllTerminal", "work_items")
            if "execution_approval" not in fields:
                _issue(issues, "Gate1 前 plan_revising 禁止结果版本与结果形状", "execution_approval")
            if "result_reviews" in fields and not result_projection_complete(fields):
                _issue(issues, "result_reviews 只能与完整结果投影同时存在", "result_reviews")
        return

    if phase == "executing":
        _require(
            fields,
            {"execution_authorization", "execution_approval", "creation_reviews"},
            issues,
            context="executing ",
        )
        _forbid(
            fields,
            {*_RESULT_PROJECTION_FIELDS, "result_reviews", "closure_proposal"},
            issues,
            context="executing ",
        )
        if all_terminal(fields):
            _issue(issues, "executing 必须至少有一项非 terminal item", "work_items")
        return

    _require(fields, {"result_version"}, issues, context=f"{phase} ")
    if not all_terminal(fields):
        _issue(issues, "进入结果链前全部 work item 必须 terminal", "work_items")
    if "execution_approval" in fields:
        _require(
            fields,
            {"execution_authorization", "creation_reviews"},
            issues,
            context=f"{phase} 已批准结果链 ",
        )
    else:
        _forbid(
            fields,
            {"execution_authorization", "creation_reviews"},
            issues,
            context=f"{phase} SafeConvergenceShape ",
        )
        if not safe_convergence_shape(fields):
            _issue(issues, "结果链 approval 缺失只允许 SafeConvergenceShape", "execution_approval")

    if phase == "controller_checking":
        _forbid(fields, {"closure_proposal"}, issues, context="controller_checking ")
        if "result_reviews" in fields and not result_projection_complete(fields):
            _issue(issues, "result_reviews 只能与完整结果投影同时存在", "result_reviews")
    elif phase == "independent_reviewing":
        _forbid(fields, {"closure_proposal"}, issues, context="independent_reviewing ")
        _require_complete_result(fields, issues, context="independent_reviewing ")
    elif phase == "closure_preparing":
        _require_complete_result(fields, issues, context="closure_preparing ")
        _require(fields, {"result_reviews"}, issues, context="closure_preparing ")
    else:  # human_closure_confirming
        _require_complete_result(fields, issues, context="human_closure_confirming ")
        _require(
            fields,
            {"result_reviews", "closure_proposal", "waiting_on"},
            issues,
            context="human_closure_confirming ",
        )


def _validate_closed_presence(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    _require(fields, _CLOSED_REQUIRED, issues, context="closed WorkCase ")
    for name in sorted(set(fields) - _CLOSED_ALLOWED):
        _issue(issues, "closed WorkCase 白名单禁止该字段", name)
    _validate_outcome(fields.get("closure_outcome"), fields, "closure_outcome", issues)
    residuals = fields.get("residual_responsibilities")
    suggestion_kinds = _validate_suggestions(fields.get("spark_suggestions"), "spark_suggestions", issues)
    routed = any(
        isinstance(relation, Mapping) and relation.get("relation_key") == "routed-to"
        for relation in fields.get("relations", [])
        if isinstance(fields.get("relations"), list)
    )
    outcome = fields.get("closure_outcome")
    if outcome == "completed":
        if residuals is not None:
            _issue(issues, "completed closed WorkCase 必须省略 residual_responsibilities", "residual_responsibilities")
        if routed:
            _issue(issues, "completed closed WorkCase 必须省略 routed-to", "relations")
        if any(kind == "constrained_responsibility" for kind in suggestion_kinds.values()):
            _issue(issues, "completed 只允许 follow_up_opportunity suggestion", "spark_suggestions")
    elif (
        outcome in CLOSURE_OUTCOMES
        and not isinstance(residuals, list)
        and not routed
        and not any(kind == "constrained_responsibility" for kind in suggestion_kinds.values())
    ):
        _issue(issues, "非 completed closed WorkCase 必须保留剩余责任、routed-to 或受限 Spark 建议", "disposition_summary")


def validate_workcase_snapshot(fields: Mapping[str, object]) -> tuple[FactIssue, ...]:
    """Validate current WorkCase presence and structure without transition history."""

    issues: list[FactIssue] = []
    object_id = fields.get("object_id")
    if not isinstance(object_id, str) or _WORKCASE_ID.fullmatch(object_id) is None:
        _issue(issues, "object_id 必须匹配 workcase-[0-9]{4,}", "object_id")
    if fields.get("fact_type_key") != "workcase":
        _issue(issues, "fact_type_key 必须为 workcase", "fact_type_key")
    status = fields.get("status")
    if status in ACTIVE_STATUSES:
        _validate_active_presence(fields, issues)
    elif status == "closed":
        _validate_closed_presence(fields, issues)
    else:
        _issue(issues, "status 不在当前 WorkCase 闭集中", "status")

    _validate_criteria(fields, issues)
    _validate_items(fields, issues)
    _validate_reviews(fields, "creation_reviews", "plan_version", issues)
    _validate_reviews(fields, "result_reviews", "result_version", issues)
    if status in ACTIVE_STATUSES:
        _validate_execution_authorization(fields, issues)
    _validate_execution_approval(fields, issues)
    _validate_proposal(fields, issues)
    _validate_terminal_residuals(fields, issues)
    _validate_relations(fields, issues)
    return tuple(issues)


__all__ = [
    "ACTIVE_PHASES",
    "CLOSURE_OUTCOMES",
    "CRITERION_OUTCOMES",
    "ITEM_STATUSES",
    "REVIEW_CONCLUSIONS",
    "validate_workcase_snapshot",
]
