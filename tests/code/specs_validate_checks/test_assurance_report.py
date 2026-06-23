import json
import subprocess
import sys
from pathlib import Path

from .common import checker, write_md

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# ══════════════════════════════════════════════════════════════════════
# assurance-report — 规范保障要求聚合报告
# ══════════════════════════════════════════════════════════════════════

def build_assurance_report_fixture(tmp_path, monkeypatch):
    docs_specs = tmp_path / "specs"
    (tmp_path / "rules").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(checker, "FORMAL_SPECS_DIR", docs_specs)
    monkeypatch.setattr(checker, "RUNTIME_PROJECTION_DEFAULT_PATHS", ["rules/LDVH-WORKSPACE-ENTRY.md"])

    write_md(
        tmp_path / "rules" / "LDVH-WORKSPACE-ENTRY.md",
        """
# Runtime Projection

规范来源：`specs/00-Test.md`
""",
    )
    write_md(
        docs_specs / "00-Test.md",
        """
# Assurance Report Test

## 章节索引

| 章节 | 主题 |
|---|---|
| 1 | 规范保障要求 |

## 1. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 后续正式规范不得违背本文的价值实现标准 | 规范检查 | 文档治理 | 审计时 |
| 确定性执行要求 | 后续 Code 应能生成 assurance report | `code/specs_validate.py` 扩展、正反样例 | 校验实现 | 规范保障要求变化时 |
| Human 交互要求 | 高影响变更应触发 Human Gate | Human Gate、确认记录 | 工作流程治理 | 变更前 |
| Human 交互要求 | 新增管辖项目条目时，应评估 Human Gate | Human Gate、影响范围说明 | 工作流程治理 | 管辖项目清单变化时 |
| Human 交互要求 | candidate 流程正式创建前，应先讨论是否独立成流程 | Human Gate、流程讨论 | 工作流程治理 | 从候选项创建流程前 |
| Human 交互要求 | Human Gate UI 应清楚展示确认对象和影响范围 | Human Gate UI、承接 06 §6.3.1 | 工作流程治理 | Human Gate UI 变化时 |
| 工作流程接管要求 | 接管后的执行和验证由 active 工作流程承担 | active 工作流程、Code 派生集合索引 | 工作流程治理 | 接管范围变化时 |
| 生命周期触发要求 | 运行投影不可用时应记录降级说明 | 人工降级检查 | 触发保障 | 工具不可用时 |
| 生命周期触发要求 | 平台能力变化后应检查平台清单是否同步 | 平台清单、人工降级检查 | 触发保障 | 平台能力变化时 |
| 生命周期触发要求 | 第三方 Skill 入口变化后应检查包装 Skill 和运行投影是否同步 | 包装 Skill、运行投影漂移检查、降级方式 | 触发保障 | 第三方 Skill 使用入口变化时 |
| 生命周期触发要求 | 41 触发保障应被 42 消费，并覆盖运行投影漂移检查和 Human Gate 证据消费 | 41 分层触发保障、42 消费检查、运行投影漂移检查、Human Gate 证据消费 | 触发保障 | 正式规范、运行投影或 Human Gate 证据变化时 |
""",
    )
    write_md(
        tmp_path / "docs" / "studies" / "18-评估.md",
        """
# 评估

## 1. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 确定性执行要求 | 不应进入正式报告 | Code | 校验实现 | 任意 |
""",
    )
    return docs_specs


def test_assurance_report_builds_statuses_and_summary(tmp_path, monkeypatch):
    docs_specs = build_assurance_report_fixture(tmp_path, monkeypatch)

    report = checker.assurance_report_build([str(docs_specs)])

    assert report["metadata"]["source_of_truth"] is False
    assert report["metadata"]["checked_file_count"] == 1
    assert report["metadata"]["source_count"] == 1
    assert report["metadata"]["requirement_count"] == 11
    assert report["metadata"]["runtime_projection_checked_file_count"] == 1
    assert report["metadata"]["runtime_projection_issue_count"] == 0
    assert report["metadata"]["human_gate_checked_file_count"] >= 2
    assert report["metadata"]["human_gate_record_count"] == 0
    assert report["metadata"]["human_gate_issue_count"] == 0
    assert report["summary"]["runtime_projection_status"] == "closed"
    assert report["summary"]["human_gate_status"] == "degraded"
    assert report["summary"]["by_status"] == {
        "closed": 3,
        "degraded": 3,
        "needs_human_gate": 4,
        "open": 1,
    }
    assert report["summary"]["by_capability_status"] == {
        "degraded": 3,
        "open": 1,
    }
    assert report["summary"]["gap_total"] == sum(
        category["total"] for category in report["gap_categories"].values()
    )
    assert report["summary"]["gap_by_owner_area"] == {
        area: category["total"] for area, category in report["gap_categories"].items()
    }
    assert report["gap_categories"]
    assert all("examples" in category for category in report["gap_categories"].values())
    assert report["gap_categories"]["human_gate"]["subcategories"]
    assert report["gap_categories"]["human_gate"]["subcategories"]["decision_record_required"]["decision_flows"]
    assert report["runtime_projection"]["summary"]["status"] == report["summary"]["runtime_projection_status"]
    assert report["summary"]["by_owner_area"]["code"] == 1
    assert report["summary"]["by_owner_area"]["workflow"] == 1
    assert [item["id"] for item in report["capability_gaps"]] == [
        "41_trigger_safeguard",
        "42_consumes_41",
        "runtime_projection_drift_check",
        "human_gate_evidence_consumption",
    ]
    assert report["capability_gaps"][0]["status"] == "open"

    statuses = {item["content"]: item["status"] for item in report["requirements"]}
    assert statuses["后续正式规范不得违背本文的价值实现标准"] == "closed"
    assert statuses["后续 Code 应能生成 assurance report"] == "closed"
    assert statuses["高影响变更应触发 Human Gate"] == "needs_human_gate"
    assert statuses["运行投影不可用时应记录降级说明"] == "degraded"
    assert statuses["41 触发保障应被 42 消费，并覆盖运行投影漂移检查和 Human Gate 证据消费"] == "needs_human_gate"
    assert next(item for item in report["requirements"] if item["owner_area"] == "code")["suggested_writeback"] == "code_request_or_test"


def test_assurance_report_cli_outputs_json(tmp_path, monkeypatch, capsys):
    docs_specs = build_assurance_report_fixture(tmp_path, monkeypatch)

    exit_code = checker.main(["assurance-report", str(docs_specs), "--format", "json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["metadata"]["report"] == "assurance-report"
    assert payload["metadata"]["runtime_projection_checked_file_count"] == 1
    assert payload["metadata"]["human_gate_record_count"] == 0
    assert payload["summary"]["human_gate_status"] == "degraded"
    assert payload["summary"]["by_status"]["open"] == 1
    assert payload["summary"]["by_status"]["needs_human_gate"] == 4
    assert payload["summary"]["gap_total"] == 12
    assert payload["summary"]["gap_by_owner_area"]["human_gate"] == 5
    assert payload["gap_categories"]["code"]["requirement_count"] == 0
    assert payload["gap_categories"]["code"]["capability_gap_count"] == 1
    assert payload["gap_categories"]["runtime_projection"]["capability_gap_count"] == 1
    assert payload["gap_categories"]["runtime_projection"]["subcategories"]["lifecycle_trigger_sync"]["total"] == 2
    assert payload["gap_categories"]["runtime_projection"]["subcategories"]["platform_capability_sync"]["total"] == 1
    assert payload["gap_categories"]["runtime_projection"]["subcategories"]["third_party_skill_projection"]["total"] == 1
    assert payload["gap_categories"]["runtime_projection"]["subcategories"]["projection_coverage_diagnostic"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["decision_record_required"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["diagnostic_coverage"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["decision_record_required"]["decision_flows"]["future_trigger_record"]["total"] == 1
    assert "current_record_required" not in payload["gap_categories"]["human_gate"]["subcategories"]["decision_record_required"]["decision_flows"]
    assert payload["gap_categories"]["human_gate"]["subcategories"]["policy_clarification"]["total"] == 2
    assert payload["gap_categories"]["human_gate"]["subcategories"]["policy_clarification"]["policy_flows"]["future_evaluation"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["policy_clarification"]["policy_flows"]["workflow_design_discussion"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["implementation_support"]["support_flows"]["web_human_facing_support"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["diagnostic_coverage"]["diagnostic_flows"]["coverage_degraded"]["total"] == 1
    assert payload["requirements"][0]["source"] == "specs/00-Test.md"
    assert payload["capability_gaps"][0]["capability"] == "41 触发保障"


def test_assurance_report_cli_outputs_text(tmp_path, monkeypatch, capsys):
    docs_specs = build_assurance_report_fixture(tmp_path, monkeypatch)

    exit_code = checker.main(["assurance-report", str(docs_specs)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "规范保障要求聚合报告" in output
    assert "需关注项:" in output
    assert "能力缺口:" in output
    assert "缺口分类:" in output
    assert "Code / Test (code):" in output
    assert "运行投影 (runtime_projection):" in output
    assert "生命周期触发同步 (lifecycle_trigger_sync):" in output
    assert "平台能力承接同步 (platform_capability_sync):" in output
    assert "第三方 Skill 投影 (third_party_skill_projection):" in output
    assert "投影覆盖诊断降级 (projection_coverage_diagnostic):" in output
    assert "Human Gate (human_gate):" in output
    assert "必须人类决策记录 (decision_record_required):" in output
    assert "未来触发时记录 (future_trigger_record):" in output
    assert "规范口径说明 (policy_clarification):" in output
    assert "未来触发时评估 (future_evaluation):" in output
    assert "流程创建前讨论 (workflow_design_discussion):" in output
    assert "承接实现支持 (implementation_support):" in output
    assert "Web / Human-facing 承接 (web_human_facing_support):" in output
    assert "Code 降级提示/覆盖 (diagnostic_coverage):" in output
    assert "覆盖范围降级 (coverage_degraded):" in output
    assert "后续 Code 应能生成 assurance report" not in output
    assert "运行投影检查文件数: 1" in output
    assert "Human Gate 记录数: 0" in output
    assert "Human Gate 问题状态" in output
    assert "运行投影漂移检查" in output
    assert "runtime-projection checked 1 project-local files" in output
    assert "human-gate checked" in output
    assert "suggested_writeback: code_request_or_test" in output


def test_assurance_report_reports_41_member_status(tmp_path, monkeypatch):
    docs_specs = build_assurance_report_fixture(tmp_path, monkeypatch)
    write_md(
        docs_specs / "40-Workflow.md",
        """
# Workflow

```yaml
ldvh_member:
  spec_id: 40
  kind: work_process
  name_en: action-orchestration-design-audit
  name_zh: 工作流程设计审核
  collection_status: active
  canonical_path: specs/40-Workflow.md
```
""",
    )
    write_md(
        docs_specs / "41-Workflow.md",
        """
# Work Model Audit

```yaml
ldvh_member:
  spec_id: 41
  kind: work_process
  name_en: fact-model-audit
  name_zh: 工作模型审核
  collection_status: candidate
  canonical_path: specs/41-Workflow.md
```
""",
    )

    report = checker.assurance_report_build([str(docs_specs)])

    gap = next(item for item in report["capability_gaps"] if item["id"] == "41_trigger_safeguard")
    assert gap["status"] == "degraded"
    assert gap["evidence"] == "workflow 40 status=active; workflow 41 status=candidate"
    assert "collection_status=candidate" in gap["status_reason"]


def test_assurance_plan_build(tmp_path, monkeypatch):
    docs_specs = build_assurance_report_fixture(tmp_path, monkeypatch)
    plan = checker.assurance_plan_build(str(tmp_path))
    assert plan["metadata"]["report"] == "assurance-plan"
    assert plan["metadata"]["read_only"] is True
    assert plan["scope"]["assurance_report_requirements"] >= 1
    assert plan["requirements"]["gap_total"] >= 1
    assert "gaps" in plan
    assert "proposed_actions" in plan
    assert "writes_required" in plan
    assert "human_gate" in plan
    assert "validation_plan" in plan
    assert "writeback_targets" in plan
    assert "capabilities" in plan
    assert len(plan["capabilities"]) >= 1


def test_assurance_plan_text_output(tmp_path, monkeypatch):
    docs_specs = build_assurance_report_fixture(tmp_path, monkeypatch)
    plan = checker.assurance_plan_build(str(tmp_path))
    text = checker.assurance_plan_format_text(plan)
    assert "Assurance Plan (只读)" in text
    assert "能力状态" in text
    assert "建议行动" in text
    assert "写入需求" in text
    assert "Human Gate" in text
    assert "验证计划" in text
    assert "回写目标" in text


def test_runtime_projection_remediation_classification(tmp_path, monkeypatch):
    docs_specs = build_assurance_report_fixture(tmp_path, monkeypatch)
    plan = checker.assurance_plan_build(str(tmp_path))
    rp_action = None
    for action in plan["proposed_actions"]:
        if action["owner_area"] == "runtime_projection":
            rp_action = action
            break
    assert rp_action is not None
    assert "remediation" in rp_action
    remediation = rp_action["remediation"]
    assert "doc_crossref_check" in remediation
    assert remediation["doc_crossref_check"]["total"] >= 1
    assert remediation["doc_crossref_check"]["label"] == "文档交叉引用检查"
    total_remediation = sum(r["total"] for r in remediation.values())
    assert total_remediation == rp_action["gap_count"]


def test_classify_runtime_projection_remediation():
    assert checker._classify_runtime_projection_remediation(
        {"content": "正式规范变化后应检查本文是否需要同步", "title": "", "id": ""}
    ) == "doc_crossref_check"
    assert checker._classify_runtime_projection_remediation(
        {"content": "入口变化后应检查配置同步", "title": "", "id": ""}
    ) == "entry_sync_check"
    assert checker._classify_runtime_projection_remediation(
        {"content": "", "title": "", "id": "runtime_projection_drift_check"}
    ) == "drift_diagnostic"
    assert checker._classify_runtime_projection_remediation(
        {"content": "平台适配清单变化后应检查", "title": "", "id": ""}
    ) == "platform_mapping_check"
    assert checker._classify_runtime_projection_remediation(
        {"content": "第三方 Skill 接管后应检查同步", "title": "", "id": ""}
    ) == "skill_projection_check"


def test_assurance_report_script_fast_path_outputs_json():
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "specs_validate.py"),
            "assurance-report",
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["metadata"]["report"] == "assurance-report"


def test_assurance_plan_script_fast_path_outputs_text():
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "specs_validate.py"),
            "assurance-plan",
            "--workspace-root",
            str(PROJECT_ROOT.parent),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode in (0, 1)
    assert "# Assurance Plan (只读)" in result.stdout
