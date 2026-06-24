"""Controlled write preflight diagnostics for LDVH assets."""

import json
from datetime import datetime
from pathlib import Path

from .deployment_entries import deployment_entries_asset_records
from .v2 import v2_check_build


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_TOOL = "code/specs_validate.py preflight"
PREFLIGHT_OPERATIONS = {"create", "update", "delete", "move", "rename"}
HIGH_IMPACT_OPERATIONS = {"delete", "move", "rename"}
RULES_ENTRY_SYNC_REVIEW_PATH = "specs/30-rules-entry-sync-review-Rules入口同步审查.md"


AUTHORIZED_PREFIXES = [
    ("specs/", "specs", "01/04/07"),
    ("code/", "code", "04/08"),
    ("web/", "web", "05/08"),
    ("rules/", "runtime_extension", "06/07"),
    ("skills/", "runtime_extension", "06/07"),
    ("agents/", "runtime_extension", "06/07"),
    ("hooks/", "runtime_extension", "06/07"),
    ("tests/", "tests", "08"),
    ("ldvh-base/", "fact_source", "02/07"),
]
AUTHORIZED_FILES = {
    "LDVH-GOVERNED-PROJECTS.yaml": ("runtime_extension", "06/07"),
    "README.md": ("project_entry", "01/07"),
    "pyproject.toml": ("code", "04/08"),
}

FIELD_PATH_RULES = {
    "v2_spec.spec_id": ("01-规范体系基础规范", "specs/attachments/01.Att.04-规范身份字段表.md", "v2_spec"),
    "v2_spec.status": ("01-规范体系基础规范", "specs/attachments/01.Att.04-规范身份字段表.md", "v2_spec"),
    "v2_spec.authority": ("01-规范体系基础规范", "specs/attachments/01.Att.04-规范身份字段表.md", "v2_spec"),
    "v2_spec.related_specs": ("01-规范体系基础规范", "specs/attachments/01.Att.04-规范身份字段表.md", "v2_spec"),
    "v2_spec.code_consumption": ("04-Code确定性执行规范", "specs/04-Code确定性执行规范.md", "v2_spec"),
    "v2_attachment.status": ("01-规范体系基础规范", "specs/attachments/01.Att.05-附件身份字段表.md", "v2_attachment"),
    "v2_attachment.parent_spec": ("01-规范体系基础规范", "specs/attachments/01.Att.05-附件身份字段表.md", "v2_attachment"),
    "ldvh_asset.source_specs": ("06-运行时扩展规范", "specs/attachments/06.Att.01-运行时扩展自描述字段表.md", "ldvh_asset"),
    "ldvh_asset.sync_triggers": ("06-运行时扩展规范", "specs/attachments/06.Att.01-运行时扩展自描述字段表.md", "ldvh_asset"),
    "ldvh_asset.verification": ("06-运行时扩展规范", "specs/attachments/06.Att.01-运行时扩展自描述字段表.md", "ldvh_asset"),
}


def source_ref(path, line=1, field=None):
    ref = {"path": path, "line_start": line, "line_end": line}
    if field:
        ref["field"] = field
    return ref


def diagnostic(code, severity, message, path, owner, check_id):
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "path": path,
        "line": 1,
        "suggested_owner": owner,
        "check_id": check_id,
        "source_refs": [source_ref(path)],
    }


def relative_target(root, target_path):
    path = Path(target_path)
    absolute = path if path.is_absolute() else root / path
    try:
        relative = absolute.resolve().relative_to(root.resolve())
        return str(relative), absolute.resolve(), True
    except ValueError:
        return str(absolute), absolute.resolve(), False


def classify_target(relative_path, inside_root):
    if not inside_root:
        return None
    if relative_path in AUTHORIZED_FILES:
        asset_type, owner = AUTHORIZED_FILES[relative_path]
        return {"asset_type": asset_type, "owner": owner}
    for prefix, asset_type, owner in AUTHORIZED_PREFIXES:
        if relative_path.startswith(prefix):
            return {"asset_type": asset_type, "owner": owner}
    return None


def check_status(diagnostics):
    if any(item["severity"] == "error" for item in diagnostics):
        return "blocked"
    if any(item["severity"] == "warning" for item in diagnostics):
        return "needs_human_gate"
    return "pass"


def rules_asset_impact(root, relative_path, target_info):
    if not target_info or target_info["asset_type"] not in {"specs", "runtime_extension"}:
        return {"required": False, "assets": [], "basis": "not_applicable"}

    records = [
        record
        for record in deployment_entries_asset_records(root)
        if record.get("type") == "rule"
    ]
    if target_info["asset_type"] == "runtime_extension":
        matches = [record for record in records if record.get("canonical_path") == relative_path or record.get("path") == relative_path]
        return {"required": True, "assets": matches, "basis": "target_runtime_asset"}

    matches = [record for record in records if relative_path in set(record.get("source_specs") or [])]
    return {"required": True, "assets": matches, "basis": "source_specs"}


def rules_entry_sync_review(root, relative_path, target_info):
    if not target_info or target_info.get("asset_type") != "specs":
        return {"required": False, "path": RULES_ENTRY_SYNC_REVIEW_PATH, "basis": "not_applicable"}
    if not relative_path.startswith("specs/"):
        return {"required": False, "path": RULES_ENTRY_SYNC_REVIEW_PATH, "basis": "not_applicable"}
    path = root / relative_path
    is_markdown = Path(relative_path).suffix == ".md" or path.suffix == ".md"
    if not is_markdown:
        return {"required": False, "path": RULES_ENTRY_SYNC_REVIEW_PATH, "basis": "not_markdown_spec"}
    if relative_path == RULES_ENTRY_SYNC_REVIEW_PATH:
        return {"required": False, "path": RULES_ENTRY_SYNC_REVIEW_PATH, "basis": "self_review"}
    return {"required": True, "path": RULES_ENTRY_SYNC_REVIEW_PATH, "basis": "specs_entry_surface"}


def field_path_info(field_path):
    if not field_path:
        return None
    if field_path in FIELD_PATH_RULES:
        owner, source_path, root_key = FIELD_PATH_RULES[field_path]
        return {
            "validated": True,
            "field_path": field_path,
            "owner": owner,
            "source_path": source_path,
            "root_key": root_key,
        }
    root_key = field_path.split(".", 1)[0]
    return {
        "validated": False,
        "field_path": field_path,
        "owner": None,
        "source_path": None,
        "root_key": root_key,
    }


def knowledge_map_context(root, relative_path, target_info):
    if not target_info or target_info.get("asset_type") not in {"specs", "runtime_extension", "fact_source"}:
        return {"available": False, "reason": "not_applicable", "recommended_reads": [], "impacted_nodes": [], "edges": [], "diagnostics": []}
    if target_info["asset_type"] == "runtime_extension":
        input_scope = "runtime_extensions"
    elif target_info["asset_type"] == "fact_source":
        input_scope = "governed_projects"
    else:
        input_scope = "active_specs"
    try:
        report = v2_check_build(
            root,
            input_scope=input_scope,
            query_layer="expand",
            start_node=relative_path,
            depth=1,
        )
    except Exception as exc:  # pragma: no cover - defensive diagnostics only
        return {
            "available": False,
            "reason": "knowledge_map_error",
            "message": str(exc),
            "recommended_reads": [],
            "impacted_nodes": [],
            "edges": [],
            "diagnostics": [],
        }
    knowledge_map = report.get("knowledge_map", {})
    nodes = knowledge_map.get("nodes", [])
    edges = knowledge_map.get("edges", [])
    recommended_reads = []
    seen_reads = set()
    for node in nodes:
        path = node.get("canonical_path") or node.get("path")
        if not path or path in seen_reads:
            continue
        if node.get("type") in {"spec", "member_spec", "attachment", "runtime_extension", "fact_object", "external_fact_source"}:
            seen_reads.add(path)
            recommended_reads.append(
                {
                    "path": path,
                    "node_id": node.get("id"),
                    "node_type": node.get("type"),
                    "label": node.get("label"),
                    "source_refs": node.get("source_refs") or [],
                }
            )
    impacted_nodes = [
        {
            "id": node.get("id"),
            "type": node.get("type"),
            "label": node.get("label"),
            "canonical_path": node.get("canonical_path"),
            "project_namespace": node.get("project_namespace"),
        }
        for node in nodes
    ]
    return {
        "available": True,
        "input_scope": input_scope,
        "query_layer": "expand",
        "start_node": relative_path,
        "degraded": knowledge_map.get("degraded"),
        "recommended_reads": recommended_reads[:12],
        "impacted_nodes": impacted_nodes[:24],
        "edges": [
            {
                "type": edge.get("type"),
                "from": edge.get("from"),
                "to": edge.get("to"),
                "derived_from": edge.get("derived_from"),
                "source_refs": edge.get("source_refs") or [],
            }
            for edge in edges[:24]
        ],
        "diagnostics": knowledge_map.get("diagnostics", []),
    }


def preflight_build(root=None, target_path=None, operation="update", field_path=None, status=None):
    root = Path(root or PROJECT_ROOT).resolve()
    relative_path, absolute_path, inside_root = relative_target(root, target_path or "")
    target_info = classify_target(relative_path, inside_root)
    operation = operation or "update"
    diagnostics = []
    checks = []

    def add_check(check_id, label, items):
        checks.append(
            {
                "id": check_id,
                "label": label,
                "status": check_status(items),
                "diagnostics": items,
            }
        )
        diagnostics.extend(items)

    if operation not in PREFLIGHT_OPERATIONS:
        add_check(
            "operation",
            "操作类型",
            [
                diagnostic(
                    "PREFLIGHT_OPERATION_INVALID",
                    "error",
                    f"operation 非法: {operation}",
                    relative_path or "<runtime>",
                    "04-Code确定性执行规范",
                    "operation",
                )
            ],
        )
    else:
        add_check("operation", "操作类型", [])

    if not target_info:
        add_check(
            "authorized_location",
            "授权位置",
            [
                diagnostic(
                    "PREFLIGHT_TARGET_LOCATION_UNAUTHORIZED",
                    "error",
                    "写入目标不在当前受控写入授权位置内",
                    relative_path or "<runtime>",
                    "04-Code确定性执行规范",
                    "authorized_location",
                )
            ],
        )
    else:
        add_check("authorized_location", "授权位置", [])

    field_items = []
    exists = absolute_path.exists()
    if operation == "create" and exists:
        field_items.append(
            diagnostic(
                "PREFLIGHT_CREATE_TARGET_EXISTS",
                "error",
                "create 操作的目标已存在",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "field_and_state",
            )
        )
    if operation in {"update", "delete", "move", "rename"} and not exists:
        field_items.append(
            diagnostic(
                "PREFLIGHT_TARGET_MISSING",
                "error",
                f"{operation} 操作的目标不存在",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "field_and_state",
            )
        )
    if target_info and target_info["asset_type"] in {"specs", "project_entry"} and absolute_path.suffix != ".md":
        field_items.append(
            diagnostic(
                "PREFLIGHT_MARKDOWN_EXPECTED",
                "warning",
                "该位置通常应使用 Markdown 承载；请确认目标格式是否由上位规范授权",
                relative_path,
                target_info["owner"],
                "field_and_state",
            )
        )
    field_info = field_path_info(field_path)
    if field_info and field_info["validated"]:
        field_items.append(
            diagnostic(
                "PREFLIGHT_FIELD_PATH_OWNER_IDENTIFIED",
                "info",
                f"field_path 已识别字段归口: {field_path} -> {field_info['owner']} ({field_info['source_path']})",
                relative_path,
                field_info["owner"],
                "field_and_state",
            )
        )
    elif field_info:
        field_items.append(
            diagnostic(
                "PREFLIGHT_FIELD_PATH_NOT_VALIDATED",
                "warning",
                f"field_path 已接收但尚未纳入字段级 Schema 映射: {field_path}",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "field_and_state",
            )
        )
    if status:
        field_items.append(
            diagnostic(
                "PREFLIGHT_STATUS_CHANGE_REQUIRES_OWNER_RULE",
                "warning",
                f"status={status} 需要回到对应规范或事实模型确认状态规则",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "field_and_state",
            )
        )
    add_check("field_and_state", "字段与状态", field_items)

    gate_items = []
    if operation in HIGH_IMPACT_OPERATIONS or status or (target_info and target_info["asset_type"] in {"specs", "runtime_extension", "fact_source"}):
        gate_items.append(
            diagnostic(
                "PREFLIGHT_HUMAN_GATE_REQUIRED",
                "warning",
                "本次写入可能影响规范、运行时扩展、事实源、状态或路径，应先识别 Human Gate",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "human_gate",
            )
        )
    add_check("human_gate", "Human Gate", gate_items)

    add_check(
        "git_trace",
        "Git 追溯",
        [
            diagnostic(
                "PREFLIGHT_GIT_TRACE_REQUIRED",
                "info",
                "若继续写入，应通过 Git commit records 保留事实源追溯",
                relative_path,
                "07-事实源边界与Git追溯规范",
                "git_trace",
            )
        ],
    )

    sync_owner = target_info["owner"] if target_info else "04-Code确定性执行规范"
    rules_impact = rules_asset_impact(root, relative_path, target_info)
    rules_entry_review = rules_entry_sync_review(root, relative_path, target_info)
    km_context = knowledge_map_context(root, relative_path, target_info)
    add_check(
        "sync_impact",
        "同步影响",
        [
            diagnostic(
                "PREFLIGHT_SYNC_IMPACT_REVIEW_REQUIRED",
                "info",
                "继续写入前应检查 specs、Code、Web、运行时扩展和测试是否存在同步影响",
                relative_path,
                sync_owner,
                "sync_impact",
            )
        ],
    )

    rules_items = []
    if rules_impact["required"]:
        assets = rules_impact["assets"]
        if assets:
            asset_paths = "、".join(asset["canonical_path"] for asset in assets)
            rules_items.append(
                diagnostic(
                    "PREFLIGHT_RULES_ASSET_IMPACT_REVIEW_REQUIRED",
                    "info",
                    f"继续写入前应评估固定 Rules 资产同步影响: {asset_paths}",
                    relative_path,
                    "06-运行时扩展规范",
                    "rules_asset_impact",
                )
            )
        else:
            rules_items.append(
                diagnostic(
                    "PREFLIGHT_RULES_ASSET_IMPACT_REVIEW_REQUIRED",
                    "info",
                    "继续写入前应评估固定 Rules 资产同步影响；未发现 source_specs 或目标路径精确匹配的固定 Rules 资产，仍需按入口行为、STOP 点、验证入口和交接路径判断",
                    relative_path,
                    "06-运行时扩展规范",
                    "rules_asset_impact",
                )
            )
    add_check("rules_asset_impact", "Rules 资产影响", rules_items)

    rules_entry_items = []
    if rules_entry_review["required"]:
        rules_entry_items.append(
            diagnostic(
                "PREFLIGHT_RULES_ENTRY_SYNC_REVIEW_REQUIRED",
                "info",
                f"本次 specs 写入可能影响固定 Rules 入口表达；应参考 {RULES_ENTRY_SYNC_REVIEW_PATH} 执行 Rules 入口同步审查。preflight 只提示同步风险，不授权自动修改 Rules",
                relative_path,
                "03-行动编排规范 / 06-运行时扩展规范",
                "rules_entry_sync_review",
            )
        )
    add_check("rules_entry_sync_review", "Rules 入口同步审查", rules_entry_items)

    add_check(
        "failure_owner",
        "失败归口",
        [
            diagnostic(
                "PREFLIGHT_FAILURE_OWNER_IDENTIFIED",
                "info",
                f"检查失败或输出受限时回到 {sync_owner}",
                relative_path,
                sync_owner,
                "failure_owner",
            )
        ],
    )

    summary_status = check_status(diagnostics)
    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "tool": PREFLIGHT_TOOL,
            "read_only": True,
            "write_authorized": False,
            "root": str(root),
        },
        "input": {
            "operation": operation,
            "target_path": target_path,
            "relative_path": relative_path,
            "field_path": field_path,
            "status": status,
            "asset_type": target_info["asset_type"] if target_info else None,
        },
        "rules_asset_impact": {
            "required": rules_impact["required"],
            "basis": rules_impact["basis"],
            "assets": [
                {
                    "id": asset.get("id"),
                    "type": asset.get("type"),
                    "canonical_path": asset.get("canonical_path"),
                    "source_specs": asset.get("source_specs") or [],
                    "sync_triggers": asset.get("sync_triggers") or [],
                    "verification": asset.get("verification") or [],
                }
                for asset in rules_impact["assets"]
            ],
        },
        "rules_entry_sync_review": rules_entry_review,
        "field_path_analysis": field_info,
        "knowledge_map_context": km_context,
        "summary": {
            "status": summary_status,
            "error_count": sum(1 for item in diagnostics if item["severity"] == "error"),
            "warning_count": sum(1 for item in diagnostics if item["severity"] == "warning"),
            "info_count": sum(1 for item in diagnostics if item["severity"] == "info"),
        },
        "checks": checks,
        "diagnostics": diagnostics,
    }


def preflight_format_text(report):
    summary = report.get("summary", {})
    input_data = report.get("input", {})
    lines = [
        "受控写入 preflight 完成",
        f"- operation: {input_data.get('operation')}",
        f"- target: {input_data.get('relative_path')}",
        f"- asset_type: {input_data.get('asset_type')}",
        f"- status: {summary.get('status')}",
        f"- write_authorized: {report.get('metadata', {}).get('write_authorized')}",
        f"- errors: {summary.get('error_count', 0)}",
        f"- warnings: {summary.get('warning_count', 0)}",
        f"- infos: {summary.get('info_count', 0)}",
    ]
    for item in report.get("diagnostics", []):
        lines.append(f"- {item['path']} [{item['severity']}/{item['code']}] {item['message']}")
    return "\n".join(lines)


def preflight_main(root=None, target_path=None, operation="update", field_path=None, status=None, output_format="text"):
    report = preflight_build(root, target_path, operation, field_path, status)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(preflight_format_text(report))
    return 1 if report.get("summary", {}).get("status") == "blocked" else 0
