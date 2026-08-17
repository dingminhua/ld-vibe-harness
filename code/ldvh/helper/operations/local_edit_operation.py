"""Bind read-only local edit candidates to the Helper runtime."""

from __future__ import annotations

from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.local_edit_candidates import read_local_edit_candidates
from ldvh.helper.operations.local_edit_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    LocalEditRequest,
    parse_local_edit_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "prepare-local-edit-candidates"
_INPUT_CONTRACT = source_reference("rule", "helper-cli-service-contract::12.1 局部编辑候选输入字段")
_IMPLEMENTATION_EVIDENCE = (source_reference("implementation", "code/ldvh/helper/operations/local_edit_operation.py"),)


def _validated_request(request: CommonRequest, context: OperationExecutionContext) -> LocalEditRequest:
    parsed = parse_local_edit_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_INPUT_CONTRACT,))
    return parsed.request


def _read(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
):
    return read_local_edit_candidates(repository, _validated_request(request, context))


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    result = _read(request, repository, context)
    if result.completed_scope == result.requested_scope:
        availability = "available_for_request"
    elif result.completed_scope:
        availability = "partially_available"
    else:
        availability = "unavailable_for_request"
    return AvailabilityEvaluation(availability, result.completed_scope, result.not_completed_scope, result.gaps)


def _summary(outcome: str) -> str:
    if outcome == "ok":
        return "已为精确局部目标形成只读候选、基线与范围证据"
    if outcome == "rejected":
        return "规则读取条件或精确目标选择拒绝形成局部编辑候选"
    if outcome == "unavailable":
        return "当前技术或读取边界无法形成局部编辑候选"
    return "当前局部编辑候选范围无法按契约可信确定"


def _call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    result = _read(request, repository, context)
    verification = tuple(
        {**entry, "evidence": [*entry["evidence"], *_IMPLEMENTATION_EVIDENCE]} for entry in result.verification
    )
    return OperationExecution(
        outcome=result.outcome,
        summary=_summary(result.outcome),
        result=None if result.items is None else {"items": list(result.items)},
        requested_scope=result.requested_scope,
        completed_scope=result.completed_scope,
        not_completed_scope=result.not_completed_scope,
        governance_resolution=result.governance_resolution,
        sources=(*result.sources, *_IMPLEMENTATION_EVIDENCE),
        gaps=result.gaps,
        verification=verification,
        diagnostics=result.diagnostics,
    )


LOCAL_EDIT_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_check_availability,
    call=_call,
    response_fields=(
    "items",
    ),
)

__all__ = ["LOCAL_EDIT_IMPLEMENTATION", "OPERATION_KEY"]
