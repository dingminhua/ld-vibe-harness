"""Focused tests for the v5 activation-layers paired experiment protocol and gateway."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, "code")

from ldvh.testing.knowledge_precheck_v2 import bytes_sha256
from ldvh.testing.knowledge_precheck_v5 import (
    _ACTION_DELTA_FIELDS,
    _ACTIVATION_HIT_FIELDS,
    _ACTIVATION_TRACE_FIELDS,
    _EXCHANGE_FIELDS,
    _OUTPUT_FIELDS,
    _RESPONSE_FIELDS,
    _SCORE_FIELDS,
    _SCORER_RESPONSE_FIELDS,
    _SOURCE_SNAPSHOT_FIELDS,
    ACTIVATION_TRACE_SCHEMA_VERSION,
    CONDITIONS,
    EVIDENCE_SCHEMA_VERSION,
    SCHEMA_VERSION,
    KnowledgePrecheckV5Error,
    ReadOnlyKnowledgeGateway,
    build_model_input_packet,
    build_model_input_packet_unchecked,
    condition_from_packet,
    validate_activation_trace,
    validate_f3_decision_response,
    validate_model_input_packet,
    validate_protocol,
    validate_score,
    validate_scorer_response,
)

_OBJECT_SET_FINGERPRINT = "f8f26823704af0f7986c2f97b0e8b09e6a8631150532d307ee254f5026545c42"


def _fingerprint(content: str) -> str:
    return bytes_sha256(content.encode("utf-8"))


# ---------------------------------------------------------------------------
# Protocol validation
# ---------------------------------------------------------------------------


def test_v5_protocol_closed():
    """The v5 protocol must validate without errors."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    problems = validate_protocol(protocol)
    assert not problems, f"protocol problems: {problems}"


def test_v5_protocol_conditions():
    """Conditions must be activation-baseline and activation-enhanced."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    assert protocol["conditions"] == list(CONDITIONS)


def test_v5_protocol_schema_version_tampered():
    """Tampered schema_version must be rejected."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    tampered = deepcopy(protocol)
    tampered["schema_version"] = "ldvh-knowledge-precheck-v5/999"
    problems = validate_protocol(tampered)
    assert "schema-version" in problems


def test_v5_protocol_conditions_tampered():
    """Tampered conditions must be rejected."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    tampered = deepcopy(protocol)
    tampered["conditions"] = ["activation-baseline"]
    problems = validate_protocol(tampered)
    assert "conditions" in problems


def test_v5_protocol_policies_keys_tampered():
    """Tampered policy keys must be rejected."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    tampered = deepcopy(protocol)
    tampered["policies"] = {"activation-baseline": protocol["policies"]["activation-baseline"]}
    problems = validate_protocol(tampered)
    assert "policies" in problems


def test_v5_protocol_ceilings_tampered():
    """Tampered ceilings must be rejected."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    tampered = deepcopy(protocol)
    tampered["ceilings"] = dict(protocol["ceilings"], maximum_member_launches=999)
    problems = validate_protocol(tampered)
    assert "ceilings" in problems


def test_v5_protocol_orders():
    """Condition orders must be 9/9 balanced."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    orders = protocol["condition_orders"]
    assert len(orders) == 18
    assert sum(1 for o in orders if o == ["activation-baseline", "activation-enhanced"]) == 9
    assert sum(1 for o in orders if o == ["activation-enhanced", "activation-baseline"]) == 9


# ---------------------------------------------------------------------------
# Source snapshot dual card set structure
# ---------------------------------------------------------------------------


def test_v5_source_snapshot_dual_card_sets():
    """Source snapshot must have family_cards_baseline and family_cards_activation covering 3 families."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    assert "family_cards_baseline" in snapshot
    assert "family_cards_activation" in snapshot
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]
    assert set(baseline) == {"adr", "pitfall", "study"}
    assert set(activation) == {"adr", "pitfall", "study"}
    # Card counts per family match (adr=5, pitfall=6, study=21)
    for family in ("adr", "pitfall", "study"):
        assert len(baseline[family]) == len(activation[family])
        assert len(baseline[family]) == snapshot["family_counts"][family]["active"]


def test_v5_activation_cards_have_projection_structure():
    """Activation-projected cards must contain activation_means and suggested_action."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    activation = snapshot["family_cards_activation"]
    for family in ("adr", "pitfall", "study"):
        for card in activation[family]:
            assert "activation_means" in card, f"{family} activation card missing activation_means"
            assert "suggested_action" in card, f"{family} activation card missing suggested_action"
            # Activation cards have the original knowledge-body fields nested under knowledge_body.fields
            assert "knowledge_body" in card, f"{family} activation card missing knowledge_body"
            body = card["knowledge_body"]
            assert "fields" in body
            assert "object_uid" in body["fields"]


def test_v5_baseline_cards_have_original_structure():
    """Baseline cards must be whole Helper cards with the original knowledge-body fields."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    for family in ("adr", "pitfall", "study"):
        for card in baseline[family]:
            assert "fields" in card
            assert "object_uid" in card["fields"]
            assert "object_id" in card["fields"]
            assert "title" in card["fields"]
            # Should NOT have projection fields
            assert "activation_means" not in card
            assert "suggested_action" not in card


# ---------------------------------------------------------------------------
# Gateway: activation card set selection
# ---------------------------------------------------------------------------


def _fake_activation_cards_dispatch(family_cards_baseline):
    """Create a fake dispatch returning the frozen baseline cards (whole Helper cards)."""

    def fake_dispatch(operation, request_bytes):
        payload = json.loads(request_bytes)
        family = payload["arguments"]["fact_type_keys"][0]
        cards = deepcopy(family_cards_baseline.get(family, []))
        return json.dumps(
            {
                "operation_key": "find-fact-object-candidates",
                "outcome": "ok",
                "changes": [],
                "result": {
                    "coverage": {
                        "status": "complete",
                        "total_matching": len(cards),
                        "returned": len(cards),
                        "object_set_fingerprint": _OBJECT_SET_FINGERPRINT,
                    },
                    "cards": cards,
                    "recovery_manifest": {"object_set_fingerprint": _OBJECT_SET_FINGERPRINT},
                },
            }
        ).encode("utf-8")

    return fake_dispatch


def test_v5_gateway_baseline_arm():
    """Gateway with activation-baseline must validate against family_cards_baseline."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]

    gateway = ReadOnlyKnowledgeGateway(
        _fake_activation_cards_dispatch(baseline),
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        {
            "arguments": {
                "governed_project_id": "ldvh",
                "card_layer": "F2",
                "fact_type_keys": ["adr"],
                "statuses": ["active"],
            }
        },
        exchange_id="e1",
        attempt_id="a1",
        card_layer="activation-baseline",
    )
    assert exchange["operation"] == "find-fact-object-candidates"
    assert exchange["state_changing_calls"] == 0
    observed = json.loads(exchange["raw_response_utf8"])["result"]["cards"]
    # Baseline arm: served cards match the frozen baseline (whole cards)
    assert [card["fields"] for card in observed] == [card["fields"] for card in baseline["adr"]]
    for card in observed:
        assert "activation_means" not in card.get("fields", {})
        assert "suggested_action" not in card.get("fields", {})
    assert observed != activation["adr"]


def _fake_activation_projection_dispatch(family_cards_baseline):
    """Create a fake dispatch that returns baseline-structured cards."""
    return _fake_activation_cards_dispatch(family_cards_baseline)


def test_v5_gateway_enhanced_arm():
    """Gateway with activation-enhanced must project the activation card set."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]

    gateway = ReadOnlyKnowledgeGateway(
        _fake_activation_projection_dispatch(baseline),
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        {
            "arguments": {
                "governed_project_id": "ldvh",
                "card_layer": "F2",
                "fact_type_keys": ["adr"],
                "statuses": ["active"],
            }
        },
        exchange_id="e2",
        attempt_id="a2",
        card_layer="activation-enhanced",
    )
    assert exchange["operation"] == "find-fact-object-candidates"
    assert exchange["state_changing_calls"] == 0
    # Enhanced arm: the served card fields are the activation-projected fields
    served = exchange["served_cards"]
    assert [card["fields"] for card in served] == activation["adr"]
    for card in served:
        f = card.get("fields", {})
        assert "activation_means" in f, f"enhanced card missing activation_means: {f.get('title')}"
        assert "suggested_action" in f, f"enhanced card missing suggested_action: {f.get('title')}"
    assert served != baseline["adr"]


# ---------------------------------------------------------------------------
# Gateway drift rejection
# ---------------------------------------------------------------------------


def test_v5_gateway_drift_rejected():
    """Gateway must reject drifted F2 cards."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]

    def fake_dispatch(operation, request_bytes):
        payload = json.loads(request_bytes)
        family = payload["arguments"]["fact_type_keys"][0]
        cards = deepcopy(baseline.get(family, []))
        # Tamper the first card's fields.title
        if cards and "fields" in cards[0]:
            cards[0]["fields"]["title"] = "TAMPERED TITLE"
        return json.dumps(
            {
                "operation_key": "find-fact-object-candidates",
                "outcome": "ok",
                "changes": [],
                "result": {
                    "coverage": {
                        "status": "complete",
                        "total_matching": len(cards),
                        "returned": len(cards),
                        "object_set_fingerprint": _OBJECT_SET_FINGERPRINT,
                    },
                    "cards": cards,
                    "recovery_manifest": {"object_set_fingerprint": _OBJECT_SET_FINGERPRINT},
                },
            }
        ).encode("utf-8")

    gateway = ReadOnlyKnowledgeGateway(
        fake_dispatch,
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
    )
    with pytest.raises(KnowledgePrecheckV5Error, match="drifted"):
        gateway.call(
            "find-fact-object-candidates",
            {
                "arguments": {
                    "governed_project_id": "ldvh",
                    "card_layer": "F2",
                    "fact_type_keys": ["adr"],
                    "statuses": ["active"],
                }
            },
            exchange_id="e1",
            attempt_id="a1",
            card_layer="activation-baseline",
        )


def test_v5_gateway_fingerprint_drift_rejected():
    """Gateway must reject drifted F3 fingerprints."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]

    def fake_dispatch(operation, request_bytes):
        # Return a valid F3 response but with a wrong fingerprint
        payload = json.loads(request_bytes)
        items = []
        for ref in payload["arguments"]["fact_refs"]:
            uid = ref["object_uid"]
            items.append(
                {
                    "check_status": "mechanically_valid",
                    "resolved_ref": {"object_uid": uid},
                    "fact_object": {
                        "frontmatter": {"object_uid": uid, "fact_type_key": "adr"},
                    },
                    "content_fingerprint": "f" * 64,
                }
            )
        return json.dumps(
            {
                "operation_key": "read-fact-objects",
                "outcome": "ok",
                "changes": [],
                "result": {"items": items},
            }
        ).encode("utf-8")

    gateway = ReadOnlyKnowledgeGateway(
        fake_dispatch,
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
        expected_f3_fingerprints=snapshot["knowledge_ref_fingerprints"],
    )
    with pytest.raises(KnowledgePrecheckV5Error, match="drifted"):
        gateway.call(
            "read-fact-objects",
            {"arguments": {"fact_refs": [{"object_uid": "019ffb52-ebb5-724c-881f-4f0f7d97038f"}]}},
            exchange_id="e1",
            attempt_id="a1",
        )


# ---------------------------------------------------------------------------
# Condition leakage rejection
# ---------------------------------------------------------------------------


def test_v5_condition_leakage_packet():
    """Model input packet must not leak the other condition identifier."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    packet = build_model_input_packet(
        protocol,
        pair_id="A1",
        condition="activation-baseline",
        attempt_id="attempt-test-leakage",
        fresh_context_id_hash="a" * 64,
    )
    # The packet must not contain the other condition's identifier
    assert "activation-enhanced" not in packet.get("card_layer", "")


def test_v5_condition_from_packet():
    """condition_from_packet must resolve from card_layer field."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    packet = {
        "schema_version": SCHEMA_VERSION,
        "attempt_id": "attempt-test",
        "pair_id": "A1",
        "family": "adr",
        "user_task": "test",
        "fresh_context_id_hash": "a" * 64,
        "card_layer": "activation-baseline",
        "l1_policy": {"content": "test", "sha256": "a" * 64},
        "knowledge_gateway_contract": {},
        "trigger_trace_contract": {},
        "response_contract": {},
    }
    condition = condition_from_packet(packet, protocol)
    assert condition == "activation-baseline"

    packet["card_layer"] = "activation-enhanced"
    condition = condition_from_packet(packet, protocol)
    assert condition == "activation-enhanced"


# ---------------------------------------------------------------------------
# F3-before-F2, cross-family, write/unknown, arguments.workspace_root
# ---------------------------------------------------------------------------


def test_v5_model_input_contract_rejects_workspace_root():
    """Model input must forbid arguments.workspace_root and writes."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    packet = build_model_input_packet(
        protocol,
        pair_id="A1",
        condition="activation-baseline",
        attempt_id="attempt-test-ws",
        fresh_context_id_hash="a" * 64,
    )
    contract = packet["knowledge_gateway_contract"]
    assert "arguments_workspace_root" in contract
    assert contract["arguments_workspace_root"] == "forbidden"
    assert "writes" in contract
    assert contract["writes"] == "forbidden"


def test_v5_model_input_packet():
    """build_model_input_packet must include card_layer field."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    packet = build_model_input_packet(
        protocol,
        pair_id="A1",
        condition="activation-baseline",
        attempt_id="attempt-test",
        fresh_context_id_hash="a" * 64,
    )
    assert packet["card_layer"] == "activation-baseline"
    assert packet["schema_version"] == SCHEMA_VERSION
    validate_model_input_packet(packet, protocol)


def test_v5_model_input_packet_unchecked():
    """build_model_input_packet_unchecked must produce deterministic output."""
    minimal = {
        "tasks": [
            {
                "pair_id": "A1",
                "family": "adr",
                "case_kind": "exact-positive",
                "user_task": "test",
            }
        ],
        "conditions": list(CONDITIONS),
        "policies": {
            "activation-baseline": {"content": "test", "sha256": "a" * 64},
            "activation-enhanced": {"content": "test", "sha256": "a" * 64},
        },
    }
    a = build_model_input_packet_unchecked(
        minimal,
        pair_id="A1",
        condition="activation-baseline",
        attempt_id="attempt-test",
        fresh_context_id_hash="a" * 64,
    )
    b = build_model_input_packet_unchecked(
        minimal,
        pair_id="A1",
        condition="activation-baseline",
        attempt_id="attempt-test",
        fresh_context_id_hash="a" * 64,
    )
    assert a == b
    assert a["card_layer"] == "activation-baseline"


# ---------------------------------------------------------------------------
# Activation trace
# ---------------------------------------------------------------------------


def _make_activation_trace() -> dict[str, Any]:
    return {
        "schema_version": ACTIVATION_TRACE_SCHEMA_VERSION,
        "attempt_id": "attempt-test",
        "pair_id": "A1",
        "condition": "activation-baseline",
        "family": "adr",
        "activation_hits": [
            {
                "family": "adr",
                "object_uid": "019ffb52-ebb5-724c-881f-4f0f7d97038f",
                "object_id": "adr-01KZXN5TXNE968G7TF1XYSE0WF",
                "hit_stage": "f2",
                "triggered": True,
            }
        ],
        "action_delta": {
            "first_legal_action": "read-rule-gap-before-code",
            "final_action": "read-rule-gap-before-code",
            "action_changed_vs_gold": False,
            "evidence_notes": "derived from deterministic Helper exchange replay",
        },
    }


def test_validate_activation_trace_field_closed():
    """validate_activation_trace must validate the closed field set."""
    trace = _make_activation_trace()
    validate_activation_trace(trace)
    assert set(trace) == _ACTIVATION_TRACE_FIELDS
    assert set(trace["activation_hits"][0]) == _ACTIVATION_HIT_FIELDS
    assert set(trace["action_delta"]) == _ACTION_DELTA_FIELDS

    with pytest.raises(KnowledgePrecheckV5Error):
        validate_activation_trace({**trace, "extra_field": "value"})


def test_validate_activation_trace_hit_stage():
    """validate_activation_trace must validate hit_stage closed set."""
    trace = _make_activation_trace()
    bad = deepcopy(trace)
    bad["activation_hits"][0]["hit_stage"] = "invalid-stage"
    with pytest.raises(KnowledgePrecheckV5Error):
        validate_activation_trace(bad)


def test_validate_activation_trace_action_delta_fields():
    """validate_activation_trace must validate action_delta fields."""
    trace = _make_activation_trace()
    bad = deepcopy(trace)
    del bad["action_delta"]["first_legal_action"]
    with pytest.raises(KnowledgePrecheckV5Error):
        validate_activation_trace(bad)


# ---------------------------------------------------------------------------
# Score / scorer validation
# ---------------------------------------------------------------------------


def _make_valid_score(action_bridge_score: int) -> dict[str, Any]:
    return {
        "attempt_id": "attempt-test",
        "blind_packet_sha256": "a" * 64,
        "scorer_model_name": None,
        "scorer_runtime_name": "codex-native-subagent",
        "fresh_scorer_context_id_hash": "a" * 64,
        "condition_blind_attested": True,
        "knowledge_adjusted_first_legal_action_correct": True,
        "action_changed": False,
        "strong_reuse": False,
        "correct_non_use": False,
        "action_bridge_score": action_bridge_score,
        "scoring_notes": "test scoring notes",
    }


def _make_valid_scorer_response(action_bridge_score: int) -> dict[str, Any]:
    return {
        "condition_blind_attested": True,
        "knowledge_adjusted_first_legal_action_correct": True,
        "action_changed": False,
        "strong_reuse": False,
        "correct_non_use": False,
        "action_bridge_score": action_bridge_score,
        "scoring_notes": "test scoring notes",
    }


def test_validate_score_0_3():
    """validate_score must accept 0-3 action_bridge_score and be closed on fields."""
    for score_val in (0, 1, 2, 3):
        score = _make_valid_score(score_val)
        validate_score(score)
        assert set(score) == _SCORE_FIELDS
        assert set(_make_valid_scorer_response(score_val)) == _SCORER_RESPONSE_FIELDS


def test_validate_score_out_of_range():
    """validate_score must reject out-of-range action_bridge_score."""
    for score_val in (-1, 4, 999):
        with pytest.raises(KnowledgePrecheckV5Error):
            validate_score(_make_valid_score(score_val))


def test_validate_scorer_response_0_3():
    """validate_scorer_response must accept 0-3 action_bridge_score."""
    for score_val in (0, 1, 2, 3):
        validate_scorer_response(_make_valid_scorer_response(score_val))


def test_validate_scorer_response_out_of_range():
    """validate_scorer_response must reject out-of-range action_bridge_score."""
    for score_val in (-1, 4, 999):
        with pytest.raises(KnowledgePrecheckV5Error):
            validate_scorer_response(_make_valid_scorer_response(score_val))


# ---------------------------------------------------------------------------
# Evidence field closures (anti-tamper)
# ---------------------------------------------------------------------------


def test_v5_evidence_field_closures():
    """Evidence field closures must match the frozen v5 sets."""
    assert set(_make_valid_score(2)) == _SCORE_FIELDS
    assert set(_make_valid_scorer_response(2)) == _SCORER_RESPONSE_FIELDS
    output = {
        "attempt_id": "attempt-test",
        "pair_id": "A1",
        "condition": "activation-baseline",
        "model_name": None,
        "agent_runtime_name": "codex-native-subagent",
        "fresh_context_id_hash": "a" * 64,
        "structured_response": {
            "decision": "wait",
            "selected_refs": [],
            "first_legal_action": "wait",
            "rationale_codes": ["none"],
            "refusal_reason_codes": [],
        },
        "helper_exchange_ids": [],
        "usage": "unavailable",
        "latency": "unavailable",
    }
    assert set(output) == _OUTPUT_FIELDS
    assert set(output["structured_response"]) == _RESPONSE_FIELDS


def test_v5_exchange_field_closure():
    """A valid helper exchange must match the closed exchange field set."""
    exchange = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "exchange_id": "e1",
        "attempt_id": "a1",
        "operation": "find-fact-object-candidates",
        "raw_request_utf8": "{}",
        "request_sha256": "a" * 64,
        "raw_response_utf8": "{}",
        "response_sha256": "a" * 64,
        "coverage": None,
        "match_reasons": [],
        "f3_objects": [],
        "state_changing_calls": 0,
        "served_cards": [],
    }
    assert set(exchange) == _EXCHANGE_FIELDS


# ---------------------------------------------------------------------------
# F3 decision response validation
# ---------------------------------------------------------------------------


def test_validate_f3_decision_response():
    """validate_f3_decision_response must accept valid refs."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    families = snapshot["knowledge_ref_families"]
    refs = validate_f3_decision_response(
        {"read_f3_refs": ["019ffb52-ebb5-724c-881f-4f0f7d97038f"]},
        family="adr",
        snapshot_families=families,
    )
    assert refs == ["019ffb52-ebb5-724c-881f-4f0f7d97038f"]


def test_validate_f3_decision_response_too_many():
    """validate_f3_decision_response must reject >2 refs."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    families = snapshot["knowledge_ref_families"]
    with pytest.raises(KnowledgePrecheckV5Error):
        validate_f3_decision_response(
            {"read_f3_refs": ["a", "b", "c"]},
            family="adr",
            snapshot_families=families,
        )


# ---------------------------------------------------------------------------
# Source snapshot / anti-tamper
# ---------------------------------------------------------------------------


def test_v5_source_snapshot_fields_closed():
    """Source snapshot fields must be closed."""
    snapshot = json.loads(Path("docs/metrics/knowledge-precheck-v5/source-snapshot.json").read_bytes())
    assert set(snapshot) == _SOURCE_SNAPSHOT_FIELDS


def test_v5_evidence_schema_version():
    """Evidence schema version must be the v5 constant."""
    assert EVIDENCE_SCHEMA_VERSION == "ldvh-knowledge-precheck-v5-evidence/1"


def test_v5_activation_trace_schema_version():
    """Activation trace schema version must be the v5 constant."""
    assert ACTIVATION_TRACE_SCHEMA_VERSION == "ldvh-knowledge-precheck-v5-activation-trace/1"


if __name__ == "__main__":
    print("tests are exercised through pytest only")
