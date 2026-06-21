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


def test_git_commit_spec_allows_conventional_commits_standard_url(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "10-Git提交规范.md",
        """
# Git 提交规范

```yaml
ldvh_doc:
  doc_id: "10"
  doc_kind: "formal_spec"
  title: "Git 提交规范"
  status: "active"
  canonical_path: "specs/10-Git提交规范.md"
  created: "2026-06-19"
  updated: "2026-06-19"
  parent_doc: ""
  relation: ""
  positioning: "定义 Git commit message 格式规则"
  scope: "LDVH 管辖项目"
  basis:
    - "specs/09-事实源边界与承载规范.md"
  related_specs: []
  code_consumption:
    - "doc_metadata"
```

---
## 1. 本文解决的问题

采用 Conventional Commits 1.0.0，官方链接为 <https://www.conventionalcommits.org/en/v1.0.0/>。
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    diagnostics = indexes["diagnostics"]
    assert not any(item["code"] == "EXTERNAL_REFERENCE_IN_SPEC" for item in diagnostics)


def test_workflow_member_exposes_assurance_takeover(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "40-Workflow.md",
        """
# Workflow

```yaml
ldvh_member:
  spec_id: 40
  kind: work_process
  name_en: workflow
  name_zh: 工作流程
  collection_status: active
  canonical_path: specs/40-Workflow.md
  code_consumption:
    - workflow_index
  assurance_takeover:
    - "source_spec=specs/04.01-规范保障声明规范.md; requirement=工作流程接管要求; scope=执行责任接管"
```
""",
    )

    checker_instance = checker.SpecsChecker(tmp_path)
    indexes = checker_instance.build()
    member = next(item for item in indexes["members"] if item["spec_id"] == "40")
    entries = checker_instance.members_as_collection_entries("work_process")

    assert member["assurance_takeover"] == [
        "source_spec=specs/04.01-规范保障声明规范.md; requirement=工作流程接管要求; scope=执行责任接管"
    ]
    assert entries[0]["assurance_takeover"] == member["assurance_takeover"]
    assert not any(item["code"] == "LDVH_MEMBER_ASSURANCE_TAKEOVER_INVALID" for item in indexes["diagnostics"])


def test_workflow_member_reports_invalid_assurance_takeover(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "40-Workflow.md",
        """
# Workflow

```yaml
ldvh_member:
  spec_id: 40
  kind: work_process
  name_en: workflow
  name_zh: 工作流程
  collection_status: active
  canonical_path: specs/40-Workflow.md
  code_consumption:
    - workflow_index
  assurance_takeover:
    - "source_spec=specs/04.01-规范保障声明规范.md; requirement=工作流程接管要求"
```
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path).build()["diagnostics"]

    assert any(item["code"] == "LDVH_MEMBER_ASSURANCE_TAKEOVER_INVALID" for item in diagnostics)


def test_workflow_member_exposes_and_validates_capability_assets(tmp_path):
    specs = tmp_path / "specs"
    skills = tmp_path / "skills" / "ldvh-example"
    hooks = tmp_path / "hooks"
    code = tmp_path / "code"
    skills.mkdir(parents=True)
    hooks.mkdir(parents=True)
    code.mkdir(parents=True)
    write_md(
        skills / "SKILL.md",
        """
---
name: ldvh-example
description: Example.
---

```yaml
ldvh_asset:
  id: "ldvh-example"
  type: "skill"
  status: "active"
  canonical_path: "skills/ldvh-example/SKILL.md"
```
""",
    )
    (hooks / "ldvh-hooks.yaml").write_text(
        """
ldvh_asset:
  id: "ldvh-hook-registry"
  type: "hook"
  status: "active"
  canonical_path: "hooks/ldvh-hooks.yaml"
""",
        encoding="utf-8",
    )
    (code / "validator.py").write_text("print('ok')\n", encoding="utf-8")
    write_md(
        specs / "44-Workflow.md",
        """
# Workflow

```yaml
ldvh_member:
  spec_id: 44
  kind: work_process
  name_en: workflow
  name_zh: 工作流程
  collection_status: active
  canonical_path: specs/44-Workflow.md
  code_consumption:
    - workflow_index
  capability_assets:
    - "type=skill; path=skills/ldvh-example/SKILL.md; purpose=复用执行外壳; status=required"
    - "type=hook; path=hooks/ldvh-hooks.yaml; purpose=事件登记; status=required"
    - "type=code; path=code/validator.py; purpose=确定性校验; status=required"
```
""",
    )

    checker_instance = checker.SpecsChecker(tmp_path)
    indexes = checker_instance.build()
    member = next(item for item in indexes["members"] if item["spec_id"] == "44")
    entries = checker_instance.members_as_collection_entries("work_process")

    assert member["capability_assets"] == [
        "type=skill; path=skills/ldvh-example/SKILL.md; purpose=复用执行外壳; status=required",
        "type=hook; path=hooks/ldvh-hooks.yaml; purpose=事件登记; status=required",
        "type=code; path=code/validator.py; purpose=确定性校验; status=required",
    ]
    assert entries[0]["capability_assets"] == member["capability_assets"]
    assert not any(item["code"].startswith("LDVH_MEMBER_CAPABILITY_ASSET") for item in indexes["diagnostics"])


def test_workflow_member_reports_invalid_capability_assets(tmp_path):
    specs = tmp_path / "specs"
    skills = tmp_path / "skills" / "bad"
    skills.mkdir(parents=True)
    write_md(skills / "SKILL.md", "# Missing metadata\n")
    write_md(
        specs / "44-Workflow.md",
        """
# Workflow

```yaml
ldvh_member:
  spec_id: 44
  kind: work_process
  name_en: workflow
  name_zh: 工作流程
  collection_status: active
  canonical_path: specs/44-Workflow.md
  code_consumption:
    - workflow_index
  capability_assets:
    - "type=skill; path=skills/bad/SKILL.md; purpose=复用执行外壳; status=installed"
    - "type=plugin; path=plugins/example; purpose=环境插件; status=required"
    - "type=code; path=code/missing.py; purpose=确定性校验; status=required"
    - "type=hook; path=hooks/missing.yaml; purpose=事件登记"
```
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path).build()["diagnostics"]
    codes = {item["code"] for item in diagnostics}

    assert "LDVH_MEMBER_CAPABILITY_ASSET_METADATA_MISSING" in codes
    assert "LDVH_MEMBER_CAPABILITY_ASSET_STATUS_INVALID" in codes
    assert "LDVH_MEMBER_CAPABILITY_ASSET_TYPE_INVALID" in codes
    assert "LDVH_MEMBER_CAPABILITY_ASSET_PATH_MISSING" in codes
    assert "LDVH_MEMBER_CAPABILITY_ASSETS_INVALID" in codes


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
        specs / "05-事实模型基础规范.md",
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
        specs / "05-事实模型基础规范.md",
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
        specs / "21-WorkCase-工作项.md",
        """
# WorkCase / 工作项

> 创建日期：2026-06-15
> 定位：工作项模型
> 适用范围：LDVH
> 上位依据：`specs/05-事实模型基础规范.md`

```yaml
ldvh_member:
  spec_id: "21"
  kind: work_model
  name_en: WorkCase
  name_zh: 工作项
  collection_status: active
  canonical_path: specs/21-WorkCase-工作项.md
  instance_root: ldvh-base/workcases/
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
    assert members[0]["spec_id"] == "21"
    assert members[0]["kind"] == "work_model"
    assert members[0]["collection_status"] == "active"
    assert members[0]["canonical_path"] == "specs/21-WorkCase-工作项.md"
    assert members[0]["code_consumption"] == ["fields", "status_machine"]
    assert not indexes["diagnostics"]


def test_index_member_kind_boundary_uses_30_for_work_process(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "29-TestModel-测试模型.md",
        """
# TestModel / 测试模型

```yaml
ldvh_member:
  spec_id: "29"
  kind: work_model
  name_en: TestModel
  name_zh: 测试模型
  collection_status: candidate
  canonical_path: specs/29-TestModel-测试模型.md
  instance_root: ldvh-base/test-models/
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - fields
```

## 1. 第一章
""",
    )
    write_md(
        specs / "30-TestWorkflow-测试流程.md",
        """
# TestWorkflow / 测试流程

```yaml
ldvh_member:
  spec_id: "30"
  kind: work_process
  name_en: TestWorkflow
  name_zh: 测试流程
  collection_status: candidate
  canonical_path: specs/30-TestWorkflow-测试流程.md
  code_consumption:
    - workflow_index
```

## 1. 第一章
""",
    )

    indexes = checker.SpecsChecker(tmp_path).build()

    members = {item["spec_id"]: item for item in indexes["members"]}
    assert members["29"]["kind"] == "work_model"
    assert members["30"]["kind"] == "work_process"
    assert not any(item["code"] == "LDVH_MEMBER_KIND_MISMATCH" for item in indexes["diagnostics"])


def test_index_extracts_ldvh_doc_metadata(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "00-LD-Vibe-Harness理念与纲要.md",
        """
# LD Vibe Harness 理念与纲要

```yaml
ldvh_doc:
  doc_id: "00"
  doc_kind: formal_spec
  title: LD Vibe Harness 理念与纲要
  status: active
  canonical_path: specs/00-LD-Vibe-Harness理念与纲要.md
  created: "2026-06-01"
  updated: "2026-06-01"
  parent_doc: ""
  relation: ""
  positioning: 总纲
  scope: LDVH
  basis: []
  related_specs: []
  code_consumption:
    - doc_metadata
```

## 1. 第一章
""",
    )
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

```yaml
ldvh_doc:
  doc_id: "03"
  doc_kind: formal_spec
  title: 文档基础规范
  status: active
  canonical_path: specs/03-文档基础规范.md
  created: "2026-06-01"
  updated: "2026-06-01"
  parent_doc: ""
  relation: ""
  positioning: 文档规范
  scope: LDVH
  basis:
    - specs/00-LD-Vibe-Harness理念与纲要.md
  related_specs: []
  code_consumption:
    - doc_metadata
    - structure
```

---

## 1. 本文解决的问题
""",
    )

    indexes = checker.SpecsChecker(tmp_path, require_ldvh_doc=True).build()
    doc = next(item for item in indexes["docs"] if item["path"] == "specs/03-文档基础规范.md")

    assert doc["ldvh_doc"]["doc_id"] == "03"
    assert doc["ldvh_doc"]["doc_kind"] == "formal_spec"
    assert doc["ldvh_doc"]["canonical_path"] == "specs/03-文档基础规范.md"
    assert not indexes["diagnostics"]


def test_index_ignores_ldvh_doc_examples_after_preamble(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03.01-规范文档规范.md",
        """
# 规范文档规范

> 创建日期：2026-06-08
> 定位：规范文档
> 适用范围：LDVH
> 所属主文档：`specs/03-文档基础规范.md`
> 关系：应用剖面
> 上位依据：`specs/03-文档基础规范.md`

---

## 1. 示例

```yaml
ldvh_doc:
  doc_id: "99"
  doc_kind: formal_spec
  title: 示例
  status: active
  canonical_path: specs/99-example.md
  created: "2026-06-08"
  positioning: 示例
  scope: 示例
  basis:
    - specs/00-LD-Vibe-Harness理念与纲要.md
  code_consumption:
    - doc_metadata
```
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path, require_ldvh_doc=True).build()["diagnostics"]

    assert any(item["code"] == "LDVH_DOC_MISSING" for item in diagnostics)
    assert not any(item["code"] == "LDVH_DOC_ID_MISMATCH" for item in diagnostics)


def test_index_reports_missing_ldvh_doc_when_required(tmp_path):
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

    diagnostics = checker.SpecsChecker(tmp_path, require_ldvh_doc=True).build()["diagnostics"]

    assert any(item["code"] == "LDVH_DOC_MISSING" for item in diagnostics)


def test_index_reports_absent_ldvh_doc_standard_field(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

```yaml
ldvh_doc:
  doc_id: "03"
  doc_kind: formal_spec
  title: 文档基础规范
  status: active
  canonical_path: specs/03-文档基础规范.md
  created: "2026-06-01"
  parent_doc: ""
  relation: ""
  positioning: 文档规范
  scope: LDVH
  basis:
    - specs/00-LD-Vibe-Harness理念与纲要.md
  related_specs: []
  code_consumption:
    - doc_metadata
```

---

## 1. 本文解决的问题
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path, require_ldvh_doc=True).build()["diagnostics"]

    assert any(item["code"] == "LDVH_DOC_FIELD_ABSENT" and "updated" in item["message"] for item in diagnostics)


def test_index_reports_empty_ldvh_doc_updated(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

```yaml
ldvh_doc:
  doc_id: "03"
  doc_kind: formal_spec
  title: 文档基础规范
  status: active
  canonical_path: specs/03-文档基础规范.md
  created: "2026-06-01"
  updated: ""
  parent_doc: ""
  relation: ""
  positioning: 文档规范
  scope: LDVH
  basis:
    - specs/00-LD-Vibe-Harness理念与纲要.md
  related_specs: []
  code_consumption:
    - doc_metadata
```

---

## 1. 本文解决的问题
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path, require_ldvh_doc=True).build()["diagnostics"]

    assert any(item["code"] == "LDVH_DOC_FIELD_EMPTY" and "updated" in item["message"] for item in diagnostics)


def test_index_reports_invalid_ldvh_doc_updated_date(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

```yaml
ldvh_doc:
  doc_id: "03"
  doc_kind: formal_spec
  title: 文档基础规范
  status: active
  canonical_path: specs/03-文档基础规范.md
  created: "2026-06-01"
  updated: "2026/06/01"
  parent_doc: ""
  relation: ""
  positioning: 文档规范
  scope: LDVH
  basis:
    - specs/00-LD-Vibe-Harness理念与纲要.md
  related_specs: []
  code_consumption:
    - doc_metadata
```

---

## 1. 本文解决的问题
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path, require_ldvh_doc=True).build()["diagnostics"]

    assert any(item["code"] == "LDVH_DOC_DATE_INVALID" and "updated" in item["message"] for item in diagnostics)


def test_index_reports_ldvh_doc_updated_before_created(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

```yaml
ldvh_doc:
  doc_id: "03"
  doc_kind: formal_spec
  title: 文档基础规范
  status: active
  canonical_path: specs/03-文档基础规范.md
  created: "2026-06-02"
  updated: "2026-06-01"
  parent_doc: ""
  relation: ""
  positioning: 文档规范
  scope: LDVH
  basis:
    - specs/00-LD-Vibe-Harness理念与纲要.md
  related_specs: []
  code_consumption:
    - doc_metadata
```

---

## 1. 本文解决的问题
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path, require_ldvh_doc=True).build()["diagnostics"]

    assert any(item["code"] == "LDVH_DOC_UPDATED_BEFORE_CREATED" for item in diagnostics)


def test_index_reports_ldvh_doc_metadata_duplicated_in_header(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "03-文档基础规范.md",
        """
# 文档基础规范

> 创建日期：2026-06-01

```yaml
ldvh_doc:
  doc_id: "03"
  doc_kind: formal_spec
  title: 文档基础规范
  status: active
  canonical_path: specs/03-文档基础规范.md
  created: "2026-06-01"
  updated: "2026-06-01"
  parent_doc: ""
  relation: ""
  positioning: 文档规范
  scope: LDVH
  basis:
    - specs/00-LD-Vibe-Harness理念与纲要.md
  related_specs: []
  code_consumption:
    - doc_metadata
```

---

## 1. 本文解决的问题
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path, require_ldvh_doc=True).build()["diagnostics"]

    assert any(item["code"] == "LDVH_DOC_HEADER_FIELD_FORBIDDEN" and "创建日期" in item["message"] for item in diagnostics)


def test_index_reports_ldvh_doc_path_and_kind_mismatch(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "21-WorkCase-工作项.md",
        """
# WorkCase / 工作项

```yaml
ldvh_doc:
  doc_id: "99"
  doc_kind: formal_spec
  title: WorkCase / 工作项
  status: active
  canonical_path: specs/99-Wrong-路径.md
  created: "2026-06-15"
  updated: "2026-06-15"
  parent_doc: ""
  relation: ""
  positioning: 工作项模型
  scope: LDVH
  basis:
    - specs/05-事实模型基础规范.md
  related_specs: []
  code_consumption:
    - doc_metadata
```

```yaml
ldvh_member:
  spec_id: "21"
  kind: work_model
  name_en: WorkCase
  name_zh: 工作项
  collection_status: active
  canonical_path: specs/21-WorkCase-工作项.md
  instance_root: ldvh-base/workcases/
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - fields
```

## 1. 第一章
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path, require_ldvh_doc=True).build()["diagnostics"]
    codes = {item["code"] for item in diagnostics}

    assert "LDVH_DOC_ID_MISMATCH" in codes
    assert "LDVH_DOC_KIND_MISMATCH" in codes
    assert "LDVH_DOC_CANONICAL_PATH_MISMATCH" in codes
    assert "LDVH_DOC_MEMBER_ID_MISMATCH" in codes


def test_index_reports_ldvh_member_spec_id_mismatch(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "21-WorkCase-工作项.md",
        """
# WorkCase / 工作项

> 创建日期：2026-06-15
> 定位：工作项模型
> 适用范围：LDVH
> 上位依据：`specs/05-事实模型基础规范.md`

```yaml
ldvh_member:
  spec_id: "99"
  kind: work_model
  name_en: WorkCase
  name_zh: 工作项
  collection_status: active
  canonical_path: specs/21-WorkCase-工作项.md
  instance_root: ldvh-base/workcases/
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
        specs / "21-WorkCase-工作项.md",
        """
# WorkCase / 工作项

> 创建日期：2026-06-15
> 定位：工作项模型
> 适用范围：LDVH
> 上位依据：`specs/05-事实模型基础规范.md`

## 1. 第一章
""",
    )

    diagnostics = checker.SpecsChecker(tmp_path).build()["diagnostics"]

    assert any(item["code"] == "LDVH_MEMBER_MISSING" for item in diagnostics)


def test_index_reports_member_fields_duplicated_in_header(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "21-WorkCase-工作项.md",
        """
# WorkCase / 工作项

> 创建日期：2026-06-15
> 定位：工作项模型
> 适用范围：LDVH
> 上位依据：`specs/05-事实模型基础规范.md`
> 文档编号：21
> 集合状态：active
> canonical_path：specs/21-WorkCase-工作项.md

```yaml
ldvh_member:
  spec_id: "21"
  kind: work_model
  name_en: WorkCase
  name_zh: 工作项
  collection_status: active
  canonical_path: specs/21-WorkCase-工作项.md
  instance_root: ldvh-base/workcases/
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

    forbidden = [item for item in diagnostics if item["code"] == "LDVH_MEMBER_HEADER_FIELD_FORBIDDEN"]
    assert len(forbidden) == 3
    assert any("文档编号" in item["message"] for item in forbidden)
    assert any("集合状态" in item["message"] for item in forbidden)
    assert any("canonical_path" in item["message"] for item in forbidden)


def test_index_reports_duplicate_ldvh_member_spec_id(tmp_path):
    specs = tmp_path / "specs"
    for filename in ("21-WorkCase-工作项.md", "22-ADR-决策.md"):
        write_md(
            specs / filename,
            f"""
# 测试

> 创建日期：2026-06-15
> 定位：测试工作模型
> 适用范围：LDVH
> 上位依据：`specs/05-事实模型基础规范.md`

```yaml
ldvh_member:
  spec_id: "21"
  kind: work_model
  name_en: Test
  name_zh: 测试
  collection_status: active
  canonical_path: specs/{filename}
  instance_root: ldvh-base/workcases/
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


def test_index_accepts_work_model_directory_matching_active_members(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "01-目录说明.md",
        """
# 目录说明

> 创建日期：2026-06-08
> 定位：目录说明
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

| 当前编号 | 工作模型 | 事实实例承载 |
|---|---|---|
| 21 | WorkCase / 工作项 | `ldvh-base/workcases/` |
| 22 | ADR / 决策 | `ldvh-base/adrs/` |
""",
    )
    for filename, spec_id, name_en, name_zh, root in (
        ("21-WorkCase-工作项.md", "21", "WorkCase", "工作项", "ldvh-base/workcases/"),
        ("22-ADR-决策.md", "22", "ADR", "决策", "ldvh-base/adrs/"),
    ):
        write_md(
            specs / filename,
            f"""
# {name_en} / {name_zh}

> 创建日期：2026-06-15
> 定位：测试工作模型
> 适用范围：LDVH
> 上位依据：`specs/05-事实模型基础规范.md`

```yaml
ldvh_member:
  spec_id: "{spec_id}"
  kind: work_model
  name_en: {name_en}
  name_zh: {name_zh}
  collection_status: active
  canonical_path: specs/{filename}
  instance_root: {root}
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

    assert not any((item["code"] or "").startswith("WORK_MODEL_DIRECTORY_") for item in diagnostics)


def test_index_reports_stale_work_model_directory_table(tmp_path):
    specs = tmp_path / "specs"
    write_md(
        specs / "01-目录说明.md",
        """
# 目录说明

> 创建日期：2026-06-08
> 定位：目录说明
> 适用范围：LDVH
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`

| 当前编号 | 工作模型 | 事实实例承载 |
|---|---|---|
| 24 | ADR / 决策 | `ldvh-base/adrs/` |
""",
    )
    write_md(
        specs / "22-ADR-决策.md",
        """
# ADR / 决策

> 创建日期：2026-06-15
> 定位：决策工作模型
> 适用范围：LDVH
> 上位依据：`specs/05-事实模型基础规范.md`

```yaml
ldvh_member:
  spec_id: "22"
  kind: work_model
  name_en: ADR
  name_zh: 决策
  collection_status: active
  canonical_path: specs/22-ADR-决策.md
  instance_root: ldvh-base/adrs/
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

    assert any(item["code"] == "WORK_MODEL_DIRECTORY_ENTRY_MISSING" for item in diagnostics)
    assert any(item["code"] == "WORK_MODEL_DIRECTORY_ENTRY_STALE" for item in diagnostics)


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

保障机制是指确保规范保障的手段。
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

检查是否需要更新规范保障要求。
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
        specs / "04-规范保障与环境适配基础规范.md",
        """
# 规范保障与环境适配基础规范

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
> 上位依据：`specs/04-规范保障与环境适配基础规范.md`

## 1. 本文解决的问题

Codex 用户级入口可写作 `~/.codex/AGENTS.md`。
Trae 用户级入口可写作 `.trae-cn/user_rules/ldvh_rules.md`。
模板变量可写作 `<LDVH_REPO_ROOT>/rules/LDVH-WORKSPACE-ENTRY.md`。
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
        specs / "05-事实模型基础规范.md",
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
        specs / "05.01-字段定义与语义规范.md",
        """
# 工作模型字段定义与语义规范

> 创建日期：2026-06-01
> 所属主文档：`specs/05-事实模型基础规范.md`
> 关系：专题子文档
> 定位：工作模型字段定义与语义规范
> 适用范围：LDVH 工作模型字段
> 上位依据：`specs/05-事实模型基础规范.md`

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
        specs / "05-事实模型基础规范.md",
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
| `specs/05.01-字段定义与语义规范.md` | 工作模型字段规则 |
""",
    )
    write_md(
        specs / "05.01-字段定义与语义规范.md",
        """
# 工作模型字段定义与语义规范

> 创建日期：2026-06-01
> 所属主文档：`specs/05-事实模型基础规范.md`
> 关系：专题子文档
> 定位：工作模型字段定义与语义规范
> 适用范围：LDVH 工作模型字段
> 上位依据：`specs/05-事实模型基础规范.md`

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
