from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from ldvh.facts.creation import schema_fingerprint
from ldvh.facts.schema import FactSchema


def test_projected_field_retains_definition_and_constraint_refs_and_fingerprint_covers_them(
    current_fact_schemas: Mapping[str, FactSchema],
) -> None:
    schema = current_fact_schemas["workcase"]
    resume_from = next(field for field in schema.fields if field.path == "resume_from")

    assert resume_from.presence == "conditional"
    assert resume_from.definition_ref == (
        "workcase-fact-type::5. WorkCase 类型定义::workcase-resume-from"
    )
    assert resume_from.constraint_ref == "workcase-fact-type::6. 状态、阶段与生命周期"

    changed_constraint_fields = tuple(
        replace(field, constraint_ref="workcase-fact-type::changed") if field.path == "resume_from" else field
        for field in schema.fields
    )
    changed_constraint_schema = FactSchema(schema.fact_type_key, changed_constraint_fields)
    assert schema_fingerprint(changed_constraint_schema) != schema_fingerprint(schema)

    changed_definition_fields = tuple(
        replace(field, definition_ref="workcase-fact-type::5. WorkCase 类型定义::changed")
        if field.path == "resume_from"
        else field
        for field in schema.fields
    )
    changed_definition_schema = FactSchema(schema.fact_type_key, changed_definition_fields)
    assert schema_fingerprint(changed_definition_schema) != schema_fingerprint(schema)
