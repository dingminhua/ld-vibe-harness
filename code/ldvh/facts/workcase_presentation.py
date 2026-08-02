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

CONTRACT_IDENTITY = "workcase-current-snapshot-presentation/1"
_FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")

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
    }


def derive_workcase_presentation(
    status: object,
    phase: object,
    source_content_fingerprint: object,
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
        ]
    )


def phase_presentation() -> Mapping[str, Mapping[str, str | None]]:
    """Expose the immutable-by-convention table to deterministic tooling."""

    return PHASE_PRESENTATION
