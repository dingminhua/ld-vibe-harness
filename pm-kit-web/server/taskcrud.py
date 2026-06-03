"""task-base task CRUD API endpoints.

Provides POST/PUT/DELETE endpoints for task-base/tasks/{task_id}.yaml
following the state machine and L0 constraints defined in 08-项目管理对象规范.
"""
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .config import (
    CLOSING_REQUIRED_FIELDS,
    HUMAN_GATE_TRANSITIONS,
    REASON_REQUIRED_TRANSITIONS,
    TASK_STATUS_TRANSITIONS,
    VALID_TASK_STATUSES,
    _cache_invalidate,
    _get_projects,
    _has_value,
    _log_action,
    normalize_task_status,
    read_text,
    validate_task_status_value,
)
from .taskbase import _generate_task_base_index, _read_yaml_file

router = APIRouter(prefix="/api/task-base", tags=["task-base-crud"])


# ---------- Payload models ----------

class TaskCreatePayload(BaseModel):
    task_id: str
    requirement_doc: Optional[str] = None
    title: str
    description: str = ""
    priority: str = "P1"
    status: str = "Planned"
    completion_criteria: str = ""
    dependencies: list[str] = []
    tags: list[str] = []
    acceptance: str = ""


class TaskUpdatePayload(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    dependencies: Optional[list[str]] = None
    completion_criteria: Optional[str] = None
    acceptance: Optional[str] = None
    tags: Optional[list[str]] = None
    block_reason: Optional[str] = None
    decision_point: Optional[str] = None
    completion_summary: Optional[str] = None
    validation_result: Optional[str] = None
    closure_evidence: Optional[str] = None
    acceptance_result: Optional[str] = None
    human_confirmed: Optional[bool] = None
    reason: Optional[str] = None


# ---------- Helpers ----------

def _task_base_dir_for_project(project_key: str) -> Optional[Path]:
    proj = _get_projects().get(project_key)
    if not proj:
        return None
    return proj["path"] / proj.get("task_base", "task-base")


def _find_default_project() -> str:
    """Return the first configured project key (fallback for single-project setups)."""
    projects = _get_projects()
    return next(iter(projects), "main")


def _load_all_task_ids() -> set[str]:
    ids = set()
    for proj_key, proj in _get_projects().items():
        tasks_dir = proj["path"] / proj.get("task_base", "task-base") / "tasks"
        if not tasks_dir.exists():
            continue
        for task_file in tasks_dir.glob("*.yaml"):
            data = _read_yaml_file(task_file)
            task_id = data.get("id", "")
            if task_id:
                ids.add(task_id)
    return ids


def _find_task_yaml(task_id: str, project_key: Optional[str] = None):
    """Locate the YAML file for a given task_id. Returns (path, project_key) or (None, None)."""
    targets = {project_key} if project_key else _get_projects().keys()
    for proj_key in targets:
        proj = _get_projects().get(proj_key)
        if not proj:
            continue
        tasks_dir = proj["path"] / proj.get("task_base", "task-base") / "tasks"
        if not tasks_dir.exists():
            continue
        yaml_path = tasks_dir / f"{task_id}.yaml"
        if yaml_path.exists():
            return yaml_path, proj_key
    return None, None


def _review_gate_satisfied(task_data: dict) -> tuple[bool, str]:
    review = task_data.get("review") or {}
    if not review.get("required", False):
        return True, ""
    review_status = review.get("status")
    if review_status == "passed" and review.get("human_ready") is True:
        return True, ""
    if review_status == "skipped" and _has_value(review.get("reason", "")):
        return True, ""
    return False, f"review.required=true 时关闭任务必须满足 review.status=passed 且 human_ready=true，或 review.status=skipped 且填写 reason。当前 review.status={review_status}, human_ready={review.get('human_ready')}"


def _validate_task_id_format(task_id: str) -> str:
    """Validate that task_id matches {PREFIX}-{NNN} format. Returns the prefix."""
    m = re.match(r"^([A-Z]+)-(\d+)$", task_id)
    if not m:
        raise HTTPException(status_code=400, detail="task_id 必须匹配 {PREFIX}-{NNN} 格式，如 PMKIT-001")
    return m.group(1)


def _validate_status_transition(old_status: str, new_status: str, payload: TaskUpdatePayload):
    """Validate a state machine transition per 08 §3.2/3.3/3.5."""
    old_norm = normalize_task_status(old_status)
    new_norm = validate_task_status_value(new_status)

    if old_norm == new_norm:
        return new_norm

    allowed = TASK_STATUS_TRANSITIONS.get(old_norm, set())
    if new_norm not in allowed:
        raise HTTPException(status_code=409, detail=f"非法状态流转：{old_norm} → {new_norm}。允许值：{sorted(allowed)}")

    # Check reason-required transitions
    reason_key = (old_norm, new_norm)
    if reason_key in REASON_REQUIRED_TRANSITIONS:
        reason_label = REASON_REQUIRED_TRANSITIONS[reason_key]
        if not _has_value(payload.reason or ""):
            raise HTTPException(status_code=400, detail=f"该流转必须填写{reason_label}（reason 字段）")

    # Check Human Gate transitions
    if reason_key in HUMAN_GATE_TRANSITIONS:
        if not payload.human_confirmed:
            gate_label = HUMAN_GATE_TRANSITIONS[reason_key]
            raise HTTPException(status_code=409, detail=f"该流转需要 Human Gate 确认：{gate_label}。设置 human_confirmed=true")

    # Check closing required fields
    if new_norm == "Closed":
        missing = []
        for field_key, field_label in CLOSING_REQUIRED_FIELDS.items():
            val = getattr(payload, field_key, None) or ""
            if not _has_value(val):
                missing.append(field_label)
        if missing:
            raise HTTPException(status_code=400, detail=f"关闭前缺少字段：{'、'.join(missing)}")
        task_path, _ = _find_task_yaml(payload.task_id if hasattr(payload, "task_id") else "")
        if task_path:
            task_data = _read_yaml_file(task_path)
            review_ok, review_error = _review_gate_satisfied(task_data)
            if not review_ok:
                raise HTTPException(status_code=409, detail=review_error)

    return new_norm


def _find_default_requirements_doc(project_key: str) -> Optional[Path]:
    """Find the first 20-59 doc that has an execution objects table."""
    proj = _get_projects().get(project_key)
    if not proj:
        return None
    docs_dir = proj["path"] / proj["docs"]
    if not docs_dir.exists():
        return None
    for f in sorted(docs_dir.iterdir()):
        if not f.is_file() or not f.name.endswith(".md"):
            continue
        m = re.match(r"^(\d{2})-", f.name)
        if not m:
            continue
        num = int(m.group(1))
        if num < 20 or num > 59:
            continue
        text = read_text(f)
        if "执行对象" in text:
            return f
    return None


def _append_to_requirements_table(doc_path: Path, task_id: str, goal: str) -> bool:
    """Append a new row to the execution objects table in a requirements doc.

    The table format is:
    | ID | 目标 |
    | --- | --- |
    | PMKIT-001 | ... |

    We insert before the closing section or after the last row.
    """
    text = doc_path.read_text(encoding="utf-8")

    # Find the execution objects section
    obj_section = re.search(r"##\s+[一二三四五六七八九十]+[、.．]\s*.*执行对象", text)
    if not obj_section:
        return False

    body_start = obj_section.end()
    next_h2 = re.search(r"\n##\s", text[body_start:])
    section_text = text[body_start:body_start + next_h2.start()] if next_h2 else text[body_start:]

    # Find the table — look for | ID | 目标 | header
    table_pattern = r"(\|\s*ID\s*\|\s*目标\s*\|\s*\n\|\s*[-—]+\s*\|\s*[-—]+\s*\|\s*\n)"
    table_match = re.search(table_pattern, section_text)
    if not table_match:
        return False

    header_end = table_match.end()
    # Find the last row in the table
    table_remainder = section_text[header_end:]
    rows = list(re.finditer(r"^\|[^|\n]+\|[^|\n]*\|\s*$", table_remainder, re.MULTILINE))

    if rows:
        last_row_end = rows[-1].end()
        insert_pos = header_end + last_row_end
    else:
        insert_pos = header_end

    new_row = f"| {task_id} | {goal} |\n"
    new_section_text = section_text[:insert_pos - header_end] + new_row + section_text[insert_pos - header_end:]
    full_new = text[:body_start] + new_section_text
    if next_h2:
        full_new += text[body_start + next_h2.start():]

    doc_path.write_text(full_new, encoding="utf-8")
    return True


# ---------- API Endpoints ----------

@router.post("/tasks/", status_code=201)
async def create_task(body: TaskCreatePayload):
    """Create a new task-base task.

    Follows L0 constraint: requirements doc first, then task-base YAML.
    """
    # Validate task_id format
    prefix = _validate_task_id_format(body.task_id)

    # Check no duplicate
    all_task_ids = _load_all_task_ids()
    if body.task_id in all_task_ids:
        raise HTTPException(status_code=409, detail=f"Task {body.task_id} 已存在")

    # Validate initial status
    initial_status = normalize_task_status(body.status)
    if initial_status not in ("Planned", "Ready for Plan"):
        raise HTTPException(status_code=400, detail="新建任务的初始状态必须是 Planned 或 Ready for Plan")

    # Validate priority
    if body.priority not in ("P0", "P1", "P2", "P3"):
        raise HTTPException(status_code=400, detail="priority 必须是 P0、P1、P2 或 P3")

    project_key = _find_default_project()
    proj = _get_projects().get(project_key)
    if not proj:
        raise HTTPException(status_code=500, detail="未找到可用项目")

    tasks_dir = proj["path"] / proj.get("task_base", "task-base") / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    # Step 1 (L0): Append to requirements doc execution objects table
    if body.requirement_doc:
        proj = _get_projects().get(project_key)
        if proj:
            req_doc_path = proj["path"] / body.requirement_doc
            if req_doc_path.exists():
                goal = body.description if body.description else body.title
                success = _append_to_requirements_table(req_doc_path, body.task_id, goal)
                if not success:
                    _log_action("create_task", body.task_id, "需求文档执行对象表追加失败（非致命）")

    # Step 2: Create task YAML
    today = datetime.now().strftime("%Y-%m-%d")
    task_yaml = tasks_dir / f"{body.task_id}.yaml"
    if task_yaml.exists():
        raise HTTPException(status_code=409, detail=f"Task 文件 {task_yaml} 已存在")

    task_data = {
        "id": body.task_id,
        "requirement_doc": body.requirement_doc,
        "parent_id": None,
        "title": body.title,
        "status": initial_status,
        "priority": body.priority,
        "dependencies": body.dependencies or [],
        "created_at": today,
        "updated_at": today,
        "closed_at": None,
        "acceptance": body.acceptance or body.completion_criteria or "待规划",
        "close_evidence": None,
        "review": {
            "required": False,
            "status": None,
            "reason": None,
        },
        "source": "manual",
        "tags": body.tags or [],
    }

    with open(task_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(task_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Step 3: Index is now generated on-demand, no rebuild needed

    _log_action("create_task", body.task_id, f"status={initial_status}, priority={body.priority}")
    _cache_invalidate()

    return {"success": True, "task": task_data, "project": project_key}


@router.put("/tasks/{task_id}")
async def update_task(task_id: str, body: TaskUpdatePayload):
    """Update a task-base task.

    Validates status transitions per the state machine in 08 §3.4.
    If status changes to Review Needed, flags for audit check.
    """
    task_path, project_key = _find_task_yaml(task_id)
    if not task_path:
        raise HTTPException(status_code=404, detail=f"Task {task_id} 不存在")

    current_data = _read_yaml_file(task_path)
    if not current_data:
        raise HTTPException(status_code=500, detail=f"Task {task_id} YAML 解析失败")

    old_status = current_data.get("status", "Ready for Plan")

    # Validate status transition if status is being updated
    if body.status is not None:
        # Attach task_id to payload for closing field check
        body.task_id = task_id  # type: ignore
        new_status = _validate_status_transition(old_status, body.status, body)
        current_data["status"] = new_status

        # Check reason-required for block/cancel transitions
        reason_key = (normalize_task_status(old_status), new_status)
        if reason_key in REASON_REQUIRED_TRANSITIONS and body.reason:
            reason_label = REASON_REQUIRED_TRANSITIONS[reason_key]
            current_data[f"{reason_label}"] = body.reason

        # If transitioning to Review Needed, set review fields
        if new_status == "Review Needed":
            if "review" not in current_data or current_data["review"] is None:
                current_data["review"] = {}
            current_data["review"]["required"] = True
            current_data["review"]["status"] = "pending"

        # If transitioning to Closed, set closing fields
        if new_status == "Closed":
            today = datetime.now().strftime("%Y-%m-%d")
            current_data["closed_at"] = today
            if body.completion_summary:
                current_data["completion_summary"] = body.completion_summary
            if body.validation_result:
                current_data["validation_result"] = body.validation_result
            if body.closure_evidence:
                current_data["close_evidence"] = body.closure_evidence
            if body.acceptance_result:
                current_data["acceptance_result"] = body.acceptance_result

    # Update other fields
    update_map = {
        "priority": body.priority,
        "title": body.title,
        "description": body.description,
        "dependencies": body.dependencies,
        "acceptance": body.acceptance,
        "tags": body.tags,
        "block_reason": body.block_reason,
        "decision_point": body.decision_point,
        "completion_summary": body.completion_summary,
        "validation_result": body.validation_result,
        "closure_evidence": body.closure_evidence,
        "acceptance_result": body.acceptance_result,
    }

    for key, value in update_map.items():
        if value is not None:
            current_data[key] = value

    current_data["updated_at"] = datetime.now().strftime("%Y-%m-%d")

    # Write back
    with open(task_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(current_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Index is now generated on-demand, no rebuild needed

    status_msg = f"status {old_status} → {current_data['status']}" if body.status else "fields updated"
    _log_action("update_task", task_id, status_msg)
    _cache_invalidate()

    return {"success": True, "task": current_data, "project": project_key}



