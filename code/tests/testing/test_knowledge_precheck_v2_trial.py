from __future__ import annotations

import json
from pathlib import Path

import pytest

from ldvh.testing.knowledge_precheck_v2 import canonical_sha256
from ldvh.testing.knowledge_precheck_v2_trial import (
    TrialRunnerError,
    build_attempt_blind_packet,
    compile_bundle,
    finalize_output,
    initialize_bundle,
    prepare_attempt,
    record_score,
    seal_bundle,
)

ROOT = Path(__file__).parents[3]
ARTIFACT_ROOT = ROOT / "docs/metrics/knowledge-precheck-v2"


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def _response() -> dict[str, object]:
    return {
        "decision": "non-use",
        "selected_refs": [],
        "first_legal_action": "bounded-action",
        "rationale_codes": ["bounded"],
        "l1_triggered": False,
        "l1_trigger_family": None,
        "l1_trigger_reason_codes": [],
        "refusal_reason_codes": [],
    }


def _score(attempt_id: str, blind: dict[str, object]) -> dict[str, object]:
    return {
        "attempt_id": attempt_id,
        "blind_packet_sha256": canonical_sha256(blind),
        "scorer_model_name": None,
        "scorer_runtime_name": "codex-native-subagent",
        "fresh_scorer_context_id_hash": canonical_sha256([attempt_id, "scorer"]),
        "condition_blind_attested": True,
        "selection_correct": 0,
        "knowledge_adjusted_first_legal_action_correct": 0,
        "action_changed": 0,
        "strong_reuse": 0,
        "correct_non_use": 0,
        "false_f3_expansion": 0,
        "scoring_notes": ["runner fixture"],
    }


def test_runner_enforces_order_and_seals_source_complete_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    initialize_bundle(artifact_root=ARTIFACT_ROOT, bundle_root=bundle)
    protocol = json.loads((bundle / "protocol.json").read_bytes())

    first_task = protocol["tasks"][0]
    wrong_condition = protocol["condition_orders"][0][1]
    with pytest.raises(TrialRunnerError, match="condition order"):
        prepare_attempt(
            root=bundle,
            pair_id=first_task["pair_id"],
            condition=wrong_condition,
            fresh_context_id_hash=canonical_sha256(["wrong"]),
        )

    for task_index, task in enumerate(protocol["tasks"]):
        for condition in protocol["condition_orders"][task_index]:
            packet = prepare_attempt(
                root=bundle,
                pair_id=task["pair_id"],
                condition=condition,
                fresh_context_id_hash=canonical_sha256([task["pair_id"], condition, "fresh"]),
            )
            attempt_id = packet["attempt_id"]
            response_file = tmp_path / f"response-{attempt_id}.json"
            score_file = tmp_path / f"score-{attempt_id}.json"
            _write(response_file, _response())
            finalize_output(root=bundle, attempt_id=attempt_id, response_file=response_file)
            blind = build_attempt_blind_packet(root=bundle, attempt_id=attempt_id)
            assert "condition" not in json.dumps(blind, ensure_ascii=False)
            _write(score_file, _score(attempt_id, blind))
            record_score(root=bundle, attempt_id=attempt_id, score_file=score_file)

    manifest = seal_bundle(bundle)
    assert len(manifest["model_input_files"]) == 24
    assert len(manifest["model_output_files"]) == 24
    first = compile_bundle(root=bundle, output_root=tmp_path / "compiled-1")
    second = compile_bundle(root=bundle, output_root=tmp_path / "compiled-2")
    assert first == second
