"""Normalize only change-log signatures added after the current HEAD snapshot."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Literal

from ldvh.commits.git_adapter import read_head_regular_file
from ldvh.facts.content import validate_fact_content
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, serialize_fact_object
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.update import atomic_replace_text_if_unchanged
from ldvh.facts.validation import validate_fact_object
from ldvh.filesystem import AtomicWriteResult

NormalizationStatus = Literal[
    "current_rejected",
    "fingerprint_stale",
    "head_unavailable",
    "head_fingerprint_stale",
    "history_mismatch",
    "nothing_to_normalize",
    "candidate_rejected",
    "replacement_conflict",
    "replacement_unavailable",
    "readback_failed",
    "updated",
]


@dataclass(frozen=True, slots=True)
class UncommittedSignatureNormalizationCommand:
    boundary: CreationBoundary
    fact_type_key: str
    object_id: str
    schema: FactSchema
    expected_content_fingerprint: str
    expected_head_content_fingerprint: str


@dataclass(frozen=True, slots=True)
class UncommittedSignatureNormalizationResult:
    status: NormalizationStatus
    issues: tuple[FactIssue, ...] = ()
    current: FactReadResult | None = None
    readback: FactReadResult | None = None
    candidate_text: str | None = None
    replacement_result: AtomicWriteResult | None = None
    rollback_result: AtomicWriteResult | None = None
    normalized_count: int = 0


def _read_current(command: UncommittedSignatureNormalizationCommand) -> FactReadResult:
    return read_fact_object(
        command.boundary.worktree_root,
        LAYOUTS[command.fact_type_key],
        command.schema,
        command.object_id,
        expected_common_dir=command.boundary.git_common_dir,
    )


def _candidate_fields(
    current: Mapping[str, object],
    head: Mapping[str, object],
) -> tuple[dict[str, object] | None, int, FactIssue | None]:
    current_log = current.get("change_log")
    head_log = head.get("change_log")
    if not isinstance(current_log, list) or not isinstance(head_log, list):
        return None, 0, FactIssue("schema", "HEAD 与 Working Tree 都必须含可比较的 change_log", "change_log")
    if len(current_log) <= len(head_log) or current_log[: len(head_log)] != head_log:
        return None, 0, FactIssue("schema", "HEAD change_log 必须是 Working Tree 的精确前缀", "change_log")

    normalized = deepcopy(dict(current))
    normalized_log = deepcopy(current_log)
    for index in range(len(head_log), len(normalized_log)):
        entry = normalized_log[index]
        signature = entry.get("signature") if isinstance(entry, dict) else None
        if not (
            isinstance(signature, dict)
            and set(signature) == {"model_id", "host_name"}
            and all(isinstance(signature.get(name), str) and signature[name].strip() for name in signature)
        ):
            return (
                None,
                0,
                FactIssue(
                    "schema",
                    "每条未提交流水必须恰为非空 model_id/host_name 中间签名形状",
                    f"change_log[{index}].signature",
                ),
            )
        entry["signature"] = {
            "model_id": signature["model_id"],
            "agent_workbench": signature["host_name"],
        }
    normalized["change_log"] = normalized_log
    return normalized, len(normalized_log) - len(head_log), None


def apply_uncommitted_signature_normalization_locked(
    command: UncommittedSignatureNormalizationCommand,
) -> UncommittedSignatureNormalizationResult:
    current = _read_current(command)
    if current.check_status != "mechanically_valid" or current.fields is None or current.raw_text is None:
        return UncommittedSignatureNormalizationResult(
            "current_rejected", issues=current.issues, current=current
        )
    if current.content_fingerprint != command.expected_content_fingerprint:
        return UncommittedSignatureNormalizationResult("fingerprint_stale", current=current)

    layout = LAYOUTS[command.fact_type_key]
    head_data, _head_oid, head_problem = read_head_regular_file(
        command.boundary.worktree_root,
        layout.canonical_path(command.object_id),
    )
    if head_data is None:
        issue = FactIssue("reference", head_problem or "HEAD 中不存在目标普通文件")
        return UncommittedSignatureNormalizationResult("head_unavailable", issues=(issue,), current=current)
    head = validate_fact_content(layout, command.schema, command.object_id, head_data)
    if head.check_status != "mechanically_valid" or head.fields is None:
        return UncommittedSignatureNormalizationResult("head_unavailable", issues=head.issues, current=current)
    if head.content_fingerprint != command.expected_head_content_fingerprint:
        return UncommittedSignatureNormalizationResult("head_fingerprint_stale", current=current)

    fields, normalized_count, issue = _candidate_fields(current.fields, head.fields)
    if issue is not None or fields is None:
        return UncommittedSignatureNormalizationResult(
            "history_mismatch", issues=(() if issue is None else (issue,)), current=current
        )
    if normalized_count == 0:
        return UncommittedSignatureNormalizationResult("nothing_to_normalize", current=current)

    candidate_text = serialize_fact_object(
        layout,
        fields,
        current.body if layout.carrier == "markdown" else None,
    )
    candidate_check = validate_fact_content(
        layout,
        command.schema,
        command.object_id,
        candidate_text.encode("utf-8"),
    )
    if candidate_check.check_status != "mechanically_valid" or candidate_check.fields is None:
        return UncommittedSignatureNormalizationResult(
            "candidate_rejected",
            issues=candidate_check.issues,
            current=current,
            candidate_text=candidate_text,
        )
    candidate_issues = validate_fact_object(command.fact_type_key, candidate_check.fields, command.schema)
    if candidate_issues:
        return UncommittedSignatureNormalizationResult(
            "candidate_rejected",
            issues=candidate_issues,
            current=current,
            candidate_text=candidate_text,
        )

    # The fact lock serializes controlled fact writers, but it does not lock
    # Git HEAD.  Rebind the HEAD side of the dual anchor immediately before
    # replacing the Working Tree file.
    latest_head_data, _latest_head_oid, _latest_head_problem = read_head_regular_file(
        command.boundary.worktree_root,
        layout.canonical_path(command.object_id),
    )
    if latest_head_data is None:
        return UncommittedSignatureNormalizationResult("head_unavailable", current=current)
    latest_head = validate_fact_content(layout, command.schema, command.object_id, latest_head_data)
    if (
        latest_head.check_status != "mechanically_valid"
        or latest_head.content_fingerprint != command.expected_head_content_fingerprint
    ):
        return UncommittedSignatureNormalizationResult("head_fingerprint_stale", current=current)

    replacement = atomic_replace_text_if_unchanged(
        command.boundary.worktree_root,
        layout,
        command.object_id,
        current.raw_text,
        candidate_text,
    )
    if replacement.namespace_state != "committed" or replacement.outcome != "replaced":
        status: NormalizationStatus = (
            "replacement_conflict" if replacement.outcome == "conflict" else "replacement_unavailable"
        )
        return UncommittedSignatureNormalizationResult(
            status,
            current=current,
            candidate_text=candidate_text,
            replacement_result=replacement,
        )

    readback = _read_current(command)
    if readback.check_status == "mechanically_valid" and readback.raw_text == candidate_text:
        return UncommittedSignatureNormalizationResult(
            "updated",
            current=current,
            readback=readback,
            candidate_text=candidate_text,
            replacement_result=replacement,
            normalized_count=normalized_count,
        )

    rollback = atomic_replace_text_if_unchanged(
        command.boundary.worktree_root,
        layout,
        command.object_id,
        candidate_text,
        current.raw_text,
    )
    return UncommittedSignatureNormalizationResult(
        "readback_failed",
        issues=readback.issues,
        current=current,
        readback=readback,
        candidate_text=candidate_text,
        replacement_result=replacement,
        rollback_result=rollback,
        normalized_count=normalized_count,
    )


__all__ = [
    "UncommittedSignatureNormalizationCommand",
    "UncommittedSignatureNormalizationResult",
    "apply_uncommitted_signature_normalization_locked",
]
