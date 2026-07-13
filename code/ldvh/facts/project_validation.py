"""Stabilize project-wide fact checks without request-order dependence."""

from __future__ import annotations

from dataclasses import replace

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactIssue
from ldvh.facts.relations import ProjectFactIndex, validate_project_relations
from ldvh.facts.repository import FactReadResult
from ldvh.facts.source_validation import validate_study_sources


def stabilize_project_index(index: ProjectFactIndex) -> None:
    """Evaluate relation and Study-source checks until the project-backed status stabilizes."""

    base_reads = {
        key: read
        for key, read in index.cache.items()
        if read.check_status == "mechanically_valid" and read.fields is not None
    }
    for fact_type_key in LAYOUTS:
        reads, _ = index.scan_valid_objects(fact_type_key)
        for read in reads:
            if read.fields is not None and isinstance(read.fields.get("object_id"), str):
                base_reads[(fact_type_key, read.fields["object_id"])] = read

    for _ in range(len(base_reads) + 1):
        evaluated: dict[tuple[str, str], FactReadResult] = {}
        for (fact_type_key, object_id), base_read in base_reads.items():
            current = index.cache.get((fact_type_key, object_id))
            if current is not None and current.check_status != "mechanically_valid":
                evaluated[(fact_type_key, object_id)] = current
                continue
            relation_issues, relation_unavailable = validate_project_relations(
                index,
                fact_type_key,
                object_id,
                base_read,
            )
            source_issues: tuple[FactIssue, ...] = ()
            source_unavailable = False
            if fact_type_key == "study":
                source_issues, source_unavailable = validate_study_sources(index, base_read)
            project_issues = (*relation_issues, *source_issues)
            if relation_unavailable or source_unavailable:
                evaluated[(fact_type_key, object_id)] = replace(
                    base_read,
                    check_status="unavailable",
                    issues=(
                        *base_read.issues,
                        *project_issues,
                        FactIssue("reference", "项目级关系或来源集合未能完成必需机械检查"),
                    ),
                )
            elif project_issues:
                evaluated[(fact_type_key, object_id)] = replace(
                    base_read,
                    check_status="invalid",
                    issues=(*base_read.issues, *project_issues),
                )
            else:
                evaluated[(fact_type_key, object_id)] = base_read
        if all(index.cache.get(key) == value for key, value in evaluated.items()):
            return
        index.cache.update(evaluated)

    for key, base_read in base_reads.items():
        index.cache[key] = replace(
            base_read,
            check_status="unavailable",
            issues=(*base_read.issues, FactIssue("relation", "项目级关系校验未能收敛")),
        )


__all__ = ["stabilize_project_index"]
