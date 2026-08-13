"""Parse inputs for the source-defined update-fact-object operation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import WRITABLE_FACT_TYPE_KEYS
from ldvh.facts.models import FactReference, StableFactReference
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.fact_creation_request import observed_signature_injection_problems
from ldvh.helper.operations.fact_reference_support import parse_stable_fact_reference
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
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class FactUpdateRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: StableFactReference
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

    fact_ref, reference_problems = parse_stable_fact_reference(request.arguments.get("fact_ref"), "arguments.fact_ref")
    problems.extend(reference_problems)
    if isinstance(fact_ref, FactReference) and fact_ref.fact_type_key not in WRITABLE_FACT_TYPE_KEYS:
        problems.append("arguments.fact_ref.fact_type_key 未匹配当前支持通用更新的五类事实类型")

    fingerprint = request.arguments.get("expected_content_fingerprint")
    if not isinstance(fingerprint, str) or _FINGERPRINT.fullmatch(fingerprint) is None:
        problems.append("arguments.expected_content_fingerprint 必须是 64 位小写十六进制 string")

    fact_object = request.arguments.get("fact_object")
    if not isinstance(fact_object, dict):
        problems.append("arguments.fact_object 必须是 object")
        fact_object = {}
    if isinstance(fact_object, dict):
        if not isinstance(fact_ref, FactReference) or fact_ref.fact_type_key != "workcase":
            problems.extend(observed_signature_injection_problems(request.observed_context, fact_object))
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
