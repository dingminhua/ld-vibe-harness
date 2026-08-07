"""L0-L2 projections derived from checked specification identities and relations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from ldvh.diagnostics import SourceLocation
from ldvh.specs.graph import GraphResult
from ldvh.specs.identity import FormalDocument

DisclosureLayer = Literal["L0", "L1", "L2"]


@dataclass(frozen=True, slots=True)
class ProjectionItem:
    layer: DisclosureLayer
    key: str
    kind: str
    path: str
    content: Mapping[str, object]
    source: SourceLocation
    source_references: Mapping[str, tuple[SourceLocation, ...]]


def _freeze(values: dict[str, object]) -> Mapping[str, object]:
    return MappingProxyType(values)


def _freeze_sources(values: dict[str, tuple[SourceLocation, ...]]) -> Mapping[str, tuple[SourceLocation, ...]]:
    return MappingProxyType(values)


def _field_source(document: FormalDocument, field_name: str) -> SourceLocation:
    return document.field_locations.get(
        field_name,
        SourceLocation(document.canonical_path, document.markdown.yaml_line),
    )


def _optional_field_sources(document: FormalDocument, field_name: str) -> tuple[SourceLocation, ...]:
    location = document.field_locations.get(field_name)
    return () if location is None else (location,)


def _target_mapping(key: str, target_paths: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType({"key": key, "path": target_paths[key]})


def _target_mappings(keys: tuple[str, ...], target_paths: Mapping[str, str]) -> tuple[Mapping[str, str], ...]:
    return tuple(_target_mapping(key, target_paths) for key in keys)


def _l0(document: FormalDocument) -> ProjectionItem:
    key_field = "attachment_key" if document.kind == "attachment" else "spec_key"
    id_field = "attachment_id" if document.kind == "attachment" else "spec_id"
    sources = {
        "key": (_field_source(document, key_field),),
        "id": (_field_source(document, id_field),),
        "title": (_field_source(document, "title"),),
        "status": (_field_source(document, "status"),),
        "path": (_field_source(document, "canonical_path"),),
    }
    return ProjectionItem(
        layer="L0",
        key=document.key,
        kind=document.kind,
        path=document.canonical_path,
        content=_freeze(
            {
                "key": document.key,
                "id": document.current_id,
                "title": document.title,
                "status": document.status,
                "path": document.canonical_path,
            }
        ),
        source=sources["key"][0],
        source_references=_freeze_sources(sources),
    )


def _l1(document: FormalDocument) -> ProjectionItem:
    content: dict[str, object] = {"positioning": document.positioning}
    sources = {"positioning": (_field_source(document, "positioning"),)}
    if document.scope is not None:
        content["scope"] = document.scope
        sources["scope"] = (_field_source(document, "scope"),)
    return ProjectionItem(
        layer="L1",
        key=document.key,
        kind=document.kind,
        path=document.canonical_path,
        content=_freeze(content),
        source=sources["positioning"][0],
        source_references=_freeze_sources(sources),
    )


def _l2(
    document: FormalDocument,
    attachment_parents: Mapping[str, str],
    documents_by_key: Mapping[str, FormalDocument],
    target_paths: Mapping[str, str],
) -> ProjectionItem:
    content: dict[str, object]
    sources: dict[str, tuple[SourceLocation, ...]]
    if document.kind == "attachment":
        parent_key = attachment_parents.get(document.key)
        parent = documents_by_key.get(parent_key) if parent_key is not None else None
        content = {
            "parent_spec": None if parent_key is None else _target_mapping(parent_key, target_paths),
            "supersedes": _target_mappings(document.supersedes, target_paths),
        }
        sources = {
            "parent_spec": (
                _field_source(parent, "authorized_attachments")
                if parent is not None
                else SourceLocation(document.canonical_path, document.markdown.yaml_line),
            ),
            "supersedes": _optional_field_sources(document, "supersedes"),
        }
    else:
        content = {
            "basis": _target_mappings(document.basis, target_paths),
            "parent_spec": (
                None if document.parent_spec is None else _target_mapping(document.parent_spec, target_paths)
            ),
            "relation": document.relation,
            "authorized_attachments": _target_mappings(document.authorized_attachments, target_paths),
            "supersedes": _target_mappings(document.supersedes, target_paths),
        }
        sources = {
            "basis": (_field_source(document, "basis"),),
            "parent_spec": _optional_field_sources(document, "parent_spec"),
            "relation": _optional_field_sources(document, "relation"),
            "authorized_attachments": (
                _optional_field_sources(document, "authorized_attachments")
                if document.kind == "root"
                else (_field_source(document, "authorized_attachments"),)
            ),
            "supersedes": _optional_field_sources(document, "supersedes"),
        }
    return ProjectionItem(
        layer="L2",
        key=document.key,
        kind=document.kind,
        path=document.canonical_path,
        content=_freeze(content),
        source=next(iter(sources.values()))[0],
        source_references=_freeze_sources(sources),
    )


def project_l0_l2(graph: GraphResult) -> tuple[ProjectionItem, ...]:
    """Create L0-L2 items for active documents that passed the implemented checks."""

    attachment_parents = dict(graph.attachment_parents)
    documents_by_key = {document.key: document for document in graph.active_documents_passing_implemented_checks}
    target_paths = dict(graph.relationship_target_paths)
    projections: list[ProjectionItem] = []
    for document in graph.active_documents_passing_implemented_checks:
        projections.extend(
            (
                _l0(document),
                _l1(document),
                _l2(document, attachment_parents, documents_by_key, target_paths),
            )
        )
    return tuple(projections)
