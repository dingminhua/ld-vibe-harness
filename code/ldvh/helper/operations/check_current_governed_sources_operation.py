"""Aggregate the current-rule and full-fact checks for the explicit ``ldvh check`` entry."""

from __future__ import annotations

import json
from typing import Any, Literal

from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_integrity_operation import execute_fact_integrity
from ldvh.helper.operations.fact_integrity_request import FactIntegrityRequest
from ldvh.helper.operations.specification_candidates import read_specification_candidates
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "check-current-governed-sources"
REQUIRED_INPUTS: tuple[str, ...] = ()
OPTIONAL_INPUTS: tuple[str, ...] = ()
_INPUT_CONTRACT = source_reference("rule", "helper-cli-service-contract::9.3 高频显式检查输入字段")
_RESULT_CONTRACT = source_reference("rule", "helper-cli-service-contract::9.4 高频显式检查结果字段")
_IMPLEMENTATION_EVIDENCE = (
    source_reference("implementation", "code/ldvh/helper/operations/check_current_governed_sources_operation.py"),
    source_reference("implementation", "code/ldvh/helper/operations/fact_integrity_operation.py"),
    source_reference("implementation", "code/ldvh/helper/operations/specification_candidates.py"),
)


def _validated_request(request: CommonRequest) -> None:
    problems: list[str] = []
    if request.task is not None:
        problems.append("高频显式检查不接受 task")
    if request.work_object_locators:
        problems.append("高频显式检查不接受 work_object_locators；事实范围固定为实际 cwd")
    if request.arguments:
        problems.append("高频显式检查不接受 arguments")
    if request.requested_disclosure is not None:
        problems.append("高频显式检查不接受 requested_disclosure")
    if request.observed_context:
        problems.append("高频显式检查不接受 observed_context")
    if request.authorization_reference:
        problems.append("高频显式检查不接受 authorization_reference")
    if problems:
        raise OperationRequestError(tuple(problems), sources=(_INPUT_CONTRACT,))


def _scope_identity(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _report(
    *,
    outcome: str,
    result: dict[str, Any] | None,
    requested: tuple[object, ...],
    completed: tuple[object, ...],
    not_completed: tuple[object, ...],
    sources: tuple[dict[str, Any], ...],
    gaps: tuple[dict[str, Any], ...],
    verification: tuple[dict[str, Any], ...],
    diagnostics: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    return {
        "outcome": outcome,
        "result": result,
        "scope": {
            "requested": list(requested),
            "completed": list(completed),
            "not_completed": list(not_completed),
        },
        "sources": list(sources),
        "gaps": list(gaps),
        "verification": list(verification),
        "diagnostics": list(diagnostics),
    }


def _has_blocking_gap(report: dict[str, Any]) -> bool:
    not_completed = {_scope_identity(item) for item in report["scope"]["not_completed"]}
    return any(any(_scope_identity(scope) in not_completed for scope in gap["scope"]) for gap in report["gaps"])


def _overall_outcome(
    rules: dict[str, Any],
    facts: dict[str, Any],
    *,
    passed: bool,
) -> Literal["ok", "partial", "unavailable", "error"]:
    if passed:
        return "ok"
    outcomes = {rules["outcome"], facts["outcome"]}
    if "error" in outcomes:
        return "error"
    if "ok" in outcomes or "partial" in outcomes:
        return "partial"
    return "unavailable"


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    _validated_request(request)
    rule_scope = {
        "check_scope": "current_rule_source",
        "rule_source_view": "working_tree",
        "git_worktree_root": str(repository.repository_root),
    }
    fact_scope = {
        "check_scope": "complete_governed_fact_library",
        "locator": str(context.cwd),
        "source": "actual_cwd",
    }

    rule_result = read_specification_candidates(
        repository,
        responsibility_keys=(),
        disclosure="L0",
        response_profile=request.response_profile,  # type: ignore[arg-type]
    )
    rules = _report(
        outcome=rule_result.suggested_outcome,
        result=None if rule_result.items is None else {"items": list(rule_result.items)},
        requested=rule_result.requested_scope,
        completed=rule_result.completed_scope,
        not_completed=rule_result.not_completed_scope,
        sources=rule_result.sources,
        gaps=rule_result.gaps,
        verification=rule_result.verification,
        diagnostics=rule_result.diagnostics,
    )

    fact_execution = execute_fact_integrity(
        FactIntegrityRequest(locator=str(context.cwd), base=context.cwd, workspace_root=None),
        repository,
        scope=(fact_scope,),
    )
    facts = _report(
        outcome=fact_execution.outcome,
        result=fact_execution.result,
        requested=fact_execution.requested_scope,
        completed=fact_execution.completed_scope,
        not_completed=fact_execution.not_completed_scope,
        sources=fact_execution.sources,
        gaps=fact_execution.gaps,
        verification=fact_execution.verification,
        diagnostics=fact_execution.diagnostics,
    )

    facts_complete = (
        facts["outcome"] == "ok" and facts["result"] is not None and facts["result"].get("status") == "complete"
    )
    rules_complete = rules["outcome"] == "ok" and not rules["scope"]["not_completed"]
    blocking = _has_blocking_gap(rules) or _has_blocking_gap(facts)
    passed = rules_complete and facts_complete and not facts["scope"]["not_completed"] and not blocking
    outcome = _overall_outcome(rules, facts, passed=passed)

    gaps = [*rules["gaps"], *facts["gaps"]]
    if facts["result"] is None or facts["result"].get("status") != "complete":
        gaps.append(
            {
                "summary": "事实完整性检查没有返回 complete，显式检查不能通过",
                "scope": [fact_scope],
                "source_refs": [_RESULT_CONTRACT],
            }
        )
    if blocking:
        gaps.append(
            {
                "summary": "子检查存在与未完成范围对应的阻断缺口，显式检查不能通过",
                "scope": [rule_scope, fact_scope],
                "source_refs": [_RESULT_CONTRACT],
            }
        )

    completed_scope: tuple[object, ...] = () if not passed else (rule_scope, fact_scope)
    not_completed_scope: tuple[object, ...] = () if passed else (rule_scope, fact_scope)
    sources = (*rule_result.sources, *fact_execution.sources, *_IMPLEMENTATION_EVIDENCE)
    return OperationExecution(
        outcome=outcome,
        summary=(
            "当前规则源与完整事实库的高频显式检查通过"
            if passed
            else "当前规则源或完整事实库的高频显式检查未通过；请读取原始子报告中的范围与缺口"
        ),
        result={"status": "passed" if passed else "not_passed", "rules": rules, "facts": facts},
        requested_scope=(rule_scope, fact_scope),
        completed_scope=completed_scope,
        not_completed_scope=not_completed_scope,
        sources=sources,
        gaps=tuple(gaps),
        verification=(
            {
                "check": "当前规则源候选全量机械读取",
                "status": "passed" if rules_complete else "not_passed",
                "scope": [rule_scope],
                "evidence": [*rule_result.sources, *_IMPLEMENTATION_EVIDENCE],
            },
            {
                "check": "当前受管辖 worktree 全量事实完整性检查",
                "status": "passed" if facts_complete else "not_passed",
                "scope": [fact_scope],
                "evidence": [*fact_execution.sources, *_IMPLEMENTATION_EVIDENCE],
            },
        ),
        diagnostics=tuple([*rule_result.diagnostics, *fact_execution.diagnostics]),
    )


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    execution = _execute(request, repository, context)
    if execution.outcome == "ok":
        return AvailabilityEvaluation("available_for_request", available_scope=execution.completed_scope)
    if execution.outcome == "partial":
        return AvailabilityEvaluation(
            "partially_available",
            available_scope=execution.completed_scope,
            unavailable_scope=execution.not_completed_scope,
            gaps=execution.gaps,
        )
    return AvailabilityEvaluation(
        "unavailable_for_request",
        unavailable_scope=execution.not_completed_scope,
        gaps=execution.gaps,
    )


CHECK_CURRENT_GOVERNED_SOURCES_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_check_availability,
    call=_execute,
)

__all__ = ["CHECK_CURRENT_GOVERNED_SOURCES_IMPLEMENTATION", "OPERATION_KEY"]
