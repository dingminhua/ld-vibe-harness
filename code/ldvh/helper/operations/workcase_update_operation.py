"""Apply a source-defined controlled delta to one current-profile WorkCase."""

from __future__ import annotations

from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, FactCoordinationUnavailable
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema, project_fact_schemas
from ldvh.facts.update_application import FactUpdateCommand, FactUpdateResult, apply_fact_update
from ldvh.facts.workcase_update import CURRENT_PROFILE, construct_workcase_update
from ldvh.filesystem import durable_writes_enabled
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_operation_support import plain, reading_boundary
from ldvh.helper.operations.workcase_update_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    WorkCaseUpdateRequest,
    parse_workcase_update_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "update-workcase"
_CONTRACT = source_reference(
    "rule",
    "workcase-fact-type::current-profile WorkCase 专属受控变更输入字段",
)
_SHARED_WRITE_CONTRACT = source_reference("rule", "fact-model-foundation::11.8 共享单对象受控写事务")
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation",
    "code/ldvh/helper/operations/workcase_update_operation.py",
)


def _validated_request(
    request: CommonRequest,
    context: OperationExecutionContext,
    schema: FactSchema | None = None,
) -> WorkCaseUpdateRequest:
    parsed = parse_workcase_update_request(request, context, schema)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACT,))
    return parsed.request


def _governance(domain: WorkCaseUpdateRequest) -> GovernanceResolutionRun:
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
    object_id: str,
) -> FactReadResult:
    layout = LAYOUTS["workcase"]
    read = read_fact_object(
        boundary.worktree_root,
        layout,
        schemas["workcase"],
        object_id,
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
    key = ("workcase", object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index)
    return index.cache.get(key, read)


def _working_tree_source(
    boundary: CreationBoundary,
    canonical_path: str,
    event_at: str | None,
) -> dict[str, Any]:
    source: dict[str, Any] = {
        "kind": "working_tree",
        "locator": (boundary.worktree_root / canonical_path).as_posix(),
        "details": {"view": "Working Tree"},
    }
    if event_at is not None:
        source["observed_at"] = event_at
    return source


def _state(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": fields.get("status"),
        "phase": fields.get("phase"),
        "plan_version": fields.get("plan_version"),
        "result_version": fields.get("result_version"),
    }


def _result(
    before: FactReadResult,
    after: FactReadResult,
    project_id: str,
    object_id: str,
    *,
    event_at: str | None,
    receipts: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    assert before.fields is not None and before.content_fingerprint is not None
    assert after.fields is not None and after.content_fingerprint is not None
    changed_fields = sorted(
        key
        for key in set(before.fields) | set(after.fields)
        if before.fields.get(key) != after.fields.get(key) or (key in before.fields) != (key in after.fields)
    )
    return {
        "actual_ref": {
            "governed_project_id": project_id,
            "fact_type_key": "workcase",
            "object_id": object_id,
        },
        "canonical_path": after.canonical_path,
        "previous_content_fingerprint": before.content_fingerprint,
        "content_fingerprint": after.content_fingerprint,
        "event_at": event_at,
        "before_state": _state(before.fields),
        "after_state": _state(after.fields),
        "changed_fields": changed_fields,
        "managed_record_receipts": list(receipts),
    }


def _issue_summary(issues: tuple[FactIssue, ...]) -> str:
    return "; ".join(f"{issue.field_path + ': ' if issue.field_path else ''}{issue.summary}" for issue in issues)


def _rejected(
    domain: WorkCaseUpdateRequest,
    run: GovernanceResolutionRun,
    summary: str,
    detail: str,
    sources: tuple[dict[str, Any], ...],
) -> OperationExecution:
    requested = (domain.fact_ref.to_json(),)
    return OperationExecution(
        outcome="rejected",
        summary=summary,
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=sources,
        gaps=({"summary": detail, "scope": list(requested), "source_refs": [_CONTRACT]},),
    )


def _application_failure(
    result: FactUpdateResult,
    domain: WorkCaseUpdateRequest,
    run: GovernanceResolutionRun,
    sources: tuple[dict[str, Any], ...],
) -> OperationExecution | None:
    requested = (domain.fact_ref.to_json(),)
    governance = run.result.to_json() if run.result else None
    if result.status in {"updated", "no_change"}:
        return None
    if result.status == "durability_unavailable":
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台尚未获准以 file-only 耐久等级更新 WorkCase",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=({"summary": "未写入目标载体", "scope": list(requested), "source_refs": [_CONTRACT]},),
        )
    if result.status in {"current_rejected", "current_unavailable"}:
        return OperationExecution(
            outcome="unavailable" if result.status == "current_unavailable" else "rejected",
            summary="当前 WorkCase 未形成可更新的 mechanically valid 快照",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": _issue_summary(result.issues) or "当前对象读取未通过机械检查",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    if result.status == "fingerprint_stale":
        return _rejected(domain, run, "WorkCase 内容指纹已经过期", "重新精确读取当前对象后再形成 delta", sources)
    if result.status == "event_time_not_successor":
        return _rejected(
            domain,
            run,
            "本次 event_at 不能形成 updated_at 严格后继",
            _issue_summary(result.issues),
            sources,
        )
    if result.status in {"candidate_rejected", "candidate_unavailable"}:
        return OperationExecution(
            outcome="unavailable" if result.status == "candidate_unavailable" else "rejected",
            summary="WorkCase 完整 after 未通过机械检查",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": _issue_summary(result.issues) or "项目级机械检查未完成",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    if result.status in {"replacement_conflict", "replacement_unavailable"}:
        return OperationExecution(
            outcome="rejected" if result.status == "replacement_conflict" else "unavailable",
            summary="原子替换前对象发生变化" if result.status == "replacement_conflict" else "原子替换技术条件不成立",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=(*sources, _IMPLEMENTATION_SOURCE),
            gaps=(
                {
                    "summary": "重新精确读取当前对象后再形成 delta",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    assert result.status == "readback_failed"
    rollback = result.rollback_result
    assert rollback is not None
    rolled_back = rollback.outcome == "replaced" and rollback.namespace_state == "committed"
    return OperationExecution(
        outcome="error",
        summary="写后回读未通过；已回滚" if rolled_back else "写后回读未通过且无法安全回滚",
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=governance,
        sources=(*sources, _IMPLEMENTATION_SOURCE),
        changes=(
            {
                "summary": "已恢复更新前载体" if rolled_back else "新载体可能残留且未完成验证",
                "status": "rolled-back" if rolled_back else "rollback-failed",
                "target": domain.fact_ref.to_json(),
                "source_refs": [_CONTRACT],
            },
        ),
        gaps=(
            {
                "summary": _issue_summary(result.issues) or "写后项目级检查未完成",
                "scope": list(requested),
                "source_refs": [_CONTRACT],
            },
        ),
    )


def _coordination_unavailable(
    error: FactCoordinationUnavailable,
    requested: tuple[dict[str, str], ...],
    run: GovernanceResolutionRun,
    sources: tuple[dict[str, Any], ...],
    *,
    diagnostic_profile: bool,
) -> OperationExecution:
    diagnostic = {
        "summary": "受控写入共同协调锁不可用",
        "code": "controlled_write_lock_unavailable",
        "details": {
            "stage": error.stage,
            "path_role": error.path_role,
            "required_access": error.required_access,
            "system_error_category": error.system_error_category,
            "target_unchanged": True,
            "allocator_unchanged": True,
            "counter_unchanged": True,
        },
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    return OperationExecution(
        outcome="unavailable",
        summary="WorkCase 共同协调锁当前不可用，未更新目标",
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=(*sources, _SHARED_WRITE_CONTRACT),
        gaps=(
            {
                "summary": "恢复 git common-dir 下 LDVH 协调根的创建、打开与排他锁权限后重试",
                "scope": list(requested),
                "source_refs": [_SHARED_WRITE_CONTRACT],
                "code": "controlled_write_lock_unavailable",
            },
        ),
        diagnostics=(diagnostic,) if diagnostic_profile else (),
        follow_up={
            "summary": "恢复共同协调根访问后重新读取当前对象并重试",
            "required_inputs": [],
            "required_human_decisions": [],
            "resume_conditions": [
                {
                    "summary": "git common-dir 的 LDVH 协调根允许创建或打开锁并取得排他锁",
                    "scope": list(requested),
                    "source_refs": [_SHARED_WRITE_CONTRACT],
                }
            ],
            "suggested_operations": [
                {
                    "summary": "重新精确读取当前 WorkCase",
                    "scope": list(requested),
                    "source_refs": [_SHARED_WRITE_CONTRACT],
                    "operation_key": "read-fact-objects",
                }
            ],
        },
    )


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_request(request, context)
    reference = domain.fact_ref
    requested = (reference.to_json(),)
    run = _governance(domain)
    boundary = _boundary(run)
    request_sources = (
        *tuple(plain(source) for source in run.sources),
        *tuple(plain(source) for source in domain.authorization_reference),
        _CONTRACT,
    )
    if boundary is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成唯一 WorkCase 更新边界",
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
    if boundary.governed_project_id != reference.governed_project_id:
        return _rejected(domain, run, "请求项目与实际管辖项目不一致", "fact_ref 已过期或属于另一项目", request_sources)

    schemas = project_fact_schemas(repository)
    schema = schemas.get("workcase")
    if schema is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前来源未形成 WorkCase 的完整派生 Schema",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=({"summary": "WorkCase Schema 不可用", "scope": list(requested), "source_refs": [_CONTRACT]},),
        )
    domain = _validated_request(request, context, schema)
    if not durable_writes_enabled():
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台尚未获准以 file-only 耐久等级更新 WorkCase",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(
                {
                    "summary": (
                        "未创建锁状态或替换 WorkCase：当前 Windows 实现未满足锁及相应耐久/"
                        "并发保障；需先说明受影响保障，并由 Human 决定是否接受具体残留风险"
                    ),
                    "scope": list(requested),
                    "source_refs": [_SHARED_WRITE_CONTRACT],
                },
            ),
        )
    current = _current_read(boundary, schemas, reference.object_id)
    if current.check_status != "mechanically_valid" or current.fields is None:
        if current.check_status == "unavailable":
            return OperationExecution(
                outcome="unavailable",
                summary="当前 WorkCase 的技术读取条件不成立",
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=request_sources,
                gaps=(
                    {
                        "summary": _issue_summary(current.issues) or "恢复目标读取条件后重试",
                        "scope": list(requested),
                        "source_refs": [_CONTRACT],
                    },
                ),
            )
        return _rejected(
            domain,
            run,
            "当前 WorkCase 不存在或未形成 mechanically valid 快照",
            _issue_summary(current.issues) or "重新精确读取并修复当前对象",
            request_sources,
        )
    if (
        current.fields.get("object_id") != reference.object_id
        or current.fields.get("fact_type_key") != "workcase"
        or current.fields.get("workcase_profile") != CURRENT_PROFILE
    ):
        return _rejected(
            domain,
            run,
            "目标对象不适用于 WorkCase 专属更新",
            "legacy 或身份不一致对象应使用通用更新",
            request_sources,
        )
    if current.content_fingerprint != domain.expected_content_fingerprint:
        return _rejected(
            domain,
            run,
            "WorkCase 内容指纹已经过期",
            "重新精确读取当前对象后再形成 delta",
            request_sources,
        )

    construction = construct_workcase_update(
        current.fields,
        set_fields=domain.set_fields,
        remove_fields=domain.remove_fields,
        managed_records=domain.managed_records,
        event_at=context.event_at,
    )
    if construction.supplied is None:
        return _rejected(
            domain,
            run,
            "显式 WorkCase delta 不能基于当前快照形成合法 after",
            "; ".join(construction.problems),
            request_sources,
        )
    try:
        application = apply_fact_update(
            FactUpdateCommand(
                boundary=boundary,
                fact_type_key="workcase",
                object_id=reference.object_id,
                schemas=schemas,
                schema=schema,
                expected_content_fingerprint=domain.expected_content_fingerprint,
                supplied=construction.supplied,
                body=None,
                event_at=context.event_at,
                allow_workcase_progress_mutation=True,
            )
        )
    except FactCoordinationUnavailable as error:
        return _coordination_unavailable(
            error,
            requested,
            run,
            request_sources,
            diagnostic_profile=request.response_profile == "diagnostic",
        )
    failure = _application_failure(application, domain, run, request_sources)
    if failure is not None:
        return failure
    before = application.current
    after = application.readback
    assert before is not None and after is not None
    no_change = application.status == "no_change"
    if no_change:
        assert construction.receipts == ()
    working_tree_source = _working_tree_source(
        boundary,
        after.canonical_path,
        None if no_change else context.event_at,
    )
    result = _result(
        before,
        after,
        boundary.governed_project_id,
        reference.object_id,
        event_at=None if no_change else context.event_at,
        receipts=() if no_change else construction.receipts,
    )
    if no_change:
        return OperationExecution(
            outcome="no_change",
            summary="显式 delta 与托管动作未形成领域变化，未重写 WorkCase",
            result=result,
            requested_scope=requested,
            completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*request_sources, working_tree_source, _IMPLEMENTATION_SOURCE),
            verification=(
                {
                    "check": "当前对象指纹仍匹配且领域 after 与 before 相同",
                    "status": "passed",
                    "scope": list(requested),
                    "evidence": [working_tree_source, _CONTRACT],
                },
            ),
        )
    replacement = application.replacement_result
    assert replacement is not None
    return OperationExecution(
        outcome="ok",
        summary="WorkCase 已完成专属 delta 构造、单对象 CAS 替换和写后回读",
        result=result,
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=(*request_sources, working_tree_source, _IMPLEMENTATION_SOURCE),
        changes=(
            {
                "summary": f"已更新字段：{', '.join(result['changed_fields'])}",
                "status": "updated",
                "target": reference.to_json(),
                "source_refs": [working_tree_source],
            },
        ),
        verification=(
            {
                "check": (
                    "指纹、完整 after、转换、原子替换和写后读取已通过；"
                    f"namespace={replacement.namespace_state}, durability={replacement.durability}, "
                    f"cleanup={replacement.cleanup}"
                ),
                "status": "passed",
                "scope": list(requested),
                "evidence": [working_tree_source, _CONTRACT],
            },
        ),
    )


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain = _validated_request(request, context)
    requested = domain.fact_ref.to_json()
    if not durable_writes_enabled():
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=({"summary": "当前平台耐久写能力未获准", "scope": [requested], "source_refs": [_CONTRACT]},),
        )
    run = _governance(domain)
    boundary = _boundary(run)
    schemas = project_fact_schemas(repository)
    schema = schemas.get("workcase")
    if boundary is None or boundary.governed_project_id != domain.fact_ref.governed_project_id or schema is None:
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前请求的管辖、项目或 WorkCase Schema 前置条件不成立",
                    "scope": [requested],
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    _validated_request(request, context, schema)
    current = _current_read(boundary, schemas, domain.fact_ref.object_id)
    if (
        current.check_status != "mechanically_valid"
        or current.fields is None
        or current.fields.get("workcase_profile") != CURRENT_PROFILE
        or current.content_fingerprint != domain.expected_content_fingerprint
    ):
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前对象不适用、不可更新或请求指纹已过期",
                    "scope": [requested],
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    return AvailabilityEvaluation(availability="available_for_request", available_scope=(requested,))


WORKCASE_UPDATE_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACT),
    check_availability=_check_availability,
    call=_execute,
)


__all__ = ["OPERATION_KEY", "WORKCASE_UPDATE_IMPLEMENTATION"]
