import re
import time
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from .config import (
    CLOSING_REQUIRED_FIELDS,
    CLOSING_STATUSES,
    DOC_ROLE_MAP,
    HUMAN_GATE_TRANSITIONS,
    NORMALIZED_TO_LEGACY_STATUS,
    PRIORITY_ORDER,
    REASON_REQUIRED_TRANSITIONS,
    STATUS_COMPAT_MAP,
    TASK_STATUS_TRANSITIONS,
    VALID_TASK_STATUSES,
    _cache_get,
    _cache_invalidate,
    _cache_set,
    _get_projects,
    _get_product,
    _has_value,
    _invalidate_cache,
    _log_action,
    normalize_task_status,
    read_text,
    storage_task_status,
    validate_task_status_value,
)


def _extract_metadata_value(text: str, name: str) -> str:
    patterns = [
        rf"^>\s*{re.escape(name)}[：:]\s*(.+)$",
        rf"^{re.escape(name)}[：:]\s*(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def _extract_section_summary(text: str, title: str) -> str:
    match = re.search(rf"^##\s+[一二三四五六七八九十]+[、.．]\s*{re.escape(title)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_h2 = re.search(r"\n##\s", text[start:])
    body = text[start:start + next_h2.start()] if next_h2 else text[start:]
    lines = [line.strip() for line in body.strip().splitlines() if line.strip()]
    return "\n".join(lines[:8])


def _priority_rank(priority: str) -> int:
    return {"high": 0, "高": 0, "urgent": 0, "medium": 1, "中": 1, "important": 1, "low": 2, "低": 2, "normal": 2}.get(priority, 9)


def _doc_role_for_num(num: int) -> str:
    if num in DOC_ROLE_MAP:
        return DOC_ROLE_MAP[num]
    if 10 <= num <= 19:
        return "客观规则"
    if 20 <= num <= 99:
        return "需求专题"
    if num == 98:
        return "专项审计"
    if num == 99:
        return "规范审计"
    return "其他"


def _derive_requirement_status(tasks: list[dict]) -> str:
    if not tasks:
        return "未拆解"
    statuses = {task.get("normalized_status") or normalize_task_status(task.get("status", "")) for task in tasks}
    for status, label in [
        ("Blocked", "有阻塞"),
        ("Decision Needed", "待决策"),
        ("Review Needed", "待验收"),
        ("Executing", "执行中"),
        ("Planned", "已规划"),
        ("Ready for Plan", "待规划"),
    ]:
        if status in statuses:
            return label
    if statuses and statuses.issubset({"Closed", "Cancelled"}):
        return "已完成"
    return "未拆解"


def _requirement_status_class(status: str) -> str:
    if status in {"已完成"}:
        return "done"
    if status in {"执行中"}:
        return "current"
    if status in {"待验收"}:
        return "review"
    if status in {"有阻塞"}:
        return "blocked"
    if status in {"待决策"}:
        return "waiting"
    if status in {"已规划", "待规划"}:
        return "next"
    return ""


def _field_value(fields: dict, *names: str) -> str:
    for name in names:
        value = fields.get(name)
        if value:
            return value
    return ""


def _replace_or_insert_table_field(block: str, field_name: str, value: str) -> str:
    safe_value = str(value or "").strip().replace("|", "｜")
    pattern = rf"(\|\s*{re.escape(field_name)}\s*\|\s*)([^|\n]*)(\s*\|)"
    new_block, count = re.subn(pattern, rf"\g<1>{safe_value}\g<3>", block, count=1)
    if count:
        return new_block
    rows = list(re.finditer(r"^\|.+\|\s*$", block, re.M))
    if not rows:
        return block.rstrip() + f"\n\n| {field_name} | {safe_value} |\n"
    pos = rows[-1].end()
    return block[:pos] + f"\n| {field_name} | {safe_value} |" + block[pos:]


def validate_task_transition(obj: dict, new_status: str, payload=None):
    if payload is None:
        payload = _make_default_payload()
    old_normalized = obj.get("normalized_status") or normalize_task_status(obj.get("status", ""))
    new_normalized = validate_task_status_value(new_status)
    if old_normalized == new_normalized:
        return new_normalized
    allowed = TASK_STATUS_TRANSITIONS.get(old_normalized, set())
    if new_normalized not in allowed:
        raise HTTPException(status_code=409, detail=f"非法状态流转：{old_normalized} → {new_normalized}")
    required_reason = REASON_REQUIRED_TRANSITIONS.get((old_normalized, new_normalized))
    if required_reason and not _has_value(payload.reason):
        raise HTTPException(status_code=409, detail=f"该流转必须填写{required_reason}")
    required_human = HUMAN_GATE_TRANSITIONS.get((old_normalized, new_normalized))
    if required_human and not payload.human_confirmed:
        raise HTTPException(status_code=409, detail=f"该流转需要 Human Gate 确认：{required_human}")
    if (old_normalized, new_normalized) in HUMAN_GATE_TRANSITIONS and not _has_value(payload.decision_record) and new_normalized != "Closed":
        raise HTTPException(status_code=409, detail="Human Gate 流转必须填写决策记录")
    if new_normalized in CLOSING_STATUSES:
        missing = [label for key, label in CLOSING_REQUIRED_FIELDS.items() if not _has_value(obj.get(key, ""))]
        if not _has_value(payload.acceptance_result):
            missing = [m for m in missing if m != "验收结果"]
            missing.append("验收结果")
        if not _has_value(payload.closure_evidence):
            missing = [m for m in missing if m != "关闭证据"]
            missing.append("关闭证据")
        missing = list(dict.fromkeys(missing))
        if missing:
            raise HTTPException(status_code=409, detail="关闭前缺少字段：" + "、".join(missing))
        review = obj.get("review") or {}
        if review.get("required", False):
            review_status = review.get("status")
            review_ready = review.get("human_ready") is True
            skipped_with_reason = review_status == "skipped" and _has_value(review.get("reason", ""))
            if not ((review_status == "passed" and review_ready) or skipped_with_reason):
                raise HTTPException(status_code=409, detail="review.required=true 时关闭任务必须先通过检查或记录免审原因")
    if obj.get("human_gate") and new_normalized == "Closed" and not payload.human_confirmed:
        raise HTTPException(status_code=409, detail="存在 Human Gate，关闭前必须确认验收结果")
    return new_normalized


def _make_default_payload():
    from .main import ObjectUpdatePayload
    return ObjectUpdatePayload()


def build_transition_remark(old_status: str, new_status: str, payload) -> str:
    parts = []
    if payload.remark.strip():
        parts.append(payload.remark.strip())
    if payload.reason.strip():
        parts.append(f"原因：{payload.reason.strip()}")
    if payload.decision_record.strip():
        parts.append(f"决策记录：{payload.decision_record.strip()}")
    if payload.acceptance_result.strip():
        parts.append(f"验收结果：{payload.acceptance_result.strip()}")
    if payload.closure_evidence.strip():
        parts.append(f"关闭证据：{payload.closure_evidence.strip()}")
    if payload.human_confirmed:
        parts.append("Human Gate：已确认")
    if parts:
        return f"{old_status} → {new_status}；" + "；".join(parts)
    return ""


def write_object_status(project: str, doc_id: str, obj_id: str, new_status: str = "", remark: str = "") -> bool:
    projects = _get_projects()
    if project not in projects:
        return False
    proj = projects[project]
    proj_docs = proj["path"] / proj["docs"]
    if not proj_docs.exists():
        return False
    target_file = None
    for f in proj_docs.iterdir():
        if f.is_file() and f.name.endswith(".md") and f.name.startswith(f"{doc_id}-"):
            target_file = f
            break
    if not target_file or not target_file.exists():
        return False
    text = target_file.read_text(encoding="utf-8")
    obj_match = re.search(rf"###\s+\d+\.\d+\s+{re.escape(obj_id)}\b", text)
    if not obj_match:
        return False
    section_start = obj_match.end()
    next_section = re.search(r"\n###\s", text[section_start:])
    section_body = text[section_start:section_start + next_section.start()] if next_section else text[section_start:]
    new_section_body = section_body
    if new_status:
        status_row_match = re.search(r"\|\s*状态\s*\|\s*(.+?)\s*\|", new_section_body)
        if not status_row_match:
            return False
        stored_status = storage_task_status(new_status)
        new_section_body = new_section_body[:status_row_match.start(1)] + stored_status + new_section_body[status_row_match.end(1):]
    extra_updates = {}
    if remark:
        for prefix, field_name in [
            ("验收结果：", "验收结果"),
            ("关闭证据：", "关闭证据"),
        ]:
            marker = remark.find(prefix)
            if marker >= 0:
                start_value = marker + len(prefix)
                end_value = remark.find("；", start_value)
                value = remark[start_value:] if end_value == -1 else remark[start_value:end_value]
                if value.strip():
                    extra_updates[field_name] = value.strip()
        for field_name, value in extra_updates.items():
            new_section_body = _replace_or_insert_table_field(new_section_body, field_name, value)
    if remark:
        safe_remark = remark.replace("|", "｜")
        remark_row_match = re.search(r"\|\s*备注\s*\|\s*(.+?)\s*\|", new_section_body)
        if remark_row_match:
            new_section_body = new_section_body[:remark_row_match.start(1)] + safe_remark + new_section_body[remark_row_match.end(1):]
        else:
            last_table_row = list(re.finditer(r"\|.+\|", new_section_body))
            if last_table_row:
                pos = last_table_row[-1].end()
                new_section_body = new_section_body[:pos] + "\n| 备注 | " + safe_remark + " |" + new_section_body[pos:]
    full_new = text[:section_start] + new_section_body
    if next_section:
        full_new += text[section_start + next_section.start():]
    target_file.write_text(full_new, encoding="utf-8")
    _invalidate_cache()
    return True


def scan_requirements() -> list[dict]:
    cached = _cache_get("requirements")
    if cached is not None:
        return cached
    results = []
    for key, proj in _get_projects().items():
        proj_docs = proj["path"] / proj["docs"]
        if not proj_docs.exists():
            continue
        for f in sorted(proj_docs.iterdir()):
            if not f.is_file() or not f.name.endswith(".md"):
                continue
            m = re.match(r"^(\d{2})-", f.name)
            if not m:
                continue
            num = int(m.group(1))
            if num < 20 or num > 89:
                continue
            text = read_text(f)
            title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else f.stem
            status_match = re.search(r"^>\s*状态[：:]\s*(.+)$", text, re.MULTILINE)
            status = status_match.group(1).strip() if status_match else "未知"
            exec_objects = []

            obj_section_match = re.search(r"##\s+[一二三四五六七八九十]+[、.．]\s*.*执行对象", text)
            if obj_section_match:
                body_start = obj_section_match.end()
                next_h2 = re.search(r"\n##\s", text[body_start:])
                body = text[body_start:body_start + next_h2.start()] if next_h2 else text[body_start:]

                has_detailed_objects = bool(re.search(r"###\s+\d+\.\d+\s+\S+", body))
                if has_detailed_objects:
                    for sub_match in re.finditer(r"###\s+\d+\.\d+\s+(\S+?)\s*[：:]\s*(.+)", body):
                        obj_id = sub_match.group(1)
                        obj_title = sub_match.group(2).strip()
                        sub_body_start = sub_match.end()
                        next_sub = re.search(r"\n###\s", body[sub_body_start:])
                        sub_body = body[sub_body_start:sub_body_start + next_sub.start()] if next_sub else body[sub_body_start:]
                        fields = {}
                        for row in sub_body.splitlines():
                            cells = [c.strip() for c in row.split("|") if c.strip()]
                            if len(cells) == 2:
                                k, val = cells
                                if k and k not in ("字段", "---"):
                                    fields[k] = val
                        obj_type = _field_value(fields, "类型")
                        obj_status = _field_value(fields, "状态")
                        obj_priority = _field_value(fields, "优先级")
                        obj_prerequisite = _field_value(fields, "前置条件", "前置", "依赖对象", "前置对象")
                        block_reason = _field_value(fields, "阻塞原因")
                        exec_objects.append({
                            "id": obj_id,
                            "title": obj_title,
                            "type": obj_type,
                            "status": obj_status,
                            "normalized_status": normalize_task_status(obj_status),
                            "priority": obj_priority,
                            "priority_reason": _field_value(fields, "优先级原因"),
                            "prerequisite": obj_prerequisite,
                            "source": _field_value(fields, "来源"),
                            "input_text": _field_value(fields, "输入原文", "原始输入"),
                            "understanding": _field_value(fields, "目标理解 / 任务理解", "目标理解", "任务理解", "AI 理解"),
                            "plan_steps": _field_value(fields, "计划步骤"),
                            "scope": _field_value(fields, "预计范围", "修改范围", "影响范围"),
                            "risk": _field_value(fields, "风险", "遗留风险"),
                            "validation_method": _field_value(fields, "验证方式"),
                            "decision_point": _field_value(fields, "决策点", "人类确认点"),
                            "decision_needed": _field_value(fields, "需要决策什么"),
                            "human_gate": _field_value(fields, "Human Gate"),
                            "current_step": _field_value(fields, "当前步骤"),
                            "recent_action": _field_value(fields, "最近动作"),
                            "next_action": _field_value(fields, "下一动作"),
                            "block_reason": block_reason,
                            "completion_summary": _field_value(fields, "完成摘要"),
                            "validation_result": _field_value(fields, "验证结果"),
                            "closure_evidence": _field_value(fields, "关闭证据"),
                            "acceptance_result": _field_value(fields, "验收结果", "人类验收结果"),
                            "allowed_next_statuses": [],
                            "fields": fields,
                        })
                else:
                    table_pattern = r"\|\s*ID\s*\|\s*目标\s*\|\s*\n\|\s*[-—]+\s*\|\s*[-—]+\s*\|\s*\n((?:\|\s*.+?\s*\|\s*.+?\s*\|\s*\n?)+)"
                    table_match = re.search(table_pattern, body, re.MULTILINE)
                    if table_match:
                        table_body = table_match.group(1)
                        for row in table_body.splitlines():
                            cells = [c.strip() for c in row.split("|") if c.strip()]
                            if len(cells) >= 2 and cells[0] != "ID" and not re.match(r"^[-—]+$", cells[0]):
                                obj_id = cells[0]
                                obj_title = cells[1] if len(cells) > 1 else ""
                                exec_objects.append({
                                    "id": obj_id,
                                    "title": obj_title,
                                    "type": "工作项",
                                    "status": "",
                                    "normalized_status": "Ready for Plan",
                                    "priority": "",
                                    "priority_reason": "",
                                    "prerequisite": "",
                                    "source": "",
                                    "input_text": "",
                                    "understanding": "",
                                    "plan_steps": "",
                                    "scope": "",
                                    "risk": "",
                                    "validation_method": "",
                                    "decision_point": "",
                                    "decision_needed": "",
                                    "human_gate": "",
                                    "current_step": "",
                                    "recent_action": "",
                                    "next_action": "",
                                    "block_reason": "",
                                    "completion_summary": "",
                                    "validation_result": "",
                                    "closure_evidence": "",
                                    "acceptance_result": "",
                                    "allowed_next_statuses": [],
                                    "fields": {},
                                })

            obj_map = {o["id"]: o for o in exec_objects}
            for obj in exec_objects:
                if obj["prerequisite"]:
                    prereqs = [p.strip() for p in re.split(r"[,，、;；]", obj["prerequisite"]) if p.strip()]
                    blocked_by = []
                    for prereq in prereqs:
                        if prereq in obj_map and obj_map[prereq]["status"] not in ("已完成",):
                            blocked_by.append(prereq)
                    obj["blocked_by"] = blocked_by
                else:
                    obj["blocked_by"] = []
                normalized = obj.get("normalized_status") or normalize_task_status(obj.get("status", ""))
                obj["allowed_next_statuses"] = sorted(TASK_STATUS_TRANSITIONS.get(normalized, set()))
            dep_section = re.search(r"##\s+[一二三四五六七八九十]+[、.．]\s*依赖关系", text)
            dependencies = []
            if dep_section:
                dep_start = dep_section.end()
                next_h2_dep = re.search(r"\n##\s", text[dep_start:])
                dep_body = text[dep_start:dep_start + next_h2_dep.start()] if next_h2_dep else text[dep_start:]
                for row in dep_body.splitlines():
                    cells = [c.strip() for c in row.split("|") if c.strip()]
                    if len(cells) >= 3 and cells[0] != "类型" and not re.match(r"^[-—]+$", cells[0]):
                        dependencies.append({"type": cells[0], "target": cells[1], "relation": cells[2]})
            results.append({
                "id": m.group(1),
                "filename": f.name,
                "title": title,
                "status": status,
                "path": f"{proj['docs']}/{f.name}",
                "project": key,
                "project_name": proj["name"],
                "exec_objects": exec_objects,
                "dependencies": dependencies,
            })
    _cache_set("requirements", results)
    return results


def scan_doc_links() -> list[dict]:
    cached = _cache_get("doc_links")
    if cached is not None:
        return cached
    results = []
    for key, proj in _get_projects().items():
        proj_docs = proj["path"] / proj["docs"]
        if not proj_docs.exists():
            continue
        for f in sorted(proj_docs.iterdir()):
            if not f.is_file() or not f.name.endswith(".md"):
                continue
            m = re.match(r"^(\d{2})-", f.name)
            if not m:
                continue
            num = int(m.group(1))
            text = read_text(f)
            title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else f.stem
            results.append({
                "id": m.group(1),
                "title": title,
                "path": f"{proj['docs']}/{f.name}",
                "role": _doc_role_for_num(num),
                "project": key,
            })
    _cache_set("doc_links", results)
    return results


def _build_requirement_ai_context(item: dict) -> str:
    doc = item.get("requirement_doc", {})
    derived = item.get("derived", {})
    tasks = item.get("tasks", [])
    memos = item.get("memos", [])
    recommended = item.get("recommended_reading", [])
    lines = [
        "请基于以下 PM Kit 事实源讨论当前需求，不要把工具聚合结果视为事实源。",
        "",
        "【项目】",
        f"- 项目：{item.get('project_name', '')}",
        f"- 项目路径：{item.get('project_path', '')}",
        "",
        "【需求】",
        f"- 文档：{doc.get('path', '')}",
        f"- 标题：{doc.get('title', '')}",
        "",
        "【需求摘要】",
        f"- 目标：{doc.get('goal') or '未写入事实源'}",
        f"- 范围：{doc.get('scope') or '未写入事实源'}",
        f"- 成功标准：{doc.get('success') or '未写入事实源'}",
        "",
        "【执行状态】",
        f"- 当前状态：{derived.get('status', '')}",
        f"- 开放任务：{derived.get('open_task_count', 0)}",
        f"- 阻塞任务：{derived.get('blocked_task_count', 0)}",
        f"- 待决策任务：{derived.get('decision_needed_count', 0)}",
        f"- 待验收任务：{derived.get('review_needed_count', 0)}",
        f"- 最高优先级：{derived.get('highest_priority') or '无'}",
        "",
        "【关联任务】",
    ]
    if tasks:
        for task in tasks:
            lines.append(f"- {task.get('id', '')}：{task.get('title', '')}，状态：{task.get('normalized_status', '')}，优先级：{task.get('priority') or '无'}")
    else:
        lines.append("- 暂无关联任务")
    lines.extend(["", "【未处理输入】"])
    if memos:
        for memo in memos:
            lines.append(f"- {memo.get('id', '')}：{memo.get('title') or memo.get('content', '')}")
    else:
        lines.append("- 暂无关联未处理 Memo")
    lines.extend(["", "【推荐阅读】"])
    for path in recommended:
        lines.append(f"- {path}")
    lines.extend([
        "",
        "【约束提醒】",
        "- 动态状态以 task-base 为事实源",
        "- 未处理输入只来自 task-base/memos",
        "- 工具不是事实源",
        "- 工具不直接调用 AI、Skill 或 Agent",
        "- 修改规范、事实源边界、新增依赖或跨项目读取 / 写入必须触发 Human Gate",
    ])
    return "\n".join(lines)


def get_requirement_overview_data(force: bool = False) -> dict:
    from .taskbase import _load_task_base_task_details, _load_task_base_memo_details
    if not force:
        cached = _cache_get("requirement_overview")
        if cached is not None:
            return cached
    items = []
    sub_items_map = {}
    summary = {
        "requirements": 0,
        "open_tasks": 0,
        "blocked_tasks": 0,
        "decision_needed_tasks": 0,
        "review_needed_tasks": 0,
        "open_memos": 0,
        "high_priority_tasks": 0,
    }
    # Pre-load all tasks and memos for quick grouping
    all_tasks_by_req = {}  # requirement_doc_path -> [tasks]
    for project_key, proj in _get_projects().items():
        tasks = _load_task_base_task_details(project_key, proj)
        for task in tasks:
            req_doc = task.get("requirement_doc") or ""
            if req_doc:
                all_tasks_by_req.setdefault(req_doc, []).append(task)
    summary["open_tasks"] += sum(1 for t in all_tasks_by_req.values() for task in t if task.get("normalized_status") not in {"Closed", "Cancelled"})
    summary["blocked_tasks"] += sum(1 for t in all_tasks_by_req.values() for task in t if task.get("normalized_status") == "Blocked")
    summary["decision_needed_tasks"] += sum(1 for t in all_tasks_by_req.values() for task in t if task.get("normalized_status") == "Decision Needed")
    summary["review_needed_tasks"] += sum(1 for t in all_tasks_by_req.values() for task in t if task.get("normalized_status") == "Review Needed")
    summary["high_priority_tasks"] += sum(1 for t in all_tasks_by_req.values() for task in t if task.get("priority") == "high")
    for project_key, proj in _get_projects().items():
        tasks = _load_task_base_task_details(project_key, proj)
        memos = _load_task_base_memo_details(project_key, proj)
        summary["open_memos"] += sum(1 for memo in memos if memo.get("status") == "open")
        docs_dir = proj["path"] / proj["docs"]
        if not docs_dir.exists():
            continue
        for f in sorted(docs_dir.iterdir()):
            if not f.is_file() or not f.name.endswith(".md"):
                continue
            main_match = re.match(r"^(\d{2})-", f.name)
            sub_match = re.match(r"^(\d{2})\.(\d+)-", f.name)
            if not main_match and not sub_match:
                continue
            if sub_match:
                doc_num = int(sub_match.group(1))
            else:
                doc_num = int(main_match.group(1))
            if doc_num < 20 or doc_num > 59:
                continue
            text = read_text(f)
            title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else f.stem
            doc_path = str(f.relative_to(proj["path"]))
            doc_tasks = all_tasks_by_req.get(doc_path, [])
            if sub_match:
                linked_task = _extract_metadata_value(text, "关联任务")
                if linked_task:
                    linked_ids = {t.strip() for t in linked_task.split(",") if t.strip()}
                    doc_tasks = [task for task in doc_tasks if task.get("id") in linked_ids]
            doc_id = sub_match.group(0).rstrip("-") if sub_match else main_match.group(1)
            task_ids = {task.get("id") for task in doc_tasks}
            doc_memos = [
                memo for memo in memos
                if memo.get("status") == "open" and (
                    memo.get("linked_requirement_id") in {doc_id, f.name, f.stem}
                    or (memo.get("linked_task_id") and memo.get("linked_task_id") in task_ids)
                )
            ]
            highest_priority = ""
            if doc_tasks:
                highest_priority = sorted([task.get("priority", "") for task in doc_tasks], key=_priority_rank)[0]
                if _priority_rank(highest_priority) == 9:
                    highest_priority = ""
            derived = {
                "status": _derive_requirement_status(doc_tasks),
                "status_class": _requirement_status_class(_derive_requirement_status(doc_tasks)),
                "highest_priority": highest_priority,
                "open_task_count": sum(1 for task in doc_tasks if task.get("normalized_status") not in {"Closed", "Cancelled"}),
                "blocked_task_count": sum(1 for task in doc_tasks if task.get("normalized_status") == "Blocked"),
                "decision_needed_count": sum(1 for task in doc_tasks if task.get("normalized_status") == "Decision Needed"),
                "review_needed_count": sum(1 for task in doc_tasks if task.get("normalized_status") == "Review Needed"),
                "open_memo_count": len(doc_memos),
            }
            recommended = [doc_path]
            recommended.extend([task.get("path", "") for task in doc_tasks])
            recommended.extend([memo.get("path", "") for memo in doc_memos])
            parent_ref = _extract_metadata_value(text, "所属主需求")
            item = {
                "project_id": project_key,
                "project_name": proj["name"],
                "project_path": str(proj["path"]),
                "is_sub_requirement": bool(sub_match),
                "parent_doc_id": str(doc_num) if sub_match else None,
                "requirement_doc": {
                    "id": doc_id,
                    "filename": f.name,
                    "title": title,
                    "path": doc_path,
                    "created_at": _extract_metadata_value(text, "创建日期"),
                    "updated_at": _extract_metadata_value(text, "最后更新"),
                    "numbering": _extract_metadata_value(text, "编号归属"),
                    "role": _extract_metadata_value(text, "治理角色"),
                    "parent_ref": parent_ref,
                    "goal": _extract_section_summary(text, "目标"),
                    "scope": _extract_section_summary(text, "范围"),
                    "success": _extract_section_summary(text, "成功标准"),
                },
                "tasks": doc_tasks,
                "memos": doc_memos,
                "derived": derived,
                "recommended_reading": [path for path in recommended if path],
                "sub_requirements": [],
            }
            item["ai_context"] = _build_requirement_ai_context(item)
            if sub_match:
                parent_key = (project_key, str(doc_num))
                sub_items_map.setdefault(parent_key, []).append(item)
            else:
                items.append(item)
            summary["requirements"] += 1
    for item in items:
        parent_key = (item["project_id"], item["requirement_doc"]["id"])
        if parent_key in sub_items_map:
            item["sub_requirements"] = sub_items_map[parent_key]
            sub_task_ids = set()
            for sub in item["sub_requirements"]:
                for t in sub.get("tasks", []):
                    sub_task_ids.add(t.get("id"))
            item["tasks"] = [t for t in item.get("tasks", []) if t.get("id") not in sub_task_ids]
            all_items = list(item["tasks"])
            for sub in item["sub_requirements"]:
                sub_tasks = sub.get("tasks", [])
                if sub_tasks and all(t.get("normalized_status") in {"Closed", "Cancelled"} for t in sub_tasks):
                    all_items.append({"normalized_status": "Closed", "status": "Closed"})
                else:
                    all_items.append({"normalized_status": sub.get("derived", {}).get("status_class", "executing"), "status": sub.get("derived", {}).get("status", "")})
            item["derived"] = {
                "status": _derive_requirement_status(all_items),
                "status_class": _requirement_status_class(_derive_requirement_status(all_items)),
                "highest_priority": item["derived"].get("highest_priority", ""),
                "open_task_count": sum(1 for task in item["tasks"] if task.get("normalized_status") not in {"Closed", "Cancelled"}),
                "blocked_task_count": sum(1 for task in item["tasks"] if task.get("normalized_status") == "Blocked"),
                "decision_needed_count": sum(1 for task in item["tasks"] if task.get("normalized_status") == "Decision Needed"),
                "review_needed_count": sum(1 for task in item["tasks"] if task.get("normalized_status") == "Review Needed"),
                "open_memo_count": item["derived"].get("open_memo_count", 0),
            }
    data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "items": items,
        "scope": "首版覆盖 product.yaml 中配置的项目；PMKIT-003 当前按 PM Kit 自身项目落地，模型保留多项目字段。",
    }
    _cache_set("requirement_overview", data)
    return data


def extract_latest_changelog(limit: int = 10) -> list[dict]:
    entries = []
    import datetime as _dt
    for key, proj in _get_projects().items():
        changelog_path = proj["path"] / proj["docs"] / "01-更新日志.md"
        text = read_text(changelog_path)
        logs_dir = proj["path"] / proj["docs"] / "logs"

        date_sections = re.split(r'(?=## \d{4}-\d{2}-\d{2})', text)
        for section in date_sections:
            date_match = re.search(r'## (\d{4}-\d{2}-\d{2})', section)
            if not date_match:
                continue
            date_str = date_match.group(1)

            for match in re.finditer(r'\|\s*\d+\s*\|\s*([^\|]+)\s*\|\s*\[详情\]\(logs/([^\)]+)\)\s*\|', section):
                title = match.group(1).strip()
                detail_file = match.group(2).strip()

                sort_date = None
                detail_path = logs_dir / detail_file
                if detail_path.exists():
                    try:
                        st = detail_path.stat()
                        # 优先使用创建时间(birthtime)，回退到修改时间(mtime)
                        birthtime = getattr(st, 'st_birthtime', None)
                        if birthtime is None:
                            birthtime = st.st_mtime
                        sort_date = _dt.datetime.fromtimestamp(birthtime).isoformat()
                    except Exception:
                        pass

                if not sort_date:
                    sort_date = date_str + "T00:00:00"
                    tz = _dt.datetime.now(_dt.timezone.utc).astimezone().tzinfo
                    tz_offset = tz.utcoffset(None)
                    tz_str = f"{tz_offset.days * 24 + tz_offset.seconds // 3600:+03d}:{((tz_offset.seconds // 60) % 60):02d}"
                    sort_date = sort_date + tz_str

                entries.append({
                    "date": sort_date,
                    "title": title,
                    "summary": "",
                    "project": key,
                    "detail_file": detail_file
                })
    entries.sort(key=lambda x: x["date"], reverse=True)
    return entries[:limit]


def _auto_extract_actions(limit: int = 8) -> list[dict]:
    from .taskbase import _load_task_base_tasks
    candidates = []
    tb_tasks = _load_task_base_tasks()
    tb_task_ids = {task["id"] for task in tb_tasks}

    reqs = scan_requirements()
    for req in reqs:
        for obj in req.get("exec_objects", []):
            obj_id = obj.get("id", "")
            if obj_id and obj_id in tb_task_ids:
                continue
            if obj.get("type") == "工作项" and obj.get("status") not in ("已完成",):
                candidates.append({
                    "id": obj["id"],
                    "title": obj["title"],
                    "priority": obj.get("priority", "低"),
                    "status": obj.get("status", "未知"),
                    "project": req["project_name"],
                    "doc": req["title"],
                })

    for task in tb_tasks:
        if task.get("status") not in ("Closed", "Cancelled"):
            candidates.append({
                "id": task["id"],
                "title": task["title"],
                "priority": task.get("priority", "低"),
                "status": task.get("status", "未知"),
                "project": task.get("project_name", ""),
                "doc": task.get("doc_title", ""),
            })

    candidates.sort(key=lambda x: PRIORITY_ORDER.get(x.get("priority", "低"), 3))
    return candidates[:limit]


def _auto_extract_phases() -> list[dict]:
    reqs = scan_requirements()
    phases = []
    for req in reqs:
        for obj in req.get("exec_objects", []):
            obj_type = obj.get("type", "")
            if obj_type == "阶段目标" or obj_type == "工作项":
                obj_status = obj.get("status", "")
                normalized_status = obj.get("normalized_status", "")
                if obj_status == "已完成" or normalized_status == "Closed":
                    phase_status = "done"
                elif obj_status == "进行中" or normalized_status == "Executing":
                    phase_status = "current"
                else:
                    phase_status = "next"
                phases.append({
                    "id": obj["id"],
                    "title": obj["title"],
                    "status": phase_status,
                    "desc": f"来自 {req['project_name']}/{req['title']}",
                })
    if not phases:
        for req in reqs:
            if req.get("status") and req["status"] not in ("未知",):
                phases.append({
                    "id": req["id"],
                    "title": req["title"],
                    "status": "current" if req["status"] == "进行中" else "done" if req["status"] == "已完成" else "next",
                    "desc": f"{req['project_name']} 需求",
                })
    return phases


def _auto_current() -> dict:
    reqs = scan_requirements()
    all_objects = []
    for req in reqs:
        for obj in req.get("exec_objects", []):
            all_objects.append(obj)
    total = len(all_objects)
    done = sum(1 for o in all_objects if o.get("status") == "已完成")
    in_progress = sum(1 for o in all_objects if o.get("status") == "进行中")
    summary = f"{total} 个执行对象，{done} 个已完成，{in_progress} 个进行中"
    doing = "暂无进行中对象"
    priority_sorted = sorted(
        [o for o in all_objects if o.get("status") == "进行中"],
        key=lambda x: PRIORITY_ORDER.get(x.get("priority", "低"), 3),
    )
    if priority_sorted:
        top = priority_sorted[0]
        doing = f"{top['id']}: {top['title']}"
    completion_rate = (done / total * 100) if total > 0 else 0
    if completion_rate >= 80:
        where = f"整体完成率 {completion_rate:.0f}%，接近收尾"
    elif completion_rate >= 50:
        where = f"整体完成率 {completion_rate:.0f}%，过半推进中"
    elif completion_rate > 0:
        where = f"整体完成率 {completion_rate:.0f}%，持续推进中"
    else:
        where = "尚无已完成对象"
    return {"summary": summary, "doing": doing, "where": where}
