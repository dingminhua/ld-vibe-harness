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
    assert "code runtime core" not in _stage_names(stages)
    assert "code hook adapter checks" not in _stage_names(stages)
    assert "code runtime long-tail" not in _stage_names(stages)


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


def test_verification_plan_explains_targeted_runtime_selection() -> None:
    runner = _load_runner()

    plan = runner.build_verification_plan("targeted", ["code/ldvh_specs.py"], slow_policy="auto")

    assert plan.profile == "targeted"
    assert plan.changed_paths == ("code/ldvh_specs.py",)
    assert "quick_structure" in plan.selected_layers
    assert "targeted_code_fast" in plan.selected_layers
    assert "runtime_core" in plan.selected_layers
    assert "environment_hook_adapter" in plan.selected_layers
    assert "runtime_slow_e2e" in plan.selected_layers
    assert "web_build" in plan.excluded_layers
    assert "runtime_static_e2e" in plan.excluded_layers
    assert any("runtime-sensitive" in reason for reason in plan.selection_reasons)
    assert any("static e2e rehearsal" in item for item in plan.unverified_scope)
    assert plan.matrix_refs == ("specs/09-测试与验证规范.md §5 验证入口选择矩阵",)


def test_verification_plan_matches_runtime_sensitive_spec_selection() -> None:
    runner = _load_runner()

    stages = runner.build_stages("targeted", ["specs/09-测试与验证规范.md"], slow_policy="auto")
    plan = runner.build_verification_plan("targeted", ["specs/09-测试与验证规范.md"], slow_policy="auto")

    assert "code runtime core" in _stage_names(stages)
    assert "code hook adapter checks" in _stage_names(stages)
    assert "code runtime long-tail" in _stage_names(stages)
    assert "runtime_core" in plan.selected_layers
    assert "environment_hook_adapter" in plan.selected_layers
    assert "runtime_slow_e2e" in plan.selected_layers
    assert "runtime_core" not in plan.excluded_layers
    assert any("runtime-sensitive spec selects runtime" in reason for reason in plan.selection_reasons)


def test_verification_plan_records_slow_skip_unverified_scope() -> None:
    runner = _load_runner()

    plan = runner.build_verification_plan("targeted", ["code/ldvh_specs.py"], slow_policy="skip")

    assert "targeted_code_fast" in plan.selected_layers
    assert "runtime_core" in plan.excluded_layers
    assert "runtime_slow_e2e" in plan.excluded_layers
    assert any("slow/runtime/e2e" in item for item in plan.unverified_scope)
    assert any("skipping slow/runtime/e2e" in item for item in plan.residual_risk)


def test_verification_plan_slow_include_without_changed_paths_has_consistent_reason() -> None:
    runner = _load_runner()

    plan = runner.build_verification_plan("targeted", [], slow_policy="include")

    assert "runtime_core" in plan.selected_layers
    assert "environment_hook_adapter" in plan.selected_layers
    assert "runtime_slow_e2e" in plan.selected_layers
    assert not any("stays at smoke baseline" in reason for reason in plan.selection_reasons)
    assert any("starts from smoke baseline" in reason for reason in plan.selection_reasons)
    assert any("slow policy include" in reason for reason in plan.selection_reasons)


def test_verification_plan_expands_full_profile_covered_layers() -> None:
    runner = _load_runner()

    plan = runner.build_verification_plan("full", [], slow_policy="auto")

    assert "code_full" in plan.selected_layers
    assert "runtime_core" in plan.selected_layers
    assert "environment_hook_adapter" in plan.selected_layers
    assert "runtime_slow_e2e" in plan.selected_layers
    assert "environment_plugin" in plan.selected_layers
    assert "web_build" in plan.selected_layers
    assert "fact_instance_validator" in plan.selected_layers
    assert "runtime_core" not in plan.excluded_layers
    assert "environment_hook_adapter" not in plan.excluded_layers
    assert "runtime_slow_e2e" not in plan.excluded_layers


def test_verification_plan_marks_fact_validation_as_selected_for_fact_paths() -> None:
    runner = _load_runner()

    plan = runner.build_verification_plan(
        "targeted",
        ["ldvh-base/workcases/workcase-0024-v2-deletion-readiness-closure.yaml"],
        slow_policy="auto",
    )

    assert "fact_instance_validator" in plan.selected_layers
    assert "fact_instance_validator" not in plan.excluded_layers
    assert any("fact instance path is covered" in reason for reason in plan.selection_reasons)


def test_verification_plan_keeps_real_lifecycle_unverified_for_environment_plugin_checks() -> None:
    runner = _load_runner()

    plan = runner.build_verification_plan(
        "targeted",
        ["hooks/environment-plugins/codex-ldvh-v3/hooks/ldvh_runtime_shim.py"],
        slow_policy="auto",
    )

    assert "environment_plugin" in plan.selected_layers
    assert "environment_plugin" not in plan.excluded_layers
    assert any("real AI lifecycle triggering" in item for item in plan.unverified_scope)
    assert any("external acceptance evidence" in item for item in plan.unverified_scope)


def test_print_verification_plan_includes_scope_and_matrix_ref(capsys) -> None:
    runner = _load_runner()
    plan = runner.build_verification_plan("smoke", [], slow_policy="auto")

    runner.print_verification_plan(plan)

    captured = capsys.readouterr()
    assert "Verification plan:" in captured.out
    assert "- selected_layers:" in captured.out
    assert "- unverified_scope:" in captured.out
    assert "- residual_risk:" in captured.out
    assert "specs/09-测试与验证规范.md §5 验证入口选择矩阵" in captured.out
