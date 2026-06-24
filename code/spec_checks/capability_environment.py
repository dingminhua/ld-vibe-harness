"""Capability asset to environment assurance matrix for LDVH."""

import json
from datetime import datetime
from pathlib import Path

from . import deployment_entries
from .common import count_by, relative_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_ENVIRONMENT_SPEC_PATH = "specs/06-运行时扩展规范.md"
CAPABILITY_ENVIRONMENT_CHECKLIST_PATH = "specs/attachments/06.Att.10-部署检查核对表.md"
OFFICIAL_ENVIRONMENT_TARGET = "Codex App"

RESPONSIBILITY_BY_TYPE = {
    "rule": {
        "capability_owner": "LDVH maintainer",
        "sync_scope": "入口路由、最小读取、STOP 点、工具入口、交接、验证和问题原因提示",
        "environment_role": "环境入口只做薄引用，指向 Rules 资产，不复制正文",
    },
    "skill": {
        "capability_owner": "LDVH maintainer",
        "sync_scope": "可复用流程、输入输出、失败处理、验证和主控交还",
        "environment_role": "环境可按 Skill 机制加载；未实装时退回手动步骤",
    },
    "hook": {
        "capability_owner": "LDVH maintainer",
        "sync_scope": "Hook 事件、参数、阻断语义、底层 Code validator 和受限检查",
        "environment_role": "环境可接入 Hook 调用；未实装时退回等价手动命令",
    },
    "agent": {
        "capability_owner": "LDVH maintainer",
        "sync_scope": "Agent 输入输出、权限边界、主控回收和事实源不分叉",
        "environment_role": "环境可调用 Agent；未登记 fixed Agent 时不得声明稳定承载",
    },
}


def _list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _diagnostic(path, code, message, line=1, severity="error", status="open"):
    return {
        "source": relative_path(path, PROJECT_ROOT),
        "line": line,
        "code": code,
        "severity": severity,
        "status": status,
        "message": message,
    }


def _issue_diagnostic(issue, root):
    try:
        source = str(issue.path.relative_to(root))
    except ValueError:
        source = relative_path(issue.path, PROJECT_ROOT)
    return {
        "source": source,
        "line": issue.line,
        "code": issue.code or "CAPABILITY_ENVIRONMENT_DEPLOYMENT_ENTRY_ISSUE",
        "severity": "error",
        "status": "open",
        "message": issue.message,
    }


def _source_spec_diagnostics(root, records):
    diagnostics = []
    for record in records:
        asset_path = root / record["path"]
        for source_spec in record.get("source_specs") or []:
            if isinstance(source_spec, str) and source_spec.startswith("specs/") and not (root / source_spec).exists():
                diagnostics.append(
                    _diagnostic(
                        asset_path,
                        "CAPABILITY_ENVIRONMENT_SOURCE_SPEC_MISSING",
                        f"固定能力资产引用的来源规范不存在: {source_spec}",
                    )
                )
    return diagnostics


def _asset_contract_diagnostics(root, records):
    diagnostics = []
    for record in records:
        asset_path = root / record["path"]
        metadata = record.get("metadata") or {}
        if not _list(metadata.get("sync_triggers")):
            diagnostics.append(
                _diagnostic(
                    asset_path,
                    "CAPABILITY_ENVIRONMENT_SYNC_TRIGGER_MISSING",
                    "固定能力资产缺少 sync_triggers，无法判断 specs 或环境变化后的同步责任",
                )
            )
        verifications = _list(metadata.get("verification"))
        if not verifications:
            diagnostics.append(
                _diagnostic(
                    asset_path,
                    "CAPABILITY_ENVIRONMENT_VERIFICATION_MISSING",
                    "固定能力资产缺少 verification，无法形成可复查保障链",
                )
            )
        elif not any("deployment-entries" in item for item in verifications if isinstance(item, str)):
            diagnostics.append(
                _diagnostic(
                    asset_path,
                    "CAPABILITY_ENVIRONMENT_DEPLOYMENT_ENTRY_VERIFICATION_MISSING",
                    "固定能力资产 verification 未包含 deployment-entries，登记一致性未进入自身验证链",
                    severity="warning",
                    status="limited",
                )
            )
    return diagnostics


def _responsibility_chain(record):
    asset_type = (record.get("type") or "").lower()
    responsibility = RESPONSIBILITY_BY_TYPE.get(
        asset_type,
        {
            "capability_owner": "LDVH maintainer",
            "sync_scope": "资产自描述、来源规范、验证和废弃规则",
            "environment_role": "环境只能按 06 适配检查接入，不得声明完整支持",
        },
    )
    return {
        "source_trigger_owner": "source_specs listed by the asset",
        "runtime_extension_owner": responsibility["capability_owner"],
        "sync_scope": responsibility["sync_scope"],
        "code_owner": "04 Code checks provide derived diagnostics and do not authorize writes",
        "test_owner": "08 verification entries and focused regression prove the check surface",
        "environment_owner": "Human or target environment owner authorizes local entry writes and installation",
    }


def _environment_landing(record):
    asset_type = (record.get("type") or "").lower()
    responsibility = RESPONSIBILITY_BY_TYPE.get(asset_type, {})
    return {
        "official_target": OFFICIAL_ENVIRONMENT_TARGET,
        "landing_mode": responsibility.get("environment_role", "按 06 部署检查和环境适配规则接入"),
        "installation_status": "not_claimed",
        "status_reason": "固定资产存在不等于用户环境已安装；当前报告只说明可承接关系和检查入口",
        "human_gate_required_for_environment_write": True,
        "deployment_checklist": CAPABILITY_ENVIRONMENT_CHECKLIST_PATH,
    }


def capability_environment_report_build(root=None):
    root = Path(root) if root is not None else PROJECT_ROOT
    records = deployment_entries.deployment_entries_asset_records(root)
    deployment_issues = deployment_entries.deployment_entries_check(root)
    diagnostics = [_issue_diagnostic(issue, root) for issue in deployment_issues]
    diagnostics.extend(_source_spec_diagnostics(root, records))
    diagnostics.extend(_asset_contract_diagnostics(root, records))

    matrix = []
    for record in records:
        metadata = record.get("metadata") or {}
        matrix.append(
            {
                "asset": {
                    "id": record.get("id"),
                    "type": record.get("type"),
                    "status": record.get("status"),
                    "path": record.get("path"),
                    "canonical_path": record.get("canonical_path"),
                },
                "capability_contract": {
                    "source_specs": _list(metadata.get("source_specs")),
                    "consumption_scenarios": _list(metadata.get("consumption_scenarios")),
                    "inputs": _list(metadata.get("inputs")),
                    "outputs": _list(metadata.get("outputs")),
                    "handoff": metadata.get("handoff"),
                    "verification": _list(metadata.get("verification")),
                    "sync_triggers": _list(metadata.get("sync_triggers")),
                    "deprecation": metadata.get("deprecation"),
                },
                "responsibility_chain": _responsibility_chain(record),
                "environment_landing": _environment_landing(record),
            }
        )

    status = "open" if any(item["status"] == "open" for item in diagnostics) else "closed"
    if status == "closed" and any(item["status"] == "limited" for item in diagnostics):
        status = "limited"

    return {
        "metadata": {
            "tool": "code/specs_validate.py",
            "report": "capability-environment",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived from fixed runtime extension self-descriptions",
            "scope": "fixed runtime extension assets and environment landing boundary",
            "root": str(root),
        },
        "summary": {
            "status": status,
            "asset_count": len(matrix),
            "diagnostic_count": len(diagnostics),
            "by_status": count_by(diagnostics, "status"),
            "by_code": count_by(diagnostics, "code"),
            "environment_installation_status": "not_claimed",
        },
        "environment_targets": [
            {
                "name": OFFICIAL_ENVIRONMENT_TARGET,
                "support_claim": "official adaptation target, not an installation claim",
                "source": CAPABILITY_ENVIRONMENT_SPEC_PATH,
            }
        ],
        "matrix": matrix,
        "diagnostics": diagnostics,
    }


def capability_environment_format_text(report):
    lines = ["能力资产与环境保障矩阵"]
    summary = report["summary"]
    lines.append(f"- 固定能力资产数: {summary['asset_count']}")
    lines.append(f"- 诊断数: {summary['diagnostic_count']}")
    lines.append(f"- 状态: {summary['status']}")
    lines.append(f"- 环境安装状态声明: {summary['environment_installation_status']}")
    lines.append("- 状态判断: Code 派生只读矩阵，非事实源，不声明环境已安装")
    lines.append("")
    lines.append("固定资产:")
    if not report["matrix"]:
        lines.append("- 无")
    for item in report["matrix"]:
        asset = item["asset"]
        landing = item["environment_landing"]
        chain = item["responsibility_chain"]
        lines.append(
            f"- {asset['path']} [{asset['type']}/{asset['status']}]: "
            f"{landing['official_target']} / {landing['installation_status']}; "
            f"sync={chain['runtime_extension_owner']}"
        )
    lines.append("")
    lines.append("诊断:")
    if not report["diagnostics"]:
        lines.append("- 无")
    else:
        for item in report["diagnostics"]:
            lines.append(f"- {item['source']}:{item['line']} [{item['status']}/{item['code']}] {item['message']}")
    return "\n".join(lines)


def capability_environment_main(root=None, output_format="text"):
    report = capability_environment_report_build(root)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(capability_environment_format_text(report))
    return 0 if report["summary"]["status"] == "closed" else 1
