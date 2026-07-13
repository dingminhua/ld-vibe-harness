"""Project mechanical fact schemas from the current rule source."""

from __future__ import annotations

from dataclasses import dataclass

from ldvh.specs.fact_type_projection import project_fact_type_fields
from ldvh.specs.field_registry import ADMISSION_AUDIT_PATH, inspect_field_registry
from ldvh.specs.markdown import parse_markdown
from ldvh.specs.repository import RepositoryInspection


@dataclass(frozen=True, slots=True)
class ProjectedField:
    path: str
    json_type: str
    presence: str
    value_structure: str | None


@dataclass(frozen=True, slots=True)
class FactSchema:
    fact_type_key: str
    fields: tuple[ProjectedField, ...]

    @property
    def direct_fields(self) -> tuple[ProjectedField, ...]:
        return tuple(field for field in self.fields if "." not in field.path and "[]" not in field.path)


def project_fact_schemas(repository: RepositoryInspection) -> dict[str, FactSchema]:
    audit = parse_markdown(
        repository.repository_root / ADMISSION_AUDIT_PATH,
        ADMISSION_AUDIT_PATH,
    ).document
    registry = inspect_field_registry(
        repository.active_documents_passing_implemented_checks,
        admission_audit=audit,
    )
    if not registry.complete:
        return {}
    grouped: dict[str, list[ProjectedField]] = {}
    for field in project_fact_type_fields(registry):
        grouped.setdefault(field.fact_type_key, []).append(
            ProjectedField(field.field_path, field.json_type, field.presence, field.value_structure)
        )
    return {key: FactSchema(key, tuple(fields)) for key, fields in grouped.items()}


__all__ = ["FactSchema", "ProjectedField", "project_fact_schemas"]
