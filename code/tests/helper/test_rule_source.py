from __future__ import annotations

import subprocess
from pathlib import Path

from ldvh.helper.rule_source import (
    inspect_colocated_repository,
    inspect_colocated_rule_source,
    locate_colocated_repository,
)


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)


def test_locates_repository_only_from_colocated_package_path(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    package_file = root / "code/ldvh/__init__.py"
    package_file.parent.mkdir(parents=True)
    package_file.write_text("", encoding="utf-8")
    root_spec = root / "specs/00-理念与构成.md"
    root_spec.parent.mkdir()
    root_spec.write_text("# root", encoding="utf-8")
    _git_init(root)

    assert locate_colocated_repository(package_file) == root


def test_worktree_selection_does_not_depend_on_specs_health(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repository"
    package_file = root / "code/ldvh/__init__.py"
    package_file.parent.mkdir(parents=True)
    package_file.write_text("", encoding="utf-8")
    _git_init(root)
    called = False

    def installed_loader(_path: Path):
        nonlocal called
        called = True
        raise AssertionError("installed snapshot fallback must not run")

    monkeypatch.setattr("ldvh.helper.rule_source.validate_installed_snapshot", installed_loader)
    result = inspect_colocated_rule_source(package_file)
    assert called is False
    assert result.repository is not None
    assert result.repository.source_identity is not None
    assert result.repository.source_identity.view == "working_tree"


def test_colocated_repository_does_not_require_helper_operation_declarations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "repository"
    package_file = root / "code/ldvh/__init__.py"
    package_file.parent.mkdir(parents=True)
    package_file.write_text("", encoding="utf-8")
    _git_init(root)
    monkeypatch.setattr(
        "ldvh.helper.rule_source.inspect_operation_sources",
        lambda _repository: (_ for _ in ()).throw(AssertionError("operation declarations must not be read")),
    )

    result = inspect_colocated_repository(package_file)

    assert result.problem is None
    assert result.repository is not None
    assert result.operations is None


def test_does_not_search_cwd_or_unrelated_sibling(tmp_path: Path, monkeypatch) -> None:
    unrelated = tmp_path / "repository"
    (unrelated / "code/ldvh").mkdir(parents=True)
    (unrelated / "specs").mkdir()
    (unrelated / "specs/00-理念与构成.md").write_text("# root", encoding="utf-8")
    package_file = tmp_path / "installed/ldvh/__init__.py"
    package_file.parent.mkdir(parents=True)
    package_file.write_text("", encoding="utf-8")
    monkeypatch.chdir(unrelated)

    assert locate_colocated_repository(package_file) is None
