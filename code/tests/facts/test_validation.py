from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

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


def _v2_workcase() -> dict[str, object]:
    fields: dict[str, object] = {
        **_common("workcase", "workcase-0008", "open"),
        "created_at": "2026-07-26T13:00:00+08:00",
        "updated_at": "2026-07-26T14:00:00+08:00",
        "workcase_profile": "control-contract-v2",
        "summary": "Executing the approved plan.",
        "priority": "P1",
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
                "current_summary": "Implementation is in progress.",
                "resume_from": "Continue the implementation.",
            }
        ],
        "execution_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-26T13:45:00+08:00",
            "summary": "Human approved the current plan.",
        },
    }
    fields["creation_reviews"] = [
        {
            "reviewer": "independent-plan-reviewer",
            "reviewed_at": "2026-07-26T13:30:00+08:00",
            "subject_version": 1,
            "scope": "Current plan",
            "conclusion": "pass",
        }
    ]
    return fields


def _v1_workcase() -> dict[str, object]:
    fields = _v2_workcase()
    fields.update(
        {
            "created_at": "2026-07-20T08:00:00+08:00",
            "updated_at": "2026-07-20T09:00:00+08:00",
            "workcase_profile": "control-contract-v1",
            "audit_summary": [
                {
                    "audit_id": "audit-01",
                    "subject_kind": "pre_creation_plan",
                    "subject_version": 1,
                    "review_count": 1,
                    "summary": "The initial plan was reviewed.",
                }
            ],
        }
    )
    fields["work_items"][0]["approach_summary"] = "Use the bounded implementation path."
    fields["execution_approval"]["approved_at"] = "2026-07-20T08:45:00+08:00"
    review = fields["creation_reviews"][0]
    review.update(
        {
            "reviewed_at": "2026-07-20T08:30:00+08:00",
            "feedback": ["The plan is coherent."],
            "controller_resolution": "Accepted.",
            "review_basis": {
                "projection_key": "plan_current",
                "subject_fingerprint": workcase_subject_fingerprint(fields, "plan_current"),
            },
        }
    )
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


def test_v2_workcase_omits_process_history_top_resume_and_redundant_approach(
    current_specs_repository: Path,
) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    fields = _v2_workcase()

    assert validate_fact_object("workcase", fields, schema) == ()


def test_workcase_template_keys_are_unique_nonempty_strings(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    for invalid in ([""], [3], ["template-a", 3], ["template-a", "template-a"]):
        fields = _v2_workcase()
        fields["work_items"][0]["template_keys"] = invalid
        issues = validate_fact_object("workcase", fields, schema)
        assert any(issue.field_path == "work_items[0].template_keys" for issue in issues)


def test_workcase_approval_source_refs_use_the_shared_reference_shape(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    valid = _v2_workcase()
    valid.update(
        {
            "phase": "executing",
            "execution_approval": {
                "subject_version": 1,
                "approved_at": "2026-07-26T13:55:00+08:00",
                "summary": "Human approved the current plan",
                "source_refs": [
                    {
                        "kind": "human-input",
                        "locator": "turn-1",
                        "observed_at": "2026-07-26T13:54:00+08:00",
                        "details": {"scope": "plan-version-1"},
                    }
                ],
            },
        }
    )
    valid.pop("waiting_on", None)
    assert validate_fact_object("workcase", valid, schema) == ()

    invalid_references = (
        [3],
        [{"kind": "human-input", "locator": "turn-1", "extra": True}],
        [{"kind": "human-input"}],
        [{"kind": "human-input", "locator": "turn-1", "observed_at": "not-a-time"}],
        [{"kind": "human-input", "locator": "turn-1", "details": "not-an-object"}],
    )
    for approval_name in ("execution_approval", "closure_approval"):
        for references in invalid_references:
            fields = deepcopy(valid)
            fields[approval_name] = {
                "subject_version": 1,
                "approved_at": "2026-07-26T13:55:00+08:00",
                "summary": "Human approval",
                "source_refs": references,
            }
            if approval_name == "closure_approval":
                fields["result_version"] = 1
            issues = validate_fact_object("workcase", fields, schema)
            assert any(
                issue.field_path is not None and issue.field_path.startswith(f"{approval_name}.source_refs[")
                for issue in issues
            )


def test_v2_forbids_v1_process_fields_and_review_basis(
    current_specs_repository: Path,
) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    for field_name, value in {
        "audit_summary": [{"audit_id": "audit-01"}],
        "progress_history": {"coverage": "full", "entries": []},
        "improvement_observations": [{"observation_id": "observation-01"}],
        "nonbinding_followups": [{"followup_id": "followup-01"}],
    }.items():
        fields = _v2_workcase()
        fields[field_name] = value
        issues = validate_fact_object("workcase", fields, schema)
        assert any(issue.field_path == field_name for issue in issues)

    fields = _v2_workcase()
    fields["creation_reviews"][0]["review_basis"] = {
        "projection_key": "plan_current",
        "subject_fingerprint": "0" * 64,
    }
    issues = validate_fact_object("workcase", fields, schema)
    assert any(issue.field_path.endswith("review_basis") for issue in issues)


def test_v2_boundary_rejects_v1_at_the_exact_effective_instant(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    fields = _v2_workcase()
    fields["created_at"] = "2026-07-26T12:45:00+08:00"
    fields["workcase_profile"] = "control-contract-v1"
    fields["audit_summary"] = [
        {
            "audit_id": "audit-01",
            "subject_kind": "pre_creation_plan",
            "subject_version": 1,
            "review_count": 1,
            "summary": "Compatibility fixture.",
        }
    ]

    issues = validate_fact_object("workcase", fields, schema)
    assert any(issue.field_path == "workcase_profile" and "V2 生效边界" in issue.summary for issue in issues)


@pytest.mark.parametrize(
    ("fields", "created_at", "required_profile"),
    (
        (_v1_workcase(), "2026-07-20T07:30:00+08:00", "control-contract-v1"),
        (_v2_workcase(), "2026-07-26T12:45:00+08:00", "control-contract-v2"),
    ),
)
def test_missing_profile_reports_the_value_required_by_created_at(
    current_specs_repository: Path,
    fields: dict[str, object],
    created_at: str,
    required_profile: str,
) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    fields = deepcopy(fields)
    fields["created_at"] = created_at
    fields.pop("workcase_profile")

    issues = validate_fact_object("workcase", fields, schema)

    assert any(issue.field_path == "workcase_profile" and required_profile in issue.summary for issue in issues)


def test_v2_is_valid_at_the_exact_effective_instant(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    fields = _v2_workcase()
    fields["created_at"] = "2026-07-26T12:45:00+08:00"

    assert validate_fact_object("workcase", fields, schema) == ()


def test_v1_keeps_approach_and_feedback_required_after_registry_fields_become_conditional(
    current_specs_repository: Path,
) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    baseline = _v1_workcase()
    assert validate_fact_object("workcase", baseline, schema) == ()

    missing_approach = _v1_workcase()
    missing_approach["work_items"][0].pop("approach_summary")
    issues = validate_fact_object("workcase", missing_approach, schema)
    assert any(issue.field_path == "work_items[0].approach_summary" for issue in issues)

    missing_feedback = _v1_workcase()
    missing_feedback["creation_reviews"][0].pop("feedback")
    issues = validate_fact_object("workcase", missing_feedback, schema)
    assert any(issue.field_path == "creation_reviews[0].feedback" for issue in issues)


def test_v2_review_feedback_and_resolution_follow_the_conclusion_and_phase(
    current_specs_repository: Path,
) -> None:
    schema = _schemas(current_specs_repository)["workcase"]
    empty_feedback = _v2_workcase()
    empty_feedback["creation_reviews"][0]["feedback"] = []
    issues = validate_fact_object("workcase", empty_feedback, schema)
    assert any(issue.field_path == "creation_reviews[0].feedback" for issue in issues)

    resolution_without_feedback = _v2_workcase()
    resolution_without_feedback["creation_reviews"][0]["controller_resolution"] = "Nothing to resolve."
    issues = validate_fact_object("workcase", resolution_without_feedback, schema)
    assert any(issue.field_path == "creation_reviews[0].controller_resolution" for issue in issues)

    fields = _v2_workcase()
    fields["creation_reviews"][0]["conclusion"] = "changes_required"
    issues = validate_fact_object("workcase", fields, schema)
    assert any(issue.field_path == "creation_reviews[0].feedback" for issue in issues)

    fields["creation_reviews"][0]["feedback"] = ["Clarify one plan boundary."]
    issues = validate_fact_object("workcase", fields, schema)
    assert any(issue.field_path == "creation_reviews[0].controller_resolution" for issue in issues)

    fields["creation_reviews"][0]["controller_resolution"] = "Accepted and clarified."
    assert validate_fact_object("workcase", fields, schema) == ()

    reviewing = _v2_workcase()
    reviewing.update(
        {
            "phase": "independent_reviewing",
            "result_version": 1,
            "controller_check_summary": "The current result was checked.",
            "success_criterion_results": [
                {
                    "criterion_id": "criterion-01",
                    "outcome": "satisfied",
                    "summary": "The current result satisfies the criterion.",
                }
            ],
            "result_reviews": [
                {
                    "reviewer": "independent-result-reviewer",
                    "reviewed_at": "2026-07-26T13:50:00+08:00",
                    "subject_version": 1,
                    "scope": "Current result",
                    "conclusion": "blocked",
                    "feedback": ["One result issue needs Controller disposition."],
                }
            ],
        }
    )
    reviewing["work_items"] = [
        {
            "item_id": "item-01",
            "goal": "Produce the result.",
            "expected_result": "One verified result.",
            "status": "completed",
            "result_summary": "The result was produced.",
        }
    ]
    assert validate_fact_object("workcase", reviewing, schema) == ()

    left_review = {**reviewing, "phase": "controller_checking"}
    issues = validate_fact_object("workcase", left_review, schema)
    assert any(issue.field_path == "result_reviews[0].controller_resolution" for issue in issues)
