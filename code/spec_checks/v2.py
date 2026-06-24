"""Diagnostics and knowledge-map projection for v2 specs."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import yaml

from .common import HEADING_RE
from .deployment_entries import deployment_entries_asset_records
from .knowledge_map import (
    KnowledgeMapMixin,
    V2_DEFAULT_PROJECT_NAMESPACE,
    V2_DEGRADED_DIAGNOSTIC_CODES,
    V2_KNOWLEDGE_MAP_TOOL,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

V2_SPEC_RE = re.compile(r"^(\d{2})-(.+)\.md$")
V2_ATTACHMENT_RE = re.compile(r"^(\d{2})\.Att\.(\d{2})-(.+)\.md$")
V2_MEMBER_RE = re.compile(r"^(\d{2})-(.+)-(.+)\.md$")
V2_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
V2_YAML_BLOCK_RE = re.compile(r"```ya?ml\s*\n(.*?\n)```", re.DOTALL)
V2_SECTION_REF_RE = re.compile(r"§(\d+(?:\.\d+)*)")

V2_SPEC_REQUIRED_FIELDS = [
    "spec_id",
    "spec_kind",
    "title",
    "status",
    "authority",
    "canonical_path",
    "created",
    "updated",
    "parent_spec",
    "relation",
    "positioning",
    "scope",
    "basis",
    "related_specs",
    "migration_sources",
    "active_fact_source",
    "code_consumption",
    "migration_status",
]
V2_SPEC_LIST_FIELDS = ["basis", "related_specs", "migration_sources", "active_fact_source", "code_consumption"]
V2_SPEC_KIND_VALUES = {"spec", "member_spec"}
V2_SPEC_STATUS_VALUES = {"draft", "ready_for_review", "active", "deprecated"}
V2_SPEC_AUTHORITY_VALUES = {"not_active_until_human_approved", "active", "deprecated_by"}
V2_SPEC_MIGRATION_STATUS_VALUES = {"not_migrated", "partially_migrated", "ready_for_review", "migrated", "not_applicable"}

V2_ATTACHMENT_REQUIRED_FIELDS = [
    "attachment_id",
    "title",
    "status",
    "authority",
    "parent_spec",
    "canonical_path",
    "purpose",
    "migration_sources",
    "code_consumption",
]
V2_ATTACHMENT_LIST_FIELDS = ["migration_sources", "code_consumption"]
V2_ATTACHMENT_STATUS_VALUES = {"draft", "ready_for_review", "active", "deprecated"}
V2_ATTACHMENT_AUTHORITY_VALUES = {
    "not_active_until_parent_and_human_approved",
    "active_with_parent",
    "active_with_parent_spec",
    "deprecated_by",
}
V2_ATTACHMENT_FORBIDDEN_SECTION_TITLES = {"AI 检查要求", "Human Gate", "Code 消费要求"}

V2_REQUIRED_SPEC_SECTIONS = {
    "本文解决的问题",
    "上位依据",
    "构成要素归属与价值判断",
    "规范保障要求",
    "Human Gate",
    "待补齐事项",
}
V2_REQUIRED_00_SECTIONS = {
    "本文解决的问题",
    "规范保障要求",
    "Human Gate",
    "待补齐事项",
}
V2_ASSURANCE_COLUMNS = ["保障要求", "要求内容", "保障机制", "同步类型", "触发条件"]
V2_INPUT_SCOPES = {"active_specs", "specs_v2", "entry_navigation", "all", "history_specs_v1", "governed_projects", "runtime_extensions"}
V2_QUERY_LAYERS = {"entry", "neighbors", "expand", "raw"}
V2_PROJECT_SCOPES = {"current_project", "all_governed_projects", "explicit_projects"}
class V2Checker(KnowledgeMapMixin):
    def __init__(
        self,
        root=None,
        specs_dir="specs",
        input_scope="active_specs",
        query_layer="entry",
        project_scope="current_project",
        start_node=None,
        relation_types=None,
        depth=1,
        projects=None,
        task_type=None,
    ):
        self.root = Path(root or PROJECT_ROOT).resolve()
        raw_specs_dir = Path(specs_dir)
        self.specs_dir = raw_specs_dir.resolve() if raw_specs_dir.is_absolute() else (self.root / raw_specs_dir).resolve()
        self.input_scope = input_scope
        self.query_layer = query_layer
        self.project_scope = project_scope
        self.start_node = start_node
        self.relation_types = set(relation_types or [])
        self.depth = max(0, int(depth or 0))
        self.projects = list(projects or [])
        self.task_type = task_type or "general"
        self.project_namespace = V2_DEFAULT_PROJECT_NAMESPACE
        self.diagnostics = []
        self.review_hints = []
        self.docs = []
        self.sections = []
        self.relations = []
        self.nodes = []
        self.edges = []
        self.node_ids = set()
        self.relation_keys = set()
        self.edge_keys = set()

    def build(self):
        self.validate_query_options()
        self.add_scope_diagnostics()

        parsed_docs = []
        known_paths = set()
        if self.should_parse_specs_v2():
            if not self.specs_dir.exists() and self.specs_dir.name == "specs":
                legacy_draft_dir = self.root / "specs-v2"
                if legacy_draft_dir.exists():
                    self.specs_dir = legacy_draft_dir.resolve()
            if not self.specs_dir.exists():
                raise FileNotFoundError(f"v2 规范目录不存在: {self.specs_dir}")
            files = sorted(self.specs_dir.rglob("*.md"))
            known_paths = {self.relative_path(path) for path in files}
            for path in files:
                parsed_docs.append(self.parse_file(path))

        spec_paths = {doc["path"] for doc in parsed_docs if doc["doc_type"] in {"spec", "member_spec"}}
        attachment_paths = {doc["path"] for doc in parsed_docs if doc["doc_type"] == "attachment"}

        for doc in parsed_docs:
            self.docs.append(self.compact_doc(doc))
            self.sections.extend(doc["sections"])
            self.add_document_node(doc)
            self.add_section_nodes(doc)
            self.validate_doc(doc, spec_paths, attachment_paths, known_paths)
            self.add_relation_edges(doc, known_paths)

        if self.should_parse_runtime_extensions():
            self.add_runtime_extension_assets()
        if self.should_parse_governed_projects():
            self.add_governed_project_graph()

        self.add_missing_attachment_authorization_diagnostics(spec_paths, attachment_paths)
        generated_at = datetime.now().isoformat(timespec="seconds")
        knowledge_map = self.project_knowledge_map(generated_at=generated_at)

        return {
            "metadata": {
                "derived": True,
                "source_of_truth": False,
                "generated_at": generated_at,
                "tool": V2_KNOWLEDGE_MAP_TOOL,
                "root": str(self.root),
                "specs_dir": self.relative_path(self.specs_dir),
                "read_only": True,
                "knowledge_map_boundary": "read_only_projection_not_fact_source",
                "input_scope": self.input_scope,
                "effective_input_scope": self.effective_input_scope(),
                "query_layer": self.query_layer,
                "project_scope": self.project_scope,
                "projects": self.projects,
                "start_node": self.start_node,
                "task_type": self.task_type,
                "relation_types": sorted(self.relation_types),
                "depth": self.depth,
                "degraded": self.is_degraded(),
            },
            "docs": self.docs,
            "sections": self.sections,
            "relations": self.relations,
            "knowledge_map": knowledge_map,
            "diagnostics": self.diagnostics,
            "review_hints": self.review_hints,
        }

    def validate_query_options(self):
        if self.input_scope not in V2_INPUT_SCOPES:
            self.diagnostics.append(
                self.diagnostic(
                    "<runtime>",
                    1,
                    "error",
                    "V2_INPUT_SCOPE_INVALID",
                    f"input_scope 非法: {self.input_scope}",
                    suggested_owner="04-Code确定性执行规范",
                )
            )
        if self.query_layer not in V2_QUERY_LAYERS:
            self.diagnostics.append(
                self.diagnostic(
                    "<runtime>",
                    1,
                    "error",
                    "V2_QUERY_LAYER_INVALID",
                    f"query_layer 非法: {self.query_layer}",
                    suggested_owner="04-Code确定性执行规范",
                )
            )
        if self.project_scope not in V2_PROJECT_SCOPES:
            self.diagnostics.append(
                self.diagnostic(
                    "<runtime>",
                    1,
                    "error",
                    "V2_PROJECT_SCOPE_INVALID",
                    f"project_scope 非法: {self.project_scope}",
                    suggested_owner="04-Code确定性执行规范",
                )
            )

    def add_scope_diagnostics(self):
        if self.input_scope in {"all", "history_specs_v1"}:
            self.diagnostics.append(
                self.diagnostic(
                    "<runtime>",
                    1,
                    "warning",
                    "V2_HISTORY_SPECS_V1_GRAPH_NOT_IMPLEMENTED",
                    "v1 历史规范图谱尚未实现；本次输出不包含历史追溯、迁移审计或价值提取节点边",
                    suggested_owner="04-Code确定性执行规范",
                )
            )

    def should_parse_specs_v2(self):
        return self.input_scope in {"active_specs", "specs_v2", "entry_navigation", "all"}

    def should_parse_runtime_extensions(self):
        return self.input_scope in {"runtime_extensions", "entry_navigation", "all"}

    def should_parse_governed_projects(self):
        return self.input_scope in {"governed_projects", "entry_navigation", "all"}

    def effective_input_scope(self):
        scopes = []
        if self.should_parse_specs_v2():
            scopes.append("active_specs")
        if self.should_parse_runtime_extensions():
            scopes.append("runtime_extensions")
        if self.should_parse_governed_projects():
            scopes.append("governed_projects")
        return scopes

    def is_degraded(self):
        return any(item.get("code") in V2_DEGRADED_DIAGNOSTIC_CODES for item in self.diagnostics)

    def parse_file(self, path):
        text = path.read_text(encoding="utf-8")
        rel_path = self.relative_path(path)
        title, title_line = self.extract_title(text)
        sections = self.extract_sections(path, text)
        preamble = self.preamble_text(text)
        spec_meta, spec_line, spec_error = self.extract_yaml_payload(preamble, text, "v2_spec")
        attachment_meta, attachment_line, attachment_error = self.extract_yaml_payload(preamble, text, "v2_attachment")
        fact_member, fact_member_line, fact_member_error = self.extract_yaml_payload(preamble, text, "v2_fact_model_member")
        action_member, action_member_line, action_member_error = self.extract_yaml_payload(preamble, text, "v2_action_member")
        doc_type = self.classify_doc(path, spec_meta, attachment_meta)

        if spec_error:
            self.diagnostics.append(self.diagnostic(rel_path, spec_line or 1, "error", "V2_SPEC_YAML_INVALID", spec_error))
        if attachment_error:
            self.diagnostics.append(self.diagnostic(rel_path, attachment_line or 1, "error", "V2_ATTACHMENT_YAML_INVALID", attachment_error))
        if fact_member_error:
            self.diagnostics.append(self.diagnostic(rel_path, fact_member_line or 1, "error", "V2_FACT_MEMBER_YAML_INVALID", fact_member_error))
        if action_member_error:
            self.diagnostics.append(self.diagnostic(rel_path, action_member_line or 1, "error", "V2_ACTION_MEMBER_YAML_INVALID", action_member_error))

        return {
            "path": rel_path,
            "absolute_path": path,
            "title": title,
            "title_line": title_line,
            "doc_type": doc_type,
            "spec": spec_meta,
            "spec_line": spec_line,
            "attachment": attachment_meta,
            "attachment_line": attachment_line,
            "fact_member": fact_member,
            "fact_member_line": fact_member_line,
            "action_member": action_member,
            "action_member_line": action_member_line,
            "sections": sections,
            "content_hash": self.sha256(text),
            "parse_status": "ok",
            "text": text,
        }

    def compact_doc(self, doc):
        payload = {
            "path": doc["path"],
            "title": doc["title"],
            "doc_type": doc["doc_type"],
            "content_hash": doc["content_hash"],
            "parse_status": doc["parse_status"],
        }
        if doc["spec"]:
            payload["v2_spec"] = doc["spec"]
        if doc["attachment"]:
            payload["v2_attachment"] = doc["attachment"]
        if doc["fact_member"]:
            payload["v2_fact_model_member"] = doc["fact_member"]
        if doc["action_member"]:
            payload["v2_action_member"] = doc["action_member"]
        return payload

    def classify_doc(self, path, spec_meta, attachment_meta):
        rel_to_specs = self.relative_to_specs_dir(path)
        name = path.name
        if V2_ATTACHMENT_RE.match(name):
            return "attachment"
        spec_match = V2_SPEC_RE.match(name)
        if spec_match and path.parent == self.specs_dir:
            if self.is_member_spec_id(spec_match.group(1)):
                return "member_spec"
            return "spec"
        if spec_meta and (
            self.is_member_spec_id(str(spec_meta.get("spec_id") or ""))
            or "20-29-事实模型" in rel_to_specs
            or "30-59-行动编排" in rel_to_specs
        ):
            return "member_spec"
        if spec_meta:
            return "spec_like"
        if attachment_meta:
            return "attachment_like"
        return "supporting_note"

    def validate_doc(self, doc, spec_paths, attachment_paths, known_paths):
        if doc["doc_type"] in {"spec", "member_spec", "spec_like"}:
            self.validate_spec_doc(doc, known_paths)
        elif doc["doc_type"] in {"attachment", "attachment_like"}:
            self.validate_attachment_doc(doc, spec_paths, known_paths)

    def validate_spec_doc(self, doc, known_paths):
        rel_path = doc["path"]
        spec = doc["spec"]
        line = doc["spec_line"] or 1
        if not spec:
            self.diagnostics.append(self.diagnostic(rel_path, 1, "error", "V2_SPEC_MISSING", "v2 规范文件缺少 v2_spec 身份块"))
            return
        self.validate_required_fields(rel_path, line, spec, V2_SPEC_REQUIRED_FIELDS, "V2_SPEC_FIELD_MISSING", "v2_spec 字段缺失")
        self.validate_list_fields(rel_path, line, spec, V2_SPEC_LIST_FIELDS, "V2_SPEC_FIELD_TYPE_INVALID")

        expected_id = self.expected_spec_id(doc)
        if expected_id and str(spec.get("spec_id")) != expected_id:
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_SPEC_ID_MISMATCH", f"v2_spec spec_id 与文件编号不一致: {spec.get('spec_id')} != {expected_id}"))
        if spec.get("canonical_path") != rel_path:
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_SPEC_CANONICAL_PATH_MISMATCH", f"v2_spec canonical_path 与实际路径不一致: {spec.get('canonical_path')} != {rel_path}"))
        if spec.get("title") != doc["title"]:
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_SPEC_TITLE_MISMATCH", f"v2_spec title 与一级标题不一致: {spec.get('title')} != {doc['title']}"))

        self.validate_enum(rel_path, line, "V2_SPEC_KIND_INVALID", "v2_spec spec_kind 非法", spec.get("spec_kind"), V2_SPEC_KIND_VALUES)
        self.validate_enum(rel_path, line, "V2_SPEC_STATUS_INVALID", "v2_spec status 非法", spec.get("status"), V2_SPEC_STATUS_VALUES)
        self.validate_enum(rel_path, line, "V2_SPEC_AUTHORITY_INVALID", "v2_spec authority 非法", spec.get("authority"), V2_SPEC_AUTHORITY_VALUES)
        self.validate_enum(rel_path, line, "V2_SPEC_MIGRATION_STATUS_INVALID", "v2_spec migration_status 非法", spec.get("migration_status"), V2_SPEC_MIGRATION_STATUS_VALUES)
        self.validate_dates(rel_path, line, spec, "V2_SPEC_DATE_INVALID")

        required_sections = V2_REQUIRED_00_SECTIONS if str(spec.get("spec_id")) == "00" else V2_REQUIRED_SPEC_SECTIONS
        section_titles = {section["title_normalized"] for section in doc["sections"] if section["level"] == 2}
        for title in sorted(required_sections):
            if title not in section_titles:
                self.diagnostics.append(self.diagnostic(rel_path, 1, "error", "V2_SPEC_REQUIRED_SECTION_MISSING", f"正式规范必要章节缺失: {title}"))

        if "规范保障要求" in section_titles:
            self.validate_assurance_table(doc)

        for field in ("basis", "related_specs", "migration_sources", "active_fact_source"):
            for target in spec.get(field) or []:
                self.validate_path_target(rel_path, line, field, target, known_paths)

        for category in spec.get("code_consumption") or []:
            if not isinstance(category, str) or not category.strip():
                self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_SPEC_CODE_CONSUMPTION_INVALID", "v2_spec code_consumption 每项必须是非空字符串"))

        if doc["doc_type"] == "member_spec":
            self.validate_member_doc(doc)

    def validate_attachment_doc(self, doc, spec_paths, known_paths):
        rel_path = doc["path"]
        attachment = doc["attachment"]
        line = doc["attachment_line"] or 1
        if not attachment:
            self.diagnostics.append(self.diagnostic(rel_path, 1, "error", "V2_ATTACHMENT_MISSING", "v2 附件文件缺少 v2_attachment 身份块"))
            return
        self.validate_required_fields(rel_path, line, attachment, V2_ATTACHMENT_REQUIRED_FIELDS, "V2_ATTACHMENT_FIELD_MISSING", "v2_attachment 字段缺失")
        self.validate_list_fields(rel_path, line, attachment, V2_ATTACHMENT_LIST_FIELDS, "V2_ATTACHMENT_FIELD_TYPE_INVALID")

        expected_id = self.expected_attachment_id(doc)
        if expected_id and attachment.get("attachment_id") != expected_id:
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_ATTACHMENT_ID_MISMATCH", f"v2_attachment attachment_id 与文件编号不一致: {attachment.get('attachment_id')} != {expected_id}"))
        if attachment.get("canonical_path") != rel_path:
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_ATTACHMENT_CANONICAL_PATH_MISMATCH", f"v2_attachment canonical_path 与实际路径不一致: {attachment.get('canonical_path')} != {rel_path}"))
        if attachment.get("title") != doc["title"]:
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_ATTACHMENT_TITLE_MISMATCH", f"v2_attachment title 与一级标题不一致: {attachment.get('title')} != {doc['title']}"))

        self.validate_enum(rel_path, line, "V2_ATTACHMENT_STATUS_INVALID", "v2_attachment status 非法", attachment.get("status"), V2_ATTACHMENT_STATUS_VALUES)
        self.validate_enum(rel_path, line, "V2_ATTACHMENT_AUTHORITY_INVALID", "v2_attachment authority 非法", attachment.get("authority"), V2_ATTACHMENT_AUTHORITY_VALUES)

        parent = attachment.get("parent_spec")
        if not parent:
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_ATTACHMENT_PARENT_MISSING", "v2_attachment parent_spec 不能为空"))
        elif parent not in spec_paths and parent not in known_paths:
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_ATTACHMENT_PARENT_NOT_FOUND", f"附件父规范不存在: {parent}"))

        section_titles = {section["title_normalized"] for section in doc["sections"] if section["level"] == 2}
        forbidden = sorted(section_titles & V2_ATTACHMENT_FORBIDDEN_SECTION_TITLES)
        for title in forbidden:
            self.diagnostics.append(self.diagnostic(rel_path, 1, "error", "V2_ATTACHMENT_FORBIDDEN_SECTION", f"附件不得设置独立章节: {title}"))

        for field in ("migration_sources",):
            for target in attachment.get(field) or []:
                self.validate_path_target(rel_path, line, field, target, known_paths)

        for category in attachment.get("code_consumption") or []:
            if not isinstance(category, str) or not category.strip():
                self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_ATTACHMENT_CODE_CONSUMPTION_INVALID", "v2_attachment code_consumption 每项必须是非空字符串"))

    def validate_member_doc(self, doc):
        rel_path = doc["path"]
        spec = doc["spec"] or {}
        line = doc["spec_line"] or 1
        spec_id = str(spec.get("spec_id") or self.expected_spec_id(doc) or "")
        if self.is_fact_model_member_id(spec_id):
            if not doc["fact_member"]:
                self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_FACT_MEMBER_MISSING", "事实模型成员规范缺少 v2_fact_model_member 身份块"))
        if self.is_action_member_id(spec_id):
            if not doc["action_member"]:
                self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_ACTION_MEMBER_MISSING", "行动编排成员规范缺少 v2_action_member 身份块"))
        if spec.get("spec_kind") != "member_spec":
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_MEMBER_SPEC_KIND_INVALID", "专题成员规范 v2_spec.spec_kind 必须为 member_spec"))

    def add_runtime_extension_assets(self):
        for record in deployment_entries_asset_records(self.root):
            metadata = record.get("metadata") or {}
            node_id = record.get("canonical_path") or record.get("path")
            self.add_node(
                node_id,
                {
                    "type": "runtime_extension",
                    "label": metadata.get("id") or node_id,
                    "path": record.get("path"),
                    "canonical_path": node_id,
                    "line": 1,
                    "status": metadata.get("status"),
                    "authority": "runtime_extension_asset",
                    "project_namespace": self.project_namespace,
                    "source_refs": [self.source_ref(record.get("path"), 1, field="ldvh_asset")],
                    "source": "ldvh_asset",
                    "asset_type": metadata.get("type"),
                    "source_specs": list(metadata.get("source_specs") or []),
                    "sync_triggers": list(metadata.get("sync_triggers") or []),
                    "verification": list(metadata.get("verification") or []),
                },
            )
            for source_spec in metadata.get("source_specs") or []:
                self.add_edge(node_id, source_spec, "derives_from", "ldvh_asset.source_specs", 1)

    def validate_assurance_table(self, doc):
        section = self.find_h2_section(doc, "规范保障要求")
        if not section:
            return
        table = self.assurance_table_in_span(doc["text"], section["line"], section["end_line"])
        if not table:
            self.diagnostics.append(self.diagnostic(doc["path"], section["line"], "error", "V2_ASSURANCE_TABLE_MISSING", "规范保障要求章节缺少五字段表"))
            return
        missing = [column for column in V2_ASSURANCE_COLUMNS if column not in table["columns"]]
        for column in missing:
            self.diagnostics.append(self.diagnostic(doc["path"], table["line"], "error", "V2_ASSURANCE_COLUMN_MISSING", f"规范保障要求表字段缺失: {column}"))

    def validate_required_fields(self, rel_path, line, data, fields, code, message):
        for field in fields:
            if field not in data:
                self.diagnostics.append(self.diagnostic(rel_path, line, "error", code, f"{message}: {field}"))

    def validate_list_fields(self, rel_path, line, data, fields, code):
        for field in fields:
            if field in data and not isinstance(data.get(field), list):
                self.diagnostics.append(self.diagnostic(rel_path, line, "error", code, f"字段必须是列表: {field}"))

    def validate_enum(self, rel_path, line, code, message, value, allowed):
        if value is not None and value not in allowed:
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", code, f"{message}: {value}"))

    def validate_dates(self, rel_path, line, data, code):
        created = data.get("created")
        updated = data.get("updated")
        for field, value in (("created", created), ("updated", updated)):
            if value is None:
                continue
            if not isinstance(value, str) or not V2_DATE_RE.match(value):
                self.diagnostics.append(self.diagnostic(rel_path, line, "error", code, f"日期字段必须为 YYYY-MM-DD: {field}={value}"))
        if isinstance(created, str) and isinstance(updated, str) and V2_DATE_RE.match(created) and V2_DATE_RE.match(updated):
            if updated < created:
                self.diagnostics.append(self.diagnostic(rel_path, line, "error", code, f"updated 不能早于 created: {updated} < {created}"))

    def validate_path_target(self, rel_path, line, field, target, known_paths):
        if not isinstance(target, str) or not target.strip():
            self.diagnostics.append(self.diagnostic(rel_path, line, "error", "V2_RELATION_TARGET_INVALID", f"{field} 目标必须是非空字符串"))
            return
        if not target.endswith(".md"):
            return
        target_path = self.root / target
        if target not in known_paths and not target_path.exists():
            self.diagnostics.append(self.diagnostic(rel_path, line, "warning", "V2_RELATION_TARGET_NOT_FOUND", f"{field} 目标文件不存在: {target}"))

    def add_missing_attachment_authorization_diagnostics(self, spec_paths, attachment_paths):
        parent_related = {}
        for doc in self.docs:
            spec = doc.get("v2_spec") or {}
            if not spec:
                continue
            parent_related[doc["path"]] = set(spec.get("related_specs") or [])
        for doc in self.docs:
            attachment = doc.get("v2_attachment") or {}
            if not attachment:
                continue
            parent = attachment.get("parent_spec")
            path = doc["path"]
            if parent in parent_related and path not in parent_related[parent]:
                self.review_hints.append(
                    self.diagnostic(
                        path,
                        1,
                        "info",
                        "V2_ATTACHMENT_NOT_IN_PARENT_RELATED_SPECS",
                        f"附件父规范 v2_spec.related_specs 未登记该附件: {parent}",
                    )
                )

    def extract_title(self, text):
        for index, line in enumerate(text.splitlines(), start=1):
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) == 1:
                return match.group(2).strip(), index
        return "", 1

    def extract_sections(self, path, text):
        rel_path = self.relative_path(path)
        sections = []
        in_fence = False
        for index, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            match = HEADING_RE.match(line)
            if not match:
                continue
            level = len(match.group(1))
            raw_title = match.group(2).strip()
            number, normalized = self.normalize_heading(raw_title)
            sections.append(
                {
                    "path": rel_path,
                    "line": index,
                    "level": level,
                    "number": number,
                    "title": raw_title,
                    "title_normalized": normalized,
                }
            )
        for pos, section in enumerate(sections):
            next_same_or_higher = next((item for item in sections[pos + 1 :] if item["level"] <= section["level"]), None)
            section["end_line"] = (next_same_or_higher["line"] - 1) if next_same_or_higher else len(text.splitlines())
        return sections

    def normalize_heading(self, raw_title):
        match = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$", raw_title)
        if match:
            return match.group(1), match.group(2).strip()
        return "", raw_title.strip()

    def preamble_text(self, text):
        lines = []
        for line in text.splitlines(keepends=True):
            if line.startswith("## "):
                break
            lines.append(line)
        return "".join(lines)

    def extract_yaml_payload(self, preamble, full_text, root_key):
        for match in V2_YAML_BLOCK_RE.finditer(preamble):
            block = match.group(1)
            line_start = len(full_text[: match.start(1)].splitlines()) + 1
            try:
                data = yaml.safe_load(block) or {}
            except yaml.YAMLError as exc:
                return None, line_start, str(exc)
            if root_key not in data:
                continue
            payload = data.get(root_key)
            if not isinstance(payload, dict):
                return None, line_start, f"{root_key} 必须是映射结构"
            normalized = dict(payload)
            normalized["path"] = self.relative_path_from_payload(normalized)
            normalized["line"] = line_start
            return normalized, line_start, None
        return None, None, None

    def relative_path_from_payload(self, payload):
        return payload.get("canonical_path") or payload.get("parent_spec") or ""

    def expected_spec_id(self, doc):
        match = V2_SPEC_RE.match(doc["absolute_path"].name)
        if match:
            return match.group(1)
        match = V2_MEMBER_RE.match(doc["absolute_path"].name)
        return match.group(1) if match else None

    def is_member_spec_id(self, spec_id):
        return self.is_fact_model_member_id(spec_id) or self.is_action_member_id(spec_id)

    def is_fact_model_member_id(self, spec_id):
        return self.spec_id_in_range(spec_id, 20, 29)

    def is_action_member_id(self, spec_id):
        return self.spec_id_in_range(spec_id, 30, 59)

    def spec_id_in_range(self, spec_id, start, end):
        if not isinstance(spec_id, str) or not re.match(r"^\d{2}$", spec_id):
            return False
        return start <= int(spec_id) <= end

    def expected_attachment_id(self, doc):
        match = V2_ATTACHMENT_RE.match(doc["absolute_path"].name)
        if not match:
            return None
        return f"{match.group(1)}.Att.{match.group(2)}"

    def find_h2_section(self, doc, title):
        return next((section for section in doc["sections"] if section["level"] == 2 and section["title_normalized"] == title), None)

    def first_table_in_span(self, text, start_line, end_line):
        tables = self.tables_in_span(text, start_line, end_line)
        return tables[0] if tables else None

    def assurance_table_in_span(self, text, start_line, end_line):
        tables = self.tables_in_span(text, start_line, end_line)
        for table in tables:
            if all(column in table["columns"] for column in V2_ASSURANCE_COLUMNS):
                return table
        for table in tables:
            if any(column in table["columns"] for column in V2_ASSURANCE_COLUMNS):
                return table
        return None

    def tables_in_span(self, text, start_line, end_line):
        lines = text.splitlines()
        tables = []
        for index in range(start_line - 1, min(end_line, len(lines))):
            line = lines[index]
            if not line.strip().startswith("|"):
                continue
            if index + 1 >= len(lines) or not self.is_table_separator(lines[index + 1]):
                continue
            tables.append({"line": index + 1, "columns": self.split_table_cells(line)})
        return tables

    def is_table_separator(self, line):
        cells = self.split_table_cells(line)
        return bool(cells) and all(re.match(r"^:?-{3,}:?$", cell) for cell in cells)

    def split_table_cells(self, line):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            return []
        return [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]

    def find_text_line(self, text, needle):
        for index, line in enumerate(text.splitlines(), start=1):
            if needle in line:
                return index
        return 1

    def relative_to_specs_dir(self, path):
        try:
            return str(Path(path).resolve().relative_to(self.specs_dir))
        except ValueError:
            return str(path)

    def relative_path(self, path):
        try:
            return str(Path(path).resolve().relative_to(self.root))
        except ValueError:
            return str(path)

    def sha256(self, text):
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    def diagnostic(self, path, line, severity, code, message, suggested_owner=None, source_refs=None):
        line = line or 1
        item = {
            "severity": severity,
            "path": path,
            "line": line,
            "code": code,
            "message": message,
            "source_refs": source_refs or [self.source_ref(path, line)],
        }
        if suggested_owner:
            item["suggested_owner"] = suggested_owner
        return item


def format_text(report):
    diagnostics = report.get("diagnostics", [])
    hints = report.get("review_hints", [])
    docs = report.get("docs", [])
    knowledge_map = report.get("knowledge_map", {})
    nodes = knowledge_map.get("nodes", [])
    edges = knowledge_map.get("edges", [])
    query = knowledge_map.get("query", {})
    lines = [
        "active specs 规范诊断完成",
        f"- input_scope: {query.get('input_scope')}",
        f"- layer: {query.get('layer')}",
        f"- task_type: {query.get('task_type')}",
        f"- degraded: {query.get('degraded')}",
        f"- docs: {len(docs)}",
        f"- knowledge_map.nodes: {len(nodes)}",
        f"- knowledge_map.edges: {len(edges)}",
        f"- read_plan: {len(knowledge_map.get('read_plan', []))}",
        f"- next_queries: {len(knowledge_map.get('next_queries', []))}",
        f"- stop_conditions: {len(knowledge_map.get('stop_conditions', []))}",
        f"- diagnostics: {len(diagnostics)}",
        f"- review_hints: {len(hints)}",
    ]
    lines.extend(format_navigation_text_lines(knowledge_map))
    if diagnostics:
        lines.append("")
        lines.append("Diagnostics:")
        for item in diagnostics:
            lines.append(f"- {item['path']}:{item['line']} [{item['severity']}/{item['code']}] {item['message']}")
    if hints:
        lines.append("")
        lines.append("Review hints:")
        for item in hints:
            lines.append(f"- {item['path']}:{item['line']} [{item['code']}] {item['message']}")
    return "\n".join(lines)


def format_navigation_text_lines(knowledge_map):
    lines = []
    navigation = knowledge_map.get("navigation") or {}
    read_plan = knowledge_map.get("read_plan") or []
    next_queries = knowledge_map.get("next_queries") or []
    stop_conditions = knowledge_map.get("stop_conditions") or []
    impact_summary = knowledge_map.get("impact_summary") or {}

    lines.append("")
    lines.append("Navigation:")
    if navigation:
        lines.append(
            f"- task_type={navigation.get('task_type')} start_node={navigation.get('start_node')} "
            f"resolved_start_node={navigation.get('resolved_start_node')} degraded={navigation.get('degraded')}"
        )
        lines.append(f"- summary: {navigation.get('summary')}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Read plan:")
    if read_plan:
        priority_items = [item for item in read_plan if item.get("priority") in {"P0", "P1"}]
        other_items = [item for item in read_plan if item.get("priority") not in {"P0", "P1"}]
        shown = priority_items + other_items[: max(0, 8 - len(priority_items))]
        for item in shown:
            lines.append(
                f"- {item.get('priority')}/{item.get('role')}: {item.get('path')} "
                f"({item.get('source_relation')}) - {item.get('reason')}"
            )
            sections = item.get("suggested_sections") or []
            if sections:
                lines.append(f"  suggested_sections: {json.dumps(sections, ensure_ascii=False)}")
        omitted = len(read_plan) - len(shown)
        if omitted > 0:
            lines.append(f"- omitted: {omitted} lower-priority items; use --format json or layer expand for the full plan")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Next queries:")
    if next_queries:
        for item in next_queries[:5]:
            lines.append(f"- {item.get('purpose')}: {item.get('command')}")
        omitted = len(next_queries) - min(len(next_queries), 5)
        if omitted > 0:
            lines.append(f"- omitted: {omitted} queries; use --format json for the full list")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Stop conditions:")
    if stop_conditions:
        for item in stop_conditions[:5]:
            lines.append(f"- {item.get('condition')}: {item.get('fallback')}")
        omitted = len(stop_conditions) - min(len(stop_conditions), 5)
        if omitted > 0:
            lines.append(f"- omitted: {omitted} stop conditions; use --format json for the full list")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Impact summary:")
    if impact_summary:
        lines.append(f"- node_type_counts: {impact_summary.get('node_type_counts', {})}")
        lines.append(f"- relation_type_counts: {impact_summary.get('relation_type_counts', {})}")
        lines.append(f"- semantic_relation_type_counts: {impact_summary.get('semantic_relation_type_counts', {})}")
        lines.append(f"- omitted_semantic_relation_type_counts: {impact_summary.get('omitted_semantic_relation_type_counts', {})}")
        lines.append(
            f"- affected: specs={len(impact_summary.get('affected_specs', []))} "
            f"runtime_extensions={len(impact_summary.get('affected_runtime_extensions', []))} "
            f"fact_objects={len(impact_summary.get('affected_fact_objects', []))}"
        )
    else:
        lines.append("- none")
    return lines


def format_knowledge_map_text(knowledge_map):
    query = knowledge_map.get("query", {})
    lines = [
        "知识地图只读投影完成",
        f"- input_scope: {knowledge_map.get('input_scope')}",
        f"- layer: {query.get('layer')}",
        f"- task_type: {query.get('task_type')}",
        f"- project_scope: {query.get('project_scope')}",
        f"- degraded: {knowledge_map.get('degraded')}",
        f"- nodes: {len(knowledge_map.get('nodes', []))}",
        f"- edges: {len(knowledge_map.get('edges', []))}",
        f"- read_plan: {len(knowledge_map.get('read_plan', []))}",
        f"- next_queries: {len(knowledge_map.get('next_queries', []))}",
        f"- stop_conditions: {len(knowledge_map.get('stop_conditions', []))}",
        f"- diagnostics: {len(knowledge_map.get('diagnostics', []))}",
        f"- excluded_inputs: {len(knowledge_map.get('excluded_inputs', []))}",
    ]
    if "raw_content" in knowledge_map:
        lines.append(f"- raw_content: {len(knowledge_map.get('raw_content', []))}")
    lines.extend(format_navigation_text_lines(knowledge_map))
    return "\n".join(lines)


def v2_check_build(
    root=None,
    specs_dir="specs",
    input_scope="active_specs",
    query_layer="entry",
    project_scope="current_project",
    start_node=None,
    relation_types=None,
    depth=1,
    projects=None,
    task_type=None,
):
    return V2Checker(
        root or PROJECT_ROOT,
        specs_dir,
        input_scope=input_scope,
        query_layer=query_layer,
        project_scope=project_scope,
        start_node=start_node,
        relation_types=relation_types,
        depth=depth,
        projects=projects,
        task_type=task_type,
    ).build()


def v2_check_main(
    root=None,
    specs_dir="specs",
    output_format="json",
    fail_on_diagnostics=False,
    input_scope="active_specs",
    query_layer="entry",
    project_scope="current_project",
    start_node=None,
    relation_types=None,
    depth=1,
    projects=None,
    task_type=None,
):
    report = v2_check_build(
        root,
        specs_dir,
        input_scope=input_scope,
        query_layer=query_layer,
        project_scope=project_scope,
        start_node=start_node,
        relation_types=relation_types,
        depth=depth,
        projects=projects,
        task_type=task_type,
    )
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_text(report))
    if fail_on_diagnostics and report.get("diagnostics"):
        return 1
    return 0


def knowledge_map_main(
    root=None,
    specs_dir="specs",
    output_format="json",
    fail_on_diagnostics=False,
    input_scope="active_specs",
    query_layer="entry",
    project_scope="current_project",
    start_node=None,
    relation_types=None,
    depth=1,
    projects=None,
    task_type=None,
):
    report = v2_check_build(
        root,
        specs_dir,
        input_scope=input_scope,
        query_layer=query_layer,
        project_scope=project_scope,
        start_node=start_node,
        relation_types=relation_types,
        depth=depth,
        projects=projects,
        task_type=task_type,
    )
    knowledge_map = report.get("knowledge_map", {})
    if output_format == "json":
        print(json.dumps(knowledge_map, ensure_ascii=False, indent=2))
    else:
        print(format_knowledge_map_text(knowledge_map))
    if fail_on_diagnostics and knowledge_map.get("diagnostics"):
        return 1
    return 0
