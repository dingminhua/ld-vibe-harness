"""Retired operation implementation; deliberately absent from public registration."""

from __future__ import annotations

from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, FactCoordinationUnavailable
from ldvh.facts.legacy_change_log_migration import (
    LegacyChangeLogMigrationCommand,
    LegacyChangeLogMigrationResult,
    apply_legacy_change_log_migration_locked,
)
from ldvh.facts.models import FactReference
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema, project_fact_schemas
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
from ldvh.helper.operations.legacy_change_log_migration_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    LegacyChangeLogMigrationRequest,
    parse_legacy_change_log_migration_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "migrate-legacy-change-log"
_CONTRACT = source_reference(
    "rule",
    "fact-model-foundation::11.7.1 遗留 change_log 受控迁移输入与结果",
)
_SHARED_WRITE_CONTRACT = source_reference("rule", "fact-model-foundation::11.8 共享单对象受控写事务")
_INTEGRITY_CONTRACT = source_reference("rule", "fact-model-foundation::11.9-11.10 事实写后独立完整性审计")
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation",
    "code/ldvh/helper/operations/legacy_change_log_migration_operation.py",
)


def _validated_request(request: CommonRequest, context: OperationExecutionContext) -> LegacyChangeLogMigrationRequest:
    parsed = parse_legacy_change_log_migration_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACT,))
    return parsed.request


def _governance(domain: LegacyChangeLogMigrationRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _boundary(run: GovernanceResolutionRun) -> CreationBoundary | None:
    resolved = reading_boundary(run)
    return CreationBoundary(*resolved) if resolved is not None else None


def _current_read(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    reference: FactReference,
) -> FactReadResult:
    layout = LAYOUTS[reference.fact_type_key]
    read = read_fact_object(
        boundary.worktree_root,
        layout,
        schemas[reference.fact_type_key],
        reference.object_id,
        expected_common_dir=boundary.git_common_dir,
    )
    if read.check_status != "mechanically_valid" or read.fields is None:
        return read
    index = ProjectFactIndex(
        boundary.worktree_root,
        boundary.governed_project_id,
        schemas,
        boundary.git_common_dir,
    )
    key = (reference.fact_type_key, reference.object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index, (key,))
    return index.cache.get(key, read)


def _working_tree_source(boundary: CreationBoundary, read: FactReadResult, event_at: str) -> dict[str, Any]:
    return {
        "kind": "working_tree",
        "locator": (boundary.worktree_root / read.canonical_path).as_posix(),
        "observed_at": event_at,
        "details": {"view": "Working Tree", "content_fingerprint": read.content_fingerprint},
    }


def _fact_object(read: FactReadResult) -> dict[str, Any]:
    assert read.fields is not None
    return {"frontmatter": read.fields, "body": read.body or ""} if read.carrier == "markdown" else read.fields


def _result(read: FactReadResult, previous: str) -> dict[str, Any]:
    assert read.fields is not None and read.content_fingerprint is not None
    return {
        "actual_ref": {
            "governed_project_id": read.fields["governed_project_id"] if "governed_project_id" in read.fields else None,
        },
        "canonical_path": read.canonical_path,
        "carrier": read.carrier,
        "previous_content_fingerprint": previous,
        "content_fingerprint": read.content_fingerprint,
        "fact_object": _fact_object(read),
    }


def _actual_ref(reference: FactReference) -> dict[str, str]:
    return reference.to_json()


def _failure(
    result: LegacyChangeLogMigrationResult,
    domain: LegacyChangeLogMigrationRequest,
    run: GovernanceResolutionRun,
    boundary: CreationBoundary,
    sources: tuple[dict[str, Any], ...],
) -> OperationExecution:
    requested = (_actual_ref(domain.fact_ref),)
    governance = run.result.to_json() if run.result else None
    status = result.status
    if status in {"current_unavailable", "current_rejected"}:
        return OperationExecution(
            outcome="unavailable" if status == "current_unavailable" else "rejected",
            summary="当前遗留对象未形成可迁移的 mechanically valid 快照",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": "；".join(issue.summary for issue in result.issues) or "当前对象读取未通过机械检查",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    if status == "fingerprint_stale":
        return OperationExecution(
            outcome="rejected",
            summary="遗留对象内容指纹已经过期",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": "必须重新精确读取当前对象并重新形成 migration 请求",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    if status == "change_log_present":
        return OperationExecution(
            outcome="rejected",
            summary="目标对象已有 change_log，拒绝重复建立迁移起点",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": "该操作只接受确实缺少 change_log 的 legacy 对象",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    if status == "candidate_rejected":
        return OperationExecution(
            outcome="rejected",
            summary="遗留 change_log 迁移候选未通过机械检查",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": "；".join(issue.summary for issue in result.issues) or "迁移候选未通过当前类型规则",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    if status in {"replacement_conflict", "replacement_unavailable"}:
        return OperationExecution(
            outcome="rejected" if status == "replacement_conflict" else "unavailable",
            summary="遗留 change_log 迁移未能形成已提交的原子替换",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": "原子替换前目标发生变化或当前写入技术条件不可用；未声明迁移成功",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )

    assert status == "readback_failed"
    rollback = result.rollback_result
    rolled_back = rollback is not None and rollback.outcome == "replaced" and rollback.namespace_state == "committed"
    residual = result.residual_readback
    changes: list[dict[str, Any]] = []
    if rolled_back:
        changes.append(
            {
                "summary": "迁移写后回读未通过，已完成条件回滚",
                "status": "rolled-back",
                "target": _actual_ref(domain.fact_ref),
                "source_refs": [_CONTRACT],
            }
        )
    else:
        changes.append(
            {
                "summary": "迁移写后回读未通过，条件回滚未能确认",
                "status": "rollback-failed",
                "target": _actual_ref(domain.fact_ref),
                "source_refs": [_CONTRACT],
            }
        )
    verification: list[dict[str, Any]] = []
    if residual is not None:
        verification.append(
            {
                "check": "条件回滚后重新精确读取实际遗留对象",
                "status": "passed" if residual.check_status == "mechanically_valid" else residual.check_status,
                "scope": list(requested),
                "evidence": [_working_tree_source(boundary, residual, result.event_at)],
            }
        )
    else:
        verification.append(
            {
                "check": "条件回滚后重新精确读取实际遗留对象",
                "status": "unavailable",
                "scope": list(requested),
                "evidence": [_CONTRACT],
            }
        )
    return OperationExecution(
        outcome="error",
        summary="遗留 change_log 迁移写后回读未通过；已如实交还回滚和残留状态",
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=governance,
        sources=sources,
        changes=tuple(changes),
        gaps=(
            {
                "summary": "写后回读未通过；必须停止后续事实写入并依据实际残留继续诊断",
                "scope": list(requested),
                "source_refs": [_CONTRACT],
            },
        ),
        verification=tuple(verification),
    )


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_request(request, context)
    run = _governance(domain)
    requested = (_actual_ref(domain.fact_ref),)
    boundary = _boundary(run)
    request_sources = (
        *tuple(plain(source) for source in run.sources),
        *tuple(plain(source) for source in domain.authorization_reference),
        _CONTRACT,
    )
    if boundary is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成唯一遗留对象迁移边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(
                {
                    "summary": "管辖输入未形成同一项目、实际 worktree 和 common-dir 的唯一边界",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    if boundary.governed_project_id != domain.fact_ref.governed_project_id:
        return OperationExecution(
            outcome="rejected",
            summary="请求项目与实际管辖项目不一致",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=({"summary": "fact_ref 已过期或属于另一项目", "scope": list(requested), "source_refs": [_CONTRACT]},),
        )
    if not native_atomic_fact_writes_supported():
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台没有启用遗留事实迁移的原生原子后端",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(
                {
                    "summary": "当前平台没有启用同时承接共享锁与条件替换的原生原子后端",
                    "scope": list(requested),
                    "source_refs": [_SHARED_WRITE_CONTRACT],
                },
            ),
        )

    schemas = project_fact_schemas(repository)
    schema = schemas.get(domain.fact_ref.fact_type_key)
    if schema is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前来源未形成目标类型的完整派生 Schema",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=({"summary": "目标类型 Schema 不可用", "scope": list(requested), "source_refs": [_CONTRACT]},),
        )
    current = _current_read(boundary, schemas, domain.fact_ref)
    if current.content_fingerprint is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前对象无法形成可信 content fingerprint",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=({"summary": "目标对象当前不可安全读取", "scope": list(requested), "source_refs": [_CONTRACT]},),
        )
    command = LegacyChangeLogMigrationCommand(
        boundary=boundary,
        fact_type_key=domain.fact_ref.fact_type_key,
        object_id=domain.fact_ref.object_id,
        schemas=schemas,
        schema=schema,
        expected_content_fingerprint=domain.expected_content_fingerprint,
        migration_signature={
            "agent_id": domain.migration_signature["agent_id"],
            "host_environment": domain.migration_signature["host_environment"],
            "session_id": domain.migration_signature["session_id"],
        },
        migration_summary=domain.migration_summary,
        event_at=context.event_at,
    )
    try:
        from ldvh.facts.creation import allocation_lock

        with allocation_lock(boundary, LAYOUTS[domain.fact_ref.fact_type_key]):
            result = apply_legacy_change_log_migration_locked(command)
    except FactCoordinationUnavailable as error:
        return OperationExecution(
            outcome="unavailable",
            summary="事实对象共同协调锁不可用，未执行 legacy change_log 迁移",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*request_sources, _SHARED_WRITE_CONTRACT),
            gaps=(
                {
                    "summary": f"共享协调锁不可用：{error}",
                    "scope": list(requested),
                    "source_refs": [_SHARED_WRITE_CONTRACT],
                },
            ),
        )
    except OSError as error:
        return OperationExecution(
            outcome="unavailable",
            summary="事实对象迁移写入技术条件不可用",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*request_sources, _SHARED_WRITE_CONTRACT),
            gaps=(
                {
                    "summary": f"受控写入未能取得或使用共享协调锁：{type(error).__name__}",
                    "scope": list(requested),
                    "source_refs": [_SHARED_WRITE_CONTRACT],
                },
            ),
        )

    if result.status != "updated":
        return _failure(result, domain, run, boundary, request_sources)
    assert result.readback is not None and result.readback.content_fingerprint is not None
    working_tree_source = _working_tree_source(boundary, result.readback, context.event_at)
    execution = OperationExecution(
        outcome="ok",
        summary="遗留 change_log 已完成单对象 CAS 迁移、写后回读",
        result={
            "actual_ref": _actual_ref(domain.fact_ref),
            "canonical_path": result.readback.canonical_path,
            "carrier": result.readback.carrier,
            "previous_content_fingerprint": domain.expected_content_fingerprint,
            "content_fingerprint": result.readback.content_fingerprint,
            "fact_object": _fact_object(result.readback),
            "migration": {"event_at": context.event_at, "history_recovered": False},
        },
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=(*request_sources, working_tree_source, _IMPLEMENTATION_SOURCE),
        changes=(
            {
                "summary": "已为一个缺失 change_log 的 legacy 事实对象建立可信迁移起点",
                "status": "updated",
                "target": _actual_ref(domain.fact_ref),
                "source_refs": [working_tree_source],
            },
        ),
        verification=(
            {
                "check": "迁移候选、CAS 替换和写后精确回读已通过；原始历史未被恢复或伪造",
                "status": "passed",
                "scope": list(requested),
                "evidence": [working_tree_source, _CONTRACT],
            },
        ),
    )
    return post_write_integrity_audit(execution, boundary=boundary, schemas=schemas, audit_contract=_INTEGRITY_CONTRACT)


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain = _validated_request(request, context)
    run = _governance(domain)
    boundary = _boundary(run)
    requested = (_actual_ref(domain.fact_ref),)
    if boundary is None:
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=requested,
            gaps=({"summary": "当前请求不能形成唯一管辖迁移边界"},),
        )
    schemas = project_fact_schemas(repository)
    current = _current_read(boundary, schemas, domain.fact_ref)
    if (
        current.check_status != "mechanically_valid"
        or current.fields is None
        or current.content_fingerprint != domain.expected_content_fingerprint
    ):
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=requested,
            gaps=({"summary": "目标对象不可迁移或请求 fingerprint 已过期"},),
        )
    if "change_log" in current.fields:
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=requested,
            gaps=({"summary": "目标对象已有 change_log，迁移操作不适用"},),
        )
    return AvailabilityEvaluation(availability="available_for_request", available_scope=requested)


MIGRATION_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACT),
    check_availability=_check_availability,
    call=_execute,
)

__all__ = ["MIGRATION_IMPLEMENTATION", "OPERATION_KEY"]
