#!/usr/bin/env python3
"""Start and read a durable LDVH complete-test run record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from ldvh.testing.test_runs import (  # noqa: E402
    FALLBACK_STEP_DURATIONS,
    FALLBACK_TOTAL_SECONDS,
    observe_run,
    recent_step_duration_stats,
    run_worker,
    start_run,
    wait_for_run,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subcommands = result.add_subparsers(dest="command", required=True)
    for name in ("start", "status", "wait"):
        command = subcommands.add_parser(name)
        command.add_argument("--runs-root", default=str(PROJECT_ROOT / ".ldvh-test-runs"))
        if name == "start":
            command.add_argument("--workspace", default=str(PROJECT_ROOT))
            command.add_argument("--plan", choices=("full-v4", "probe"), default="full-v4")
            command.add_argument("--probe-seconds", type=int, default=3)
        elif name == "status":
            command.add_argument("--run-id", default=None)
        else:
            command.add_argument("--run-id", required=True)
        if name == "wait":
            command.add_argument("--timeout-seconds", type=int, default=30)
    worker = subcommands.add_parser("_worker")
    worker.add_argument("--run-dir", required=True)
    return result


def emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _round_seconds(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 1)


def build_duration_estimate(runs_root: Path, *, window: int = 5) -> dict[str, object]:
    """Build the per-step duration estimate consumed by ``status``.

    Real aggregates come from the most recent ``window`` terminal v2 runs;
    steps without history fall back to the fixed experience values and are
    flagged with ``"source": "fallback"`` so the caller can distinguish them
    from measured data.
    """

    stats = recent_step_duration_stats(runs_root, window=window)
    steps: dict[str, object] = {}
    measured_total = 0.0
    fallback_used = False
    for name, fallback in FALLBACK_STEP_DURATIONS.items():
        entry = stats.get(name) or {}
        mean = entry.get("mean")
        if mean is None:
            steps[name] = {
                "estimated_seconds": _round_seconds(fallback),
                "source": "fallback",
                "mean_seconds": None,
                "median_seconds": None,
            }
            fallback_used = True
        else:
            measured_total += float(mean)
            steps[name] = {
                "estimated_seconds": _round_seconds(mean),
                "source": "history",
                "mean_seconds": _round_seconds(mean),
                "median_seconds": _round_seconds(entry.get("median")),
            }
    total = measured_total if not fallback_used else FALLBACK_TOTAL_SECONDS
    return {
        "estimated_total_seconds": _round_seconds(total),
        "history_window": window,
        "source": "fallback" if fallback_used else "history",
        "steps": steps,
    }


def main() -> int:
    arguments = parser().parse_args()
    if arguments.command == "_worker":
        run_worker(Path(arguments.run_dir))
        return 0
    try:
        runs_root = Path(arguments.runs_root)
        if arguments.command == "start":
            response = start_run(
                workspace=Path(arguments.workspace),
                runs_root=runs_root,
                plan=arguments.plan,
                probe_seconds=arguments.probe_seconds,
                tool_path=Path(__file__).resolve(),
            )
        elif arguments.command == "status":
            if arguments.run_id is None:
                emit(
                    {
                        "kind": "duration-estimate",
                        "duration_estimate": build_duration_estimate(runs_root),
                    }
                )
                return 0
            response = observe_run(runs_root=runs_root, run_id=arguments.run_id)
        else:
            response = wait_for_run(
                runs_root=runs_root, run_id=arguments.run_id, timeout_seconds=arguments.timeout_seconds
            )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        emit({"status": "unknown", "evidence_complete": False, "observation_error": str(error)})
        return 2
    emit(response)
    return 0 if response["status"] in {"passed", "running", "starting"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
