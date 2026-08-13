"""Bind the exact current WorkCase read to the source-defined handoff verdict.

This is a read-only Helper operation.  It derives the same
``current_snapshot_projection`` consumed by Helper reads, Web and AI handoff,
then exposes the closed-set ``handoff_allowed`` / ``handoff_reason`` verdict
and the structural ``next_required_control_step`` for a precisely bound
WorkCase.  It never writes a fact, advances a phase or selects a work item.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.models import FactReference
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.workcase_presentation import derive_workcase_presentation
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.check_workcase_handoff_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    CheckWorkCaseHandoffRequest,
    parse_check_workcase_handoff_request,
)
from ldvh.helper.operations.fact_operation_support import plain, reading_boundary
from ldvh.helper.operations.fact_reference_support import ResolvedFactReference, resolve_stable_fact_reference
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection
from ldvh.time import utc_now_iso

OPERATION_KEY = "check-workcase-handoff"
_CONTRACT = source_reference("rule", "workcase-fact-type::check-workcase-handoff 输入与结果")
_IMPLEMENTATION_EVIDENCE = (
    source_reference(
        "implementation",
        "code/ldvh/helper/operations/check_workcase_handoff_operation.py",
    ),
    source_reference("implementation", "code/ldvh/facts/workcase_presentation.py"),
)


def _validated_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> CheckWorkCaseHandoffRequest:
    parsed = parse_check_workcase_handoff_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACT,))
    return parsed.request


def _governance(domain: CheckWorkCaseHandoffRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _working_tree_source(root: Path, read: FactReadResult) -> dict[str, Any]:
    return {
        "kind": "working_tree",
        "locator": (root / read.canonical_path).as_posix(),
        "observed_at": utc_now_iso(),
        "details": {"view": "Working Tree", "check_status": read.check_status},
    }


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_request(request, context)
    run = _governance(domain)
    requested = (domain.fact_ref.to_json(),)
    governance_json = None if run.result is None else run.result.to_json()
    schemas = project_fact_schemas(repository)
    if isinstance(domain.fact_ref, FactReference):
        boundary = reading_boundary(run)
        resolution_status = (
            "unavailable"
            if boundary is None
            else "governance_mismatch"
            if boundary[0] != domain.fact_ref.governed_project_id
            else "resolved"
        )
        resolved = (
            ResolvedFactReference(domain.fact_ref, CreationBoundary(*boundary))
            if boundary is not None and boundary[0] == domain.fact_ref.governed_project_id
            else None
        )
    else:
        resolved, resolution_status = resolve_stable_fact_reference(run, domain.fact_ref, schemas)
    if resolved is None:
        return OperationExecution(
            outcome="rejected" if resolution_status == "governance_mismatch" else "unavailable",
            summary="当前管辖结果不能形成唯一 WorkCase 读取边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + (_CONTRACT,) + _IMPLEMENTATION_EVIDENCE,
            gaps=(
                {
                    "summary": "无法在同一管辖项目与实际 Working Tree 中读取当前 WorkCase",
                    "scope": list(requested),
                    "source_refs": [plain(source) for source in run.sources],
                },
            ),
        )

    reference = resolved.reference
    if reference.fact_type_key != "workcase":
        raise OperationRequestError(("arguments.fact_ref 解析后的类型必须为 workcase",), sources=(_CONTRACT,))
    project_id = resolved.boundary.governed_project_id
    root = resolved.boundary.worktree_root
    common_dir = resolved.boundary.git_common_dir
    schema = schemas.get("workcase")
    if schema is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前规则源未能形成 WorkCase Schema，无法读取当前 WorkCase",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + (_CONTRACT,) + _IMPLEMENTATION_EVIDENCE,
            gaps=(
                {
                    "summary": "当前规则源缺少完整 WorkCase 派生 Schema",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )

    read = read_fact_object(
        root,
        LAYOUTS["workcase"],
        schema,
        reference.object_id,
        expected_common_dir=common_dir,
    )
    working_tree_source = _working_tree_source(root, read)
    sources = (
        *(plain(source) for source in run.sources),
        _CONTRACT,
        working_tree_source,
        *_IMPLEMENTATION_EVIDENCE,
    )
    if read.check_status == "unavailable":
        return OperationExecution(
            outcome="unavailable",
            summary="当前技术条件不足，无法读取当前 WorkCase",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=sources,
            gaps=(
                {
                    "summary": "WorkCase source 当前不可用，未形成交还判定",
                    "scope": list(requested),
                    "source_refs": [working_tree_source],
                },
            ),
        )

    if (
        read.check_status != "mechanically_valid"
        or read.fields is None
        or read.content_fingerprint is None
    ):
        return OperationExecution(
            outcome="rejected",
            summary="当前 WorkCase 快照未通过机械校验，未形成交还判定",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=sources,
            gaps=(
                {
                    "summary": "source 必须完整、mechanically valid 且带当前 content_fingerprint",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT, working_tree_source],
                },
            ),
        )

    projection = derive_workcase_presentation(
        read.fields.get("status"),
        read.fields.get("phase"),
        read.content_fingerprint,
    )
    result = {
        "actual_ref": domain.fact_ref.to_json(),
        "canonical_path": read.canonical_path,
        "carrier": read.carrier,
        "source_content_fingerprint": read.content_fingerprint,
        "current_snapshot_projection": projection,
        "handoff_allowed": projection["handoff_allowed"],
        "handoff_reason": projection["handoff_reason"],
        "next_required_control_step": projection.get("next_required_control_step"),
    }
    return OperationExecution(
        outcome="ok",
        summary="已从当前精确读取的 WorkCase 快照形成只读交还判定",
        result=result,
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=governance_json,
        sources=sources,
        verification=(
            {
                "check": "交还判定绑定刚读取 source 指纹并按 21 的唯一派生语义形成；未写事实、未推进 phase、未选择 item",
                "status": "passed",
                "scope": list(requested),
                "evidence": [_CONTRACT, working_tree_source],
            },
        ),
    )


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    execution = _execute(request, repository, context)
    available = execution.outcome == "ok"
    return AvailabilityEvaluation(
        availability="available_for_request" if available else "unavailable_for_request",
        available_scope=execution.completed_scope,
        unavailable_scope=execution.not_completed_scope,
        gaps=execution.gaps,
    )


def _call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute(request, repository, context)


CHECK_WORKCASE_HANDOFF_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(*_IMPLEMENTATION_EVIDENCE, _CONTRACT),
    check_availability=_check_availability,
    call=_call,
)

__all__ = ["CHECK_WORKCASE_HANDOFF_IMPLEMENTATION", "OPERATION_KEY"]
