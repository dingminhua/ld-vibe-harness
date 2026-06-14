#!/usr/bin/env python3
"""Specs 文档结构、引用完整性和派生索引统一检查工具。"""

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from spec_checks import doc_structure as doc_structure_checks
from spec_checks import deployment_entries as deployment_entries_checks
from spec_checks import consistency as consistency_checks
from spec_checks import governed_projects as governed_projects_checks
from spec_checks import human_gate as human_gate_checks
from spec_checks import landing as landing_checks
from spec_checks import ldvh_landing as ldvh_landing_checks
from spec_checks import landing_report as landing_report_checks
from spec_checks import refs as refs_checks
from spec_checks import runtime_projection as runtime_projection_checks
from spec_checks import web_validate as web_validate_checks


# ── 通用常量 ──

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = PROJECT_ROOT / "specs"
LEGACY_SPECS_DIR = PROJECT_ROOT / "docs" / "specs"
DOCS_DIR = PROJECT_ROOT / "docs"
FORMAL_SPECS_DIR = SPECS_DIR
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


# ── 通用数据结构 ──

@dataclass
class Issue:
    path: Path
    line: int
    message: str
    code: str = None

    def format(self, root=None):
        display_path = self.path
        if root:
            try:
                display_path = self.path.relative_to(root)
            except ValueError:
                display_path = self.path
        if self.code:
            return f"{display_path}:{self.line}: [{self.code}] {self.message}"
        return f"{display_path}:{self.line}: {self.message}"


def iter_markdown_files(paths):
    files = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
    return sorted(set(files))


RUNTIME_PROJECTION_DEFAULT_PATHS = list(runtime_projection_checks.RUNTIME_PROJECTION_DEFAULT_PATHS)


def sync_runtime_projection_config():
    runtime_projection_checks.PROJECT_ROOT = PROJECT_ROOT
    runtime_projection_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    runtime_projection_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def runtime_projection_is_project_local(path):
    sync_runtime_projection_config()
    return runtime_projection_checks.is_project_local(path)


def runtime_projection_report_build(paths=None):
    sync_runtime_projection_config()
    return runtime_projection_checks.report_build(paths)


def runtime_projection_main(paths=None, output_format="text"):
    sync_runtime_projection_config()
    return runtime_projection_checks.main(paths, output_format)


DEPLOYMENT_ENTRIES_AI_ENTRY_PATH = deployment_entries_checks.DEPLOYMENT_ENTRIES_AI_ENTRY_PATH
DEPLOYMENT_ENTRIES_SPEC_PATH = deployment_entries_checks.DEPLOYMENT_ENTRIES_SPEC_PATH
DEPLOYMENT_ENTRIES_REQUIRED_ASSETS = deployment_entries_checks.DEPLOYMENT_ENTRIES_REQUIRED_ASSETS
DEPLOYMENT_ENTRIES_FORBIDDEN_TYPES = deployment_entries_checks.DEPLOYMENT_ENTRIES_FORBIDDEN_TYPES


def sync_deployment_entries_config():
    deployment_entries_checks.PROJECT_ROOT = PROJECT_ROOT


def deployment_entries_fixed_asset_section(text):
    return deployment_entries_checks.deployment_entries_fixed_asset_section(text)


def deployment_entries_check(root=None):
    sync_deployment_entries_config()
    return deployment_entries_checks.deployment_entries_check(root)


def deployment_entries_main(root=None):
    sync_deployment_entries_config()
    return deployment_entries_checks.deployment_entries_main(root)


CONSISTENCY_WORK_MODEL_REQUIRED_SECTIONS = consistency_checks.CONSISTENCY_WORK_MODEL_REQUIRED_SECTIONS
CONSISTENCY_NEGATIVE_TERMS = consistency_checks.CONSISTENCY_NEGATIVE_TERMS
CONSISTENCY_DANGEROUS_TERMS = consistency_checks.CONSISTENCY_DANGEROUS_TERMS
CONSISTENCY_RETIRED_REFERENCE_RULES = consistency_checks.CONSISTENCY_RETIRED_REFERENCE_RULES
CONSISTENCY_FORBIDDEN_TEXT_RULES = consistency_checks.CONSISTENCY_FORBIDDEN_TEXT_RULES
CONSISTENCY_04_SERIES_FILES = consistency_checks.CONSISTENCY_04_SERIES_FILES
CONSISTENCY_04_SERIES_ORDER = consistency_checks.CONSISTENCY_04_SERIES_ORDER
CONSISTENCY_04_REQUIRED_TAIL = consistency_checks.CONSISTENCY_04_REQUIRED_TAIL
CONSISTENCY_04_RETIRED_FILES = consistency_checks.CONSISTENCY_04_RETIRED_FILES
CONSISTENCY_WORKFLOW_REQUIRED_SECTIONS = consistency_checks.CONSISTENCY_WORKFLOW_REQUIRED_SECTIONS
CONSISTENCY_INDEX_REQUIRED_SECTIONS = consistency_checks.CONSISTENCY_INDEX_REQUIRED_SECTIONS
CONSISTENCY_COLLECTION_NUMBER_RANGES = consistency_checks.CONSISTENCY_COLLECTION_NUMBER_RANGES
CONSISTENCY_HUMAN_GATE_CHECK_TITLES = consistency_checks.CONSISTENCY_HUMAN_GATE_CHECK_TITLES
CONSISTENCY_BARE_TERMS = consistency_checks.CONSISTENCY_BARE_TERMS
CONSISTENCY_DEPRECATED_EXPRESSIONS = consistency_checks.CONSISTENCY_DEPRECATED_EXPRESSIONS
CONSISTENCY_INDEX_OVERRUN_KEYWORDS = consistency_checks.CONSISTENCY_INDEX_OVERRUN_KEYWORDS
CONSISTENCY_INDEX_FILE_RE = consistency_checks.CONSISTENCY_INDEX_FILE_RE
CONSISTENCY_INDEX_BOUNDARY_TERMS = consistency_checks.CONSISTENCY_INDEX_BOUNDARY_TERMS


def sync_consistency_config():
    consistency_checks.PROJECT_ROOT = PROJECT_ROOT
    consistency_checks.SPECS_DIR = SPECS_DIR
    consistency_checks.CONSISTENCY_WORK_MODEL_REQUIRED_SECTIONS = CONSISTENCY_WORK_MODEL_REQUIRED_SECTIONS
    consistency_checks.CONSISTENCY_NEGATIVE_TERMS = CONSISTENCY_NEGATIVE_TERMS
    consistency_checks.CONSISTENCY_DANGEROUS_TERMS = CONSISTENCY_DANGEROUS_TERMS
    consistency_checks.CONSISTENCY_RETIRED_REFERENCE_RULES = CONSISTENCY_RETIRED_REFERENCE_RULES
    consistency_checks.CONSISTENCY_FORBIDDEN_TEXT_RULES = CONSISTENCY_FORBIDDEN_TEXT_RULES
    consistency_checks.CONSISTENCY_04_SERIES_FILES = CONSISTENCY_04_SERIES_FILES
    consistency_checks.CONSISTENCY_04_SERIES_ORDER = CONSISTENCY_04_SERIES_ORDER
    consistency_checks.CONSISTENCY_04_REQUIRED_TAIL = CONSISTENCY_04_REQUIRED_TAIL
    consistency_checks.CONSISTENCY_04_RETIRED_FILES = CONSISTENCY_04_RETIRED_FILES
    consistency_checks.CONSISTENCY_WORKFLOW_REQUIRED_SECTIONS = CONSISTENCY_WORKFLOW_REQUIRED_SECTIONS
    consistency_checks.CONSISTENCY_INDEX_REQUIRED_SECTIONS = CONSISTENCY_INDEX_REQUIRED_SECTIONS
    consistency_checks.CONSISTENCY_COLLECTION_NUMBER_RANGES = CONSISTENCY_COLLECTION_NUMBER_RANGES
    consistency_checks.CONSISTENCY_HUMAN_GATE_CHECK_TITLES = CONSISTENCY_HUMAN_GATE_CHECK_TITLES
    consistency_checks.CONSISTENCY_BARE_TERMS = CONSISTENCY_BARE_TERMS
    consistency_checks.CONSISTENCY_DEPRECATED_EXPRESSIONS = CONSISTENCY_DEPRECATED_EXPRESSIONS
    consistency_checks.CONSISTENCY_INDEX_OVERRUN_KEYWORDS = CONSISTENCY_INDEX_OVERRUN_KEYWORDS
    consistency_checks.CONSISTENCY_INDEX_FILE_RE = CONSISTENCY_INDEX_FILE_RE
    consistency_checks.CONSISTENCY_INDEX_BOUNDARY_TERMS = CONSISTENCY_INDEX_BOUNDARY_TERMS


def consistency_04_series_issues():
    sync_consistency_config()
    return consistency_checks.consistency_04_series_issues()


def consistency_forbidden_text_issues(paths):
    sync_consistency_config()
    return consistency_checks.consistency_forbidden_text_issues(paths)


def consistency_line_is_index_boundary_context(line):
    sync_consistency_config()
    return consistency_checks.consistency_line_is_index_boundary_context(line)


def consistency_index_overrun_issues(paths):
    sync_consistency_config()
    return consistency_checks.consistency_index_overrun_issues(paths)


def consistency_clean_cell(value):
    return consistency_checks.consistency_clean_cell(value)


def consistency_table_rows(path, heading_title):
    sync_consistency_config()
    return consistency_checks.consistency_table_rows(path, heading_title)


def consistency_collection_entries(path, collection_kind):
    sync_consistency_config()
    return consistency_checks.consistency_collection_entries(path, collection_kind)


def consistency_collection_range_issues(entries, collection_kind):
    sync_consistency_config()
    return consistency_checks.consistency_collection_range_issues(entries, collection_kind)


def consistency_entry_aliases(number, title, position):
    sync_consistency_config()
    return consistency_checks.consistency_entry_aliases(number, title, position)


def consistency_h2_sections(path):
    sync_consistency_config()
    return consistency_checks.consistency_h2_sections(path)


def consistency_work_model_skeleton_issues(entries):
    sync_consistency_config()
    return consistency_checks.consistency_work_model_skeleton_issues(entries)


def consistency_line_has_removed_alias(line, aliases):
    sync_consistency_config()
    return consistency_checks.consistency_line_has_removed_alias(line, aliases)


def consistency_line_is_negative(line):
    sync_consistency_config()
    return consistency_checks.consistency_line_is_negative(line)


def consistency_line_is_dangerous(line):
    sync_consistency_config()
    return consistency_checks.consistency_line_is_dangerous(line)


def consistency_removed_consumption_issues(entries, paths, code):
    sync_consistency_config()
    return consistency_checks.consistency_removed_consumption_issues(entries, paths, code)


def consistency_terminology_status_issues(model_entries, workflow_entries):
    sync_consistency_config()
    return consistency_checks.consistency_terminology_status_issues(model_entries, workflow_entries)


def consistency_retired_semantic_issues(paths):
    sync_consistency_config()
    return consistency_checks.consistency_retired_semantic_issues(paths)


def consistency_workflow_skeleton_issues(workflow_entries):
    sync_consistency_config()
    return consistency_checks.consistency_workflow_skeleton_issues(workflow_entries)


def consistency_index_skeleton_issues(paths):
    sync_consistency_config()
    return consistency_checks.consistency_index_skeleton_issues(paths)


def consistency_human_gate_check_section_issues(paths):
    sync_consistency_config()
    return consistency_checks.consistency_human_gate_check_section_issues(paths)


def consistency_bare_term_issues(paths):
    sync_consistency_config()
    return consistency_checks.consistency_bare_term_issues(paths)


def consistency_deprecated_expression_issues(paths):
    sync_consistency_config()
    return consistency_checks.consistency_deprecated_expression_issues(paths)


def consistency_check(paths=None):
    sync_consistency_config()
    return consistency_checks.consistency_check(paths)


def consistency_main(paths=None):
    sync_consistency_config()
    return consistency_checks.consistency_main(paths)


# ══════════════════════════════════════════════════════════════════════
# doc — 文档编号/标题规范检查
# ══════════════════════════════════════════════════════════════════════

DOC_NUMBERED_HEADING_RE = doc_structure_checks.DOC_NUMBERED_HEADING_RE
DOC_CHINESE_HEADING_RE = doc_structure_checks.DOC_CHINESE_HEADING_RE
DOC_ROMAN_HEADING_RE = doc_structure_checks.DOC_ROMAN_HEADING_RE
DOC_UNNUMBERED_ALLOWED_HEADINGS = doc_structure_checks.DOC_UNNUMBERED_ALLOWED_HEADINGS
Heading = doc_structure_checks.Heading
HeadingNumberState = doc_structure_checks.HeadingNumberState


def sync_doc_structure_config():
    doc_structure_checks.PROJECT_ROOT = PROJECT_ROOT


def doc_parse_heading_number(title):
    return doc_structure_checks.parse_heading_number(title)


def doc_check_file(path):
    return doc_structure_checks.check_file(path)


def doc_check_paths(paths):
    return doc_structure_checks.check_paths(paths)


def doc_main(paths):
    sync_doc_structure_config()
    return doc_structure_checks.main(paths)


# ══════════════════════════════════════════════════════════════════════
# refs — 引用完整性检查
# ══════════════════════════════════════════════════════════════════════

REFS_SECTION_HEADING_RE = refs_checks.REFS_SECTION_HEADING_RE
REFS_SECTION_REF_RE = refs_checks.REFS_SECTION_REF_RE
REFS_EXPLICIT_PATH_RE = refs_checks.REFS_EXPLICIT_PATH_RE
REFS_SHORTHAND_RE = refs_checks.REFS_SHORTHAND_RE
REFS_CHINESE_SECTION_RE = refs_checks.REFS_CHINESE_SECTION_RE
Document = refs_checks.Document


def sync_refs_config():
    refs_checks.PROJECT_ROOT = PROJECT_ROOT
    refs_checks.SPECS_DIR = SPECS_DIR
    refs_checks.LEGACY_SPECS_DIR = LEGACY_SPECS_DIR


def refs_extract_sections(path):
    return refs_checks.extract_sections(path)


def refs_build_document_map(paths):
    sync_refs_config()
    return refs_checks.build_document_map(paths)


def refs_resolve_markdown_path(raw_path, current_path):
    sync_refs_config()
    return refs_checks.resolve_markdown_path(raw_path, current_path)


def refs_resolve_shorthand(prefix, documents):
    sync_refs_config()
    return refs_checks.resolve_shorthand(prefix, documents)


def refs_resolve_parent_document(path, documents):
    sync_refs_config()
    return refs_checks.resolve_parent_document(path, documents)


def refs_default_check_paths():
    sync_refs_config()
    return refs_checks.default_check_paths()


def refs_check_section_target(issues, source_path, line_number, target_path, section, documents, code):
    sync_refs_config()
    refs_checks.check_section_target(issues, source_path, line_number, target_path, section, documents, code)


def refs_check_file(path, documents):
    sync_refs_config()
    return refs_checks.check_file(path, documents)


def refs_check_paths(paths):
    sync_refs_config()
    return refs_checks.check_paths(paths)


def refs_main(paths):
    sync_refs_config()
    return refs_checks.main(paths)


# ══════════════════════════════════════════════════════════════════════
# landing — 规范落地要求表检查
# ══════════════════════════════════════════════════════════════════════

LANDING_SECTION_TITLE = landing_checks.LANDING_SECTION_TITLE
LANDING_REQUIRED_COLUMNS = landing_checks.LANDING_REQUIRED_COLUMNS
LANDING_ALLOWED_TYPES = landing_checks.LANDING_ALLOWED_TYPES
LANDING_REPORT_OWNER_AREAS = landing_report_checks.LANDING_REPORT_OWNER_AREAS
LANDING_REPORT_AREA_LABELS = landing_report_checks.LANDING_REPORT_AREA_LABELS
LANDING_REPORT_WRITEBACK_AREAS = landing_report_checks.LANDING_REPORT_WRITEBACK_AREAS
LANDING_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS
LANDING_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS
LANDING_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS
LANDING_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS
LANDING_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS
LANDING_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS = landing_report_checks.LANDING_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS
RUNTIME_PROJECTION_REMEDIATION_LABELS = landing_report_checks.RUNTIME_PROJECTION_REMEDIATION_LABELS
RUNTIME_PROJECTION_REMEDIATION_TERMS = landing_report_checks.RUNTIME_PROJECTION_REMEDIATION_TERMS
LANDING_REPORT_HUMAN_GATE_DECISION_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_DECISION_TERMS
LANDING_REPORT_HUMAN_GATE_POLICY_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_POLICY_TERMS
LANDING_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS
LANDING_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS
LANDING_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS
LANDING_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS
LANDING_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS = landing_report_checks.LANDING_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS
LANDING_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS = landing_report_checks.LANDING_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS
LANDING_REPORT_DEGRADED_MARKERS = landing_report_checks.LANDING_REPORT_DEGRADED_MARKERS
LANDING_REPORT_OPEN_MARKERS = landing_report_checks.LANDING_REPORT_OPEN_MARKERS
LANDING_REPORT_OPEN_PATTERNS = landing_report_checks.LANDING_REPORT_OPEN_PATTERNS
LANDING_REPORT_HUMAN_GATE_PATTERNS = landing_report_checks.LANDING_REPORT_HUMAN_GATE_PATTERNS
LANDING_REPORT_CAPABILITY_CHECKS = landing_report_checks.LANDING_REPORT_CAPABILITY_CHECKS


def sync_landing_config():
    landing_checks.PROJECT_ROOT = PROJECT_ROOT
    landing_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR


def sync_landing_report_config():
    landing_report_checks.PROJECT_ROOT = PROJECT_ROOT
    landing_report_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    landing_report_checks.DOCS_DIR = DOCS_DIR
    landing_report_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def landing_default_check_paths():
    sync_landing_config()
    return landing_checks.default_check_paths()


def landing_is_formal_spec(path):
    sync_landing_config()
    return landing_checks.is_formal_spec(path)


def landing_strip_section_number(title):
    return landing_checks.strip_section_number(title)


def landing_split_cells(line):
    return landing_checks.split_cells(line)


def landing_is_separator(cells):
    return landing_checks.is_separator(cells)


def landing_clean_cell(value):
    return landing_checks.clean_cell(value)


def landing_relative_path(path):
    sync_landing_config()
    return landing_checks.landing_relative_path(path)


def landing_extract_requirements_file(path):
    sync_landing_config()
    return landing_checks.extract_requirements_file(path)


def landing_report_match_marker(text, markers):
    return landing_report_checks.landing_report_match_marker(text, markers)


def landing_report_infer_status(requirement):
    return landing_report_checks.landing_report_infer_status(requirement)


def landing_report_count_by(requirements, key):
    return landing_report_checks.landing_report_count_by(requirements, key)


def landing_report_is_gap(item):
    return landing_report_checks.landing_report_is_gap(item)


def landing_report_human_gate_subcategory(item):
    return landing_report_checks.landing_report_human_gate_subcategory(item)


def landing_report_human_gate_decision_flow(item):
    return landing_report_checks.landing_report_human_gate_decision_flow(item)


def landing_report_human_gate_policy_flow(item):
    return landing_report_checks.landing_report_human_gate_policy_flow(item)


def landing_report_human_gate_support_flow(item):
    return landing_report_checks.landing_report_human_gate_support_flow(item)


def landing_report_human_gate_diagnostic_flow(item):
    return landing_report_checks.landing_report_human_gate_diagnostic_flow(item)


def landing_report_runtime_projection_subcategory(item):
    return landing_report_checks.landing_report_runtime_projection_subcategory(item)


def _classify_runtime_projection_remediation(item):
    return landing_report_checks._classify_runtime_projection_remediation(item)


def landing_report_build_gap_categories(requirements, capability_gaps):
    return landing_report_checks.landing_report_build_gap_categories(requirements, capability_gaps)


def landing_report_document_text(paths):
    return landing_report_checks.landing_report_document_text(paths)


def landing_report_terms_present(text, terms):
    return landing_report_checks.landing_report_terms_present(text, terms)


def landing_report_build_capability_gaps(formal_files, runtime_projection_report=None, human_gate_report=None):
    return landing_report_checks.landing_report_build_capability_gaps(formal_files, runtime_projection_report, human_gate_report)


def landing_report_build(paths=None):
    sync_landing_report_config()
    return landing_report_checks.landing_report_build(paths)


def landing_report_shorten(text, limit=96):
    return landing_report_checks.landing_report_shorten(text, limit)


def landing_report_format_text(report):
    return landing_report_checks.landing_report_format_text(report)


def landing_report_main(paths=None, output_format="text"):
    sync_landing_report_config()
    return landing_report_checks.landing_report_main(paths, output_format)


def landing_check_file(path):
    sync_landing_config()
    return landing_checks.check_file(path)


def landing_check_paths(paths):
    sync_landing_config()
    return landing_checks.check_paths(paths)


def landing_main(paths):
    sync_landing_config()
    return landing_checks.main(paths)


# ══════════════════════════════════════════════════════════════════════
# human-gate — Human Gate 轻量人类决策记录结构检查
# ══════════════════════════════════════════════════════════════════════

HUMAN_GATE_HEADER_RE = human_gate_checks.HUMAN_GATE_HEADER_RE
HUMAN_GATE_FIELD_RE = human_gate_checks.HUMAN_GATE_FIELD_RE
HUMAN_GATE_FILE_SUFFIXES = human_gate_checks.HUMAN_GATE_FILE_SUFFIXES
HUMAN_GATE_REQUIRED_FIELDS = human_gate_checks.HUMAN_GATE_REQUIRED_FIELDS
HUMAN_GATE_YAML_KEYS = human_gate_checks.HUMAN_GATE_YAML_KEYS


def sync_human_gate_config():
    human_gate_checks.PROJECT_ROOT = PROJECT_ROOT
    human_gate_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    human_gate_checks.DOCS_DIR = DOCS_DIR


def human_gate_default_check_paths():
    sync_human_gate_config()
    return human_gate_checks.default_check_paths()


def human_gate_iter_files(paths):
    sync_human_gate_config()
    return human_gate_checks.iter_files(paths)


def human_gate_normalize_label(label):
    return human_gate_checks.normalize_label(label)


def human_gate_alias_map():
    return human_gate_checks.alias_map()


def human_gate_parse_field_line(line):
    return human_gate_checks.parse_field_line(line)


def human_gate_collect_record(lines, start_index):
    return human_gate_checks.collect_record(lines, start_index)


def human_gate_record_fields(block):
    return human_gate_checks.record_fields(block)


def human_gate_check_record_fields(path, line, fields, field_lines):
    return human_gate_checks.check_record_fields(path, line, fields, field_lines)


def human_gate_check_markdown_file(path):
    return human_gate_checks.check_markdown_file(path)


def human_gate_yaml_records(data):
    return human_gate_checks.yaml_records(data)


def human_gate_yaml_line_map(text):
    return human_gate_checks.yaml_line_map(text)


def human_gate_yaml_record_fields(record):
    return human_gate_checks.yaml_record_fields(record)


def human_gate_check_yaml_file(path):
    return human_gate_checks.check_yaml_file(path)


def human_gate_check_file(path):
    return human_gate_checks.check_file(path)


def human_gate_check_paths(paths):
    return human_gate_checks.check_paths(paths)


def human_gate_count_markdown_records_file(path):
    return human_gate_checks.count_markdown_records_file(path)


def human_gate_count_yaml_records_file(path):
    return human_gate_checks.count_yaml_records_file(path)


def human_gate_count_records_file(path):
    return human_gate_checks.count_records_file(path)


def human_gate_report_build(paths=None):
    sync_human_gate_config()
    return human_gate_checks.report_build(paths)


def human_gate_report_format_text(report):
    return human_gate_checks.report_format_text(report)


def human_gate_report_main(paths=None, output_format="text"):
    sync_human_gate_config()
    return human_gate_checks.report_main(paths, output_format)


def human_gate_main(paths):
    sync_human_gate_config()
    return human_gate_checks.main(paths)


# ══════════════════════════════════════════════════════════════════════
# governed-projects — 工作区根目录管辖项目配置检查
# ══════════════════════════════════════════════════════════════════════

GOVERNED_PROJECTS_FILENAME = governed_projects_checks.GOVERNED_PROJECTS_FILENAME


def governed_projects_check_root(root):
    return governed_projects_checks.check_root(root)


def governed_projects_main(root):
    governed_projects_checks.PROJECT_ROOT = PROJECT_ROOT
    return governed_projects_checks.main(root)


LDVH_LANDING_CHECK_STATUS_ORDER = ldvh_landing_checks.LDVH_LANDING_CHECK_STATUS_ORDER
BOOTSTRAP_BASELINE_DEFINITIONS = ldvh_landing_checks.BOOTSTRAP_BASELINE_DEFINITIONS


def sync_ldvh_landing_config():
    ldvh_landing_checks.PROJECT_ROOT = PROJECT_ROOT
    ldvh_landing_checks.SPECS_DIR = SPECS_DIR
    ldvh_landing_checks.LEGACY_SPECS_DIR = LEGACY_SPECS_DIR
    ldvh_landing_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    ldvh_landing_checks.DOCS_DIR = DOCS_DIR
    ldvh_landing_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)
    ldvh_landing_checks.GOVERNED_PROJECTS_FILENAME = GOVERNED_PROJECTS_FILENAME


def ldvh_landing_check_status(items):
    return ldvh_landing_checks.ldvh_landing_check_status(items)


def ldvh_landing_check_fact_files():
    sync_ldvh_landing_config()
    return ldvh_landing_checks.ldvh_landing_check_fact_files()


def ldvh_landing_check_fact_validate():
    sync_ldvh_landing_config()
    return ldvh_landing_checks.ldvh_landing_check_fact_validate()


def ldvh_landing_check_spec_validate():
    sync_ldvh_landing_config()
    return ldvh_landing_checks.ldvh_landing_check_spec_validate()


def ldvh_bootstrap_issue(code, message, path=None, category="Code"):
    sync_ldvh_landing_config()
    return ldvh_landing_checks.ldvh_bootstrap_issue(code, message, path, category)


def ldvh_bootstrap_baseline_item(item_id, label, status, evidence, categories=None, issues=None):
    return ldvh_landing_checks.ldvh_bootstrap_baseline_item(item_id, label, status, evidence, categories, issues)


def ldvh_bootstrap_baseline_build(workspace_root, checks, governed_issues, runtime_report, spec_report, remaining_gaps):
    sync_ldvh_landing_config()
    return ldvh_landing_checks.ldvh_bootstrap_baseline_build(workspace_root, checks, governed_issues, runtime_report, spec_report, remaining_gaps)


def ldvh_landing_check_build(workspace_root=None):
    sync_ldvh_landing_config()
    return ldvh_landing_checks.ldvh_landing_check_build(workspace_root)


def landing_plan_build(workspace_root=None):
    sync_ldvh_landing_config()
    return ldvh_landing_checks.landing_plan_build(workspace_root)


def landing_plan_format_text(plan):
    return ldvh_landing_checks.landing_plan_format_text(plan)


def landing_plan_main(workspace_root=None, output_format="text"):
    sync_ldvh_landing_config()
    return ldvh_landing_checks.landing_plan_main(workspace_root, output_format)


def ldvh_landing_check_format_text(report):
    return ldvh_landing_checks.ldvh_landing_check_format_text(report)


def ldvh_landing_check_main(workspace_root=None, output_format="text"):
    sync_ldvh_landing_config()
    return ldvh_landing_checks.ldvh_landing_check_main(workspace_root, output_format)


# ══════════════════════════════════════════════════════════════════════
# web-validate — Web Validate 页面只读数据合同
# ══════════════════════════════════════════════════════════════════════

def sync_web_validate_config():
    web_validate_checks.PROJECT_ROOT = PROJECT_ROOT
    web_validate_checks.SPECS_DIR = SPECS_DIR
    web_validate_checks.LEGACY_SPECS_DIR = LEGACY_SPECS_DIR
    web_validate_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    web_validate_checks.DOCS_DIR = DOCS_DIR
    web_validate_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def web_validate_compact_landing_check(report):
    return web_validate_checks.web_validate_compact_landing_check(report)


def web_validate_compact_landing_report(report):
    return web_validate_checks.web_validate_compact_landing_report(report)


def web_validate_compact_human_gate_report(report):
    return web_validate_checks.web_validate_compact_human_gate_report(report)


def web_validate_build(workspace_root=None):
    sync_web_validate_config()
    return web_validate_checks.web_validate_build(workspace_root)


def web_validate_format_text(report):
    return web_validate_checks.web_validate_format_text(report)


def web_validate_main(workspace_root=None, output_format="text"):
    sync_web_validate_config()
    return web_validate_checks.web_validate_main(workspace_root, output_format)


# ══════════════════════════════════════════════════════════════════════
# index — 生成索引
# ══════════════════════════════════════════════════════════════════════

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
INDEX_SECTION_REF_RE = re.compile(r"§([一二三四五六七八九十百千万\d]+(?:\.\d+)*)")
INDEX_DOC_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)?)-")
INDEX_DEFINITION_SENTENCE_RE = re.compile(r"^(?:(?:在本文|在本规范|在本文档)中[，,]?\s*)?(?:(?:[-*]|\d+[.、])\s*)?(?:\*\*)?([^|。；;，,\s`*是]{2,24})(?:\*\*)?\s*(?:是指|定义为|包括且仅包括|指(?!向|引|标|回|令|定|派|出|控|责|南|针|纹|挥|数|甲|望)|是(?!否))")
INDEX_FOOTNOTE_RE = re.compile(r"^\[\^[^\]]+\]:\s*(.+)$")
INDEX_FORBIDDEN_DEFINITION_SECTION_TITLES = {"术语定义", "概念定义", "名词解释"}
INDEX_GOVERNED_TERMS = {
    "LDVH 自身项目", "管辖项目", "管辖项目配置", "LDVH 文档工作区", "规范正文区", "管辖项目文档工作区", "正文区", "studies", "sources",
    "来源", "吸收", "参考与研究材料", "待补齐事项", "正式规范", "资产", "规范资产", "文本能力资产", "Code 能力资产", "Web 能力资产",
    "工作对象事实源", "用户资产", "可变资料区", "候选事项", "索引文档", "说明性索引", "规范型集合索引", "规范落地要求", "能力保障",
    "LDVH 能力资产", "保障机制", "环境入口", "环境适配", "环境能力清单", "适配措施", "适配措施状态", "环境", "AI 开发环境",
    "环境实体", "环境能力", "适配边界", "适配检查", "适配降级", "工作区级入口", "项目级入口", "AI 统一入口", "LDVH 项目事实源",
    "项目接入说明", "能力缺口", "环境缺口", "漂移", "LDVH 运行纪律", "启用", "薄引用", "开发环境", "工作模型", "工作对象", "工作字段",
    "字段内容格式", "对象状态", "集合状态", "检查过程状态", "派生状态", "Change commit", "工作流程", "Code", "Web", "受控写入", "受控轻写入",
    "Rules / Instructions", "Skill", "LDVH 自建 Skill", "LDVH 包装 Skill", "Agent", "Hook / 自动触发", "MCP / 模型上下文协议", "运行闭环", "具体工作流程",
    "行动", "Scenario 识别条件", "适用场景", "步骤", "阶段标签", "Apply", "Verify", "Review", "Recheck", "Gate", "Human Gate 记录", "LDVH落地",
    "环境确认", "LDVH落地与检查", "落地检查报告", "检查", "校验", "验证", "审计", "审阅", "审核", "写入", "回写", "事实源回写",
}
INDEX_DEFINITION_WHITELIST_TERMS = {"本文", "本规范", "00", "02", "Code", "Web", "Human Gate", "Rules", "Skill", "Agent", "Hook", "MCP"}
INDEX_ALLOWED_DEFINITION_OWNERS = {
    "开发环境": {"00"},
    "工作模型": {"00", "05"},
    "字段内容格式": {"00", "05.01"},
    "管辖项目配置": {"03.05"},
    "工作流程": {"00", "06"},
    "Gate": {"06"},
    "事实源回写": {"06", "09"},
}
INDEX_REVERSE_RELATED_TERMS = ("反向", "被下游", "被引用", "谁引用", "可发现性", "追溯", "影响面")


class SpecsIndexError(Exception):
    pass


class SpecsChecker:
    def __init__(self, root, specs_dir="specs"):
        self.root = Path(root).resolve()
        raw_specs_dir = Path(specs_dir)
        self.specs_dir = raw_specs_dir.resolve() if raw_specs_dir.is_absolute() else (self.root / raw_specs_dir).resolve()

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
        diagnostics = []
        for path in files:
            parsed = self.parse_file(path)
            docs.append(parsed["doc"])
            sections.extend(parsed["sections"])
            relations.extend(parsed["relations"])
            mechanisms.extend(parsed["mechanisms"])
            diagnostics.extend(parsed["diagnostics"])
        diagnostics.extend(self.diagnose_cross_document(docs, relations))
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
            "diagnostics": diagnostics,
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
        diagnostics = self.diagnose_document(path, lines, title, header, headings, doc_kind)
        return {
            "doc": {
                "path": rel_path,
                "title": title,
                "doc_number": doc_number,
                "doc_kind": doc_kind,
                "created_at": header.get("创建日期"),
                "updated_at": header.get("更新日期"),
                "positioning": header.get("定位"),
                "scope": header.get("适用范围"),
                "parent_doc": header.get("所属主文档"),
                "relation": header.get("关系"),
                "basis": self.extract_paths_from_value(header.get("上位依据")),
                "related_specs": self.extract_paths_from_value(header.get("相关规范")),
                "index_scope": header.get("索引范围"),
                "header": header,
                "content_hash": content_hash,
                "parse_status": "ok" if not any(item["severity"] == "error" for item in diagnostics) else "error",
            },
            "sections": headings,
            "relations": self.extract_relations(path, lines, header, content_hash),
            "mechanisms": self.extract_mechanisms(path, lines, content_hash),
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

    def extract_relations(self, path, lines, header, content_hash):
        relations = []
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

    def diagnose_document(self, path, lines, title, header, sections, doc_kind):
        diagnostics = []
        rel_path = self.relative_path(path)
        if not title:
            diagnostics.append(self.diagnostic(rel_path, 1, "error", "MISSING_TITLE", "文档缺少一级标题"))
        required = self.required_header_fields(doc_kind)
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
                diagnostics.append(
                    self.diagnostic(rel_path, line_number, "warning", "EXTERNAL_REFERENCE_IN_SPEC", f"正式规范不得引用外部 URL: {target}")
                )
            if doc_kind in {"formal_spec", "subdocument"} and not path.name.startswith("02-"):
                diagnostics.extend(self.diagnose_definition_section_heading(rel_path, line_number, stripped))
                diagnostics.extend(self.diagnose_definition_sentences(rel_path, line_number, stripped))
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


    def diagnose_cross_document(self, docs, relations):
        diagnostics = []
        docs_by_path = {doc["path"]: doc for doc in docs}
        for doc in docs:
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
        "specs-diagnostics.json": {"metadata": metadata, "diagnostics": indexes["diagnostics"]},
    }
    for name, payload in outputs.items():
        (out_path / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return sorted(outputs)


def index_main(root, out=None, fail_on_diagnostics=False, specs_dir="specs"):
    checker = SpecsChecker(root, specs_dir)
    if not checker.specs_dir.exists() and specs_dir == "specs":
        legacy_checker = SpecsChecker(root, "specs")
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


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

def build_parser():
    parser = argparse.ArgumentParser(description="Specs 文档结构、引用完整性和派生索引统一检查工具。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # doc
    doc_parser = subparsers.add_parser("doc", help="检查 specs Markdown 文档是否符合 03 文档基础规范的章节编号要求。")
    doc_parser.add_argument("paths", nargs="*", default=[str(SPECS_DIR)], help="要检查的 Markdown 文件或目录，默认检查 specs/。")

    # refs
    refs_parser = subparsers.add_parser("refs", help="检查 specs Markdown 文档中的 § 引用是否存在。")
    refs_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")

    # landing
    landing_parser = subparsers.add_parser("landing", help="检查 specs 正式规范的规范落地要求表。")
    landing_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")

    # landing-report
    landing_report_parser = subparsers.add_parser("landing-report", help="生成 specs 规范落地要求聚合报告。")
    landing_report_parser.add_argument("paths", nargs="*", default=None, help="要聚合的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")
    landing_report_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # ldvh-landing-check
    ldvh_landing_check_parser = subparsers.add_parser("ldvh-landing-check", help="生成 42 LDVH落地与检查派生报告。")
    ldvh_landing_check_parser.add_argument("--workspace-root", default=str(PROJECT_ROOT), help="包含 LDVH-GOVERNED-PROJECTS.yaml 的工作区根目录，默认项目根。")
    ldvh_landing_check_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # landing-plan
    landing_plan_parser = subparsers.add_parser("landing-plan", help="生成只读 landing-plan 聚合计划视图。")
    landing_plan_parser.add_argument("--workspace-root", default=str(PROJECT_ROOT), help="工作区根目录，默认项目根。")
    landing_plan_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # web-validate
    web_validate_parser = subparsers.add_parser("web-validate", help="生成 Web Validate 页面只读数据合同。")
    web_validate_parser.add_argument("--workspace-root", default=str(PROJECT_ROOT), help="工作区根目录，默认项目根。")
    web_validate_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # runtime-projection
    runtime_projection_parser = subparsers.add_parser("runtime-projection", help="检查项目内运行投影是否存在漂移风险。")
    runtime_projection_parser.add_argument("paths", nargs="*", default=None, help="要检查的运行投影文件或目录，默认检查项目内授权运行投影。")
    runtime_projection_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # deployment-entries
    deployment_entries_parser = subparsers.add_parser("deployment-entries", help="检查 LDVH 能力资产与 04.02 定义是否一致。")
    deployment_entries_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")

    # human-gate
    human_gate_parser = subparsers.add_parser("human-gate", help="检查 Markdown 中的 Human Gate 记录是否符合 06 最小证据结构。")
    human_gate_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/ 和 ldvh-base/。")

    # human-gate-report
    human_gate_report_parser = subparsers.add_parser("human-gate-report", help="生成 Human Gate 证据结构派生报告。")
    human_gate_report_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/ 和 ldvh-base/。")
    human_gate_report_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # consistency
    consistency_parser = subparsers.add_parser("consistency", help="检查集合状态消费、工作模型骨架和 02 术语状态一致性。")
    consistency_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/。")

    # governed-projects
    governed_projects_parser = subparsers.add_parser("governed-projects", help="检查工作区根目录管辖项目配置。")
    governed_projects_parser.add_argument("--root", default=str(PROJECT_ROOT), help="工作区根目录，默认使用当前工具所在项目。")

    # index
    index_parser = subparsers.add_parser("index", help="生成 specs 文档派生索引和诊断结果（03.01 规范文档剖面）。")
    index_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")
    index_parser.add_argument("--specs-dir", default="specs", help="要生成索引的规范目录，默认 specs。")
    index_parser.add_argument("--out", default=None, help="输出目录；未提供时将完整索引输出到 stdout。")
    index_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态。")

    # all
    all_parser = subparsers.add_parser("all", help="运行所有检查（doc + refs + landing + human-gate + index）。")
    all_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/。")
    all_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录（用于 index 子命令）。")
    all_parser.add_argument("--specs-dir", default=None, help="要生成索引的规范目录；未提供时根据 paths 推断，默认 specs。")
    all_parser.add_argument("--out", default=None, help="输出目录（用于 index 子命令）；未提供时将完整索引输出到 stdout。")
    all_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态（用于 index 子命令）。")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    command = args.command

    if command == "doc":
        return doc_main(args.paths)

    if command == "refs":
        paths = args.paths if args.paths is not None else refs_default_check_paths()
        return refs_main(paths)

    if command == "landing":
        return landing_main(args.paths)

    if command == "landing-report":
        return landing_report_main(args.paths, args.format)

    if command == "ldvh-landing-check":
        return ldvh_landing_check_main(args.workspace_root, args.format)

    if command == "landing-plan":
        return landing_plan_main(args.workspace_root, args.format)

    if command == "web-validate":
        return web_validate_main(args.workspace_root, args.format)

    if command == "runtime-projection":
        return runtime_projection_main(args.paths, args.format)

    if command == "deployment-entries":
        return deployment_entries_main(args.root)

    if command == "human-gate":
        return human_gate_main(args.paths)

    if command == "human-gate-report":
        return human_gate_report_main(args.paths, args.format)

    if command == "consistency":
        return consistency_main(args.paths)

    if command == "governed-projects":
        return governed_projects_main(args.root)

    if command == "index":
        try:
            return index_main(args.root, args.out, args.fail_on_diagnostics, args.specs_dir)
        except SpecsIndexError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    if command == "all":
        exit_code = 0
        doc_paths = args.paths if args.paths else [str(SPECS_DIR)]
        # doc
        if doc_main(doc_paths) != 0:
            exit_code = 1
        # refs
        refs_paths = args.paths if args.paths else refs_default_check_paths()
        if refs_main(refs_paths) != 0:
            exit_code = 1
        # landing
        landing_paths = args.paths if args.paths else landing_default_check_paths()
        if landing_main(landing_paths) != 0:
            exit_code = 1
        # human-gate
        human_gate_paths = args.paths if args.paths else human_gate_default_check_paths()
        if human_gate_main(human_gate_paths) != 0:
            exit_code = 1
        # runtime-projection
        if runtime_projection_main(None) != 0:
            exit_code = 1
        # deployment-entries
        if deployment_entries_main(args.root) != 0:
            exit_code = 1
        # consistency
        consistency_paths = args.paths if args.paths else [str(SPECS_DIR)]
        if consistency_main(consistency_paths) != 0:
            exit_code = 1
        # governed-projects
        if governed_projects_main(args.root) != 0:
            exit_code = 1
        # index
        try:
            index_specs_dir = args.specs_dir or infer_specs_dir_from_paths(args.paths)
            if index_main(args.root, args.out, args.fail_on_diagnostics, index_specs_dir) != 0:
                exit_code = 1
        except SpecsIndexError as exc:
            print(str(exc), file=sys.stderr)
            exit_code = 2
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
