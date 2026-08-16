"""Equivalence-retrial runner and machine scoring for the rule-exact-read task family.

This module carries the WFPQDZ-continuation retrial protocol: it executes a
frozen task/variant package through one fixed execution carrier (declared model
entry, tool entry, and runner identity), records a structured machine record
per trial, passes every trial through the ``session_comparability``
comparability gate before scoring, and scores directly from machine records
rather than natural-language retelling.  Raw trial content only ever enters a
``SafeTrialTempRoot`` and is not retained long-term; only structural
fingerprints and aggregates leave the boundary, matching the governing
Spark/Study privacy stop-boundary.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ldvh.testing.evidence_protocol import (
    IdentityFingerprintSet,
    ProtocolComparability,
    extract_trial_identity,
    is_out_of_protocol,
    judge_protocol_comparability,
)
from ldvh.testing.session_comparability import (
    ComparabilityVerdict,
    audit_events,
    judge_comparability,
)
from ldvh.testing.trial_measurement import SafeTrialTempRoot, TrialMeasurementError

EQUIVALENCE_RETRIAL_VERSION = "ldvh-equivalence-retrial/1"
VARIANTS = ("full_contract", "required_removed", "irrelevant_added")
_OUTCOMES = frozenset({"success", "failure", "timeout"})


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TrialMeasurementError(f"{name} must be a non-empty string")
    return value


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _nonnegative_number(value: object, name: str) -> float:
    if type(value) not in (int, float) or value < 0:
        raise TrialMeasurementError(f"{name} must be a non-negative number")
    return float(value)


@dataclass(frozen=True, slots=True)
class CarrierDeclaration:
    """The frozen execution carrier a retrial batch must hold constant."""

    provider: str
    model: str
    runner_identity: str
    tool_entry: str

    @property
    def entry(self) -> tuple[str, str]:
        return (self.provider, self.model)

    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "provider": self.provider,
                "model": self.model,
                "runner_identity": self.runner_identity,
                "tool_entry": self.tool_entry,
            }
        )


@dataclass(frozen=True, slots=True)
class TrialEnvelope:
    """One frozen task × variant × sample package handed to the executor."""

    trial_id: str
    task_id: str
    variant: str
    condition_key: str
    sample_index: int
    task_package_hash: str
    contract_sha256: str
    carrier: CarrierDeclaration
    payload: Mapping[str, Any]
    envelope_sha256: str


@dataclass(frozen=True, slots=True)
class ExecutorResult:
    """Structured machine output of one trial execution (no prose retelling)."""

    output_sha256: str
    event_lines: tuple[str, ...]
    duration_seconds: float
    outcome: str
    failure: str | None = None


@dataclass(frozen=True, slots=True)
class TrialRecord:
    """One validated machine trial record."""

    schema_version: str
    trial_id: str
    task_id: str
    variant: str
    condition_key: str
    sample_index: int
    task_package_hash: str
    contract_sha256: str
    carrier_fingerprint: str
    carrier_entry: tuple[str, str]
    model_reason: str
    event_lines_sha256: str
    comparability: ComparabilityVerdict
    pairing_ok: bool
    outcome: str
    output_sha256: str
    duration_seconds: float
    failure: str | None = None
    protocol_identity: IdentityFingerprintSet | None = None
    protocol_verdict: ProtocolComparability | None = None
    out_of_protocol: bool = False


@dataclass(frozen=True, slots=True)
class RubricCheck:
    """One objective rubric assertion evaluated from machine fields only."""

    check_id: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class TrialAssessment:
    """Score of one trial consumed directly from its machine record."""

    trial_id: str
    status: str
    checks: tuple[RubricCheck, ...]
    assessed_sha256: str


def build_trial_envelope(
    *,
    trial_id: str,
    task_id: str,
    variant: str,
    condition_key: str,
    sample_index: int,
    task_package_hash: str,
    contract_sha256: str,
    carrier: CarrierDeclaration,
    payload: Mapping[str, Any],
) -> TrialEnvelope:
    """Construct one frozen trial envelope (payload is structural only)."""
    _nonempty_string(trial_id, "trial_id")
    _nonempty_string(task_id, "task_id")
    if variant not in VARIANTS:
        raise TrialMeasurementError(f"variant must be one of {VARIANTS}")
    _nonempty_string(condition_key, "condition_key")
    if type(sample_index) is not int or sample_index < 0:
        raise TrialMeasurementError("sample_index must be a non-negative integer")
    _nonempty_string(task_package_hash, "task_package_hash")
    _nonempty_string(contract_sha256, "contract_sha256")
    if not isinstance(payload, Mapping) or not payload:
        raise TrialMeasurementError("payload must be a non-empty mapping")
    envelope_payload = {
        "trial_id": trial_id,
        "task_id": task_id,
        "variant": variant,
        "condition_key": condition_key,
        "sample_index": sample_index,
        "task_package_hash": task_package_hash,
        "contract_sha256": contract_sha256,
        "carrier": carrier.fingerprint(),
        "payload": dict(payload),
    }
    return TrialEnvelope(
        trial_id=trial_id,
        task_id=task_id,
        variant=variant,
        condition_key=condition_key,
        sample_index=sample_index,
        task_package_hash=task_package_hash,
        contract_sha256=contract_sha256,
        carrier=carrier,
        payload=payload,
        envelope_sha256=_canonical_sha256(envelope_payload),
    )


def validate_executor_result(result: ExecutorResult) -> None:
    """Fail closed unless the executor result is structural and complete."""
    _nonempty_string(result.output_sha256, "output_sha256")
    if not isinstance(result.event_lines, tuple) or not result.event_lines:
        raise TrialMeasurementError("event_lines must be a non-empty tuple of structural lines")
    for line in result.event_lines:
        _nonempty_string(line, "event line")
    if result.outcome not in _OUTCOMES:
        raise TrialMeasurementError(f"outcome must be one of {_OUTCOMES}")
    _nonnegative_number(result.duration_seconds, "duration_seconds")
    if result.outcome != "success" and not result.failure:
        raise TrialMeasurementError("failed and timeout outcomes require failure")
    if result.outcome == "success" and result.failure is not None:
        raise TrialMeasurementError("successful outcomes cannot carry failure")


def run_trial(
    *,
    envelope: TrialEnvelope,
    executor: Callable[[TrialEnvelope], ExecutorResult],
    reference_identity: IdentityFingerprintSet | None = None,
) -> TrialRecord:
    """Execute one frozen trial and fold the comparability gate into the record.

    The comparability gate consumes the structural event lines through
    ``session_comparability``: the machine record carries the verdict and
    pairing status, so scoring can exclude ``not_comparable`` trials without
    reading any content.

    When *reference_identity* is provided, the trial records its protocol
    identity fingerprints and a ``ProtocolComparability`` verdict.  Trials
    whose identity fingerprints do not match the reference are marked
    ``out_of_protocol`` and can be excluded from scoring.
    """
    result = executor(envelope)
    validate_executor_result(result)
    fingerprint = audit_events(_parse_event_lines(result.event_lines))
    verdict = judge_comparability(fingerprint)

    # Protocol identity recording.
    trial_identity = extract_trial_identity(
        task_id=envelope.task_id,
        task_package_hash=envelope.task_package_hash,
        contract_sha256=envelope.contract_sha256,
        payload=envelope.payload,
        carrier_fingerprint=envelope.carrier.fingerprint(),
    )
    protocol_verdict = None
    out_of_protocol = False
    if reference_identity is not None:
        pc = judge_protocol_comparability(
            fingerprint,
            trial_identity=trial_identity,
            reference_identity=reference_identity,
        )
        protocol_verdict = pc
        out_of_protocol = is_out_of_protocol(pc)

    record = TrialRecord(
        schema_version=EQUIVALENCE_RETRIAL_VERSION,
        trial_id=envelope.trial_id,
        task_id=envelope.task_id,
        variant=envelope.variant,
        condition_key=envelope.condition_key,
        sample_index=envelope.sample_index,
        task_package_hash=envelope.task_package_hash,
        contract_sha256=envelope.contract_sha256,
        carrier_fingerprint=envelope.carrier.fingerprint(),
        carrier_entry=envelope.carrier.entry,
        model_reason="declared",
        event_lines_sha256=_canonical_sha256(result.event_lines),
        comparability=verdict,
        pairing_ok=fingerprint.pairing_ok,
        outcome=result.outcome,
        output_sha256=result.output_sha256,
        duration_seconds=result.duration_seconds,
        failure=result.failure,
        protocol_identity=trial_identity,
        protocol_verdict=protocol_verdict,
        out_of_protocol=out_of_protocol,
    )
    return record


def _parse_event_lines(lines: Sequence[str]) -> list[Mapping[str, Any]]:
    parsed: list[Mapping[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except (TypeError, json.JSONDecodeError) as error:
            raise TrialMeasurementError("trial event line is not valid JSON") from error
        if not isinstance(value, Mapping):
            raise TrialMeasurementError("trial event line must be a JSON object")
        parsed.append(value)
    return parsed


def assess_trial(record: TrialRecord, rubric: Mapping[str, Any]) -> TrialAssessment:
    """Score one trial directly from its machine record.

    ``rubric`` maps check ids to a predicate over the machine record.  The
    assessment is evaluated from structural fields only; content hashes are
    compared, not decoded.
    """
    if not isinstance(rubric, Mapping) or not rubric:
        raise TrialMeasurementError("rubric must be a non-empty mapping")
    checks: list[RubricCheck] = []
    for check_id, predicate in rubric.items():
        if not isinstance(check_id, str) or not check_id:
            raise TrialMeasurementError("rubric check id must be a non-empty string")
        if not callable(predicate):
            raise TrialMeasurementError("rubric predicate must be callable")
        try:
            passed = bool(predicate(record))
        except Exception as error:  # noqa: BLE001 - a broken predicate must fail closed.
            raise TrialMeasurementError(f"rubric predicate {check_id!r} failed") from error
        checks.append(RubricCheck(check_id=check_id, passed=passed, detail="machine-evaluated"))
    status = "satisfied" if all(check.passed for check in checks) else "not_satisfied"
    return TrialAssessment(
        trial_id=record.trial_id,
        status=status,
        checks=tuple(checks),
        assessed_sha256=_canonical_sha256([check.check_id for check in checks]),
    )


@dataclass(frozen=True, slots=True)
class BatchSummary:
    """Aggregate of a retrial batch; no raw content, no causal claims."""

    schema_version: str
    carrier_fingerprint: str
    carrier_entry: tuple[str, str]
    trials: int
    comparable_count: int
    not_comparable_count: int
    inconclusive_count: int
    satisfied_count: int
    not_satisfied_count: int
    verdict_counts: Mapping[str, int] = field(default_factory=dict)
    out_of_protocol_count: int = 0

    def payload(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "carrier_fingerprint": self.carrier_fingerprint,
            "carrier_entry": list(self.carrier_entry),
            "trials": self.trials,
            "comparable_count": self.comparable_count,
            "not_comparable_count": self.not_comparable_count,
            "inconclusive_count": self.inconclusive_count,
            "satisfied_count": self.satisfied_count,
            "not_satisfied_count": self.not_satisfied_count,
            "verdict_counts": dict(self.verdict_counts),
            "out_of_protocol_count": self.out_of_protocol_count,
            "claim_boundary": (
                "aggregate only; does not prove causal effect, host receipt, "
                "or overall service improvement"
            ),
        }


def summarize_batch(records: Sequence[TrialRecord], assessments: Sequence[TrialAssessment]) -> BatchSummary:
    """Fold records and assessments into a structural aggregate."""
    if len(records) != len(assessments):
        raise TrialMeasurementError("records and assessments must be aligned")
    if not records:
        raise TrialMeasurementError("batch summary requires at least one trial")
    carriers = {(record.carrier_fingerprint, record.carrier_entry) for record in records}
    if len(carriers) != 1:
        raise TrialMeasurementError("batch records must share one frozen carrier")
    carrier_fingerprint, carrier_entry = next(iter(carriers))
    verdict_counts: dict[str, int] = {}
    comparable = not_comparable = inconclusive = satisfied = not_satisfied = out_of_protocol = 0
    for record, assessment in zip(records, assessments, strict=True):
        verdict_counts[record.comparability.verdict] = verdict_counts.get(record.comparability.verdict, 0) + 1
        if record.comparability.verdict == "comparable":
            comparable += 1
        elif record.comparability.verdict == "not_comparable":
            not_comparable += 1
        else:
            inconclusive += 1
        if assessment.status == "satisfied":
            satisfied += 1
        else:
            not_satisfied += 1
        if record.out_of_protocol:
            out_of_protocol += 1
    return BatchSummary(
        schema_version=EQUIVALENCE_RETRIAL_VERSION,
        carrier_fingerprint=carrier_fingerprint,
        carrier_entry=carrier_entry,
        trials=len(records),
        comparable_count=comparable,
        not_comparable_count=not_comparable,
        inconclusive_count=inconclusive,
        satisfied_count=satisfied,
        not_satisfied_count=not_satisfied,
        verdict_counts=verdict_counts,
        out_of_protocol_count=out_of_protocol,
    )


def persist_batch_artifacts(
    root: SafeTrialTempRoot,
    *,
    records: Sequence[TrialRecord],
    assessments: Sequence[TrialAssessment],
    summary: BatchSummary,
) -> tuple[Any, ...]:
    """Persist structural aggregates beneath the identity-bound temp root."""
    record_payloads = [
        {
            "trial_id": record.trial_id,
            "task_id": record.task_id,
            "variant": record.variant,
            "condition_key": record.condition_key,
            "sample_index": record.sample_index,
            "carrier_entry": list(record.carrier_entry),
            "carrier_fingerprint": record.carrier_fingerprint,
            "comparability": record.comparability.verdict,
            "comparability_reasons": list(record.comparability.reasons),
            "pairing_ok": record.pairing_ok,
            "outcome": record.outcome,
            "output_sha256": record.output_sha256,
            "event_lines_sha256": record.event_lines_sha256,
            "duration_seconds": record.duration_seconds,
            "out_of_protocol": record.out_of_protocol,
        }
        for record in records
    ]
    assessment_payloads = [
        {"trial_id": a.trial_id, "status": a.status, "checks": [c.check_id for c in a.checks]}
        for a in assessments
    ]
    records_path = root.write_json("records/trials.json", {"records": record_payloads})
    assessments_path = root.write_json("records/assessments.json", {"assessments": assessment_payloads})
    summary_path = root.write_json("records/summary.json", summary.payload())
    return records_path, assessments_path, summary_path
