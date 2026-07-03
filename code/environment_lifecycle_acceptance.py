from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from ldvh_specs import ROOT


AUTHORIZATION = "human_gate_required"
DEFAULT_ACCEPTANCE_PATH = ".ldvh-runtime/environment-lifecycle-acceptance.json"
REQUIRED_FLAGS = [
    "plugin_page_ok",
    "app_restarted",
    "authorization_ok",
    "session_start_observed",
    "pre_tool_use_observed",
    "blocking_observed",
    "positive_observed",
]


def acceptance_path(ldvh_root: Path = ROOT, path: Path | None = None) -> Path:
    if path is not None:
        return path.expanduser().resolve()
    return (ldvh_root / DEFAULT_ACCEPTANCE_PATH).resolve()


def _diagnostic(level: str, code: str, path: str, message: str, disposition: str = "blocking") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "path": path,
        "message": message,
        "disposition": disposition,
    }


def _base_status(path: Path, record: dict[str, Any] | None, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    blocking = sum(1 for diagnostic in diagnostics if diagnostic["level"] in {"blocking", "error"})
    valid = record is not None and blocking == 0
    return {
        "summary": {
            "status": "ok" if valid else "absent" if record is None and not diagnostics else "blocked",
            "valid": valid,
            "path": path.as_posix(),
            "diagnostics": len(diagnostics),
            "blocking": blocking,
        },
        "record": record,
        "diagnostics": diagnostics,
    }


def build_lifecycle_acceptance_status(
    *,
    ldvh_root: Path = ROOT,
    environment_name: str = "Codex",
    path: Path | None = None,
) -> dict[str, Any]:
    target = acceptance_path(ldvh_root, path)
    if not target.is_file():
        return _base_status(target, None, [])
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _base_status(
            target,
            None,
            [
                _diagnostic(
                    "blocking",
                    "ENV_LIFECYCLE_ACCEPTANCE_UNREADABLE",
                    target.as_posix(),
                    f"环境 lifecycle 验收记录无法读取: {exc}",
                )
            ],
        )
    record = raw if isinstance(raw, dict) else {}
    diagnostics: list[dict[str, str]] = []
    if str(record.get("environment_name", "")).strip().lower() != environment_name.strip().lower():
        diagnostics.append(
            _diagnostic(
                "blocking",
                "ENV_LIFECYCLE_ACCEPTANCE_ENVIRONMENT_MISMATCH",
                target.as_posix(),
                f"环境 lifecycle 验收记录目标环境不是 {environment_name}。",
            )
        )
    missing = [flag for flag in REQUIRED_FLAGS if record.get(flag) is not True]
    if missing:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "ENV_LIFECYCLE_ACCEPTANCE_INCOMPLETE",
                target.as_posix(),
                "环境 lifecycle 验收记录缺少通过项: " + "；".join(missing),
            )
        )
    if record.get("human_gate_confirmed") is not True:
        diagnostics.append(
            _diagnostic(
                "blocking",
                "ENV_LIFECYCLE_ACCEPTANCE_HUMAN_GATE_MISSING",
                target.as_posix(),
                "环境 lifecycle 验收记录缺少 Human Gate 确认。",
            )
        )
    return _base_status(target, record, diagnostics)


def record_lifecycle_acceptance(
    *,
    ldvh_root: Path = ROOT,
    environment_name: str = "Codex",
    path: Path | None = None,
    confirm_human_gate: bool = False,
    source_note: str = "",
) -> dict[str, Any]:
    target = acceptance_path(ldvh_root, path)
    if not confirm_human_gate:
        return _base_status(
            target,
            None,
            [
                _diagnostic(
                    "blocking",
                    "ENV_LIFECYCLE_ACCEPTANCE_CONFIRMATION_REQUIRED",
                    target.as_posix(),
                    "记录环境 lifecycle 验收前必须带 --confirm-human-gate。",
                )
            ],
        )
    record: dict[str, Any] = {
        "environment_name": environment_name,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "human_gate_confirmed": True,
        "source_note": source_note,
    }
    for flag in REQUIRED_FLAGS:
        record[flag] = True
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return build_lifecycle_acceptance_status(ldvh_root=ldvh_root, environment_name=environment_name, path=target)


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH environment lifecycle acceptance")
    print(f"- status: {summary['status']}")
    print(f"- valid: {summary['valid']}")
    print(f"- path: {summary['path']}")
    if result.get("record"):
        record = result["record"]
        print(f"- environment_name: {record.get('environment_name', '')}")
        print(f"- recorded_at: {record.get('recorded_at', '')}")
    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record or inspect LDVH environment lifecycle acceptance evidence.")
    parser.add_argument("command", choices=["status", "record"], help="status reads evidence; record writes Human-confirmed evidence")
    parser.add_argument("--ldvh-root", default=ROOT.as_posix(), help="LDVH root")
    parser.add_argument("--environment-name", default="Codex", help="target environment name")
    parser.add_argument("--path", default="", help="override acceptance evidence path")
    parser.add_argument("--confirm-human-gate", action="store_true", help="required for record")
    parser.add_argument("--source-note", default="", help="short Human-facing evidence note")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.ldvh_root).resolve()
    path = Path(args.path).resolve() if args.path else None
    if args.command == "record":
        result = record_lifecycle_acceptance(
            ldvh_root=root,
            environment_name=args.environment_name,
            path=path,
            confirm_human_gate=args.confirm_human_gate,
            source_note=args.source_note,
        )
    else:
        result = build_lifecycle_acceptance_status(ldvh_root=root, environment_name=args.environment_name, path=path)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
