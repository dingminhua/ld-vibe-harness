"""Deterministic isolated-fixture replay for ``prepare-fact-object-update``.

The replay compares a known-contract read/compose/write path with the public
prepare/write path.  It records only labels, hashes, counts, booleans, and
aggregates; request bodies, fact bodies, signatures, authorization data,
absolute paths, and session data are never retained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import serialize_fact_object
from ldvh.helper.service import handle_request

CALIBER = "wc-e-prepare-update-replay/1"
TASK_COUNT = 12
STRATEGIES = ("known-contract", "prepare")
DISCOVERY_MODES = frozenset({"minimal", "cold"})
BRANCHES = frozenset({"positive", "stale", "no-op", "invalid-signature"})
FACT_TYPES = frozenset({"spark", "study", "adr", "pitfall", "workcase"})
MANAGED_FIELDS = frozenset({"object_uid", "object_id", "fact_type_key", "created_at", "updated_at"})
RETAINED_RECORD_FIELDS = frozenset(
    {
        "task_id",
        "task_hash",
        "fact_type_key",
        "branch",
        "discovery_mode",
        "strategy",
        "helper_calls",
        "shell_invocations",
        "request_chars",
        "caller_transformations",
        "expected_outcome_met",
        "state_changed",
        "zero_write_failure",
        "host_receipt",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "wall_ms",
        "queue_ms",
    }
)
_DENIED_KEYS = frozenset(
    {
        "raw_prompt",
        "prompt",
        "request",
        "request_body",
        "fact_object",
        "authorization_reference",
        "signature",
        "absolute_path",
        "session_id",
        "transcript",
        "secret",
    }
)
_SIGNATURE = {
    "product_name": "deterministic-replay",
    "model_name": "fixture-runner",
}
_BODY = (
    "## 研究问题\n\n准备草案是否保持正文。\n\n"
    "## 输入与边界\n\n只使用隔离 fixture。\n\n"
    "## 关键发现\n\n正文应保持不变。\n\n"
    "## 建议\n\n使用受控更新入口。\n\n"
    "## 后续分流\n\n无需分流。\n"
)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, member in value.items():
            keys.add(str(key))
            keys.update(_all_keys(member))
    elif isinstance(value, list):
        for member in value:
            keys.update(_all_keys(member))
    return keys


def validate_protocol(protocol: dict[str, Any]) -> tuple[str, ...]:
    problems: list[str] = []
    if protocol.get("caliber") != CALIBER:
        problems.append("caliber")
    if protocol.get("protocol_version") != 1:
        problems.append("protocol-version")
    if protocol.get("frozen_before_execution") is not True:
        problems.append("not-frozen")
    tasks = protocol.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != TASK_COUNT:
        problems.append("task-count")
        return tuple(problems)
    ids: list[object] = []
    for task in tasks:
        if not isinstance(task, dict):
            problems.append("task-shape")
            continue
        if set(task) != {"task_id", "fact_type_key", "branch", "discovery_mode"}:
            problems.append("task-fields")
        ids.append(task.get("task_id"))
        if task.get("fact_type_key") not in FACT_TYPES:
            problems.append("task-fact-type")
        if task.get("branch") not in BRANCHES:
            problems.append("task-branch")
        if task.get("discovery_mode") not in DISCOVERY_MODES:
            problems.append("task-discovery-mode")
    if len(set(ids)) != TASK_COUNT:
        problems.append("task-id-uniqueness")
    if {task.get("fact_type_key") for task in tasks if isinstance(task, dict)} != FACT_TYPES:
        problems.append("fact-type-coverage")
    if {task.get("branch") for task in tasks if isinstance(task, dict)} != BRANCHES:
        problems.append("branch-coverage")
    expected_hash = canonical_sha256(tasks)
    if protocol.get("task_package_sha256") != expected_hash:
        problems.append("task-package-hash")
    metrics = protocol.get("metrics", {})
    if metrics.get("helper_calls_and_shell_invocations_separate") is not True:
        problems.append("call-count-boundary")
    if metrics.get("host_metrics") != "unavailable-unless-observed":
        problems.append("host-metric-boundary")
    privacy = protocol.get("privacy", {})
    if set(privacy.get("retained_record_fields", [])) != RETAINED_RECORD_FIELDS:
        problems.append("retained-record-fields")
    if set(privacy.get("denylist", [])) != _DENIED_KEYS:
        problems.append("privacy-denylist")
    return tuple(sorted(set(problems)))


def _uid(counter: int) -> str:
    return f"0198f1c7-8a2b-7c3d-9e4f-{counter:012x}"


def _authorization() -> dict[str, Any]:
    return {
        "authorized_actions": [
            {
                "action_id": "authorization-bounded-write",
                "summary": "Write one isolated fixture update.",
                "target_scope": "The isolated fixture WorkCase.",
                "effect_scope": "One local fixture write.",
                "risk_summary": "No external or real-project effect.",
                "rollback_summary": "Discard the temporary directory.",
                "rule_refs": ["specs/21", "specs/06"],
            },
            {
                "action_id": "authorization-delegate-independent-review",
                "summary": "Delegate isolated review.",
                "target_scope": "The isolated fixture WorkCase.",
                "effect_scope": "Read-only fixture review.",
                "risk_summary": "Fixture declaration is not real independence.",
                "rollback_summary": "Discard the temporary directory.",
                "rule_refs": ["specs/21"],
            },
            {
                "action_id": "authorization-independent-result-review",
                "summary": "Review isolated fixture result.",
                "target_scope": "The isolated fixture WorkCase.",
                "effect_scope": "Read-only fixture review.",
                "risk_summary": "Fixture declaration is not real independence.",
                "rollback_summary": "Discard the temporary directory.",
                "rule_refs": ["specs/21"],
            },
        ],
        "quality_gates": [
            {
                "gate_id": "independent-result-review",
                "reviewer_mode": "independent-read-only",
                "delegation_action_id": "authorization-delegate-independent-review",
                "result_review_action_id": "authorization-independent-result-review",
            }
        ],
        "action_ceiling": "Only the isolated fixture may change.",
        "prohibited_actions": ["publish", "push"],
        "allowed_adjustments": "Only deterministic fixture setup may vary.",
        "verification_and_rollback": "Compare bytes and discard the temporary directory.",
        "out_of_bounds_handling": "Stop the fixture task.",
    }


def _fact_fields(fact_type_key: str, object_uid: str) -> dict[str, Any]:
    object_id = f"{fact_type_key}-0001"
    fields: dict[str, Any] = {
        "object_uid": object_uid,
        "object_id": object_id,
        "fact_type_key": fact_type_key,
        "title": f"Isolated {fact_type_key} fixture",
        "created_at": "2026-07-14T09:00:00+08:00",
        "updated_at": "2026-07-14T10:00:00+08:00",
        "change_log": [
            {
                "signature": deepcopy(_SIGNATURE),
                "at": "2026-07-14T09:00:00+08:00",
                "summary": "Create isolated fixture.",
            }
        ],
    }
    if fact_type_key == "spark":
        fields.update(status="open", summary="Before fixture update.", priority="P2")
    elif fact_type_key == "study":
        fields.update(
            status="active",
            report_kind="technical_assessment",
            research_question="Does the draft preserve the isolated fact?",
            abstract="Before fixture update.",
            research_intent="Exercise the deterministic replay boundary.",
            recommendation_summary="Use only bounded fixture evidence.",
            input_refs=[{"kind": "specification", "locator": "specs/05-事实模型基础规范.md"}],
        )
    elif fact_type_key == "adr":
        fields.update(
            status="active",
            decision_question="Which isolated direction is selected?",
            decision="Use the bounded fixture direction.",
            applicability="Only this deterministic fixture.",
            rationale="Before fixture update.",
            consequences="No real project decision or broad claim follows.",
        )
    elif fact_type_key == "pitfall":
        fields.update(
            status="active",
            applicability="Only this deterministic fixture.",
            validation_summary="Before fixture update.",
            symptoms="The fixture operation did not complete.",
            trigger_conditions="The fixture input was incomplete.",
            root_cause="The fixture lacked its required input.",
            resolution="Restore the fixture input.",
            avoidance="Check the fixture input before execution.",
        )
    elif fact_type_key == "workcase":
        fields.update(
            status="open",
            phase="human_plan_confirming",
            plan_version=1,
            goal="Produce one bounded deterministic fixture result.",
            scope="Only this isolated temporary WorkCase.",
            priority="P2",
            success_criterion_definitions=[
                {"criterion_id": "criterion-main", "statement": "The fixture remains mechanically valid."}
            ],
            work_items=[
                {
                    "item_id": "item-main",
                    "goal": "Complete the isolated fixture.",
                    "expected_result": "A bounded result is available.",
                    "status": "pending",
                }
            ],
            creation_reviews=[
                {
                    "reviewer": "fixture-reviewer",
                    "reviewed_at": "2026-07-14T09:30:00+08:00",
                    "subject_version": 1,
                    "scope": "Review the isolated fixture plan.",
                    "conclusion": "pass",
                    "actual_method": "subagent-read-only",
                    "covered_quality_gate_ids": ["independent-result-review"],
                }
            ],
            execution_authorization=_authorization(),
            waiting_on="Wait for the isolated Human Gate fixture.",
        )
    else:  # pragma: no cover - validated protocol closes the type set
        raise ValueError(f"unsupported fixture type: {fact_type_key}")
    return fields


def _fixture(root: Path, fact_type_key: str, counter: int) -> tuple[Path, Path, Path, str]:
    workspace = root / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    subprocess.run(["git", "-C", str(project), "init", "-q"], check=True, capture_output=True)
    object_uid = _uid(counter)
    fields = _fact_fields(fact_type_key, object_uid)
    path = project / LAYOUTS[fact_type_key].canonical_path(fields["object_id"])
    path.parent.mkdir(parents=True)
    body = _BODY if fact_type_key == "study" else None
    path.write_text(serialize_fact_object(LAYOUTS[fact_type_key], fields, body), encoding="utf-8")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "governance_instance_name: Replay Workspace",
                "product_description: Deterministic prepare-update replay.",
                "projects:",
                "  - id: replay",
                f"    path: {project}",
                "    name: Replay",
                "    description: Isolated replay project.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workspace, project, path, object_uid


def _managed_draft(fact_object: dict[str, Any], carrier: str) -> dict[str, Any]:
    draft = deepcopy(fact_object)
    if carrier == "markdown":
        for field in MANAGED_FIELDS:
            draft["frontmatter"].pop(field, None)
        return draft
    for field in MANAGED_FIELDS:
        draft.pop(field, None)
    return draft


def _semantic_fields(fact_type_key: str) -> tuple[str, str]:
    return {
        "spark": ("summary", "完成隔离 fixture 更新"),
        "study": ("abstract", "完成隔离 fixture 更新"),
        "adr": ("rationale", "完成隔离 fixture 更新"),
        "pitfall": ("validation_summary", "完成隔离 fixture 更新"),
        "workcase": ("title", "完成更新的隔离 WorkCase fixture"),
    }[fact_type_key]


def _mutate_request(request: dict[str, Any], fact_type_key: str, branch: str) -> None:
    fact_object = request["arguments"]["fact_object"]
    fields = fact_object["frontmatter"] if fact_type_key == "study" else fact_object
    if branch in {"positive", "stale", "invalid-signature"}:
        field, value = _semantic_fields(fact_type_key)
        fields[field] = value
        fields["change_log"].append(
            {"at": "2000-01-01T00:00:00Z", "summary": "应用隔离 replay 更新"}
        )
    if branch != "invalid-signature":
        request["observed_context"]["signature"] = deepcopy(_SIGNATURE)


def _call(
    operation_key: str | None,
    request_kind: str,
    payload: dict[str, Any],
    counters: dict[str, int],
) -> dict[str, Any]:
    raw = canonical_json(payload)
    counters["helper_calls"] += 1
    counters["request_chars"] += len(raw)
    return handle_request(request_kind, operation_key, raw).response


def _run_strategy(task: dict[str, Any], strategy: str, counter: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ldvh-prepare-replay-") as temporary:
        workspace, project, path, object_uid = _fixture(Path(temporary), task["fact_type_key"], counter)
        counters = {"helper_calls": 0, "request_chars": 0}
        transformations: list[str] = []
        if strategy == "known-contract":
            if task["discovery_mode"] == "cold":
                _call(None, "capabilities", {}, counters)
                transformations.append("discover-update-contract")
            read = _call(
                "read-fact-objects",
                "call",
                {
                    "work_object_locators": [str(project)],
                    "arguments": {
                        "workspace_root": str(workspace),
                        "fact_refs": [{"object_uid": object_uid}],
                    },
                },
                counters,
            )
            item = read["result"]["items"][0]
            transformations.extend(["extract-read-item", "strip-managed-fields", "compose-write-request"])
            request = {
                "arguments": {
                    "fact_ref": {"object_uid": object_uid},
                    "expected_content_fingerprint": item["content_fingerprint"],
                    "fact_object": _managed_draft(item["fact_object"], item["carrier"]),
                },
                "observed_context": {
                    "signature": {
                        "product_name": None,
                        "model_name": None,
                    }
                },
            }
            target_operation = "update-workcase" if task["fact_type_key"] == "workcase" else "update-fact-object"
        else:
            prepared = _call(
                "prepare-fact-object-update",
                "call",
                {
                    "work_object_locators": [str(project)],
                    "arguments": {
                        "workspace_root": str(workspace),
                        "fact_ref": {"object_uid": object_uid},
                    },
                },
                counters,
            )
            request = deepcopy(prepared["result"]["request_draft"])
            target_operation = prepared["result"]["target_operation"]
            transformations.append("consume-request-draft")

        branch = task["branch"]
        _mutate_request(request, task["fact_type_key"], branch)
        transformations.extend(["apply-branch-change", "supply-observed-signature"])
        if branch == "stale":
            path.write_bytes(path.read_bytes() + b"\n")
        request["work_object_locators"] = [str(project)]
        request["arguments"]["workspace_root"] = str(workspace)
        before_write = path.read_bytes()
        response = _call(target_operation, "call", request, counters)
        after_write = path.read_bytes()
        expected_success = branch == "positive"
        expected_outcome_met = response["outcome"] == "ok" if expected_success else response["outcome"] != "ok"
        state_changed = before_write != after_write
        zero_write_failure = None if expected_success else not state_changed and response["changes"] == []
        return {
            "task_id": task["task_id"],
            "task_hash": canonical_sha256(task),
            "fact_type_key": task["fact_type_key"],
            "branch": branch,
            "discovery_mode": task["discovery_mode"],
            "strategy": strategy,
            "helper_calls": counters["helper_calls"],
            "shell_invocations": 0,
            "request_chars": counters["request_chars"],
            "caller_transformations": len(transformations),
            "expected_outcome_met": expected_outcome_met,
            "state_changed": state_changed,
            "zero_write_failure": zero_write_failure,
            "host_receipt": "unavailable",
            "input_tokens": "unavailable",
            "output_tokens": "unavailable",
            "cache_read_tokens": "unavailable",
            "wall_ms": "unavailable",
            "queue_ms": "unavailable",
        }


def record_problems(records: list[dict[str, Any]], protocol: dict[str, Any]) -> tuple[str, ...]:
    problems: list[str] = []
    tasks = protocol["tasks"]
    expected = {(task["task_id"], strategy) for task in tasks for strategy in STRATEGIES}
    observed = {(record.get("task_id"), record.get("strategy")) for record in records}
    if observed != expected or len(records) != TASK_COUNT * len(STRATEGIES):
        problems.append("record-balance")
    for record in records:
        if set(record) != RETAINED_RECORD_FIELDS:
            problems.append("record-fields")
        if _all_keys(record) & _DENIED_KEYS:
            problems.append("record-privacy")
        if record.get("expected_outcome_met") is not True:
            problems.append("unexpected-outcome")
        if record.get("branch") == "positive" and record.get("state_changed") is not True:
            problems.append("positive-not-written")
        if record.get("branch") != "positive" and record.get("zero_write_failure") is not True:
            problems.append("failure-wrote")
    return tuple(sorted(set(problems)))


def _aggregate(records: list[dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    by_mode: dict[str, Any] = {}
    for mode in ("minimal", "cold"):
        members = [record for record in records if record["discovery_mode"] == mode]
        strategies: dict[str, Any] = {}
        for strategy in STRATEGIES:
            rows = [record for record in members if record["strategy"] == strategy]
            strategies[strategy] = {
                "tasks": len(rows),
                "helper_calls_total": sum(record["helper_calls"] for record in rows),
                "helper_calls_per_task": sum(record["helper_calls"] for record in rows) / len(rows),
                "shell_invocations_total": sum(record["shell_invocations"] for record in rows),
                "request_chars_total": sum(record["request_chars"] for record in rows),
                "caller_transformations_total": sum(record["caller_transformations"] for record in rows),
            }
        by_mode[mode] = strategies
    minimal = by_mode["minimal"]
    cold = by_mode["cold"]
    return {
        "task_count": TASK_COUNT,
        "record_count": len(records),
        "all_expected_outcomes_met": all(record["expected_outcome_met"] for record in records),
        "all_failure_branches_zero_write": all(
            record["zero_write_failure"] is True for record in records if record["branch"] != "positive"
        ),
        "fact_type_coverage": sorted({record["fact_type_key"] for record in records}),
        "branch_coverage": sorted({record["branch"] for record in records}),
        "by_discovery_mode": by_mode,
        "minimal_known_contract_helper_calls": {
            "baseline": minimal["known-contract"]["helper_calls_per_task"],
            "prepare": minimal["prepare"]["helper_calls_per_task"],
            "difference": minimal["prepare"]["helper_calls_per_task"]
            - minimal["known-contract"]["helper_calls_per_task"],
            "interpretation": "parity-only",
        },
        "cold_discovery_helper_calls": {
            "baseline": cold["known-contract"]["helper_calls_per_task"],
            "prepare": cold["prepare"]["helper_calls_per_task"],
            "difference": cold["prepare"]["helper_calls_per_task"]
            - cold["known-contract"]["helper_calls_per_task"],
            "interpretation": "one-mechanical-call-reduction",
        },
        "task_package_sha256": protocol["task_package_sha256"],
    }


def run_replay(protocol: dict[str, Any]) -> dict[str, Any]:
    problems = validate_protocol(protocol)
    if problems:
        raise ValueError("invalid frozen protocol: " + ", ".join(problems))
    records: list[dict[str, Any]] = []
    for task_index, task in enumerate(protocol["tasks"], start=1):
        for strategy_index, strategy in enumerate(STRATEGIES):
            records.append(_run_strategy(task, strategy, task_index * 10 + strategy_index))
    problems = record_problems(records, protocol)
    if problems:
        raise ValueError("invalid replay records: " + ", ".join(problems))
    return {
        "caliber": CALIBER,
        "protocol_sha256": canonical_sha256(protocol),
        "evidence_class": "deterministic-isolated-fixture-integration",
        "records": records,
        "summary": _aggregate(records, protocol),
        "unavailable_metrics": [
            "host_receipt",
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "wall_ms",
            "queue_ms",
        ],
        "limitations": [
            "No real-task, representative-sample, fresh-agent, host-delivery, causal, or broad service-quality claim.",
            (
                "Helper calls are in-process service-boundary calls; shell invocations are counted separately "
                "and remain zero."
            ),
            "Fixture setup and temporary Git initialization are infrastructure, not strategy roundtrips.",
        ],
    }


def _report_row(mode: str, strategy: str, values: dict[str, Any]) -> str:
    parts = [
        mode,
        strategy,
        str(values["tasks"]),
        f"{values['helper_calls_per_task']:.1f}",
        str(values["shell_invocations_total"]),
        str(values["request_chars_total"]),
        str(values["caller_transformations_total"]),
    ]
    return "| " + " | ".join(parts) + " |"


def render_report(results: dict[str, Any]) -> str:
    summary = results["summary"]
    modes = summary["by_discovery_mode"]
    minimal = summary["minimal_known_contract_helper_calls"]
    cold = summary["cold_discovery_helper_calls"]
    rows = [
        _report_row("minimal", "known-contract", modes["minimal"]["known-contract"]),
        _report_row("minimal", "prepare", modes["minimal"]["prepare"]),
        _report_row("cold", "known-contract", modes["cold"]["known-contract"]),
        _report_row("cold", "prepare", modes["cold"]["prepare"]),
    ]
    lines = [
        "# WC-E prepare-update deterministic fixture replay",
        "",
        "## Frozen execution",
        "",
        f"- Tasks: **{summary['task_count']}**; strategy records: **{summary['record_count']}**.",
        "- Evidence class: **deterministic isolated fixture integration**.",
        f"- Fact types: `{', '.join(summary['fact_type_coverage'])}`.",
        f"- Branches: `{', '.join(summary['branch_coverage'])}`.",
        f"- All expected outcomes met: **{str(summary['all_expected_outcomes_met']).lower()}**.",
        f"- All failing branches zero-write: **{str(summary['all_failure_branches_zero_write']).lower()}**.",
        "",
        "## Mechanical interaction counts",
        "",
        (
            "| Discovery mode | Strategy | Tasks | Helper calls/task | Shell invocations | "
            "Request chars total | Caller transformations total |"
        ),
        "|---|---|---:|---:|---:|---:|---:|",
        *rows,
        "",
        (
            "The minimal known-contract comparison is **parity only**: "
            f"`{minimal['baseline']:.1f} → {minimal['prepare']:.1f}` Helper calls/task. "
            f"The cold-discovery comparison is `{cold['baseline']:.1f} → {cold['prepare']:.1f}`, "
            "one mechanical Helper call fewer because the source-defined prepare operation removes the separate "
            "capabilities-discovery call in this frozen setup. Helper calls and shell invocations are separate "
            "metrics; strategy shell invocations were zero."
        ),
        "",
        (
            "Isolation terminology: each task-strategy member uses a fresh temporary Git repository and that "
            "repository's initial working tree. It does not exercise a linked worktree and is not evidence from "
            "the current project repository."
        ),
        "",
        (
            "Caller transformations count frozen, strategy-specific named workflow steps. A counted step is not "
            "a normalized unit of work or cognitive effort, so cross-strategy totals are descriptive fixture "
            "observations only."
        ),
        "",
        "## Evidence boundary",
        "",
        (
            "Host receipt, tokens, cache use, wall latency, and queue latency were unavailable and are not "
            "recorded as zero. Results retain labels, hashes, counts, booleans, and aggregates only; no raw "
            "request, full fact, signature, authorization, path, session, transcript, or secret is retained."
        ),
        "",
        (
            "This is deterministic isolated-fixture integration evidence only. It is not real-task or "
            "representative evidence, does not establish host delivery, and supports no causal or broad "
            "service-quality conclusion."
        ),
        "",
        f"Protocol SHA-256: `{results['protocol_sha256']}`.",
        f"Task package SHA-256: `{summary['task_package_sha256']}`.",
        "",
    ]
    return "\n".join(lines)


def regenerate(protocol: dict[str, Any]) -> tuple[dict[str, Any], str]:
    results = run_replay(protocol)
    return results, render_report(results)


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    results, report = regenerate(protocol)
    args.results.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
