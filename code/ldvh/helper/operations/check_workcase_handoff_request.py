"""Parse the source-defined read-only workcase handoff check request."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.facts.models import StableFactReference
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.fact_reference_support import parse_stable_fact_reference
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS = ("arguments.fact_ref",)
OPTIONAL_INPUTS = ("work_object_locators", "arguments.workspace_root")
_ARGUMENT_FIELDS = frozenset({"workspace_root", "fact_ref"})


@dataclass(frozen=True, slots=True)
class CheckWorkCaseHandoffRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: StableFactReference
    base: Path


@dataclass(frozen=True, slots=True)
class CheckWorkCaseHandoffRequestParseResult:
    request: CheckWorkCaseHandoffRequest | None
    problems: tuple[str, ...]


def parse_check_workcase_handoff_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> CheckWorkCaseHandoffRequestParseResult:
    """Require one precise WorkCase fact_ref and reject any other domain input."""

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

    raw_reference = request.arguments.get("fact_ref")
    reference, reference_problems = parse_stable_fact_reference(raw_reference, "arguments.fact_ref")
    problems.extend(reference_problems)
    legacy_type = raw_reference.get("fact_type_key") if isinstance(raw_reference, dict) else None
    if legacy_type is not None and legacy_type != "workcase":
        problems.append("arguments.fact_ref.fact_type_key 必须精确为 workcase")
        reference = None

    if request.observed_context:
        problems.append("observed_context 对本只读操作必须为空 object")
    if request.authorization_reference:
        problems.append("authorization_reference 对本只读操作必须为空 array")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对本操作必须为 null 或省略")
    if problems or reference is None:
        return CheckWorkCaseHandoffRequestParseResult(None, tuple(problems))

    governance_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return CheckWorkCaseHandoffRequestParseResult(
        CheckWorkCaseHandoffRequest(workspace_root, governance_scope, reference, context.cwd),
        (),
    )


__all__ = [
    "CheckWorkCaseHandoffRequest",
    "CheckWorkCaseHandoffRequestParseResult",
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "parse_check_workcase_handoff_request",
]
