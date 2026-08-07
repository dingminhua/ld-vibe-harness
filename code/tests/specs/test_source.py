from pathlib import Path

import pytest

from ldvh.specs.source import RuleSourceIdentity


def test_rule_source_identity_enforces_view_specific_fields(tmp_path: Path) -> None:
    working = RuleSourceIdentity("working_tree", git_worktree_root=tmp_path.resolve())
    assert working.view == "working_tree"

    with pytest.raises(ValueError):
        RuleSourceIdentity("working_tree", git_worktree_root=Path("relative"))
    with pytest.raises(ValueError):
        RuleSourceIdentity("unknown", git_worktree_root=tmp_path.resolve())  # type: ignore[arg-type]
