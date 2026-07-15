"""Conditionally replace one exact, mechanically valid fact object."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, allocation_lock, serialize_fact_object
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema, project_fact_schemas
from ldvh.facts.transitions import validate_fact_transition
from ldvh.facts.update import atomic_replace_text_if_unchanged
from ldvh.facts.validation import validate_fact_object
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
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation",
    "code/ldvh/helper/operations/fact_update_operation.py",
)
_MANAGED_FIELDS = frozenset({"object_id", "fact_type_key", "created_at", "updated_at"})


def _validated_request(request: CommonRequest, context: OperationExecutionContext) -> FactUpdateRequest:
    parsed = parse_fact_update_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACT,))
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
    stabilize_project_index(index)
    return index.cache.get(key, read)


def _candidate(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    schema: FactSchema,
    fact_type_key: str,
    object_id: str,
    before: dict[str, Any],
    supplied: dict[str, Any],
    body: str | None,
) -> tuple[FactReadResult, str]:
    layout = LAYOUTS[fact_type_key]
    fields = {
        **supplied,
        "object_id": before["object_id"],
        "fact_type_key": before["fact_type_key"],
        "created_at": before["created_at"],
        "updated_at": datetime.now().astimezone().isoformat(),
    }
    text = serialize_fact_object(layout, fields, body)
    parsed = parse_study_markdown(text) if layout.carrier == "markdown" else parse_yaml_object(text)
    issues = list(parsed.issues)
    if parsed.fields is not None:
        issues.extend(validate_fact_object(fact_type_key, parsed.fields, schema))
        issues.extend(validate_fact_transition(fact_type_key, before, parsed.fields))
    read = FactReadResult(
        layout.canonical_path(object_id),
        layout.carrier,
        "invalid" if issues or parsed.fields is None else "mechanically_valid",
        parsed.fields,
        parsed.body,
        tuple(issues),
        None,
        text,
    )
    if read.check_status != "mechanically_valid" or read.fields is None:
        return read, text
    index = ProjectFactIndex(
        boundary.worktree_root,
        boundary.governed_project_id,
        schemas,
        boundary.git_common_dir,
    )
    key = (fact_type_key, object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index)
    return index.cache.get(key, read), text


def _working_tree_source(boundary: CreationBoundary, canonical_path: str) -> dict[str, Any]:
    return {
        "kind": "working_tree",
        "locator": (boundary.worktree_root / canonical_path).as_posix(),
        "observed_at": datetime.now().astimezone().isoformat(),
        "details": {"view": "Working Tree"},
    }


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
    if not durable_writes_enabled():
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台尚未获准以 file-only 耐久等级更新事实对象",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=request_sources,
            gaps=(
                {
                    "summary": "未创建锁状态或替换事实文件；需先决定是否接受 Windows file-only 耐久降级",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )

    with allocation_lock(boundary, layout):
        current = _current_read(
            boundary,
            schemas,
            reference.fact_type_key,
            reference.object_id,
        )
        if current.check_status != "mechanically_valid" or current.fields is None:
            status = "unavailable" if current.check_status == "unavailable" else "rejected"
            return OperationExecution(
                outcome=status,  # type: ignore[arg-type]
                summary="当前对象未形成可更新的 mechanically valid 快照",
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=request_sources,
                gaps=(
                    {
                        "summary": _issue_summary(current.issues) or f"当前读取状态为 {current.check_status}",
                        "scope": list(requested),
                        "source_refs": [_CONTRACT],
                    },
                ),
            )
        if current.content_fingerprint != domain.expected_content_fingerprint or current.raw_text is None:
            return _rejected(
                domain,
                run,
                "事实对象内容指纹已经过期",
                "必须重新调用 read-fact-objects 并基于最新完整对象形成目标内容",
                request_sources,
            )

        mutable_current = {key: value for key, value in current.fields.items() if key not in _MANAGED_FIELDS}
        if mutable_current == supplied and (layout.carrier != "markdown" or (current.body or "") == body):
            working_tree_source = _working_tree_source(boundary, current.canonical_path)
            sources = (*request_sources, working_tree_source, _IMPLEMENTATION_SOURCE)
            return OperationExecution(
                outcome="no_change",
                summary="提交的完整目标与当前对象相同，未重写文件",
                result=_result(
                    current,
                    boundary.governed_project_id,
                    reference.fact_type_key,
                    reference.object_id,
                    current.content_fingerprint,
                ),
                requested_scope=requested,
                completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=sources,
                verification=(
                    {
                        "check": "当前完整目标与请求内容相同且内容指纹仍匹配",
                        "status": "passed",
                        "scope": list(requested),
                        "evidence": [working_tree_source, _CONTRACT],
                    },
                ),
            )

        candidate, candidate_text = _candidate(
            boundary,
            schemas,
            schema,
            reference.fact_type_key,
            reference.object_id,
            current.fields,
            supplied,
            body,
        )
        if candidate.check_status != "mechanically_valid":
            status = "unavailable" if candidate.check_status == "unavailable" else "rejected"
            return OperationExecution(
                outcome=status,  # type: ignore[arg-type]
                summary="完整目标未通过更新前机械检查",
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=request_sources,
                gaps=(
                    {
                        "summary": _issue_summary(candidate.issues) or "项目级机械检查未完成",
                        "scope": list(requested),
                        "source_refs": [_CONTRACT],
                    },
                ),
            )

        replacement = atomic_replace_text_if_unchanged(
            boundary.worktree_root,
            layout,
            reference.object_id,
            current.raw_text,
            candidate_text,
        )
        if replacement.outcome != "replaced" or replacement.namespace_state != "committed":
            outcome = "rejected" if replacement.outcome == "conflict" else "unavailable"
            return OperationExecution(
                outcome=outcome,  # type: ignore[arg-type]
                summary=("原子替换前对象发生变化" if replacement.outcome == "conflict" else "原子替换技术条件不成立"),
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=(*request_sources, _IMPLEMENTATION_SOURCE),
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

        readback = _current_read(
            boundary,
            schemas,
            reference.fact_type_key,
            reference.object_id,
        )
        if readback.check_status != "mechanically_valid" or readback.fields is None:
            rollback = atomic_replace_text_if_unchanged(
                boundary.worktree_root,
                layout,
                reference.object_id,
                candidate_text,
                current.raw_text,
            )
            return OperationExecution(
                outcome="error",
                summary=(
                    "写后回读未通过；已回滚"
                    if rollback.outcome == "replaced" and rollback.namespace_state == "committed"
                    else "写后回读未通过且无法安全回滚"
                ),
                requested_scope=requested,
                not_completed_scope=requested,
                governance_resolution=run.result.to_json() if run.result else None,
                sources=(*request_sources, _IMPLEMENTATION_SOURCE),
                changes=(
                    {
                        "summary": (
                            "已恢复更新前载体"
                            if rollback.outcome == "replaced" and rollback.namespace_state == "committed"
                            else "新载体可能残留且未完成验证"
                        ),
                        "status": (
                            "rolled-back"
                            if rollback.outcome == "replaced" and rollback.namespace_state == "committed"
                            else "rollback-failed"
                        ),
                        "target": reference.to_json(),
                        "source_refs": [_CONTRACT],
                    },
                ),
                gaps=(
                    {
                        "summary": _issue_summary(readback.issues) or "写后项目级机械检查未完成",
                        "scope": list(requested),
                        "source_refs": [_CONTRACT],
                    },
                ),
            )

    working_tree_source = _working_tree_source(boundary, readback.canonical_path)
    sources = (*request_sources, working_tree_source, _IMPLEMENTATION_SOURCE)
    return OperationExecution(
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
        changes=(
            {
                "summary": (
                    f"已原子替换并回读事实对象（durability={replacement.durability}, cleanup={replacement.cleanup}）"
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
            gaps=(
                {
                    "summary": "当前平台尚未获准以 file-only 耐久等级更新事实对象",
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
        current.check_status != "mechanically_valid"
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
