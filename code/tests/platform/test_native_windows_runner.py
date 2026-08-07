from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = PROJECT_ROOT / "tools/verify_native_windows.py"


def _runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_native_windows", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _repository(root: Path) -> tuple[Path, str]:
    source = root / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q", str(source)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "config", "user.name", "LDVH Test"], check=True)
    subprocess.run(["git", "-C", str(source), "config", "user.email", "ldvh@example.invalid"], check=True)
    (source / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(source), "commit", "-qm", "initial"], check=True)
    commit = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        text=True,
        encoding="ascii",
        capture_output=True,
        check=True,
    ).stdout.strip()
    return source.resolve(), commit


def test_plan_is_cross_platform_read_only_and_separates_support_conclusions(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(RUNNER_PATH), "--plan"],
        cwd=tmp_path,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    plan = json.loads(completed.stdout)
    assert plan["contract"] == "ldvh-native-windows-verification/1"
    assert set(plan["phases"]) == {"preflight", "core-readonly", "core-full", "adapter-handoff"}
    assert plan["phases"]["core-full"]["human_gate"]
    assert set(plan["phases"]["core-full"]["matrix"].values()) == {"scheduled"}
    assert plan["phases"]["adapter-handoff"]["automated"] is False
    assert tuple(tmp_path.iterdir()) == ()


def test_non_windows_execution_rejects_without_creating_evidence(tmp_path: Path) -> None:
    if sys.platform == "win32":
        pytest.skip("non-Windows rejection is exercised on non-Windows development hosts")
    evidence = tmp_path / "evidence"

    completed = subprocess.run(
        [sys.executable, str(RUNNER_PATH), "--phase", "preflight", "--evidence-dir", str(evidence)],
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode == 2
    assert completed.stderr == ""
    response = json.loads(completed.stdout)
    assert response["outcome"] == "rejected"
    assert "use --plan" in response["summary"]
    assert not evidence.exists()


def test_phase_commands_are_policy_separated_and_use_argv(tmp_path: Path) -> None:
    runner = _runner()
    source = tmp_path / "source"
    work = tmp_path / "work"

    preflight = runner._commands("preflight", source, work)
    readonly = runner._commands("core-readonly", source, work)
    full = runner._commands("core-full", source, work)

    def names(commands: list[tuple[str, list[str]]]) -> set[str]:
        return {name for name, _ in commands}

    assert all(isinstance(argv, list) and argv and all(isinstance(item, str) for item in argv) for _, argv in full)
    assert "write-policy-probes" not in names(preflight)
    assert "write-policy-probes" in names(readonly)
    assert "approved-write-probes" not in names(readonly)
    assert "approved-write-probes" in names(full)
    assert "full-suite" not in names(full)
    dependency_command = dict(preflight)["prepare-dependencies"]
    assert str(source / "requirements-dev.txt") in dependency_command
    assert str(source) not in dependency_command
    assert runner.verification_plan()["phases"]["adapter-handoff"]["automated"] is False


def test_runner_never_enables_a_shell() -> None:
    tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    subprocess_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"run", "Popen"}
    ]

    assert subprocess_calls
    assert all(
        not any(
            keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
            for keyword in call.keywords
        )
        for call in subprocess_calls
    )


def test_child_environment_removes_ambient_python_pip_git_and_proxy_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _runner()
    hostile = {
        "PYTEST_ADDOPTS": "--collect-only",
        "PYTHONPATH": "shadow-package",
        "PIP_INDEX_URL": "https://credential@example.invalid/simple",
        "PIP_CONFIG_FILE": "private.ini",
        "GIT_CONFIG_GLOBAL": "private.gitconfig",
        "HTTPS_PROXY": "https://credential@proxy.invalid",
    }
    for key, value in hostile.items():
        monkeypatch.setenv(key, value)

    environment = runner._child_environment(tmp_path / "work")

    for key, hostile_value in hostile.items():
        assert environment.get(key) != hostile_value
    assert "PYTEST_ADDOPTS" not in environment
    assert "PYTHONPATH" not in environment
    assert "PIP_INDEX_URL" not in environment
    assert "GIT_CONFIG_GLOBAL" not in environment
    assert "HTTPS_PROXY" not in environment
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["PIP_CONFIG_FILE"] == os.devnull
    assert Path(environment["TEMP"]).is_dir()


def test_recorded_command_uses_clean_environment_and_cannot_be_changed_to_collect_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _runner()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTHONPATH", "shadow-package")
    environment = runner._child_environment(tmp_path / "work")
    argv = [
        sys.executable,
        "-c",
        "import os,sys; sys.exit(0 if 'PYTEST_ADDOPTS' not in os.environ and 'PYTHONPATH' not in os.environ else 9)",
    ]

    record = runner._record_command(evidence, 1, "clean-env", argv, tmp_path, environment)

    assert record["outcome"] == "completed"
    assert record["exit_code"] == 0
    assert (evidence / record["stdout"]["path"]).read_bytes() == b""


def test_source_identity_requires_exact_clean_git_top_level_and_full_commit(tmp_path: Path) -> None:
    runner = _runner()
    source, commit = _repository(tmp_path)
    arguments = runner._parser().parse_args(
        ["--phase", "preflight", "--source-root", str(source), "--source-commit", commit]
    )

    identity = runner._source_identity(source, arguments)

    assert identity["kind"] == "clean_git_worktree"
    assert identity["top_level"] == str(source)
    assert identity["commit"] == commit
    assert identity["clean"] is True

    nested = source / "nested"
    nested.mkdir()
    nested_arguments = runner._parser().parse_args(["--source-root", str(nested)])
    with pytest.raises(RuntimeError, match="top level"):
        runner._source_identity(nested.resolve(), nested_arguments)


def test_source_identity_rejects_wrong_commit_and_dirty_worktree(tmp_path: Path) -> None:
    runner = _runner()
    source, _commit = _repository(tmp_path)
    wrong = runner._parser().parse_args(["--source-root", str(source), "--source-commit", "a" * 40])
    with pytest.raises(RuntimeError, match="does not match"):
        runner._source_identity(source, wrong)

    (source / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    arguments = runner._parser().parse_args(["--source-root", str(source)])
    with pytest.raises(RuntimeError, match="must be clean"):
        runner._source_identity(source, arguments)


def test_command_timeout_and_os_error_are_structured_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _runner()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    environment = runner._child_environment(tmp_path / "work")

    def timeout(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(["probe"], runner.COMMAND_TIMEOUT_SECONDS, output=b"partial")

    monkeypatch.setattr(runner.subprocess, "run", timeout)
    timed_out = runner._record_command(evidence, 1, "timeout", ["probe"], tmp_path, environment)
    assert timed_out["outcome"] == "timeout"
    assert timed_out["exit_code"] is None
    assert (evidence / timed_out["stdout"]["path"]).read_bytes() == b"partial"

    def os_error(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated launch failure")

    monkeypatch.setattr(runner.subprocess, "run", os_error)
    failed = runner._record_command(evidence, 2, "os-error", ["probe"], tmp_path, environment)
    assert failed["outcome"] == "os_error"
    assert b"simulated launch failure" in (evidence / failed["stderr"]["path"]).read_bytes()


def test_junit_probe_matrix_reports_pass_skip_fail_and_policy_blocks(tmp_path: Path) -> None:
    runner = _runner()
    work = tmp_path / "work"
    work.mkdir()
    (work / "native-probes.xml").write_text(
        """<?xml version='1.0' encoding='utf-8'?>
<testsuites><testsuite>
  <testcase name='test_native_junction_is_rejected_before_read'/>
  <testcase name='test_native_symlink_is_rejected_when_privilege_is_available'><skipped/></testcase>
  <testcase name='test_native_drive_letter_case_alias_reads_the_same_file'><failure/></testcase>
</testsuite></testsuites>
""",
        encoding="utf-8",
    )

    matrix = runner._probe_matrix(work, "preflight")

    assert matrix["junction_rejection"] == "passed"
    assert matrix["symlink_rejection"] == "skipped"
    assert matrix["drive_case_alias"] == "failed"
    assert matrix["public_write_fail_closed"] == "not_run"
    assert matrix["allocator_six_process_contiguous_ids"] == "blocked_by_file_only_human_gate"


def test_junit_probe_matrix_parses_approved_write_probes_for_core_full(tmp_path: Path) -> None:
    runner = _runner()
    work = tmp_path / "work"
    work.mkdir()
    (work / "approved-write-probes.xml").write_text(
        """<?xml version='1.0' encoding='utf-8'?>
<testsuites><testsuite>
  <testcase name='test_native_six_process_allocator_contiguous_ids'/>
  <testcase name='test_native_conditional_update_single_winner'><failure/></testcase>
</testsuite></testsuites>
""",
        encoding="utf-8",
    )

    matrix = runner._probe_matrix(work, "core-full")

    assert matrix["allocator_six_process_contiguous_ids"] == "passed"
    assert matrix["main_linked_shared_counter"] == "not_run"
    assert matrix["conditional_update_single_winner"] == "failed"


def test_embedded_lock_worker_is_valid_python() -> None:
    native_module_path = PROJECT_ROOT / "code/tests/platform/test_native_windows.py"
    tree = ast.parse(native_module_path.read_text(encoding="utf-8"))
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "LOCK_WORKER" for target in node.targets)
    )
    assert isinstance(assignment.value, ast.Constant)
    assert isinstance(assignment.value.value, str)

    compile(assignment.value.value, "<native-lock-worker>", "exec")


def test_rejection_initialization_keeps_the_five_contract_files(tmp_path: Path) -> None:
    runner = _runner()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    work = evidence / "_work"
    work.mkdir()
    runner._write_json(evidence / "source.json", {"commit": "a" * 40})
    runner._pending_summaries(evidence, "preflight")
    runner._write_json(evidence / "environment.json", {"platform": "simulated"})

    exit_code = runner._rejection(evidence, "preflight", RuntimeError("simulated rejection"), work)

    assert exit_code == 2
    assert all((evidence / name).is_file() for name in runner.EVIDENCE_FILES)
    assert json.loads((evidence / "core-summary.json").read_text(encoding="utf-8"))["status"] == "rejected"
    assert work.is_dir()


def test_cleanup_failure_is_explicit_and_preserves_the_work_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _runner()
    work = tmp_path / "_work"
    work.mkdir()

    def fail_cleanup(_path: Path) -> None:
        raise OSError("simulated cleanup failure")

    monkeypatch.setattr(runner.shutil, "rmtree", fail_cleanup)

    status, residual, error = runner._remove_work_dir(work)

    assert status == "failed_cleanup"
    assert residual == str(work)
    assert isinstance(error, OSError)
    assert work.is_dir()


def test_initialization_failure_after_evidence_creation_still_closes_the_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _runner()
    evidence = tmp_path / "evidence"
    source = {"kind": "clean_git_worktree", "commit": "a" * 40, "clean": True}

    def fail_pending(_evidence: Path, _phase: str) -> None:
        raise OSError("simulated initialization failure")

    monkeypatch.setattr(runner, "_pending_summaries", fail_pending)

    work, exit_code = runner._initialize_evidence(evidence, "preflight", source)

    assert exit_code == 2
    assert work.is_dir()
    assert all((evidence / name).is_file() for name in runner.EVIDENCE_FILES)
    assert (evidence / "rejection.json").is_file()
    assert json.loads((evidence / "core-summary.json").read_text(encoding="utf-8"))["status"] == "rejected"
