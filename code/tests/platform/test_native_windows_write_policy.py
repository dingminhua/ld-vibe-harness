from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from ldvh.filesystem import native_atomic_fact_writes_supported

pytestmark = [
    pytest.mark.native_windows,
    pytest.mark.skipif(sys.platform != "win32" or os.name != "nt", reason="requires native Windows"),
    pytest.mark.skipif(
        native_atomic_fact_writes_supported(),
        reason="the current fail-closed backend probe no longer applies",
    ),
]


def _cli(
    helper: Path, cwd: Path, command: str, operation: str | None, request: dict[str, Any] | None
) -> tuple[int, dict[str, Any]]:
    argv = [sys.executable, str(helper), command]
    if operation:
        argv.append(operation)
    payload = b"" if request is None else json.dumps(request, ensure_ascii=False).encode("utf-8")
    completed = subprocess.run(argv, cwd=cwd, input=payload, capture_output=True, check=False, timeout=30)
    assert completed.stderr == b""
    return completed.returncode, json.loads(completed.stdout.decode("utf-8"))


def _managed_project(root: Path) -> tuple[Path, Path]:
    workspace = root / "工作区 with spaces"
    project = workspace / "项目 one"
    project.mkdir(parents=True)
    initialized = subprocess.run(
        ["git", "init", "-q", str(project)], cwd=root, capture_output=True, check=False, timeout=30
    )
    assert initialized.returncode == 0, initialized.stderr.decode(errors="replace")
    (project / "observed.txt").write_text("native Windows observation\n", encoding="utf-8")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "governance_instance_name: Native Windows Matrix",
                "product_description: Disposable native verification workspace.",
                "projects:",
                "  - id: sample",
                f"    path: {project}",
                "    name: Sample",
                "    description: Disposable governed project.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workspace, project


def _request(workspace: Path, project: Path, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "work_object_locators": [str(project)],
        "arguments": {"workspace_root": str(workspace), **arguments},
    }


def _project_bytes(project: Path) -> dict[str, bytes]:
    return {
        path.relative_to(project).as_posix(): path.read_bytes()
        for path in project.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(project).parts
    }


def test_native_public_create_and_update_are_unavailable_without_side_effects(tmp_path: Path) -> None:
    assert native_atomic_fact_writes_supported() is False
    helper = Path.cwd() / "ldvh"
    workspace, project = _managed_project(tmp_path)
    prepare_request = _request(
        workspace,
        project,
        {"governed_project_id": "sample", "fact_type_key": "spark"},
    )
    exit_code, prepared = _cli(helper, project, "call", "prepare-fact-object-draft", prepare_request)
    assert exit_code == 0
    basis = prepared["result"]
    fact_object = {
        "title": "Native Windows fail-closed probe",
        "status": "open",
        "source_refs": [{"kind": "repository-path", "locator": "observed.txt"}],
        "summary": "No public Windows write is authorized by this probe.",
        "priority": "P2",
    }
    create_request = _request(
        workspace,
        project,
        {
            "draft_basis": {
                key: basis[key]
                for key in (
                    "governed_project_id",
                    "fact_type_key",
                    "candidate_object_id",
                    "schema_fingerprint",
                    "worktree_fingerprint",
                )
            },
            "fact_object": fact_object,
        },
    )
    update_request = _request(
        workspace,
        project,
        {
            "fact_ref": {
                "governed_project_id": "sample",
                "fact_type_key": "spark",
                "object_id": "spark-0001",
            },
            "expected_content_fingerprint": "0" * 64,
            "fact_object": fact_object,
        },
    )
    workcase_update_request = _request(
        workspace,
        project,
        {
            "fact_ref": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": "workcase-0001",
            },
            "expected_content_fingerprint": "0" * 64,
            "set": {"summary": "Must not be written"},
            "remove": [],
            "managed_records": {},
        },
    )
    before = _project_bytes(project)

    for operation, request in (
        ("create-fact-object", create_request),
        ("update-fact-object", update_request),
        ("update-workcase", workcase_update_request),
    ):
        for command in ("capabilities", "call"):
            exit_code, response = _cli(helper, project, command, operation, request)
            assert exit_code == 5
            assert response["outcome"] == "unavailable"
            assert "原生原子后端" in json.dumps(response, ensure_ascii=False)

    assert _project_bytes(project) == before
    assert not (project / "facts").exists()
    assert not (project / ".git/ldvh").exists()
