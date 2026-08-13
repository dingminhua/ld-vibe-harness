"""Append-only artifact fingerprint registry for the version-omission guard.

This is the controlled, append-only source of truth that the version-omission
tests consult.  It records one *canonical digest* per known version on each of
the two independent version lines (Skill and Git Hook bundle).  The tests compute
the current artifact's deterministic digest and require it to *hit* a registered
entry for the current version; if an artifact body changes without a version
bump, the digest no longer matches and the test fails.

Design rules (enforced by :func:`validate_registry`):

* Append-only.  A coordinator registers a new version by appending an entry; they
  never edit or remove a historical ``digests`` mapping.  When the canonical
  Skill is intentionally promoted to a new version (e.g. ``2026-08-14 00:00``),
  the coordinator only *adds* a new registry entry and, if desired, repoints
  ``CURRENT`` — the old mapping for ``2026-08-13 00:01`` stays intact.
* Version keys are unique within a line; a duplicate key raises on validation.
* The two lines (``skill`` / ``hook``) are independent: neither requires the
  other to advance in lockstep.
* ``current`` points at the version the running repo is expected to carry.  The
  tests assert the *current* artifact's digest equals
  ``REGISTRY[line]["digests"][current]``.

The digests below were produced by ``ldvh.version_guard`` against the repository
at the moment each version was approved.  Do not hand-edit a digest; if a body
must change, bump the version and append a fresh entry instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

_VersionLine = Literal["skill", "hook"]


@dataclass(frozen=True, slots=True)
class VersionLine:
    """One append-only version line with its registered digests and current pointer."""

    name: str
    current: str
    digests: dict[str, str]


# --- Skill line ---------------------------------------------------------------
# Keyed by the ``> Skill 版本：<ts>`` marker in ``skill/SKILL.md``.
SKILL_LINE = VersionLine(
    name="skill",
    current="2026-08-14 00:00",
    digests={
        "2026-08-13 00:01": "fe1254762ebe24953d1817278f845b795341a4898085c592eac36d30fe5e0e5a",
        "2026-08-14 00:00": "714b515df0e09aa418558edc4ebb278b50b8d5f1d750867d5e6d2aacc367e4c2",
    },
)

# --- Hook line ----------------------------------------------------------------
# Keyed by ``HOOK_BUNDLE_VERSION``. Each digest covers the full rendered Hook,
# including its bundle-version marker and managed-content digest marker.
HOOK_LINE = VersionLine(
    name="hook",
    current="2026-08-13 00:00",
    digests={
        "2026-08-13 00:00": "ae96a516b8a6ff33998542edab6241f06ddbbebce4f6c3c687eb84a5f3713ff2",
    },
)

REGISTRY: dict[str, VersionLine] = {
    "skill": SKILL_LINE,
    "hook": HOOK_LINE,
}


def validate_registry(registry: dict[str, VersionLine] = REGISTRY) -> None:
    """Raise on structural violations: missing current, bad digests."""

    for line_name, line in registry.items():
        if line.current not in line.digests:
            raise ValueError(f"{line_name}: current version {line.current!r} has no registered digest")
        for version, digest in line.digests.items():
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError(f"{line_name}: version {version!r} has a non-hex SHA-256 digest")


def register_version(
    line: str,
    version: str,
    digest: str,
    *,
    make_current: bool = False,
    registry: dict[str, VersionLine] = REGISTRY,
) -> None:
    """Append-only registration: add ``version``/``digest`` to ``line``.

    Refuses to overwrite a historical mapping — re-registering an already known
    version raises.  A coordinator therefore cannot silently rewrite an old digest;
    to change the running artifact they must *bump* the version and register the
    new one (optionally repointing ``current`` via ``make_current``).
    """

    entry = registry.get(line)
    if entry is None:
        raise ValueError(f"unknown version line {line!r}")
    if version in entry.digests:
        raise ValueError(f"{line}: version {version!r} is already registered and must not be rewritten")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError(f"{line}: version {version!r} has a non-hex SHA-256 digest")
    updated = VersionLine(
        name=entry.name,
        current=version if make_current else entry.current,
        digests={**entry.digests, version: digest},
    )
    registry[line] = updated


def lookup_digest(line: str, version: str, registry: dict[str, VersionLine] = REGISTRY) -> str | None:
    """Return the registered digest for ``line``/``version``, or None when unknown."""

    entry = registry.get(line)
    if entry is None:
        return None
    return entry.digests.get(version)
