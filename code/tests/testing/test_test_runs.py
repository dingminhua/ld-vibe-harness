from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

from ldvh.testing.test_runs import plan_commands

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOOL = PROJECT_ROOT / "tools" / "run_full_tests.py"


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
