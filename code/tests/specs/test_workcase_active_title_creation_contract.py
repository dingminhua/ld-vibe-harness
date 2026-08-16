from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]


def test_current_sources_define_the_exact_active_workcase_title_guard() -> None:
    foundation = (_ROOT / "specs/05-事实模型基础规范.md").read_text(encoding="utf-8")
    workcase = (_ROOT / "specs/21-WorkCase-工作项.md").read_text(encoding="utf-8")

    for source in (foundation, workcase):
        assert "active_workcase_title_conflict" in source
        assert "existing_refs" in source
        assert "ambiguous" in source
        assert "Unicode normalize" in source
        assert "closed" in source
        assert "fail closed" in source
        assert "实际 Git Working Tree" in source


def test_code_and_helper_preserve_the_source_owned_conflict_reason() -> None:
    application = (_ROOT / "code/ldvh/facts/creation_application.py").read_text(encoding="utf-8")
    helper = (_ROOT / "code/ldvh/helper/operations/fact_creation_operation.py").read_text(encoding="utf-8")

    assert '"active_workcase_title_conflict"' in application
    assert '"active_workcase_title_scan_unavailable"' in application
    assert '"active_workcase_title_conflict"' in helper
    assert '"target-not-attempted"' in helper
