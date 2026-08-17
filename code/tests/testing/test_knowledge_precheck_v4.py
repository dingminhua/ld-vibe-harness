"""Focused tests for the v4 structure experiment protocol and gateway."""

import json
import sys
from pathlib import Path

sys.path.insert(0, "code")

from ldvh.testing.knowledge_precheck_v2 import canonical_json_bytes, bytes_sha256
from ldvh.testing.knowledge_precheck_v4 import (
    CONDITIONS,
    EVIDENCE_SCHEMA_VERSION,
    SCHEMA_VERSION,
    KnowledgePrecheckV4Error,
    ReadOnlyKnowledgeGateway,
    _strip_f2_cards,
    build_model_input_packet,
    build_model_input_packet_unchecked,
    compile_evidence_bundle,
    condition_from_packet,
    validate_model_input_packet,
    validate_protocol,
)


def _fingerprint(content: str) -> str:
    return bytes_sha256(content.encode("utf-8"))


def test_v4_protocol_closed():
    """The v4 protocol must validate without errors."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v4/protocol.json").read_bytes())
    problems = validate_protocol(protocol)
    assert not problems, f"protocol problems: {problems}"


def test_v4_protocol_conditions():
    """Conditions must be struct-baseline and struct-enhanced."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v4/protocol.json").read_bytes())
    assert protocol["conditions"] == list(CONDITIONS)


def test_v4_protocol_same_policy():
    """Both arms must share the exact same policy."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v4/protocol.json").read_bytes())
    base = protocol["policies"]["struct-baseline"]
    enhanced = protocol["policies"]["struct-enhanced"]
    assert base["sha256"] == enhanced["sha256"]
    assert base["content"] == enhanced["content"]


def test_v4_protocol_orders():
    """Condition orders must be 9/9 balanced."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v4/protocol.json").read_bytes())
    orders = protocol["condition_orders"]
    assert len(orders) == 18
    assert sum(1 for o in orders if o == ["struct-baseline", "struct-enhanced"]) == 9
    assert sum(1 for o in orders if o == ["struct-enhanced", "struct-baseline"]) == 9


def test_strip_f2_cards():
    """_strip_f2_cards must remove trigger_signal, scope_of_impact, action_relevance."""
    cards = [
        {"uid": "1", "trigger_signal": "x", "scope_of_impact": "y", "action_relevance": "z", "title": "t"},
        {"uid": "2", "trigger_signal": "a", "title": "b"},
    ]
    result = _strip_f2_cards(cards)
    for card in result:
        assert "trigger_signal" not in card
        assert "scope_of_impact" not in card
        assert "action_relevance" not in card
    assert result[0]["title"] == "t"
    assert result[1]["uid"] == "2"


def test_fake_gateway_strip():
    """Gateway with struct-baseline must strip cards."""
    _ALL_FAMILIES = {"adr", "pitfall", "study"}
    f2_cards = {
        "adr": [
            {"uid": "1", "trigger_signal": "signal", "title": "ADR 1"},
            {"uid": "2", "trigger_signal": "signal2", "title": "ADR 2"},
        ],
        "pitfall": [{"uid": "p1", "scope_of_impact": "scope", "title": "PIT 1"}],
        "study": [{"uid": "s1", "action_relevance": "action", "title": "STU 1"}],
    }
    stripped = {
        "adr": [
            {"uid": "1", "title": "ADR 1"},
            {"uid": "2", "title": "ADR 2"},
        ],
        "pitfall": [{"uid": "p1", "title": "PIT 1"}],
        "study": [{"uid": "s1", "title": "STU 1"}],
    }

    def fake_dispatch(operation, request_bytes):
        payload = json.loads(request_bytes)
        if operation == "find-fact-object-candidates":
            family = payload["arguments"]["fact_type_keys"][0]
            return json.dumps({
                "operation_key": "find-fact-object-candidates",
                "outcome": "ok",
                "changes": [],
                "result": {
                    "coverage": {
                        "status": "complete",
                        "total_matching": len(f2_cards.get(family, [])),
                        "returned": len(f2_cards.get(family, [])),
                        "object_set_fingerprint": "a" * 64,
                    },
                    "cards": [
                        {"fact_ref": {"object_uid": c["uid"]}, "fields": dict(c), "match_reasons": []}
                        for c in f2_cards.get(family, [])
                    ],
                    "recovery_manifest": {"object_set_fingerprint": "a" * 64},
                },
            }).encode("utf-8")
        raise ValueError(f"unexpected operation: {operation}")

    gateway = ReadOnlyKnowledgeGateway(
        fake_dispatch,
        expected_f2_cards_enhanced=f2_cards,
        expected_f2_cards_stripped=stripped,
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        {"arguments": {"governed_project_id": "ldvh", "card_layer": "F2", "fact_type_keys": ["adr"], "statuses": ["active"]}},
        exchange_id="e1",
        attempt_id="a1",
        card_layer="struct-baseline",
    )
    assert exchange["operation"] == "find-fact-object-candidates"


def test_fake_gateway_enhanced():
    """Gateway with struct-enhanced must keep cards as-is."""
    f2_cards = {
        "adr": [{"uid": "1", "trigger_signal": "signal", "title": "ADR 1"}],
        "pitfall": [{"uid": "p1", "scope_of_impact": "scope", "title": "PIT 1"}],
        "study": [{"uid": "s1", "action_relevance": "action", "title": "STU 1"}],
    }
    stripped = {
        "adr": [{"uid": "1", "title": "ADR 1"}],
        "pitfall": [{"uid": "p1", "title": "PIT 1"}],
        "study": [{"uid": "s1", "title": "STU 1"}],
    }

    def fake_dispatch(operation, request_bytes):
        return json.dumps({
            "operation_key": "find-fact-object-candidates",
            "outcome": "ok",
            "changes": [],
            "result": {
                "coverage": {
                    "status": "complete",
                    "total_matching": 1,
                    "returned": 1,
                    "object_set_fingerprint": "a" * 64,
                },
                "cards": [
                    {"fact_ref": {"object_uid": "1"}, "fields": {"uid": "1", "trigger_signal": "signal", "title": "ADR 1"}, "match_reasons": []},
                ],
                "recovery_manifest": {"object_set_fingerprint": "a" * 64},
            },
        }).encode("utf-8")

    gateway = ReadOnlyKnowledgeGateway(
        fake_dispatch,
        expected_f2_cards_enhanced=f2_cards,
        expected_f2_cards_stripped=stripped,
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        {"arguments": {"governed_project_id": "ldvh", "card_layer": "F2", "fact_type_keys": ["adr"], "statuses": ["active"]}},
        exchange_id="e1",
        attempt_id="a1",
        card_layer="struct-enhanced",
    )
    assert exchange["operation"] == "find-fact-object-candidates"


def test_fake_gateway_drift_rejected():
    """Gateway must reject drifted F2 cards."""
    f2_cards = {
        "adr": [{"uid": "1", "trigger_signal": "signal", "title": "ADR 1"}],
        "pitfall": [{"uid": "p1", "scope_of_impact": "scope", "title": "PIT 1"}],
        "study": [{"uid": "s1", "action_relevance": "action", "title": "STU 1"}],
    }

    def fake_dispatch(operation, request_bytes):
        return json.dumps({
            "operation_key": "find-fact-object-candidates",
            "outcome": "ok",
            "changes": [],
            "result": {
                "coverage": {
                    "status": "complete",
                    "total_matching": 1,
                    "returned": 1,
                    "object_set_fingerprint": "a" * 64,
                },
                "cards": [
                    {"fact_ref": {"object_uid": "1"}, "fields": {"uid": "1", "trigger_signal": "DIFFERENT", "title": "ADR 1"}, "match_reasons": []},
                ],
                "recovery_manifest": {"object_set_fingerprint": "a" * 64},
            },
        }).encode("utf-8")

    gateway = ReadOnlyKnowledgeGateway(
        fake_dispatch,
        expected_f2_cards_enhanced=f2_cards,
    )
    try:
        gateway.call(
            "find-fact-object-candidates",
            {"arguments": {"governed_project_id": "ldvh", "card_layer": "F2", "fact_type_keys": ["adr"], "statuses": ["active"]}},
            exchange_id="e1",
            attempt_id="a1",
        )
        assert False, "expected drift rejection"
    except KnowledgePrecheckV4Error:
        pass


def test_fake_gateway_stripped_drift_rejected():
    """Gateway must reject stripped card drift on struct-baseline."""
    f2_cards = {
        "adr": [{"uid": "1", "trigger_signal": "signal", "title": "ADR 1"}],
        "pitfall": [{"uid": "p1", "scope_of_impact": "scope", "title": "PIT 1"}],
        "study": [{"uid": "s1", "action_relevance": "action", "title": "STU 1"}],
    }
    # Deliberately wrong stripped set - title differs
    stripped = {
        "adr": [{"uid": "1", "title": "DIFFERENT TITLE"}],
        "pitfall": [{"uid": "p1", "title": "PIT 1"}],
        "study": [{"uid": "s1", "title": "STU 1"}],
    }

    def fake_dispatch(operation, request_bytes):
        return json.dumps({
            "operation_key": "find-fact-object-candidates",
            "outcome": "ok",
            "changes": [],
            "result": {
                "coverage": {
                    "status": "complete",
                    "total_matching": 1,
                    "returned": 1,
                    "object_set_fingerprint": "a" * 64,
                },
                "cards": [
                    {"fact_ref": {"object_uid": "1"}, "fields": {"uid": "1", "trigger_signal": "signal", "title": "ADR 1"}, "match_reasons": []},
                ],
                "recovery_manifest": {"object_set_fingerprint": "a" * 64},
            },
        }).encode("utf-8")

    gateway = ReadOnlyKnowledgeGateway(
        fake_dispatch,
        expected_f2_cards_enhanced=f2_cards,
        expected_f2_cards_stripped=stripped,
    )
    try:
        gateway.call(
            "find-fact-object-candidates",
            {"arguments": {"governed_project_id": "ldvh", "card_layer": "F2", "fact_type_keys": ["adr"], "statuses": ["active"]}},
            exchange_id="e1",
            attempt_id="a1",
            card_layer="struct-baseline",
        )
        assert False, "expected stripped drift rejection"
    except KnowledgePrecheckV4Error:
        pass


def test_condition_from_packet():
    """condition_from_packet must resolve from card_layer field."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v4/protocol.json").read_bytes())
    packet = {
        "schema_version": SCHEMA_VERSION,
        "attempt_id": "attempt-test",
        "pair_id": "A1",
        "family": "adr",
        "user_task": "test",
        "fresh_context_id_hash": "a" * 64,
        "card_layer": "struct-baseline",
        "l1_policy": {"content": "test", "sha256": "a" * 64},
        "knowledge_gateway_contract": {},
        "trigger_trace_contract": {},
        "response_contract": {},
    }
    condition = condition_from_packet(packet, protocol)
    assert condition == "struct-baseline"

    packet["card_layer"] = "struct-enhanced"
    condition = condition_from_packet(packet, protocol)
    assert condition == "struct-enhanced"


def test_model_input_packet():
    """build_model_input_packet must include card_layer field."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v4/protocol.json").read_bytes())
    packet = build_model_input_packet(
        protocol,
        pair_id="A1",
        condition="struct-baseline",
        attempt_id="attempt-test",
        fresh_context_id_hash="a" * 64,
    )
    assert packet["card_layer"] == "struct-baseline"
    assert packet["schema_version"] == SCHEMA_VERSION

    # Validate it
    validate_model_input_packet(packet, protocol)


def test_model_input_packet_unchecked():
    """build_model_input_packet_unchecked must produce deterministic output."""
    a = build_model_input_packet_unchecked(
        {"tasks": [{"pair_id": "A1", "family": "adr", "case_kind": "exact-positive", "user_task": "test"}],
         "conditions": list(CONDITIONS),
         "policies": {"struct-baseline": {"content": "test", "sha256": "a" * 64},
                      "struct-enhanced": {"content": "test", "sha256": "a" * 64}}},
        pair_id="A1",
        condition="struct-baseline",
        attempt_id="attempt-test",
        fresh_context_id_hash="a" * 64,
    )
    b = build_model_input_packet_unchecked(
        {"tasks": [{"pair_id": "A1", "family": "adr", "case_kind": "exact-positive", "user_task": "test"}],
         "conditions": list(CONDITIONS),
         "policies": {"struct-baseline": {"content": "test", "sha256": "a" * 64},
                      "struct-enhanced": {"content": "test", "sha256": "a" * 64}}},
        pair_id="A1",
        condition="struct-baseline",
        attempt_id="attempt-test",
        fresh_context_id_hash="a" * 64,
    )
    assert a == b
    assert a["card_layer"] == "struct-baseline"


def test_condition_not_in_policy_hash():
    """v4 condition must NOT be resolved from policy hash (both arms share it)."""
    protocol = json.loads(Path("docs/metrics/knowledge-precheck-v4/protocol.json").read_bytes())
    base_policy = protocol["policies"]["struct-baseline"]
    enhanced_policy = protocol["policies"]["struct-enhanced"]
    assert base_policy["sha256"] == enhanced_policy["sha256"]
    assert base_policy["content"] == enhanced_policy["content"]

    # Verify that condition_from_packet does NOT use the policy hash
    packet = {
        "schema_version": SCHEMA_VERSION,
        "attempt_id": "attempt-test",
        "pair_id": "A1",
        "family": "adr",
        "user_task": "test",
        "fresh_context_id_hash": "a" * 64,
        "card_layer": "struct-baseline",  # This is the only discriminator
        "l1_policy": {"content": base_policy["content"], "sha256": base_policy["sha256"]},
        "knowledge_gateway_contract": {},
        "trigger_trace_contract": {},
        "response_contract": {},
    }
    condition = condition_from_packet(packet, protocol)
    assert condition == "struct-baseline"

    # Exact same policy content with different card_layer
    packet["card_layer"] = "struct-enhanced"
    condition = condition_from_packet(packet, protocol)
    assert condition == "struct-enhanced"


if __name__ == "__main__":
    test_v4_protocol_closed()
    test_v4_protocol_conditions()
    test_v4_protocol_same_policy()
    test_v4_protocol_orders()
    test_strip_f2_cards()
    test_fake_gateway_strip()
    test_fake_gateway_enhanced()
    test_fake_gateway_drift_rejected()
    test_fake_gateway_stripped_drift_rejected()
    test_condition_from_packet()
    test_model_input_packet()
    test_model_input_packet_unchecked()
    test_condition_not_in_policy_hash()
    print("ALL TESTS PASSED")
