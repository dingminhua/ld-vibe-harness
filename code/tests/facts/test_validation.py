from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.validation import validate_fact_object
from ldvh.specs.repository import inspect_repository


def _common(fact_type_key: str, object_id: str, status: str) -> dict[str, object]:
    return {
        "object_id": object_id,
        "fact_type_key": fact_type_key,
        "title": "Example",
        "created_at": "2026-07-14T09:00:00+08:00",
        "updated_at": "2026-07-14T10:00:00+08:00",
        "status": status,
        "source_refs": [{"kind": "repository-path", "locator": "docs/input.md"}],
    }


def test_projected_schemas_validate_all_five_minimal_shapes(current_specs_repository: Path) -> None:
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    objects = {
        "spark": {**_common("spark", "spark-0001", "open"), "summary": "Question", "priority": "P2"},
        "workcase": {
            **_common("workcase", "workcase-0001", "open"),
            "summary": "Current",
            "priority": "P2",
            "goal": "Ship",
            "scope": "One module",
            "success_criteria": ["Tests pass"],
        },
        "adr": {
            **_common("adr", "adr-0001", "active"),
            "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
            "decision_question": "Which?",
            "decision": "Choose A",
            "applicability": "This project",
            "rationale": "Lower risk",
            "consequences": "Maintain A",
            "decided_at": "2026-07-14T08:00:00+08:00",
        },
        "pitfall": {
            **_common("pitfall", "pitfall-0001", "active"),
            "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
            "applicability": "This project",
            "validation_summary": "Reproduced and fixed",
            "symptoms": "Failure",
            "trigger_conditions": "Specific input",
            "root_cause": "Wrong boundary",
            "resolution": "Move boundary",
            "avoidance": "Check first",
        },
        "study": {
            **_common("study", "study-0001", "active"),
            "source_refs": [
                {
                    "kind": "repository-path",
                    "locator": "docs/input.md",
                    "observed_at": "2026-07-14T09:30:00+08:00",
                }
            ],
            "evidence_refs": [
                {
                    "kind": "repository-path",
                    "locator": "docs/evidence.md",
                    "observed_at": "2026-07-14T09:30:00+08:00",
                }
            ],
            "applicability": "This version",
            "validation_summary": "Sources compared",
            "research_question": "What works?",
            "abstract": "A bounded answer",
        },
    }

    assert set(schemas) == set(objects)
    for fact_type_key, fields in objects.items():
        assert validate_fact_object(fact_type_key, fields, schemas[fact_type_key]) == ()


def test_validator_rejects_unknown_nested_fields_status_and_time(current_specs_repository: Path) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["spark"]
    fields = {
        **_common("spark", "spark-0001", "unknown"),
        "created_at": "2026-07-14T10:00:00",
        "updated_at": "2026-07-14T09:00:00+08:00",
        "summary": "Question",
        "source_refs": [{"kind": "human", "locator": "input", "extra": "forbidden"}],
    }

    issues = validate_fact_object("spark", fields, schema)

    assert {issue.category for issue in issues} >= {"schema"}
    assert any(issue.field_path == "source_refs[0].extra" for issue in issues)
    assert any(issue.field_path == "status" for issue in issues)
    assert any(issue.field_path == "created_at" for issue in issues)


def test_study_reference_profiles_and_observation_time_are_mechanical(current_specs_repository: Path) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["study"]
    fields = {
        **_common("study", "study-0001", "active"),
        "source_refs": [
            {
                "kind": "web-page",
                "locator": "/tmp/not-a-url",
                "observed_at": "2026-07-14T11:00:00+08:00",
            }
        ],
        "evidence_refs": [{"kind": "git-revision", "locator": "../escape", "observed_at": "bad"}],
        "applicability": "This version",
        "validation_summary": "Compared",
        "research_question": "What?",
        "abstract": "Answer",
    }

    issues = validate_fact_object("study", fields, schema)

    assert any(issue.field_path == "source_refs[0].locator" for issue in issues)
    assert any(issue.field_path == "source_refs[0].observed_at" for issue in issues)
    assert any(issue.field_path == "evidence_refs[0].locator" for issue in issues)
    assert any(issue.field_path == "evidence_refs[0].version" for issue in issues)


def test_each_fact_type_rejects_an_unknown_top_level_field(current_specs_repository: Path) -> None:
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    required_by_type = {
        "spark": {"summary": "Question", "priority": "P2"},
        "workcase": {
            "summary": "Current",
            "priority": "P2",
            "goal": "Ship",
            "scope": "One module",
            "success_criteria": ["Tests pass"],
        },
        "adr": {
            "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
            "decision_question": "Which?",
            "decision": "Choose A",
            "applicability": "This project",
            "rationale": "Lower risk",
            "consequences": "Maintain A",
            "decided_at": "2026-07-14T08:00:00+08:00",
        },
        "pitfall": {
            "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
            "applicability": "This project",
            "validation_summary": "Reproduced",
            "symptoms": "Failure",
            "trigger_conditions": "Input",
            "root_cause": "Boundary",
            "resolution": "Move it",
            "avoidance": "Check",
        },
        "study": {
            "source_refs": [
                {
                    "kind": "repository-path",
                    "locator": "docs/input.md",
                    "observed_at": "2026-07-14T09:30:00+08:00",
                }
            ],
            "evidence_refs": [
                {
                    "kind": "repository-path",
                    "locator": "docs/evidence.md",
                    "observed_at": "2026-07-14T09:30:00+08:00",
                }
            ],
            "applicability": "This version",
            "validation_summary": "Compared",
            "research_question": "What?",
            "abstract": "Answer",
        },
    }
    statuses = {"spark": "open", "workcase": "open", "adr": "active", "pitfall": "active", "study": "active"}

    for fact_type_key, additions in required_by_type.items():
        fields = {
            **_common(fact_type_key, f"{fact_type_key}-0001", statuses[fact_type_key]),
            **additions,
            "implementation_private": True,
        }
        issues = validate_fact_object(fact_type_key, fields, schemas[fact_type_key])
        assert any(issue.field_path == "implementation_private" for issue in issues), fact_type_key


@pytest.mark.parametrize(
    ("fact_type_key", "status", "required_field"),
    [
        ("spark", "routed", "disposition_summary"),
        ("spark", "discarded", "closed_at"),
        ("workcase", "blocked", "blocking_summary"),
        ("workcase", "closed", "validation_summary"),
        ("adr", "superseded", "disposition_summary"),
        ("adr", "retired", "closed_at"),
        ("pitfall", "superseded", "disposition_summary"),
        ("pitfall", "retired", "closed_at"),
        ("study", "superseded", "disposition_summary"),
        ("study", "retired", "closed_at"),
    ],
)
def test_each_terminal_or_blocked_state_enforces_its_condition_fields(
    current_specs_repository: Path,
    fact_type_key: str,
    status: str,
    required_field: str,
) -> None:
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    fields = {**_common(fact_type_key, f"{fact_type_key}-0001", status)}
    additions = {
        "spark": {"summary": "Question"},
        "workcase": {
            "summary": "Current",
            "goal": "Ship",
            "scope": "One module",
            "success_criteria": ["Tests pass"],
        },
        "adr": {
            "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
            "decision_question": "Which?",
            "decision": "Choose A",
            "applicability": "This project",
            "rationale": "Lower risk",
            "consequences": "Maintain A",
            "decided_at": "2026-07-14T08:00:00+08:00",
        },
        "pitfall": {
            "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
            "applicability": "This project",
            "validation_summary": "Reproduced",
            "symptoms": "Failure",
            "trigger_conditions": "Input",
            "root_cause": "Boundary",
            "resolution": "Move it",
            "avoidance": "Check",
        },
        "study": {
            "source_refs": [
                {
                    "kind": "web-page",
                    "locator": "https://example.invalid/source",
                    "observed_at": "2026-07-14T09:30:00+08:00",
                }
            ],
            "evidence_refs": [
                {
                    "kind": "web-page",
                    "locator": "https://example.invalid/evidence",
                    "observed_at": "2026-07-14T09:30:00+08:00",
                }
            ],
            "applicability": "This version",
            "validation_summary": "Compared",
            "research_question": "What?",
            "abstract": "Answer",
        },
    }
    fields.update(additions[fact_type_key])
    issues = validate_fact_object(fact_type_key, fields, schemas[fact_type_key])
    assert any(issue.field_path == required_field for issue in issues)


@pytest.mark.parametrize(
    ("kind", "locator", "version"),
    [
        ("fact-object", "facts/sparks/spark-0001.yaml", None),
        ("repository-path", "docs/input.md", None),
        ("git-revision", "docs/input.md", "HEAD"),
        ("web-page", "https://example.invalid/page", None),
        ("api-observation", "https://example.invalid/api", "v1"),
        ("runtime-observation", "evidence/run.json", "python-3.12"),
        ("human-provided-artifact", "evidence/input.pdf", None),
    ],
)
def test_all_seven_study_reference_kinds_pass_their_lexical_contract(
    current_specs_repository: Path,
    kind: str,
    locator: str,
    version: str | None,
) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["study"]
    reference = {
        "kind": kind,
        "locator": locator,
        "observed_at": "2026-07-14T09:30:00+08:00",
    }
    if version is not None:
        reference["version"] = version
    fields = {
        **_common("study", "study-0001", "active"),
        "source_refs": [reference],
        "evidence_refs": [reference],
        "applicability": "This version",
        "validation_summary": "Compared",
        "research_question": "What?",
        "abstract": "Answer",
    }
    assert validate_fact_object("study", fields, schema) == ()


def test_all_observed_at_values_use_strict_rfc3339(current_specs_repository: Path) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["spark"]
    fields = {
        **_common("spark", "spark-0001", "open"),
        "source_refs": [
            {"kind": "repository-path", "locator": "docs/input.md", "observed_at": "2026-07-14T09:30:00+0800"}
        ],
        "summary": "Question",
        "priority": "P2",
    }
    issues = validate_fact_object("spark", fields, schema)
    assert any(issue.field_path == "source_refs[0].observed_at" for issue in issues)
