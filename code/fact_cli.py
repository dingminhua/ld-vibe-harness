#!/usr/bin/env python3
"""LDVH 事实模型 CLI 工具：create / transition / delete / list / show / search / stats / related / link-rule / deprecate / supersede。

对 LDVH 当前工作对象（workcase, adr, pitfall, spark, study）
执行创建、状态流转、删除、列表查询、详情查看、搜索、统计等操作。
Git 提交记录使用 Git commit records 作为事实源，不通过本 CLI 管理。
ADR 专属写入操作（link-rule / deprecate）必须携带 Human Gate 确认参数。
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

# Git 提交记录使用 Git commit records 作为事实源，不通过本 CLI 管理 YAML 文件
OBJECT_TYPES = {"workcase", "adr", "pitfall", "spark", "study"}


class BlockScalarDumper(yaml.SafeDumper):
    pass


class LiteralString(str):
    pass


def _string_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    style = "|" if isinstance(data, LiteralString) or "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style=style)


BlockScalarDumper.add_representer(str, _string_representer)
BlockScalarDumper.add_representer(LiteralString, _string_representer)

LIST_SUMMARY_FIELDS = ("priority", "importance")
GLOBAL_REMOVED_FIELDS = {"related_changes", "related_" + "work" + "areas"}
REMOVED_FIELDS_BY_TYPE = {
    "adr": {"related_taskplans", "related_tasks", "related_objects", "superseded_by", "alternatives", "affects"},
    "study": {"related_taskplans", "related_tasks", "related_refs", "superseded_by", "source", "source_detail", "source_docs"},
}

ID_PATTERNS = {
    "workcase": re.compile(r"^workcase-\d{4}$"),
    "adr": re.compile(r"^adr-\d{4}$"),
    "pitfall": re.compile(r"^pitfall-\d{4}$"),
    "spark": re.compile(r"^spark-\d{4}$"),
    "study": re.compile(r"^study-\d{4}$"),
}

FILENAME_PATTERNS = {
    "workcase": re.compile(r"^workcase-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "adr": re.compile(r"^adr-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "pitfall": re.compile(r"^pitfall-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "spark": re.compile(r"^spark-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "study": re.compile(r"^study-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$"),
}

WORKCASE_LEGACY_STATUSES = {"draft", "active", "review_needed"}
WORKCASE_CURRENT_STATUSES = {
    "subagents_plan_reviewing",
    "human_plan_confirming",
    "executing",
    "result_self_checking",
    "subagents_result_reviewing",
    "human_closure_confirming",
    "closed",
}
WORKCASE_CLOSURE_OUTCOMES = {"completed", "partial_completed", "cancelled", "superseded", "invalid", "degraded_accepted"}

VALID_STATUSES = {
    "workcase": WORKCASE_CURRENT_STATUSES | WORKCASE_LEGACY_STATUSES,
    "adr": {"active", "archived", "deprecated"},
    "pitfall": {"active", "archived"},
    "spark": {"pending", "resolved", "discarded"},
    "study": {"active", "archived"},
}
VALID_SPARK_RESOLVED_TO_TYPES = {"workcase", "adr", "pitfall", "docs", "governed-projects", "other"}

VALID_TRANSITIONS = {
    "workcase": {
        "draft": {"active"},
        "active": {"review_needed"},
        "review_needed": {"closed", "active"},
        "subagents_plan_reviewing": {"human_plan_confirming"},
        "human_plan_confirming": {"executing", "subagents_plan_reviewing"},
        "executing": {"result_self_checking", "subagents_plan_reviewing"},
        "result_self_checking": {"subagents_result_reviewing", "executing"},
        "subagents_result_reviewing": {"human_closure_confirming", "result_self_checking", "executing"},
        "human_closure_confirming": {"closed", "subagents_result_reviewing", "result_self_checking", "executing", "subagents_plan_reviewing"},
        "closed": set(),
    },
    "adr": {
        "active": {"archived", "deprecated"},
        "archived": set(),
        "deprecated": set(),
    },
    "pitfall": {
        "active": {"archived"},
        "archived": set(),
    },
    "spark": {
        "pending": {"resolved", "discarded"},
        "resolved": {"discarded"},
        "discarded": set(),
    },
    "study": {
        "active": {"archived"},
        "archived": set(),
    },
}

REQUIRED_FIELDS = {
    "workcase": ["id", "type", "title", "goal", "status", "created", "updated", "priority", "description", "success_criteria", "source", "orchestration"],
    "adr": ["id", "type", "title", "status", "created", "updated", "date", "context", "decision", "consequences"],
    "pitfall": ["id", "type", "title", "status", "created", "updated", "symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"],
    "spark": ["id", "type", "title", "status", "created", "updated", "description", "source", "priority"],
    "study": ["id", "type", "title", "status", "created", "updated", "summary"],
}

DEFAULT_STATUS = {
    "workcase": "subagents_plan_reviewing",
    "adr": "active",
    "pitfall": "active",
    "spark": "pending",
    "study": "active",
}

DIRECTORY_MAP = {
    "workcase": "ldvh-base/workcases/",
    "adr": "ldvh-base/adrs/",
    "pitfall": "ldvh-base/pitfalls/",
    "spark": "ldvh-base/sparks/",
    "study": "ldvh-base/studies/",
}

# 允许删除的状态集合
DELETABLE_STATUSES = {"draft", "pending", "subagents_plan_reviewing"}

# ADR 专属常量
ADR_TERMINAL_STATUSES = {"archived", "deprecated"}
ADR_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PITFALL_ACTIVE_REQUIRED_FIELDS = (
    "symptoms",
    "trigger_conditions",
    "root_cause",
    "resolution",
    "verification",
    "avoidance",
    "applicability",
)
EVIDENCE_REQUIRED_HEADINGS = ("验证计划", "验证命令", "验证结果", "结论")


# ── 工具函数 ────────────────────────────────────────────────────────────

def error(msg: str) -> None:
    """输出错误信息到 stderr。"""
    print(f"错误: {msg}", file=sys.stderr)


def is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    return False


def evidence_headings(value: str) -> list[str]:
    return [line[3:].strip() for line in value.splitlines() if re.match(r"^##\s+", line)]


def evidence_has_required_structure(value: str) -> bool:
    headings = evidence_headings(value)
    ordered = [heading for heading in headings if heading in EVIDENCE_REQUIRED_HEADINGS]
    return ordered == list(EVIDENCE_REQUIRED_HEADINGS)


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
        if f.is_file() and f.suffix in {".yaml", ".md"}:
            m = re.match(rf"^{prefix}-(\d{{4}})-", f.name)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
    return max_num + 1


def load_yaml(path: Path) -> dict | None:
    """加载 YAML 文件，失败时输出错误并返回 None。"""
    if path.suffix == ".md":
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            error(f"读取文件失败: {exc}")
            return None
        if not content.startswith("---\n"):
            error("Markdown Study 缺少 YAML frontmatter")
            return None
        end = content.find("\n---", 4)
        if end == -1:
            error("Markdown Study 缺少 frontmatter 结束标记")
            return None
        try:
            data = yaml.safe_load(content[4:end])
        except yaml.YAMLError as exc:
            error(f"frontmatter 解析失败: {exc}")
            return None
        if not isinstance(data, dict):
            error("frontmatter 顶层结构必须是映射对象")
            return None
        data["report_body"] = content[end + 4:].lstrip("\n")
        return data
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


def object_glob(object_type: str) -> str:
    return f"{object_type}-*.md" if object_type == "study" else f"{object_type}-*.yaml"


def save_yaml(path: Path, data: dict) -> None:
    """将数据写入 YAML 文件；Study Markdown 写入 frontmatter 和正文。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".md":
        frontmatter = {key: value for key, value in data.items() if key != "report_body"}
        if frontmatter.get("type") == "study" and isinstance(frontmatter.get("summary"), str):
            frontmatter["summary"] = LiteralString(frontmatter["summary"])
        body = str(data.get("report_body") or "").strip()
        if not body:
            title = data.get("title", "研究报告")
            body = (
                f"# {title}\n\n"
                "## 研究问题\n\n"
                "待补充。\n\n"
                "## 输入与边界\n\n"
                "待补充。\n\n"
                "## 关键发现\n\n"
                "待补充。\n\n"
                "## 建议\n\n"
                "待补充。\n\n"
                "## 后续分流\n\n"
                "待补充。"
            )
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(blockify_multiline(frontmatter), f, Dumper=BlockScalarDumper, allow_unicode=True, default_flow_style=False, sort_keys=False)
            f.write("---\n\n")
            f.write(body)
            f.write("\n")
        return
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(blockify_multiline(data), f, Dumper=BlockScalarDumper, allow_unicode=True, default_flow_style=False, sort_keys=False)


def blockify_multiline(value: Any) -> Any:
    if isinstance(value, str) and "\n" in value:
        return LiteralString(value)
    if isinstance(value, dict):
        return {key: blockify_multiline(item) for key, item in value.items()}
    if isinstance(value, list):
        return [blockify_multiline(item) for item in value]
    return value


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
    for filepath in sorted(directory.glob(object_glob(object_type))):
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
        "status": "active",
        "created": now,
        "updated": now,
        "date": getattr(args, "date", None) or date.today().isoformat(),
        "context": context_with_gate,
        "decision": args.decision,
        "consequences": args.consequences,
        "related_rules": _parse_list_values(getattr(args, "related_rules", None)),
        "archive_reason": "",
        "deprecated_reason": "",
    }
    return data


def _default_workcase_orchestration() -> dict[str, Any]:
    return {
        "mode": "single",
        "execution_items": [
            {
                "id": "item-1",
                "title": "整理可审核执行方案",
                "role": "main-controller",
                "mode": "single",
                "input_refs": ["current-conversation"],
                "expected_output": "形成可供方案审核的执行计划、成功标准和验证边界。",
                "status": "pending",
                "result_summary": None,
                "evidence_refs": [],
                "blocking_reason": None,
            }
        ],
        "plan_review": {
            "orchestration_owner": "main_controller",
            "workflow_ref": None,
            "review_policy": {
                "selection_reason": "默认由主控选择必要审核视角；如存在专门审核流程，应改由 workflow 接管。",
                "required_perspectives": [],
                "optional_perspectives": [],
                "tool_method_requirements": [],
                "aggregation_rule": "存在 fail 或 needs_human_gate 结论时不得进入 Human 方案确认，必须先处理或提交 Human 裁决。",
            },
            "review_items": [],
            "controller_resolution": None,
            "human_confirmation": None,
        },
        "result_review": {
            "controller_self_check": None,
            "orchestration_owner": "main_controller",
            "workflow_ref": None,
            "review_policy": {
                "selection_reason": "默认由主控在结果自检后选择必要复核视角。",
                "required_perspectives": [],
                "optional_perspectives": [],
                "tool_method_requirements": [],
                "aggregation_rule": "存在 fail 或 needs_human_gate 结论时不得提交 Human 关闭确认，必须先处理或提交 Human 裁决。",
            },
            "review_items": [],
            "controller_resolution": None,
            "human_closure_confirmation": None,
        },
    }


def _get_workcase_review_section(data: dict[str, Any], name: str) -> dict[str, Any] | None:
    orchestration = data.get("orchestration")
    if not isinstance(orchestration, dict):
        return None
    section = orchestration.get(name)
    return section if isinstance(section, dict) else None


def _ensure_workcase_review_dict(data: dict[str, Any], name: str) -> dict[str, Any]:
    orchestration = data.setdefault("orchestration", {})
    if not isinstance(orchestration, dict):
        orchestration = {}
        data["orchestration"] = orchestration
    section = orchestration.get(name)
    if not isinstance(section, dict):
        section = {}
        orchestration[name] = section
    return section


def _has_open_execution_items(data: dict[str, Any]) -> bool:
    orchestration = data.get("orchestration")
    execution_items = orchestration.get("execution_items") if isinstance(orchestration, dict) else None
    if not isinstance(execution_items, list):
        return True
    return any(isinstance(item, dict) and item.get("status") in {"pending", "in_progress"} for item in execution_items)


def _require_workcase_review_object(data: dict[str, Any], section_name: str, field_name: str, message: str) -> bool:
    section = _get_workcase_review_section(data, section_name)
    if not isinstance(section, dict) or not isinstance(section.get(field_name), dict):
        error(message)
        return False
    return True


def _set_plan_human_confirmation(data: dict[str, Any], args: argparse.Namespace, now: str) -> None:
    plan_review = _ensure_workcase_review_dict(data, "plan_review")
    if not isinstance(plan_review.get("human_confirmation"), dict):
        plan_review["human_confirmation"] = {
            "decision": "execute",
            "scope": getattr(args, "confirmation_context", "") or "Human Gate 已确认执行范围。",
            "constraints": [],
            "confirmed_at": now,
            "summary": f"{getattr(args, 'confirmed_by', 'Human')} 确认方案可进入执行。",
        }
    if is_empty(data.get("plan_confirmed_at")):
        data["plan_confirmed_at"] = now


def _set_closure_human_confirmation(data: dict[str, Any], args: argparse.Namespace, now: str) -> None:
    result_review = _ensure_workcase_review_dict(data, "result_review")
    if not isinstance(result_review.get("human_closure_confirmation"), dict):
        result_review["human_closure_confirmation"] = {
            "decision": "close",
            "scope": getattr(args, "confirmation_context", "") or "Human Gate 已确认关闭范围。",
            "constraints": [],
            "confirmed_at": now,
            "summary": f"{getattr(args, 'confirmed_by', 'Human')} 确认 WorkCase 可关闭。",
        }


def _append_workcase_revision_history(data: dict[str, Any], args: argparse.Namespace, current_status: str, new_status: str) -> None:
    reason = getattr(args, "reason", None)
    if not reason:
        error(f"退回流转 {current_status} → {new_status} 需要提供 --reason")
        raise SystemExit(1)
    history = data.setdefault("revision_history", [])
    if not isinstance(history, list):
        history = []
        data["revision_history"] = history
    history.append({
        "at": datetime.now().isoformat(),
        "from_status": current_status,
        "to_status": new_status,
        "actor": getattr(args, "confirmed_by", None) or "Human",
        "reason": reason,
        "changed_fields": [],
        "summary": reason,
    })


# ── create 命令 ─────────────────────────────────────────────────────────

def cmd_create(args: argparse.Namespace) -> int:
    """创建 LDVH 事实对象文件。"""
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
    suffix = ".md" if object_type == "study" else ".yaml"
    filename = f"{obj_id}-{short_title}{suffix}"
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
        elif field == "goal":
            data[field] = title
        elif field == "status":
            data[field] = DEFAULT_STATUS[object_type]
        elif field in ("created", "updated"):
            data[field] = now
        elif object_type == "adr" and field == "date":
            data[field] = date.today().isoformat()
        else:
            # 其他必填字段默认为空字符串占位
            data[field] = ""
    if object_type == "workcase":
        data["priority"] = "P2"
        data["orchestration"] = _default_workcase_orchestration()
        data["plan_confirmed_at"] = ""
        data["verification_evidence"] = ""
        data["closure_evidence"] = ""
        data["closure_requested_at"] = ""
        data["review_requested_at"] = ""
        data["closed_at"] = ""
        data["closure_outcome"] = ""
        data["residual_risks"] = []
        data["followup_refs"] = []
        data["revision_history"] = []
        data["related_docs"] = []
        data["related_adrs"] = []
        data["related_sparks"] = []
        data["related_pitfalls"] = []
        data["related_workcases"] = []
    if object_type == "spark":
        data["description"] = f"{title} 的火花摘要。"
        data["priority"] = "P3"
        data["source"] = "conversation"
        data["source_detail"] = ""
        data["evolution"] = []
        data["resolved_to"] = ""
        data["resolved_at"] = ""
        data["discard_reason"] = ""
        data["related_workcases"] = []
        data["related_adrs"] = []
        data["related_studies"] = []
        data["related_docs"] = []
    if object_type == "pitfall":
        data["symptoms"] = "待补充已解决问题的具体现象。"
        data["trigger_conditions"] = "待补充触发条件、上下文或复现场景。"
        data["root_cause"] = "待补充根因或误判原因。"
        data["resolution"] = "待补充已验证的解决方式。"
        data["verification"] = (
            "## 验证计划\n\n"
            "待补充验证计划。\n\n"
            "## 验证命令\n\n"
            "待补充验证命令或人工验证方式。\n\n"
            "## 验证结果\n\n"
            "待补充验证结果。\n\n"
            "## 结论\n\n"
            "待补充是否具备复用价值。"
        )
        data["avoidance"] = "待补充后续规避策略。"
        data["applicability"] = "待补充适用范围和不适用范围。"
        data["tags"] = []
        data["source_objects"] = []
        data["source_sparks"] = []
        data["related_adrs"] = []
        data["related_docs"] = []
        data["related_rules"] = []
        data["archive_reason"] = ""
        data["notes"] = ""
    if object_type == "study":
        data["user_intent"] = ""
        data["summary"] = f"{title} 的稳定研究报告。"
        data["conclusion"] = ""
        data["urls"] = []
        data["related_sparks"] = []
        data["related_workcases"] = []
        data["related_adrs"] = []
        data["related_pitfalls"] = []
        data["related_docs"] = []
        data["archive_reason"] = ""
        data["report_body"] = (
            f"# {title}\n\n"
            "## 研究问题\n\n"
            "待补充。\n\n"
            "## 输入与边界\n\n"
            "待补充。\n\n"
            "## 关键发现\n\n"
            "待补充。\n\n"
            "## 建议\n\n"
            "待补充。\n\n"
            "## 后续分流\n\n"
            "待补充。\n"
        )

    # ADR 创建时回写 Human Gate 记录到 context
    if object_type == "adr":
        gate_record = (
            f"[Human Gate 确认记录: 确认人={getattr(args, 'confirmed_by', 'N/A')}, "
            f"确认时间={now}, 确认上下文={getattr(args, 'confirmation_context', 'N/A')}]"
        )
        data["context"] = gate_record
        data["decision"] = "待补充。"
        data["consequences"] = "## 正向价值\n\n待补充。\n\n## 逆向价值\n\n当前决策无逆向价值\n\n## 实施成本\n\n待补充。\n\n## 风险评估\n\n待补充。\n\n## 注意事项\n\n待补充。\n"
        data["related_workcases"] = []
        data["related_sparks"] = []
        data["related_adrs"] = []
        data["related_rules"] = []
        data["archive_reason"] = ""
        data["deprecated_reason"] = ""

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

    if object_type == "adr" and new_status == "archived":
        if is_empty(data.get("archive_reason")):
            error("archive_reason 未填写，无法归档 ADR")
            return 1

    if object_type == "adr" and new_status == "deprecated":
        if is_empty(data.get("deprecated_reason")):
            error("deprecated_reason 未填写，无法废弃 ADR")
            return 1

    # WorkCase 激活和关闭审查条件校验（新 WorkCase 契约）
    if object_type == "workcase" and current_status == "draft" and new_status == "active":
        orchestration = data.get("orchestration")
        execution_items = orchestration.get("execution_items") if isinstance(orchestration, dict) else None
        if not isinstance(execution_items, list) or not execution_items:
            error("orchestration.execution_items 未填写，无法激活 WorkCase")
            return 1

    if object_type == "workcase" and current_status == "active" and new_status == "review_needed":
        for field in ("verification_evidence", "closure_evidence"):
            value = data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                error(f"{field} 未填写，无法将 WorkCase 标记为 review_needed")
                return 1
        if not data.get("review_requested_at"):
            data["review_requested_at"] = datetime.now().isoformat()

    if object_type == "workcase" and current_status == "review_needed" and new_status == "closed":
        for field in ("review_requested_at", "verification_evidence", "closure_evidence"):
            value = data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                error(f"{field} 未填写，无法关闭 WorkCase")
                return 1

    if object_type == "workcase" and current_status == "subagents_plan_reviewing" and new_status == "human_plan_confirming":
        if not _require_workcase_review_object(
            data,
            "plan_review",
            "controller_resolution",
            "plan_review.controller_resolution 未填写，无法进入 Human 方案确认",
        ):
            return 1

    if object_type == "workcase" and current_status == "human_plan_confirming" and new_status == "executing":
        _set_plan_human_confirmation(data, args, datetime.now().isoformat())

    if object_type == "workcase" and current_status == "executing" and new_status == "result_self_checking":
        if _has_open_execution_items(data):
            error("仍存在 pending 或 in_progress 执行项，无法进入结果自检")
            return 1

    if object_type == "workcase" and current_status == "result_self_checking" and new_status == "subagents_result_reviewing":
        if not _require_workcase_review_object(
            data,
            "result_review",
            "controller_self_check",
            "result_review.controller_self_check 未填写，无法进入子 Agent 结果复核",
        ):
            return 1
        for field in ("verification_evidence", "closure_evidence"):
            if is_empty(data.get(field)):
                error(f"{field} 未填写，无法进入子 Agent 结果复核")
                return 1

    if object_type == "workcase" and current_status == "subagents_result_reviewing" and new_status == "human_closure_confirming":
        if not _require_workcase_review_object(
            data,
            "result_review",
            "controller_resolution",
            "result_review.controller_resolution 未填写，无法进入 Human 关闭确认",
        ):
            return 1
        if is_empty(data.get("closure_requested_at")):
            data["closure_requested_at"] = datetime.now().isoformat()

    if object_type == "workcase" and current_status == "human_closure_confirming" and new_status == "closed":
        if is_empty(data.get("plan_confirmed_at")):
            error("plan_confirmed_at 未填写，无法关闭 WorkCase")
            return 1
        if not _require_workcase_review_object(
            data,
            "plan_review",
            "human_confirmation",
            "plan_review.human_confirmation 未填写，无法关闭 WorkCase",
        ):
            return 1
        if not _require_workcase_review_object(
            data,
            "result_review",
            "controller_self_check",
            "result_review.controller_self_check 未填写，无法关闭 WorkCase",
        ):
            return 1
        if not _require_workcase_review_object(
            data,
            "result_review",
            "controller_resolution",
            "result_review.controller_resolution 未填写，无法关闭 WorkCase",
        ):
            return 1
        for field in ("closure_requested_at", "verification_evidence", "closure_evidence", "closure_outcome"):
            if is_empty(data.get(field)):
                error(f"{field} 未填写，无法关闭 WorkCase")
                return 1
        if data.get("closure_outcome") not in WORKCASE_CLOSURE_OUTCOMES:
            error(f"closure_outcome 不合法，有效值: {', '.join(sorted(WORKCASE_CLOSURE_OUTCOMES))}")
            return 1
        _set_closure_human_confirmation(data, args, datetime.now().isoformat())

    # Spark 分流条件校验（pending → resolved）
    if object_type == "spark" and current_status == "pending" and new_status == "resolved":
        resolved_to = data.get("resolved_to")
        if not resolved_to or (isinstance(resolved_to, str) and not resolved_to.strip()):
            error("resolved_to 未填写，无法将 Spark 标记为 resolved")
            return 1
        if not isinstance(resolved_to, dict):
            error("resolved_to 必须是 {type, ref} 对象，无法将 Spark 标记为 resolved")
            return 1
        target_type = resolved_to.get("type")
        target_ref = resolved_to.get("ref")
        if not target_type or not target_ref:
            error("resolved_to 必须填写 type 和 ref，无法将 Spark 标记为 resolved")
            return 1
        if target_type not in VALID_SPARK_RESOLVED_TO_TYPES:
            valid_values = ", ".join(sorted(VALID_SPARK_RESOLVED_TO_TYPES))
            error(f"resolved_to.type 必须是以下值之一: {valid_values}；Study 只能通过 related_studies 关联")
            return 1
        if not data.get("resolved_at"):
            data["resolved_at"] = datetime.now().isoformat()

    if object_type == "spark" and new_status == "discarded":
        discard_reason = data.get("discard_reason")
        if not discard_reason or (isinstance(discard_reason, str) and not discard_reason.strip()):
            error("discard_reason 未填写，无法废弃 Spark")
            return 1

    if object_type == "study" and new_status == "archived":
        archive_reason = data.get("archive_reason")
        if not archive_reason or (isinstance(archive_reason, str) and not archive_reason.strip()):
            error("archive_reason 未填写，无法归档 Study")
            return 1

    if object_type == "pitfall" and current_status != "active" and new_status == "active":
        for field in PITFALL_ACTIVE_REQUIRED_FIELDS:
            if is_empty(data.get(field)):
                error(f"{field} 未填写，无法激活 Pitfall")
                return 1
        verification = data.get("verification")
        if not isinstance(verification, str) or not evidence_has_required_structure(verification):
            error("verification 未按 05.02 四段式顺序填写，无法激活 Pitfall")
            return 1

    if object_type == "pitfall" and new_status == "archived":
        archive_reason = data.get("archive_reason")
        if is_empty(archive_reason):
            error("archive_reason 未填写，无法归档 Pitfall")
            return 1

    # 执行流转
    data["status"] = new_status
    data["updated"] = datetime.now().isoformat()
    if object_type == "workcase" and new_status == "closed":
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

    current_workcase_backward_pairs = {
        ("human_plan_confirming", "subagents_plan_reviewing"),
        ("executing", "subagents_plan_reviewing"),
        ("result_self_checking", "executing"),
        ("subagents_result_reviewing", "result_self_checking"),
        ("subagents_result_reviewing", "executing"),
        ("human_closure_confirming", "subagents_result_reviewing"),
        ("human_closure_confirming", "result_self_checking"),
        ("human_closure_confirming", "executing"),
        ("human_closure_confirming", "subagents_plan_reviewing"),
    }
    if object_type == "workcase" and (current_status, new_status) in current_workcase_backward_pairs:
        try:
            _append_workcase_revision_history(data, args, current_status, new_status)
        except SystemExit:
            return 1

    # 写回文件
    save_yaml(yaml_file, data)
    print(f"{current_status} → {new_status}")


    return 0


# ── delete 命令 ─────────────────────────────────────────────────────────

def cmd_delete(args: argparse.Namespace) -> int:
    """删除事实对象文件。"""
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
        for yaml_path in sorted(directory.glob(object_glob(object_type))):
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
                    suffix = ".md" if obj_type == "study" else ".yaml"
                    for yaml_path in sorted(directory.glob(f"{target}-*{suffix}")):
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
        for yaml_path in sorted(directory.glob(object_glob(otype))):
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
            for yaml_path in sorted(directory.glob(object_glob(otype))):
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
        related_rules = adr.get("related_rules", [])
        all_refs = [str(r) for r in (related_rules or [])]
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
    """废弃 ADR（active → deprecated + deprecated_reason 回写）。"""
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

    updates: dict[str, Any] = {
        "status": "deprecated",
        "updated": _today_iso(),
        "deprecated_reason": args.reason,
    }

    path = _update_adr_file(adr, updates, base_dir)
    print(f"已废弃 ADR: {args.adr_id}")
    return 0


# ── supersede 命令 ─────────────────────────────────────────────────────

def cmd_supersede(args: argparse.Namespace) -> int:
    """兼容旧命令：ADR 不再使用 superseded 状态。"""
    error("ADR 已取消 superseded 状态；请新建 active ADR，并在 related_adrs / related_rules 中记录追溯关系。")
    return 1


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
                    suffix = ".md" if obj_type == "study" else ".yaml"
                    for yp in sorted(directory.glob(f"{target}-*{suffix}")):
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
        if key in ("related_workcases", "related_adrs",
                    "related_sparks", "related_studies", "related_pitfalls", "related_docs",
                    "urls", "source_docs", "source_sparks", "related_rules"):
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

    removed_fields = GLOBAL_REMOVED_FIELDS | REMOVED_FIELDS_BY_TYPE.get(str(object_type), set())
    invalid_fields = sorted(field for field in updates if field in removed_fields)
    if invalid_fields:
        error(f"{object_type} 不允许写入已移除字段: {', '.join(invalid_fields)}")
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
    create_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    _add_authorization_args(create_parser)

    # transition 子命令
    transition_parser = subparsers.add_parser("transition", help="执行状态流转")
    transition_parser.add_argument("yaml_file", help="YAML 文件路径")
    transition_parser.add_argument("--to", required=True, dest="to", help="目标状态")
    transition_parser.add_argument("--reason", default=None, help="退回流转原因")
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

    # show 子命令
    show_parser = subparsers.add_parser("show", help="查看事实对象详情")
    show_parser.add_argument("target", help="YAML 文件路径或对象 ID（如 workcase-0001）")
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
    deprecate_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    _add_authorization_args(deprecate_parser)

    # supersede 子命令
    supersede_parser = subparsers.add_parser("supersede", help="兼容旧命令：ADR 已取消 superseded 状态")
    supersede_parser.add_argument("--old-adr-id", required=True, help="被推翻的 ADR ID")
    supersede_parser.add_argument("--base-dir", default=".", help="项目根目录（默认当前目录）")
    _add_authorization_args(supersede_parser)

    # update 子命令
    update_parser = subparsers.add_parser("update", help="更新事实对象的指定字段")
    update_parser.add_argument("target", help="对象 ID（如 workcase-0002）或 YAML 文件路径")
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
