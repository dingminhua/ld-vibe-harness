"""Thin Helper service orchestration for the public foundational commands."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import ldvh
from ldvh.diagnostics import Issue
from ldvh.helper.operation_runtime import (
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
    bind_operation_implementations,
    implementation_contract_diagnostics,
    implementation_error_execution,
)
from ldvh.helper.operation_sources import OperationDeclarationCandidate
from ldvh.helper.operations import IMPLEMENTATIONS
from ldvh.helper.requests import parse_common_request, valid_operation_key
from ldvh.helper.responses import RequestKind, ServiceResult, common_response, diagnostic, gap, source_reference
from ldvh.helper.rule_source import inspect_colocated_rule_source
from ldvh.helper.source_refs import RuleReferenceBinder, reset_reference_binder, set_reference_binder
from ldvh.specs.source import RuleSourceIdentity

CONTRACT_SOURCES = [
    source_reference("rule", "specs/04-Helper CLI 服务规范.md"),
    source_reference("rule", "specs/attachments/04.Att.01-Helper CLI 请求与响应字段表.md"),
]
RULE_SOURCE_QUALIFICATION_SOURCE = source_reference("rule", "specs/01-规范模型基础规范.md")
OPERATION_IMPLEMENTATIONS: dict[str, OperationImplementation] = dict(IMPLEMENTATIONS)


def _issue_source(issue: Issue) -> dict[str, Any]:
    locator = issue.location.path if issue.location.line is None else f"{issue.location.path}:{issue.location.line}"
    details = {} if issue.location.heading is None else {"heading": issue.location.heading}
    return source_reference("rule", locator, **details)


def _issue_sources(issues: tuple[Issue, ...]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for issue in issues:
        source = _issue_source(issue)
        identity = (str(source["kind"]), str(source["locator"]))
        if identity not in seen:
            seen.add(identity)
            results.append(source)
    return results


def _issue_diagnostic(issue: Issue) -> dict[str, Any]:
    details: dict[str, Any] = {
        "path": issue.location.path,
        "line": issue.location.line,
        "affected": list(issue.affected),
    }
    if issue.cause is not None:
        details["cause"] = issue.cause
    result = diagnostic(issue.summary, **details)
    result["source_refs"] = [_issue_source(issue)]
    return result


def invalid_request_result(
    request_kind: RequestKind,
    operation_key: str | None,
    problems: tuple[str, ...],
    *,
    sources: list[dict[str, Any]] | None = None,
    response_profile: str = "compact",
) -> ServiceResult:
    response_sources = CONTRACT_SOURCES if sources is None else [*CONTRACT_SOURCES, *sources]
    return common_response(
        request_kind=request_kind,
        operation_key=operation_key,
        outcome="invalid_request",
        summary="Helper 请求不符合共同接口契约",
        response_profile=response_profile,
        requested_scope=[] if operation_key is None else [operation_key],
        not_completed_scope=[] if operation_key is None else [operation_key],
        sources=response_sources,
        gaps=[gap(problem, sources=response_sources) for problem in problems],
        diagnostics=[diagnostic("请求解析或校验未通过", problems=list(problems))],
    )


def _rule_source_unavailable(
    request_kind: RequestKind,
    operation_key: str | None,
    problem: str,
    *,
    response_profile: str,
) -> ServiceResult:
    return common_response(
        request_kind=request_kind,
        operation_key=operation_key,
        outcome="unavailable",
        summary="当前进程无法形成可信的规则源发现结果",
        response_profile=response_profile,
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
    response_profile: str = "compact",
) -> list[dict[str, Any]]:
    unique_conditions = tuple(dict.fromkeys(conditions))
    if not unique_conditions:
        return []
    if response_profile == "compact":
        return [
            gap(
                f"当前 Code 尚未自动证明 {len(unique_conditions)} 项资格条件；请求 diagnostic 档可读取逐项明细",
                scope=scope,
                sources=sources,
            )
        ]
    return [
        gap(
            f"当前 Code 尚未自动证明：{condition}",
            scope=scope,
            sources=sources,
        )
        for condition in unique_conditions
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
    response_profile: str = "compact",
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
            response_profile=response_profile,
        ),
        *_qualification_gaps(
            contract_conditions,
            sources=CONTRACT_SOURCES,
            scope=operation_scope,
            response_profile=response_profile,
        ),
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
    *,
    response_profile: str,
) -> ServiceResult:
    return common_response(
        request_kind=request_kind,
        operation_key=operation_key,
        outcome=execution.outcome,
        summary=execution.summary,
        response_profile=response_profile,
        result=execution.result,
        requested_scope=list(execution.requested_scope),
        completed_scope=list(execution.completed_scope),
        not_completed_scope=list(execution.not_completed_scope),
        governance_resolution=execution.governance_resolution,
        sources=[*CONTRACT_SOURCES, declaration_source, *execution.sources],
        disclosure=execution.disclosure,
        gaps=list(execution.gaps),
        changes=list(execution.changes),
        verification=list(execution.verification),
        diagnostics=list(execution.diagnostics),
        follow_up=execution.follow_up,
    )


def handle_request(request_kind: RequestKind, operation_key: str | None, raw_input: str) -> ServiceResult:
    token = set_reference_binder(None)
    try:
        return _handle_request(request_kind, operation_key, raw_input)
    finally:
        reset_reference_binder(token)


def _handle_request(request_kind: RequestKind, operation_key: str | None, raw_input: str) -> ServiceResult:
    execution_context = OperationExecutionContext(cwd=Path.cwd())
    general_discovery = request_kind == "capabilities" and operation_key is None
    parsed = parse_common_request(raw_input, general_discovery=general_discovery)
    if parsed.request is None:
        return invalid_request_result(request_kind, operation_key, parsed.problems)
    response_profile = parsed.request.response_profile
    if operation_key is not None and not valid_operation_key(operation_key):
        return invalid_request_result(
            request_kind,
            operation_key,
            ("命令位置中的 operation_key 格式无效",),
            response_profile=response_profile,
        )

    inspected = inspect_colocated_rule_source(Path(ldvh.__file__))
    if inspected.problem is not None:
        return _rule_source_unavailable(
            request_kind,
            operation_key,
            inspected.problem,
            response_profile=response_profile,
        )
    assert inspected.repository is not None and inspected.operations is not None
    repository = inspected.repository
    identity = repository.source_identity or RuleSourceIdentity(
        "working_tree",
        git_worktree_root=repository.repository_root.resolve(),
    )
    set_reference_binder(RuleReferenceBinder(identity, repository.parsed_documents))
    operations = inspected.operations
    operation_only_issues = tuple(issue for issue in operations.issues if issue not in repository.issues)
    operation_only_incomplete = tuple(
        scope for scope in operations.incomplete_sources if scope not in repository.incomplete_scope
    )
    declarations = operations.candidate_declarations
    repository_incomplete = bool(repository.issues or repository.incomplete_scope)
    declaration_incomplete = bool(operation_only_issues or operation_only_incomplete)
    if declaration_incomplete or (repository_incomplete and not declarations):
        blocking_issues = (*repository.issues, *operation_only_issues)
        issue_sources = _issue_sources(blocking_issues)
        affected = [*repository.incomplete_scope, *operation_only_incomplete]
        problem = "规则源或公开操作声明检查存在未完成范围"
        return common_response(
            request_kind=request_kind,
            operation_key=operation_key,
            outcome="unavailable",
            summary="当前进程未能完整检查规则源",
            response_profile=response_profile,
            requested_scope=[] if operation_key is None else [operation_key],
            not_completed_scope=affected or ([] if operation_key is None else [operation_key]),
            sources=[*CONTRACT_SOURCES, *issue_sources],
            gaps=[gap(problem, scope=affected, sources=[*CONTRACT_SOURCES, *issue_sources])],
            diagnostics=[_issue_diagnostic(issue) for issue in blocking_issues],
        )

    unchecked_conditions = tuple(dict.fromkeys(operations.unchecked_conditions))
    contract_conditions = tuple(dict.fromkeys(operations.contract_conditions))
    qualification_gaps = [
        *_qualification_gaps(
            unchecked_conditions,
            sources=[RULE_SOURCE_QUALIFICATION_SOURCE],
            response_profile=response_profile,
        ),
        *_qualification_gaps(
            contract_conditions,
            sources=CONTRACT_SOURCES,
            response_profile=response_profile,
        ),
    ]
    runtime = bind_operation_implementations(operations, OPERATION_IMPLEMENTATIONS)
    bound_by_key = runtime.by_key()
    runtime_diagnostics = implementation_contract_diagnostics(runtime)
    observed_at = datetime.now().astimezone().isoformat()

    if operation_key is not None:
        bound_operation = bound_by_key.get(operation_key)
        if bound_operation is None:
            if repository_incomplete:
                repository_sources = _issue_sources(repository.issues)
                return common_response(
                    request_kind=request_kind,
                    operation_key=operation_key,
                    outcome="unavailable",
                    summary="当前规则源存在未完成范围，无法确定请求的操作是否已由来源定义",
                    response_profile=response_profile,
                    requested_scope=[operation_key],
                    not_completed_scope=[operation_key, *repository.incomplete_scope],
                    sources=[*CONTRACT_SOURCES, *repository_sources],
                    gaps=[
                        gap(
                            "规则源未完成范围可能影响公开操作身份判断",
                            scope=[operation_key, *repository.incomplete_scope],
                            sources=[*CONTRACT_SOURCES, *repository_sources],
                        )
                    ],
                    diagnostics=[_issue_diagnostic(issue) for issue in repository.issues],
                )
            return invalid_request_result(
                request_kind,
                operation_key,
                (f"当前规则源未定义公开操作 {operation_key!r}",),
                response_profile=response_profile,
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
                response_profile=response_profile,
                requested_scope=[operation_key],
                not_completed_scope=[operation_key],
                sources=[*CONTRACT_SOURCES, declaration_source, RULE_SOURCE_QUALIFICATION_SOURCE],
                gaps=[operation_gap, *qualification_gaps],
                diagnostics=runtime_diagnostics,
            )
        if request_kind == "call":
            assert implementation is not None
            try:
                execution = implementation.call(parsed.request, repository, execution_context)
            except OperationRequestError as error:
                return invalid_request_result(
                    "call",
                    operation_key,
                    error.problems,
                    sources=list(error.sources),
                    response_profile=response_profile,
                )
            except Exception as error:  # noqa: BLE001 - service boundary converts implementation failures
                execution = implementation_error_execution(bound_operation, error)
            return _execution_response(
                "call",
                operation_key,
                declaration_source,
                execution,
                response_profile=response_profile,
            )

        availability = None
        available_scope: list[object] = []
        unavailable_scope: list[object] = []
        availability_gaps: list[dict[str, Any]] = []
        if implementation is not None:
            try:
                evaluated = implementation.check_availability(parsed.request, repository, execution_context)
                availability = evaluated.availability
                available_scope = list(evaluated.available_scope)
                unavailable_scope = list(evaluated.unavailable_scope)
                availability_gaps = list(evaluated.gaps)
            except OperationRequestError as error:
                return invalid_request_result(
                    "capabilities",
                    operation_key,
                    error.problems,
                    sources=list(error.sources),
                    response_profile=response_profile,
                )
            except Exception as error:  # noqa: BLE001 - service boundary converts implementation failures
                execution = implementation_error_execution(bound_operation, error)
                return _execution_response(
                    "capabilities",
                    operation_key,
                    declaration_source,
                    execution,
                    response_profile=response_profile,
                )
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
            response_profile=response_profile,
        )
        return common_response(
            request_kind="capabilities",
            operation_key=operation_key,
            outcome="ok",
            summary="已完成公开操作的当次可用性检查",
            response_profile=response_profile,
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
            response_profile=response_profile,
        )
        for bound_operation in runtime.operations
        for declaration in (bound_operation.declaration,)
    ]
    declaration_sources = [_declaration_source(declaration) for declaration in declarations]
    repository_sources = _issue_sources(repository.issues)

    return common_response(
        request_kind="capabilities",
        operation_key=None,
        outcome="partial" if repository_incomplete else "ok",
        summary=(
            f"已完成部分当前规则源的公开操作发现；发现 {len(discovered_operations)} 项领域公开操作"
            if repository_incomplete
            else f"已完成当前规则源的公开操作发现；发现 {len(discovered_operations)} 项领域公开操作"
        ),
        response_profile=response_profile,
        result={"mode": "discovery", "operations": discovered_operations},
        completed_scope=[declaration.operation_key for declaration in declarations],
        not_completed_scope=list(repository.incomplete_scope),
        sources=[
            *CONTRACT_SOURCES,
            *declaration_sources,
            RULE_SOURCE_QUALIFICATION_SOURCE,
            *repository_sources,
        ],
        gaps=(
            qualification_gaps
            + (
                [
                    gap(
                        "规则源存在未完成候选范围；已发现操作不覆盖这些范围",
                        scope=list(repository.incomplete_scope),
                        sources=[*CONTRACT_SOURCES, *repository_sources],
                    )
                ]
                if repository_incomplete
                else []
            )
        ),
        diagnostics=runtime_diagnostics
        + ([_issue_diagnostic(issue) for issue in repository.issues] if repository_incomplete else []),
    )
