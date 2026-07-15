from pathlib import Path

import pytest

from ldvh.specs.source import RuleSourceIdentity


def test_rule_source_identity_enforces_view_specific_fields(tmp_path: Path) -> None:
    working = RuleSourceIdentity("working_tree", git_worktree_root=tmp_path.resolve())
    installed = RuleSourceIdentity(
        "installed_release_snapshot",
        distribution="ld-vibe-harness",
        version="0.1.0",
        snapshot_sha256="a" * 64,
    )
    assert working.view == "working_tree"
    assert installed.snapshot_sha256 == "a" * 64

    with pytest.raises(ValueError):
        RuleSourceIdentity("working_tree", git_worktree_root=Path("relative"))
    with pytest.raises(ValueError):
        RuleSourceIdentity(
            "working_tree",
            git_worktree_root=tmp_path.resolve(),
            distribution="ld-vibe-harness",
        )
    with pytest.raises(ValueError):
        RuleSourceIdentity(
            "installed_release_snapshot",
            distribution="ld-vibe-harness",
            version="0.1.0",
            snapshot_sha256="A" * 64,
        )
