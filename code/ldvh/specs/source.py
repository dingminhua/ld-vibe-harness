"""Typed identities and already-observed bytes for one rule-source view."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class RuleSourceIdentity:
    view: Literal["working_tree", "installed_release_snapshot"]
    git_worktree_root: Path | None = None
    distribution: str | None = None
    version: str | None = None
    snapshot_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.view == "working_tree":
            if self.git_worktree_root is None or not self.git_worktree_root.is_absolute():
                raise ValueError("working_tree requires an absolute git_worktree_root")
            if any(value is not None for value in (self.distribution, self.version, self.snapshot_sha256)):
                raise ValueError("working_tree cannot carry installed release identity")
            return
        if self.view != "installed_release_snapshot":
            raise ValueError("unknown rule source view")
        if self.git_worktree_root is not None:
            raise ValueError("installed_release_snapshot cannot carry git_worktree_root")
        if not self.distribution or not self.version or not self.snapshot_sha256:
            raise ValueError("installed_release_snapshot requires distribution, version, and snapshot_sha256")
        if _SHA256.fullmatch(self.snapshot_sha256) is None:
            raise ValueError("snapshot_sha256 must be 64 lowercase hexadecimal characters")


@dataclass(frozen=True, slots=True)
class ObservedResource:
    canonical_path: str
    raw_bytes: bytes
    observed_at: str


__all__ = ["ObservedResource", "RuleSourceIdentity"]
