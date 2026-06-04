"""Tests for tools/fact_model_cli.py: create / transition / delete / list / show commands."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "tools" / "ldvh_fact_cli.py"


def run_cli(*args, base_dir: Optional[str] = None):
    """Run fact_model_cli.py with the given arguments."""
    cmd = ["python3", str(SCRIPT_PATH)]
    if base_dir is not None:
        # Insert --base-dir right after the subcommand
        # We assume the caller passes subcommand as first arg
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


# ── create 命令 ──────────────────────────────────────────────────────────


def test_create_intent(tmp_path):
    result = run_cli("create", "intent", "--title", "My First Intent", base_dir=str(tmp_path))
    assert result.returncode == 0

    out_lines = result.stdout.strip().splitlines()
    assert len(out_lines) == 1
    created_path = Path(out_lines[0])

    # Verify file exists and content
    data = yaml.safe_load(created_path.read_text(encoding="utf-8"))
    assert data["id"] == "intent-0001"
    assert data["type"] == "intent"
    assert data["title"] == "My First Intent"
    assert data["status"] == "draft"
    for field in ("id", "type", "title", "status", "created", "updated",
                  "description", "success_criteria", "source"):
        assert field in data


def test_create_task(tmp_path):
    result = run_cli("create", "task", "--title", "Do Something", base_dir=str(tmp_path))
    assert result.returncode == 0

    out_lines = result.stdout.strip().splitlines()
    assert len(out_lines) == 1
    created_path = Path(out_lines[0])

    data = yaml.safe_load(created_path.read_text(encoding="utf-8"))
    assert data["id"] == "task-0001"
    assert data["type"] == "task"
    assert data["status"] == "planned"
    assert "acceptance" in data


def test_create_adr_with_change(tmp_path):
    result = run_cli("create", "adr", "--title", "Choose Framework", base_dir=str(tmp_path))
    assert result.returncode == 0

    out_lines = result.stdout.strip().splitlines()
    # ADR create should output two lines: ADR file and Change file
    assert len(out_lines) == 2

    adr_path = Path(out_lines[0])
    change_path = Path(out_lines[1])

    # Verify ADR
    adr_data = yaml.safe_load(adr_path.read_text(encoding="utf-8"))
    assert adr_data["id"] == "adr-0001"
    assert adr_data["type"] == "adr"
    assert adr_data["status"] == "proposed"
    for field in ("context", "decision", "consequences"):
        assert field in adr_data

    # Verify associated Change
    change_data = yaml.safe_load(change_path.read_text(encoding="utf-8"))
    assert change_data["id"] == "change-0001"
    assert change_data["type"] == "change"
    assert change_data["status"] == "proposed"
    assert "ADR adr-0001" in change_data["description"]


def test_create_auto_numbering(tmp_path):
    # Create first intent
    run_cli("create", "intent", "--title", "First", base_dir=str(tmp_path))
    # Create second intent
    result = run_cli("create", "intent", "--title", "Second", base_dir=str(tmp_path))
    assert result.returncode == 0

    out_lines = result.stdout.strip().splitlines()
    created_path = Path(out_lines[0])
    data = yaml.safe_load(created_path.read_text(encoding="utf-8"))
    assert data["id"] == "intent-0002"


def test_create_with_short_title(tmp_path):
    result = run_cli(
        "create", "memo", "--title", "My Memo Title",
        "--short-title", "custom-slug",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0

    out_lines = result.stdout.strip().splitlines()
    created_path = Path(out_lines[0])
    assert "custom-slug" in created_path.name


def test_create_pitfall(tmp_path):
    result = run_cli("create", "pitfall", "--title", "Common Mistake", base_dir=str(tmp_path))
    assert result.returncode == 0

    out_lines = result.stdout.strip().splitlines()
    data = yaml.safe_load(Path(out_lines[0]).read_text(encoding="utf-8"))
    assert data["id"] == "pitfall-0001"
    assert data["status"] == "draft"


def test_create_profile(tmp_path):
    result = run_cli("create", "profile", "--title", "Project Profile", base_dir=str(tmp_path))
    assert result.returncode == 0

    out_lines = result.stdout.strip().splitlines()
    data = yaml.safe_load(Path(out_lines[0]).read_text(encoding="utf-8"))
    assert data["id"] == "profile-0001"
    assert data["status"] == "draft"


def test_create_change(tmp_path):
    result = run_cli("create", "change", "--title", "Schema Update", base_dir=str(tmp_path))
    assert result.returncode == 0

    out_lines = result.stdout.strip().splitlines()
    data = yaml.safe_load(Path(out_lines[0]).read_text(encoding="utf-8"))
    assert data["id"] == "change-0001"
    assert data["status"] == "proposed"


# ── transition 命令 ──────────────────────────────────────────────────────


def test_transition_valid(tmp_path):
    # Create an intent first
    result = run_cli("create", "intent", "--title", "Transition Test", base_dir=str(tmp_path))
    intent_path = Path(result.stdout.strip().splitlines()[0])

    # Transition draft -> active
    result = run_cli("transition", str(intent_path), "--to", "active")
    assert result.returncode == 0
    assert "draft → active" in result.stdout

    # Verify file updated
    data = yaml.safe_load(intent_path.read_text(encoding="utf-8"))
    assert data["status"] == "active"


def test_transition_invalid_disallowed(tmp_path):
    # Create a task (status: planned)
    result = run_cli("create", "task", "--title", "Bad Transition", base_dir=str(tmp_path))
    task_path = Path(result.stdout.strip().splitlines()[0])

    # Try planned -> closed (not allowed)
    result = run_cli("transition", str(task_path), "--to", "closed")
    assert result.returncode == 1
    assert "不允许的流转" in result.stderr


def test_transition_backward_needs_reason(tmp_path):
    # Create a task and advance to verifying
    result = run_cli("create", "task", "--title", "Backward Test", base_dir=str(tmp_path))
    task_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(task_path), "--to", "executing")
    run_cli("transition", str(task_path), "--to", "verifying")

    # Try verifying -> executing without reason
    result = run_cli("transition", str(task_path), "--to", "executing")
    assert result.returncode == 1
    assert "需要提供 --reason" in result.stderr

    # With reason, should succeed
    result = run_cli("transition", str(task_path), "--to", "executing", "--reason", "needs more work")
    assert result.returncode == 0
    assert "verifying → executing" in result.stdout

    # Verify transition_reasons recorded
    data = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    assert "transition_reasons" in data
    assert data["transition_reasons"][0]["reason"] == "needs more work"


def test_transition_review_needed_to_executing_needs_reason(tmp_path):
    # Create task, advance to review_needed
    result = run_cli("create", "task", "--title", "Review Backward", base_dir=str(tmp_path))
    task_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(task_path), "--to", "executing")
    run_cli("transition", str(task_path), "--to", "verifying")
    run_cli("transition", str(task_path), "--to", "review_needed", "--reason", "ready for review")

    # Try review_needed -> executing without reason
    result = run_cli("transition", str(task_path), "--to", "executing")
    assert result.returncode == 1
    assert "需要提供 --reason" in result.stderr


def test_transition_task_close_requires_acceptance_and_evidence(tmp_path):
    # Create task, advance to review_needed
    result = run_cli("create", "task", "--title", "Close Test", base_dir=str(tmp_path))
    task_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(task_path), "--to", "executing")
    run_cli("transition", str(task_path), "--to", "verifying")
    run_cli("transition", str(task_path), "--to", "review_needed", "--reason", "ready")

    # Try closing without closure_evidence
    result = run_cli("transition", str(task_path), "--to", "closed")
    assert result.returncode == 1
    assert "closure_evidence" in result.stderr

    # Set closure_evidence but leave acceptance with unchecked items
    data = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    data["closure_evidence"] = "All tests pass"
    data["acceptance"] = "- [ ] Item one\n- [ ] Item two"
    task_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
                         encoding="utf-8")

    result = run_cli("transition", str(task_path), "--to", "closed")
    assert result.returncode == 1
    assert "acceptance" in result.stderr

    # Set acceptance all checked + closure_evidence
    data["acceptance"] = "- [x] Item one\n- [x] Item two"
    task_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
                         encoding="utf-8")

    result = run_cli("transition", str(task_path), "--to", "closed")
    assert result.returncode == 0
    assert "review_needed → closed" in result.stdout
    data = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    assert data["closed_at"]


def test_transition_invalid_target_status(tmp_path):
    result = run_cli("create", "intent", "--title", "Bad Target", base_dir=str(tmp_path))
    intent_path = Path(result.stdout.strip().splitlines()[0])

    # Try transitioning to a status that doesn't exist for intent
    result = run_cli("transition", str(intent_path), "--to", "executing")
    assert result.returncode == 1
    assert "目标状态不合法" in result.stderr


# ── delete 命令 ──────────────────────────────────────────────────────────


def test_delete_draft_status(tmp_path):
    result = run_cli("create", "intent", "--title", "Delete Me", base_dir=str(tmp_path))
    intent_path = Path(result.stdout.strip().splitlines()[0])
    assert intent_path.exists()

    result = run_cli("delete", str(intent_path))
    assert result.returncode == 0
    assert not intent_path.exists()


def test_delete_proposed_status(tmp_path):
    result = run_cli("create", "adr", "--title", "Delete ADR", base_dir=str(tmp_path))
    adr_path = Path(result.stdout.strip().splitlines()[0])

    result = run_cli("delete", str(adr_path))
    assert result.returncode == 0
    assert not adr_path.exists()


def test_delete_non_deletable_status(tmp_path):
    result = run_cli("create", "intent", "--title", "Active Intent", base_dir=str(tmp_path))
    intent_path = Path(result.stdout.strip().splitlines()[0])

    # Transition to active
    run_cli("transition", str(intent_path), "--to", "active")

    # Try deleting active intent
    result = run_cli("delete", str(intent_path))
    assert result.returncode == 1
    assert "不允许删除" in result.stderr
    assert intent_path.exists()


def test_delete_task_executing_status(tmp_path):
    result = run_cli("create", "task", "--title", "Executing Task", base_dir=str(tmp_path))
    task_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(task_path), "--to", "executing")

    result = run_cli("delete", str(task_path))
    assert result.returncode == 1
    assert "不允许删除" in result.stderr


# ── 无效输入 ──────────────────────────────────────────────────────────────


def test_invalid_object_type(tmp_path):
    result = run_cli("create", "invalid_type", "--title", "Bad Type", base_dir=str(tmp_path))
    assert result.returncode != 0


def test_invalid_status_in_yaml(tmp_path):
    """Transition command should reject a YAML file with an invalid current status."""
    # Manually create a YAML with invalid status
    bad_dir = tmp_path / "ldvh-base" / "intents"
    bad_dir.mkdir(parents=True)
    bad_yaml = bad_dir / "intent-0001-bad-status.yaml"
    bad_yaml.write_text(
        "id: intent-0001\ntype: intent\ntitle: Bad\nstatus: nonexistent\ncreated: '2026-06-04'\nupdated: '2026-06-04'\n",
        encoding="utf-8",
    )

    result = run_cli("transition", str(bad_yaml), "--to", "active")
    assert result.returncode == 1
    assert "当前状态不合法" in result.stderr


def test_transition_nonexistent_file(tmp_path):
    fake_path = tmp_path / "ldvh-base" / "tasks" / "task-9999-nope.yaml"
    result = run_cli("transition", str(fake_path), "--to", "active")
    assert result.returncode == 1


def test_delete_nonexistent_file(tmp_path):
    fake_path = tmp_path / "ldvh-base" / "intents" / "intent-9999-nope.yaml"
    result = run_cli("delete", str(fake_path))
    assert result.returncode == 1


# ── list 命令 ──────────────────────────────────────────────────────────


def test_list_text_output(tmp_path):
    # Create two intents
    run_cli("create", "intent", "--title", "First Intent", base_dir=str(tmp_path))
    run_cli("create", "intent", "--title", "Second Intent", base_dir=str(tmp_path))

    result = run_cli("list", "intent", base_dir=str(tmp_path))
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 2
    assert "intent-0001" in lines[0]
    assert "intent-0002" in lines[1]


def test_list_json_output(tmp_path):
    run_cli("create", "task", "--title", "List JSON Task", base_dir=str(tmp_path))

    result = run_cli("list", "task", "--format", "json", base_dir=str(tmp_path))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["action"] == "list"
    assert data["target"] == "task"
    assert data["summary"]["count"] == 1
    assert len(data["data"]["items"]) == 1
    item = data["data"]["items"][0]
    assert item["id"] == "task-0001"
    assert item["status"] == "planned"
    assert item["title"] == "List JSON Task"


def test_list_status_filter(tmp_path):
    run_cli("create", "intent", "--title", "Draft One", base_dir=str(tmp_path))
    # Create and transition second to active
    result = run_cli("create", "intent", "--title", "Active One", base_dir=str(tmp_path))
    intent_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(intent_path), "--to", "active")

    result = run_cli("list", "intent", "--status", "draft", base_dir=str(tmp_path))
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "intent-0001" in lines[0]
    assert "draft" in lines[0]


def test_list_empty_directory(tmp_path):
    result = run_cli("list", "memo", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "未找到 memo 对象" in result.stdout


# ── show 命令 ──────────────────────────────────────────────────────────


def test_show_by_file_path(tmp_path):
    result = run_cli("create", "memo", "--title", "Show Test", base_dir=str(tmp_path))
    memo_path = Path(result.stdout.strip().splitlines()[0])

    result = run_cli("show", str(memo_path))
    assert result.returncode == 0
    data = yaml.safe_load(result.stdout)
    assert data["id"] == "memo-0001"
    assert data["title"] == "Show Test"


def test_show_by_object_id(tmp_path):
    run_cli("create", "intent", "--title", "ID Lookup", base_dir=str(tmp_path))

    result = run_cli("show", "intent-0001", base_dir=str(tmp_path))
    assert result.returncode == 0
    data = yaml.safe_load(result.stdout)
    assert data["id"] == "intent-0001"


def test_show_json_output(tmp_path):
    result = run_cli("create", "task", "--title", "Show JSON", base_dir=str(tmp_path))
    task_path = Path(result.stdout.strip().splitlines()[0])

    result = run_cli("show", str(task_path), "--format", "json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["action"] == "show"
    assert data["summary"]["id"] == "task-0001"
    assert data["data"]["title"] == "Show JSON"


def test_show_nonexistent_id(tmp_path):
    result = run_cli("show", "task-9999", base_dir=str(tmp_path))
    assert result.returncode == 1
    assert "找不到对象" in result.stderr
