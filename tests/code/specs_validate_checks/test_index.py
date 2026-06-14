import json
from .common import checker, write_md
from spec_checks import index as index_checks

def test_index_core_implementation_lives_in_spec_checks():
    assert checker.index_checks is index_checks
    assert checker.SpecsChecker is index_checks.SpecsChecker
    assert index_checks.index_main.__module__ == "spec_checks.index"


def test_specs_document_reports_docs_path_reference(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

不得依赖 `docs/studies/01-LDVH评估.md`。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "DOCS_PATH_REFERENCE_IN_SPEC" for item in diagnostics)


def test_specs_document_reports_docs_root_asset_reference(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        tmp_path / "docs" / "README.md",
        """
# 项目文档
""",
    )
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

不得依赖 `docs/README.md`。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "DOCS_ROOT_ASSET_REFERENCE_IN_SPEC" for item in diagnostics)


def test_specs_document_reports_external_url_reference(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

不得依赖 https://example.com/tool-doc 。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "EXTERNAL_REFERENCE_IN_SPEC" for item in diagnostics)


def test_specs_document_reports_possible_duplicate_term_definition(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

适配措施是当前规范重新给出的定义。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "适配措施" in item["message"] for item in diagnostics)


def test_specs_document_allows_term_definition_in_owner_spec(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "00-LD-Vibe-Harness理念与纲要.md",
        """
# LD Vibe Harness 理念与纲要

> 创建日期：2026-06-15
> 定位：总纲
> 适用范围：LDVH

## 1. 第一章
""",
    )
    write_md(
        specs / "05-工作模型基础规范.md",
        """
# 工作模型基础规范

> 创建日期：2026-06-01
> 定位：工作模型规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

工作模型是 LDVH 对工程事实的标准化建模结构。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    assert not any(
        item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "工作模型" in item["message"]
        for item in indexes["diagnostics"]
    )


def test_index_extracts_ldvh_member_for_work_model(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "00-LD-Vibe-Harness理念与纲要.md",
        """
# LD Vibe Harness 理念与纲要

> 创建日期：2026-06-15
> 定位：总纲
> 适用范围：LDVH

## 1. 第一章
""",
    )
    write_md(
        specs / "05-工作模型基础规范.md",
        """
# 工作模型基础规范

> 创建日期：2026-06-15
> 定位：工作模型基础规则
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

## 1. 第一章
""",
    )
    write_md(
        specs / "22-Task-任务.md",
        """
# Task / 任务

> 创建日期：2026-06-15
> 定位：任务工作模型
> 适用范围：LDVH
> 上位依据：`specs/05-工作模型基础规范.md`

```yaml
ldvh_member:
  spec_id: "22"
  kind: work_model
  name_en: Task
  name_zh: 任务
  collection_status: active
  canonical_path: specs/22-Task-任务.md
  instance_root: ldvh-base/tasks/
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - fields
    - status_machine
```

## 1. 第一章
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    members = indexes["members"]
    assert len(members) == 1
    assert members[0]["spec_id"] == "22"
    assert members[0]["kind"] == "work_model"
    assert members[0]["collection_status"] == "active"
    assert members[0]["canonical_path"] == "specs/22-Task-任务.md"
    assert members[0]["code_consumption"] == ["fields", "status_machine"]
    assert not indexes["diagnostics"]


def test_index_reports_ldvh_member_spec_id_mismatch(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "22-Task-任务.md",
        """
# Task / 任务

> 创建日期：2026-06-15
> 定位：任务工作模型
> 适用范围：LDVH
> 上位依据：`specs/05-工作模型基础规范.md`

```yaml
ldvh_member:
  spec_id: "23"
  kind: work_model
  name_en: Task
  name_zh: 任务
  collection_status: active
  canonical_path: specs/22-Task-任务.md
  instance_root: ldvh-base/tasks/
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - fields
```

## 1. 第一章
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path).build()["diagnostics"]

    assert any(item["code"] == "LDVH_MEMBER_SPEC_ID_MISMATCH" for item in diagnostics)


def test_index_reports_missing_ldvh_member_for_concrete_work_model(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "22-Task-任务.md",
        """
# Task / 任务

> 创建日期：2026-06-15
> 定位：任务工作模型
> 适用范围：LDVH
> 上位依据：`specs/05-工作模型基础规范.md`

## 1. 第一章
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path).build()["diagnostics"]

    assert any(item["code"] == "LDVH_MEMBER_MISSING" for item in diagnostics)


def test_index_reports_duplicate_ldvh_member_spec_id(tmp_path):
    specs = tmp_path / "specs"
    for filename in ("22-Task-任务.md", "23-SubTask-子任务.md"):
        write_md(
            specs / filename,
            f"""
# 测试

> 创建日期：2026-06-15
> 定位：测试工作模型
> 适用范围：LDVH
> 上位依据：`specs/05-工作模型基础规范.md`

```yaml
ldvh_member:
  spec_id: "22"
  kind: work_model
  name_en: Test
  name_zh: 测试
  collection_status: active
  canonical_path: specs/{filename}
  instance_root: ldvh-base/tasks/
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - fields
```

## 1. 第一章
""",
        )

    diagnostics = checker.SpecsChecker(tmp_path).build()["diagnostics"]

    assert any(item["code"] == "LDVH_MEMBER_DUPLICATE_SPEC_ID" for item in diagnostics)


def test_specs_document_skips_definition_sentence_in_terminology_spec(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "02-术语规范.md",
        """
# 术语规范

> 创建日期：2026-06-01
> 定位：术语规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

适配措施是正式术语。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert not any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" for item in diagnostics)


def test_specs_subdocument_reports_possible_duplicate_term_definition(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---
## 1. 本文解决的问题
""",
    )
    write_md(
        specs / "03.01-规范文档规范.md",
        """
# 规范文档规范

> 创建日期：2026-06-01
> 所属主文档：`specs/03-文档基础规范.md`
> 关系：应用剖面
> 适用范围：LDVH specs
> 上位依据：`specs/03-文档基础规范.md`

---
## 1. 本文解决的问题

适配措施是当前子文档重新给出的定义。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "适配措施" in item["message"] for item in diagnostics)


def test_specs_subdocument_allows_term_application_sentence(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---
## 1. 本文解决的问题
""",
    )
    write_md(
        specs / "03.01-规范文档规范.md",
        """
# 规范文档规范

> 创建日期：2026-06-01
> 所属主文档：`specs/03-文档基础规范.md`
> 关系：应用剖面
> 适用范围：LDVH specs
> 上位依据：`specs/03-文档基础规范.md`

---
## 1. 本文解决的问题

适配措施在本文中用于说明具体环境接入结果。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    assert not any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" for item in indexes["diagnostics"])


def test_specs_subdocument_reports_forbidden_term_definition_section(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---
## 1. 本文解决的问题
""",
    )
    write_md(
        specs / "03.01-规范文档规范.md",
        """
# 规范文档规范

> 创建日期：2026-06-01
> 所属主文档：`specs/03-文档基础规范.md`
> 关系：应用剖面
> 适用范围：LDVH specs
> 上位依据：`specs/03-文档基础规范.md`

---
## 1. 本文解决的问题

## 2. 术语定义
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "FORBIDDEN_TERM_DEFINITION_SECTION" and "术语定义" in item["message"] for item in diagnostics)


def test_specs_subdocument_reports_definition_in_header_field(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03.01-规范文档规范.md",
        """
# 规范文档规范

> 创建日期：2026-06-01
> 所属主文档：`specs/03-文档基础规范.md`
> 关系：应用剖面
> 定位：适配措施是当前子文档重新给出的定义
> 适用范围：LDVH specs
> 上位依据：`specs/03-文档基础规范.md`

---
## 1. 本文解决的问题
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "适配措施" in item["message"] for item in diagnostics)


def test_specs_subdocument_reports_definition_in_table_cell(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03.01-规范文档规范.md",
        """
# 规范文档规范

> 创建日期：2026-06-01
> 所属主文档：`specs/03-文档基础规范.md`
> 关系：应用剖面
> 适用范围：LDVH specs
> 上位依据：`specs/03-文档基础规范.md`

---
## 1. 本文解决的问题

| 术语 | 说明 |
|---|---|
| 适配措施 | 适配措施是当前子文档重新给出的定义 |
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "适配措施" in item["message"] for item in diagnostics)


def test_specs_subdocument_reports_definition_in_footnote(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03.01-规范文档规范.md",
        """
# 规范文档规范

> 创建日期：2026-06-01
> 所属主文档：`specs/03-文档基础规范.md`
> 关系：应用剖面
> 适用范围：LDVH specs
> 上位依据：`specs/03-文档基础规范.md`

---
## 1. 本文解决的问题

[^term]: 适配措施是当前子文档重新给出的定义。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "适配措施" in item["message"] for item in diagnostics)


def test_specs_document_reports_definition_with_prefix(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

在本文中，适配措施是指当前规范重新给出的定义。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "适配措施" in item["message"] for item in diagnostics)


def test_specs_document_reports_definition_with_zai_ben_guifan_prefix(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

在本规范中，环境入口定义为某种入口机制。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "环境入口" in item["message"] for item in diagnostics)


def test_specs_document_reports_definition_with_shi_zhi(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

保障机制是指确保规范落地的手段。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "保障机制" in item["message"] for item in diagnostics)


def test_specs_document_reports_definition_with_bare_zhi(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

适配措施指当前规范重新给出的定义。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "适配措施" in item["message"] for item in diagnostics)


def test_specs_document_reports_definition_in_numbered_list(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

1. 适配措施是当前规范重新给出的定义。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" and "适配措施" in item["message"] for item in diagnostics)


def test_specs_document_does_not_report_jiancha_shifou(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

检查是否需要更新规范落地要求。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    assert not any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" for item in indexes["diagnostics"])


def test_specs_document_does_not_report_zhi_xiang(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

环境入口指向具体环境提供的位置或机制。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    assert not any(item["code"] == "POSSIBLE_DUPLICATE_TERM_DEFINITION" for item in indexes["diagnostics"])


def test_specs_document_reports_possible_reverse_related_spec(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范，反向追溯和可发现性登记
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/21-ADR-决策记录.md`

---

## 1. 本文解决的问题

本文定义文档基础规则。
""",
    )
    write_md(
        specs / "21-ADR-决策记录.md",
        """
# ADR 决策记录

> 创建日期：2026-06-01
> 定位：ADR 规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---

## 1. 本文解决的问题

ADR 文档遵守 `specs/03-文档基础规范.md`。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert any(item["code"] == "POSSIBLE_REVERSE_RELATED_SPEC" for item in diagnostics)


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
        tmp_path / "docs" / "studies" / "01-评估.md",
        """
# 评估

> 创建日期：2026-06-01
> 定位：评估
> 调研边界：内部评估
> 执行效力：无
> 编号归属：studies

## 1. 结论
""",
    )
    write_md(
        tmp_path / "docs" / "sources" / "01-外部资料.md",
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


def test_numbered_specs_subdocument_is_inferred_from_filename(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03.01-规范文档规范.md",
        """
# 规范文档规范

> 创建日期：2026-06-01
> 定位：规范文档应用剖面
> 适用范围：LDVH specs
> 上位依据：`specs/03-文档基础规范.md`

---
## 1. 本文解决的问题
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    doc = indexes["docs"][0]
    assert doc["doc_kind"] == "subdocument"
    assert any(item["code"] == "MISSING_HEADER_FIELD" and "所属主文档" in item["message"] for item in indexes["diagnostics"])
    assert any(item["code"] == "MISSING_HEADER_FIELD" and "关系" in item["message"] for item in indexes["diagnostics"])


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


def test_code_docs_path_is_resolved(tmp_path):
    specs = tmp_path / "specs"
    code_docs = tmp_path / "code" / "docs"
    write_md(code_docs / "01-Code参考实现结构规范.md", "# Code 参考实现结构规范")
    write_md(
        specs / "07-Code确定性执行实现规范.md",
        """
# Code 确定性执行实现规范

> 创建日期：2026-06-01
> 定位：Code 规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

## 1. 本文解决的问题

Code 参考实现结构入口为 `code/docs/01-Code参考实现结构规范.md`。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    assert not any(
        item["code"] == "BROKEN_MARKDOWN_PATH" and "code/docs/01-Code参考实现结构规范.md" in item["message"]
        for item in indexes["diagnostics"]
    )


def test_missing_code_docs_path_reports_broken_path(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "07-Code确定性执行实现规范.md",
        """
# Code 确定性执行实现规范

> 创建日期：2026-06-01
> 定位：Code 规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

## 1. 本文解决的问题

Code 参考实现结构入口为 `code/docs/missing.md`。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    assert any(
        item["code"] == "BROKEN_MARKDOWN_PATH" and "code/docs/missing.md" in item["message"]
        for item in indexes["diagnostics"]
    )


def test_environment_template_markdown_paths_do_not_require_repo_files(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "04-规范落地与环境适配基础规范.md",
        """
# 规范落地与环境适配基础规范

> 创建日期：2026-06-01
> 定位：04 父规范
> 适用范围：LDVH

## 1. 本文解决的问题
""",
    )
    write_md(
        specs / "04.03-环境入口适配与部署规范.md",
        """
# 环境入口适配与部署规范

> 创建日期：2026-06-01
> 定位：环境入口
> 适用范围：LDVH
> 上位依据：`specs/04-规范落地与环境适配基础规范.md`

## 1. 本文解决的问题

Codex 用户级入口可写作 `~/.codex/AGENTS.md`。
Trae 用户级入口可写作 `.trae-cn/user_rules/ldvh_rules.md`。
模板变量可写作 `<LDVH_REPO_ROOT>/rules/LDVH-AI-ENTRY.md`。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    assert not any(
        item["code"] == "BROKEN_MARKDOWN_PATH"
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


def test_subdocument_contract_diagnostics_help_ai_review(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03.01-规范文档规范.md",
        """
# 规范文档规范

> 创建日期：2026-06-01
> 所属主文档：`specs/03-文档基础规范.md`
> 关系：父规范扩展
> 定位：规范文档应用剖面
> 适用范围：LDVH specs
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---
## 1. 本文解决的问题
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path).build()["diagnostics"]
    codes = {item["code"] for item in diagnostics}

    assert "SUBDOCUMENT_PARENT_NUMBER_NOT_FOUND" in codes
    assert "SUBDOCUMENT_PARENT_DOC_NOT_FOUND" in codes
    assert "SUBDOCUMENT_BASIS_MISSING_PARENT" in codes
    assert "SUBDOCUMENT_RELATION_INVALID" in codes


def test_parent_subdocument_registry_diagnostics(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "05-工作模型基础规范.md",
        """
# 工作模型基础规范

> 创建日期：2026-06-01
> 定位：工作模型基础规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---
## 1. 本文解决的问题

本文定义工作模型基础规则。
""",
    )
    write_md(
        specs / "05.01-工作字段内容格式规范.md",
        """
# 工作字段内容格式规范

> 创建日期：2026-06-01
> 所属主文档：`specs/05-工作模型基础规范.md`
> 关系：专题子文档
> 定位：字段内容格式规范
> 适用范围：LDVH 工作模型字段
> 上位依据：`specs/05-工作模型基础规范.md`

---
## 1. 本文解决的问题
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path).build()["diagnostics"]
    codes = {item["code"] for item in diagnostics}

    assert "PARENT_SUBDOCUMENT_BOUNDARY_SECTION_MISSING" in codes
    assert "PARENT_SUBDOCUMENT_NOT_REGISTERED" in codes


def test_parent_subdocument_registry_passes_when_boundary_lists_child(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "05-工作模型基础规范.md",
        """
# 工作模型基础规范

> 创建日期：2026-06-01
> 定位：工作模型基础规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---
## 1. 本文解决的问题

本文定义工作模型基础规则。

## 2. 子文档清单与边界

| 子文档 | 说明 |
|---|---|
| `specs/05.01-工作字段内容格式规范.md` | 字段内容格式规则 |
""",
    )
    write_md(
        specs / "05.01-工作字段内容格式规范.md",
        """
# 工作字段内容格式规范

> 创建日期：2026-06-01
> 所属主文档：`specs/05-工作模型基础规范.md`
> 关系：专题子文档
> 定位：字段内容格式规范
> 适用范围：LDVH 工作模型字段
> 上位依据：`specs/05-工作模型基础规范.md`

---
## 1. 本文解决的问题
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path).build()["diagnostics"]
    codes = {item["code"] for item in diagnostics}

    assert "PARENT_SUBDOCUMENT_BOUNDARY_SECTION_MISSING" not in codes
    assert "PARENT_SUBDOCUMENT_NOT_REGISTERED" not in codes


def test_related_spec_without_body_reference_is_reported(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/21-ADR-决策记录.md`

---
## 1. 本文解决的问题

本文定义文档基础规则。
""",
    )
    write_md(
        specs / "21-ADR-决策记录.md",
        """
# ADR 决策记录

> 创建日期：2026-06-01
> 定位：ADR 规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

---
## 1. 本文解决的问题
""",
    )

    hints = checker.SpecsChecker(tmp_path).build()["review_hints"]

    assert any(item["code"] == "RELATED_SPEC_WITHOUT_BODY_REFERENCE" for item in hints)


def test_bidirectional_related_spec_weak_evidence_is_reported(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01
> 定位：文档规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/21-ADR-决策记录.md`

---
## 1. 本文解决的问题

本文消费 `specs/21-ADR-决策记录.md`。
""",
    )
    write_md(
        specs / "21-ADR-决策记录.md",
        """
# ADR 决策记录

> 创建日期：2026-06-01
> 定位：ADR 规范
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/03-文档基础规范.md`

---
## 1. 本文解决的问题
""",
    )

    hints = checker.SpecsChecker(tmp_path).build()["review_hints"]

    assert any(item["code"] == "BIDIRECTIONAL_RELATED_SPEC_WEAK_EVIDENCE" for item in hints)


def test_write_outputs_creates_expected_json_files(tmp_path):
    root = build_fixture(tmp_path)
    indexes = checker.SpecsChecker(root).build()
    out_dir = tmp_path / "out"

    written = checker.write_outputs(indexes, out_dir)

    assert written == [
        "specs-diagnostics.json",
        "specs-docs-index.json",
        "specs-mechanism-index.json",
        "specs-members-index.json",
        "specs-relations-index.json",
        "specs-review-hints.json",
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
    assert payload["metadata"]["tool"] == "code/specs_validate.py"
    assert payload["docs"]
