from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPOSITORY_ROOT / "code/plugins/ldvh"
CONFIGURE = PLUGIN_ROOT / "scripts/configure.py"
SESSION_START = PLUGIN_ROOT / "scripts/session_start.py"


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "product_name: Test\nproduct_description: Test workspace.\nprojects: []\n",
        encoding="utf-8",
    )
    return workspace


def _helper(
    tmp_path: Path,
    *,
    outcome: str = "ok",
    exit_code: int = 0,
    contract: str = "ldvh-helper-cli/2",
    availability: str = "available_for_request",
) -> Path:
    stem = f"ldvh-{outcome}-{exit_code}"
    script = tmp_path / f"{stem}.py"
    script.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "import json",
                "import sys",
                "request = json.load(sys.stdin)",
                "request_kind = sys.argv[1]",
                "operation_key = sys.argv[2]",
                f"availability = {availability!r} if request_kind == 'capabilities' else None",
                "result = ({'operations': [{'operation_key': operation_key, "
                "'availability': availability}]} if availability else {})",
                f"response = {{'contract': {contract!r}, 'request_kind': request_kind, "
                f"'operation_key': operation_key, 'outcome': {outcome!r}, 'result': result, "
                "'arguments': sys.argv[1:], 'request': request}",
                "print(json.dumps(response, ensure_ascii=False, sort_keys=True))",
                f"raise SystemExit({exit_code})",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if sys.platform == "win32":
        helper = tmp_path / f"{stem}.cmd"
        helper.write_text(
            f'@"{sys.executable}" -X utf8 "{script}" %*\r\n',
            encoding="utf-8",
        )
    else:
        helper = tmp_path / stem
        helper.write_text(
            f"#!{sys.executable}\n" + script.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        helper.chmod(0o755)
    return helper


def _raw_helper(tmp_path: Path, name: str, body: str) -> Path:
    script = tmp_path / f"{name}.py"
    script.write_text(body, encoding="utf-8")
    if sys.platform == "win32":
        helper = tmp_path / f"{name}.cmd"
        helper.write_text(
            f'@"{sys.executable}" -X utf8 "{script}" %*\r\n',
            encoding="utf-8",
        )
    else:
        helper = tmp_path / name
        helper.write_text(
            f"#!{sys.executable}\n" + script.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        helper.chmod(0o755)
    return helper


def _run_configure(*arguments: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, str(CONFIGURE), *arguments],
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
    )
    assert completed.stderr == ""
    return completed, json.loads(completed.stdout)


def _apply(plugin_data: Path, helper: Path, workspace: Path) -> dict[str, Any]:
    completed, response = _run_configure(
        "apply",
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(helper),
        "--workspace-root",
        str(workspace),
        "--confirm-write",
    )
    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    return response


def _run_hook(
    plugin_data: Path,
    cwd: Path,
    *,
    event: str = "SessionStart",
    source: str = "startup",
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    environment = os.environ.copy()
    environment.update({"PLUGIN_DATA": str(plugin_data), "PLUGIN_ROOT": str(PLUGIN_ROOT)})
    completed = subprocess.run(
        [sys.executable, str(SESSION_START)],
        input=json.dumps({"hook_event_name": event, "source": source, "cwd": str(cwd)}),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        env=environment,
        check=False,
    )
    assert completed.stderr == ""
    return completed, json.loads(completed.stdout)


def test_manifest_and_hook_register_only_the_supported_session_start_scope() -> None:
    manifest = json.loads((PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    hooks = json.loads((PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))

    assert manifest["name"] == "ldvh"
    assert "hooks" not in manifest
    assert "skills" not in manifest
    assert hooks == {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'python3 -X utf8 "${PLUGIN_ROOT}/scripts/session_start.py"',
                            "commandWindows": ('py -3.12 -X utf8 "${PLUGIN_ROOT}\\scripts\\session_start.py"'),
                            "timeout": 30,
                            "statusMessage": "Loading LDVH governance context",
                        }
                    ],
                }
            ]
        }
    }


def test_adapter_helper_processes_use_argv_without_a_shell() -> None:
    for path in (CONFIGURE, SESSION_START):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run"
        ]
        assert len(calls) == 1
        assert isinstance(calls[0].args[0], ast.List)
        assert not any(
            keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
            for keyword in calls[0].keywords
        )


def test_plan_is_read_only_and_apply_requires_confirmation(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    helper = _helper(tmp_path)
    common = (
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(helper),
        "--workspace-root",
        str(workspace),
    )

    planned, plan = _run_configure("plan", *common)
    rejected, rejection = _run_configure("apply", *common)

    assert planned.returncode == 0
    assert plan["planned_change"] == "create"
    assert plan["changes"] == []
    assert not plugin_data.exists()
    assert rejected.returncode == 2
    assert rejection["outcome"] == "invalid_request"
    assert not plugin_data.exists()


def test_apply_writes_one_explicit_configuration_and_rereads_it(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    helper = _helper(tmp_path)

    applied = _apply(plugin_data, helper, workspace)
    checked, check = _run_configure("check", "--plugin-data", str(plugin_data))
    repeated, repeat = _run_configure(
        "apply",
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(helper),
        "--workspace-root",
        str(workspace),
        "--confirm-write",
    )

    assert applied["changes"] == [{"kind": "created", "path": str(plugin_data / "ldvh.json")}]
    assert checked.returncode == 0
    assert check["configuration"] == {
        "config_version": 1,
        "helper_executable": str(helper.resolve()),
        "workspace_root": str(workspace.resolve()),
    }
    assert repeated.returncode == 0
    assert repeat["outcome"] == "no_change"
    assert repeat["changes"] == []


def test_existing_different_configuration_requires_explicit_replace(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    original = _helper(tmp_path, outcome="original")
    replacement = _helper(tmp_path, outcome="replacement")
    _apply(plugin_data, original, workspace)

    rejected, response = _run_configure(
        "apply",
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(replacement),
        "--workspace-root",
        str(workspace),
        "--confirm-write",
    )

    assert rejected.returncode == 2
    assert response["outcome"] == "conflict"
    current = json.loads((plugin_data / "ldvh.json").read_text(encoding="utf-8"))
    assert current["helper_executable"] == str(original.resolve())


def test_invalid_existing_configuration_is_not_treated_as_absent_or_overwritten(
    tmp_path: Path,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir()
    config_path = plugin_data / "ldvh.json"
    original = '{"unknown_user_field": true}\n'
    config_path.write_text(original, encoding="utf-8")
    workspace = _workspace(tmp_path)
    helper = _helper(tmp_path)
    common = (
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(helper),
        "--workspace-root",
        str(workspace),
    )

    planned, plan = _run_configure("plan", *common)
    applied, apply = _run_configure("apply", *common, "--confirm-write", "--replace")

    assert planned.returncode == 2
    assert plan["outcome"] == "unavailable"
    assert "unknown fields" in plan["summary"]
    assert applied.returncode == 2
    assert apply["outcome"] == "unavailable"
    assert config_path.read_text(encoding="utf-8") == original


def test_broken_configuration_symlink_is_not_treated_as_absent_or_overwritten(
    tmp_path: Path,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir()
    config_path = plugin_data / "ldvh.json"
    config_path.symlink_to(tmp_path / "missing-user-target")
    workspace = _workspace(tmp_path)
    helper = _helper(tmp_path)

    completed, response = _run_configure(
        "apply",
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(helper),
        "--workspace-root",
        str(workspace),
        "--confirm-write",
        "--replace",
    )

    assert completed.returncode == 2
    assert response["outcome"] == "unavailable"
    assert config_path.is_symlink()


def test_static_verify_calls_helper_without_claiming_real_trigger(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    helper = _helper(tmp_path)
    _apply(plugin_data, helper, workspace)

    completed, response = _run_configure("verify", "--plugin-data", str(plugin_data))

    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    assert response["real_environment_trigger_verified"] is False
    assert response["helper_available_for_request"] is True
    assert response["helper_response"]["arguments"] == ["capabilities", "resolve-governance-scope"]
    assert response["helper_response"]["request"] == {
        "arguments": {"workspace_root": str(workspace.resolve())},
        "response_profile": "compact",
    }


def test_static_verify_rejects_helper_that_is_not_available_for_the_request(
    tmp_path: Path,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    helper = _helper(tmp_path, availability="unavailable_for_request")
    _apply(plugin_data, helper, workspace)

    completed, response = _run_configure("verify", "--plugin-data", str(plugin_data))

    assert completed.returncode == 2
    assert response["outcome"] == "unavailable"
    assert response["helper_available_for_request"] is False
    assert response["real_environment_trigger_verified"] is False


def test_utf8_transport_preserves_unicode_paths_and_helper_json(tmp_path: Path) -> None:
    root = tmp_path / "含 空格"
    root.mkdir()
    plugin_data = root / "插件 数据"
    workspace = _workspace(root)
    project = root / "项目 甲"
    project.mkdir()
    helper = _helper(root)
    _apply(plugin_data, helper, workspace)

    verified, verification = _run_configure("verify", "--plugin-data", str(plugin_data))
    completed, response = _run_hook(plugin_data, project)

    assert verified.returncode == 0
    assert verification["helper_response"]["request"] == {
        "arguments": {"workspace_root": str(workspace.resolve())},
        "response_profile": "compact",
    }
    assert completed.returncode == 0
    context = response["hookSpecificOutput"]["additionalContext"]
    assert str(project) in context
    assert str(workspace.resolve()) in context
    assert str(helper.resolve()) in context


def test_invalid_utf8_helper_output_is_an_explicit_gap(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _raw_helper(
        tmp_path,
        "invalid-utf8-helper",
        "import sys\nsys.stdout.buffer.write(b'\\xff')\n",
    )
    _apply(plugin_data, helper, workspace)

    verified, verification = _run_configure("verify", "--plugin-data", str(plugin_data))
    completed, response = _run_hook(plugin_data, project)

    assert verified.returncode == 2
    assert verification["outcome"] == "unavailable"
    assert "decode" in verification["summary"]
    assert completed.returncode == 0
    assert "decode" in response["systemMessage"]
    assert "governance scope as unresolved" in response["systemMessage"]


def test_stderr_is_not_reinterpreted_as_helper_json(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _raw_helper(
        tmp_path,
        "stderr-only-helper",
        'import sys\nsys.stderr.write(\'{"outcome": "ok"}\\n\')\n',
    )
    _apply(plugin_data, helper, workspace)

    verified, verification = _run_configure("verify", "--plugin-data", str(plugin_data))
    completed, response = _run_hook(plugin_data, project)

    assert verified.returncode == 2
    assert verification["summary"] == "Helper verification did not return JSON"
    assert completed.returncode == 0
    assert "Helper did not return one JSON response" in response["systemMessage"]
    assert "governance scope as unresolved" in response["systemMessage"]


def test_helper_timeout_is_an_explicit_non_blocking_gap(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _helper(tmp_path)
    _apply(plugin_data, helper, workspace)
    patch_dir = tmp_path / "timeout-patch"
    patch_dir.mkdir()
    (patch_dir / "sitecustomize.py").write_text(
        "import subprocess\n"
        "def timeout(*args, **kwargs):\n"
        "    raise subprocess.TimeoutExpired(args[0], kwargs.get('timeout'))\n"
        "subprocess.run = timeout\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment.update(
        {
            "PLUGIN_DATA": str(plugin_data),
            "PLUGIN_ROOT": str(PLUGIN_ROOT),
            "PYTHONPATH": str(patch_dir),
        }
    )

    completed = subprocess.run(
        [sys.executable, str(SESSION_START)],
        input=json.dumps({"hook_event_name": "SessionStart", "source": "startup", "cwd": str(project)}),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        env=environment,
        check=False,
    )
    response = json.loads(completed.stdout)

    assert completed.returncode == 0
    assert "timed out after 20 seconds" in response["systemMessage"]
    assert "governance scope as unresolved" in response["systemMessage"]


@pytest.mark.parametrize(("outcome", "exit_code"), [("ok", 0), ("partial", 3)])
def test_session_start_maps_actual_cwd_and_preserves_helper_result(
    tmp_path: Path,
    outcome: str,
    exit_code: int,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _helper(tmp_path, outcome=outcome, exit_code=exit_code)
    _apply(plugin_data, helper, workspace)

    completed, response = _run_hook(plugin_data, project)

    assert completed.returncode == 0
    assert response["continue"] is True
    context = response["hookSpecificOutput"]["additionalContext"]
    assert f"Helper executable: {helper.resolve()}" in context
    assert f"Helper exit code: {exit_code}" in context
    encoded_request = context.split("Adapter request: ", 1)[1].split(". Helper exit code:", 1)[0]
    assert json.loads(encoded_request) == {
        "work_object_locators": [str(project)],
        "arguments": {"workspace_root": str(workspace.resolve())},
        "response_profile": "compact",
    }
    encoded = context.split("Result: ", 1)[1]
    helper_response = json.loads(encoded)
    assert helper_response["outcome"] == outcome
    assert helper_response["arguments"] == ["call", "resolve-governance-scope"]
    assert helper_response["request"] == {
        "work_object_locators": [str(project)],
        "arguments": {"workspace_root": str(workspace.resolve())},
        "response_profile": "compact",
    }


@pytest.mark.parametrize(
    ("outcome", "exit_code", "contract", "expected"),
    [
        ("partial", 1, "ldvh-helper-cli/2", "outcome and process exit code"),
        ("ok", 0, "ldvh-helper-cli/future", "response contract"),
    ],
)
def test_inconsistent_or_unknown_helper_protocol_is_an_explicit_gap(
    tmp_path: Path,
    outcome: str,
    exit_code: int,
    contract: str,
    expected: str,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _helper(tmp_path, outcome=outcome, exit_code=exit_code, contract=contract)
    _apply(plugin_data, helper, workspace)

    completed, response = _run_hook(plugin_data, project)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert expected in response["systemMessage"]
    context = response["hookSpecificOutput"]["additionalContext"]
    assert expected in context
    assert "governance scope as unresolved" in context


def test_missing_configuration_is_an_explicit_non_blocking_gap(tmp_path: Path) -> None:
    cwd = tmp_path / "project"
    cwd.mkdir()

    completed, response = _run_hook(tmp_path / "missing-plugin-data", cwd)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert "configuration does not exist" in response["systemMessage"]
    context = response["hookSpecificOutput"]["additionalContext"]
    assert "configuration does not exist" in context
    assert "governance scope as unresolved" in context


def test_helper_removed_after_configuration_is_an_explicit_non_blocking_gap(
    tmp_path: Path,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _helper(tmp_path)
    _apply(plugin_data, helper, workspace)
    helper.unlink()

    completed, response = _run_hook(plugin_data, project)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert "helper_executable does not identify a current file" in response["systemMessage"]
    context = response["hookSpecificOutput"]["additionalContext"]
    assert "helper_executable does not identify a current file" in context
    assert "governance scope as unresolved" in context


@pytest.mark.parametrize(
    ("event", "source", "expected"),
    [
        ("Stop", "startup", "hook_event_name must be SessionStart"),
        ("SessionStart", "clear", "source must be startup or resume"),
    ],
)
def test_unsupported_hook_scope_is_not_silently_reinterpreted(
    tmp_path: Path,
    event: str,
    source: str,
    expected: str,
) -> None:
    cwd = tmp_path / "project"
    cwd.mkdir()

    completed, response = _run_hook(tmp_path / "plugin-data", cwd, event=event, source=source)

    assert completed.returncode == 0
    assert expected in response["systemMessage"]


def test_relative_cwd_is_not_silently_reinterpreted(tmp_path: Path) -> None:
    completed, response = _run_hook(tmp_path / "plugin-data", Path("relative-project"))

    assert completed.returncode == 0
    assert response["continue"] is True
    assert "cwd must be a non-empty absolute path" in response["systemMessage"]
    context = response["hookSpecificOutput"]["additionalContext"]
    assert "cwd must be a non-empty absolute path" in context
    assert "governance scope as unresolved" in context
