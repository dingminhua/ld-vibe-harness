"""Read-only knowledge-map projection helpers for specs diagnostics."""

import hashlib
import re
from pathlib import Path


V2_DEFAULT_PROJECT_NAMESPACE = "ldvh_self"
V2_KNOWLEDGE_MAP_SCHEMA_VERSION = "04.Att.06.v1"
V2_KNOWLEDGE_MAP_TOOL = "code/specs_validate.py v2-check"
V2_DEGRADED_DIAGNOSTIC_CODES = {
    "V2_GOVERNED_PROJECT_GRAPH_NOT_IMPLEMENTED",
    "V2_GIT_HISTORY_GRAPH_NOT_IMPLEMENTED",
    "V2_RAW_LAYER_NOT_IMPLEMENTED",
    "V2_QUERY_START_NODE_MISSING",
    "V2_QUERY_START_NODE_NOT_FOUND",
    "V2_PROJECT_SCOPE_NOT_IMPLEMENTED",
}
V2_PATH_REF_RE = re.compile(r"`((?:specs-v2|specs|code|web|tests|rules|skills|agents|hooks)/[^`]+?)`")


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
                "project_namespace": self.project_namespace,
                "source_refs": [self.source_ref(source if source.endswith(".md") else target, line, field=source_structure)],
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
                "source_refs": [self.source_ref(source if source.endswith(".md") else target, line, field=source_structure)],
                **({"label": label} if label else {}),
            }
        )

    def add_node(self, node_id, payload):
        if node_id in self.node_ids:
            return
        self.node_ids.add(node_id)
        payload.setdefault("canonical_path", payload.get("path"))
        payload.setdefault("project_namespace", self.project_namespace)
        payload.setdefault("source_refs", [])
        payload.setdefault("status", None)
        payload.setdefault("authority", None)
        self.nodes.append({"id": node_id, **payload})

    def project_knowledge_map(self, generated_at=None):
        nodes_by_id = {node["id"]: node for node in self.nodes}
        edges = self.filtered_edges_by_relation(self.edges)
        layer = "expand" if self.query_layer == "raw" else self.query_layer

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
                selected_nodes, selected_edges = self.traverse_edges(start_id, edges, 1 if layer == "neighbors" else self.depth)
        else:
            selected_nodes, selected_edges = self.entry_fallback(edges)

        projected_nodes = [nodes_by_id[node_id] for node_id in self.sorted_node_ids(selected_nodes) if node_id in nodes_by_id]
        source_refs = self.knowledge_map_source_refs(projected_nodes, selected_edges)
        return {
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
                "relation_types": sorted(self.relation_types),
                "depth": self.depth,
                "degraded": self.is_degraded(),
            },
            "project_namespace": self.project_namespace,
            "nodes": projected_nodes,
            "edges": selected_edges,
            "excluded_inputs": self.excluded_inputs(),
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
        if self.input_scope in {"all", "governed_projects"}:
            excluded.append({"input": "governed_projects", "reason": "not_implemented", "diagnostic": "V2_GOVERNED_PROJECT_GRAPH_NOT_IMPLEMENTED"})
        if self.input_scope in {"all", "git_history"}:
            excluded.append({"input": "git_history", "reason": "not_implemented", "diagnostic": "V2_GIT_HISTORY_GRAPH_NOT_IMPLEMENTED"})
        if self.query_layer == "raw":
            excluded.append({"input": "raw_content", "reason": "not_implemented", "diagnostic": "V2_RAW_LAYER_NOT_IMPLEMENTED"})
        return excluded

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

    def source_ref(self, path, line_start=1, line_end=None, field=None, anchor=None):
        ref = {
            "path": path,
            "line_start": line_start or 1,
            "line_end": line_end or line_start or 1,
        }
        if field:
            ref["field"] = field
        if anchor:
            ref["anchor"] = anchor
        return ref

    def edge_id(self, source, target, relation_type, source_structure, label=None):
        raw = "|".join([str(source), str(relation_type), str(target), str(source_structure), str(label or "")])
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        return f"edge:{digest}"
