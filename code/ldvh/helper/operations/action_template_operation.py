"""Expose source-declared action templates as read-only Helper operations."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal, assert_never

from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.action_template_request import (
    CANDIDATE_OPTIONAL_INPUTS,
    CANDIDATE_REQUIRED_INPUTS,
    CONTENT_OPTIONAL_INPUTS,
    CONTENT_REQUIRED_INPUTS,
    ActionTemplateRequest,
    parse_action_template_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.action_templates import (
    ActionTemplateDeclaration,
    ActionTemplateSourceInspection,
    inspect_action_template_sources,
)
from ldvh.specs.repository import RepositoryInspection

CANDIDATE_OPERATION_KEY = "read-action-template-candidates"
CONTENT_OPERATION_KEY = "read-action-template-content"
_CANDIDATE_CONTRACT = source_reference(
    "rule",
    "action-template-foundation::9.5 行动模板候选读取输入与结果",
)
_CONTENT_CONTRACT = source_reference(
    "rule",
    "action-template-foundation::9.6 行动模板内容读取输入与结果",
)
_IMPLEMENTATION_EVIDENCE = (
    source_reference(
        "implementation",
        "code/ldvh/helper/operations/action_template_operation.py",
    ),
)
SuggestedOutcome = Literal["ok", "partial", "unavailable"]


@dataclass(frozen=True, slots=True)
class _ReadResult:
    outcome: SuggestedOutcome
    items: tuple[dict[str, object], ...] | None
    requested: tuple[str, ...]
    completed: tuple[str, ...]
    not_completed: tuple[str, ...]
    unchecked_conditions: tuple[str, ...]
    sources: tuple[dict[str, object], ...]
    gaps: tuple[dict[str, object], ...]
    diagnostics: tuple[dict[str, object], ...]
    verification: tuple[dict[str, object], ...]


def _validated_request(request: CommonRequest, *, require_keys: bool) -> ActionTemplateRequest:
    parsed = parse_action_template_request(request, require_keys=require_keys)
    if parsed.request is None:
        contract = _CONTENT_CONTRACT if require_keys else _CANDIDATE_CONTRACT
        raise OperationRequestError(parsed.problems, sources=(contract,))
    return parsed.request


def _candidate_item(declaration: ActionTemplateDeclaration) -> dict[str, object]:
    return {
        "template_key": declaration.template_key,
        "summary": declaration.summary,
        "activation_hint": declaration.activation_hint,
        "source_key": declaration.source_key,
        "canonical_path": declaration.document.canonical_path,
        "definition_ref": f"{declaration.source_key}::{declaration.definition_heading.title}",
        "definition_heading": declaration.definition_heading.title,
        "definition_start_line": declaration.definition_start_line,
        "definition_end_line": declaration.definition_end_line,
    }


def _content(declaration: ActionTemplateDeclaration) -> str:
    """Deliver the executable template package, without duplicating the source body.

    A template's definition starts at its declared H2.  Its following sections contain
    verification, Human Gate, and Stop Conditions, so the normal path must include the
    remainder of this same source document.  Full source identity is still exposed by
    the candidate fields and source digest and can be expanded through the existing
    specification reader.
    """
    lines = declaration.document.markdown.raw_lines[declaration.definition_start_line - 1 :]
    return "\n".join(lines) + "\n"


def _inspection_issue_reference(issue) -> dict[str, object]:
    locator = issue.location.path if issue.location.line is None else f"{issue.location.path}:{issue.location.line}"
    reference = source_reference("rule", locator)
    if issue.location.heading is not None:
        reference["details"] = {"heading": issue.location.heading}
    return reference


def _inspection_disclosure(
    inspection: ActionTemplateSourceInspection,
    repository: RepositoryInspection,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    gaps: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    sources: list[dict[str, object]] = []
    source_paths = {document.key: document.canonical_path for document in repository.parsed_documents}
    for source_key in inspection.incomplete_sources:
        relevant = [issue for issue in inspection.issues if source_key in issue.affected]
        references = [_inspection_issue_reference(issue) for issue in relevant]
        if not references:
            references = [
                source_reference(
                    "rule",
                    source_paths.get(source_key, source_key),
                    source_key=source_key,
                )
            ]
        gaps.append(
            {
                "summary": f"行动模板声明来源 {source_key!r} 未通过全部机械检查；有效候选不代表该来源完整",
                "scope": [],
                "source_refs": references,
            }
        )
        sources.extend(references)
    for issue in inspection.issues:
        reference = _inspection_issue_reference(issue)
        details: dict[str, object] = {
            "path": issue.location.path,
            "line": issue.location.line,
            "affected": list(issue.affected),
        }
        if issue.cause is not None:
            details["cause"] = issue.cause
        diagnostics.append(
            {
                "summary": issue.summary,
                "details": details,
                "source_refs": [reference],
            }
        )
    return gaps, diagnostics, sources


def _read(
    request: CommonRequest,
    repository: RepositoryInspection,
    *,
    include_content: bool,
) -> _ReadResult:
    domain = _validated_request(request, require_keys=include_content)
    inspection = inspect_action_template_sources(repository)
    declarations = {item.template_key: item for item in inspection.candidate_declarations}
    select_all = not domain.template_keys
    selection = domain.template_keys or tuple(sorted(declarations))
    completed: list[str] = []
    missing: list[str] = []
    items: list[dict[str, object]] = []
    source_gaps, diagnostics, issue_sources = _inspection_disclosure(inspection, repository)
    sources: list[dict[str, object]] = list(issue_sources)
    gaps: list[dict[str, object]] = list(source_gaps)
    verification: list[dict[str, object]] = []
    for key in selection:
        declaration = declarations.get(key)
        if declaration is None:
            missing.append(key)
            if inspection.incomplete_sources:
                summary = f"当前无法从机械有效声明确认 template_key {key!r}；已披露的不完整来源可能遮蔽该候选"
            else:
                summary = f"未从当前有效行动模板声明精确匹配 template_key {key!r}"
            gaps.append(
                {
                    "summary": summary,
                    "scope": [key],
                    "source_refs": [_CONTENT_CONTRACT if include_content else _CANDIDATE_CONTRACT],
                }
            )
            continue
        item = _candidate_item(declaration)
        if include_content:
            content = _content(declaration)
            source_content = declaration.document.markdown.raw_text
            item["content"] = content
            item["content_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
            item["source_content_sha256"] = hashlib.sha256(source_content.encode("utf-8")).hexdigest()
        items.append(item)
        completed.append(key)
        source = source_reference(
            "rule",
            declaration.document.canonical_path,
            line=declaration.definition_start_line,
            source_key=declaration.source_key,
            template_key=key,
        )
        sources.append(source)
        verification.append(
            {
                "check": "action-template-content" if include_content else "action-template-candidate",
                "status": "passed",
                "scope": [key],
                "evidence": [source, *_IMPLEMENTATION_EVIDENCE],
            }
        )
    if completed and missing:
        outcome: SuggestedOutcome = "partial"
    elif missing and not completed:
        outcome = "unavailable"
    elif select_all and not completed and inspection.incomplete_sources:
        outcome = "unavailable"
    else:
        outcome = "ok"
    return _ReadResult(
        outcome=outcome,
        items=tuple(items) if items else (None if outcome == "unavailable" else ()),
        requested=selection,
        completed=tuple(completed),
        not_completed=tuple(missing),
        unchecked_conditions=tuple(dict.fromkeys(inspection.unchecked_conditions)),
        sources=tuple(sources),
        gaps=tuple(gaps),
        diagnostics=tuple(diagnostics),
        verification=tuple(verification),
    )


def _availability(result: _ReadResult) -> AvailabilityEvaluation:
    if result.outcome == "ok":
        availability = "available_for_request"
    elif result.outcome == "partial":
        availability = "partially_available"
    elif result.outcome == "unavailable":
        availability = "unavailable_for_request"
    else:
        assert_never(result.outcome)
    return AvailabilityEvaluation(
        availability=availability,
        available_scope=result.completed,
        unavailable_scope=result.not_completed,
        gaps=result.gaps,
    )


def _execution(result: _ReadResult, repository: RepositoryInspection, *, include_content: bool) -> OperationExecution:
    del repository
    if result.outcome == "ok":
        summary = "已精确读取行动模板定义内容" if include_content else "已读取当前行动模板机械候选"
    elif result.outcome == "partial":
        summary = "已读取部分行动模板范围，并保留未完成 key"
    else:
        summary = "当前没有请求范围能够形成可信的行动模板读取结果"
    payload: dict[str, object] | None
    if result.items is None:
        payload = None
    elif include_content:
        payload = {"items": list(result.items)}
    else:
        payload = {
            "items": list(result.items),
            "unchecked_conditions": list(result.unchecked_conditions),
        }
    return OperationExecution(
        outcome=result.outcome,
        summary=summary,
        result=payload,
        requested_scope=result.requested,
        completed_scope=result.completed,
        not_completed_scope=result.not_completed,
        sources=(*result.sources, *_IMPLEMENTATION_EVIDENCE),
        gaps=result.gaps,
        diagnostics=result.diagnostics,
        verification=result.verification,
    )


def _candidate_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    del context
    return _availability(_read(request, repository, include_content=False))


def _candidate_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    del context
    return _execution(_read(request, repository, include_content=False), repository, include_content=False)


def _content_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    del context
    return _availability(_read(request, repository, include_content=True))


def _content_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    del context
    return _execution(_read(request, repository, include_content=True), repository, include_content=True)


ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION = OperationImplementation(
    required_inputs=CANDIDATE_REQUIRED_INPUTS,
    optional_inputs=CANDIDATE_OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_candidate_availability,
    call=_candidate_call,
    response_fields=("items", "unchecked_conditions"),
)
ACTION_TEMPLATE_CONTENT_IMPLEMENTATION = OperationImplementation(
    required_inputs=CONTENT_REQUIRED_INPUTS,
    optional_inputs=CONTENT_OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_content_availability,
    call=_content_call,
    response_fields=("items",),
)


__all__ = [
    "ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION",
    "ACTION_TEMPLATE_CONTENT_IMPLEMENTATION",
    "CANDIDATE_OPERATION_KEY",
    "CONTENT_OPERATION_KEY",
]
