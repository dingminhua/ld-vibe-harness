from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts.workcase_presentation import (
    CONTRACT_IDENTITY,
    PHASE_HANDOFF,
    PHASE_PRESENTATION,
    derive_handoff_verdict,
    derive_workcase_presentation,
    render_typescript_contract,
)

FINGERPRINT = "a" * 64


@pytest.mark.parametrize("phase, expected", PHASE_PRESENTATION.items())
def test_open_phase_matrix_is_resolved(phase: str, expected: dict[str, str | None]) -> None:
    projection = derive_workcase_presentation("open", phase, FINGERPRINT)

    assert projection == {
        **expected,
        "contract_identity": CONTRACT_IDENTITY,
        "resolution": "resolved",
        "source_content_fingerprint": FINGERPRINT,
        "blocking_overlay": False,
        "stage_goal_status": "not_attempted",
        "pending_item_observation": "unavailable",
        **PHASE_HANDOFF[phase],
    }


@pytest.mark.parametrize("phase, expected", PHASE_PRESENTATION.items())
def test_blocked_phase_matrix_preserves_position_and_overlays_blocker(
    phase: str,
    expected: dict[str, str | None],
) -> None:
    projection = derive_workcase_presentation("blocked", phase, FINGERPRINT)

    assert projection["lifecycle_position"] == expected["lifecycle_position"]
    assert projection["progress_group"] == expected["progress_group"]
    assert projection["progress_step"] == expected["progress_step"]
    assert projection["next_required_control_step"] == expected["next_required_control_step"]
    assert projection["blocking_overlay"] is True
    expected_narrative = (
        "gate2_position_blocked" if phase == "human_closure_confirming" else "blocked_at_current_position"
    )
    assert projection["handoff_narrative_key"] == expected_narrative
    assert projection["handoff_allowed"] is True
    assert projection["handoff_reason"] == expected_narrative


def test_only_open_human_closure_confirming_uses_gate2_waiting() -> None:
    projections = [
        derive_workcase_presentation(status, phase, FINGERPRINT)
        for status in ("open", "blocked")
        for phase in PHASE_PRESENTATION
    ]

    gate2 = [projection for projection in projections if projection.get("handoff_narrative_key") == "gate2_waiting"]
    assert len(gate2) == 1
    assert gate2[0]["lifecycle_position"] == "human_closure_confirming"
    assert gate2[0]["blocking_overlay"] is False
    assert gate2[0]["handoff_allowed"] is True
    assert gate2[0]["handoff_reason"] == "gate2_waiting"
    for phase in ("independent_reviewing", "closure_preparing"):
        assert derive_workcase_presentation("open", phase, FINGERPRINT)["handoff_narrative_key"] != "gate2_waiting"


def test_controller_owned_open_phases_deny_handoff_with_the_closed_reason() -> None:
    for phase, expected in PHASE_HANDOFF.items():
        if phase in {"human_plan_confirming", "human_closure_confirming"}:
            continue
        projection = derive_workcase_presentation("open", phase, FINGERPRINT)
        assert projection["resolution"] == "resolved"
        assert projection["handoff_allowed"] is False
        assert projection["handoff_reason"] == "controller_owned"
        assert expected["handoff_allowed"] is False


def test_gate_waiting_open_phases_allow_handoff_with_the_gate_reason() -> None:
    gate1 = derive_workcase_presentation("open", "human_plan_confirming", FINGERPRINT)
    assert gate1["handoff_allowed"] is True
    assert gate1["handoff_reason"] == "gate1_waiting"
    gate2 = derive_workcase_presentation("open", "human_closure_confirming", FINGERPRINT)
    assert gate2["handoff_allowed"] is True
    assert gate2["handoff_reason"] == "gate2_waiting"


def test_closed_requires_phase_absence() -> None:
    closed = derive_workcase_presentation("closed", None, FINGERPRINT)
    invalid = derive_workcase_presentation("closed", "human_closure_confirming", FINGERPRINT)

    assert closed["resolution"] == "resolved"
    assert closed["handoff_narrative_key"] == "closed"
    assert closed["next_required_control_step"] == "none"
    assert closed["handoff_allowed"] is True
    assert closed["handoff_reason"] == "closed"
    assert invalid == {
        "contract_identity": CONTRACT_IDENTITY,
        "resolution": "unresolved",
        "source_content_fingerprint": FINGERPRINT,
        "unresolved_reason": "closed_with_phase",
        "handoff_allowed": True,
        "handoff_reason": "unresolved",
    }


@pytest.mark.parametrize(
    ("status", "phase", "fingerprint", "reason"),
    [
        ("open", "executing", None, "missing_source_content_fingerprint"),
        (None, "executing", FINGERPRINT, "missing_status"),
        ("paused", "executing", FINGERPRINT, "unsupported_status"),
        ("open", None, FINGERPRINT, "missing_phase"),
        ("open", "reviewing", FINGERPRINT, "unexpected_phase"),
        ("open", 3, FINGERPRINT, "invalid_status_phase_combination"),
    ],
)
def test_unresolved_projection_never_guesses_lifecycle_or_handoff(
    status: object,
    phase: object,
    fingerprint: object,
    reason: str,
) -> None:
    projection = derive_workcase_presentation(status, phase, fingerprint)

    assert projection["resolution"] == "unresolved"
    assert projection["unresolved_reason"] == reason
    assert not {
        "lifecycle_position",
        "handoff_narrative_key",
        "next_required_control_step",
        "progress_group",
        "progress_step",
    }.intersection(projection)
    assert projection["handoff_allowed"] is True
    assert projection["handoff_reason"] == "unresolved"


def test_handoff_verdict_fails_open_for_unknown_inputs() -> None:
    assert derive_handoff_verdict(None, "executing") == {"handoff_allowed": True, "handoff_reason": "unresolved"}
    assert derive_handoff_verdict("paused", "executing") == {"handoff_allowed": True, "handoff_reason": "unresolved"}
    assert derive_handoff_verdict("open", "unknown") == {"handoff_allowed": True, "handoff_reason": "unresolved"}


def test_generated_web_contract_matches_python_renderer() -> None:
    target = Path(__file__).resolve().parents[3] / "web" / "shared" / "workcasePresentationContract.generated.ts"
    assert target.read_text(encoding="utf-8") == render_typescript_contract()
