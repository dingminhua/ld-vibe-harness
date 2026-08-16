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
        "### 5.1 前置精确读取与执行期能力预检",
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
    assert "普通 `in_progress` 检查点" in source
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


def test_controlled_write_failure_must_be_repaired_not_silently_skipped() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "受控写入调用的失败处置" in source
    assert (
        "任一 21 专属 Helper 写入操作返回 `invalid_request`、`rejected`、`unavailable` 或其它非成功外层结果时"
        in source
    )
    assert "Controller 必须当场读取该响应的 `gaps` 与 `diagnostics`" in source
    assert "修正请求形状、指纹或内容后重试" in source
    assert "停在最后合法状态，按 §5.4 只经真实 blocked 或读取缺口交还" in source
    assert "不得静默跳过失败的写入并继续后续控制步骤、形成成功声明或任何 phase/status 宣称" in source
    assert "修复与重试受 Gate1 冻结的 `allowed_adjustments` 约束，不构成扩权" in source


def test_gate1_post_approval_pre_yield_invariant_covers_the_full_controller_chain() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "Gate 1 后统一 pre-yield 控制点" in source
    assert "完整 after、CAS、精确回读与独立事实完整性审计" in source
    assert "`source_content_fingerprint` 与刚回读 `content_fingerprint` 相同" in source
    assert "fresh projection" in source
    assert "Controller-owned 结构步骤" in source

    expected_steps = {
        "plan_revising": "form_current_plan",
        "executing": "advance_current_work_item",
        "controller_checking": "form_complete_result_projection",
        "independent_reviewing": "complete_independent_result_review",
        "closure_preparing": "form_closure_proposal",
    }
    for phase, next_step in expected_steps.items():
        assert f"`{phase}`" in source
        projection = derive_workcase_presentation("open", phase, FINGERPRINT)
        assert projection["resolution"] == "resolved"
        assert projection["blocking_overlay"] is False
        assert projection["source_content_fingerprint"] == FINGERPRINT
        assert projection["handoff_narrative_key"] != "gate2_waiting"
        assert projection["next_required_control_step"] == next_step


def test_intermediate_milestones_cannot_be_used_as_pre_gate2_handoffs() -> None:
    source = _source(EXECUTION_TEMPLATE)

    for milestone in (
        "current plan 或 fresh creation review",
        "单项进入 `completed` / `cancelled` 或全部 item terminal",
        "完整 canonical result projection",
        "Reviewer 返回或 feedback 已处置",
        "进入 `closure_preparing` 或形成完整 closure proposal",
    ):
        assert milestone in source
    assert "每个里程碑写回后仍须按 fresh fingerprint-matched projection 继续" in source


def test_only_gate2_blocked_unresolved_closed_are_legal_post_gate1_exits() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "`phase=human_closure_confirming`" in source
    assert "`handoff_narrative_key=gate2_waiting`" in source
    assert "`next_required_control_step=human_gate_2`" in source
    assert "Gate 1 后其它 phase 不构成 Human 交还点" in source
    assert "真实外部/能力阻塞与恢复条件" in source
    assert "连续精确读取后投影仍 unresolved" in source

    for phase in PHASE_PRESENTATION:
        blocked = derive_workcase_presentation("blocked", phase, FINGERPRINT)
        assert blocked["resolution"] == "resolved"
        assert blocked["blocking_overlay"] is True
        assert blocked["handoff_narrative_key"] != "gate2_waiting"
        assert blocked["handoff_allowed"] is True
        assert blocked["handoff_reason"] != "controller_owned"

    gate2 = derive_workcase_presentation("open", "human_closure_confirming", FINGERPRINT)
    assert gate2["resolution"] == "resolved"
    assert gate2["blocking_overlay"] is False
    assert gate2["handoff_narrative_key"] == "gate2_waiting"
    assert gate2["next_required_control_step"] == "human_gate_2"
    assert gate2["handoff_allowed"] is True
    assert gate2["handoff_reason"] == "gate2_waiting"

    closed = derive_workcase_presentation("closed", None, FINGERPRINT)
    assert closed["resolution"] == "resolved"
    assert closed["handoff_narrative_key"] == "closed"
    assert closed["next_required_control_step"] == "none"
    assert closed["handoff_allowed"] is True
    assert closed["handoff_reason"] == "closed"


def test_template_legal_exits_equal_the_derived_handoff_allowed_set() -> None:
    source = _source(EXECUTION_TEMPLATE)
    workcase_spec = _source(Path(__file__).resolve().parents[3] / "specs/21-WorkCase-工作项.md")

    assert "handoff_allowed" in source
    assert "controller_owned" in source
    assert "§9.3.1 的派生 `handoff_allowed=true`" in source
    assert "这四类合法退出" in source

    allowed_exits = {
        ("closed", None),
        *((status, phase) for status in ("open", "blocked") for phase in PHASE_PRESENTATION),
    }
    resolved_allowed = {
        (status, phase)
        for status, phase in allowed_exits
        if derive_workcase_presentation(status, phase, FINGERPRINT)["handoff_allowed"] is True
    }
    # 安全出口：closed、真实 blocked 全部、gate1_waiting、gate2_waiting。
    assert {
        ("closed", None),
        ("open", "human_plan_confirming"),
        ("open", "human_closure_confirming"),
    } <= resolved_allowed
    for status in ("open", "blocked"):
        for phase in PHASE_PRESENTATION:
            if status == "blocked":
                assert (status, phase) in resolved_allowed
            elif phase not in {"human_plan_confirming", "human_closure_confirming"}:
                assert (status, phase) not in resolved_allowed

    assert "handoff_allowed" in workcase_spec
    assert "controller_owned" in workcase_spec
    assert "不新增 `controller_checking → Gate2` 捷径" in workcase_spec


def test_new_human_decision_need_converges_without_a_third_human_wait() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "新的 Human 决策需求，不构成 blocked 或 unresolved" in source
    assert "不得新增 Human Gate、写入 Human waiting 或请求第三次确认" in source
    assert "受影响 item 及无法继续的依赖 item 据实记为 `cancelled`" in source
    assert "全部 item terminal 后继续结果链" in source
    assert "若在 items 已 terminal 后才发现，不重开或新增 item" in source
    assert "结果、验证以及 closure proposal 的 residual decision" in source
    assert "`cancelled` 不得写成 `completed`" in source
    assert "不自动决定 closure outcome" in source
    assert "Controller 不得代替 Human 作出该 residual decision" in source


def test_gate1_post_approval_criterion_self_reference_converges_without_recursive_review() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "Gate1 后才发现 success criterion" in source
    assert "冻结验收基线不得改写" in source
    assert "不重开或新增 item、增加递归复核或建立第三次 Human Gate" in source
    assert "将该 criterion 据实写为 `not_verified`" in source
    assert "validation 与 closure proposal 的 residual decision" in source
    assert "继续既有结果链至 Gate2" in source


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
        "contract_identity": "workcase-current-snapshot-presentation/2",
        "resolution": "unresolved",
        "source_content_fingerprint": None,
        "unresolved_reason": "missing_source_content_fingerprint",
        "handoff_allowed": True,
        "handoff_reason": "unresolved",
    }


def test_continuation_requires_proactive_stop_gate_binding() -> None:
    source = _source(EXECUTION_TEMPLATE)

    assert "续接绑定要求" in source
    assert "跨执行环境、新会话或上下文恢复后继续消费当前 WorkCase 时" in source
    assert (
        "按 09 §5.8 绑定形状为当前会话主动建立 Stop gate 精确绑定"
        "（`LDVH_WORKCASE_STOP_BINDING` 或 `.ldvh-stop-bindings/<session_id>.json`）" in source
    )
    assert "绑定不可建立、形状不满足或宿主不支持时如实记录该缺口" in source
    assert "不伪造绑定、不按候选特征猜测，也不为此新增 Human 确认" in source
    assert "本要求不改变 09 §5.8 的 fail-open 与禁止猜测设计" in source


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
