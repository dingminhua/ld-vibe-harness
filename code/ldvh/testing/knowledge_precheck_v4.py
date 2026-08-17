"""Source-complete F2 structure paired experiment helpers.

The v4 experiment compares F2 cards with and without the new action-guidance
fields (trigger_signal/scope_of_impact/action_relevance) under the same L1
trigger policy.  Both arms share the identical L1-baseline policy; the only
difference is whether the F2 card fields include the three new fields.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from ldvh.testing.helper_interaction_factorial import paired_estimate
from ldvh.testing.knowledge_precheck_v2 import (
    KnowledgePrecheckV2Error,
    bytes_sha256,
    canonical_json_bytes,
    canonical_sha256,
    logical_line_count,
    subprocess_helper_dispatch,
)
from ldvh.testing.knowledge_precheck_v2 import (
    _validate_gateway_request as _validate_v2_gateway_request,
)
from ldvh.testing.knowledge_precheck_v3 import (
    ALLOWED_KNOWLEDGE_OPERATIONS,
    CASE_KINDS,
    EVIDENCE_SCHEMA_VERSION as V3_EVIDENCE_SCHEMA_VERSION,
    MAX_MEMBER_LAUNCHES,
    MAX_PAIR_ATTEMPTS,
    MAX_REPLACEMENTS,
    MAX_SCORER_CONTEXTS,
    POLICY_MAX_BYTES,
    POLICY_MAX_LINES,
    RETAINED_PAIR_TARGET,
    RUN_TIMEOUT_SECONDS,
    TASK_FAMILIES,
    TECHNICAL_EXCLUSION_CODES,
    TOTAL_TIMEOUT_SECONDS,
    KnowledgePrecheckV3Error,
    build_blind_packet,
    build_raw_response_evidence,
    is_valid_structured_response,
    parse_raw_response_evidence,
    validate_f3_decision_response,
    validate_score,
    validate_scorer_response,
    validate_technical_failure_response,
)

# Build v4-specific trigger trace that uses v4 condition_from_packet
_TRIGGER_TRACE_FIELDS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "pair_id",
        "condition",
        "family",
        "triggered",
        "trigger_family",
        "positive_condition_codes",
        "veto_condition_codes",
    }
)

SCHEMA_VERSION = "ldvh-knowledge-precheck-v4/1"
EVIDENCE_SCHEMA_VERSION = "ldvh-knowledge-precheck-v4-evidence/1"
CONDITIONS = ("struct-baseline", "struct-enhanced")
NATIVE_SUBAGENT_RUNTIME = "codex-native-subagent"

# New fields that are stripped for struct-baseline
_STRIPPED_FIELDS = frozenset({"trigger_signal", "scope_of_impact", "action_relevance"})

_HEX64 = re.compile(r"[0-9a-f]{64}")

# Re-export from v3
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
        "expected_f2_trigger",
        "expected_f2_family",
        "expected_f3_allow_set",
        "admissible_answer",
        "first_legal_action",
        "wrong_action_codes",
        "action_changed_definition",
        "strong_reuse_definition",
        "correct_non_use_definition",
    }
)
_POLICY_FIELDS = frozenset({"content", "sha256", "bytes", "lines"})
_MODEL_INPUT_FIELDS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "pair_id",
        "family",
        "user_task",
        "fresh_context_id_hash",
        "l1_policy",
        "card_layer",
        "knowledge_gateway_contract",
        "trigger_trace_contract",
        "response_contract",
    }
)
_TRIGGER_RESPONSE_FIELDS = frozenset(
    {
        "triggered",
        "trigger_family",
        "positive_condition_codes",
        "veto_condition_codes",
    }
)
_F3_DECISION_RESPONSE_FIELDS = frozenset({"read_f3_refs"})
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
        "knowledge_adjusted_first_legal_action_correct",
        "action_changed",
        "strong_reuse",
        "correct_non_use",
        "scoring_notes",
    }
)
_SCORER_RESPONSE_FIELDS = frozenset(
    {
        "condition_blind_attested",
        "knowledge_adjusted_first_legal_action_correct",
        "action_changed",
        "strong_reuse",
        "correct_non_use",
        "scoring_notes",
    }
)
_RAW_RESPONSE_FIELDS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "response_kind",
        "raw_response_utf8",
        "response_sha256",
    }
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
_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "files",
        "protocol_file",
        "source_snapshot_file",
        "source_observation_files",
        "attempt_ledger_file",
        "model_input_files",
        "member_trigger_response_files",
        "trigger_trace_files",
        "helper_exchange_files",
        "member_f3_decision_response_files",
        "technical_failure_response_files",
        "member_final_response_files",
        "model_output_files",
        "blind_packet_files",
        "scorer_technical_failure_response_files",
        "scorer_response_files",
        "score_files",
        "adjudication_file",
    }
)
_SOURCE_SNAPSHOT_FIELDS = frozenset(
    {
        "schema_version",
        "frozen_at",
        "governed_project_id",
        "object_set_fingerprint",
        "family_counts",
        "family_cards_enhanced",
        "family_cards_stripped",
        "knowledge_ref_fingerprints",
        "knowledge_ref_families",
        "observation_file_sha256",
    }
)


class KnowledgePrecheckV4Error(ValueError):
    """Raised when the frozen v4 protocol or evidence fails closed."""


def _one_line(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise KnowledgePrecheckV4Error(f"{field} must be one non-empty line")
    return value


def _hex64(value: object, field: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise KnowledgePrecheckV4Error(f"{field} must be lowercase SHA-256")
    return value


def _closed_mapping(value: object, fields: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise KnowledgePrecheckV4Error(f"{label} fields are not closed")
    return value


def _unique_strings(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise KnowledgePrecheckV4Error(f"{field} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise KnowledgePrecheckV4Error(f"{field} must be unique")
    return value


def _strip_f2_cards(cards: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Remove the three new action-guidance fields from F2 card fields."""
    return [
        {k: v for k, v in card.items() if k not in _STRIPPED_FIELDS}
        for card in cards
    ]


def _validate_gateway_request(operation: str, request: Mapping[str, Any]) -> None:
    try:
        _validate_v2_gateway_request(operation, request)
    except KnowledgePrecheckV2Error as error:
        raise KnowledgePrecheckV4Error(str(error)) from error


class ReadOnlyKnowledgeGateway:
    """Fail-closed v4 gateway with dual-card-set F2 validation and projection.

    The gateway validates the live Helper response against the *enhanced* card set
    (the production shape), then projects the cards back to the caller according to
    the condition: ``struct-baseline`` strips the three new fields; ``struct-enhanced``
    returns them as-is.  The ``expected_f2_cards_stripped`` set is used for a secondary
    drift check on the stripped output.
    """

    def __init__(
        self,
        dispatch: Callable[[str, bytes], bytes],
        *,
        expected_object_set_fingerprint: str | None = None,
        expected_f2_cards_enhanced: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
        expected_f2_cards_stripped: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
        expected_f3_fingerprints: Mapping[str, str] | None = None,
    ) -> None:
        if expected_object_set_fingerprint is None and expected_f2_cards_enhanced is None:
            raise KnowledgePrecheckV4Error("gateway needs a frozen F2 source binding")
        self._dispatch = dispatch
        self._expected_object_set_fingerprint = (
            _hex64(expected_object_set_fingerprint, "expected_object_set_fingerprint")
            if expected_object_set_fingerprint is not None
            else None
        )
        self._expected_f2_cards_enhanced = {
            family: deepcopy(list(cards))
            for family, cards in (expected_f2_cards_enhanced or {}).items()
        }
        if self._expected_f2_cards_enhanced and set(self._expected_f2_cards_enhanced) != set(TASK_FAMILIES):
            raise KnowledgePrecheckV4Error("frozen enhanced F2 cards must cover every knowledge family")
        self._expected_f2_cards_stripped = {
            family: deepcopy(list(cards))
            for family, cards in (expected_f2_cards_stripped or {}).items()
        }
        if self._expected_f2_cards_stripped and set(self._expected_f2_cards_stripped) != set(TASK_FAMILIES):
            raise KnowledgePrecheckV4Error("frozen stripped F2 cards must cover every knowledge family")
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
        card_layer: str | None = None,
    ) -> dict[str, Any]:
        _one_line(exchange_id, "exchange_id")
        _one_line(attempt_id, "attempt_id")
        if any(exchange["exchange_id"] == exchange_id for exchange in self._exchanges):
            raise KnowledgePrecheckV4Error("exchange_id must be unique")
        _validate_gateway_request(operation, request)
        request_bytes = canonical_json_bytes(request)
        response_bytes = self._dispatch(operation, request_bytes)
        if not isinstance(response_bytes, bytes):
            raise KnowledgePrecheckV4Error("dispatch must return bytes")
        try:
            response = json.loads(response_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise KnowledgePrecheckV4Error("Helper response is not UTF-8 JSON") from error
        if not isinstance(response, Mapping):
            raise KnowledgePrecheckV4Error("Helper response must be an object")
        if response.get("operation_key") != operation or response.get("outcome") != "ok":
            raise KnowledgePrecheckV4Error("Helper response operation/outcome mismatch")
        if response.get("changes") != []:
            raise KnowledgePrecheckV4Error("knowledge gateway observed a state-changing response")

        coverage: dict[str, Any] | None = None
        match_reasons: list[dict[str, Any]] = []
        f3_objects: list[dict[str, str]] = []
        result = response.get("result")
        if not isinstance(result, Mapping):
            raise KnowledgePrecheckV4Error("Helper response has no result object")
        if operation == "find-fact-object-candidates":
            raw_coverage = result.get("coverage")
            cards = result.get("cards")
            if not isinstance(raw_coverage, Mapping) or raw_coverage.get("status") != "complete":
                raise KnowledgePrecheckV4Error("F2 coverage is not complete")
            if not isinstance(cards, list):
                raise KnowledgePrecheckV4Error("F2 cards must be an array")
            observed_fingerprint = raw_coverage.get("object_set_fingerprint")
            family = request["arguments"]["fact_type_keys"][0]
            if self._expected_f2_cards_enhanced:
                observed_cards = []
                for card in cards:
                    if not isinstance(card, Mapping) or not isinstance(card.get("fields"), Mapping):
                        raise KnowledgePrecheckV4Error("F2 card has no frozen fields")
                    observed_cards.append(card["fields"])
                if observed_cards != self._expected_f2_cards_enhanced[family]:
                    raise KnowledgePrecheckV4Error(f"F2 {family} knowledge cards drifted")
            elif observed_fingerprint != self._expected_object_set_fingerprint:
                raise KnowledgePrecheckV4Error("F2 object set drifted")

            # Project cards according to the condition
            if card_layer == "struct-baseline":
                # Strip the three new fields from the returned cards
                projected_cards = _strip_f2_cards(observed_cards)
                if self._expected_f2_cards_stripped:
                    if projected_cards != self._expected_f2_cards_stripped[family]:
                        raise KnowledgePrecheckV4Error(
                            f"F2 {family} stripped projection drifted from frozen stripped set"
                        )
                # Replace the cards in the response with the stripped version
                projected_response = []
                for original_card, projected_fields in zip(cards, projected_cards):
                    card_copy = deepcopy(original_card)
                    card_copy["fields"] = projected_fields
                    projected_response.append(card_copy)
                response = deepcopy(response)
                response["result"] = deepcopy(result)
                response["result"]["cards"] = projected_response
                cards = projected_response

            coverage = {
                "status": raw_coverage.get("status"),
                "total_matching": raw_coverage.get("total_matching"),
                "returned": raw_coverage.get("returned"),
                "object_set_fingerprint": observed_fingerprint,
            }
            for card in cards:
                if not isinstance(card, Mapping) or not isinstance(card.get("match_reasons"), list):
                    raise KnowledgePrecheckV4Error("F2 card has no match reasons")
                match_reasons.extend(deepcopy(card["match_reasons"]))
        else:
            items = result.get("items")
            if not isinstance(items, list) or not items:
                raise KnowledgePrecheckV4Error("F3 read returned no items")
            for item in items:
                if not isinstance(item, Mapping) or item.get("check_status") != "mechanically_valid":
                    raise KnowledgePrecheckV4Error("F3 item is not mechanically valid")
                fact_object = item.get("fact_object")
                if not isinstance(fact_object, Mapping):
                    raise KnowledgePrecheckV4Error("F3 item has no fact object")
                identity = fact_object.get("frontmatter", fact_object)
                resolved_ref = item.get("resolved_ref")
                if not isinstance(identity, Mapping) or not isinstance(resolved_ref, Mapping):
                    raise KnowledgePrecheckV4Error("F3 item has no normalized identity")
                uid = _one_line(resolved_ref.get("object_uid"), "F3 object_uid")
                if identity.get("object_uid") not in (None, uid):
                    raise KnowledgePrecheckV4Error("F3 fact identity does not match resolved ref")
                fact_type_key = _one_line(identity.get("fact_type_key"), "F3 fact_type_key")
                if fact_type_key not in TASK_FAMILIES:
                    raise KnowledgePrecheckV4Error("F3 object type is not a knowledge family")
                fingerprint = _hex64(item.get("content_fingerprint"), "F3 content_fingerprint")
                expected = self._expected_f3_fingerprints.get(uid)
                if self._expected_f3_fingerprints and expected is None:
                    raise KnowledgePrecheckV4Error(f"F3 object is not frozen: {uid}")
                if expected is not None and fingerprint != expected:
                    raise KnowledgePrecheckV4Error(f"F3 source drifted: {uid}")
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
                raise KnowledgePrecheckV4Error("F3 response does not exactly match requested refs")

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


def validate_protocol(protocol: Mapping[str, Any]) -> tuple[str, ...]:
    """Return stable protocol problem codes; an empty tuple means valid."""

    problems: list[str] = []
    if protocol.get("schema_version") != SCHEMA_VERSION:
        problems.append("schema-version")
    if protocol.get("conditions") != list(CONDITIONS):
        problems.append("conditions")
    if protocol.get("allowed_knowledge_operations") != list(ALLOWED_KNOWLEDGE_OPERATIONS):
        problems.append("allowed-knowledge-operations")
    if protocol.get("ceilings") != {
        "retained_pair_target": RETAINED_PAIR_TARGET,
        "maximum_pair_attempts": MAX_PAIR_ATTEMPTS,
        "maximum_replacements": MAX_REPLACEMENTS,
        "maximum_member_launches": MAX_MEMBER_LAUNCHES,
        "maximum_scorer_contexts": MAX_SCORER_CONTEXTS,
        "run_timeout_seconds": RUN_TIMEOUT_SECONDS,
        "total_timeout_seconds": TOTAL_TIMEOUT_SECONDS,
        "same_arm_retries": 0,
    }:
        problems.append("ceilings")

    source = protocol.get("source_snapshot")
    if not isinstance(source, Mapping):
        problems.append("source-snapshot")
    else:
        try:
            _hex64(source.get("object_set_fingerprint"), "object_set_fingerprint")
            _hex64(source.get("content_sha256"), "source_snapshot.content_sha256")
            _one_line(source.get("path"), "source_snapshot.path")
        except KnowledgePrecheckV4Error:
            problems.append("source-snapshot")

    policies = protocol.get("policies")
    if not isinstance(policies, Mapping) or set(policies) != set(CONDITIONS):
        problems.append("policies")
    else:
        for condition in CONDITIONS:
            policy = policies.get(condition)
            if not isinstance(policy, Mapping) or set(policy) != _POLICY_FIELDS:
                problems.append(f"policy-fields:{condition}")
                continue
            content = policy.get("content")
            if not isinstance(content, str) or not content.strip():
                problems.append(f"policy-content:{condition}")
                continue
            measured_bytes = len(content.encode("utf-8"))
            measured_lines = logical_line_count(content)
            if policy.get("bytes") != measured_bytes or policy.get("lines") != measured_lines:
                problems.append(f"policy-measurement:{condition}")
            if policy.get("sha256") != bytes_sha256(content.encode("utf-8")):
                problems.append(f"policy-hash:{condition}")
            if measured_bytes > POLICY_MAX_BYTES or measured_lines > POLICY_MAX_LINES:
                problems.append(f"policy-capacity:{condition}")

    tasks = protocol.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != RETAINED_PAIR_TARGET:
        problems.append("task-count")
        tasks = []
    pair_ids: list[str] = []
    family_case_counts: Counter[tuple[object, object]] = Counter()
    applicable_count = 0
    non_use_count = 0
    no_trigger_count = 0
    for raw_task in tasks:
        if not isinstance(raw_task, Mapping):
            problems.append("task-object")
            continue
        pair_id = str(raw_task.get("pair_id"))
        if set(raw_task) != _TASK_FIELDS:
            problems.append(f"task-fields:{pair_id}")
        try:
            pair_ids.append(_one_line(raw_task.get("pair_id"), "pair_id"))
            family = _one_line(raw_task.get("family"), "family")
            case_kind = _one_line(raw_task.get("case_kind"), "case_kind")
            _one_line(raw_task.get("confidence"), "confidence")
            _one_line(raw_task.get("text_origin"), "text_origin")
            _one_line(raw_task.get("user_task"), "user_task")
        except KnowledgePrecheckV4Error:
            problems.append(f"task-scalars:{pair_id}")
            continue
        family_case_counts[(family, case_kind)] += 1
        if family not in TASK_FAMILIES or case_kind not in CASE_KINDS:
            problems.append(f"task-stratum:{pair_id}")
        refs = raw_task.get("source_refs")
        if not isinstance(refs, list):
            problems.append(f"task-source-refs:{pair_id}")
        else:
            for ref in refs:
                if not isinstance(ref, Mapping) or set(ref) != {"object_uid", "content_fingerprint"}:
                    problems.append(f"task-source-ref-fields:{pair_id}")
                    continue
                try:
                    _one_line(ref.get("object_uid"), "source ref object_uid")
                    _hex64(ref.get("content_fingerprint"), "source ref content_fingerprint")
                except KnowledgePrecheckV4Error:
                    problems.append(f"task-source-ref-values:{pair_id}")
        gold = raw_task.get("gold")
        if not isinstance(gold, Mapping) or set(gold) != _GOLD_FIELDS:
            problems.append(f"gold-fields:{pair_id}")
            continue
        try:
            applicable = _unique_strings(gold.get("applicable_refs"), "applicable_refs")
            tempting = _unique_strings(gold.get("tempting_nonapplicable_refs"), "tempting_nonapplicable_refs")
            allow_set = _unique_strings(gold.get("expected_f3_allow_set"), "expected_f3_allow_set")
            if set(applicable) & set(tempting) or allow_set != applicable:
                problems.append(f"gold-ref-boundary:{pair_id}")
            expected_f2 = gold.get("expected_f2_trigger")
            if type(expected_f2) is not bool:
                problems.append(f"gold-f2-type:{pair_id}")
            expected_family = gold.get("expected_f2_family")
            if (expected_f2 and expected_family != family) or (not expected_f2 and expected_family is not None):
                problems.append(f"gold-f2-family:{pair_id}")
            for field in (
                "admissible_answer",
                "first_legal_action",
                "action_changed_definition",
                "strong_reuse_definition",
                "correct_non_use_definition",
            ):
                _one_line(gold.get(field), field)
            _unique_strings(gold.get("wrong_action_codes"), "wrong_action_codes")
        except KnowledgePrecheckV4Error:
            problems.append(f"gold-values:{pair_id}")
            continue
        if applicable:
            applicable_count += 1
        else:
            non_use_count += 1
        if not gold.get("expected_f2_trigger"):
            no_trigger_count += 1
    if len(pair_ids) != len(set(pair_ids)):
        problems.append("pair-id-uniqueness")
    expected_strata = Counter()
    for family in TASK_FAMILIES:
        expected_strata[(family, "exact-positive")] = 2
        for kind in CASE_KINDS[1:]:
            expected_strata[(family, kind)] = 1
    if family_case_counts != expected_strata:
        problems.append("family-case-balance")
    if (applicable_count, non_use_count, no_trigger_count) != (9, 9, 6):
        problems.append("applicability-balance")

    orders = protocol.get("condition_orders")
    if not isinstance(orders, list) or len(orders) != RETAINED_PAIR_TARGET:
        problems.append("condition-order-count")
    elif Counter(tuple(order) for order in orders) != Counter(
        {("struct-baseline", "struct-enhanced"): 9, ("struct-enhanced", "struct-baseline"): 9}
    ):
        problems.append("condition-order-balance")

    if protocol.get("adoption_thresholds") is None:
        problems.append("adoption-thresholds")
    denylist = protocol.get("artifact_denylist")
    if not isinstance(denylist, list) or not denylist or len(denylist) != len(set(denylist)):
        problems.append("artifact-denylist")
    if protocol.get("runner_identity_strategy") != {
        "agent_runtime_name": NATIVE_SUBAGENT_RUNTIME,
        "consistency_rule": (
            "Each member and scorer is a newly spawned fresh subagent inheriting the root-thread model without "
            "override; model identity, usage, and model-only latency remain unavailable."
        ),
        "model_name": "unavailable",
    }:
        problems.append("runner-identity")
    if not isinstance(protocol.get("scorer_rubric"), Mapping):
        problems.append("scorer-rubric")
    return tuple(sorted(set(problems)))


def build_model_input_packet(
    protocol: Mapping[str, Any],
    *,
    pair_id: str,
    condition: str,
    attempt_id: str,
    fresh_context_id_hash: str,
) -> dict[str, Any]:
    problems = validate_protocol(protocol)
    if problems:
        raise KnowledgePrecheckV4Error(f"protocol is invalid: {','.join(problems)}")
    if condition not in CONDITIONS:
        raise KnowledgePrecheckV4Error("condition is not frozen")
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}
    if pair_id not in tasks:
        raise KnowledgePrecheckV4Error("pair_id is not frozen")
    _one_line(attempt_id, "attempt_id")
    _hex64(fresh_context_id_hash, "fresh_context_id_hash")
    task = tasks[pair_id]
    policy = protocol["policies"][condition]
    packet = {
        "schema_version": SCHEMA_VERSION,
        "attempt_id": attempt_id,
        "pair_id": pair_id,
        "family": task["family"],
        "user_task": task["user_task"],
        "fresh_context_id_hash": fresh_context_id_hash,
        "card_layer": condition,
        "l1_policy": {
            "content": policy["content"],
            "sha256": policy["sha256"],
        },
        "knowledge_gateway_contract": {
            "allowed_operations": list(ALLOWED_KNOWLEDGE_OPERATIONS),
            "sequence": "zero calls, F2 only, or F2 then one F3; F3 maximum two exact same-family UIDs",
            "writes": "forbidden",
            "arguments_workspace_root": "forbidden",
            "f3_decision_response": {
                "fields": sorted(_F3_DECISION_RESPONSE_FIELDS),
                "instruction": "After F2, return zero to two exact same-family UIDs; an empty list stops at F2.",
            },
        },
        "trigger_trace_contract": {
            "must_precede_helper": True,
            "fields": sorted(_TRIGGER_RESPONSE_FIELDS),
            "instruction": (
                "Return one trigger trace JSON before any lookup. The Controller will return F2/F3 evidence if allowed."
            ),
        },
        "response_contract": {
            "fields": sorted(_RESPONSE_FIELDS),
            "instruction": "After permitted lookups, return only the closed structured response JSON.",
        },
    }
    validate_model_input_packet(packet, protocol)
    return packet


def validate_model_input_packet(packet: Mapping[str, Any], protocol: Mapping[str, Any]) -> None:
    _closed_mapping(packet, _MODEL_INPUT_FIELDS, "model input")
    if packet.get("schema_version") != SCHEMA_VERSION:
        raise KnowledgePrecheckV4Error("model input schema is invalid")
    rebuilt = build_model_input_packet_unchecked(
        protocol,
        pair_id=str(packet.get("pair_id")),
        condition=condition_from_packet(packet, protocol),
        attempt_id=str(packet.get("attempt_id")),
        fresh_context_id_hash=str(packet.get("fresh_context_id_hash")),
    )
    if packet != rebuilt:
        raise KnowledgePrecheckV4Error("model input is not the deterministic frozen projection")


def build_model_input_packet_unchecked(
    protocol: Mapping[str, Any],
    *,
    pair_id: str,
    condition: str,
    attempt_id: str,
    fresh_context_id_hash: str,
) -> dict[str, Any]:
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}
    if pair_id not in tasks or condition not in CONDITIONS:
        raise KnowledgePrecheckV4Error("model input binding is not frozen")
    _one_line(attempt_id, "attempt_id")
    _hex64(fresh_context_id_hash, "fresh_context_id_hash")
    task = tasks[pair_id]
    policy = protocol["policies"][condition]
    return {
        "schema_version": SCHEMA_VERSION,
        "attempt_id": attempt_id,
        "pair_id": pair_id,
        "family": task["family"],
        "user_task": task["user_task"],
        "fresh_context_id_hash": fresh_context_id_hash,
        "card_layer": condition,
        "l1_policy": {"content": policy["content"], "sha256": policy["sha256"]},
        "knowledge_gateway_contract": {
            "allowed_operations": list(ALLOWED_KNOWLEDGE_OPERATIONS),
            "sequence": "zero calls, F2 only, or F2 then one F3; F3 maximum two exact same-family UIDs",
            "writes": "forbidden",
            "arguments_workspace_root": "forbidden",
            "f3_decision_response": {
                "fields": sorted(_F3_DECISION_RESPONSE_FIELDS),
                "instruction": "After F2, return zero to two exact same-family UIDs; an empty list stops at F2.",
            },
        },
        "trigger_trace_contract": {
            "must_precede_helper": True,
            "fields": sorted(_TRIGGER_RESPONSE_FIELDS),
            "instruction": (
                "Return one trigger trace JSON before any lookup. The Controller will return F2/F3 evidence if allowed."
            ),
        },
        "response_contract": {
            "fields": sorted(_RESPONSE_FIELDS),
            "instruction": "After permitted lookups, return only the closed structured response JSON.",
        },
    }


def condition_from_packet(packet: Mapping[str, Any], protocol: Mapping[str, Any]) -> str:
    """Resolve the internal arm from the explicit card_layer field.

    Unlike v3, v4 arms share the same policy hash, so the condition is
    resolved from the ``card_layer`` field in the model input packet.
    """
    card_layer = packet.get("card_layer")
    if not isinstance(card_layer, str) or card_layer not in CONDITIONS:
        raise KnowledgePrecheckV4Error("model input card_layer does not identify one frozen arm")
    return card_layer


def validate_trigger_response(response: Mapping[str, Any], family: str) -> None:
    _closed_mapping(response, _TRIGGER_RESPONSE_FIELDS, "member trigger response")
    triggered = response.get("triggered")
    if type(triggered) is not bool:
        raise KnowledgePrecheckV4Error("triggered must be boolean")
    trigger_family = response.get("trigger_family")
    if (triggered and trigger_family != family) or (not triggered and trigger_family is not None):
        raise KnowledgePrecheckV4Error("trigger family is inconsistent")
    positives = _unique_strings(response.get("positive_condition_codes"), "positive_condition_codes")
    vetoes = _unique_strings(response.get("veto_condition_codes"), "veto_condition_codes")
    if triggered and (not positives or vetoes):
        raise KnowledgePrecheckV4Error("a positive trigger needs reasons and no veto")
    if not triggered and positives and not vetoes:
        raise KnowledgePrecheckV4Error("a vetoed positive signal must name a veto")


def build_trigger_trace(
    response: Mapping[str, Any],
    packet: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    """v4-specific trigger trace that resolves condition from card_layer."""
    validate_trigger_response(response, str(packet["family"]))
    trace = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "attempt_id": packet["attempt_id"],
        "pair_id": packet["pair_id"],
        "condition": condition_from_packet(packet, protocol),
        "family": packet["family"],
        **response,
    }
    validate_trigger_trace(trace, packet, protocol)
    return trace


def validate_trigger_trace(
    trace: Mapping[str, Any],
    packet: Mapping[str, Any],
    protocol: Mapping[str, Any] | None = None,
) -> None:
    """v4-specific trigger trace validation that resolves condition from card_layer."""
    if set(trace) != _TRIGGER_TRACE_FIELDS:
        raise KnowledgePrecheckV4Error("trigger trace fields are not closed")
    for field in ("attempt_id", "pair_id", "family"):
        if trace.get(field) != packet.get(field):
            raise KnowledgePrecheckV4Error(f"trigger trace {field} binding is invalid")
    if protocol is not None and trace.get("condition") != condition_from_packet(packet, protocol):
        raise KnowledgePrecheckV4Error("trigger trace condition binding is invalid")
    if trace.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise KnowledgePrecheckV4Error("trigger trace schema is invalid")
    validate_trigger_response({field: trace[field] for field in _TRIGGER_RESPONSE_FIELDS}, str(packet["family"]))


def validate_model_output(output: Mapping[str, Any], protocol: Mapping[str, Any]) -> None:
    """v4-specific model output validation using v4 CONDITIONS."""
    _closed_mapping(output, _OUTPUT_FIELDS, "model output")
    response = _closed_mapping(output.get("structured_response"), _RESPONSE_FIELDS, "structured response")
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}
    if output.get("pair_id") not in tasks or output.get("condition") not in CONDITIONS:
        raise KnowledgePrecheckV4Error("model output binding is not frozen")
    for field in ("attempt_id", "agent_runtime_name", "fresh_context_id_hash"):
        _one_line(output.get(field), field)
    _hex64(output.get("fresh_context_id_hash"), "fresh_context_id_hash")
    if output.get("model_name") is not None or output.get("agent_runtime_name") != NATIVE_SUBAGENT_RUNTIME:
        raise KnowledgePrecheckV4Error("member identity must remain the frozen native-subagent identity")
    for field in ("decision", "first_legal_action"):
        _one_line(response.get(field), field)
    for field in ("selected_refs", "rationale_codes", "refusal_reason_codes"):
        _unique_strings(response.get(field), field)
    _unique_strings(output.get("helper_exchange_ids"), "helper_exchange_ids")
    if output.get("usage") != "unavailable" or output.get("latency") != "unavailable":
        raise KnowledgePrecheckV4Error("unobservable usage/latency must remain unavailable")


def is_valid_structured_response(
    response: Mapping[str, Any],
    *,
    packet: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> bool:
    """v4-specific check using v4 CONDITIONS."""
    candidate = {
        "attempt_id": packet["attempt_id"],
        "pair_id": packet["pair_id"],
        "condition": condition_from_packet(packet, protocol),
        "model_name": None,
        "agent_runtime_name": NATIVE_SUBAGENT_RUNTIME,
        "fresh_context_id_hash": packet["fresh_context_id_hash"],
        "structured_response": response,
        "helper_exchange_ids": [],
        "usage": "unavailable",
        "latency": "unavailable",
    }
    try:
        validate_model_output(candidate, protocol)
    except KnowledgePrecheckV4Error:
        return False
    return True


def validate_technical_failure_response(
    response: Mapping[str, Any],
    *,
    exclusion_code: str,
    packet: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> None:
    """v4-specific technical failure validation using v4 CONDITIONS."""
    if exclusion_code not in TECHNICAL_EXCLUSION_CODES:
        raise KnowledgePrecheckV4Error("replacement uses a nontechnical exclusion")
    if exclusion_code != "missing_structured_output":
        return
    if not is_valid_structured_response(response, packet=packet, protocol=protocol):
        return
    raise KnowledgePrecheckV4Error("technical failure response is a valid structured output")


def _source_snapshot_observation_hashes(root: Path, snapshot: Mapping[str, Any]) -> dict[str, str]:
    """Return the observation file hashes from the snapshot."""
    raw = snapshot.get("observation_file_sha256")
    if not isinstance(raw, Mapping):
        raise KnowledgePrecheckV4Error("source observation hashes are missing")
    return dict(raw)


def _validate_source_observations(
    root: Path,
    observation_files: Sequence[str],
    snapshot: Mapping[str, Any],
) -> None:
    expected_names = {
        f"{family}-{layer}.{direction}.json"
        for family in TASK_FAMILIES
        for layer in ("f2", "f3")
        for direction in ("request", "response")
    }
    by_name = {str(Path(path).relative_to("source-observations")): path for path in observation_files}
    if set(by_name) != expected_names:
        raise KnowledgePrecheckV4Error("source observation names are not the frozen three-family F2/F3 set")
    family_counts = snapshot.get("family_counts")
    family_cards_enhanced = snapshot.get("family_cards_enhanced")
    family_cards_stripped = snapshot.get("family_cards_stripped")
    fingerprints = snapshot.get("knowledge_ref_fingerprints")
    families = snapshot.get("knowledge_ref_families")
    if (
        not isinstance(family_counts, Mapping)
        or set(family_counts) != set(TASK_FAMILIES)
        or not isinstance(family_cards_enhanced, Mapping)
        or set(family_cards_enhanced) != set(TASK_FAMILIES)
        or not isinstance(family_cards_stripped, Mapping)
        or set(family_cards_stripped) != set(TASK_FAMILIES)
        or not isinstance(fingerprints, Mapping)
        or not isinstance(families, Mapping)
    ):
        raise KnowledgePrecheckV4Error("source snapshot family projection is incomplete")

    for family in TASK_FAMILIES:
        f2_request = _read_json(root, by_name[f"{family}-f2.request.json"])
        if f2_request != {
            "arguments": {
                "governed_project_id": snapshot.get("governed_project_id"),
                "card_layer": "F2",
                "fact_type_keys": [family],
                "statuses": ["active"],
            }
        }:
            raise KnowledgePrecheckV4Error(f"{family} source F2 request is not frozen")
        f2_response = _read_json(root, by_name[f"{family}-f2.response.json"])
        if (
            not isinstance(f2_response, Mapping)
            or f2_response.get("operation_key") != "find-fact-object-candidates"
            or f2_response.get("outcome") != "ok"
            or f2_response.get("changes") != []
        ):
            raise KnowledgePrecheckV4Error(f"{family} source F2 response is invalid")
        result = f2_response.get("result")
        recovery = result.get("recovery_manifest") if isinstance(result, Mapping) else None
        cards = result.get("cards") if isinstance(result, Mapping) else None
        if (
            not isinstance(recovery, Mapping)
            or recovery.get("object_set_fingerprint") != snapshot.get("object_set_fingerprint")
            or not isinstance(cards, list)
            or family_counts[family] != len(cards)
            or not isinstance(family_counts[family], int)
        ):
            raise KnowledgePrecheckV4Error(f"{family} source F2 coverage is invalid")
        card_uids: list[str] = []
        enhanced_cards: list[Mapping[str, Any]] = []
        for card in cards:
            if not isinstance(card, Mapping) or not isinstance(card.get("fields"), Mapping):
                raise KnowledgePrecheckV4Error(f"{family} source F2 card is invalid")
            fields = card["fields"]
            uid = fields.get("object_uid")
            if (
                not isinstance(uid, str)
                or card.get("fact_ref") != {"object_uid": uid}
                or fields.get("status") != "active"
                or families.get(uid) != family
            ):
                raise KnowledgePrecheckV4Error(f"{family} source F2 card identity is invalid")
            enhanced_cards.append(fields)
            card_uids.append(uid)
        if enhanced_cards != family_cards_enhanced[family] or len(card_uids) != len(set(card_uids)):
            raise KnowledgePrecheckV4Error(f"{family} source F2 enhanced cards differ from the snapshot")
        # Verify stripped cards are correctly derived
        stripped_cards = _strip_f2_cards(enhanced_cards)
        if stripped_cards != family_cards_stripped[family]:
            raise KnowledgePrecheckV4Error(f"{family} source F2 stripped cards differ from the snapshot")

        f3_request = _read_json(root, by_name[f"{family}-f3.request.json"])
        expected_f3_request = {"arguments": {"fact_refs": [{"object_uid": uid} for uid in card_uids]}}
        if f3_request != expected_f3_request:
            raise KnowledgePrecheckV4Error(f"{family} source F3 request does not cover its F2 cards")
        f3_response = _read_json(root, by_name[f"{family}-f3.response.json"])
        if (
            not isinstance(f3_response, Mapping)
            or f3_response.get("operation_key") != "read-fact-objects"
            or f3_response.get("outcome") != "ok"
            or f3_response.get("changes") != []
        ):
            raise KnowledgePrecheckV4Error(f"{family} source F3 response is invalid")
        f3_result = f3_response.get("result")
        items = f3_result.get("items") if isinstance(f3_result, Mapping) else None
        if not isinstance(items, list) or len(items) != len(card_uids):
            raise KnowledgePrecheckV4Error(f"{family} source F3 coverage is incomplete")
        for expected_uid, item in zip(card_uids, items, strict=True):
            fact = item.get("fact_object") if isinstance(item, Mapping) else None
            identity = fact.get("frontmatter", fact) if isinstance(fact, Mapping) else None
            if (
                not isinstance(item, Mapping)
                or item.get("check_status") != "mechanically_valid"
                or item.get("resolved_ref") != {"object_uid": expected_uid}
                or item.get("content_fingerprint") != fingerprints.get(expected_uid)
                or not isinstance(fact, Mapping)
                or not isinstance(identity, Mapping)
                or identity.get("object_uid") != expected_uid
                or identity.get("fact_type_key") != family
            ):
                raise KnowledgePrecheckV4Error(f"{family} source F3 object differs from the snapshot")


def _read_json(root: Path, relative: str) -> Any:
    try:
        return json.loads((root / relative).read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise KnowledgePrecheckV4Error(f"cannot read evidence file: {relative}") from error


def _timestamp(value: object, field: str) -> datetime:
    text = _one_line(value, field)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise KnowledgePrecheckV4Error(f"{field} must be RFC3339") from error


def _manifest_files(manifest: Mapping[str, Any]) -> dict[str, str]:
    raw = manifest.get("files")
    if not isinstance(raw, Mapping) or not raw:
        raise KnowledgePrecheckV4Error("manifest files must be a non-empty object")
    files: dict[str, str] = {}
    for relative, digest in raw.items():
        path = _one_line(relative, "manifest path")
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise KnowledgePrecheckV4Error("manifest path escapes the bundle")
        files[path] = _hex64(digest, f"manifest digest:{path}")
    return files


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


def _contains_key(value: object, target: str) -> bool:
    if isinstance(value, Mapping):
        return target in value or any(_contains_key(member, target) for member in value.values())
    if isinstance(value, list):
        return any(_contains_key(member, target) for member in value)
    return False


def _condition_sums(records: Sequence[Mapping[str, Any]], metric: str) -> dict[str, int]:
    return {
        condition: sum(int(record[metric]) for record in records if record["condition"] == condition)
        for condition in CONDITIONS
    }


def _strata(records: Sequence[Mapping[str, Any]], tasks: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in TASK_FAMILIES:
        for case_kind in CASE_KINDS:
            pair_ids = [
                pair_id
                for pair_id, task in tasks.items()
                if task["family"] == family and task["case_kind"] == case_kind
            ]
            if not pair_ids:
                continue
            members = [record for record in records if record["pair_id"] in pair_ids]
            rows.append(
                {
                    "family": family,
                    "case_kind": case_kind,
                    "pairs": len(pair_ids),
                    "conditions": {
                        condition: {
                            "trigger_correct": sum(
                                record["trigger_decision_correct"]
                                for record in members
                                if record["condition"] == condition
                            ),
                            "strong_reuse": sum(
                                int(record["strong_reuse"]) for record in members if record["condition"] == condition
                            ),
                            "correct_non_use": sum(
                                int(record["correct_non_use"]) for record in members if record["condition"] == condition
                            ),
                            "false_f3_expansion": sum(
                                record["false_f3_expansion"] for record in members if record["condition"] == condition
                            ),
                        }
                        for condition in CONDITIONS
                    },
                }
            )
    return rows


def compile_evidence_bundle(bundle_root: Path) -> dict[str, bytes]:
    """Validate a sealed bundle and deterministically rebuild all outputs."""

    root = bundle_root.resolve(strict=True)
    manifest = _read_json(root, "manifest.json")
    if not isinstance(manifest, Mapping) or set(manifest) != _MANIFEST_FIELDS:
        raise KnowledgePrecheckV4Error("evidence manifest fields are invalid")
    if manifest.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise KnowledgePrecheckV4Error("evidence manifest schema is invalid")
    files = _manifest_files(manifest)
    actual = {
        str(path.relative_to(root)) for path in root.rglob("*") if path.is_file() and path.name != "manifest.json"
    }
    if actual != set(files):
        raise KnowledgePrecheckV4Error(
            f"bundle file closure mismatch: missing={sorted(set(files) - actual)}, extra={sorted(actual - set(files))}"
        )
    for relative, digest in files.items():
        if bytes_sha256((root / relative).read_bytes()) != digest:
            raise KnowledgePrecheckV4Error(f"bundle hash mismatch: {relative}")

    protocol = _read_json(root, str(manifest["protocol_file"]))
    if not isinstance(protocol, Mapping) or validate_protocol(protocol):
        raise KnowledgePrecheckV4Error("frozen protocol is invalid")
    snapshot = _read_json(root, str(manifest["source_snapshot_file"]))
    if not isinstance(snapshot, Mapping) or set(snapshot) != _SOURCE_SNAPSHOT_FIELDS:
        raise KnowledgePrecheckV4Error("source snapshot fields are not closed")
    if (
        snapshot.get("schema_version") != "ldvh-knowledge-precheck-v4-source-snapshot/1"
        or snapshot.get("governed_project_id") != "ldvh"
    ):
        raise KnowledgePrecheckV4Error("source snapshot identity is invalid")
    _timestamp(snapshot.get("frozen_at"), "source snapshot frozen_at")
    if canonical_sha256(snapshot) != protocol["source_snapshot"]["content_sha256"]:
        raise KnowledgePrecheckV4Error("source snapshot hash mismatch")
    if snapshot.get("object_set_fingerprint") != protocol["source_snapshot"]["object_set_fingerprint"]:
        raise KnowledgePrecheckV4Error("source snapshot object set fingerprint mismatch")
    observation_files = manifest["source_observation_files"]
    if not isinstance(observation_files, list) or observation_files != sorted(observation_files):
        raise KnowledgePrecheckV4Error("source observation file list is invalid")
    expected_observations = snapshot.get("observation_file_sha256")
    if not isinstance(expected_observations, Mapping):
        raise KnowledgePrecheckV4Error("source observation hashes are missing")
    observed_names = [str(Path(path).relative_to("source-observations")) for path in observation_files]
    if set(observed_names) != set(expected_observations):
        raise KnowledgePrecheckV4Error("source observation coverage is incomplete")
    for path, name in zip(observation_files, observed_names, strict=True):
        if bytes_sha256((root / path).read_bytes()) != expected_observations[name]:
            raise KnowledgePrecheckV4Error(f"source observation drifted: {name}")
    _validate_source_observations(root, observation_files, snapshot)
    fingerprints = snapshot.get("knowledge_ref_fingerprints")
    families = snapshot.get("knowledge_ref_families")
    if not isinstance(fingerprints, Mapping) or not isinstance(families, Mapping) or set(fingerprints) != set(families):
        raise KnowledgePrecheckV4Error("knowledge reference snapshot is incomplete")
    for digest in fingerprints.values():
        _hex64(digest, "knowledge ref fingerprint")
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}
    for task in tasks.values():
        all_refs = task["gold"]["applicable_refs"] + task["gold"]["tempting_nonapplicable_refs"]
        if any(ref not in fingerprints for ref in all_refs):
            raise KnowledgePrecheckV4Error("task gold references an unfrozen object")
        if any(families[ref] != task["family"] for ref in all_refs):
            raise KnowledgePrecheckV4Error("task gold reference family is inconsistent")
        source_refs = {ref["object_uid"]: ref["content_fingerprint"] for ref in task["source_refs"]}
        if set(source_refs) != set(all_refs) or any(source_refs[ref] != fingerprints[ref] for ref in all_refs):
            raise KnowledgePrecheckV4Error("task source refs do not exactly bind the frozen gold boundary")
    denylist = set(protocol["artifact_denylist"])
    family_cards_enhanced = snapshot.get("family_cards_enhanced")
    family_cards_stripped = snapshot.get("family_cards_stripped")

    # ... rest of compilation follows the same pattern as v3 but adapted for v4 conditions
    # (The full compile_evidence_bundle is long; it mirrors v3's logic but with new conditions)
    # For brevity, reuse the v3 compile approach with v4-specific conditions

    return _compile_evidence_bundle_v4(
        root, manifest, protocol, snapshot, files, denylist,
        family_cards_enhanced, family_cards_stripped, fingerprints, families,
    )


def _compile_evidence_bundle_v4(
    root: Path,
    manifest: Mapping[str, Any],
    protocol: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    files: dict[str, str],
    denylist: set[str],
    family_cards_enhanced: Mapping[str, Sequence[Mapping[str, Any]]],
    family_cards_stripped: Mapping[str, Sequence[Mapping[str, Any]]],
    fingerprints: Mapping[str, str],
    families: Mapping[str, str],
) -> dict[str, bytes]:
    """Deterministically rebuild v4 records, results, and report from sealed evidence."""

    tasks = {task["pair_id"]: task for task in protocol["tasks"]}

    ledger = _read_json(root, str(manifest["attempt_ledger_file"]))
    if not isinstance(ledger, Mapping) or set(ledger) != {
        "pair_attempts",
        "technical_replacements",
        "process_launches",
        "retained_scorer_contexts",
        "scorer_technical_failures",
        "launches",
        "scorer_runs",
    }:
        raise KnowledgePrecheckV4Error("attempt ledger shape is invalid")
    pair_attempts = ledger["pair_attempts"]
    replacements = ledger["technical_replacements"]
    process_launches = ledger["process_launches"]
    retained_scorer_contexts = ledger["retained_scorer_contexts"]
    scorer_technical_failures = ledger["scorer_technical_failures"]
    if type(pair_attempts) is not int or not RETAINED_PAIR_TARGET <= pair_attempts <= MAX_PAIR_ATTEMPTS:
        raise KnowledgePrecheckV4Error("pair attempt ceiling is invalid")
    if not isinstance(replacements, list) or len(replacements) > MAX_REPLACEMENTS:
        raise KnowledgePrecheckV4Error("replacement ceiling is invalid")
    if pair_attempts != RETAINED_PAIR_TARGET + len(replacements):
        raise KnowledgePrecheckV4Error("pair attempt/replacement accounting is inconsistent")
    replacement_attempt_groups: dict[tuple[str, ...], Mapping[str, Any]] = {}
    replacement_pair_counts: Counter[str] = Counter()
    for replacement in replacements:
        if not isinstance(replacement, Mapping) or set(replacement) != {
            "pair_id",
            "exclusion_code",
            "excluded_attempt_ids",
        }:
            raise KnowledgePrecheckV4Error("replacement entry shape is invalid")
        pair_id = str(replacement["pair_id"])
        attempt_ids = replacement["excluded_attempt_ids"]
        if pair_id not in tasks or replacement["exclusion_code"] not in TECHNICAL_EXCLUSION_CODES:
            raise KnowledgePrecheckV4Error("replacement uses a nontechnical exclusion")
        if (
            not isinstance(attempt_ids, list)
            or len(attempt_ids) != len(CONDITIONS)
            or any(not isinstance(attempt_id, str) or not attempt_id for attempt_id in attempt_ids)
            or len(attempt_ids) != len(set(attempt_ids))
        ):
            raise KnowledgePrecheckV4Error("replacement attempt binding is invalid")
        attempt_group = tuple(attempt_ids)
        if attempt_group in replacement_attempt_groups:
            raise KnowledgePrecheckV4Error("replacement attempt binding is duplicated")
        replacement_attempt_groups[attempt_group] = replacement
        replacement_pair_counts[pair_id] += 1
    expected_members = RETAINED_PAIR_TARGET * len(CONDITIONS)
    expected_launches = expected_members + len(CONDITIONS) * len(replacements)
    if (
        type(process_launches) is not int
        or process_launches != expected_launches
        or process_launches > MAX_MEMBER_LAUNCHES
    ):
        raise KnowledgePrecheckV4Error("member launch ceiling is invalid")
    if (
        type(retained_scorer_contexts) is not int
        or retained_scorer_contexts != expected_members
        or not isinstance(scorer_technical_failures, list)
    ):
        raise KnowledgePrecheckV4Error("scorer context ceiling is invalid")

    launch_by_attempt: dict[str, Mapping[str, Any]] = {}
    pair_launches: dict[str, list[Mapping[str, Any]]] = {}
    launch_rows = ledger["launches"]
    for index, launch in enumerate(launch_rows, start=1):
        if not isinstance(launch, Mapping) or set(launch) != {
            "sequence",
            "attempt_id",
            "pair_id",
            "condition",
            "started_at",
            "finished_at",
        }:
            raise KnowledgePrecheckV4Error("member launch row shape is invalid")
        if launch["sequence"] != index:
            raise KnowledgePrecheckV4Error("member launch sequence is not contiguous")
        attempt_id = _one_line(launch["attempt_id"], "launch attempt_id")
        if attempt_id in launch_by_attempt:
            raise KnowledgePrecheckV4Error("member launch attempt id is duplicated")
        started = _timestamp(launch["started_at"], "launch started_at")
        finished = _timestamp(launch["finished_at"], "launch finished_at")
        elapsed = (finished - started).total_seconds()
        if elapsed < 0 or elapsed > RUN_TIMEOUT_SECONDS:
            raise KnowledgePrecheckV4Error("member run exceeded its frozen timeout")
        launch_by_attempt[attempt_id] = launch
        pair_id = str(launch["pair_id"])
        if pair_id not in tasks or launch["condition"] not in CONDITIONS:
            raise KnowledgePrecheckV4Error("member launch pair or condition is not frozen")
        pair_launches.setdefault(pair_id, []).append(launch)

    excluded_attempt_ids: set[str] = set()
    retained_attempt_ids: set[str] = set()
    observed_replacement_groups: set[tuple[str, ...]] = set()
    for index, pair_id in enumerate(tasks):
        rows = pair_launches.get(pair_id, [])
        waves = 1 + replacement_pair_counts[pair_id]
        expected_order = protocol["condition_orders"][index]
        if [str(row["condition"]) for row in rows] != expected_order * waves:
            raise KnowledgePrecheckV4Error("member runs violate frozen condition order")
        chunks = [rows[offset : offset + len(CONDITIONS)] for offset in range(0, len(rows), len(CONDITIONS))]
        if len(chunks) != waves:
            raise KnowledgePrecheckV4Error("member pair-attempt accounting is inconsistent")
        for chunk in chunks[:-1]:
            attempt_group = tuple(str(row["attempt_id"]) for row in chunk)
            replacement = replacement_attempt_groups.get(attempt_group)
            if replacement is None or replacement["pair_id"] != pair_id:
                raise KnowledgePrecheckV4Error("excluded whole-pair launch binding is incomplete")
            observed_replacement_groups.add(attempt_group)
            excluded_attempt_ids.update(attempt_group)
        retained_attempt_ids.update(str(row["attempt_id"]) for row in chunks[-1])
    if set(pair_launches) != set(tasks) or observed_replacement_groups != set(replacement_attempt_groups):
        raise KnowledgePrecheckV4Error("replacement/launch coverage is inconsistent")
    if excluded_attempt_ids & retained_attempt_ids or len(retained_attempt_ids) != expected_members:
        raise KnowledgePrecheckV4Error("retained and excluded member launch sets are invalid")

    model_inputs = [_read_json(root, path) for path in manifest["model_input_files"]]
    input_by_id: dict[str, Mapping[str, Any]] = {}
    for packet in model_inputs:
        if not isinstance(packet, Mapping):
            raise KnowledgePrecheckV4Error("model input must be an object")
        validate_model_input_packet(packet, protocol)
        attempt_id = str(packet["attempt_id"])
        if attempt_id in input_by_id:
            raise KnowledgePrecheckV4Error("duplicate model input attempt id")
        launch = launch_by_attempt.get(attempt_id)
        if (
            launch is None
            or launch["pair_id"] != packet["pair_id"]
            or launch["condition"] != condition_from_packet(packet, protocol)
        ):
            raise KnowledgePrecheckV4Error("model input/member launch binding is invalid")
        input_by_id[attempt_id] = packet
    if set(input_by_id) != set(launch_by_attempt):
        raise KnowledgePrecheckV4Error("model input/member launch coverage is incomplete")

    trigger_responses = [_read_json(root, path) for path in manifest["member_trigger_response_files"]]
    derived_traces: dict[str, dict[str, Any]] = {}
    for evidence in trigger_responses:
        if not isinstance(evidence, Mapping):
            raise KnowledgePrecheckV4Error("member trigger raw response must be an object")
        response = parse_raw_response_evidence(evidence, response_kind="member-trigger")
        attempt_id = str(evidence["attempt_id"])
        packet = input_by_id.get(attempt_id)
        if packet is None or attempt_id in derived_traces:
            raise KnowledgePrecheckV4Error("member trigger raw response binding is invalid")
        derived_traces[attempt_id] = build_trigger_trace(response, packet, protocol)
    if not retained_attempt_ids <= set(derived_traces) <= set(input_by_id):
        raise KnowledgePrecheckV4Error("member trigger raw response coverage is incomplete")

    traces = [_read_json(root, path) for path in manifest["trigger_trace_files"]]
    trace_by_id: dict[str, Mapping[str, Any]] = {}
    for trace in traces:
        if not isinstance(trace, Mapping):
            raise KnowledgePrecheckV4Error("trigger trace must be an object")
        attempt_id = str(trace.get("attempt_id"))
        packet = input_by_id.get(attempt_id)
        if packet is None or attempt_id in trace_by_id:
            raise KnowledgePrecheckV4Error("trigger trace attempt binding is invalid")
        # Use v3's validate_trigger_trace since the trace fields are the same
        validate_trigger_trace(trace, packet, protocol)
        if trace != derived_traces[attempt_id]:
            raise KnowledgePrecheckV4Error("trigger trace differs from the raw member response")
        trace_by_id[attempt_id] = trace
    if set(trace_by_id) != set(derived_traces):
        raise KnowledgePrecheckV4Error("trigger trace coverage is incomplete")
    if set(input_by_id) - set(trace_by_id) - excluded_attempt_ids:
        raise KnowledgePrecheckV4Error("retained member trigger evidence is incomplete")

    f3_decision_responses = [_read_json(root, path) for path in manifest["member_f3_decision_response_files"]]
    f3_decision_by_id: dict[str, list[str]] = {}
    for evidence in f3_decision_responses:
        if not isinstance(evidence, Mapping):
            raise KnowledgePrecheckV4Error("member F3 decision raw response must be an object")
        response = parse_raw_response_evidence(evidence, response_kind="member-f3-decision")
        attempt_id = str(evidence["attempt_id"])
        packet = input_by_id.get(attempt_id)
        trace = trace_by_id.get(attempt_id)
        if packet is None or attempt_id in f3_decision_by_id or trace is None or not trace["triggered"]:
            raise KnowledgePrecheckV4Error("member F3 decision raw response binding is invalid")
        f3_decision_by_id[attempt_id] = validate_f3_decision_response(
            response,
            family=str(packet["family"]),
            snapshot_families=families,
        )

    exchanges = [_read_json(root, path) for path in manifest["helper_exchange_files"]]
    exchange_by_id: dict[str, Mapping[str, Any]] = {}
    exchanges_by_attempt: dict[str, list[Mapping[str, Any]]] = {}
    for exchange in exchanges:
        if not isinstance(exchange, Mapping) or set(exchange) != _EXCHANGE_FIELDS:
            raise KnowledgePrecheckV4Error("helper exchange fields are invalid")
        if exchange.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
            raise KnowledgePrecheckV4Error("helper exchange schema is invalid")
        if exchange.get("operation") not in ALLOWED_KNOWLEDGE_OPERATIONS or exchange.get("state_changing_calls") != 0:
            raise KnowledgePrecheckV4Error("helper exchange is not read-only allowlisted evidence")
        request_bytes = str(exchange.get("raw_request_utf8", "")).encode("utf-8")
        response_bytes = str(exchange.get("raw_response_utf8", "")).encode("utf-8")
        if bytes_sha256(request_bytes) != exchange.get("request_sha256") or bytes_sha256(
            response_bytes
        ) != exchange.get("response_sha256"):
            raise KnowledgePrecheckV4Error("helper raw bytes do not match their hashes")
        try:
            raw_request = json.loads(request_bytes)
            json.loads(response_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise KnowledgePrecheckV4Error("helper raw bytes are not JSON") from error
        denied = _denylisted_keys(raw_request, denylist) | _denylisted_keys(json.loads(response_bytes), denylist)
        if denied:
            raise KnowledgePrecheckV4Error(f"helper exchange contains denylisted keys: {','.join(sorted(denied))}")
        exchange_id = _one_line(exchange.get("exchange_id"), "exchange_id")
        attempt_id = _one_line(exchange.get("attempt_id"), "exchange attempt_id")
        packet = input_by_id.get(attempt_id)
        if packet is None or exchange_id in exchange_by_id:
            raise KnowledgePrecheckV4Error("helper exchange binding is invalid")
        _validate_gateway_request(str(exchange["operation"]), raw_request)
        if exchange["operation"] == "find-fact-object-candidates" and raw_request["arguments"]["fact_type_keys"] != [
            packet["family"]
        ]:
            raise KnowledgePrecheckV4Error("F2 request family differs from the member input")
        if exchange["operation"] == "read-fact-objects":
            requested_uids = [ref["object_uid"] for ref in raw_request["arguments"]["fact_refs"]]
            if any(families.get(uid) != packet["family"] for uid in requested_uids):
                raise KnowledgePrecheckV4Error("F3 request crossed the frozen task family")
            if requested_uids != f3_decision_by_id.get(attempt_id):
                raise KnowledgePrecheckV4Error("F3 request differs from the raw member decision")
        card_layer = str(packet.get("card_layer", "struct-enhanced"))
        replay = ReadOnlyKnowledgeGateway(
            lambda _operation, _request, payload=response_bytes: payload,
            expected_f2_cards_enhanced=family_cards_enhanced,
            expected_f2_cards_stripped=family_cards_stripped,
            expected_f3_fingerprints=fingerprints,
        ).call(
            str(exchange["operation"]),
            raw_request,
            exchange_id=exchange_id,
            attempt_id=attempt_id,
            card_layer=card_layer,
        )
        if replay != exchange:
            raise KnowledgePrecheckV4Error("helper derived fields do not replay from raw bytes")
        exchange_by_id[exchange_id] = exchange
        exchanges_by_attempt.setdefault(attempt_id, []).append(exchange)
    f2_attempt_ids = {
        str(exchange["attempt_id"]) for exchange in exchanges if exchange["operation"] == "find-fact-object-candidates"
    }
    f3_attempt_ids = {
        str(exchange["attempt_id"]) for exchange in exchanges if exchange["operation"] == "read-fact-objects"
    }
    if set(f3_decision_by_id) != f2_attempt_ids:
        raise KnowledgePrecheckV4Error("raw post-F2 member decision coverage is incomplete")
    if {attempt_id for attempt_id, refs in f3_decision_by_id.items() if refs} != f3_attempt_ids:
        raise KnowledgePrecheckV4Error("raw member F3 decisions do not match actual F3 calls")

    replacement_code_by_attempt = {
        attempt_id: str(replacement["exclusion_code"])
        for replacement in replacements
        for attempt_id in replacement["excluded_attempt_ids"]
    }
    technical_responses = [_read_json(root, path) for path in manifest["technical_failure_response_files"]]
    technical_response_ids: set[str] = set()
    for evidence in technical_responses:
        if not isinstance(evidence, Mapping):
            raise KnowledgePrecheckV4Error("member technical failure raw response must be an object")
        response = parse_raw_response_evidence(evidence, response_kind="member-technical-failure")
        attempt_id = str(evidence["attempt_id"])
        if attempt_id not in excluded_attempt_ids or attempt_id in technical_response_ids:
            raise KnowledgePrecheckV4Error("member technical failure raw response binding is invalid")
        validate_technical_failure_response(
            response,
            exclusion_code=replacement_code_by_attempt[attempt_id],
            packet=input_by_id[attempt_id],
            protocol=protocol,
        )
        technical_response_ids.add(attempt_id)
    if technical_response_ids != excluded_attempt_ids:
        raise KnowledgePrecheckV4Error("member technical failure raw response coverage is incomplete")

    final_responses = [_read_json(root, path) for path in manifest["member_final_response_files"]]
    final_response_by_id: dict[str, Mapping[str, Any]] = {}
    for evidence in final_responses:
        if not isinstance(evidence, Mapping):
            raise KnowledgePrecheckV4Error("member final raw response must be an object")
        response = parse_raw_response_evidence(evidence, response_kind="member-final")
        _closed_mapping(response, _RESPONSE_FIELDS, "member final response")
        attempt_id = str(evidence["attempt_id"])
        if attempt_id not in retained_attempt_ids or attempt_id in final_response_by_id:
            raise KnowledgePrecheckV4Error("member final raw response binding is invalid")
        final_response_by_id[attempt_id] = response
    if set(final_response_by_id) != retained_attempt_ids:
        raise KnowledgePrecheckV4Error("member final raw response coverage is incomplete")

    outputs = [_read_json(root, path) for path in manifest["model_output_files"]]
    output_by_id: dict[str, Mapping[str, Any]] = {}
    for output in outputs:
        if not isinstance(output, Mapping):
            raise KnowledgePrecheckV4Error("model output must be an object")
        validate_model_output(output, protocol)
        if _denylisted_keys(output, denylist):
            raise KnowledgePrecheckV4Error("model output contains a denylisted field")
        attempt_id = str(output["attempt_id"])
        packet = input_by_id.get(attempt_id)
        if packet is None or attempt_id not in retained_attempt_ids or attempt_id in output_by_id:
            raise KnowledgePrecheckV4Error("model output binding is invalid")
        if (
            packet["pair_id"] != output["pair_id"]
            or condition_from_packet(packet, protocol) != output["condition"]
            or packet["fresh_context_id_hash"] != output["fresh_context_id_hash"]
            or output["structured_response"] != final_response_by_id[attempt_id]
        ):
            raise KnowledgePrecheckV4Error("model output/input/raw-response binding is inconsistent")
        bound = []
        for exchange_id in output["helper_exchange_ids"]:
            exchange = exchange_by_id.get(exchange_id)
            if exchange is None or exchange["attempt_id"] != attempt_id:
                raise KnowledgePrecheckV4Error("model output references an unbound exchange")
            bound.append(exchange)
        output_by_id[attempt_id] = output

    blind_packets = [_read_json(root, path) for path in manifest["blind_packet_files"]]
    blind_by_id: dict[str, Mapping[str, Any]] = {}
    for packet in blind_packets:
        if not isinstance(packet, Mapping):
            raise KnowledgePrecheckV4Error("blind packet must be an object")
        attempt_id = str(packet.get("attempt_id"))
        output = output_by_id.get(attempt_id)
        if output is None or attempt_id in blind_by_id:
            raise KnowledgePrecheckV4Error("blind packet binding is invalid")
        bound = [exchange_by_id[item] for item in output["helper_exchange_ids"]]
        expected = build_blind_packet(
            output,
            tasks[str(output["pair_id"])],
            trace_by_id[attempt_id],
            bound,
            protocol["scorer_rubric"],
        )
        if packet != expected:
            raise KnowledgePrecheckV4Error("blind packet differs from its condition-blind projection")
        blind_by_id[attempt_id] = packet
    if set(blind_by_id) != set(output_by_id):
        raise KnowledgePrecheckV4Error("blind packet coverage is incomplete")

    scorer_responses = [_read_json(root, path) for path in manifest["scorer_response_files"]]
    scorer_response_by_id: dict[str, Mapping[str, Any]] = {}
    for evidence in scorer_responses:
        if not isinstance(evidence, Mapping):
            raise KnowledgePrecheckV4Error("scorer raw response must be an object")
        response = parse_raw_response_evidence(evidence, response_kind="scorer")
        validate_scorer_response(response)
        attempt_id = str(evidence["attempt_id"])
        if attempt_id not in output_by_id or attempt_id in scorer_response_by_id:
            raise KnowledgePrecheckV4Error("scorer raw response binding is invalid")
        scorer_response_by_id[attempt_id] = response
    if set(scorer_response_by_id) != set(output_by_id):
        raise KnowledgePrecheckV4Error("scorer raw response coverage is incomplete")

    scores = [_read_json(root, path) for path in manifest["score_files"]]
    score_by_id: dict[str, Mapping[str, Any]] = {}
    for score in scores:
        if not isinstance(score, Mapping):
            raise KnowledgePrecheckV4Error("score must be an object")
        validate_score(score)
        attempt_id = str(score["attempt_id"])
        if attempt_id not in output_by_id or attempt_id in score_by_id:
            raise KnowledgePrecheckV4Error("score attempt binding is invalid")
        if score["blind_packet_sha256"] != canonical_sha256(blind_by_id[attempt_id]):
            raise KnowledgePrecheckV4Error("score is not bound to its blind packet")
        if {field: score[field] for field in _SCORER_RESPONSE_FIELDS} != scorer_response_by_id[attempt_id]:
            raise KnowledgePrecheckV4Error("score differs from the raw scorer response")
        score_by_id[attempt_id] = score
    if set(score_by_id) != set(output_by_id):
        raise KnowledgePrecheckV4Error("score coverage is incomplete")

    adjudication = _read_json(root, str(manifest["adjudication_file"]))
    if not isinstance(adjudication, Mapping) or adjudication != {"overrides": []}:
        raise KnowledgePrecheckV4Error("post-hoc score overrides are disabled")

    records: list[dict[str, Any]] = []
    for output in sorted(outputs, key=lambda item: (item["pair_id"], item["condition"])):
        attempt_id = str(output["attempt_id"])
        task = tasks[str(output["pair_id"])]
        gold = task["gold"]
        trace = trace_by_id[attempt_id]
        score = score_by_id[attempt_id]
        bound = [exchange_by_id[item] for item in output["helper_exchange_ids"]]
        f3_refs = [obj["object_uid"] for exchange in bound for obj in exchange["f3_objects"]]
        allow = set(gold["expected_f3_allow_set"])
        f3_true = len(set(f3_refs) & allow)
        false_f3 = len([ref for ref in f3_refs if ref not in allow])
        actual_f2 = int(any(exchange["operation"] == "find-fact-object-candidates" for exchange in bound))
        selected = set(output["structured_response"]["selected_refs"])
        records.append(
            {
                "attempt_id": attempt_id,
                "pair_id": output["pair_id"],
                "family": task["family"],
                "case_kind": task["case_kind"],
                "condition": output["condition"],
                "model_name": output["model_name"],
                "agent_runtime_name": output["agent_runtime_name"],
                "fresh_context_id_hash": output["fresh_context_id_hash"],
                "model_input_sha256": canonical_sha256(input_by_id[attempt_id]),
                "trigger_trace_sha256": canonical_sha256(trace),
                "response": output["structured_response"],
                "helper_exchange_ids": output["helper_exchange_ids"],
                "triggered_f2": actual_f2,
                "trigger_decision_correct": int(bool(actual_f2) == gold["expected_f2_trigger"]),
                "unnecessary_f2": int(actual_f2 and not gold["expected_f2_trigger"]),
                "f3_expansion_count": len(f3_refs),
                "f3_true_positive_count": f3_true,
                "false_f3_expansion": false_f3,
                "f3_precision": (f3_true / len(f3_refs)) if f3_refs else (1.0 if not allow else 0.0),
                "f3_recall": (f3_true / len(allow)) if allow else (1.0 if not f3_refs else 0.0),
                "selection_correct": int(selected == set(gold["applicable_refs"])),
                "knowledge_adjusted_first_legal_action_correct": int(
                    score["knowledge_adjusted_first_legal_action_correct"]
                ),
                "action_changed": int(score["action_changed"]),
                "strong_reuse": int(score["strong_reuse"]),
                "correct_non_use": int(score["correct_non_use"]),
                "helper_call_count": len(bound),
                "usage": output["usage"],
                "latency": output["latency"],
            }
        )

    metric_names = (
        "trigger_decision_correct",
        "unnecessary_f2",
        "false_f3_expansion",
        "selection_correct",
        "knowledge_adjusted_first_legal_action_correct",
        "action_changed",
        "strong_reuse",
        "correct_non_use",
        "helper_call_count",
        "f3_expansion_count",
    )
    by_key = {(record["pair_id"], record["condition"]): record for record in records}
    paired_analysis: dict[str, Any] = {}
    for metric in metric_names:
        delta = [
            float(by_key[(pair_id, "struct-enhanced")][metric]) - float(by_key[(pair_id, "struct-baseline")][metric])
            for pair_id in sorted(tasks)
        ]
        paired_analysis[metric] = paired_estimate(delta)

    thresholds = protocol["adoption_thresholds"]
    applicable_ids = thresholds["applicable_pair_ids"]
    non_use_ids = thresholds["non_use_pair_ids"]
    no_trigger_ids = thresholds["no_trigger_pair_ids"]
    trigger_sums = _condition_sums(records, "trigger_decision_correct")
    strong_sums = {
        condition: sum(int(by_key[(pair_id, condition)]["strong_reuse"]) for pair_id in applicable_ids)
        for condition in CONDITIONS
    }
    selection_sums = _condition_sums(records, "selection_correct")
    first_action_sums = _condition_sums(records, "knowledge_adjusted_first_legal_action_correct")
    false_f3_sums = _condition_sums(records, "false_f3_expansion")
    non_use_correct_sums = _condition_sums(records, "correct_non_use")
    unnecessary_f2_sums = _condition_sums(records, "unnecessary_f2")

    # V4 threshold gates: enhanced must not significantly regress on baseline
    trigger_gate = (
        trigger_sums["struct-enhanced"] >= thresholds.get("trigger_correctness_absolute_minimum", 15)
    )
    non_use_gate = non_use_correct_sums["struct-enhanced"] >= non_use_correct_sums.get("struct-baseline", 0)
    false_f3_gate = bool(
        false_f3_sums["struct-enhanced"] <= false_f3_sums.get("struct-baseline", 0)
    )
    unnecessary_f2_gate = unnecessary_f2_sums["struct-enhanced"] <= unnecessary_f2_sums.get("struct-baseline", 0)

    gates = {
        "trigger_correctness_absolute": trigger_gate,
        "non_use_correct_not_decreased": non_use_gate,
        "false_f3_not_increased": false_f3_gate,
        "unnecessary_f2_not_increased": unnecessary_f2_gate,
        "selection_not_decreased": selection_sums["struct-enhanced"] >= selection_sums.get("struct-baseline", 0),
        "first_legal_action_not_decreased": first_action_sums["struct-enhanced"] >= first_action_sums.get("struct-baseline", 0),
        "policy_capacity": True,
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
        "member_launches": process_launches,
        "scorer_contexts": retained_scorer_contexts + len(scorer_technical_failures),
        "retained_scorer_runs": retained_scorer_contexts,
        "scorer_technical_failures": len(scorer_technical_failures),
        "runner_identity": protocol["runner_identity_strategy"],
        "paired_analysis": paired_analysis,
        "condition_totals": {
            "trigger_correct": trigger_sums,
            "strong_reuse_applicable": strong_sums,
            "selection_correct": selection_sums,
            "first_legal_action_correct": first_action_sums,
            "correct_non_use": non_use_correct_sums,
            "false_f3_expansion": false_f3_sums,
            "helper_calls": _condition_sums(records, "helper_call_count"),
            "f3_expansions": _condition_sums(records, "f3_expansion_count"),
            "unnecessary_f2": unnecessary_f2_sums,
        },
        "strata": _strata(records, tasks),
        "adoption_gates": gates,
        "adoption_decision": (
            "supports-enhanced-fields" if support else "do-not-support-enhanced-fields"
        ),
        "usage_availability": sorted({str(record["usage"]) for record in records}),
        "latency_availability": sorted({str(record["latency"]) for record in records}),
    }
    lines = [
        "# F2 structure paired experiment (v4)",
        "",
        f"- Evidence manifest SHA-256: `{results['evidence_manifest_sha256']}`",
        f"- Protocol SHA-256: `{results['protocol_sha256']}`",
        f"- Source snapshot SHA-256: `{results['source_snapshot_sha256']}`",
        f"- Retained pairs: {results['retained_pairs']}",
        f"- Member runs / total scorer contexts: {results['member_runs']} / {results['scorer_contexts']}",
        (
            "- Retained scorer runs / invalid scorer responses: "
            f"{results['retained_scorer_runs']} / {results['scorer_technical_failures']}"
        ),
        f"- Decision: **{results['adoption_decision']}**",
        "",
        "## Gate observations",
        "",
    ]
    for gate, passed in gates.items():
        lines.append(f"- {gate}: {'PASS' if passed else 'FAIL'}")
    lines.extend(
        [
            "",
            "## Condition totals",
            "",
            "```json",
            json.dumps(results["condition_totals"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Interpretation boundary",
            "",
            (
                "This source-complete paired run tests whether the three new F2 fields "
                "(trigger_signal, scope_of_impact, action_relevance) independently improve "
                "the model's F2 trigger decision and F2→F3 consumption.  Both arms share "
                "the identical L1-baseline trigger policy; the only difference is whether "
                "the F2 cards include the three new fields.  The experiment does not "
                "establish broad causal generalization beyond the frozen 18 tasks and "
                "observable runtime."
            ),
            "",
        ]
    )
    return {
        "records.json": json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
        "results.json": json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
        "report.md": "\n".join(lines).encode("utf-8"),
    }


__all__ = [
    "ALLOWED_KNOWLEDGE_OPERATIONS",
    "CASE_KINDS",
    "CONDITIONS",
    "EVIDENCE_SCHEMA_VERSION",
    "KnowledgePrecheckV4Error",
    "MAX_MEMBER_LAUNCHES",
    "MAX_PAIR_ATTEMPTS",
    "MAX_REPLACEMENTS",
    "MAX_SCORER_CONTEXTS",
    "POLICY_MAX_BYTES",
    "POLICY_MAX_LINES",
    "RETAINED_PAIR_TARGET",
    "RUN_TIMEOUT_SECONDS",
    "SCHEMA_VERSION",
    "TASK_FAMILIES",
    "TECHNICAL_EXCLUSION_CODES",
    "TOTAL_TIMEOUT_SECONDS",
    "ReadOnlyKnowledgeGateway",
    "build_blind_packet",
    "build_model_input_packet",
    "build_raw_response_evidence",
    "build_trigger_trace",
    "bytes_sha256",
    "canonical_json_bytes",
    "canonical_sha256",
    "compile_evidence_bundle",
    "condition_from_packet",
    "is_valid_structured_response",
    "logical_line_count",
    "parse_raw_response_evidence",
    "subprocess_helper_dispatch",
    "validate_f3_decision_response",
    "validate_model_input_packet",
    "validate_model_output",
    "validate_protocol",
    "validate_score",
    "validate_trigger_trace",
    "_strip_f2_cards",
]