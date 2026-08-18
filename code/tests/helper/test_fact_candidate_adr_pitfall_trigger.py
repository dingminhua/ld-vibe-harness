"""Focused tests for ADR/Pitfall differentiated trigger_reason field."""

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


# ---------------------------------------------------------------------------
# _compute_trigger_reason unit tests
# ---------------------------------------------------------------------------

class TestComputeTriggerReason:
    def test_adr_decision_question_match(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "decision_question", "matched_text": "test"}]
        assert _compute_trigger_reason("adr", reasons) == "signal_hit:decision_question_match"

    def test_adr_decision_match(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "decision", "matched_text": "test"}]
        assert _compute_trigger_reason("adr", reasons) == "signal_hit:decision_match"

    def test_adr_applicability_match(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "applicability", "matched_text": "test"}]
        assert _compute_trigger_reason("adr", reasons) == "signal_hit:applicability_match"

    def test_adr_trigger_signal_match(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "trigger_signal", "matched_text": "test"}]
        assert _compute_trigger_reason("adr", reasons) == "signal_hit:trigger_signal_match"

    def test_adr_non_trigger_field(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "title", "matched_text": "test"}]
        assert _compute_trigger_reason("adr", reasons) == "signal_hit:relation_or_status"

    def test_adr_empty_reasons(self) -> None:
        assert _compute_trigger_reason("adr", []) == "signal_hit:relation_or_status"

    def test_pitfall_symptoms_match(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "symptoms", "matched_text": "test"}]
        result = _compute_trigger_reason("pitfall", reasons)
        assert result == "signal_hit:symptoms_match AND anchor:observed_symptom"

    def test_pitfall_trigger_conditions_match(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "trigger_conditions", "matched_text": "test"}]
        result = _compute_trigger_reason("pitfall", reasons)
        assert result == "signal_hit:trigger_conditions_match AND anchor:potential_risk"

    def test_pitfall_applicability_match(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "applicability", "matched_text": "test"}]
        result = _compute_trigger_reason("pitfall", reasons)
        assert result == "signal_hit:applicability_match AND anchor:potential_risk"

    def test_pitfall_non_trigger_field(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "title", "matched_text": "test"}]
        assert _compute_trigger_reason("pitfall", reasons) == "signal_hit:relation_or_status"


# ---------------------------------------------------------------------------
# _compute_matched_fields tests
# ---------------------------------------------------------------------------

class TestComputeMatchedFields:
    def test_returns_field_paths_from_field_text_reasons(self) -> None:
        reasons = [
            {"kind": "field-text", "field_path": "decision_question", "matched_text": "x"},
            {"kind": "status", "field_path": "status"},
            {"kind": "field-text", "field_path": "applicability", "matched_text": "y"},
        ]
        assert _compute_matched_fields(reasons) == ["decision_question", "applicability"]

    def test_empty_when_no_field_text(self) -> None:
        reasons = [{"kind": "status", "field_path": "status"}]
        assert _compute_matched_fields(reasons) == []


# ---------------------------------------------------------------------------
# _compute_exclusion_candidates tests
# ---------------------------------------------------------------------------

class TestComputeExclusionCandidates:
    def test_adr_title_only_match(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "title", "matched_text": "test"}]
        assert _compute_exclusion_candidates("adr", reasons) == ["non-trigger-field-only-match"]

    def test_adr_trigger_field_match_no_exclusion(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "decision_question", "matched_text": "test"}]
        assert _compute_exclusion_candidates("adr", reasons) == []

    def test_adr_applicability_only(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "applicability", "matched_text": "test"}]
        result = _compute_exclusion_candidates("adr", reasons)
        assert "applicability-only-match" in result

    def test_pitfall_returns_empty(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "symptoms", "matched_text": "test"}]
        assert _compute_exclusion_candidates("pitfall", reasons) == []


# ---------------------------------------------------------------------------
# _compute_anchor_type tests
# ---------------------------------------------------------------------------

class TestComputeAnchorType:
    def test_pitfall_symptoms_observed(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "symptoms", "matched_text": "test"}]
        assert _compute_anchor_type("pitfall", reasons) == "observed_symptom"

    def test_pitfall_trigger_conditions_potential(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "trigger_conditions", "matched_text": "test"}]
        assert _compute_anchor_type("pitfall", reasons) == "potential_risk"

    def test_pitfall_applicability_potential(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "applicability", "matched_text": "test"}]
        assert _compute_anchor_type("pitfall", reasons) == "potential_risk"

    def test_pitfall_no_trigger_returns_none(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "title", "matched_text": "test"}]
        assert _compute_anchor_type("pitfall", reasons) is None

    def test_adr_returns_none(self) -> None:
        reasons = [{"kind": "field-text", "field_path": "decision_question", "matched_text": "test"}]
        assert _compute_anchor_type("adr", reasons) is None


# ---------------------------------------------------------------------------
# Card-level trigger_reason presence tests
# ---------------------------------------------------------------------------

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


class TestCardTriggerReason:
    def test_adr_card_includes_trigger_reason_and_matched_fields(self) -> None:
        domain = _MockDomain("F2")
        read = _make_read("adr", {
            "object_uid": "00000000-0000-0000-0000-000000000001",
            "object_id": "adr-0001",
            "title": "Test ADR",
            "status": "active",
            "decision_question": "Should we use X?",
            "decision": "Use X",
            "applicability": "All web projects",
            "trigger_signal": "When choosing tech stack",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "decision_question", "matched_text": "test"}]
        card = _card(domain, "test", Path("/tmp/test"), "adr", read, reasons)
        assert "trigger_reason" in card
        assert card["trigger_reason"] == "signal_hit:decision_question_match"
        assert "matched_fields" in card
        assert card["matched_fields"] == ["decision_question"]
        # No exclusion candidates when trigger field matched
        assert "exclusion_candidates" not in card

    def test_pitfall_card_includes_trigger_reason(self) -> None:
        domain = _MockDomain("F2")
        read = _make_read("pitfall", {
            "object_uid": "00000000-0000-0000-0000-000000000002",
            "object_id": "pitfall-0001",
            "title": "Test Pitfall",
            "status": "active",
            "symptoms": "Build fails with error X",
            "trigger_conditions": "After npm install",
            "scope_of_impact": "Build process",
            "applicability": "Node.js projects",
            "validation_summary": "Tested on v18",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "symptoms", "matched_text": "test"}]
        card = _card(domain, "test", Path("/tmp/test"), "pitfall", read, reasons)
        assert "trigger_reason" in card
        assert card["trigger_reason"] == "signal_hit:symptoms_match AND anchor:observed_symptom"
        assert card["matched_fields"] == ["symptoms"]
        assert card["anchor_type"] == "observed_symptom"

    def test_adr_title_only_exclusion_candidate(self) -> None:
        domain = _MockDomain("F2")
        read = _make_read("adr", {
            "object_uid": "00000000-0000-0000-0000-000000000004",
            "object_id": "adr-0002",
            "title": "React decision",
            "status": "active",
            "decision_question": "Should we use X?",
            "decision": "Use X",
            "applicability": "All web projects",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "title", "matched_text": "React"}]
        card = _card(domain, "test", Path("/tmp/test"), "adr", read, reasons)
        assert "trigger_reason" in card
        assert card["trigger_reason"] == "signal_hit:relation_or_status"
        assert card["matched_fields"] == ["title"]
        assert "exclusion_candidates" in card
        assert "non-trigger-field-only-match" in card["exclusion_candidates"]

    def test_pitfall_trigger_conditions_potential_risk(self) -> None:
        domain = _MockDomain("F2")
        read = _make_read("pitfall", {
            "object_uid": "00000000-0000-0000-0000-000000000005",
            "object_id": "pitfall-0002",
            "title": "Test Pitfall 2",
            "status": "active",
            "symptoms": "Error X",
            "trigger_conditions": "After npm install",
            "applicability": "Node.js projects",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        reasons = [{"kind": "field-text", "field_path": "trigger_conditions", "matched_text": "npm"}]
        card = _card(domain, "test", Path("/tmp/test"), "pitfall", read, reasons)
        assert card["anchor_type"] == "potential_risk"

    def test_spark_card_no_trigger_reason(self) -> None:
        domain = _MockDomain("F2")
        read = _make_read("spark", {
            "object_uid": "00000000-0000-0000-0000-000000000003",
            "object_id": "spark-0001",
            "title": "Test Spark",
            "status": "open",
            "priority": "P1",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        card = _card(domain, "test", Path("/tmp/test"), "spark", read, [])
        assert "trigger_reason" not in card
