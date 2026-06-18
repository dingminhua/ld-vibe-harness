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


def write_valid_workplan_tree(tmp_path: Path, *, status: str = "active") -> tuple[Path, Path]:
    root = tmp_path / "project"
    (root / "tests" / "code").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "code" / "test_fact_validate.py").write_text("# evidence fixture\n", encoding="utf-8")
    write_yaml(
        root / "ldvh-base" / "workareas" / "workarea-0001-core.yaml",
        """
id: workarea-0001
type: workarea
title: Core
status: active
created: "2026-06-12T09:00:00"
updated: "2026-06-12T09:30:00"
description: Core work area
source: test
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
workplans:
  - workplan-0001
""",
    )
    workplan = write_yaml(
        root / "ldvh-base" / "workplans" / "workplan-0001-core-plan.yaml",
        f"""
id: workplan-0001
type: workplan
title: Core Plan
status: {status}
created: "2026-06-12T09:00:00"
updated: "2026-06-12T09:30:00"
workarea: workarea-0001
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
      expected_output: Current WorkPlan validates.
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
  ## 验证结果

  当前 WorkPlan 校验通过。
closure_evidence: |
  ## 结论

  可进入关闭审查。
review_requested_at: "2026-06-12T00:00:00"
closed_at: {"'2026-06-12T01:00:00'" if status == "closed" else "''"}
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
related_workplans: []
related_changes: []
""",
    )
    return root, workplan


def test_valid_workplan_tree(tmp_path):
    root, _ = write_valid_workplan_tree(tmp_path)

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=2 errors=0 warnings=0"
    assert result.stderr == ""


def test_legacy_taskplan_file_is_unknown_object_type(tmp_path):
    root, _ = write_valid_workplan_tree(tmp_path)
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
    root, _ = write_valid_workplan_tree(tmp_path)
    workarea = root / "ldvh-base" / "workareas" / "workarea-0001-core.yaml"
    workarea.write_text(
        workarea.read_text(encoding="utf-8")
        .replace('created: "2026-06-12T09:00:00"', 'created: "2026-06-12"')
        .replace('updated: "2026-06-12T09:30:00"', 'updated: "2026-06-12"'),
        encoding="utf-8",
    )

    result = run_checker(workarea)

    assert result.returncode == 1
    assert "INVALID_DATETIME_FIELD" in result.stdout
    assert "created" in result.stdout
    assert "updated" in result.stdout


def test_study_draft_status_is_invalid(tmp_path):
    root, _ = write_valid_workplan_tree(tmp_path)
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
source: ai
source_docs: []
related_workareas: []
related_workplans: []
related_adrs: []
related_memos: []
related_pitfalls: []
related_docs: []
archive_reason:
---

# Draft Report

This report should not validate because Study has no draft state.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout
    assert "draft" in result.stdout


def test_study_superseded_status_and_field_are_invalid(tmp_path):
    root, _ = write_valid_workplan_tree(tmp_path)
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
source: ai
source_docs: []
related_workareas: []
related_workplans: []
related_adrs: []
related_memos: []
related_pitfalls: []
related_docs: []
superseded_by: study-0002
archive_reason:
---

# Superseded Report

This report should not validate because Study has no superseded state.
""",
        encoding="utf-8",
    )

    result = run_checker(study)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout
    assert "superseded" in result.stdout
    assert "REMOVED_OBJECT_FIELD" in result.stdout
    assert "superseded_by" in result.stdout


def test_pitfall_repeatability_field_is_no_longer_allowed(tmp_path):
    root, _ = write_valid_workplan_tree(tmp_path)
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
  Validator rejects the legacy field.
avoidance: |
  Do not write repeatability in Pitfall facts.
applicability: |
  Applies to Pitfall facts.
repeatability: recurring
tags: []
source_objects: []
source_memos: []
related_workareas: []
related_workplans: []
related_adrs: []
related_changes: []
related_docs: []
related_rules: []
superseded_by:
archive_reason:
notes:
""",
    )

    result = run_checker(pitfall)

    assert result.returncode == 1
    assert "REMOVED_OBJECT_FIELD" in result.stdout
    assert "repeatability" in result.stdout


def test_workarea_taskplans_field_is_no_longer_allowed(tmp_path):
    root, _ = write_valid_workplan_tree(tmp_path)
    workarea = root / "ldvh-base" / "workareas" / "workarea-0001-core.yaml"
    workarea.write_text(workarea.read_text(encoding="utf-8") + "taskplans:\n  - taskplan-0001\n", encoding="utf-8")

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 1
    assert "REMOVED_WORKAREA_FIELD" in result.stdout
    assert "taskplans" in result.stdout


def test_workplan_legacy_fields_are_errors(tmp_path):
    _, workplan = write_valid_workplan_tree(tmp_path)
    workplan.write_text(
        workplan.read_text(encoding="utf-8") + "tasks: []\ncompletion_evidence: done\n",
        encoding="utf-8",
    )

    result = run_checker(workplan)

    assert result.returncode == 1
    assert "LEGACY_WORKPLAN_FIELD" in result.stdout
    assert "tasks" in result.stdout
    assert "completion_evidence" in result.stdout


def test_workplan_evidence_refs_missing_path_is_error(tmp_path):
    root, workplan = write_valid_workplan_tree(tmp_path)
    content = workplan.read_text(encoding="utf-8")
    workplan.write_text(
        content.replace(
            "        - tests/code/test_fact_validate.py",
            "        - ldvh-base/workplans/workplan-9999-missing.yaml",
        ),
        encoding="utf-8",
    )

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 1
    assert "EVIDENCE_REF_PATH_NOT_FOUND" in result.stdout
    assert "workplan-9999-missing.yaml" in result.stdout


def test_workplan_evidence_refs_non_paths_are_not_errors(tmp_path):
    root, workplan = write_valid_workplan_tree(tmp_path)
    content = workplan.read_text(encoding="utf-8")
    workplan.write_text(
        content.replace(
            "        - tests/code/test_fact_validate.py",
            "\n".join(
                [
                    "        - tests/code/test_fact_validate.py",
                    "        - python3 code/fact_validate.py ldvh-base/",
                    "        - workplan-0071",
                    "        - 95a0604",
                    "        - https://example.com/evidence",
                    "        - /tmp/non-stable-external-evidence.txt",
                    "        - specs/21-WorkPlan-工作计划.md（修订）",
                ]
            ),
        ),
        encoding="utf-8",
    )

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=2 errors=0 warnings=0"


def test_workplan_evidence_refs_section_suffix_checks_path_part(tmp_path):
    root, workplan = write_valid_workplan_tree(tmp_path)
    content = workplan.read_text(encoding="utf-8")
    workplan.write_text(
        content.replace(
            "        - tests/code/test_fact_validate.py",
            "        - tests/code/test_fact_validate.py §fixture",
        ),
        encoding="utf-8",
    )

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=2 errors=0 warnings=0"


def test_json_output_reports_current_workplan(tmp_path):
    root, _ = write_valid_workplan_tree(tmp_path)

    result = run_checker(root / "ldvh-base", extra_args=["--format", "json"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["files"] == 2
    assert payload["summary"]["errors"] == 0
