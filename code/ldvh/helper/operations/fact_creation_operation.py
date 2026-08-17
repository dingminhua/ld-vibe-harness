"""Prepare AI-fillable fact drafts and atomically create validated fact objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    CreationBoundary,
    FactCoordinationUnavailable,
    schema_fingerprint,
    worktree_fingerprint,
)
from ldvh.facts.creation_application import FactCreationCommand, FactCreationResult, create_fact_object
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import project_fact_schemas
from ldvh.filesystem import native_atomic_fact_writes_supported
from ldvh.governance.models import ObjectStatus
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.governance.signature_guard import signature_governance_instance_collision
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
    parse_observed_write_signature,
)
from ldvh.helper.operations.fact_operation_support import (
    configuration_reading_boundaries,
    post_write_integrity_audit,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

PREPARE_OPERATION_KEY = "prepare-fact-object-draft"
CREATE_OPERATION_KEY = "create-fact-object"
_PREPARE_CONTRACT = source_reference("rule", "fact-model-foundation::11.3 事实对象草案准备输入与结果")
_CREATE_CONTRACT = source_reference("rule", "fact-model-foundation::11.4 事实对象受控创建输入与结果")
_SHARED_WRITE_CONTRACT = source_reference("rule", "fact-model-foundation::11.8 共享单对象受控写事务")
_INTEGRITY_CONTRACT = source_reference("rule", "fact-model-foundation::11.9-11.10 事实写后独立完整性审计")
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation",
    "code/ldvh/helper/operations/fact_creation_operation.py",
)
_MANAGED_FIELDS = frozenset({"object_uid", "object_id", "fact_type_key", "created_at", "updated_at"})
_FACT_TYPE_SOURCES = {
    "spark": "specs/20-Spark-火花.md",
    "workcase": "specs/21-WorkCase-工作项.md",
    "adr": "specs/22-ADR-决策.md",
    "pitfall": "specs/23-Pitfall-踩坑经验.md",
    "study": "specs/24-Study-研究报告.md",
}


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def inject_observed_write_signature(
    supplied: dict[str, Any],
    observed_context: dict[str, Any],
) -> dict[str, Any]:
    """Replace the newest change-log signature with one observed snapshot."""
    parsed = parse_observed_write_signature(observed_context)
    if parsed.problems or parsed.signature is None:
        return supplied
    change_log = supplied.get("change_log")
    if not isinstance(change_log, list) or not change_log or not isinstance(change_log[-1], dict):
        return supplied
    newest = dict(change_log[-1])
    newest["signature"] = parsed.signature.as_dict()
    newest.pop("session_id", None)
    return {**supplied, "change_log": [*change_log[:-1], newest]}


def signature_governance_collision_execution(
    run: GovernanceResolutionRun,
    observed_context: dict[str, Any],
    requested_scope: tuple[object, ...],
    sources: tuple[dict[str, Any], ...],
    *,
    diagnostic_profile: bool,
) -> OperationExecution | None:
    """Project the shared pure collision guard before any fact write side effect."""

    if run.result is None:
        return None
    parsed = parse_observed_write_signature(observed_context)
    if parsed.problems or parsed.signature is None:
        return None
    collision = signature_governance_instance_collision(
        run.result.governance_instance_name,
        parsed.signature,
    )
    if collision is None:
        return None
    gap = {
        "summary": collision.message,
        "scope": list(requested_scope),
        "source_refs": list(sources),
        "code": collision.code,
    }
    diagnostic = {
        "summary": collision.message,
        "details": {"stage": "signature_governance_guard", "code": collision.code},
        "source_refs": list(sources),
        "code": collision.code,
    }
    return OperationExecution(
        outcome="rejected",
        summary=collision.message,
        requested_scope=requested_scope,
        not_completed_scope=requested_scope,
        governance_resolution=run.result.to_json(),
        sources=sources,
        gaps=(gap,),
        diagnostics=(diagnostic,) if diagnostic_profile else (),
    )


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
    if schema is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前来源或 Git 身份不能形成可信草案",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=tuple(_plain(source) for source in run.sources) + (_PREPARE_CONTRACT,),
            gaps=(
                {
                    "summary": "派生 Schema 或 Git 身份状态不可用",
                    "scope": list(requested),
                    "source_refs": [_PREPARE_CONTRACT],
                },
            ),
        )
    fingerprint = schema_fingerprint(schema)
    basis = {
        "governed_project_id": boundary.governed_project_id,
        "fact_type_key": domain.fact_type_key,
        "schema_fingerprint": fingerprint,
        "worktree_fingerprint": worktree_fingerprint(boundary),
    }
    result = {
        **basis,
        "carrier": layout.carrier,
        "managed_fields": sorted(_MANAGED_FIELDS),
        "field_contracts": [
            {
                "field_path": field.path,
                "json_type": field.json_type,
                "presence": field.presence,
                "definition_ref": field.definition_ref,
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


def _residual_working_tree_source(
    boundary: CreationBoundary,
    read: FactReadResult,
    event_at: str,
) -> dict[str, Any]:
    source: dict[str, Any] = {
        "kind": "working_tree",
        "locator": (boundary.worktree_root / read.canonical_path).as_posix(),
        "observed_at": event_at,
        "details": {
            "view": "Working Tree",
            "check_status": read.check_status,
        },
    }
    if read.content_fingerprint is not None:
        source["details"]["content_fingerprint"] = read.content_fingerprint
    return source


def _current_target_residual_summary(
    prefix: str,
    residual: FactReadResult | None,
    expected_text: str | None,
) -> tuple[str, bool]:
    if residual is None or residual.check_status == "unavailable":
        return f"{prefix}；实际事实对象载体的当前状态无法确认", True
    if expected_text is not None and residual.raw_text == expected_text:
        return (
            f"{prefix}；当前重新读取观察到的实际事实对象载体完整字节内容与本次创建载体一致",
            False,
        )
    if residual.check_status == "mechanically_valid":
        return f"{prefix}；当前重新读取观察到的实际事实对象载体是另一机械有效版本", False
    if residual.check_status == "not_found":
        return f"{prefix}；当前重新读取确认实际事实对象载体的预期位置不存在", False
    if residual.raw_text is not None:
        return f"{prefix}；当前实际事实对象载体已安全完整读取，但对象未通过机械检查", False
    return (
        f"{prefix}；当前实际事实对象载体未能安全完整读取，机械检查未通过（状态为 `invalid`）",
        False,
    )


def _creation_rollback_failure_prefix(rollback: object) -> str:
    namespace_state = getattr(rollback, "namespace_state", None)
    if namespace_state == "uncertain":
        return "删除回滚在文件命名空间（namespace）中的生效情况无法确认"
    if namespace_state == "not_committed":
        if getattr(rollback, "outcome", None) == "conflict":
            return "删除回滚发生冲突，确认未在文件命名空间（namespace）生效"
        return "删除回滚确认未在文件命名空间（namespace）生效"
    return "删除回滚未完成"


def _creation_final_observation(creation: FactCreationResult) -> str:
    residual = creation.residual_readback
    if residual is None:
        return "not_required"
    if creation.actual_text is not None and residual.raw_text == creation.actual_text:
        return "same_created_bytes"
    if residual.check_status == "mechanically_valid":
        return "other_mechanically_valid"
    if residual.check_status == "invalid":
        return "mechanically_invalid"
    if residual.check_status == "not_found":
        return "not_found"
    return "unavailable"


def _creation_domain_result(
    creation: FactCreationResult,
    *,
    governed_project_id: str,
    fact_type_key: str,
) -> dict[str, Any] | None:
    """Project one UID-native create attempt and its target namespace state."""

    attempted_id = creation.actual_id
    if attempted_id is None:
        return None
    create = creation.creation_result
    if create is None:
        create_namespace_state = "not_attempted"
    elif create.outcome == "created" and create.namespace_state == "committed":
        create_namespace_state = "created"
    elif create.namespace_state == "uncertain":
        create_namespace_state = "uncertain"
    else:
        create_namespace_state = "not_created"

    if create_namespace_state != "created":
        post_create_readback = "not_run"
    elif creation.read is None:
        post_create_readback = "unavailable"
    elif (
        creation.read.check_status == "mechanically_valid"
        and creation.actual_text is not None
        and creation.read.raw_text == creation.actual_text
    ):
        post_create_readback = "passed"
    elif creation.read.check_status == "unavailable":
        post_create_readback = "unavailable"
    else:
        post_create_readback = "failed"

    rollback = creation.rollback_result
    if create_namespace_state != "created":
        if rollback is not None:
            raise AssertionError("target not confirmed created cannot have a delete rollback result")
        rollback_state = "not_applicable"
    elif post_create_readback == "passed":
        if rollback is not None:
            raise AssertionError("successful post-create readback cannot have a delete rollback result")
        rollback_state = "not_needed"
    elif rollback is None:
        raise AssertionError("failed post-create readback must retain its delete rollback result")
    elif rollback.outcome == "removed" and rollback.namespace_state == "committed":
        rollback_state = "removed"
    elif rollback.namespace_state == "uncertain":
        rollback_state = "uncertain"
    else:
        rollback_state = "not_removed"

    final_observation = _creation_final_observation(creation)
    observation_required = create_namespace_state in {"not_created", "uncertain"} or rollback_state in {
        "not_removed",
        "uncertain",
    }
    if observation_required:
        if final_observation == "not_required":
            raise AssertionError("creation outcome requires a fresh final target observation")
    elif final_observation != "not_required":
        raise AssertionError("creation outcome forbids an unrequired final target observation")
    layout = LAYOUTS[fact_type_key]
    result: dict[str, Any] = {
        "identity": {
            "attempted_object_uid": creation.attempted_object_uid,
            "attempted_locator": attempted_id,
        },
        "target_namespace": {
            "canonical_path": layout.canonical_path(attempted_id),
            "create_namespace_state": create_namespace_state,
            "post_create_readback": post_create_readback,
            "rollback_state": rollback_state,
            "final_observation": final_observation,
        },
    }
    if creation.status == "active_workcase_title_conflict":
        result.update(
            {
                "existing_refs": [dict(reference) for reference in creation.existing_refs],
                "ambiguous": creation.ambiguous,
            }
        )
    if create_namespace_state == "created" and post_create_readback == "passed":
        read = creation.read
        assert read is not None and read.fields is not None
        result.update(
            {
                "created": True,
                "actual_ref": {"object_uid": read.fields["object_uid"]},
                "content_fingerprint": read.content_fingerprint,
                "carrier": layout.carrier,
                "fact_object": (
                    {"frontmatter": read.fields, "body": read.body or ""}
                    if layout.carrier == "markdown"
                    else read.fields
                ),
            }
        )
    return result


def _creation_release_gap(
    requested: tuple[object, ...],
    *,
    created: bool,
    status: object,
) -> dict[str, Any]:
    gap = {
        "summary": (
            "事实对象已原子创建并成功回读；共同创建锁释放未能确认，"
            "后续受控写的串行协调状态未知；再次执行受控写入前须人工核对锁状态"
            if created
            else (
                f"事实对象创建领域结果（status={status}）已在共同锁释放前形成并保留；"
                "共同锁释放未能确认，后续受控写的串行协调状态未知；"
                "目标与残留范围仍以本响应原结果为准，再次执行受控写入前须人工核对锁状态"
            )
        ),
        "scope": list(requested),
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    if created:
        gap["code"] = "controlled_write_lock_release_uncertain"
    return gap


def _creation_release_diagnostic(creation: object, *, created: bool) -> dict[str, Any]:
    details = {
        "stage": "common_dir_lock_release",
        "creation_result_status": getattr(creation, "status", None),
        "subsequent_controlled_write_serialization": "uncertain",
    }
    if created:
        details.update(
            {
                "fact_target_state": "created_and_read_back",
                "identity_state": "uid_and_locator_bound",
            }
        )
    diagnostic = {
        "summary": "共同协调锁释放状态未能确认",
        "details": details,
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    if created:
        diagnostic["code"] = "controlled_write_lock_release_uncertain"
    return diagnostic


def _creation_release_follow_up(requested: tuple[object, ...]) -> dict[str, Any]:
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


def _workcase_public_readback_follow_up(actual_ref: dict[str, str]) -> dict[str, Any]:
    scope = [actual_ref]
    return {
        "summary": (
            "先以 result.actual_ref 公开精确回读已创建的 WorkCase；取得完整当前对象和非空 "
            "content_fingerprint 前不得向 Human 呈交 Gate 1"
        ),
        "required_inputs": [
            {
                "summary": "把 result.actual_ref 原样作为 read-fact-objects 的精确定位输入",
                "scope": scope,
                "source_refs": [_CREATE_CONTRACT],
            }
        ],
        "required_human_decisions": [],
        "resume_conditions": [
            {
                "summary": (
                    "公开 read-fact-objects 已返回完整当前 WorkCase 和非空 content_fingerprint；"
                    "create-fact-object 内部的 post-create readback 或 integrity audit 不替代该公开读取"
                ),
                "scope": scope,
                "source_refs": [_CREATE_CONTRACT],
            }
        ],
        "suggested_operations": [
            {
                "operation_key": "read-fact-objects",
                "summary": "使用 result.actual_ref 公开精确回读刚创建的 WorkCase",
                "scope": scope,
                "source_refs": [_CREATE_CONTRACT],
            }
        ],
    }


def _creation_release_overlay(
    execution: OperationExecution,
    creation: object,
    requested: tuple[object, ...],
    *,
    diagnostic_profile: bool,
) -> OperationExecution:
    if not bool(getattr(creation, "coordination_release_uncertain", False)):
        return execution
    created = getattr(creation, "status", None) == "created"
    status = getattr(creation, "status", None)
    diagnostic = _creation_release_diagnostic(creation, created=created)
    follow_up = _creation_release_follow_up(requested)
    sources = (
        execution.sources
        if _SHARED_WRITE_CONTRACT in execution.sources
        else (*execution.sources, _SHARED_WRITE_CONTRACT)
    )
    return replace(
        execution,
        sources=sources,
        gaps=(
            *execution.gaps,
            _creation_release_gap(requested, created=created, status=status),
        ),
        diagnostics=(*execution.diagnostics, *((diagnostic,) if diagnostic_profile else ())),
        follow_up=_merge_follow_up(execution.follow_up, follow_up),
    )


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
            "target_namespace_unchanged": True,
        },
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    return OperationExecution(
        outcome="unavailable",
        summary="事实对象共同创建锁当前不可用，未创建对象或写入目标文件",
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
    configuration_boundaries = configuration_reading_boundaries(run)
    if configuration_boundaries is None:
        return _boundary_execution(run, requested, "当前管辖结果不能形成完整配置级 UID 扫描边界")
    type_contract = source_reference("rule", _FACT_TYPE_SOURCES[basis.fact_type_key])
    change_sources = [_CREATE_CONTRACT, type_contract]
    request_sources = tuple(_plain(source) for source in run.sources) + tuple(change_sources)
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
    supplied = inject_observed_write_signature(supplied, request.observed_context)
    collision = signature_governance_collision_execution(
        run,
        request.observed_context,
        requested,
        request_sources,
        diagnostic_profile=request.response_profile == "diagnostic",
    )
    if collision is not None:
        return collision
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
                supplied=supplied,
                body=body,
                configuration_boundaries=configuration_boundaries,
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

    def finalized(execution: OperationExecution) -> OperationExecution:
        return _creation_release_overlay(
            execution,
            creation,
            requested,
            diagnostic_profile=request.response_profile == "diagnostic",
        )

    layout = LAYOUTS[basis.fact_type_key]
    domain_result = _creation_domain_result(
        creation,
        governed_project_id=boundary.governed_project_id,
        fact_type_key=basis.fact_type_key,
    )

    if creation.status == "candidate_unavailable":
        return finalized(
            OperationExecution(
                outcome="unavailable",
                summary="创建前项目级机械检查未能完成",
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=request_sources,
                gaps=(_issue_gap(creation.issues, requested[0]),),
            )
        )
    if creation.status == "candidate_rejected":
        return finalized(
            OperationExecution(
                outcome="rejected",
                summary="AI 填写内容未通过当前事实类型机械检查",
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=request_sources,
                gaps=(_issue_gap(creation.issues, requested[0]),),
            )
        )
    if creation.status == "durability_unavailable":
        return finalized(
            OperationExecution(
                outcome="unavailable",
                summary="当前平台没有启用公共事实写入的原生原子后端",
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=request_sources,
                gaps=(
                    {
                        "summary": (
                            "未创建事实文件：当前平台没有启用事实文件写入所需的原生原子后端"
                        ),
                        "scope": list(requested),
                        "source_refs": change_sources,
                    },
                ),
            )
        )
    if creation.status in {"final_rejected", "final_unavailable"}:
        assert creation.actual_id is not None
        assert domain_result is not None
        return finalized(
            OperationExecution(
                outcome="unavailable" if creation.status == "final_unavailable" else "rejected",
                summary="最终 UID 定位符机械前置条件发生变化，未创建对象",
                result=domain_result,
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=request_sources,
                changes=(
                    {
                        "summary": "最终机械前置检查未通过，目标原子创建未开始",
                        "status": "target-not-attempted",
                        "target": layout.canonical_path(creation.actual_id),
                        "source_refs": change_sources,
                    },
                ),
                gaps=(_issue_gap(creation.issues, requested[0]),),
            )
        )
    if creation.status == "active_workcase_title_scan_unavailable":
        assert creation.actual_id is not None
        assert domain_result is not None
        return finalized(
            OperationExecution(
                outcome="unavailable",
                summary="活跃 WorkCase title 全扫描未能完整形成，目标创建未尝试",
                result=domain_result,
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=request_sources,
                changes=(
                    {
                        "summary": "活跃 WorkCase title 或 status 判定不完整，目标原子创建未开始",
                        "status": "target-not-attempted",
                        "target": layout.canonical_path(creation.actual_id),
                        "source_refs": change_sources,
                    },
                ),
                gaps=(_issue_gap(creation.issues, requested[0]),),
            )
        )
    if creation.status == "active_workcase_title_conflict":
        assert creation.actual_id is not None
        assert domain_result is not None
        return finalized(
            OperationExecution(
                outcome="rejected",
                summary="同一实际 Git Working Tree 已存在严格同标题的活跃 WorkCase",
                result=domain_result,
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=request_sources,
                changes=(
                    {
                        "summary": "命中活跃 WorkCase title 冲突，目标原子创建未开始",
                        "status": "target-not-attempted",
                        "target": layout.canonical_path(creation.actual_id),
                        "source_refs": change_sources,
                    },
                ),
                gaps=(
                    {
                        "code": "active_workcase_title_conflict",
                        "summary": "活跃 WorkCase title 严格相等冲突",
                        "scope": list(requested),
                        "source_refs": [_CREATE_CONTRACT],
                    },
                ),
            )
        )
    if creation.status in {"creation_conflict", "creation_unavailable"}:
        assert creation.actual_id is not None
        assert domain_result is not None
        write = creation.creation_result
        assert write is not None
        residual = creation.residual_readback
        residual_source = (
            _residual_working_tree_source(boundary, residual, context.event_at)
            if isinstance(residual, FactReadResult)
            else None
        )
        if write.namespace_state == "uncertain":
            prefix = "目标原子创建在文件命名空间（namespace）中的生效情况无法确认"
        elif write.outcome == "conflict":
            prefix = "目标原子创建发生冲突，确认本次载体未在文件命名空间（namespace）提交"
        else:
            prefix = "目标原子创建确认未在文件命名空间（namespace）提交"
        target_summary, residual_unknown = _current_target_residual_summary(
            prefix,
            residual if isinstance(residual, FactReadResult) else None,
            creation.actual_text,
        )
        residual_refs = () if residual_source is None else (residual_source,)
        verification = (
            (
                {
                    "check": "目标 namespace 不确定后重新精确读取并机械检查实际事实对象载体",
                    "status": (
                        "unavailable"
                        if not isinstance(residual, FactReadResult) or residual.check_status == "unavailable"
                        else "passed"
                        if residual.check_status == "mechanically_valid"
                        else "failed"
                    ),
                    "scope": list(requested),
                    "evidence": [*residual_refs, _CREATE_CONTRACT],
                },
            )
            if isinstance(residual, FactReadResult) or write.namespace_state == "uncertain"
            else ()
        )
        return finalized(
            OperationExecution(
                outcome="unavailable",
                summary="UID 定位符目标的原子创建未能完成或确认",
                result=domain_result,
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=(*request_sources, *residual_refs, _IMPLEMENTATION_SOURCE),
                changes=(
                    {
                        "summary": target_summary,
                        "status": (
                            "target-create-uncertain" if write.namespace_state == "uncertain" else "target-not-created"
                        ),
                        "target": layout.canonical_path(creation.actual_id),
                        "source_refs": [*change_sources, *residual_refs],
                    },
                ),
                gaps=(
                    (
                        {
                            "summary": "目标 namespace 不确定后的实际事实对象载体无法确认",
                            "scope": list(requested),
                            "source_refs": [_CREATE_CONTRACT],
                        },
                    )
                    if residual_unknown
                    else ()
                ),
                verification=verification,
            )
        )
    if creation.status == "readback_failed":
        assert creation.actual_id is not None
        assert creation.actual_text is not None
        assert domain_result is not None
        rollback = creation.rollback_result
        assert rollback is not None
        rolled_back = rollback.outcome == "removed" and rollback.namespace_state == "committed"
        residual = creation.residual_readback
        residual_source = (
            _residual_working_tree_source(boundary, residual, context.event_at)
            if isinstance(residual, FactReadResult)
            else None
        )
        rollback_failure_prefix = _creation_rollback_failure_prefix(rollback)
        if rolled_back:
            target_summary = "本次创建载体已删除回滚"
        elif not isinstance(residual, FactReadResult) or residual.check_status == "unavailable":
            target_summary = f"{rollback_failure_prefix}；实际事实对象载体的残留状态无法确认"
        elif residual.raw_text == creation.actual_text:
            target_summary = (
                f"{rollback_failure_prefix}；当前重新读取观察到的实际事实对象载体完整字节内容与本次创建载体一致"
            )
        elif residual.check_status == "mechanically_valid":
            target_summary = f"{rollback_failure_prefix}；当前重新读取观察到的实际事实对象载体是另一机械有效版本"
        elif residual.check_status == "not_found":
            target_summary = f"{rollback_failure_prefix}；当前重新读取确认实际事实对象载体的预期位置不存在"
        elif residual.raw_text is not None:
            target_summary = f"{rollback_failure_prefix}；当前实际事实对象载体已安全完整读取，但对象未通过机械检查"
        else:
            target_summary = (
                f"{rollback_failure_prefix}；当前实际事实对象载体未能安全完整读取，机械检查未通过（状态为 `invalid`）"
            )
        residual_unknown = not rolled_back and (
            not isinstance(residual, FactReadResult) or residual.check_status == "unavailable"
        )
        residual_refs = () if residual_source is None else (residual_source,)
        residual_gap = (
            (
                {
                    "summary": "删除回滚后的实际事实对象载体无法确认",
                    "scope": list(requested),
                    "source_refs": [_CREATE_CONTRACT],
                },
            )
            if residual_unknown
            else ()
        )
        residual_verification = (
            (
                {
                    "check": "删除回滚后重新精确读取并机械检查实际事实对象载体",
                    "status": (
                        "unavailable"
                        if not isinstance(residual, FactReadResult) or residual.check_status == "unavailable"
                        else "passed"
                        if residual.check_status == "mechanically_valid"
                        else "failed"
                    ),
                    "scope": list(requested),
                    "evidence": [*residual_refs, _CREATE_CONTRACT],
                },
            )
            if not rolled_back
            else ()
        )
        return finalized(
            OperationExecution(
                outcome="error",
                summary=(
                    "写后回读未通过；已完成删除回滚" if rolled_back else "写后回读未通过，且未能确认删除回滚已经完成"
                ),
                result=domain_result,
                requested_scope=requested,
                completed_scope=(),
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=(*request_sources, *residual_refs, _IMPLEMENTATION_SOURCE),
                changes=(
                    {
                        "summary": "目标事实对象载体已由原子 no-overwrite 创建提交，但写后回读未通过",
                        "status": "target-created",
                        "target": layout.canonical_path(creation.actual_id),
                        "source_refs": change_sources,
                    },
                    {
                        "summary": target_summary,
                        "status": "target-removed" if rolled_back else "target-remove-unconfirmed",
                        "target": layout.canonical_path(creation.actual_id),
                        "source_refs": [*change_sources, *residual_refs],
                    },
                ),
                gaps=(_issue_gap(creation.issues, requested[0]), *residual_gap),
                verification=residual_verification,
            )
        )

    assert creation.status == "created"
    actual_id = creation.actual_id
    read = creation.read
    creation_result = creation.creation_result
    assert actual_id is not None
    assert read is not None
    assert creation_result is not None
    assert domain_result is not None

    assert read.fields is not None and isinstance(read.fields.get("object_uid"), str)
    actual_ref = {"object_uid": read.fields["object_uid"]}
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
    return finalized(
        post_write_integrity_audit(
            OperationExecution(
                outcome="ok",
                summary="事实对象已由 Code 最终分配身份、原子创建并完成写后回读",
                result=domain_result,
                requested_scope=requested,
                completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=sources,
                changes=(
                    {
                        "summary": "已原子创建并回读事实对象",
                        "status": "target-created",
                        "target": layout.canonical_path(actual_id),
                        "source_refs": [*change_sources, working_tree_source],
                    },
                ),
                verification=(
                    {
                        "check": (
                            "写后读取、派生 Schema、身份、引用和关系机械检查已通过；"
                            f"namespace={creation_result.namespace_state}"
                        ),
                        "status": "passed",
                        "scope": [actual_ref],
                        "evidence": [working_tree_source, _CREATE_CONTRACT],
                    },
                ),
                follow_up=(
                    _workcase_public_readback_follow_up(actual_ref)
                    if basis.fact_type_key == "workcase"
                    else None
                ),
            ),
            boundary=boundary,
            schemas=schemas,
            audit_contract=_INTEGRITY_CONTRACT,
            configuration_boundaries=configuration_boundaries,
        )
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
    if not native_atomic_fact_writes_supported():
        requested = (domain.draft_basis.to_json(),)
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=requested,
            gaps=(
                {
                    "summary": "当前平台没有启用公共事实写入的原生原子后端",
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
    response_fields=(
        "basis",
        "schema_fingerprint",
        "worktree_fingerprint",
        "carrier",
        "managed_fields",
        "field_contracts",
    ),
)

CREATE_FACT_OBJECT_IMPLEMENTATION = OperationImplementation(
    required_inputs=CREATE_REQUIRED_INPUTS,
    optional_inputs=CREATE_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CREATE_CONTRACT),
    check_availability=_create_availability,
    call=_create_execute,
    response_fields=(
        "identity",
        "target_namespace",
        "created",
        "actual_ref",
        "content_fingerprint",
        "carrier",
        "fact_object",
    ),
)


__all__ = [
    "CREATE_FACT_OBJECT_IMPLEMENTATION",
    "CREATE_OPERATION_KEY",
    "PREPARE_FACT_DRAFT_IMPLEMENTATION",
    "PREPARE_OPERATION_KEY",
]
