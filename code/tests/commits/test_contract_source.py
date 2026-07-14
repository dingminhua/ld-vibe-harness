from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ldvh.commits.contract_source import project_commit_contract
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
        authorized_attachments=(),
        supersedes=(),
        markdown=parsed.document,
    )


def test_projects_current_03_tables_and_fingerprint() -> None:
    result = project_commit_contract(_document())

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
    assert result.projection.mechanical_triggers == ("multiple-paths", "breaking-marker", "revert-type")
    assert len(result.projection.content_fingerprint) == 64


def test_rejects_non_active_or_wrong_source() -> None:
    document = _document()

    assert project_commit_contract(replace(document, status="draft")).projection is None
    assert project_commit_contract(replace(document, key="other-source")).projection is None


def test_rejects_duplicate_source_table(tmp_path: Path) -> None:
    original = PROJECT_ROOT / "specs/03-事实源与信息溯源规范.md"
    source = tmp_path / "specs/03-事实源与信息溯源规范.md"
    source.parent.mkdir(parents=True)
    text = original.read_text(encoding="utf-8")
    duplicate = "\n| type | 语义 |\n|---|---|\n| `feat` | duplicate |\n"
    source.write_text(text.replace("\n## 10. 代表性判断场景", duplicate + "\n## 10. 代表性判断场景"), encoding="utf-8")

    result = project_commit_contract(_document(source))

    assert result.projection is None
    assert any("必须唯一存在" in issue.summary for issue in result.issues)


def test_same_headers_outside_section_do_not_change_projection(tmp_path: Path) -> None:
    original = PROJECT_ROOT / "specs/03-事实源与信息溯源规范.md"
    source = tmp_path / "specs/03-事实源与信息溯源规范.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        original.read_text(encoding="utf-8") + "\n| type | 语义 |\n|---|---|\n| `outside` | ignored |\n",
        encoding="utf-8",
    )

    result = project_commit_contract(_document(source))

    assert result.issues == ()
    assert result.projection is not None
    assert "outside" not in result.projection.type_tokens
