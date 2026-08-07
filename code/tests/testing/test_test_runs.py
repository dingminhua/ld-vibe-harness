from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from ldvh.testing import test_runs as runs_module
from ldvh.testing.test_runs import plan_commands
from ldvh.testing.working_tree_capture import (
    BoundaryDiagnostic,
    BoundaryResolution,
    GovernedWorktreeBoundary,
    ManifestCapture,
)
from ldvh.testing.working_tree_evidence import (
    current_complete_coverage,
    finalize_working_tree_evidence,
    manifest_fingerprint,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOOL = PROJECT_ROOT / "tools" / "run_full_tests.py"


def _manifest(content: bytes = b"same") -> dict[str, Any]:
    coverage = current_complete_coverage()
    files = [{"path": "input.txt", "size_bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}]
    return {
        "observed_at": "2026-07-20T08:00:00+08:00",
        "status": "complete",
        "manifest_fingerprint": manifest_fingerprint(files, coverage["policy_fingerprint"]),
        "file_count": 1,
        "byte_count": len(content),
        "files": files,
    }


def _boundary(workspace: Path, common: Path | None = None) -> GovernedWorktreeBoundary:
    return GovernedWorktreeBoundary("ldvh", workspace, common or workspace.parent / "main.git")


def _capture(content: bytes = b"same") -> ManifestCapture:
    return ManifestCapture(manifest=_manifest(content), coverage=current_complete_coverage(), diagnostics=())


def _incomplete_capture() -> ManifestCapture:
    coverage = current_complete_coverage()
    coverage.update(
        {
            "status": "incomplete",
            "gaps": [
                {
                    "stage": "after",
                    "path": "input.txt",
                    "code": "read_unavailable",
                    "summary": "input could not be read completely",
                }
            ],
        }
    )
    manifest = _manifest()
    manifest.update({"status": "incomplete", "manifest_fingerprint": None})
    return ManifestCapture(manifest=manifest, coverage=coverage, diagnostics=())


def _v2_record(
    tmp_path: Path,
    *,
    steps: list[dict[str, Any]],
    before: bytes = b"same",
    fixed_steps: bool = False,
    bind_run_identity: bool = False,
) -> tuple[dict[str, Any], Path, Path]:
    run_id = "run-" + "c" * 32
    if bind_run_identity and tmp_path.name != run_id:
        tmp_path = tmp_path / run_id
        tmp_path.mkdir(parents=True)
    record_path = tmp_path / "record.json"
    output_path = tmp_path / "output.log"
    boundary = _boundary(tmp_path)
    record = {
        "contract": "ldvh-test-run/2",
        "run_id": run_id,
        "plan": "full-v4",
        "status": "running",
        "evidence_complete": False,
        "started_at": "2026-07-20T08:00:00+08:00",
        "ended_at": None,
        "final_exit_code": None,
        "raw_output_path": str(output_path),
        "record_path": str(record_path),
        "workspace": str(tmp_path),
        "steps": _fixed_steps(tmp_path, steps) if fixed_steps else steps,
        "working_tree_evidence": None,
        "working_tree_capture_checkpoint": {
            **boundary.to_json(),
            "coverage": current_complete_coverage(),
            "before": _manifest(before),
            "capture_diagnostics": [],
        },
        "diagnostics": [],
    }
    record_path.write_text(json.dumps(record), encoding="utf-8")
    return record, record_path, output_path


def _step(status: str, exit_code: int | None) -> dict[str, Any]:
    started_at = None if status == "not_run" else "2026-07-20T08:00:00+08:00"
    ended_at = None if status in {"not_run", "running"} else "2026-07-20T08:00:01+08:00"
    return {
        "name": "check",
        "cwd": "/workspace",
        "argv": ["check"],
        "status": status,
        "started_at": started_at,
        "ended_at": ended_at,
        "exit_code": exit_code,
    }


def _fixed_steps(workspace: Path, outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    commands = plan_commands(workspace, "full-v4", 1)
    steps: list[dict[str, Any]] = []
    for index, command in enumerate(commands):
        outcome = outcomes[index] if index < len(outcomes) else _step("not_run", None)
        steps.append(
            {
                **command,
                "status": outcome["status"],
                "started_at": outcome["started_at"],
                "ended_at": outcome["ended_at"],
                "exit_code": outcome["exit_code"],
            }
        )
    return steps


def _set_all_steps_passed(record: dict[str, Any]) -> None:
    for step in record["steps"]:
        step.update(
            {
                "status": "passed",
                "started_at": "2026-07-20T08:00:00+08:00",
                "ended_at": "2026-07-20T08:00:01+08:00",
                "exit_code": 0,
            }
        )


def _finish_valid_v2_passed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], Path, Path]:
    record, record_path, output_path = _v2_record(
        tmp_path, steps=[_step("not_run", None)], fixed_steps=True, bind_run_identity=True
    )
    boundary = _boundary(Path(record["workspace"]))

    def execute(current: dict[str, Any], _path: Path, log: Any) -> None:
        _set_all_steps_passed(current)
        log.write(b"complete raw output\n")

    monkeypatch.setattr(runs_module, "_execute_steps", execute)
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=boundary, diagnostics=()),
    )
    monkeypatch.setattr(runs_module, "capture_manifest", lambda *_args: _capture())
    runs_module._run_worker_v2(record, record_path, output_path)
    return json.loads(record_path.read_text(encoding="utf-8")), record_path, output_path


def _tool_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_full_tests", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call(*arguments: str) -> tuple[int, dict[str, object]]:
    completed = subprocess.run(
        [sys.executable, str(TOOL), *arguments],
        cwd=PROJECT_ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert completed.stderr == ""
    return completed.returncode, json.loads(completed.stdout)


def test_full_plan_has_fixed_argv_steps_and_no_shell() -> None:
    commands = plan_commands(PROJECT_ROOT, "full-v4", 3)
    assert [command["name"] for command in commands] == [
        "code-lint",
        "code-tests",
        "fact-integrity",
        "web-typecheck",
        "web-tests",
        "web-build",
    ]
    assert all(isinstance(command["argv"], list) and command["argv"] for command in commands)
    assert all("shell" not in command for command in commands)


def test_detached_probe_can_be_read_after_the_launcher_has_exited(tmp_path: Path) -> None:
    code, started = _call("start", "--plan", "probe", "--probe-seconds", "1", "--runs-root", str(tmp_path))
    assert code == 0
    assert started["run_id"] and started["started_at"] and started["raw_output_path"]
    assert started["final_exit_code"] is None
    run_id = str(started["run_id"])
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        code, result = _call("status", "--run-id", run_id, "--runs-root", str(tmp_path))
        if result["status"] in {"passed", "failed", "unknown"}:
            break
        time.sleep(0.1)
    assert code == 0
    assert result["status"] == "passed"
    assert result["evidence_complete"] is True and result["final_exit_code"] == 0 and result["ended_at"]
    assert "probe worker finished" in Path(str(result["raw_output_path"])).read_text(encoding="utf-8")


def test_missing_worker_before_terminal_record_is_explicitly_unknown(tmp_path: Path) -> None:
    module = _tool_module()
    run_id = "run-" + "a" * 32
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    (run_dir / "record.json").write_text(
        json.dumps(
            {
                "contract": "ldvh-test-run/1",
                "run_id": run_id,
                "status": "running",
                "evidence_complete": False,
                "started_at": "2026-01-01T00:00:00+00:00",
                "ended_at": None,
                "final_exit_code": None,
                "worker_pid": 999_999_999,
            }
        ),
        encoding="utf-8",
    )
    observed = module.observe_run(runs_root=tmp_path, run_id=run_id)
    assert observed["status"] == "unknown" and observed["evidence_complete"] is False
    assert observed["final_exit_code"] is None and "worker is absent" in observed["observation_error"]


def test_terminal_result_without_raw_output_is_explicitly_unknown(tmp_path: Path) -> None:
    module = _tool_module()
    run_id = "run-" + "b" * 32
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    (run_dir / "record.json").write_text(
        json.dumps(
            {
                "contract": "ldvh-test-run/1",
                "run_id": run_id,
                "status": "passed",
                "evidence_complete": True,
                "started_at": "2026-01-01T00:00:00+00:00",
                "ended_at": "2026-01-01T00:01:00+00:00",
                "final_exit_code": 0,
                "raw_output_path": str(run_dir / "absent.log"),
            }
        ),
        encoding="utf-8",
    )

    observed = module.observe_run(runs_root=tmp_path, run_id=run_id)

    assert observed["status"] == "unknown" and observed["evidence_complete"] is False
    assert observed["final_exit_code"] is None and "raw output cannot be read" in observed["observation_error"]


def test_full_v4_rejects_nonfixed_runs_root_before_creating_a_run(tmp_path: Path) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    custom = tmp_path / "custom-runs"

    with pytest.raises(ValueError, match="runs_root"):
        runs_module.start_run(
            workspace=workspace,
            runs_root=custom,
            plan="full-v4",
            probe_seconds=1,
            tool_path=TOOL,
        )

    assert not custom.exists()


def test_cli_reports_full_v4_request_errors_with_exit_two(tmp_path: Path) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    custom = tmp_path / "custom-runs"

    code, response = _call(
        "start",
        "--plan",
        "full-v4",
        "--workspace",
        str(workspace),
        "--runs-root",
        str(custom),
    )

    assert code == 2
    assert response["status"] == "unknown"
    assert "runs_root" in str(response["observation_error"])
    assert not custom.exists()


def test_cli_reads_v2_unknown_as_a_conclusion_not_a_request_error(tmp_path: Path) -> None:
    run_id = "run-" + "e" * 32
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    record = {
        "contract": "ldvh-test-run/2",
        "run_id": run_id,
        "plan": "full-v4",
        "status": "unknown",
        "evidence_complete": False,
        "started_at": "2026-07-20T08:00:00+08:00",
        "ended_at": "2026-07-20T08:00:01+08:00",
        "final_exit_code": None,
        "raw_output_path": str(run_dir / "output.log"),
        "record_path": str(run_dir / "record.json"),
        "workspace": str(tmp_path),
        "steps": _fixed_steps(tmp_path, [_step("not_run", None)]),
        "working_tree_evidence": None,
        "diagnostics": [
            {"stage": "identity", "code": "governance_incomplete", "summary": "scope was not resolved"}
        ],
    }
    (run_dir / "record.json").write_text(json.dumps(record), encoding="utf-8")

    code, response = _call("status", "--run-id", run_id, "--runs-root", str(tmp_path))

    assert code == 1
    assert response["contract"] == "ldvh-test-run/2"
    assert response["status"] == "unknown" and response["evidence_complete"] is False


def test_full_v4_persists_v2_checkpoint_before_spawn_and_parent_merges_current_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    runs_root = workspace / ".ldvh-test-runs"
    boundary = _boundary(workspace)

    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=boundary, diagnostics=()),
    )
    monkeypatch.setattr(runs_module, "capture_manifest", lambda *_args: _capture())
    monkeypatch.setattr(runs_module, "_pid_alive", lambda _pid: True)

    class FakeWorker:
        pid = 4321

    def spawn(argv: list[str], **_kwargs: Any) -> FakeWorker:
        run_dir = Path(argv[-1])
        record_path = run_dir / "record.json"
        durable = json.loads(record_path.read_text(encoding="utf-8"))
        assert durable["contract"] == "ldvh-test-run/2"
        assert durable["status"] == "running"
        assert durable["working_tree_capture_checkpoint"]["before"]["status"] == "complete"
        assert durable["working_tree_evidence"] is None
        assert "source" not in durable
        durable["worker_observed_checkpoint"] = True
        record_path.write_text(json.dumps(durable), encoding="utf-8")
        return FakeWorker()

    monkeypatch.setattr(runs_module.subprocess, "Popen", spawn)

    started = runs_module.start_run(
        workspace=workspace,
        runs_root=runs_root,
        plan="full-v4",
        probe_seconds=1,
        tool_path=TOOL,
    )

    assert started["worker_pid"] == 4321
    assert started["worker_observed_checkpoint"] is True
    assert started["contract"] == "ldvh-test-run/2"
    assert "source" not in started


def test_full_v4_governance_failure_is_unknown_without_spawning_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    runs_root = workspace / ".ldvh-test-runs"
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(
            boundary=None,
            diagnostics=(BoundaryDiagnostic("scope_not_governed_single", "scope is not governed"),),
        ),
    )
    monkeypatch.setattr(
        runs_module.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("governance failure must not start a worker"),
    )

    result = runs_module.start_run(
        workspace=workspace,
        runs_root=runs_root,
        plan="full-v4",
        probe_seconds=1,
        tool_path=TOOL,
    )

    assert result["status"] == "unknown"
    assert result["working_tree_evidence"] is None
    assert result["diagnostics"] == [
        {"stage": "identity", "code": "scope_not_governed_single", "summary": "scope is not governed"}
    ]


@pytest.mark.parametrize(
    ("steps", "expected"),
    [
        ([_step("passed", 0), _step("passed", 0)], ("passed", 0)),
        ([_step("passed", 0), _step("failed", 7), _step("not_run", None)], ("failed", 7)),
        ([_step("unknown", None), _step("not_run", None)], ("unknown", None)),
        ([_step("running", None)], ("unknown", None)),
        ([_step("failed", 0)], ("unknown", None)),
    ],
)
def test_step_aggregation_is_a_closed_prefix_matrix(
    steps: list[dict[str, Any]], expected: tuple[str, int | None]
) -> None:
    assert runs_module._aggregate_steps(steps) == expected


@pytest.mark.parametrize(
    ("step_status", "step_exit", "after_bytes", "expected_status", "expected_exit", "evidence_status"),
    [
        ("passed", 0, b"same", "passed", 0, "complete"),
        ("failed", 9, b"same", "failed", 9, "complete"),
        ("passed", 0, b"changed", "unknown", 0, "stale"),
        ("failed", 9, b"changed", "unknown", 9, "stale"),
        ("unknown", None, b"same", "unknown", None, "complete"),
    ],
)
def test_v2_worker_combines_step_and_evidence_status_without_losing_known_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    step_status: str,
    step_exit: int | None,
    after_bytes: bytes,
    expected_status: str,
    expected_exit: int | None,
    evidence_status: str,
) -> None:
    record, record_path, output_path = _v2_record(tmp_path, steps=[_step("not_run", None)])
    boundary = _boundary(tmp_path)

    def execute(current: dict[str, Any], _path: Path, _log: Any) -> None:
        current["steps"][0].update({"status": step_status, "exit_code": step_exit})

    monkeypatch.setattr(runs_module, "_execute_steps", execute)
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=boundary, diagnostics=()),
    )
    monkeypatch.setattr(runs_module, "capture_manifest", lambda *_args: _capture(after_bytes))

    runs_module._run_worker_v2(record, record_path, output_path)
    result = json.loads(record_path.read_text(encoding="utf-8"))

    assert result["status"] == expected_status
    assert result["final_exit_code"] == expected_exit
    assert result["evidence_complete"] is (expected_status in {"passed", "failed"})
    assert result["working_tree_evidence"]["status"] == evidence_status
    assert "working_tree_capture_checkpoint" not in result


def test_v2_worker_forms_incomplete_dto_when_after_identity_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, record_path, output_path = _v2_record(tmp_path, steps=[_step("not_run", None)])
    different = _boundary(tmp_path, tmp_path / "different.git")

    def execute(current: dict[str, Any], _path: Path, _log: Any) -> None:
        current["steps"][0].update({"status": "passed", "exit_code": 0})

    monkeypatch.setattr(runs_module, "_execute_steps", execute)
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=different, diagnostics=()),
    )
    monkeypatch.setattr(
        runs_module,
        "capture_manifest",
        lambda *_args: pytest.fail("identity mismatch must not compare an after manifest"),
    )

    runs_module._run_worker_v2(record, record_path, output_path)
    result = json.loads(record_path.read_text(encoding="utf-8"))

    assert result["status"] == "unknown" and result["final_exit_code"] == 0
    assert result["working_tree_evidence"]["status"] == "incomplete"
    assert result["working_tree_evidence"]["after"] is None
    assert result["working_tree_evidence"]["coverage"]["gaps"][-1]["code"] == "identity_mismatch"


def test_v2_worker_downgrades_incomplete_after_capture_but_preserves_pass_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, record_path, output_path = _v2_record(tmp_path, steps=[_step("not_run", None)])
    boundary = _boundary(tmp_path)

    def execute(current: dict[str, Any], _path: Path, _log: Any) -> None:
        current["steps"][0].update({"status": "passed", "exit_code": 0})

    monkeypatch.setattr(runs_module, "_execute_steps", execute)
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=boundary, diagnostics=()),
    )
    monkeypatch.setattr(runs_module, "capture_manifest", lambda *_args: _incomplete_capture())

    runs_module._run_worker_v2(record, record_path, output_path)
    result = json.loads(record_path.read_text(encoding="utf-8"))

    assert result["status"] == "unknown" and result["final_exit_code"] == 0
    assert result["working_tree_evidence"]["status"] == "incomplete"
    assert result["working_tree_evidence"]["coverage"]["gaps"][0]["code"] == "read_unavailable"


def test_v2_worker_forms_incomplete_dto_for_policy_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, record_path, output_path = _v2_record(tmp_path, steps=[_step("not_run", None)])
    boundary = _boundary(tmp_path)

    def execute(current: dict[str, Any], _path: Path, _log: Any) -> None:
        current["steps"][0].update({"status": "passed", "exit_code": 0})

    after = _capture()
    after.coverage["policy_fingerprint"] = "0" * 64
    monkeypatch.setattr(runs_module, "_execute_steps", execute)
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=boundary, diagnostics=()),
    )
    monkeypatch.setattr(runs_module, "capture_manifest", lambda *_args: after)

    runs_module._run_worker_v2(record, record_path, output_path)
    result = json.loads(record_path.read_text(encoding="utf-8"))

    evidence = result["working_tree_evidence"]
    assert result["status"] == "unknown" and result["final_exit_code"] == 0
    assert evidence["status"] == "incomplete" and evidence["after"] is None
    assert evidence["coverage"]["gaps"][-1]["code"] == "policy_mismatch"


def test_v2_worker_keeps_checkpoint_if_after_capture_cannot_form_dto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, record_path, output_path = _v2_record(tmp_path, steps=[_step("not_run", None)])
    boundary = _boundary(tmp_path)

    def execute(current: dict[str, Any], _path: Path, _log: Any) -> None:
        current["steps"][0].update({"status": "passed", "exit_code": 0})

    monkeypatch.setattr(runs_module, "_execute_steps", execute)
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=boundary, diagnostics=()),
    )
    monkeypatch.setattr(runs_module, "capture_manifest", lambda *_args: (_ for _ in ()).throw(OSError("lost")))

    runs_module._run_worker_v2(record, record_path, output_path)
    result = json.loads(record_path.read_text(encoding="utf-8"))

    assert result["status"] == "unknown" and result["final_exit_code"] == 0
    assert result["working_tree_evidence"] is None
    assert result["working_tree_capture_checkpoint"]["after_capture_started_at"]
    assert result["diagnostics"][-1]["code"] == "evidence_finalization_failed"


def test_v2_worker_attempts_after_capture_when_step_execution_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, record_path, output_path = _v2_record(tmp_path, steps=[_step("not_run", None)])
    boundary = _boundary(tmp_path)
    after_calls: list[str] = []
    monkeypatch.setattr(runs_module, "_execute_steps", lambda *_args: (_ for _ in ()).throw(OSError("boom")))
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=boundary, diagnostics=()),
    )

    def capture(_boundary_value: GovernedWorktreeBoundary, stage: str) -> ManifestCapture:
        after_calls.append(stage)
        return _capture()

    monkeypatch.setattr(runs_module, "capture_manifest", capture)

    runs_module._run_worker_v2(record, record_path, output_path)
    result = json.loads(record_path.read_text(encoding="utf-8"))

    assert after_calls == ["after"]
    assert result["status"] == "unknown"
    assert result["working_tree_evidence"]["status"] == "complete"
    assert any(item["code"] == "step_execution_interrupted" for item in result["diagnostics"])


@pytest.mark.parametrize(("aggregate", "expected_exit"), [("passed", 0), ("failed", 7)])
def test_v2_worker_execution_interruption_can_never_report_passed_or_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    aggregate: str,
    expected_exit: int,
) -> None:
    record, record_path, output_path = _v2_record(
        tmp_path, steps=[_step("not_run", None)], fixed_steps=True, bind_run_identity=True
    )
    boundary = _boundary(Path(record["workspace"]))

    def interrupted(current: dict[str, Any], _path: Path, _log: Any) -> None:
        if aggregate == "passed":
            _set_all_steps_passed(current)
        else:
            current["steps"][0].update(
                {
                    "status": "failed",
                    "started_at": "2026-07-20T08:00:00+08:00",
                    "ended_at": "2026-07-20T08:00:01+08:00",
                    "exit_code": 7,
                }
            )
        raise OSError("interrupted after a mechanically aggregatable state")

    monkeypatch.setattr(runs_module, "_execute_steps", interrupted)
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=boundary, diagnostics=()),
    )
    monkeypatch.setattr(runs_module, "capture_manifest", lambda *_args: _capture())

    runs_module._run_worker_v2(record, record_path, output_path)
    result = runs_module._read_record(record_path)

    assert result["status"] == "unknown" and result["evidence_complete"] is False
    assert result["final_exit_code"] == expected_exit
    assert result["working_tree_evidence"]["status"] == "complete"
    assert any(item["code"] == "step_execution_interrupted" for item in result["diagnostics"])


def test_v2_worker_raw_output_integrity_failure_forces_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, record_path, output_path = _v2_record(
        tmp_path, steps=[_step("not_run", None)], fixed_steps=True
    )
    boundary = _boundary(tmp_path)

    def execute(current: dict[str, Any], _path: Path, _log: Any) -> None:
        _set_all_steps_passed(current)

    original_read = Path.read_bytes
    monkeypatch.setattr(runs_module, "_execute_steps", execute)
    monkeypatch.setattr(
        runs_module,
        "resolve_capture_boundary",
        lambda _workspace: BoundaryResolution(boundary=boundary, diagnostics=()),
    )
    monkeypatch.setattr(runs_module, "capture_manifest", lambda *_args: _capture())
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda path: (_ for _ in ()).throw(OSError("cannot finalize"))
        if path == output_path
        else original_read(path),
    )

    runs_module._run_worker_v2(record, record_path, output_path)
    result = json.loads(record_path.read_text(encoding="utf-8"))

    assert result["status"] == "unknown" and result["final_exit_code"] == 0
    assert "raw_output_size_bytes" not in result and "raw_output_sha256" not in result
    assert any(item["code"] == "raw_output_finalization_failed" for item in result["diagnostics"])


def test_pid_gate_timeout_executes_zero_steps_and_records_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, record_path, _output_path = _v2_record(
        tmp_path, steps=[_step("not_run", None)], fixed_steps=True, bind_run_identity=True
    )
    record["worker_pid"] = 999_999_999
    record_path.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(runs_module, "WORKER_GATE_TIMEOUT_SECONDS", 0.0)

    assert runs_module._wait_for_worker_assignment(record_path) is None
    result = json.loads(record_path.read_text(encoding="utf-8"))

    assert result["status"] == "unknown"
    assert result["steps"][0]["status"] == "not_run"
    assert result["diagnostics"][-1]["code"] == "worker_pid_gate_timeout"


def test_v2_observer_preserves_known_exit_code_for_worker_and_output_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id = "run-" + "d" * 32
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    record, record_path, output_path = _v2_record(
        run_dir, steps=[_step("failed", 7)], fixed_steps=True
    )
    record.update({"run_id": run_id, "status": "running", "worker_pid": 999_999_999})
    record_path.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(runs_module, "_pid_alive", lambda _pid: False)

    missing_worker = runs_module.observe_run(runs_root=tmp_path, run_id=run_id)
    assert missing_worker["status"] == "unknown" and missing_worker["final_exit_code"] == 7
    assert missing_worker["working_tree_capture_checkpoint"]
    assert missing_worker["diagnostics"][-1]["code"] == "worker_absent"

    record.update(
        {
            "status": "failed",
            "evidence_complete": True,
            "final_exit_code": 7,
            "ended_at": "2026-07-20T08:01:00+08:00",
            "working_tree_evidence": finalize_working_tree_evidence(
                governed_project_id="ldvh",
                git_worktree_root=str(run_dir),
                git_common_dir=str(run_dir.parent / "main.git"),
                coverage=current_complete_coverage(),
                before=_manifest(),
                after=_manifest(),
            ),
            "raw_output_size_bytes": 0,
            "raw_output_sha256": hashlib.sha256(b"").hexdigest(),
        }
    )
    record.pop("working_tree_capture_checkpoint")
    record_path.write_text(json.dumps(record), encoding="utf-8")
    assert not output_path.exists()

    missing_output = runs_module.observe_run(runs_root=tmp_path, run_id=run_id)
    assert missing_output["status"] == "unknown" and missing_output["final_exit_code"] == 7
    assert missing_output["diagnostics"][-1]["code"] == "raw_output_unavailable"


def test_v2_reader_rejects_source_and_invalid_diagnostic_shape(tmp_path: Path) -> None:
    record, record_path, _output_path = _v2_record(
        tmp_path, steps=[_step("not_run", None)], fixed_steps=True, bind_run_identity=True
    )
    record["source"] = {"kind": "git-worktree"}
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="must not contain source"):
        runs_module._read_record(record_path)

    record.pop("source")
    record["diagnostics"] = [{"stage": "worker", "code": "bad", "summary": "bad", "path": "secret"}]
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid field set"):
        runs_module._read_record(record_path)


def test_v2_reader_rejects_checkpoint_drift_and_checkpoint_with_terminal_dto(tmp_path: Path) -> None:
    record, record_path, _output_path = _v2_record(
        tmp_path, steps=[_step("not_run", None)], fixed_steps=True, bind_run_identity=True
    )
    record["working_tree_capture_checkpoint"]["unexpected"] = True
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="checkpoint has an invalid field set"):
        runs_module._read_record(record_path)

    record["working_tree_capture_checkpoint"].pop("unexpected")
    record["working_tree_capture_checkpoint"]["capture_diagnostics"] = [
        {"stage": "before", "path": None, "code": "read_unavailable"}
    ]
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="capture diagnostic has an invalid field set"):
        runs_module._read_record(record_path)

    record["working_tree_capture_checkpoint"]["capture_diagnostics"] = []
    record.update(
        {
            "status": "unknown",
            "working_tree_evidence": finalize_working_tree_evidence(
                governed_project_id="ldvh",
                git_worktree_root=record["workspace"],
                git_common_dir=str(Path(record["workspace"]).parent / "main.git"),
                coverage=current_complete_coverage(),
                before=_manifest(),
                after=_manifest(),
            ),
        }
    )
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="mutually exclusive"):
        runs_module._read_record(record_path)


def test_v2_reader_rejects_fixed_step_and_top_level_matrix_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    valid, record_path, _output_path = _finish_valid_v2_passed(tmp_path, monkeypatch)

    missing_steps = dict(valid)
    missing_steps["steps"] = []
    record_path.write_text(json.dumps(missing_steps), encoding="utf-8")
    with pytest.raises(ValueError, match="fixed full-v4 steps"):
        runs_module._read_record(record_path)

    false_failed = dict(valid)
    false_failed.update({"status": "failed", "final_exit_code": 9})
    record_path.write_text(json.dumps(false_failed), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match its step aggregate"):
        runs_module._read_record(record_path)

    false_unknown = dict(valid)
    false_unknown.update({"status": "unknown", "evidence_complete": False, "final_exit_code": 7})
    record_path.write_text(json.dumps(false_unknown), encoding="utf-8")
    with pytest.raises(ValueError, match="known step aggregate"):
        runs_module._read_record(record_path)

    invalid_time = json.loads(json.dumps(valid))
    invalid_time["steps"][0]["started_at"] = "not-a-date"
    record_path.write_text(json.dumps(invalid_time), encoding="utf-8")
    with pytest.raises(ValueError, match="terminal times"):
        runs_module._read_record(record_path)


@pytest.mark.parametrize("failure", ["missing", "truncated", "changed", "wrong_path", "symlink_alias"])
def test_v2_observer_rejects_incomplete_or_unbound_raw_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    valid, record_path, output_path = _finish_valid_v2_passed(tmp_path, monkeypatch)
    run_id = valid["run_id"]
    run_dir = record_path.parent
    if failure == "missing":
        output_path.unlink()
    elif failure == "truncated":
        output_path.write_bytes(b"")
    elif failure == "changed":
        output_path.write_bytes(b"X" * valid["raw_output_size_bytes"])
    elif failure == "wrong_path":
        alternate = run_dir / "alternate.log"
        alternate.write_bytes(output_path.read_bytes())
        valid["raw_output_path"] = str(alternate)
        record_path.write_text(json.dumps(valid), encoding="utf-8")
    else:
        alias = run_dir / "alias.log"
        try:
            alias.symlink_to(output_path)
        except OSError:
            pytest.skip("symlinks are unavailable")
        valid["raw_output_path"] = str(alias)
        record_path.write_text(json.dumps(valid), encoding="utf-8")

    observed = runs_module.observe_run(runs_root=run_dir.parent, run_id=run_id)

    assert observed["status"] == "unknown" and observed["evidence_complete"] is False
    assert observed["final_exit_code"] == 0
    assert observed["working_tree_evidence"]["status"] == "complete"
    assert observed["diagnostics"][-1]["code"] == "raw_output_unavailable"


def test_v2_reader_binds_run_id_and_record_path_to_durable_location(tmp_path: Path) -> None:
    record, record_path, _output_path = _v2_record(
        tmp_path, steps=[_step("not_run", None)], fixed_steps=True, bind_run_identity=True
    )

    record["run_id"] = "run-" + "d" * 32
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="run_id does not match"):
        runs_module._read_record(record_path)

    record["run_id"] = record_path.parent.name
    record["record_path"] = str(record_path.parent / "." / "record.json") + "/../record.json"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="record_path does not identify"):
        runs_module._read_record(record_path)


def test_v2_reader_binds_checkpoint_and_terminal_evidence_to_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, record_path, _output_path = _v2_record(
        tmp_path, steps=[_step("not_run", None)], fixed_steps=True, bind_run_identity=True
    )
    other_workspace = record_path.parent.parent / "other-workspace"
    record["working_tree_capture_checkpoint"]["git_worktree_root"] = str(other_workspace)
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="capture checkpoint does not match"):
        runs_module._read_record(record_path)

    terminal, terminal_path, _terminal_output = _finish_valid_v2_passed(
        tmp_path / "terminal", monkeypatch
    )
    terminal["workspace"] = str(other_workspace)
    terminal["steps"] = _fixed_steps(other_workspace, terminal["steps"])
    terminal_path.write_text(json.dumps(terminal), encoding="utf-8")
    with pytest.raises(ValueError, match="terminal evidence does not match"):
        runs_module._read_record(terminal_path)
