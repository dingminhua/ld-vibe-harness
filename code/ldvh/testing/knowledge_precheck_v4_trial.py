"""Runner-owned command surface for the v4 F2 structure paired trial."""

from __future__ import annotations

import argparse
import json
import secrets
import shutil
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ldvh.testing.knowledge_precheck_v4 import (
    CONDITIONS,
    EVIDENCE_SCHEMA_VERSION,
    MAX_MEMBER_LAUNCHES,
    MAX_REPLACEMENTS,
    MAX_SCORER_CONTEXTS,
    RETAINED_PAIR_TARGET,
    TECHNICAL_EXCLUSION_CODES,
    ReadOnlyKnowledgeGateway,
    build_blind_packet,
    build_model_input_packet,
    build_raw_response_evidence,
    build_trigger_trace,
    bytes_sha256,
    canonical_sha256,
    compile_evidence_bundle,
    condition_from_packet,
    is_valid_structured_response,
    parse_raw_response_evidence,
    subprocess_helper_dispatch,
    validate_f3_decision_response,
    validate_model_input_packet,
    validate_model_output,
    validate_protocol,
    validate_score,
    validate_scorer_response,
    validate_technical_failure_response,
    validate_trigger_trace,
)


class TrialRunnerError(ValueError):
    """Raised before a partial or out-of-order artifact is accepted."""


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TrialRunnerError(f"cannot read {label}") from error
    if not isinstance(value, dict):
        raise TrialRunnerError(f"{label} must be a JSON object")
    return value


def _write_new_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise TrialRunnerError(f"refusing to replace existing evidence: {path.name}")
    path.write_bytes(_json_bytes(value))


def _replace_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    temporary.write_bytes(_json_bytes(value))
    temporary.replace(path)


def _bundle(path: str) -> Path:
    root = Path(path).resolve(strict=True)
    if not root.is_dir():
        raise TrialRunnerError("bundle must be a directory")
    if (root / "manifest.json").exists():
        raise TrialRunnerError("bundle is already sealed")
    return root


def _protocol(root: Path) -> dict[str, Any]:
    protocol = _read_object(root / "protocol.json", "protocol")
    problems = validate_protocol(protocol)
    if problems:
        raise TrialRunnerError(f"protocol is invalid: {','.join(problems)}")
    return protocol


def _attempt_inputs(root: Path) -> list[dict[str, Any]]:
    return [_read_object(path, "model input") for path in sorted((root / "model-inputs").glob("*.json"))]


def _excluded_attempt_ids(ledger: Mapping[str, Any]) -> set[str]:
    replacements = ledger.get("technical_replacements")
    if not isinstance(replacements, list):
        raise TrialRunnerError("technical replacement ledger is invalid")
    excluded: list[str] = []
    for replacement in replacements:
        if not isinstance(replacement, Mapping):
            raise TrialRunnerError("technical replacement ledger is invalid")
        attempt_ids = replacement.get("excluded_attempt_ids")
        if not isinstance(attempt_ids, list) or len(attempt_ids) != len(CONDITIONS):
            raise TrialRunnerError("technical replacement ledger is invalid")
        excluded.extend(str(attempt_id) for attempt_id in attempt_ids)
    if len(excluded) != len(set(excluded)):
        raise TrialRunnerError("technical replacement attempts are duplicated")
    return set(excluded)


def _active_launch(root: Path, attempt_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    ledger = _read_object(root / "attempt-ledger.json", "attempt ledger")
    launches = [launch for launch in ledger.get("launches", []) if launch.get("attempt_id") == attempt_id]
    if len(launches) != 1 or launches[0].get("finished_at") is not None:
        raise TrialRunnerError("member launch is not active")
    if attempt_id in _excluded_attempt_ids(ledger):
        raise TrialRunnerError("technical replacement attempt is not active")
    return ledger, launches[0]


def initialize_bundle(*, artifact_root: Path, bundle_root: Path) -> None:
    source = artifact_root.resolve(strict=True)
    if bundle_root.exists() and any(bundle_root.iterdir()):
        raise TrialRunnerError("bundle root must not exist or must be empty")
    bundle_root.mkdir(parents=True, exist_ok=True)
    for name in ("protocol.json", "source-snapshot.json"):
        shutil.copyfile(source / name, bundle_root / name)
    source_observations = source / "source-observations"
    if not source_observations.is_dir():
        raise TrialRunnerError("source observations are missing")
    shutil.copytree(source_observations, bundle_root / "source-observations")
    protocol = _protocol(bundle_root)
    snapshot = _read_object(bundle_root / "source-snapshot.json", "source snapshot")
    if protocol["source_snapshot"]["content_sha256"] != canonical_sha256(snapshot):
        raise TrialRunnerError("source snapshot does not match protocol")
    _write_new_json(
        bundle_root / "attempt-ledger.json",
        {
            "pair_attempts": 0,
            "technical_replacements": [],
            "process_launches": 0,
            "retained_scorer_contexts": 0,
            "scorer_technical_failures": [],
            "launches": [],
            "scorer_runs": [],
        },
    )
    _write_new_json(bundle_root / "adjudication.json", {"overrides": []})


def prepare_attempt(*, root: Path, pair_id: str, condition: str, fresh_context_id_hash: str) -> dict[str, Any]:
    protocol = _protocol(root)
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}
    if pair_id not in tasks:
        raise TrialRunnerError("pair is not frozen")
    if condition not in CONDITIONS:
        raise TrialRunnerError("condition is invalid")
    packets = _attempt_inputs(root)
    ledger = _read_object(root / "attempt-ledger.json", "attempt ledger")
    launches = ledger.get("launches")
    if not isinstance(launches, list):
        raise TrialRunnerError("member launch ledger is invalid")
    same_pair = [launch for launch in launches if launch.get("pair_id") == pair_id]
    order_index = [task["pair_id"] for task in protocol["tasks"]].index(pair_id)
    expected_order = protocol["condition_orders"][order_index]
    replacements = ledger.get("technical_replacements")
    if not isinstance(replacements, list) or len(replacements) > MAX_REPLACEMENTS:
        raise TrialRunnerError("technical replacement ledger is invalid")
    pair_replacements = [replacement for replacement in replacements if replacement.get("pair_id") == pair_id]
    if len(same_pair) >= len(CONDITIONS) * (1 + len(pair_replacements)):
        raise TrialRunnerError("a new whole-pair attempt requires a recorded technical exclusion")
    if len(same_pair) % len(CONDITIONS) == 0 and same_pair:
        prior_attempt_ids = [str(launch["attempt_id"]) for launch in same_pair[-len(CONDITIONS) :]]
        if not pair_replacements or pair_replacements[-1].get("excluded_attempt_ids") != prior_attempt_ids:
            raise TrialRunnerError("a new whole-pair attempt requires exclusion of the prior pair")
    if condition != expected_order[len(same_pair) % len(CONDITIONS)]:
        raise TrialRunnerError("attempt violates the frozen condition order or same-arm retry rule")
    if any(packet["fresh_context_id_hash"] == fresh_context_id_hash for packet in packets):
        raise TrialRunnerError("fresh context hash must be unique")
    if len(packets) >= MAX_MEMBER_LAUNCHES:
        raise TrialRunnerError("member launch ceiling reached")

    attempt_id = f"attempt-{secrets.token_hex(12)}"
    packet = build_model_input_packet(
        protocol,
        pair_id=pair_id,
        condition=condition,
        attempt_id=attempt_id,
        fresh_context_id_hash=fresh_context_id_hash,
    )
    _write_new_json(root / "model-inputs" / f"{attempt_id}.json", packet)
    ledger["process_launches"] += 1
    if len(same_pair) % len(CONDITIONS) == 0:
        ledger["pair_attempts"] += 1
    ledger["launches"].append(
        {
            "sequence": ledger["process_launches"],
            "attempt_id": attempt_id,
            "pair_id": pair_id,
            "condition": condition,
            "started_at": _now(),
            "finished_at": None,
        }
    )
    _replace_json(root / "attempt-ledger.json", ledger)
    return packet


def record_trigger(*, root: Path, attempt_id: str, trace_file: Path) -> dict[str, Any]:
    _active_launch(root, attempt_id)
    protocol = _protocol(root)
    packet = _read_object(root / "model-inputs" / f"{attempt_id}.json", "model input")
    validate_model_input_packet(packet, protocol)
    if list((root / "helper-exchanges").glob(f"{attempt_id}-*.json")):
        raise TrialRunnerError("trigger trace must be recorded before any Helper call")
    if (root / "model-outputs" / f"{attempt_id}.json").exists():
        raise TrialRunnerError("trigger trace must precede final output")
    raw_response = trace_file.resolve(strict=True).read_bytes()
    response = _read_object(trace_file.resolve(strict=True), "member trigger response")
    trace = build_trigger_trace(response, packet, protocol)
    evidence = build_raw_response_evidence(
        attempt_id=attempt_id,
        response_kind="member-trigger",
        raw_response=raw_response,
    )
    _write_new_json(root / "member-trigger-responses" / f"{attempt_id}.json", evidence)
    _write_new_json(root / "trigger-traces" / f"{attempt_id}.json", trace)
    return trace


def record_f3_decision(*, root: Path, attempt_id: str, decision_file: Path) -> dict[str, Any]:
    _active_launch(root, attempt_id)
    protocol = _protocol(root)
    packet = _read_object(root / "model-inputs" / f"{attempt_id}.json", "model input")
    validate_model_input_packet(packet, protocol)
    trace = _read_object(root / "trigger-traces" / f"{attempt_id}.json", "trigger trace")
    validate_trigger_trace(trace, packet, protocol)
    if not trace["triggered"]:
        raise TrialRunnerError("a negative trigger decision forbids an F3 decision")
    existing = sorted((root / "helper-exchanges").glob(f"{attempt_id}-*.json"))
    operations = [_read_object(path, "Helper exchange")["operation"] for path in existing]
    if operations != ["find-fact-object-candidates"]:
        raise TrialRunnerError("the member F3 decision must follow exactly one F2 call")
    if (root / "model-outputs" / f"{attempt_id}.json").exists():
        raise TrialRunnerError("the member F3 decision must precede final output")
    raw_response = decision_file.resolve(strict=True).read_bytes()
    response = _read_object(decision_file.resolve(strict=True), "member F3 decision response")
    snapshot = _read_object(root / "source-snapshot.json", "source snapshot")
    validate_f3_decision_response(
        response,
        family=str(packet["family"]),
        snapshot_families=snapshot["knowledge_ref_families"],
    )
    evidence = build_raw_response_evidence(
        attempt_id=attempt_id,
        response_kind="member-f3-decision",
        raw_response=raw_response,
    )
    _write_new_json(root / "member-f3-decision-responses" / f"{attempt_id}.json", evidence)
    return response


def helper_call(
    *,
    root: Path,
    repository_root: Path,
    ldvh_executable: Path,
    attempt_id: str,
    operation: str,
    request_file: Path,
) -> dict[str, Any]:
    _active_launch(root, attempt_id)
    protocol = _protocol(root)
    packet = _read_object(root / "model-inputs" / f"{attempt_id}.json", "model input")
    validate_model_input_packet(packet, protocol)
    trace_path = root / "trigger-traces" / f"{attempt_id}.json"
    if not trace_path.is_file():
        raise TrialRunnerError("a pre-F2 trigger trace is required")
    trace = _read_object(trace_path, "trigger trace")
    validate_trigger_trace(trace, packet, protocol)
    if not trace["triggered"]:
        raise TrialRunnerError("a negative trigger decision forbids Helper lookup")
    if (root / "model-outputs" / f"{attempt_id}.json").exists():
        raise TrialRunnerError("cannot call Helper after final output")
    request = _read_object(request_file.resolve(strict=True), "Helper request")
    arguments = request.get("arguments")
    if operation == "find-fact-object-candidates" and (
        not isinstance(arguments, Mapping) or arguments.get("fact_type_keys") != [packet["family"]]
    ):
        raise TrialRunnerError("F2 request family must match the member input")
    existing = sorted((root / "helper-exchanges").glob(f"{attempt_id}-*.json"))
    prior_operations = [_read_object(path, "Helper exchange")["operation"] for path in existing]
    if operation == "find-fact-object-candidates" and prior_operations:
        raise TrialRunnerError("F2 must be the first and only discovery call")
    if operation == "read-fact-objects" and prior_operations != ["find-fact-object-candidates"]:
        raise TrialRunnerError("one F3 call is allowed only after the attempt's single F2 call")
    snapshot = _read_object(root / "source-snapshot.json", "source snapshot")
    if operation == "read-fact-objects":
        refs = arguments.get("fact_refs") if isinstance(arguments, Mapping) else None
        families = snapshot.get("knowledge_ref_families")
        if (
            not isinstance(refs, list)
            or not isinstance(families, Mapping)
            or any(
                not isinstance(ref, Mapping) or families.get(ref.get("object_uid")) != packet["family"] for ref in refs
            )
        ):
            raise TrialRunnerError("F3 request UIDs must be frozen members of the input family")
        decision_path = root / "member-f3-decision-responses" / f"{attempt_id}.json"
        if not decision_path.is_file():
            raise TrialRunnerError("a raw member F3 decision is required before F3")
        decision_evidence = _read_object(decision_path, "member F3 decision evidence")
        decision = parse_raw_response_evidence(decision_evidence, response_kind="member-f3-decision")
        decided_refs = validate_f3_decision_response(
            decision,
            family=str(packet["family"]),
            snapshot_families=snapshot["knowledge_ref_families"],
        )
        if [ref["object_uid"] for ref in refs] != decided_refs:
            raise TrialRunnerError("F3 request differs from the raw member decision")
    card_layer = str(packet.get("card_layer", "struct-enhanced"))
    gateway = ReadOnlyKnowledgeGateway(
        subprocess_helper_dispatch(repository_root=repository_root, ldvh_executable=ldvh_executable),
        expected_f2_cards_enhanced=snapshot["family_cards_enhanced"],
        expected_f2_cards_stripped=snapshot["family_cards_stripped"],
        expected_f3_fingerprints=snapshot["knowledge_ref_fingerprints"],
    )
    exchange_id = f"exchange-{secrets.token_hex(12)}"
    exchange = gateway.call(
        operation, request,
        exchange_id=exchange_id,
        attempt_id=attempt_id,
        card_layer=card_layer,
    )
    if any(item["fact_type_key"] != packet["family"] for item in exchange["f3_objects"]):
        raise TrialRunnerError("F3 result family does not match the member input")
    sequence = len(existing) + 1
    _write_new_json(root / "helper-exchanges" / f"{attempt_id}-{sequence:02d}-{exchange_id}.json", exchange)
    return {"exchange_id": exchange_id, "helper_response": json.loads(exchange["raw_response_utf8"])}


def finalize_output(*, root: Path, attempt_id: str, response_file: Path) -> dict[str, Any]:
    ledger, launch = _active_launch(root, attempt_id)
    protocol = _protocol(root)
    packet = _read_object(root / "model-inputs" / f"{attempt_id}.json", "model input")
    validate_model_input_packet(packet, protocol)
    trace = _read_object(root / "trigger-traces" / f"{attempt_id}.json", "trigger trace")
    validate_trigger_trace(trace, packet, protocol)
    output_path = root / "model-outputs" / f"{attempt_id}.json"
    if output_path.exists():
        raise TrialRunnerError("model output is already finalized")
    raw_response = response_file.resolve(strict=True).read_bytes()
    response = _read_object(response_file.resolve(strict=True), "structured response")
    exchange_files = sorted((root / "helper-exchanges").glob(f"{attempt_id}-*.json"))
    exchange_ids = [_read_object(path, "Helper exchange")["exchange_id"] for path in exchange_files]
    if bool(exchange_ids) != trace["triggered"]:
        raise TrialRunnerError("trigger decision and actual F2 trace disagree")
    decision_path = root / "member-f3-decision-responses" / f"{attempt_id}.json"
    if trace["triggered"] != decision_path.is_file():
        raise TrialRunnerError("triggered attempts require one raw post-F2 member decision")
    if decision_path.is_file():
        decision = parse_raw_response_evidence(
            _read_object(decision_path, "member F3 decision evidence"),
            response_kind="member-f3-decision",
        )
        decided_refs = validate_f3_decision_response(
            decision,
            family=str(packet["family"]),
            snapshot_families=_read_object(root / "source-snapshot.json", "source snapshot")["knowledge_ref_families"],
        )
        expanded_refs = [
            obj["object_uid"] for path in exchange_files for obj in _read_object(path, "Helper exchange")["f3_objects"]
        ]
        if expanded_refs != decided_refs:
            raise TrialRunnerError("actual F3 expansion differs from the raw member decision")
    output = {
        "attempt_id": attempt_id,
        "pair_id": packet["pair_id"],
        "condition": condition_from_packet(packet, protocol),
        "model_name": None,
        "agent_runtime_name": "codex-native-subagent",
        "fresh_context_id_hash": packet["fresh_context_id_hash"],
        "structured_response": response,
        "helper_exchange_ids": exchange_ids,
        "usage": "unavailable",
        "latency": "unavailable",
    }
    validate_model_output(output, protocol)
    expanded_refs = []
    for path in exchange_files:
        exchange = _read_object(path, "Helper exchange")
        expanded_refs.extend(obj["object_uid"] for obj in exchange["f3_objects"])
    if any(ref not in expanded_refs for ref in response["selected_refs"]):
        raise TrialRunnerError("selected refs must have been expanded by F3")
    evidence = build_raw_response_evidence(
        attempt_id=attempt_id,
        response_kind="member-final",
        raw_response=raw_response,
    )
    _write_new_json(root / "member-final-responses" / f"{attempt_id}.json", evidence)
    _write_new_json(output_path, output)
    launch["finished_at"] = _now()
    _replace_json(root / "attempt-ledger.json", ledger)
    return output


def exclude_pair(
    *,
    root: Path,
    pair_id: str,
    exclusion_code: str,
    failure_files: Mapping[str, Path],
) -> dict[str, Any]:
    """Exclude exactly the latest two-arm wave and preserve both raw failures."""

    protocol = _protocol(root)
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}
    if pair_id not in tasks:
        raise TrialRunnerError("pair is not frozen")
    if exclusion_code not in TECHNICAL_EXCLUSION_CODES:
        raise TrialRunnerError("replacement uses a nontechnical exclusion")
    ledger = _read_object(root / "attempt-ledger.json", "attempt ledger")
    replacements = ledger.get("technical_replacements")
    launches = ledger.get("launches")
    if not isinstance(replacements, list) or not isinstance(launches, list):
        raise TrialRunnerError("attempt ledger is invalid")
    if len(replacements) >= MAX_REPLACEMENTS:
        raise TrialRunnerError("technical replacement ceiling reached")
    pair_launches = [launch for launch in launches if launch.get("pair_id") == pair_id]
    if len(pair_launches) < len(CONDITIONS) or len(pair_launches) % len(CONDITIONS):
        raise TrialRunnerError("technical exclusion requires both arms of the latest pair attempt")
    current = pair_launches[-len(CONDITIONS) :]
    order_index = [task["pair_id"] for task in protocol["tasks"]].index(pair_id)
    expected_order = protocol["condition_orders"][order_index]
    if [launch.get("condition") for launch in current] != expected_order:
        raise TrialRunnerError("technical exclusion does not bind a frozen whole pair")
    attempt_ids = [str(launch.get("attempt_id")) for launch in current]
    if set(failure_files) != set(attempt_ids):
        raise TrialRunnerError("technical failure files must bind both and only the latest pair arms")
    if any(launch.get("finished_at") is not None for launch in current):
        raise TrialRunnerError("technical exclusion requires two active member launches")
    if set(attempt_ids) & _excluded_attempt_ids(ledger):
        raise TrialRunnerError("technical replacement attempt is already excluded")

    has_trigger_evidence = (root / "member-trigger-responses" / f"{attempt_ids[0]}.json").is_file()
    for attempt_id in attempt_ids:
        raw_exists = (root / "member-trigger-responses" / f"{attempt_id}.json").is_file()
        trace_exists = (root / "trigger-traces" / f"{attempt_id}.json").is_file()
        if raw_exists != trace_exists or raw_exists != has_trigger_evidence:
            raise TrialRunnerError("whole-pair technical exclusion must bind one consistent evidence stage")

    snapshot = _read_object(root / "source-snapshot.json", "source snapshot")
    for attempt_id in attempt_ids:
        packet = _read_object(root / "model-inputs" / f"{attempt_id}.json", "model input")
        validate_model_input_packet(packet, protocol)
        exchange_files = sorted((root / "helper-exchanges").glob(f"{attempt_id}-*.json"))
        exchanges = [_read_object(path, "Helper exchange") for path in exchange_files]
        decision_path = root / "member-f3-decision-responses" / f"{attempt_id}.json"
        if has_trigger_evidence:
            trigger_evidence = _read_object(
                root / "member-trigger-responses" / f"{attempt_id}.json",
                "member trigger response",
            )
            trigger_response = parse_raw_response_evidence(trigger_evidence, response_kind="member-trigger")
            trace = _read_object(root / "trigger-traces" / f"{attempt_id}.json", "trigger trace")
            if build_trigger_trace(trigger_response, packet, protocol) != trace:
                raise TrialRunnerError("technical attempt trigger evidence is inconsistent")
            if not exchanges and decision_path.exists():
                raise TrialRunnerError("technical attempt F3 decision without F2 exchange")
        elif exchanges or decision_path.exists():
            raise TrialRunnerError("pre-trigger technical failure cannot retain later-stage evidence")
        for directory in (
            "member-final-responses",
            "model-outputs",
            "blind-packets",
            "scorer-responses",
            "scores",
            "technical-failure-responses",
        ):
            if (root / directory / f"{attempt_id}.json").exists():
                raise TrialRunnerError("technical exclusion cannot replace existing terminal evidence")
        raw_response = failure_files[attempt_id].resolve(strict=True).read_bytes()
        response = _read_object(failure_files[attempt_id].resolve(strict=True), "technical failure response")
        validate_technical_failure_response(
            response,
            exclusion_code=exclusion_code,
            packet=packet,
            protocol=protocol,
        )
        evidence_by_attempt = {
            attempt_id: build_raw_response_evidence(
                attempt_id=attempt_id,
                response_kind="member-technical-failure",
                raw_response=raw_response,
            )
        }
        for eid, ev in evidence_by_attempt.items():
            _write_new_json(
                root / "technical-failure-responses" / f"{eid}.json",
                ev,
            )

    finished_at = _now()
    for launch in current:
        launch["finished_at"] = finished_at
    replacement = {
        "pair_id": pair_id,
        "exclusion_code": exclusion_code,
        "excluded_attempt_ids": attempt_ids,
    }
    replacements.append(replacement)
    _replace_json(root / "attempt-ledger.json", ledger)
    return replacement


def build_attempt_blind_packet(*, root: Path, attempt_id: str) -> dict[str, Any]:
    protocol = _protocol(root)
    output = _read_object(root / "model-outputs" / f"{attempt_id}.json", "model output")
    validate_model_output(output, protocol)
    trace = _read_object(root / "trigger-traces" / f"{attempt_id}.json", "trigger trace")
    packet = _read_object(root / "model-inputs" / f"{attempt_id}.json", "model input")
    validate_trigger_trace(trace, packet, protocol)
    task = next(task for task in protocol["tasks"] if task["pair_id"] == output["pair_id"])
    exchanges = [
        _read_object(path, "Helper exchange")
        for path in sorted((root / "helper-exchanges").glob(f"{attempt_id}-*.json"))
    ]
    blind = build_blind_packet(output, task, trace, exchanges, protocol["scorer_rubric"])
    _write_new_json(root / "blind-packets" / f"{attempt_id}.json", blind)
    return blind


def record_score(
    *,
    root: Path,
    attempt_id: str,
    score_file: Path,
    fresh_scorer_context_id_hash: str,
) -> dict[str, Any]:
    blind_path = root / "blind-packets" / f"{attempt_id}.json"
    if not blind_path.is_file():
        raise TrialRunnerError("blind packet must exist before scoring")
    blind = _read_object(blind_path, "blind packet")
    raw_response = score_file.resolve(strict=True).read_bytes()
    response = _read_object(score_file.resolve(strict=True), "scorer response")
    validate_scorer_response(response)
    score = {
        "attempt_id": attempt_id,
        "blind_packet_sha256": canonical_sha256(blind),
        "scorer_model_name": None,
        "scorer_runtime_name": "codex-native-subagent",
        "fresh_scorer_context_id_hash": fresh_scorer_context_id_hash,
        **response,
    }
    validate_score(score)
    ledger = _read_object(root / "attempt-ledger.json", "attempt ledger")
    technical_failures = ledger.get("scorer_technical_failures")
    if not isinstance(technical_failures, list):
        raise TrialRunnerError("scorer technical failure ledger is invalid")
    existing_scores = [_read_object(path, "score") for path in sorted((root / "scores").glob("*.json"))]
    if any(old["fresh_scorer_context_id_hash"] == score["fresh_scorer_context_id_hash"] for old in existing_scores):
        raise TrialRunnerError("fresh scorer context hash must be unique")
    if any(
        failure.get("fresh_scorer_context_id_hash") == score["fresh_scorer_context_id_hash"]
        for failure in technical_failures
        if isinstance(failure, Mapping)
    ):
        raise TrialRunnerError("fresh scorer context hash must be unique")
    if len(existing_scores) + len(technical_failures) >= MAX_SCORER_CONTEXTS:
        raise TrialRunnerError("scorer context ceiling reached")
    evidence = build_raw_response_evidence(
        attempt_id=attempt_id,
        response_kind="scorer",
        raw_response=raw_response,
    )
    _write_new_json(root / "scorer-responses" / f"{attempt_id}.json", evidence)
    _write_new_json(root / "scores" / f"{attempt_id}.json", score)
    ledger["retained_scorer_contexts"] += 1
    ledger["scorer_runs"].append(
        {
            "sequence": ledger["retained_scorer_contexts"],
            "attempt_id": attempt_id,
            "recorded_at": _now(),
        }
    )
    _replace_json(root / "attempt-ledger.json", ledger)
    return score


def record_scorer_technical_failure(
    *,
    root: Path,
    attempt_id: str,
    response_file: Path,
    fresh_scorer_context_id_hash: str,
) -> dict[str, Any]:
    if not (root / "blind-packets" / f"{attempt_id}.json").is_file():
        raise TrialRunnerError("blind packet must exist before scoring")
    try:
        if len(fresh_scorer_context_id_hash) != 64:
            raise ValueError
        int(fresh_scorer_context_id_hash, 16)
    except (TypeError, ValueError) as error:
        raise TrialRunnerError("fresh scorer context hash must be lowercase SHA-256 hex") from error
    if fresh_scorer_context_id_hash != fresh_scorer_context_id_hash.lower():
        raise TrialRunnerError("fresh scorer context hash must be lowercase SHA-256 hex")

    raw_response = response_file.resolve(strict=True).read_bytes()
    response = _read_object(response_file.resolve(strict=True), "scorer technical failure response")
    try:
        validate_scorer_response(response)
    except ValueError:
        pass
    else:
        raise TrialRunnerError("scorer technical failure response must be invalid")

    ledger = _read_object(root / "attempt-ledger.json", "attempt ledger")
    technical_failures = ledger.get("scorer_technical_failures")
    if not isinstance(technical_failures, list):
        raise TrialRunnerError("scorer technical failure ledger is invalid")
    if any(
        isinstance(failure, Mapping) and failure.get("attempt_id") == attempt_id
        for failure in technical_failures
    ):
        raise TrialRunnerError("scorer technical failure attempt is duplicated")
    existing_scores = [_read_object(path, "score") for path in sorted((root / "scores").glob("*.json"))]
    used_hashes = {
        str(score.get("fresh_scorer_context_id_hash")) for score in existing_scores
    } | {
        str(failure.get("fresh_scorer_context_id_hash"))
        for failure in technical_failures
        if isinstance(failure, Mapping)
    }
    if fresh_scorer_context_id_hash in used_hashes:
        raise TrialRunnerError("fresh scorer context hash must be unique")
    if len(existing_scores) + len(technical_failures) >= MAX_SCORER_CONTEXTS:
        raise TrialRunnerError("scorer context ceiling reached")

    evidence = build_raw_response_evidence(
        attempt_id=attempt_id,
        response_kind="scorer-technical-failure",
        raw_response=raw_response,
    )
    _write_new_json(
        root / "scorer-technical-failure-responses" / f"{attempt_id}.json",
        evidence,
    )
    entry = {
        "sequence": len(technical_failures) + 1,
        "attempt_id": attempt_id,
        "fresh_scorer_context_id_hash": fresh_scorer_context_id_hash,
        "failure_code": "invalid_scorer_response",
    }
    technical_failures.append(entry)
    _replace_json(root / "attempt-ledger.json", ledger)
    return entry


def seal_bundle(root: Path) -> dict[str, Any]:
    protocol = _protocol(root)
    expected_retained = RETAINED_PAIR_TARGET * len(CONDITIONS)
    ledger = _read_object(root / "attempt-ledger.json", "attempt ledger")
    replacements = ledger.get("technical_replacements")
    if not isinstance(replacements, list) or len(replacements) > MAX_REPLACEMENTS:
        raise TrialRunnerError("technical replacement ledger is invalid")
    expected_launches = expected_retained + len(CONDITIONS) * len(replacements)
    inputs = _attempt_inputs(root)
    if len(inputs) != expected_launches:
        raise TrialRunnerError(f"bundle does not have exactly {expected_launches} model inputs")
    for packet in inputs:
        validate_model_input_packet(packet, protocol)
    scorer_technical_failures = ledger.get("scorer_technical_failures")
    if (
        ledger.get("pair_attempts") != RETAINED_PAIR_TARGET + len(replacements)
        or ledger.get("process_launches") != expected_launches
        or ledger.get("retained_scorer_contexts") != expected_retained
        or not isinstance(scorer_technical_failures, list)
        or expected_retained + len(scorer_technical_failures) > MAX_SCORER_CONTEXTS
        or not isinstance(ledger.get("launches"), list)
        or len(ledger["launches"]) != expected_launches
        or any(launch.get("finished_at") is None for launch in ledger["launches"])
        or not isinstance(ledger.get("scorer_runs"), list)
        or len(ledger["scorer_runs"]) != expected_retained
    ):
        raise TrialRunnerError("attempt ledger is not a complete preregistered v4 run")

    def relative_files(directory: str) -> list[str]:
        return [str(path.relative_to(root)) for path in sorted((root / directory).glob("*.json"))]

    source_observations = [
        str(path.relative_to(root)) for path in sorted((root / "source-observations").glob("*.json"))
    ]
    model_inputs = relative_files("model-inputs")
    member_trigger_responses = relative_files("member-trigger-responses")
    trigger_traces = relative_files("trigger-traces")
    helper_exchanges = relative_files("helper-exchanges")
    member_f3_decision_responses = relative_files("member-f3-decision-responses")
    technical_failure_responses = relative_files("technical-failure-responses")
    member_final_responses = relative_files("member-final-responses")
    model_outputs = relative_files("model-outputs")
    blind_packets = relative_files("blind-packets")
    scorer_technical_failure_responses = relative_files("scorer-technical-failure-responses")
    scorer_responses = relative_files("scorer-responses")
    scores = relative_files("scores")
    if (
        len(model_inputs) != expected_launches
        or len(member_trigger_responses) != len(trigger_traces)
        or not expected_retained <= len(trigger_traces) <= expected_launches
    ) or not all(
        len(items) == expected_retained
        for items in (member_final_responses, model_outputs, blind_packets, scorer_responses, scores)
    ) or len(technical_failure_responses) != len(CONDITIONS) * len(replacements):
        raise TrialRunnerError("input/raw/trigger/output/blind/score coverage is incomplete")
    if len(scorer_technical_failure_responses) != len(scorer_technical_failures):
        raise TrialRunnerError("scorer technical failure coverage is incomplete")
    files = {
        str(path.relative_to(root)): bytes_sha256(path.read_bytes())
        for path in root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "files": files,
        "protocol_file": "protocol.json",
        "source_snapshot_file": "source-snapshot.json",
        "source_observation_files": source_observations,
        "attempt_ledger_file": "attempt-ledger.json",
        "model_input_files": model_inputs,
        "member_trigger_response_files": member_trigger_responses,
        "trigger_trace_files": trigger_traces,
        "helper_exchange_files": helper_exchanges,
        "member_f3_decision_response_files": member_f3_decision_responses,
        "technical_failure_response_files": technical_failure_responses,
        "member_final_response_files": member_final_responses,
        "model_output_files": model_outputs,
        "blind_packet_files": blind_packets,
        "scorer_technical_failure_response_files": scorer_technical_failure_responses,
        "scorer_response_files": scorer_responses,
        "score_files": scores,
        "adjudication_file": "adjudication.json",
    }
    _write_new_json(root / "manifest.json", manifest)
    compile_evidence_bundle(root)
    return manifest


def compile_bundle(*, root: Path, output_root: Path) -> dict[str, str]:
    compiled = compile_evidence_bundle(root)
    if output_root.exists() and any(output_root.iterdir()):
        raise TrialRunnerError("compile output root must not exist or must be empty")
    output_root.mkdir(parents=True, exist_ok=True)
    digests: dict[str, str] = {}
    for name, content in compiled.items():
        path = output_root / name
        path.write_bytes(content)
        digests[name] = bytes_sha256(content)
    return digests


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("--artifact-root", required=True)
    init.add_argument("--bundle", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--bundle", required=True)
    prepare.add_argument("--pair-id", required=True)
    prepare.add_argument("--condition", required=True, choices=CONDITIONS)
    prepare.add_argument("--fresh-context-id-hash", required=True)
    trigger = subparsers.add_parser("record-trigger")
    trigger.add_argument("--bundle", required=True)
    trigger.add_argument("--attempt-id", required=True)
    trigger.add_argument("--trace", required=True)
    f3_decision = subparsers.add_parser("record-f3-decision")
    f3_decision.add_argument("--bundle", required=True)
    f3_decision.add_argument("--attempt-id", required=True)
    f3_decision.add_argument("--decision", required=True)
    exclude = subparsers.add_parser("exclude-pair")
    exclude.add_argument("--bundle", required=True)
    exclude.add_argument("--pair-id", required=True)
    exclude.add_argument("--exclusion-code", required=True, choices=TECHNICAL_EXCLUSION_CODES)
    exclude.add_argument("--failure", required=True, action="append")
    helper = subparsers.add_parser("helper-call")
    helper.add_argument("--bundle", required=True)
    helper.add_argument("--repository-root", required=True)
    helper.add_argument("--ldvh-executable", required=True)
    helper.add_argument("--attempt-id", required=True)
    helper.add_argument("--operation", required=True)
    helper.add_argument("--request", required=True)
    output = subparsers.add_parser("finalize-output")
    output.add_argument("--bundle", required=True)
    output.add_argument("--attempt-id", required=True)
    output.add_argument("--response", required=True)
    blind = subparsers.add_parser("build-blind")
    blind.add_argument("--bundle", required=True)
    blind.add_argument("--attempt-id", required=True)
    score = subparsers.add_parser("record-score")
    score.add_argument("--bundle", required=True)
    score.add_argument("--attempt-id", required=True)
    score.add_argument("--score", required=True)
    score.add_argument("--fresh-scorer-context-id-hash", required=True)
    scorer_failure = subparsers.add_parser("record-scorer-technical-failure")
    scorer_failure.add_argument("--bundle", required=True)
    scorer_failure.add_argument("--attempt-id", required=True)
    scorer_failure.add_argument("--response", required=True)
    scorer_failure.add_argument("--fresh-scorer-context-id-hash", required=True)
    seal = subparsers.add_parser("seal")
    seal.add_argument("--bundle", required=True)
    compile_parser = subparsers.add_parser("compile")
    compile_parser.add_argument("--bundle", required=True)
    compile_parser.add_argument("--output-root", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "init":
        initialize_bundle(artifact_root=Path(args.artifact_root), bundle_root=Path(args.bundle))
        result: object = {"initialized": str(Path(args.bundle).resolve())}
    elif args.command == "prepare":
        result = prepare_attempt(
            root=_bundle(args.bundle),
            pair_id=args.pair_id,
            condition=args.condition,
            fresh_context_id_hash=args.fresh_context_id_hash,
        )
    elif args.command == "record-trigger":
        result = record_trigger(
            root=_bundle(args.bundle),
            attempt_id=args.attempt_id,
            trace_file=Path(args.trace),
        )
    elif args.command == "record-f3-decision":
        result = record_f3_decision(
            root=_bundle(args.bundle),
            attempt_id=args.attempt_id,
            decision_file=Path(args.decision),
        )
    elif args.command == "exclude-pair":
        failures: dict[str, Path] = {}
        for raw in args.failure:
            attempt_id, separator, path = raw.partition("=")
            if not separator or not attempt_id or not path or attempt_id in failures:
                raise TrialRunnerError("--failure must be a unique ATTEMPT_ID=PATH binding")
            failures[attempt_id] = Path(path)
        result = exclude_pair(
            root=_bundle(args.bundle),
            pair_id=args.pair_id,
            exclusion_code=args.exclusion_code,
            failure_files=failures,
        )
    elif args.command == "helper-call":
        result = helper_call(
            root=_bundle(args.bundle),
            repository_root=Path(args.repository_root),
            ldvh_executable=Path(args.ldvh_executable),
            attempt_id=args.attempt_id,
            operation=args.operation,
            request_file=Path(args.request),
        )
    elif args.command == "finalize-output":
        result = finalize_output(
            root=_bundle(args.bundle),
            attempt_id=args.attempt_id,
            response_file=Path(args.response),
        )
    elif args.command == "build-blind":
        result = build_attempt_blind_packet(root=_bundle(args.bundle), attempt_id=args.attempt_id)
    elif args.command == "record-score":
        result = record_score(
            root=_bundle(args.bundle),
            attempt_id=args.attempt_id,
            score_file=Path(args.score),
            fresh_scorer_context_id_hash=args.fresh_scorer_context_id_hash,
        )
    elif args.command == "record-scorer-technical-failure":
        result = record_scorer_technical_failure(
            root=_bundle(args.bundle),
            attempt_id=args.attempt_id,
            response_file=Path(args.response),
            fresh_scorer_context_id_hash=args.fresh_scorer_context_id_hash,
        )
    elif args.command == "seal":
        result = seal_bundle(_bundle(args.bundle))
    else:
        result = compile_bundle(
            root=Path(args.bundle).resolve(strict=True),
            output_root=Path(args.output_root),
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())