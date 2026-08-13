"""Configuration-wide stable UID resolution over actual governed worktrees."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.facts.identity import canonical_object_uid
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema


@dataclass(frozen=True, slots=True)
class ConfigurationFactEntry:
    governed_project_id: str
    root: Path
    common_dir: Path
    fact_type_key: str
    object_id: str
    read: FactReadResult
    project_index: ProjectFactIndex


class ConfigurationFactIndex:
    """Resolve UIDs only after every registered project completed its scan."""

    def __init__(
        self,
        projects: tuple[tuple[str, Path, Path], ...],
        schemas: dict[str, FactSchema],
    ) -> None:
        self._indexes = tuple(
            (project_id, root, common_dir, ProjectFactIndex(root, project_id, schemas, common_dir))
            for project_id, root, common_dir in projects
        )

    @property
    def project_indexes(self) -> tuple[tuple[str, Path, Path, ProjectFactIndex], ...]:
        return self._indexes

    def prepare(self) -> bool:
        """Complete all UID scans, then bind configuration-aware relation resolution."""

        for _project_id, _root, _common_dir, index in self._indexes:
            index._scan_uid_index()
        complete = all(index.uid_scan_complete for _project_id, _root, _common_dir, index in self._indexes)
        if complete:
            for _project_id, _root, _common_dir, index in self._indexes:
                index.configuration_uid_resolver = self.resolve_uid_target
        return complete

    def resolve_uid_target(
        self,
        object_uid: str,
    ) -> tuple[tuple[str, str, str, FactReadResult] | None, str]:
        entry, status = self.resolve_uid(object_uid)
        if entry is None:
            return None, status
        return (
            entry.governed_project_id,
            entry.fact_type_key,
            entry.object_id,
            entry.read,
        ), status

    def resolve_uid(self, object_uid: str) -> tuple[ConfigurationFactEntry | None, str]:
        canonical = canonical_object_uid(object_uid)
        if canonical is None:
            return None, "invalid"
        matches: list[ConfigurationFactEntry] = []
        complete = True
        for project_id, root, common_dir, index in self._indexes:
            index._scan_uid_index()
            if not index.uid_scan_complete:
                complete = False
            for fact_type_key, object_id, read in index.uid_cache.get(canonical, ()):
                matches.append(
                    ConfigurationFactEntry(
                        project_id,
                        root,
                        common_dir,
                        fact_type_key,
                        object_id,
                        read,
                        index,
                    )
                )
        if not complete:
            return None, "unavailable"
        if len(matches) > 1:
            return None, "duplicate"
        if not matches:
            return None, "not_found"
        return matches[0], "resolved"


__all__ = ["ConfigurationFactEntry", "ConfigurationFactIndex"]
