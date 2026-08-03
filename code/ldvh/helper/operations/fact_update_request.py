"""Parse inputs for the source-defined update-fact-object operation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS, WRITABLE_FACT_TYPE_KEYS
from ldvh.facts.models import FactReference
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS = (
    "arguments.fact_ref",
    "arguments.expected_content_fingerprint",
    "arguments.fact_object",
)
OPTIONAL_INPUTS = (
    "work_object_locators",
    "arguments.workspace_root",
    "authorization_reference",
)
_ARGUMENT_FIELDS = frozenset({"workspace_root", "fact_ref", "expected_content_fingerprint", "fact_object"})
_FACT_REF_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class FactUpdateRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: FactReference
    expected_content_fingerprint: str
    fact_object: dict[str, Any]
    authorization_reference: tuple[dict[str, Any], ...]
    base: Path


@dataclass(frozen=True, slots=True)
class FactUpdateRequestParseResult:
    request: FactUpdateRequest | None
    problems: tuple[str, ...]


def parse_fact_update_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> FactUpdateRequestParseResult:
    problems: list[str] = []
    if not context.cwd.is_absolute():
        problems.append("Helper 进程实际 cwd 必须是绝对路径")

    locators: list[str] = []
    for index, locator in enumerate(request.work_object_locators):
        if not isinstance(locator, str) or not locator:
            problems.append(f"work_object_locators[{index}] 必须是非空路径 string")
        else:
            locators.append(locator)

    unknown = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")

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
        unknown_ref = sorted(set(raw_ref) - _FACT_REF_FIELDS)
        if unknown_ref:
            problems.append(f"arguments.fact_ref 包含未知字段: {', '.join(unknown_ref)}")
        values: dict[str, str] = {}
        for name in sorted(_FACT_REF_FIELDS):
            value = raw_ref.get(name)
            if not isinstance(value, str) or not value:
                problems.append(f"arguments.fact_ref.{name} 必须是非空 string")
            else:
                values[name] = value
        if len(values) == len(_FACT_REF_FIELDS):
            layout = LAYOUTS.get(values["fact_type_key"])
            if layout is None or values["fact_type_key"] not in WRITABLE_FACT_TYPE_KEYS:
                problems.append("arguments.fact_ref.fact_type_key 未匹配当前支持通用更新的五类事实类型")
            elif layout.object_id_pattern.fullmatch(values["object_id"]) is None:
                problems.append("arguments.fact_ref.object_id 与事实类型格式不一致")
            else:
                fact_ref = FactReference(
                    values["governed_project_id"],
                    values["fact_type_key"],
                    values["object_id"],
                )

    fingerprint = request.arguments.get("expected_content_fingerprint")
    if not isinstance(fingerprint, str) or _FINGERPRINT.fullmatch(fingerprint) is None:
        problems.append("arguments.expected_content_fingerprint 必须是 64 位小写十六进制 string")

    fact_object = request.arguments.get("fact_object")
    if not isinstance(fact_object, dict):
        problems.append("arguments.fact_object 必须是 object")
        fact_object = {}
    if request.observed_context:
        problems.append("observed_context 对事实对象更新操作必须为空 object")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对事实对象更新操作必须为 null 或省略")
    if problems:
        return FactUpdateRequestParseResult(None, tuple(problems))

    assert fact_ref is not None and isinstance(fingerprint, str)
    governance_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return FactUpdateRequestParseResult(
        FactUpdateRequest(
            workspace_root,
            governance_scope,
            fact_ref,
            fingerprint,
            dict(fact_object),
            request.authorization_reference,
            context.cwd,
        ),
        (),
    )


__all__ = [
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "FactUpdateRequest",
    "FactUpdateRequestParseResult",
    "parse_fact_update_request",
]
