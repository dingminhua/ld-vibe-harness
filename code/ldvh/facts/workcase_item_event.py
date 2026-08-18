"""Strict WorkCase item-event projection onto one complete current after object."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Literal

from ldvh.facts.update_application import MANAGED_FIELDS

_TERMINAL_ITEM_STATUSES = frozenset({"completed", "cancelled"})

WorkCaseItemEventKey = Literal[
    "start-work-item",
    "update-work-item-checkpoint",
    "complete-work-item",
    "cancel-work-item",
]


@dataclass(frozen=True, slots=True)
class WorkCaseItemEvent:
    """One parsed event from the closed update-workcase input union."""

    event_key: WorkCaseItemEventKey
    item_id: str
    change_summary: str
    current_summary: str | None = None
    resume_from: str | None = None
    result_summary: str | None = None


class WorkCaseItemEventError(ValueError):
    """A current snapshot cannot accept the requested item event."""


def _event_item(fields: Mapping[str, object], item_id: str) -> dict[str, object]:
    work_items = fields.get("work_items")
    if not isinstance(work_items, list):
        raise WorkCaseItemEventError("当前 WorkCase 缺少完整 work_items")
    matches = [item for item in work_items if isinstance(item, dict) and item.get("item_id") == item_id]
    if len(matches) != 1:
        raise WorkCaseItemEventError("item_event.item_id 必须在当前 WorkCase 中精确命中一项")
    return matches[0]


def _project_all_terminal_phase_transition(supplied: dict[str, object]) -> None:
    """When an item becomes terminal and leaves no non-terminal item, transition
    executing -> controller_checking in the same transaction (21 §6.3.3).

    The event projector performs the same phase projection the fact_object path would;
    publication still flows through the shared WorkCase publish function, which
    re-validates the full transition including AllTerminal -> controller_checking.
    """
    work_items = supplied.get("work_items")
    if not isinstance(work_items, list):
        return
    if not all(
        isinstance(_item, dict) and _item.get("status") in _TERMINAL_ITEM_STATUSES
        for _item in work_items
    ):
        return
    if supplied.get("phase") == "executing":
        supplied["phase"] = "controller_checking"
        # First result projection for this plan version starts at 1 (21 §6.3.3).
        if "result_version" not in supplied:
            supplied["result_version"] = 1


def project_workcase_item_event(
    fields: Mapping[str, object],
    event: WorkCaseItemEvent,
    event_at: str,
) -> dict[str, object]:
    """Project an event onto a complete after; publication remains elsewhere."""

    if fields.get("status") != "open" or fields.get("phase") != "executing":
        raise WorkCaseItemEventError("item_event 只接受 status=open, phase=executing 的当前 WorkCase")

    supplied = {key: deepcopy(value) for key, value in fields.items() if key not in MANAGED_FIELDS}
    item = _event_item(supplied, event.item_id)
    status = item.get("status")

    if event.event_key == "start-work-item":
        if status != "pending":
            raise WorkCaseItemEventError("start-work-item 的目标 item 必须为 pending")
        item.update(
            {
                "status": "in_progress",
                "current_summary": event.current_summary,
                "resume_from": event.resume_from,
            }
        )
    elif event.event_key == "update-work-item-checkpoint":
        if status != "in_progress":
            raise WorkCaseItemEventError("update-work-item-checkpoint 的目标 item 必须为 in_progress")
        if (
            item.get("current_summary") == event.current_summary
            and item.get("resume_from") == event.resume_from
        ):
            raise WorkCaseItemEventError("update-work-item-checkpoint 与当前值相同，是禁止写入的 no-op")
        item["current_summary"] = event.current_summary
        item["resume_from"] = event.resume_from
    elif event.event_key == "complete-work-item":
        if status != "in_progress":
            raise WorkCaseItemEventError("complete-work-item 的目标 item 必须为 in_progress")
        item["status"] = "completed"
        item.pop("current_summary", None)
        item.pop("resume_from", None)
        item.pop("blocking_summary", None)
        item["result_summary"] = event.result_summary
        _project_all_terminal_phase_transition(supplied)
    elif event.event_key == "cancel-work-item":
        if status not in ("in_progress", "blocked"):
            raise WorkCaseItemEventError("cancel-work-item 的目标 item 必须为 in_progress 或 blocked")
        item["status"] = "cancelled"
        item.pop("current_summary", None)
        item.pop("resume_from", None)
        item.pop("blocking_summary", None)
        item["result_summary"] = event.result_summary
        _project_all_terminal_phase_transition(supplied)
    else:
        raise WorkCaseItemEventError(f"未知 item_event event_key: {event.event_key}")

    change_log = supplied.get("change_log")
    if not isinstance(change_log, list):
        raise WorkCaseItemEventError("当前 WorkCase 缺少可追加的 change_log")
    change_log.append(
        {
            "signature": {
                "product_name": None,
                "model_name": None,
            },
            "at": event_at,
            "summary": event.change_summary,
        }
    )
    return supplied


__all__ = [
    "WorkCaseItemEvent",
    "WorkCaseItemEventError",
    "WorkCaseItemEventKey",
    "project_workcase_item_event",
]
