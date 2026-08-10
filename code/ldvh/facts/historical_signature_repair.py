"""Controlled correction of invalid historical change-log workbench names."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from ldvh.facts.content import validate_fact_content
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, serialize_fact_object
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.update import atomic_replace_text_if_unchanged
from ldvh.facts.validation import validate_fact_object
from ldvh.filesystem import AtomicWriteResult

RepairStatus = Literal[
    "current_unavailable",
    "current_rejected",
    "fingerprint_stale",
    "repair_rejected",
    "candidate_rejected",
    "replacement_conflict",
    "replacement_unavailable",
    "readback_failed",
    "updated",
]


@dataclass(frozen=True, slots=True)
class HistoricalSignatureRepairCommand:
    boundary: CreationBoundary
    fact_type_key: str
    object_id: str
    schema: FactSchema
    expected_content_fingerprint: str
    repairs: tuple[dict[str, Any], ...]
    correction_signature: dict[str, str]
    session_id: str | None
    event_at: str


@dataclass(frozen=True, slots=True)
class HistoricalSignatureRepairResult:
    status: RepairStatus
    issues: tuple[FactIssue, ...] = ()
    current: FactReadResult | None = None
    readback: FactReadResult | None = None
    candidate_text: str | None = None
    replacement_result: AtomicWriteResult | None = None
    rollback_result: AtomicWriteResult | None = None
    repaired_count: int = 0


def _read(command: HistoricalSignatureRepairCommand) -> FactReadResult:
    return read_fact_object(
        command.boundary.worktree_root,
        LAYOUTS[command.fact_type_key],
        command.schema,
        command.object_id,
        expected_common_dir=command.boundary.git_common_dir,
    )


def _repairable_issues(read: FactReadResult) -> tuple[FactIssue, ...]:
    return tuple(
        issue
        for issue in read.issues
        if issue.field_path.endswith(".signature.agent_workbench")
        and "单 token" in issue.summary
    )


def apply_historical_signature_repair_locked(
    command: HistoricalSignatureRepairCommand,
) -> HistoricalSignatureRepairResult:
    current = _read(command)
    if current.fields is None or current.raw_text is None or current.check_status == "unavailable":
        return HistoricalSignatureRepairResult("current_unavailable", issues=current.issues, current=current)
    if current.content_fingerprint != command.expected_content_fingerprint:
        return HistoricalSignatureRepairResult("fingerprint_stale", current=current)
    allowed = _repairable_issues(current)
    if not allowed or len(allowed) != len(current.issues):
        return HistoricalSignatureRepairResult(
            "current_rejected",
            issues=current.issues or (FactIssue("schema", "当前对象没有可由该入口修复的历史署名问题", "change_log"),),
            current=current,
        )

    fields = deepcopy(current.fields)
    change_log = fields.get("change_log")
    if not isinstance(change_log, list):
        return HistoricalSignatureRepairResult(
            "current_rejected", issues=(FactIssue("schema", "change_log 必须是 array", "change_log"),), current=current
        )
    issue_paths = {issue.field_path for issue in allowed}
    repaired_indices: list[int] = []
    repaired_values: list[str] = []
    for repair in command.repairs:
        index = repair["change_log_index"]
        path = f"change_log[{index}].signature.agent_workbench"
        if path not in issue_paths or index >= len(change_log):
            return HistoricalSignatureRepairResult(
                "repair_rejected",
                issues=(FactIssue("schema", "指定索引不是当前可修复的历史署名问题", path),),
                current=current,
            )
        entry = change_log[index]
        if not isinstance(entry, dict) or not isinstance(entry.get("signature"), dict):
            return HistoricalSignatureRepairResult(
                "repair_rejected", issues=(FactIssue("schema", "目标历史流水签名不可解析", path),), current=current
            )
        repaired_values.append(
            f"{index}: {entry['signature'].get('agent_workbench')} -> {repair['agent_workbench']}"
        )
        entry["signature"]["agent_workbench"] = repair["agent_workbench"]
        repaired_indices.append(index)
    if set(repaired_indices) != {
        int(issue.field_path.split("[")[1].split("]")[0]) for issue in allowed
    }:
        return HistoricalSignatureRepairResult(
            "repair_rejected",
            issues=(FactIssue("schema", "repairs 必须覆盖当前对象全部可修复历史署名问题", "repairs"),),
            current=current,
        )

    correction = {
        "at": command.event_at,
        "summary": (
            "受控更正历史 change_log 中的 agent_workbench 格式；"
            f"修复项为 {'; '.join(repaired_values)}。原始错误值已由本次更正覆盖并保留本条修复记录。"
        ),
        "signature": dict(command.correction_signature),
    }
    if command.session_id is not None:
        correction["session_id"] = command.session_id
    fields["change_log"] = [*change_log, correction]
    fields["updated_at"] = command.event_at
    layout = LAYOUTS[command.fact_type_key]
    candidate_text = serialize_fact_object(layout, fields, current.body if layout.carrier == "markdown" else None)
    candidate_check = validate_fact_content(layout, command.schema, command.object_id, candidate_text.encode("utf-8"))
    if candidate_check.check_status != "mechanically_valid" or candidate_check.fields is None:
        return HistoricalSignatureRepairResult(
            "candidate_rejected", issues=candidate_check.issues, current=current, candidate_text=candidate_text
        )
    candidate_issues = validate_fact_object(command.fact_type_key, candidate_check.fields, command.schema)
    if candidate_issues:
        return HistoricalSignatureRepairResult(
            "candidate_rejected", issues=candidate_issues, current=current, candidate_text=candidate_text
        )

    replacement = atomic_replace_text_if_unchanged(
        command.boundary.worktree_root, layout, command.object_id, current.raw_text, candidate_text
    )
    if replacement.outcome != "replaced" or replacement.namespace_state != "committed":
        status: RepairStatus = (
            "replacement_conflict" if replacement.outcome == "conflict" else "replacement_unavailable"
        )
        return HistoricalSignatureRepairResult(
            status, current=current, candidate_text=candidate_text, replacement_result=replacement
        )
    readback = _read(command)
    if readback.check_status == "mechanically_valid" and readback.raw_text == candidate_text:
        return HistoricalSignatureRepairResult(
            "updated",
            current=current,
            readback=readback,
            candidate_text=candidate_text,
            replacement_result=replacement,
            repaired_count=len(repaired_indices),
        )
    rollback = atomic_replace_text_if_unchanged(
        command.boundary.worktree_root, layout, command.object_id, candidate_text, current.raw_text
    )
    return HistoricalSignatureRepairResult(
        "readback_failed",
        issues=readback.issues,
        current=current,
        readback=readback,
        candidate_text=candidate_text,
        replacement_result=replacement,
        rollback_result=rollback,
        repaired_count=len(repaired_indices),
    )


__all__ = [
    "HistoricalSignatureRepairCommand",
    "HistoricalSignatureRepairResult",
    "apply_historical_signature_repair_locked",
]
