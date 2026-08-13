"""Tests for the tools/check_skill_sync.py skill/hook alignment tool."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tools import check_skill_sync as tool_module

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PLATFORM = "claude-code"
SKILL_PATH = str(PROJECT_ROOT / "skill" / "SKILL.md")


def _write_skill(path: Path, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nname: ldvh\ndescription: test\n---\n\n> Skill 版本：{version}\n",
        encoding="utf-8",
    )


def _run_main(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (str(PROJECT_ROOT / "tools" / "check_skill_sync.py"), *arguments),
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
    )


class TestSkillVersion:
    def test_reads_target_version(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        assert tool_module._read_skill_version(target) == "Skill 版本：2026-08-12 07:17"

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        assert tool_module._read_skill_version(tmp_path / "missing.md") is None

    def test_ldvh_frontmatter_detection(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        assert tool_module._has_ldvh_frontmatter(target) is True
        not_skill = tmp_path / "other.md"
        not_skill.write_text("just some text\n", encoding="utf-8")
        assert tool_module._has_ldvh_frontmatter(not_skill) is False


class TestCheckSkillCopy:
    def test_aligned_when_identical(self) -> None:
        aligned, detail = tool_module.check_skill_copy(
            skill_path=SKILL_PATH, platform=PLATFORM, sync=False, confirm_human_gate=False
        )
        assert aligned is True
        assert detail["target_version"] == detail["project_version"]

    def test_misaligned_when_different(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        aligned, detail = tool_module.check_skill_copy(
            skill_path=str(target), platform=PLATFORM, sync=False, confirm_human_gate=False
        )
        assert aligned is False
        assert detail["target_version"] == "Skill 版本：2026-08-12 07:17"

    def test_sync_requires_gate(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        original = target.read_bytes()
        aligned, detail = tool_module.check_skill_copy(
            skill_path=str(target), platform=PLATFORM, sync=True, confirm_human_gate=False
        )
        assert aligned is False
        assert detail.get("synced") is not True
        assert target.read_bytes() == original

    def test_sync_copies_project_source_with_gate(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        aligned, detail = tool_module.check_skill_copy(
            skill_path=str(target), platform=PLATFORM, sync=True, confirm_human_gate=True
        )
        assert aligned is True
        assert detail["synced"] is True
        assert target.read_bytes() == (PROJECT_ROOT / "skill" / "SKILL.md").read_bytes()


class TestStopGate:
    def test_wrapper_delegates_to_implementation(self) -> None:
        aligned, detail = tool_module.check_stop_gate()
        assert aligned is True
        assert detail["wrapper_exists"] is True
        assert detail["implementation_exists"] is True
        assert detail["wrapper_references_implementation"] is True


class TestWorktreeCoverage:
    def test_project_worktrees_share_common_dir(self) -> None:
        aligned, detail = tool_module.check_worktree_coverage(PROJECT_ROOT)
        assert aligned is True
        assert len(detail["distinct_common_dirs"]) == 1

    def test_linked_worktree_absolute_common_dir_is_preserved(self, tmp_path: Path) -> None:
        repository = tmp_path / "repository"
        linked = tmp_path / "linked"
        repository.mkdir()
        subprocess.run(("git", "-C", str(repository), "init", "-q"), check=True)
        subprocess.run(("git", "-C", str(repository), "config", "user.name", "LDVH Test"), check=True)
        subprocess.run(("git", "-C", str(repository), "config", "user.email", "ldvh@example.invalid"), check=True)
        (repository / "initial.txt").write_text("initial\n", encoding="utf-8")
        subprocess.run(("git", "-C", str(repository), "add", "initial.txt"), check=True)
        subprocess.run(("git", "-C", str(repository), "commit", "-qm", "initial"), check=True)
        subprocess.run(("git", "-C", str(repository), "worktree", "add", "-q", str(linked)), check=True)
        common = Path(tool_module._run_git(linked, "rev-parse", "--git-common-dir") or "")
        assert common.is_absolute()
        completed = _run_main(
            "--platform",
            PLATFORM,
            "--skill-path",
            SKILL_PATH,
            "--worktree",
            str(linked),
            "--json",
        )
        report = __import__("json").loads(completed.stdout)
        assert report["common_hooks_dir"] == str(common.resolve() / "hooks")

    def test_non_git_directory_fails(self, tmp_path: Path) -> None:
        aligned, detail = tool_module.check_worktree_coverage(tmp_path)
        assert aligned is False
        assert "error" in detail


class TestMainExitCodes:
    def test_aligned_run_exits_zero(self) -> None:
        completed = _run_main("--platform", PLATFORM, "--skill-path", SKILL_PATH, "--json")
        assert completed.returncode == 0

    def test_misaligned_run_exits_one_with_unknown_target(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        completed = _run_main(
            "--platform", PLATFORM, "--skill-path", str(target), "--json"
        )
        assert completed.returncode == 1

    def test_sync_without_gate_exits_two(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        original = target.read_bytes()
        completed = _run_main(
            "--platform", PLATFORM, "--skill-path", str(target), "--sync"
        )
        assert completed.returncode == 2
        assert target.read_bytes() == original
