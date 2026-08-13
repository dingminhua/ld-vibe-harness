"""Parse closed requests for read-only local edit candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.facts.models import FactReference, StableFactReference
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.fact_reference_support import parse_stable_fact_reference
from ldvh.helper.requests import CommonRequest

SourceKind = Literal["rule", "study"]

REQUIRED_INPUTS = ("arguments.source_kind",)
OPTIONAL_INPUTS = (
    "arguments.responsibility_key",
    "arguments.heading_path",
    "arguments.fact_ref",
    "arguments.body_heading",
    "arguments.expected_baseline",
    "arguments.candidate_after",
    "work_object_locators",
)

_ARGUMENT_FIELDS = frozenset(
    {
        "source_kind",
        "responsibility_key",
        "heading_path",
        "fact_ref",
        "body_heading",
        "expected_baseline",
        "candidate_after",
    }
)
_STUDY_BODY_HEADINGS = frozenset({"研究问题", "输入与边界", "关键发现", "建议", "后续分流"})


@dataclass(frozen=True, slots=True)
class RuleLocalEditRequest:
    responsibility_key: str
    heading_path: tuple[str, ...]
    expected_baseline: str | None
    candidate_after: str | None


@dataclass(frozen=True, slots=True)
class StudyLocalEditRequest:
    fact_ref: StableFactReference
    body_heading: str
    expected_baseline: str | None
    candidate_after: str | None
    governance_scope: tuple[ScopeDescriptor, ...]
    base: Path


@dataclass(frozen=True, slots=True)
class LocalEditRequest:
    source_kind: SourceKind
    rule: RuleLocalEditRequest | None = None
    study: StudyLocalEditRequest | None = None


@dataclass(frozen=True, slots=True)
class LocalEditRequestParseResult:
    request: LocalEditRequest | None
    problems: tuple[str, ...]


def _optional_hash(value: object, *, prefix: str, problems: list[str]) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        problems.append(f"{prefix} 必须是 null 或 64 位小写十六进制 string")
        return None
    return value


def _optional_candidate(value: object, *, prefix: str, problems: list[str]) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        problems.append(f"{prefix} 必须是 null 或非空 string")
        return None
    return value


def _rule_request(request: CommonRequest, problems: list[str]) -> RuleLocalEditRequest | None:
    forbidden = sorted({"fact_ref", "body_heading"} & set(request.arguments))
    if forbidden:
        problems.append(f"source_kind=rule 禁止字段: {', '.join(forbidden)}")
    if request.work_object_locators:
        problems.append("source_kind=rule 不接受 work_object_locators")

    responsibility_key = request.arguments.get("responsibility_key")
    if not isinstance(responsibility_key, str) or not responsibility_key:
        problems.append("arguments.responsibility_key 在 source_kind=rule 时必须是非空 string")

    raw_path = request.arguments.get("heading_path")
    heading_path: tuple[str, ...] = ()
    if not isinstance(raw_path, list) or len(raw_path) not in {1, 2}:
        problems.append("arguments.heading_path 在 source_kind=rule 时必须是长度为 1 或 2 的 string array")
    else:
        values: list[str] = []
        for index, heading in enumerate(raw_path):
            if not isinstance(heading, str) or not heading:
                problems.append(f"arguments.heading_path[{index}] 必须是非空 string")
                continue
            if heading != heading.strip():
                problems.append(f"arguments.heading_path[{index}] 不得带首尾空白")
            values.append(heading)
        heading_path = tuple(values)

    expected = _optional_hash(
        request.arguments.get("expected_baseline"), prefix="arguments.expected_baseline", problems=problems
    )
    candidate = _optional_candidate(
        request.arguments.get("candidate_after"), prefix="arguments.candidate_after", problems=problems
    )
    if problems or not isinstance(responsibility_key, str) or not responsibility_key or not heading_path:
        return None
    return RuleLocalEditRequest(responsibility_key, heading_path, expected, candidate)


def _study_request(
    request: CommonRequest,
    context: OperationExecutionContext,
    problems: list[str],
) -> StudyLocalEditRequest | None:
    forbidden = sorted({"responsibility_key", "heading_path"} & set(request.arguments))
    if forbidden:
        problems.append(f"source_kind=study 禁止字段: {', '.join(forbidden)}")

    locators: list[str] = []
    for index, locator in enumerate(request.work_object_locators):
        if not isinstance(locator, str) or not locator:
            problems.append(f"work_object_locators[{index}] 必须是非空路径 string")
        else:
            locators.append(locator)

    fact_ref, reference_problems = parse_stable_fact_reference(
        request.arguments.get("fact_ref"), "arguments.fact_ref"
    )
    problems.extend(reference_problems)
    if isinstance(fact_ref, FactReference) and fact_ref.fact_type_key != "study":
        problems.append("arguments.fact_ref.fact_type_key 在 source_kind=study 时必须精确等于 study")

    body_heading = request.arguments.get("body_heading")
    if body_heading not in _STUDY_BODY_HEADINGS:
        expected_titles = "、".join(sorted(_STUDY_BODY_HEADINGS))
        problems.append(f"arguments.body_heading 在 source_kind=study 时只允许: {expected_titles}")

    expected = _optional_hash(
        request.arguments.get("expected_baseline"), prefix="arguments.expected_baseline", problems=problems
    )
    candidate = _optional_candidate(
        request.arguments.get("candidate_after"), prefix="arguments.candidate_after", problems=problems
    )
    if not context.cwd.is_absolute():
        problems.append("Helper 进程实际 cwd 必须是绝对路径")
    if problems or fact_ref is None or not isinstance(body_heading, str):
        return None
    scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return StudyLocalEditRequest(
        fact_ref,
        body_heading,
        expected,
        candidate,
        scope,
        context.cwd,
    )


def parse_local_edit_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> LocalEditRequestParseResult:
    """Validate the source-kind-discriminated read-only request."""

    problems: list[str] = []
    unknown = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")
    if request.observed_context:
        problems.append("observed_context 对本操作必须为空 object")
    if request.authorization_reference:
        problems.append("authorization_reference 对本只读操作必须为空 array")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对本操作必须为 null 或省略")

    source_kind = request.arguments.get("source_kind")
    if source_kind not in {"rule", "study"}:
        problems.append("arguments.source_kind 必须精确为 rule 或 study")
        return LocalEditRequestParseResult(None, tuple(problems))
    if source_kind == "rule":
        rule = _rule_request(request, problems)
        return LocalEditRequestParseResult(None if problems else LocalEditRequest("rule", rule=rule), tuple(problems))
    study = _study_request(request, context, problems)
    return LocalEditRequestParseResult(None if problems else LocalEditRequest("study", study=study), tuple(problems))


__all__ = [
    "LocalEditRequest",
    "LocalEditRequestParseResult",
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "RuleLocalEditRequest",
    "StudyLocalEditRequest",
    "parse_local_edit_request",
]
