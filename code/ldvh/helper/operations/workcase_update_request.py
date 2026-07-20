"""Parse inputs for the source-defined update-workcase operation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactReference
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import parse_rfc3339
from ldvh.facts.workcase_update import PLAN_RESET_FIELDS
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS = (
    "arguments.fact_ref",
    "arguments.expected_content_fingerprint",
    "arguments.set",
    "arguments.remove",
    "arguments.managed_records",
)
OPTIONAL_INPUTS = (
    "work_object_locators",
    "arguments.workspace_root",
    "authorization_reference",
)

_ARGUMENT_FIELDS = frozenset(
    {"workspace_root", "fact_ref", "expected_content_fingerprint", "set", "remove", "managed_records"}
)
_FACT_REF_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})
_MANAGED_FIELDS = frozenset(
    {
        "replace_creation_reviews",
        "append_result_reviews",
        "resolve_result_reviews",
        "execution_approval",
        "closure_approval",
    }
)
_CREATION_REVIEW_FIELDS = frozenset({"reviewer", "scope", "conclusion", "feedback", "controller_resolution"})
_RESULT_REVIEW_FIELDS = frozenset({"reviewer", "scope", "conclusion", "feedback", "projection_key"})
_RESOLUTION_FIELDS = frozenset({"review_index", "controller_resolution"})
_APPROVAL_FIELDS = frozenset({"summary", "source_refs"})
_SOURCE_REF_FIELDS = frozenset({"kind", "locator", "version", "observed_at", "details"})
_REVIEW_CONCLUSIONS = frozenset({"pass", "pass_with_followups", "changes_required", "blocked"})
_RESULT_PROJECTIONS = frozenset({"result_implementation", "result_with_closure_report"})
_ORDINARY_MANAGED_FIELDS = frozenset(
    {
        "object_id",
        "fact_type_key",
        "created_at",
        "updated_at",
        "workcase_profile",
        "creation_reviews",
        "result_reviews",
        "execution_approval",
        "closure_approval",
        "closed_at",
    }
)
_VERSION_FIELDS = frozenset({"plan_version", "result_version"})
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class WorkCaseUpdateRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: FactReference
    expected_content_fingerprint: str
    set_fields: dict[str, Any]
    remove_fields: tuple[str, ...]
    managed_records: dict[str, Any]
    authorization_reference: tuple[dict[str, Any], ...]
    base: Path


@dataclass(frozen=True, slots=True)
class WorkCaseUpdateRequestParseResult:
    request: WorkCaseUpdateRequest | None
    problems: tuple[str, ...]


def workcase_top_level_fields(schema: FactSchema) -> frozenset[str]:
    """Project top-level names from the current source-derived WorkCase schema."""

    if schema.fact_type_key != "workcase":
        raise ValueError("workcase schema required")
    return frozenset(field.path.split(".", 1)[0].split("[]", 1)[0] for field in schema.fields)


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _closed_member(value: object, path: str, fields: frozenset[str], problems: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        problems.append(f"{path} 必须是 object")
        return None
    unknown = sorted(key for key in value if isinstance(key, str) and key not in fields)
    if unknown:
        problems.append(f"{path} 包含未知字段: {', '.join(unknown)}")
    non_string_keys = [key for key in value if not isinstance(key, str)]
    if non_string_keys:
        problems.append(f"{path} 的字段名必须是 string")
    missing = sorted(fields - {key for key in value if isinstance(key, str)})
    if missing:
        problems.append(f"{path} 缺少字段: {', '.join(missing)}")
    return value


def _review_member(value: object, path: str, fields: frozenset[str], problems: list[str]) -> dict[str, Any] | None:
    member = _closed_member(value, path, fields, problems)
    if member is None:
        return None
    for name in ("reviewer", "scope"):
        if not _nonempty_string(member.get(name)):
            problems.append(f"{path}.{name} 必须是非空 string")
    conclusion = member.get("conclusion")
    if conclusion not in _REVIEW_CONCLUSIONS:
        problems.append(f"{path}.conclusion 不在当前闭集中")
    feedback = member.get("feedback")
    if not isinstance(feedback, list) or not feedback:
        problems.append(f"{path}.feedback 必须是非空 array")
    elif any(not _nonempty_string(item) for item in feedback):
        problems.append(f"{path}.feedback 成员必须是非空 string")
    elif len(feedback) != len(set(feedback)):
        problems.append(f"{path}.feedback 成员不得重复")
    return member


def _source_ref(value: object, path: str, problems: list[str]) -> None:
    if not isinstance(value, dict):
        problems.append(f"{path} 必须是 object")
        return
    unknown = sorted(key for key in value if isinstance(key, str) and key not in _SOURCE_REF_FIELDS)
    if unknown:
        problems.append(f"{path} 包含未知字段: {', '.join(unknown)}")
    if any(not isinstance(key, str) for key in value):
        problems.append(f"{path} 的字段名必须是 string")
    for name in ("kind", "locator"):
        if not _nonempty_string(value.get(name)):
            problems.append(f"{path}.{name} 必须是非空 string")
    for name in ("version", "observed_at"):
        if name in value and not _nonempty_string(value[name]):
            problems.append(f"{path}.{name} 出现时必须是非空 string")
    observed_at = value.get("observed_at")
    if isinstance(observed_at, str) and observed_at and parse_rfc3339(observed_at) is None:
        problems.append(f"{path}.observed_at 必须是包含 UTC 偏移的 RFC 3339 时间")
    if "details" in value and not isinstance(value["details"], dict):
        problems.append(f"{path}.details 出现时必须是 object")


def _approval(value: object, path: str, problems: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        problems.append(f"{path} 必须是 object 或 null")
        return None
    unknown = sorted(key for key in value if isinstance(key, str) and key not in _APPROVAL_FIELDS)
    if unknown:
        problems.append(f"{path} 包含未知字段: {', '.join(unknown)}")
    if any(not isinstance(key, str) for key in value):
        problems.append(f"{path} 的字段名必须是 string")
    if not _nonempty_string(value.get("summary")):
        problems.append(f"{path}.summary 必须是非空 string")
    if "source_refs" in value:
        refs = value["source_refs"]
        if not isinstance(refs, list) or not refs:
            problems.append(f"{path}.source_refs 出现时必须是非空 array")
        else:
            for index, reference in enumerate(refs):
                _source_ref(reference, f"{path}.source_refs[{index}]", problems)
    return value


def _managed_records(value: object, problems: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        problems.append("arguments.managed_records 必须是 object")
        return {}
    unknown = sorted(key for key in value if isinstance(key, str) and key not in _MANAGED_FIELDS)
    if unknown:
        problems.append(f"arguments.managed_records 包含未知字段: {', '.join(unknown)}")
    if any(not isinstance(key, str) for key in value):
        problems.append("arguments.managed_records 的字段名必须是 string")

    normalized: dict[str, Any] = {}
    array_fields = {
        "replace_creation_reviews": _CREATION_REVIEW_FIELDS,
        "append_result_reviews": _RESULT_REVIEW_FIELDS,
        "resolve_result_reviews": _RESOLUTION_FIELDS,
    }
    action_count = 0
    review_indices: list[int] = []
    for name, fields in array_fields.items():
        if name not in value or value[name] is None:
            continue
        items = value[name]
        path = f"arguments.managed_records.{name}"
        if not isinstance(items, list):
            problems.append(f"{path} 必须是 array 或 null")
            continue
        if not items:
            problems.append(f"{path} 出现时必须是非空 array")
        action_count += len(items)
        normalized[name] = [dict(item) if isinstance(item, dict) else item for item in items]
        for index, item in enumerate(items):
            member_path = f"{path}[{index}]"
            if name == "resolve_result_reviews":
                member = _closed_member(item, member_path, fields, problems)
                if member is None:
                    continue
                review_index = member.get("review_index")
                if not isinstance(review_index, int) or isinstance(review_index, bool) or review_index < 0:
                    problems.append(f"{member_path}.review_index 必须是非负 integer")
                else:
                    review_indices.append(review_index)
                if not _nonempty_string(member.get("controller_resolution")):
                    problems.append(f"{member_path}.controller_resolution 必须是非空 string")
                continue
            member = _review_member(item, member_path, fields, problems)
            if member is None:
                continue
            if name == "replace_creation_reviews":
                if not _nonempty_string(member.get("controller_resolution")):
                    problems.append(f"{member_path}.controller_resolution 必须是非空 string")
            elif member.get("projection_key") not in _RESULT_PROJECTIONS:
                problems.append(f"{member_path}.projection_key 不在结果投影闭集中")
    if len(review_indices) != len(set(review_indices)):
        problems.append("arguments.managed_records.resolve_result_reviews 的 review_index 不得重复")

    for name in ("execution_approval", "closure_approval"):
        if name not in value or value[name] is None:
            continue
        action_count += 1
        approval = _approval(value[name], f"arguments.managed_records.{name}", problems)
        if approval is not None:
            normalized[name] = dict(approval)
    if action_count > 16:
        problems.append("arguments.managed_records 单次最多包含 16 项托管动作")
    return normalized


def parse_workcase_update_request(
    request: CommonRequest,
    context: OperationExecutionContext,
    workcase_schema: FactSchema | None = None,
) -> WorkCaseUpdateRequestParseResult:
    """Parse rules that do not require reading the current WorkCase snapshot.

    When supplied, ``workcase_schema`` is the current source-derived schema and
    closes ordinary delta field membership.  Before-dependent version, reset,
    projection-change, index-existence, and final-state checks remain with the
    domain constructor and shared update transaction.
    """

    problems: list[str] = []
    if not context.cwd.is_absolute():
        problems.append("Helper 进程实际 cwd 必须是绝对路径")

    locators: list[str] = []
    for index, locator in enumerate(request.work_object_locators):
        if not isinstance(locator, str) or not locator:
            problems.append(f"work_object_locators[{index}] 必须是非空路径 string")
        else:
            locators.append(locator)

    unknown = sorted(key for key in request.arguments if isinstance(key, str) and key not in _ARGUMENT_FIELDS)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")
    if any(not isinstance(key, str) for key in request.arguments):
        problems.append("arguments 的字段名必须是 string")

    workspace_root: Path | None = None
    if "workspace_root" in request.arguments:
        value = request.arguments["workspace_root"]
        if not isinstance(value, str) or not value or not Path(value).is_absolute():
            problems.append("arguments.workspace_root 必须是非空绝对路径 string")
        else:
            workspace_root = Path(value)

    fact_ref: FactReference | None = None
    raw_ref = request.arguments.get("fact_ref")
    if not isinstance(raw_ref, dict):
        problems.append("arguments.fact_ref 必须是 object")
    else:
        unknown_ref = sorted(key for key in raw_ref if isinstance(key, str) and key not in _FACT_REF_FIELDS)
        if unknown_ref:
            problems.append(f"arguments.fact_ref 包含未知字段: {', '.join(unknown_ref)}")
        if any(not isinstance(key, str) for key in raw_ref):
            problems.append("arguments.fact_ref 的字段名必须是 string")
        values: dict[str, str] = {}
        for name in sorted(_FACT_REF_FIELDS):
            value = raw_ref.get(name)
            if not _nonempty_string(value):
                problems.append(f"arguments.fact_ref.{name} 必须是非空 string")
            else:
                values[name] = value
        if len(values) == len(_FACT_REF_FIELDS):
            if values["fact_type_key"] != "workcase":
                problems.append("arguments.fact_ref.fact_type_key 必须精确等于 workcase")
            elif LAYOUTS["workcase"].object_id_pattern.fullmatch(values["object_id"]) is None:
                problems.append("arguments.fact_ref.object_id 必须匹配 workcase-[0-9]{4,}")
            else:
                fact_ref = FactReference(values["governed_project_id"], "workcase", values["object_id"])

    fingerprint = request.arguments.get("expected_content_fingerprint")
    if not isinstance(fingerprint, str) or _FINGERPRINT.fullmatch(fingerprint) is None:
        problems.append("arguments.expected_content_fingerprint 必须是 64 位小写十六进制 string")

    raw_set = request.arguments.get("set")
    set_fields: dict[str, Any] = {}
    if not isinstance(raw_set, dict):
        problems.append("arguments.set 必须是 object")
    else:
        if any(not isinstance(key, str) or not key for key in raw_set):
            problems.append("arguments.set 的字段名必须是非空 string")
        set_fields = {key: value for key, value in raw_set.items() if isinstance(key, str) and key}

    raw_remove = request.arguments.get("remove")
    remove_fields: list[str] = []
    if not isinstance(raw_remove, list):
        problems.append("arguments.remove 必须是 array")
    else:
        if any(not _nonempty_string(item) for item in raw_remove):
            problems.append("arguments.remove 成员必须是非空顶层字段名 string")
        remove_fields = [item for item in raw_remove if isinstance(item, str) and item]
        if len(remove_fields) != len(set(remove_fields)):
            problems.append("arguments.remove 成员不得重复")

    managed_records = _managed_records(request.arguments.get("managed_records"), problems)

    if workcase_schema is not None:
        allowed = workcase_top_level_fields(workcase_schema)
        unknown_set = sorted(set(set_fields) - allowed)
        unknown_remove = sorted(set(remove_fields) - allowed)
        if unknown_set:
            problems.append(f"arguments.set 引用了未在当前 WorkCase Schema 登记的字段: {', '.join(unknown_set)}")
        if unknown_remove:
            problems.append(f"arguments.remove 引用了未在当前 WorkCase Schema 登记的字段: {', '.join(unknown_remove)}")

    set_managed = sorted(set(set_fields) & _ORDINARY_MANAGED_FIELDS)
    remove_managed = sorted(set(remove_fields) & _ORDINARY_MANAGED_FIELDS)
    if set_managed:
        problems.append(f"arguments.set 不得触碰 Helper 托管字段: {', '.join(set_managed)}")
    if remove_managed:
        problems.append(f"arguments.remove 不得触碰 Helper 托管字段: {', '.join(remove_managed)}")
    removed_versions = sorted(set(remove_fields) & _VERSION_FIELDS)
    if removed_versions:
        problems.append(f"arguments.remove 不得包含版本字段: {', '.join(removed_versions)}")
    overlap = sorted(set(set_fields) & set(remove_fields))
    if overlap:
        problems.append(f"arguments.set 与 arguments.remove 不得交叉: {', '.join(overlap)}")
    for name in sorted(_VERSION_FIELDS & set(set_fields)):
        if not _positive_integer(set_fields[name]):
            problems.append(f"arguments.set.{name} 必须是正整数")

    raw_managed = request.arguments.get("managed_records")
    active_actions = {
        name for name in _MANAGED_FIELDS if isinstance(raw_managed, dict) and raw_managed.get(name) is not None
    }
    if not set_fields and not remove_fields and not active_actions:
        problems.append("arguments.set、arguments.remove、arguments.managed_records 不得同时为空")
    if {"append_result_reviews", "resolve_result_reviews"} <= active_actions:
        problems.append("append_result_reviews 与 resolve_result_reviews 不得同次出现")
    for singleton in ("execution_approval", "closure_approval"):
        if singleton in active_actions and len(active_actions) != 1:
            problems.append(f"{singleton} 不得与其它托管动作同次出现")

    if "plan_version" in set_fields:
        if set_fields.get("phase") != "human_plan_confirming":
            problems.append("set.plan_version 要求显式 set.phase=human_plan_confirming")
        if "replace_creation_reviews" not in active_actions:
            problems.append("set.plan_version 要求同次 replace_creation_reviews")
        if active_actions - {"replace_creation_reviews"}:
            problems.append("set.plan_version 后同次托管动作只允许 replace_creation_reviews")
        reset_conflicts = sorted(set(set_fields) & PLAN_RESET_FIELDS)
        if reset_conflicts:
            problems.append(f"计划升版时 arguments.set 不得包含固定 reset 字段: {', '.join(reset_conflicts)}")
    elif "replace_creation_reviews" in active_actions:
        problems.append("replace_creation_reviews 只能与 set.plan_version 同次出现")

    if "closure_approval" in active_actions and (
        set_fields.get("status") != "closed" or set_fields.get("phase") != "closed"
    ):
        problems.append("closure_approval 要求显式 set.status=closed 且 set.phase=closed")

    if request.observed_context:
        problems.append("observed_context 对 WorkCase 更新操作必须为空 object")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对 WorkCase 更新操作必须为 null 或省略")
    if problems:
        return WorkCaseUpdateRequestParseResult(None, tuple(problems))

    assert fact_ref is not None and isinstance(fingerprint, str)
    governance_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return WorkCaseUpdateRequestParseResult(
        WorkCaseUpdateRequest(
            workspace_root=workspace_root,
            governance_scope=governance_scope,
            fact_ref=fact_ref,
            expected_content_fingerprint=fingerprint,
            set_fields=dict(set_fields),
            remove_fields=tuple(remove_fields),
            managed_records=managed_records,
            authorization_reference=request.authorization_reference,
            base=context.cwd,
        ),
        (),
    )


__all__ = [
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "WorkCaseUpdateRequest",
    "WorkCaseUpdateRequestParseResult",
    "parse_workcase_update_request",
    "workcase_top_level_fields",
]
