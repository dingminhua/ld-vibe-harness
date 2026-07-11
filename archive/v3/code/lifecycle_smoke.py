from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from acknowledge_read_plan import build_acknowledge_read_plan
from completion_claim import build_completion_claim
from ldvh_specs import ROOT, build_preflight, required_ack_paths_for_runtime_event
from pre_tool_use import build_pre_tool_use
from session_start import build_session_start


TRIGGER_SOURCE = "ldvh.lifecycle_smoke"


def _blocking_count(result: dict[str, Any]) -> int:
    return int(result.get("summary", {}).get("blocking") or 0)


def _diagnostic(code: str, path: str, message: str) -> dict[str, str]:
    return {
        "level": "blocking",
        "code": code,
        "path": path,
        "message": message,
        "disposition": "blocking",
    }


def _stage(name: str, result: dict[str, Any]) -> dict[str, Any]:
    summary = result.get("summary", {})
    return {
        "stage": name,
        "event": summary.get("event", ""),
        "internal_event": summary.get("internal_event", ""),
        "status": summary.get("status", ""),
        "blocking": _blocking_count(result),
        "diagnostics": len(result.get("diagnostics", [])),
    }


def build_lifecycle_smoke(
    root: Path = ROOT,
    *,
    session_id: str = "ldvh-lifecycle-smoke",
    target_path: str = "tests/code/test_ldvh_specs_validate.py",
    task: str = "LDVH lifecycle same-chain smoke",
    verification_evidence: list[str] | None = None,
) -> dict[str, Any]:
    evidence = verification_evidence or ["LDVH lifecycle smoke reached ldvh.completion_claim with prior stages ok"]
    preflight_plan = build_preflight(
        root,
        target_path=target_path,
        operation="write",
        task=task,
        trigger_source=TRIGGER_SOURCE,
    )
    acknowledged_paths = required_ack_paths_for_runtime_event("pre_tool_use", preflight_plan)

    session_start = build_session_start(
        root,
        session_id=session_id,
        target_path=target_path,
        task=task,
        trigger_source=TRIGGER_SOURCE,
    )
    acknowledge = build_acknowledge_read_plan(
        root,
        session_id=session_id,
        target_path=target_path,
        task=task,
        trigger_source=TRIGGER_SOURCE,
        acknowledged_paths=acknowledged_paths,
        runtime_cache=True,
    )
    pre_tool_use = build_pre_tool_use(
        root,
        session_id=session_id,
        target_path=target_path,
        task=task,
        operation="write",
        trigger_source=TRIGGER_SOURCE,
        acknowledged_paths=[],
        runtime_cache=True,
    )
    completion_claim = build_completion_claim(
        root,
        session_id=session_id,
        target_path=target_path,
        task=task,
        operation="complete",
        trigger_source=TRIGGER_SOURCE,
        acknowledged_paths=acknowledged_paths,
        verification_evidence=evidence,
    )

    stages = [
        _stage("ldvh.session_start", session_start),
        _stage("ldvh.acknowledge_read_plan", acknowledge),
        _stage("ldvh.pre_tool_use", pre_tool_use),
        _stage("ldvh.completion_claim", completion_claim),
    ]
    diagnostics: list[dict[str, str]] = []
    for result in (session_start, acknowledge, pre_tool_use, completion_claim):
        diagnostics.extend(result.get("diagnostics", []))

    if acknowledge.get("summary", {}).get("runtime_cache") != "written":
        diagnostics.append(
            _diagnostic(
                "LDVH_LIFECYCLE_ACK_CACHE_NOT_WRITTEN",
                "runtime://ldvh.acknowledge_read_plan",
                "ldvh.acknowledge_read_plan 未写入同 session runtime receipt cache。",
            )
        )
    if pre_tool_use.get("summary", {}).get("runtime_cache") != "hit":
        diagnostics.append(
            _diagnostic(
                "LDVH_LIFECYCLE_PRE_TOOL_CACHE_MISS",
                "runtime://ldvh.pre_tool_use",
                "ldvh.pre_tool_use 未命中同 session read_plan 消费依据。",
            )
        )

    expected_events = [
        "ldvh.session_start",
        "ldvh.acknowledge_read_plan",
        "ldvh.pre_tool_use",
        "ldvh.completion_claim",
    ]
    observed_events = [stage["event"] for stage in stages]
    if observed_events != expected_events:
        diagnostics.append(
            _diagnostic(
                "LDVH_LIFECYCLE_CANONICAL_EVENT_MISMATCH",
                "runtime://ldvh.lifecycle_smoke",
                "LDVH lifecycle smoke 未按预期输出 canonical events: " + " -> ".join(observed_events),
            )
        )

    blocking = sum(1 for diagnostic in diagnostics if diagnostic.get("level") in {"error", "blocking"})
    status = "blocked" if blocking else "ok"

    return {
        "metadata": {
            "read_only": True,
            "authority": "ldvh_lifecycle_canonical_event_smoke",
            "authorization": "none",
            "environment_integrated": False,
            "root": root.as_posix(),
        },
        "summary": {
            "status": status,
            "events": observed_events,
            "stages": len(stages),
            "blocking": blocking,
            "diagnostics": len(diagnostics),
            "environment_integrated": False,
            "runtime_cache_bridge": pre_tool_use.get("summary", {}).get("runtime_cache", ""),
        },
        "session_id": session_id,
        "target_path": target_path,
        "stages": stages,
        "runtime_cache": {
            "acknowledge_status": acknowledge.get("summary", {}).get("runtime_cache", ""),
            "pre_tool_use_status": pre_tool_use.get("summary", {}).get("runtime_cache", ""),
            "path": pre_tool_use.get("runtime_cache", {}).get("path") or acknowledge.get("runtime_cache", {}).get("path", ""),
        },
        "results": {
            "session_start": session_start,
            "acknowledge_read_plan": acknowledge,
            "pre_tool_use": pre_tool_use,
            "completion_claim": completion_claim,
        },
        "diagnostics": diagnostics,
    }


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 lifecycle canonical-event smoke")
    print(f"- status: {summary['status']}")
    print(f"- session_id: {result['session_id']}")
    print(f"- target_path: {result['target_path']}")
    print(f"- environment_integrated: false")
    print(f"- runtime_cache_bridge: {summary['runtime_cache_bridge']}")
    print("\nEvents:")
    for event in summary["events"]:
        print(f"- {event}")
    print("\nStages:")
    for stage in result["stages"]:
        print(f"- {stage['stage']}: {stage['status']} ({stage['event']})")
    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")
    print("\nAuthorization: none")
    print("Boundary: this smoke tests LDVH canonical events and runtime cache bridge; it does not prove target environment integrated.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run LDVH lifecycle same-chain smoke over LDVH canonical events.")
    parser.add_argument("--root", default=ROOT.as_posix(), help="repository root")
    parser.add_argument("--session-id", default="ldvh-lifecycle-smoke", help="current session identifier")
    parser.add_argument("--target-path", default="tests/code/test_ldvh_specs_validate.py", help="safe target for pre-tool-use check")
    parser.add_argument("--task", default="LDVH lifecycle same-chain smoke", help="current task summary")
    parser.add_argument(
        "--verification-evidence",
        action="append",
        default=[],
        help="verification evidence for ldvh.completion_claim; may be repeated",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_lifecycle_smoke(
        Path(args.root).resolve(),
        session_id=args.session_id,
        target_path=args.target_path,
        task=args.task,
        verification_evidence=args.verification_evidence,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
