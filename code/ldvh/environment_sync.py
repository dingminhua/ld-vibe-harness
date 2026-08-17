"""Platform-explicit, target-absolute alignment of one AI environment's LDVH skill copy.

This module is the single shared surface for every command that must check or
update the LDVH Skill deployed to *one* target environment.  The current AI must
name its platform (a non-empty label used only for reporting) and the *absolute*
``skill_path`` of the actual target file.  The module never guesses a vendor
directory (e.g. WorkBuddy) and never writes anything without an explicit Human Gate.

Two verbs are exposed:

* :func:`inspect_skill` — read-only.  Returns byte-alignment, version alignment and
  the resolved target path for the platform/skill_path pair actually given.
* :func:`update_skill` — mutating, only after ``human_gate_confirmed``.  Creates the
  target when absent; when present, replaces it atomically *only* when the existing
  file is provably an LDVH Skill (legal version marker + frontmatter identity).
  Any unknown file is left untouched (conflict, zero write).  Failures preserve the
  original bytes.

Both verbs reuse the Git Hook manager for any Hook work, never copying its
state machine.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.git_hooks.commit_msg import (
    _MANAGED_MARKER_PREFIX,
    HOOK_BUNDLE_VERSION,
    _existing_hook_state,
    _hook_bundle_version,
)

_PLATFORM_REQUIRED = "platform 必须是非空字符串标签"
_SKILL_PATH_REQUIRED = "skill_path 必须是非空绝对路径"
_SKILL_VERSION_MARKER = "> Skill 版本"
_SKILL_FILENAME = "SKILL.md"

__all__ = [
    "SkillInspection",
    "SkillUpdate",
    "inspect_skill",
    "update_skill",
    "skill_digest",
    "_SKILL_FILENAME",
]

_LDVH_FRONTMATTER_NAME = "ldvh"


@dataclass(frozen=True, slots=True)
class SkillInspection:
    """Read-only observation of one target skill copy."""

    platform: str
    skill_path: str
    exists: bool
    is_ldvh_skill: bool
    target_version: str | None
    source_version: str | None
    byte_aligned: bool
    version_aligned: bool


@dataclass(frozen=True, slots=True)
class SkillUpdate:
    """Outcome of an authorized skill synchronization attempt."""

    platform: str
    skill_path: str
    created: bool
    replaced: bool
    conflict: bool
    aligned: bool
    target_version: str | None
    source_version: str | None
    detail: str


def _validate_platform(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(_PLATFORM_REQUIRED)
    return value.strip()


def _validate_skill_path(value: object) -> Path:
    if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
        raise ValueError(_SKILL_PATH_REQUIRED)
    target = Path(value)
    # 09 §5.9.1: skill_path points at the target SKILL.md file; a caller may pass the
    # skill directory instead. Resolve a directory (not itself named SKILL.md) to its
    # SKILL.md so is_file()/read_bytes() behave consistently. A directory literally
    # named SKILL.md is a malformed target and stays as-is (a write conflict).
    if target.is_dir() and target.name != _SKILL_FILENAME:
        target = target / _SKILL_FILENAME
    return target


def _read_skill_version(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(_SKILL_VERSION_MARKER):
            return stripped.removeprefix("> ").strip()
    return None


def _has_ldvh_frontmatter(path: Path) -> bool:
    """A file is an LDVH Skill only with frontmatter `name: ldvh` and a version marker."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    frontmatter = text[3:end]
    name_seen = False
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("name:"):
            value = stripped.removeprefix("name:").strip()
            if value == _LDVH_FRONTMATTER_NAME:
                name_seen = True
    if not name_seen:
        return False
    return _read_skill_version(path) is not None


def inspect_skill(*, platform: str, skill_path: str, source_path: Path) -> SkillInspection:
    """Read-only alignment check; never writes and never creates."""
    label = _validate_platform(platform)
    target = _validate_skill_path(skill_path)
    exists = target.is_file()
    target_version = _read_skill_version(target) if exists else None
    source_version = _read_skill_version(source_path) if source_path.is_file() else None
    byte_aligned = bool(exists and source_path.is_file() and target.read_bytes() == source_path.read_bytes())
    version_aligned = bool(
        exists and source_version is not None and target_version is not None and target_version == source_version
    )
    return SkillInspection(
        platform=label,
        skill_path=str(target),
        exists=exists,
        is_ldvh_skill=bool(exists and _has_ldvh_frontmatter(target)),
        target_version=target_version,
        source_version=source_version,
        byte_aligned=byte_aligned,
        version_aligned=version_aligned,
    )


def update_skill(
    *,
    platform: str,
    skill_path: str,
    source_path: Path,
    human_gate_confirmed: bool,
) -> SkillUpdate:
    """Synchronize a target skill copy after an explicit Human Gate.

    Zero writes occur before the Gate is confirmed.  When the target is absent it is
    created.  When present, it is replaced atomically only if it is provably an LDVH
    Skill; any other file is left untouched (conflict, zero write).  A temporary file
    and ``os.replace`` are used so a failed replacement preserves the original bytes.
    """
    label = _validate_platform(platform)
    target = _validate_skill_path(skill_path)
    if not source_path.is_file():
        return SkillUpdate(
            platform=label,
            skill_path=str(target),
            created=False,
            replaced=False,
            conflict=False,
            aligned=False,
            target_version=None,
            source_version=None,
            detail="canonical 源 Skill 不存在，无法同步",
        )
    source_bytes = source_path.read_bytes()
    source_version = _read_skill_version(source_path)

    if not human_gate_confirmed:
        return SkillUpdate(
            platform=label,
            skill_path=str(target),
            created=False,
            replaced=False,
            conflict=False,
            aligned=bool(target.is_file() and target.read_bytes() == source_bytes),
            target_version=_read_skill_version(target) if target.is_file() else None,
            source_version=source_version,
            detail="Human Gate 确认前不写入任何字节",
        )

    if target.is_symlink():
        return SkillUpdate(
            platform=label,
            skill_path=str(target),
            created=False,
            replaced=False,
            conflict=True,
            aligned=False,
            target_version=_read_skill_version(target),
            source_version=source_version,
            detail="目标路径是符号链接，冲突零写入",
        )

    if target.exists() and not target.is_file():
        return SkillUpdate(
            platform=label,
            skill_path=str(target),
            created=False,
            replaced=False,
            conflict=True,
            aligned=False,
            target_version=None,
            source_version=source_version,
            detail="目标路径已存在但不是普通文件，冲突零写入",
        )

    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".ldvh-skill-", dir=str(target.parent))
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(source_bytes)
            temporary.chmod(source_path.stat().st_mode & 0o777)
            os.replace(temporary, target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return SkillUpdate(
            platform=label,
            skill_path=str(target),
            created=True,
            replaced=False,
            conflict=False,
            aligned=True,
            target_version=source_version,
            source_version=source_version,
            detail="目标不存在；已创建与 canonical 逐字节一致的 Skill 副本",
        )

    if not _has_ldvh_frontmatter(target):
        return SkillUpdate(
            platform=label,
            skill_path=str(target),
            created=False,
            replaced=False,
            conflict=True,
            aligned=False,
            target_version=_read_skill_version(target),
            source_version=source_version,
            detail="目标文件不是可确认的 LDVH Skill，冲突零写入",
        )

    descriptor, temporary_name = tempfile.mkstemp(prefix=".ldvh-skill-", dir=str(target.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(source_bytes)
        temporary.chmod(source_path.stat().st_mode & 0o777)
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return SkillUpdate(
        platform=label,
        skill_path=str(target),
        created=False,
        replaced=True,
        conflict=False,
        aligned=True,
        target_version=source_version,
        source_version=source_version,
        detail="目标已是 LDVH Skill；已原子替换为 canonical 逐字节副本",
    )


def inspect_hook_surface(*, common_hooks: Path) -> dict[str, object]:
    """Reuse the Git Hook manager's deterministic state classification verbatim."""
    commit_msg = _hook_check(common_hooks, "commit-msg", _MANAGED_MARKER_PREFIX, HOOK_BUNDLE_VERSION)
    return {"commit-msg": commit_msg}


def _hook_check(common_hooks: Path, name: str, marker_prefix: str, expected_version: str) -> dict[str, object]:
    hook = common_hooks / name
    state, detail_text = _existing_hook_state(hook, name=name, marker_prefix=marker_prefix)
    deployed_version = _hook_bundle_version(hook) if hook.is_file() else None
    aligned = state == "managed" and deployed_version == expected_version

    return {
        "path": str(hook),
        "state": state,
        "detail": detail_text,
        "deployed_bundle_version": deployed_version,
        "expected_bundle_version": expected_version,
        "aligned": aligned,
    }


def skill_digest(path: Path) -> str | None:
    """SHA-256 of a skill file, or None when unreadable."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError):
        return None


SkillSyncStatus = Literal["created", "replaced", "conflict", "gate_pending", "source_missing"]
