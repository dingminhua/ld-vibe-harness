import importlib.util
import io
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DISPATCHER_PATH = PROJECT_ROOT / "code" / "hook_dispatch.py"


def load_dispatcher():
    spec = importlib.util.spec_from_file_location("hook_dispatch", DISPATCHER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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
    assert payload["action_policy"] == "continue_with_limited_receipt"
    assert payload["diagnostics"][0]["code"] == "V2_PROJECT_FACT_GRAPH_LOAD_FAILED"


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
