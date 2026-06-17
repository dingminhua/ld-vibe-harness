from __future__ import annotations

import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "code" / "workplan_migration.py"


def write_yaml(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def run_preview(root: Path, *args: str):
    return subprocess.run(
        ["python3", str(SCRIPT_PATH), "--base-dir", str(root), *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_fact_validate(root: Path):
    return subprocess.run(
        ["python3", str(PROJECT_ROOT / "code" / "fact_validate.py"), str(root / "ldvh-base")],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_legacy_tree(root: Path) -> None:
    write_yaml(
        root / "ldvh-base" / "workareas" / "workarea-0001-core.yaml",
        """
id: workarea-0001
type: workarea
title: Core WorkArea
status: active
created: "2026-06-12"
updated: "2026-06-13"
description: Core test area.
source: test
owners: []
tags: []
workplans: []
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
related_changes: []
""",
    )
    write_yaml(
        root / "ldvh-base" / "taskplans" / "taskplan-0001-demo.yaml",
        """
id: taskplan-0001
type: taskplan
title: Legacy Plan
status: closed
created: "2026-06-12"
updated: "2026-06-13"
workarea: workarea-0001
priority: P1
description: Legacy plan description.
success_criteria: |
  - [x] Legacy task closed.
source: test
tasks:
  - task-0001
related_docs:
  - docs/demo.md
related_adrs: []
related_memos: []
related_pitfalls: []
review_requested_at: "2026-06-13T00:00:00+08:00"
completion_evidence: |
  ## 验证结果
  Legacy plan passed.
closed_at: "2026-06-13T01:00:00+08:00"
        """,
    )
    write_yaml(
        root / "docs" / "demo.md",
        """
# Demo
""",
    )
    write_yaml(
        root / "ldvh-base" / "tasks" / "task-0001-demo.yaml",
        """
id: task-0001
type: task
title: Legacy Task
status: closed
created: "2026-06-12"
updated: "2026-06-13"
taskplan: taskplan-0001
description: Legacy task description.
source: test
acceptance: |
  - [x] Task passed.
verification: |
  ## 验证结果
  Task verification passed.
closure_evidence: |
  ## 结论
  Task closed.
blocked_by: []
deliverables:
  - docs/demo.md
related_docs: []
related_adrs: []
related_changes:
  - abc1234
closed_at: "2026-06-13T01:00:00+08:00"
""",
    )


def test_preview_maps_taskplan_to_workplan_contract(tmp_path):
    write_legacy_tree(tmp_path)

    result = run_preview(tmp_path, "--id", "taskplan-0001")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["summary"]["taskplan_count"] == 1
    assert payload["summary"]["convertible_count"] == 1
    item = payload["items"][0]
    assert item["source_id"] == "taskplan-0001"
    assert item["target_id"] == "workplan-0001"
    assert item["target_path"].endswith("ldvh-base/workplans/workplan-0001-demo.yaml")
    assert item["can_convert"] is True
    assert item["warning_count"] == 1
    assert item["issues"][0]["code"] == "COMPLETION_EVIDENCE_SPLIT"
    workplan = item["workplan"]
    assert workplan["type"] == "workplan"
    assert workplan["status"] == "closed"
    assert workplan["verification_evidence"].startswith("## 验证结果")
    assert workplan["closure_evidence"].startswith("## 验证结果")
    assert workplan["orchestration"]["mode"] == "single"
    execution_item = workplan["orchestration"]["execution_items"][0]
    assert execution_item["id"] == "task-0001"
    assert execution_item["status"] == "done"
    assert execution_item["role"] == "legacy-task"
    assert "docs/demo.md" in execution_item["evidence_refs"]


def test_preview_blocks_missing_legacy_task(tmp_path):
    write_yaml(
        tmp_path / "ldvh-base" / "workareas" / "workarea-0001-core.yaml",
        """
id: workarea-0001
type: workarea
title: Core WorkArea
status: active
created: "2026-06-12"
updated: "2026-06-13"
description: Core test area.
source: test
owners: []
tags: []
workplans: []
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
related_changes: []
""",
    )
    write_yaml(
        tmp_path / "ldvh-base" / "taskplans" / "taskplan-0002-missing-task.yaml",
        """
id: taskplan-0002
type: taskplan
title: Missing Task Plan
status: active
created: "2026-06-12"
updated: "2026-06-13"
workarea: workarea-0001
priority: P2
description: Legacy plan description.
success_criteria: |
  - [ ] Task exists.
source: test
tasks:
  - task-0002
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
""",
    )

    result = run_preview(tmp_path, "--id", "taskplan-0002")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["summary"]["blocked_count"] == 1
    assert payload["items"][0]["can_convert"] is False
    assert payload["items"][0]["issues"][0]["code"] == "TASK_NOT_FOUND"


def test_write_creates_workplan_and_updates_workarea(tmp_path):
    write_legacy_tree(tmp_path)

    result = run_preview(
        tmp_path,
        "--write",
        "--human-gate-confirmed",
        "--confirmed-by",
        "pytest",
        "--confirmation-context",
        "controlled migration test",
        "--id",
        "taskplan-0001",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["action"] == "write-taskplan-to-workplan"
    assert payload["write"]["written_count"] == 1
    assert payload["write"]["updated_workarea_count"] == 1

    workplan_path = tmp_path / "ldvh-base" / "workplans" / "workplan-0001-demo.yaml"
    workarea_path = tmp_path / "ldvh-base" / "workareas" / "workarea-0001-core.yaml"
    assert workplan_path.exists()
    workplan_text = workplan_path.read_text(encoding="utf-8")
    assert "Human Gate confirmed by pytest: controlled migration test" in workplan_text
    assert "verification_evidence: |" in workplan_text

    workarea_text = workarea_path.read_text(encoding="utf-8")
    assert "description: Core test area.\nsource: test" in workarea_text
    assert "workplans:\n- workplan-0001" in workarea_text

    validation = run_fact_validate(tmp_path)
    assert validation.returncode == 0, validation.stdout + validation.stderr


def test_write_requires_human_gate_confirmation(tmp_path):
    result = run_preview(tmp_path, "--write")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["issues"][0]["code"] == "HUMAN_GATE_REQUIRED"
