import importlib.util
import io
import json
import subprocess
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DISPATCHER_PATH = PROJECT_ROOT / "code" / "hook_dispatch.py"
HOOK_REGISTRY_PATH = PROJECT_ROOT / "hooks" / "ldvh-hooks.yaml"
FILE_COMMAND_MAP_PATH = PROJECT_ROOT / "code" / "constants" / "file_command_map.py"


def load_dispatcher():
    spec = importlib.util.spec_from_file_location("hook_dispatch", DISPATCHER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_file_command_map():
    spec = importlib.util.spec_from_file_location("file_command_map", FILE_COMMAND_MAP_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_file_command_map_declares_authorized_suggestions():
    command_map = load_file_command_map()

    assert set(command_map.FILE_COMMAND_MAP) == {"spec", "workcase", "spark", "python", "web"}
    spec_commands = command_map.FILE_COMMAND_MAP["spec"]
    assert spec_commands["before_change"]
    assert spec_commands["after_change"]
    assert "preflight --target-path <path>" in spec_commands["before_change"][0]["command"]
    assert "v2-check --fail-on-diagnostics" in spec_commands["after_change"][0]["command"]
    for file_type in ("workcase", "spark", "python", "web"):
        assert command_map.FILE_COMMAND_MAP[file_type]["before_change"] == []
        assert command_map.FILE_COMMAND_MAP[file_type]["after_change"] == []
        assert "04.Att.02" in command_map.FILE_COMMAND_MAP[file_type]["reason"]
    assert command_map.classify_file_type("specs/04-Code确定性执行规范.md") == "spec"
    assert command_map.classify_file_type("ldvh-base/workcases/workcase-0020-code-command-timing-orchestration.yaml") == "workcase"
    assert command_map.classify_file_type("ldvh-base/sparks/spark-0036-skill-encapsulation-and-trigger-gap.yaml") == "spark"
    assert command_map.classify_file_type("code/hook_dispatch.py") == "python"
    assert command_map.classify_file_type("web/app.tsx") == "web"


def test_hook_registry_declares_dispatcher_entrypoints():
    registry = yaml.safe_load(HOOK_REGISTRY_PATH.read_text(encoding="utf-8"))
    hooks = {hook["event"]: hook for hook in registry["hooks"]}

    assert hooks["git.commit-msg"]["dispatcher_command"][:4] == [
        "python3",
        "code/hook_dispatch.py",
        "run",
        "git.commit-msg",
    ]
    assert hooks["git.commit-msg"]["command"][:2] == ["python3", "code/commit_validate.py"]
    assert "--target" in hooks["session-start"]["dispatcher_command"]
    assert "--target" in hooks["pre-tool-use"]["dispatcher_command"]
    assert "UserPromptSubmit" not in registry["hooks"]
    assert "stdin" in registry["ldvh_asset"]["handoff"]
    assert "payload" in registry["ldvh_asset"]["handoff"]
    assert any("tool_input" in item for item in registry["ldvh_asset"]["verification"])
    assert any("target" in item for item in registry["ldvh_asset"]["verification"])


def test_session_start_limited_receipt_does_not_block(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {
            "result_status": "limited",
            "diagnostics": [
                {
                    "severity": "warning",
                    "code": "V2_PROJECT_FACT_GRAPH_LOAD_FAILED",
                    "message": "fact source parse failed",
                }
            ],
        },
    )

    exit_code = dispatcher.handle_session_start(tmp_path, trigger_source="hook")
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["receipt"] == "limited"
    assert payload["action_policy"] == "fallback_read_plan_required"
    assert payload["diagnostics_policy"] == "continue_with_limited_receipt"
    assert payload["read_plan_source"] == "fallback"
    assert [item["path"] for item in payload["read_plan"]] == [
        "rules/LDVH-RUNTIME-PROTOCOL.md",
        "specs/06-运行时扩展规范.md",
        "specs/attachments/06.Att.02-固定运行时扩展登记表.md",
    ]
    assert payload["diagnostics"][0]["code"] == "V2_PROJECT_FACT_GRAPH_LOAD_FAILED"


def test_session_start_falls_back_when_knowledge_map_has_no_required_read_plan(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {
            "result_status": "ok",
            "diagnostics": [],
            "read_plan": [
                {"path": "ldvh-base/sparks/spark-0032-runtime-operation-assurance-hook-agent-deployment.yaml", "priority": "P2"}
            ],
        },
    )

    exit_code = dispatcher.handle_session_start(tmp_path, trigger_source="hook")
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["read_plan_source"] == "fallback"
    assert payload["action_policy"] == "fallback_read_plan_required"
    assert payload["read_plan"][0]["priority"] == "P0"
    assert payload["read_plan"][1]["priority"] == "P1"


def test_run_knowledge_map_failure_returns_structured_error(monkeypatch):
    dispatcher = load_dispatcher()

    class FailedResult:
        returncode = 2
        stderr = "bad start node\nwith details"
        stdout = ""

    monkeypatch.setattr(dispatcher.subprocess, "run", lambda *args, **kwargs: FailedResult())

    payload = dispatcher._run_knowledge_map("missing-node", "general")

    assert payload["status"] == "error"
    assert "failed_command" in payload
    assert payload["exit_code"] == 2
    assert payload["stderr_head"] == "bad start node\nwith details"
    assert "参数" in payload["stderr_summary"]
    assert payload["suggested_action"]


def test_git_text_structured_preserves_error_and_git_text_signature(tmp_path):
    dispatcher = load_dispatcher()

    stdout, error = dispatcher._git_text_structured(tmp_path, ["rev-parse", "--show-toplevel"])

    assert stdout == ""
    assert isinstance(error, dict)
    assert error["status"] == "error"
    assert error["failed_command"].startswith("git -C ")
    assert error["exit_code"] != 0
    assert error["stderr_head"]
    assert error["suggested_action"]
    assert dispatcher._git_text(tmp_path, ["rev-parse", "--show-toplevel"]) == ""


def test_acknowledge_read_plan_blocks_empty_required_paths_for_governed_receipt(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    dispatcher._write_session_receipt(
        "empty-plan",
        "session-start",
        {
            "governed": True,
            "cwd": str(tmp_path),
            "read_plan": [],
        },
    )

    exit_code = dispatcher.handle_acknowledge_read_plan(tmp_path, trigger_source="rules", session_id="empty-plan")
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["acknowledged"] is False
    assert payload["blocked"] is True
    assert "空读取计划" in payload["reason"]


def test_acknowledge_action_hint_returns_tool_plan_and_post_read_action(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    dispatcher._write_session_receipt(
        "action-plan",
        "session-start",
        {
            "governed": True,
            "cwd": str(tmp_path),
            "target_paths": [str(tmp_path)],
            "read_plan": [
                {"path": "rules/LDVH-RUNTIME-PROTOCOL.md", "priority": "P0"},
                {"path": "specs/06-运行时扩展规范.md", "priority": "P1"},
            ],
        },
    )

    exit_code = dispatcher.handle_acknowledge_read_plan(
        tmp_path,
        trigger_source="rules",
        session_id="action-plan",
        action_hint="fix",
    )
    payload = json.loads(capsys.readouterr().out)
    receipt = dispatcher._read_session_receipt("action-plan")

    assert exit_code == 0
    assert payload["acknowledged"] is True
    assert payload["task_type"] == "code_change"
    assert payload["tool_plan"]
    assert "测试" in payload["post_read_action"]
    assert receipt["read_plan_consumed"]["action_hint"] == "fix"
    assert receipt["read_plan_consumed"]["target"] == [str(tmp_path)]


def test_acknowledge_unknown_action_hint_is_ambiguous(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    dispatcher._write_session_receipt(
        "unknown-action",
        "session-start",
        {
            "governed": True,
            "cwd": str(tmp_path),
            "read_plan": [{"path": "rules/LDVH-RUNTIME-PROTOCOL.md", "priority": "P0"}],
        },
    )

    exit_code = dispatcher.handle_acknowledge_read_plan(
        tmp_path,
        trigger_source="rules",
        session_id="unknown-action",
        action_hint="unknown",
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["task_type"] == "AMBIGUOUS"
    assert payload["tool_plan"] == []
    assert payload["post_read_action"] == ""


def test_acknowledge_expands_next_queries(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    dispatcher._write_session_receipt(
        "deep-read",
        "session-start",
        {
            "governed": True,
            "cwd": str(tmp_path),
            "read_plan": [{"path": "rules/LDVH-RUNTIME-PROTOCOL.md", "priority": "P0"}],
            "next_queries": [
                {
                    "purpose": "expand_if_needed",
                    "input_scope": "entry_navigation",
                    "layer": "expand",
                    "start_node": "rules/LDVH-RUNTIME-PROTOCOL.md",
                }
            ],
        },
    )

    def fake_knowledge_map(start_node, task_type, **kwargs):
        return {
            "read_plan": [{"path": "specs/06-运行时扩展规范.md", "priority": "P1"}],
            "stop_conditions": [{"condition": "runtime_protocol_stop_points"}],
        }

    monkeypatch.setattr(dispatcher, "_run_knowledge_map", fake_knowledge_map)

    exit_code = dispatcher.handle_acknowledge_read_plan(
        tmp_path,
        trigger_source="rules",
        session_id="deep-read",
        action_hint="fix",
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["deep_read_plan"][0]["path"] == "specs/06-运行时扩展规范.md"
    assert payload["deep_stop_conditions"][0]["condition"] == "runtime_protocol_stop_points"


def test_acknowledge_reuses_existing_guide_receipt_for_same_scope(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    dispatcher._write_session_receipt(
        "dedupe",
        "session-start",
        {
            "governed": True,
            "cwd": str(tmp_path),
            "target_paths": [str(tmp_path)],
            "read_plan": [{"path": "rules/LDVH-RUNTIME-PROTOCOL.md", "priority": "P0"}],
        },
    )

    assert dispatcher.handle_acknowledge_read_plan(
        tmp_path,
        trigger_source="rules",
        session_id="dedupe",
        action_hint="fix",
    ) == 0
    capsys.readouterr()

    exit_code = dispatcher.handle_acknowledge_read_plan(
        tmp_path,
        trigger_source="rules",
        session_id="dedupe",
        action_hint="fix",
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["guide_receipt"] == "found"
    assert "tool_plan" not in payload


def test_session_start_writes_receipt_state(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {"result_status": "ok", "diagnostics": []},
    )

    exit_code = dispatcher.handle_session_start(tmp_path, trigger_source="hook", session_id="session-1")
    payload = json.loads(capsys.readouterr().out)
    receipt = dispatcher._read_session_receipt("session-1")

    assert exit_code == 0
    assert payload["receipt"] == "ok"
    assert receipt["event"] == "session-start"
    assert receipt["result"]["receipt"] == "ok"


def test_session_start_exposes_attention_points_tool_plan_and_next_queries(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {
            "result_status": "ok",
            "diagnostics": [],
            "read_plan": [
                {
                    "path": "ldvh-base/workcases/workcase-0001-pending.yaml",
                    "priority": "P0",
                    "role": "work_object",
                    "title": "Pending WorkCase",
                    "source_relation": "pending_work_object",
                },
                {"path": "rules/start.md", "priority": "P1", "role": "start"},
            ],
            "next_queries": [{"purpose": "expand_if_needed", "start_node": "rules/start.md"}],
        },
    )

    exit_code = dispatcher.handle_session_start(tmp_path, trigger_source="hook")
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert any("未闭环" in point for point in payload["attention_points"])
    assert payload["tool_plan"] == []
    assert payload["next_queries"][0]["purpose"] == "expand_if_needed"


def test_session_start_non_governed_exposes_empty_runtime_guides(tmp_path, capsys):
    dispatcher = load_dispatcher()

    exit_code = dispatcher.handle_session_start(tmp_path, trigger_source="rules")
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["governed"] is False
    assert payload["attention_points"] == []
    assert payload["tool_plan"] == []
    assert payload["next_queries"] == []


def test_session_start_recognizes_git_worktree_as_governed_project(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    repo = tmp_path / "project"
    worktree = tmp_path / "project-worktree"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "ldvh@example.test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "LDVH Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "test: init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "worktree", "add", str(worktree)], cwd=repo, check=True, capture_output=True, text=True)
    common_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text(
        f"""
product_name: LD Vibe Harness
product_description: |
  Test.
projects:
  - id: app
    path: {repo}
    git:
      common_dir: {common_dir}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {"result_status": "ok", "diagnostics": []},
    )

    exit_code = dispatcher.handle_session_start(worktree, trigger_source="hook")
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["governed"] is True
    assert payload["governed_via"] == "git.common_dir"
    assert payload["governed_project_id"] == "app"
    assert payload["config_path"] == str(config)


def test_pre_tool_use_creates_implicit_receipt_when_session_start_missing(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {"result_status": "ok", "diagnostics": []},
    )

    exit_code = dispatcher.handle_pre_tool_use(
        tmp_path,
        trigger_source="hook",
        tool_name="Bash",
        session_id="session-2",
    )
    payload = json.loads(capsys.readouterr().out)
    receipt = dispatcher._read_session_receipt("session-2")

    assert exit_code == 0
    assert payload["session_receipt"] == "created_by_pre_tool_use"
    assert payload["receipt"] == "ok"
    assert receipt["event"] == "pre-tool-use-implicit-session-start"


def test_pre_tool_use_marks_existing_receipt_when_found(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {"result_status": "ok", "diagnostics": []},
    )

    assert dispatcher.handle_session_start(tmp_path, trigger_source="hook", session_id="session-4") == 0
    capsys.readouterr()
    exit_code = dispatcher.handle_pre_tool_use(
        tmp_path,
        trigger_source="hook",
        tool_name="Bash",
        session_id="session-4",
    )
    payload = json.loads(capsys.readouterr().out)
    receipt = dispatcher._read_session_receipt("session-4")

    assert exit_code == 0
    assert payload["session_receipt"] == "found"
    assert receipt["event"] == "session-start"
    assert receipt["last_pre_tool_use"]["event"] == "pre-tool-use"
    assert receipt["last_pre_tool_use"]["tool"] == "Bash"
    assert receipt["events"][-1]["session_receipt"] == "found"


def test_pre_tool_use_blocks_write_until_read_plan_acknowledged(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {
            "result_status": "ok",
            "diagnostics": [],
            "read_plan": [
                {"path": "rules/LDVH-RUNTIME-PROTOCOL.md", "priority": "P0"},
                {"path": "specs/06-运行时扩展规范.md", "priority": "P1"},
                {"path": "ldvh-base/sparks/spark-0032-runtime-operation-assurance-hook-agent-deployment.yaml", "priority": "P2"},
            ],
        },
    )

    assert dispatcher.handle_session_start(tmp_path, trigger_source="hook", session_id="session-5") == 0
    capsys.readouterr()

    blocked_code = dispatcher.handle_pre_tool_use(
        tmp_path,
        trigger_source="hook",
        tool_name="Write",
        session_id="session-5",
        targets=[tmp_path / "changed.txt"],
    )
    blocked = json.loads(capsys.readouterr().out)

    assert blocked_code == 1
    assert blocked["blocked"] is True
    assert blocked["required_paths"] == [
        "rules/LDVH-RUNTIME-PROTOCOL.md",
        "specs/06-运行时扩展规范.md",
    ]

    assert dispatcher.handle_acknowledge_read_plan(tmp_path, trigger_source="rules", session_id="session-5") == 0
    ack = json.loads(capsys.readouterr().out)
    assert ack["acknowledged"] is True

    exit_code = dispatcher.handle_pre_tool_use(
        tmp_path,
        trigger_source="hook",
        tool_name="Write",
        session_id="session-5",
        targets=[tmp_path / "changed.txt"],
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["blocked"] is False
    assert payload["read_plan_consumed"] == "acknowledged"


def test_pre_tool_use_blocks_write_when_target_unknown(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()

    exit_code = dispatcher.handle_pre_tool_use(
        tmp_path,
        trigger_source="hook",
        tool_name="Write",
        session_id="session-unknown",
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["blocked"] is True
    assert payload["blocked_reason"] == "unknown_target"


def test_pre_tool_use_blocks_mutating_bash_until_read_plan_acknowledged(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": []},
    )

    assert dispatcher.handle_session_start(tmp_path, trigger_source="hook", session_id="session-6") == 0
    capsys.readouterr()

    exit_code = dispatcher.handle_pre_tool_use(
        tmp_path,
        trigger_source="hook",
        tool_name="Bash",
        session_id="session-6",
        tool_command="cat > changed.txt",
        targets=[tmp_path / "changed.txt"],
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["blocked"] is True
    assert payload["tool"] == "Bash"


def test_pre_tool_use_target_under_project_is_governed_from_workspace_root(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    workspace = tmp_path / "workspace"
    project = workspace / "ldvh"
    project.mkdir(parents=True)
    config = project / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - id: ldvh\n    path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": []},
    )

    assert dispatcher.handle_session_start(project, trigger_source="rules", session_id="session-target") == 0
    capsys.readouterr()
    assert dispatcher.handle_acknowledge_read_plan(project, trigger_source="rules", session_id="session-target") == 0
    capsys.readouterr()

    exit_code = dispatcher.handle_pre_tool_use(
        workspace,
        trigger_source="rules",
        tool_name="Write",
        session_id="session-target",
        targets=[project / "code" / "hook_dispatch.py"],
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["governed"] is True
    assert payload["governed_project_id"] == "ldvh"
    assert payload["subject_source"] == "target"
    assert payload["target_resolutions"][0]["status"] == "governed"


def test_session_start_discovers_subproject_from_workspace_root(monkeypatch, tmp_path, capsys):
    """SessionStart from workspace root should discover governed subprojects
    listed in the root config under cwd-fallback mode."""
    dispatcher = load_dispatcher()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subproject = workspace / "governed-app"
    subproject.mkdir()

    # Root config lists the subproject
    config = workspace / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text(
        f"projects:\n  - id: governed-app\n    path: {subproject}\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": [
            {"path": "rules/start.md", "priority": "P0", "role": "start"},
        ]},
    )

    # SessionStart from workspace root — no explicit targets
    exit_code = dispatcher.handle_session_start(workspace, trigger_source="rules", session_id="cwd-sub")
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["governed"] is True
    assert payload["governed_project_id"] == "governed-app"
    assert payload["subject_source"] == "cwd-subproject"
    assert len(payload["target_resolutions"]) >= 1
    assert payload["target_resolutions"][0]["status"] == "governed"
    assert payload["target_resolutions"][0]["governed_via"] == "path"


def test_hook_payload_and_rules_cli_target_have_same_governance(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    project = tmp_path / "project"
    project.mkdir()
    (project / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "projects:\n  - id: app\n    path: .\n",
        encoding="utf-8",
    )
    target = project / "file.txt"

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_run_knowledge_map", lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": []})
    assert dispatcher.handle_session_start(project, trigger_source="rules", session_id="session-parity") == 0
    capsys.readouterr()
    assert dispatcher.handle_acknowledge_read_plan(project, trigger_source="rules", session_id="session-parity") == 0
    capsys.readouterr()

    rules_code = dispatcher.main([
        "run",
        "pre-tool-use",
        "--cwd",
        str(tmp_path),
        "--target",
        str(target),
        "--tool-name",
        "Write",
        "--session-id",
        "session-parity",
    ])
    rules_payload = json.loads(capsys.readouterr().out)

    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "cwd": str(tmp_path),
                    "session_id": "session-parity",
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(target)},
                }
            )
        ),
    )
    hook_code = dispatcher.main([])
    hook_payload = json.loads(capsys.readouterr().out)

    assert rules_code == 0
    assert hook_code == 0
    for key in ("governed_subject", "governed_via", "governed_project_id", "blocked"):
        assert hook_payload[key] == rules_payload[key]
    assert hook_payload["target_paths"] == rules_payload["target_paths"]
    assert hook_payload["target_resolutions"][0]["status"] == rules_payload["target_resolutions"][0]["status"]
    assert hook_payload["event"] == rules_payload["event"] == "pre-tool-use"


def test_target_outside_governed_project_noops(tmp_path, capsys):
    dispatcher = load_dispatcher()
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "projects:\n  - id: app\n    path: .\n",
        encoding="utf-8",
    )

    exit_code = dispatcher.handle_pre_tool_use(
        project,
        trigger_source="rules",
        tool_name="Bash",
        targets=[outside / "README.md"],
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["blocked"] is False
    assert payload["governed"] is False
    assert payload["target_resolutions"][0]["status"] == "not_governed"


def test_same_project_multiple_targets_are_allowed(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    project = tmp_path / "project"
    project.mkdir()
    (project / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "projects:\n  - id: app\n    path: .\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_run_knowledge_map", lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": []})
    assert dispatcher.handle_session_start(project, session_id="multi-same") == 0
    capsys.readouterr()
    assert dispatcher.handle_acknowledge_read_plan(project, session_id="multi-same") == 0
    capsys.readouterr()

    exit_code = dispatcher.handle_pre_tool_use(
        project,
        tool_name="Write",
        session_id="multi-same",
        targets=[project / "a.txt", project / "b.txt"],
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["blocked"] is False
    assert len(payload["target_resolutions"]) == 2


def test_mixed_governed_and_ungoverned_targets_block(tmp_path, capsys):
    dispatcher = load_dispatcher()
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "projects:\n  - id: app\n    path: .\n",
        encoding="utf-8",
    )

    exit_code = dispatcher.handle_pre_tool_use(
        project,
        tool_name="Bash",
        targets=[project / "a.txt", outside / "b.txt"],
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["blocked_reason"] == "mixed_governed_and_ungoverned_targets"


def test_multiple_governed_projects_block_even_without_ids(tmp_path, capsys):
    dispatcher = load_dispatcher()
    workspace = tmp_path / "workspace"
    one = workspace / "one"
    two = workspace / "two"
    one.mkdir(parents=True)
    two.mkdir()
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "projects:\n  - path: one\n  - path: two\n",
        encoding="utf-8",
    )

    exit_code = dispatcher.handle_pre_tool_use(
        workspace,
        tool_name="Bash",
        targets=[one / "a.txt", two / "b.txt"],
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["blocked_reason"] == "multiple_governed_projects"


def test_git_worktree_file_target_matches_common_dir(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    repo = tmp_path / "project"
    worktree = tmp_path / "project-worktree"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "ldvh@example.test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "LDVH Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "test: init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "worktree", "add", str(worktree)], cwd=repo, check=True, capture_output=True, text=True)
    common_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text(
        f"projects:\n  - id: app\n    path: {repo}\n    git:\n      common_dir: {common_dir}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_run_knowledge_map", lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": []})
    assert dispatcher.handle_session_start(worktree, session_id="wt-file") == 0
    capsys.readouterr()
    assert dispatcher.handle_acknowledge_read_plan(worktree, session_id="wt-file") == 0
    capsys.readouterr()

    exit_code = dispatcher.handle_pre_tool_use(
        tmp_path,
        tool_name="Write",
        session_id="wt-file",
        targets=[worktree / "README.md"],
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["governed"] is True
    assert payload["governed_via"] == "git.common_dir"


def test_git_commit_msg_blocks_until_latest_read_plan_acknowledged(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        dispatcher,
        "_run_knowledge_map",
        lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": []},
    )
    monkeypatch.setattr(dispatcher, "run_event", lambda event, registry, context, dry_run=False: 0)

    assert dispatcher.handle_session_start(tmp_path, trigger_source="hook", session_id="session-7") == 0
    capsys.readouterr()

    message = tmp_path / "message.txt"
    message.write_text("test: commit\n", encoding="utf-8")
    blocked_code = dispatcher.main([
        "run",
        "git.commit-msg",
        "--cwd",
        str(tmp_path),
        "--message-file",
        str(message),
    ])
    blocked = json.loads(capsys.readouterr().out)

    assert blocked_code == 1
    assert blocked["blocked"] is True
    assert blocked["action"] == "git.commit-msg"

    assert dispatcher.handle_acknowledge_read_plan(tmp_path, trigger_source="rules", session_id="session-7") == 0
    capsys.readouterr()

    exit_code = dispatcher.main([
        "run",
        "git.commit-msg",
        "--cwd",
        str(tmp_path),
        "--message-file",
        str(message),
    ])

    assert exit_code == 0


def test_git_commit_msg_uses_repo_root_and_staged_paths_not_message_file(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "ldvh@example.test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "LDVH Test"], cwd=repo, check=True)
    (repo / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "projects:\n  - id: app\n    path: .\n",
        encoding="utf-8",
    )
    (repo / "changed.txt").write_text("changed\n", encoding="utf-8")
    subprocess.run(["git", "add", "changed.txt"], cwd=repo, check=True)
    message = tmp_path / "message.txt"
    message.write_text("feat: 提交测试\n", encoding="utf-8")
    captured = {}

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_run_knowledge_map", lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": []})
    def fake_run_event(event, registry, context, dry_run=False):
        captured["context"] = context
        return 0

    monkeypatch.setattr(dispatcher, "run_event", fake_run_event)
    assert dispatcher.handle_session_start(repo, session_id="commit-target") == 0
    capsys.readouterr()
    assert dispatcher.handle_acknowledge_read_plan(repo, session_id="commit-target") == 0
    capsys.readouterr()

    exit_code = dispatcher.main([
        "run",
        "git.commit-msg",
        "--cwd",
        str(repo / "subdir"),
        "--message-file",
        str(message),
    ])

    assert exit_code == 0
    assert captured["context"]["repo_root"] == str(repo)
    assert captured["context"]["message_file"] == str(message)


def test_cli_event_survives_codex_stdin_payload_without_event(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(dispatcher, "_governed_project_match", lambda cwd, config_path: {"governed": True})
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(json.dumps({"cwd": str(tmp_path), "tool_name": "Bash"})),
    )

    exit_code = dispatcher.main(["run", "pre-tool-use", "--trigger-source", "hook"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["blocked"] is False
    assert payload["governed"] is True
    assert payload["trigger_source"] == "hook"


def test_cli_event_wins_over_unrecognized_codex_stdin_event(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(dispatcher, "_governed_project_match", lambda cwd, config_path: {"governed": True})
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(json.dumps({"event": "unexpected-shape", "cwd": str(tmp_path)})),
    )

    exit_code = dispatcher.main(["run", "pre-tool-use", "--trigger-source", "hook"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["blocked"] is False
    assert payload["governed"] is True


def test_codex_hook_event_name_stdin_payload_routes_to_builtin_handler(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    config = tmp_path / "LDVH-GOVERNED-PROJECTS.yaml"
    config.write_text("projects:\n  - path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_find_governed_config", lambda cwd: config)
    monkeypatch.setattr(dispatcher, "_cwd_in_governed_project", lambda cwd, config_path: True)
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "cwd": str(tmp_path),
                    "session_id": "session-3",
                    "tool_name": "Bash",
                }
            )
        ),
    )

    exit_code = dispatcher.main([])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["blocked"] is False
    assert payload["tool"] == "Bash"
    assert payload["trigger_source"] == "hook"
    assert payload["session_receipt"] == "created_by_pre_tool_use"



def test_hook_payload_gap_is_reported_for_governed_read_without_target(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    project = tmp_path / "project"
    project.mkdir()
    (project / "LDVH-GOVERNED-PROJECTS.yaml").write_text("projects:\n  - id: app\n    path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_run_knowledge_map", lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": []})
    assert dispatcher.handle_session_start(project, trigger_source="hook", session_id="session-gap") == 0
    capsys.readouterr()
    assert dispatcher.handle_acknowledge_read_plan(project, trigger_source="hook", session_id="session-gap") == 0
    capsys.readouterr()

    exit_code = dispatcher.handle_pre_tool_use(
        project,
        trigger_source="hook",
        tool_name="Bash",
        session_id="session-gap",
        tool_command="pwd",
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["blocked"] is False
    assert payload["payload_present"] is False
    assert payload["diagnostics"][0]["code"] == "HOOK_ADAPTER_PAYLOAD_GAP"
    assert payload["diagnostics"][0]["payload_present"] is False



def test_hook_payload_gap_blocking_write_keeps_unknown_target(monkeypatch, tmp_path, capsys):
    dispatcher = load_dispatcher()
    project = tmp_path / "project"
    project.mkdir()
    (project / "LDVH-GOVERNED-PROJECTS.yaml").write_text("projects:\n  - id: app\n    path: .\n", encoding="utf-8")

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.setattr(dispatcher, "_run_knowledge_map", lambda start_node, task_type: {"result_status": "ok", "diagnostics": [], "read_plan": []})
    assert dispatcher.handle_session_start(project, trigger_source="hook", session_id="session-gap-write") == 0
    capsys.readouterr()

    exit_code = dispatcher.handle_pre_tool_use(
        project,
        trigger_source="hook",
        tool_name="Write",
        session_id="session-gap-write",
        tool_command="apply_patch",
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["blocked_reason"] == "unknown_target"
    assert payload["diagnostics"][0]["code"] == "HOOK_ADAPTER_PAYLOAD_GAP"



def test_hook_payload_gap_not_reported_for_non_governed_noop(tmp_path, capsys):
    dispatcher = load_dispatcher()
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / "LDVH-GOVERNED-PROJECTS.yaml").write_text("projects:\n  - id: app\n    path: .\n", encoding="utf-8")

    exit_code = dispatcher.handle_pre_tool_use(
        project,
        trigger_source="hook",
        tool_name="Bash",
        targets=[outside / "README.md"],
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["blocked"] is False
    assert payload["governed"] is False
    assert "diagnostics" not in payload
