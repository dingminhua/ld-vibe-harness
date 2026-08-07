"""Durable records for LDVH's complete local verification run.

The launcher returns after starting a detached worker.  The worker owns the raw
output and final record, so a terminal or UI callback is never the only place
where a result exists.  New full-v4 runs use a v2 record whose conclusion is
bound to a before/after observation of the governed Working Tree; probes and
historical records retain the v1 contract.
"""

from __future__ import annotations

import hashlib
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

from ldvh.testing.working_tree_capture import (
    CaptureDiagnostic,
    GovernedWorktreeBoundary,
    ManifestCapture,
    capture_manifest,
    resolve_capture_boundary,
    same_capture_boundary,
)
from ldvh.testing.working_tree_evidence import (
    finalize_working_tree_evidence,
    validate_coverage,
    validate_manifest,
    validate_working_tree_evidence,
)

CONTRACT_V1 = "ldvh-test-run/1"
CONTRACT_V2 = "ldvh-test-run/2"
CONTRACT = CONTRACT_V1
SUPPORTED_CONTRACTS = frozenset({CONTRACT_V1, CONTRACT_V2})
FINAL_STATUSES = frozenset({"passed", "failed", "unknown"})
V2_STATUSES = frozenset({"running", *FINAL_STATUSES})
RUN_ID_PATTERN = re.compile(r"^run-[0-9a-f]{32}$")
WORKER_GATE_TIMEOUT_SECONDS = 10.0


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


def _read_record(path: Path, *, permit_v2_output_path_mismatch: bool = False) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("contract") not in SUPPORTED_CONTRACTS:
        raise ValueError("run record has an unrecognized contract")
    if value["contract"] == CONTRACT_V2:
        _validate_v2_record_shape(
            value,
            record_path=path,
            permit_output_path_mismatch=permit_v2_output_path_mismatch,
        )
    return value


def _validate_v2_record_shape(
    record: dict[str, Any],
    *,
    record_path: Path,
    permit_output_path_mismatch: bool = False,
) -> None:
    if record.get("plan") != "full-v4":
        raise ValueError("v2 run record must use the full-v4 plan")
    if record.get("status") not in V2_STATUSES:
        raise ValueError("v2 run record has an invalid status")
    if not _is_offset_datetime(record.get("started_at")):
        raise ValueError("v2 run record started_at must be an offset date-time")
    if "source" in record:
        raise ValueError("v2 run record must not contain source")
    if "working_tree_evidence" not in record or type(record.get("evidence_complete")) is not bool:
        raise ValueError("v2 run record is missing its evidence fields")
    run_id = record.get("run_id")
    if type(run_id) is not str or RUN_ID_PATTERN.fullmatch(run_id) is None or run_id != record_path.parent.name:
        raise ValueError("v2 run_id does not match the durable run directory")
    workspace = record.get("workspace")
    if type(workspace) is not str or not Path(workspace).is_absolute():
        raise ValueError("v2 run record workspace must be an absolute path")
    recorded_path = record.get("record_path")
    if type(recorded_path) is not str or Path(recorded_path) != record_path:
        raise ValueError("v2 run record record_path does not identify the durable record")
    raw_output_path = record.get("raw_output_path")
    if type(raw_output_path) is not str or not Path(raw_output_path).is_absolute():
        raise ValueError("v2 run record raw_output_path must be an absolute path")
    if not permit_output_path_mismatch and Path(raw_output_path) != record_path.parent / "output.log":
        raise ValueError("v2 raw_output_path does not identify the durable run output")
    _validate_v2_steps(record)
    diagnostics = record.get("diagnostics")
    if not isinstance(diagnostics, list):
        raise ValueError("v2 run record diagnostics must be an array")
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict) or set(diagnostic) != {"stage", "code", "summary"}:
            raise ValueError("v2 run record diagnostic has an invalid field set")
        if any(type(diagnostic[field]) is not str or not diagnostic[field] for field in diagnostic):
            raise ValueError("v2 run record diagnostic fields must be non-empty strings")
    evidence = record["working_tree_evidence"]
    checkpoint = record.get("working_tree_capture_checkpoint")
    if evidence is not None:
        if not isinstance(evidence, dict):
            raise ValueError("v2 working_tree_evidence must be an object or null")
        validate_working_tree_evidence(evidence)
        if evidence.get("git_worktree_root") != workspace:
            raise ValueError("v2 terminal evidence does not match the run workspace")
        if checkpoint is not None:
            raise ValueError("v2 terminal evidence and capture checkpoint are mutually exclusive")
    if checkpoint is not None:
        if not isinstance(checkpoint, dict):
            raise ValueError("v2 capture checkpoint must be an object")
        required = {
            "governed_project_id",
            "git_worktree_root",
            "git_common_dir",
            "coverage",
            "before",
            "capture_diagnostics",
        }
        checkpoint_fields = frozenset(checkpoint)
        if checkpoint_fields not in {frozenset(required), frozenset({*required, "after_capture_started_at"})}:
            raise ValueError("v2 capture checkpoint has an invalid field set")
        if not isinstance(checkpoint["capture_diagnostics"], list):
            raise ValueError("v2 checkpoint capture_diagnostics must be an array")
        for diagnostic in checkpoint["capture_diagnostics"]:
            if not isinstance(diagnostic, dict) or set(diagnostic) != {
                "stage",
                "path",
                "code",
                "system_error_category",
            }:
                raise ValueError("v2 checkpoint capture diagnostic has an invalid field set")
            if diagnostic.get("stage") not in {"before", "after"}:
                raise ValueError("v2 checkpoint capture diagnostic has an invalid stage")
            if diagnostic.get("path") is not None and (
                type(diagnostic["path"]) is not str or not diagnostic["path"]
            ):
                raise ValueError("v2 checkpoint capture diagnostic path must be null or non-empty")
            if type(diagnostic.get("code")) is not str or not diagnostic["code"]:
                raise ValueError("v2 checkpoint capture diagnostic code must be non-empty")
            if diagnostic.get("system_error_category") not in {
                "none",
                "filesystem_unavailable",
                "path_changed",
                "unsafe_topology",
                "unstable_identity",
                "unsupported_type",
                "normalization_failure",
            }:
                raise ValueError("v2 checkpoint capture diagnostic has an invalid system error category")
        if type(checkpoint["governed_project_id"]) is not str or not checkpoint["governed_project_id"]:
            raise ValueError("v2 checkpoint governed_project_id must be a non-empty string")
        for field in ("git_worktree_root", "git_common_dir"):
            value = checkpoint[field]
            if type(value) is not str or not Path(value).is_absolute():
                raise ValueError(f"v2 checkpoint {field} must be an absolute path")
        if checkpoint["git_worktree_root"] != workspace:
            raise ValueError("v2 capture checkpoint does not match the run workspace")
        validate_coverage(checkpoint["coverage"])
        validate_manifest(checkpoint["before"], checkpoint["coverage"]["policy_fingerprint"])
        if "after_capture_started_at" in checkpoint and (
            not _is_offset_datetime(checkpoint["after_capture_started_at"])
        ):
            raise ValueError("v2 checkpoint after_capture_started_at must be an offset date-time")
    status = record["status"]
    evidence_complete = record["evidence_complete"]
    if evidence_complete != (status in {"passed", "failed"}):
        raise ValueError("v2 evidence_complete does not match the top-level status")
    if status in {"passed", "failed"} and (
        not isinstance(evidence, dict) or evidence.get("status") != "complete"
    ):
        raise ValueError("v2 passed or failed requires complete Working Tree evidence")
    if status == "running" and (evidence is not None or checkpoint is None):
        raise ValueError("v2 running record requires only a capture checkpoint")
    final_exit_code = record.get("final_exit_code")
    if status == "running" and final_exit_code is not None:
        raise ValueError("v2 running record must not have a final exit code")
    if status == "running" and record.get("ended_at") is not None:
        raise ValueError("v2 running record must not have ended_at")
    if status in FINAL_STATUSES and not _is_offset_datetime(record.get("ended_at")):
        raise ValueError("v2 terminal record ended_at must be an offset date-time")
    if status == "passed" and final_exit_code != 0:
        raise ValueError("v2 passed record must have final exit code 0")
    if status == "failed" and (type(final_exit_code) is not int or final_exit_code == 0):
        raise ValueError("v2 failed record must have a nonzero final exit code")
    if status == "unknown" and final_exit_code is not None and type(final_exit_code) is not int:
        raise ValueError("v2 unknown record final exit code must be an integer or null")
    aggregate, aggregate_exit_code = _aggregate_steps(record["steps"])
    if status == "passed" and (aggregate, aggregate_exit_code) != ("passed", 0):
        raise ValueError("v2 passed record does not match its step aggregate")
    if status == "failed" and (aggregate != "failed" or aggregate_exit_code != final_exit_code):
        raise ValueError("v2 failed record does not match its step aggregate")
    if status == "unknown" and final_exit_code != aggregate_exit_code:
        raise ValueError("v2 unknown record final exit code does not match its known step aggregate")
    output_size = record.get("raw_output_size_bytes")
    output_sha256 = record.get("raw_output_sha256")
    has_output_integrity = "raw_output_size_bytes" in record or "raw_output_sha256" in record
    if has_output_integrity and (
        type(output_size) is not int
        or output_size < 0
        or type(output_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", output_sha256) is None
    ):
        raise ValueError("v2 raw output integrity fields are incomplete or invalid")
    if status == "running" and has_output_integrity:
        raise ValueError("v2 running record must not contain raw output integrity fields")
    if status in {"passed", "failed"} and not has_output_integrity:
        raise ValueError("v2 passed or failed record requires raw output integrity fields")


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
        {
            "name": "fact-integrity",
            "cwd": str(workspace),
            "argv": [python, "-m", "ldvh.testing.fact_integrity", "--workspace", str(workspace)],
        },
        {"name": "web-typecheck", "cwd": str(workspace / "web"), "argv": ["npm", "run", "check"]},
        {"name": "web-tests", "cwd": str(workspace / "web"), "argv": ["npm", "test"]},
        {"name": "web-build", "cwd": str(workspace / "web"), "argv": ["npm", "run", "build"]},
    ]


def _validate_v2_steps(record: dict[str, Any]) -> None:
    steps = record.get("steps")
    if not isinstance(steps, list):
        raise ValueError("v2 run record steps must be an array")
    expected = plan_commands(Path(record["workspace"]), "full-v4", 1)
    if len(steps) != len(expected):
        raise ValueError("v2 run record must contain the fixed full-v4 steps")
    statuses: list[str] = []
    required_fields = {"name", "cwd", "argv", "status", "started_at", "ended_at", "exit_code"}
    for index, (step, command) in enumerate(zip(steps, expected, strict=True)):
        if not isinstance(step, dict) or not required_fields <= set(step) or set(step) - required_fields - {"error"}:
            raise ValueError(f"v2 step {index} has an invalid field set")
        if any(step.get(field) != command[field] for field in ("name", "cwd", "argv")):
            raise ValueError(f"v2 step {index} does not match the fixed full-v4 command")
        status = step.get("status")
        if status not in {"not_run", "running", "passed", "failed", "unknown"}:
            raise ValueError(f"v2 step {index} has an invalid status")
        started_at, ended_at, exit_code = step.get("started_at"), step.get("ended_at"), step.get("exit_code")
        if status == "not_run" and any(value is not None for value in (started_at, ended_at, exit_code)):
            raise ValueError(f"v2 step {index} not_run fields are inconsistent")
        if status == "running" and (
            not _is_offset_datetime(started_at) or ended_at is not None or exit_code is not None
        ):
            raise ValueError(f"v2 step {index} running fields are inconsistent")
        if status in {"passed", "failed", "unknown"} and (
            not _is_offset_datetime(started_at) or not _is_offset_datetime(ended_at)
        ):
            raise ValueError(f"v2 step {index} terminal times are incomplete")
        if status == "passed" and exit_code != 0:
            raise ValueError(f"v2 step {index} passed exit code is invalid")
        if status == "failed" and (type(exit_code) is not int or exit_code == 0):
            raise ValueError(f"v2 step {index} failed exit code is invalid")
        if status == "unknown" and exit_code is not None:
            raise ValueError(f"v2 step {index} unknown exit code must be null")
        if "error" in step and (status != "unknown" or type(step["error"]) is not str or not step["error"]):
            raise ValueError(f"v2 step {index} error field is inconsistent")
        statuses.append(status)
    active = [index for index, status in enumerate(statuses) if status != "passed"]
    if active:
        first = active[0]
        if statuses[first] not in {"not_run", "running", "failed", "unknown"} or any(
            status != "not_run" for status in statuses[first + 1 :]
        ):
            raise ValueError("v2 steps do not form one monotonic execution prefix")


def _is_offset_datetime(value: object) -> bool:
    if type(value) is not str or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _git_identity(workspace: Path) -> dict[str, Any]:
    """Retain the historical v1 source observation; v2 never calls this."""

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


def _new_steps(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {**command, "status": "not_run", "started_at": None, "ended_at": None, "exit_code": None}
        for command in commands
    ]


def _diagnostic(*, stage: str, code: str, summary: str) -> dict[str, str]:
    return {"stage": stage, "code": code, "summary": summary}


def _append_diagnostic(record: dict[str, Any], diagnostic: dict[str, str]) -> None:
    diagnostics = record.setdefault("diagnostics", [])
    if diagnostic not in diagnostics:
        diagnostics.append(diagnostic)


def _capture_diagnostic(diagnostic: CaptureDiagnostic) -> dict[str, str]:
    location = diagnostic.path or "the worktree root"
    return _diagnostic(
        stage=diagnostic.stage,
        code=diagnostic.code,
        summary=f"capture could not completely observe {location} ({diagnostic.system_error_category})",
    )


def _checkpoint(boundary: GovernedWorktreeBoundary, capture: ManifestCapture) -> dict[str, Any]:
    return {
        **boundary.to_json(),
        "coverage": capture.coverage,
        "before": capture.manifest,
        "capture_diagnostics": [diagnostic.to_json() for diagnostic in capture.diagnostics],
    }


def start_run(*, workspace: Path, runs_root: Path, plan: str, probe_seconds: int, tool_path: Path) -> dict[str, Any]:
    workspace, runs_root = workspace.resolve(), runs_root.resolve()
    if not workspace.is_dir():
        raise ValueError("workspace must be an existing directory")
    if not 1 <= probe_seconds <= 30:
        raise ValueError("probe_seconds must be between 1 and 30")
    if plan == "full-v4" and runs_root != (workspace / ".ldvh-test-runs").resolve():
        raise ValueError("full-v4 runs_root must be <workspace>/.ldvh-test-runs")
    commands = plan_commands(workspace, plan, probe_seconds)
    run_id = f"run-{uuid.uuid4().hex}"
    run_dir = _run_directory(runs_root, run_id)
    run_dir.mkdir(parents=True, exist_ok=False)
    record_path, output_path = run_dir / "record.json", run_dir / "output.log"

    if plan == "full-v4":
        record = _start_v2_record(
            workspace=workspace,
            run_id=run_id,
            record_path=record_path,
            output_path=output_path,
            commands=commands,
        )
        _atomic_json(record_path, record)
        if record["status"] == "unknown":
            return record
    else:
        record = {
            "contract": CONTRACT_V1,
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
            "steps": _new_steps(commands),
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
        record.update({"status": "unknown", "evidence_complete": False, "ended_at": utc_now()})
        if record["contract"] == CONTRACT_V2:
            _append_diagnostic(
                record,
                _diagnostic(stage="worker", code="worker_start_failed", summary=f"worker could not start: {error}"),
            )
        else:
            record["observation_error"] = f"worker could not start: {error}"
        _atomic_json(record_path, record)
    else:
        # Merge from the current durable value.  The child may already have
        # opened the record while waiting for this exact PID assignment.
        current = _read_record(record_path)
        if current["status"] not in FINAL_STATUSES:
            current.update({"status": "running", "worker_pid": worker.pid, "worker_started_at": utc_now()})
            _atomic_json(record_path, current)
    return observe_run(runs_root=runs_root, run_id=run_id)


def _start_v2_record(
    *,
    workspace: Path,
    run_id: str,
    record_path: Path,
    output_path: Path,
    commands: list[dict[str, Any]],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "contract": CONTRACT_V2,
        "run_id": run_id,
        "plan": "full-v4",
        "status": "running",
        "evidence_complete": False,
        "started_at": utc_now(),
        "ended_at": None,
        "final_exit_code": None,
        "raw_output_path": str(output_path),
        "record_path": str(record_path),
        "workspace": str(workspace),
        "steps": _new_steps(commands),
        "working_tree_evidence": None,
        "diagnostics": [],
    }
    boundary_result = resolve_capture_boundary(workspace)
    if boundary_result.boundary is None:
        record.update({"status": "unknown", "ended_at": utc_now()})
        for diagnostic in boundary_result.diagnostics:
            _append_diagnostic(record, diagnostic.to_json())
        return record
    try:
        before_capture = capture_manifest(boundary_result.boundary, "before")
    except BaseException as error:
        record.update({"status": "unknown", "ended_at": utc_now()})
        _append_diagnostic(
            record,
            _diagnostic(
                stage="before",
                code="capture_failed",
                summary=f"before capture could not form a durable checkpoint: {error!r}",
            ),
        )
        return record
    record["working_tree_capture_checkpoint"] = _checkpoint(boundary_result.boundary, before_capture)
    for diagnostic in before_capture.diagnostics:
        _append_diagnostic(record, _capture_diagnostic(diagnostic))
    return record


def _append_line(stream: Any, message: str) -> None:
    stream.write(f"[{utc_now()}] {message}\n".encode())
    stream.flush()
    os.fsync(stream.fileno())


def _wait_for_worker_assignment(record_path: Path) -> dict[str, Any] | None:
    deadline = time.monotonic() + WORKER_GATE_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        record = _read_record(record_path)
        if record.get("worker_pid") == os.getpid():
            return record
        if record.get("status") in FINAL_STATUSES:
            return None
        time.sleep(0.01)
    record = _read_record(record_path)
    if record.get("status") not in FINAL_STATUSES:
        record.update({"status": "unknown", "evidence_complete": False, "final_exit_code": None, "ended_at": utc_now()})
        if record["contract"] == CONTRACT_V2:
            _append_diagnostic(
                record,
                _diagnostic(
                    stage="worker",
                    code="worker_pid_gate_timeout",
                    summary="worker PID assignment was not durably confirmed before the gate timeout",
                ),
            )
        else:
            record["observation_error"] = "worker PID assignment was not durably confirmed before the gate timeout"
        _atomic_json(record_path, record)
    return None


def run_worker(run_dir: Path) -> None:
    record_path, output_path = run_dir / "record.json", run_dir / "output.log"
    try:
        record = _wait_for_worker_assignment(record_path)
        if record is None:
            return
        if record["contract"] == CONTRACT_V2:
            _run_worker_v2(record, record_path, output_path)
        else:
            _run_worker_v1(record, record_path, output_path)
    except BaseException as error:
        _record_worker_exception(record_path, output_path, error)


def _execute_steps(record: dict[str, Any], record_path: Path, log: Any) -> None:
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


def _aggregate_steps(steps: object) -> tuple[str, int | None]:
    if not isinstance(steps, list) or not steps:
        return "unknown", None
    statuses = [step.get("status") for step in steps if isinstance(step, dict)]
    if len(statuses) != len(steps):
        return "unknown", None
    if all(status == "passed" for status in statuses):
        return "passed", 0
    failed_indexes = [index for index, status in enumerate(statuses) if status == "failed"]
    if len(failed_indexes) == 1:
        failed_index = failed_indexes[0]
        if all(status == "passed" for status in statuses[:failed_index]) and all(
            status == "not_run" for status in statuses[failed_index + 1 :]
        ):
            exit_code = steps[failed_index].get("exit_code")
            if type(exit_code) is int and exit_code != 0:
                return "failed", exit_code
    return "unknown", None


def _run_worker_v1(record: dict[str, Any], record_path: Path, output_path: Path) -> None:
    with output_path.open("ab", buffering=0) as log:
        _execute_steps(record, record_path, log)
    outcome, exit_code = _aggregate_steps(record["steps"])
    record.update(
        {
            "status": outcome,
            "evidence_complete": outcome != "unknown",
            "final_exit_code": exit_code,
            "ended_at": utc_now(),
        }
    )
    _atomic_json(record_path, record)


def _merge_coverage(before: dict[str, Any], after: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    policies_match = (
        before.get("policy_key") == after.get("policy_key")
        and before.get("policy_fingerprint") == after.get("policy_fingerprint")
        and before.get("include_policy_refs") == after.get("include_policy_refs")
        and before.get("exclude_policy_refs") == after.get("exclude_policy_refs")
    )
    merged = dict(before)
    gaps = [*before.get("gaps", []), *after.get("gaps", [])]
    if not policies_match:
        gaps.append(
            {
                "stage": "comparison",
                "path": None,
                "code": "policy_mismatch",
                "summary": "before and after captures used different coverage policies",
            }
        )
    merged["gaps"] = gaps
    merged["status"] = "complete" if policies_match and not gaps else "incomplete"
    return merged, policies_match


def _identity_mismatch_coverage(coverage: dict[str, Any]) -> dict[str, Any]:
    result = dict(coverage)
    result["status"] = "incomplete"
    result["gaps"] = [
        *coverage.get("gaps", []),
        {
            "stage": "comparison",
            "path": None,
            "code": "identity_mismatch",
            "summary": "after governance identity did not match the accepted before identity",
        },
    ]
    return result


def _boundary_from_checkpoint(checkpoint: dict[str, Any]) -> GovernedWorktreeBoundary:
    return GovernedWorktreeBoundary(
        governed_project_id=checkpoint["governed_project_id"],
        git_worktree_root=Path(checkpoint["git_worktree_root"]),
        git_common_dir=Path(checkpoint["git_common_dir"]),
    )


def _run_worker_v2(record: dict[str, Any], record_path: Path, output_path: Path) -> None:
    execution_error: BaseException | None = None
    output_integrity: tuple[int, str] | None = None
    try:
        with output_path.open("ab", buffering=0) as log:
            _execute_steps(record, record_path, log)
    except BaseException as error:
        execution_error = error
        _append_diagnostic(
            record,
            _diagnostic(
                stage="steps",
                code="step_execution_interrupted",
                summary=f"step execution was interrupted: {error!r}",
            ),
        )
    try:
        raw_output = output_path.read_bytes()
        output_integrity = (len(raw_output), hashlib.sha256(raw_output).hexdigest())
    except BaseException as error:
        if execution_error is None:
            execution_error = error
        _append_diagnostic(
            record,
            _diagnostic(
                stage="output",
                code="raw_output_finalization_failed",
                summary=f"raw output integrity could not be formed after closing the output: {error!r}",
            ),
        )
    finally:
        checkpoint = record.get("working_tree_capture_checkpoint")
        evidence: dict[str, Any] | None = None
        if not isinstance(checkpoint, dict):
            _append_diagnostic(
                record,
                _diagnostic(
                    stage="after",
                    code="checkpoint_unavailable",
                    summary="after capture has no durable before checkpoint",
                ),
            )
        else:
            checkpoint["after_capture_started_at"] = utc_now()
            _atomic_json(record_path, record)
            evidence = _finalize_v2_evidence(record, checkpoint)
        aggregate, exit_code = _aggregate_steps(record.get("steps"))
        record["working_tree_evidence"] = evidence
        evidence_status = evidence.get("status") if evidence is not None else None
        status = (
            aggregate
            if execution_error is None and aggregate in {"passed", "failed"} and evidence_status == "complete"
            else "unknown"
        )
        record.update(
            {
                "status": status,
                "evidence_complete": status in {"passed", "failed"},
                "final_exit_code": exit_code,
                "ended_at": utc_now(),
            }
        )
        if output_integrity is not None:
            record["raw_output_size_bytes"], record["raw_output_sha256"] = output_integrity
        if evidence is not None:
            record.pop("working_tree_capture_checkpoint", None)
        _atomic_json(record_path, record)
    if execution_error is not None:
        return


def _finalize_v2_evidence(record: dict[str, Any], checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    before_boundary = _boundary_from_checkpoint(checkpoint)
    after_manifest: dict[str, Any] | None = None
    coverage = checkpoint["coverage"]
    identities_match = False
    policies_match = True
    try:
        after_boundary_result = resolve_capture_boundary(Path(record["workspace"]))
        if after_boundary_result.boundary is None or not same_capture_boundary(
            before_boundary, after_boundary_result.boundary
        ):
            for diagnostic in after_boundary_result.diagnostics:
                _append_diagnostic(record, diagnostic.to_json())
            coverage = _identity_mismatch_coverage(coverage)
        else:
            identities_match = True
            after_capture = capture_manifest(after_boundary_result.boundary, "after")
            after_manifest = after_capture.manifest
            coverage, policies_match = _merge_coverage(coverage, after_capture.coverage)
            if not policies_match:
                # The DTO carries one coverage identity.  Keeping an after
                # manifest produced under a different policy would make the
                # pair look comparable to the validator, so preserve the
                # policy-mismatch gap and withhold the incomparable fragment.
                after_manifest = None
            for diagnostic in after_capture.diagnostics:
                _append_diagnostic(record, _capture_diagnostic(diagnostic))
        return finalize_working_tree_evidence(
            governed_project_id=checkpoint["governed_project_id"],
            git_worktree_root=checkpoint["git_worktree_root"],
            git_common_dir=checkpoint["git_common_dir"],
            coverage=coverage,
            before=checkpoint["before"],
            after=after_manifest,
            identities_match=identities_match,
            policies_match=policies_match,
        )
    except BaseException as error:
        _append_diagnostic(
            record,
            _diagnostic(
                stage="after",
                code="evidence_finalization_failed",
                summary=f"terminal evidence could not be formed: {error!r}",
            ),
        )
        return None


def _record_worker_exception(record_path: Path, output_path: Path, error: BaseException) -> None:
    try:
        with output_path.open("ab", buffering=0) as log:
            _append_line(log, f"worker_exception={error!r}")
            log.write(traceback.format_exc().encode("utf-8", errors="backslashreplace"))
    except OSError:
        pass
    try:
        record = _read_record(record_path)
        aggregate, exit_code = _aggregate_steps(record.get("steps"))
        record.update(
            {
                "status": "unknown",
                "evidence_complete": False,
                "final_exit_code": exit_code if record["contract"] == CONTRACT_V2 else None,
                "ended_at": utc_now(),
            }
        )
        if record["contract"] == CONTRACT_V2:
            _append_diagnostic(
                record,
                _diagnostic(
                    stage="worker",
                    code="worker_record_failed",
                    summary=f"worker did not complete its durable record: {error!r}",
                ),
            )
        else:
            record["observation_error"] = f"worker did not complete its durable record: {error!r}"
        _atomic_json(record_path, record)
    except (OSError, ValueError, json.JSONDecodeError):
        pass


def observe_run(*, runs_root: Path, run_id: str) -> dict[str, Any]:
    record_path = _run_directory(runs_root.resolve(), run_id) / "record.json"
    record = _read_record(record_path, permit_v2_output_path_mismatch=True)
    is_v2 = record["contract"] == CONTRACT_V2
    if record["status"] not in FINAL_STATUSES and not _pid_alive(record.get("worker_pid")):
        _, aggregate_exit_code = _aggregate_steps(record.get("steps"))
        record.update(
            {
                "status": "unknown",
                "evidence_complete": False,
                "final_exit_code": aggregate_exit_code if is_v2 else None,
                "ended_at": utc_now(),
            }
        )
        if is_v2:
            _append_diagnostic(
                record,
                _diagnostic(
                    stage="observer",
                    code="worker_absent",
                    summary="worker is absent before a durable terminal result was recorded",
                ),
            )
        else:
            record["observation_error"] = "worker is absent before a durable terminal result was recorded"
        _atomic_json(record_path, record)
    elif record["status"] in {"passed", "failed"}:
        output_problem = _v2_output_problem(record, record_path) if is_v2 else _v1_output_problem(record)
        if output_problem is not None:
            record.update(
                {
                    "status": "unknown",
                    "evidence_complete": False,
                    "final_exit_code": record.get("final_exit_code") if is_v2 else None,
                }
            )
            if is_v2:
                _append_diagnostic(
                    record,
                    _diagnostic(
                        stage="observer",
                        code="raw_output_unavailable",
                        summary=output_problem,
                    ),
                )
            else:
                record["observation_error"] = output_problem
            _atomic_json(record_path, record)
    return record


def _v1_output_problem(record: dict[str, Any]) -> str | None:
    output_path = Path(record.get("raw_output_path", ""))
    try:
        output_path.read_bytes()
    except OSError as error:
        return f"raw output cannot be read: {error}"
    return None


def _v2_output_problem(record: dict[str, Any], record_path: Path) -> str | None:
    expected = record_path.parent / "output.log"
    actual = Path(record["raw_output_path"])
    if actual != expected:
        return "raw output path does not identify this run directory's output.log"
    try:
        raw_output = expected.read_bytes()
    except OSError as error:
        return f"raw output cannot be read: {error}"
    if len(raw_output) != record["raw_output_size_bytes"]:
        return "raw output size does not match the durable terminal record"
    if hashlib.sha256(raw_output).hexdigest() != record["raw_output_sha256"]:
        return "raw output hash does not match the durable terminal record"
    return None


def wait_for_run(*, runs_root: Path, run_id: str, timeout_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while True:
        record = observe_run(runs_root=runs_root, run_id=run_id)
        if record["status"] in FINAL_STATUSES or time.monotonic() >= deadline:
            return record
        time.sleep(0.1)
