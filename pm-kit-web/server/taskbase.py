import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from fastapi import HTTPException
from pydantic import BaseModel

from .config import (
    ENTRY_TYPES,
    PRIORITY_MAP,
    STATUS_CANCEL_MARKERS,
    STATUS_DONE_MARKERS,
    STATUS_PROGRESS_MARKERS,
    TASK_STATUS_TRANSITIONS,
    _cache_get,
    _cache_invalidate,
    _cache_set,
    _get_projects,
    _invalidate_cache,
    _log_action,
    _read_yaml_file,
    normalize_task_status,
    read_text,
)


class TaskBaseMemoUpdatePayload(BaseModel):
    status: str = ""
    close_reason: str = ""
    linked_task_id: str = ""
    linked_adr_id: str = ""


@dataclass
class Entry:
    project: str
    date: str
    type: str
    content: str
    line_number: int
    status: str = "pending"
    priority: str = "P2"
    group_title: str = ""
    sequence: int = 0

    @property
    def id(self) -> str:
        return f"{self.project}_{self.date}_{self.sequence}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project": self.project,
            "date": self.date,
            "type": self.type,
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
            "group_title": self.group_title,
            "line_number": self.line_number,
            "sequence": self.sequence,
        }


def _task_base_dir(project_key: str) -> Optional[Path]:
    proj = _get_projects().get(project_key)
    if not proj:
        return None
    return proj["path"] / proj.get("task_base", "task-base")


def _task_base_memo_path(project_key: str, memo_id: str) -> Optional[Path]:
    proj = _get_projects().get(project_key)
    if not proj:
        return None
    path = proj["path"] / proj.get("task_base", "task-base") / "memos" / f"{memo_id}.yaml"
    if path.exists() and path.is_file():
        return path
    return None


def _load_task_base_task_details(project_key: str, proj: dict) -> list[dict]:
    items = []
    tasks_dir = proj["path"] / proj.get("task_base", "task-base") / "tasks"
    if not tasks_dir.exists():
        return items
    for f in sorted(tasks_dir.iterdir()):
        if f.is_file() and f.name.endswith(".yaml"):
            data = _read_yaml_file(f)
            if not data or not data.get("id"):
                continue
            normalized = normalize_task_status(data.get("status", ""))
            items.append({
                "id": data.get("id", ""),
                "title": data.get("title", ""),
                "requirement_doc": data.get("requirement_doc", ""),
                "parent_id": data.get("parent_id"),
                "status": data.get("status", ""),
                "normalized_status": normalized,
                "priority": data.get("priority", ""),
                "dependencies": data.get("dependencies") or [],
                "acceptance": data.get("acceptance", ""),
                "review": data.get("review") or {},
                "close_evidence": data.get("close_evidence"),
                "allowed_next_statuses": sorted(TASK_STATUS_TRANSITIONS.get(normalized, set())),
                "project": project_key,
                "project_name": proj["name"],
                "path": str(f.relative_to(proj["path"])),
            })
    return items


def _load_task_base_memo_details(project_key: str, proj: dict) -> list[dict]:
    items = []
    memos_dir = proj["path"] / proj.get("task_base", "task-base") / "memos"
    if not memos_dir.exists():
        return items
    for f in sorted(memos_dir.iterdir()):
        if f.is_file() and f.name.endswith(".yaml"):
            data = _read_yaml_file(f)
            if not data or not data.get("id"):
                continue
            items.append({
                "id": data.get("id", ""),
                "title": data.get("title") or data.get("summary") or str(data.get("content", ""))[:60],
                "content": data.get("content", ""),
                "status": data.get("status", ""),
                "priority": data.get("priority", ""),
                "created_at": data.get("created_at", ""),
                "closed_at": data.get("closed_at"),
                "close_reason": data.get("close_reason"),
                "source": data.get("source", ""),
                "linked_task_id": data.get("linked_task_id", ""),
                "linked_requirement_id": data.get("linked_requirement_id", ""),
                "linked_adr_id": data.get("linked_adr_id", ""),
                "project": project_key,
                "project_name": proj["name"],
                "path": str(f.relative_to(proj["path"])),
            })
    return items


def _load_task_base_tasks() -> list[dict]:
    items = []
    for key, proj in _get_projects().items():
        tasks_dir = proj["path"] / proj.get("task_base", "task-base") / "tasks"
        if not tasks_dir.exists():
            continue
        for f in sorted(tasks_dir.iterdir()):
            if f.is_file() and f.name.endswith(".yaml"):
                data = _read_yaml_file(f)
                if not data or not data.get("id"):
                    continue
                items.append({
                    "id": data.get("id", ""),
                    "title": data.get("title", ""),
                    "type": "工作项",
                    "status": data.get("status", ""),
                    "normalized_status": normalize_task_status(data.get("status", "")),
                    "priority": data.get("priority", ""),
                    "priority_reason": "",
                    "prerequisite": "",
                    "source": data.get("source", ""),
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
                    "allowed_next_statuses": sorted(TASK_STATUS_TRANSITIONS.get(normalize_task_status(data.get("status", "")), set())),
                    "fields": {},
                    "blocked_by": [],
                    "project": key,
                    "project_name": proj["name"],
                    "doc_id": "",
                    "doc_title": "task-base",
                    "path": str(f.relative_to(proj["path"])),
                })
    return items


def _all_task_objects() -> list[dict]:
    from .requirements import scan_requirements
    items = []
    tb_tasks = _load_task_base_tasks()
    tb_task_ids = {task["id"] for task in tb_tasks}

    for req in scan_requirements():
        for obj in req.get("exec_objects", []):
            obj_id = obj.get("id", "")
            if obj_id and obj_id in tb_task_ids:
                continue
            merged = dict(obj)
            merged.update({
                "project": req.get("project", ""),
                "project_name": req.get("project_name", ""),
                "doc_id": req.get("id", ""),
                "doc_title": req.get("title", ""),
                "path": req.get("path", ""),
            })
            items.append(merged)
    items.extend(tb_tasks)
    return items


def get_task_base_data(force: bool = False) -> dict:
    if not force:
        cached = _cache_get("task_base")
        if cached is not None:
            return cached
    projects_data = []
    summary = {"tasks": 0, "memos": 0, "open_memos": 0, "closed_memos": 0}
    for project_key, proj in _get_projects().items():
        tasks = _load_task_base_task_details(project_key, proj)
        memos = _load_task_base_memo_details(project_key, proj)
        project_data = {
            "project": project_key,
            "project_name": proj["name"],
            "project_path": str(proj["path"]),
            "tasks": tasks,
            "memos": memos,
            "summary": {
                "tasks": len(tasks),
                "memos": len(memos),
                "open_memos": sum(1 for memo in memos if memo.get("status") == "open"),
                "closed_memos": sum(1 for memo in memos if memo.get("status") == "closed"),
            },
        }
        for key in summary:
            summary[key] += project_data["summary"].get(key, 0)
        projects_data.append(project_data)
    data = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "summary": summary, "projects": projects_data}
    _cache_set("task_base", data)
    return data


def update_task_base_memo(project_key: str, memo_id: str, payload: TaskBaseMemoUpdatePayload) -> dict:
    path = _task_base_memo_path(project_key, memo_id)
    if not path:
        raise HTTPException(status_code=404, detail="Memo not found")
    data = _read_yaml_file(path)
    if not data:
        raise HTTPException(status_code=404, detail="Memo not found")
    new_status = (payload.status or data.get("status") or "").strip()
    if new_status not in {"open", "closed"}:
        raise HTTPException(status_code=400, detail="Memo 状态只允许 open 或 closed")
    data["status"] = new_status
    if payload.linked_task_id:
        data["linked_task_id"] = payload.linked_task_id.strip()
    if payload.linked_adr_id:
        data["linked_adr_id"] = payload.linked_adr_id.strip()
    if payload.close_reason:
        data["close_reason"] = payload.close_reason.strip()
    if new_status == "closed":
        data["closed_at"] = data.get("closed_at") or time.strftime("%Y-%m-%d")
        if not data.get("close_reason") and not data.get("linked_task_id") and not data.get("linked_adr_id"):
            raise HTTPException(status_code=409, detail="关闭 Memo 必须填写 close_reason、linked_task_id 或 linked_adr_id")
    else:
        data["closed_at"] = None
        if not payload.close_reason:
            data["close_reason"] = None
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    _invalidate_cache()
    proj = _get_projects()[project_key]
    updated = _read_yaml_file(path)
    updated["project"] = project_key
    updated["project_name"] = proj["name"]
    updated["path"] = str(path.relative_to(proj["path"]))
    return updated


def _extract_priority(text: str) -> str:
    for emoji, level in PRIORITY_MAP.items():
        if emoji in text:
            return level
    return "P2"


def _parse_entry_type(line: str) -> Optional[str]:
    stripped = line.lstrip("- ").strip()
    for t in ENTRY_TYPES:
        if stripped.startswith(f"{t}:") or stripped.startswith(f"~~{t}:"):
            return t
    return None


def _parse_status(line: str) -> str:
    stripped = line.strip()
    if "~~" in stripped:
        for marker in STATUS_DONE_MARKERS:
            if marker in stripped:
                return "done"
        for marker in STATUS_CANCEL_MARKERS:
            if marker in stripped:
                return "cancelled"
        return "done"
    for marker in STATUS_PROGRESS_MARKERS:
        if marker in stripped:
            return "in_progress"
    return "pending"


def _extract_content(line: str, entry_type: str) -> str:
    stripped = line.lstrip("- ").strip()
    is_strikethrough = stripped.startswith("~~")
    if is_strikethrough:
        stripped = stripped[2:]
    prefix = f"{entry_type}:"
    idx = stripped.find(prefix)
    if idx >= 0:
        content = stripped[idx + len(prefix):].strip()
    else:
        content = stripped
    if is_strikethrough and content.endswith("~~"):
        content = content[:-2].strip()
    for marker in STATUS_DONE_MARKERS | STATUS_CANCEL_MARKERS | STATUS_PROGRESS_MARKERS:
        content = content.replace(marker, "").strip()
    return content


def _format_entry_line(entry: Entry) -> str:
    content = entry.content
    if entry.status == "done":
        return f"- ~~{entry.type}: {content}~~ \u2705"
    elif entry.status == "cancelled":
        return f"- ~~{entry.type}: {content}~~ \u274c"
    elif entry.status == "in_progress":
        return f"- {entry.type}: {content} \U0001f504"
    else:
        return f"- {entry.type}: {content}"


def _find_line_by_content(lines: list[str], entry: Entry) -> Optional[int]:
    target_prefix = f"- {entry.type}:"
    target_strikethrough = f"- ~~{entry.type}:"
    content_prefix = entry.content[:30] if len(entry.content) >= 30 else entry.content
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        if not (stripped.startswith(target_prefix) or stripped.startswith(target_strikethrough)):
            continue
        if content_prefix in stripped:
            return i
    return None


def parse_memo_file(filepath: Path, project: str) -> list[Entry]:
    entries: list[Entry] = []
    if not filepath.exists():
        return entries
    lines = filepath.read_text(encoding="utf-8").splitlines()
    current_date = ""
    current_group_title = ""
    current_priority = "P2"
    entry_seq = 0
    for i, line in enumerate(lines):
        h3_match = re.match(r"^###\s+(\d{4}-\d{2}-\d{2})\s*(.*)", line)
        if h3_match:
            current_date = h3_match.group(1)
            current_group_title = h3_match.group(2).strip()
            current_priority = _extract_priority(current_group_title)
            entry_seq = 0
            continue
        if not line.startswith("- "):
            continue
        entry_type = _parse_entry_type(line)
        if not entry_type:
            continue
        if not current_date:
            continue
        status = _parse_status(line)
        content = _extract_content(line, entry_type)
        entries.append(Entry(
            project=project,
            date=current_date,
            type=entry_type,
            content=content,
            line_number=i + 1,
            status=status,
            priority=current_priority,
            group_title=current_group_title,
            sequence=entry_seq,
        ))
        entry_seq += 1
    return entries


def parse_all_memos() -> dict[str, list[Entry]]:
    all_entries: dict[str, list[Entry]] = {}
    for key, proj in _get_projects().items():
        memos_dir = proj["path"] / proj.get("task_base", "task-base") / "memos"
        entries = []
        if memos_dir.exists():
            for f in sorted(memos_dir.iterdir()):
                if f.is_file() and f.name.endswith(".yaml"):
                    data = _read_yaml_file(f)
                    if data:
                        status_map = {"open": "pending", "closed": "done", "cancelled": "cancelled"}
                        priority_map = {"P0": "P0", "P1": "P1", "P2": "P2", "P3": "P3"}
                        entries.append(Entry(
                            project=key,
                            date=data.get("created_at", ""),
                            type="FOUND",
                            content=data.get("content", ""),
                            line_number=0,
                            status=status_map.get(data.get("status"), "pending"),
                            priority=priority_map.get(data.get("priority"), "P2"),
                            group_title=data.get("id", ""),
                            sequence=len(entries),
                        ))
        all_entries[key] = entries
    return all_entries


def _get_all_memos(force: bool = False) -> dict[str, list[Entry]]:
    if not force:
        cached = _cache_get("memos")
        if cached is not None:
            return cached
    result = parse_all_memos()
    _cache_set("memos", result)
    return result


def update_memo_entry(project: str, entry_id: str, updates: dict) -> Optional[Entry]:
    projects = _get_projects()
    if project not in projects:
        return None
    filepath = projects[project]["path"] / projects[project]["docs"] / "03-开发备忘.md"
    if not filepath.exists():
        return None
    entries = parse_memo_file(filepath, project)
    target = None
    for e in entries:
        if e.id == entry_id:
            target = e
            break
    if not target:
        return None
    for k, v in updates.items():
        if k in ("status", "priority", "content", "type", "group_title"):
            setattr(target, k, v)
    lines = filepath.read_text(encoding="utf-8").splitlines()
    line_idx = target.line_number - 1
    if 0 <= line_idx < len(lines):
        old_line = lines[line_idx]
        old_type = _parse_entry_type(old_line)
        if old_type and target.content[:20] in old_line:
            lines[line_idx] = _format_entry_line(target)
            filepath.write_text("\n".join(lines), encoding="utf-8")
            _invalidate_cache()
            return target
    idx = _find_line_by_content(lines, target)
    if idx is not None:
        lines[idx] = _format_entry_line(target)
        filepath.write_text("\n".join(lines), encoding="utf-8")
        _invalidate_cache()
        return target
    return None


def add_memo_entry(project: str, entry_data: dict) -> Optional[Entry]:
    projects = _get_projects()
    if project not in projects:
        return None
    filepath = projects[project]["path"] / projects[project]["docs"] / "03-开发备忘.md"
    if not filepath.exists():
        return None
    entry = Entry(
        project=project,
        date=entry_data.get("date", time.strftime("%Y-%m-%d")),
        type=entry_data.get("type", "TODO"),
        content=entry_data.get("content", ""),
        line_number=0,
        status=entry_data.get("status", "pending"),
        priority=entry_data.get("priority", "P2"),
        group_title=entry_data.get("group_title", ""),
        sequence=0,
    )
    lines = filepath.read_text(encoding="utf-8").splitlines()
    group_header = f"### {entry.date}"
    group_end = len(lines)
    for i, line in enumerate(lines):
        if line.strip().startswith(group_header):
            j = i + 1
            while j < len(lines):
                if lines[j].strip().startswith("### ") and j > i:
                    group_end = j
                    break
                j += 1
            else:
                group_end = len(lines)
            insert_pos = group_end
            while insert_pos > i + 1 and lines[insert_pos - 1].strip() == "":
                insert_pos -= 1
            new_line = _format_entry_line(entry)
            lines.insert(insert_pos, new_line)
            filepath.write_text("\n".join(lines), encoding="utf-8")
            _invalidate_cache()
            return entry
    header_line = f"\n### {entry.date}"
    if entry.group_title:
        header_line += f" {entry.group_title}"
    new_entry_line = _format_entry_line(entry)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.append(header_line)
    lines.append(new_entry_line)
    filepath.write_text("\n".join(lines), encoding="utf-8")
    _invalidate_cache()
    return entry


def delete_memo_entry(project: str, entry_id: str) -> bool:
    projects = _get_projects()
    if project not in projects:
        return False
    filepath = projects[project]["path"] / projects[project]["docs"] / "03-开发备忘.md"
    if not filepath.exists():
        return False
    entries = parse_memo_file(filepath, project)
    target = None
    for e in entries:
        if e.id == entry_id:
            target = e
            break
    if not target:
        return False
    lines = filepath.read_text(encoding="utf-8").splitlines()
    line_idx = target.line_number - 1
    if 0 <= line_idx < len(lines):
        old_line = lines[line_idx]
        old_type = _parse_entry_type(old_line)
        if old_type and target.content[:20] in old_line:
            lines[line_idx] = f"- ~~{old_type}: {target.content}~~ \u274c 已归档"
            filepath.write_text("\n".join(lines), encoding="utf-8")
            _invalidate_cache()
            return True
    idx = _find_line_by_content(lines, target)
    if idx is not None:
        old_line = lines[idx]
        old_type = _parse_entry_type(old_line)
        if old_type:
            lines[idx] = f"- ~~{old_type}: {target.content}~~ \u274c 已归档"
        else:
            lines[idx] = f"- ~~{old_line.lstrip('- ').strip()}~~ \u274c 已归档"
        filepath.write_text("\n".join(lines), encoding="utf-8")
        _invalidate_cache()
        return True
    return False


def _generate_task_base_index() -> dict:
    """实时扫描 task-base 目录生成索引视图，不依赖持久化索引文件。

    返回结构：
    {
        "<project_key>": {
            "open_tasks": [...],
            "open_memos": [...],
            "closed_tasks": [...],
            "closed_memos": [...],
        }
    }
    """
    results = {}
    for proj_key, proj in _get_projects().items():
        task_base_path = proj["path"] / proj.get("task_base", "task-base")

        if not task_base_path.exists():
            results[proj_key] = {"status": "skipped", "reason": "task-base directory not found"}
            continue

        open_tasks = []
        open_memos = []
        closed_tasks = []
        closed_memos = []

        tasks_dir = task_base_path / "tasks"
        if tasks_dir.exists():
            for f in tasks_dir.iterdir():
                if f.is_file() and f.name.endswith(".yaml"):
                    data = _read_yaml_file(f)
                    if data and data.get("id"):
                        entry = {
                            "id": data.get("id", ""),
                            "title": data.get("title", ""),
                            "status": data.get("status", ""),
                            "priority": data.get("priority", ""),
                            "requirement_doc": data.get("requirement_doc", ""),
                        }
                        status = data.get("status", "")
                        if status in ("Closed", "Cancelled"):
                            closed_tasks.append(entry)
                        else:
                            open_tasks.append(entry)

        memos_dir = task_base_path / "memos"
        if memos_dir.exists():
            for f in memos_dir.iterdir():
                if f.is_file() and f.name.endswith(".yaml"):
                    data = _read_yaml_file(f)
                    if data and data.get("id"):
                        entry = {
                            "id": data.get("id", ""),
                            "content": data.get("content", "")[:100] + "..." if len(data.get("content", "")) > 100 else data.get("content", ""),
                            "priority": data.get("priority", ""),
                            "status": data.get("status", ""),
                        }
                        status = data.get("status", "")
                        if status == "closed":
                            closed_memos.append(entry)
                        else:
                            open_memos.append(entry)

        results[proj_key] = {
            "open_tasks": open_tasks,
            "open_memos": open_memos,
            "closed_tasks": closed_tasks,
            "closed_memos": closed_memos,
            "generated_at": datetime.now().isoformat(),
        }

    return results
