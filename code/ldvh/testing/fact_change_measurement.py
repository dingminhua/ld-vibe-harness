"""Testing-only measurement for the fact-set change-location question.

This module deliberately does not extend a Helper response.  It captures what
the current public candidate response can say, then compares a separately
held, in-memory per-object projection for fixture experiments.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ldvh.facts.candidate_discovery import FactCandidateSnapshot


class FactChangeMeasurementError(ValueError):
    """A measurement input cannot support a reliable comparison."""


REQUIRED_SCENARIOS = frozenset({"modified", "added", "removed", "cross-checkpoint"})


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise FactChangeMeasurementError(f"{label} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class PublicObservation:
    """The identity-free result available from the current public response."""

    object_set_fingerprint: str
    response_sha256: str
    response_bytes: int
    operation_count: int = 1

    def to_json(self) -> dict[str, object]:
        return {
            "object_set_fingerprint": self.object_set_fingerprint,
            "response_sha256": self.response_sha256,
            "response_bytes": self.response_bytes,
            "operation_count": self.operation_count,
            "location_supported": False,
            "located_refs": [],
        }


def capture_public_observation(response: Mapping[str, Any]) -> PublicObservation:
    """Capture only the complete F0 aggregate exposed by candidate discovery."""

    result = response.get("result")
    if response.get("outcome") != "ok" or not isinstance(result, Mapping):
        raise FactChangeMeasurementError("public candidate response must be a successful result")
    manifest = result.get("recovery_manifest")
    coverage = result.get("coverage")
    if not isinstance(manifest, Mapping) or not isinstance(coverage, Mapping):
        raise FactChangeMeasurementError("public candidate response lacks recovery manifest or coverage")
    if coverage.get("status") != "complete":
        raise FactChangeMeasurementError("incomplete public candidate response cannot establish a baseline")
    manifest_fingerprint = _string(manifest.get("object_set_fingerprint"), "manifest fingerprint")
    coverage_fingerprint = _string(coverage.get("object_set_fingerprint"), "coverage fingerprint")
    if manifest_fingerprint != coverage_fingerprint:
        raise FactChangeMeasurementError("public response fingerprints disagree")
    raw = _canonical_bytes(response)
    return PublicObservation(manifest_fingerprint, hashlib.sha256(raw).hexdigest(), len(raw))


@dataclass(frozen=True, order=True, slots=True)
class ObjectVersion:
    fact_type_key: str
    object_id: str
    content_fingerprint: str

    def identity(self) -> tuple[str, str]:
        return (self.fact_type_key, self.object_id)

    def to_json(self) -> dict[str, str]:
        return {
            "fact_type_key": self.fact_type_key,
            "object_id": self.object_id,
            "content_fingerprint": self.content_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class CandidateProjection:
    """A complete test-only per-object snapshot; never a public API payload."""

    entries: tuple[ObjectVersion, ...]
    projection_sha256: str

    def to_json(self) -> dict[str, object]:
        entries = [entry.to_json() for entry in self.entries]
        return {"kind": "test-only-in-memory", "entries": entries, "projection_sha256": self.projection_sha256}


def capture_candidate_projection(snapshot: FactCandidateSnapshot) -> CandidateProjection:
    """Create a fail-closed test-only projection from a complete valid scan."""

    if not snapshot.complete or snapshot.structural_problems:
        raise FactChangeMeasurementError("incomplete candidate scan is not comparable")
    entries: list[ObjectVersion] = []
    for fact_type_key, object_id in snapshot.keys:
        read = snapshot.index.cache.get((fact_type_key, object_id))
        if read is None or read.check_status != "mechanically_valid" or read.fields is None:
            raise FactChangeMeasurementError("candidate projection requires mechanically valid object reads")
        entries.append(
            ObjectVersion(
                fact_type_key,
                object_id,
                _string(read.content_fingerprint, "content fingerprint"),
            )
        )
    ordered = tuple(sorted(entries))
    if len({entry.identity() for entry in ordered}) != len(ordered):
        raise FactChangeMeasurementError("candidate projection contains duplicate identities")
    return CandidateProjection(ordered, _digest([entry.to_json() for entry in ordered]))


def parse_candidate_projection(value: Mapping[str, Any]) -> CandidateProjection:
    """Reload a persisted test checkpoint and revalidate every digest."""

    if value.get("kind") != "test-only-in-memory" or not isinstance(value.get("entries"), Sequence):
        raise FactChangeMeasurementError("candidate projection checkpoint is malformed")
    entries: list[ObjectVersion] = []
    for item in value["entries"]:
        if not isinstance(item, Mapping):
            raise FactChangeMeasurementError("candidate projection entry is malformed")
        entries.append(
            ObjectVersion(
                _string(item.get("fact_type_key"), "fact type"),
                _string(item.get("object_id"), "object id"),
                _string(item.get("content_fingerprint"), "content fingerprint"),
            )
        )
    ordered = tuple(sorted(entries))
    if entries != list(ordered) or len({entry.identity() for entry in ordered}) != len(ordered):
        raise FactChangeMeasurementError("candidate projection checkpoint ordering or identities are invalid")
    expected = _digest([entry.to_json() for entry in ordered])
    if value.get("projection_sha256") != expected:
        raise FactChangeMeasurementError("candidate projection checkpoint fingerprint drifted")
    return CandidateProjection(ordered, expected)


def compare_candidate_projections(before: CandidateProjection, after: CandidateProjection) -> dict[str, object]:
    """Return exact identity deltas for two complete test-only projections."""

    before_by_id = {entry.identity(): entry for entry in before.entries}
    after_by_id = {entry.identity(): entry for entry in after.entries}
    added = [after_by_id[key].to_json() for key in sorted(set(after_by_id) - set(before_by_id))]
    removed = [before_by_id[key].to_json() for key in sorted(set(before_by_id) - set(after_by_id))]
    modified = [
        {
            "fact_type_key": key[0],
            "object_id": key[1],
            "before_content_fingerprint": before_by_id[key].content_fingerprint,
            "after_content_fingerprint": after_by_id[key].content_fingerprint,
        }
        for key in sorted(set(before_by_id) & set(after_by_id))
        if before_by_id[key].content_fingerprint != after_by_id[key].content_fingerprint
    ]
    return {
        "kind": "test-only-in-memory-diff",
        "before_projection_sha256": before.projection_sha256,
        "after_projection_sha256": after.projection_sha256,
        "added": added,
        "removed": removed,
        "modified": modified,
        "located_count": len(added) + len(removed) + len(modified),
    }


def compare_public_observations(before: PublicObservation, after: PublicObservation) -> dict[str, object]:
    """Describe the public aggregate boundary without inventing object identities."""

    return {
        "changed_detected": before.object_set_fingerprint != after.object_set_fingerprint,
        "operation_count": before.operation_count + after.operation_count,
        "response_bytes": before.response_bytes + after.response_bytes,
        "location_supported": False,
        "located_refs": [],
    }


def persist_fixture_measurement(
    root: Any,
    *,
    fixture_contract: Mapping[str, object],
    scenario_observations: Mapping[str, Mapping[str, object]],
    matrix: Mapping[str, object],
) -> dict[str, object]:
    """Persist a bounded, recomputable fixture batch through a runner-owned root."""

    if set(scenario_observations) != REQUIRED_SCENARIOS:
        raise FactChangeMeasurementError("fixture batch must cover exactly four frozen scenarios")
    contract_path = root.write_json("protocol/fixture-contract.json", dict(fixture_contract))
    paths: dict[str, str] = {"fixture_contract": str(contract_path)}
    for scenario in sorted(REQUIRED_SCENARIOS):
        observation = dict(scenario_observations[scenario])
        path = root.write_json(f"observations/{scenario}/comparison.json", observation)
        paths[scenario] = str(path)
    matrix_path = root.write_json("analysis/matrix.json", dict(matrix))
    paths["matrix"] = str(matrix_path)
    return {"paths": paths, "fixture_contract_sha256": _digest(fixture_contract), "matrix_sha256": _digest(matrix)}


__all__ = [
    "CandidateProjection",
    "FactChangeMeasurementError",
    "ObjectVersion",
    "PublicObservation",
    "capture_candidate_projection",
    "capture_public_observation",
    "compare_candidate_projections",
    "compare_public_observations",
    "parse_candidate_projection",
    "persist_fixture_measurement",
]
