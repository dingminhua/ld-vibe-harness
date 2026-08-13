"""Privacy-limited, replayable evidence for local-edit candidate trials.

The record deliberately stores protocol observations, not Helper request or
response bodies.  It is an observation source only: no projection produced by
this module proves that a candidate is correct, that a fact changed, or that a
WorkCase is complete.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ldvh.testing.trial_measurement import SafeTrialTempRoot, TrialMeasurementError

EVIDENCE_SCHEMA_VERSION = "ldvh-local-edit-evidence/2"
RUNNER_VERSION = "ldvh-local-edit-evidence-runner/2"
OPERATION_KEY = "prepare-local-edit-candidates"
Projection = Literal["observed", "failed", "timeout", "inconclusive"]

_SHA256 = re.compile(r"[0-9a-f]{64}")
_PROJECTIONS = frozenset({"observed", "failed", "timeout", "inconclusive"})
_TRACE_SPECS: dict[str, dict[str, Any]] = {
    "T1": {
        "origin": "real_helper",
        "events": ("request_observed", "response_observed", "external_state_checked", "verification_completed"),
        "calls": 1,
        "repairs": 0,
        "projection": "observed",
        "helper_outcome": "ok",
        "stale": False,
    },
    "T2": {
        "origin": "real_helper",
        "events": (
            "request_observed",
            "initial_response_observed",
            "repair_request_observed",
            "repaired_response_observed",
            "external_state_checked",
            "verification_completed",
        ),
        "calls": 2,
        "repairs": 1,
        "projection": "observed",
        "helper_outcome": "ok",
        "stale": False,
    },
    "T3a": {
        "origin": "real_helper",
        "events": ("request_observed", "response_observed", "external_state_checked", "verification_completed"),
        "calls": 1,
        "repairs": 0,
        "projection": "failed",
        "helper_outcome": "rejected",
        "stale": None,
    },
    "T3b": {
        "origin": "synthetic_harness",
        "events": ("deadline_observed", "verification_completed"),
        "calls": 0,
        "repairs": 0,
        "projection": "timeout",
        "helper_outcome": "timeout",
        "stale": None,
    },
    "T4a": {
        "origin": "synthetic_harness",
        "events": ("interruption_observed", "verification_completed"),
        "calls": 0,
        "repairs": 0,
        "projection": "inconclusive",
        "helper_outcome": "not_observed",
        "stale": None,
    },
    "T4b": {
        "origin": "synthetic_harness",
        "events": ("integrity_violation_observed", "verification_completed"),
        "calls": 0,
        "repairs": 0,
        "projection": "inconclusive",
        "helper_outcome": "not_observed",
        "stale": None,
    },
}
_INPUT_KINDS = frozenset({"rule_locator", "capability_locator", "task_package"})
_INPUT_STATUSES = frozenset({"delivered", "unavailable"})
_HASH_SUBJECTS = frozenset({"public_stable_identifier", "canonical_high_entropy_task_package"})
_FAULT_EVIDENCE_KINDS = frozenset(
    {"rejected_response", "process_exit", "deadline", "interruption", "integrity_violation"}
)
_SENSITIVE_HASH_SUBJECTS = frozenset(
    {
        "fact_body",
        "candidate_before",
        "candidate_after",
        "candidate_diff",
        "helper_request",
        "helper_response",
        "full_prompt",
    }
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _closed(value: Mapping[str, Any], fields: set[str], name: str) -> None:
    if set(value) != fields:
        raise TrialMeasurementError(
            f"{name} fields must be closed; missing={sorted(fields - set(value))}, "
            f"extra={sorted(set(value) - fields)}"
        )


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TrialMeasurementError(f"{name} must be a non-empty string")
    return value


def _sha(value: object, name: str) -> str:
    text = _text(value, name)
    if _SHA256.fullmatch(text) is None:
        raise TrialMeasurementError(f"{name} must be a lowercase SHA-256")
    return text


def task_package_fingerprint(package: Mapping[str, Any], *, entropy_nonce: str) -> str:
    """Hash a canonical task package only when it carries an explicit nonce.

    The nonce is part of the experiment protocol, not sensitive task prose.  A
    128-bit hex minimum keeps short or guessable text from being accepted as a
    supposedly privacy-preserving hash subject.
    """

    if re.fullmatch(r"[0-9a-f]{32,}", entropy_nonce) is None:
        raise TrialMeasurementError("task package entropy_nonce must contain at least 128 bits of hex entropy")
    if not isinstance(package, Mapping) or not package:
        raise TrialMeasurementError("task package must be a non-empty object")
    forbidden = _SENSITIVE_HASH_SUBJECTS.intersection(package)
    if forbidden:
        raise TrialMeasurementError(f"task package contains forbidden hash subjects: {sorted(forbidden)}")
    return _digest({"hash_subject": "canonical_high_entropy_task_package", "nonce": entropy_nonce, "package": package})


@dataclass(frozen=True, slots=True)
class EvidenceIdentity:
    run_id: str
    trial_id: str
    worktree_fingerprint: str
    governed_project_id: str
    task_package_fingerprint: str
    rule_fingerprint: str
    capability_fingerprint: str
    runner_fingerprint: str

    def to_json(self) -> dict[str, str]:
        value = {
            "run_id": _text(self.run_id, "run_id"),
            "trial_id": _text(self.trial_id, "trial_id"),
            "worktree_fingerprint": _sha(self.worktree_fingerprint, "worktree_fingerprint"),
            "governed_project_id": _text(self.governed_project_id, "governed_project_id"),
            "task_package_fingerprint": _sha(self.task_package_fingerprint, "task_package_fingerprint"),
            "rule_fingerprint": _sha(self.rule_fingerprint, "rule_fingerprint"),
            "capability_fingerprint": _sha(self.capability_fingerprint, "capability_fingerprint"),
            "runner_fingerprint": _sha(self.runner_fingerprint, "runner_fingerprint"),
        }
        return value


def input_receipt(
    *,
    kind: str,
    status: str,
    locator: str,
    source_range: str | None = None,
    fingerprint: str | None = None,
    unavailable_reason: str | None = None,
    length: int | None = None,
    hash_subject: str = "public_stable_identifier",
) -> dict[str, Any]:
    """Create a body-free receipt for input the harness can prove it delivered."""

    if kind not in _INPUT_KINDS:
        raise TrialMeasurementError("input receipt kind is not allowed")
    if status not in _INPUT_STATUSES:
        raise TrialMeasurementError("input receipt status is not allowed")
    if hash_subject in _SENSITIVE_HASH_SUBJECTS or hash_subject not in _HASH_SUBJECTS:
        raise TrialMeasurementError("input receipt hash_subject is not allowed")
    _text(locator, "input receipt locator")
    if source_range is not None:
        _text(source_range, "input receipt source_range")
    if length is not None and (type(length) is not int or length < 0):
        raise TrialMeasurementError("input receipt length must be a non-negative integer or null")
    if status == "delivered":
        _sha(fingerprint, "delivered input fingerprint")
        if unavailable_reason is not None:
            raise TrialMeasurementError("delivered input cannot have unavailable_reason")
    else:
        if fingerprint is not None:
            raise TrialMeasurementError("unavailable input cannot have a fingerprint")
        _text(unavailable_reason, "unavailable input reason")
    return {
        "kind": kind,
        "status": status,
        "locator": locator,
        "source_range": source_range,
        "fingerprint": fingerprint,
        "unavailable_reason": unavailable_reason,
        "length": length,
        "hash_subject": hash_subject,
    }


def trace_event(
    sequence: int,
    name: str,
    *,
    call_index: int | None = None,
    response_bytes: int | None = None,
    duration_ms: int | None = None,
) -> dict[str, Any]:
    if type(sequence) is not int or sequence < 0:
        raise TrialMeasurementError("event sequence must be a non-negative integer")
    for value, field in ((call_index, "call_index"), (response_bytes, "response_bytes"), (duration_ms, "duration_ms")):
        if value is not None and (type(value) is not int or value < 0):
            raise TrialMeasurementError(f"{field} must be a non-negative integer or null")
    return {
        "sequence": sequence,
        "name": _text(name, "event name"),
        "call_index": call_index,
        "response_bytes": response_bytes,
        "duration_ms": duration_ms,
    }


def build_record(
    *,
    identity: EvidenceIdentity,
    trace_id: str,
    inputs: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    helper_calls: int,
    repairs: int,
    external_state: Mapping[str, Any],
    verification: Mapping[str, Any],
    fault: Mapping[str, Any],
) -> dict[str, Any]:
    record = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "runner_version": RUNNER_VERSION,
        "identity": identity.to_json(),
        "operation_key": OPERATION_KEY,
        "trace_id": trace_id,
        "inputs": [dict(item) for item in inputs],
        "events": [dict(item) for item in events],
        "helper_calls": helper_calls,
        "repairs": repairs,
        "external_state": dict(external_state),
        "verification": dict(verification),
        "fault": dict(fault),
    }
    validate_record(record)
    return record


def validate_record(record: Mapping[str, Any]) -> None:
    _closed(
        record,
        {
            "schema_version",
            "runner_version",
            "identity",
            "operation_key",
            "trace_id",
            "inputs",
            "events",
            "helper_calls",
            "repairs",
            "external_state",
            "verification",
            "fault",
        },
        "evidence record",
    )
    if record["schema_version"] != EVIDENCE_SCHEMA_VERSION or record["runner_version"] != RUNNER_VERSION:
        raise TrialMeasurementError("unsupported evidence schema or runner version")
    if record["operation_key"] != OPERATION_KEY:
        raise TrialMeasurementError("evidence operation key is not supported")
    trace_id = record["trace_id"]
    if trace_id not in _TRACE_SPECS:
        raise TrialMeasurementError("evidence trace is not frozen")
    identity = record["identity"]
    if not isinstance(identity, Mapping):
        raise TrialMeasurementError("identity must be an object")
    _closed(
        identity,
        {
            "run_id",
            "trial_id",
            "worktree_fingerprint",
            "governed_project_id",
            "task_package_fingerprint",
            "rule_fingerprint",
            "capability_fingerprint",
            "runner_fingerprint",
        },
        "identity",
    )
    _text(identity["run_id"], "run_id")
    _text(identity["trial_id"], "trial_id")
    _text(identity["governed_project_id"], "governed_project_id")
    for field in (
        "worktree_fingerprint",
        "task_package_fingerprint",
        "rule_fingerprint",
        "capability_fingerprint",
        "runner_fingerprint",
    ):
        _sha(identity[field], field)
    inputs = record["inputs"]
    if not isinstance(inputs, list) or not inputs:
        raise TrialMeasurementError("inputs must be a non-empty array")
    for receipt in inputs:
        if not isinstance(receipt, Mapping):
            raise TrialMeasurementError("input receipt must be an object")
        _closed(
            receipt,
            {
                "kind",
                "status",
                "locator",
                "source_range",
                "fingerprint",
                "unavailable_reason",
                "length",
                "hash_subject",
            },
            "input receipt",
        )
        input_receipt(**receipt)
    events = record["events"]
    if not isinstance(events, list) or not events:
        raise TrialMeasurementError("events must be a non-empty array")
    names: list[str] = []
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise TrialMeasurementError("event must be an object")
        _closed(event, {"sequence", "name", "call_index", "response_bytes", "duration_ms"}, "event")
        if event["sequence"] != index:
            raise TrialMeasurementError("event sequence is missing, duplicated, or out of order")
        trace_event(**event)
        names.append(event["name"])
    expected_events = _TRACE_SPECS[trace_id]["events"]
    if tuple(names) != expected_events[: len(names)]:
        raise TrialMeasurementError("event sequence does not match the frozen trace or a valid prefix")
    for field in ("helper_calls", "repairs"):
        if type(record[field]) is not int or record[field] < 0:
            raise TrialMeasurementError(f"{field} must be a non-negative integer")
    spec = _TRACE_SPECS[trace_id]
    if record["helper_calls"] > spec["calls"] or record["repairs"] > spec["repairs"]:
        raise TrialMeasurementError("call or repair count crossed the frozen trace boundary")
    external = record["external_state"]
    if not isinstance(external, Mapping):
        raise TrialMeasurementError("external_state must be an object")
    _closed(external, {"helper_outcome", "stale", "change_count", "source_locator", "source_range"}, "external_state")
    if external["helper_outcome"] not in {"ok", "rejected", "timeout", "not_observed"}:
        raise TrialMeasurementError("external helper outcome is not allowed")
    if external["stale"] is not None and type(external["stale"]) is not bool:
        raise TrialMeasurementError("external stale must be boolean or null")
    if type(external["change_count"]) is not int or external["change_count"] < 0:
        raise TrialMeasurementError("external change_count must be a non-negative integer")
    if external["source_locator"] is not None:
        _text(external["source_locator"], "source locator")
    if external["source_range"] is not None:
        _text(external["source_range"], "source range")
    verification = record["verification"]
    if not isinstance(verification, Mapping):
        raise TrialMeasurementError("verification must be an object")
    _closed(verification, {"readback", "integrity", "boundary_match", "external_evidence"}, "verification")
    if any(type(value) is not bool for value in verification.values()):
        raise TrialMeasurementError("verification values must be booleans")
    fault = record["fault"]
    if not isinstance(fault, Mapping):
        raise TrialMeasurementError("fault must be an object")
    _closed(fault, {"origin", "operation_key", "deadline_seconds", "deadline_source", "evidence_kind"}, "fault")
    if fault["origin"] != spec["origin"] or fault["origin"] not in {"real_helper", "synthetic_harness"}:
        raise TrialMeasurementError("fault origin does not match the frozen trace")
    if fault["operation_key"] != OPERATION_KEY:
        raise TrialMeasurementError("fault operation key is not supported")
    if fault["deadline_seconds"] is not None and (
        type(fault["deadline_seconds"]) not in (int, float) or fault["deadline_seconds"] < 0
    ):
        raise TrialMeasurementError("fault deadline_seconds must be a non-negative number or null")
    if fault["deadline_source"] is not None:
        _text(fault["deadline_source"], "fault deadline_source")
    if fault["evidence_kind"] not in _FAULT_EVIDENCE_KINDS:
        raise TrialMeasurementError("fault evidence_kind is not in the frozen closed set")
    if trace_id == "T3a" and fault["evidence_kind"] != "rejected_response":
        raise TrialMeasurementError("T3a requires rejected_response evidence")
    if trace_id == "T3b" and fault["evidence_kind"] != "deadline":
        raise TrialMeasurementError("T3b requires deadline evidence")
    if trace_id == "T4a" and fault["evidence_kind"] != "interruption":
        raise TrialMeasurementError("T4a requires interruption evidence")
    if trace_id == "T4b" and fault["evidence_kind"] != "integrity_violation":
        raise TrialMeasurementError("T4b requires integrity_violation evidence")
    if trace_id in {"T1", "T2"} and fault["evidence_kind"] != "process_exit":
        raise TrialMeasurementError("successful real traces require process_exit evidence")
    if trace_id == "T3b":
        if fault["deadline_seconds"] is None or fault["deadline_source"] is None:
            raise TrialMeasurementError("deadline evidence requires deadline_seconds and deadline_source")
    elif fault["deadline_seconds"] is not None or fault["deadline_source"] is not None:
        raise TrialMeasurementError("deadline fields are only allowed for deadline evidence")


def project_record(
    record: Mapping[str, Any],
    *,
    expected_identity: EvidenceIdentity | None = None,
) -> Projection:
    """Project a record, treating every unavailable or invalid boundary as inconclusive."""

    try:
        validate_record(record)
        if expected_identity is not None and record["identity"] != expected_identity.to_json():
            return "inconclusive"
        if any(receipt["status"] != "delivered" for receipt in record["inputs"]):
            return "inconclusive"
        spec = _TRACE_SPECS[record["trace_id"]]
        if tuple(event["name"] for event in record["events"]) != spec["events"]:
            return "inconclusive"
        if record["helper_calls"] != spec["calls"] or record["repairs"] != spec["repairs"]:
            return "inconclusive"
        external = record["external_state"]
        if external["helper_outcome"] != spec["helper_outcome"] or external["stale"] is not spec["stale"]:
            return "inconclusive"
        if not all(record["verification"].values()):
            return "inconclusive"
        if external["change_count"] != 0:
            return "inconclusive"
        projection = spec["projection"]
        if projection not in _PROJECTIONS:
            return "inconclusive"
        return projection
    except (KeyError, TypeError, TrialMeasurementError):
        return "inconclusive"


def persist_record(root: SafeTrialTempRoot, relative_path: str, record: Mapping[str, Any]) -> Path:
    """Persist an integrity envelope in the identity-bound temporary root."""

    validate_record(record)
    envelope = {
        "envelope_version": EVIDENCE_SCHEMA_VERSION,
        "record": dict(record),
        "integrity_sha256": _digest(record),
    }
    return root.write_json(relative_path, envelope)


def recover_record(
    root: SafeTrialTempRoot,
    relative_path: str,
    *,
    expected_identity: EvidenceIdentity,
) -> tuple[Projection, dict[str, Any] | None]:
    """Read and verify a persisted record without repairing it in place."""

    try:
        envelope = root.read_json(relative_path)
        _closed(envelope, {"envelope_version", "record", "integrity_sha256"}, "evidence envelope")
        if envelope["envelope_version"] != EVIDENCE_SCHEMA_VERSION:
            return "inconclusive", None
        record = envelope["record"]
        if not isinstance(record, dict):
            return "inconclusive", None
        observed = _digest(record)
        expected = _sha(envelope["integrity_sha256"], "integrity_sha256")
        if not hmac.compare_digest(observed, expected):
            return "inconclusive", None
        projection = project_record(record, expected_identity=expected_identity)
        return projection, record if projection != "inconclusive" else None
    except (OSError, TrialMeasurementError):
        return "inconclusive", None


def summarize(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return protocol-layer counts only; it makes no product or health claim."""

    projections = {name: 0 for name in sorted(_PROJECTIONS)}
    calls = repairs = response_bytes = duration_ms = 0
    for record in records:
        projection = project_record(record)
        projections[projection] += 1
        if projection == "inconclusive":
            continue
        calls += record["helper_calls"]
        repairs += record["repairs"]
        response_bytes += sum(event["response_bytes"] or 0 for event in record["events"])
        duration_ms += sum(event["duration_ms"] or 0 for event in record["events"])
    return {
        "record_count": len(records),
        "projection_counts": projections,
        "helper_calls": calls,
        "repairs": repairs,
        "response_bytes": response_bytes,
        "duration_ms": duration_ms,
        "claim_boundary": (
            "protocol observations only; no correctness, health, completion, acceptance, "
            "or product-benefit claim"
        ),
    }
