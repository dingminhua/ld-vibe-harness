import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "specs_index_validate.py"
spec = importlib.util.spec_from_file_location("specs_index_validate", MODULE_PATH)
specs_index_validate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(specs_index_validate)


def write_md(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


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
    indexes = specs_index_validate.SpecsChecker(root).build()

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

    indexes = specs_index_validate.SpecsChecker(tmp_path).build()

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

    indexes = specs_index_validate.SpecsChecker(tmp_path).build()

    messages = [item["message"] for item in indexes["diagnostics"]]
    assert any("specs/not-found.md" in message for message in messages)
    assert any("specs/missing.md" in message for message in messages)


def test_write_outputs_creates_expected_json_files(tmp_path):
    root = build_fixture(tmp_path)
    indexes = specs_index_validate.SpecsChecker(root).build()
    out_dir = tmp_path / "out"

    written = specs_index_validate.write_outputs(indexes, out_dir)

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


def test_main_outputs_json_to_stdout(tmp_path, capsys):
    root = build_fixture(tmp_path)

    exit_code = specs_index_validate.main(["--root", str(root)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["metadata"]["tool"] == "tools/specs_index_validate.py"
    assert payload["docs"]
