"""Process entry point for the LDVH Helper CLI machine interface."""

from __future__ import annotations

import json
import sys
from typing import Any

from ldvh.helper.responses import common_response, diagnostic, gap
from ldvh.helper.service import handle_request, invalid_request_result


def _emit(response: dict[str, Any]) -> None:
    payload = json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n"
    sys.stdout.buffer.write(payload.encode("utf-8"))


def _command(arguments: list[str]) -> tuple[str, str | None] | None:
    if arguments == ["capabilities"]:
        return "capabilities", None
    if len(arguments) == 2 and arguments[0] in {"capabilities", "call"}:
        return arguments[0], arguments[1]
    return None


def main() -> int:
    arguments = sys.argv[1:]
    command = _command(arguments)
    if command is None:
        if len(arguments) > 2 and arguments[0] in {"capabilities", "call"} and arguments[1]:
            result = invalid_request_result(
                arguments[0],  # type: ignore[arg-type]
                arguments[1],
                ("命令位置包含公开入口未定义的额外参数",),
            )
            _emit(result.response)
            return result.exit_code
        sys.stderr.write("usage: ldvh capabilities [operation_key] | ldvh call <operation_key>\n")
        return 2
    request_kind, operation_key = command
    try:
        try:
            raw_input = sys.stdin.buffer.read().decode("utf-8")
        except UnicodeDecodeError:
            result = invalid_request_result(request_kind, operation_key, ("标准输入必须是 UTF-8",))
        else:
            result = handle_request(request_kind, operation_key, raw_input)
    except Exception as exc:  # last boundary: still form the defined machine response
        result = common_response(
            request_kind=request_kind,  # type: ignore[arg-type]
            operation_key=operation_key,
            outcome="error",
            summary="Helper 实现发生未预期错误",
            not_completed_scope=[] if operation_key is None else [operation_key],
            gaps=[gap("实现异常使 Helper 无法形成所请求的可信结果")],
            diagnostics=[diagnostic("Helper 服务边界捕获未预期异常", exception_type=type(exc).__name__)],
        )
    _emit(result.response)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
