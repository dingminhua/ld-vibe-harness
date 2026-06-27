from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V2_ROOT = ROOT.parent / "ld-vibe-harness"
sys.path.insert(0, str(ROOT / "_migration" / "code"))

from spec_bloat_scan import scan_specs  # noqa: E402


def test_spec_bloat_scan_detects_repeated_skeletons() -> None:
    scan = scan_specs(V2_ROOT / "specs")

    repeated = {item["heading"]: item["file_count"] for item in scan["repeated_h2"]}

    assert scan["body_spec_count"] == 21
    assert repeated["本文解决的问题"] == 21
    assert repeated["Human Gate"] == 21
    assert repeated["规范保障要求"] == 21
    assert repeated["上位依据"] == 20


def test_spec_bloat_scan_detects_member_families() -> None:
    scan = scan_specs(V2_ROOT / "specs")
    families = scan["families"]

    action = families["action_members_30_31_32_34_35_36"]
    fact = families["fact_members_20_24"]

    assert action["file_count"] == 6
    assert action["common_prefix_length"] == 19
    assert "执行流程" in action["common_h2"]
    assert "行动编排成员检查要求" in action["common_h2"]

    assert fact["file_count"] == 5
    assert fact["common_prefix_length"] >= 11
    assert "状态机" in fact["common_h2"]
    assert "字段契约" in fact["common_h2"]


def test_spec_bloat_scan_reports_candidate_categories() -> None:
    scan = scan_specs(V2_ROOT / "specs")
    candidates = {item["candidate"] for item in scan["bloat_candidates"]}

    assert "universal_governance_sections" in candidates
    assert "action_member_template_duplication" in candidates
    assert "fact_member_template_duplication" in candidates
    assert "cross_cutting_boundary_repetition" in candidates
