"""Expose the three source-defined WorkCase full-after write operations."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Literal

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, FactCoordinationUnavailable
from ldvh.facts.models import FactIssue
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
from ldvh.helper.operations.fact_creation_operation import inject_observed_write_signature
from ldvh.helper.operations.fact_creation_request import observed_write_signature_required_problem
from ldvh.helper.operations.fact_operation_support import (
    plain,
    post_write_integrity_audit,
    reading_boundary,
)
from ldvh.helper.operations.workcase_update_request import (
    BEGIN_TERMINATION_OPTIONAL_INPUTS,
    BEGIN_TERMINATION_REQUIRED_INPUTS,
    CLOSE_OPTIONAL_INPUTS,
    CLOSE_REQUIRED_INPUTS,
    COMPLETE_TERMINATION_OPTIONAL_INPUTS,
    COMPLETE_TERMINATION_REQUIRED_INPUTS,
    CORRECT_CLOSED_OPTIONAL_INPUTS,
    CORRECT_CLOSED_REQUIRED_INPUTS,
    UPDATE_OPTIONAL_INPUTS,
    UPDATE_REQUIRED_INPUTS,
    CorrectClosedWorkCaseRequest,
    WorkCaseWriteRequest,
    parse_begin_workcase_termination_request,
    parse_close_workcase_request,
    parse_complete_workcase_termination_request,
    parse_correct_closed_workcase_request,
    parse_update_workcase_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

WorkCaseWriteMode = Literal["update", "close", "correct", "begin_termination", "complete_termination"]

UPDATE_OPERATION_KEY = "update-workcase"
CLOSE_OPERATION_KEY = "close-workcase"
CORRECT_CLOSED_OPERATION_KEY = "correct-closed-workcase"
BEGIN_TERMINATION_OPERATION_KEY = "begin-workcase-termination"
COMPLETE_TERMINATION_OPERATION_KEY = "complete-workcase-termination"

_CONTRACTS = {
    "update": source_reference("rule", "workcase-fact-type::update-workcase 输入与结果"),
    "close": source_reference("rule", "workcase-fact-type::close-workcase 输入与结果"),
    "correct": source_reference("rule", "workcase-fact-type::correct-closed-workcase 输入与结果"),
    "begin_termination": source_reference("rule", "workcase-fact-type::begin-workcase-termination 输入与结果"),
    "complete_termination": source_reference("rule", "workcase-fact-type::complete-workcase-termination 输入与结果"),
}
_SHARED_WRITE_CONTRACT = source_reference("rule", "fact-model-foundation::11.8 共享单对象受控写事务")
_INTEGRITY_CONTRACT = source_reference("rule", "fact-model-foundation::11.9-11.10 事实写后独立完整性审计")
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation",
    "code/ldvh/helper/operations/workcase_update_operation.py",
)


def _validated_request(
    mode: WorkCaseWriteMode,
    request: CommonRequest,
    context: OperationExecutionContext,
) -> WorkCaseWriteRequest:
    if mode == "update":
        parsed = parse_update_workcase_request(request, context)
    elif mode == "close":
        parsed = parse_close_workcase_request(request, context)
    elif mode == "begin_termination":
        parsed = parse_begin_workcase_termination_request(request, context)
    elif mode == "complete_termination":
        parsed = parse_complete_workcase_termination_request(request, context)
    else:
        parsed = parse_correct_closed_workcase_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACTS[mode],))
    return parsed.request


def _governance(domain: WorkCaseWriteRequest) -> GovernanceResolutionRun:
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
    stabilize_project_index(index, (key,))
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


def _residual_working_tree_source(
    boundary: CreationBoundary,
    read: FactReadResult,
    event_at: str,
) -> dict[str, Any]:
    source = _working_tree_source(boundary, read.canonical_path, event_at)
    details = source["details"]
    details["check_status"] = read.check_status
    if read.content_fingerprint is not None:
        details["content_fingerprint"] = read.content_fingerprint
    return source


def _coordination_release_gap(
    requested: tuple[dict[str, str], ...],
    *,
    committed: bool,
) -> dict[str, Any]:
    gap = {
        "summary": (
            "事实目标的原子替换已在 Working Tree 生效并成功回读；共同锁释放未能确认，"
            "后续受控写的串行协调状态未知；再次执行受控写入前须人工核对锁状态"
            if committed
            else (
                "事实目标确认未变化；共同锁释放未能确认，后续受控写的串行协调状态未知；"
                "再次执行受控写入前须人工核对锁状态"
            )
        ),
        "scope": list(requested),
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    if committed:
        gap["code"] = "controlled_write_lock_release_uncertain"
    return gap


def _coordination_release_diagnostic(*, committed: bool) -> dict[str, Any]:
    diagnostic = {
        "summary": "共同协调锁释放状态未能确认",
        "details": {
            "stage": "common_dir_lock_release",
            "fact_target_state": "committed_and_read_back" if committed else "unchanged_and_read_back",
            "subsequent_controlled_write_serialization": "uncertain",
        },
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    if committed:
        diagnostic["code"] = "controlled_write_lock_release_uncertain"
    return diagnostic


def _coordination_release_follow_up(requested: tuple[dict[str, str], ...]) -> dict[str, Any]:
    return {
        "summary": "再次执行受控写入前，需要恢复并确认共同锁的串行协调状态",
        "required_inputs": [],
        "required_human_decisions": [],
        "resume_conditions": [
            {
                "summary": "人工核对共同锁状态，并确认受控写入口能够重新取得和释放该锁",
                "scope": list(requested),
                "source_refs": [_SHARED_WRITE_CONTRACT],
            }
        ],
        "suggested_operations": [],
    }


def _merge_follow_up(
    existing: dict[str, Any] | None,
    coordination: dict[str, Any],
) -> dict[str, Any]:
    if existing is None:
        return coordination
    return {
        "summary": f"{existing['summary']}；{coordination['summary']}",
        "required_inputs": [*existing["required_inputs"], *coordination["required_inputs"]],
        "required_human_decisions": [
            *existing["required_human_decisions"],
            *coordination["required_human_decisions"],
        ],
        "resume_conditions": [*existing["resume_conditions"], *coordination["resume_conditions"]],
        "suggested_operations": [*existing["suggested_operations"], *coordination["suggested_operations"]],
    }


def _coordination_preserved_result_overlay(
    execution: OperationExecution,
    application: object,
    requested: tuple[dict[str, str], ...],
    *,
    diagnostic_profile: bool,
) -> OperationExecution:
    if not bool(getattr(application, "coordination_release_uncertain", False)):
        return execution
    status = getattr(application, "status", None)
    gap = {
        "summary": (
            f"WorkCase 领域结果（status={status}）已在共同锁释放前形成并保留；共同锁释放未能确认，"
            "后续受控写的串行协调状态未知；目标、残留与未完成验证仍以本响应原结果为准，"
            "再次执行受控写入前须人工核对锁状态"
        ),
        "scope": list(requested),
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    diagnostic = {
        "summary": "共同协调锁释放状态未能确认",
        "details": {
            "stage": "common_dir_lock_release",
            "domain_result_status": status,
            "fact_target_state": "as_reported_by_domain_result",
            "subsequent_controlled_write_serialization": "uncertain",
        },
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    sources = (
        execution.sources
        if _SHARED_WRITE_CONTRACT in execution.sources
        else (*execution.sources, _SHARED_WRITE_CONTRACT)
    )
    coordination_follow_up = _coordination_release_follow_up(requested)
    return replace(
        execution,
        sources=sources,
        gaps=(*execution.gaps, gap),
        diagnostics=(*execution.diagnostics, *((diagnostic,) if diagnostic_profile else ())),
        follow_up=_merge_follow_up(execution.follow_up, coordination_follow_up),
    )


def _rollback_failure_prefix(rollback: object) -> str:
    """Describe only the rollback result's own namespace evidence."""

    namespace_state = getattr(rollback, "namespace_state", None)
    if namespace_state == "uncertain":
        return "条件回滚在文件命名空间（namespace）中的生效情况无法确认"
    if namespace_state == "not_committed":
        if getattr(rollback, "outcome", None) == "conflict":
            return "条件回滚发生冲突，确认未在文件命名空间（namespace）生效"
        return "条件回滚确认未在文件命名空间（namespace）生效"
    return "条件回滚未完成"


def _fact_object(read: FactReadResult) -> dict[str, Any]:
    assert read.fields is not None
    return read.fields


def _result(
    before: FactReadResult,
    after: FactReadResult,
    project_id: str,
    object_id: str,
) -> dict[str, Any]:
    assert before.content_fingerprint is not None
    assert after.content_fingerprint is not None
    return {
        "actual_ref": {
            "governed_project_id": project_id,
            "fact_type_key": "workcase",
            "object_id": object_id,
        },
        "canonical_path": after.canonical_path,
        "carrier": after.carrier,
        "previous_content_fingerprint": before.content_fingerprint,
        "content_fingerprint": after.content_fingerprint,
        "fact_object": _fact_object(after),
    }


def _issue_summary(issues: tuple[FactIssue, ...]) -> str:
    return "; ".join(f"{issue.field_path + ': ' if issue.field_path else ''}{issue.summary}" for issue in issues)


def _request_sources(
    mode: WorkCaseWriteMode,
    domain: WorkCaseWriteRequest,
    run: GovernanceResolutionRun,
) -> tuple[dict[str, Any], ...]:
    review_reference: tuple[dict[str, Any], ...] = ()
    if isinstance(domain, CorrectClosedWorkCaseRequest) and domain.independent_review_reference is not None:
        review_reference = (plain(domain.independent_review_reference),)
    return (
        *tuple(plain(source) for source in run.sources),
        *tuple(plain(source) for source in domain.authorization_reference),
        *review_reference,
        _CONTRACTS[mode],
    )


def _rejected(
    mode: WorkCaseWriteMode,
    domain: WorkCaseWriteRequest,
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
        gaps=(
            {
                "summary": detail,
                "scope": list(requested),
                "source_refs": [_CONTRACTS[mode]],
            },
        ),
    )


def _apply_core_workcase_write(
    mode: WorkCaseWriteMode,
    domain: WorkCaseWriteRequest,
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    schema: FactSchema,
    event_at: str,
    observed_context: dict[str, Any],
) -> object:
    """The only Helper-to-Core WorkCase transaction adapter."""

    from ldvh.facts.relations import WorkCaseRouteTargetSnapshot
    from ldvh.facts.workcase_update import WorkCaseWriteCommand, apply_workcase_write

    route_targets = ()
    independent_review_reference = None
    if isinstance(domain, CorrectClosedWorkCaseRequest):
        route_targets = tuple(
            WorkCaseRouteTargetSnapshot(
                item.target,
                item.content_fingerprint,
                f"route_target_fingerprints[{index}].target",
            )
            for index, item in enumerate(domain.route_target_fingerprints)
        )
        independent_review_reference = domain.independent_review_reference
    return apply_workcase_write(
        WorkCaseWriteCommand(
            boundary=boundary,
            schemas=schemas,
            schema=schema,
            object_id=domain.fact_ref.object_id,
            expected_content_fingerprint=domain.expected_content_fingerprint,
            supplied=inject_observed_write_signature(dict(domain.fact_object), observed_context),
            event_at=event_at,
            mode=mode,
            authorization_reference=domain.authorization_reference,
            route_target_fingerprints=route_targets,
            independent_review_reference=independent_review_reference,
        )
    )


def _application_failure(
    mode: WorkCaseWriteMode,
    result: object,
    domain: WorkCaseWriteRequest,
    run: GovernanceResolutionRun,
    sources: tuple[dict[str, Any], ...],
    boundary: CreationBoundary,
    event_at: str,
) -> OperationExecution | None:
    status = getattr(result, "status", None)
    if status in {"updated", "no_change"}:
        return None
    requested = (domain.fact_ref.to_json(),)
    governance = run.result.to_json() if run.result else None
    issues = getattr(result, "issues", ())
    issue_summary = _issue_summary(issues) if isinstance(issues, tuple) else ""

    if status == "invalid_request":
        return OperationExecution(
            outcome="invalid_request",
            summary="提交给 WorkCase 核心事务的请求结构不符合规范",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=({"summary": issue_summary, "scope": list(requested), "source_refs": [_CONTRACTS[mode]]},),
        )
    if status == "durability_unavailable":
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台没有启用 WorkCase 写入的原生原子后端",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=({"summary": "未写入目标载体", "scope": list(requested), "source_refs": [_SHARED_WRITE_CONTRACT]},),
        )
    if status in {"current_rejected", "current_unavailable"}:
        return OperationExecution(
            outcome="unavailable" if status == "current_unavailable" else "rejected",
            summary="当前 WorkCase 不满足该操作对变更前快照的要求",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": issue_summary or "当前对象读取或 operation before 条件不成立",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    if status == "fingerprint_stale":
        return _rejected(mode, domain, run, "WorkCase 内容指纹已经过期", "重新精确读取当前对象后重试", sources)
    if status == "event_time_not_successor":
        return _rejected(
            mode,
            domain,
            run,
            "本次事件时间不能形成 updated_at 严格后继",
            issue_summary,
            sources,
        )
    if status in {"candidate_rejected", "candidate_unavailable"}:
        return OperationExecution(
            outcome="unavailable" if status == "candidate_unavailable" else "rejected",
            summary="WorkCase 完整 after 未通过专属机械检查",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": issue_summary or "完整 after、转换、关口或目标检查未成立",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    if status in {"replacement_conflict", "replacement_unavailable"}:
        replacement = getattr(result, "replacement_result", None)
        namespace_uncertain = getattr(replacement, "namespace_state", None) == "uncertain"
        return OperationExecution(
            outcome="rejected" if status == "replacement_conflict" else "unavailable",
            summary=(
                "原子替换前 WorkCase 已发生变化" if status == "replacement_conflict" else "原子替换技术条件不成立"
            ),
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=(*sources, _IMPLEMENTATION_SOURCE),
            gaps=(
                {
                    "summary": (
                        "文件命名空间（namespace）中的原子替换是否生效无法确认；"
                        "必须重新精确读取当前 WorkCase 事实载体与全部分流目标（route targets）"
                        if namespace_uncertain
                        else (
                            "已确认原子替换未在文件命名空间（namespace）生效；"
                            "重新精确读取当前 WorkCase 事实载体与全部分流目标（route targets）后重试"
                        )
                    ),
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    if status == "readback_failed":
        rollback = getattr(result, "rollback_result", None)
        rolled_back = (
            rollback is not None
            and getattr(rollback, "outcome", None) == "replaced"
            and getattr(rollback, "namespace_state", None) == "committed"
        )
        residual = getattr(result, "residual_readback", None)
        residual_source: dict[str, Any] | None = None
        if isinstance(residual, FactReadResult):
            residual_source = _residual_working_tree_source(boundary, residual, event_at)
        current = getattr(result, "current", None)
        rollback_failure_prefix = _rollback_failure_prefix(rollback)
        if rolled_back:
            change_summary = "已恢复更新前载体"
        elif not isinstance(residual, FactReadResult) or residual.check_status == "unavailable":
            change_summary = f"{rollback_failure_prefix}；实际 WorkCase 事实载体的残留状态无法确认"
        elif residual.raw_text == getattr(result, "candidate_text", None):
            change_summary = (
                f"{rollback_failure_prefix}；当前重新读取观察到的实际 WorkCase 事实载体完整字节内容与本次新载体一致"
            )
        elif isinstance(current, FactReadResult) and residual.raw_text == current.raw_text:
            change_summary = (
                f"{rollback_failure_prefix}；当前重新读取观察到的实际 WorkCase 事实载体完整字节内容与更新前载体一致"
            )
        elif residual.check_status == "mechanically_valid":
            change_summary = f"{rollback_failure_prefix}；当前重新读取观察到的实际 WorkCase 事实载体是另一机械有效版本"
        elif residual.check_status == "not_found":
            change_summary = f"{rollback_failure_prefix}；当前重新读取确认实际 WorkCase 事实载体的预期位置不存在"
        elif residual.raw_text is not None:
            change_summary = (
                f"{rollback_failure_prefix}；当前实际 WorkCase 事实载体已安全完整读取，但对象未通过机械检查"
            )
        else:
            change_summary = (
                f"{rollback_failure_prefix}；当前实际 WorkCase 事实载体未能安全完整读取，"
                "机械检查未通过（状态为 `invalid`）"
            )
        residual_unknown = not rolled_back and (
            not isinstance(residual, FactReadResult) or residual.check_status == "unavailable"
        )
        residual_refs = () if residual_source is None else (residual_source,)
        residual_gap = (
            (
                {
                    "summary": "条件回滚后的实际 WorkCase 事实载体无法确认",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            )
            if residual_unknown
            else ()
        )
        residual_verification = (
            (
                {
                    "check": "条件回滚后重新精确读取并机械检查实际 WorkCase 事实载体",
                    "status": (
                        "unavailable"
                        if not isinstance(residual, FactReadResult) or residual.check_status == "unavailable"
                        else "passed"
                        if residual.check_status == "mechanically_valid"
                        else "failed"
                    ),
                    "scope": list(requested),
                    "evidence": [*residual_refs, _CONTRACTS[mode]],
                },
            )
            if not rolled_back
            else ()
        )
        return OperationExecution(
            outcome="error",
            summary=("写后回读未通过；已完成条件回滚" if rolled_back else "写后回读未通过，且未能确认条件回滚已经完成"),
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=(*sources, *residual_refs, _IMPLEMENTATION_SOURCE),
            changes=(
                {
                    "summary": change_summary,
                    "status": "rolled-back" if rolled_back else "rollback-failed",
                    "target": domain.fact_ref.to_json(),
                    "source_refs": [_CONTRACTS[mode], *residual_refs],
                },
            ),
            gaps=(
                {
                    "summary": issue_summary or "写后项目级检查未完成",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
                *residual_gap,
            ),
            verification=residual_verification,
        )
    return OperationExecution(
        outcome="error",
        summary="WorkCase 专属事务返回未知内部状态",
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=governance,
        sources=(*sources, _IMPLEMENTATION_SOURCE),
    )


def _coordination_unavailable(
    mode: WorkCaseWriteMode,
    error: FactCoordinationUnavailable,
    domain: WorkCaseWriteRequest,
    run: GovernanceResolutionRun,
    sources: tuple[dict[str, Any], ...],
    *,
    diagnostic_profile: bool,
) -> OperationExecution:
    requested = (domain.fact_ref.to_json(),)
    diagnostic = {
        "summary": "受控写入共同协调锁不可用",
        "code": "controlled_write_lock_unavailable",
        "details": {
            "stage": error.stage,
            "path_role": error.path_role,
            "required_access": error.required_access,
            "system_error_category": error.system_error_category,
            "target_unchanged": True,
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
                "summary": "恢复 git common-dir 下 LDVH 协调根访问后重试",
                "scope": list(requested),
                "source_refs": [_SHARED_WRITE_CONTRACT],
                "code": "controlled_write_lock_unavailable",
            },
        ),
        diagnostics=(diagnostic,) if diagnostic_profile else (),
    )


def _execute(
    mode: WorkCaseWriteMode,
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_request(mode, request, context)
    reference = domain.fact_ref
    requested = (reference.to_json(),)
    run = _governance(domain)
    sources = _request_sources(mode, domain, run)
    boundary = _boundary(run)
    if boundary is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成唯一 WorkCase 写入边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
            gaps=(
                {
                    "summary": "管辖输入未形成同一项目、实际 worktree 和 common-dir 的唯一边界",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    if boundary.governed_project_id != reference.governed_project_id:
        return _rejected(mode, domain, run, "请求项目与实际管辖项目不一致", "fact_ref 属于另一项目", sources)

    schemas = project_fact_schemas(repository)
    schema = schemas.get("workcase")
    if schema is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前来源未形成 WorkCase 的完整派生 Schema",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
        )
    if not native_atomic_fact_writes_supported():
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台没有启用 WorkCase 写入的原生原子后端",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*sources, _SHARED_WRITE_CONTRACT),
        )

    observed_problem = observed_write_signature_required_problem(request.observed_context)
    if observed_problem is not None:
        return OperationExecution(
            outcome="unavailable",
            summary=observed_problem,
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
            gaps=({"summary": observed_problem, "scope": list(requested), "source_refs": [_CONTRACTS[mode]]},),
        )
    try:
        application = _apply_core_workcase_write(
            mode,
            domain,
            boundary,
            schemas,
            schema,
            context.event_at,
            request.observed_context,
        )
    except FactCoordinationUnavailable as error:
        return _coordination_unavailable(
            mode,
            error,
            domain,
            run,
            sources,
            diagnostic_profile=request.response_profile == "diagnostic",
        )

    failure = _application_failure(
        mode,
        application,
        domain,
        run,
        sources,
        boundary,
        context.event_at,
    )
    if failure is not None:
        return _coordination_preserved_result_overlay(
            failure,
            application,
            requested,
            diagnostic_profile=request.response_profile == "diagnostic",
        )
    before = getattr(application, "current", None)
    after = getattr(application, "readback", None)
    if not isinstance(before, FactReadResult) or not isinstance(after, FactReadResult):
        return OperationExecution(
            outcome="error",
            summary="WorkCase 专属事务没有返回可回读的 before/after",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*sources, _IMPLEMENTATION_SOURCE),
        )
    no_change = getattr(application, "status", None) == "no_change"
    coordination_release_uncertain = bool(getattr(application, "coordination_release_uncertain", False))
    working_tree_source = _working_tree_source(
        boundary,
        after.canonical_path,
        context.event_at,
    )
    result = _result(before, after, boundary.governed_project_id, reference.object_id)
    if no_change:
        return OperationExecution(
            outcome="no_change",
            summary="完整 after 与当前 WorkCase 相同，未重写目标",
            result=result,
            requested_scope=requested,
            completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(
                *sources,
                working_tree_source,
                *((_SHARED_WRITE_CONTRACT,) if coordination_release_uncertain else ()),
                _IMPLEMENTATION_SOURCE,
            ),
            gaps=(_coordination_release_gap(requested, committed=False),) if coordination_release_uncertain else (),
            verification=(
                {
                    "check": "当前对象指纹匹配且完整 after 与 before 相同",
                    "status": "passed",
                    "scope": list(requested),
                    "evidence": [working_tree_source, _CONTRACTS[mode]],
                },
            ),
            diagnostics=(_coordination_release_diagnostic(committed=False),)
            if coordination_release_uncertain and request.response_profile == "diagnostic"
            else (),
            follow_up=(_coordination_release_follow_up(requested) if coordination_release_uncertain else None),
        )
    replacement = getattr(application, "replacement_result", None)
    return post_write_integrity_audit(
        OperationExecution(
        outcome="ok",
        summary="WorkCase 已完成专属完整 after 校验、CAS 替换和写后回读",
        result=result,
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=(
            *sources,
            working_tree_source,
            *((_SHARED_WRITE_CONTRACT,) if coordination_release_uncertain else ()),
            _IMPLEMENTATION_SOURCE,
        ),
        gaps=(_coordination_release_gap(requested, committed=True),) if coordination_release_uncertain else (),
        changes=(
            {
                "summary": "已原子更新 WorkCase 当前完整快照",
                "status": "updated",
                "target": reference.to_json(),
                "source_refs": [working_tree_source],
            },
        ),
        verification=(
            {
                "check": (
                    "完整 after 的结构与转换机械检查、CAS 与写后回读已通过"
                    if replacement is None
                    else (
                        "完整 after 的结构与转换机械检查、CAS 与写后回读已通过；"
                        f"namespace={replacement.namespace_state}"
                    )
                ),
                "status": "passed",
                "scope": list(requested),
                "evidence": [working_tree_source, _CONTRACTS[mode]],
            },
        ),
        diagnostics=(_coordination_release_diagnostic(committed=True),)
        if coordination_release_uncertain and request.response_profile == "diagnostic"
        else (),
        follow_up=(_coordination_release_follow_up(requested) if coordination_release_uncertain else None),
    ),
        boundary=boundary,
        schemas=schemas,
        audit_contract=_INTEGRITY_CONTRACT,
    )


def _check_availability(
    mode: WorkCaseWriteMode,
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain = _validated_request(mode, request, context)
    requested = domain.fact_ref.to_json()
    if not native_atomic_fact_writes_supported():
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前平台没有启用 WorkCase 写入的原生原子后端",
                    "scope": [requested],
                    "source_refs": [_SHARED_WRITE_CONTRACT],
                },
            ),
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
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    current = _current_read(boundary, schemas, domain.fact_ref.object_id)
    if (
        current.check_status != "mechanically_valid"
        or current.content_fingerprint != domain.expected_content_fingerprint
    ):
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前对象不可读取、不能进入该操作或请求指纹已过期",
                    "scope": [requested],
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    return AvailabilityEvaluation(availability="available_for_request", available_scope=(requested,))


def _update_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("update", request, repository, context)


def _close_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("close", request, repository, context)


def _begin_termination_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("begin_termination", request, repository, context)


def _complete_termination_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("complete_termination", request, repository, context)


def _correct_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("correct", request, repository, context)


def _update_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("update", request, repository, context)


def _close_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("close", request, repository, context)


def _begin_termination_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("begin_termination", request, repository, context)


def _complete_termination_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("complete_termination", request, repository, context)


def _correct_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("correct", request, repository, context)


UPDATE_WORKCASE_IMPLEMENTATION = OperationImplementation(
    required_inputs=UPDATE_REQUIRED_INPUTS,
    optional_inputs=UPDATE_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["update"]),
    check_availability=_update_availability,
    call=_update_call,
)
BEGIN_WORKCASE_TERMINATION_IMPLEMENTATION = OperationImplementation(
    required_inputs=BEGIN_TERMINATION_REQUIRED_INPUTS,
    optional_inputs=BEGIN_TERMINATION_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["begin_termination"]),
    check_availability=_begin_termination_availability,
    call=_begin_termination_call,
)
COMPLETE_WORKCASE_TERMINATION_IMPLEMENTATION = OperationImplementation(
    required_inputs=COMPLETE_TERMINATION_REQUIRED_INPUTS,
    optional_inputs=COMPLETE_TERMINATION_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["complete_termination"]),
    check_availability=_complete_termination_availability,
    call=_complete_termination_call,
)
CLOSE_WORKCASE_IMPLEMENTATION = OperationImplementation(
    required_inputs=CLOSE_REQUIRED_INPUTS,
    optional_inputs=CLOSE_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["close"]),
    check_availability=_close_availability,
    call=_close_call,
)
CORRECT_CLOSED_WORKCASE_IMPLEMENTATION = OperationImplementation(
    required_inputs=CORRECT_CLOSED_REQUIRED_INPUTS,
    optional_inputs=CORRECT_CLOSED_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["correct"]),
    check_availability=_correct_availability,
    call=_correct_call,
)


__all__ = [
    "BEGIN_TERMINATION_OPERATION_KEY",
    "BEGIN_WORKCASE_TERMINATION_IMPLEMENTATION",
    "CLOSE_OPERATION_KEY",
    "CLOSE_WORKCASE_IMPLEMENTATION",
    "CORRECT_CLOSED_OPERATION_KEY",
    "CORRECT_CLOSED_WORKCASE_IMPLEMENTATION",
    "COMPLETE_TERMINATION_OPERATION_KEY",
    "COMPLETE_WORKCASE_TERMINATION_IMPLEMENTATION",
    "UPDATE_OPERATION_KEY",
    "UPDATE_WORKCASE_IMPLEMENTATION",
]
