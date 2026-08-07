from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from ldvh.specs import discovery
from ldvh.specs.discovery import Candidate, discover_candidates


def test_discovery_git_environment_uses_the_shared_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "attacker.gitconfig")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "attacker-system.gitconfig")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.hooksPath")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "/tmp/attacker-hooks")

    environment = discovery._git_environment()

    assert environment["GIT_CONFIG_GLOBAL"] == os.devnull
    assert environment["GIT_CONFIG_NOSYSTEM"] == "1"
    assert "GIT_CONFIG_SYSTEM" not in environment
    assert "GIT_CONFIG_COUNT" not in environment
    assert "GIT_CONFIG_KEY_0" not in environment
    assert "GIT_CONFIG_VALUE_0" not in environment


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "-q")
    return root


def test_discovers_direct_untracked_spec_and_attachment_candidates(repository: Path) -> None:
    _write(repository / "specs/09-Untracked specification.md")
    _write(repository / "specs/attachments/09.Att.12-Untracked attachment.md")

    result = discover_candidates(repository)

    assert result.repository_root == repository.resolve()
    assert result.complete is True
    assert result.issues == ()
    assert result.candidates == (
        Candidate(
            relative_path="specs/09-Untracked specification.md",
            absolute_path=repository / "specs/09-Untracked specification.md",
            kind="spec",
        ),
        Candidate(
            relative_path="specs/attachments/09.Att.12-Untracked attachment.md",
            absolute_path=repository / "specs/attachments/09.Att.12-Untracked attachment.md",
            kind="attachment",
        ),
    )


def test_unsupported_windows_root_fails_before_filesystem_or_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = tmp_path / "must-not-be-read"
    monkeypatch.setattr(discovery, "windows_path_problem", lambda _path: "UNC is unsupported")
    monkeypatch.setattr(
        discovery,
        "_run_git",
        lambda *args, **kwargs: pytest.fail("unsupported root must not start Git"),
    )

    result = discover_candidates(requested)

    assert result.complete is False
    assert result.candidates == ()
    assert result.issues[0].summary == "The explicit repository root is unsupported on Windows"
    assert not requested.exists()


def test_only_exact_direct_regular_markdown_paths_are_candidates(repository: Path) -> None:
    _write(repository / "specs/01-Valid.md")
    _write(repository / "specs/attachments/01.Att.01-Valid.md")

    for relative_path in (
        "00-Outside-specs.md",
        "specs/1-Short-number.md",
        "specs/01_No-hyphen.md",
        "specs/01-Uppercase-extension.MD",
        "specs/01-.md",
        "specs/01.Att.01-Not-a-direct-spec.md",
        "specs/nested/02-Nested.md",
        "specs/attachments/1.Att.01-Short-parent.md",
        "specs/attachments/01.Att.1-Short-sequence.md",
        "specs/attachments/01.att.01-Wrong-marker.md",
        "specs/attachments/01.Att.02-Uppercase-extension.MD",
        "specs/attachments/nested/01.Att.03-Nested.md",
    ):
        _write(repository / relative_path)

    (repository / "specs/02-Directory.md").mkdir()
    (repository / "specs/attachments/01.Att.04-Directory.md").mkdir()

    result = discover_candidates(repository)

    assert result.complete is True
    assert [candidate.relative_path for candidate in result.candidates] == [
        "specs/01-Valid.md",
        "specs/attachments/01.Att.01-Valid.md",
    ]


def test_includes_current_files_regardless_of_git_ignore_status(repository: Path) -> None:
    _write(repository / ".gitignore", "specs/02-Ignored.md\nspecs/attachments/\n")
    _write(repository / "specs/01-Included.md")
    _write(repository / "specs/02-Ignored.md")
    _write(repository / "specs/attachments/01.Att.01-Ignored.md")

    result = discover_candidates(repository)

    assert result.complete is True
    assert result.issues == ()
    assert [candidate.relative_path for candidate in result.candidates] == [
        "specs/01-Included.md",
        "specs/02-Ignored.md",
        "specs/attachments/01.Att.01-Ignored.md",
    ]


def test_candidate_qualification_does_not_depend_on_index_or_ignore_status(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_path = "specs/01-Tracked.md"
    _write(repository / candidate_path)
    _commit(repository, candidate_path)
    _write(repository / ".gitignore", f"{candidate_path}\n")
    monkeypatch.setenv("GIT_INDEX_FILE", str(repository / "alternate-index"))

    result = discover_candidates(repository)

    assert result.complete is True
    assert result.issues == ()
    assert [candidate.relative_path for candidate in result.candidates] == [candidate_path]


def test_does_not_follow_candidate_file_symlinks_outside_worktree(
    repository: Path,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    _write(outside / "External-spec.md")
    _write(outside / "External-attachment.md")
    _write(repository / "specs/01-Regular.md")
    (repository / "specs/02-Linked.md").symlink_to(outside / "External-spec.md")
    (repository / "specs/attachments").mkdir()
    (repository / "specs/attachments/01.Att.01-Linked.md").symlink_to(outside / "External-attachment.md")

    result = discover_candidates(repository)

    assert result.complete is True
    assert result.issues == ()
    assert [candidate.relative_path for candidate in result.candidates] == ["specs/01-Regular.md"]


def test_does_not_follow_symlinked_specs_directory_outside_worktree(
    repository: Path,
    tmp_path: Path,
) -> None:
    outside_specs = tmp_path / "outside-specs"
    _write(outside_specs / "01-External.md")
    _write(outside_specs / "attachments/01.Att.01-External.md")
    (repository / "specs").symlink_to(outside_specs, target_is_directory=True)

    result = discover_candidates(repository)

    assert result.complete is True
    assert result.issues == ()
    assert result.candidates == ()


def test_rejects_linked_repository_root(repository: Path, tmp_path: Path) -> None:
    linked_root = tmp_path / "linked-repository"
    try:
        linked_root.symlink_to(repository, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    result = discover_candidates(linked_root)

    assert result.complete is False
    assert result.candidates == ()
    assert len(result.issues) == 1
    assert "link or reparse" in result.issues[0].summary


def test_does_not_enter_reparse_specs_directory(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = repository / "specs/01-Outside.md"
    _write(candidate)
    specs_inode = (repository / "specs").lstat().st_ino
    real_is_link_or_reparse = discovery.is_link_or_reparse

    def simulated_reparse(observation: object) -> bool:
        return getattr(observation, "st_ino", None) == specs_inode or real_is_link_or_reparse(observation)

    monkeypatch.setattr(discovery, "is_link_or_reparse", simulated_reparse)

    result = discover_candidates(repository)

    assert result.complete is True
    assert result.issues == ()
    assert result.candidates == ()


def test_file_replaced_by_external_symlink_before_revalidation_is_rejected(
    repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_path = "specs/01-Replaced.md"
    candidate = repository / candidate_path
    outside = tmp_path / "outside.md"
    _write(candidate)
    _write(outside, "outside\n")
    real_revalidate = discovery._revalidate_observations

    def replace_before_revalidation(
        observations: tuple[object, ...],
        directories: tuple[object, ...],
        *,
        phase: str,
    ) -> tuple[tuple[object, ...], list[object]]:
        candidate.unlink()
        candidate.symlink_to(outside)
        return real_revalidate(observations, directories, phase=phase)  # type: ignore[arg-type,return-value]

    monkeypatch.setattr(discovery, "_revalidate_observations", replace_before_revalidation)

    result = discover_candidates(repository)

    assert result.complete is False
    assert result.candidates == ()
    assert len(result.issues) == 1
    assert result.issues[0].location.path == "specs"
    assert result.issues[0].affected == (candidate_path,)


def test_candidate_added_to_same_directory_before_revalidation_invalidates_scope(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_path = "specs/01-Original.md"
    added_path = "specs/02-Added-during-query.md"
    _write(repository / original_path)
    real_revalidate = discovery._revalidate_observations

    def add_before_revalidation(
        observations: tuple[object, ...],
        directories: tuple[object, ...],
        *,
        phase: str,
    ) -> tuple[tuple[object, ...], list[object]]:
        _write(repository / added_path)
        return real_revalidate(observations, directories, phase=phase)  # type: ignore[arg-type,return-value]

    monkeypatch.setattr(discovery, "_revalidate_observations", add_before_revalidation)

    result = discover_candidates(repository)

    assert result.complete is False
    assert result.candidates == ()
    assert len(result.issues) == 1
    assert result.issues[0].location.path == "specs"
    assert result.issues[0].affected == (original_path, added_path)


def test_missing_attachments_directory_created_before_revalidation_is_detected(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_path = "specs/01-Original.md"
    added_path = "specs/attachments/01.Att.01-Added-during-query.md"
    _write(repository / original_path)
    real_revalidate = discovery._revalidate_observations

    def add_attachment_before_revalidation(
        observations: tuple[object, ...],
        directories: tuple[object, ...],
        *,
        phase: str,
    ) -> tuple[tuple[object, ...], list[object]]:
        _write(repository / added_path)
        return real_revalidate(observations, directories, phase=phase)  # type: ignore[arg-type,return-value]

    monkeypatch.setattr(discovery, "_revalidate_observations", add_attachment_before_revalidation)

    result = discover_candidates(repository)

    assert result.complete is False
    assert [candidate.relative_path for candidate in result.candidates] == [original_path]
    assert len(result.issues) == 1
    assert result.issues[0].location.path == "specs/attachments"
    assert result.issues[0].affected == ("specs/attachments",)


def test_directory_replaced_before_revalidation_only_invalidates_its_scope(
    repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    direct_path = "specs/01-Unaffected.md"
    attachment_path = "specs/attachments/01.Att.01-Replaced.md"
    _write(repository / direct_path)
    _write(repository / attachment_path)
    outside_attachments = tmp_path / "outside-attachments"
    _write(outside_attachments / "01.Att.01-Replaced.md", "outside\n")
    attachments = repository / "specs/attachments"
    real_revalidate = discovery._revalidate_observations

    def replace_before_revalidation(
        observations: tuple[object, ...],
        directories: tuple[object, ...],
        *,
        phase: str,
    ) -> tuple[tuple[object, ...], list[object]]:
        attachments.rename(repository / "specs/saved-attachments")
        attachments.symlink_to(outside_attachments, target_is_directory=True)
        return real_revalidate(observations, directories, phase=phase)  # type: ignore[arg-type,return-value]

    monkeypatch.setattr(discovery, "_revalidate_observations", replace_before_revalidation)

    result = discover_candidates(repository)

    assert result.complete is False
    assert [candidate.relative_path for candidate in result.candidates] == [direct_path]
    assert len(result.issues) == 1
    assert result.issues[0].location.path == "specs/attachments"
    assert result.issues[0].affected == (attachment_path,)


def test_does_not_restore_a_worktree_file_deleted_since_head(repository: Path) -> None:
    deleted = repository / "specs/01-Deleted.md"
    _write(deleted)
    _commit(repository, "specs/01-Deleted.md")
    deleted.unlink()
    _write(repository / "specs/02-Untracked.md")

    result = discover_candidates(repository)

    assert result.complete is True
    assert [candidate.relative_path for candidate in result.candidates] == ["specs/02-Untracked.md"]


def test_rejects_a_directory_that_is_not_a_git_worktree_root(tmp_path: Path) -> None:
    non_repository = tmp_path / "not-a-repository"
    non_repository.mkdir()

    result = discover_candidates(non_repository)

    assert result.complete is False
    assert result.candidates == ()
    assert len(result.issues) == 1
    assert result.issues[0].location.path == "."
    assert "Git worktree root" in result.issues[0].summary


def test_rejects_a_subdirectory_of_a_git_worktree(repository: Path) -> None:
    specs_directory = repository / "specs"
    specs_directory.mkdir()

    result = discover_candidates(specs_directory)

    assert result.complete is False
    assert result.candidates == ()
    assert len(result.issues) == 1
    assert "not its root" in result.issues[0].summary


def test_repository_selection_environment_cannot_redirect_discovery(
    repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ordinary_directory = tmp_path / "ordinary-directory"
    _write(ordinary_directory / "specs/01-False-candidate.md")
    monkeypatch.setenv("GIT_DIR", str(repository / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(ordinary_directory))

    result = discover_candidates(ordinary_directory)

    assert result.complete is False
    assert result.candidates == ()
    assert len(result.issues) == 1
    assert "Git worktree root" in result.issues[0].summary


def test_git_executable_failure_is_reported_as_incomplete(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable_git(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError("git executable missing")

    monkeypatch.setattr(discovery.subprocess, "run", unavailable_git)

    result = discover_candidates(repository)

    assert result.complete is False
    assert result.candidates == ()
    assert len(result.issues) == 1
    assert result.issues[0].cause == "git executable missing"
    assert result.issues[0].affected == (".",)


def test_worktree_query_failure_is_reported_as_incomplete(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failed_worktree_query(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(
            command,
            returncode=128,
            stdout=b"",
            stderr=b"simulated worktree failure",
        )

    monkeypatch.setattr(discovery.subprocess, "run", failed_worktree_query)

    result = discover_candidates(repository)

    assert result.complete is False
    assert result.candidates == ()
    assert len(result.issues) == 1
    assert result.issues[0].cause == "simulated worktree failure"


def test_discovery_does_not_query_per_file_git_status(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_path = "specs/01-Ignored.md"
    _write(repository / ".gitignore", f"{candidate_path}\n")
    _write(repository / candidate_path)
    real_run = subprocess.run

    def reject_per_file_status_query(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[bytes]:
        assert "check-ignore" not in command
        assert "ls-files" not in command
        return real_run(command, **kwargs)

    monkeypatch.setattr(discovery.subprocess, "run", reject_per_file_status_query)

    result = discover_candidates(repository)

    assert result.complete is True
    assert [candidate.relative_path for candidate in result.candidates] == [candidate_path]


def _write(path: Path, content: str = "# candidate\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit(repository: Path, *paths: str) -> None:
    _git(repository, "add", *paths)
    _git(
        repository,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "add candidates",
    )


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
    )
