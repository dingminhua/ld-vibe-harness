"""Bind governance-scope resolution to the source-defined Helper operation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, assert_never

from ldvh.governance.models import ConfigStatus, ScopeDescriptor
from ldvh.governance.resolver import (
    GovernanceResolutionRun,
    ResolutionDiagnostic,
    ResolutionGap,
    TechnicalOutcome,
    resolve_governance_scope,
)
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.governance_scope_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    GovernanceScopeRequest,
    parse_governance_scope_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "resolve-governance-scope"
_INPUT_CONTRACT = source_reference(
    "rule",
    "work-object-governance-scope::10.1 管辖范围解析输入字段",
)
_SCOPE_UNKNOWN_SOURCE = source_reference(
    "rule",
    "work-object-governance-scope::8.3 scope_unknown 识别、报告与处理",
)
_ENVIRONMENT_INTEGRATION_TEMPLATE = source_reference(
    "rule",
    "specs/33-环境接入行动模板.md",
    details={"line": 77},
)
_IMPLEMENTATION_EVIDENCE = (
    source_reference(
        "implementation",
        "code/ldvh/helper/operations/governance_scope_operation.py",
    ),
)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _scope_json(scope: tuple[ScopeDescriptor, ...]) -> tuple[dict[str, object], ...]:
    return tuple(item.to_json() for item in scope)


def _gap_json(item: ResolutionGap) -> dict[str, Any]:
    return {
        "summary": item.summary,
        "scope": list(_scope_json(item.scope)),
        "source_refs": [_plain(source) for source in item.source_refs],
    }


def _diagnostic_json(item: ResolutionDiagnostic) -> dict[str, Any]:
    result: dict[str, Any] = {
        "summary": item.summary,
        "details": {
            "stage": item.stage,
            "scope": list(_scope_json(item.scope)),
        },
    }
    if item.source_refs:
        result["source_refs"] = [_plain(source) for source in item.source_refs]
    return result


def _validated_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> GovernanceScopeRequest:
    parsed = parse_governance_scope_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_INPUT_CONTRACT,))
    return parsed.request


def _resolve(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> GovernanceResolutionRun:
    domain_request = _validated_request(request, context)
    return resolve_governance_scope(
        domain_request.requested_scope,
        base=domain_request.base,
        explicit_workspace_root=domain_request.workspace_root,
    )


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    del repository
    run = _resolve(request, context)
    available_scope = _scope_json(run.completed_scope)
    unavailable_scope = _scope_json(run.not_completed_scope)
    if not unavailable_scope:
        availability = "available_for_request"
    elif available_scope:
        availability = "partially_available"
    else:
        availability = "unavailable_for_request"
    return AvailabilityEvaluation(
        availability=availability,
        available_scope=available_scope,
        unavailable_scope=unavailable_scope,
        gaps=tuple(_gap_json(item) for item in run.gaps),
    )


def _outcome(run: GovernanceResolutionRun) -> str:
    if not run.technical_non_completions:
        return "ok"
    if run.completed_scope:
        return "partial"
    outcomes = {item.outcome for item in run.technical_non_completions}
    if TechnicalOutcome.ERROR in outcomes:
        return "error"
    if outcomes == {TechnicalOutcome.UNAVAILABLE}:
        return "unavailable"
    raise AssertionError(f"unsupported technical outcomes: {sorted(outcomes)}")


def _summary(outcome: str) -> str:
    if outcome == "ok":
        return "已完成全部请求范围的管辖范围解析"
    if outcome == "partial":
        return "已完成部分请求范围的管辖范围解析，并保留技术未完成范围"
    if outcome == "unavailable":
        return "当前技术条件不足，无法形成请求范围的管辖解析结果"
    if outcome == "error":
        return "管辖范围解析发生技术错误，无法形成可信结果"
    assert_never(outcome)  # type: ignore[arg-type]


def _scope_refs() -> list[Any]:
    return []


def _follow_up_for_config_status(config_status_value: str) -> dict[str, Any] | None:
    if config_status_value == ConfigStatus.VALID.value:
        return None
    if config_status_value == ConfigStatus.MISSING.value:
        return {
            "summary": "当前工作区未找到管辖配置；依赖管辖结论的受控操作暂时不可用",
            "required_inputs": [],
            "required_human_decisions": [
                {
                    "summary": "请确认工作区根目录，并在其下创建 LDVH-GOVERNED-PROJECTS.yaml",
                    "scope": _scope_refs(),
                    "source_refs": [_plain(_SCOPE_UNKNOWN_SOURCE)],
                },
            ],
            "resume_conditions": [
                {
                    "summary": "工作区根下存在格式有效的 LDVH-GOVERNED-PROJECTS.yaml，且其中登记了当前 Git worktree",
                    "scope": _scope_refs(),
                    "source_refs": [_plain(_SCOPE_UNKNOWN_SOURCE)],
                },
            ],
            "suggested_operations": [
                {
                    "operation_key": "read-action-template-content",
                    "summary": "读取环境接入行动模板，按其引导完成管辖配置的创建与验证",
                    "scope": _scope_refs(),
                    "source_refs": [_plain(_ENVIRONMENT_INTEGRATION_TEMPLATE)],
                },
            ],
        }
    if config_status_value == ConfigStatus.INVALID.value:
        return {
            "summary": "已找到管辖配置，但格式或字段无效；依赖管辖结论的受控操作暂时不可用",
            "required_inputs": [],
            "required_human_decisions": [
                {
                    "summary": "请修正 LDVH-GOVERNED-PROJECTS.yaml 的 YAML 格式或字段定义",
                    "scope": _scope_refs(),
                    "source_refs": [_plain(_SCOPE_UNKNOWN_SOURCE)],
                },
            ],
            "resume_conditions": [
                {
                    "summary": "已按规范修复 LDVH-GOVERNED-PROJECTS.yaml 的格式与字段问题",
                    "scope": _scope_refs(),
                    "source_refs": [_plain(_SCOPE_UNKNOWN_SOURCE)],
                },
            ],
            "suggested_operations": [
                {
                    "operation_key": "read-action-template-content",
                    "summary": "读取环境接入行动模板，按其引导完成管辖配置的修复与验证",
                    "scope": _scope_refs(),
                    "source_refs": [_plain(_ENVIRONMENT_INTEGRATION_TEMPLATE)],
                },
            ],
        }
    if config_status_value == ConfigStatus.CONFLICT.value:
        return {
            "summary": "存在多个候选管辖配置且产生冲突；依赖管辖结论的受控操作暂时不可用",
            "required_inputs": [],
            "required_human_decisions": [
                {
                    "summary": "请在多个候选 LDVH-GOVERNED-PROJECTS.yaml 之间选择或合并为单一有效配置",
                    "scope": _scope_refs(),
                    "source_refs": [_plain(_SCOPE_UNKNOWN_SOURCE)],
                },
            ],
            "resume_conditions": [
                {
                    "summary": "候选冲突已通过选择或合并解决，工作区根下存在单一有效配置",
                    "scope": _scope_refs(),
                    "source_refs": [_plain(_SCOPE_UNKNOWN_SOURCE)],
                },
            ],
            "suggested_operations": [
                {
                    "operation_key": "read-action-template-content",
                    "summary": "读取环境接入行动模板，按其引导完成管辖配置冲突的解决与验证",
                    "scope": _scope_refs(),
                    "source_refs": [_plain(_ENVIRONMENT_INTEGRATION_TEMPLATE)],
                },
            ],
        }
    return None


def _build_follow_up(run: GovernanceResolutionRun) -> dict[str, Any] | None:
    if run.result is None:
        return None
    config_status_value = getattr(run.result, "config_status", None)
    if config_status_value is None:
        return None
    return _follow_up_for_config_status(config_status_value.value)


def _call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    del repository
    run = _resolve(request, context)
    outcome = _outcome(run)
    follow_up = _build_follow_up(run)
    return OperationExecution(
        outcome=outcome,  # type: ignore[arg-type]
        summary=_summary(outcome),
        result=None if run.result is None else run.result.to_json(),
        requested_scope=_scope_json(run.requested_scope),
        completed_scope=_scope_json(run.completed_scope),
        not_completed_scope=_scope_json(run.not_completed_scope),
        sources=tuple(_plain(source) for source in run.sources) + _IMPLEMENTATION_EVIDENCE,
        gaps=tuple(_gap_json(item) for item in run.gaps),
        diagnostics=tuple(_diagnostic_json(item) for item in run.diagnostics),
        follow_up=follow_up,
    )


GOVERNANCE_SCOPE_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_check_availability,
    call=_call,
    response_fields=(
    "workspace_root",
    "config_path",
    "config_status",
    "scope_status",
    "object_resolutions",
    "registered_project_candidates",
    "source_refs",
    ),
)

__all__ = ["GOVERNANCE_SCOPE_IMPLEMENTATION", "OPERATION_KEY"]
