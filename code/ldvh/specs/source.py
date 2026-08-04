"""Typed identities and already-observed bytes for one rule-source view."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True, slots=True)
class RuleSourceIdentity:
    view: Literal["working_tree"]
    git_worktree_root: Path

    def __post_init__(self) -> None:
        if self.view != "working_tree":
            raise ValueError("working_tree is the only rule source view")
        if not self.git_worktree_root.is_absolute():
            raise ValueError("working_tree requires an absolute git_worktree_root")


@dataclass(frozen=True, slots=True)
class ObservedResource:
    canonical_path: str
    raw_bytes: bytes
    observed_at: str


__all__ = ["ObservedResource", "RuleSourceIdentity"]
