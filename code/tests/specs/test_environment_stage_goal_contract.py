from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CREATION_TEMPLATE = ROOT / "specs/31-事实对象判定与受控创建行动模板.md"
EXECUTION_TEMPLATE = ROOT / "specs/34-WorkCase获批计划执行行动模板.md"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_gate1_environment_goal_uses_only_fresh_public_projection_as_success() -> None:
    source = _source(CREATION_TEMPLATE)

    assert "Gate 1 非持久化环境阶段 Goal" in source
    assert "另行公开精确回读" in source
    assert "`resolution=resolved`" in source
    assert "`source_content_fingerprint`" in source
    assert "`content_fingerprint`" in source
    assert "`handoff_narrative_key=gate1_waiting`" in source
    assert "`next_required_control_step=human_gate_1`" in source
    assert "内部回读或工具返回成功都不是完成依据" in source


def test_gate2_environment_goal_does_not_complete_at_intermediate_milestones() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "Gate 2 非持久化环境阶段 Goal" in source
    assert "另行公开精确回读" in source
    assert "`resolution=resolved`" in source
    assert "`source_content_fingerprint`" in source
    assert "`handoff_narrative_key=gate2_waiting`" in source
    assert "`next_required_control_step=human_gate_2`" in source
    for milestone in (
        "item terminal",
        "测试通过",
        "Reviewer 返回",
        "结果形成",
        "本地 commit",
        "closure proposal",
    ):
        assert milestone in source
    assert "都不是完成依据" in source


def test_environment_goal_is_optional_host_neutral_and_not_ldvh_state() -> None:
    for path in (CREATION_TEMPLATE, EXECUTION_TEMPLATE):
        source = _source(path)
        assert "非持久化环境阶段 Goal" in source
        assert "不是 LDVH 事实对象、状态、授权、投影或第二调度器" in source
        assert "不写入 canonical 载体或模板运行字段" in source
        assert "能力不可用、不可观察、存在冲突或调用失败时" in source
        assert "不伪造 Goal，不引入适配层" in source
        for host_api_name in ("create_goal", "get_goal", "update_goal"):
            assert host_api_name not in source


def test_environment_goal_safe_exits_are_not_reported_as_stage_success() -> None:
    for path, gate in ((CREATION_TEMPLATE, "Gate 1"), (EXECUTION_TEMPLATE, "Gate 2")):
        source = _source(path)
        assert "真实 blocked、持续 unresolved、Human 主动中止或对象 closed" in source
        assert f"不得被写成该 {gate} 阶段 Goal 的成功" in source
        assert "宿主真实支持的保持、阻塞或取消语义" in source
