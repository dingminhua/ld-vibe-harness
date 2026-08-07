from __future__ import annotations

from types import SimpleNamespace

from ldvh.facts.candidate_discovery import FactCandidateSnapshot
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.testing.fact_integrity import assess_fact_snapshot


def _snapshot(
    *,
    complete: bool,
    reads: dict[tuple[str, str], FactReadResult],
    structural: tuple[dict[str, object], ...] = (),
) -> FactCandidateSnapshot:
    return FactCandidateSnapshot(
        index=SimpleNamespace(cache=reads),  # type: ignore[arg-type]
        keys=tuple(reads),
        structural_problems=structural,
        complete=complete,
        schema_fingerprint="schema",
        object_set_fingerprint="objects",
    )


def _read(status: str, issues: tuple[FactIssue, ...] = ()) -> FactReadResult:
    return FactReadResult(
        canonical_path="ldvh-base/sparks/spark-0001.yaml",
        carrier="yaml",
        check_status=status,  # type: ignore[arg-type]
        fields=None,
        body=None,
        issues=issues,
    )


def test_assess_fact_snapshot_is_complete_only_when_every_object_is_mechanically_valid() -> None:
    status, problems = assess_fact_snapshot(
        _snapshot(complete=True, reads={("spark", "spark-0001"): _read("mechanically_valid")})
    )

    assert status == "complete"
    assert problems == ()


def test_assess_fact_snapshot_reports_invalid_object_without_claiming_unavailable_scope() -> None:
    status, problems = assess_fact_snapshot(
        _snapshot(
            complete=True,
            reads={
                ("spark", "spark-0001"): _read(
                    "invalid", (FactIssue("relation", "routed Spark 至少需要一条 routed-to 关系"),)
                )
            },
        )
    )

    assert status == "partial"
    assert problems[0]["canonical_path"] == "ldvh-base/sparks/spark-0001.yaml"
    assert problems[0]["issues"] == [
        {
            "category": "relation",
            "field_path": None,
            "summary": "routed Spark 至少需要一条 routed-to 关系",
        }
    ]


def test_assess_fact_snapshot_marks_incomplete_scanning_as_unavailable() -> None:
    status, problems = assess_fact_snapshot(
        _snapshot(
            complete=False,
            reads={("spark", "spark-0001"): _read("mechanically_valid")},
            structural=(
                {
                    "fact_type_key": "spark",
                    "canonical_path": "ldvh-base/sparks",
                    "check_status": "unavailable",
                    "issues": [],
                },
            ),
        )
    )

    assert status == "unavailable"
    assert problems[0]["check_status"] == "unavailable"
