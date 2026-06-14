#!/usr/bin/env python3
"""Specs 文档结构、引用完整性和派生索引统一检查工具。"""

import argparse
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from spec_checks import common as common_checks
from spec_checks import doc_structure as doc_structure_checks
from spec_checks import deployment_entries as deployment_entries_checks
from spec_checks import consistency as consistency_checks
from spec_checks import governed_projects as governed_projects_checks
from spec_checks import human_gate as human_gate_checks
from spec_checks import index as index_checks
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
HEADING_RE = common_checks.HEADING_RE
Issue = common_checks.Issue
iter_markdown_files = common_checks.iter_markdown_files


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

INDEX_INPUT_PATTERNS = index_checks.INDEX_INPUT_PATTERNS
INDEX_NUMBERED_HEADING_RE = index_checks.INDEX_NUMBERED_HEADING_RE
INDEX_HEADER_FIELD_RE = index_checks.INDEX_HEADER_FIELD_RE
INDEX_BACKTICK_MD_RE = index_checks.INDEX_BACKTICK_MD_RE
INDEX_PLAIN_SPECS_MD_RE = index_checks.INDEX_PLAIN_SPECS_MD_RE
INDEX_RESEARCH_REF_RE = index_checks.INDEX_RESEARCH_REF_RE
INDEX_DOCS_MATERIAL_REF_RE = index_checks.INDEX_DOCS_MATERIAL_REF_RE
INDEX_DOCS_ROOT_ASSET_REF_RE = index_checks.INDEX_DOCS_ROOT_ASSET_REF_RE
INDEX_EXTERNAL_URL_RE = index_checks.INDEX_EXTERNAL_URL_RE
INDEX_SECTION_REF_RE = index_checks.INDEX_SECTION_REF_RE
INDEX_DOC_NUMBER_RE = index_checks.INDEX_DOC_NUMBER_RE
INDEX_DEFINITION_SENTENCE_RE = index_checks.INDEX_DEFINITION_SENTENCE_RE
INDEX_FOOTNOTE_RE = index_checks.INDEX_FOOTNOTE_RE
INDEX_FORBIDDEN_DEFINITION_SECTION_TITLES = index_checks.INDEX_FORBIDDEN_DEFINITION_SECTION_TITLES
INDEX_GOVERNED_TERMS = index_checks.INDEX_GOVERNED_TERMS
INDEX_DEFINITION_WHITELIST_TERMS = index_checks.INDEX_DEFINITION_WHITELIST_TERMS
INDEX_ALLOWED_DEFINITION_OWNERS = index_checks.INDEX_ALLOWED_DEFINITION_OWNERS
INDEX_REVERSE_RELATED_TERMS = index_checks.INDEX_REVERSE_RELATED_TERMS
SpecsIndexError = index_checks.SpecsIndexError
SpecsChecker = index_checks.SpecsChecker


def sync_index_config():
    index_checks.PROJECT_ROOT = PROJECT_ROOT
    index_checks.INDEX_INPUT_PATTERNS = INDEX_INPUT_PATTERNS
    index_checks.INDEX_NUMBERED_HEADING_RE = INDEX_NUMBERED_HEADING_RE
    index_checks.INDEX_HEADER_FIELD_RE = INDEX_HEADER_FIELD_RE
    index_checks.INDEX_BACKTICK_MD_RE = INDEX_BACKTICK_MD_RE
    index_checks.INDEX_PLAIN_SPECS_MD_RE = INDEX_PLAIN_SPECS_MD_RE
    index_checks.INDEX_RESEARCH_REF_RE = INDEX_RESEARCH_REF_RE
    index_checks.INDEX_DOCS_MATERIAL_REF_RE = INDEX_DOCS_MATERIAL_REF_RE
    index_checks.INDEX_DOCS_ROOT_ASSET_REF_RE = INDEX_DOCS_ROOT_ASSET_REF_RE
    index_checks.INDEX_EXTERNAL_URL_RE = INDEX_EXTERNAL_URL_RE
    index_checks.INDEX_SECTION_REF_RE = INDEX_SECTION_REF_RE
    index_checks.INDEX_DOC_NUMBER_RE = INDEX_DOC_NUMBER_RE
    index_checks.INDEX_DEFINITION_SENTENCE_RE = INDEX_DEFINITION_SENTENCE_RE
    index_checks.INDEX_FOOTNOTE_RE = INDEX_FOOTNOTE_RE
    index_checks.INDEX_FORBIDDEN_DEFINITION_SECTION_TITLES = INDEX_FORBIDDEN_DEFINITION_SECTION_TITLES
    index_checks.INDEX_GOVERNED_TERMS = INDEX_GOVERNED_TERMS
    index_checks.INDEX_DEFINITION_WHITELIST_TERMS = INDEX_DEFINITION_WHITELIST_TERMS
    index_checks.INDEX_ALLOWED_DEFINITION_OWNERS = INDEX_ALLOWED_DEFINITION_OWNERS
    index_checks.INDEX_REVERSE_RELATED_TERMS = INDEX_REVERSE_RELATED_TERMS


def write_outputs(indexes, out_dir):
    return index_checks.write_outputs(indexes, out_dir)


def index_main(root, out=None, fail_on_diagnostics=False, specs_dir="specs"):
    sync_index_config()
    return index_checks.index_main(root, out, fail_on_diagnostics, specs_dir)


def infer_specs_dir_from_paths(paths):
    sync_index_config()
    return index_checks.infer_specs_dir_from_paths(paths)


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
