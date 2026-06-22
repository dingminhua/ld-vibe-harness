"""Read-only diagnostics and knowledge-map projection for specs-v2 drafts."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import yaml

from .common import HEADING_RE


PROJECT_ROOT = Path(__file__).resolve().parents[2]

V2_SPEC_RE = re.compile(r"^(\d{2})-(.+)\.md$")
V2_ATTACHMENT_RE = re.compile(r"^(\d{2})\.Att\.(\d{2})-(.+)\.md$")
V2_MEMBER_RE = re.compile(r"^(\d{2})-(.+)-(.+)\.md$")
V2_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
V2_YAML_BLOCK_RE = re.compile(r"```ya?ml\s*\n(.*?\n)```", re.DOTALL)
V2_PATH_REF_RE = re.compile(r"`((?:specs-v2|specs|code|web|tests|rules|skills|agents|hooks)/[^`]+?)`")
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
V2_ATTACHMENT_AUTHORITY_VALUES = {"not_active_until_parent_and_human_approved", "active_with_parent", "deprecated_by"}
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
V2_INPUT_SCOPES = {"specs_v2", "all", "governed_projects", "git_history"}
V2_QUERY_LAYERS = {"entry", "neighbors", "expand", "raw"}
V2_PROJECT_SCOPES = {"current_project", "all_governed_projects", "explicit_projects"}
V2_DEFAULT_PROJECT_NAMESPACE = "ldvh_self"
V2_DEGRADED_DIAGNOSTIC_CODES = {
    "V2_GOVERNED_PROJECT_GRAPH_NOT_IMPLEMENTED",
    "V2_GIT_HISTORY_GRAPH_NOT_IMPLEMENTED",
    "V2_RAW_LAYER_NOT_IMPLEMENTED",
    "V2_QUERY_START_NODE_MISSING",
    "V2_QUERY_START_NODE_NOT_FOUND",
    "V2_PROJECT_SCOPE_NOT_IMPLEMENTED",
}


class V2Checker:
    def __init__(
        self,
        root=None,
        specs_dir="specs-v2",
        input_scope="specs_v2",
        query_layer="entry",
        project_scope="current_project",
        start_node=None,
        relation_types=None,
        depth=1,
        projects=None,
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

        self.add_missing_attachment_authorization_diagnostics(spec_paths, attachment_paths)
        knowledge_map = self.project_knowledge_map()

        return {
            "metadata": {
                "derived": True,
                "source_of_truth": False,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "tool": "code/specs_validate.py v2-check",
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
        if self.input_scope in {"all", "governed_projects"}:
            self.diagnostics.append(
                self.diagnostic(
                    "<runtime>",
                    1,
                    "warning",
                    "V2_GOVERNED_PROJECT_GRAPH_NOT_IMPLEMENTED",
                    "管辖项目运行时图谱尚未实现；本次输出不包含 ldvh-base 工作对象关系或多项目扫描结果",
                    suggested_owner="04-Code确定性执行规范",
                )
            )
        if self.input_scope in {"all", "git_history"}:
            self.diagnostics.append(
                self.diagnostic(
                    "<runtime>",
                    1,
                    "warning",
                    "V2_GIT_HISTORY_GRAPH_NOT_IMPLEMENTED",
                    "Git history 证据层尚未实现；本次输出不包含 commit、diff 或变更事件边",
                    suggested_owner="04-Code确定性执行规范",
                )
            )
        if self.project_scope != "current_project":
            self.diagnostics.append(
                self.diagnostic(
                    "<runtime>",
                    1,
                    "warning",
                    "V2_PROJECT_SCOPE_NOT_IMPLEMENTED",
                    f"project_scope={self.project_scope} 尚未实现；本次输出仅使用 {self.project_namespace} 命名空间",
                    suggested_owner="04-Code确定性执行规范",
                )
            )
        if self.query_layer == "raw":
            self.diagnostics.append(
                self.diagnostic(
                    "<runtime>",
                    1,
                    "warning",
                    "V2_RAW_LAYER_NOT_IMPLEMENTED",
                    "原文层展开尚未实现；本次输出退回到 expand 关系视图，不返回正文全文、Git diff 或事实对象全文",
                    suggested_owner="04-Code确定性执行规范",
                )
            )

    def should_parse_specs_v2(self):
        return self.input_scope in {"specs_v2", "all"}

    def effective_input_scope(self):
        scopes = []
        if self.should_parse_specs_v2():
            scopes.append("specs_v2")
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
                    "source_refs": [self.source_ref(doc["path"], section["line"], section["end_line"], anchor=f"§{section['number']}" if section["number"] else None)],
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
        self.nodes.append({"id": node_id, **payload})

    def project_knowledge_map(self):
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
        return {
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
    nodes = report.get("knowledge_map", {}).get("nodes", [])
    edges = report.get("knowledge_map", {}).get("edges", [])
    query = report.get("knowledge_map", {}).get("query", {})
    lines = [
        "specs-v2 只读诊断完成",
        f"- input_scope: {query.get('input_scope')}",
        f"- layer: {query.get('layer')}",
        f"- degraded: {query.get('degraded')}",
        f"- docs: {len(docs)}",
        f"- knowledge_map.nodes: {len(nodes)}",
        f"- knowledge_map.edges: {len(edges)}",
        f"- diagnostics: {len(diagnostics)}",
        f"- review_hints: {len(hints)}",
    ]
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


def v2_check_build(
    root=None,
    specs_dir="specs-v2",
    input_scope="specs_v2",
    query_layer="entry",
    project_scope="current_project",
    start_node=None,
    relation_types=None,
    depth=1,
    projects=None,
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
    ).build()


def v2_check_main(
    root=None,
    specs_dir="specs-v2",
    output_format="json",
    fail_on_diagnostics=False,
    input_scope="specs_v2",
    query_layer="entry",
    project_scope="current_project",
    start_node=None,
    relation_types=None,
    depth=1,
    projects=None,
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
    )
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_text(report))
    if fail_on_diagnostics and report.get("diagnostics"):
        return 1
    return 0
