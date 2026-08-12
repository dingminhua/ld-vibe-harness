from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ldvh.hooks.workcase_stop import (
    BINDING_ENV,
    HandoffVerdict,
    HookDecision,
    WorkCaseBinding,
    decide,
    binding_path,
    evaluate,
    main,
    parse_binding,
    parse_stop_input,
    read_session_binding,
)

BINDING = WorkCaseBinding("sample", "workcase-0047")
BINDING_JSON = json.dumps(BINDING.to_json())


def _stop(*, active: bool = False) -> str:
    return json.dumps(
        {
            "stop_hook_active": active,
            "session_id": "session-1",
            "transcript_path": "/tmp/transcript.jsonl",
            "cwd": "/project",
            "permission_mode": "default",
            "hook_event_name": "Stop",
        }
    )


def test_parse_stop_input_requires_a_boolean_active_flag() -> None:
    parsed = parse_stop_input(_stop())
    assert parsed.stop_hook_active is False
    assert parsed.cwd == "/project"

    import pytest

    from ldvh.hooks.workcase_stop import WorkCaseStopHookError

    with pytest.raises(WorkCaseStopHookError):
        parse_stop_input("not-json")
    with pytest.raises(WorkCaseStopHookError):
        parse_stop_input(json.dumps({"stop_hook_active": "yes"}))


def test_parse_binding_only_accepts_an_exact_workcase_binding() -> None:
    assert parse_binding(None) is None
    assert parse_binding("not-json") is None
    assert parse_binding(json.dumps({"governed_project_id": "sample"})) is None
    assert parse_binding(json.dumps({"governed_project_id": "sample", "fact_type_key": "spark", "object_id": "spark-1"})) is None
    assert parse_binding(json.dumps({"governed_project_id": "sample", "fact_type_key": "workcase", "object_id": "workcase-invalid"})) is None
    assert parse_binding(BINDING_JSON) == BINDING


def test_session_binding_path_is_exact_and_malformed_files_fail_open(tmp_path: Path) -> None:
    path = binding_path(tmp_path, "session-1")
    assert path == tmp_path / ".ldvh-stop-bindings" / "session-1.json"
    assert binding_path(tmp_path, "../escape") is None
    assert read_session_binding(tmp_path, "session-1") is None
    assert path is not None
    path.parent.mkdir()
    path.write_text(BINDING_JSON, encoding="utf-8")
    assert read_session_binding(tmp_path, "session-1") == BINDING
    path.write_text("not-json", encoding="utf-8")
    assert read_session_binding(tmp_path, "session-1") is None


def test_decide_fails_open_without_binding_or_verdict() -> None:
    assert decide(parse_stop_input(_stop()), None, None) == HookDecision("continue")
    assert decide(parse_stop_input(_stop()), BINDING, None) == HookDecision("continue")
    assert decide(parse_stop_input(_stop(active=True)), BINDING, HandoffVerdict(False, "controller_owned", "advance_current_work_item")) == HookDecision("continue")


def test_decide_blocks_only_controller_owned_verdicts() -> None:
    allowed = HandoffVerdict(True, "gate2_waiting", "human_gate_2")
    assert decide(parse_stop_input(_stop()), BINDING, allowed) == HookDecision("continue")

    blocked = decide(
        parse_stop_input(_stop()),
        BINDING,
        HandoffVerdict(False, "controller_owned", "form_complete_result_projection"),
    )
    assert blocked.decision == "block"
    assert blocked.reason is not None
    assert "form_complete_result_projection" in blocked.reason


def test_evaluate_fails_open_on_runner_failure() -> None:
    def boom(binding, cwd):
        del binding, cwd
        raise RuntimeError("helper unavailable")

    decision = evaluate(parse_stop_input(_stop()), BINDING, boom)
    assert decision == HookDecision("continue")


def test_evaluate_uses_the_runner_verdict() -> None:
    def runner(binding, cwd):
        assert binding == BINDING
        assert cwd == "/project"
        return HandoffVerdict(False, "controller_owned", "advance_current_work_item")

    assert evaluate(parse_stop_input(_stop()), BINDING, runner).decision == "block"
    assert evaluate(parse_stop_input(_stop()), None, runner) == HookDecision("continue")


def _run_main(stdin: str, env: dict[str, str]) -> dict[str, object]:
    return json.loads(main(stdin=stdin, env=env))


def test_main_outputs_continue_json_without_binding_and_for_invalid_stdin(capsys) -> None:
    assert main(stdin=_stop(), env={}) == 0
    assert json.loads(capsys.readouterr().out) == {"decision": "continue"}

    assert main(stdin="not-json", env={BINDING_ENV: BINDING_JSON}) == 0
    assert json.loads(capsys.readouterr().out) == {"decision": "continue"}


def test_main_blocks_only_when_bound_and_controller_owned(monkeypatch, capsys) -> None:
    import ldvh.hooks.workcase_stop as module

    def fake_runner(repository_root):
        del repository_root

        def invoke(binding, cwd):
            del binding, cwd
            return HandoffVerdict(False, "controller_owned", "form_complete_result_projection")

        return invoke

    monkeypatch.setattr(module, "make_cli_runner", fake_runner)

    assert main(stdin=_stop(), env={BINDING_ENV: BINDING_JSON}) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["decision"] == "block"
    assert "form_complete_result_projection" in payload["reason"]


def test_project_stop_gate_assets_are_tracked_and_executable() -> None:
    root = Path(__file__).resolve().parents[3]
    wrapper = root / ".claude" / "hooks" / "ldvh-workcase-stop.py"
    settings = root / ".claude" / "settings.json"
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(wrapper.relative_to(root)), str(settings.relative_to(root))],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert tracked.returncode == 0, tracked.stderr
    assert wrapper.stat().st_mode & 0o111
    configured = json.loads(settings.read_text(encoding="utf-8"))
    assert configured["hooks"]["Stop"][0]["hooks"][0]["command"] == "python3 .claude/hooks/ldvh-workcase-stop.py"


def test_wrapper_process_continues_without_binding(tmp_path: Path) -> None:
    wrapper = Path(__file__).resolve().parents[3] / ".claude" / "hooks" / "ldvh-workcase-stop.py"
    assert wrapper.is_file()
    completed = subprocess.run(
        ["python3", str(wrapper)],
        input=_stop(),
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout) == {"decision": "continue"}
