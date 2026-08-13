"""Contract tests for the git-hooks-status public operation (specs 09 §5.9)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from conftest import PROJECT_ROOT

from ldvh.helper.service import handle_request

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")

PLATFORM = "claude-code"
SKILL_PATH = str(PROJECT_ROOT / "skill" / "SKILL.md")


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
                "product_description: git-hooks-status operation tests.",
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


def _call_operation(operation: str, payload: str):
    return handle_request("call", operation, payload)


def _valid_payload() -> str:
    return json.dumps(
        {
            "arguments": {"platform": PLATFORM, "skill_path": SKILL_PATH},
            "work_object_locators": [str(PROJECT_ROOT)],
        }
    )


def test_operation_is_discoverable_with_implementation() -> None:
    discovered = handle_request("capabilities", None, "")

    operations = discovered.response["result"]["operations"]
    entry = next(item for item in operations if item["operation_key"] == "git-hooks-status")
    assert entry["implementation"]["present"] is True
    assert entry["required_inputs"] == ["arguments.platform", "arguments.skill_path"]
    assert entry["optional_inputs"] == ["work_object_locators"]
    assert entry["effect"] == "read"
    source_paths = [source["locator"] for source in entry["sources"]]
    assert any("09-环境接入规范" in path for path in source_paths)


def test_valid_input_returns_contract_shape() -> None:
    """The real governed project has a deployed hook and skill copy; the
    operation must return the documented result closure."""
    result = _call_operation("git-hooks-status", _valid_payload())

    assert result.exit_code == 0
    response = result.response
    assert response["outcome"] == "ok"
    domain = response["result"]
    assert set(domain) == {"status", "worktree", "common_hooks_dir", "checks"}
    assert domain["status"] in {"aligned", "misaligned"}
    assert isinstance(domain["worktree"], str)
    assert isinstance(domain["common_hooks_dir"], str)
    assert len(domain["checks"]) == 5
    surfaces = {check["surface"] for check in domain["checks"]}
    assert surfaces == {"commit-msg", "prepare-commit-msg", "skill", "stop-gate", "worktrees"}
    for check in domain["checks"]:
        assert set(check) == {"surface", "aligned", "detail"}
        assert isinstance(check["aligned"], bool)
    commit_msg = next(check for check in domain["checks"] if check["surface"] == "commit-msg")
    assert set(commit_msg["detail"]) == {
        "aligned",
        "path",
        "state",
        "detail",
        "deployed_bundle_version",
        "expected_bundle_version",
    }
    assert commit_msg["detail"]["state"] in {
        "managed",
        "outdated",
        "absent",
        "conflict",
        "unavailable",
    }
    skill = next(check for check in domain["checks"] if check["surface"] == "skill")
    assert skill["detail"]["platform"] == PLATFORM
    assert skill["detail"]["target_skill_path"] == SKILL_PATH
    assert set(skill["detail"]) >= {
        "aligned",
        "platform",
        "target_skill_path",
        "target_version",
        "project_version",
    }
    assert response["changes"] == []


def test_missing_platform_is_invalid_request() -> None:
    payload = json.dumps({"arguments": {"skill_path": SKILL_PATH}})
    result = _call_operation("git-hooks-status", payload)

    assert result.exit_code != 0
    assert result.response["outcome"] == "invalid_request"


def test_missing_skill_path_is_invalid_request() -> None:
    payload = json.dumps({"arguments": {"platform": PLATFORM}})
    result = _call_operation("git-hooks-status", payload)

    assert result.exit_code != 0
    assert result.response["outcome"] == "invalid_request"


def test_relative_skill_path_is_invalid_request() -> None:
    payload = json.dumps({"arguments": {"platform": PLATFORM, "skill_path": "relative/SKILL.md"}})
    result = _call_operation("git-hooks-status", payload)

    assert result.exit_code != 0
    assert result.response["outcome"] == "invalid_request"


def test_locator_input_matches_explicit_input() -> None:
    result = _call_operation("git-hooks-status", _valid_payload())

    assert result.exit_code == 0
    assert result.response["outcome"] == "ok"
    assert result.response["result"]["status"] in {"aligned", "misaligned"}
    assert result.response["result"]["worktree"] == str(PROJECT_ROOT)


def test_rejects_task_input() -> None:
    payload = json.dumps({"arguments": {"platform": PLATFORM, "skill_path": SKILL_PATH}, "task": "任意任务"})
    result = _call_operation("git-hooks-status", payload)

    assert result.exit_code != 0
    assert result.response["outcome"] in {"invalid_request", "rejected"}


def test_ungoverned_locator_is_not_silently_successful(tmp_path: Path) -> None:
    """A worktree outside governance must not be reported as aligned."""
    outsider = tmp_path / "outsider"
    outsider.mkdir()
    _git(outsider, "init", "-q")
    payload = json.dumps(
        {"arguments": {"platform": PLATFORM, "skill_path": SKILL_PATH}, "work_object_locators": [str(outsider)]}
    )

    result = _call_operation("git-hooks-status", payload)

    assert result.response["outcome"] in {"unavailable", "rejected", "invalid_request"}
