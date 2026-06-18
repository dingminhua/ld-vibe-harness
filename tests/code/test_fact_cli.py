"""Tests for code/fact_cli.py current work objects."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

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


def run_cli(*args: str):
    return subprocess.run(
        ["python3", str(SCRIPT_PATH), *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def read_study_frontmatter(path: Path):
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    end = content.index("\n---", 4)
    return yaml.safe_load(content[4:end])


def test_create_workplan_uses_current_contract(tmp_path):
    result = run_cli("create", "workplan", "--title", "Current Plan", "--base-dir", str(tmp_path))

    assert result.returncode == 0, result.stderr
    path = Path(result.stdout.strip())
    data = read_yaml(path)
    assert data["id"] == "workplan-0001"
    assert data["type"] == "workplan"
    assert data["status"] == "draft"
    assert "orchestration" in data
    assert data["verification_evidence"] == ""
    assert data["closure_evidence"] == ""
    assert "tasks" not in data
    assert "completion_evidence" not in data


def test_create_study_defaults_to_active(tmp_path):
    result = run_cli("create", "study", "--title", "Stable Study", "--base-dir", str(tmp_path))

    assert result.returncode == 0, result.stderr
    path = Path(result.stdout.strip())
    data = read_study_frontmatter(path)
    assert data["id"] == "study-0001"
    assert data["type"] == "study"
    assert data["status"] == "active"
    assert data["user_intent"] == ""
    assert data["summary"] == "Stable Study 的稳定研究报告。"
    assert data["related_refs"] == []
    assert "source" not in data
    assert "source_detail" not in data
    assert "source_docs" not in data
    content = path.read_text(encoding="utf-8")
    assert "研究报告草稿" not in content
    assert "summary: |" in content
    assert "## 研究问题" in content
    assert "## 输入与边界" in content
    assert "## 关键发现" in content
    assert "## 建议" in content
    assert "## 后续分流" in content


def test_update_study_rejects_removed_fields(tmp_path):
    created = run_cli("create", "study", "--title", "Stable Study", "--base-dir", str(tmp_path))
    assert created.returncode == 0, created.stderr
    path = Path(created.stdout.strip())

    result = run_cli("update", str(path), "--set", "source=ai", *AUTH_ARGS)

    assert result.returncode == 1
    assert "已移除字段" in result.stderr
    data = read_study_frontmatter(path)
    assert "source" not in data


def test_legacy_object_types_are_not_cli_choices(tmp_path):
    for object_type in ("taskplan", "task", "subtask"):
        result = run_cli("create", object_type, "--title", "Legacy", "--base-dir", str(tmp_path))
        assert result.returncode == 2
        assert "invalid choice" in result.stderr


def test_show_does_not_resolve_legacy_ids(tmp_path):
    legacy_dir = tmp_path / "ldvh-base" / "taskplans"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "taskplan-0001-old.yaml").write_text(
        yaml.safe_dump({"id": "taskplan-0001", "type": "taskplan", "status": "draft"}, allow_unicode=True),
        encoding="utf-8",
    )

    result = run_cli("show", "taskplan-0001", "--base-dir", str(tmp_path), "--format", "json")

    assert result.returncode == 1
    assert "找不到对象" in result.stderr


def test_workplan_transition_requires_review_evidence(tmp_path):
    created = run_cli("create", "workplan", "--title", "Transition Plan", "--base-dir", str(tmp_path))
    assert created.returncode == 0, created.stderr
    path = Path(created.stdout.strip())
    data = read_yaml(path)
    data["orchestration"]["execution_items"] = [
        {
            "id": "item-1",
            "title": "Implement",
            "role": "code",
            "mode": "single",
            "input_refs": ["code/fact_cli.py"],
            "expected_output": "Current contract checked.",
            "status": "done",
            "result_summary": "Done.",
            "evidence_refs": ["tests/code/test_fact_cli.py"],
            "blocking_reason": None,
        }
    ]
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    activated = run_cli("transition", str(path), "--to", "active", *AUTH_ARGS)
    assert activated.returncode == 0, activated.stderr

    blocked = run_cli("transition", str(path), "--to", "review_needed", *AUTH_ARGS)
    assert blocked.returncode == 1
    assert "verification_evidence" in blocked.stderr

    data = read_yaml(path)
    data["verification_evidence"] = "## 验证结果\n\n通过。"
    data["closure_evidence"] = "## 结论\n\n可提交关闭审查。"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    reviewed = run_cli("transition", str(path), "--to", "review_needed", *AUTH_ARGS)
    assert reviewed.returncode == 0, reviewed.stderr
    final = read_yaml(path)
    assert final["status"] == "review_needed"
    assert final["review_requested_at"]


def test_list_json_only_reports_current_objects(tmp_path):
    run_cli("create", "workplan", "--title", "Listed Plan", "--base-dir", str(tmp_path))

    result = run_cli("list", "workplan", "--base-dir", str(tmp_path), "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["summary"]["count"] == 1
    assert payload["data"]["items"][0]["type"] == "workplan"
