"""Runner-owned command surface for the v7 knowledge-activation trial.

The v7 trial has two phases:

- Phase 1 (Study evaluation) runs an independent study-only evaluation on the
  frozen S1-S6 sample with the Study fixed mechanism (no-trigger +
  relationship navigation + F2 index + F3 on-demand), producing discovery /
  application / interference rates that are mechanically judged.
- Phase 2 (ADR/Pitfall differentiation) runs the calibration paired trial
  (baseline = v5 wide trigger; enhanced = per-family differentiated trigger)
  and judges the per-family thresholds anchored to the archived v6 baseline.

This module owns the deterministic trial surface: trigger evaluation, evidence
trace building, and bundle compilation helpers.  Live member/scorer subagent
runs are orchestrated by the trial CLI subcommands under the WorkCase's
run authorization; the deterministic trigger decision helpers are pure and
fully testable here.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ldvh.testing.knowledge_precheck_v7 import (
    CONDITIONS,
    RETAINED_PAIR_TARGET,
    TASK_FAMILIES,
    build_v7_trigger_trace,
    evaluate_v7_trigger,
    read_frozen_protocol,
)


class V7TrialError(ValueError):
    """Raised before a partial or out-of-order artifact is accepted."""


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _write_new_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise V7TrialError(f"refusing to replace existing evidence: {path.name}")
    path.write_bytes(_json_bytes(value))


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise V7TrialError(f"cannot read {label}") from error
    if not isinstance(value, dict):
        raise V7TrialError(f"{label} must be a JSON object")
    return value


def evaluate_all_triggers(
    protocol: dict[str, Any],
    condition: str,
) -> list[dict[str, Any]]:
    """Deterministically evaluate every frozen task's trigger decision."""
    if condition not in CONDITIONS:
        raise V7TrialError(f"unknown condition: {condition}")
    traces: list[dict[str, Any]] = []
    for index, task in enumerate(protocol["tasks"]):
        family = task["family"]
        user_task = task["user_task"]
        pair_id = task["pair_id"]
        packet = {
            "attempt_id": f"v7-{condition}-{pair_id}-{index:02d}",
            "pair_id": pair_id,
            "family": family,
            "condition": condition,
        }
        response = evaluate_v7_trigger(family, user_task, condition)
        trace = build_v7_trigger_trace(response, packet, protocol)
        traces.append(trace)
    return traces


def judge_trigger_metrics(
    traces: list[dict[str, Any]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    """Judge the deterministic trigger metrics against the frozen gold.

    trigger_correct counts tasks where triggered == gold.expected_f2_trigger.
    unnecessary_f2 counts gold=false tasks that triggered (unnecessary F2).
    """
    gold_by_id = {task["pair_id"]: task for task in protocol["tasks"]}
    per_family = Counter()
    overall = Counter()
    unnecessary = 0
    missed = 0
    for trace in traces:
        pair_id = trace["pair_id"]
        task = gold_by_id[pair_id]
        family = task["family"]
        expected = bool(task["gold"]["expected_f2_trigger"])
        triggered = bool(trace["triggered"])
        correct = expected == triggered
        per_family[(family, "correct")] += int(correct)
        per_family[(family, "total")] += 1
        overall["correct"] += int(correct)
        overall["total"] += 1
        if expected and not triggered:
            missed += 1
        if not expected and triggered:
            unnecessary += 1
    per_family_summary = {}
    for family in TASK_FAMILIES:
        c = per_family[(family, "correct")]
        t = per_family[(family, "total")]
        per_family_summary[family] = {"trigger_correct": f"{c}/{t}"}
    return {
        "overall": {
            "trigger_correct": f"{overall['correct']}/{overall['total']}",
            "unnecessary_f2": unnecessary,
            "missed_detection": missed,
        },
        "per_family": per_family_summary,
    }


def compile_trigger_evidence(
    protocol_path: Path,
    snapshot_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Compile the deterministic trigger evidence bundle (pre-seal draft)."""
    protocol = read_frozen_protocol(protocol_path)
    snapshot = _read_json(snapshot_path, "v7 source snapshot")
    traces = {condition: evaluate_all_triggers(protocol, condition) for condition in CONDITIONS}
    metrics = {condition: judge_trigger_metrics(traces[condition], protocol) for condition in CONDITIONS}
    bundle = {
        "schema_version": "ldvh-knowledge-precheck-v7-evidence/1",
        "compiled_at": _now(),
        "governed_project_id": "ldvh",
        "protocol_sha256": None,  # filled by seal step from canonical bytes
        "retained_pairs": RETAINED_PAIR_TARGET,
        "conditions": list(CONDITIONS),
        "trigger_traces": traces,
        "trigger_metrics": metrics,
        "study_relationship_graph": snapshot.get("study_relationship_graph"),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_new_json(out_dir / "trigger-evidence.json", bundle)
    return bundle


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="v7 knowledge-activation trial runner")
    sub = parser.add_subparsers(dest="command", required=True)
    p_eval = sub.add_parser("evaluate-triggers", help="deterministic trigger evaluation over the frozen 18 tasks")
    p_eval.add_argument("--protocol", required=True, help="path to protocol.json")
    p_eval.add_argument("--condition", choices=list(CONDITIONS), help="limit to one condition")
    p_eval.add_argument("--out", required=True, help="output directory for trigger evidence")
    p_compile = sub.add_parser("compile-trigger-evidence", help="compile deterministic trigger evidence bundle")
    p_compile.add_argument("--protocol", required=True)
    p_compile.add_argument("--snapshot", required=True)
    p_compile.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if args.command == "evaluate-triggers":
        protocol = read_frozen_protocol(Path(args.protocol))
        traces = evaluate_all_triggers(protocol, args.condition)
        metrics = judge_trigger_metrics(traces, protocol)
        print(json.dumps({"traces": traces, "metrics": metrics}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "compile-trigger-evidence":
        bundle = compile_trigger_evidence(Path(args.protocol), Path(args.snapshot), Path(args.out))
        print(json.dumps({"compiled": bundle["schema_version"], "pairs": bundle["retained_pairs"]}, ensure_ascii=False))
        return 0
    raise V7TrialError(f"unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
