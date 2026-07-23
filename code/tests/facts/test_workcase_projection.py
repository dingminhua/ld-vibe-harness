from __future__ import annotations

import re

import pytest

from ldvh.facts.workcase_projection import (
    project_workcase_subject,
    workcase_subject_fingerprint,
)


def _workcase() -> dict[str, object]:
    return {
        "object_id": "workcase-0042",
        "status": "open",
        "phase": "closure_preparing",
        "goal": "Ship the bounded result",
        "scope": "One implementation",
        "success_criterion_definitions": [
            {"criterion_id": "criterion-02", "statement": "Second"},
            {"criterion_id": "criterion-01", "statement": "First"},
        ],
        "work_items": [
            {
                "item_id": "item-02",
                "goal": "Verify",
                "expected_result": "Evidence",
                "status": "completed",
                "approach_summary": "Run checks",
                "result_summary": "Passed",
            },
            {
                "item_id": "item-01",
                "goal": "Build",
                "expected_result": "Code",
                "status": "completed",
                "approach_summary": "Implement",
                "result_summary": "Built",
            },
        ],
        "success_criterion_results": [
            {"criterion_id": "criterion-02", "outcome": "satisfied", "summary": "Yes"},
            {"criterion_id": "criterion-01", "outcome": "satisfied", "summary": "Yes"},
        ],
        "controller_check_summary": "Checked",
        "improvement_observations": [
            {
                "observation_id": "observation-01",
                "topic_key": "one",
                "summary": "One",
            }
        ],
        "validation_summary": "Validated",
        "closure_outcome": "completed",
        "disposition_summary": "No remaining work",
        "residual_responsibilities": [
            {"residual_id": "residual-01", "summary": "One", "disposition": "routed"}
        ],
        "nonbinding_followups": [
            {"followup_id": "followup-01", "summary": "Maybe", "rationale": "Later"}
        ],
        "relations": [
            {
                "relation_key": "routed-to",
                "target": {
                    "governed_project_id": "p",
                    "fact_type_key": "workcase",
                    "object_id": "workcase-0043",
                },
            }
        ],
        "result_reviews": [{"reviewer": "someone"}],
        "audit_summary": [{"audit_id": "audit-01"}],
        "updated_at": "2026-07-20T12:00:00+08:00",
    }


def test_plan_projection_excludes_lifecycle_identity_reviews_and_results() -> None:
    projection = project_workcase_subject(_workcase(), "plan_current")

    assert set(projection) == {"goal", "scope", "success_criterion_definitions", "work_items"}
    assert [item["item_id"] for item in projection["work_items"]] == ["item-01", "item-02"]
    assert "status" not in projection["work_items"][0]


def test_result_and_closure_projections_have_distinct_owned_fields() -> None:
    workcase = _workcase()
    implementation = project_workcase_subject(workcase, "result_implementation")
    closure = project_workcase_subject(workcase, "result_with_closure_report")

    assert "validation_summary" not in implementation
    assert implementation["work_items"][0]["status"] == "completed"
    assert closure["validation_summary"] == "Validated"
    assert closure["residual_responsibilities"][0]["disposition"] == "routed"


def test_fingerprint_is_order_stable_but_subject_changes_are_visible() -> None:
    first = _workcase()
    second = _workcase()
    second["work_items"] = list(reversed(second["work_items"]))
    second["success_criterion_definitions"] = list(
        reversed(second["success_criterion_definitions"])
    )
    second["status"] = "blocked"
    second["result_reviews"] = [{"reviewer": "different"}]

    fingerprint = workcase_subject_fingerprint(first, "result_implementation")
    assert re.fullmatch(r"[0-9a-f]{64}", fingerprint)
    assert workcase_subject_fingerprint(second, "result_implementation") == fingerprint

    second["controller_check_summary"] = "Changed subject"
    assert workcase_subject_fingerprint(second, "result_implementation") != fingerprint


def test_closure_report_does_not_change_implementation_review_subject() -> None:
    before = _workcase()
    after = {**before, "validation_summary": "A more complete closure report"}

    assert workcase_subject_fingerprint(before, "result_implementation") == workcase_subject_fingerprint(
        after, "result_implementation"
    )
    assert workcase_subject_fingerprint(
        before, "result_with_closure_report"
    ) != workcase_subject_fingerprint(after, "result_with_closure_report")


def test_unknown_projection_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown WorkCase projection"):
        project_workcase_subject(_workcase(), "plan-v3")
