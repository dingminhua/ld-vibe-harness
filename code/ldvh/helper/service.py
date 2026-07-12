"""Thin Helper service orchestration for the public foundational commands."""

from __future__ import annotations

from pathlib import Path

import ldvh
from ldvh.helper.requests import parse_common_request, valid_operation_key
from ldvh.helper.responses import RequestKind, ServiceResult, common_response, diagnostic, gap, source_reference
from ldvh.helper.rule_source import inspect_colocated_rule_source

CONTRACT_SOURCES = [
    source_reference("rule", "specs/04-Helper CLI 服务契约规范.md"),
    source_reference("rule", "specs/attachments/04.Att.01-Helper CLI 请求与响应字段表.md"),
]
RULE_SOURCE_QUALIFICATION_SOURCE = source_reference("rule", "specs/01-规范模型基础规范.md")


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

    declarations = operations.candidate_declarations
    if declarations:
        return _rule_source_unavailable(
            request_kind,
            operation_key,
            "发现了领域公开操作声明候选，但本增量尚未实现其完整输入契约与实现依据发现",
        )

    if operation_key is not None:
        return invalid_request_result(request_kind, operation_key, (f"当前规则源未定义公开操作 {operation_key!r}",))

    unchecked_conditions = tuple(dict.fromkeys(operations.unchecked_conditions))
    qualification_gaps = [
        gap(
            f"当前 Code 尚未自动证明：{condition}",
            sources=[RULE_SOURCE_QUALIFICATION_SOURCE],
        )
        for condition in unchecked_conditions
    ]

    return common_response(
        request_kind="capabilities",
        operation_key=None,
        outcome="ok",
        summary="已完成当前规则源的公开操作发现；当前没有领域公开操作",
        result={"mode": "discovery", "operations": []},
        completed_scope=[],
        sources=[*CONTRACT_SOURCES, RULE_SOURCE_QUALIFICATION_SOURCE],
        gaps=qualification_gaps,
    )
