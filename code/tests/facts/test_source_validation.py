from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ldvh.facts import repository as fact_repository
from ldvh.facts.models import FactIssue
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult
from ldvh.facts.source_validation import validate_study_sources


def _git(project: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _index(tmp_path: Path) -> tuple[ProjectFactIndex, str]:
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    (project / "docs").mkdir()
    (project / "docs" / "input.md").write_text("input\n", encoding="utf-8")
    _git(project, "add", ".")
    _git(project, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "input")
    common_dir = Path(_git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return ProjectFactIndex(project, "sample", {}, common_dir), _git(project, "rev-parse", "HEAD")


def _read(*references: dict[str, str]) -> FactReadResult:
    return FactReadResult(
        "ldvh-base/studies/study-0001.md",
        "markdown",
        "mechanically_valid",
        {"source_refs": list(references), "evidence_refs": []},
        "body",
        (),
    )


def test_study_repository_source_must_exist_and_be_git_traceable(tmp_path: Path) -> None:
    index, _ = _index(tmp_path)
    valid_issues, valid_unavailable = validate_study_sources(
        index,
        _read({"kind": "repository-path", "locator": "docs/input.md"}),
    )
    missing_issues, missing_unavailable = validate_study_sources(
        index,
        _read({"kind": "repository-path", "locator": "docs/missing.md"}),
    )
    assert valid_issues == () and valid_unavailable is False
    assert missing_unavailable is False
    assert missing_issues and isinstance(missing_issues[0], FactIssue)


def test_study_git_revision_binds_locator_to_a_real_commit(tmp_path: Path) -> None:
    index, commit = _index(tmp_path)
    valid, unavailable = validate_study_sources(
        index,
        _read({"kind": "git-revision", "locator": "docs/input.md", "version": commit}),
    )
    invalid, invalid_unavailable = validate_study_sources(
        index,
        _read({"kind": "git-revision", "locator": "docs/input.md", "version": "not-a-ref"}),
    )
    assert valid == () and unavailable is False
    assert invalid_unavailable is False
    assert any("commit" in issue.summary for issue in invalid)


def test_study_fact_object_reference_requires_a_valid_current_target(tmp_path: Path) -> None:
    index, _ = _index(tmp_path)
    issues, unavailable = validate_study_sources(
        index,
        _read({"kind": "fact-object", "locator": "ldvh-base/sparks/spark-9999.yaml"}),
    )
    assert unavailable is False
    assert any("mechanically valid" in issue.summary for issue in issues)


def test_runtime_and_human_artifacts_accept_ignored_current_files_but_reject_symlinks(tmp_path: Path) -> None:
    index, _ = _index(tmp_path)
    evidence = index.root / "evidence"
    evidence.mkdir()
    (evidence / "runtime.json").write_text("{}\n", encoding="utf-8")
    (evidence / "human.pdf").write_bytes(b"artifact")
    _git(index.root, "add", "evidence")
    _git(index.root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "evidence")

    valid, unavailable = validate_study_sources(
        index,
        _read(
            {"kind": "runtime-observation", "locator": "evidence/runtime.json", "version": "tool-v1"},
            {"kind": "human-provided-artifact", "locator": "evidence/human.pdf"},
        ),
    )
    assert valid == () and unavailable is False

    (index.root / ".gitignore").write_text("evidence/ignored.txt\n", encoding="utf-8")
    (evidence / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    (evidence / "linked.txt").symlink_to(evidence / "human.pdf")
    checked, checked_unavailable = validate_study_sources(
        index,
        _read(
            {"kind": "runtime-observation", "locator": "evidence/ignored.txt", "version": "tool-v1"},
            {"kind": "human-provided-artifact", "locator": "evidence/linked.txt"},
        ),
    )
    assert checked_unavailable is False
    assert len(checked) == 1
    assert checked[0].category == "location"
    assert checked[0].field_path == "source_refs[1].locator"


def test_git_revision_technical_failure_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index, commit = _index(tmp_path)
    monkeypatch.setattr("ldvh.facts.source_validation._git", lambda *_args: None)
    issues, unavailable = validate_study_sources(
        index,
        _read({"kind": "git-revision", "locator": "docs/input.md", "version": commit}),
    )
    assert unavailable is True
    assert any(issue.category == "git-traceability" for issue in issues)


def test_non_utf8_git_identity_output_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid = subprocess.CompletedProcess([], 0, b"/workspace/\xff\n.git\n", b"")
    monkeypatch.setattr(fact_repository, "_git", lambda *_args: invalid)

    assert fact_repository._git_identity(tmp_path) is None
