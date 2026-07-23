from __future__ import annotations

from ldvh.facts.workcase_projection import workcase_subject_fingerprint
from ldvh.facts.workcase_update import construct_workcase_update

EVENT_AT = "2026-07-20T16:00:00+08:00"


def _before() -> dict[str, object]:
    fields: dict[str, object] = {
        "object_id": "workcase-0006",
        "fact_type_key": "workcase",
        "created_at": "2026-07-20T14:00:00+08:00",
        "updated_at": "2026-07-20T15:00:00+08:00",
        "workcase_profile": "control-contract-v1",
        "status": "open",
        "phase": "controller_checking",
        "priority": "P1",
        "summary": "Controller checking",
        "resume_from": "Complete the check",
        "goal": "Ship one bounded change",
        "scope": "One module",
        "plan_version": 1,
        "result_version": 1,
        "success_criterion_definitions": [
            {"criterion_id": "criterion-01", "statement": "Tests pass"}
        ],
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Build",
                "expected_result": "Built",
                "status": "completed",
                "approach_summary": "Implement",
                "result_summary": "Built",
                "evidence_refs": [{"kind": "working_tree", "locator": "code/module.py"}],
            }
        ],
        "audit_summary": [
            {
                "audit_id": "audit-01",
                "subject_kind": "pre_creation_plan",
                "subject_version": 1,
                "review_count": 1,
                "summary": "Reviewed",
            }
        ],
        "creation_reviews": [],
        "execution_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-20T14:30:00+08:00",
            "summary": "Approved",
        },
    }
    return fields


def _result_review(conclusion: str = "changes_required") -> dict[str, object]:
    before = _before()
    return {
        "reviewer": "independent-reviewer",
        "reviewed_at": "2026-07-20T15:30:00+08:00",
        "subject_version": 1,
        "scope": "Implementation result",
        "conclusion": conclusion,
        "feedback": ["Controller should inspect one point"],
        "review_basis": {
            "projection_key": "result_implementation",
            "subject_fingerprint": workcase_subject_fingerprint(before, "result_implementation"),
        },
    }


def test_ordinary_delta_never_infers_lifecycle_from_review_conclusion() -> None:
    before = {**_before(), "phase": "independent_reviewing", "result_reviews": [_result_review("pass")]}

    construction = construct_workcase_update(
        before,
        set_fields={"summary": "Review received"},
        remove_fields=(),
        managed_records={},
        event_at=EVENT_AT,
    )

    assert construction.problems == ()
    assert construction.supplied is not None
    assert construction.supplied["phase"] == "independent_reviewing"
    assert construction.supplied["summary"] == "Review received"


def test_result_review_append_and_resolution_are_separate() -> None:
    before = {**_before(), "phase": "independent_reviewing"}
    submitted = {
        "reviewer": "independent-reviewer",
        "scope": "Implementation result",
        "conclusion": "changes_required",
        "feedback": ["Controller should inspect one point"],
        "projection_key": "result_implementation",
    }
    appended = construct_workcase_update(
        before,
        set_fields={},
        remove_fields=(),
        managed_records={"append_result_reviews": [submitted]},
        event_at=EVENT_AT,
    )

    assert appended.problems == ()
    assert appended.supplied is not None
    review = appended.supplied["result_reviews"][0]
    assert "controller_resolution" not in review
    assert review["reviewed_at"] == EVENT_AT
    assert appended.receipts[0]["action"] == "result_review_appended"

    resolved = construct_workcase_update(
        {**before, "result_reviews": appended.supplied["result_reviews"]},
        set_fields={},
        remove_fields=(),
        managed_records={
            "resolve_result_reviews": [
                {"review_index": 0, "controller_resolution": "Accepted and corrected."}
            ]
        },
        event_at=EVENT_AT,
    )
    assert resolved.supplied is not None
    assert resolved.supplied["result_reviews"][0]["controller_resolution"] == "Accepted and corrected."
    assert resolved.receipts == (
        {"action": "result_review_resolved", "subject_version": 1, "review_index": 0},
    )

    unchanged = construct_workcase_update(
        {**before, "result_reviews": resolved.supplied["result_reviews"]},
        set_fields={},
        remove_fields=(),
        managed_records={
            "resolve_result_reviews": [
                {"review_index": 0, "controller_resolution": "Accepted and corrected."}
            ]
        },
        event_at="2026-07-20T17:00:00+08:00",
    )
    assert unchanged.receipts == ()
    assert unchanged.supplied == resolved.supplied


def test_identical_result_review_inputs_remain_distinct_events_without_stable_identity() -> None:
    before = {**_before(), "phase": "independent_reviewing"}
    submitted = {
        "reviewer": "independent-reviewer",
        "scope": "Implementation result",
        "conclusion": "pass",
        "feedback": ["The current result is acceptable"],
        "projection_key": "result_implementation",
    }

    result = construct_workcase_update(
        before,
        set_fields={},
        remove_fields=(),
        managed_records={"append_result_reviews": [submitted, submitted]},
        event_at=EVENT_AT,
    )

    assert result.supplied is not None
    assert len(result.supplied["result_reviews"]) == 2
    assert [receipt["review_index"] for receipt in result.receipts] == [0, 1]


def test_review_append_rejects_same_request_subject_change() -> None:
    result = construct_workcase_update(
        {**_before(), "phase": "independent_reviewing"},
        set_fields={"controller_check_summary": "New subject content"},
        remove_fields=(),
        managed_records={
            "append_result_reviews": [
                {
                    "reviewer": "reviewer",
                    "scope": "Result",
                    "conclusion": "pass",
                    "feedback": ["Looks good"],
                    "projection_key": "result_implementation",
                }
            ]
        },
        event_at=EVENT_AT,
    )

    assert result.supplied is None
    assert "subject projection" in result.problems[0]


def test_result_version_increment_resets_only_result_reviews_and_closure_approval() -> None:
    review = _result_review()
    before = {
        **_before(),
        "result_reviews": [review],
        "closure_approval": {"subject_version": 1},
        "validation_summary": "Keep this Controller report",
    }
    before["audit_summary"] = [
        *before["audit_summary"],
        {
            "audit_id": "audit-02",
            "subject_kind": "superseded_result",
            "subject_version": 1,
            "review_count": 1,
            "summary": "Old review value retained",
        },
    ]

    result = construct_workcase_update(
        before,
        set_fields={"result_version": 2},
        remove_fields=(),
        managed_records={},
        event_at=EVENT_AT,
    )

    assert result.problems == ()
    assert result.supplied is not None
    assert "result_reviews" not in result.supplied
    assert "closure_approval" not in result.supplied
    assert result.supplied["validation_summary"] == "Keep this Controller report"


def test_execution_approval_is_version_bound_and_semantically_idempotent() -> None:
    before = _before()
    before.pop("execution_approval")
    approval = {"summary": "Human approved plan version 1"}
    formed = construct_workcase_update(
        before,
        set_fields={"phase": "executing"},
        remove_fields=(),
        managed_records={"execution_approval": approval},
        event_at=EVENT_AT,
    )
    assert formed.supplied is not None
    assert formed.supplied["execution_approval"]["approved_at"] == EVENT_AT
    assert formed.receipts == (
        {"action": "execution_approval_recorded", "subject_version": 1},
    )

    unchanged = construct_workcase_update(
        {**before, **formed.supplied},
        set_fields={},
        remove_fields=(),
        managed_records={"execution_approval": approval},
        event_at="2026-07-20T17:00:00+08:00",
    )
    assert unchanged.receipts == ()
    assert unchanged.supplied == formed.supplied


def test_execution_approval_withdrawal_restores_pending_plan_without_a_version_bump() -> None:
    before = _before()
    for field in (
        "result_version",
        "success_criterion_results",
        "controller_check_summary",
        "result_reviews",
        "improvement_observations",
        "residual_responsibilities",
        "nonbinding_followups",
        "closure_approval",
        "validation_summary",
        "closure_outcome",
        "disposition_summary",
    ):
        before.pop(field, None)
    before["phase"] = "executing"
    before["work_items"] = [
        {
            **before["work_items"][0],
            "status": "in_progress",
            "current_summary": "An approval was recorded before execution could begin.",
            "resume_from": "Wait for the actual Human decision.",
        }
    ]

    withdrawal = construct_workcase_update(
        before,
        set_fields={
            "phase": "human_plan_confirming",
            "work_items": [{**before["work_items"][0], "status": "pending"}],
            "summary": "The current plan is waiting for explicit Human approval.",
            "resume_from": "Present the current plan to Human.",
            "waiting_on": "Human execution approval for plan_version 1",
        },
        remove_fields=(),
        managed_records={
            "withdraw_execution_approval": {
                "summary": "Human clarified that the recorded execution approval was not granted."
            }
        },
        event_at=EVENT_AT,
    )

    assert withdrawal.problems == ()
    assert withdrawal.supplied is not None
    assert withdrawal.supplied["plan_version"] == 1
    assert withdrawal.supplied["phase"] == "human_plan_confirming"
    assert "execution_approval" not in withdrawal.supplied
    assert withdrawal.supplied["work_items"][0]["status"] == "pending"
    assert withdrawal.receipts == (
        {"action": "execution_approval_withdrawn", "subject_version": 1},
    )


def test_execution_approval_withdrawal_rejects_result_or_active_work() -> None:
    before = _before()
    before["phase"] = "executing"
    before["work_items"] = [
        {
            **before["work_items"][0],
            "status": "in_progress",
            "current_summary": "Already working.",
            "resume_from": "Continue.",
        }
    ]

    rejected = construct_workcase_update(
        before,
        set_fields={"phase": "human_plan_confirming", "work_items": before["work_items"]},
        remove_fields=(),
        managed_records={"withdraw_execution_approval": {"summary": "Retract."}},
        event_at=EVENT_AT,
    )

    assert rejected.supplied is None
    assert any("尚未形成结果包" in problem for problem in rejected.problems)
    assert any("恢复为 pending" in problem for problem in rejected.problems)


def test_closure_approval_requires_explicit_atomic_closed_snapshot() -> None:
    before = {
        **_before(),
        "phase": "human_closure_confirming",
        "waiting_on": "Human closure decision",
        "validation_summary": "Validated",
        "closure_outcome": "completed",
        "disposition_summary": "No residual work",
    }
    rejected = construct_workcase_update(
        before,
        set_fields={},
        remove_fields=(),
        managed_records={"closure_approval": {"summary": "Human approved closure"}},
        event_at=EVENT_AT,
    )
    assert rejected.supplied is None

    formed = construct_workcase_update(
        before,
        set_fields={"status": "closed", "phase": "closed"},
        remove_fields=("priority", "resume_from", "waiting_on"),
        managed_records={"closure_approval": {"summary": "Human approved closure"}},
        event_at=EVENT_AT,
    )
    assert formed.problems == ()
    assert formed.supplied is not None
    assert formed.supplied["closed_at"] == EVENT_AT
    assert formed.supplied["closure_approval"]["approved_at"] == EVENT_AT
    assert formed.receipts == (
        {"action": "closure_approval_recorded", "subject_version": 1},
    )
