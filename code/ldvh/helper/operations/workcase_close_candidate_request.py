"""Parse the source-defined closed WorkCase candidate read request."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactReference
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS = ("arguments.fact_ref",)
OPTIONAL_INPUTS = ("work_object_locators", "arguments.workspace_root")
_ARGUMENT_FIELDS = frozenset({"workspace_root", "fact_ref"})
_FACT_REF_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})


@dataclass(frozen=True, slots=True)
class WorkCaseCloseCandidateRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: FactReference
    base: Path


@dataclass(frozen=True, slots=True)
class WorkCaseCloseCandidateRequestParseResult:
    request: WorkCaseCloseCandidateRequest | None
    problems: tuple[str, ...]


def parse_workcase_close_candidate_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> WorkCaseCloseCandidateRequestParseResult:
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

    reference: FactReference | None = None
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
            if values["fact_type_key"] != "workcase":
                problems.append("arguments.fact_ref.fact_type_key 必须精确为 workcase")
            elif LAYOUTS["workcase"].object_id_pattern.fullmatch(values["object_id"]) is None:
                problems.append("arguments.fact_ref.object_id 不符合 workcase 当前格式")
            else:
                reference = FactReference(
                    values["governed_project_id"],
                    values["fact_type_key"],
                    values["object_id"],
                )

    if request.observed_context:
        problems.append("observed_context 对本只读操作必须为空 object")
    if request.authorization_reference:
        problems.append("authorization_reference 对本只读操作必须为空 array")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对本操作必须为 null 或省略")
    if problems or reference is None:
        return WorkCaseCloseCandidateRequestParseResult(None, tuple(problems))

    governance_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return WorkCaseCloseCandidateRequestParseResult(
        WorkCaseCloseCandidateRequest(workspace_root, governance_scope, reference, context.cwd),
        (),
    )


__all__ = [
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "WorkCaseCloseCandidateRequest",
    "WorkCaseCloseCandidateRequestParseResult",
    "parse_workcase_close_candidate_request",
]
