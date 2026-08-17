"""Connect exact specification-content reading to the Helper runtime."""

from __future__ import annotations

from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.specification_content import (
    SpecificationContentReadResult,
    SpecificationContentSelectionError,
    read_specification_content,
)
from ldvh.helper.operations.specification_content_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    SpecificationContentRequest,
    parse_specification_content_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "read-specification-content"
_INPUT_CONTRACT = source_reference(
    "rule",
    "specification-model-foundation::9.6 规范内容读取输入字段",
)
_IMPLEMENTATION_EVIDENCE = (
    source_reference(
        "implementation",
        "code/ldvh/helper/operations/specification_content_operation.py",
    ),
)


def _validated_request(request: CommonRequest) -> SpecificationContentRequest:
    parsed = parse_specification_content_request(request)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_INPUT_CONTRACT,))
    return parsed.request


def _read(
    request: CommonRequest,
    repository: RepositoryInspection,
) -> SpecificationContentReadResult:
    domain_request = _validated_request(request)
    try:
        return read_specification_content(
            repository,
            request=domain_request,
            response_profile=request.response_profile,  # type: ignore[arg-type]
        )
    except SpecificationContentSelectionError as error:
        raise OperationRequestError(error.problems, sources=error.sources) from error


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    del context
    result = _read(request, repository)
    if result.completed_scope == result.requested_scope:
        availability = "available_for_request"
    elif result.completed_scope:
        availability = "partially_available"
    else:
        availability = "unavailable_for_request"
    return AvailabilityEvaluation(
        availability=availability,
        available_scope=result.completed_scope,
        unavailable_scope=result.not_completed_scope,
        gaps=result.gaps,
    )


def _summary(result: SpecificationContentReadResult) -> str:
    if result.suggested_outcome == "ok":
        return "已按契约读取全部精确选择的规范内容"
    if result.suggested_outcome == "partial":
        return "已读取部分精确选择的规范内容，并保留未完成范围"
    if result.suggested_outcome == "rejected":
        return "当前规则、授权或 Stop Conditions 拒绝读取全部请求范围"
    if result.suggested_outcome == "unavailable":
        return "当前实现、依赖、配置或环境无法读取任一请求范围"
    return "当前来源身份或范围无法按契约确定"


def _call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    del context
    result = _read(request, repository)
    verification = tuple(
        {
            **item,
            "evidence": [*item["evidence"], *_IMPLEMENTATION_EVIDENCE],
        }
        for item in result.verification
    )
    return OperationExecution(
        outcome=result.suggested_outcome,
        summary=_summary(result),
        result=None if result.items is None else {"items": list(result.items)},
        requested_scope=result.requested_scope,
        completed_scope=result.completed_scope,
        not_completed_scope=result.not_completed_scope,
        sources=(*result.sources, *_IMPLEMENTATION_EVIDENCE),
        disclosure={"requested": request.requested_disclosure, "parts": list(result.disclosure_parts)},
        gaps=result.gaps,
        verification=verification,
        diagnostics=result.diagnostics,
    )


SPECIFICATION_CONTENT_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_check_availability,
    call=_call,
    response_fields=("items",),
)

__all__ = ["OPERATION_KEY", "SPECIFICATION_CONTENT_IMPLEMENTATION"]
