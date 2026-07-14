"""Connect the source-defined specification-candidate operation to its Code implementation."""

from __future__ import annotations

from datetime import datetime
from typing import assert_never

from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.specification_candidate_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    SpecificationCandidateRequest,
    parse_specification_candidate_request,
)
from ldvh.helper.operations.specification_candidates import (
    SpecificationCandidateReadResult,
    read_specification_candidates,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "read-specification-candidates"
_INPUT_CONTRACT = source_reference(
    "rule",
    "specification-model-foundation::9.4 规范候选读取输入字段",
)
_IMPLEMENTATION_EVIDENCE = (
    source_reference(
        "implementation",
        "code/ldvh/helper/operations/specification_candidate_operation.py",
    ),
)


def _validated_request(request: CommonRequest) -> SpecificationCandidateRequest:
    parsed = parse_specification_candidate_request(request)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_INPUT_CONTRACT,))
    return parsed.request


def _read(
    request: CommonRequest,
    repository: RepositoryInspection,
) -> tuple[SpecificationCandidateRequest, SpecificationCandidateReadResult]:
    domain_request = _validated_request(request)
    result = read_specification_candidates(
        repository,
        responsibility_keys=domain_request.responsibility_keys,
        disclosure=domain_request.disclosure,
        response_profile=request.response_profile,  # type: ignore[arg-type]
    )
    return domain_request, result


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    del context
    _, result = _read(request, repository)
    if result.suggested_outcome == "ok":
        availability = "available_for_request"
    elif result.suggested_outcome == "partial":
        availability = "partially_available"
    elif result.suggested_outcome == "unavailable":
        availability = "unavailable_for_request"
    else:
        assert_never(result.suggested_outcome)
    return AvailabilityEvaluation(
        availability=availability,
        available_scope=result.completed_scope,
        unavailable_scope=result.not_completed_scope,
        gaps=result.gaps,
    )


def _summary(result: SpecificationCandidateReadResult) -> str:
    if result.suggested_outcome == "ok":
        return "已读取全部请求范围内的规范候选信息"
    if result.suggested_outcome == "partial":
        return "已读取部分请求范围内的规范候选信息，并保留未完成范围"
    if result.suggested_outcome == "unavailable":
        return "当前没有请求范围能够形成可信的规范候选读取结果"
    assert_never(result.suggested_outcome)


def _call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    del context
    _, result = _read(request, repository)
    working_tree_observation = {
        "kind": "working_tree",
        "locator": repository.repository_root.as_posix(),
        "observed_at": datetime.now().astimezone().isoformat(),
        "details": {"view": "Working Tree"},
    }
    verification = tuple(
        {
            **item,
            "evidence": [*item["evidence"], working_tree_observation, *_IMPLEMENTATION_EVIDENCE],
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
        sources=(*result.sources, working_tree_observation, *_IMPLEMENTATION_EVIDENCE),
        disclosure={
            "requested": request.requested_disclosure,
            "parts": list(result.disclosure_parts),
        },
        gaps=result.gaps,
        verification=verification,
        diagnostics=result.diagnostics,
    )


SPECIFICATION_CANDIDATE_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_check_availability,
    call=_call,
)

__all__ = ["OPERATION_KEY", "SPECIFICATION_CANDIDATE_IMPLEMENTATION"]
