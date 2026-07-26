from __future__ import annotations

from copy import deepcopy

from ldvh.facts.transitions import validate_fact_transition


def _workcase() -> dict[str, object]:
    return {
        "status": "open",
        "phase": "executing",
        "plan_version": 1,
        "goal": "Deliver one result",
        "scope": "One bounded object",
        "success_criteria": ["The result is verified"],
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Produce the result",
                "expected_result": "One verified result",
                "status": "in_progress",
                "approach_summary": "Use the bounded implementation path",
            },
        ],
        "creation_reviews": [{"subject_version": 1}],
        "execution_approval": {"subject_version": 1},
    }


def _review(conclusion: str = "changes_required") -> dict[str, object]:
    return {
        "reviewer": "independent-result-reviewer",
        "reviewed_at": "2026-07-14T10:30:00+08:00",
        "subject_version": 1,
        "scope": "Result, validation, residual risk, and success criteria",
        "conclusion": conclusion,
        "feedback": ["One issue needs Controller disposition"],
        "controller_resolution": "1. Accepted for Controller handling.",
    }


def _reviewing() -> dict[str, object]:
    return {
        **_workcase(),
        "phase": "independent_reviewing",
        "result_version": 1,
        "controller_check_summary": "Initial Controller check",
        "result_reviews": [_review()],
    }


def _v2_workcase() -> dict[str, object]:
    fields = {
        **_workcase(),
        "workcase_profile": "control-contract-v2",
        "success_criterion_definitions": [{"criterion_id": "criterion-01", "statement": "The result is verified"}],
    }
    fields.pop("success_criteria")
    return fields


def test_workcase_plan_change_requires_version_bump_and_reset() -> None:
    before = _workcase()
    unchanged_version = {**before, "goal": "A materially different result"}

    issues = validate_fact_transition("workcase", before, unchanged_version)

    assert any(issue.field_path == "plan_version" and "必须递增" in issue.summary for issue in issues)

    valid_reset = {
        **before,
        "goal": "A materially different result",
        "phase": "human_plan_confirming",
        "plan_version": 2,
        "creation_reviews": [{"subject_version": 2}],
    }
    valid_reset.pop("execution_approval")
    assert validate_fact_transition("workcase", before, valid_reset) == ()


def test_workcase_version_bump_cannot_reuse_old_approval_or_result_package() -> None:
    before = _workcase()
    after = {
        **before,
        "goal": "Changed result",
        "phase": "human_plan_confirming",
        "plan_version": 2,
        "result_version": 1,
    }

    issues = validate_fact_transition("workcase", before, after)

    assert any(issue.field_path == "execution_approval" for issue in issues)
    assert any(issue.field_path == "result_version" for issue in issues)


def test_v2_plan_projection_ignores_declared_nonsemantic_collection_order() -> None:
    before = _v2_workcase()
    before["success_criterion_definitions"] = [
        {"criterion_id": "criterion-01", "statement": "First result"},
        {"criterion_id": "criterion-02", "statement": "Second result"},
    ]
    before["work_items"] = [
        {
            "item_id": "item-01",
            "goal": "First dependency",
            "expected_result": "First result",
            "status": "completed",
            "result_summary": "Done",
        },
        {
            "item_id": "item-02",
            "goal": "Second dependency",
            "expected_result": "Second result",
            "status": "completed",
            "result_summary": "Done",
        },
        {
            "item_id": "item-03",
            "goal": "Consume both dependencies",
            "expected_result": "Combined result",
            "status": "in_progress",
            "depends_on": ["item-01", "item-02"],
            "template_keys": ["template-b", "template-a"],
        },
    ]
    criteria_reordered = deepcopy(before)
    criteria_reordered["success_criterion_definitions"].reverse()
    assert validate_fact_transition("workcase", before, criteria_reordered) == ()

    members_reordered = deepcopy(before)
    item = next(item for item in members_reordered["work_items"] if item["item_id"] == "item-03")
    item["depends_on"].reverse()
    item["template_keys"].reverse()
    assert validate_fact_transition("workcase", before, members_reordered) == ()

    items_reordered = deepcopy(before)
    items_reordered["work_items"].reverse()
    assert validate_fact_transition("workcase", before, items_reordered) == ()


def test_cancelled_item_can_remain_runtime_state_or_explicitly_drive_plan_revision() -> None:
    before = _v2_workcase()
    before["work_items"] = [
        {
            "item_id": "item-01",
            "goal": "Optional bounded item",
            "expected_result": "Either a result or the planned stop condition",
            "status": "pending",
        }
    ]
    cancelled = deepcopy(before)
    cancelled["work_items"][0].update({"status": "cancelled", "result_summary": "The planned stop condition occurred"})
    assert validate_fact_transition("workcase", before, cancelled) == ()

    revised = deepcopy(cancelled)
    revised.update(
        {
            "phase": "human_plan_confirming",
            "plan_version": 2,
            "creation_reviews": [{"subject_version": 2}],
        }
    )
    revised.pop("execution_approval")
    assert validate_fact_transition("workcase", before, revised) == ()


def test_workcase_result_fields_do_not_semantically_control_result_version() -> None:
    before = _reviewing()
    after = {
        **before,
        "phase": "closure_preparing",
        "controller_check_summary": "Corrected Controller check",
        "validation_summary": "Current validation summary",
        "closure_outcome": "completed",
        "disposition_summary": "No residual responsibility",
    }

    assert validate_fact_transition("workcase", before, after) == ()


def test_controller_can_explicitly_bump_result_version_and_restart_review() -> None:
    before = _reviewing()
    after = {**before, "result_version": 2}

    issues = validate_fact_transition("workcase", before, after)
    assert any(issue.field_path == "result_reviews" for issue in issues)

    after.pop("result_reviews")
    assert validate_fact_transition("workcase", before, after) == ()


def test_first_result_version_has_one_mechanical_source_edge() -> None:
    before = _workcase()
    first_result = {**before, "phase": "controller_checking", "result_version": 1}
    assert validate_fact_transition("workcase", before, first_result) == ()

    wrong_value = {**first_result, "result_version": 2}
    issues = validate_fact_transition("workcase", before, wrong_value)
    assert any(issue.field_path == "result_version" and "建立为 1" in issue.summary for issue in issues)

    wrong_edge = {**before, "phase": "independent_reviewing", "result_version": 1}
    issues = validate_fact_transition("workcase", before, wrong_edge)
    assert any(issue.field_path == "result_version" and "只能" in issue.summary for issue in issues)


def test_first_execution_cannot_carry_result_context() -> None:
    before = {**_workcase(), "phase": "human_plan_confirming"}
    before.pop("execution_approval")
    after = {
        **before,
        "phase": "executing",
        "execution_approval": {"subject_version": 1},
        "result_version": 1,
    }

    issues = validate_fact_transition("workcase", before, after)
    assert any(issue.field_path == "result_version" and "首次" in issue.summary for issue in issues)


def test_v2_progress_phase_transition_needs_no_history_event() -> None:
    before = _v2_workcase()
    after = {
        **before,
        "phase": "controller_checking",
        "result_version": 1,
    }

    assert validate_fact_transition("workcase", before, after) == ()


def test_review_must_originate_from_independent_reviewing() -> None:
    controller = {
        **_workcase(),
        "phase": "controller_checking",
        "result_version": 1,
        "controller_check_summary": "Controller check complete",
    }
    forged = {**controller, "phase": "closure_preparing", "result_reviews": [_review()]}

    issues = validate_fact_transition("workcase", controller, forged)
    assert any(
        issue.field_path == "result_reviews" and "只能在 independent_reviewing" in issue.summary for issue in issues
    )
    assert any(issue.field_path == "result_reviews" and "转换前" in issue.summary for issue in issues)

    reviewing = {**controller, "phase": "independent_reviewing"}
    returned = {**reviewing, "phase": "controller_checking", "result_reviews": [_review()]}
    assert validate_fact_transition("workcase", reviewing, returned) == ()

    closure = {**returned, "phase": "closure_preparing"}
    assert validate_fact_transition("workcase", returned, closure) == ()


def test_legacy_reviewer_fields_are_immutable_after_independent_reviewing() -> None:
    before = {**_reviewing(), "phase": "controller_checking"}
    changed_review = {**_review(), "conclusion": "pass"}
    changed = {**before, "result_reviews": [changed_review]}

    issues = validate_fact_transition("workcase", before, changed)
    assert any(issue.field_path == "result_reviews" and "Reviewer" in issue.summary for issue in issues)

    appended = {**before, "result_reviews": [*before["result_reviews"], _review("pass")]}
    assert any(issue.field_path == "result_reviews" for issue in validate_fact_transition("workcase", before, appended))

    resolution_only = {
        **before,
        "result_reviews": [{**_review(), "controller_resolution": "1. Rejected with current evidence."}],
    }
    assert validate_fact_transition("workcase", before, resolution_only) == ()


def test_v2_transition_distinguishes_authorized_same_event_correction_from_event_formation() -> None:
    creation_review = {
        "reviewer": "independent-plan-reviewer",
        "reviewed_at": "2026-07-14T09:00:00+08:00",
        "subject_version": 1,
        "scope": "Current plan",
        "conclusion": "pass",
    }
    result_review = _review()
    before = {
        **_v2_workcase(),
        "phase": "closure_preparing",
        "creation_reviews": [creation_review],
        "result_version": 1,
        "controller_check_summary": "Current result checked",
        "result_reviews": [result_review],
    }
    corrected = {
        **before,
        "creation_reviews": [{**creation_review, "scope": "Corrected current plan scope"}],
        "result_reviews": [{**result_review, "scope": "Corrected current result scope"}],
    }
    assert validate_fact_transition("workcase", before, corrected) == ()

    corrected_on_phase_edge = {**corrected, "phase": "human_closure_confirming"}
    issues = validate_fact_transition("workcase", before, corrected_on_phase_edge)
    assert any(issue.field_path == "creation_reviews" and "status 与 phase 不变" in issue.summary for issue in issues)
    assert any(issue.field_path == "result_reviews" and "status 与 phase 不变" in issue.summary for issue in issues)

    resolution_on_phase_edge = {
        **before,
        "phase": "human_closure_confirming",
        "result_reviews": [{**result_review, "controller_resolution": "Updated current Controller disposition"}],
    }
    assert validate_fact_transition("workcase", before, resolution_on_phase_edge) == ()

    formed_creation_event = {
        **before,
        "creation_reviews": [
            *before["creation_reviews"],
            {**creation_review, "reviewer": "another-plan-reviewer"},
        ],
    }
    issues = validate_fact_transition("workcase", before, formed_creation_event)
    assert any(issue.field_path == "creation_reviews" and "新事件" in issue.summary for issue in issues)

    formed_result_event = {
        **before,
        "result_reviews": [
            *before["result_reviews"],
            {**result_review, "reviewer": "another-result-reviewer"},
        ],
    }
    issues = validate_fact_transition("workcase", before, formed_result_event)
    assert any(issue.field_path == "result_reviews" and "新事件" in issue.summary for issue in issues)


def test_controller_has_all_four_post_review_choices() -> None:
    before = _reviewing()
    for phase in ("executing", "controller_checking", "closure_preparing"):
        assert validate_fact_transition("workcase", before, {**before, "phase": phase}) == ()
    assert (
        validate_fact_transition(
            "workcase",
            before,
            {
                **before,
                "result_reviews": [{**_review(), "controller_resolution": "1. Accepted; request another review."}],
            },
        )
        == ()
    )


def test_controller_can_bump_and_return_to_execution_without_reusing_reviews() -> None:
    before = {**_reviewing(), "phase": "controller_checking"}
    after = {**before, "phase": "executing", "result_version": 2}
    after.pop("result_reviews")

    assert validate_fact_transition("workcase", before, after) == ()


def test_controller_can_request_additional_same_version_review_from_closure_preparing() -> None:
    before = {
        **_reviewing(),
        "phase": "closure_preparing",
        "validation_summary": "Current validation summary",
        "closure_outcome": "completed",
        "disposition_summary": "No residual responsibility",
    }
    reviewing = {**before, "phase": "independent_reviewing"}

    assert validate_fact_transition("workcase", before, reviewing) == ()

    additional_review = {
        **_review("pass"),
        "reviewer": "additional-independent-reviewer",
        "reviewed_at": "2026-07-14T11:00:00+08:00",
        "feedback": ["No additional issue"],
        "controller_resolution": "Pending Controller handling.",
    }
    with_additional_review = {
        **reviewing,
        "result_reviews": [*reviewing["result_reviews"], additional_review],
    }
    assert validate_fact_transition("workcase", reviewing, with_additional_review) == ()


def test_controller_can_bump_result_version_when_closure_change_needs_rereview() -> None:
    before = {
        **_reviewing(),
        "phase": "closure_preparing",
        "validation_summary": "Current validation summary",
        "closure_outcome": "completed",
        "disposition_summary": "No residual responsibility",
    }
    after = {**before, "phase": "independent_reviewing", "result_version": 2}
    after.pop("result_reviews")

    assert validate_fact_transition("workcase", before, after) == ()


def test_v2_plan_and_result_bumps_need_no_audit_continuity() -> None:
    before = _v2_workcase()
    after_plan = {
        **before,
        "goal": "Deliver a changed result",
        "phase": "human_plan_confirming",
        "plan_version": 2,
        "creation_reviews": [{"subject_version": 2}],
    }
    after_plan.pop("execution_approval")
    assert validate_fact_transition("workcase", before, after_plan) == ()

    reviewed = {
        **before,
        "phase": "controller_checking",
        "result_version": 1,
        "controller_check_summary": "Checked",
        "result_reviews": [_review()],
    }
    after_result = {**reviewed, "result_version": 2}
    after_result.pop("result_reviews")
    assert validate_fact_transition("workcase", reviewed, after_result) == ()


def test_v1_only_accepts_explicit_v2_migration_and_strips_review_basis() -> None:
    before = {
        **_v2_workcase(),
        "workcase_profile": "control-contract-v1",
        "audit_summary": [{"audit_id": "audit-01"}],
        "creation_reviews": [
            {
                "reviewer": "removed-reviewer",
                "subject_version": 1,
                "review_basis": {"projection_key": "plan_current", "subject_fingerprint": "0" * 64},
            },
            {
                "reviewer": "current-reviewer",
                "subject_version": 1,
                "scope": "Current plan",
                "feedback": ["Clarify one boundary"],
                "controller_resolution": "Original Controller disposition",
                "review_basis": {"projection_key": "plan_current", "subject_fingerprint": "1" * 64},
            },
        ],
    }
    ordinary = {**before, "summary": "Attempted V1 update"}
    issues = validate_fact_transition("workcase", before, ordinary)
    assert any(issue.field_path == "workcase_profile" and "只允许显式迁移" in issue.summary for issue in issues)

    migrated = {
        **before,
        "workcase_profile": "control-contract-v2",
        "creation_reviews": [
            {
                "reviewer": "current-reviewer",
                "subject_version": 1,
                "scope": "Current plan",
                "feedback": ["Clarify one boundary"],
                "controller_resolution": "Calibrated current Controller disposition",
            }
        ],
    }
    migrated.pop("audit_summary")
    assert validate_fact_transition("workcase", before, migrated) == ()

    changed_review = {**migrated, "creation_reviews": [{"reviewer": "other", "subject_version": 1}]}
    issues = validate_fact_transition("workcase", before, changed_review)
    assert any(issue.field_path == "creation_reviews" and "有序子序列" in issue.summary for issue in issues)

    changed_feedback = deepcopy(migrated)
    changed_feedback["creation_reviews"][0]["feedback"] = ["Rewritten Reviewer feedback"]
    issues = validate_fact_transition("workcase", before, changed_feedback)
    assert any(issue.field_path == "creation_reviews" and "Reviewer 自有字段" in issue.summary for issue in issues)

    changed_scope = deepcopy(migrated)
    changed_scope["creation_reviews"][0]["scope"] = "Rewritten review scope"
    issues = validate_fact_transition("workcase", before, changed_scope)
    assert any(issue.field_path == "creation_reviews" and "Reviewer 自有字段" in issue.summary for issue in issues)

    removed_all = {**migrated, "creation_reviews": []}
    issues = validate_fact_transition("workcase", before, removed_all)
    assert any(issue.field_path == "creation_reviews" and "有序子序列" in issue.summary for issue in issues)

    reordered = {
        **migrated,
        "creation_reviews": [
            {"reviewer": "current-reviewer", "subject_version": 1},
            {"reviewer": "removed-reviewer", "subject_version": 1},
        ],
    }
    issues = validate_fact_transition("workcase", before, reordered)
    assert any(issue.field_path == "creation_reviews" and "有序子序列" in issue.summary for issue in issues)

    no_result_before = deepcopy(before)
    no_result_before.pop("result_reviews", None)
    no_result_after = deepcopy(migrated)
    no_result_after.pop("result_reviews", None)
    assert validate_fact_transition("workcase", no_result_before, no_result_after) == ()

    formed_result = deepcopy(no_result_after)
    formed_result["result_reviews"] = [_review()]
    issues = validate_fact_transition("workcase", no_result_before, formed_result)
    assert any(issue.field_path == "result_reviews" and "不得新增" in issue.summary for issue in issues)


def test_closed_v1_can_migrate_in_place_but_cannot_change_closure() -> None:
    before = {
        **_v2_workcase(),
        "workcase_profile": "control-contract-v1",
        "status": "closed",
        "phase": "closed",
        "result_version": 1,
        "validation_summary": "Validated result",
        "closure_outcome": "completed",
        "disposition_summary": "No residual responsibility",
        "execution_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-14T09:30:00+08:00",
            "summary": "Human approved execution",
        },
        "closure_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-14T11:00:00+08:00",
            "summary": "Human approved closure",
        },
        "audit_summary": [{"audit_id": "audit-01"}],
    }
    migrated = {
        **before,
        "workcase_profile": "control-contract-v2",
        "validation_summary": "Validated result with corrected wording",
        "disposition_summary": "No residual responsibility remains",
        "closure_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-14T11:00:00+08:00",
            "summary": "Human approved the same closure result",
        },
    }
    migrated.pop("audit_summary")
    assert validate_fact_transition("workcase", before, migrated) == ()

    changed = {**migrated, "closure_outcome": "partial"}
    issues = validate_fact_transition("workcase", before, changed)
    assert any(issue.field_path == "closure_outcome" and "不得改变" in issue.summary for issue in issues)

    reopened = {**migrated, "status": "open", "phase": "human_closure_confirming"}
    issues = validate_fact_transition("workcase", before, reopened)
    assert any(issue.field_path == "workcase_profile" and "status 与 phase" in issue.summary for issue in issues)

    approval_rebound = {**migrated, "closure_approval": {"subject_version": 2}}
    issues = validate_fact_transition("workcase", before, approval_rebound)
    assert any(issue.field_path == "closure_approval" and "版本或形成时点" in issue.summary for issue in issues)

    approval_retimed = {
        **migrated,
        "closure_approval": {**migrated["closure_approval"], "approved_at": "2026-07-14T11:01:00+08:00"},
    }
    issues = validate_fact_transition("workcase", before, approval_retimed)
    assert any(issue.field_path == "closure_approval" and "版本或形成时点" in issue.summary for issue in issues)


def test_v2_cannot_downgrade_and_closed_legacy_cannot_upgrade() -> None:
    current = _v2_workcase()
    downgraded = {**current, "workcase_profile": "control-contract-v1"}
    issues = validate_fact_transition("workcase", current, downgraded)
    assert any(issue.field_path == "workcase_profile" and "不得移除或降级" in issue.summary for issue in issues)

    legacy_closed = {**_workcase(), "status": "closed", "phase": "closed"}
    upgraded = {**legacy_closed, "workcase_profile": "control-contract-v2"}
    issues = validate_fact_transition("workcase", legacy_closed, upgraded)
    assert any(issue.field_path == "workcase_profile" and "closed legacy" in issue.summary for issue in issues)

    legacy_open = _workcase()
    direct_v2 = {
        **legacy_open,
        "workcase_profile": "control-contract-v2",
        "success_criterion_definitions": [{"criterion_id": "criterion-01", "statement": "The result is verified"}],
        "plan_version": 2,
    }
    direct_v2.pop("success_criteria")
    issues = validate_fact_transition("workcase", legacy_open, direct_v2)
    assert any(issue.field_path == "workcase_profile" and "不得借 V2" in issue.summary for issue in issues)


def test_invalid_missing_profile_repairs_to_the_profile_required_by_created_at() -> None:
    missing_v2 = {**_v2_workcase(), "created_at": "2026-07-26T12:45:00+08:00"}
    missing_v2.pop("workcase_profile")
    repaired_v2 = {**missing_v2, "workcase_profile": "control-contract-v2"}
    assert (
        validate_fact_transition(
            "workcase",
            missing_v2,
            repaired_v2,
            repairing_invalid_before=True,
        )
        == ()
    )

    missing_v1 = {
        **_v2_workcase(),
        "created_at": "2026-07-20T07:30:00+08:00",
        "workcase_profile": "control-contract-v1",
        "audit_summary": [{"audit_id": "audit-01"}],
    }
    missing_v1.pop("workcase_profile")
    repaired_v1 = {**missing_v1, "workcase_profile": "control-contract-v1"}
    assert (
        validate_fact_transition(
            "workcase",
            missing_v1,
            repaired_v1,
            repairing_invalid_before=True,
        )
        == ()
    )

    wrong_profile = {**missing_v1, "workcase_profile": "control-contract-v2"}
    issues = validate_fact_transition(
        "workcase",
        missing_v1,
        wrong_profile,
        repairing_invalid_before=True,
    )
    assert any(issue.field_path == "workcase_profile" and "created_at" in issue.summary for issue in issues)

    expanded_repair = {
        **repaired_v2,
        "goal": "Changed while adding the required profile",
        "phase": "human_plan_confirming",
        "execution_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-26T13:00:00+08:00",
            "summary": "Attempted approval formation",
        },
    }
    issues = validate_fact_transition(
        "workcase",
        missing_v2,
        expanded_repair,
        repairing_invalid_before=True,
    )
    assert any(issue.field_path == "workcase_profile" and "不得同次改变" in issue.summary for issue in issues)

    true_legacy = {**_workcase(), "created_at": "2026-07-20T07:29:59+08:00"}
    direct_v2 = {
        **true_legacy,
        "workcase_profile": "control-contract-v2",
        "success_criterion_definitions": [{"criterion_id": "criterion-01", "statement": "Verified"}],
    }
    direct_v2.pop("success_criteria")
    issues = validate_fact_transition(
        "workcase",
        true_legacy,
        direct_v2,
        repairing_invalid_before=True,
    )
    assert any(issue.field_path == "workcase_profile" and "不得借 V2" in issue.summary for issue in issues)


def test_removed_superseded_status_is_rejected_by_the_current_lifecycle() -> None:
    before = {"status": "active", "relations": []}
    after = {"status": "superseded", "relations": []}

    issues = validate_fact_transition("adr", before, after)

    assert any(issue.field_path == "status" and "不在当前单对象更新允许边中" in issue.summary for issue in issues)


def test_workcase_open_blocked_change_cannot_move_phase() -> None:
    before = _workcase()
    after = {**before, "status": "blocked", "phase": "controller_checking"}

    issues = validate_fact_transition("workcase", before, after)

    assert any("不得同时改变 phase" in issue.summary for issue in issues)


def test_actual_update_timestamp_must_move_forward() -> None:
    before = {"status": "open", "updated_at": "2026-07-14T10:00:00+08:00"}
    after = {"status": "open", "updated_at": "2026-07-14T09:59:59+08:00"}

    issues = validate_fact_transition("spark", before, after)

    assert any(issue.field_path == "updated_at" and "晚于" in issue.summary for issue in issues)
