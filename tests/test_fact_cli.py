"""Tests for tools/fact_cli.py: all subcommands."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Optional

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "tools" / "fact_cli.py"

# 导入 fact_cli 模块用于单元测试
MODULE_PATH = SCRIPT_PATH
_spec = importlib.util.spec_from_file_location("fact_cli", MODULE_PATH)
fact_cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fact_cli)


def run_cli(*args, base_dir: Optional[str] = None):
    """Run fact_cli.py with the given arguments."""
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


# ── ADR 辅助函数 ────────────────────────────────────────────────────────


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def auth_args(**overrides):
    data = {
        "human_gate_confirmed": True,
        "confirmed_by": "user",
        "confirmation_context": "测试 Human Gate 确认",
    }
    data.update(overrides)
    return data


def adr_content(**overrides):
    data = {
        "slug": "test-adr",
        "title": "测试 ADR",
        "context": "测试背景",
        "decision": "测试决策",
        "consequences": "测试影响",
        "date": "2026-06-01",
        "alternatives": None,
        "affects": None,
        "related_objects": None,
        "related_rules": None,
    }
    data.update(overrides)
    return data


def write_adr(path, **overrides):
    data = {
        "id": "adr-0001",
        "type": "adr",
        "title": "测试 ADR",
        "status": "accepted",
        "created": "2026-06-01",
        "updated": "2026-06-01",
        "date": "2026-06-01",
        "context": "测试背景",
        "decision": "测试决策",
        "consequences": "测试影响",
        "affects": ["specs/12.01-Tools辅助规范.md"],
        "related_objects": [],
        "related_rules": ["specs/21-ADR-决策.md"],
    }
    data.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def read_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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
    assert data["blocked_by"] == []


def test_create_adr_no_change(tmp_path):
    """ADR 创建不再自动生成 Change YAML。Change 使用 Git commit 作为事实源。"""
    result = run_cli("create", "adr", "--title", "Choose Framework",
                     "--human-gate-confirmed", "--confirmed-by", "tester",
                     "--confirmation-context", "test",
                     base_dir=str(tmp_path))
    assert result.returncode == 0

    out_lines = result.stdout.strip().splitlines()
    # ADR create should output only ADR file (no Change file)
    assert len(out_lines) == 1

    adr_path = Path(out_lines[0])
    adr_data = yaml.safe_load(adr_path.read_text(encoding="utf-8"))
    assert adr_data["id"] == "adr-0001"
    assert adr_data["type"] == "adr"
    assert adr_data["status"] == "proposed"
    for field in ("context", "decision", "consequences"):
        assert field in adr_data


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


def test_transition_intent_review_needed_and_closed(tmp_path):
    result = run_cli("create", "intent", "--title", "Intent Review", base_dir=str(tmp_path))
    intent_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(intent_path), "--to", "active")

    result = run_cli("transition", str(intent_path), "--to", "review_needed")
    assert result.returncode == 1
    assert "completion_evidence" in result.stderr

    data = yaml.safe_load(intent_path.read_text(encoding="utf-8"))
    data["completion_evidence"] = "Related tasks are closed and success criteria are met."
    intent_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")

    result = run_cli("transition", str(intent_path), "--to", "review_needed")
    assert result.returncode == 0
    assert "active → review_needed" in result.stdout
    data = yaml.safe_load(intent_path.read_text(encoding="utf-8"))
    assert data["status"] == "review_needed"
    assert data["review_requested_at"]

    result = run_cli("transition", str(intent_path), "--to", "closed")
    assert result.returncode == 0
    assert "review_needed → closed" in result.stdout
    data = yaml.safe_load(intent_path.read_text(encoding="utf-8"))
    assert data["status"] == "closed"
    assert data["closed_at"]


def test_transition_intent_review_needed_to_active_needs_reason(tmp_path):
    result = run_cli("create", "intent", "--title", "Intent Return", base_dir=str(tmp_path))
    intent_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(intent_path), "--to", "active")
    data = yaml.safe_load(intent_path.read_text(encoding="utf-8"))
    data["completion_evidence"] = "Ready for review."
    intent_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")
    run_cli("transition", str(intent_path), "--to", "review_needed")

    result = run_cli("transition", str(intent_path), "--to", "active")
    assert result.returncode == 1
    assert "需要提供 --reason" in result.stderr

    result = run_cli("transition", str(intent_path), "--to", "active", "--reason", "needs more tasks")
    assert result.returncode == 0
    assert "review_needed → active" in result.stdout


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
    data = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    data["verification"] = "pytest"
    task_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
                         encoding="utf-8")
    result = run_cli("transition", str(task_path), "--to", "closed")
    assert result.returncode == 1
    assert "closure_evidence" in result.stderr

    # Set verification and closure_evidence but leave acceptance with unchecked items
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


def test_transition_task_close_requires_verification(tmp_path):
    result = run_cli("create", "task", "--title", "Close Needs Verification", base_dir=str(tmp_path))
    task_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(task_path), "--to", "executing")
    run_cli("transition", str(task_path), "--to", "verifying")
    run_cli("transition", str(task_path), "--to", "review_needed", "--reason", "ready")

    data = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    data["acceptance"] = "- [x] Item one"
    data["closure_evidence"] = "All tests pass"
    task_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")

    result = run_cli("transition", str(task_path), "--to", "closed")
    assert result.returncode == 1
    assert "verification" in result.stderr


def test_transition_task_close_requires_closed_subtasks(tmp_path):
    parent_result = run_cli("create", "task", "--title", "Parent", base_dir=str(tmp_path))
    parent_path = Path(parent_result.stdout.strip().splitlines()[0])
    child_result = run_cli("create", "task", "--title", "Child", base_dir=str(tmp_path))
    child_path = Path(child_result.stdout.strip().splitlines()[0])

    parent_data = yaml.safe_load(parent_path.read_text(encoding="utf-8"))
    parent_data["sub_tasks"] = ["task-0002"]
    parent_data["acceptance"] = "- [x] Item one"
    parent_data["verification"] = "pytest"
    parent_data["closure_evidence"] = "All tests pass"
    parent_path.write_text(yaml.dump(parent_data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")

    run_cli("transition", str(parent_path), "--to", "executing")
    run_cli("transition", str(parent_path), "--to", "verifying")
    run_cli("transition", str(parent_path), "--to", "review_needed", "--reason", "ready")

    result = run_cli("transition", str(parent_path), "--to", "closed")
    assert result.returncode == 1
    assert "子 Task 未关闭" in result.stderr

    child_data = yaml.safe_load(child_path.read_text(encoding="utf-8"))
    child_data["status"] = "closed"
    child_data["acceptance"] = "- [x] Item one"
    child_data["verification"] = "pytest"
    child_data["closure_evidence"] = "done"
    child_data["closed_at"] = "2026-06-11"
    child_path.write_text(yaml.dump(child_data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")

    result = run_cli("transition", str(parent_path), "--to", "closed")
    assert result.returncode == 0


def test_transition_invalid_target_status(tmp_path):
    result = run_cli("create", "intent", "--title", "Bad Target", base_dir=str(tmp_path))
    intent_path = Path(result.stdout.strip().splitlines()[0])

    # Try transitioning to a status that doesn't exist for intent
    result = run_cli("transition", str(intent_path), "--to", "executing")
    assert result.returncode == 1
    assert "目标状态不合法" in result.stderr


def test_transition_adr_proposed_to_deprecated_disallowed(tmp_path):
    result = run_cli(
        "create", "adr", "--title", "ADR Drift",
        "--human-gate-confirmed", "--confirmed-by", "tester",
        "--confirmation-context", "test",
        base_dir=str(tmp_path),
    )
    adr_path = Path(result.stdout.strip().splitlines()[0])

    result = run_cli(
        "transition", str(adr_path), "--to", "deprecated",
        "--human-gate-confirmed", "--confirmed-by", "tester",
        "--confirmation-context", "test",
    )

    assert result.returncode == 1
    assert "不允许的流转" in result.stderr


def test_transition_memo_resolved_to_archived(tmp_path):
    result = run_cli("create", "memo", "--title", "Memo Archive", base_dir=str(tmp_path))
    memo_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(memo_path), "--to", "active")
    data = yaml.safe_load(memo_path.read_text(encoding="utf-8"))
    data["resolved_to"] = "task-0001"
    memo_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")
    run_cli("transition", str(memo_path), "--to", "resolved")

    result = run_cli("transition", str(memo_path), "--to", "archived")

    assert result.returncode == 0
    assert "resolved → archived" in result.stdout


def test_transition_memo_resolved_to_archived_requires_route(tmp_path):
    result = run_cli("create", "memo", "--title", "Memo Bad Archive", base_dir=str(tmp_path))
    memo_path = Path(result.stdout.strip().splitlines()[0])
    data = yaml.safe_load(memo_path.read_text(encoding="utf-8"))
    data["status"] = "resolved"
    memo_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")

    result = run_cli("transition", str(memo_path), "--to", "archived")

    assert result.returncode == 1
    assert "resolved_to" in result.stderr


def test_transition_memo_resolved_requires_target(tmp_path):
    result = run_cli("create", "memo", "--title", "Memo Resolve", base_dir=str(tmp_path))
    memo_path = Path(result.stdout.strip().splitlines()[0])
    run_cli("transition", str(memo_path), "--to", "active")

    result = run_cli("transition", str(memo_path), "--to", "resolved")

    assert result.returncode == 1
    assert "resolved_to" in result.stderr


def test_transition_memo_archive_requires_reason(tmp_path):
    result = run_cli("create", "memo", "--title", "Memo Archive", base_dir=str(tmp_path))
    memo_path = Path(result.stdout.strip().splitlines()[0])

    result = run_cli("transition", str(memo_path), "--to", "archived")

    assert result.returncode == 1
    assert "archive_reason" in result.stderr


def test_transition_task_blocked_by_requires_closed_predecessor(tmp_path):
    blocker_result = run_cli("create", "task", "--title", "Blocker", base_dir=str(tmp_path))
    blocker_path = Path(blocker_result.stdout.strip().splitlines()[0])
    blocked_result = run_cli("create", "task", "--title", "Blocked", base_dir=str(tmp_path))
    blocked_path = Path(blocked_result.stdout.strip().splitlines()[0])

    blocked_data = yaml.safe_load(blocked_path.read_text(encoding="utf-8"))
    blocked_data["blocked_by"] = ["task-0001"]
    blocked_path.write_text(yaml.dump(blocked_data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")

    result = run_cli("transition", str(blocked_path), "--to", "executing")
    assert result.returncode == 1
    assert "前置 Task 未关闭" in result.stderr

    blocker_data = yaml.safe_load(blocker_path.read_text(encoding="utf-8"))
    blocker_data["status"] = "closed"
    blocker_data["closure_evidence"] = "done"
    blocker_data["closed_at"] = "2026-06-04"
    blocker_path.write_text(yaml.dump(blocker_data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")

    result = run_cli("transition", str(blocked_path), "--to", "executing")
    assert result.returncode == 0
    assert "planned → executing" in result.stdout


def test_deps_outputs_structured_task_dependencies(tmp_path):
    blocker_result = run_cli("create", "task", "--title", "Blocker", base_dir=str(tmp_path))
    blocker_path = Path(blocker_result.stdout.strip().splitlines()[0])
    blocked_result = run_cli("create", "task", "--title", "Blocked", base_dir=str(tmp_path))
    blocked_path = Path(blocked_result.stdout.strip().splitlines()[0])

    blocked_data = yaml.safe_load(blocked_path.read_text(encoding="utf-8"))
    blocked_data["blocked_by"] = ["task-0001"]
    blocked_path.write_text(yaml.dump(blocked_data, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")

    result = run_cli("deps", "task-0002", "--format", "json", base_dir=str(tmp_path))
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "deps"
    assert payload["summary"]["blocked_by_count"] == 1
    assert payload["summary"]["ready_to_execute"] is False
    assert payload["data"]["blocked_by"][0]["id"] == "task-0001"

    result = run_cli("deps", "task-0001", "--format", "json", base_dir=str(tmp_path))
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["blocks_count"] == 1
    assert payload["data"]["blocks"][0]["id"] == "task-0002"


# ── delete 命令 ──────────────────────────────────────────────────────────


def test_delete_draft_status(tmp_path):
    result = run_cli("create", "intent", "--title", "Delete Me", base_dir=str(tmp_path))
    intent_path = Path(result.stdout.strip().splitlines()[0])
    assert intent_path.exists()

    result = run_cli("delete", str(intent_path))
    assert result.returncode == 0
    assert not intent_path.exists()


def test_delete_proposed_status(tmp_path):
    result = run_cli("create", "adr", "--title", "Delete ADR",
                     "--human-gate-confirmed", "--confirmed-by", "tester",
                     "--confirmation-context", "test",
                     base_dir=str(tmp_path))
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


def test_list_json_includes_attention_summary_fields(tmp_path):
    memo_dir = tmp_path / "ldvh-base" / "memos"
    memo_dir.mkdir(parents=True)
    (memo_dir / "memo-0001-important-gap.yaml").write_text(
        """\
id: memo-0001
type: memo
title: Important Gap
status: draft
created: "2026-06-03"
updated: "2026-06-03"
description: Something to preserve
source: test
category: gap
priority: high
""",
        encoding="utf-8",
    )

    result = run_cli("list", "memo", "--format", "json", base_dir=str(tmp_path))
    assert result.returncode == 0
    item = json.loads(result.stdout)["data"]["items"][0]
    assert item["category"] == "gap"
    assert item["priority"] == "high"


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


# ── ADR 工具函数单元测试 ────────────────────────────────────────────────


def test_parse_list_values_handles_none_and_comma_separated():
    assert fact_cli._parse_list_values(None) == []
    assert fact_cli._parse_list_values(["a,b", "c"]) == ["a", "b", "c"]


def test_ensure_authorized_rejects_missing_gate():
    args = Args(human_gate_confirmed=False, confirmed_by="user", confirmation_context="ctx")
    with pytest.raises(SystemExit):
        fact_cli._ensure_authorized(args)


def test_ensure_authorized_rejects_missing_confirmed_by():
    args = Args(human_gate_confirmed=True, confirmed_by=None, confirmation_context="ctx")
    with pytest.raises(SystemExit):
        fact_cli._ensure_authorized(args)


def test_ensure_authorized_rejects_missing_context():
    args = Args(human_gate_confirmed=True, confirmed_by="user", confirmation_context=None)
    with pytest.raises(SystemExit):
        fact_cli._ensure_authorized(args)


def test_load_all_of_type_returns_objects(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml")
    write_adr(adrs_dir / "adr-0002-second.yaml", id="adr-0002", title="第二个 ADR")

    objects, errors = fact_cli._load_all_of_type("adr", tmp_path)
    assert len(objects) == 2
    assert errors == []


def test_load_all_of_type_reports_parse_errors(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-good.yaml")
    bad_path = adrs_dir / "adr-0002-bad.yaml"
    bad_path.write_text("id: adr-0002\ntype: adr\nstatus: [broken\n", encoding="utf-8")

    objects, errors = fact_cli._load_all_of_type("adr", tmp_path)
    assert len(objects) == 1
    assert len(errors) == 1


def test_find_adr_by_id_returns_matching_adr(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml")
    write_adr(adrs_dir / "adr-0002-second.yaml", id="adr-0002")

    adrs, _ = fact_cli._load_all_of_type("adr", tmp_path)
    found = fact_cli._find_adr_by_id(adrs, "adr-0002")
    assert found["id"] == "adr-0002"


def test_find_adr_by_id_raises_on_missing(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml")

    adrs, _ = fact_cli._load_all_of_type("adr", tmp_path)
    with pytest.raises(SystemExit):
        fact_cli._find_adr_by_id(adrs, "adr-9999")


def test_build_adr_data_includes_gate_record():
    args = Args(**adr_content(), **auth_args())
    now = "2026-06-01T10:00:00"
    data = fact_cli._build_adr_data("adr-0001", args, now)
    assert data["id"] == "adr-0001"
    assert data["status"] == "proposed"
    assert "Human Gate 确认记录" in data["context"]
    assert data["decision"] == "测试决策"


# ── search 子命令 ──────────────────────────────────────────────────────


def test_search_matches_keyword(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", title="采用 pytest", decision="使用 pytest 框架")

    result = run_cli("search", "pytest", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "找到 1 个匹配的对象" in result.stdout
    assert "adr-0001" in result.stdout


def test_search_no_match(tmp_path):
    result = run_cli("search", "nonexistent-keyword", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "未找到" in result.stdout


def test_search_with_type_filter(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", title="采用 pytest")

    result = run_cli("search", "pytest", "--type", "adr", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "adr-0001" in result.stdout


# ── stats 子命令 ───────────────────────────────────────────────────────


def test_stats_shows_status_distribution(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="accepted")
    write_adr(adrs_dir / "adr-0002-second.yaml", id="adr-0002", status="proposed")

    result = run_cli("stats", "--type", "adr", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "adr 总数: 2" in result.stdout
    assert "accepted: 1" in result.stdout
    assert "proposed: 1" in result.stdout


def test_stats_empty_directory(tmp_path):
    result = run_cli("stats", "--type", "adr", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "adr 总数: 0" in result.stdout


# ── related 子命令 ─────────────────────────────────────────────────────


def test_related_matches_affects_and_related_rules(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", affects=["specs/12.01-Tools辅助规范.md"], related_rules=[])
    write_adr(adrs_dir / "adr-0002-second.yaml", id="adr-0002", title="第二个", affects=[], related_rules=["specs/21.06-Contract.md"])

    result = run_cli("related", "21.06", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "共 1 个" in result.stdout
    assert "adr-0002" in result.stdout
    assert "adr-0001" not in result.stdout


def test_related_no_match(tmp_path):
    result = run_cli("related", "nonexistent", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "未找到" in result.stdout


# ── link-rule 子命令 ───────────────────────────────────────────────────


def test_link_rule_appends_unique_rule(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", related_rules=[])

    result = run_cli(
        "link-rule", "adr-0001",
        "--rule", "specs/21-ADR-决策.md",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "已更新 related_rules" in result.stdout

    data = read_yaml(adrs_dir / "adr-0001-test.yaml")
    assert data["related_rules"] == ["specs/21-ADR-决策.md"]


def test_link_rule_rejects_without_human_gate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", related_rules=[])

    result = run_cli("link-rule", "adr-0001", "--rule", "specs/test.md", base_dir=str(tmp_path))
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_link_rule_no_change_when_duplicate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", related_rules=["specs/existing.md"])

    result = run_cli(
        "link-rule", "adr-0001",
        "--rule", "specs/existing.md",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "无变化" in result.stdout


# ── deprecate 子命令 ───────────────────────────────────────────────────


def test_deprecate_updates_status_and_reason(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="accepted", consequences="原影响")

    result = run_cli(
        "deprecate", "adr-0001",
        "--reason", "已不适用",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "已废弃 ADR" in result.stdout

    data = read_yaml(adrs_dir / "adr-0001-test.yaml")
    assert data["status"] == "deprecated"
    assert "废弃原因：已不适用" in data["consequences"]


def test_deprecate_rejects_without_human_gate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="accepted")

    result = run_cli("deprecate", "adr-0001", "--reason", "已不适用", base_dir=str(tmp_path))
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_deprecate_rejects_illegal_transition(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="rejected")

    result = run_cli(
        "deprecate", "adr-0001",
        "--reason", "已不适用",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode != 0
    assert "非法" in result.stderr


def test_deprecate_writes_reason_to_context(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="accepted", context="原背景")

    result = run_cli(
        "deprecate", "adr-0001",
        "--reason", "已不适用",
        "--reason-field", "context",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0

    data = read_yaml(adrs_dir / "adr-0001-test.yaml")
    assert data["status"] == "deprecated"
    assert "废弃原因：已不适用" in data["context"]


# ── supersede 子命令 ───────────────────────────────────────────────────


def test_supersede_creates_new_adr_and_updates_old(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-old.yaml", id="adr-0001", status="accepted", title="原 ADR")

    result = run_cli(
        "supersede",
        "--old-adr-id", "adr-0001",
        "--slug", "new-adr",
        "--title", "新 ADR",
        "--context", "新背景",
        "--decision", "新决策",
        "--consequences", "新影响",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "已创建替代 ADR" in result.stdout
    assert "已更新原 ADR" in result.stdout

    old_data = read_yaml(adrs_dir / "adr-0001-old.yaml")
    new_data = read_yaml(adrs_dir / "adr-0002-new-adr.yaml")
    assert old_data["status"] == "superseded"
    assert old_data["superseded_by"] == "adr-0002"
    assert new_data["status"] == "proposed"
    assert "adr-0001" in new_data["related_objects"]


def test_supersede_rejects_without_human_gate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-old.yaml", id="adr-0001", status="accepted")

    result = run_cli(
        "supersede",
        "--old-adr-id", "adr-0001",
        "--slug", "new-adr",
        "--title", "新 ADR",
        "--decision", "新决策",
        "--consequences", "新影响",
        base_dir=str(tmp_path),
    )
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_supersede_rejects_non_accepted_old_adr(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-old.yaml", id="adr-0001", status="proposed")

    result = run_cli(
        "supersede",
        "--old-adr-id", "adr-0001",
        "--slug", "new-adr",
        "--title", "新 ADR",
        "--decision", "新决策",
        "--consequences", "新影响",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode != 0
    assert "非法" in result.stderr


# ── ADR create Human Gate 强制检查 ─────────────────────────────────────


def test_create_adr_requires_human_gate(tmp_path):
    result = run_cli("create", "adr", "--title", "Test ADR", base_dir=str(tmp_path))
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_create_adr_with_human_gate_succeeds(tmp_path):
    result = run_cli(
        "create", "adr", "--title", "Test ADR",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) >= 1


# ── ADR transition Human Gate 强制检查 ─────────────────────────────────


def test_transition_adr_requires_human_gate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="proposed")

    result = run_cli("transition", str(adrs_dir / "adr-0001-test.yaml"), "--to", "accepted")
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_transition_adr_with_human_gate_succeeds(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="proposed")

    result = run_cli(
        "transition", str(adrs_dir / "adr-0001-test.yaml"),
        "--to", "accepted",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "proposed → accepted" in result.stdout


def test_transition_adr_rejects_illegal_status_change(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="proposed")

    result = run_cli(
        "transition", str(adrs_dir / "adr-0001-test.yaml"),
        "--to", "superseded",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
    )
    assert result.returncode != 0
    assert "不允许的流转" in result.stderr


def test_transition_adr_rejects_terminal_status_reopen(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="rejected")

    result = run_cli(
        "transition", str(adrs_dir / "adr-0001-test.yaml"),
        "--to", "accepted",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
    )
    assert result.returncode != 0
    assert "不允许的流转" in result.stderr or "终态" in result.stderr


# ── 测试辅助函数
