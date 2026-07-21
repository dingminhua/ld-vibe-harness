from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_readme_exposes_environment_neutral_five_step_flow() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

    assert "获取 → 安装 → 配置 → 接入 → 验证" in readme
    assert "docs/启用与AI环境接入.md" in readme
    assert "docs/LDVH接入面.md" in readme
    assert "不预先维护所有厂商" in readme
    assert "unsupported" in readme
    assert "unverified" in readme


def test_integration_surface_doc_matches_current_distribution_entry_points() -> None:
    project = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    surfaces = (REPOSITORY_ROOT / "docs/LDVH接入面.md").read_text(encoding="utf-8")

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
    guide = (REPOSITORY_ROOT / "docs/启用与AI环境接入.md").read_text(encoding="utf-8")

    for heading in ("## 1. 获取", "## 2. 安装", "## 3. 配置", "## 4. 接入", "## 5. 验证"):
        assert heading in guide
    assert "本地 wheel 不等于" in guide
    assert "不要只搜索 “Hook”" in guide
    assert "停止安装，先形成独立 Code 计划" in guide
    assert "资料或权限不足，保持 unverified" in guide
    assert "肯定依据证明所需自动机制不存在" in guide
    assert "fixture 或 shell 直调当成真实触发" in guide
