"""Deterministic protocol and analysis helpers for the WC-D knowledge-precheck trial.

The trial estimates the combined effect of one source-bound F2→F3 knowledge
precheck package.  This module never launches agents or calls Helper operations;
it validates the frozen package, enforces the retained-record privacy boundary,
constructs condition-blind scoring packets, and derives paired summaries.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from ldvh.testing.helper_interaction_factorial import paired_estimate

CALIBER = "wc-d-knowledge-precheck/1"
CONDITIONS = ("control", "treatment")
TASK_FAMILIES = ("adr-decision", "pitfall-debug", "study-research")
CASE_KINDS = frozenset({"positive", "negative-non-use", "ambiguity"})
TECHNICAL_EXCLUSION_CODES = frozenset(
    {
        "missing_structured_output",
        "model_technical_failure",
        "runner_failure",
        "cross_condition_leakage",
    }
)
RETAINED_PAIR_TARGET = 12
MAX_PAIR_ATTEMPTS = 15
MAX_REPLACEMENTS = 3
ANALYSIS_METRICS = (
    "answer_correct",
    "applicability_correct",
    "selection_correct",
    "non_use_correct",
    "duplicate_avoidance_correct",
    "first_action_correct",
    "fact_read_count",
    "candidate_expansion_count",
    "prompt_chars",
    "packet_chars",
    "material_chars",
    "response_chars",
)
_REQUIRED_TASK_FIELDS = frozenset(
    {
        "pair_id",
        "family",
        "case_kind",
        "user_task",
        "applicable_refs",
        "tempting_nonapplicable_refs",
        "admissible_answer",
        "wrong_selection_taxonomy",
        "duplicate_research_definition",
        "first_legal_action",
        "blind_scoring_notes",
        "control_materials",
        "treatment_materials",
    }
)
_BLIND_VISIBLE_FIELDS = (
    "attempt_id",
    "pair_id",
    "family",
    "case_kind",
    "response",
    "gold",
    "rubric",
)


def canonical_json(value: object) -> str:
    """Return the trial's canonical compact JSON encoding."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: object) -> str:
    """Hash one JSON-compatible value under :func:`canonical_json`."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def expand_assignments(protocol: Mapping[str, Any]) -> list[dict[str, object]]:
    """Expand the frozen twelve-pair, six-by-six counterbalanced assignment."""

    tasks = protocol.get("task_package", {}).get("tasks", [])
    orders = protocol.get("assignment", {}).get("condition_orders", [])
    if not isinstance(tasks, list) or not isinstance(orders, list):
        return []
    expanded: list[dict[str, object]] = []
    for task, order in zip(tasks, orders, strict=False):
        if not isinstance(task, Mapping) or not isinstance(order, list):
            continue
        pair_id = task.get("pair_id")
        for sequence, condition in enumerate(order, start=1):
            expanded.append(
                {
                    "pair_id": pair_id,
                    "family": task.get("family"),
                    "case_kind": task.get("case_kind"),
                    "condition": condition,
                    "sequence": sequence,
                }
            )
    return expanded


def _all_keys(value: object) -> set[str]:
    if isinstance(value, Mapping):
        return set(value) | {key for member in value.values() for key in _all_keys(member)}
    if isinstance(value, list):
        return {key for member in value for key in _all_keys(member)}
    return set()


def _nonempty_strings(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(member, str) and bool(member.strip()) for member in value
    )


def validate_protocol(protocol: Mapping[str, Any]) -> tuple[str, ...]:
    """Return deterministic frozen-protocol problems; empty means valid."""

    problems: list[str] = []
    if protocol.get("caliber") != CALIBER:
        problems.append("caliber")
    runner = protocol.get("fixed_runner", {})
    if not isinstance(runner, Mapping):
        return ("fixed-runner",)
    if runner.get("model") != "gpt-5.6-sol":
        problems.append("fixed-model")
    if runner.get("retained_pair_target") != RETAINED_PAIR_TARGET:
        problems.append("retained-pair-target")
    if runner.get("maximum_pair_attempts") != MAX_PAIR_ATTEMPTS:
        problems.append("maximum-pair-attempts")
    if runner.get("maximum_replacements") != MAX_REPLACEMENTS:
        problems.append("maximum-replacements")
    if runner.get("outcome_dependent_stopping") is not False:
        problems.append("outcome-dependent-stopping")

    task_package = protocol.get("task_package", {})
    tasks = task_package.get("tasks", []) if isinstance(task_package, Mapping) else []
    if not isinstance(tasks, list) or len(tasks) != RETAINED_PAIR_TARGET:
        problems.append("task-count")
        tasks = []
    pair_ids: list[object] = []
    family_counts: Counter[object] = Counter()
    case_kinds: set[object] = set()
    for task in tasks:
        if not isinstance(task, Mapping):
            problems.append("task-not-object")
            continue
        if set(task) != _REQUIRED_TASK_FIELDS:
            problems.append(f"task-fields:{task.get('pair_id')}")
        pair_ids.append(task.get("pair_id"))
        family_counts[task.get("family")] += 1
        case_kinds.add(task.get("case_kind"))
        for field in (
            "applicable_refs",
            "tempting_nonapplicable_refs",
            "wrong_selection_taxonomy",
            "blind_scoring_notes",
        ):
            if not _nonempty_strings(task.get(field)):
                problems.append(f"task-{field}:{task.get('pair_id')}")
        for field in ("control_materials", "treatment_materials"):
            materials = task.get(field)
            if not isinstance(materials, list) or not materials or not all(
                isinstance(member, Mapping) for member in materials
            ):
                problems.append(f"task-{field}:{task.get('pair_id')}")
        for field in (
            "pair_id",
            "family",
            "case_kind",
            "user_task",
            "admissible_answer",
            "duplicate_research_definition",
            "first_legal_action",
        ):
            if not isinstance(task.get(field), str) or not str(task.get(field)).strip():
                problems.append(f"task-{field}:{task.get('pair_id')}")
    if len(pair_ids) != len(set(pair_ids)):
        problems.append("pair-id-uniqueness")
    if family_counts != Counter({family: 4 for family in TASK_FAMILIES}):
        problems.append("family-balance")
    if not CASE_KINDS.issubset(case_kinds):
        problems.append("case-kind-coverage")

    orders = protocol.get("assignment", {}).get("condition_orders", [])
    if not isinstance(orders, list) or len(orders) != RETAINED_PAIR_TARGET:
        problems.append("condition-order-count")
        orders = []
    valid_orders = [["control", "treatment"], ["treatment", "control"]]
    if any(order not in valid_orders for order in orders):
        problems.append("condition-order-members")
    if Counter(tuple(order) for order in orders) != Counter(
        {("control", "treatment"): 6, ("treatment", "control"): 6}
    ):
        problems.append("condition-order-balance")
    if len(expand_assignments(protocol)) != RETAINED_PAIR_TARGET * 2:
        problems.append("assignment-count")

    if runner.get("task_package_sha256") != canonical_sha256(task_package):
        problems.append("task-package-hash")
    for name in ("prompt_skeleton_sha256", "control_packet_sha256", "treatment_packet_sha256"):
        material_key = name.removesuffix("_sha256")
        if runner.get(name) != canonical_sha256(protocol.get(material_key)):
            problems.append(name)

    record_schema = protocol.get("retained_record_schema", [])
    denylist = protocol.get("artifact_denylist", [])
    if not _nonempty_strings(record_schema) or len(record_schema) != len(set(record_schema)):
        problems.append("retained-record-schema")
    if not _nonempty_strings(denylist) or len(denylist) != len(set(denylist)):
        problems.append("artifact-denylist")
    if set(record_schema) & set(denylist):
        problems.append("schema-denylist-overlap")
    if set(protocol.get("technical_exclusion_codes", [])) != TECHNICAL_EXCLUSION_CODES:
        problems.append("technical-exclusion-codes")
    return tuple(problems)


def render_trial_prompt(task: Mapping[str, Any], condition: str) -> str:
    """Reconstruct the exact prompt form used for one retained attempt."""

    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    materials = task[f"{condition}_materials"]
    lines = [
        "Complete one fresh, read-only judgment. Do not use tools, files, network, or prior context. "
        f"Task: {task['user_task']}",
        "Packet:",
    ]
    if condition == "control":
        lines.extend(
            f"- {material['slot']} / {material['title']} / {material['boundary']}"
            for material in materials
        )
    else:
        lines.extend(
            "- "
            f"{material['object_uid']} / {material['object_id']} / {material['title']} / "
            f"{material['boundary']}"
            for material in materials
        )
    if task["family"] == "adr-decision":
        lines.append("Judge applicability before selection. Non-use is valid.")
    lines.append(
        "Return exactly one JSON object, no prose: "
        '{"decision":"use|non-use|ambiguous","selected_refs":["zero or more supplied refs"],'
        '"first_legal_action":"short-action-code","duplicate_research":true|false,'
        '"rationale_codes":["short-code"]}'
    )
    return "\n".join(lines)


def retained_record_problems(
    record: Mapping[str, object], protocol: Mapping[str, Any]
) -> tuple[str, ...]:
    """Reject retained attempt content outside the frozen allowlist."""

    allowed = set(protocol["retained_record_schema"])
    denylist = set(protocol["artifact_denylist"])
    problems: list[str] = []
    extras = sorted(set(record) - allowed)
    missing = sorted(allowed - set(record))
    if extras:
        problems.append(f"extra-fields:{','.join(extras)}")
    if missing:
        problems.append(f"missing-fields:{','.join(missing)}")
    denied = sorted(_all_keys(record) & denylist)
    if denied:
        problems.append(f"denylist-fields:{','.join(denied)}")
    return tuple(problems)


def build_blind_scoring_packet(
    record: Mapping[str, object], task: Mapping[str, object], protocol: Mapping[str, Any]
) -> dict[str, object]:
    """Build the condition-blind scorer packet from one allowlisted record."""

    if retained_record_problems(record, protocol):
        raise ValueError("record does not satisfy the frozen allowlist")
    if record.get("pair_id") != task.get("pair_id"):
        raise ValueError("record/task pair mismatch")
    packet = {
        "attempt_id": record["attempt_id"],
        "pair_id": task["pair_id"],
        "family": task["family"],
        "case_kind": task["case_kind"],
        "response": record["response"],
        "gold": {
            "applicable_refs": task["applicable_refs"],
            "tempting_nonapplicable_refs": task["tempting_nonapplicable_refs"],
            "admissible_answer": task["admissible_answer"],
            "duplicate_research_definition": task["duplicate_research_definition"],
            "first_legal_action": task["first_legal_action"],
        },
        "rubric": protocol["blind_scoring_rubric"],
    }
    if tuple(packet) != _BLIND_VISIBLE_FIELDS:
        raise AssertionError("blind scorer packet shape drifted")
    return packet


def validate_result_records(
    records: Sequence[Mapping[str, object]],
    excluded_attempts: Sequence[Mapping[str, object]],
    protocol: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate retained balance, source bindings, ceilings, and privacy."""

    problems: list[str] = []
    if len(records) != RETAINED_PAIR_TARGET * 2:
        problems.append("retained-record-count")
    tasks = {
        task["pair_id"]: task
        for task in protocol["task_package"]["tasks"]
        if isinstance(task, Mapping)
    }
    assignments = {
        (item["pair_id"], item["condition"]): item for item in expand_assignments(protocol)
    }
    unavailable_fields = (
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "wall_ms",
        "queue_ms",
    )
    context_hashes: list[object] = []
    for record in records:
        problems.extend(retained_record_problems(record, protocol))
        pair_id = record.get("pair_id")
        condition = record.get("condition")
        task = tasks.get(pair_id)
        assignment = assignments.get((pair_id, condition))
        if task is None or assignment is None:
            continue
        prefix = f"record:{record.get('attempt_id')}"
        prompt = render_trial_prompt(task, str(condition))
        materials = task[f"{condition}_materials"]
        expected_values = {
            "task_hash": canonical_sha256(task),
            "prompt_hash": canonical_sha256(prompt),
            "prompt_chars": len(prompt),
            "packet_hash": canonical_sha256(materials),
            "packet_chars": len(canonical_json(materials)),
            "material_chars": len(canonical_json(materials)),
            "sequence": assignment["sequence"],
            "model": protocol["fixed_runner"]["model"],
            "agent": protocol["fixed_runner"]["agent_runtime"],
            "structured_valid": True,
            "state_changing_helper_calls": 0,
            "exclusion_code": None,
            "candidate_expansion_count": len(materials) if condition == "treatment" else 0,
        }
        for field, expected_value in expected_values.items():
            if record.get(field) != expected_value:
                problems.append(f"{prefix}:{field}")
        response = record.get("response")
        if not isinstance(response, Mapping):
            problems.append(f"{prefix}:response")
        else:
            if record.get("selected_refs") != response.get("selected_refs"):
                problems.append(f"{prefix}:selected-refs")
            if record.get("response_chars") != len(canonical_json(response)):
                problems.append(f"{prefix}:response-chars")
        if any(record.get(field) != "unavailable" for field in unavailable_fields):
            problems.append(f"{prefix}:unavailable-fields")
        context_hash = record.get("fresh_context_id_hash")
        context_hashes.append(context_hash)
        if not isinstance(context_hash, str) or re.fullmatch(r"[0-9a-f]{64}", context_hash) is None:
            problems.append(f"{prefix}:fresh-context-hash-shape")
    by_pair: Counter[tuple[object, object]] = Counter(
        (record.get("pair_id"), record.get("condition")) for record in records
    )
    expected = Counter(assignments.keys())
    if by_pair != expected:
        problems.append("retained-pair-balance")
    if len({record.get("attempt_id") for record in records}) != len(records):
        problems.append("retained-attempt-id-uniqueness")
    if len(set(context_hashes)) != len(context_hashes):
        problems.append("fresh-context-hash-uniqueness")
    if len(excluded_attempts) > MAX_REPLACEMENTS:
        problems.append("replacement-ceiling")
    for excluded in excluded_attempts:
        if excluded.get("exclusion_code") not in TECHNICAL_EXCLUSION_CODES:
            problems.append("nontechnical-exclusion")
    total_pair_attempts = RETAINED_PAIR_TARGET + len(excluded_attempts)
    if total_pair_attempts > MAX_PAIR_ATTEMPTS:
        problems.append("pair-attempt-ceiling")
    return tuple(sorted(set(problems)))


def paired_metric_differences(
    records: Sequence[Mapping[str, object]], metric: str
) -> list[float]:
    """Return treatment-minus-control differences in frozen pair order."""

    indexed: dict[tuple[object, object], Mapping[str, object]] = {}
    for record in records:
        key = (record["pair_id"], record["condition"])
        if key in indexed:
            raise ValueError(f"duplicate record: {key}")
        indexed[key] = record
    differences: list[float] = []
    for pair_id in sorted({record["pair_id"] for record in records}):
        control = indexed.get((pair_id, "control"))
        treatment = indexed.get((pair_id, "treatment"))
        if control is None or treatment is None:
            raise ValueError(f"missing condition for pair: {pair_id}")
        differences.append(float(treatment[metric]) - float(control[metric]))
    return differences


def analyze_records(
    records: Sequence[Mapping[str, object]], metrics: Sequence[str]
) -> dict[str, object]:
    """Return deterministic paired estimates for the preregistered metrics."""

    return {
        metric: paired_estimate(paired_metric_differences(records, metric))
        for metric in metrics
    }


def regenerate_results_artifact(
    result: Mapping[str, Any], protocol: Mapping[str, Any]
) -> str:
    """Replay derived fields in an existing result; this is not source-complete reconstruction."""

    regenerated = deepcopy(dict(result))
    records = regenerated["records"]
    regenerated["caliber"] = protocol["caliber"]
    regenerated["protocol_sha256"] = canonical_sha256(protocol)
    regenerated["task_package_sha256"] = protocol["fixed_runner"]["task_package_sha256"]
    regenerated["records_sha256"] = canonical_sha256(records)
    regenerated["paired_analysis"] = analyze_records(records, ANALYSIS_METRICS)
    regenerated["evidence_boundary"] = deepcopy(protocol["evidence_vocabulary"])
    return json.dumps(regenerated, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_report(result: Mapping[str, Any]) -> str:
    """Render the deterministic human-readable WC-D evidence report."""

    analysis = result["paired_analysis"]
    sample = result["sample"]
    quality_metrics = (
        "answer_correct",
        "applicability_correct",
        "selection_correct",
        "non_use_correct",
        "duplicate_avoidance_correct",
        "first_action_correct",
    )
    cost_metrics = (
        "fact_read_count",
        "candidate_expansion_count",
        "prompt_chars",
        "packet_chars",
        "material_chars",
        "response_chars",
    )

    def row(metric: str) -> str:
        value = analysis[metric]
        low, high = value["confidence_interval_95"]
        return (
            f"| `{metric}` | {value['mean_difference']:.6f} | "
            f"[{low:.6f}, {high:.6f}] | {value['two_sided_sign_flip_p']:.6f} |"
        )

    lines = [
        "# WC-D knowledge-precheck paired experiment",
        "",
        "## Frozen sample",
        "",
        f"- Retained pairs: **{sample['retained_pairs']}**; member calls: **{sample['member_calls']}**.",
        f"- Technical pair replacements: **{sample['technical_replacements']}**.",
        f"- Control-first / treatment-first: **{sample['order_control_first']} / {sample['order_treatment_first']}**.",
        f"- State-changing Helper calls: **{sample['state_changing_helper_calls']}**.",
        f"- Host receipt: **{sample['host_received']}**.",
        "",
        "## Paired knowledge-quality estimates",
        "",
        "Treatment minus control; positive favors the source-bound precheck package.",
        "",
        "| Metric | Mean difference | Bootstrap 95% CI | Exact sign-flip p |",
        "|---|---:|---:|---:|",
        *(row(metric) for metric in quality_metrics),
        "",
        "`selection_correct` was nominally higher for the combined source-identity-plus-content package in this ",
        "selected frozen corpus (mean +0.666667; exact sign-flip p=0.0078125). Source identity availability, ",
        "source content, and precheck instruction are inseparable in this contrast. Six quality metrics were ",
        "examined and no multiple-comparison adjustment was applied. The overall answer, applicability, ",
        "non-use, duplicate-avoidance, and first-action estimates remain compatible with null or mixed task ",
        "effects at this sample size.",
        "",
        "## Added observable cost",
        "",
        "| Metric | Mean difference | Bootstrap 95% CI | Exact sign-flip p |",
        "|---|---:|---:|---:|",
        *(row(metric) for metric in cost_metrics),
        "",
        "Input/output/cache usage and wall/queue latency were not exposed by the retained native-subagent ",
        "boundary and are recorded as `unavailable`, not zero. `fact_read_count=0` means trial agents made no ",
        "fact calls; treatment received two LDVH-prepared F3 material cards per task. Candidate expansion and ",
        "character counts are behavior/cost measures, not proof of knowledge value.",
        "",
        "## Blind scoring and limitations",
        "",
        "- One full scorer failed before returning any score. Three disjoint family scorers supplied the first ",
        "  perspective; a separate scorer supplied the preregistered second perspective for ambiguity cases.",
        "- Seven disputed metric fields were resolved only against the frozen gold and are retained in the ",
        "  structured adjudication ledger; no condition or pair counterpart was disclosed to scorers.",
        "- The derived-field replay test recomputes hashes, analysis, and report from the existing result plus ",
        "  protocol. It is not a source-complete records-only reconstruction of scorer provenance, so the ",
        "  original reproducibility criterion is not satisfied.",
        "- The control packet was source-free but structurally matched, so this estimates the combined ",
        "  source-bound package, not separate F2, F3, instruction, or card effects.",
        "- The corpus is twelve selected LDVH tasks and is not a random sample of all project work.",
        "",
        "## Evidence boundary and residual decision",
        "",
        "The protocol and cards are **ldvh-prepared** and were **harness-delivered**. Provider/host receipt is ",
        "**unavailable**. The nominal selection score was higher under a package that uniquely exposed source ",
        "identities and content; this is not by itself demonstrated knowledge or reuse improvement. Other ",
        "quality effects are null or mixed and the package adds material/context cost. ",
        "This report does not claim broad causal benefit, does not close the service-quality Spark, does not ",
        "establish HV4 generally, and provides no Phase3/MCP or product-change authorization.",
        "",
        f"Records SHA-256: `{result['records_sha256']}`.",
    ]
    return "\n".join(lines) + "\n"


__all__ = [
    "ANALYSIS_METRICS",
    "CALIBER",
    "CASE_KINDS",
    "CONDITIONS",
    "MAX_PAIR_ATTEMPTS",
    "MAX_REPLACEMENTS",
    "RETAINED_PAIR_TARGET",
    "TASK_FAMILIES",
    "TECHNICAL_EXCLUSION_CODES",
    "analyze_records",
    "build_blind_scoring_packet",
    "canonical_json",
    "canonical_sha256",
    "expand_assignments",
    "paired_metric_differences",
    "regenerate_results_artifact",
    "render_report",
    "render_trial_prompt",
    "retained_record_problems",
    "validate_protocol",
    "validate_result_records",
]
