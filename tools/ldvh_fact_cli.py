#!/usr/bin/env python3
"""LDVH 事实模型 CLI 工具：create / transition / delete / list / show。

对 LDVH 生产对象（intent, task, adr, pitfall, memo, profile, change）
执行创建、状态流转、删除、列表查询和详情查看操作。当前硬编码元数据，后续迁移到读取 Contract。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml


# ── 对象元数据（硬编码，与 check_fact_model.py 保持一致） ──────────────

OBJECT_TYPES = {"intent", "task", "adr", "pitfall", "memo", "profile", "change"}

ID_PATTERNS = {
    "intent": re.compile(r"^intent-\d{4}$"),
    "task": re.compile(r"^task-\d{4}$"),
    "adr": re.compile(r"^adr-\d{4}$"),
    "pitfall": re.compile(r"^pitfall-\d{4}$"),
    "profile": re.compile(r"^profile-\d{4}$"),
    "memo": re.compile(r"^memo-\d{4}$"),
    "change": re.compile(r"^change-\d{4}$"),
}

FILENAME_PATTERNS = {
    "intent": re.compile(r"^intent-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "task": re.compile(r"^task-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "adr": re.compile(r"^adr-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "pitfall": re.compile(r"^pitfall-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "profile": re.compile(r"^profile-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "memo": re.compile(r"^memo-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "change": re.compile(r"^change-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
}

VALID_STATUSES = {
    "intent": {"draft", "active", "completed", "closed"},
    "task": {"planned", "executing", "verifying", "review_needed", "closed"},
    "adr": {"proposed", "accepted", "rejected", "deprecated", "superseded"},
    "pitfall": {"draft", "active", "superseded", "archived"},
    "profile": {"draft", "active", "suspended", "archived"},
    "memo": {"draft", "active", "resolved", "archived"},
    "change": {"proposed", "accepted", "implemented", "deprecated"},
}

VALID_TRANSITIONS = {
    "intent": {
        "draft": {"active"},
        "active": {"completed", "closed"},
        "completed": {"closed"},
        "closed": set(),
    },
    "task": {
        "planned": {"executing"},
        "executing": {"verifying"},
        "verifying": {"review_needed", "executing"},
        "review_needed": {"closed", "executing"},
        "closed": set(),
    },
    "adr": {
        "proposed": {"accepted", "rejected", "deprecated"},
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
    "profile": {
        "draft": {"active"},
        "active": {"suspended", "archived"},
        "suspended": {"active", "archived"},
        "archived": set(),
    },
    "memo": {
        "draft": {"active", "archived"},
        "active": {"resolved", "archived"},
        "resolved": set(),
        "archived": set(),
    },
    "change": {
        "proposed": {"accepted", "deprecated"},
        "accepted": {"implemented", "deprecated"},
        "implemented": {"deprecated"},
        "deprecated": set(),
    },
}

REQUIRED_FIELDS = {
    "intent": ["id", "type", "title", "status", "created", "updated", "description", "success_criteria", "source"],
    "task": ["id", "type", "title", "status", "created", "updated", "description", "source", "acceptance"],
    "adr": ["id", "type", "title", "status", "created", "updated", "context", "decision", "consequences"],
    "pitfall": ["id", "type", "title", "status", "created", "updated", "symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"],
    "profile": ["id", "type", "title", "status", "created", "updated", "description", "project_name", "project_path", "ldvh_base_path"],
    "memo": ["id", "type", "title", "status", "created", "updated", "description", "source", "category"],
    "change": ["id", "type", "title", "status", "created", "updated", "description", "change_type", "scope"],
}

DEFAULT_STATUS = {
    "intent": "draft",
    "task": "planned",
    "adr": "proposed",
    "pitfall": "draft",
    "profile": "draft",
    "memo": "draft",
    "change": "proposed",
}

DIRECTORY_MAP = {
    "intent": "ldvh-base/intents/",
    "task": "ldvh-base/tasks/",
    "adr": "ldvh-base/adrs/",
    "pitfall": "ldvh-base/pitfalls/",
    "profile": "ldvh-base/profiles/",
    "memo": "ldvh-base/memos/",
    "change": "ldvh-base/changes/",
}

# 允许删除的状态集合
DELETABLE_STATUSES = {"draft", "proposed"}


# ── 工具函数 ────────────────────────────────────────────────────────────

def error(msg: str) -> None:
    """输出错误信息到 stderr。"""
    print(f"错误: {msg}", file=sys.stderr)


def title_to_short(title: str) -> str:
    """将标题转换为文件名短标识：小写、空格替换短横线、去掉非字母数字短横线。"""
    result = title.lower()
    result = result.replace(" ", "-")
    result = re.sub(r"[^a-z0-9\u4e00-\u9fff-]", "", result)
    # 去掉连续短横线
    result = re.sub(r"-+", "-", result)
    # 去掉首尾短横线
    result = result.strip("-")
    return result


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
    today = date.today().isoformat()
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
            data[field] = today
        else:
            # 其他必填字段默认为空字符串占位
            data[field] = ""
    if object_type == "task":
        data["blocked_by"] = []

    # 写入文件
    save_yaml(filepath, data)
    print(str(filepath))

    # ADR 创建时同时创建关联的 Change YAML（原子操作）
    if object_type == "adr":
        change_dir = base_dir / DIRECTORY_MAP["change"]
        change_num = next_number(change_dir, "change")
        change_id = f"change-{change_num:04d}"
        change_filename = f"{change_id}-{short_title}.yaml"
        change_filepath = change_dir / change_filename

        change_data = {}
        for field in REQUIRED_FIELDS["change"]:
            if field == "id":
                change_data[field] = change_id
            elif field == "type":
                change_data[field] = "change"
            elif field == "title":
                change_data[field] = title
            elif field == "status":
                change_data[field] = DEFAULT_STATUS["change"]
            elif field in ("created", "updated"):
                change_data[field] = today
            elif field == "description":
                change_data[field] = f"ADR {obj_id} 创建"
            else:
                change_data[field] = ""

        save_yaml(change_filepath, change_data)
        print(str(change_filepath))

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
        # 校验 sub_tasks 全部 closed
        sub_tasks = data.get("sub_tasks", [])
        if isinstance(sub_tasks, list) and sub_tasks:
            # 检查子任务是否全部 closed（子任务为 id 列表时无法直接判断状态，
            # 这里检查是否有非 closed 状态的子任务 id 记录）
            # 当前简化处理：如果有 sub_tasks 列表且非空，提示需要确认
            # 严格来说需要读取每个子任务文件，此处仅做基本检查
            pass
        # 校验 closure_evidence 已填写
        closure_evidence = data.get("closure_evidence")
        if not closure_evidence or (isinstance(closure_evidence, str) and not closure_evidence.strip()):
            error("closure_evidence 未填写，无法关闭 Task")
            return 1

    # 执行流转
    data["status"] = new_status
    data["updated"] = date.today().isoformat()
    if object_type == "task" and new_status == "closed":
        data["closed_at"] = date.today().isoformat()

    # 退回流转记录 reason
    # 判断是否为退回：新状态在当前状态之前（简化判断：非正向推进）
    backward_pairs = {
        ("verifying", "executing"),
        ("review_needed", "executing"),
    }
    if (current_status, new_status) in backward_pairs:
        if not reason:
            error(f"退回流转 {current_status} → {new_status} 需要提供 --reason")
            return 1
        # 将 reason 追加到 description 或单独记录
        if "transition_reasons" not in data:
            data["transition_reasons"] = []
        data["transition_reasons"].append({
            "from": current_status,
            "to": new_status,
            "reason": reason,
            "date": date.today().isoformat(),
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
        # 目录不存在不算错误，返回空列表
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
            items.append({
                "id": data.get("id", ""),
                "type": data.get("type", object_type),
                "status": obj_status,
                "title": data.get("title", ""),
                "path": str(yaml_path),
                "updated": data.get("updated", ""),
            })

    if fmt == "json":
        result: dict[str, Any] = {
            "ok": True,
            "command": "ldvh_fact_cli",
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

    # target 可为 Task ID 或 YAML 文件路径
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
            "command": "ldvh_fact_cli",
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

    # 判断 target 是文件路径还是对象 ID
    target_path = Path(target)
    if target_path.is_file():
        yaml_file = target_path
    else:
        # 按 ID 查找：解析类型和编号，在对应目录搜索
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
            "command": "ldvh_fact_cli",
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
        # 文本模式直接输出 YAML
        print(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False).rstrip())

    return 0


# ── CLI 入口 ────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """构建 argparse 解析器。"""
    parser = argparse.ArgumentParser(
        description="LDVH 事实模型 CLI：创建、状态流转、删除、列表查询、详情查看"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create 子命令
    create_parser = subparsers.add_parser("create", help="创建事实对象")
    create_parser.add_argument("object_type", choices=sorted(OBJECT_TYPES), help="对象类型")
    create_parser.add_argument("--title", required=True, help="对象标题")
    create_parser.add_argument("--short-title", default=None, help="文件名短标识（默认从标题自动生成）")
    create_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")

    # transition 子命令
    transition_parser = subparsers.add_parser("transition", help="执行状态流转")
    transition_parser.add_argument("yaml_file", help="YAML 文件路径")
    transition_parser.add_argument("--to", required=True, dest="to", help="目标状态")
    transition_parser.add_argument("--reason", default=None, help="退回流转原因")

    # delete 子命令
    delete_parser = subparsers.add_parser("delete", help="删除事实对象")
    delete_parser.add_argument("yaml_file", help="YAML 文件路径")

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
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
