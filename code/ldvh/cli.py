"""Process entry point for the LDVH Helper CLI machine interface."""

from __future__ import annotations

import json
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


def _read_request_input() -> str:
    """Read the machine request body from stdin without blocking.

    An unconditional ``sys.stdin.buffer.read()`` blocks forever when stdin is a
    pipe without EOF (CI/sandbox/tooling that leaves stdin open), and the
    surrounding timeout/watchdog then SIGKILLs the process (exit 137). Probe stdin
    first: read the full body only when data is immediately available, otherwise
    fall back to an empty body. Callers that pipe a request (``subprocess.run(
    input=...)`` or ``echo body | ldvh ...``) pre-buffer the data before the Helper
    finishes importing, so the probe sees it; an idle open pipe yields "" instead
    of hanging. Windows ``select()`` does not support pipe/file handles, so on that
    platform the probe raises and we fall back to a blocking read — callers that
    pipe a body always provide EOF, so body reading is preserved; an idle open pipe
    would hang there, matching pre-existing behaviour rather than adding a regression.
    """
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
            raw_input = _read_request_input()
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
