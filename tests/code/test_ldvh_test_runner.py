from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    spec = importlib.util.spec_from_file_location("ldvh_test_runner", ROOT / "code" / "test_runner.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _stage_names(stages) -> list[str]:
    return [stage.name for stage in stages]


def _pytest_stages(stages) -> list:
    return [stage for stage in stages if len(stage.command) >= 3 and stage.command[1:3] == ("-m", "pytest")]


def test_all_pytest_stages_use_short_tracebacks() -> None:
    runner = _load_runner()

    stage_sets = [
        runner.build_stages("smoke", []),
        runner.build_stages("runtime", []),
        runner.build_stages("full", []),
        runner.build_stages(
            "targeted",
            ["code/ldvh_specs.py"],
            slow_policy="include",
        ),
    ]

    missing = [stage.name for stages in stage_sets for stage in _pytest_stages(stages) if "--tb=short" not in stage.command]

    assert missing == []


def test_smoke_profile_uses_fast_formal_validation_stages() -> None:
    runner = _load_runner()

    stages = runner.build_stages("smoke", [])

    assert _stage_names(stages) == ["specs validator", "formal specs structure tests"]


def test_targeted_profile_selects_web_checks_for_web_changes() -> None:
    runner = _load_runner()

    stages = runner.build_stages("targeted", ["web/api/app.ts"])

    assert "specs validator" in _stage_names(stages)
    assert "formal specs structure tests" in _stage_names(stages)
    assert "web typecheck" in _stage_names(stages)
    assert "web api tests" in _stage_names(stages)


def test_targeted_profile_selects_code_checks() -> None:
    runner = _load_runner()

    stages = runner.build_stages("targeted", ["code/ldvh_specs.py"])

    assert "code pytest fast" in _stage_names(stages)
    assert "code runtime core" in _stage_names(stages)
    assert "code hook adapter checks" in _stage_names(stages)
    assert "code runtime long-tail" in _stage_names(stages)


def test_targeted_profile_selects_environment_plugin_checks_for_hook_assets() -> None:
    runner = _load_runner()

    stages = runner.build_stages(
        "targeted",
        ["hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"],
    )

    assert "environment plugin checks" in _stage_names(stages)


def test_targeted_profile_can_skip_slow_runtime_checks() -> None:
    runner = _load_runner()

    stages = runner.build_stages("targeted", ["code/ldvh_specs.py"], slow_policy="skip")

    assert "code pytest fast" in _stage_names(stages)
    assert "code runtime/e2e pytest" not in _stage_names(stages)


def test_runtime_profile_runs_runtime_tier_without_web_build() -> None:
    runner = _load_runner()

    stages = runner.build_stages("runtime", [])

    assert "specs validator" in _stage_names(stages)
    assert "e2e rehearsal" in _stage_names(stages)
    assert "code runtime core" in _stage_names(stages)
    assert "code hook adapter checks" in _stage_names(stages)
    assert "code runtime long-tail" in _stage_names(stages)
    assert "web production build" not in _stage_names(stages)


def test_full_profile_includes_e2e_full_pytest_and_web_build() -> None:
    runner = _load_runner()

    stages = runner.build_stages("full", [])

    assert "e2e rehearsal" in _stage_names(stages)
    assert "code pytest" in _stage_names(stages)
    assert "web production build" in _stage_names(stages)
