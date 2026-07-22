from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ldvh.facts import web_machine
from ldvh.facts.web_machine import MachineRequestError, MachineUnavailableError, handle_machine_request


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
                "product_description: V4 Web machine boundary.",
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


def _request(workspace: Path, project: Path, operation: str, arguments: dict[str, object]):
    return {
        "protocol_version": 1,
        "operation": operation,
        "scope": {
            "workspace_root": str(workspace),
            "worktree_locator": str(project),
            "expected_governed_project_id": "sample",
        },
        "arguments": arguments,
    }


def test_machine_create_list_and_detail_share_one_governed_boundary(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    empty = handle_machine_request(_request(workspace, project, "list-sparks", {}))
    created = handle_machine_request(
        _request(
            workspace,
            project,
            "create-spark",
            {"title": "Machine", "intent": "Verify the bridge", "description": "Closed bridge", "priority": "P1"},
        )
    )
    listed = handle_machine_request(_request(workspace, project, "list-sparks", {}))
    detail = handle_machine_request(_request(workspace, project, "read-spark", {"object_id": "spark-0001"}))

    assert empty["status"] == "complete"
    assert empty["result"]["items"] == []
    assert created["status"] == "created"
    assert created["result"]["actual_ref"]["object_id"] == "spark-0001"
    assert listed["status"] == "complete"
    assert listed["result"]["items"][0]["fact_object"]["title"] == "Machine"
    assert detail["status"] == "ok"
    assert detail["result"]["item"]["object_ref"]["object_id"] == "spark-0001"
    for response in (empty, created, listed, detail):
        assert set(response) == {
            "protocol_version",
            "operation",
            "status",
            "result",
            "error",
            "completion_unknown",
        }
        assert response["result"]["governance_resolution"]["scope_status"] == "governed_single"


def test_machine_rejects_identity_drift_and_unavailable_scope(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    drifted = _request(workspace, project, "list-sparks", {})
    drifted["scope"]["expected_governed_project_id"] = "other"

    with pytest.raises(MachineRequestError, match="identity"):
        handle_machine_request(drifted)
    with pytest.raises(MachineUnavailableError, match="complete governed"):
        handle_machine_request(_request(tmp_path / "missing", project, "list-sparks", {}))


def test_unexpected_create_failure_after_write_is_completion_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    real_capture = web_machine.create_web_spark_direct_capture

    def write_then_raise(*args, **kwargs):
        result = real_capture(*args, **kwargs)
        assert result.status == "created"
        raise RuntimeError("injected post-write failure")

    monkeypatch.setattr(web_machine, "create_web_spark_direct_capture", write_then_raise)
    raw = json.dumps(
        _request(
            workspace,
            project,
            "create-spark",
            {"title": "Unknown", "intent": "Exercise unknown completion", "description": "Write then fail", "priority": "P1"},
        ),
        separators=(",", ":"),
    ).encode("utf-8")

    response = json.loads(web_machine._process_request_bytes(raw))

    assert response["status"] == "error"
    assert response["completion_unknown"] is True
    assert (project / "ldvh-base/sparks/spark-0001.yaml").is_file()


def test_create_response_overflow_after_write_is_completion_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    monkeypatch.setattr(web_machine, "MAX_RESPONSE_BYTES", 1)
    raw = json.dumps(
        _request(
            workspace,
            project,
            "create-spark",
            {"title": "Overflow", "intent": "Exercise overflow handling", "description": "Write then exceed response", "priority": "P1"},
        ),
        separators=(",", ":"),
    ).encode("utf-8")

    response = json.loads(web_machine._process_request_bytes(raw))

    assert response["status"] == "error"
    assert response["result"] is None
    assert response["completion_unknown"] is True
    assert (project / "ldvh-base/sparks/spark-0001.yaml").is_file()


def test_response_encoding_failure_still_returns_one_closed_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    request = _request(workspace, project, "list-sparks", {})
    monkeypatch.setattr(
        web_machine,
        "handle_machine_request",
        lambda _request: web_machine._response("list-sparks", "complete", result={"not_json": {1}}),
    )

    encoded = web_machine._process_request_bytes(json.dumps(request, separators=(",", ":")).encode("utf-8"))
    response = json.loads(encoded)

    assert encoded.endswith(b"\n") and encoded.count(b"\n") == 1
    assert response["status"] == "error"
    assert response["completion_unknown"] is False
    assert response["error"] == "internal machine failure: TypeError"


@pytest.mark.parametrize(
    "payload",
    [
        {"protocol_version": 1, "operation": "unknown", "scope": {}, "arguments": {}},
        {"protocol_version": 2, "operation": "list-sparks", "scope": {}, "arguments": {}},
        {
            "protocol_version": 1,
            "operation": "list-sparks",
            "scope": {},
            "arguments": {},
            "extra": True,
        },
    ],
)
def test_machine_request_shape_is_closed(payload: dict[str, object]) -> None:
    with pytest.raises(MachineRequestError):
        handle_machine_request(payload)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (b"", "request is empty"),
        (b"{}\n", "framing whitespace"),
        (b"\xef\xbb\xbf{}", "BOM"),
        (b'{"protocol_version":1,"protocol_version":1}', "duplicate JSON key"),
        (b'{"protocol_version":NaN,"operation":"list-sparks","scope":{},"arguments":{}}', "non-finite"),
        (b"\xff", "unique UTF-8 JSON"),
    ],
)
def test_real_isolated_machine_always_returns_one_closed_error_line(raw: bytes, expected: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-m", "ldvh.facts.web_machine"],
        input=raw,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout.endswith(b"\n") and completed.stdout.count(b"\n") == 1
    response = json.loads(completed.stdout)
    assert set(response) == {
        "protocol_version",
        "operation",
        "status",
        "result",
        "error",
        "completion_unknown",
    }
    assert response["status"] == "invalid"
    assert expected in response["error"]
