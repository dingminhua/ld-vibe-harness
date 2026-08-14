"""Evidence protocol: identity shapes, source grading, and comparability thresholds.

This module defines the minimum execution evidence protocol for LDVH testing.
It is a read-only, pure-data module that provides:

- Four identity types (task, contract, payload, runner) with fingerprint shapes
- Five-level event source grading (ldvh-prepared / harness-delivered /
  host-received / behavior-consistent / causal-effect)
- Pre-scoring comparability threshold rules that reuse
  ``session_comparability``'s comparable judgment and event graph pairing
  completeness

The protocol deliberately uses harness-delivered event logs as the evidence
source and never claims host-received availability.  It never reads message
bodies, tool-result content, or assistant output.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ldvh.testing.session_comparability import (
    ComparabilityVerdict,
    SessionFingerprint,
    judge_comparability,
)

EVIDENCE_PROTOCOL_VERSION = "ldvh-evidence-protocol/1"

# ---------------------------------------------------------------------------
# Identity type constants
# ---------------------------------------------------------------------------

IDENTITY_TYPES: tuple[str, ...] = ("task", "contract", "payload", "runner")
"""Closed set of four identity types that every trial must record."""

# ---------------------------------------------------------------------------
# Source grading constants
# ---------------------------------------------------------------------------

SOURCE_LEVEL_LDVH_PREPARED = "ldvh-prepared"
SOURCE_LEVEL_HARNESS_DELIVERED = "harness-delivered"
SOURCE_LEVEL_HOST_RECEIVED = "host-received"
SOURCE_LEVEL_BEHAVIOR_CONSISTENT = "behavior-consistent"
SOURCE_LEVEL_CAUSAL_EFFECT = "causal-effect"

SOURCE_LEVELS: tuple[str, ...] = (
    SOURCE_LEVEL_LDVH_PREPARED,
    SOURCE_LEVEL_HARNESS_DELIVERED,
    SOURCE_LEVEL_HOST_RECEIVED,
    SOURCE_LEVEL_BEHAVIOR_CONSISTENT,
    SOURCE_LEVEL_CAUSAL_EFFECT,
)
"""Five-level event source grading from most to least directly observable.

- ``ldvh-prepared``: events explicitly prepared or controlled by LDVH
  (e.g. approval/asked, permission/preset, sandbox/mode, compaction events).
- ``harness-delivered``: events delivered by the execution harness and
  observable from session event logs (request/header, turn/step/tool events).
  This is the evidence source boundary.
- ``host-received``: events as received by the host platform
  (unavailable from session logs; outside scope).
- ``behavior-consistent``: observed behavioural consistency across trials
  (aggregate pattern, not per-event).
- ``causal-effect``: causal effect claims (outside scope; not derivable from
  structured event logs alone).
"""

# Which event types (from session_comparability) map to each source level.
# These are the concrete classifications used by ``classify_event_type``.
SOURCE_LEVEL_MAP: dict[str, str] = {
    "approval/asked": SOURCE_LEVEL_LDVH_PREPARED,
    "approval/decided": SOURCE_LEVEL_LDVH_PREPARED,
    "approval/policy": SOURCE_LEVEL_LDVH_PREPARED,
    "permission/preset": SOURCE_LEVEL_LDVH_PREPARED,
    "sandbox/mode": SOURCE_LEVEL_LDVH_PREPARED,
    "compaction/start": SOURCE_LEVEL_LDVH_PREPARED,
    "compaction/end": SOURCE_LEVEL_LDVH_PREPARED,
    "compaction/summary": SOURCE_LEVEL_LDVH_PREPARED,
    "compaction/prune": SOURCE_LEVEL_LDVH_PREPARED,
    "llm/retry": SOURCE_LEVEL_LDVH_PREPARED,
    "llm/retry-started": SOURCE_LEVEL_LDVH_PREPARED,
    "hook/invoked": SOURCE_LEVEL_LDVH_PREPARED,
    "hook/result": SOURCE_LEVEL_LDVH_PREPARED,
    "session/end-seed": SOURCE_LEVEL_LDVH_PREPARED,
    "plan/mode": SOURCE_LEVEL_LDVH_PREPARED,
    "feedback/record": SOURCE_LEVEL_LDVH_PREPARED,
    "subagent/descriptor": SOURCE_LEVEL_LDVH_PREPARED,
    "todo/write": SOURCE_LEVEL_LDVH_PREPARED,
    "tool-workflow/run-start": SOURCE_LEVEL_LDVH_PREPARED,
    "tool-workflow/run-end": SOURCE_LEVEL_LDVH_PREPARED,
    "request/header": SOURCE_LEVEL_HARNESS_DELIVERED,
    "tool/call": SOURCE_LEVEL_HARNESS_DELIVERED,
    "tool/result": SOURCE_LEVEL_HARNESS_DELIVERED,
    "turn/start": SOURCE_LEVEL_HARNESS_DELIVERED,
    "turn/end": SOURCE_LEVEL_HARNESS_DELIVERED,
    "step/start": SOURCE_LEVEL_HARNESS_DELIVERED,
    "step/end": SOURCE_LEVEL_HARNESS_DELIVERED,
}
"""Maps known session event type strings to their source grading level.

Event types not in this map (opaque content types, unknown event types) are
not classified and return ``None`` from ``classify_event_type``.
"""

# The source levels that are observable from session logs (the protocol's
# evidence boundary).  ``host-received`` and ``causal-effect`` are explicitly
# outside this boundary.
OBSERVABLE_SOURCE_LEVELS: tuple[str, ...] = (
    SOURCE_LEVEL_LDVH_PREPARED,
    SOURCE_LEVEL_HARNESS_DELIVERED,
    SOURCE_LEVEL_BEHAVIOR_CONSISTENT,
)

# ---------------------------------------------------------------------------
# Identity fingerprints
# ---------------------------------------------------------------------------


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class IdentityFingerprintSet:
    """The four identity fingerprints for one trial.

    Each field is a hex SHA-256 of the canonical JSON representation of the
    corresponding identity shape.
    """

    task_identity: str
    contract_identity: str
    payload_identity: str
    runner_identity: str

    def fingerprint(self) -> str:
        """Canonical hash of the full identity set."""
        return _canonical_sha256(
            {
                "task": self.task_identity,
                "contract": self.contract_identity,
                "payload": self.payload_identity,
                "runner": self.runner_identity,
            }
        )

    def identity_mismatch(self, other: IdentityFingerprintSet) -> dict[str, bool]:
        """Return a per-type mismatch map versus *other*.

        ``True`` means the two identities match for that type; ``False`` means
        a mismatch.
        """
        return {
            "task": self.task_identity == other.task_identity,
            "contract": self.contract_identity == other.contract_identity,
            "payload": self.payload_identity == other.payload_identity,
            "runner": self.runner_identity == other.runner_identity,
        }

    def fully_matches(self, other: IdentityFingerprintSet) -> bool:
        """Return ``True`` only when all four identity types match."""
        return all(self.identity_mismatch(other).values())


def extract_trial_identity(
    *,
    task_id: str,
    task_package_hash: str,
    contract_sha256: str,
    payload: Mapping[str, Any],
    carrier_fingerprint: str,
) -> IdentityFingerprintSet:
    """Build the four identity fingerprints from a trial's structural fields.

    Each identity is a canonical SHA-256 of the relevant subset of trial
    fields.  The payload identity is computed from the structural payload
    keys only (never the values of opaque content fields).
    """
    task_identity = _canonical_sha256({"task_id": task_id, "task_package_hash": task_package_hash})
    contract_identity = _canonical_sha256({"contract_sha256": contract_sha256})
    payload_identity = _canonical_sha256(
        {
            "payload_keys": sorted(payload.keys()),
            "payload_sha256": _canonical_sha256(payload),
        }
    )
    runner_identity = _canonical_sha256({"carrier_fingerprint": carrier_fingerprint})
    return IdentityFingerprintSet(
        task_identity=task_identity,
        contract_identity=contract_identity,
        payload_identity=payload_identity,
        runner_identity=runner_identity,
    )


def extract_session_identity(
    fingerprint: SessionFingerprint,
) -> IdentityFingerprintSet:
    """Build identity fingerprints from a session fingerprint.

    For sessions, the task/contract/payload identities are not directly
    observable (they belong to the trial definition).  The runner identity
    is derived from the session's carrier entries.
    """
    runner_identity = _canonical_sha256(
        {
            "distinct_entries": list(fingerprint.distinct_entries),
            "tool_names": list(fingerprint.tool_names),
        }
    )
    return IdentityFingerprintSet(
        task_identity=_canonical_sha256({"source": "session_only"}),
        contract_identity=_canonical_sha256({"source": "session_only"}),
        payload_identity=_canonical_sha256({"source": "session_only"}),
        runner_identity=runner_identity,
    )


# ---------------------------------------------------------------------------
# Event source classification
# ---------------------------------------------------------------------------


def classify_event_type(event_type: str) -> str | None:
    """Return the source grading level for a known event type, or ``None``.

    Unclassified event types (opaque content types, unknown types) return
    ``None``, meaning they are not part of the observable evidence protocol.
    """
    return SOURCE_LEVEL_MAP.get(event_type)


def classify_event_types(event_types: Sequence[str]) -> dict[str, str]:
    """Classify a sequence of event type strings into a type-to-level map.

    Only classified event types appear in the result; unclassified types are
    omitted.
    """
    result: dict[str, str] = {}
    for event_type in event_types:
        level = classify_event_type(event_type)
        if level is not None:
            result[event_type] = level
    return result


def classify_session_events(fingerprint: SessionFingerprint) -> dict[str, int]:
    """Count session fingerprint events by source grading level.

    Returns a map of source level to count of events at that level.
    Flag events (from ``fingerprint.flags``) are classified by their
    event type name (the flag key).  Turn/step/tool counts are all
    classified as ``harness-delivered``.
    """
    counts: dict[str, int] = {}
    # Classify flag events by their type name.
    for flag_type, count in fingerprint.flags:
        level = classify_event_type(flag_type)
        if level is not None:
            counts[level] = counts.get(level, 0) + count
    # Turn/step/tool events are always harness-delivered.
    harness_count = (
        fingerprint.turn_start
        + fingerprint.turn_end
        + fingerprint.step_start
        + fingerprint.step_end
        + fingerprint.tool_call
        + fingerprint.tool_result
    )
    if harness_count > 0:
        counts[SOURCE_LEVEL_HARNESS_DELIVERED] = (
            counts.get(SOURCE_LEVEL_HARNESS_DELIVERED, 0) + harness_count
        )
    return counts


# ---------------------------------------------------------------------------
# Comparability threshold rules
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProtocolComparability:
    """Protocol-level comparability verdict that extends session comparability.

    Wraps ``session_comparability.judge_comparability()`` and adds protocol-
    specific checks: identity fingerprint matching, event graph pairing
    completeness, and source-level observability.
    """

    session_verdict: ComparabilityVerdict
    protocol_verdict: str
    protocol_reasons: tuple[str, ...] = ()
    identity_mismatch_types: tuple[str, ...] = ()

    @property
    def effective_verdict(self) -> str:
        """Combined verdict: ``protocol_verdict`` wins if stricter.

        - If either verdict is ``not_comparable``, the combined verdict is
          ``not_comparable``.
        - Otherwise, the session verdict is used.
        """
        if self.protocol_verdict == "not_comparable":
            return "not_comparable"
        return self.session_verdict.verdict


def judge_protocol_comparability(
    session_fingerprint: SessionFingerprint,
    *,
    trial_identity: IdentityFingerprintSet | None = None,
    reference_identity: IdentityFingerprintSet | None = None,
) -> ProtocolComparability:
    """Evaluate protocol-level comparability for a trial.

    Steps:
    1. Run ``session_comparability.judge_comparability()``.
    2. If *trial_identity* and *reference_identity* are both provided, check
       identity fingerprint matching across all four identity types.
    3. Check event graph pairing completeness from the session fingerprint.
    4. Combine into a ``ProtocolComparability``.

    A trial whose identity fingerprints do not match the reference is marked
    ``not_comparable`` with ``out_of_protocol`` reason.
    """
    session_verdict = judge_comparability(session_fingerprint)
    protocol_reasons: list[str] = []
    mismatch_types: list[str] = []

    # Identity fingerprint matching.
    if trial_identity is not None and reference_identity is not None:
        mismatch = trial_identity.identity_mismatch(reference_identity)
        for id_type, matches in mismatch.items():
            if not matches:
                mismatch_types.append(id_type)
        if mismatch_types:
            protocol_reasons.append(
                f"out_of_protocol: identity mismatch on {','.join(mismatch_types)}"
            )

    # Event graph pairing completeness.
    if not session_fingerprint.pairing_ok:
        protocol_reasons.append("event_graph_pairing_incomplete")

    if protocol_reasons:
        protocol_verdict = "not_comparable"
    else:
        protocol_verdict = "comparable"

    return ProtocolComparability(
        session_verdict=session_verdict,
        protocol_verdict=protocol_verdict,
        protocol_reasons=tuple(protocol_reasons),
        identity_mismatch_types=tuple(mismatch_types),
    )


def is_out_of_protocol(protocol_comparability: ProtocolComparability) -> bool:
    """Return ``True`` if the trial is out of protocol (identity mismatch)."""
    return any("out_of_protocol" in reason for reason in protocol_comparability.protocol_reasons)


def check_pre_scoring_threshold(
    protocol_comparability: ProtocolComparability,
) -> tuple[bool, str]:
    """Check whether a trial passes the pre-scoring comparability threshold.

    Returns ``(passed, reason)``:
    - ``(True, "comparable")`` if the trial passes all thresholds.
    - ``(False, reason)`` if the trial is ``not_comparable`` or
      ``inconclusive``, with the first blocking reason.
    """
    if is_out_of_protocol(protocol_comparability):
        return (False, "out_of_protocol")
    if protocol_comparability.session_verdict.verdict == "not_comparable":
        if protocol_comparability.session_verdict.reasons:
            return (False, protocol_comparability.session_verdict.reasons[0])
        return (False, "session_not_comparable")
    if protocol_comparability.session_verdict.verdict == "inconclusive":
        return (False, "session_inconclusive")
    if protocol_comparability.protocol_verdict == "not_comparable":
        if protocol_comparability.protocol_reasons:
            return (False, protocol_comparability.protocol_reasons[0])
        return (False, "protocol_not_comparable")
    return (True, "comparable")