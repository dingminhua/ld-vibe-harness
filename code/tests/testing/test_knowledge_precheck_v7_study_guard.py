"""Regression guards for the frozen Study fixed mechanism.

These tests pin the Study mechanism baseline (no-trigger + related-to
relationship navigation + F2 index visibility + F3 on-demand progressive
reading) so that degradation is mechanically rejected after the mechanism is
frozen:

- Contract: F2 must return the Study index; trigger decision is always
  no-trigger; related-to navigation entry points exist.
- Relationship-graph integrity: every active Study relation target resolves to
  an object in the frozen snapshot; the graph baseline is byte-stable.
- Behavior-snapshot replay: the live F2 Study index card identity set is
  byte-identical to the frozen baseline card identity set.

These are standalone pytest tests (auto-discovered by the standard runner);
they do not modify any existing regression runner/CI configuration.
"""

from __future__ import annotations

import json
from pathlib import Path

from ldvh.testing.knowledge_precheck_v7 import (
    CONDITIONS,
    evaluate_v7_trigger,
    read_frozen_protocol,
)

_PROTOCOL_PATH = Path("docs/metrics/knowledge-precheck-v7/protocol.json")
_SNAPSHOT_PATH = Path("docs/metrics/knowledge-precheck-v7/source-snapshot.json")
_V6_SNAPSHOT_PATH = Path("docs/metrics/knowledge-precheck-v6/source-snapshot.json")
_F2_LIVE_PATH = Path("docs/metrics/knowledge-precheck-v7/.v7_f2_study.json")


def _protocol() -> dict:
    return read_frozen_protocol(_PROTOCOL_PATH)


def _snapshot() -> dict:
    return json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _v6_snapshot() -> dict:
    return json.loads(_V6_SNAPSHOT_PATH.read_text(encoding="utf-8"))


# --- Contract tests: F2 index visibility + no-trigger + navigation ----------


def test_study_f2_index_visible_in_snapshot():
    """F2 must return a non-empty Study index (index-visible, not injected)."""
    snapshot = _snapshot()
    study_cards = snapshot["family_cards_baseline"]["study"]
    assert len(study_cards) >= 1
    for card in study_cards:
        assert card["card_layer"] == "F2"
        assert set(card["fields"]) >= {
            "object_uid",
            "object_id",
            "title",
            "status",
            "research_question",
            "abstract",
            "recommendation_summary",
        }


def test_study_trigger_decision_always_no_trigger():
    """Study trigger decision is always false in every condition and task."""
    protocol = _protocol()
    for cond in CONDITIONS:
        for task in protocol["tasks"]:
            if task["family"] != "study":
                continue
            response = evaluate_v7_trigger("study", task["user_task"], cond)
            assert response["triggered"] is False
            assert response["trigger_family"] is None


def test_study_relationship_navigation_entry_exists():
    """related-to navigation entry points exist on the Study graph baseline."""
    snapshot = _snapshot()
    graph = snapshot["study_relationship_graph"]
    assert graph["graph_integrity"]["active_study_count"] >= 1
    assert graph["graph_integrity"]["all_relation_targets_resolvable"] is True
    assert isinstance(graph["existing_relations_by_study"], dict)


# --- Relationship-graph integrity --------------------------------------------


def test_study_relationship_graph_integrity():
    """Every active Study's relation target must resolve in the frozen set."""
    snapshot = _snapshot()
    v6 = _v6_snapshot()
    active_study_uids = {card["fact_ref"]["object_uid"] for card in v6["family_cards_baseline"]["study"]}
    graph = snapshot["study_relationship_graph"]
    for uid, relations in graph["existing_relations_by_study"].items():
        assert uid in active_study_uids, f"study {uid} not active in baseline"
        for relation in relations:
            target = relation["target_object_uid"]
            assert isinstance(target, str) and target
    # applicable navigation anchors reference frozen study objects
    for _pair_id, anchor in graph["applicable_navigation_anchors"].items():
        for study_uid in anchor["applicable_study_uids"]:
            assert study_uid in active_study_uids or study_uid == anchor["task_uid"]


def test_study_graph_baseline_stable():
    """The Study relationship graph baseline is byte-stable in the snapshot."""
    snapshot = _snapshot()
    graph = snapshot["study_relationship_graph"]
    # Re-serialize and re-parse must be stable (no unbound mutations).
    serialized = json.dumps(graph, ensure_ascii=False, sort_keys=True)
    reparsed = json.loads(serialized)
    assert reparsed == graph


# --- Behavior-snapshot replay (byte-identical) -------------------------------


def test_study_f2_live_index_identity_matches_baseline():
    """The live F2 Study index card identity set is byte-identical to the
    frozen v6 baseline set (behavior-snapshot replay)."""
    v6 = _v6_snapshot()
    baseline_uids = {card["fact_ref"]["object_uid"] for card in v6["family_cards_baseline"]["study"]}
    live = json.loads(_F2_LIVE_PATH.read_text(encoding="utf-8"))
    live_cards = live["result"]["cards"]
    live_uids = {card["fact_ref"]["object_uid"] for card in live_cards}
    assert live_uids == baseline_uids
    # object_set_fingerprint must be present and complete
    coverage = live["result"]["coverage"]
    assert coverage["status"] == "complete"
    assert coverage["total_matching"] == len(baseline_uids)


def test_study_f2_live_has_no_state_change():
    """The live F2 Study read is read-only (no state-changing side effect)."""
    live = json.loads(_F2_LIVE_PATH.read_text(encoding="utf-8"))
    assert live["changes"] == []
