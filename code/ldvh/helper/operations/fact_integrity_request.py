"""Parse inputs for the source-defined fact-integrity check operation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS: tuple[str, ...] = ("work_object_locators",)
OPTIONAL_INPUTS: tuple[str, ...] = ("arguments.workspace_root",)

_ARGUMENT_FIELDS = frozenset({"workspace_root"})


@dataclass(frozen=True, slots=True)
class FactIntegrityRequest:
    """Validated public inputs without reading rules, governance, or Git."""

    locator: str
    base: Path
    workspace_root: Path | None


@dataclass(frozen=True, slots=True)
class FactIntegrityRequestParseResult:
    request: FactIntegrityRequest | None
    problems: tuple[str, ...]


def parse_fact_integrity_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> FactIntegrityRequestParseResult:
    problems: list[str] = []

    if not context.cwd.is_absolute():
        problems.append("Helper 进程实际 cwd 必须是绝对路径")

    if len(request.work_object_locators) != 1:
        problems.append("work_object_locators 必须恰有一个目标路径 string")
        locator = ""
    else:
        raw_locator = request.work_object_locators[0]
        if not isinstance(raw_locator, str) or not raw_locator.strip():
            problems.append("work_object_locators[0] 必须是非空路径 string")
            locator = ""
        else:
            locator = raw_locator

    unknown = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    for field in unknown:
        problems.append(f"arguments 包含未知字段: {field}")

    raw_workspace = request.arguments.get("workspace_root")
    workspace_root: Path | None = None
    if raw_workspace is not None:
        if not isinstance(raw_workspace, str) or not raw_workspace.strip():
            problems.append("arguments.workspace_root 出现时必须为非空绝对路径 string")
        else:
            candidate = Path(raw_workspace)
            if not candidate.is_absolute():
                problems.append("arguments.workspace_root 出现时必须为非空绝对路径 string")
            else:
                workspace_root = candidate

    if problems:
        return FactIntegrityRequestParseResult(None, tuple(problems))
    return FactIntegrityRequestParseResult(FactIntegrityRequest(locator, context.cwd, workspace_root), ())


__all__ = [
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "FactIntegrityRequest",
    "FactIntegrityRequestParseResult",
    "parse_fact_integrity_request",
]
