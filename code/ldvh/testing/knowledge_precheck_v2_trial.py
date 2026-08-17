"""Runner-owned command surface for the knowledge-precheck v0.2 trial.

The native model process is intentionally outside this Python process.  Each
member run receives one closed input packet, and any knowledge lookup must come
back through ``helper-call`` so the real read-only Helper exchange is captured
before a bounded structured response is accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import shutil
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ldvh.testing.knowledge_precheck_v2 import (
    CONDITIONS,
    EVIDENCE_SCHEMA_VERSION,
    MAX_PROCESS_LAUNCHES,
    RETAINED_PAIR_TARGET,
    ReadOnlyKnowledgeGateway,
    build_blind_packet,
    build_model_input_packet,
    bytes_sha256,
    compile_evidence_bundle,
    subprocess_helper_dispatch,
    validate_model_input_packet,
    validate_model_output,
    validate_protocol,
    validate_score,
)


class TrialRunnerError(ValueError):
    """Raised before any partial trial evidence is accepted."""


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _read_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
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
    packets = []
    for path in sorted((root / "model-inputs").glob("*.json")):
        packets.append(_read_object(path, "model input"))
    return packets


def initialize_bundle(*, artifact_root: Path, bundle_root: Path) -> None:
    source = artifact_root.resolve(strict=True)
    if bundle_root.exists() and any(bundle_root.iterdir()):
        raise TrialRunnerError("bundle root must not exist or must be empty")
    bundle_root.mkdir(parents=True, exist_ok=True)
    for name in ("protocol.json", "source-snapshot.json"):
        shutil.copyfile(source / name, bundle_root / name)
    protocol = _protocol(bundle_root)
    snapshot = _read_object(bundle_root / "source-snapshot.json", "source snapshot")
    if (
        protocol["source_snapshot"]["content_sha256"]
        != hashlib.sha256(
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    ):
        raise TrialRunnerError("source snapshot does not match protocol")
    _write_new_json(
        bundle_root / "attempt-ledger.json",
        {
            "pair_attempts": 0,
            "technical_replacements": [],
            "process_launches": 0,
            "launches": [],
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
    same_pair = [packet for packet in packets if packet["pair_id"] == pair_id]
    order_index = [task["pair_id"] for task in protocol["tasks"]].index(pair_id)
    expected_order = protocol["condition_orders"][order_index]
    if len(same_pair) >= 2 or condition != expected_order[len(same_pair)]:
        raise TrialRunnerError("attempt violates the frozen condition order or same-arm retry rule")
    if any(packet["fresh_context_id_hash"] == fresh_context_id_hash for packet in packets):
        raise TrialRunnerError("fresh context hash must be unique")
    if len(packets) >= MAX_PROCESS_LAUNCHES:
        raise TrialRunnerError("process launch ceiling reached")

    attempt_id = f"attempt-{secrets.token_hex(12)}"
    packet = build_model_input_packet(
        protocol,
        pair_id=pair_id,
        condition=condition,
        attempt_id=attempt_id,
        fresh_context_id_hash=fresh_context_id_hash,
    )
    _write_new_json(root / "model-inputs" / f"{attempt_id}.json", packet)
    ledger = _read_object(root / "attempt-ledger.json", "attempt ledger")
    ledger["process_launches"] += 1
    if not same_pair:
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


def helper_call(
    *,
    root: Path,
    repository_root: Path,
    ldvh_executable: Path,
    attempt_id: str,
    operation: str,
    request_file: Path,
) -> dict[str, Any]:
    protocol = _protocol(root)
    input_path = root / "model-inputs" / f"{attempt_id}.json"
    packet = _read_object(input_path, "model input")
    validate_model_input_packet(packet, protocol)
    if (root / "model-outputs" / f"{attempt_id}.json").exists():
        raise TrialRunnerError("cannot call Helper after model output is finalized")
    request = _read_object(request_file.resolve(strict=True), "Helper request")
    arguments = request.get("arguments")
    if operation == "find-fact-object-candidates" and (
        not isinstance(arguments, Mapping) or arguments.get("fact_type_keys") != [packet["family"]]
    ):
        raise TrialRunnerError("F2 request family must match the member-run input")
    snapshot = _read_object(root / "source-snapshot.json", "source snapshot")
    dispatch = subprocess_helper_dispatch(
        repository_root=repository_root,
        ldvh_executable=ldvh_executable,
    )
    gateway = ReadOnlyKnowledgeGateway(
        dispatch,
        expected_object_set_fingerprint=protocol["source_snapshot"]["object_set_fingerprint"],
        expected_f3_fingerprints=snapshot["knowledge_ref_fingerprints"],
    )
    existing = sorted((root / "helper-exchanges").glob(f"{attempt_id}-*.json"))
    prior_operations = [_read_object(path, "Helper exchange")["operation"] for path in existing]
    if operation == "find-fact-object-candidates" and prior_operations:
        raise TrialRunnerError("F2 must be the first and only discovery call")
    if operation == "read-fact-objects" and prior_operations != ["find-fact-object-candidates"]:
        raise TrialRunnerError("one F3 call is allowed only after the attempt's single F2 call")
    exchange_id = f"exchange-{secrets.token_hex(12)}"
    exchange = gateway.call(
        operation,
        request,
        exchange_id=exchange_id,
        attempt_id=attempt_id,
    )
    if any(item["fact_type_key"] != packet["family"] for item in exchange["f3_objects"]):
        raise TrialRunnerError("F3 result family does not match the member-run input")
    sequence = len(existing) + 1
    _write_new_json(
        root / "helper-exchanges" / f"{attempt_id}-{sequence:02d}-{exchange_id}.json",
        exchange,
    )
    return {
        "exchange_id": exchange_id,
        "helper_response": json.loads(exchange["raw_response_utf8"]),
    }


def finalize_output(*, root: Path, attempt_id: str, response_file: Path) -> dict[str, Any]:
    protocol = _protocol(root)
    packet = _read_object(root / "model-inputs" / f"{attempt_id}.json", "model input")
    validate_model_input_packet(packet, protocol)
    output_path = root / "model-outputs" / f"{attempt_id}.json"
    if output_path.exists():
        raise TrialRunnerError("model output is already finalized")
    response = _read_object(response_file.resolve(strict=True), "structured response")
    exchange_files = sorted((root / "helper-exchanges").glob(f"{attempt_id}-*.json"))
    exchange_ids = [_read_object(path, "Helper exchange")["exchange_id"] for path in exchange_files]
    output = {
        "attempt_id": attempt_id,
        "pair_id": packet["pair_id"],
        "condition": packet["condition"],
        "model_name": None,
        "agent_runtime_name": "codex-native-subagent",
        "fresh_context_id_hash": packet["fresh_context_id_hash"],
        "structured_response": response,
        "helper_exchange_ids": exchange_ids,
        "usage": "unavailable",
        "latency": "unavailable",
    }
    validate_model_output(output, protocol)
    _write_new_json(output_path, output)
    ledger = _read_object(root / "attempt-ledger.json", "attempt ledger")
    launches = [launch for launch in ledger["launches"] if launch["attempt_id"] == attempt_id]
    if len(launches) != 1 or launches[0]["finished_at"] is not None:
        raise TrialRunnerError("process launch ledger cannot finalize this attempt")
    launches[0]["finished_at"] = _now()
    _replace_json(root / "attempt-ledger.json", ledger)
    return output


def build_attempt_blind_packet(*, root: Path, attempt_id: str) -> dict[str, Any]:
    protocol = _protocol(root)
    output = _read_object(root / "model-outputs" / f"{attempt_id}.json", "model output")
    validate_model_output(output, protocol)
    task = next(task for task in protocol["tasks"] if task["pair_id"] == output["pair_id"])
    exchanges = []
    for path in sorted((root / "helper-exchanges").glob(f"{attempt_id}-*.json")):
        exchanges.append(_read_object(path, "Helper exchange"))
    packet = build_blind_packet(output, task, exchanges)
    _write_new_json(root / "blind-packets" / f"{attempt_id}.json", packet)
    return packet


def record_score(*, root: Path, attempt_id: str, score_file: Path) -> dict[str, Any]:
    blind_path = root / "blind-packets" / f"{attempt_id}.json"
    if not blind_path.is_file():
        raise TrialRunnerError("blind packet must exist before scoring")
    score = _read_object(score_file.resolve(strict=True), "score")
    validate_score(score)
    if score["attempt_id"] != attempt_id:
        raise TrialRunnerError("score attempt id does not match")
    blind_packet = _read_object(blind_path, "blind packet")
    expected_hash = hashlib.sha256(
        json.dumps(blind_packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if score["blind_packet_sha256"] != expected_hash:
        raise TrialRunnerError("score is not bound to the blind packet")
    _write_new_json(root / "scores" / f"{attempt_id}.json", score)
    return score


def seal_bundle(root: Path) -> dict[str, Any]:
    protocol = _protocol(root)
    inputs = _attempt_inputs(root)
    if len(inputs) != RETAINED_PAIR_TARGET * len(CONDITIONS):
        raise TrialRunnerError("bundle does not have exactly 24 model inputs")
    for packet in inputs:
        validate_model_input_packet(packet, protocol)
    ledger = _read_object(root / "attempt-ledger.json", "attempt ledger")
    if (
        ledger.get("pair_attempts") != 12
        or ledger.get("technical_replacements") != []
        or ledger.get("process_launches") != 24
        or not isinstance(ledger.get("launches"), list)
        or len(ledger["launches"]) != 24
        or any(launch.get("finished_at") is None for launch in ledger["launches"])
    ):
        raise TrialRunnerError("attempt ledger is not the preregistered 12-pair/24-launch run")

    def relative_files(directory: str) -> list[str]:
        paths = sorted((root / directory).glob("*.json"))
        return [str(path.relative_to(root)) for path in paths]

    model_inputs = relative_files("model-inputs")
    helper_exchanges = relative_files("helper-exchanges")
    model_outputs = relative_files("model-outputs")
    blind_packets = relative_files("blind-packets")
    scores = relative_files("scores")
    if not all(len(items) == 24 for items in (model_inputs, model_outputs, blind_packets, scores)):
        raise TrialRunnerError("model input/output/blind/score coverage is incomplete")
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
        "attempt_ledger_file": "attempt-ledger.json",
        "model_input_files": model_inputs,
        "helper_exchange_files": helper_exchanges,
        "model_output_files": model_outputs,
        "blind_packet_files": blind_packets,
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
        )
    elif args.command == "seal":
        result = seal_bundle(_bundle(args.bundle))
    else:
        root = Path(args.bundle).resolve(strict=True)
        result = compile_bundle(root=root, output_root=Path(args.output_root))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
