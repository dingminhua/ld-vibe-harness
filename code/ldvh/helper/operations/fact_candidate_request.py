"""Parse the source-defined find-fact-object-candidates request."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactReference
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS = ("arguments.governed_project_id", "arguments.card_layer")
OPTIONAL_INPUTS = (
    "work_object_locators",
    "arguments.workspace_root",
    "arguments.fact_type_keys",
    "arguments.statuses",
    "arguments.exact_refs",
    "arguments.relation_targets",
    "arguments.current_workcase_ref",
    "arguments.selected_fact_refs",
    "arguments.locator_text",
    "arguments.text_match",
    "arguments.page_size",
    "arguments.cursor",
)

_ARGUMENT_FIELDS = frozenset(
    {
        "workspace_root",
        "governed_project_id",
        "card_layer",
        "fact_type_keys",
        "statuses",
        "exact_refs",
        "relation_targets",
        "current_workcase_ref",
        "selected_fact_refs",
        "locator_text",
        "text_match",
        "page_size",
        "cursor",
    }
)
_REFERENCE_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})
_TEXT_MATCH_FIELDS = frozenset({"text", "field_paths"})
_F2_FIELDS = {
    "spark": frozenset({"object_id", "title", "status", "summary", "priority", "updated_at"}),
    "workcase": frozenset(
        {
            "object_id",
            "title",
            "status",
            "phase",
            "goal",
            "scope",
            "summary",
            "priority",
            "blocking_summary",
            "updated_at",
        }
    ),
    "adr": frozenset({"object_id", "title", "status", "decision_question", "decision", "applicability", "updated_at"}),
    "pitfall": frozenset(
        {
            "object_id",
            "title",
            "status",
            "symptoms",
            "trigger_conditions",
            "applicability",
            "validation_summary",
            "updated_at",
        }
    ),
    "study": frozenset(
        {
            "object_id",
            "title",
            "status",
            "research_question",
            "abstract",
            "applicability",
            "validation_summary",
            "updated_at",
        }
    ),
}
_F2_ONLY_FIELDS = frozenset(
    {
        "fact_type_keys",
        "statuses",
        "exact_refs",
        "relation_targets",
        "locator_text",
        "text_match",
    }
)


@dataclass(frozen=True, slots=True)
class TextMatch:
    text: str
    field_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FactCandidateRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    governed_project_id: str
    card_layer: Literal["F1", "F2"]
    fact_type_keys: tuple[str, ...]
    statuses: tuple[str, ...] | None
    exact_refs: tuple[FactReference, ...]
    relation_targets: tuple[FactReference, ...]
    current_workcase_ref: FactReference | None
    selected_fact_refs: tuple[FactReference, ...]
    locator_text: str | None
    text_match: TextMatch | None
    page_size: int
    cursor: str | None
    base: Path


@dataclass(frozen=True, slots=True)
class FactCandidateRequestParseResult:
    request: FactCandidateRequest | None
    problems: tuple[str, ...]


def _unique_strings(value: object, path: str, *, minimum: int, maximum: int) -> tuple[tuple[str, ...], list[str]]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        return (), [f"{path} 必须是包含 {minimum}–{maximum} 项的 array"]
    problems: list[str] = []
    strings: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            problems.append(f"{path}[{index}] 必须是非空 string")
        else:
            strings.append(item)
    if len(strings) != len(set(strings)):
        problems.append(f"{path} 不得包含重复成员")
    return tuple(strings), problems


def _references(
    value: object,
    path: str,
    governed_project_id: str | None,
    selected_types: tuple[str, ...],
) -> tuple[tuple[FactReference, ...], list[str]]:
    if not isinstance(value, list) or not 1 <= len(value) <= 128:
        return (), [f"{path} 必须是包含 1–128 项的 array"]
    problems: list[str] = []
    references: list[FactReference] = []
    for index, item in enumerate(value):
        prefix = f"{path}[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{prefix} 必须是 object")
            continue
        unknown = sorted(set(item) - _REFERENCE_FIELDS)
        if unknown:
            problems.append(f"{prefix} 包含未知字段: {', '.join(unknown)}")
        values: dict[str, str] = {}
        for field in sorted(_REFERENCE_FIELDS):
            raw = item.get(field)
            if not isinstance(raw, str) or not raw:
                problems.append(f"{prefix}.{field} 必须是非空 string")
            else:
                values[field] = raw
        if len(values) != 3:
            continue
        layout = LAYOUTS.get(values["fact_type_key"])
        if layout is None or layout.object_id_pattern.fullmatch(values["object_id"]) is None:
            problems.append(f"{prefix} 未形成当前类型的合法稳定引用")
            continue
        if governed_project_id is not None and values["governed_project_id"] != governed_project_id:
            problems.append(f"{prefix}.governed_project_id 必须等于 arguments.governed_project_id")
        if selected_types and values["fact_type_key"] not in selected_types:
            problems.append(f"{prefix}.fact_type_key 必须位于 arguments.fact_type_keys")
        references.append(FactReference(values["governed_project_id"], values["fact_type_key"], values["object_id"]))
    identities = [(item.governed_project_id, item.fact_type_key, item.object_id) for item in references]
    if len(identities) != len(set(identities)):
        problems.append(f"{path} 不得包含重复稳定引用")
    return tuple(references), problems


def parse_fact_candidate_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> FactCandidateRequestParseResult:
    problems: list[str] = []
    if not context.cwd.is_absolute():
        problems.append("Helper 进程实际 cwd 必须是绝对路径")
    locators: list[str] = []
    for index, locator in enumerate(request.work_object_locators):
        if not isinstance(locator, str) or not locator:
            problems.append(f"work_object_locators[{index}] 必须是非空路径 string")
        else:
            locators.append(locator)
    unknown = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")

    workspace_root: Path | None = None
    if "workspace_root" in request.arguments:
        raw = request.arguments["workspace_root"]
        if not isinstance(raw, str) or not raw or not Path(raw).is_absolute():
            problems.append("arguments.workspace_root 必须是非空绝对路径 string")
        else:
            workspace_root = Path(raw)
    project_value = request.arguments.get("governed_project_id")
    project_id = project_value if isinstance(project_value, str) and project_value else None
    if project_id is None:
        problems.append("arguments.governed_project_id 必须是非空 string")
    layer_value = request.arguments.get("card_layer")
    layer: Literal["F1", "F2"] | None = layer_value if layer_value in {"F1", "F2"} else None
    if layer is None:
        problems.append("arguments.card_layer 只允许 F1 或 F2")

    fact_type_keys: tuple[str, ...] = ()
    if layer == "F2":
        fact_type_keys, type_problems = _unique_strings(
            request.arguments.get("fact_type_keys"), "arguments.fact_type_keys", minimum=1, maximum=5
        )
        problems.extend(type_problems)
        unknown_types = sorted(set(fact_type_keys) - set(LAYOUTS))
        if unknown_types:
            problems.append(f"arguments.fact_type_keys 包含未知类型: {', '.join(unknown_types)}")
    elif layer == "F1":
        present = sorted(_F2_ONLY_FIELDS & set(request.arguments))
        if present:
            problems.append(f"F1 不接受 F2 过滤字段: {', '.join(present)}")
        fact_type_keys = ("adr", "workcase")

    statuses: tuple[str, ...] | None = None
    if layer == "F2" and "statuses" in request.arguments:
        statuses, status_problems = _unique_strings(
            request.arguments["statuses"], "arguments.statuses", minimum=1, maximum=9
        )
        problems.extend(status_problems)
        allowed = set().union(*(LAYOUTS[key].statuses for key in fact_type_keys if key in LAYOUTS))
        invalid = sorted(set(statuses) - allowed)
        if invalid:
            problems.append(f"arguments.statuses 包含所选类型不允许的状态: {', '.join(invalid)}")

    exact_refs: tuple[FactReference, ...] = ()
    if layer == "F2" and "exact_refs" in request.arguments:
        exact_refs, reference_problems = _references(
            request.arguments["exact_refs"], "arguments.exact_refs", project_id, fact_type_keys
        )
        problems.extend(reference_problems)
    relation_targets: tuple[FactReference, ...] = ()
    if layer == "F2" and "relation_targets" in request.arguments:
        relation_targets, reference_problems = _references(
            request.arguments["relation_targets"], "arguments.relation_targets", project_id, ()
        )
        problems.extend(reference_problems)

    current_workcase_ref: FactReference | None = None
    if "current_workcase_ref" in request.arguments:
        current_refs, reference_problems = _references(
            [request.arguments["current_workcase_ref"]],
            "arguments.current_workcase_ref",
            project_id,
            ("workcase",),
        )
        problems.extend(reference_problems)
        if current_refs:
            current_workcase_ref = current_refs[0]
    selected_fact_refs: tuple[FactReference, ...] = ()
    if "selected_fact_refs" in request.arguments:
        selected_fact_refs, reference_problems = _references(
            request.arguments["selected_fact_refs"],
            "arguments.selected_fact_refs",
            project_id,
            (),
        )
        problems.extend(reference_problems)

    locator_text: str | None = None
    if layer == "F2" and "locator_text" in request.arguments:
        raw = request.arguments["locator_text"]
        if not isinstance(raw, str) or not raw or len(raw) > 512:
            problems.append("arguments.locator_text 必须是 1–512 code points 的 string")
        else:
            locator_text = raw

    text_match: TextMatch | None = None
    if layer == "F2" and "text_match" in request.arguments:
        raw = request.arguments["text_match"]
        if not isinstance(raw, dict):
            problems.append("arguments.text_match 必须是 object")
        else:
            unknown_text = sorted(set(raw) - _TEXT_MATCH_FIELDS)
            if unknown_text:
                problems.append(f"arguments.text_match 包含未知字段: {', '.join(unknown_text)}")
            text = raw.get("text")
            if not isinstance(text, str) or not text or len(text) > 512:
                problems.append("arguments.text_match.text 必须是 1–512 code points 的 string")
            fields, field_problems = _unique_strings(
                raw.get("field_paths"), "arguments.text_match.field_paths", minimum=1, maximum=16
            )
            problems.extend(field_problems)
            allowed_fields = set().union(*(_F2_FIELDS[key] for key in fact_type_keys if key in _F2_FIELDS))
            invalid_fields = sorted(set(fields) - allowed_fields)
            if invalid_fields:
                problems.append(
                    "arguments.text_match.field_paths 包含所选类型 F2 投影之外的字段: " + ", ".join(invalid_fields)
                )
            if isinstance(text, str) and text and len(text) <= 512 and fields:
                text_match = TextMatch(text, fields)

    page_size = request.arguments.get("page_size", 100)
    if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 200:
        problems.append("arguments.page_size 必须是 1–200 的 integer")
        page_size = 100
    cursor_value = request.arguments.get("cursor")
    cursor = cursor_value if isinstance(cursor_value, str) and cursor_value else None
    if "cursor" in request.arguments and cursor is None:
        problems.append("arguments.cursor 必须是非空 string")

    if request.observed_context:
        problems.append("observed_context 对本操作必须为空 object")
    if request.authorization_reference:
        problems.append("authorization_reference 对本只读操作必须为空 array")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对本操作必须为 null 或省略")
    if problems or project_id is None or layer is None:
        return FactCandidateRequestParseResult(None, tuple(problems))
    governance_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return FactCandidateRequestParseResult(
        FactCandidateRequest(
            workspace_root,
            governance_scope,
            project_id,
            layer,
            fact_type_keys,
            statuses,
            exact_refs,
            relation_targets,
            current_workcase_ref,
            selected_fact_refs,
            locator_text,
            text_match,
            page_size,
            cursor,
            context.cwd,
        ),
        (),
    )


__all__ = [
    "FactCandidateRequest",
    "FactCandidateRequestParseResult",
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "TextMatch",
    "parse_fact_candidate_request",
]
