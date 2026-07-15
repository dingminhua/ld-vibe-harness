"""Project mechanical fact schemas from the current rule source."""

from __future__ import annotations

from dataclasses import dataclass

from ldvh.specs.fact_type_projection import project_fact_type_fields
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
    registry = repository.field_registry
    if registry is None or not registry.complete:
        return {}
    grouped: dict[str, list[ProjectedField]] = {}
    for field in project_fact_type_fields(registry):
        grouped.setdefault(field.fact_type_key, []).append(
            ProjectedField(field.field_path, field.json_type, field.presence, field.value_structure)
        )
    return {key: FactSchema(key, tuple(fields)) for key, fields in grouped.items()}


__all__ = ["FactSchema", "ProjectedField", "project_fact_schemas"]
