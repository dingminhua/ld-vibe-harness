"""Parse source-defined draft preparation and controlled creation requests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS, WRITABLE_FACT_TYPE_KEYS
from ldvh.facts.validation import _is_host_product_concatenation, _truncate_workbench_compound
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

_MODEL_PRODUCT_ALIASES = frozenset(
    {"codex", "claude-code", "workbuddy", "workbuddy-ai", "deepseek", "glm", "gpt", "claude", "kimi", "k3"}
)

PREPARE_REQUIRED_INPUTS = ("arguments.governed_project_id", "arguments.fact_type_key")
PREPARE_OPTIONAL_INPUTS = ("work_object_locators", "arguments.workspace_root")
CREATE_REQUIRED_INPUTS = ("arguments.draft_basis", "arguments.fact_object")
CREATE_OPTIONAL_INPUTS = (
    "work_object_locators",
    "arguments.workspace_root",
    "authorization_reference",
)
_PREPARE_FIELDS = frozenset({"workspace_root", "governed_project_id", "fact_type_key"})
_CREATE_FIELDS = frozenset({"workspace_root", "draft_basis", "fact_object"})
_DRAFT_BASIS_FIELDS = frozenset(
    {
        "governed_project_id",
        "fact_type_key",
        "candidate_object_id",
        "schema_fingerprint",
        "worktree_fingerprint",
    }
)


@dataclass(frozen=True, slots=True)
class DraftBasis:
    governed_project_id: str
    fact_type_key: str
    candidate_object_id: str
    schema_fingerprint: str
    worktree_fingerprint: str

    def to_json(self) -> dict[str, str]:
        return {
            "governed_project_id": self.governed_project_id,
            "fact_type_key": self.fact_type_key,
            "candidate_object_id": self.candidate_object_id,
            "schema_fingerprint": self.schema_fingerprint,
            "worktree_fingerprint": self.worktree_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class FactDraftRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    governed_project_id: str
    fact_type_key: str
    base: Path


@dataclass(frozen=True, slots=True)
class FactCreateRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    draft_basis: DraftBasis
    fact_object: dict[str, Any]
    authorization_reference: tuple[dict[str, Any], ...]
    base: Path


@dataclass(frozen=True, slots=True)
class CreationRequestParseResult:
    request: FactDraftRequest | FactCreateRequest | None
    problems: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ObservedWriteSignature:
    signature: dict[str, str]
    session_id: str | None
    problems: tuple[str, ...]


def parse_observed_write_signature(observed_context: dict[str, Any]) -> ObservedWriteSignature:
    """Parse the write-only observed signature without changing display values."""

    if not observed_context:
        return ObservedWriteSignature({}, None, ())
    problems: list[str] = []
    unknown = sorted(set(observed_context) - {"signature"})
    if unknown:
        problems.append(f"observed_context 只允许 signature 子字段: {', '.join(unknown)}")
        return ObservedWriteSignature({}, None, tuple(problems))
    raw = observed_context.get("signature", {})
    if not isinstance(raw, dict):
        return ObservedWriteSignature({}, None, ("observed_context.signature 必须是 object",))
    allowed = {"model_id", "agent_workbench", "session_id"}
    unknown_signature = sorted(set(raw) - allowed)
    if unknown_signature:
        problems.append(f"observed_context.signature 包含未知字段: {', '.join(unknown_signature)}")
    values: dict[str, str] = {}
    for field in sorted(allowed):
        value = raw.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            problems.append(f"observed_context.signature.{field} 出现时必须是非空 string")
            continue
        values[field] = value.strip()
        if field == "agent_workbench":
            values[field] = _truncate_workbench_compound(values[field])
        if field == "model_id" and value.strip().lower() in _MODEL_PRODUCT_ALIASES:
            problems.append("observed_context.signature.model_id 不得使用已知裸产品别名")
        if field == "model_id" and _is_host_product_concatenation(value):
            problems.append("observed_context.signature.model_id 不得拼接宿主产品名")
        if field == "agent_workbench" and value.strip().endswith(")") and "(" in value.strip():
            problems.append("observed_context.signature.agent_workbench 不得包含括号系统后缀")
    signature = {
        field: value.lower() if field == "model_id" else value
        for field, value in values.items()
        if field in {"model_id", "agent_workbench"}
    }
    return ObservedWriteSignature(signature, values.get("session_id"), tuple(problems))


def observed_signature_injection_problems(
    observed_context: dict[str, Any],
    fact_object: dict[str, Any],
) -> tuple[str, ...]:
    parsed = parse_observed_write_signature(observed_context)
    problems = list(parsed.problems)
    change_log = fact_object.get("change_log")
    if isinstance(change_log, list) and change_log and isinstance(change_log[-1], dict):
        existing = change_log[-1].get("signature")
        if isinstance(existing, dict) and set(existing) == {"agent_id", "host_environment"}:
            problems.append(
                "最新 change_log.signature 仍为 agent_id/host_environment 旧形状；"
                "新写入必须使用 model_id 与 agent_workbench"
            )
        elif isinstance(existing, dict) and set(existing) == {"model_id", "host_name"}:
            problems.append(
                "最新 change_log.signature 仍为 model_id/host_name 旧形状；新写入必须使用 model_id 与 agent_workbench"
            )
    if problems or (not parsed.signature and parsed.session_id is None):
        return tuple(problems)
    if not isinstance(change_log, list) or not change_log or not isinstance(change_log[-1], dict):
        problems.append("observed_context.signature 注入要求 fact_object.change_log 含最新 object 条目")
        return tuple(problems)
    existing = change_log[-1].get("signature")
    merged = (
        {}
        if isinstance(existing, dict)
        and set(existing) in ({"agent_id", "host_environment"}, {"model_id", "host_name"})
        else dict(existing) if isinstance(existing, dict) else {}
    )
    merged.update(parsed.signature)
    if set(merged) != {"model_id", "agent_workbench"} or any(
        not isinstance(merged[field], str) or not merged[field].strip()
        for field in ("model_id", "agent_workbench")
        if field in merged
    ):
        problems.append("observed_context.signature 合并后必须恰含非空 model_id 与 agent_workbench")
    return tuple(problems)


def _common(
    request: CommonRequest,
    context: OperationExecutionContext,
    allowed_fields: frozenset[str],
) -> tuple[list[str], list[str], Path | None, tuple[ScopeDescriptor, ...]]:
    problems: list[str] = []
    if not context.cwd.is_absolute():
        problems.append("Helper 进程实际 cwd 必须是绝对路径")
    unknown = sorted(set(request.arguments) - allowed_fields)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")
    locators: list[str] = []
    for index, locator in enumerate(request.work_object_locators):
        if not isinstance(locator, str) or not locator:
            problems.append(f"work_object_locators[{index}] 必须是非空路径 string")
        else:
            locators.append(locator)
    workspace_root: Path | None = None
    if "workspace_root" in request.arguments:
        value = request.arguments["workspace_root"]
        if not isinstance(value, str) or not value or not Path(value).is_absolute():
            problems.append("arguments.workspace_root 必须是非空绝对路径 string")
        else:
            workspace_root = Path(value)
    if request.observed_context:
        observed_result = parse_observed_write_signature(request.observed_context)
        problems.extend(observed_result.problems)
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对事实对象草案和创建操作必须为 null 或省略")
    scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    return problems, locators, workspace_root, scope


def parse_draft_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> CreationRequestParseResult:
    problems, _, workspace_root, scope = _common(request, context, _PREPARE_FIELDS)
    project_id = request.arguments.get("governed_project_id")
    fact_type_key = request.arguments.get("fact_type_key")
    if not isinstance(project_id, str) or not project_id:
        problems.append("arguments.governed_project_id 必须是非空 string")
    if not isinstance(fact_type_key, str) or fact_type_key not in WRITABLE_FACT_TYPE_KEYS:
        problems.append("arguments.fact_type_key 必须匹配当前支持的五类事实类型")
    if request.authorization_reference:
        problems.append("authorization_reference 对无副作用草案操作必须为空 array")
    if problems:
        return CreationRequestParseResult(None, tuple(problems))
    assert isinstance(project_id, str) and isinstance(fact_type_key, str)
    return CreationRequestParseResult(
        FactDraftRequest(workspace_root, scope, project_id, fact_type_key, context.cwd),
        (),
    )


def parse_create_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> CreationRequestParseResult:
    problems, _, workspace_root, scope = _common(request, context, _CREATE_FIELDS)
    raw_basis = request.arguments.get("draft_basis")
    basis: DraftBasis | None = None
    if not isinstance(raw_basis, dict):
        problems.append("arguments.draft_basis 必须是 object")
    else:
        unknown = sorted(set(raw_basis) - _DRAFT_BASIS_FIELDS)
        if unknown:
            problems.append(f"arguments.draft_basis 包含未知字段: {', '.join(unknown)}")
        values: dict[str, str] = {}
        for field in sorted(_DRAFT_BASIS_FIELDS):
            value = raw_basis.get(field)
            if not isinstance(value, str) or not value:
                problems.append(f"arguments.draft_basis.{field} 必须是非空 string")
            else:
                values[field] = value
        if len(values) == len(_DRAFT_BASIS_FIELDS):
            fact_type_key = values["fact_type_key"]
            layout = LAYOUTS.get(fact_type_key)
            if layout is None or fact_type_key not in WRITABLE_FACT_TYPE_KEYS:
                problems.append("arguments.draft_basis.fact_type_key 未匹配当前支持的五类事实类型")
            elif layout.object_id_pattern.fullmatch(values["candidate_object_id"]) is None:
                problems.append("arguments.draft_basis.candidate_object_id 与事实类型格式不一致")
            else:
                basis = DraftBasis(**values)
    fact_object = request.arguments.get("fact_object")
    if not isinstance(fact_object, dict):
        problems.append("arguments.fact_object 必须是 object")
        fact_object = {}
    else:
        problems.extend(observed_signature_injection_problems(request.observed_context, fact_object))
    if problems:
        return CreationRequestParseResult(None, tuple(problems))
    assert basis is not None
    return CreationRequestParseResult(
        FactCreateRequest(
            workspace_root,
            scope,
            basis,
            dict(fact_object),
            request.authorization_reference,
            context.cwd,
        ),
        (),
    )


__all__ = [
    "CREATE_OPTIONAL_INPUTS",
    "CREATE_REQUIRED_INPUTS",
    "PREPARE_OPTIONAL_INPUTS",
    "PREPARE_REQUIRED_INPUTS",
    "CreationRequestParseResult",
    "DraftBasis",
    "FactCreateRequest",
    "FactDraftRequest",
    "ObservedWriteSignature",
    "observed_signature_injection_problems",
    "parse_observed_write_signature",
    "parse_create_request",
    "parse_draft_request",
]
