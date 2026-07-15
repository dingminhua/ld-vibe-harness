from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.helper.service import handle_request


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
                "product_name: Test Workspace",
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
