"""Read-only knowledge-map projection helpers for specs diagnostics."""

import hashlib
import re
from pathlib import Path

import yaml


V2_DEFAULT_PROJECT_NAMESPACE = "ldvh_self"
V2_KNOWLEDGE_MAP_SCHEMA_VERSION = "04.Att.06.v1"
V2_KNOWLEDGE_MAP_TOOL = "code/specs_validate.py v2-check"
V2_DEGRADED_DIAGNOSTIC_CODES = {
    "V2_HISTORY_SPECS_V1_GRAPH_NOT_IMPLEMENTED",
    "V2_QUERY_START_NODE_MISSING",
    "V2_QUERY_START_NODE_NOT_FOUND",
    "V2_GOVERNED_PROJECTS_CONFIG_MISSING",
    "V2_GOVERNED_PROJECTS_CONFIG_INVALID",
    "V2_GOVERNED_PROJECT_NOT_FOUND",
    "V2_GOVERNED_PROJECT_LDVH_BASE_MISSING",
    "V2_PROJECT_FACT_GRAPH_LOAD_FAILED",
    "V2_PROJECT_FACT_GRAPH_TARGET_NOT_FOUND",
    "V2_PROJECT_PATH_OUT_OF_SCOPE",
    "V2_INPUT_SCOPE_INVALID",
    "V2_QUERY_LAYER_INVALID",
    "V2_PROJECT_SCOPE_INVALID",
}
V2_PATH_REF_RE = re.compile(r"`((?:specs-v2|specs|code|web|tests|rules|skills|agents|hooks)/[^`]+?)`")
V2_OBJECT_ID_RE = re.compile(r"^(workcase|adr|pitfall|spark|study)-\d{4}$")
V2_FACT_DIR_TO_TYPE = {
    "workcases": "workcase",
    "adrs": "adr",
    "pitfalls": "pitfall",
    "sparks": "spark",
    "studies": "study",
}
V2_FACT_RELATION_FIELD_PREFIXES = (
    ("related_", "related"),
    ("source_", "derives_from"),
)
V2_FACT_SEMANTIC_RELATION_TYPES = {"consumes", "validates", "impacts", "derives_from"}
V2_FACT_SEMANTIC_RELATION_FIELDS = {
    "input_refs",
    "depends_on",
    "blocked_by",
    "evidence_refs",
    "verification_refs",
    "resolved_to",
}


class KnowledgeMapMixin:
    def add_document_node(self, doc):
        meta = doc["spec"] or doc["attachment"] or {}
        node_type = doc["doc_type"]
        if node_type == "supporting_note":
            return
        self.add_node(
            doc["path"],
            {
                "type": node_type,
                "label": doc["title"],
                "path": doc["path"],
                "canonical_path": doc["path"],
                "line": doc["title_line"],
                "status": meta.get("status"),
                "authority": meta.get("authority"),
                "project_namespace": self.project_namespace,
                "source_refs": [self.source_ref(doc["path"], doc["title_line"])],
                "source": "markdown_file",
            },
        )

    def add_section_nodes(self, doc):
        if doc["doc_type"] == "supporting_note":
            return
        for section in doc["sections"]:
            if section["level"] != 2:
                continue
            section_id = f"{doc['path']}#§{section['number']}" if section["number"] else f"{doc['path']}#L{section['line']}"
            self.add_node(
                section_id,
                {
                    "type": "section",
                    "label": section["title_normalized"],
                    "path": doc["path"],
                    "canonical_path": doc["path"],
                    "line": section["line"],
                    "project_namespace": self.project_namespace,
                    "source_refs": [
                        self.source_ref(
                            doc["path"],
                            section["line"],
                            section["end_line"],
                            anchor=f"§{section['number']}" if section["number"] else None,
                        )
                    ],
                    "source": "markdown_heading",
                },
            )

    def add_relation_edges(self, doc, known_paths):
        if doc["doc_type"] == "supporting_note":
            return
        source = doc["path"]
        spec = doc["spec"] or {}
        attachment = doc["attachment"] or {}

        for field, relation_type in (
            ("basis", "basis"),
            ("related_specs", "related"),
            ("migration_sources", "derives_from"),
            ("active_fact_source", "derives_from"),
        ):
            for target in spec.get(field) or []:
                self.add_edge(source, target, relation_type, field, doc["spec_line"] or 1)

        for category in spec.get("code_consumption") or []:
            code_node = f"code_consumption:{category}"
            self.add_node(
                code_node,
                {
                    "type": "code_consumption_category",
                    "label": category,
                    "canonical_path": doc["path"],
                    "project_namespace": self.project_namespace,
                    "source_refs": [self.source_ref(doc["path"], doc["spec_line"] or 1, field="v2_spec.code_consumption")],
                    "source": "v2_spec.code_consumption",
                },
            )
            self.add_edge(code_node, source, "consumes", "code_consumption", doc["spec_line"] or 1, label=category)

        if attachment:
            parent = attachment.get("parent_spec")
            if parent:
                self.add_edge(source, parent, "parent", "parent_spec", doc["attachment_line"] or 1)
                self.add_edge(parent, source, "owns_attachment", "parent_spec", doc["attachment_line"] or 1)
            for target in attachment.get("migration_sources") or []:
                self.add_edge(source, target, "derives_from", "migration_sources", doc["attachment_line"] or 1)
            for category in attachment.get("code_consumption") or []:
                code_node = f"code_consumption:{category}"
                self.add_node(
                    code_node,
                    {
                        "type": "code_consumption_category",
                        "label": category,
                        "canonical_path": doc["path"],
                        "project_namespace": self.project_namespace,
                        "source_refs": [self.source_ref(doc["path"], doc["attachment_line"] or 1, field="v2_attachment.code_consumption")],
                        "source": "v2_attachment.code_consumption",
                    },
                )
                self.add_edge(code_node, source, "consumes", "code_consumption", doc["attachment_line"] or 1, label=category)

        for ref in sorted(set(V2_PATH_REF_RE.findall(doc["text"]))):
            relation_type = "related" if ref in known_paths else "derives_from"
            self.add_relation(source, ref, relation_type, "body_path_ref", self.find_text_line(doc["text"], ref))

    def add_edge(self, source, target, relation_type, source_structure, line, label=None):
        self.add_relation(source, target, relation_type, source_structure, line, label)
        self.ensure_reference_node(target, line)
        key = (source, target, relation_type, source_structure, label)
        if key in self.edge_keys:
            return
        self.edge_keys.add(key)
        edge_id = self.edge_id(source, target, relation_type, source_structure, label)
        self.edges.append(
            {
                "id": edge_id,
                "source": source,
                "target": target,
                "from": source,
                "to": target,
                "type": relation_type,
                "source_structure": source_structure,
                "direction": "A -> B",
                "derived_from": source_structure,
                "line": line,
                "project_namespace": self.edge_project_namespace(source, target),
                "source_refs": [self.edge_source_ref(source, target, line, source_structure)],
                **({"label": label} if label else {}),
            }
        )

    def add_relation(self, source, target, relation_type, source_structure, line, label=None):
        key = (source, target, relation_type, source_structure, label)
        if key in self.relation_keys:
            return
        self.relation_keys.add(key)
        self.relations.append(
            {
                "source": source,
                "target": target,
                "relation_type": relation_type,
                "source_structure": source_structure,
                "line": line,
                "source_refs": [self.edge_source_ref(source, target, line, source_structure)],
                **({"label": label} if label else {}),
            }
        )

    def add_node(self, node_id, payload):
        if node_id in self.node_ids:
            for node in self.nodes:
                if node.get("id") != node_id:
                    continue
                if self.should_replace_node(node, payload):
                    payload.setdefault("canonical_path", payload.get("path"))
                    payload.setdefault("project_namespace", self.project_namespace)
                    payload.setdefault("source_refs", [])
                    payload.setdefault("status", None)
                    payload.setdefault("authority", None)
                    node.clear()
                    node.update({"id": node_id, **payload})
            return
        self.node_ids.add(node_id)
        payload.setdefault("canonical_path", payload.get("path"))
        payload.setdefault("project_namespace", self.project_namespace)
        payload.setdefault("source_refs", [])
        payload.setdefault("status", None)
        payload.setdefault("authority", None)
        self.nodes.append({"id": node_id, **payload})

    def should_replace_node(self, existing, incoming):
        existing_type = existing.get("type")
        incoming_type = incoming.get("type")
        existing_source = existing.get("source")
        incoming_source = incoming.get("source")
        if existing_source == "relation_target" and incoming_source == "markdown_file":
            return True
        if existing_type in {"external_fact_source", "missing_reference"} and incoming_type not in {"external_fact_source", "missing_reference"}:
            return True
        return False

    def project_knowledge_map(self, generated_at=None):
        nodes_by_id = {node["id"]: node for node in self.nodes}
        edges = self.filtered_edges_by_relation(self.edges)
        layer = "expand" if self.query_layer == "raw" else self.query_layer

        resolved_start_id = None
        if layer == "entry":
            selected_nodes = {
                node["id"]
                for node in self.nodes
                if node.get("type") not in {"section", "code_consumption_category"}
            }
            selected_edges = [
                edge
                for edge in edges
                if edge.get("type") in {"basis", "related", "parent", "owns_attachment", "derives_from"}
                and (edge.get("from") in selected_nodes or edge.get("to") in selected_nodes)
            ]
            selected_nodes.update(self.edge_endpoint_ids(selected_edges))
        elif layer in {"neighbors", "expand"}:
            start_id = self.resolve_start_node(nodes_by_id)
            if not start_id:
                selected_nodes, selected_edges = self.entry_fallback(edges)
            else:
                resolved_start_id = start_id
                selected_nodes, selected_edges = self.traverse_edges(start_id, edges, 1 if layer == "neighbors" else self.depth)
        else:
            selected_nodes, selected_edges = self.entry_fallback(edges)

        projected_nodes = [nodes_by_id[node_id] for node_id in self.sorted_node_ids(selected_nodes) if node_id in nodes_by_id]
        read_plan = self.build_read_plan(projected_nodes, selected_edges, resolved_start_id)
        next_queries = self.build_next_queries(resolved_start_id)
        stop_conditions = self.build_stop_conditions(read_plan, resolved_start_id)
        impact_summary = self.build_impact_summary(projected_nodes, selected_edges, edges)
        source_refs = self.knowledge_map_source_refs(projected_nodes, selected_edges)
        projection = {
            "schema_version": V2_KNOWLEDGE_MAP_SCHEMA_VERSION,
            "generated_at": generated_at,
            "tool": V2_KNOWLEDGE_MAP_TOOL,
            "input_scope": self.input_scope,
            "degraded": self.is_degraded(),
            "diagnostics": list(self.diagnostics),
            "source_refs": source_refs,
            "query": {
                "input_scope": self.input_scope,
                "effective_input_scope": self.effective_input_scope(),
                "layer": self.query_layer,
                "project_scope": self.project_scope,
                "projects": self.projects,
                "start_node": self.start_node,
                "resolved_start_node": resolved_start_id,
                "task_type": self.task_type,
                "relation_types": sorted(self.relation_types),
                "depth": self.depth,
                "degraded": self.is_degraded(),
            },
            "navigation": self.build_navigation(resolved_start_id, read_plan),
            "read_plan": read_plan,
            "next_queries": next_queries,
            "stop_conditions": stop_conditions,
            "impact_summary": impact_summary,
            "project_namespace": self.project_namespace,
            "nodes": projected_nodes,
            "edges": selected_edges,
            "excluded_inputs": self.excluded_inputs(),
        }
        if self.query_layer == "raw":
            projection["raw_content"] = self.raw_content_for_projection(projected_nodes)
        return projection

    def build_navigation(self, resolved_start_id, read_plan):
        if resolved_start_id:
            summary = f"已围绕 {resolved_start_id} 生成任务导航读取计划。"
        elif self.start_node:
            summary = f"未定位起点 {self.start_node}，已退回入口视图并给出后续查询建议。"
        else:
            summary = "未提供 start_node，已生成入口层候选读取计划。"
        return {
            "task_type": self.task_type,
            "start_node": self.start_node,
            "resolved_start_node": resolved_start_id,
            "input_scope": self.input_scope,
            "effective_input_scope": self.effective_input_scope(),
            "layer": self.query_layer,
            "project_scope": self.project_scope,
            "degraded": self.is_degraded(),
            "summary": summary,
            "read_plan_count": len(read_plan),
        }

    def build_read_plan(self, nodes, edges, resolved_start_id):
        nodes_by_id = {node["id"]: node for node in nodes}
        plan = []
        if resolved_start_id and resolved_start_id in nodes_by_id:
            plan.append(self.read_plan_entry(nodes_by_id[resolved_start_id], "P0", "start", "self", "任务起点原文，先核对身份、状态、权威和目标。"))

        if resolved_start_id:
            directly_related = [
                edge for edge in edges if edge.get("from") == resolved_start_id or edge.get("to") == resolved_start_id
            ]
            for edge in directly_related:
                counterpart_id = edge.get("to") if edge.get("from") == resolved_start_id else edge.get("from")
                node = nodes_by_id.get(counterpart_id)
                if not node:
                    continue
                priority, role = self.read_role_for_relation(edge.get("type"), edge.get("source_structure"), node)
                reason = self.read_reason_for_relation(edge, resolved_start_id)
                plan.append(self.read_plan_entry(node, priority, role, edge.get("type") or "related", reason))
        else:
            for node in nodes:
                if len(plan) >= 12:
                    break
                if node.get("type") not in {"spec", "member_spec", "attachment", "runtime_extension", "fact_object"}:
                    continue
                priority = "P1" if node.get("type") in {"spec", "member_spec", "runtime_extension"} else "P2"
                plan.append(self.read_plan_entry(node, priority, "context", "entry_candidate", "入口层候选原文；需要具体判断时应以它作为 start_node 追加邻接查询。"))

        return self.compact_read_plan(plan)

    def read_role_for_relation(self, relation_type, source_structure, node=None):
        node = node or {}
        path = node.get("canonical_path") or node.get("path") or ""
        if (
            self.task_type in {"workcase_execution", "work_object"}
            and relation_type == "consumes"
            and isinstance(source_structure, str)
            and "execution_items" in source_structure
        ):
            if path.startswith(("specs/", "specs-v2/", "rules/")):
                return "P1", "authority"
            return "P1", "context"
        if self.task_type == "code_change" and path.startswith(("code/", "tests/")):
            return "P1", "context"
        if self.task_type == "code_change" and path.startswith(("specs/04-", "specs/08-", "specs/attachments/04.", "specs/attachments/08.")):
            return "P1", "authority"
        if source_structure in {"ldvh_asset.source_specs", "basis", "parent_spec"}:
            return "P1", "authority"
        if relation_type in {"basis", "parent", "derives_from", "gated_by"}:
            return "P1", "authority"
        if relation_type in {"impacts", "writes_to"}:
            return "P1", "impact"
        if relation_type in {"validates", "renders"}:
            return "P2", "verification"
        if relation_type in {"related", "owns_attachment", "consumes"}:
            return "P2", "context"
        return "P3", "context"

    def read_reason_for_relation(self, edge, resolved_start_id):
        relation_type = edge.get("type") or "related"
        source_structure = edge.get("source_structure") or edge.get("derived_from") or "relation"
        if source_structure == "ldvh_asset.source_specs":
            return "Rules 或运行时扩展的 source_specs 来源规范，判断入口表达时必须回读。"
        if relation_type in {"basis", "parent", "derives_from", "gated_by"}:
            return f"与起点 {resolved_start_id} 存在 {relation_type} 权威或来源关系，影响规则判断。"
        if relation_type in {"impacts", "writes_to"}:
            return f"与起点 {resolved_start_id} 存在 {relation_type} 影响关系，需评估同步或写入边界。"
        if relation_type in {"validates", "renders"}:
            return f"与起点 {resolved_start_id} 存在 {relation_type} 验证或展示关系，需用于验证计划。"
        return f"与起点 {resolved_start_id} 存在 {relation_type} 上下文关系，必要时回读确认。"

    def read_plan_entry(self, node, priority, role, source_relation, reason):
        path = node.get("canonical_path") or node.get("path") or node.get("id")
        return {
            "path": path,
            "node_id": node.get("id"),
            "title": node.get("label") or node.get("id"),
            "priority": priority,
            "role": role,
            "reason": reason,
            "source_relation": source_relation,
            "suggested_sections": self.suggested_sections_for_node(node, role),
            "project_namespace": node.get("project_namespace"),
            **({"object_id": node.get("object_id")} if node.get("object_id") else {}),
            "source_refs": node.get("source_refs") or [],
        }

    def suggested_sections_for_node(self, node, role):
        node_type = node.get("type")
        path = node.get("canonical_path") or node.get("path") or ""
        if node_type in {"spec", "member_spec"}:
            if role == "authority":
                return ["上位依据", "规范保障要求", "Human Gate"]
            return ["本文解决的问题", "构成要素归属与价值判断", "待补齐事项"]
        if node_type == "attachment":
            return ["定位", "目标字段", "任务导航字段", "待补齐事项"]
        if node_type == "runtime_extension" or path.startswith("rules/"):
            return ["最小启动顺序", "场景路由", "STOP 点", "维护规则"]
        if node_type == "fact_object":
            return ["goal", "success_criteria", "orchestration", "verification_evidence"]
        return []

    def compact_read_plan(self, plan):
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        best_by_key = {}
        for item in plan:
            path = item.get("path")
            node_id = item.get("node_id")
            if not path or not self.is_readable_plan_path(path, node_id):
                continue
            key = (path, node_id)
            existing = best_by_key.get(key)
            if existing and priority_order.get(existing.get("priority"), 9) <= priority_order.get(item.get("priority"), 9):
                continue
            best_by_key[key] = item
        return sorted(
            best_by_key.values(),
            key=lambda item: (
                priority_order.get(item.get("priority"), 9),
                str(item.get("path") or ""),
                str(item.get("node_id") or ""),
            ),
        )[:24]

    def is_readable_plan_path(self, path, node_id):
        if not isinstance(path, str) or not path:
            return False
        if path.startswith(("code_consumption:", "project:")):
            return False
        if node_id and isinstance(node_id, str) and node_id.startswith("code_consumption:"):
            return False
        return path.endswith((".md", ".yaml", ".yml", ".py", ".toml", ".json"))

    def build_next_queries(self, resolved_start_id):
        queries = []
        start = self.start_node or resolved_start_id
        if self.start_node and not resolved_start_id:
            queries.append(
                self.next_query(
                    "retry_with_entry_navigation",
                    self.start_node,
                    "entry_navigation",
                    "neighbors",
                    "当前输入范围未定位起点；入口导航组合范围可同时读取 active specs、runtime extensions 和 governed projects。",
                )
            )
        if start and self.input_scope != "entry_navigation" and self.start_node_needs_entry_navigation(start):
            queries.append(
                self.next_query(
                    "combine_entry_sources",
                    start,
                    "entry_navigation",
                    "neighbors",
                    "任务涉及 Rules 入口、工作对象或跨入口影响，需在同一任务视图中消费多类节点。",
                )
            )
        if resolved_start_id and self.query_layer == "neighbors":
            queries.append(
                self.next_query(
                    "expand_if_needed",
                    resolved_start_id,
                    self.input_scope,
                    "expand",
                    "一跳关系不足以判断影响面、验证链或关闭条件时再展开二跳。",
                    depth=2,
                )
            )
        if not self.start_node and self.query_layer == "entry":
            queries.append(
                {
                    "purpose": "choose_start_node",
                    "command": "python3 code/specs_validate.py knowledge-map --layer neighbors --start-node <path-or-node> --format json",
                    "input_scope": self.input_scope,
                    "layer": "neighbors",
                    "start_node": "<path-or-node>",
                    "reason": "入口层只用于选择起点；具体判断必须追加带 start_node 的任务导航查询。",
                }
            )
        return self.dedupe_next_queries(queries)

    def start_node_needs_entry_navigation(self, start):
        return isinstance(start, str) and (
            start.startswith(("rules/", "ldvh-base/"))
            or ":workcase:" in start
            or ":spark:" in start
            or ":adr:" in start
            or ":pitfall:" in start
            or ":study:" in start
        )

    def next_query(self, purpose, start_node, input_scope, layer, reason, depth=1):
        command = (
            "python3 code/specs_validate.py knowledge-map "
            f"--input-scope {input_scope} --layer {layer} --start-node {start_node} --format json"
        )
        if layer == "expand":
            command += f" --depth {depth}"
        return {
            "purpose": purpose,
            "command": command,
            "input_scope": input_scope,
            "layer": layer,
            "start_node": start_node,
            "reason": reason,
        }

    def dedupe_next_queries(self, queries):
        seen = set()
        result = []
        for query in queries:
            key = (query.get("purpose"), query.get("input_scope"), query.get("layer"), query.get("start_node"))
            if key in seen:
                continue
            seen.add(key)
            result.append(query)
        return result

    def build_stop_conditions(self, read_plan, resolved_start_id=None):
        conditions = []
        if self.is_degraded():
            conditions.append(
                {
                    "condition": "knowledge_map_degraded",
                    "reason": "知识地图查询已降级；不得把当前输出当作完整定位或影响判断。",
                    "fallback": "说明降级诊断，退回 active specs、Rules 入口、事实对象和 Git 文件事实源原文核对。",
                    "source_refs": self.diagnostic_source_refs(),
                }
            )
        if self.start_node and not self.read_plan_matches_start(read_plan, resolved_start_id):
            conditions.append(
                {
                    "condition": "start_node_not_in_read_plan",
                    "reason": "读取计划中没有命中用户给定起点；继续判断前必须重新选择 start_node 或扩大输入范围。",
                    "fallback": "优先尝试 --input-scope entry_navigation；仍失败时回到文件事实源和人工降级检查。",
                    "source_refs": self.diagnostic_source_refs(),
                }
            )
        if not read_plan:
            conditions.append(
                {
                    "condition": "empty_read_plan",
                    "reason": "当前查询未能生成可执行读取计划。",
                    "fallback": "提供明确 start_node，或使用 entry_navigation 组合范围后重试。",
                    "source_refs": self.diagnostic_source_refs(),
                }
            )
        return conditions

    def read_plan_matches_start(self, read_plan, resolved_start_id=None):
        expected = {value for value in (self.start_node, resolved_start_id) if value}
        for item in read_plan:
            if item.get("node_id") in expected or item.get("path") in expected or item.get("title") in expected:
                return True
        return False

    def diagnostic_source_refs(self):
        refs = []
        for diagnostic in self.diagnostics:
            refs.extend(diagnostic.get("source_refs") or [])
        return refs

    def build_impact_summary(self, nodes, edges, all_edges=None):
        node_type_counts = {}
        relation_type_counts = {}
        semantic_relation_type_counts = {}
        omitted_semantic_relation_type_counts = {}
        affected_specs = []
        affected_runtime_extensions = []
        affected_fact_objects = []
        projected_node_ids = {node.get("id") for node in nodes}
        selected_edge_ids = {edge.get("id") for edge in edges}
        for node in nodes:
            node_type = node.get("type") or "unknown"
            node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
            node_id = node.get("id")
            if node_type in {"spec", "member_spec", "attachment"}:
                affected_specs.append(node_id)
            elif node_type == "runtime_extension":
                affected_runtime_extensions.append(node_id)
            elif node_type == "fact_object":
                affected_fact_objects.append(node_id)
        for edge in edges:
            relation_type = edge.get("type") or "unknown"
            relation_type_counts[relation_type] = relation_type_counts.get(relation_type, 0) + 1
            if relation_type in V2_FACT_SEMANTIC_RELATION_TYPES:
                semantic_relation_type_counts[relation_type] = semantic_relation_type_counts.get(relation_type, 0) + 1
        for edge in all_edges or []:
            relation_type = edge.get("type") or "unknown"
            if relation_type not in V2_FACT_SEMANTIC_RELATION_TYPES or edge.get("id") in selected_edge_ids:
                continue
            if edge.get("from") in projected_node_ids or edge.get("to") in projected_node_ids:
                omitted_semantic_relation_type_counts[relation_type] = omitted_semantic_relation_type_counts.get(relation_type, 0) + 1
        return {
            "node_type_counts": node_type_counts,
            "relation_type_counts": relation_type_counts,
            "semantic_relation_type_counts": semantic_relation_type_counts,
            "omitted_semantic_relation_type_counts": omitted_semantic_relation_type_counts,
            "affected_specs": sorted(filter(None, affected_specs))[:40],
            "affected_runtime_extensions": sorted(filter(None, affected_runtime_extensions))[:40],
            "affected_fact_objects": sorted(filter(None, affected_fact_objects))[:40],
        }

    def knowledge_map_source_refs(self, nodes, edges):
        refs = []
        seen = set()
        for item in list(nodes) + list(edges) + list(self.diagnostics):
            for ref in item.get("source_refs") or []:
                key = tuple(sorted(ref.items()))
                if key in seen:
                    continue
                seen.add(key)
                refs.append(ref)
        return refs

    def filtered_edges_by_relation(self, edges):
        if not self.relation_types:
            return list(edges)
        return [edge for edge in edges if edge.get("type") in self.relation_types]

    def entry_fallback(self, edges):
        selected_nodes = {
            node["id"]
            for node in self.nodes
            if node.get("type") not in {"section", "code_consumption_category"}
        }
        selected_edges = [
            edge
            for edge in edges
            if edge.get("type") in {"basis", "related", "parent", "owns_attachment", "derives_from"}
            and (edge.get("from") in selected_nodes or edge.get("to") in selected_nodes)
        ]
        selected_nodes.update(self.edge_endpoint_ids(selected_edges))
        return selected_nodes, selected_edges

    def resolve_start_node(self, nodes_by_id):
        if not self.start_node:
            self.diagnostics.append(
                self.diagnostic(
                    "<runtime>",
                    1,
                    "warning",
                    "V2_QUERY_START_NODE_MISSING",
                    f"query_layer={self.query_layer} 需要 start_node；本次退回入口层",
                    suggested_owner="04-Code确定性执行规范",
                )
            )
            return None
        if self.start_node in nodes_by_id:
            return self.start_node
        matches = [
            node["id"]
            for node in self.nodes
            if node.get("path") == self.start_node
            or node.get("canonical_path") == self.start_node
            or node.get("label") == self.start_node
        ]
        if matches:
            return sorted(matches)[0]
        self.diagnostics.append(
            self.diagnostic(
                "<runtime>",
                1,
                "warning",
                "V2_QUERY_START_NODE_NOT_FOUND",
                f"未找到 start_node: {self.start_node}；本次退回入口层",
                suggested_owner="04-Code确定性执行规范",
            )
        )
        return None

    def traverse_edges(self, start_id, edges, depth):
        selected_nodes = {start_id}
        selected_edges = []
        frontier = {start_id}
        for _ in range(max(1, depth)):
            next_frontier = set()
            for edge in edges:
                from_id = edge.get("from")
                to_id = edge.get("to")
                if from_id in frontier or to_id in frontier:
                    selected_edges.append(edge)
                    if from_id:
                        next_frontier.add(from_id)
                    if to_id:
                        next_frontier.add(to_id)
            next_frontier -= selected_nodes
            selected_nodes.update(next_frontier)
            frontier = next_frontier
            if not frontier:
                break
        selected_nodes.update(self.edge_endpoint_ids(selected_edges))
        return selected_nodes, self.unique_edges(selected_edges)

    def edge_endpoint_ids(self, edges):
        endpoint_ids = set()
        for edge in edges:
            if edge.get("from"):
                endpoint_ids.add(edge["from"])
            if edge.get("to"):
                endpoint_ids.add(edge["to"])
        return endpoint_ids

    def unique_edges(self, edges):
        seen = set()
        result = []
        for edge in edges:
            key = edge.get("id")
            if key in seen:
                continue
            seen.add(key)
            result.append(edge)
        return result

    def sorted_node_ids(self, node_ids):
        order = {node["id"]: index for index, node in enumerate(self.nodes)}
        return sorted(node_ids, key=lambda node_id: order.get(node_id, len(order)))

    def excluded_inputs(self):
        excluded = []
        if self.input_scope in {"all", "history_specs_v1"}:
            excluded.append({"input": "history_specs_v1", "reason": "not_implemented", "diagnostic": "V2_HISTORY_SPECS_V1_GRAPH_NOT_IMPLEMENTED"})
        return excluded

    def raw_content_for_projection(self, nodes):
        items = []
        seen = set()
        for node in nodes:
            refs = node.get("source_refs") or []
            for ref in refs[:1]:
                path_value = ref.get("path")
                if not path_value:
                    continue
                path = self.resolve_source_path(path_value)
                key = (str(path), ref.get("line_start"), ref.get("line_end"))
                if key in seen or not path.exists() or not path.is_file():
                    continue
                seen.add(key)
                try:
                    lines = path.read_text(encoding="utf-8").splitlines()
                except OSError:
                    continue
                start = max(1, int(ref.get("line_start") or 1))
                end = max(start, int(ref.get("line_end") or start))
                end = min(end, start + 39, len(lines))
                excerpt = "\n".join(lines[start - 1 : end])
                items.append(
                    {
                        "node_id": node.get("id"),
                        "path": path_value,
                        "line_start": start,
                        "line_end": end,
                        "text": excerpt,
                    }
                )
        return items

    def resolve_source_path(self, path_value):
        path = Path(path_value)
        if path.is_absolute():
            return path
        return self.root / path

    def add_governed_project_graph(self):
        config_path = self.governed_projects_config_path()
        if not config_path:
            self.diagnostics.append(
                self.diagnostic(
                    "<workspace>",
                    1,
                    "warning",
                    "V2_GOVERNED_PROJECTS_CONFIG_MISSING",
                    "未找到 LDVH-GOVERNED-PROJECTS.yaml，无法生成管辖项目知识地图投影",
                    suggested_owner="06-运行时扩展规范",
                )
            )
            return
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            self.diagnostics.append(
                self.diagnostic(
                    str(config_path),
                    1,
                    "warning",
                    "V2_GOVERNED_PROJECTS_CONFIG_INVALID",
                    f"管辖项目配置无法解析: {exc}",
                    suggested_owner="06-运行时扩展规范",
                )
            )
            return
        projects = data.get("projects")
        if not isinstance(projects, list):
            self.diagnostics.append(
                self.diagnostic(
                    self.relative_or_absolute(config_path),
                    1,
                    "warning",
                    "V2_GOVERNED_PROJECTS_CONFIG_INVALID",
                    "管辖项目配置 projects 必须是列表",
                    suggested_owner="06-运行时扩展规范",
                )
            )
            return

        selected = self.select_governed_projects(projects)
        for project in selected:
            self.add_project_graph(project, config_path)

    def governed_projects_config_path(self):
        for candidate in (self.root / "LDVH-GOVERNED-PROJECTS.yaml", self.root.parent / "LDVH-GOVERNED-PROJECTS.yaml"):
            if candidate.exists():
                return candidate
        return None

    def select_governed_projects(self, projects):
        valid_projects = [project for project in projects if isinstance(project, dict) and project.get("id") and project.get("path")]
        if self.project_scope == "all_governed_projects":
            return valid_projects
        if self.project_scope == "explicit_projects":
            wanted = set(self.projects)
            selected = [project for project in valid_projects if project.get("id") in wanted]
            missing = sorted(wanted - {project.get("id") for project in selected})
            for project_id in missing:
                self.diagnostics.append(
                    self.diagnostic(
                        "<workspace>",
                        1,
                        "warning",
                        "V2_GOVERNED_PROJECT_NOT_FOUND",
                        f"未找到显式指定的管辖项目: {project_id}",
                        suggested_owner="06-运行时扩展规范",
                    )
                )
            return selected

        root = self.root.resolve()
        selected = []
        for project in valid_projects:
            try:
                project_root = Path(project["path"]).resolve()
            except OSError:
                continue
            if project_root == root:
                selected.append(project)
        if selected:
            return selected
        return valid_projects[:1] if len(valid_projects) == 1 else []

    def add_project_graph(self, project, config_path):
        project_id = str(project.get("id"))
        project_root = Path(project.get("path")).resolve()
        project_node_id = f"project:{project_id}"
        config_ref_path = self.relative_or_absolute(config_path)
        self.add_node(
            project_node_id,
            {
                "type": "governed_project",
                "label": project.get("name") or project_id,
                "path": str(project_root),
                "canonical_path": str(project_root),
                "line": 1,
                "status": "active",
                "authority": "LDVH-GOVERNED-PROJECTS.yaml",
                "project_namespace": project_id,
                "project_id": project_id,
                "source_refs": [self.source_ref(config_ref_path, 1, field=f"projects.{project_id}")],
                "source": "governed_projects_config",
            },
        )
        ldvh_base = project_root / "ldvh-base"
        if not ldvh_base.exists():
            self.diagnostics.append(
                self.diagnostic(
                    str(ldvh_base),
                    1,
                    "warning",
                    "V2_GOVERNED_PROJECT_LDVH_BASE_MISSING",
                    f"管辖项目缺少 ldvh-base: {project_id}",
                    suggested_owner="02-事实模型基础规范",
                )
            )
            return

        records = []
        object_index = {}
        for directory_name, object_type in V2_FACT_DIR_TO_TYPE.items():
            directory = ldvh_base / directory_name
            if not directory.exists():
                continue
            suffix = ".md" if object_type == "study" else ".yaml"
            for path in sorted(directory.glob(f"{object_type}-*{suffix}")):
                record = self.load_fact_record(project_id, project_root, object_type, path)
                if not record:
                    continue
                records.append(record)
                object_index[record["object_id"]] = record

        for record in records:
            self.add_fact_node(record)
            self.add_edge(project_node_id, record["node_id"], "related", "governed_project.ldvh_base", 1)
        for record in records:
            self.add_fact_edges(record, object_index, project_root)
            self.add_fact_relation_quality_hints(record)

    def load_fact_record(self, project_id, project_root, object_type, path):
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".md":
                if not text.startswith("---\n"):
                    raise ValueError("Study Markdown 缺少 YAML frontmatter")
                end = text.find("\n---", 4)
                if end == -1:
                    raise ValueError("Study Markdown 缺少 frontmatter 结束标记")
                data = yaml.safe_load(text[4:end]) or {}
            else:
                data = yaml.safe_load(text) or {}
        except (OSError, yaml.YAMLError, ValueError) as exc:
            self.diagnostics.append(
                self.diagnostic(
                    self.project_relative_or_absolute(project_root, path),
                    1,
                    "warning",
                    "V2_PROJECT_FACT_GRAPH_LOAD_FAILED",
                    f"事实对象无法解析为知识地图节点: {exc}",
                    suggested_owner="02-事实模型基础规范",
                )
            )
            return None
        if not isinstance(data, dict):
            return None
        object_id = data.get("id")
        if not isinstance(object_id, str) or not object_id:
            return None
        object_type = str(data.get("type") or object_type)
        node_id = f"{project_id}:{object_type}:{object_id}"
        return {
            "project_id": project_id,
            "project_root": project_root,
            "object_type": object_type,
            "object_id": object_id,
            "node_id": node_id,
            "path": path,
            "relative_path": self.project_relative_or_absolute(project_root, path),
            "data": data,
            "text": text,
        }

    def add_fact_node(self, record):
        data = record["data"]
        self.add_node(
            record["node_id"],
            {
                "type": "fact_object",
                "object_type": record["object_type"],
                "object_id": record["object_id"],
                "label": data.get("title") or record["object_id"],
                "path": record["relative_path"],
                "canonical_path": record["relative_path"],
                "line": 1,
                "status": data.get("status"),
                "authority": "ldvh-base",
                "project_namespace": record["project_id"],
                "project_id": record["project_id"],
                "source_refs": [self.source_ref(record["relative_path"], 1, object_id=record["object_id"])],
                "source": "ldvh_base_fact_object",
            },
        )

    def add_fact_edges(self, record, object_index, project_root):
        data = record["data"]
        for field, value in data.items():
            if field in {"source", "source_detail"}:
                continue
            relation_type = None
            for prefix, mapped_relation in V2_FACT_RELATION_FIELD_PREFIXES:
                if field.startswith(prefix):
                    relation_type = mapped_relation
                    break
            if field in {"input_refs", "depends_on", "blocked_by"}:
                relation_type = "consumes"
            if field in {"evidence_refs", "verification_refs"}:
                relation_type = "validates"
            if field == "resolved_to":
                relation_type = "impacts"
            if relation_type:
                self.add_fact_relation_values(record, object_index, project_root, field, value, relation_type)
            if field == "execution_items" and isinstance(value, list):
                for index, item in enumerate(value):
                    if not isinstance(item, dict):
                        continue
                    self.add_fact_relation_values(record, object_index, project_root, f"execution_items[{index}].input_refs", item.get("input_refs"), "consumes")
                    self.add_fact_relation_values(record, object_index, project_root, f"execution_items[{index}].evidence_refs", item.get("evidence_refs"), "validates")
            if field == "orchestration" and isinstance(value, dict):
                execution_items = value.get("execution_items")
                if isinstance(execution_items, list):
                    for index, item in enumerate(execution_items):
                        if not isinstance(item, dict):
                            continue
                        self.add_fact_relation_values(record, object_index, project_root, f"orchestration.execution_items[{index}].input_refs", item.get("input_refs"), "consumes")
                        self.add_fact_relation_values(record, object_index, project_root, f"orchestration.execution_items[{index}].evidence_refs", item.get("evidence_refs"), "validates")

    def add_fact_relation_quality_hints(self, record):
        data = record["data"]
        related_targets = self.fact_targets_by_field(data, lambda field: field.startswith("related_"))
        semantic_targets = self.fact_targets_by_field(
            data,
            lambda field: field.startswith("source_") or field in V2_FACT_SEMANTIC_RELATION_FIELDS,
        )
        semantic_target_ids = set(semantic_targets)
        for target in sorted(set(related_targets) & set(semantic_targets)):
            related_fields = sorted(related_targets[target])
            semantic_fields = sorted(semantic_targets[target])
            line = self.find_text_line(record["text"], related_fields[0])
            self.review_hints.append(
                self.diagnostic(
                    record["relative_path"],
                    line,
                    "info",
                    "KG_FACT_RELATION_DUPLICATED_AS_RELATED",
                    f"事实对象同时用弱关联字段 {', '.join(related_fields)} 和语义字段 {', '.join(semantic_fields)} 引用 {target}；如语义字段已表达真实消费、证据、来源或承接关系，应避免用 related_* 替代语义边。",
                    suggested_owner="01.Att.01-知识地图关系类型表",
                    source_refs=[self.source_ref(record["relative_path"], line, field=related_fields[0], object_id=record["object_id"])],
                )
            )
        if not self.review_only_related_hints_for_record(record):
            return
        for target in sorted(set(related_targets) - semantic_target_ids):
            related_fields = sorted(related_targets[target])
            line = self.find_text_line(record["text"], related_fields[0])
            self.review_hints.append(
                self.diagnostic(
                    record["relative_path"],
                    line,
                    "info",
                    "KG_FACT_RELATION_ONLY_RELATED",
                    f"事实对象仅通过弱关联字段 {', '.join(related_fields)} 引用 {target}；若它实际表达输入、依赖、证据、来源或承接关系，应改用对应语义字段，不能用 related_* 替代。",
                    suggested_owner="01.Att.01-知识地图关系类型表",
                    source_refs=[self.source_ref(record["relative_path"], line, field=related_fields[0], object_id=record["object_id"])],
                )
            )

    def review_only_related_hints_for_record(self, record):
        if not self.start_node:
            return False
        return self.start_node in {record["node_id"], record["relative_path"], record["object_id"]}

    def fact_targets_by_field(self, data, field_predicate):
        targets = {}
        for field, value in data.items():
            if not field_predicate(field):
                continue
            for raw_target in value if isinstance(value, list) else [value]:
                target = self.normalize_fact_target(raw_target)
                if target:
                    targets.setdefault(target, set()).add(field)
        return targets

    def add_fact_relation_values(self, record, object_index, project_root, field, value, relation_type):
        values = value if isinstance(value, list) else [value]
        for raw_target in values:
            target = self.normalize_fact_target(raw_target)
            if not target:
                continue
            target_node = self.resolve_fact_target(record, object_index, project_root, target, field)
            line = self.find_text_line(record["text"], field.split("[")[0])
            self.add_edge(record["node_id"], target_node, relation_type, field, line)

    def normalize_fact_target(self, raw_target):
        if raw_target is None:
            return None
        if isinstance(raw_target, str):
            value = raw_target.strip()
            if not value:
                return None
            if V2_OBJECT_ID_RE.match(value) or "/" in value or value.endswith((".md", ".yaml", ".yml")):
                return value
            return None
        if isinstance(raw_target, dict):
            target_type = raw_target.get("type")
            target_id = raw_target.get("id")
            if target_type and target_id:
                return f"{target_type}:{target_id}"
            if raw_target.get("path"):
                return str(raw_target.get("path"))
        return None

    def resolve_fact_target(self, record, object_index, project_root, target, field):
        project_id = record["project_id"]
        target_id = target.split(":", 1)[1] if ":" in target and V2_OBJECT_ID_RE.match(target.split(":", 1)[1]) else target
        if V2_OBJECT_ID_RE.match(target_id) and target_id in object_index:
            return object_index[target_id]["node_id"]
        if V2_OBJECT_ID_RE.match(target_id):
            node_id = f"{project_id}:missing:{target_id}"
            self.add_missing_fact_target_node(node_id, target_id, record, field)
            return node_id

        path = Path(target)
        if not path.is_absolute():
            path = project_root / target
        try:
            resolved = path.resolve()
            resolved.relative_to(project_root)
        except ValueError:
            node_id = f"{project_id}:out_of_scope:{hashlib.sha1(target.encode('utf-8')).hexdigest()[:12]}"
            self.diagnostics.append(
                self.diagnostic(
                    record["relative_path"],
                    self.find_text_line(record["text"], field.split("[")[0]),
                    "warning",
                    "V2_PROJECT_PATH_OUT_OF_SCOPE",
                    f"事实对象字段 {field} 引用项目根目录外路径: {target}",
                    suggested_owner="07-事实源边界与Git追溯规范",
                )
            )
            self.add_node(
                node_id,
                {
                    "type": "missing_reference",
                    "label": target,
                    "path": target,
                    "canonical_path": target,
                    "line": 1,
                    "project_namespace": project_id,
                    "project_id": project_id,
                    "source_refs": [self.source_ref(record["relative_path"], self.find_text_line(record["text"], field.split("[")[0]), field=field, object_id=record["object_id"])],
                    "source": "ldvh_base_fact_reference",
                },
            )
            return node_id

        rel = self.project_relative_or_absolute(project_root, resolved)
        if rel in self.node_ids:
            return rel
        node_id = f"{project_id}:path:{rel}"
        node_type = "external_fact_source" if resolved.exists() else "missing_reference"
        if not resolved.exists():
            self.diagnostics.append(
                self.diagnostic(
                    record["relative_path"],
                    self.find_text_line(record["text"], field.split("[")[0]),
                    "warning",
                    "V2_PROJECT_FACT_GRAPH_TARGET_NOT_FOUND",
                    f"事实对象字段 {field} 引用目标不存在: {target}",
                    suggested_owner="02-事实模型基础规范",
                )
            )
        self.add_node(
            node_id,
            {
                "type": node_type,
                "label": target,
                "path": rel,
                "canonical_path": rel,
                "line": 1,
                "project_namespace": project_id,
                "project_id": project_id,
                "source_refs": [self.source_ref(record["relative_path"], self.find_text_line(record["text"], field.split("[")[0]), field=field, object_id=record["object_id"])],
                "source": "ldvh_base_fact_reference",
            },
        )
        return node_id

    def add_missing_fact_target_node(self, node_id, target_id, record, field):
        self.diagnostics.append(
            self.diagnostic(
                record["relative_path"],
                self.find_text_line(record["text"], field.split("[")[0]),
                "warning",
                "V2_PROJECT_FACT_GRAPH_TARGET_NOT_FOUND",
                f"事实对象字段 {field} 引用对象不存在: {target_id}",
                suggested_owner="02-事实模型基础规范",
            )
        )
        self.add_node(
            node_id,
            {
                "type": "missing_reference",
                "label": target_id,
                "path": record["relative_path"],
                "canonical_path": record["relative_path"],
                "line": 1,
                "project_namespace": record["project_id"],
                "project_id": record["project_id"],
                "source_refs": [self.source_ref(record["relative_path"], self.find_text_line(record["text"], field.split("[")[0]), field=field, object_id=record["object_id"])],
                "source": "ldvh_base_fact_reference",
            },
        )

    def edge_project_namespace(self, source, target):
        for node_id in (source, target):
            if not isinstance(node_id, str):
                continue
            if node_id.startswith("project:"):
                return node_id.split(":", 1)[1]
            if ":" in node_id and not node_id.startswith("code_consumption:"):
                return node_id.split(":", 1)[0]
        return self.project_namespace

    def ensure_reference_node(self, node_id, line):
        if node_id in self.node_ids:
            return
        if not isinstance(node_id, str) or not node_id.endswith(".md"):
            return
        node_path = self.root / node_id
        node_type = "external_fact_source" if node_path.exists() else "missing_reference"
        self.add_node(
            node_id,
            {
                "type": node_type,
                "label": Path(node_id).name,
                "path": node_id,
                "canonical_path": node_id,
                "line": line,
                "project_namespace": self.project_namespace,
                "source_refs": [self.source_ref(node_id, line)],
                "source": "relation_target",
            },
        )

    def source_ref(self, path, line_start=1, line_end=None, field=None, anchor=None, object_id=None):
        ref = {
            "path": path,
            "line_start": line_start or 1,
            "line_end": line_end or line_start or 1,
        }
        if field:
            ref["field"] = field
        if anchor:
            ref["anchor"] = anchor
        if object_id:
            ref["object_id"] = object_id
        return ref

    def edge_source_ref(self, source, target, line, field):
        for node_id in (source, target):
            ref = self.primary_node_source_ref(node_id)
            if ref:
                result = dict(ref)
                result.setdefault("line_start", line or 1)
                result.setdefault("line_end", line or result.get("line_start", 1))
                result["field"] = field
                return result
        for value in (source, target):
            if isinstance(value, str) and value.endswith((".md", ".yaml", ".yml")):
                return self.source_ref(value, line, field=field)
        return self.source_ref("<runtime>", line, field=field)

    def primary_node_source_ref(self, node_id):
        for node in self.nodes:
            if node.get("id") == node_id and node.get("source_refs"):
                return node["source_refs"][0]
        return None

    def edge_id(self, source, target, relation_type, source_structure, label=None):
        raw = "|".join([str(source), str(relation_type), str(target), str(source_structure), str(label or "")])
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        return f"edge:{digest}"

    def relative_or_absolute(self, path):
        try:
            return str(Path(path).resolve().relative_to(self.root))
        except ValueError:
            return str(Path(path).resolve())

    def project_relative_or_absolute(self, project_root, path):
        try:
            return str(Path(path).resolve().relative_to(Path(project_root).resolve()))
        except ValueError:
            return str(Path(path).resolve())
