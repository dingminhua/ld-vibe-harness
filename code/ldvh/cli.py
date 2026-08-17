"""Process entry point for the LDVH Helper CLI machine interface."""

from __future__ import annotations

import json
import os
import select
import sys
from pathlib import Path
from typing import Any

# Allow `python code/ldvh/cli.py ...` to resolve the `ldvh` package without the
# project launcher. The launcher already puts `code/` on sys.path; this only helps
# the direct-invocation path that would otherwise raise ModuleNotFoundError.
_CODE_ROOT = str(Path(__file__).resolve().parent.parent)
if _CODE_ROOT not in sys.path:
    sys.path.insert(0, _CODE_ROOT)

from ldvh.cli_projection import (  # noqa: E402
    build_example_projection,
    parse_cli_arguments,
    project_response_fields,
    read_request_file,
)
from ldvh.helper.responses import common_response, diagnostic, gap  # noqa: E402
from ldvh.helper.service import handle_request, invalid_request_result  # noqa: E402


def _emit(response: dict[str, Any]) -> None:
    payload = json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n"
    sys.stdout.buffer.write(payload.encode("utf-8"))


def _read_request_input() -> str:
    """Read the ordinary stdin request body with the pre-existing compatibility path."""

    stdin_buffer = getattr(sys.stdin, "buffer", None)
    if stdin_buffer is None:
        return ""
    try:
        readable, _, _ = select.select([stdin_buffer], [], [], 0.0)
    except (OSError, ValueError):
        return stdin_buffer.read().decode("utf-8")
    if not readable:
        return ""
    return stdin_buffer.read().decode("utf-8")


def _alternate_input_conflicts() -> bool:
    """Reject redirected stdin unless it is observably closed and empty, without waiting."""

    stdin_buffer = getattr(sys.stdin, "buffer", None)
    if stdin_buffer is None or sys.stdin.isatty():
        return False
    try:
        readable, _, _ = select.select([stdin_buffer], [], [], 0.0)
    except (OSError, ValueError):
        try:
            descriptor = stdin_buffer.fileno()
            was_blocking = os.get_blocking(descriptor)
            os.set_blocking(descriptor, False)
            try:
                raw = os.read(descriptor, 1)
            except BlockingIOError:
                return True
            finally:
                os.set_blocking(descriptor, was_blocking)
        except (AttributeError, OSError, ValueError):
            return True
        return bool(raw)
    if not readable:
        # A non-tty pipe with a live writer may receive bytes later.  Treat that
        # indeterminate second source as a conflict instead of waiting for EOF.
        return True
    raw = stdin_buffer.read(1)
    return raw is None or bool(raw)


def main() -> int:
    parsed, command_problems, show_usage = parse_cli_arguments(sys.argv[1:])
    if show_usage or parsed is None:
        sys.stderr.write(
            "usage: ldvh capabilities [operation_key] [--request PATH] [--fields PATHS] | "
            "ldvh capabilities <operation_key> --example | "
            "ldvh call <operation_key> [--request PATH] [--fields PATHS]\n"
        )
        return 2
    request_kind = parsed.request_kind
    operation_key = parsed.operation_key
    if command_problems:
        result = invalid_request_result(request_kind, operation_key, command_problems)
        _emit(result.response)
        return result.exit_code

    if parsed.example:
        if _alternate_input_conflicts():
            result = invalid_request_result(
                request_kind,
                operation_key,
                ("--example 不接受非空标准输入",),
            )
            _emit(result.response)
            return result.exit_code
        result = handle_request("capabilities", None, "")
        if result.exit_code != 0 or result.response.get("outcome") != "ok":
            _emit(result.response)
            return result.exit_code
        try:
            operations = result.response["result"]["operations"]
            operation = next(item for item in operations if item["operation_key"] == operation_key)
        except (KeyError, StopIteration, TypeError):
            problem = "--example 指定的 operation_key 不在当前 capabilities discovery"
        else:
            try:
                if operation["implementation"]["present"] is not True:
                    raise ValueError("目标操作没有可投影的实现 metadata")
                projection = build_example_projection(operation)
                # 04/05 交互改进: --example 同时暴露 response 字段闭集,
                # 调用方无需再查阅 spec 的 "领域 result 字段闭集" 小节。
                projection["response_fields"] = operation.get("response_fields", [])
                projection["result_contract"] = operation.get("result_contract")
            except (KeyError, TypeError, ValueError):
                problem = "--example 目标 metadata 不完整，不能形成请求骨架"
            else:
                _emit(projection)
                return result.exit_code
        invalid = invalid_request_result("capabilities", operation_key, (problem,))
        _emit(invalid.response)
        return invalid.exit_code

    if parsed.summary:
        # 04/05 交互改进: capabilities --summary 提供渐进发现中间档,返回每个操作的
        # 紧凑投影(operation_key/summary/effect/result_contract/response_fields),
        # 避免每次发现都拉取全量 capabilities(约 68KB) 再逐项截断。
        if _alternate_input_conflicts():
            result = invalid_request_result(
                request_kind,
                operation_key,
                ("--summary 不接受非空标准输入",),
            )
            _emit(result.response)
            return result.exit_code
        result = handle_request("capabilities", None, "")
        if result.exit_code != 0 or result.response.get("outcome") != "ok":
            _emit(result.response)
            return result.exit_code
        operations = result.response["result"]["operations"]
        summary_response = {
            "contract": result.response["contract"],
            "response_profile": "compact",
            "request_kind": "capabilities",
            "operation_key": None,
            "outcome": "ok",
            "summary": "已按 --summary 投影各公开操作的紧凑发现信息",
            "result": {
                "mode": "discovery",
                "operations": [
                    {
                        "operation_key": op["operation_key"],
                        "summary": op["summary"],
                        "effect": op["effect"],
                        "result_contract": op.get("result_contract"),
                        "response_fields": op.get("response_fields", []),
                    }
                    for op in operations
                ],
            },
            "scope": {
                "requested": [],
                "completed": [],
                "not_completed": [],
                "governance_resolution": None,
            },
            "sources": result.response.get("sources", []),
            "disclosure": None,
            "gaps": [],
            "changes": [],
            "verification": [],
            "diagnostics": [],
            "follow_up": {
                "summary": "需要单个操作详情时, 使用 capabilities <operation_key> --example",
                "required_inputs": [],
                "required_human_decisions": [],
                "resume_conditions": [],
                "suggested_operations": [],
            },
        }
        _emit(summary_response)
        return result.exit_code

    try:
        if parsed.request_path is None:
            try:
                raw_input = _read_request_input()
            except UnicodeDecodeError:
                result = invalid_request_result(request_kind, operation_key, ("标准输入必须是 UTF-8",))
            else:
                result = handle_request(request_kind, operation_key, raw_input)
        else:
            if _alternate_input_conflicts():
                result = invalid_request_result(
                    request_kind,
                    operation_key,
                    ("--request 不得与非空标准输入同时使用",),
                )
            else:
                raw_input, file_problems = read_request_file(parsed.request_path)
                if file_problems:
                    result = invalid_request_result(request_kind, operation_key, file_problems)
                else:
                    result = handle_request(request_kind, operation_key, raw_input or "")
    except Exception as exc:  # last boundary: still form the defined machine response
        result = common_response(
            request_kind=request_kind,
            operation_key=operation_key,
            outcome="error",
            summary="Helper 实现发生未预期错误",
            not_completed_scope=[] if operation_key is None else [operation_key],
            gaps=[gap("实现异常使 Helper 无法形成所请求的可信结果")],
            diagnostics=[diagnostic("Helper 服务边界捕获未预期异常", exception_type=type(exc).__name__)],
        )
    if parsed.field_selectors:
        try:
            output = project_response_fields(result.response, parsed.field_selectors, result.exit_code)
        except ValueError:
            # A malformed internal common response cannot truthfully claim a
            # complete projection.  Preserve the source response and exit code.
            output = result.response
    else:
        output = result.response
    _emit(output)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
