#!/usr/bin/env python3
"""Replay DSH session logs through the evidence protocol and output structured results.

This script reads session logs from ~/.dsh/sessions/ (structured fields only),
runs each through the evidence protocol, and outputs a structured verification
record.  It never reads message bodies, tool-result content, or assistant output.

Usage:
    .venv/bin/python code/plans/replay-session-samples.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ldvh.testing.session_comparability import audit_session, SessionLogError
from ldvh.testing.evidence_protocol import (
    classify_session_events,
    extract_session_identity,
    judge_protocol_comparability,
    SOURCE_LEVELS,
)

# Session log directory and session IDs to replay.
SESSION_DIR = Path.home() / ".dsh" / "sessions" / "--Users-dmh2002-poker_hud_projects-ld-vibe-harness-v4--"

# Select 5+ sessions with a range of sizes for varied replay coverage.
SESSION_IDS = [
    "1d71a60f-655a-47ff-90af-e15ede5fe93d",  # large (449KB)
    "7e8893c3-b986-4ac6-a093-7c23502f5ee4",  # large (388KB)
    "49ccc7be-e906-4396-b908-3d70ab64d013",  # large (413KB)
    "6d361846-2a50-412c-9364-ee1081d0163c",  # medium (210KB)
    "17c8e759-81c4-4b70-8b41-8dd15bbc36ec",  # medium (119KB)
    "1ebd4598-94ab-446b-a93a-615071705c83",  # small (15KB)
    "650897ee-a1e8-4fae-86fb-40f9d2a8fe65",  # small (13KB)
]


def replay_session(session_id: str) -> dict:
    """Replay one session through the evidence protocol.

    Returns a structured result dict with identity fingerprints, source
    grading counts, and comparability verdict.  No raw content is included.
    """
    path = SESSION_DIR / session_id / "session.jsonl.zstd"
    if not path.exists():
        return {
            "session_id": session_id,
            "error": f"session log not found: {path}",
        }

    try:
        fingerprint, comparability = audit_session(path)
    except SessionLogError as error:
        return {
            "session_id": session_id,
            "error": str(error),
        }

    # Protocol-level analysis.
    source_counts = classify_session_events(fingerprint)
    identity = extract_session_identity(fingerprint)
    protocol_comparability = judge_protocol_comparability(fingerprint)

    # Build structured result (no raw content, no message bodies).
    result = {
        "session_id": session_id,
        "carrier_entries": list(fingerprint.distinct_entries),
        "tool_names": list(fingerprint.tool_names),
        "event_graph": {
            "turn_start": fingerprint.turn_start,
            "turn_end": fingerprint.turn_end,
            "step_start": fingerprint.step_start,
            "step_end": fingerprint.step_end,
            "tool_call": fingerprint.tool_call,
            "tool_result": fingerprint.tool_result,
            "pairing_ok": fingerprint.pairing_ok,
        },
        "flag_events": [
            {"type": t, "count": c} for t, c in fingerprint.flags
        ],
        "source_grading": {
            level: source_counts.get(level, 0) for level in SOURCE_LEVELS
        },
        "identity_fingerprints": {
            "task": identity.task_identity[:16] + "...",
            "contract": identity.contract_identity[:16] + "...",
            "payload": identity.payload_identity[:16] + "...",
            "runner": identity.runner_identity[:16] + "...",
            "full_fingerprint": identity.fingerprint()[:16] + "...",
        },
        "comparability": {
            "session_verdict": comparability.verdict,
            "session_reasons": list(comparability.reasons),
            "protocol_verdict": protocol_comparability.protocol_verdict,
            "protocol_reasons": list(protocol_comparability.protocol_reasons),
            "effective_verdict": protocol_comparability.effective_verdict,
            "identity_mismatch_types": list(protocol_comparability.identity_mismatch_types),
        },
    }
    return result


def main() -> None:
    results: list[dict] = []
    errors = 0

    for session_id in SESSION_IDS:
        result = replay_session(session_id)
        if "error" in result and result.get("session_id"):
            errors += 1
        results.append(result)

    # Build verification record.
    summary = {
        "protocol_version": "ldvh-evidence-protocol/1",
        "total_sessions": len(SESSION_IDS),
        "successful_sessions": len(SESSION_IDS) - errors,
        "failed_sessions": errors,
        "verdict_counts": {},
        "claim_boundary": (
            "structured replay only; does not prove causal effect, host receipt, "
            "or overall service improvement.  No raw content or message bodies "
            "were read or retained."
        ),
    }

    for result in results:
        if "error" in result:
            verdict = "error"
        else:
            verdict = result["comparability"]["effective_verdict"]
        summary["verdict_counts"][verdict] = summary["verdict_counts"].get(verdict, 0) + 1

    output = {
        "summary": summary,
        "sessions": results,
    }

    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()