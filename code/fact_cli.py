#!/usr/bin/env python3
"""LDVH 事实模型 CLI 工具：create / transition / delete / list / show / search / stats / related / link-rule / deprecate / supersede。

对 LDVH 生产对象（workarea, taskplan, task, subtask, adr, pitfall, memo）
执行创建、状态流转、删除、列表查询、详情查看、搜索、统计等操作。
Change 使用 Git commit 作为事实源，不通过本 CLI 管理。
ADR 专属写入操作（link-rule / deprecate / supersede）必须携带 Human Gate 确认参数。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


# ── 对象元数据（硬编码，与 fact_validate.py 保持一致） ──────────────

# Change 使用 Git commit 作为事实源，不通过本 CLI 管理 YAML 文件
OBJECT_TYPES = {"workarea", "taskplan", "task", "subtask", "adr", "pitfall", "memo"}

LIST_SUMMARY_FIELDS = ("category", "priority", "importance", "repeatability")

ID_PATTERNS = {
    "workarea": re.compile(r"^workarea-\d{4}$"),
    "taskplan": re.compile(r"^taskplan-\d{4}$"),
    "task": re.compile(r"^task-\d{4}$"),
    "subtask": re.compile(r"^subtask-\d{4}$"),
    "adr": re.compile(r"^adr-\d{4}$"),
    "pitfall": re.compile(r"^pitfall-\d{4}$"),
    "memo": re.compile(r"^memo-\d{4}$"),
}

FILENAME_PATTERNS = {
    "workarea": re.compile(r"^workarea-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "taskplan": re.compile(r"^taskplan-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "task": re.compile(r"^task-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "subtask": re.compile(r"^subtask-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "adr": re.compile(r"^adr-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "pitfall": re.compile(r"^pitfall-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "memo": re.compile(r"^memo-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
}

VALID_STATUSES = {
    "workarea": {"active", "archived"},
    "taskplan": {"draft", "active", "review_needed", "closed"},
    "task": {"planned", "executing", "verifying", "review_needed", "closed"},
    "subtask": {"planned", "executing", "verifying", "review_needed", "closed"},
    "adr": {"proposed", "accepted", "rejected", "deprecated", "superseded"},
    "pitfall": {"draft", "active", "superseded", "archived"},
    "memo": {"pending", "resolved", "discarded"},
}

VALID_TRANSITIONS = {
    "workarea": {
        "active": {"archived"},
        "archived": {"active"},
    },
    "taskplan": {
        "draft": {"active"},
        "active": {"review_needed"},
        "review_needed": {"closed", "active"},
        "closed": set(),
    },
    "task": {
        "planned": {"executing"},
        "executing": {"verifying"},
        "verifying": {"review_needed", "executing"},
        "review_needed": {"closed", "executing"},
        "closed": set(),
    },
    "subtask": {
        "planned": {"executing"},
        "executing": {"verifying"},
        "verifying": {"review_needed", "executing"},
        "review_needed": {"closed", "executing"},
        "closed": set(),
    },
    "adr": {
        "proposed": {"accepted", "rejected"},
        "accepted": {"deprecated", "superseded"},
        "rejected": set(),
        "deprecated": set(),
        "superseded": set(),
    },
    "pitfall": {
        "draft": {"active", "archived"},
        "active": {"superseded", "archived"},
        "superseded": set(),
        "archived": set(),
    },
    "memo": {
        "pending": {"resolved", "discarded"},
        "resolved": {"discarded"},
        "discarded": set(),
    },
}

REQUIRED_FIELDS = {
    "workarea": ["id", "type", "title", "status", "created", "updated", "description", "source"],
    "taskplan": ["id", "type", "title", "status", "created", "updated", "workarea", "priority", "description", "success_criteria", "source", "tasks"],
    "task": ["id", "type", "title", "status", "created", "updated", "taskplan", "description", "source", "acceptance"],
    "subtask": ["id", "type", "title", "status", "created", "updated", "task", "description", "source", "acceptance"],
    "adr": ["id", "type", "title", "status", "created", "updated", "context", "decision", "consequences"],
    "pitfall": ["id", "type", "title", "status", "created", "updated", "symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"],
    "memo": ["id", "type", "title", "status", "created", "updated", "description", "source", "category", "priority"],
}

DEFAULT_STATUS = {
    "workarea": "active",
    "taskplan": "draft",
    "task": "planned",
    "subtask": "planned",
    "adr": "proposed",
    "pitfall": "draft",
    "memo": "pending",
}

DIRECTORY_MAP = {
    "workarea": "ldvh-base/workareas/",
    "taskplan": "ldvh-base/taskplans/",
    "task": "ldvh-base/tasks/",
    "subtask": "ldvh-base/subtasks/",
    "adr": "ldvh-base/adrs/",
    "pitfall": "ldvh-base/pitfalls/",
    "memo": "ldvh-base/memos/",
}

# 允许删除的状态集合
DELETABLE_STATUSES = {"draft", "pending", "proposed"}

# ADR 专属常量
ADR_TERMINAL_STATUSES = {"deprecated", "superseded", "rejected"}
ADR_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# ── 工具函数 ────────────────────────────────────────────────────────────

def error(msg: str) -> None:
    """输出错误信息到 stderr。"""
    print(f"错误: {msg}", file=sys.stderr)


def title_to_short(title: str) -> str:
    """将标题转换为文件名短标识：小写、空格替换短横线、去掉非字母数字短横线。"""
    result = title.lower()
    result = result.replace(" ", "-")
    result = re.sub(r"[^a-z0-9-]", "", result)
    # 去掉连续短横线
    result = re.sub(r"-+", "-", result)
    # 去掉首尾短横线
    result = result.strip("-")
    return result or "untitled"


def next_number(directory: Path, prefix: str) -> int:
    """扫描目录下现有文件，找最大编号 +1。"""
    if not directory.exists():
        return 1
    max_num = 0
    for f in directory.iterdir():
        if f.is_file() and f.suffix == ".yaml":
            m = re.match(rf"^{prefix}-(\d{{4}})-", f.name)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
    return max_num + 1


def load_yaml(path: Path) -> dict | None:
    """加载 YAML 文件，失败时输出错误并返回 None。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        error(f"YAML 解析失败: {exc}")
        return None
    except OSError as exc:
        error(f"读取文件失败: {exc}")
        return None
    if not isinstance(data, dict):
        error("YAML 顶层结构必须是映射对象")
        return None
    return data


def save_yaml(path: Path, data: dict) -> None:
    """将数据写入 YAML 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def find_task_by_id(tasks_dir: Path, task_id: str) -> tuple[Path | None, dict[str, Any] | None]:
    matches = sorted(tasks_dir.glob(f"{task_id}-*.yaml"))
    if not matches:
        return None, None
    task_path = matches[0]
    task_data = load_yaml(task_path)
    return task_path, task_data


def validate_task_blockers_closed(yaml_file: Path, data: dict[str, Any]) -> bool:
    blocked_by = data.get("blocked_by", [])
    if not blocked_by:
        return True
    if not isinstance(blocked_by, list):
        error("blocked_by 必须是 Task ID 列表")
        return False
    for blocker_id in blocked_by:
        if not isinstance(blocker_id, str) or not ID_PATTERNS["task"].match(blocker_id):
            error(f"blocked_by 中必须使用 task-{{NNNN}} 格式的 Task ID: {blocker_id}")
            return False
        if blocker_id == data.get("id"):
            error("blocked_by 不得引用当前 Task 自身")
            return False
        blocker_path, blocker_data = find_task_by_id(yaml_file.parent, blocker_id)
        if blocker_path is None or blocker_data is None:
            error(f"blocked_by 引用的 Task 不存在: {blocker_id}")
            return False
        if blocker_data.get("status") != "closed":
            error(f"前置 Task 未关闭，当前 Task 不得进入执行态: {blocker_id}")
            return False
    return True


def get_task_dependencies(tasks_dir: Path, task_id: str) -> dict[str, Any] | None:
    task_path, task_data = find_task_by_id(tasks_dir, task_id)
    if task_path is None or task_data is None:
        return None
    blocked_by = task_data.get("blocked_by", [])
    blocks = []
    if tasks_dir.exists():
        for yaml_path in sorted(tasks_dir.glob("task-*.yaml")):
            data = load_yaml(yaml_path)
            if data is None:
                continue
            if task_id in (data.get("blocked_by") or []):
                blocks.append({
                    "id": data.get("id", ""),
                    "status": data.get("status", ""),
                    "title": data.get("title", ""),
                    "path": str(yaml_path),
                })
    blockers = []
    if isinstance(blocked_by, list):
        for blocker_id in blocked_by:
            blocker_path, blocker_data = find_task_by_id(tasks_dir, blocker_id) if isinstance(blocker_id, str) else (None, None)
            blockers.append({
                "id": blocker_id,
                "status": blocker_data.get("status", "") if blocker_data else "",
                "title": blocker_data.get("title", "") if blocker_data else "",
                "path": str(blocker_path) if blocker_path else "",
                "closed": bool(blocker_data and blocker_data.get("status") == "closed"),
            })
    return {
        "id": task_data.get("id", task_id),
        "status": task_data.get("status", ""),
        "title": task_data.get("title", ""),
        "path": str(task_path),
        "blocked_by": blockers,
        "blocks": blocks,
        "ready_to_execute": all(item.get("closed") for item in blockers),
    }


def _json_safe(obj: Any) -> Any:
    """递归转换不可 JSON 序列化的对象为可序列化类型。"""
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


# ── ADR 专属工具函数 ────────────────────────────────────────────────────

def _today_iso() -> str:
    """返回当前 ISO 格式时间戳。"""
    return datetime.now().isoformat()


def _parse_list_values(values: list[str] | None) -> list[str]:
    """将 --flag 多值和逗号分隔值展平为列表。"""
    if not values:
        return []
    items = []
    for value in values:
        for item in str(value).split(","):
            item = item.strip()
            if item:
                items.append(item)
    return items


def _ensure_authorized(args: argparse.Namespace) -> None:
    """检查 Human Gate 确认参数，缺少时抛出 SystemExit。"""
    if not getattr(args, "human_gate_confirmed", False):
        error("写入被拒绝：缺少 --human-gate-confirmed。Tools 不生成授权，必须由 Human Gate 先确认。")
        raise SystemExit(1)
    if not getattr(args, "confirmed_by", None):
        error("写入被拒绝：缺少 --confirmed-by。")
        raise SystemExit(1)
    if not getattr(args, "confirmation_context", None):
        error("写入被拒绝：缺少 --confirmation-context。")
        raise SystemExit(1)


def _load_all_of_type(object_type: str, base_dir: Path) -> tuple[list[dict], list[tuple[str, str]]]:
    """加载指定类型的所有对象，返回 (对象列表, 解析错误列表)。"""
    directory = base_dir / DIRECTORY_MAP[object_type]
    if not directory.exists():
        return [], []
    objects = []
    parse_errors = []
    for filepath in sorted(directory.glob(f"{object_type}-*.yaml")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data is None:
                parse_errors.append((filepath.name, "YAML 内容为空"))
                continue
            data["_file"] = filepath.name
            data["_path"] = str(filepath)
            objects.append(data)
        except Exception as e:
            parse_errors.append((filepath.name, str(e)))
    return objects, parse_errors


def _find_adr_by_id(adrs: list[dict], adr_id: str) -> dict:
    """在 ADR 列表中按 id 查找，找不到时抛出 SystemExit。"""
    for adr in adrs:
        if adr.get("id") == adr_id:
            return adr
    error(f"未找到 ADR: {adr_id}")
    raise SystemExit(1)


def _adr_filepath(adr_id: str, slug: str, base_dir: Path) -> Path:
    """根据 ADR ID 和 slug 计算文件路径。"""
    if not ID_PATTERNS["adr"].match(adr_id):
        error(f"ADR ID 不合法: {adr_id}")
        raise SystemExit(1)
    if not ADR_SLUG_PATTERN.match(slug):
        error("slug 不合法：必须使用小写英文、数字和短横线，例如 use-yaml-for-adr。")
        raise SystemExit(1)
    return base_dir / DIRECTORY_MAP["adr"] / f"{adr_id}-{slug}.yaml"


def _update_adr_file(adr: dict, updates: dict, base_dir: Path) -> Path:
    """更新 ADR 文件，移除运行时字段后写入。"""
    path = Path(adr["_path"])
    data = {k: v for k, v in adr.items() if not k.startswith("_")}
    data.update(updates)
    save_yaml(path, data)
    return path





def _build_adr_data(adr_id: str, args: argparse.Namespace, now: str) -> dict:
    """构建 ADR 数据字典。"""
    gate_record = (
        f"[Human Gate 确认记录: 确认人={getattr(args, 'confirmed_by', 'N/A')}, "
        f"确认时间={now}, 确认上下文={getattr(args, 'confirmation_context', 'N/A')}]"
    )
    context_val = getattr(args, "context", "") or ""
    context_with_gate = f"{context_val}\n{gate_record}" if context_val else gate_record
    data = {
        "id": adr_id,
        "type": "adr",
        "title": args.title,
        "status": "proposed",
        "created": now,
        "updated": now,
        "date": getattr(args, "date", None) or now,
        "context": context_with_gate,
        "decision": args.decision,
        "consequences": args.consequences,
        "affects": _parse_list_values(getattr(args, "affects", None)),
        "related_objects": _parse_list_values(getattr(args, "related_objects", None)),
        "related_rules": _parse_list_values(getattr(args, "related_rules", None)),
    }
    if getattr(args, "alternatives", None):
        data["alternatives"] = args.alternatives
    return data


# ── create 命令 ─────────────────────────────────────────────────────────

def cmd_create(args: argparse.Namespace) -> int:
    """创建 LDVH 事实对象 YAML 文件。"""
    object_type = args.object_type
    title = args.title
    short_title = args.short_title or title_to_short(title)
    base_dir = Path(args.base_dir) if args.base_dir else Path(".")

    # 校验 object_type
    if object_type not in OBJECT_TYPES:
        error(f"不支持的对象类型: {object_type}，有效类型: {', '.join(sorted(OBJECT_TYPES))}")
        return 1

    # ADR 创建时强制 Human Gate
    if object_type == "adr":
        try:
            _ensure_authorized(args)
        except SystemExit:
            return 1

    # 计算目录和编号
    directory = base_dir / DIRECTORY_MAP[object_type]
    obj_num = next_number(directory, object_type)
    obj_id = f"{object_type}-{obj_num:04d}"
    filename = f"{obj_id}-{short_title}.yaml"
    filepath = directory / filename

    # 检查文件是否已存在
    if filepath.exists():
        error(f"文件已存在: {filepath}")
        return 1

    # 构建 YAML 数据
    now = datetime.now().isoformat()
    data = {}
    for field in REQUIRED_FIELDS[object_type]:
        if field == "id":
            data[field] = obj_id
        elif field == "type":
            data[field] = object_type
        elif field == "title":
            data[field] = title
        elif field == "status":
            data[field] = DEFAULT_STATUS[object_type]
        elif field in ("created", "updated"):
            data[field] = now
        else:
            # 其他必填字段默认为空字符串占位
            data[field] = ""
    if object_type == "workarea":
        data["related_docs"] = []
        data["related_adrs"] = []
        data["related_memos"] = []
        data["related_pitfalls"] = []
    if object_type == "taskplan":
        data["priority"] = "P2"
        data["tasks"] = []
        data["related_docs"] = []
        data["related_adrs"] = []
        data["related_memos"] = []
        data["related_pitfalls"] = []
    if object_type == "task":
        data["blocked_by"] = []
        data["deliverables"] = []
        data["verification"] = "## 验证计划\n\n## 验证命令\n"
        deliverables_val = getattr(args, "deliverables", None)
        if deliverables_val:
            data["deliverables"] = _parse_list_values(deliverables_val)
    if object_type == "subtask":
        data["blocked_by"] = []
        data["verification"] = "## 验证计划\n\n## 验证命令\n"
    if object_type == "memo":
        data["priority"] = "P3"

    # ADR 创建时回写 Human Gate 记录到 context
    if object_type == "adr":
        gate_record = (
            f"[Human Gate 确认记录: 确认人={getattr(args, 'confirmed_by', 'N/A')}, "
            f"确认时间={now}, 确认上下文={getattr(args, 'confirmation_context', 'N/A')}]"
        )
        data["context"] = gate_record

    # 写入文件
    save_yaml(filepath, data)
    print(str(filepath))


    return 0


# ── transition 命令 ─────────────────────────────────────────────────────

def cmd_transition(args: argparse.Namespace) -> int:
    """执行对象状态流转。"""
    yaml_file = Path(args.yaml_file)
    new_status = args.to
    reason = args.reason

    # 读取 YAML
    data = load_yaml(yaml_file)
    if data is None:
        return 1

    object_type = data.get("type")
    current_status = data.get("status")

    # 校验对象类型
    if object_type not in OBJECT_TYPES:
        error(f"不支持的对象类型: {object_type}")
        return 1

    # 状态流转属于既有事实源受控写入，必须先经过 Human Gate。
    try:
        _ensure_authorized(args)
    except SystemExit:
        return 1

    # 校验当前状态合法
    if current_status not in VALID_STATUSES[object_type]:
        error(f"当前状态不合法: {current_status}")
        return 1

    # 校验新状态合法
    if new_status not in VALID_STATUSES[object_type]:
        error(f"目标状态不合法: {new_status}，有效状态: {', '.join(sorted(VALID_STATUSES[object_type]))}")
        return 1

    # 校验流转合法性
    allowed = VALID_TRANSITIONS[object_type].get(current_status, set())
    if new_status not in allowed:
        error(f"不允许的流转: {current_status} → {new_status}，允许的目标状态: {', '.join(sorted(allowed)) or '无'}")
        return 1

    # ADR 终态不可重开
    if object_type == "adr" and current_status in ADR_TERMINAL_STATUSES:
        error(f"状态流转被拒绝：{current_status} 为终态，不得重开。")
        return 1

    # ADR accepted → superseded 必须提供 --superseded-by
    if object_type == "adr" and new_status == "superseded":
        if not getattr(args, "superseded_by", None):
            error("状态流转被拒绝：accepted → superseded 必须提供 --superseded-by。")
            return 1
        data["superseded_by"] = args.superseded_by

    # Task 前置任务强制校验（planned → executing）
    if object_type == "task" and current_status == "planned" and new_status == "executing":
        if not validate_task_blockers_closed(yaml_file, data):
            return 1

    # Task 关闭条件校验（review_needed → closed）
    if object_type == "task" and current_status == "review_needed" and new_status == "closed":
        # 校验 acceptance 全部 - [x]
        acceptance = data.get("acceptance", "")
        if isinstance(acceptance, str):
            unchecked = re.findall(r"- \[ \]", acceptance)
            if unchecked:
                error(f"acceptance 存在未完成项（{len(unchecked)} 项未勾选），无法关闭")
                return 1
        # 校验 verification 已填写
        verification = data.get("verification")
        if not verification or (isinstance(verification, str) and not verification.strip()):
            error("verification 未填写，无法关闭 Task")
            return 1
        # 校验 closure_evidence 已填写
        closure_evidence = data.get("closure_evidence")
        if not closure_evidence or (isinstance(closure_evidence, str) and not closure_evidence.strip()):
            error("closure_evidence 未填写，无法关闭 Task")
            return 1

    # TaskPlan 待关闭审查条件校验（active → review_needed）
    if object_type == "taskplan" and current_status == "active" and new_status == "review_needed":
        completion_evidence = data.get("completion_evidence")
        if not completion_evidence or (isinstance(completion_evidence, str) and not completion_evidence.strip()):
            error("completion_evidence 未填写，无法将 TaskPlan 标记为 review_needed")
            return 1
        if not data.get("review_requested_at"):
            data["review_requested_at"] = datetime.now().isoformat()

    # TaskPlan 关闭条件校验（review_needed → closed）
    if object_type == "taskplan" and current_status == "review_needed" and new_status == "closed":
        for field in ("review_requested_at", "completion_evidence"):
            value = data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                error(f"{field} 未填写，无法关闭 TaskPlan")
                return 1

    if object_type == "workarea" and new_status == "archived":
        archive_reason = data.get("archive_reason")
        if not archive_reason or (isinstance(archive_reason, str) and not archive_reason.strip()):
            error("archive_reason 未填写，无法归档 WorkArea")
            return 1

    if object_type == "subtask" and current_status == "review_needed" and new_status == "closed":
        for field in ("verification", "closure_evidence"):
            value = data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                error(f"{field} 未填写，无法关闭 SubTask")
                return 1

    # Memo 分流条件校验（pending → resolved）
    if object_type == "memo" and current_status == "pending" and new_status == "resolved":
        resolved_to = data.get("resolved_to")
        if not resolved_to or (isinstance(resolved_to, str) and not resolved_to.strip()):
            error("resolved_to 未填写，无法将 Memo 标记为 resolved")
            return 1
        if not data.get("resolved_at"):
            data["resolved_at"] = datetime.now().isoformat()

    if object_type == "memo" and new_status == "discarded":
        discard_reason = data.get("discard_reason")
        if not discard_reason or (isinstance(discard_reason, str) and not discard_reason.strip()):
            error("discard_reason 未填写，无法废弃 Memo")
            return 1

    # 执行流转
    data["status"] = new_status
    data["updated"] = datetime.now().isoformat()
    if object_type == "task" and new_status == "closed":
        data["closed_at"] = datetime.now().isoformat()
    if object_type == "taskplan" and new_status == "closed":
        data["closed_at"] = datetime.now().isoformat()
    if object_type == "subtask" and new_status == "closed":
        data["closed_at"] = datetime.now().isoformat()

    # ADR 流转时回写 Human Gate 记录到 context
    if object_type == "adr":
        gate_record = (
            f"[Human Gate 确认记录: 确认人={getattr(args, 'confirmed_by', 'N/A')}, "
            f"确认时间={_today_iso()}, 确认上下文={getattr(args, 'confirmation_context', 'N/A')}]"
        )
        existing_context = data.get("context", "")
        data["context"] = f"{existing_context}\n{gate_record}" if existing_context else gate_record

    # 退回流转记录 reason
    backward_pairs = {
        ("review_needed", "active"),
        ("verifying", "executing"),
        ("review_needed", "executing"),
    }
    if (current_status, new_status) in backward_pairs:
        if not reason:
            error(f"退回流转 {current_status} → {new_status} 需要提供 --reason")
            return 1
        if "transition_reasons" not in data:
            data["transition_reasons"] = []
        data["transition_reasons"].append({
            "from": current_status,
            "to": new_status,
            "reason": reason,
            "date": datetime.now().isoformat(),
        })

    # 写回文件
    save_yaml(yaml_file, data)
    print(f"{current_status} → {new_status}")


    return 0


# ── delete 命令 ─────────────────────────────────────────────────────────

def cmd_delete(args: argparse.Namespace) -> int:
    """删除事实对象 YAML 文件。"""
    yaml_file = Path(args.yaml_file)

    # 读取 YAML
    data = load_yaml(yaml_file)
    if data is None:
        return 1

    try:
        _ensure_authorized(args)
    except SystemExit:
        return 1

    current_status = data.get("status")

    # 校验状态允许删除
    if current_status not in DELETABLE_STATUSES:
        error(f"状态 {current_status} 不允许删除，仅 {', '.join(sorted(DELETABLE_STATUSES))} 状态可删除")
        return 1

    # 删除文件
    try:
        yaml_file.unlink()
    except OSError as exc:
        error(f"删除文件失败: {exc}")
        return 1

    print(str(yaml_file))
    return 0


# ── list 命令 ──────────────────────────────────────────────────────────

def cmd_list(args: argparse.Namespace) -> int:
    """列出指定类型的事实对象摘要。"""
    object_type = args.object_type
    status_filter = args.status
    base_dir = Path(args.base_dir) if args.base_dir else Path(".")
    fmt = args.format

    if object_type not in OBJECT_TYPES:
        error(f"不支持的对象类型: {object_type}，有效类型: {', '.join(sorted(OBJECT_TYPES))}")
        return 1

    directory = base_dir / DIRECTORY_MAP[object_type]
    items: list[dict[str, Any]] = []
    issues: list[dict[str, str | None]] = []

    if not directory.exists():
        pass
    else:
        for yaml_path in sorted(directory.glob("*.yaml")):
            data = load_yaml(yaml_path)
            if data is None:
                issues.append({
                    "level": "warning",
                    "code": "YAML_LOAD_FAILED",
                    "message": f"无法加载: {yaml_path}",
                    "path": str(yaml_path),
                    "field": None,
                    "suggestion": None,
                })
                continue
            obj_status = data.get("status", "")
            if status_filter and obj_status != status_filter:
                continue
            item_data: dict[str, Any] = {
                "id": data.get("id", ""),
                "type": data.get("type", object_type),
                "status": obj_status,
                "title": data.get("title", ""),
                "path": str(yaml_path),
                "updated": data.get("updated", ""),
            }
            if "title_en" in data:
                item_data["title_en"] = data["title_en"]
            if "title_zh" in data:
                item_data["title_zh"] = data["title_zh"]
            for field in LIST_SUMMARY_FIELDS:
                if field in data:
                    item_data[field] = data[field]
            items.append(item_data)

    if fmt == "json":
        result: dict[str, Any] = {
            "ok": True,
            "command": "fact_cli",
            "action": "list",
            "target": object_type,
            "summary": {
                "count": len(items),
                "errors": 0,
                "warnings": len(issues),
            },
            "issues": issues,
            "data": {"items": items},
        }
        print(json.dumps(_json_safe(result), ensure_ascii=False, indent=2))
    else:
        for item in items:
            print(f"{item['id']}\t{item['status']}\t{item['title']}")
        if not items:
            print(f"未找到 {object_type} 对象")

    return 0


# ── deps 命令 ──────────────────────────────────────────────────────────

def cmd_deps(args: argparse.Namespace) -> int:
    """展示 Task 的前置依赖与被阻塞关系。"""
    target = args.target
    base_dir = Path(args.base_dir) if args.base_dir else Path(".")
    fmt = args.format
    tasks_dir = base_dir / DIRECTORY_MAP["task"]

    target_path = Path(target)
    if target_path.is_file():
        data = load_yaml(target_path)
        if data is None:
            return 1
        if data.get("type") != "task":
            error(f"deps 仅支持 task 对象: {target}")
            return 1
        task_id = data.get("id")
        if not isinstance(task_id, str) or not ID_PATTERNS["task"].match(task_id):
            error(f"Task ID 不合法: {task_id}")
            return 1
        tasks_dir = target_path.parent
    else:
        task_id = target
        if not ID_PATTERNS["task"].match(task_id):
            error(f"Task ID 必须使用 task-{{NNNN}} 格式: {task_id}")
            return 1

    deps = get_task_dependencies(tasks_dir, task_id)
    if deps is None:
        error(f"找不到 Task: {task_id}")
        return 1

    if fmt == "json":
        result = {
            "ok": True,
            "command": "fact_cli",
            "action": "deps",
            "target": task_id,
            "summary": {
                "id": deps.get("id", task_id),
                "status": deps.get("status", ""),
                "blocked_by_count": len(deps.get("blocked_by", [])),
                "blocks_count": len(deps.get("blocks", [])),
                "ready_to_execute": deps.get("ready_to_execute", False),
            },
            "issues": [],
            "data": deps,
        }
        print(json.dumps(_json_safe(result), ensure_ascii=False, indent=2))
    else:
        print(f"{deps.get('id', task_id)}\t{deps.get('status', '')}\t{deps.get('title', '')}")
        print(f"path: {deps.get('path', '')}")
        print(f"ready_to_execute: {deps.get('ready_to_execute', False)}")
        print("blocked_by:")
        blockers = deps.get("blocked_by", [])
        if blockers:
            for item in blockers:
                closed_mark = "closed" if item.get("closed") else "not_closed"
                print(f"  - {item.get('id', '')}\t{item.get('status', '')}\t{closed_mark}\t{item.get('title', '')}")
        else:
            print("  (none)")
        print("blocks:")
        blocked = deps.get("blocks", [])
        if blocked:
            for item in blocked:
                print(f"  - {item.get('id', '')}\t{item.get('status', '')}\t{item.get('title', '')}")
        else:
            print("  (none)")

    return 0


# ── show 命令 ──────────────────────────────────────────────────────────

def cmd_show(args: argparse.Namespace) -> int:
    """展示单个事实对象详情。"""
    target = args.target
    base_dir = Path(args.base_dir) if args.base_dir else Path(".")
    fmt = args.format

    target_path = Path(target)
    if target_path.is_file():
        yaml_file = target_path
    else:
        matched = False
        for obj_type, pattern in ID_PATTERNS.items():
            if pattern.match(target):
                directory = base_dir / DIRECTORY_MAP[obj_type]
                if directory.exists():
                    for yaml_path in sorted(directory.glob(f"{target}-*.yaml")):
                        yaml_file = yaml_path
                        matched = True
                        break
                break
        if not matched:
            error(f"找不到对象: {target}")
            return 1

    data = load_yaml(yaml_file)
    if data is None:
        return 1

    if fmt == "json":
        result = {
            "ok": True,
            "command": "fact_cli",
            "action": "show",
            "target": str(yaml_file),
            "summary": {
                "id": data.get("id", ""),
                "type": data.get("type", ""),
                "status": data.get("status", ""),
            },
            "issues": [],
            "data": data,
        }
        print(json.dumps(_json_safe(result), ensure_ascii=False, indent=2))
    else:
        print(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False).rstrip())

    return 0


# ── search 命令 ────────────────────────────────────────────────────────

def cmd_search(args: argparse.Namespace) -> int:
    """按关键词搜索事实对象。"""
    keyword = args.keyword
    object_type = getattr(args, "type", None)
    base_dir = Path(args.base_dir) if args.base_dir else Path(".")
    keyword_lower = keyword.lower()

    types_to_search = [object_type] if object_type else sorted(OBJECT_TYPES)
    matched: list[dict[str, Any]] = []

    for otype in types_to_search:
        if otype not in OBJECT_TYPES:
            error(f"不支持的对象类型: {otype}")
            return 1
        directory = base_dir / DIRECTORY_MAP[otype]
        if not directory.exists():
            continue
        for yaml_path in sorted(directory.glob(f"{otype}-*.yaml")):
            data = load_yaml(yaml_path)
            if data is None:
                continue
            searchable = " ".join([
                str(data.get("title", "")),
                str(data.get("context", "")),
                str(data.get("decision", "")),
                str(data.get("consequences", "")),
                str(data.get("description", "")),
                str(data.get("id", "")),
            ]).lower()
            if keyword_lower in searchable:
                matched.append({
                    "id": data.get("id", ""),
                    "type": data.get("type", otype),
                    "status": data.get("status", ""),
                    "title": data.get("title", ""),
                    "path": str(yaml_path),
                })

    if not matched:
        print(f"未找到包含 '{keyword}' 的对象。")
        return 0

    print(f"找到 {len(matched)} 个匹配的对象：\n")
    print(f"{'ID':<16} {'类型':<10} {'状态':<14} {'标题':<40}")
    print("-" * 85)
    for item in matched:
        title = item["title"]
        if len(title) > 38:
            title = title[:36] + ".."
        print(f"{item['id']:<16} {item['type']:<10} {item['status']:<14} {title:<40}")
    return 0


# ── stats 命令 ─────────────────────────────────────────────────────────

def cmd_stats(args: argparse.Namespace) -> int:
    """统计对象状态分布。"""
    object_type = getattr(args, "type", None)
    base_dir = Path(args.base_dir) if args.base_dir else Path(".")

    types_to_stat = [object_type] if object_type else sorted(OBJECT_TYPES)

    for otype in types_to_stat:
        if otype not in OBJECT_TYPES:
            error(f"不支持的对象类型: {otype}")
            return 1
        directory = base_dir / DIRECTORY_MAP[otype]
        status_counts: dict[str, int] = {}
        total = 0
        if directory.exists():
            for yaml_path in sorted(directory.glob(f"{otype}-*.yaml")):
                data = load_yaml(yaml_path)
                if data is None:
                    continue
                s = data.get("status", "unknown")
                status_counts[s] = status_counts.get(s, 0) + 1
                total += 1

        print(f"{otype} 总数: {total}")
        for status in sorted(VALID_STATUSES.get(otype, [])):
            count = status_counts.get(status, 0)
            if count > 0:
                print(f"  {status}: {count}")
        other = sum(v for k, v in status_counts.items() if k not in VALID_STATUSES.get(otype, set()))
        if other:
            print(f"  其他: {other}")
        print()

    return 0


# ── related 命令 ───────────────────────────────────────────────────────

def cmd_related(args: argparse.Namespace) -> int:
    """查询与指定 specs 关联的 ADR。"""
    spec_path = args.spec_path
    base_dir = Path(args.base_dir) if args.base_dir else Path(".")

    adrs, _ = _load_all_of_type("adr", base_dir)
    matched = []
    for adr in adrs:
        affects = adr.get("affects", [])
        related_rules = adr.get("related_rules", [])
        all_refs = [str(r) for r in (affects or []) + (related_rules or [])]
        if any(spec_path in ref for ref in all_refs):
            matched.append(adr)

    if not matched:
        print(f"未找到与 '{spec_path}' 关联的 ADR。")
        return 0

    print(f"与 '{spec_path}' 关联的 ADR 共 {len(matched)} 个：\n")
    print(f"{'ID':<12} {'状态':<14} {'标题':<40}")
    print("-" * 70)
    for adr in matched:
        adr_id = adr.get("id", "N/A")
        status = adr.get("status", "N/A")
        title = adr.get("title", "N/A")
        if len(str(title)) > 38:
            title = str(title)[:36] + ".."
        print(f"{adr_id:<12} {status:<14} {title:<40}")
    return 0


# ── link-rule 命令 ─────────────────────────────────────────────────────

def cmd_link_rule(args: argparse.Namespace) -> int:
    """更新 ADR 的 related_rules 字段。"""
    try:
        _ensure_authorized(args)
    except SystemExit:
        return 1

    base_dir = Path(args.base_dir) if args.base_dir else Path(".")
    adrs, _ = _load_all_of_type("adr", base_dir)
    adr = _find_adr_by_id(adrs, args.adr_id)

    rules = adr.get("related_rules") or []
    if not isinstance(rules, list):
        error("related_rules 当前不是列表，拒绝写入。")
        return 1

    changed = False
    for rule in _parse_list_values(args.rule):
        if rule not in rules:
            rules.append(rule)
            changed = True

    if not changed:
        print("related_rules 无变化。")
        return 0

    path = _update_adr_file(adr, {"related_rules": rules, "updated": _today_iso()}, base_dir)
    print(f"已更新 related_rules: {args.adr_id}")
    return 0


# ── deprecate 命令 ─────────────────────────────────────────────────────

def cmd_deprecate(args: argparse.Namespace) -> int:
    """废弃 ADR（accepted → deprecated + 废弃原因回写）。"""
    try:
        _ensure_authorized(args)
    except SystemExit:
        return 1

    base_dir = Path(args.base_dir) if args.base_dir else Path(".")
    adrs, _ = _load_all_of_type("adr", base_dir)
    adr = _find_adr_by_id(adrs, args.adr_id)

    current = adr.get("status")
    allowed = VALID_TRANSITIONS["adr"].get(current, set())
    if "deprecated" not in allowed:
        error(f"废弃被拒绝：{current} → deprecated 非法。")
        return 1

    context = str(adr.get("context", ""))
    consequences = str(adr.get("consequences", ""))
    addition = f"废弃原因：{args.reason}"
    reason_field = getattr(args, "reason_field", "consequences")
    updates: dict[str, Any] = {"status": "deprecated", "updated": _today_iso()}
    if reason_field == "context":
        updates["context"] = f"{context}\n\n{addition}" if context else addition
    else:
        updates["consequences"] = f"{consequences}\n\n{addition}" if consequences else addition

    path = _update_adr_file(adr, updates, base_dir)
    print(f"已废弃 ADR: {args.adr_id}")
    return 0


# ── supersede 命令 ─────────────────────────────────────────────────────

def cmd_supersede(args: argparse.Namespace) -> int:
    """推翻 ADR（创建新 ADR + 原 ADR 标记 superseded）。"""
    try:
        _ensure_authorized(args)
    except SystemExit:
        return 1

    base_dir = Path(args.base_dir) if args.base_dir else Path(".")
    adrs, _ = _load_all_of_type("adr", base_dir)
    old_adr = _find_adr_by_id(adrs, args.old_adr_id)

    old_status = old_adr.get("status")
    allowed = VALID_TRANSITIONS["adr"].get(old_status, set())
    if "superseded" not in allowed:
        error(f"推翻被拒绝：{old_status} → superseded 非法。")
        return 1

    # 计算新 ADR ID
    adr_dir = base_dir / DIRECTORY_MAP["adr"]
    new_num = next_number(adr_dir, "adr")
    new_id = f"adr-{new_num:04d}"
    now = _today_iso()

    # 构建新 ADR 数据
    new_adr = _build_adr_data(new_id, args, now)
    related_objects = new_adr.get("related_objects", [])
    if args.old_adr_id not in related_objects:
        related_objects.append(args.old_adr_id)
    new_adr["related_objects"] = related_objects

    new_path = _adr_filepath(new_id, args.slug, base_dir)
    if new_path.exists():
        error(f"写入被拒绝：目标文件已存在 {new_path}")
        return 1

    # 写入新 ADR
    save_yaml(new_path, new_adr)

    # 更新原 ADR
    old_path = _update_adr_file(
        old_adr,
        {"status": "superseded", "superseded_by": new_id, "updated": now},
        base_dir,
    )

    print(f"已创建替代 ADR: {new_path}")
    print(f"已更新原 ADR: {args.old_adr_id} → superseded_by {new_id}")
    return 0


# ── update 命令 ─────────────────────────────────────────────────────────

def cmd_update(args: argparse.Namespace) -> int:
    """更新事实对象的指定字段。"""
    target = args.target
    base_dir = Path(args.base_dir) if args.base_dir else Path(".")

    # 定位文件
    target_path = Path(target)
    if target_path.is_file():
        yaml_file = target_path
    else:
        matched = False
        for obj_type, pattern in ID_PATTERNS.items():
            if pattern.match(target):
                directory = base_dir / DIRECTORY_MAP[obj_type]
                if directory.exists():
                    for yp in sorted(directory.glob(f"{target}-*.yaml")):
                        yaml_file = yp
                        matched = True
                        break
                break
        if not matched:
            error(f"找不到对象: {target}")
            return 1

    data = load_yaml(yaml_file)
    if data is None:
        return 1

    object_type = data.get("type")
    if object_type not in OBJECT_TYPES:
        error(f"不支持的对象类型: {object_type}")
        return 1

    try:
        _ensure_authorized(args)
    except SystemExit:
        return 1

    # 解析 --set 参数（key=value 格式）
    updates = {}
    for item in (args.set or []):
        if "=" not in item:
            error(f"--set 格式错误，应为 key=value: {item}")
            return 1
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        # 处理字符串转义：\n → 换行, \\ → 反斜杠
        value = value.replace("\\n", "\n").replace("\\\\", "\\")
        # 列表类型字段：逗号分隔
        if key in ("related_workareas", "related_taskplans", "related_tasks", "related_adrs",
                    "related_memos", "related_pitfalls", "related_docs",
                    "affected_docs", "deliverables", "tasks",
                    "blocked_by", "affects", "related_objects", "related_rules"):
            updates[key] = [v.strip() for v in value.split(",") if v.strip()] if value else []
        else:
            updates[key] = value

    if not updates:
        error("未指定要更新的字段，请使用 --set key=value")
        return 1

    # 禁止修改 id 和 type
    if "id" in updates or "type" in updates:
        error("不允许修改 id 和 type 字段")
        return 1

    # 应用更新
    data.update(updates)
    data["updated"] = datetime.now().isoformat()

    # 写回文件
    save_yaml(yaml_file, data)
    print(f"已更新 {data.get('id', target)}: {', '.join(f'{k}={v}' for k, v in updates.items())}")
    return 0


# ── CLI 入口 ────────────────────────────────────────────────────────────

def _add_authorization_args(parser: argparse.ArgumentParser) -> None:
    """为写入类子命令添加 Human Gate 确认参数。"""
    parser.add_argument("--human-gate-confirmed", action="store_true", help="Human Gate 已确认")
    parser.add_argument("--confirmed-by", default=None, help="确认人")
    parser.add_argument("--confirmation-context", default=None, help="确认上下文")


def _add_adr_content_args(parser: argparse.ArgumentParser) -> None:
    """为 ADR 创建类子命令添加内容参数。"""
    parser.add_argument("--slug", required=True, help="ADR 文件名 slug")
    parser.add_argument("--title", required=True, help="ADR 标题")
    parser.add_argument("--context", default="", help="ADR 背景")
    parser.add_argument("--decision", required=True, help="ADR 决策")
    parser.add_argument("--consequences", required=True, help="ADR 影响")
    parser.add_argument("--date", default=None, help="决策日期")
    parser.add_argument("--alternatives", default=None, help="替代方案")
    parser.add_argument("--affects", action="append", default=None, help="影响文件（可多次指定）")
    parser.add_argument("--related-objects", action="append", default=None, help="关联对象（可多次指定）")
    parser.add_argument("--related-rules", action="append", default=None, help="关联规范（可多次指定）")


def build_parser() -> argparse.ArgumentParser:
    """构建 argparse 解析器。"""
    parser = argparse.ArgumentParser(
        description="LDVH 事实模型 CLI：创建、状态流转、删除、列表查询、详情查看、搜索、统计"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create 子命令
    create_parser = subparsers.add_parser("create", help="创建事实对象")
    create_parser.add_argument("object_type", choices=sorted(OBJECT_TYPES), help="对象类型")
    create_parser.add_argument("--title", required=True, help="对象标题")
    create_parser.add_argument("--short-title", default=None, help="文件名短标识（默认从标题自动生成）")
    create_parser.add_argument("--deliverables", action="append", default=None, help="Task 产出物路径（可多次指定，支持逗号分隔）")
    create_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    _add_authorization_args(create_parser)

    # transition 子命令
    transition_parser = subparsers.add_parser("transition", help="执行状态流转")
    transition_parser.add_argument("yaml_file", help="YAML 文件路径")
    transition_parser.add_argument("--to", required=True, dest="to", help="目标状态")
    transition_parser.add_argument("--reason", default=None, help="退回流转原因")
    transition_parser.add_argument("--superseded-by", default=None, help="被替代的新 ADR ID（ADR superseded 时必填）")
    transition_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    _add_authorization_args(transition_parser)

    # delete 子命令
    delete_parser = subparsers.add_parser("delete", help="删除事实对象")
    delete_parser.add_argument("yaml_file", help="YAML 文件路径")
    _add_authorization_args(delete_parser)

    # list 子命令
    list_parser = subparsers.add_parser("list", help="列出事实对象摘要")
    list_parser.add_argument("object_type", choices=sorted(OBJECT_TYPES), help="对象类型")
    list_parser.add_argument("--status", default=None, help="按状态过滤")
    list_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    list_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")

    # deps 子命令
    deps_parser = subparsers.add_parser("deps", help="查看 Task 依赖关系")
    deps_parser.add_argument("target", help="Task ID（如 task-0001）或 Task YAML 文件路径")
    deps_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    deps_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")

    # show 子命令
    show_parser = subparsers.add_parser("show", help="查看事实对象详情")
    show_parser.add_argument("target", help="YAML 文件路径或对象 ID（如 task-0001）")
    show_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    show_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")

    # search 子命令
    search_parser = subparsers.add_parser("search", help="按关键词搜索事实对象")
    search_parser.add_argument("keyword", help="搜索关键词")
    search_parser.add_argument("--type", default=None, dest="type", help="限定对象类型（默认搜索所有类型）")
    search_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")

    # stats 子命令
    stats_parser = subparsers.add_parser("stats", help="统计对象状态分布")
    stats_parser.add_argument("--type", default=None, dest="type", help="限定对象类型（默认统计所有类型）")
    stats_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")

    # related 子命令
    related_parser = subparsers.add_parser("related", help="查询与指定 specs 关联的 ADR")
    related_parser.add_argument("spec_path", help="specs 文件路径（如 specs/21-ADR-决策.md）")
    related_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")

    # link-rule 子命令
    link_rule_parser = subparsers.add_parser("link-rule", help="更新 ADR 关联规范")
    link_rule_parser.add_argument("adr_id", help="ADR ID（如 adr-0001）")
    link_rule_parser.add_argument("--rule", action="append", required=True, help="规范路径（可多次指定）")
    link_rule_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    _add_authorization_args(link_rule_parser)

    # deprecate 子命令
    deprecate_parser = subparsers.add_parser("deprecate", help="废弃 ADR")
    deprecate_parser.add_argument("adr_id", help="ADR ID（如 adr-0001）")
    deprecate_parser.add_argument("--reason", required=True, help="废弃原因")
    deprecate_parser.add_argument("--reason-field", choices=["context", "consequences"], default="consequences", help="废弃原因写入字段（默认 consequences）")
    deprecate_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    _add_authorization_args(deprecate_parser)

    # supersede 子命令
    supersede_parser = subparsers.add_parser("supersede", help="推翻 ADR（创建新 ADR + 原 ADR 标记 superseded）")
    supersede_parser.add_argument("--old-adr-id", required=True, help="被推翻的 ADR ID")
    _add_adr_content_args(supersede_parser)
    supersede_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    _add_authorization_args(supersede_parser)

    # update 子命令
    update_parser = subparsers.add_parser("update", help="更新事实对象的指定字段")
    update_parser.add_argument("target", help="对象 ID（如 taskplan-0002）或 YAML 文件路径")
    update_parser.add_argument("--set", action="append", default=None, help="设置字段值（key=value，可多次指定，列表字段用逗号分隔）")
    update_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    _add_authorization_args(update_parser)

    return parser


def main() -> int:
    """CLI 主入口。"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create":
        return cmd_create(args)
    elif args.command == "transition":
        return cmd_transition(args)
    elif args.command == "delete":
        return cmd_delete(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "deps":
        return cmd_deps(args)
    elif args.command == "show":
        return cmd_show(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "stats":
        return cmd_stats(args)
    elif args.command == "related":
        return cmd_related(args)
    elif args.command == "link-rule":
        return cmd_link_rule(args)
    elif args.command == "deprecate":
        return cmd_deprecate(args)
    elif args.command == "supersede":
        return cmd_supersede(args)
    elif args.command == "update":
        return cmd_update(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
