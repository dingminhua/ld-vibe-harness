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
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"
CONFIGURE = SCRIPTS_ROOT / "configure.py"
CODEX_CONTEXT = SCRIPTS_ROOT / "codex_context.py"
CONTEXT_RECOVERY = SCRIPTS_ROOT / "context_recovery.py"

sys.path.insert(0, str(SCRIPTS_ROOT))
import context_recovery  # noqa: E402

ACTUAL_HELPER = Path(sys.executable).with_name("ldvh.exe" if sys.platform == "win32" else "ldvh")


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


def _recording_helper(tmp_path: Path) -> tuple[Path, Path]:
    records = tmp_path / "actual-helper-records.jsonl"
    helper = _raw_helper(
        tmp_path,
        "recording-helper",
        "\n".join(
            [
                "import json",
                "import subprocess",
                "import sys",
                "from pathlib import Path",
                f"helper = {str(ACTUAL_HELPER)!r}",
                f"records = Path({str(records)!r})",
                "request = sys.stdin.read()",
                "completed = subprocess.run(",
                "    [helper, *sys.argv[1:]],",
                "    input=request,",
                "    text=True,",
                "    encoding='utf-8',",
                "    errors='strict',",
                "    capture_output=True,",
                "    check=False,",
                ")",
                "with records.open('a', encoding='utf-8') as stream:",
                "    stream.write(json.dumps({",
                "        'request': request,",
                "        'exit_code': completed.returncode,",
                "        'stdout': completed.stdout,",
                "    }, ensure_ascii=False) + '\\n')",
                "sys.stdout.write(completed.stdout)",
                "sys.stderr.write(completed.stderr)",
                "raise SystemExit(completed.returncode)",
            ]
        )
        + "\n",
    )
    return helper, records


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


def _recover(helper: Path, workspace: Path, cwd: Path) -> tuple[dict[str, Any], ...]:
    return context_recovery.recover_context(
        helper_executable=str(helper.resolve()),
        workspace_root=str(workspace.resolve()),
        cwd=str(cwd),
    )


def _recorded_recovery(
    monkeypatch: pytest.MonkeyPatch,
    helper: Path,
    workspace: Path,
    cwd: Path,
) -> tuple[tuple[dict[str, Any], ...], list[tuple[list[str], str]], list[subprocess.CompletedProcess[str]]]:
    actual_run = subprocess.run
    calls: list[tuple[list[str], str]] = []
    outputs: list[subprocess.CompletedProcess[str]] = []

    def record(*arguments: Any, **keywords: Any) -> subprocess.CompletedProcess[str]:
        calls.append((list(arguments[0]), keywords["input"]))
        completed = actual_run(*arguments, **keywords)
        outputs.append(completed)
        return completed

    monkeypatch.setattr(context_recovery.subprocess, "run", record)
    return _recover(helper, workspace, cwd), calls, outputs


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


def test_adapter_helper_processes_use_argv_without_a_shell() -> None:
    for path in (CONFIGURE, CONTEXT_RECOVERY):
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
    common = (
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(ACTUAL_HELPER),
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

    applied = _apply(plugin_data, ACTUAL_HELPER, workspace)
    checked, check = _run_configure("check", "--plugin-data", str(plugin_data))
    repeated, repeat = _run_configure(
        "apply",
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(ACTUAL_HELPER),
        "--workspace-root",
        str(workspace),
        "--confirm-write",
    )

    assert applied["changes"] == [{"kind": "created", "path": str(plugin_data / "ldvh.json")}]
    assert checked.returncode == 0
    assert check["configuration"] == {
        "config_version": 1,
        "helper_executable": str(ACTUAL_HELPER.resolve()),
        "workspace_root": str(workspace.resolve()),
    }
    assert repeated.returncode == 0
    assert repeat["outcome"] == "no_change"
    assert repeat["changes"] == []


def test_existing_different_configuration_requires_explicit_replace(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    original = _raw_helper(tmp_path, "original", "raise SystemExit(0)\n")
    replacement = _raw_helper(tmp_path, "replacement", "raise SystemExit(0)\n")
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
    assert json.loads((plugin_data / "ldvh.json").read_text(encoding="utf-8"))["helper_executable"] == str(
        original.resolve()
    )


def test_invalid_existing_configuration_is_not_treated_as_absent_or_overwritten(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir()
    config_path = plugin_data / "ldvh.json"
    original = '{"unknown_user_field": true}\n'
    config_path.write_text(original, encoding="utf-8")
    workspace = _workspace(tmp_path)
    common = (
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(ACTUAL_HELPER),
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


def test_broken_configuration_symlink_is_not_treated_as_absent_or_overwritten(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir()
    config_path = plugin_data / "ldvh.json"
    config_path.symlink_to(tmp_path / "missing-user-target")
    workspace = _workspace(tmp_path)

    completed, response = _run_configure(
        "apply",
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(ACTUAL_HELPER),
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
    _apply(plugin_data, ACTUAL_HELPER, workspace)

    completed, response = _run_configure("verify", "--plugin-data", str(plugin_data))

    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    assert response["real_environment_trigger_verified"] is False
    assert response["helper_available_for_request"] is True
    assert response["helper_response"]["operation_key"] == "resolve-governance-scope"


def test_utf8_transport_preserves_unicode_paths_and_helper_json(tmp_path: Path) -> None:
    root = tmp_path / "含 空格"
    root.mkdir()
    plugin_data = root / "插件 数据"
    workspace = _workspace(root)
    project = root / "项目 甲"
    project.mkdir()
    _apply(plugin_data, ACTUAL_HELPER, workspace)

    verified, verification = _run_configure("verify", "--plugin-data", str(plugin_data))
    completed, response = _run_hook(plugin_data, project)

    assert verified.returncode == 0
    assert verification["helper_response"]["operation_key"] == "resolve-governance-scope"
    assert completed.returncode == 0
    context = response["hookSpecificOutput"]["additionalContext"]
    assert str(project) in context
    assert str(workspace.resolve()) in context
    assert str(ACTUAL_HELPER.resolve()) in context


@pytest.mark.parametrize(
    ("name", "body", "error_type", "expected"),
    [
        ("invalid-utf8-helper", "import sys\nsys.stdout.buffer.write(b'\\xff')\n", UnicodeDecodeError, "decode"),
        (
            "stderr-only-helper",
            'import sys\nsys.stderr.write(\'{"outcome": "ok"}\\n\')\n',
            ValueError,
            "Helper did not return one JSON response",
        ),
    ],
)
def test_shared_recovery_rejects_non_json_stdout_transport(
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
        _recover(_raw_helper(tmp_path, name, body), workspace, project)

    assert expected in str(captured.value)


def test_shared_recovery_propagates_helper_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()

    def timeout(*arguments: Any, **keywords: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(arguments[0], keywords["timeout"])

    monkeypatch.setattr(context_recovery.subprocess, "run", timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        _recover(ACTUAL_HELPER, workspace, project)


def test_shared_recovery_calls_governance_then_f1_and_preserves_raw_exchanges(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()

    exchanges, calls, outputs = _recorded_recovery(monkeypatch, ACTUAL_HELPER, workspace, project)

    assert [command[1:] for command, _ in calls] == [
        ["call", "resolve-governance-scope"],
        ["call", "find-fact-object-candidates"],
    ]
    assert (
        exchanges[0]["request"]
        == json.loads(calls[0][1])
        == {
            "work_object_locators": [str(project)],
            "arguments": {"workspace_root": str(workspace.resolve())},
            "response_profile": "compact",
        }
    )
    assert (
        exchanges[1]["request"]
        == json.loads(calls[1][1])
        == {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace.resolve()),
                "governed_project_id": "sample",
                "card_layer": "F1",
            },
            "response_profile": "compact",
        }
    )
    assert [exchange["exit_code"] for exchange in exchanges] == [output.returncode for output in outputs]
    assert [exchange["response"] for exchange in exchanges] == [json.loads(output.stdout) for output in outputs]


def test_shared_recovery_does_not_call_f1_for_a_real_non_governed_scope(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path, governed=False)
    project = tmp_path / "project"
    project.mkdir()

    exchanges, calls, _ = _recorded_recovery(monkeypatch, ACTUAL_HELPER, workspace, project)

    assert [command[1:] for command, _ in calls] == [["call", "resolve-governance-scope"]]
    assert len(exchanges) == 1
    assert exchanges[0]["response"]["result"]["scope_status"] == "non_governed"


def test_shared_recovery_preserves_an_actual_partial_f1_response(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    sparks = tmp_path / "facts/sparks"
    sparks.mkdir(parents=True)
    (sparks / "spark-9999.yaml").write_text("not: [valid", encoding="utf-8")

    exchanges, _, outputs = _recorded_recovery(monkeypatch, ACTUAL_HELPER, workspace, project)

    assert len(exchanges) == 2
    assert exchanges[-1]["response"]["outcome"] == "partial"
    assert exchanges[-1]["response"] == json.loads(outputs[-1].stdout)


def test_malformed_governance_precondition_does_not_trigger_f1(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    calls = tmp_path / "calls.txt"
    helper = _raw_helper(
        tmp_path,
        "malformed-governance",
        "\n".join(
            [
                "import json",
                "import sys",
                "from pathlib import Path",
                f"calls = Path({str(calls)!r})",
                "with calls.open('a', encoding='utf-8') as stream:",
                "    stream.write(sys.argv[2] + '\\n')",
                "print(json.dumps({",
                "    'contract': 'ldvh-helper-cli/2',",
                "    'request_kind': sys.argv[1],",
                "    'operation_key': sys.argv[2],",
                "    'outcome': 'ok',",
                "    'result': {",
                "        'scope_status': 'governed_single',",
                "        'object_resolutions': [{'status': 'unknown', 'governed_project_id': 'sample'}],",
                "    },",
                "}))",
            ]
        )
        + "\n",
    )

    exchanges = _recover(helper, workspace, project)

    assert calls.read_text(encoding="utf-8").splitlines() == ["resolve-governance-scope"]
    assert len(exchanges) == 1
    assert exchanges[0]["response"]["result"]["scope_status"] == "governed_single"


@pytest.mark.parametrize(
    ("contract", "operation_expression", "outcome", "exit_code", "expected"),
    [
        ("ldvh-helper-cli/future", "sys.argv[2]", "ok", 0, "response contract"),
        ("ldvh-helper-cli/2", "'wrong-operation'", "ok", 0, "response operation_key"),
        ("ldvh-helper-cli/2", "sys.argv[2]", "partial", 0, "outcome and process exit code"),
    ],
)
def test_shared_recovery_rejects_protocol_identity_or_exit_mismatch(
    tmp_path: Path,
    contract: str,
    operation_expression: str,
    outcome: str,
    exit_code: int,
    expected: str,
) -> None:
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _raw_helper(
        tmp_path,
        "invalid-protocol",
        "\n".join(
            [
                "import json",
                "import sys",
                "print(json.dumps({",
                f"    'contract': {contract!r},",
                "    'request_kind': sys.argv[1],",
                f"    'operation_key': {operation_expression},",
                f"    'outcome': {outcome!r},",
                "}))",
                f"raise SystemExit({exit_code})",
            ]
        )
        + "\n",
    )

    with pytest.raises(ValueError) as captured:
        _recover(helper, workspace, project)

    assert expected in str(captured.value)


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
def test_codex_adapter_thinly_maps_supported_native_events(
    tmp_path: Path,
    event: str,
    source: str | None,
    native_trigger: str,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper, records = _recording_helper(tmp_path)
    _apply(plugin_data, helper, workspace)

    completed, response = _run_hook(plugin_data, project, event=event, source=source)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert response["hookSpecificOutput"]["hookEventName"] == event
    context = response["hookSpecificOutput"]["additionalContext"]
    assert f"mapped {native_trigger} to shared context recovery" in context
    assert "Helper exchanges contain each actual request" in context
    assert "Code did not interpret fact applicability" in context
    encoded_exchanges = context.split("unmodified Helper response: ", 1)[1].rsplit(". Code did not interpret", 1)[0]
    exchanges = json.loads(encoded_exchanges)
    assert [exchange["operation_key"] for exchange in exchanges] == [
        "resolve-governance-scope",
        "find-fact-object-candidates",
    ]
    assert [exchange["exit_code"] for exchange in exchanges] == [0, 0]
    assert exchanges[0]["request"] == {
        "work_object_locators": [str(project)],
        "arguments": {"workspace_root": str(workspace.resolve())},
        "response_profile": "compact",
    }
    assert exchanges[1]["request"] == {
        "work_object_locators": [str(project)],
        "arguments": {
            "workspace_root": str(workspace.resolve()),
            "governed_project_id": "sample",
            "card_layer": "F1",
        },
        "response_profile": "compact",
    }
    actual_records = [json.loads(line) for line in records.read_text(encoding="utf-8").splitlines()]
    assert [exchange["request"] for exchange in exchanges] == [
        json.loads(record["request"]) for record in actual_records
    ]
    assert [exchange["exit_code"] for exchange in exchanges] == [record["exit_code"] for record in actual_records]
    assert [exchange["response"] for exchange in exchanges] == [
        json.loads(record["stdout"]) for record in actual_records
    ]


def test_missing_configuration_is_an_explicit_non_blocking_gap(tmp_path: Path) -> None:
    cwd = tmp_path / "project"
    cwd.mkdir()

    completed, response = _run_hook(tmp_path / "missing-plugin-data", cwd)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert "configuration does not exist" in response["systemMessage"]
    assert "LDVH context as unresolved" in response["hookSpecificOutput"]["additionalContext"]


def test_helper_removed_after_configuration_is_an_explicit_non_blocking_gap(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    workspace = _workspace(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    helper = _raw_helper(tmp_path, "removed-helper", "raise SystemExit(0)\n")
    _apply(plugin_data, helper, workspace)
    helper.unlink()

    completed, response = _run_hook(plugin_data, project)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert "helper_executable does not identify a current file" in response["systemMessage"]
    assert "LDVH context as unresolved" in response["hookSpecificOutput"]["additionalContext"]


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
