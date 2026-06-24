import json
import subprocess
import sys
from pathlib import Path

from .common import checker, write_md
from spec_checks import knowledge_map as knowledge_map_checks
from spec_checks import v2 as v2_checks


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def write_minimal_v2_knowledge_map_fixture(root):
    specs_v2 = root / "specs-v2"
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

定义规范治理，并引用 `code/specs_validate.py`。

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
    return specs_v2


def write_navigation_value_fixture(root):
    specs = root / "specs"
    attachments = specs / "attachments"
    rules = root / "rules"
    write_md(
        specs / "04-Code确定性执行规范.md",
        """
# Code确定性执行规范

```yaml
v2_spec:
  spec_id: "04"
  spec_kind: "spec"
  title: "Code确定性执行规范"
  status: "active"
  authority: "active"
  canonical_path: "specs/04-Code确定性执行规范.md"
  created: "2026-06-24"
  updated: "2026-06-24"
  parent_spec: ""
  relation: ""
  positioning: "定义 Code"
  scope: "Code"
  basis: []
  related_specs:
    - "specs/attachments/04.Att.01-Code需求记录字段表.md"
    - "specs/attachments/04.Att.03-Code结构化输出Schema表.md"
    - "specs/attachments/04.Att.05-知识地图输入范围表.md"
    - "specs/attachments/04.Att.06-知识地图投影Schema表.md"
    - "specs/attachments/04.Att.09-Code回归入口表.md"
  migration_sources:
    - "history/specs-v1/07-Code确定性执行实现规范.md"
  active_fact_source: []
  code_consumption:
    - "knowledge_map_input"
  migration_status: "migrated"
```

## 1. 本文解决的问题

定义 Code。

## 2. 上位依据

无。

## 3. 构成要素归属与价值判断

属于 Code。

## 4. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 知识地图投影要求 | 需要实时投影 | Code | Code | 修改时 |

## 5. Human Gate

改变事实源、Gate、Git 判断、长期降级或输出持久化口径时必须暂停。

## 6. 待补齐事项

无。
""",
    )
    write_md(
        specs / "30-rules-entry-sync-review-Rules入口同步审查.md",
        """
# rules-entry-sync-review-Rules入口同步审查

```yaml
v2_spec:
  spec_id: "30"
  spec_kind: "member_spec"
  title: "rules-entry-sync-review-Rules入口同步审查"
  status: "active"
  authority: "active"
  canonical_path: "specs/30-rules-entry-sync-review-Rules入口同步审查.md"
  created: "2026-06-24"
  updated: "2026-06-24"
  parent_spec: "specs/03-行动编排规范.md"
  relation: "action_member"
  positioning: "Rules 同步审查"
  scope: "Rules"
  basis: []
  related_specs: []
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "action_member_identity"
  migration_status: "migrated"
```

```yaml
v2_action_member:
  spec_id: "30"
  kind: "action_process"
  name_en: "rules-entry-sync-review"
  name_zh: "Rules入口同步审查"
  collection_status: "active"
  canonical_path: "specs/30-rules-entry-sync-review-Rules入口同步审查.md"
  scenario_anchor: "§4"
  context_anchor: "§3"
  gate_anchor: "§5"
  execution_anchor: "§6"
  issue_routing_anchor: "§7"
  writeback_anchor: "§8"
  evidence_anchor: "§8"
  testability_anchor: "§9"
  assurance_takeover: []
  capability_assets: []
  code_consumption:
    - "action_member_identity"
```

## 1. 本文解决的问题

定义 Rules 同步审查。

## 2. 上位依据

承接 03。

## 3. 构成要素归属与价值判断

属于行动编排。

## 4. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| Rules 同步要求 | 需要审查入口 | 行动编排 | Rules | 修改时 |

## 5. Human Gate

高影响入口边界、长期降级、冲突或自动同步判断必须进入 Human Gate。

## 6. 待补齐事项

无。
""",
    )
    attachment_specs = {
        "04.Att.01-Code需求记录字段表.md": ("Code需求记录字段表", "需求字段", "code_requirement_fields"),
        "04.Att.03-Code结构化输出Schema表.md": ("Code结构化输出Schema表", "Schema", "code_output_schema"),
        "04.Att.05-知识地图输入范围表.md": ("知识地图输入范围表", "输入范围", "knowledge_map_input_scope"),
        "04.Att.06-知识地图投影Schema表.md": ("知识地图投影Schema表", "Schema", "knowledge_map_projection_schema"),
        "04.Att.09-Code回归入口表.md": ("Code回归入口表", "回归入口", "code_regression_entry"),
    }
    for filename, (title, purpose, code_consumption) in attachment_specs.items():
        write_md(
            attachments / filename,
            f"""
# {title}

```yaml
v2_attachment:
  attachment_id: "{filename.split('-')[0]}"
  title: "{title}"
  status: "active"
  authority: "active_with_parent_spec"
  parent_spec: "specs/04-Code确定性执行规范.md"
  canonical_path: "specs/attachments/{filename}"
  purpose: "{purpose}"
  migration_sources: []
  code_consumption:
    - "{code_consumption}"
```

## 1. 定位

{purpose}。

## 2. 待补齐事项

无。
""",
        )
    for filename, asset_id, source_specs in (
        (
            "LDVH-WORKSPACE-ENTRY.md",
            "ldvh-workspace-entry",
            ["specs/04-Code确定性执行规范.md", "specs/30-rules-entry-sync-review-Rules入口同步审查.md"],
        ),
        ("LDVH-MAINTAINER-ENTRY.md", "ldvh-maintainer-entry", ["specs/04-Code确定性执行规范.md"]),
    ):
        write_md(
            rules / filename,
            f"""
# {asset_id}

```yaml
ldvh_asset:
  id: "{asset_id}"
  type: "rule"
  status: "active"
  canonical_path: "rules/{filename}"
  source_specs:
{chr(10).join(f'    - "{item}"' for item in source_specs)}
  consumption_scenarios:
    - "测试"
  inputs:
    - "测试"
  outputs:
    - "测试"
  handoff: "测试"
  verification:
    - "pytest"
  sync_triggers:
    - "测试"
  deprecation: "测试"
```

## 1. 最小启动顺序

先查询知识地图。

## 2. 场景路由

按任务路由。

## 3. STOP 点

命中职责边界、环境入口、入口冲突或高影响修改时暂停。

## 4. 维护规则

修改后验证。
""",
        )


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
    assert report["metadata"]["degraded"] is False
    assert "basis" in edge_types
    assert "owns_attachment" in edge_types
    assert all(node.get("source_refs") for node in report["knowledge_map"]["nodes"])
    assert all(node.get("project_namespace") == "ldvh_self" for node in report["knowledge_map"]["nodes"])
    assert all(edge.get("source_refs") for edge in report["knowledge_map"]["edges"])
    assert all(edge.get("from") and edge.get("to") for edge in report["knowledge_map"]["edges"])
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


def test_v2_check_treats_root_20_to_59_files_as_member_specs(tmp_path):
    specs_v2 = tmp_path / "specs-v2"
    write_md(
        specs_v2 / "20-Spark-火花.md",
        """
# Spark-火花

```yaml
v2_spec:
  spec_id: "20"
  spec_kind: "member_spec"
  title: "Spark-火花"
  status: "draft"
  authority: "not_active_until_human_approved"
  canonical_path: "specs-v2/20-Spark-火花.md"
  created: "2026-06-23"
  updated: "2026-06-23"
  parent_spec: "specs-v2/02-事实模型基础规范.md"
  relation: "fact_model_member"
  positioning: "定义 Spark 事实模型成员"
  scope: "v2"
  basis: []
  related_specs: []
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "fact_model_member_identity"
  migration_status: "partially_migrated"
```

```yaml
v2_fact_model_member:
  spec_id: "20"
  kind: "fact_model"
  name_en: "Spark"
  name_zh: "火花"
  collection_status: "active"
  canonical_path: "specs-v2/20-Spark-火花.md"
  instance_root: "ldvh-base/sparks/"
  instance_carrier: "yaml"
  fact_source_anchor: "§5"
  schema_anchor: "§9"
  state_machine_anchor: "§6"
  human_gate_anchor: "§8"
  code_consumption:
    - "fields"
```

## 1. 本文解决的问题

定义成员。

## 2. 上位依据

承接 02。

## 3. 构成要素归属与价值判断

属于事实模型。

## 4. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 成员身份要求 | 需要成员身份块 | Code 校验 | 事实模型治理 | 修改时 |

## 5. Human Gate

改变成员身份时暂停。

## 6. 待补齐事项

无。
""",
    )

    report = checker.v2_check_build(tmp_path)
    docs = {doc["path"]: doc for doc in report["docs"]}

    assert docs["specs-v2/20-Spark-火花.md"]["doc_type"] == "member_spec"
    assert docs["specs-v2/20-Spark-火花.md"]["v2_fact_model_member"]["spec_id"] == "20"
    assert not report["diagnostics"]


def test_v2_core_implementation_lives_in_spec_checks():
    assert checker.v2_checks is v2_checks
    assert v2_checks.v2_check_build.__module__ == "spec_checks.v2"
    assert v2_checks.KnowledgeMapMixin is knowledge_map_checks.KnowledgeMapMixin
    assert knowledge_map_checks.KnowledgeMapMixin.project_knowledge_map.__module__ == "spec_checks.knowledge_map"


def test_v2_check_neighbors_layer_uses_start_node(tmp_path):
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

## 4. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 需要承接 01 | 人工降级检查 | 规范治理 | 修改时 |

## 5. Human Gate

改变附件授权时暂停。

## 6. 待补齐事项

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

    report = checker.v2_check_build(
        tmp_path,
        query_layer="neighbors",
        start_node="specs-v2/01-规范体系基础规范.md",
    )
    node_ids = {node["id"] for node in report["knowledge_map"]["nodes"]}
    edge_types = {edge["type"] for edge in report["knowledge_map"]["edges"]}

    assert report["knowledge_map"]["query"]["layer"] == "neighbors"
    assert "specs-v2/01-规范体系基础规范.md" in node_ids
    assert "specs-v2/01.Att.01-知识地图关系类型表.md" in node_ids
    assert {"related", "owns_attachment"} & edge_types
    assert not report["diagnostics"]


def test_knowledge_map_real_doc_node_replaces_prior_reference_placeholder(tmp_path):
    specs_v2 = tmp_path / "specs-v2"
    write_md(
        specs_v2 / "06-运行时扩展规范.md",
        """
# 运行时扩展规范

```yaml
v2_spec:
  spec_id: "06"
  spec_kind: "spec"
  title: "运行时扩展规范"
  status: "active"
  authority: "active"
  canonical_path: "specs-v2/06-运行时扩展规范.md"
  created: "2026-06-23"
  updated: "2026-06-24"
  parent_spec: ""
  relation: ""
  positioning: "定义运行时扩展"
  scope: "v2"
  basis: []
  related_specs:
    - "specs-v2/30-rules-entry-sync-review-Rules入口同步审查.md"
  migration_sources: []
  active_fact_source:
    - "specs-v2/06-运行时扩展规范.md"
  code_consumption:
    - "v2_spec_metadata"
  migration_status: "migrated"
```

## 1. 本文解决的问题

定义运行时扩展。

## 2. 上位依据

承接 00。

## 3. 构成要素归属与价值判断

属于运行时扩展。

## 4. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 入口可见要求 | 需要定位 30 | Code 检查 | 运行时扩展 | 修改时 |

## 5. Human Gate

改变入口时暂停。

## 6. 待补齐事项

无。
""",
    )
    write_md(
        specs_v2 / "30-rules-entry-sync-review-Rules入口同步审查.md",
        """
# rules-entry-sync-review-Rules入口同步审查

```yaml
v2_spec:
  spec_id: "30"
  spec_kind: "member_spec"
  title: "rules-entry-sync-review-Rules入口同步审查"
  status: "active"
  authority: "active"
  canonical_path: "specs-v2/30-rules-entry-sync-review-Rules入口同步审查.md"
  created: "2026-06-24"
  updated: "2026-06-24"
  parent_spec: "specs-v2/03-行动编排规范.md"
  relation: "action_member"
  positioning: "定义 Rules 同步审查"
  scope: "v2"
  basis: []
  related_specs: []
  migration_sources: []
  active_fact_source:
    - "specs-v2/30-rules-entry-sync-review-Rules入口同步审查.md"
  code_consumption:
    - "action_member_identity"
  migration_status: "not_applicable"
```

```yaml
v2_action_member:
  spec_id: "30"
  kind: "action_process"
  name_en: "rules-entry-sync-review"
  name_zh: "Rules入口同步审查"
  collection_status: "active"
  canonical_path: "specs-v2/30-rules-entry-sync-review-Rules入口同步审查.md"
  scenario_anchor: "§8"
  context_anchor: "§7"
  gate_anchor: "§11"
  execution_anchor: "§9"
  issue_routing_anchor: "§10"
  writeback_anchor: "§14"
  evidence_anchor: "§14"
  testability_anchor: "§16"
  assurance_takeover: []
  capability_assets: []
  code_consumption:
    - "action_member_identity"
```

## 1. 本文解决的问题

定义 Rules 同步审查。

## 2. 上位依据

承接 03。

## 3. 构成要素归属与价值判断

属于行动编排。

## 4. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 入口可见要求 | 需要同步 Rules | 本文 | 行动实践关联 | 修改时 |

## 5. Human Gate

改变成员状态时暂停。

## 6. 待补齐事项

无。
""",
    )

    report = checker.v2_check_build(
        tmp_path,
        query_layer="neighbors",
        start_node="specs-v2/30-rules-entry-sync-review-Rules入口同步审查.md",
    )
    nodes = {node["id"]: node for node in report["knowledge_map"]["nodes"]}
    node = nodes["specs-v2/30-rules-entry-sync-review-Rules入口同步审查.md"]

    assert node["type"] == "member_spec"
    assert node["status"] == "active"
    assert node["authority"] == "active"


def test_v2_check_reports_degraded_when_governed_projects_config_is_missing(tmp_path):
    (tmp_path / "specs-v2").mkdir()

    report = checker.v2_check_build(tmp_path, input_scope="all", project_scope="all_governed_projects")
    codes = {item["code"] for item in report["diagnostics"]}
    excluded = {item["input"]: item["diagnostic"] for item in report["knowledge_map"]["excluded_inputs"]}

    assert report["metadata"]["degraded"] is True
    assert report["knowledge_map"]["query"]["degraded"] is True
    assert "V2_HISTORY_SPECS_V1_GRAPH_NOT_IMPLEMENTED" in codes
    assert "V2_GOVERNED_PROJECTS_CONFIG_MISSING" in codes
    assert excluded["history_specs_v1"] == "V2_HISTORY_SPECS_V1_GRAPH_NOT_IMPLEMENTED"


def test_v2_check_governed_projects_projects_namespaced_fact_nodes(tmp_path):
    workspace = tmp_path / "workspace"
    project_a = workspace / "project-a"
    project_b = workspace / "project-b"
    write_md(
        workspace / "LDVH-GOVERNED-PROJECTS.yaml",
        f"""
product_name: Test LDVH
product_description: Test workspace
projects:
  - id: project-a
    path: {project_a}
    name: Project A
  - id: project-b
    path: {project_b}
    name: Project B
""",
    )
    write_md(
        project_a / "ldvh-base" / "sparks" / "spark-0001-alpha.yaml",
        """
id: spark-0001
type: spark
title: Alpha
status: pending
created: '2026-06-23'
updated: '2026-06-23'
description: Alpha
source: conversation
priority: P1
related_studies:
  - study-0001
""",
    )
    write_md(
        project_a / "ldvh-base" / "studies" / "study-0001-alpha.md",
        """
---
id: study-0001
type: study
title: Alpha Study
status: active
created: '2026-06-23'
updated: '2026-06-23'
summary: Alpha
input_refs:
  - spark-0001
related_sparks:
  - spark-0001
related_docs:
  - docs/alpha.md
---
# Alpha Study
""",
    )
    write_md(
        project_b / "ldvh-base" / "sparks" / "spark-0001-beta.yaml",
        """
id: spark-0001
type: spark
title: Beta
status: pending
created: '2026-06-23'
updated: '2026-06-23'
description: Beta
source: conversation
priority: P1
""",
    )

    report = checker.v2_check_build(project_a, input_scope="governed_projects", project_scope="all_governed_projects")
    nodes = {node["id"]: node for node in report["knowledge_map"]["nodes"]}
    edges = {(edge["from"], edge["to"], edge["type"]) for edge in report["knowledge_map"]["edges"]}

    assert "project-a:spark:spark-0001" in nodes
    assert "project-b:spark:spark-0001" in nodes
    assert nodes["project-a:spark:spark-0001"]["project_namespace"] == "project-a"
    assert nodes["project-b:spark:spark-0001"]["project_namespace"] == "project-b"
    assert ("project-a:spark:spark-0001", "project-a:study:study-0001", "related") in edges
    assert report["knowledge_map"]["impact_summary"]["omitted_semantic_relation_type_counts"]["consumes"] >= 1
    assert any(item["code"] == "KG_FACT_RELATION_DUPLICATED_AS_RELATED" for item in report["review_hints"])
    assert report["knowledge_map"]["excluded_inputs"] == []

    focused_report = checker.v2_check_build(
        project_a,
        input_scope="governed_projects",
        project_scope="all_governed_projects",
        query_layer="raw",
        start_node="project-a:study:study-0001",
    )
    focused_edges = {(edge["from"], edge["to"], edge["type"]) for edge in focused_report["knowledge_map"]["edges"]}
    focused_edge_payloads = focused_report["knowledge_map"]["edges"]
    assert ("project-a:study:study-0001", "project-a:spark:spark-0001", "consumes") in focused_edges
    assert any(
        edge["from"] == "project-a:study:study-0001"
        and edge["to"] == "project-a:spark:spark-0001"
        and edge["type"] == "consumes"
        and edge["project_namespace"] == "project-a"
        for edge in focused_edge_payloads
    )
    assert focused_report["knowledge_map"]["impact_summary"]["semantic_relation_type_counts"]["consumes"] >= 1
    assert any(item["code"] == "KG_FACT_RELATION_ONLY_RELATED" for item in focused_report["review_hints"])

    neighbors_report = checker.v2_check_build(
        project_a,
        input_scope="governed_projects",
        project_scope="all_governed_projects",
        query_layer="neighbors",
        start_node="project-a:study:study-0001",
    )
    neighbors_edges = {(edge["from"], edge["to"], edge["type"]) for edge in neighbors_report["knowledge_map"]["edges"]}
    assert ("project-a:study:study-0001", "project-a:spark:spark-0001", "consumes") in neighbors_edges


def test_v2_check_history_specs_v1_scope_is_degraded_without_active_parse(tmp_path):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    report = checker.v2_check_build(tmp_path, input_scope="history_specs_v1")
    codes = {item["code"] for item in report["diagnostics"]}
    excluded = {item["input"]: item for item in report["knowledge_map"]["excluded_inputs"]}

    assert report["metadata"]["degraded"] is True
    assert report["metadata"]["effective_input_scope"] == []
    assert report["docs"] == []
    assert report["knowledge_map"]["nodes"] == []
    assert report["knowledge_map"]["degraded"] is True
    assert "V2_HISTORY_SPECS_V1_GRAPH_NOT_IMPLEMENTED" in codes
    assert excluded["history_specs_v1"]["diagnostic"] == "V2_HISTORY_SPECS_V1_GRAPH_NOT_IMPLEMENTED"


def test_v2_check_runtime_extensions_scope_projects_fixed_asset_nodes(tmp_path):
    write_md(
        tmp_path / "rules" / "LDVH-MAINTAINER-ENTRY.md",
        """
# LDVH 维护入口

```yaml
ldvh_asset:
  id: "ldvh-maintainer-entry"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-MAINTAINER-ENTRY.md"
  source_specs:
    - "specs/01-规范体系基础规范.md"
    - "specs/06-运行时扩展规范.md"
  consumption_scenarios:
    - "测试场景"
  inputs:
    - "测试输入"
  outputs:
    - "测试输出"
  handoff: "测试交还"
  verification:
    - "python3 code/specs_validate.py deployment-entries"
  sync_triggers:
    - "source_specs 变化"
  deprecation: "测试废弃规则"
```
""",
    )

    report = checker.v2_check_build(tmp_path, input_scope="runtime_extensions")
    nodes = {node["id"]: node for node in report["knowledge_map"]["nodes"]}
    edge_pairs = {(edge["from"], edge["to"], edge["type"]) for edge in report["knowledge_map"]["edges"]}

    assert report["metadata"]["effective_input_scope"] == ["runtime_extensions"]
    assert report["docs"] == []
    assert nodes["rules/LDVH-MAINTAINER-ENTRY.md"]["type"] == "runtime_extension"
    assert nodes["rules/LDVH-MAINTAINER-ENTRY.md"]["asset_type"] == "rule"
    assert "specs/01-规范体系基础规范.md" in nodes["rules/LDVH-MAINTAINER-ENTRY.md"]["source_specs"]
    assert ("rules/LDVH-MAINTAINER-ENTRY.md", "specs/01-规范体系基础规范.md", "derives_from") in edge_pairs
    assert report["knowledge_map"]["excluded_inputs"] == []


def test_v2_check_json_and_text_output_shape_are_stable(tmp_path, capsys):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    exit_code = checker.v2_check_main(tmp_path, output_format="json")
    json_output = capsys.readouterr().out
    report = json.loads(json_output)

    assert exit_code == 0
    assert set(report) == {
        "metadata",
        "docs",
        "sections",
        "relations",
        "knowledge_map",
        "diagnostics",
        "review_hints",
    }
    assert report["metadata"]["tool"] == "code/specs_validate.py v2-check"
    assert report["metadata"]["read_only"] is True
    assert report["metadata"]["knowledge_map_boundary"] == "read_only_projection_not_fact_source"
    assert report["metadata"]["input_scope"] == "active_specs"
    assert report["metadata"]["effective_input_scope"] == ["active_specs"]
    assert report["knowledge_map"]["schema_version"] == "04.Att.06.v1"
    assert report["knowledge_map"]["generated_at"] == report["metadata"]["generated_at"]
    assert report["knowledge_map"]["tool"] == report["metadata"]["tool"]
    assert report["knowledge_map"]["input_scope"] == "active_specs"
    assert report["knowledge_map"]["degraded"] is False
    assert report["knowledge_map"]["diagnostics"] == []
    assert report["knowledge_map"]["source_refs"]
    assert report["knowledge_map"]["query"]["layer"] == "entry"
    assert report["knowledge_map"]["project_namespace"] == "ldvh_self"
    assert report["knowledge_map"]["excluded_inputs"] == []
    assert {"navigation", "read_plan", "next_queries", "stop_conditions", "impact_summary"} <= set(report["knowledge_map"])
    assert report["knowledge_map"]["navigation"]["task_type"] == "general"
    assert report["knowledge_map"]["read_plan"]
    assert report["diagnostics"] == []
    assert all(
        {"id", "type", "label", "canonical_path", "source_refs", "project_namespace", "status", "authority"} <= set(node)
        for node in report["knowledge_map"]["nodes"]
    )
    assert all(
        {"id", "type", "from", "to", "source_refs", "direction", "derived_from"} <= set(edge)
        for edge in report["knowledge_map"]["edges"]
    )

    exit_code = checker.v2_check_main(tmp_path, output_format="text")
    text_output = capsys.readouterr().out

    assert exit_code == 0
    assert "active specs 规范诊断完成" in text_output
    assert "- input_scope: active_specs" in text_output
    assert "- layer: entry" in text_output
    assert "- read_plan:" in text_output
    assert "Navigation:" in text_output
    assert "Read plan:" in text_output
    assert "Next queries:" in text_output
    assert "Stop conditions:" in text_output
    assert "Impact summary:" in text_output
    assert "suggested_sections:" in text_output
    assert "- degraded: False" in text_output
    assert "- diagnostics: 0" in text_output


def test_knowledge_map_text_output_includes_suggested_sections(tmp_path, capsys):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    exit_code = checker.knowledge_map_main(
        tmp_path,
        input_scope="active_specs",
        query_layer="neighbors",
        start_node="specs-v2/01-规范体系基础规范.md",
        output_format="text",
    )
    text_output = capsys.readouterr().out

    assert exit_code == 0
    assert "- P0/start:" in text_output
    assert 'suggested_sections: ["本文解决的问题", "构成要素归属与价值判断", "待补齐事项"]' in text_output


def test_knowledge_map_stop_conditions_include_task_level_human_gates(tmp_path):
    write_navigation_value_fixture(tmp_path)

    workspace_report = checker.v2_check_build(
        tmp_path,
        input_scope="entry_navigation",
        query_layer="neighbors",
        start_node="rules/LDVH-WORKSPACE-ENTRY.md",
        task_type="workspace_entry",
    )
    workspace_stops = {item["condition"]: item for item in workspace_report["knowledge_map"]["stop_conditions"]}

    assert "workspace_entry_stop_points" in workspace_stops
    assert workspace_stops["workspace_entry_stop_points"]["source_refs"]

    maintainer_report = checker.v2_check_build(
        tmp_path,
        input_scope="entry_navigation",
        query_layer="neighbors",
        start_node="rules/LDVH-MAINTAINER-ENTRY.md",
        task_type="rules_entry",
    )
    maintainer_stops = {item["condition"]: item for item in maintainer_report["knowledge_map"]["stop_conditions"]}

    assert "maintainer_entry_stop_points" in maintainer_stops
    assert maintainer_stops["maintainer_entry_stop_points"]["source_refs"]

    code_report = checker.v2_check_build(
        tmp_path,
        input_scope="entry_navigation",
        query_layer="neighbors",
        start_node="specs/04-Code确定性执行规范.md",
        task_type="rules_sync_review",
    )
    code_stops = {item["condition"]: item for item in code_report["knowledge_map"]["stop_conditions"]}

    assert "rules_sync_review_human_gate" in code_stops
    assert "code_human_gate" in code_stops
    assert code_stops["rules_sync_review_human_gate"]["source_refs"]
    assert code_stops["code_human_gate"]["source_refs"]


def test_knowledge_map_read_plan_roles_are_refined_for_attachments(tmp_path):
    write_navigation_value_fixture(tmp_path)

    report = checker.v2_check_build(
        tmp_path,
        input_scope="entry_navigation",
        query_layer="neighbors",
        start_node="specs/04-Code确定性执行规范.md",
        task_type="rules_sync_review",
    )
    read_roles = {item["path"]: item["role"] for item in report["knowledge_map"]["read_plan"]}
    edge_pairs = {(edge["from"], edge["to"], edge["type"]) for edge in report["knowledge_map"]["edges"]}

    assert read_roles["specs/attachments/04.Att.05-知识地图输入范围表.md"] == "authority"
    assert read_roles["specs/attachments/04.Att.06-知识地图投影Schema表.md"] == "authority"
    assert read_roles["specs/attachments/04.Att.09-Code回归入口表.md"] == "verification"
    assert read_roles["specs/attachments/04.Att.01-Code需求记录字段表.md"] == "context"
    assert read_roles["specs/attachments/04.Att.03-Code结构化输出Schema表.md"] == "context"
    assert "authority" not in {
        read_roles["specs/attachments/04.Att.09-Code回归入口表.md"],
        read_roles["specs/attachments/04.Att.01-Code需求记录字段表.md"],
        read_roles["specs/attachments/04.Att.03-Code结构化输出Schema表.md"],
    }
    assert (
        "specs/attachments/04.Att.05-知识地图输入范围表.md",
        "specs/04-Code确定性执行规范.md",
        "parent",
    ) in edge_pairs
    assert (
        "specs/04-Code确定性执行规范.md",
        "specs/attachments/04.Att.05-知识地图输入范围表.md",
        "owns_attachment",
    ) in edge_pairs


def test_attachment_boundary_diagnostics_detect_hidden_main_spec(tmp_path):
    specs = tmp_path / "specs"
    attachments = specs / "attachments"
    write_md(
        specs / "01-规范体系基础规范.md",
        """
# 规范体系基础规范

```yaml
v2_spec:
  spec_id: "01"
  spec_kind: "spec"
  title: "规范体系基础规范"
  status: "active"
  authority: "active"
  canonical_path: "specs/01-规范体系基础规范.md"
  created: "2026-06-24"
  updated: "2026-06-24"
  parent_spec: ""
  relation: ""
  positioning: "定义规范体系"
  scope: "v2"
  basis: []
  related_specs:
    - "specs/attachments/01.Att.09-附件治理规则.md"
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "v2_spec_metadata"
  migration_status: "migrated"
```

## 1. 本文解决的问题

定义规范治理。

## 2. 上位依据

无。

## 3. 构成要素归属与价值判断

属于规范体系。

## 4. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 附件边界 | 附件不得成为隐性主规范 | Code | 规范治理 | 修改附件时 |

## 5. Human Gate

改变附件授权时暂停。

## 6. 待补齐事项

无。
""",
    )
    write_md(
        attachments / "01.Att.09-附件治理规则.md",
        """
# 附件治理规则

```yaml
v2_attachment:
  attachment_id: "01.Att.09"
  title: "附件治理规则"
  status: "active"
  authority: "active_with_parent_spec"
  parent_spec: "specs/01-规范体系基础规范.md"
  canonical_path: "specs/attachments/01.Att.09-附件治理规则.md"
  purpose: "错误地把附件写成规则入口"
  migration_sources: []
  code_consumption:
    - "attachment_boundary"
```

## 1. 定位

本文定义事实源边界和状态机。

## 2. Human Gate

附件自行设置 Gate。

## 3. 待补齐事项

无。
""",
    )

    report = checker.v2_check_build(tmp_path)
    diagnostic_codes = {item["code"] for item in report["diagnostics"]}
    hint_codes = {item["code"] for item in report["review_hints"]}

    assert "V2_ATTACHMENT_NAME_FORBIDDEN_TYPE" in diagnostic_codes
    assert "V2_ATTACHMENT_FORBIDDEN_SECTION" in diagnostic_codes
    assert "V2_ATTACHMENT_POSSIBLE_CORE_RULE_OVERREACH" in hint_codes


def test_v2_check_entry_navigation_resolves_workcase_start_node(tmp_path):
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    write_minimal_v2_knowledge_map_fixture(project)
    write_md(
        workspace / "LDVH-GOVERNED-PROJECTS.yaml",
        f"""
product_name: Test LDVH
product_description: Test workspace
projects:
  - id: project
    path: {project}
    name: Project
""",
    )
    write_md(
        project / "ldvh-base" / "workcases" / "workcase-0001-entry-navigation.yaml",
        """
id: workcase-0001
type: workcase
title: Entry Navigation
status: executing
created: '2026-06-24'
updated: '2026-06-24'
goal: Entry Navigation
priority: P1
description: Entry Navigation
success_criteria: Entry Navigation
source: conversation
orchestration:
  mode: sequential
  execution_items:
    - id: item-1
      title: Read specs
      role: specs
      mode: single
      input_refs:
        - specs-v2/01-规范体系基础规范.md
      expected_output: Read specs
      status: pending
""",
    )

    report = checker.v2_check_build(
        project,
        input_scope="entry_navigation",
        query_layer="neighbors",
        start_node="ldvh-base/workcases/workcase-0001-entry-navigation.yaml",
        task_type="workcase_execution",
    )
    knowledge_map = report["knowledge_map"]
    read_plan = knowledge_map["read_plan"]
    read_paths = {item["path"] for item in read_plan}
    priorities = {item["path"]: item["priority"] for item in read_plan}

    assert report["metadata"]["effective_input_scope"] == ["active_specs", "runtime_extensions", "governed_projects"]
    assert knowledge_map["query"]["resolved_start_node"] == "project:workcase:workcase-0001"
    assert knowledge_map["navigation"]["task_type"] == "workcase_execution"
    assert "ldvh-base/workcases/workcase-0001-entry-navigation.yaml" in read_paths
    assert "specs-v2/01-规范体系基础规范.md" in read_paths
    assert priorities["specs-v2/01-规范体系基础规范.md"] == "P1"
    assert not knowledge_map["diagnostics"]

    general_report = checker.v2_check_build(
        project,
        input_scope="entry_navigation",
        query_layer="neighbors",
        start_node="ldvh-base/workcases/workcase-0001-entry-navigation.yaml",
        task_type="general",
    )
    general_priorities = {item["path"]: item["priority"] for item in general_report["knowledge_map"]["read_plan"]}
    assert general_priorities["specs-v2/01-规范体系基础规范.md"] == "P2"

    title_report = checker.v2_check_build(
        project,
        input_scope="entry_navigation",
        query_layer="neighbors",
        start_node="Entry Navigation",
        task_type="workcase_execution",
    )
    assert title_report["knowledge_map"]["query"]["resolved_start_node"] == "project:workcase:workcase-0001"
    assert not title_report["knowledge_map"]["stop_conditions"]


def test_v2_check_relation_type_filter_limits_projected_edges(tmp_path):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    report = checker.v2_check_build(tmp_path, relation_types=["owns_attachment"])
    edges = report["knowledge_map"]["edges"]

    assert report["metadata"]["relation_types"] == ["owns_attachment"]
    assert report["knowledge_map"]["query"]["relation_types"] == ["owns_attachment"]
    assert edges
    assert {edge["type"] for edge in edges} == {"owns_attachment"}
    assert all(edge["derived_from"] for edge in edges)
    assert not report["diagnostics"]


def test_v2_check_raw_layer_returns_bounded_source_excerpts(tmp_path):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    report = checker.v2_check_build(
        tmp_path,
        query_layer="raw",
        start_node="specs-v2/01-规范体系基础规范.md",
        depth=1,
    )
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["metadata"]["degraded"] is False
    assert report["knowledge_map"]["query"]["layer"] == "raw"
    assert report["knowledge_map"]["query"]["degraded"] is False
    assert report["knowledge_map"]["degraded"] is False
    assert "V2_RAW_LAYER_NOT_IMPLEMENTED" not in codes
    assert report["knowledge_map"]["raw_content"]
    assert all("text" in item for item in report["knowledge_map"]["raw_content"])


def test_v2_check_neighbors_without_start_node_falls_back_to_entry(tmp_path):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    report = checker.v2_check_build(tmp_path, query_layer="neighbors")
    codes = {item["code"] for item in report["diagnostics"]}
    node_types = {node["type"] for node in report["knowledge_map"]["nodes"]}

    assert report["metadata"]["degraded"] is True
    assert "V2_QUERY_START_NODE_MISSING" in codes
    assert "section" not in node_types
    assert "code_consumption_category" not in node_types


def test_v2_check_neighbors_unknown_start_node_falls_back_to_entry(tmp_path):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    report = checker.v2_check_build(tmp_path, query_layer="neighbors", start_node="missing-node")
    codes = {item["code"] for item in report["diagnostics"]}
    node_ids = {node["id"] for node in report["knowledge_map"]["nodes"]}

    assert report["metadata"]["degraded"] is True
    assert "V2_QUERY_START_NODE_NOT_FOUND" in codes
    assert "specs-v2/00-LDVH理念与价值标准.md" in node_ids
    assert "specs-v2/01-规范体系基础规范.md" in node_ids


def test_v2_check_invalid_query_options_return_diagnostics_without_parsing_specs(tmp_path):
    report = checker.v2_check_build(
        tmp_path,
        input_scope="bad_scope",
        query_layer="bad_layer",
        project_scope="bad_project_scope",
    )
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["metadata"]["degraded"] is True
    assert report["metadata"]["effective_input_scope"] == []
    assert report["docs"] == []
    assert report["knowledge_map"]["nodes"] == []
    assert "V2_INPUT_SCOPE_INVALID" in codes
    assert "V2_QUERY_LAYER_INVALID" in codes
    assert "V2_PROJECT_SCOPE_INVALID" in codes


def test_v2_check_accepts_legacy_specs_v2_input_scope_alias(tmp_path):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    report = checker.v2_check_build(tmp_path, input_scope="specs_v2")

    assert report["metadata"]["input_scope"] == "specs_v2"
    assert report["metadata"]["effective_input_scope"] == ["active_specs"]
    assert report["knowledge_map"]["input_scope"] == "specs_v2"


def test_v2_check_script_fast_path_outputs_json(tmp_path):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "specs_validate.py"),
            "v2-check",
            "--root",
            str(tmp_path),
            "--format",
            "json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    report = json.loads(result.stdout)

    assert result.returncode == 0
    assert report["metadata"]["tool"] == "code/specs_validate.py v2-check"
    assert report["metadata"]["input_scope"] == "active_specs"
    assert report["knowledge_map"]["schema_version"] == "04.Att.06.v1"
    assert report["diagnostics"] == []
