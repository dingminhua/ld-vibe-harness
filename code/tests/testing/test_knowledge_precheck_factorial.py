from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ldvh.testing.knowledge_precheck_factorial import (
    CALIBER,
    MAX_PAIR_ATTEMPTS,
    MAX_REPLACEMENTS,
    RETAINED_PAIR_TARGET,
    TECHNICAL_EXCLUSION_CODES,
    analyze_records,
    build_blind_scoring_packet,
    canonical_json,
    canonical_sha256,
    expand_assignments,
    paired_metric_differences,
    regenerate_results_artifact,
    render_report,
    render_trial_prompt,
    retained_record_problems,
    validate_protocol,
    validate_result_records,
)

ROOT = Path(__file__).parents[3]
PROTOCOL_PATH = ROOT / "docs/metrics/knowledge-precheck-protocol-v1.json"
RESULTS_PATH = ROOT / "docs/metrics/knowledge-precheck-results-v1.json"
REPORT_PATH = ROOT / "docs/metrics/knowledge-precheck-report-v1.md"

_RECORD_SCHEMA = [
    "agent",
    "answer_correct",
    "applicability_correct",
    "attempt_id",
    "cache_read_tokens",
    "candidate_expansion_count",
    "condition",
    "duplicate_avoidance_correct",
    "exclusion_code",
    "fact_read_count",
    "first_action_correct",
    "fresh_context_id_hash",
    "input_tokens",
    "material_chars",
    "model",
    "non_use_correct",
    "output_tokens",
    "packet_chars",
    "packet_hash",
    "pair_id",
    "prompt_chars",
    "prompt_hash",
    "queue_ms",
    "response",
    "response_chars",
    "selected_refs",
    "selection_correct",
    "sequence",
    "state_changing_helper_calls",
    "structured_valid",
    "task_hash",
    "wall_ms",
    "wrong_selection",
]
_DENYLIST = [
    "full_transcript",
    "hidden_reasoning",
    "raw_prompt",
    "secret",
    "session_id",
    "session_path",
    "tool_body",
]


def _tasks() -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    for family_index, family in enumerate(("adr-decision", "pitfall-debug", "study-research")):
        for member in range(1, 5):
            pair_id = f"{family_index + 1}-{member}"
            case_kind = ("positive", "negative-non-use", "ambiguity", "positive")[member - 1]
            tasks.append(
                {
                    "pair_id": pair_id,
                    "family": family,
                    "case_kind": case_kind,
                    "user_task": f"Read-only judgment task {pair_id}",
                    "applicable_refs": [f"uid-applicable-{pair_id}"],
                    "tempting_nonapplicable_refs": [f"uid-tempting-{pair_id}"],
                    "admissible_answer": f"Use the applicable source for {pair_id}.",
                    "wrong_selection_taxonomy": ["missed-applicable", "selected-nonapplicable"],
                    "duplicate_research_definition": "Starting new research despite a current applicable source.",
                    "first_legal_action": "Read the applicable source before proposing action.",
                    "blind_scoring_notes": ["Score source selection independently of condition."],
                    "control_materials": [
                        {
                            "slot": "candidate-1",
                            "title": "Candidate A",
                            "boundary": "Assess applicability before acting.",
                        }
                    ],
                    "treatment_materials": [
                        {
                            "object_uid": f"uid-applicable-{pair_id}",
                            "object_id": f"object-applicable-{pair_id}",
                            "title": f"Applicable source {pair_id}",
                            "boundary": "Use only when its stated applicability matches.",
                        }
                    ],
                }
            )
    return tasks


def _protocol() -> dict[str, object]:
    task_package = {"tasks": _tasks()}
    prompt_skeleton = {"required_output": "closed-structured-response", "same_for_both": True}
    control_packet = {"kind": "source-free-neutral-navigation", "fields": ["candidate", "boundary"]}
    treatment_packet = {"kind": "source-bound-f2-f3-precheck", "fields": ["candidate", "boundary"]}
    return {
        "caliber": CALIBER,
        "fixed_runner": {
            "model": "gpt-5.6-sol",
            "agent_runtime": "native-subagent",
            "retained_pair_target": RETAINED_PAIR_TARGET,
            "maximum_pair_attempts": MAX_PAIR_ATTEMPTS,
            "maximum_replacements": MAX_REPLACEMENTS,
            "outcome_dependent_stopping": False,
            "task_package_sha256": canonical_sha256(task_package),
            "prompt_skeleton_sha256": canonical_sha256(prompt_skeleton),
            "control_packet_sha256": canonical_sha256(control_packet),
            "treatment_packet_sha256": canonical_sha256(treatment_packet),
        },
        "assignment": {
            "condition_orders": [
                ["control", "treatment"] if index % 2 == 0 else ["treatment", "control"]
                for index in range(RETAINED_PAIR_TARGET)
            ]
        },
        "task_package": task_package,
        "prompt_skeleton": prompt_skeleton,
        "control_packet": control_packet,
        "treatment_packet": treatment_packet,
        "blind_scoring_rubric": {
            "metrics": [
                "applicability_correct",
                "selection_correct",
                "non_use_correct",
                "duplicate_avoidance_correct",
                "first_action_correct",
            ]
        },
        "retained_record_schema": _RECORD_SCHEMA,
        "artifact_denylist": _DENYLIST,
        "technical_exclusion_codes": sorted(TECHNICAL_EXCLUSION_CODES),
    }


def _record(pair_id: str, condition: str, sequence: int) -> dict[str, object]:
    return {
        "agent": "native-subagent",
        "answer_correct": 1,
        "applicability_correct": 1,
        "attempt_id": f"attempt-{canonical_sha256([pair_id, condition])[:16]}",
        "cache_read_tokens": "unavailable",
        "candidate_expansion_count": int(condition == "treatment"),
        "condition": condition,
        "duplicate_avoidance_correct": 1,
        "exclusion_code": None,
        "fact_read_count": int(condition == "treatment"),
        "first_action_correct": 1,
        "fresh_context_id_hash": canonical_sha256([pair_id, condition]),
        "input_tokens": "unavailable",
        "material_chars": 100,
        "model": "gpt-5.6-sol",
        "non_use_correct": 1,
        "output_tokens": "unavailable",
        "packet_chars": 50,
        "packet_hash": canonical_sha256([condition, "packet"]),
        "pair_id": pair_id,
        "prompt_chars": 200,
        "prompt_hash": canonical_sha256([pair_id, "prompt"]),
        "queue_ms": "unavailable",
        "response": {
            "decision": "use",
            "duplicate_research": False,
            "first_legal_action": "read-source",
            "rationale_codes": ["source-applicable"],
            "selected_refs": [f"uid-applicable-{pair_id}"],
        },
        "response_chars": 90,
        "selected_refs": [f"uid-applicable-{pair_id}"],
        "selection_correct": 1,
        "sequence": sequence,
        "state_changing_helper_calls": 0,
        "structured_valid": True,
        "task_hash": canonical_sha256(pair_id),
        "wall_ms": "unavailable",
        "wrong_selection": False,
    }


def _records(protocol: dict[str, object]) -> list[dict[str, object]]:
    tasks = {task["pair_id"]: task for task in protocol["task_package"]["tasks"]}
    records: list[dict[str, object]] = []
    for item in expand_assignments(protocol):
        pair_id = str(item["pair_id"])
        condition = str(item["condition"])
        record = _record(pair_id, condition, int(item["sequence"]))
        task = tasks[pair_id]
        materials = task[f"{condition}_materials"]
        prompt = render_trial_prompt(task, condition)
        record.update(
            {
                "agent": protocol["fixed_runner"]["agent_runtime"],
                "candidate_expansion_count": len(materials) if condition == "treatment" else 0,
                "material_chars": len(canonical_json(materials)),
                "model": protocol["fixed_runner"]["model"],
                "packet_chars": len(canonical_json(materials)),
                "packet_hash": canonical_sha256(materials),
                "prompt_chars": len(prompt),
                "prompt_hash": canonical_sha256(prompt),
                "response_chars": len(canonical_json(record["response"])),
                "task_hash": canonical_sha256(task),
            }
        )
        records.append(record)
    return records


def test_frozen_protocol_artifact_is_valid() -> None:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    assert validate_protocol(protocol) == ()
    assert protocol["frozen_before_retained_execution"] is True


def test_frozen_results_and_report_regenerate_byte_identically() -> None:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    result_text = RESULTS_PATH.read_text(encoding="utf-8")
    results = json.loads(result_text)
    assert validate_result_records(results["records"], results["excluded_attempts"], protocol) == ()
    assert results["records_sha256"] == canonical_sha256(results["records"])
    assert regenerate_results_artifact(results, protocol) == result_text
    assert render_report(results) == REPORT_PATH.read_text(encoding="utf-8")
    assert results["sample"]["state_changing_helper_calls"] == 0
    assert results["sample"]["host_received"] == "unavailable"


def test_protocol_is_frozen_balanced_and_privacy_closed() -> None:
    protocol = _protocol()
    assert validate_protocol(protocol) == ()
    assignments = expand_assignments(protocol)
    assert len(assignments) == 24
    assert sum(item["sequence"] == 1 and item["condition"] == "control" for item in assignments) == 6
    assert sum(item["sequence"] == 1 and item["condition"] == "treatment" for item in assignments) == 6


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        (lambda value: value["fixed_runner"].update(maximum_pair_attempts=16), "maximum-pair-attempts"),
        (
            lambda value: value["assignment"]["condition_orders"].append(["control", "treatment"]),
            "condition-order-count",
        ),
        (lambda value: value["task_package"]["tasks"].pop(), "task-count"),
    ],
)
def test_protocol_rejects_drift(mutation: object, problem: str) -> None:
    protocol = _protocol()
    mutation(protocol)
    assert problem in validate_protocol(protocol)


def test_record_allowlist_rejects_nested_denied_and_extra_fields() -> None:
    protocol = _protocol()
    record = _record("1-1", "control", 1)
    assert retained_record_problems(record, protocol) == ()
    record["unexpected"] = True
    record["response"]["hidden_reasoning"] = "sensitive"
    assert retained_record_problems(record, protocol) == (
        "extra-fields:unexpected",
        "denylist-fields:hidden_reasoning",
    )


def test_prompt_renderer_preserves_pair_structure_and_source_boundary() -> None:
    task = _tasks()[0]
    control = render_trial_prompt(task, "control")
    treatment = render_trial_prompt(task, "treatment")
    assert task["user_task"] in control and task["user_task"] in treatment
    assert "uid-applicable-1-1" not in control
    assert "uid-applicable-1-1" in treatment
    expected_suffix = (
        '"first_legal_action":"short-action-code","duplicate_research":true|false,'
        '"rationale_codes":["short-code"]}'
    )
    assert control.endswith(expected_suffix)
    with pytest.raises(ValueError, match="unknown condition"):
        render_trial_prompt(task, "unknown")


def test_blind_packet_strips_condition_order_and_provenance() -> None:
    protocol = _protocol()
    record = _record("1-1", "treatment", 2)
    task = protocol["task_package"]["tasks"][0]
    packet = build_blind_scoring_packet(record, task, protocol)
    assert set(packet) == {"attempt_id", "pair_id", "family", "case_kind", "response", "gold", "rubric"}
    encoded = str(packet)
    assert "treatment" not in encoded
    assert "sequence" not in encoded
    assert "fresh_context_id_hash" not in encoded


def test_result_validation_enforces_balance_and_technical_replacements() -> None:
    protocol = _protocol()
    records = _records(protocol)
    assert validate_result_records(records, [], protocol) == ()
    drifted = deepcopy(records)
    drifted[0]["prompt_hash"] = "0" * 64
    drifted[1]["fresh_context_id_hash"] = drifted[0]["fresh_context_id_hash"]
    drift_problems = validate_result_records(drifted, [], protocol)
    assert any(problem.endswith(":prompt_hash") for problem in drift_problems)
    assert "fresh-context-hash-uniqueness" in drift_problems
    missing = records[:-1]
    assert "retained-record-count" in validate_result_records(missing, [], protocol)
    excluded = [{"exclusion_code": "wrong-answer"}]
    assert "nontechnical-exclusion" in validate_result_records(records, excluded, protocol)
    too_many = [{"exclusion_code": "runner_failure"}] * 4
    assert "replacement-ceiling" in validate_result_records(records, too_many, protocol)
    assert "pair-attempt-ceiling" in validate_result_records(records, too_many, protocol)


def test_paired_metrics_and_analysis_are_deterministic() -> None:
    protocol = _protocol()
    records = _records(protocol)
    for record in records:
        record["response_chars"] = 100 if record["condition"] == "treatment" else 90
    differences = paired_metric_differences(records, "response_chars")
    assert differences == [10.0] * 12
    analysis = analyze_records(records, ["response_chars", "answer_correct"])
    assert analysis["response_chars"]["mean_difference"] == 10.0
    assert analysis["answer_correct"]["mean_difference"] == 0.0


def test_duplicate_pair_and_missing_condition_fail_closed() -> None:
    protocol = _protocol()
    records = _records(protocol)
    duplicate = deepcopy(records[0])
    records.append(duplicate)
    with pytest.raises(ValueError, match="duplicate record"):
        paired_metric_differences(records, "answer_correct")
    with pytest.raises(ValueError, match="missing condition"):
        paired_metric_differences(_records(protocol)[:-1], "answer_correct")
