"""Deterministic scoring and aggregation for the WC-C Helper interaction trial.

The module deliberately separates three inputs:

* a frozen task/protocol package;
* one agent's unmodified synthetic ``update-workcase`` request; and
* ephemeral DSH events used to derive an allowlisted structural record.

It never executes the synthetic update request and never serializes raw prompts,
commands, tool-result bodies, or request bodies into retained records.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
import re
import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from ldvh.facts.transitions import validate_workcase_transition
from ldvh.facts.workcase_item_event import WorkCaseItemEvent, project_workcase_item_event
from ldvh.facts.workcase_validation import validate_workcase_snapshot
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.workcase_update_request import parse_update_workcase_request
from ldvh.helper.requests import parse_common_request
from ldvh.testing.session_comparability import audit_events, judge_comparability

CALIBER = "wc-c-helper-factorial/1"
CELL_KEYS = ("legacy-full", "new-event", "new-full", "legacy-event")
MANAGED_FIELDS = frozenset({"object_uid", "object_id", "fact_type_key", "created_at", "updated_at"})
STATE_CHANGING_OPERATIONS = frozenset(
    {
        "create-fact-object",
        "update-workcase",
        "close-workcase",
        "begin-workcase-termination",
        "complete-workcase-termination",
        "correct-closed-workcase",
    }
)
_EVENT_COUNT_ALLOWLIST = frozenset(
    {
        "request/header",
        "turn/start",
        "turn/end",
        "step/start",
        "step/end",
        "tool/call",
        "tool/result",
        "assistant/message",
    }
)
_HELPER_PATTERN = re.compile(r"(?:^|[;&|]\s*)(?:\./)?ldvh\s+(call|capabilities|check)(?:\s+([a-z0-9-]+))?")
_HEREDOC_PATTERN = re.compile(r"(?:python(?:3)?\s+-\s+<<|<<-?\s*['\"]?(?:PY|PYEOF|EOF))")


def canonical_json(value: object) -> str:
    """Return the trial's canonical compact JSON encoding."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: object) -> str:
    """Hash one JSON-compatible value under :func:`canonical_json`."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def expand_assignments(protocol: Mapping[str, Any]) -> list[dict[str, object]]:
    """Expand the frozen Latin-square declaration into forty primary trials."""

    assignment = protocol["assignment"]
    rows = assignment["cell_order_rows"]
    replicates = assignment["replicates"]
    expanded: list[dict[str, object]] = []
    ordinal = 0
    for replicate_id in range(1, replicates + 1):
        row = rows[(replicate_id - 1) % len(rows)]
        for cell_key in row:
            ordinal += 1
            expanded.append(
                {
                    "trial_id": f"primary-r{replicate_id:02d}-{cell_key}",
                    "attempt_ordinal": ordinal,
                    "replicate_id": replicate_id,
                    "cell_key": cell_key,
                    "phase1": protocol["cells"][cell_key]["phase1"],
                    "phase2": protocol["cells"][cell_key]["phase2"],
                }
            )
    return expanded


def build_gold_after(protocol: Mapping[str, Any]) -> dict[str, object]:
    """Project the frozen event into the one complete expected after object."""

    task = protocol["task_package"]["synthetic_update_task"]
    event = WorkCaseItemEvent(
        event_key="update-work-item-checkpoint",
        item_id=task["target_item_id"],
        current_summary=task["new_current_summary"],
        resume_from=task["new_resume_from"],
        change_summary=task["change_summary"],
    )
    return project_workcase_item_event(task["current_snapshot"], event, task["event_at"])


def _full_with_managed(current: Mapping[str, object], supplied: Mapping[str, object]) -> dict[str, object]:
    candidate = {key: deepcopy(value) for key, value in current.items() if key in MANAGED_FIELDS}
    candidate.update(deepcopy(dict(supplied)))
    return candidate


def validate_protocol(protocol: Mapping[str, Any]) -> tuple[str, ...]:
    """Return closed, deterministic protocol problems; empty means valid."""

    problems: list[str] = []
    if protocol.get("caliber") != CALIBER:
        problems.append("caliber")
    assignments = expand_assignments(protocol)
    if len(assignments) != 40:
        problems.append("assignment-count")
    counts = Counter(record["cell_key"] for record in assignments)
    if counts != Counter({key: 10 for key in protocol.get("cells", {})}):
        problems.append("cell-balance")
    if len({record["trial_id"] for record in assignments}) != len(assignments):
        problems.append("trial-id-uniqueness")
    stopping = protocol.get("stopping_rule", {})
    if stopping.get("valid_target") != 40 or stopping.get("maximum_attempts") != 48:
        problems.append("stopping-rule")
    if stopping.get("outcome_dependent_stopping") is not False:
        problems.append("outcome-dependent-stopping")
    task_hash = canonical_sha256(protocol.get("task_package"))
    if protocol.get("fixed_runner", {}).get("task_package_sha256") != task_hash:
        problems.append("task-package-hash")
    retained = protocol.get("retained_trial_schema", [])
    if len(retained) != len(set(retained)):
        problems.append("retained-schema-duplicates")
    if set(retained) & set(protocol.get("artifact_denylist", [])):
        problems.append("retained-denylist-overlap")

    current = protocol["task_package"]["synthetic_update_task"]["current_snapshot"]
    if validate_workcase_snapshot(current):
        problems.append("synthetic-current-invalid")
    gold = build_gold_after(protocol)
    full_after = _full_with_managed(current, gold)
    if validate_workcase_snapshot(full_after):
        problems.append("synthetic-gold-invalid")
    if validate_workcase_transition(dict(current), full_after):
        problems.append("synthetic-transition-invalid")
    return tuple(problems)


def _signature_is_exact(raw_request: Mapping[str, object], protocol: Mapping[str, Any]) -> bool:
    observed = raw_request.get("observed_context")
    if not isinstance(observed, Mapping) or set(observed) != {"signature"}:
        return False
    signature = observed.get("signature")
    expected = protocol["task_package"]["synthetic_update_task"]["observed_signature"]
    return isinstance(signature, Mapping) and dict(signature) == expected


def score_raw_request(
    raw_request: object,
    *,
    phase2: str,
    protocol: Mapping[str, Any],
) -> dict[str, object]:
    """Score one original synthetic request without repair or normalization."""

    payload_bytes = len(canonical_json(raw_request).encode("utf-8"))
    payload_hash = canonical_sha256(raw_request)
    codes: list[str] = []
    request_valid = False
    projected_valid = False

    if not isinstance(raw_request, Mapping):
        codes.append("top-level-not-object")
        return {
            "raw_request_sha256": payload_hash,
            "raw_request_bytes": payload_bytes,
            "raw_request_valid": False,
            "projected_after_valid": False,
            "score_codes": codes,
        }

    if not _signature_is_exact(raw_request, protocol):
        codes.append("signature-mismatch")
    common = parse_common_request(canonical_json(raw_request), general_discovery=False)
    if common.problems or common.request is None:
        codes.extend(f"common:{problem}" for problem in common.problems)
    else:
        context = OperationExecutionContext(cwd=Path(protocol["fixed_runner"]["workspace"]))
        parsed = parse_update_workcase_request(common.request, context)
        if parsed.problems or parsed.request is None:
            codes.extend(f"update:{problem}" for problem in parsed.problems)
        else:
            request = parsed.request
            expected = protocol["task_package"]["synthetic_update_task"]
            expected_ref = expected["fact_ref"]["object_uid"]
            actual_ref = getattr(request.fact_ref, "object_uid", None)
            if actual_ref != expected_ref:
                codes.append("fact-ref-mismatch")
            if request.expected_content_fingerprint != expected["expected_content_fingerprint"]:
                codes.append("cas-mismatch")
            if common.request.authorization_reference:
                codes.append("unexpected-authorization-reference")
            if "workspace_root" in common.request.arguments:
                codes.append("unexpected-workspace-root")
            event = request.item_event
            if phase2 == "item_event" and event is None:
                codes.append("wrong-alternative-full-object")
            elif phase2 == "full_object" and event is not None:
                codes.append("wrong-alternative-item-event")
            if phase2 not in {"full_object", "item_event"}:
                codes.append("unknown-phase2-condition")
            request_valid = not codes
            if request_valid:
                if event is not None:
                    candidate = project_workcase_item_event(
                        expected["current_snapshot"], event, expected["event_at"]
                    )
                else:
                    candidate = request.fact_object
                gold = build_gold_after(protocol)
                if candidate != gold:
                    codes.append("projected-after-mismatch")
                else:
                    full_after = _full_with_managed(expected["current_snapshot"], candidate)
                    snapshot_issues = validate_workcase_snapshot(full_after)
                    transition_issues = validate_workcase_transition(
                        dict(expected["current_snapshot"]), full_after
                    )
                    if snapshot_issues:
                        codes.append("projected-after-snapshot-invalid")
                    if transition_issues:
                        codes.append("projected-after-transition-invalid")
                    projected_valid = not snapshot_issues and not transition_issues
    if not codes:
        codes.append("valid")
    return {
        "raw_request_sha256": payload_hash,
        "raw_request_bytes": payload_bytes,
        "raw_request_valid": request_valid,
        "projected_after_valid": projected_valid,
        "score_codes": codes,
    }


def _invalid_request_count(value: object) -> int:
    """Count explicit outcome markers while retaining no source content."""

    if isinstance(value, Mapping):
        direct = int(value.get("outcome") == "invalid_request")
        return direct + sum(_invalid_request_count(member) for member in value.values())
    if isinstance(value, list):
        return sum(_invalid_request_count(member) for member in value)
    if isinstance(value, str) and "invalid_request" in value:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return len(re.findall(r'"outcome"\s*:\s*"invalid_request"', value))
        return _invalid_request_count(parsed)
    return 0


def extract_session_metrics(
    events: Sequence[Mapping[str, Any]],
    *,
    session_id: str,
) -> dict[str, object]:
    """Derive allowlisted metrics without retaining content-bearing values."""

    event_counts = Counter(
        event_type
        for event in events
        if isinstance((event_type := event.get("type")), str) and event_type in _EVENT_COUNT_ALLOWLIST
    )
    bash_call_ids: set[str] = set()
    bash_total = 0
    helper_total = 0
    helper_chars = 0
    all_bash_chars = 0
    heredoc = 0
    per_op: Counter[str] = Counter()
    new_flags: Counter[str] = Counter()
    state_changing = 0

    for event in events:
        if event.get("type") != "tool/call":
            continue
        data = event.get("data")
        if not isinstance(data, Mapping) or data.get("name") != "bash":
            continue
        call_id = data.get("callId")
        if isinstance(call_id, str):
            bash_call_ids.add(call_id)
        raw_arguments = data.get("arguments")
        try:
            arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        except json.JSONDecodeError:
            arguments = {}
        command = arguments.get("command", "") if isinstance(arguments, Mapping) else ""
        if not isinstance(command, str):
            command = ""
        bash_total += 1
        all_bash_chars += len(command)
        heredoc += len(_HEREDOC_PATTERN.findall(command))
        for flag in ("--request", "--example", "--fields"):
            new_flags[flag] += command.count(flag)
        helper_matches = list(_HELPER_PATTERN.finditer(command))
        if helper_matches:
            helper_chars += len(command)
        for match in helper_matches:
            kind, operation = match.groups()
            helper_total += 1
            op_key = operation if kind in {"call", "capabilities"} and operation else kind
            per_op[op_key] += 1
            if kind == "call" and operation in STATE_CHANGING_OPERATIONS:
                state_changing += 1

    invalid_hits = 0
    for event in events:
        if event.get("type") != "tool/result":
            continue
        data = event.get("data")
        if not isinstance(data, Mapping):
            continue
        message = data.get("message")
        source = message.get("source") if isinstance(message, Mapping) else None
        call_id = source.get("callId") if isinstance(source, Mapping) else None
        if call_id in bash_call_ids:
            invalid_hits += _invalid_request_count(message)

    input_tokens = output_tokens = cache_tokens = 0
    for event in events:
        if event.get("type") != "assistant/message":
            continue
        data = event.get("data")
        usage = data.get("usage") if isinstance(data, Mapping) else None
        if not isinstance(usage, Mapping):
            continue
        input_tokens += int(usage.get("inputTokens") or 0)
        output_tokens += int(usage.get("outputTokens") or 0)
        cache_tokens += int(usage.get("cacheReadTokens") or 0)

    fingerprint = audit_events(events)
    verdict = judge_comparability(fingerprint)
    models = sorted({header.model for header in fingerprint.headers})
    return {
        "session_id_hash": hashlib.sha256(session_id.encode("utf-8")).hexdigest(),
        "model": models[0] if len(models) == 1 else "+".join(models),
        "terminal_status": "complete" if verdict.verdict == "comparable" else verdict.verdict,
        "event_type_counts": dict(sorted(event_counts.items())),
        "bash_total": bash_total,
        "helper_direct_total": helper_total,
        "per_op": dict(sorted(per_op.items())),
        "helper_command_chars": helper_chars,
        "all_bash_command_chars": all_bash_chars,
        "python_heredoc_calls": heredoc,
        "invalid_request_hits": invalid_hits,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_tokens,
        "share_of_bash": helper_total / bash_total if bash_total else 0.0,
        "cache_amplification_proxy": cache_tokens / max(output_tokens, 1),
        "new_flag_counts": dict(sorted(new_flags.items())),
        "state_changing_helper_calls": state_changing,
        "session_comparability": {
            "verdict": verdict.verdict,
            "reasons": list(verdict.reasons),
        },
    }


def retained_record_problems(record: Mapping[str, object], protocol: Mapping[str, Any]) -> tuple[str, ...]:
    """Reject any persisted trial field outside the frozen allowlist."""

    allowed = set(protocol["retained_trial_schema"])
    problems: list[str] = []
    extras = sorted(set(record) - allowed)
    if extras:
        problems.append(f"extra-fields:{','.join(extras)}")
    missing = sorted(allowed - set(record))
    if missing:
        problems.append(f"missing-fields:{','.join(missing)}")
    denylist = set(protocol["artifact_denylist"])
    if set(record) & denylist:
        problems.append("denylist-field")
    return tuple(problems)


def paired_differences(
    records: Sequence[Mapping[str, object]],
    *,
    factor: str,
    metric: str,
) -> list[float]:
    """Return treatment-minus-control differences in deterministic pair order."""

    if factor == "phase1":
        control, treatment, stratum = "legacy_cli", "new_cli", "phase2"
    elif factor == "phase2":
        control, treatment, stratum = "full_object", "item_event", "phase1"
    else:
        raise ValueError("factor must be phase1 or phase2")
    indexed: dict[tuple[object, object, object], Mapping[str, object]] = {}
    for record in records:
        key = (record["replicate_id"], record[stratum], record[factor])
        if key in indexed:
            raise ValueError(f"duplicate paired record: {key}")
        indexed[key] = record
    differences: list[float] = []
    strata = sorted({record[stratum] for record in records})
    replicates = sorted({record["replicate_id"] for record in records})
    for stratum_value, replicate_id in itertools.product(strata, replicates):
        control_record = indexed.get((replicate_id, stratum_value, control))
        treatment_record = indexed.get((replicate_id, stratum_value, treatment))
        if control_record is None or treatment_record is None:
            raise ValueError(f"missing pair: {factor}/{stratum_value}/{replicate_id}")
        differences.append(float(treatment_record[metric]) - float(control_record[metric]))
    return differences


def _exact_sign_flip_pvalue(differences: Sequence[float]) -> float:
    if not differences:
        raise ValueError("at least one difference is required")
    observed = abs(sum(differences))
    sums = [0.0]
    for difference in differences:
        sums = [value + difference for value in sums] + [value - difference for value in sums]
    extreme = sum(abs(value) >= observed - 1e-12 for value in sums)
    return extreme / len(sums)


def _bootstrap_ci(differences: Sequence[float], *, samples: int = 10_000) -> tuple[float, float]:
    rng = random.Random(20_260_815)
    n = len(differences)
    means = sorted(sum(rng.choice(differences) for _ in range(n)) / n for _ in range(samples))
    return means[int(0.025 * samples)], means[int(0.975 * samples) - 1]


def paired_estimate(differences: Sequence[float]) -> dict[str, object]:
    """Compute the preregistered paired summary, exact sign flip, and bootstrap CI."""

    values = [float(value) for value in differences]
    low, high = _bootstrap_ci(values)
    return {
        "pairs": len(values),
        "mean_difference": statistics.fmean(values),
        "median_difference": statistics.median(values),
        "confidence_interval_95": [low, high],
        "two_sided_sign_flip_p": _exact_sign_flip_pvalue(values),
        "zero_differences": sum(value == 0 for value in values),
    }


def interaction_estimate(
    records: Sequence[Mapping[str, object]],
    *,
    metric: str,
) -> dict[str, object]:
    """Return P1 new-minus-legacy contrasts by P2 stratum and their difference."""

    by_phase2: dict[str, list[float]] = {}
    for phase2 in ("full_object", "item_event"):
        subset = [record for record in records if record["phase2"] == phase2]
        by_phase2[phase2] = paired_differences(subset, factor="phase1", metric=metric)
    interaction = [
        event - full
        for event, full in zip(by_phase2["item_event"], by_phase2["full_object"], strict=True)
    ]
    return {
        "legacy_to_new_with_full_object": paired_estimate(by_phase2["full_object"]),
        "legacy_to_new_with_item_event": paired_estimate(by_phase2["item_event"]),
        "difference_in_differences": paired_estimate(interaction),
    }


__all__ = [
    "CALIBER",
    "build_gold_after",
    "canonical_json",
    "canonical_sha256",
    "expand_assignments",
    "extract_session_metrics",
    "interaction_estimate",
    "paired_differences",
    "paired_estimate",
    "retained_record_problems",
    "score_raw_request",
    "validate_protocol",
]
