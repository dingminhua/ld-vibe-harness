import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "check_03_specs_doc_standard.py"
spec = importlib.util.spec_from_file_location("check_03_specs_doc_standard", MODULE_PATH)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def write_md(path, content):
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def messages(issues):
    return [issue.message for issue in issues]


def test_valid_heading_structure_passes(tmp_path):
    path = write_md(
        tmp_path / "valid.md",
        """
# 文档标题

## 1. 第一章

### 1.1 第一节

#### 1.1.1 第一小节

### 1.2 第二节

## 2. 第二章

### 2.1 第一节
""",
    )

    assert checker.check_file(path) == []


def test_first_level_heading_gap_is_reported(tmp_path):
    path = write_md(
        tmp_path / "gap.md",
        """
# 文档标题

## 1. 第一章

## 3. 第三章
""",
    )

    assert any("期望 §2" in message for message in messages(checker.check_file(path)))


def test_second_level_parent_mismatch_is_reported(tmp_path):
    path = write_md(
        tmp_path / "parent.md",
        """
# 文档标题

## 7. 第七章

### 8.1 错误父级
""",
    )

    result = messages(checker.check_file(path))
    assert any("父级应为 §7" in message for message in result)
    assert any("期望 §7.1" in message for message in result)


def test_second_level_gap_is_reported(tmp_path):
    path = write_md(
        tmp_path / "second-gap.md",
        """
# 文档标题

## 1. 第一章

### 1.1 第一节

### 1.3 第三节
""",
    )

    assert any("期望 §1.2" in message for message in messages(checker.check_file(path)))


def test_third_level_parent_mismatch_is_reported(tmp_path):
    path = write_md(
        tmp_path / "third-parent.md",
        """
# 文档标题

## 7. 第七章

### 7.2 第二节

#### 7.3.1 错误父级
""",
    )

    assert any("父级应为 §7.2" in message for message in messages(checker.check_file(path)))


def test_duplicate_number_is_reported(tmp_path):
    path = write_md(
        tmp_path / "duplicate.md",
        """
# 文档标题

## 1. 第一章

### 1.1 第一节

### 1.1 重复节
""",
    )

    assert any("章节编号重复: §1.1" in message for message in messages(checker.check_file(path)))


def test_heading_level_and_number_depth_mismatch_is_reported(tmp_path):
    path = write_md(
        tmp_path / "mismatch.md",
        """
# 文档标题

## 1.1 错误一级

### 1 错误二级

#### 1.1 错误三级
""",
    )

    result = messages(checker.check_file(path))
    assert sum("标题层级与编号层级不一致" in message for message in result) == 3


def test_chinese_and_roman_heading_numbers_are_reported(tmp_path):
    path = write_md(
        tmp_path / "legacy.md",
        """
# 文档标题

## 七、引用纪律

## VIII. Human Gate
""",
    )

    result = messages(checker.check_file(path))
    assert any("中文大写编号" in message for message in result)
    assert any("罗马数字编号" in message for message in result)


def test_code_blocks_and_ordered_lists_are_ignored(tmp_path):
    path = write_md(
        tmp_path / "ignored.md",
        """
# 文档标题

## 1. 第一章

1. 普通列表
2. 普通列表

```markdown
## 七、示例标题
### 9.3 示例标题
```

~~~markdown
## VIII. 示例标题
~~~

## 2. 第二章
""",
    )

    assert checker.check_file(path) == []


def test_missing_arabic_heading_number_is_reported(tmp_path):
    path = write_md(
        tmp_path / "missing.md",
        """
# 文档标题

## 引用纪律
""",
    )

    assert any("缺少阿拉伯数字编号" in message for message in messages(checker.check_file(path)))


def test_check_paths_reads_markdown_files_recursively(tmp_path):
    write_md(tmp_path / "a.md", "# 标题\n\n## 1. 第一章")
    nested = tmp_path / "nested"
    nested.mkdir()
    write_md(nested / "b.md", "# 标题\n\n## 二、第二章")
    (nested / "ignored.txt").write_text("## 三、忽略", encoding="utf-8")

    issues = checker.check_paths([str(tmp_path)])

    assert len(issues) == 1
    assert issues[0].path.name == "b.md"


def test_main_returns_non_zero_when_issues_exist(tmp_path, capsys):
    path = write_md(tmp_path / "bad.md", "# 标题\n\n## 三、错误")

    exit_code = checker.main([str(path)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "检查失败" in output
    assert "中文大写编号" in output


def test_main_returns_zero_when_no_issues(tmp_path, capsys):
    path = write_md(tmp_path / "ok.md", "# 标题\n\n## 1. 正确")

    exit_code = checker.main([str(path)])

    assert exit_code == 0
    assert "检查通过" in capsys.readouterr().out
