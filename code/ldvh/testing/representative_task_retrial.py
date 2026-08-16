"""Fail-closed orchestration for the representative Helper task retrial.

The protocol is intentionally single-arm: an observed Helper trace is compared
with a pre-registered legal trace.  The module can identify an operation-level
task-burden residual; it cannot establish a causal effect, business value, or a
product-wide Helper judgement.

Raw prompts, model prose, reasoning, and tool-result bodies are never returned
by this module.  Only structural session events, hashes, operation names, and
aggregate measurements may leave the runner-owned temporary root.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ldvh.testing.equivalence_retrial import CarrierDeclaration
from ldvh.testing.evidence_protocol import (
    check_pre_scoring_threshold,
    extract_trial_identity,
    judge_protocol_comparability,
)
from ldvh.testing.session_comparability import audit_events
from ldvh.testing.trial_measurement import SafeTrialTempRoot, TrialMeasurementError

PROTOCOL_SCHEMA_VERSION = "ldvh-representative-task-retrial-protocol/1"
RESULTS_SCHEMA_VERSION = "ldvh-representative-task-retrial-results/1"
SESSION_SCHEMA_VERSION = "ldvh-representative-task-retrial-session/1"
FAMILIES = ("read", "ordinary_fact_update", "workcase_non_item_update")
RUNNER_IDENTITY_SOURCE = "harness-request-header"
EXPECTED_FRAME_COUNT = 18
EXPECTED_SCHEDULE_COUNT = 36
MAXIMUM_ATTEMPTS = 42

_PROTOCOL_FIELDS = {
    "schema_version",
    "protocol_id",
    "frozen_at",
    "design",
    "source_binding",
    "runner_binding",
    "task_frames",
    "schedule",
    "measurements",
    "thresholds",
    "exclusions",
    "privacy",
    "stopping_rules",
    "reproduction",
}
_FRAME_FIELDS = {
    "task_id",
    "family",
    "operation_under_test",
    "task_prompt",
    "fixture_kind",
    "source_selection",
    "gold_legal_trace",
    "gold_assertions",
    "replicates",
}
_TRACE_STEP_FIELDS = {"operation", "purpose", "state_changing"}
_SCHEDULE_FIELDS = {"session_slot", "task_id", "replicate", "blind_task_key"}
_RUNNER_OBSERVATION_FIELDS = {
    "provider",
    "model",
    "runner_identity",
    "tool_entry",
    "entrypoint",
    "permission_profile",
    "prompt_layout",
    "identity_source",
}
_METRIC_FIELDS = {
    "helper_call_count",
    "gold_call_count",
    "helper_request_chars",
    "gold_request_chars",
    "helper_request_bytes",
    "helper_response_bytes",
    "invalid_request_count",
    "first_legal_action",
    "extra_rule_reads",
    "repair_count",
    "fallback_count",
    "duration_ms",
    "extra_duration_ms",
    "duration_unavailable_reason",
    "cache_observation",
    "cache_unavailable_reason",
}
_SESSION_FIELDS = {
    "schema_version",
    "trial_id",
    "attempt_index",
    "task_id",
    "family",
    "operation_under_test",
    "replicate",
    "blind_task_key",
    "protocol_sha256",
    "task_package_hash",
    "fixture_identity",
    "carrier_fingerprint",
    "provider",
    "model",
    "event_lines_sha256",
    "comparability",
    "comparability_reasons",
    "retained",
    "exclusion_reason",
    "helper_call_count",
    "gold_call_count",
    "extra_helper_calls",
    "helper_request_chars",
    "gold_request_chars",
    "extra_request_chars",
    "helper_request_bytes",
    "helper_response_bytes",
    "invalid_request_count",
    "first_legal_action",
    "extra_rule_reads",
    "repair_count",
    "fallback_count",
    "duration_ms",
    "extra_duration_ms",
    "duration_unavailable_reason",
    "cache_observation",
    "cache_unavailable_reason",
    "burden_points",
}


class RepresentativeRetrialError(TrialMeasurementError):
    """The representative retrial input cannot be trusted."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_exact_fields(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    actual = set(value)
    if actual != expected:
        raise RepresentativeRetrialError(
            f"{name} fields must be closed; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise RepresentativeRetrialError(f"{name} must be a non-empty string")
    return value


def _sha256_string(value: object, name: str) -> str:
    rendered = _nonempty_string(value, name)
    if len(rendered) != 64 or any(character not in "0123456789abcdef" for character in rendered):
        raise RepresentativeRetrialError(f"{name} must be a lowercase SHA-256")
    return rendered


def _nonnegative_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise RepresentativeRetrialError(f"{name} must be a non-negative integer")
    return value


def _nullable_nonnegative_number(value: object, name: str) -> float | None:
    if value is None:
        return None
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise RepresentativeRetrialError(f"{name} must be a non-negative finite number or null")
    return float(value)


def load_protocol(source: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    """Load and validate one frozen protocol without mutating it."""

    if isinstance(source, Mapping):
        protocol = json.loads(json.dumps(source, ensure_ascii=False))
    else:
        try:
            protocol = json.loads(Path(source).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RepresentativeRetrialError("protocol is not readable UTF-8 JSON") from error
    if not isinstance(protocol, dict):
        raise RepresentativeRetrialError("protocol must be a JSON object")
    validate_protocol(protocol)
    return protocol


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    """Validate the closed 18-frame/36-session protocol."""

    _require_exact_fields(protocol, _PROTOCOL_FIELDS, "protocol")
    if protocol["schema_version"] != PROTOCOL_SCHEMA_VERSION:
        raise RepresentativeRetrialError("unrecognized protocol schema version")
    _nonempty_string(protocol["protocol_id"], "protocol_id")
    _nonempty_string(protocol["frozen_at"], "frozen_at")

    design = protocol["design"]
    if not isinstance(design, Mapping):
        raise RepresentativeRetrialError("design must be an object")
    expected_design = {
        "design_kind",
        "claim_boundary",
        "representativeness_boundary",
        "families",
        "frames_per_family",
        "replicates_per_frame",
        "planned_retained_sessions",
        "maximum_technical_replacements",
        "maximum_attempts",
        "counterbalance",
        "scoring_blindness",
    }
    _require_exact_fields(design, expected_design, "design")
    if design["design_kind"] != "single-arm-gold-legal-trace":
        raise RepresentativeRetrialError("design_kind must remain single-arm-gold-legal-trace")
    if tuple(design["families"]) != FAMILIES:
        raise RepresentativeRetrialError("families must use the frozen three-family order")
    if (
        design["frames_per_family"] != 6
        or design["replicates_per_frame"] != 2
        or design["planned_retained_sessions"] != EXPECTED_SCHEDULE_COUNT
        or design["maximum_technical_replacements"] != 6
        or design["maximum_attempts"] != MAXIMUM_ATTEMPTS
    ):
        raise RepresentativeRetrialError("18/36/42 sample ceilings changed")

    runner = protocol["runner_binding"]
    if not isinstance(runner, Mapping):
        raise RepresentativeRetrialError("runner_binding must be an object")
    required_runner_fields = {
        "entrypoint",
        "model_binding_rule",
        "allowed_model_identity_source",
        "controller_declared_product_name",
        "controller_declared_model_name",
        "controller_declared_agent_runtime_name",
        "fixed_fields",
        "unknown_is_not_fixed",
    }
    _require_exact_fields(runner, required_runner_fields, "runner_binding")
    if runner["allowed_model_identity_source"] != RUNNER_IDENTITY_SOURCE:
        raise RepresentativeRetrialError("runner model identity source changed")
    if runner["unknown_is_not_fixed"] is not True:
        raise RepresentativeRetrialError("unknown runner identity must fail closed")

    frames = protocol["task_frames"]
    if not isinstance(frames, list) or len(frames) != EXPECTED_FRAME_COUNT:
        raise RepresentativeRetrialError("task_frames must contain exactly 18 frames")
    task_ids: set[str] = set()
    family_counts: Counter[str] = Counter()
    for frame in frames:
        if not isinstance(frame, Mapping):
            raise RepresentativeRetrialError("each task frame must be an object")
        _require_exact_fields(frame, _FRAME_FIELDS, "task frame")
        task_id = _nonempty_string(frame["task_id"], "task_id")
        if task_id in task_ids:
            raise RepresentativeRetrialError("task_id must be unique")
        task_ids.add(task_id)
        family = frame["family"]
        if family not in FAMILIES:
            raise RepresentativeRetrialError("task family is outside the frozen set")
        family_counts[family] += 1
        if frame["replicates"] != 2:
            raise RepresentativeRetrialError("every task frame must have two replicates")
        trace = frame["gold_legal_trace"]
        if not isinstance(trace, list) or not trace:
            raise RepresentativeRetrialError("gold_legal_trace must be non-empty")
        state_changing = 0
        for trace_step in trace:
            if not isinstance(trace_step, Mapping):
                raise RepresentativeRetrialError("gold trace step must be an object")
            _require_exact_fields(trace_step, _TRACE_STEP_FIELDS, "gold trace step")
            _nonempty_string(trace_step["operation"], "gold trace operation")
            _nonempty_string(trace_step["purpose"], "gold trace purpose")
            if type(trace_step["state_changing"]) is not bool:
                raise RepresentativeRetrialError("state_changing must be boolean")
            state_changing += int(trace_step["state_changing"])
        if family == "read" and state_changing:
            raise RepresentativeRetrialError("read frames cannot contain state-changing gold steps")
        if family != "read" and (
            state_changing != 1 or frame["fixture_kind"] != "isolated-governed-fixture"
        ):
            raise RepresentativeRetrialError("update frames require one isolated state-changing step")
    if family_counts != Counter({family: 6 for family in FAMILIES}):
        raise RepresentativeRetrialError("each family must contain exactly six frames")

    schedule = protocol["schedule"]
    if not isinstance(schedule, list) or len(schedule) != EXPECTED_SCHEDULE_COUNT:
        raise RepresentativeRetrialError("schedule must contain exactly 36 sessions")
    slots: list[int] = []
    blind_keys: set[str] = set()
    task_replicates: dict[str, set[int]] = defaultdict(set)
    for entry in schedule:
        if not isinstance(entry, Mapping):
            raise RepresentativeRetrialError("schedule entry must be an object")
        _require_exact_fields(entry, _SCHEDULE_FIELDS, "schedule entry")
        slot = _nonnegative_int(entry["session_slot"], "session_slot")
        slots.append(slot)
        task_id = _nonempty_string(entry["task_id"], "schedule task_id")
        if task_id not in task_ids:
            raise RepresentativeRetrialError("schedule references an unknown task")
        replicate = entry["replicate"]
        if replicate not in {1, 2}:
            raise RepresentativeRetrialError("schedule replicate must be 1 or 2")
        task_replicates[task_id].add(replicate)
        blind_key = _nonempty_string(entry["blind_task_key"], "blind_task_key")
        if blind_key in blind_keys:
            raise RepresentativeRetrialError("blind_task_key must be unique")
        blind_keys.add(blind_key)
    if slots != list(range(1, EXPECTED_SCHEDULE_COUNT + 1)):
        raise RepresentativeRetrialError("session slots must be the closed 1..36 sequence")
    if set(task_replicates) != task_ids or any(value != {1, 2} for value in task_replicates.values()):
        raise RepresentativeRetrialError("every task must appear once per replicate")

    source_binding = protocol["source_binding"]
    if not isinstance(source_binding, Mapping):
        raise RepresentativeRetrialError("source_binding must be an object")
    for field_name in ("helper_capabilities_sha256", "target_spark_content_fingerprint"):
        _sha256_string(source_binding.get(field_name), field_name)
    if not isinstance(protocol["measurements"], Mapping):
        raise RepresentativeRetrialError("measurements must be an object")
    if not isinstance(protocol["thresholds"], Mapping):
        raise RepresentativeRetrialError("thresholds must be an object")
    if not isinstance(protocol["exclusions"], Mapping):
        raise RepresentativeRetrialError("exclusions must be an object")
    if protocol["exclusions"].get("maximum_replacements") != 6:
        raise RepresentativeRetrialError("maximum replacements changed")
    if protocol["exclusions"].get("replacement_allowed_only_for") != [
        "technical_failure_before_target"
    ]:
        raise RepresentativeRetrialError("replacement reason changed")
    if not isinstance(protocol["privacy"], Mapping) or not isinstance(
        protocol["privacy"].get("forbidden_fields"), list
    ):
        raise RepresentativeRetrialError("privacy boundary is incomplete")
    if not isinstance(protocol["stopping_rules"], list) or not protocol["stopping_rules"]:
        raise RepresentativeRetrialError("stopping_rules must be non-empty")
    if not isinstance(protocol["reproduction"], Mapping):
        raise RepresentativeRetrialError("reproduction must be an object")


def protocol_sha256(protocol: Mapping[str, Any]) -> str:
    """Return the canonical hash of a fully validated protocol."""

    validate_protocol(protocol)
    return _canonical_sha256(protocol)


def task_package_hash(frame: Mapping[str, Any]) -> str:
    """Hash one frozen task frame without exposing it to a result artifact."""

    _require_exact_fields(frame, _FRAME_FIELDS, "task frame")
    return _canonical_sha256(frame)


@dataclass(frozen=True, slots=True)
class RunnerPreflight:
    """The auditable fixed-carrier decision made before any trial."""

    status: str
    reasons: tuple[str, ...]
    provider: str | None
    model: str | None
    runner_identity: str | None
    tool_entry: str | None
    entrypoint: str | None
    permission_profile: str | None
    prompt_layout: str | None
    identity_source: str | None
    carrier_fingerprint: str | None

    def payload(self) -> dict[str, Any]:
        return asdict(self)


def assess_runner_preflight(
    protocol: Mapping[str, Any], observation: Mapping[str, Any]
) -> RunnerPreflight:
    """Bind a directly observed carrier or stop before attempt one."""

    validate_protocol(protocol)
    _require_exact_fields(observation, _RUNNER_OBSERVATION_FIELDS, "runner observation")
    values: dict[str, str | None] = {}
    for field_name in _RUNNER_OBSERVATION_FIELDS:
        value = observation[field_name]
        if value is not None and (not isinstance(value, str) or not value):
            raise RepresentativeRetrialError(f"runner observation {field_name} must be non-empty or null")
        values[field_name] = value

    reasons: list[str] = []
    if (
        values["identity_source"] != RUNNER_IDENTITY_SOURCE
        or values["provider"] is None
        or values["model"] is None
    ):
        reasons.append("runner_model_identity_unavailable")
    if values["runner_identity"] is None or values["tool_entry"] is None:
        reasons.append("runner_identity_drift")
    if values["entrypoint"] != protocol["runner_binding"]["entrypoint"]:
        reasons.append("entrypoint_drift")
    if values["permission_profile"] is None:
        reasons.append("permission_profile_drift")
    if values["prompt_layout"] is None:
        reasons.append("prompt_layout_drift")

    reasons = list(dict.fromkeys(reasons))
    carrier_fingerprint: str | None = None
    if not reasons:
        carrier = CarrierDeclaration(
            provider=values["provider"],  # type: ignore[arg-type]
            model=values["model"],  # type: ignore[arg-type]
            runner_identity=values["runner_identity"],  # type: ignore[arg-type]
            tool_entry=values["tool_entry"],  # type: ignore[arg-type]
        )
        carrier_fingerprint = carrier.fingerprint()
    return RunnerPreflight(
        status="comparable" if not reasons else "not_comparable",
        reasons=tuple(reasons),
        provider=values["provider"],
        model=values["model"],
        runner_identity=values["runner_identity"],
        tool_entry=values["tool_entry"],
        entrypoint=values["entrypoint"],
        permission_profile=values["permission_profile"],
        prompt_layout=values["prompt_layout"],
        identity_source=values["identity_source"],
        carrier_fingerprint=carrier_fingerprint,
    )


def create_isolated_trial_root(*, repository_root: Path) -> SafeTrialTempRoot:
    """Create an identity-bound trial root outside the repository."""

    return SafeTrialTempRoot.create(prefix="ldvh-representative-retrial-", repository_root=repository_root)


def guard_state_changing_target(
    *, repository_root: Path, trial_root: SafeTrialTempRoot, target: Path
) -> None:
    """Reject any state-changing target outside the runner-owned trial root."""

    repository = repository_root.resolve(strict=True)
    isolated = trial_root.root.resolve(strict=True)
    candidate = target.resolve(strict=False)
    if candidate == repository or repository in candidate.parents:
        raise RepresentativeRetrialError("state-changing trial target cannot be inside the repository")
    if candidate != isolated and isolated not in candidate.parents:
        raise RepresentativeRetrialError("state-changing trial target escaped the isolated root")


def assert_current_fact_fingerprint_unchanged(*, before: str, after: str) -> None:
    """Fail closed when a trial changed the current governed fact set."""

    _sha256_string(before, "before fact fingerprint")
    _sha256_string(after, "after fact fingerprint")
    if before != after:
        raise RepresentativeRetrialError("current governed fact fingerprint changed during trial")


def _frame_by_id(protocol: Mapping[str, Any], task_id: str) -> Mapping[str, Any]:
    matches = [frame for frame in protocol["task_frames"] if frame["task_id"] == task_id]
    if len(matches) != 1:
        raise RepresentativeRetrialError("task_id does not resolve uniquely")
    return matches[0]


def _schedule_entry(
    protocol: Mapping[str, Any], *, task_id: str, replicate: int
) -> Mapping[str, Any]:
    matches = [
        entry
        for entry in protocol["schedule"]
        if entry["task_id"] == task_id and entry["replicate"] == replicate
    ]
    if len(matches) != 1:
        raise RepresentativeRetrialError("task/replicate does not resolve uniquely")
    return matches[0]


def _validate_metrics(metrics: Mapping[str, Any]) -> None:
    _require_exact_fields(metrics, _METRIC_FIELDS, "session metrics")
    for field_name in (
        "helper_call_count",
        "gold_call_count",
        "helper_request_chars",
        "gold_request_chars",
        "helper_request_bytes",
        "helper_response_bytes",
        "invalid_request_count",
        "extra_rule_reads",
        "repair_count",
        "fallback_count",
    ):
        _nonnegative_int(metrics[field_name], field_name)
    if type(metrics["first_legal_action"]) is not bool:
        raise RepresentativeRetrialError("first_legal_action must be boolean")
    duration = _nullable_nonnegative_number(metrics["duration_ms"], "duration_ms")
    extra_duration = _nullable_nonnegative_number(metrics["extra_duration_ms"], "extra_duration_ms")
    duration_reason = metrics["duration_unavailable_reason"]
    if (duration is None or extra_duration is None) != (duration_reason is not None):
        raise RepresentativeRetrialError("duration nullability requires one unavailable reason")
    if duration_reason is not None:
        _nonempty_string(duration_reason, "duration_unavailable_reason")
    cache = metrics["cache_observation"]
    cache_reason = metrics["cache_unavailable_reason"]
    if cache is None:
        _nonempty_string(cache_reason, "cache_unavailable_reason")
    else:
        _nonempty_string(cache, "cache_observation")
        if cache_reason is not None:
            raise RepresentativeRetrialError("available cache observation cannot carry unavailable reason")


def _burden_points(metrics: Mapping[str, Any]) -> float | None:
    if metrics["extra_duration_ms"] is None:
        return None
    extra_calls = max(metrics["helper_call_count"] - metrics["gold_call_count"], 0)
    extra_chars = max(metrics["helper_request_chars"] - metrics["gold_request_chars"], 0)
    return round(
        metrics["invalid_request_count"] * 4.0
        + (metrics["repair_count"] + metrics["fallback_count"]) * 3.0
        + extra_calls * 2.0
        + metrics["extra_rule_reads"]
        + min(extra_chars / 500.0, 2.0)
        + min(metrics["extra_duration_ms"] / 2000.0, 2.0),
        6,
    )


def make_session_record(
    *,
    protocol: Mapping[str, Any],
    preflight: RunnerPreflight,
    trial_id: str,
    attempt_index: int,
    task_id: str,
    replicate: int,
    task_package_sha256: str,
    expected_fixture_identity: str,
    actual_fixture_identity: str,
    observed_carrier_fingerprint: str,
    event_lines: Sequence[str],
    metrics: Mapping[str, Any],
) -> dict[str, Any]:
    """Convert one structural session into a privacy-safe machine record."""

    validate_protocol(protocol)
    if preflight.status != "comparable" or preflight.carrier_fingerprint is None:
        raise RepresentativeRetrialError("cannot create a session record after failed preflight")
    _nonempty_string(trial_id, "trial_id")
    _nonnegative_int(attempt_index, "attempt_index")
    if attempt_index < 1 or attempt_index > MAXIMUM_ATTEMPTS:
        raise RepresentativeRetrialError("attempt_index is outside 1..42")
    if replicate not in {1, 2}:
        raise RepresentativeRetrialError("replicate must be 1 or 2")
    _sha256_string(task_package_sha256, "task_package_sha256")
    _nonempty_string(expected_fixture_identity, "expected_fixture_identity")
    _nonempty_string(actual_fixture_identity, "actual_fixture_identity")
    _sha256_string(observed_carrier_fingerprint, "observed_carrier_fingerprint")
    _validate_metrics(metrics)

    frame = _frame_by_id(protocol, task_id)
    schedule = _schedule_entry(protocol, task_id=task_id, replicate=replicate)
    expected_task_hash = task_package_hash(frame)
    protocol_hash = protocol_sha256(protocol)
    try:
        parsed_events = [json.loads(line) for line in event_lines]
    except (TypeError, json.JSONDecodeError) as error:
        raise RepresentativeRetrialError("event lines must be valid JSON objects") from error
    if not parsed_events or any(not isinstance(event, Mapping) for event in parsed_events):
        raise RepresentativeRetrialError("event lines must contain JSON objects")
    session_fingerprint = audit_events(parsed_events)

    reference_identity = extract_trial_identity(
        task_id=task_id,
        task_package_hash=expected_task_hash,
        contract_sha256=protocol_hash,
        payload={
            "blind_task_key": schedule["blind_task_key"],
            "fixture_identity": expected_fixture_identity,
        },
        carrier_fingerprint=preflight.carrier_fingerprint,
    )
    trial_identity = extract_trial_identity(
        task_id=task_id,
        task_package_hash=task_package_sha256,
        contract_sha256=protocol_hash,
        payload={
            "blind_task_key": schedule["blind_task_key"],
            "fixture_identity": actual_fixture_identity,
        },
        carrier_fingerprint=observed_carrier_fingerprint,
    )
    comparable = judge_protocol_comparability(
        session_fingerprint,
        trial_identity=trial_identity,
        reference_identity=reference_identity,
    )
    passed, threshold_reason = check_pre_scoring_threshold(comparable)
    exclusion_reason: str | None = None
    if observed_carrier_fingerprint != preflight.carrier_fingerprint:
        exclusion_reason = "runner_identity_drift"
    elif session_fingerprint.distinct_entries != ((preflight.provider, preflight.model),):
        exclusion_reason = "runner_identity_drift"
    elif not passed:
        exclusion_reason = (
            "out_of_protocol_identity"
            if threshold_reason == "out_of_protocol"
            else "event_graph_pairing_incomplete"
        )

    burden = _burden_points(metrics)
    if burden is None and exclusion_reason is None:
        exclusion_reason = "missing_key_metric"
    retained = exclusion_reason is None
    record = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "trial_id": trial_id,
        "attempt_index": attempt_index,
        "task_id": task_id,
        "family": frame["family"],
        "operation_under_test": frame["operation_under_test"],
        "replicate": replicate,
        "blind_task_key": schedule["blind_task_key"],
        "protocol_sha256": protocol_hash,
        "task_package_hash": task_package_sha256,
        "fixture_identity": _canonical_sha256(actual_fixture_identity),
        "carrier_fingerprint": observed_carrier_fingerprint,
        "provider": preflight.provider,
        "model": preflight.model,
        "event_lines_sha256": _canonical_sha256(list(event_lines)),
        "comparability": comparable.effective_verdict,
        "comparability_reasons": list(
            comparable.session_verdict.reasons + comparable.protocol_reasons
        ),
        "retained": retained,
        "exclusion_reason": exclusion_reason,
        "helper_call_count": metrics["helper_call_count"],
        "gold_call_count": metrics["gold_call_count"],
        "extra_helper_calls": max(metrics["helper_call_count"] - metrics["gold_call_count"], 0),
        "helper_request_chars": metrics["helper_request_chars"],
        "gold_request_chars": metrics["gold_request_chars"],
        "extra_request_chars": max(
            metrics["helper_request_chars"] - metrics["gold_request_chars"], 0
        ),
        "helper_request_bytes": metrics["helper_request_bytes"],
        "helper_response_bytes": metrics["helper_response_bytes"],
        "invalid_request_count": metrics["invalid_request_count"],
        "first_legal_action": metrics["first_legal_action"],
        "extra_rule_reads": metrics["extra_rule_reads"],
        "repair_count": metrics["repair_count"],
        "fallback_count": metrics["fallback_count"],
        "duration_ms": metrics["duration_ms"],
        "extra_duration_ms": metrics["extra_duration_ms"],
        "duration_unavailable_reason": metrics["duration_unavailable_reason"],
        "cache_observation": metrics["cache_observation"],
        "cache_unavailable_reason": metrics["cache_unavailable_reason"],
        "burden_points": burden,
    }
    validate_session_record(record, protocol)
    return record


def validate_session_record(record: Mapping[str, Any], protocol: Mapping[str, Any]) -> None:
    """Validate the closed privacy-safe session record schema."""

    validate_protocol(protocol)
    _require_exact_fields(record, _SESSION_FIELDS, "session record")
    if record["schema_version"] != SESSION_SCHEMA_VERSION:
        raise RepresentativeRetrialError("unrecognized session schema version")
    if record["protocol_sha256"] != protocol_sha256(protocol):
        raise RepresentativeRetrialError("session protocol hash mismatch")
    frame = _frame_by_id(protocol, record["task_id"])
    schedule = _schedule_entry(protocol, task_id=record["task_id"], replicate=record["replicate"])
    if record["family"] != frame["family"] or record["operation_under_test"] != frame[
        "operation_under_test"
    ]:
        raise RepresentativeRetrialError("session task projection drifted")
    if record["blind_task_key"] != schedule["blind_task_key"]:
        raise RepresentativeRetrialError("session blind key drifted")
    _nonnegative_int(record["attempt_index"], "attempt_index")
    if record["attempt_index"] not in range(1, MAXIMUM_ATTEMPTS + 1):
        raise RepresentativeRetrialError("attempt_index is outside 1..42")
    if type(record["retained"]) is not bool:
        raise RepresentativeRetrialError("retained must be boolean")
    if record["retained"] != (record["exclusion_reason"] is None):
        raise RepresentativeRetrialError("retained must exactly match exclusion_reason absence")
    if record["exclusion_reason"] is not None and record["exclusion_reason"] not in protocol[
        "exclusions"
    ]["closed_reason_codes"]:
        raise RepresentativeRetrialError("session exclusion reason is outside the frozen set")
    if record["retained"] and record["burden_points"] is None:
        raise RepresentativeRetrialError("retained session requires burden_points")
    for field_name in ("task_package_hash", "fixture_identity", "carrier_fingerprint", "event_lines_sha256"):
        _sha256_string(record[field_name], field_name)


def _percentile(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * quantile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _bootstrap_median_ci(values: Sequence[float], *, seed: int) -> tuple[float, float]:
    generator = random.Random(seed)
    medians = [
        statistics.median(generator.choice(values) for _ in range(len(values)))
        for _ in range(10_000)
    ]
    return (round(_percentile(medians, 0.025), 6), round(_percentile(medians, 0.975), 6))


def _family_result(
    family: str, records: Sequence[Mapping[str, Any]], *, seed: int
) -> dict[str, Any]:
    retained = [record for record in records if record["retained"]]
    by_frame: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in retained:
        by_frame[record["task_id"]].append(record)
    complete = len(by_frame) == 6 and all(
        len(frame_records) == 2
        and {record["replicate"] for record in frame_records} == {1, 2}
        for frame_records in by_frame.values()
    )
    if not complete:
        return {
            "family": family,
            "status": "not_comparable",
            "reason": "family_frame_completeness_failed",
            "retained_sessions": len(retained),
            "complete_frames": sum(len(value) == 2 for value in by_frame.values()),
            "positive_frames": None,
            "median_frame_burden_points": None,
            "bootstrap_median_ci_95": None,
        }
    frame_values: list[float] = []
    positive_frames = 0
    for task_id in sorted(by_frame):
        burdens = [float(record["burden_points"]) for record in by_frame[task_id]]
        frame_values.append(statistics.mean(burdens))
        positive_frames += int(all(value >= 2.0 for value in burdens))
    median = statistics.median(frame_values)
    interval = _bootstrap_median_ci(frame_values, seed=seed)
    go = positive_frames >= 5 and median >= 2.0 and interval[0] > 0
    return {
        "family": family,
        "status": "go-to-narrow-design-workcase" if go else "no-go",
        "reason": "all_preregistered_thresholds_met" if go else "one_or_more_thresholds_not_met",
        "retained_sessions": len(retained),
        "complete_frames": 6,
        "positive_frames": positive_frames,
        "median_frame_burden_points": round(median, 6),
        "bootstrap_median_ci_95": list(interval),
    }


def build_results(
    *,
    protocol: Mapping[str, Any],
    preflight: RunnerPreflight,
    records: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    """Build a hash-bound batch result without raw session content."""

    validate_protocol(protocol)
    _nonempty_string(generated_at, "generated_at")
    if len(records) > MAXIMUM_ATTEMPTS:
        raise RepresentativeRetrialError("record count exceeds the 42-attempt ceiling")
    if preflight.status != "comparable" and records:
        raise RepresentativeRetrialError("failed preflight must stop before attempt one")
    for record in records:
        validate_session_record(record, protocol)
    attempt_indices = [record["attempt_index"] for record in records]
    if len(attempt_indices) != len(set(attempt_indices)):
        raise RepresentativeRetrialError("attempt_index must be unique")

    exclusions = [
        {
            "attempt_index": record["attempt_index"],
            "task_id": record["task_id"],
            "reason": record["exclusion_reason"],
        }
        for record in records
        if not record["retained"]
    ]
    if preflight.status != "comparable":
        exclusions.insert(
            0,
            {
                "attempt_index": None,
                "task_id": None,
                "reason": preflight.reasons[0] if preflight.reasons else "runner_model_identity_unavailable",
            },
        )
        family_results = [
            {
                "family": family,
                "status": "not_comparable",
                "reason": exclusions[0]["reason"],
                "retained_sessions": 0,
                "complete_frames": 0,
                "positive_frames": None,
                "median_frame_burden_points": None,
                "bootstrap_median_ci_95": None,
            }
            for family in FAMILIES
        ]
    else:
        family_results = [
            _family_result(
                family,
                [record for record in records if record["family"] == family],
                seed=int(protocol["reproduction"]["bootstrap_seed"]),
            )
            for family in FAMILIES
        ]
    retained_count = sum(bool(record["retained"]) for record in records)
    complete_family_set = all(
        family_result["status"] in {"go-to-narrow-design-workcase", "no-go"}
        for family_result in family_results
    )
    result_payload = {
        "batch_status": (
            "not_comparable"
            if preflight.status != "comparable"
            else "complete"
            if retained_count == EXPECTED_SCHEDULE_COUNT and complete_family_set
            else "partial"
        ),
        "claim_boundary": protocol["design"]["claim_boundary"],
        "preflight": preflight.payload(),
        "attempt_count": len(records),
        "retained_session_count": retained_count,
        "maximum_attempts": MAXIMUM_ATTEMPTS,
        "exclusion_ledger": exclusions,
        "family_results": family_results,
        "unavailable_semantics": {
            "host_received": "unavailable",
            "causal_effect": "not_measured",
            "business_benefit": "not_measured",
            "raw_session_content": "not_retained",
        },
        "reproduction": {
            "bootstrap_seed": protocol["reproduction"]["bootstrap_seed"],
            "protocol_schema_version": protocol["schema_version"],
            "session_schema_version": SESSION_SCHEMA_VERSION,
            "record_hashes": [_canonical_sha256(record) for record in records],
        },
    }
    artifact = {
        "schema_version": RESULTS_SCHEMA_VERSION,
        "protocol_sha256": protocol_sha256(protocol),
        "generated_at": generated_at,
        "result": result_payload,
        "results_payload_sha256": _canonical_sha256(result_payload),
    }
    return artifact


def validate_results(results: Mapping[str, Any], protocol: Mapping[str, Any]) -> None:
    """Validate the hash binding of a result artifact."""

    expected = {
        "schema_version",
        "protocol_sha256",
        "generated_at",
        "result",
        "results_payload_sha256",
    }
    _require_exact_fields(results, expected, "results")
    if results["schema_version"] != RESULTS_SCHEMA_VERSION:
        raise RepresentativeRetrialError("unrecognized results schema version")
    if results["protocol_sha256"] != protocol_sha256(protocol):
        raise RepresentativeRetrialError("results protocol hash mismatch")
    if results["results_payload_sha256"] != _canonical_sha256(results["result"]):
        raise RepresentativeRetrialError("results payload hash mismatch")


def render_report(
    *, protocol: Mapping[str, Any], results: Mapping[str, Any], results_file_sha256: str
) -> str:
    """Render a concise report whose claims stay inside the protocol boundary."""

    validate_results(results, protocol)
    _sha256_string(results_file_sha256, "results_file_sha256")
    payload = results["result"]
    lines = [
        "# Representative Helper task retrial v1",
        "",
        "## Decision boundary",
        "",
        protocol["design"]["claim_boundary"],
        "",
        "## Reproduction binding",
        "",
        f"- Protocol SHA-256: `{results['protocol_sha256']}`",
        f"- Results payload SHA-256: `{results['results_payload_sha256']}`",
        f"- Results file SHA-256: `{results_file_sha256}`",
        f"- Batch status: `{payload['batch_status']}`",
        f"- Attempts / retained: `{payload['attempt_count']} / {payload['retained_session_count']}`",
        "",
        "## Operation-family decisions",
        "",
        "| Family | Decision | Comparable frames | Positive frames | Median burden | 95% CI |",
        "|---|---|---:|---:|---:|---|",
    ]
    for family in payload["family_results"]:
        interval = family["bootstrap_median_ci_95"]
        interval_text = "n/a" if interval is None else f"[{interval[0]}, {interval[1]}]"
        lines.append(
            "| {family} | {status} | {complete} | {positive} | {median} | {interval} |".format(
                family=family["family"],
                status=family["status"],
                complete=family["complete_frames"],
                positive="n/a" if family["positive_frames"] is None else family["positive_frames"],
                median=(
                    "n/a"
                    if family["median_frame_burden_points"] is None
                    else family["median_frame_burden_points"]
                ),
                interval=interval_text,
            )
        )
    lines.extend(
        [
            "",
            "## Exclusions and unavailable semantics",
            "",
            f"- Exclusion ledger entries: `{len(payload['exclusion_ledger'])}`",
            f"- Preflight reasons: `{', '.join(payload['preflight']['reasons']) or 'none'}`",
            "- Host-received delivery is unavailable; causal effect and business benefit were not measured.",
            "- Raw session content was not retained in version-controlled artifacts.",
            "",
            "## Interpretation",
            "",
        ]
    )
    if payload["batch_status"] == "not_comparable":
        lines.append(
            "The fixed execution carrier could not be established from the pre-registered auditable source, "
            "so no trial was attempted and no operation-level residual was scored."
        )
    else:
        lines.append(
            "Each family decision is limited to the frozen frames and burden proxy. A go result only merits "
            "a separate narrow design WorkCase; it does not authorize production changes."
        )
    return "\n".join(lines) + "\n"


def write_new_json_artifact(path: Path, value: Mapping[str, Any]) -> None:
    """Create a new JSON artifact without overwriting an existing path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_new_text_artifact(path: Path, value: str) -> None:
    """Create a new UTF-8 text artifact without overwriting an existing path."""

    _nonempty_string(value, "text artifact")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(value)
