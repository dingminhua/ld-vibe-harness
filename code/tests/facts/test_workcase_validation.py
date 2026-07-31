from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.validation import validate_fact_object
from ldvh.facts.workcase_projection import approval_baseline_fingerprint
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


def _authorization() -> dict[str, object]:
    return {
        "authorized_actions": [
            {
                "action_id": "authorization-bounded-write",
                "summary": "Write the bounded result.",
                "target_scope": "The selected implementation files.",
                "effect_scope": "Workspace writes and read-only independent review.",
                "risk_summary": "Unrelated existing changes must be preserved.",
                "rollback_summary": "Revert only the bounded newly written content.",
                "rule_refs": ["specs/21", "specs/06"],
            }
        ],
        "action_ceiling": "No external publication or unrelated object changes.",
        "prohibited_actions": ["push", "publish"],
        "allowed_adjustments": "The bounded implementation method may change.",
        "verification_and_rollback": "Run bounded checks and preserve recoverable checkpoints.",
        "out_of_bounds_handling": "Cancel affected items and converge to closure.",
    }


def _approval(fields: dict[str, object] | None = None) -> dict[str, object]:
    baseline = fields if fields is not None else _base("executing")
    return {
        "subject_version": 1,
        "approved_at": "2026-07-26T10:20:00+08:00",
        "summary": "Human approved this exact plan.",
        "baseline_fingerprint": approval_baseline_fingerprint(baseline),
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
        "execution_authorization": _authorization(),
        "phase": phase,
        "plan_version": 1,
        "work_items": [_pending_item()],
        "creation_reviews": [_review()],
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
            "execution_approval": _approval(fields),
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
        {**_base("plan_revising"), "execution_approval": _approval()},
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
    fields["execution_approval"] = _approval(fields)
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


def test_pre_gate_plan_revising_requires_noexec_and_forbids_result_shape() -> None:
    valid = _base("plan_revising")
    valid["waiting_on"] = "Independent reviewer input"
    assert validate_workcase_snapshot(valid) == ()

    started = deepcopy(valid)
    started["work_items"][0].update(
        {
            "status": "in_progress",
            "current_summary": "Execution must not have started before Gate1.",
            "resume_from": "No authorized resume point exists.",
        }
    )
    assert any(
        issue.field_path == "execution_approval" and "NoExec" in issue.summary
        for issue in validate_workcase_snapshot(started)
    )

    versioned = {**valid, "result_version": 1}
    assert any(
        issue.field_path == "execution_approval" and "禁止结果版本" in issue.summary
        for issue in validate_workcase_snapshot(versioned)
    )


def test_pre_execution_stop_can_reach_result_chain_without_fabricated_approval() -> None:
    fields = _complete_result("human_closure_confirming")
    fields.pop("execution_approval")
    fields.pop("execution_authorization")
    fields.pop("creation_reviews")
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
    fields["execution_approval"]["baseline_fingerprint"] = approval_baseline_fingerprint(fields)
    before = deepcopy(fields)

    assert validate_fact_object("workcase", fields, schema) == ()
    assert fields == before


def _contributed(fact_type_key: str, object_id: str) -> dict[str, object]:
    return {
        "relation_key": "contributed-to",
        "target": {
            "governed_project_id": "current-project",
            "fact_type_key": fact_type_key,
            "object_id": object_id,
        },
    }


def _file_asset_relation(
    object_id: str = "file-asset-0007",
    *,
    relation_key: str = "has-file-asset",
    fact_type_key: str = "file-asset",
) -> dict[str, object]:
    return {
        "relation_key": relation_key,
        "target": {
            "governed_project_id": "current-project",
            "fact_type_key": fact_type_key,
            "object_id": object_id,
        },
    }


def test_has_file_asset_is_valid_in_active_and_closed_workcase_snapshots() -> None:
    active = _base("executing")
    active["execution_approval"] = _approval()
    active["relations"] = [_file_asset_relation()]
    closed = _closed()
    closed["relations"] = [_file_asset_relation()]

    assert validate_workcase_snapshot(active) == ()
    assert validate_workcase_snapshot(closed) == ()


def test_file_asset_must_use_has_file_asset_and_exact_file_asset_identity() -> None:
    related = _base("executing")
    related["execution_approval"] = _approval()
    related["relations"] = [_file_asset_relation(relation_key="related-to")]
    wrong_type = _base("executing")
    wrong_type["execution_approval"] = _approval()
    wrong_type["relations"] = [_file_asset_relation(fact_type_key="study", object_id="study-0007")]
    wrong_id = _base("executing")
    wrong_id["execution_approval"] = _approval()
    wrong_id["relations"] = [_file_asset_relation(object_id="study-0007")]

    assert any(issue.field_path == "relations[0].target.object_id" for issue in validate_workcase_snapshot(related))
    assert any(
        issue.field_path == "relations[0].target.fact_type_key"
        for issue in validate_workcase_snapshot(wrong_type)
    )
    assert any(issue.field_path == "relations[0].target.object_id" for issue in validate_workcase_snapshot(wrong_id))


def test_contributed_to_targets_pitfall_in_active_and_closed_snapshots() -> None:
    fact_type_key = "pitfall"
    object_id = "pitfall-0007"
    active = _base("executing")
    active["execution_approval"] = _approval()
    active["relations"] = [_contributed(fact_type_key, object_id)]
    assert validate_workcase_snapshot(active) == ()

    closed = _closed()
    closed["relations"] = [_contributed(fact_type_key, object_id)]
    assert validate_workcase_snapshot(closed) == ()


def test_contributed_to_rejects_non_pitfall_targets_and_mismatched_object_id() -> None:
    for fact_type_key, object_id in (
        ("workcase", "workcase-0007"),
        ("study", "study-0007"),
        ("spark", "spark-0007"),
        ("adr", "adr-0007"),
    ):
        fields = _base("executing")
        fields["execution_approval"] = _approval()
        fields["relations"] = [_contributed(fact_type_key, object_id)]
        issues = validate_workcase_snapshot(fields)
        assert any(issue.field_path == "relations[0].target.fact_type_key" for issue in issues)

    mismatched = _base("executing")
    mismatched["execution_approval"] = _approval()
    mismatched["relations"] = [_contributed("pitfall", "adr-0007")]
    issues = validate_workcase_snapshot(mismatched)
    assert any(issue.field_path == "relations[0].target.object_id" for issue in issues)


def test_human_closure_confirming_retains_contributed_to_but_rejects_depends_on() -> None:
    fields = _human_closure_confirming()
    fields["relations"] = [_contributed("pitfall", "pitfall-0007")]
    assert validate_workcase_snapshot(fields) == ()

    fields["relations"] = [
        {
            "relation_key": "depends-on",
            "target": {
                "governed_project_id": "current-project",
                "fact_type_key": "workcase",
                "object_id": "workcase-0007",
            },
        }
    ]
    issues = validate_workcase_snapshot(fields)
    assert any(
        issue.field_path == "relations[0].relation_key" and "depends-on" in issue.summary for issue in issues
    )


def test_closed_contributed_to_is_retained_but_never_counts_as_residual_disposition() -> None:
    completed = _closed()
    completed["relations"] = [_contributed("pitfall", "pitfall-0007")]
    assert validate_workcase_snapshot(completed) == ()

    partial = _closed()
    partial["closure_outcome"] = "not-achieved"
    partial["success_criterion_results"][0].update(
        {"outcome": "not_satisfied", "summary": "The criterion did not form a satisfied result."}
    )
    partial["disposition_summary"] = "The remaining responsibility was explicitly addressed."
    partial["relations"] = [_contributed("pitfall", "pitfall-0007")]
    issues = validate_workcase_snapshot(partial)
    assert any(issue.field_path == "disposition_summary" for issue in issues)

    partial["residual_responsibilities"] = [
        {"residual_id": "residual-result", "summary": "The unmet criterion responsibility is accepted as stopped."}
    ]
    assert validate_workcase_snapshot(partial) == ()


def test_suggest_spark_requires_one_complete_constrained_suggestion_and_never_a_future_id() -> None:
    fields = _human_closure_confirming()
    fields["closure_proposal"] = {
        "proposed_outcome": "not-achieved",
        "proposed_disposition_summary": "当前责任受外部条件限制，Human 可先关闭并日后独立判断 Spark。",
        "residual_decisions": [
            {
                "residual_id": "residual-limited",
                "summary": "外部条件恢复后继续验证当前责任。",
                "proposed_disposition": "suggest_spark",
                "spark_suggestion_id": "suggestion-limited",
            }
        ],
        "spark_suggestions": [
            {
                "suggestion_id": "suggestion-limited",
                "suggestion_kind": "constrained_responsibility",
                "summary": "外部条件恢复后继续验证。",
                "restriction_reason": "当前缺少只能由外部系统提供的输入。",
                "impact_summary": "成功标准当前不能验证。",
                "resume_condition": "外部输入可用。",
                "follow_up_summary": "由 Human 日后判断是否建立 Spark。",
            }
        ],
    }
    fields["success_criterion_results"][0].update(
        {"outcome": "not_satisfied", "summary": "外部条件限制使当前标准未满足。"}
    )

    assert validate_workcase_snapshot(fields) == ()

    fields["closure_proposal"]["spark_suggestions"][0]["object_id"] = "spark-9999"
    issues = validate_workcase_snapshot(fields)
    assert any("object_id" in (issue.field_path or "") for issue in issues)


def test_completed_allows_only_follow_up_opportunity_suggestions() -> None:
    fields = _closed()
    fields["spark_suggestions"] = [
        {
            "suggestion_id": "suggestion-opportunity",
            "suggestion_kind": "follow_up_opportunity",
            "summary": "结果中出现了一个范围外优化机会。",
            "follow_up_summary": "由 Human 日后独立判断是否建立 Spark。",
        }
    ]
    assert validate_workcase_snapshot(fields) == ()

    fields["spark_suggestions"][0].update(
        {
            "suggestion_kind": "constrained_responsibility",
            "restriction_reason": "当前受限。",
            "impact_summary": "当前结果受影响。",
            "resume_condition": "限制解除。",
        }
    )
    issues = validate_workcase_snapshot(fields)
    assert any(issue.field_path == "spark_suggestions" and "completed" in issue.summary for issue in issues)


def test_completed_proposal_rejects_constrained_responsibility_suggestions() -> None:
    fields = _human_closure_confirming()
    fields["closure_proposal"]["spark_suggestions"] = [
        {
            "suggestion_id": "suggestion-invalid-constraint",
            "suggestion_kind": "constrained_responsibility",
            "summary": "这不是 completed 可以携带的受限责任。",
            "restriction_reason": "仍有条件限制。",
            "impact_summary": "当前责任仍受影响。",
            "resume_condition": "限制解除。",
            "follow_up_summary": "日后继续当前责任。",
        }
    ]

    issues = validate_workcase_snapshot(fields)

    assert any(
        issue.field_path == "closure_proposal.spark_suggestions" and "completed" in issue.summary
        for issue in issues
    )
