from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from action_guide import compile_action_guide, load_formatted_source  # noqa: E402


def test_code_determinism_spec_compiles_to_action_guide() -> None:
    spec = load_formatted_source(ROOT / "specs" / "code-determinism.yaml")

    guide = compile_action_guide(spec)

    assert guide["guide_type"] == "action_guide"
    assert guide["result_status"] == "usable"
    assert guide["target"]["id"] == "SPEC-CODE-DETERMINISM"
    assert guide["read_plan"][0]["target"] == "specs/code-determinism.yaml"


def test_code_determinism_spec_does_not_depend_on_migration_scaffold() -> None:
    spec_path = ROOT / "specs" / "code-determinism.yaml"
    raw = spec_path.read_text(encoding="utf-8")
    spec = yaml.safe_load(raw)

    assert "_migration/" not in raw
    assert spec["source_refs"][0]["path"] == "specs/code-determinism.yaml"
    assert spec["migration_notes"]["legacy_source"].startswith("../ld-vibe-harness/")
