from __future__ import annotations

from pathlib import Path

from ldvh.facts.relations import (
    _source_condition,
    _target_condition,
    _target_has_readable_title,
    validate_project_relations,
)
from ldvh.facts.repository import FactReadResult


class _CurrentProjectIndex:
    governed_project_id = "current-project"


def test_spark_routed_to_rejects_study_but_accepts_other_stable_fact_types_across_target_lifecycle_states() -> None:
    assert not _target_condition("spark", "routed-to", "study", "active")
    assert not _target_condition("spark", "routed-to", "spark", "open")
    assert _target_condition("spark", "routed-to", "workcase", "open")
    assert _target_condition("spark", "routed-to", "workcase", "closed")


def test_spark_routed_to_requires_a_nonempty_current_target_title() -> None:
    assert _target_has_readable_title("spark", "routed-to", {"title": "Helper 事实对象机械结构校验闭环"})
    assert not _target_has_readable_title("spark", "routed-to", {"title": "  "})
    assert _target_has_readable_title("spark", "related-to", {})


def test_spark_routed_to_source_matches_its_status_semantics() -> None:
    assert _source_condition("spark", "routed-to", {"status": "routed"})
    assert not _source_condition("spark", "routed-to", {"status": "discarded"})


def test_spark_relations_are_limited_to_the_current_project_until_cross_project_is_designed() -> None:
    read = FactReadResult(
        Path("ldvh-base/sparks/spark-0001.yaml"),
        "yaml",
        "mechanically_valid",
        {
            "status": "open",
            "relations": [
                {
                    "relation_key": "related-to",
                    "target": {
                        "governed_project_id": "other-project",
                        "fact_type_key": "workcase",
                        "object_id": "workcase-0001",
                    },
                }
            ],
        },
        None,
        (),
    )

    issues, unavailable = validate_project_relations(_CurrentProjectIndex(), "spark", "spark-0001", read)  # type: ignore[arg-type]

    assert not unavailable
    assert any(issue.summary == "Spark 关系目标只允许同一管辖项目" for issue in issues)


def test_routed_spark_requires_at_least_one_routed_to_relation() -> None:
    read = FactReadResult(
        Path("ldvh-base/sparks/spark-0001.yaml"),
        "yaml",
        "mechanically_valid",
        {"status": "routed", "relations": []},
        None,
        (),
    )

    issues, unavailable = validate_project_relations(_CurrentProjectIndex(), "spark", "spark-0001", read)  # type: ignore[arg-type]

    assert not unavailable
    assert any(issue.summary == "routed Spark 至少需要一条 routed-to 关系" for issue in issues)


def test_spark_related_to_can_target_an_implemented_spark() -> None:
    assert _target_condition("spark", "related-to", "spark", "implemented")
