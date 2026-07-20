from __future__ import annotations

from pathlib import Path

from ldvh.specs.field_registry import inspect_field_registry
from ldvh.specs.repository import inspect_repository


def _inspection(repository: Path):
    source = inspect_repository(repository)
    return inspect_field_registry(source.parsed_documents)


def test_current_registry_is_complete_and_resolves_all_current_types(current_specs_repository: Path) -> None:
    inspection = _inspection(current_specs_repository)

    assert inspection.complete is True
    assert len(inspection.structures) == 16
    assert len(inspection.registrations) == 126
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
