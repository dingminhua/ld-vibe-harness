from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from ldvh.testing.test_runs import (
    FALLBACK_STEP_DURATIONS,
    FALLBACK_TOTAL_SECONDS,
    plan_commands,
    recent_step_duration_stats,
    step_duration_seconds,
)
from ldvh.testing.working_tree_evidence import (
    current_complete_coverage,
    finalize_working_tree_evidence,
    manifest_fingerprint,
)


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


def _evidence(workspace: Path) -> dict[str, Any]:
    return finalize_working_tree_evidence(
        governed_project_id="ldvh",
        git_worktree_root=str(workspace),
        git_common_dir=str(workspace / ".git"),
        coverage=current_complete_coverage(),
        before=_manifest(),
        after=_manifest(),
        identities_match=True,
        policies_match=True,
    )


def _write_passed_v2_run(runs_root: Path, index: int, *, lint_seconds: int) -> None:
    run_id = f"run-{index:032x}"
    directory = runs_root / run_id
    directory.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, Any]] = []
    for command in plan_commands(runs_root.parent, "full-v4", 1):
        started_at = "2026-07-20T08:00:00+08:00"
        if command["name"] == "code-lint":
            ended_at = f"2026-07-20T08:00:{lint_seconds:02d}+08:00"
        else:
            ended_at = "2026-07-20T08:00:01+08:00"
        steps.append(
            {
                **command,
                "status": "passed",
                "started_at": started_at,
                "ended_at": ended_at,
                "exit_code": 0,
            }
        )
    record: dict[str, Any] = {
        "contract": "ldvh-test-run/2",
        "run_id": run_id,
        "plan": "full-v4",
        "status": "passed",
        "evidence_complete": True,
        "started_at": "2026-07-20T08:00:00+08:00",
        "ended_at": "2026-07-20T08:00:30+08:00",
        "final_exit_code": 0,
        "raw_output_path": str(directory / "output.log"),
        "record_path": str(directory / "record.json"),
        "workspace": str(runs_root.parent),
        "steps": steps,
        "working_tree_evidence": _evidence(runs_root.parent),
        "diagnostics": [],
        "raw_output_size_bytes": 1,
        "raw_output_sha256": "a" * 64,
    }
    (directory / "record.json").write_text(json.dumps(record), encoding="utf-8")
    (directory / "output.log").write_text("x", encoding="utf-8")


class TestStepDurationDerivation:
    def test_terminal_passed_step_derives_wall_clock_seconds(self) -> None:
        step = {
            "name": "code-lint",
            "status": "passed",
            "started_at": "2026-07-20T08:00:00+08:00",
            "ended_at": "2026-07-20T08:00:05+08:00",
            "exit_code": 0,
        }
        assert step_duration_seconds(step) == 5.0

    def test_failed_step_is_still_terminal(self) -> None:
        step = {
            "name": "code-tests",
            "status": "failed",
            "started_at": "2026-07-20T08:00:00+08:00",
            "ended_at": "2026-07-20T08:00:03+08:00",
            "exit_code": 1,
        }
        assert step_duration_seconds(step) == 3.0

    def test_unknown_step_with_complete_timestamps_is_terminal(self) -> None:
        step = {
            "name": "web-build",
            "status": "unknown",
            "started_at": "2026-07-20T08:00:00+08:00",
            "ended_at": "2026-07-20T08:00:02+08:00",
            "exit_code": None,
        }
        assert step_duration_seconds(step) == 2.0

    def test_non_terminal_steps_derive_nothing(self) -> None:
        assert step_duration_seconds({"status": "not_run", "started_at": None, "ended_at": None}) is None
        assert step_duration_seconds(
            {"status": "running", "started_at": "2026-07-20T08:00:00+08:00", "ended_at": None}
        ) is None

    def test_missing_or_unparseable_timestamps_derive_nothing(self) -> None:
        assert step_duration_seconds({"status": "passed", "started_at": None, "ended_at": None}) is None
        assert step_duration_seconds(
            {"status": "passed", "started_at": "not-a-time", "ended_at": "2026-07-20T08:00:01+08:00"}
        ) is None

    def test_negative_duration_is_rejected(self) -> None:
        step = {
            "status": "passed",
            "started_at": "2026-07-20T08:00:05+08:00",
            "ended_at": "2026-07-20T08:00:00+08:00",
        }
        assert step_duration_seconds(step) is None

    def test_non_dict_step_is_rejected(self) -> None:
        assert step_duration_seconds("not-a-step") is None


class TestRecentStepDurationStats:
    def test_aggregates_most_recent_runs_within_window(self, tmp_path: Path) -> None:
        runs_root = tmp_path / ".ldvh-test-runs"
        for index, seconds in enumerate([5, 7, 9], start=1):
            _write_passed_v2_run(runs_root, index, lint_seconds=seconds)
        stats = recent_step_duration_stats(runs_root, window=5)
        lint = stats["code-lint"]
        assert lint["mean"] == pytest.approx(7.0)
        assert lint["median"] == pytest.approx(7.0)

    def test_window_limits_the_considered_runs(self, tmp_path: Path) -> None:
        runs_root = tmp_path / ".ldvh-test-runs"
        for index, seconds in enumerate([1, 2, 3, 4, 5, 6, 7], start=1):
            _write_passed_v2_run(runs_root, index, lint_seconds=seconds)
        stats = recent_step_duration_stats(runs_root, window=5)
        # Most recent five runs are 7, 6, 5, 4, 3 -> mean 5.0, median 5.0
        assert stats["code-lint"]["mean"] == pytest.approx(5.0)
        assert stats["code-lint"]["median"] == pytest.approx(5.0)

    def test_even_sample_uses_midpoint_median(self, tmp_path: Path) -> None:
        runs_root = tmp_path / ".ldvh-test-runs"
        for index, seconds in enumerate([1, 2, 3, 4], start=1):
            _write_passed_v2_run(runs_root, index, lint_seconds=seconds)
        stats = recent_step_duration_stats(runs_root, window=5)
        # Most recent four runs are 4, 3, 2, 1 -> mean 2.5, median (2+3)/2 = 2.5
        assert stats["code-lint"]["mean"] == pytest.approx(2.5)
        assert stats["code-lint"]["median"] == pytest.approx(2.5)

    def test_no_history_yields_none_with_fallback_entries(self, tmp_path: Path) -> None:
        stats = recent_step_duration_stats(tmp_path / "missing")
        assert set(stats) == set(FALLBACK_STEP_DURATIONS)
        for entry in stats.values():
            assert entry["mean"] is None
            assert entry["median"] is None

    def test_partial_history_uses_available_runs(self, tmp_path: Path) -> None:
        runs_root = tmp_path / ".ldvh-test-runs"
        _write_passed_v2_run(runs_root, 1, lint_seconds=5)
        stats = recent_step_duration_stats(runs_root, window=5)
        assert stats["code-lint"]["mean"] == pytest.approx(5.0)
        assert stats["code-lint"]["median"] == pytest.approx(5.0)

    def test_corrupt_records_are_skipped_without_failing(self, tmp_path: Path) -> None:
        runs_root = tmp_path / ".ldvh-test-runs"
        _write_passed_v2_run(runs_root, 1, lint_seconds=5)
        (runs_root / "run-00000000000000000000000000000099").mkdir(parents=True)
        (runs_root / "run-00000000000000000000000000000099" / "record.json").write_text(
            "{not json", encoding="utf-8"
        )
        stats = recent_step_duration_stats(runs_root, window=5)
        assert stats["code-lint"]["mean"] == pytest.approx(5.0)

    def test_non_terminal_running_record_is_not_counted(self, tmp_path: Path) -> None:
        runs_root = tmp_path / ".ldvh-test-runs"
        _write_passed_v2_run(runs_root, 1, lint_seconds=5)
        # Overwrite with a running record that has no ended_at.
        directory = runs_root / f"run-{1:032x}"
        record = json.loads((directory / "record.json").read_text(encoding="utf-8"))
        record["status"] = "running"
        record["evidence_complete"] = False
        record["ended_at"] = None
        record["final_exit_code"] = None
        record.pop("working_tree_evidence", None)
        (directory / "record.json").write_text(json.dumps(record), encoding="utf-8")
        stats = recent_step_duration_stats(runs_root, window=5)
        assert stats["code-lint"]["mean"] is None


class TestFallbackEstimates:
    def test_fallback_total_matches_sum_of_step_fallbacks(self) -> None:
        assert FALLBACK_TOTAL_SECONDS == pytest.approx(sum(FALLBACK_STEP_DURATIONS.values()))

    def test_fallback_covers_all_fixed_full_v4_step_names(self) -> None:
        commands = plan_commands(Path("/workspace"), "full-v4", 1)
        assert {command["name"] for command in commands} == set(FALLBACK_STEP_DURATIONS)


class TestDurationEstimateTool:
    def test_status_estimate_uses_fallback_when_no_history(self, tmp_path: Path) -> None:
        from tools import run_full_tests as tool_module

        estimate = tool_module.build_duration_estimate(tmp_path / ".ldvh-test-runs")
        assert estimate["history_window"] == 5
        assert estimate["source"] == "fallback"
        assert estimate["estimated_total_seconds"] == pytest.approx(FALLBACK_TOTAL_SECONDS)
        for name in FALLBACK_STEP_DURATIONS:
            step = estimate["steps"][name]
            assert step["source"] == "fallback"
            assert step["estimated_seconds"] == pytest.approx(FALLBACK_STEP_DURATIONS[name])

    def test_status_estimate_uses_history_when_available(self, tmp_path: Path) -> None:
        from tools import run_full_tests as tool_module

        runs_root = tmp_path / ".ldvh-test-runs"
        _write_passed_v2_run(runs_root, 1, lint_seconds=5)
        estimate = tool_module.build_duration_estimate(runs_root)
        assert estimate["source"] == "history"
        assert estimate["steps"]["code-lint"]["mean_seconds"] == pytest.approx(5.0)
        assert estimate["steps"]["code-lint"]["median_seconds"] == pytest.approx(5.0)
        assert estimate["estimated_total_seconds"] is not None
