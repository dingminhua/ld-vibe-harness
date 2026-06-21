"""Web Validate read-only data contract for LDVH checks."""

import json
from pathlib import Path

from . import human_gate as human_gate_checks
from . import assurance_report as assurance_report_checks
from . import ldvh_assurance as ldvh_assurance_checks


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = PROJECT_ROOT / "specs"
LEGACY_SPECS_DIR = PROJECT_ROOT / "docs" / "specs"
FORMAL_SPECS_DIR = SPECS_DIR
DOCS_DIR = PROJECT_ROOT / "docs"
RUNTIME_PROJECTION_DEFAULT_PATHS = list(assurance_report_checks.RUNTIME_PROJECTION_DEFAULT_PATHS)


def sync_ldvh_assurance_config():
    ldvh_assurance_checks.PROJECT_ROOT = PROJECT_ROOT
    ldvh_assurance_checks.SPECS_DIR = SPECS_DIR
    ldvh_assurance_checks.LEGACY_SPECS_DIR = LEGACY_SPECS_DIR
    ldvh_assurance_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    ldvh_assurance_checks.DOCS_DIR = DOCS_DIR
    ldvh_assurance_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def sync_assurance_report_config():
    assurance_report_checks.PROJECT_ROOT = PROJECT_ROOT
    assurance_report_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    assurance_report_checks.DOCS_DIR = DOCS_DIR
    assurance_report_checks.RUNTIME_PROJECTION_DEFAULT_PATHS = list(RUNTIME_PROJECTION_DEFAULT_PATHS)


def sync_human_gate_config():
    human_gate_checks.PROJECT_ROOT = PROJECT_ROOT
    human_gate_checks.FORMAL_SPECS_DIR = FORMAL_SPECS_DIR
    human_gate_checks.DOCS_DIR = DOCS_DIR


def ldvh_assurance_check_fact_validate():
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.ldvh_assurance_check_fact_validate()


def ldvh_assurance_check_build(workspace_root=None):
    sync_ldvh_assurance_config()
    return ldvh_assurance_checks.ldvh_assurance_check_build(workspace_root)


def assurance_report_build(paths=None):
    sync_assurance_report_config()
    return assurance_report_checks.assurance_report_build(paths)


def human_gate_report_build(paths=None):
    sync_human_gate_config()
    return human_gate_checks.report_build(paths)


def web_validate_compact_assurance_check(report):
    return {
        "metadata": {
            "generated_at": report.get("metadata", {}).get("generated_at"),
            "status_source": report.get("metadata", {}).get("status_source"),
            "scope": report.get("metadata", {}).get("scope"),
        },
        "summary": {
            "status": report.get("summary", {}).get("status"),
            "remaining_gap_count": report.get("summary", {}).get("remaining_gap_count", 0),
            "by_status": report.get("summary", {}).get("by_status", {}),
        },
        "checks": [
            {
                "id": item.get("id"),
                "status": item.get("status"),
                "issue_count": item.get("issue_count", 0),
                "evidence": item.get("evidence"),
                "suggested_writeback": item.get("suggested_writeback"),
            }
            for item in report.get("checks", [])
        ],
        "remaining_gaps": [
            {
                "id": item.get("id"),
                "status": item.get("status"),
                "message": item.get("message"),
                "suggested_writeback": item.get("suggested_writeback"),
            }
            for item in report.get("remaining_gaps", [])
        ],
    }


def web_validate_compact_assurance_report(report):
    return {
        "metadata": {
            "generated_at": report.get("metadata", {}).get("generated_at"),
            "requirement_count": report.get("metadata", {}).get("requirement_count", 0),
            "human_gate_record_count": report.get("metadata", {}).get("human_gate_record_count", 0),
            "runtime_projection_issue_count": report.get("metadata", {}).get("runtime_projection_issue_count", 0),
            "human_gate_issue_count": report.get("metadata", {}).get("human_gate_issue_count", 0),
            "status_source": report.get("metadata", {}).get("status_source"),
        },
        "summary": {
            "by_status": report.get("summary", {}).get("by_status", {}),
            "gap_total": report.get("summary", {}).get("gap_total", 0),
            "runtime_projection_status": report.get("summary", {}).get("runtime_projection_status"),
            "human_gate_status": report.get("summary", {}).get("human_gate_status"),
            "gap_by_owner_area": report.get("summary", {}).get("gap_by_owner_area", {}),
        },
        "capability_gaps": [
            {
                "id": item.get("id"),
                "capability": item.get("capability"),
                "status": item.get("status"),
                "owner_area": item.get("owner_area"),
                "suggested_writeback": item.get("suggested_writeback"),
                "evidence": item.get("evidence"),
            }
            for item in report.get("capability_gaps", [])
        ],
        "gap_categories": [
            {
                "key": key,
                "label": category.get("label"),
                "total": category.get("total", 0),
                "by_status": category.get("by_status", {}),
                "examples": [
                    {
                        "source": example.get("source"),
                        "status": example.get("status"),
                        "title": example.get("title"),
                        "suggested_writeback": example.get("suggested_writeback"),
                    }
                    for example in category.get("examples", [])
                ],
            }
            for key, category in report.get("gap_categories", {}).items()
        ],
    }


def web_validate_compact_human_gate_report(report):
    return {
        "metadata": {
            "generated_at": report.get("metadata", {}).get("generated_at"),
            "checked_file_count": report.get("metadata", {}).get("checked_file_count", 0),
            "record_count": report.get("metadata", {}).get("record_count", 0),
            "issue_count": report.get("metadata", {}).get("issue_count", 0),
            "status_source": report.get("metadata", {}).get("status_source"),
            "scope": report.get("metadata", {}).get("scope"),
        },
        "summary": {
            "status": report.get("summary", {}).get("status"),
        },
        "issues": report.get("issues", []),
    }


def web_validate_build(workspace_root=None):
    fact_report = ldvh_assurance_check_fact_validate()
    assurance_check = ldvh_assurance_check_build(workspace_root)
    assurance_report = assurance_report_build()
    human_gate_report = assurance_report.get("human_gate")
    if human_gate_report is None:
        human_gate_report = human_gate_report_build()

    return {
        "ok": fact_report.get("error_count", 0) == 0,
        "command": "web_validate",
        "action": "validate",
        "target": "ldvh-base",
        "summary": {
            "files": fact_report.get("checked_file_count", 0),
            "errors": fact_report.get("error_count", 0),
            "warnings": fact_report.get("warning_count", 0),
        },
        "issues": fact_report.get("issues", []),
        "reports": {
            "assuranceCheck": web_validate_compact_assurance_check(assurance_check),
            "assuranceReport": web_validate_compact_assurance_report(assurance_report),
            "humanGateReport": web_validate_compact_human_gate_report(human_gate_report),
        },
    }


def web_validate_format_text(report):
    assurance = report.get("reports", {}).get("assuranceCheck", {})
    assurance_report = report.get("reports", {}).get("assuranceReport", {})
    human_gate = report.get("reports", {}).get("humanGateReport", {})
    lines = ["Web Validate 派生报告"]
    lines.append(f"- fact files: {report.get('summary', {}).get('files', 0)}")
    lines.append(f"- fact errors: {report.get('summary', {}).get('errors', 0)}")
    lines.append(f"- fact warnings: {report.get('summary', {}).get('warnings', 0)}")
    lines.append(f"- 42 status: {assurance.get('summary', {}).get('status')}")
    lines.append(f"- assurance gaps: {assurance_report.get('summary', {}).get('gap_total', 0)}")
    lines.append(f"- Human Gate records: {human_gate.get('metadata', {}).get('record_count', 0)}")
    return "\n".join(lines)


def web_validate_main(workspace_root=None, output_format="text"):
    report = web_validate_build(workspace_root)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(web_validate_format_text(report))
    return 0
