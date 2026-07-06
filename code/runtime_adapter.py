from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from completion_claim import build_completion_claim
from ldvh_specs import ROOT
from pre_tool_use import build_pre_tool_use
from session_start import build_session_start


INTEGRATION_SCOPE = "hook.runtime_adapter"
REQUIRED_PAYLOAD_FIELDS = [
    "event",
    "session_id",
    "target_path",
    "operation",
    "task",
    "acknowledged_paths",
    "verification_evidence",
]


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _diagnostic(level: str, code: str, path: str, message: str, disposition: str = "blocking") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "path": path,
        "message": message,
        "disposition": disposition,
    }


def _normalize_event(event: str) -> str:
    return event.strip().replace("-", "_")


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return [str(value)]


def _base_result(root: Path, payload: dict[str, Any], diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"error", "blocking"})
    status = "blocked" if blocking else "ok"
    event = _normalize_event(str(payload.get("event", "")))
    return {
        "metadata": {
            "read_only": True,
            "authority": "runtime_adapter_payload_contract",
            "authorization": "none",
            "environment_integrated": False,
            "adapter_integrated": False,
            "integration_scope": INTEGRATION_SCOPE,
            "root": root.as_posix(),
        },
        "summary": {
            "status": status,
            "event": event,
            "dispatch_status": "",
            "diagnostics": len(diagnostics),
            "blocking": blocking,
            "adapter_integrated": False,
            "environment_integrated": False,
            "integration_scope": INTEGRATION_SCOPE,
        },
        "payload": payload,
        "dispatch": None,
        "diagnostics": diagnostics,
    }


def _missing_field_diagnostics(payload: dict[str, Any]) -> list[dict[str, str]]:
    missing = [field for field in REQUIRED_PAYLOAD_FIELDS if field not in payload]
    diagnostics: list[dict[str, str]] = []
    if missing:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "RUNTIME_ADAPTER_PAYLOAD_FIELD_MISSING",
                "runtime://adapter-payload",
                "runtime adapter payload 缺少字段: " + "；".join(missing),
            )
        )

    trigger_source = str(payload.get("trigger_source") or "")
    target_values = [
        str(value).strip()
        for value in [payload.get("target_path"), *_list_value(payload.get("target_paths"))]
        if str(value).strip()
    ]
    is_external_trigger = bool(trigger_source) and not trigger_source.startswith("manual")
    has_relative_target = any(not Path(target).expanduser().is_absolute() for target in target_values)
    has_cwd = bool(str(payload.get("cwd") or "").strip())
    if is_external_trigger and has_relative_target and not has_cwd:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "RUNTIME_ADAPTER_CWD_REQUIRED_FOR_RELATIVE_TARGET",
                "runtime://adapter-payload",
                "外部 adapter 或 Hook payload 使用相对 target_path 时必须提供真实 cwd，不能由 LDVH root 代替。",
            )
        )
    return diagnostics


def _dispatchers() -> dict[str, Callable[..., dict[str, Any]]]:
    return {
        "session_start": build_session_start,
        "pre_tool_use": build_pre_tool_use,
        "completion_claim": build_completion_claim,
    }


def dispatch_runtime_payload(root: Path = ROOT, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized_payload = dict(payload or {})
    diagnostics = _missing_field_diagnostics(normalized_payload)
    if diagnostics:
        return _base_result(root, normalized_payload, diagnostics)

    event = _normalize_event(str(normalized_payload.get("event", "")))
    dispatcher = _dispatchers().get(event)
    if dispatcher is None:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "RUNTIME_ADAPTER_EVENT_UNKNOWN",
                "runtime://adapter-payload",
                f"runtime adapter 不支持事件: {event}",
            )
        )
        return _base_result(root, normalized_payload, diagnostics)

    trigger_source = str(normalized_payload.get("trigger_source") or INTEGRATION_SCOPE)
    common_kwargs = {
        "session_id": str(normalized_payload.get("session_id", "")),
        "target_path": str(normalized_payload.get("target_path", "")),
        "cwd": str(normalized_payload.get("cwd", "")) or None,
        "config_root": str(normalized_payload.get("config_root", "")) or None,
        "target_paths": _list_value(normalized_payload.get("target_paths")),
        "task": str(normalized_payload.get("task", "")),
        "operation": str(normalized_payload.get("operation", "")) or "write",
        "trigger_source": trigger_source,
    }
    if event == "session_start":
        dispatch = dispatcher(
            root,
            session_id=common_kwargs["session_id"],
            target_path=common_kwargs["target_path"],
            cwd=common_kwargs["cwd"],
            config_root=common_kwargs["config_root"],
            target_paths=common_kwargs["target_paths"],
            task=common_kwargs["task"],
            trigger_source=trigger_source,
        )
    elif event == "pre_tool_use":
        dispatch = dispatcher(
            root,
            **common_kwargs,
            acknowledged_paths=_list_value(normalized_payload.get("acknowledged_paths")),
        )
    else:
        dispatch = dispatcher(
            root,
            **common_kwargs,
            acknowledged_paths=_list_value(normalized_payload.get("acknowledged_paths")),
            verification_evidence=_list_value(normalized_payload.get("verification_evidence")),
        )

    result = _base_result(root, normalized_payload, dispatch["diagnostics"])
    result["summary"]["status"] = dispatch["summary"]["status"]
    result["summary"]["event"] = event
    result["summary"]["dispatch_status"] = dispatch["summary"]["status"]
    result["summary"]["diagnostics"] = len(dispatch["diagnostics"])
    result["summary"]["blocking"] = dispatch["summary"]["blocking"]
    result["dispatch"] = dispatch
    result["diagnostics"] = dispatch["diagnostics"]
    return result


def _payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload_file:
        return json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    if args.payload_json:
        return json.loads(args.payload_json)
    return {
        "event": args.event or "",
        "session_id": args.session_id,
        "cwd": args.cwd,
        "config_root": args.config_root,
        "target_path": args.target_path,
        "target_paths": args.target_paths,
        "operation": args.operation,
        "task": args.task,
        "acknowledged_paths": args.acknowledged_path,
        "verification_evidence": args.verification_evidence,
        "trigger_source": args.trigger_source,
    }


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 runtime adapter")
    print(f"- status: {summary['status']}")
    print(f"- event: {summary['event']}")
    print(f"- dispatch_status: {summary['dispatch_status']}")
    print(f"- adapter_integrated: {_bool_text(summary['adapter_integrated'])}")
    print(f"- environment_integrated: {_bool_text(summary['environment_integrated'])}")
    print(f"- integration_scope: {summary['integration_scope']}")

    dispatch = result.get("dispatch")
    if dispatch:
        receipt = dispatch["receipt"]
        print(f"- receipt_id: {receipt['receipt_id']}")
        print(f"- receipt_storage: {receipt['storage']}")
        print(f"- dispatch_integration_scope: {dispatch['summary'].get('integration_scope', '')}")

    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")

    print("\nAuthorization: none")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dispatch LDVH v3 lifecycle Hook events through one adapter payload.")
    parser.add_argument(
        "event",
        nargs="?",
        help="runtime event: session-start, pre-tool-use, or completion-claim",
    )
    parser.add_argument("--root", default=ROOT.as_posix(), help="repository root")
    parser.add_argument("--payload-file", default="", help="JSON payload file")
    parser.add_argument("--payload-json", default="", help="JSON payload string")
    parser.add_argument("--session-id", default="", help="current session identifier")
    parser.add_argument("--cwd", default="", help="current working directory for target resolution")
    parser.add_argument("--config-root", default="", help="root containing LDVH-GOVERNED-PROJECTS.yaml")
    parser.add_argument("--target-path", default="", help="target path")
    parser.add_argument("--target-paths", action="append", default=[], help="explicit target path; may be repeated")
    parser.add_argument("--task", default="", help="current task summary")
    parser.add_argument("--operation", default="write", help="operation kind")
    parser.add_argument("--trigger-source", default=INTEGRATION_SCOPE, help="trigger source label")
    parser.add_argument(
        "--acknowledged-path",
        action="append",
        default=[],
        help="acknowledged read_plan path; may be repeated or comma-separated",
    )
    parser.add_argument(
        "--verification-evidence",
        action="append",
        default=[],
        help="verification evidence; may be repeated or comma-separated",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = dispatch_runtime_payload(Path(args.root).resolve(), _payload_from_args(args))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
