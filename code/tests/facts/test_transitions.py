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


def test_workcase_result_change_requires_result_version_and_review_reset() -> None:
    before = {
        **_workcase(),
        "phase": "independent_reviewing",
        "result_version": 1,
        "controller_check_summary": "Initial check",
        "result_reviews": [{"subject_version": 1}],
    }
    after = {**before, "controller_check_summary": "Corrected check"}

    issues = validate_fact_transition("workcase", before, after)
    assert any(issue.field_path == "result_version" and "必须递增" in issue.summary for issue in issues)

    after["result_version"] = 2
    bumped_issues = validate_fact_transition("workcase", before, after)
    assert any(issue.field_path == "result_reviews" for issue in bumped_issues)

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
