"""Durable records for LDVH's complete local verification run.

The launcher returns after starting a detached worker. The worker owns the raw
output and final record, so a terminal or UI callback is never the only place
where a result exists.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CONTRACT = "ldvh-test-run/1"
FINAL_STATUSES = frozenset({"passed", "failed", "unknown"})
RUN_ID_PATTERN = re.compile(r"^run-[0-9a-f]{32}$")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _read_record(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("contract") != CONTRACT:
        raise ValueError("run record has an unrecognized contract")
    return value


def _python(workspace: Path) -> str:
    executable = workspace / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return str(executable if executable.is_file() else sys.executable)


def plan_commands(workspace: Path, plan: str, probe_seconds: int) -> list[dict[str, Any]]:
    python = _python(workspace)
    if plan == "probe":
        probe_program = (
            "import time; print('probe worker started', flush=True); "
            f"time.sleep({probe_seconds}); print('probe worker finished', flush=True)"
        )
        return [
            {
                "name": "detached-observability-probe",
                "cwd": str(workspace),
                "argv": [python, "-c", probe_program],
            }
        ]
    if plan != "full-v4":
        raise ValueError(f"unsupported plan: {plan}")
    return [
        {"name": "code-lint", "cwd": str(workspace), "argv": [python, "-m", "ruff", "check", "code", "tools"]},
        {"name": "code-tests", "cwd": str(workspace), "argv": [python, "-m", "pytest", "code/tests", "-q"]},
        {"name": "web-typecheck", "cwd": str(workspace / "web"), "argv": ["npm", "run", "check"]},
        {"name": "web-tests", "cwd": str(workspace / "web"), "argv": ["npm", "test"]},
        {"name": "web-build", "cwd": str(workspace / "web"), "argv": ["npm", "run", "build"]},
    ]


def _git_identity(workspace: Path) -> dict[str, Any]:
    try:
        head = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
            timeout=10,
        )
        status = subprocess.run(
            ["git", "-C", str(workspace), "status", "--porcelain=v1"],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"kind": "git-observation-unavailable", "reason": str(error)}
    if head.returncode != 0 or status.returncode != 0:
        return {
            "kind": "git-observation-unavailable",
            "head_exit_code": head.returncode,
            "status_exit_code": status.returncode,
        }
    return {"kind": "git-worktree", "head": head.stdout.strip(), "dirty": bool(status.stdout.strip())}


def _run_directory(runs_root: Path, run_id: str) -> Path:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("invalid run id")
    directory = (runs_root / run_id).resolve()
    if directory.parent != runs_root.resolve():
        raise ValueError("run directory is outside the runs root")
    return directory


def _pid_alive(pid: object) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def start_run(*, workspace: Path, runs_root: Path, plan: str, probe_seconds: int, tool_path: Path) -> dict[str, Any]:
    workspace, runs_root = workspace.resolve(), runs_root.resolve()
    if not workspace.is_dir():
        raise ValueError("workspace must be an existing directory")
    if not 1 <= probe_seconds <= 30:
        raise ValueError("probe_seconds must be between 1 and 30")
    commands = plan_commands(workspace, plan, probe_seconds)
    run_id = f"run-{uuid.uuid4().hex}"
    run_dir = _run_directory(runs_root, run_id)
    run_dir.mkdir(parents=True, exist_ok=False)
    record_path, output_path = run_dir / "record.json", run_dir / "output.log"
    record: dict[str, Any] = {
        "contract": CONTRACT,
        "run_id": run_id,
        "plan": plan,
        "status": "starting",
        "evidence_complete": False,
        "started_at": utc_now(),
        "ended_at": None,
        "final_exit_code": None,
        "raw_output_path": str(output_path),
        "record_path": str(record_path),
        "workspace": str(workspace),
        "source": _git_identity(workspace),
        "steps": [
            {**command, "status": "not_run", "started_at": None, "ended_at": None, "exit_code": None}
            for command in commands
        ],
    }
    _atomic_json(record_path, record)
    try:
        worker = subprocess.Popen(
            [sys.executable, str(tool_path), "_worker", "--run-dir", str(run_dir)],
            cwd=workspace,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as error:
        record.update(
            {
                "status": "unknown",
                "evidence_complete": False,
                "ended_at": utc_now(),
                "observation_error": f"worker could not start: {error}",
            }
        )
        _atomic_json(record_path, record)
    else:
        record.update({"status": "running", "worker_pid": worker.pid, "worker_started_at": utc_now()})
        _atomic_json(record_path, record)
    return observe_run(runs_root=runs_root, run_id=run_id)


def _append_line(stream: Any, message: str) -> None:
    stream.write(f"[{utc_now()}] {message}\n".encode())
    stream.flush()
    os.fsync(stream.fileno())


def run_worker(run_dir: Path) -> None:
    record_path, output_path = run_dir / "record.json", run_dir / "output.log"
    try:
        record = _read_record(record_path)
        record.update({"status": "running", "worker_pid": os.getpid(), "worker_started_at": utc_now()})
        _atomic_json(record_path, record)
        with output_path.open("ab", buffering=0) as log:
            _append_line(log, f"run_id={record['run_id']} plan={record['plan']} worker_pid={os.getpid()}")
            for step in record["steps"]:
                step.update({"status": "running", "started_at": utc_now()})
                _atomic_json(record_path, record)
                _append_line(log, f"step={step['name']} cwd={step['cwd']} argv={json.dumps(step['argv'])}")
                try:
                    with subprocess.Popen(
                        step["argv"], cwd=step["cwd"], stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL
                    ) as process:
                        exit_code = process.wait()
                except OSError as error:
                    exit_code, step["status"], step["error"] = None, "unknown", str(error)
                    _append_line(log, f"step={step['name']} launch_error={error}")
                else:
                    step["status"] = "passed" if exit_code == 0 else "failed"
                step.update({"exit_code": exit_code, "ended_at": utc_now()})
                _append_line(log, f"step={step['name']} status={step['status']} exit_code={exit_code}")
                _atomic_json(record_path, record)
                if step["status"] != "passed":
                    break
        statuses = {step["status"] for step in record["steps"]}
        finished = statuses == {"passed"}
        outcome = "passed" if finished else "unknown" if "unknown" in statuses else "failed"
        record.update(
            {
                "status": outcome,
                "evidence_complete": outcome != "unknown",
                "final_exit_code": 0
                if finished
                else (
                    next((step["exit_code"] for step in record["steps"] if step["status"] != "passed"), None)
                    if outcome == "failed"
                    else None
                ),
                "ended_at": utc_now(),
            }
        )
        _atomic_json(record_path, record)
    except BaseException as error:
        try:
            with output_path.open("ab", buffering=0) as log:
                _append_line(log, f"worker_exception={error!r}")
                log.write(traceback.format_exc().encode("utf-8", errors="backslashreplace"))
        except OSError:
            pass
        try:
            record = _read_record(record_path)
            record.update(
                {
                    "status": "unknown",
                    "evidence_complete": False,
                    "final_exit_code": None,
                    "ended_at": utc_now(),
                    "observation_error": f"worker did not complete its durable record: {error!r}",
                }
            )
            _atomic_json(record_path, record)
        except (OSError, ValueError, json.JSONDecodeError):
            pass


def observe_run(*, runs_root: Path, run_id: str) -> dict[str, Any]:
    record_path = _run_directory(runs_root.resolve(), run_id) / "record.json"
    record = _read_record(record_path)
    if record["status"] not in FINAL_STATUSES and not _pid_alive(record.get("worker_pid")):
        record.update(
            {
                "status": "unknown",
                "evidence_complete": False,
                "final_exit_code": None,
                "ended_at": utc_now(),
                "observation_error": "worker is absent before a durable terminal result was recorded",
            }
        )
        _atomic_json(record_path, record)
    elif record["status"] in {"passed", "failed"}:
        output_path = Path(record.get("raw_output_path", ""))
        try:
            output_path.read_bytes()
        except OSError as error:
            record.update(
                {
                    "status": "unknown",
                    "evidence_complete": False,
                    "final_exit_code": None,
                    "observation_error": f"raw output cannot be read: {error}",
                }
            )
            _atomic_json(record_path, record)
    return record


def wait_for_run(*, runs_root: Path, run_id: str, timeout_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while True:
        record = observe_run(runs_root=runs_root, run_id=run_id)
        if record["status"] in FINAL_STATUSES or time.monotonic() >= deadline:
            return record
        time.sleep(0.1)
