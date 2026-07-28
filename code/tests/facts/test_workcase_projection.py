from __future__ import annotations

from copy import deepcopy

import pytest

from ldvh.facts.workcase_projection import (
    all_terminal,
    canonical_plan_projection,
    canonical_result_projection,
    no_execution_facts,
    plan_delta,
    pre_execution_stop_shape,
    result_delta,
    result_projection_complete,
)


def _complete_result() -> dict[str, object]:
    return {
        "goal": "Ship the bounded result",
        "scope": "One implementation",
        "success_criterion_definitions": [
            {"criterion_id": "criterion-second", "statement": "Second"},
            {"criterion_id": "criterion-first", "statement": "First"},
        ],
        "work_items": [
            {
                "item_id": "item-verify",
                "goal": "Verify",
                "expected_result": "A checked result",
                "depends_on": ["item-build", "item-build"],
                "template_keys": ["check", "check"],
                "status": "completed",
                "result_summary": "Verified",
            },
            {
                "item_id": "item-build",
                "goal": "Build",
                "expected_result": "A result",
                "status": "completed",
                "result_summary": "Built",
            },
        ],
        "success_criterion_results": [
            {"criterion_id": "criterion-second", "outcome": "satisfied", "summary": "Yes"},
            {"criterion_id": "criterion-first", "outcome": "satisfied", "summary": "Yes"},
        ],
        "result_summary": "The bounded result shipped.",
        "controller_check_summary": "Controller checked the current result.",
        "validation_summary": "Both criteria were checked.",
    }


def test_plan_projection_normalizes_only_plan_members() -> None:
    fields = _complete_result()
    fields.update({"phase": "closure_preparing", "result_version": 1, "waiting_on": "Nobody"})

    projection = canonical_plan_projection(fields)

    assert list(projection) == ["goal", "scope", "success_criterion_definitions", "work_items"]
    assert [criterion["criterion_id"] for criterion in projection["success_criterion_definitions"]] == [
        "criterion-first",
        "criterion-second",
    ]
    assert [item["item_id"] for item in projection["work_items"]] == ["item-build", "item-verify"]
    assert projection["work_items"][1]["depends_on"] == ["item-build"]
    assert projection["work_items"][1]["template_keys"] == ["check"]
    assert "status" not in projection["work_items"][0]


def test_plan_delta_ignores_nonsemantic_order_and_lifecycle_fields() -> None:
    before = _complete_result()
    after = deepcopy(before)
    after["work_items"] = list(reversed(after["work_items"]))
    after["success_criterion_definitions"] = list(reversed(after["success_criterion_definitions"]))
    after["phase"] = "plan_revising"

    assert plan_delta(before, after) is False

    after["scope"] = "A changed boundary"
    assert plan_delta(before, after) is True


def test_result_projection_contains_only_current_result_subject() -> None:
    fields = _complete_result()
    fields.update({"goal": "Changed display", "result_reviews": [{"reviewer": "reviewer"}]})

    projection = canonical_result_projection(fields)

    assert set(projection) == {
        "work_items",
        "success_criterion_results",
        "result_summary",
        "controller_check_summary",
        "validation_summary",
    }
    assert set(projection["work_items"][0]) == {"item_id", "status", "result_summary"}
    assert "goal" not in projection
    assert "result_reviews" not in projection


def test_result_projection_remains_inspectable_while_partial() -> None:
    fields = _complete_result()
    del fields["validation_summary"]

    projection = canonical_result_projection(fields)

    assert "validation_summary" not in projection
    assert result_projection_complete(fields) is False
    with pytest.raises(ValueError, match="complete canonical result projections"):
        result_delta(fields, _complete_result())


def test_result_delta_is_order_stable_and_detects_result_changes() -> None:
    before = _complete_result()
    after = deepcopy(before)
    after["work_items"] = list(reversed(after["work_items"]))
    after["success_criterion_results"] = list(reversed(after["success_criterion_results"]))

    assert result_projection_complete(before)
    assert result_delta(before, after) is False

    after["controller_check_summary"] = "The controller found a new issue."
    assert result_delta(before, after) is True


def test_all_terminal_requires_a_nonempty_entirely_terminal_item_set() -> None:
    fields = _complete_result()
    assert all_terminal(fields)

    fields["work_items"][0]["status"] = "blocked"
    assert not all_terminal(fields)
    assert not all_terminal({"work_items": []})


def test_no_execution_facts_is_exact_and_rejects_result_or_item_progress() -> None:
    fields = {
        "work_items": [
            {"item_id": "item-one", "goal": "One", "expected_result": "One", "status": "pending"}
        ]
    }
    assert no_execution_facts(fields)

    with_progress = deepcopy(fields)
    with_progress["work_items"][0]["current_summary"] = "Started"
    assert not no_execution_facts(with_progress)

    with_result_version = {**fields, "result_version": 1}
    assert not no_execution_facts(with_result_version)

    with_suggestion = {**fields, "spark_suggestions": [{"suggestion_id": "suggestion-later"}]}
    assert not no_execution_facts(with_suggestion)


def test_pre_execution_stop_shape_is_the_only_approval_less_result_shape() -> None:
    fields = {
        "phase": "controller_checking",
        "result_version": 1,
        "work_items": [
            {
                "item_id": "item-one",
                "goal": "One",
                "expected_result": "One",
                "status": "cancelled",
                "result_summary": "Human stopped before execution; no result was formed.",
            }
        ],
    }
    assert pre_execution_stop_shape(fields)

    assert not pre_execution_stop_shape({**fields, "execution_approval": {"subject_version": 1}})
    changed = deepcopy(fields)
    changed["work_items"][0]["status"] = "completed"
    assert not pre_execution_stop_shape(changed)


def test_pre_execution_stop_shape_rejects_a_whitespace_only_result_summary() -> None:
    fields = {
        "phase": "controller_checking",
        "result_version": 1,
        "work_items": [
            {
                "item_id": "item-one",
                "goal": "One",
                "expected_result": "One",
                "status": "cancelled",
                "result_summary": " \t\n ",
            }
        ],
    }

    assert not pre_execution_stop_shape(fields)


@pytest.mark.parametrize(
    "blank_member",
    [
        "item_id",
        "item_result_summary",
        "criterion_ids",
        "criterion_result_summary",
        "result_summary",
        "controller_check_summary",
        "validation_summary",
    ],
)
def test_complete_result_predicate_rejects_whitespace_only_strings(blank_member: str) -> None:
    fields = _complete_result()
    if blank_member == "item_id":
        fields["work_items"][0]["item_id"] = " \t "
    elif blank_member == "item_result_summary":
        fields["work_items"][0]["result_summary"] = " \t "
    elif blank_member == "criterion_ids":
        fields["success_criterion_definitions"][0]["criterion_id"] = " \t "
        fields["success_criterion_results"][0]["criterion_id"] = " \t "
    elif blank_member == "criterion_result_summary":
        fields["success_criterion_results"][0]["summary"] = " \t "
    else:
        fields[blank_member] = " \t "

    assert not result_projection_complete(fields)
