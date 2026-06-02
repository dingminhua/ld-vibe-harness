import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "check_03_specs_references.py"
spec = importlib.util.spec_from_file_location("check_03_specs_references", MODULE_PATH)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def write_md(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def messages(issues):
    return [issue.message for issue in issues]


def codes(issues):
    return [issue.code for issue in issues]


def test_internal_section_reference_passes(tmp_path):
    path = write_md(
        tmp_path / "01-Test.md",
        """
# 测试文档

## 1. 第一章

依据本文 §1。
""",
    )

    assert checker.check_paths([path]) == []


def test_missing_internal_section_is_reported(tmp_path):
    path = write_md(
        tmp_path / "01-Test.md",
        """
# 测试文档

## 1. 第一章

依据本文 §2。
""",
    )

    result = checker.check_paths([path])

    assert "MISSING_INTERNAL_SECTION" in codes(result)
    assert any("§2" in message for message in messages(result))


def test_explicit_specs_path_reference_passes(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    target = write_md(specs_dir / "03-Specs文档规范.md", "# 规范\n\n## 7. 引用纪律")
    source = write_md(
        specs_dir / "11.01-Rules机制规范.md",
        """
# Rules

## 1. 第一章

依据 `specs/03-Specs文档规范.md` §7。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    assert checker.check_paths([source, target]) == []


def test_missing_explicit_specs_path_section_is_reported(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    target = write_md(specs_dir / "03-Specs文档规范.md", "# 规范\n\n## 7. 引用纪律")
    source = write_md(
        specs_dir / "11.01-Rules机制规范.md",
        """
# Rules

## 1. 第一章

依据 `specs/03-Specs文档规范.md` §8。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    result = checker.check_paths([source, target])

    assert "MISSING_EXTERNAL_SECTION" in codes(result)
    assert any("03-Specs文档规范.md §8" in message for message in messages(result))


def test_missing_explicit_file_is_reported(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    source = write_md(
        specs_dir / "11.01-Rules机制规范.md",
        """
# Rules

## 1. 第一章

依据 `specs/not-found.md` §1。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    result = checker.check_paths([source])

    assert "FILE_NOT_FOUND" in codes(result)
    assert any("引用文件不存在" in message for message in messages(result))


def test_shorthand_reference_passes(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    target = write_md(specs_dir / "13-LDVH事实模型基础规范.md", "# 规范\n\n## 4. 状态机")
    source = write_md(
        specs_dir / "21-ADR-决策记录.md",
        """
# ADR

## 1. 第一章

依据 13 §4。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    assert checker.check_paths([source, target]) == []


def test_subdocument_can_reference_parent_sections(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    parent = write_md(specs_dir / "51-multi-role-thinking-多角色思考.md", "# 主文档\n\n## 8. 执行流程\n\n### 8.6 汇总对比")
    source = write_md(
        specs_dir / "51.03-Agent.md",
        """
# Agent 子文档

## 1. 第一章

主控按 51 主文档 §8.6 汇总对比。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    assert checker.check_paths([source, parent]) == []


def test_shorthand_subdocument_reference_passes(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    target = write_md(specs_dir / "21.06-Contract.md", "# Contract\n\n## 3. 字段契约")
    source = write_md(
        specs_dir / "21-ADR-决策记录.md",
        """
# ADR

## 1. 第一章

依据 21.06 §3。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    assert checker.check_paths([source, target]) == []


def test_missing_shorthand_section_is_reported(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    target = write_md(specs_dir / "13-LDVH事实模型基础规范.md", "# 规范\n\n## 4. 状态机")
    source = write_md(
        specs_dir / "21-ADR-决策记录.md",
        """
# ADR

## 1. 第一章

依据 13 §5。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    result = checker.check_paths([source, target])

    assert "MISSING_SHORTHAND_SECTION" in codes(result)
    assert any("13-LDVH事实模型基础规范.md §5" in message for message in messages(result))


def test_unresolved_shorthand_is_reported(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    source = write_md(
        specs_dir / "21-ADR-决策记录.md",
        """
# ADR

## 1. 第一章

依据 99 §1。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    result = checker.check_paths([source])

    assert "SHORTHAND_UNRESOLVED" in codes(result)
    assert any("99 §1" in message for message in messages(result))


def test_chinese_section_reference_is_reported(tmp_path):
    path = write_md(
        tmp_path / "01-Test.md",
        """
# 测试文档

## 1. 第一章

依据本文 §七。
""",
    )

    result = checker.check_paths([path])

    assert "CHINESE_SECTION_REF" in codes(result)
    assert any("阿拉伯数字" in message for message in messages(result))


def test_code_blocks_are_ignored(tmp_path):
    path = write_md(
        tmp_path / "01-Test.md",
        """
# 测试文档

## 1. 第一章

```markdown
依据本文 §七。
依据本文 §99。
```
""",
    )

    assert checker.check_paths([path]) == []


def test_check_paths_reads_markdown_files_recursively(tmp_path):
    write_md(tmp_path / "a.md", "# A\n\n## 1. 第一章\n\n依据本文 §1。")
    nested = tmp_path / "nested"
    write_md(nested / "b.md", "# B\n\n## 1. 第一章\n\n依据本文 §2。")
    (nested / "ignored.txt").write_text("依据本文 §9。", encoding="utf-8")

    result = checker.check_paths([tmp_path])

    assert len(result) == 1
    assert result[0].path.name == "b.md"
    assert result[0].code == "MISSING_INTERNAL_SECTION"


def test_explicit_specs_path_reference_resolves_unchecked_existing_file(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    target = write_md(specs_dir / "02-LDVH术语规范.md", "# 术语\n\n## 7. 管辖项目")
    source = write_md(
        specs_dir / "01-LDVH目录说明.md",
        """
# 目录

## 1. 第一章

依据 `specs/02-LDVH术语规范.md` §7。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    assert checker.check_paths([source]) == []
    assert target.exists()

