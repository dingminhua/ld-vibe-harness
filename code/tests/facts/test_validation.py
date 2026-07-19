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


def _workcase_fields() -> dict[str, object]:
    return {
        "summary": "Waiting for Human execution approval",
        "resume_from": "Present plan version 1 for Human approval",
        "waiting_on": "Human execution approval",
        "priority": "P2",
        "goal": "Ship",
        "scope": "One module",
        "success_criteria": ["Tests pass"],
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Implement the module",
                "expected_result": "The module passes its tests",
                "status": "pending",
                "approach_summary": "Implement within the declared scope and run focused tests",
            }
        ],
        "creation_reviews": [
            {
                "reviewer": "independent-plan-reviewer",
                "reviewed_at": "2026-07-14T09:30:00+08:00",
                "subject_version": 1,
                "scope": "Goal, scope, success criteria, work items, method, validation and risks",
                "conclusion": "pass",
                "feedback": ["The plan is bounded and independently checkable"],
                "controller_resolution": "1. Accepted; no plan change required.",
            }
        ],
    }


def _workcase_phase_fields(phase: str) -> dict[str, object]:
    fields = _workcase_fields()
    if phase == "human_plan_confirming":
        return fields

    fields.pop("waiting_on")
    fields["phase"] = phase
    fields["execution_approval"] = {
        "subject_version": 1,
        "approved_at": "2026-07-14T09:35:00+08:00",
        "summary": "Human approved plan version 1",
    }
    if phase == "executing":
        return fields

    fields["work_items"] = [
        {
            "item_id": "item-01",
            "goal": "Implement the module",
            "expected_result": "The module passes its tests",
            "status": "completed",
            "approach_summary": "Implement within the declared scope and run focused tests",
            "result_summary": "The module is implemented and its focused tests pass",
            "evidence_refs": [{"kind": "repository-path", "locator": "evidence/item-01.txt"}],
        }
    ]
    fields["result_version"] = 1
    if phase == "controller_checking":
        return fields

    fields["controller_check_summary"] = "Checked the work item, success criteria, tests, and residual scope"
    if phase == "independent_reviewing":
        return fields

    fields["result_reviews"] = [
        {
            "reviewer": "independent-result-reviewer",
            "reviewed_at": "2026-07-14T09:50:00+08:00",
            "subject_version": 1,
            "scope": "Work item result, success criteria, validation, residual scope, and routing",
            "conclusion": "pass",
            "feedback": ["The result package is complete"],
            "controller_resolution": "1. Accepted; no result change required.",
        }
    ]
    if phase == "closure_preparing":
        return fields

    fields.update(
        {
            "waiting_on": "Human closure confirmation",
            "validation_summary": "The success criterion is satisfied by the recorded test evidence",
            "closure_outcome": "completed",
            "disposition_summary": "The responsibility is complete with no residual work",
            "evidence_refs": [{"kind": "repository-path", "locator": "evidence/final.txt"}],
        }
    )
    if phase == "human_closure_confirming":
        return fields

    fields.pop("resume_from")
    fields.pop("waiting_on")
    fields["closure_approval"] = {
        "subject_version": 1,
        "approved_at": "2026-07-14T09:55:00+08:00",
        "summary": "Human approved closing result version 1",
    }
    fields["closed_at"] = "2026-07-14T09:55:00+08:00"
    return fields


def test_projected_schemas_validate_all_five_minimal_shapes(current_specs_repository: Path) -> None:
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    objects = {
        "spark": {**_common("spark", "spark-0001", "open"), "summary": "Question", "priority": "P2"},
        "workcase": {
            **_common("workcase", "workcase-0001", "open"),
            **_workcase_fields(),
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
                },
                {
                    "kind": "web-page",
                    "locator": "https://example.invalid/study-evidence",
                    "observed_at": "2026-07-14T09:30:00+08:00",
                },
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
    assert any(issue.field_path == "evidence_refs" and "web-page" in issue.summary for issue in issues)


def test_study_requires_external_evidence_but_allows_internal_context(current_specs_repository: Path) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["study"]
    fields = {
        **_common("study", "study-0001", "active"),
        "source_refs": [
            {
                "kind": "repository-path",
                "locator": "docs/research-request.md",
                "observed_at": "2026-07-14T09:30:00+08:00",
            }
        ],
        "evidence_refs": [
            {
                "kind": "repository-path",
                "locator": "docs/internal-context.md",
                "observed_at": "2026-07-14T09:30:00+08:00",
            }
        ],
        "applicability": "The current governed project.",
        "validation_summary": "The external evidence and internal context were separately reviewed.",
        "research_question": "What does the external product document say about its public contract?",
        "abstract": "The report distinguishes the external contract from local adoption decisions.",
    }

    issues = validate_fact_object("study", fields, schema)
    assert any(issue.field_path == "evidence_refs" and "外部证据" in issue.summary for issue in issues)

    fields["evidence_refs"].append(
        {
            "kind": "web-page",
            "locator": "https://example.invalid/external-contract",
            "observed_at": "2026-07-14T09:30:00+08:00",
        }
    )
    assert validate_fact_object("study", fields, schema) == ()

    fields["evidence_refs"] = [
        {
            "kind": "human-provided-artifact",
            "locator": "evidence/external-paper.pdf",
            "observed_at": "2026-07-14T09:30:00+08:00",
        }
    ]
    assert validate_fact_object("study", fields, schema) == ()


def test_workcase_phase_items_versions_and_event_times_are_mechanical(current_specs_repository: Path) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]
    fields = {
        **_common("workcase", "workcase-0001", "open"),
        **_workcase_fields(),
        "phase": "executing",
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "First result",
                "expected_result": "First result is observable",
                "status": "pending",
                "depends_on": ["item-02"],
                "approach_summary": "Execute within the declared scope",
            },
            {
                "item_id": "item-02",
                "goal": "Second result",
                "expected_result": "Second result is observable",
                "status": "pending",
                "depends_on": ["item-01"],
                "approach_summary": "Execute within the declared scope",
            },
        ],
        "creation_reviews": [
            {
                "reviewer": "independent-plan-reviewer",
                "reviewed_at": "2026-07-14T11:00:00+08:00",
                "subject_version": 2,
                "scope": "Current plan",
                "conclusion": "pass",
                "feedback": ["Plan is bounded"],
                "controller_resolution": "1. Accepted.",
            }
        ],
    }

    issues = validate_fact_object("workcase", fields, schema)

    assert any(issue.field_path == "execution_approval" for issue in issues)
    assert any(issue.field_path == "work_items" and "成环" in issue.summary for issue in issues)
    assert any(issue.field_path == "creation_reviews[0].subject_version" for issue in issues)
    assert any(issue.field_path == "creation_reviews[0].reviewed_at" for issue in issues)


@pytest.mark.parametrize(
    ("phase", "status"),
    [
        ("human_plan_confirming", "open"),
        ("executing", "open"),
        ("controller_checking", "open"),
        ("independent_reviewing", "open"),
        ("closure_preparing", "open"),
        ("human_closure_confirming", "open"),
        ("closed", "closed"),
    ],
)
def test_each_workcase_phase_has_a_mechanically_valid_snapshot(
    current_specs_repository: Path,
    phase: str,
    status: str,
) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]
    fields = {
        **_common("workcase", "workcase-0001", status),
        **_workcase_phase_fields(phase),
    }
    if status == "closed":
        fields.pop("priority")

    assert validate_fact_object("workcase", fields, schema) == ()


def test_human_closure_confirmation_requires_waiting_on(current_specs_repository: Path) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]
    fields = {
        **_common("workcase", "workcase-0001", "open"),
        **_workcase_phase_fields("human_closure_confirming"),
    }
    fields.pop("waiting_on")

    issues = validate_fact_object("workcase", fields, schema)

    assert any(issue.field_path == "waiting_on" and "要求" in issue.summary for issue in issues)


def test_each_fact_type_rejects_an_unknown_top_level_field(current_specs_repository: Path) -> None:
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    required_by_type = {
        "spark": {"summary": "Question", "priority": "P2"},
        "workcase": {
            **_workcase_fields(),
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
            **_workcase_fields(),
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
        ("fact-object", "ldvh-base/sparks/spark-0001.yaml", None),
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
        "evidence_refs": [
            reference,
            {
                "kind": "web-page",
                "locator": "https://example.invalid/external-evidence",
                "observed_at": "2026-07-14T09:30:00+08:00",
            },
        ],
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
