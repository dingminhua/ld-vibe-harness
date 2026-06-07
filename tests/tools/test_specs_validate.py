import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "specs_validate.py"
spec = importlib.util.spec_from_file_location("specs_validate", MODULE_PATH)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def write_md(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


# ══════════════════════════════════════════════════════════════════════
# doc — 文档编号/标题规范检查
# ══════════════════════════════════════════════════════════════════════


def doc_messages(issues):
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

    assert checker.doc_check_file(path) == []


def test_first_level_heading_gap_is_reported(tmp_path):
    path = write_md(
        tmp_path / "gap.md",
        """
# 文档标题

## 1. 第一章

## 3. 第三章
""",
    )

    assert any("期望 §2" in message for message in doc_messages(checker.doc_check_file(path)))


def test_second_level_parent_mismatch_is_reported(tmp_path):
    path = write_md(
        tmp_path / "parent.md",
        """
# 文档标题

## 7. 第七章

### 8.1 错误父级
""",
    )

    result = doc_messages(checker.doc_check_file(path))
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

    assert any("期望 §1.2" in message for message in doc_messages(checker.doc_check_file(path)))


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

    assert any("父级应为 §7.2" in message for message in doc_messages(checker.doc_check_file(path)))


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

    assert any("章节编号重复: §1.1" in message for message in doc_messages(checker.doc_check_file(path)))


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

    result = doc_messages(checker.doc_check_file(path))
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

    result = doc_messages(checker.doc_check_file(path))
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

    assert checker.doc_check_file(path) == []


def test_missing_arabic_heading_number_is_reported(tmp_path):
    path = write_md(
        tmp_path / "missing.md",
        """
# 文档标题

## 引用纪律
""",
    )

    assert any("缺少阿拉伯数字编号" in message for message in doc_messages(checker.doc_check_file(path)))


def test_chapter_index_heading_without_number_is_allowed(tmp_path):
    path = write_md(
        tmp_path / "index.md",
        """
# 文档标题

## 章节索引

## 1. 第一章
""",
    )

    assert checker.doc_check_file(path) == []


def test_heading_deeper_than_four_levels_is_reported(tmp_path):
    path = write_md(
        tmp_path / "deep.md",
        """
# 文档标题

## 1. 第一章

### 1.1 第一节

#### 1.1.1 第一小节

##### 1.1.1.1 过深标题
""",
    )

    assert any("不支持超过四级" in message for message in doc_messages(checker.doc_check_file(path)))


def test_doc_check_paths_reads_markdown_files_recursively(tmp_path):
    write_md(tmp_path / "a.md", "# 标题\n\n## 1. 第一章")
    nested = tmp_path / "nested"
    nested.mkdir()
    write_md(nested / "b.md", "# 标题\n\n## 二、第二章")
    (nested / "ignored.txt").write_text("## 三、忽略", encoding="utf-8")

    issues = checker.doc_check_paths([str(tmp_path)])

    assert len(issues) == 1
    assert issues[0].path.name == "b.md"


def test_doc_main_returns_non_zero_when_issues_exist(tmp_path, capsys):
    path = write_md(tmp_path / "bad.md", "# 标题\n\n## 三、错误")

    exit_code = checker.main(["doc", str(path)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "检查失败" in output
    assert "中文大写编号" in output


def test_doc_main_returns_zero_when_no_issues(tmp_path, capsys):
    path = write_md(tmp_path / "ok.md", "# 标题\n\n## 1. 正确")

    exit_code = checker.main(["doc", str(path)])

    assert exit_code == 0
    assert "检查通过" in capsys.readouterr().out


# ══════════════════════════════════════════════════════════════════════
# refs — 引用完整性检查
# ══════════════════════════════════════════════════════════════════════


def refs_messages(issues):
    return [issue.message for issue in issues]


def refs_codes(issues):
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

    assert checker.refs_check_paths([path]) == []


def test_missing_internal_section_is_reported(tmp_path):
    path = write_md(
        tmp_path / "01-Test.md",
        """
# 测试文档

## 1. 第一章

依据本文 §2。
""",
    )

    result = checker.refs_check_paths([path])

    assert "MISSING_INTERNAL_SECTION" in refs_codes(result)
    assert any("§2" in message for message in refs_messages(result))


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

    assert checker.refs_check_paths([source, target]) == []


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

    result = checker.refs_check_paths([source, target])

    assert "MISSING_EXTERNAL_SECTION" in refs_codes(result)
    assert any("03-Specs文档规范.md §8" in message for message in refs_messages(result))


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

    result = checker.refs_check_paths([source])

    assert "FILE_NOT_FOUND" in refs_codes(result)
    assert any("引用文件不存在" in message for message in refs_messages(result))


def test_shorthand_reference_passes(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    target = write_md(specs_dir / "13-LDVH事实模型基础规范.md", "# 规范\n\n## 4. 状态机")
    source = write_md(
        specs_dir / "21-ADR-决策.md",
        """
# ADR

## 1. 第一章

依据 13 §4。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    assert checker.refs_check_paths([source, target]) == []


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

    assert checker.refs_check_paths([source, parent]) == []


def test_shorthand_main_document_reference_passes(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    target = write_md(specs_dir / "21-ADR-决策.md", "# ADR\n\n## 3. 字段契约")
    source = write_md(
        specs_dir / "20-工作模型集合索引.md",
        """
# 工作模型集合索引

## 1. 第一章

依据 21 §3。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    assert checker.refs_check_paths([source, target]) == []


def test_missing_shorthand_section_is_reported(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    target = write_md(specs_dir / "13-LDVH事实模型基础规范.md", "# 规范\n\n## 4. 状态机")
    source = write_md(
        specs_dir / "21-ADR-决策.md",
        """
# ADR

## 1. 第一章

依据 13 §5。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    result = checker.refs_check_paths([source, target])

    assert "MISSING_SHORTHAND_SECTION" in refs_codes(result)
    assert any("13-LDVH事实模型基础规范.md §5" in message for message in refs_messages(result))


def test_unresolved_shorthand_is_reported(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    source = write_md(
        specs_dir / "21-ADR-决策.md",
        """
# ADR

## 1. 第一章

依据 99 §1。
""",
    )
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", specs_dir)

    result = checker.refs_check_paths([source])

    assert "SHORTHAND_UNRESOLVED" in refs_codes(result)
    assert any("99 §1" in message for message in refs_messages(result))


def test_chinese_section_reference_is_reported(tmp_path):
    path = write_md(
        tmp_path / "01-Test.md",
        """
# 测试文档

## 1. 第一章

依据本文 §七。
""",
    )

    result = checker.refs_check_paths([path])

    assert "CHINESE_SECTION_REF" in refs_codes(result)
    assert any("阿拉伯数字" in message for message in refs_messages(result))


def test_refs_code_blocks_are_ignored(tmp_path):
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

    assert checker.refs_check_paths([path]) == []


def test_refs_check_paths_reads_markdown_files_recursively(tmp_path):
    write_md(tmp_path / "a.md", "# A\n\n## 1. 第一章\n\n依据本文 §1。")
    nested = tmp_path / "nested"
    write_md(nested / "b.md", "# B\n\n## 1. 第一章\n\n依据本文 §2。")
    (nested / "ignored.txt").write_text("依据本文 §9。", encoding="utf-8")

    result = checker.refs_check_paths([tmp_path])

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

    assert checker.refs_check_paths([source]) == []
    assert target.exists()


# ══════════════════════════════════════════════════════════════════════
# index — 生成索引
# ══════════════════════════════════════════════════════════════════════


def build_fixture(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-Specs文档规范.md",
        """
# Specs 文档规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：specs 文档
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/10-事实源边界与承载规范.md`

---

## 章节索引

| 章节 | 主题 |
|---|---|
| 1 | 本文解决的问题 |
| 2 | 机制关系声明 |

---

## 1. 本文解决的问题

依据 `specs/10-事实源边界与承载规范.md` §6。

### 1.1 子章节

内容。

## 2. 机制关系声明

| 关联机制 | 关联实体 | 关系类型 | 同步触发 |
|---|---|---|---|
| Rules | `.trae/rules/ldvh-l2-specs-rules.md` | specs 入口 | 文档骨架变化时 |
""",
    )
    write_md(
        specs / "10-事实源边界与承载规范.md",
        """
# 事实源边界与承载规范

> 创建日期：2026-06-01
> 定位：事实源边界
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

## 章节索引

| 章节 | 主题 |
|---|---|
| 6 | 事实源读取策略 |

## 6. 事实源读取策略

内容。
""",
    )
    write_md(
        specs / "evals" / "01-评估.md",
        """
# 评估

> 创建日期：2026-06-01
> 定位：评估
> 调研边界：内部评估
> 执行效力：无
> 编号归属：evals

## 1. 结论
""",
    )
    write_md(
        specs / "refs" / "01-外部资料.md",
        """
# 外部资料

> 创建日期：2026-06-01
> 来源：外部
> 定位：参考

## 1. 摘要
""",
    )
    return tmp_path


def test_build_generates_docs_sections_relations_and_mechanisms(tmp_path):
    root = build_fixture(tmp_path)
    indexes = checker.SpecsChecker(root).build()

    assert indexes["metadata"]["derived"] is True
    assert indexes["metadata"]["source_of_truth"] is False
    assert {doc["path"] for doc in indexes["docs"]} == {
        "specs/03-Specs文档规范.md",
        "specs/10-事实源边界与承载规范.md",
    }
    assert indexes["metadata"]["input_patterns"] == ["*.md"]

    doc = next(item for item in indexes["docs"] if item["path"] == "specs/03-Specs文档规范.md")
    assert doc["title"] == "Specs 文档规范"
    assert doc["doc_number"] == "03"
    assert doc["doc_kind"] == "formal_spec"
    assert doc["basis"] == ["specs/00-LD-Vibe-Harness理念与纲要.md"]
    assert doc["related_specs"] == ["specs/10-事实源边界与承载规范.md"]
    assert doc["content_hash"].startswith("sha256:")

    section = next(
        item
        for item in indexes["sections"]
        if item["path"] == "specs/03-Specs文档规范.md" and item["section_number"] == "1"
    )
    assert section["line_start"] < section["line_end"]
    assert section["title"] == "本文解决的问题"

    child = next(item for item in indexes["sections"] if item["section_number"] == "1.1")
    assert child["parent_section"] == "1"

    assert any(
        item["relation_kind"] == "path_ref" and item["target_ref"] == "specs/10-事实源边界与承载规范.md"
        for item in indexes["relations"]
    )
    assert any(item["relation_kind"] == "section_ref" and item["target_section"] == "6" for item in indexes["relations"])

    mechanism = indexes["mechanisms"][0]
    assert mechanism["mechanism"] == "Rules"
    assert mechanism["entity"] == ".trae/rules/ldvh-l2-specs-rules.md"


def test_document_kind_and_required_header_diagnostics(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "11.01-Rules.md",
        """
# Rules 子文档

> 创建日期：2026-06-01
> 所属主文档：`specs/11-LDVH-AI协作规范.md`
> 关系：父规范扩展
> 上位依据：`specs/11-LDVH-AI协作规范.md`

## 1. 定位
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    doc = indexes["docs"][0]
    assert doc["doc_kind"] == "subdocument"
    assert any(item["code"] == "MISSING_HEADER_FIELD" and "适用范围" in item["message"] for item in indexes["diagnostics"])


def test_broken_markdown_path_is_reported(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "01-Test.md",
        """
# Test

> 创建日期：2026-06-01
> 定位：测试
> 适用范围：测试
> 上位依据：`specs/not-found.md`

## 1. 第一章

依据 `specs/missing.md`。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    messages = [item["message"] for item in indexes["diagnostics"]]
    assert any("specs/not-found.md" in message for message in messages)
    assert any("specs/missing.md" in message for message in messages)


def test_write_outputs_creates_expected_json_files(tmp_path):
    root = build_fixture(tmp_path)
    indexes = checker.SpecsChecker(root).build()
    out_dir = tmp_path / "out"

    written = checker.write_outputs(indexes, out_dir)

    assert written == [
        "specs-diagnostics.json",
        "specs-docs-index.json",
        "specs-mechanism-index.json",
        "specs-relations-index.json",
        "specs-sections-index.json",
    ]
    payload = json.loads((out_dir / "specs-docs-index.json").read_text(encoding="utf-8"))
    assert payload["metadata"]["derived"] is True
    assert len(payload["docs"]) == 2


def test_index_main_outputs_json_to_stdout(tmp_path, capsys):
    root = build_fixture(tmp_path)

    exit_code = checker.main(["index", "--root", str(root)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["metadata"]["tool"] == "tools/specs_validate.py"
    assert payload["docs"]


# ══════════════════════════════════════════════════════════════════════
# env-init — 根目录 LDVH 环境初始化记录检查
# ══════════════════════════════════════════════════════════════════════


def write_env_init(root, extra_status_rows="", heading_override=None):
    title = heading_override or "LDVH 环境初始化记录"
    return write_md(
        root / "LDVH-ENVIRONMENT-INITIALIZATION.md",
        f"""
# {title}

## 1. 这个文件是什么

说明。

## 2. 适配状态与持续提醒

| 检查项 | 当前记录 |
|---|---|
| 记录适用项目 | 示例项目 |
| 记录适用环境 | Codex |
| 用户当前项目 | 示例项目 |
| 用户当前开发平台 | Codex |
| 适配状态 | 已适配当前项目与当前环境 |
| 最近 Human 确认 | 2026-06-08 |
{extra_status_rows}

## 3. 初始化摘要

内容。

## 4. 能力核验来源

内容。

## 5. 环境适配映射

内容。

## 6. 当前运行投影状态

内容。

## 7. 初始化动作

内容。

## 8. 更新规则

内容。

## 9. Human Gate 与检查

内容。

## 10. 未决限制与后续事项

内容。
""",
    )


def env_init_codes(issues):
    return [issue.code for issue in issues]


def test_env_init_valid_root_record_passes(tmp_path):
    write_env_init(tmp_path)

    assert checker.env_init_check_root(tmp_path) == []


def test_env_init_missing_root_record_is_reported(tmp_path):
    issues = checker.env_init_check_root(tmp_path)

    assert env_init_codes(issues) == ["ENV_INIT_MISSING"]
    assert "先按 04.03 模板创建并完成当前项目与当前开发平台适配" in issues[0].message


def test_env_init_missing_status_field_is_reported(tmp_path):
    write_md(
        tmp_path / "LDVH-ENVIRONMENT-INITIALIZATION.md",
        """
# LDVH 环境初始化记录

## 1. 这个文件是什么

## 2. 适配状态与持续提醒

| 检查项 | 当前记录 |
|---|---|
| 记录适用项目 | 示例项目 |
| 记录适用环境 | Codex |

## 3. 初始化摘要

## 4. 能力核验来源

## 5. 环境适配映射

## 6. 当前运行投影状态

## 7. 初始化动作

## 8. 更新规则

## 9. Human Gate 与检查

## 10. 未决限制与后续事项
""",
    )

    issues = checker.env_init_check_root(tmp_path)

    assert "ENV_INIT_STATUS_FIELD_MISSING" in env_init_codes(issues)
    assert any("用户当前开发平台" in issue.message for issue in issues)


def test_env_init_legacy_english_heading_is_reported(tmp_path):
    write_env_init(tmp_path)
    path = tmp_path / "LDVH-ENVIRONMENT-INITIALIZATION.md"
    text = path.read_text(encoding="utf-8").replace("## 1. 这个文件是什么", "## 1. What This File Is")
    path.write_text(text, encoding="utf-8")

    issues = checker.env_init_check_root(tmp_path)

    assert "ENV_INIT_LEGACY_HEADING" in env_init_codes(issues)
    assert "ENV_INIT_SECTION_MISSING" in env_init_codes(issues)
