from __future__ import annotations

from pathlib import Path

from ldvh.facts.schema import project_fact_schemas
from ldvh.specs.field_registry import inspect_field_registry
from ldvh.specs.repository import inspect_repository


def _inspection(repository: Path):
    source = inspect_repository(repository)
    return inspect_field_registry(source.parsed_documents)


def test_current_registry_is_complete_and_resolves_all_current_types(current_specs_repository: Path) -> None:
    inspection = _inspection(current_specs_repository)

    assert inspection.complete is True
    assert len(inspection.structures) == 18
    assert len(inspection.registrations) == 130
    assert {item.fact_type_key for item in inspection.fact_types} == {
        "spark",
        "workcase",
        "adr",
        "pitfall",
        "study",
    }


def test_duplicate_field_key_is_rejected(current_specs_repository: Path) -> None:
    registry = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    text = registry.read_text(encoding="utf-8")
    duplicate = (
        "| `object-id` | `fact-object` | `alternate_object_id` | string | object-field | `none` | "
        "required | foundation | `*` | "
        "`fact-object-field-registry::公共顶层字段::object-id` | current |\n"
    )
    registry.write_text(text.replace("| `fact-type-key`", duplicate + "| `fact-type-key`", 1), encoding="utf-8")

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any("重复 field_key 'object-id'" == issue.summary for issue in inspection.issues)


def test_required_foundation_field_cannot_be_weakened_by_type_binding(current_specs_repository: Path) -> None:
    spark = current_specs_repository / "specs/20-Spark-火花.md"
    text = spark.read_text(encoding="utf-8")
    spark.write_text(
        text.replace(
            "| `object-id` | required | `spark-fact-type::5. Spark 类型定义` |",
            "| `object-id` | conditional | `spark-fact-type::5. Spark 类型定义` |",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any("基础必填字段 'object-id' 必须绑定为 required" == issue.summary for issue in inspection.issues)


def test_workcase_v1_progress_structures_keep_compatibility_admission_records(
    current_specs_repository: Path,
) -> None:
    registry = (current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md").read_text(
        encoding="utf-8"
    )
    workcase = (current_specs_repository / "specs/21-WorkCase-工作项.md").read_text(encoding="utf-8")

    assert "| information_need | compared_structure_keys | decision | resulting_structure_key | rationale |" in registry
    obsolete_header = (
        "| information_need | compared_structure_keys | decision | resulting_structure_key | rationale | review_ref |"
    )
    assert obsolete_header not in registry
    assert workcase.count("### workcase 结构准入记录") == 1
    assert "| `differentiate` | `workcase-progress-history` |" in workcase
    assert "| `differentiate` | `workcase-progress-entry` |" in workcase


def test_workcase_v2_optional_members_are_conditional_while_v1_compatibility_fields_remain_registered(
    current_specs_repository: Path,
) -> None:
    inspection = _inspection(current_specs_repository)
    registrations = {item.field_key: item for item in inspection.registrations}
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]
    projected = {item.path: item for item in schema.fields}

    assert registrations["workcase-item-approach-summary"].base_presence == "conditional"
    assert registrations["workcase-review-feedback"].base_presence == "conditional"
    assert registrations["workcase-review-basis-member"].base_presence == "conditional"
    for field_path in (
        "work_items[].approach_summary",
        "creation_reviews[].feedback",
        "result_reviews[].feedback",
        "creation_reviews[].review_basis",
        "result_reviews[].review_basis",
    ):
        assert projected[field_path].presence == "conditional"
    for field_key in (
        "workcase-audit-summary",
        "workcase-progress-history",
        "workcase-improvement-observations",
        "workcase-nonbinding-followups",
    ):
        assert registrations[field_key].status == "current"
    for field_path in (
        "audit_summary",
        "progress_history",
        "improvement_observations",
        "nonbinding_followups",
    ):
        assert projected[field_path].presence == "conditional"
