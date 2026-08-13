"""Privacy-bounded evidence contracts for rule-exact-read service trials."""

from __future__ import annotations

import hmac
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from ldvh.testing.trial_measurement import SafeTrialTempRoot, TrialMeasurementError
from ldvh.testing.working_tree_evidence import canonical_sha256

CONTRACT_VERSION = "ldvh-rule-read-context-contract/1"
AGGREGATE_VERSION = "ldvh-rule-read-context-aggregate/1"
VARIANTS = ("full_contract", "required_removed", "irrelevant_added")
EVIDENCE_LEVELS = ("LDVH prepared", "harness-delivered", "host-received", "behavior-consistent", "causal-effect")
HOST_RECEIVED_UNAVAILABLE = "unavailable"
CLAIM_BOUNDARY = (
    "This bounded method trial does not prove that the host delivered a final prompt, "
    "that the model used an input, or that overall LDVH service quality improved."
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CONTEXT_KINDS = frozenset({"required", "conditional", "excluded"})
_SENSITIVE_KEYS = frozenset(
    {
        "credential",
        "full_prompt",
        "helper_request",
        "helper_response",
        "home_path",
        "raw_chat",
        "raw_prompt",
        "raw_response",
        "repository_body",
        "rule_body",
    }
)


@dataclass(frozen=True, slots=True)
class ContextEntry:
    entry_id: str
    kind: str
    locator: str
    source_sha256: str
    applies_when: str
    allowed_alternatives: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RuleReadContextContract:
    contract_version: str
    entries: tuple[ContextEntry, ...]
    invalidation_conditions: tuple[str, ...]
    contract_sha256: str


@dataclass(frozen=True, slots=True)
class FrozenRuleReadTask:
    task_id: str
    human_goal: str
    responsibility_key: str
    heading_path: tuple[str, ...]
    disclosure: str
    source_locator: str
    source_sha256: str
    expected_outcome: str
    expected_completed_scope: tuple[tuple[str, tuple[str, ...]], ...]
    expected_part_sha256: tuple[str, ...]
    task_sha256: str


@dataclass(frozen=True, slots=True)
class BoundVariantEnvelope:
    task_sha256: str
    contract_sha256: str
    variant: str
    context_entry_ids: tuple[str, ...]
    removed_entry_id: str | None
    added_entry_id: str | None
    condition_key: str
    payload_sha256: str
    envelope_sha256: str


@dataclass(frozen=True, slots=True)
class ObjectiveAssessment:
    status: str
    checks: Mapping[str, bool]
    output_sha256: str
    reason: str | None


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TrialMeasurementError(f"{name} must be a non-empty string")
    return value


def _sha(value: object, name: str) -> str:
    text = _text(value, name)
    if not _SHA256.fullmatch(text):
        raise TrialMeasurementError(f"{name} must be a lowercase SHA-256")
    return text


def _unique(values: Sequence[str], name: str) -> tuple[str, ...]:
    projected = tuple(values)
    if not projected or len(set(projected)) != len(projected):
        raise TrialMeasurementError(f"{name} must be non-empty and unique")
    return projected


def _entry_projection(entry: ContextEntry) -> dict[str, Any]:
    return {
        "entry_id": entry.entry_id,
        "kind": entry.kind,
        "locator": entry.locator,
        "source_sha256": entry.source_sha256,
        "applies_when": entry.applies_when,
        "allowed_alternatives": list(entry.allowed_alternatives),
    }


def build_contract(
    entries: Sequence[ContextEntry],
    *,
    invalidation_conditions: Sequence[str],
) -> RuleReadContextContract:
    projected = tuple(entries)
    _unique([entry.entry_id for entry in projected], "context entry ids")
    kinds = {entry.kind for entry in projected}
    if not kinds.issubset(_CONTEXT_KINDS) or not {"required", "excluded"}.issubset(kinds):
        raise TrialMeasurementError("contract must use known kinds and contain required and excluded entries")
    for entry in projected:
        _text(entry.locator, f"{entry.entry_id}.locator")
        _sha(entry.source_sha256, f"{entry.entry_id}.source_sha256")
        _text(entry.applies_when, f"{entry.entry_id}.applies_when")
        if entry.entry_id in entry.allowed_alternatives or len(set(entry.allowed_alternatives)) != len(
            entry.allowed_alternatives
        ):
            raise TrialMeasurementError("allowed alternatives must be unique and may not self-reference")
    invalidation = _unique(tuple(invalidation_conditions), "invalidation conditions")
    payload = {
        "contract_version": CONTRACT_VERSION,
        "entries": [_entry_projection(entry) for entry in projected],
        "invalidation_conditions": list(invalidation),
    }
    return RuleReadContextContract(
        contract_version=CONTRACT_VERSION,
        entries=projected,
        invalidation_conditions=invalidation,
        contract_sha256=canonical_sha256(payload),
    )


def _task_projection(task: FrozenRuleReadTask, *, include_hash: bool = False) -> dict[str, Any]:
    payload = {
        "task_id": task.task_id,
        "human_goal": task.human_goal,
        "responsibility_key": task.responsibility_key,
        "heading_path": list(task.heading_path),
        "disclosure": task.disclosure,
        "source_locator": task.source_locator,
        "source_sha256": task.source_sha256,
        "expected_outcome": task.expected_outcome,
        "expected_completed_scope": [
            {"responsibility_key": key, "heading_path": list(path)} for key, path in task.expected_completed_scope
        ],
        "expected_part_sha256": list(task.expected_part_sha256),
    }
    if include_hash:
        payload["task_sha256"] = task.task_sha256
    return payload


def freeze_task(
    *,
    task_id: str,
    human_goal: str,
    responsibility_key: str,
    heading_path: Sequence[str],
    disclosure: str,
    source_locator: str,
    source_sha256: str,
    expected_outcome: str,
    expected_completed_scope: Sequence[tuple[str, Sequence[str]]],
    expected_part_sha256: Sequence[str],
) -> FrozenRuleReadTask:
    path = tuple(heading_path)
    if disclosure != "L3" or len(path) not in {1, 2}:
        raise TrialMeasurementError("rule-read tasks must use exact L3 H2/H3 selections")
    scope = tuple((key, tuple(scope_path)) for key, scope_path in expected_completed_scope)
    if not scope:
        raise TrialMeasurementError("expected completed scope must be non-empty")
    for index, (key, scope_path) in enumerate(scope):
        _text(key, f"expected_completed_scope[{index}].responsibility_key")
        if len(scope_path) not in {1, 2} or any(not isinstance(heading, str) or not heading for heading in scope_path):
            raise TrialMeasurementError("expected completed scope must use exact H2/H3 paths")
    parts = tuple(expected_part_sha256)
    _unique(parts, "expected part hashes")
    for index, digest in enumerate(parts):
        _sha(digest, f"expected_part_sha256[{index}]")
    task = FrozenRuleReadTask(
        task_id=_text(task_id, "task_id"),
        human_goal=_text(human_goal, "human_goal"),
        responsibility_key=_text(responsibility_key, "responsibility_key"),
        heading_path=path,
        disclosure=disclosure,
        source_locator=_text(source_locator, "source_locator"),
        source_sha256=_sha(source_sha256, "source_sha256"),
        expected_outcome=_text(expected_outcome, "expected_outcome"),
        expected_completed_scope=scope,
        expected_part_sha256=parts,
        task_sha256="0" * 64,
    )
    return replace(task, task_sha256=canonical_sha256(_task_projection(task)))


def _entry_index(contract: RuleReadContextContract) -> dict[str, ContextEntry]:
    return {entry.entry_id: entry for entry in contract.entries}


def bind_variant(
    contract: RuleReadContextContract,
    task: FrozenRuleReadTask,
    *,
    variant: str,
    condition_key: str,
    removed_entry_id: str | None = None,
    added_entry_id: str | None = None,
) -> BoundVariantEnvelope:
    if variant not in VARIANTS:
        raise TrialMeasurementError("unknown context variant")
    entries = _entry_index(contract)
    required_ids = tuple(entry.entry_id for entry in contract.entries if entry.kind in {"required", "conditional"})
    selected = list(required_ids)
    if variant == "required_removed":
        if (
            removed_entry_id not in entries
            or entries[removed_entry_id].kind != "required"
            or added_entry_id is not None
        ):
            raise TrialMeasurementError("required_removed must name one required entry only")
        selected.remove(removed_entry_id)
    elif variant == "irrelevant_added":
        if added_entry_id not in entries or entries[added_entry_id].kind != "excluded" or removed_entry_id is not None:
            raise TrialMeasurementError("irrelevant_added must name one excluded entry only")
        selected.append(added_entry_id)
    elif removed_entry_id is not None or added_entry_id is not None:
        raise TrialMeasurementError("full_contract may not carry a context delta")
    payload = {
        "contract_sha256": contract.contract_sha256,
        "task_sha256": task.task_sha256,
        "context_entry_ids": selected,
        "removed_entry_id": removed_entry_id,
        "added_entry_id": added_entry_id,
    }
    payload_sha256 = canonical_sha256(payload)
    envelope = {
        **payload,
        "variant": variant,
        "condition_key": _text(condition_key, "condition_key"),
        "payload_sha256": payload_sha256,
    }
    return BoundVariantEnvelope(
        task_sha256=task.task_sha256,
        contract_sha256=contract.contract_sha256,
        variant=variant,
        context_entry_ids=tuple(selected),
        removed_entry_id=removed_entry_id,
        added_entry_id=added_entry_id,
        condition_key=condition_key,
        payload_sha256=payload_sha256,
        envelope_sha256=canonical_sha256(envelope),
    )


def execution_payload(envelope: BoundVariantEnvelope, task: FrozenRuleReadTask) -> dict[str, Any]:
    if envelope.task_sha256 != task.task_sha256:
        raise TrialMeasurementError("variant envelope does not bind the task")
    return {
        "contract_sha256": envelope.contract_sha256,
        "task": _task_projection(task, include_hash=True),
        "context_entry_ids": list(envelope.context_entry_ids),
        "payload_sha256": envelope.payload_sha256,
    }


def blind_score_payload(
    task: FrozenRuleReadTask,
    *,
    output_sha256: str,
    objective_checks: Mapping[str, bool],
) -> dict[str, Any]:
    return {
        "task_sha256": task.task_sha256,
        "rubric": {
            "expected_outcome": task.expected_outcome,
            "expected_completed_scope": [
                {"responsibility_key": key, "heading_path": list(path)}
                for key, path in task.expected_completed_scope
            ],
            "expected_part_sha256": list(task.expected_part_sha256),
        },
        "output_sha256": _sha(output_sha256, "output_sha256"),
        "objective_checks": dict(objective_checks),
    }


def assess_output(task: FrozenRuleReadTask, output: Mapping[str, Any]) -> ObjectiveAssessment:
    _reject_sensitive_keys(output)
    part_hashes = tuple(output.get("part_sha256", ()))
    scope = tuple(
        (item.get("responsibility_key"), tuple(item.get("heading_path", ())))
        for item in output.get("completed_scope", ())
        if isinstance(item, Mapping)
    )
    checks = {
        "outcome": output.get("outcome") == task.expected_outcome,
        "completed_scope": scope == task.expected_completed_scope,
        "part_sha256": part_hashes == task.expected_part_sha256,
        "source_locator": output.get("source_locator") == task.source_locator,
        "disclosure": output.get("actual_disclosure") == task.disclosure,
    }
    status = "passed" if all(checks.values()) else "failed"
    return ObjectiveAssessment(
        status=status,
        checks=checks,
        output_sha256=canonical_sha256(output),
        reason=None if status == "passed" else "objective rule-read rubric mismatch",
    )


def _reject_sensitive_keys(value: object, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _SENSITIVE_KEYS:
                raise TrialMeasurementError(f"sensitive field is not permitted at {path}.{key}")
            _reject_sensitive_keys(child, f"{path}.{key}")
    elif isinstance(value, list | tuple):
        for index, child in enumerate(value):
            _reject_sensitive_keys(child, f"{path}[{index}]")


def summarize_aggregate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    projected: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        _reject_sensitive_keys(record, f"records[{index}]")
        required = {
            "task_sha256",
            "variant",
            "output_sha256",
            "objective_status",
            "independent_scores",
            "calls",
            "repairs",
            "latency_ms",
            "failure_reason",
        }
        if set(record) != required:
            raise TrialMeasurementError("aggregate record fields must be closed")
        _sha(record["task_sha256"], "task_sha256")
        _sha(record["output_sha256"], "output_sha256")
        if record["variant"] not in VARIANTS:
            raise TrialMeasurementError("aggregate variant must use the closed set")
        if record["objective_status"] not in {"passed", "failed", "inconclusive"}:
            raise TrialMeasurementError("objective_status must use the closed set")
        for name in ("calls", "repairs", "latency_ms"):
            value = record[name]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise TrialMeasurementError(f"{name} must be a non-negative integer")
        if record["failure_reason"] is not None and not isinstance(record["failure_reason"], str):
            raise TrialMeasurementError("failure_reason must be a string or null")
        scores = record["independent_scores"]
        invalid_scores = isinstance(scores, list) and any(
            score not in {"pass", "fail", "inconclusive"} for score in scores
        )
        if not isinstance(scores, list) or len(scores) < 2 or invalid_scores:
            raise TrialMeasurementError("at least two closed-set independent scores are required")
        agreement = len(set(scores)) == 1 and scores[0] != "inconclusive"
        projected.append({**record, "agreement": agreement})
    conclusive = all(record["objective_status"] in {"passed", "failed"} and record["agreement"] for record in projected)
    return {
        "contract": AGGREGATE_VERSION,
        "records": projected,
        "method_status": "observed" if conclusive else "inconclusive",
        "evidence_levels": {
            "LDVH prepared": "observed",
            "harness-delivered": "observed",
            "host-received": HOST_RECEIVED_UNAVAILABLE,
            "behavior-consistent": "observed" if conclusive else "inconclusive",
            "causal-effect": "not_established",
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }


def persist_integrity_envelope(root: SafeTrialTempRoot, relative_path: str, record: Mapping[str, Any]) -> None:
    _reject_sensitive_keys(record)
    payload = dict(record)
    root.write_json(
        relative_path,
        {"record": payload, "integrity_sha256": canonical_sha256(payload)},
    )


def recover_integrity_envelope(root: SafeTrialTempRoot, relative_path: str) -> tuple[str, dict[str, Any] | None]:
    envelope = root.read_json(relative_path)
    if set(envelope) != {"record", "integrity_sha256"} or not isinstance(envelope.get("record"), dict):
        return "inconclusive", None
    expected = envelope.get("integrity_sha256")
    if not isinstance(expected, str) or not hmac.compare_digest(expected, canonical_sha256(envelope["record"])):
        return "inconclusive", None
    try:
        _reject_sensitive_keys(envelope["record"])
    except TrialMeasurementError:
        return "inconclusive", None
    return "observed", envelope["record"]


__all__ = [
    "AGGREGATE_VERSION",
    "BoundVariantEnvelope",
    "CLAIM_BOUNDARY",
    "CONTRACT_VERSION",
    "ContextEntry",
    "EVIDENCE_LEVELS",
    "FrozenRuleReadTask",
    "HOST_RECEIVED_UNAVAILABLE",
    "ObjectiveAssessment",
    "RuleReadContextContract",
    "VARIANTS",
    "assess_output",
    "bind_variant",
    "blind_score_payload",
    "build_contract",
    "execution_payload",
    "freeze_task",
    "persist_integrity_envelope",
    "recover_integrity_envelope",
    "summarize_aggregate",
]
