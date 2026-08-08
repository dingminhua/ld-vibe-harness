"""Conditionally replace one exact, mechanically valid fact object."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, FactCoordinationUnavailable
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema, project_fact_schemas
from ldvh.facts.update_application import FactUpdateCommand, FactUpdateResult, apply_fact_update
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
from ldvh.helper.operations.fact_operation_support import (
    plain,
    post_write_integrity_audit,
    reading_boundary,
)
from ldvh.helper.operations.fact_update_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    FactUpdateRequest,
    parse_fact_update_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "update-fact-object"
_CONTRACT = source_reference(
    "rule",
    "fact-model-foundation::11.7 事实对象单对象 CAS 更新输入与结果",
)
_SHARED_WRITE_CONTRACT = source_reference("rule", "fact-model-foundation::11.8 共享单对象受控写事务")
_INTEGRITY_CONTRACT = source_reference("rule", "fact-model-foundation::11.9-11.10 事实写后独立完整性审计")
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation",
    "code/ldvh/helper/operations/fact_update_operation.py",
)
_MANAGED_FIELDS = frozenset({"object_id", "fact_type_key", "created_at", "updated_at"})


def _validated_request(request: CommonRequest, context: OperationExecutionContext) -> FactUpdateRequest:
    parsed = parse_fact_update_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACT,))
    if parsed.request.fact_ref.fact_type_key == "workcase":
        raise OperationRequestError(
            (
                "通用 update-fact-object 不接受 WorkCase；活动期更新、关闭与终态更正必须分别使用 "
                "update-workcase、close-workcase 与 correct-closed-workcase",
            ),
            sources=(_CONTRACT,),
        )
    return parsed.request


def _governance(domain: FactUpdateRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _boundary(run: GovernanceResolutionRun) -> CreationBoundary | None:
    resolved = reading_boundary(run)
    return CreationBoundary(*resolved) if resolved is not None else None


def _fact_object(read: FactReadResult) -> dict[str, Any]:
    assert read.fields is not None
    return {"frontmatter": read.fields, "body": read.body or ""} if read.carrier == "markdown" else read.fields


def _content(
    domain: FactUpdateRequest,
    carrier: str,
) -> tuple[dict[str, Any] | None, str | None, tuple[str, ...]]:
    if carrier == "markdown":
        if set(domain.fact_object) != {"frontmatter", "body"}:
            return None, None, ("Study fact_object 必须精确包含 frontmatter 与 body",)
        frontmatter = domain.fact_object.get("frontmatter")
        body = domain.fact_object.get("body")
        problems: list[str] = []
        if not isinstance(frontmatter, dict):
            problems.append("Study fact_object.frontmatter 必须是 object")
        if not isinstance(body, str) or not body.strip():
            problems.append("Study fact_object.body 必须是非空 string")
        return (
            dict(frontmatter) if isinstance(frontmatter, dict) else None,
            body if isinstance(body, str) else None,
            tuple(problems),
        )
    return dict(domain.fact_object), None, ()


def _issue_summary(issues: tuple[FactIssue, ...]) -> str:
    return "; ".join(f"{issue.field_path + ': ' if issue.field_path else ''}{issue.summary}" for issue in issues)


def _current_read(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    fact_type_key: str,
    object_id: str,
) -> FactReadResult:
    layout = LAYOUTS[fact_type_key]
    schema = schemas[fact_type_key]
    read = read_fact_object(
        boundary.worktree_root,
        layout,
        schema,
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
    key = (fact_type_key, object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index, (key,))
    return index.cache.get(key, read)


def _working_tree_source(boundary: CreationBoundary, canonical_path: str, event_at: str) -> dict[str, Any]:
    return {
        "kind": "working_tree",
        "locator": (boundary.worktree_root / canonical_path).as_posix(),
        "observed_at": event_at,
        "details": {"view": "Working Tree"},
    }


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
            f"事实对象更新领域结果（status={status}）已在共同锁释放前形成并保留；"
            "共同锁释放未能确认，"
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
    namespace_state = getattr(rollback, "namespace_state", None)
    if namespace_state == "uncertain":
        return "条件回滚在文件命名空间（namespace）中的生效情况无法确认"
    if namespace_state == "not_committed":
        if getattr(rollback, "outcome", None) == "conflict":
            return "条件回滚发生冲突，确认未在文件命名空间（namespace）生效"
        return "条件回滚确认未在文件命名空间（namespace）生效"
    return "条件回滚未完成"


def _result(read: FactReadResult, project_id: str, fact_type_key: str, object_id: str, previous: str) -> dict[str, Any]:
    assert read.content_fingerprint is not None
    return {
        "actual_ref": {
            "governed_project_id": project_id,
            "fact_type_key": fact_type_key,
            "object_id": object_id,
        },
        "canonical_path": read.canonical_path,
        "carrier": read.carrier,
        "previous_content_fingerprint": previous,
        "content_fingerprint": read.content_fingerprint,
        "fact_object": _fact_object(read),
    }


def _rejected(
    domain: FactUpdateRequest,
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
    domain: FactUpdateRequest,
    run: GovernanceResolutionRun,
    requested: tuple[dict[str, str], ...],
    sources: tuple[dict[str, Any], ...],
    boundary: CreationBoundary,
    event_at: str,
) -> OperationExecution | None:
    governance = run.result.to_json() if run.result else None
    if result.status in {"updated", "no_change"}:
        return None
    if result.status == "invalid_request":
        return OperationExecution(
            outcome="invalid_request",
            summary="通用事实对象更新请求不适用于目标类型",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": _issue_summary(result.issues),
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    if result.status == "durability_unavailable":
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台没有启用公共事实更新的原生原子后端",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": (
                        "未创建锁状态或替换事实文件：当前平台没有启用同时承接锁与条件替换的原生原子后端"
                    ),
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    if result.status in {"current_rejected", "current_unavailable"}:
        return OperationExecution(
            outcome="unavailable" if result.status == "current_unavailable" else "rejected",
            summary="当前对象未形成可更新的 mechanically valid 快照",
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
        return _rejected(
            domain,
            run,
            "事实对象内容指纹已经过期",
            "必须重新调用 read-fact-objects 并基于最新完整对象形成目标内容",
            sources,
        )
    if result.status == "event_time_not_successor":
        return _rejected(
            domain,
            run,
            "本次操作时间不能形成 updated_at 严格后继",
            _issue_summary(result.issues),
            sources,
        )
    if result.status in {"candidate_rejected", "candidate_unavailable"}:
        return OperationExecution(
            outcome="unavailable" if result.status == "candidate_unavailable" else "rejected",
            summary="完整目标未通过更新前机械检查",
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
        replacement = result.replacement_result
        assert replacement is not None
        return OperationExecution(
            outcome="rejected" if result.status == "replacement_conflict" else "unavailable",
            summary=("原子替换前对象发生变化" if result.status == "replacement_conflict" else "原子替换技术条件不成立"),
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=(*sources, _IMPLEMENTATION_SOURCE),
            gaps=(
                {
                    "summary": (
                        "namespace 提交状态不确定；必须重新精确读取当前对象"
                        if replacement.namespace_state == "uncertain"
                        else "未提交写入；重新精确读取当前对象后再形成更新请求"
                    ),
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    assert result.status == "readback_failed"
    rollback = result.rollback_result
    assert rollback is not None
    rolled_back = rollback.outcome == "replaced" and rollback.namespace_state == "committed"
    residual = result.residual_readback
    residual_source = (
        _residual_working_tree_source(boundary, residual, event_at) if isinstance(residual, FactReadResult) else None
    )
    current = result.current
    rollback_failure_prefix = _rollback_failure_prefix(rollback)
    if rolled_back:
        change_summary = "已恢复更新前载体"
    elif not isinstance(residual, FactReadResult) or residual.check_status == "unavailable":
        change_summary = f"{rollback_failure_prefix}；实际事实对象载体的残留状态无法确认"
    elif residual.raw_text == result.candidate_text:
        change_summary = f"{rollback_failure_prefix}；当前重新读取观察到的实际事实对象载体完整字节内容与本次新载体一致"
    elif isinstance(current, FactReadResult) and residual.raw_text == current.raw_text:
        change_summary = f"{rollback_failure_prefix}；当前重新读取观察到的实际事实对象载体完整字节内容与更新前载体一致"
    elif residual.check_status == "mechanically_valid":
        change_summary = f"{rollback_failure_prefix}；当前重新读取观察到的实际事实对象载体是另一机械有效版本"
    elif residual.check_status == "not_found":
        change_summary = f"{rollback_failure_prefix}；当前重新读取确认实际事实对象载体的预期位置不存在"
    elif residual.raw_text is not None:
        change_summary = f"{rollback_failure_prefix}；当前实际事实对象载体已安全完整读取，但对象未通过机械检查"
    else:
        change_summary = (
            f"{rollback_failure_prefix}；当前实际事实对象载体未能安全完整读取，机械检查未通过（状态为 `invalid`）"
        )
    residual_unknown = not rolled_back and (
        not isinstance(residual, FactReadResult) or residual.check_status == "unavailable"
    )
    residual_refs = () if residual_source is None else (residual_source,)
    residual_gap = (
        (
            {
                "summary": "条件回滚后的实际事实对象载体无法确认",
                "scope": list(requested),
                "source_refs": [_CONTRACT],
            },
        )
        if residual_unknown
        else ()
    )
    residual_verification = (
        (
            {
                "check": "条件回滚后重新精确读取并机械检查实际事实对象载体",
                "status": (
                    "unavailable"
                    if not isinstance(residual, FactReadResult) or residual.check_status == "unavailable"
                    else "passed"
                    if residual.check_status == "mechanically_valid"
                    else "failed"
                ),
                "scope": list(requested),
                "evidence": [*residual_refs, _CONTRACT],
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
                "source_refs": [_CONTRACT, *residual_refs],
            },
        ),
        gaps=(
            {
                "summary": _issue_summary(result.issues) or "写后项目级机械检查未完成",
                "scope": list(requested),
                "source_refs": [_CONTRACT],
            },
            *residual_gap,
        ),
        verification=residual_verification,
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
            "counter_unchanged": True,
        },
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    return OperationExecution(
        outcome="unavailable",
        summary="事实对象共同协调锁当前不可用，未更新目标",
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
                    "summary": "重新精确读取当前事实对象",
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
            summary="当前管辖结果不能形成唯一事实对象更新边界",
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
    schema = schemas.get(reference.fact_type_key)
    if schema is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前来源未形成目标类型的完整派生 Schema",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=({"summary": "目标 Schema 不可用", "scope": list(requested), "source_refs": [_CONTRACT]},),
        )
    layout = LAYOUTS[reference.fact_type_key]
    supplied, body, content_problems = _content(domain, layout.carrier)
    if supplied is None or content_problems:
        raise OperationRequestError(content_problems, sources=(_CONTRACT,))
    managed = sorted(set(supplied) & _MANAGED_FIELDS)
    if managed:
        raise OperationRequestError(
            (f"AI 不得填写 Code 托管字段: {', '.join(managed)}",),
            sources=(_CONTRACT,),
        )
    supplied = inject_observed_write_signature(supplied, request.observed_context)
    if not native_atomic_fact_writes_supported():
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台没有启用公共事实更新的原生原子后端",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(
                {
                    "summary": (
                        "未创建锁状态或替换事实文件：当前平台没有启用同时承接锁与条件替换的原生原子后端"
                    ),
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )

    try:
        application = apply_fact_update(
            FactUpdateCommand(
                boundary=boundary,
                fact_type_key=reference.fact_type_key,
                object_id=reference.object_id,
                schemas=schemas,
                schema=schema,
                expected_content_fingerprint=domain.expected_content_fingerprint,
                supplied=supplied,
                body=body,
                event_at=context.event_at,
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
    failure = _application_failure(
        application,
        domain,
        run,
        requested,
        request_sources,
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
    readback = application.readback
    assert readback is not None and readback.content_fingerprint is not None
    coordination_release_uncertain = application.coordination_release_uncertain
    if application.status == "no_change":
        working_tree_source = _working_tree_source(boundary, readback.canonical_path, context.event_at)
        sources = (
            *request_sources,
            working_tree_source,
            *((_SHARED_WRITE_CONTRACT,) if coordination_release_uncertain else ()),
            _IMPLEMENTATION_SOURCE,
        )
        return OperationExecution(
            outcome="no_change",
            summary="提交的完整目标与当前对象相同，未重写文件",
            result=_result(
                readback,
                boundary.governed_project_id,
                reference.fact_type_key,
                reference.object_id,
                readback.content_fingerprint,
            ),
            requested_scope=requested,
            completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
            gaps=(_coordination_release_gap(requested, committed=False),) if coordination_release_uncertain else (),
            verification=(
                {
                    "check": "当前完整目标与请求内容相同且内容指纹仍匹配",
                    "status": "passed",
                    "scope": list(requested),
                    "evidence": [working_tree_source, _CONTRACT],
                },
            ),
            diagnostics=(_coordination_release_diagnostic(committed=False),)
            if coordination_release_uncertain and request.response_profile == "diagnostic"
            else (),
            follow_up=(_coordination_release_follow_up(requested) if coordination_release_uncertain else None),
        )

    replacement = application.replacement_result
    assert replacement is not None
    working_tree_source = _working_tree_source(boundary, readback.canonical_path, context.event_at)
    sources = (
        *request_sources,
        working_tree_source,
        *((_SHARED_WRITE_CONTRACT,) if coordination_release_uncertain else ()),
        _IMPLEMENTATION_SOURCE,
    )
    return post_write_integrity_audit(
        OperationExecution(
        outcome="ok",
        summary="事实对象已完成单对象 CAS 替换和写后回读",
        result=_result(
            readback,
            boundary.governed_project_id,
            reference.fact_type_key,
            reference.object_id,
            domain.expected_content_fingerprint,
        ),
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=sources,
        gaps=(_coordination_release_gap(requested, committed=True),) if coordination_release_uncertain else (),
        changes=(
            {
                "summary": (
                    f"已原子替换并回读事实对象"
                ),
                "status": "updated",
                "target": reference.to_json(),
                "source_refs": [working_tree_source],
            },
        ),
        verification=(
            {
                "check": (
                    "旧内容指纹、完整目标、转换边界、原子替换和写后机械读取已通过；"
                    f"namespace={replacement.namespace_state}"
                ),
                "status": "passed",
                "scope": list(requested),
                "evidence": [working_tree_source, _CONTRACT],
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
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain = _validated_request(request, context)
    requested = domain.fact_ref.to_json()
    if not native_atomic_fact_writes_supported():
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前平台没有启用公共事实更新的原生原子后端",
                    "scope": [requested],
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    run = _governance(domain)
    boundary = _boundary(run)
    schemas = project_fact_schemas(repository)
    schema = schemas.get(domain.fact_ref.fact_type_key)
    if boundary is None or boundary.governed_project_id != domain.fact_ref.governed_project_id or schema is None:
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前请求的管辖、项目或 Schema 前置条件不成立",
                    "scope": [requested],
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    current = _current_read(
        boundary,
        schemas,
        domain.fact_ref.fact_type_key,
        domain.fact_ref.object_id,
    )
    if (
        current.check_status == "unavailable"
        or current.fields is None
        or current.content_fingerprint != domain.expected_content_fingerprint
    ):
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前对象不可更新或请求内容指纹已过期",
                    "scope": [requested],
                    "source_refs": [_CONTRACT],
                },
            ),
        )
    return AvailabilityEvaluation(availability="available_for_request", available_scope=(requested,))


FACT_UPDATE_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACT),
    check_availability=_check_availability,
    call=_execute,
)


__all__ = ["FACT_UPDATE_IMPLEMENTATION", "OPERATION_KEY"]
