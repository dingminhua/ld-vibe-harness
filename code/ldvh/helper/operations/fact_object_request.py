"""Parse inputs for the source-defined read-fact-objects operation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactReference, FactReferenceScope
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS = ("arguments.fact_refs",)
OPTIONAL_INPUTS = ("work_object_locators", "arguments.workspace_root")
_ARGUMENT_FIELDS = frozenset({"workspace_root", "fact_refs"})
_FACT_REF_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})


@dataclass(frozen=True, slots=True)
class FactObjectRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_scopes: tuple[FactReferenceScope, ...]
    base: Path


@dataclass(frozen=True, slots=True)
class FactObjectRequestParseResult:
    request: FactObjectRequest | None
    problems: tuple[str, ...]


def parse_fact_object_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> FactObjectRequestParseResult:
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

    raw_refs = request.arguments.get("fact_refs")
    fact_scopes: list[FactReferenceScope] = []
    if not isinstance(raw_refs, list) or not raw_refs or len(raw_refs) > 128:
        problems.append("arguments.fact_refs 必须是包含 1–128 项的 array")
    else:
        for index, raw_ref in enumerate(raw_refs):
            prefix = f"arguments.fact_refs[{index}]"
            if not isinstance(raw_ref, dict):
                problems.append(f"{prefix} 必须是 object")
                continue
            unknown_ref = sorted(set(raw_ref) - _FACT_REF_FIELDS)
            if unknown_ref:
                problems.append(f"{prefix} 包含未知字段: {', '.join(unknown_ref)}")
            values: dict[str, str] = {}
            for name in sorted(_FACT_REF_FIELDS):
                value = raw_ref.get(name)
                if not isinstance(value, str) or not value:
                    problems.append(f"{prefix}.{name} 必须是非空 string")
                else:
                    values[name] = value
            if len(values) != len(_FACT_REF_FIELDS):
                continue
            fact_type_key = values["fact_type_key"]
            layout = LAYOUTS.get(fact_type_key)
            if layout is None:
                problems.append(f"{prefix}.fact_type_key 未精确匹配当前五类可读事实类型")
                continue
            if layout.object_id_pattern.fullmatch(values["object_id"]) is None:
                problems.append(f"{prefix}.object_id 不符合 {fact_type_key} 当前格式")
                continue
            reference = FactReference(values["governed_project_id"], fact_type_key, values["object_id"])
            fact_scopes.append(FactReferenceScope(index, reference))

    if request.observed_context:
        problems.append("observed_context 对本操作必须为空 object")
    if request.authorization_reference:
        problems.append("authorization_reference 对本只读操作必须为空 array")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对本操作必须为 null 或省略")
    if problems:
        return FactObjectRequestParseResult(None, tuple(problems))
    governance_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return FactObjectRequestParseResult(
        FactObjectRequest(workspace_root, governance_scope, tuple(fact_scopes), context.cwd),
        (),
    )


__all__ = [
    "FactObjectRequest",
    "FactObjectRequestParseResult",
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "parse_fact_object_request",
]
