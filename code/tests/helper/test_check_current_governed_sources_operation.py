"""Contract tests for the explicit, one-shot ``ldvh check`` operation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from conftest import assert_common_response

from ldvh.helper.service import handle_request

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")

_VALID_SPARK = (
    "title: 测试火花\n"
    "intent: 验证显式检查\n"
    "status: open\n"
    "priority: P1\n"
    "summary: 测试摘要\n"
    "object_id: spark-0001\n"
    "fact_type_key: spark\n"
    "created_at: '2026-07-01T00:00:00+08:00'\n"
    "updated_at: '2026-07-01T00:00:00+08:00'\n"
)


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
                "product_description: Explicit check operation tests.",
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


def _write_fact(project: Path, content: str) -> None:
    target = project / "ldvh-base" / "sparks" / "spark-0001.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def test_complete_check_preserves_raw_subreports_and_excludes_business_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, project = _fixture(tmp_path)
    (project / "business.py").write_text("broken ordinary code is out of scope\n", encoding="utf-8")
    (project / "temporary.txt").write_text("not a fact\n", encoding="utf-8")
    _write_fact(project, _VALID_SPARK)
    monkeypatch.chdir(project)

    response = handle_request("call", "check-current-governed-sources", "").response

    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["result"]["status"] == "passed"
    assert set(response["result"]) == {"status", "rules", "facts"}
    for name in ("rules", "facts"):
        report = response["result"][name]
        assert set(report) == {
            "outcome",
            "result",
            "scope",
            "sources",
            "gaps",
            "verification",
            "diagnostics",
        }
        assert set(report["scope"]) == {"requested", "completed", "not_completed"}
    facts = response["result"]["facts"]
    assert facts["result"] == {"status": "complete", "object_count": 1, "problems": []}
    assert response["scope"]["requested"][0]["check_scope"] == "current_rule_source"
    assert response["scope"]["requested"][1] == {
        "check_scope": "complete_governed_fact_library",
        "locator": str(project),
        "source": "actual_cwd",
    }


def test_partial_fact_integrity_cannot_be_masked_as_a_passing_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, project = _fixture(tmp_path)
    _write_fact(project, "title: only title\n")
    monkeypatch.chdir(project)

    result = handle_request("call", "check-current-governed-sources", "")
    response = result.response

    assert result.exit_code == 3
    assert response["outcome"] == "partial"
    assert response["result"]["status"] == "not_passed"
    assert response["result"]["facts"]["outcome"] == "ok"
    assert response["result"]["facts"]["result"]["status"] == "partial"
    assert response["result"]["facts"]["result"]["problems"]
    assert any("没有返回 complete" in gap["summary"] for gap in response["gaps"])


def test_ungoverned_cwd_preserves_unavailable_fact_subreport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outsider = tmp_path / "outsider"
    outsider.mkdir()
    _git(outsider, "init", "-q")
    monkeypatch.chdir(outsider)

    result = handle_request("call", "check-current-governed-sources", "")
    response = result.response

    assert result.exit_code == 3
    assert response["outcome"] == "partial"
    assert response["result"]["status"] == "not_passed"
    facts = response["result"]["facts"]
    assert facts["outcome"] == "unavailable"
    assert facts["result"] is None
    assert facts["scope"]["not_completed"]
    assert facts["gaps"]


def test_extra_common_input_is_rejected_before_a_check_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, project = _fixture(tmp_path)
    monkeypatch.chdir(project)

    result = handle_request(
        "call",
        "check-current-governed-sources",
        json.dumps({"arguments": {"workspace_root": str(tmp_path)}}),
    )

    assert result.exit_code == 2
    assert result.response["outcome"] == "invalid_request"
    assert "不接受 arguments" in result.response["gaps"][0]["summary"]


def test_linked_worktree_is_the_fact_check_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace, project = _fixture(tmp_path)
    (project / "README.md").write_text("base\n", encoding="utf-8")
    _git(project, "add", ".")
    _git(project, "-c", "user.name=LDVH Test", "-c", "user.email=ldvh@example.invalid", "commit", "-qm", "base")
    linked = workspace / "linked"
    _git(project, "worktree", "add", "--detach", "-q", str(linked))
    for directory in ("sparks", "workcases", "adrs", "pitfalls", "studies"):
        (linked / "ldvh-base" / directory).mkdir(parents=True, exist_ok=True)
    _write_fact(linked, _VALID_SPARK)
    monkeypatch.chdir(linked)

    response = handle_request("call", "check-current-governed-sources", "").response

    assert response["outcome"] == "ok"
    assert response["result"]["facts"]["result"]["object_count"] == 1
    assert response["scope"]["requested"][1]["locator"] == str(linked)
