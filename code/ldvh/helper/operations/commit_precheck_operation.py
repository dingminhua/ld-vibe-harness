"""Expose the shared Git commit precheck through the Helper contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ldvh.commits.precheck import CommitPrecheckResult, precheck_git_commit
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.commit_precheck_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    CommitPrecheckRequest,
    parse_commit_precheck_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import diagnostic, gap, source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "precheck-git-commit"
_INPUT_CONTRACT = source_reference(
    "rule",
    "source-of-truth-traceability::9.7 Git commit 候选机械预检输入字段",
)
_RESULT_CONTRACT = source_reference(
    "rule",
    "source-of-truth-traceability::9.8 Git commit 候选机械预检结果字段",
)
_IMPLEMENTATION_EVIDENCE = (
    source_reference(
        "implementation",
        "code/ldvh/helper/operations/commit_precheck_operation.py",
    ),
    source_reference(
        "implementation",
        "code/ldvh/commits/precheck.py",
    ),
)
_COMMIT_MESSAGE_INPUT_EXAMPLE = {
    "summary": "Git commit message 的三字段 LDVH trailer 待填写骨架",
    "arguments_fragment": {
        "message": (
            "feat: <fill-subject>\n\n"
            "LDVH-Product-Name: <fill-directly-observed-product-name>\n"
            "LDVH-Model-Name: <fill-directly-observed-model-name>\n"
            "LDVH-Agent-Runtime-Name: <fill-directly-observed-agent-runtime-name>"
        )
    },
    "source_refs": (_INPUT_CONTRACT,),
    "composition_note": (
        "按同一次提交前直接观察逐项替换尖括号占位；不可观察的单项 trailer 应省略并先向 Human 披露，"
        "三项均不可观察时必须停止。该片段只示例连续 trailer 排列，不证明 message、授权或提交内容有效。"
    ),
}


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _validated_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> CommitPrecheckRequest:
    parsed = parse_commit_precheck_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_INPUT_CONTRACT,))
    return parsed.request


def _precheck(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> tuple[CommitPrecheckRequest, CommitPrecheckResult]:
    domain_request = _validated_request(request, context)
    result = precheck_git_commit(
        repository=repository,
        locator=domain_request.locator,
        base=domain_request.base,
        workspace_root=domain_request.workspace_root,
        message=domain_request.message,
    )
    return domain_request, result


def _scope(domain_request: CommitPrecheckRequest) -> dict[str, object]:
    return {
        "locator_index": 0,
        "locator": domain_request.locator,
        "source": "explicit_locator",
    }


def _governance_json(result: CommitPrecheckResult) -> dict[str, Any] | None:
    if result.governance_run is None or result.governance_run.result is None:
        return None
    return result.governance_run.result.to_json()


def _sources(result: CommitPrecheckResult) -> tuple[dict[str, Any], ...]:
    observed: list[dict[str, Any]] = [_INPUT_CONTRACT, _RESULT_CONTRACT]
    if result.contract is not None:
        observed.append(
            source_reference(
                "rule",
                result.contract.source_path,
                source_key=result.contract.source_key,
                content_fingerprint=result.contract.content_fingerprint,
            )
        )
    if result.governance_run is not None:
        observed.extend(_plain(item) for item in result.governance_run.sources)
    observed.extend(_IMPLEMENTATION_EVIDENCE)
    return tuple(observed)


def _result_json(result: CommitPrecheckResult) -> dict[str, Any]:
    if result.contract is None or result.observation is None or result.validation is None:
        raise ValueError("completed commit precheck is missing a bound result")
    value = result.observation.validation_input
    if value is None:
        raise ValueError("completed commit precheck is missing validation input")
    validation = result.validation
    return {
        "mechanical_outcome": validation.outcome,
        "candidate": {
            "git_worktree_root": value.git_worktree_root,
            "paths": list(value.candidate_paths or ()),
            "snapshot_identity": value.snapshot_identity,
        },
        "message": {
            "normalized_message": validation.normalized_message,
            "header": validation.header,
            "body": validation.body,
        },
        "contract": {
            "source_key": result.contract.source_key,
            "source_path": result.contract.source_path,
            "source_fingerprint": result.contract.content_fingerprint,
            "observed_at": result.contract.observed_at,
        },
        "issues": [
            {"code": issue.code, "message": issue.message} for issue in result.issues if issue.stage == "validation"
        ],
        "semantic_checks_required": list(validation.semantic_checks_required),
    }


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain_request, result = _precheck(request, repository, context)
    scope = (_scope(domain_request),)
    if result.completed:
        return AvailabilityEvaluation(
            availability="available_for_request",
            available_scope=scope,
        )
    sources = list(_sources(result))
    return AvailabilityEvaluation(
        availability="unavailable_for_request",
        unavailable_scope=scope,
        gaps=tuple(gap(issue.message, scope=list(scope), sources=sources) for issue in result.issues),
    )


def _call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain_request, result = _precheck(request, repository, context)
    scope = (_scope(domain_request),)
    sources = _sources(result)
    if not result.completed:
        return OperationExecution(
            outcome="unavailable",
            summary="当前来源、管辖或 Git 候选不足以形成可信提交机械预检",
            requested_scope=scope,
            not_completed_scope=scope,
            governance_resolution=_governance_json(result),
            sources=sources,
            gaps=tuple(gap(issue.message, scope=list(scope), sources=list(sources)) for issue in result.issues),
            diagnostics=tuple(
                diagnostic(
                    "提交机械预检未完成",
                    stage=issue.stage,
                    code=issue.code,
                    detail=issue.message,
                )
                for issue in result.issues
            ),
        )

    result_json = _result_json(result)
    mechanical_outcome = result_json["mechanical_outcome"]
    return OperationExecution(
        outcome="ok",
        summary=f"已完成当前 Git commit 候选机械预检：{mechanical_outcome}",
        result=result_json,
        requested_scope=scope,
        completed_scope=scope,
        governance_resolution=_governance_json(result),
        sources=sources,
        verification=(
            {
                "check": "03 提交契约机械预检",
                "status": mechanical_outcome,
                "scope": list(scope),
                "evidence": list(sources),
            },
        ),
    )


COMMIT_PRECHECK_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_check_availability,
    call=_call,
    input_examples=(_COMMIT_MESSAGE_INPUT_EXAMPLE,),
    response_fields=("mechanical_outcome", "candidate", "message", "contract"),
)

__all__ = ["COMMIT_PRECHECK_IMPLEMENTATION", "OPERATION_KEY"]
