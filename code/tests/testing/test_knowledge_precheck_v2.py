from __future__ import annotations

import json
from pathlib import Path

import pytest

from ldvh.testing.knowledge_precheck_v2 import (
    EVIDENCE_SCHEMA_VERSION,
    KnowledgePrecheckV2Error,
    ReadOnlyKnowledgeGateway,
    build_blind_packet,
    build_model_input_packet,
    bytes_sha256,
    canonical_sha256,
    compile_evidence_bundle,
    logical_line_count,
    render_l0_packet,
    subprocess_helper_dispatch,
    validate_protocol,
)

ROOT = Path(__file__).parents[3]
ARTIFACT_ROOT = ROOT / "docs/metrics/knowledge-precheck-v2"
PROTOCOL_PATH = ARTIFACT_ROOT / "protocol.json"
SNAPSHOT_PATH = ARTIFACT_ROOT / "source-snapshot.json"


def _protocol() -> dict[str, object]:
    return json.loads(PROTOCOL_PATH.read_bytes())


def _snapshot() -> dict[str, object]:
    return json.loads(SNAPSHOT_PATH.read_bytes())


def _f2_response(fingerprint: str) -> bytes:
    return json.dumps(
        {
            "operation_key": "find-fact-object-candidates",
            "outcome": "ok",
            "changes": [],
            "result": {
                "coverage": {
                    "status": "complete",
                    "total_matching": 1,
                    "returned": 1,
                    "object_set_fingerprint": fingerprint,
                },
                "cards": [
                    {
                        "match_reasons": [{"kind": "text", "field_path": "title"}],
                    }
                ],
            },
        },
        separators=(",", ":"),
    ).encode()


def _f3_response(uid: str, fingerprint: str) -> bytes:
    return json.dumps(
        {
            "operation_key": "read-fact-objects",
            "outcome": "ok",
            "changes": [],
            "result": {
                "items": [
                    {
                        "check_status": "mechanically_valid",
                        "content_fingerprint": fingerprint,
                        "resolved_ref": {"object_uid": uid},
                        "fact_object": {"object_uid": uid, "fact_type_key": "adr"},
                    }
                ]
            },
        },
        separators=(",", ":"),
    ).encode()


def test_frozen_protocol_and_l0_are_current_closed_and_within_cap() -> None:
    protocol = _protocol()
    snapshot = _snapshot()
    assert validate_protocol(protocol) == ()
    assert protocol["source_snapshot"]["content_sha256"] == canonical_sha256(snapshot)
    assert protocol["l0_packet"]["content"] == render_l0_packet(snapshot)
    assert protocol["l0_packet"]["bytes"] == len(protocol["l0_packet"]["content"].encode())
    assert protocol["l0_packet"]["lines"] == logical_line_count(protocol["l0_packet"]["content"])
    assert protocol["l0_packet"]["bytes"] <= 24 * 1024
    assert protocol["l0_packet"]["lines"] <= 200
    assert [task["confidence"] for task in protocol["tasks"]].count("medium") == 5


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        (lambda value: value["ceilings"].update(maximum_pair_attempts=16), "ceilings"),
        (lambda value: value["tasks"].pop(), "task-count"),
        (lambda value: value["l0_packet"].update(bytes=1), "l0-measurement"),
        (
            lambda value: value["productization_thresholds"].update(main_metric_net_gain_minimum=2),
            "productization-thresholds",
        ),
    ],
)
def test_protocol_rejects_preregistered_drift(mutation: object, problem: str) -> None:
    protocol = _protocol()
    mutation(protocol)
    assert problem in validate_protocol(protocol)


def test_gateway_records_raw_f2_and_f3_bytes_and_hashes() -> None:
    object_set = "a" * 64
    uid = "019ffb52-ebb5-724c-881f-4f0f7d97038f"
    content = "b" * 64

    def dispatch(operation: str, _: bytes) -> bytes:
        return _f2_response(object_set) if operation.startswith("find-") else _f3_response(uid, content)

    gateway = ReadOnlyKnowledgeGateway(
        dispatch,
        expected_object_set_fingerprint=object_set,
        expected_f3_fingerprints={uid: content},
    )
    f2 = gateway.call(
        "find-fact-object-candidates",
        {
            "arguments": {
                "governed_project_id": "ldvh",
                "card_layer": "F2",
                "fact_type_keys": ["adr"],
                "statuses": ["active"],
            }
        },
        exchange_id="exchange-1",
        attempt_id="attempt-1",
    )
    f3 = gateway.call(
        "read-fact-objects",
        {"arguments": {"fact_refs": [{"object_uid": uid}]}},
        exchange_id="exchange-2",
        attempt_id="attempt-1",
    )
    assert f2["coverage"]["object_set_fingerprint"] == object_set
    assert f2["match_reasons"] == [{"kind": "text", "field_path": "title"}]
    assert f3["f3_objects"] == [{"object_uid": uid, "fact_type_key": "adr", "content_fingerprint": content}]
    for exchange in gateway.exchanges:
        assert exchange["state_changing_calls"] == 0
        assert bytes_sha256(exchange["raw_request_utf8"].encode()) == exchange["request_sha256"]
        assert bytes_sha256(exchange["raw_response_utf8"].encode()) == exchange["response_sha256"]


@pytest.mark.parametrize(
    ("operation", "payload", "message"),
    [
        ("update-workcase", {"arguments": {}}, "not allowlisted"),
        (
            "find-fact-object-candidates",
            {
                "arguments": {
                    "governed_project_id": "ldvh",
                    "card_layer": "F1",
                    "fact_type_keys": ["adr"],
                }
            },
            "must request F2",
        ),
        (
            "find-fact-object-candidates",
            {
                "arguments": {
                    "governed_project_id": "ldvh",
                    "card_layer": "F2",
                    "fact_type_keys": ["adr"],
                    "workspace_root": "/tmp",
                }
            },
            "workspace_root",
        ),
    ],
)
def test_gateway_rejects_write_unknown_f1_and_workspace_root(
    operation: str, payload: dict[str, object], message: str
) -> None:
    gateway = ReadOnlyKnowledgeGateway(lambda *_: _f2_response("a" * 64), expected_object_set_fingerprint="a" * 64)
    with pytest.raises(KnowledgePrecheckV2Error, match=message):
        gateway.call(operation, payload, exchange_id="exchange", attempt_id="attempt")
    assert gateway.exchanges == ()


def test_gateway_rejects_object_set_and_f3_fingerprint_drift() -> None:
    f2_gateway = ReadOnlyKnowledgeGateway(lambda *_: _f2_response("b" * 64), expected_object_set_fingerprint="a" * 64)
    with pytest.raises(KnowledgePrecheckV2Error, match="object set drifted"):
        f2_gateway.call(
            "find-fact-object-candidates",
            {
                "arguments": {
                    "governed_project_id": "ldvh",
                    "card_layer": "F2",
                    "fact_type_keys": ["study"],
                    "statuses": ["active"],
                }
            },
            exchange_id="exchange-1",
            attempt_id="attempt-1",
        )
    uid = "019ffb52-ebb5-724c-881f-4f0f7d97038f"
    f3_gateway = ReadOnlyKnowledgeGateway(
        lambda *_: _f3_response(uid, "b" * 64),
        expected_object_set_fingerprint="a" * 64,
        expected_f3_fingerprints={uid: "c" * 64},
    )
    with pytest.raises(KnowledgePrecheckV2Error, match="F3 source drifted"):
        f3_gateway.call(
            "read-fact-objects",
            {"arguments": {"fact_refs": [{"object_uid": uid}]}},
            exchange_id="exchange-2",
            attempt_id="attempt-1",
        )


def test_real_cli_gateway_fixture_is_read_only_and_source_bound() -> None:
    protocol = _protocol()
    dispatch = subprocess_helper_dispatch(
        repository_root=ROOT,
        ldvh_executable=ROOT / "ldvh",
    )
    gateway = ReadOnlyKnowledgeGateway(
        dispatch,
        expected_object_set_fingerprint=protocol["source_snapshot"]["object_set_fingerprint"],
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        {
            "arguments": {
                "governed_project_id": "ldvh",
                "card_layer": "F2",
                "fact_type_keys": ["adr"],
                "statuses": ["active"],
            }
        },
        exchange_id="real-read-only-fixture",
        attempt_id="real-fixture",
    )
    assert exchange["state_changing_calls"] == 0
    assert exchange["coverage"]["status"] == "complete"
    assert exchange["match_reasons"]


def _attempt_id(pair_id: str, condition: str) -> str:
    return f"attempt-{canonical_sha256([pair_id, condition])[:20]}"


def _output(pair_id: str, condition: str) -> dict[str, object]:
    attempt = _attempt_id(pair_id, condition)
    return {
        "attempt_id": attempt,
        "pair_id": pair_id,
        "condition": condition,
        "model_name": None,
        "agent_runtime_name": "codex-native-subagent",
        "fresh_context_id_hash": canonical_sha256([pair_id, condition, "fresh"]),
        "structured_response": {
            "decision": "non-use",
            "selected_refs": [],
            "first_legal_action": "bounded-action",
            "rationale_codes": ["bounded"],
            "l1_triggered": False,
            "l1_trigger_family": None,
            "l1_trigger_reason_codes": [],
            "refusal_reason_codes": [],
        },
        "helper_exchange_ids": [],
        "usage": "unavailable",
        "latency": "unavailable",
    }


def _score(pair_id: str, condition: str, blind_packet: dict[str, object]) -> dict[str, object]:
    treatment = condition == "l0-plus-l1"
    improved = pair_id in {"A1", "P1", "S1"}
    strong = pair_id in {"A1", "P1"}
    return {
        "attempt_id": _attempt_id(pair_id, condition),
        "blind_packet_sha256": canonical_sha256(blind_packet),
        "scorer_model_name": None,
        "scorer_runtime_name": "codex-native-subagent",
        "fresh_scorer_context_id_hash": canonical_sha256([pair_id, condition, "scorer"]),
        "condition_blind_attested": True,
        "selection_correct": 1,
        "knowledge_adjusted_first_legal_action_correct": int(treatment and improved),
        "action_changed": int(treatment and improved),
        "strong_reuse": int(treatment and strong),
        "correct_non_use": int(pair_id in {"A2", "P2", "S2"}),
        "false_f3_expansion": 0,
        "scoring_notes": ["deterministic fixture"],
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _bundle(tmp_path: Path) -> Path:
    root = tmp_path / "bundle"
    root.mkdir(parents=True)
    protocol = _protocol()
    snapshot = _snapshot()
    _write_json(root / "protocol.json", protocol)
    _write_json(root / "source-snapshot.json", snapshot)
    output_files: list[str] = []
    input_files: list[str] = []
    blind_files: list[str] = []
    score_files: list[str] = []
    launches: list[dict[str, object]] = []
    for task_index, task in enumerate(protocol["tasks"]):
        pair_id = task["pair_id"]
        for condition in protocol["condition_orders"][task_index]:
            output = _output(pair_id, condition)
            input_path = f"model-inputs/{output['attempt_id']}.json"
            output_path = f"model-outputs/{output['attempt_id']}.json"
            blind_path = f"blind-packets/{output['attempt_id']}.json"
            score_path = f"scores/{output['attempt_id']}.json"
            _write_json(
                root / input_path,
                build_model_input_packet(
                    protocol,
                    pair_id=pair_id,
                    condition=condition,
                    attempt_id=output["attempt_id"],
                    fresh_context_id_hash=output["fresh_context_id_hash"],
                ),
            )
            _write_json(root / output_path, output)
            blind_packet = build_blind_packet(output, task, [])
            _write_json(root / blind_path, blind_packet)
            _write_json(root / score_path, _score(pair_id, condition, blind_packet))
            launches.append(
                {
                    "sequence": len(launches) + 1,
                    "attempt_id": output["attempt_id"],
                    "pair_id": pair_id,
                    "condition": condition,
                    "started_at": "2026-08-16T00:00:00Z",
                    "finished_at": "2026-08-16T00:00:01Z",
                }
            )
            input_files.append(input_path)
            output_files.append(output_path)
            blind_files.append(blind_path)
            score_files.append(score_path)
    _write_json(
        root / "attempt-ledger.json",
        {
            "pair_attempts": 12,
            "technical_replacements": [],
            "process_launches": 24,
            "launches": launches,
        },
    )
    _write_json(root / "adjudication.json", {"overrides": []})
    files = {str(path.relative_to(root)): bytes_sha256(path.read_bytes()) for path in root.rglob("*") if path.is_file()}
    manifest = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "files": files,
        "protocol_file": "protocol.json",
        "source_snapshot_file": "source-snapshot.json",
        "attempt_ledger_file": "attempt-ledger.json",
        "model_input_files": input_files,
        "helper_exchange_files": [],
        "model_output_files": output_files,
        "blind_packet_files": blind_files,
        "score_files": score_files,
        "adjudication_file": "adjudication.json",
    }
    _write_json(root / "manifest.json", manifest)
    return root


def test_compiler_rebuilds_all_outputs_byte_identically_from_closed_bundle(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    first = compile_evidence_bundle(root)
    second = compile_evidence_bundle(root)
    assert first == second
    results = json.loads(first["results.json"])
    assert results["productization_decision"] == "support-productizing-l0"
    assert results["threshold_observations"]["main_metric_net_gain"] == 3
    assert results["threshold_observations"]["strong_reuse_net_gain"] == 2
    assert first["report.md"].startswith(b"# Knowledge precheck v0.2")


def test_compiler_rejects_missing_extra_hash_drift_and_nontechnical_replacement(
    tmp_path: Path,
) -> None:
    missing = _bundle(tmp_path / "missing")
    next((missing / "scores").iterdir()).unlink()
    with pytest.raises(KnowledgePrecheckV2Error, match="file closure"):
        compile_evidence_bundle(missing)

    extra = _bundle(tmp_path / "extra")
    (extra / "extra.json").write_text("{}")
    with pytest.raises(KnowledgePrecheckV2Error, match="file closure"):
        compile_evidence_bundle(extra)

    drift = _bundle(tmp_path / "drift")
    protocol = json.loads((drift / "protocol.json").read_bytes())
    protocol["frozen_at"] = "drift"
    _write_json(drift / "protocol.json", protocol)
    with pytest.raises(KnowledgePrecheckV2Error, match="hash mismatch"):
        compile_evidence_bundle(drift)

    exclusion = _bundle(tmp_path / "exclusion")
    exclusion_ledger = json.loads((exclusion / "attempt-ledger.json").read_bytes())
    exclusion_ledger.update(
        {
            "pair_attempts": 13,
            "technical_replacements": [{"pair_id": "A1", "exclusion_code": "wrong-answer"}],
            "process_launches": 24,
        }
    )
    _write_json(
        exclusion / "attempt-ledger.json",
        exclusion_ledger,
    )
    manifest = json.loads((exclusion / "manifest.json").read_bytes())
    manifest["files"]["attempt-ledger.json"] = bytes_sha256((exclusion / "attempt-ledger.json").read_bytes())
    _write_json(exclusion / "manifest.json", manifest)
    with pytest.raises(KnowledgePrecheckV2Error, match="nontechnical"):
        compile_evidence_bundle(exclusion)


def test_compiler_replays_raw_helper_exchange_instead_of_trusting_summary(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    protocol = _protocol()
    output_path = next((root / "model-outputs").iterdir())
    output = json.loads(output_path.read_bytes())
    attempt_id = output["attempt_id"]
    gateway = ReadOnlyKnowledgeGateway(
        lambda *_: _f2_response(protocol["source_snapshot"]["object_set_fingerprint"]),
        expected_object_set_fingerprint=protocol["source_snapshot"]["object_set_fingerprint"],
    )
    exchange = gateway.call(
        "find-fact-object-candidates",
        {
            "arguments": {
                "governed_project_id": "ldvh",
                "card_layer": "F2",
                "fact_type_keys": [{"A": "adr", "P": "pitfall", "S": "study"}[output["pair_id"][0]]],
                "statuses": ["active"],
            }
        },
        exchange_id="exchange-forged-summary",
        attempt_id=attempt_id,
    )
    exchange["match_reasons"] = []
    exchange_path = root / "helper-exchanges" / "forged.json"
    _write_json(exchange_path, exchange)
    output["helper_exchange_ids"] = [exchange["exchange_id"]]
    _write_json(output_path, output)
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["helper_exchange_files"] = [str(exchange_path.relative_to(root))]
    manifest["files"][str(exchange_path.relative_to(root))] = bytes_sha256(exchange_path.read_bytes())
    manifest["files"][str(output_path.relative_to(root))] = bytes_sha256(output_path.read_bytes())
    _write_json(root / "manifest.json", manifest)
    with pytest.raises(KnowledgePrecheckV2Error, match="derived fields"):
        compile_evidence_bundle(root)


def test_blind_packet_has_no_condition_or_counterpart() -> None:
    protocol = _protocol()
    task = protocol["tasks"][0]
    output = _output(task["pair_id"], "l0-plus-l1")
    packet = build_blind_packet(output, task, [])
    encoded = json.dumps(packet, ensure_ascii=False)
    assert "condition" not in encoded
    assert "l0-plus-l1" not in encoded
    assert set(packet) == {
        "attempt_id",
        "response",
        "knowledge_trace",
        "gold",
        "rubric",
    }
