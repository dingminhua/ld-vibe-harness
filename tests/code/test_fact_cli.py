"""Tests for code/fact_cli.py WorkPlan writes and legacy object compatibility."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "code" / "fact_cli.py"
AUTH_ARGS = (
    "--human-gate-confirmed",
    "--confirmed-by",
    "tester",
    "--confirmation-context",
    "pytest controlled write",
)


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


def read_study(path: Path):
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    end = content.index("\n---", 4)
    frontmatter = yaml.safe_load(content[4:end])
    return frontmatter, content[end + 4:].lstrip()


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def authorized(*args: str) -> tuple[str, ...]:
    return (*args, *AUTH_ARGS)


def write_legacy_taskplan(tmp_path: Path, *, title: str = "Legacy Plan", status: str = "draft", suffix: str = "legacy-plan") -> Path:
    path = tmp_path / "ldvh-base" / "taskplans" / f"taskplan-0001-{suffix}.yaml"
    write_yaml(
        path,
        {
            "id": "taskplan-0001",
            "type": "taskplan",
            "title": title,
            "status": status,
            "created": "2026-06-01T00:00:00",
            "updated": "2026-06-01T00:00:00",
            "workarea": "",
            "priority": "P2",
            "description": "Legacy plan fixture.",
            "success_criteria": "- [x] Fixture ready",
            "source": "pytest",
            "tasks": [],
            "completion_evidence": "",
            "review_requested_at": "",
            "closed_at": "",
            "related_docs": [],
            "related_adrs": [],
            "related_memos": [],
            "related_pitfalls": [],
        },
    )
    return path


def write_legacy_task(tmp_path: Path, *, title: str = "Legacy Task", status: str = "planned", suffix: str = "legacy-task") -> Path:
    path = tmp_path / "ldvh-base" / "tasks" / f"task-0001-{suffix}.yaml"
    write_yaml(
        path,
        {
            "id": "task-0001",
            "type": "task",
            "title": title,
            "status": status,
            "created": "2026-06-01T00:00:00",
            "updated": "2026-06-01T00:00:00",
            "taskplan": "taskplan-0001",
            "description": "Legacy task fixture.",
            "source": "pytest",
            "acceptance": "- [x] Fixture ready",
            "blocked_by": [],
            "deliverables": [],
            "verification": "## 验证计划\n\n## 验证命令\n",
            "closure_evidence": "",
        },
    )
    return path


def write_legacy_subtask(tmp_path: Path, *, title: str = "Legacy SubTask", status: str = "planned") -> Path:
    path = tmp_path / "ldvh-base" / "subtasks" / "subtask-0001-legacy-subtask.yaml"
    write_yaml(
        path,
        {
            "id": "subtask-0001",
            "type": "subtask",
            "title": title,
            "status": status,
            "created": "2026-06-01T00:00:00",
            "updated": "2026-06-01T00:00:00",
            "task": "task-0001",
            "description": "Legacy subtask fixture.",
            "source": "pytest",
            "acceptance": "- [x] Fixture ready",
            "blocked_by": [],
            "verification": "## 验证计划\n\n## 验证命令\n",
            "closure_evidence": "",
        },
    )
    return path


def test_create_workarea_and_reject_legacy_work_objects(tmp_path):
    result = run_cli("create", "workarea", "--title", "Create workarea", base_dir=str(tmp_path))
    assert result.returncode == 0, result.stderr
    data = read_yaml(Path(result.stdout.strip()))
    assert data["id"] == "workarea-0001"
    assert data["type"] == "workarea"
    assert data["status"] == "active"
    assert data["workplans"] == []

    for object_type in ("taskplan", "task", "subtask"):
        rejected = run_cli("create", object_type, "--title", f"Create {object_type}", base_dir=str(tmp_path))
        assert rejected.returncode == 1
        assert "已废弃" in rejected.stderr


def test_create_and_transition_workplan_contract(tmp_path):
    result = run_cli("create", "workplan", "--title", "Create WorkPlan", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())

    assert result.returncode == 0, result.stderr
    data = read_yaml(path)
    assert data["id"] == "workplan-0001"
    assert data["type"] == "workplan"
    assert data["status"] == "draft"
    assert data["priority"] == "P2"
    assert data["orchestration"]["mode"] == "single"
    assert data["orchestration"]["execution_items"] == []
    assert data["related_workplans"] == []
    assert data["related_changes"] == []

    rejected = run_cli(*authorized("transition", str(path), "--to", "active"))
    assert rejected.returncode == 1
    assert "orchestration.execution_items" in rejected.stderr

    data["orchestration"]["execution_items"] = [
        {
            "id": "item-1",
            "title": "Run check",
            "role": "code",
            "mode": "single",
            "input_refs": [],
            "expected_output": "Check result",
            "status": "done",
            "result_summary": "Check passed.",
            "evidence_refs": [],
            "blocking_reason": None,
        }
    ]
    data["verification_evidence"] = "## 验证结果\npassed"
    data["closure_evidence"] = "## 结论\nready"
    write_yaml(path, data)

    accepted = run_cli(*authorized("transition", str(path), "--to", "active"))
    assert accepted.returncode == 0, accepted.stderr

    review = run_cli(*authorized("transition", str(path), "--to", "review_needed"))
    assert review.returncode == 0, review.stderr
    data = read_yaml(path)
    assert data["review_requested_at"]

    closed = run_cli(*authorized("transition", str(path), "--to", "closed"))
    assert closed.returncode == 0, closed.stderr
    assert read_yaml(path)["closed_at"]


def test_update_workplan_list_fields_and_block_scalars(tmp_path):
    result = run_cli("create", "workplan", "--title", "Update WorkPlan", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())

    accepted = run_cli(
        *authorized(
            "update",
            str(path),
            "--set",
            "related_changes=abc1234,def5678",
            "--set",
            "verification_evidence=## 验证结果\\npassed",
        )
    )

    assert accepted.returncode == 0, accepted.stderr
    data = read_yaml(path)
    assert data["related_changes"] == ["abc1234", "def5678"]
    assert data["verification_evidence"] == "## 验证结果\npassed"
    text = path.read_text(encoding="utf-8")
    assert "verification_evidence: |" in text
    assert "related_changes:\n- abc1234\n- def5678" in text


def test_create_auto_numbering_uses_new_workarea_prefix(tmp_path):
    run_cli("create", "workarea", "--title", "First", base_dir=str(tmp_path))
    result = run_cli("create", "workarea", "--title", "Second", base_dir=str(tmp_path))

    assert result.returncode == 0
    data = read_yaml(Path(result.stdout.strip()))
    assert data["id"] == "workarea-0002"


def test_workarea_archive_requires_reason(tmp_path):
    result = run_cli("create", "workarea", "--title", "Archive Area", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())

    result = run_cli(*authorized("transition", str(path), "--to", "archived"))
    assert result.returncode == 1
    assert "archive_reason" in result.stderr

    data = read_yaml(path)
    data["archive_reason"] = "No longer used."
    write_yaml(path, data)

    result = run_cli(*authorized("transition", str(path), "--to", "archived"))
    assert result.returncode == 0
    assert "active → archived" in result.stdout
    assert read_yaml(path)["status"] == "archived"


def test_taskplan_review_and_close_flow(tmp_path):
    path = write_legacy_taskplan(tmp_path, title="Review Plan", suffix="review-plan")

    result = run_cli(*authorized("transition", str(path), "--to", "active"))
    assert result.returncode == 0

    result = run_cli(*authorized("transition", str(path), "--to", "review_needed"))
    assert result.returncode == 1
    assert "completion_evidence" in result.stderr

    data = read_yaml(path)
    data["completion_evidence"] = "Plan scope is complete."
    write_yaml(path, data)

    result = run_cli(*authorized("transition", str(path), "--to", "review_needed"))
    assert result.returncode == 0
    data = read_yaml(path)
    assert data["status"] == "review_needed"
    assert data["review_requested_at"]

    result = run_cli(*authorized("transition", str(path), "--to", "closed"))
    assert result.returncode == 0
    data = read_yaml(path)
    assert data["status"] == "closed"
    assert data["closed_at"]


def test_create_memo_uses_priority_not_importance(tmp_path):
    result = run_cli("create", "memo", "--title", "Create memo", base_dir=str(tmp_path))

    assert result.returncode == 0, result.stderr
    data = read_yaml(Path(result.stdout.strip()))
    assert data["status"] == "pending"
    assert data["priority"] == "P3"
    assert data["source"] == "conversation"
    assert data["evolution"] == []
    assert data["related_studies"] == []
    assert "related_changes" not in data
    assert "importance" not in data


def test_create_study_uses_markdown_frontmatter(tmp_path):
    result = run_cli("create", "study", "--title", "Create study", base_dir=str(tmp_path))

    assert result.returncode == 0, result.stderr
    created_path = Path(result.stdout.strip())
    assert created_path.name == "study-0001-create-study.md"
    frontmatter, body = read_study(created_path)
    assert frontmatter["id"] == "study-0001"
    assert frontmatter["type"] == "study"
    assert frontmatter["status"] == "draft"
    assert frontmatter["source"] == "ai"
    assert frontmatter["related_memos"] == []
    assert "related_changes" not in frontmatter
    assert "# Create study" in body


def test_memo_resolve_and_discard_require_supporting_fields(tmp_path):
    result = run_cli("create", "memo", "--title", "Route memo", base_dir=str(tmp_path))
    path = Path(result.stdout.strip())

    result = run_cli(*authorized("transition", str(path), "--to", "resolved"))
    assert result.returncode == 1
    assert "resolved_to" in result.stderr

    data = read_yaml(path)
    data["resolved_to"] = {"type": "task", "ref": "task-0001"}
    write_yaml(path, data)

    result = run_cli(*authorized("transition", str(path), "--to", "resolved"))
    assert result.returncode == 0
    data = read_yaml(path)
    assert data["status"] == "resolved"
    assert data["resolved_at"]

    result = run_cli(*authorized("transition", str(path), "--to", "discarded"))
    assert result.returncode == 1
    assert "discard_reason" in result.stderr

    data["discard_reason"] = "分流记录已被目标对象承接。"
    write_yaml(path, data)

    result = run_cli(*authorized("transition", str(path), "--to", "discarded"))
    assert result.returncode == 0
    assert read_yaml(path)["status"] == "discarded"


def test_taskplan_review_needed_to_active_needs_reason(tmp_path):
    path = write_legacy_taskplan(tmp_path, title="Return Plan", suffix="return-plan")
    run_cli(*authorized("transition", str(path), "--to", "active"))
    data = read_yaml(path)
    data["completion_evidence"] = "Ready for review."
    write_yaml(path, data)
    run_cli(*authorized("transition", str(path), "--to", "review_needed"))

    result = run_cli(*authorized("transition", str(path), "--to", "active"))
    assert result.returncode == 1
    assert "需要提供 --reason" in result.stderr

    result = run_cli(*authorized("transition", str(path), "--to", "active", "--reason", "needs another task"))
    assert result.returncode == 0
    assert "review_needed → active" in result.stdout


def test_task_close_requires_acceptance_verification_and_evidence(tmp_path):
    write_legacy_taskplan(tmp_path)
    path = write_legacy_task(tmp_path, title="Close Task", suffix="close-task")
    run_cli(*authorized("transition", str(path), "--to", "executing"))
    run_cli(*authorized("transition", str(path), "--to", "verifying"))
    run_cli(*authorized("transition", str(path), "--to", "review_needed"))

    data = read_yaml(path)
    data["acceptance"] = "- [x] Done"
    data["verification"] = "pytest"
    write_yaml(path, data)

    result = run_cli(*authorized("transition", str(path), "--to", "closed"))
    assert result.returncode == 1
    assert "closure_evidence" in result.stderr

    data = read_yaml(path)
    data["closure_evidence"] = "All checks passed."
    write_yaml(path, data)

    result = run_cli(*authorized("transition", str(path), "--to", "closed"))
    assert result.returncode == 0
    assert read_yaml(path)["closed_at"]


def test_subtask_close_requires_verification_and_evidence(tmp_path):
    write_legacy_task(tmp_path)
    path = write_legacy_subtask(tmp_path, title="Close SubTask")
    run_cli(*authorized("transition", str(path), "--to", "executing"))
    run_cli(*authorized("transition", str(path), "--to", "verifying"))
    run_cli(*authorized("transition", str(path), "--to", "review_needed"))

    result = run_cli(*authorized("transition", str(path), "--to", "closed"))
    assert result.returncode == 1
    assert "closure_evidence" in result.stderr

    data = read_yaml(path)
    data["verification"] = "pytest"
    data["closure_evidence"] = "done"
    write_yaml(path, data)

    result = run_cli(*authorized("transition", str(path), "--to", "closed"))
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
    path = write_legacy_taskplan(tmp_path, title="Delete Plan", suffix="delete-plan")

    result = run_cli(*authorized("delete", str(path)))

    assert result.returncode == 0
    assert not path.exists()


def test_transition_requires_human_gate(tmp_path):
    path = write_legacy_taskplan(tmp_path, title="Gate Plan", suffix="gate-plan")

    result = run_cli("transition", str(path), "--to", "active")

    assert result.returncode == 1
    assert "--human-gate-confirmed" in result.stderr
    assert read_yaml(path)["status"] == "draft"


def test_delete_requires_human_gate(tmp_path):
    path = write_legacy_taskplan(tmp_path, title="Gate Delete", suffix="gate-delete")

    result = run_cli("delete", str(path))

    assert result.returncode == 1
    assert "--human-gate-confirmed" in result.stderr
    assert path.exists()


def test_update_requires_human_gate_and_updates_when_authorized(tmp_path):
    path = write_legacy_taskplan(tmp_path, title="Gate Update", suffix="gate-update")

    rejected = run_cli("update", str(path), "--set", "title=Rejected title")
    assert rejected.returncode == 1
    assert "--human-gate-confirmed" in rejected.stderr
    assert read_yaml(path)["title"] == "Gate Update"

    accepted = run_cli(*authorized("update", str(path), "--set", "title=Accepted title"))
    assert accepted.returncode == 0
    assert read_yaml(path)["title"] == "Accepted title"


def test_legacy_intent_type_is_rejected(tmp_path):
    result = run_cli("create", "intent", "--title", "Old Intent", base_dir=str(tmp_path))

    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_deps_outputs_structured_task_dependencies(tmp_path):
    write_legacy_taskplan(tmp_path)
    blocker_path = write_legacy_task(tmp_path, title="Blocker", suffix="blocker")
    blocked_path = tmp_path / "ldvh-base" / "tasks" / "task-0002-blocked.yaml"
    blocked_data = read_yaml(blocker_path)
    blocked_data["id"] = "task-0002"
    blocked_data["title"] = "Blocked"
    write_yaml(blocked_path, blocked_data)
    data = read_yaml(blocked_path)
    data["blocked_by"] = ["task-0001"]
    write_yaml(blocked_path, data)

    result = run_cli("deps", "task-0002", "--format", "json", base_dir=str(tmp_path))

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["blocked_by_count"] == 1
    assert payload["data"]["blocked_by"][0]["id"] == "task-0001"
