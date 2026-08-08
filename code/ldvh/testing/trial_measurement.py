"""Fail-closed measurement primitives for synthetic trial tests.

This module deliberately does not know how to run a Helper task.  It records
events supplied by a test runner, validates the resulting record, and protects
its temporary output boundary.  A future experiment must build on this record
rather than reconstructing metrics from prose or terminal output.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import stat
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TRIAL_SCHEMA_VERSION = "ldvh-trial-measurement/2"
FROZEN_PROTOCOL_SCHEMA_VERSION = "ldvh-frozen-trial-protocol/1"
_CALL_CATEGORIES = frozenset({"discovery", "target", "repair"})
_OUTCOMES = frozenset({"success", "failure", "timeout"})
_CONTRACT_IDENTIFIER = re.compile(r"\b[a-zA-Z][a-zA-Z0-9]*(?:[_-][a-zA-Z0-9]+)+\b")
_BRACED_IDENTIFIER = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*")


class TrialMeasurementError(ValueError):
    """A trial record or output boundary is not trustworthy."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _nonempty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TrialMeasurementError(f"{field_name} must be a non-empty string")
    return value


def _nonnegative_int(value: object, field_name: str, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or value < 0:
        raise TrialMeasurementError(f"{field_name} must be a non-negative integer")
    return value


def _nullable_bool(value: object, field_name: str) -> bool | None:
    if value is None:
        return None
    if type(value) is not bool:
        raise TrialMeasurementError(f"{field_name} must be a boolean or null")
    return value


def validate_trial_record(record: Mapping[str, Any]) -> None:
    """Validate the versioned, closed JSON trial-record schema.

    Records are intentionally complete for every terminal outcome.  Metrics
    that cannot be observed are represented by ``null`` plus a reason; they
    must never be replaced with a convenient zero.
    """

    required = {
        "schema_version",
        "trial_id",
        "task_id",
        "task_package_hash",
        "condition",
        "runner_fingerprint",
        "runner_identity",
        "worker_envelope_sha256",
        "schema_fingerprint",
        "rule_fingerprint",
        "capability_fingerprint",
        "outcome",
        "correct",
        "first_legal",
        "discovery_calls",
        "target_calls",
        "repair_calls",
        "total_calls",
        "extra_calls",
        "invalid_requests",
        "response_bytes",
        "transcript_sha256",
        "estimated_tokens",
        "duration_seconds",
        "timed_out",
        "failure",
        "unavailable_reason",
    }
    actual = set(record)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        raise TrialMeasurementError(f"record fields must be closed; missing={missing}, extra={extra}")
    if record["schema_version"] != TRIAL_SCHEMA_VERSION:
        raise TrialMeasurementError("unrecognized trial schema version")
    for field_name in (
        "trial_id",
        "task_id",
        "task_package_hash",
        "condition",
        "runner_fingerprint",
        "runner_identity",
        "worker_envelope_sha256",
        "schema_fingerprint",
        "rule_fingerprint",
        "capability_fingerprint",
        "transcript_sha256",
    ):
        _nonempty_string(record[field_name], field_name)
    if len(record["transcript_sha256"]) != 64 or any(
        character not in "0123456789abcdef" for character in record["transcript_sha256"]
    ):
        raise TrialMeasurementError("transcript_sha256 must be a lowercase SHA-256")
    if len(record["worker_envelope_sha256"]) != 64 or any(
        character not in "0123456789abcdef" for character in record["worker_envelope_sha256"]
    ):
        raise TrialMeasurementError("worker_envelope_sha256 must be a lowercase SHA-256")
    if record["condition"] not in {"baseline", "candidate"}:
        raise TrialMeasurementError("condition must be baseline or candidate")
    if record["outcome"] not in _OUTCOMES:
        raise TrialMeasurementError("outcome must be success, failure, or timeout")
    _nullable_bool(record["correct"], "correct")
    _nullable_bool(record["first_legal"], "first_legal")
    for field_name in (
        "discovery_calls",
        "target_calls",
        "repair_calls",
        "total_calls",
        "extra_calls",
        "invalid_requests",
        "response_bytes",
    ):
        _nonnegative_int(record[field_name], field_name)
    if record["total_calls"] != record["discovery_calls"] + record["target_calls"] + record["repair_calls"]:
        raise TrialMeasurementError("total_calls must equal the classified call count")
    _nonnegative_int(record["estimated_tokens"], "estimated_tokens", nullable=True)
    if record["estimated_tokens"] is None and record["unavailable_reason"] is None:
        raise TrialMeasurementError("unavailable token data requires unavailable_reason")
    if record["estimated_tokens"] is not None and record["unavailable_reason"] is not None:
        raise TrialMeasurementError("unavailable_reason is only allowed when a metric is unavailable")
    if type(record["duration_seconds"]) not in (int, float) or record["duration_seconds"] < 0:
        raise TrialMeasurementError("duration_seconds must be a non-negative number")
    if type(record["timed_out"]) is not bool or record["timed_out"] != (record["outcome"] == "timeout"):
        raise TrialMeasurementError("timed_out must exactly match timeout outcome")
    failure = record["failure"]
    if record["outcome"] == "success":
        if failure is not None:
            raise TrialMeasurementError("successful records cannot contain failure")
    elif not isinstance(failure, str) or not failure:
        raise TrialMeasurementError("failed and timeout records require failure")


def parse_trial_record(raw: str | bytes) -> dict[str, Any]:
    """Parse an externally supplied record and fail closed on malformed JSON."""

    try:
        parsed = json.loads(raw)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TrialMeasurementError("trial record is not valid JSON") from error
    if not isinstance(parsed, dict):
        raise TrialMeasurementError("trial record must be a JSON object")
    validate_trial_record(parsed)
    return parsed


@dataclass(frozen=True, slots=True)
class HelperResponseEvent:
    """One raw Helper response observed by a synthetic runner."""

    category: str
    raw_response: str | bytes
    legal: bool
    raw_request: str | bytes | None = None

    def byte_count(self) -> int:
        if self.category not in _CALL_CATEGORIES:
            raise TrialMeasurementError("response category is not recognized")
        if type(self.legal) is not bool:
            raise TrialMeasurementError("legal must be a boolean")
        if isinstance(self.raw_response, str):
            response_bytes = len(self.raw_response.encode("utf-8"))
        elif isinstance(self.raw_response, bytes):
            response_bytes = len(self.raw_response)
        else:
            raise TrialMeasurementError("raw_response must be bytes or text")
        if self.raw_request is not None and not isinstance(self.raw_request, (bytes, str)):
            raise TrialMeasurementError("raw_request must be bytes, text, or null")
        return response_bytes


def _raw_bytes(value: str | bytes) -> bytes:
    return value.encode("utf-8") if isinstance(value, str) else value


def _event_transcript_chunks(event: HelperResponseEvent) -> tuple[bytes, ...]:
    """Canonical transcript material for one runner-observed invocation."""

    event.byte_count()
    request = b"" if event.raw_request is None else _raw_bytes(event.raw_request)
    response = _raw_bytes(event.raw_response)
    return (
        event.category.encode("ascii"), b"\0", b"1" if event.legal else b"0", b"\0",
        str(len(request)).encode("ascii"), b"\0", request, b"\0",
        str(len(response)).encode("ascii"), b"\0", response, b"\0",
    )


@dataclass(slots=True)
class TrialMeasurementCollector:
    """Collect metrics from raw events without performing Helper calls."""

    trial_id: str
    task_id: str
    task_package_hash: str
    condition: str
    runner_fingerprint: str
    runner_identity: str
    worker_envelope_sha256: str
    rule_fingerprint: str
    capability_fingerprint: str
    expected_calls: int = 1
    _started_monotonic: float = field(default_factory=time.monotonic)
    _calls: dict[str, int] = field(default_factory=lambda: {category: 0 for category in _CALL_CATEGORIES})
    _invalid_requests: int = 0
    _response_bytes: int = 0
    _first_legal: bool | None = None
    _transcript_chunks: list[bytes] = field(default_factory=list)

    def observe(self, event: HelperResponseEvent) -> None:
        """Capture a raw response regardless of whether the call was legal."""

        byte_count = event.byte_count()
        self._calls[event.category] += 1
        self._response_bytes += byte_count
        self._transcript_chunks.extend(_event_transcript_chunks(event))
        if event.category == "target" and self._first_legal is None:
            self._first_legal = event.legal
        if not event.legal:
            self._invalid_requests += 1

    def finalize(
        self,
        *,
        outcome: str,
        correct: bool | None,
        failure: str | None = None,
        estimated_tokens: int | None = None,
        unavailable_reason: str | None = None,
    ) -> dict[str, Any]:
        if outcome not in _OUTCOMES:
            raise TrialMeasurementError("outcome must be success, failure, or timeout")
        _nonnegative_int(self.expected_calls, "expected_calls")
        total_calls = sum(self._calls.values())
        record: dict[str, Any] = {
            "schema_version": TRIAL_SCHEMA_VERSION,
            "trial_id": self.trial_id,
            "task_id": self.task_id,
            "task_package_hash": self.task_package_hash,
            "condition": self.condition,
            "runner_fingerprint": self.runner_fingerprint,
            "runner_identity": self.runner_identity,
            "worker_envelope_sha256": self.worker_envelope_sha256,
            "schema_fingerprint": _sha256_text(TRIAL_SCHEMA_VERSION),
            "rule_fingerprint": self.rule_fingerprint,
            "capability_fingerprint": self.capability_fingerprint,
            "outcome": outcome,
            "correct": correct,
            "first_legal": self._first_legal,
            "discovery_calls": self._calls["discovery"],
            "target_calls": self._calls["target"],
            "repair_calls": self._calls["repair"],
            "total_calls": total_calls,
            "extra_calls": max(total_calls - self.expected_calls, 0),
            "invalid_requests": self._invalid_requests,
            "response_bytes": self._response_bytes,
            "transcript_sha256": _sha256_bytes(b"".join(self._transcript_chunks)),
            "estimated_tokens": estimated_tokens,
            "duration_seconds": time.monotonic() - self._started_monotonic,
            "timed_out": outcome == "timeout",
            "failure": failure,
            "unavailable_reason": unavailable_reason,
        }
        validate_trial_record(record)
        return record


@dataclass(frozen=True, slots=True)
class FrozenTrialTask:
    """One condition-blind task and its evaluator-only gold rubric."""

    task_id: str
    prompt: str
    gold_rubric: Mapping[str, Any]


def _iter_strings(value: object) -> Sequence[str]:
    """Return every string-bearing part of a condition-blind task material."""

    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        strings: list[str] = []
        for key, nested in value.items():
            if isinstance(key, str):
                strings.append(key)
            strings.extend(_iter_strings(nested))
        return tuple(strings)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        strings = []
        for nested in value:
            strings.extend(_iter_strings(nested))
        return tuple(strings)
    return ()


def _protected_contract_terms(candidate_card: Mapping[str, Any]) -> tuple[str, ...]:
    """Derive terms that only the candidate card may disclose to a runner.

    The extractor intentionally protects operation-style identifiers (for
    example ``find-fact-object-candidates`` and ``text_match``) plus any
    identifiers written inside an explicit request shape such as
    ``{text, field_paths}``.  It is conservative: an ambiguous term blocks a
    protocol rather than allowing a comparison whose intervention is unclear.
    """

    claims = candidate_card.get("claims")
    if not isinstance(claims, list) or not claims:
        raise TrialMeasurementError("candidate card must contain verified claims")
    protected: set[str] = set()
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise TrialMeasurementError("candidate card claim must be an object")
        statement = _nonempty_string(claim.get("statement"), "candidate card claim statement")
        protected.update(match.group(0) for match in _CONTRACT_IDENTIFIER.finditer(statement))
        for braced in re.findall(r"\{([^{}]+)\}", statement):
            protected.update(_BRACED_IDENTIFIER.findall(braced))
    if not protected:
        raise TrialMeasurementError("candidate card does not expose a protectable contract term")
    return tuple(sorted(protected, key=str.casefold))


def verify_nonleakage_protocol(
    *,
    tasks: Sequence[FrozenTrialTask],
    baseline_prompt: str,
    candidate_base_prompt: str,
    candidate_card: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed unless the card is the sole contract-discovery intervention."""

    _nonempty_string(baseline_prompt, "baseline_prompt")
    _nonempty_string(candidate_base_prompt, "candidate_base_prompt")
    if candidate_base_prompt != baseline_prompt:
        raise TrialMeasurementError("baseline and candidate base prompts must be identical")

    protected_terms = _protected_contract_terms(candidate_card)
    common_material: list[tuple[str, str]] = [("baseline prompt", baseline_prompt)]
    for task in tasks:
        common_material.append((f"task {task.task_id} prompt", task.prompt))
        common_material.extend(
            (f"task {task.task_id} gold", text) for text in _iter_strings(task.gold_rubric)
        )
    for location, text in common_material:
        lowered = text.casefold()
        for term in protected_terms:
            if term.casefold() in lowered:
                raise TrialMeasurementError(
                    f"non-candidate material leaks protected contract term {term!r} in {location}"
                )
    for task in tasks:
        gold_text = "\n".join(_iter_strings(task.gold_rubric)).casefold()
        if "baseline" in gold_text or "candidate" in gold_text:
            raise TrialMeasurementError("gold rubric must remain condition-blind")
    return {
        "status": "passed",
        "protected_terms": list(protected_terms),
        "candidate_base_prompt_hash": _sha256_text(candidate_base_prompt),
        "baseline_prompt_hash": _sha256_text(baseline_prompt),
    }


@dataclass(frozen=True, slots=True)
class FrozenTrialProtocol:
    """Protocol material written before any trial is allowed to start."""

    root: SafeTrialTempRoot
    task_package_hash: str
    baseline_prompt_hash: str
    candidate_card_fingerprint: str
    protocol_path: Path
    worker_envelopes: Mapping[tuple[str, str], WorkerEnvelope]
    candidate_claims: tuple[ContractClaim, ...]


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def freeze_trial_protocol(
    *,
    repository_root: Path,
    tasks: Sequence[FrozenTrialTask],
    baseline_prompt: str,
    candidate_base_prompt: str | None = None,
    candidate_claims: Sequence[ContractClaim],
    read_current_source: Callable[[str], str],
    allowed_operations: Sequence[str],
    environment_metadata: Mapping[str, str],
    environment_fingerprints: Mapping[str, str],
    seed: int,
    prefix: str = "ldvh-wc0071-",
) -> FrozenTrialProtocol:
    """Freeze the complete comparison input in a newly-created safe temp root.

    The task prompt deliberately excludes the gold rubric.  The returned root
    is the sole place this helper may materialize protocol, cards, transcripts,
    records, analysis input, and the before/after scope manifest.
    """

    if len(tasks) != 12:
        raise TrialMeasurementError("the frozen protocol requires exactly twelve tasks")
    _nonempty_string(baseline_prompt, "baseline_prompt")
    if type(seed) is not int:
        raise TrialMeasurementError("seed must be an integer")
    operation_set = sorted(set(allowed_operations))
    if not operation_set or any(not isinstance(operation, str) or not operation for operation in operation_set):
        raise TrialMeasurementError("allowed_operations must contain non-empty operation names")
    if not environment_metadata or any(
        not isinstance(key, str) or not key or not isinstance(value, str) or not value
        for key, value in environment_metadata.items()
    ):
        raise TrialMeasurementError("environment_metadata must be a non-empty string mapping")
    if not environment_fingerprints or any(
        not isinstance(key, str) or not key or not isinstance(value, str) or not value
        for key, value in environment_fingerprints.items()
    ):
        raise TrialMeasurementError("environment_fingerprints must be a non-empty string mapping")

    task_ids: set[str] = set()
    package_tasks: list[dict[str, str]] = []
    gold: dict[str, Mapping[str, Any]] = {}
    for task in tasks:
        _nonempty_string(task.task_id, "task.task_id")
        _nonempty_string(task.prompt, "task.prompt")
        if task.task_id in task_ids:
            raise TrialMeasurementError("task ids must be unique")
        if not isinstance(task.gold_rubric, Mapping) or not task.gold_rubric:
            raise TrialMeasurementError("task.gold_rubric must be a non-empty mapping")
        task_ids.add(task.task_id)
        package_tasks.append({"task_id": task.task_id, "prompt": task.prompt})
        gold[task.task_id] = dict(task.gold_rubric)

    package_tasks.sort(key=lambda task: task["task_id"])
    task_package_hash = _sha256_bytes(_canonical_json_bytes(package_tasks))
    candidate_card = build_prompt_card(candidate_claims, read_current_source=read_current_source)
    preflight = verify_nonleakage_protocol(
        tasks=tasks,
        baseline_prompt=baseline_prompt,
        candidate_base_prompt=baseline_prompt if candidate_base_prompt is None else candidate_base_prompt,
        candidate_card=candidate_card,
    )
    root = SafeTrialTempRoot.create(prefix=prefix, repository_root=repository_root)
    worker_envelopes = {
        (task["task_id"], condition): _worker_envelope(
            task_id=task["task_id"],
            condition=condition,
            baseline_prompt=baseline_prompt,
            task_prompt=task["prompt"],
            candidate_card=candidate_card,
        )
        for task in package_tasks
        for condition in ("baseline", "candidate")
    }
    root.write_json("protocol/tasks.json", {"tasks": package_tasks, "task_package_hash": task_package_hash})
    root.write_json("protocol/gold.json", {"gold": gold})
    root.write_json(
        "protocol/baseline.json",
        {"prompt": baseline_prompt, "prompt_sha256": _sha256_text(baseline_prompt)},
    )
    root.write_json("protocol/candidate-card.json", candidate_card)
    trial_order = [
        {"task_id": task["task_id"], "condition": condition}
        for task in package_tasks
        for condition in ("baseline", "candidate")
    ]
    random.Random(seed).shuffle(trial_order)
    protocol = {
        "schema_version": FROZEN_PROTOCOL_SCHEMA_VERSION,
        "task_count": len(package_tasks),
        "conditions": ["baseline", "candidate"],
        "task_package_hash": task_package_hash,
        "baseline_prompt_hash": _sha256_text(baseline_prompt),
        "candidate_card_fingerprint": candidate_card["card_fingerprint"],
        "preflight": preflight,
        "worker_envelopes": [
            {
                "task_id": envelope.task_id,
                "condition": envelope.condition,
                "envelope_sha256": envelope.envelope_sha256,
            }
            for _, envelope in sorted(worker_envelopes.items())
        ],
        "allowed_operations": operation_set,
        "environment_metadata": dict(sorted(environment_metadata.items())),
        "environment_fingerprints": dict(sorted(environment_fingerprints.items())),
        "seed": seed,
        "trial_order": trial_order,
        "primary_measure": {
            "name": "paired_first_legal_delta",
            "definition": "candidate first_legal count minus baseline first_legal count across paired tasks",
            "directional_signal_threshold": 1,
            "guardrail": "all compared correct values are true and candidate terminal failures do not exceed baseline",
            "missing_or_timeout": "no directional signal; retain only descriptive counts",
        },
        "claims": {
            "not_made": [
                "statistical significance",
                "causal proof",
                "product net benefit",
            ]
        },
    }
    protocol_path = root.write_json("protocol/frozen-protocol.json", protocol)
    root.write_json("scope/before.json", {"repository_root": str(repository_root.resolve()), "changed_paths": []})
    return FrozenTrialProtocol(
        root=root,
        task_package_hash=task_package_hash,
        baseline_prompt_hash=_sha256_text(baseline_prompt),
        candidate_card_fingerprint=candidate_card["card_fingerprint"],
        protocol_path=protocol_path,
        worker_envelopes=worker_envelopes,
        candidate_claims=tuple(candidate_claims),
    )


def persist_trial_artifacts(
    protocol: FrozenTrialProtocol,
    *,
    record: Mapping[str, Any],
    transcript: Sequence[HelperResponseEvent],
) -> tuple[Path, Path]:
    """Persist one validated record and its hash-bound raw response transcript."""

    validate_trial_record(record)
    try:
        expected_envelope = protocol.worker_envelopes[(record["task_id"], record["condition"])]
    except KeyError as error:
        raise TrialMeasurementError("record task and condition have no frozen worker envelope") from error
    if record["worker_envelope_sha256"] != expected_envelope.envelope_sha256:
        raise TrialMeasurementError("record envelope hash does not match frozen task and condition")
    expected_runner_fingerprint = _sha256_text(
        f"{record['runner_identity']}\0{record['worker_envelope_sha256']}"
    )
    if record["runner_fingerprint"] != expected_runner_fingerprint:
        raise TrialMeasurementError("record runner fingerprint does not bind its envelope and runner identity")
    encoded_events: list[dict[str, Any]] = []
    chunks: list[bytes] = []
    for event in transcript:
        event.byte_count()
        response = _raw_bytes(event.raw_response)
        request = None if event.raw_request is None else _raw_bytes(event.raw_request)
        encoded_events.append(
            {
                "category": event.category,
                "legal": event.legal,
                "raw_request_utf8": None if request is None else request.decode("utf-8", errors="strict"),
                "raw_response_utf8": response.decode("utf-8", errors="strict"),
            }
        )
        chunks.extend(_event_transcript_chunks(event))
    if record["transcript_sha256"] != _sha256_bytes(b"".join(chunks)):
        raise TrialMeasurementError("record transcript hash does not match supplied raw transcript")
    trial_id = _nonempty_string(record["trial_id"], "trial_id")
    transcript_path = protocol.root.write_json(f"transcripts/{trial_id}.json", {"events": encoded_events})
    record_path = protocol.root.write_json(f"records/{trial_id}.json", dict(record))
    return record_path, transcript_path


@dataclass(frozen=True, slots=True)
class ContractClaim:
    """An exact prompt-card statement tied to a currently read contract source."""

    statement: str
    source_ref: str
    source_fingerprint: str


def build_prompt_card(
    claims: Sequence[ContractClaim],
    *,
    read_current_source: Callable[[str], str],
) -> dict[str, Any]:
    """Read current sources to build a card, rejecting unverified assertions.

    Claims are exact excerpts rather than model-authored paraphrases.  This is
    intentionally conservative: a caller must obtain current capability or
    specification content through its approved reader and cannot attach a
    stale, unrelated, or invented statement to a valid-looking fingerprint.
    """

    if not claims:
        raise TrialMeasurementError("a prompt card requires at least one verified claim")
    rendered: list[dict[str, str]] = []
    seen: set[str] = set()
    for claim in claims:
        _nonempty_string(claim.statement, "claim.statement")
        _nonempty_string(claim.source_ref, "claim.source_ref")
        source_text = read_current_source(claim.source_ref)
        _nonempty_string(source_text, "current source text")
        if claim.source_fingerprint != _sha256_text(source_text):
            raise TrialMeasurementError("claim source fingerprint does not match current source text")
        if claim.statement not in source_text:
            raise TrialMeasurementError("claim statement is not supported by current source text")
        if claim.statement in seen:
            raise TrialMeasurementError("prompt card claims must be unique")
        seen.add(claim.statement)
        rendered.append(
            {
                "statement": claim.statement,
                "source_ref": claim.source_ref,
                "source_fingerprint": claim.source_fingerprint,
            }
        )
    card_payload = json.dumps(rendered, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"claims": rendered, "card_fingerprint": _sha256_text(card_payload)}


@dataclass(frozen=True, slots=True)
class WorkerEnvelope:
    """The only immutable material a condition worker may receive."""

    task_id: str
    condition: str
    payload: Mapping[str, Any]
    envelope_sha256: str


def _worker_envelope(
    *,
    task_id: str,
    condition: str,
    baseline_prompt: str,
    task_prompt: str,
    candidate_card: Mapping[str, Any],
) -> WorkerEnvelope:
    payload: dict[str, Any] = {
        "task_id": task_id,
        "condition": condition,
        "instructions": baseline_prompt,
        "task": task_prompt,
    }
    if condition == "candidate":
        payload["candidate_card"] = dict(candidate_card)
    elif condition != "baseline":
        raise TrialMeasurementError("worker envelope condition is not recognized")
    return WorkerEnvelope(
        task_id=task_id,
        condition=condition,
        payload=payload,
        envelope_sha256=_sha256_bytes(_canonical_json_bytes(payload)),
    )


def _response_is_legal(raw_response: bytes) -> bool:
    """Derive request legality from the actual Helper response envelope."""

    try:
        decoded = json.loads(raw_response)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(decoded, Mapping):
        return False
    return decoded.get("outcome") not in {"invalid_request", "rejected", "error"}


@dataclass(slots=True)
class RunnerOwnedTrialSession:
    """One runner-owned session; workers cannot supply metric classifications."""

    adapter: RunnerOwnedTrialAdapter
    envelope: WorkerEnvelope
    collector: TrialMeasurementCollector
    transcript: list[HelperResponseEvent] = field(default_factory=list)

    def invoke(
        self,
        operation: str,
        request: str | bytes,
        *,
        dispatch: Callable[[str, bytes], str | bytes],
    ) -> bytes:
        """Dispatch one allowed operation and record actual request/response bytes."""

        if operation not in self.adapter.allowed_operations:
            raise TrialMeasurementError("operation is outside the frozen read-only allowlist")
        request_bytes = _raw_bytes(request)
        response = dispatch(operation, request_bytes)
        if not isinstance(response, (bytes, str)):
            raise TrialMeasurementError("runner dispatch must return actual response bytes or text")
        response_bytes = _raw_bytes(response)
        event = HelperResponseEvent(
            category=self.adapter.operation_categories[operation],
            raw_response=response_bytes,
            legal=_response_is_legal(response_bytes),
            raw_request=request_bytes,
        )
        self.collector.observe(event)
        self.transcript.append(event)
        return response_bytes

    def finalize(self, **terminal: Any) -> tuple[dict[str, Any], tuple[HelperResponseEvent, ...]]:
        """Return a strict record plus the exact runner-owned transcript."""

        return self.collector.finalize(**terminal), tuple(self.transcript)


@dataclass(frozen=True, slots=True)
class RunnerOwnedTrialAdapter:
    """Create isolated envelopes and collect only runner-observed Helper calls."""

    protocol: FrozenTrialProtocol
    read_current_source: Callable[[str], str]
    operation_categories: Mapping[str, str]
    runner_identity: str
    environment_readers: Mapping[str, Callable[[], bytes]]

    def __post_init__(self) -> None:
        _nonempty_string(self.runner_identity, "runner_identity")
        if set(self.operation_categories) != set(self.allowed_operations):
            raise TrialMeasurementError("runner categories must cover exactly the frozen allowlist")
        if any(category not in _CALL_CATEGORIES for category in self.operation_categories.values()):
            raise TrialMeasurementError("runner category is not recognized")
        frozen_fingerprints = self._environment_fingerprints()
        if set(self.environment_readers) != set(frozen_fingerprints):
            raise TrialMeasurementError("environment readers must cover exactly the frozen fingerprint set")

    @property
    def allowed_operations(self) -> tuple[str, ...]:
        payload = json.loads(self.protocol.protocol_path.read_text(encoding="utf-8"))
        operations = payload.get("allowed_operations")
        if not isinstance(operations, list) or any(not isinstance(value, str) for value in operations):
            raise TrialMeasurementError("frozen protocol allowlist is malformed")
        return tuple(operations)

    def _assert_source_current(self) -> None:
        # Rebuild from the original immutable claims at every runner boundary.
        build_prompt_card(self.protocol.candidate_claims, read_current_source=self.read_current_source)

    def _environment_fingerprints(self) -> Mapping[str, str]:
        payload = json.loads(self.protocol.protocol_path.read_text(encoding="utf-8"))
        fingerprints = payload.get("environment_fingerprints")
        if not isinstance(fingerprints, Mapping) or any(
            not isinstance(key, str) or not isinstance(value, str) for key, value in fingerprints.items()
        ):
            raise TrialMeasurementError("frozen protocol fingerprints are malformed")
        return fingerprints

    def _assert_environment_current(self) -> Mapping[str, str]:
        fingerprints = self._environment_fingerprints()
        for name, expected in fingerprints.items():
            observed = self.environment_readers[name]()
            if not isinstance(observed, bytes) or _sha256_bytes(observed) != expected:
                raise TrialMeasurementError(f"frozen environment fingerprint drifted: {name}")
        return fingerprints

    def start_trial(self, *, task_id: str, condition: str, trial_id: str) -> RunnerOwnedTrialSession:
        """Revalidate sources and return the sole permitted worker delivery package."""

        self._assert_source_current()
        fingerprints = self._assert_environment_current()
        try:
            envelope = self.protocol.worker_envelopes[(task_id, condition)]
        except KeyError as error:
            raise TrialMeasurementError("requested task/condition has no frozen worker envelope") from error
        rule_fingerprint = _nonempty_string(fingerprints.get("candidate_rule_source"), "candidate rule fingerprint")
        capability_fingerprint = _nonempty_string(fingerprints.get("capability_source"), "capability fingerprint")
        runner_fingerprint = _sha256_text(f"{self.runner_identity}\0{envelope.envelope_sha256}")
        return RunnerOwnedTrialSession(
            adapter=self,
            envelope=envelope,
            collector=TrialMeasurementCollector(
                trial_id=trial_id,
                task_id=task_id,
                task_package_hash=self.protocol.task_package_hash,
                condition=condition,
                runner_fingerprint=runner_fingerprint,
                runner_identity=self.runner_identity,
                worker_envelope_sha256=envelope.envelope_sha256,
                rule_fingerprint=rule_fingerprint,
                capability_fingerprint=capability_fingerprint,
            ),
        )


def _contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


@dataclass(slots=True)
class SafeTrialTempRoot:
    """A temporary-root writer that rejects every path escape before writing."""

    root: Path
    _identity: tuple[int, int]
    _resolved_root: Path
    _created_directories: set[Path]

    @classmethod
    def create(cls, *, prefix: str = "ldvh-trial-", repository_root: Path) -> SafeTrialTempRoot:
        root = Path(tempfile.mkdtemp(prefix=prefix))
        resolved = root.resolve(strict=True)
        if _contained(resolved, repository_root.resolve(strict=True)):
            raise TrialMeasurementError("mkdtemp root may not be inside the repository")
        info = root.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise TrialMeasurementError("mkdtemp did not create a safe directory")
        return cls(
            root=root,
            _identity=(info.st_dev, info.st_ino),
            _resolved_root=resolved,
            _created_directories={root},
        )

    def _verify_root(self) -> None:
        info = self.root.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or (info.st_dev, info.st_ino) != self._identity:
            raise TrialMeasurementError("temporary root identity changed")
        if self.root.resolve(strict=True) != self._resolved_root:
            raise TrialMeasurementError("temporary root realpath drifted")

    def _output_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if not relative_path or candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
            raise TrialMeasurementError("output path must be a non-empty, traversal-free relative path")
        return self.root.joinpath(*candidate.parts)

    def write_json(self, relative_path: str, value: Mapping[str, Any]) -> Path:
        """Create exactly one new JSON file beneath the identity-bound root."""

        self._verify_root()
        output = self._output_path(relative_path)
        parent = self.root
        for part in output.relative_to(self.root).parts[:-1]:
            parent = parent / part
            if parent.exists():
                info = parent.lstat()
                if (
                    stat.S_ISLNK(info.st_mode)
                    or not stat.S_ISDIR(info.st_mode)
                    or parent not in self._created_directories
                ):
                    raise TrialMeasurementError("output parent was not created by this runner")
            else:
                parent.mkdir()
                self._created_directories.add(parent)
            if not _contained(parent.resolve(strict=True), self._resolved_root):
                raise TrialMeasurementError("output parent escaped temporary root")
        if output.exists() or output.is_symlink():
            raise TrialMeasurementError("output path must be newly created")
        if not _contained(output.parent.resolve(strict=True), self._resolved_root):
            raise TrialMeasurementError("output realpath escaped temporary root")
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        try:
            descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            if output.is_symlink():
                output.unlink()
            raise TrialMeasurementError("output path changed before exclusive creation") from error
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            try:
                output.unlink()
            except FileNotFoundError:
                pass
            raise
        self._verify_root()
        if output.is_symlink() or not _contained(output.resolve(strict=True), self._resolved_root):
            raise TrialMeasurementError("output path changed after write")
        return output


def synthetic_trial(
    factory: Callable[[], TrialMeasurementCollector],
    events: Sequence[HelperResponseEvent],
    **terminal: Any,
) -> dict[str, Any]:
    """Small helper for synthetic tests; it never invokes a real Helper."""

    collector = factory()
    for event in events:
        collector.observe(event)
    return collector.finalize(**terminal)
