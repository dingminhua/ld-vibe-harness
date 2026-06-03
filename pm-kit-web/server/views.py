import re
import time
from pathlib import Path

from .config import (
    CLOSING_REQUIRED_FIELDS,
    PRIORITY_ORDER,
    WAITING_DECISION_STATUSES,
    _cache_get,
    _cache_invalidate,
    _cache_set,
    _get_product,
    _has_value,
    _log_action,
    normalize_task_status,
    read_text,
)


def is_waiting_decision(obj: dict) -> bool:
    normalized = obj.get("normalized_status") or normalize_task_status(obj.get("status", ""))
    if normalized in WAITING_DECISION_STATUSES:
        return True
    if obj.get("human_gate") or obj.get("decision_point") or obj.get("decision_needed"):
        return True
    block_text = " ".join([obj.get("block_reason", ""), obj.get("prerequisite", "")])
    return any(needle in block_text for needle in ("需人类确认", "用户确认", "Human Gate", "决策", "确认"))


def missing_task_fields(obj: dict) -> list[dict]:
    checks = [
        ("input_text", "输入原文", "基础"),
        ("understanding", "目标理解 / 任务理解", "基础"),
        ("plan_steps", "计划步骤", "计划"),
        ("current_step", "当前步骤", "执行"),
        ("next_action", "下一动作", "执行"),
        ("validation_method", "验证方式", "验证"),
        ("completion_summary", "完成摘要", "关闭"),
        ("validation_result", "验证结果", "关闭"),
        ("closure_evidence", "关闭证据", "关闭"),
        ("acceptance_result", "验收结果", "关闭"),
    ]
    return [{"key": key, "label": label, "group": group} for key, label, group in checks if not _has_value(obj.get(key, ""))]


def task_health_item(obj: dict) -> dict:
    normalized = obj.get("normalized_status") or normalize_task_status(obj.get("status", ""))
    missing = missing_task_fields(obj)
    closing_missing = [item for item in missing if item["key"] in CLOSING_REQUIRED_FIELDS]
    has_human_gate = bool(obj.get("human_gate") or is_waiting_decision(obj))
    health_issues: list[str] = []
    if normalized != "Closed" and missing:
        health_issues.append("关键执行字段缺失")
    if normalized in {"Decision Needed", "Review Needed", "Blocked"}:
        health_issues.append("处于待决策 / 待验收 / 阻塞状态")
    if normalized in {"Planned", "Executing", "Ready for Plan"} and missing:
        health_issues.append("缺少计划步骤、当前步骤、下一动作或验证方式")
    if normalized == "Closed" and closing_missing:
        health_issues.append("缺少关闭摘要、验证结果、关闭证据或验收结果")
    return {
        "id": obj.get("id", ""),
        "title": obj.get("title", ""),
        "project": obj.get("project", ""),
        "project_name": obj.get("project_name", ""),
        "doc_id": obj.get("doc_id", ""),
        "doc_title": obj.get("doc_title", ""),
        "path": obj.get("path", ""),
        "status": obj.get("status", ""),
        "normalized_status": normalized,
        "missing_fields": missing,
        "missing_count": len(missing),
        "can_close": normalized == "Review Needed" and not closing_missing,
        "human_gate": has_human_gate,
        "allowed_next_statuses": obj.get("allowed_next_statuses", []),
        "health_issues": health_issues,
    }


def get_task_health_data() -> dict:
    from .taskbase import _all_task_objects
    items = [task_health_item(obj) for obj in _all_task_objects()]
    status_summary = {}
    for item in items:
        status = item["normalized_status"]
        status_summary[status] = status_summary.get(status, 0) + 1
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status_summary": status_summary,
        "items": items,
    }


def _display_value(value: str) -> str:
    if value is None:
        return "未写入事实源"
    text = str(value).strip()
    return text if text else "未写入事实源"


def _task_card(obj: dict) -> dict:
    return {
        "id": obj.get("id", ""),
        "title": obj.get("title", ""),
        "type": obj.get("type", ""),
        "status": obj.get("status", ""),
        "normalized_status": obj.get("normalized_status") or normalize_task_status(obj.get("status", "")),
        "priority": obj.get("priority", ""),
        "project": obj.get("project", ""),
        "project_name": obj.get("project_name", ""),
        "doc_id": obj.get("doc_id", ""),
        "doc_title": obj.get("doc_title", ""),
        "path": obj.get("path", ""),
        "decision_needed": obj.get("decision_needed", ""),
        "human_gate": obj.get("human_gate", ""),
        "block_reason": obj.get("block_reason", ""),
        "current_step": obj.get("current_step", ""),
        "next_action": obj.get("next_action", ""),
        "allowed_next_statuses": obj.get("allowed_next_statuses", []),
        "blocked_by": obj.get("blocked_by", []),
    }


def get_action_board_data() -> dict:
    from .taskbase import _all_task_objects
    columns = ["Ready for Plan", "Planned", "Executing", "Blocked", "Decision Needed", "Review Needed", "Closed", "Cancelled"]
    grouped = {key: [] for key in columns}
    items = [_task_card(obj) for obj in _all_task_objects()]
    items.sort(key=lambda x: (PRIORITY_ORDER.get(x.get("priority", ""), 9), x.get("project_name", ""), x.get("id", "")))
    for item in items:
        key = item.get("normalized_status") or "Ready for Plan"
        if key not in grouped:
            key = "Ready for Plan"
        grouped[key].append(item)
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "columns": [{"key": key, "items": grouped[key]} for key in columns],
        "summary": {key: len(grouped[key]) for key in columns},
    }


def _find_task_object(project: str, doc_id: str, obj_id: str) -> tuple[dict, dict]:
    from .requirements import scan_requirements
    for req in scan_requirements():
        if req.get("project") != project or req.get("id") != doc_id:
            continue
        for obj in req.get("exec_objects", []):
            if obj.get("id") == obj_id:
                return req, obj
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Task object not found")


def get_task_detail_data(project: str, doc_id: str, obj_id: str) -> dict:
    req, obj = _find_task_object(project, doc_id, obj_id)
    source = {
        "project": project,
        "project_name": req.get("project_name", ""),
        "doc_id": doc_id,
        "doc_title": req.get("title", ""),
        "path": req.get("path", ""),
    }
    return {
        "id": obj.get("id", ""),
        "title": obj.get("title", ""),
        "source": source,
        "sections": [
            {"title": "基础信息", "fields": [
                {"label": "标题", "value": _display_value(obj.get("title", ""))},
                {"label": "类型", "value": _display_value(obj.get("type", ""))},
                {"label": "来源", "value": _display_value(obj.get("source", ""))},
                {"label": "所属项目", "value": _display_value(req.get("project_name", ""))},
                {"label": "状态", "value": _display_value(obj.get("status", ""))},
                {"label": "标准状态", "value": _display_value(obj.get("normalized_status", ""))},
                {"label": "优先级", "value": _display_value(obj.get("priority", ""))},
                {"label": "优先级原因", "value": _display_value(obj.get("priority_reason", ""))},
            ]},
            {"title": "目标与任务理解", "fields": [
                {"label": "输入原文", "value": _display_value(obj.get("input_text", ""))},
                {"label": "目标理解 / 任务理解", "value": _display_value(obj.get("understanding", ""))},
            ]},
            {"title": "执行计划", "fields": [
                {"label": "计划步骤", "value": _display_value(obj.get("plan_steps", ""))},
                {"label": "预计范围", "value": _display_value(obj.get("scope", ""))},
                {"label": "风险", "value": _display_value(obj.get("risk", ""))},
                {"label": "验证方式", "value": _display_value(obj.get("validation_method", ""))},
            ]},
            {"title": "当前执行", "fields": [
                {"label": "当前步骤", "value": _display_value(obj.get("current_step", ""))},
                {"label": "最近动作", "value": _display_value(obj.get("recent_action", ""))},
                {"label": "下一动作", "value": _display_value(obj.get("next_action", ""))},
                {"label": "阻塞原因", "value": _display_value(obj.get("block_reason", ""))},
            ]},
            {"title": "阻塞与决策点", "fields": [
                {"label": "Human Gate", "value": _display_value(obj.get("human_gate", ""))},
                {"label": "决策点", "value": _display_value(obj.get("decision_point", ""))},
                {"label": "需要决策什么", "value": _display_value(obj.get("decision_needed", ""))},
                {"label": "前置条件", "value": _display_value(obj.get("prerequisite", ""))},
                {"label": "等待对象", "value": _display_value("、".join(obj.get("blocked_by", [])))},
            ]},
            {"title": "完成摘要", "fields": [
                {"label": "完成摘要", "value": _display_value(obj.get("completion_summary", ""))},
                {"label": "修改范围", "value": _display_value(obj.get("scope", ""))},
                {"label": "遗留风险", "value": _display_value(obj.get("risk", ""))},
            ]},
            {"title": "验证结果", "fields": [
                {"label": "验证方式", "value": _display_value(obj.get("validation_method", ""))},
                {"label": "验证结果", "value": _display_value(obj.get("validation_result", ""))},
            ]},
            {"title": "关闭证据", "fields": [
                {"label": "关闭证据", "value": _display_value(obj.get("closure_evidence", ""))},
                {"label": "更新日志链接", "value": _display_value(obj.get("fields", {}).get("更新日志链接", ""))},
            ]},
            {"title": "验收结果", "fields": [
                {"label": "验收结果", "value": _display_value(obj.get("acceptance_result", ""))},
            ]},
            {"title": "源文档", "fields": [
                {"label": "项目", "value": _display_value(req.get("project_name", ""))},
                {"label": "文档", "value": _display_value(req.get("title", ""))},
                {"label": "路径", "value": _display_value(req.get("path", ""))},
            ]},
        ],
    }


def get_waiting_decisions_data() -> dict:
    from .taskbase import _all_task_objects
    items = [obj for obj in _all_task_objects() if is_waiting_decision(obj)]
    items.sort(key=lambda x: (PRIORITY_ORDER.get(x.get("priority", ""), 9), x.get("project_name", ""), x.get("id", "")))
    return {"items": items}


def get_pm_overview_data() -> dict:
    from .taskbase import _all_task_objects
    from .requirements import extract_latest_changelog
    items = _all_task_objects()
    executing = [o for o in items if o.get("normalized_status") == "Executing"]
    decision_needed = [o for o in items if o.get("normalized_status") == "Decision Needed"]
    blocked = [o for o in items if o.get("normalized_status") == "Blocked" or o.get("blocked_by") or o.get("block_reason")]
    review = [o for o in items if o.get("normalized_status") == "Review Needed"]
    closed = [o for o in items if o.get("normalized_status") == "Closed"]
    planned = [o for o in items if o.get("normalized_status") == "Planned"]
    ready_for_plan = [o for o in items if o.get("normalized_status") == "Ready for Plan"]
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "executing": len(executing),
            "decision_needed": len(decision_needed),
            "review_needed": len(review),
            "blocked": len(blocked),
            "planned": len(planned),
            "closed": len(closed),
            "ready_for_plan": len(ready_for_plan),
        },
        "executing": executing[:12],
        "planned": planned[:12],
        "blocked": blocked[:12],
        "decision_needed": decision_needed[:12],
        "review_needed": review[:12],
        "closed": closed[:12],
        "latest_changes": extract_latest_changelog(),
    }


def _scan_adrs() -> list[dict]:
    results = []
    for key, proj in _get_projects().items():
        adr_dir = proj["path"] / proj["docs"] / "adr"
        if not adr_dir.exists():
            continue
        for f in sorted(adr_dir.iterdir()):
            if not f.is_file() or not f.name.endswith(".md"):
                continue
            text = read_text(f)
            if not text.strip():
                continue
            title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else f.stem
            status = "未知"
            for pat in [
                r"^>\s*状态[：:]\s*(.+)$",
                r"^-\s*\*\*状态\*\*[：:]\s*(.+)$",
                r"^\*\*状态\*\*[：:]\s*(.+)$",
                r"^\|\s*状态\s*\|\s*(.+?)\s*\|",
                r"^##\s*状态\s*$",
            ]:
                m = re.search(pat, text, re.MULTILINE)
                if m:
                    val = m.group(1).strip() if m.lastindex else ""
                    if not val and pat.endswith("状态\\s*$"):
                        after = text[m.end():]
                        line_m = re.search(r"^(\S+)", after, re.MULTILINE)
                        if line_m:
                            val = line_m.group(1).strip()
                    if val:
                        status = val
                        break
            date = ""
            for pat in [
                r"^>\s*日期[：:]\s*(.+)$",
                r"^-\s*\*\*日期\*\*[：:]\s*(.+)$",
                r"^\*\*日期\*\*[：:]\s*(.+)$",
                r"^\|\s*日期\s*\|\s*(.+?)\s*\|",
            ]:
                m = re.search(pat, text, re.MULTILINE)
                if m:
                    date = m.group(1).strip()
                    break
            if not date:
                dm = re.search(r"(\d{4}-\d{2}-\d{2})", text)
                if dm:
                    date = dm.group(1)
            results.append({
                "id": f.stem,
                "title": title,
                "status": status,
                "date": date,
                "path": f"{proj['docs']}/adr/{f.name}",
                "project": key,
            })
    return results


def _scan_all_decisions() -> list[dict]:
    results = []
    adrs = _scan_adrs()
    for adr in adrs:
        results.append({
            "id": adr["id"],
            "title": adr["title"],
            "status": adr["status"],
            "date": adr.get("date", ""),
            "source": "ADR",
            "project": adr.get("project", ""),
            "path": adr.get("path", ""),
        })
    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    return results


def get_panorama_data() -> dict:
    from .requirements import scan_requirements
    reqs = scan_requirements()
    all_deps = []
    for req in reqs:
        for dep in req.get("dependencies", []):
            all_deps.append(dep)

    projects = _get_projects()
    data_flow = 'graph LR\n'
    proj_keys = list(projects.keys())
    for i, key in enumerate(proj_keys):
        data_flow += f'  P{i}["{projects[key]["name"]}"]\n'
    for i, dep in enumerate(all_deps[:8]):
        data_flow += f'  dep{i}["{dep.get("type", "?").replace(chr(34), chr(39))}"] -->|"{dep.get("relation", "")[:20].replace(chr(34), chr(39))}"| depT{i}["{dep.get("target", "?").replace("`", "").replace(chr(34), chr(39))}"]\n'

    dep_graph = 'graph TD\n'
    for i, dep in enumerate(all_deps[:8]):
        nid = f"dep{i}"
        tid = f"depT{i}"
        label = dep.get("type", "?").replace('"', "'")
        target = dep.get("target", "?").replace("`", "").replace('"', "'")
        rel = dep.get("relation", "").replace('"', "'")[:20]
        dep_graph += f'  {nid}["{label}"] -->|"{rel}"| {tid}["{target}"]\n'

    systems = []
    for req in reqs:
        for obj in req.get("exec_objects", []):
            obj_type = obj.get("type", "")
            if obj_type == "阶段目标" or obj_type == "工作项":
                systems.append({
                    "id": obj["id"],
                    "name": obj["title"],
                    "desc": f"来自 {req['project_name']}",
                    "project": req["project_name"],
                    "priority": obj.get("priority", "P2"),
                    "status": obj.get("status", "未知"),
                    "dep": obj.get("prerequisite", "无"),
                })

    adrs = _scan_adrs()

    return {
        "data_flow_mermaid": data_flow,
        "dependency_mermaid": dep_graph,
        "systems": systems[:10],
        "decisions": adrs,
    }


def get_dashboard_data(force: bool = False) -> dict:
    from .taskbase import get_task_base_data
    from .requirements import scan_requirements, scan_doc_links, extract_latest_changelog, _auto_extract_actions, _auto_extract_phases, _auto_current
    from .task_check import project_rule_status
    if not force:
        cached = _cache_get("dashboard")
        if cached is not None:
            return cached
    config_error = _get_config_error()
    if config_error:
        return {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config_error": config_error,
            "product": {"id": "", "name": "", "description": ""},
            "current": {"summary": "配置缺失", "doing": "请设置 product.yaml", "where": config_error},
            "phases": [],
            "projects": [],
            "project_rules": [],
            "doc_links": [],
            "actions": [],
            "latest_changes": [],
            "decisions": [],
            "tool_boundary": [],
        }
    data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "product": _get_product(),
        "current": _auto_current(),
        "phases": _auto_extract_phases(),
        "projects": {key: {"name": proj["name"]} for key, proj in _get_projects().items()},
        "project_rules": project_rule_status(),
        "doc_links": scan_doc_links(),
        "actions": _auto_extract_actions(),
        "latest_changes": extract_latest_changelog(),
        "decisions": _scan_all_decisions(),
        "tool_boundary": [
            {"tool": "pm-kit-web", "role": "本地服务与交互入口", "source": False, "next": "承载驾驶舱、API 和后续受控编辑"},
            {"tool": "docs/*.md", "role": "事实源、规则源、审计归档", "source": True, "next": "继续保持单一事实源"},
        ],
    }
    _cache_set("dashboard", data)
    return data


def _get_config_error():
    from .config import _get_config_error as _gce
    return _gce()


def _get_projects():
    from .config import _get_projects as _gp
    return _gp()
