from __future__ import annotations

from pathlib import Path

from ldvh.facts.workcase_presentation import PHASE_PRESENTATION, derive_workcase_presentation

ROOT = Path(__file__).resolve().parents[3]
FOUNDATION = ROOT / "specs/06-行动模板基础规范.md"
EXECUTION_TEMPLATE = ROOT / "specs/34-WorkCase获批计划执行行动模板.md"
FINGERPRINT = "a" * 64


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_execution_template_has_only_the_five_controller_flow_sections() -> None:
    source = _source(EXECUTION_TEMPLATE)

    headings = [line for line in source.splitlines() if line.startswith("### 5.")]
    assert headings == [
        "### 5.1 前置精确读取",
        "### 5.2 执行循环",
        "### 5.3 稳定检查点",
        "### 5.4 合法退出",
        "### 5.5 恢复交还",
    ]
    assert "21 定义全部字段、phase、转换、quality gate 与投影语义" in source
    assert "32 组织受控写回" in source
    assert "本文不重述其闭集或成立条件" in source


def test_fresh_projection_is_required_but_does_not_replace_controller_judgment() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "`source_content_fingerprint` 与本次读取内容指纹精确相同" in source
    assert "缺失、不匹配、stale 或 unresolved 时先重新精确读取" in source
    assert "重复读取后仍不能形成 current 投影则只保留读取缺口" in source
    assert "每次成功回读后，AI Controller" in source
    assert "`next_required_control_step` 只指出结构上下一必经控制步骤" in source
    assert "不自动选择 item" in source
    assert "不允许 Code 推进 phase 或断言完成" in source


def test_execution_checkpoint_and_blocking_overlay_are_not_successful_exit_shortcuts() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "存在当前合法下一控制步骤时，Controller 继续消费已批准责任" in source
    assert "`phase=executing` 的普通 `in_progress` 检查点" in source
    assert "都不是完成出口" in source
    assert "`status=blocked` 时投影保留生命周期位置只用于定位" in source
    assert "不消费其中结构提示自动续跑" in source

    blocked = derive_workcase_presentation("blocked", "executing", FINGERPRINT)
    assert blocked["blocking_overlay"] is True
    assert blocked["handoff_narrative_key"] == "blocked_at_current_position"
    assert blocked["next_required_control_step"] == "advance_current_work_item"


def test_terminal_item_reenters_controller_without_becoming_workcase_terminal() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "`item terminal ≠ WorkCase execution terminal`" in source
    assert "刚回读且指纹匹配的 resolved projection 必须成为下一轮 Controller 输入" in source
    assert "仍有非 terminal item 时，Controller 继续" in source
    assert "全部 item terminal 时，则按 21 进入 `controller_checking` 并继续既有结果链" in source
    assert "该控制点不表示 phase 一律返回 `executing`" in source
    assert "单个 terminal item" in source
    assert "都不是完成出口" in source


def test_reviewer_pass_requires_controlled_writeback_before_gate2_handoff() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "Reviewer pass 只是一项实际 review 输入，不等于 Gate 2" in source
    assert "完整 after、CAS、精确回读与完整性审计" in source
    assert "直至真实快照进入 Human 关闭确认" in source
    assert "不能只输出聊天总结" in source

    for phase in ("independent_reviewing", "closure_preparing"):
        projection = derive_workcase_presentation("open", phase, FINGERPRINT)
        assert projection["handoff_narrative_key"] != "gate2_waiting"

    gate2 = derive_workcase_presentation("open", "human_closure_confirming", FINGERPRINT)
    assert gate2["handoff_narrative_key"] == "gate2_waiting"
    assert gate2["next_required_control_step"] == "human_gate_2"


def test_gate2_language_is_bound_to_the_just_read_resolved_projection() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "只有 resolved 投影的 `handoff_narrative_key=gate2_waiting`" in source
    assert (
        "`independent_reviewing`、`closure_preparing`、任何 blocked、stale 或 unresolved 快照均禁止这些结论" in source
    )

    projections = [
        derive_workcase_presentation(status, phase, FINGERPRINT)
        for status in ("open", "blocked")
        for phase in PHASE_PRESENTATION
    ]
    assert sum(item.get("handoff_narrative_key") == "gate2_waiting" for item in projections) == 1

    unresolved = derive_workcase_presentation("open", "executing", None)
    assert unresolved == {
        "contract_identity": "workcase-current-snapshot-presentation/1",
        "resolution": "unresolved",
        "source_content_fingerprint": None,
        "unresolved_reason": "missing_source_content_fingerprint",
    }


def test_derived_continuation_flags_are_not_persisted_or_reintroduced() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "continuation_required" not in source
    assert "execution_stalled" not in source
    assert "本文不保存运行日志、receipt、续跑字段或第二状态机" in source


def test_temporary_artifact_hygiene_has_one_minimal_common_home() -> None:
    foundation = _source(FOUNDATION)
    template = _source(EXECUTION_TEMPLATE)

    assert "### 8.7 临时工件的最小共同边界" in foundation
    assert "应优先把它们置于 Git Working Tree 外" in foundation
    assert "能够确认由本次行动创建" in foundation
    assert "仍有继续、恢复或交接价值的内容不得删除" in foundation
    assert "不把 clean Working Tree 建立为模板完成条件" in foundation

    assert "临时工件只按 06 §8.7 的最小共同边界处置和交还" in template
    assert "payload、一次性脚本、scratch" not in template
