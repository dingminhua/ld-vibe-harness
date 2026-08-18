"""Real-scenario validation tests for ADR/Pitfall differentiated triggers.

These tests simulate real-world scenarios where the AI would consume
F2 cards and need to apply light_exclusion (ADR) or anchor_type (Pitfall)
to make correct filtering decisions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ldvh.facts.repository import FactReadResult
from ldvh.helper.operations.fact_candidate_operation import (
    _compute_trigger_reason,
    _compute_matched_fields,
    _compute_exclusion_candidates,
    _compute_anchor_type,
    _card,
)


class _MockDomain:
    def __init__(self, card_layer: str = "F2") -> None:
        self.card_layer = card_layer


def _make_read(fact_type_key: str, fields: dict[str, Any]) -> FactReadResult:
    return FactReadResult(
        canonical_path=f"ldvh-base/{fact_type_key}s/{fact_type_key}-0001.md",
        carrier="md",
        check_status="ok",
        fields=fields,
        body=None,
        issues=(),
    )


# ---------------------------------------------------------------------------
# ADR real scenarios
# ---------------------------------------------------------------------------

class TestADRRealScenarios:
    """ADR: triggered = signal_hit AND NOT light_exclusion"""

    def test_scenario_architecture_choice_matches_decision_question(self) -> None:
        """Scenario: AI is choosing between React and Vue.
        ADR says '前端使用 React' → signal_hit via decision_question.
        Should trigger (no exclusion)."""
        read = _make_read("adr", {
            "object_uid": "adr-001",
            "object_id": "adr-001",
            "title": "Frontend uses React",
            "status": "active",
            "decision_question": "Which frontend framework to use?",
            "decision": "Use React for all web projects",
            "applicability": "All web frontend development",
            "trigger_signal": "When choosing frontend framework",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "decision_question", "matched_text": "frontend framework"}]
        card = _card(_MockDomain("F2"), "test", Path("/tmp"), "adr", read, reasons)

        assert card["trigger_reason"] == "signal_hit:decision_question_match"
        assert "decision_question" in card["matched_fields"]
        assert "exclusion_candidates" not in card  # No exclusion needed

    def test_scenario_title_only_match_suggests_exclusion(self) -> None:
        """Scenario: AI is writing a doc, text_match hits only title.
        Title-only match → exclusion_candidates suggests non-trigger-field-only-match.
        AI should check if this really触达 a decision boundary."""
        read = _make_read("adr", {
            "object_uid": "adr-002",
            "object_id": "adr-002",
            "title": "React decision",
            "status": "active",
            "decision_question": "Which frontend framework?",
            "decision": "Use React",
            "applicability": "Web projects",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "title", "matched_text": "React"}]
        card = _card(_MockDomain("F2"), "test", Path("/tmp"), "adr", read, reasons)

        assert "non-trigger-field-only-match" in card["exclusion_candidates"]
        # AI should consider: is "writing a doc about React" really a decision boundary?

    def test_scenario_applicability_only_match(self) -> None:
        """Scenario: AI is modifying a config in a web project, only applicability matched.
        applicability-only-match → potential exclusion."""
        read = _make_read("adr", {
            "object_uid": "adr-003",
            "object_id": "adr-003",
            "title": "API style decision",
            "status": "active",
            "decision_question": "REST vs GraphQL?",
            "decision": "Use REST",
            "applicability": "External API design",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "applicability", "matched_text": "API"}]
        card = _card(_MockDomain("F2"), "test", Path("/tmp"), "adr", read, reasons)

        assert "applicability-only-match" in card["exclusion_candidates"]
        # AI should check: is this config change really an API design decision?

    def test_scenario_multiple_trigger_fields_no_exclusion(self) -> None:
        """Scenario: decision_question AND applicability both match.
        Strong signal → no exclusion candidates."""
        read = _make_read("adr", {
            "object_uid": "adr-004",
            "object_id": "adr-004",
            "title": "Data model decision",
            "status": "active",
            "decision_question": "Use UUID or auto-increment?",
            "decision": "Use UUID",
            "applicability": "All data models",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [
            {"kind": "field-text", "field_path": "decision_question", "matched_text": "UUID"},
            {"kind": "field-text", "field_path": "applicability", "matched_text": "data model"},
        ]
        card = _card(_MockDomain("F2"), "test", Path("/tmp"), "adr", read, reasons)

        assert "exclusion_candidates" not in card
        assert len(card["matched_fields"]) == 2


# ---------------------------------------------------------------------------
# Pitfall real scenarios
# ---------------------------------------------------------------------------

class TestPitfallRealScenarios:
    """Pitfall: triggered = signal_hit AND symptom_risk_anchor"""

    def test_scenario_build_error_matches_symptoms(self) -> None:
        """Scenario: AI encounters 'ModuleNotFoundError' during build.
        Symptoms matched → anchor_type=observed_symptom → should trigger."""
        read = _make_read("pitfall", {
            "object_uid": "pit-001",
            "object_id": "pit-001",
            "title": "Module not found after pnpm install",
            "status": "active",
            "symptoms": "ModuleNotFoundError after pnpm install",
            "trigger_conditions": "After running pnpm install in web profile",
            "scope_of_impact": "Build and runtime",
            "applicability": "Node.js projects with pnpm",
            "validation_summary": "Verified on Node 18 + pnpm 8",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "symptoms", "matched_text": "ModuleNotFoundError"}]
        card = _card(_MockDomain("F2"), "test", Path("/tmp"), "pitfall", read, reasons)

        assert card["anchor_type"] == "observed_symptom"
        assert "observed_symptom" in card["trigger_reason"]
        # AI should directly check avoidance strategy

    def test_scenario_planning_risk_operation_matches_trigger_conditions(self) -> None:
        """Scenario: AI is about to run pnpm install, trigger_conditions matched.
        Potential risk → anchor_type=potential_risk → should trigger."""
        read = _make_read("pitfall", {
            "object_uid": "pit-002",
            "object_id": "pit-002",
            "title": "pnpm module twins issue",
            "status": "active",
            "symptoms": "Tool calls fail after pnpm install",
            "trigger_conditions": "Running pnpm install in web profile",
            "scope_of_impact": "Module loading",
            "applicability": "Projects with pnpm",
            "validation_summary": "Verified",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "trigger_conditions", "matched_text": "pnpm install"}]
        card = _card(_MockDomain("F2"), "test", Path("/tmp"), "pitfall", read, reasons)

        assert card["anchor_type"] == "potential_risk"
        assert "potential_risk" in card["trigger_reason"]
        # AI should evaluate: is the current task about to execute this operation?

    def test_scenario_pure_hypothesis_no_anchor(self) -> None:
        """Scenario: AI is discussing 'what if we use Docker in the future'.
        Only title matched, no trigger field → anchor_type=None → should NOT trigger."""
        read = _make_read("pitfall", {
            "object_uid": "pit-003",
            "object_id": "pit-003",
            "title": "Docker build platform issue",
            "status": "active",
            "symptoms": "exec format error in Docker build",
            "trigger_conditions": "Building Docker image on ARM",
            "applicability": "Docker projects",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "title", "matched_text": "Docker"}]
        card = _card(_MockDomain("F2"), "test", Path("/tmp"), "pitfall", read, reasons)

        assert card.get("anchor_type") is None  # No anchor → should not trigger
        assert "relation_or_status" in card["trigger_reason"]

    def test_scenario_investigating_fault_matches_applicability(self) -> None:
        """Scenario: AI is investigating a Docker build failure, applicability matched.
        Potential risk → anchor_type=potential_risk → should trigger."""
        read = _make_read("pitfall", {
            "object_uid": "pit-004",
            "object_id": "pit-004",
            "title": "Docker platform mismatch",
            "status": "active",
            "symptoms": "exec format error",
            "trigger_conditions": "Building on ARM without platform flag",
            "scope_of_impact": "Docker build",
            "applicability": "Docker projects on ARM",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "applicability", "matched_text": "Docker"}]
        card = _card(_MockDomain("F2"), "test", Path("/tmp"), "pitfall", read, reasons)

        assert card["anchor_type"] == "potential_risk"
        # AI should check: is the current task investigating a Docker build issue?
