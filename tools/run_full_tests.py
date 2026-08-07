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
    observe_run,
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
        else:
            command.add_argument("--run-id", required=True)
        if name == "wait":
            command.add_argument("--timeout-seconds", type=int, default=30)
    worker = subcommands.add_parser("_worker")
    worker.add_argument("--run-dir", required=True)
    return result


def emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


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
