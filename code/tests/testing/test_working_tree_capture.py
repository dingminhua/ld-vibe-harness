from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ldvh.filesystem import PathChangedError
from ldvh.governance.configuration import CONFIGURATION_FILENAME
from ldvh.governance.models import ConfigStatus, ObjectStatus, ScopeStatus
from ldvh.testing import working_tree_capture as capture_module
from ldvh.testing.working_tree_capture import (
    GovernedWorktreeBoundary,
    capture_manifest,
    resolve_capture_boundary,
    same_capture_boundary,
)
from ldvh.testing.working_tree_evidence import (
    current_policy_fingerprint,
    policy_excludes_relative_path,
    validate_coverage,
    validate_manifest,
)


def _boundary(root: Path) -> GovernedWorktreeBoundary:
    return GovernedWorktreeBoundary("ldvh", root, root.parent / ".git-common")


def _paths(result: Any) -> set[str]:
    return {item["path"] for item in result.manifest["files"]}


def _git(path: Path, *arguments: str) -> str:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "LDVH Test",
            "GIT_AUTHOR_EMAIL": "ldvh@example.invalid",
            "GIT_COMMITTER_NAME": "LDVH Test",
            "GIT_COMMITTER_EMAIL": "ldvh@example.invalid",
        }
    )
    completed = subprocess.run(
        ["git", "-C", str(path), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return completed.stdout.strip()


@pytest.mark.parametrize(
    ("path", "kind"),
    [
        (".git", "other"),
        (".git/objects/aa", "regular_file"),
        (".ldvh-test-runs", "directory"),
        (".venv", "directory"),
        ("web/node_modules/pkg/index.js", "regular_file"),
        ("pkg/__pycache__", "directory"),
        ("pkg/cache.egg-info/PKG-INFO", "regular_file"),
        ("module.pyc", "regular_file"),
        ("nested/.DS_Store", "regular_file"),
    ],
)
def test_policy_matcher_uses_fixed_exclusions(path: str, kind: str) -> None:
    assert policy_excludes_relative_path(path, entry_kind=kind) is True  # type: ignore[arg-type]


def test_policy_matcher_does_not_add_hidden_or_name_based_exclusions() -> None:
    assert policy_excludes_relative_path(".hidden/input.txt", entry_kind="regular_file") is False
    assert policy_excludes_relative_path("nested/node_modules/input.js", entry_kind="regular_file") is False
    assert policy_excludes_relative_path("nested/.git/input", entry_kind="regular_file") is False
    assert policy_excludes_relative_path(".DS_Store", entry_kind="other") is False


def test_capture_includes_all_regular_bytes_and_prunes_policy_output(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    (tmp_path / "ignored.txt").write_bytes(b"ignored but included")
    (tmp_path / "untracked.txt").write_bytes(b"untracked")
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "input.bin").write_bytes(b"\x00\xff")
    excluded = tmp_path / ".ldvh-test-runs"
    excluded.mkdir()
    (excluded / "record.json").write_bytes(b"self-reference")
    cache = tmp_path / "pkg" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "module.pyc").write_bytes(b"cache")

    result = capture_manifest(_boundary(tmp_path), "before")

    assert result.coverage["status"] == "complete"
    assert _paths(result) == {".gitignore", ".hidden/input.bin", "ignored.txt", "untracked.txt"}
    assert result.manifest["status"] == "complete"
    validate_coverage(result.coverage)
    validate_manifest(result.manifest, current_policy_fingerprint())


def test_excluded_root_is_pruned_without_observing_its_type(tmp_path: Path) -> None:
    target = tmp_path / "outside"
    target.mkdir()
    (target / "secret").write_bytes(b"outside")
    try:
        (tmp_path / ".venv").symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    result = capture_manifest(_boundary(tmp_path), "before")

    assert result.coverage["status"] == "complete"
    assert not result.diagnostics
    assert ".venv/secret" not in _paths(result)


def test_included_symlink_or_reparse_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source.txt"
    source.write_bytes(b"source")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("symlinks are unavailable")

    result = capture_manifest(_boundary(tmp_path), "before")
    assert result.coverage["status"] == "incomplete"
    assert any(gap["path"] == "link.txt" and gap["code"] == "unsafe_entry" for gap in result.coverage["gaps"])

    link.unlink()
    reparse_candidate = tmp_path / "reparse.bin"
    reparse_candidate.write_bytes(b"candidate")
    original = capture_module.is_link_or_reparse
    monkeypatch.setattr(
        capture_module,
        "is_link_or_reparse",
        lambda observation: stat.S_ISREG(observation.st_mode) or original(observation),
    )
    result = capture_manifest(_boundary(tmp_path), "after")
    assert any(gap["path"] == "reparse.bin" and gap["code"] == "unsafe_entry" for gap in result.coverage["gaps"])


@pytest.mark.skipif(os.name == "nt", reason="mkfifo is not a portable Windows fixture")
def test_unsupported_entry_fails_closed(tmp_path: Path) -> None:
    os.mkfifo(tmp_path / "pipe")

    result = capture_manifest(_boundary(tmp_path), "before")

    assert result.manifest["status"] == "incomplete"
    assert result.manifest["manifest_fingerprint"] is None
    assert any(gap["path"] == "pipe" and gap["code"] == "unsupported_entry" for gap in result.coverage["gaps"])


@pytest.mark.parametrize(
    ("failure", "expected_code"),
    [(OSError("unreadable"), "read_unavailable"), (PathChangedError("changed"), "path_changed")],
)
def test_read_failure_and_path_change_are_distinguished(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: OSError,
    expected_code: str,
) -> None:
    (tmp_path / "input.txt").write_bytes(b"input")
    monkeypatch.setattr(capture_module, "safe_read_relative", lambda *_args, **_kwargs: (_ for _ in ()).throw(failure))

    result = capture_manifest(_boundary(tmp_path), "after")

    assert result.coverage["status"] == "incomplete"
    assert any(gap["path"] == "input.txt" and gap["code"] == expected_code for gap in result.coverage["gaps"])


def test_traversal_failure_is_not_reported_as_an_empty_complete_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(capture_module.os, "scandir", lambda _path: (_ for _ in ()).throw(PermissionError()))

    result = capture_manifest(_boundary(tmp_path), "before")

    assert result.manifest["status"] == "incomplete"
    assert result.manifest["file_count"] == 0
    assert result.coverage["gaps"][0]["code"] == "traversal_unavailable"


def test_nfc_collision_fails_closed_before_entry_type_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeEntry:
        def __init__(self, name: str) -> None:
            self.name = name
            self.path = str(tmp_path / name)

        def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
            raise AssertionError("colliding entries must not be observed")

    class FakeScandir:
        def __enter__(self) -> tuple[FakeEntry, FakeEntry]:
            return (FakeEntry("e\u0301.txt"), FakeEntry("é.txt"))

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(capture_module.os, "scandir", lambda _path: FakeScandir())

    result = capture_manifest(_boundary(tmp_path), "before")

    assert result.manifest["status"] == "incomplete"
    assert result.manifest["files"] == []
    assert result.coverage["gaps"] == [
        {
            "stage": "before",
            "path": "é.txt",
            "code": "normalization_collision",
            "summary": "multiple observed paths collide after NFC normalization",
        }
    ]


def test_resolve_boundary_accepts_only_exact_complete_unique_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    resolver_calls: list[dict[str, Any]] = []

    def resolved(requested: Any, **kwargs: Any) -> Any:
        resolver_calls.append(kwargs)
        resolution = SimpleNamespace(
            status=ObjectStatus.GOVERNED,
            governed_project_id="ldvh",
            git_worktree_root=str(workspace),
            git_common_dir=str(tmp_path / "common.git"),
        )
        result = SimpleNamespace(
            config_status=ConfigStatus.VALID,
            scope_status=ScopeStatus.GOVERNED_SINGLE,
            object_resolutions=(resolution,),
        )
        return SimpleNamespace(
            technical_non_completions=(),
            requested_scope=tuple(requested),
            completed_scope=tuple(requested),
            result=result,
        )

    monkeypatch.setattr(capture_module, "resolve_governance_scope", resolved)
    accepted = resolve_capture_boundary(workspace)

    assert accepted.boundary == GovernedWorktreeBoundary("ldvh", workspace, tmp_path / "common.git")
    assert accepted.diagnostics == ()
    assert resolver_calls == [{"base": workspace}]

    def incomplete(requested: Any, **_kwargs: Any) -> Any:
        return SimpleNamespace(
            technical_non_completions=(object(),),
            requested_scope=tuple(requested),
            completed_scope=(),
            result=None,
        )

    monkeypatch.setattr(capture_module, "resolve_governance_scope", incomplete)
    rejected = resolve_capture_boundary(workspace)
    assert rejected.boundary is None
    assert rejected.diagnostics[0].code == "governance_incomplete"


def test_boundary_comparison_covers_after_identity_mismatch(tmp_path: Path) -> None:
    before = _boundary(tmp_path)
    assert same_capture_boundary(before, before)
    assert not same_capture_boundary(
        before,
        GovernedWorktreeBoundary("ldvh", tmp_path, tmp_path.parent / "different.git"),
    )


def test_linked_worktree_resolves_registered_common_dir_but_captures_linked_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    main = workspace / "main"
    main.mkdir(parents=True)
    _git(main, "init", "-q")
    (main / "tracked.txt").write_text("main\n", encoding="utf-8")
    _git(main, "add", ".")
    _git(main, "commit", "-qm", "initial")
    linked = workspace / "linked"
    _git(main, "worktree", "add", "-qb", "linked-capture", str(linked))
    (workspace / CONFIGURATION_FILENAME).write_text(
        f"product_name: Test\nproduct_description: Test workspace\nprojects:\n  - id: ldvh\n    path: {main}\n",
        encoding="utf-8",
    )
    (linked / "untracked.txt").write_text("linked only\n", encoding="utf-8")

    resolution = resolve_capture_boundary(linked)

    assert resolution.diagnostics == ()
    assert resolution.boundary is not None
    assert resolution.boundary.git_worktree_root == linked.resolve()
    assert resolution.boundary.git_common_dir == (main / ".git").resolve()
    result = capture_manifest(resolution.boundary, "before")
    assert result.manifest["status"] == "complete"
    assert "untracked.txt" in _paths(result)
