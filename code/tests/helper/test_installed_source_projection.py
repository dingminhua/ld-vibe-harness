from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ldvh.helper.operation_sources import inspect_operation_sources
from ldvh.helper.rule_source import RuleSourceResult
from ldvh.helper.service import handle_request
from ldvh.specs.repository import inspect_repository
from ldvh.specs.source import RuleSourceIdentity


def _references(value):
    results = []
    if isinstance(value, dict):
        if value.get("kind") in {"rule", "implementation"} and isinstance(value.get("locator"), str):
            results.append(value)
        for child in value.values():
            results.extend(_references(child))
    elif isinstance(value, list):
        for child in value:
            results.extend(_references(child))
    return results


def _installed_repository(current_specs_repository: Path, tmp_path: Path):
    working = inspect_repository(current_specs_repository)
    identity = RuleSourceIdentity(
        "installed_release_snapshot",
        distribution="ld-vibe-harness",
        version="0.1.0",
        snapshot_sha256="b" * 64,
    )
    return replace(working, repository_root=tmp_path / "_rule_snapshot", source_identity=identity)


def _assert_installed_references(response) -> None:
    references = _references(response)
    assert references
    for reference in references:
        assert reference["version"] == "0.1.0"
        details = reference["details"]
        assert details["distribution"] == "ld-vibe-harness"
        assert "git_worktree_root" not in details
        if reference["kind"] == "rule":
            assert details["rule_source_view"] == "installed_release_snapshot"
            assert details["snapshot_sha256"] == "b" * 64
        else:
            assert details["implementation_source_view"] == "installed_distribution"
            assert "snapshot_sha256" not in details
    serialized = json.dumps(response, ensure_ascii=False)
    assert "_rule_snapshot" not in serialized
    assert "working_tree_rule_set" not in serialized


def test_installed_capabilities_bind_every_internal_rule_and_implementation(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository = _installed_repository(current_specs_repository, tmp_path)
    operations = inspect_operation_sources(repository)
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: RuleSourceResult(repository, operations, None),
    )

    result = handle_request("capabilities", None, "")

    assert result.response["outcome"] == "ok"
    _assert_installed_references(result.response)


def test_installed_snapshot_prechecks_a_real_governed_index(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository = _installed_repository(current_specs_repository, tmp_path)
    operations = inspect_operation_sources(repository)
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: RuleSourceResult(repository, operations, None),
    )

    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    subprocess.run(["git", "-C", str(project), "init", "-q"], check=True, capture_output=True)
    (project / "change.txt").write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(project), "add", "change.txt"], check=True, capture_output=True)
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Installed Snapshot Test",
                "product_description: Installed precheck source identity.",
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
    payload = json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "message": "test: 验证安装快照预检",
            },
        }
    )

    result = handle_request("call", "precheck-git-commit", payload)

    assert result.response["outcome"] == "ok"
    assert result.response["result"]["mechanical_outcome"] == "passed"
    _assert_installed_references(result.response)


@pytest.mark.parametrize(
    ("operation_key", "raw_input"),
    [
        ("read-specification-candidates", ""),
        (
            "read-specification-content",
            json.dumps(
                {
                    "arguments": {
                        "selections": [
                            {
                                "responsibility_key": "ldvh-root",
                                "heading_path": None,
                            }
                        ]
                    },
                    "requested_disclosure": "L4",
                }
            ),
        ),
        ("read-action-template-candidates", ""),
        (
            "read-action-template-content",
            json.dumps({"arguments": {"template_keys": ["git-commit"]}}),
        ),
    ],
)
def test_installed_read_calls_project_internal_sources_without_physical_snapshot_paths(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
    operation_key: str,
    raw_input: str,
) -> None:
    repository = _installed_repository(current_specs_repository, tmp_path)
    operations = inspect_operation_sources(repository)
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: RuleSourceResult(repository, operations, None),
    )

    result = handle_request("call", operation_key, raw_input)

    assert result.response["outcome"] == "ok"
    _assert_installed_references(result.response)
