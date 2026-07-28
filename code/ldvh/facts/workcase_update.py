"""Type-owned, full-after write transaction for the current WorkCase contract.

The three public modes share one source-file CAS boundary.  Route targets are
read-only participants: they are fingerprint-checked while the WorkCase type
lock is held, and checked again after the source replacement.  No audit receipt
or compatibility shape is constructed here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Literal

from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import ACTIVE_STATUSES, LAYOUTS
from ldvh.facts.creation import CreationBoundary, allocation_lock, serialize_fact_object
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import (
    ProjectFactIndex,
    WorkCaseRouteTargetSnapshot,
    proposal_route_target_snapshots,
    validate_workcase_incoming_dependencies,
    validate_workcase_route_target_alignment,
    validate_workcase_route_target_snapshots,
    workcase_routed_target_identities,
)
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.transitions import validate_workcase_transition
from ldvh.facts.update import atomic_replace_text_if_unchanged
from ldvh.facts.update_application import MANAGED_FIELDS, UpdateStatus
from ldvh.facts.validation import parse_rfc3339, validate_fact_object
from ldvh.filesystem import AtomicWriteResult, durable_writes_enabled
from ldvh.source_references import validate_source_reference

WorkCaseWriteMode = Literal["update", "close", "correct"]


@dataclass(frozen=True, slots=True)
class WorkCaseWriteCommand:
    """One exact WorkCase after bound to its source and read-only targets."""

    boundary: CreationBoundary
    schemas: Mapping[str, FactSchema]
    schema: FactSchema
    object_id: str
    expected_content_fingerprint: str
    supplied: Mapping[str, Any]
    event_at: str
    mode: WorkCaseWriteMode
    authorization_reference: tuple[Mapping[str, Any], ...] = ()
    route_target_fingerprints: tuple[WorkCaseRouteTargetSnapshot, ...] = ()
    independent_review_reference: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class WorkCaseWriteResult:
    status: UpdateStatus
    event_at: str
    issues: tuple[FactIssue, ...] = ()
    current: FactReadResult | None = None
    candidate: FactReadResult | None = None
    readback: FactReadResult | None = None
    candidate_text: str | None = None
    replacement_result: AtomicWriteResult | None = None
    rollback_result: AtomicWriteResult | None = None
    residual_readback: FactReadResult | None = None
    coordination_release_uncertain: bool = False


def _result(
    command: WorkCaseWriteCommand,
    status: UpdateStatus,
    *,
    issues: Sequence[FactIssue] = (),
    current: FactReadResult | None = None,
    candidate: FactReadResult | None = None,
    readback: FactReadResult | None = None,
    candidate_text: str | None = None,
    replacement_result: AtomicWriteResult | None = None,
    rollback_result: AtomicWriteResult | None = None,
    residual_readback: FactReadResult | None = None,
) -> WorkCaseWriteResult:
    return WorkCaseWriteResult(
        status=status,
        event_at=command.event_at,
        issues=tuple(issues),
        current=current,
        candidate=candidate,
        readback=readback,
        candidate_text=candidate_text,
        replacement_result=replacement_result,
        rollback_result=rollback_result,
        residual_readback=residual_readback,
    )


def _project_index(command: WorkCaseWriteCommand) -> ProjectFactIndex:
    return ProjectFactIndex(
        command.boundary.worktree_root,
        command.boundary.governed_project_id,
        dict(command.schemas),
        command.boundary.git_common_dir,
    )


def _project_read(command: WorkCaseWriteCommand) -> FactReadResult:
    layout = LAYOUTS["workcase"]
    read = read_fact_object(
        command.boundary.worktree_root,
        layout,
        command.schema,
        command.object_id,
        expected_common_dir=command.boundary.git_common_dir,
    )
    if read.check_status == "unavailable" or read.fields is None:
        return read
    if read.check_status != "mechanically_valid":
        return read
    index = _project_index(command)
    key = ("workcase", command.object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index, (key,))
    return index.cache.get(key, read)


def _complete_after(
    command: WorkCaseWriteCommand,
    before: Mapping[str, Any],
    *,
    updated_at: object,
) -> dict[str, Any]:
    return {
        **dict(command.supplied),
        "object_id": before["object_id"],
        "fact_type_key": before["fact_type_key"],
        "created_at": before["created_at"],
        "updated_at": updated_at,
    }


def _operation_boundary_issues(
    command: WorkCaseWriteCommand,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> tuple[FactIssue, ...]:
    issues: list[FactIssue] = []
    before_status = before.get("status")
    after_status = after.get("status")
    if command.mode == "update":
        if before_status not in ACTIVE_STATUSES or after_status not in ACTIVE_STATUSES:
            issues.append(FactIssue("schema", "update-workcase 只接受活动期 before 与活动期完整 after", "status"))
    elif command.mode == "close":
        if before_status != "open" or before.get("phase") != "human_closure_confirming":
            issues.append(
                FactIssue(
                    "schema",
                    "close-workcase 要求 before 为 open/human_closure_confirming",
                    "phase",
                )
            )
        if after_status != "closed":
            issues.append(FactIssue("schema", "close-workcase 的完整 after 必须为 closed", "status"))
    elif command.mode == "correct":
        if before_status != "closed" or after_status != "closed":
            issues.append(FactIssue("schema", "correct-closed-workcase 只接受 closed → closed", "status"))
    else:
        issues.append(FactIssue("schema", "未知 WorkCase 写入 mode"))

    if command.mode != "correct" and command.route_target_fingerprints:
        issues.append(
            FactIssue(
                "schema",
                "只有 correct-closed-workcase 接受独立 route_target_fingerprints 请求字段",
                "route_target_fingerprints",
            )
        )
    if command.mode != "correct" and command.independent_review_reference is not None:
        issues.append(
            FactIssue(
                "schema",
                "只有 correct-closed-workcase 接受 independent_review_reference",
                "independent_review_reference",
            )
        )
    if command.mode == "close" and not command.authorization_reference:
        issues.append(
            FactIssue(
                "schema",
                "close-workcase 必须取得回指 Human 当次关闭决定的 authorization_reference",
                "authorization_reference",
            )
        )
    return tuple(issues)


def _changed_roots(before: Mapping[str, Any], after: Mapping[str, Any]) -> set[str]:
    return {
        key
        for key in set(before) | set(after)
        if key not in MANAGED_FIELDS and before.get(key, _MISSING) != after.get(key, _MISSING)
    }


_MISSING = object()
_SUBSTANTIVE_CLOSED_ROOTS = frozenset(
    {
        "goal",
        "scope",
        "success_criterion_definitions",
        "success_criterion_results",
        "result_summary",
        "validation_summary",
        "closure_outcome",
        "disposition_summary",
        "residual_responsibilities",
        "spark_suggestions",
        "relations",
    }
)


def _gate_issues(
    command: WorkCaseWriteCommand,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> tuple[FactIssue, ...]:
    changed = _changed_roots(before, after)
    issues: list[FactIssue] = []
    if command.mode == "correct":
        title_only = changed == {"title"}
        urls_only = changed == {"urls"}
        conservative_urls = urls_only and (
            command.independent_review_reference is not None or bool(command.authorization_reference)
        )
        relation_only = changed == {"relations"}
        before_relations = _relation_identities(before)
        after_relations = _relation_identities(after)
        related_only = relation_only and all(
            identity[0] == "related-to" for identity in before_relations ^ after_relations
        )
        substantive = (
            bool(changed & _SUBSTANTIVE_CLOSED_ROOTS)
            or conservative_urls
            or (bool(changed) and not title_only and not urls_only)
        ) and not related_only
        if substantive:
            if command.independent_review_reference is None:
                issues.append(
                    FactIssue(
                        "schema",
                        "closed 实质更正必须回指当次实际独立复核",
                        "independent_review_reference",
                    )
                )
            if not command.authorization_reference:
                issues.append(
                    FactIssue(
                        "schema",
                        "closed 实质更正必须回指 Human 对完整更正的决定",
                        "authorization_reference",
                    )
                )
        elif command.independent_review_reference is not None:
            issues.append(
                FactIssue(
                    "schema",
                    "title-only 或无变化的非实质更正不得提交 independent_review_reference",
                    "independent_review_reference",
                )
            )
        if related_only and not command.authorization_reference:
            issues.append(
                FactIssue(
                    "schema",
                    "closed related-to 记录更正必须回指 Human 的实质更正决定",
                    "authorization_reference",
                )
            )
    return tuple(issues)


def _relation_identities(fields: Mapping[str, Any]) -> set[tuple[object, object, object, object]]:
    relations = fields.get("relations")
    identities: set[tuple[object, object, object, object]] = set()
    for relation in relations if isinstance(relations, list) else []:
        if not isinstance(relation, Mapping):
            continue
        target = relation.get("target")
        target_mapping = target if isinstance(target, Mapping) else {}
        identities.add(
            (
                relation.get("relation_key"),
                target_mapping.get("governed_project_id"),
                target_mapping.get("fact_type_key"),
                target_mapping.get("object_id"),
            )
        )
    return identities


def _contributed_to_identities(fields: Mapping[str, Any]) -> list[tuple[object, object, object]]:
    relations = fields.get("relations")
    identities: list[tuple[object, object, object]] = []
    for relation in relations if isinstance(relations, list) else []:
        if not isinstance(relation, Mapping) or relation.get("relation_key") != "contributed-to":
            continue
        target = relation.get("target")
        target_mapping = target if isinstance(target, Mapping) else {}
        identities.append(
            (
                target_mapping.get("governed_project_id"),
                target_mapping.get("fact_type_key"),
                target_mapping.get("object_id"),
            )
        )
    return sorted(identities, key=repr)


def _close_mapping_issues(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> tuple[FactIssue, ...]:
    """Require the closed after to be the exact projection of the current proposal."""

    issues: list[FactIssue] = []
    for field_name in (
        "title",
        "goal",
        "scope",
        "success_criterion_definitions",
        "success_criterion_results",
        "result_summary",
        "validation_summary",
        "urls",
    ):
        if before.get(field_name, _MISSING) != after.get(field_name, _MISSING):
            issues.append(
                FactIssue(
                    "schema",
                    "close-workcase 必须逐值保留关闭前已成立的终态事实",
                    field_name,
                )
            )

    proposal = before.get("closure_proposal")
    if not isinstance(proposal, Mapping):
        return (
            *issues,
            FactIssue(
                "schema",
                "close-workcase before 必须包含完整 closure_proposal",
                "closure_proposal",
            ),
        )
    for proposal_name, terminal_name in (
        ("proposed_outcome", "closure_outcome"),
        ("proposed_disposition_summary", "disposition_summary"),
    ):
        if proposal.get(proposal_name, _MISSING) != after.get(terminal_name, _MISSING):
            issues.append(
                FactIssue(
                    "schema",
                    f"closed {terminal_name} 必须精确映射 proposal {proposal_name}",
                    terminal_name,
                )
            )

    expected_suggestions = proposal.get("spark_suggestions", _MISSING)
    if expected_suggestions != after.get("spark_suggestions", _MISSING):
        issues.append(
            FactIssue(
                "schema",
                "closed spark_suggestions 必须精确映射 proposal 同名数组",
                "spark_suggestions",
            )
        )

    expected_residuals: list[dict[str, object]] = []
    expected_route_targets: set[tuple[object, object, object]] = set()
    decisions = proposal.get("residual_decisions")
    for decision in decisions if isinstance(decisions, list) else []:
        if not isinstance(decision, Mapping):
            continue
        if decision.get("proposed_disposition") == "accept_stop":
            expected_residuals.append(
                {
                    "residual_id": decision.get("residual_id"),
                    "summary": decision.get("summary"),
                }
            )
        elif decision.get("proposed_disposition") == "route_existing":
            target = decision.get("route_target")
            if isinstance(target, Mapping):
                expected_route_targets.add(
                    (
                        target.get("governed_project_id"),
                        target.get("fact_type_key"),
                        target.get("object_id"),
                    )
                )

    actual_residuals = after.get("residual_responsibilities")
    actual_residual_values = actual_residuals if isinstance(actual_residuals, list) else []
    expected_by_id = {
        value["residual_id"]: value for value in expected_residuals if isinstance(value.get("residual_id"), str)
    }
    actual_by_id = {
        value.get("residual_id"): dict(value)
        for value in actual_residual_values
        if isinstance(value, Mapping) and isinstance(value.get("residual_id"), str)
    }
    if (
        (bool(expected_residuals) != isinstance(actual_residuals, list))
        or len(expected_by_id) != len(expected_residuals)
        or len(actual_by_id) != len(actual_residual_values)
        or actual_by_id != expected_by_id
    ):
        issues.append(
            FactIssue(
                "schema",
                "closed residual_responsibilities 必须按 residual_id 精确等于 proposal 中全部 accept_stop decisions",
                "residual_responsibilities",
            )
        )
    actual_route_targets = set(workcase_routed_target_identities(after))
    if actual_route_targets != expected_route_targets:
        issues.append(
            FactIssue(
                "relation",
                "closed routed-to targets 必须精确等于 proposal 中全部 route decisions 的去重目标集",
                "relations",
            )
        )
    for relation_key in ("contributed-to", "related-to"):
        before_relations = {identity for identity in _relation_identities(before) if identity[0] == relation_key}
        after_relations = {identity for identity in _relation_identities(after) if identity[0] == relation_key}
        if before_relations == after_relations:
            continue
        issues.append(
            FactIssue(
                "relation",
                f"close-workcase after 的 {relation_key} relations 必须与 before 解析后精确相同",
                "relations",
            )
        )
    return tuple(issues)


def _candidate(
    command: WorkCaseWriteCommand,
    before: dict[str, Any],
) -> tuple[FactReadResult, str]:
    layout = LAYOUTS["workcase"]
    fields = _complete_after(command, before, updated_at=command.event_at)
    text = serialize_fact_object(layout, fields, None)
    parsed = parse_yaml_object(text)
    issues = list(parsed.issues)
    if parsed.fields is not None:
        snapshot_issues = validate_fact_object("workcase", parsed.fields, command.schema)
        issues.extend(snapshot_issues)
        if not snapshot_issues:
            issues.extend(
                validate_workcase_transition(
                    before,
                    parsed.fields,
                    operation=command.mode,
                )
            )
    read = FactReadResult(
        layout.canonical_path(command.object_id),
        layout.carrier,
        "invalid" if issues or parsed.fields is None else "mechanically_valid",
        parsed.fields,
        parsed.body,
        tuple(issues),
        raw_text=text,
        raw_byte_count=len(text.encode("utf-8")),
    )
    if read.check_status != "mechanically_valid" or read.fields is None:
        return read, text
    index = _project_index(command)
    key = ("workcase", command.object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index, (key,))
    return index.cache.get(key, read), text


def _event_time_issue(current: FactReadResult, event_at: str) -> FactIssue | None:
    assert current.fields is not None
    before = parse_rfc3339(current.fields.get("updated_at"))
    event = parse_rfc3339(event_at)
    if before is None or event is None or event <= before:
        return FactIssue("schema", "event_at 必须严格晚于当前 updated_at", "updated_at")
    return None


def _update_proposal_route_guard_required(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> bool:
    """Return whether this active update consumes proposal target snapshots."""

    before_phase = before.get("phase")
    after_phase = after.get("phase")
    if after_phase == "human_closure_confirming" and before_phase != after_phase:
        return True
    return (
        after_phase == "closure_preparing"
        and "closure_proposal" in after
        and before.get("closure_proposal", _MISSING) != after.get("closure_proposal", _MISSING)
    )


def _project_stable_route_target_issues(
    index: ProjectFactIndex,
    snapshots: Sequence[WorkCaseRouteTargetSnapshot],
) -> tuple[tuple[FactIssue, ...], bool]:
    """Confirm that freshly read targets remain valid after project relation stabilization."""

    stabilize_project_index(
        index,
        ((snapshot.target.fact_type_key, snapshot.target.object_id) for snapshot in snapshots),
    )
    issues: list[FactIssue] = []
    unavailable = False
    for snapshot in snapshots:
        path = snapshot.origin_path
        target_read = index.cache.get((snapshot.target.fact_type_key, snapshot.target.object_id))
        if target_read is None or target_read.fields is None:
            if target_read is not None and target_read.check_status == "unavailable":
                unavailable = True
                issues.append(
                    FactIssue(
                        "reference",
                        "WorkCase route target 的项目级关系检查当前不可用",
                        path,
                    )
                )
            else:
                issues.append(
                    FactIssue(
                        "relation",
                        "WorkCase route target 的项目级关系未稳定为 mechanically valid 当前对象",
                        path,
                    )
                )
            continue
        if target_read.check_status == "unavailable":
            unavailable = True
            issues.append(
                FactIssue(
                    "reference",
                    "WorkCase route target 的项目级关系检查当前不可用",
                    path,
                )
            )
        elif target_read.check_status != "mechanically_valid":
            issues.append(
                FactIssue(
                    "relation",
                    "WorkCase route target 的项目级关系未稳定为 mechanically valid 当前对象",
                    path,
                )
            )
        elif target_read.content_fingerprint != snapshot.content_fingerprint:
            issues.append(
                FactIssue(
                    "reference",
                    "WorkCase route target content_fingerprint 已变化",
                    path,
                )
            )
    return tuple(issues), unavailable


def _route_checks(
    command: WorkCaseWriteCommand,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    post_write: bool = False,
) -> tuple[tuple[FactIssue, ...], bool, tuple[WorkCaseRouteTargetSnapshot, ...]]:
    issues: list[FactIssue] = []
    if command.mode == "close":
        snapshots, snapshot_issues = proposal_route_target_snapshots(before)
        issues.extend(snapshot_issues)
        issues.extend(validate_workcase_route_target_alignment(after, proposal_snapshots=snapshots))
        existing = frozenset()
    elif command.mode == "correct":
        snapshots = command.route_target_fingerprints
        issues.extend(validate_workcase_route_target_alignment(after, request_snapshots=snapshots))
        existing = workcase_routed_target_identities(before)
    elif command.mode == "update" and _update_proposal_route_guard_required(before, after):
        snapshots, snapshot_issues = proposal_route_target_snapshots(after)
        issues.extend(snapshot_issues)
        existing = frozenset()
    else:
        return (), False, ()

    if issues:
        return tuple(issues), False, tuple(snapshots)
    if not snapshots:
        return (), False, ()
    index = _project_index(command)
    target_issues, unavailable = validate_workcase_route_target_snapshots(
        index,
        command.object_id,
        snapshots,
        existing_routed_targets=existing,
    )
    issues.extend(target_issues)
    if not issues and not unavailable:
        stable_issues, stable_unavailable = _project_stable_route_target_issues(index, snapshots)
        issues.extend(stable_issues)
        unavailable = stable_unavailable
    if post_write and unavailable:
        issues.append(FactIssue("reference", "写后未能重新确认全部 route targets"))
    return tuple(issues), unavailable, tuple(snapshots)


def _route_alignment_issues(
    command: WorkCaseWriteCommand,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> tuple[FactIssue, ...]:
    """Validate request/after target identity alignment without reading targets."""

    if command.mode == "close":
        snapshots, snapshot_issues = proposal_route_target_snapshots(before)
        return (
            *snapshot_issues,
            *validate_workcase_route_target_alignment(after, proposal_snapshots=snapshots),
        )
    if command.mode == "correct":
        return validate_workcase_route_target_alignment(
            after,
            request_snapshots=command.route_target_fingerprints,
        )
    return ()


def _new_contributed_to_issues(
    command: WorkCaseWriteCommand,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> tuple[tuple[FactIssue, ...], bool]:
    """Require every newly formed WorkCase contribution edge to target a current draft Pitfall."""

    if command.mode != "update":
        return (), False
    before_edges = {identity for identity in _relation_identities(before) if identity[0] == "contributed-to"}
    new_edges = [identity for identity in _relation_identities(after) - before_edges if identity[0] == "contributed-to"]
    if not new_edges:
        return (), False
    issues: list[FactIssue] = []
    if before.get("status") == "blocked" or after.get("status") == "blocked":
        issues.append(FactIssue("relation", "blocked WorkCase 禁止形成 contributed-to", "relations"))
    if after.get("phase") == "human_closure_confirming":
        issues.append(FactIssue("relation", "human_closure_confirming 禁止形成 contributed-to", "relations"))
    index = _project_index(command)
    unavailable = False
    for _, project_id, target_type, target_id in new_edges:
        if project_id != index.governed_project_id or target_type != "pitfall" or not isinstance(target_id, str):
            continue
        target_read = index.read_fresh("pitfall", target_id)
        if target_read is not None and target_read.check_status == "unavailable":
            unavailable = True
            issues.append(FactIssue("reference", "新 contributed-to target 当前不可用", "relations"))
            continue
        if target_read is None or target_read.check_status in {"not_found", "invalid"} or target_read.fields is None:
            issues.append(FactIssue("relation", "新 contributed-to target 必须是可读的 mechanically valid draft Pitfall", "relations"))
            continue
        if target_read.fields.get("status") != "draft":
            issues.append(FactIssue("relation", "新 contributed-to 只能指向 status=draft Pitfall", "relations"))
    return tuple(issues), unavailable


def _request_source_reference_issues(command: WorkCaseWriteCommand) -> tuple[FactIssue, ...]:
    problems = [
        problem
        for index, reference in enumerate(command.authorization_reference)
        for problem in validate_source_reference(reference, f"authorization_reference[{index}]")
    ]
    if command.independent_review_reference is not None:
        problems.extend(
            validate_source_reference(
                command.independent_review_reference,
                "independent_review_reference",
            )
        )
    return tuple(FactIssue("schema", problem.summary, problem.path) for problem in problems)


def apply_workcase_write_locked(command: WorkCaseWriteCommand) -> WorkCaseWriteResult:
    """Apply one WorkCase write while the caller holds the WorkCase type lock."""

    reference_issues = _request_source_reference_issues(command)
    if (
        command.schema.fact_type_key != "workcase"
        or command.schemas.get("workcase") != command.schema
        or any(field in command.supplied for field in MANAGED_FIELDS)
        or reference_issues
    ):
        issues: tuple[FactIssue, ...] = reference_issues or (
            FactIssue(
                "schema",
                "WorkCase 写入必须使用当前 schema、完整非托管 after 与有效来源回指",
            ),
        )
        return _result(
            command,
            "invalid_request",
            issues=issues,
        )

    current = _project_read(command)
    if current.check_status == "unavailable" or current.fields is None:
        status: UpdateStatus = "current_unavailable" if current.check_status == "unavailable" else "current_rejected"
        return _result(command, status, issues=current.issues, current=current)
    if current.check_status != "mechanically_valid":
        return _result(command, "current_rejected", issues=current.issues, current=current)
    if current.content_fingerprint != command.expected_content_fingerprint or current.raw_text is None:
        return _result(command, "fingerprint_stale", current=current)

    preview = _complete_after(command, current.fields, updated_at=current.fields["updated_at"])
    boundary_issues = _operation_boundary_issues(command, current.fields, preview)
    alignment_issues = _route_alignment_issues(command, current.fields, preview)
    if boundary_issues or alignment_issues:
        return _result(
            command,
            "candidate_rejected",
            issues=(*boundary_issues, *alignment_issues),
            current=current,
        )

    mutable_current = {key: value for key, value in current.fields.items() if key not in MANAGED_FIELDS}
    gate_issues = _gate_issues(command, current.fields, preview)
    close_mapping_issues = _close_mapping_issues(current.fields, preview) if command.mode == "close" else ()
    preflight_issues = (
        *gate_issues,
        *close_mapping_issues,
    )
    if preflight_issues:
        return _result(command, "candidate_rejected", issues=preflight_issues, current=current)

    route_issues, route_unavailable, _snapshots = _route_checks(
        command,
        current.fields,
        preview,
    )
    if route_issues or route_unavailable:
        status = "candidate_unavailable" if route_unavailable else "candidate_rejected"
        return _result(command, status, issues=route_issues, current=current)

    contribution_issues, contribution_unavailable = _new_contributed_to_issues(
        command,
        current.fields,
        preview,
    )
    if contribution_issues or contribution_unavailable:
        status = "candidate_unavailable" if contribution_unavailable else "candidate_rejected"
        return _result(command, status, issues=contribution_issues, current=current)

    if mutable_current == dict(command.supplied):
        return _result(command, "no_change", current=current, readback=current)

    if command.mode == "close":
        dependency_index = _project_index(command)
        dependency_issues, dependency_unavailable = validate_workcase_incoming_dependencies(
            dependency_index,
            command.object_id,
        )
        if dependency_issues or dependency_unavailable:
            status = "candidate_unavailable" if dependency_unavailable else "candidate_rejected"
            return _result(command, status, issues=dependency_issues, current=current)

    time_issue = _event_time_issue(current, command.event_at)
    if time_issue is not None:
        return _result(
            command,
            "event_time_not_successor",
            issues=(time_issue,),
            current=current,
        )

    candidate, candidate_text = _candidate(command, current.fields)
    if candidate.check_status != "mechanically_valid":
        status = "candidate_unavailable" if candidate.check_status == "unavailable" else "candidate_rejected"
        return _result(
            command,
            status,
            issues=candidate.issues,
            current=current,
            candidate=candidate,
            candidate_text=candidate_text,
        )

    layout = LAYOUTS["workcase"]
    replacement = atomic_replace_text_if_unchanged(
        command.boundary.worktree_root,
        layout,
        command.object_id,
        current.raw_text,
        candidate_text,
    )
    if replacement.outcome != "replaced" or replacement.namespace_state != "committed":
        status = "replacement_conflict" if replacement.outcome == "conflict" else "replacement_unavailable"
        return _result(
            command,
            status,
            current=current,
            candidate=candidate,
            candidate_text=candidate_text,
            replacement_result=replacement,
        )

    readback = _project_read(command)
    readback_issues: tuple[FactIssue, ...] = readback.issues
    if readback.check_status == "mechanically_valid" and readback.raw_text != candidate_text:
        readback_issues = (
            *readback_issues,
            FactIssue("parse", "写后回读 bytes 与本次 WorkCase payload 不一致"),
        )

    post_route_issues, post_route_unavailable, _post_snapshots = _route_checks(
        command,
        current.fields,
        readback.fields if readback.fields is not None else preview,
        post_write=True,
    )
    post_dependency_issues: tuple[FactIssue, ...] = ()
    post_dependency_unavailable = False
    if command.mode == "close":
        post_dependency_index = _project_index(command)
        post_dependency_issues, post_dependency_unavailable = validate_workcase_incoming_dependencies(
            post_dependency_index,
            command.object_id,
        )
        if post_dependency_unavailable:
            post_dependency_issues = (
                *post_dependency_issues,
                FactIssue("reference", "写后未能重新确认全部入向 depends-on"),
            )
    readback_ok = (
        readback.check_status == "mechanically_valid"
        and readback.fields is not None
        and readback.raw_text == candidate_text
        and not post_route_issues
        and not post_route_unavailable
        and not post_dependency_issues
        and not post_dependency_unavailable
    )
    if not readback_ok:
        rollback = atomic_replace_text_if_unchanged(
            command.boundary.worktree_root,
            layout,
            command.object_id,
            candidate_text,
            current.raw_text,
        )
        rolled_back = rollback.outcome == "replaced" and rollback.namespace_state == "committed"
        residual_readback = None if rolled_back else _project_read(command)
        return _result(
            command,
            "readback_failed",
            issues=(*readback_issues, *post_route_issues, *post_dependency_issues),
            current=current,
            candidate=candidate,
            readback=readback,
            candidate_text=candidate_text,
            replacement_result=replacement,
            rollback_result=rollback,
            residual_readback=residual_readback,
        )

    return _result(
        command,
        "updated",
        current=current,
        candidate=candidate,
        readback=readback,
        candidate_text=candidate_text,
        replacement_result=replacement,
    )


def apply_workcase_write(command: WorkCaseWriteCommand) -> WorkCaseWriteResult:
    """Validate, lock, CAS-replace, re-read targets, and conditionally roll back."""

    if not durable_writes_enabled():
        return _result(command, "durability_unavailable")
    completed: WorkCaseWriteResult | None = None
    try:
        with allocation_lock(command.boundary, LAYOUTS["workcase"]):
            completed = apply_workcase_write_locked(command)
    except OSError:
        if completed is None:
            raise
        return replace(completed, coordination_release_uncertain=True)
    assert completed is not None
    return completed


__all__ = [
    "WorkCaseWriteCommand",
    "WorkCaseWriteMode",
    "WorkCaseWriteResult",
    "apply_workcase_write",
    "apply_workcase_write_locked",
]
