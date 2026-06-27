from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
V2_ROOT = ROOT.parent / "ld-vibe-harness"
sys.path.insert(0, str(ROOT / "_migration" / "code"))
sys.path.insert(0, str(ROOT / "code"))

from action_guide import compile_action_guide  # noqa: E402
from md_spec_extractor import extract_action_source, extract_markdown_spec  # noqa: E402


SPEC_01 = V2_ROOT / "specs" / "01-规范体系基础规范.md"
REPRESENTATIVE_SPECS = [
    ("00", V2_ROOT / "specs" / "00-LDVH理念与价值标准.md", []),
    ("01", SPEC_01, []),
    ("04", V2_ROOT / "specs" / "04-Code确定性执行规范.md", []),
    ("20", V2_ROOT / "specs" / "20-Spark-火花.md", ["v2_fact_model_member"]),
    (
        "31",
        V2_ROOT / "specs" / "31-git-commit-action-Git提交行动编排.md",
        ["v2_action_member", "ldvh_member"],
    ),
]
EXPECTED_LIMITED_SPECS = {
    "32-environment-entry-adaptation-环境入口落地与适配检查.md",
    "34-study-research-output-研究行动产物编排.md",
    "35-workcase-action-carrying-工作项行动承接编排.md",
    "36-record-object-routing-recall-记录对象归口与召回.md",
}


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


@pytest.mark.parametrize(("spec_id", "path", "secondary"), REPRESENTATIVE_SPECS)
def test_representative_specs_extract_identity_and_compile(
    spec_id: str, path: Path, secondary: list[str]
) -> None:
    extracted = extract_markdown_spec(path)
    source = extract_action_source(path)

    assert extracted["identity"]["spec_id"] == spec_id
    assert extracted["identity"]["canonical_path"].startswith("specs/")
    assert extracted["sections"]
    assert source["id"] == f"SPEC-{spec_id}"
    assert source["source_refs"][0]["path"] == extracted["identity"]["canonical_path"]
    assert source["read_plan"][0]["target"] == extracted["identity"]["canonical_path"]
    assert source["md_extract"]["secondary_identities"] == secondary

    guide = compile_action_guide(source)

    assert guide["result_status"] == "usable"
    assert guide["target"]["id"] == f"SPEC-{spec_id}"


def test_member_specs_expose_parent_and_secondary_identity() -> None:
    spark = extract_action_source(V2_ROOT / "specs" / "20-Spark-火花.md")
    commit_action = extract_action_source(
        V2_ROOT / "specs" / "31-git-commit-action-Git提交行动编排.md"
    )

    assert spark["md_extract"]["parent_spec"] == "specs/02-事实模型基础规范.md"
    assert spark["md_extract"]["relation"] == "fact_model_member"
    assert "v2_fact_model_member" in spark["md_extract"]["secondary_identities"]
    assert any(
        relation["target"] == "specs/02-事实模型基础规范.md"
        for relation in spark["relations"]
    )

    assert commit_action["md_extract"]["parent_spec"] == "specs/03-行动编排规范.md"
    assert commit_action["md_extract"]["relation"] == "action_member"
    assert "v2_action_member" in commit_action["md_extract"]["secondary_identities"]
    assert "ldvh_member" in commit_action["md_extract"]["secondary_identities"]
    assert any(
        item["target"] == "specs/07-事实源边界与Git追溯规范.md"
        for item in commit_action["read_plan"]
    )


def test_all_v2_body_specs_extract_and_compile_from_markdown() -> None:
    spec_paths = sorted((V2_ROOT / "specs").glob("*.md"))
    limited: set[str] = set()

    for path in spec_paths:
        source = extract_action_source(path)
        guide = compile_action_guide(source)

        assert source["source_refs"][0]["path"].startswith("specs/")
        assert guide["target"]["id"].startswith("SPEC-")
        assert guide["read_plan"]
        if guide["result_status"] == "limited":
            limited.add(path.name)
        else:
            assert guide["result_status"] == "usable"

    assert len(spec_paths) == 21
    assert limited == EXPECTED_LIMITED_SPECS
