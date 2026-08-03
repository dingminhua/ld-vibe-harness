from __future__ import annotations

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from conftest import assert_common_response

from ldvh.facts import file_asset_creation
from ldvh.filesystem import AtomicWriteResult
from ldvh.helper.service import handle_request


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
                "product_description: FileAsset controlled creation tests.",
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
    return workspace, project


def _prepare(workspace: Path, project: Path, source: Path) -> dict[str, object]:
    response = handle_request(
        "call",
        "prepare-file-asset-intake",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    "source_path": str(source),
                },
            }
        ),
    ).response
    assert_common_response(response)
    assert response["outcome"] == "ok"
    return response["result"]["intake_basis"]


def _create(
    workspace: Path,
    project: Path,
    basis: dict[str, object],
    *,
    signature: dict[str, str] | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    fact_object: dict[str, object] = {
        "title": "审计原始文件",
        "filename": Path(str(basis["source_path"])).name,
        "media_type": "text/markdown",
        "signature": signature or {"signer_type": "human"},
        "change_log": [
            {
                "signature": {
                    "signer_type": "ai-agent",
                    "agent_id": "test-agent",
                    "host_environment": "pytest",
                },
                "session_id": "file-asset-creation-test-session",
                "at": (datetime.now().astimezone() - timedelta(minutes=1)).isoformat(),
                "summary": "Created by the controlled FileAsset test fixture.",
            }
        ],
    }
    if extra:
        fact_object.update(extra)
    return handle_request(
        "call",
        "create-file-asset",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "intake_basis": basis,
                    "fact_object": fact_object,
                },
            }
        ),
    ).response


@pytest.mark.skipif(os.name != "posix", reason="directory creation requires POSIX durability")
def test_prepare_then_create_human_file_asset_roundtrips_exact_bytes(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "external-audit.md"
    payload = "# 外部审计\n\n客观存在的原始内容。\n".encode()
    source.write_bytes(payload)

    basis = _prepare(workspace, project, source)

    assert basis["candidate_object_id"] == "file-asset-0001"
    assert basis["source_size_bytes"] == len(payload)
    assert not (project / "ldvh-base/file-assets").exists()

    response = _create(workspace, project, basis)

    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["result"]["actual_ref"] == {
        "governed_project_id": "sample",
        "fact_type_key": "file-asset",
        "object_id": "file-asset-0001",
    }
    directory = project / "ldvh-base/file-assets/file-asset-0001"
    assert {path.name for path in directory.iterdir()} == {"file-asset.yaml", "payload"}
    assert (directory / "payload").read_bytes() == payload
    manifest = (directory / "file-asset.yaml").read_text(encoding="utf-8")
    assert str(source) not in manifest
    assert "signer_type: human" in manifest
    assert response["result"]["payload"]["current_bytes_confirmed"] is True
    assert source.read_bytes() == payload


@pytest.mark.skipif(os.name != "posix", reason="directory creation requires POSIX durability")
def test_ai_agent_signature_is_persisted_as_the_only_other_branch(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "agent-audit.md"
    source.write_text("AI 形成并提交的最终 bytes。\n", encoding="utf-8")
    basis = _prepare(workspace, project, source)

    response = _create(
        workspace,
        project,
        basis,
        signature={
            "signer_type": "ai-agent",
            "agent_id": "codex",
            "host_environment": "Codex Desktop",
        },
    )

    assert_common_response(response)
    assert response["outcome"] == "ok"
    signature = response["result"]["fact_object"]["signature"]
    assert signature == {
        "signer_type": "ai-agent",
        "agent_id": "codex",
        "host_environment": "Codex Desktop",
    }


def test_source_drift_after_prepare_is_rejected_before_allocation(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "drifting.md"
    source.write_text("before\n", encoding="utf-8")
    basis = _prepare(workspace, project, source)
    source.write_text("after\n", encoding="utf-8")

    response = _create(workspace, project, basis)

    assert_common_response(response)
    assert response["outcome"] == "rejected"
    assert "source_stale" in response["gaps"][0]["summary"]
    assert not (project / "ldvh-base/file-assets").exists()
    assert not (project / ".git/ldvh/fact-id-allocators").exists()


def test_source_identity_replacement_with_same_bytes_requires_prepare_again(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "replaced.md"
    payload = b"same bytes\n"
    source.write_bytes(payload)
    basis = _prepare(workspace, project, source)
    replacement = tmp_path / "replacement.md"
    replacement.write_bytes(payload)
    os.replace(replacement, source)

    response = _create(workspace, project, basis)

    assert_common_response(response)
    assert response["outcome"] == "rejected"
    assert "source_stale" in response["gaps"][0]["summary"]
    assert not (project / "ldvh-base/file-assets").exists()
    assert not (project / ".git/ldvh/fact-id-allocators").exists()


def test_prepare_rejects_payload_over_four_mib_without_writes(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "too-large.bin"
    source.write_bytes(b"x" * (4 * 1024 * 1024 + 1))

    response = handle_request(
        "call",
        "prepare-file-asset-intake",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    "source_path": str(source),
                },
            }
        ),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "unavailable"
    assert "4194304" in response["gaps"][0]["summary"]
    assert not (project / "ldvh-base").exists()


def test_create_rejects_unknown_fact_object_field_as_invalid_request(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "audit.md"
    source.write_text("audit\n", encoding="utf-8")
    basis = _prepare(workspace, project, source)

    response = _create(workspace, project, basis, extra={"source_path": str(source)})

    assert_common_response(response)
    assert response["outcome"] == "invalid_request"
    assert "未知字段" in response["gaps"][0]["summary"]
    assert not (project / "ldvh-base/file-assets").exists()


@pytest.mark.parametrize(
    "signature",
    [
        {"signer_type": "human", "agent_id": "must-not-appear"},
        {"signer_type": "ai-agent", "agent_id": "codex"},
        {"signer_type": "other"},
    ],
)
def test_signature_branch_shape_is_rejected_before_allocation(
    tmp_path: Path,
    signature: dict[str, str],
) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "audit.md"
    source.write_text("audit\n", encoding="utf-8")
    basis = _prepare(workspace, project, source)

    response = _create(workspace, project, basis, signature=signature)

    assert_common_response(response)
    assert response["outcome"] == "rejected"
    assert not (project / "ldvh-base/file-assets").exists()
    assert not (project / ".git/ldvh/fact-id-allocators").exists()


@pytest.mark.skipif(os.name != "posix", reason="directory creation requires POSIX durability")
def test_concurrent_creates_share_allocator_and_do_not_overwrite(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("first\n", encoding="utf-8")
    second.write_text("second\n", encoding="utf-8")
    first_basis = _prepare(workspace, project, first)
    second_basis = _prepare(workspace, project, second)
    assert first_basis["candidate_object_id"] == second_basis["candidate_object_id"] == "file-asset-0001"

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = tuple(
            executor.map(
                lambda item: _create(workspace, project, item),
                (first_basis, second_basis),
            )
        )

    assert {response["outcome"] for response in responses} == {"ok"}
    assert {
        response["result"]["actual_ref"]["object_id"]
        for response in responses
    } == {"file-asset-0001", "file-asset-0002"}
    assert (project / "ldvh-base/file-assets/file-asset-0001/payload").read_bytes() in {
        b"first\n",
        b"second\n",
    }
    assert (project / "ldvh-base/file-assets/file-asset-0002/payload").read_bytes() in {
        b"first\n",
        b"second\n",
    }


@pytest.mark.skipif(os.name != "posix", reason="directory creation requires POSIX durability")
def test_committed_directory_with_unknown_durability_is_not_reported_as_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "audit.md"
    source.write_text("audit\n", encoding="utf-8")
    basis = _prepare(workspace, project, source)
    real_create = file_asset_creation.atomic_create_directory_relative

    def create_without_confirmed_directory_durability(*args: object, **kwargs: object) -> AtomicWriteResult:
        created = real_create(*args, **kwargs)  # type: ignore[arg-type]
        assert created.outcome == "created" and created.namespace_state == "committed"
        return AtomicWriteResult("created", "committed", "unknown", created.cleanup)

    monkeypatch.setattr(
        file_asset_creation,
        "atomic_create_directory_relative",
        create_without_confirmed_directory_durability,
    )

    response = _create(workspace, project, basis)

    assert_common_response(response)
    assert response["outcome"] == "unavailable"
    assert response["result"]["target_namespace"]["create_state"] == "committed"
    assert response["result"]["target_namespace"]["durability"] == "unknown"
    assert response["result"]["residual"]["check_status"] == "mechanically_valid"
    assert response["result"]["residual"]["current_bytes_confirmed"] is True
