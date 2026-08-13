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
        "termination_preparing",
    }
)
ITEM_STATUSES = frozenset({"pending", "in_progress", "blocked", "completed", "cancelled"})
REVIEW_CONCLUSIONS = frozenset({"pass", "pass_with_followups", "changes_required", "blocked"})
REVIEW_METHODS = frozenset(
    {
        "subagent-read-only",
        "collaboration-worker-read-only",
        "same-ai-switched-role-read-only",
    }
)
SAME_AI_REVIEW_METHOD = "same-ai-switched-role-read-only"
SUBAGENT_REVIEW_METHOD = "subagent-read-only"
COLLABORATION_REVIEW_METHOD = "collaboration-worker-read-only"
CAPABILITY_LIMITATION_CAPABILITY = "independent-subagent-review"
CAPABILITY_LIMITATION_AVAILABILITY = "unavailable"
CAPABILITY_LIMITATION_FALLBACK_POLICY = SAME_AI_REVIEW_METHOD
REVIEW_CATEGORIES = frozenset({"creation_review", "plan_delta_review", "result_review"})
REQUIRED_QUALITY_GATE_ID = "independent-result-review"
REQUIRED_REVIEWER_MODE = "independent-read-only"
REVIEWER_PREFERRED_METHODS = frozenset(REVIEW_METHODS)
CRITERION_OUTCOMES = frozenset({"satisfied", "not_satisfied", "not_verified"})
CLOSURE_OUTCOMES = frozenset({"completed", "partial", "not-achieved", "cancelled"})

_ITEM_ID = re.compile(r"item-[a-z0-9][a-z0-9-]*\Z")
_CRITERION_ID = re.compile(r"criterion-[a-z0-9][a-z0-9-]*\Z")
_RESIDUAL_ID = re.compile(r"residual-[a-z0-9][a-z0-9-]*\Z")
_SUGGESTION_ID = re.compile(r"suggestion-[a-z0-9][a-z0-9-]*\Z")
_WORKCASE_ID = re.compile(r"workcase-[0-9]{4,}\Z")
_AUTHORIZATION_ID = re.compile(r"authorization-[a-z0-9][a-z0-9-]*\Z")
_LIMITATION_ID = re.compile(r"limitation-[a-z0-9][a-z0-9-]*\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_TERMINATION_QUALITY_STEP = re.compile(
    r"(independent_result_review|closure_proposal|gate_2):(not_reached|actual|skipped)\Z"
)

_RESULT_PROJECTION_FIELDS = frozenset(
    {"success_criterion_results", "result_summary", "controller_check_summary", "validation_summary"}
)
_RESULT_CHAIN_FIELDS = frozenset({"result_version", *_RESULT_PROJECTION_FIELDS, "result_reviews", "closure_proposal"})
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
    {
        *_CLOSED_REQUIRED,
        "object_uid",
        "change_log",
        "residual_responsibilities",
        "spark_suggestions",
        "relations",
        "urls",
        "termination",
    }
)

_TERMINATION_REQUIRED = frozenset(
    {
        "initiated_at",
        "source_status",
        "source_phase",
        "source_content_fingerprint",
        "reason",
        "source_refs",
        "item_snapshots",
        "quality_steps",
        "cleanup_status",
        "cleanup_summary",
    }
)
_TERMINATION_OPTIONAL_ARRAYS = frozenset(
    {"retained_scope", "discarded_scope", "unverified_scope", "relationship_impacts"}
)
_TERMINATION_ALLOWED = _TERMINATION_REQUIRED | _TERMINATION_OPTIONAL_ARRAYS


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


def _capability_limitations(fields: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    authorization = fields.get("execution_authorization")
    if not isinstance(authorization, Mapping):
        return {}
    values = authorization.get("capability_limitations")
    if not isinstance(values, list):
        return {}
    return {
        str(value["limitation_id"]): value
        for value in values
        if isinstance(value, Mapping) and _nonempty_string(value.get("limitation_id"))
    }


def _review_category(fields: Mapping[str, object], array_name: str) -> str:
    if array_name == "result_reviews":
        return "result_review"
    approval = fields.get("execution_approval")
    plan_version = fields.get("plan_version")
    approved_version = approval.get("subject_version") if isinstance(approval, Mapping) else None
    if (
        _positive_integer(approved_version)
        and _positive_integer(plan_version)
        and int(plan_version) > int(approved_version)
    ):
        return "plan_delta_review"
    return "creation_review"


def _validate_review_method(
    fields: Mapping[str, object],
    review: Mapping[str, object],
    *,
    array_name: str,
    path: str,
    issues: list[FactIssue],
) -> None:
    limitations = _capability_limitations(fields)
    method = review.get("actual_method")
    fallback_fields = {
        "capability_limitation_id",
        "capability_evidence",
        "assurance_gap",
        "stop_condition_assessment",
    }
    carrier_fields = {"actual_agent", "actual_model", "evidence"}
    if method is None:
        if limitations:
            _issue(
                issues,
                "authorization 含 capability limitations 时 review 必须记录 actual_method",
                f"{path}.actual_method",
            )
        for name in sorted(fallback_fields & set(review)):
            _issue(issues, "fallback 披露字段要求 actual_method", f"{path}.{name}")
        for name in sorted(carrier_fields & set(review)):
            _issue(issues, "carrier 披露字段要求 actual_method", f"{path}.{name}")
        return
    if method not in REVIEW_METHODS:
        _issue(issues, "review actual_method 不在当前闭集中", f"{path}.actual_method")
        return
    if method == SAME_AI_REVIEW_METHOD:
        for name in sorted(fallback_fields - set(review)):
            _issue(issues, "same-AI fallback review 缺少必填披露字段", f"{path}.{name}")
        limitation_id = review.get("capability_limitation_id")
        limitation = limitations.get(str(limitation_id)) if _nonempty_string(limitation_id) else None
        if limitation is None:
            _issue(
                issues,
                "same-AI fallback 必须精确引用当前 capability limitation",
                f"{path}.capability_limitation_id",
            )
        else:
            category = _review_category(fields, array_name)
            categories = limitation.get("affected_review_categories")
            if not isinstance(categories, list) or category not in categories:
                _issue(
                    issues,
                    "capability limitation 未覆盖当前 review 类别",
                    f"{path}.capability_limitation_id",
                )
            if limitation.get("fallback_policy") != SAME_AI_REVIEW_METHOD:
                _issue(
                    issues,
                    "capability limitation fallback_policy 与实际方法不一致",
                    f"{path}.capability_limitation_id",
                )
            if review.get("assurance_gap") != limitation.get("assurance_gap"):
                _issue(
                    issues,
                    "review assurance_gap 必须与 capability limitation 精确一致",
                    f"{path}.assurance_gap",
                )
        _validate_unique_strings(review.get("capability_evidence"), f"{path}.capability_evidence", issues)
        if review.get("stop_condition_assessment") != "clear":
            _issue(
                issues,
                "same-AI fallback 的 stop_condition_assessment 必须为 clear",
                f"{path}.stop_condition_assessment",
            )
        for name in sorted(carrier_fields & set(review)):
            _issue(issues, "same-AI review 禁止 carrier 披露字段", f"{path}.{name}")
        return

    # subagent-read-only or collaboration-worker-read-only (non-fallback carriers)
    for name in sorted(fallback_fields & set(review)):
        _issue(issues, "独立 review 禁止 fallback 披露字段", f"{path}.{name}")
    if method == COLLABORATION_REVIEW_METHOD:
        if not _nonempty_string(review.get("actual_agent")):
            _issue(issues, "collaboration review 必须记录 actual_agent", f"{path}.actual_agent")
        if not _nonempty_string(review.get("actual_model")):
            _issue(issues, "collaboration review 必须记录 actual_model", f"{path}.actual_model")
        _validate_unique_strings(review.get("evidence"), f"{path}.evidence", issues)
        _validate_reviewer_policy_match(fields, review, path, issues)


def _validate_reviewer_policy_match(
    fields: Mapping[str, object],
    review: Mapping[str, object],
    path: str,
    issues: list[FactIssue],
) -> None:
    """collaboration review 必须与冻结 reviewer policy 的模型/Agent 映射一致并满足每轮视角上限。"""
    authorization = fields.get("execution_authorization")
    if not isinstance(authorization, Mapping):
        return
    policy = authorization.get("reviewer_policy")
    if not isinstance(policy, Mapping):
        return
    agent = policy.get("collaboration_agent")
    model = policy.get("model")
    if _nonempty_string(agent) and _nonempty_string(review.get("actual_agent")) and review.get("actual_agent") != agent:
        _issue(issues, "collaboration review actual_agent 必须与冻结 reviewer policy 一致", f"{path}.actual_agent")
    if _nonempty_string(model) and _nonempty_string(review.get("actual_model")) and review.get("actual_model") != model:
        _issue(issues, "collaboration review actual_model 必须与冻结 reviewer policy 一致", f"{path}.actual_model")


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
        if array_name != "creation_reviews" and "covered_quality_gate_ids" in review:
            _issue(issues, "covered_quality_gate_ids 只允许出现在 creation_reviews", f"{path}.covered_quality_gate_ids")
        _validate_review_method(fields, review, array_name=array_name, path=path, issues=issues)
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
        _issue(
            issues, "execution approval subject_version 不得晚于当前 plan_version", "execution_approval.subject_version"
        )
    baseline = approval.get("baseline_fingerprint")
    if not isinstance(baseline, str) or _SHA256.fullmatch(baseline) is None:
        _issue(
            issues,
            "execution approval baseline_fingerprint 必须是 64 位小写 SHA-256",
            "execution_approval.baseline_fingerprint",
        )
    elif baseline != approval_baseline_fingerprint(fields):
        _issue(
            issues,
            "execution approval baseline_fingerprint 与当前批准基线不一致",
            "execution_approval.baseline_fingerprint",
        )
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
    limitations = value.get("capability_limitations")
    if limitations is not None:
        path = "execution_authorization.capability_limitations"
        if not isinstance(limitations, list) or not limitations:
            _issue(issues, "capability_limitations 出现时必须是非空 array", path)
        else:
            limitation_ids: list[str] = []
            required = {
                "limitation_id",
                "capability",
                "availability",
                "observation_summary",
                "evidence",
                "affected_review_categories",
                "fallback_policy",
                "assurance_gap",
                "stop_conditions",
            }
            for index, limitation in enumerate(limitations):
                item_path = f"{path}[{index}]"
                if not isinstance(limitation, Mapping):
                    _issue(issues, "capability limitation 必须是 object", item_path)
                    continue
                _require(limitation, required, issues, context="capability limitation ")
                unknown = sorted(set(limitation) - required)
                if unknown:
                    _issue(issues, "capability limitation 包含未知成员", item_path)
                limitation_id = limitation.get("limitation_id")
                if _nonempty_string(limitation_id):
                    limitation_ids.append(str(limitation_id))
                    if _LIMITATION_ID.fullmatch(str(limitation_id)) is None:
                        _issue(issues, "limitation_id 格式不符合当前闭集", f"{item_path}.limitation_id")
                else:
                    _issue(issues, "limitation_id 必须是非空 string", f"{item_path}.limitation_id")
                if limitation.get("capability") != CAPABILITY_LIMITATION_CAPABILITY:
                    _issue(issues, "capability 不在当前闭集中", f"{item_path}.capability")
                if limitation.get("availability") != CAPABILITY_LIMITATION_AVAILABILITY:
                    _issue(issues, "availability 必须明确为 unavailable", f"{item_path}.availability")
                if not _nonempty_string(limitation.get("observation_summary")):
                    _issue(issues, "observation_summary 必须是非空 string", f"{item_path}.observation_summary")
                evidence = _validate_unique_strings(limitation.get("evidence"), f"{item_path}.evidence", issues)
                categories = _validate_unique_strings(
                    limitation.get("affected_review_categories"),
                    f"{item_path}.affected_review_categories",
                    issues,
                )
                for category_index, category in enumerate(categories):
                    if category not in REVIEW_CATEGORIES:
                        _issue(
                            issues,
                            "affected review category 不在当前闭集中",
                            f"{item_path}.affected_review_categories[{category_index}]",
                        )
                if limitation.get("fallback_policy") != CAPABILITY_LIMITATION_FALLBACK_POLICY:
                    _issue(issues, "fallback_policy 不在当前闭集中", f"{item_path}.fallback_policy")
                if not _nonempty_string(limitation.get("assurance_gap")):
                    _issue(issues, "assurance_gap 必须是非空 string", f"{item_path}.assurance_gap")
                stop_conditions = _validate_unique_strings(
                    limitation.get("stop_conditions"), f"{item_path}.stop_conditions", issues
                )
                if not evidence or not stop_conditions:
                    continue
            if len(limitation_ids) != len(set(limitation_ids)):
                _issue(issues, "capability limitation_id 不得重复", path)

    reviewer_policy = value.get("reviewer_policy")
    if reviewer_policy is not None:
        path = "execution_authorization.reviewer_policy"
        if not isinstance(reviewer_policy, Mapping):
            _issue(issues, "reviewer_policy 必须是 object", path)
        else:
            required = {
                "model",
                "collaboration_agent",
                "effort",
                "fast",
                "preferred_method",
                "fallback_order",
                "max_perspectives",
                "activation",
                "same_ai_limit",
            }
            _require(reviewer_policy, required, issues, context="reviewer policy ")
            for name in ("model", "collaboration_agent", "effort", "activation", "same_ai_limit"):
                if not _nonempty_string(reviewer_policy.get(name)):
                    _issue(issues, "reviewer policy 文本成员必须是非空 string", f"{path}.{name}")
            if not isinstance(reviewer_policy.get("fast"), bool):
                _issue(issues, "reviewer policy fast 必须是 boolean", f"{path}.fast")
            preferred = reviewer_policy.get("preferred_method")
            if preferred not in REVIEWER_PREFERRED_METHODS:
                _issue(issues, "reviewer policy preferred_method 不在当前闭集中", f"{path}.preferred_method")
            fallback_order = _validate_unique_strings(
                reviewer_policy.get("fallback_order"), f"{path}.fallback_order", issues
            )
            for member in fallback_order:
                if member not in REVIEWER_PREFERRED_METHODS:
                    _issue(issues, "reviewer policy fallback_order 成员不在当前闭集中", f"{path}.fallback_order")
            if preferred is not None:
                if not fallback_order or fallback_order[0] != preferred:
                    _issue(
                        issues,
                        "reviewer policy fallback_order 首项必须等于 preferred_method",
                        f"{path}.fallback_order",
                    )
                if len(fallback_order) != len(set(fallback_order)):
                    _issue(issues, "reviewer policy fallback_order 成员不得重复", f"{path}.fallback_order")
            max_perspectives = reviewer_policy.get("max_perspectives")
            if not _positive_integer(max_perspectives):
                _issue(issues, "reviewer policy max_perspectives 必须是正整数", f"{path}.max_perspectives")
            elif int(max_perspectives) > 3:
                _issue(issues, "reviewer policy max_perspectives 不大于 3", f"{path}.max_perspectives")
            unknown = sorted(set(reviewer_policy) - required)
            if unknown:
                _issue(issues, "reviewer policy 包含未知成员", path)


def required_quality_gate_issues(fields: Mapping[str, object]) -> tuple[FactIssue, ...]:
    """Check the current minimal, mechanical result-review authorization set.

    This deliberately validates only a fixed declaration, action references and
    creation-review coverage.  It neither interprets authorization prose nor
    attempts to establish a Reviewer's real-world independence.
    """

    issues: list[FactIssue] = []
    authorization = fields.get("execution_authorization")
    if not isinstance(authorization, Mapping):
        return (FactIssue("schema", "Gate1 候选必须声明 execution_authorization", "execution_authorization"),)
    actions = authorization.get("authorized_actions")
    action_ids = (
        {
            action.get("action_id")
            for action in actions
            if isinstance(action, Mapping) and isinstance(action.get("action_id"), str)
        }
        if isinstance(actions, list)
        else set()
    )
    gates = authorization.get("quality_gates")
    if not isinstance(gates, list) or len(gates) != 1:
        return (
            FactIssue(
                "schema",
                "Gate1 候选必须精确声明一个必经独立结果复核质量关口",
                "execution_authorization.quality_gates",
            ),
        )
    gate = gates[0]
    path = "execution_authorization.quality_gates[0]"
    if not isinstance(gate, Mapping):
        return (FactIssue("schema", "质量关口必须是 object", path),)
    required = {"gate_id", "reviewer_mode", "delegation_action_id", "result_review_action_id"}
    for name in sorted(required - set(gate)):
        issues.append(FactIssue("schema", "质量关口缺少必填成员", f"{path}.{name}"))
    unknown = sorted(set(gate) - required)
    if unknown:
        issues.append(FactIssue("schema", "质量关口包含未知成员", path))
    if gate.get("gate_id") != REQUIRED_QUALITY_GATE_ID:
        issues.append(FactIssue("schema", "质量关口 gate_id 不在当前必经闭集中", f"{path}.gate_id"))
    if gate.get("reviewer_mode") != REQUIRED_REVIEWER_MODE:
        issues.append(FactIssue("schema", "Reviewer mode 不在当前必经闭集中", f"{path}.reviewer_mode"))
    references = [gate.get("delegation_action_id"), gate.get("result_review_action_id")]
    if any(not _nonempty_string(value) for value in references):
        issues.append(FactIssue("schema", "质量关口 action 引用必须是非空 string", path))
    elif len(set(references)) != len(references):
        issues.append(FactIssue("schema", "质量关口不得复用 delegation 与 result review action 引用", path))
    else:
        for name, action_id in zip(("delegation_action_id", "result_review_action_id"), references, strict=True):
            if action_id not in action_ids:
                issues.append(
                    FactIssue("schema", "质量关口 action 引用必须精确指向 authorized_actions", f"{path}.{name}")
                )

    reviews = fields.get("creation_reviews")
    if not isinstance(reviews, list) or not reviews:
        issues.append(FactIssue("schema", "质量关口必须由当前 creation reviews 覆盖", "creation_reviews"))
    else:
        for index, review in enumerate(reviews):
            review_path = f"creation_reviews[{index}].covered_quality_gate_ids"
            covered = review.get("covered_quality_gate_ids") if isinstance(review, Mapping) else None
            if covered != [REQUIRED_QUALITY_GATE_ID]:
                issues.append(FactIssue("schema", "creation review 必须精确覆盖全部必经质量关口", review_path))
    return tuple(issues)


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
    if outcome == "completed" and any(kind == "constrained_responsibility" for kind in suggestion_kinds.values()):
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
            if (
                not isinstance(suggestion_id, str)
                or suggestion_kinds.get(suggestion_id) != "constrained_responsibility"
            ):
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
            if (
                not isinstance(target_id, str)
                or layout is None
                or layout.object_id_pattern.fullmatch(target_id) is None
            ):
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
        {"routed-to", "contributed-to", "related-to"}
        if status == "closed"
        else {"depends-on", "contributed-to", "related-to"}
    )
    observed: list[tuple[object, ...]] = []
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
        if set(target) == {"object_uid"}:
            target_uid = target.get("object_uid")
            if target_uid == fields.get("object_uid"):
                _issue(issues, "WorkCase relation 禁止自指", f"{path}.target.object_uid")
            observed.append((relation_key, "uid", target_uid))
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
        elif relation_key == "related-to":
            target_type = target.get("fact_type_key")
            layout = LAYOUTS.get(target_type) if isinstance(target_type, str) else None
            if (
                not isinstance(target_id, str)
                or layout is None
                or layout.object_id_pattern.fullmatch(target_id) is None
            ):
                _issue(
                    issues,
                    "related-to target 必须是当前事实类型稳定身份",
                    f"{path}.target.object_id",
                )
        else:
            target_type = target.get("fact_type_key")
            if relation_key == "routed-to" and target_type not in {"workcase", "spark"}:
                _issue(issues, "routed-to target 必须为 workcase 或 spark", f"{path}.target.fact_type_key")
            elif relation_key == "depends-on" and target_type != "workcase":
                _issue(issues, "depends-on target 必须为 workcase", f"{path}.target.fact_type_key")
            layout = LAYOUTS.get(target_type) if isinstance(target_type, str) else None
            if (
                not isinstance(target_id, str)
                or layout is None
                or layout.object_id_pattern.fullmatch(target_id) is None
            ):
                _issue(issues, "relation target.object_id 必须匹配目标类型稳定身份", f"{path}.target.object_id")
            elif target_id == source_id:
                _issue(issues, "WorkCase relation 禁止自指", f"{path}.target.object_id")
        identity = (relation_key, target.get("governed_project_id"), target.get("fact_type_key"), target_id)
        observed.append(identity)
    if len(observed) != len(set(observed)):
        _issue(issues, "同一 relation_key 与 target 不得重复", "relations")
    keys_by_target: dict[tuple[object, ...], set[object]] = {}
    for identity in observed:
        relation_key, target_identity = identity[0], identity[1:]
        keys_by_target.setdefault(target_identity, set()).add(relation_key)
    if any("related-to" in keys and len(keys) > 1 for keys in keys_by_target.values()):
        _issue(issues, "related-to 不得与同一 target 的强关系重叠", "relations")


def _require_complete_result(fields: Mapping[str, object], issues: list[FactIssue], *, context: str) -> None:
    _require(fields, _RESULT_PROJECTION_FIELDS, issues, context=context)
    if not all_terminal(fields):
        _issue(issues, "完整结果投影要求全部 work item terminal", "work_items")
    elif all(name in fields for name in _RESULT_PROJECTION_FIELDS) and not result_projection_complete(fields):
        _issue(issues, "canonical result projection 结构不完整", "success_criterion_results")


def _validate_termination(fields: Mapping[str, object], issues: list[FactIssue]) -> None:
    value = fields.get("termination")
    if not isinstance(value, Mapping):
        _issue(issues, "termination 必须是 object", "termination")
        return
    unknown = set(value) - _TERMINATION_ALLOWED
    for name in sorted(unknown):
        _issue(issues, "termination 包含未登记字段", f"termination.{name}")
    _require(value, _TERMINATION_REQUIRED, issues, context="termination ")
    for name in ("initiated_at", "reason", "cleanup_summary"):
        if name in value and not _nonempty_string(value.get(name)):
            _issue(issues, "termination string 成员必须非空", f"termination.{name}")
    if value.get("source_status") not in ACTIVE_STATUSES:
        _issue(issues, "termination source_status 必须为 open 或 blocked", "termination.source_status")
    source_phase = value.get("source_phase")
    if source_phase not in ACTIVE_PHASES - {"termination_preparing"}:
        _issue(issues, "termination source_phase 必须为原活动 phase", "termination.source_phase")
    fingerprint = value.get("source_content_fingerprint")
    if not isinstance(fingerprint, str) or _SHA256.fullmatch(fingerprint) is None:
        _issue(
            issues,
            "termination source_content_fingerprint 必须为 SHA-256",
            "termination.source_content_fingerprint",
        )
    for name in ("source_refs", "item_snapshots", "quality_steps"):
        if name in value:
            _validate_unique_strings(value.get(name), f"termination.{name}", issues)
    for name in _TERMINATION_OPTIONAL_ARRAYS:
        members = value.get(name)
        if name not in value:
            continue
        if not isinstance(members, list) or any(not _nonempty_string(member) for member in members):
            _issue(
                issues,
                "termination 善后范围必须是非空 string array；已检查且无时写 none-observed 边界",
                f"termination.{name}",
            )
        elif len(members) != len(set(members)):
            _issue(issues, "termination 善后范围不得重复", f"termination.{name}")
    quality_steps = value.get("quality_steps")
    if isinstance(quality_steps, list):
        observed_keys: list[str] = []
        for member in quality_steps:
            match = _TERMINATION_QUALITY_STEP.fullmatch(member) if isinstance(member, str) else None
            if match is None:
                _issue(
                    issues,
                    "termination quality_steps 只允许三项标准步骤及 not_reached/actual/skipped",
                    "termination.quality_steps",
                )
                continue
            observed_keys.append(match.group(1))
        expected_keys = {"independent_result_review", "closure_proposal", "gate_2"}
        if set(observed_keys) != expected_keys or len(observed_keys) != len(expected_keys):
            _issue(issues, "termination quality_steps 必须逐项且仅一次覆盖三项标准步骤", "termination.quality_steps")
    if value.get("cleanup_status") not in {"pending", "blocked", "completed"}:
        _issue(issues, "termination cleanup_status 不在当前闭集", "termination.cleanup_status")


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

    if phase == "termination_preparing":
        _require(fields, {"termination"}, issues, context="termination_preparing ")
        _validate_termination(fields, issues)
        return
    _forbid(fields, {"termination"}, issues, context=f"{phase} ")
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
    if "termination" in fields:
        _validate_termination(fields, issues)
        termination = fields.get("termination")
        if isinstance(termination, Mapping) and termination.get("cleanup_status") != "completed":
            _issue(issues, "closed termination 必须已完成善后", "termination.cleanup_status")
        if isinstance(termination, Mapping):
            for name in _TERMINATION_OPTIONAL_ARRAYS:
                if name not in termination:
                    _issue(issues, "closed termination 必须显式记录已检查的善后范围", f"termination.{name}")
            quality_steps = termination.get("quality_steps")
            if isinstance(quality_steps, list) and any(
                isinstance(member, str) and member.endswith(":not_reached") for member in quality_steps
            ):
                _issue(issues, "closed termination 的质量步骤不得保留 not_reached", "termination.quality_steps")
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
        _issue(
            issues, "非 completed closed WorkCase 必须保留剩余责任、routed-to 或受限 Spark 建议", "disposition_summary"
        )


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
    "REQUIRED_QUALITY_GATE_ID",
    "REQUIRED_REVIEWER_MODE",
    "REVIEW_CONCLUSIONS",
    "required_quality_gate_issues",
    "validate_workcase_snapshot",
]
