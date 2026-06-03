import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import (
    _audit_log,
    _cache_invalidate,
    _get_config,
    _get_config_error,
    _get_product,
    _get_projects,
    _invalidate_cache,
    _log_action,
    normalize_task_status,
    validate_task_status_value,
)
from .taskbase import (
    TaskBaseMemoUpdatePayload,
    _generate_task_base_index,
    _get_all_memos,
    add_memo_entry,
    delete_memo_entry,
    get_task_base_data,
    parse_memo_file,
    update_memo_entry,
    update_task_base_memo,
)
from .requirements import (
    build_transition_remark,
    get_requirement_overview_data,
    scan_requirements,
    validate_task_transition,
    write_object_status,
)
from .views import (
    get_action_board_data,
    get_dashboard_data,
    get_panorama_data,
    get_pm_overview_data,
    get_task_detail_data,
    get_task_health_data,
    get_waiting_decisions_data,
)
from .taskbase import (
    _load_task_base_task_details,
)
from .taskcrud import router as taskcrud_router
from .task_check import (
    _check_task_check_trigger,
    _perform_task_check,
    _trigger_pending_task_checks,
    _update_task_review_status,
    audit_project_rules,
    audit_task_base_data,
    project_rule_status,
)


class ObjectUpdatePayload(BaseModel):
    status: str = ""
    remark: str = ""
    reason: str = ""
    decision_record: str = ""
    acceptance_result: str = ""
    closure_evidence: str = ""
    human_confirmed: bool = False


class ReopenPayload(BaseModel):
    reason: str
    scope: str = ""
    evidence_review: str = ""
    human_confirmed: bool = False


app = FastAPI(title="Trae PM Kit", version="1.0.0")

# Mount task-base CRUD router
app.include_router(taskcrud_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_client_dir = str(Path(__file__).resolve().parent.parent / "client")
app.mount("/client", StaticFiles(directory=_client_dir), name="client")


@app.get("/api/config")
async def config():
    product = _get_product()
    projects = _get_projects()
    config_error = _get_config_error()
    return {
        "product": {
            "id": product["id"],
            "name": product["name"],
            "description": product["description"],
        },
        "projects": {key: {"name": proj["name"]} for key, proj in projects.items()},
        "config_error": config_error,
    }


@app.get("/api/panorama")
async def panorama():
    return get_panorama_data()


@app.get("/api/readme/{project}")
async def readme(project: str):
    proj = _get_projects().get(project)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    readme_path = Path(proj["path"]) / "README.md"
    if not readme_path.exists():
        return {"project": project, "content": "", "exists": False}
    from .config import read_text
    text = read_text(readme_path)
    return {"project": project, "content": text, "exists": True}


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).resolve().parent.parent / "client" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/dashboard")
async def dashboard():
    return get_dashboard_data()


@app.post("/api/refresh")
async def refresh():
    global _config
    from .config import _config as _cfg_ref
    _cfg_ref = None
    _cache_invalidate()
    return {"success": True, "dashboard": get_dashboard_data(force=True)}


@app.get("/api/projects")
async def projects():
    return {"projects": project_rule_status()}


@app.get("/api/pm/overview")
async def pm_overview():
    return get_pm_overview_data()


@app.get("/api/pm/waiting-decisions")
async def pm_waiting_decisions():
    return get_waiting_decisions_data()


@app.get("/api/pm/action-board")
async def pm_action_board():
    return get_action_board_data()


@app.get("/api/pm/requirement-overview")
async def pm_requirement_overview():
    return get_requirement_overview_data()


@app.get("/api/pm/task-base")
async def pm_task_base():
    return get_task_base_data()


@app.put("/api/pm/task-base/memos/{project}/{memo_id}")
async def pm_update_task_base_memo(project: str, memo_id: str, body: TaskBaseMemoUpdatePayload = None):
    if body is None:
        body = TaskBaseMemoUpdatePayload()
    result = update_task_base_memo(project, memo_id, body)
    _log_action("update_task_base_memo", f"{project}/{memo_id}", f"status → {result.get('status')}")
    return {"success": True, "memo": result}


@app.get("/api/pm/task-health")
async def pm_task_health():
    return get_task_health_data()


@app.get("/api/pm/tasks/{project}/{doc_id}/{obj_id}")
async def pm_task_detail(project: str, doc_id: str, obj_id: str):
    return get_task_detail_data(project, doc_id, obj_id)


@app.get("/api/rules/audit")
async def rules_audit():
    return audit_project_rules()


@app.get("/api/task-base/audit")
async def task_base_audit():
    return audit_task_base_data()


@app.get("/api/docs")
async def docs():
    from .requirements import scan_doc_links
    return {"docs": scan_doc_links()}


@app.get("/api/requirements")
async def requirements(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    obj_status: Optional[str] = Query(None),
    obj_type: Optional[str] = Query(None),
):
    results = scan_requirements()
    if status:
        results = [r for r in results if r.get("status") == status]
    if project:
        results = [r for r in results if r.get("project") == project]
    if search:
        s = search.lower()
        results = [r for r in results if s in r.get("title", "").lower() or any(s in o.get("title", "").lower() for o in r.get("exec_objects", []))]
    if priority:
        results = [r for r in results if any(o.get("priority") == priority for o in r.get("exec_objects", []))]
    if obj_status:
        for r in results:
            r["exec_objects"] = [o for o in r.get("exec_objects", []) if o.get("status") == obj_status]
    if obj_type:
        for r in results:
            r["exec_objects"] = [o for o in r.get("exec_objects", []) if o.get("type") == obj_type]
    return {"requirements": results}


@app.put("/api/requirements/{project}/{doc_id}/objects/{obj_id}")
async def update_object_status(project: str, doc_id: str, obj_id: str, body: ObjectUpdatePayload = None):
    if body is None:
        body = ObjectUpdatePayload()
    new_status = body.status.strip()
    remark = body.remark.strip()
    if not new_status and not remark:
        raise HTTPException(status_code=400, detail="Missing 'status' or 'remark' field")
    from .views import _find_task_object
    req, current_obj = _find_task_object(project, doc_id, obj_id)
    normalized_status = ""
    old_normalized = current_obj.get("normalized_status") or normalize_task_status(current_obj.get("status", ""))
    effective_remark = remark
    if new_status:
        normalized_status = validate_task_transition(current_obj, new_status, body)
        transition_remark = build_transition_remark(old_normalized, normalized_status, body)
        effective_remark = transition_remark or remark
    success = write_object_status(project, doc_id, obj_id, normalized_status, effective_remark)
    if not success:
        raise HTTPException(status_code=404, detail="Object not found or update failed")
    detail_parts = []
    if normalized_status:
        detail_parts.append(f"status {current_obj.get('normalized_status') or current_obj.get('status')} → {normalized_status}")
    if effective_remark:
        detail_parts.append(f"remark → {effective_remark}")
    _log_action("update_object", f"{project}/{doc_id}/{obj_id}", "; ".join(detail_parts))
    updated_obj = None
    for updated_req in scan_requirements():
        if updated_req.get("project") == project and updated_req.get("id") == doc_id:
            for obj in updated_req.get("exec_objects", []):
                if obj.get("id") == obj_id:
                    updated_obj = obj
                    break
    return {"success": True, "object": updated_obj}


@app.get("/api/doc")
async def doc(path: str = Query(...)):
    if path.startswith("/") or ".." in Path(path).parts:
        raise HTTPException(status_code=400, detail="Invalid path")
    for key, proj in _get_projects().items():
        file_path = proj["path"] / path
        if file_path.exists() and file_path.is_file():
            try:
                file_path.relative_to(proj["path"])
            except ValueError:
                raise HTTPException(status_code=400, detail="Path outside project")
            return {"path": path, "content": file_path.read_text(encoding="utf-8")}
    raise HTTPException(status_code=404, detail="Document not found")


@app.get("/api/memos/stats")
async def memo_stats():
    all_memos = _get_all_memos()
    stats = {}
    for project, entries in all_memos.items():
        stats[project] = {
            "total": len(entries),
            "pending": sum(1 for e in entries if e.status == "pending"),
            "in_progress": sum(1 for e in entries if e.status == "in_progress"),
            "done": sum(1 for e in entries if e.status == "done"),
            "cancelled": sum(1 for e in entries if e.status == "cancelled"),
            "by_type": {},
            "by_priority": {},
        }
        for e in entries:
            stats[project]["by_type"][e.type] = stats[project]["by_type"].get(e.type, 0) + 1
            stats[project]["by_priority"][e.priority] = stats[project]["by_priority"].get(e.priority, 0) + 1
    return {"stats": stats}


@app.get("/api/memos")
async def list_memos(
    project: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    all_memos = _get_all_memos()
    entries = []
    for proj_key, proj_entries in all_memos.items():
        if project and proj_key != project:
            continue
        entries.extend(proj_entries)
    if type:
        entries = [e for e in entries if e.type == type]
    if status:
        entries = [e for e in entries if e.status == status]
    if priority:
        entries = [e for e in entries if e.priority == priority]
    if search:
        s = search.lower()
        entries = [e for e in entries if s in e.content.lower() or s in e.group_title.lower()]
    return {"memos": [e.to_dict() for e in entries]}


@app.get("/api/memos/{project}")
async def list_project_memos(
    project: str,
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    if project not in _get_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    all_memos = _get_all_memos()
    entries = all_memos.get(project, [])
    if type:
        entries = [e for e in entries if e.type == type]
    if status:
        entries = [e for e in entries if e.status == status]
    if priority:
        entries = [e for e in entries if e.priority == priority]
    if search:
        s = search.lower()
        entries = [e for e in entries if s in e.content.lower() or s in e.group_title.lower()]
    return {"memos": [e.to_dict() for e in entries]}


@app.put("/api/memos/{project}/{entry_id}")
async def update_memo(project: str, entry_id: str, body: dict = None):
    if project not in _get_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    if body is None:
        body = {}
    result = update_memo_entry(project, entry_id, body)
    if not result:
        raise HTTPException(status_code=404, detail="Entry not found or update failed")
    _log_action("update_memo", f"{project}/{entry_id}", str(body))
    return {"success": True, "entry": result.to_dict()}


@app.post("/api/memos/{project}")
async def create_memo(project: str, body: dict = None):
    if project not in _get_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    if body is None:
        body = {}
    if not body.get("content"):
        raise HTTPException(status_code=400, detail="Missing 'content' field")
    result = add_memo_entry(project, body)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to add entry")
    _log_action("create_memo", f"{project}/{result.id}", body.get("content", "")[:80])
    return {"success": True, "entry": result.to_dict()}


@app.delete("/api/memos/{project}/{entry_id}")
async def delete_memo(project: str, entry_id: str):
    if project not in _get_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    success = delete_memo_entry(project, entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found or delete failed")
    _log_action("delete_memo", f"{project}/{entry_id}")
    return {"success": True}


@app.get("/api/audit-log")
async def get_audit_log(limit: int = Query(50, ge=1, le=200)):
    return {"logs": _audit_log[-limit:]}


@app.get("/api/task-base/index")
async def get_task_base_index():
    """实时生成索引视图，不依赖持久化索引文件。"""
    results = _generate_task_base_index()
    return {
        "results": results,
        "generated_at": datetime.now().isoformat(),
    }


@app.get("/api/pm/task-check/trigger")
async def pm_trigger_task_check(task_id: Optional[str] = Query(None)):
    if task_id:
        for project_key, proj in _get_projects().items():
            tasks = _load_task_base_task_details(project_key, proj)
            task = next((t for t in tasks if t.get("id") == task_id), None)
            if task:
                if _check_task_check_trigger(task):
                    check_result = _perform_task_check(task)
                    _update_task_review_status(project_key, task_id, check_result)
                    return {"success": True, "check": check_result}
                else:
                    return {"success": False, "message": "任务不满足检查触发条件"}
        return {"success": False, "message": "未找到任务"}
    else:
        results = _trigger_pending_task_checks()
        return {"success": True, "count": len(results), "checks": results}


@app.get("/api/pm/task-check/status/{task_id}")
async def pm_get_task_check_status(task_id: str):
    for project_key, proj in _get_projects().items():
        tasks = _load_task_base_task_details(project_key, proj)
        task = next((t for t in tasks if t.get("id") == task_id), None)
        if task:
            review = task.get("review", {})
            return {
                "task_id": task_id,
                "task_title": task.get("title"),
                "status": task.get("status"),
                "review_status": review.get("status"),
                "review_summary": review.get("summary"),
                "human_ready": review.get("human_ready", False),
                "can_check": _check_task_check_trigger(task),
            }
    return {"error": "任务不存在"}


if __name__ == "__main__":
    # Index is now generated on-demand, no initialization needed
    import uvicorn
    port = int(os.environ.get("PM_KIT_PORT", "8770"))
    uvicorn.run(app, host="0.0.0.0", port=port)
