"""Tests for code/fact_cli.py under the WorkArea -> TaskPlan -> Task -> SubTask model."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "code" / "fact_cli.py"


def run_cli(*args, base_dir: Optional[str] = None):
    cmd = ["python3", str(SCRIPT_PATH)]
    if base_dir is not None:
        cmd.append(args[0])
        cmd.extend(["--base-dir", base_dir])
        cmd.extend(args[1:])
    else:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_create_workarea_taskplan_task_and_subtask(tmp_path):
    for object_type, expected_status in [
        ("workarea", "active"),
        ("taskplan", "draft"),
        ("task", "planned"),
        ("subtask", "planned"),
    ]:
        result = run_cli("create", object_type, "--title", f"Create {object_type}", base_dir=str(tmp_path))
        assert result.returncode == 0, result.stderr
        created_path = Path(result.stdout.strip())
        data = read_yaml(created_path)
        assert data["id"] == f"{object_type}-0001"
        assert data["type"] == object_type
        assert data["status"] == expected_status

    task_data = read_yaml(tmp_path / "ldvh-base" / "tasks" / "task-0001-create-task.yaml")
    assert "taskplan" in task_data
    assert "source_intent" not in task_data
    assert "parent_task" not in task_data
    assert "sub_tasks" not in task_data


def test_create_auto_numbering_uses_new_workarea_prefix(tmp_path):
    run_cli("create", "workarea", "--title", "First", base_dir=str(tmp_path))
    result = run_cli("create", "workarea", "--title", "Second", base_dir=str(tmp_path))

    assert result.returncode == 0
    data = read_yaml(Path(result.stdout.strip()))
    assert data["id"] == "workarea-0002"


def test_workarea_archive_requires_reason(tmp_path):
    result = run_cli("create", "workarea", "--title", "Archive Area", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())

    result = run_cli("transition", str(path), "--to", "archived")
    assert result.returncode == 1
    assert "archive_reason" in result.stderr

    data = read_yaml(path)
    data["archive_reason"] = "No longer used."
    write_yaml(path, data)

    result = run_cli("transition", str(path), "--to", "archived")
    assert result.returncode == 0
    assert "active → archived" in result.stdout
    assert read_yaml(path)["status"] == "archived"


def test_taskplan_review_and_close_flow(tmp_path):
    result = run_cli("create", "taskplan", "--title", "Review Plan", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())

    result = run_cli("transition", str(path), "--to", "active")
    assert result.returncode == 0

    result = run_cli("transition", str(path), "--to", "review_needed")
    assert result.returncode == 1
    assert "completion_evidence" in result.stderr

    data = read_yaml(path)
    data["completion_evidence"] = "Plan scope is complete."
    write_yaml(path, data)

    result = run_cli("transition", str(path), "--to", "review_needed")
    assert result.returncode == 0
    data = read_yaml(path)
    assert data["status"] == "review_needed"
    assert data["review_requested_at"]

    result = run_cli("transition", str(path), "--to", "closed")
    assert result.returncode == 0
    data = read_yaml(path)
    assert data["status"] == "closed"
    assert data["closed_at"]


def test_taskplan_review_needed_to_active_needs_reason(tmp_path):
    result = run_cli("create", "taskplan", "--title", "Return Plan", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())
    run_cli("transition", str(path), "--to", "active")
    data = read_yaml(path)
    data["completion_evidence"] = "Ready for review."
    write_yaml(path, data)
    run_cli("transition", str(path), "--to", "review_needed")

    result = run_cli("transition", str(path), "--to", "active")
    assert result.returncode == 1
    assert "需要提供 --reason" in result.stderr

    result = run_cli("transition", str(path), "--to", "active", "--reason", "needs another task")
    assert result.returncode == 0
    assert "review_needed → active" in result.stdout


def test_task_close_requires_acceptance_verification_and_evidence(tmp_path):
    result = run_cli("create", "task", "--title", "Close Task", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())
    run_cli("transition", str(path), "--to", "executing")
    run_cli("transition", str(path), "--to", "verifying")
    run_cli("transition", str(path), "--to", "review_needed")

    data = read_yaml(path)
    data["acceptance"] = "- [x] Done"
    data["verification"] = "pytest"
    write_yaml(path, data)

    result = run_cli("transition", str(path), "--to", "closed")
    assert result.returncode == 1
    assert "closure_evidence" in result.stderr

    data = read_yaml(path)
    data["closure_evidence"] = "All checks passed."
    write_yaml(path, data)

    result = run_cli("transition", str(path), "--to", "closed")
    assert result.returncode == 0
    assert read_yaml(path)["closed_at"]


def test_subtask_close_requires_verification_and_evidence(tmp_path):
    result = run_cli("create", "subtask", "--title", "Close SubTask", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())
    run_cli("transition", str(path), "--to", "executing")
    run_cli("transition", str(path), "--to", "verifying")
    run_cli("transition", str(path), "--to", "review_needed")

    result = run_cli("transition", str(path), "--to", "closed")
    assert result.returncode == 1
    assert "verification" in result.stderr

    data = read_yaml(path)
    data["verification"] = "pytest"
    data["closure_evidence"] = "done"
    write_yaml(path, data)

    result = run_cli("transition", str(path), "--to", "closed")
    assert result.returncode == 0
    assert read_yaml(path)["closed_at"]


def test_list_and_show_workarea_json(tmp_path):
    run_cli("create", "workarea", "--title", "First Area", base_dir=str(tmp_path))
    run_cli("create", "workarea", "--title", "Second Area", base_dir=str(tmp_path))

    result = run_cli("list", "workarea", "--format", "json", base_dir=str(tmp_path))
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["count"] == 2
    assert [item["id"] for item in payload["data"]["items"]] == ["workarea-0001", "workarea-0002"]

    result = run_cli("show", "workarea-0001", "--format", "json", base_dir=str(tmp_path))
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["id"] == "workarea-0001"
    assert payload["data"]["title"] == "First Area"


def test_delete_draft_taskplan(tmp_path):
    result = run_cli("create", "taskplan", "--title", "Delete Plan", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())

    result = run_cli("delete", str(path))

    assert result.returncode == 0
    assert not path.exists()


def test_legacy_intent_type_is_rejected(tmp_path):
    result = run_cli("create", "intent", "--title", "Old Intent", base_dir=str(tmp_path))

    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_deps_outputs_structured_task_dependencies(tmp_path):
    blocker = run_cli("create", "task", "--title", "Blocker", base_dir=str(tmp_path))
    blocked = run_cli("create", "task", "--title", "Blocked", base_dir=str(tmp_path))
    blocked_path = Path(blocked.stdout.strip())
    data = read_yaml(blocked_path)
    data["blocked_by"] = ["task-0001"]
    write_yaml(blocked_path, data)

    result = run_cli("deps", "task-0002", "--format", "json", base_dir=str(tmp_path))

    assert blocker.returncode == 0
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["blocked_by_count"] == 1
    assert payload["data"]["blocked_by"][0]["id"] == "task-0001"
