from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import assert_common_response

HELPER_EXECUTABLE = Path(sys.executable).with_name("ldvh")


def _run(cwd: Path, *arguments: str, stdin: str = "") -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), *arguments],
        cwd=cwd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )
    response = json.loads(completed.stdout)
    assert_common_response(response)
    assert completed.stderr == ""
    return completed, response


def test_general_discovery_accepts_zero_public_operations_from_outside_repository(tmp_path: Path) -> None:
    completed, response = _run(tmp_path, "capabilities")

    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    assert response["operation_key"] is None
    assert response["result"] == {"mode": "discovery", "operations": []}
    assert len(response["gaps"]) == 5
    assert all(gap["summary"].startswith("当前 Code 尚未自动证明：") for gap in response["gaps"])


@pytest.mark.parametrize("command", [("capabilities", "one", "extra"), ("call", "one", "extra")])
def test_recognized_command_with_extra_arguments_is_json_invalid_request(
    tmp_path: Path,
    command: tuple[str, str, str],
) -> None:
    completed, response = _run(tmp_path, *command)

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["operation_key"] == "one"


@pytest.mark.parametrize("command", [(), ("call",), ("unknown-entry",)])
def test_shape_without_fields_required_by_common_response_stays_process_usage_error(
    tmp_path: Path,
    command: tuple[str, ...],
) -> None:
    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), *command],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr.startswith("usage: ldvh ")


@pytest.mark.parametrize("command", [("capabilities", "unknown-operation"), ("call", "unknown-operation")])
def test_unknown_operation_is_invalid_request(tmp_path: Path, command: tuple[str, str]) -> None:
    completed, response = _run(tmp_path, *command)

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["operation_key"] == "unknown-operation"
    assert response["result"] is None


def test_invalid_json_is_a_machine_response(tmp_path: Path) -> None:
    completed, response = _run(tmp_path, "capabilities", stdin="not-json")

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["gaps"]


def test_invalid_utf8_is_a_machine_invalid_request(tmp_path: Path) -> None:
    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), "capabilities"],
        cwd=tmp_path,
        input=b"\xff",
        capture_output=True,
        check=False,
    )
    response = json.loads(completed.stdout.decode("utf-8"))
    assert_common_response(response)

    assert completed.returncode == 2
    assert completed.stderr == b""
    assert response["outcome"] == "invalid_request"
    assert response["gaps"][0]["summary"] == "标准输入必须是 UTF-8"
