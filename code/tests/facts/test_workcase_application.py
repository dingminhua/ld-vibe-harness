from __future__ import annotations

import ast
import subprocess
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from ldvh.facts import workcase_update
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, serialize_fact_object
from ldvh.facts.models import FactIssue, FactReference
from ldvh.facts.relations import ProjectFactIndex, WorkCaseRouteTargetSnapshot
from ldvh.facts.repository import read_fact_object
from ldvh.facts.schema import FactSchema
from ldvh.facts.update_application import MANAGED_FIELDS
from ldvh.facts.workcase_projection import approval_baseline_fingerprint
from ldvh.facts.workcase_update import WorkCaseWriteCommand, apply_workcase_write
from ldvh.filesystem import AtomicWriteResult
from ldvh.time import canonical_utc_timestamp


def _git(project: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@dataclass(frozen=True, slots=True)
class _Project:
    boundary: CreationBoundary
    schemas: Mapping[str, FactSchema]


def _project(current_fact_schemas: Mapping[str, FactSchema], tmp_path: Path) -> _Project:
    root = tmp_path / "project"
    root.mkdir()
    _git(root, "init", "-q")
    common_dir = Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return _Project(CreationBoundary("sample", root, common_dir), current_fact_schemas)


def _write(project: _Project, fields: dict[str, Any]) -> Path:
    object_id = fields["object_id"]
    path = project.boundary.worktree_root / LAYOUTS["workcase"].canonical_path(object_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_fact_object(LAYOUTS["workcase"], fields, None), encoding="utf-8")
    return path


def _read(project: _Project, object_id: str):
    return read_fact_object(
        project.boundary.worktree_root,
        LAYOUTS["workcase"],
        project.schemas["workcase"],
        object_id,
        expected_common_dir=project.boundary.git_common_dir,
    )


def _supplied(fields: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in fields.items() if key not in MANAGED_FIELDS}


def _review(version: int = 1) -> dict[str, Any]:
    return {
        "reviewer": "independent-reviewer",
        "reviewed_at": "2026-07-26T10:30:00+08:00",
        "subject_version": version,
        "scope": "检查当前版本的完整性、边界和隐藏风险。",
        "conclusion": "pass",
    }


def _creation_review(version: int = 1) -> dict[str, Any]:
    return {
        **_review(version),
        "covered_quality_gate_ids": ["independent-result-review"],
    }


def _authorization() -> dict[str, Any]:
    return {
        "authorized_actions": [
            {
                "action_id": "authorization-bounded-write",
                "summary": "写入当前测试责任的有界结果。",
                "target_scope": "当前临时项目的目标 WorkCase 与测试文件。",
                "effect_scope": "有界工作区写入和只读独立复核。",
                "risk_summary": "保留无关既有变更。",
                "rollback_summary": "只回退本次新增的有界内容。",
                "rule_refs": ["specs/21", "specs/06"],
            },
            {
                "action_id": "authorization-delegate-independent-review",
                "summary": "委派独立结果复核。",
                "target_scope": "当前测试 WorkCase 的结果。",
                "effect_scope": "只读 Reviewer 委派。",
                "risk_summary": "声明不证明真实独立性。",
                "rollback_summary": "不持久化委派收据。",
                "rule_refs": ["specs/21"],
            },
            {
                "action_id": "authorization-independent-result-review",
                "summary": "执行独立结果复核。",
                "target_scope": "当前测试 WorkCase 的结果。",
                "effect_scope": "只读结果复核。",
                "risk_summary": "复核是咨询性结论。",
                "rollback_summary": "不自动接受任何结果。",
                "rule_refs": ["specs/21"],
            },
        ],
        "quality_gates": [
            {
                "gate_id": "independent-result-review",
                "reviewer_mode": "independent-read-only",
                "delegation_action_id": "authorization-delegate-independent-review",
                "result_review_action_id": "authorization-independent-result-review",
            }
        ],
        "action_ceiling": "禁止外部发布和无关对象变化。",
        "prohibited_actions": ["push", "publish"],
        "allowed_adjustments": "允许在同一范围内调整实现方法。",
        "verification_and_rollback": "运行有界检查并保留可恢复检查点。",
        "out_of_bounds_handling": "取消受影响工作项并收敛到关闭。",
    }


def _active(
    object_id: str,
    *,
    title: str = "当前工作责任",
) -> dict[str, Any]:
    return {
        "object_id": object_id,
        "fact_type_key": "workcase",
        "title": title,
        "created_at": "2026-07-26T09:00:00+08:00",
        "updated_at": "2026-07-26T11:00:00+08:00",
        "change_log": [
            {
                "signature": {"agent_id": "test-agent", "host_environment": "test"},
                "session_id": "test-session",
                "at": "2026-07-26T09:00:00+08:00",
                "summary": "建立测试 WorkCase。",
            }
        ],
        "status": "open",
        "goal": "形成一个可由 Human 判断的完整结果。",
        "scope": "只处理当前测试责任。",
        "execution_authorization": _authorization(),
        "success_criterion_definitions": [{"criterion_id": "criterion-main", "statement": "当前责任形成稳定结果。"}],
        "priority": "P2",
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "work_items": [
            {
                "item_id": "item-main",
                "goal": "完成当前责任。",
                "expected_result": "形成可检查的结果。",
                "status": "pending",
            }
        ],
        "creation_reviews": [_creation_review()],
        "waiting_on": "等待 Human 确认当前计划。",
    }


def _closing(
    object_id: str,
    *,
    outcome: str = "completed",
    target: WorkCaseRouteTargetSnapshot | None = None,
) -> dict[str, Any]:
    criterion_outcome = "satisfied" if outcome == "completed" else "not_satisfied"
    proposal: dict[str, Any] = {
        "proposed_outcome": outcome,
        "proposed_disposition_summary": (
            "当前责任完整结束。" if outcome == "completed" else "未完成责任转交给目标 WorkCase。"
        ),
    }
    if target is not None:
        proposal["residual_decisions"] = [
            {
                "residual_id": "residual-main",
                "summary": "继续承担当前未完成责任。",
                "proposed_disposition": "route_existing",
                "route_target": {
                    **target.target.to_json(),
                    "content_fingerprint": target.content_fingerprint,
                },
            }
        ]
    fields = {
        "object_id": object_id,
        "fact_type_key": "workcase",
        "title": "等待关闭的责任",
        "created_at": "2026-07-26T09:00:00+08:00",
        "updated_at": "2026-07-26T12:00:00+08:00",
        "change_log": [
            {
                "signature": {"agent_id": "test-agent", "host_environment": "test"},
                "session_id": "test-session",
                "at": "2026-07-26T09:00:00+08:00",
                "summary": "建立测试 WorkCase。",
            }
        ],
        "status": "open",
        "goal": "形成一个可由 Human 判断的完整结果。",
        "scope": "只处理当前测试责任。",
        "execution_authorization": _authorization(),
        "success_criterion_definitions": [{"criterion_id": "criterion-main", "statement": "当前责任形成稳定结果。"}],
        "success_criterion_results": [
            {
                "criterion_id": "criterion-main",
                "outcome": criterion_outcome,
                "summary": "按实际结果形成的标准判断。",
            }
        ],
        "priority": "P2",
        "phase": "human_closure_confirming",
        "plan_version": 1,
        "creation_reviews": [_creation_review()],
        "work_items": [
            {
                "item_id": "item-main",
                "goal": "完成当前责任。",
                "expected_result": "形成可检查的结果。",
                "status": "completed",
                "result_summary": "已形成当前局部结果。",
            }
        ],
        "result_version": 1,
        "result_summary": "当前完整结果已经形成。",
        "controller_check_summary": "主控已检查结果与标准判断的一致性。",
        "result_reviews": [_review()],
        "validation_summary": "已检查当前测试边界，未覆盖外部系统。",
        "closure_proposal": proposal,
        "waiting_on": "等待 Human 判断关闭与责任处置。",
    }
    fields["execution_approval"] = {
        "subject_version": 1,
        "approved_at": "2026-07-26T10:00:00+08:00",
        "summary": "Human 批准当前计划。",
        "baseline_fingerprint": approval_baseline_fingerprint(fields),
        "source_refs": ["turn:gate1"],
    }
    return fields


def _preparing(
    object_id: str,
    *,
    outcome: str = "completed",
    target: WorkCaseRouteTargetSnapshot | None = None,
    include_proposal: bool = True,
) -> dict[str, Any]:
    fields = _closing(object_id, outcome=outcome, target=target)
    fields["phase"] = "closure_preparing"
    fields.pop("waiting_on")
    if not include_proposal:
        fields.pop("closure_proposal")
    return fields


def _snapshot(project: _Project, fields: dict[str, Any]) -> WorkCaseRouteTargetSnapshot:
    _write(project, fields)
    read = _read(project, fields["object_id"])
    assert read.content_fingerprint is not None
    return WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", fields["object_id"]),
        read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )


def _closed_from(before: dict[str, Any]) -> dict[str, Any]:
    proposal = before["closure_proposal"]
    fields = {
        "object_id": before["object_id"],
        "fact_type_key": "workcase",
        "title": before["title"],
        "created_at": before["created_at"],
        "updated_at": "2026-07-26T13:00:00+08:00",
        "status": "closed",
        "goal": before["goal"],
        "scope": before["scope"],
        "success_criterion_definitions": before["success_criterion_definitions"],
        "success_criterion_results": before["success_criterion_results"],
        "result_summary": before["result_summary"],
        "validation_summary": before["validation_summary"],
        "change_log": deepcopy(before["change_log"]),
        "closure_outcome": proposal["proposed_outcome"],
        "disposition_summary": proposal["proposed_disposition_summary"],
    }
    decisions = proposal.get("residual_decisions", [])
    residuals = [
        {"residual_id": item["residual_id"], "summary": item["summary"]}
        for item in decisions
        if item["proposed_disposition"] == "accept_stop"
    ]
    if residuals:
        fields["residual_responsibilities"] = residuals
    if "spark_suggestions" in proposal:
        fields["spark_suggestions"] = [dict(item) for item in proposal["spark_suggestions"]]
    route_targets = {
        (
            item["route_target"]["governed_project_id"],
            item["route_target"]["fact_type_key"],
            item["route_target"]["object_id"],
        )
        for item in decisions
        if item["proposed_disposition"] == "route_existing"
    }
    if route_targets:
        fields["relations"] = [
            {
                "relation_key": "routed-to",
                "target": {
                    "governed_project_id": project_id,
                    "fact_type_key": fact_type_key,
                    "object_id": object_id,
                },
            }
            for project_id, fact_type_key, object_id in sorted(route_targets)
        ]
    return fields


def test_closed_candidate_projection_is_complete_nonmanaged_and_matches_close_after() -> None:
    before = _closing("workcase-0006", outcome="completed")
    before["urls"] = _url()
    before["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "spark",
                "object_id": "spark-0001",
            },
        }
    ]

    candidate = workcase_update.project_closed_workcase_candidate(before)
    expected = _closed_from(before)
    for managed in ("object_id", "fact_type_key", "created_at", "updated_at"):
        expected.pop(managed)
    expected["urls"] = before["urls"]
    expected["relations"] = before["relations"]

    assert candidate == expected
    closed_after = _closed_from(before) | {"urls": before["urls"], "relations": before["relations"]}
    assert workcase_update._close_mapping_issues(before, closed_after) == ()


def test_closed_candidate_projection_deduplicates_routes_and_separates_fingerprint_basis() -> None:
    before = _closing(
        "workcase-0006",
        outcome="partial",
        target=WorkCaseRouteTargetSnapshot(
            FactReference("sample", "workcase", "workcase-0008"),
            "a" * 64,
            "proposal",
        ),
    )
    before["closure_proposal"]["residual_decisions"].append(
        dict(before["closure_proposal"]["residual_decisions"][0], residual_id="residual-second")
    )

    candidate = workcase_update.project_closed_workcase_candidate(before)
    basis, issues = workcase_update.proposal_route_target_basis(before)

    assert candidate["relations"] == [
        {
            "relation_key": "routed-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": "workcase-0008",
            },
        }
    ]
    assert basis == [
        {
            "target": candidate["relations"][0]["target"],
            "content_fingerprint": "a" * 64,
        }
    ]
    assert issues == ()


def test_close_replaces_same_target_related_to_with_routed_to(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target = _snapshot(project, _active("workcase-0008"))
    unrelated_target = _snapshot(project, _active("workcase-0009"))
    before = _closing("workcase-0001", outcome="partial", target=target)
    before["success_criterion_definitions"].append(
        {"criterion_id": "criterion-complete", "statement": "已形成可保留的局部结果。"}
    )
    before["success_criterion_results"].append(
        {"criterion_id": "criterion-complete", "outcome": "satisfied", "summary": "局部结果已验证。"}
    )
    before["relations"] = [
        {
            "relation_key": "related-to",
            "target": target.target.to_json(),
        },
        {
            "relation_key": "related-to",
            "target": unrelated_target.target.to_json(),
        },
    ]
    before["execution_approval"]["baseline_fingerprint"] = approval_baseline_fingerprint(before)
    _write(project, before)

    after = workcase_update.project_closed_workcase_candidate(before)
    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["relations"] == [
        {"relation_key": "related-to", "target": unrelated_target.target.to_json()},
        {"relation_key": "routed-to", "target": target.target.to_json()},
    ]


def _command(
    project: _Project,
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    mode: workcase_update.WorkCaseWriteMode,
    authorization_reference: tuple[dict[str, Any], ...] = (),
    route_target_fingerprints: tuple[WorkCaseRouteTargetSnapshot, ...] = (),
    independent_review_reference: dict[str, Any] | None = None,
    event_at: str = "2026-07-26T13:00:00+08:00",
) -> WorkCaseWriteCommand:
    current = _read(project, before["object_id"])
    assert current.check_status == "mechanically_valid", current.issues
    assert current.content_fingerprint is not None
    candidate_after = deepcopy(after)
    current_fields = current.fields
    assert current_fields is not None
    candidate_log = candidate_after.get("change_log")
    before_log = before.get("change_log")
    current_log = current_fields.get("change_log")
    # A preceding write may have appended a Code-owned history entry while
    # the test's logical ``before`` snapshot is intentionally stale.  Build
    # the next complete after from the actual CAS snapshot, then append the
    # one event required by the update contract.
    if (
        isinstance(candidate_log, list)
        and candidate_log == before_log
        and isinstance(current_log, list)
    ):
        candidate_after["change_log"] = deepcopy(current_log)
    if (
        _supplied(candidate_after) != _supplied(current_fields)
        and isinstance(candidate_after.get("change_log"), list)
        and candidate_after.get("change_log") == current_log
    ):
        candidate_after["change_log"] = [
            *candidate_after["change_log"],
            {
                "signature": {"agent_id": "test-agent", "host_environment": "test"},
                "session_id": "test-session",
                "at": "2000-01-01T00:00:00Z",
                "summary": "更新测试 WorkCase。",
            },
        ]
    return WorkCaseWriteCommand(
        boundary=project.boundary,
        schemas=project.schemas,
        schema=project.schemas["workcase"],
        object_id=before["object_id"],
        expected_content_fingerprint=current.content_fingerprint,
        supplied=_supplied(candidate_after),
        event_at=event_at,
        mode=mode,
        authorization_reference=authorization_reference,
        route_target_fingerprints=route_target_fingerprints,
        independent_review_reference=independent_review_reference,
    )


def _human_reference() -> tuple[dict[str, Any], ...]:
    return ({"kind": "conversation", "locator": "human-decision"},)


def _termination_for(before: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    snapshots = []
    for item in before["work_items"]:
        summary = next(
            (
                item[name]
                for name in ("result_summary", "current_summary", "blocking_summary", "resume_from")
                if name in item
            ),
            "no-runtime-summary",
        )
        snapshots.append(f"{item['item_id']}::{item['status']}::{summary}")
    return {
        "initiated_at": "2026-07-26T13:00:00+08:00",
        "source_status": before["status"],
        "source_phase": before["phase"],
        "source_content_fingerprint": fingerprint,
        "reason": "Human instructed the WorkCase to stop and wind down.",
        "source_refs": ["human-decision"],
        "item_snapshots": sorted(snapshots),
        "quality_steps": [
            "independent_result_review:not_reached",
            "closure_proposal:not_reached",
            "gate_2:not_reached",
        ],
        "cleanup_status": "pending",
        "cleanup_summary": "The original plan is frozen; cleanup inventory is pending.",
    }


def test_begin_update_and_complete_termination_use_one_human_instruction(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0084")
    _write(project, before)
    current = _read(project, before["object_id"])
    assert current.content_fingerprint is not None

    begun_after = deepcopy(before)
    begun_after["status"] = "open"
    begun_after["phase"] = "termination_preparing"
    for name in ("waiting_on", "blocking_summary", "summary", "resume_from"):
        begun_after.pop(name, None)
    begun_after["termination"] = _termination_for(before, current.content_fingerprint)
    begun = apply_workcase_write(
        _command(
            project,
            before,
            begun_after,
            mode="begin_termination",
            authorization_reference=_human_reference(),
        )
    )
    assert begun.status == "updated", begun.issues
    assert begun.readback is not None and begun.readback.fields is not None
    assert begun.readback.fields["phase"] == "termination_preparing"

    cleanup_before = deepcopy(begun.readback.fields)
    cleanup_after = deepcopy(cleanup_before)
    termination = deepcopy(cleanup_after["termination"])
    termination.update(
        {
            "retained_scope": ["The already formed bounded result."],
            "discarded_scope": ["none-observed: no physical discard was requested"],
            "unverified_scope": ["No additional environment matrix was run after termination."],
            "relationship_impacts": ["none-observed: no inbound dependency or routed responsibility"],
            "quality_steps": [
                "independent_result_review:actual",
                "closure_proposal:skipped",
                "gate_2:skipped",
            ],
            "cleanup_status": "completed",
            "cleanup_summary": "Retained work and validation gaps were recorded; no physical discard was requested.",
        }
    )
    cleanup_after["termination"] = termination
    invalid_cleanup_after = deepcopy(cleanup_after)
    invalid_cleanup_after["termination"]["quality_steps"][-1] = "gate_2:invented"
    invalid_cleanup = apply_workcase_write(
        _command(
            project,
            cleanup_before,
            invalid_cleanup_after,
            mode="update",
            event_at="2026-07-26T13:30:00+08:00",
        )
    )
    assert invalid_cleanup.status == "candidate_rejected"
    assert any("quality_steps" in issue.field_path for issue in invalid_cleanup.issues)

    cleaned = apply_workcase_write(
        _command(project, cleanup_before, cleanup_after, mode="update", event_at="2026-07-26T14:00:00+08:00")
    )
    assert cleaned.status == "updated", cleaned.issues
    assert cleaned.readback is not None and cleaned.readback.fields is not None

    completed_before = deepcopy(cleaned.readback.fields)
    closed = {
        "object_id": completed_before["object_id"],
        "fact_type_key": "workcase",
        "title": completed_before["title"],
        "created_at": completed_before["created_at"],
        "updated_at": completed_before["updated_at"],
        "change_log": deepcopy(completed_before["change_log"]),
        "status": "closed",
        "goal": completed_before["goal"],
        "scope": completed_before["scope"],
        "success_criterion_definitions": deepcopy(completed_before["success_criterion_definitions"]),
        "success_criterion_results": deepcopy(completed_before["success_criterion_results"]),
        "result_summary": completed_before["result_summary"],
        "validation_summary": completed_before["validation_summary"],
        "closure_outcome": "completed",
        "disposition_summary": (
            "Human-initiated termination retained the completed bounded result and recorded skipped gates."
        ),
        "termination": deepcopy(completed_before["termination"]),
    }
    routed_closed = deepcopy(closed)
    routed_closed["relations"] = [
        {
            "relation_key": "routed-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": "workcase-0086",
            },
        }
    ]
    routed_rejected = apply_workcase_write(
        _command(
            project,
            completed_before,
            routed_closed,
            mode="complete_termination",
            event_at="2026-07-26T14:30:00+08:00",
        )
    )
    assert routed_rejected.status == "candidate_rejected"
    assert any("不创建 routed-to" in issue.summary for issue in routed_rejected.issues)

    dependent = _active("workcase-0085", title="Dependent responsibility")
    dependent["relations"] = [
        {
            "relation_key": "depends-on",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": completed_before["object_id"],
            },
        }
    ]
    dependent_path = _write(project, dependent)
    rejected = apply_workcase_write(
        _command(
            project,
            completed_before,
            closed,
            mode="complete_termination",
            event_at="2026-07-26T15:00:00+08:00",
        )
    )
    assert rejected.status == "candidate_rejected"
    assert any("depends-on" in issue.summary for issue in rejected.issues)
    dependent_path.unlink()

    completed = apply_workcase_write(
        _command(
            project,
            completed_before,
            closed,
            mode="complete_termination",
            event_at="2026-07-26T15:00:00+08:00",
        )
    )
    assert completed.status == "updated", completed.issues
    assert completed.readback is not None and completed.readback.fields is not None
    assert completed.readback.fields["status"] == "closed"
    assert completed.readback.fields["termination"]["quality_steps"][-1] == "gate_2:skipped"


def _review_reference() -> dict[str, Any]:
    return {"kind": "conversation", "locator": "independent-review"}


def _url() -> list[dict[str, str]]:
    return [
        {
            "ref": "https://example.com/current-source",
            "title": "当前外部资料",
            "summary": "只支持当前更正的有限范围。",
        }
    ]


def test_workcase_transaction_has_no_helper_dependency() -> None:
    module = Path(__file__).resolve().parents[2] / "ldvh/facts/workcase_update.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names} | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any(name == "ldvh.helper" or name.startswith("ldvh.helper.") for name in imports)


@pytest.mark.parametrize(
    ("current_time", "event_time", "expected_status"),
    [
        (
            "2026-07-26T11:00:00.1234567+08:00",
            "2026-07-26T11:00:00.1234568+08:00",
            "updated",
        ),
        (
            "2026-07-26T11:00:00.1234568+08:00",
            "2026-07-26T11:00:00.1234567+08:00",
            "event_time_not_successor",
        ),
        (
            "2026-07-26T11:00:00+08:00",
            "2026-07-26T12:00:00-00:00",
            "event_time_not_successor",
        ),
    ],
)
def test_workcase_update_compares_fractional_seconds_beyond_microseconds_without_loss(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    current_time: str,
    event_time: str,
    expected_status: str,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    before["updated_at"] = current_time
    path = _write(project, before)
    after = deepcopy(before)
    after["waiting_on"] = "等待 Human 对当前计划作出新的明确决定。"
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="update",
            event_at=event_time,
        )
    )

    assert result.status == expected_status
    if expected_status == "updated":
        assert result.readback is not None and result.readback.fields is not None
        assert result.readback.fields["updated_at"] == canonical_utc_timestamp(event_time)
    else:
        assert path.read_bytes() == original


@pytest.mark.parametrize(
    "authorization_reference",
    [
        ({"x": 1},),
        ({"kind": "   ", "locator": "\t", "extra": True},),
        (
            {
                "kind": "human",
                "locator": "turn:12",
                "observed_at": "2026-07-27T10:20:30+08:60",
            },
        ),
    ],
)
def test_core_close_rejects_malformed_authorization_before_read_or_write(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    authorization_reference: tuple[dict[str, Any], ...],
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0001")
    path = _write(project, before)
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            before,
            _closed_from(before),
            mode="close",
            authorization_reference=authorization_reference,
        )
    )

    assert result.status == "invalid_request"
    assert result.current is None
    assert result.candidate is None
    assert result.replacement_result is None
    assert any(issue.field_path.startswith("authorization_reference[0]") for issue in result.issues)
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    ("authorization_reference", "independent_review_reference", "expected_path"),
    [
        (({"x": 1},), _review_reference(), "authorization_reference[0]"),
        (
            _human_reference(),
            {"kind": "review", "locator": "\t", "extra": True},
            "independent_review_reference",
        ),
    ],
)
def test_core_substantive_correction_rejects_malformed_gate_references_before_read_or_write(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    authorization_reference: tuple[dict[str, Any], ...],
    independent_review_reference: dict[str, Any],
    expected_path: str,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closed_from(_closing("workcase-0001"))
    before["updated_at"] = "2026-07-26T12:00:00+08:00"
    path = _write(project, before)
    original = path.read_bytes()
    after = {**before, "title": "实质更正后的标题", "urls": _url()}

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="correct",
            authorization_reference=authorization_reference,
            independent_review_reference=independent_review_reference,
        )
    )

    assert result.status == "invalid_request"
    assert result.current is None
    assert result.candidate is None
    assert result.replacement_result is None
    assert any(issue.field_path.startswith(expected_path) for issue in result.issues)
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    ("field_name", "changed_value"),
    [
        ("goal", "更正后的目标。"),
        ("scope", "更正后的范围。"),
        (
            "success_criterion_definitions",
            [{"criterion_id": "criterion-main", "statement": "更正后的成功标准。"}],
        ),
        (
            "success_criterion_results",
            [
                {
                    "criterion_id": "criterion-main",
                    "outcome": "satisfied",
                    "summary": "更正后的标准结果。",
                }
            ],
        ),
        ("result_summary", "更正后的总体结果。"),
        ("validation_summary", "更正后的验证边界。"),
        ("closure_outcome", "cancelled"),
        ("disposition_summary", "更正后的终态处置。"),
        (
            "residual_responsibilities",
            [{"residual_id": "residual-main", "summary": "更正后的剩余责任。"}],
        ),
        (
            "relations",
            [
                {
                    "relation_key": "routed-to",
                    "target": {
                        "governed_project_id": "sample",
                        "fact_type_key": "workcase",
                        "object_id": "workcase-0002",
                    },
                }
            ],
        ),
    ],
)
def test_each_substantive_closed_root_requires_review_and_human_references(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    field_name: str,
    changed_value: object,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closed_from(_closing("workcase-0001"))
    before["updated_at"] = "2026-07-26T12:00:00+08:00"
    _write(project, before)
    after = {**before, field_name: changed_value}
    command = _command(project, before, after, mode="correct")

    issues = workcase_update._gate_issues(command, before, after)

    assert {issue.field_path for issue in issues} == {
        "independent_review_reference",
        "authorization_reference",
    }


def test_update_workcase_applies_one_full_after_and_core_managed_fields(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    after = {**before, "title": "修正后的当前责任"}

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["object_id"] == before["object_id"]
    assert result.readback.fields["created_at"] == before["created_at"]
    assert result.readback.fields["updated_at"] == canonical_utc_timestamp("2026-07-26T13:00:00+08:00")
    assert result.readback.fields["title"] == "修正后的当前责任"
    assert path.read_text(encoding="utf-8") == result.candidate_text


def test_plan_delta_item_execution_fact_removal_without_updated_summary_has_zero_writes(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _gate1_after(_active("workcase-0001"))
    before.update(
        {
            "summary": "保留中的跨 item 稳定检查点。",
            "work_items": [
                {
                    **before["work_items"][0],
                    "status": "in_progress",
                    "current_summary": "旧 item 已形成需要承接的执行事实。",
                    "resume_from": "从旧 item 的当前边界继续。",
                }
            ],
        }
    )
    path = _write(project, before)
    original_bytes = path.read_bytes()

    after = deepcopy(before)
    after.update(
        {
            "phase": "plan_revising",
            "plan_version": 2,
            "work_items": [
                {
                    "item_id": "item-new",
                    "goal": "完成修订后的责任。",
                    "expected_result": "形成修订后的可检查结果。",
                    "status": "pending",
                }
            ],
            "creation_reviews": [_creation_review(2)],
        }
    )

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "work_items" and "可回读承接载体" in issue.summary for issue in result.issues)
    assert path.read_bytes() == original_bytes


@pytest.mark.parametrize("release_stage", ["unlock", "descriptor close"])
def test_committed_workcase_result_survives_coordination_release_failure(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    release_stage: str,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    after = {**before, "title": "已提交且回读成功的责任"}
    command = _command(project, before, after, mode="update")

    @contextmanager
    def release_fails(*_args: object, **_kwargs: object):
        yield Path("unused-lock-counter")
        raise OSError(f"simulated {release_stage} failure")

    monkeypatch.setattr(workcase_update, "fact_write_lock", release_fails)

    result = apply_workcase_write(command)

    assert result.status == "updated"
    assert result.coordination_release_uncertain is True
    assert result.replacement_result is not None
    assert result.replacement_result.outcome == "replaced"
    assert result.replacement_result.namespace_state == "committed"
    assert result.readback is not None
    assert result.readback.check_status == "mechanically_valid"
    assert result.readback.raw_text == result.candidate_text
    assert path.read_text(encoding="utf-8") == result.candidate_text


def test_rejected_workcase_result_survives_coordination_release_failure(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    original = path.read_bytes()
    command = _command(project, before, {**before, "title": "Rejected candidate"}, mode="update")

    @contextmanager
    def release_fails(*_args: object, **_kwargs: object):
        yield Path("unused-lock-counter")
        raise OSError("simulated lock release failure")

    expected = workcase_update.WorkCaseWriteResult(
        "candidate_rejected",
        command.event_at,
        issues=(FactIssue("schema", "forced candidate rejection"),),
    )
    monkeypatch.setattr(workcase_update, "fact_write_lock", release_fails)
    monkeypatch.setattr(workcase_update, "apply_workcase_write_locked", lambda *_args: expected)

    result = apply_workcase_write(command)

    assert result.status == "candidate_rejected"
    assert result.issues == expected.issues
    assert result.coordination_release_uncertain is True
    assert path.read_bytes() == original


def test_known_uncommitted_replacement_has_zero_source_writes(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    original = path.read_bytes()
    after = {**before, "title": "不得写入的候选责任"}
    monkeypatch.setattr(
        workcase_update,
        "atomic_replace_text_if_unchanged",
        lambda *_args, **_kwargs: AtomicWriteResult.not_committed("unavailable"),
    )

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "replacement_unavailable"
    assert result.replacement_result is not None
    assert result.replacement_result.namespace_state == "not_committed"
    assert result.readback is None
    assert result.residual_readback is None
    assert path.read_bytes() == original


def test_invalid_after_review_identity_is_rejected_without_writing(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    after = {**before, "creation_reviews": [{**before["creation_reviews"][0], "reviewer": ["invalid"]}]}
    original = path.read_bytes()

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "creation_reviews[0].reviewer" for issue in result.issues)
    assert path.read_bytes() == original


def test_result_review_rejects_creation_only_quality_gate_coverage(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    fields = _closing("workcase-0001")
    fields["result_reviews"][0]["covered_quality_gate_ids"] = ["independent-result-review"]
    _write(project, fields)

    readback = _read(project, "workcase-0001")

    assert readback.check_status == "invalid"
    assert any(issue.field_path == "result_reviews[0].covered_quality_gate_ids" for issue in readback.issues)


def test_update_rejects_whitespace_only_text_without_writing(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    after = {**before, "goal": " \t\n "}
    original = path.read_bytes()

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "goal" and "空白" in issue.summary for issue in result.issues)
    assert path.read_bytes() == original


def test_full_after_omission_is_rejected_instead_of_merged_from_before(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    after = dict(before)
    after.pop("goal")
    original = path.read_bytes()

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "goal" for issue in result.issues)
    assert path.read_bytes() == original


def test_update_checks_proposal_targets_when_forming_proposal_and_entering_human_confirmation(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target = _snapshot(project, _active("workcase-0002", title="当前承接目标"))
    before = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        include_proposal=False,
    )
    _write(project, before)
    proposal_after = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        target=target,
    )

    formed = apply_workcase_write(_command(project, before, proposal_after, mode="update"))

    assert formed.status == "updated"
    assert formed.readback is not None and formed.readback.fields is not None
    preparing = formed.readback.fields
    confirming = {**preparing, "phase": "human_closure_confirming", "waiting_on": "等待 Human 判断完整提案。"}

    entered = apply_workcase_write(
        _command(
            project,
            preparing,
            confirming,
            mode="update",
            event_at="2026-07-26T14:00:00+08:00",
        )
    )

    assert entered.status == "updated"
    assert entered.readback is not None and entered.readback.fields is not None
    assert entered.readback.fields["phase"] == "human_closure_confirming"


def test_same_phase_proposal_replacement_guard_reads_the_new_after_target(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    old_target = _snapshot(project, _active("workcase-0002", title="原提案目标"))
    new_target_fields = _active("workcase-0003", title="新提案目标")
    new_target_path = _write(project, new_target_fields)
    new_target_read = _read(project, "workcase-0003")
    assert new_target_read.content_fingerprint is not None
    new_target = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0003"),
        new_target_read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )
    before = _preparing("workcase-0001", outcome="not-achieved", target=old_target)
    _write(project, before)
    after = _preparing("workcase-0001", outcome="not-achieved", target=new_target)
    command = _command(project, before, after, mode="update")
    new_target_path.write_text(
        serialize_fact_object(
            LAYOUTS["workcase"],
            {
                **new_target_fields,
                "title": "形成 after 后已经漂移的新目标",
                "updated_at": "2026-07-26T12:30:00+08:00",
            },
            None,
        ),
        encoding="utf-8",
    )

    issues, unavailable, snapshots = workcase_update._route_checks(command, before, after)

    assert unavailable is False
    assert [snapshot.target.object_id for snapshot in snapshots] == ["workcase-0003"]
    assert any(
        issue.field_path == "closure_proposal.residual_decisions[0].route_target"
        and "content_fingerprint 已变化" in issue.summary
        for issue in issues
    )


@pytest.mark.parametrize(
    ("case", "expected_status", "summary_fragment"),
    [
        ("missing", "candidate_rejected", "不存在"),
        ("invalid", "candidate_rejected", "不存在"),
        ("unavailable", "candidate_unavailable", "当前不可用"),
        ("stale", "candidate_rejected", "已变化"),
        ("cross_project", "candidate_rejected", "同一管辖项目"),
        ("cross_type", "candidate_rejected", "只能指向 WorkCase 或 Spark"),
        ("closed", "candidate_rejected", "open/blocked WorkCase"),
    ],
)
def test_update_proposal_target_failures_have_zero_source_writes(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    expected_status: str,
    summary_fragment: str | None,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    if case == "missing":
        target = WorkCaseRouteTargetSnapshot(
            FactReference("sample", "workcase", "workcase-0002"),
            "0" * 64,
            "closure_proposal.residual_decisions[0].route_target",
        )
    elif case == "invalid":
        target = _snapshot(
            project,
            {**_active("workcase-0002"), "unknown_field": "not registered"},
        )
    elif case == "cross_project":
        target = WorkCaseRouteTargetSnapshot(
            FactReference("another-project", "workcase", "workcase-0002"),
            "0" * 64,
            "closure_proposal.residual_decisions[0].route_target",
        )
    elif case == "cross_type":
        target = WorkCaseRouteTargetSnapshot(
            FactReference("sample", "adr", "adr-0002"),
            "0" * 64,
            "closure_proposal.residual_decisions[0].route_target",
        )
    elif case == "closed":
        closed = _closed_from(_closing("workcase-0002"))
        closed["updated_at"] = "2026-07-26T12:00:00+08:00"
        target = _snapshot(project, closed)
    else:
        target_fields = _active("workcase-0002", title="当前承接目标")
        target = _snapshot(project, target_fields)
        if case == "stale":
            changed_target = {
                **target_fields,
                "title": "已经漂移的承接目标",
                "updated_at": "2026-07-26T12:30:00+08:00",
            }
            target_path = project.boundary.worktree_root / LAYOUTS["workcase"].canonical_path("workcase-0002")
            target_path.write_text(
                serialize_fact_object(LAYOUTS["workcase"], changed_target, None),
                encoding="utf-8",
            )
        else:
            actual_read_fresh = ProjectFactIndex.read_fresh

            def unavailable_read_fresh(
                index: ProjectFactIndex,
                fact_type_key: str,
                object_id: str,
            ):
                read = actual_read_fresh(index, fact_type_key, object_id)
                if object_id != "workcase-0002" or read is None:
                    return read
                return replace(
                    read,
                    check_status="unavailable",
                    fields=None,
                    issues=(FactIssue("reference", "目标当前不可读"),),
                )

            monkeypatch.setattr(ProjectFactIndex, "read_fresh", unavailable_read_fresh)

    before = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        include_proposal=False,
    )
    source_path = _write(project, before)
    after = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        target=target,
    )
    original = source_path.read_bytes()

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == expected_status
    if summary_fragment is not None:
        assert any(
            summary_fragment in issue.summary
            and issue.field_path == "closure_proposal.residual_decisions[0].route_target"
            for issue in result.issues
        )
    assert source_path.read_bytes() == original


def test_update_proposal_target_must_be_project_relation_stable(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target_fields = _active("workcase-0002", title="关系不稳定的承接目标")
    target_fields["relations"] = [
        {
            "relation_key": "depends-on",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": "workcase-9999",
            },
        }
    ]
    target = _snapshot(project, target_fields)
    before = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        include_proposal=False,
    )
    source_path = _write(project, before)
    after = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        target=target,
    )
    original = source_path.read_bytes()

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "candidate_rejected"
    assert any("项目级关系未稳定" in issue.summary for issue in result.issues)
    assert source_path.read_bytes() == original


def test_update_proposal_without_routes_does_not_activate_target_guard(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _preparing("workcase-0001", include_proposal=False)
    _write(project, before)
    after = _preparing("workcase-0001")

    def unexpected_target_guard(*args, **kwargs):
        raise AssertionError("无 route proposal 不应读取 route target")

    monkeypatch.setattr(
        workcase_update,
        "validate_workcase_route_target_snapshots",
        unexpected_target_guard,
    )

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "updated"


def test_target_drift_after_proposal_formation_rejects_human_confirmation(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target_fields = _active("workcase-0002", title="提案形成时的承接目标")
    target = _snapshot(project, target_fields)
    before = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        include_proposal=False,
    )
    _write(project, before)
    proposal_after = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        target=target,
    )
    formed = apply_workcase_write(_command(project, before, proposal_after, mode="update"))
    assert formed.status == "updated"
    assert formed.readback is not None and formed.readback.fields is not None

    target_path = project.boundary.worktree_root / LAYOUTS["workcase"].canonical_path("workcase-0002")
    target_path.write_text(
        serialize_fact_object(
            LAYOUTS["workcase"],
            {
                **target_fields,
                "title": "提案形成后已经漂移的承接目标",
                "updated_at": "2026-07-26T13:30:00+08:00",
            },
            None,
        ),
        encoding="utf-8",
    )
    preparing = formed.readback.fields
    source_path = project.boundary.worktree_root / LAYOUTS["workcase"].canonical_path("workcase-0001")
    original = source_path.read_bytes()
    confirming = {**preparing, "phase": "human_closure_confirming", "waiting_on": "等待 Human 判断完整提案。"}

    result = apply_workcase_write(
        _command(
            project,
            preparing,
            confirming,
            mode="update",
            event_at="2026-07-26T14:00:00+08:00",
        )
    )

    assert result.status == "candidate_rejected"
    assert any("content_fingerprint 已变化" in issue.summary for issue in result.issues)
    assert any(issue.field_path == "closure_proposal.residual_decisions[0].route_target" for issue in result.issues)
    assert source_path.read_bytes() == original


def test_post_write_update_target_drift_conditionally_rolls_back_source(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target_fields = _active("workcase-0002", title="提案承接目标")
    target_path = _write(project, target_fields)
    target_read = _read(project, "workcase-0002")
    assert target_read.content_fingerprint is not None
    target = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )
    before = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        include_proposal=False,
    )
    source_path = _write(project, before)
    after = _preparing(
        "workcase-0001",
        outcome="not-achieved",
        target=target,
    )
    original_source = source_path.read_bytes()
    actual_guard = workcase_update.validate_workcase_route_target_snapshots
    calls = 0

    def drifting_guard(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            target_path.write_text(
                serialize_fact_object(
                    LAYOUTS["workcase"],
                    {
                        **target_fields,
                        "title": "source 写后漂移的承接目标",
                        "updated_at": "2026-07-26T13:30:00+08:00",
                    },
                    None,
                ),
                encoding="utf-8",
            )
        return actual_guard(*args, **kwargs)

    monkeypatch.setattr(workcase_update, "validate_workcase_route_target_snapshots", drifting_guard)

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert calls == 2
    assert result.status == "readback_failed"
    assert result.rollback_result is not None
    assert result.rollback_result.outcome == "replaced"
    assert source_path.read_bytes() == original_source


def test_stale_source_fingerprint_has_zero_writes(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    after = {**before, "title": "不会覆盖当前对象的标题"}
    command = replace(
        _command(project, before, after, mode="update"),
        expected_content_fingerprint="0" * 64,
    )
    original = path.read_bytes()

    result = apply_workcase_write(command)

    assert result.status == "fingerprint_stale"
    assert path.read_bytes() == original


def _gate1_after(before: dict[str, Any], *, source_refs: list[str] | None = None) -> dict[str, Any]:
    after = deepcopy(before)
    after["phase"] = "executing"
    after.pop("waiting_on")
    after["execution_approval"] = {
        "subject_version": before["plan_version"],
        "approved_at": "2026-07-26T10:45:00+08:00",
        "summary": "Human approved the bounded Gate1 baseline.",
        "baseline_fingerprint": approval_baseline_fingerprint(before),
        "source_refs": source_refs or ["human-decision"],
    }
    return after


def test_gate1_approval_requires_matching_request_authorization_and_readback(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    _write(project, before)
    after = _gate1_after(before)

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="update",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    expected_approval = deepcopy(after["execution_approval"])
    expected_approval["approved_at"] = canonical_utc_timestamp(expected_approval["approved_at"])
    assert result.readback.fields["execution_approval"] == expected_approval


def test_gate1_freezes_quality_gate_declaration_even_if_baseline_is_recomputed(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    _write(project, before)
    approved = _gate1_after(before)
    first = apply_workcase_write(
        _command(project, before, approved, mode="update", authorization_reference=_human_reference())
    )
    assert first.status == "updated" and first.readback is not None and first.readback.fields is not None

    candidate = deepcopy(first.readback.fields)
    candidate["execution_authorization"]["quality_gates"][0]["reviewer_mode"] = "unknown"
    candidate["execution_approval"]["baseline_fingerprint"] = approval_baseline_fingerprint(candidate)
    original = _write(project, first.readback.fields).read_bytes()

    rejected = apply_workcase_write(
        _command(project, first.readback.fields, candidate, mode="update", event_at="2026-07-26T14:00:00+08:00")
    )

    assert rejected.status == "candidate_rejected"
    assert any(issue.field_path == "execution_authorization" for issue in rejected.issues)
    assert _write(project, first.readback.fields).read_bytes() == original


@pytest.mark.parametrize(
    ("authorization_reference", "source_refs", "expected_path"),
    [
        ((), ["human-decision"], "authorization_reference"),
        (_human_reference(), ["another-decision"], "execution_approval.source_refs"),
    ],
)
def test_gate1_approval_missing_or_mismatched_proof_has_zero_writes(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    authorization_reference: tuple[dict[str, Any], ...],
    source_refs: list[str],
    expected_path: str,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    original = path.read_bytes()
    after = _gate1_after(before, source_refs=source_refs)

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="update",
            authorization_reference=authorization_reference,
        )
    )

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == expected_path for issue in result.issues)
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    ("mutate", "expected_path"),
    [
        (
            lambda fields: fields["execution_authorization"].pop("quality_gates"),
            "execution_authorization.quality_gates",
        ),
        (
            lambda fields: fields["execution_authorization"]["quality_gates"][0].update(
                {"delegation_action_id": "authorization-missing"}
            ),
            "execution_authorization.quality_gates[0].delegation_action_id",
        ),
        (
            lambda fields: fields["execution_authorization"]["quality_gates"][0].update(
                {"result_review_action_id": "authorization-delegate-independent-review"}
            ),
            "execution_authorization.quality_gates[0]",
        ),
        (
            lambda fields: fields["creation_reviews"][0].update({"covered_quality_gate_ids": []}),
            "creation_reviews[0].covered_quality_gate_ids",
        ),
    ],
)
def test_gate1_rejects_incomplete_or_reused_quality_gate_authorization_with_zero_writes(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    mutate: object,
    expected_path: str,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    original = path.read_bytes()
    mutate(before)  # type: ignore[operator]
    after = _gate1_after(before)

    result = apply_workcase_write(
        _command(project, before, after, mode="update", authorization_reference=_human_reference())
    )

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == expected_path for issue in result.issues)
    assert path.read_bytes() == original


def test_terminal_legacy_workcase_cannot_bypass_quality_gate_by_entering_result_chain(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    before["execution_authorization"].pop("quality_gates")
    before["creation_reviews"][0].pop("covered_quality_gate_ids")
    before["work_items"][0].update(
        {"status": "completed", "result_summary": "Legacy implementation result already exists."}
    )
    path = _write(project, before)
    original = path.read_bytes()
    after = deepcopy(before)
    after.update(
        {
            "phase": "controller_checking",
            "result_version": 1,
            "success_criterion_results": [
                {"criterion_id": "criterion-main", "outcome": "satisfied", "summary": "Legacy result is recorded."}
            ],
            "result_summary": "Legacy terminal result is ready for controller checking.",
            "controller_check_summary": "Controller recorded the legacy terminal result.",
            "validation_summary": "No new implementation is performed by this transition.",
        }
    )
    after.pop("waiting_on")
    after["execution_approval"] = {
        "subject_version": 1,
        "approved_at": "2026-07-26T10:45:00+08:00",
        "summary": "Attempted Gate1 approval for a legacy terminal result.",
        "baseline_fingerprint": approval_baseline_fingerprint(before),
        "source_refs": ["human-decision"],
    }

    result = apply_workcase_write(
        _command(project, before, after, mode="update", authorization_reference=_human_reference())
    )

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "execution_authorization.quality_gates" for issue in result.issues)
    assert path.read_bytes() == original


def test_gate1_baseline_fingerprint_mismatch_has_zero_writes(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _active("workcase-0001")
    path = _write(project, before)
    original = path.read_bytes()
    after = _gate1_after(before)
    after["execution_approval"]["baseline_fingerprint"] = "0" * 64

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="update",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "execution_approval.baseline_fingerprint" for issue in result.issues)
    assert path.read_bytes() == original


def test_approved_plan_delta_keeps_gate1_baseline_and_can_resume_execution(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    gate1 = _gate1_after(_active("workcase-0001"))
    _write(project, gate1)
    revising = deepcopy(gate1)
    revising.update(
        {
            "phase": "plan_revising",
            "plan_version": 2,
            "work_items": [
                {
                    **gate1["work_items"][0],
                    "goal": "Complete the same bounded responsibility with an adjusted method.",
                }
            ],
            "creation_reviews": [_creation_review(2)],
        }
    )

    revised = apply_workcase_write(_command(project, gate1, revising, mode="update"))
    assert revised.status == "updated"
    assert revising["execution_approval"]["subject_version"] == 1

    executing = {**deepcopy(revising), "phase": "executing"}
    resumed = apply_workcase_write(
        _command(
            project,
            revising,
            executing,
            mode="update",
            event_at="2026-07-26T14:00:00+08:00",
        )
    )
    assert resumed.status == "updated"


def test_pre_gate_plan_revision_roundtrip_does_not_require_or_fabricate_approval(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    confirming = _active("workcase-0001")
    _write(project, confirming)
    revising = deepcopy(confirming)
    revising["phase"] = "plan_revising"
    revising.pop("waiting_on")

    entered = apply_workcase_write(_command(project, confirming, revising, mode="update"))
    assert entered.status == "updated"
    assert "execution_approval" not in revising

    candidate = deepcopy(revising)
    candidate.update(
        {
            "phase": "human_plan_confirming",
            "plan_version": 2,
            "creation_reviews": [
                {
                    **_creation_review(2),
                    "reviewed_at": "2026-07-26T13:30:00+08:00",
                }
            ],
            "waiting_on": "等待 Human 对修订后的完整计划与授权基线作 Gate1 决定。",
        }
    )
    candidate["work_items"][0]["goal"] = "完成修订后的有界责任。"
    candidate["execution_authorization"]["authorized_actions"][0]["summary"] = "写入修订后的有界结果。"

    returned = apply_workcase_write(
        _command(project, revising, candidate, mode="update", event_at="2026-07-26T14:00:00+08:00")
    )
    assert returned.status == "updated"
    assert returned.readback is not None and returned.readback.fields is not None
    assert "execution_approval" not in returned.readback.fields


def test_gate2_rejects_every_update_and_requires_close_operation(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0001")
    path = _write(project, before)
    original = path.read_bytes()
    after = deepcopy(before)
    after["title"] = "Gate2 cannot be updated"

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "phase" and "close-workcase" in issue.summary for issue in result.issues)
    assert path.read_bytes() == original


@pytest.mark.parametrize("mode", ["update", "close", "correct"])
def test_all_workcase_modes_reject_an_invalid_current_object_without_repair(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    mode: workcase_update.WorkCaseWriteMode,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    invalid = {**_active("workcase-0001"), "unknown_field": "not-registered"}
    path = _write(project, invalid)
    current = _read(project, "workcase-0001")
    assert current.check_status == "invalid" and current.content_fingerprint is not None
    original = path.read_bytes()
    command = WorkCaseWriteCommand(
        boundary=project.boundary,
        schemas=project.schemas,
        schema=project.schemas["workcase"],
        object_id="workcase-0001",
        expected_content_fingerprint=current.content_fingerprint,
        supplied=_supplied(_active("workcase-0001")),
        event_at="2026-07-26T13:00:00+08:00",
        mode=mode,
    )

    result = apply_workcase_write(command)

    assert result.status == "current_rejected"
    assert path.read_bytes() == original


def test_close_workcase_projects_the_current_proposal_and_removes_active_state(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0001")
    _write(project, before)
    after = _closed_from(before)

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["status"] == "closed"
    assert "phase" not in result.readback.fields
    assert "closure_proposal" not in result.readback.fields
    assert "execution_approval" not in result.readback.fields
    assert result.readback.fields["change_log"][:-1] == before["change_log"]
    assert result.readback.fields["change_log"][-1]["at"] == result.readback.fields["updated_at"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda after: after.pop("change_log"),
        lambda after: after.__setitem__("change_log", []),
        lambda after: after["change_log"].extend(
            [
                {
                    "signature": {"agent_id": "test-agent", "host_environment": "test"},
                    "session_id": "test-session",
                    "at": "2000-01-01T00:00:00Z",
                    "summary": "伪造的额外关闭流水。",
                },
                {
                    "signature": {"agent_id": "test-agent", "host_environment": "test"},
                    "session_id": "test-session",
                    "at": "2000-01-01T00:01:00Z",
                    "summary": "伪造的第二条额外关闭流水。",
                },
            ]
        ),
    ],
)
def test_close_rejects_missing_or_extra_change_log_entries_without_writing(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0001")
    path = _write(project, before)
    after = _closed_from(before)
    mutation(after)
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "change_log" for issue in result.issues)
    assert path.read_bytes() == original


def test_correct_closed_workcase_appends_one_change_log_entry(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closed_from(_closing("workcase-0001"))
    before["updated_at"] = "2026-07-26T12:00:00+08:00"
    _write(project, before)
    after = {**before, "title": "更正后的关闭标题"}

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="correct",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["change_log"][:-1] == before["change_log"]
    assert result.readback.fields["change_log"][-1]["at"] == result.readback.fields["updated_at"]


def test_correct_closed_legacy_without_change_log_cannot_invent_history(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closed_from(_closing("workcase-0001"))
    before.pop("change_log")
    before["updated_at"] = "2026-07-26T12:00:00+08:00"
    path = _write(project, before)
    assert _read(project, before["object_id"]).check_status == "mechanically_valid"
    after = {**before, "title": "不应补造历史的更正标题"}
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="correct",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "change_log" for issue in result.issues)
    assert path.read_bytes() == original


def test_close_rejects_any_change_to_a_retained_terminal_fact(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0001")
    path = _write(project, before)
    after = {**_closed_from(before), "result_summary": "关闭时夹带改写的结果。"}
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "result_summary" for issue in result.issues)
    assert path.read_bytes() == original


def test_close_mapping_compares_terminal_residuals_by_stable_id_not_array_order() -> None:
    before = _closing("workcase-0001", outcome="partial")
    before["success_criterion_definitions"] = [
        {"criterion_id": "criterion-one", "statement": "形成第一项结果。"},
        {"criterion_id": "criterion-two", "statement": "形成第二项结果。"},
    ]
    before["success_criterion_results"] = [
        {"criterion_id": "criterion-one", "outcome": "satisfied", "summary": "第一项完成。"},
        {
            "criterion_id": "criterion-two",
            "outcome": "not_satisfied",
            "summary": "第二项未完成。",
        },
    ]
    before["closure_proposal"]["residual_decisions"] = [
        {
            "residual_id": "residual-one",
            "summary": "第一项停止责任。",
            "proposed_disposition": "accept_stop",
        },
        {
            "residual_id": "residual-two",
            "summary": "第二项停止责任。",
            "proposed_disposition": "accept_stop",
        },
    ]
    after = _closed_from(before)
    after["residual_responsibilities"].reverse()

    assert workcase_update._close_mapping_issues(before, after) == ()

    after["residual_responsibilities"][0]["summary"] = "被改写的责任。"
    assert any(
        issue.field_path == "residual_responsibilities"
        for issue in workcase_update._close_mapping_issues(before, after)
    )


def test_close_mapping_preserves_spark_suggestions_without_creating_a_relation() -> None:
    before = _closing("workcase-0001", outcome="not-achieved")
    before["closure_proposal"]["spark_suggestions"] = [
        {
            "suggestion_id": "suggestion-resume",
            "suggestion_kind": "constrained_responsibility",
            "summary": "外部条件恢复后继续验证。",
            "restriction_reason": "当前缺少受控环境。",
            "impact_summary": "无法验证当前成功标准。",
            "resume_condition": "取得受控环境。",
            "follow_up_summary": "由 Human 判断是否创建 Spark。",
        }
    ]
    before["closure_proposal"]["residual_decisions"] = [
        {
            "residual_id": "residual-main",
            "summary": "恢复环境后完成验证。",
            "proposed_disposition": "suggest_spark",
            "spark_suggestion_id": "suggestion-resume",
        }
    ]
    after = _closed_from(before)

    assert workcase_update._close_mapping_issues(before, after) == ()
    assert after["spark_suggestions"] == before["closure_proposal"]["spark_suggestions"]
    assert "relations" not in after

    after["spark_suggestions"][0]["summary"] = "关闭时被改写。"
    assert any(
        issue.field_path == "spark_suggestions" for issue in workcase_update._close_mapping_issues(before, after)
    )


def test_close_rejects_an_incoming_depends_on_before_writing(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0001")
    _write(project, before)
    dependent = _active("workcase-0002")
    dependent["relations"] = [
        {
            "relation_key": "depends-on",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": "workcase-0001",
            },
        }
    ]
    _write(project, dependent)
    path = project.boundary.worktree_root / LAYOUTS["workcase"].canonical_path("workcase-0001")
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            before,
            _closed_from(before),
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "candidate_rejected"
    assert any("入向 depends-on" in issue.summary for issue in result.issues)
    assert path.read_bytes() == original


def test_close_is_unavailable_when_a_canonical_peer_is_invalid(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0001")
    path = _write(project, before)
    invalid_peer = {**_active("workcase-0002"), "unknown_field": "not-registered"}
    _write(project, invalid_peer)
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            before,
            _closed_from(before),
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "candidate_unavailable"
    assert any(
        issue.category == "reference" and issue.field_path == "relations" and "入向 depends-on" in issue.summary
        for issue in result.issues
    )
    assert path.read_bytes() == original


def test_close_is_unavailable_when_a_locally_valid_peer_is_project_invalid(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0001")
    path = _write(project, before)
    peer = _active("workcase-0002")
    peer["relations"] = [
        {
            "relation_key": "depends-on",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": "workcase-9999",
            },
        }
    ]
    _write(project, peer)
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            before,
            _closed_from(before),
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "candidate_unavailable"
    assert any(
        issue.category == "reference" and issue.field_path == "relations" and "入向 depends-on" in issue.summary
        for issue in result.issues
    )
    assert path.read_bytes() == original
    assert _read(project, "workcase-0001").fields["status"] == "open"


def test_close_rechecks_incoming_dependencies_after_source_write_and_rolls_back(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closing("workcase-0001")
    path = _write(project, before)
    original = path.read_bytes()
    actual_guard = workcase_update.validate_workcase_incoming_dependencies
    calls = 0

    def changing_guard(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            return (
                (FactIssue("relation", "写后出现新的入向 depends-on", "relations"),),
                False,
            )
        return actual_guard(*args, **kwargs)

    monkeypatch.setattr(workcase_update, "validate_workcase_incoming_dependencies", changing_guard)

    result = apply_workcase_write(
        _command(
            project,
            before,
            _closed_from(before),
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert calls == 2
    assert result.status == "readback_failed"
    assert result.rollback_result is not None
    assert result.rollback_result.outcome == "replaced"
    assert path.read_bytes() == original


def test_close_rejects_a_stale_route_target_before_source_write(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target = _active("workcase-0002", title="初始承接目标")
    target_path = _write(project, target)
    target_read = _read(project, "workcase-0002")
    assert target_read.content_fingerprint is not None
    snapshot = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )
    before = _closing("workcase-0001", outcome="not-achieved", target=snapshot)
    source_path = _write(project, before)
    changed_target = {
        **target,
        "title": "已发生变化的承接目标",
        "updated_at": "2026-07-26T12:30:00+08:00",
    }
    target_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], changed_target, None),
        encoding="utf-8",
    )
    original_source = source_path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            before,
            _closed_from(before),
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "candidate_rejected"
    assert any("content_fingerprint 已变化" in issue.summary for issue in result.issues)
    assert any(issue.field_path == "closure_proposal.residual_decisions[0].route_target" for issue in result.issues)
    assert source_path.read_bytes() == original_source


def test_post_write_route_target_drift_conditionally_rolls_back_source(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target_fields = _active("workcase-0002", title="承接目标")
    target_path = _write(project, target_fields)
    original_target = target_path.read_bytes()
    target_read = _read(project, "workcase-0002")
    assert target_read.content_fingerprint is not None
    snapshot = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )
    before = _closing("workcase-0001", outcome="not-achieved", target=snapshot)
    source_path = _write(project, before)
    original_source = source_path.read_bytes()
    actual_guard = workcase_update.validate_workcase_route_target_snapshots
    calls = 0

    def drifting_guard(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            changed = {
                **target_fields,
                "title": "锁外发生变化的承接目标",
                "updated_at": "2026-07-26T12:30:00+08:00",
            }
            target_path.write_text(
                serialize_fact_object(LAYOUTS["workcase"], changed, None),
                encoding="utf-8",
            )
        return actual_guard(*args, **kwargs)

    monkeypatch.setattr(workcase_update, "validate_workcase_route_target_snapshots", drifting_guard)

    result = apply_workcase_write(
        _command(
            project,
            before,
            _closed_from(before),
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "readback_failed"
    assert result.rollback_result is not None
    assert result.rollback_result.outcome == "replaced"
    assert source_path.read_bytes() == original_source
    assert target_path.read_bytes() != original_target


def test_conditional_rollback_does_not_overwrite_a_newer_external_source_write(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target_fields = _active("workcase-0002", title="承接目标")
    target_path = _write(project, target_fields)
    target_read = _read(project, "workcase-0002")
    assert target_read.content_fingerprint is not None
    snapshot = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )
    before = _closing("workcase-0001", outcome="not-achieved", target=snapshot)
    source_path = _write(project, before)
    actual_guard = workcase_update.validate_workcase_route_target_snapshots
    actual_lock = workcase_update.fact_write_lock
    calls = 0

    @contextmanager
    def release_fails(boundary: CreationBoundary, layout):
        with actual_lock(boundary, layout) as counter_path:
            yield counter_path
        raise OSError("simulated lock release failure")

    def conflicting_guard(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            changed_target = {
                **target_fields,
                "title": "锁外变化的目标",
                "updated_at": "2026-07-26T12:30:00+08:00",
            }
            target_path.write_text(
                serialize_fact_object(LAYOUTS["workcase"], changed_target, None),
                encoding="utf-8",
            )
            observed_source = _read(project, "workcase-0001")
            assert observed_source.fields is not None
            external_source = {
                **observed_source.fields,
                "title": "锁外更新后的 source",
                "updated_at": "2026-07-26T13:30:00+08:00",
            }
            source_path.write_text(
                serialize_fact_object(LAYOUTS["workcase"], external_source, None),
                encoding="utf-8",
            )
        return actual_guard(*args, **kwargs)

    monkeypatch.setattr(workcase_update, "validate_workcase_route_target_snapshots", conflicting_guard)
    monkeypatch.setattr(workcase_update, "fact_write_lock", release_fails)

    result = apply_workcase_write(
        _command(
            project,
            before,
            _closed_from(before),
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "readback_failed"
    assert result.coordination_release_uncertain is True
    assert result.rollback_result is not None
    assert result.rollback_result.outcome == "conflict"
    assert result.residual_readback is not None
    assert result.residual_readback.check_status == "mechanically_valid"
    assert result.residual_readback.fields is not None
    assert result.residual_readback.fields["title"] == "锁外更新后的 source"
    assert result.residual_readback.raw_text != result.candidate_text
    assert result.current is not None
    assert result.residual_readback.raw_text != result.current.raw_text
    assert "锁外更新后的 source" in source_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("authorization_reference", "independent_review_reference", "expected_status"),
    [
        ((), None, "updated"),
        (_human_reference(), _review_reference(), "updated"),
        (_human_reference(), None, "candidate_rejected"),
        ((), _review_reference(), "candidate_rejected"),
    ],
)
def test_urls_only_correction_supports_explicit_nonimpact_or_conservative_gate(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    authorization_reference: tuple[dict[str, Any], ...],
    independent_review_reference: dict[str, Any] | None,
    expected_status: str,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    closing = _closing("workcase-0001")
    before = _closed_from(closing)
    before["updated_at"] = "2026-07-26T12:00:00+08:00"
    _write(project, before)
    after = {**before, "urls": _url()}

    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="correct",
            authorization_reference=authorization_reference,
            independent_review_reference=independent_review_reference,
        )
    )

    assert result.status == expected_status


def test_title_and_urls_together_require_both_substantive_correction_inputs(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _closed_from(_closing("workcase-0001"))
    before["updated_at"] = "2026-07-26T12:00:00+08:00"
    path = _write(project, before)
    after = {**before, "title": "同时修正标题和网址", "urls": _url()}
    original = path.read_bytes()

    rejected = apply_workcase_write(_command(project, before, after, mode="correct"))

    assert rejected.status == "candidate_rejected"
    assert path.read_bytes() == original

    accepted = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="correct",
            authorization_reference=_human_reference(),
            independent_review_reference=_review_reference(),
        )
    )
    assert accepted.status == "updated"


def test_correct_closed_requires_exact_after_route_target_fingerprint_set(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target = _active("workcase-0002", title="承接目标")
    _write(project, target)
    target_read = _read(project, "workcase-0002")
    assert target_read.content_fingerprint is not None
    snapshot = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )
    source = _closed_from(_closing("workcase-0001", outcome="not-achieved", target=snapshot))
    source["updated_at"] = "2026-07-26T12:00:00+08:00"
    path = _write(project, source)
    original = path.read_bytes()
    after = {**source, "title": "只修正标题"}

    result = apply_workcase_write(_command(project, source, after, mode="correct"))

    assert result.status == "candidate_rejected"
    assert any("精确一致" in issue.summary for issue in result.issues)
    assert path.read_bytes() == original


def test_identical_closed_after_revalidates_request_target_before_no_change(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target = _active("workcase-0002", title="承接目标")
    target_path = _write(project, target)
    target_read = _read(project, "workcase-0002")
    assert target_read.content_fingerprint is not None
    current_snapshot = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )
    source = _closed_from(_closing("workcase-0001", outcome="not-achieved", target=current_snapshot))
    source["updated_at"] = "2026-07-26T12:00:00+08:00"
    path = _write(project, source)
    original = path.read_bytes()
    inode = path.stat().st_ino
    request_snapshot = replace(
        current_snapshot,
        origin_path="route_target_fingerprints[0].target",
    )
    target_path.write_text(
        serialize_fact_object(
            LAYOUTS["workcase"],
            {
                **target,
                "title": "相同 after 提交前已经漂移的目标",
                "updated_at": "2026-07-26T12:30:00+08:00",
            },
            None,
        ),
        encoding="utf-8",
    )
    command = _command(
        project,
        source,
        source,
        mode="correct",
        route_target_fingerprints=(request_snapshot,),
    )
    command = replace(command, event_at="2026-07-26T08:00:00+08:00")

    result = apply_workcase_write(command)

    assert result.status == "candidate_rejected"
    assert any(
        issue.field_path == "route_target_fingerprints[0].target" and "content_fingerprint 已变化" in issue.summary
        for issue in result.issues
    )
    assert path.read_bytes() == original
    assert path.stat().st_ino == inode


def test_identical_closed_after_returns_no_change_only_after_current_target_check(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target = _active("workcase-0002", title="承接目标")
    _write(project, target)
    target_read = _read(project, "workcase-0002")
    assert target_read.content_fingerprint is not None
    proposal_snapshot = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )
    request_snapshot = replace(
        proposal_snapshot,
        origin_path="route_target_fingerprints[0].target",
    )
    source = _closed_from(_closing("workcase-0001", outcome="not-achieved", target=proposal_snapshot))
    source["updated_at"] = "2026-07-26T12:00:00+08:00"
    path = _write(project, source)
    original = path.read_bytes()
    actual_lock = workcase_update.fact_write_lock

    @contextmanager
    def release_fails(boundary: CreationBoundary, layout):
        with actual_lock(boundary, layout) as counter_path:
            yield counter_path
        raise OSError("simulated lock release failure")

    monkeypatch.setattr(workcase_update, "fact_write_lock", release_fails)

    result = apply_workcase_write(
        _command(
            project,
            source,
            source,
            mode="correct",
            route_target_fingerprints=(request_snapshot,),
        )
    )

    assert result.status == "no_change"
    assert result.coordination_release_uncertain is True
    assert result.current is result.readback
    assert path.read_bytes() == original


def test_identical_closed_after_rejects_independent_review_reference(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    source = _closed_from(_closing("workcase-0001"))
    source["updated_at"] = "2026-07-26T12:00:00+08:00"
    path = _write(project, source)
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            source,
            source,
            mode="correct",
            independent_review_reference=_review_reference(),
        )
    )

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "independent_review_reference" for issue in result.issues)
    assert path.read_bytes() == original


def test_correct_closed_allows_an_unchanged_existing_route_target_that_is_now_closed(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target = _closed_from(_closing("workcase-0002"))
    target["updated_at"] = "2026-07-26T12:00:00+08:00"
    _write(project, target)
    target_read = _read(project, "workcase-0002")
    assert target_read.check_status == "mechanically_valid"
    assert target_read.content_fingerprint is not None
    snapshot = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "route_target_fingerprints[0].target",
    )
    source = _closed_from(_closing("workcase-0001", outcome="not-achieved", target=snapshot))
    source["updated_at"] = "2026-07-26T12:00:00+08:00"
    _write(project, source)
    after = {**source, "title": "更正后的关闭标题"}

    result = apply_workcase_write(
        _command(
            project,
            source,
            after,
            mode="correct",
            route_target_fingerprints=(snapshot,),
        )
    )

    assert result.status == "updated"


def test_correct_closed_rejects_a_new_route_target_that_is_already_closed(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target = _closed_from(_closing("workcase-0002"))
    target["updated_at"] = "2026-07-26T12:00:00+08:00"
    _write(project, target)
    target_read = _read(project, "workcase-0002")
    assert target_read.check_status == "mechanically_valid"
    assert target_read.content_fingerprint is not None
    snapshot = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "route_target_fingerprints[0].target",
    )
    closing = _closing("workcase-0001", outcome="not-achieved")
    closing["closure_proposal"]["residual_decisions"] = [
        {
            "residual_id": "residual-main",
            "summary": "Human 原先接受停止的责任。",
            "proposed_disposition": "accept_stop",
        }
    ]
    source = _closed_from(closing)
    source["updated_at"] = "2026-07-26T12:00:00+08:00"
    path = _write(project, source)
    after = dict(source)
    after.pop("residual_responsibilities")
    after["relations"] = [{"relation_key": "routed-to", "target": snapshot.target.to_json()}]
    after["disposition_summary"] = "原关闭时遗漏记录的责任转交。"
    original = path.read_bytes()

    result = apply_workcase_write(
        _command(
            project,
            source,
            after,
            mode="correct",
            authorization_reference=_human_reference(),
            route_target_fingerprints=(snapshot,),
            independent_review_reference=_review_reference(),
        )
    )

    assert result.status == "candidate_rejected"
    assert any("新形成" in issue.summary for issue in result.issues)
    assert path.read_bytes() == original


def _contributed(fact_type_key: str, object_id: str) -> dict[str, Any]:
    return {
        "relation_key": "contributed-to",
        "target": {
            "governed_project_id": "sample",
            "fact_type_key": fact_type_key,
            "object_id": object_id,
        },
    }


def _write_adr(project: _Project, object_id: str) -> Path:
    fields = {
        "object_id": object_id,
        "fact_type_key": "adr",
        "title": "当前有界决定",
        "created_at": "2026-07-26T09:00:00+08:00",
        "updated_at": "2026-07-26T09:30:00+08:00",
        "status": "active",
        "decision_question": "当前有界问题。",
        "decision": "当前实际决定。",
        "applicability": "只适用于当前项目边界。",
        "rationale": "当前决定的实际理由。",
        "consequences": "当前决定的实际后果。",
    }
    path = project.boundary.worktree_root / LAYOUTS["adr"].canonical_path(object_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_fact_object(LAYOUTS["adr"], fields, None), encoding="utf-8")
    return path


def _write_pitfall(project: _Project, object_id: str, *, status: str = "draft") -> Path:
    fields = {
        "object_id": object_id,
        "fact_type_key": "pitfall",
        "title": "当前完整现场经验",
        "created_at": "2026-07-26T09:00:00+08:00",
        "updated_at": "2026-07-26T09:30:00+08:00",
        "status": status,
        "symptoms": "可稳定识别的实际症状。",
        "trigger_conditions": "能够复现问题的完整触发条件。",
        "root_cause": "已经验证的根因。",
        "resolution": "已经完成并验证的解决方式。",
        "avoidance": "以后避免同类问题的具体方法。",
        "applicability": "只适用于当前项目边界。",
        "validation_summary": "已按实际现场完成验证。",
    }
    if status == "discarded":
        fields["disposition_summary"] = "Human 已作出当前生命周期处置。"
    path = project.boundary.worktree_root / LAYOUTS["pitfall"].canonical_path(object_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_fact_object(LAYOUTS["pitfall"], fields, None), encoding="utf-8")
    return path


def test_close_preserves_contributed_to_and_rejects_any_add_remove_or_change(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    _write_pitfall(project, "pitfall-0001")
    _write_pitfall(project, "pitfall-0002")
    before = _closing("workcase-0001")
    before["relations"] = [_contributed("pitfall", "pitfall-0001")]
    path = _write(project, before)
    original = path.read_bytes()

    for mutated in (
        [],
        [_contributed("pitfall", "pitfall-0002")],
        [_contributed("pitfall", "pitfall-0001"), _contributed("pitfall", "pitfall-0002")],
    ):
        rejected_after = _closed_from(before)
        rejected_after["relations"] = mutated
        rejected = apply_workcase_write(
            _command(
                project,
                before,
                rejected_after,
                mode="close",
                authorization_reference=_human_reference(),
            )
        )
        assert rejected.status == "candidate_rejected"
        assert any(issue.field_path == "relations" for issue in rejected.issues)
        assert path.read_bytes() == original

    after = _closed_from(before)
    after["relations"] = deepcopy(before["relations"])
    result = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="close",
            authorization_reference=_human_reference(),
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["relations"] == before["relations"]


def test_close_mapping_requires_contributed_to_before_after_exact_equality() -> None:
    before = _closing("workcase-0001")
    before["relations"] = [_contributed("pitfall", "pitfall-0001")]
    after = _closed_from(before)
    after["relations"] = deepcopy(before["relations"])

    assert workcase_update._close_mapping_issues(before, after) == ()

    for mutated in (
        [],
        [_contributed("pitfall", "pitfall-0002")],
        [_contributed("pitfall", "pitfall-0001"), _contributed("pitfall", "pitfall-0002")],
    ):
        changed = _closed_from(before)
        changed["relations"] = mutated
        assert any(
            issue.field_path == "relations" and "contributed-to" in issue.summary
            for issue in workcase_update._close_mapping_issues(before, changed)
        )


def test_correct_closed_contributed_to_change_is_substantive_and_ignores_route_fingerprint_set(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    _write_pitfall(project, "pitfall-0001")
    before = _closed_from(_closing("workcase-0001"))
    before["updated_at"] = "2026-07-26T12:00:00+08:00"
    path = _write(project, before)
    original = path.read_bytes()
    after = {**before, "relations": [_contributed("pitfall", "pitfall-0001")]}

    rejected = apply_workcase_write(_command(project, before, after, mode="correct"))

    assert rejected.status == "candidate_rejected"
    assert {issue.field_path for issue in rejected.issues} == {
        "independent_review_reference",
        "authorization_reference",
    }
    assert path.read_bytes() == original

    accepted = apply_workcase_write(
        _command(
            project,
            before,
            after,
            mode="correct",
            authorization_reference=_human_reference(),
            independent_review_reference=_review_reference(),
        )
    )

    assert accepted.status == "updated"
    assert not any("精确一致" in issue.summary for issue in accepted.issues)
    readback = _read(project, "workcase-0001")
    assert readback.fields is not None
    assert readback.fields["relations"] == after["relations"]


def test_update_workcase_forms_contributed_to_in_an_active_phase(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    _write_pitfall(project, "pitfall-0001")
    before = _preparing("workcase-0001")
    _write(project, before)
    after = {**before, "relations": [_contributed("pitfall", "pitfall-0001")]}

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["relations"] == after["relations"]


def test_update_workcase_blocked_freeze_rejects_contributed_to_change(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    _write_pitfall(project, "pitfall-0001")
    before = {
        **_active("workcase-0001"),
        "status": "blocked",
        "blocking_summary": "外部输入到达前当前责任无法推进。",
    }
    path = _write(project, before)
    original = path.read_bytes()
    after = {**before, "relations": [_contributed("pitfall", "pitfall-0001")]}

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "relations" for issue in result.issues)
    assert path.read_bytes() == original


def test_update_workcase_can_enter_blocked_with_its_required_change_log_append(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    before = _gate1_after(_active("workcase-0001"))
    _write(project, before)
    after = deepcopy(before)
    after.update(
        {
            "status": "blocked",
            "blocking_summary": "可信签发根尚未可用，当前责任无法继续。",
        }
    )
    after["work_items"][0].update(
        {
            "status": "blocked",
            "current_summary": "已确认当前缺少可信签发根。",
            "blocking_summary": "需要 Human 决定可信签发与验证通道。",
        }
    )

    result = apply_workcase_write(_command(project, before, after, mode="update"))

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["status"] == "blocked"
    assert result.readback.fields["change_log"][:-1] == before["change_log"]
    assert result.readback.fields["change_log"][-1]["at"] == result.readback.fields["updated_at"]


def test_update_workcase_human_closure_confirming_allows_legal_relation_but_rejects_every_update(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    _write_pitfall(project, "pitfall-0001")
    before = _closing("workcase-0001")
    before["relations"] = [_contributed("pitfall", "pitfall-0001")]
    path = _write(project, before)
    current = _read(project, "workcase-0001")
    assert current.check_status == "mechanically_valid"
    unchanged_after = {**before, "waiting_on": "等待 Human 对同一关闭提案作出新的判断。"}
    original = path.read_bytes()

    rejected = apply_workcase_write(_command(project, before, unchanged_after, mode="update"))

    assert rejected.status == "candidate_rejected"
    assert any(issue.field_path == "phase" and "close-workcase" in issue.summary for issue in rejected.issues)
    assert path.read_bytes() == original


def test_update_workcase_entering_human_closure_confirming_freezes_contributed_to(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    _write_pitfall(project, "pitfall-0001")
    _write_pitfall(project, "pitfall-0002")
    before = _preparing("workcase-0001")
    before["relations"] = [_contributed("pitfall", "pitfall-0001")]
    path = _write(project, before)
    original = path.read_bytes()
    entering_after = {
        **before,
        "phase": "human_closure_confirming",
        "waiting_on": "等待 Human 判断关闭与责任处置。",
    }
    rejected_after = {
        **entering_after,
        "relations": [_contributed("pitfall", "pitfall-0001"), _contributed("pitfall", "pitfall-0002")],
    }

    rejected = apply_workcase_write(_command(project, before, rejected_after, mode="update"))

    assert rejected.status == "candidate_rejected"
    assert any(issue.field_path == "relations" for issue in rejected.issues)
    assert path.read_bytes() == original

    accepted = apply_workcase_write(_command(project, before, entering_after, mode="update"))

    assert accepted.status == "updated"
    assert accepted.readback is not None and accepted.readback.fields is not None
    assert accepted.readback.fields["relations"] == before["relations"]


def _first_log_after(before: dict[str, Any], *, title: str) -> dict[str, Any]:
    after = deepcopy(before)
    after["title"] = title
    after["change_log"] = [
        {
            "signature": {
                "product_name": "pytest",
                "model_name": "test-model",
                "agent_runtime_name": "pytest-runtime",
            },
            "at": "2000-01-01T00:00:00Z",
            "summary": "首次真实更新建立流水；此前历史未恢复。",
        }
    ]
    return after


def test_first_log_update_rejects_unborn_head_without_writing(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    source = _active("workcase-0001")
    source.pop("change_log")
    path = _write(project, source)
    original = path.read_bytes()
    after = _first_log_after(source, title="首次真实更新")

    result = apply_workcase_write(_command(project, source, after, mode="update"))

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "change_log" and "HEAD" in issue.summary for issue in result.issues)
    assert path.read_bytes() == original


def test_first_log_update_succeeds_when_head_and_wt_lack_log(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    source = _active("workcase-0001")
    source.pop("change_log")
    path = _write(project, source)
    _git(project.boundary.worktree_root, "add", "-A")
    _git(
        project.boundary.worktree_root,
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-q",
        "-m",
        "seed",
    )
    after = _first_log_after(source, title="首次真实更新")

    result = apply_workcase_write(_command(project, source, after, mode="update"))

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    fields = result.readback.fields
    assert fields["status"] == "open"
    assert fields["phase"] == "human_plan_confirming"
    assert fields["title"] == "首次真实更新"
    change_log = fields["change_log"]
    assert len(change_log) == 1
    entry = change_log[0]
    assert set(entry["signature"]) == {"product_name", "model_name", "agent_runtime_name"}
    assert "session_id" not in entry
    assert entry["at"] == fields["updated_at"]
    assert path.read_text(encoding="utf-8") == result.candidate_text


def test_first_log_correct_closed_succeeds_when_head_lacks_log(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = _project(current_fact_schemas, tmp_path)
    target = _active("workcase-0002", title="承接目标")
    _write(project, target)
    target_read = _read(project, "workcase-0002")
    proposal_snapshot = WorkCaseRouteTargetSnapshot(
        FactReference("sample", "workcase", "workcase-0002"),
        target_read.content_fingerprint,
        "closure_proposal.residual_decisions[0].route_target",
    )
    request_snapshot = replace(proposal_snapshot, origin_path="route_target_fingerprints[0].target")
    source = _closed_from(_closing("workcase-0001", outcome="not-achieved", target=proposal_snapshot))
    source["updated_at"] = "2026-07-26T12:00:00+08:00"
    source.pop("change_log")
    _write(project, source)
    _git(project.boundary.worktree_root, "add", "-A")
    _git(
        project.boundary.worktree_root,
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-q",
        "-m",
        "seed",
    )
    after = _first_log_after(source, title="更正原关闭时的标题")
    after["status"] = "closed"

    result = apply_workcase_write(
        _command(
            project,
            source,
            after,
            mode="correct",
            route_target_fingerprints=(request_snapshot,),
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    fields = result.readback.fields
    assert fields["status"] == "closed"
    assert fields["closure_outcome"] == "not-achieved"
    change_log = fields["change_log"]
    assert len(change_log) == 1
    entry = change_log[0]
    assert set(entry["signature"]) == {"product_name", "model_name", "agent_runtime_name"}
    assert "session_id" not in entry
    assert entry["at"] == fields["updated_at"]
