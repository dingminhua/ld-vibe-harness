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


def test_v2_check_reports_degraded_for_unimplemented_scopes(tmp_path):
    (tmp_path / "specs-v2").mkdir()

    report = checker.v2_check_build(tmp_path, input_scope="all", project_scope="all_governed_projects")
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["metadata"]["degraded"] is True
    assert report["knowledge_map"]["query"]["degraded"] is True
    assert "V2_GOVERNED_PROJECT_GRAPH_NOT_IMPLEMENTED" in codes
    assert "V2_GIT_HISTORY_GRAPH_NOT_IMPLEMENTED" in codes
    assert "V2_PROJECT_SCOPE_NOT_IMPLEMENTED" in codes
