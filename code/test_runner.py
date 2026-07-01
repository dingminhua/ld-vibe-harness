from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
import sys
import time
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Stage:
    name: str
    command: tuple[str, ...]


def _python_command(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


SMOKE_STAGES: tuple[Stage, ...] = (
    Stage(
        "specs validator",
        _python_command("code/specs_validate.py", "all", "--format", "text", "--fail-on-diagnostics"),
    ),
    Stage(
        "formal specs hash tests",
        _python_command("-m", "pytest", "tests/code/test_formal_specs.py", "-q"),
    ),
)

FULL_STAGES: tuple[Stage, ...] = (
    *SMOKE_STAGES,
    Stage(
        "e2e rehearsal",
        _python_command(
            "code/specs_validate.py",
            "e2e",
            "--target-path",
            "tests/code/test_ldvh_specs_validate.py",
            "--format",
            "text",
            "--fail-on-diagnostics",
        ),
    ),
    Stage(
        "code and migration pytest",
        _python_command("-m", "pytest", "tests/code", "_migration/tests", "-q", "--durations=20"),
    ),
    Stage("web typecheck", ("npm", "run", "web:check")),
    Stage("web api tests", ("npm", "run", "test:web:api")),
    Stage("web production build", ("npm", "run", "web:build")),
)


def normalize_changed_paths(values: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for value in values:
        for raw in value.split(","):
            path = raw.strip()
            if not path:
                continue
            if path.startswith("./"):
                path = path[2:]
            paths.append(path)
    return paths


def _dedupe(stages: Iterable[Stage]) -> list[Stage]:
    seen: set[tuple[str, ...]] = set()
    deduped: list[Stage] = []
    for stage in stages:
        if stage.command in seen:
            continue
        seen.add(stage.command)
        deduped.append(stage)
    return deduped


def build_targeted_stages(changed_paths: Iterable[str]) -> list[Stage]:
    stages: list[Stage] = list(SMOKE_STAGES)
    paths = normalize_changed_paths(changed_paths)

    for path in paths:
        if path.startswith(("web/", "tests/web/")) or path in {"package.json", "web/package.json", "web/package-lock.json"}:
            stages.extend(
                [
                    Stage("web typecheck", ("npm", "run", "web:check")),
                    Stage("web api tests", ("npm", "run", "test:web:api")),
                ]
            )
        if path.startswith(("code/", "tests/code/")):
            stages.append(Stage("code pytest", _python_command("-m", "pytest", "tests/code", "-q", "--durations=20")))
        if path.startswith(("_migration/code/", "_migration/tests/", "_migration/fixtures/", "_migration/schemas/")):
            stages.append(Stage("migration pytest", _python_command("-m", "pytest", "_migration/tests", "-q", "--durations=20")))
        if path.startswith("ldvh-base/"):
            stages.append(
                Stage(
                    "fact instance validator",
                    _python_command("code/specs_validate.py", "all", "--format", "text", "--fail-on-diagnostics"),
                )
            )

    return _dedupe(stages)


def build_stages(profile: str, changed_paths: Iterable[str]) -> list[Stage]:
    if profile == "smoke":
        return list(SMOKE_STAGES)
    if profile == "targeted":
        return build_targeted_stages(changed_paths)
    if profile == "full":
        return list(FULL_STAGES)
    raise ValueError(f"Unknown profile: {profile}")


def _format_command(command: tuple[str, ...]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _format_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remainder = seconds - minutes * 60
    return f"{minutes}m {remainder:.1f}s"


def run_stages(stages: list[Stage], *, dry_run: bool, continue_on_fail: bool) -> int:
    if not stages:
        print("No test stages selected.")
        return 0

    total = len(stages)
    results: list[tuple[Stage, int, float]] = []
    started_at = time.monotonic()

    for index, stage in enumerate(stages, start=1):
        print(f"[{index}/{total}] {stage.name}", flush=True)
        print(f"      {_format_command(stage.command)}", flush=True)
        if dry_run:
            results.append((stage, 0, 0.0))
            continue

        stage_started_at = time.monotonic()
        completed = subprocess.run(stage.command, cwd=ROOT)
        elapsed = time.monotonic() - stage_started_at
        results.append((stage, completed.returncode, elapsed))
        status = "ok" if completed.returncode == 0 else f"failed({completed.returncode})"
        print(f"[{index}/{total}] {stage.name} ... {status} {_format_seconds(elapsed)}", flush=True)
        if completed.returncode != 0 and not continue_on_fail:
            break

    total_elapsed = time.monotonic() - started_at
    print("\nSummary:", flush=True)
    for stage, returncode, elapsed in results:
        status = "ok" if returncode == 0 else f"failed({returncode})"
        duration = "dry-run" if dry_run else _format_seconds(elapsed)
        print(f"- {stage.name}: {status} ({duration})", flush=True)
    print(f"- total: {'dry-run' if dry_run else _format_seconds(total_elapsed)}", flush=True)

    failures = [returncode for _, returncode, _ in results if returncode != 0]
    return failures[0] if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run LDVH v3 test profiles with stage progress.")
    parser.add_argument("profile", choices=["smoke", "targeted", "full"], help="test profile to run")
    parser.add_argument(
        "--changed",
        action="append",
        default=[],
        help="changed path for targeted selection; may be repeated or comma-separated",
    )
    parser.add_argument("--dry-run", action="store_true", help="print selected stages without running them")
    parser.add_argument("--continue-on-fail", action="store_true", help="continue running later stages after a failure")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    stages = build_stages(args.profile, args.changed)
    return run_stages(stages, dry_run=args.dry_run, continue_on_fail=args.continue_on_fail)


if __name__ == "__main__":
    raise SystemExit(main())
