"""Parse the three source-defined full-after WorkCase write requests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactReference
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.fact_creation_request import observed_signature_injection_problems
from ldvh.helper.requests import CommonRequest
from ldvh.source_references import source_reference_problems

UPDATE_REQUIRED_INPUTS = (
    "arguments.fact_ref",
    "arguments.expected_content_fingerprint",
    "arguments.fact_object",
)
UPDATE_OPTIONAL_INPUTS = (
    "work_object_locators",
    "arguments.workspace_root",
    "authorization_reference",
)
CLOSE_REQUIRED_INPUTS = (*UPDATE_REQUIRED_INPUTS, "authorization_reference")
CLOSE_OPTIONAL_INPUTS = (
    "work_object_locators",
    "arguments.workspace_root",
)
CORRECT_CLOSED_REQUIRED_INPUTS = (
    *UPDATE_REQUIRED_INPUTS,
    "arguments.route_target_fingerprints",
    "arguments.independent_review_reference",
)
CORRECT_CLOSED_OPTIONAL_INPUTS = UPDATE_OPTIONAL_INPUTS

_COMMON_ARGUMENT_FIELDS = frozenset({"workspace_root", "fact_ref", "expected_content_fingerprint", "fact_object"})
_CORRECT_ARGUMENT_FIELDS = frozenset(
    {*_COMMON_ARGUMENT_FIELDS, "route_target_fingerprints", "independent_review_reference"}
)
_FACT_REF_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})
_ROUTE_TARGET_FINGERPRINT_FIELDS = frozenset({"target", "content_fingerprint"})
_CODE_MANAGED_FIELDS = frozenset({"object_id", "fact_type_key", "created_at", "updated_at"})
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class WorkCaseWriteRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: FactReference
    expected_content_fingerprint: str
    fact_object: dict[str, Any]
    authorization_reference: tuple[dict[str, Any], ...]
    base: Path


@dataclass(frozen=True, slots=True)
class UpdateWorkCaseRequest(WorkCaseWriteRequest):
    """One complete desired active WorkCase snapshot."""


@dataclass(frozen=True, slots=True)
class CloseWorkCaseRequest(WorkCaseWriteRequest):
    """One complete desired closed snapshot plus a Human authorization reference."""


@dataclass(frozen=True, slots=True)
class RouteTargetFingerprint:
    target: FactReference
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class CorrectClosedWorkCaseRequest(WorkCaseWriteRequest):
    route_target_fingerprints: tuple[RouteTargetFingerprint, ...]
    independent_review_reference: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class WorkCaseWriteRequestParseResult:
    request: WorkCaseWriteRequest | None
    problems: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ParsedBase:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: FactReference
    expected_content_fingerprint: str
    fact_object: dict[str, Any]
    authorization_reference: tuple[dict[str, Any], ...]
    base: Path

    def values(self) -> tuple[object, ...]:
        return (
            self.workspace_root,
            self.governance_scope,
            self.fact_ref,
            self.expected_content_fingerprint,
            self.fact_object,
            self.authorization_reference,
            self.base,
        )


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unknown_string_fields(value: dict[object, object], allowed: frozenset[str]) -> list[str]:
    return sorted(key for key in value if isinstance(key, str) and key not in allowed)


def _fact_reference(value: object, path: str, problems: list[str]) -> FactReference | None:
    if not isinstance(value, dict):
        problems.append(f"{path} 必须是 object")
        return None
    unknown = _unknown_string_fields(value, _FACT_REF_FIELDS)
    if unknown:
        problems.append(f"{path} 包含未知字段: {', '.join(unknown)}")
    if any(not isinstance(key, str) for key in value):
        problems.append(f"{path} 的字段名必须是 string")

    parsed: dict[str, str] = {}
    for name in sorted(_FACT_REF_FIELDS):
        member = value.get(name)
        if not _nonempty_string(member):
            problems.append(f"{path}.{name} 必须是非空 string（至少包含一个非空白字符）")
        else:
            parsed[name] = member
    if len(parsed) != len(_FACT_REF_FIELDS):
        return None
    if parsed["fact_type_key"] != "workcase":
        problems.append(f"{path}.fact_type_key 必须精确等于 workcase")
        return None
    if LAYOUTS["workcase"].object_id_pattern.fullmatch(parsed["object_id"]) is None:
        problems.append(f"{path}.object_id 必须匹配 workcase-[0-9]{{4,}}")
        return None
    return FactReference(parsed["governed_project_id"], "workcase", parsed["object_id"])


def _parse_base(
    request: CommonRequest,
    context: OperationExecutionContext,
    *,
    allowed_argument_fields: frozenset[str],
) -> tuple[_ParsedBase | None, list[str]]:
    problems: list[str] = []
    if not context.cwd.is_absolute():
        problems.append("Helper 进程实际 cwd 必须是绝对路径")

    locators: list[str] = []
    for index, locator in enumerate(request.work_object_locators):
        if not _nonempty_string(locator):
            problems.append(f"work_object_locators[{index}] 必须是非空路径 string")
        else:
            locators.append(locator)

    unknown = _unknown_string_fields(request.arguments, allowed_argument_fields)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")
    if any(not isinstance(key, str) for key in request.arguments):
        problems.append("arguments 的字段名必须是 string")

    workspace_root: Path | None = None
    if "workspace_root" in request.arguments:
        value = request.arguments["workspace_root"]
        if not _nonempty_string(value) or not Path(value).is_absolute():
            problems.append("arguments.workspace_root 必须是非空绝对路径 string")
        else:
            workspace_root = Path(value)

    fact_ref = _fact_reference(request.arguments.get("fact_ref"), "arguments.fact_ref", problems)

    fingerprint = request.arguments.get("expected_content_fingerprint")
    if not isinstance(fingerprint, str) or _FINGERPRINT.fullmatch(fingerprint) is None:
        problems.append("arguments.expected_content_fingerprint 必须是 64 位小写十六进制 string")

    raw_fact_object = request.arguments.get("fact_object")
    fact_object: dict[str, Any] = {}
    if not isinstance(raw_fact_object, dict):
        problems.append("arguments.fact_object 必须是 object")
    else:
        if any(not isinstance(key, str) for key in raw_fact_object):
            problems.append("arguments.fact_object 的字段名必须是 string")
        fact_object = {key: value for key, value in raw_fact_object.items() if isinstance(key, str)}
        managed = sorted(set(fact_object) & _CODE_MANAGED_FIELDS)
        if managed:
            problems.append(f"arguments.fact_object 不得提交 Code 托管字段: {', '.join(managed)}")

    problems.extend(observed_signature_injection_problems(request.observed_context, fact_object))
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对 WorkCase 写入操作必须为 null 或省略")
    for index, reference in enumerate(request.authorization_reference):
        problems.extend(source_reference_problems(reference, f"authorization_reference[{index}]"))
    if problems or fact_ref is None or not isinstance(fingerprint, str):
        return None, problems

    governance_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return (
        _ParsedBase(
            workspace_root=workspace_root,
            governance_scope=governance_scope,
            fact_ref=fact_ref,
            expected_content_fingerprint=fingerprint,
            fact_object=fact_object,
            authorization_reference=request.authorization_reference,
            base=context.cwd,
        ),
        problems,
    )


def parse_update_workcase_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> WorkCaseWriteRequestParseResult:
    parsed, problems = _parse_base(request, context, allowed_argument_fields=_COMMON_ARGUMENT_FIELDS)
    if parsed is None:
        return WorkCaseWriteRequestParseResult(None, tuple(problems))
    return WorkCaseWriteRequestParseResult(UpdateWorkCaseRequest(*parsed.values()), ())


def parse_close_workcase_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> WorkCaseWriteRequestParseResult:
    parsed, problems = _parse_base(request, context, allowed_argument_fields=_COMMON_ARGUMENT_FIELDS)
    if not request.authorization_reference:
        problems.append("authorization_reference 对 close-workcase 必须至少包含一项 Human 决定来源")
    if parsed is None or problems:
        return WorkCaseWriteRequestParseResult(None, tuple(problems))
    return WorkCaseWriteRequestParseResult(CloseWorkCaseRequest(*parsed.values()), ())


def _route_target_fingerprints(
    value: object,
    problems: list[str],
) -> tuple[RouteTargetFingerprint, ...]:
    path = "arguments.route_target_fingerprints"
    if not isinstance(value, list):
        problems.append(f"{path} 必须是 array")
        return ()
    parsed: list[RouteTargetFingerprint] = []
    identities: set[tuple[str, str, str]] = set()
    for index, item in enumerate(value):
        member_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{member_path} 必须是 object")
            continue
        unknown = _unknown_string_fields(item, _ROUTE_TARGET_FINGERPRINT_FIELDS)
        if unknown:
            problems.append(f"{member_path} 包含未知字段: {', '.join(unknown)}")
        if any(not isinstance(key, str) for key in item):
            problems.append(f"{member_path} 的字段名必须是 string")
        missing = sorted(_ROUTE_TARGET_FINGERPRINT_FIELDS - set(item))
        if missing:
            problems.append(f"{member_path} 缺少字段: {', '.join(missing)}")
        target = _fact_reference(item.get("target"), f"{member_path}.target", problems)
        fingerprint = item.get("content_fingerprint")
        if not isinstance(fingerprint, str) or _FINGERPRINT.fullmatch(fingerprint) is None:
            problems.append(f"{member_path}.content_fingerprint 必须是 64 位小写十六进制 string")
        if target is None or not isinstance(fingerprint, str) or _FINGERPRINT.fullmatch(fingerprint) is None:
            continue
        identity = (target.governed_project_id, target.fact_type_key, target.object_id)
        if identity in identities:
            problems.append(f"{path} 不得包含重复 target")
            continue
        identities.add(identity)
        parsed.append(RouteTargetFingerprint(target, fingerprint))
    return tuple(parsed)


def parse_correct_closed_workcase_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> WorkCaseWriteRequestParseResult:
    parsed, problems = _parse_base(request, context, allowed_argument_fields=_CORRECT_ARGUMENT_FIELDS)

    if "route_target_fingerprints" not in request.arguments:
        problems.append("arguments.route_target_fingerprints 必填")
        route_targets: tuple[RouteTargetFingerprint, ...] = ()
    else:
        route_targets = _route_target_fingerprints(request.arguments["route_target_fingerprints"], problems)

    review_reference: dict[str, Any] | None = None
    if "independent_review_reference" not in request.arguments:
        problems.append("arguments.independent_review_reference 必填且值必须是 object 或 null")
    else:
        value = request.arguments["independent_review_reference"]
        if value is not None:
            reference_problems = source_reference_problems(value, "arguments.independent_review_reference")
            problems.extend(reference_problems)
            if not reference_problems and isinstance(value, dict):
                review_reference = dict(value)

    if parsed is not None:
        for index, target in enumerate(route_targets):
            if target.target.governed_project_id != parsed.fact_ref.governed_project_id:
                problems.append(
                    f"arguments.route_target_fingerprints[{index}].target.governed_project_id "
                    "必须与 source WorkCase 属于同一项目"
                )
    if parsed is None or problems:
        return WorkCaseWriteRequestParseResult(None, tuple(problems))
    return WorkCaseWriteRequestParseResult(
        CorrectClosedWorkCaseRequest(
            *parsed.values(),
            route_target_fingerprints=route_targets,
            independent_review_reference=review_reference,
        ),
        (),
    )


__all__ = [
    "CLOSE_OPTIONAL_INPUTS",
    "CLOSE_REQUIRED_INPUTS",
    "CORRECT_CLOSED_OPTIONAL_INPUTS",
    "CORRECT_CLOSED_REQUIRED_INPUTS",
    "UPDATE_OPTIONAL_INPUTS",
    "UPDATE_REQUIRED_INPUTS",
    "CloseWorkCaseRequest",
    "CorrectClosedWorkCaseRequest",
    "RouteTargetFingerprint",
    "UpdateWorkCaseRequest",
    "WorkCaseWriteRequest",
    "WorkCaseWriteRequestParseResult",
    "parse_close_workcase_request",
    "parse_correct_closed_workcase_request",
    "parse_update_workcase_request",
]
