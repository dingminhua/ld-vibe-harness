"""Version-omission guard: same-version artifacts must not diverge in body.

These tests prove the contract in ``ldvh.version_guard`` + ``version_guard_registry``:

1. The current canonical Skill's body (and its version line) is pinned by digest;
   a future body change that keeps the version marker must fail.
2. The current Git Hook render (fixed virtual runner/workspace) is pinned by
   digest; a future Hook body change that keeps ``HOOK_BUNDLE_VERSION`` must fail.
3. The Skill and Hook version lines are independent — bumping one never implies
   the other, and each line is verified on its own.

The registry is append-only: a coordinator registers a new approved digest by
*adding* a key (and optionally repointing ``current``); historical mappings are
never rewritten.  The tests therefore only ever read the registry.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ldvh import version_guard as guard
from ldvh import version_guard_registry as registry


def test_registry_is_valid_structure() -> None:
    """The append-only registry must pass its own structural invariants."""
    registry.validate_registry()


def test_skill_current_version_is_registered() -> None:
    """The running Skill version must have a registered canonical digest."""
    version = guard.current_skill_version()
    assert version is not None
    expected = registry.lookup_digest("skill", version)
    assert expected is not None, f"Skill version {version!r} is missing from the registry"


def test_skill_current_digest_hits_registry() -> None:
    """Current Skill file bytes must equal the registered digest for its version."""
    version = guard.current_skill_version()
    assert version is not None
    expected = registry.lookup_digest("skill", version)
    assert expected is not None
    assert guard.current_skill_digest() == expected


def test_hook_current_version_is_registered() -> None:
    """The running HOOK_BUNDLE_VERSION must have a registered canonical digest."""
    version = guard.current_hook_bundle_version()
    expected = registry.lookup_digest("hook", version)
    assert expected is not None, f"Hook version {version!r} is missing from the registry"


def test_hook_current_digest_hits_registry() -> None:
    """Current Hook render bytes must equal the registered digest for its version."""
    version = guard.current_hook_bundle_version()
    expected = registry.lookup_digest("hook", version)
    assert expected is not None
    assert guard.current_hook_digest() == expected


def test_hook_render_is_deterministic() -> None:
    """The virtual-runner Hook render must be byte-stable across calls."""
    assert guard.render_current_commit_msg_hook() == guard.render_current_commit_msg_hook()


def test_modifying_skill_body_while_keeping_version_fails(tmp_path: Path) -> None:
    """A body change that retains the version marker must NOT match the registry digest.

    This is the core future-proofing check: when the Skill text changes but the
    version marker is left untouched, the computed digest must diverge and the
    guard (a plain function) returns a mismatch.
    """
    source = guard._CANONICAL_SKILL_PATH.read_text(encoding="utf-8")
    version = guard.read_skill_version(guard._CANONICAL_SKILL_PATH)
    assert version is not None

    # Insert an invisible extra line; keep the version marker identical.
    tampered = source + "\n<!-- silent edit: 版本未提升但正文变化 -->\n"
    assert guard.read_skill_version_from_text(tampered) == version  # helper keeps version

    tampered_digest = guard.skill_digest_bytes(tampered)
    assert tampered_digest != guard.current_skill_digest()
    # This is the same version-to-digest comparison used by the live CI guard.
    assert tampered_digest != registry.lookup_digest("skill", version)


def test_duplicate_skill_version_markers_are_rejected() -> None:
    source = guard._CANONICAL_SKILL_PATH.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="more than one version marker"):
        guard.read_skill_version_from_text(source + "\n> Skill 版本：2099-01-01 00:00\n")


def test_modifying_hook_body_while_keeping_version_fails() -> None:
    """A Hook body change that keeps HOOK_BUNDLE_VERSION must NOT match the registry digest."""
    version = guard.current_hook_bundle_version()
    expected = registry.lookup_digest("hook", version)
    assert expected is not None

    rendered = guard.render_current_commit_msg_hook()
    # Append a no-op comment line: same bundle version, different body.
    tampered = rendered + "\n# silent edit: bundle 版本未提升\n"
    tampered_digest = guard.hook_digest_bytes(tampered)

    assert tampered_digest != guard.current_hook_digest()
    assert tampered_digest != expected


def test_two_version_lines_are_independent() -> None:
    """Skill and Hook lines are separate keys; each is verified without the other."""
    skill_version = guard.current_skill_version()
    hook_version = guard.current_hook_bundle_version()
    # Independence is structural: distinct registry keys, distinct current pointers.
    assert "skill" in registry.REGISTRY
    assert "hook" in registry.REGISTRY
    assert registry.REGISTRY["skill"].name != registry.REGISTRY["hook"].name
    assert skill_version is not None
    # The Skill line carries its own digest map; the Hook line never borrows it.
    assert hook_version not in registry.REGISTRY["skill"].digests
    # Each current digest resolves on its own line only.
    assert registry.lookup_digest("skill", skill_version) is not None
    assert registry.lookup_digest("hook", hook_version) is not None


def test_registry_rejects_duplicate_version_key() -> None:
    """Re-registering an existing version key must be refused (append-only)."""

    from ldvh.version_guard_registry import register_version

    existing = "2026-08-13 00:00"
    with pytest.raises(ValueError, match="already registered"):
        register_version(
            "hook",
            existing,
            "0000000000000000000000000000000000000000000000000000000000000000",
        )


def test_coordinator_can_add_future_version_without_touching_old() -> None:
    """Appending a future Skill version must leave the historical mapping intact.

    Mirrors the workflow: when the canonical Skill is approved at a new version,
    the coordinator appends a new registry entry via :func:`register_version`
    (and may repoint ``current``).  They must not rewrite the old digest, and
    attempting to do so is refused.  Runs against a private copy so the live
    registry is never mutated under the parallel test runner.
    """
    from ldvh.version_guard_registry import VersionLine, register_version

    future_version = "2099-01-01 00:00"
    old_version = "2026-08-13 00:01"
    old_digest = registry.lookup_digest("skill", old_version)
    assert old_digest is not None

    local = {
        "skill": VersionLine(
            name="skill",
            current=old_version,
            digests={"2026-08-13 00:01": old_digest},
        ),
        "hook": registry.REGISTRY["hook"],
    }

    # Append-only add of the future version; old key is preserved automatically.
    register_version("skill", future_version, "0" * 64, registry=local)
    assert local["skill"].digests[old_version] == old_digest
    assert old_version in local["skill"].digests
    assert future_version in local["skill"].digests

    # Rewriting the historical digest is refused.
    with pytest.raises(ValueError, match="already registered"):
        register_version("skill", old_version, "f" * 64, registry=local)

    # And the running repo's live registry is untouched.
    assert future_version not in registry.REGISTRY["skill"].digests
