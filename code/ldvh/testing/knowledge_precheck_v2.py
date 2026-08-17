"""Source-complete L0 incremental-value experiment helpers.

This module is deliberately separate from :mod:`knowledge_precheck_factorial`.
The v1 module validates a synthetic, packet-delivery experiment.  This v2
module freezes a real L0/L1 protocol, gates the only two knowledge-reading
Helper operations, and compiles a closed evidence bundle without trusting
precomputed records, results, or reports.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from ldvh.testing.helper_interaction_factorial import paired_estimate

SCHEMA_VERSION = "ldvh-knowledge-precheck-v2/1"
EVIDENCE_SCHEMA_VERSION = "ldvh-knowledge-precheck-v2-evidence/1"
CONDITIONS = ("l1-only", "l0-plus-l1")
TASK_FAMILIES = ("adr", "pitfall", "study")
CASE_KINDS = ("positive", "empty", "tempting-negative", "complex-partial")
ALLOWED_KNOWLEDGE_OPERATIONS = (
    "find-fact-object-candidates",
    "read-fact-objects",
)
TECHNICAL_EXCLUSION_CODES = (
    "missing_structured_output",
    "model_technical_failure",
    "runner_failure",
    "cross_condition_leakage",
)
RETAINED_PAIR_TARGET = 12
MAX_PAIR_ATTEMPTS = 15
MAX_REPLACEMENTS = 3
MAX_PROCESS_LAUNCHES = 30
RUN_TIMEOUT_SECONDS = 600
TOTAL_TIMEOUT_SECONDS = 18_000
L0_MAX_BYTES = 24 * 1024
L0_MAX_LINES = 200

_HEX64 = re.compile(r"[0-9a-f]{64}")
_TASK_FIELDS = frozenset(
    {
        "pair_id",
        "family",
        "case_kind",
        "confidence",
        "text_origin",
        "user_task",
        "source_refs",
        "gold",
    }
)
_GOLD_FIELDS = frozenset(
    {
        "applicable_refs",
        "tempting_nonapplicable_refs",
        "admissible_answer",
        "first_legal_action",
        "wrong_action_codes",
        "action_changed_definition",
        "strong_reuse_definition",
    }
)
_OUTPUT_FIELDS = frozenset(
    {
        "attempt_id",
        "pair_id",
        "condition",
        "model_name",
        "agent_runtime_name",
        "fresh_context_id_hash",
        "structured_response",
        "helper_exchange_ids",
        "usage",
        "latency",
    }
)
_RESPONSE_FIELDS = frozenset(
    {
        "decision",
        "selected_refs",
        "first_legal_action",
        "rationale_codes",
        "l1_triggered",
        "l1_trigger_family",
        "l1_trigger_reason_codes",
        "refusal_reason_codes",
    }
)
_SCORE_FIELDS = frozenset(
    {
        "attempt_id",
        "blind_packet_sha256",
        "scorer_model_name",
        "scorer_runtime_name",
        "fresh_scorer_context_id_hash",
        "condition_blind_attested",
        "selection_correct",
        "knowledge_adjusted_first_legal_action_correct",
        "action_changed",
        "strong_reuse",
        "correct_non_use",
        "false_f3_expansion",
        "scoring_notes",
    }
)
_BLIND_FIELDS = (
    "attempt_id",
    "response",
    "knowledge_trace",
    "gold",
    "rubric",
)
_EXCHANGE_FIELDS = frozenset(
    {
        "schema_version",
        "exchange_id",
        "attempt_id",
        "operation",
        "raw_request_utf8",
        "request_sha256",
        "raw_response_utf8",
        "response_sha256",
        "coverage",
        "match_reasons",
        "f3_objects",
        "state_changing_calls",
    }
)
_MODEL_INPUT_FIELDS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "pair_id",
        "family",
        "user_task",
        "condition",
        "fresh_context_id_hash",
        "l1_trigger_contract",
        "l0_packet",
        "knowledge_gateway_contract",
        "response_contract",
    }
)
_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "files",
        "protocol_file",
        "source_snapshot_file",
        "attempt_ledger_file",
        "model_input_files",
        "helper_exchange_files",
        "model_output_files",
        "blind_packet_files",
        "score_files",
        "adjudication_file",
    }
)


class KnowledgePrecheckV2Error(ValueError):
    """Raised when a frozen input or evidence boundary fails closed."""


def canonical_json_bytes(value: object) -> bytes:
    """Return deterministic compact UTF-8 JSON bytes."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: object) -> str:
    """Hash one JSON-compatible value under :func:`canonical_json_bytes`."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def logical_line_count(text: str) -> int:
    """Count logical lines without inventing a trailing empty line."""

    return 0 if not text else len(text.splitlines())


def _one_line(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise KnowledgePrecheckV2Error(f"{field} must be one non-empty logical line")
    return value


def _closed_mapping(value: object, fields: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise KnowledgePrecheckV2Error(f"{label} must use the exact closed field set")
    return value


def _hex64(value: object, field: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise KnowledgePrecheckV2Error(f"{field} must be a lowercase sha256")
    return value


def render_l0_packet(source_snapshot: Mapping[str, Any]) -> str:
    """Render the frozen task-independent L0 packet from its source snapshot."""

    adr_cards = source_snapshot.get("active_adr_f1")
    studies = source_snapshot.get("active_study_index")
    pitfalls = source_snapshot.get("selected_pitfalls")
    if not isinstance(adr_cards, list) or not isinstance(studies, list) or not isinstance(pitfalls, list):
        raise KnowledgePrecheckV2Error("source snapshot collections must be arrays")
    if len(adr_cards) != 5 or len(studies) != 21 or len(pitfalls) != 2:
        raise KnowledgePrecheckV2Error("source snapshot must contain 5 ADR, 21 Study, and 2 Pitfall entries")

    lines = [
        "# LDVH L0 knowledge packet",
        "",
        "This task-independent packet is navigation context, not a rule or fact-source replacement.",
        "Any status drift invalidates it. Apply a card only after checking its stated boundary.",
        "",
        "## Active ADR decision cards",
        "",
    ]
    for card in adr_cards:
        if not isinstance(card, Mapping):
            raise KnowledgePrecheckV2Error("ADR card must be an object")
        lines.extend(
            [
                f"### {card['object_id']} — {card['title']}",
                f"- UID: `{card['object_uid']}`",
                f"- Question: {card['decision_question']}",
                f"- Decision: {card['decision']}",
                f"- Applicability: {card['applicability']}",
                f"- Updated: {card['updated_at']}",
                "",
            ]
        )

    lines.extend(["## Human-selected Pitfall warnings", ""])
    for card in pitfalls:
        if not isinstance(card, Mapping):
            raise KnowledgePrecheckV2Error("Pitfall card must be an object")
        lines.extend(
            [
                f"### {card['object_id']} — {card['title']}",
                f"- UID: `{card['object_uid']}`",
                f"- Warning: {card['warning']}",
                f"- Applicability: {card['applicability']}",
                f"- Selection reason: {card['selection_reason']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Active Study index",
            "",
            "Use this index only to decide whether an on-demand F2/F3 lookup is warranted.",
            "",
        ]
    )
    for study in studies:
        if not isinstance(study, Mapping):
            raise KnowledgePrecheckV2Error("Study index entry must be an object")
        lines.append(f"- `{study['object_id']}` | {study['title']} | {study['updated_at']}")
    lines.extend(["", "Do not infer applicability or adoption from index membership alone."])
    return "\n".join(lines) + "\n"


def validate_protocol(protocol: Mapping[str, Any]) -> tuple[str, ...]:
    """Return deterministic frozen protocol problems; empty means valid."""

    problems: list[str] = []
    if protocol.get("schema_version") != SCHEMA_VERSION:
        problems.append("schema-version")
    if protocol.get("conditions") != list(CONDITIONS):
        problems.append("conditions")
    if protocol.get("allowed_knowledge_operations") != list(ALLOWED_KNOWLEDGE_OPERATIONS):
        problems.append("allowed-knowledge-operations")
    ceilings = protocol.get("ceilings")
    expected_ceilings = {
        "retained_pair_target": RETAINED_PAIR_TARGET,
        "maximum_pair_attempts": MAX_PAIR_ATTEMPTS,
        "maximum_replacements": MAX_REPLACEMENTS,
        "maximum_process_launches": MAX_PROCESS_LAUNCHES,
        "run_timeout_seconds": RUN_TIMEOUT_SECONDS,
        "total_timeout_seconds": TOTAL_TIMEOUT_SECONDS,
        "same_arm_retries": 0,
    }
    if ceilings != expected_ceilings:
        problems.append("ceilings")

    snapshot = protocol.get("source_snapshot")
    if not isinstance(snapshot, Mapping):
        problems.append("source-snapshot")
        snapshot = {}
    try:
        _hex64(snapshot.get("object_set_fingerprint"), "object_set_fingerprint")
        _hex64(snapshot.get("content_sha256"), "source_snapshot.content_sha256")
    except KnowledgePrecheckV2Error:
        problems.append("source-snapshot-fingerprint")

    l0 = protocol.get("l0_packet")
    if not isinstance(l0, Mapping):
        problems.append("l0-packet")
    else:
        content = l0.get("content")
        if not isinstance(content, str):
            problems.append("l0-content")
        else:
            actual_bytes = len(content.encode("utf-8"))
            actual_lines = logical_line_count(content)
            if l0.get("bytes") != actual_bytes or l0.get("lines") != actual_lines:
                problems.append("l0-measurement")
            if l0.get("sha256") != bytes_sha256(content.encode("utf-8")):
                problems.append("l0-hash")
            if actual_bytes > L0_MAX_BYTES or actual_lines > L0_MAX_LINES:
                problems.append("l0-cap")
        if l0.get("max_bytes") != L0_MAX_BYTES or l0.get("max_lines") != L0_MAX_LINES:
            problems.append("l0-cap-declaration")

    tasks = protocol.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != RETAINED_PAIR_TARGET:
        problems.append("task-count")
        tasks = []
    pair_ids: list[object] = []
    family_counts: Counter[object] = Counter()
    kind_counts: Counter[object] = Counter()
    medium_count = 0
    for task in tasks:
        if not isinstance(task, Mapping):
            problems.append("task-object")
            continue
        pair_id = task.get("pair_id")
        if set(task) != _TASK_FIELDS:
            problems.append(f"task-fields:{pair_id}")
        pair_ids.append(pair_id)
        family_counts[task.get("family")] += 1
        kind_counts[task.get("case_kind")] += 1
        if task.get("confidence") == "medium":
            medium_count += 1
            if task.get("text_origin") != "rewritten-for-v0.2-not-historical-verbatim":
                problems.append(f"medium-origin:{pair_id}")
        gold = task.get("gold")
        if not isinstance(gold, Mapping) or set(gold) != _GOLD_FIELDS:
            problems.append(f"gold-fields:{pair_id}")
        for field in ("pair_id", "family", "case_kind", "confidence", "text_origin", "user_task"):
            if not isinstance(task.get(field), str) or not str(task.get(field)).strip():
                problems.append(f"task-{field}:{pair_id}")
    if len(pair_ids) != len(set(pair_ids)):
        problems.append("pair-id-uniqueness")
    if family_counts != Counter({family: 4 for family in TASK_FAMILIES}):
        problems.append("family-balance")
    if kind_counts != Counter({kind: 3 for kind in CASE_KINDS}):
        problems.append("case-kind-balance")
    if medium_count != 5:
        problems.append("medium-task-count")

    orders = protocol.get("condition_orders")
    if not isinstance(orders, list) or len(orders) != RETAINED_PAIR_TARGET:
        problems.append("condition-order-count")
    elif Counter(tuple(order) for order in orders) != Counter(
        {("l1-only", "l0-plus-l1"): 6, ("l0-plus-l1", "l1-only"): 6}
    ):
        problems.append("condition-order-balance")

    thresholds = protocol.get("productization_thresholds")
    if thresholds != {
        "main_metric_net_gain_minimum": 3,
        "strong_reuse_intervention_only_net_gain_minimum": 2,
        "selection_correct_must_not_decrease": True,
        "empty_pair_ids": ["A2", "P2", "S2"],
        "empty_pairs_all_correct_non_use": True,
        "false_f3_total_increment_maximum": 2,
        "capacity_required": True,
        "source_complete_replay_required": True,
        "insufficient_evidence_decision": "do-not-support-productizing-l0",
    }:
        problems.append("productization-thresholds")
    denylist = protocol.get("artifact_denylist")
    if not isinstance(denylist, list) or not denylist or len(denylist) != len(set(denylist)):
        problems.append("artifact-denylist")
    return tuple(sorted(set(problems)))


def _denylisted_keys(value: object, denylist: set[str]) -> set[str]:
    if isinstance(value, Mapping):
        found = {str(key) for key in value if str(key) in denylist}
        for member in value.values():
            found.update(_denylisted_keys(member, denylist))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for member in value:
            found.update(_denylisted_keys(member, denylist))
        return found
    return set()


def _validate_gateway_request(operation: str, request: Mapping[str, Any]) -> None:
    if operation not in ALLOWED_KNOWLEDGE_OPERATIONS:
        raise KnowledgePrecheckV2Error(f"operation is not allowlisted: {operation}")
    if set(request) != {"arguments"} or not isinstance(request.get("arguments"), Mapping):
        raise KnowledgePrecheckV2Error("gateway request must contain only arguments")
    arguments = request["arguments"]
    if "workspace_root" in arguments:
        raise KnowledgePrecheckV2Error("gateway forbids arguments.workspace_root")
    if operation == "find-fact-object-candidates":
        if arguments.get("card_layer") != "F2":
            raise KnowledgePrecheckV2Error("knowledge discovery must request F2")
        if arguments.get("governed_project_id") != "ldvh":
            raise KnowledgePrecheckV2Error("knowledge discovery is bound to project ldvh")
        if set(arguments) != {
            "governed_project_id",
            "card_layer",
            "fact_type_keys",
            "statuses",
        }:
            raise KnowledgePrecheckV2Error("F2 request must use the exact broad active-family shape")
        fact_types = arguments.get("fact_type_keys")
        if not isinstance(fact_types, list) or len(fact_types) != 1 or fact_types[0] not in TASK_FAMILIES:
            raise KnowledgePrecheckV2Error("knowledge discovery fact types are not allowlisted")
        if arguments.get("statuses") != ["active"]:
            raise KnowledgePrecheckV2Error("knowledge discovery must be restricted to active objects")
    else:
        if set(arguments) != {"fact_refs"}:
            raise KnowledgePrecheckV2Error("F3 request must contain only exact fact refs")
        refs = arguments.get("fact_refs")
        if not isinstance(refs, list) or not refs or len(refs) > 2:
            raise KnowledgePrecheckV2Error("F3 read requires one or two exact fact refs")
        if any(not isinstance(ref, Mapping) or set(ref) != {"object_uid"} for ref in refs):
            raise KnowledgePrecheckV2Error("F3 refs must be exact object_uid references")


class ReadOnlyKnowledgeGateway:
    """Fail-closed gateway for real F2 discovery and exact F3 reads."""

    def __init__(
        self,
        dispatch: Callable[[str, bytes], bytes],
        *,
        expected_object_set_fingerprint: str,
        expected_f3_fingerprints: Mapping[str, str] | None = None,
    ) -> None:
        self._dispatch = dispatch
        self._expected_object_set_fingerprint = _hex64(
            expected_object_set_fingerprint, "expected_object_set_fingerprint"
        )
        self._expected_f3_fingerprints = dict(expected_f3_fingerprints or {})
        self._exchanges: list[dict[str, Any]] = []

    @property
    def exchanges(self) -> tuple[dict[str, Any], ...]:
        return tuple(deepcopy(self._exchanges))

    def call(
        self,
        operation: str,
        request: Mapping[str, Any],
        *,
        exchange_id: str,
        attempt_id: str,
    ) -> dict[str, Any]:
        _one_line(exchange_id, "exchange_id")
        _one_line(attempt_id, "attempt_id")
        if any(exchange["exchange_id"] == exchange_id for exchange in self._exchanges):
            raise KnowledgePrecheckV2Error("exchange_id must be unique")
        _validate_gateway_request(operation, request)
        request_bytes = canonical_json_bytes(request)
        response_bytes = self._dispatch(operation, request_bytes)
        if not isinstance(response_bytes, bytes):
            raise KnowledgePrecheckV2Error("dispatch must return bytes")
        try:
            response = json.loads(response_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise KnowledgePrecheckV2Error("Helper response is not UTF-8 JSON") from error
        if not isinstance(response, Mapping):
            raise KnowledgePrecheckV2Error("Helper response must be an object")
        if response.get("operation_key") != operation or response.get("outcome") != "ok":
            raise KnowledgePrecheckV2Error("Helper response operation/outcome mismatch")
        if response.get("changes") != []:
            raise KnowledgePrecheckV2Error("knowledge gateway observed a state-changing response")

        coverage: dict[str, Any] | None = None
        match_reasons: list[dict[str, Any]] = []
        f3_objects: list[dict[str, str]] = []
        result = response.get("result")
        if not isinstance(result, Mapping):
            raise KnowledgePrecheckV2Error("Helper response has no result object")
        if operation == "find-fact-object-candidates":
            raw_coverage = result.get("coverage")
            if not isinstance(raw_coverage, Mapping) or raw_coverage.get("status") != "complete":
                raise KnowledgePrecheckV2Error("F2 coverage is not complete")
            observed_fingerprint = raw_coverage.get("object_set_fingerprint")
            if observed_fingerprint != self._expected_object_set_fingerprint:
                raise KnowledgePrecheckV2Error("F2 object set drifted")
            coverage = {
                "status": raw_coverage.get("status"),
                "total_matching": raw_coverage.get("total_matching"),
                "returned": raw_coverage.get("returned"),
                "object_set_fingerprint": observed_fingerprint,
            }
            cards = result.get("cards")
            if not isinstance(cards, list):
                raise KnowledgePrecheckV2Error("F2 cards must be an array")
            for card in cards:
                if not isinstance(card, Mapping) or not isinstance(card.get("match_reasons"), list):
                    raise KnowledgePrecheckV2Error("F2 card has no match reasons")
                match_reasons.extend(deepcopy(card["match_reasons"]))
        else:
            items = result.get("items")
            if not isinstance(items, list) or not items:
                raise KnowledgePrecheckV2Error("F3 read returned no items")
            for item in items:
                if not isinstance(item, Mapping) or item.get("check_status") != "mechanically_valid":
                    raise KnowledgePrecheckV2Error("F3 item is not mechanically valid")
                fact_object = item.get("fact_object")
                if not isinstance(fact_object, Mapping):
                    raise KnowledgePrecheckV2Error("F3 item has no fact object")
                identity = fact_object.get("frontmatter", fact_object)
                resolved_ref = item.get("resolved_ref")
                if not isinstance(identity, Mapping) or not isinstance(resolved_ref, Mapping):
                    raise KnowledgePrecheckV2Error("F3 item has no normalized identity")
                uid = _one_line(resolved_ref.get("object_uid"), "F3 object_uid")
                if identity.get("object_uid") not in (None, uid):
                    raise KnowledgePrecheckV2Error("F3 fact identity does not match resolved ref")
                fact_type_key = _one_line(identity.get("fact_type_key"), "F3 fact_type_key")
                if fact_type_key not in TASK_FAMILIES:
                    raise KnowledgePrecheckV2Error("F3 object type is not a knowledge family")
                fingerprint = _hex64(item.get("content_fingerprint"), "F3 content_fingerprint")
                expected = self._expected_f3_fingerprints.get(uid)
                if self._expected_f3_fingerprints and expected is None:
                    raise KnowledgePrecheckV2Error(f"F3 object is not frozen: {uid}")
                if expected is not None and fingerprint != expected:
                    raise KnowledgePrecheckV2Error(f"F3 source drifted: {uid}")
                f3_objects.append(
                    {
                        "object_uid": uid,
                        "fact_type_key": fact_type_key,
                        "content_fingerprint": fingerprint,
                    }
                )
            requested_uids = [ref["object_uid"] for ref in request["arguments"]["fact_refs"]]
            returned_uids = [item["object_uid"] for item in f3_objects]
            if len(returned_uids) != len(set(returned_uids)) or set(returned_uids) != set(requested_uids):
                raise KnowledgePrecheckV2Error("F3 response does not exactly match requested refs")

        exchange = {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "exchange_id": exchange_id,
            "attempt_id": attempt_id,
            "operation": operation,
            "raw_request_utf8": request_bytes.decode("utf-8"),
            "request_sha256": bytes_sha256(request_bytes),
            "raw_response_utf8": response_bytes.decode("utf-8"),
            "response_sha256": bytes_sha256(response_bytes),
            "coverage": coverage,
            "match_reasons": match_reasons,
            "f3_objects": f3_objects,
            "state_changing_calls": 0,
        }
        self._exchanges.append(exchange)
        return deepcopy(exchange)


def subprocess_helper_dispatch(
    *, repository_root: Path, ldvh_executable: Path, timeout_seconds: int = 30
) -> Callable[[str, bytes], bytes]:
    """Return a real CLI dispatcher suitable for :class:`ReadOnlyKnowledgeGateway`."""

    root = repository_root.resolve(strict=True)
    executable = ldvh_executable.resolve(strict=True)

    def dispatch(operation: str, request_bytes: bytes) -> bytes:
        _validate_gateway_request(operation, json.loads(request_bytes))
        with tempfile.NamedTemporaryFile(prefix="ldvh-kp-v2-", suffix=".json") as request_file:
            request_file.write(request_bytes)
            request_file.flush()
            completed = subprocess.run(
                [str(executable), "call", operation, "--request", request_file.name],
                cwd=root,
                input=b"",
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        if completed.stderr:
            raise KnowledgePrecheckV2Error("Helper CLI wrote to stderr")
        if completed.returncode != 0:
            raise KnowledgePrecheckV2Error(f"Helper CLI failed with exit {completed.returncode}")
        return completed.stdout

    return dispatch


def build_model_input_packet(
    protocol: Mapping[str, Any],
    *,
    pair_id: str,
    condition: str,
    attempt_id: str,
    fresh_context_id_hash: str,
) -> dict[str, Any]:
    """Build the exact bounded input shown to one fresh member-run context."""

    if validate_protocol(protocol):
        raise KnowledgePrecheckV2Error("cannot build input from an invalid protocol")
    _one_line(attempt_id, "attempt_id")
    _hex64(fresh_context_id_hash, "fresh_context_id_hash")
    if condition not in CONDITIONS:
        raise KnowledgePrecheckV2Error("condition is invalid")
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}
    task = tasks.get(pair_id)
    if task is None:
        raise KnowledgePrecheckV2Error("pair is not frozen")
    packet = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "attempt_id": attempt_id,
        "pair_id": pair_id,
        "family": task["family"],
        "user_task": task["user_task"],
        "condition": condition,
        "fresh_context_id_hash": fresh_context_id_hash,
        "l1_trigger_contract": deepcopy(protocol["l1_trigger_contract"]),
        "l0_packet": protocol["l0_packet"]["content"] if condition == "l0-plus-l1" else None,
        "knowledge_gateway_contract": {
            "allowed_operations": list(ALLOWED_KNOWLEDGE_OPERATIONS),
            "direct_ldvh_calls_forbidden": True,
            "state_changes_forbidden": True,
            "f2_layer": "F2",
            "f2_project": "ldvh",
            "f2_fact_type_must_match_family": True,
            "f3_exact_uid_only": True,
            "f3_refs_per_call_maximum": 2,
            "workspace_root_argument_forbidden": True,
            "lookup_is_optional_until_l1_triggered": True,
        },
        "response_contract": {
            "exact_fields": sorted(_RESPONSE_FIELDS),
            "decision_values": ["use", "non-use", "ambiguous"],
            "first_legal_action_format": "one-non-empty-line-action-code",
            "selected_refs_format": "array-of-object-uids",
            "reason_code_fields_are_arrays": True,
            "l1_trigger_family_values": [None, *TASK_FAMILIES],
        },
    }
    if set(packet) != _MODEL_INPUT_FIELDS:
        raise AssertionError("model input packet shape drifted")
    return packet


def validate_model_input_packet(packet: Mapping[str, Any], protocol: Mapping[str, Any]) -> None:
    """Reject a member-run input that is not the deterministic frozen projection."""

    _closed_mapping(packet, _MODEL_INPUT_FIELDS, "model input")
    expected = build_model_input_packet(
        protocol,
        pair_id=packet["pair_id"],
        condition=packet["condition"],
        attempt_id=packet["attempt_id"],
        fresh_context_id_hash=packet["fresh_context_id_hash"],
    )
    if packet != expected:
        raise KnowledgePrecheckV2Error("model input does not match deterministic projection")


def validate_model_output(output: Mapping[str, Any], protocol: Mapping[str, Any]) -> None:
    _closed_mapping(output, _OUTPUT_FIELDS, "model output")
    if output.get("condition") not in CONDITIONS:
        raise KnowledgePrecheckV2Error("model output condition is invalid")
    _hex64(output.get("fresh_context_id_hash"), "fresh_context_id_hash")
    response = _closed_mapping(output.get("structured_response"), _RESPONSE_FIELDS, "structured response")
    if response.get("decision") not in {"use", "non-use", "ambiguous"}:
        raise KnowledgePrecheckV2Error("decision is invalid")
    array_fields = (
        "selected_refs",
        "rationale_codes",
        "l1_trigger_reason_codes",
        "refusal_reason_codes",
    )
    if any(not isinstance(response.get(field), list) for field in array_fields):
        raise KnowledgePrecheckV2Error("structured response arrays are invalid")
    for field in array_fields:
        if any(not isinstance(item, str) or not item or "\n" in item for item in response[field]):
            raise KnowledgePrecheckV2Error(f"structured response {field} entries are invalid")
    _one_line(response.get("first_legal_action"), "first_legal_action")
    if type(response.get("l1_triggered")) is not bool:
        raise KnowledgePrecheckV2Error("l1_triggered must be a boolean")
    trigger_family = response.get("l1_trigger_family")
    if trigger_family not in (None, *TASK_FAMILIES):
        raise KnowledgePrecheckV2Error("l1_trigger_family is invalid")
    if response["l1_triggered"] != (trigger_family is not None):
        raise KnowledgePrecheckV2Error("L1 trigger flag and family are inconsistent")
    if not isinstance(output.get("helper_exchange_ids"), list):
        raise KnowledgePrecheckV2Error("helper_exchange_ids must be an array")
    if output.get("usage") not in ("unavailable", None) and not isinstance(output.get("usage"), Mapping):
        raise KnowledgePrecheckV2Error("usage must be unavailable, null, or an object")
    if output.get("latency") not in ("unavailable", None) and not isinstance(output.get("latency"), Mapping):
        raise KnowledgePrecheckV2Error("latency must be unavailable, null, or an object")
    task_ids = {task["pair_id"] for task in protocol["tasks"]}
    if output.get("pair_id") not in task_ids:
        raise KnowledgePrecheckV2Error("model output pair is not frozen")


def build_blind_packet(
    output: Mapping[str, Any],
    task: Mapping[str, Any],
    exchanges: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the exact condition-blind scorer input."""

    trace: list[dict[str, Any]] = []
    for exchange in exchanges:
        trace.append(
            {
                "operation": exchange["operation"],
                "coverage": exchange["coverage"],
                "match_reasons": exchange["match_reasons"],
                "f3_objects": exchange["f3_objects"],
            }
        )
    packet = {
        "attempt_id": output["attempt_id"],
        "response": deepcopy(output["structured_response"]),
        "knowledge_trace": trace,
        "gold": deepcopy(task["gold"]),
        "rubric": {
            "binary_metrics": [
                "selection_correct",
                "knowledge_adjusted_first_legal_action_correct",
                "action_changed",
                "strong_reuse",
                "correct_non_use",
            ],
            "count_metrics": ["false_f3_expansion"],
            "arm_and_pair_counterpart_hidden": True,
            "definitions": {
                "selection_correct": "Selected refs contain all and only applicable_refs.",
                "knowledge_adjusted_first_legal_action_correct": (
                    "first_legal_action matches the frozen first legal action in substance."
                ),
                "action_changed": (
                    "The response demonstrates that bounded knowledge changed the action, plan, "
                    "investigation scope, validation order, or risk treatment; lookup alone is zero."
                ),
                "strong_reuse": ("At least one applicable object is selected and substantively changes the action."),
                "correct_non_use": (
                    "When applicable_refs is empty, the response declines knowledge reuse and still "
                    "chooses the frozen first legal action."
                ),
                "false_f3_expansion": (
                    "Count F3 objects outside applicable_refs that the response needlessly expanded."
                ),
            },
        },
    }
    if tuple(packet) != _BLIND_FIELDS:
        raise AssertionError("blind packet shape drifted")
    encoded = canonical_json_bytes(packet)
    if b'"condition"' in encoded or b"l0-plus-l1" in encoded or b"l1-only" in encoded:
        raise KnowledgePrecheckV2Error("blind packet leaks condition")
    return packet


def validate_score(score: Mapping[str, Any]) -> None:
    _closed_mapping(score, _SCORE_FIELDS, "score")
    _hex64(score.get("blind_packet_sha256"), "blind_packet_sha256")
    _hex64(score.get("fresh_scorer_context_id_hash"), "fresh_scorer_context_id_hash")
    if score.get("scorer_model_name") is not None:
        raise KnowledgePrecheckV2Error("unobservable scorer model name must be null")
    if score.get("scorer_runtime_name") != "codex-native-subagent":
        raise KnowledgePrecheckV2Error("scorer runtime identity is invalid")
    if score.get("condition_blind_attested") is not True:
        raise KnowledgePrecheckV2Error("score must attest condition-blind input")
    for field in (
        "selection_correct",
        "knowledge_adjusted_first_legal_action_correct",
        "action_changed",
        "strong_reuse",
        "correct_non_use",
    ):
        if score.get(field) not in (0, 1):
            raise KnowledgePrecheckV2Error(f"score {field} must be 0 or 1")
    if type(score.get("false_f3_expansion")) is not int or score["false_f3_expansion"] < 0:
        raise KnowledgePrecheckV2Error("false_f3_expansion must be a non-negative integer")
    notes = score.get("scoring_notes")
    if (
        not isinstance(notes, list)
        or not notes
        or any(not isinstance(note, str) or not note or "\n" in note for note in notes)
    ):
        raise KnowledgePrecheckV2Error("scoring_notes must be a non-empty one-line array")


def _read_json(root: Path, relative: str) -> Any:
    path = (root / relative).resolve(strict=True)
    if root not in path.parents:
        raise KnowledgePrecheckV2Error("manifest path escapes bundle root")
    return json.loads(path.read_bytes())


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise KnowledgePrecheckV2Error(f"{field} must be an RFC3339 UTC timestamp")
    try:
        return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as error:
        raise KnowledgePrecheckV2Error(f"{field} must be an RFC3339 UTC timestamp") from error


def _manifest_files(manifest: Mapping[str, Any]) -> dict[str, str]:
    files = manifest.get("files")
    if not isinstance(files, Mapping) or not files:
        raise KnowledgePrecheckV2Error("manifest.files must be a non-empty object")
    normalized: dict[str, str] = {}
    for relative, digest in files.items():
        relative = _one_line(relative, "manifest file")
        if relative.startswith("/") or ".." in Path(relative).parts or relative == "manifest.json":
            raise KnowledgePrecheckV2Error("manifest file path is invalid")
        normalized[relative] = _hex64(digest, f"manifest digest {relative}")
    return normalized


def compile_evidence_bundle(bundle_root: Path) -> dict[str, bytes]:
    """Compile records, results, and report from a closed source-complete bundle."""

    root = bundle_root.resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_bytes())
    if (
        not isinstance(manifest, Mapping)
        or set(manifest) != _MANIFEST_FIELDS
        or manifest.get("schema_version") != EVIDENCE_SCHEMA_VERSION
    ):
        raise KnowledgePrecheckV2Error("evidence manifest schema is invalid")
    files = _manifest_files(manifest)
    actual = {
        str(path.relative_to(root)) for path in root.rglob("*") if path.is_file() and path.name != "manifest.json"
    }
    if actual != set(files):
        missing = sorted(set(files) - actual)
        extra = sorted(actual - set(files))
        raise KnowledgePrecheckV2Error(f"bundle file closure mismatch: missing={missing}, extra={extra}")
    for relative, digest in files.items():
        if bytes_sha256((root / relative).read_bytes()) != digest:
            raise KnowledgePrecheckV2Error(f"bundle hash mismatch: {relative}")

    protocol = _read_json(root, manifest["protocol_file"])
    if not isinstance(protocol, Mapping) or validate_protocol(protocol):
        raise KnowledgePrecheckV2Error("frozen protocol is invalid")
    snapshot = _read_json(root, manifest["source_snapshot_file"])
    if canonical_sha256(snapshot) != protocol["source_snapshot"]["content_sha256"]:
        raise KnowledgePrecheckV2Error("source snapshot hash mismatch")
    if render_l0_packet(snapshot) != protocol["l0_packet"]["content"]:
        raise KnowledgePrecheckV2Error("L0 packet is not derived from the frozen snapshot")
    denylist = set(protocol["artifact_denylist"])

    attempt_ledger = _read_json(root, manifest["attempt_ledger_file"])
    if not isinstance(attempt_ledger, Mapping) or set(attempt_ledger) != {
        "pair_attempts",
        "technical_replacements",
        "process_launches",
        "launches",
    }:
        raise KnowledgePrecheckV2Error("attempt ledger shape is invalid")
    pair_attempts = attempt_ledger["pair_attempts"]
    replacements = attempt_ledger["technical_replacements"]
    launches = attempt_ledger["process_launches"]
    launch_rows = attempt_ledger["launches"]
    if type(pair_attempts) is not int or not RETAINED_PAIR_TARGET <= pair_attempts <= MAX_PAIR_ATTEMPTS:
        raise KnowledgePrecheckV2Error("pair attempt ceiling is invalid")
    if type(replacements) is not list or len(replacements) > MAX_REPLACEMENTS:
        raise KnowledgePrecheckV2Error("replacement ceiling is invalid")
    if type(launches) is not int or not RETAINED_PAIR_TARGET * 2 <= launches <= MAX_PROCESS_LAUNCHES:
        raise KnowledgePrecheckV2Error("process launch ceiling is invalid")
    if not isinstance(launch_rows, list) or len(launch_rows) != launches:
        raise KnowledgePrecheckV2Error("process launch ledger coverage is invalid")
    if pair_attempts != RETAINED_PAIR_TARGET + len(replacements):
        raise KnowledgePrecheckV2Error("pair attempt/replacement accounting is inconsistent")
    for replacement in replacements:
        if not isinstance(replacement, Mapping) or set(replacement) != {
            "pair_id",
            "exclusion_code",
        }:
            raise KnowledgePrecheckV2Error("replacement ledger entry shape is invalid")
        if replacement["exclusion_code"] not in TECHNICAL_EXCLUSION_CODES:
            raise KnowledgePrecheckV2Error("replacement uses a nontechnical exclusion")

    launch_by_attempt: dict[str, Mapping[str, Any]] = {}
    started_times: list[datetime] = []
    finished_times: list[datetime] = []
    pair_launches: dict[str, list[str]] = {}
    for index, launch in enumerate(launch_rows, start=1):
        if not isinstance(launch, Mapping) or set(launch) != {
            "sequence",
            "attempt_id",
            "pair_id",
            "condition",
            "started_at",
            "finished_at",
        }:
            raise KnowledgePrecheckV2Error("process launch row shape is invalid")
        if launch["sequence"] != index:
            raise KnowledgePrecheckV2Error("process launch sequence is not contiguous")
        attempt_id = _one_line(launch["attempt_id"], "launch attempt_id")
        if attempt_id in launch_by_attempt:
            raise KnowledgePrecheckV2Error("process launch attempt id is duplicated")
        started = _timestamp(launch["started_at"], "launch started_at")
        finished = _timestamp(launch["finished_at"], "launch finished_at")
        elapsed = (finished - started).total_seconds()
        if elapsed < 0 or elapsed > RUN_TIMEOUT_SECONDS:
            raise KnowledgePrecheckV2Error("member run exceeded its frozen timeout")
        started_times.append(started)
        finished_times.append(finished)
        launch_by_attempt[attempt_id] = launch
        pair_launches.setdefault(str(launch["pair_id"]), []).append(str(launch["condition"]))
    if started_times and (max(finished_times) - min(started_times)).total_seconds() > TOTAL_TIMEOUT_SECONDS:
        raise KnowledgePrecheckV2Error("trial exceeded its frozen total timeout")
    tasks_by_id = {task["pair_id"]: task for task in protocol["tasks"]}
    for index, pair_id in enumerate(tasks_by_id):
        if pair_launches.get(pair_id) != protocol["condition_orders"][index]:
            raise KnowledgePrecheckV2Error("actual member runs violate frozen condition order")

    model_inputs = [_read_json(root, path) for path in manifest["model_input_files"]]
    input_by_id: dict[str, Mapping[str, Any]] = {}
    for packet in model_inputs:
        if not isinstance(packet, Mapping):
            raise KnowledgePrecheckV2Error("model input must be an object")
        validate_model_input_packet(packet, protocol)
        attempt_id = packet["attempt_id"]
        if attempt_id in input_by_id:
            raise KnowledgePrecheckV2Error("duplicate model input attempt id")
        launch = launch_by_attempt.get(attempt_id)
        if launch is None or launch["pair_id"] != packet["pair_id"] or launch["condition"] != packet["condition"]:
            raise KnowledgePrecheckV2Error("model input/process launch binding is invalid")
        input_by_id[attempt_id] = packet
    if set(input_by_id) != set(launch_by_attempt):
        raise KnowledgePrecheckV2Error("model input/process launch coverage is incomplete")

    exchanges = [_read_json(root, path) for path in manifest["helper_exchange_files"]]
    exchange_by_id: dict[str, Mapping[str, Any]] = {}
    for exchange in exchanges:
        if (
            not isinstance(exchange, Mapping)
            or set(exchange) != _EXCHANGE_FIELDS
            or exchange.get("schema_version") != EVIDENCE_SCHEMA_VERSION
        ):
            raise KnowledgePrecheckV2Error("helper exchange schema is invalid")
        if exchange.get("operation") not in ALLOWED_KNOWLEDGE_OPERATIONS:
            raise KnowledgePrecheckV2Error("helper exchange operation is not allowlisted")
        if exchange.get("state_changing_calls") != 0:
            raise KnowledgePrecheckV2Error("helper exchange records a state-changing call")
        request_bytes = str(exchange.get("raw_request_utf8", "")).encode("utf-8")
        response_bytes = str(exchange.get("raw_response_utf8", "")).encode("utf-8")
        if bytes_sha256(request_bytes) != exchange.get("request_sha256") or bytes_sha256(
            response_bytes
        ) != exchange.get("response_sha256"):
            raise KnowledgePrecheckV2Error("helper exchange raw bytes do not match hashes")
        try:
            raw_request = json.loads(request_bytes)
            raw_response = json.loads(response_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise KnowledgePrecheckV2Error("helper exchange raw bytes are not JSON") from error
        denied = _denylisted_keys(raw_request, denylist) | _denylisted_keys(raw_response, denylist)
        if denied:
            raise KnowledgePrecheckV2Error(f"helper exchange contains denylisted keys: {','.join(sorted(denied))}")
        exchange_id = _one_line(exchange.get("exchange_id"), "exchange_id")
        if exchange_id in exchange_by_id:
            raise KnowledgePrecheckV2Error("duplicate helper exchange id")
        attempt_id = _one_line(exchange.get("attempt_id"), "exchange attempt_id")
        input_packet = input_by_id.get(attempt_id)
        if input_packet is None:
            raise KnowledgePrecheckV2Error("helper exchange attempt is unknown")
        _validate_gateway_request(str(exchange["operation"]), raw_request)
        if exchange["operation"] == "find-fact-object-candidates" and raw_request["arguments"]["fact_type_keys"] != [
            input_packet["family"]
        ]:
            raise KnowledgePrecheckV2Error("F2 request family does not match member-run input")
        replay_gateway = ReadOnlyKnowledgeGateway(
            lambda _operation, _request, response_bytes=response_bytes: response_bytes,
            expected_object_set_fingerprint=protocol["source_snapshot"]["object_set_fingerprint"],
            expected_f3_fingerprints=snapshot["knowledge_ref_fingerprints"],
        )
        replayed = replay_gateway.call(
            str(exchange["operation"]),
            raw_request,
            exchange_id=exchange_id,
            attempt_id=attempt_id,
        )
        if replayed != exchange:
            raise KnowledgePrecheckV2Error("helper exchange derived fields do not replay from raw bytes")
        exchange_by_id[exchange_id] = exchange

    outputs = [_read_json(root, path) for path in manifest["model_output_files"]]
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}
    output_by_id: dict[str, Mapping[str, Any]] = {}
    pair_conditions: Counter[tuple[object, object]] = Counter()
    context_ids: set[object] = set()
    for output in outputs:
        if not isinstance(output, Mapping):
            raise KnowledgePrecheckV2Error("model output must be an object")
        validate_model_output(output, protocol)
        if _denylisted_keys(output, denylist):
            raise KnowledgePrecheckV2Error("model output contains a denylisted key")
        attempt_id = _one_line(output["attempt_id"], "attempt_id")
        if attempt_id in output_by_id:
            raise KnowledgePrecheckV2Error("duplicate model attempt id")
        input_packet = input_by_id.get(attempt_id)
        if input_packet is None:
            raise KnowledgePrecheckV2Error("model output has no bound input")
        if (
            input_packet["pair_id"] != output["pair_id"]
            or input_packet["condition"] != output["condition"]
            or input_packet["fresh_context_id_hash"] != output["fresh_context_id_hash"]
        ):
            raise KnowledgePrecheckV2Error("model output/input binding is invalid")
        if len(output["helper_exchange_ids"]) != len(set(output["helper_exchange_ids"])):
            raise KnowledgePrecheckV2Error("model output repeats a Helper exchange")
        bound_operations: list[str] = []
        for exchange_id in output["helper_exchange_ids"]:
            exchange = exchange_by_id.get(exchange_id)
            if exchange is None or exchange.get("attempt_id") != attempt_id:
                raise KnowledgePrecheckV2Error("model output helper exchange binding is invalid")
            bound_operations.append(str(exchange["operation"]))
            if any(item["fact_type_key"] != input_packet["family"] for item in exchange["f3_objects"]):
                raise KnowledgePrecheckV2Error("F3 object family does not match member-run input")
        if bound_operations.count("find-fact-object-candidates") > 1 or bound_operations.count("read-fact-objects") > 1:
            raise KnowledgePrecheckV2Error("member run exceeded its bounded F2/F3 call sequence")
        if "read-fact-objects" in bound_operations and bound_operations != [
            "find-fact-object-candidates",
            "read-fact-objects",
        ]:
            raise KnowledgePrecheckV2Error("member run did not preserve the F2-to-F3 sequence")
        selected_refs = output["structured_response"]["selected_refs"]
        if len(selected_refs) != len(set(selected_refs)) or any(
            ref not in snapshot["knowledge_ref_fingerprints"] for ref in selected_refs
        ):
            raise KnowledgePrecheckV2Error("model output selected refs are duplicated or unfrozen")
        output_by_id[attempt_id] = output
        pair_conditions[(output["pair_id"], output["condition"])] += 1
        context_ids.add(output["fresh_context_id_hash"])
    expected_pairs = Counter((pair_id, condition) for pair_id in tasks for condition in CONDITIONS)
    if pair_conditions != expected_pairs or len(outputs) != RETAINED_PAIR_TARGET * 2:
        raise KnowledgePrecheckV2Error("model outputs are not twelve balanced pairs")
    if set(input_by_id) != set(output_by_id):
        raise KnowledgePrecheckV2Error("model input coverage is incomplete")
    referenced_exchange_ids = [exchange_id for output in outputs for exchange_id in output["helper_exchange_ids"]]
    if len(referenced_exchange_ids) != len(set(referenced_exchange_ids)) or set(referenced_exchange_ids) != set(
        exchange_by_id
    ):
        raise KnowledgePrecheckV2Error("Helper exchange coverage is incomplete or multiply bound")
    if len(context_ids) != len(outputs):
        raise KnowledgePrecheckV2Error("fresh contexts are not unique")

    blind_packets = [_read_json(root, path) for path in manifest["blind_packet_files"]]
    blind_by_id: dict[str, Mapping[str, Any]] = {}
    for packet in blind_packets:
        if not isinstance(packet, Mapping):
            raise KnowledgePrecheckV2Error("blind packet must be an object")
        attempt_id = packet.get("attempt_id")
        output = output_by_id.get(attempt_id)
        if output is None:
            raise KnowledgePrecheckV2Error("blind packet attempt is unknown")
        bound_exchanges = [exchange_by_id[item] for item in output["helper_exchange_ids"]]
        expected_packet = build_blind_packet(output, tasks[output["pair_id"]], bound_exchanges)
        if packet != expected_packet:
            raise KnowledgePrecheckV2Error("blind packet does not match deterministic projection")
        if attempt_id in blind_by_id:
            raise KnowledgePrecheckV2Error("duplicate blind packet")
        blind_by_id[attempt_id] = packet
    if set(blind_by_id) != set(output_by_id):
        raise KnowledgePrecheckV2Error("blind packet coverage is incomplete")

    scores = [_read_json(root, path) for path in manifest["score_files"]]
    score_by_id: dict[str, dict[str, Any]] = {}
    scorer_context_ids: set[str] = set()
    for score in scores:
        if not isinstance(score, Mapping):
            raise KnowledgePrecheckV2Error("score must be an object")
        validate_score(score)
        attempt_id = score["attempt_id"]
        if attempt_id not in output_by_id or attempt_id in score_by_id:
            raise KnowledgePrecheckV2Error("score attempt binding is invalid")
        if score["blind_packet_sha256"] != canonical_sha256(blind_by_id[attempt_id]):
            raise KnowledgePrecheckV2Error("score is not bound to its blind packet")
        scorer_context_id = score["fresh_scorer_context_id_hash"]
        if scorer_context_id in scorer_context_ids:
            raise KnowledgePrecheckV2Error("fresh scorer contexts are not unique")
        scorer_context_ids.add(scorer_context_id)
        score_by_id[attempt_id] = dict(score)
    if set(score_by_id) != set(output_by_id):
        raise KnowledgePrecheckV2Error("score coverage is incomplete")

    adjudication = _read_json(root, manifest["adjudication_file"])
    if not isinstance(adjudication, Mapping) or set(adjudication) != {"overrides"}:
        raise KnowledgePrecheckV2Error("adjudication ledger shape is invalid")
    overrides = adjudication["overrides"]
    if not isinstance(overrides, list):
        raise KnowledgePrecheckV2Error("adjudication overrides must be an array")
    if overrides:
        raise KnowledgePrecheckV2Error("post-hoc score overrides are disabled for v0.2")
    for override in overrides:
        if not isinstance(override, Mapping) or set(override) != {
            "attempt_id",
            "field",
            "value",
            "reason",
        }:
            raise KnowledgePrecheckV2Error("adjudication override shape is invalid")
        attempt_id = override["attempt_id"]
        field = override["field"]
        if attempt_id not in score_by_id or field not in _SCORE_FIELDS - {"attempt_id", "scoring_notes"}:
            raise KnowledgePrecheckV2Error("adjudication override target is invalid")
        score_by_id[attempt_id][field] = override["value"]
        validate_score(score_by_id[attempt_id])

    records: list[dict[str, Any]] = []
    for output in sorted(outputs, key=lambda item: (item["pair_id"], item["condition"])):
        score = score_by_id[output["attempt_id"]]
        bound_exchanges = [exchange_by_id[item] for item in output["helper_exchange_ids"]]
        records.append(
            {
                "attempt_id": output["attempt_id"],
                "pair_id": output["pair_id"],
                "condition": output["condition"],
                "model_name": output["model_name"],
                "agent_runtime_name": output["agent_runtime_name"],
                "fresh_context_id_hash": output["fresh_context_id_hash"],
                "model_input_sha256": canonical_sha256(input_by_id[output["attempt_id"]]),
                "response": output["structured_response"],
                "helper_exchange_ids": output["helper_exchange_ids"],
                "helper_call_count": len(bound_exchanges),
                "f3_expansion_count": sum(len(exchange["f3_objects"]) for exchange in bound_exchanges),
                "usage": output["usage"],
                "latency": output["latency"],
                **{field: score[field] for field in _SCORE_FIELDS if field not in {"attempt_id", "scoring_notes"}},
            }
        )

    metric_names = (
        "selection_correct",
        "knowledge_adjusted_first_legal_action_correct",
        "action_changed",
        "strong_reuse",
        "correct_non_use",
        "false_f3_expansion",
        "helper_call_count",
        "f3_expansion_count",
    )
    by_key = {(record["pair_id"], record["condition"]): record for record in records}
    analysis: dict[str, Any] = {}
    differences: dict[str, list[float]] = {}
    for metric in metric_names:
        delta = [
            float(by_key[(pair_id, "l0-plus-l1")][metric]) - float(by_key[(pair_id, "l1-only")][metric])
            for pair_id in sorted(tasks)
        ]
        differences[metric] = delta
        analysis[metric] = paired_estimate(delta)

    thresholds = protocol["productization_thresholds"]
    main_gain = int(sum(differences["knowledge_adjusted_first_legal_action_correct"]))
    strong_gain = int(sum(differences["strong_reuse"]))
    selection_gain = int(sum(differences["selection_correct"]))
    false_f3_gain = int(sum(differences["false_f3_expansion"]))
    empty_non_use = all(
        by_key[(pair_id, "l0-plus-l1")]["correct_non_use"] == 1 for pair_id in thresholds["empty_pair_ids"]
    )
    gates = {
        "main_metric": main_gain >= thresholds["main_metric_net_gain_minimum"],
        "strong_reuse": strong_gain >= thresholds["strong_reuse_intervention_only_net_gain_minimum"],
        "selection_not_decreased": selection_gain >= 0,
        "empty_correct_non_use": empty_non_use,
        "false_f3_increment": false_f3_gain <= thresholds["false_f3_total_increment_maximum"],
        "capacity": protocol["l0_packet"]["bytes"] <= L0_MAX_BYTES and protocol["l0_packet"]["lines"] <= L0_MAX_LINES,
        "source_complete_replay": True,
    }
    support = all(gates.values())
    results = {
        "schema_version": SCHEMA_VERSION,
        "evidence_manifest_sha256": bytes_sha256((root / "manifest.json").read_bytes()),
        "protocol_sha256": canonical_sha256(protocol),
        "source_snapshot_sha256": canonical_sha256(snapshot),
        "records_sha256": canonical_sha256(records),
        "retained_pairs": RETAINED_PAIR_TARGET,
        "member_runs": len(records),
        "pair_attempts": pair_attempts,
        "technical_replacements": len(replacements),
        "process_launches": launches,
        "paired_analysis": analysis,
        "threshold_observations": {
            "main_metric_net_gain": main_gain,
            "strong_reuse_net_gain": strong_gain,
            "selection_correct_net_gain": selection_gain,
            "false_f3_total_increment": false_f3_gain,
            "empty_pairs_all_correct_non_use": empty_non_use,
        },
        "productization_gates": gates,
        "productization_decision": ("support-productizing-l0" if support else "do-not-support-productizing-l0"),
        "usage_availability": sorted({str(record["usage"]) for record in records}),
        "latency_availability": sorted({str(record["latency"]) for record in records}),
        "runner_identity": deepcopy(protocol["runner_identity_strategy"]),
    }

    records_bytes = json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    results_bytes = json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    report_lines = [
        "# Knowledge precheck v0.2 paired experiment",
        "",
        f"- Retained pairs: **{RETAINED_PAIR_TARGET}**; member runs: **{len(records)}**.",
        f"- L0 size: **{protocol['l0_packet']['bytes']} bytes / {protocol['l0_packet']['lines']} lines**.",
        f"- Productization decision: **{results['productization_decision']}**.",
        f"- Evidence manifest SHA-256: **`{results['evidence_manifest_sha256']}`**.",
        "",
        "## Preregistered gate observations",
        "",
        f"- Main metric net gain: **{main_gain}/12** (required at least 3/12).",
        f"- Strong reuse net gain: **{strong_gain}** (required at least 2).",
        f"- Selection-correct net gain: **{selection_gain}** (must not decrease).",
        f"- Empty pairs all correct non-use: **{str(empty_non_use).lower()}**.",
        f"- False-F3 total increment: **{false_f3_gain}** (maximum 2).",
        "",
        "## Paired estimates",
        "",
        "| Metric | Mean difference | 95% CI | Exact sign-flip p |",
        "|---|---:|---:|---:|",
    ]
    for metric in metric_names:
        estimate = analysis[metric]
        low, high = estimate["confidence_interval_95"]
        report_lines.append(
            f"| `{metric}` | {estimate['mean_difference']:.6f} | "
            f"[{low:.6f}, {high:.6f}] | {estimate['two_sided_sign_flip_p']:.6f} |"
        )
    report_lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "The compiler rejected unlisted, missing, or hash-drifted evidence and rebuilt this report from ",
            "the frozen protocol, source snapshot, raw Helper exchanges, model outputs, blind packets, scores, ",
            "and adjudication ledger. This selected twelve-task corpus does not establish broad causal effect. ",
            "A failed preregistered gate is not reinterpreted as support for more context.",
            "The native collaboration runtime does not expose the underlying model name, token usage, "
            "or model-only latency; those values are reported as unavailable rather than inferred. The "
            "runner preserves bounded model inputs and structured final outputs, not full transcripts or "
            "hidden reasoning. Fresh-context separation and gateway-only tool use are executed by the "
            "Controller but are not independently attested by the native runtime API.",
            "",
            f"Records SHA-256: `{results['records_sha256']}`.",
        ]
    )
    report_bytes = ("\n".join(report_lines) + "\n").encode("utf-8")
    return {"records.json": records_bytes, "results.json": results_bytes, "report.md": report_bytes}


__all__ = [
    "ALLOWED_KNOWLEDGE_OPERATIONS",
    "CASE_KINDS",
    "CONDITIONS",
    "EVIDENCE_SCHEMA_VERSION",
    "KnowledgePrecheckV2Error",
    "L0_MAX_BYTES",
    "L0_MAX_LINES",
    "MAX_PAIR_ATTEMPTS",
    "MAX_PROCESS_LAUNCHES",
    "MAX_REPLACEMENTS",
    "RETAINED_PAIR_TARGET",
    "RUN_TIMEOUT_SECONDS",
    "ReadOnlyKnowledgeGateway",
    "SCHEMA_VERSION",
    "TASK_FAMILIES",
    "TECHNICAL_EXCLUSION_CODES",
    "TOTAL_TIMEOUT_SECONDS",
    "build_blind_packet",
    "build_model_input_packet",
    "bytes_sha256",
    "canonical_json_bytes",
    "canonical_sha256",
    "compile_evidence_bundle",
    "logical_line_count",
    "render_l0_packet",
    "subprocess_helper_dispatch",
    "validate_model_output",
    "validate_model_input_packet",
    "validate_protocol",
    "validate_score",
]
