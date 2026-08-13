"""Deterministic version guards for the canonical Skill and Git Hook bundle."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ldvh.git_hooks.commit_msg import HOOK_BUNDLE_VERSION, render_commit_msg_hook

_VIRTUAL_COMMIT_MSG_RUNNER = Path("/opt/ldvh/.venv/bin/ldvh")
_VIRTUAL_WORKSPACE_ROOT = Path("/opt/ldvh/workspace")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CANONICAL_SKILL_PATH = _PROJECT_ROOT / "skill" / "SKILL.md"
_SKILL_VERSION_RE = re.compile(r"^\s*> Skill 版本[：:]\s*(.+?)\s*$")


def skill_digest_bytes(text: str) -> str:
    """Return the UTF-8 SHA-256 digest of a Skill body."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hook_digest_bytes(rendered: str) -> str:
    """Return the UTF-8 SHA-256 digest of a rendered Hook artifact."""

    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def read_skill_version(path: Path) -> str | None:
    """Extract the one Skill version marker, or return None when unreadable or absent."""

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    return read_skill_version_from_text(text)


def read_skill_version_from_text(text: str) -> str | None:
    """Extract the one Skill version marker and reject ambiguous bodies."""

    versions = [match.group(1).strip() for line in text.splitlines() if (match := _SKILL_VERSION_RE.match(line))]
    if len(versions) > 1:
        raise ValueError("Skill body contains more than one version marker")
    return versions[0] if versions else None


def current_skill_version() -> str | None:
    """Return the version in the repository's canonical Skill."""

    return read_skill_version(_CANONICAL_SKILL_PATH)


def current_skill_digest() -> str | None:
    """Return the full canonical Skill file digest, or None when unreadable."""

    try:
        return skill_digest_bytes(_CANONICAL_SKILL_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return None


def current_hook_bundle_version() -> str:
    """Return the current Git Hook bundle version."""

    return HOOK_BUNDLE_VERSION


def render_current_commit_msg_hook() -> str:
    """Render the full Hook artifact using fixed virtual absolute paths."""

    return render_commit_msg_hook(
        commit_msg_runner=_VIRTUAL_COMMIT_MSG_RUNNER,
        workspace_root=_VIRTUAL_WORKSPACE_ROOT,
        include_bundle_version=True,
    )


def current_hook_digest() -> str:
    """Return the digest of the full rendered Hook, including its markers."""

    return hook_digest_bytes(render_current_commit_msg_hook())
