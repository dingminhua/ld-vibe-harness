import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "specs_validate.py"
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
        specs / "research" / "01-评估.md",
        """
# 评估

> 创建日期：2026-06-01
> 定位：评估
> 调研边界：内部评估
> 执行效力：无
> 编号归属：research

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


def test_root_readme_path_is_resolved(tmp_path):
    specs = tmp_path / "specs"
    write_md(tmp_path / "README.md", "# README")
    write_md(
        specs / "04-Test.md",
        """
# Test

> 创建日期：2026-06-01
> 定位：测试
> 适用范围：测试
> 上位依据：`specs/00-Test.md`

## 1. 第一章

检查根目录 `README.md`。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    assert not any(
        item["code"] == "BROKEN_MARKDOWN_PATH" and "README.md" in item["message"]
        for item in indexes["diagnostics"]
    )


def test_00_document_does_not_require_parent_basis(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "00-总纲.md",
        """
# 总纲

> 创建日期：2026-06-01
> 定位：测试总纲
> 适用范围：测试

## 1. 第一章
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    assert not any(
        item["code"] == "MISSING_HEADER_FIELD" and "上位依据" in item["message"]
        for item in indexes["diagnostics"]
    )


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
# landing-report — 规范落地要求聚合报告
# ══════════════════════════════════════════════════════════════════════

def build_landing_report_fixture(tmp_path, monkeypatch):
    docs_specs = tmp_path / "docs" / "specs"
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(checker, "DOCS_SPECS_DIR", docs_specs)
    monkeypatch.setattr(checker, "RUNTIME_PROJECTION_DEFAULT_PATHS", ["LDVH-AI-ENTRY.md"])

    write_md(
        tmp_path / "LDVH-AI-ENTRY.md",
        """
# Runtime Projection

规范来源：`docs/specs/00-Test.md`
""",
    )
    write_md(
        docs_specs / "00-Test.md",
        """
# Landing Report Test

## 章节索引

| 章节 | 主题 |
|---|---|
| 1 | 规范落地要求 |

## 1. 规范落地要求

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 后续正式规范不得违背本文的价值实现标准 | 规范检查 | 文档治理 | 审计时 |
| 确定性执行要求 | 后续 Code 应能生成 landing report | `tools/specs_validate.py` 扩展、正反样例 | 校验实现 | 规范落地要求变化时 |
| Human 交互要求 | 高影响变更应触发 Human Gate | Human Gate、确认记录 | 工作流程治理 | 变更前 |
| Human 交互要求 | 新增管辖项目条目时，应评估 Human Gate | Human Gate、影响范围说明 | 工作流程治理 | 管辖项目清单变化时 |
| Human 交互要求 | candidate 流程正式创建前，应先讨论是否独立成流程 | Human Gate、流程讨论 | 工作流程治理 | 从候选项创建流程前 |
| Human 交互要求 | Human Gate UI 应清楚展示确认对象和影响范围 | Human Gate UI、承接 06 §6.3.1 | 工作流程治理 | Human Gate UI 变化时 |
| 生命周期触发要求 | 运行投影不可用时应记录降级说明 | 人工降级检查 | 触发保障 | 工具不可用时 |
| 生命周期触发要求 | 平台能力变化后应检查平台清单是否同步 | 平台清单、人工降级检查 | 触发保障 | 平台能力变化时 |
| 生命周期触发要求 | 第三方 Skill 入口变化后应检查包装 Skill 和运行投影是否同步 | 包装 Skill、运行投影漂移检查、降级方式 | 触发保障 | 第三方 Skill 使用入口变化时 |
| 生命周期触发要求 | 41 触发保障应被 42 消费，并覆盖运行投影漂移检查和 Human Gate 证据消费 | 41 分层触发保障、42 消费检查、运行投影漂移检查、Human Gate 证据消费 | 触发保障 | 正式规范、运行投影或 Human Gate 证据变化时 |
""",
    )
    write_md(
        tmp_path / "docs" / "research" / "18-评估.md",
        """
# 评估

## 1. 规范落地要求

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 确定性执行要求 | 不应进入正式报告 | Code | 校验实现 | 任意 |
""",
    )
    return docs_specs


def test_landing_report_builds_statuses_and_summary(tmp_path, monkeypatch):
    docs_specs = build_landing_report_fixture(tmp_path, monkeypatch)

    report = checker.landing_report_build([str(docs_specs)])

    assert report["metadata"]["source_of_truth"] is False
    assert report["metadata"]["checked_file_count"] == 1
    assert report["metadata"]["source_count"] == 1
    assert report["metadata"]["requirement_count"] == 10
    assert report["metadata"]["runtime_projection_checked_file_count"] == 1
    assert report["metadata"]["runtime_projection_issue_count"] == 0
    assert report["metadata"]["human_gate_checked_file_count"] >= 2
    assert report["metadata"]["human_gate_record_count"] == 0
    assert report["metadata"]["human_gate_issue_count"] == 0
    assert report["summary"]["runtime_projection_status"] == "closed"
    assert report["summary"]["human_gate_status"] == "degraded"
    assert report["summary"]["by_status"] == {
        "closed": 1,
        "degraded": 3,
        "needs_human_gate": 4,
        "open": 2,
    }
    assert report["summary"]["by_capability_status"] == {
        "degraded": 4,
    }
    assert report["summary"]["gap_total"] == sum(
        category["total"] for category in report["gap_categories"].values()
    )
    assert report["summary"]["gap_by_owner_area"] == {
        area: category["total"] for area, category in report["gap_categories"].items()
    }
    assert report["gap_categories"]
    assert all("examples" in category for category in report["gap_categories"].values())
    assert report["gap_categories"]["human_gate"]["subcategories"]
    assert report["gap_categories"]["human_gate"]["subcategories"]["decision_record_required"]["decision_flows"]
    assert report["runtime_projection"]["summary"]["status"] == report["summary"]["runtime_projection_status"]
    assert report["summary"]["by_owner_area"]["code"] == 1
    assert [item["id"] for item in report["capability_gaps"]] == [
        "41_trigger_safeguard",
        "42_consumes_41",
        "runtime_projection_drift_check",
        "human_gate_evidence_consumption",
    ]

    statuses = {item["content"]: item["status"] for item in report["requirements"]}
    assert statuses["后续正式规范不得违背本文的价值实现标准"] == "closed"
    assert statuses["后续 Code 应能生成 landing report"] == "open"
    assert statuses["高影响变更应触发 Human Gate"] == "needs_human_gate"
    assert statuses["运行投影不可用时应记录降级说明"] == "degraded"
    assert statuses["41 触发保障应被 42 消费，并覆盖运行投影漂移检查和 Human Gate 证据消费"] == "needs_human_gate"
    assert next(item for item in report["requirements"] if item["owner_area"] == "code")["suggested_writeback"] == "code_request_or_test"


def test_landing_report_cli_outputs_json(tmp_path, monkeypatch, capsys):
    docs_specs = build_landing_report_fixture(tmp_path, monkeypatch)

    exit_code = checker.main(["landing-report", str(docs_specs), "--format", "json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["metadata"]["report"] == "landing-report"
    assert payload["metadata"]["runtime_projection_checked_file_count"] == 1
    assert payload["metadata"]["human_gate_record_count"] == 0
    assert payload["summary"]["human_gate_status"] == "degraded"
    assert payload["summary"]["by_status"]["open"] == 2
    assert payload["summary"]["by_status"]["needs_human_gate"] == 4
    assert payload["summary"]["gap_total"] == 13
    assert payload["summary"]["gap_by_owner_area"]["human_gate"] == 5
    assert payload["gap_categories"]["code"]["requirement_count"] == 1
    assert payload["gap_categories"]["runtime_projection"]["capability_gap_count"] == 1
    assert payload["gap_categories"]["runtime_projection"]["subcategories"]["lifecycle_trigger_sync"]["total"] == 2
    assert payload["gap_categories"]["runtime_projection"]["subcategories"]["platform_capability_sync"]["total"] == 1
    assert payload["gap_categories"]["runtime_projection"]["subcategories"]["third_party_skill_projection"]["total"] == 1
    assert payload["gap_categories"]["runtime_projection"]["subcategories"]["projection_coverage_diagnostic"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["decision_record_required"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["diagnostic_coverage"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["decision_record_required"]["decision_flows"]["future_trigger_record"]["total"] == 1
    assert "current_record_required" not in payload["gap_categories"]["human_gate"]["subcategories"]["decision_record_required"]["decision_flows"]
    assert payload["gap_categories"]["human_gate"]["subcategories"]["policy_clarification"]["total"] == 2
    assert payload["gap_categories"]["human_gate"]["subcategories"]["policy_clarification"]["policy_flows"]["future_evaluation"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["policy_clarification"]["policy_flows"]["workflow_design_discussion"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["implementation_support"]["support_flows"]["web_human_facing_support"]["total"] == 1
    assert payload["gap_categories"]["human_gate"]["subcategories"]["diagnostic_coverage"]["diagnostic_flows"]["coverage_degraded"]["total"] == 1
    assert payload["requirements"][0]["source"] == "docs/specs/00-Test.md"
    assert payload["capability_gaps"][0]["capability"] == "41 触发保障"


def test_landing_report_cli_outputs_text(tmp_path, monkeypatch, capsys):
    docs_specs = build_landing_report_fixture(tmp_path, monkeypatch)

    exit_code = checker.main(["landing-report", str(docs_specs)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "规范落地要求聚合报告" in output
    assert "需关注项:" in output
    assert "能力缺口:" in output
    assert "缺口分类:" in output
    assert "Code / Test (code):" in output
    assert "运行投影 (runtime_projection):" in output
    assert "生命周期触发同步 (lifecycle_trigger_sync):" in output
    assert "平台能力承接同步 (platform_capability_sync):" in output
    assert "第三方 Skill 投影 (third_party_skill_projection):" in output
    assert "投影覆盖诊断降级 (projection_coverage_diagnostic):" in output
    assert "Human Gate (human_gate):" in output
    assert "必须人类决策记录 (decision_record_required):" in output
    assert "未来触发时记录 (future_trigger_record):" in output
    assert "规范口径说明 (policy_clarification):" in output
    assert "未来触发时评估 (future_evaluation):" in output
    assert "流程创建前讨论 (workflow_design_discussion):" in output
    assert "承接实现支持 (implementation_support):" in output
    assert "Web / Human-facing 承接 (web_human_facing_support):" in output
    assert "Code 降级提示/覆盖 (diagnostic_coverage):" in output
    assert "覆盖范围降级 (coverage_degraded):" in output
    assert "后续 Code 应能生成 landing report" in output
    assert "运行投影检查文件数: 1" in output
    assert "Human Gate 记录数: 0" in output
    assert "Human Gate 问题状态" in output
    assert "运行投影漂移检查" in output
    assert "runtime-projection checked 1 project-local files" in output
    assert "human-gate checked" in output
    assert "suggested_writeback: code_request_or_test" in output


def test_landing_plan_build(tmp_path, monkeypatch):
    docs_specs = build_landing_report_fixture(tmp_path, monkeypatch)
    plan = checker.landing_plan_build(str(tmp_path))
    assert plan["metadata"]["report"] == "landing-plan"
    assert plan["metadata"]["read_only"] is True
    assert plan["scope"]["landing_report_requirements"] >= 1
    assert plan["requirements"]["gap_total"] >= 1
    assert "gaps" in plan
    assert "proposed_actions" in plan
    assert "writes_required" in plan
    assert "human_gate" in plan
    assert "validation_plan" in plan
    assert "writeback_targets" in plan
    assert "capabilities" in plan
    assert len(plan["capabilities"]) >= 1


def test_landing_plan_text_output(tmp_path, monkeypatch):
    docs_specs = build_landing_report_fixture(tmp_path, monkeypatch)
    plan = checker.landing_plan_build(str(tmp_path))
    text = checker.landing_plan_format_text(plan)
    assert "Landing Plan (只读)" in text
    assert "能力状态" in text
    assert "建议行动" in text
    assert "写入需求" in text
    assert "Human Gate" in text
    assert "验证计划" in text
    assert "回写目标" in text


def test_runtime_projection_remediation_classification(tmp_path, monkeypatch):
    docs_specs = build_landing_report_fixture(tmp_path, monkeypatch)
    plan = checker.landing_plan_build(str(tmp_path))
    rp_action = None
    for action in plan["proposed_actions"]:
        if action["owner_area"] == "runtime_projection":
            rp_action = action
            break
    assert rp_action is not None
    assert "remediation" in rp_action
    remediation = rp_action["remediation"]
    assert "doc_crossref_check" in remediation
    assert remediation["doc_crossref_check"]["total"] >= 1
    assert remediation["doc_crossref_check"]["label"] == "文档交叉引用检查"
    total_remediation = sum(r["total"] for r in remediation.values())
    assert total_remediation == rp_action["gap_count"]


def test_classify_runtime_projection_remediation():
    assert checker._classify_runtime_projection_remediation(
        {"content": "正式规范变化后应检查本文是否需要同步", "title": "", "id": ""}
    ) == "doc_crossref_check"
    assert checker._classify_runtime_projection_remediation(
        {"content": "入口变化后应检查配置同步", "title": "", "id": ""}
    ) == "entry_sync_check"
    assert checker._classify_runtime_projection_remediation(
        {"content": "", "title": "", "id": "runtime_projection_drift_check"}
    ) == "drift_diagnostic"
    assert checker._classify_runtime_projection_remediation(
        {"content": "平台适配清单变化后应检查", "title": "", "id": ""}
    ) == "platform_mapping_check"
    assert checker._classify_runtime_projection_remediation(
        {"content": "第三方 Skill 接管后应检查同步", "title": "", "id": ""}
    ) == "skill_projection_check"


def test_runtime_projection_reports_missing_authority_and_spec_ref(tmp_path, monkeypatch):
    docs_specs = tmp_path / "docs" / "specs"
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "DOCS_SPECS_DIR", docs_specs)
    projection = write_md(
        tmp_path / "LDVH-AI-ENTRY.md",
        """
# Runtime Projection

无权威来源引用
""",
    )
    missing_ref_projection = write_md(
        tmp_path / "runtime-missing-ref.md",
        """
# Runtime Projection

规范来源：`docs/specs/99-Missing.md`
""",
    )

    report = checker.runtime_projection_report_build([str(projection), str(missing_ref_projection)])

    assert report["summary"]["status"] == "open"
    assert report["metadata"]["checked_file_count"] == 2
    assert {item["code"] for item in report["issues"]} == {
        "RUNTIME_PROJECTION_AUTHORITY_MISSING",
        "RUNTIME_PROJECTION_SPEC_REF_MISSING",
    }


def test_runtime_projection_reports_copied_formal_body(tmp_path, monkeypatch):
    docs_specs = tmp_path / "docs" / "specs"
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "DOCS_SPECS_DIR", docs_specs)
    write_md(
        docs_specs / "04.02-Test.md",
        """
# Runtime Source

这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第一行。
这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第二行。
这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第三行。
""",
    )
    projection = write_md(
        tmp_path / "LDVH-AI-ENTRY.md",
        """
# Runtime Projection

规范来源：`docs/specs/04.02-Test.md`

这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第一行。
这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第二行。
这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第三行。
""",
    )

    report = checker.runtime_projection_report_build([str(projection)])

    assert report["summary"]["status"] == "degraded"
    assert report["issues"][0]["code"] == "RUNTIME_PROJECTION_BODY_COPIED"


def test_runtime_projection_cli_outputs_json(tmp_path, monkeypatch, capsys):
    docs_specs = tmp_path / "docs" / "specs"
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "DOCS_SPECS_DIR", docs_specs)
    write_md(
        docs_specs / "04.02-Test.md",
        """
# Runtime Source
""",
    )
    projection = write_md(
        tmp_path / "LDVH-AI-ENTRY.md",
        """
# Runtime Projection

规范来源：`docs/specs/04.02-Test.md`
""",
    )

    exit_code = checker.main(["runtime-projection", str(projection), "--format", "json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["metadata"]["report"] == "runtime-projection"
    assert payload["summary"]["status"] == "closed"


# ══════════════════════════════════════════════════════════════════════
# human-gate — Human Gate 轻量人类决策记录结构检查
# ══════════════════════════════════════════════════════════════════════

def human_gate_codes(issues):
    return [issue.code for issue in issues]


def test_human_gate_complete_record_passes(tmp_path):
    path = write_md(
        tmp_path / "gate.md",
        """
# Gate

Human Gate 记录：
- 时间：2026-06-10
- 决策：确认推进
- 范围：docs/specs/41、docs/research/18
- 约束：验证命令通过，剩余 Web 消费未实现，后续写回评估
""",
    )

    assert checker.human_gate_check_file(path) == []


def test_human_gate_missing_fields_are_reported(tmp_path):
    path = write_md(
        tmp_path / "gate-missing.md",
        """
# Gate

Human Gate 记录：
- Human 决策：用户同意
""",
    )

    issues = checker.human_gate_check_file(path)

    assert "HUMAN_GATE_FIELD_MISSING" in human_gate_codes(issues)
    assert any("时间" in issue.message for issue in issues)
    assert any("范围" in issue.message for issue in issues)


def test_human_gate_empty_field_is_reported(tmp_path):
    path = write_md(
        tmp_path / "gate-empty.md",
        """
# Gate

Human Gate 记录：
- 时间：
- 决策：是否关闭
- 范围：docs
- 约束：人工确认
""",
    )

    issues = checker.human_gate_check_file(path)

    assert "HUMAN_GATE_FIELD_EMPTY" in human_gate_codes(issues)
    assert any("时间" in issue.message for issue in issues)


def test_human_gate_continuation_satisfies_field_value(tmp_path):
    path = write_md(
        tmp_path / "gate-continuation.md",
        """
# Gate

Human Gate 记录：
- 时间：
  2026-06-10
- 决策：暂缓
- 范围：Task 和 docs/research/18
- 约束：测试通过，后续仍需 Web
""",
    )

    assert checker.human_gate_check_file(path) == []


def test_human_gate_template_in_code_block_is_ignored(tmp_path):
    path = write_md(
        tmp_path / "gate-template.md",
        """
# Gate

```text
Human Gate 记录：
- 时间：
- 决策：
```
""",
    )

    assert checker.human_gate_check_file(path) == []


def test_human_gate_cli_reports_issues(tmp_path, capsys):
    path = write_md(
        tmp_path / "gate-cli.md",
        """
# Gate

Human Gate 记录：
- Human 决策：确认
""",
    )

    exit_code = checker.main(["human-gate", str(path)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Human Gate 轻量人类决策记录结构检查失败" in output
    assert "HUMAN_GATE_FIELD_MISSING" in output


def test_human_gate_report_degraded_when_no_records(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "notes.md",
        """
# Notes

No gate records.
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "degraded"
    assert report["metadata"]["record_count"] == 0
    assert report["metadata"]["issue_count"] == 0


def test_human_gate_report_open_when_record_incomplete(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-incomplete.md",
        """
# Gate

Human Gate 记录：
- Human 决策：确认
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "open"
    assert report["metadata"]["record_count"] == 1
    assert report["metadata"]["issue_count"] > 0
    assert {item["status"] for item in report["issues"]} == {"open"}
    assert "HUMAN_GATE_FIELD_MISSING" in {item["code"] for item in report["issues"]}


def test_human_gate_report_closed_when_record_complete(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-complete.md",
        """
# Gate

Human Gate 记录：
- 时间：2026-06-10
- 决策：确认推进
- 范围：docs/specs/41、docs/research/18
- 约束：验证命令通过，剩余 Web 消费未实现，后续写回评估
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "closed"
    assert report["metadata"]["record_count"] == 1
    assert report["issues"] == []


def test_human_gate_report_counts_multiple_markdown_records(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-multiple.md",
        """
# Gate

Human Gate 记录：
- 时间：2026-06-10
- 决策：确认推进
- 范围：docs/specs/41
- 约束：需要验证

Human Gate 记录：
- 时间：2026-06-11
- 决策：暂缓
- 范围：docs/specs/42
- 约束：等待补充证据
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "closed"
    assert report["metadata"]["record_count"] == 2
    assert report["issues"] == []


def test_human_gate_report_accepts_yaml_records(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate.yaml",
        """
human_gate:
  - time: 2026-06-10
    decision: 确认推进
    scope: docs/specs/41
    constraints: 需要验证
  - time: 2026-06-11
    decision: 暂缓
    scope: docs/specs/42
    constraints: 等待补充证据
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "closed"
    assert report["metadata"]["record_count"] == 2
    assert report["metadata"]["scope"] == "project-local Markdown/YAML facts only"
    assert report["issues"] == []


def test_human_gate_yaml_missing_fields_are_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-incomplete.yaml",
        """
human_gates:
  - decision: 确认推进
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "open"
    assert report["metadata"]["record_count"] == 1
    assert "HUMAN_GATE_FIELD_MISSING" in {item["code"] for item in report["issues"]}


def test_human_gate_report_cli_outputs_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-cli-report.md",
        """
# Gate

Human Gate 记录：
- Human 决策：确认
""",
    )

    exit_code = checker.main(["human-gate-report", str(path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["metadata"]["report"] == "human-gate"
    assert payload["summary"]["status"] == "open"
    assert payload["metadata"]["record_count"] == 1


# ══════════════════════════════════════════════════════════════════════
# governed-projects — 工作区根目录管辖项目配置检查
# ══════════════════════════════════════════════════════════════════════


def write_governed_projects(root, content):
    return write_md(root / "LDVH-GOVERNED-PROJECTS.yaml", content)


def governed_project_codes(issues):
    return [issue.code for issue in issues]


def test_governed_projects_empty_list_passes(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理当前工作区项目。
projects: []
""",
    )

    assert checker.governed_projects_check_root(tmp_path) == []


def test_governed_projects_multiple_projects_pass(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理多个项目。
projects:
  - id: app-web
    path: /Users/me/projects/app-web
    name: App Web
    description: |
      前端项目。
  - id: app-api
    path: /Users/me/projects/app-api
""",
    )

    assert checker.governed_projects_check_root(tmp_path) == []


def test_governed_projects_product_fields_are_required(tmp_path):
    write_governed_projects(tmp_path, "projects: []")

    codes = governed_project_codes(checker.governed_projects_check_root(tmp_path))

    assert "GOVERNED_PROJECTS_ROOT_FIELD_MISSING" in codes


def test_governed_projects_duplicate_id_is_reported(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理当前工作区项目。
projects:
  - id: app
    name: App One
    description: One
    path: /tmp/app-one
  - id: app
    name: App Two
    description: Two
    path: /tmp/app-two
""",
    )

    issues = checker.governed_projects_check_root(tmp_path)

    assert "GOVERNED_PROJECT_ID_DUPLICATE" in governed_project_codes(issues)


def test_governed_projects_extra_fields_are_reported(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理当前工作区项目。
version: 1
projects:
  - id: app
    name: App
    description: App project
    path: /tmp/app
    type: governed_project
""",
    )

    codes = governed_project_codes(checker.governed_projects_check_root(tmp_path))

    assert "GOVERNED_PROJECTS_ROOT_FIELD_FORBIDDEN" in codes
    assert "GOVERNED_PROJECT_FIELD_FORBIDDEN" in codes

# ══════════════════════════════════════════════════════════════════════
# ldvh-landing-check — 42 LDVH落地与检查派生报告
# ══════════════════════════════════════════════════════════════════════

def build_ldvh_landing_check_fixture(tmp_path, monkeypatch):
    docs_specs = build_landing_report_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(checker, "SPECS_DIR", docs_specs)
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  测试管辖项目配置。
projects:
  - id: ldvh-test
    path: /tmp/ldvh-test
""",
    )
    task_dir = tmp_path / "ldvh-base" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    workarea_dir = tmp_path / "ldvh-base" / "workareas"
    workarea_dir.mkdir(parents=True, exist_ok=True)
    (workarea_dir / "workarea-0001-test.yaml").write_text(
        """
id: workarea-0001
type: workarea
title: 测试工作域
status: active
created: '2026-06-10T00:00:00'
updated: '2026-06-10T00:00:00'
description: 测试工作域说明
source: 测试
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    taskplan_dir = tmp_path / "ldvh-base" / "taskplans"
    taskplan_dir.mkdir(parents=True, exist_ok=True)
    (taskplan_dir / "taskplan-0001-test.yaml").write_text(
        """
id: taskplan-0001
type: taskplan
title: 测试计划
status: active
created: '2026-06-10T00:00:00'
updated: '2026-06-10T00:00:00'
workarea: workarea-0001
description: 测试计划说明
success_criteria: |
  - [ ] 可验证条件
source: 测试
tasks:
  - task-0001
related_docs: []
related_adrs: []
related_memos: []
related_pitfalls: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (task_dir / "task-0001-test.yaml").write_text(
        """
id: task-0001
type: task
title: 测试任务
status: planned
created: '2026-06-10T00:00:00'
updated: '2026-06-10T00:00:00'
taskplan: taskplan-0001
description: |
  测试任务说明。
source: 测试
acceptance: |
  - [ ] 可验证条件
blocked_by: []
related_adrs: []
related_docs: []
affected_docs: []
deliverables: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return docs_specs


def test_ldvh_landing_check_consumes_existing_reports(tmp_path, monkeypatch):
    build_ldvh_landing_check_fixture(tmp_path, monkeypatch)

    report = checker.ldvh_landing_check_build(tmp_path)

    assert report["metadata"]["report"] == "ldvh-landing-check"
    assert report["metadata"]["source_of_truth"] is False
    assert {item["id"] for item in report["checks"]} == {
        "governed_projects",
        "landing_report",
        "runtime_projection",
        "human_gate",
        "fact_validate",
        "spec_validate",
    }
    assert report["summary"]["status"] == "open"
    assert report["summary"]["bootstrap_baseline_status"] == "open"
    assert report["summary"]["bootstrap_baseline_open_item_count"] >= 1
    assert next(item for item in report["checks"] if item["id"] == "governed_projects")["status"] == "closed"
    assert next(item for item in report["checks"] if item["id"] == "fact_validate")["status"] == "closed"
    assert any(item["id"] == "human_gate" and item["status"] == "degraded" for item in report["remaining_gaps"])
    baseline = report["bootstrap_baseline"]
    assert [item["id"] for item in baseline["definitions"]] == [
        "specs_integrity",
        "asset_directories",
        "governed_projects_config",
        "work_model_workflow_indexes",
        "environment_matrix",
        "runtime_projection_entry",
        "code_self_check",
        "web_asset",
        "report_structure",
        "gap_classification_routing",
    ]
    assert {item["id"] for item in baseline["items"]} == {item["id"] for item in baseline["definitions"]}
    assert baseline["summary"]["item_count"] == 10
    assert next(item for item in baseline["items"] if item["id"] == "web_asset")["status"] == "open"
    assert next(item for item in baseline["items"] if item["id"] == "report_structure")["status"] == "closed"
    assert "环境承接" in next(item for item in baseline["items"] if item["id"] == "environment_matrix")["gap_categories"]
    assert set(baseline["summary"]["gap_categories"]) <= {"规范", "Code", "Web", "Task", "事实源", "环境承接", "Human Gate"}


def test_ldvh_landing_check_reports_missing_governed_projects(tmp_path, monkeypatch):
    build_landing_report_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(checker, "SPECS_DIR", tmp_path / "docs" / "specs")

    report = checker.ldvh_landing_check_build(tmp_path)

    governed = next(item for item in report["checks"] if item["id"] == "governed_projects")
    assert report["summary"]["status"] == "open"
    assert governed["status"] == "open"
    assert governed["issues"][0]["code"] == "GOVERNED_PROJECTS_MISSING"


def test_ldvh_landing_check_reports_fact_validation_issues(tmp_path, monkeypatch):
    build_ldvh_landing_check_fixture(tmp_path, monkeypatch)
    bad_task = tmp_path / "ldvh-base" / "tasks" / "task-0002-bad.yaml"
    bad_task.write_text("id: bad\ntype: task\n", encoding="utf-8")

    report = checker.ldvh_landing_check_build(tmp_path)

    fact_check = next(item for item in report["checks"] if item["id"] == "fact_validate")
    assert report["summary"]["status"] == "open"
    assert fact_check["status"] == "open"
    assert fact_check["issue_count"] > 0


def test_ldvh_landing_check_cli_outputs_json(tmp_path, monkeypatch, capsys):
    build_ldvh_landing_check_fixture(tmp_path, monkeypatch)

    exit_code = checker.main(["ldvh-landing-check", "--workspace-root", str(tmp_path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["metadata"]["report"] == "ldvh-landing-check"
    assert payload["summary"]["status"] == "open"
    assert payload["metadata"]["bootstrap_baseline_source"] == "docs/research/42-ldvh-landing-check-LDVH落地与检查.md (已退回 research，待重新设计)"
    assert payload["bootstrap_baseline"]["summary"]["item_count"] == 10
    assert payload["remaining_gaps"]


# ══════════════════════════════════════════════════════════════════════
# web-validate — Web Validate 页面只读数据合同
# ══════════════════════════════════════════════════════════════════════

def test_web_validate_builds_web_contract_from_code(tmp_path, monkeypatch):
    build_ldvh_landing_check_fixture(tmp_path, monkeypatch)

    report = checker.web_validate_build(str(tmp_path))

    assert report["command"] == "web_validate"
    assert report["action"] == "validate"
    assert report["target"] == "ldvh-base"
    assert report["summary"]["files"] == 3
    assert report["summary"]["errors"] == 0
    assert "landingCheck" in report["reports"]
    assert "landingReport" in report["reports"]
    assert "humanGateReport" in report["reports"]
    assert report["reports"]["landingCheck"]["summary"]["status"] == "open"
    assert report["reports"]["landingReport"]["summary"]["gap_total"] >= 1
    assert report["reports"]["humanGateReport"]["metadata"]["record_count"] == 0


def test_web_validate_cli_outputs_json_without_failing_on_open_status(tmp_path, monkeypatch, capsys):
    build_ldvh_landing_check_fixture(tmp_path, monkeypatch)

    exit_code = checker.main(["web-validate", "--workspace-root", str(tmp_path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "web_validate"
    assert payload["reports"]["landingCheck"]["summary"]["status"] == "open"
