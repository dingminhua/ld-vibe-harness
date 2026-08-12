"""Expose the whole-library fact mechanical integrity check (specs 05 §11.9-11.10)."""

from __future__ import annotations

from typing import Any

from ldvh.facts.candidate_discovery import discover_fact_candidates
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.schema import project_fact_schemas
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_integrity_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    FactIntegrityRequest,
    parse_fact_integrity_request,
)
from ldvh.helper.operations.fact_operation_support import plain, reading_boundary
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection
from ldvh.testing.fact_integrity import assess_fact_snapshot

OPERATION_KEY = "check-fact-integrity"
_INPUT_CONTRACT = source_reference("rule", "fact-model-foundation::11.9 事实完整性机械检查输入字段")
_RESULT_CONTRACT = source_reference("rule", "fact-model-foundation::11.10 事实完整性机械检查结果字段")
_IMPLEMENTATION_EVIDENCE = (
    source_reference("implementation", "code/ldvh/helper/operations/fact_integrity_operation.py"),
    source_reference("implementation", "code/ldvh/testing/fact_integrity.py"),
    source_reference("implementation", "code/ldvh/facts/candidate_discovery.py"),
)


def _validated_request(request: CommonRequest, context: OperationExecutionContext) -> FactIntegrityRequest:
    parsed = parse_fact_integrity_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_INPUT_CONTRACT,))
    return parsed.request


def _scope(domain: FactIntegrityRequest) -> dict[str, object]:
    return {
        "locator_index": 0,
        "locator": domain.locator,
        "source": "explicit_locator",
    }


def _governance(domain: FactIntegrityRequest) -> GovernanceResolutionRun:
    requested_scope = (ScopeDescriptor(0, domain.locator, LocatorSource.EXPLICIT_LOCATOR),)
    return resolve_governance_scope(
        requested_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _unavailable(
    summary: str,
    scope: tuple[dict[str, object], ...],
    run: GovernanceResolutionRun,
    problems: tuple[dict[str, object], ...],
) -> OperationExecution:
    governance_json = None if run.result is None else run.result.to_json()
    sources = (
        (_INPUT_CONTRACT, _RESULT_CONTRACT) + tuple(plain(source) for source in run.sources) + _IMPLEMENTATION_EVIDENCE
    )
    return OperationExecution(
        outcome="unavailable",
        summary=summary,
        requested_scope=scope,
        not_completed_scope=scope,
        governance_resolution=governance_json,
        sources=sources,
        gaps=tuple(
            {
                "summary": problem.get("summary") or str(problem),
                "scope": list(scope),
                "source_refs": list(sources),
            }
            for problem in problems
        )
        or (
            {
                "summary": summary,
                "scope": list(scope),
                "source_refs": list(sources),
            },
        ),
    )


def _format_integrity_problem_summary(problem: dict[str, Any]) -> str:
    label = problem.get("canonical_path") or problem.get("fact_type_key") or "扫描边界"
    detail = (
        "; ".join(str(issue.get("summary")) for issue in problem.get("issues", ()) if isinstance(issue, dict))
        or problem.get("check_status")
        or "读取未完成"
    )
    return f"{label}: {detail}"


def execute_fact_integrity(
    domain: FactIntegrityRequest,
    repository: RepositoryInspection,
    *,
    scope: tuple[dict[str, object], ...] | None = None,
) -> OperationExecution:
    scope = (_scope(domain),) if scope is None else scope
    run = _governance(domain)
    boundary = reading_boundary(run)
    if boundary is None:
        return _unavailable(
            "当前管辖结果不能形成唯一事实完整性检查边界",
            scope,
            run,
            ({"summary": "管辖输入未形成同一项目、同一实际 worktree 和 common-dir 的唯一边界"},),
        )
    project_id, root, common_dir = boundary
    schemas = project_fact_schemas(repository)
    if set(schemas) != set(LAYOUTS):
        return _unavailable(
            "当前规则源不能形成五类型完整派生 Schema",
            scope,
            run,
            ({"summary": "五类型派生 Schema 不完整，不能形成可信全量检查"},),
        )

    snapshot = discover_fact_candidates(root, project_id, common_dir, schemas)
    status, problems = assess_fact_snapshot(snapshot)
    if status == "unavailable":
        return _unavailable(
            "事实对象发现或读取未完成，不能形成可信全量检查",
            scope,
            run,
            tuple(
                {
                    "summary": _format_integrity_problem_summary(problem),
                    **problem,
                }
                for problem in problems
            ),
        )

    governance_json = None if run.result is None else run.result.to_json()
    sources = (
        (_INPUT_CONTRACT, _RESULT_CONTRACT) + tuple(plain(source) for source in run.sources) + _IMPLEMENTATION_EVIDENCE
    )
    result_json: dict[str, Any] = {
        "status": status,
        "object_count": len(snapshot.keys),
        "problems": [dict(problem) for problem in problems],
    }
    return OperationExecution(
        outcome="ok",
        summary=f"已完成当前事实库全量机械完整性检查：{status}（{len(snapshot.keys)} 个对象）",
        result=result_json,
        requested_scope=scope,
        completed_scope=scope,
        governance_resolution=governance_json,
        sources=sources,
        verification=(
            {
                "check": "05 事实完整性机械检查",
                "status": status,
                "scope": list(scope),
                "evidence": list(sources),
            },
        ),
    )


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return execute_fact_integrity(_validated_request(request, context), repository)


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    execution = _execute(request, repository, context)
    if execution.outcome == "ok":
        return AvailabilityEvaluation(
            availability="available_for_request",
            available_scope=execution.completed_scope,
        )
    return AvailabilityEvaluation(
        availability="unavailable_for_request",
        unavailable_scope=execution.requested_scope,
        gaps=execution.gaps,
    )


FACT_INTEGRITY_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_check_availability,
    call=_execute,
)

__all__ = ["FACT_INTEGRITY_IMPLEMENTATION", "OPERATION_KEY", "execute_fact_integrity"]
