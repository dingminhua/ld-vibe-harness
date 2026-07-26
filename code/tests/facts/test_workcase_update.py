from __future__ import annotations

from ldvh.facts.workcase_update import construct_workcase_update

EVENT_AT = "2026-07-26T16:00:00+08:00"


def _before() -> dict[str, object]:
    return {
        "object_id": "workcase-0006",
        "fact_type_key": "workcase",
        "created_at": "2026-07-26T13:00:00+08:00",
        "updated_at": "2026-07-26T15:00:00+08:00",
        "workcase_profile": "control-contract-v2",
        "status": "open",
        "phase": "controller_checking",
        "priority": "P1",
        "summary": "Controller checking",
        "goal": "Ship one bounded change",
        "scope": "One module",
        "plan_version": 1,
        "result_version": 1,
        "success_criterion_definitions": [{"criterion_id": "criterion-01", "statement": "Tests pass"}],
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Build",
                "expected_result": "Built",
                "status": "completed",
                "result_summary": "Built",
            }
        ],
        "creation_reviews": [],
        "controller_check_summary": "The implementation was checked.",
        "execution_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-26T14:30:00+08:00",
            "summary": "Approved",
        },
    }


def _result_review(conclusion: str = "changes_required") -> dict[str, object]:
    return {
        "reviewer": "independent-reviewer",
        "reviewed_at": "2026-07-26T15:30:00+08:00",
        "subject_version": 1,
        "scope": "Implementation result",
        "conclusion": conclusion,
        "feedback": ["Controller should inspect one point"],
        "controller_resolution": "Accepted and handled.",
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
    assert review == {
        "reviewer": "independent-reviewer",
        "reviewed_at": EVENT_AT,
        "subject_version": 1,
        "scope": "Implementation result",
        "conclusion": "changes_required",
        "feedback": ["Controller should inspect one point"],
    }
    assert appended.receipts == ({"action": "result_review_appended", "subject_version": 1, "review_index": 0},)

    resolved = construct_workcase_update(
        {**before, "result_reviews": appended.supplied["result_reviews"]},
        set_fields={},
        remove_fields=(),
        managed_records={
            "resolve_result_reviews": [{"review_index": 0, "controller_resolution": "Accepted and corrected."}]
        },
        event_at=EVENT_AT,
    )
    assert resolved.supplied is not None
    assert resolved.supplied["result_reviews"][0]["controller_resolution"] == "Accepted and corrected."
    assert resolved.receipts == ({"action": "result_review_resolved", "subject_version": 1, "review_index": 0},)

    unchanged = construct_workcase_update(
        {**before, "result_reviews": resolved.supplied["result_reviews"]},
        set_fields={},
        remove_fields=(),
        managed_records={
            "resolve_result_reviews": [{"review_index": 0, "controller_resolution": "Accepted and corrected."}]
        },
        event_at="2026-07-26T17:00:00+08:00",
    )
    assert unchanged.receipts == ()
    assert unchanged.supplied == resolved.supplied


def test_review_without_feedback_stores_only_the_core_review_fields() -> None:
    result = construct_workcase_update(
        {**_before(), "phase": "independent_reviewing"},
        set_fields={},
        remove_fields=(),
        managed_records={
            "append_result_reviews": [{"reviewer": "reviewer", "scope": "Current result", "conclusion": "pass"}]
        },
        event_at=EVENT_AT,
    )

    assert result.problems == ()
    assert result.supplied is not None
    review = result.supplied["result_reviews"][0]
    assert set(review) == {"reviewer", "reviewed_at", "subject_version", "scope", "conclusion"}

    rejected_resolution = construct_workcase_update(
        {**_before(), "phase": "independent_reviewing", "result_reviews": [review]},
        set_fields={},
        remove_fields=(),
        managed_records={
            "resolve_result_reviews": [{"review_index": 0, "controller_resolution": "Nothing to resolve"}]
        },
        event_at=EVENT_AT,
    )
    assert rejected_resolution.supplied is None
    assert rejected_resolution.problems == ("review_index 0 没有 feedback，不得形成 Controller 处置",)


def test_identical_result_review_inputs_remain_distinct_events_without_stable_identity() -> None:
    before = {**_before(), "phase": "independent_reviewing"}
    submitted = {
        "reviewer": "independent-reviewer",
        "scope": "Implementation result",
        "conclusion": "pass",
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


def test_review_append_rejects_subject_change_in_the_same_request() -> None:
    result = construct_workcase_update(
        {**_before(), "phase": "independent_reviewing"},
        set_fields={"controller_check_summary": "New subject content"},
        remove_fields=(),
        managed_records={"append_result_reviews": [{"reviewer": "reviewer", "scope": "Result", "conclusion": "pass"}]},
        event_at=EVENT_AT,
    )

    assert result.supplied is None
    assert any("不得变更被审结果主体" in problem for problem in result.problems)


def test_review_append_may_update_only_review_context_in_the_same_request() -> None:
    result = construct_workcase_update(
        {**_before(), "phase": "independent_reviewing", "blocking_summary": "Old blocker"},
        set_fields={"summary": "Independent review completed", "phase": "controller_checking"},
        remove_fields=("blocking_summary",),
        managed_records={"append_result_reviews": [{"reviewer": "reviewer", "scope": "Result", "conclusion": "pass"}]},
        event_at=EVENT_AT,
    )

    assert result.problems == ()
    assert result.supplied is not None
    assert result.supplied["summary"] == "Independent review completed"
    assert "blocking_summary" not in result.supplied
    assert result.supplied["result_reviews"][0]["reviewed_at"] == EVENT_AT


def test_result_version_increment_resets_only_result_reviews_and_closure_approval() -> None:
    before = {
        **_before(),
        "result_reviews": [_result_review()],
        "closure_approval": {"subject_version": 1},
        "validation_summary": "Keep this Controller report",
    }

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


def test_plan_increment_resets_old_approval_and_result_without_audit_receipts() -> None:
    before = {**_before(), "result_reviews": [_result_review()]}
    replacement = {"reviewer": "plan-reviewer", "scope": "Current plan", "conclusion": "pass"}

    result = construct_workcase_update(
        before,
        set_fields={"goal": "Ship the revised bounded change", "plan_version": 2, "phase": "human_plan_confirming"},
        remove_fields=(),
        managed_records={"replace_creation_reviews": [replacement]},
        event_at=EVENT_AT,
    )

    assert result.problems == ()
    assert result.supplied is not None
    assert "execution_approval" not in result.supplied
    assert "result_version" not in result.supplied
    assert "result_reviews" not in result.supplied
    assert "audit_summary" not in result.supplied
    assert result.supplied["creation_reviews"][0] == {
        "reviewer": "plan-reviewer",
        "reviewed_at": EVENT_AT,
        "subject_version": 2,
        "scope": "Current plan",
        "conclusion": "pass",
    }
    assert result.receipts == ({"action": "creation_review_replaced", "subject_version": 2, "review_index": 0},)


def test_execution_approval_is_version_bound_idempotent_and_needs_no_progress_event() -> None:
    before = _before()
    for field in ("execution_approval", "result_version", "controller_check_summary"):
        before.pop(field)
    before.update(
        {
            "phase": "human_plan_confirming",
            "waiting_on": "Human execution approval",
            "work_items": [
                {
                    "item_id": "item-01",
                    "goal": "Build",
                    "expected_result": "Built",
                    "status": "pending",
                }
            ],
        }
    )
    approval = {
        "summary": "Human approved plan version 1",
        "source_refs": [{"kind": "human-input", "locator": "turn-1"}],
    }
    formed = construct_workcase_update(
        before,
        set_fields={"phase": "executing"},
        remove_fields=("waiting_on",),
        managed_records={"execution_approval": approval},
        event_at=EVENT_AT,
    )

    assert formed.problems == ()
    assert formed.supplied is not None
    assert formed.supplied["execution_approval"]["approved_at"] == EVENT_AT
    assert "progress_history" not in formed.supplied
    assert formed.receipts == ({"action": "execution_approval_recorded", "subject_version": 1},)

    persisted = {**before, **formed.supplied}
    persisted.pop("waiting_on", None)
    unchanged = construct_workcase_update(
        persisted,
        set_fields={},
        remove_fields=(),
        managed_records={"execution_approval": approval},
        event_at="2026-07-26T17:00:00+08:00",
    )
    assert unchanged.receipts == ()
    assert unchanged.supplied == formed.supplied

    rewritten = construct_workcase_update(
        persisted,
        set_fields={},
        remove_fields=(),
        managed_records={
            "execution_approval": {
                "summary": "A different approval statement",
                "source_refs": approval["source_refs"],
            }
        },
        event_at="2026-07-26T17:00:00+08:00",
    )
    assert rewritten.supplied is None
    assert rewritten.problems == ("既有执行批准不得由 update-workcase 改写；获授权的同事件修正须使用通用事实修正",)


def test_execution_approval_withdrawal_restores_pending_plan_without_a_version_bump() -> None:
    before = _before()
    for field in ("result_version", "controller_check_summary"):
        before.pop(field)
    before.update(
        {
            "phase": "executing",
            "work_items": [
                {
                    "item_id": "item-01",
                    "goal": "Build",
                    "expected_result": "Built",
                    "status": "pending",
                }
            ],
        }
    )

    withdrawal = construct_workcase_update(
        before,
        set_fields={
            "phase": "human_plan_confirming",
            "work_items": before["work_items"],
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
    assert withdrawal.receipts == ({"action": "execution_approval_withdrawn", "subject_version": 1},)


def test_execution_approval_withdrawal_rejects_result_or_active_work() -> None:
    before = {**_before(), "phase": "executing"}
    before["work_items"] = [
        {
            "item_id": "item-01",
            "goal": "Build",
            "expected_result": "Built",
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
        "result_reviews": [_result_review("pass")],
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
        remove_fields=("priority", "waiting_on"),
        managed_records={"closure_approval": {"summary": "Human approved closure"}},
        event_at=EVENT_AT,
    )
    assert formed.problems == ()
    assert formed.supplied is not None
    assert formed.supplied["closure_approval"]["approved_at"] == EVENT_AT
    assert formed.receipts == ({"action": "closure_approval_recorded", "subject_version": 1},)

    persisted = {**before, **formed.supplied}
    for key in ("priority", "waiting_on"):
        persisted.pop(key, None)
    retry = construct_workcase_update(
        persisted,
        set_fields={"status": "closed", "phase": "closed"},
        remove_fields=(),
        managed_records={"closure_approval": {"summary": "Human approved closure"}},
        event_at="2026-07-26T17:00:00+08:00",
    )
    assert retry.problems == ()
    assert retry.receipts == ()
    assert retry.supplied == formed.supplied

    rewritten = construct_workcase_update(
        persisted,
        set_fields={"status": "closed", "phase": "closed"},
        remove_fields=(),
        managed_records={"closure_approval": {"summary": "A different closure statement"}},
        event_at="2026-07-26T17:00:00+08:00",
    )
    assert rewritten.supplied is None
    assert rewritten.problems == ("既有关闭批准不得由 update-workcase 改写；获授权的同事件修正须使用通用事实修正",)


def test_update_constructor_rejects_v1_even_when_the_delta_is_otherwise_ordinary() -> None:
    before = {**_before(), "workcase_profile": "control-contract-v1"}

    result = construct_workcase_update(
        before,
        set_fields={"summary": "Attempted legacy update"},
        remove_fields=(),
        managed_records={},
        event_at=EVENT_AT,
    )

    assert result.supplied is None
    assert result.problems == ("对象不是 control-contract-v2 WorkCase",)
