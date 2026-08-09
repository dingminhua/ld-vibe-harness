"""Parse requests for uncommitted change-log signature normalization."""

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
    "arguments.expected_head_content_fingerprint",
    "authorization_reference",
)
OPTIONAL_INPUTS = ("work_object_locators", "arguments.workspace_root")
_ARGUMENT_FIELDS = frozenset(
    {"workspace_root", "fact_ref", "expected_content_fingerprint", "expected_head_content_fingerprint"}
)
_FACT_REF_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class UncommittedSignatureNormalizationRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: FactReference
    expected_content_fingerprint: str
    expected_head_content_fingerprint: str
    authorization_reference: tuple[dict[str, Any], ...]
    base: Path


def parse_uncommitted_signature_normalization_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> tuple[UncommittedSignatureNormalizationRequest | None, tuple[str, ...]]:
    problems: list[str] = []
    unknown = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")

    workspace_root: Path | None = None
    raw_root = request.arguments.get("workspace_root")
    if raw_root is not None:
        if not isinstance(raw_root, str) or not raw_root or not Path(raw_root).is_absolute():
            problems.append("arguments.workspace_root 必须是非空绝对路径 string")
        else:
            workspace_root = Path(raw_root)

    values: dict[str, str] = {}
    raw_ref = request.arguments.get("fact_ref")
    if not isinstance(raw_ref, dict):
        problems.append("arguments.fact_ref 必须是 object")
    else:
        unknown_ref = sorted(set(raw_ref) - _FACT_REF_FIELDS)
        if unknown_ref:
            problems.append(f"arguments.fact_ref 包含未知字段: {', '.join(unknown_ref)}")
        for name in sorted(_FACT_REF_FIELDS):
            value = raw_ref.get(name)
            if not isinstance(value, str) or not value:
                problems.append(f"arguments.fact_ref.{name} 必须是非空 string")
            else:
                values[name] = value

    fact_ref: FactReference | None = None
    if len(values) == len(_FACT_REF_FIELDS):
        layout = LAYOUTS.get(values["fact_type_key"])
        if layout is None or values["fact_type_key"] not in WRITABLE_FACT_TYPE_KEYS:
            problems.append("arguments.fact_ref.fact_type_key 不是当前可写事实类型")
        elif layout.object_id_pattern.fullmatch(values["object_id"]) is None:
            problems.append("arguments.fact_ref.object_id 与事实类型格式不一致")
        else:
            fact_ref = FactReference(values["governed_project_id"], values["fact_type_key"], values["object_id"])

    current_fingerprint = request.arguments.get("expected_content_fingerprint")
    head_fingerprint = request.arguments.get("expected_head_content_fingerprint")
    if not isinstance(current_fingerprint, str) or _FINGERPRINT.fullmatch(current_fingerprint) is None:
        problems.append("arguments.expected_content_fingerprint 必须是 64 位小写十六进制 string")
    if not isinstance(head_fingerprint, str) or _FINGERPRINT.fullmatch(head_fingerprint) is None:
        problems.append("arguments.expected_head_content_fingerprint 必须是 64 位小写十六进制 string")
    if not request.authorization_reference:
        problems.append("authorization_reference 必须至少包含一个 Human 授权来源")
    if request.observed_context:
        problems.append("observed_context 对未提交流水签名归一必须为空 object")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 必须为 null 或省略")
    if problems:
        return None, tuple(problems)

    assert fact_ref is not None
    assert isinstance(current_fingerprint, str)
    assert isinstance(head_fingerprint, str)
    locators = tuple(locator for locator in request.work_object_locators if isinstance(locator, str) and locator)
    governance_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return (
        UncommittedSignatureNormalizationRequest(
            workspace_root,
            governance_scope,
            fact_ref,
            current_fingerprint,
            head_fingerprint,
            request.authorization_reference,
            context.cwd,
        ),
        (),
    )


__all__ = [
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "UncommittedSignatureNormalizationRequest",
    "parse_uncommitted_signature_normalization_request",
]
