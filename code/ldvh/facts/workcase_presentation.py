"""Deterministic presentation projection for the current WorkCase snapshot.

Specification 21 owns the lifecycle and presentation semantics.  This module
is the single Code maintenance point that transports that table to Helper and
Web consumers; it does not decide authorization, readiness, completion, or a
lifecycle transition.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping

CONTRACT_IDENTITY = "workcase-current-snapshot-presentation/2"
_FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")

#: Closed set of derived handoff reasons.  ``controller_owned`` marks a
#: Gate 1 post-approval position that must keep consuming its next control
#: step instead of yielding to a Human; the other values are safe exits or
#: fail-open categories.  ``unresolved`` always fails open to ``allow``.
HANDOFF_REASONS = (
    "closed",
    "blocked_at_current_position",
    "gate2_position_blocked",
    "gate1_waiting",
    "gate2_waiting",
    "controller_owned",
    "unresolved",
)

#: Derived open/non-blocked handoff verdict per phase.  ``blocked`` and
#: ``closed`` are overlays computed separately in :func:`derive_workcase_presentation`.
PHASE_HANDOFF: dict[str, dict[str, bool | str]] = {
    "human_plan_confirming": {"handoff_allowed": True, "handoff_reason": "gate1_waiting"},
    "plan_revising": {"handoff_allowed": False, "handoff_reason": "controller_owned"},
    "executing": {"handoff_allowed": False, "handoff_reason": "controller_owned"},
    "controller_checking": {"handoff_allowed": False, "handoff_reason": "controller_owned"},
    "independent_reviewing": {"handoff_allowed": False, "handoff_reason": "controller_owned"},
    "closure_preparing": {"handoff_allowed": False, "handoff_reason": "controller_owned"},
    "human_closure_confirming": {"handoff_allowed": True, "handoff_reason": "gate2_waiting"},
    "termination_preparing": {"handoff_allowed": False, "handoff_reason": "controller_owned"},
}

PHASE_PRESENTATION: dict[str, dict[str, str | None]] = {
    "human_plan_confirming": {
        "lifecycle_position": "human_plan_confirming",
        "handoff_narrative_key": "gate1_waiting",
        "next_required_control_step": "human_gate_1",
        "progress_group": "plan_confirmation",
        "progress_step": None,
    },
    "plan_revising": {
        "lifecycle_position": "plan_revising",
        "handoff_narrative_key": "plan_revision_in_progress",
        "next_required_control_step": "form_current_plan",
        "progress_group": "progressing",
        "progress_step": None,
    },
    "executing": {
        "lifecycle_position": "executing",
        "handoff_narrative_key": "item_execution_in_progress",
        "next_required_control_step": "advance_current_work_item",
        "progress_group": "progressing",
        "progress_step": "item_execution",
    },
    "controller_checking": {
        "lifecycle_position": "controller_checking",
        "handoff_narrative_key": "result_projection_preparing",
        "next_required_control_step": "form_complete_result_projection",
        "progress_group": "progressing",
        "progress_step": "controller_self_check",
    },
    "independent_reviewing": {
        "lifecycle_position": "independent_reviewing",
        "handoff_narrative_key": "independent_result_review_in_progress",
        "next_required_control_step": "complete_independent_result_review",
        "progress_group": "progressing",
        "progress_step": "independent_review",
    },
    "closure_preparing": {
        "lifecycle_position": "closure_preparing",
        "handoff_narrative_key": "closure_proposal_preparing",
        "next_required_control_step": "form_closure_proposal",
        "progress_group": "progressing",
        "progress_step": "controller_synthesis",
    },
    "human_closure_confirming": {
        "lifecycle_position": "human_closure_confirming",
        "handoff_narrative_key": "gate2_waiting",
        "next_required_control_step": "human_gate_2",
        "progress_group": "closure_confirmation",
        "progress_step": None,
    },
    "termination_preparing": {
        "lifecycle_position": "termination_preparing",
        "handoff_narrative_key": "termination_cleanup_in_progress",
        "next_required_control_step": "termination_cleanup",
        "progress_group": "termination_cleanup",
        "progress_step": None,
    },
}

CLOSED_PRESENTATION: dict[str, str | None] = {
    "lifecycle_position": "closed",
    "handoff_narrative_key": "closed",
    "next_required_control_step": "none",
    "progress_group": "closed",
    "progress_step": None,
}

UNRESOLVED_REASONS = (
    "missing_source_content_fingerprint",
    "missing_status",
    "unsupported_status",
    "missing_phase",
    "unexpected_phase",
    "closed_with_phase",
    "invalid_status_phase_combination",
)


def _unresolved(reason: str, source_content_fingerprint: str | None) -> dict[str, object]:
    return {
        "contract_identity": CONTRACT_IDENTITY,
        "resolution": "unresolved",
        "source_content_fingerprint": source_content_fingerprint,
        "unresolved_reason": reason,
        "handoff_allowed": True,
        "handoff_reason": "unresolved",
    }


def derive_handoff_verdict(status: object, phase: object) -> dict[str, object]:
    """Derive the closed-set handoff verdict without a lifecycle judgment.

    ``blocked`` and ``closed`` are safe exits; ``unresolved`` fails open so a
    caller never blocks an ordinary task on an unreadable snapshot.  Every
    other open position is Controller-owned after Gate 1 and yields only at a
    Human Gate or a real exit.
    """

    if not isinstance(status, str) or status not in {"open", "blocked", "closed"}:
        return {"handoff_allowed": True, "handoff_reason": "unresolved"}
    if status == "closed":
        return {"handoff_allowed": True, "handoff_reason": "closed"}
    if status == "blocked":
        if phase == "human_closure_confirming":
            return {"handoff_allowed": True, "handoff_reason": "gate2_position_blocked"}
        return {"handoff_allowed": True, "handoff_reason": "blocked_at_current_position"}
    if isinstance(phase, str) and phase in PHASE_HANDOFF:
        entry = PHASE_HANDOFF[phase]
        return {
            "handoff_allowed": bool(entry["handoff_allowed"]),
            "handoff_reason": str(entry["handoff_reason"]),
        }
    return {"handoff_allowed": True, "handoff_reason": "unresolved"}


_STAGE_GOAL_STATUSES = (
    "established",
    "not_attempted",
    "unavailable",
    "conflict",
)

_PENDING_ITEM_OBSERVATION_STATUSES = (
    "no_pending_items",
    "has_pending_items",
    "unavailable",
)


def _derive_stage_goal_status(fields: Mapping[str, object] | None) -> str:
    """Project a non-blocking observation of whether a non-persistent stage Goal
    has been declared by the Controller.

    The WorkCase fact object never persists a stage Goal (it is a host-side
    non-persistent concern), so the projection can only surface what the
    Controller has declared in the object's ``summary`` or a dedicated
    ``stage_goal_status`` field if one is ever introduced.  For now this stays
    ``not_attempted`` unless the fields carry an explicit declaration.  This
    field is purely observational; it never changes ``handoff_allowed``.
    """

    if not isinstance(fields, Mapping):
        return "not_attempted"
    declared = fields.get("stage_goal_status")
    if isinstance(declared, str) and declared in _STAGE_GOAL_STATUSES:
        return declared
    return "not_attempted"


def _derive_pending_item_observation(fields: Mapping[str, object] | None) -> str:
    """Project a non-blocking observation of whether the executing phase still
    has pending items alongside work that may have been done.

    This is an observational field only; it never changes ``handoff_allowed``
    or any transition verdict.  It surfaces the gap (Spark 缺口一方向 3)
    that the fact_object path does not detect "should-have-changed-but-didn't"
    item drift — making the gap visible without blocking.
    """

    if not isinstance(fields, Mapping):
        return "unavailable"
    work_items = fields.get("work_items")
    if not isinstance(work_items, list):
        return "unavailable"
    has_pending = any(
        isinstance(item, Mapping) and item.get("status") == "pending"
        for item in work_items
    )
    return "has_pending_items" if has_pending else "no_pending_items"


def derive_workcase_presentation(
    status: object,
    phase: object,
    source_content_fingerprint: object,
    fields: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Project a just-read WorkCase snapshot without making semantic judgments."""

    fingerprint = (
        source_content_fingerprint
        if isinstance(source_content_fingerprint, str) and _FINGERPRINT.fullmatch(source_content_fingerprint)
        else None
    )
    if fingerprint is None:
        return _unresolved("missing_source_content_fingerprint", None)
    if status is None or status == "":
        return _unresolved("missing_status", fingerprint)
    if not isinstance(status, str) or status not in {"open", "blocked", "closed"}:
        return _unresolved("unsupported_status", fingerprint)

    if status == "closed":
        if phase not in {None, ""}:
            return _unresolved("closed_with_phase", fingerprint)
        projected = dict(CLOSED_PRESENTATION)
        projected.update(
            contract_identity=CONTRACT_IDENTITY,
            resolution="resolved",
            source_content_fingerprint=fingerprint,
            blocking_overlay=False,
            stage_goal_status=_derive_stage_goal_status(fields),
            pending_item_observation=_derive_pending_item_observation(fields),
            **derive_handoff_verdict(status, phase),
        )
        return projected

    if phase is None or phase == "":
        return _unresolved("missing_phase", fingerprint)
    if not isinstance(phase, str):
        return _unresolved("invalid_status_phase_combination", fingerprint)
    phase_projection = PHASE_PRESENTATION.get(phase)
    if phase_projection is None:
        return _unresolved("unexpected_phase", fingerprint)

    projected = dict(phase_projection)
    blocked = status == "blocked"
    if blocked:
        projected["handoff_narrative_key"] = (
            "gate2_position_blocked" if phase == "human_closure_confirming" else "blocked_at_current_position"
        )
    projected.update(
        contract_identity=CONTRACT_IDENTITY,
        resolution="resolved",
        source_content_fingerprint=fingerprint,
        blocking_overlay=blocked,
        stage_goal_status=_derive_stage_goal_status(fields),
        pending_item_observation=_derive_pending_item_observation(fields),
        **derive_handoff_verdict(status, phase),
    )
    return projected


def _typescript_literal(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, separators=(",", ": "))


def render_typescript_contract() -> str:
    """Render the generated TypeScript data contract byte-for-byte."""

    phases = list(PHASE_PRESENTATION)
    return "\n".join(
        [
            "// Generated by code/tools/generate_workcase_presentation_contract.py.",
            "// Do not edit by hand; specification 21 owns the semantics.",
            "",
            f"export const WORKCASE_PRESENTATION_CONTRACT_IDENTITY = {json.dumps(CONTRACT_IDENTITY)} as const;",
            "",
            f"export const WORKCASE_CURRENT_PHASES = {_typescript_literal(phases)} as const;",
            "",
            f"export const WORKCASE_PHASE_PRESENTATION = {_typescript_literal(PHASE_PRESENTATION)} as const;",
            "",
            f"export const WORKCASE_CLOSED_PRESENTATION = {_typescript_literal(CLOSED_PRESENTATION)} as const;",
            "",
            "export const WORKCASE_PRESENTATION_UNRESOLVED_REASONS = "
            f"{_typescript_literal(list(UNRESOLVED_REASONS))} as const;",
            "",
            "export const WORKCASE_PRESENTATION_HANDOFF_REASONS = "
            f"{_typescript_literal(list(HANDOFF_REASONS))} as const;",
            "",
            f"export const WORKCASE_PHASE_HANDOFF = {_typescript_literal(PHASE_HANDOFF)} as const;",
            "",
        ]
    )


def phase_presentation() -> Mapping[str, Mapping[str, str | None]]:
    """Expose the immutable-by-convention table to deterministic tooling."""

    return PHASE_PRESENTATION


def phase_handoff() -> Mapping[str, Mapping[str, object]]:
    """Expose the immutable-by-convention handoff table to deterministic tooling."""

    return PHASE_HANDOFF
