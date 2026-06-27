"""Read-only file-type to Code command suggestions.

This module is a small navigation aid derived from 04.Att.02 and 04.Att.07.
It does not authorize writes and must not become an independent rule source.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

SOURCE_REFS = [
    "specs/attachments/04.Att.02-Code命令入口表.md",
    "specs/attachments/04.Att.07-受控写入前检查矩阵.md",
]

NO_AUTHORIZED_COMMAND_REASON = "04.Att.02 暂未授权该文件类型的建议命令。"

FILE_COMMAND_MAP: dict[str, dict[str, Any]] = {
    "spec": {
        "before_change": [
            {
                "command": "python3 code/specs_validate.py preflight --target-path <path>",
                "purpose": "写入前只读检查",
                "source_refs": SOURCE_REFS,
            }
        ],
        "after_change": [
            {
                "command": "python3 code/specs_validate.py v2-check --fail-on-diagnostics",
                "purpose": "修改后验证",
                "source_refs": SOURCE_REFS,
            }
        ],
        "reason": "",
        "source_refs": SOURCE_REFS,
    },
    "workcase": {
        "before_change": [],
        "after_change": [],
        "reason": NO_AUTHORIZED_COMMAND_REASON,
        "source_refs": SOURCE_REFS,
    },
    "spark": {
        "before_change": [],
        "after_change": [],
        "reason": NO_AUTHORIZED_COMMAND_REASON,
        "source_refs": SOURCE_REFS,
    },
    "python": {
        "before_change": [],
        "after_change": [],
        "reason": NO_AUTHORIZED_COMMAND_REASON,
        "source_refs": SOURCE_REFS,
    },
    "web": {
        "before_change": [],
        "after_change": [],
        "reason": NO_AUTHORIZED_COMMAND_REASON,
        "source_refs": SOURCE_REFS,
    },
}


def classify_file_type(path: str | Path) -> str:
    """Classify a repository path by directory structure first."""
    normalized = Path(path).as_posix().lstrip("./")
    if normalized.startswith("specs/"):
        return "spec"
    if normalized.startswith("ldvh-base/workcases/"):
        return "workcase"
    if normalized.startswith("ldvh-base/sparks/"):
        return "spark"
    if normalized.startswith("code/"):
        return "python"
    if normalized.startswith("web/"):
        return "web"
    return "unknown"


def command_suggestions_for_path(path: str | Path) -> dict[str, Any]:
    """Return a copy of command suggestions for *path*'s file type."""
    file_type = classify_file_type(path)
    entry = FILE_COMMAND_MAP.get(file_type)
    if entry is None:
        return {
            "file_type": file_type,
            "before_change": [],
            "after_change": [],
            "reason": NO_AUTHORIZED_COMMAND_REASON,
            "source_refs": SOURCE_REFS,
        }
    return {
        "file_type": file_type,
        "before_change": list(entry["before_change"]),
        "after_change": list(entry["after_change"]),
        "reason": entry["reason"],
        "source_refs": list(entry["source_refs"]),
    }
