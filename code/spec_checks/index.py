"""Specs derived index and diagnostics for LDVH."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from .common import HEADING_RE


PROJECT_ROOT = Path(__file__).resolve().parents[2]


INDEX_INPUT_PATTERNS = ("*.md",)
INDEX_NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
INDEX_HEADER_FIELD_RE = re.compile(r"^>\s*([^：:]+)[：:]\s*(.*)\s*$")
INDEX_BACKTICK_MD_RE = re.compile(r"`([^`]+\.md)`")
INDEX_PLAIN_SPECS_MD_RE = re.compile(
    r"(?<![`\w./-])((?:specs/[^\s`，。；、)）]+\.md|code/docs/[^\s`，。；、)）]+\.md|docs/(?:studies|sources|research|refs)/[^\s`，。；、)）]+\.md|docs/[^/\s`，。；、)）]+\.md))"
)
INDEX_RESEARCH_REF_RE = re.compile(r"(?<![`\w./-])(?:`)?((?:specs/research/|docs/research/)[^`\s，。；、)）]+\.md)(?:`)?")
INDEX_DOCS_MATERIAL_REF_RE = re.compile(r"(?<![`\w./-])(?:`)?((?:docs/(?:studies|sources|research|refs)/)[^`\s，。；、)）]+\.md)(?:`)?")
INDEX_DOCS_ROOT_ASSET_REF_RE = re.compile(r"(?<![`\w./-])(?:`)?(docs/[^/`\s，。；、)）]+\.md)(?:`)?")
INDEX_EXTERNAL_URL_RE = re.compile(r"https?://[^\s`，。；、)）]+")
INDEX_ALLOWED_EXTERNAL_STANDARD_URLS = {
    "specs/10-Git提交规范.md": {
        "https://www.conventionalcommits.org/en/v1.0.0/",
    },
}
INDEX_SECTION_REF_RE = re.compile(r"§([一二三四五六七八九十百千万\d]+(?:\.\d+)*)")
INDEX_DOC_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)?)-")
INDEX_DEFINITION_SENTENCE_RE = re.compile(r"^(?:(?:在本文|在本规范|在本文档)中[，,]?\s*)?(?:(?:[-*]|\d+[.、])\s*)?(?:\*\*)?([^|。；;，,\s`*是]{2,24})(?:\*\*)?\s*(?:是指|定义为|包括且仅包括|指(?!向|引|标|回|令|定|派|出|控|责|南|针|纹|挥|数|甲|望)|是(?!否))")
INDEX_FOOTNOTE_RE = re.compile(r"^\[\^[^\]]+\]:\s*(.+)$")
INDEX_LDVH_MEMBER_RE = re.compile(r"```ya?ml\s*\n(.*?\n)```", re.DOTALL)
INDEX_LDVH_DOC_ALLOWED_KINDS = {"formal_spec", "specs_subdocument", "work_model_spec", "work_process_spec"}
INDEX_LDVH_DOC_ALLOWED_STATUS = {"active", "candidate", "reserved", "removed"}
INDEX_LDVH_DOC_STANDARD_FIELDS = [
    "doc_id",
    "doc_kind",
    "title",
    "status",
    "canonical_path",
    "created",
    "updated",
    "parent_doc",
    "relation",
    "positioning",
    "scope",
    "basis",
    "related_specs",
    "code_consumption",
]
INDEX_LDVH_DOC_NONEMPTY_FIELDS = ["doc_id", "doc_kind", "title", "status", "canonical_path", "created", "updated", "positioning", "scope", "basis", "code_consumption"]
INDEX_LDVH_DOC_HEADER_FORBIDDEN_FIELDS = {"创建日期", "更新日期", "所属主文档", "关系", "定位", "适用范围", "上位依据", "相关规范"}
INDEX_LDVH_DOC_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INDEX_WORK_MODEL_DIRECTORY_HEADER = ("当前编号", "工作模型", "事实实例承载")
INDEX_FORBIDDEN_DEFINITION_SECTION_TITLES = {"术语定义", "概念定义", "名词解释"}
INDEX_ALLOWED_SUBDOCUMENT_RELATIONS = {"应用剖面", "专题子文档"}
INDEX_SUBDOCUMENT_BOUNDARY_TITLE_TERMS = ("子文档", "应用剖面", "专题子文档")
INDEX_LDVH_MEMBER_HEADER_FORBIDDEN_FIELDS = {
    "文档编号",
    "文档类型",
    "集合状态",
    "canonical_path",
    "schema_anchor",
    "state_machine_anchor",
    "human_gate_anchor",
    "scenario_anchor",
    "context_anchor",
    "gate_anchor",
    "execution_anchor",
    "writeback_anchor",
    "evidence_anchor",
    "testability_anchor",
    "code_consumption",
}
INDEX_GOVERNED_TERMS = {
    "LDVH 自身项目", "管辖项目", "管辖项目配置", "LDVH 文档工作区", "规范正文区", "管辖项目文档工作区", "正文区", "studies", "sources",
    "来源", "吸收", "参考与研究材料", "待补齐事项", "正式规范", "资产", "规范资产", "文本能力资产", "Code 能力资产", "Web 能力资产",
    "工作对象事实源", "用户资产", "可变资料区", "候选事项", "索引文档", "说明性索引", "规范型集合索引", "规范落地要求", "能力保障",
    "LDVH 能力资产", "保障机制", "环境入口", "环境适配", "环境能力清单", "适配措施", "适配措施状态", "环境", "AI 开发环境",
    "环境实体", "环境能力", "适配边界", "适配检查", "适配降级", "工作区级入口", "项目级入口", "AI 入口分层", "LDVH 项目事实源",
    "项目接入说明", "能力缺口", "环境缺口", "漂移", "LDVH 运行纪律", "启用", "薄引用", "开发环境", "工作模型", "工作对象", "工作字段",
    "字段内容格式", "对象状态", "集合状态", "检查过程状态", "派生状态", "Git 提交记录", "工作流程", "Code", "Web", "受控写入", "受控轻写入",
    "Rules / Instructions", "Skill", "LDVH 自建 Skill", "LDVH 包装 Skill", "Agent", "Hook / 自动触发", "MCP / 模型上下文协议", "运行闭环", "具体工作流程",
    "行动", "Scenario 识别条件", "适用场景", "步骤", "阶段标签", "Apply", "Verify", "Review", "Recheck", "Gate", "Human Gate 记录", "LDVH落地",
    "环境确认", "LDVH落地与检查", "落地检查报告", "检查", "校验", "验证", "审计", "审阅", "审核", "写入", "回写", "事实源回写",
}
INDEX_DEFINITION_WHITELIST_TERMS = {"本文", "本规范", "00", "02", "Code", "Web", "Human Gate", "Rules", "Skill", "Agent", "Hook", "MCP"}
INDEX_ALLOWED_DEFINITION_OWNERS = {
    "开发环境": {"00"},
    "工作模型": {"00", "05"},
    "字段内容格式": {"00", "05.01"},
    "管辖项目配置": {"03.04"},
    "工作流程": {"00", "06"},
    "Gate": {"06"},
    "事实源回写": {"06", "09"},
}
INDEX_REVERSE_RELATED_TERMS = ("反向", "被下游", "被引用", "谁引用", "可发现性", "追溯", "影响面")


class SpecsIndexError(Exception):
    pass


class SpecsChecker:
    def __init__(self, root, specs_dir="specs", require_ldvh_doc=False):
        self.root = Path(root).resolve()
        raw_specs_dir = Path(specs_dir)
        self.specs_dir = raw_specs_dir.resolve() if raw_specs_dir.is_absolute() else (self.root / raw_specs_dir).resolve()
        self.require_ldvh_doc = require_ldvh_doc

    def scan_files(self):
        files = []
        for pattern in INDEX_INPUT_PATTERNS:
            files.extend(self.specs_dir.glob(pattern))
        return sorted(path.resolve() for path in files if path.is_file())

    def build(self):
        files = self.scan_files()
        docs = []
        sections = []
        relations = []
        mechanisms = []
        members = []
        diagnostics = []
        for path in files:
            parsed = self.parse_file(path)
            docs.append(parsed["doc"])
            sections.extend(parsed["sections"])
            relations.extend(parsed["relations"])
            mechanisms.extend(parsed["mechanisms"])
            if parsed.get("member"):
                members.append(parsed["member"])
            diagnostics.extend(parsed["diagnostics"])
        diagnostics.extend(self.diagnose_cross_document(docs, sections, relations))
        diagnostics.extend(self.diagnose_members(members))
        review_hints = self.build_review_hints(docs, relations)
        return {
            "metadata": {
                "derived": True,
                "source_of_truth": False,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "tool": "code/specs_validate.py",
                "input_patterns": list(INDEX_INPUT_PATTERNS),
                "root": str(self.root),
            },
            "docs": docs,
            "sections": sections,
            "relations": relations,
            "mechanisms": mechanisms,
            "members": members,
            "diagnostics": diagnostics,
            "review_hints": review_hints,
        }

    def parse_file(self, path):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        rel_path = self.relative_path(path)
        content_hash = self.sha256(text)
        headings = self.extract_headings(path, lines, content_hash)
        header = self.extract_header(lines)
        title = self.extract_title(lines)
        doc_number = self.extract_doc_number(path)
        doc_kind = self.infer_doc_kind(path, title, header)
        doc_meta, doc_meta_diagnostics = self.extract_ldvh_doc(path, text)
        member, member_diagnostics = self.extract_ldvh_member(path, text) if self.is_member_candidate(path) else (None, [])
        diagnostics = self.diagnose_document(path, lines, title, header, headings, doc_kind, doc_meta)
        diagnostics.extend(doc_meta_diagnostics)
        diagnostics.extend(self.diagnose_ldvh_doc(path, title, doc_kind, header, doc_meta, member))
        diagnostics.extend(self.diagnose_ldvh_doc_header_boundary(path, header, doc_meta))
        diagnostics.extend(member_diagnostics)
        diagnostics.extend(self.diagnose_member_header_boundary(path, header))
        diagnostics.extend(self.diagnose_member_document(path, member))
        doc_basis = self.doc_meta_paths(doc_meta.get("basis")) if doc_meta else self.extract_paths_from_value(header.get("上位依据"))
        doc_related_specs = self.doc_meta_paths(doc_meta.get("related_specs")) if doc_meta else self.extract_paths_from_value(header.get("相关规范"))
        doc_parent = self.doc_meta_paths(doc_meta.get("parent_doc")) if doc_meta else self.extract_paths_from_value(header.get("所属主文档"))
        return {
            "doc": {
                "path": rel_path,
                "title": title,
                "doc_number": doc_number,
                "doc_kind": doc_kind,
                "created_at": doc_meta.get("created") if doc_meta else header.get("创建日期"),
                "updated_at": doc_meta.get("updated") if doc_meta else header.get("更新日期"),
                "positioning": doc_meta.get("positioning") if doc_meta else header.get("定位"),
                "scope": doc_meta.get("scope") if doc_meta else header.get("适用范围"),
                "parent_doc": doc_parent[0] if doc_parent else None,
                "relation": doc_meta.get("relation") if doc_meta else header.get("关系"),
                "basis": doc_basis,
                "related_specs": doc_related_specs,
                "index_scope": header.get("索引范围"),
                "header": header,
                "ldvh_doc": doc_meta,
                "content_hash": content_hash,
                "parse_status": "ok" if not any(item["severity"] == "error" for item in diagnostics) else "error",
            },
            "sections": headings,
            "relations": self.extract_relations(path, lines, header, content_hash, doc_meta),
            "mechanisms": self.extract_mechanisms(path, lines, content_hash),
            "member": member,
            "diagnostics": diagnostics,
        }

    def extract_title(self, lines):
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) == 1:
                return match.group(2).strip()
        return None

    def extract_header(self, lines):
        header = {}
        for line in lines[:80]:
            stripped = line.strip()
            if stripped == "---" and header:
                break
            match = INDEX_HEADER_FIELD_RE.match(line)
            if match:
                header[match.group(1).strip()] = match.group(2).strip()
        return header

    def extract_headings(self, path, lines, content_hash):
        raw = []
        in_code = False
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            match = HEADING_RE.match(line)
            if not match:
                continue
            level = len(match.group(1))
            if level == 1:
                continue
            title = match.group(2).strip()
            raw.append({"level": level, "title": title, "line_start": line_number})
        sections = []
        stack = []
        for index, item in enumerate(raw):
            line_end = len(lines)
            for later in raw[index + 1 :]:
                if later["level"] <= item["level"]:
                    line_end = later["line_start"] - 1
                    break
            while stack and stack[-1]["level"] >= item["level"]:
                stack.pop()
            parent = stack[-1]["section_number"] if stack else None
            section_number = self.extract_section_number(item["title"])
            record = {
                "path": self.relative_path(path),
                "heading_level": item["level"],
                "section_number": section_number,
                "title": self.strip_section_number(item["title"]),
                "raw_title": item["title"],
                "line_start": item["line_start"],
                "line_end": line_end,
                "parent_section": parent,
                "content_hash": content_hash,
            }
            sections.append(record)
            stack.append({"level": item["level"], "section_number": section_number})
        return sections

    def extract_relations(self, path, lines, header, content_hash, doc_meta=None):
        relations = []
        if doc_meta:
            for field, relation_kind in (("basis", "basis"), ("related_specs", "related_spec"), ("parent_doc", "parent_doc")):
                for target in self.doc_meta_paths(doc_meta.get(field)):
                    relations.append(self.relation_record(path, doc_meta.get("line") or 0, relation_kind, target, content_hash, "ldvh_doc"))
        else:
            for field, relation_kind in (("上位依据", "basis"), ("相关规范", "related_spec"), ("所属主文档", "parent_doc")):
                value = header.get(field)
                if value:
                    for target in self.extract_paths_from_value(value):
                        relations.append(self.relation_record(path, 0, relation_kind, target, content_hash, "header_field"))
        in_code = False
        seen_line_refs = set()
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if stripped.startswith(">"):
                continue
            for target in self.extract_markdown_paths(line):
                key = (line_number, "path", target)
                if key not in seen_line_refs:
                    relations.append(self.relation_record(path, line_number, "path_ref", target, content_hash, "body_path"))
                    seen_line_refs.add(key)
            for match in INDEX_SECTION_REF_RE.finditer(line):
                section = match.group(1)
                key = (line_number, "section", section)
                if key not in seen_line_refs:
                    relations.append(
                        {
                            "source_path": self.relative_path(path),
                            "source_line": line_number,
                            "relation_kind": "section_ref",
                            "target_ref": f"§{section}",
                            "target_path": None,
                            "target_exists": None,
                            "target_section": section,
                            "parse_method": "body_section",
                            "content_hash": content_hash,
                        }
                    )
                    seen_line_refs.add(key)
        return relations

    def extract_mechanisms(self, path, lines, content_hash):
        mechanisms = []
        in_section = False
        in_table = False
        header_seen = False
        in_code = False
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            heading = HEADING_RE.match(line)
            if heading:
                title = heading.group(2).strip()
                in_section = (
                    "规范落地要求" in title
                    or "机制承接关系" in title
                    or "机制落地关系" in title
                    or "机制关系声明" in title
                )
                in_table = False
                header_seen = False
                continue
            if not in_section:
                continue
            if not stripped:
                if in_table:
                    break
                continue
            if not stripped.startswith("|"):
                if in_table:
                    break
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) < 4:
                continue
            if all(set(cell) <= {"-", ":", " "} for cell in cells):
                continue
            if not header_seen:
                header_seen = True
                in_table = True
                continue
            mechanisms.append(
                {
                    "source_doc": self.relative_path(path),
                    "source_line": line_number,
                    "mechanism": self.clean_cell(cells[0]),
                    "entity": self.clean_cell(cells[1]),
                    "relation_type": self.clean_cell(cells[2]),
                    "sync_trigger": self.clean_cell(cells[3]),
                    "landing_requirement": self.clean_cell(cells[0]) if len(cells) >= 5 else None,
                    "requirement_content": self.clean_cell(cells[1]) if len(cells) >= 5 else None,
                    "guarantee_mechanism": self.clean_cell(cells[2]) if len(cells) >= 5 else None,
                    "sync_type": self.clean_cell(cells[3]) if len(cells) >= 5 else None,
                    "landing_trigger": self.clean_cell(cells[4]) if len(cells) >= 5 else None,
                    "content_hash": content_hash,
                }
            )
        return mechanisms

    def diagnose_document(self, path, lines, title, header, sections, doc_kind, doc_meta=None):
        diagnostics = []
        rel_path = self.relative_path(path)
        if not title:
            diagnostics.append(self.diagnostic(rel_path, 1, "error", "MISSING_TITLE", "文档缺少一级标题"))
        required = [] if doc_meta else self.required_header_fields(doc_kind)
        if self.extract_doc_number(path) == "00":
            required = [field for field in required if field != "上位依据"]
        for field in required:
            if not header.get(field):
                diagnostics.append(self.diagnostic(rel_path, 1, "warning", "MISSING_HEADER_FIELD", f"头部字段缺失: {field}"))
        numbers = {}
        for section in sections:
            number = section["section_number"]
            if not number:
                continue
            if number in numbers:
                diagnostics.append(
                    self.diagnostic(rel_path, section["line_start"], "warning", "DUPLICATE_SECTION_NUMBER", f"章节编号重复: §{number}")
                )
            numbers[number] = section["line_start"]
        in_code = False
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            for target in self.extract_markdown_paths(line):
                resolved = self.resolve_target_path(target, path)
                if not resolved.exists():
                    diagnostics.append(
                        self.diagnostic(rel_path, line_number, "warning", "BROKEN_MARKDOWN_PATH", f"Markdown 路径引用不存在: {target}")
                    )
            for match in INDEX_RESEARCH_REF_RE.finditer(line):
                target = match.group(1)
                diagnostics.append(
                    self.diagnostic(rel_path, line_number, "warning", "RESEARCH_REFERENCE_IN_SPEC", f"正式规范不得引用 studies 文档路径: {target}")
                )
            for match in INDEX_DOCS_MATERIAL_REF_RE.finditer(line):
                target = match.group(1)
                diagnostics.append(
                    self.diagnostic(rel_path, line_number, "warning", "DOCS_PATH_REFERENCE_IN_SPEC", f"正式规范不得引用 docs 可变资料路径: {target}")
                )
            for match in INDEX_DOCS_ROOT_ASSET_REF_RE.finditer(line):
                target = match.group(1)
                diagnostics.append(
                    self.diagnostic(rel_path, line_number, "warning", "DOCS_ROOT_ASSET_REFERENCE_IN_SPEC", f"正式规范不得引用 docs 根目录用户资产路径: {target}")
                )
            for match in INDEX_EXTERNAL_URL_RE.finditer(line):
                target = match.group(0)
                normalized_target = target.rstrip(">")
                if normalized_target in INDEX_ALLOWED_EXTERNAL_STANDARD_URLS.get(rel_path, set()):
                    continue
                diagnostics.append(
                    self.diagnostic(rel_path, line_number, "warning", "EXTERNAL_REFERENCE_IN_SPEC", f"正式规范不得引用外部 URL: {target}")
                )
            if doc_kind in {"formal_spec", "subdocument"} and not path.name.startswith("02-"):
                diagnostics.extend(self.diagnose_definition_section_heading(rel_path, line_number, stripped))
                diagnostics.extend(self.diagnose_definition_sentences(rel_path, line_number, stripped))
        return diagnostics


    def diagnose_member_header_boundary(self, path, header):
        if not self.is_member_candidate(path):
            return []
        rel_path = self.relative_path(path)
        diagnostics = []
        for field in sorted(INDEX_LDVH_MEMBER_HEADER_FORBIDDEN_FIELDS):
            if field not in header:
                continue
            diagnostics.append(
                self.diagnostic(
                    rel_path,
                    1,
                    "error",
                    "LDVH_MEMBER_HEADER_FIELD_FORBIDDEN",
                    f"20-39 / 40-59 普通头部不得重复登记成员自描述字段: {field}",
                )
            )
        return diagnostics


    def diagnose_ldvh_doc_header_boundary(self, path, header, doc_meta):
        if not doc_meta:
            return []
        rel_path = self.relative_path(path)
        diagnostics = []
        for field in sorted(INDEX_LDVH_DOC_HEADER_FORBIDDEN_FIELDS):
            if field not in header:
                continue
            diagnostics.append(
                self.diagnostic(
                    rel_path,
                    1,
                    "error",
                    "LDVH_DOC_HEADER_FIELD_FORBIDDEN",
                    f"specs 普通头部不得重复登记 ldvh_doc 文档元信息字段: {field}",
                )
            )
        return diagnostics


    def diagnose_definition_section_heading(self, rel_path, line_number, stripped):
        diagnostics = []
        match = HEADING_RE.match(stripped)
        if not match:
            return diagnostics
        title = self.strip_section_number(match.group(2).strip())
        if title not in INDEX_FORBIDDEN_DEFINITION_SECTION_TITLES:
            return diagnostics
        diagnostics.append(
            self.diagnostic(
                rel_path,
                line_number,
                "warning",
                "FORBIDDEN_TERM_DEFINITION_SECTION",
                f"非 02 术语规范不得设置二次术语定义章节: {title}",
            )
        )
        return diagnostics


    def diagnose_definition_sentences(self, rel_path, line_number, stripped):
        diagnostics = []
        if not stripped or stripped.startswith("#"):
            return diagnostics
        doc_number = self.extract_doc_number(Path(rel_path))
        reported_terms = set()
        for candidate in self.definition_sentence_candidates(stripped):
            for match in INDEX_DEFINITION_SENTENCE_RE.finditer(candidate):
                term = match.group(1).strip("`：:、（）() ")
                if term in reported_terms:
                    continue
                if not term or term in INDEX_DEFINITION_WHITELIST_TERMS or term not in INDEX_GOVERNED_TERMS:
                    continue
                if doc_number in INDEX_ALLOWED_DEFINITION_OWNERS.get(term, set()):
                    continue
                reported_terms.add(term)
                diagnostics.append(
                    self.diagnostic(
                        rel_path,
                        line_number,
                        "warning",
                        "POSSIBLE_DUPLICATE_TERM_DEFINITION",
                        f"非 02 术语规范疑似使用定义句式: {term}",
                    )
                )
        return diagnostics


    def definition_sentence_candidates(self, stripped):
        if not stripped:
            return []
        if stripped.startswith(">"):
            match = INDEX_HEADER_FIELD_RE.match(stripped)
            if match:
                return [match.group(2).strip()]
            return [stripped.lstrip("> ").strip()]
        if stripped.startswith("|"):
            cells = [self.clean_cell(cell) for cell in stripped.strip("|").split("|")]
            return [cell for cell in cells if cell and not all(char in "-: " for char in cell)]
        footnote = INDEX_FOOTNOTE_RE.match(stripped)
        if footnote:
            return [footnote.group(1).strip()]
        return [stripped]


    def diagnose_cross_document(self, docs, sections, relations):
        diagnostics = []
        docs_by_path = {doc["path"]: doc for doc in docs}
        sections_by_path = {}
        for section in sections:
            sections_by_path.setdefault(section.get("path"), []).append(section)
        body_refs = self.body_reference_map(relations)
        diagnostics.extend(self.diagnose_parent_subdocument_registry(docs, docs_by_path, sections_by_path, body_refs))
        for doc in docs:
            diagnostics.extend(self.diagnose_subdocument_contract(doc, docs_by_path))
            related_specs = doc.get("related_specs") or []
            rel_path = doc.get("path")
            for target in related_specs:
                target_path = self.relative_path(self.resolve_target_path(target, self.root / rel_path))
                header_text = " | ".join(str(doc.get("header", {}).get(field, "")) for field in ("定位", "适用范围", "相关规范"))
                if target_path in docs_by_path and any(term in header_text for term in INDEX_REVERSE_RELATED_TERMS) and not self.has_body_reference(relations, rel_path, target_path):
                    diagnostics.append(
                        self.diagnostic(
                            rel_path,
                            1,
                            "warning",
                            "POSSIBLE_REVERSE_RELATED_SPEC",
                            f"相关规范可能基于反向、追溯或可发现性理由登记: {target_path}",
                        )
                    )
        return diagnostics

    def diagnose_parent_subdocument_registry(self, docs, docs_by_path, sections_by_path, body_refs):
        diagnostics = []
        children_by_parent = {}
        for doc in docs:
            if doc.get("doc_kind") != "subdocument":
                continue
            rel_path = doc.get("path")
            for parent_doc in self.extract_paths_from_value(doc.get("parent_doc")):
                parent_path = self.relative_path(self.resolve_target_path(parent_doc, self.root / rel_path))
                children_by_parent.setdefault(parent_path, []).append(rel_path)
        for parent_path, child_paths in sorted(children_by_parent.items()):
            parent = docs_by_path.get(parent_path)
            if not parent:
                continue
            parent_sections = sections_by_path.get(parent_path, [])
            has_boundary_section = any(any(term in section.get("title", "") for term in INDEX_SUBDOCUMENT_BOUNDARY_TITLE_TERMS) for section in parent_sections)
            if not has_boundary_section:
                diagnostics.append(
                    self.diagnostic(
                        parent_path,
                        1,
                        "warning",
                        "PARENT_SUBDOCUMENT_BOUNDARY_SECTION_MISSING",
                        "父规范存在子文档，但正文缺少子文档清单或边界章节",
                    )
                )
            parent_body_refs = body_refs.get(parent_path, set())
            for child_path in sorted(child_paths):
                if child_path not in parent_body_refs:
                    diagnostics.append(
                        self.diagnostic(
                            parent_path,
                            1,
                            "warning",
                            "PARENT_SUBDOCUMENT_NOT_REGISTERED",
                            f"父规范未在正文子文档清单或边界中登记实际子文档: {child_path}",
                        )
                    )
        return diagnostics

    def build_review_hints(self, docs, relations):
        hints = []
        docs_by_path = {doc["path"]: doc for doc in docs}
        body_refs = self.body_reference_map(relations)
        for doc in docs:
            related_specs = doc.get("related_specs") or []
            rel_path = doc.get("path")
            if len(related_specs) > 5:
                hints.append(
                    self.diagnostic(
                        rel_path,
                        1,
                        "info",
                        "POSSIBLE_RELATED_SPEC_OVERLOAD",
                        f"相关规范数量较多，需确认是否均存在真实读取、消费、同步或检查义务: {len(related_specs)}",
                    )
                )
            for target in related_specs:
                target_path = self.relative_path(self.resolve_target_path(target, self.root / rel_path))
                if target_path not in body_refs.get(rel_path, set()):
                    hints.append(
                        self.diagnostic(
                            rel_path,
                            1,
                            "info",
                            "RELATED_SPEC_WITHOUT_BODY_REFERENCE",
                            f"相关规范未在正文中出现路径消费证据: {target_path}",
                        )
                    )
                if target_path in docs_by_path and rel_path in (docs_by_path[target_path].get("related_specs") or []):
                    source_has_body = target_path in body_refs.get(rel_path, set())
                    target_has_body = rel_path in body_refs.get(target_path, set())
                    if not source_has_body or not target_has_body:
                        hints.append(
                            self.diagnostic(
                                rel_path,
                                1,
                                "info",
                                "BIDIRECTIONAL_RELATED_SPEC_WEAK_EVIDENCE",
                                f"双向相关规范缺少双方正文消费证据: {rel_path} <-> {target_path}",
                            )
                        )
        return hints

    def diagnose_subdocument_contract(self, doc, docs_by_path):
        diagnostics = []
        if doc.get("doc_kind") != "subdocument":
            return diagnostics
        rel_path = doc.get("path")
        doc_number = str(doc.get("doc_number") or "")
        parent_docs = self.extract_paths_from_value(doc.get("parent_doc"))
        basis = doc.get("basis") or []
        relation = doc.get("relation")
        if doc_number and "." in doc_number:
            parent_number = doc_number.split(".", 1)[0]
            if not any(item.get("doc_number") == parent_number for item in docs_by_path.values()):
                diagnostics.append(
                    self.diagnostic(
                        rel_path,
                        1,
                        "warning",
                        "SUBDOCUMENT_PARENT_NUMBER_NOT_FOUND",
                        f"子文档编号缺少对应父规范编号: {parent_number}",
                    )
                )
        for parent_doc in parent_docs:
            parent_path = self.relative_path(self.resolve_target_path(parent_doc, self.root / rel_path))
            if parent_path not in docs_by_path:
                diagnostics.append(
                    self.diagnostic(
                        rel_path,
                        1,
                        "warning",
                        "SUBDOCUMENT_PARENT_DOC_NOT_FOUND",
                        f"所属主文档不存在或不在当前 specs 索引中: {parent_doc}",
                    )
                )
            if parent_doc not in basis and parent_path not in [self.relative_path(self.resolve_target_path(item, self.root / rel_path)) for item in basis]:
                diagnostics.append(
                    self.diagnostic(
                        rel_path,
                        1,
                        "warning",
                        "SUBDOCUMENT_BASIS_MISSING_PARENT",
                        f"子文档上位依据未包含所属主文档: {parent_doc}",
                    )
                )
        if relation and relation not in INDEX_ALLOWED_SUBDOCUMENT_RELATIONS:
            diagnostics.append(
                self.diagnostic(
                    rel_path,
                    1,
                    "warning",
                    "SUBDOCUMENT_RELATION_INVALID",
                    f"子文档关系字段不在稳定枚举中: {relation}",
                )
            )
        return diagnostics

    def body_reference_map(self, relations):
        body_refs = {}
        for relation in relations:
            if relation.get("relation_kind") != "path_ref" or relation.get("parse_method") != "body_path":
                continue
            source_path = relation.get("source_path")
            target_path = relation.get("target_path")
            if not source_path or not target_path:
                continue
            body_refs.setdefault(source_path, set()).add(target_path)
        return body_refs

    def extract_ldvh_doc(self, path, text):
        return self.extract_ldvh_block(path, text, "ldvh_doc", "LDVH_DOC_INVALID", "ldvh_doc 必须是映射结构")

    def extract_ldvh_member(self, path, text):
        return self.extract_ldvh_block(path, text, "ldvh_member", "LDVH_MEMBER_INVALID", "ldvh_member 必须是映射结构")

    def extract_ldvh_block(self, path, text, root_key, invalid_code, invalid_message):
        rel_path = self.relative_path(path)
        metadata_text = self.metadata_preamble_text(text)
        for match in INDEX_LDVH_MEMBER_RE.finditer(metadata_text):
            block = match.group(1)
            lines_before = text[:match.start(1)].splitlines()
            line_start = len(lines_before) + 1
            parsed = self.parse_ldvh_member_block(block)
            if parsed is None:
                continue
            payload = parsed.get(root_key)
            if payload is None:
                continue
            if not isinstance(payload, dict):
                return None, [self.diagnostic(rel_path, line_start, "error", invalid_code, invalid_message)]
            normalized = dict(payload)
            normalized["path"] = rel_path
            normalized["line"] = line_start
            normalized["doc_number"] = self.extract_doc_number(path)
            return normalized, []
        return None, []

    def metadata_preamble_text(self, text):
        lines = text.splitlines(keepends=True)
        preamble = []
        for line in lines:
            if line.strip() == "---":
                break
            preamble.append(line)
        return "".join(preamble) if preamble else text

    def parse_ldvh_member_block(self, block):
        raw_lines = block.splitlines()
        root = {}
        current_root_key = None
        current_list_key = None
        for raw_line in raw_lines:
            if not raw_line.strip():
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            stripped = raw_line.strip()
            if stripped.startswith("#"):
                continue
            if indent == 0:
                if not stripped.endswith(":"):
                    return None
                current_root_key = stripped[:-1].strip()
                root[current_root_key] = {}
                current_list_key = None
                continue
            if current_root_key is None:
                return None
            current = root[current_root_key]
            if stripped.startswith("- "):
                if current_list_key is None:
                    return None
                current[current_list_key].append(self.parse_scalar(stripped[2:].strip()))
                continue
            if ":" not in stripped:
                return None
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not value:
                current[key] = []
                current_list_key = key
            else:
                current[key] = self.parse_scalar(value)
                current_list_key = None
        return root if root else None

    def diagnose_ldvh_doc(self, path, title, doc_kind, header, doc_meta, member):
        rel_path = self.relative_path(path)
        if not doc_meta:
            if self.require_ldvh_doc:
                return [self.diagnostic(rel_path, 1, "error", "LDVH_DOC_MISSING", "specs 文档缺少 ldvh_doc 文档自描述")]
            return []
        diagnostics = []
        line = doc_meta.get("line") or 1
        missing_fields = [field for field in INDEX_LDVH_DOC_STANDARD_FIELDS if field not in doc_meta]
        for field in missing_fields:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_FIELD_ABSENT", f"ldvh_doc 标准字段缺失: {field}"))
        required = list(INDEX_LDVH_DOC_NONEMPTY_FIELDS)
        if self.expected_ldvh_doc_kind(path, doc_kind) == "specs_subdocument":
            required.extend(["parent_doc", "relation"])
        for field in required:
            if doc_meta.get(field) in (None, "", []):
                if field == "basis" and self.extract_doc_number(path) == "00":
                    continue
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_FIELD_EMPTY", f"ldvh_doc 字段值为空: {field}"))
        doc_id = str(doc_meta.get("doc_id") or "")
        doc_number = str(self.extract_doc_number(path) or "")
        if doc_id != doc_number:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_ID_MISMATCH", f"ldvh_doc doc_id 与文件编号不一致: {doc_id} != {doc_number}"))
        expected_kind = self.expected_ldvh_doc_kind(path, doc_kind)
        if doc_meta.get("doc_kind") != expected_kind:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_KIND_MISMATCH", f"ldvh_doc doc_kind 与文档类型不一致: {doc_meta.get('doc_kind')} != {expected_kind}"))
        if doc_meta.get("doc_kind") and doc_meta.get("doc_kind") not in INDEX_LDVH_DOC_ALLOWED_KINDS:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_KIND_INVALID", f"ldvh_doc doc_kind 非法: {doc_meta.get('doc_kind')}"))
        if doc_meta.get("status") and doc_meta.get("status") not in INDEX_LDVH_DOC_ALLOWED_STATUS:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_STATUS_INVALID", f"ldvh_doc status 非法: {doc_meta.get('status')}"))
        diagnostics.extend(self.diagnose_ldvh_doc_dates(path, doc_meta))
        canonical_path = doc_meta.get("canonical_path")
        if canonical_path and canonical_path != rel_path:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_CANONICAL_PATH_MISMATCH", f"ldvh_doc canonical_path 与实际路径不一致: {canonical_path} != {rel_path}"))
        if doc_meta.get("title") and title and doc_meta.get("title") != title:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_TITLE_MISMATCH", f"ldvh_doc title 与一级标题不一致: {doc_meta.get('title')} != {title}"))
        if doc_meta.get("created") and header.get("创建日期") and doc_meta.get("created") != header.get("创建日期"):
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_CREATED_MISMATCH", f"ldvh_doc created 与普通头部创建日期不一致: {doc_meta.get('created')} != {header.get('创建日期')}"))
        if doc_meta.get("updated") and header.get("更新日期") and doc_meta.get("updated") != header.get("更新日期"):
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_UPDATED_MISMATCH", f"ldvh_doc updated 与普通头部更新日期不一致: {doc_meta.get('updated')} != {header.get('更新日期')}"))
        if doc_meta.get("positioning") and header.get("定位") and doc_meta.get("positioning") != header.get("定位"):
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_POSITIONING_MISMATCH", "ldvh_doc positioning 与普通头部定位不一致"))
        if doc_meta.get("scope") and header.get("适用范围") and doc_meta.get("scope") != header.get("适用范围"):
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_SCOPE_MISMATCH", "ldvh_doc scope 与普通头部适用范围不一致"))
        if doc_meta.get("parent_doc") and header.get("所属主文档"):
            doc_parent = self.doc_meta_paths(doc_meta.get("parent_doc"))
            header_parent = self.extract_paths_from_value(header.get("所属主文档"))
            if doc_parent != header_parent:
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_PARENT_MISMATCH", f"ldvh_doc parent_doc 与普通头部所属主文档不一致: {doc_parent} != {header_parent}"))
        if doc_meta.get("relation") and header.get("关系") and doc_meta.get("relation") != header.get("关系"):
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_RELATION_MISMATCH", f"ldvh_doc relation 与普通头部关系不一致: {doc_meta.get('relation')} != {header.get('关系')}"))
        if doc_meta.get("basis") is not None and header.get("上位依据"):
            doc_basis = self.doc_meta_paths(doc_meta.get("basis"))
            header_basis = self.extract_paths_from_value(header.get("上位依据"))
            if doc_basis != header_basis:
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_BASIS_MISMATCH", f"ldvh_doc basis 与普通头部上位依据不一致: {doc_basis} != {header_basis}"))
        if doc_meta.get("related_specs") is not None and header.get("相关规范"):
            doc_related = self.doc_meta_paths(doc_meta.get("related_specs"))
            header_related = self.extract_paths_from_value(header.get("相关规范"))
            if doc_related != header_related:
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_RELATED_SPECS_MISMATCH", f"ldvh_doc related_specs 与普通头部相关规范不一致: {doc_related} != {header_related}"))
        if member:
            if str(member.get("spec_id") or "") != doc_id:
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_MEMBER_ID_MISMATCH", f"ldvh_doc doc_id 与 ldvh_member spec_id 不一致: {doc_id} != {member.get('spec_id')}"))
            if member.get("canonical_path") and canonical_path and member.get("canonical_path") != canonical_path:
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_MEMBER_PATH_MISMATCH", f"ldvh_doc canonical_path 与 ldvh_member canonical_path 不一致: {canonical_path} != {member.get('canonical_path')}"))
            expected_member_kind = {"work_model_spec": "work_model", "work_process_spec": "work_process"}.get(doc_meta.get("doc_kind"))
            if expected_member_kind and member.get("kind") != expected_member_kind:
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_MEMBER_KIND_MISMATCH", f"ldvh_doc doc_kind 与 ldvh_member kind 不一致: {doc_meta.get('doc_kind')} != {member.get('kind')}"))
        return diagnostics

    def diagnose_ldvh_doc_dates(self, path, doc_meta):
        diagnostics = []
        rel_path = self.relative_path(path)
        line = doc_meta.get("line") or 1
        parsed_dates = {}
        for field in ("created", "updated"):
            value = doc_meta.get(field)
            if value in (None, ""):
                continue
            value = str(value)
            if not INDEX_LDVH_DOC_DATE_RE.match(value):
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_DATE_INVALID", f"ldvh_doc {field} 日期格式必须为 YYYY-MM-DD: {value}"))
                continue
            try:
                parsed_dates[field] = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_DATE_INVALID", f"ldvh_doc {field} 日期无效: {value}"))
        if parsed_dates.get("created") and parsed_dates.get("updated") and parsed_dates["updated"] < parsed_dates["created"]:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_DOC_UPDATED_BEFORE_CREATED", f"ldvh_doc updated 不能早于 created: {doc_meta.get('updated')} < {doc_meta.get('created')}"))
        return diagnostics

    def doc_meta_paths(self, value):
        if value in (None, "", []):
            return []
        if isinstance(value, list):
            return [self.clean_cell(str(item)) for item in value if str(item).strip()]
        paths = self.extract_paths_from_value(str(value))
        if paths:
            return paths
        cleaned = self.clean_cell(str(value))
        return [cleaned] if cleaned else []

    def parse_scalar(self, value):
        if value == "[]":
            return []
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            return value[1:-1]
        if value in {"true", "false"}:
            return value == "true"
        return value

    def diagnose_member_document(self, path, member):
        rel_path = self.relative_path(path)
        doc_number = self.extract_doc_number(path)
        if not self.is_member_candidate(path):
            return []
        if not member:
            return [self.diagnostic(rel_path, 1, "error", "LDVH_MEMBER_MISSING", "20-39 / 40-59 具体成员主文件缺少 ldvh_member 自描述")]
        diagnostics = []
        line = member.get("line") or 1
        required = self.required_member_fields(member.get("kind"))
        for field in required:
            if member.get(field) in (None, "", []):
                diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_MEMBER_FIELD_MISSING", f"ldvh_member 字段缺失: {field}"))
        spec_id = str(member.get("spec_id") or "")
        if spec_id != str(doc_number):
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_MEMBER_SPEC_ID_MISMATCH", f"ldvh_member spec_id 与文件编号不一致: {spec_id} != {doc_number}"))
        expected_kind = self.expected_member_kind(doc_number)
        if expected_kind and member.get("kind") != expected_kind:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_MEMBER_KIND_MISMATCH", f"ldvh_member kind 与编号区段不一致: {member.get('kind')} != {expected_kind}"))
        canonical_path = member.get("canonical_path")
        if canonical_path and canonical_path != rel_path:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_MEMBER_CANONICAL_PATH_MISMATCH", f"ldvh_member canonical_path 与实际路径不一致: {canonical_path} != {rel_path}"))
        status = member.get("collection_status")
        allowed_statuses = self.allowed_member_statuses(member.get("kind"))
        if status and status not in allowed_statuses:
            diagnostics.append(self.diagnostic(rel_path, line, "error", "LDVH_MEMBER_STATUS_INVALID", f"ldvh_member collection_status 非法: {status}"))
        return diagnostics

    def members_as_collection_entries(self, kind):
        indexes = self.build()
        entries = []
        for member in indexes.get("members", []):
            if member.get("kind") != kind:
                continue
            entries.append(
                {
                    "path": member.get("path"),
                    "line": member.get("line") or 1,
                    "number": str(member.get("spec_id") or ""),
                    "title": member.get("canonical_path") or member.get("path") or "",
                    "type": "具体工作模型规范" if kind == "work_model" else "具体工作流程规范",
                    "status": member.get("collection_status") or "",
                    "source": None,
                    "position": " / ".join(part for part in (member.get("name_en"), member.get("name_zh")) if part),
                    "aliases": [],
                }
            )
        return entries

    def diagnose_members(self, members):
        diagnostics = []
        by_spec_id = {}
        by_path = {}
        for member in members:
            spec_id = str(member.get("spec_id") or "")
            canonical_path = member.get("canonical_path")
            if spec_id:
                by_spec_id.setdefault((member.get("kind"), spec_id), []).append(member)
            if canonical_path:
                by_path.setdefault(canonical_path, []).append(member)
        for (_, spec_id), items in by_spec_id.items():
            if len(items) <= 1:
                continue
            paths = ", ".join(item.get("path", "") for item in items)
            for item in items:
                diagnostics.append(self.diagnostic(item.get("path"), item.get("line") or 1, "error", "LDVH_MEMBER_DUPLICATE_SPEC_ID", f"ldvh_member spec_id 重复: {spec_id} ({paths})"))
        for canonical_path, items in by_path.items():
            if len(items) <= 1:
                continue
            paths = ", ".join(item.get("path", "") for item in items)
            for item in items:
                diagnostics.append(self.diagnostic(item.get("path"), item.get("line") or 1, "error", "LDVH_MEMBER_DUPLICATE_CANONICAL_PATH", f"ldvh_member canonical_path 重复: {canonical_path} ({paths})"))
        diagnostics.extend(self.diagnose_work_model_directory_table(members))
        return diagnostics

    def diagnose_work_model_directory_table(self, members):
        index_path = self.specs_dir / "01-目录说明.md"
        if not index_path.exists():
            return []
        table_entries = self.extract_work_model_directory_table(index_path)
        if not table_entries:
            return []
        diagnostics = []
        table_by_number = {entry["number"]: entry for entry in table_entries}
        active_work_models = {
            str(member.get("spec_id") or ""): member
            for member in members
            if member.get("kind") == "work_model" and member.get("collection_status") == "active"
        }
        for number, member in sorted(active_work_models.items(), key=lambda item: item[0]):
            entry = table_by_number.get(number)
            if not entry:
                diagnostics.append(
                    self.diagnostic(
                        self.relative_path(index_path),
                        1,
                        "error",
                        "WORK_MODEL_DIRECTORY_ENTRY_MISSING",
                        f"01 active 工作模型目录缺少成员: {number} {member.get('name_en') or ''}",
                    )
                )
                continue
            expected_label = self.member_directory_label(member)
            if entry["label"] != expected_label:
                diagnostics.append(
                    self.diagnostic(
                        self.relative_path(index_path),
                        entry["line"],
                        "error",
                        "WORK_MODEL_DIRECTORY_ENTRY_MISMATCH",
                        f"01 active 工作模型目录与成员自描述不一致: {number} {entry['label']} != {expected_label}",
                    )
                )
        for number, entry in sorted(table_by_number.items(), key=lambda item: item[0]):
            if number not in active_work_models:
                diagnostics.append(
                    self.diagnostic(
                        self.relative_path(index_path),
                        entry["line"],
                        "error",
                        "WORK_MODEL_DIRECTORY_ENTRY_STALE",
                        f"01 active 工作模型目录包含非 active 成员编号: {number} {entry['label']}",
                    )
                )
        return diagnostics

    def extract_work_model_directory_table(self, path):
        entries = []
        lines = path.read_text(encoding="utf-8").splitlines()
        in_table = False
        separator_seen = False
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped.startswith("|"):
                if in_table and entries:
                    break
                continue
            cells = [self.clean_cell(cell) for cell in stripped.strip("|").split("|")]
            if len(cells) < 3:
                continue
            if not in_table:
                if tuple(cells[:3]) == INDEX_WORK_MODEL_DIRECTORY_HEADER:
                    in_table = True
                    separator_seen = False
                continue
            if not separator_seen and all(set(cell) <= {"-", ":", " "} for cell in cells[:3]):
                separator_seen = True
                continue
            if not separator_seen:
                continue
            entries.append({"number": cells[0], "label": cells[1], "instance_root": cells[2], "line": line_number})
        return entries

    def member_directory_label(self, member):
        return " / ".join(part for part in (member.get("name_en"), member.get("name_zh")) if part)

    def is_member_candidate(self, path):
        doc_number = self.extract_doc_number(path)
        if not doc_number or "." in doc_number:
            return False
        try:
            number = int(doc_number)
        except ValueError:
            return False
        title = self.extract_title(path.read_text(encoding="utf-8").splitlines()) or ""
        if "迁移待删除" in title:
            return False
        return 20 <= number <= 39 or 40 <= number <= 59

    def expected_member_kind(self, doc_number):
        try:
            number = int(doc_number)
        except (TypeError, ValueError):
            return None
        if 20 <= number <= 39:
            return "work_model"
        if 40 <= number <= 59:
            return "work_process"
        return None

    def expected_ldvh_doc_kind(self, path, doc_kind):
        doc_number = self.extract_doc_number(path)
        try:
            number = int(doc_number) if doc_number and "." not in str(doc_number) else None
        except ValueError:
            number = None
        if number is not None and 20 <= number <= 39:
            return "work_model_spec"
        if number is not None and 40 <= number <= 59:
            return "work_process_spec"
        if doc_kind == "subdocument":
            return "specs_subdocument"
        return "formal_spec"

    def required_member_fields(self, kind):
        common = ["spec_id", "kind", "name_en", "name_zh", "collection_status", "canonical_path", "code_consumption"]
        if kind == "work_model":
            return common + ["instance_root", "schema_anchor", "state_machine_anchor", "human_gate_anchor"]
        if kind == "work_process":
            return common
        return common

    def allowed_member_statuses(self, kind):
        if kind == "work_model":
            return {"active", "candidate", "reserved", "removed"}
        if kind == "work_process":
            return {"active", "planned", "candidate", "reserved", "removed"}
        return {"active", "planned", "candidate", "reserved", "removed"}

    def has_body_reference(self, relations, source_path, target_path):
        for relation in relations:
            if relation.get("source_path") != source_path:
                continue
            if relation.get("target_path") != target_path:
                continue
            if relation.get("relation_kind") == "path_ref" and relation.get("parse_method") == "body_path":
                return True
        return False

    def relation_record(self, path, line_number, relation_kind, target, content_hash, parse_method):
        resolved = self.resolve_target_path(target, path)
        return {
            "source_path": self.relative_path(path),
            "source_line": line_number,
            "relation_kind": relation_kind,
            "target_ref": target,
            "target_path": self.relative_path(resolved) if self.is_inside_root(resolved) else str(resolved),
            "target_exists": resolved.exists(),
            "target_section": None,
            "parse_method": parse_method,
            "content_hash": content_hash,
        }

    def extract_markdown_paths(self, text):
        paths = []
        for match in INDEX_BACKTICK_MD_RE.finditer(text):
            target = match.group(1)
            if not self.is_environment_or_template_path(target):
                paths.append(target)
        for match in INDEX_PLAIN_SPECS_MD_RE.finditer(text):
            target = match.group(1)
            if not self.is_environment_or_template_path(target):
                paths.append(target)
        return sorted(set(paths), key=paths.index)

    def is_environment_or_template_path(self, raw_path):
        raw = str(raw_path).strip()
        return raw.startswith(("~/", "<", ".trae", ".codex")) or raw in {"AGENTS.md", "CLAUDE.md"}

    def extract_paths_from_value(self, value):
        if not value:
            return []
        return self.extract_markdown_paths(value)

    def clean_cell(self, value):
        text = str(value).strip()
        if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
            return text[1:-1]
        return text

    def resolve_target_path(self, raw_path, current_path):
        raw = str(raw_path)
        if raw.startswith("specs/") or raw.startswith("docs/") or raw.startswith("code/docs/"):
            return (self.root / raw).resolve()
        if raw.startswith("./") or raw.startswith("../"):
            return (current_path.parent / raw).resolve()
        if raw == "README.md":
            return (self.root / raw).resolve()
        return (self.specs_dir / raw).resolve()

    def required_header_fields(self, doc_kind):
        if doc_kind == "research":
            return ["创建日期", "定位", "调研边界", "执行效力", "编号归属"]
        if doc_kind == "refs":
            return ["创建日期", "来源", "定位"]
        if doc_kind == "subdocument":
            return ["创建日期", "所属主文档", "关系", "适用范围", "上位依据"]
        return ["创建日期", "定位", "适用范围", "上位依据"]

    def infer_doc_kind(self, path, title, header):
        rel = path.relative_to(self.root)
        parts = rel.parts
        if len(parts) >= 2 and parts[0] == "docs" and parts[1] == "research":
            return "research"
        if len(parts) >= 2 and parts[0] == "docs" and parts[1] == "refs":
            return "refs"
        if len(parts) >= 2 and parts[0] == "specs" and parts[1] == "research":
            return "research"
        if len(parts) >= 2 and parts[0] == "specs" and parts[1] == "refs":
            return "refs"
        doc_number = self.extract_doc_number(path)
        if header.get("所属主文档") or (doc_number and "." in doc_number and parts[0] == "specs"):
            return "subdocument"
        if title and "集合索引" in title:
            return "collection_index"
        return "formal_spec"

    def extract_doc_number(self, path):
        match = INDEX_DOC_NUMBER_RE.match(path.name)
        return match.group(1) if match else None

    def extract_section_number(self, title):
        match = INDEX_NUMBERED_HEADING_RE.match(title)
        return match.group(1) if match else None

    def strip_section_number(self, title):
        return INDEX_NUMBERED_HEADING_RE.sub("", title, count=1).strip()

    def relative_path(self, path):
        try:
            return str(Path(path).resolve().relative_to(self.root))
        except ValueError:
            return str(path)

    def is_inside_root(self, path):
        try:
            Path(path).resolve().relative_to(self.root)
            return True
        except ValueError:
            return False

    def sha256(self, text):
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    def diagnostic(self, path, line, severity, code, message):
        return {"severity": severity, "path": path, "line": line, "code": code, "message": message}


def write_outputs(indexes, out_dir):
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    metadata = indexes["metadata"]
    outputs = {
        "specs-docs-index.json": {"metadata": metadata, "docs": indexes["docs"]},
        "specs-sections-index.json": {"metadata": metadata, "sections": indexes["sections"]},
        "specs-relations-index.json": {"metadata": metadata, "relations": indexes["relations"]},
        "specs-mechanism-index.json": {"metadata": metadata, "mechanisms": indexes["mechanisms"]},
            "specs-members-index.json": {"metadata": metadata, "members": indexes.get("members", [])},
        "specs-diagnostics.json": {"metadata": metadata, "diagnostics": indexes["diagnostics"]},
            "specs-review-hints.json": {"metadata": metadata, "review_hints": indexes.get("review_hints", [])},
    }
    for name, payload in outputs.items():
        (out_path / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return sorted(outputs)


def index_main(root, out=None, fail_on_diagnostics=False, specs_dir="specs"):
    checker = SpecsChecker(root, specs_dir, require_ldvh_doc=True)
    if not checker.specs_dir.exists() and specs_dir == "specs":
        legacy_checker = SpecsChecker(root, "specs", require_ldvh_doc=True)
        if legacy_checker.specs_dir.exists():
            checker = legacy_checker
    if not checker.specs_dir.exists():
        raise SpecsIndexError(f"规范目录不存在: {checker.specs_dir}")
    indexes = checker.build()
    if out:
        written = write_outputs(indexes, out)
        print(f"已生成 specs 文档派生索引与诊断结果: {out}")
        for name in written:
            print(f"- {name}")
    else:
        print(json.dumps(indexes, ensure_ascii=False, indent=2))
    if fail_on_diagnostics and indexes["diagnostics"]:
        return 1
    return 0


def infer_specs_dir_from_paths(paths):
    if not paths:
        return "specs"
    resolved_dirs = []
    for raw_path in paths:
        path = Path(raw_path)
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if rel.parts[:2] == ("docs", "specs"):
            resolved_dirs.append("specs")
        elif rel.parts:
            resolved_dirs.append(rel.parts[0])
    if resolved_dirs and all(item == "specs" for item in resolved_dirs):
        return "specs"
    return "specs"
