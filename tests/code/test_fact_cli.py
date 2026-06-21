"""Tests for code/fact_cli.py current work objects."""

from __future__ import annotations

import json
import subprocess
import sys
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


def write_spark(path: Path, *, resolved_to: dict[str, str] | str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "id": "spark-0001",
        "type": "spark",
        "title": "Study Boundary",
        "status": "pending",
        "created": "2026-06-20T09:00:00",
        "updated": "2026-06-20T09:00:00",
        "description": "Discuss whether a Study can close a Spark.",
        "evolution": [],
        "source": "conversation",
        "source_detail": "test",
        "priority": "P2",
        "resolved_to": resolved_to,
        "resolved_at": "",
        "discard_reason": "",
        "related_workcases": [],
        "related_adrs": [],
        "related_studies": ["study-0001"],
        "related_docs": [],
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_create_workcase_uses_current_contract(tmp_path):
    result = run_cli("create", "workcase", "--title", "Current Plan", "--base-dir", str(tmp_path))

    assert result.returncode == 0, result.stderr
    path = Path(result.stdout.strip())
    data = read_yaml(path)
    assert data["id"] == "workcase-0001"
    assert data["type"] == "workcase"
    assert data["status"] == "subagents_plan_reviewing"
    assert "orchestration" in data
    assert isinstance(data["orchestration"]["plan_review"], dict)
    assert isinstance(data["orchestration"]["result_review"], dict)
    assert "review" not in data["orchestration"]
    assert data["plan_confirmed_at"] == ""
    assert data["verification_evidence"] == ""
    assert data["closure_evidence"] == ""
    assert data["closure_requested_at"] == ""
    assert data["closure_outcome"] == ""
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
    assert data["urls"] == []
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


def test_create_pitfall_defaults_to_active(tmp_path):
    result = run_cli("create", "pitfall", "--title", "Stable Pitfall", "--base-dir", str(tmp_path))

    assert result.returncode == 0, result.stderr
    path = Path(result.stdout.strip())
    data = read_yaml(path)
    assert data["id"] == "pitfall-0001"
    assert data["type"] == "pitfall"
    assert data["status"] == "active"
    assert "superseded_by" not in data


def write_adr(path: Path, *, status: str = "active", archive_reason: str = "", deprecated_reason: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "id": "adr-0001",
        "type": "adr",
        "title": "Current ADR",
        "status": status,
        "created": "2026-06-19T09:00:00",
        "updated": "2026-06-19T09:00:00",
        "date": "2026-06-19",
        "context": "Context.",
        "decision": "Decision.",
        "consequences": "Consequences.",
        "related_workcases": [],
        "related_adrs": [],
        "related_sparks": [],
        "related_rules": [],
        "archive_reason": archive_reason,
        "deprecated_reason": deprecated_reason,
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_create_adr_defaults_to_active_contract(tmp_path):
    result = run_cli(
        "create",
        "adr",
        "--title",
        "Current ADR",
        "--base-dir",
        str(tmp_path),
        *AUTH_ARGS,
    )

    assert result.returncode == 0, result.stderr
    data = read_yaml(Path(result.stdout.strip()))
    assert data["status"] == "active"
    assert data["date"]
    assert data["decision"] == "待补充。"
    assert data["related_workcases"] == []
    assert data["archive_reason"] == ""
    assert data["deprecated_reason"] == ""
    assert "related_objects" not in data
    assert "superseded_by" not in data
    assert "alternatives" not in data
    assert "affects" not in data
    validate = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "code" / "fact_validate.py"), str(tmp_path / "ldvh-base" / "adrs"), "--format", "text"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0, validate.stdout + validate.stderr


def test_adr_transition_requires_terminal_reasons(tmp_path):
    path = tmp_path / "ldvh-base" / "adrs" / "adr-0001-current-adr.yaml"
    write_adr(path)

    blocked_archive = run_cli("transition", str(path), "--to", "archived", *AUTH_ARGS)
    assert blocked_archive.returncode == 1
    assert "archive_reason" in blocked_archive.stderr

    data = read_yaml(path)
    data["archive_reason"] = "Decision absorbed into specs."
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    archived = run_cli("transition", str(path), "--to", "archived", *AUTH_ARGS)
    assert archived.returncode == 0, archived.stderr
    assert read_yaml(path)["status"] == "archived"

    write_adr(path)
    blocked_deprecated = run_cli("transition", str(path), "--to", "deprecated", *AUTH_ARGS)
    assert blocked_deprecated.returncode == 1
    assert "deprecated_reason" in blocked_deprecated.stderr


def test_adr_deprecate_sets_deprecated_reason_and_supersede_is_removed(tmp_path):
    path = tmp_path / "ldvh-base" / "adrs" / "adr-0001-current-adr.yaml"
    write_adr(path)

    supersede = run_cli("supersede", "--old-adr-id", "adr-0001", "--base-dir", str(tmp_path), *AUTH_ARGS)
    assert supersede.returncode == 1
    assert "取消 superseded" in supersede.stderr

    deprecated = run_cli("deprecate", "adr-0001", "--reason", "No longer applicable.", "--base-dir", str(tmp_path), *AUTH_ARGS)
    assert deprecated.returncode == 0, deprecated.stderr
    data = read_yaml(path)
    assert data["status"] == "deprecated"
    assert data["deprecated_reason"] == "No longer applicable."


def test_update_study_rejects_removed_fields(tmp_path):
    created = run_cli("create", "study", "--title", "Stable Study", "--base-dir", str(tmp_path))
    assert created.returncode == 0, created.stderr
    path = Path(created.stdout.strip())

    result = run_cli("update", str(path), "--set", "source=ai", *AUTH_ARGS)

    assert result.returncode == 1
    assert "已移除字段" in result.stderr
    data = read_study_frontmatter(path)
    assert "source" not in data


def test_update_rejects_global_related_changes_field(tmp_path):
    created = run_cli("create", "workcase", "--title", "Stable Plan", "--base-dir", str(tmp_path))
    assert created.returncode == 0, created.stderr
    path = Path(created.stdout.strip())

    result = run_cli("update", str(path), "--set", "related_changes=abc1234", *AUTH_ARGS)

    assert result.returncode == 1
    assert "已移除字段" in result.stderr
    data = read_yaml(path)
    assert "related_changes" not in data


def test_update_rejects_removed_area_relation_field(tmp_path):
    old_field = "related_" + "work" + "areas"
    old_ref = "work" + "area-0001"
    created = run_cli("create", "workcase", "--title", "Stable Plan", "--base-dir", str(tmp_path))
    assert created.returncode == 0, created.stderr
    path = Path(created.stdout.strip())

    result = run_cli("update", str(path), "--set", f"{old_field}={old_ref}", *AUTH_ARGS)

    assert result.returncode == 1
    assert "已移除字段" in result.stderr
    data = read_yaml(path)
    assert old_field not in data


def test_legacy_object_types_are_not_cli_choices(tmp_path):
    for object_type in ("taskplan", "task", "subtask", "work" + "area"):
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


def test_spark_transition_rejects_study_resolved_target(tmp_path):
    path = tmp_path / "ldvh-base" / "sparks" / "spark-0001-study-boundary.yaml"
    write_spark(path, resolved_to={"type": "study", "ref": "study-0001"})

    result = run_cli("transition", str(path), "--to", "resolved", *AUTH_ARGS)

    assert result.returncode == 1
    assert "Study 只能通过 related_studies 关联" in result.stderr
    data = read_yaml(path)
    assert data["status"] == "pending"
    assert data["resolved_at"] == ""


def test_create_spark_defaults_validate(tmp_path):
    result = run_cli("create", "spark", "--title", "Capture Followup", "--base-dir", str(tmp_path))

    assert result.returncode == 0, result.stderr
    path = Path(result.stdout.strip())
    data = read_yaml(path)
    assert data["type"] == "spark"
    assert data["description"] == "Capture Followup 的火花摘要。"
    validate = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "code" / "fact_validate.py"), str(path), "--format", "text"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0, validate.stdout + validate.stderr


def test_update_source_sparks_writes_list(tmp_path):
    spark_path = tmp_path / "ldvh-base" / "sparks" / "spark-0001-study-boundary.yaml"
    write_spark(spark_path)
    pitfall_path = tmp_path / "ldvh-base" / "pitfalls" / "pitfall-0001-transition-guard.yaml"
    write_pitfall(pitfall_path, verification=PITFALL_VERIFICATION)

    result = run_cli("update", str(pitfall_path), "--set", "source_sparks=spark-0001", *AUTH_ARGS)

    assert result.returncode == 0, result.stderr
    data = read_yaml(pitfall_path)
    assert data["source_sparks"] == ["spark-0001"]
    validate = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "code" / "fact_validate.py"), str(tmp_path / "ldvh-base"), "--format", "text"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0, validate.stdout + validate.stderr


def test_workcase_transition_requires_review_evidence(tmp_path):
    created = run_cli("create", "workcase", "--title", "Transition Plan", "--base-dir", str(tmp_path))
    assert created.returncode == 0, created.stderr
    path = Path(created.stdout.strip())
    data = read_yaml(path)
    data["status"] = "draft"
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
    data["verification_evidence"] = (
        "## 验证计划\n\n"
        "检查当前工作项是否满足 review_needed 前置验证。\n\n"
        "## 验证命令\n\n"
        "```bash\n"
        "python3 code/fact_validate.py ldvh-base/workcases\n"
        "```\n\n"
        "## 验证结果\n\n"
        "通过。\n\n"
        "## 结论\n\n"
        "验证证据满足关闭审查要求。"
    )
    data["closure_evidence"] = (
        "## 验证计划\n\n"
        "检查关闭审查材料是否齐备。\n\n"
        "## 验证命令\n\n"
        "人工检查成功标准、验证证据和执行项状态。\n\n"
        "## 验证结果\n\n"
        "关闭审查材料已整理。\n\n"
        "## 结论\n\n"
        "可提交关闭审查。"
    )
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    reviewed = run_cli("transition", str(path), "--to", "review_needed", *AUTH_ARGS)
    assert reviewed.returncode == 0, reviewed.stderr
    final = read_yaml(path)
    assert final["status"] == "review_needed"
    assert final["review_requested_at"]


def test_workcase_current_transition_chain_sets_gate_fields(tmp_path):
    created = run_cli("create", "workcase", "--title", "Current Transition Plan", "--base-dir", str(tmp_path))
    assert created.returncode == 0, created.stderr
    path = Path(created.stdout.strip())

    data = read_yaml(path)
    data["orchestration"]["plan_review"]["controller_resolution"] = {
        "resolved_at": "2026-06-20T10:00:00",
        "resolver": "test-controller",
        "source_review_item_ids": [],
        "accepted_findings": [],
        "rejected_findings": [],
        "required_changes_applied": [],
        "unresolved_items": [],
        "changed_fields": [],
        "revision_history_refs": [],
        "summary": "Plan review resolved.",
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    plan_confirming = run_cli("transition", str(path), "--to", "human_plan_confirming", *AUTH_ARGS)
    assert plan_confirming.returncode == 0, plan_confirming.stderr

    executing = run_cli("transition", str(path), "--to", "executing", *AUTH_ARGS)
    assert executing.returncode == 0, executing.stderr
    data = read_yaml(path)
    assert data["status"] == "executing"
    assert data["plan_confirmed_at"]
    assert data["orchestration"]["plan_review"]["human_confirmation"]["decision"] == "execute"

    data["orchestration"]["execution_items"][0]["status"] = "done"
    data["orchestration"]["execution_items"][0]["result_summary"] = "Done."
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    self_checking = run_cli("transition", str(path), "--to", "result_self_checking", *AUTH_ARGS)
    assert self_checking.returncode == 0, self_checking.stderr

    data = read_yaml(path)
    data["verification_evidence"] = (
        "## 验证计划\n\n"
        "检查当前 WorkCase 新状态链路。\n\n"
        "## 验证命令\n\n"
        "python3 code/fact_validate.py ldvh-base/workcases\n\n"
        "## 验证结果\n\n"
        "通过。\n\n"
        "## 结论\n\n"
        "可以进入结果复核。"
    )
    data["closure_evidence"] = (
        "## 验证计划\n\n"
        "检查关闭材料。\n\n"
        "## 验证命令\n\n"
        "人工检查测试夹具。\n\n"
        "## 验证结果\n\n"
        "关闭材料齐备。\n\n"
        "## 结论\n\n"
        "可以提交关闭确认。"
    )
    data["orchestration"]["result_review"]["controller_self_check"] = {
        "controller": "test-controller",
        "checked_at": "2026-06-20T10:30:00",
        "prompt_context": {
            "objective": "Check current transition fixture.",
            "input_refs": ["tests/code/test_fact_cli.py"],
        },
        "result": {
            "status": "pass",
            "summary": "Fixture can enter result review.",
            "key_findings": ["未发现范围内问题。"],
            "required_changes": [],
            "evidence_refs": ["tests/code/test_fact_cli.py"],
        },
        "attested_at": "2026-06-20T10:35:00",
        "attestation": {
            "signer": "test-controller",
            "statement": "Checked fixture evidence.",
        },
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    result_reviewing = run_cli("transition", str(path), "--to", "subagents_result_reviewing", *AUTH_ARGS)
    assert result_reviewing.returncode == 0, result_reviewing.stderr

    data = read_yaml(path)
    data["orchestration"]["result_review"]["controller_resolution"] = {
        "resolved_at": "2026-06-20T10:45:00",
        "resolver": "test-controller",
        "source_review_item_ids": [],
        "accepted_findings": [],
        "rejected_findings": [],
        "required_changes_applied": [],
        "unresolved_items": [],
        "changed_fields": [],
        "revision_history_refs": [],
        "summary": "Result review resolved.",
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    closure_confirming = run_cli("transition", str(path), "--to", "human_closure_confirming", *AUTH_ARGS)
    assert closure_confirming.returncode == 0, closure_confirming.stderr
    data = read_yaml(path)
    assert data["status"] == "human_closure_confirming"
    assert data["closure_requested_at"]

    data["closure_outcome"] = "completed"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    closed = run_cli("transition", str(path), "--to", "closed", *AUTH_ARGS)
    assert closed.returncode == 0, closed.stderr
    final = read_yaml(path)
    assert final["status"] == "closed"
    assert final["closed_at"]
    assert final["orchestration"]["result_review"]["human_closure_confirmation"]["decision"] == "close"


def test_workcase_current_backward_transition_requires_reason(tmp_path):
    created = run_cli("create", "workcase", "--title", "Backward Transition Plan", "--base-dir", str(tmp_path))
    assert created.returncode == 0, created.stderr
    path = Path(created.stdout.strip())

    data = read_yaml(path)
    data["orchestration"]["plan_review"]["controller_resolution"] = {
        "resolved_at": "2026-06-20T10:00:00",
        "resolver": "test-controller",
        "source_review_item_ids": [],
        "accepted_findings": [],
        "rejected_findings": [],
        "required_changes_applied": [],
        "unresolved_items": [],
        "changed_fields": [],
        "revision_history_refs": [],
        "summary": "Plan review resolved.",
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    plan_confirming = run_cli("transition", str(path), "--to", "human_plan_confirming", *AUTH_ARGS)
    assert plan_confirming.returncode == 0, plan_confirming.stderr

    blocked = run_cli("transition", str(path), "--to", "subagents_plan_reviewing", *AUTH_ARGS)
    assert blocked.returncode == 1
    assert "--reason" in blocked.stderr

    returned = run_cli(
        "transition",
        str(path),
        "--to",
        "subagents_plan_reviewing",
        "--reason",
        "Human requested plan revision.",
        *AUTH_ARGS,
    )
    assert returned.returncode == 0, returned.stderr
    final = read_yaml(path)
    assert final["status"] == "subagents_plan_reviewing"
    assert final["revision_history"][-1]["from_status"] == "human_plan_confirming"
    assert final["revision_history"][-1]["reason"] == "Human requested plan revision."


def write_pitfall(path: Path, *, status: str = "active", verification: str | None = None, archive_reason: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "id": "pitfall-0001",
        "type": "pitfall",
        "title": "Pitfall Transition Guard",
        "status": status,
        "created": "2026-06-19T09:00:00",
        "updated": "2026-06-19T09:00:00",
        "symptoms": "Symptom.",
        "trigger_conditions": "Trigger.",
        "root_cause": "Root cause.",
        "resolution": "Resolution.",
        "verification": verification if verification is not None else "",
        "avoidance": "Avoidance.",
        "applicability": "Applicability.",
        "tags": ["transition-guard"],
        "source_objects": [],
        "source_sparks": [],
        "related_adrs": [],
        "related_docs": [],
        "related_rules": [],
        "archive_reason": archive_reason,
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


PITFALL_VERIFICATION = (
    "## 验证计划\n\n"
    "检查 Pitfall 是否可激活。\n\n"
    "## 验证命令\n\n"
    "python3 code/fact_validate.py ldvh-base/pitfalls\n\n"
    "## 验证结果\n\n"
    "校验通过。\n\n"
    "## 结论\n\n"
    "经验可复用。"
)


def test_pitfall_transition_rejects_removed_superseded_status(tmp_path):
    path = tmp_path / "ldvh-base" / "pitfalls" / "pitfall-0001-transition-guard.yaml"
    write_pitfall(path, verification=PITFALL_VERIFICATION)

    blocked = run_cli("transition", str(path), "--to", "superseded", *AUTH_ARGS)
    assert blocked.returncode == 1
    assert "目标状态不合法" in blocked.stderr
    assert "superseded" in blocked.stderr

    data = read_yaml(path)
    assert data["status"] == "active"
    assert "superseded_by" not in data


def test_pitfall_transition_requires_archive_reason(tmp_path):
    path = tmp_path / "ldvh-base" / "pitfalls" / "pitfall-0001-transition-guard.yaml"
    write_pitfall(path, status="active", verification=PITFALL_VERIFICATION)

    blocked = run_cli("transition", str(path), "--to", "archived", *AUTH_ARGS)
    assert blocked.returncode == 1
    assert "archive_reason" in blocked.stderr

    data = read_yaml(path)
    data["archive_reason"] = "No longer useful."
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    archived = run_cli("transition", str(path), "--to", "archived", *AUTH_ARGS)
    assert archived.returncode == 0, archived.stderr
    assert read_yaml(path)["status"] == "archived"


def test_list_json_only_reports_current_objects(tmp_path):
    run_cli("create", "workcase", "--title", "Listed Plan", "--base-dir", str(tmp_path))

    result = run_cli("list", "workcase", "--base-dir", str(tmp_path), "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["summary"]["count"] == 1
    assert payload["data"]["items"][0]["type"] == "workcase"
