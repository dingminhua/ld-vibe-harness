#!/usr/bin/env python3
"""Run LDVH's manual native-Windows evidence gate without creating CI state."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CONTRACT = "ldvh-native-windows-verification/1"
PHASES = ("preflight", "core-readonly", "core-full", "adapter-handoff")
EVIDENCE_FILES = (
    "environment.json",
    "source.json",
    "commands.jsonl",
    "core-summary.json",
    "adapter-summary.json",
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND_TIMEOUT_SECONDS = 900
IDENTITY_TIMEOUT_SECONDS = 30
FIXED_DRIVE = 3

BASE_PROBES = {
    "test_native_environment_is_windows_ntfs_with_source_launcher": "native_environment_and_source_launcher",
    "test_native_junction_is_rejected_before_read": "junction_rejection",
    "test_native_symlink_is_rejected_when_privilege_is_available": "symlink_rejection",
    "test_native_msvcrt_lock_serializes_and_recovers_after_kill": "lock_kill_recovery",
    "test_native_file_only_create_and_replace_report_exact_boundaries": "file_only_atomic_boundaries",
    "test_native_git_linked_worktree_and_temporary_index_are_isolated": "git_linked_worktree_temp_index",
    "test_native_drive_letter_case_alias_reads_the_same_file": "drive_case_alias",
    "test_native_unc_read_is_rejected_before_filesystem_access": "unc_fail_closed",
}
POLICY_PROBES = {
    "test_native_public_create_and_update_are_unavailable_without_side_effects": "public_write_fail_closed",
}
APPROVED_PROBES = {
    "test_native_six_process_allocator_contiguous_ids": "allocator_six_process_contiguous_ids",
    "test_native_linked_worktree_shared_counter": "main_linked_shared_counter",
    "test_native_conditional_update_single_winner": "conditional_update_single_winner",
}
FUTURE_WRITE_PROBES = tuple(APPROVED_PROBES.values())


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def verification_plan() -> dict[str, Any]:
    return {
        "contract": CONTRACT,
        "mode": "plan",
        "platform_required": {
            "sys_platform": "win32",
            "os_name": "nt",
            "filesystem": "NTFS",
            "drive_type": "fixed",
        },
        "phases": {
            "preflight": {
                "purpose": (
                    "prove the native host, isolated dependencies, source launcher and native read/platform probes"
                ),
                "matrix": {
                    **dict.fromkeys(BASE_PROBES.values(), "scheduled"),
                    **dict.fromkeys(FUTURE_WRITE_PROBES, "blocked_by_file_only_human_gate"),
                },
            },
            "core-readonly": {
                "purpose": "add the current public create/update fail-closed policy probe",
                "matrix": {
                    **dict.fromkeys(BASE_PROBES.values(), "scheduled"),
                    **dict.fromkeys(POLICY_PROBES.values(), "scheduled"),
                    **dict.fromkeys(FUTURE_WRITE_PROBES, "blocked_by_file_only_human_gate"),
                },
            },
            "core-full": {
                "purpose": (
                    "approved native write matrix: six-process allocator, shared linked-worktree counter, "
                    "and conditional-update single-winner probes"
                ),
                "human_gate": "Windows file_only durability accepted via 05 §11.8 condition (c) on 2026-08-07",
                "matrix": dict.fromkeys(FUTURE_WRITE_PROBES, "scheduled"),
            },
            "adapter-handoff": {
                "automated": False,
                "purpose": "emit a Human-gated checklist; never install, trust, enable, restart or trigger Codex",
            },
        },
        "evidence_files": list(EVIDENCE_FILES),
        "safety": [
            "evidence_dir must be an explicit absolute path outside the source tree",
            "source_root must be the exact top level of a clean Git worktree",
            "commands use argv, a bounded timeout and a minimal child environment without ambient "
            "Python/Pip/Git overrides",
            "Pip prepares only declared third-party dependencies; it never installs LDVH itself",
            "no command commits, pushes, changes a remote, or touches a governed user project",
            "environment thin-Skill integration remains a separate Human Gate",
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="print the cross-platform plan without writing files")
    parser.add_argument("--phase", choices=PHASES, default="preflight")
    parser.add_argument("--evidence-dir")
    parser.add_argument("--source-root", default=str(PROJECT_ROOT))
    parser.add_argument("--source-commit")
    return parser


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_environment() -> dict[str, str]:
    allowed = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC")
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment.update({"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"})
    return environment


def _child_environment(work_dir: Path) -> dict[str, str]:
    temp_dir = work_dir / "temp"
    cache_dir = work_dir / "pip-cache"
    temp_dir.mkdir(parents=True, exist_ok=True)
    environment = _base_environment()
    environment.update(
        {
            "TEMP": str(temp_dir),
            "TMP": str(temp_dir),
            "TMPDIR": str(temp_dir),
            "PIP_CACHE_DIR": str(cache_dir),
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INPUT": "1",
        }
    )
    return environment


def _checked(argv: list[str], *, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=_base_environment(),
        capture_output=True,
        check=False,
        timeout=IDENTITY_TIMEOUT_SECONDS,
    )


def _source_identity(source_root: Path, arguments: argparse.Namespace) -> dict[str, Any]:
    git = shutil.which("git")
    if not git:
        raise RuntimeError("Git is required to verify source identity")
    top = _checked([git, "-C", str(source_root), "rev-parse", "--show-toplevel"], cwd=source_root)
    if top.returncode != 0:
        raise RuntimeError("source_root must be a Git worktree")
    top_level = Path(top.stdout.decode("utf-8", errors="strict").strip()).resolve()
    if top_level != source_root:
        raise RuntimeError("source_root must equal the Git worktree top level")
    head = _checked([git, "-C", str(source_root), "rev-parse", "--verify", "HEAD^{commit}"], cwd=source_root)
    if head.returncode != 0:
        raise RuntimeError("Git HEAD commit could not be verified")
    commit = head.stdout.decode("ascii", errors="strict").strip().lower()
    if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit) is None:
        raise RuntimeError("Git returned an invalid full commit identity")
    if arguments.source_commit and arguments.source_commit.lower() != commit:
        raise RuntimeError("--source-commit does not match Git HEAD")
    status = _checked(
        [git, "-C", str(source_root), "status", "--porcelain=v1", "--untracked-files=all"], cwd=source_root
    )
    if status.returncode != 0:
        raise RuntimeError("Git status could not be read")
    if status.stdout:
        raise RuntimeError("Git source must be clean")
    return {"kind": "clean_git_worktree", "top_level": str(source_root), "commit": commit, "clean": True}


def _volume_observation(path: Path) -> dict[str, Any]:
    volume_path = ctypes.create_unicode_buffer(261)
    if not ctypes.windll.kernel32.GetVolumePathNameW(str(path), volume_path, len(volume_path)):
        raise OSError("GetVolumePathNameW failed")
    filesystem = ctypes.create_unicode_buffer(261)
    if not ctypes.windll.kernel32.GetVolumeInformationW(
        volume_path.value, None, 0, None, None, None, filesystem, len(filesystem)
    ):
        raise OSError("GetVolumeInformationW failed")
    drive_type = ctypes.windll.kernel32.GetDriveTypeW(volume_path.value)
    return {"filesystem": filesystem.value, "drive_type": drive_type}


def _utc_iso(value: datetime | None = None) -> str:
    return (value or datetime.now(UTC)).astimezone(UTC).isoformat().replace("+00:00", "Z")


def _environment(evidence_dir: Path, isolated_temp: Path) -> dict[str, Any]:
    return {
        "observed_at": _utc_iso(),
        "platform": platform.platform(),
        "windows_edition": platform.win32_edition(),
        "windows_version": platform.win32_ver(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "git_executable": shutil.which("git"),
        "codex_executable": shutil.which("codex"),
        "evidence_volume": _volume_observation(evidence_dir),
        "isolated_temp_volume": _volume_observation(isolated_temp),
        "symlink_privilege": "measured_by_junit_probe",
    }


def _venv_python(work_dir: Path) -> Path:
    return work_dir / "venv" / "Scripts" / "python.exe"


def _pytest_command(python: Path, junit: Path, test_path: str) -> list[str]:
    return [
        str(python),
        "-m",
        "pytest",
        "-q",
        "--override-ini=addopts=-ra --strict-markers",
        f"--junitxml={junit}",
        test_path,
    ]


def _commands(phase: str, source_root: Path, work_dir: Path) -> list[tuple[str, list[str]]]:
    python = _venv_python(work_dir)
    commands: list[tuple[str, list[str]]] = [
        ("create-venv", [sys.executable, "-m", "venv", str(work_dir / "venv")]),
        (
            "prepare-dependencies",
            [
                str(python),
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-cache-dir",
                "--disable-pip-version-check",
                "--no-input",
                "-r",
                str(source_root / "requirements-dev.txt"),
            ],
        ),
        (
            "native-probes",
            _pytest_command(python, work_dir / "native-probes.xml", "code/tests/platform/test_native_windows.py"),
        ),
    ]
    if phase == "core-readonly":
        commands.extend(
            [
                (
                    "write-policy-probes",
                    _pytest_command(
                        python,
                        work_dir / "write-policy-probes.xml",
                        "code/tests/platform/test_native_windows_write_policy.py",
                    ),
                ),
                ("ruff-check", [str(python), "-m", "ruff", "check", "code"]),
                ("ruff-format", [str(python), "-m", "ruff", "format", "--check", "code"]),
            ]
        )
    if phase == "core-full":
        commands.append(
            (
                "approved-write-probes",
                _pytest_command(
                    python,
                    work_dir / "approved-write-probes.xml",
                    "code/tests/platform/test_native_windows_approved_writes.py",
                ),
            )
        )
    return commands


def _record_command(
    evidence_dir: Path,
    index: int,
    name: str,
    argv: list[str],
    source_root: Path,
    child_environment: dict[str, str],
) -> dict[str, Any]:
    started = datetime.now(UTC)
    outcome = "completed"
    exit_code: int | None = None
    stdout = b""
    stderr = b""
    try:
        completed = subprocess.run(
            argv,
            cwd=source_root,
            env=child_environment,
            capture_output=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as error:
        outcome = "timeout"
        stdout = error.stdout or b""
        stderr = (error.stderr or b"") + f"\ncommand timed out after {COMMAND_TIMEOUT_SECONDS}s\n".encode()
    except OSError as error:
        outcome = "os_error"
        stderr = f"{type(error).__name__}: {error}\n".encode("utf-8", errors="replace")
    ended = datetime.now(UTC)
    stdout_path = evidence_dir / f"command-{index:02d}-{name}.stdout"
    stderr_path = evidence_dir / f"command-{index:02d}-{name}.stderr"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    return {
        "index": index,
        "name": name,
        "argv": argv,
        "cwd": str(source_root),
        "started_at": _utc_iso(started),
        "completed_at": _utc_iso(ended),
        "timeout_seconds": COMMAND_TIMEOUT_SECONDS,
        "outcome": outcome,
        "exit_code": exit_code,
        "stdout": {"path": stdout_path.name, "sha256": _sha256(stdout_path)},
        "stderr": {"path": stderr_path.name, "sha256": _sha256(stderr_path)},
    }


def _probe_matrix(work_dir: Path, phase: str) -> dict[str, str]:
    matrix = {**dict.fromkeys(BASE_PROBES.values(), "not_run"), **dict.fromkeys(POLICY_PROBES.values(), "not_run")}
    future_default = "not_run" if phase == "core-full" else "blocked_by_file_only_human_gate"
    matrix.update(dict.fromkeys(FUTURE_WRITE_PROBES, future_default))
    files = [(work_dir / "native-probes.xml", BASE_PROBES)]
    if phase == "core-readonly":
        files.append((work_dir / "write-policy-probes.xml", POLICY_PROBES))
    if phase == "core-full":
        files.append((work_dir / "approved-write-probes.xml", APPROVED_PROBES))
    for junit, mapping in files:
        if not junit.is_file():
            continue
        for case in ET.parse(junit).getroot().iter("testcase"):
            key = mapping.get(case.attrib.get("name", ""))
            if key is None:
                continue
            if case.find("skipped") is not None:
                matrix[key] = "skipped"
            elif case.find("failure") is not None or case.find("error") is not None:
                matrix[key] = "failed"
            else:
                matrix[key] = "passed"
    return matrix


def _pending_summaries(evidence_dir: Path, phase: str) -> None:
    (evidence_dir / "commands.jsonl").write_text("", encoding="utf-8")
    _write_json(
        evidence_dir / "core-summary.json",
        {"contract": CONTRACT, "phase": phase, "status": "initializing", "commands": [], "matrix": {}},
    )
    _write_json(
        evidence_dir / "adapter-summary.json",
        {"contract": CONTRACT, "status": "not_run", "reason": "separate Human Gate"},
    )


def _adapter_handoff(evidence_dir: Path, source: dict[str, Any], work_dir: Path) -> int:
    summary = {
        "contract": CONTRACT,
        "status": "human_gate_required",
        "source_commit": source["commit"],
        "automated_changes": [],
        "required_checks": [
            "record existing marketplace, source, cache, configuration and trust state without mutation",
            "obtain Human authorization for canonical Skill deployment and any environment restart",
            "verify canonical Skill bytes and bind every CLI route to the confirmed source launcher",
            "deploy and verify the mandatory Git Hook as a separate common-dir action",
            "run startup, route, governance, Hook allow/block and rollback probes",
            "restore only environment assets changed by this authorized action on failure",
        ],
        "not_verified": ["installed", "enabled", "trusted", "startup", "resume", "rollback"],
    }
    _write_json(evidence_dir / "adapter-summary.json", summary)
    _write_json(
        evidence_dir / "core-summary.json",
        {"contract": CONTRACT, "phase": "adapter-handoff", "status": "not_run", "commands": [], "matrix": {}},
    )
    shutil.rmtree(work_dir)
    return 0


def _rejection(
    evidence_dir: Path,
    phase: str,
    error: BaseException,
    work_dir: Path,
    source: dict[str, Any] | None = None,
) -> int:
    if not (evidence_dir / "environment.json").is_file():
        _write_json(
            evidence_dir / "environment.json",
            {"observed_at": _utc_iso(), "status": "initialization_failed"},
        )
    if not (evidence_dir / "source.json").is_file():
        _write_json(evidence_dir / "source.json", source or {"status": "unavailable"})
    if not (evidence_dir / "commands.jsonl").is_file():
        (evidence_dir / "commands.jsonl").write_text("", encoding="utf-8")
    rejection = {
        "contract": CONTRACT,
        "outcome": "rejected",
        "phase": phase,
        "error_type": type(error).__name__,
        "summary": str(error),
        "work_dir": str(work_dir) if work_dir.exists() else "not_present",
    }
    _write_json(evidence_dir / "rejection.json", rejection)
    _write_json(
        evidence_dir / "core-summary.json",
        {
            "contract": CONTRACT,
            "phase": phase,
            "status": "rejected",
            "commands": [],
            "matrix": {},
            "reason": str(error),
        },
    )
    _write_json(
        evidence_dir / "adapter-summary.json",
        {"contract": CONTRACT, "status": "not_run", "reason": "core evidence rejected"},
    )
    return 2


def _initialize_evidence(
    evidence_dir: Path,
    phase: str,
    source: dict[str, Any],
) -> tuple[Path, int | None]:
    work_dir = evidence_dir / "_work"
    try:
        evidence_dir.mkdir(parents=True)
        work_dir.mkdir()
        (work_dir / "temp").mkdir()
        _write_json(evidence_dir / "source.json", source)
        _pending_summaries(evidence_dir, phase)
        _write_json(
            evidence_dir / "environment.json",
            {"observed_at": _utc_iso(), "status": "initializing"},
        )
    except (OSError, RuntimeError, UnicodeError) as error:
        if evidence_dir.exists():
            return work_dir, _rejection(evidence_dir, phase, error, work_dir, source)
        raise
    return work_dir, None


def _remove_work_dir(work_dir: Path) -> tuple[str, str, OSError | None]:
    try:
        shutil.rmtree(work_dir)
    except OSError as error:
        residual = str(work_dir) if work_dir.exists() else "partially_removed"
        return "failed_cleanup", residual, error
    return "passed", "removed", None


def _run(arguments: argparse.Namespace) -> int:
    if sys.platform != "win32" or os.name != "nt":
        raise RuntimeError("native execution requires sys.platform=win32 and os.name=nt; use --plan elsewhere")
    if not arguments.evidence_dir:
        raise RuntimeError("native execution requires --evidence-dir")
    source_root = Path(arguments.source_root).resolve()
    evidence_dir = Path(arguments.evidence_dir)
    if not evidence_dir.is_absolute():
        raise RuntimeError("--evidence-dir must be absolute")
    evidence_dir = evidence_dir.resolve()
    if _inside(evidence_dir, source_root):
        raise RuntimeError("--evidence-dir must be outside the source tree")
    if evidence_dir.exists():
        raise RuntimeError("--evidence-dir must not already exist")
    source = _source_identity(source_root, arguments)
    work_dir, initialization_exit = _initialize_evidence(evidence_dir, arguments.phase, source)
    if initialization_exit is not None:
        return initialization_exit
    isolated_temp = work_dir / "temp"
    try:
        environment = _environment(evidence_dir, isolated_temp)
        _write_json(evidence_dir / "environment.json", environment)
        for volume in (environment["evidence_volume"], environment["isolated_temp_volume"]):
            if volume["filesystem"].upper() != "NTFS" or volume["drive_type"] != FIXED_DRIVE:
                raise RuntimeError("the evidence and isolated TEMP paths must be on fixed NTFS volumes")
        if arguments.phase == "adapter-handoff":
            return _adapter_handoff(evidence_dir, source, work_dir)
        if arguments.phase == "core-full":
            sys.path.insert(0, str(source_root / "code"))
            from ldvh.filesystem import native_atomic_fact_writes_supported

            if not native_atomic_fact_writes_supported("nt"):
                matrix = dict.fromkeys(FUTURE_WRITE_PROBES, "blocked_by_file_only_human_gate")
                _write_json(
                    evidence_dir / "core-summary.json",
                    {
                        "contract": CONTRACT,
                        "phase": arguments.phase,
                        "status": "human_gate_required",
                        "reason": "Windows file_only durability is not accepted by the current public write policy",
                        "commands": [],
                        "matrix": matrix,
                        "work_dir": str(work_dir),
                    },
                )
                return 4

        child_environment = _child_environment(work_dir)
        commands = _commands(arguments.phase, source_root, work_dir)
        records: list[dict[str, Any]] = []
        for index, (name, argv) in enumerate(commands, start=1):
            record = _record_command(evidence_dir, index, name, argv, source_root, child_environment)
            records.append(record)
            with (evidence_dir / "commands.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(_json(record) + "\n")
            if record["outcome"] != "completed" or record["exit_code"] != 0:
                break
        passed = len(records) == len(commands) and all(
            record["outcome"] == "completed" and record["exit_code"] == 0 for record in records
        )
        matrix = _probe_matrix(work_dir, arguments.phase)
        status = "passed" if passed else "failed"
        work_state = str(work_dir)
        if passed:
            status, work_state, cleanup_error = _remove_work_dir(work_dir)
            if cleanup_error is not None:
                _write_json(
                    evidence_dir / "cleanup-error.json",
                    {
                        "contract": CONTRACT,
                        "error_type": type(cleanup_error).__name__,
                        "summary": str(cleanup_error),
                    },
                )
        summary = {
            "contract": CONTRACT,
            "phase": arguments.phase,
            "status": status,
            "source_commit": source["commit"],
            "commands": [
                {"name": record["name"], "outcome": record["outcome"], "exit_code": record["exit_code"]}
                for record in records
            ],
            "matrix": matrix,
            "write_policy": (
                "fail_closed_file_only_not_accepted"
                if arguments.phase == "core-readonly"
                else "file_only_approved" if arguments.phase == "core-full" else "not_exercised"
            ),
            "work_dir": work_state,
            "residual_risk": [
                "Environment thin-Skill integration is a separate Human Gate",
                "a passing preflight or core-readonly phase does not authorize create/update",
                "core-full exercises approved file_only writes; directory metadata fsync is not performed on Windows",
            ],
        }
        _write_json(evidence_dir / "core-summary.json", summary)
        return 0 if status == "passed" else 1
    except (ET.ParseError, OSError, RuntimeError, UnicodeError) as error:
        return _rejection(evidence_dir, arguments.phase, error, work_dir, source)


def main() -> int:
    arguments = _parser().parse_args()
    if arguments.plan:
        print(json.dumps(verification_plan(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    try:
        return _run(arguments)
    except (OSError, RuntimeError, UnicodeError, subprocess.TimeoutExpired) as error:
        print(_json({"contract": CONTRACT, "outcome": "rejected", "summary": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
