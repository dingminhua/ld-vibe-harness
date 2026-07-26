from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.validation import validate_fact_object
from ldvh.facts.workcase_projection import workcase_subject_fingerprint
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


def _current_progress_workcase() -> dict[str, object]:
    fields: dict[str, object] = {
        **_common("workcase", "workcase-0008", "open"),
        "created_at": "2026-07-26T08:00:00+08:00",
        "updated_at": "2026-07-26T09:00:00+08:00",
        "workcase_profile": "control-contract-v1",
        "summary": "Executing the approved plan.",
        "priority": "P1",
        "resume_from": "Continue the current work item.",
        "goal": "Deliver one bounded result.",
        "scope": "One bounded module.",
        "phase": "executing",
        "plan_version": 1,
        "success_criterion_definitions": [
            {"criterion_id": "criterion-01", "statement": "The bounded result is verified."}
        ],
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Produce the result.",
                "expected_result": "One verified result.",
                "status": "in_progress",
                "approach_summary": "Use the bounded implementation path.",
                "current_summary": "Implementation is in progress.",
                "resume_from": "Continue the implementation.",
            }
        ],
        "audit_summary": [
            {
                "audit_id": "audit-01",
                "subject_kind": "pre_creation_plan",
                "subject_version": 1,
                "review_count": 1,
                "summary": "The initial plan review was resolved before creation.",
            }
        ],
        "execution_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-26T08:45:00+08:00",
            "summary": "Human approved the current plan.",
        },
        "progress_history": {
            "coverage": "full",
            "entries": [
                {
                    "event_id": "progress-001",
                    "plan_version": 1,
                    "round": 1,
                    "phase": "executing",
                    "entered_at": "2026-07-26T08:45:00+08:00",
                    "transition_kind": "started",
                    "transition_summary": "Begin the approved current plan.",
                }
            ],
        },
    }
    fields["creation_reviews"] = [
        {
            "reviewer": "independent-plan-reviewer",
            "reviewed_at": "2026-07-26T08:30:00+08:00",
            "subject_version": 1,
            "scope": "Current plan",
            "conclusion": "pass",
            "feedback": ["The bounded plan is coherent."],
            "review_basis": {
                "projection_key": "plan_current",
                "subject_fingerprint": workcase_subject_fingerprint(fields, "plan_current"),
            },
            "controller_resolution": "Accepted.",
        }
    ]
    return fields


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


def test_pitfall_uses_natural_language_boundaries_without_reference_fields(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["pitfall"]
    fields = {
        **_common("pitfall", "pitfall-0001", "active"),
        "applicability": "Only the observed local installation conditions; other environments remain unverified.",
        "validation_summary": (
            "The handling restored the observed behavior; upgrade and secondary event coverage remain unverified."
        ),
        "symptoms": "The declared hook did not run.",
        "trigger_conditions": "The runtime data directory was empty in the observed local installation.",
        "root_cause": "In the observed conditions, the runtime could not find its required configuration.",
        "resolution": "Copy the required configuration into the selected runtime data directory and restart.",
        "avoidance": "Check the selected runtime data directory and confirm the observed event before generalizing.",
    }

    assert validate_fact_object("pitfall", fields, schema) == ()

    fields["source_ref"] = {"kind": "repository-path", "locator": "docs/input.md"}
    fields["evidence_ref"] = {"kind": "repository-path", "locator": "docs/output.md"}
    issues = validate_fact_object("pitfall", fields, schema)

    assert {issue.field_path for issue in issues} >= {"source_ref", "evidence_ref"}


def test_adr_uses_natural_language_boundaries_without_reference_fields(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["adr"]
    fields = {
        **_common("adr", "adr-0001", "active"),
        "decision_question": "Which bounded direction has already been selected?",
        "decision": "The Human has selected the bounded direction described here.",
        "applicability": "Only the declared long-term choice; implementation effects remain unverified.",
        "rationale": "The selection records the contemporaneous trade-off, not a proof of its premises.",
        "consequences": (
            "The selected direction does not itself prove implementation, rule effectiveness, or authorization."
        ),
    }

    assert validate_fact_object("adr", fields, schema) == ()

    fields["source_ref"] = {"kind": "repository-path", "locator": "docs/input.md"}
    fields["evidence_ref"] = {"kind": "repository-path", "locator": "docs/output.md"}
    issues = validate_fact_object("adr", fields, schema)

    assert {issue.field_path for issue in issues} >= {"source_ref", "evidence_ref"}


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


def test_current_workcase_progress_history_is_a_validated_fact_structure(
    current_specs_repository: Path,
) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    fields = _current_progress_workcase()

    assert validate_fact_object("workcase", fields, schema) == ()

    missing = deepcopy(fields)
    missing.pop("progress_history")
    issues = validate_fact_object("workcase", missing, schema)
    assert any(issue.field_path == "progress_history" and "边界后" in issue.summary for issue in issues)

    wrong_round = deepcopy(fields)
    wrong_round["progress_history"]["entries"][0]["round"] = 2
    issues = validate_fact_object("workcase", wrong_round, schema)
    assert any("首项轮次" in issue.summary for issue in issues)


def test_existing_workcase_can_start_an_explicit_partial_progress_baseline(
    current_specs_repository: Path,
) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    fields = _current_progress_workcase()
    fields["created_at"] = "2026-07-25T08:00:00+08:00"
    history = fields["progress_history"]
    history["coverage"] = "partial"
    history["entries"][0]["transition_kind"] = "baseline"

    assert validate_fact_object("workcase", fields, schema) == ()
