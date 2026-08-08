from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ldvh.testing.fact_change_measurement import (
    CandidateProjection,
    FactChangeMeasurementError,
    ObjectVersion,
    capture_candidate_projection,
    capture_public_observation,
    compare_candidate_projections,
    compare_public_observations,
    parse_candidate_projection,
    persist_fixture_measurement,
)
from ldvh.testing.trial_measurement import SafeTrialTempRoot


def _public_response(fingerprint: str) -> dict[str, object]:
    return {
        "outcome": "ok",
        "result": {
            "recovery_manifest": {"object_set_fingerprint": fingerprint},
            "coverage": {"status": "complete", "object_set_fingerprint": fingerprint},
        },
    }


def _projection(*entries: tuple[str, str, str]) -> CandidateProjection:
    objects = tuple(ObjectVersion(*entry) for entry in entries)
    payload = [entry.to_json() for entry in objects]
    import hashlib

    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(raw).hexdigest()
    return CandidateProjection(objects, digest)


def _snapshot(*entries: tuple[str, str, str], complete: bool = True) -> object:
    cache = {
        (fact_type, object_id): SimpleNamespace(
            check_status="mechanically_valid", fields={"status": "open"}, content_fingerprint=fingerprint
        )
        for fact_type, object_id, fingerprint in entries
    }
    return SimpleNamespace(
        complete=complete,
        structural_problems=(),
        keys=tuple((fact_type, object_id) for fact_type, object_id, _ in entries),
        index=SimpleNamespace(cache=cache),
    )


def test_public_observation_exposes_only_aggregate_change() -> None:
    before = capture_public_observation(_public_response("a" * 64))
    after = capture_public_observation(_public_response("b" * 64))
    comparison = compare_public_observations(before, after)
    assert comparison["changed_detected"] is True
    assert comparison["location_supported"] is False
    assert comparison["located_refs"] == []
    assert comparison["operation_count"] == 2
    assert comparison["response_bytes"] == before.response_bytes + after.response_bytes


@pytest.mark.parametrize("response", [_public_response("a" * 64), {"outcome": "rejected", "result": None}])
def test_public_observation_rejects_incomplete_or_invalid_boundaries(response: dict[str, object]) -> None:
    if response["outcome"] == "ok":
        response["result"]["coverage"]["status"] = "partial"  # type: ignore[index]
    with pytest.raises(FactChangeMeasurementError):
        capture_public_observation(response)


def test_candidate_projection_requires_complete_valid_snapshot() -> None:
    with pytest.raises(FactChangeMeasurementError, match="incomplete"):
        capture_candidate_projection(_snapshot(("spark", "spark-0001", "a" * 64), complete=False))  # type: ignore[arg-type]

    broken = _snapshot(("spark", "spark-0001", "a" * 64))
    broken.index.cache[("spark", "spark-0001")].check_status = "invalid"
    with pytest.raises(FactChangeMeasurementError, match="mechanically valid"):
        capture_candidate_projection(broken)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("scenario", "before", "after", "expected_key"),
    [
        (
            "modified",
            _projection(("spark", "spark-0001", "a" * 64)),
            _projection(("spark", "spark-0001", "b" * 64)),
            "modified",
        ),
        (
            "added",
            _projection(("spark", "spark-0001", "a" * 64)),
            _projection(("spark", "spark-0001", "a" * 64), ("adr", "adr-0001", "b" * 64)),
            "added",
        ),
        (
            "removed",
            _projection(("spark", "spark-0001", "a" * 64), ("adr", "adr-0001", "b" * 64)),
            _projection(("spark", "spark-0001", "a" * 64)),
            "removed",
        ),
        (
            "cross-checkpoint",
            _projection(("spark", "spark-0001", "a" * 64)),
            _projection(("spark", "spark-0001", "a" * 64), ("study", "study-0001", "b" * 64)),
            "added",
        ),
    ],
)
def test_four_frozen_change_scenarios_are_exact_and_recomputable(
    scenario: str, before: CandidateProjection, after: CandidateProjection, expected_key: str
) -> None:
    if scenario == "cross-checkpoint":
        before = parse_candidate_projection(json.loads(json.dumps(before.to_json())))
    comparison = compare_candidate_projections(before, after)
    assert comparison["located_count"] == 1
    assert len(comparison[expected_key]) == 1
    assert all(comparison[key] == [] for key in {"added", "removed", "modified"} - {expected_key})


def test_capture_and_parse_projection_recomputes_fingerprint() -> None:
    projection = capture_candidate_projection(_snapshot(("spark", "spark-0001", "a" * 64)))  # type: ignore[arg-type]
    assert parse_candidate_projection(projection.to_json()) == projection
    tampered = projection.to_json()
    tampered["projection_sha256"] = "0" * 64
    with pytest.raises(FactChangeMeasurementError, match="fingerprint"):
        parse_candidate_projection(tampered)


def test_fixture_artifacts_are_bounded_to_runner_owned_temp_root(tmp_path: Path) -> None:
    root = SafeTrialTempRoot.create(prefix="ldvh-change-test-", repository_root=tmp_path)
    scenarios = ("modified", "added", "removed", "cross-checkpoint")
    observations = {scenario: {"scenario": scenario} for scenario in scenarios}
    persisted = persist_fixture_measurement(
        root,
        fixture_contract={"fixture_fingerprint": "a" * 64, "environment_fingerprint": "b" * 64},
        scenario_observations=observations,
        matrix={"rows": sorted(observations)},
    )
    assert set(persisted["paths"]) == {"fixture_contract", *observations, "matrix"}
    assert all(Path(path).is_relative_to(root.root) for path in persisted["paths"].values())
    with pytest.raises(FactChangeMeasurementError, match="exactly four"):
        persist_fixture_measurement(root, fixture_contract={}, scenario_observations={}, matrix={})
