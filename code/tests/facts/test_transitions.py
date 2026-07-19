from __future__ import annotations

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
            }
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


def test_workcase_result_fields_do_not_semantically_control_result_version() -> None:
    before = _reviewing()
    after = {
        **before,
        "phase": "closure_preparing",
        "controller_check_summary": "Corrected Controller check",
        "validation_summary": "Current validation summary",
        "closure_outcome": "completed",
        "disposition_summary": "No residual responsibility",
        "evidence_refs": [{"kind": "repository-path", "locator": "evidence/final.txt"}],
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
        issue.field_path == "result_reviews" and "只能在 independent_reviewing" in issue.summary
        for issue in issues
    )
    assert any(issue.field_path == "result_reviews" and "转换前" in issue.summary for issue in issues)

    reviewing = {**controller, "phase": "independent_reviewing"}
    returned = {**reviewing, "phase": "controller_checking", "result_reviews": [_review()]}
    assert validate_fact_transition("workcase", reviewing, returned) == ()

    closure = {**returned, "phase": "closure_preparing"}
    assert validate_fact_transition("workcase", returned, closure) == ()


def test_reviewer_fields_are_immutable_after_independent_reviewing() -> None:
    before = {**_reviewing(), "phase": "controller_checking"}
    changed_review = {**_review(), "conclusion": "pass"}
    changed = {**before, "result_reviews": [changed_review]}

    issues = validate_fact_transition("workcase", before, changed)
    assert any(issue.field_path == "result_reviews" and "Reviewer" in issue.summary for issue in issues)

    appended = {**before, "result_reviews": [*before["result_reviews"], _review("pass")]}
    assert any(
        issue.field_path == "result_reviews"
        for issue in validate_fact_transition("workcase", before, appended)
    )

    resolution_only = {
        **before,
        "result_reviews": [{**_review(), "controller_resolution": "1. Rejected with current evidence."}],
    }
    assert validate_fact_transition("workcase", before, resolution_only) == ()


def test_controller_has_all_four_post_review_choices() -> None:
    before = _reviewing()
    for phase in ("executing", "controller_checking", "closure_preparing"):
        assert validate_fact_transition("workcase", before, {**before, "phase": phase}) == ()
    assert validate_fact_transition(
        "workcase",
        before,
        {
            **before,
            "result_reviews": [
                {**_review(), "controller_resolution": "1. Accepted; request another review."}
            ],
        },
    ) == ()


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


def test_single_object_transition_rejects_supersedes_and_superseded_status() -> None:
    before = {"status": "active", "relations": []}
    after = {
        "status": "superseded",
        "relations": [
            {
                "relation_key": "supersedes",
                "target": {
                    "governed_project_id": "sample",
                    "fact_type_key": "adr",
                    "object_id": "adr-0001",
                },
            }
        ],
    }

    issues = validate_fact_transition("adr", before, after)

    assert any(issue.field_path == "status" and "多对象" in issue.summary for issue in issues)
    assert any(issue.field_path == "relations" and "多对象" in issue.summary for issue in issues)


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
