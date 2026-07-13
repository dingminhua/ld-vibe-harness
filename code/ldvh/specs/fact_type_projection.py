"""Derived, non-authoritative field views for current fact types."""

from __future__ import annotations

from dataclasses import dataclass

from ldvh.specs.field_registry import BINDING_HEADERS, FieldRegistryInspection
from ldvh.specs.markdown import parse_table_after_heading


@dataclass(frozen=True, slots=True)
class FactTypeFieldProjection:
    fact_type_key: str
    field_key: str
    field_path: str
    json_type: str
    presence: str
    value_structure: str | None
    definition_ref: str
    constraint_ref: str


def project_fact_type_fields(
    inspection: FieldRegistryInspection,
) -> tuple[FactTypeFieldProjection, ...]:
    """Combine canonical registrations and type bindings without copying semantics."""

    if not inspection.complete:
        return ()
    registrations = {item.field_key: item for item in inspection.registrations}
    members_by_structure = {
        structure.structure_key: tuple(
            item
            for item in inspection.registrations
            if item.container_ref == structure.structure_key and item.field_role == "structure-member"
        )
        for structure in inspection.structures
    }
    projected: list[FactTypeFieldProjection] = []

    def append_structure_members(
        *,
        fact_type_key: str,
        structure_key: str,
        prefix: str,
        visited: frozenset[str],
    ) -> None:
        if structure_key in visited:
            return
        next_visited = visited | {structure_key}
        for member in members_by_structure.get(structure_key, ()):
            if member.status != "current" or (member.applies_to is not None and fact_type_key not in member.applies_to):
                continue
            member_path = f"{prefix}.{member.field_path}"
            projected.append(
                FactTypeFieldProjection(
                    fact_type_key=fact_type_key,
                    field_key=member.field_key,
                    field_path=member_path,
                    json_type=member.json_type,
                    presence=member.base_presence,
                    value_structure=member.value_structure,
                    definition_ref=f"{member.definition_key}::{member.definition_heading}",
                    constraint_ref="inherit",
                )
            )
            if member.value_structure is not None:
                nested_prefix = f"{member_path}[]" if member.json_type == "array" else member_path
                append_structure_members(
                    fact_type_key=fact_type_key,
                    structure_key=member.value_structure,
                    prefix=nested_prefix,
                    visited=next_visited,
                )

    for definition in inspection.fact_types:
        headings = definition.document.markdown.find_headings("类型字段使用绑定", level=3)
        if len(headings) != 1:
            continue
        table = parse_table_after_heading(definition.document.markdown, headings[0])
        if table is None or table.headers != BINDING_HEADERS:
            continue
        for field_key, presence, constraint_ref in table.rows:
            registration = registrations[field_key]
            projected.append(
                FactTypeFieldProjection(
                    fact_type_key=definition.fact_type_key,
                    field_key=field_key,
                    field_path=registration.field_path,
                    json_type=registration.json_type,
                    presence=presence,
                    value_structure=registration.value_structure,
                    definition_ref=f"{registration.definition_key}::{registration.definition_heading}",
                    constraint_ref=constraint_ref,
                )
            )
            if registration.value_structure is not None:
                structure_prefix = (
                    f"{registration.field_path}[]" if registration.json_type == "array" else registration.field_path
                )
                append_structure_members(
                    fact_type_key=definition.fact_type_key,
                    structure_key=registration.value_structure,
                    prefix=structure_prefix,
                    visited=frozenset(),
                )
    return tuple(projected)


def render_fact_type_field_projection(items: tuple[FactTypeFieldProjection, ...]) -> str:
    """Render a compact Markdown view that can always be regenerated."""

    lines = [
        "# V4 事实类型完整字段派生视图",
        "",
        "> 本视图由统一登记与类型绑定生成，只用于快速阅读；它不是规则源、字段定义或独立 Schema 权威。",
    ]
    fact_type_keys = tuple(dict.fromkeys(item.fact_type_key for item in items))
    for fact_type_key in fact_type_keys:
        lines.extend(
            (
                "",
                f"## {fact_type_key}",
                "",
                "| field_path | field_key | JSON type | presence | value_structure | definition_ref | constraint_ref |",
                "|---|---|---|---|---|---|---|",
            )
        )
        for item in items:
            if item.fact_type_key != fact_type_key:
                continue
            value_structure = item.value_structure or "none"
            lines.append(
                f"| `{item.field_path}` | `{item.field_key}` | `{item.json_type}` | `{item.presence}` | "
                f"`{value_structure}` | `{item.definition_ref}` | `{item.constraint_ref}` |"
            )
    return "\n".join(lines) + "\n"
