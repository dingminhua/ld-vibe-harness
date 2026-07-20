from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import HELPER_EXECUTABLE

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
WORKCASE_FIXTURE = REPOSITORY_ROOT / "code/tests/fixtures/context_recovery/workcase-0007.yaml"
PLUGIN_ROOT = REPOSITORY_ROOT / "code/plugins/ldvh"
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"
CONFIGURE = SCRIPTS_ROOT / "configure.py"
CODEX_CONTEXT = SCRIPTS_ROOT / "codex_context.py"


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(["product_name: Test", "product_description: Test workspace.", "projects: []", ""]),
        encoding="utf-8",
    )
    return workspace


def _governed_workspace(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "bounded-workspace"
    project = tmp_path / "bounded-project"
    workspace.mkdir()
    project.mkdir()
    subprocess.run(["git", "-C", str(project), "init", "-q"], check=True, capture_output=True)
    workcase = project / "ldvh-base/workcases/workcase-0007.yaml"
    workcase.parent.mkdir(parents=True)
    shutil.copyfile(WORKCASE_FIXTURE, workcase)
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test",
                "product_description: Test workspace.",
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


def _executable(tmp_path: Path, name: str, body: str) -> Path:
    script = tmp_path / f"{name}.py"
    script.write_text(body, encoding="utf-8")
    if sys.platform == "win32":
        executable = tmp_path / f"{name}.cmd"
        executable.write_text(f'@"{sys.executable}" -X utf8 "{script}" %*\r\n', encoding="utf-8")
    else:
        executable = tmp_path / name
        executable.write_text(f"#!{sys.executable}\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
        executable.chmod(0o755)
    return executable


def _core_runner(tmp_path: Path) -> Path:
    return _executable(
        tmp_path,
        "ldvh-context-recovery",
        "\n".join(
            [
                "import sys",
                f"sys.path.insert(0, {str(REPOSITORY_ROOT / 'code')!r})",
                "from ldvh.hooks.context_recovery import main",
                "raise SystemExit(main())",
            ]
        )
        + "\n",
    )


def _recording_runner(tmp_path: Path, response: Any, *, exit_code: int = 0) -> tuple[Path, Path]:
    records = tmp_path / "runner-records.jsonl"
    runner = _executable(
        tmp_path,
        "recording-runner",
        "\n".join(
            [
                "import json",
                "import sys",
                "from pathlib import Path",
                f"records = Path({str(records)!r})",
                "with records.open('a', encoding='utf-8') as stream:",
                "    stream.write(json.dumps({'argv': sys.argv[1:], 'cwd': str(Path.cwd())}) + '\\n')",
                f"print(json.dumps({response!r}, ensure_ascii=False))",
                f"raise SystemExit({exit_code})",
            ]
        )
        + "\n",
    )
    return runner, records


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


def _configuration_arguments(plugin_data: Path, helper: Path, runner: Path, workspace: Path) -> tuple[str, ...]:
    return (
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(helper),
        "--context-recovery-executable",
        str(runner),
        "--workspace-root",
        str(workspace),
    )


def _apply(plugin_data: Path, helper: Path, runner: Path, workspace: Path) -> dict[str, Any]:
    completed, response = _run_configure(
        "apply",
        *_configuration_arguments(plugin_data, helper, runner, workspace),
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
    source: str | None = "startup",
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    environment = os.environ.copy()
    environment.update({"PLUGIN_DATA": str(plugin_data), "PLUGIN_ROOT": str(PLUGIN_ROOT)})
    hook_input: dict[str, Any] = {"hook_event_name": event, "cwd": str(cwd)}
    if source is not None:
        hook_input["source"] = source
    if event == "SubagentStart":
        hook_input.update({"agent_id": "fixture-agent", "agent_type": "default"})
    completed = subprocess.run(
        [sys.executable, str(CODEX_CONTEXT)],
        input=json.dumps(hook_input),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        env=environment,
        check=False,
    )
    assert completed.stderr == ""
    return completed, json.loads(completed.stdout)


def _rendered_projection(context: str) -> dict[str, Any]:
    encoded = context.split("Bounded recovery projection: ", 1)[1].rsplit(
        ". Bindings are mechanical recovery state only", 1
    )[0]
    return json.loads(encoded)


def test_manifest_hooks_and_assets_form_the_supported_thin_codex_mapping() -> None:
    manifest = json.loads((PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    hooks = json.loads((PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))

    assert manifest["name"] == "ldvh"
    assert "hooks" not in manifest
    assert "skills" not in manifest
    assert manifest["interface"]["displayName"] == "LD Vibe Harness"
    assert manifest["interface"]["brandColor"] == "#1F6FEB"
    assert manifest["interface"]["composerIcon"] == "./assets/ldvh-plugin-icon-128.png"
    assert manifest["interface"]["logo"] == "./assets/ldvh-plugin-icon-512.png"
    for size in (128, 512):
        assert (PLUGIN_ROOT / f"assets/ldvh-plugin-icon-{size}.png").read_bytes() == (
            REPOSITORY_ROOT / f"icons/ldvh-plugin-icon-{size}.png"
        ).read_bytes()
    assert hooks == {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'python3 -X utf8 "${PLUGIN_ROOT}/scripts/codex_context.py"',
                            "commandWindows": 'py -3.12 -X utf8 "${PLUGIN_ROOT}\\scripts\\codex_context.py"',
                            "timeout": 60,
                            "statusMessage": "Restoring LDVH context",
                        }
                    ],
                }
            ],
            "SubagentStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'python3 -X utf8 "${PLUGIN_ROOT}/scripts/codex_context.py"',
                            "commandWindows": 'py -3.12 -X utf8 "${PLUGIN_ROOT}\\scripts\\codex_context.py"',
                            "timeout": 60,
                            "statusMessage": "Restoring LDVH context",
                        }
                    ]
                }
            ],
        }
    }


def test_plugin_subprocess_invocations_use_argv_without_a_shell() -> None:
    for path in (CONFIGURE, CODEX_CONTEXT):
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
    runner = _core_runner(tmp_path)
    arguments = _configuration_arguments(plugin_data, HELPER_EXECUTABLE, runner, workspace)

    planned, plan = _run_configure("plan", *arguments)
    rejected, rejection = _run_configure("apply", *arguments)

    assert planned.returncode == 0
    assert plan["planned_change"] == "create"
    assert plan["changes"] == []
    assert not plugin_data.exists()
    assert rejected.returncode == 2
    assert rejection["outcome"] == "invalid_request"
    assert not plugin_data.exists()


def test_apply_writes_v2_configuration_and_requires_explicit_replace(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    runner = _core_runner(tmp_path)

    applied = _apply(plugin_data, HELPER_EXECUTABLE, runner, workspace)
    checked, check = _run_configure("check", "--plugin-data", str(plugin_data))
    legacy = {
        "config_version": 1,
        "helper_executable": str(HELPER_EXECUTABLE),
        "workspace_root": str(workspace),
    }
    (plugin_data / "ldvh.json").write_text(json.dumps(legacy), encoding="utf-8")
    planned, plan = _run_configure(
        "plan",
        *_configuration_arguments(plugin_data, HELPER_EXECUTABLE, runner, workspace),
    )
    rejected, conflict = _run_configure(
        "apply",
        *_configuration_arguments(plugin_data, HELPER_EXECUTABLE, runner, workspace),
        "--confirm-write",
    )
    replaced, replacement_result = _run_configure(
        "apply",
        *_configuration_arguments(plugin_data, HELPER_EXECUTABLE, runner, workspace),
        "--confirm-write",
        "--replace",
    )

    assert applied["changes"] == [{"kind": "created", "path": str(plugin_data / "ldvh.json")}]
    assert checked.returncode == 0
    assert check["configuration"] == {
        "config_version": 2,
        "helper_executable": str(HELPER_EXECUTABLE.resolve()),
        "context_recovery_executable": str(runner.resolve()),
        "workspace_root": str(workspace.resolve()),
    }
    assert planned.returncode == 0
    assert plan["planned_change"] == "replace"
    assert plan["current"] == {
        "config_version": 1,
        "helper_executable": str(HELPER_EXECUTABLE.resolve()),
        "workspace_root": str(workspace.resolve()),
    }
    assert rejected.returncode == 2
    assert conflict["outcome"] == "conflict"
    assert replaced.returncode == 0
    assert replacement_result["changes"] == [{"kind": "replaced", "path": str(plugin_data / "ldvh.json")}]


def test_invalid_existing_configuration_is_not_treated_as_absent_or_overwritten(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir()
    config_path = plugin_data / "ldvh.json"
    original = '{"unknown_user_field": true}\n'
    config_path.write_text(original, encoding="utf-8")
    workspace = _workspace(tmp_path)
    runner = _core_runner(tmp_path)
    arguments = _configuration_arguments(plugin_data, HELPER_EXECUTABLE, runner, workspace)

    planned, plan = _run_configure("plan", *arguments)
    applied, apply = _run_configure("apply", *arguments, "--confirm-write", "--replace")

    assert planned.returncode == 2
    assert plan["outcome"] == "unavailable"
    assert "unknown fields" in plan["summary"]
    assert applied.returncode == 2
    assert apply["outcome"] == "unavailable"
    assert config_path.read_text(encoding="utf-8") == original


def test_broken_configuration_symlink_is_not_treated_as_absent_or_overwritten(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir()
    config_path = plugin_data / "ldvh.json"
    config_path.symlink_to(tmp_path / "missing-user-target")
    workspace = _workspace(tmp_path)
    runner = _core_runner(tmp_path)

    completed, response = _run_configure(
        "apply",
        *_configuration_arguments(plugin_data, HELPER_EXECUTABLE, runner, workspace),
        "--confirm-write",
        "--replace",
    )

    assert completed.returncode == 2
    assert response["outcome"] == "unavailable"
    assert config_path.is_symlink()


def test_static_verify_checks_the_configured_runner_without_claiming_a_real_trigger(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    helper = _executable(tmp_path, "helper", "raise SystemExit(0)\n")
    expected_projection = {"contract": "ldvh-context-recovery/1", "opaque_core_projection": "verified"}
    runner, _ = _recording_runner(tmp_path, expected_projection)
    _apply(plugin_data, helper, runner, workspace)

    completed, response = _run_configure("verify", "--plugin-data", str(plugin_data))

    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    assert response["context_recovery_runner_verified"] is True
    assert response["real_environment_trigger_verified"] is False
    assert response["context_recovery_projection"] == expected_projection


@pytest.mark.parametrize(
    ("event", "source", "native_trigger"),
    [
        ("SessionStart", "startup", "SessionStart/startup"),
        ("SessionStart", "resume", "SessionStart/resume"),
        ("SessionStart", "clear", "SessionStart/clear"),
        ("SessionStart", "compact", "SessionStart/compact"),
        ("SubagentStart", None, "SubagentStart"),
    ],
)
def test_codex_adapter_projects_native_events_to_the_configured_core_runner(
    tmp_path: Path,
    event: str,
    source: str | None,
    native_trigger: str,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _executable(tmp_path, "helper", "raise SystemExit(0)\n")
    expected_projection = {"contract": "ldvh-context-recovery/1", "opaque_core_projection": "preserved"}
    runner, records = _recording_runner(tmp_path, expected_projection)
    _apply(plugin_data, helper, runner, workspace)

    completed, response = _run_hook(plugin_data, project, event=event, source=source)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert response["hookSpecificOutput"]["hookEventName"] == event
    context = response["hookSpecificOutput"]["additionalContext"]
    assert f"mapped {native_trigger} to shared context recovery" in context
    assert _rendered_projection(context) == expected_projection
    assert records.read_text(encoding="utf-8").splitlines()
    record = json.loads(records.read_text(encoding="utf-8").splitlines()[0])
    assert record == {
        "argv": [
            "--helper-executable",
            str(helper.resolve()),
            "--workspace-root",
            str(workspace.resolve()),
            "--work-object-locator",
            str(project),
            "--helper-cwd",
            str(project),
        ],
        "cwd": str(project),
    }


def test_complete_additional_context_obeys_frozen_governed_and_workspace_byte_budgets(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace, project = _governed_workspace(tmp_path)
    runner = _core_runner(tmp_path)
    _apply(plugin_data, HELPER_EXECUTABLE, runner, workspace)

    governed_completed, governed_response = _run_hook(plugin_data, project)
    workspace_completed, workspace_response = _run_hook(plugin_data, workspace)

    assert governed_completed.returncode == workspace_completed.returncode == 0
    governed_context = governed_response["hookSpecificOutput"]["additionalContext"]
    workspace_context = workspace_response["hookSpecificOutput"]["additionalContext"]
    assert len(governed_context.encode("utf-8")) <= 13_915
    assert len(workspace_context.encode("utf-8")) <= 4_830
    governed_projection = _rendered_projection(governed_context)
    workspace_projection = _rendered_projection(workspace_context)
    assert governed_projection["project_binding"]["reason"] == "governed_single"
    assert governed_projection["delivery_coverage"]["status"] == "complete"
    assert workspace_projection["project_binding"]["reason"] == "sole_registered_project_candidate"
    assert workspace_projection["delivery_coverage"]["status"] == "incomplete"
    assert workspace_projection["project_binding"]["status"] == "bound"
    assert workspace_projection["workcase_binding"]["status"] == "unresolved"


@pytest.mark.parametrize(
    ("runner_output", "exit_code", "expected"),
    [
        ([], 1, "context_recovery_executable did not complete successfully"),
        ([], 0, "context_recovery_executable did not return ldvh-context-recovery/1"),
    ],
)
def test_adapter_keeps_runner_failure_or_empty_output_non_blocking_and_context_unresolved(
    tmp_path: Path,
    runner_output: Any,
    exit_code: int,
    expected: str,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _executable(tmp_path, "helper", "raise SystemExit(0)\n")
    runner, _ = _recording_runner(tmp_path, runner_output, exit_code=exit_code)
    _apply(plugin_data, helper, runner, workspace)

    completed, response = _run_hook(plugin_data, project)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert expected in response["systemMessage"]
    assert "LDVH context as unresolved" in response["hookSpecificOutput"]["additionalContext"]


def test_missing_configuration_is_an_explicit_non_blocking_gap(tmp_path: Path) -> None:
    cwd = tmp_path / "project"
    cwd.mkdir()

    completed, response = _run_hook(tmp_path / "missing-plugin-data", cwd)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert "configuration does not exist" in response["systemMessage"]
    assert "LDVH context as unresolved" in response["hookSpecificOutput"]["additionalContext"]


def test_utf8_native_paths_and_opaque_runner_output_are_preserved(tmp_path: Path) -> None:
    root = tmp_path / "含 空格"
    root.mkdir()
    plugin_data = root / "插件 数据"
    workspace = _workspace(root)
    project = root / "项目 甲"
    project.mkdir()
    helper = _executable(root, "helper", "raise SystemExit(0)\n")
    expected_projection = {"contract": "ldvh-context-recovery/1", "opaque_core_projection": "中文"}
    runner, records = _recording_runner(root, expected_projection)
    _apply(plugin_data, helper, runner, workspace)

    completed, response = _run_hook(plugin_data, project)

    assert completed.returncode == 0
    assert _rendered_projection(response["hookSpecificOutput"]["additionalContext"]) == expected_projection
    record = json.loads(records.read_text(encoding="utf-8").splitlines()[0])
    assert str(project) in record["argv"]
    assert str(workspace.resolve()) in record["argv"]


@pytest.mark.parametrize(
    ("event", "source", "expected"),
    [
        ("Stop", "startup", "hook_event_name must be SessionStart or SubagentStart"),
        ("SessionStart", "manual", "source must be startup, resume, clear, or compact"),
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
    assert "hookSpecificOutput" not in response


def test_relative_cwd_is_not_silently_reinterpreted(tmp_path: Path) -> None:
    completed, response = _run_hook(tmp_path / "plugin-data", Path("relative-project"))

    assert completed.returncode == 0
    assert response["continue"] is True
    assert "cwd must be a non-empty absolute path" in response["systemMessage"]
    assert "cwd must be a non-empty absolute path" in response["hookSpecificOutput"]["additionalContext"]
    assert "LDVH context as unresolved" in response["hookSpecificOutput"]["additionalContext"]
