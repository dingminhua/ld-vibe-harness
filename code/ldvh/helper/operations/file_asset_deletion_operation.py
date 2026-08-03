"""Safely delete one active FileAsset payload while retaining its tombstone."""

from __future__ import annotations

from typing import Any

from ldvh.facts.creation import CreationBoundary, FactCoordinationUnavailable
from ldvh.facts.file_asset_deletion import FileAssetDeletionCommand, delete_file_asset
from ldvh.facts.schema import project_fact_schemas
from ldvh.filesystem import durable_writes_enabled
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_operation_support import plain, post_write_integrity_audit, reading_boundary
from ldvh.helper.operations.file_asset_deletion_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    FileAssetDeletionRequest,
    parse_file_asset_deletion_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "delete-file-asset"
_CONTRACT = source_reference("rule", "file-asset-fact-type::7.3 FileAsset 受控安全删除输入与结果")
_TYPE_CONTRACT = source_reference("rule", "specs/25-FileAsset-文件资产.md")
_INTEGRITY_CONTRACT = source_reference("rule", "fact-model-foundation::11.9-11.10 事实写后独立完整性审计")
_IMPLEMENTATION_EVIDENCE = (
    source_reference("implementation", "code/ldvh/helper/operations/file_asset_deletion_operation.py"),
    source_reference("implementation", "code/ldvh/facts/file_asset_deletion.py"),
    source_reference(
        "implementation",
        "code/ldvh/filesystem.py::atomic_replace_directory_relative_if_members_equal",
    ),
)


def _validated(request: CommonRequest, context: OperationExecutionContext) -> FileAssetDeletionRequest:
    parsed = parse_file_asset_deletion_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACT,))
    return parsed.request


def _governance(domain: FileAssetDeletionRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _scope(domain: FileAssetDeletionRequest) -> tuple[dict[str, object], ...]:
    return (domain.fact_ref.to_json(),)


def _sources(run: GovernanceResolutionRun) -> tuple[dict[str, Any], ...]:
    return tuple(plain(source) for source in run.sources) + (
        _CONTRACT,
        _TYPE_CONTRACT,
        *_IMPLEMENTATION_EVIDENCE,
    )


def _context(
    domain: FileAssetDeletionRequest,
    repository: RepositoryInspection,
    run: GovernanceResolutionRun,
) -> tuple[CreationBoundary | None, dict[str, Any], str | None]:
    observed = reading_boundary(run)
    schemas = project_fact_schemas(repository)
    if observed is None:
        return None, schemas, "当前管辖结果不能形成唯一 FileAsset 删除边界"
    boundary = CreationBoundary(*observed)
    if boundary.governed_project_id != domain.fact_ref.governed_project_id:
        return boundary, schemas, "请求项目与实际管辖项目不一致"
    if "file-asset" not in schemas or "workcase" not in schemas:
        return boundary, schemas, "FileAsset 或 WorkCase 当前派生 Schema 不可用"
    if not durable_writes_enabled():
        return boundary, schemas, "当前平台未开放安全删除所需的耐久目录写入"
    return boundary, schemas, None


def _availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain = _validated(request, context)
    requested = _scope(domain)
    run = _governance(domain)
    boundary, _, problem = _context(domain, repository, run)
    if problem is not None or boundary is None:
        return AvailabilityEvaluation(
            "unavailable_for_request",
            unavailable_scope=requested,
            gaps=({"summary": problem or "安全删除边界不可用", "scope": list(requested)},),
        )
    return AvailabilityEvaluation("available_for_request", available_scope=requested)


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated(request, context)
    requested = _scope(domain)
    run = _governance(domain)
    boundary, schemas, problem = _context(domain, repository, run)
    sources = _sources(run)
    governance = None if run.result is None else run.result.to_json()
    if problem is not None or boundary is None:
        return OperationExecution(
            outcome="unavailable",
            summary="FileAsset 安全删除未执行",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=({"summary": problem or "安全删除边界不可用", "scope": list(requested)},),
        )
    try:
        deletion = delete_file_asset(
            FileAssetDeletionCommand(
                boundary,
                schemas,
                domain.fact_ref.object_id,
                domain.expected_content_fingerprint,
                domain.deletion_summary,
                domain.change_log_entry,
            ),
            observed_at=context.event_at,
        )
    except FactCoordinationUnavailable as error:
        return OperationExecution(
            outcome="unavailable",
            summary="FileAsset 关系或类型协调锁不可用，未执行安全删除",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": f"恢复 git common-dir 协调根访问后重试（{error.system_error_category}）",
                    "scope": list(requested),
                },
            ),
        )

    result: dict[str, Any] = {
        "actual_ref": domain.fact_ref.to_json(),
        "canonical_path": deletion.current.canonical_path if deletion.current is not None else None,
        "carrier": "file-asset-directory",
        "previous_content_fingerprint": deletion.previous_content_fingerprint,
        "content_fingerprint": deletion.content_fingerprint,
        "fact_object": deletion.fields,
        "payload_removed": (
            deletion.replacement_result is not None
            and deletion.replacement_result.namespace_state == "committed"
        ),
        "incoming_reference_scan": {
            "complete": deletion.incoming_scan_complete,
            "incoming_refs": list(deletion.incoming_refs),
        },
        "recovery": None if deletion.recovery is None else deletion.recovery.to_json(),
        "transaction": {
            "status": deletion.status,
            "namespace_state": (
                None if deletion.replacement_result is None else deletion.replacement_result.namespace_state
            ),
            "durability": (
                None if deletion.replacement_result is None else deletion.replacement_result.durability
            ),
            "cleanup": None if deletion.replacement_result is None else deletion.replacement_result.cleanup,
        },
    }
    committed = (
        deletion.replacement_result is not None
        and deletion.replacement_result.namespace_state == "committed"
    )
    changes: tuple[dict[str, Any], ...] = ()
    if committed:
        changes = (
            {
                "summary": "FileAsset payload 已移除并形成 deleted tombstone",
                "status": "target-deleted",
                "target": deletion.current.canonical_path if deletion.current is not None else None,
                "source_refs": [_CONTRACT, _TYPE_CONTRACT],
            },
        )
    if deletion.status == "deleted":
        gaps: tuple[dict[str, Any], ...] = ()
        if deletion.coordination_release_uncertain:
            gaps = (
                {
                    "summary": "删除已形成并回读，但共同协调锁释放状态未知；再次事实写入前须核对",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            )
        return post_write_integrity_audit(
            OperationExecution(
            outcome="ok",
            summary="FileAsset 已安全删除 payload 并从实际 Working Tree 回读 tombstone",
            result=result,
            requested_scope=requested,
            completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=gaps,
            changes=changes,
            verification=(
                {
                    "check": "active CAS、入向引用零证明、HEAD blob 锚点、payload 移除与 tombstone 回读",
                    "status": "passed",
                    "scope": list(requested),
                    "evidence": list(sources),
                },
            ),
        ),
            boundary=boundary,
            schemas=schemas,
            audit_contract=_INTEGRITY_CONTRACT,
        )

    rejected = {
        "candidate_rejected",
        "conflict",
        "git_anchor_mismatch",
        "incoming_reference",
    }
    details = "; ".join(issue.summary for issue in deletion.issues) or deletion.status
    return OperationExecution(
        outcome="rejected" if deletion.status in rejected and not committed else "unavailable",
        summary="FileAsset 安全删除未完成" if not committed else "FileAsset 已变化但写后验证未完成",
        result=result,
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=governance,
        sources=sources,
        gaps=(
            {
                "summary": f"{deletion.status}: {details}",
                "scope": list(requested),
                "source_refs": list(sources),
            },
        ),
        changes=changes,
    )


DELETE_FILE_ASSET_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_availability,
    call=_execute,
)


__all__ = ["DELETE_FILE_ASSET_IMPLEMENTATION", "OPERATION_KEY"]
