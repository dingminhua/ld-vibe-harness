import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "tools" / "fact_validate.py"


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


def base_tree(tmp_path: Path) -> Path:
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
""",
    )
    write_yaml(
        root / "ldvh-base" / "taskplans" / "taskplan-0001-core-plan.yaml",
        """
id: taskplan-0001
type: taskplan
title: Core Plan
status: active
created: "2026-06-12"
updated: "2026-06-12"
workarea: workarea-0001
description: Core plan
success_criteria: |
  - [ ] Plan can be validated
source: test
tasks:
  - task-0001
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
""",
    )
    write_yaml(
        root / "ldvh-base" / "tasks" / "task-0001-core-task.yaml",
        """
id: task-0001
type: task
title: Core Task
status: planned
created: "2026-06-12"
updated: "2026-06-12"
taskplan: taskplan-0001
description: Core task
source: test
acceptance: |
  - [ ] Task can be validated
blocked_by: []
deliverables: []
related_docs: []
related_adrs: []
""",
    )
    write_yaml(
        root / "ldvh-base" / "subtasks" / "subtask-0001-core-subtask.yaml",
        """
id: subtask-0001
type: subtask
title: Core SubTask
status: planned
created: "2026-06-12"
updated: "2026-06-12"
task: task-0001
description: Core subtask
source: test
acceptance: |
  - [ ] SubTask can be validated
blocked_by: []
""",
    )
    return root


def test_valid_workarea_taskplan_task_subtask_tree(tmp_path):
    root = base_tree(tmp_path)

    result = run_checker(root / "ldvh-base")

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=4 errors=0 warnings=0"
    assert result.stderr == ""


def test_workarea_archived_requires_archive_reason(tmp_path):
    root = base_tree(tmp_path)
    path = root / "ldvh-base" / "workareas" / "workarea-0001-core.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("status: active", "status: archived"), encoding="utf-8")

    result = run_checker(path)

    assert result.returncode == 1
    assert "MISSING_ARCHIVE_REASON" in result.stdout
    assert "archive_reason" in result.stdout


def test_taskplan_review_needed_requires_review_fields(tmp_path):
    root = base_tree(tmp_path)
    path = root / "ldvh-base" / "taskplans" / "taskplan-0001-core-plan.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("status: active", "status: review_needed"), encoding="utf-8")

    result = run_checker(path)

    assert result.returncode == 1
    assert "MISSING_TASKPLAN_REVIEW_FIELD" in result.stdout
    assert "review_requested_at" in result.stdout
    assert "completion_evidence" in result.stdout


def test_taskplan_closed_requires_closed_tasks_and_closed_at(tmp_path):
    root = base_tree(tmp_path)
    path = root / "ldvh-base" / "taskplans" / "taskplan-0001-core-plan.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "status: active",
            'status: closed\nreview_requested_at: "2026-06-12T00:00:00+08:00"\ncompletion_evidence: done',
        ),
        encoding="utf-8",
    )

    result = run_checker(path)

    assert result.returncode == 1
    assert "TASKPLAN_TASK_NOT_CLOSED" in result.stdout
    assert "MISSING_TASKPLAN_CLOSED_AT" in result.stdout


def test_task_requires_taskplan(tmp_path):
    root = base_tree(tmp_path)
    path = root / "ldvh-base" / "tasks" / "task-0001-core-task.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("taskplan: taskplan-0001\n", ""), encoding="utf-8")

    result = run_checker(path)

    assert result.returncode == 1
    assert "MISSING_REQUIRED_FIELD" in result.stdout
    assert "taskplan" in result.stdout


def test_task_rejects_legacy_intent_and_nested_task_fields(tmp_path):
    root = base_tree(tmp_path)
    path = root / "ldvh-base" / "tasks" / "task-0001-core-task.yaml"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\nsource_intent: intent-0001\nparent_task: task-0000\nsub_tasks:\n  - task-0002\n",
        encoding="utf-8",
    )

    result = run_checker(path)

    assert result.returncode == 1
    assert result.stdout.count("LEGACY_TASK_FIELD") == 3


def test_blocked_by_must_stay_in_same_taskplan(tmp_path):
    root = base_tree(tmp_path)
    write_yaml(
        root / "ldvh-base" / "taskplans" / "taskplan-0002-other-plan.yaml",
        """
id: taskplan-0002
type: taskplan
title: Other Plan
status: active
created: "2026-06-12"
updated: "2026-06-12"
workarea: workarea-0001
description: Other plan
success_criteria: |
  - [ ] Other plan can be validated
source: test
tasks:
  - task-0002
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
""",
    )
    write_yaml(
        root / "ldvh-base" / "tasks" / "task-0002-other-task.yaml",
        """
id: task-0002
type: task
title: Other Task
status: closed
created: "2026-06-12"
updated: "2026-06-12"
closed_at: "2026-06-12"
taskplan: taskplan-0002
description: Other task
source: test
acceptance: |
  - [x] Other task can be validated
verification: |
  ## 验证结果
  passed
closure_evidence: |
  ## 结论
  done
blocked_by: []
deliverables: []
related_docs: []
related_adrs: []
""",
    )
    task_path = root / "ldvh-base" / "tasks" / "task-0001-core-task.yaml"
    task_path.write_text(
        task_path.read_text(encoding="utf-8").replace("blocked_by: []", "blocked_by:\n  - task-0002"),
        encoding="utf-8",
    )

    result = run_checker(task_path)

    assert result.returncode == 1
    assert "BLOCKED_BY_TASKPLAN_MISMATCH" in result.stdout


def test_subtask_rejects_recursive_fields(tmp_path):
    root = base_tree(tmp_path)
    path = root / "ldvh-base" / "subtasks" / "subtask-0001-core-subtask.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\nparent_task: task-0001\nsub_tasks: []\n", encoding="utf-8")

    result = run_checker(path)

    assert result.returncode == 1
    assert result.stdout.count("FORBIDDEN_SUBTASK_FIELD") == 2


def test_change_file_rejected_by_validator(tmp_path):
    path = write_yaml(
        tmp_path / "change-0001-old-change.yaml",
        """
id: change-0001
type: change
title: Old Change
status: proposed
created: "2026-06-12"
updated: "2026-06-12"
description: Change is backed by Git commits
""",
    )

    result = run_checker(path)

    assert result.returncode == 2
    assert "UNKNOWN_OBJECT_TYPE" in result.stdout


def test_json_output_valid(tmp_path):
    root = base_tree(tmp_path)

    result = run_checker(root / "ldvh-base", extra_args=["--format", "json"])

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["summary"]["files"] == 4
    assert data["summary"]["errors"] == 0
    assert data["summary"]["warnings"] == 0
    assert data["issues"] == []
