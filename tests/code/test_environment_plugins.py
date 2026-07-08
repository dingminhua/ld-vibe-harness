from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import action_classifier


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = ROOT / "hooks/environment-plugins/codex-ldvh-v3"
SHIM = ROOT / "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"
PLUGIN_JSON = PLUGIN_ROOT / "plugin.json"
WORKBUDDY_PLUGIN_ROOT = ROOT / "hooks/environment-plugins/workbuddy-ldvh-v3"
WORKBUDDY_SHIM = WORKBUDDY_PLUGIN_ROOT / "hooks/ldvh_runtime_shim.py"
ENTRY_ACK_PATHS = [
    "specs/00-理念与构成.md",
    "specs/01-保障与衔接.md",
    "specs/02-AI行为规范.md",
]
TEST_TARGET_ACK_PATHS = [
    *ENTRY_ACK_PATHS,
    "specs/03-事实源与Git溯源规范.md",
    "specs/04-Specs基础规范.md",
    "specs/09-测试与验证规范.md",
    "specs/07-Code确定性执行规范.md",
]
WORKCASE_TARGET = "ldvh-base/workcases/workcase-0024-v2-deletion-readiness-closure.yaml"
WORKCASE_ACK_PATHS = [
    *ENTRY_ACK_PATHS,
    "specs/03-事实源与Git溯源规范.md",
    "specs/04-Specs基础规范.md",
    "specs/05-事实模型基础规范.md",
    "specs/09-测试与验证规范.md",
    "specs/21-WorkCase-工作项.md",
    WORKCASE_TARGET,
]


def _ack_args(paths: list[str]) -> list[str]:
    args: list[str] = []
    for path in paths:
        args.extend(["--acknowledged-path", path])
    return args


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def _run_shim(payload: dict, *, check: bool = True, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["LDVH_ROOT"] = ROOT.as_posix()
    env["LDVH_HOOK_SPARK_CAPTURE"] = "0"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, SHIM.as_posix()],
        cwd=ROOT,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=check,
        env=env,
        timeout=60,
    )


def _run_workbuddy_shim(
    payload: dict, *, check: bool = True, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["LDVH_ROOT"] = ROOT.as_posix()
    env["LDVH_HOOK_SPARK_CAPTURE"] = "0"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, WORKBUDDY_SHIM.as_posix()],
        cwd=ROOT,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=check,
        env=env,
        timeout=60,
    )


def _diagnostic_codes(result: dict) -> set[str]:
    return {diagnostic["code"] for diagnostic in result.get("diagnostics", [])}


def _hook_output(payload: dict) -> dict:
    value = payload.get("hookSpecificOutput")
    return value if isinstance(value, dict) else {}


def _command_payload(command: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "sessionId": "shim-shared-classifier",
        "cwd": ROOT.as_posix(),
        "toolName": "functions.exec_command",
        "arguments": {"cmd": command},
    }


def _nested_command_payloads(command: str) -> list[dict]:
    return [
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-nested-tool",
            "cwd": ROOT.as_posix(),
            "tool": {"name": "functions.exec_command", "arguments": {"cmd": command}},
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-nested-bash",
            "cwd": ROOT.as_posix(),
            "tool": {"name": "Bash", "input": {"command": command}},
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-nested-tool-call",
            "cwd": ROOT.as_posix(),
            "tool_call": {
                "function": {
                    "name": "functions.exec_command",
                    "arguments": json.dumps({"cmd": command}, ensure_ascii=False),
                }
            },
        },
    ]


def _nested_write_payloads() -> list[dict]:
    return [
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-nested-write",
            "cwd": ROOT.as_posix(),
            "tool": {"name": "Write", "input": {"file_path": "README.md"}},
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-nested-edit",
            "cwd": ROOT.as_posix(),
            "tool": {
                "name": "Edit",
                "input": {
                    "file_path": "README.md",
                    "old_string": "LDVH",
                    "new_string": "LDVH V3",
                },
            },
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-nested-apply-patch",
            "cwd": ROOT.as_posix(),
            "tool": {
                "name": "apply_patch",
                "input": {
                    "patch": (
                        "*** Begin Patch\n"
                        "*** Update File: README.md\n"
                        "@@\n"
                        "-LDVH\n"
                        "+LDVH V3\n"
                        "*** End Patch\n"
                    ),
                },
            },
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-nested-functions-apply-patch",
            "cwd": ROOT.as_posix(),
            "tool_call": {
                "function": {
                    "name": "functions.apply_patch",
                    "arguments": json.dumps(
                        {
                            "patch": (
                                "*** Begin Patch\n"
                                "*** Update File: README.md\n"
                                "@@\n"
                                "-LDVH\n"
                                "+LDVH V3\n"
                                "*** End Patch\n"
                            )
                        },
                        ensure_ascii=False,
                    ),
                }
            },
        },
    ]


def test_shared_action_classifier_covers_read_and_write_command_matrix() -> None:
    read_only_commands = [
        "pwd",
        'rg -n "read_plan|target_path" code/runtime_adapter.py | sed -n \'1,20p\'',
        "find ldvh-base -maxdepth 2 -type f -print | sort | sed -n '1,120p'",
        'rg -l "LDVH" README.md | xargs wc -l',
        'pwd && rg -n "session_start|receipt" -S .',
        "sleep 20",
        f"git -C {ROOT.as_posix()} status --short",
        "python3 code/session_start.py --task probe --target-path README.md",
        "python3 code/runtime_adapter.py session-start --help",
    ]
    write_like_commands = [
        "sed -i '' -e 's/old/new/' README.md",
        "sed -n 'w tmp/sed-out.txt' README.md",
        "sed '/LDVH/w tmp/sed-out.txt' README.md",
        "sed 's/LDVH/echo LDVH/e' README.md",
        "find . -name '*.tmp' -exec rm {} \\;",
        "find . -name '*.tmp' -delete",
        "find . -name '*.py' -fprint tmp/list.txt",
        "find . -name '*.py' -fprint0 tmp/list.txt",
        "find . -name '*.py' -fprintf tmp/list.txt '%p\\n'",
        "find . -name '*.py' -fls tmp/list.txt",
        "pwd &",
        "git commit -m test",
        "python3 -c 'print(1)'",
        'rg -l "LDVH" README.md | xargs rm -f',
        "python3 code/acknowledge_read_plan.py --session-id x --target-path README.md --format json && touch tmp/leak",
    ]

    for command in read_only_commands:
        classification = action_classifier.classify_action(_command_payload(command), ROOT)
        assert classification.operation == "read", command
        assert classification.requires_preflight is False, command

    for command in write_like_commands:
        classification = action_classifier.classify_action(_command_payload(command), ROOT)
        assert classification.requires_preflight is True, command


def test_shared_action_classifier_noops_codex_read_and_process_tools() -> None:
    for tool_name in (
        "codex_applist_threads",
        "codex_app.list_threads",
        "update_plan",
        "functions.update_plan",
        "close_agent",
        "multi_agent_v1.close_agent",
        "multi_agent_v1close_agent",
    ):
        classification = action_classifier.classify_action({"hook_event_name": "PreToolUse", "toolName": tool_name}, ROOT)
        assert classification.operation == "read"
        assert classification.requires_preflight is False
        assert classification.reason == "read_only_tool"


def test_shared_action_classifier_covers_nested_tool_payloads() -> None:
    for payload in _nested_command_payloads("pwd"):
        classification = action_classifier.classify_action(payload, ROOT)
        assert classification.operation == "read"
        assert classification.requires_preflight is False
        assert classification.reason == "read_only_command"

    for payload in _nested_write_payloads():
        classification = action_classifier.classify_action(payload, ROOT)
        assert classification.operation == "write"
        assert classification.requires_preflight is True


def test_environment_shims_delegate_to_shared_classifier_for_command_parity(tmp_path: Path) -> None:
    read_only_commands = [
        "pwd",
        'rg -n "read_plan|target_path" code/runtime_adapter.py | sed -n \'1,20p\'',
        "find ldvh-base -maxdepth 2 -type f -print | sort | sed -n '1,120p'",
        'rg -l "LDVH" README.md | xargs wc -l',
        'pwd && rg -n "session_start|receipt" -S .',
        "sleep 20",
        f"git -C {ROOT.as_posix()} status --short",
        "python3 code/session_start.py --task probe --target-path README.md",
    ]
    write_like_commands = [
        "sed -i '' -e 's/old/new/' README.md",
        "sed -n 'w tmp/sed-out.txt' README.md",
        "sed '/LDVH/w tmp/sed-out.txt' README.md",
        "sed 's/LDVH/echo LDVH/e' README.md",
        "find . -name '*.tmp' -exec rm {} \\;",
        "find . -name '*.tmp' -delete",
        "find . -name '*.py' -fprint tmp/list.txt",
        "find . -name '*.py' -fprintf tmp/list.txt '%p\\n'",
        "pwd &",
        "python3 -c 'print(1)'",
        'rg -l "LDVH" README.md | xargs rm -f',
    ]

    for command in read_only_commands:
        codex = _run_shim(_command_payload(command))
        workbuddy = _run_workbuddy_shim(
            _command_payload(command),
            extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        )
        assert codex.stdout == "", command
        assert workbuddy.stdout == "", command

    for command in write_like_commands:
        codex = _run_shim(_command_payload(command), check=False)
        workbuddy = _run_workbuddy_shim(
            _command_payload(command),
            check=False,
            extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        )
        codex_output = _hook_output(json.loads(codex.stdout))
        workbuddy_output = _hook_output(json.loads(workbuddy.stdout))
        assert codex_output["permissionDecision"] == "deny", command
        assert workbuddy_output["permissionDecision"] == "deny", command
        assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in codex_output["permissionDecisionReason"], command
        assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in workbuddy_output["permissionDecisionReason"], command


def test_environment_shims_allow_nested_read_only_command_payloads(tmp_path: Path) -> None:
    for payload in _nested_command_payloads("pwd"):
        codex = _run_shim(payload)
        workbuddy = _run_workbuddy_shim(
            payload,
            extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        )
        assert codex.stdout == "", payload
        assert workbuddy.stdout == "", payload

    for payload in _nested_write_payloads():
        codex = _run_shim(payload, check=False)
        workbuddy = _run_workbuddy_shim(
            payload,
            check=False,
            extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        )
        codex_output = _hook_output(json.loads(codex.stdout))
        workbuddy_output = _hook_output(json.loads(workbuddy.stdout))
        assert codex_output["permissionDecision"] == "deny"
        assert workbuddy_output["permissionDecision"] == "deny"
        assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in codex_output["permissionDecisionReason"]
        assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in workbuddy_output["permissionDecisionReason"]


def test_environment_shims_do_not_keep_local_command_classification_registries() -> None:
    shared_raw = (ROOT / "code/action_classifier.py").read_text(encoding="utf-8")
    assert "READ_ONLY_COMMANDS =" in shared_raw
    assert "COMMAND_EXECUTION_TOOLS =" in shared_raw

    for shim in (SHIM, WORKBUDDY_SHIM):
        raw = shim.read_text(encoding="utf-8")
        assert "READ_ONLY_COMMANDS =" not in raw
        assert "COMMAND_EXECUTION_TOOLS =" not in raw
        assert "READ_ONLY_TOOLS =" not in raw


def test_codex_sample_plugin_manifest_consumes_package_icons() -> None:
    assert not (PLUGIN_ROOT / ".codex-plugin").exists()

    manifest = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    interface = manifest["interface"]

    assert interface["composerIcon"] == "./assets/ldvh-plugin-icon-128.png"
    assert interface["logo"] == "./assets/ldvh-plugin-icon-512.png"

    for field in ("composerIcon", "logo"):
        rel_path = interface[field]
        assert rel_path.startswith("./assets/")
        asset_path = (PLUGIN_ROOT / rel_path[2:]).resolve()
        assert PLUGIN_ROOT.resolve() in asset_path.parents
        assert asset_path.is_file()


def test_codex_sample_plugin_hooks_do_not_emit_status_messages() -> None:
    hooks = json.loads((PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
    raw = json.dumps(hooks, ensure_ascii=False)

    assert "statusMessage" not in raw


def test_codex_sample_plugin_declares_six_research_hook_events() -> None:
    hooks = json.loads((PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]

    assert set(hooks) == {
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
        "UserPromptSubmit",
        "Stop",
        "Notification",
    }
    for event_name, entries in hooks.items():
        assert entries
        assert all(
            hook["command"] == 'python3 "$PLUGIN_ROOT/hooks/ldvh_runtime_shim.py"'
            for entry in entries
            for hook in entry["hooks"]
        ), event_name


def test_environment_plugin_readmes_use_ldvh_canonical_events() -> None:
    readmes = [
        PLUGIN_ROOT / "README.md",
        WORKBUDDY_PLUGIN_ROOT / "README.md",
    ]

    for readme in readmes:
        raw = readme.read_text(encoding="utf-8")
        assert "LDVH canonical event" in raw
        assert "`ldvh.session_start`" in raw
        assert "`ldvh.pre_tool_use`" in raw
        assert "`ldvh.completion_claim`" in raw
        assert "code/action_classifier.py" in raw
        assert "shared classifier" in raw
        assert "shim 中不得维护独立分类规则" in raw
        assert "V3 runtime event" not in raw
        assert "PreToolUse 阻断返回" not in raw
        assert "| `SessionStart` | `session_start` |" not in raw
        assert "| `PreToolUse` | `pre_tool_use` |" not in raw
        assert "| `Stop` | `completion_claim` |" not in raw


def test_environment_plugin_practice_and_directory_readme_use_shared_classifier_boundary() -> None:
    practice = (ROOT / "code/docs/02-Environment-Plugin-Practice.md").read_text(encoding="utf-8")
    directory_readme = (ROOT / "hooks/environment-plugins/README.md").read_text(encoding="utf-8")

    assert "specs/attachments/33.Att.01-环境插件差异速查.md" in practice
    assert "code/action_classifier.py" in practice
    assert "只读 / 写入副作用分类由 `code/action_classifier.py` 统一判断" in practice
    assert "不维护第二套规则源、字段契约、状态机、事实源、命令分类、target 归口、diagnostic 分流或完成判断" in practice
    assert "shared classifier parity" in practice
    assert "code/action_classifier.py" in directory_readme
    assert "33.Att.01" in directory_readme
    assert "不维护独立命令分类、target 归口、diagnostic 分流、read_plan、repair、bypass、completion 或状态推进" in directory_readme
    assert "不复制 specs、事实对象、行动模板、Human Gate 或管辖项目配置内容" in directory_readme
    assert "定位 LDVH 根目录和已确认的管辖项目配置" not in practice
    assert "shim 自己判断" not in practice + directory_readme


def test_v2_absorbed_icon_assets_have_expected_png_sizes() -> None:
    expected_sizes = {
        "ldvh-plugin-icon-16.png": (16, 16),
        "ldvh-plugin-icon-32.png": (32, 32),
        "ldvh-plugin-icon-48.png": (48, 48),
        "ldvh-plugin-icon-64.png": (64, 64),
        "ldvh-plugin-icon-128.png": (128, 128),
        "ldvh-plugin-icon-180.png": (180, 180),
        "ldvh-plugin-icon-192.png": (192, 192),
        "ldvh-plugin-icon-256.png": (256, 256),
        "ldvh-plugin-icon-512.png": (512, 512),
        "ldvh-plugin-icon.png": (512, 512),
    }

    for filename, dimensions in expected_sizes.items():
        assert _png_dimensions(ROOT / "icons" / filename) == dimensions

    assert _png_dimensions(PLUGIN_ROOT / "assets/ldvh-plugin-icon-128.png") == (128, 128)
    assert _png_dimensions(PLUGIN_ROOT / "assets/ldvh-plugin-icon-512.png") == (512, 512)


def test_codex_sample_shim_passes_session_payload_to_runtime_adapter() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "SessionStart",
            "sessionId": "shim-session",
            "cwd": ROOT.as_posix(),
            "prompt": "进入 LDVH v3 工作",
            "targetPath": "README.md",
        },
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "SessionStart"
    assert "LDVH V3 session read plan is active" in hook_output["additionalContext"]
    assert "specs/00-理念与构成.md" in hook_output["additionalContext"]
    assert "specs/01-保障与衔接.md" in hook_output["additionalContext"]
    assert "specs/02-AI行为规范.md" in hook_output["additionalContext"]


def test_codex_sample_shim_silent_noops_for_non_governed_events(tmp_path: Path) -> None:
    outside = tmp_path / "outside-project"
    outside.mkdir()
    payloads = [
        {
            "hook_event_name": "SessionStart",
            "sessionId": "shim-outside-session",
            "cwd": outside.as_posix(),
            "prompt": "外部项目工作",
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-outside-pretool",
            "cwd": outside.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "notes.txt"},
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-outside-edit",
            "cwd": outside.as_posix(),
            "toolName": "Edit",
            "toolInput": {"filePath": "notes.txt"},
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-outside-multipath",
            "cwd": outside.as_posix(),
            "toolName": "MultiEdit",
            "tool_input": {"file_paths": ["notes.txt", "docs/todo.md"]},
        },
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-outside-camel-multipath",
            "cwd": outside.as_posix(),
            "toolName": "MultiEdit",
            "toolInput": {"filePaths": ["notes.txt", "docs/todo.md"]},
        },
        {
            "hook_event_name": "Stop",
            "sessionId": "shim-outside-stop",
            "cwd": outside.as_posix(),
        },
    ]

    for payload in payloads:
        completed = _run_shim(payload)
        assert completed.returncode == 0
        assert completed.stdout == ""
        assert completed.stderr == ""


def test_codex_sample_shim_blocks_pre_tool_use_without_read_plan_ack() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "tests/code/test_environment_plugins.py"},
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_allows_read_only_bash_probe_without_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-read",
            "cwd": ROOT.as_posix(),
            "toolName": "Bash",
            "tool_input": {"command": "pwd"},
        },
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_codex_sample_shim_allows_read_only_exec_command_pipeline_without_acknowledgement() -> None:
    for command in (
        "rg -n \"read_plan|target_path\" code/runtime_adapter.py | sed -n '1,20p'",
        "find ldvh-base -maxdepth 2 -type f -print | sort | sed -n '1,120p'",
    ):
        completed = _run_shim(
            {
                "hook_event_name": "PreToolUse",
                "sessionId": "shim-pretool-exec-read",
                "cwd": ROOT.as_posix(),
                "toolName": "functions.exec_command",
                "arguments": {"cmd": command},
            },
        )

        assert completed.returncode == 0
        assert completed.stdout == ""


def test_codex_sample_shim_does_not_treat_sed_in_place_as_read_only() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-sed-in-place",
            "cwd": ROOT.as_posix(),
            "toolName": "functions.exec_command",
            "arguments": {"cmd": "sed -i '' -e 's/old/new/' README.md"},
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_allows_read_only_exec_command_and_chain_without_acknowledgement() -> None:
    for command in (
        'pwd && rg -n "session_start|receipt|lifecycle|read plan|read_plan|LDVH" -S .',
        "ls -la && rg --files",
        "sleep 20",
        f"git -C {ROOT.as_posix()} log -1 --oneline",
        f"git -C {ROOT.as_posix()} status --short",
    ):
        completed = _run_shim(
            {
                "hook_event_name": "PreToolUse",
                "sessionId": "shim-pretool-exec-and-chain-read",
                "cwd": ROOT.as_posix(),
                "toolName": "functions.exec_command",
                "arguments": {"cmd": command},
            },
        )

        assert completed.returncode == 0
        assert completed.stdout == ""


def test_codex_sample_shim_allows_multi_agent_wait_without_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-agent-wait",
            "cwd": ROOT.as_posix(),
            "toolName": "multi_agent_v1wait_agent",
            "tool_input": {"targets": ["019f39fa-148e-7aa2-b6cd-50504f7a2fa3"], "timeout_ms": 300000},
        },
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_codex_sample_shim_allows_session_start_probe_command_without_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-session-start-probe",
            "cwd": ROOT.as_posix(),
            "toolName": "functions.exec_command",
            "arguments": {
                "cmd": (
                    "python3 code/session_start.py --task "
                    "\"请在当前 ld-vibe-harness-v3 项目中触发 LDVH 会话入口检查；不要写文件，只把你看到的 LDVH read plan、session_start、receipt 或 lifecycle 输出原样告诉我。\" "
                    f"--target-path \"{ROOT.as_posix()}\""
                )
            },
        },
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_codex_sample_shim_allows_runtime_adapter_session_start_probe_without_acknowledgement() -> None:
    for command in (
        "python3 code/runtime_adapter.py session-start --help",
        (
            "python3 code/runtime_adapter.py session-start "
            f"--root \"{ROOT.as_posix()}\" "
            "--config-root \"/Users/dmh2002/poker_hud_projects\" "
            "--session-id \"lifecycle-verify-probe\" "
            f"--target-path \"{ROOT.as_posix()}\" "
            "--task \"LDVH lifecycle verification probe\" "
            "--operation read "
            "--trigger-source \"hook.lifecycle-verify-probe\" "
            "--format text"
        ),
    ):
        completed = _run_shim(
            {
                "hook_event_name": "PreToolUse",
                "sessionId": "shim-pretool-runtime-adapter-session-start",
                "cwd": ROOT.as_posix(),
                "toolName": "functions.exec_command",
                "arguments": {"cmd": command},
            },
        )

        assert completed.returncode == 0
        assert completed.stdout == ""


def test_codex_sample_shim_allows_acknowledge_read_plan_bootstrap_command_without_acknowledgement() -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id shim-pretool-ack-bootstrap "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-ack-bootstrap",
            "cwd": ROOT.as_posix(),
            "toolName": "functions.exec_command",
            "arguments": {"cmd": command},
        },
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_codex_sample_shim_allows_acknowledge_bootstrap_from_tool_field() -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id shim-pretool-ack-bootstrap-tool-field "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-ack-bootstrap-tool-field",
            "cwd": ROOT.as_posix(),
            "tool": "Bash",
            "input": {"command": command},
        },
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_codex_sample_shim_allows_acknowledge_bootstrap_from_mcp_exec_tool() -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id shim-pretool-ack-bootstrap-mcp-exec "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-ack-bootstrap-mcp-exec",
            "cwd": ROOT.as_posix(),
            "toolName": "mcp__functions__exec_command",
            "arguments": {"cmd": command},
        },
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_codex_sample_shim_does_not_treat_nested_name_as_tool_identity() -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id shim-pretool-ack-bootstrap-nested-name "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-ack-bootstrap-nested-name",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {
                "file_path": "README.md",
                "name": "bash",
                "command": command,
            },
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_does_not_allow_chained_acknowledge_bootstrap_write_without_acknowledgement() -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id shim-pretool-ack-bootstrap-chain "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json && touch tmp/ldvh-bootstrap-leak.txt"
    )
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-ack-bootstrap-chain",
            "cwd": ROOT.as_posix(),
            "toolName": "functions.exec_command",
            "arguments": {"cmd": command},
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_does_not_allow_acknowledge_bootstrap_from_write_tool_without_acknowledgement() -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id shim-pretool-ack-bootstrap-write-tool "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-ack-bootstrap-write-tool",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "README.md"},
            "cmd": command,
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_allows_explicit_read_operation_without_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-explicit-read",
            "cwd": ROOT.as_posix(),
            "toolName": "mcp.read_context",
            "operation": "read",
            "tool_input": {"query": "LDVH lifecycle boundary"},
        },
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_codex_sample_shim_allows_codex_app_read_thread_without_acknowledgement() -> None:
    for tool_name in ("codex_appread_thread", "codex_appread_thread_terminal"):
        completed = _run_shim(
            {
                "hook_event_name": "PreToolUse",
                "sessionId": "shim-pretool-read-thread",
                "cwd": ROOT.as_posix(),
                "toolName": tool_name,
                "tool_input": {"threadId": "019f39b2-9a9d-7c50-973c-21f810eebaa6"},
            },
        )

        assert completed.returncode == 0
        assert completed.stdout == ""


def test_codex_sample_shim_allows_collaboration_review_operation_without_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-agent-review",
            "cwd": ROOT.as_posix(),
            "toolName": "multi_agent.spawn_agent",
            "operation": "review",
            "tool_input": {"target_path": "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"},
        },
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_codex_sample_shim_allows_collaboration_read_only_review_intent_without_acknowledgement() -> None:
    for tool_name, tool_input in (
        (
            "spawn_agent",
            {
                "message": "请只读审核当前判断，不要修改文件，不要提交。",
            },
        ),
        (
            "multi_agent_v1send_input",
            {
                "message": "请停止继续委派，直接只读审查并返回结论。不要修改文件，不要提交。",
                "target": "019f39fa-148e-7aa2-b6cd-50504f7a2fa3",
            },
        ),
    ):
        completed = _run_shim(
            {
                "hook_event_name": "PreToolUse",
                "sessionId": "shim-pretool-agent-read-only-review",
                "cwd": ROOT.as_posix(),
                "toolName": tool_name,
                "tool_input": tool_input,
            },
        )

        assert completed.returncode == 0
        assert completed.stdout == ""


def test_codex_sample_shim_blocks_collaboration_write_operation_without_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-agent-write",
            "cwd": ROOT.as_posix(),
            "toolName": "multi_agent.spawn_agent",
            "operation": "write",
            "tool_input": {"target_path": "hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"},
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_blocks_collaboration_without_read_only_intent() -> None:
    for tool_name in ("spawn_agent", "multi_agent_v1send_input"):
        completed = _run_shim(
            {
                "hook_event_name": "PreToolUse",
                "sessionId": "shim-pretool-agent-unknown-intent",
                "cwd": ROOT.as_posix(),
                "toolName": tool_name,
                "tool_input": {"message": "请处理这个任务。"},
            },
            check=False,
        )

        payload = json.loads(completed.stdout)
        hook_output = _hook_output(payload)
        assert completed.returncode == 0
        assert hook_output["hookEventName"] == "PreToolUse"
        assert hook_output["permissionDecision"] == "deny"
        assert "PREFLIGHT_TARGET_UNKNOWN" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_blocks_write_when_target_unknown_even_with_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-write-unknown-target",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {},
            "acknowledgedPaths": ENTRY_ACK_PATHS,
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "PREFLIGHT_TARGET_UNKNOWN" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_does_not_allow_runtime_adapter_pre_tool_probe_without_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-runtime-adapter-pre-tool",
            "cwd": ROOT.as_posix(),
            "toolName": "functions.exec_command",
            "arguments": {"cmd": "python3 code/runtime_adapter.py pre-tool-use --target-path README.md --format text"},
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_does_not_allow_mixed_read_write_and_chain_without_acknowledgement() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-exec-and-chain-write",
            "cwd": ROOT.as_posix(),
            "toolName": "functions.exec_command",
            "arguments": {"cmd": "pwd && touch tmp/ldvh-mixed-chain.txt"},
        },
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_codex_sample_shim_infers_read_plan_ack_from_transcript(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        "\n".join(
            json.dumps(
                {
                    "payload": {
                        "type": "function_call",
                        "arguments": json.dumps({"cmd": f"cat {path}"}),
                    }
                },
                ensure_ascii=False,
            )
            for path in TEST_TARGET_ACK_PATHS
        ),
        encoding="utf-8",
    )

    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-transcript-ack",
            "cwd": ROOT.as_posix(),
            "transcript_path": transcript.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "tests/code/test_environment_plugins.py"},
        },
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["additionalContext"].startswith("LDVH V3 pre-tool check passed.")


def test_codex_sample_shim_consumes_session_runtime_cache(tmp_path: Path) -> None:
    extra_env = {"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "receipt-cache").as_posix()}
    subprocess.run(
        [
            sys.executable,
            "code/acknowledge_read_plan.py",
            "--session-id",
            "shim-runtime-cache",
            "--target-path",
            "tests/code/test_environment_plugins.py",
            *_ack_args(TEST_TARGET_ACK_PATHS),
            "--format",
            "json",
        ],
        cwd=ROOT,
        env={**os.environ, **extra_env},
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )

    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-runtime-cache",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "tests/code/test_environment_plugins.py"},
        },
        extra_env=extra_env,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["additionalContext"].startswith("LDVH V3 pre-tool check passed.")


def test_workbuddy_sample_shim_session_start_does_not_ack_read_plan(tmp_path: Path) -> None:
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()
    session_id = "workbuddy-no-session-ack"
    extra_env = {
        "TMPDIR": tmp_dir.as_posix(),
        "LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix(),
    }

    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "SessionStart",
            "sessionId": session_id,
            "cwd": ROOT.as_posix(),
            "prompt": "进入 LDVH v3 工作",
            "targetPath": "README.md",
        },
        extra_env=extra_env,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    legacy_cache = tmp_dir / "ldvh-codex-hook" / "receipts" / f"{session_id}.json"
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "SessionStart"
    assert "LDVH V3 session read plan is active" in hook_output["additionalContext"]
    assert not legacy_cache.exists()

    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": session_id,
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "tests/code/test_environment_plugins.py"},
        },
        extra_env=extra_env,
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_workbuddy_sample_shim_allows_acknowledge_read_plan_bootstrap_command_without_acknowledgement(
    tmp_path: Path,
) -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id workbuddy-ack-bootstrap "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-ack-bootstrap",
            "cwd": ROOT.as_posix(),
            "toolName": "functions.exec_command",
            "arguments": {"cmd": command},
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_workbuddy_sample_shim_allows_acknowledge_bootstrap_from_tool_field(
    tmp_path: Path,
) -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id workbuddy-ack-bootstrap-tool-field "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-ack-bootstrap-tool-field",
            "cwd": ROOT.as_posix(),
            "tool": "Bash",
            "input": {"command": command},
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_workbuddy_sample_shim_allows_acknowledge_bootstrap_from_mcp_exec_tool(
    tmp_path: Path,
) -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id workbuddy-ack-bootstrap-mcp-exec "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-ack-bootstrap-mcp-exec",
            "cwd": ROOT.as_posix(),
            "toolName": "mcp__functions__exec_command",
            "arguments": {"cmd": command},
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_workbuddy_sample_shim_does_not_treat_nested_name_as_tool_identity(
    tmp_path: Path,
) -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id workbuddy-ack-bootstrap-nested-name "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-ack-bootstrap-nested-name",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {
                "file_path": "README.md",
                "name": "bash",
                "command": command,
            },
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_workbuddy_sample_shim_does_not_allow_chained_acknowledge_bootstrap_write_without_acknowledgement(
    tmp_path: Path,
) -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id workbuddy-ack-bootstrap-chain "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json && touch tmp/ldvh-workbuddy-bootstrap-leak.txt"
    )
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-ack-bootstrap-chain",
            "cwd": ROOT.as_posix(),
            "toolName": "functions.exec_command",
            "arguments": {"cmd": command},
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_workbuddy_sample_shim_does_not_allow_acknowledge_bootstrap_from_write_tool_without_acknowledgement(
    tmp_path: Path,
) -> None:
    command = (
        "python3 code/acknowledge_read_plan.py "
        "--session-id workbuddy-ack-bootstrap-write-tool "
        "--target-path README.md "
        + " ".join(f"--acknowledged-path {path}" for path in ENTRY_ACK_PATHS)
        + " --format json"
    )
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-ack-bootstrap-write-tool",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "README.md"},
            "cmd": command,
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_workbuddy_sample_shim_blocks_target_unknown_even_with_acknowledgement(tmp_path: Path) -> None:
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-unknown-target",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {},
            "acknowledgedPaths": ENTRY_ACK_PATHS,
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "PREFLIGHT_TARGET_UNKNOWN" in hook_output["permissionDecisionReason"]


def test_workbuddy_sample_shim_does_not_treat_sed_in_place_as_read_only(tmp_path: Path) -> None:
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-sed-in-place",
            "cwd": ROOT.as_posix(),
            "toolName": "functions.exec_command",
            "arguments": {"cmd": "sed -i '' -e 's/old/new/' README.md"},
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        check=False,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert "RUNTIME_READ_PLAN_CONSUMED_EMPTY" in hook_output["permissionDecisionReason"]


def test_workbuddy_sample_shim_recognizes_workcase_fact_instance_target(tmp_path: Path) -> None:
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-workcase-target",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {
                "file_path": WORKCASE_TARGET
            },
            "acknowledgedPaths": WORKCASE_ACK_PATHS,
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["additionalContext"].startswith("LDVH V3 pre-tool check passed.")
    assert "specs/21-WorkCase-工作项.md" in hook_output["additionalContext"]
    assert "PREFLIGHT_TARGET_UNKNOWN" not in json.dumps(payload, ensure_ascii=False)


def test_workbuddy_sample_shim_consumes_standard_runtime_cache(tmp_path: Path) -> None:
    extra_env = {"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "receipt-cache").as_posix()}
    subprocess.run(
        [
            sys.executable,
            "code/acknowledge_read_plan.py",
            "--session-id",
            "workbuddy-runtime-cache",
            "--target-path",
            "tests/code/test_environment_plugins.py",
            *_ack_args(TEST_TARGET_ACK_PATHS),
            "--format",
            "json",
        ],
        cwd=ROOT,
        env={**os.environ, **extra_env},
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )

    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "workbuddy-runtime-cache",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "tool_input": {"file_path": "tests/code/test_environment_plugins.py"},
        },
        extra_env=extra_env,
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["additionalContext"].startswith("LDVH V3 pre-tool check passed.")


def test_codex_sample_shim_extracts_apply_patch_targets() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-apply-patch",
            "cwd": ROOT.as_posix(),
            "toolName": "apply_patch",
            "input": """*** Begin Patch
*** Update File: tests/code/test_environment_plugins.py
@@
 pass
*** End Patch
""",
            "acknowledgedPaths": TEST_TARGET_ACK_PATHS,
        },
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["additionalContext"].startswith("LDVH V3 pre-tool check passed.")


def test_codex_sample_shim_allows_pre_tool_use_with_acknowledged_paths() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-ok",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "toolInput": {"file_path": "tests/code/test_environment_plugins.py"},
            "acknowledgedPaths": TEST_TARGET_ACK_PATHS,
        },
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["additionalContext"].startswith("LDVH V3 pre-tool check passed.")
    assert "specs/00-理念与构成.md" in hook_output["additionalContext"]


def test_codex_sample_shim_recognizes_workcase_fact_instance_target() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-pretool-workcase-target",
            "cwd": ROOT.as_posix(),
            "toolName": "Write",
            "toolInput": {
                "file_path": WORKCASE_TARGET
            },
            "acknowledgedPaths": WORKCASE_ACK_PATHS,
        },
    )

    payload = json.loads(completed.stdout)
    hook_output = _hook_output(payload)
    assert completed.returncode == 0
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["additionalContext"].startswith("LDVH V3 pre-tool check passed.")
    assert "specs/21-WorkCase-工作项.md" in hook_output["additionalContext"]
    assert "PREFLIGHT_TARGET_UNKNOWN" not in json.dumps(payload, ensure_ascii=False)


def test_codex_sample_shim_degrades_completion_claim_to_non_blocking_stop() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "Stop",
            "sessionId": "shim-stop",
            "cwd": ROOT.as_posix(),
            "targetPath": "README.md",
        },
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["continue"] is True
    assert "LDVH V3 completion check warning" in payload["systemMessage"]
    assert "RUNTIME_COMPLETION_VERIFICATION_MISSING" in payload["systemMessage"]


def test_codex_sample_shim_warns_on_completion_review_required_without_blocking_stop() -> None:
    completed = _run_shim(
        {
            "hook_event_name": "Stop",
            "sessionId": "shim-stop-review-required",
            "cwd": ROOT.as_posix(),
            "targetPath": "code/ldvh_specs.py",
            "verificationEvidence": ["python3 code/specs_validate.py all --format text --fail-on-diagnostics"],
        },
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["continue"] is True
    assert "LDVH V3 completion check warning" in payload["systemMessage"]
    assert "PREFLIGHT_CODE_OUTPUT_NOT_AUTHORIZATION" in payload["systemMessage"]


def test_workbuddy_sample_shim_warns_on_completion_review_required_without_blocking_stop(tmp_path: Path) -> None:
    completed = _run_workbuddy_shim(
        {
            "hook_event_name": "Stop",
            "sessionId": "workbuddy-stop-review-required",
            "cwd": ROOT.as_posix(),
            "targetPath": "code/ldvh_specs.py",
            "verificationEvidence": ["python3 code/specs_validate.py all --format text --fail-on-diagnostics"],
        },
        extra_env={"LDVH_RUNTIME_CACHE_DIR": (tmp_path / "runtime-cache").as_posix()},
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["continue"] is True
    assert "LDVH V3 completion check warning" in payload["systemMessage"]
    assert "PREFLIGHT_CODE_OUTPUT_NOT_AUTHORIZATION" in payload["systemMessage"]


def test_codex_sample_shim_does_not_capture_research_spark_by_default(tmp_path: Path) -> None:
    spark_dir = tmp_path / "sparks"
    completed = _run_shim(
        {"hook_event_name": "SessionStart", "sessionId": "shim-no-capture", "cwd": ROOT.as_posix()},
        extra_env={
            "LDVH_HOOK_SPARK_CAPTURE": "",
            "LDVH_HOOK_SPARK_DIR": spark_dir.as_posix(),
        },
    )

    assert completed.returncode == 0
    assert not spark_dir.exists()


def test_codex_sample_shim_opt_in_records_six_hook_events_to_temp_research_spark(tmp_path: Path) -> None:
    spark_dir = tmp_path / "sparks"
    env = {
        "LDVH_HOOK_SPARK_CAPTURE": "1",
        "LDVH_HOOK_SPARK_DIR": spark_dir.as_posix(),
    }
    payloads = [
        {"hook_event_name": "SessionStart", "sessionId": "shim-research", "cwd": ROOT.as_posix()},
        {
            "hook_event_name": "PreToolUse",
            "sessionId": "shim-research",
            "cwd": ROOT.as_posix(),
            "toolName": "Read",
            "tool_input": {"file_path": "README.md"},
        },
        {
            "hook_event_name": "PostToolUse",
            "sessionId": "shim-research",
            "cwd": ROOT.as_posix(),
            "toolName": "Read",
            "tool_input": {"file_path": "README.md"},
        },
        {"hook_event_name": "UserPromptSubmit", "sessionId": "shim-research", "cwd": ROOT.as_posix()},
        {"hook_event_name": "Stop", "sessionId": "shim-research", "cwd": ROOT.as_posix()},
        {"hook_event_name": "Notification", "sessionId": "shim-research", "cwd": ROOT.as_posix()},
    ]

    for payload in payloads:
        completed = _run_shim(payload, extra_env=env)
        assert completed.returncode == 0

    files = list(spark_dir.glob("spark-0001-codex-hook-six-event-research-capture.yaml"))
    assert len(files) == 1
    raw = files[0].read_text(encoding="utf-8")

    for event_name in ("SessionStart", "PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop", "Notification"):
        assert f"event={event_name}" in raw
    assert "title: Codex Hook 六类事件研究采样" in raw
    assert "source: codex_hook" in raw
