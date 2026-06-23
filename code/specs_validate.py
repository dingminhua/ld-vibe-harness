#!/usr/bin/env python3
"""Specs 文档结构、引用完整性和派生索引统一检查工具。"""

import argparse
import os
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))


def _project_root_fast():
    return Path(__file__).resolve().parent.parent


def _default_workspace_root_path_fast():
    project_root = _project_root_fast()
    parent_root = project_root.parent
    if (parent_root / "LDVH-GOVERNED-PROJECTS.yaml").exists():
        return parent_root
    return project_root


def _fast_preflight_main(argv):
    from spec_checks import preflight as preflight_checks

    parser = argparse.ArgumentParser(description="执行受控写入前只读检查，不授权写入。")
    parser.add_argument("--root", default=str(_project_root_fast()), help="项目根目录，默认使用当前工具所在项目。")
    parser.add_argument("--target-path", required=True, help="准备写入的目标路径，可为相对或绝对路径。")
    parser.add_argument("--operation", choices=["create", "update", "delete", "move", "rename"], default="update", help="准备执行的写入类型，默认 update。")
    parser.add_argument("--field-path", default=None, help="可选字段路径；第一版仅暴露降级诊断，不做字段级 Schema 校验。")
    parser.add_argument("--status", default=None, help="可选状态值；第一版仅提示回到对应状态规则。")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")
    args = parser.parse_args(argv)
    return preflight_checks.preflight_main(args.root, args.target_path, args.operation, args.field_path, args.status, args.format)


def _fast_v2_check_main(argv):
    from spec_checks import v2 as v2_checks

    parser = argparse.ArgumentParser(description="生成 active specs 诊断和知识地图派生预览。")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent), help="项目根目录，默认使用当前工具所在项目。")
    parser.add_argument("--specs-dir", default="specs", help="要检查的 v2 规范目录，默认 specs。")
    parser.add_argument("--format", choices=["text", "json"], default="json", help="报告输出格式，默认 json。")
    parser.add_argument("--input-scope", choices=["active_specs", "specs_v2", "all", "history_specs_v1", "governed_projects", "runtime_extensions"], default="active_specs", help="知识地图输入范围，默认 active_specs；specs_v2 保留为兼容别名；runtime_extensions 显式读取固定运行时扩展自描述。Git 历史查询使用原生 Git，不作为知识地图输入范围。")
    parser.add_argument("--layer", choices=["entry", "neighbors", "expand", "raw"], default="entry", help="知识地图渐进读取层级，默认 entry。")
    parser.add_argument("--project-scope", choices=["current_project", "all_governed_projects", "explicit_projects"], default="current_project", help="项目范围，默认 current_project。")
    parser.add_argument("--project", action="append", default=[], help="project_scope=explicit_projects 时指定项目，可重复。")
    parser.add_argument("--start-node", default=None, help="neighbors/expand/raw 层级的起点节点 ID、路径或标题。")
    parser.add_argument("--relation-type", action="append", default=[], help="限制返回的关系类型，可重复。")
    parser.add_argument("--depth", type=int, default=1, help="expand/raw 层级的最大展开深度，默认 1。")
    parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在诊断时返回非零状态。")
    args = parser.parse_args(argv)
    return v2_checks.v2_check_main(
        args.root,
        args.specs_dir,
        args.format,
        args.fail_on_diagnostics,
        input_scope=args.input_scope,
        query_layer=args.layer,
        project_scope=args.project_scope,
        start_node=args.start_node,
        relation_types=args.relation_type,
        depth=args.depth,
        projects=args.project,
    )


def _default_workspace_root_fast(governed_projects_checks):
    env_root = os.environ.get("LDVH_WORKSPACE_ROOT")
    if env_root:
        return Path(env_root)
    project_root = Path(__file__).resolve().parent.parent
    parent_root = project_root.parent
    if (parent_root / governed_projects_checks.GOVERNED_PROJECTS_FILENAME).exists():
        return parent_root
    return project_root


def _fast_governed_projects_main(argv):
    from spec_checks import governed_projects as governed_projects_checks

    parser = argparse.ArgumentParser(description="检查工作区根目录管辖项目配置。")
    parser.add_argument("--root", default=str(_default_workspace_root_fast(governed_projects_checks)), help="工作区根目录，默认自动定位。")
    args = parser.parse_args(argv)
    governed_projects_checks.PROJECT_ROOT = _project_root_fast()
    return governed_projects_checks.main(args.root)


def _fast_deployment_entries_main(argv):
    from spec_checks import deployment_entries as deployment_entries_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="检查固定运行时扩展登记表与承载物自描述是否一致。")
    parser.add_argument("--root", default=str(project_root), help="项目根目录，默认使用当前工具所在项目。")
    args = parser.parse_args(argv)
    deployment_entries_checks.PROJECT_ROOT = project_root
    return deployment_entries_checks.deployment_entries_main(args.root)


def _fast_runtime_projection_main(argv):
    from spec_checks import runtime_projection as runtime_projection_checks

    parser = argparse.ArgumentParser(description="检查项目内运行投影是否存在漂移风险。")
    parser.add_argument("paths", nargs="*", default=None, help="要检查的运行投影文件或目录，默认检查项目内授权运行投影。")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")
    args = parser.parse_args(argv)
    return runtime_projection_checks.main(args.paths, args.format)


def _fast_human_gate_main(argv):
    from spec_checks import human_gate as human_gate_checks

    parser = argparse.ArgumentParser(description="检查 Markdown 中的 Human Gate 记录是否符合 06 最小证据结构。")
    parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/ 和 ldvh-base/。")
    args = parser.parse_args(argv)
    return human_gate_checks.main(args.paths)


def _fast_human_gate_report_main(argv):
    from spec_checks import human_gate as human_gate_checks

    parser = argparse.ArgumentParser(description="生成 Human Gate 证据结构派生报告。")
    parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 docs/ 和 ldvh-base/。")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")
    args = parser.parse_args(argv)
    return human_gate_checks.report_main(args.paths, args.format)


def _fast_field_registry_main(argv):
    from spec_checks import field_registry as field_registry_checks

    parser = argparse.ArgumentParser(description="检查 05.03 字段注册与消费表。")
    parser.add_argument("paths", nargs="*", default=None, help="要检查的 05.03 文件或目录，默认检查 specs/05.03。")
    args = parser.parse_args(argv)
    return field_registry_checks.main(args.paths)


def _fast_doc_main(argv):
    from spec_checks import doc_structure as doc_structure_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="检查 specs Markdown 文档是否符合 03 文档基础规范的章节编号要求。")
    parser.add_argument("paths", nargs="*", default=[str(project_root / "specs")], help="要检查的 Markdown 文件或目录，默认检查 specs/。")
    args = parser.parse_args(argv)
    doc_structure_checks.PROJECT_ROOT = project_root
    return doc_structure_checks.main(args.paths)


def _fast_refs_main(argv):
    from spec_checks import refs as refs_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="检查 specs Markdown 文档中的 § 引用是否存在。")
    parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")
    args = parser.parse_args(argv)
    refs_checks.PROJECT_ROOT = project_root
    refs_checks.SPECS_DIR = project_root / "specs"
    refs_checks.LEGACY_SPECS_DIR = project_root / "docs" / "specs"
    paths = args.paths if args.paths is not None else refs_checks.default_check_paths()
    return refs_checks.main(paths)


def _fast_assurance_main(argv):
    from spec_checks import assurance as assurance_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="检查 specs 正式规范的规范保障要求表。")
    parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")
    args = parser.parse_args(argv)
    assurance_checks.PROJECT_ROOT = project_root
    assurance_checks.FORMAL_SPECS_DIR = project_root / "specs"
    return assurance_checks.main(args.paths)


def _fast_assurance_report_main(argv):
    from spec_checks import assurance_report as assurance_report_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="生成 specs 规范保障要求聚合报告。")
    parser.add_argument("paths", nargs="*", default=None, help="要聚合的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")
    args = parser.parse_args(argv)
    assurance_report_checks.PROJECT_ROOT = project_root
    assurance_report_checks.FORMAL_SPECS_DIR = project_root / "specs"
    assurance_report_checks.DOCS_DIR = project_root / "docs"
    return assurance_report_checks.assurance_report_main(args.paths, args.format)


def _fast_ldvh_assurance_check_main(argv):
    from spec_checks import ldvh_assurance as ldvh_assurance_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="生成 42 LDVH部署与适配检查派生报告。")
    parser.add_argument("--workspace-root", default=str(_default_workspace_root_path_fast()), help="包含 LDVH-GOVERNED-PROJECTS.yaml 的工作区根目录，默认自动定位。")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")
    args = parser.parse_args(argv)
    ldvh_assurance_checks.PROJECT_ROOT = project_root
    ldvh_assurance_checks.SPECS_DIR = project_root / "specs"
    ldvh_assurance_checks.LEGACY_SPECS_DIR = project_root / "docs" / "specs"
    ldvh_assurance_checks.FORMAL_SPECS_DIR = project_root / "specs"
    ldvh_assurance_checks.DOCS_DIR = project_root / "docs"
    return ldvh_assurance_checks.ldvh_assurance_check_main(args.workspace_root, args.format)


def _fast_assurance_plan_main(argv):
    from spec_checks import ldvh_assurance as ldvh_assurance_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="生成只读 assurance-plan 聚合计划视图。")
    parser.add_argument("--workspace-root", default=str(_default_workspace_root_path_fast()), help="工作区根目录，默认自动定位。")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")
    args = parser.parse_args(argv)
    ldvh_assurance_checks.PROJECT_ROOT = project_root
    ldvh_assurance_checks.SPECS_DIR = project_root / "specs"
    ldvh_assurance_checks.LEGACY_SPECS_DIR = project_root / "docs" / "specs"
    ldvh_assurance_checks.FORMAL_SPECS_DIR = project_root / "specs"
    ldvh_assurance_checks.DOCS_DIR = project_root / "docs"
    return ldvh_assurance_checks.assurance_plan_main(args.workspace_root, args.format)


def _fast_web_validate_main(argv):
    from spec_checks import web_validate as web_validate_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="生成 Web Validate 页面只读数据合同。")
    parser.add_argument("--workspace-root", default=str(_default_workspace_root_path_fast()), help="工作区根目录，默认自动定位。")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")
    args = parser.parse_args(argv)
    web_validate_checks.PROJECT_ROOT = project_root
    web_validate_checks.SPECS_DIR = project_root / "specs"
    web_validate_checks.LEGACY_SPECS_DIR = project_root / "docs" / "specs"
    web_validate_checks.FORMAL_SPECS_DIR = project_root / "specs"
    web_validate_checks.DOCS_DIR = project_root / "docs"
    return web_validate_checks.web_validate_main(args.workspace_root, args.format)


def _fast_consistency_main(argv):
    from spec_checks import consistency as consistency_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="检查集合状态消费、工作模型骨架和 02 术语状态一致性。")
    parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/。")
    args = parser.parse_args(argv)
    consistency_checks.PROJECT_ROOT = project_root
    consistency_checks.SPECS_DIR = project_root / "specs"
    return consistency_checks.consistency_main(args.paths)


def _fast_index_main(argv):
    from spec_checks import index as index_checks

    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="生成 specs 文档派生索引和诊断结果（03.01 规范文档剖面）。")
    parser.add_argument("--root", default=str(project_root), help="项目根目录，默认使用当前工具所在项目。")
    parser.add_argument("--specs-dir", default="specs", help="要生成索引的规范目录，默认 specs。")
    parser.add_argument("--out", default=None, help="输出目录；未提供时将完整索引输出到 stdout。")
    parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态。")
    args = parser.parse_args(argv)
    index_checks.PROJECT_ROOT = project_root
    try:
        return index_checks.index_main(args.root, args.out, args.fail_on_diagnostics, args.specs_dir)
    except index_checks.SpecsIndexError as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _fast_all_main(argv):
    project_root = _project_root_fast()
    parser = argparse.ArgumentParser(description="运行 active specs 综合检查。")
    parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/。")
    parser.add_argument("--root", default=str(project_root), help="项目根目录（用于 index 子命令）。")
    parser.add_argument("--workspace-root", default=str(_default_workspace_root_path_fast()), help="工作区根目录（用于 governed-projects 检查），默认自动定位。")
    parser.add_argument("--specs-dir", default=None, help="要生成索引的规范目录；未提供时根据 paths 推断，默认 specs。")
    parser.add_argument("--out", default=None, help="输出目录（用于 index 子命令）；未提供时将完整索引输出到 stdout。")
    parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态（用于 index 子命令）。")
    args = parser.parse_args(argv)
    if args.paths:
        from spec_checks import doc_structure as doc_structure_checks

        doc_structure_checks.PROJECT_ROOT = project_root
        return doc_structure_checks.main(args.paths)

    from spec_checks import v2 as v2_checks

    specs_dir = args.specs_dir or "specs"
    v2_checks.PROJECT_ROOT = project_root
    return v2_checks.v2_check_main(
        args.root,
        specs_dir,
        "text",
        args.fail_on_diagnostics,
        input_scope="active_specs",
        query_layer="entry",
        project_scope="current_project",
    )


if __name__ == "__main__" and len(sys.argv) > 1:
    _FAST_COMMANDS = {
        "preflight": _fast_preflight_main,
        "v2-check": _fast_v2_check_main,
        "governed-projects": _fast_governed_projects_main,
        "deployment-entries": _fast_deployment_entries_main,
        "runtime-projection": _fast_runtime_projection_main,
        "human-gate": _fast_human_gate_main,
        "human-gate-report": _fast_human_gate_report_main,
        "field-registry": _fast_field_registry_main,
        "doc": _fast_doc_main,
        "refs": _fast_refs_main,
        "assurance": _fast_assurance_main,
        "assurance-report": _fast_assurance_report_main,
        "ldvh-assurance-check": _fast_ldvh_assurance_check_main,
        "assurance-plan": _fast_assurance_plan_main,
        "web-validate": _fast_web_validate_main,
        "consistency": _fast_consistency_main,
        "index": _fast_index_main,
        "all": _fast_all_main,
    }
    if sys.argv[1] in _FAST_COMMANDS:
        sys.exit(_FAST_COMMANDS[sys.argv[1]](sys.argv[2:]))

from spec_checks import common as common_checks
from spec_checks import doc_structure as doc_structure_checks
from spec_checks import deployment_entries as deployment_entries_checks
from spec_checks import consistency as consistency_checks
from spec_checks import field_registry as field_registry_checks
from spec_checks import governed_projects as governed_projects_checks
from spec_checks import human_gate as human_gate_checks
from spec_checks import index as index_checks
from spec_checks import assurance as assurance_checks
from spec_checks import ldvh_assurance as ldvh_assurance_checks
from spec_checks import preflight as preflight_checks
from spec_checks import assurance_report as assurance_report_checks
from spec_checks import refs as refs_checks
from spec_checks import runtime_projection as runtime_projection_checks
from spec_checks import web_validate as web_validate_checks
from spec_checks import v2 as v2_checks


# ── 通用常量 ──

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOVERNED_PROJECTS_FILENAME = governed_projects_checks.GOVERNED_PROJECTS_FILENAME


def default_workspace_root():
    env_root = os.environ.get("LDVH_WORKSPACE_ROOT")
    if env_root:
        return Path(env_root)
    parent_root = PROJECT_ROOT.parent
    if (parent_root / GOVERNED_PROJECTS_FILENAME).exists():
        return parent_root
    return PROJECT_ROOT


DEFAULT_WORKSPACE_ROOT = default_workspace_root()
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
DEPLOYMENT_ENTRIES_AI_ENTRY_PATHS = deployment_entries_checks.DEPLOYMENT_ENTRIES_AI_ENTRY_PATHS
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


def sync_field_registry_config():
    field_registry_checks.PROJECT_ROOT = PROJECT_ROOT
    field_registry_checks.SPECS_DIR = SPECS_DIR


def field_registry_check(paths=None):
    sync_field_registry_config()
    return field_registry_checks.check_paths(paths)


def field_registry_main(paths=None):
    sync_field_registry_config()
    return field_registry_checks.main(paths)


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
# assurance — 规范保障要求表检查
# ══════════════════════════════════════════════════════════════════════

ASSURANCE_SECTION_TITLE = assurance_checks.ASSURANCE_SECTION_TITLE
ASSURANCE_REQUIRED_COLUMNS = assurance_checks.ASSURANCE_REQUIRED_COLUMNS
ASSURANCE_ALLOWED_TYPES = assurance_checks.ASSURANCE_ALLOWED_TYPES
ASSURANCE_REPORT_OWNER_AREAS = assurance_report_checks.ASSURANCE_REPORT_OWNER_AREAS
ASSURANCE_REPORT_AREA_LABELS = assurance_report_checks.ASSURANCE_REPORT_AREA_LABELS
ASSURANCE_REPORT_WRITEBACK_AREAS = assurance_report_checks.ASSURANCE_REPORT_WRITEBACK_AREAS
ASSURANCE_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_SUBCATEGORY_LABELS
ASSURANCE_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_DECISION_FLOW_LABELS
ASSURANCE_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_POLICY_FLOW_LABELS
ASSURANCE_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_SUPPORT_FLOW_LABELS
ASSURANCE_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_DIAGNOSTIC_FLOW_LABELS
ASSURANCE_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS = assurance_report_checks.ASSURANCE_REPORT_RUNTIME_PROJECTION_SUBCATEGORY_LABELS
RUNTIME_PROJECTION_REMEDIATION_LABELS = assurance_report_checks.RUNTIME_PROJECTION_REMEDIATION_LABELS
RUNTIME_PROJECTION_REMEDIATION_TERMS = assurance_report_checks.RUNTIME_PROJECTION_REMEDIATION_TERMS
ASSURANCE_REPORT_HUMAN_GATE_DECISION_TERMS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_DECISION_TERMS
ASSURANCE_REPORT_HUMAN_GATE_POLICY_TERMS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_POLICY_TERMS
ASSURANCE_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_POLICY_DISCUSSION_TERMS
ASSURANCE_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_IMPLEMENTATION_TERMS
ASSURANCE_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_CURRENT_RECORD_TERMS
ASSURANCE_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_FUTURE_TRIGGER_TERMS
ASSURANCE_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS = assurance_report_checks.ASSURANCE_REPORT_RUNTIME_PROJECTION_PLATFORM_TERMS
ASSURANCE_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS = assurance_report_checks.ASSURANCE_REPORT_RUNTIME_PROJECTION_THIRD_PARTY_TERMS
ASSURANCE_REPORT_DEGRADED_MARKERS = assurance_report_checks.ASSURANCE_REPORT_DEGRADED_MARKERS
ASSURANCE_REPORT_OPEN_MARKERS = assurance_report_checks.ASSURANCE_REPORT_OPEN_MARKERS
ASSURANCE_REPORT_OPEN_PATTERNS = assurance_report_checks.ASSURANCE_REPORT_OPEN_PATTERNS
ASSURANCE_REPORT_HUMAN_GATE_PATTERNS = assurance_report_checks.ASSURANCE_REPORT_HUMAN_GATE_PATTERNS
ASSURANCE_REPORT_CAPABILITY_CHECKS = assurance_report_checks.ASSURANCE_REPORT_CAPABILITY_CHECKS


def sync_assurance_config():
    assurance_checks.PROJECT_ROOT = PROJECT_ROOT
    assurance_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR


def sync_assurance_report_config():
    assurance_report_checks.PROJECT_ROOT = PROJECT_ROOT
    assurance_report_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    assurance_report_checks.DOCS_DIR = DOCS_DIR
    assurance_report_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def assurance_default_check_paths():
    sync_assurance_config()
    return assurance_checks.default_check_paths()


def assurance_is_formal_spec(path):
    sync_assurance_config()
    return assurance_checks.is_formal_spec(path)


def assurance_strip_section_number(title):
    return assurance_checks.strip_section_number(title)


def assurance_split_cells(line):
    return assurance_checks.split_cells(line)


def assurance_is_separator(cells):
    return assurance_checks.is_separator(cells)


def assurance_clean_cell(value):
    return assurance_checks.clean_cell(value)


def assurance_relative_path(path):
    sync_assurance_config()
    return assurance_checks.assurance_relative_path(path)


def assurance_extract_requirements_file(path):
    sync_assurance_config()
    return assurance_checks.extract_requirements_file(path)


def assurance_report_match_marker(text, markers):
    return assurance_report_checks.assurance_report_match_marker(text, markers)


def assurance_report_infer_status(requirement):
    return assurance_report_checks.assurance_report_infer_status(requirement)


def assurance_report_count_by(requirements, key):
    return assurance_report_checks.assurance_report_count_by(requirements, key)


def assurance_report_is_gap(item):
    return assurance_report_checks.assurance_report_is_gap(item)


def assurance_report_human_gate_subcategory(item):
    return assurance_report_checks.assurance_report_human_gate_subcategory(item)


def assurance_report_human_gate_decision_flow(item):
    return assurance_report_checks.assurance_report_human_gate_decision_flow(item)


def assurance_report_human_gate_policy_flow(item):
    return assurance_report_checks.assurance_report_human_gate_policy_flow(item)


def assurance_report_human_gate_support_flow(item):
    return assurance_report_checks.assurance_report_human_gate_support_flow(item)


def assurance_report_human_gate_diagnostic_flow(item):
    return assurance_report_checks.assurance_report_human_gate_diagnostic_flow(item)


def assurance_report_runtime_projection_subcategory(item):
    return assurance_report_checks.assurance_report_runtime_projection_subcategory(item)


def _classify_runtime_projection_remediation(item):
    return assurance_report_checks._classify_runtime_projection_remediation(item)


def assurance_report_build_gap_categories(requirements, capability_gaps):
    return assurance_report_checks.assurance_report_build_gap_categories(requirements, capability_gaps)


def assurance_report_document_text(paths):
    return assurance_report_checks.assurance_report_document_text(paths)


def assurance_report_terms_present(text, terms):
    return assurance_report_checks.assurance_report_terms_present(text, terms)


def assurance_report_build_capability_gaps(formal_files, runtime_projection_report=None, human_gate_report=None):
    return assurance_report_checks.assurance_report_build_capability_gaps(formal_files, runtime_projection_report, human_gate_report)


def assurance_report_build(paths=None):
    sync_assurance_report_config()
    return assurance_report_checks.assurance_report_build(paths)


def assurance_report_shorten(text, limit=96):
    return assurance_report_checks.assurance_report_shorten(text, limit)


def assurance_report_format_text(report):
    return assurance_report_checks.assurance_report_format_text(report)


def assurance_report_main(paths=None, output_format="text"):
    sync_assurance_report_config()
    return assurance_report_checks.assurance_report_main(paths, output_format)


def assurance_check_file(path):
    sync_assurance_config()
    return assurance_checks.check_file(path)


def assurance_check_paths(paths):
    sync_assurance_config()
    return assurance_checks.check_paths(paths)


def assurance_main(paths):
    sync_assurance_config()
    return assurance_checks.main(paths)


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

def governed_projects_check_root(root):
    return governed_projects_checks.check_root(root)


def governed_projects_main(root):
    governed_projects_checks.PROJECT_ROOT = PROJECT_ROOT
    return governed_projects_checks.main(root)


LDVH_ASSURANCE_CHECK_STATUS_ORDER = ldvh_assurance_checks.LDVH_ASSURANCE_CHECK_STATUS_ORDER
BOOTSTRAP_BASELINE_DEFINITIONS = ldvh_assurance_checks.BOOTSTRAP_BASELINE_DEFINITIONS


def sync_ldvh_assurance_config():
    ldvh_assurance_checks.PROJECT_ROOT = PROJECT_ROOT
    ldvh_assurance_checks.SPECS_DIR = SPECS_DIR
    ldvh_assurance_checks.LEGACY_SPECS_DIR = LEGACY_SPECS_DIR
    ldvh_assurance_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    ldvh_assurance_checks.DOCS_DIR = DOCS_DIR
    ldvh_assurance_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)
    ldvh_assurance_checks.GOVERNED_PROJECTS_FILENAME = GOVERNED_PROJECTS_FILENAME


def ldvh_assurance_check_status(items):
    return ldvh_assurance_checks.ldvh_assurance_check_status(items)


def ldvh_assurance_check_fact_files():
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.ldvh_assurance_check_fact_files()


def ldvh_assurance_check_fact_validate():
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.ldvh_assurance_check_fact_validate()


def ldvh_assurance_check_spec_validate():
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.ldvh_assurance_check_spec_validate()


def ldvh_bootstrap_issue(code, message, path=None, category="Code"):
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.ldvh_bootstrap_issue(code, message, path, category)


def ldvh_bootstrap_baseline_item(item_id, label, status, evidence, categories=None, issues=None):
    return ldvh_assurance_checks.ldvh_bootstrap_baseline_item(item_id, label, status, evidence, categories, issues)


def ldvh_bootstrap_baseline_build(workspace_root, checks, governed_issues, runtime_report, spec_report, remaining_gaps):
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.ldvh_bootstrap_baseline_build(workspace_root, checks, governed_issues, runtime_report, spec_report, remaining_gaps)


def ldvh_assurance_check_build(workspace_root=None):
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.ldvh_assurance_check_build(workspace_root)


def assurance_plan_build(workspace_root=None):
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.assurance_plan_build(workspace_root)


def assurance_plan_format_text(plan):
    return ldvh_assurance_checks.assurance_plan_format_text(plan)


def assurance_plan_main(workspace_root=None, output_format="text"):
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.assurance_plan_main(workspace_root, output_format)


def ldvh_assurance_check_format_text(report):
    return ldvh_assurance_checks.ldvh_assurance_check_format_text(report)


def ldvh_assurance_check_main(workspace_root=None, output_format="text"):
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.ldvh_assurance_check_main(workspace_root, output_format)


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


def web_validate_compact_assurance_check(report):
    return web_validate_checks.web_validate_compact_assurance_check(report)


def web_validate_compact_assurance_report(report):
    return web_validate_checks.web_validate_compact_assurance_report(report)


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


# active specs 诊断与知识地图投影

def sync_v2_config():
    v2_checks.PROJECT_ROOT = PROJECT_ROOT


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
):
    sync_v2_config()
    return v2_checks.v2_check_build(
        root or PROJECT_ROOT,
        specs_dir,
        input_scope=input_scope,
        query_layer=query_layer,
        project_scope=project_scope,
        start_node=start_node,
        relation_types=relation_types,
        depth=depth,
        projects=projects,
    )


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
):
    sync_v2_config()
    return v2_checks.v2_check_main(
        root or PROJECT_ROOT,
        specs_dir,
        output_format,
        fail_on_diagnostics,
        input_scope=input_scope,
        query_layer=query_layer,
        project_scope=project_scope,
        start_node=start_node,
        relation_types=relation_types,
        depth=depth,
        projects=projects,
    )


def sync_preflight_config():
    preflight_checks.PROJECT_ROOT = PROJECT_ROOT


def preflight_build(root=None, target_path=None, operation="update", field_path=None, status=None):
    sync_preflight_config()
    return preflight_checks.preflight_build(root or PROJECT_ROOT, target_path, operation, field_path, status)


def preflight_main(root=None, target_path=None, operation="update", field_path=None, status=None, output_format="text"):
    sync_preflight_config()
    return preflight_checks.preflight_main(root or PROJECT_ROOT, target_path, operation, field_path, status, output_format)


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

    # assurance
    assurance_parser = subparsers.add_parser("assurance", help="检查 specs 正式规范的规范保障要求表。")
    assurance_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")

    # assurance-report
    assurance_report_parser = subparsers.add_parser("assurance-report", help="生成 specs 规范保障要求聚合报告。")
    assurance_report_parser.add_argument("paths", nargs="*", default=None, help="要聚合的 Markdown 文件或目录，默认检查 specs/ 根目录正式规范。")
    assurance_report_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # ldvh-assurance-check
    ldvh_assurance_check_parser = subparsers.add_parser("ldvh-assurance-check", help="生成 42 LDVH部署与适配检查派生报告。")
    ldvh_assurance_check_parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT), help="包含 LDVH-GOVERNED-PROJECTS.yaml 的工作区根目录，默认自动定位。")
    ldvh_assurance_check_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # assurance-plan
    assurance_plan_parser = subparsers.add_parser("assurance-plan", help="生成只读 assurance-plan 聚合计划视图。")
    assurance_plan_parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT), help="工作区根目录，默认自动定位。")
    assurance_plan_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # web-validate
    web_validate_parser = subparsers.add_parser("web-validate", help="生成 Web Validate 页面只读数据合同。")
    web_validate_parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT), help="工作区根目录，默认自动定位。")
    web_validate_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # runtime-projection
    runtime_projection_parser = subparsers.add_parser("runtime-projection", help="检查项目内运行投影是否存在漂移风险。")
    runtime_projection_parser.add_argument("paths", nargs="*", default=None, help="要检查的运行投影文件或目录，默认检查项目内授权运行投影。")
    runtime_projection_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # deployment-entries
    deployment_entries_parser = subparsers.add_parser("deployment-entries", help="检查固定运行时扩展登记表与承载物自描述是否一致。")
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

    # field-registry
    field_registry_parser = subparsers.add_parser("field-registry", help="检查 05.03 字段注册与消费表。")
    field_registry_parser.add_argument("paths", nargs="*", default=None, help="要检查的 05.03 文件或目录，默认检查 specs/05.03。")

    # governed-projects
    governed_projects_parser = subparsers.add_parser("governed-projects", help="检查工作区根目录管辖项目配置。")
    governed_projects_parser.add_argument("--root", default=str(DEFAULT_WORKSPACE_ROOT), help="工作区根目录，默认自动定位。")

    # index
    index_parser = subparsers.add_parser("index", help="生成 specs 文档派生索引和诊断结果（03.01 规范文档剖面）。")
    index_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")
    index_parser.add_argument("--specs-dir", default="specs", help="要生成索引的规范目录，默认 specs。")
    index_parser.add_argument("--out", default=None, help="输出目录；未提供时将完整索引输出到 stdout。")
    index_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 warning 或 error 诊断时返回非零状态。")

    # v2-check
    v2_parser = subparsers.add_parser("v2-check", help="生成 active specs 诊断和知识地图派生预览。")
    v2_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")
    v2_parser.add_argument("--specs-dir", default="specs", help="要检查的 v2 规范目录，默认 specs。")
    v2_parser.add_argument("--format", choices=["text", "json"], default="json", help="报告输出格式，默认 json。")
    v2_parser.add_argument("--input-scope", choices=["active_specs", "specs_v2", "all", "history_specs_v1", "governed_projects", "runtime_extensions"], default="active_specs", help="知识地图输入范围，默认 active_specs；specs_v2 保留为兼容别名；runtime_extensions 显式读取固定运行时扩展自描述。Git 历史查询使用原生 Git，不作为知识地图输入范围。")
    v2_parser.add_argument("--layer", choices=["entry", "neighbors", "expand", "raw"], default="entry", help="知识地图渐进读取层级，默认 entry。")
    v2_parser.add_argument("--project-scope", choices=["current_project", "all_governed_projects", "explicit_projects"], default="current_project", help="项目范围，默认 current_project。")
    v2_parser.add_argument("--project", action="append", default=[], help="project_scope=explicit_projects 时指定项目，可重复。")
    v2_parser.add_argument("--start-node", default=None, help="neighbors/expand/raw 层级的起点节点 ID、路径或标题。")
    v2_parser.add_argument("--relation-type", action="append", default=[], help="限制返回的关系类型，可重复。")
    v2_parser.add_argument("--depth", type=int, default=1, help="expand/raw 层级的最大展开深度，默认 1。")
    v2_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在诊断时返回非零状态。")

    # preflight
    preflight_parser = subparsers.add_parser("preflight", help="执行受控写入前只读检查，不授权写入。")
    preflight_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录，默认使用当前工具所在项目。")
    preflight_parser.add_argument("--target-path", required=True, help="准备写入的目标路径，可为相对或绝对路径。")
    preflight_parser.add_argument("--operation", choices=["create", "update", "delete", "move", "rename"], default="update", help="准备执行的写入类型，默认 update。")
    preflight_parser.add_argument("--field-path", default=None, help="可选字段路径；第一版仅暴露降级诊断，不做字段级 Schema 校验。")
    preflight_parser.add_argument("--status", default=None, help="可选状态值；第一版仅提示回到对应状态规则。")
    preflight_parser.add_argument("--format", choices=["text", "json"], default="text", help="报告输出格式，默认 text。")

    # all
    all_parser = subparsers.add_parser("all", help="运行 active specs 综合检查。")
    all_parser.add_argument("paths", nargs="*", default=None, help="要检查的 Markdown 文件或目录，默认检查 specs/。")
    all_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录（用于 index 子命令）。")
    all_parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT), help="工作区根目录（用于 governed-projects 检查），默认自动定位。")
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

    if command == "assurance":
        return assurance_main(args.paths)

    if command == "assurance-report":
        return assurance_report_main(args.paths, args.format)

    if command == "ldvh-assurance-check":
        return ldvh_assurance_check_main(args.workspace_root, args.format)

    if command == "assurance-plan":
        return assurance_plan_main(args.workspace_root, args.format)

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

    if command == "field-registry":
        return field_registry_main(args.paths)

    if command == "governed-projects":
        return governed_projects_main(args.root)

    if command == "index":
        try:
            return index_main(args.root, args.out, args.fail_on_diagnostics, args.specs_dir)
        except SpecsIndexError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    if command == "v2-check":
        return v2_check_main(
            args.root,
            args.specs_dir,
            args.format,
            args.fail_on_diagnostics,
            input_scope=args.input_scope,
            query_layer=args.layer,
            project_scope=args.project_scope,
            start_node=args.start_node,
            relation_types=args.relation_type,
            depth=args.depth,
            projects=args.project,
        )

    if command == "preflight":
        return preflight_main(
            args.root,
            args.target_path,
            args.operation,
            args.field_path,
            args.status,
            args.format,
        )

    if command == "all":
        if args.paths:
            return doc_main(args.paths)
        specs_dir = args.specs_dir or "specs"
        return v2_check_main(
            args.root,
            specs_dir,
            "text",
            args.fail_on_diagnostics,
            input_scope="active_specs",
            query_layer="entry",
            project_scope="current_project",
        )


if __name__ == "__main__":
    sys.exit(main())
