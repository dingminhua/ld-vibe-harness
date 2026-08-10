"""Expose controlled correction of invalid committed change-log workbench names."""

from __future__ import annotations

from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, FactCoordinationUnavailable, allocation_lock
from ldvh.facts.historical_signature_repair import (
    HistoricalSignatureRepairCommand,
    apply_historical_signature_repair_locked,
)
from ldvh.facts.schema import project_fact_schemas
from ldvh.filesystem import native_atomic_fact_writes_supported
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_operation_support import plain, post_write_integrity_audit, reading_boundary
from ldvh.helper.operations.historical_signature_repair_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    HistoricalSignatureRepairRequest,
    parse_historical_signature_repair_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "repair-historical-change-log-signatures"
_CONTRACT = source_reference("rule", "fact-model-foundation::11.7.3 历史 change_log 签名受控更正输入与结果")
_SHARED_WRITE_CONTRACT = source_reference("rule", "fact-model-foundation::11.8 共享单对象受控写事务")
_INTEGRITY_CONTRACT = source_reference("rule", "fact-model-foundation::11.9-11.10 事实写后独立完整性审计")
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation", "code/ldvh/helper/operations/historical_signature_repair_operation.py"
)


def _validated(request: CommonRequest, context: OperationExecutionContext) -> HistoricalSignatureRepairRequest:
    domain, problems = parse_historical_signature_repair_request(request, context)
    if domain is None:
        raise OperationRequestError(problems, sources=(_CONTRACT,))
    return domain


def _governance(domain: HistoricalSignatureRepairRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope, base=domain.base, explicit_workspace_root=domain.workspace_root
    )


def _boundary(run: GovernanceResolutionRun) -> CreationBoundary | None:
    resolved = reading_boundary(run)
    return CreationBoundary(*resolved) if resolved is not None else None


def _ref(domain: HistoricalSignatureRepairRequest) -> dict[str, str]:
    return domain.fact_ref.to_json()


def _fact_object(readback: Any) -> dict[str, Any]:
    assert readback.fields is not None
    if readback.carrier == "markdown":
        return {"frontmatter": readback.fields, "body": readback.body or ""}
    return readback.fields


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated(request, context)
    requested = (_ref(domain),)
    run = _governance(domain)
    boundary = _boundary(run)
    sources = (
        *tuple(plain(source) for source in run.sources),
        *tuple(plain(source) for source in domain.authorization_reference),
        _CONTRACT,
    )
    if boundary is None or boundary.governed_project_id != domain.fact_ref.governed_project_id:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成唯一历史签名修复边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
        )
    schemas = project_fact_schemas(repository)
    schema = schemas.get(domain.fact_ref.fact_type_key)
    if schema is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前来源未形成目标类型 Schema",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
        )
    if not native_atomic_fact_writes_supported():
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台没有启用受控原子写后端",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*sources, _SHARED_WRITE_CONTRACT),
        )
    command = HistoricalSignatureRepairCommand(
        boundary=boundary,
        fact_type_key=domain.fact_ref.fact_type_key,
        object_id=domain.fact_ref.object_id,
        schema=schema,
        expected_content_fingerprint=domain.expected_content_fingerprint,
        repairs=domain.repairs,
        correction_signature=domain.observed_signature,
        session_id=domain.session_id,
        event_at=context.event_at,
    )
    try:
        with allocation_lock(boundary, LAYOUTS[domain.fact_ref.fact_type_key]):
            result = apply_historical_signature_repair_locked(command)
    except (FactCoordinationUnavailable, OSError) as error:
        return OperationExecution(
            outcome="unavailable",
            summary="历史签名修复未能取得受控写入条件",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*sources, _SHARED_WRITE_CONTRACT),
            diagnostics=({"summary": "受控写入不可用", "exception_type": type(error).__name__},),
        )
    if result.status != "updated":
        outcome = "unavailable" if result.status in {"current_unavailable", "replacement_unavailable"} else "rejected"
        if result.status == "readback_failed":
            outcome = "error"
        return OperationExecution(
            outcome=outcome,
            summary=f"历史 change_log 签名修复未完成：{result.status}",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
            gaps=({
                "summary": "；".join(issue.summary for issue in result.issues) or "目标未通过历史签名修复条件",
                "scope": list(requested),
                "source_refs": [_CONTRACT],
            },),
        )
    assert result.readback is not None and result.readback.content_fingerprint is not None
    working_tree_source = {
        "kind": "working_tree",
        "locator": (boundary.worktree_root / result.readback.canonical_path).as_posix(),
        "observed_at": context.event_at,
        "details": {"view": "Working Tree", "content_fingerprint": result.readback.content_fingerprint},
    }
    execution = OperationExecution(
        outcome="ok",
        summary=f"已原子修复 {result.repaired_count} 条历史 change_log 签名并追加修复流水",
        result={
            "actual_ref": _ref(domain),
            "canonical_path": result.readback.canonical_path,
            "carrier": result.readback.carrier,
            "previous_content_fingerprint": domain.expected_content_fingerprint,
            "content_fingerprint": result.readback.content_fingerprint,
            "repaired_entry_count": result.repaired_count,
            "fact_object": _fact_object(result.readback),
        },
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=(*sources, working_tree_source, _IMPLEMENTATION_SOURCE),
        changes=({
            "summary": f"已修复 {result.repaired_count} 条历史 agent_workbench；原始值与修复依据写入新增流水",
            "status": "updated",
            "target": _ref(domain),
            "source_refs": [working_tree_source, _CONTRACT],
        },),
        verification=({
            "check": "单对象 CAS、原子替换、写后精确回读",
            "status": "passed",
            "scope": list(requested),
            "evidence": [working_tree_source, _CONTRACT],
        },),
    )
    return post_write_integrity_audit(
        execution,
        boundary=boundary,
        schemas=schemas,
        audit_contract=_INTEGRITY_CONTRACT,
        allow_partial_repair=True,
    )


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain = _validated(request, context)
    run = _governance(domain)
    boundary = _boundary(run)
    requested = (_ref(domain),)
    if boundary is None or domain.fact_ref.fact_type_key not in project_fact_schemas(repository):
        return AvailabilityEvaluation("unavailable_for_request", unavailable_scope=requested)
    return AvailabilityEvaluation("available_for_request", available_scope=requested)


HISTORICAL_SIGNATURE_REPAIR_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACT),
    check_availability=_check_availability,
    call=_execute,
)


__all__ = ["HISTORICAL_SIGNATURE_REPAIR_IMPLEMENTATION", "OPERATION_KEY"]
