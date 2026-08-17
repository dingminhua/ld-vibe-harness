from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts.workcase_item_event import (
    WorkCaseItemEvent,
    WorkCaseItemEventError,
    project_workcase_item_event,
)
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.workcase_update_request import parse_update_workcase_request
from ldvh.helper.requests import CommonRequest

EVENT_AT = "2026-08-15T01:00:00Z"


def _current_item(status: str = "in_progress") -> dict[str, object]:
    item: dict[str, object] = {
        "item_id": "item-main",
        "goal": "Do the bounded work",
        "expected_result": "One bounded result",
        "status": status,
    }
    if status == "in_progress":
        item.update({"current_summary": "before", "resume_from": "before next"})
    return item


def _fields(status: str = "in_progress") -> dict[str, object]:
    return {
        "object_id": "workcase-0001",
        "fact_type_key": "workcase",
        "created_at": "2026-08-15T00:00:00Z",
        "updated_at": "2026-08-15T00:30:00Z",
        "title": "Bounded work",
        "status": "open",
        "phase": "executing",
        "work_items": [_current_item(status)],
        "change_log": [
            {
                "signature": {
                    "product_name": "existing",
                    "model_name": "existing",
                },
                "at": "2026-08-15T00:30:00Z",
                "summary": "Existing event",
            }
        ],
    }


def test_start_item_event_changes_only_the_target_checkpoint_and_appends_log() -> None:
    before = _fields("pending")
    event = WorkCaseItemEvent(
        "start-work-item",
        "item-main",
        "Started item-main.",
        current_summary="started",
        resume_from="continue here",
    )

    after = project_workcase_item_event(before, event, EVENT_AT)

    assert "object_id" not in after
    assert "created_at" not in after
    assert "updated_at" not in after
    assert after["phase"] == "executing"
    item = after["work_items"][0]
    assert item["status"] == "in_progress"
    assert item["current_summary"] == "started"
    assert item["resume_from"] == "continue here"
    assert len(before["change_log"]) == 1
    assert after["change_log"][-1]["summary"] == "Started item-main."
    assert set(after["change_log"][-1]["signature"]) == {
        "product_name",
        "model_name",
    }


def test_checkpoint_event_replaces_only_checkpoint_text() -> None:
    event = WorkCaseItemEvent(
        "update-work-item-checkpoint",
        "item-main",
        "Updated item-main checkpoint.",
        current_summary="after",
        resume_from="after next",
    )

    after = project_workcase_item_event(_fields(), event, EVENT_AT)

    item = after["work_items"][0]
    assert item["status"] == "in_progress"
    assert item["current_summary"] == "after"
    assert item["resume_from"] == "after next"


def test_checkpoint_noop_is_rejected_before_change_log_append() -> None:
    before = _fields()
    event = WorkCaseItemEvent(
        "update-work-item-checkpoint",
        "item-main",
        "Would be a no-op.",
        current_summary="before",
        resume_from="before next",
    )

    with pytest.raises(WorkCaseItemEventError, match="no-op"):
        project_workcase_item_event(before, event, EVENT_AT)

    assert len(before["change_log"]) == 1


def test_complete_item_event_removes_checkpoint_and_sets_result() -> None:
    event = WorkCaseItemEvent(
        "complete-work-item",
        "item-main",
        "Completed item-main.",
        result_summary="stable result",
    )

    after = project_workcase_item_event(_fields(), event, EVENT_AT)

    item = after["work_items"][0]
    assert item["status"] == "completed"
    assert item["result_summary"] == "stable result"
    assert "current_summary" not in item
    assert "resume_from" not in item


@pytest.mark.parametrize(
    ("arguments", "problem"),
    [
        ({}, "必须且只能出现一个"),
        ({"fact_object": {}, "item_event": {}}, "必须且只能出现一个"),
        (
            {
                "item_event": {
                    "event_key": "start-work-item",
                    "item_id": "item-main",
                    "current_summary": "started",
                    "resume_from": "continue",
                    "change_summary": "started",
                    "unknown": "forbidden",
                }
            },
            "未知字段",
        ),
        (
            {
                "item_event": {
                    "event_key": "complete-work-item",
                    "item_id": "item-main",
                    "result_summary": "   ",
                    "change_summary": "completed",
                }
            },
            "result_summary",
        ),
    ],
)
def test_update_request_enforces_xor_and_exact_event_union(
    arguments: dict[str, object], problem: str
) -> None:
    complete_arguments = {
        "fact_ref": {"object_uid": "0198f1c7-8a2b-7c3d-9e4f-123456789abc"},
        "expected_content_fingerprint": "a" * 64,
        **arguments,
    }
    request = CommonRequest(None, (), complete_arguments, None, {}, ())

    parsed = parse_update_workcase_request(
        request,
        OperationExecutionContext(Path("/project"), EVENT_AT),
    )

    assert parsed.request is None
    assert any(problem in item for item in parsed.problems)


def test_update_request_parses_one_strict_item_event() -> None:
    request = CommonRequest(
        None,
        (),
        {
            "fact_ref": {"object_uid": "0198f1c7-8a2b-7c3d-9e4f-123456789abc"},
            "expected_content_fingerprint": "a" * 64,
            "item_event": {
                "event_key": "complete-work-item",
                "item_id": "item-main",
                "result_summary": "stable result",
                "change_summary": "Completed item-main.",
            },
        },
        None,
        {},
        (),
    )

    parsed = parse_update_workcase_request(
        request,
        OperationExecutionContext(Path("/project"), EVENT_AT),
    )

    assert parsed.problems == ()
    assert parsed.request is not None
    assert parsed.request.item_event == WorkCaseItemEvent(
        "complete-work-item",
        "item-main",
        "Completed item-main.",
        result_summary="stable result",
    )
    assert parsed.request.fact_object == {}
