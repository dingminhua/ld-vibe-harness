"""Prepare one read-only, caller-completed whole-object fact update draft."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_object_operation import FACT_OBJECT_IMPLEMENTATION
from ldvh.helper.operations.fact_object_request import parse_fact_object_request
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "prepare-fact-object-update"
REQUIRED_INPUTS = ("arguments.fact_ref",)
OPTIONAL_INPUTS = ("work_object_locators", "arguments.workspace_root")
_ARGUMENT_FIELDS = frozenset({"workspace_root", "fact_ref"})
_MANAGED_FIELDS = ("object_uid", "object_id", "fact_type_key", "created_at", "updated_at")
_CONTRACT = source_reference(
    "rule",
    "fact-model-foundation::11.6.1 事实对象更新草案准备输入与结果",
)
_WORKCASE_CONTRACT = source_reference(
    "rule",
    "workcase-fact-type::prepare-fact-object-update 对 WorkCase 的限制",
)
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation",
    "code/ldvh/helper/operations/fact_update_prepare_operation.py",
)
_INPUT_EXAMPLE = {
    "summary": "按稳定 UID 准备一个仍须调用方补齐的 whole-object 更新草案",
    "arguments_fragment": {"fact_ref": {"object_uid": "0198f1c7-8a2b-7c3d-9e4f-123456789abc"}},
    "source_refs": (_CONTRACT,),
    "composition_note": (
        "该只读请求只返回 caller_completion_required 草案。调用方仍须独立形成真实语义变化、"
        "恰追加一条真实 change_log、重新观察三字段 signature，并仅在目标入口与实际转换要求时补授权。"
    ),
}


def _read_request(request: CommonRequest, context: OperationExecutionContext) -> CommonRequest:
    problems: list[str] = []
    unknown = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")
    if "fact_ref" not in request.arguments:
        problems.append("arguments.fact_ref 必填")
    if problems:
        raise OperationRequestError(tuple(problems), sources=(_CONTRACT,))

    read_arguments: dict[str, Any] = {"fact_refs": [request.arguments.get("fact_ref")]}
    if "workspace_root" in request.arguments:
        read_arguments["workspace_root"] = request.arguments["workspace_root"]
    read_request = CommonRequest(
        task=request.task,
        work_object_locators=request.work_object_locators,
        arguments=read_arguments,
        requested_disclosure=request.requested_disclosure,
        observed_context=request.observed_context,
        authorization_reference=request.authorization_reference,
        response_profile=request.response_profile,
    )
    parsed = parse_fact_object_request(read_request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACT,))
    if len(parsed.request.fact_scopes) != 1:
        raise OperationRequestError(("arguments.fact_ref 必须精确解析为一个稳定事实引用",), sources=(_CONTRACT,))
    return read_request


def _sources(*groups: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    merged: list[dict[str, Any]] = []
    for group in groups:
        for source in group:
            if source not in merged:
                merged.append(source)
    return tuple(merged)


def _requested(request: CommonRequest) -> tuple[dict[str, Any], ...]:
    value = request.arguments.get("fact_ref")
    return (deepcopy(value),) if isinstance(value, dict) else ()


def _rejected(
    request: CommonRequest,
    execution: OperationExecution,
    summary: str,
    detail: str,
) -> OperationExecution:
    requested = _requested(request)
    return OperationExecution(
        outcome="rejected",
        summary=summary,
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=execution.governance_resolution,
        sources=_sources(execution.sources, (_CONTRACT, _WORKCASE_CONTRACT, _IMPLEMENTATION_SOURCE)),
        gaps=(
            {
                "summary": detail,
                "scope": list(requested),
                "source_refs": [_CONTRACT, _WORKCASE_CONTRACT],
            },
        ),
    )


def _draft_fact_object(fact_object: dict[str, Any], carrier: str) -> dict[str, Any]:
    draft = deepcopy(fact_object)
    if carrier == "markdown":
        frontmatter = draft.get("frontmatter")
        body = draft.get("body")
        if set(draft) != {"frontmatter", "body"} or not isinstance(frontmatter, dict) or not isinstance(body, str):
            raise ValueError("mechanically valid Markdown fact did not expose frontmatter/body")
        for field in _MANAGED_FIELDS:
            frontmatter.pop(field, None)
        return {"frontmatter": frontmatter, "body": body}
    for field in _MANAGED_FIELDS:
        draft.pop(field, None)
    return draft


def _completion_requirements() -> dict[str, Any]:
    return {
        "semantic_change": {"required": True, "provider": "caller"},
        "change_log_append": {
            "required": True,
            "provider": "caller",
            "target": "arguments.fact_object.change_log",
            "count": 1,
            "fields": ["summary"],
            "signature_source": "observed_context.signature",
        },
        "observed_signature": {
            "required": True,
            "provider": "caller",
            "target": "observed_context.signature",
            "fields": ["product_name", "model_name", "agent_runtime_name"],
        },
        "authorization_reference": {
            "required": "source_conditioned",
            "provider": "caller",
            "source": "target-operation-and-transition",
        },
    }


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    read_request = _read_request(request, context)
    read_execution = FACT_OBJECT_IMPLEMENTATION.call(read_request, repository, context)
    requested = _requested(request)
    sources = _sources(read_execution.sources, (_CONTRACT, _WORKCASE_CONTRACT, _IMPLEMENTATION_SOURCE))
    if read_execution.result is None:
        return OperationExecution(
            outcome=read_execution.outcome,
            summary="当前事实对象读取未形成可准备的完整目标",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=read_execution.governance_resolution,
            sources=sources,
            gaps=read_execution.gaps,
            diagnostics=read_execution.diagnostics,
            follow_up=read_execution.follow_up,
        )

    items = read_execution.result.get("items")
    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
        return OperationExecution(
            outcome="error",
            summary="内部读取结果没有形成唯一事实对象",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=read_execution.governance_resolution,
            sources=sources,
            gaps=(
                {
                    "summary": "read-fact-objects 未返回唯一 item，未形成任何更新草案",
                    "scope": list(requested),
                    "source_refs": [_CONTRACT],
                },
            ),
        )

    item = items[0]
    check_status = item.get("check_status")
    if check_status != "mechanically_valid":
        detail = "目标未通过当前完整机械检查，未形成任何更新草案"
        return _rejected(request, read_execution, "当前事实对象不具备草案准备资格", detail)
    fact_object = item.get("fact_object")
    resolved_ref = item.get("resolved_ref")
    fingerprint = item.get("content_fingerprint")
    carrier = item.get("carrier")
    canonical_path = item.get("canonical_path")
    if (
        not isinstance(fact_object, dict)
        or not isinstance(resolved_ref, dict)
        or set(resolved_ref) != {"object_uid"}
        or not isinstance(resolved_ref.get("object_uid"), str)
        or not isinstance(fingerprint, str)
        or not isinstance(carrier, str)
        or not isinstance(canonical_path, str)
    ):
        return _rejected(
            request,
            read_execution,
            "当前事实对象缺少可组合的稳定读取结果",
            "目标必须具有权威 object_uid、完整内容指纹、canonical path 与可解析完整对象",
        )

    fields = fact_object.get("frontmatter") if carrier == "markdown" else fact_object
    if not isinstance(fields, dict) or not isinstance(fields.get("fact_type_key"), str):
        return _rejected(request, read_execution, "当前事实对象缺少类型身份", "未形成事实类型与官方更新路由")
    fact_type_key = fields["fact_type_key"]
    if fact_type_key == "workcase" and fields.get("status") != "open":
        return _rejected(
            request,
            read_execution,
            "当前 WorkCase 不具备草案准备资格",
            "只有 mechanically valid 且 status=open 的 WorkCase 才能准备 update-workcase 草案",
        )

    target_operation = "update-workcase" if fact_type_key == "workcase" else "update-fact-object"
    draft = _draft_fact_object(fact_object, carrier)
    actual_ref = {"object_uid": resolved_ref["object_uid"]}
    working_sources = tuple(item.get("source_refs", ())) if isinstance(item.get("source_refs"), list) else ()
    evidence = _sources(working_sources, (_CONTRACT, _WORKCASE_CONTRACT))
    return OperationExecution(
        outcome="ok",
        summary="已形成绑定当前读取的 caller-completion-required 更新草案",
        result={
            "actual_ref": actual_ref,
            "canonical_path": canonical_path,
            "carrier": carrier,
            "fact_type_key": fact_type_key,
            "source_content_fingerprint": fingerprint,
            "target_operation": target_operation,
            "draft_status": "caller_completion_required",
            "managed_fields_removed": list(_MANAGED_FIELDS),
            "request_draft": {
                "arguments": {
                    "fact_ref": deepcopy(actual_ref),
                    "expected_content_fingerprint": fingerprint,
                    "fact_object": draft,
                },
                "observed_context": {
                    "signature": {
                        "product_name": None,
                        "model_name": None,
                        "agent_runtime_name": None,
                    }
                },
            },
            "completion_requirements": _completion_requirements(),
        },
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=read_execution.governance_resolution,
        sources=sources,
        verification=(
            {
                "check": "当前读取、托管字段移除与 whole-object draft composition 已确定性完成",
                "status": "passed",
                "scope": list(requested),
                "evidence": list(evidence),
            },
        ),
    )


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    execution = _execute(request, repository, context)
    if execution.outcome == "ok":
        return AvailabilityEvaluation(
            availability="available_for_request",
            available_scope=execution.completed_scope,
        )
    return AvailabilityEvaluation(
        availability="unavailable_for_request",
        unavailable_scope=execution.not_completed_scope or execution.requested_scope,
        gaps=execution.gaps,
    )


FACT_UPDATE_PREPARE_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACT, _WORKCASE_CONTRACT),
    check_availability=_check_availability,
    call=_execute,
    input_examples=(_INPUT_EXAMPLE,),
)

__all__ = ["FACT_UPDATE_PREPARE_IMPLEMENTATION", "OPERATION_KEY"]
