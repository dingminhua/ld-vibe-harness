from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.helper.service import handle_request

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")


def _git(cwd: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    target = project / "current.txt"
    target.write_text("current working tree\n", encoding="utf-8")
    config = workspace / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text(
        "\n".join(
            [
                "governance_instance_name: Test Workspace",
                "product_description: Test governed projects configuration.",
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
    return workspace, project, target


def _payload(workspace: Path, target: Path) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(target)],
            "arguments": {"workspace_root": str(workspace)},
        }
    )


def test_service_call_returns_the_source_defined_governance_result(tmp_path: Path) -> None:
    workspace, project, target = _fixture(tmp_path)

    result = handle_request("call", "resolve-governance-scope", _payload(workspace, target))
    response = result.response

    assert result.exit_code == 0
    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["scope"]["governance_resolution"] is None
    assert response["scope"]["requested"] == response["scope"]["completed"]
    assert response["scope"]["not_completed"] == []
    assert response["result"]["config_status"] == "valid"
    assert response["result"]["scope_status"] == "governed_single"
    assert response["result"]["registered_project_candidates"] == [
        {
            "governed_project_id": "sample",
            "registered_project_path": str(project.resolve()),
            "git_worktree_root": str(project.resolve()),
            "git_common_dir": _git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"),
            "source_refs": response["result"]["registered_project_candidates"][0]["source_refs"],
        }
    ]
    assert any(
        source["kind"] == "registered_project_git_identity"
        for source in response["result"]["registered_project_candidates"][0]["source_refs"]
    )
    item = response["result"]["object_resolutions"][0]
    assert item["status"] == "governed"
    assert item["governed_project_id"] == "sample"
    assert item["registered_project_path"] == str(project.resolve())
    assert item["git_worktree_root"] == str(project.resolve())
    assert item["governed_via"] == "path"
    assert any(source["kind"] == "registered_project_git_identity" for source in item["identity_evidence"])
    assert response["disclosure"] is None
    assert response["changes"] == []


def test_request_specific_capabilities_treats_domain_resolution_as_callable(tmp_path: Path) -> None:
    workspace, _, target = _fixture(tmp_path)

    result = handle_request("capabilities", "resolve-governance-scope", _payload(workspace, target))
    operation = result.response["result"]["operations"][0]

    assert result.exit_code == 0
    assert result.response["outcome"] == "ok"
    assert operation["availability"] == "available_for_request"
    assert operation["implementation"]["present"] is True
    assert operation["required_inputs"] == []
    assert operation["optional_inputs"] == ["work_object_locators", "arguments.workspace_root"]


def test_operation_rejects_object_locators_before_filesystem_resolution() -> None:
    result = handle_request(
        "call",
        "resolve-governance-scope",
        json.dumps({"work_object_locators": [{"path": "/not-supported"}]}),
    )

    assert result.exit_code == 2
    assert result.response["outcome"] == "invalid_request"
    assert "必须是非空路径 string" in result.response["gaps"][0]["summary"]


def test_real_cli_process_returns_one_clean_governance_response(tmp_path: Path) -> None:
    workspace, _, target = _fixture(tmp_path)

    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), "call", "resolve-governance-scope"],
        cwd=workspace,
        input=_payload(workspace, target),
        text=True,
        capture_output=True,
        check=False,
    )
    response: dict[str, Any] = json.loads(completed.stdout)

    assert completed.returncode == 0
    assert completed.stderr == ""
    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["result"]["object_resolutions"][0]["status"] == "governed"


def _missing_payload(project: Path) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project / "current.txt")],
            "arguments": {"workspace_root": str(project)},
        }
    )


def test_valid_config_follow_up_is_empty_default(tmp_path: Path) -> None:
    workspace, project, target = _fixture(tmp_path)

    result = handle_request("call", "resolve-governance-scope", _payload(workspace, target))
    response = result.response

    assert_common_response(response)
    assert response["result"]["config_status"] == "valid"
    follow_up = response["follow_up"]
    assert follow_up["summary"] == "当前响应没有能够由 Helper 明确的专属后续信息"
    assert follow_up["required_inputs"] == []
    assert follow_up["required_human_decisions"] == []
    assert follow_up["resume_conditions"] == []
    assert follow_up["suggested_operations"] == []


def test_missing_config_follow_up_provides_guidance(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    (project / "current.txt").write_text("current\n", encoding="utf-8")

    result = handle_request("call", "resolve-governance-scope", _missing_payload(project))
    response = result.response

    assert_common_response(response)
    assert response["result"]["config_status"] == "missing"
    assert response["result"]["scope_status"] == "scope_unknown"
    follow_up = response["follow_up"]
    assert "未找到管辖配置" in follow_up["summary"]
    assert follow_up["required_inputs"] == []
    assert len(follow_up["required_human_decisions"]) == 1
    assert "创建 LDVH-GOVERNED-PROJECTS.yaml" in follow_up["required_human_decisions"][0]["summary"]
    assert len(follow_up["resume_conditions"]) == 1
    assert len(follow_up["suggested_operations"]) == 1
    suggested = follow_up["suggested_operations"][0]
    assert suggested["operation_key"] == "read-action-template-content"
    assert "环境接入" in suggested["summary"]


def test_invalid_config_follow_up_provides_guidance(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    (project / "current.txt").write_text("current\n", encoding="utf-8")
    config = workspace / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("governance_instance_name: Only a name without projects key.\n", encoding="utf-8")

    payload = json.dumps(
        {
            "work_object_locators": [str(project / "current.txt")],
            "arguments": {"workspace_root": str(workspace)},
        }
    )
    result = handle_request("call", "resolve-governance-scope", payload)
    response = result.response

    assert_common_response(response)
    assert response["result"]["config_status"] == "invalid"
    follow_up = response["follow_up"]
    assert "格式或字段无效" in follow_up["summary"]
    assert follow_up["required_inputs"] == []
    assert len(follow_up["required_human_decisions"]) == 1
    assert len(follow_up["resume_conditions"]) == 1
    assert len(follow_up["suggested_operations"]) == 1
    assert follow_up["suggested_operations"][0]["operation_key"] == "read-action-template-content"


def test_conflict_config_follow_up_provides_guidance(tmp_path: Path) -> None:
    first_workspace = tmp_path / "first-workspace"
    second_workspace = tmp_path / "second-workspace"
    first = first_workspace / "first"
    second = second_workspace / "second"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    _git(first, "init", "-q")
    _git(second, "init", "-q")
    (first / "tracked.txt").write_text("first\n", encoding="utf-8")
    (second / "tracked.txt").write_text("second\n", encoding="utf-8")
    (first_workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "governance_instance_name: First",
                "product_description: First configuration.",
                "projects:",
                "  - id: first",
                f"    path: {first}",
                "    name: First",
                "    description: First project.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (second_workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "governance_instance_name: Second",
                "product_description: Second configuration.",
                "projects:",
                "  - id: second",
                f"    path: {second}",
                "    name: Second",
                "    description: Second project.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    payload = json.dumps(
        {
            "work_object_locators": [str(first / "tracked.txt"), str(second / "tracked.txt")],
        }
    )
    result = handle_request("call", "resolve-governance-scope", payload)
    response = result.response

    assert_common_response(response)
    assert response["result"]["config_status"] == "conflict"
    follow_up = response["follow_up"]
    assert "冲突" in follow_up["summary"]
    assert follow_up["required_inputs"] == []
    assert len(follow_up["required_human_decisions"]) == 1
    assert "选择或合并" in follow_up["required_human_decisions"][0]["summary"]
    assert len(follow_up["resume_conditions"]) == 1
    assert len(follow_up["suggested_operations"]) == 1
    assert follow_up["suggested_operations"][0]["operation_key"] == "read-action-template-content"
