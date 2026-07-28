from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.validation import parse_rfc3339, validate_fact_object
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


@pytest.mark.parametrize(
    "value",
    [
        "2026-07-27T10:20:30Z",
        "2026-07-27T10:20:30+08:00",
        "2026-07-27T10:20:30.123456-03:30",
        "2026-07-27T10:20:30.12345678901234567890+08:00",
        "0001-01-01T00:00:00+23:59",
        "9999-12-31T23:59:59-23:59",
    ],
)
def test_common_timestamp_parser_accepts_regular_rfc3339_forms(value: str) -> None:
    assert parse_rfc3339(value) is not None


@pytest.mark.parametrize(
    "value",
    [
        "2026-W30-1T10:20:30+08:00",
        "20260727T102030+08:00",
        "2026-07-27T10:20:30+0800",
        "2026-07-27T10:20:30+08:00:30",
        "2026-07-27T10:20:30+08:60",
        "2026-02-30T10:20:30+08:00",
        "2026-07-27T24:00:00+08:00",
        "2026-07-27T10:60:00+08:00",
        "2026-07-27T10:20:60+08:00",
        "2026-07-27T10:20:30-00:00",
        " 2026-07-27T10:20:30+08:00 ",
    ],
)
def test_common_timestamp_parser_rejects_noncanonical_or_invalid_components(value: str) -> None:
    assert parse_rfc3339(value) is None


@pytest.mark.parametrize(
    ("fact_type_key", "object_id", "status"),
    [
        ("spark", "spark-0001", "open"),
        ("workcase", "workcase-0001", "open"),
        ("adr", "adr-0001", "active"),
        ("pitfall", "pitfall-0001", "active"),
        ("study", "study-0001", "active"),
    ],
)
def test_all_fact_types_reject_unknown_local_offset_in_managed_timestamps(
    current_specs_repository: Path,
    fact_type_key: str,
    object_id: str,
    status: str,
) -> None:
    fields = _common(fact_type_key, object_id, status)
    fields["created_at"] = "2026-07-14T09:00:00-00:00"
    fields["updated_at"] = "2026-07-14T10:00:00-00:00"

    issues = validate_fact_object(
        fact_type_key,
        fields,
        _schemas(current_specs_repository)[fact_type_key],
    )

    invalid_time_paths = {
        issue.field_path for issue in issues if issue.summary == "时间必须是包含 UTC 偏移的 RFC 3339 string"
    }
    assert invalid_time_paths == {"created_at", "updated_at"}


@pytest.mark.parametrize(
    ("earlier", "later"),
    [
        (
            "2026-07-27T10:20:30.1234567+08:00",
            "2026-07-27T10:20:30.1234568+08:00",
        ),
        (
            "2026-07-27T02:20:30.12345678901234567890Z",
            "2026-07-27T10:20:30.12345678901234567891+08:00",
        ),
    ],
)
def test_common_timestamp_parser_orders_arbitrary_fractional_precision_losslessly(
    earlier: str,
    later: str,
) -> None:
    parsed_earlier = parse_rfc3339(earlier)
    parsed_later = parse_rfc3339(later)

    assert parsed_earlier is not None and parsed_later is not None
    assert parsed_earlier < parsed_later
    assert parsed_later > parsed_earlier


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (
            "2026-07-27T10:20:30.1+08:00",
            "2026-07-27T10:20:30.10000000000000000000+08:00",
        ),
        (
            "2026-07-27T10:20:30.12345678901234567890+08:00",
            "2026-07-27T02:20:30.123456789012345678900Z",
        ),
    ],
)
def test_common_timestamp_parser_treats_trailing_zero_and_offset_equivalents_as_equal(
    left: str,
    right: str,
) -> None:
    assert parse_rfc3339(left) == parse_rfc3339(right)


def test_common_timestamp_parser_compares_more_than_python_integer_digit_limit() -> None:
    earlier = parse_rfc3339(f"2026-07-27T10:20:30.{('0' * 4_999)}1+08:00")
    later = parse_rfc3339(f"2026-07-27T10:20:30.{('0' * 4_999)}2+08:00")

    assert earlier is not None and later is not None
    assert earlier < later


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


def test_spark_evolution_accepts_twenty_entries_and_rejects_twenty_one(
    current_specs_repository: Path,
) -> None:
    schema = _schemas(current_specs_repository)["spark"]
    fields = {
        **_common("spark", "spark-0001", "open"),
        "summary": "A current bounded question.",
        "priority": "P2",
        "evolution": [
            {
                "at": "2026-07-14T09:30:00+08:00",
                "summary": f"Key semantic transition {index + 1}.",
            }
            for index in range(20)
        ],
    }

    assert validate_fact_object("spark", fields, schema) == ()

    fields["evolution"].append(
        {
            "at": "2026-07-14T09:30:00+08:00",
            "summary": "Key semantic transition 21.",
        }
    )
    issues = validate_fact_object("spark", fields, schema)

    assert any(issue.field_path == "evolution" and "最多保留 20 项" in issue.summary for issue in issues)


def test_unregistered_reference_fields_are_rejected(current_specs_repository: Path) -> None:
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


def test_pitfall_status_contract_has_only_draft_active_and_discarded(current_specs_repository: Path) -> None:
    schema = _schemas(current_specs_repository)["pitfall"]
    fields = {
        **_common("pitfall", "pitfall-0001", "retired"),
        "applicability": "Only the observed environment.",
        "validation_summary": "The bounded handling was verified.",
        "symptoms": "The declared operation did not run.",
        "trigger_conditions": "The required runtime input was absent.",
        "root_cause": "The runtime could not locate its required input.",
        "resolution": "Restore the required input and rerun the operation.",
        "avoidance": "Check the required input before relying on the operation.",
        "disposition_summary": "The experience no longer applies.",
    }

    issues = validate_fact_object("pitfall", fields, schema)

    assert any(issue.field_path == "status" and "discarded" in issue.summary for issue in issues)


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
