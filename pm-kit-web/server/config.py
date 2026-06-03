import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from fastapi import HTTPException

PRODUCT_CONFIG_ENV = "PM_KIT_PRODUCT_YAML"
PRODUCT_CONFIG_DEFAULT = "product.yaml"

DOC_ROLE_MAP = {
    0: "管理目标",
    1: "历史追踪",
    2: "知识沉淀",
    3: "输入池",
    6: "AI协作",
    7: "文档治理",
    8: "管理对象",
}

ENTRY_TYPES = {"TODO", "FOUND", "DECISION", "QUESTION"}

PRIORITY_MAP = {
    "\U0001f534": "P0",
    "\U0001f7e1": "P1",
    "\U0001f7e2": "P2",
}

STATUS_DONE_MARKERS = {"\u2705", "\u2714\ufe0f"}
STATUS_CANCEL_MARKERS = {"\u274c", "\u2716\ufe0f"}
STATUS_PROGRESS_MARKERS = {"\U0001f504", "\U0001f527"}

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

STATUS_COMPAT_MAP = {
    "待执行": "Planned",
    "待办": "Planned",
    "进行中": "Executing",
    "阻塞": "Blocked",
    "待验证": "Review Needed",
    "已完成": "Closed",
    "已取消": "Cancelled",
    "已归档": "Closed",
}

NORMALIZED_TO_LEGACY_STATUS = {
    "Ready for Plan": "待办",
    "Planned": "待办",
    "Executing": "进行中",
    "Blocked": "阻塞",
    "Decision Needed": "阻塞",
    "Review Needed": "待验证",
    "Closed": "已完成",
    "Cancelled": "已取消",
}

VALID_TASK_STATUSES = set(NORMALIZED_TO_LEGACY_STATUS) | set(STATUS_COMPAT_MAP)

TASK_STATUS_TRANSITIONS = {
    "Ready for Plan": {"Planned", "Cancelled"},
    "Planned": {"Executing", "Blocked", "Decision Needed", "Cancelled"},
    "Executing": {"Blocked", "Decision Needed", "Review Needed", "Cancelled"},
    "Blocked": {"Executing", "Decision Needed", "Review Needed", "Cancelled"},
    "Decision Needed": {"Planned", "Executing", "Blocked", "Review Needed", "Cancelled"},
    "Review Needed": {"Executing", "Decision Needed", "Closed", "Cancelled"},
    "Closed": set(),
    "Cancelled": {"Ready for Plan", "Planned"},
}

CLOSING_STATUSES = {"Closed"}
CLOSING_REQUIRED_FIELDS = {
    "completion_summary": "完成摘要",
    "validation_result": "验证结果",
    "closure_evidence": "关闭证据",
    "acceptance_result": "验收结果",
}

WAITING_DECISION_STATUSES = {"Decision Needed"}

REASON_REQUIRED_TRANSITIONS = {
    ("Executing", "Blocked"): "阻塞原因",
    ("Executing", "Cancelled"): "取消原因",
    ("Planned", "Cancelled"): "取消原因",
    ("Review Needed", "Decision Needed"): "决策问题",
    ("Review Needed", "Executing"): "回退原因",
    ("Blocked", "Cancelled"): "取消原因",
    ("Decision Needed", "Cancelled"): "取消原因",
}

HUMAN_GATE_TRANSITIONS = {
    ("Review Needed", "Closed"): "验收确认与关闭授权",
    ("Decision Needed", "Planned"): "决策记录",
    ("Decision Needed", "Executing"): "决策记录",
}

_audit_log: list = []

_cache: dict = {}
_CACHE_TTL = 5.0

_file_mtimes: dict = {}

_config: Optional[dict] = None
_config_error: Optional[str] = None


def _cache_get(key: str):
    if _check_file_changes():
        _cache_invalidate()
        return None
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data):
    _cache[key] = {"ts": time.time(), "data": data}


def _cache_invalidate(key: str = ""):
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()


def _check_file_changes() -> bool:
    changed = False
    for key, proj in _get_projects().items():
        proj_docs = proj["path"] / proj["docs"]
        if proj_docs.exists():
            for f in proj_docs.iterdir():
                if f.is_file() and f.name.endswith(".md"):
                    try:
                        mtime = f.stat().st_mtime
                        old_mtime = _file_mtimes.get(str(f), 0)
                        if mtime > old_mtime:
                            _file_mtimes[str(f)] = mtime
                            changed = True
                    except:
                        pass
        task_base = proj["path"] / proj.get("task_base", "task-base")
        if task_base.exists():
            for f in task_base.rglob("*.yaml"):
                try:
                    mtime = f.stat().st_mtime
                    old_mtime = _file_mtimes.get(str(f), 0)
                    if mtime > old_mtime:
                        _file_mtimes[str(f)] = mtime
                        changed = True
                except:
                    pass
    return changed


def _invalidate_cache_on_file_change():
    if _check_file_changes():
        _cache_invalidate()


def _log_action(action: str, target: str, detail: str = ""):
    _audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "target": target,
        "detail": detail,
    })
    if len(_audit_log) > 500:
        _audit_log.pop(0)
    _cache_invalidate()


def _resolve_product_config_path() -> Path:
    env_path = os.environ.get(PRODUCT_CONFIG_ENV, "").strip()
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    cwd_path = Path.cwd() / PRODUCT_CONFIG_DEFAULT
    if cwd_path.exists():
        return cwd_path
    script_path = Path(__file__).resolve().parents[2] / PRODUCT_CONFIG_DEFAULT
    if script_path.exists():
        return script_path
    # 额外检查：从脚本路径向上查找
    current_dir = Path(__file__).resolve().parent
    while current_dir.parent != current_dir:
        candidate = current_dir / PRODUCT_CONFIG_DEFAULT
        if candidate.exists():
            return candidate
        current_dir = current_dir.parent
    raise FileNotFoundError(
        f"product.yaml not found. Set {PRODUCT_CONFIG_ENV} env var or place product.yaml in CWD or project root."
    )


def _load_product_config() -> dict:
    config_path = _resolve_product_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    product = data.get("product", {})
    product_root = (config_path.parent / product.get("root", ".")).resolve()
    projects = {}
    for proj in data.get("projects", []):
        proj_path = (config_path.parent / proj["path"]).resolve()
        projects[proj["id"]] = {
            "name": proj.get("name", proj["id"]),
            "path": proj_path,
            "docs": proj.get("docs", "docs"),
            "task_base": proj.get("task_base", "task-base"),
        }
    return {
        "product": {
            "id": product.get("id", ""),
            "name": product.get("name", ""),
            "description": product.get("description", ""),
            "root": product_root,
        },
        "projects": projects,
        "config_path": config_path,
    }


def _get_config() -> dict:
    global _config, _config_error
    if _config is None:
        try:
            _config = _load_product_config()
            _config_error = None
        except FileNotFoundError as e:
            _config_error = str(e)
            _config = {
                "product": {"id": "", "name": "", "description": "", "root": Path.cwd()},
                "projects": {},
                "config_path": None,
            }
    return _config


def _get_config_error() -> Optional[str]:
    _get_config()
    return _config_error


def _get_projects() -> dict:
    return _get_config()["projects"]


def _get_product() -> dict:
    return _get_config()["product"]


def normalize_task_status(status: str) -> str:
    status = (status or "").strip()
    return STATUS_COMPAT_MAP.get(status, status or "Ready for Plan")


def storage_task_status(status: str) -> str:
    normalized = normalize_task_status(status)
    return NORMALIZED_TO_LEGACY_STATUS.get(normalized, status)


def validate_task_status_value(status: str) -> str:
    normalized = normalize_task_status(status)
    if normalized not in VALID_TASK_STATUSES:
        allowed = sorted(set(NORMALIZED_TO_LEGACY_STATUS) | set(STATUS_COMPAT_MAP))
        raise HTTPException(status_code=400, detail=f"非法状态：{status}。允许值：{', '.join(allowed)}")
    return normalized


def _has_value(value: str) -> bool:
    text = str(value or "").strip()
    return bool(text and text != "未写入事实源")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _read_yaml_file(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _invalidate_cache():
    _cache_invalidate()
