"""Prepare FileAsset source intake and atomically create one directory carrier."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    CreationBoundary,
    FactCoordinationUnavailable,
    candidate_object_id,
    schema_fingerprint,
    worktree_fingerprint,
)
from ldvh.facts.file_asset import DEFAULT_PAYLOAD_BUDGET
from ldvh.facts.file_asset_creation import (
    FileAssetCreationCommand,
    create_file_asset,
    observe_file_asset_source,
)
from ldvh.facts.schema import project_fact_schemas
from ldvh.filesystem import ReadBudgetExceeded, UnsafePathError, durable_writes_enabled
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_operation_support import plain, post_write_integrity_audit, reading_boundary
from ldvh.helper.operations.file_asset_creation_request import (
    CREATE_OPTIONAL_INPUTS,
    CREATE_REQUIRED_INPUTS,
    PREPARE_OPTIONAL_INPUTS,
    PREPARE_REQUIRED_INPUTS,
    FileAssetCreateRequest,
    FileAssetIntakeRequest,
    parse_file_asset_create_request,
    parse_file_asset_intake_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

PREPARE_OPERATION_KEY = "prepare-file-asset-intake"
CREATE_OPERATION_KEY = "create-file-asset"
_PREPARE_CONTRACT = source_reference("rule", "file-asset-fact-type::7.1 FileAsset 摄取准备输入与结果")
_CREATE_CONTRACT = source_reference("rule", "file-asset-fact-type::7.2 FileAsset 受控创建输入与结果")
_TYPE_CONTRACT = source_reference("rule", "specs/25-FileAsset-文件资产.md")
_INTEGRITY_CONTRACT = source_reference("rule", "fact-model-foundation::11.9-11.10 事实写后独立完整性审计")
_IMPLEMENTATION_EVIDENCE = (
    source_reference("implementation", "code/ldvh/helper/operations/file_asset_creation_operation.py"),
    source_reference("implementation", "code/ldvh/facts/file_asset_creation.py"),
    source_reference("implementation", "code/ldvh/filesystem.py::atomic_create_directory_relative"),
)


def _governance(domain: FileAssetIntakeRequest | FileAssetCreateRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _boundary(run: GovernanceResolutionRun) -> CreationBoundary | None:
    observed = reading_boundary(run)
    return None if observed is None else CreationBoundary(*observed)


def _sources(run: GovernanceResolutionRun, contract: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(plain(source) for source in run.sources) + (
        contract,
        _TYPE_CONTRACT,
        *_IMPLEMENTATION_EVIDENCE,
    )


def _scope(project_id: str, source_path: str) -> tuple[dict[str, Any], ...]:
    return ({"governed_project_id": project_id, "source_path": source_path},)


def _unavailable(
    summary: str,
    requested: tuple[dict[str, Any], ...],
    run: GovernanceResolutionRun,
    contract: dict[str, Any],
    detail: str,
) -> OperationExecution:
    sources = _sources(run, contract)
    return OperationExecution(
        outcome="unavailable",
        summary=summary,
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=None if run.result is None else run.result.to_json(),
        sources=sources,
        gaps=({"summary": detail, "scope": list(requested), "source_refs": list(sources)},),
    )


def _validated_intake(request: CommonRequest, context: OperationExecutionContext) -> FileAssetIntakeRequest:
    parsed = parse_file_asset_intake_request(request, context)
    if not isinstance(parsed.request, FileAssetIntakeRequest):
        raise OperationRequestError(parsed.problems, sources=(_PREPARE_CONTRACT,))
    return parsed.request


def _validated_create(request: CommonRequest, context: OperationExecutionContext) -> FileAssetCreateRequest:
    parsed = parse_file_asset_create_request(request, context)
    if not isinstance(parsed.request, FileAssetCreateRequest):
        raise OperationRequestError(parsed.problems, sources=(_CREATE_CONTRACT,))
    return parsed.request


def _intake_execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_intake(request, context)
    requested = _scope(domain.governed_project_id, domain.source_path.as_posix())
    run = _governance(domain)
    boundary = _boundary(run)
    if boundary is None:
        return _unavailable(
            "当前管辖结果不能形成唯一 FileAsset 摄取准备边界",
            requested,
            run,
            _PREPARE_CONTRACT,
            "管辖输入未形成同一项目、同一实际 worktree 和 common-dir 的唯一边界",
        )
    if boundary.governed_project_id != domain.governed_project_id:
        return OperationExecution(
            outcome="rejected",
            summary="请求项目与实际管辖项目不一致",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=_sources(run, _PREPARE_CONTRACT),
        )
    schema = project_fact_schemas(repository).get("file-asset")
    candidate = candidate_object_id(boundary, LAYOUTS["file-asset"])
    if schema is None or candidate is None:
        return _unavailable(
            "当前来源、Git 身份或共享编号状态不能形成可信 FileAsset 摄取依据",
            requested,
            run,
            _PREPARE_CONTRACT,
            "FileAsset 派生 Schema、linked worktree 扫描或共享编号状态不可用",
        )
    try:
        observed = observe_file_asset_source(domain.source_path)
    except ReadBudgetExceeded:
        return _unavailable(
            "来源文件超过 FileAsset 摄取资源上限",
            requested,
            run,
            _PREPARE_CONTRACT,
            f"来源文件超过 {DEFAULT_PAYLOAD_BUDGET} bytes 摄取上限",
        )
    except (OSError, UnsafePathError):
        return _unavailable(
            "来源文件不能被安全、稳定地完整读取",
            requested,
            run,
            _PREPARE_CONTRACT,
            "source_path 必须指向可稳定读取的非 symlink 普通文件",
        )
    basis = {
        "governed_project_id": boundary.governed_project_id,
        "candidate_object_id": candidate,
        "schema_fingerprint": schema_fingerprint(schema),
        "worktree_fingerprint": worktree_fingerprint(boundary),
        "source_path": observed.source_path,
        "source_size_bytes": observed.source_size_bytes,
        "source_content_sha256": observed.source_content_sha256,
        "source_fingerprint": observed.source_fingerprint,
    }
    result = {
        "intake_basis": basis,
        "candidate_canonical_path": LAYOUTS["file-asset"].canonical_path(candidate),
        "carrier": "file-asset-directory",
        "payload_limit_bytes": DEFAULT_PAYLOAD_BUDGET,
        "fact_object_contract": {
            "required_fields": ["title", "filename", "media_type", "signature"],
            "managed_fields": [
                "object_id",
                "fact_type_key",
                "created_at",
                "updated_at",
                "status",
                "size_bytes",
                "content_sha256",
            ],
            "signature_branches": [
                {"signer_type": "human"},
                {
                    "signer_type": "ai-agent",
                    "required_fields": ["agent_id", "host_environment"],
                },
            ],
        },
    }
    sources = _sources(run, _PREPARE_CONTRACT)
    return OperationExecution(
        outcome="ok",
        summary="已安全读取来源文件并形成无事实源副作用的 FileAsset 摄取依据",
        result=result,
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=sources,
        verification=(
            {
                "check": "来源文件身份、完整 bytes、size/SHA-256、Schema 与 worktree 绑定",
                "status": "passed",
                "scope": list(requested),
                "evidence": list(sources),
            },
        ),
    )


def _current_create_context(
    domain: FileAssetCreateRequest,
    repository: RepositoryInspection,
    run: GovernanceResolutionRun,
) -> tuple[CreationBoundary | None, Any | None, str | None]:
    boundary = _boundary(run)
    schema = project_fact_schemas(repository).get("file-asset")
    basis = domain.intake_basis
    if boundary is None:
        return None, schema, "当前管辖结果不能形成唯一 FileAsset 创建边界"
    if (
        boundary.governed_project_id != basis.governed_project_id
        or worktree_fingerprint(boundary) != basis.worktree_fingerprint
        or schema is None
        or schema_fingerprint(schema) != basis.schema_fingerprint
    ):
        return boundary, schema, "摄取依据已经过期或不属于当前项目、worktree 与 Schema"
    return boundary, schema, None


def _create_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain = _validated_create(request, context)
    requested = (domain.intake_basis.to_json(),)
    run = _governance(domain)
    boundary, schema, problem = _current_create_context(domain, repository, run)
    if problem is not None or boundary is None or schema is None or not durable_writes_enabled():
        detail = problem or "当前平台未开放 FileAsset 所需目录耐久写入"
        return AvailabilityEvaluation(
            "unavailable_for_request",
            unavailable_scope=requested,
            gaps=({"summary": detail, "scope": list(requested), "source_refs": [_CREATE_CONTRACT]},),
        )
    try:
        observed = observe_file_asset_source(Path(domain.intake_basis.source_path))
    except OSError:
        return AvailabilityEvaluation(
            "unavailable_for_request",
            unavailable_scope=requested,
            gaps=({"summary": "来源文件当前不能被安全完整读取", "scope": list(requested)},),
        )
    basis = domain.intake_basis
    if (
        observed.source_size_bytes != basis.source_size_bytes
        or observed.source_content_sha256 != basis.source_content_sha256
        or observed.source_fingerprint != basis.source_fingerprint
    ):
        return AvailabilityEvaluation(
            "unavailable_for_request",
            unavailable_scope=requested,
            gaps=({"summary": "来源文件已不匹配摄取依据", "scope": list(requested)},),
        )
    return AvailabilityEvaluation("available_for_request", available_scope=requested)


def _create_execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_create(request, context)
    basis = domain.intake_basis
    requested = (basis.to_json(),)
    run = _governance(domain)
    boundary, schema, problem = _current_create_context(domain, repository, run)
    sources = _sources(run, _CREATE_CONTRACT)
    if problem is not None or boundary is None or schema is None:
        return OperationExecution(
            outcome="rejected" if boundary is not None else "unavailable",
            summary=problem or "当前管辖结果不能形成唯一 FileAsset 创建边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
            gaps=(
                {
                    "summary": "必须重新调用 prepare-file-asset-intake",
                    "scope": list(requested),
                    "source_refs": [_CREATE_CONTRACT],
                },
            ),
        )
    try:
        creation = create_file_asset(
            FileAssetCreationCommand(
                boundary=boundary,
                schema=schema,
                requested_candidate_id=basis.candidate_object_id,
                expected_source_path=basis.source_path,
                expected_source_size_bytes=basis.source_size_bytes,
                expected_source_content_sha256=basis.source_content_sha256,
                expected_source_fingerprint=basis.source_fingerprint,
                supplied=domain.fact_object,
            ),
            observed_at=context.event_at,
        )
    except FactCoordinationUnavailable as error:
        return _unavailable(
            "FileAsset 共同协调锁当前不可用，未创建对象或推进编号",
            requested,
            run,
            _CREATE_CONTRACT,
            f"恢复 git common-dir 协调根访问后重试（{error.system_error_category}）",
        )

    result: dict[str, Any] = {
        "requested_candidate_id": basis.candidate_object_id,
        "allocation": {
            "allocated_object_id": creation.actual_id,
            "status": creation.allocation_status,
            "consumed": creation.allocation_consumed,
        },
        "target_namespace": {
            "canonical_path": (
                LAYOUTS["file-asset"].canonical_path(creation.actual_id)
                if creation.actual_id is not None
                else None
            ),
            "create_state": None if creation.creation_result is None else creation.creation_result.namespace_state,
            "durability": None if creation.creation_result is None else creation.creation_result.durability,
            "cleanup": None if creation.creation_result is None else creation.creation_result.cleanup,
            "rollback_state": None if creation.rollback_result is None else creation.rollback_result.namespace_state,
        },
    }
    if creation.residual_readback is not None:
        result["residual"] = {
            "canonical_path": creation.residual_readback.canonical_path,
            "check_status": creation.residual_readback.check_status,
            "current_bytes_confirmed": creation.residual_readback.current_bytes_confirmed,
        }
    if creation.status == "created":
        assert creation.actual_id is not None and creation.read is not None and creation.read.fields is not None
        result.update(
            {
                "actual_ref": {
                    "governed_project_id": boundary.governed_project_id,
                    "fact_type_key": "file-asset",
                    "object_id": creation.actual_id,
                },
                "carrier": "file-asset-directory",
                "fact_object": creation.read.fields,
                "payload": {
                    "canonical_path": creation.read.payload_canonical_path,
                    "size_bytes": creation.read.observed_size_bytes,
                    "content_sha256": creation.read.observed_content_sha256,
                    "current_bytes_confirmed": creation.read.current_bytes_confirmed,
                },
            }
        )
        gaps: tuple[dict[str, Any], ...] = ()
        if creation.coordination_release_uncertain:
            gaps = (
                {
                    "summary": "对象已创建并回读，但共同协调锁释放状态未知；再次受控写入前须核对",
                    "scope": list(requested),
                    "source_refs": [_CREATE_CONTRACT],
                },
            )
        return post_write_integrity_audit(
            OperationExecution(
            outcome="ok",
            summary="FileAsset 已原子创建并从实际 Working Tree 完整回读",
            result=result,
            requested_scope=requested,
            completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
            gaps=gaps,
            changes=(
                {
                    "summary": "FileAsset 目录已原子创建并完整回读",
                    "status": "target-created",
                    "target": LAYOUTS["file-asset"].canonical_path(creation.actual_id),
                    "source_refs": [_CREATE_CONTRACT, _TYPE_CONTRACT],
                },
            ),
            verification=(
                {
                    "check": "来源重读、成员闭集、manifest/payload 完整性与写后回读",
                    "status": "passed",
                    "scope": list(requested),
                    "evidence": list(sources),
                },
            ),
        ),
            boundary=boundary,
            schemas=project_fact_schemas(repository),
            audit_contract=_INTEGRITY_CONTRACT,
        )

    outcome = (
        "rejected"
        if creation.status in {"source_stale", "candidate_rejected", "creation_conflict"}
        else "unavailable"
    )
    details = "; ".join(issue.summary for issue in creation.issues) or creation.status
    return OperationExecution(
        outcome=outcome,
        summary="FileAsset 未创建",
        result=result,
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=sources,
        gaps=(
            {
                "summary": f"{creation.status}: {details}",
                "scope": list(requested),
                "source_refs": list(sources),
            },
        ),
    )


def _intake_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    execution = _intake_execute(request, repository, context)
    if execution.outcome == "ok":
        return AvailabilityEvaluation("available_for_request", available_scope=execution.completed_scope)
    return AvailabilityEvaluation(
        "unavailable_for_request",
        unavailable_scope=execution.requested_scope,
        gaps=execution.gaps,
    )


PREPARE_FILE_ASSET_INTAKE_IMPLEMENTATION = OperationImplementation(
    required_inputs=PREPARE_REQUIRED_INPUTS,
    optional_inputs=PREPARE_OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_intake_availability,
    call=_intake_execute,
)

CREATE_FILE_ASSET_IMPLEMENTATION = OperationImplementation(
    required_inputs=CREATE_REQUIRED_INPUTS,
    optional_inputs=CREATE_OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_create_availability,
    call=_create_execute,
)

__all__ = [
    "CREATE_FILE_ASSET_IMPLEMENTATION",
    "CREATE_OPERATION_KEY",
    "PREPARE_FILE_ASSET_INTAKE_IMPLEMENTATION",
    "PREPARE_OPERATION_KEY",
]
