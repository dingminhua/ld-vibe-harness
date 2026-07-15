from pathlib import Path

from ldvh.specs.audit_evidence import inspect_audit_evidence_locators, validate_audit_document
from ldvh.specs.markdown import parse_markdown
from ldvh.specs.repository import inspect_repository


def test_current_registry_declares_the_mechanical_evidence(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    inspection = inspect_audit_evidence_locators(repository.parsed_documents)
    assert inspection.issues == ()
    assert [(item.audit_record_key, item.canonical_path, item.audit_namespace) for item in inspection.locators] == [
        (
            "v4-five-type-closure",
            "docs/v4-architecture/active/V4-五类型全局归并封闭记录.md",
            "five-type-admission-audit",
        )
    ]
    locator = inspection.locators[0]
    document = parse_markdown(
        current_specs_repository / locator.canonical_path,
        locator.canonical_path,
    ).document
    assert validate_audit_document(locator, document) == ()


def test_locator_table_rejects_rule_candidate_path(current_specs_repository: Path) -> None:
    registry = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    text = registry.read_text(encoding="utf-8")
    registry.write_text(
        text.replace(
            "docs/v4-architecture/active/V4-五类型全局归并封闭记录.md",
            "specs/99-Fake.md",
            1,
        ),
        encoding="utf-8",
    )
    repository = inspect_repository(current_specs_repository)
    inspection = inspect_audit_evidence_locators(repository.parsed_documents)
    assert any("非法机械证据 canonical_path" in issue.summary for issue in inspection.issues)
