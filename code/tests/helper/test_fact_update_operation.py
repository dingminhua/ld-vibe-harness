from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytest
from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.facts import update_application
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import FactCoordinationUnavailable, serialize_fact_object
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.facts.workcase_projection import workcase_subject_fingerprint
from ldvh.helper.operations import fact_update_operation, workcase_update_operation
from ldvh.helper.service import handle_request


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    fact = project / "ldvh-base" / "sparks" / "spark-0001.yaml"
    fact.parent.mkdir(parents=True)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Exact update
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: open
summary: Before update
priority: P2
""",
        encoding="utf-8",
    )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
                "product_description: Fact update tests.",
                "projects:",
                "  - id: sample",
                f"    path: {project}",
                "    name: Sample",
                "    description: Test project.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workspace, project, fact


def _ref() -> dict[str, str]:
    return {
        "governed_project_id": "sample",
        "fact_type_key": "spark",
        "object_id": "spark-0001",
    }


def _read(
    workspace: Path,
    project: Path,
    fact_ref: dict[str, str] | None = None,
) -> dict[str, object]:
    item = _read_unchecked(workspace, project, fact_ref)
    assert item["check_status"] == "mechanically_valid"
    return item


def _read_unchecked(
    workspace: Path,
    project: Path,
    fact_ref: dict[str, str] | None = None,
) -> dict[str, object]:
    response = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {"workspace_root": str(workspace), "fact_refs": [fact_ref or _ref()]},
            }
        ),
    ).response
    assert response["outcome"] == "ok"
    item = response["result"]["items"][0]
    return item


def _mutable(item: dict[str, object]) -> dict[str, object]:
    fields = dict(item["fact_object"])
    for key in ("object_id", "fact_type_key", "created_at", "updated_at"):
        fields.pop(key)
    return fields


def _update_payload(
    workspace: Path,
    project: Path,
    fingerprint: object,
    fact_object: dict[str, object],
    fact_ref: dict[str, str] | None = None,
) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_ref": fact_ref or _ref(),
                "expected_content_fingerprint": fingerprint,
                "fact_object": fact_object,
            },
        }
    )


def _workcase_update_payload(
    workspace: Path,
    project: Path,
    fact_ref: dict[str, str],
    fingerprint: object,
    *,
    set_fields: dict[str, object] | None = None,
    remove_fields: list[str] | None = None,
    managed_records: dict[str, object] | None = None,
    response_profile: str = "compact",
) -> str:
    return json.dumps(
        {
            "response_profile": response_profile,
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_ref": fact_ref,
                "expected_content_fingerprint": fingerprint,
                "set": {} if set_fields is None else set_fields,
                "remove": [] if remove_fields is None else remove_fields,
                "managed_records": {} if managed_records is None else managed_records,
            },
        }
    )


def _create_workcase(workspace: Path, project: Path) -> dict[str, str]:
    prepared = handle_request(
        "call",
        "prepare-fact-object-draft",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    "fact_type_key": "workcase",
                },
            }
        ),
    ).response["result"]
    fact_object: dict[str, object] = {
        "title": "Controller-owned review lifecycle",
        "status": "open",
        "summary": "Current plan is ready for Human approval",
        "resume_from": "Request approval for the presented current plan",
        "waiting_on": "Human execution approval",
        "priority": "P1",
        "goal": "Exercise the Controller-owned review and closure lifecycle",
        "scope": "One bounded Helper lifecycle test",
        "workcase_profile": "control-contract-v2",
        "success_criterion_definitions": [
            {
                "criterion_id": "criterion-01",
                "statement": "The WorkCase reaches closed through all required phases",
            }
        ],
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Produce one verified result",
                "expected_result": "One result is available for Controller check",
                "status": "pending",
                "approach_summary": "Use controlled full-object Helper updates",
            }
        ],
    }
    fact_object["creation_reviews"] = [
        {
            "reviewer": "independent-plan-reviewer",
            "reviewed_at": "2026-07-20T07:20:00+08:00",
            "subject_version": 1,
            "scope": "Goal, scope, success criterion, work item, method, and risk",
            "conclusion": "changes_required",
            "feedback": ["Controller should explicitly own the phase decision"],
            "controller_resolution": "1. Accepted; the plan records Controller ownership.",
        }
    ]
    created = handle_request(
        "call",
        "create-fact-object",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "draft_basis": {
                        key: prepared[key]
                        for key in (
                            "governed_project_id",
                            "fact_type_key",
                            "candidate_object_id",
                            "schema_fingerprint",
                            "worktree_fingerprint",
                        )
                    },
                    "fact_object": fact_object,
                },
            }
        ),
    ).response
    assert created["outcome"] == "ok", json.dumps(created, ensure_ascii=False, indent=2)
    return created["result"]["actual_ref"]


def _write_v1_workcase(project: Path, *, closed: bool = False) -> tuple[dict[str, str], Path]:
    fields: dict[str, object] = {
        "object_id": "workcase-0001",
        "fact_type_key": "workcase",
        "title": "V1 migration fixture",
        "created_at": "2026-07-20T08:00:00+08:00",
        "updated_at": "2026-07-20T09:00:00+08:00",
        "status": "open",
        "summary": "Waiting for Human execution approval",
        "resume_from": "Present the current plan",
        "waiting_on": "Human execution approval",
        "priority": "P2",
        "goal": "Migrate one V1 WorkCase without changing its plan",
        "scope": "One compatibility fixture",
        "workcase_profile": "control-contract-v1",
        "success_criterion_definitions": [
            {"criterion_id": "criterion-01", "statement": "The current object migrates without history fields"}
        ],
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Perform the controlled migration",
                "expected_result": "One mechanically valid V2 object",
                "status": "pending",
                "approach_summary": "Use the generic full-snapshot update with exact CAS",
            }
        ],
        "audit_summary": [
            {
                "audit_id": "audit-01",
                "subject_kind": "pre_creation_plan",
                "subject_version": 1,
                "review_count": 1,
                "summary": "The current plan was reviewed before object creation",
            }
        ],
    }
    if closed:
        fields.update(
            {
                "status": "closed",
                "summary": "The V1 WorkCase is closed",
                "phase": "closed",
                "result_version": 1,
                "work_items": [
                    {
                        "item_id": "item-01",
                        "goal": "Perform the controlled migration",
                        "expected_result": "One mechanically valid V2 object",
                        "status": "completed",
                        "approach_summary": "Use the generic full-snapshot update with exact CAS",
                        "result_summary": "The bounded work completed",
                    }
                ],
                "success_criterion_results": [
                    {
                        "criterion_id": "criterion-01",
                        "outcome": "satisfied",
                        "summary": "The bounded result was verified",
                    }
                ],
                "execution_approval": {
                    "subject_version": 1,
                    "approved_at": "2026-07-20T08:35:00+08:00",
                    "summary": "Human approved plan version 1",
                },
                "controller_check_summary": "The Controller checked the current result",
                "validation_summary": "The current result satisfies the criterion",
                "closure_outcome": "completed",
                "disposition_summary": "No residual responsibility remains",
                "closure_approval": {
                    "subject_version": 1,
                    "approved_at": "2026-07-20T08:55:00+08:00",
                    "summary": "Human approved the completed result",
                },
                "progress_history": {
                    "coverage": "full",
                    "entries": [
                        {
                            "event_id": "progress-001",
                            "plan_version": 1,
                            "round": 1,
                            "phase": "executing",
                            "entered_at": "2026-07-20T08:36:00+08:00",
                            "transition_kind": "started",
                            "transition_summary": "Execution started after Human approval",
                        },
                        {
                            "event_id": "progress-002",
                            "plan_version": 1,
                            "round": 1,
                            "phase": "controller_checking",
                            "entered_at": "2026-07-20T08:42:00+08:00",
                            "transition_kind": "advanced",
                            "transition_summary": "Controller began checking the completed item",
                        },
                        {
                            "event_id": "progress-003",
                            "plan_version": 1,
                            "round": 1,
                            "phase": "independent_reviewing",
                            "entered_at": "2026-07-20T08:47:00+08:00",
                            "transition_kind": "advanced",
                            "transition_summary": "The current result entered independent review",
                        },
                        {
                            "event_id": "progress-004",
                            "plan_version": 1,
                            "round": 1,
                            "phase": "closure_preparing",
                            "entered_at": "2026-07-20T08:52:00+08:00",
                            "transition_kind": "advanced",
                            "transition_summary": "Controller prepared the closure report",
                        },
                    ],
                },
                "nonbinding_followups": [
                    {
                        "followup_id": "followup-01",
                        "summary": "Consider simplifying compatibility fixtures later",
                        "rationale": "This is not part of the completed migration responsibility",
                    }
                ],
                "improvement_observations": [
                    {
                        "observation_id": "observation-01",
                        "topic_key": "compatibility-fixture-simplification",
                        "summary": "The compatibility fixture could be easier to maintain",
                        "ownership": "current_scope",
                        "value_dimensions": ["V6"],
                        "net_value_summary": "A later cleanup may reduce maintenance cost",
                        "disposition": "nonbinding_followup",
                        "disposition_ref": "followup-01",
                        "disposition_summary": "Deferred because it does not affect the current result",
                    }
                ],
            }
        )
        for field_name in ("resume_from", "waiting_on", "priority"):
            fields.pop(field_name, None)
    creation_fingerprint = workcase_subject_fingerprint(fields, "plan_current")
    fields["creation_reviews"] = [
        {
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "subject_version": 1,
            "scope": scope,
            "conclusion": "pass",
            "feedback": [feedback],
            "controller_resolution": "Accepted",
            "review_basis": {
                "projection_key": "plan_current",
                "subject_fingerprint": creation_fingerprint,
            },
        }
        for reviewer, reviewed_at, scope, feedback in (
            (
                "independent-plan-reviewer-a",
                "2026-07-20T08:25:00+08:00",
                "Current goal, scope, and criteria",
                "The migration fixture has a bounded objective",
            ),
            (
                "independent-plan-reviewer-b",
                "2026-07-20T08:30:00+08:00",
                "Current item and compatibility method",
                "The compatibility method is explicit",
            ),
        )
    ]
    fields["audit_summary"][0]["review_count"] = len(fields["creation_reviews"])
    if closed:
        result_fingerprint = workcase_subject_fingerprint(fields, "result_implementation")
        fields["result_reviews"] = [
            {
                "reviewer": reviewer,
                "reviewed_at": reviewed_at,
                "subject_version": 1,
                "scope": scope,
                "conclusion": "pass",
                "feedback": [feedback],
                "controller_resolution": "Accepted",
                "review_basis": {
                    "projection_key": "result_implementation",
                    "subject_fingerprint": result_fingerprint,
                },
            }
            for reviewer, reviewed_at, scope, feedback in (
                (
                    "independent-result-reviewer-a",
                    "2026-07-20T08:48:00+08:00",
                    "Current implementation result",
                    "The implementation result matches the item outcome",
                ),
                (
                    "independent-result-reviewer-b",
                    "2026-07-20T08:50:00+08:00",
                    "Current criterion result and closure readiness",
                    "The current result is ready for closure",
                ),
            )
        ]
    path = project / "ldvh-base/workcases/workcase-0001.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_fact_object(LAYOUTS["workcase"], fields, None), encoding="utf-8")
    return {
        "governed_project_id": "sample",
        "fact_type_key": "workcase",
        "object_id": "workcase-0001",
    }, path


def test_generic_full_snapshot_can_update_v2_content_without_process_history(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)
    approved = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            before["content_fingerprint"],
            set_fields={
                "phase": "executing",
                "summary": "Human approved the plan; execution may start",
                "resume_from": "Execute item-01",
            },
            remove_fields=["waiting_on"],
            managed_records={"execution_approval": {"summary": "Human approved plan version 1"}},
        ),
    ).response
    assert approved["outcome"] == "ok"

    current = _read(workspace, project, workcase_ref)
    target = _mutable(current)
    target["summary"] = "Execution continues with a clarified current summary"
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, current["content_fingerprint"], target, workcase_ref),
    ).response

    assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
    after = _read(workspace, project, workcase_ref)["fact_object"]
    assert after["summary"] == target["summary"]
    assert "progress_history" not in after


def test_generic_v2_fact_correction_preserves_managed_event_identity_and_blocks_new_events(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)

    before_review_correction = _read(workspace, project, workcase_ref)
    corrected_review_target = _mutable(before_review_correction)
    corrected_review_target["creation_reviews"][0]["scope"] = "Corrected current plan review scope"
    corrected_review_target["creation_reviews"][0]["feedback"] = ["Corrected current plan finding"]
    corrected_review_target["creation_reviews"][0]["controller_resolution"] = "Corrected current disposition"
    corrected_review = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            before_review_correction["content_fingerprint"],
            corrected_review_target,
            workcase_ref,
        ),
    ).response
    assert corrected_review["outcome"] == "ok", json.dumps(corrected_review, ensure_ascii=False, indent=2)

    current = _read(workspace, project, workcase_ref)
    approved = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            current["content_fingerprint"],
            set_fields={"phase": "executing", "summary": "Human approved execution"},
            remove_fields=["waiting_on"],
            managed_records={"execution_approval": {"summary": "Human approved plan version 1"}},
        ),
    ).response
    assert approved["outcome"] == "ok", json.dumps(approved, ensure_ascii=False, indent=2)

    before_approval_correction = _read(workspace, project, workcase_ref)
    corrected_approval_target = _mutable(before_approval_correction)
    corrected_approval_target["execution_approval"]["summary"] = "Corrected wording for the same Human approval"
    corrected_approval = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            before_approval_correction["content_fingerprint"],
            corrected_approval_target,
            workcase_ref,
        ),
    ).response
    assert corrected_approval["outcome"] == "ok", json.dumps(corrected_approval, ensure_ascii=False, indent=2)

    corrected = _read(workspace, project, workcase_ref)
    fact_path = project / corrected["canonical_path"]
    raw = fact_path.read_bytes()
    retimed = _mutable(corrected)
    retimed["execution_approval"]["approved_at"] = "2026-07-26T18:00:00+08:00"
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, corrected["content_fingerprint"], retimed, workcase_ref),
    ).response
    assert rejected["outcome"] == "rejected"
    assert any("事件身份" in gap["summary"] for gap in rejected["gaps"])
    assert fact_path.read_bytes() == raw

    formed_review = _mutable(corrected)
    formed_review["creation_reviews"].append(
        {
            **formed_review["creation_reviews"][0],
            "reviewer": "new-review-event",
        }
    )
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, corrected["content_fingerprint"], formed_review, workcase_ref),
    ).response
    assert rejected["outcome"] == "rejected"
    assert any("review 必须使用 update-workcase" in gap["summary"] for gap in rejected["gaps"])
    assert fact_path.read_bytes() == raw


def test_generic_full_snapshot_cannot_form_v2_approval_records(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)
    target = _mutable(before)
    target.update(
        {
            "phase": "executing",
            "summary": "Attempted generic approval formation",
            "execution_approval": {
                "subject_version": 1,
                "approved_at": before["fact_object"]["updated_at"],
                "summary": "Human approved plan version 1",
            },
        }
    )
    target.pop("waiting_on")

    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target, workcase_ref),
    ).response

    assert rejected["outcome"] == "rejected"
    assert any("approval 必须使用 update-workcase" in gap["summary"] for gap in rejected["gaps"])


def test_generic_full_snapshot_rejects_controller_resolution_without_feedback(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)
    fact_path = project / before["canonical_path"]
    raw = fact_path.read_bytes()
    target = _mutable(before)
    review = target["creation_reviews"][0]
    review["conclusion"] = "pass"
    review.pop("feedback")
    review["controller_resolution"] = "Nothing remains to resolve"

    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target, workcase_ref),
    ).response

    assert rejected["outcome"] == "rejected"
    assert any("没有 feedback" in gap["summary"] for gap in rejected["gaps"])
    assert fact_path.read_bytes() == raw


def test_generic_invalid_repair_can_restore_missing_creation_resolution_without_retiming(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)
    valid = _read(workspace, project, workcase_ref)
    fact_path = project / valid["canonical_path"]
    invalid_fields = deepcopy(valid["fact_object"])
    invalid_fields["creation_reviews"][0].pop("controller_resolution")
    fact_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], invalid_fields, None),
        encoding="utf-8",
    )
    invalid = _read_unchecked(workspace, project, workcase_ref)
    assert invalid["check_status"] == "invalid"
    assert invalid["content_fingerprint"] is not None
    raw = fact_path.read_bytes()

    retimed_target = deepcopy(_mutable(invalid))
    retimed_target["creation_reviews"][0]["reviewed_at"] = "2026-07-26T12:45:00+08:00"
    retimed_target["creation_reviews"][0]["controller_resolution"] = "Accepted and handled."
    retimed = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            invalid["content_fingerprint"],
            retimed_target,
            workcase_ref,
        ),
    ).response
    assert retimed["outcome"] == "rejected"
    assert any("review 必须使用 update-workcase" in gap["summary"] for gap in retimed["gaps"])
    assert fact_path.read_bytes() == raw

    widened_target = deepcopy(_mutable(invalid))
    widened_target["summary"] = "Also changed while repairing the invalid review"
    widened_target["creation_reviews"][0]["feedback"] = ["Also rewrote Reviewer-owned feedback"]
    widened_target["creation_reviews"][0]["controller_resolution"] = "Accepted and handled."
    widened = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            invalid["content_fingerprint"],
            widened_target,
            workcase_ref,
        ),
    ).response
    assert widened["outcome"] == "rejected"
    assert any("invalid-before 窄修复" in gap["summary"] for gap in widened["gaps"])
    assert fact_path.read_bytes() == raw

    repaired_target = deepcopy(_mutable(invalid))
    repaired_target["creation_reviews"][0]["controller_resolution"] = "Accepted and handled."
    repaired = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            invalid["content_fingerprint"],
            repaired_target,
            workcase_ref,
        ),
    ).response
    assert repaired["outcome"] == "ok", json.dumps(repaired, ensure_ascii=False, indent=2)
    after = _read(workspace, project, workcase_ref)["fact_object"]
    assert after["creation_reviews"][0]["controller_resolution"] == "Accepted and handled."


def test_generic_invalid_repair_can_restore_missing_result_resolution(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)
    created = _read(workspace, project, workcase_ref)
    fact_path = project / created["canonical_path"]
    valid_fields = deepcopy(created["fact_object"])
    event_at = valid_fields["updated_at"]
    valid_fields.update(
        {
            "phase": "controller_checking",
            "summary": "Controller handled the independent result feedback",
            "result_version": 1,
            "success_criterion_results": [
                {
                    "criterion_id": "criterion-01",
                    "outcome": "satisfied",
                    "summary": "The bounded result was produced and checked",
                }
            ],
            "controller_check_summary": "The Controller checked the completed item and criterion result",
            "execution_approval": {
                "subject_version": 1,
                "approved_at": event_at,
                "summary": "Human approved plan version 1",
            },
            "result_reviews": [
                {
                    "reviewer": "independent-result-reviewer",
                    "reviewed_at": event_at,
                    "subject_version": 1,
                    "scope": "Current item and criterion result",
                    "conclusion": "changes_required",
                    "feedback": ["Clarify the Controller check"],
                    "controller_resolution": "Accepted and clarified in the current check",
                }
            ],
            "work_items": [
                {
                    **valid_fields["work_items"][0],
                    "status": "completed",
                    "result_summary": "The bounded result was produced",
                }
            ],
        }
    )
    valid_fields.pop("waiting_on")
    fact_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], valid_fields, None),
        encoding="utf-8",
    )
    assert _read(workspace, project, workcase_ref)["check_status"] == "mechanically_valid"

    invalid_fields = deepcopy(valid_fields)
    invalid_fields["result_reviews"][0].pop("controller_resolution")
    fact_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], invalid_fields, None),
        encoding="utf-8",
    )
    invalid = _read_unchecked(workspace, project, workcase_ref)
    assert invalid["check_status"] == "invalid"
    repaired_target = _mutable(invalid)
    repaired_target["result_reviews"][0]["controller_resolution"] = "Accepted and clarified in the current check"

    repaired = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            invalid["content_fingerprint"],
            repaired_target,
            workcase_ref,
        ),
    ).response

    assert repaired["outcome"] == "ok", json.dumps(repaired, ensure_ascii=False, indent=2)
    after = _read(workspace, project, workcase_ref)["fact_object"]
    assert after["result_reviews"][0]["controller_resolution"] == "Accepted and clarified in the current check"


def test_generic_invalid_repair_adds_only_the_profile_required_by_created_at(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)
    valid = _read(workspace, project, workcase_ref)
    fact_path = project / valid["canonical_path"]
    invalid_fields = deepcopy(valid["fact_object"])
    invalid_fields.pop("workcase_profile")
    fact_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], invalid_fields, None),
        encoding="utf-8",
    )
    invalid = _read_unchecked(workspace, project, workcase_ref)
    assert invalid["check_status"] == "invalid"
    assert invalid["content_fingerprint"] is not None
    raw = fact_path.read_bytes()

    expanded_target = deepcopy(_mutable(invalid))
    expanded_target["workcase_profile"] = "control-contract-v2"
    expanded_target["goal"] = "Changed while adding the missing profile"
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            invalid["content_fingerprint"],
            expanded_target,
            workcase_ref,
        ),
    ).response
    assert rejected["outcome"] == "rejected"
    assert any("不得同次改变其它领域内容" in gap["summary"] for gap in rejected["gaps"])
    assert fact_path.read_bytes() == raw

    repaired_target = deepcopy(_mutable(invalid))
    repaired_target["workcase_profile"] = "control-contract-v2"
    repaired = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            invalid["content_fingerprint"],
            repaired_target,
            workcase_ref,
        ),
    ).response
    assert repaired["outcome"] == "ok", json.dumps(repaired, ensure_ascii=False, indent=2)
    after = _read(workspace, project, workcase_ref)["fact_object"]
    assert after["workcase_profile"] == "control-contract-v2"
    assert after["goal"] == valid["fact_object"]["goal"]


def test_generic_invalid_unknown_profile_repair_cannot_form_a_new_creation_review(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)
    valid = _read(workspace, project, workcase_ref)
    fact_path = project / valid["canonical_path"]
    invalid_fields = deepcopy(valid["fact_object"])
    invalid_fields["workcase_profile"] = "unknown-contract"
    fact_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], invalid_fields, None),
        encoding="utf-8",
    )
    invalid = _read_unchecked(workspace, project, workcase_ref)
    assert invalid["check_status"] == "invalid"
    raw = fact_path.read_bytes()

    forged_target = deepcopy(_mutable(invalid))
    forged_target["workcase_profile"] = "control-contract-v2"
    forged_target["goal"] = "Silently replace the reviewed plan while repairing the profile"
    forged_target["plan_version"] = 2
    forged_target["creation_reviews"] = [
        {
            "reviewer": "forged-plan-reviewer",
            "reviewed_at": "2026-07-26T14:00:00+08:00",
            "subject_version": 2,
            "scope": "The silently replaced plan",
            "conclusion": "pass",
        }
    ]
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            invalid["content_fingerprint"],
            forged_target,
            workcase_ref,
        ),
    ).response

    assert rejected["outcome"] == "rejected"
    assert any(
        "新增或替换 WorkCase review 必须使用 update-workcase" in gap["summary"]
        for gap in rejected["gaps"]
    )
    assert fact_path.read_bytes() == raw


def test_generic_invalid_ordinary_repair_cannot_rewrite_existing_managed_review(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)
    valid = _read(workspace, project, workcase_ref)
    fact_path = project / valid["canonical_path"]
    invalid_fields = deepcopy(valid["fact_object"])
    invalid_fields["summary"] = ""
    fact_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], invalid_fields, None),
        encoding="utf-8",
    )
    invalid = _read_unchecked(workspace, project, workcase_ref)
    assert invalid["check_status"] == "invalid"
    raw = fact_path.read_bytes()

    rewritten_target = deepcopy(_mutable(invalid))
    rewritten_target["summary"] = "Repaired current summary"
    rewritten_target["creation_reviews"][0]["scope"] = "Silently rewritten review scope"
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            invalid["content_fingerprint"],
            rewritten_target,
            workcase_ref,
        ),
    ).response

    assert rejected["outcome"] == "rejected"
    assert any(
        "invalid-before 修复必须原样保留 WorkCase 托管 review/approval" in gap["summary"]
        for gap in rejected["gaps"]
    )
    assert fact_path.read_bytes() == raw


def test_generic_v2_fact_correction_cannot_delete_an_existing_review_event(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)
    current = _read(workspace, project, workcase_ref)
    fact_path = project / current["canonical_path"]
    fields = deepcopy(current["fact_object"])
    fields["creation_reviews"].append(
        {
            "reviewer": "second-plan-reviewer",
            "reviewed_at": "2026-07-26T13:05:00+08:00",
            "subject_version": 1,
            "scope": "A second independent view of the current plan",
            "conclusion": "pass",
        }
    )
    fact_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], fields, None),
        encoding="utf-8",
    )
    before = _read(workspace, project, workcase_ref)
    raw = fact_path.read_bytes()
    target = deepcopy(_mutable(before))
    target["creation_reviews"].pop()

    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target, workcase_ref),
    ).response

    assert rejected["outcome"] == "rejected"
    assert any("移除 WorkCase review 事件" in gap["summary"] for gap in rejected["gaps"])
    assert fact_path.read_bytes() == raw


def test_generic_v2_same_event_reviewer_correction_can_form_its_required_creation_resolution(
    tmp_path: Path,
) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)
    current = _read(workspace, project, workcase_ref)
    fact_path = project / current["canonical_path"]
    fields = deepcopy(current["fact_object"])
    review = fields["creation_reviews"][0]
    review["conclusion"] = "pass"
    review.pop("feedback")
    review.pop("controller_resolution")
    fact_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], fields, None),
        encoding="utf-8",
    )
    before = _read(workspace, project, workcase_ref)
    target = deepcopy(_mutable(before))
    corrected_review = target["creation_reviews"][0]
    corrected_review["conclusion"] = "changes_required"
    corrected_review["feedback"] = ["The original review omitted one finding"]
    corrected_review["controller_resolution"] = "Accepted the corrected finding."

    corrected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target, workcase_ref),
    ).response

    assert corrected["outcome"] == "ok", json.dumps(corrected, ensure_ascii=False, indent=2)
    after = _read(workspace, project, workcase_ref)["fact_object"]
    assert after["creation_reviews"][0]["controller_resolution"] == "Accepted the corrected finding."


def test_generic_invalid_repair_cannot_add_resolutions_to_multiple_reviews_at_once(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    workcase_ref = _create_workcase(workspace, project)
    valid = _read(workspace, project, workcase_ref)
    fact_path = project / valid["canonical_path"]
    invalid_fields = deepcopy(valid["fact_object"])
    invalid_fields["creation_reviews"][0].pop("controller_resolution")
    invalid_fields["creation_reviews"].append(
        {
            "reviewer": "second-plan-reviewer",
            "reviewed_at": "2026-07-26T13:05:00+08:00",
            "subject_version": 1,
            "scope": "A second review with one finding",
            "conclusion": "changes_required",
            "feedback": ["Clarify the second boundary"],
        }
    )
    fact_path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], invalid_fields, None),
        encoding="utf-8",
    )
    invalid = _read_unchecked(workspace, project, workcase_ref)
    assert invalid["check_status"] == "invalid"
    raw = fact_path.read_bytes()
    target = deepcopy(_mutable(invalid))
    target["creation_reviews"][0]["controller_resolution"] = "Accepted the first finding."
    target["creation_reviews"][1]["controller_resolution"] = "Accepted the second finding."

    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, invalid["content_fingerprint"], target, workcase_ref),
    ).response

    assert rejected["outcome"] == "rejected"
    assert any("唯一窄例外" in gap["summary"] for gap in rejected["gaps"])
    assert fact_path.read_bytes() == raw


def test_workcase_delta_records_execution_approval_and_idempotent_retry(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)
    payload = _workcase_update_payload(
        workspace,
        project,
        workcase_ref,
        before["content_fingerprint"],
        set_fields={
            "phase": "executing",
            "summary": "Human approved the plan; execution may start",
            "resume_from": "Execute item-01",
        },
        remove_fields=["waiting_on"],
        managed_records={"execution_approval": {"summary": "Human approved plan version 1"}},
    )

    response = handle_request("call", "update-workcase", payload).response

    assert_common_response(response)
    assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
    assert response["result"]["before_state"]["phase"] == "human_plan_confirming"
    assert response["result"]["after_state"]["phase"] == "executing"
    assert response["result"]["managed_record_receipts"] == [
        {"action": "execution_approval_recorded", "subject_version": 1}
    ]
    assert any(
        source["kind"] == "rule" and source["locator"] == "workcase-fact-type::v2 WorkCase 专属受控变更输入字段"
        for source in response["sources"]
    )
    assert response["result"]["event_at"] is not None
    current = _read(workspace, project, workcase_ref)
    fields = current["fact_object"]
    assert fields["updated_at"] == response["result"]["event_at"]
    assert fields["execution_approval"]["approved_at"] == response["result"]["event_at"]
    assert "progress_history" not in fields
    observation = next(source for source in response["sources"] if source["kind"] == "working_tree")
    assert observation["observed_at"] == response["result"]["event_at"]

    fact_path = project / current["canonical_path"]
    raw = fact_path.read_bytes()
    retry = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            current["content_fingerprint"],
            managed_records={"execution_approval": {"summary": "Human approved plan version 1"}},
        ),
    ).response
    assert retry["outcome"] == "no_change"
    assert retry["result"]["event_at"] is None
    assert retry["result"]["changed_fields"] == []
    assert retry["result"]["managed_record_receipts"] == []
    assert fact_path.read_bytes() == raw


def test_workcase_delta_withdraws_an_erroneously_recorded_execution_approval(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)
    approved = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            before["content_fingerprint"],
            set_fields={
                "phase": "executing",
                "summary": "Execution was recorded as approved.",
                "resume_from": "Begin item-01.",
            },
            remove_fields=["waiting_on"],
            managed_records={"execution_approval": {"summary": "Human approved plan version 1"}},
        ),
    ).response
    assert approved["outcome"] == "ok"

    current = _read(workspace, project, workcase_ref)
    response = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            current["content_fingerprint"],
            set_fields={
                "phase": "human_plan_confirming",
                "summary": "The plan awaits explicit Human approval.",
                "resume_from": "Present the complete current plan to Human.",
                "waiting_on": "Human execution approval for plan_version 1",
                "work_items": [
                    {
                        **current["fact_object"]["work_items"][0],
                        "status": "pending",
                    }
                ],
            },
            managed_records={
                "withdraw_execution_approval": {"summary": "Human clarified that execution approval was not granted."}
            },
        ),
    ).response

    assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
    assert response["result"]["managed_record_receipts"] == [
        {"action": "execution_approval_withdrawn", "subject_version": 1}
    ]
    after = _read(workspace, project, workcase_ref)["fact_object"]
    assert after["plan_version"] == 1
    assert after["phase"] == "human_plan_confirming"
    assert "execution_approval" not in after
    assert "progress_history" not in after
    assert after["work_items"][0]["status"] == "pending"


def test_workcase_delta_walks_controller_owned_review_and_atomic_closure(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    (docs / "evidence.md").write_text("Verified result\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)

    def update(
        *,
        set_fields: dict[str, object] | None = None,
        remove_fields: list[str] | None = None,
        managed_records: dict[str, object] | None = None,
    ) -> dict[str, object]:
        before = _read(workspace, project, workcase_ref)
        response = handle_request(
            "call",
            "update-workcase",
            _workcase_update_payload(
                workspace,
                project,
                workcase_ref,
                before["content_fingerprint"],
                set_fields=set_fields,
                remove_fields=remove_fields,
                managed_records=managed_records,
            ),
        ).response
        assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
        return _read(workspace, project, workcase_ref)["fact_object"]

    pending = _read(workspace, project, workcase_ref)["fact_object"]["work_items"][0]
    in_progress = {
        **pending,
        "status": "in_progress",
        "current_summary": "Producing the bounded result",
        "resume_from": "Finish and verify the result",
    }
    update(
        set_fields={
            "phase": "executing",
            "summary": "Human approved the current plan; execution started",
            "resume_from": "Complete item-01",
            "work_items": [in_progress],
        },
        remove_fields=["waiting_on"],
        managed_records={"execution_approval": {"summary": "Human approved the presented current plan"}},
    )

    completed_item = {key: value for key, value in in_progress.items() if key not in {"current_summary", "resume_from"}}
    completed_item.update(
        {
            "status": "completed",
            "result_summary": "The bounded result was produced and verified",
        }
    )
    update(
        set_fields={
            "phase": "controller_checking",
            "summary": "Controller is checking the completed result",
            "resume_from": "Check the result and initiate independent review",
            "result_version": 1,
            "controller_check_summary": "Controller checked the item result and focused evidence",
            "work_items": [completed_item],
            "success_criterion_results": [
                {
                    "criterion_id": "criterion-01",
                    "outcome": "satisfied",
                    "summary": "The focused lifecycle result was produced and verified",
                }
            ],
        },
    )
    update(
        set_fields={
            "phase": "independent_reviewing",
            "summary": "Independent result review is in progress",
            "resume_from": "Obtain review feedback and let Controller decide the next phase",
        },
    )
    before_invalid_review = _read(workspace, project, workcase_ref)
    fact_path = project / before_invalid_review["canonical_path"]
    raw = fact_path.read_bytes()
    invalid_review = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            before_invalid_review["content_fingerprint"],
            set_fields={"controller_check_summary": "Changed while the review event was recorded"},
            managed_records={
                "append_result_reviews": [
                    {
                        "reviewer": "independent-result-reviewer",
                        "scope": "Current result subject",
                        "conclusion": "pass",
                    }
                ]
            },
        ),
    ).response
    assert invalid_review["outcome"] == "invalid_request"
    assert any("不得变更被审结果主体" in gap["summary"] for gap in invalid_review["gaps"])
    assert fact_path.read_bytes() == raw

    reviewed = update(
        managed_records={
            "append_result_reviews": [
                {
                    "reviewer": "independent-result-reviewer",
                    "scope": "Item result, success criterion, Controller check, validation, and residual risk",
                    "conclusion": "blocked",
                    "feedback": ["The reviewer would prefer another validation statement"],
                }
            ]
        }
    )
    assert reviewed["phase"] == "independent_reviewing"
    assert "controller_resolution" not in reviewed["result_reviews"][0]

    handled = update(
        set_fields={
            "phase": "controller_checking",
            "summary": "Controller handled the feedback and decided no rereview is required",
            "resume_from": "Enter closure preparation with the retained current-version review",
        },
        managed_records={
            "resolve_result_reviews": [
                {
                    "review_index": 0,
                    "controller_resolution": (
                        "Rejected as a phase veto; existing evidence is sufficient, so no rereview is needed."
                    ),
                }
            ],
        },
    )
    assert handled["phase"] == "controller_checking"
    assert handled["result_reviews"][0]["conclusion"] == "blocked"

    update(
        set_fields={
            "phase": "closure_preparing",
            "summary": "Controller is preparing the final closure report",
            "resume_from": "Complete validation, outcome, and disposition",
        },
    )
    prepared = update(
        set_fields={
            "validation_summary": "The success criterion is supported by the focused evidence",
            "closure_outcome": "completed",
            "disposition_summary": "No residual responsibility remains",
        }
    )
    assert prepared["result_version"] == 1
    assert prepared["result_reviews"][0]["conclusion"] == "blocked"

    update(
        set_fields={
            "phase": "human_closure_confirming",
            "summary": "Controller judged the complete report ready for Human closure confirmation",
            "resume_from": "Await Human decision on the current result and report",
            "waiting_on": "Human closure confirmation",
        }
    )
    closed = update(
        set_fields={
            "status": "closed",
            "phase": "closed",
            "summary": "Human approved the current result and report; the WorkCase is closed",
        },
        remove_fields=["priority", "resume_from", "waiting_on"],
        managed_records={
            "closure_approval": {"summary": "Human approved the current result version and complete report"}
        },
    )
    assert closed["status"] == "closed"
    assert closed["phase"] == "closed"
    assert closed["closure_approval"]["approved_at"] == closed["updated_at"]

    persisted = _read(workspace, project, workcase_ref)
    fact_path = project / persisted["canonical_path"]
    raw = fact_path.read_bytes()
    rewritten_approval = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            persisted["content_fingerprint"],
            set_fields={"status": "closed", "phase": "closed"},
            managed_records={"closure_approval": {"summary": "A different closure approval statement"}},
        ),
    ).response
    assert rewritten_approval["outcome"] == "rejected"
    assert any("通用事实修正" in gap["summary"] for gap in rewritten_approval["gaps"])
    assert fact_path.read_bytes() == raw


def test_workcase_delta_current_dependent_construction_failure_is_rejected(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)

    response = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            before["content_fingerprint"],
            set_fields={"plan_version": 2, "phase": "human_plan_confirming"},
            managed_records={
                "replace_creation_reviews": [
                    {
                        "reviewer": "reviewer",
                        "scope": "Unchanged plan",
                        "conclusion": "pass",
                        "feedback": ["No plan change"],
                        "controller_resolution": "Accepted",
                    }
                ]
            },
        ),
    ).response

    assert response["outcome"] == "rejected"
    assert response["changes"] == []


def test_workcase_delta_preserves_current_read_unavailable_classification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)
    unavailable = FactReadResult(
        "ldvh-base/workcases/workcase-0001.yaml",
        "yaml",
        "unavailable",
        None,
        None,
        (FactIssue("location", "simulated safe-read capability gap"),),
    )
    monkeypatch.setattr(workcase_update_operation, "_current_read", lambda *_args, **_kwargs: unavailable)

    response = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            before["content_fingerprint"],
            set_fields={"summary": "Would update"},
        ),
    ).response

    assert response["outcome"] == "unavailable"
    assert response["changes"] == []


def test_workcase_delta_platform_durability_unavailable_precedes_target_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    monkeypatch.setattr(workcase_update_operation, "durable_writes_enabled", lambda: False)
    reference = {
        "governed_project_id": "sample",
        "fact_type_key": "workcase",
        "object_id": "workcase-0001",
    }
    original = fact.read_bytes()

    response = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            reference,
            "0" * 64,
            set_fields={"summary": "Must not be written"},
        ),
    ).response

    assert response["outcome"] == "unavailable"
    assert "file-only" in response["summary"]
    assert fact.read_bytes() == original


def test_workcase_delta_stale_fingerprint_rejects_without_writing(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)
    fact_path = project / before["canonical_path"]
    fact_path.write_text(
        fact_path.read_text(encoding="utf-8").replace("Current plan is ready", "Current plan remains ready"),
        encoding="utf-8",
    )
    changed = fact_path.read_bytes()

    response = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            before["content_fingerprint"],
            set_fields={"summary": "Would overwrite stale content"},
        ),
    ).response

    assert response["outcome"] == "rejected"
    assert fact_path.read_bytes() == changed


def test_workcase_delta_plan_bump_applies_fixed_reset_and_replaces_creation_review(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)
    approved = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            before["content_fingerprint"],
            set_fields={
                "phase": "executing",
                "summary": "Execution approved",
                "resume_from": "Execute item-01",
            },
            remove_fields=["waiting_on"],
            managed_records={"execution_approval": {"summary": "Human approved plan version 1"}},
        ),
    ).response
    assert approved["outcome"] == "ok"
    current = _read(workspace, project, workcase_ref)
    response = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            current["content_fingerprint"],
            set_fields={
                "goal": "Exercise the revised Controller-owned lifecycle",
                "phase": "human_plan_confirming",
                "plan_version": 2,
                "summary": "Revised plan is ready for Human approval",
                "resume_from": "Request approval for revised plan version 2",
                "waiting_on": "Human execution approval",
            },
            managed_records={
                "replace_creation_reviews": [
                    {
                        "reviewer": "independent-plan-reviewer-v2",
                        "scope": "Revised goal and unchanged bounded implementation",
                        "conclusion": "pass",
                        "feedback": ["The revised plan is coherent"],
                        "controller_resolution": "Accepted; the current plan includes the review feedback.",
                    }
                ]
            },
        ),
    ).response

    assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
    after = _read(workspace, project, workcase_ref)["fact_object"]
    assert after["plan_version"] == 2
    assert after["phase"] == "human_plan_confirming"
    assert "execution_approval" not in after
    assert after["creation_reviews"][0]["subject_version"] == 2
    assert after["creation_reviews"][0]["reviewed_at"] == after["updated_at"]
    assert response["result"]["managed_record_receipts"][0]["action"] == "creation_review_replaced"


def test_workcase_delta_rejects_legacy_workcase_without_writing(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Legacy authorized work\n", encoding="utf-8")
    fact_path = project / "ldvh-base" / "workcases" / "workcase-0001.yaml"
    fact_path.parent.mkdir(parents=True)
    fact_path.write_text(
        """object_id: workcase-0001
fact_type_key: workcase
title: Legacy WorkCase
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: open
summary: Waiting for Human approval
resume_from: Present the plan
waiting_on: Human execution approval
priority: P2
goal: Complete legacy work
scope: One legacy object
success_criteria:
- The result is verified
phase: human_plan_confirming
plan_version: 1
work_items:
- item_id: item-01
  goal: Produce the result
  expected_result: One result
  status: pending
  approach_summary: Use the bounded implementation path
creation_reviews:
- reviewer: independent-reviewer
  reviewed_at: 2026-07-14T09:30:00+08:00
  subject_version: 1
  scope: Goal, scope, criteria, work item and risks
  conclusion: pass
  feedback:
  - The plan is coherent
  controller_resolution: Accepted; no change required.
""",
        encoding="utf-8",
    )
    reference = {
        "governed_project_id": "sample",
        "fact_type_key": "workcase",
        "object_id": "workcase-0001",
    }
    before = _read(workspace, project, reference)
    raw = fact_path.read_bytes()

    response = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            reference,
            before["content_fingerprint"],
            set_fields={"summary": "Must use the generic full-target update"},
        ),
    ).response

    assert response["outcome"] == "rejected"
    assert fact_path.read_bytes() == raw


def test_v1_migration_uses_generic_full_snapshot_and_update_workcase_rejects_v1(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    reference, fact_path = _write_v1_workcase(project)
    before = _read(workspace, project, reference)
    raw = fact_path.read_bytes()

    convenience = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            reference,
            before["content_fingerprint"],
            set_fields={"summary": "Attempted V1 convenience update"},
        ),
    ).response
    assert convenience["outcome"] == "rejected"
    assert fact_path.read_bytes() == raw

    target = _mutable(before)
    target["workcase_profile"] = "control-contract-v2"
    target.pop("audit_summary")
    target["creation_reviews"] = [
        {key: value for key, value in target["creation_reviews"][0].items() if key != "review_basis"}
    ]
    migrated = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target, reference),
    ).response

    assert migrated["outcome"] == "ok", json.dumps(migrated, ensure_ascii=False, indent=2)
    after = _read(workspace, project, reference)["fact_object"]
    assert after["workcase_profile"] == "control-contract-v2"
    assert "audit_summary" not in after
    assert "review_basis" not in after["creation_reviews"][0]
    assert after["plan_version"] == before["fact_object"]["plan_version"]
    assert after["phase"] == before["fact_object"]["phase"]


def test_closed_v1_generic_migration_preserves_terminal_event_identity_and_classification(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    reference, fact_path = _write_v1_workcase(project, closed=True)
    before = _read(workspace, project, reference)
    raw = fact_path.read_bytes()

    ordinary = _mutable(before)
    ordinary["summary"] = "Attempted ordinary V1 rewrite"
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], ordinary, reference),
    ).response
    assert rejected["outcome"] == "rejected"
    assert fact_path.read_bytes() == raw

    migrated_target = _mutable(before)
    migrated_target["workcase_profile"] = "control-contract-v2"
    for field_name in (
        "audit_summary",
        "progress_history",
        "improvement_observations",
        "nonbinding_followups",
    ):
        migrated_target.pop(field_name)
    for field_name in ("creation_reviews", "result_reviews"):
        migrated_target[field_name] = [
            {key: value for key, value in review.items() if key != "review_basis"}
            for review in migrated_target[field_name]
        ]

    invalid_targets = []
    reopened = deepcopy(migrated_target)
    reopened.update({"status": "open", "phase": "human_closure_confirming", "waiting_on": "Human decision"})
    invalid_targets.append(reopened)
    reclassified = deepcopy(migrated_target)
    reclassified["closure_outcome"] = "partial"
    invalid_targets.append(reclassified)
    retimed = deepcopy(migrated_target)
    retimed["closure_approval"]["approved_at"] = "2026-07-20T08:56:00+08:00"
    invalid_targets.append(retimed)
    execution_reversioned = deepcopy(migrated_target)
    execution_reversioned["execution_approval"]["subject_version"] = 2
    invalid_targets.append(execution_reversioned)
    closure_reversioned = deepcopy(migrated_target)
    closure_reversioned["closure_approval"]["subject_version"] = 2
    invalid_targets.append(closure_reversioned)
    reordered_reviews = deepcopy(migrated_target)
    reordered_reviews["creation_reviews"] = list(reversed(reordered_reviews["creation_reviews"]))
    reordered_reviews["result_reviews"] = list(reversed(reordered_reviews["result_reviews"]))
    invalid_targets.append(reordered_reviews)
    for invalid in invalid_targets:
        response = handle_request(
            "call",
            "update-fact-object",
            _update_payload(workspace, project, before["content_fingerprint"], invalid, reference),
        ).response
        assert response["outcome"] == "rejected"
        assert fact_path.read_bytes() == raw

    migrated_target["creation_reviews"] = migrated_target["creation_reviews"][1:]
    migrated_target["result_reviews"] = migrated_target["result_reviews"][1:]
    migrated_target["validation_summary"] = "The current result satisfies the same criterion; wording corrected"
    migrated_target["disposition_summary"] = "No current residual responsibility remains"
    migrated_target["closure_approval"]["summary"] = "Human approved the same completed result"
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], migrated_target, reference),
    ).response

    assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
    after = _read(workspace, project, reference)["fact_object"]
    assert (after["status"], after["phase"], after["closure_outcome"]) == ("closed", "closed", "completed")
    assert after["plan_version"] == before["fact_object"]["plan_version"]
    assert after["result_version"] == before["fact_object"]["result_version"]
    assert after["execution_approval"]["subject_version"] == 1
    assert after["execution_approval"]["approved_at"] == "2026-07-20T08:35:00+08:00"
    assert after["closure_approval"]["subject_version"] == 1
    assert after["closure_approval"]["approved_at"] == "2026-07-20T08:55:00+08:00"
    assert [review["reviewer"] for review in after["creation_reviews"]] == ["independent-plan-reviewer-b"]
    assert [review["reviewer"] for review in after["result_reviews"]] == ["independent-result-reviewer-b"]
    for field_name in (
        "audit_summary",
        "progress_history",
        "improvement_observations",
        "nonbinding_followups",
    ):
        assert field_name not in after
    assert all("review_basis" not in review for review in after["creation_reviews"])
    assert all("review_basis" not in review for review in after["result_reviews"])


def test_workcase_delta_profiles_preserve_result_and_carrier_with_frozen_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    diagnostic_workspace = tmp_path / "diagnostic-workspace"
    shutil.copytree(workspace, diagnostic_workspace)
    diagnostic_project = diagnostic_workspace / "project"
    config_path = diagnostic_workspace / "LDVH-GOVERNED-PROJECTS.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(str(project), str(diagnostic_project)),
        encoding="utf-8",
    )

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromisoformat("2027-07-20T18:00:00+08:00")

    monkeypatch.setattr("ldvh.helper.service.datetime", FrozenDateTime)
    compact_before = _read(workspace, project, workcase_ref)
    diagnostic_before = _read(diagnostic_workspace, diagnostic_project, workcase_ref)
    assert compact_before["content_fingerprint"] == diagnostic_before["content_fingerprint"]
    compact = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            compact_before["content_fingerprint"],
            set_fields={"summary": "Profile-equivalent controlled update"},
            response_profile="compact",
        ),
    ).response
    diagnostic = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            diagnostic_workspace,
            diagnostic_project,
            workcase_ref,
            diagnostic_before["content_fingerprint"],
            set_fields={"summary": "Profile-equivalent controlled update"},
            response_profile="diagnostic",
        ),
    ).response

    assert compact["outcome"] == diagnostic["outcome"] == "ok"
    assert compact["result"] == diagnostic["result"]
    assert compact["changes"][0]["summary"] == diagnostic["changes"][0]["summary"]
    assert compact["changes"][0]["status"] == diagnostic["changes"][0]["status"]
    assert compact["changes"][0]["target"] == diagnostic["changes"][0]["target"]
    compact_path = project / compact["result"]["canonical_path"]
    diagnostic_path = diagnostic_project / diagnostic["result"]["canonical_path"]
    assert compact_path.read_bytes() == diagnostic_path.read_bytes()
    assert len(json.dumps(compact["result"], ensure_ascii=False, separators=(",", ":")).encode()) <= 4096


def test_workcase_success_result_with_sixteen_receipts_stays_within_contract_limit() -> None:
    before_fields = {
        "status": "open",
        "phase": "independent_reviewing",
        "plan_version": 1,
        "result_version": 1,
    }
    after_fields = {**before_fields, "updated_at": "2026-07-20T18:00:00+08:00", "result_reviews": []}
    before = FactReadResult(
        "ldvh-base/workcases/workcase-0001.yaml",
        "yaml",
        "mechanically_valid",
        before_fields,
        None,
        (),
        content_fingerprint="b" * 64,
        raw_text="before\n",
    )
    after = FactReadResult(
        "ldvh-base/workcases/workcase-0001.yaml",
        "yaml",
        "mechanically_valid",
        after_fields,
        None,
        (),
        content_fingerprint="c" * 64,
        raw_text="after\n",
    )
    receipts = tuple(
        {
            "action": "result_review_appended",
            "subject_version": 1,
            "review_index": index,
        }
        for index in range(16)
    )

    result = workcase_update_operation._result(
        before,
        after,
        "sample",
        "workcase-0001",
        event_at="2026-07-20T18:00:00+08:00",
        receipts=receipts,
    )

    assert len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode()) <= 4096


def test_update_replaces_full_target_and_preserves_managed_identity(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    before_fields = dict(before["fact_object"])
    target = _mutable(before)
    target["summary"] = "After update"
    fact.chmod(0o640)

    result = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    )
    response = result.response

    assert result.exit_code == 0
    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["result"]["previous_content_fingerprint"] == before["content_fingerprint"]
    assert response["result"]["content_fingerprint"] != before["content_fingerprint"]
    after_fields = response["result"]["fact_object"]
    assert after_fields["summary"] == "After update"
    assert after_fields["object_id"] == before_fields["object_id"]
    assert after_fields["fact_type_key"] == before_fields["fact_type_key"]
    assert after_fields["created_at"] == before_fields["created_at"]
    assert after_fields["updated_at"] != before_fields["updated_at"]
    working_tree_source = next(source for source in response["sources"] if source["kind"] == "working_tree")
    assert working_tree_source["observed_at"] == after_fields["updated_at"]
    assert fact.stat().st_mode & 0o777 == 0o640
    assert response["changes"][0]["status"] == "updated"


def test_update_repairs_a_parseable_invalid_snapshot_with_its_read_fingerprint(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Exact update
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: routed
summary: Before update
disposition_summary: Incorrectly recorded as routed without a fact target.
""",
        encoding="utf-8",
    )
    read = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "fact_refs": [_ref()],
                },
            }
        ),
    ).response
    item = read["result"]["items"][0]

    assert item["check_status"] == "invalid"
    assert item["content_fingerprint"] is not None
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            item["content_fingerprint"],
            {
                "title": "Exact update",
                "status": "implemented",
                "summary": "Before update",
                "disposition_summary": (
                    "The bounded Spark content was directly implemented with no residual fact responsibility."
                ),
            },
        ),
    ).response

    assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
    assert response["result"]["fact_object"]["status"] == "implemented"


def test_no_change_does_not_rewrite_or_change_timestamp(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    raw = fact.read_bytes()
    stat_before = fact.stat()

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], _mutable(before)),
    ).response

    assert response["outcome"] == "no_change"
    assert response["changes"] == []
    assert response["result"]["previous_content_fingerprint"] == response["result"]["content_fingerprint"]
    assert fact.read_bytes() == raw
    assert fact.stat().st_ino == stat_before.st_ino
    assert response["result"]["fact_object"]["updated_at"] == "2026-07-14T10:00:00+08:00"


def test_stale_fingerprint_rejects_without_writing(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Requested update"
    fact.write_text(fact.read_text(encoding="utf-8").replace("Before update", "Manual change"), encoding="utf-8")
    manually_changed = fact.read_bytes()

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "rejected"
    assert "指纹" in response["summary"]
    assert response["changes"] == []
    assert fact.read_bytes() == manually_changed


def test_capability_check_never_mutates_target(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Would change on call"
    raw = fact.read_bytes()

    response = handle_request(
        "capabilities",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["operations"][0]["availability"] == "available_for_request"
    assert fact.read_bytes() == raw


def test_failed_write_back_read_rolls_back_only_matching_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    original = fact.read_bytes()
    target = _mutable(before)
    target["summary"] = "This replacement will fail its simulated readback"
    actual_project_read = update_application._project_read
    calls = 0

    def failing_readback(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            return FactReadResult(
                "ldvh-base/sparks/spark-0001.yaml",
                "yaml",
                "invalid",
                None,
                None,
                (FactIssue("schema", "simulated write-back failure"),),
            )
        return actual_project_read(*args, **kwargs)

    monkeypatch.setattr(update_application, "_project_read", failing_readback)
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "error"
    assert response["changes"][0]["status"] == "rolled-back"
    assert fact.read_bytes() == original


def test_concurrent_updates_with_one_fingerprint_have_one_winner(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    before = _read(workspace, project)
    targets: list[dict[str, object]] = []
    for summary in ("First contender", "Second contender"):
        target = _mutable(before)
        target["summary"] = summary
        targets.append(target)
    payloads = [_update_payload(workspace, project, before["content_fingerprint"], target) for target in targets]

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = tuple(
            executor.map(
                lambda payload: handle_request("call", "update-fact-object", payload).response,
                payloads,
            )
        )

    assert sorted(response["outcome"] for response in responses) == ["ok", "rejected"]
    final = _read(workspace, project)
    assert final["fact_object"]["summary"] in {"First contender", "Second contender"}


def test_update_reports_committed_namespace_when_directory_sync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Committed despite directory sync failure"
    real_fsync = os.fsync
    target_directory = fact.parent

    def fail_directory_sync(descriptor: int) -> None:
        observation = os.fstat(descriptor)
        if stat.S_ISDIR(observation.st_mode) and (observation.st_dev, observation.st_ino) == (
            target_directory.stat().st_dev,
            target_directory.stat().st_ino,
        ):
            raise OSError("directory sync failed")
        real_fsync(descriptor)

    monkeypatch.setattr("ldvh.filesystem.os.fsync", fail_directory_sync)
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "ok"
    assert response["changes"][0]["status"] == "updated"
    assert "durability=unknown" in response["changes"][0]["summary"]
    assert "Committed despite directory sync failure" in fact.read_text(encoding="utf-8")


def test_update_fails_before_lock_or_file_mutation_when_platform_durability_is_not_approved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Must not be written"
    original = fact.read_bytes()
    monkeypatch.setattr(fact_update_operation, "durable_writes_enabled", lambda: False)

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "unavailable"
    assert "file-only" in response["summary"]
    assert not (project / ".git/ldvh").exists()
    assert fact.read_bytes() == original


def test_coordination_permission_failure_is_structured_unavailable_with_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Must remain unwritten"
    original = fact.read_bytes()

    def unavailable(*args, **kwargs):
        raise FactCoordinationUnavailable("permission_denied")

    monkeypatch.setattr(fact_update_operation, "apply_fact_update", unavailable)
    response = handle_request(
        "call",
        "update-fact-object",
        json.dumps(
            {
                "response_profile": "diagnostic",
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "fact_ref": _ref(),
                    "expected_content_fingerprint": before["content_fingerprint"],
                    "fact_object": target,
                },
            }
        ),
    ).response

    assert response["outcome"] == "unavailable"
    assert response["changes"] == []
    assert response["gaps"][0]["code"] == "controlled_write_lock_unavailable"
    assert response["diagnostics"][0]["code"] == "controlled_write_lock_unavailable"
    assert response["diagnostics"][0]["details"] == {
        "stage": "common_dir_lock",
        "path_role": "git_common_dir_ldvh_coordination_root",
        "required_access": "create_or_open_and_exclusively_lock",
        "system_error_category": "permission_denied",
        "target_unchanged": True,
        "allocator_unchanged": True,
        "counter_unchanged": True,
    }
    assert fact.read_bytes() == original


def test_independent_process_updates_with_one_fingerprint_have_one_winner(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    before = _read(workspace, project)
    payloads: list[str] = []
    for summary in ("First process", "Second process"):
        target = _mutable(before)
        target["summary"] = summary
        payloads.append(_update_payload(workspace, project, before["content_fingerprint"], target))

    def run(payload: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(HELPER_EXECUTABLE), "call", "update-fact-object"],
            cwd=project,
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        completed = tuple(executor.map(run, payloads))

    assert all(item.stderr == "" for item in completed)
    assert sorted(json.loads(item.stdout)["outcome"] for item in completed) == ["ok", "rejected"]
    final = _read(workspace, project)
    assert final["fact_object"]["summary"] in {"First process", "Second process"}


def test_update_rejects_managed_fields_and_terminal_reopen(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    managed = _mutable(before)
    managed["object_id"] = "spark-9999"

    invalid_request = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], managed),
    ).response
    assert invalid_request["outcome"] == "invalid_request"

    terminal = _mutable(before)
    terminal["status"] = "discarded"
    terminal["disposition_summary"] = "Human chose to stop tracking this Spark"
    terminal.pop("priority")
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], terminal),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["fact_object"]["status"] == "discarded"
    terminal_read = _read(workspace, project)
    reopen = _mutable(terminal_read)
    reopen["status"] = "open"
    for key in ("disposition_summary",):
        reopen.pop(key)
    reopen["priority"] = "P2"
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, terminal_read["content_fingerprint"], reopen),
    ).response

    assert rejected["outcome"] == "rejected"
    assert "status 转换" in rejected["gaps"][0]["summary"]
    assert fact.is_file()


def test_study_update_preserves_submitted_body_boundary(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "question.md").write_text("question\n", encoding="utf-8")
    (docs / "evidence.md").write_text("evidence\n", encoding="utf-8")
    prepare = handle_request(
        "call",
        "prepare-fact-object-draft",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    "fact_type_key": "study",
                },
            }
        ),
    ).response["result"]
    study = {
        "frontmatter": {
            "title": "Study update",
            "status": "active",
            "urls": [
                {
                    "ref": "https://example.invalid/study-update",
                    "title": "Study update evidence",
                    "summary": "External material used by the test Study.",
                }
            ],
            "research_question": "Does update preserve the submitted Markdown body boundary?",
            "abstract": "The full target body remains stable across serialization.",
            "research_intent": (
                "Confirm that a controlled update retains the project reason for this external research."
            ),
            "recommendation_summary": "Use the complete target boundary when updating a Study report.",
        },
        "body": """
## 研究问题

### 项目问题

验证 Study 更新。

### 外部问题

外部资料如何限定完整目标更新？

## 输入与边界

### 已读外部资料

读取外部研究资料并限定当前问题。

### 本次边界

不把序列化行为当作研究结论。

## 关键发现

### 完整目标

完整目标不会积累空行，启发是保持一次完整替换；不等于任意内容均可更新。

### 载体边界

提交正文会被保留，启发是避免隐式改写；不证明外部资料当前。

## 建议

### 可立即采用的工作方式

保持完整目标语义。

## 后续分流

| 分流类别 | 触发条件 | 下一步或不创建理由 |
|---|---|---|
| 无需对象化 | 仅验证更新路径 | 不创建额外对象。 |
""",
    }
    created = handle_request(
        "call",
        "create-fact-object",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "draft_basis": {
                        key: prepare[key]
                        for key in (
                            "governed_project_id",
                            "fact_type_key",
                            "candidate_object_id",
                            "schema_fingerprint",
                            "worktree_fingerprint",
                        )
                    },
                    "fact_object": study,
                },
            }
        ),
    ).response
    assert created["outcome"] == "ok", json.dumps(created, ensure_ascii=False, indent=2)
    reference = created["result"]["actual_ref"]
    read = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {"workspace_root": str(workspace), "fact_refs": [reference]},
            }
        ),
    ).response["result"]["items"][0]
    target = {
        "frontmatter": dict(read["fact_object"]["frontmatter"]),
        "body": read["fact_object"]["body"].replace(
            "完整目标不会积累空行，启发是保持一次完整替换；不等于任意内容均可更新。",
            "更新后的正文不会积累空行，启发是保持一次完整替换；不等于任意内容均可更新。",
        ),
    }
    for key in ("object_id", "fact_type_key", "created_at", "updated_at"):
        target["frontmatter"].pop(key)

    updated = handle_request(
        "call",
        "update-fact-object",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "fact_ref": reference,
                    "expected_content_fingerprint": read["content_fingerprint"],
                    "fact_object": target,
                },
            }
        ),
    ).response

    assert updated["outcome"] == "ok"
    assert updated["result"]["fact_object"]["body"] == target["body"]
