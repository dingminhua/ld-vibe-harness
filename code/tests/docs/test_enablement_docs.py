from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_readme_exposes_environment_neutral_five_step_flow() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

    assert "获取 → 安装 → 配置 → 接入 → 验证" in readme
    assert "specs/attachments/09.Att.01-环境接入面.md" in readme
    assert "specs/33-环境接入安装与验证行动模板.md" in readme
    assert "ldvh capabilities" in readme
    assert "ldvh-doctor" in readme


def test_integration_surface_attachment_matches_current_distribution_entry_points() -> None:
    project = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    surfaces = (REPOSITORY_ROOT / "specs/attachments/09.Att.01-环境接入面.md").read_text(encoding="utf-8")

    for entry_point in (
        "ldvh",
        "ldvh-doctor",
        "ldvh-context-recovery",
        "ldvh-git-commit-msg",
        "ldvh-git-hook",
    ):
        assert entry_point in project
        assert f"`{entry_point}`" in surfaces
    assert "统一厂商 payload" in surfaces
    assert "新增 manifest" in surfaces


def test_ai_enablement_guide_keeps_capability_and_evidence_boundaries() -> None:
    template = (REPOSITORY_ROOT / "specs/33-环境接入安装与验证行动模板.md").read_text(encoding="utf-8")

    assert "#### A. 建立目标与当前基线" in template
    assert "不只看" in template
    assert "unverified" in template
    assert "unsupported" in template
    assert "肯定依据证明不存在" in template
    assert "fixture" in template