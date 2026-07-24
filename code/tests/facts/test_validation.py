from __future__ import annotations

from pathlib import Path

from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.validation import validate_fact_object
from ldvh.specs.repository import inspect_repository


def _common(kind: str, object_id: str, status: str) -> dict[str, object]:
    return {
        "object_id": object_id,
        "fact_type_key": kind,
        "title": "A bounded fact",
        "created_at": "2026-07-14T09:00:00+08:00",
        "updated_at": "2026-07-14T10:00:00+08:00",
        "status": status,
    }


def _schemas(root: Path) -> dict[str, object]:
    return project_fact_schemas(inspect_repository(root))


def test_urls_are_validated(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["study"]
    fields = {
        **_common("study", "study-0001", "active"),
        "urls": [
            {"ref": "https://example.invalid/research", "title": "Research", "summary": "Supports the bounded finding."}
        ],
        "research_question": "What is the external contract?",
        "abstract": "A bounded answer.",
        "research_intent": "Determine whether the external contract changes the current project judgment.",
        "recommendation_summary": "Use the bounded finding as an input to a later project decision.",
    }
    assert validate_fact_object("study", fields, schema) == ()

    fields["urls"] = [{"ref": "docs/local.md", "title": "Local", "summary": "Invalid."}]
    issues = validate_fact_object("study", fields, schema)
    assert any(issue.field_path == "urls[0].ref" for issue in issues)


def test_study_requires_urls(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["study"]
    fields = {
        **_common("study", "study-0001", "active"),
        "research_question": "What is the external contract?",
        "abstract": "A bounded answer.",
        "research_intent": "Determine whether the external contract changes the current project judgment.",
        "recommendation_summary": "Use the bounded finding as an input to a later project decision.",
    }
    issues = validate_fact_object("study", fields, schema)
    assert any(issue.field_path == "urls" for issue in issues)


def test_all_fact_types_validate_the_shared_url_member_contract(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["spark"]
    fields = {
        **_common("spark", "spark-0001", "open"),
        "summary": "A current question.",
        "priority": "P2",
        "urls": [{"ref": "https://example.invalid/material", "title": "Material"}],
    }

    issues = validate_fact_object("spark", fields, schema)

    assert any(issue.field_path == "urls[0].summary" for issue in issues)


def test_legacy_reference_fields_are_rejected(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["spark"]
    fields = {
        **_common("spark", "spark-0001", "open"),
        "summary": "A current question.",
        "priority": "P2",
        "source_refs": [{"kind": "repository-path", "locator": "docs/input.md"}],
        "evidence_refs": [{"kind": "repository-path", "locator": "docs/output.md"}],
    }
    issues = validate_fact_object("spark", fields, schema)
    assert {issue.field_path for issue in issues} >= {"source_refs", "evidence_refs"}


def test_relations_accept_only_key_and_target(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["spark"]
    fields = {
        **_common("spark", "spark-0001", "open"),
        "summary": "A current question.",
        "priority": "P2",
        "relations": [
            {
                "relation_key": "related-to",
                "target": {"governed_project_id": "p", "fact_type_key": "adr", "object_id": "adr-0001"},
            }
        ],
    }
    assert validate_fact_object("spark", fields, schema) == ()
    fields["relations"] = [{**fields["relations"][0], "source_refs": []}]
    assert any(
        issue.field_path == "relations[0].source_refs" for issue in validate_fact_object("spark", fields, schema)
    )


def test_workcase_natural_language_result_is_the_evidence_carrier(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    fields = {
        **_common("workcase", "workcase-0001", "open"),
        "summary": "Waiting for plan confirmation.",
        "goal": "Complete one bounded change.",
        "scope": "Only the stated change.",
        "success_criteria": ["The change is validated."],
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Implement",
                "expected_result": "A validated result",
                "status": "pending",
                "approach_summary": "Make the bounded change.",
            }
        ],
        "creation_reviews": [
            {
                "reviewer": "reviewer",
                "reviewed_at": "2026-07-14T09:30:00+08:00",
                "subject_version": 1,
                "scope": "Plan",
                "conclusion": "pass",
                "feedback": ["Proceed"],
                "controller_resolution": "Accepted.",
            }
        ],
        "priority": "P2",
        "resume_from": "Wait for Human plan approval.",
        "waiting_on": "Human plan approval.",
    }
    assert validate_fact_object("workcase", fields, schema) == ()
