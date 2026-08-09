"""End-to-end tests for the check-fact-integrity public operation (specs 05 §11.9-11.10)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ldvh.helper.service import handle_request

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")


_VALID_SPARK = (
    "title: 测试火花\n"
    "intent: 验证事实完整性一等化操作\n"
    "status: open\n"
    "priority: P1\n"
    "summary: 测试摘要\n"
    "object_id: spark-0001\n"
    "fact_type_key: spark\n"
    "created_at: '2026-07-01T00:00:00+08:00'\n"
    "updated_at: '2026-07-01T00:00:00+08:00'\n"
)


def _git(project: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
                "product_description: Fact integrity operation tests.",
                "projects:",
                "  - id: sample",
                f"    path: {project}",
                "    name: Sample",
                "    description: Test project.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for directory in ("sparks", "workcases", "adrs", "pitfalls", "studies"):
        (project / "ldvh-base" / directory).mkdir(parents=True)
    return workspace, project


def _write_fact(project: Path, content: str, path: str = "ldvh-base/sparks/spark-0001.yaml") -> None:
    target = project / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _payload(workspace: Path, project: Path) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {"workspace_root": str(workspace)},
        }
    )


def test_operation_is_discoverable_with_implementation() -> None:
    discovered = handle_request("capabilities", None, "")

    operations = discovered.response["result"]["operations"]
    entry = next(item for item in operations if item["operation_key"] == "check-fact-integrity")
    assert entry["implementation"]["present"] is True
    assert entry["required_inputs"] == ["work_object_locators"]
    assert entry["optional_inputs"] == ["arguments.workspace_root"]
    assert entry["effect"] == "read"
    source_paths = [source["locator"] for source in entry["sources"]]
    assert any("05-事实模型基础规范" in path for path in source_paths)


def test_complete_library_reports_complete_with_contract_shape(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _write_fact(project, _VALID_SPARK)

    result = handle_request("call", "check-fact-integrity", _payload(workspace, project))

    assert result.exit_code == 0
    assert result.response["outcome"] == "ok"
    domain = result.response["result"]
    assert set(domain) == {"status", "object_count", "problems"}
    assert domain["status"] == "complete"
    assert domain["object_count"] == 1
    assert domain["problems"] == []
    assert result.response["changes"] == []


def test_invalid_object_reports_partial_with_precise_problem(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _write_fact(project, "title: 只有标题\n")

    result = handle_request("call", "check-fact-integrity", _payload(workspace, project))

    assert result.exit_code == 0
    assert result.response["outcome"] == "ok"
    domain = result.response["result"]
    assert domain["status"] == "partial"
    assert domain["object_count"] == 1
    assert len(domain["problems"]) == 1
    problem = domain["problems"][0]
    assert set(problem) == {"fact_type_key", "canonical_path", "check_status", "issues"}
    assert problem["fact_type_key"] == "spark"
    assert problem["canonical_path"] == "ldvh-base/sparks/spark-0001.yaml"
    assert problem["check_status"] == "invalid"
    assert problem["issues"]
    for issue in problem["issues"]:
        assert set(issue) == {"category", "field_path", "summary"}
    assert any("缺少必填字段" in issue["summary"] for issue in problem["issues"])


def test_ungoverned_locator_is_unavailable_with_gaps(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    outsider = tmp_path / "outsider"
    outsider.mkdir()
    _git(outsider, "init", "-q")
    payload = json.dumps(
        {
            "work_object_locators": [str(outsider)],
            "arguments": {"workspace_root": str(workspace)},
        }
    )

    result = handle_request("call", "check-fact-integrity", payload)

    assert result.response["outcome"] == "unavailable"
    assert result.response["result"] is None
    assert result.response["gaps"]
    assert result.response["scope"]["not_completed"]


def test_missing_required_inputs_are_invalid_request(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    result = handle_request(
        "call",
        "check-fact-integrity",
        json.dumps({"work_object_locators": [], "arguments": {"workspace_root": str(workspace)}}),
    )

    assert result.response["outcome"] == "invalid_request"
    assert result.response["changes"] == []
