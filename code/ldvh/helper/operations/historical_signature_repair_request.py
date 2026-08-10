"""Parse requests for controlled correction of historical change-log signatures."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS, WRITABLE_FACT_TYPE_KEYS
from ldvh.facts.models import FactReference
from ldvh.governance.models import ScopeDescriptor, cwd_scope, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest, parse_observed_signature

REQUIRED_INPUTS = (
    "arguments.fact_ref",
    "arguments.expected_content_fingerprint",
    "arguments.repairs",
    "authorization_reference",
)
OPTIONAL_INPUTS = ("work_object_locators", "arguments.workspace_root")
_ARGUMENT_FIELDS = frozenset({"workspace_root", "fact_ref", "expected_content_fingerprint", "repairs"})
_FACT_REF_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})
_REPAIR_FIELDS = frozenset({"change_log_index", "agent_workbench"})
_LEGACY_REPAIR_FIELDS = frozenset({"change_log_index", "agent_workbench", "source_field", "expected_value"})
_LEGACY_SOURCE_FIELDS = frozenset({"agent_id", "agent_workbench", "host_environment", "host_name", "model_id"})
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")
_TOKEN = re.compile(r"[^\s\-/()]+\Z")
_MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


@dataclass(frozen=True, slots=True)
class HistoricalSignatureRepairRequest:
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: FactReference
    expected_content_fingerprint: str
    repairs: tuple[dict[str, Any], ...]
    authorization_reference: tuple[dict[str, Any], ...]
    observed_signature: dict[str, str]
    session_id: str | None
    base: Path


def parse_historical_signature_repair_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> tuple[HistoricalSignatureRepairRequest | None, tuple[str, ...]]:
    problems: list[str] = []
    unknown = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")

    locators: list[str] = []
    for index, locator in enumerate(request.work_object_locators):
        if not isinstance(locator, str) or not locator:
            problems.append(f"work_object_locators[{index}] 必须是非空路径 string")
        else:
            locators.append(locator)

    workspace_root: Path | None = None
    raw_root = request.arguments.get("workspace_root")
    if raw_root is not None:
        if not isinstance(raw_root, str) or not raw_root or not Path(raw_root).is_absolute():
            problems.append("arguments.workspace_root 必须是非空绝对路径 string")
        else:
            workspace_root = Path(raw_root)

    raw_ref = request.arguments.get("fact_ref")
    fact_ref: FactReference | None = None
    if not isinstance(raw_ref, dict):
        problems.append("arguments.fact_ref 必须是 object")
    else:
        unknown_ref = sorted(set(raw_ref) - _FACT_REF_FIELDS)
        if unknown_ref:
            problems.append(f"arguments.fact_ref 包含未知字段: {', '.join(unknown_ref)}")
        values = {name: raw_ref.get(name) for name in _FACT_REF_FIELDS}
        if any(not isinstance(value, str) or not value for value in values.values()):
            problems.append("arguments.fact_ref 的三个字段必须是非空 string")
        elif values["fact_type_key"] not in WRITABLE_FACT_TYPE_KEYS:
            problems.append("arguments.fact_ref.fact_type_key 不是当前可写事实类型")
        elif LAYOUTS[values["fact_type_key"]].object_id_pattern.fullmatch(values["object_id"]) is None:
            problems.append("arguments.fact_ref.object_id 与事实类型格式不一致")
        else:
            fact_ref = FactReference(values["governed_project_id"], values["fact_type_key"], values["object_id"])

    fingerprint = request.arguments.get("expected_content_fingerprint")
    if not isinstance(fingerprint, str) or _FINGERPRINT.fullmatch(fingerprint) is None:
        problems.append("arguments.expected_content_fingerprint 必须是 64 位小写十六进制 string")

    raw_repairs = request.arguments.get("repairs")
    repairs: list[dict[str, Any]] = []
    if not isinstance(raw_repairs, list) or not raw_repairs:
        problems.append("arguments.repairs 必须是非空 array")
    else:
        seen: set[tuple[int, str]] = set()
        for index, repair in enumerate(raw_repairs):
            if not isinstance(repair, dict) or set(repair) not in {_REPAIR_FIELDS, _LEGACY_REPAIR_FIELDS}:
                problems.append(
                    f"arguments.repairs[{index}] 必须为旧版两字段，或兼容格式迁移四字段"
                )
                continue
            log_index = repair["change_log_index"]
            workbench = repair["agent_workbench"]
            if not isinstance(log_index, int) or log_index < 0:
                problems.append(f"arguments.repairs[{index}].change_log_index 必须是非负 integer")
            source_field = repair.get("source_field")
            repair_key = (log_index, source_field) if isinstance(log_index, int) else None
            if repair_key in seen:
                problems.append(f"arguments.repairs[{index}] 的 change_log_index 与 source_field 组合不得重复")
            elif repair_key is not None:
                seen.add(repair_key)
            target_pattern = _MODEL_ID if source_field in {"agent_id", "model_id"} else _TOKEN
            if (
                not isinstance(workbench, str)
                or not workbench.strip()
                or target_pattern.fullmatch(workbench.strip()) is None
            ):
                problems.append(f"arguments.repairs[{index}].agent_workbench 必须是单 token")
            if set(repair) == _LEGACY_REPAIR_FIELDS:
                source_field = repair["source_field"]
                expected_value = repair["expected_value"]
                if source_field not in _LEGACY_SOURCE_FIELDS:
                    problems.append(
                        f"arguments.repairs[{index}].source_field 必须为 agent_id、model_id、"
                        "agent_workbench、host_environment 或 host_name"
                    )
                if not isinstance(expected_value, str) or not expected_value.strip():
                    problems.append(f"arguments.repairs[{index}].expected_value 必须是非空 string")
            if (
                isinstance(log_index, int)
                and log_index >= 0
                and isinstance(workbench, str)
                and target_pattern.fullmatch(workbench.strip())
            ):
                item = {"change_log_index": log_index, "agent_workbench": workbench.strip()}
                if set(repair) == _LEGACY_REPAIR_FIELDS:
                    if repair["source_field"] in _LEGACY_SOURCE_FIELDS and isinstance(repair["expected_value"], str):
                        item.update(
                            {
                                "source_field": repair["source_field"],
                                "expected_value": repair["expected_value"].strip(),
                            }
                        )
                repairs.append(item)

    observed = parse_observed_signature(request.observed_context)
    problems.extend(observed.problems)
    if not observed.signature.get("model_id") or not observed.signature.get("agent_workbench"):
        problems.append("observed_context.signature 必须提供 model_id 与 agent_workbench")
    session_id = (
        request.observed_context.get("signature", {}).get("session_id")
        if isinstance(request.observed_context.get("signature"), dict)
        else None
    )
    if session_id is not None and (not isinstance(session_id, str) or not session_id.strip()):
        problems.append("observed_context.signature.session_id 出现时必须是非空 string")
    if not request.authorization_reference:
        problems.append("authorization_reference 必须至少包含一个 Human 授权来源")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 必须为 null 或省略")
    if problems:
        return None, tuple(problems)
    assert fact_ref is not None and isinstance(fingerprint, str)
    governance_scope = explicit_scope(locators) if locators else cwd_scope(str(context.cwd))
    observed_signature = {
        key: value for key, value in observed.signature.items() if key != "session_id"
    }
    return HistoricalSignatureRepairRequest(
        workspace_root,
        governance_scope,
        fact_ref,
        fingerprint,
        tuple(repairs),
        request.authorization_reference,
        observed_signature,
        session_id.strip() if isinstance(session_id, str) else None,
        context.cwd,
    ), ()


__all__ = [
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "HistoricalSignatureRepairRequest",
    "parse_historical_signature_repair_request",
]
