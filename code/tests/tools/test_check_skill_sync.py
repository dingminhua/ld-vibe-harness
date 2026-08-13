"""Tests for the tools/check_skill_sync.py skill/hook alignment tool."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tools import check_skill_sync as tool_module

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _write_skill(path: Path, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"> Skill 版本：{version}\n", encoding="utf-8")


class TestVersionLine:
    def test_extracts_version_marker(self) -> None:
        path = PROJECT_ROOT / "skill" / "SKILL.md"
        assert path.is_file()
        version = tool_module._version_line(path)
        assert version is not None
        assert version.startswith("Skill 版本：")

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        assert tool_module._version_line(tmp_path / "missing.md") is None


class TestCheckSkillCopy:
    def test_aligned_when_identical(self) -> None:
        aligned, detail = tool_module.check_skill_copy(sync=False)
        assert aligned is True
        assert detail["project_version"] == detail["user_version"]

    def test_misaligned_when_different(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        with patch.object(tool_module, "USER_SKILL_DEFAULT", target):
            aligned, detail = tool_module.check_skill_copy(sync=False)
        assert aligned is False
        assert detail["user_version"] == "Skill 版本：2026-08-12 07:17"

    def test_sync_copies_project_source(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        with patch.object(tool_module, "USER_SKILL_DEFAULT", target):
            aligned, detail = tool_module.check_skill_copy(sync=True)
        assert aligned is True
        assert detail["synced"] is True
        assert target.read_text(encoding="utf-8") == (PROJECT_ROOT / "skill" / "SKILL.md").read_text(
            encoding="utf-8"
        )


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

    def test_non_git_directory_fails(self, tmp_path: Path) -> None:
        aligned, detail = tool_module.check_worktree_coverage(tmp_path)
        assert aligned is False
        assert "error" in detail


class TestMainExitCodes:
    def test_aligned_run_exits_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_skill_sync.py"])
        assert tool_module.main() == 0

    def test_misaligned_run_exits_one(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_skill_sync.py"])
        target = tmp_path / "SKILL.md"
        _write_skill(target, "2026-08-12 07:17")
        with patch.object(tool_module, "USER_SKILL_DEFAULT", target):
            assert tool_module.main() == 1
