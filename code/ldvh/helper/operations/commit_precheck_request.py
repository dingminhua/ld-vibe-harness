"""Parse inputs for the source-defined Git commit precheck operation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS: tuple[str, ...] = (
    "work_object_locators",
    "arguments.message",
)
OPTIONAL_INPUTS: tuple[str, ...] = ("arguments.workspace_root",)

_ARGUMENT_FIELDS = frozenset({"message", "workspace_root"})


@dataclass(frozen=True, slots=True)
class CommitPrecheckRequest:
    """Validated public inputs without reading rules, governance, or Git."""

    locator: str
    base: Path
    workspace_root: Path | None
    message: str


@dataclass(frozen=True, slots=True)
class CommitPrecheckRequestParseResult:
    request: CommitPrecheckRequest | None
    problems: tuple[str, ...]


def parse_commit_precheck_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> CommitPrecheckRequestParseResult:
    problems: list[str] = []

    if not context.cwd.is_absolute():
        problems.append("Helper 进程实际 cwd 必须是绝对路径")

    if len(request.work_object_locators) != 1:
        problems.append("work_object_locators 必须恰有一个目标路径 string")
        locator = ""
    else:
        raw_locator = request.work_object_locators[0]
        if not isinstance(raw_locator, str) or not raw_locator:
            problems.append("work_object_locators[0] 必须是非空路径 string")
            locator = ""
        else:
            locator = raw_locator

    unknown_arguments = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown_arguments:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown_arguments)}")

    raw_message = request.arguments.get("message")
    if "message" not in request.arguments or not isinstance(raw_message, str):
        problems.append("arguments.message 必须出现且为 string")
        message = ""
    else:
        message = raw_message

    workspace_root: Path | None = None
    if "workspace_root" in request.arguments:
        raw_workspace_root = request.arguments["workspace_root"]
        if not isinstance(raw_workspace_root, str) or not raw_workspace_root:
            problems.append("arguments.workspace_root 出现时必须是非空绝对路径 string")
        else:
            candidate = Path(raw_workspace_root)
            if not candidate.is_absolute():
                problems.append("arguments.workspace_root 出现时必须是非空绝对路径 string")
            else:
                workspace_root = candidate

    if request.observed_context:
        problems.append("observed_context 必须为空 object")
    if request.authorization_reference:
        problems.append("authorization_reference 必须为空 array")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 必须省略或为 null")

    if problems:
        return CommitPrecheckRequestParseResult(None, tuple(problems))
    return CommitPrecheckRequestParseResult(
        CommitPrecheckRequest(
            locator=locator,
            base=context.cwd,
            workspace_root=workspace_root,
            message=message,
        ),
        (),
    )


__all__ = [
    "CommitPrecheckRequest",
    "CommitPrecheckRequestParseResult",
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "parse_commit_precheck_request",
]
