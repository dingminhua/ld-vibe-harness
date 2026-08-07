from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ldvh.commits.contract_source import ATTACHMENT_KEY, project_commit_contract
from ldvh.specs.identity import FormalDocument
from ldvh.specs.markdown import parse_markdown

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _document(path: Path | None = None) -> FormalDocument:
    source = path or PROJECT_ROOT / "specs/03-事实源与信息溯源规范.md"
    parsed = parse_markdown(source, "specs/03-事实源与信息溯源规范.md")
    assert parsed.issues == ()
    return FormalDocument(
        kind="spec",
        key="source-of-truth-traceability",
        current_id="03",
        title="事实源与信息溯源规范",
        status="active",
        canonical_path="specs/03-事实源与信息溯源规范.md",
        positioning="test",
        scope="test",
        basis=(),
        parent_spec="ldvh-root",
        relation="refines",
        authorized_attachments=(ATTACHMENT_KEY,),
        supersedes=(),
        markdown=parsed.document,
    )


def _attachment(path: Path | None = None) -> FormalDocument:
    source = path or PROJECT_ROOT / "specs/attachments/03.Att.01-来源参考枚举闭集.md"
    parsed = parse_markdown(source, "specs/attachments/03.Att.01-来源参考枚举闭集.md")
    assert parsed.issues == ()
    return FormalDocument(
        kind="attachment",
        key=ATTACHMENT_KEY,
        current_id="03.Att.01",
        title="来源参考枚举闭集",
        status="active",
        canonical_path="specs/attachments/03.Att.01-来源参考枚举闭集.md",
        positioning="test",
        scope="test",
        basis=(),
        parent_spec=None,
        relation=None,
        authorized_attachments=(),
        supersedes=(),
        markdown=parsed.document,
    )


def test_projects_current_03_tables_and_fingerprint() -> None:
    result = project_commit_contract(_document(), _attachment())

    assert result.issues == ()
    assert result.projection is not None
    assert result.projection.type_tokens == (
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "build",
        "ci",
        "chore",
        "revert",
    )
    assert "runtime" in result.projection.scope_tokens
    assert result.projection.mechanical_triggers == ("all-commits-minimum-body", "breaking-marker")
    assert len(result.projection.content_fingerprint) == 64


def test_rejects_non_active_or_wrong_source() -> None:
    document = _document()

    attachment = _attachment()

    assert project_commit_contract(replace(document, status="draft"), attachment).projection is None
    assert project_commit_contract(replace(document, key="other-source"), attachment).projection is None


def test_rejects_duplicate_authorized_attachment_table(tmp_path: Path) -> None:
    original = PROJECT_ROOT / "specs/attachments/03.Att.01-来源参考枚举闭集.md"
    source = tmp_path / "specs/attachments/03.Att.01-来源参考枚举闭集.md"
    source.parent.mkdir(parents=True)
    duplicate = "\n| type | 语义 |\n|---|---|\n| `feat` | duplicate |\n"
    source.write_text(original.read_text(encoding="utf-8") + duplicate, encoding="utf-8")

    result = project_commit_contract(_document(), _attachment(source))

    assert result.projection is None
    assert any("必须唯一存在" in issue.summary for issue in result.issues)


def test_same_headers_outside_03_att01_do_not_change_projection(tmp_path: Path) -> None:
    original = PROJECT_ROOT / "specs/03-事实源与信息溯源规范.md"
    source = tmp_path / "specs/03-事实源与信息溯源规范.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        original.read_text(encoding="utf-8") + "\n| type | 语义 |\n|---|---|\n| `outside` | ignored |\n",
        encoding="utf-8",
    )

    result = project_commit_contract(_document(source), _attachment())

    assert result.issues == ()
    assert result.projection is not None
    assert "outside" not in result.projection.type_tokens


def test_rejects_missing_or_unauthorized_or_mismatched_attachment() -> None:
    document = _document()
    attachment = _attachment()

    assert project_commit_contract(document, None).projection is None
    assert project_commit_contract(replace(document, authorized_attachments=()), attachment).projection is None
    assert project_commit_contract(replace(document, authorized_attachments=()), attachment).issues[0].summary == (
        "03 未授权提交契约附件 source-reference-enumerations"
    )
    assert project_commit_contract(document, replace(attachment, current_id="03.Att.99")).projection is None


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("| `all-commits-minimum-body` | `true`", "| `unknown-minimum-body` | `true`"),
        ("| `project-required` | `false`", "| `high-impact` | `false`"),
        ("| `project-required` | `false`", "| `project-required` | `maybe`"),
    ],
)
def test_rejects_unknown_duplicate_or_invalid_trigger_rows(tmp_path: Path, old: str, new: str) -> None:
    original = PROJECT_ROOT / "specs/attachments/03.Att.01-来源参考枚举闭集.md"
    source = tmp_path / "specs/attachments/03.Att.01-来源参考枚举闭集.md"
    source.parent.mkdir(parents=True)
    source.write_text(original.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    result = project_commit_contract(_document(), _attachment(source))

    assert result.projection is None
    assert any("trigger" in issue.summary for issue in result.issues)


def test_rejects_out_of_order_trigger_rows(tmp_path: Path) -> None:
    original = PROJECT_ROOT / "specs/attachments/03.Att.01-来源参考枚举闭集.md"
    source = tmp_path / "specs/attachments/03.Att.01-来源参考枚举闭集.md"
    source.parent.mkdir(parents=True)
    text = original.read_text(encoding="utf-8")
    minimum = next(line for line in text.splitlines() if line.startswith("| `all-commits-minimum-body`"))
    breaking = next(line for line in text.splitlines() if line.startswith("| `breaking-marker`"))
    source.write_text(text.replace(minimum + "\n" + breaking, breaking + "\n" + minimum), encoding="utf-8")

    result = project_commit_contract(_document(), _attachment(source))

    assert result.projection is None
    assert any("固定顺序" in issue.summary for issue in result.issues)
