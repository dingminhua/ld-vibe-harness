import importlib.util
import json
import subprocess
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "code" / "hook_adapter.py"
spec = importlib.util.spec_from_file_location("hook_adapter", MODULE_PATH)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def test_find_dispatcher_prefers_adapter_installation_when_cwd_is_parent(tmp_path):
    parent = tmp_path / "workspace"
    governed_project = parent / "governed-project"
    governed_project.mkdir(parents=True)

    dispatcher = adapter.find_dispatcher(parent)

    assert dispatcher == MODULE_PATH.with_name("hook_dispatch.py")


def test_adapter_preserves_parent_cwd_and_child_target(monkeypatch, tmp_path, capsys):
    parent = tmp_path / "workspace"
    child_target = parent / "governed-project" / "README.md"
    child_target.parent.mkdir(parents=True)
    child_target.write_text("# demo\n", encoding="utf-8")
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(parent),
        "session_id": "adapter-parent-child",
        "tool_name": "Bash",
        "tool_input": {"file_path": str(child_target)},
    }
    observed = {}

    def fake_run(cmd, *, input, text, capture_output):
        observed["cmd"] = cmd
        observed["input"] = input
        observed["text"] = text
        observed["capture_output"] = capture_output
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout=json.dumps({"governed": True, "target_paths": [str(child_target)]}),
            stderr="",
        )

    monkeypatch.setattr("sys.stdin", type("Stdin", (), {"read": lambda self: json.dumps(payload)})())
    monkeypatch.setattr("sys.argv", ["hook_adapter.py", "pre-tool-use"])
    monkeypatch.setattr(adapter.subprocess, "run", fake_run)

    exit_code = adapter.main()

    assert exit_code == 0
    assert observed["cmd"][1] == str(MODULE_PATH.with_name("hook_dispatch.py"))
    assert observed["cmd"][2:5] == ["run", "pre-tool-use", "--trigger-source"]
    assert observed["input"] == json.dumps(payload)
    assert observed["capture_output"] is True
    assert json.loads(capsys.readouterr().out)["target_paths"] == [str(child_target)]
