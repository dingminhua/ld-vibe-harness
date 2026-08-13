"""Shared parsing and configuration-wide resolution for stable fact references."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.facts.configuration_index import ConfigurationFactIndex
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.identity import canonical_object_uid
from ldvh.facts.models import FactReference, StableFactReference, UIDFactReference
from ldvh.facts.schema import FactSchema
from ldvh.governance.resolver import GovernanceResolutionRun
from ldvh.helper.operations.fact_operation_support import configuration_reading_boundaries, reading_boundary


def parse_stable_fact_reference(value: object, path: str) -> tuple[StableFactReference | None, list[str]]:
    if not isinstance(value, dict):
        return None, [f"{path} 必须是 object"]
    if "object_uid" in value:
        problems = []
        unknown = sorted(set(value) - {"object_uid"})
        if unknown:
            problems.append(f"{path} 包含未知字段: {', '.join(unknown)}")
        object_uid = canonical_object_uid(value.get("object_uid"))
        if object_uid is None:
            problems.append(f"{path}.object_uid 必须是 canonical 小写 UUIDv7")
            return None, problems
        return UIDFactReference(object_uid), problems
    fields = {"governed_project_id", "fact_type_key", "object_id"}
    problems = []
    unknown = sorted(set(value) - fields)
    missing = sorted(fields - set(value))
    if unknown:
        problems.append(f"{path} 包含未知字段: {', '.join(unknown)}")
    if missing:
        problems.append(f"{path} 缺少 legacy 字段: {', '.join(missing)}")
        return None, problems
    if any(not isinstance(value.get(name), str) or not value[name].strip() for name in fields):
        problems.append(f"{path} legacy 三元组的每个成员必须是非空 string")
        return None, problems
    fact_type_key = str(value["fact_type_key"])
    layout = LAYOUTS.get(fact_type_key)
    if layout is None or layout.object_id_pattern.fullmatch(str(value["object_id"])) is None:
        problems.append(f"{path} 未形成当前事实类型的合法 legacy 引用")
        return None, problems
    return FactReference(str(value["governed_project_id"]), fact_type_key, str(value["object_id"])), problems


@dataclass(frozen=True, slots=True)
class ResolvedFactReference:
    reference: FactReference
    boundary: CreationBoundary


def resolve_stable_fact_reference(
    run: GovernanceResolutionRun,
    reference: StableFactReference,
    schemas: dict[str, FactSchema],
) -> tuple[ResolvedFactReference | None, str]:
    boundaries = configuration_reading_boundaries(run)
    if isinstance(reference, FactReference):
        match = next(
            (item for item in boundaries or () if item[0] == reference.governed_project_id),
            None,
        )
        if match is None:
            current = reading_boundary(run)
            if current is not None and current[0] == reference.governed_project_id:
                match = current
        if match is None:
            return None, "unavailable" if boundaries is None else "not_found"
        return ResolvedFactReference(reference, CreationBoundary(*match)), "resolved"
    if boundaries is None:
        return None, "unavailable"
    entry, status = ConfigurationFactIndex(boundaries, schemas).resolve_uid(reference.object_uid)
    if entry is None:
        return None, status
    return (
        ResolvedFactReference(
            FactReference(entry.governed_project_id, entry.fact_type_key, entry.object_id),
            CreationBoundary(entry.governed_project_id, entry.root, entry.common_dir),
        ),
        "resolved",
    )


__all__ = ["ResolvedFactReference", "parse_stable_fact_reference", "resolve_stable_fact_reference"]
