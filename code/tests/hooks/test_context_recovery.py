from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import HELPER_EXECUTABLE

from ldvh.hooks import context_recovery

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _workspace(tmp_path: Path, *, governed: bool = True) -> Path:
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True, capture_output=True)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    projects = (
        [
            "projects:",
            "  - id: sample",
            f"    path: {tmp_path}",
            "    name: Sample",
            "    description: Test project.",
        ]
        if governed
        else ["projects: []"]
    )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(["product_name: Test", "product_description: Test workspace.", *projects, ""]),
        encoding="utf-8",
    )
    return workspace


def _raw_helper(tmp_path: Path, name: str, body: str) -> Path:
    script = tmp_path / f"{name}.py"
    script.write_text(body, encoding="utf-8")
    if sys.platform == "win32":
        helper = tmp_path / f"{name}.cmd"
        helper.write_text(f'@"{sys.executable}" -X utf8 "{script}" %*\r\n', encoding="utf-8")
    else:
        helper = tmp_path / name
        helper.write_text(f"#!{sys.executable}\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
        helper.chmod(0o755)
    return helper


def _recover(helper: Path, workspace: Path, locator: Path, helper_cwd: Path) -> tuple[dict[str, Any], ...]:
    return context_recovery.recover_context(
        helper_executable=str(helper),
        workspace_root=str(workspace),
        work_object_locator=str(locator),
        helper_cwd=str(helper_cwd),
    )


def _recorded_recovery(
    monkeypatch: pytest.MonkeyPatch,
    helper: Path,
    workspace: Path,
    locator: Path,
    helper_cwd: Path,
) -> tuple[tuple[dict[str, Any], ...], list[dict[str, Any]], list[subprocess.CompletedProcess[str]]]:
    actual_run = subprocess.run
    calls: list[dict[str, Any]] = []
    outputs: list[subprocess.CompletedProcess[str]] = []

    def record(*arguments: Any, **keywords: Any) -> subprocess.CompletedProcess[str]:
        calls.append(
            {
                "argv": list(arguments[0]),
                "cwd": str(keywords["cwd"]),
                "input": keywords["input"],
            }
        )
        completed = actual_run(*arguments, **keywords)
        outputs.append(completed)
        return completed

    monkeypatch.setattr(context_recovery.subprocess, "run", record)
    return _recover(helper, workspace, locator, helper_cwd), calls, outputs


def test_recovery_uses_explicit_locator_and_helper_cwd_and_preserves_exchanges(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    locator = project / "task.md"
    locator.write_text("task\n", encoding="utf-8")
    helper_cwd = tmp_path / "environment-cwd"
    helper_cwd.mkdir()

    exchanges, calls, outputs = _recorded_recovery(
        monkeypatch,
        HELPER_EXECUTABLE,
        workspace,
        locator,
        helper_cwd,
    )

    assert [call["argv"][1:] for call in calls] == [
        ["call", "resolve-governance-scope"],
        ["call", "find-fact-object-candidates"],
    ]
    assert [call["cwd"] for call in calls] == [str(helper_cwd), str(helper_cwd)]
    assert (
        exchanges[0]["request"]
        == json.loads(calls[0]["input"])
        == {
            "work_object_locators": [str(locator)],
            "arguments": {"workspace_root": str(workspace)},
            "response_profile": "compact",
        }
    )
    assert (
        exchanges[1]["request"]
        == json.loads(calls[1]["input"])
        == {
            "work_object_locators": [str(locator)],
            "arguments": {
                "workspace_root": str(workspace),
                "governed_project_id": "sample",
                "card_layer": "F1",
            },
            "response_profile": "compact",
        }
    )
    assert [exchange["exit_code"] for exchange in exchanges] == [output.returncode for output in outputs]
    assert [exchange["response"] for exchange in exchanges] == [json.loads(output.stdout) for output in outputs]


def test_recovery_does_not_call_f1_without_a_unique_governed_project(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path, governed=False)
    project = tmp_path / "project"
    project.mkdir()

    exchanges, calls, _ = _recorded_recovery(monkeypatch, HELPER_EXECUTABLE, workspace, project, project)

    assert [call["argv"][1:] for call in calls] == [["call", "resolve-governance-scope"]]
    assert len(exchanges) == 1
    assert exchanges[0]["response"]["result"]["scope_status"] == "non_governed"


def test_recovery_preserves_an_actual_partial_f1_response(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    sparks = tmp_path / "facts/sparks"
    sparks.mkdir(parents=True)
    (sparks / "spark-9999.yaml").write_text("not: [valid", encoding="utf-8")

    exchanges, _, outputs = _recorded_recovery(monkeypatch, HELPER_EXECUTABLE, workspace, project, project)

    assert len(exchanges) == 2
    assert exchanges[-1]["response"]["outcome"] == "partial"
    assert exchanges[-1]["response"] == json.loads(outputs[-1].stdout)


@pytest.mark.parametrize(
    ("name", "body", "error_type", "expected"),
    [
        ("invalid-utf8-helper", "import sys\nsys.stdout.buffer.write(b'\\xff')\n", UnicodeDecodeError, "decode"),
        (
            "stderr-only-helper",
            'import sys\nsys.stderr.write(\'{"outcome": "ok"}\\n\')\n',
            context_recovery.ContextRecoveryError,
            "did not return one JSON response",
        ),
        (
            "invalid-contract",
            "\n".join(
                [
                    "import json",
                    "import sys",
                    "print(json.dumps({",
                    "    'contract': 'ldvh-helper-cli/future',",
                    "    'request_kind': sys.argv[1],",
                    "    'operation_key': sys.argv[2],",
                    "    'outcome': 'ok',",
                    "}))",
                ]
            )
            + "\n",
            context_recovery.ContextRecoveryError,
            "response contract",
        ),
        (
            "invalid-exit",
            "\n".join(
                [
                    "import json",
                    "import sys",
                    "print(json.dumps({",
                    "    'contract': 'ldvh-helper-cli/2',",
                    "    'request_kind': sys.argv[1],",
                    "    'operation_key': sys.argv[2],",
                    "    'outcome': 'partial',",
                    "}))",
                ]
            )
            + "\n",
            context_recovery.ContextRecoveryError,
            "outcome and process exit code",
        ),
    ],
)
def test_recovery_rejects_unfaithful_helper_transport_or_identity(
    tmp_path: Path,
    name: str,
    body: str,
    error_type: type[Exception],
    expected: str,
) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(error_type) as captured:
        _recover(_raw_helper(tmp_path, name, body), workspace, project, project)

    assert expected in str(captured.value)


def test_recovery_propagates_helper_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()

    def timeout(*arguments: Any, **keywords: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(arguments[0], keywords["timeout"])

    monkeypatch.setattr(context_recovery.subprocess, "run", timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        _recover(HELPER_EXECUTABLE, workspace, project, project)


def test_runner_executes_the_packaged_core_from_a_decoy_cwd(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    decoy = tmp_path / "decoy-cwd"
    decoy.mkdir()
    environment = os.environ.copy()
    source_path = str(REPOSITORY_ROOT / "code")
    environment["PYTHONPATH"] = source_path + os.pathsep + environment.get("PYTHONPATH", "")

    completed = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "ldvh.hooks.context_recovery",
            "--helper-executable",
            str(HELPER_EXECUTABLE),
            "--workspace-root",
            str(workspace),
            "--work-object-locator",
            str(project),
            "--helper-cwd",
            str(decoy),
        ],
        cwd=decoy,
        input="",
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        env=environment,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    exchanges = json.loads(completed.stdout)
    assert [exchange["operation_key"] for exchange in exchanges] == [
        "resolve-governance-scope",
        "find-fact-object-candidates",
    ]
