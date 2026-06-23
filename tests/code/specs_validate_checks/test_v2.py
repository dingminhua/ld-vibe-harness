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


def test_v2_check_reports_degraded_for_unimplemented_scopes(tmp_path):
    (tmp_path / "specs-v2").mkdir()

    report = checker.v2_check_build(tmp_path, input_scope="all", project_scope="all_governed_projects")
    codes = {item["code"] for item in report["diagnostics"]}
    excluded = {item["input"]: item["diagnostic"] for item in report["knowledge_map"]["excluded_inputs"]}

    assert report["metadata"]["degraded"] is True
    assert report["knowledge_map"]["query"]["degraded"] is True
    assert "V2_HISTORY_SPECS_V1_GRAPH_NOT_IMPLEMENTED" in codes
    assert "V2_GOVERNED_PROJECT_GRAPH_NOT_IMPLEMENTED" in codes
    assert "V2_GIT_HISTORY_GRAPH_NOT_IMPLEMENTED" in codes
    assert "V2_PROJECT_SCOPE_NOT_IMPLEMENTED" in codes
    assert excluded["history_specs_v1"] == "V2_HISTORY_SPECS_V1_GRAPH_NOT_IMPLEMENTED"
    assert excluded["governed_projects"] == "V2_GOVERNED_PROJECT_GRAPH_NOT_IMPLEMENTED"
    assert excluded["git_history"] == "V2_GIT_HISTORY_GRAPH_NOT_IMPLEMENTED"


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
    assert report["metadata"]["input_scope"] == "specs_v2"
    assert report["metadata"]["effective_input_scope"] == ["specs_v2"]
    assert report["knowledge_map"]["schema_version"] == "04.Att.06.v1"
    assert report["knowledge_map"]["generated_at"] == report["metadata"]["generated_at"]
    assert report["knowledge_map"]["tool"] == report["metadata"]["tool"]
    assert report["knowledge_map"]["input_scope"] == "specs_v2"
    assert report["knowledge_map"]["degraded"] is False
    assert report["knowledge_map"]["diagnostics"] == []
    assert report["knowledge_map"]["source_refs"]
    assert report["knowledge_map"]["query"]["layer"] == "entry"
    assert report["knowledge_map"]["project_namespace"] == "ldvh_self"
    assert report["knowledge_map"]["excluded_inputs"] == []
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
    assert "v2 active 规范诊断完成" in text_output
    assert "- input_scope: specs_v2" in text_output
    assert "- layer: entry" in text_output
    assert "- degraded: False" in text_output
    assert "- diagnostics: 0" in text_output


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


def test_v2_check_raw_layer_degrades_to_expand_projection(tmp_path):
    write_minimal_v2_knowledge_map_fixture(tmp_path)

    report = checker.v2_check_build(
        tmp_path,
        query_layer="raw",
        start_node="specs-v2/01-规范体系基础规范.md",
        depth=1,
    )
    codes = {item["code"] for item in report["diagnostics"]}
    excluded = {item["input"]: item for item in report["knowledge_map"]["excluded_inputs"]}

    assert report["metadata"]["degraded"] is True
    assert report["knowledge_map"]["query"]["layer"] == "raw"
    assert report["knowledge_map"]["query"]["degraded"] is True
    assert report["knowledge_map"]["degraded"] is True
    assert "V2_RAW_LAYER_NOT_IMPLEMENTED" in codes
    assert "V2_RAW_LAYER_NOT_IMPLEMENTED" in {item["code"] for item in report["knowledge_map"]["diagnostics"]}
    assert excluded["raw_content"]["diagnostic"] == "V2_RAW_LAYER_NOT_IMPLEMENTED"
    assert all("text" not in node for node in report["knowledge_map"]["nodes"])


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
    assert "V2_PROJECT_SCOPE_NOT_IMPLEMENTED" in codes


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
    assert report["metadata"]["input_scope"] == "specs_v2"
    assert report["knowledge_map"]["schema_version"] == "04.Att.06.v1"
    assert report["diagnostics"] == []
