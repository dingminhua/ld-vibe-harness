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
STAGE_TIMEOUT_SECONDS = 1200


@dataclass(frozen=True)
class Stage:
    name: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class VerificationPlan:
    profile: str
    changed_paths: tuple[str, ...]
    slow_policy: str
    selected_layers: tuple[str, ...]
    excluded_layers: tuple[str, ...]
    selection_reasons: tuple[str, ...]
    unverified_scope: tuple[str, ...]
    residual_risk: tuple[str, ...]
    matrix_refs: tuple[str, ...]


def _python_command(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


SMOKE_STAGES: tuple[Stage, ...] = (
    Stage(
        "specs validator",
        _python_command("code/specs_validate.py", "all", "--format", "text", "--fail-on-diagnostics"),
    ),
    Stage(
        "formal specs structure tests",
        _python_command("-m", "pytest", "tests/code/test_formal_specs.py", "-q", "--tb=short"),
    ),
)

E2E_REHEARSAL_STAGE = Stage(
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
)
CODE_FAST_STAGE = Stage(
    "code pytest fast",
    _python_command("-m", "pytest", "tests/code", "-q", "-m", "not slow", "--durations=10", "--tb=short"),
)
CODE_RUNTIME_CORE_STAGE = Stage(
    "code runtime core",
    _python_command(
        "-m",
        "pytest",
        "tests/code",
        "-q",
        "-m",
        "runtime and not runtime_slow and not hook_adapter",
        "--durations=20",
        "--tb=short",
    ),
)
CODE_HOOK_ADAPTER_STAGE = Stage(
    "code hook adapter checks",
    _python_command(
        "-m",
        "pytest",
        "tests/code",
        "-q",
        "-m",
        "hook_adapter",
        "--durations=20",
        "--tb=short",
    ),
)
CODE_RUNTIME_SLOW_STAGE = Stage(
    "code runtime long-tail",
    _python_command(
        "-m",
        "pytest",
        "tests/code",
        "-q",
        "-m",
        "runtime_slow or e2e",
        "--durations=20",
        "--tb=short",
    ),
)
CODE_FULL_STAGE = Stage(
    "code pytest",
    _python_command("-m", "pytest", "tests/code", "-q", "--durations=20", "--tb=short"),
)
ENVIRONMENT_PLUGIN_STAGE = Stage(
    "environment plugin checks",
    _python_command(
        "-m",
        "pytest",
        "tests/code/test_environment_plugins.py",
        "tests/code/test_install_verification.py",
        "-q",
        "--tb=short",
    ),
)
RUNTIME_STAGES: tuple[Stage, ...] = (
    *SMOKE_STAGES,
    E2E_REHEARSAL_STAGE,
    CODE_RUNTIME_CORE_STAGE,
    CODE_HOOK_ADAPTER_STAGE,
    CODE_RUNTIME_SLOW_STAGE,
)
FULL_STAGES: tuple[Stage, ...] = (
    *SMOKE_STAGES,
    E2E_REHEARSAL_STAGE,
    CODE_FULL_STAGE,
    Stage("web typecheck", ("npm", "run", "web:check")),
    Stage("web api tests", ("npm", "run", "test:web:api")),
    Stage("web production build", ("npm", "run", "web:build")),
)
RUNTIME_SENSITIVE_PATHS = {
    "code/ldvh_specs.py",
    "code/specs_validate.py",
    "code/runtime_adapter.py",
    "code/session_start.py",
    "code/pre_tool_use.py",
    "code/completion_claim.py",
    "code/environment_status.py",
    "code/environment_entry_audit.py",
    "code/install_verification.py",
    "tests/code/test_ldvh_specs_validate.py",
    "tests/code/test_install_verification.py",
}
RUNTIME_SENSITIVE_PREFIXES = (
    "specs/01-",
    "specs/02-",
    "specs/07-",
    "specs/09-",
    "specs/attachments/01.Att.",
)

STAGE_LAYER_LABELS = {
    "specs validator": ("quick_structure", "fact_instance_validator"),
    "formal specs structure tests": ("quick_structure",),
    "e2e rehearsal": ("runtime_static_e2e",),
    "code pytest fast": ("targeted_code_fast",),
    "code runtime core": ("runtime_core",),
    "code hook adapter checks": ("environment_hook_adapter",),
    "code runtime long-tail": ("runtime_slow_e2e",),
    "code pytest": (
        "targeted_code_fast",
        "runtime_core",
        "environment_hook_adapter",
        "runtime_slow_e2e",
        "environment_plugin",
        "code_full",
    ),
    "environment plugin checks": ("environment_plugin",),
    "web typecheck": ("web_typecheck",),
    "web api tests": ("web_api",),
    "web production build": ("web_build",),
    "fact instance validator": ("fact_instance_validator",),
}

ALL_VERIFICATION_LAYERS = (
    "quick_structure",
    "targeted_code_fast",
    "runtime_core",
    "environment_hook_adapter",
    "runtime_static_e2e",
    "runtime_slow_e2e",
    "environment_plugin",
    "web_typecheck",
    "web_api",
    "web_build",
    "code_full",
    "fact_instance_validator",
)


def _path_requires_runtime_tier(path: str) -> bool:
    return path in RUNTIME_SENSITIVE_PATHS or path.startswith(RUNTIME_SENSITIVE_PREFIXES)


def _include_runtime_tier(paths: list[str], slow_policy: str) -> bool:
    if slow_policy == "include":
        return True
    if slow_policy == "skip":
        return False
    return any(_path_requires_runtime_tier(path) for path in paths)


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


def _stage_layers(stages: Iterable[Stage]) -> tuple[str, ...]:
    layers: list[str] = []
    for stage in stages:
        stage_layers = STAGE_LAYER_LABELS.get(stage.name, (stage.name,))
        for layer in stage_layers:
            if layer not in layers:
                layers.append(layer)
    return tuple(layers)


def _excluded_layers(selected_layers: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(layer for layer in ALL_VERIFICATION_LAYERS if layer not in selected_layers)


def _selection_reasons(profile: str, paths: list[str], slow_policy: str) -> tuple[str, ...]:
    if profile == "smoke":
        return ("smoke profile selected: quick structure and fact instance validation checks, matching specs/09 §5 fast layer.",)
    if profile == "runtime":
        return (
            "runtime profile selected: covers runtime facade, preflight, completion claim, hook adapter checks and static e2e rehearsal.",
        )
    if profile == "full":
        return (
            "full profile selected: stage closure, cross-domain migration or release-level confidence; includes slow layer and web checks.",
        )

    reasons = ["targeted profile selected: start from quick structure checks, then add stages by changed path."]
    if not paths:
        if slow_policy == "include":
            reasons.append("no changed paths provided: targeted profile starts from smoke baseline; slow policy include still selects runtime layers.")
        else:
            reasons.append("no changed paths provided: targeted profile stays at smoke baseline.")
    if slow_policy == "skip":
        reasons.append("slow policy skip: runtime/e2e slow layers are excluded and must be declared as unverified scope.")
    elif slow_policy == "include":
        reasons.append("slow policy include: runtime/e2e layers are selected even if changed paths do not require them.")
    else:
        reasons.append("slow policy auto: runtime/e2e layers are selected only for runtime-sensitive paths.")

    for path in paths:
        if path.startswith(("web/", "tests/web/")) or path in {"package.json", "web/package.json", "web/package-lock.json"}:
            reasons.append(f"{path}: web path selects web typecheck and web API tests.")
        if path.startswith(("code/", "tests/code/")):
            reasons.append(f"{path}: code/tests path selects targeted code pytest.")
            if _include_runtime_tier([path], slow_policy):
                reasons.append(f"{path}: runtime-sensitive or slow policy include selects runtime and hook adapter layers.")
            elif _path_requires_runtime_tier(path):
                reasons.append(f"{path}: runtime-sensitive path has runtime and hook adapter layers excluded by slow policy.")
        if path.startswith("hooks/environment-plugins/"):
            reasons.append(f"{path}: environment plugin asset selects environment plugin checks.")
        if path.startswith("ldvh-base/"):
            reasons.append(f"{path}: fact instance path is covered by specs validator / fact instance validation.")
        if path.startswith("specs/"):
            if _path_requires_runtime_tier(path):
                if _include_runtime_tier([path], slow_policy):
                    reasons.append(f"{path}: runtime-sensitive spec selects runtime and hook adapter layers.")
                else:
                    reasons.append(f"{path}: runtime-sensitive spec has runtime and hook adapter layers excluded by slow policy.")
            else:
                reasons.append(f"{path}: spec text is covered by specs validator and formal structure checks.")
    return tuple(reasons)


def _unverified_scope(
    profile: str,
    selected_layers: tuple[str, ...],
    excluded_layers: tuple[str, ...],
    slow_policy: str,
) -> tuple[str, ...]:
    scope: list[str] = []
    if profile == "smoke":
        scope.append("target-specific code, runtime/e2e, environment plugin, web and full-build behavior are not covered.")
    if profile == "targeted":
        if "runtime_core" in excluded_layers or "runtime_slow_e2e" in excluded_layers:
            scope.append("runtime facade, pre_tool_use, completion_claim and static e2e slow coverage may be unverified.")
        if "runtime_static_e2e" in excluded_layers:
            scope.append("static e2e rehearsal is not covered by this targeted plan.")
        if "web_typecheck" in excluded_layers and "web_api" in excluded_layers:
            scope.append("web TypeScript/API behavior is unverified unless selected by changed paths.")
        if "web_build" in excluded_layers:
            scope.append("production web build is excluded from targeted profile.")
        if slow_policy == "skip":
            scope.append("slow/runtime/e2e layers were intentionally skipped by policy.")
    if profile == "runtime":
        scope.append("web typecheck, web API and production web build are not covered by runtime profile.")
    if profile == "full" and not excluded_layers:
        scope.append("external services not modeled by the local runner remain outside this plan.")
    scope.append("target environment installation, real AI lifecycle triggering and Human acceptance require external acceptance evidence outside this local runner.")
    return tuple(scope)


def _residual_risk(profile: str, excluded_layers: tuple[str, ...], slow_policy: str) -> tuple[str, ...]:
    risks = [
        "runner output is verification evidence only; it does not replace Human Gate, source-of-truth review or completion judgment.",
    ]
    if profile != "full":
        risks.append("non-selected layers can still hide regressions outside this change scope.")
    if slow_policy == "skip":
        risks.append("skipping slow/runtime/e2e layers increases risk for runtime facade and hook-adapter regressions.")
    if "web_build" in excluded_layers:
        risks.append("production build regressions remain possible until full profile or equivalent web build runs.")
    return tuple(risks)


def build_verification_plan(
    profile: str,
    changed_paths: Iterable[str],
    *,
    slow_policy: str = "auto",
) -> VerificationPlan:
    paths = normalize_changed_paths(changed_paths)
    stages = build_stages(profile, paths, slow_policy=slow_policy)
    selected_layers = _stage_layers(stages)
    excluded = _excluded_layers(selected_layers)
    return VerificationPlan(
        profile=profile,
        changed_paths=tuple(paths),
        slow_policy=slow_policy,
        selected_layers=selected_layers,
        excluded_layers=excluded,
        selection_reasons=_selection_reasons(profile, paths, slow_policy),
        unverified_scope=_unverified_scope(profile, selected_layers, excluded, slow_policy),
        residual_risk=_residual_risk(profile, excluded, slow_policy),
        matrix_refs=("specs/09-测试与验证规范.md §5 验证入口选择矩阵",),
    )


def build_targeted_stages(changed_paths: Iterable[str], *, slow_policy: str = "auto") -> list[Stage]:
    stages: list[Stage] = list(SMOKE_STAGES)
    paths = normalize_changed_paths(changed_paths)
    include_runtime = _include_runtime_tier(paths, slow_policy)

    for path in paths:
        if path.startswith(("web/", "tests/web/")) or path in {"package.json", "web/package.json", "web/package-lock.json"}:
            stages.extend(
                [
                    Stage("web typecheck", ("npm", "run", "web:check")),
                    Stage("web api tests", ("npm", "run", "test:web:api")),
                ]
            )
        if path.startswith(("code/", "tests/code/")):
            stages.append(CODE_FAST_STAGE)
            if include_runtime:
                stages.append(CODE_RUNTIME_CORE_STAGE)
                stages.append(CODE_HOOK_ADAPTER_STAGE)
                if slow_policy in {"auto", "include"}:
                    stages.append(CODE_RUNTIME_SLOW_STAGE)
        if path.startswith("hooks/environment-plugins/"):
            stages.append(ENVIRONMENT_PLUGIN_STAGE)
        if path.startswith("ldvh-base/"):
            stages.append(
                Stage(
                    "fact instance validator",
                    _python_command("code/specs_validate.py", "all", "--format", "text", "--fail-on-diagnostics"),
                )
            )

    if include_runtime:
        stages.append(CODE_RUNTIME_CORE_STAGE)
        stages.append(CODE_HOOK_ADAPTER_STAGE)
        if slow_policy in {"auto", "include"}:
            stages.append(CODE_RUNTIME_SLOW_STAGE)

    return _dedupe(stages)


def build_stages(profile: str, changed_paths: Iterable[str], *, slow_policy: str = "auto") -> list[Stage]:
    if profile == "smoke":
        return list(SMOKE_STAGES)
    if profile == "targeted":
        return build_targeted_stages(changed_paths, slow_policy=slow_policy)
    if profile == "runtime":
        return list(RUNTIME_STAGES)
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


def _print_list(label: str, values: Iterable[str]) -> None:
    print(f"- {label}:")
    listed = list(values)
    if not listed:
        print("  - none")
        return
    for value in listed:
        print(f"  - {value}")


def print_verification_plan(plan: VerificationPlan) -> None:
    print("Verification plan:", flush=True)
    print(f"- profile: {plan.profile}", flush=True)
    print(f"- slow_policy: {plan.slow_policy}", flush=True)
    _print_list("changed_paths", plan.changed_paths)
    _print_list("selected_layers", plan.selected_layers)
    _print_list("excluded_layers", plan.excluded_layers)
    _print_list("selection_reasons", plan.selection_reasons)
    _print_list("unverified_scope", plan.unverified_scope)
    _print_list("residual_risk", plan.residual_risk)
    _print_list("matrix_refs", plan.matrix_refs)
    print("", flush=True)


def run_stages(
    stages: list[Stage],
    *,
    dry_run: bool,
    continue_on_fail: bool,
) -> int:
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
        try:
            completed = subprocess.run(stage.command, cwd=ROOT, timeout=STAGE_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - stage_started_at
            returncode = 124
            results.append((stage, returncode, elapsed))
            print(
                f"[{index}/{total}] {stage.name} ... timeout({STAGE_TIMEOUT_SECONDS}s)",
                flush=True,
            )
            if not continue_on_fail:
                break
            continue
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
    parser.add_argument("profile", choices=["smoke", "targeted", "runtime", "full"], help="test profile to run")
    parser.add_argument(
        "--changed",
        action="append",
        default=[],
        help="changed path for targeted selection; may be repeated or comma-separated",
    )
    parser.add_argument(
        "--slow",
        choices=["auto", "skip", "include"],
        default="auto",
        help="targeted slow test policy: auto selects runtime/e2e by changed paths, skip omits it, include always adds it",
    )
    parser.add_argument("--dry-run", action="store_true", help="print selected stages without running them")
    parser.add_argument("--continue-on-fail", action="store_true", help="continue running later stages after a failure")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    stages = build_stages(args.profile, args.changed, slow_policy=args.slow)
    plan = build_verification_plan(args.profile, args.changed, slow_policy=args.slow)
    print_verification_plan(plan)
    return run_stages(stages, dry_run=args.dry_run, continue_on_fail=args.continue_on_fail)


if __name__ == "__main__":
    raise SystemExit(main())
