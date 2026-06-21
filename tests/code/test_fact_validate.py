import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "code" / "fact_validate.py"


def run_checker(*paths, extra_args=None):
    cmd = ["python3", str(SCRIPT_PATH), *[str(path) for path in paths]]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_yaml(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def write_valid_spark(tmp_path: Path, *, status: str = "pending", resolved_to: str = "", resolved_at: str = "") -> Path:
    return write_yaml(
        tmp_path / "ldvh-base" / "sparks" / "spark-0001-study-boundary.yaml",
        f"""
id: spark-0001
type: spark
title: Study boundary
status: {status}
created: "2026-06-20T09:00:00"
updated: "2026-06-20T09:00:00"
description: |
  Discuss whether a Study can close a Spark.
evolution: []
source: conversation
source_detail: test
priority: P2
resolved_to: {resolved_to}
resolved_at: {resolved_at}
discard_reason: ""
related_workcases: []
related_adrs: []
related_studies:
  - study-0001
related_docs: []
""",
    )


def write_valid_workcase_tree(tmp_path: Path, *, status: str = "active") -> tuple[Path, Path]:
    root = tmp_path / "project"
    (root / "tests" / "code").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "code" / "test_fact_validate.py").write_text("# evidence fixture\n", encoding="utf-8")
    workcase = write_yaml(
        root / "ldvh-base" / "workcases" / "workcase-0001-core-plan.yaml",
        f"""
id: workcase-0001
type: workcase
title: Core Plan
goal: |
  Validate the core WorkCase fixture.
status: {status}
created: "2026-06-12T09:00:00"
updated: "2026-06-12T09:30:00"
priority: P2
description: Core plan
success_criteria: |
  - [ ] Plan can be validated
source: test
orchestration:
  mode: single
  execution_items:
    - id: item-1
      title: Validate
      role: code
      mode: single
      input_refs:
        - code/fact_validate.py
      expected_output: Current WorkCase validates.
      status: done
      result_summary: Done.
      evidence_refs:
        - tests/code/test_fact_validate.py
      blocking_reason:
  review:
    controller_self_check: true
    specialist_review:
      required: false
      role:
      expected_output:
    human_closure_review: true
verification_evidence: |
  ## 验证计划

  检查当前 WorkCase 是否满足关闭审查前的验证条件。

  ## 验证命令

  ```bash
  python3 code/fact_validate.py ldvh-base/workcases
  ```

  ## 验证结果

  当前 WorkCase 校验通过。

  ## 结论

  验证证据满足关闭审查要求。
closure_evidence: |
  ## 验证计划

  检查是否具备进入关闭审查的最小证据。

  ## 验证命令

  人工检查 WorkCase 成功标准、执行项和验证证据。

  ## 验证结果

  成功标准、执行项和验证证据均已整理。

  ## 结论

  可进入关闭审查。
review_requested_at: "2026-06-12T00:00:00"
closed_at: {"'2026-06-12T01:00:00'" if status == "closed" else "''"}
related_docs: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_workcases: []
""",
    )
    return root, workcase


def add_current_review_contract(workcase: Path, *, closure_outcome: str = "completed") -> None:
    content = workcase.read_text(encoding="utf-8")
    content = content.replace(
        """  review:
    controller_self_check: true
    specialist_review:
      required: false
      role:
      expected_output:
    human_closure_review: true
""",
        """  plan_review:
    orchestration_owner: main_controller
    workflow_ref:
    review_policy:
      selection_reason: Current contract fixture.
      required_perspectives: []
      optional_perspectives: []
      tool_method_requirements: []
      aggregation_rule: All blocking findings must be resolved before execution.
    review_items: []
    controller_resolution:
      resolved_at: "2026-06-12T00:10:00"
      resolver: test-controller
      source_review_item_ids: []
      accepted_findings: []
      rejected_findings: []
      required_changes_applied: []
      unresolved_items: []
      changed_fields: []
      revision_history_refs: []
      summary: Plan review resolved.
    human_confirmation:
      decision: execute
      scope: Test fixture scope.
      constraints: []
      confirmed_at: "2026-06-12T00:20:00"
      summary: Human confirmed execution.
  result_review:
    controller_self_check:
      controller: test-controller
      checked_at: "2026-06-12T00:40:00"
      prompt_context:
        objective: Check fixture closure.
        input_refs:
          - tests/code/test_fact_validate.py
      result:
        status: pass
        summary: Fixture can close.
        key_findings:
          - 未发现范围内问题。
        required_changes: []
        evidence_refs:
          - tests/code/test_fact_validate.py
      attested_at: "2026-06-12T00:45:00"
      attestation:
        signer: test-controller
        statement: Checked fixture evidence.
    orchestration_owner: main_controller
    workflow_ref:
    review_policy:
      selection_reason: Current contract fixture.
      required_perspectives: []
      optional_perspectives: []
      tool_method_requirements: []
      aggregation_rule: All blocking findings must be resolved before closure.
    review_items: []
    controller_resolution:
      resolved_at: "2026-06-12T00:50:00"
      resolver: test-controller
      source_review_item_ids: []
      accepted_findings: []
      rejected_findings: []
      required_changes_applied: []
      unresolved_items: []
      changed_fields: []
      revision_history_refs: []
      summary: Result review resolved.
    human_closure_confirmation:
      decision: close
      scope: Test fixture closure.
      constraints: []
      confirmed_at: "2026-06-12T01:00:00"
      summary: Human confirmed closure.
""",
    )
    content = content.replace(
        'review_requested_at: "2026-06-12T00:00:00"\n',
        'review_requested_at: "2026-06-12T00:00:00"\nplan_confirmed_at: "2026-06-12T00:20:00"\nclosure_requested_at: "2026-06-12T00:55:00"\n',
    )
    content = content.replace(
        "closed_at: '2026-06-12T01:00:00'\n",
        f"closed_at: '2026-06-12T01:00:00'\nclosure_outcome: {closure_outcome}\n",
    )
    workcase.write_text(content, encoding="utf-8")


def write_valid_adr(tmp_path: Path, *, status: str = "active", extra: str = "") -> Path:
    return write_yaml(
        tmp_path / "project" / "ldvh-base" / "adrs" / "adr-0001-current-decision.yaml",
        f"""
id: adr-0001
type: adr
title: Current Decision Patch
status: {status}
created: "2026-06-19T09:00:00"
updated: "2026-06-19T09:30:00"
date: "2026-06-19"
context: |
  Current context.
decision: |
  Current decision.
consequences: |
  ## 正向价值

  Current value.

  ## 逆向价值

  当前决策无逆向价值

  ## 实施成本

  Current cost.

  ## 风险评估

  Current risk.

  ## 注意事项

  Current notes.
related_workcases: []
related_adrs: []
related_sparks: []
related_rules: []
archive_reason:
deprecated_reason:
{extra}
""",
    )


def write_valid_pitfall(tmp_path: Path, *, extra: str = "") -> Path:
    return write_yaml(
        tmp_path / "project" / "ldvh-base" / "pitfalls" / "pitfall-0001-current-pitfall.yaml",
        f"""
id: pitfall-0001
type: pitfall
title: Current Pitfall
status: active
created: "2026-06-19T09:00:00"
updated: "2026-06-19T09:30:00"
symptoms: |
  Current symptoms.
trigger_conditions: |
  Current trigger conditions.
root_cause: |
  Current root cause.
resolution: |
  Current resolution.
verification: |
  ## 验证计划

  Validate the pitfall fixture.

  ## 验证命令

  ```bash
  python3 code/fact_validate.py ldvh-base/pitfalls
  ```

  ## 验证结果

  Fixture can be checked.

  ## 结论

  Fixture is valid.
avoidance: |
  Current avoidance.
applicability: |
  Current applicability.
source_objects: []
related_objects: []
related_rules: []
tags: []
source_sparks: []
related_adrs: []
related_docs: []
archive_reason:
{extra}
""",
    )


def test_valid_workcase_tree(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"
    assert result.stderr == ""


def test_related_changes_is_rejected_for_all_current_work_objects(tmp_path):
    root, workcase = write_valid_workcase_tree(tmp_path / "workcase")
    workcase.write_text(
        workcase.read_text(encoding="utf-8") + "related_changes:\n  - abc1234\n",
        encoding="utf-8",
    )
    adr = write_valid_adr(tmp_path / "adr", extra="related_changes:\n  - abc1234\n")
    pitfall = write_valid_pitfall(tmp_path / "pitfall", extra="related_changes:\n  - abc1234\n")

    workcase_result = run_checker(workcase)
    adr_result = run_checker(adr)
    pitfall_result = run_checker(pitfall)

    assert workcase_result.returncode == 1
    assert "REMOVED_OBJECT_FIELD" in workcase_result.stdout
    assert "related_changes" in workcase_result.stdout
    assert adr_result.returncode == 1
    assert "REMOVED_OBJECT_FIELD" in adr_result.stdout
    assert "related_changes" in adr_result.stdout
    assert pitfall_result.returncode == 1
    assert "REMOVED_OBJECT_FIELD" in pitfall_result.stdout
    assert "related_changes" in pitfall_result.stdout


def test_removed_area_relation_field_is_rejected(tmp_path):
    old_field = "related_" + "work" + "areas"
    old_ref = "work" + "area-0001"
    _, workcase = write_valid_workcase_tree(tmp_path)
    workcase.write_text(
        workcase.read_text(encoding="utf-8") + f"{old_field}:\n  - {old_ref}\n",
        encoding="utf-8",
    )

    result = run_checker(workcase)

    assert result.returncode == 1
    assert "REMOVED_OBJECT_FIELD" in result.stdout
    assert "旧范围对象关联字段已移除" in result.stdout


def test_removed_area_object_type_is_unknown(tmp_path):
    old_type = "work" + "area"
    legacy = write_yaml(
        tmp_path / "ldvh-base" / "old-area" / "old-area-0001-core.yaml",
        f"""
id: {old_type}-0001
type: {old_type}
title: Old area
status: active
created: "2026-06-12T09:00:00"
updated: "2026-06-12T09:30:00"
description: Old area fixture
""",
    )

    result = run_checker(legacy)

    assert result.returncode == 2
    assert "UNKNOWN_OBJECT_TYPE" in result.stdout


def test_legacy_taskplan_file_is_unknown_object_type(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    legacy = write_yaml(
        root / "ldvh-base" / "taskplans" / "taskplan-0001-old.yaml",
        """
id: taskplan-0001
type: taskplan
title: Old
status: active
""",
    )

    result = run_checker(legacy)

    assert result.returncode == 2
    assert "UNKNOWN_OBJECT_TYPE" in result.stdout


def test_datetime_fields_reject_date_only_values(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path)
    workcase.write_text(
        workcase.read_text(encoding="utf-8")
        .replace('created: "2026-06-12T09:00:00"', 'created: "2026-06-12"')
        .replace('updated: "2026-06-12T09:30:00"', 'updated: "2026-06-12"'),
        encoding="utf-8",
    )

    result = run_checker(workcase)

    assert result.returncode == 1
    assert "INVALID_DATETIME_FIELD" in result.stdout
    assert "created" in result.stdout
    assert "updated" in result.stdout


def test_spark_related_study_does_not_resolve_spark(tmp_path):
    spark = write_valid_spark(tmp_path)

    result = run_checker(spark)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"


def test_spark_rejects_study_as_resolved_target(tmp_path):
    spark = write_valid_spark(
        tmp_path,
        status="resolved",
        resolved_to="{type: study, ref: study-0001}",
        resolved_at="2026-06-20",
    )

    result = run_checker(spark)

    assert result.returncode == 1
    assert "INVALID_SPARK_RESOLVED_TO_TYPE" in result.stdout
    assert "Study 只能通过 related_studies 关联" in result.stdout


def test_adr_uses_current_three_state_contract(tmp_path):
    adr = write_valid_adr(tmp_path)

    result = run_checker(adr)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"


def test_adr_rejects_old_status_and_removed_fields(tmp_path):
    adr = write_valid_adr(
        tmp_path,
        status="accepted",
        extra="""
superseded_by: adr-0002
related_objects:
  - spark-0001
alternatives: |
  Old option.
affects:
  - code
""",
    )

    result = run_checker(adr)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout
    assert "REMOVED_OBJECT_FIELD" in result.stdout
    assert "superseded_by" in result.stdout
    assert "related_objects" in result.stdout
    assert "alternatives" in result.stdout
    assert "affects" in result.stdout


def test_active_adr_requires_consequences_impact_loop(tmp_path):
    adr = write_valid_adr(
        tmp_path,
        extra="""
consequences: |
  积极后果：
  - Missing required four-part impact loop.
""",
    )

    result = run_checker(adr)

    assert result.returncode == 1
    assert "INVALID_ADR_CONSEQUENCES_STRUCTURE" in result.stdout
    assert "正向价值" in result.stdout
    assert "逆向价值" in result.stdout
    assert "实施成本" in result.stdout
    assert "风险评估" in result.stdout
    assert "注意事项" in result.stdout


def test_active_adr_requires_reverse_value_section(tmp_path):
    adr = write_valid_adr(
        tmp_path,
        extra="""
consequences: |
  ## 正向价值

  Current value.

  ## 实施成本

  Current cost.

  ## 风险评估

  Current risk.

  ## 注意事项

  Current notes.
""",
    )

    result = run_checker(adr)

    assert result.returncode == 1
    assert "INVALID_ADR_CONSEQUENCES_STRUCTURE" in result.stdout
    assert "逆向价值" in result.stdout


def test_active_adr_accepts_explicit_reverse_value_statement(tmp_path):
    adr = write_valid_adr(
        tmp_path,
        extra="""
consequences: |
  ## 正向价值

  Current value.

  ## 逆向价值

  This decision weakens V2 by reducing direct readability.

  ## 实施成本

  Current cost.

  ## 风险评估

  Current risk.

  ## 注意事项

  Current notes.
""",
    )

    result = run_checker(adr)

    assert result.returncode == 0


def test_active_adr_reverse_value_requires_00_value_reference(tmp_path):
    adr = write_valid_adr(
        tmp_path,
        extra="""
consequences: |
  ## 正向价值

  Current value.

  ## 逆向价值

  This decision has a tradeoff but does not cite the value standard.

  ## 实施成本

  Current cost.

  ## 风险评估

  Current risk.

  ## 注意事项

  Current notes.
""",
    )

    result = run_checker(adr)

    assert result.returncode == 1
    assert "INVALID_ADR_REVERSE_VALUE" in result.stdout
    assert "V1-V10" in result.stdout


def test_active_adr_accepts_compact_chinese_value_reference(tmp_path):
    adr = write_valid_adr(
        tmp_path,
        extra="""
consequences: |
  ## 正向价值

  Current value.

  ## 逆向价值

  削弱V10持续完善：需要额外维护判断说明。

  ## 实施成本

  Current cost.

  ## 风险评估

  Current risk.

  ## 注意事项

  Current notes.
""",
    )

    result = run_checker(adr)

    assert result.returncode == 0


def test_adr_terminal_statuses_require_reasons(tmp_path):
    archived = write_valid_adr(tmp_path / "archived", status="archived")
    deprecated = write_valid_adr(tmp_path / "deprecated", status="deprecated")

    archived_result = run_checker(archived)
    deprecated_result = run_checker(deprecated)

    assert archived_result.returncode == 1
    assert "MISSING_ARCHIVE_REASON" in archived_result.stdout
    assert deprecated_result.returncode == 1
    assert "MISSING_DEPRECATED_REASON" in deprecated_result.stdout


def test_study_draft_status_is_invalid(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    study = root / "ldvh-base" / "studies" / "study-0001-draft-report.md"
    study.parent.mkdir(parents=True, exist_ok=True)
    study.write_text(
        """---
id: study-0001
type: study
title: Draft Report
status: draft
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
summary: Draft report.
urls: []
related_workcases: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_docs: []
archive_reason:
---

# Draft Report

## 研究问题

This report should not validate because Study has no draft state.

## 输入与边界

Test fixture.

## 关键发现

Study has no draft state.

## 建议

Reject draft Study status.

## 后续分流

None.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout
    assert "draft" in result.stdout


def test_study_superseded_status_and_field_are_invalid(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    study = root / "ldvh-base" / "studies" / "study-0001-superseded-report.md"
    study.parent.mkdir(parents=True, exist_ok=True)
    study.write_text(
        """---
id: study-0001
type: study
title: Superseded Report
status: superseded
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
summary: Superseded report.
urls: []
related_workcases: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_docs: []
superseded_by: study-0002
archive_reason:
---

# Superseded Report

## 研究问题

This report should not validate because Study has no superseded state.

## 输入与边界

Test fixture.

## 关键发现

Study has no superseded state.

## 建议

Reject superseded Study status and superseded_by.

## 后续分流

None.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout
    assert "superseded" in result.stdout
    assert "REMOVED_OBJECT_FIELD" in result.stdout
    assert "superseded_by" in result.stdout


def test_study_source_field_is_no_longer_allowed(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    study = root / "ldvh-base" / "studies" / "study-0001-source-report.md"
    study.parent.mkdir(parents=True, exist_ok=True)
    study.write_text(
        """---
id: study-0001
type: study
title: Source Report
status: active
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
summary: Source report.
source: ai
user_intent: Trigger context remains here.
urls: []
related_workcases: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_docs: []
archive_reason:
---

# Source Report

## 研究问题

This report should not validate because Study no longer maintains source.

## 输入与边界

Test fixture.

## 关键发现

Study no longer maintains source.

## 建议

Reject source on Study.

## 后续分流

None.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 1
    assert "REMOVED_OBJECT_FIELD" in result.stdout
    assert "source" in result.stdout


def test_study_source_detail_field_is_no_longer_allowed(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    study = root / "ldvh-base" / "studies" / "study-0001-source-detail-report.md"
    study.parent.mkdir(parents=True, exist_ok=True)
    study.write_text(
        """---
id: study-0001
type: study
title: Source Detail Report
status: active
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
source_detail: Old source detail field.
summary: Source detail report.
urls: []
related_workcases: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_docs: []
archive_reason:
---

# Source Detail Report

## 研究问题

This report should not validate because Study renamed source_detail to user_intent.

## 输入与边界

Test fixture.

## 关键发现

Study renamed source_detail to user_intent.

## 建议

Reject source_detail on Study.

## 后续分流

None.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 1
    assert "REMOVED_OBJECT_FIELD" in result.stdout
    assert "source_detail" in result.stdout


def test_study_source_docs_field_is_no_longer_allowed(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    study = root / "ldvh-base" / "studies" / "study-0001-source-docs-report.md"
    study.parent.mkdir(parents=True, exist_ok=True)
    study.write_text(
        """---
id: study-0001
type: study
title: Source Docs Report
status: active
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
summary: Source docs report.
source_docs:
  - docs/studies/source.md
related_refs:
  - https://example.com/legacy
urls: []
related_workcases: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_docs: []
archive_reason:
---

# Source Docs Report

## 研究问题

This report should not validate because Study uses urls instead of legacy source/reference fields.

## 输入与边界

Test fixture.

## 关键发现

Study uses urls for external web sources.

## 建议

Reject source_docs on Study.

## 后续分流

None.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 1
    assert "REMOVED_OBJECT_FIELD" in result.stdout
    assert "source_docs" in result.stdout
    assert "related_refs" in result.stdout


def test_study_urls_accept_structured_items(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    study = root / "ldvh-base" / "studies" / "study-0001-structured-refs.md"
    study.parent.mkdir(parents=True, exist_ok=True)
    study.write_text(
        """---
id: study-0001
type: study
title: Structured Refs Report
status: active
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
summary: Structured refs report.
urls:
  - ref: https://example.com/reference
    title: Reference title
    summary: 用于说明这个网址支撑报告中的核心判断。
  - ref: https://example.com/second-reference
    summary: 用于补充第二个外部网址的中文用途说明。
related_workcases: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_docs: []
archive_reason:
---

# Structured Refs Report

## 研究问题

This report should validate with structured urls items.

## 输入与边界

Test fixture.

## 关键发现

Structured urls items are valid.

## 建议

Accept structured urls items.

## 后续分流

None.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 0
    assert "errors=0" in result.stdout


def test_study_urls_reject_invalid_structured_items(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    study = root / "ldvh-base" / "studies" / "study-0001-invalid-refs.md"
    study.parent.mkdir(parents=True, exist_ok=True)
    study.write_text(
        """---
id: study-0001
type: study
title: Invalid Refs Report
status: active
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
summary: Invalid refs report.
urls:
  - https://example.com/bare-url
  - title: Missing ref
    summary: This item has no ref.
  - ref: specs/24-Study-研究报告.md
    title: Local path is not a URL.
  - ref: https://example.com/reference
    note: Unexpected field.
  - ref: https://example.com/no-summary
    title: Missing summary
  - ref: https://example.com/english-summary
    summary: English-only summary is not enough.
related_workcases: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_docs: []
archive_reason:
---

# Invalid Refs Report

## 研究问题

This report should not validate because urls items are malformed.

## 输入与边界

Test fixture.

## 关键发现

Malformed urls items are invalid.

## 建议

Reject malformed urls items.

## 后续分流

None.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 1
    assert "INVALID_URL" in result.stdout
    assert "urls" in result.stdout


def test_study_report_body_requires_standard_headings(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    study = root / "ldvh-base" / "studies" / "study-0001-bad-body.md"
    study.parent.mkdir(parents=True, exist_ok=True)
    study.write_text(
        """---
id: study-0001
type: study
title: Bad Body Report
status: active
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
summary: Bad body report.
urls: []
related_workcases: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_docs: []
archive_reason:
---

# Bad Body Report

## 研究问题

Missing standard body sections.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 1
    assert "INVALID_STUDY_BODY_STRUCTURE" in result.stdout


def test_pitfall_repeatability_field_is_no_longer_allowed(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    pitfall = write_yaml(
        root / "ldvh-base" / "pitfalls" / "pitfall-0001-repeatability.yaml",
        """
id: pitfall-0001
type: pitfall
title: Repeatability Legacy Field
status: active
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
symptoms: |
  Legacy repeatability field should not validate.
trigger_conditions: |
  Any Pitfall file includes repeatability.
root_cause: |
  repeatability no longer carries useful distinction.
resolution: |
  Move recurrence context into trigger_conditions, applicability, and avoidance.
verification: |
  ## 验证计划

  确认 Validator 会拒绝旧字段 repeatability。

  ## 验证命令

  ```bash
  python3 code/fact_validate.py ldvh-base/pitfalls
  ```

  ## 验证结果

  Validator 报告 REMOVED_OBJECT_FIELD。

  ## 结论

  旧字段不再允许写入 Pitfall。
avoidance: |
  Do not write repeatability in Pitfall facts.
applicability: |
  Applies to Pitfall facts.
repeatability: recurring
tags: []
source_objects: []
source_sparks: []
related_workcases: []
related_adrs: []
related_docs: []
related_rules: []
archive_reason:
notes:
""",
    )

    result = run_checker(pitfall)

    assert result.returncode == 1
    assert "REMOVED_OBJECT_FIELD" in result.stdout
    assert "repeatability" in result.stdout


def test_pitfall_superseded_status_and_field_are_invalid(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    pitfall = write_yaml(
        root / "ldvh-base" / "pitfalls" / "pitfall-0001-superseded.yaml",
        """
id: pitfall-0001
type: pitfall
title: Superseded Pitfall
status: superseded
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
symptoms: |
  Superseded should no longer be a Pitfall status.
trigger_conditions: |
  A legacy fact uses superseded.
root_cause: |
  Pitfall lifecycle kept an old replacement state.
resolution: |
  Use archived with archive_reason and related references.
verification: |
  ## 验证计划

  Confirm validator rejects superseded Pitfall state.

  ## 验证命令

  python3 code/fact_validate.py ldvh-base/pitfalls

  ## 验证结果

  Validator rejects the legacy state and field.

  ## 结论

  Pitfall lifecycle is active/archived only.
avoidance: |
  Do not write superseded Pitfall facts.
applicability: |
  Applies to Pitfall facts.
tags: []
source_objects: []
source_sparks: []
related_adrs: []
related_docs: []
related_rules: []
superseded_by: specs/23-Pitfall-踩坑经验.md
archive_reason:
notes:
""",
    )

    result = run_checker(pitfall)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout
    assert "superseded" in result.stdout
    assert "superseded_by" in result.stdout


def test_pitfall_tags_must_be_english_slugs(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    pitfall = write_yaml(
        root / "ldvh-base" / "pitfalls" / "pitfall-0001-bad-tags.yaml",
        """
id: pitfall-0001
type: pitfall
title: Bad Tags
status: active
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
symptoms: |
  Invalid tag should not validate.
trigger_conditions: |
  Any tag includes spaces or non-English text.
root_cause: |
  Tag format is not constrained.
resolution: |
  Reject invalid tags.
verification: |
  ## 验证计划

  Check tag validation.

  ## 验证命令

  python3 code/fact_validate.py ldvh-base/pitfalls

  ## 验证结果

  Validator rejects invalid tags.

  ## 结论

  Tags are constrained.
avoidance: |
  Use English slugs.
applicability: |
  Applies to Pitfall facts.
tags:
  - bad tag
  - 中文
source_objects: []
source_sparks: []
related_adrs: []
related_docs: []
related_rules: []
archive_reason:
notes:
""",
    )

    result = run_checker(pitfall)

    assert result.returncode == 1
    assert "INVALID_PITFALL_TAG" in result.stdout


def test_pitfall_verification_headings_must_be_ordered(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)
    pitfall = write_yaml(
        root / "ldvh-base" / "pitfalls" / "pitfall-0001-bad-evidence-order.yaml",
        """
id: pitfall-0001
type: pitfall
title: Bad Evidence Order
status: active
created: "2026-06-18T09:00:00"
updated: "2026-06-18T09:30:00"
symptoms: |
  Evidence headings are present but not ordered.
trigger_conditions: |
  Any verification field is rewritten with wrong order.
root_cause: |
  Heading presence alone is not enough.
resolution: |
  Warn about wrong order.
verification: |
  ## 验证计划

  Check evidence order.

  ## 验证结果

  Result appears too early.

  ## 验证命令

  python3 code/fact_validate.py ldvh-base/pitfalls

  ## 结论

  Order should be reported.
avoidance: |
  Use 05.02 heading order.
applicability: |
  Applies to Pitfall facts.
tags:
  - evidence-order
source_objects: []
source_sparks: []
related_adrs: []
related_docs: []
related_rules: []
archive_reason:
notes:
""",
    )

    result = run_checker(pitfall)

    assert result.returncode == 0
    assert "EVIDENCE_FORMAT_ORDER" in result.stdout
    assert "warnings=1" in result.stdout


def test_workcase_legacy_fields_are_errors(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path)
    workcase.write_text(
        workcase.read_text(encoding="utf-8") + "tasks: []\ncompletion_evidence: done\n",
        encoding="utf-8",
    )

    result = run_checker(workcase)

    assert result.returncode == 1
    assert "LEGACY_WORKCASE_FIELD" in result.stdout
    assert "tasks" in result.stdout
    assert "completion_evidence" in result.stdout


def test_legacy_closed_workcase_does_not_require_current_review_contract(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path, status="closed")

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"


def test_current_closed_workcase_requires_closure_outcome(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path, status="closed")
    add_current_review_contract(workcase, closure_outcome="")

    result = run_checker(workcase)

    assert result.returncode == 1
    assert "MISSING_WORKCASE_CLOSURE_OUTCOME" in result.stdout


def test_current_closed_workcase_contract_validates(tmp_path):
    root, workcase = write_valid_workcase_tree(tmp_path, status="closed")
    add_current_review_contract(workcase)

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"


def test_workcase_review_item_warns_when_self_signed_by_controller(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path, status="human_plan_confirming")
    add_current_review_contract(workcase)
    workcase.write_text(
        workcase.read_text(encoding="utf-8").replace(
            "    review_items: []",
            """    review_items:
      - id: plan-review-1
        role: specs-reviewer
        agent_name: codex-main-controller
        requested_at: "2026-06-12T00:05:00"
        result:
          status: pass
""",
            1,
        ),
        encoding="utf-8",
    )

    result = run_checker(workcase)

    assert result.returncode == 0
    assert "WORKCASE_REVIEW_ITEM_SELF_SIGNED" in result.stdout
    assert "warnings=1" in result.stdout


def test_workcase_revision_history_requires_transition_fields(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path, status="human_closure_confirming")
    add_current_review_contract(workcase)
    workcase.write_text(
        workcase.read_text(encoding="utf-8")
        + """
revision_history:
  - revised_at: "2026-06-12T00:30:00"
    actor: test-controller
    reason: Test revision.
    changed_fields:
      - status
    summary: Missing transition fields.
""",
        encoding="utf-8",
    )

    result = run_checker(workcase)

    assert result.returncode == 1
    assert "LEGACY_WORKCASE_REVISION_TIME_FIELD" in result.stdout
    assert "MISSING_WORKCASE_REVISION_FIELD" in result.stdout
    assert "from_status" in result.stdout
    assert "to_status" in result.stdout


def test_executing_workcase_warns_when_all_execution_items_are_pending(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path, status="executing")
    add_current_review_contract(workcase)
    workcase.write_text(
        workcase.read_text(encoding="utf-8").replace("      status: done", "      status: pending"),
        encoding="utf-8",
    )

    result = run_checker(workcase)

    assert result.returncode == 0
    assert "WORKCASE_EXECUTION_PROGRESS_NOT_RECORDED" in result.stdout
    assert "warnings=1" in result.stdout


def test_executing_workcase_rejects_unresolved_plan_items(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path, status="executing")
    add_current_review_contract(workcase)
    workcase.write_text(
        workcase.read_text(encoding="utf-8").replace(
            "      unresolved_items: []",
            "      unresolved_items:\n        - Human still needs to confirm action wording.",
            1,
        ),
        encoding="utf-8",
    )

    result = run_checker(workcase)

    assert result.returncode == 1
    assert "UNRESOLVED_PLAN_ITEMS_AFTER_CONFIRMATION" in result.stdout


def test_result_reviewing_workcase_warns_when_review_items_empty(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path, status="subagents_result_reviewing")
    add_current_review_contract(workcase)

    result = run_checker(workcase)

    assert result.returncode == 0
    assert "RESULT_REVIEW_NOT_STARTED" in result.stdout
    assert "warnings=1" in result.stdout


def test_result_self_check_requires_key_findings(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path, status="subagents_result_reviewing")
    add_current_review_contract(workcase)
    workcase.write_text(
        workcase.read_text(encoding="utf-8").replace(
            "        key_findings:\n          - 未发现范围内问题。",
            "        key_findings: []",
        ),
        encoding="utf-8",
    )

    result = run_checker(workcase)

    assert result.returncode == 1
    assert "MISSING_RESULT_SELF_CHECK_FINDINGS" in result.stdout


def test_result_self_check_requires_required_changes_list(tmp_path):
    _, workcase = write_valid_workcase_tree(tmp_path, status="subagents_result_reviewing")
    add_current_review_contract(workcase)
    workcase.write_text(
        workcase.read_text(encoding="utf-8").replace(
            "        required_changes: []",
            "        required_changes:",
        ),
        encoding="utf-8",
    )

    result = run_checker(workcase)

    assert result.returncode == 1
    assert "MISSING_RESULT_SELF_CHECK_REQUIRED_CHANGES" in result.stdout


def test_result_self_check_required_changes_must_be_resolved_before_later_states(tmp_path):
    for status in ("subagents_result_reviewing", "human_closure_confirming", "closed"):
        _, workcase = write_valid_workcase_tree(tmp_path / status, status=status)
        add_current_review_contract(workcase)
        workcase.write_text(
            workcase.read_text(encoding="utf-8").replace(
                "        required_changes: []",
                "        required_changes:\n          - Fix a self-check finding before result review.",
            ),
            encoding="utf-8",
        )

        result = run_checker(workcase)

        assert result.returncode == 1
        assert "UNRESOLVED_RESULT_SELF_CHECK_REQUIRED_CHANGES" in result.stdout


def test_workcase_evidence_refs_missing_path_is_error(tmp_path):
    root, workcase = write_valid_workcase_tree(tmp_path)
    content = workcase.read_text(encoding="utf-8")
    workcase.write_text(
        content.replace(
            "        - tests/code/test_fact_validate.py",
            "        - ldvh-base/workcases/workcase-9999-missing.yaml",
        ),
        encoding="utf-8",
    )

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 1
    assert "EVIDENCE_REF_PATH_NOT_FOUND" in result.stdout
    assert "workcase-9999-missing.yaml" in result.stdout


def test_workcase_evidence_refs_non_paths_are_not_errors(tmp_path):
    root, workcase = write_valid_workcase_tree(tmp_path)
    content = workcase.read_text(encoding="utf-8")
    workcase.write_text(
        content.replace(
            "        - tests/code/test_fact_validate.py",
            "\n".join(
                [
                    "        - tests/code/test_fact_validate.py",
                    "        - python3 code/fact_validate.py ldvh-base/",
                    "        - workcase-0071",
                    "        - 95a0604",
                    "        - https://example.com/evidence",
                    "        - /tmp/non-stable-external-evidence.txt",
                    "        - specs/21-WorkCase-工作项.md（修订）",
                ]
            ),
        ),
        encoding="utf-8",
    )

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"


def test_workcase_evidence_refs_section_suffix_checks_path_part(tmp_path):
    root, workcase = write_valid_workcase_tree(tmp_path)
    content = workcase.read_text(encoding="utf-8")
    workcase.write_text(
        content.replace(
            "        - tests/code/test_fact_validate.py",
            "        - tests/code/test_fact_validate.py §fixture",
        ),
        encoding="utf-8",
    )

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"


def test_json_output_reports_current_workcase(tmp_path):
    root, _ = write_valid_workcase_tree(tmp_path)

    result = run_checker(root / "ldvh-base", extra_args=["--format", "json"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["files"] == 1
    assert payload["summary"]["errors"] == 0
