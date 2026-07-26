from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.validation import validate_fact_object
from ldvh.facts.workcase_validation import validate_workcase_snapshot
from ldvh.specs.repository import inspect_repository


def _review(version: int = 1, *, feedback: bool = False) -> dict[str, object]:
    review: dict[str, object] = {
        "reviewer": "independent-reviewer",
        "reviewed_at": "2026-07-26T10:10:00+08:00",
        "subject_version": version,
        "scope": "The current bounded subject.",
        "conclusion": "pass",
    }
    if feedback:
        review.update(
            {
                "conclusion": "pass_with_followups",
                "feedback": ["Clarify the remaining boundary."],
                "controller_resolution": "The boundary was clarified.",
            }
        )
    return review


def _approval() -> dict[str, object]:
    return {
        "subject_version": 1,
        "approved_at": "2026-07-26T10:20:00+08:00",
        "summary": "Human approved this exact plan.",
        "source_refs": ["conversation:plan-approval"],
    }


def _pending_item() -> dict[str, object]:
    return {
        "item_id": "item-build",
        "goal": "Build the bounded result.",
        "expected_result": "A bounded result exists.",
        "status": "pending",
    }


def _pending_item_chain(length: int) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for index in range(length):
        item: dict[str, object] = {
            "item_id": f"item-{index:04d}",
            "goal": f"Complete bounded item {index}.",
            "expected_result": f"Bounded result {index} exists.",
            "status": "pending",
        }
        if index + 1 < length:
            item["depends_on"] = [f"item-{index + 1:04d}"]
        items.append(item)
    return items


def _base(phase: str) -> dict[str, object]:
    return {
        "object_id": "workcase-0042",
        "fact_type_key": "workcase",
        "title": "Bounded work",
        "created_at": "2026-07-26T10:00:00+08:00",
        "updated_at": "2026-07-26T11:00:00+08:00",
        "status": "open",
        "priority": "P1",
        "goal": "Ship one bounded result.",
        "scope": "The bounded implementation and its validation.",
        "success_criterion_definitions": [
            {"criterion_id": "criterion-result", "statement": "The result exists and is checked."}
        ],
        "phase": phase,
        "plan_version": 1,
        "work_items": [_pending_item()],
    }


def _complete_result(phase: str) -> dict[str, object]:
    fields = _base(phase)
    fields["work_items"] = [
        {
            **_pending_item(),
            "status": "completed",
            "result_summary": "The bounded result was built.",
        }
    ]
    fields.update(
        {
            "execution_approval": _approval(),
            "result_version": 1,
            "success_criterion_results": [
                {
                    "criterion_id": "criterion-result",
                    "outcome": "satisfied",
                    "summary": "The result exists and the targeted check passed.",
                }
            ],
            "result_summary": "The bounded result was delivered.",
            "controller_check_summary": "The Controller checked the item result and criterion mapping.",
            "validation_summary": "The targeted check passed; unrelated behavior was not checked.",
        }
    )
    return fields


def _human_closure_confirming() -> dict[str, object]:
    fields = _complete_result("human_closure_confirming")
    fields.update(
        {
            "result_reviews": [_review()],
            "closure_proposal": {
                "proposed_outcome": "completed",
                "proposed_disposition_summary": "The bounded responsibility is complete with no residual work.",
            },
            "waiting_on": "Human decision on the complete closure proposal.",
        }
    )
    return fields


def _closed() -> dict[str, object]:
    active = _human_closure_confirming()
    return {
        name: deepcopy(active[name])
        for name in (
            "object_id",
            "fact_type_key",
            "title",
            "created_at",
            "updated_at",
            "goal",
            "scope",
            "success_criterion_definitions",
            "success_criterion_results",
            "result_summary",
            "validation_summary",
        )
    } | {
        "status": "closed",
        "closure_outcome": "completed",
        "disposition_summary": "The bounded responsibility is complete with no residual work.",
    }


def test_workcase_review_and_approval_times_accept_arbitrary_fractional_precision(
    current_specs_repository: Path,
) -> None:
    fields = _complete_result("independent_reviewing")
    fields["updated_at"] = "2026-07-26T11:00:00.99999999999999999999+08:00"
    approval = fields["execution_approval"]
    assert isinstance(approval, dict)
    approval["approved_at"] = "2026-07-26T10:20:00.12345678901234567890+08:00"
    review = _review()
    review["reviewed_at"] = "2026-07-26T10:30:00.98765432109876543210+08:00"
    fields["result_reviews"] = [review]
    fields["waiting_on"] = "Waiting for the independent Reviewer."
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]

    assert validate_fact_object("workcase", fields, schema) == ()


@pytest.mark.parametrize(
    "fields",
    [
        {
            **_base("human_plan_confirming"),
            "creation_reviews": [_review()],
            "waiting_on": "Human plan decision.",
        },
        _base("plan_revising"),
        {
            **_base("executing"),
            "work_items": [
                {
                    **_pending_item(),
                    "status": "in_progress",
                    "current_summary": "The bounded implementation has started.",
                    "resume_from": "Continue from the current implementation boundary.",
                }
            ],
            "execution_approval": _approval(),
        },
        {
            **_complete_result("controller_checking"),
            "success_criterion_results": [
                {
                    "criterion_id": "criterion-result",
                    "outcome": "satisfied",
                    "summary": "The current check passed.",
                }
            ],
        },
        _complete_result("independent_reviewing"),
        {**_complete_result("closure_preparing"), "result_reviews": [_review()]},
        _human_closure_confirming(),
        _closed(),
    ],
)
def test_current_phase_and_closed_snapshots_are_accepted(fields: dict[str, object]) -> None:
    assert validate_workcase_snapshot(fields) == ()


def test_blocked_item_resume_from_is_conditional_not_required() -> None:
    fields = {
        **_base("executing"),
        "status": "blocked",
        "blocking_summary": "No current action can continue until the external input arrives.",
        "work_items": [
            {
                **_pending_item(),
                "status": "blocked",
                "current_summary": "The item reached the external input boundary.",
                "blocking_summary": "The required external input is unavailable.",
            }
        ],
        "execution_approval": _approval(),
    }

    assert validate_workcase_snapshot(fields) == ()


def test_item_dependencies_require_existing_completed_targets_and_an_acyclic_graph() -> None:
    fields = {
        **_base("executing"),
        "execution_approval": _approval(),
        "work_items": [
            {**_pending_item(), "status": "cancelled", "result_summary": "Stopped."},
            {
                "item_id": "item-use",
                "goal": "Use the result.",
                "expected_result": "The result is used.",
                "status": "in_progress",
                "depends_on": ["item-build"],
                "current_summary": "Use has started.",
                "resume_from": "Continue using the result.",
            },
        ],
    }

    issues = validate_workcase_snapshot(fields)
    assert any(issue.field_path == "work_items[1].depends_on[0]" for issue in issues)

    cyclic = deepcopy(fields)
    cyclic["work_items"][0]["status"] = "pending"
    cyclic["work_items"][0].pop("result_summary")
    cyclic["work_items"][0]["depends_on"] = ["item-use"]
    assert any(issue.field_path == "work_items" for issue in validate_workcase_snapshot(cyclic))


def test_item_dag_accepts_a_large_valid_linear_dependency_chain_without_recursion() -> None:
    fields = _base("plan_revising")
    fields["work_items"] = _pending_item_chain(1_500)

    assert validate_workcase_snapshot(fields) == ()


def test_item_dag_rejects_a_large_chain_closed_by_a_terminal_cycle_without_crashing() -> None:
    fields = _base("plan_revising")
    fields["work_items"] = _pending_item_chain(1_500)
    fields["work_items"][-1]["depends_on"] = ["item-0000"]

    issues = validate_workcase_snapshot(fields)

    assert any(
        issue.field_path == "work_items" and issue.summary == "work item depends_on 有向图不得成环" for issue in issues
    )


def test_result_arrays_must_cover_every_current_criterion() -> None:
    fields = _complete_result("independent_reviewing")
    fields["success_criterion_definitions"].append(
        {"criterion_id": "criterion-second", "statement": "A second boundary is checked."}
    )

    issues = validate_workcase_snapshot(fields)

    assert any(issue.field_path == "success_criterion_results" for issue in issues)


def test_result_reviews_bind_current_version_and_feedback_is_resolved_before_closure() -> None:
    fields = _complete_result("closure_preparing")
    fields["result_reviews"] = [
        {
            **_review(2, feedback=True),
            "controller_resolution": "",
        }
    ]

    paths = {issue.field_path for issue in validate_workcase_snapshot(fields)}

    assert "result_reviews[0].subject_version" in paths
    assert "result_reviews[0].controller_resolution" in paths


def test_review_event_triple_is_unique_within_each_review_array() -> None:
    fields = _complete_result("closure_preparing")
    fields["result_reviews"] = [_review(), _review()]

    assert any(
        issue.field_path == "result_reviews" and "三元组" in issue.summary
        for issue in validate_workcase_snapshot(fields)
    )


def test_approval_source_refs_are_nonempty_unique_stable_strings() -> None:
    fields = _base("executing")
    fields["work_items"] = [
        {
            **_pending_item(),
            "status": "in_progress",
            "current_summary": "Started.",
            "resume_from": "Continue.",
        }
    ]
    fields["execution_approval"] = {**_approval(), "source_refs": ["decision:1", "decision:1"]}

    assert any(issue.field_path == "execution_approval.source_refs" for issue in validate_workcase_snapshot(fields))


def test_pre_execution_stop_can_reach_result_chain_without_fabricated_approval() -> None:
    fields = _complete_result("human_closure_confirming")
    fields.pop("execution_approval")
    fields["work_items"][0]["status"] = "cancelled"
    fields["work_items"][0]["result_summary"] = "Human stopped the work before execution; no output was formed."
    fields["success_criterion_results"][0].update(
        {"outcome": "not_verified", "summary": "Execution and validation did not occur."}
    )
    fields.update(
        {
            "result_summary": "No implementation result was formed.",
            "result_reviews": [_review()],
            "closure_proposal": {
                "proposed_outcome": "cancelled",
                "proposed_disposition_summary": (
                    "Human may stop without a result and accept the remaining responsibility."
                ),
                "residual_decisions": [
                    {
                        "residual_id": "residual-unfinished",
                        "summary": "The intended result was not implemented or verified.",
                        "proposed_disposition": "accept_stop",
                    }
                ],
            },
            "waiting_on": "Human closure decision.",
        }
    )

    assert validate_workcase_snapshot(fields) == ()


@pytest.mark.parametrize(
    ("criterion_outcome", "closure_outcome"),
    [
        ("not_verified", "not-achieved"),
        ("not_satisfied", "cancelled"),
    ],
)
def test_terminal_outcome_distinguishes_unknown_from_known_nonachievement(
    criterion_outcome: str,
    closure_outcome: str,
) -> None:
    fields = _closed()
    fields["success_criterion_results"][0].update(
        {
            "outcome": criterion_outcome,
            "summary": "The criterion is either known unmet or remains unverified.",
        }
    )
    fields["closure_outcome"] = closure_outcome
    fields["disposition_summary"] = "The remaining responsibility was explicitly addressed."
    fields["residual_responsibilities"] = [
        {
            "residual_id": "residual-result",
            "summary": "The original success criterion did not form a satisfied result.",
        }
    ]

    issues = validate_workcase_snapshot(fields)

    assert any(issue.field_path == "closure_outcome" for issue in issues)


def test_completed_proposal_and_closed_snapshot_cannot_hide_residual_work() -> None:
    active = _human_closure_confirming()
    active["closure_proposal"]["residual_decisions"] = [
        {
            "residual_id": "residual-hidden",
            "summary": "Hidden remaining work.",
            "proposed_disposition": "accept_stop",
        }
    ]
    assert any(
        issue.field_path == "closure_proposal.residual_decisions" for issue in validate_workcase_snapshot(active)
    )

    closed = _closed()
    closed["residual_responsibilities"] = [{"residual_id": "residual-hidden", "summary": "Hidden remaining work."}]
    assert any(issue.field_path == "residual_responsibilities" for issue in validate_workcase_snapshot(closed))


def test_closed_whitelist_removes_activity_and_process_fields() -> None:
    fields = _closed()
    fields.update({"phase": "human_closure_confirming", "plan_version": 1, "closed_at": fields["updated_at"]})

    paths = {issue.field_path for issue in validate_workcase_snapshot(fields)}

    assert {"phase", "plan_version", "closed_at"} <= paths


def test_schema_integration_distinguishes_unknown_fields_from_current_presence_errors(
    current_specs_repository: Path,
) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]
    fields = _human_closure_confirming()
    fields["unknown_field"] = "not registered"
    fields.pop("waiting_on")

    issues = validate_fact_object("workcase", fields, schema)
    by_path = {issue.field_path: issue.summary for issue in issues}

    assert by_path["unknown_field"] == "字段未在当前 Schema 登记"
    assert "要求该字段" in by_path["waiting_on"]


@pytest.mark.parametrize(
    ("semantic_family", "field_path"),
    [
        ("plan", "goal"),
        ("criterion_definition", "success_criterion_definitions[0].statement"),
        ("work_item", "work_items[0].result_summary"),
        ("execution_approval", "execution_approval.summary"),
        ("criterion_result", "success_criterion_results[0].summary"),
        ("result", "result_summary"),
        ("controller_check", "controller_check_summary"),
        ("independent_review", "result_reviews[0].scope"),
        ("validation", "validation_summary"),
        ("closure_proposal", "closure_proposal.proposed_disposition_summary"),
        ("human_handoff", "waiting_on"),
    ],
)
def test_current_workcase_snapshot_rejects_whitespace_only_semantic_strings(
    current_specs_repository: Path,
    semantic_family: str,
    field_path: str,
) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]
    fields = _human_closure_confirming()
    blank = " \t\n "
    if semantic_family == "plan":
        fields["goal"] = blank
    elif semantic_family == "criterion_definition":
        fields["success_criterion_definitions"][0]["statement"] = blank
    elif semantic_family == "work_item":
        fields["work_items"][0]["result_summary"] = blank
    elif semantic_family == "execution_approval":
        fields["execution_approval"]["summary"] = blank
    elif semantic_family == "criterion_result":
        fields["success_criterion_results"][0]["summary"] = blank
    elif semantic_family == "result":
        fields["result_summary"] = blank
    elif semantic_family == "controller_check":
        fields["controller_check_summary"] = blank
    elif semantic_family == "independent_review":
        fields["result_reviews"][0]["scope"] = blank
    elif semantic_family == "validation":
        fields["validation_summary"] = blank
    elif semantic_family == "closure_proposal":
        fields["closure_proposal"]["proposed_disposition_summary"] = blank
    else:
        fields["waiting_on"] = blank

    issues = validate_fact_object("workcase", fields, schema)

    assert any(issue.field_path == field_path and "空白" in issue.summary for issue in issues)


def test_workcase_semantic_layer_also_treats_whitespace_only_text_as_empty() -> None:
    fields = _human_closure_confirming()
    blank = " \t\n "
    fields["success_criterion_definitions"][0]["statement"] = blank
    fields["success_criterion_results"][0]["summary"] = blank
    fields["execution_approval"]["summary"] = blank
    fields["result_reviews"][0]["scope"] = blank
    fields["closure_proposal"]["proposed_disposition_summary"] = blank

    paths = {issue.field_path for issue in validate_workcase_snapshot(fields)}

    assert {
        "success_criterion_definitions[0].statement",
        "success_criterion_results[0].summary",
        "execution_approval.summary",
        "result_reviews[0].scope",
        "closure_proposal.proposed_disposition_summary",
    } <= paths


def test_snapshot_validation_preserves_meaningful_surrounding_whitespace(
    current_specs_repository: Path,
) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]
    fields = _human_closure_confirming()
    fields["goal"] = "  Keep this exact meaningful text.  "
    before = deepcopy(fields)

    assert validate_fact_object("workcase", fields, schema) == ()
    assert fields == before
