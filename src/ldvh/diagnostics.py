"""Internal diagnostic records shared by deterministic Code modules."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """A repository-relative source location."""

    path: str
    line: int | None = None
    heading: str | None = None


@dataclass(frozen=True, slots=True)
class Issue:
    """A source-locatable internal problem without a global error-code taxonomy."""

    summary: str
    location: SourceLocation
    affected: tuple[str, ...] = field(default_factory=tuple)
    cause: str | None = None
    blocks_projection: bool = True
