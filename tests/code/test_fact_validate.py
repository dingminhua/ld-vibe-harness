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
    write_yaml(
        root / "ldvh-base" / "workareas" / "workarea-0001-core.yaml",
        """
id: workarea-0001
type: workarea
title: Core
status: active
created: "2026-06-12"
updated: "2026-06-12"
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
created: "2026-06-12"
updated: "2026-06-12"
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


def test_json_output_reports_current_workplan(tmp_path):
    root, _ = write_valid_workplan_tree(tmp_path)

    result = run_checker(root / "ldvh-base", extra_args=["--format", "json"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["files"] == 2
    assert payload["summary"]["errors"] == 0
