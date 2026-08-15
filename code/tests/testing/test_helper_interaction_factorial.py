from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ldvh.testing.helper_interaction_factorial import (
    build_gold_after,
    canonical_sha256,
    expand_assignments,
    extract_session_metrics,
    interaction_estimate,
    paired_differences,
    paired_estimate,
    retained_record_problems,
    score_raw_request,
    validate_protocol,
)

ROOT = Path(__file__).parents[3]
PROTOCOL_PATH = ROOT / "docs/metrics/wc-c-factorial-protocol-v1.json"
RESULTS_PATH = ROOT / "docs/metrics/wc-c-factorial-results-v1.json"


@pytest.fixture
def protocol() -> dict[str, object]:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def _request(protocol: dict[str, object], phase2: str) -> dict[str, object]:
    task = protocol["task_package"]["synthetic_update_task"]
    arguments: dict[str, object] = {
        "fact_ref": task["fact_ref"],
        "expected_content_fingerprint": task["expected_content_fingerprint"],
    }
    if phase2 == "full_object":
        arguments["fact_object"] = build_gold_after(protocol)
    else:
        arguments["item_event"] = {
            "event_key": "update-work-item-checkpoint",
            "item_id": task["target_item_id"],
            "current_summary": task["new_current_summary"],
            "resume_from": task["new_resume_from"],
            "change_summary": task["change_summary"],
        }
    return {
        "arguments": arguments,
        "observed_context": {"signature": task["observed_signature"]},
    }


def test_protocol_is_frozen_balanced_and_mechanically_valid(protocol: dict[str, object]) -> None:
    assert validate_protocol(protocol) == ()
    assert canonical_sha256(protocol["task_package"]) == protocol["fixed_runner"][
        "task_package_sha256"
    ]
    assignments = expand_assignments(protocol)
    assert len(assignments) == 40
    assert len({item["trial_id"] for item in assignments}) == 40
    assert {key: sum(item["cell_key"] == key for item in assignments) for key in protocol["cells"]} == {
        key: 10 for key in protocol["cells"]
    }


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for member in value.values() for key in _all_keys(member)}
    if isinstance(value, list):
        return {key for member in value for key in _all_keys(member)}
    return set()


def test_results_are_balanced_hash_bound_and_privacy_closed(protocol: dict[str, object]) -> None:
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    records = results["records"]
    assert len(records) == 40
    assert results["records_sha256"] == canonical_sha256(records)
    assert results["sample"] == {
        "all_session_comparability": "comparable",
        "attempts": 43,
        "cells": {key: 10 for key in sorted(protocol["cells"])},
        "fixed_model": "gpt-5.6-sol",
        "phase1_control": 20,
        "phase1_treatment": 20,
        "phase2_control": 20,
        "phase2_treatment": 20,
        "pairing": "replay",
        "primary_attempts": 40,
        "state_changing_helper_calls": 0,
        "technical_replacements": 3,
        "valid_records": 40,
    }
    assert [item["attempt_ordinal"] for item in results["excluded_attempts"]] == [9, 20, 25]
    assert all(retained_record_problems(record, protocol) == () for record in records)
    assert all(record["identity_verdict"] == "match" for record in records)
    assert all(record["state_changing_helper_calls"] == 0 for record in records)
    assert not (_all_keys(results) & set(protocol["artifact_denylist"]))
    assert results["privacy"]["raw_prompt_or_command_or_request_body_retained"] is False
    assert results["privacy"]["session_ids_retained"] is False
    assert results["residual_judgment"]["value"] == "significant"


@pytest.mark.parametrize("phase2", ["full_object", "item_event"])
def test_raw_request_scores_before_projection_without_repair(
    protocol: dict[str, object], phase2: str
) -> None:
    request = _request(protocol, phase2)
    scored = score_raw_request(request, phase2=phase2, protocol=protocol)
    assert scored["raw_request_valid"] is True
    assert scored["projected_after_valid"] is True
    assert scored["score_codes"] == ["valid"]
    assert scored["raw_request_sha256"] == canonical_sha256(request)
    if phase2 == "item_event":
        full_bytes = score_raw_request(
            _request(protocol, "full_object"), phase2="full_object", protocol=protocol
        )["raw_request_bytes"]
        assert scored["raw_request_bytes"] < full_bytes


def test_raw_request_rejects_dual_alternatives_without_repair(protocol: dict[str, object]) -> None:
    request = _request(protocol, "item_event")
    request["arguments"]["fact_object"] = build_gold_after(protocol)
    scored = score_raw_request(request, phase2="item_event", protocol=protocol)
    assert scored["raw_request_valid"] is False
    assert scored["projected_after_valid"] is False
    assert any("必须且只能出现一个" in code for code in scored["score_codes"])


def test_raw_request_keeps_raw_valid_separate_from_after_valid(protocol: dict[str, object]) -> None:
    request = _request(protocol, "item_event")
    request["arguments"]["item_event"]["current_summary"] = "A different but nonempty checkpoint."
    scored = score_raw_request(request, phase2="item_event", protocol=protocol)
    assert scored["raw_request_valid"] is True
    assert scored["projected_after_valid"] is False
    assert "projected-after-mismatch" in scored["score_codes"]


def test_raw_full_object_rejects_code_managed_fields(protocol: dict[str, object]) -> None:
    request = _request(protocol, "full_object")
    request["arguments"]["fact_object"]["updated_at"] = "2026-08-15T03:00:00Z"
    scored = score_raw_request(request, phase2="full_object", protocol=protocol)
    assert scored["raw_request_valid"] is False
    assert any("Code 托管字段" in code for code in scored["score_codes"])


def _events() -> list[dict[str, object]]:
    call_id = "call-bash-1"
    return [
        {
            "type": "request/header",
            "seq": 1,
            "data": {
                "reason": "trial",
                "header": {"config": {"provider": "fixed", "model": "gpt-5.6-sol"}},
            },
        },
        {"type": "turn/start", "data": {}},
        {"type": "step/start", "data": {}},
        {
            "type": "tool/call",
            "data": {
                "callId": call_id,
                "name": "bash",
                "arguments": json.dumps(
                    {
                        "command": "./ldvh capabilities update-workcase --example; "
                        "./ldvh call update-workcase --request /tmp/x --fields result.x <<'PY'"
                    }
                ),
            },
        },
        {
            "type": "tool/result",
            "data": {
                "message": {
                    "source": {"callId": call_id},
                    "content": [{"type": "text", "text": '{"outcome":"invalid_request"}'}],
                }
            },
        },
        {
            "type": "assistant/message",
            "data": {
                "usage": {"inputTokens": 10, "outputTokens": 5, "cacheReadTokens": 20},
                "message": {"content": "opaque"},
            },
        },
        {"type": "step/end", "data": {}},
        {"type": "turn/end", "data": {}},
    ]


def test_ephemeral_extractor_retains_only_aggregates() -> None:
    metrics = extract_session_metrics(_events(), session_id="sensitive-session-id")
    assert metrics["model"] == "gpt-5.6-sol"
    assert metrics["session_id_hash"] != "sensitive-session-id"
    assert metrics["bash_total"] == 1
    assert metrics["helper_direct_total"] == 2
    assert metrics["per_op"] == {"update-workcase": 2}
    assert metrics["python_heredoc_calls"] == 1
    assert metrics["invalid_request_hits"] == 1
    assert metrics["state_changing_helper_calls"] == 1
    assert metrics["new_flag_counts"] == {"--example": 1, "--fields": 1, "--request": 1}
    assert metrics["cache_amplification_proxy"] == 4.0
    assert "opaque" not in json.dumps(metrics)
    assert "sensitive-session-id" not in json.dumps(metrics)


def test_retained_record_schema_rejects_extra_and_missing_fields(protocol: dict[str, object]) -> None:
    record = {key: None for key in protocol["retained_trial_schema"]}
    assert retained_record_problems(record, protocol) == ()
    record["raw_request"] = {"secret": True}
    assert retained_record_problems(record, protocol) == (
        "extra-fields:raw_request",
        "denylist-field",
    )
    del record["trial_id"]
    assert "missing-fields:trial_id" in retained_record_problems(record, protocol)


def _balanced_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for replicate in range(1, 11):
        for phase1 in ("legacy_cli", "new_cli"):
            for phase2 in ("full_object", "item_event"):
                records.append(
                    {
                        "replicate_id": replicate,
                        "phase1": phase1,
                        "phase2": phase2,
                        "metric": (
                            replicate
                            + (10 if phase1 == "new_cli" else 0)
                            + (100 if phase2 == "item_event" else 0)
                            + (5 if phase1 == "new_cli" and phase2 == "item_event" else 0)
                        ),
                    }
                )
    return records


def test_paired_estimands_and_interaction_use_the_frozen_strata() -> None:
    records = _balanced_records()
    assert paired_differences(records, factor="phase1", metric="metric") == [10.0] * 10 + [15.0] * 10
    assert paired_differences(records, factor="phase2", metric="metric") == [100.0] * 10 + [105.0] * 10
    interaction = interaction_estimate(records, metric="metric")
    assert interaction["legacy_to_new_with_full_object"]["mean_difference"] == 10.0
    assert interaction["legacy_to_new_with_item_event"]["mean_difference"] == 15.0
    assert interaction["difference_in_differences"]["mean_difference"] == 5.0


def test_paired_estimate_uses_exact_sign_flips_and_deterministic_bootstrap() -> None:
    estimate = paired_estimate([-1.0, -1.0])
    assert estimate == {
        "pairs": 2,
        "mean_difference": -1.0,
        "median_difference": -1.0,
        "confidence_interval_95": [-1.0, -1.0],
        "two_sided_sign_flip_p": 0.5,
        "zero_differences": 0,
    }


def test_pairing_rejects_duplicate_or_missing_cells() -> None:
    records = _balanced_records()
    with pytest.raises(ValueError, match="duplicate paired record"):
        paired_differences(records + [deepcopy(records[0])], factor="phase1", metric="metric")
    with pytest.raises(ValueError, match="missing pair"):
        paired_differences(records[1:], factor="phase1", metric="metric")
