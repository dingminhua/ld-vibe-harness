"""LDVH landing check and read-only landing plan reports."""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .common import iter_markdown_files
from . import doc_structure as doc_structure_checks
from . import governed_projects as governed_projects_checks
from . import landing as landing_checks
from . import landing_report as landing_report_checks
from . import refs as refs_checks


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = PROJECT_ROOT / "specs"
LEGACY_SPECS_DIR = PROJECT_ROOT / "docs" / "specs"
FORMAL_SPECS_DIR = SPECS_DIR
DOCS_DIR = PROJECT_ROOT / "docs"
RUNTIME_PROJECTION_DEFAULT_PATHS = list(landing_report_checks.RUNTIME_PROJECTION_DEFAULT_PATHS)
GOVERNED_PROJECTS_FILENAME = governed_projects_checks.GOVERNED_PROJECTS_FILENAME

RUNTIME_PROJECTION_REMEDIATION_LABELS = landing_report_checks.RUNTIME_PROJECTION_REMEDIATION_LABELS
LDVH_LANDING_CHECK_STATUS_ORDER = {"closed": 0, "degraded": 1, "open": 2, "blocked": 3}


def sync_doc_structure_config():
    doc_structure_checks.PROJECT_ROOT = PROJECT_ROOT


def sync_refs_config():
    refs_checks.PROJECT_ROOT = PROJECT_ROOT
    refs_checks.SPECS_DIR = SPECS_DIR
    refs_checks.LEGACY_SPECS_DIR = LEGACY_SPECS_DIR


def sync_landing_config():
    landing_checks.PROJECT_ROOT = PROJECT_ROOT
    landing_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR


def sync_landing_report_config():
    landing_report_checks.PROJECT_ROOT = PROJECT_ROOT
    landing_report_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    landing_report_checks.DOCS_DIR = DOCS_DIR
    landing_report_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def sync_governed_projects_config():
    governed_projects_checks.PROJECT_ROOT = PROJECT_ROOT


def doc_check_paths(paths):
    sync_doc_structure_config()
    return doc_structure_checks.check_paths(paths)


def refs_default_check_paths():
    sync_refs_config()
    return refs_checks.default_check_paths()


def refs_check_paths(paths):
    sync_refs_config()
    return refs_checks.check_paths(paths)


def landing_check_paths(paths):
    sync_landing_config()
    return landing_checks.check_paths(paths)


def landing_default_check_paths():
    sync_landing_config()
    return landing_checks.default_check_paths()


def landing_relative_path(path):
    sync_landing_config()
    return landing_checks.landing_relative_path(path)


def landing_report_count_by(items, key):
    return landing_report_checks.landing_report_count_by(items, key)


def landing_report_is_gap(item):
    return landing_report_checks.landing_report_is_gap(item)


def landing_report_build(paths=None):
    sync_landing_report_config()
    return landing_report_checks.landing_report_build(paths)


def classify_runtime_projection_remediation(item):
    return landing_report_checks._classify_runtime_projection_remediation(item)


def governed_projects_check_root(root):
    sync_governed_projects_config()
    return governed_projects_checks.check_root(root)


def ldvh_landing_check_status(items):
    status = "closed"
    for item in items:
        item_status = item.get("status", "closed")
        if LDVH_LANDING_CHECK_STATUS_ORDER.get(item_status, 0) > LDVH_LANDING_CHECK_STATUS_ORDER.get(status, 0):
            status = item_status
    return status


def ldvh_landing_check_fact_files():
    facts_dir = PROJECT_ROOT / "ldvh-base"
    if not facts_dir.exists():
        return []
    return sorted(facts_dir.rglob("*.yaml"))


def ldvh_landing_check_fact_validate():
    fact_files = ldvh_landing_check_fact_files()
    if not fact_files:
        return {
            "status": "degraded",
            "issue_count": 0,
            "error_count": 0,
            "warning_count": 0,
            "checked_file_count": 0,
            "evidence": "no ldvh-base YAML fact files found in project scope",
            "issues": [],
        }
    command = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "fact_validate.py"),
        *[str(path) for path in fact_files],
        "--format",
        "json",
    ]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    try:
        payload = json.loads(completed.stdout)
        summary = payload.get("summary", {})
        issues = payload.get("issues", [])
        errors = int(summary.get("errors", 0))
        warnings = int(summary.get("warnings", 0))
        status = "closed"
        if errors or completed.returncode in {1, 2}:
            status = "open"
        elif warnings:
            status = "degraded"
        return {
            "status": status,
            "issue_count": len(issues),
            "error_count": errors,
            "warning_count": warnings,
            "checked_file_count": int(summary.get("files", len(fact_files))),
            "evidence": f"fact_validate checked {summary.get('files', len(fact_files))} fact files, errors: {errors}, warnings: {warnings}",
            "issues": issues,
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        return {
            "status": "open",
            "issue_count": 1,
            "error_count": 1,
            "warning_count": 0,
            "checked_file_count": len(fact_files),
            "evidence": "fact_validate output could not be parsed as JSON",
            "issues": [
                {
                    "level": "error",
                    "code": "FACT_VALIDATE_OUTPUT_INVALID",
                    "message": completed.stderr.strip() or completed.stdout.strip() or "fact_validate failed without parseable output",
                    "path": str(PROJECT_ROOT / "ldvh-base"),
                }
            ],
        }


def ldvh_landing_check_spec_validate():
    doc_issues = doc_check_paths([str(SPECS_DIR)])
    refs_issues = refs_check_paths(refs_default_check_paths())
    landing_issues = landing_check_paths(landing_default_check_paths())
    issues = doc_issues + refs_issues + landing_issues
    return {
        "status": "open" if issues else "closed",
        "issue_count": len(issues),
        "doc_issue_count": len(doc_issues),
        "refs_issue_count": len(refs_issues),
        "landing_issue_count": len(landing_issues),
        "checked_file_count": len(iter_markdown_files([str(SPECS_DIR)])),
        "evidence": f"spec checks found doc={len(doc_issues)}, refs={len(refs_issues)}, landing={len(landing_issues)} issues",
        "issues": [
            {
                "source": landing_relative_path(issue.path),
                "line": issue.line,
                "code": issue.code,
                "message": issue.message,
            }
            for issue in issues
        ],
    }


BOOTSTRAP_BASELINE_DEFINITIONS = [
    ("specs_integrity", "specs 完整性检查"),
    ("asset_directories", "资产目录检查"),
    ("governed_projects_config", "管辖项目配置检查"),
    ("work_model_workflow_indexes", "工作模型和工作流程索引检查"),
    ("environment_matrix", "环境入口与能力资产检查"),
    ("runtime_projection_entry", "运行投影入口检查"),
    ("code_self_check", "Code 自检"),
    ("web_asset", "Web 资产检查"),
    ("report_structure", "42 报告结构输出"),
    ("gap_classification_routing", "缺口分类与分流"),
]


def ldvh_bootstrap_issue(code, message, path=None, category="Code"):
    return {
        "code": code,
        "message": message,
        "path": landing_relative_path(path) if path else None,
        "category": category,
    }


def ldvh_bootstrap_baseline_item(item_id, label, status, evidence, categories=None, issues=None):
    issues = issues or []
    return {
        "id": item_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "issue_count": len(issues),
        "gap_categories": sorted(set(categories or [issue.get("category") for issue in issues if issue.get("category")])) or [],
        "issues": issues,
    }


def ldvh_bootstrap_baseline_build(workspace_root, checks, governed_issues, runtime_report, spec_report, remaining_gaps):
    workspace_root = Path(workspace_root)
    items = []

    items.append(ldvh_bootstrap_baseline_item(
        "specs_integrity",
        "specs 完整性检查",
        spec_report["status"],
        spec_report["evidence"],
        ["规范"] if spec_report["status"] != "closed" else [],
        spec_report.get("issues", []),
    ))

    required_assets = [
        (PROJECT_ROOT / "specs", "规范资产", "规范"),
        (PROJECT_ROOT / "code", "Code 能力资产", "Code"),
        (PROJECT_ROOT / "tests", "测试证明", "Code"),
        (PROJECT_ROOT / "web", "Web 能力资产", "Web"),
        (PROJECT_ROOT / "ldvh-base", "工作对象事实源", "事实源"),
        (PROJECT_ROOT / "rules" / "LDVH-WORKSPACE-ENTRY.md", "工作区运行投影入口", "环境承接"),
        (PROJECT_ROOT / "rules" / "LDVH-MAINTAINER-ENTRY.md", "LDVH 维护运行投影入口", "环境承接"),
        (PROJECT_ROOT / "rules" / "LDVH-AI-ENTRY.md", "兼容运行投影入口", "环境承接"),
    ]
    asset_issues = [
        ldvh_bootstrap_issue("BOOTSTRAP_ASSET_MISSING", f"缺少{label}: {landing_relative_path(path)}", path, category)
        for path, label, category in required_assets
        if not path.exists()
    ]
    items.append(ldvh_bootstrap_baseline_item(
        "asset_directories",
        "资产目录检查",
        "open" if asset_issues else "closed",
        f"checked {len(required_assets)} required asset paths",
        None,
        asset_issues,
    ))

    items.append(ldvh_bootstrap_baseline_item(
        "governed_projects_config",
        "管辖项目配置检查",
        "open" if governed_issues else "closed",
        f"checked {landing_relative_path(workspace_root / GOVERNED_PROJECTS_FILENAME)}",
        ["事实源"] if governed_issues else [],
        [
            ldvh_bootstrap_issue(issue.code, issue.message, issue.path, "事实源")
            for issue in governed_issues
        ],
    ))

    index_paths = [SPECS_DIR / "20-工作模型集合索引.md", SPECS_DIR / "40-工作流程集合索引.md"]
    index_issues = [
        ldvh_bootstrap_issue("BOOTSTRAP_INDEX_MISSING", f"缺少索引文件: {landing_relative_path(path)}", path, "规范")
        for path in index_paths
        if not path.exists()
    ]
    items.append(ldvh_bootstrap_baseline_item(
        "work_model_workflow_indexes",
        "工作模型和工作流程索引检查",
        "open" if index_issues else "closed",
        "checked 20/40 index files",
        None,
        index_issues,
    ))

    capability_path = SPECS_DIR / "04.02-LDVH能力资产与落地保障规范.md"
    environment_path = SPECS_DIR / "04.03-环境入口适配与部署规范.md"
    matrix_issues = []
    if not capability_path.exists():
        matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_CAPABILITY_SPEC_MISSING", "缺少 LDVH 能力资产规范文件", capability_path, "环境承接"))
    else:
        capability_text = capability_path.read_text(encoding="utf-8")
        for asset_type in ["Rules 资产", "Skill 资产", "Agent 资产", "Hook 资产"]:
            if asset_type not in capability_text:
                matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_CAPABILITY_ASSET_MISSING", f"能力资产规范缺少固定资产类型: {asset_type}", capability_path, "环境承接"))
    if not environment_path.exists():
        matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_ENV_ENTRY_SPEC_MISSING", "缺少环境入口适配与部署规范文件", environment_path, "环境承接"))
    else:
        environment_text = environment_path.read_text(encoding="utf-8")
        for environment in ["Trae CN", "Trae 国际版", "Codex App"]:
            if environment not in environment_text:
                matrix_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_ENV_ENTRY_MISSING", f"环境入口适配规范缺少入口: {environment}", environment_path, "环境承接"))
    items.append(ldvh_bootstrap_baseline_item(
        "environment_matrix",
        "环境入口与能力资产检查",
        "open" if matrix_issues else "closed",
        "checked 04.02 capability assets and 04.03 environment entries",
        None,
        matrix_issues,
    ))

    items.append(ldvh_bootstrap_baseline_item(
        "runtime_projection_entry",
        "运行投影入口检查",
        runtime_report["summary"]["status"],
        f"runtime-projection checked {runtime_report['metadata']['checked_file_count']} project-local files",
        ["环境承接"] if runtime_report["summary"]["status"] != "closed" else [],
        runtime_report.get("issues", []),
    ))

    code_paths = [PROJECT_ROOT / "code" / "specs_validate.py", PROJECT_ROOT / "tests" / "code" / "test_specs_validate.py"]
    code_issues = [
        ldvh_bootstrap_issue("BOOTSTRAP_CODE_SELF_CHECK_MISSING", f"缺少 Code 自检关键文件: {landing_relative_path(path)}", path, "Code")
        for path in code_paths
        if not path.exists()
    ]
    items.append(ldvh_bootstrap_baseline_item(
        "code_self_check",
        "Code 自检",
        "open" if code_issues else "closed",
        "checked specs_validate.py and tests/code/test_specs_validate.py presence",
        None,
        code_issues,
    ))

    web_paths = [PROJECT_ROOT / "web", PROJECT_ROOT / "web" / "api", PROJECT_ROOT / "web" / "src"]
    web_issues = [
        ldvh_bootstrap_issue("BOOTSTRAP_WEB_ASSET_MISSING", f"缺少 Web 资产路径: {landing_relative_path(path)}", path, "Web")
        for path in web_paths
        if not path.exists()
    ]
    items.append(ldvh_bootstrap_baseline_item(
        "web_asset",
        "Web 资产检查",
        "open" if web_issues else "closed",
        "checked Web asset paths without requiring Web runtime",
        None,
        web_issues,
    ))

    required_report_keys = {"metadata", "summary", "checks", "remaining_gaps"}
    present_report_keys = {"metadata", "summary", "checks", "remaining_gaps"}
    report_issues = [] if required_report_keys <= present_report_keys else [ldvh_bootstrap_issue("BOOTSTRAP_REPORT_STRUCTURE_MISSING", "42 报告结构缺少必需字段", category="Code")]
    items.append(ldvh_bootstrap_baseline_item(
        "report_structure",
        "42 报告结构输出",
        "open" if report_issues else "closed",
        "checked ldvh-landing-check report structure contract",
        None,
        report_issues,
    ))

    allowed_categories = {"规范", "Code", "Web", "Task", "事实源", "环境承接", "Human Gate"}
    routing_issues = []
    for gap in remaining_gaps:
        if not gap.get("suggested_writeback"):
            routing_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_GAP_ROUTING_MISSING", f"缺口缺少分流建议: {gap.get('id')}", category="Task"))
    routed_categories = set()
    for item in items:
        routed_categories.update(item.get("gap_categories", []))
    unknown_categories = sorted(routed_categories - allowed_categories)
    for category in unknown_categories:
        routing_issues.append(ldvh_bootstrap_issue("BOOTSTRAP_GAP_CATEGORY_UNKNOWN", f"未知缺口分类: {category}", category="Task"))
    items.append(ldvh_bootstrap_baseline_item(
        "gap_classification_routing",
        "缺口分类与分流",
        "open" if routing_issues else "closed",
        f"checked {len(remaining_gaps)} remaining gaps for routing metadata",
        sorted(routed_categories & allowed_categories),
        routing_issues,
    ))

    return {
        "definitions": [{"id": item_id, "label": label} for item_id, label in BOOTSTRAP_BASELINE_DEFINITIONS],
        "items": items,
        "summary": {
            "status": ldvh_landing_check_status(items),
            "by_status": landing_report_count_by(items, "status"),
            "item_count": len(items),
            "open_item_count": len([item for item in items if item["status"] != "closed"]),
            "gap_categories": sorted({category for item in items for category in item.get("gap_categories", [])}),
        },
    }


def ldvh_landing_check_build(workspace_root=None):
    workspace_root = Path(workspace_root) if workspace_root else PROJECT_ROOT
    governed_issues = governed_projects_check_root(workspace_root)
    landing_report = landing_report_build()
    runtime_report = landing_report["runtime_projection"]
    human_gate_report = landing_report["human_gate"]
    fact_report = ldvh_landing_check_fact_validate()
    spec_report = ldvh_landing_check_spec_validate()
    capability_status = ldvh_landing_check_status(landing_report.get("capability_gaps", []))
    requirement_status = ldvh_landing_check_status(landing_report.get("requirements", []))
    checks = [
        {
            "id": "governed_projects",
            "source_area": "governed-projects",
            "status": "open" if governed_issues else "closed",
            "issue_count": len(governed_issues),
            "evidence": f"governed-projects checked at {landing_relative_path(workspace_root / GOVERNED_PROJECTS_FILENAME)}",
            "suggested_writeback": "governed_projects_config",
            "issues": [
                {"source": landing_relative_path(issue.path), "line": issue.line, "code": issue.code, "message": issue.message}
                for issue in governed_issues
            ],
        },
        {
            "id": "landing_report",
            "source_area": "landing-report",
            "status": ldvh_landing_check_status([{"status": capability_status}, {"status": requirement_status}]),
            "issue_count": len([item for item in landing_report.get("requirements", []) if item.get("status") != "closed"]) + len([item for item in landing_report.get("capability_gaps", []) if item.get("status") != "closed"]),
            "evidence": f"landing-report consumed {landing_report['metadata']['requirement_count']} requirements and {len(landing_report.get('capability_gaps', []))} capability checks",
            "suggested_writeback": "landing_report_followup",
            "issues": [],
        },
        {
            "id": "runtime_projection",
            "source_area": "runtime-projection",
            "status": runtime_report["summary"]["status"],
            "issue_count": runtime_report["metadata"]["issue_count"],
            "evidence": f"runtime-projection checked {runtime_report['metadata']['checked_file_count']} project-local files",
            "suggested_writeback": "runtime_projection_or_env_record",
            "issues": runtime_report.get("issues", []),
        },
        {
            "id": "human_gate",
            "source_area": "human-gate",
            "status": human_gate_report["summary"]["status"],
            "issue_count": human_gate_report["metadata"]["issue_count"],
            "evidence": f"human-gate checked {human_gate_report['metadata']['checked_file_count']} project-local files and {human_gate_report['metadata']['record_count']} records",
            "suggested_writeback": "human_gate_record",
            "issues": human_gate_report.get("issues", []),
        },
        {
            "id": "fact_validate",
            "source_area": "fact/spec",
            "status": fact_report["status"],
            "issue_count": fact_report["issue_count"],
            "evidence": fact_report["evidence"],
            "suggested_writeback": "fact_yaml_fix_or_task",
            "issues": fact_report["issues"],
        },
        {
            "id": "spec_validate",
            "source_area": "fact/spec",
            "status": spec_report["status"],
            "issue_count": spec_report["issue_count"],
            "evidence": spec_report["evidence"],
            "suggested_writeback": "spec_fix_or_task",
            "issues": spec_report["issues"],
        },
    ]
    remaining_gaps = []
    for check in checks:
        if check["status"] == "closed":
            continue
        remaining_gaps.append(
            {
                "id": check["id"],
                "status": check["status"],
                "source_area": check["source_area"],
                "message": check["evidence"],
                "suggested_writeback": check["suggested_writeback"],
            }
        )
    bootstrap_baseline = ldvh_bootstrap_baseline_build(
        workspace_root,
        checks,
        governed_issues,
        runtime_report,
        spec_report,
        remaining_gaps,
    )
    return {
        "metadata": {
            "tool": "code/specs_validate.py",
            "report": "ldvh-landing-check",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "project_root": str(PROJECT_ROOT),
            "workspace_root": str(workspace_root),
            "scope": "project-local Git facts plus explicit workspace governed-projects config",
            "bootstrap_baseline_source": "docs/studies/42-ldvh-landing-check-LDVH落地与检查.md (已退回 studies，待重新设计)",
        },
        "summary": {
            "status": ldvh_landing_check_status(checks),
            "by_status": landing_report_count_by(checks, "status"),
            "remaining_gap_count": len(remaining_gaps),
            "bootstrap_baseline_status": bootstrap_baseline["summary"]["status"],
            "bootstrap_baseline_open_item_count": bootstrap_baseline["summary"]["open_item_count"],
        },
        "checks": checks,
        "bootstrap_baseline": bootstrap_baseline,
        "remaining_gaps": remaining_gaps,
    }


def landing_plan_build(workspace_root=None):
    workspace_root = Path(workspace_root) if workspace_root else PROJECT_ROOT
    landing_report = landing_report_build()
    ldvh_check = ldvh_landing_check_build(workspace_root)
    gap_categories = landing_report.get("gap_categories", {})

    facts_read = []
    for req in landing_report.get("requirements", []):
        src = req.get("source", "")
        if src and src not in [f["path"] for f in facts_read]:
            facts_read.append({"path": src, "type": "spec"})
    for cap in landing_report.get("capability_gaps", []):
        src = cap.get("source", "capability_gaps")
        if src and src not in [f["path"] for f in facts_read]:
            facts_read.append({"path": src, "type": "capability"})

    capabilities = []
    for check in ldvh_check.get("checks", []):
        capabilities.append({
            "id": check["id"],
            "source_area": check["source_area"],
            "status": check["status"],
            "issue_count": check["issue_count"],
            "evidence": check["evidence"],
        })

    proposed_actions = []
    for area, category in gap_categories.items():
        action = {
            "owner_area": area,
            "label": category.get("label", area),
            "gap_count": category["total"],
            "by_status": category.get("by_status", {}),
            "suggested_writebacks": list(category.get("by_suggested_writeback", {}).keys()),
        }
        if area == "human_gate" and "subcategories" in category:
            action["subcategories"] = {
                k: {"label": v["label"], "total": v["total"]}
                for k, v in category["subcategories"].items()
            }
        if area == "runtime_projection" and "subcategories" in category:
            action["subcategories"] = {
                k: {"label": v["label"], "total": v["total"]}
                for k, v in category["subcategories"].items()
            }
            rp_items = [
                r for r in landing_report.get("requirements", [])
                if r.get("owner_area") == "runtime_projection" and landing_report_is_gap(r)
            ] + [
                c for c in landing_report.get("capability_gaps", [])
                if c.get("owner_area") == "runtime_projection" and landing_report_is_gap(c)
            ]
            remediation_counts = {}
            for item in rp_items:
                rtype = classify_runtime_projection_remediation(item)
                remediation_counts[rtype] = remediation_counts.get(rtype, 0) + 1
            action["remediation"] = {
                rtype: {
                    "label": RUNTIME_PROJECTION_REMEDIATION_LABELS.get(rtype, rtype),
                    "total": count,
                }
                for rtype, count in sorted(remediation_counts.items(), key=lambda x: -x[1])
            }
        proposed_actions.append(action)

    writes_required = {
        "required": any(
            cat.get("by_suggested_writeback", {})
            for cat in gap_categories.values()
            if any(k not in ("manual_review", "none") for k in cat.get("by_suggested_writeback", {}))
        ),
        "targets": sorted(set(
            wb
            for cat in gap_categories.values()
            for wb in cat.get("by_suggested_writeback", {})
            if wb not in ("manual_review", "none")
        )),
    }

    human_gate = {
        "total_gaps": gap_categories.get("human_gate", {}).get("total", 0),
        "subcategories": {},
    }
    hg_cat = gap_categories.get("human_gate", {})
    if "subcategories" in hg_cat:
        for sk, sv in hg_cat["subcategories"].items():
            entry = {"label": sv["label"], "total": sv["total"], "by_status": sv.get("by_status", {})}
            if "decision_flows" in sv:
                entry["decision_flows"] = {fk: {"label": fv["label"], "total": fv["total"]} for fk, fv in sv["decision_flows"].items()}
            if "policy_flows" in sv:
                entry["policy_flows"] = {fk: {"label": fv["label"], "total": fv["total"]} for fk, fv in sv["policy_flows"].items()}
            if "support_flows" in sv:
                entry["support_flows"] = {fk: {"label": fv["label"], "total": fv["total"]} for fk, fv in sv["support_flows"].items()}
            if "diagnostic_flows" in sv:
                entry["diagnostic_flows"] = {fk: {"label": fv["label"], "total": fv["total"]} for fk, fv in sv["diagnostic_flows"].items()}
            human_gate["subcategories"][sk] = entry

    validation_plan = {
        "spec_validate_status": ldvh_check.get("checks", [{}])[5].get("status", "unknown") if len(ldvh_check.get("checks", [])) > 5 else "unknown",
        "fact_validate_status": ldvh_check.get("checks", [{}])[4].get("status", "unknown") if len(ldvh_check.get("checks", [])) > 4 else "unknown",
        "runtime_projection_status": ldvh_check.get("checks", [{}])[2].get("status", "unknown") if len(ldvh_check.get("checks", [])) > 2 else "unknown",
        "human_gate_status": ldvh_check.get("checks", [{}])[3].get("status", "unknown") if len(ldvh_check.get("checks", [])) > 3 else "unknown",
    }

    writeback_targets = sorted(set(
        wb
        for cat in gap_categories.values()
        for wb in cat.get("by_suggested_writeback", {})
        if wb not in ("manual_review", "none")
    ))

    return {
        "metadata": {
            "tool": "code/specs_validate.py",
            "report": "landing-plan",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "read_only": True,
        },
        "scope": {
            "project_root": str(PROJECT_ROOT),
            "workspace_root": str(workspace_root),
            "landing_report_sources": landing_report["metadata"]["source_count"],
            "landing_report_requirements": landing_report["metadata"]["requirement_count"],
        },
        "facts_read": facts_read,
        "capabilities": capabilities,
        "requirements": {
            "total": landing_report["metadata"]["requirement_count"],
            "by_status": landing_report["summary"]["by_status"],
            "gap_total": landing_report["summary"]["gap_total"],
            "gap_by_owner_area": landing_report["summary"]["gap_by_owner_area"],
        },
        "gaps": {
            "by_owner_area": {area: cat["total"] for area, cat in gap_categories.items()},
            "categories": gap_categories,
        },
        "proposed_actions": proposed_actions,
        "writes_required": writes_required,
        "human_gate": human_gate,
        "validation_plan": validation_plan,
        "writeback_targets": writeback_targets,
    }


def landing_plan_format_text(plan):
    lines = []
    lines.append("# Landing Plan (只读)")
    lines.append("")
    scope = plan.get("scope", {})
    lines.append(f"项目: {scope.get('project_root', '')}")
    lines.append(f"规范来源: {scope.get('landing_report_sources', 0)} 篇")
    lines.append(f"规范落地要求: {scope.get('landing_report_requirements', 0)} 条")
    req = plan.get("requirements", {})
    lines.append(f"未关闭缺口: {req.get('gap_total', 0)}")
    lines.append(f"缺口分布: {req.get('gap_by_owner_area', {})}")
    lines.append("")

    lines.append("## 能力状态")
    for cap in plan.get("capabilities", []):
        lines.append(f"- {cap['id']}: {cap['status']} (issues: {cap['issue_count']})")
    lines.append("")

    lines.append("## 建议行动")
    for action in plan.get("proposed_actions", []):
        lines.append(f"- {action['label']} ({action['owner_area']}): {action['gap_count']} 缺口, status={action['by_status']}")
        if "subcategories" in action:
            for sk, sv in action["subcategories"].items():
                lines.append(f"  - {sv['label']} ({sk}): {sv['total']}")
        if "remediation" in action:
            for rk, rv in action["remediation"].items():
                lines.append(f"  - {rv['label']} ({rk}): {rv['total']}")
    lines.append("")

    lines.append("## 写入需求")
    wr = plan.get("writes_required", {})
    lines.append(f"需要写入: {'是' if wr.get('required') else '否'}")
    if wr.get("targets"):
        lines.append(f"写入目标: {', '.join(wr['targets'])}")
    lines.append("")

    lines.append("## Human Gate")
    hg = plan.get("human_gate", {})
    lines.append(f"总缺口: {hg.get('total_gaps', 0)}")
    for sk, sv in hg.get("subcategories", {}).items():
        lines.append(f"- {sv['label']} ({sk}): {sv['total']}, status={sv.get('by_status', {})}")
    lines.append("")

    lines.append("## 验证计划")
    vp = plan.get("validation_plan", {})
    for k, v in vp.items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## 回写目标")
    for target in plan.get("writeback_targets", []):
        lines.append(f"- {target}")

    return "\n".join(lines)


def landing_plan_main(workspace_root=None, output_format="text"):
    plan = landing_plan_build(workspace_root)
    if output_format == "json":
        json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    else:
        print(landing_plan_format_text(plan))
    has_open = plan.get("requirements", {}).get("gap_total", 0) > 0
    return 1 if has_open else 0


def ldvh_landing_check_format_text(report):
    lines = ["LDVH落地与检查派生报告"]
    lines.append(f"- 状态: {report['summary']['status']}")
    lines.append(f"- 剩余缺口数: {report['summary']['remaining_gap_count']}")
    lines.append(f"- Bootstrap Code 基线状态: {report['summary'].get('bootstrap_baseline_status')}")
    lines.append(f"- Bootstrap Code 基线未关闭项: {report['summary'].get('bootstrap_baseline_open_item_count')}")
    lines.append("- 状态判断: Code 派生启发式，非事实源")
    lines.append("")
    lines.append("Bootstrap Code 基线能力:")
    for item in report.get("bootstrap_baseline", {}).get("items", []):
        categories = ",".join(item.get("gap_categories", [])) or "none"
        lines.append(f"- [{item['status']}] {item['id']} ({item['label']}) -> {item['evidence']}; issues: {item['issue_count']}; categories: {categories}")
    lines.append("")
    lines.append("检查项:")
    for item in report["checks"]:
        lines.append(f"- [{item['status']}/{item['source_area']}] {item['id']} -> {item['evidence']}; issues: {item['issue_count']}; suggested_writeback: {item['suggested_writeback']}")
    lines.append("")
    lines.append("剩余缺口:")
    if not report["remaining_gaps"]:
        lines.append("- 无")
    else:
        for item in report["remaining_gaps"]:
            lines.append(f"- [{item['status']}/{item['source_area']}] {item['id']} -> {item['message']}; suggested_writeback: {item['suggested_writeback']}")
    return "\n".join(lines)


def ldvh_landing_check_main(workspace_root=None, output_format="text"):
    report = ldvh_landing_check_build(workspace_root)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(ldvh_landing_check_format_text(report))
    return 0 if report["summary"]["status"] in {"closed", "degraded"} else 1
