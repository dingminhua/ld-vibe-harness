"""Controlled correction of invalid historical change-log workbench names."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
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


def _preserve_yaml_repair_text(
    raw_text: str,
    repairs: tuple[dict[str, Any], ...],
    correction: dict[str, Any],
    event_at: str,
) -> str | None:
    """Patch only legacy signature scalars while preserving YAML formatting."""

    lines = raw_text.splitlines(keepends=True)
    change_log_line = next(
        (index for index, line in enumerate(lines) if line.strip() == "change_log:"),
        None,
    )
    if change_log_line is None:
        return None

    targets = {
        (repair["change_log_index"], repair.get("source_field", "agent_workbench")): repair["agent_workbench"]
        for repair in repairs
    }
    item_index = -1
    item_start = change_log_line + 1
    replaced: set[tuple[int, str]] = set()
    for line_index in range(item_start, len(lines)):
        line = lines[line_index]
        if re.match(r"^\s*[A-Za-z0-9_-]+:", line) and not line.startswith((" ", "\t")):
            break
        if re.match(r"^  -(?:\s|$)", line):
            item_index += 1
            item_start = line_index
        for (target_index, field), new_value in targets.items():
            if target_index != item_index or (target_index, field) in replaced:
                continue
            match = re.match(rf"^(\s+){re.escape(field)}:\s*(.*?)(\r?\n)?$", line)
            if match is None:
                continue
            old_value = match.group(2).strip().strip("'\"")
            expected = next(
                repair["expected_value"]
                for repair in repairs
                if repair["change_log_index"] == target_index
                and repair.get("source_field", "agent_workbench") == field
            )
            if old_value != expected:
                return None
            newline = match.group(3) or ""
            lines[line_index] = f"{match.group(1)}{field}: {new_value}{newline}"
            replaced.add((target_index, field))

    if replaced != set(targets):
        return None

    updated_line = next(
        (index for index, line in enumerate(lines) if re.match(r"^updated_at:\s*", line)),
        None,
    )
    if updated_line is None:
        return None
    newline = "\n" if lines[updated_line].endswith("\n") else ""
    lines[updated_line] = f"updated_at: '{event_at}'{newline}"

    next_top_level = next(
        (
            index
            for index in range(item_start + 1, len(lines))
            if re.match(r"^[A-Za-z0-9_-]+:", lines[index])
        ),
        len(lines),
    )
    repaired_values = "; ".join(
        f"{repair['change_log_index']}: {repair.get('expected_value')} -> {repair['agent_workbench']}"
        for repair in repairs
    )
    summary = (
        "受控更正历史 change_log 中的 agent_workbench 格式；"
        f"修复项为 {repaired_values}。原始错误值已由本次更正覆盖并保留本条修复记录。"
    )
    audit = [
        "  - at: '" + event_at + "'\n",
        "    summary: '" + summary.replace("'", "''") + "'\n",
        "    signature:\n",
        f"      agent_workbench: {correction['signature']['agent_workbench']}\n",
        f"      model_id: {correction['signature']['model_id']}\n",
    ]
    if "session_id" in correction:
        audit.append(f"    session_id: {correction['session_id']}\n")
    lines[next_top_level:next_top_level] = audit
    return "".join(lines)


def _repairable_issues(read: FactReadResult) -> tuple[FactIssue, ...]:
    return tuple(
        issue
        for issue in read.issues
        if issue.field_path.endswith(".signature.agent_workbench")
        and "单 token" in issue.summary
    )


def _legacy_repair_indices(change_log: list[Any], repairs: tuple[dict[str, Any], ...]) -> set[int]:
    indices: set[int] = set()
    for repair in repairs:
        source_field = repair.get("source_field")
        if source_field not in {"agent_id", "model_id", "agent_workbench", "host_environment", "host_name"}:
            continue
        index = repair["change_log_index"]
        if index >= len(change_log):
            continue
        entry = change_log[index]
        signature = entry.get("signature") if isinstance(entry, dict) else None
        if not isinstance(signature, dict):
            continue
        if source_field == "agent_id":
            if set(signature) == {"agent_id", "host_environment"}:
                indices.add(index)
        elif source_field == "model_id":
            if set(signature) in ({"model_id", "agent_workbench"}, {"model_id", "host_name"}):
                indices.add(index)
        elif source_field == "agent_workbench":
            if set(signature) == {"model_id", "agent_workbench"}:
                indices.add(index)
        elif source_field == "host_environment":
            if set(signature) == {"agent_id", "host_environment"}:
                indices.add(index)
        elif set(signature) == {"model_id", "host_name"}:
            indices.add(index)
    return indices


def apply_historical_signature_repair_locked(
    command: HistoricalSignatureRepairCommand,
) -> HistoricalSignatureRepairResult:
    current = _read(command)
    if current.fields is None or current.raw_text is None or current.check_status == "unavailable":
        return HistoricalSignatureRepairResult("current_unavailable", issues=current.issues, current=current)
    if current.content_fingerprint != command.expected_content_fingerprint:
        return HistoricalSignatureRepairResult("fingerprint_stale", current=current)
    fields = deepcopy(current.fields)
    change_log = fields.get("change_log")
    if not isinstance(change_log, list):
        return HistoricalSignatureRepairResult(
            "current_rejected", issues=(FactIssue("schema", "change_log 必须是 array", "change_log"),), current=current
        )
    allowed = _repairable_issues(current)
    legacy_indices = _legacy_repair_indices(change_log, command.repairs) if not current.issues else set()
    issue_indices = {
        int(issue.field_path.split("[")[1].split("]")[0])
        for issue in allowed
        if "[" in issue.field_path
    }
    if current.issues and (not allowed or len(allowed) != len(current.issues)):
        return HistoricalSignatureRepairResult(
            "current_rejected",
            issues=current.issues or (FactIssue("schema", "当前对象没有可由该入口修复的历史署名问题", "change_log"),),
            current=current,
        )
    if not current.issues and not legacy_indices:
        return HistoricalSignatureRepairResult(
            "current_rejected",
            issues=(FactIssue("schema", "没有指定可迁移的旧版历史签名", "repairs"),),
            current=current,
        )
    issue_paths = {issue.field_path for issue in allowed}
    repaired_indices: list[int] = []
    repaired_values: list[str] = []
    for repair in command.repairs:
        index = repair["change_log_index"]
        source_field = repair.get("source_field", "agent_workbench")
        path = f"change_log[{index}].signature.{source_field}"
        if (
            index >= len(change_log)
            or (current.issues and source_field == "agent_workbench" and path not in issue_paths)
            or (source_field in {"agent_id", "model_id", "agent_workbench", "host_environment", "host_name"}
                and index not in legacy_indices and not current.issues)
        ):
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
        signature = entry["signature"]
        old_value = signature.get(source_field)
        if source_field in {"host_environment", "host_name"}:
            if old_value != repair.get("expected_value"):
                return HistoricalSignatureRepairResult(
                    "repair_rejected",
                    issues=(FactIssue("schema", "指定旧版签名值与当前对象不一致", path),),
                    current=current,
                )
            # Legacy records may use agent_id as an Agent identity rather than
            # a model_id. Preserve that historical shape and only normalize
            # the displayed host/workbench value.
            signature[source_field] = repair["agent_workbench"]
        else:
            if old_value != repair.get("expected_value"):
                return HistoricalSignatureRepairResult(
                    "repair_rejected",
                    issues=(FactIssue("schema", "指定旧版签名值与当前对象不一致", path),),
                    current=current,
                )
            signature[source_field] = repair["agent_workbench"]
        repaired_values.append(f"{index}: {old_value} -> {repair['agent_workbench']}")
        repaired_indices.append(index)
    expected_indices = issue_indices if current.issues else legacy_indices
    if set(repaired_indices) != expected_indices:
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
    candidate_text = (
        _preserve_yaml_repair_text(current.raw_text, command.repairs, correction, command.event_at)
        if layout.carrier == "yaml" and current.raw_text is not None
        else serialize_fact_object(layout, fields, current.body if layout.carrier == "markdown" else None)
    )
    if candidate_text is None:
        return HistoricalSignatureRepairResult(
            "candidate_rejected",
            issues=(FactIssue("serialization", "无法在保留原始 YAML 格式的前提下形成修复候选", "change_log"),),
            current=current,
        )
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
