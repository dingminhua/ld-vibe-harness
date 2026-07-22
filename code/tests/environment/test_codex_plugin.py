from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import HELPER_EXECUTABLE

from ldvh import work_context

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPOSITORY_ROOT / "code/plugins/ldvh"
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"
CONFIGURE = SCRIPTS_ROOT / "configure.py"
CODEX_CONTEXT = SCRIPTS_ROOT / "codex_context.py"


def _executable(tmp_path: Path, name: str, body: str) -> Path:
    script = tmp_path / f"{name}.py"
    script.write_text(body, encoding="utf-8")
    executable = tmp_path / name
    executable.write_text(f"#!{sys.executable}\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
    executable.chmod(0o755)
    return executable


def _recording_core(tmp_path: Path, *, response: dict[str, Any] | None = None) -> tuple[Path, Path]:
    records = tmp_path / "core-records.jsonl"
    body = "\n".join(
        [
            "import json",
            "import sys",
            "from pathlib import Path",
            f"records = Path({str(records)!r})",
            "native = json.load(sys.stdin)",
            "with records.open('a', encoding='utf-8') as stream:",
            "    stream.write(json.dumps({'argv': sys.argv[1:], 'stdin': native}) + '\\n')",
            (
                f"response = {response!r}"
                if response is not None
                else "response = {'contract': 'ldvh-work-context/1', 'event_name': native['hook_event_name'], "
                "'outcome': 'ok', 'facts': 'not_requested', 'additional_context': 'core result'}"
            ),
            "print(json.dumps(response, ensure_ascii=False))",
        ]
    ) + "\n"
    return _executable(tmp_path, "recording-work-context", body), records


def _actual_work_context(tmp_path: Path) -> Path:
    return _executable(
        tmp_path,
        "ldvh-work-context",
        "\n".join(
            [
                "import sys",
                f"sys.path.insert(0, {str(REPOSITORY_ROOT / 'code')!r})",
                "from ldvh.work_context import main",
                "raise SystemExit(main())",
            ]
        )
        + "\n",
    )


def _recording_actual_work_context(tmp_path: Path) -> tuple[Path, Path]:
    actual_core = _actual_work_context(tmp_path)
    records = tmp_path / "actual-core-records.jsonl"
    body = "\n".join(
        [
            "import json",
            "import subprocess",
            "import sys",
            "from pathlib import Path",
            f"actual_core = {str(actual_core)!r}",
            f"records = Path({str(records)!r})",
            "raw = sys.stdin.buffer.read()",
            "native = json.loads(raw)",
            "with records.open('a', encoding='utf-8') as stream:",
            "    stream.write(json.dumps({'native': native, 'raw': raw.decode('utf-8')}, ensure_ascii=False) + '\\n')",
            "completed = subprocess.run([actual_core, *sys.argv[1:]], input=raw, capture_output=True, check=False)",
            "sys.stdout.buffer.write(completed.stdout)",
            "sys.stderr.buffer.write(completed.stderr)",
            "raise SystemExit(completed.returncode)",
        ]
    ) + "\n"
    return _executable(tmp_path, "recording-actual-work-context", body), records


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


def _apply(plugin_data: Path, helper: Path, core: Path) -> dict[str, Any]:
    completed, response = _run_configure(
        "apply",
        "--plugin-data",
        str(plugin_data),
        "--helper-executable",
        str(helper),
        "--work-context-executable",
        str(core),
        "--confirm-write",
        "--replace",
    )
    assert completed.returncode == 0
    assert response["outcome"] in {"ok", "no_change"}
    return response


def _run_hook(
    plugin_data: Path,
    cwd: Path,
    *,
    event: str = "SessionStart",
    source: str | None = "startup",
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], dict[str, Any]]:
    environment = os.environ.copy()
    environment.update({"PLUGIN_DATA": str(plugin_data), "PLUGIN_ROOT": str(PLUGIN_ROOT)})
    native: dict[str, Any] = {"hook_event_name": event, "cwd": str(cwd)}
    if source is not None:
        native["source"] = source
    if event == "SubagentStart":
        native.update({"agent_id": "fixture-agent", "agent_type": "default"})
    completed = subprocess.run(
        [sys.executable, str(CODEX_CONTEXT)],
        input=json.dumps(native),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        env=environment,
        check=False,
    )
    assert completed.stderr == ""
    return completed, json.loads(completed.stdout), native


@pytest.mark.parametrize(
    ("cwd", "message"),
    [
        ("relative-project", "current directory must be an absolute path"),
        ("missing", "current directory does not identify an existing directory"),
    ],
)
def test_work_context_reports_the_specific_native_cwd_problem(
    tmp_path: Path,
    cwd: str,
    message: str,
) -> None:
    supplied_cwd = cwd if cwd == "relative-project" else str(tmp_path / cwd)

    with pytest.raises(work_context.WorkContextError, match=message):
        work_context._native_trigger(
            {
                "hook_event_name": "SessionStart",
                "source": "startup",
                "cwd": supplied_cwd,
            }
        )


def test_manifest_keeps_only_the_current_five_event_registrations() -> None:
    hooks = json.loads((PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
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
                            "statusMessage": "Loading LDVH rule context",
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
                            "statusMessage": "Loading LDVH rule context",
                        }
                    ]
                }
            ],
        }
    }


def test_adapter_is_a_thin_core_reference_without_business_selection() -> None:
    source = CODEX_CONTEXT.read_text(encoding="utf-8")
    assert "RULE_ORIENTATION" not in source
    assert "read-specification-content" not in source
    assert "context_recovery" not in source
    tree = ast.parse(source)
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


def test_configuration_migrates_to_explicit_work_context_core(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    core, _ = _recording_core(tmp_path)

    applied = _apply(plugin_data, HELPER_EXECUTABLE, core)
    checked, check = _run_configure("check", "--plugin-data", str(plugin_data))

    assert applied["configuration"] == {
        "config_version": 4,
        "helper_executable": str(HELPER_EXECUTABLE.resolve()),
        "work_context_executable": str(core.resolve()),
    }
    assert checked.returncode == 0
    assert check["configuration"] == applied["configuration"]


def test_legacy_configuration_is_not_a_silent_context_recovery_fallback(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir()
    cwd = tmp_path / "project"
    cwd.mkdir()
    legacy_runner, records = _recording_core(tmp_path)
    (plugin_data / "ldvh.json").write_text(
        json.dumps(
            {
                "config_version": 3,
                "helper_executable": str(HELPER_EXECUTABLE),
                "context_recovery_executable": str(legacy_runner),
                "workspace_root": str(tmp_path),
            }
        ),
        encoding="utf-8",
    )

    completed, response, _ = _run_hook(plugin_data, cwd)

    assert completed.returncode == 0
    assert response["continue"] is True
    assert "requires explicit migration to version 4" in response["systemMessage"]
    assert "hookSpecificOutput" not in response
    assert not records.exists()


def test_explicit_replace_can_migrate_a_stale_legacy_recovery_configuration(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir()
    core, _ = _recording_core(tmp_path)
    (plugin_data / "ldvh.json").write_text(
        json.dumps(
            {
                "config_version": 2,
                "helper_executable": str(tmp_path / "missing-helper"),
                "context_recovery_executable": str(tmp_path / "missing-recovery"),
                "workspace_root": str(tmp_path / "missing-workspace"),
            }
        ),
        encoding="utf-8",
    )

    applied = _apply(plugin_data, HELPER_EXECUTABLE, core)

    assert applied["changes"] == [{"kind": "replaced", "path": str(plugin_data / "ldvh.json")}]
    assert applied["configuration"]["config_version"] == 4


@pytest.mark.parametrize(
    ("event", "source"),
    [
        ("SessionStart", "startup"),
        ("SessionStart", "resume"),
        ("SessionStart", "clear"),
        ("SessionStart", "compact"),
        ("SubagentStart", None),
    ],
)
def test_each_registered_event_forwards_its_native_object_to_the_same_core(
    tmp_path: Path,
    event: str,
    source: str | None,
) -> None:
    plugin_data = tmp_path / "plugin-data"
    cwd = tmp_path / "project"
    cwd.mkdir()
    core, records = _recording_core(tmp_path)
    _apply(plugin_data, HELPER_EXECUTABLE, core)

    completed, response, native = _run_hook(plugin_data, cwd, event=event, source=source)

    assert completed.returncode == 0
    assert response == {
        "continue": True,
        "hookSpecificOutput": {"hookEventName": event, "additionalContext": "core result"},
    }
    record = json.loads(records.read_text(encoding="utf-8").strip())
    assert record["stdin"] == native
    assert record["argv"] == ["--helper-executable", str(HELPER_EXECUTABLE.resolve())]


def test_adapter_maps_an_unavailable_core_result_without_reinterpreting_it(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    cwd = tmp_path / "project"
    cwd.mkdir()
    core, _ = _recording_core(
        tmp_path,
        response={
            "contract": "ldvh-work-context/1",
            "event_name": "SessionStart",
            "outcome": "unavailable",
            "facts": "not_requested",
            "additional_context": "core unavailable with original gap",
        },
    )
    _apply(plugin_data, HELPER_EXECUTABLE, core)

    completed, response, _ = _run_hook(plugin_data, cwd)

    assert completed.returncode == 0
    assert response["hookSpecificOutput"]["additionalContext"] == "core unavailable with original gap"


def test_adapter_rejects_a_core_result_with_a_different_event_identity(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    cwd = tmp_path / "project"
    cwd.mkdir()
    core, _ = _recording_core(
        tmp_path,
        response={
            "contract": "ldvh-work-context/1",
            "event_name": "SubagentStart",
            "outcome": "ok",
            "facts": "not_requested",
            "additional_context": "wrong event",
        },
    )
    _apply(plugin_data, HELPER_EXECUTABLE, core)

    completed, response, _ = _run_hook(plugin_data, cwd)

    assert completed.returncode == 0
    assert "did not return a valid result" in response["systemMessage"]
    assert "hookSpecificOutput" not in response


def test_adapter_forwards_exact_native_json_to_the_actual_core(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    cwd = tmp_path / "project"
    cwd.mkdir()
    helper = _executable(
        tmp_path,
        "helper",
        "print('{\"contract\": \"ldvh-helper-cli/2\", \"request_kind\": \"call\", "
        "\"operation_key\": \"read-specification-content\", \"outcome\": \"ok\", "
        "\"result\": {\"items\": []}, \"scope\": {\"completed\": [], \"not_completed\": []}, "
        "\"gaps\": [], \"follow_up\": {\"summary\": \"continue\"}}')\n",
    )
    core, records = _recording_actual_work_context(tmp_path)
    _apply(plugin_data, helper, core)

    completed, response, native = _run_hook(plugin_data, cwd, event="SessionStart", source="compact")

    assert completed.returncode == 0
    assert response["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    record = json.loads(records.read_text(encoding="utf-8").strip())
    assert record["raw"] == json.dumps(native, ensure_ascii=False, separators=(",", ":"))
    assert record["native"] == native


def test_work_context_core_deduplicates_shared_rule_parts_without_hiding_delivery_scope() -> None:
    shared_part = {
        "content": "共同根上下文",
        "heading_path": ["8. 系统级运行架构"],
        "source": {"locator": "specs/00-理念与构成.md#L189-L196"},
    }
    response = {
        "result": {"items": [{"parts": [shared_part]}, {"parts": [shared_part]}]},
    }

    parts = work_context._rule_parts(response)

    assert parts == [
        {
            "content": "共同根上下文",
            "heading_path": ["8. 系统级运行架构"],
            "locator": "specs/00-理念与构成.md#L189-L196",
        }
    ]


def test_actual_core_keeps_rule_selection_fixed_while_using_native_cwd_for_source_view(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    cwd = tmp_path / "project"
    cwd.mkdir()
    helper_records = tmp_path / "helper-records.jsonl"
    helper = _executable(
        tmp_path,
        "recording-helper",
        "\n".join(
            [
                "import json",
                "import sys",
                "from pathlib import Path",
                f"records = Path({str(helper_records)!r})",
                "with records.open('a', encoding='utf-8') as stream:",
                "    record = {'argv': sys.argv[1:], 'cwd': str(Path.cwd()), 'stdin': json.load(sys.stdin)}",
                "    stream.write(json.dumps(record) + '\\n')",
                "print(json.dumps({'contract': 'ldvh-helper-cli/2', 'request_kind': 'call', "
                "'operation_key': 'read-specification-content', 'outcome': 'ok', "
                "'result': {'items': [{'parts': [{'content': '规则原文', 'heading_path': ['8. 系统级运行架构', "
                "'8.1 工作上下文的信息交付顺序与渐进式披露'], 'source': {'locator': 'specs/00-理念与构成.md'}}]}]}, "
                "'scope': {'completed': [], 'not_completed': []}, 'gaps': [], 'follow_up': {'summary': '继续读取'}}))",
            ]
        )
        + "\n",
    )
    _apply(plugin_data, helper, _actual_work_context(tmp_path))

    other_cwd = tmp_path / "other-project"
    other_cwd.mkdir()
    completed, response, _ = _run_hook(plugin_data, cwd)
    other_completed, other_response, _ = _run_hook(plugin_data, other_cwd)

    assert completed.returncode == 0
    assert other_completed.returncode == 0
    assert "Facts: not_requested" in response["hookSpecificOutput"]["additionalContext"]
    assert "Facts: not_requested" in other_response["hookSpecificOutput"]["additionalContext"]
    expected_request = {
        "arguments": {
            "selections": [
                {
                    "responsibility_key": "ldvh-root",
                    "heading_path": ["8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"],
                },
                {
                    "responsibility_key": "ldvh-root",
                    "heading_path": ["8. 系统级运行架构", "8.2 环境 Hook 的薄引用与核心职责边界"],
                },
            ]
        },
        "requested_disclosure": "L3",
        "response_profile": "compact",
        "observed_context": {},
    }
    records = [json.loads(line) for line in helper_records.read_text(encoding="utf-8").splitlines()]
    assert [record["argv"] for record in records] == [
        ["call", "read-specification-content"],
        ["call", "read-specification-content"],
    ]
    assert [record["cwd"] for record in records] == [str(cwd), str(other_cwd)]
    assert [record["stdin"] for record in records] == [expected_request, expected_request]


def test_actual_core_failure_preserves_the_native_event_for_thin_mapping(tmp_path: Path) -> None:
    plugin_data = tmp_path / "plugin-data"
    cwd = tmp_path / "project"
    cwd.mkdir()
    helper = _executable(tmp_path, "invalid-helper", "print('not-json')\n")
    _apply(plugin_data, helper, _actual_work_context(tmp_path))

    completed, response, _ = _run_hook(plugin_data, cwd)

    assert completed.returncode == 0
    assert response["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    context = response["hookSpecificOutput"]["additionalContext"]
    assert "LDVH work-context core unavailable" in context
    assert "facts remain not_requested" in context
