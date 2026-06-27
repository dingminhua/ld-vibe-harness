#!/usr/bin/env python3
"""LDVH unified hook dispatcher — dual-path entry for lifecycle protocol events.

Two calling conventions, one handler per event:

  Hook path (AI Hook env: WorkBuddy / Codex / Claude Code):
    echo '{"event":"SessionStart","cwd":"/path/to/project"}' | python3 code/hook_dispatch.py

  Rules path (no AI Hook env: Trae etc.):
    python3 code/hook_dispatch.py run session-start --cwd /path/to/project

Both paths execute the same handler logic.  The dispatcher does not pretend
that a CLI call came from an environment Hook.
"""

from __future__ import annotations

import argparse
import shlex
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = PROJECT_ROOT / "hooks" / "ldvh-hooks.yaml"
GIT_COMMIT_ACTION_SPEC = "specs/31-git-commit-action-Git提交行动编排.md"
GIT_COMMIT_SKILL_ID = "ldvh-git-commit"
RUNTIME_FALLBACK_READ_PLAN = [
    {
        "path": "rules/LDVH-RUNTIME-PROTOCOL.md",
        "node_id": "rules/LDVH-RUNTIME-PROTOCOL.md",
        "title": "ldvh-runtime-protocol",
        "priority": "P0",
        "role": "start",
        "reason": "knowledge-map 未返回有效 P0/P1 read_plan 时的固定入口原文。",
        "source_relation": "fallback",
    },
    {
        "path": "specs/06-运行时扩展规范.md",
        "node_id": "specs/06-运行时扩展规范.md",
        "title": "运行时扩展规范",
        "priority": "P1",
        "role": "authority",
        "reason": "Runtime Protocol 来源规范，knowledge-map 不可用或无答案时必须回读。",
        "source_relation": "fallback",
    },
    {
        "path": "specs/attachments/06.Att.02-固定运行时扩展登记表.md",
        "node_id": "specs/attachments/06.Att.02-固定运行时扩展登记表.md",
        "title": "固定运行时扩展登记表",
        "priority": "P1",
        "role": "authority",
        "reason": "Runtime Protocol 固定运行时扩展登记依据，knowledge-map 不可用或无答案时必须回读。",
        "source_relation": "fallback",
    },
]
ACTION_HINT_TO_TASK_TYPE = {
    "fix": "code_change",
    "create": "create",
    "review": "review",
    "modify": "modify",
    "discuss": "discuss",
}
POST_READ_ACTION_BY_TASK_TYPE = {
    "code_change": "建议先运行测试确认当前状态，再基于 read_plan 定位修改点和相关规范",
    "create": "建议先通过 knowledge-map 检查是否已有类似 Spark/WorkCase，避免重复创建",
    "review": "建议按相关审查流程核对来源、影响边界和验证证据",
    "rules_sync_review": "建议按 30 Rules 入口同步审查流程，检查固定 Rules 资产的 source_specs 和 sync_triggers",
    "modify": "建议先运行写入前检查，再按 read_plan 核对受影响事实源和验证入口",
    "discuss": "建议围绕 read_plan 先澄清目标、约束和需要补读的事实源",
}
TOOL_PLAN_BY_TASK_TYPE = {
    "code_change": [
        "python3 code/specs_validate.py v2-check --format text",
    ],
    "create": [
        "python3 code/specs_validate.py knowledge-map --input-scope governed_projects --layer entry --format json",
    ],
    "review": [
        "python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node specs/30-rules-entry-sync-review-Rules入口同步审查.md --task-type rules_sync_review --format json",
    ],
    "rules_sync_review": [
        "python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node specs/30-rules-entry-sync-review-Rules入口同步审查.md --task-type rules_sync_review --format json",
    ],
    "modify": [
        "python3 code/specs_validate.py preflight --target-path <path>",
        "python3 code/specs_validate.py v2-check --format text",
    ],
    "discuss": [
        "python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node <path-or-node> --format json",
    ],
}

# ── Skill registry ──────────────────────────────────────────────────────────

SKILL_MANIFEST_KEY = "ldvh_asset"
SKILLS_ROOT = PROJECT_ROOT / "skills"


def _scan_skills() -> list[dict[str, Any]]:
    """Walk skills/ dir, parse ldvh_asset blocks from SKILL.md files."""
    skills: list[dict[str, Any]] = []
    if not SKILLS_ROOT.is_dir():
        return skills
    for skill_md in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        try:
            text = skill_md.read_text()
        except OSError:
            continue
        # Find the ```yaml … ``` block containing ldvh_asset
        block_start = text.find("```yaml")
        if block_start == -1:
            continue
        block_start = text.find("\n", block_start) + 1
        block_end = text.find("```", block_start)
        if block_end == -1:
            continue
        try:
            data = yaml.safe_load(text[block_start:block_end])
        except yaml.YAMLError:
            continue
        if isinstance(data, dict):
            asset = data.get(SKILL_MANIFEST_KEY, data) if SKILL_MANIFEST_KEY in data else data
        else:
            continue
        if isinstance(asset, dict) and asset.get("type") == "skill":
            asset.setdefault("_canonical_path", str(skill_md.relative_to(PROJECT_ROOT)))
            skills.append(asset)
    return skills


def _match_skill_plan(skills: list[dict[str, Any]], event: str, tool: str,
                      command: str, action_hint: str) -> list[str]:
    """Return skill IDs whose trigger_conditions match the current context.

    Matching rules (AND within each condition, OR across conditions):
      - event:       exact match on canonical event name
      - tool:        substring match on tool name (case-insensitive)
      - command_pattern: substring match on observed command
      - action_hint: value in action_hint list
    """
    matched: list[str] = []
    tool_lower = tool.lower()
    command_lower = command.lower()
    for skill in skills:
        conditions = skill.get("trigger_conditions")
        if not isinstance(conditions, list):
            continue
        for cond in conditions:
            if not isinstance(cond, dict):
                continue
            if cond.get("event") != event:
                continue
            if "tool" in cond and str(cond["tool"]).lower() not in tool_lower:
                continue
            if "command_pattern" in cond and str(cond["command_pattern"]).lower() not in command_lower:
                continue
            if "action_hint" in cond and action_hint not in map(str, cond.get("action_hint", [])):
                continue
            skill_id = skill.get("id", "")
            if skill_id and skill_id not in matched:
                matched.append(skill_id)
    return matched


_SKILL_CACHE: list[dict[str, Any]] | None = None


def _cached_skills() -> list[dict[str, Any]]:
    global _SKILL_CACHE
    if _SKILL_CACHE is None:
        _SKILL_CACHE = _scan_skills()
    return _SKILL_CACHE


def _build_skill_plan(event: str, tool: str = "", command: str = "",
                      action_hint: str = "") -> list[str]:
    """Return a list of Skill IDs relevant to the current dispatch context.

    AI should read skills/<id>/SKILL.md for each returned ID and follow the
    workflow described there.
    """
    return _match_skill_plan(_cached_skills(), event, tool, command, action_hint)


def _receipt_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    home = Path(codex_home) if codex_home else Path.home() / ".codex"
    return home / "ldvh" / "session-receipts"


def _safe_receipt_name(session_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in session_id)
    return safe or "unknown"


def _receipt_path(session_id: str) -> Optional[Path]:
    if not session_id:
        return None
    return _receipt_root() / f"{_safe_receipt_name(session_id)}.json"


def _write_session_receipt(session_id: str, event: str, result: dict[str, Any]) -> None:
    path = _receipt_path(session_id)
    if path is None:
        return
    payload = {
        "session_id": session_id,
        "event": event,
        "written_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def _mark_pre_tool_use_receipt(session_id: str, result: dict[str, Any]) -> None:
    """Update the session receipt with the latest pre_tool_use timestamp for observability."""
    path = _receipt_path(session_id)
    if path is None:
        return
    receipt = _read_session_receipt(session_id)
    if receipt is None:
        return
    observed_at = datetime.now(timezone.utc).isoformat()
    observation = {
        "event": "pre-tool-use",
        "observed_at": observed_at,
        "cwd": result.get("cwd", ""),
        "trigger_source": result.get("trigger_source", ""),
        "session_receipt": result.get("session_receipt", ""),
    }
    if result.get("tool"):
        observation["tool"] = result["tool"]
    if result.get("receipt"):
        observation["receipt"] = result["receipt"]

    events = receipt.get("events")
    if not isinstance(events, list):
        events = []
    events.append(observation)
    receipt["events"] = events[-20:]
    receipt["last_pre_tool_use"] = observation
    receipt["updated_at"] = observed_at
    try:
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def _read_session_receipt(session_id: str) -> Optional[dict[str, Any]]:
    path = _receipt_path(session_id)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _receipt_matches_cwd(receipt: dict[str, Any], cwd: Path) -> bool:
    result = receipt.get("result")
    if not isinstance(result, dict) or result.get("governed") is not True:
        return False
    candidates = []
    for key in ("cwd", "governed_project_path", "governed_subject"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            candidates.append(value)
    for value in result.get("target_paths", []):
        if isinstance(value, str) and value.strip():
            candidates.append(value)
    for raw in candidates:
        try:
            path = Path(raw).expanduser().resolve()
        except OSError:
            path = Path(raw).expanduser()
        try:
            cwd_resolved = cwd.resolve()
        except OSError:
            cwd_resolved = cwd
        if cwd_resolved == path or str(cwd_resolved).startswith(str(path) + os.sep):
            return True
    return False


def _latest_session_receipt(cwd: Path) -> Optional[dict[str, Any]]:
    root = _receipt_root()
    try:
        paths = sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    except OSError:
        return None
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and _receipt_matches_cwd(data, cwd):
            return data
    return None


def _receipt_read_plan_consumed(receipt: Optional[dict[str, Any]]) -> bool:
    if not receipt:
        return False
    consumed = receipt.get("read_plan_consumed")
    return isinstance(consumed, dict) and consumed.get("status") == "acknowledged"


def _commit_action_scope(cwd: Path) -> dict[str, Any]:
    return {
        "repo_root": str(_git_repo_root(cwd)),
        "staged_paths": _git_staged_relative_paths(cwd),
    }


def _receipt_commit_action_acknowledged(receipt: Optional[dict[str, Any]], cwd: Path) -> bool:
    if not receipt:
        return False
    execution = receipt.get("commit_action_execution")
    if not isinstance(execution, dict) or execution.get("status") != "acknowledged":
        return False
    if execution.get("skill_id") != GIT_COMMIT_SKILL_ID:
        return False
    if execution.get("action_member") != GIT_COMMIT_ACTION_SPEC:
        return False
    if execution.get("execution_mode") not in {"skill_runtime_invoked", "manual_equivalent_execution"}:
        return False
    scope = _commit_action_scope(cwd)
    return (
        execution.get("repo_root") == scope["repo_root"]
        and execution.get("staged_paths") == scope["staged_paths"]
    )


def _required_read_plan_paths(receipt: dict[str, Any]) -> list[str]:
    result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
    read_plan = result.get("read_plan") if isinstance(result, dict) else []
    required = []
    if isinstance(read_plan, list):
        for item in read_plan:
            if not isinstance(item, dict):
                continue
            if item.get("priority") not in {"P0", "P1"}:
                continue
            path = item.get("path")
            if isinstance(path, str) and path.strip():
                required.append(path.strip())
    return required


def _has_required_read_plan(read_plan: Any) -> bool:
    if not isinstance(read_plan, list):
        return False
    return any(
        isinstance(item, dict)
        and item.get("priority") in {"P0", "P1"}
        and isinstance(item.get("path"), str)
        and item.get("path", "").strip()
        for item in read_plan
    )


def _normalize_action_hint(action_hint: str) -> tuple[str, str]:
    """Map user-facing action hint to (normalized_hint, task_type). Returns ("unknown", "AMBIGUOUS") for unknowns."""
    normalized = action_hint.strip().lower().replace("_", "-")
    if not normalized:
        return "", ""
    if normalized in {"unknown", "ambiguous"}:
        return normalized, "AMBIGUOUS"
    task_type = ACTION_HINT_TO_TASK_TYPE.get(normalized)
    if task_type:
        return normalized, task_type
    return normalized, "AMBIGUOUS"


def _ack_target_key(cwd: Path, targets: list[Path] | None, receipt: dict[str, Any]) -> list[str]:
    """Build a stable dedup key from cwd and target paths for acknowledge scope comparison."""
    if targets:
        return [str(target) for target in targets]
    result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
    target_paths = result.get("target_paths") if isinstance(result, dict) else []
    if isinstance(target_paths, list) and target_paths:
        return [str(item) for item in target_paths if isinstance(item, str)]
    return [str(cwd)]


def _same_ack_scope(consumed: Any, *, cwd: Path, target_key: list[str], action_hint: str) -> bool:
    """Check whether a prior acknowledge covers the same target/action scope."""
    if not isinstance(consumed, dict) or consumed.get("status") != "acknowledged":
        return False
    stored_target = consumed.get("target")
    if isinstance(stored_target, str):
        stored_targets = [stored_target]
    elif isinstance(stored_target, list):
        stored_targets = [str(item) for item in stored_target]
    else:
        stored_targets = [str(cwd)]
    return (
        consumed.get("cwd") == str(cwd)
        and stored_targets == target_key
        and str(consumed.get("action_hint") or "") == action_hint
    )


def _tool_plan_for_task_type(task_type: str) -> list[str]:
    """Return CLI command suggestions for a given task_type; empty list when unknown."""
    return list(TOOL_PLAN_BY_TASK_TYPE.get(task_type, []))


def _post_read_action_for_task_type(task_type: str) -> str:
    """Return a deterministic Chinese post-read action template for the given task_type."""
    return POST_READ_ACTION_BY_TASK_TYPE.get(task_type, "")


def _build_attention_points(read_plan: list[dict[str, Any]], diagnostics: Any, result_status: str) -> list[str]:
    """Build 3-5 Chinese attention points for the AI from pending work objects, diagnostics, and receipt status."""
    points: list[str] = []
    pending = [
        item
        for item in read_plan
        if isinstance(item, dict) and item.get("source_relation") == "pending_work_object"
    ]
    if pending:
        titles = "、".join(str(item.get("title") or item.get("path")) for item in pending[:3])
        points.append(f"当前有未闭环工作对象需优先核对：{titles}")
    if isinstance(diagnostics, list):
        for diagnostic in diagnostics[:2]:
            if not isinstance(diagnostic, dict):
                continue
            code = diagnostic.get("code") or "diagnostic"
            message = diagnostic.get("message") or "知识地图输出受限"
            points.append(f"诊断提醒 {code}：{message}")
    if result_status == "limited":
        points.append("知识地图处于 limited 状态，继续前需回读 read_plan 中的权威原文。")
    if not points:
        points.append("未发现阻断性知识地图诊断；仍需按 read_plan 回读权威原文。")
    if len(points) < 3:
        points.append("行动前请确认目标、工作对象状态和 Human Gate 边界。")
    if len(points) < 3:
        points.append("修改后应使用对应 Code 或测试入口留下验证证据。")
    return points[:5]


def _expand_next_queries(receipt: dict[str, Any], task_type: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Expand next_queries from a session receipt into deep_read_plan and deep_stop_conditions.

    Skips queries with placeholder start_nodes (containing '<'). Deduplicates by path+node_id.
    """
    result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
    queries = result.get("next_queries") if isinstance(result, dict) else []
    if not isinstance(queries, list):
        return [], []
    read_plan: list[dict[str, Any]] = []
    stop_conditions: list[dict[str, Any]] = []
    seen_read_plan: set[tuple[str, str]] = set()
    seen_stop_conditions: set[str] = set()
    for query in queries:
        if not isinstance(query, dict):
            continue
        start_node = query.get("start_node")
        if not isinstance(start_node, str) or not start_node or "<" in start_node:
            continue
        km = _run_knowledge_map(
            start_node,
            task_type if task_type and task_type != "AMBIGUOUS" else "general",
            input_scope=str(query.get("input_scope") or "entry_navigation"),
            layer=str(query.get("layer") or "neighbors"),
        )
        for item in km.get("read_plan", []) if isinstance(km.get("read_plan"), list) else []:
            if not isinstance(item, dict):
                continue
            key = (str(item.get("path") or ""), str(item.get("node_id") or ""))
            if key in seen_read_plan:
                continue
            seen_read_plan.add(key)
            read_plan.append(item)
        for item in km.get("stop_conditions", []) if isinstance(km.get("stop_conditions"), list) else []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("condition") or item.get("reason") or "")
            if key in seen_stop_conditions:
                continue
            seen_stop_conditions.add(key)
            stop_conditions.append(item)
    return read_plan[:24], stop_conditions[:12]


def _acknowledge_read_plan(session_id: str, cwd: Path, *, trigger_source: str = "rules",
                           action_hint: str = "", targets: list[Path] | None = None) -> dict[str, Any]:
    receipt = _read_session_receipt(session_id) if session_id else _latest_session_receipt(cwd)
    if not receipt:
        return {
            "acknowledged": False,
            "blocked": True,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "reason": "未找到可确认的 session receipt；必须先完成 session-start。",
        }
    normalized_action_hint, task_type = _normalize_action_hint(action_hint)
    target_key = _ack_target_key(cwd, targets, receipt)
    consumed = receipt.get("read_plan_consumed")
    if _same_ack_scope(consumed, cwd=cwd, target_key=target_key, action_hint=normalized_action_hint):
        return {
            "acknowledged": True,
            "blocked": False,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "session_id": receipt.get("session_id", ""),
            "guide_receipt": "found",
        }

    ack = {
        "status": "acknowledged",
        "acknowledged_at": datetime.now(timezone.utc).isoformat(),
        "trigger_source": trigger_source,
        "cwd": str(cwd),
        "target": target_key,
        "action_hint": normalized_action_hint,
        "required_paths": _required_read_plan_paths(receipt),
    }
    result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
    if isinstance(result, dict) and result.get("governed") is True and not ack["required_paths"]:
        return {
            "acknowledged": False,
            "blocked": True,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "session_id": receipt.get("session_id", ""),
            "reason": "管辖项目 session receipt 缺少 P0/P1 read_plan required_paths，不能确认空读取计划。",
            "next_action": "重新运行 session-start 获取 knowledge-map read_plan；若 knowledge-map 无答案，dispatcher 必须返回固定 fallback read_plan。",
        }
    receipt["read_plan_consumed"] = ack
    receipt["updated_at"] = ack["acknowledged_at"]
    path = _receipt_path(str(receipt.get("session_id", "")))
    if path is None:
        return {
            "acknowledged": False,
            "blocked": True,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "reason": "receipt 缺少 session_id，无法写入 read_plan 消费证据。",
        }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        return {
            "acknowledged": False,
            "blocked": True,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "reason": f"写入 read_plan 消费证据失败: {exc}",
        }
    deep_read_plan, deep_stop_conditions = _expand_next_queries(receipt, task_type)
    result_payload = {
        "acknowledged": True,
        "blocked": False,
        "cwd": str(cwd),
        "trigger_source": trigger_source,
        "session_id": receipt.get("session_id", ""),
        "required_paths": ack["required_paths"],
        "receipt": "read_plan_consumed",
    }
    if normalized_action_hint:
        result_payload["action_hint"] = normalized_action_hint
        result_payload["task_type"] = task_type
        result_payload["tool_plan"] = _tool_plan_for_task_type(task_type)
        result_payload["post_read_action"] = _post_read_action_for_task_type(task_type)
        result_payload["skill_plan"] = _build_skill_plan("acknowledge-read-plan", action_hint=task_type)
        if result_payload["skill_plan"]:
            result_payload["skill_plan_hint"] = (
                "对于列出的每个 skill_id，请读取 skills/<id>/SKILL.md 并按其中的 Workflow 执行。"
            )
    # Surface skill_plan accumulated from pre-tool-use into session receipt
    receipt_skill_plan = receipt.get("skill_plan", []) if receipt else []
    if receipt_skill_plan and not result_payload.get("skill_plan"):
        result_payload["skill_plan"] = receipt_skill_plan
        result_payload["skill_plan_hint"] = (
            "对于列出的每个 skill_id，请读取 skills/<id>/SKILL.md 并按其中的 Workflow 执行。"
        )
    if deep_read_plan:
        result_payload["deep_read_plan"] = deep_read_plan
    if deep_stop_conditions:
        result_payload["deep_stop_conditions"] = deep_stop_conditions
    return result_payload


def _acknowledge_commit_action(session_id: str, cwd: Path, *, trigger_source: str = "rules",
                               execution_mode: str = "manual_equivalent_execution") -> dict[str, Any]:
    normalized_mode = execution_mode.strip() or "manual_equivalent_execution"
    if normalized_mode not in {"skill_runtime_invoked", "manual_equivalent_execution"}:
        return {
            "acknowledged": False,
            "blocked": True,
            "cwd": str(cwd),
            "trigger_source": trigger_source,
            "reason": "execution_mode 必须是 skill_runtime_invoked 或 manual_equivalent_execution。",
        }

    subject = resolve_governed_subject(cwd, _git_staged_paths(cwd))
    if subject.get("blocked"):
        return {**subject, **_commit_action_fields(), "acknowledged": False, "trigger_source": trigger_source}
    if not subject.get("governed"):
        return {
            **subject,
            "acknowledged": True,
            "blocked": False,
            "trigger_source": trigger_source,
            "receipt": "no_op_non_governed",
        }

    receipt = _read_session_receipt(session_id) if session_id else _latest_session_receipt(cwd)
    if not receipt:
        return {
            **subject,
            **_commit_action_fields(),
            "acknowledged": False,
            "blocked": True,
            "trigger_source": trigger_source,
            "reason": "未找到可写入 commit action execution 的 session receipt；必须先完成 session-start。",
        }
    if not _receipt_read_plan_consumed(receipt):
        return {
            **subject,
            **_commit_action_fields(),
            "acknowledged": False,
            "blocked": True,
            "trigger_source": trigger_source,
            "reason": "管辖项目提交行动执行确认前必须先消费 session-start receipt 的 P0/P1 read_plan。",
            "next_action": "先运行 acknowledge-read-plan，再读取 skills/ldvh-git-commit/SKILL.md 并执行后重试 acknowledge-commit-action。",
        }

    scope = _commit_action_scope(cwd)
    execution = {
        "status": "acknowledged",
        "acknowledged_at": datetime.now(timezone.utc).isoformat(),
        "trigger_source": trigger_source,
        "execution_mode": normalized_mode,
        "skill_id": GIT_COMMIT_SKILL_ID,
        "action_member": GIT_COMMIT_ACTION_SPEC,
        "repo_root": scope["repo_root"],
        "staged_paths": scope["staged_paths"],
    }
    receipt["commit_action_execution"] = execution
    receipt["updated_at"] = execution["acknowledged_at"]
    path = _receipt_path(str(receipt.get("session_id", "")))
    if path is None:
        return {
            **subject,
            **_commit_action_fields(),
            "acknowledged": False,
            "blocked": True,
            "trigger_source": trigger_source,
            "reason": "receipt 缺少 session_id，无法写入 commit action execution 凭证。",
        }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        return {
            **subject,
            **_commit_action_fields(),
            "acknowledged": False,
            "blocked": True,
            "trigger_source": trigger_source,
            "reason": f"写入 commit action execution 凭证失败: {exc}",
        }
    return {
        **subject,
        **_commit_action_fields(),
        "acknowledged": True,
        "blocked": False,
        "trigger_source": trigger_source,
        "receipt": "commit_action_execution",
        "commit_action_execution": execution,
    }

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _find_governed_config(cwd: Path, targets: list[Path] | None = None) -> Optional[Path]:
    """Find LDVH-GOVERNED-PROJECTS.yaml from target paths first, then cwd."""
    for candidate in [*(targets or []), cwd]:
        direct = _walk_for_governed_config(candidate)
        if direct is not None:
            return direct
        for worktree_root in _git_worktree_roots(candidate):
            config = _walk_for_governed_config(worktree_root)
            if config is not None:
                return config
    return None


def _find_governed_config_for_targets(cwd: Path, targets: list[Path]) -> Optional[Path]:
    try:
        return _find_governed_config(cwd, targets)
    except TypeError:
        # Backward-compatible with tests that monkeypatch the old one-arg helper.
        return _find_governed_config(cwd)  # type: ignore[call-arg]


def _walk_for_governed_config(cwd: Path) -> Optional[Path]:
    for parent in [cwd, *cwd.parents]:
        config = parent / "LDVH-GOVERNED-PROJECTS.yaml"
        if config.is_file():
            return config
    return None


def _git_lookup_cwd(path: Path) -> Path:
    """Return an existing directory suitable for `git -C` for a file/target path."""
    candidate = path.expanduser()
    if candidate.is_file():
        return candidate.parent
    if candidate.is_dir():
        return candidate
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    for parent in [candidate.parent, *candidate.parents]:
        if parent.exists() and parent.is_dir():
            return parent
    return candidate.parent


def _stderr_summary_for_exit_code(exit_code: int) -> str:
    if exit_code == 1:
        return "命令返回 exit_code=1，通常表示检查未通过或目标状态不满足要求。"
    if exit_code == 2:
        return "命令返回 exit_code=2，通常表示参数、配置或输入解析错误。"
    if exit_code == 126:
        return "命令返回 exit_code=126，命令存在但不可执行。"
    if exit_code == 127:
        return "命令返回 exit_code=127，命令不存在或未在 PATH 中。"
    if exit_code < 0:
        return "命令启动失败，请手动检查可执行文件、权限或运行环境。"
    return f"命令返回未知 exit_code={exit_code}，请手动检查 stderr_head。"


def _structured_subprocess_error(command: list[str], exit_code: int, stderr: str,
                                 *, suggested_action: str = "") -> dict[str, Any]:
    stderr_head = (stderr or "").strip()[:500]
    return {
        "status": "error",
        "failed_command": shlex.join(command),
        "exit_code": exit_code,
        "stderr_head": stderr_head,
        "stderr_summary": _stderr_summary_for_exit_code(exit_code),
        "suggested_action": suggested_action or "检查 failed_command、exit_code 和 stderr_head；必要时回到对应 Code 入口或事实源原文定位问题。",
    }


def _git_text_structured(cwd: Path, args: list[str]) -> tuple[str, Optional[dict[str, Any]]]:
    git_cwd = _git_lookup_cwd(cwd)
    command = ["git", "-C", str(git_cwd), *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return "", _structured_subprocess_error(
            command,
            -1,
            str(exc),
            suggested_action="确认 git 可执行文件可用，并检查 cwd 是否存在。",
        )
    if result.returncode != 0:
        return "", _structured_subprocess_error(
            command,
            result.returncode,
            result.stderr,
            suggested_action="确认目标路径位于 Git 仓库内，或改用显式 target/repo root 后重试。",
        )
    return result.stdout.strip(), None


def _git_text(cwd: Path, args: list[str]) -> str:
    stdout, _error = _git_text_structured(cwd, args)
    return stdout


def _git_common_dir(cwd: Path) -> str:
    return _git_text(cwd, ["rev-parse", "--path-format=absolute", "--git-common-dir"])


def _git_remote_url(cwd: Path) -> str:
    return _git_text(cwd, ["remote", "get-url", "origin"])


def _git_worktree_roots(cwd: Path) -> list[Path]:
    output = _git_text(cwd, ["worktree", "list", "--porcelain"])
    roots: list[Path] = []
    for line in output.splitlines():
        if not line.startswith("worktree "):
            continue
        raw = line.removeprefix("worktree ").strip()
        if raw:
            roots.append(Path(raw))
    return roots


def _project_git_value(entry: dict[str, Any], key: str) -> str:
    git_info = entry.get("git")
    if not isinstance(git_info, dict):
        return ""
    value = git_info.get(key, "")
    return value.strip() if isinstance(value, str) else ""


def _resolve_path(path: Path, base: Path) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = base / expanded
    try:
        return expanded.resolve()
    except OSError:
        return expanded.absolute()


def _resolved_common_dir(raw: str) -> str:
    if not raw:
        return ""
    try:
        return str(Path(raw).expanduser().resolve())
    except OSError:
        return str(Path(raw).expanduser().absolute())


def _load_projects(config_path: Path) -> list[dict[str, Any]]:
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    projects = data.get("projects", [])
    return projects if isinstance(projects, list) else []


def _base_match(path: Path, config_path: Path) -> dict[str, Any]:
    base = {
        "governed": False,
        "governed_via": "",
        "governed_project_id": "",
        "governed_project_path": "",
        "git_common_dir": "",
        "git_remote_url": "",
    }
    current = _resolve_path(path, Path.cwd())
    current_common_dir = _resolved_common_dir(_git_common_dir(current))
    current_remote_url = _git_remote_url(current)
    base["git_common_dir"] = current_common_dir
    base["git_remote_url"] = current_remote_url

    matches: list[dict[str, Any]] = []
    for entry in _load_projects(config_path):
        if not isinstance(entry, dict):
            continue
        proj_path = entry.get("path", "")
        if not isinstance(proj_path, str) or not proj_path.strip():
            continue
        resolved = (config_path.parent / proj_path).resolve()
        project_id = entry.get("id", "")
        match = {
            **base,
            "governed": True,
            "governed_project_id": project_id.strip() if isinstance(project_id, str) else "",
            "governed_project_path": str(resolved),
            "project_key": project_id.strip() if isinstance(project_id, str) and project_id.strip() else str(resolved),
        }
        if current == resolved or str(current).startswith(str(resolved) + os.sep):
            match["governed_via"] = "path"
            matches.append(match)
            continue

        registered_common_dir = _resolved_common_dir(_project_git_value(entry, "common_dir"))
        if current_common_dir and registered_common_dir and current_common_dir == registered_common_dir:
            match["governed_via"] = "git.common_dir"
            matches.append(match)
            continue

        project_common_dir = _resolved_common_dir(_git_common_dir(resolved))
        if current_common_dir and project_common_dir and current_common_dir == project_common_dir:
            match["governed_via"] = "git.common_dir"
            matches.append(match)

    project_ids = {item.get("governed_project_id", "") for item in matches}
    if len(project_ids) > 1:
        return {
            **base,
            "blocked": True,
            "reason": "Git identity 命中多个管辖项目，必须拆分或显式确认。",
            "ambiguous_project_ids": sorted(project_ids),
        }
    if matches:
        return matches[0]

    return base


def _governed_project_match(cwd: Path, config_path: Path) -> dict[str, Any]:
    """Return deterministic governed-project match metadata for *cwd*."""
    return _base_match(cwd, config_path)


def _cwd_in_governed_project(cwd: Path, config_path: Path) -> bool:
    """Return True when *cwd* is inside a directory listed in the config."""
    return bool(_governed_project_match(cwd, config_path).get("governed"))


def _target_resolution(path: Path, config_path: Path, *, source: str) -> dict[str, Any]:
    match = _base_match(path, config_path)
    resolved = _resolve_path(path, Path.cwd())
    return {
        "target": str(path),
        "normalized_path": str(resolved),
        "source": source,
        "governed": bool(match.get("governed")),
        "governed_via": match.get("governed_via", ""),
        "governed_project_id": match.get("governed_project_id", ""),
        "governed_project_path": match.get("governed_project_path", ""),
        "project_key": match.get("project_key", ""),
        "git_common_dir": match.get("git_common_dir", ""),
        "git_remote_url": match.get("git_remote_url", ""),
        "status": "governed" if match.get("governed") else "not_governed",
        "unknown_reason": "" if match.get("governed") else "not_in_governed_project",
    }


def _discover_subproject_targets(cwd: Path, config_path: Path) -> list[Path]:
    """Return config-listed project paths that exist as subdirectories of *cwd*.

    Used when no explicit targets and cwd itself does not match any project,
    e.g. SessionStart from a workspace root that contains governed subprojects.
    """
    sub_targets: list[Path] = []
    for entry in _load_projects(config_path):
        if not isinstance(entry, dict):
            continue
        proj_path = entry.get("path", "")
        if not isinstance(proj_path, str) or not proj_path.strip():
            continue
        resolved = (config_path.parent / Path(proj_path)).resolve()
        try:
            is_subdir = str(resolved).startswith(str(cwd) + os.sep)
        except (ValueError, OSError):
            is_subdir = False
        if is_subdir and resolved.is_dir() and resolved != cwd:
            sub_targets.append(resolved)
    return sub_targets


def resolve_governed_subject(cwd: Path, targets: list[Path], *, target_sources: list[str] | None = None) -> dict[str, Any]:
    explicit_targets = bool(targets)
    effective_targets = targets if targets else [cwd]
    sources = target_sources if target_sources and len(target_sources) == len(effective_targets) else []
    if not sources:
        sources = ["target"] * len(effective_targets) if explicit_targets else ["cwd-fallback"]
    config = _find_governed_config_for_targets(cwd, effective_targets)
    result: dict[str, Any] = {
        "governed": False,
        "cwd": str(cwd),
        "target_paths": [str(_resolve_path(path, cwd)) for path in effective_targets],
        "target_resolutions": [],
        "event": "",
        "operation_kind": "",
        "read_write_kind": "",
        "tool_name": "",
        "tool_command": "",
        "message_file": "",
        "session_id": "",
        "governed_subject": "",
        "governed_via": "",
        "governed_project_id": "",
        "governed_project_path": "",
        "git_common_dir": "",
        "git_remote_url": "",
        "config_path": str(config) if config else "",
        "subject_source": "target" if explicit_targets else "cwd-fallback",
    }
    if config is None:
        result["message"] = "未找到 LDVH-GOVERNED-PROJECTS.yaml，no-op"
        return result

    resolutions = [_target_resolution(path, config, source=source) for path, source in zip(effective_targets, sources)]
    result["target_resolutions"] = resolutions

    # --- cwd-fallback subproject discovery -----------------------------------
    # When no explicit targets were given and none matched from the config,
    # scan the config's project entries for subdirectories of cwd that exist
    # on disk. This covers the "workspace root contains governed subproject"
    # pattern without requiring the user to change cwd.
    if not explicit_targets and config is not None:
        first_pass_governed = any(item.get("governed") for item in resolutions)
        if not first_pass_governed:
            sub_targets = _discover_subproject_targets(cwd, config)
            if sub_targets:
                sub_sources = [f"cwd-subproject:{t.name}" for t in sub_targets]
                sub_resolutions = [_target_resolution(path, config, source=source)
                                   for path, source in zip(sub_targets, sub_sources)]
                resolutions = sub_resolutions
                result["target_resolutions"] = resolutions
                result["target_paths"] = [str(r["normalized_path"]) for r in resolutions]
                result["subject_source"] = "cwd-subproject"
    # -------------------------------------------------------------------------

    governed_resolutions = [item for item in resolutions if item.get("governed")]
    governed_ids = {item.get("project_key") or item.get("governed_project_path", "") for item in governed_resolutions}
    nongoverned = [item for item in resolutions if not item.get("governed")]

    if len(governed_ids) > 1:
        result.update({
            "blocked": True,
            "reason": "一次操作命中多个管辖项目，必须拆分或显式确认。",
            "blocked_reason": "multiple_governed_projects",
        })
        return result
    if governed_resolutions and nongoverned and explicit_targets:
        result.update({
            "blocked": True,
            "reason": "一次写入操作混合管辖与非管辖目标，必须拆分或显式确认。",
            "blocked_reason": "mixed_governed_and_ungoverned_targets",
        })
        return result
    if not governed_resolutions:
        result["message"] = "工作对象未命中管辖项目，no-op"
        return result

    subject = governed_resolutions[0]
    result.update({
        "governed": True,
        "governed_subject": subject.get("normalized_path", ""),
        "governed_via": subject.get("governed_via", ""),
        "governed_project_id": subject.get("governed_project_id", ""),
        "governed_project_path": subject.get("governed_project_path", ""),
        "git_common_dir": subject.get("git_common_dir", ""),
        "git_remote_url": subject.get("git_remote_url", ""),
    })
    return result


def _run_knowledge_map(start_node: str, task_type: str, *, input_scope: str = "entry_navigation",
                       layer: str = "neighbors") -> dict[str, Any]:
    """Run knowledge-map for the given start node and return the JSON receipt."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "code" / "specs_validate.py"),
        "knowledge-map",
        "--input-scope", input_scope,
        "--layer", layer,
        "--start-node", start_node,
        "--task-type", task_type,
        "--format", "json",
    ]
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    except OSError as exc:
        return _structured_subprocess_error(
            cmd,
            -1,
            str(exc),
            suggested_action="确认 Python 与 specs_validate.py 可执行，并检查当前运行环境。",
        )
    if result.returncode != 0:
        return _structured_subprocess_error(
            cmd,
            result.returncode,
            result.stderr,
            suggested_action="检查 knowledge-map 参数、输入范围和 start_node；必要时回读 active specs 与事实源原文。",
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        error = _structured_subprocess_error(
            cmd,
            0,
            result.stderr or str(exc),
            suggested_action="knowledge-map 已执行但未返回合法 JSON；检查 raw_stdout 与 specs_validate.py 输出格式。",
        )
        error["raw_stdout"] = result.stdout[:500]
        return error


# ---------------------------------------------------------------------------
# registry helpers (for git.commit-msg and extensible events)
# ---------------------------------------------------------------------------


def load_registry(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise RuntimeError(f"读取 Hook registry 失败: {exc}") from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(f"解析 Hook registry 失败: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Hook registry 顶层必须是 YAML object")
    return data


def hooks_for_event(registry: dict[str, Any], event: str) -> list[dict[str, Any]]:
    hooks = registry.get("hooks", [])
    if not isinstance(hooks, list):
        raise RuntimeError("Hook registry 的 hooks 字段必须是 list")
    matched = []
    for hook in hooks:
        if not isinstance(hook, dict):
            continue
        if hook.get("event") == event and hook.get("status", "active") == "active":
            matched.append(hook)
    return matched


def render_arg(value: str, context: dict[str, str]) -> str:
    rendered = value
    for key, replacement in context.items():
        rendered = rendered.replace("{" + key + "}", replacement)
    if "{" in rendered or "}" in rendered:
        raise RuntimeError(f"Hook command 包含未知占位符: {value}")
    return rendered


def render_command(raw_command: Any, context: dict[str, str]) -> list[str]:
    if not isinstance(raw_command, list) or not raw_command:
        raise RuntimeError("Hook command 必须是非空 list")
    command = []
    for part in raw_command:
        if not isinstance(part, str):
            raise RuntimeError("Hook command 的每个参数都必须是 string")
        command.append(render_arg(part, context))
    return command


# ---------------------------------------------------------------------------
# built-in lifecycle protocol handlers
# ---------------------------------------------------------------------------


def _build_user_diagnostic_report(diagnostics: list[dict[str, Any]]) -> str:
    """Build a human-readable diagnostic summary for AI to relay to the user."""
    if not diagnostics:
        return ""
    severity_map = {"error": "错误", "warning": "警告", "info": "提示"}
    lines = [f"LDVH 诊断检测到 {len(diagnostics)} 个问题：", ""]
    for idx, diag in enumerate(diagnostics, 1):
        severity = severity_map.get(diag.get("severity", ""), diag.get("severity", ""))
        code = diag.get("code", "")
        message = diag.get("message", "")
        suggested_owner = diag.get("suggested_owner", "")
        lines.append(f"  {idx}. [{severity}] {code}")
        if message:
            lines.append(f"     {message}")
        if suggested_owner:
            lines.append(f"     建议归口: {suggested_owner}")
    return "\n".join(lines)


def _build_session_start_result(cwd: Path, *, trigger_source: str = "rules",
                                targets: list[Path] | None = None) -> dict[str, Any]:
    subject = resolve_governed_subject(cwd, targets or [])
    governed = bool(subject.get("governed"))
    result = {
        **subject,
        "event": "session-start",
        "operation_kind": "session",
        "read_write_kind": "read",
        "trigger_source": trigger_source,
    }
    if not governed:
        result["attention_points"] = []
        result["tool_plan"] = []
        result["next_queries"] = []
        result["skill_plan"] = []
        return result

    # Run knowledge-map to get the entry chain receipt
    km = _run_knowledge_map("rules/LDVH-RUNTIME-PROTOCOL.md", "rules_entry")
    result["receipt"] = km.get("result_status", "unknown")
    result["diagnostics"] = km.get("diagnostics", 0)
    result["tool_plan"] = _tool_plan_for_task_type("rules_entry")

    # Extract read_plan and stop_conditions for AI consumption
    read_plan = km.get("read_plan", [])
    stop_conditions = km.get("stop_conditions", [])
    next_queries = km.get("next_queries", [])
    if _has_required_read_plan(read_plan):
        result["read_plan"] = read_plan[:8]  # top entries only
        result["read_plan_source"] = "knowledge-map"
    else:
        result["read_plan"] = RUNTIME_FALLBACK_READ_PLAN
        result["read_plan_source"] = "fallback"
        result["action_policy"] = "fallback_read_plan_required"
        result["fallback"] = (
            "knowledge-map 未返回有效 P0/P1 read_plan；AI 必须按 fallback read_plan "
            "回读 Runtime Protocol、active specs 和固定登记原文后再 acknowledge。"
        )
    if stop_conditions:
        result["stop_conditions"] = stop_conditions
    result["next_queries"] = next_queries if isinstance(next_queries, list) else []

    diags = km.get("diagnostics")
    if isinstance(diags, list) and diags:
        result["diagnostics"] = diags
    has_diagnostics = bool(diags) if isinstance(diags, list) else bool(diags)
    if has_diagnostics:
        result.setdefault("action_policy", "continue_with_limited_receipt")
        result["diagnostics_policy"] = "continue_with_limited_receipt"
        result["fallback"] = result.get("fallback") or (
            "知识地图或事实源投影受限；入口握手不阻断行动。AI 应回读 Runtime Protocol、"
            "active specs 和相关事实源原文，并优先修复 diagnostics 指向的问题。"
        )
        report = _build_user_diagnostic_report(diags)
        result["user_diagnostic_report"] = report
        result["next_action"] = (
            "本次 session-start receipt 包含诊断问题。AI 必须在收到此 receipt 后的首次回复中，"
            "主动将 user_diagnostic_report 内容告知用户，不得静默消费。"
            "待用户确认后，优先修复 diagnostics 指向的问题。"
        )

    result["attention_points"] = _build_attention_points(
        result.get("read_plan", []),
        result.get("diagnostics", []),
        str(result.get("receipt") or ""),
    )
    result["skill_plan"] = _build_skill_plan("session-start")
    return result


def handle_acknowledge_read_plan(cwd: Path, *, trigger_source: str = "rules", session_id: str = "",
                                 action_hint: str = "", targets: list[Path] | None = None) -> int:
    """Record that the AI consumed the current receipt read_plan P0/P1 entries."""
    result = _acknowledge_read_plan(
        session_id,
        cwd,
        trigger_source=trigger_source,
        action_hint=action_hint,
        targets=targets,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("acknowledged") else 1


def handle_acknowledge_commit_action(cwd: Path, *, trigger_source: str = "rules", session_id: str = "",
                                     execution_mode: str = "manual_equivalent_execution") -> int:
    """Record that ldvh-git-commit was executed for the current staged scope."""
    result = _acknowledge_commit_action(
        session_id,
        cwd,
        trigger_source=trigger_source,
        execution_mode=execution_mode,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("acknowledged") else 1


def handle_session_start(cwd: Path, *, trigger_source: str = "rules", session_id: str = "",
                         targets: list[Path] | None = None) -> int:
    """SessionStart / session-start handler.

    Determine whether the operation target falls inside an LDVH-governed project.
    If yes, run knowledge-map and return a receipt so the AI can consume
    the full entry chain.
    """
    result = _build_session_start_result(cwd, trigger_source=trigger_source, targets=targets)
    _write_session_receipt(session_id, "session-start", result)
    print(json.dumps(result, ensure_ascii=False))
    return 0


MUTATING_SHELL_PATTERNS = [
    re.compile(r"(^|[;&|]\s*)apply_patch\b"),
    re.compile(r"(^|\s)cat\s+>"),
    re.compile(r"(^|\s)tee\s+"),
    re.compile(r"(^|\s)(rm|mv|cp|touch|mkdir)\s+"),
    re.compile(r"(^|\s)sed\s+(-[A-Za-z]*i|.*\s-i)\b"),
    re.compile(r"(^|\s)echo\s+.*>\s*\S+"),
    re.compile(r">\s*\S+"),
    re.compile(r"(^|\s)git\s+(commit|reset|checkout|merge|rebase|push)\b"),
    re.compile(r"(^|\s)npm\s+version\b"),
    re.compile(r"python3?\s+.*\b(write_text|open\([^)]*['\"]w|unlink|remove|rmtree)\b"),
]


def _stdin_tool_command(payload: dict[str, Any]) -> str:
    for key in ("command", "cmd"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    for key in ("tool_input", "toolInput", "input", "args", "arguments"):
        value = payload.get(key)
        if isinstance(value, dict):
            for nested_key in ("command", "cmd"):
                nested = value.get(nested_key)
                if isinstance(nested, str):
                    return nested
        if isinstance(value, str):
            return value
    return ""


TARGET_KEYS = {
    "target",
    "targets",
    "target_path",
    "target_paths",
    "path",
    "paths",
    "file",
    "files",
    "file_path",
    "file_paths",
    "repo",
    "repo_path",
    "repository",
    "workdir",
}


def _append_target(raw: Any, targets: list[Path], sources: list[str], source: str) -> None:
    if isinstance(raw, str) and raw.strip():
        targets.append(Path(raw.strip()))
        sources.append(source)
    elif isinstance(raw, list):
        for item in raw:
            _append_target(item, targets, sources, source)


def _collect_targets_from_mapping(data: dict[str, Any], targets: list[Path], sources: list[str], *,
                                  prefix: str = "payload") -> None:
    for key, value in data.items():
        normalized = key.replace("-", "_")
        if normalized in TARGET_KEYS:
            _append_target(value, targets, sources, f"{prefix}.{key}")
        if isinstance(value, dict):
            _collect_targets_from_mapping(value, targets, sources, prefix=f"{prefix}.{key}")
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    _collect_targets_from_mapping(item, targets, sources, prefix=f"{prefix}.{key}[{idx}]")


def _targets_from_command(command: str) -> tuple[list[Path], list[str]]:
    targets: list[Path] = []
    sources: list[str] = []
    if not command:
        return targets, sources
    try:
        parts = shlex.split(command)
    except ValueError:
        return targets, sources
    for idx, part in enumerate(parts):
        if part == "-C" and idx + 1 < len(parts):
            _append_target(parts[idx + 1], targets, sources, "command.-C")
        if part in {">", ">>"} and idx + 1 < len(parts):
            _append_target(parts[idx + 1], targets, sources, "command.redirect")
        if part.startswith(">") and len(part) > 1:
            _append_target(part.lstrip(">"), targets, sources, "command.redirect")
    return targets, sources


def _extract_payload_targets(payload: dict[str, Any]) -> tuple[list[Path], list[str]]:
    targets: list[Path] = []
    sources: list[str] = []
    _collect_targets_from_mapping(payload, targets, sources)
    command_targets, command_sources = _targets_from_command(_stdin_tool_command(payload))
    targets.extend(command_targets)
    sources.extend(command_sources)
    return targets, sources


def _tool_requires_read_plan_consumed(tool_name: str, command: str = "") -> bool:
    normalized = tool_name.strip().lower()
    if normalized in {"write", "edit", "multiedit", "multi_edit", "apply_patch"}:
        return True
    if normalized == "bash" and command and any(pattern.search(command) for pattern in MUTATING_SHELL_PATTERNS):
        return True
    return False



def _hook_adapter_gap_diagnostic(*, cwd: Path, tool_name: str = "", session_id: str = "",
                                 subject: dict[str, Any] | None = None,
                                 target_paths: list[str] | None = None,
                                 trigger_source: str = "hook",
                                 command_observed: str = "") -> dict[str, Any]:
    """Build a HOOK_ADAPTER_PAYLOAD_GAP diagnostic dict when the hook adapter fails to forward payload/target."""
    subject = subject or {}
    return {
        "severity": "warning",
        "code": "HOOK_ADAPTER_PAYLOAD_GAP",
        "message": "Hook adapter 未显式转发 payload / target，dispatcher 只能依赖 cwd fallback；请让 adapter 传入原始 payload 或等价 canonical context。",
        "source_refs": [
            "ldvh-base/workcases/workcase-0016-hook-adapter-payload-target-assurance.yaml",
            "specs/attachments/06.Att.15-环境Hook事件映射表.md",
            "code/hook_dispatch.py",
        ],
        "suggested_owner": "runtime-adapter",
        "cwd": str(cwd),
        "trigger_source": trigger_source,
        "session_id": session_id,
        "tool": tool_name,
        "payload_present": False,
        "target_paths": target_paths or subject.get("target_paths", []),
        "subject_source": subject.get("subject_source", "cwd-fallback"),
        "command_observed": command_observed[:200] if command_observed else "",
    }




def _read_plan_guard_result(cwd: Path, receipt: Optional[dict[str, Any]], *, trigger_source: str,
                            tool_name: str, command: str, action: str,
                            subject: dict[str, Any] | None = None,
                            message_file: str = "", session_id: str = "") -> Optional[dict[str, Any]]:
    """Check whether read_plan has been consumed; return a blocking dict if not, None if ok."""
    if _receipt_read_plan_consumed(receipt):
        return None
    required_paths = _required_read_plan_paths(receipt) if receipt else []
    subject = subject or {}
    return {
        "blocked": True,
        "cwd": str(cwd),
        "governed": True,
        "target_paths": subject.get("target_paths", []),
        "target_resolutions": subject.get("target_resolutions", []),
        "event": action,
        "operation_kind": "commit" if action == "git.commit-msg" else "tool",
        "read_write_kind": "write",
        "message_file": message_file,
        "session_id": session_id,
        "governed_subject": subject.get("governed_subject", ""),
        "governed_via": subject.get("governed_via", ""),
        "governed_project_id": subject.get("governed_project_id", ""),
        "governed_project_path": subject.get("governed_project_path", ""),
        "trigger_source": trigger_source,
        "tool": tool_name,
        "action": action,
        "reason": "管辖项目写入/提交前必须先消费 session-start receipt 的 P0/P1 read_plan，并记录 read_plan_consumed 证据。",
        "required_paths": required_paths,
        "next_action": "读取 required_paths 后运行 `python3 code/hook_dispatch.py run acknowledge-read-plan --cwd <cwd>`；支持 session_id 的 Hook 环境应传入同一 session_id。",
        "command_observed": command[:200] if command else "",
    }


def _commit_action_guard_result(cwd: Path, receipt: Optional[dict[str, Any]], *,
                                trigger_source: str, subject: dict[str, Any] | None = None,
                                message_file: str = "", session_id: str = "") -> Optional[dict[str, Any]]:
    if _receipt_commit_action_acknowledged(receipt, cwd):
        return None
    subject = subject or {}
    return {
        "blocked": True,
        "cwd": str(cwd),
        "governed": True,
        "target_paths": subject.get("target_paths", []),
        "target_resolutions": subject.get("target_resolutions", []),
        "event": "git.commit-msg",
        "operation_kind": "commit",
        "read_write_kind": "write",
        "message_file": message_file,
        "session_id": session_id,
        "governed_subject": subject.get("governed_subject", ""),
        "governed_via": subject.get("governed_via", ""),
        "governed_project_id": subject.get("governed_project_id", ""),
        "governed_project_path": subject.get("governed_project_path", ""),
        "trigger_source": trigger_source,
        "tool": "git.commit-msg",
        "action": "git.commit-msg",
        "reason": "管辖项目提交前必须先执行 ldvh-git-commit，并写入 commit_action_execution 凭证。",
        "required_execution_modes": ["skill_runtime_invoked", "manual_equivalent_execution"],
        "next_action": (
            "读取 skills/ldvh-git-commit/SKILL.md 并按 Workflow 执行后，运行 "
            "`python3 code/hook_dispatch.py run acknowledge-commit-action --cwd <repo-root> "
            "--execution-mode manual_equivalent_execution`。"
        ),
    }


def handle_pre_tool_use(cwd: Path, *, trigger_source: str = "rules", tool_name: str = "",
                        session_id: str = "", tool_command: str = "",
                        targets: list[Path] | None = None,
                        target_sources: list[str] | None = None) -> int:
    """PreToolUse / pre-tool-use handler.

    Check whether the current session has completed the session-start
    handshake before allowing Write/Edit tools.
    """
    mutating = _tool_requires_read_plan_consumed(tool_name, tool_command)
    explicit_targets = bool(targets)
    subject = resolve_governed_subject(cwd, targets or [], target_sources=target_sources)
    payload_gap_diagnostic = None
    if trigger_source == "hook" and not explicit_targets and subject.get("governed"):
        payload_gap_diagnostic = _hook_adapter_gap_diagnostic(
            cwd=cwd,
            tool_name=tool_name,
            session_id=session_id,
            subject=subject,
            trigger_source=trigger_source,
            command_observed=tool_command,
        )
    if mutating and not explicit_targets:
        blocked = {
            "blocked": True,
            "cwd": str(cwd),
            "governed": False,
            "event": "pre-tool-use",
            "operation_kind": "tool",
            "read_write_kind": "write",
            "target_paths": [],
            "target_resolutions": [],
            "governed_subject": "",
            "trigger_source": trigger_source,
            "tool": tool_name,
            "tool_name": tool_name,
            "tool_command": tool_command,
            "session_id": session_id,
            "action": "pre-tool-use",
            "blocked_reason": "unknown_target",
            "reason": "写类工具未提供可确定工作对象；必须由 Hook payload 或 Rules CLI 显式提供 target。",
            "next_action": "重新触发 pre-tool-use，并传入 --target <path>；Hook adapter 应从 tool_input 提取 file_path/path/workdir 等字段。",
            "command_observed": tool_command[:200] if tool_command else "",
        }
        if payload_gap_diagnostic is not None:
            blocked["diagnostics"] = [payload_gap_diagnostic]
            blocked["payload_present"] = False
            blocked["user_diagnostic_report"] = _build_user_diagnostic_report([payload_gap_diagnostic])
            blocked["next_action"] = (
                blocked.get("next_action", "")
                + " 同时请向用户报告：Hook adapter 未传递真实工作对象，"
                "写类工具的管辖判定和 read_plan 门禁可能无法作用在正确目标上。"
            )
        print(json.dumps(blocked, ensure_ascii=False))
        return 1

    if subject.get("blocked"):
        print(json.dumps({**subject, "trigger_source": trigger_source, "action": "pre-tool-use"}, ensure_ascii=False))
        return 1

    governed = bool(subject.get("governed"))
    if not governed:
        result = {"blocked": False, "reason": subject.get("message", "工作对象未命中管辖项目，no-op"),
                  **subject, "trigger_source": trigger_source, "payload_present": explicit_targets}
        if payload_gap_diagnostic is not None:
            result["diagnostics"] = [payload_gap_diagnostic]
        print(json.dumps(result, ensure_ascii=False))
        return 0

    # In governed projects, keep the hook non-blocking while making the receipt
    # state queryable. Codex may not surface SessionStart stdout in the thread,
    # so PreToolUse can create the same receipt when a session_id is present.
    result = {
        **subject,
        "event": "pre-tool-use",
        "operation_kind": "tool",
        "read_write_kind": "write" if mutating else "read",
        "tool_name": tool_name,
        "tool_command": tool_command,
        "session_id": session_id,
        "blocked": False,
        "governed": True,
        "trigger_source": trigger_source,
        "payload_present": explicit_targets,
    }
    receipt = _read_session_receipt(session_id) if session_id else _latest_session_receipt(cwd)
    if receipt:
        receipt_result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
        result["session_receipt"] = "found"
        if isinstance(receipt_result, dict):
            result["receipt"] = receipt_result.get("receipt", "unknown")
            result["receipt_event"] = receipt.get("event", "")
        if _receipt_read_plan_consumed(receipt):
            result["read_plan_consumed"] = "acknowledged"
    elif session_id:
        session_result = _build_session_start_result(cwd, trigger_source=trigger_source, targets=targets)
        _write_session_receipt(session_id, "pre-tool-use-implicit-session-start", session_result)
        receipt = _read_session_receipt(session_id)
        result["session_receipt"] = "created_by_pre_tool_use"
        result["receipt"] = session_result.get("receipt", "unknown")
        result["action_policy"] = "read_plan_ack_required_before_write"
    else:
        result["session_receipt"] = "unavailable"
        result["warning"] = "管辖项目中，hook payload 未提供 session_id；请确认本会话已完成 session-start。"
    if tool_name:
        result["tool"] = tool_name
    if tool_command:
        result["command_observed"] = tool_command[:200]
    if payload_gap_diagnostic is not None:
        result["diagnostics"] = [payload_gap_diagnostic]
        result["user_diagnostic_report"] = _build_user_diagnostic_report([payload_gap_diagnostic])
        result.setdefault("next_action",
            "请向用户报告：Hook adapter 未传递真实工作对象，当前管辖判定基于 cwd fallback。"
        )
    if mutating:
        blocked = _read_plan_guard_result(
            cwd,
            receipt,
            trigger_source=trigger_source,
            tool_name=tool_name,
            command=tool_command,
            action="pre-tool-use",
            subject=subject,
            session_id=session_id,
        )
        if blocked:
            print(json.dumps(blocked, ensure_ascii=False))
            return 1
    if receipt and session_id:
        _mark_pre_tool_use_receipt(session_id, result)
    result["skill_plan"] = _build_skill_plan("pre-tool-use", tool=tool_name,
                                              command=tool_command)
    if result["skill_plan"]:
        result["skill_plan_hint"] = (
            "对于列出的每个 skill_id，请读取 skills/<id>/SKILL.md 并按其中的 Workflow 执行。"
        )
        # Persist to session receipt so acknowledge-read-plan can surface it
        if receipt and session_id:
            receipt.setdefault("skill_plan", [])
            for sid in result["skill_plan"]:
                if sid not in receipt["skill_plan"]:
                    receipt["skill_plan"].append(sid)
            _write_session_receipt(session_id, receipt.get("event", "pre-tool-use"), receipt)
    print(json.dumps(result, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# registry-based execution (git.commit-msg and future events)
# ---------------------------------------------------------------------------


def run_event(event: str, registry_path: Path, context: dict[str, str],
              dry_run: bool = False) -> int:
    registry = load_registry(registry_path)
    matched = hooks_for_event(registry, event)
    if not matched:
        print(f"未找到 active Hook event: {event}", file=sys.stderr)
        return 2

    exit_code = 0
    for hook in matched:
        hook_id = hook.get("id", "<unknown>")
        command = render_command(hook.get("command"), context)
        print(f"LDVH Hook {hook_id}: {' '.join(command)}")
        if dry_run:
            continue
        result = subprocess.run(command, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            exit_code = result.returncode
            if hook.get("blocking", True):
                break
    return exit_code


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_stdin() -> Optional[dict[str, Any]]:
    """Try to read a JSON object from stdin (Hook path).  Returns None when
    stdin is not a pipe / empty / unparseable (Rules path)."""
    if sys.stdin.isatty():
        return None
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return None
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None


def _stdin_event(payload: dict[str, Any]) -> str:
    """Return the hook event name from known Codex/AI hook payload shapes."""
    for key in ("event", "hook_event", "hookEvent", "hook_event_name", "hookEventName", "event_name", "eventName"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _stdin_tool_name(payload: dict[str, Any]) -> str:
    """Return the tool name from known hook payload shapes when present."""
    for key in ("tool_name", "toolName", "tool"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _stdin_session_id(payload: dict[str, Any]) -> str:
    """Return the Codex session id from hook payloads when present."""
    for key in ("session_id", "sessionId"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _git_repo_root(cwd: Path) -> Path:
    root = _git_text(cwd, ["rev-parse", "--show-toplevel"])
    return Path(root) if root else cwd


def _git_staged_paths(cwd: Path) -> list[Path]:
    output = _git_text(cwd, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    repo_root = _git_repo_root(cwd)
    paths = [repo_root]
    for line in output.splitlines():
        raw = line.strip()
        if raw:
            paths.append(repo_root / raw)
    return paths


def _git_staged_relative_paths(cwd: Path) -> list[str]:
    output = _git_text(cwd, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [line.strip() for line in output.splitlines() if line.strip()]


def _commit_action_fields() -> dict[str, Any]:
    return {
        "action_member": GIT_COMMIT_ACTION_SPEC,
        "action_policy": "governed_project_commit_action_required",
        "skill_plan": [GIT_COMMIT_SKILL_ID],
        "skill_plan_hint": (
            "读取 skills/ldvh-git-commit/SKILL.md，并按其中 Workflow 执行；"
            "若运行时没有真实 Skill 调用机制，必须声明 manual_equivalent_execution。"
        ),
        "next_action": (
            "先按管辖项目判定结果进入 specs/31 Git 提交行动编排和 ldvh-git-commit Skill，"
            "再检查 staged files、验证命令、commit body 和 Human Gate。"
        ),
    }


def handle_commit_preflight(cwd: Path, *, trigger_source: str = "rules",
                            targets: list[Path] | None = None,
                            session_id: str = "") -> int:
    commit_targets = targets if targets else _git_staged_paths(cwd)
    subject = resolve_governed_subject(cwd, commit_targets)
    result = {
        **subject,
        "event": "commit-preflight",
        "operation_kind": "commit",
        "read_write_kind": "read",
        "trigger_source": trigger_source,
        "session_id": session_id,
        "repo_root": str(_git_repo_root(cwd)),
        "staged_paths": _git_staged_relative_paths(cwd),
    }
    if subject.get("blocked"):
        result.update(_commit_action_fields())
        print(json.dumps(result, ensure_ascii=False))
        return 1
    if not subject.get("governed"):
        result["action_policy"] = "no_op_non_governed"
        print(json.dumps(result, ensure_ascii=False))
        return 0

    receipt = _read_session_receipt(session_id) if session_id else _latest_session_receipt(cwd)
    result.update(_commit_action_fields())
    result["session_receipt"] = "found" if receipt else "missing"
    result["read_plan_consumed"] = "acknowledged" if _receipt_read_plan_consumed(receipt) else "missing"
    result["commit_action_execution"] = (
        "acknowledged" if _receipt_commit_action_acknowledged(receipt, cwd) else "missing"
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def _guard_git_commit_msg(cwd: Path, *, trigger_source: str,
                          targets: list[Path] | None = None,
                          message_file: str = "", session_id: str = "") -> Optional[dict[str, Any]]:
    commit_targets = targets if targets else _git_staged_paths(cwd)
    subject = resolve_governed_subject(cwd, commit_targets)
    if subject.get("blocked"):
        return {**subject, **_commit_action_fields(), "trigger_source": trigger_source, "action": "git.commit-msg"}
    if not subject.get("governed"):
        return None
    receipt = _latest_session_receipt(cwd)
    blocked = _read_plan_guard_result(
        cwd,
        receipt,
        trigger_source=trigger_source,
        tool_name="git.commit-msg",
        command="git commit",
        action="git.commit-msg",
        subject=subject,
        message_file=message_file,
        session_id=session_id,
    )
    if blocked:
        blocked.update(_commit_action_fields())
        return blocked
    blocked = _commit_action_guard_result(
        cwd,
        receipt,
        trigger_source=trigger_source,
        subject=subject,
        message_file=message_file,
        session_id=session_id,
    )
    if blocked:
        blocked.update(_commit_action_fields())
    return blocked


def main(argv: Optional[list[str]] = None) -> int:
    # --- Hook path: stdin JSON ------------------------------------------------
    stdin_payload = _parse_stdin()
    cli_args = list(sys.argv[1:] if argv is None else argv)
    cli_has_explicit_event = len(cli_args) >= 2 and cli_args[0] == "run"
    # Codex command hooks pass JSON on stdin. Plugin-bundled hooks also carry the
    # event in argv (`run pre-tool-use`). If stdin has no event field, keep the
    # explicit CLI event instead of treating it as an unknown empty event.
    if stdin_payload is not None and not cli_has_explicit_event:
        event = _stdin_event(stdin_payload)
        cwd_raw = stdin_payload.get("cwd", os.getcwd())
        cwd = Path(cwd_raw)
        trigger_source = stdin_payload.get("trigger_source", "hook")
        session_id = _stdin_session_id(stdin_payload)
        targets, target_sources = _extract_payload_targets(stdin_payload)

        # Normalize event name: both "SessionStart" (Hook) and "session-start" (CLI) accepted
        normalized = event.replace("_", "-").lower().lstrip("-")

        if normalized in ("session-start", "sessionstart"):
            return handle_session_start(cwd, trigger_source=trigger_source, session_id=session_id, targets=targets)
        if normalized in ("acknowledge-read-plan", "acknowledgereadplan"):
            action_hint = stdin_payload.get("action_hint", "")
            return handle_acknowledge_read_plan(
                cwd,
                trigger_source=trigger_source,
                session_id=session_id,
                action_hint=action_hint if isinstance(action_hint, str) else "",
                targets=targets,
            )
        if normalized in ("acknowledge-commit-action", "acknowledgecommitaction"):
            execution_mode = stdin_payload.get("execution_mode", "manual_equivalent_execution")
            return handle_acknowledge_commit_action(
                cwd,
                trigger_source=trigger_source,
                session_id=session_id,
                execution_mode=execution_mode if isinstance(execution_mode, str) else "manual_equivalent_execution",
            )
        if normalized in ("pre-tool-use", "pretooluse"):
            tool = _stdin_tool_name(stdin_payload)
            command = _stdin_tool_command(stdin_payload)
            return handle_pre_tool_use(
                cwd,
                trigger_source=trigger_source,
                tool_name=tool,
                session_id=session_id,
                tool_command=command,
                targets=targets,
                target_sources=target_sources,
            )
        if normalized in ("git-commit-msg", "git.commit-msg"):
            message_file = stdin_payload.get("message_file", "")
            blocked = _guard_git_commit_msg(
                cwd,
                trigger_source=trigger_source,
                targets=targets,
                message_file=message_file if isinstance(message_file, str) else "",
                session_id=session_id,
            )
            if blocked:
                print(json.dumps(blocked, ensure_ascii=False))
                return 1
            context: dict[str, str] = {"cwd": str(cwd), "repo_root": str(_git_repo_root(cwd))}
            if stdin_payload.get("message_file"):
                context["message_file"] = stdin_payload["message_file"]
            return run_event("git.commit-msg", DEFAULT_REGISTRY, context)

        # Unknown event — try registry lookup
        context = {"cwd": str(cwd)}
        for key, val in stdin_payload.items():
            if isinstance(val, str) and key not in ("event",):
                context[key] = val
        return run_event(event, DEFAULT_REGISTRY, context)

    # --- Rules path: CLI subcommands ------------------------------------------
    parser = argparse.ArgumentParser(
        description="LDVH lifecycle protocol dispatcher — Hook path (stdin) or Rules path (CLI)."
    )
    subparsers = parser.add_subparsers(dest="command")

    # run <event>
    run_parser = subparsers.add_parser("run", help="Execute a lifecycle protocol event.")
    run_parser.add_argument("event", help="Event: session-start | acknowledge-read-plan | acknowledge-commit-action | pre-tool-use | commit-preflight | git.commit-msg")
    run_parser.add_argument("--cwd", type=Path, default=Path(os.getcwd()),
                            help="Current working directory for the event.")
    run_parser.add_argument("--trigger-source", type=str, choices=["hook", "rules"],
                            default="rules",
                            help="Trigger source: hook (environment) or rules (AI self-trigger).")
    run_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY,
                            help="Hook registry YAML path.")
    run_parser.add_argument("--message-file", type=Path, default=None,
                            help="Commit message file (git.commit-msg only).")
    run_parser.add_argument("--target", type=Path, action="append", default=[],
                            help="Operation target path. May be passed multiple times.")
    run_parser.add_argument("--tool-name", type=str, default="",
                            help="Tool name being invoked (pre-tool-use only).")
    run_parser.add_argument("--tool-command", type=str, default="",
                            help="Tool command or payload summary (pre-tool-use only).")
    run_parser.add_argument("--session-id", type=str, default="",
                            help="Session id for receipt lookup or acknowledgement.")
    run_parser.add_argument("--action-hint", type=str, default="",
                            help="Action hint for acknowledge-read-plan: fix | create | review | modify | discuss | unknown.")
    run_parser.add_argument("--execution-mode", type=str, default="manual_equivalent_execution",
                            choices=["skill_runtime_invoked", "manual_equivalent_execution"],
                            help="Execution mode for acknowledge-commit-action.")
    run_parser.add_argument("--dry-run", action="store_true",
                            help="Print commands without executing (git.commit-msg only).")

    args = parser.parse_args(cli_args)

    if args.command == "run":
        event = args.event
        cwd = args.cwd.resolve()
        trigger_source = args.trigger_source
        if stdin_payload is not None and cli_has_explicit_event and "--cwd" not in cli_args:
            payload_cwd = stdin_payload.get("cwd")
            if isinstance(payload_cwd, str) and payload_cwd.strip():
                cwd = Path(payload_cwd).resolve()
        targets = [_resolve_path(target, cwd) for target in args.target]
        target_sources = ["cli.target"] * len(targets)
        if stdin_payload is not None and cli_has_explicit_event:
            payload_targets, payload_sources = _extract_payload_targets(stdin_payload)
            if not targets:
                targets = [_resolve_path(target, cwd) for target in payload_targets]
                target_sources = payload_sources
            if not args.tool_name:
                args.tool_name = _stdin_tool_name(stdin_payload)
            if not args.tool_command:
                args.tool_command = _stdin_tool_command(stdin_payload)
            if not args.session_id:
                args.session_id = _stdin_session_id(stdin_payload)

        try:
            # --- built-in lifecycle handlers ---
            if event in ("session-start", "SessionStart"):
                return handle_session_start(cwd, trigger_source=trigger_source, session_id=args.session_id, targets=targets)

            if event in ("acknowledge-read-plan", "AcknowledgeReadPlan"):
                return handle_acknowledge_read_plan(
                    cwd,
                    trigger_source=trigger_source,
                    session_id=args.session_id,
                    action_hint=args.action_hint,
                    targets=targets,
                )

            if event in ("acknowledge-commit-action", "AcknowledgeCommitAction"):
                return handle_acknowledge_commit_action(
                    cwd,
                    trigger_source=trigger_source,
                    session_id=args.session_id,
                    execution_mode=args.execution_mode,
                )

            if event in ("pre-tool-use", "PreToolUse"):
                return handle_pre_tool_use(
                    cwd,
                    trigger_source=trigger_source,
                    tool_name=args.tool_name,
                    session_id=args.session_id,
                    tool_command=args.tool_command,
                    targets=targets,
                    target_sources=target_sources,
                )

            if event in ("commit-preflight", "CommitPreflight"):
                return handle_commit_preflight(
                    cwd,
                    trigger_source=trigger_source,
                    targets=targets,
                    session_id=args.session_id,
                )

            if event == "git.commit-msg":
                blocked = _guard_git_commit_msg(
                    cwd,
                    trigger_source=trigger_source,
                    targets=targets,
                    message_file=str(args.message_file) if args.message_file is not None else "",
                    session_id=args.session_id,
                )
                if blocked:
                    print(json.dumps(blocked, ensure_ascii=False))
                    return 1
                context: dict[str, str] = {"cwd": str(cwd), "repo_root": str(_git_repo_root(cwd))}
                if args.message_file is not None:
                    context["message_file"] = str(args.message_file)
                return run_event(event, args.registry, context, dry_run=args.dry_run)

            # --- fallback: registry lookup for unknown events ---
            context: dict[str, str] = {}
            return run_event(event, args.registry, context, dry_run=args.dry_run)

        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    return 2


if __name__ == "__main__":
    sys.exit(main())
