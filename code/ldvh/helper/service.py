"""Thin Helper service orchestration for the public foundational commands."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import ldvh
from ldvh.helper.operation_runtime import (
    OperationExecution,
    OperationImplementation,
    bind_operation_implementations,
    implementation_contract_diagnostics,
    implementation_error_execution,
)
from ldvh.helper.operation_sources import OperationDeclarationCandidate
from ldvh.helper.requests import parse_common_request, valid_operation_key
from ldvh.helper.responses import RequestKind, ServiceResult, common_response, diagnostic, gap, source_reference
from ldvh.helper.rule_source import inspect_colocated_rule_source

CONTRACT_SOURCES = [
    source_reference("rule", "specs/04-Helper CLI 服务规范.md"),
    source_reference("rule", "specs/attachments/04.Att.01-Helper CLI 请求与响应字段表.md"),
]
RULE_SOURCE_QUALIFICATION_SOURCE = source_reference("rule", "specs/01-规范模型基础规范.md")
OPERATION_IMPLEMENTATIONS: dict[str, OperationImplementation] = {}


def invalid_request_result(
    request_kind: RequestKind,
    operation_key: str | None,
    problems: tuple[str, ...],
) -> ServiceResult:
    return common_response(
        request_kind=request_kind,
        operation_key=operation_key,
        outcome="invalid_request",
        summary="Helper 请求不符合共同接口契约",
        requested_scope=[] if operation_key is None else [operation_key],
        not_completed_scope=[] if operation_key is None else [operation_key],
        sources=CONTRACT_SOURCES,
        gaps=[gap(problem, sources=CONTRACT_SOURCES) for problem in problems],
        diagnostics=[diagnostic("请求解析或校验未通过", problems=list(problems))],
    )


def _rule_source_unavailable(request_kind: RequestKind, operation_key: str | None, problem: str) -> ServiceResult:
    return common_response(
        request_kind=request_kind,
        operation_key=operation_key,
        outcome="unavailable",
        summary="当前进程无法形成可信的规则源发现结果",
        requested_scope=[] if operation_key is None else [operation_key],
        not_completed_scope=[] if operation_key is None else [operation_key],
        sources=CONTRACT_SOURCES,
        gaps=[gap(problem, sources=CONTRACT_SOURCES)],
        diagnostics=[diagnostic("规则源检查未完成", problem=problem)],
    )


def _declaration_source(declaration: OperationDeclarationCandidate) -> dict[str, Any]:
    return source_reference(
        "rule",
        declaration.source.path,
        line=declaration.source.line,
        heading=declaration.source.heading,
        source_key=declaration.source_key,
    )


def _qualification_gaps(
    conditions: tuple[str, ...],
    *,
    sources: list[dict[str, Any]],
    scope: list[object] | None = None,
) -> list[dict[str, Any]]:
    return [
        gap(
            f"当前 Code 尚未自动证明：{condition}",
            scope=scope,
            sources=sources,
        )
        for condition in dict.fromkeys(conditions)
    ]


def _operation_item(
    declaration: OperationDeclarationCandidate,
    *,
    observed_at: str,
    request_check: bool,
    rule_source_conditions: tuple[str, ...],
    contract_conditions: tuple[str, ...],
    implementation: OperationImplementation | None = None,
    availability: str | None = None,
    available_scope: list[object] | None = None,
    unavailable_scope: list[object] | None = None,
    availability_gaps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    operation_scope: list[object] = [declaration.operation_key]
    declaration_source = _declaration_source(declaration)
    operation_gaps = [
        *(
            [
                gap(
                    "当前 Code 尚未发现该公开操作的实际实现及可复核能力依据",
                    scope=operation_scope,
                    sources=[declaration_source],
                )
            ]
            if implementation is None
            else []
        ),
        *(
            [
                gap(
                    "领域输入清单尚未由 Code 机械确认；required_inputs 与 optional_inputs 的空数组不表示该操作没有输入",
                    scope=operation_scope,
                    sources=[source_reference("rule", declaration.arguments_contract)],
                )
            ]
            if contract_conditions and implementation is None
            else []
        ),
        *_qualification_gaps(
            rule_source_conditions,
            sources=[RULE_SOURCE_QUALIFICATION_SOURCE],
            scope=operation_scope,
        ),
        *_qualification_gaps(contract_conditions, sources=CONTRACT_SOURCES, scope=operation_scope),
        *([] if availability_gaps is None else availability_gaps),
    ]
    return {
        "operation_key": declaration.operation_key,
        "summary": declaration.summary,
        "sources": [declaration_source],
        "effect": declaration.effect,
        "required_inputs": [] if implementation is None else list(implementation.required_inputs),
        "optional_inputs": [] if implementation is None else list(implementation.optional_inputs),
        "implementation": {
            "present": implementation is not None,
            "evidence": [] if implementation is None else list(implementation.evidence),
        },
        "availability": (
            ("unavailable_for_request" if implementation is None else availability) if request_check else None
        ),
        "available_scope": [] if available_scope is None else available_scope,
        "unavailable_scope": (
            operation_scope
            if request_check and implementation is None
            else ([] if unavailable_scope is None else unavailable_scope)
        ),
        "gaps": operation_gaps,
        "observed_at": observed_at,
    }


def _execution_response(
    request_kind: RequestKind,
    operation_key: str,
    declaration_source: dict[str, Any],
    execution: OperationExecution,
) -> ServiceResult:
    return common_response(
        request_kind=request_kind,
        operation_key=operation_key,
        outcome=execution.outcome,
        summary=execution.summary,
        result=execution.result,
        requested_scope=list(execution.requested_scope),
        completed_scope=list(execution.completed_scope),
        not_completed_scope=list(execution.not_completed_scope),
        sources=[*CONTRACT_SOURCES, declaration_source, *execution.sources],
        disclosure=execution.disclosure,
        gaps=list(execution.gaps),
        changes=list(execution.changes),
        verification=list(execution.verification),
        diagnostics=list(execution.diagnostics),
        follow_up=execution.follow_up,
    )


def handle_request(request_kind: RequestKind, operation_key: str | None, raw_input: str) -> ServiceResult:
    general_discovery = request_kind == "capabilities" and operation_key is None
    parsed = parse_common_request(raw_input, general_discovery=general_discovery)
    if parsed.request is None:
        return invalid_request_result(request_kind, operation_key, parsed.problems)
    if operation_key is not None and not valid_operation_key(operation_key):
        return invalid_request_result(request_kind, operation_key, ("命令位置中的 operation_key 格式无效",))

    inspected = inspect_colocated_rule_source(Path(ldvh.__file__))
    if inspected.problem is not None:
        return _rule_source_unavailable(request_kind, operation_key, inspected.problem)
    assert inspected.repository is not None and inspected.operations is not None
    repository = inspected.repository
    operations = inspected.operations
    if repository.issues or repository.incomplete_scope or operations.issues or operations.incomplete_sources:
        summaries = [issue.summary for issue in (*repository.issues, *operations.issues)]
        affected = [*repository.incomplete_scope, *operations.incomplete_sources]
        problem = "规则源或公开操作声明检查存在未完成范围"
        return common_response(
            request_kind=request_kind,
            operation_key=operation_key,
            outcome="unavailable",
            summary="当前进程未能完整检查规则源",
            requested_scope=[] if operation_key is None else [operation_key],
            not_completed_scope=affected or ([] if operation_key is None else [operation_key]),
            sources=CONTRACT_SOURCES,
            gaps=[gap(problem, scope=affected, sources=CONTRACT_SOURCES)],
            diagnostics=[diagnostic("规则源机械检查未通过", issues=summaries)],
        )

    unchecked_conditions = tuple(dict.fromkeys(operations.unchecked_conditions))
    contract_conditions = tuple(dict.fromkeys(operations.contract_conditions))
    qualification_gaps = [
        *_qualification_gaps(unchecked_conditions, sources=[RULE_SOURCE_QUALIFICATION_SOURCE]),
        *_qualification_gaps(contract_conditions, sources=CONTRACT_SOURCES),
    ]
    declarations = operations.candidate_declarations
    runtime = bind_operation_implementations(operations, OPERATION_IMPLEMENTATIONS)
    bound_by_key = runtime.by_key()
    runtime_diagnostics = implementation_contract_diagnostics(runtime)
    observed_at = datetime.now().astimezone().isoformat()

    if operation_key is not None:
        bound_operation = bound_by_key.get(operation_key)
        if bound_operation is None:
            return invalid_request_result(
                request_kind,
                operation_key,
                (f"当前规则源未定义公开操作 {operation_key!r}",),
            )
        declaration = bound_operation.declaration
        implementation = bound_operation.implementation
        declaration_source = _declaration_source(declaration)
        operation_gap = gap(
            "当前 Code 尚未发现该公开操作的实际实现及可复核能力依据",
            scope=[operation_key],
            sources=[declaration_source],
        )
        if request_kind == "call" and implementation is None:
            return common_response(
                request_kind="call",
                operation_key=operation_key,
                outcome="unavailable",
                summary="公开操作已经定义，但当前没有可调用的实现与能力依据",
                requested_scope=[operation_key],
                not_completed_scope=[operation_key],
                sources=[*CONTRACT_SOURCES, declaration_source, RULE_SOURCE_QUALIFICATION_SOURCE],
                gaps=[operation_gap, *qualification_gaps],
                diagnostics=runtime_diagnostics,
            )
        if request_kind == "call":
            assert implementation is not None
            try:
                execution = implementation.call(parsed.request, repository)
            except Exception as error:  # noqa: BLE001 - service boundary converts implementation failures
                execution = implementation_error_execution(bound_operation, error)
            return _execution_response("call", operation_key, declaration_source, execution)

        availability = None
        available_scope: list[object] = []
        unavailable_scope: list[object] = []
        availability_gaps: list[dict[str, Any]] = []
        if implementation is not None:
            try:
                evaluated = implementation.check_availability(parsed.request, repository)
                availability = evaluated.availability
                available_scope = list(evaluated.available_scope)
                unavailable_scope = list(evaluated.unavailable_scope)
                availability_gaps = list(evaluated.gaps)
            except Exception as error:  # noqa: BLE001 - service boundary converts implementation failures
                execution = implementation_error_execution(bound_operation, error)
                return _execution_response("capabilities", operation_key, declaration_source, execution)
        operation = _operation_item(
            declaration,
            observed_at=observed_at,
            request_check=True,
            rule_source_conditions=unchecked_conditions,
            contract_conditions=contract_conditions,
            implementation=implementation,
            availability=availability,
            available_scope=available_scope,
            unavailable_scope=unavailable_scope,
            availability_gaps=availability_gaps,
        )
        return common_response(
            request_kind="capabilities",
            operation_key=operation_key,
            outcome="ok",
            summary="已完成公开操作的当次可用性检查",
            result={"mode": "request_check", "operations": [operation]},
            requested_scope=[operation_key],
            completed_scope=[operation_key],
            sources=[*CONTRACT_SOURCES, declaration_source, RULE_SOURCE_QUALIFICATION_SOURCE],
            gaps=([operation_gap] if implementation is None else []) + qualification_gaps + availability_gaps,
            diagnostics=runtime_diagnostics,
        )

    discovered_operations = [
        _operation_item(
            declaration,
            observed_at=observed_at,
            request_check=False,
            rule_source_conditions=unchecked_conditions,
            contract_conditions=contract_conditions,
            implementation=bound_operation.implementation,
        )
        for bound_operation in runtime.operations
        for declaration in (bound_operation.declaration,)
    ]
    declaration_sources = [_declaration_source(declaration) for declaration in declarations]

    return common_response(
        request_kind="capabilities",
        operation_key=None,
        outcome="ok",
        summary=f"已完成当前规则源的公开操作发现；发现 {len(discovered_operations)} 项领域公开操作",
        result={"mode": "discovery", "operations": discovered_operations},
        completed_scope=[declaration.operation_key for declaration in declarations],
        sources=[*CONTRACT_SOURCES, *declaration_sources, RULE_SOURCE_QUALIFICATION_SOURCE],
        gaps=qualification_gaps,
        diagnostics=runtime_diagnostics,
    )
