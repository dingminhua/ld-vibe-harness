from .common import checker, write_md
from spec_checks import v2 as v2_checks


def test_v2_check_builds_read_only_knowledge_map(tmp_path):
    specs_v2 = tmp_path / "specs-v2"
    write_md(
        specs_v2 / "00-LDVH理念与价值标准.md",
        """
# LDVH理念与价值标准

```yaml
v2_spec:
  spec_id: "00"
  spec_kind: "spec"
  title: "LDVH理念与价值标准"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs-v2/00-LDVH理念与价值标准.md"
  created: "2026-06-22"
  updated: "2026-06-22"
  parent_spec: ""
  relation: ""
  positioning: "定义理念"
  scope: "v2"
  basis: []
  related_specs:
    - "specs-v2/01-规范体系基础规范.md"
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "v2_spec_metadata"
  migration_status: "not_migrated"
```

## 1. 本文解决的问题

定义上位锚点。

## 2. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 需要承接 00 | 人工降级检查 | 规范治理 | 修改时 |

## 3. Human Gate

改变最高锚点时暂停。

## 4. 待补齐事项

无。
""",
    )
    write_md(
        specs_v2 / "01-规范体系基础规范.md",
        """
# 规范体系基础规范

```yaml
v2_spec:
  spec_id: "01"
  spec_kind: "spec"
  title: "规范体系基础规范"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs-v2/01-规范体系基础规范.md"
  created: "2026-06-22"
  updated: "2026-06-22"
  parent_spec: ""
  relation: ""
  positioning: "定义规范体系"
  scope: "v2"
  basis:
    - "specs-v2/00-LDVH理念与价值标准.md"
  related_specs:
    - "specs-v2/01.Att.01-知识地图关系类型表.md"
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "knowledge_map_input"
  migration_status: "not_migrated"
```

## 1. 本文解决的问题

定义规范治理。

## 2. 上位依据

承接 00。

## 3. 构成要素归属与价值判断

属于规范体系。

## 4. 附件规则

授权附件。

## 5. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 需要承接 01 | 人工降级检查 | 规范治理 | 修改时 |

## 6. Human Gate

改变附件授权时暂停。

## 7. 待补齐事项

无。
""",
    )
    write_md(
        specs_v2 / "01.Att.01-知识地图关系类型表.md",
        """
# 知识地图关系类型表

```yaml
v2_attachment:
  attachment_id: "01.Att.01"
  title: "知识地图关系类型表"
  status: "draft"
  authority: "not_active_until_parent_and_human_approved"
  parent_spec: "specs-v2/01-规范体系基础规范.md"
  canonical_path: "specs-v2/01.Att.01-知识地图关系类型表.md"
  purpose: "承载关系类型"
  migration_sources: []
  code_consumption:
    - "knowledge_map_relation_types"
```

## 1. 定位

承载关系类型表。

## 2. 待补齐事项

无。
""",
    )

    report = checker.v2_check_build(tmp_path)
    edge_types = {edge["type"] for edge in report["knowledge_map"]["edges"]}

    assert report["metadata"]["read_only"] is True
    assert "basis" in edge_types
    assert "owns_attachment" in edge_types
    assert not report["diagnostics"]


def test_v2_check_reports_missing_required_section(tmp_path):
    specs_v2 = tmp_path / "specs-v2"
    write_md(
        specs_v2 / "01-规范体系基础规范.md",
        """
# 规范体系基础规范

```yaml
v2_spec:
  spec_id: "01"
  spec_kind: "spec"
  title: "规范体系基础规范"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs-v2/01-规范体系基础规范.md"
  created: "2026-06-22"
  updated: "2026-06-22"
  parent_spec: ""
  relation: ""
  positioning: "定义规范体系"
  scope: "v2"
  basis: []
  related_specs: []
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "v2_spec_metadata"
  migration_status: "not_migrated"
```

## 1. 本文解决的问题

定义规范治理。
""",
    )

    report = checker.v2_check_build(tmp_path)

    assert any(item["code"] == "V2_SPEC_REQUIRED_SECTION_MISSING" for item in report["diagnostics"])


def test_v2_core_implementation_lives_in_spec_checks():
    assert checker.v2_checks is v2_checks
    assert v2_checks.v2_check_build.__module__ == "spec_checks.v2"
