"""Deterministic fact-object checks derived from projected fields and type sources."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from ldvh.facts.contracts import LAYOUTS, TERMINAL_COMMON
from ldvh.facts.models import FactIssue
from ldvh.facts.schema import FactSchema
from ldvh.facts.workcase_projection import PROJECTION_KEYS, workcase_subject_fingerprint


@dataclass(slots=True)
class _Node:
    json_type: str | None = None
    presence: str = "conditional"
    children: dict[str, _Node] = field(default_factory=dict)


def _tree(schema: FactSchema) -> _Node:
    root = _Node(json_type="object", presence="required")
    for projected in schema.fields:
        current = root
        for raw_segment in projected.path.split("."):
            segment = raw_segment.removesuffix("[]")
            current = current.children.setdefault(segment, _Node())
        current.json_type = projected.json_type
        current.presence = projected.presence
    return root


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def _join(parent: str, child: str) -> str:
    return child if not parent else f"{parent}.{child}"


def _validate_node(value: Any, node: _Node, path: str, issues: list[FactIssue]) -> None:
    expected = node.json_type
    if expected is None or not _matches_type(value, expected):
        issues.append(FactIssue("schema", f"字段必须是 {expected or '已登记类型'}", path))
        return
    if isinstance(value, str) and not value:
        issues.append(FactIssue("schema", "string 字段不得为空", path))
        return
    if isinstance(value, list):
        if not value:
            issues.append(FactIssue("schema", "array 字段出现时不得为空", path))
            return
        if node.children:
            for index, item in enumerate(value):
                item_path = f"{path}[{index}]"
                if not isinstance(item, dict):
                    issues.append(FactIssue("schema", "array 成员必须是 object", item_path))
                    continue
                _validate_mapping(item, node, item_path, issues)
        return
    if isinstance(value, dict):
        _validate_mapping(value, node, path, issues)


def _validate_mapping(value: dict[str, Any], node: _Node, path: str, issues: list[FactIssue]) -> None:
    for key in value:
        if not isinstance(key, str):
            issues.append(FactIssue("schema", "JSON object 的字段名必须是 string", path or None))
    string_keys = {key for key in value if isinstance(key, str)}
    unknown = sorted(string_keys - set(node.children))
    for key in unknown:
        issues.append(FactIssue("schema", "字段未在当前 Schema 登记", _join(path, str(key))))
    for key, child in node.children.items():
        child_path = _join(path, key)
        if key not in value:
            if child.presence == "required":
                issues.append(FactIssue("schema", "缺少必填字段", child_path))
            continue
        if child.presence == "forbidden":
            issues.append(FactIssue("schema", "当前类型禁止该字段", child_path))
            continue
        if value[key] is None:
            issues.append(FactIssue("schema", "字段不得使用 null 占位", child_path))
            continue
        _validate_node(value[key], child, child_path, issues)


_RFC3339 = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z"
)


def parse_rfc3339(value: object) -> datetime | None:
    if not isinstance(value, str) or _RFC3339.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _time(value: object, path: str, issues: list[FactIssue]) -> datetime | None:
    parsed = parse_rfc3339(value)
    if parsed is None:
        issues.append(FactIssue("schema", "时间必须是包含 UTC 偏移的 RFC 3339 string", path))
        return None
    return parsed


def _require(fields: dict[str, Any], names: set[str] | frozenset[str], issues: list[FactIssue]) -> None:
    for name in sorted(names):
        if name not in fields:
            issues.append(FactIssue("schema", "当前状态要求该字段", name))


def _forbid(fields: dict[str, Any], names: set[str] | frozenset[str], issues: list[FactIssue]) -> None:
    for name in sorted(names):
        if name in fields:
            issues.append(FactIssue("schema", "当前状态禁止该字段", name))


def _validate_status(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    status = fields.get("status")
    layout = LAYOUTS[fact_type_key]
    if status not in layout.statuses:
        issues.append(FactIssue("schema", f"status 必须属于 {sorted(layout.statuses)}", "status"))
        return
    if "priority" in fields and fields["priority"] not in {"P0", "P1", "P2", "P3"}:
        issues.append(FactIssue("schema", "priority 不在 P0、P1、P2、P3 闭集中", "priority"))
    if fact_type_key == "spark":
        if status == "open":
            _require(fields, {"priority"}, issues)
            _forbid(fields, {"disposition_summary", "closed_at"}, issues)
        elif status == "routed":
            _require(fields, TERMINAL_COMMON, issues)
            _forbid(fields, {"priority"}, issues)
        else:  # discarded
            _require(fields, {"disposition_summary", "closed_at"}, issues)
            _forbid(fields, {"priority"}, issues)
    elif fact_type_key == "workcase":
        terminal = {"validation_summary", "closure_outcome", "disposition_summary", "closed_at"}
        if status == "open":
            _require(fields, {"priority"}, issues)
            _forbid(fields, {"blocking_summary", "closure_approval", "closed_at"}, issues)
        elif status == "blocked":
            _require(fields, {"priority", "blocking_summary"}, issues)
            _forbid(fields, {"closure_approval", "closed_at"}, issues)
        else:
            _require(fields, terminal, issues)
            _forbid(fields, {"priority", "blocking_summary"}, issues)
            if fields.get("closure_outcome") not in {
                "completed",
                "partial",
                "not-achieved",
                "cancelled",
                "superseded",
            }:
                issues.append(FactIssue("schema", "closure_outcome 不在当前闭集中", "closure_outcome"))
    elif fact_type_key == "study":
        if status == "active":
            _require(fields, {"research_intent", "recommendation_summary"}, issues)
            _forbid(fields, {"disposition_summary", "closed_at"}, issues)
        else:
            _require(fields, TERMINAL_COMMON, issues)
    else:
        if status == "active":
            _forbid(fields, {"disposition_summary", "closed_at"}, issues)
        else:
            _require(fields, TERMINAL_COMMON, issues)


_WORKCASE_PHASES = {
    "human_plan_confirming",
    "executing",
    "controller_checking",
    "independent_reviewing",
    "closure_preparing",
    "human_closure_confirming",
    "closed",
}
_WORKCASE_ITEM_STATUSES = {"pending", "in_progress", "blocked", "completed", "cancelled"}
_WORKCASE_REVIEW_CONCLUSIONS = {"pass", "pass_with_followups", "changes_required", "blocked"}
_WORKCASE_CURRENT_PROFILE = "control-contract-v1"
_WORKCASE_CURRENT_BOUNDARY = datetime.fromisoformat("2026-07-20T07:30:00+08:00")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_WORKCASE_CURRENT_ONLY_FIELDS = {
    "success_criterion_definitions",
    "success_criterion_results",
    "audit_summary",
    "residual_responsibilities",
    "nonbinding_followups",
    "improvement_observations",
}
_WORKCASE_RESULT_PHASES = {
    "independent_reviewing",
    "closure_preparing",
    "human_closure_confirming",
    "closed",
}
_LOCAL_ID_PATTERNS = {
    "criterion_id": re.compile(r"criterion-[0-9]{2,}\Z"),
    "audit_id": re.compile(r"audit-[0-9]{2,}\Z"),
    "finding_id": re.compile(r"finding-[0-9]{2,}\Z"),
    "residual_id": re.compile(r"residual-[0-9]{2,}\Z"),
    "followup_id": re.compile(r"followup-[0-9]{2,}\Z"),
    "observation_id": re.compile(r"observation-[0-9]{2,}\Z"),
    "topic_key": re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z"),
}


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _workcase_profile(fields: dict[str, Any]) -> str:
    return "current" if fields.get("workcase_profile") == _WORKCASE_CURRENT_PROFILE else "legacy"


def _validate_unique_local_values(
    values: list[Any],
    *,
    array_name: str,
    member_name: str,
    pattern_name: str | None,
    issues: list[FactIssue],
) -> set[str]:
    observed: list[str] = []
    pattern = _LOCAL_ID_PATTERNS.get(pattern_name or "")
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            continue
        member = value.get(member_name)
        path = f"{array_name}[{index}].{member_name}"
        if not isinstance(member, str):
            continue
        observed.append(member)
        if pattern is not None and pattern.fullmatch(member) is None:
            issues.append(FactIssue("schema", f"{member_name} 格式不符合当前闭集", path))
    if len(observed) != len(set(observed)):
        issues.append(FactIssue("schema", f"{member_name} 在同一 WorkCase 内不得重复", array_name))
    return set(observed)


def _validate_workcase_profile(fields: dict[str, Any], issues: list[FactIssue]) -> str:
    raw_profile = fields.get("workcase_profile")
    created = parse_rfc3339(fields.get("created_at"))
    if raw_profile is not None and raw_profile != _WORKCASE_CURRENT_PROFILE:
        issues.append(
            FactIssue("schema", f"workcase_profile 只允许 {_WORKCASE_CURRENT_PROFILE}", "workcase_profile")
        )
    current = raw_profile == _WORKCASE_CURRENT_PROFILE
    if not current and created is not None and created >= _WORKCASE_CURRENT_BOUNDARY:
        issues.append(
            FactIssue(
                "schema",
                "生效边界后创建的 WorkCase 必须显式使用 current profile",
                "workcase_profile",
            )
        )
    if current:
        _require(fields, {"success_criterion_definitions", "audit_summary"}, issues)
        _forbid(fields, {"success_criteria"}, issues)
    else:
        _require(fields, {"success_criteria"}, issues)
        _forbid(fields, _WORKCASE_CURRENT_ONLY_FIELDS, issues)
        for array_name in ("creation_reviews", "result_reviews"):
            reviews = fields.get(array_name)
            if not isinstance(reviews, list):
                continue
            for index, review in enumerate(reviews):
                if isinstance(review, dict) and "review_basis" in review:
                    issues.append(
                        FactIssue(
                            "schema",
                            "legacy WorkCase review 禁止 review_basis",
                            f"{array_name}[{index}].review_basis",
                        )
                    )
    return "current" if current else "legacy"


def _validate_workcase_criteria(fields: dict[str, Any], profile: str, issues: list[FactIssue]) -> None:
    if profile != "current":
        criteria = fields.get("success_criteria")
        if isinstance(criteria, list):
            if any(not isinstance(item, str) or not item for item in criteria):
                issues.append(FactIssue("schema", "success_criteria 成员必须是非空 string", "success_criteria"))
            elif len(criteria) != len(set(criteria)):
                issues.append(FactIssue("schema", "success_criteria 成员不得重复", "success_criteria"))
        return

    definitions = fields.get("success_criterion_definitions")
    definition_values = definitions if isinstance(definitions, list) else []
    criterion_ids = _validate_unique_local_values(
        definition_values,
        array_name="success_criterion_definitions",
        member_name="criterion_id",
        pattern_name="criterion_id",
        issues=issues,
    )
    statements = [
        item.get("statement")
        for item in definition_values
        if isinstance(item, dict) and isinstance(item.get("statement"), str)
    ]
    if len(statements) != len(set(statements)):
        issues.append(
            FactIssue("schema", "成功标准 statement 在同一 WorkCase 内不得重复", "success_criterion_definitions")
        )

    phase = fields.get("phase")
    if phase in _WORKCASE_RESULT_PHASES:
        _require(fields, {"success_criterion_results"}, issues)
    results = fields.get("success_criterion_results")
    if not isinstance(results, list):
        return
    result_ids = _validate_unique_local_values(
        results,
        array_name="success_criterion_results",
        member_name="criterion_id",
        pattern_name="criterion_id",
        issues=issues,
    )
    if result_ids != criterion_ids:
        issues.append(
            FactIssue(
                "schema",
                "success_criterion_results 必须按 criterion_id 精确覆盖当前成功标准",
                "success_criterion_results",
            )
        )
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            continue
        path = f"success_criterion_results[{index}]"
        outcome = result.get("outcome")
        if outcome not in {"satisfied", "not_satisfied", "not_verified"}:
            issues.append(FactIssue("schema", "criterion outcome 不在当前闭集中", f"{path}.outcome"))


def _validate_workcase_audit(fields: dict[str, Any], profile: str, issues: list[FactIssue]) -> None:
    if profile != "current":
        return
    entries = fields.get("audit_summary")
    if not isinstance(entries, list):
        return
    _validate_unique_local_values(
        entries,
        array_name="audit_summary",
        member_name="audit_id",
        pattern_name="audit_id",
        issues=issues,
    )
    finding_values: list[dict[str, Any]] = []
    subject_kinds: list[object] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        path = f"audit_summary[{index}]"
        subject_kind = entry.get("subject_kind")
        subject_kinds.append(subject_kind)
        if subject_kind not in {"pre_creation_plan", "superseded_plan", "superseded_result"}:
            issues.append(FactIssue("schema", "audit subject_kind 不在当前闭集中", f"{path}.subject_kind"))
        for name in ("subject_version", "review_count"):
            if not _positive_integer(entry.get(name)):
                issues.append(FactIssue("schema", f"audit {name} 必须是正整数", f"{path}.{name}"))
        findings = entry.get("findings")
        if isinstance(findings, list):
            finding_values.extend(item for item in findings if isinstance(item, dict))
    created = parse_rfc3339(fields.get("created_at"))
    if created is not None and created >= _WORKCASE_CURRENT_BOUNDARY and "pre_creation_plan" not in subject_kinds:
        issues.append(
            FactIssue("schema", "current 新建 WorkCase 必须保留 pre_creation_plan audit", "audit_summary")
        )
    _validate_unique_local_values(
        finding_values,
        array_name="audit_summary.findings",
        member_name="finding_id",
        pattern_name="finding_id",
        issues=issues,
    )
    for finding in finding_values:
        finding_id = finding.get("finding_id")
        path = f"audit_summary.findings[{finding_id if isinstance(finding_id, str) else '?'}]"
        if finding.get("controller_disposition") not in {"accepted", "corrected", "rejected", "carried"}:
            issues.append(
                FactIssue("schema", "audit controller_disposition 不在当前闭集中", f"{path}.controller_disposition")
            )
        if finding.get("rereview_outcome") not in {"performed", "not_required"}:
            issues.append(FactIssue("schema", "audit rereview_outcome 不在当前闭集中", f"{path}.rereview_outcome"))
        if finding.get("final_route") not in {
            "current_plan",
            "current_result",
            "nonbinding_followup",
            "residual_responsibility",
            "rejected",
        }:
            issues.append(FactIssue("schema", "audit final_route 不在当前闭集中", f"{path}.final_route"))


def _validate_workcase_observations(fields: dict[str, Any], profile: str, issues: list[FactIssue]) -> None:
    if profile != "current":
        return
    residuals = fields.get("residual_responsibilities")
    residual_values = residuals if isinstance(residuals, list) else []
    residual_ids = _validate_unique_local_values(
        residual_values,
        array_name="residual_responsibilities",
        member_name="residual_id",
        pattern_name="residual_id",
        issues=issues,
    )
    for index, residual in enumerate(residual_values):
        if isinstance(residual, dict) and residual.get("disposition") not in {"routed", "accepted_stop"}:
            issues.append(
                FactIssue(
                    "schema",
                    "residual disposition 不在当前闭集中",
                    f"residual_responsibilities[{index}].disposition",
                )
            )

    followups = fields.get("nonbinding_followups")
    followup_values = followups if isinstance(followups, list) else []
    followup_ids = _validate_unique_local_values(
        followup_values,
        array_name="nonbinding_followups",
        member_name="followup_id",
        pattern_name="followup_id",
        issues=issues,
    )
    observations = fields.get("improvement_observations")
    if not isinstance(observations, list):
        return
    if "result_version" not in fields:
        issues.append(
            FactIssue("schema", "improvement_observations 要求有效 result_version", "result_version")
        )
    if len(observations) > 20:
        issues.append(FactIssue("schema", "单一 result_version 最多保留 20 项 observation", "improvement_observations"))
    _validate_unique_local_values(
        observations,
        array_name="improvement_observations",
        member_name="observation_id",
        pattern_name="observation_id",
        issues=issues,
    )
    _validate_unique_local_values(
        observations,
        array_name="improvement_observations",
        member_name="topic_key",
        pattern_name="topic_key",
        issues=issues,
    )
    item_ids = {
        item.get("item_id")
        for item in fields.get("work_items", [])
        if isinstance(item, dict) and isinstance(item.get("item_id"), str)
    }
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            continue
        path = f"improvement_observations[{index}]"
        if observation.get("ownership") not in {"current_scope", "adjacent_project", "external"}:
            issues.append(FactIssue("schema", "observation ownership 不在当前闭集中", f"{path}.ownership"))
        dimensions = observation.get("value_dimensions")
        if isinstance(dimensions, list):
            if any(value not in {f"V{number}" for number in range(1, 9)} for value in dimensions):
                issues.append(FactIssue("schema", "value_dimensions 只允许 V1–V8", f"{path}.value_dimensions"))
            elif len(dimensions) != len(set(dimensions)):
                issues.append(FactIssue("schema", "value_dimensions 不得重复", f"{path}.value_dimensions"))
        disposition = observation.get("disposition")
        disposition_ref = observation.get("disposition_ref")
        if disposition == "absorbed_current_scope":
            expected_refs = item_ids
        elif disposition == "nonbinding_followup":
            expected_refs = followup_ids
        elif disposition == "residual_responsibility":
            expected_refs = residual_ids
        elif disposition == "rejected":
            expected_refs = None
        else:
            expected_refs = set()
            issues.append(FactIssue("schema", "observation disposition 不在当前闭集中", f"{path}.disposition"))
        if expected_refs is None:
            if "disposition_ref" in observation:
                issues.append(
                    FactIssue(
                        "schema",
                        "rejected observation 禁止 disposition_ref",
                        f"{path}.disposition_ref",
                    )
                )
        elif disposition_ref not in expected_refs:
            issues.append(
                FactIssue("schema", "observation disposition_ref 未指向相应 local ID", f"{path}.disposition_ref")
            )


def _validate_workcase_items(fields: dict[str, Any], issues: list[FactIssue]) -> None:
    values = fields.get("work_items")
    if not isinstance(values, list):
        return
    item_ids = [item.get("item_id") for item in values if isinstance(item, dict)]
    string_ids = [item_id for item_id in item_ids if isinstance(item_id, str)]
    if len(string_ids) != len(set(string_ids)):
        issues.append(FactIssue("schema", "work_items.item_id 不得重复", "work_items"))
    known = set(string_ids)
    statuses = {
        item.get("item_id"): item.get("status")
        for item in values
        if isinstance(item, dict) and isinstance(item.get("item_id"), str)
    }
    graph: dict[str, set[str]] = {item_id: set() for item_id in string_ids}
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            continue
        path = f"work_items[{index}]"
        item_id = item.get("item_id")
        if isinstance(item_id, str) and re.fullmatch(r"item-[0-9]{2,}", item_id) is None:
            issues.append(FactIssue("schema", "item_id 必须匹配 item-[0-9]{2,}", f"{path}.item_id"))
        status = item.get("status")
        if status not in _WORKCASE_ITEM_STATUSES:
            issues.append(FactIssue("schema", "work item status 不在当前闭集中", f"{path}.status"))
            continue
        conditions = {"current_summary", "resume_from", "blocking_summary", "result_summary"}
        required: set[str] = set()
        allowed: set[str] = set()
        if status == "in_progress":
            required = {"current_summary", "resume_from"}
            allowed = {"current_summary", "resume_from"}
        elif status == "blocked":
            required = {"current_summary", "resume_from", "blocking_summary"}
            allowed = required
        elif status == "completed":
            required = {"result_summary"}
            allowed = required
        elif status == "cancelled":
            required = {"result_summary"}
            allowed = {"result_summary"}
        for name in sorted(required - set(item)):
            issues.append(FactIssue("schema", "当前 work item 状态要求该字段", f"{path}.{name}"))
        for name in sorted((conditions - allowed) & set(item)):
            issues.append(FactIssue("schema", "当前 work item 状态禁止该字段", f"{path}.{name}"))
        dependencies = item.get("depends_on")
        if not isinstance(dependencies, list):
            continue
        if any(not isinstance(target, str) or not target for target in dependencies):
            issues.append(FactIssue("schema", "depends_on 成员必须是非空 item_id", f"{path}.depends_on"))
            continue
        if len(dependencies) != len(set(dependencies)):
            issues.append(FactIssue("schema", "depends_on 成员不得重复", f"{path}.depends_on"))
        for target in dependencies:
            if target not in known:
                issues.append(FactIssue("schema", "depends_on 目标不存在", f"{path}.depends_on"))
            elif target == item_id:
                issues.append(FactIssue("schema", "work item 不得依赖自身", f"{path}.depends_on"))
            elif isinstance(item_id, str):
                graph[item_id].add(target)
            if status == "in_progress" and statuses.get(target) not in {"completed", "cancelled"}:
                issues.append(FactIssue("schema", "in_progress work item 的依赖必须已完成或取消", f"{path}.depends_on"))
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in graph.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(visit(node) for node in graph if node not in visited):
        issues.append(FactIssue("schema", "work item depends_on 有向图不得成环", "work_items"))


def _validate_workcase_reviews(
    fields: dict[str, Any],
    array_name: str,
    version_name: str,
    profile: str,
    issues: list[FactIssue],
) -> None:
    values = fields.get(array_name)
    version = fields.get(version_name)
    if not isinstance(values, list):
        return
    for index, review in enumerate(values):
        if not isinstance(review, dict):
            continue
        path = f"{array_name}[{index}]"
        if _positive_integer(version) and review.get("subject_version") != version:
            issues.append(FactIssue("schema", f"审核必须绑定当前 {version_name}", f"{path}.subject_version"))
        if review.get("conclusion") not in _WORKCASE_REVIEW_CONCLUSIONS:
            issues.append(FactIssue("schema", "review conclusion 不在当前闭集中", f"{path}.conclusion"))
        feedback = review.get("feedback")
        if isinstance(feedback, list):
            if any(not isinstance(item, str) or not item for item in feedback):
                issues.append(FactIssue("schema", "review feedback 成员必须是非空 string", f"{path}.feedback"))
            elif len(feedback) != len(set(feedback)):
                issues.append(FactIssue("schema", "review feedback 不得重复", f"{path}.feedback"))
        if profile == "legacy":
            if "controller_resolution" not in review:
                issues.append(
                    FactIssue(
                        "schema",
                        "legacy review 必须包含 Controller 处置",
                        f"{path}.controller_resolution",
                    )
                )
            continue
        basis = review.get("review_basis")
        if not isinstance(basis, dict):
            issues.append(FactIssue("schema", "current review 必须包含 review_basis", f"{path}.review_basis"))
        else:
            projection_key = basis.get("projection_key")
            subject_fingerprint = basis.get("subject_fingerprint")
            allowed_keys = {"plan_current"} if array_name == "creation_reviews" else {
                "result_implementation",
                "result_with_closure_report",
            }
            if projection_key not in allowed_keys:
                issues.append(
                    FactIssue(
                        "schema",
                        "review projection_key 不适用于当前审核域",
                        f"{path}.review_basis.projection_key",
                    )
                )
            if not isinstance(subject_fingerprint, str) or _SHA256_PATTERN.fullmatch(
                subject_fingerprint
            ) is None:
                issues.append(
                    FactIssue(
                        "schema",
                        "review subject_fingerprint 必须是 64 位小写 SHA-256",
                        f"{path}.review_basis.subject_fingerprint",
                    )
                )
            elif projection_key in PROJECTION_KEYS and (
                array_name == "creation_reviews" or "controller_resolution" not in review
            ):
                expected = workcase_subject_fingerprint(fields, projection_key)
                if subject_fingerprint != expected:
                    issues.append(
                        FactIssue(
                            "schema",
                            "review subject_fingerprint 与形成时主体投影不一致",
                            f"{path}.review_basis.subject_fingerprint",
                        )
                    )
        if array_name == "creation_reviews" or fields.get("phase") != "independent_reviewing":
            if "controller_resolution" not in review:
                issues.append(
                    FactIssue(
                        "schema",
                        "离开独立审核前 review 必须包含 Controller 处置",
                        f"{path}.controller_resolution",
                    )
                )


def _validate_workcase(fields: dict[str, Any], issues: list[FactIssue]) -> None:
    profile = _validate_workcase_profile(fields, issues)
    status = fields.get("status")
    phase = fields.get("phase")
    if phase not in _WORKCASE_PHASES:
        issues.append(FactIssue("schema", "phase 不在 WorkCase 推进阶段闭集中", "phase"))
    if not _positive_integer(fields.get("plan_version")):
        issues.append(FactIssue("schema", "plan_version 必须是正整数", "plan_version"))
    if status == "closed":
        if phase != "closed":
            issues.append(FactIssue("schema", "closed WorkCase 的 phase 必须为 closed", "phase"))
        _forbid(fields, {"resume_from", "waiting_on"}, issues)
    else:
        _require(fields, {"resume_from"}, issues)
        if phase == "closed":
            issues.append(FactIssue("schema", "非 closed WorkCase 不得使用 closed phase", "phase"))
    if phase in {"human_plan_confirming", "human_closure_confirming"}:
        _require(fields, {"waiting_on"}, issues)
    if phase == "human_plan_confirming":
        _forbid(
            fields,
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
                "closed_at",
            },
            issues,
        )
    if phase == "executing":
        _forbid(
            fields,
            {
                "closure_approval",
                "validation_summary",
                "closure_outcome",
                "disposition_summary",
                "closed_at",
            },
            issues,
        )
    if phase == "controller_checking":
        _forbid(fields, {"closure_approval", "closed_at"}, issues)
    if phase == "independent_reviewing":
        _forbid(fields, {"closure_approval", "closed_at"}, issues)
    if phase == "closure_preparing":
        _forbid(fields, {"closure_approval", "closed_at"}, issues)
    if phase in {
        "executing",
        "controller_checking",
        "independent_reviewing",
        "closure_preparing",
        "human_closure_confirming",
        "closed",
    }:
        _require(fields, {"execution_approval"}, issues)
    if phase == "executing":
        items = fields.get("work_items")
        if isinstance(items, list) and not any(
            isinstance(item, dict) and item.get("status") not in {"completed", "cancelled"} for item in items
        ):
            issues.append(FactIssue("schema", "executing 阶段必须仍有未完成工作项", "work_items"))
    if phase in {
        "controller_checking",
        "independent_reviewing",
        "closure_preparing",
        "human_closure_confirming",
        "closed",
    }:
        _require(fields, {"result_version"}, issues)
        items = fields.get("work_items")
        if isinstance(items, list) and any(
            isinstance(item, dict) and item.get("status") not in {"completed", "cancelled"} for item in items
        ):
            issues.append(FactIssue("schema", "进入结果阶段前全部 work item 必须完成或取消", "work_items"))
    result_context_fields = {
        "success_criterion_results",
        "controller_check_summary",
        "result_reviews",
        "improvement_observations",
        "residual_responsibilities",
        "nonbinding_followups",
        "validation_summary",
        "closure_outcome",
        "disposition_summary",
    }
    if "result_version" in fields and not _positive_integer(fields.get("result_version")):
        issues.append(FactIssue("schema", "result_version 必须是正整数", "result_version"))
    if any(key in fields for key in result_context_fields) and "result_version" not in fields:
        issues.append(FactIssue("schema", "结果从属字段要求有效 result_version", "result_version"))
    if phase in {"independent_reviewing", "closure_preparing", "human_closure_confirming", "closed"}:
        _require(fields, {"controller_check_summary"}, issues)
    if phase in {"closure_preparing", "human_closure_confirming", "closed"}:
        _require(fields, {"result_reviews"}, issues)
    if phase in {"human_closure_confirming", "closed"}:
        _require(fields, {"validation_summary", "closure_outcome", "disposition_summary"}, issues)
    if phase == "human_closure_confirming":
        _forbid(fields, {"closure_approval", "closed_at"}, issues)
    if phase == "closed":
        _require(fields, {"closure_approval"}, issues)
    plan_version = fields.get("plan_version")
    approval = fields.get("execution_approval")
    if (
        isinstance(approval, dict)
        and _positive_integer(plan_version)
        and approval.get("subject_version") != plan_version
    ):
        issues.append(
            FactIssue("schema", "execution_approval 必须绑定当前 plan_version", "execution_approval.subject_version")
        )
    result_version = fields.get("result_version")
    closure = fields.get("closure_approval")
    if (
        isinstance(closure, dict)
        and _positive_integer(result_version)
        and closure.get("subject_version") != result_version
    ):
        issues.append(
            FactIssue("schema", "closure_approval 必须绑定当前 result_version", "closure_approval.subject_version")
        )
    _validate_workcase_items(fields, issues)
    _validate_workcase_criteria(fields, profile, issues)
    _validate_workcase_audit(fields, profile, issues)
    _validate_workcase_observations(fields, profile, issues)
    _validate_workcase_reviews(fields, "creation_reviews", "plan_version", profile, issues)
    _validate_workcase_reviews(fields, "result_reviews", "result_version", profile, issues)


def _validate_times(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    created = _time(fields.get("created_at"), "created_at", issues) if "created_at" in fields else None
    updated = _time(fields.get("updated_at"), "updated_at", issues) if "updated_at" in fields else None
    if created is not None and updated is not None and created > updated:
        issues.append(FactIssue("schema", "created_at 不得晚于 updated_at", "created_at"))
    closed = _time(fields.get("closed_at"), "closed_at", issues) if "closed_at" in fields else None
    if created is not None and closed is not None and created > closed:
        issues.append(FactIssue("schema", "closed_at 不得早于 created_at", "closed_at"))
    if updated is not None and closed is not None and closed > updated:
        issues.append(FactIssue("schema", "closed_at 不得晚于 updated_at", "closed_at"))
    if fact_type_key == "adr" and "decided_at" in fields:
        decided = _time(fields["decided_at"], "decided_at", issues)
        if decided is not None and created is not None and decided > created:
            issues.append(FactIssue("schema", "decided_at 不得晚于 created_at", "decided_at"))
    if fact_type_key == "spark" and isinstance(fields.get("evolution"), list):
        evolution = fields["evolution"]
        if len(evolution) > 8:
            issues.append(FactIssue("schema", "evolution 最多保留 8 项", "evolution"))
        for index, entry in enumerate(evolution):
            if not isinstance(entry, dict) or "at" not in entry:
                continue
            at = _time(entry["at"], f"evolution[{index}].at", issues)
            if at is not None and created is not None and at < created:
                issues.append(FactIssue("schema", "evolution.at 不得早于 created_at", f"evolution[{index}].at"))
            if at is not None and updated is not None and at > updated:
                issues.append(FactIssue("schema", "evolution.at 不得晚于 updated_at", f"evolution[{index}].at"))
    if fact_type_key == "workcase":
        nested_times: list[tuple[str, object, bool]] = []
        for array_name in ("creation_reviews", "result_reviews"):
            values = fields.get(array_name)
            if isinstance(values, list):
                nested_times.extend(
                    (
                        f"{array_name}[{index}].reviewed_at",
                        value.get("reviewed_at"),
                        array_name != "creation_reviews",
                    )
                    for index, value in enumerate(values)
                    if isinstance(value, dict) and "reviewed_at" in value
                )
        for approval_name in ("execution_approval", "closure_approval"):
            value = fields.get(approval_name)
            if isinstance(value, dict) and "approved_at" in value:
                nested_times.append((f"{approval_name}.approved_at", value["approved_at"], True))
        for path, value, requires_created_lower_bound in nested_times:
            at = _time(value, path, issues)
            if at is not None and created is not None and requires_created_lower_bound and at < created:
                issues.append(FactIssue("schema", "WorkCase 事件时间不得早于 created_at", path))
            if at is not None and updated is not None and at > updated:
                issues.append(FactIssue("schema", "WorkCase 事件时间不得晚于 updated_at", path))


def _validate_references(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    urls = fields.get("urls")
    if urls is None:
        if fact_type_key == "study":
            issues.append(FactIssue("reference", "Study 必须至少包含一项 urls", "urls"))
        return
    if not isinstance(urls, list):
        return
    seen: set[str] = set()
    for index, value in enumerate(urls):
        if not isinstance(value, dict):
            continue
        ref = value.get("ref")
        if not isinstance(ref, str) or urlparse(ref).scheme not in {"http", "https"} or not urlparse(ref).netloc:
            issues.append(FactIssue("reference", "urls.ref 必须是绝对 HTTP(S) URL", f"urls[{index}].ref"))
            continue
        if ref in seen:
            issues.append(FactIssue("reference", "同一对象中 urls.ref 不得重复", f"urls[{index}].ref"))
        seen.add(ref)


def _validate_relations(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    relations = fields.get("relations")
    if not isinstance(relations, list):
        return
    allowed = LAYOUTS[fact_type_key].relation_keys
    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            continue
        path = f"relations[{index}]"
        if relation.get("relation_key") not in allowed:
            issues.append(FactIssue("relation", "relation_key 不在当前类型闭集中", f"{path}.relation_key"))


def validate_fact_object(fact_type_key: str, fields: dict[str, Any], schema: FactSchema) -> tuple[FactIssue, ...]:
    issues: list[FactIssue] = []
    _validate_mapping(fields, _tree(schema), "", issues)
    if fields.get("fact_type_key") != fact_type_key:
        issues.append(FactIssue("identity", "fact_type_key 与请求类型不一致", "fact_type_key"))
    _validate_status(fact_type_key, fields, issues)
    if fact_type_key == "workcase":
        _validate_workcase(fields, issues)
    _validate_times(fact_type_key, fields, issues)
    _validate_references(fact_type_key, fields, issues)
    _validate_relations(fact_type_key, fields, issues)
    return tuple(issues)


__all__ = ["parse_rfc3339", "validate_fact_object"]
