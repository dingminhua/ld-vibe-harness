from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ldvh.facts.creation import schema_fingerprint
from ldvh.facts.schema import FactSchema, project_fact_schemas
from ldvh.specs.repository import inspect_repository


def test_projected_field_retains_constraint_ref_and_fingerprint_covers_it(
    current_specs_repository: Path,
) -> None:
    schema = project_fact_schemas(inspect_repository(current_specs_repository))["workcase"]
    resume_from = next(field for field in schema.fields if field.path == "resume_from")

    assert resume_from.presence == "conditional"
    assert resume_from.constraint_ref == "workcase-fact-type::6. 对象语义与生命周期"

    changed_fields = tuple(
        replace(field, constraint_ref="workcase-fact-type::changed") if field.path == "resume_from" else field
        for field in schema.fields
    )
    changed_schema = FactSchema(schema.fact_type_key, changed_fields)
    assert schema_fingerprint(changed_schema) != schema_fingerprint(schema)
