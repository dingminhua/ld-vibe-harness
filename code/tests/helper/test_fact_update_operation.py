from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest
from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.facts import update_application
from ldvh.facts.creation import FactCoordinationUnavailable
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
    assert item["check_status"] == "mechanically_valid"
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
        "workcase_profile": "control-contract-v1",
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
        "audit_summary": [
            {
                "audit_id": "audit-01",
                "subject_kind": "pre_creation_plan",
                "subject_version": 1,
                "review_count": 1,
                "summary": "Independent review improved and confirmed the initial plan",
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
            "review_basis": {
                "projection_key": "plan_current",
                "subject_fingerprint": workcase_subject_fingerprint(fact_object, "plan_current"),
            },
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


def test_current_workcase_progress_rejects_generic_full_object_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    (docs / "evidence.md").write_text("Verified result\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)

    def update(mutator) -> dict[str, object]:
        before = _read(workspace, project, workcase_ref)
        target = _mutable(before)
        mutator(target)
        response = handle_request(
            "call",
            "update-fact-object",
            _update_payload(
                workspace,
                project,
                before["content_fingerprint"],
                target,
                workcase_ref,
            ),
        ).response
        return response

    event_at = "2027-01-01T12:00:00+08:00"

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = cls.fromisoformat(event_at)
            return value if tz is None else value.astimezone(tz)

    monkeypatch.setattr("ldvh.helper.service.datetime", FrozenDateTime)

    def approve_execution(fields: dict[str, object]) -> None:
        fields.update(
            {
                "phase": "executing",
                "summary": "Human approved the current plan; execution started",
                "resume_from": "Complete item-01",
                "execution_approval": {
                    "subject_version": 1,
                    "approved_at": event_at,
                    "summary": "Human approved the presented current plan",
                },
                "progress_history": {
                    "coverage": "full",
                    "entries": [
                        {
                            "event_id": "progress-001",
                            "plan_version": 1,
                            "round": 1,
                            "phase": "executing",
                            "entered_at": event_at,
                            "transition_kind": "started",
                            "transition_summary": "Begin the approved current plan",
                        }
                    ],
                },
            }
        )
        fields.pop("waiting_on")
        fields["work_items"][0].update(
            {
                "status": "in_progress",
                "current_summary": "Producing the bounded result",
                "resume_from": "Finish and verify the result",
            }
        )

    approve_response = update(approve_execution)
    assert approve_response["outcome"] == "rejected"
    assert any("只能由 update-workcase 托管追加" in gap["summary"] for gap in approve_response["gaps"])


def test_generic_full_snapshot_can_update_non_progress_content_without_changing_history(tmp_path: Path) -> None:
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
            managed_records={
                "execution_approval": {"summary": "Human approved plan version 1"},
                "progress_transition": {"summary": "Begin the approved current plan"},
            },
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
    assert after["progress_history"] == current["fact_object"]["progress_history"]


def test_workcase_delta_records_same_phase_repetition_as_a_new_round(tmp_path: Path) -> None:
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
            managed_records={
                "execution_approval": {"summary": "Human approved plan version 1"},
                "progress_transition": {"summary": "Begin the approved current plan"},
            },
        ),
    ).response
    assert approved["outcome"] == "ok"

    current = _read(workspace, project, workcase_ref)
    repeated = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            current["content_fingerprint"],
            set_fields={"summary": "Controller began another execution iteration"},
            managed_records={
                "progress_transition": {"summary": "Repeat execution after reviewing the current result"}
            },
        ),
    ).response

    assert repeated["outcome"] == "ok", json.dumps(repeated, ensure_ascii=False, indent=2)
    history = _read(workspace, project, workcase_ref)["fact_object"]["progress_history"]
    assert len(history["entries"]) == 2
    assert history["entries"][-1]["event_id"] == "progress-002"
    assert history["entries"][-1]["round"] == 2
    assert history["entries"][-1]["phase"] == "executing"
    assert history["entries"][-1]["transition_kind"] == "repeated"


def test_workcase_delta_records_execution_approval_with_one_event_and_idempotent_retry(tmp_path: Path) -> None:
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
        managed_records={
            "execution_approval": {"summary": "Human approved plan version 1"},
            "progress_transition": {"summary": "Begin the approved current plan"},
        },
    )

    response = handle_request("call", "update-workcase", payload).response

    assert_common_response(response)
    assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
    assert response["result"]["before_state"]["phase"] == "human_plan_confirming"
    assert response["result"]["after_state"]["phase"] == "executing"
    assert response["result"]["managed_record_receipts"] == [
        {"action": "execution_approval_recorded", "subject_version": 1},
        {
            "action": "progress_recorded",
            "subject_version": 1,
            "progress_event_id": "progress-001",
            "progress_round": 1,
            "progress_phase": "executing",
            "transition_kind": "started",
        },
    ]
    assert response["result"]["event_at"] is not None
    current = _read(workspace, project, workcase_ref)
    fields = current["fact_object"]
    assert fields["updated_at"] == response["result"]["event_at"]
    assert fields["execution_approval"]["approved_at"] == response["result"]["event_at"]
    assert fields["progress_history"]["entries"][0]["entered_at"] == response["result"]["event_at"]
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


def test_generic_full_snapshot_can_correct_progress_content_but_not_event_identity(tmp_path: Path) -> None:
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
            managed_records={
                "execution_approval": {"summary": "Human approved plan version 1"},
                "progress_transition": {"summary": "Initial description that requires correction"},
            },
        ),
    ).response
    assert approved["outcome"] == "ok"

    current = _read(workspace, project, workcase_ref)
    corrected = _mutable(current)
    corrected["progress_history"]["entries"][0]["transition_summary"] = (
        "Corrected factual description without inventing another progress round"
    )
    correction = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            current["content_fingerprint"],
            corrected,
            workcase_ref,
        ),
    ).response
    assert correction["outcome"] == "ok", json.dumps(correction, ensure_ascii=False, indent=2)
    corrected_read = _read(workspace, project, workcase_ref)
    corrected_entry = corrected_read["fact_object"]["progress_history"]["entries"][0]
    assert corrected_entry["event_id"] == "progress-001"
    assert corrected_entry["transition_summary"].startswith("Corrected factual description")

    rewritten = _mutable(corrected_read)
    rewritten["progress_history"]["entries"][0]["event_id"] = "progress-002"
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            corrected_read["content_fingerprint"],
            rewritten,
            workcase_ref,
        ),
    ).response
    assert rejected["outcome"] == "rejected"
    assert any("progress_history" in gap["summary"] for gap in rejected["gaps"])

    fact_path = project / corrected_read["canonical_path"]
    fact_path.write_text(
        fact_path.read_text(encoding="utf-8").replace(
            "transition_kind: started",
            "transition_kind: advanced",
            1,
        ),
        encoding="utf-8",
    )
    invalid_read = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {"workspace_root": str(workspace), "fact_refs": [workcase_ref]},
            }
        ),
    ).response["result"]["items"][0]
    assert invalid_read["check_status"] == "invalid"
    repaired = _mutable(invalid_read)
    repaired["progress_history"]["entries"][0]["transition_kind"] = "started"
    repaired_response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            invalid_read["content_fingerprint"],
            repaired,
            workcase_ref,
        ),
    ).response
    assert repaired_response["outcome"] == "ok", json.dumps(repaired_response, ensure_ascii=False, indent=2)


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
            managed_records={
                "execution_approval": {"summary": "Human approved plan version 1"},
                "progress_transition": {"summary": "Begin the recorded execution"},
            },
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
        managed_records={
            "execution_approval": {"summary": "Human approved the presented current plan"},
            "progress_transition": {"summary": "Begin the approved current plan"},
        },
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
        managed_records={"progress_transition": {"summary": "Enter Controller self-check"}},
    )
    update(
        set_fields={
            "phase": "independent_reviewing",
            "summary": "Independent result review is in progress",
            "resume_from": "Obtain review feedback and let Controller decide the next phase",
        },
        managed_records={"progress_transition": {"summary": "Enter independent result review"}},
    )
    reviewed = update(
        managed_records={
            "append_result_reviews": [
                {
                    "reviewer": "independent-result-reviewer",
                    "scope": "Item result, success criterion, Controller check, validation, and residual risk",
                    "conclusion": "blocked",
                    "feedback": ["The reviewer would prefer another validation statement"],
                    "projection_key": "result_implementation",
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
            "progress_transition": {"summary": "Return to Controller self-check after review"},
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
        managed_records={"progress_transition": {"summary": "Enter Controller convergence"}},
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
            managed_records={
                "execution_approval": {"summary": "Human approved plan version 1"},
                "progress_transition": {"summary": "Begin the approved current plan"},
            },
        ),
    ).response
    assert approved["outcome"] == "ok"
    current = _read(workspace, project, workcase_ref)
    fields = current["fact_object"]
    audit_summary = [
        *fields["audit_summary"],
        {
            "audit_id": "audit-02",
            "subject_kind": "superseded_plan",
            "subject_version": 1,
            "review_count": 1,
            "summary": "The prior review value was consumed by the revised plan",
        },
    ]

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
                "audit_summary": audit_summary,
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


def test_new_workcase_plan_v2_first_execution_writes_full_history(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "input.md").write_text("Human-authorized work\n", encoding="utf-8")
    workcase_ref = _create_workcase(workspace, project)
    before = _read(workspace, project, workcase_ref)
    fields = before["fact_object"]
    audit_summary = [
        *fields["audit_summary"],
        {
            "audit_id": "audit-02",
            "subject_kind": "superseded_plan",
            "subject_version": 1,
            "review_count": 1,
            "summary": "The unexecuted first plan review was consumed by plan version 2",
        },
    ]
    bumped = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            before["content_fingerprint"],
            set_fields={
                "goal": "Exercise the revised plan before any execution",
                "phase": "human_plan_confirming",
                "plan_version": 2,
                "summary": "Revised unexecuted plan is ready for Human approval",
                "resume_from": "Request approval for plan version 2",
                "audit_summary": audit_summary,
            },
            managed_records={
                "replace_creation_reviews": [
                    {
                        "reviewer": "independent-plan-reviewer-v2",
                        "scope": "Revised goal before first execution",
                        "conclusion": "pass",
                        "feedback": ["The revised plan is coherent"],
                        "controller_resolution": "Accepted; plan version 2 is ready for Human approval.",
                    }
                ]
            },
        ),
    ).response
    assert bumped["outcome"] == "ok", json.dumps(bumped, ensure_ascii=False, indent=2)

    current = _read(workspace, project, workcase_ref)
    approved = handle_request(
        "call",
        "update-workcase",
        _workcase_update_payload(
            workspace,
            project,
            workcase_ref,
            current["content_fingerprint"],
            set_fields={
                "phase": "executing",
                "summary": "Human approved plan version 2; first execution begins",
                "resume_from": "Execute item-01",
            },
            remove_fields=["waiting_on"],
            managed_records={
                "execution_approval": {"summary": "Human approved plan version 2"},
                "progress_transition": {"summary": "Begin the first execution of this WorkCase"},
            },
        ),
    ).response
    assert approved["outcome"] == "ok", json.dumps(approved, ensure_ascii=False, indent=2)
    history = _read(workspace, project, workcase_ref)["fact_object"]["progress_history"]
    assert history["coverage"] == "full"
    assert history["entries"][0]["round"] == 1
    assert history["entries"][0]["transition_kind"] == "started"


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
            "projection_key": "result_implementation",
            "subject_fingerprint": "a" * 64,
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
