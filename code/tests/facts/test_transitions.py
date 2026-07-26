from __future__ import annotations

from copy import deepcopy

import pytest

from ldvh.facts.transitions import (
    _ACTIVE_PHASES,
    _GATE_WAITING_EXIT_EDGES,
    _WORKCASE_PHASE_EDGES,
    validate_fact_transition,
    validate_workcase_transition,
)
from ldvh.facts.workcase_validation import validate_workcase_snapshot


def _plan_review(version: int = 1) -> dict[str, object]:
    return {
        "reviewer": "independent-plan-reviewer",
        "reviewed_at": "2026-07-26T09:00:00+08:00",
        "subject_version": version,
        "scope": "Current plan and verification boundary",
        "conclusion": "pass",
    }


def _result_review(version: int = 1, *, resolved: bool = True) -> dict[str, object]:
    review: dict[str, object] = {
        "reviewer": "independent-result-reviewer",
        "reviewed_at": "2026-07-26T11:00:00+08:00",
        "subject_version": version,
        "scope": "Current result and validation boundary",
        "conclusion": "changes_required",
        "feedback": ["State the unverified boundary explicitly"],
    }
    if resolved:
        review["controller_resolution"] = "The result now states the unverified boundary."
    return review


def _approval(version: int = 1, *, suffix: str = "") -> dict[str, object]:
    return {
        "subject_version": version,
        "approved_at": f"2026-07-26T09:30:0{suffix or '0'}+08:00",
        "summary": "Human approved this exact plan and its stated boundary.",
    }


def _pending_item(item_id: str = "item-main") -> dict[str, object]:
    return {
        "item_id": item_id,
        "goal": f"Complete {item_id}",
        "expected_result": f"A stable result for {item_id}",
        "status": "pending",
    }


def _item_with_status(status: str, item_id: str = "item-main") -> dict[str, object]:
    item = _pending_item(item_id)
    item["status"] = status
    if status == "in_progress":
        item.update({"current_summary": "Work is in progress.", "resume_from": "Continue the bounded work."})
    elif status == "blocked":
        item.update({"current_summary": "Work reached a blocker.", "blocking_summary": "A blocker remains."})
    elif status in {"completed", "cancelled"}:
        item["result_summary"] = f"The item is {status}."
    return item


def _base() -> dict[str, object]:
    return {
        "object_id": "workcase-0001",
        "fact_type_key": "workcase",
        "title": "Bounded result",
        "created_at": "2026-07-26T08:00:00+08:00",
        "updated_at": "2026-07-26T08:30:00+08:00",
        "status": "open",
        "phase": "human_plan_confirming",
        "goal": "Deliver one bounded current-contract result",
        "scope": "Cover the selected object and exclude unrelated changes",
        "success_criterion_definitions": [
            {"criterion_id": "criterion-main", "statement": "The selected result is verified"}
        ],
        "priority": "P2",
        "plan_version": 1,
        "work_items": [_pending_item()],
        "creation_reviews": [_plan_review()],
        "waiting_on": "Human decision on the current plan",
    }


def _executing() -> dict[str, object]:
    fields = _base()
    fields.update(
        {
            "phase": "executing",
            "execution_approval": _approval(),
            "work_items": [
                {
                    **_pending_item(),
                    "status": "in_progress",
                    "current_summary": "The bounded implementation has started.",
                    "resume_from": "Continue from the current implementation checkpoint.",
                }
            ],
        }
    )
    fields.pop("creation_reviews")
    fields.pop("waiting_on")
    return fields


def _controller_checking(*, reviewed: bool = False) -> dict[str, object]:
    fields = _executing()
    fields.update(
        {
            "phase": "controller_checking",
            "result_version": 1,
            "work_items": [
                {
                    **_pending_item(),
                    "status": "completed",
                    "result_summary": "The bounded implementation result exists.",
                }
            ],
            "success_criterion_results": [
                {
                    "criterion_id": "criterion-main",
                    "outcome": "satisfied",
                    "summary": "The selected result passed its bounded validation.",
                }
            ],
            "result_summary": "The selected current-contract result was delivered.",
            "controller_check_summary": "Controller checked the result projection and its limits.",
            "validation_summary": "The bounded validation passed; unrelated behavior was not checked.",
        }
    )
    if reviewed:
        fields["result_reviews"] = [_result_review()]
    return fields


def _independent_reviewing(*, resolved: bool = True) -> dict[str, object]:
    fields = _controller_checking()
    fields["phase"] = "independent_reviewing"
    fields["result_reviews"] = [_result_review(resolved=resolved)]
    return fields


def _proposal() -> dict[str, object]:
    return {
        "proposed_outcome": "completed",
        "proposed_disposition_summary": "The bounded responsibility is complete with no residual responsibility.",
    }


def _closure_preparing() -> dict[str, object]:
    fields = _independent_reviewing()
    fields["phase"] = "closure_preparing"
    fields["closure_proposal"] = _proposal()
    return fields


def _human_closure_confirming() -> dict[str, object]:
    fields = _closure_preparing()
    fields["phase"] = "human_closure_confirming"
    fields["waiting_on"] = "Human decision on the complete closure proposal"
    return fields


def _closed() -> dict[str, object]:
    before = _human_closure_confirming()
    return {
        "object_id": before["object_id"],
        "fact_type_key": before["fact_type_key"],
        "title": before["title"],
        "created_at": before["created_at"],
        "updated_at": before["updated_at"],
        "status": "closed",
        "goal": before["goal"],
        "scope": before["scope"],
        "success_criterion_definitions": before["success_criterion_definitions"],
        "success_criterion_results": before["success_criterion_results"],
        "result_summary": before["result_summary"],
        "validation_summary": before["validation_summary"],
        "closure_outcome": "completed",
        "disposition_summary": _proposal()["proposed_disposition_summary"],
    }


def _plan_revising() -> dict[str, object]:
    fields = _base()
    fields["phase"] = "plan_revising"
    fields.pop("creation_reviews")
    fields.pop("waiting_on")
    return fields


def _pre_execution_controller(before: dict[str, object]) -> dict[str, object]:
    fields = deepcopy(before)
    fields.update(
        {
            "phase": "controller_checking",
            "result_version": 1,
            "work_items": [
                {**_pending_item(), "status": "cancelled", "result_summary": "Human stopped before execution."}
            ],
            "success_criterion_results": [
                {
                    "criterion_id": "criterion-main",
                    "outcome": "not_verified",
                    "summary": "No execution result exists to verify.",
                }
            ],
            "result_summary": "Execution did not start.",
            "controller_check_summary": "Controller confirmed that no execution fact exists.",
            "validation_summary": "No implementation validation was possible because execution did not start.",
        }
    )
    fields.pop("creation_reviews", None)
    fields.pop("waiting_on", None)
    return fields


def _assert_current_snapshot(fields: dict[str, object], label: str) -> None:
    issues = validate_workcase_snapshot(fields)
    assert issues == (), f"{label}: {[(issue.field_path, issue.summary) for issue in issues]}"


@pytest.mark.parametrize(
    ("label", "fields"),
    [
        ("human plan confirming", _base()),
        ("plan revising", _plan_revising()),
        ("executing", _executing()),
        ("controller checking", _controller_checking()),
        ("independent reviewing", _independent_reviewing()),
        ("closure preparing", _closure_preparing()),
        ("human closure confirming", _human_closure_confirming()),
        ("closed", _closed()),
    ],
)
def test_representative_current_snapshots_are_valid(label: str, fields: dict[str, object]) -> None:
    _assert_current_snapshot(fields, label)


def test_current_phase_edge_set_is_exactly_the_specified_closed_set() -> None:
    assert _WORKCASE_PHASE_EDGES == {
        ("human_plan_confirming", "executing"),
        ("human_plan_confirming", "plan_revising"),
        ("human_plan_confirming", "controller_checking"),
        ("plan_revising", "human_plan_confirming"),
        ("plan_revising", "executing"),
        ("plan_revising", "controller_checking"),
        ("executing", "plan_revising"),
        ("executing", "controller_checking"),
        ("controller_checking", "executing"),
        ("controller_checking", "plan_revising"),
        ("controller_checking", "independent_reviewing"),
        ("controller_checking", "closure_preparing"),
        ("independent_reviewing", "controller_checking"),
        ("independent_reviewing", "plan_revising"),
        ("independent_reviewing", "closure_preparing"),
        ("closure_preparing", "controller_checking"),
        ("closure_preparing", "plan_revising"),
        ("closure_preparing", "human_closure_confirming"),
        ("human_closure_confirming", "closure_preparing"),
        ("human_closure_confirming", "controller_checking"),
        ("human_closure_confirming", "plan_revising"),
    }


def test_gate_waiting_exit_edge_set_is_limited_to_fixed_human_and_reviewer_gates() -> None:
    assert _GATE_WAITING_EXIT_EDGES == {
        ("human_plan_confirming", "executing"),
        ("human_plan_confirming", "plan_revising"),
        ("human_plan_confirming", "controller_checking"),
        ("independent_reviewing", "controller_checking"),
        ("independent_reviewing", "plan_revising"),
        ("independent_reviewing", "closure_preparing"),
        ("human_closure_confirming", "closure_preparing"),
        ("human_closure_confirming", "controller_checking"),
        ("human_closure_confirming", "plan_revising"),
    }


def test_every_listed_phase_edge_has_a_current_contract_example() -> None:
    confirming = _base()
    execution_approved = deepcopy(confirming)
    execution_approved.update({"phase": "executing", "execution_approval": _approval()})
    execution_approved.pop("creation_reviews")
    execution_approved.pop("waiting_on")

    revising = _plan_revising()
    revising_to_execution = deepcopy(revising)
    revising_to_execution.update({"phase": "executing", "execution_approval": _approval()})

    executing = _executing()
    checking = _controller_checking()
    checking_reviewed = _controller_checking(reviewed=True)
    reviewing_without_review = deepcopy(checking)
    reviewing_without_review["phase"] = "independent_reviewing"
    reviewing = _independent_reviewing()
    preparing_without_proposal = deepcopy(reviewing)
    preparing_without_proposal["phase"] = "closure_preparing"
    preparing = _closure_preparing()
    human = _human_closure_confirming()

    checking_return = _executing()
    checking_return["result_version"] = 1

    pairs: list[tuple[str, dict[str, object], dict[str, object]]] = [
        ("human plan confirming -> executing", confirming, execution_approved),
        ("human plan confirming -> plan revising", confirming, revising),
        ("human plan confirming -> controller checking", confirming, _pre_execution_controller(confirming)),
        ("plan revising -> human plan confirming", revising, confirming),
        ("plan revising -> executing", revising, revising_to_execution),
        ("plan revising -> controller checking", revising, _pre_execution_controller(revising)),
        ("executing -> plan revising", executing, {**executing, "phase": "plan_revising"}),
        ("executing -> controller checking", executing, checking),
        ("controller checking -> executing", checking, checking_return),
        ("controller checking -> plan revising", checking, {**checking, "phase": "plan_revising"}),
        ("controller checking -> independent reviewing", checking, reviewing_without_review),
        (
            "controller checking -> closure preparing",
            checking_reviewed,
            {**checking_reviewed, "phase": "closure_preparing"},
        ),
        ("independent reviewing -> controller checking", reviewing, {**reviewing, "phase": "controller_checking"}),
        ("independent reviewing -> plan revising", reviewing, {**reviewing, "phase": "plan_revising"}),
        ("independent reviewing -> closure preparing", reviewing, preparing_without_proposal),
        (
            "closure preparing -> controller checking",
            preparing,
            {
                key: value
                for key, value in {**preparing, "phase": "controller_checking"}.items()
                if key != "closure_proposal"
            },
        ),
        (
            "closure preparing -> plan revising",
            preparing,
            {key: value for key, value in {**preparing, "phase": "plan_revising"}.items() if key != "closure_proposal"},
        ),
        ("closure preparing -> human closure confirming", preparing, human),
        (
            "human closure confirming -> closure preparing",
            human,
            {
                key: value
                for key, value in {**human, "phase": "closure_preparing"}.items()
                if key not in {"closure_proposal", "waiting_on"}
            },
        ),
        (
            "human closure confirming -> controller checking",
            human,
            {
                key: value
                for key, value in {**human, "phase": "controller_checking"}.items()
                if key not in {"closure_proposal", "waiting_on"}
            },
        ),
        (
            "human closure confirming -> plan revising",
            human,
            {
                key: value
                for key, value in {**human, "phase": "plan_revising"}.items()
                if key not in {"closure_proposal", "waiting_on"}
            },
        ),
    ]

    for label, before, after in pairs:
        _assert_current_snapshot(before, f"{label} before")
        _assert_current_snapshot(after, f"{label} after")
        assert validate_workcase_transition(before, after) == (), label


@pytest.mark.parametrize(
    ("before_phase", "after_phase"),
    sorted(
        (before_phase, after_phase)
        for before_phase in _ACTIVE_PHASES
        for after_phase in _ACTIVE_PHASES
        if before_phase != after_phase and (before_phase, after_phase) not in _WORKCASE_PHASE_EDGES
    ),
)
def test_unlisted_phase_edges_are_rejected(before_phase: str, after_phase: str) -> None:
    before = _controller_checking()
    before["phase"] = before_phase
    after = deepcopy(before)
    after["phase"] = after_phase

    issues = validate_workcase_transition(before, after)

    assert any(issue.field_path == "phase" and "不在当前允许边" in issue.summary for issue in issues)


def test_status_block_and_unblock_keep_phase_and_only_change_block_snapshot() -> None:
    before = _executing()
    blocked = {
        **before,
        "status": "blocked",
        "blocking_summary": "The required external service is unavailable.",
        "waiting_on": "Availability of the required external service",
    }
    assert validate_workcase_transition(before, blocked) == ()

    corrected_while_blocked = {**blocked, "title": "A corrected title"}
    assert validate_workcase_transition(blocked, corrected_while_blocked) == ()

    progressed_while_blocked = {**blocked, "summary": "Attempted progress while blocked"}
    issues = validate_workcase_transition(blocked, progressed_while_blocked)
    assert any(issue.field_path == "summary" and "blocked 同 phase" in issue.summary for issue in issues)

    advanced_while_unblocking = {**before, "phase": "controller_checking"}
    issues = validate_workcase_transition(blocked, advanced_while_unblocking)
    assert any(issue.field_path == "phase" for issue in issues)

    assert validate_workcase_transition(blocked, before) == ()


def test_block_and_unblock_can_atomically_record_only_the_causal_item_edge() -> None:
    before = _executing()
    blocked = deepcopy(before)
    blocked.update(
        {
            "status": "blocked",
            "blocking_summary": "The active item cannot continue until the required input arrives.",
            "waiting_on": "The required input",
        }
    )
    blocked["work_items"][0].update(
        {
            "status": "blocked",
            "current_summary": "Implementation reached the input boundary.",
            "blocking_summary": "The required input is unavailable.",
        }
    )
    blocked["work_items"][0].pop("resume_from")
    assert validate_workcase_transition(before, blocked) == ()

    unblocked = deepcopy(blocked)
    unblocked["status"] = "open"
    unblocked.pop("blocking_summary")
    unblocked.pop("waiting_on")
    unblocked["work_items"][0].update(
        {
            "status": "in_progress",
            "current_summary": "The required input arrived and implementation can continue.",
            "resume_from": "Continue from the input boundary.",
        }
    )
    unblocked["work_items"][0].pop("blocking_summary")
    assert validate_workcase_transition(blocked, unblocked) == ()

    reauthorized = deepcopy(unblocked)
    reauthorized["execution_approval"] = _approval(suffix="1")
    assert validate_workcase_transition(blocked, reauthorized) == ()

    wrong_version = deepcopy(reauthorized)
    wrong_version["execution_approval"] = _approval(2, suffix="1")
    issues = validate_workcase_transition(blocked, wrong_version)
    assert any(issue.field_path == "execution_approval" and "同版" in issue.summary for issue in issues)

    skipped = deepcopy(blocked)
    skipped["status"] = "open"
    skipped.pop("blocking_summary")
    skipped["work_items"][0] = {
        **_pending_item(),
        "status": "completed",
        "result_summary": "Illegally completed while unblocking.",
    }
    issues = validate_workcase_transition(blocked, skipped)
    assert any(issue.field_path.endswith(".status") and "解除" in issue.summary for issue in issues)


def test_non_executing_block_overlay_cannot_advance_item_state() -> None:
    before = _plan_revising()
    after = deepcopy(before)
    after.update(
        {
            "status": "blocked",
            "blocking_summary": "The plan cannot continue until Human input arrives.",
            "waiting_on": "Human input",
        }
    )
    after["work_items"][0].update(
        {
            "status": "blocked",
            "current_summary": "Attempted item state change outside executing.",
            "blocking_summary": "Human input is unavailable.",
        }
    )

    issues = validate_workcase_transition(before, after)

    assert any(issue.field_path == "work_items" and "非 executing" in issue.summary for issue in issues)


def test_block_overlay_ignores_all_collection_order_declared_nonsemantic() -> None:
    before = _controller_checking(reviewed=True)
    before["success_criterion_definitions"] = [
        {"criterion_id": "criterion-a", "statement": "A"},
        {"criterion_id": "criterion-b", "statement": "B"},
    ]
    before["success_criterion_results"] = [
        {"criterion_id": "criterion-a", "outcome": "satisfied", "summary": "A passed."},
        {"criterion_id": "criterion-b", "outcome": "satisfied", "summary": "B passed."},
    ]
    before["result_reviews"].append(
        {
            **_result_review(),
            "reviewer": "second-independent-reviewer",
            "reviewed_at": "2026-07-26T11:30:00+08:00",
        }
    )
    after = deepcopy(before)
    after.update({"status": "blocked", "blocking_summary": "Result checking cannot currently continue."})
    after["success_criterion_definitions"].reverse()
    after["success_criterion_results"].reverse()
    after["result_reviews"].reverse()

    assert validate_workcase_transition(before, after) == ()


def test_update_close_and_correct_are_operation_separated() -> None:
    active = _human_closure_confirming()
    closed = _closed()

    assert validate_workcase_transition(active, closed, operation="close") == ()
    assert any(
        issue.field_path == "status" for issue in validate_workcase_transition(active, closed, operation="update")
    )
    assert validate_workcase_transition(closed, {**closed, "title": "Corrected"}, operation="correct") == ()

    fake_closed = {**closed, "phase": "closed"}
    issues = validate_workcase_transition(active, fake_closed, operation="close")
    assert any(issue.field_path == "status" and "无 phase" in issue.summary for issue in issues)


def test_current_workcase_operations_reject_invalid_before_repair() -> None:
    before = {**_executing(), "priority": None}
    repaired = {**before, "priority": "P2"}
    issues = validate_workcase_transition(before, repaired, repairing_invalid_before=True)
    assert any(issue.field_path == "status" and "不接受 invalid-before" in issue.summary for issue in issues)


def test_plan_projection_normalizes_unordered_collections() -> None:
    before = _executing()
    before["success_criterion_definitions"] = [
        {"criterion_id": "criterion-a", "statement": "A"},
        {"criterion_id": "criterion-b", "statement": "B"},
    ]
    before["work_items"] = [
        {**_pending_item("item-a"), "status": "completed", "result_summary": "A done"},
        {**_pending_item("item-b"), "status": "completed", "result_summary": "B done"},
        {
            **_pending_item("item-main"),
            "status": "in_progress",
            "depends_on": ["item-a", "item-b"],
            "template_keys": ["template-b", "template-a"],
            "current_summary": "Main item started.",
            "resume_from": "Continue the main item.",
        },
    ]
    reordered = deepcopy(before)
    reordered["success_criterion_definitions"].reverse()
    reordered["work_items"].reverse()
    main = next(item for item in reordered["work_items"] if item["item_id"] == "item-main")
    main["depends_on"].reverse()
    main["template_keys"].reverse()

    assert validate_workcase_transition(before, reordered) == ()


def test_phase_freeze_does_not_assign_meaning_to_work_item_array_order() -> None:
    before = _base()
    before["work_items"] = [_pending_item("item-a"), _pending_item("item-b")]
    after = deepcopy(before)
    after.update({"phase": "executing", "execution_approval": _approval()})
    after["work_items"].reverse()
    after.pop("creation_reviews")
    after.pop("waiting_on")

    assert validate_workcase_transition(before, after) == ()


def test_plan_delta_requires_exact_increment_fresh_review_and_full_reset() -> None:
    before = _executing()
    before["phase"] = "plan_revising"
    changed_without_bump = {**before, "goal": "Deliver the revised bounded result"}

    issues = validate_workcase_transition(before, changed_without_bump)
    assert any(issue.field_path == "plan_version" and "精确加 1" in issue.summary for issue in issues)

    valid = deepcopy(changed_without_bump)
    valid.update(
        {
            "phase": "human_plan_confirming",
            "plan_version": 2,
            "creation_reviews": [_plan_review(2)],
            "waiting_on": "Human decision on revised plan version 2",
        }
    )
    valid.pop("execution_approval")
    assert validate_workcase_transition(before, valid) == ()

    retained_result = {**valid, "result_version": 1}
    issues = validate_workcase_transition(before, retained_result)
    assert any(issue.field_path == "result_version" and "必须清除" in issue.summary for issue in issues)


def test_plan_delta_new_items_start_pending_and_retained_execution_facts_are_not_reset() -> None:
    before = _executing()
    before["phase"] = "plan_revising"
    revised = deepcopy(before)
    revised.update(
        {
            "goal": "Deliver the revised plan",
            "phase": "human_plan_confirming",
            "plan_version": 2,
            "creation_reviews": [_plan_review(2)],
            "waiting_on": "Human decision on plan 2",
        }
    )
    revised.pop("execution_approval")

    reset = deepcopy(revised)
    reset["work_items"][0] = _pending_item()
    issues = validate_workcase_transition(before, reset)
    assert any(issue.field_path.endswith(".status") and "重置为 pending" in issue.summary for issue in issues)

    fabricated = deepcopy(revised)
    fabricated["work_items"].append({**_pending_item("item-new"), "status": "completed", "result_summary": "Done"})
    issues = validate_workcase_transition(before, fabricated)
    assert any(
        issue.field_path == "work_items[item-new].status" and "只能以 pending" in issue.summary for issue in issues
    )


def test_plan_delta_rejects_silent_removal_of_an_item_with_execution_facts() -> None:
    before = _executing()
    before.update({"phase": "plan_revising", "summary": "The existing cross-item checkpoint."})
    after = deepcopy(before)
    after.update(
        {
            "phase": "human_plan_confirming",
            "plan_version": 2,
            "work_items": [_pending_item("item-new")],
            "creation_reviews": [_plan_review(2)],
            "waiting_on": "Human decision on plan 2",
        }
    )
    after.pop("execution_approval")

    _assert_current_snapshot(before, "PlanDelta removal before")
    _assert_current_snapshot(after, "PlanDelta removal after")
    issues = validate_workcase_transition(before, after)

    assert any(
        issue.field_path == "work_items"
        and "可回读承接载体" in issue.summary
        and "不证明自然语言已无损吸收" in issue.summary
        for issue in issues
    )


def test_plan_delta_accepts_execution_item_removal_when_top_summary_is_updated() -> None:
    before = _executing()
    before.update({"phase": "plan_revising", "summary": "The existing cross-item checkpoint."})
    after = deepcopy(before)
    after.update(
        {
            "summary": "The removed item facts now constrain the revised plan boundary.",
            "phase": "human_plan_confirming",
            "plan_version": 2,
            "work_items": [_pending_item("item-new")],
            "creation_reviews": [_plan_review(2)],
            "waiting_on": "Human decision on plan 2",
        }
    )
    after.pop("execution_approval")

    _assert_current_snapshot(before, "PlanDelta carrier before")
    _assert_current_snapshot(after, "PlanDelta carrier after")
    assert validate_workcase_transition(before, after) == ()


def test_plan_delta_can_remove_a_pending_item_without_an_execution_fact_carrier() -> None:
    before = _plan_revising()
    before["work_items"] = [_pending_item("item-keep"), _pending_item("item-remove")]
    after = deepcopy(before)
    after.update(
        {
            "phase": "human_plan_confirming",
            "plan_version": 2,
            "work_items": [_pending_item("item-keep")],
            "creation_reviews": [_plan_review(2)],
            "waiting_on": "Human decision on plan 2",
        }
    )

    _assert_current_snapshot(before, "pending removal before")
    _assert_current_snapshot(after, "pending removal after")
    assert validate_workcase_transition(before, after) == ()


@pytest.mark.parametrize(
    ("old_status", "new_status"),
    [
        ("pending", "in_progress"),
        ("pending", "blocked"),
        ("pending", "completed"),
        ("pending", "cancelled"),
        ("in_progress", "blocked"),
        ("in_progress", "completed"),
        ("in_progress", "cancelled"),
        ("blocked", "in_progress"),
        ("blocked", "completed"),
        ("blocked", "cancelled"),
    ],
)
def test_all_listed_executing_item_edges_are_accepted(old_status: str, new_status: str) -> None:
    before = _executing()
    before["work_items"] = [
        {**_pending_item("item-dependency"), "status": "completed", "result_summary": "Dependency done"},
        _pending_item(),
        _pending_item("item-remaining"),
    ]
    item = before["work_items"][1]
    item["depends_on"] = ["item-dependency"]
    if old_status == "in_progress":
        item.update(
            {
                "status": "in_progress",
                "current_summary": "Work started.",
                "resume_from": "Continue work.",
            }
        )
    elif old_status == "blocked":
        item.update(
            {
                "status": "blocked",
                "current_summary": "Work reached a blocked point.",
                "blocking_summary": "A required input is unavailable.",
            }
        )

    after = deepcopy(before)
    changed = after["work_items"][1]
    for key in ("current_summary", "resume_from", "blocking_summary", "result_summary"):
        changed.pop(key, None)
    changed["status"] = new_status
    if new_status == "in_progress":
        changed.update({"current_summary": "Work continues.", "resume_from": "Continue the item."})
    elif new_status == "blocked":
        changed.update({"current_summary": "Work is blocked.", "blocking_summary": "A real blocker remains."})
    elif new_status in {"completed", "cancelled"}:
        changed["result_summary"] = "The item reached its actual terminal result."

    _assert_current_snapshot(before, f"{old_status} before")
    _assert_current_snapshot(after, f"{old_status} -> {new_status} after")
    assert validate_workcase_transition(before, after) == ()


_EXECUTING_ITEM_EDGES = {
    ("pending", "in_progress"),
    ("pending", "blocked"),
    ("pending", "completed"),
    ("pending", "cancelled"),
    ("in_progress", "blocked"),
    ("in_progress", "completed"),
    ("in_progress", "cancelled"),
    ("blocked", "in_progress"),
    ("blocked", "completed"),
    ("blocked", "cancelled"),
}
_ITEM_STATUSES = {"pending", "in_progress", "blocked", "completed", "cancelled"}


@pytest.mark.parametrize(
    ("old_status", "new_status"),
    sorted(
        (old_status, new_status)
        for old_status in _ITEM_STATUSES
        for new_status in _ITEM_STATUSES
        if old_status != new_status and (old_status, new_status) not in _EXECUTING_ITEM_EDGES
    ),
)
def test_every_unlisted_executing_item_edge_is_rejected(old_status: str, new_status: str) -> None:
    before = _executing()
    before["work_items"] = [_item_with_status(old_status), _pending_item("item-remaining")]
    after = deepcopy(before)
    after["work_items"][0] = _item_with_status(new_status)

    issues = validate_workcase_transition(before, after)

    assert any(
        issue.field_path == "work_items[item-main].status" and "不在当前允许边" in issue.summary for issue in issues
    )


def test_unlisted_item_edge_and_cancelled_dependency_are_rejected() -> None:
    before = _executing()
    before["work_items"] = [
        {**_pending_item("item-dependency"), "status": "cancelled", "result_summary": "Dependency cancelled"},
        {**_pending_item(), "depends_on": ["item-dependency"]},
        _pending_item("item-remaining"),
    ]
    after = deepcopy(before)
    after["work_items"][1].update(
        {
            "status": "in_progress",
            "current_summary": "Attempted start.",
            "resume_from": "Continue.",
        }
    )
    issues = validate_workcase_transition(before, after)
    assert any(issue.field_path.endswith("depends_on") and "必须为 completed" in issue.summary for issue in issues)

    terminal = _controller_checking()
    illegal = deepcopy(terminal)
    illegal["work_items"][0].update(
        {"status": "in_progress", "current_summary": "Reopened in place", "resume_from": "Continue"}
    )
    illegal["work_items"][0].pop("result_summary")
    issues = validate_workcase_transition(terminal, illegal)
    assert any(issue.field_path.endswith(".status") and "终态分类" in issue.summary for issue in issues)

    unchanged_summary = deepcopy(terminal)
    unchanged_summary["work_items"][0]["status"] = "cancelled"
    issues = validate_workcase_transition(terminal, unchanged_summary)
    assert any(issue.field_path.endswith(".result_summary") and "同时更新" in issue.summary for issue in issues)


def test_last_terminal_item_must_atomically_enter_controller_checking() -> None:
    before = _executing()
    stuck = deepcopy(before)
    stuck["work_items"][0] = {
        **_pending_item(),
        "status": "completed",
        "result_summary": "The item result is stable.",
    }
    issues = validate_workcase_transition(before, stuck)
    assert any(issue.field_path == "phase" and "AllTerminal" in issue.summary for issue in issues)

    transitioned = deepcopy(stuck)
    transitioned.update(
        {
            "phase": "controller_checking",
            "result_version": 1,
            "success_criterion_results": [
                {"criterion_id": "criterion-main", "outcome": "satisfied", "summary": "Verified."}
            ],
            "result_summary": "The result exists.",
            "controller_check_summary": "Controller checked the current result.",
            "validation_summary": "The bounded validation passed.",
        }
    )
    assert validate_workcase_transition(before, transitioned) == ()


def test_pre_execution_stop_is_the_only_approval_free_result_entry() -> None:
    before = _base()
    after = deepcopy(before)
    after.update(
        {
            "phase": "controller_checking",
            "result_version": 1,
            "work_items": [
                {**_pending_item(), "status": "cancelled", "result_summary": "Human stopped before execution."}
            ],
            "success_criterion_results": [
                {
                    "criterion_id": "criterion-main",
                    "outcome": "not_verified",
                    "summary": "No execution result exists to verify.",
                }
            ],
            "result_summary": "Execution did not start.",
            "controller_check_summary": "Controller confirmed that no execution fact exists.",
            "validation_summary": "No implementation validation was possible because execution did not start.",
        }
    )
    after.pop("creation_reviews")
    after.pop("waiting_on")
    assert validate_workcase_transition(before, after) == ()

    fabricated_approval = {**after, "execution_approval": _approval()}
    issues = validate_workcase_transition(before, fabricated_approval)
    assert any(issue.field_path == "execution_approval" and "禁止补造" in issue.summary for issue in issues)

    stale_waiting = {**after, "waiting_on": before["waiting_on"]}
    issues = validate_workcase_transition(before, stale_waiting)
    assert any(issue.field_path == "waiting_on" and "原样滞留" in issue.summary for issue in issues)


def test_result_projection_is_mutable_before_first_review_and_versioned_after_it() -> None:
    unreviewed = _controller_checking()
    corrected = {**unreviewed, "result_summary": "A corrected current result summary."}
    assert validate_workcase_transition(unreviewed, corrected) == ()

    reviewed = _controller_checking(reviewed=True)
    changed_without_bump = {**reviewed, "result_summary": "A changed reviewed result."}
    issues = validate_workcase_transition(reviewed, changed_without_bump)
    assert any(issue.field_path == "result_version" and "必须精确升版" in issue.summary for issue in issues)

    changed = deepcopy(changed_without_bump)
    changed["result_version"] = 2
    changed.pop("result_reviews")
    assert validate_workcase_transition(reviewed, changed) == ()

    fake_bump = deepcopy(reviewed)
    fake_bump["result_version"] = 2
    fake_bump.pop("result_reviews")
    issues = validate_workcase_transition(reviewed, fake_bump)
    assert any(issue.field_path == "result_version" and "未变化" in issue.summary for issue in issues)


def test_terminal_classification_correction_updates_summary_and_obeys_result_freeze() -> None:
    before = _controller_checking()
    corrected = deepcopy(before)
    corrected["work_items"][0].update(
        {
            "status": "cancelled",
            "result_summary": "New facts show the item stopped without its intended local result.",
        }
    )
    assert validate_workcase_transition(before, corrected) == ()

    reviewed = _controller_checking(reviewed=True)
    reviewed_correction = deepcopy(reviewed)
    reviewed_correction["work_items"][0].update(
        {
            "status": "cancelled",
            "result_summary": "New facts show the reviewed terminal classification was wrong.",
        }
    )
    reviewed_correction["result_version"] = 2
    reviewed_correction.pop("result_reviews")
    assert validate_workcase_transition(reviewed, reviewed_correction) == ()


def test_return_to_execution_reopens_only_actual_scope_and_preserves_or_bumps_result_identity() -> None:
    unreviewed = _controller_checking()
    returned = _executing()
    returned["result_version"] = 1
    assert validate_workcase_transition(unreviewed, returned) == ()

    reviewed = _controller_checking(reviewed=True)
    reviewed_return = deepcopy(returned)
    reviewed_return["result_version"] = 2
    assert validate_workcase_transition(reviewed, reviewed_return) == ()

    stale = deepcopy(returned)
    stale["result_reviews"] = reviewed["result_reviews"]
    issues = validate_workcase_transition(reviewed, stale)
    assert any(issue.field_path == "result_version" for issue in issues)
    assert any(issue.field_path == "result_reviews" for issue in issues)


def test_review_events_and_same_event_corrections_obey_role_and_event_boundaries() -> None:
    reviewing = _independent_reviewing()
    added = deepcopy(reviewing)
    second = _result_review()
    second.update({"reviewer": "second-independent-reviewer", "reviewed_at": "2026-07-26T11:30:00+08:00"})
    added["result_reviews"].append(second)
    assert validate_workcase_transition(reviewing, added) == ()

    forged = _controller_checking()
    forged_after = {**forged, "result_reviews": [_result_review()]}
    issues = validate_workcase_transition(forged, forged_after)
    assert any(issue.field_path == "result_reviews" and "新事件只能" in issue.summary for issue in issues)

    corrected = deepcopy(reviewing)
    corrected["result_reviews"][0]["scope"] = "Corrected scope for the same actual event"
    assert validate_workcase_transition(reviewing, corrected) == ()

    corrected_and_advanced = deepcopy(corrected)
    corrected_and_advanced["phase"] = "controller_checking"
    issues = validate_workcase_transition(reviewing, corrected_and_advanced)
    assert any(issue.field_path == "result_reviews" and "不得与 status 或 phase" in issue.summary for issue in issues)

    resolved_on_exit_before = _independent_reviewing(resolved=False)
    resolved_on_exit = deepcopy(resolved_on_exit_before)
    resolved_on_exit["phase"] = "closure_preparing"
    resolved_on_exit["result_reviews"][0]["controller_resolution"] = "Controller resolved the actual feedback."
    assert validate_workcase_transition(resolved_on_exit_before, resolved_on_exit) == ()


@pytest.mark.parametrize(("field", "invalid"), [("reviewer", []), ("reviewed_at", {}), ("subject_version", [])])
def test_invalid_review_identity_is_left_to_snapshot_validation_without_crashing(field: str, invalid: object) -> None:
    before = _base()
    after = deepcopy(before)
    after["creation_reviews"][0][field] = invalid

    issues = validate_workcase_transition(before, after)

    assert isinstance(issues, tuple)
    assert any(issue.field_path == "creation_reviews" for issue in issues)


def test_creation_review_and_execution_approval_have_separate_formation_boundaries() -> None:
    confirming = _base()
    corrected = deepcopy(confirming)
    corrected["creation_reviews"][0]["scope"] = "Corrected current-plan review scope"
    assert validate_workcase_transition(confirming, corrected) == ()

    executing = _executing()
    forged = {**executing, "execution_approval": {**_approval(), "subject_version": 2}}
    issues = validate_workcase_transition(executing, forged)
    assert any(issue.field_path == "execution_approval.subject_version" for issue in issues)

    closure = _closure_preparing()
    forged_at_closure = {**closure, "execution_approval": _approval(suffix="1")}
    issues = validate_workcase_transition(closure, forged_at_closure)
    assert any(issue.field_path == "execution_approval" and "Human" in issue.summary for issue in issues)


def test_no_execution_plan_revision_can_record_approval_withdrawal_without_fake_version_change() -> None:
    before = _plan_revising()
    before["execution_approval"] = _approval()
    after = deepcopy(before)
    after.pop("execution_approval")
    assert validate_workcase_transition(before, after) == ()

    executed_before = _executing()
    executed_before["phase"] = "plan_revising"
    executed_after = deepcopy(executed_before)
    executed_after.pop("execution_approval")
    issues = validate_workcase_transition(executed_before, executed_after)
    assert any(issue.field_path == "execution_approval" and "撤回或失效边" in issue.summary for issue in issues)


def test_result_quality_chain_and_human_return_edges_preserve_the_judgment_subject() -> None:
    controller = _controller_checking()
    reviewing = deepcopy(controller)
    reviewing["phase"] = "independent_reviewing"
    assert validate_workcase_transition(controller, reviewing) == ()

    with_review = _independent_reviewing()
    closure = deepcopy(with_review)
    closure["phase"] = "closure_preparing"
    assert validate_workcase_transition(with_review, closure) == ()

    closure["closure_proposal"] = _proposal()
    human = deepcopy(closure)
    human.update({"phase": "human_closure_confirming", "waiting_on": "Human closure decision"})
    assert validate_workcase_transition(closure, human) == ()

    returned = deepcopy(human)
    returned["phase"] = "controller_checking"
    returned.pop("closure_proposal")
    returned.pop("waiting_on")
    assert validate_workcase_transition(human, returned) == ()

    changed_during_return = {**returned, "result_summary": "Changed while returning"}
    issues = validate_workcase_transition(human, changed_during_return)
    assert any(issue.field_path == "result_summary" and "冻结" in issue.summary for issue in issues)


def test_fixed_human_and_reviewer_gate_waiting_cannot_be_carried_unchanged() -> None:
    confirming = _base()
    revising = _plan_revising()
    revising["waiting_on"] = confirming["waiting_on"]

    reviewing = _independent_reviewing()
    reviewing["waiting_on"] = "Independent Reviewer response"
    review_return = deepcopy(reviewing)
    review_return.update({"phase": "plan_revising", "waiting_on": "Independent Reviewer response"})

    human = _human_closure_confirming()
    human_return = deepcopy(human)
    human_return.update({"phase": "plan_revising", "waiting_on": human["waiting_on"]})
    human_return.pop("closure_proposal")

    pairs = [
        ("plan confirmation return", confirming, revising),
        ("independent review return", reviewing, review_return),
        ("human closure return", human, human_return),
    ]
    for label, before, after in pairs:
        _assert_current_snapshot(before, f"{label} before")
        _assert_current_snapshot(after, f"{label} after")
        issues = validate_workcase_transition(before, after)
        assert any(issue.field_path == "waiting_on" and "原样滞留" in issue.summary for issue in issues), label


def test_fixed_gate_exit_accepts_a_distinct_new_actual_waiting_without_proving_its_semantics() -> None:
    confirming = _base()
    revising = _plan_revising()
    revising["waiting_on"] = "Revised plan boundary decision"

    reviewing = _independent_reviewing()
    reviewing["waiting_on"] = "Independent Reviewer response"
    review_return = deepcopy(reviewing)
    review_return.update({"phase": "plan_revising", "waiting_on": "Human boundary decision"})

    human = _human_closure_confirming()
    human_return = deepcopy(human)
    human_return.update({"phase": "plan_revising", "waiting_on": "Revised plan decision"})
    human_return.pop("closure_proposal")

    pairs = [
        ("plan confirmation return", confirming, revising),
        ("independent review return", reviewing, review_return),
        ("human closure return", human, human_return),
    ]
    for label, before, after in pairs:
        _assert_current_snapshot(before, f"{label} before")
        _assert_current_snapshot(after, f"{label} after")
        assert validate_workcase_transition(before, after) == (), label


def test_non_gate_waiting_may_remain_unchanged_across_phase_edges() -> None:
    executing = _executing()
    executing["waiting_on"] = "External service availability"
    execution_revising = deepcopy(executing)
    execution_revising["phase"] = "plan_revising"

    revising = _plan_revising()
    revising["waiting_on"] = "External service availability"
    revising_executing = deepcopy(revising)
    revising_executing.update({"phase": "executing", "execution_approval": _approval()})

    checking = _controller_checking(reviewed=True)
    checking["waiting_on"] = "Route target availability"
    checking_preparing = deepcopy(checking)
    checking_preparing["phase"] = "closure_preparing"

    preparing = _closure_preparing()
    preparing["waiting_on"] = "Route target availability"
    preparing_checking = deepcopy(preparing)
    preparing_checking["phase"] = "controller_checking"
    preparing_checking.pop("closure_proposal")

    pairs = [
        ("executing to plan revising", executing, execution_revising),
        ("plan revising to executing", revising, revising_executing),
        ("controller checking to closure preparing", checking, checking_preparing),
        ("closure preparing to controller checking", preparing, preparing_checking),
    ]
    for label, before, after in pairs:
        _assert_current_snapshot(before, f"{label} before")
        _assert_current_snapshot(after, f"{label} after")
        assert validate_workcase_transition(before, after) == (), label


def test_closure_proposal_is_removed_and_formed_as_a_whole_not_rewritten_in_place() -> None:
    before = _closure_preparing()
    rewritten = deepcopy(before)
    rewritten["closure_proposal"]["proposed_disposition_summary"] = "A different complete disposition."
    issues = validate_workcase_transition(before, rewritten)
    assert any(issue.field_path == "closure_proposal" and "先整体移除" in issue.summary for issue in issues)

    removed = deepcopy(before)
    removed.pop("closure_proposal")
    assert validate_workcase_transition(before, removed) == ()

    formed = deepcopy(removed)
    formed["closure_proposal"] = _proposal()
    assert validate_workcase_transition(removed, formed) == ()


def test_actual_update_timestamp_must_move_forward_for_all_fact_types() -> None:
    before = {"status": "open", "updated_at": "2026-07-26T10:00:00+08:00"}
    after = {"status": "open", "updated_at": "2026-07-26T09:59:59+08:00"}

    issues = validate_fact_transition("spark", before, after)

    assert any(issue.field_path == "updated_at" and "晚于" in issue.summary for issue in issues)


def test_removed_status_edges_for_other_fact_types_stay_rejected() -> None:
    issues = validate_fact_transition("adr", {"status": "active"}, {"status": "superseded"})
    assert any(issue.field_path == "status" and "不在当前单对象更新允许边" in issue.summary for issue in issues)
