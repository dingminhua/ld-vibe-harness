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

from ldvh.environment_sync import inspect_skill, update_skill, validate_skill_frontmatter

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


def _write_broken_frontmatter(path: Path, version: str = "2026-08-12 00:00") -> None:
    """A skill whose frontmatter is byte-identical to a legal one except for a
    plain-scalar `: ` inside the description — the exact shape that runtime
    loaders silently drop (see validate_skill_frontmatter)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nname: ldvh\ndescription: `status: unavailable` 恢复时使用\n---\n\n> Skill 版本：{version}\n",
        encoding="utf-8",
    )


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


class TestDirectorySkillPath:
    """09 §5.9.1: skill_path may point at the skill directory; the directory is
    resolved to its SKILL.md so is_file()/read_bytes() behave consistently."""

    def inspect_via_directory(self, tmp_path: Path, target: Path):
        # make target byte-identical to canonical so alignment is determinable
        target.write_bytes(CANONICAL_SKILL.read_bytes())
        return inspect_skill(
            platform="p",
            skill_path=str(tmp_path),  # the directory, not the file
            source_path=CANONICAL_SKILL,
        )

    def test_inspect_resolves_directory_to_skill_md(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        skill = self.inspect_via_directory(tmp_path, target)
        assert skill.exists is True
        assert skill.skill_path == str(target)
        assert skill.byte_aligned is True

    def test_inspect_directory_without_skill_md_reports_missing(self, tmp_path: Path) -> None:
        skill = inspect_skill(
            platform="p",
            skill_path=str(tmp_path),  # directory with no SKILL.md
            source_path=CANONICAL_SKILL,
        )
        assert skill.exists is False
        assert skill.skill_path == str(tmp_path / "SKILL.md")

    def test_directory_named_skill_md_is_not_resolved(self, tmp_path: Path) -> None:
        dir_target = tmp_path / "SKILL.md"
        dir_target.mkdir()
        # A directory literally named SKILL.md must stay as-is (a write conflict
        # target), never be joined onto. read-only inspect sees it as non-file.
        skill = inspect_skill(
            platform="p",
            skill_path=str(dir_target),
            source_path=CANONICAL_SKILL,
        )
        assert skill.exists is False
        assert skill.skill_path == str(dir_target)


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


class TestFrontmatterValidationGate:
    """validate_skill_frontmatter is the deployment gate that byte-alignment
    cannot provide: a broken YAML frontmatter makes runtime loaders silently
    drop the whole skill file."""

    def test_legal_canonical_passes(self) -> None:
        valid, error = validate_skill_frontmatter(CANONICAL_SKILL)
        assert valid is True
        assert error is None

    def test_plain_scalar_colon_is_rejected(self, tmp_path: Path) -> None:
        broken = tmp_path / "SKILL.md"
        _write_broken_frontmatter(broken)
        valid, error = validate_skill_frontmatter(broken)
        assert valid is False
        assert error is not None
        assert "解析失败" in error

    def test_missing_name_rejected(self, tmp_path: Path) -> None:
        broken = tmp_path / "SKILL.md"
        broken.write_text("---\ndescription: 无 name\n---\n\n> Skill 版本：2026-08-12 00:00\n", encoding="utf-8")
        valid, error = validate_skill_frontmatter(broken)
        assert valid is False
        assert "name" in (error or "")

    def test_missing_description_rejected(self, tmp_path: Path) -> None:
        broken = tmp_path / "SKILL.md"
        broken.write_text("---\nname: ldvh\n---\n\n> Skill 版本：2026-08-12 00:00\n", encoding="utf-8")
        valid, error = validate_skill_frontmatter(broken)
        assert valid is False
        assert "description" in (error or "")

    def test_missing_fence_rejected(self, tmp_path: Path) -> None:
        broken = tmp_path / "SKILL.md"
        broken.write_text("name: ldvh\ndescription: x\n", encoding="utf-8")
        valid, error = validate_skill_frontmatter(broken)
        assert valid is False
        assert "围栏" in (error or "")

    def test_update_refuses_broken_source_even_with_gate(self, tmp_path: Path) -> None:
        broken_source = tmp_path / "source" / "SKILL.md"
        _write_broken_frontmatter(broken_source, version="2026-08-13 00:00")
        target = tmp_path / "target" / "SKILL.md"
        _write_ldvh_skill(target, "2026-08-12 00:00")
        original = target.read_bytes()
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=broken_source,
            human_gate_confirmed=True,
        )
        assert outcome.replaced is False
        assert outcome.created is False
        assert outcome.aligned is False
        assert "frontmatter 非法" in outcome.detail
        assert target.read_bytes() == original

    def test_update_refuses_broken_source_when_absent(self, tmp_path: Path) -> None:
        broken_source = tmp_path / "source" / "SKILL.md"
        _write_broken_frontmatter(broken_source, version="2026-08-13 00:00")
        target = tmp_path / "target" / "SKILL.md"
        outcome = update_skill(
            platform="p",
            skill_path=str(target),
            source_path=broken_source,
            human_gate_confirmed=True,
        )
        assert outcome.created is False
        assert outcome.replaced is False
        assert outcome.aligned is False
        assert "frontmatter 非法" in outcome.detail
        assert not target.exists()

    def test_inspect_reports_frontmatter_validity(self, tmp_path: Path) -> None:
        broken = tmp_path / "SKILL.md"
        _write_broken_frontmatter(broken)
        skill = inspect_skill(platform="p", skill_path=str(broken), source_path=CANONICAL_SKILL)
        assert skill.source_frontmatter_valid is True
        assert skill.target_frontmatter_valid is False
        assert skill.frontmatter_error is not None


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
