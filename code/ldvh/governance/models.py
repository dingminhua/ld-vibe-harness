"""Immutable domain results for work-object governance resolution.

This module represents the result contract defined by specification 02.  It does
not discover configuration, inspect paths or Git, or decide Helper outcomes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

type JsonObject = Mapping[str, Any]


class ConfigStatus(StrEnum):
    VALID = "valid"
    MISSING = "missing"
    INVALID = "invalid"
    CONFLICT = "conflict"


class ObjectStatus(StrEnum):
    GOVERNED = "governed"
    NOT_GOVERNED = "not_governed"
    UNKNOWN = "unknown"


class ScopeStatus(StrEnum):
    GOVERNED_SINGLE = "governed_single"
    MULTIPLE_GOVERNED_PROJECTS = "multiple_governed_projects"
    NON_GOVERNED = "non_governed"
    SCOPE_UNKNOWN = "scope_unknown"
    MIXED_SCOPE = "mixed_scope"


class GovernedVia(StrEnum):
    PATH = "path"
    GIT_COMMON_DIR = "git.common_dir"


class LocatorSource(StrEnum):
    EXPLICIT_LOCATOR = "explicit_locator"
    CWD = "cwd"


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _freeze_references(values: Iterable[JsonObject]) -> tuple[JsonObject, ...]:
    return tuple(_freeze_json(value) for value in values)


def _references_json(values: Sequence[JsonObject]) -> list[dict[str, Any]]:
    return [_thaw_json(value) for value in values]


def _require_absolute_or_none(value: str | None, field_name: str) -> None:
    if value is not None and not Path(value).is_absolute():
        raise ValueError(f"{field_name} must be an absolute path or None")


@dataclass(frozen=True, slots=True)
class ScopeDescriptor:
    """One requested/completed/not-completed scope member from specification 02."""

    locator_index: int
    locator: str
    source: LocatorSource

    def __post_init__(self) -> None:
        if self.locator_index < 0:
            raise ValueError("locator_index must be non-negative")
        if not self.locator:
            raise ValueError("locator must be non-empty")

    def to_json(self) -> dict[str, object]:
        return {
            "locator_index": self.locator_index,
            "locator": self.locator,
            "source": self.source.value,
        }


@dataclass(frozen=True, slots=True)
class ObjectResolution:
    locator_index: int
    locator: str
    resolved_identity: str | None
    identity_evidence: tuple[JsonObject, ...]
    source: LocatorSource
    status: ObjectStatus
    governed_project_id: str | None
    registered_project_path: str | None
    governed_via: GovernedVia | None
    git_worktree_root: str | None
    git_common_dir: str | None
    source_refs: tuple[JsonObject, ...]
    unknown_reason: str | None

    def __post_init__(self) -> None:
        if self.locator_index < 0:
            raise ValueError("locator_index must be non-negative")
        if not self.locator:
            raise ValueError("locator must be non-empty")
        for field_name in (
            "resolved_identity",
            "registered_project_path",
            "git_worktree_root",
            "git_common_dir",
        ):
            _require_absolute_or_none(getattr(self, field_name), field_name)
        object.__setattr__(self, "identity_evidence", _freeze_references(self.identity_evidence))
        object.__setattr__(self, "source_refs", _freeze_references(self.source_refs))
        if not self.source_refs:
            raise ValueError("source_refs must be non-empty")

        if self.status is ObjectStatus.GOVERNED:
            if not self.identity_evidence:
                raise ValueError("governed resolution requires identity_evidence")
            if not self.governed_project_id or not self.registered_project_path or self.governed_via is None:
                raise ValueError("governed resolution requires its project and match method")
            if self.unknown_reason is not None:
                raise ValueError("governed resolution cannot have unknown_reason")
        elif self.status is ObjectStatus.NOT_GOVERNED:
            if not self.identity_evidence:
                raise ValueError("not_governed resolution requires identity_evidence")
            self._require_no_governed_match()
            if self.unknown_reason is not None:
                raise ValueError("not_governed resolution cannot have unknown_reason")
        else:
            self._require_no_governed_match()
            if not self.unknown_reason:
                raise ValueError("unknown resolution requires unknown_reason")

    def _require_no_governed_match(self) -> None:
        if any(
            value is not None for value in (self.governed_project_id, self.registered_project_path, self.governed_via)
        ):
            raise ValueError(f"{self.status.value} resolution cannot identify a governed project")

    @property
    def scope_descriptor(self) -> ScopeDescriptor:
        return ScopeDescriptor(self.locator_index, self.locator, self.source)

    def to_json(self) -> dict[str, object]:
        return {
            "locator_index": self.locator_index,
            "locator": self.locator,
            "resolved_identity": self.resolved_identity,
            "identity_evidence": _references_json(self.identity_evidence),
            "source": self.source.value,
            "status": self.status.value,
            "governed_project_id": self.governed_project_id,
            "registered_project_path": self.registered_project_path,
            "governed_via": None if self.governed_via is None else self.governed_via.value,
            "git_worktree_root": self.git_worktree_root,
            "git_common_dir": self.git_common_dir,
            "source_refs": _references_json(self.source_refs),
            "unknown_reason": self.unknown_reason,
        }


def aggregate_scope_status(resolutions: Sequence[ObjectResolution]) -> ScopeStatus:
    """Apply the five mutually exclusive aggregation rules from specification 02."""

    if not resolutions:
        return ScopeStatus.SCOPE_UNKNOWN
    statuses = {resolution.status for resolution in resolutions}
    if len(statuses) > 1:
        return ScopeStatus.MIXED_SCOPE
    status = next(iter(statuses))
    if status is ObjectStatus.UNKNOWN:
        return ScopeStatus.SCOPE_UNKNOWN
    if status is ObjectStatus.NOT_GOVERNED:
        return ScopeStatus.NON_GOVERNED
    project_ids = {resolution.governed_project_id for resolution in resolutions}
    if len(project_ids) == 1:
        return ScopeStatus.GOVERNED_SINGLE
    return ScopeStatus.MULTIPLE_GOVERNED_PROJECTS


@dataclass(frozen=True, slots=True)
class GovernanceScopeResult:
    workspace_root: str | None
    config_path: str | None
    config_status: ConfigStatus
    object_resolutions: tuple[ObjectResolution, ...]
    source_refs: tuple[JsonObject, ...]
    scope_status: ScopeStatus = field(init=False)

    def __post_init__(self) -> None:
        _require_absolute_or_none(self.workspace_root, "workspace_root")
        _require_absolute_or_none(self.config_path, "config_path")
        ordered = tuple(sorted(self.object_resolutions, key=lambda item: item.locator_index))
        indexes = [item.locator_index for item in ordered]
        if len(indexes) != len(set(indexes)):
            raise ValueError("object_resolutions must have unique locator_index values")
        object.__setattr__(self, "object_resolutions", ordered)
        object.__setattr__(self, "source_refs", _freeze_references(self.source_refs))
        if not self.source_refs:
            raise ValueError("source_refs must be non-empty")
        if self.config_status is not ConfigStatus.VALID and any(
            item.status is not ObjectStatus.UNKNOWN for item in ordered
        ):
            raise ValueError("a non-valid configuration cannot support a determined object status")
        object.__setattr__(self, "scope_status", aggregate_scope_status(ordered))

    @property
    def completed_scope(self) -> tuple[ScopeDescriptor, ...]:
        return tuple(item.scope_descriptor for item in self.object_resolutions)

    def to_json(self) -> dict[str, object]:
        return {
            "workspace_root": self.workspace_root,
            "config_path": self.config_path,
            "config_status": self.config_status.value,
            "scope_status": self.scope_status.value,
            "object_resolutions": [item.to_json() for item in self.object_resolutions],
            "source_refs": _references_json(self.source_refs),
        }


def explicit_scope(locators: Sequence[str]) -> tuple[ScopeDescriptor, ...]:
    """Preserve every explicit locator, including duplicates, in request order."""

    return tuple(
        ScopeDescriptor(locator_index=index, locator=locator, source=LocatorSource.EXPLICIT_LOCATOR)
        for index, locator in enumerate(locators)
    )


def cwd_scope(cwd: str) -> tuple[ScopeDescriptor, ...]:
    return (ScopeDescriptor(locator_index=0, locator=cwd, source=LocatorSource.CWD),)


def helper_scope(
    requested: Sequence[ScopeDescriptor],
    completed: Sequence[ScopeDescriptor],
) -> dict[str, object]:
    """Map domain scope members to the common Helper scope without deduplication."""

    completed_indexes = {item.locator_index for item in completed}
    requested_indexes = [item.locator_index for item in requested]
    if len(requested_indexes) != len(set(requested_indexes)):
        raise ValueError("requested scope must have unique locator_index values")
    if not completed_indexes.issubset(requested_indexes):
        raise ValueError("completed scope must be a subset of requested scope")
    completed_by_index = {item.locator_index: item for item in completed}
    requested_by_index = {item.locator_index: item for item in requested}
    if any(requested_by_index[index] != item for index, item in completed_by_index.items()):
        raise ValueError("completed scope members must equal their requested descriptors")
    return {
        "requested": [item.to_json() for item in requested],
        "completed": [item.to_json() for item in requested if item.locator_index in completed_indexes],
        "not_completed": [item.to_json() for item in requested if item.locator_index not in completed_indexes],
    }


__all__ = [
    "ConfigStatus",
    "GovernanceScopeResult",
    "GovernedVia",
    "LocatorSource",
    "ObjectResolution",
    "ObjectStatus",
    "ScopeDescriptor",
    "ScopeStatus",
    "aggregate_scope_status",
    "cwd_scope",
    "explicit_scope",
    "helper_scope",
]
