"""Focused tests for the v6 action-semantic trigger calibration protocol and gateway."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, "code")

from ldvh.testing.knowledge_precheck_v2 import bytes_sha256
from ldvh.testing.knowledge_precheck_v6 import (
    _ACTION_DELTA_FIELDS,
    _ACTIVATION_HIT_FIELDS,
    _ACTIVATION_TRACE_FIELDS,
    _EXCHANGE_FIELDS,
    _OUTPUT_FIELDS,
    _RESPONSE_FIELDS,
    _SCORE_FIELDS,
    _SCORER_RESPONSE_FIELDS,
    _SOURCE_SNAPSHOT_FIELDS,
    _TRIGGER_RESPONSE_FIELDS,
    ACTIVATION_TRACE_SCHEMA_VERSION,
    CONDITIONS,
    EVIDENCE_SCHEMA_VERSION,
    SCHEMA_VERSION,
    KnowledgePrecheckV6Error,
    ReadOnlyKnowledgeGateway,
    build_model_input_packet,
    build_model_input_packet_unchecked,
    build_trigger_trace,
    condition_from_packet,
    is_valid_structured_response,
    validate_activation_trace,
    validate_f3_decision_response,
    validate_model_input_packet,
    validate_model_output,
    validate_protocol,
    validate_score,
    validate_scorer_response,
    validate_trigger_response,
    validate_trigger_trace,
)

_OBJECT_SET_FINGERPRINT = "43678e7d3e10caf25af7ea88e2a404b255b552f57a35c20124403953b17961af"


def _fingerprint(content: str) -> str:
    return bytes_sha256(content.encode("utf-8"))


def _protocol() -> dict[str, Any]:
    return json.loads(Path("docs/metrics/knowledge-precheck-v6/protocol.json").read_bytes())


def _snapshot() -> dict[str, Any]:
    return json.loads(Path("docs/metrics/knowledge-precheck-v6/source-snapshot.json").read_bytes())


# ---------------------------------------------------------------------------
# Protocol validation
# ---------------------------------------------------------------------------


def test_v6_protocol_closed():
    """The v6 protocol must validate without errors."""
    problems = validate_protocol(_protocol())
    assert not problems, f"protocol problems: {problems}"


def test_v6_protocol_conditions():
    """Conditions must be calibration-baseline and calibration-enhanced."""
    protocol = _protocol()
    assert protocol["conditions"] == list(CONDITIONS)


def test_v6_protocol_conditions_constant():
    """The v6 CONDITIONS constant must be the calibration pair."""
    assert CONDITIONS == ("calibration-baseline", "calibration-enhanced")


def test_v6_protocol_schema_version_tampered():
    """Tampered schema_version must be rejected."""
    tampered = deepcopy(_protocol())
    tampered["schema_version"] = "ldvh-knowledge-precheck-v6/999"
    problems = validate_protocol(tampered)
    assert "schema-version" in problems


def test_v6_protocol_conditions_tampered():
    """Tampered conditions must be rejected."""
    tampered = deepcopy(_protocol())
    tampered["conditions"] = ["calibration-baseline"]
    problems = validate_protocol(tampered)
    assert "conditions" in problems


def test_v6_protocol_policies_keys_tampered():
    """Tampered policy keys must be rejected."""
    protocol = _protocol()
    tampered = deepcopy(protocol)
    tampered["policies"] = {"calibration-baseline": protocol["policies"]["calibration-baseline"]}
    problems = validate_protocol(tampered)
    assert "policies" in problems


def test_v6_protocol_ceilings_tampered():
    """Tampered ceilings must be rejected."""
    tampered = deepcopy(_protocol())
    tampered["ceilings"] = dict(tampered["ceilings"], maximum_member_launches=999)
    problems = validate_protocol(tampered)
    assert "ceilings" in problems


def test_v6_protocol_orders():
    """Condition orders must be 9/9 balanced."""
    orders = _protocol()["condition_orders"]
    assert len(orders) == 18
    assert sum(1 for o in orders if o == ["calibration-baseline", "calibration-enhanced"]) == 9
    assert sum(1 for o in orders if o == ["calibration-enhanced", "calibration-baseline"]) == 9


# ---------------------------------------------------------------------------
# Source snapshot dual card set structure
# ---------------------------------------------------------------------------


def test_v6_source_snapshot_dual_card_sets():
    """Source snapshot must have both card sets covering every knowledge family."""
    snapshot = _snapshot()
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]
    assert "family_cards_baseline" in snapshot
    assert "family_cards_activation" in snapshot
    assert set(baseline) == {"adr", "pitfall", "study"}
    assert set(activation) == {"adr", "pitfall", "study"}
    # Card counts per family match (adr=5, pitfall=6, study=21)
    for family in ("adr", "pitfall", "study"):
        assert len(baseline[family]) == len(activation[family])
        assert len(baseline[family]) == snapshot["family_counts"][family]["active"]


def test_v6_activation_cards_have_projection_structure():
    """Activation-projected cards must contain activation_means and suggested_action."""
    activation = _snapshot()["family_cards_activation"]
    for family in ("adr", "pitfall", "study"):
        for card in activation[family]:
            assert "activation_means" in card, f"{family} activation card missing activation_means"
            assert "suggested_action" in card, f"{family} activation card missing suggested_action"
            # Activation cards have the original knowledge-body fields nested under knowledge_body.fields
            assert "knowledge_body" in card, f"{family} activation card missing knowledge_body"
            body = card["knowledge_body"]
            assert "fields" in body
            assert "object_uid" in body["fields"]


def test_v6_baseline_cards_have_original_structure():
    """Baseline cards must be whole Helper cards with the original knowledge-body fields."""
    baseline = _snapshot()["family_cards_baseline"]
    for family in ("adr", "pitfall", "study"):
        for card in baseline[family]:
            assert "fields" in card
            assert "object_uid" in card["fields"]
            assert "object_id" in card["fields"]
            assert "title" in card["fields"]
            # Should NOT have projection fields
            assert "activation_means" not in card
            assert "suggested_action" not in card


def test_v6_source_snapshot_family_coverage():
    """knowledge_ref_families must bind the frozen task gold refs (Study refs are unknown)."""
    snapshot = _snapshot()
    families = snapshot["knowledge_ref_families"]
    task_families = {task["family"] for task in _protocol()["tasks"]}
    assert task_families == {"adr", "pitfall", "study"}
    known = {family for family in families.values() if family != "unknown"}
    # The v6 snapshot maps the Study refs to "unknown" (unclassified), so only
    # adr/pitfall are recorded with a known family.
    assert known == {"adr", "pitfall"}
    assert "unknown" in families.values()
    # Every gold-bound ref must be present in the family map
    for task in _protocol()["tasks"]:
        all_refs = task["gold"]["applicable_refs"] + task["gold"]["tempting_nonapplicable_refs"]
        for ref in all_refs:
            assert ref in families


# ---------------------------------------------------------------------------
# v6 policies reference
# ---------------------------------------------------------------------------


def test_v6_l1_policy_per_condition():
    """The model input packet must reference the frozen policy text per condition."""
    protocol = _protocol()
    for condition in CONDITIONS:
        packet = build_model_input_packet(
            protocol,
            pair_id="A1",
            condition=condition,
            attempt_id=f"attempt-policy-{condition}",
            fresh_context_id_hash="a" * 64,
        )
        expected = protocol["policies"][condition]
        assert packet["l1_policy"]["content"] == expected["content"]
        assert packet["l1_policy"]["sha256"] == expected["sha256"]
        assert packet["card_layer"] == condition


def test_v6_baseline_policy_matches_v5_activation_enhanced():
    """The v6 calibration-baseline policy must be the v5 activation-enhanced policy."""
    v6_protocol = _protocol()
    v5_protocol = json.loads(Path("docs/metrics/knowledge-precheck-v5/protocol.json").read_bytes())
    baseline = v6_protocol["policies"]["calibration-baseline"]
    v5_enhanced = v5_protocol["policies"]["activation-enhanced"]
    assert baseline["content"] == v5_enhanced["content"]
    assert baseline["sha256"] == v5_enhanced["sha256"]
    # The v6 enhanced policy must be a distinct action-semantic trigger policy
    enhanced = v6_protocol["policies"]["calibration-enhanced"]
    assert enhanced["content"] != baseline["content"]
    assert "action-anchor" in enhanced["content"]


# ---------------------------------------------------------------------------
# Gateway: activation card set selection
# ---------------------------------------------------------------------------


def _fake_activation_cards_dispatch(family_cards_baseline):
    """Create a fake dispatch returning the frozen baseline cards (whole Helper cards)."""

    def fake_dispatch(operation, request_bytes):
        del operation
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


def _f2_request(family: str) -> dict[str, Any]:
    return {
        "arguments": {
            "governed_project_id": "ldvh",
            "card_layer": "F2",
            "fact_type_keys": [family],
            "statuses": ["active"],
        }
    }


def test_v6_gateway_baseline_arm():
    """Gateway with calibration-baseline must validate against family_cards_baseline."""
    snapshot = _snapshot()
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]

    gateway = ReadOnlyKnowledgeGateway(
        _fake_activation_cards_dispatch(baseline),
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        _f2_request("adr"),
        exchange_id="e1",
        attempt_id="a1",
        card_layer="calibration-baseline",
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
    # The baseline arm serves the raw Helper cards unchanged
    assert exchange["served_cards"] == observed


def test_v6_gateway_enhanced_arm():
    """Gateway with calibration-enhanced must project the activation card set."""
    snapshot = _snapshot()
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]

    gateway = ReadOnlyKnowledgeGateway(
        _fake_activation_cards_dispatch(baseline),
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        _f2_request("adr"),
        exchange_id="e2",
        attempt_id="a2",
        card_layer="calibration-enhanced",
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
    # The raw Helper response stays byte-identical (source-complete): its cards
    # remain the baseline shape and differ from what the model was served.
    raw_cards = json.loads(exchange["raw_response_utf8"])["result"]["cards"]
    assert [card["fields"] for card in raw_cards] == [card["fields"] for card in baseline["adr"]]
    assert served != raw_cards


# ---------------------------------------------------------------------------
# Gateway drift / invalid request rejection
# ---------------------------------------------------------------------------


def test_v6_gateway_drift_rejected():
    """Gateway must reject drifted F2 cards."""
    snapshot = _snapshot()
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]

    def fake_dispatch(operation, request_bytes):
        del operation
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
    with pytest.raises(KnowledgePrecheckV6Error, match="drifted"):
        gateway.call(
            "find-fact-object-candidates",
            _f2_request("adr"),
            exchange_id="e1",
            attempt_id="a1",
            card_layer="calibration-baseline",
        )


def test_v6_gateway_fingerprint_drift_rejected():
    """Gateway must reject drifted F3 fingerprints."""
    snapshot = _snapshot()
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]

    def fake_dispatch(operation, request_bytes):
        # Return a valid F3 response but with a wrong fingerprint
        del operation
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
    with pytest.raises(KnowledgePrecheckV6Error, match="drifted"):
        gateway.call(
            "read-fact-objects",
            {"arguments": {"fact_refs": [{"object_uid": "019ffb52-ebb5-724c-881f-4f0f7d97038f"}]}},
            exchange_id="e1",
            attempt_id="a1",
        )


def test_v6_gateway_rejects_unknown_operation():
    """Gateway must reject an unknown/state-changing Helper operation."""
    gateway = ReadOnlyKnowledgeGateway(
        _fake_activation_cards_dispatch(_snapshot()["family_cards_baseline"]),
        expected_f2_cards_baseline=_snapshot()["family_cards_baseline"],
        expected_f2_cards_activation=_snapshot()["family_cards_activation"],
    )
    with pytest.raises(KnowledgePrecheckV6Error, match="not allowlisted"):
        gateway.call("write-facts", {"arguments": {}}, exchange_id="e1", attempt_id="a1")


def test_v6_gateway_rejects_workspace_root():
    """Gateway must reject arguments.workspace_root."""
    gateway = ReadOnlyKnowledgeGateway(
        _fake_activation_cards_dispatch(_snapshot()["family_cards_baseline"]),
        expected_f2_cards_baseline=_snapshot()["family_cards_baseline"],
        expected_f2_cards_activation=_snapshot()["family_cards_activation"],
    )
    request = _f2_request("adr")
    request["arguments"]["workspace_root"] = "/tmp/evil"
    with pytest.raises(KnowledgePrecheckV6Error, match="workspace_root"):
        gateway.call(
            "find-fact-object-candidates",
            request,
            exchange_id="e1",
            attempt_id="a1",
            card_layer="calibration-baseline",
        )


def test_v6_gateway_rejects_state_changing_response():
    """Gateway must reject a Helper response that observed state changes."""
    snapshot = _snapshot()
    baseline = snapshot["family_cards_baseline"]
    activation = snapshot["family_cards_activation"]
    frozen = json.loads(
        Path("docs/metrics/knowledge-precheck-v6/source-observations/adr-f2.response.json").read_bytes()
    )
    frozen = deepcopy(frozen)
    frozen["changes"] = [{"summary": "wrote something", "status": "changed"}]

    gateway = ReadOnlyKnowledgeGateway(
        lambda operation, request_bytes: json.dumps(frozen).encode("utf-8"),
        expected_f2_cards_baseline=baseline,
        expected_f2_cards_activation=activation,
    )
    with pytest.raises(KnowledgePrecheckV6Error, match="state-changing"):
        gateway.call(
            "find-fact-object-candidates",
            _f2_request("adr"),
            exchange_id="e1",
            attempt_id="a1",
            card_layer="calibration-baseline",
        )


# ---------------------------------------------------------------------------
# Condition leakage rejection
# ---------------------------------------------------------------------------


def test_v6_condition_leakage_packet():
    """Model input packet must not leak the other condition identifier."""
    protocol = _protocol()
    for condition in CONDITIONS:
        packet = build_model_input_packet(
            protocol,
            pair_id="A1",
            condition=condition,
            attempt_id=f"attempt-test-leakage-{condition}",
            fresh_context_id_hash="a" * 64,
        )
        other = [c for c in CONDITIONS if c != condition][0]
        assert other not in packet.get("card_layer", "")
        assert other not in packet.get("l1_policy", {}).get("content", "")


def test_v6_condition_from_packet():
    """condition_from_packet must resolve from the card_layer field."""
    protocol = _protocol()
    packet = {
        "schema_version": SCHEMA_VERSION,
        "attempt_id": "attempt-test",
        "pair_id": "A1",
        "family": "adr",
        "user_task": "test",
        "fresh_context_id_hash": "a" * 64,
        "card_layer": "calibration-baseline",
        "l1_policy": {"content": "test", "sha256": "a" * 64},
        "knowledge_gateway_contract": {},
        "trigger_trace_contract": {},
        "response_contract": {},
    }
    assert condition_from_packet(packet, protocol) == "calibration-baseline"
    packet["card_layer"] = "calibration-enhanced"
    assert condition_from_packet(packet, protocol) == "calibration-enhanced"


# ---------------------------------------------------------------------------
# F3-before-F2, cross-family, write/unknown, arguments.workspace_root contract
# ---------------------------------------------------------------------------


def test_v6_model_input_contract_rejects_workspace_root():
    """Model input must forbid arguments.workspace_root and writes."""
    packet = build_model_input_packet(
        _protocol(),
        pair_id="A1",
        condition="calibration-baseline",
        attempt_id="attempt-test-ws",
        fresh_context_id_hash="a" * 64,
    )
    contract = packet["knowledge_gateway_contract"]
    assert contract["arguments_workspace_root"] == "forbidden"
    assert contract["writes"] == "forbidden"
    assert "F2 then one F3" in contract["sequence"]
    assert contract["allowed_operations"] == ["find-fact-object-candidates", "read-fact-objects"]


def test_v6_model_input_packet():
    """build_model_input_packet must include the card_layer field."""
    protocol = _protocol()
    packet = build_model_input_packet(
        protocol,
        pair_id="A1",
        condition="calibration-baseline",
        attempt_id="attempt-test",
        fresh_context_id_hash="a" * 64,
    )
    assert packet["card_layer"] == "calibration-baseline"
    assert packet["schema_version"] == SCHEMA_VERSION
    validate_model_input_packet(packet, protocol)


def test_v6_model_input_packet_unchecked():
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
            "calibration-baseline": {"content": "test", "sha256": "a" * 64},
            "calibration-enhanced": {"content": "test", "sha256": "a" * 64},
        },
    }
    a = build_model_input_packet_unchecked(
        minimal,
        pair_id="A1",
        condition="calibration-baseline",
        attempt_id="attempt-test",
        fresh_context_id_hash="a" * 64,
    )
    b = build_model_input_packet_unchecked(
        minimal,
        pair_id="A1",
        condition="calibration-baseline",
        attempt_id="attempt-test",
        fresh_context_id_hash="a" * 64,
    )
    assert a == b
    assert a["card_layer"] == "calibration-baseline"


def test_v6_model_input_packet_tamper_rejected():
    """validate_model_input_packet must reject a tampered packet (anti-tamper)."""
    protocol = _protocol()
    packet = build_model_input_packet(
        protocol,
        pair_id="A1",
        condition="calibration-baseline",
        attempt_id="attempt-test-tamper",
        fresh_context_id_hash="a" * 64,
    )
    tampered = deepcopy(packet)
    tampered["l1_policy"]["content"] = "TAMPERED POLICY"
    with pytest.raises(KnowledgePrecheckV6Error, match="deterministic frozen projection"):
        validate_model_input_packet(tampered, protocol)


# ---------------------------------------------------------------------------
# Trigger trace validation
# ---------------------------------------------------------------------------


def _make_trigger_response(triggered: bool, family: str) -> dict[str, Any]:
    return {
        "triggered": triggered,
        "trigger_family": family if triggered else None,
        "positive_condition_codes": ["observed-signal"] if triggered else [],
        "veto_condition_codes": [],
    }


def test_v6_trigger_response_closed():
    """validate_trigger_response must enforce the closed field set and trigger rules."""
    packet = build_model_input_packet(
        _protocol(),
        pair_id="A1",
        condition="calibration-baseline",
        attempt_id="attempt-trigger",
        fresh_context_id_hash="a" * 64,
    )
    positive = _make_trigger_response(True, "adr")
    validate_trigger_response(positive, "adr")
    assert set(positive) == _TRIGGER_RESPONSE_FIELDS
    trace = build_trigger_trace(positive, packet, _protocol())
    validate_trigger_trace(trace, packet, _protocol())
    assert trace["condition"] == "calibration-baseline"

    # A positive trigger for a different family is inconsistent
    with pytest.raises(KnowledgePrecheckV6Error, match="trigger family"):
        validate_trigger_response(_make_trigger_response(True, "adr"), "pitfall")
    # A vetoed positive signal must name a veto
    vetoed = {
        "triggered": False,
        "trigger_family": None,
        "positive_condition_codes": ["observed-signal"],
        "veto_condition_codes": [],
    }
    with pytest.raises(KnowledgePrecheckV6Error, match="veto"):
        validate_trigger_response(vetoed, "adr")


def test_v6_trigger_trace_binding():
    """validate_trigger_trace must reject a mismatched condition binding."""
    protocol = _protocol()
    packet = build_model_input_packet(
        protocol,
        pair_id="A1",
        condition="calibration-baseline",
        attempt_id="attempt-trigger-binding",
        fresh_context_id_hash="a" * 64,
    )
    response = _make_trigger_response(False, "adr")
    trace = build_trigger_trace(response, packet, protocol)
    assert trace["condition"] == "calibration-baseline"
    assert trace["triggered"] is False

    tampered = deepcopy(trace)
    tampered["condition"] = "calibration-enhanced"
    with pytest.raises(KnowledgePrecheckV6Error, match="condition binding"):
        validate_trigger_trace(tampered, packet, protocol)


# ---------------------------------------------------------------------------
# Activation trace
# ---------------------------------------------------------------------------


def _make_activation_trace() -> dict[str, Any]:
    return {
        "schema_version": ACTIVATION_TRACE_SCHEMA_VERSION,
        "attempt_id": "attempt-test",
        "pair_id": "A1",
        "condition": "calibration-baseline",
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


def test_v6_validate_activation_trace_field_closed():
    """validate_activation_trace must validate the closed field set."""
    trace = _make_activation_trace()
    validate_activation_trace(trace)
    assert set(trace) == _ACTIVATION_TRACE_FIELDS
    assert set(trace["activation_hits"][0]) == _ACTIVATION_HIT_FIELDS
    assert set(trace["action_delta"]) == _ACTION_DELTA_FIELDS

    with pytest.raises(KnowledgePrecheckV6Error):
        validate_activation_trace({**trace, "extra_field": "value"})


def test_v6_validate_activation_trace_hit_stage():
    """validate_activation_trace must validate hit_stage closed set."""
    bad = deepcopy(_make_activation_trace())
    bad["activation_hits"][0]["hit_stage"] = "invalid-stage"
    with pytest.raises(KnowledgePrecheckV6Error):
        validate_activation_trace(bad)


def test_v6_validate_activation_trace_action_delta_fields():
    """validate_activation_trace must validate action_delta fields."""
    bad = deepcopy(_make_activation_trace())
    del bad["action_delta"]["first_legal_action"]
    with pytest.raises(KnowledgePrecheckV6Error):
        validate_activation_trace(bad)


def test_v6_activation_trace_schema_version():
    """Activation trace schema version must be the v6 constant."""
    assert ACTIVATION_TRACE_SCHEMA_VERSION == "ldvh-knowledge-precheck-v6-activation-trace/1"


# ---------------------------------------------------------------------------
# Model output / structured response validation
# ---------------------------------------------------------------------------


def _valid_response() -> dict[str, Any]:
    return {
        "decision": "wait",
        "selected_refs": [],
        "first_legal_action": "wait",
        "rationale_codes": ["none"],
        "refusal_reason_codes": [],
    }


def test_v6_model_output_validation():
    """validate_model_output must accept a valid closed model output."""
    protocol = _protocol()
    packet = build_model_input_packet(
        protocol,
        pair_id="A1",
        condition="calibration-baseline",
        attempt_id="attempt-output",
        fresh_context_id_hash="a" * 64,
    )
    output = {
        "attempt_id": packet["attempt_id"],
        "pair_id": packet["pair_id"],
        "condition": "calibration-baseline",
        "model_name": None,
        "agent_runtime_name": "codex-native-subagent",
        "fresh_context_id_hash": packet["fresh_context_id_hash"],
        "structured_response": _valid_response(),
        "helper_exchange_ids": [],
        "usage": "unavailable",
        "latency": "unavailable",
    }
    validate_model_output(output, protocol)
    assert set(output) == _OUTPUT_FIELDS
    assert set(output["structured_response"]) == _RESPONSE_FIELDS


def test_v6_is_valid_structured_response():
    """is_valid_structured_response must reject an unclosed structured response."""
    protocol = _protocol()
    packet = build_model_input_packet(
        protocol,
        pair_id="A1",
        condition="calibration-baseline",
        attempt_id="attempt-isvalid",
        fresh_context_id_hash="a" * 64,
    )
    assert is_valid_structured_response(_valid_response(), packet=packet, protocol=protocol)
    assert not is_valid_structured_response({"decision": "wait"}, packet=packet, protocol=protocol)


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


def test_v6_validate_score_0_3():
    """validate_score must accept 0-3 action_bridge_score and be closed on fields."""
    for score_val in (0, 1, 2, 3):
        score = _make_valid_score(score_val)
        validate_score(score)
        assert set(score) == _SCORE_FIELDS
        assert set(_make_valid_scorer_response(score_val)) == _SCORER_RESPONSE_FIELDS


def test_v6_validate_score_out_of_range():
    """validate_score must reject out-of-range action_bridge_score."""
    for score_val in (-1, 4, 999):
        with pytest.raises(KnowledgePrecheckV6Error):
            validate_score(_make_valid_score(score_val))


def test_v6_validate_scorer_response_0_3():
    """validate_scorer_response must accept 0-3 action_bridge_score."""
    for score_val in (0, 1, 2, 3):
        validate_scorer_response(_make_valid_scorer_response(score_val))


def test_v6_validate_scorer_response_out_of_range():
    """validate_scorer_response must reject out-of-range action_bridge_score."""
    for score_val in (-1, 4, 999):
        with pytest.raises(KnowledgePrecheckV6Error):
            validate_scorer_response(_make_valid_scorer_response(score_val))


def test_v6_validate_scorer_response_strong_reuse_inconsistent():
    """strong_reuse=True requires the other substantive action fields."""
    inconsistent = _make_valid_scorer_response(3)
    inconsistent["strong_reuse"] = True
    inconsistent["action_changed"] = False
    with pytest.raises(KnowledgePrecheckV6Error, match="internally inconsistent"):
        validate_scorer_response(inconsistent)


# ---------------------------------------------------------------------------
# Evidence field closures (anti-tamper)
# ---------------------------------------------------------------------------


def test_v6_evidence_field_closures():
    """Evidence field closures must match the frozen v6 sets."""
    assert set(_make_valid_score(2)) == _SCORE_FIELDS
    assert set(_make_valid_scorer_response(2)) == _SCORER_RESPONSE_FIELDS
    output = {
        "attempt_id": "attempt-test",
        "pair_id": "A1",
        "condition": "calibration-baseline",
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


def test_v6_exchange_field_closure():
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


def test_v6_evidence_schema_version():
    """Evidence schema version must be the v6 constant."""
    assert EVIDENCE_SCHEMA_VERSION == "ldvh-knowledge-precheck-v6-evidence/1"


# ---------------------------------------------------------------------------
# Source snapshot / anti-tamper
# ---------------------------------------------------------------------------


def test_v6_source_snapshot_fields_closed():
    """Source snapshot fields must be closed."""
    assert set(_snapshot()) == _SOURCE_SNAPSHOT_FIELDS


# ---------------------------------------------------------------------------
# F3 decision response validation
# ---------------------------------------------------------------------------


def test_v6_validate_f3_decision_response():
    """validate_f3_decision_response must accept valid refs."""
    families = _snapshot()["knowledge_ref_families"]
    refs = validate_f3_decision_response(
        {"read_f3_refs": ["019ffb52-ebb5-724c-881f-4f0f7d97038f"]},
        family="adr",
        snapshot_families=families,
    )
    assert refs == ["019ffb52-ebb5-724c-881f-4f0f7d97038f"]


def test_v6_validate_f3_decision_response_too_many():
    """validate_f3_decision_response must reject >2 refs."""
    families = _snapshot()["knowledge_ref_families"]
    with pytest.raises(KnowledgePrecheckV6Error):
        validate_f3_decision_response(
            {"read_f3_refs": ["a", "b", "c"]},
            family="adr",
            snapshot_families=families,
        )


def test_v6_validate_f3_decision_response_cross_family_rejected():
    """validate_f3_decision_response must reject a known different-family UID."""
    families = _snapshot()["knowledge_ref_families"]
    pitfall_uid = "019ffb52-ebb5-705a-aa9b-e2ac31dfc7cb"
    assert families[pitfall_uid] == "pitfall"
    with pytest.raises(KnowledgePrecheckV6Error, match="crossed the frozen task family"):
        validate_f3_decision_response(
            {"read_f3_refs": [pitfall_uid]},
            family="adr",
            snapshot_families=families,
        )
    # An unclassified (unknown) ref is allowed from any family (Study refs).
    unknown_uid = next(uid for uid, family in families.items() if family == "unknown")
    validate_f3_decision_response(
        {"read_f3_refs": [unknown_uid]},
        family="study",
        snapshot_families=families,
    )


if __name__ == "__main__":
    print("tests are exercised through pytest only")
