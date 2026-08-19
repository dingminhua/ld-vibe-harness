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
    assert len(inspection.structures) == 22
    assert len(inspection.registrations) == 171
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


def test_conditional_object_id_binding_is_allowed_for_uid_native_objects(current_specs_repository: Path) -> None:
    spark = current_specs_repository / "specs/20-Spark-火花.md"
    text = spark.read_text(encoding="utf-8")
    spark.write_text(
        text.replace(
            "| `object-id` | required | `spark-fact-type::5. Spark 类型定义` |",
            "| `object-id` | required | `spark-fact-type::5. Spark 类型定义` |",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is True


def test_workcase_current_structures_have_admission_records(
    current_specs_repository: Path,
) -> None:
    inspection = _inspection(current_specs_repository)
    workcase = (current_specs_repository / "specs/21-WorkCase-工作项.md").read_text(encoding="utf-8")
    workcase_structures = {
        item.structure_key for item in inspection.structures if item.applies_to == ("workcase",)
    }

    assert workcase_structures == {
        "workcase-item",
        "workcase-execution-authorization",
        "workcase-authorized-action",
        "workcase-quality-gate",
        "workcase-review",
        "workcase-human-approval",
        "workcase-success-criterion",
        "workcase-success-result",
        "workcase-closure-proposal",
        "workcase-residual-decision",
        "workcase-proposed-route-target",
        "workcase-residual-responsibility",
            "workcase-spark-suggestion",
            "workcase-termination",
        }
    assert workcase.count("### workcase 结构准入记录") == 1
    for structure_key in (
        "workcase-closure-proposal",
        "workcase-residual-decision",
        "workcase-proposed-route-target",
        "workcase-residual-responsibility",
        "workcase-spark-suggestion",
        "workcase-execution-authorization",
        "workcase-authorized-action",
        "workcase-quality-gate",
        "workcase-review",
        "workcase-human-approval",
    ):
        assert f"| `{structure_key}` |" in workcase


def test_workcase_current_optional_members_are_conditionally_projected(
    current_specs_repository: Path,
) -> None:
    inspection = _inspection(current_specs_repository)
    registrations = {item.field_key: item for item in inspection.registrations}
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]
    projected = {item.path: item for item in schema.fields}

    assert registrations["workcase-item-approach-summary"].base_presence == "conditional"
    assert registrations["workcase-review-feedback"].base_presence == "conditional"
    assert registrations["workcase-authorization-human-prerequisites"].base_presence == "conditional"
    assert registrations["workcase-approval-baseline-fingerprint"].base_presence == "required"
    assert registrations["workcase-approval-source-refs"].base_presence == "required"
    assert registrations["workcase-proposal-residual-decisions"].base_presence == "conditional"
    assert registrations["workcase-residual-decision-route-target"].base_presence == "conditional"
    for field_path in (
        "work_items[].approach_summary",
        "execution_authorization.human_prerequisites",
        "creation_reviews[].feedback",
        "result_reviews[].feedback",
        "closure_proposal.residual_decisions",
        "closure_proposal.residual_decisions[].route_target",
        "residual_responsibilities",
    ):
        assert projected[field_path].presence == "conditional"
    for field_key in (
        "workcase-overall-result-summary",
        "workcase-closure-proposal",
        "workcase-closure-outcome",
        "workcase-residual-responsibilities",
    ):
        assert registrations[field_key].status == "current"
    for field_path in (
        "result_summary",
        "closure_proposal",
        "closure_outcome",
        "residual_responsibilities",
    ):
        assert projected[field_path].presence == "conditional"


def test_change_log_signature_registration_carries_value_convention(
    current_specs_repository: Path,
) -> None:
    """取值约定以规范投影机械回指：05.Att.01 的 change-log-signature 相关行须含取值约定与注入责任。"""

    inspection = _inspection(current_specs_repository)
    registrations = {item.field_key: item for item in inspection.registrations}
    for field_key in (
        "change-log-signature",
        "change-log-signature-product-name",
        "change-log-signature-model-name",
    ):
        assert registrations[field_key].status == "current"
    assert registrations["change-log-signature-agent-runtime-name"].status == "retired"
    text = (current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md").read_text(
        encoding="utf-8"
    )
    assert "取值约定" in text
    assert "模型名称" in text
    assert "禁止" in text and "重复" in text
    assert "产品名称" in text
