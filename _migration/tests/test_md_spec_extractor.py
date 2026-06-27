from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V2_ROOT = ROOT.parent / "ld-vibe-harness"
sys.path.insert(0, str(ROOT / "_migration" / "code"))
sys.path.insert(0, str(ROOT / "code"))

from action_guide import compile_action_guide  # noqa: E402
from md_spec_extractor import extract_action_source, extract_markdown_spec  # noqa: E402


SPEC_01 = V2_ROOT / "specs" / "01-规范体系基础规范.md"


def test_extracts_v2_spec_identity_directly_from_markdown() -> None:
    extracted = extract_markdown_spec(SPEC_01)

    assert extracted["title"] == "规范体系基础规范"
    assert extracted["identity"]["spec_id"] == "01"
    assert extracted["identity"]["canonical_path"] == "specs/01-规范体系基础规范.md"
    assert "specs/attachments/01.Att.04-规范身份字段表.md" in extracted["path_refs"]
    assert any(section["title"] == "2. 上位依据" for section in extracted["sections"])


def test_markdown_spec_compiles_to_action_guide_without_per_spec_yaml() -> None:
    source = extract_action_source(SPEC_01)

    guide = compile_action_guide(source)

    assert guide["guide_type"] == "action_guide"
    assert guide["result_status"] == "usable"
    assert guide["target"]["id"] == "SPEC-01"
    assert guide["source_refs"][0]["path"] == "specs/01-规范体系基础规范.md"
    assert guide["read_plan"][0]["target"] == "specs/01-规范体系基础规范.md"
    assert any(
        item["target"] == "specs/attachments/01.Att.04-规范身份字段表.md"
        for item in guide["read_plan"]
    )
    assert "allowed" not in guide
    assert "approved" not in guide
