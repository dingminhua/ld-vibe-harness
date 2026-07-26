from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from conftest import HELPER_EXECUTABLE

from ldvh import doctor


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _workspace(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Doctor Test",
                "product_description: Read-only diagnostics.",
                "projects:",
                "  - id: sample",
                f"    path: {project}",
                "    name: Sample",
                "    description: Doctor fixture.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workspace, project


def test_doctor_reports_ready_for_explicit_governed_project(tmp_path: Path) -> None:
    workspace, project = _workspace(tmp_path)

    result = doctor.run_doctor(
        workspace_root=str(workspace),
        work_object_locator=str(project),
        helper_executable=str(HELPER_EXECUTABLE.resolve()),
    )

    assert result["contract"] == "ldvh-doctor/1"
    assert result["status"] == "ready"
    assert result["distribution"] == {"name": "ld-vibe-harness", "version": "0.1.0"}
    assert result["helper"]["contract"] == "ldvh-helper-cli/2"
    assert result["helper"]["operation_count"] == 15
    assert result["configuration"]["config_status"] == "valid"
    assert result["configuration"]["scope_status"] == "governed_single"
    assert result["configuration"]["governed_project_id"] == "sample"
    assert {item["surface_key"] for item in result["integration_surfaces"]} == {
        "helper-cli",
        "work-context-core",
        "context-recovery",
        "git-commit-msg-gate",
        "git-hook-manager",
    }
    assert all(item["state"] == "available" for item in result["integration_surfaces"])
    assert "documentation" not in result
    assert all(item["status"] == "passed" for item in result["checks"])
    assert result["diagnostics"] == []


def test_doctor_ready_does_not_claim_environment_installation_or_triggering(tmp_path: Path) -> None:
    workspace, project = _workspace(tmp_path)

    result = doctor.run_doctor(
        workspace_root=str(workspace),
        work_object_locator=str(project),
        helper_executable=str(HELPER_EXECUTABLE.resolve()),
    )

    assert result["status"] == "ready"
    assert next(
        item for item in result["integration_surfaces"] if item["surface_key"] == "work-context-core"
    )["state"] == "available"
    assert (
        "static entry points do not prove installation into, automatic triggering by, "
        "or verification of an environment"
    ) in result["limitations"]
    assert not any("environment_trigger" in item["check"] for item in result["checks"])


def test_doctor_reports_attention_without_guessing_project_binding(tmp_path: Path) -> None:
    workspace, _ = _workspace(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()

    result = doctor.run_doctor(
        workspace_root=str(workspace),
        work_object_locator=str(outside),
        helper_executable=str(HELPER_EXECUTABLE.resolve()),
    )

    assert result["status"] == "attention"
    assert result["configuration"]["scope_status"] == "non_governed"
    assert result["configuration"]["governed_project_id"] is None
    assert next(item for item in result["checks"] if item["check"] == "governance")["status"] == "attention"
    assert all(
        "target AI development environment" in item or "automatic triggering" in item
        for item in result["limitations"]
    )


def test_doctor_never_reports_ready_for_non_ok_governance_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    responses = iter(
        (
            {"outcome": "ok", "result": {"operations": []}},
            {
                "outcome": "partial",
                "result": {
                    "config_status": "valid",
                    "scope_status": "governed_single",
                    "object_resolutions": [
                        {"status": "governed", "governed_project_id": "sample"},
                    ],
                },
            },
        )
    )
    monkeypatch.setattr(doctor, "_invoke_helper", lambda *args, **kwargs: next(responses))

    result = doctor.run_doctor(
        workspace_root=str(tmp_path),
        work_object_locator=str(tmp_path),
        helper_executable=str(HELPER_EXECUTABLE.resolve()),
    )

    assert result["status"] == "attention"
    assert result["configuration"]["helper_outcome"] == "partial"
    assert next(item for item in result["checks"] if item["check"] == "configuration")["status"] == "attention"
    assert next(item for item in result["checks"] if item["check"] == "governance")["status"] == "attention"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("workspace_root", "relative", "workspace_root must be an absolute"),
        ("work_object_locator", "", "work_object_locator must be a non-empty"),
        ("helper_executable", "relative", "helper_executable must be an absolute"),
    ),
)
def test_doctor_rejects_non_explicit_inputs(tmp_path: Path, field: str, value: str, message: str) -> None:
    arguments = {
        "workspace_root": str(tmp_path),
        "work_object_locator": str(tmp_path),
        "helper_executable": str(HELPER_EXECUTABLE.resolve()),
    }
    arguments[field] = value

    with pytest.raises(doctor.DoctorError, match=message):
        doctor.run_doctor(**arguments)


def test_doctor_cli_returns_contractual_unavailable_result(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            str(HELPER_EXECUTABLE.parent / "python"),
            "-m",
            "ldvh.doctor",
            "--workspace-root",
            str(tmp_path),
            "--work-object-locator",
            str(tmp_path),
            "--helper-executable",
            str(tmp_path / "missing-helper"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert completed.stderr == ""
    response = json.loads(completed.stdout)
    assert response["contract"] == "ldvh-doctor/1"
    assert response["status"] == "unavailable"
    assert "documentation" not in response
    assert response["diagnostics"][0]["exception_type"] == "DoctorError"
