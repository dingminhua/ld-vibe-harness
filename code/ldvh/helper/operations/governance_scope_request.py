"""Parse inputs for the source-defined governance-scope operation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS: tuple[str, ...] = ()
OPTIONAL_INPUTS: tuple[str, ...] = (
    "work_object_locators",
    "arguments.workspace_root",
)

_ARGUMENT_FIELDS = frozenset({"workspace_root"})


@dataclass(frozen=True, slots=True)
class GovernanceScopeRequest:
    """Validated domain inputs without performing filesystem resolution."""

    workspace_root: Path | None
    requested_scope: tuple[ScopeDescriptor, ...]
    base: Path


@dataclass(frozen=True, slots=True)
class GovernanceScopeRequestParseResult:
    request: GovernanceScopeRequest | None
    problems: tuple[str, ...]


def parse_governance_scope_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> GovernanceScopeRequestParseResult:
    """Validate operation inputs while preserving each explicit locator.

    Path identity, existence and Git observations belong to the resolver.  This
    boundary only establishes the original requested scope and its relative
    path base.
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

    unknown_arguments = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown_arguments:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown_arguments)}")

    workspace_root: Path | None = None
    if "workspace_root" in request.arguments:
        raw_workspace_root = request.arguments["workspace_root"]
        if not isinstance(raw_workspace_root, str) or not raw_workspace_root:
            problems.append("arguments.workspace_root 必须是非空绝对路径 string")
        else:
            candidate = Path(raw_workspace_root)
            if not candidate.is_absolute():
                problems.append("arguments.workspace_root 必须是非空绝对路径 string")
            else:
                workspace_root = candidate

    if request.observed_context:
        unknown_observations = ", ".join(sorted(request.observed_context))
        problems.append(f"observed_context 包含本操作未知字段: {unknown_observations}")

    if problems:
        return GovernanceScopeRequestParseResult(None, tuple(problems))

    requested_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return GovernanceScopeRequestParseResult(
        GovernanceScopeRequest(
            workspace_root=workspace_root,
            requested_scope=requested_scope,
            base=context.cwd,
        ),
        (),
    )


__all__ = [
    "GovernanceScopeRequest",
    "GovernanceScopeRequestParseResult",
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "parse_governance_scope_request",
]
