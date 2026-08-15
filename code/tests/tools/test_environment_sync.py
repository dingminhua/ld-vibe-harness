"""Tests for the platform-explicit environment-sync inspect/update surface.

Covers: arbitrary platform labels with different paths, missing/relative paths,
read-only zero-write, no-gate zero-write, create-when-absent, unknown-file conflict,
atomic upgrade of an old LDVH Skill, the Helper contract shape, and a temporary repo
inspect -> update -> inspect round trip.  Existing Hook logic semantics are preserved
by reusing the Git Hook manager.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from ldvh.environment_sync import inspect_skill, update_skill

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_SKILL = REPOSITORY_ROOT / "skill" / "SKILL.md"
LAUNCHER = REPOSITORY_ROOT / "ldvh"


@pytest.fixture(autouse=True)
def _isolated_git_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for key in tuple(os.environ):
        if key in {"GIT_CONFIG_COUNT", "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"} or key.startswith(
            ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
        ):
            monkeypatch.delenv(key, raising=False)


def _write_ldvh_skill(path: Path, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nname: ldvh\ndescription: 测试 Skill\n---\n\n> Skill 版本：{version}\n",
        encoding="utf-8",
    )


def _write_unknown_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("this is not an LDVH skill at all\n", encoding="utf-8")


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": "LDVH Test",
            "GIT_AUTHOR_EMAIL": "ldvh@example.invalid",
            "GIT_COMMITTER_NAME": "LDVH Test",
            "GIT_COMMITTER_EMAIL": "ldvh@example.invalid",
        }
    )
    return environment


def _git(path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", "-C", str(path), *arguments),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        env=_environment(),
    )


def _managed_workspace(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    _git(project, "config", "user.name", "LDVH Test")
    _git(project, "config", "user.email", "ldvh@example.invalid")
    (project / "initial.txt").write_text("initial\n", encoding="utf-8")
    _git(project, "add", "initial.txt")
    _git(project, "commit", "-qm", "initial")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            (
                "governance_instance_name: Sync Tests",
                "product_description: environment-sync tests.",
                "projects:",
                "  - id: sample",
                f"    path: {project}",
                "    name: Sample",
                "    description: Sync test.",
                "",
            )
        ),
        encoding="utf-8",
    )
    return workspace, project


class TestArbitraryPlatformPaths:
    def test_different_label_same_source_aligned(self, tmp_path: Path) -> None:
        target = tmp_path / "claude" / "SKILL.md"
        _write_ldvh_skill(target, "2026-08-13 00:01")
        # make it byte-identical to canonical
        target.write_bytes(CANONICAL_SKILL.read_bytes())
        for label in ("claude-code", "codex", "cursor", "A-Platform-1"):
            skill = inspect_skill(platform=label, skill_path=str(target), source_path=CANONICAL_SKILL)
            assert skill.platform == label
            assert skill.byte_aligned is True
            assert skill.is_ldvh_skill is True

    def test_different_paths_reported_independently(self, tmp_path: Path) -> None:
        a = tmp_path / "a" / "SKILL.md"
        b = tmp_path / "b" / "SKILL.md"
        _write_ldvh_skill(a, "2026-08-13 00:01")
        _write_ldvh_skill(b, "2026-08-12 00:00")
        a.write_bytes(CANONICAL_SKILL.read_bytes())
        sa = inspect_skill(platform="p", skill_path=str(a), source_path=CANONICAL_SKILL)
        sb = inspect_skill(platform="p", skill_path=str(b), source_path=CANONICAL_SKILL)
        assert sa.byte_aligned is True
        assert sb.byte_aligned is False


class TestInvalidInputs:
    def test_empty_platform_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            inspect_skill(platform="", skill_path=str(tmp_path / "x"), source_path=CANONICAL_SKILL)

    def test_relative_skill_path_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            inspect_skill(platform="p", skill_path="relative/SKILL.md", source_path=CANONICAL_SKILL)


class TestReadOnlyZeroWrite:
    def test_inspect_does_not_create_or_modify(self, tmp_path: Path) -> None:
        target = tmp_path / "absent" / "SKILL.md"
        before = list(tmp_path.iterdir())
        skill = inspect_skill(platform="p", skill_path=str(target), source_path=CANONICAL_SKILL)
        after = list(tmp_path.iterdir())
        assert skill.exists is False
        assert not target.exists()
        assert before == after

    def test_inspect_leaves_existing_bytes_untouched(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_ldvh_skill(target, "2026-08-12 00:00")
        original = target.read_bytes()
        inspect_skill(platform="p", skill_path=str(target), source_path=CANONICAL_SKILL)
        assert target.read_bytes() == original


class TestNoGateZeroWrite:
    def test_update_without_gate_does_not_write(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_ldvh_skill(target, "2026-08-12 00:00")
        original = target.read_bytes()
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=CANONICAL_SKILL,
            human_gate_confirmed=False,
        )
        assert outcome.aligned is False
        assert outcome.replaced is False
        assert outcome.conflict is False
        assert target.read_bytes() == original

    def test_update_without_gate_does_not_create(self, tmp_path: Path) -> None:
        target = tmp_path / "absent" / "SKILL.md"
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=CANONICAL_SKILL,
            human_gate_confirmed=False,
        )
        assert not target.exists()
        assert outcome.created is False


class TestCreateWhenAbsent:
    def test_update_creates_target(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "SKILL.md"
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=CANONICAL_SKILL,
            human_gate_confirmed=True,
        )
        assert outcome.created is True
        assert outcome.aligned is True
        assert target.read_bytes() == CANONICAL_SKILL.read_bytes()


class TestUnknownFileConflict:
    def test_unknown_file_not_overwritten(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_unknown_file(target)
        original = target.read_bytes()
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=CANONICAL_SKILL,
            human_gate_confirmed=True,
        )
        assert outcome.conflict is True
        assert outcome.replaced is False
        assert target.read_bytes() == original

    def test_existing_directory_is_not_replaced(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        target.mkdir()
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=CANONICAL_SKILL,
            human_gate_confirmed=True,
        )
        assert outcome.conflict is True
        assert target.is_dir()

    def test_symlink_target_is_not_replaced(self, tmp_path: Path) -> None:
        backing = tmp_path / "backing.md"
        _write_ldvh_skill(backing, "2026-08-12 00:00")
        target = tmp_path / "SKILL.md"
        target.symlink_to(backing)
        original = backing.read_bytes()
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=CANONICAL_SKILL,
            human_gate_confirmed=True,
        )
        assert outcome.conflict is True
        assert target.is_symlink()
        assert backing.read_bytes() == original

    def test_missing_canonical_source_does_not_write(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_ldvh_skill(target, "2026-08-12 00:00")
        original = target.read_bytes()
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=tmp_path / "missing-canonical.md",
            human_gate_confirmed=True,
        )
        assert outcome.aligned is False
        assert outcome.conflict is False
        assert target.read_bytes() == original


class TestAtomicUpgrade:
    def test_old_ldvh_skill_replaced_atomically(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_ldvh_skill(target, "2026-08-12 00:00")
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=CANONICAL_SKILL,
            human_gate_confirmed=True,
        )
        assert outcome.replaced is True
        assert outcome.aligned is True
        assert target.read_bytes() == CANONICAL_SKILL.read_bytes()

    def test_upgrade_failure_preserves_original(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        target = tmp_path / "SKILL.md"
        _write_ldvh_skill(target, "2026-08-12 00:00")
        original = target.read_bytes()

        real_replace = os.replace

        def _boom(src: str, dst: str) -> None:
            if str(dst) == str(target):
                raise OSError("simulated failure")
            real_replace(src, dst)

        monkeypatch.setattr(os, "replace", _boom)
        with pytest.raises(OSError):
            update_skill(
                platform="p",
                skill_path=str(target),
                source_path=CANONICAL_SKILL,
                human_gate_confirmed=True,
            )
        assert target.read_bytes() == original


class TestHelperContractShape:
    def test_inspect_contract_fields(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        target.write_bytes(CANONICAL_SKILL.read_bytes())
        skill = inspect_skill(platform="claude-code", skill_path=str(target), source_path=CANONICAL_SKILL)
        assert skill.platform == "claude-code"
        assert skill.skill_path == str(target)
        assert skill.target_version == skill.source_version
        assert skill.byte_aligned is True
        assert skill.version_aligned is True


class TestLauncherInspectUpdateRoundTrip:
    def _run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            (str(LAUNCHER), "environment-sync", *arguments),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env={**_environment(), "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
        )

    def test_inspect_readonly_then_update_then_inspect(self, tmp_path: Path) -> None:
        _, project = _managed_workspace(tmp_path)
        target = tmp_path / "target" / "SKILL.md"
        _write_ldvh_skill(target, "2026-08-12 00:00")

        inspect0 = self._run(
            "inspect", "--platform", "claude-code", "--skill-path", str(target)
        )
        assert inspect0.returncode == 0
        assert not target.read_bytes() == CANONICAL_SKILL.read_bytes()

        update = self._run(
            "update",
            "--platform",
            "claude-code",
            "--skill-path",
            str(target),
            "--worktree",
            str(project),
            "--commit-msg-runner",
            str(LAUNCHER),
            "--confirm-human-gate",
        )
        assert update.returncode == 0
        assert target.read_bytes() == CANONICAL_SKILL.read_bytes()

        inspect1 = self._run(
            "inspect", "--platform", "claude-code", "--skill-path", str(target)
        )
        assert inspect1.returncode == 0
        report = __import__("json").loads(inspect1.stdout)
        assert report["skill"]["byte_aligned"] is True

    def test_update_without_gate_zero_write(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_unknown_file(target)
        original = target.read_bytes()
        update = self._run("update", "--platform", "p", "--skill-path", str(target))
        assert update.returncode == 2
        assert target.read_bytes() == original

    def test_update_uses_current_worktree_defaults(self, tmp_path: Path) -> None:
        _, project = _managed_workspace(tmp_path)
        target = tmp_path / "target" / "SKILL.md"
        _write_ldvh_skill(target, "2026-08-12 00:00")
        completed = subprocess.run(
            (
                str(LAUNCHER),
                "environment-sync",
                "update",
                "--platform",
                "claude-code",
                "--skill-path",
                str(target),
                "--confirm-human-gate",
            ),
            cwd=project,
            capture_output=True,
            text=True,
            env={**_environment(), "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
        )
        assert completed.returncode == 0
        assert target.read_bytes() == CANONICAL_SKILL.read_bytes()

    def test_skill_conflict_does_not_install_hook(self, tmp_path: Path) -> None:
        _, project = _managed_workspace(tmp_path)
        target = tmp_path / "unknown" / "SKILL.md"
        _write_unknown_file(target)
        completed = subprocess.run(
            (
                str(LAUNCHER),
                "environment-sync",
                "update",
                "--platform",
                "claude-code",
                "--skill-path",
                str(target),
                "--confirm-human-gate",
            ),
            cwd=project,
            capture_output=True,
            text=True,
            env={**_environment(), "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
        )
        assert completed.returncode == 1
        common_dir = _git(project, "rev-parse", "--git-common-dir").stdout.strip()
        common_path = Path(common_dir)
        if not common_path.is_absolute():
            common_path = (project / common_path).resolve()
        assert not (common_path / "hooks" / "commit-msg").exists()

    def test_missing_platform_errors(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        result = self._run("inspect", "--skill-path", str(target))
        assert result.returncode == 2
