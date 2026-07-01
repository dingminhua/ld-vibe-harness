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


def test_smoke_profile_uses_fast_formal_validation_stages() -> None:
    runner = _load_runner()

    stages = runner.build_stages("smoke", [])

    assert _stage_names(stages) == ["specs validator", "formal specs hash tests"]


def test_targeted_profile_selects_web_checks_for_web_changes() -> None:
    runner = _load_runner()

    stages = runner.build_stages("targeted", ["web/api/app.ts"])

    assert "specs validator" in _stage_names(stages)
    assert "formal specs hash tests" in _stage_names(stages)
    assert "web typecheck" in _stage_names(stages)
    assert "web api tests" in _stage_names(stages)


def test_targeted_profile_selects_code_and_migration_checks() -> None:
    runner = _load_runner()

    stages = runner.build_stages("targeted", ["code/ldvh_specs.py,_migration/tests/test_migration_gate.py"])

    assert "code pytest" in _stage_names(stages)
    assert "migration pytest" in _stage_names(stages)


def test_full_profile_includes_e2e_full_pytest_and_web_build() -> None:
    runner = _load_runner()

    stages = runner.build_stages("full", [])

    assert "e2e rehearsal" in _stage_names(stages)
    assert "code and migration pytest" in _stage_names(stages)
    assert "web production build" in _stage_names(stages)
