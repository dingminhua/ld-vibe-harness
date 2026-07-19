from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

import pytest

from ldvh.rule_snapshot import (
    SnapshotError,
    inspect_verified_snapshot,
    snapshot_plan_for_source,
    validate_installed_snapshot,
    validate_snapshot_directory,
    write_snapshot,
)
from ldvh.specs.repository import UNCHECKED_CONDITIONS


class _Distribution:
    def __init__(self, root: Path, files: list[str]) -> None:
        self.root = root
        self.files = [PurePosixPath(item) for item in files]
        self.metadata = {"Name": "ld-vibe-harness"}
        self.version = "0.1.0"

    def locate_file(self, item: PurePosixPath) -> Path:
        return self.root / item.as_posix()


def test_worktree_snapshot_separates_rules_and_mechanical_evidence(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    plan = snapshot_plan_for_source(current_specs_repository, "0.1.0")
    assert {item.role for item in plan.files} == {"rule_candidate"}

    root = tmp_path / "snapshot"
    write_snapshot(plan, root)
    verified = validate_snapshot_directory(root, distribution="ld-vibe-harness", version="0.1.0")
    repository = inspect_verified_snapshot(verified)
    assert repository.implemented_checks_complete is True
    assert repository.unchecked_conditions == UNCHECKED_CONDITIONS
    assert repository.source_identity is not None
    assert repository.source_identity.view == "installed_release_snapshot"
    assert all(candidate.relative_path.startswith("specs/") for candidate in repository.candidates)


def test_manifest_rejects_unknown_fields_and_noncanonical_json(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    plan = snapshot_plan_for_source(current_specs_repository, "0.1.0")
    root = tmp_path / "snapshot"
    write_snapshot(plan, root)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["unknown"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SnapshotError, match="top-level field set"):
        validate_snapshot_directory(root, distribution="ld-vibe-harness", version="0.1.0")


def test_manifest_rejects_resource_tampering(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    plan = snapshot_plan_for_source(current_specs_repository, "0.1.0")
    root = tmp_path / "snapshot"
    write_snapshot(plan, root)
    target = root / plan.files[0].path
    target.write_bytes(target.read_bytes() + b"tampered")
    with pytest.raises(SnapshotError, match="does not match manifest"):
        validate_snapshot_directory(root, distribution="ld-vibe-harness", version="0.1.0")


def test_snapshot_walk_rejects_linked_directory_without_descending(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    plan = snapshot_plan_for_source(current_specs_repository, "0.1.0")
    root = tmp_path / "snapshot"
    write_snapshot(plan, root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "undeclared.md").write_text("outside", encoding="utf-8")
    try:
        (root / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(SnapshotError, match="unsafe resource"):
        validate_snapshot_directory(root, distribution="ld-vibe-harness", version="0.1.0")


def test_snapshot_rejects_nested_undeclared_manifest_name(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    plan = snapshot_plan_for_source(current_specs_repository, "0.1.0")
    root = tmp_path / "snapshot"
    write_snapshot(plan, root)
    (root / "specs/manifest.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(SnapshotError, match="undeclared"):
        validate_snapshot_directory(root, distribution="ld-vibe-harness", version="0.1.0")


def test_snapshot_rejects_linked_root(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    plan = snapshot_plan_for_source(current_specs_repository, "0.1.0")
    root = tmp_path / "snapshot"
    write_snapshot(plan, root)
    linked_root = tmp_path / "linked-snapshot"
    try:
        linked_root.symlink_to(root, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(SnapshotError, match="cannot be read safely"):
        validate_snapshot_directory(linked_root, distribution="ld-vibe-harness", version="0.1.0")


def test_installed_snapshot_requires_the_distribution_to_own_package_and_resources(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    plan = snapshot_plan_for_source(current_specs_repository, "0.1.0")
    site = tmp_path / "site"
    package = site / "ldvh"
    package.mkdir(parents=True)
    package_file = package / "__init__.py"
    package_file.write_text("", encoding="utf-8")
    write_snapshot(plan, package / "_rule_snapshot")
    claimed = [
        "ldvh/__init__.py",
        "ldvh/_rule_snapshot/manifest.json",
        *(f"ldvh/_rule_snapshot/{item.path}" for item in plan.files),
    ]
    owner = _Distribution(site, claimed)
    monkeypatch.setattr("ldvh.rule_snapshot.importlib.metadata.distributions", lambda **_: [owner])
    assert validate_installed_snapshot(package_file).snapshot_sha256 == plan.snapshot_sha256

    non_owner = _Distribution(tmp_path / "other-site", claimed)
    monkeypatch.setattr("ldvh.rule_snapshot.importlib.metadata.distributions", lambda **_: [non_owner])
    with pytest.raises(SnapshotError, match="proven distribution owner"):
        validate_installed_snapshot(package_file)
