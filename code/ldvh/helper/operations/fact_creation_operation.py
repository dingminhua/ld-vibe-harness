"""Prepare AI-fillable fact drafts and atomically create validated fact objects."""

from __future__ import annotations

from collections.abc import Mapping
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
from ldvh.facts.creation_application import FactCreationCommand, create_fact_object
from ldvh.facts.models import FactIssue
from ldvh.facts.schema import project_fact_schemas
from ldvh.filesystem import durable_writes_enabled
from ldvh.governance.models import ObjectStatus
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_creation_request import (
    CREATE_OPTIONAL_INPUTS,
    CREATE_REQUIRED_INPUTS,
    PREPARE_OPTIONAL_INPUTS,
    PREPARE_REQUIRED_INPUTS,
    FactCreateRequest,
    FactDraftRequest,
    parse_create_request,
    parse_draft_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

PREPARE_OPERATION_KEY = "prepare-fact-object-draft"
CREATE_OPERATION_KEY = "create-fact-object"
_PREPARE_CONTRACT = source_reference("rule", "fact-model-foundation::11.3 事实对象草案准备输入与结果")
_CREATE_CONTRACT = source_reference("rule", "fact-model-foundation::11.4 事实对象受控创建输入与结果")
_SHARED_WRITE_CONTRACT = source_reference("rule", "fact-model-foundation::11.8 共享单对象受控写事务")
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation",
    "code/ldvh/helper/operations/fact_creation_operation.py",
)
_MANAGED_FIELDS = frozenset({"object_id", "fact_type_key", "created_at", "updated_at"})


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _governance(domain: FactDraftRequest | FactCreateRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _boundary(run: GovernanceResolutionRun) -> CreationBoundary | None:
    if run.result is None or run.technical_non_completions or len(run.completed_scope) != len(run.requested_scope):
        return None
    resolutions = run.result.object_resolutions
    if len(resolutions) != len(run.requested_scope) or any(
        item.status is not ObjectStatus.GOVERNED for item in resolutions
    ):
        return None
    project_ids = {item.governed_project_id for item in resolutions}
    roots = {item.git_worktree_root for item in resolutions}
    common_dirs = {item.git_common_dir for item in resolutions}
    if (
        len(project_ids) != 1
        or len(roots) != 1
        or len(common_dirs) != 1
        or None in project_ids
        or None in roots
        or None in common_dirs
    ):
        return None
    return CreationBoundary(
        next(iter(project_ids)),  # type: ignore[arg-type]
        Path(next(iter(roots))),  # type: ignore[arg-type]
        Path(next(iter(common_dirs))),  # type: ignore[arg-type]
    )


def _boundary_execution(
    run: GovernanceResolutionRun,
    requested: tuple[object, ...],
    summary: str,
) -> OperationExecution:
    return OperationExecution(
        outcome="unavailable",
        summary=summary,
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=None if run.result is None else run.result.to_json(),
        sources=tuple(_plain(source) for source in run.sources) + (_IMPLEMENTATION_SOURCE,),
        gaps=(
            {
                "summary": "管辖输入未形成同一项目、同一实际 worktree 和 common-dir 的唯一边界",
                "scope": list(requested),
                "source_refs": [_plain(source) for source in run.sources],
            },
        ),
    )


def _validated_draft(request: CommonRequest, context: OperationExecutionContext) -> FactDraftRequest:
    parsed = parse_draft_request(request, context)
    if not isinstance(parsed.request, FactDraftRequest):
        raise OperationRequestError(parsed.problems, sources=(_PREPARE_CONTRACT,))
    return parsed.request


def _validated_create(request: CommonRequest, context: OperationExecutionContext) -> FactCreateRequest:
    parsed = parse_create_request(request, context)
    if not isinstance(parsed.request, FactCreateRequest):
        raise OperationRequestError(parsed.problems, sources=(_CREATE_CONTRACT,))
    return parsed.request


def _prepare_execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_draft(request, context)
    requested = ({"governed_project_id": domain.governed_project_id, "fact_type_key": domain.fact_type_key},)
    run = _governance(domain)
    boundary = _boundary(run)
    if boundary is None:
        return _boundary_execution(run, requested, "当前管辖结果不能形成唯一事实对象草案边界")
    if boundary.governed_project_id != domain.governed_project_id:
        return OperationExecution(
            outcome="rejected",
            summary="请求项目与实际管辖项目不一致",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=tuple(_plain(source) for source in run.sources) + (_PREPARE_CONTRACT,),
            gaps=(
                {
                    "summary": "governed_project_id 与实际管辖结果不一致",
                    "scope": list(requested),
                    "source_refs": [_PREPARE_CONTRACT],
                },
            ),
        )
    schema = project_fact_schemas(repository).get(domain.fact_type_key)
    layout = LAYOUTS[domain.fact_type_key]
    candidate = candidate_object_id(boundary, layout)
    if schema is None or candidate is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前来源、Git 身份或 allocator 不能形成可信草案",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=tuple(_plain(source) for source in run.sources) + (_PREPARE_CONTRACT,),
            gaps=(
                {
                    "summary": "派生 Schema、linked worktree 扫描或 allocator 状态不可用",
                    "scope": list(requested),
                    "source_refs": [_PREPARE_CONTRACT],
                },
            ),
        )
    fingerprint = schema_fingerprint(schema)
    basis = {
        "governed_project_id": boundary.governed_project_id,
        "fact_type_key": domain.fact_type_key,
        "candidate_object_id": candidate,
        "schema_fingerprint": fingerprint,
        "worktree_fingerprint": worktree_fingerprint(boundary),
    }
    result = {
        **basis,
        "candidate_canonical_path": layout.canonical_path(candidate),
        "carrier": layout.carrier,
        "managed_fields": sorted(_MANAGED_FIELDS),
        "field_contracts": [
            {
                "field_path": field.path,
                "json_type": field.json_type,
                "presence": field.presence,
                "constraint_ref": field.constraint_ref,
            }
            for field in schema.fields
        ],
    }
    sources = tuple(_plain(source) for source in run.sources) + (_PREPARE_CONTRACT, _IMPLEMENTATION_SOURCE)
    return OperationExecution(
        outcome="ok",
        summary="已生成无事实源副作用的 AI 待填写草案依据",
        result=result,
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=sources,
        verification=(
            {
                "check": "当前派生 Schema、候选身份和 worktree 绑定已形成",
                "status": "passed",
                "scope": list(requested),
                "evidence": list(sources),
            },
        ),
    )


def _content(
    domain: FactCreateRequest,
    layout_carrier: str,
) -> tuple[dict[str, Any] | None, str | None, tuple[str, ...]]:
    problems: list[str] = []
    if layout_carrier == "markdown":
        if set(domain.fact_object) != {"frontmatter", "body"}:
            return None, None, ("Study fact_object 必须精确包含 frontmatter 与 body",)
        frontmatter = domain.fact_object.get("frontmatter")
        body = domain.fact_object.get("body")
        if not isinstance(frontmatter, dict):
            problems.append("Study fact_object.frontmatter 必须是 object")
        if not isinstance(body, str) or not body.strip():
            problems.append("Study fact_object.body 必须是非空 string")
        return (
            (dict(frontmatter) if isinstance(frontmatter, dict) else None),
            body if isinstance(body, str) else None,
            tuple(problems),
        )
    return dict(domain.fact_object), None, ()


def _issue_gap(issues: tuple[FactIssue, ...], scope: object) -> dict[str, Any]:
    summary = "; ".join(f"{issue.field_path + ': ' if issue.field_path else ''}{issue.summary}" for issue in issues)
    return {
        "summary": summary or "项目级检查所需事实源当前不可用",
        "scope": [scope],
        "source_refs": [_CREATE_CONTRACT],
    }


def _coordination_unavailable(
    error: FactCoordinationUnavailable,
    requested: tuple[object, ...],
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
        summary="事实对象共同协调锁当前不可用，未创建对象或推进 allocator",
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
            "summary": "恢复共同协调根访问后重新读取当前范围并重试",
            "required_inputs": [],
            "required_human_decisions": [],
            "resume_conditions": [
                {
                    "summary": "git common-dir 的 LDVH 协调根允许创建或打开锁并取得排他锁",
                    "scope": list(requested),
                    "source_refs": [_SHARED_WRITE_CONTRACT],
                }
            ],
            "suggested_operations": [],
        },
    )


def _create_execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_create(request, context)
    basis = domain.draft_basis
    requested = (basis.to_json(),)
    run = _governance(domain)
    boundary = _boundary(run)
    if boundary is None:
        return _boundary_execution(run, requested, "当前管辖结果不能形成唯一事实对象创建边界")
    request_sources = tuple(_plain(source) for source in run.sources) + (_CREATE_CONTRACT,)
    schemas = project_fact_schemas(repository)
    schema = schemas.get(basis.fact_type_key)
    if (
        boundary.governed_project_id != basis.governed_project_id
        or worktree_fingerprint(boundary) != basis.worktree_fingerprint
        or schema is None
        or schema_fingerprint(schema) != basis.schema_fingerprint
    ):
        return OperationExecution(
            outcome="rejected",
            summary="草案依据已经过期或不属于当前项目、worktree 与 Schema",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(
                {
                    "summary": "必须重新调用 prepare-fact-object-draft",
                    "scope": list(requested),
                    "source_refs": [_CREATE_CONTRACT],
                },
            ),
        )
    supplied, body, content_problems = _content(domain, LAYOUTS[basis.fact_type_key].carrier)
    if supplied is None or content_problems:
        raise OperationRequestError(content_problems, sources=(_CREATE_CONTRACT,))
    managed = sorted(set(supplied) & _MANAGED_FIELDS)
    if managed:
        raise OperationRequestError(
            (f"AI 不得填写 Code 托管字段: {', '.join(managed)}",),
            sources=request_sources,
        )
    initial_statuses = LAYOUTS[basis.fact_type_key].initial_statuses
    if supplied.get("status") not in initial_statuses:
        rendered_statuses = ", ".join(sorted(initial_statuses))
        return OperationExecution(
            outcome="rejected",
            summary="事实对象初始状态不符合当前类型来源",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(
                {
                    "summary": f"{basis.fact_type_key} 初始状态必须属于: {rendered_statuses}",
                    "scope": list(requested),
                    "source_refs": [_CREATE_CONTRACT],
                },
            ),
        )
    try:
        creation = create_fact_object(
            FactCreationCommand(
                boundary=boundary,
                fact_type_key=basis.fact_type_key,
                schemas=schemas,
                schema=schema,
                requested_candidate_id=basis.candidate_object_id,
                supplied=supplied,
                body=body,
            ),
            observed_at=context.event_at,
        )
    except FactCoordinationUnavailable as error:
        return _coordination_unavailable(
            error,
            requested,
            run,
            request_sources,
            diagnostic_profile=request.response_profile == "diagnostic",
        )
    if creation.status == "candidate_unavailable":
        return OperationExecution(
            outcome="unavailable",
            summary="创建前项目级机械检查未能完成",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(_issue_gap(creation.issues, requested[0]),),
        )
    if creation.status == "candidate_rejected":
        return OperationExecution(
            outcome="rejected",
            summary="AI 填写内容未通过当前事实类型机械检查",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(_issue_gap(creation.issues, requested[0]),),
        )
    if creation.status == "durability_unavailable":
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台尚未获准以 file-only 耐久等级写入事实对象",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(
                {
                    "summary": (
                        "未创建 allocator 状态或事实文件：当前 Windows 实现未满足 allocator 及相应耐久/"
                        "并发保障；需先说明受影响保障，并由 Human 决定是否接受具体残留风险"
                    ),
                    "scope": list(requested),
                    "source_refs": [_CREATE_CONTRACT],
                },
            ),
        )
    if creation.status in {"final_rejected", "final_unavailable"}:
        assert creation.actual_id is not None
        return OperationExecution(
            outcome="unavailable" if creation.status == "final_unavailable" else "rejected",
            summary="最终身份分配后机械前置条件发生变化，未创建对象",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            changes=(
                {
                    "summary": "顺序编号已消耗但未创建对象；编号不会复用",
                    "status": "allocation-consumed",
                    "target": creation.actual_id,
                    "source_refs": [_CREATE_CONTRACT],
                },
            ),
            gaps=(_issue_gap(creation.issues, requested[0]),),
        )
    if creation.status == "allocation_unavailable":
        write = creation.creation_result
        return OperationExecution(
            outcome="unavailable",
            summary="无法在受控重试范围内取得可原子创建的事实对象身份",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            changes=(
                {
                    "summary": (
                        "allocator 已推进；文件系统 namespace 提交状态不确定"
                        if write is not None and write.namespace_state == "uncertain"
                        else "allocator 可能已推进；没有创建事实对象"
                    ),
                    "status": (
                        "namespace-uncertain"
                        if write is not None and write.namespace_state == "uncertain"
                        else "allocation-consumed"
                        if creation.allocation_consumed
                        else "not-created"
                    ),
                    "target": basis.fact_type_key,
                    "source_refs": [_CREATE_CONTRACT],
                },
            ),
        )
    layout = LAYOUTS[basis.fact_type_key]
    if creation.status == "readback_failed":
        assert creation.actual_id is not None
        rollback = creation.rollback_result
        assert rollback is not None
        rolled_back = rollback.outcome == "removed" and rollback.namespace_state == "committed"
        return OperationExecution(
            outcome="error",
            summary="写后回读未通过；已回滚" if rolled_back else "写后回读未通过且无法安全回滚",
            requested_scope=requested,
            completed_scope=(),
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*request_sources, _IMPLEMENTATION_SOURCE),
            changes=(
                {
                    "summary": "新对象已删除回滚" if rolled_back else "新对象仍残留且未完成验证",
                    "status": "rolled-back" if rolled_back else "rollback-failed",
                    "target": layout.canonical_path(creation.actual_id),
                    "source_refs": [_CREATE_CONTRACT],
                },
            ),
            gaps=(_issue_gap(creation.issues, requested[0]),),
        )

    assert creation.status == "created"
    actual_id = creation.actual_id
    read = creation.read
    creation_result = creation.creation_result
    assert actual_id is not None
    assert read is not None
    assert creation_result is not None

    actual_ref = {
        "governed_project_id": boundary.governed_project_id,
        "fact_type_key": basis.fact_type_key,
        "object_id": actual_id,
    }
    working_tree_source = {
        "kind": "working_tree",
        "locator": (boundary.worktree_root / layout.canonical_path(actual_id)).as_posix(),
        "observed_at": context.event_at,
        "details": {"view": "Working Tree"},
    }
    sources = (
        *tuple(_plain(source) for source in run.sources),
        *tuple(_plain(source) for source in domain.authorization_reference),
        _CREATE_CONTRACT,
        working_tree_source,
        _IMPLEMENTATION_SOURCE,
    )
    assert read.fields is not None
    assert creation_result is not None
    result_object: dict[str, Any] = (
        {"frontmatter": read.fields, "body": read.body or ""} if layout.carrier == "markdown" else read.fields
    )
    return OperationExecution(
        outcome="ok",
        summary="事实对象已由 Code 最终分配身份、原子创建并完成写后回读",
        result={
            "requested_candidate_id": basis.candidate_object_id,
            "actual_ref": actual_ref,
            "canonical_path": layout.canonical_path(actual_id),
            "carrier": layout.carrier,
            "fact_object": result_object,
        },
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=sources,
        changes=(
            {
                "summary": (
                    "已原子创建并回读事实对象"
                    f"（durability={creation_result.durability}, cleanup={creation_result.cleanup}）"
                ),
                "status": "created",
                "target": actual_ref,
                "source_refs": [working_tree_source],
            },
        ),
        verification=(
            {
                "check": (
                    "写后读取、派生 Schema、身份、引用和关系机械检查已通过；"
                    f"namespace={creation_result.namespace_state}, durability={creation_result.durability}, "
                    f"cleanup={creation_result.cleanup}"
                ),
                "status": "passed",
                "scope": [actual_ref],
                "evidence": [working_tree_source, _CREATE_CONTRACT],
            },
        ),
    )


def _availability_from_execution(execution: OperationExecution) -> AvailabilityEvaluation:
    if execution.outcome in {"ok", "no_change"}:
        availability = "available_for_request"
    elif execution.completed_scope:
        availability = "partially_available"
    else:
        availability = "unavailable_for_request"
    return AvailabilityEvaluation(
        availability=availability,
        available_scope=execution.completed_scope,
        unavailable_scope=execution.not_completed_scope,
        gaps=execution.gaps,
    )


def _prepare_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _availability_from_execution(_prepare_execute(request, repository, context))


def _create_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain = _validated_create(request, context)
    if not durable_writes_enabled():
        requested = (domain.draft_basis.to_json(),)
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=requested,
            gaps=(
                {
                    "summary": "当前平台尚未获准以 file-only 耐久等级写入事实对象",
                    "scope": list(requested),
                    "source_refs": [_CREATE_CONTRACT],
                },
            ),
        )
    run = _governance(domain)
    boundary = _boundary(run)
    schemas = project_fact_schemas(repository)
    schema = schemas.get(domain.draft_basis.fact_type_key)
    if (
        boundary is None
        or boundary.governed_project_id != domain.draft_basis.governed_project_id
        or worktree_fingerprint(boundary) != domain.draft_basis.worktree_fingerprint
        or schema is None
        or schema_fingerprint(schema) != domain.draft_basis.schema_fingerprint
    ):
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(domain.draft_basis.to_json(),),
            gaps=(
                {
                    "summary": "当前请求的草案、管辖、worktree 或 Schema 前置条件不成立",
                    "scope": [domain.draft_basis.to_json()],
                    "source_refs": [_CREATE_CONTRACT],
                },
            ),
        )
    return AvailabilityEvaluation(
        availability="available_for_request",
        available_scope=(domain.draft_basis.to_json(),),
    )


PREPARE_FACT_DRAFT_IMPLEMENTATION = OperationImplementation(
    required_inputs=PREPARE_REQUIRED_INPUTS,
    optional_inputs=PREPARE_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _PREPARE_CONTRACT),
    check_availability=_prepare_availability,
    call=_prepare_execute,
)

CREATE_FACT_OBJECT_IMPLEMENTATION = OperationImplementation(
    required_inputs=CREATE_REQUIRED_INPUTS,
    optional_inputs=CREATE_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CREATE_CONTRACT),
    check_availability=_create_availability,
    call=_create_execute,
)


__all__ = [
    "CREATE_FACT_OBJECT_IMPLEMENTATION",
    "CREATE_OPERATION_KEY",
    "PREPARE_FACT_DRAFT_IMPLEMENTATION",
    "PREPARE_OPERATION_KEY",
]
