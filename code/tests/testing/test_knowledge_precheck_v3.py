from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ldvh.testing.knowledge_precheck_v3 import (
    CONDITIONS,
    EVIDENCE_SCHEMA_VERSION,
    POLICY_MAX_BYTES,
    POLICY_MAX_LINES,
    KnowledgePrecheckV3Error,
    ReadOnlyKnowledgeGateway,
    build_model_input_packet,
    bytes_sha256,
    canonical_sha256,
    compile_evidence_bundle,
    condition_from_packet,
    validate_protocol,
)
from ldvh.testing.knowledge_precheck_v3_trial import (
    TrialRunnerError,
    build_attempt_blind_packet,
    exclude_pair,
    finalize_output,
    initialize_bundle,
    prepare_attempt,
    record_score,
    record_scorer_technical_failure,
    record_trigger,
    seal_bundle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = PROJECT_ROOT / "docs/metrics/knowledge-precheck-v3"


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_bytes())
    assert isinstance(value, dict)
    return value


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _refresh_manifest_digests(root: Path, *paths: Path) -> None:
    manifest = _json(root / "manifest.json")
    for path in paths:
        relative = str(path.relative_to(root))
        manifest["files"][relative] = bytes_sha256(path.read_bytes())  # type: ignore[index]
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_frozen_protocol_has_balanced_falsifiable_l1_design() -> None:
    protocol = _json(ARTIFACT_ROOT / "protocol.json")
    snapshot = _json(ARTIFACT_ROOT / "source-snapshot.json")
    assert validate_protocol(protocol) == ()
    assert protocol["source_snapshot"]["content_sha256"] == canonical_sha256(snapshot)  # type: ignore[index]
    tasks = protocol["tasks"]
    assert isinstance(tasks, list) and len(tasks) == 18
    assert sum(bool(task["gold"]["applicable_refs"]) for task in tasks) == 9
    assert sum(not bool(task["gold"]["applicable_refs"]) for task in tasks) == 9
    assert sum(task["gold"]["expected_f2_trigger"] is False for task in tasks) == 6
    for family in ("adr", "pitfall", "study"):
        members = [task for task in tasks if task["family"] == family]
        assert len(members) == 6
        assert sum(task["case_kind"] == "exact-positive" for task in members) == 2
    specific = protocol["policies"]["l1-specific"]
    assert specific["bytes"] <= POLICY_MAX_BYTES
    assert specific["lines"] <= POLICY_MAX_LINES


def test_model_packets_hide_arm_label_and_only_policy_semantics_differ() -> None:
    protocol = _json(ARTIFACT_ROOT / "protocol.json")
    packets = [
        build_model_input_packet(
            protocol,
            pair_id="A1",
            condition=condition,
            attempt_id=f"attempt-{index}",
            fresh_context_id_hash=bytes_sha256(f"ctx-{index}".encode()),
        )
        for index, condition in enumerate(CONDITIONS)
    ]
    assert all("condition" not in packet for packet in packets)
    assert all("condition" not in packet["trigger_trace_contract"]["fields"] for packet in packets)
    assert all("attempt_id" not in packet["trigger_trace_contract"]["fields"] for packet in packets)
    assert [condition_from_packet(packet, protocol) for packet in packets] == list(CONDITIONS)
    left, right = [dict(packet) for packet in packets]
    for packet in (left, right):
        packet.pop("attempt_id")
        packet.pop("fresh_context_id_hash")
        packet.pop("l1_policy")
    assert left == right


def _f2_response(object_set_fingerprint: str) -> bytes:
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
                    "object_set_fingerprint": object_set_fingerprint,
                },
                "cards": [{"match_reasons": [{"kind": "status", "field_path": "status"}]}],
            },
        },
        separators=(",", ":"),
    ).encode()


def _f2_card_response(object_set_fingerprint: str, fields: dict[str, object]) -> bytes:
    response = json.loads(_f2_response(object_set_fingerprint))
    response["result"]["cards"][0]["fields"] = fields
    return json.dumps(response, separators=(",", ":")).encode()


def _f3_response(uid: str, family: str, fingerprint: str) -> bytes:
    return json.dumps(
        {
            "operation_key": "read-fact-objects",
            "outcome": "ok",
            "changes": [],
            "result": {
                "items": [
                    {
                        "check_status": "mechanically_valid",
                        "resolved_ref": {"object_uid": uid},
                        "content_fingerprint": fingerprint,
                        "fact_object": {"object_uid": uid, "fact_type_key": family},
                    }
                ]
            },
        },
        separators=(",", ":"),
    ).encode()


def test_gateway_rejects_write_workspace_drift_and_cross_family() -> None:
    object_set = "a" * 64
    uid = "019ffb52-ebb5-724c-881f-4f0f7d97038f"
    fingerprint = "b" * 64
    calls: list[str] = []

    def dispatch(operation: str, _request: bytes) -> bytes:
        calls.append(operation)
        if operation == "find-fact-object-candidates":
            return _f2_response(object_set)
        return _f3_response(uid, "study", fingerprint)

    gateway = ReadOnlyKnowledgeGateway(
        dispatch,
        expected_object_set_fingerprint=object_set,
        expected_f3_fingerprints={uid: fingerprint},
    )
    with pytest.raises(KnowledgePrecheckV3Error, match="allowlisted"):
        gateway.call("update-fact-object", {"arguments": {}}, exchange_id="e0", attempt_id="a0")
    with pytest.raises(KnowledgePrecheckV3Error, match="workspace_root"):
        gateway.call(
            "find-fact-object-candidates",
            {
                "arguments": {
                    "governed_project_id": "ldvh",
                    "card_layer": "F2",
                    "fact_type_keys": ["adr"],
                    "statuses": ["active"],
                    "workspace_root": "/tmp",
                }
            },
            exchange_id="e1",
            attempt_id="a0",
        )
    assert calls == []

    drifted = ReadOnlyKnowledgeGateway(
        lambda _op, _request: _f2_response("c" * 64),
        expected_object_set_fingerprint=object_set,
    )
    with pytest.raises(KnowledgePrecheckV3Error, match="drifted"):
        drifted.call(
            "find-fact-object-candidates",
            {
                "arguments": {
                    "governed_project_id": "ldvh",
                    "card_layer": "F2",
                    "fact_type_keys": ["adr"],
                    "statuses": ["active"],
                }
            },
            exchange_id="e2",
            attempt_id="a0",
        )

    exchange = gateway.call(
        "read-fact-objects",
        {"arguments": {"fact_refs": [{"object_uid": uid}]}},
        exchange_id="e3",
        attempt_id="a0",
    )
    assert exchange["schema_version"] == EVIDENCE_SCHEMA_VERSION
    assert exchange["f3_objects"][0]["fact_type_key"] == "study"


def test_gateway_ignores_unrelated_global_drift_but_rejects_knowledge_card_drift() -> None:
    frozen_card = {"object_uid": "019ffb52-ebb5-724c-881f-4f0f7d97038f", "status": "active"}
    cards = {"adr": [frozen_card], "pitfall": [], "study": []}
    request = {
        "arguments": {
            "governed_project_id": "ldvh",
            "card_layer": "F2",
            "fact_type_keys": ["adr"],
            "statuses": ["active"],
        }
    }
    gateway = ReadOnlyKnowledgeGateway(
        lambda _op, _request: _f2_card_response("c" * 64, frozen_card),
        expected_f2_cards=cards,
    )
    exchange = gateway.call("find-fact-object-candidates", request, exchange_id="knowledge-ok", attempt_id="a0")
    assert exchange["coverage"]["object_set_fingerprint"] == "c" * 64

    drifted = ReadOnlyKnowledgeGateway(
        lambda _op, _request: _f2_card_response("c" * 64, {**frozen_card, "status": "retired"}),
        expected_f2_cards=cards,
    )
    with pytest.raises(KnowledgePrecheckV3Error, match="knowledge cards drifted"):
        drifted.call("find-fact-object-candidates", request, exchange_id="knowledge-drift", attempt_id="a1")


@pytest.fixture(scope="module")
def sealed_bundle(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("knowledge-precheck-v3") / "bundle"
    initialize_bundle(artifact_root=ARTIFACT_ROOT, bundle_root=root)
    protocol = _json(ARTIFACT_ROOT / "protocol.json")
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}  # type: ignore[index]
    orders = protocol["condition_orders"]
    for pair_index, pair_id in enumerate(tasks):
        for arm_index, condition in enumerate(orders[pair_index]):
            packet = prepare_attempt(
                root=root,
                pair_id=pair_id,
                condition=condition,
                fresh_context_id_hash=bytes_sha256(f"member-{pair_id}-{arm_index}".encode()),
            )
            attempt_id = str(packet["attempt_id"])
            trace_path = root.parent / f"{attempt_id}-trace.json"
            _write(
                trace_path,
                {
                    "triggered": False,
                    "trigger_family": None,
                    "positive_condition_codes": [],
                    "veto_condition_codes": [],
                },
            )
            record_trigger(root=root, attempt_id=attempt_id, trace_file=trace_path)
            response_path = root.parent / f"{attempt_id}-response.json"
            task = tasks[pair_id]
            _write(
                response_path,
                {
                    "decision": task["gold"]["admissible_answer"],
                    "selected_refs": [],
                    "first_legal_action": task["gold"]["first_legal_action"],
                    "rationale_codes": ["frozen-first-action"],
                    "refusal_reason_codes": [],
                },
            )
            finalize_output(root=root, attempt_id=attempt_id, response_file=response_path)
            build_attempt_blind_packet(root=root, attempt_id=attempt_id)
            score_path = root.parent / f"{attempt_id}-score.json"
            non_use = not bool(task["gold"]["applicable_refs"])
            _write(
                score_path,
                {
                    "condition_blind_attested": True,
                    "knowledge_adjusted_first_legal_action_correct": True,
                    "action_changed": False,
                    "strong_reuse": False,
                    "correct_non_use": non_use,
                    "scoring_notes": "Deterministic fixture score.",
                },
            )
            record_score(
                root=root,
                attempt_id=attempt_id,
                score_file=score_path,
                fresh_scorer_context_id_hash=bytes_sha256(f"scorer-{pair_id}-{arm_index}".encode()),
            )
    seal_bundle(root)
    return root


def test_source_complete_bundle_replays_byte_identically(sealed_bundle: Path) -> None:
    first = compile_evidence_bundle(sealed_bundle)
    second = compile_evidence_bundle(sealed_bundle)
    assert first == second
    results = json.loads(first["results.json"])
    records = json.loads(first["records.json"])
    assert results["retained_pairs"] == 18
    assert results["member_runs"] == 36
    assert results["adoption_decision"] == "do-not-support-adopting-l1-specific"
    assert len(records) == 36
    assert all("trigger_decision_correct" in record for record in records)
    assert all("false_f3_expansion" in record for record in records)
    blind_packets = [_json(path) for path in (sealed_bundle / "blind-packets").glob("*.json")]
    assert all("positive_condition_codes" not in packet["trigger_decision"] for packet in blind_packets)
    assert all("veto_condition_codes" not in packet["trigger_decision"] for packet in blind_packets)


def test_invalid_scorer_retry_is_retained_and_counted(sealed_bundle: Path, tmp_path: Path) -> None:
    root = tmp_path / "scorer-retry"
    shutil.copytree(sealed_bundle, root)
    (root / "manifest.json").unlink()
    attempt_id = _json(next((root / "model-outputs").glob("*.json")))["attempt_id"]
    valid = tmp_path / "valid-scorer.json"
    _write(
        valid,
        {
            "condition_blind_attested": True,
            "knowledge_adjusted_first_legal_action_correct": True,
            "action_changed": False,
            "strong_reuse": False,
            "correct_non_use": False,
            "scoring_notes": "Valid responses cannot be retained as technical failures.",
        },
    )
    with pytest.raises(TrialRunnerError, match="must be invalid"):
        record_scorer_technical_failure(
            root=root,
            attempt_id=str(attempt_id),
            response_file=valid,
            fresh_scorer_context_id_hash=bytes_sha256(b"valid-scorer-context"),
        )
    invalid = tmp_path / "invalid-scorer.json"
    _write(
        invalid,
        {
            "condition_blind_attested": True,
            "knowledge_adjusted_first_legal_action_correct": False,
            "action_changed": True,
            "strong_reuse": True,
            "correct_non_use": False,
            "scoring_notes": "Invalid because strong reuse contradicts the first-action score.",
        },
    )
    record_scorer_technical_failure(
        root=root,
        attempt_id=str(attempt_id),
        response_file=invalid,
        fresh_scorer_context_id_hash=bytes_sha256(b"invalid-scorer-context"),
    )
    seal_bundle(root)
    results = json.loads(compile_evidence_bundle(root)["results.json"])
    assert results["scorer_contexts"] == 37
    assert results["retained_scorer_runs"] == 36
    assert results["scorer_technical_failures"] == 1


def test_source_complete_bundle_accepts_one_whole_pair_replacement(tmp_path: Path) -> None:
    root = tmp_path / "replacement-bundle"
    initialize_bundle(artifact_root=ARTIFACT_ROOT, bundle_root=root)
    protocol = _json(root / "protocol.json")
    tasks = {task["pair_id"]: task for task in protocol["tasks"]}  # type: ignore[index]
    orders = protocol["condition_orders"]

    failures: dict[str, Path] = {}
    for arm_index, condition in enumerate(orders[0]):
        packet = prepare_attempt(
            root=root,
            pair_id="A1",
            condition=condition,
            fresh_context_id_hash=bytes_sha256(f"failed-A1-{arm_index}".encode()),
        )
        attempt_id = str(packet["attempt_id"])
        failure_path = tmp_path / f"{attempt_id}-failure.json"
        _write(
            failure_path,
            {
                "triggered": False,
                "trigger_family": "adr",
                "positive_condition_codes": [],
                "veto_condition_codes": ["invalid-trigger-family"],
            },
        )
        failures[attempt_id] = failure_path
    exclude_pair(
        root=root,
        pair_id="A1",
        exclusion_code="model_technical_failure",
        failure_files=failures,
    )

    for pair_index, pair_id in enumerate(tasks):
        for arm_index, condition in enumerate(orders[pair_index]):
            packet = prepare_attempt(
                root=root,
                pair_id=pair_id,
                condition=condition,
                fresh_context_id_hash=bytes_sha256(f"retained-{pair_id}-{arm_index}".encode()),
            )
            attempt_id = str(packet["attempt_id"])
            trace_path = tmp_path / f"{attempt_id}-trace.json"
            _write(
                trace_path,
                {
                    "triggered": False,
                    "trigger_family": None,
                    "positive_condition_codes": [],
                    "veto_condition_codes": [],
                },
            )
            record_trigger(root=root, attempt_id=attempt_id, trace_file=trace_path)
            task = tasks[pair_id]
            response_path = tmp_path / f"{attempt_id}-response.json"
            _write(
                response_path,
                {
                    "decision": task["gold"]["admissible_answer"],
                    "selected_refs": [],
                    "first_legal_action": task["gold"]["first_legal_action"],
                    "rationale_codes": ["frozen-first-action"],
                    "refusal_reason_codes": [],
                },
            )
            finalize_output(root=root, attempt_id=attempt_id, response_file=response_path)
            build_attempt_blind_packet(root=root, attempt_id=attempt_id)
            score_path = tmp_path / f"{attempt_id}-score.json"
            _write(
                score_path,
                {
                    "condition_blind_attested": True,
                    "knowledge_adjusted_first_legal_action_correct": True,
                    "action_changed": False,
                    "strong_reuse": False,
                    "correct_non_use": not bool(task["gold"]["applicable_refs"]),
                    "scoring_notes": "Deterministic replacement fixture score.",
                },
            )
            record_score(
                root=root,
                attempt_id=attempt_id,
                score_file=score_path,
                fresh_scorer_context_id_hash=bytes_sha256(f"replacement-scorer-{pair_id}-{arm_index}".encode()),
            )
    seal_bundle(root)
    compiled = compile_evidence_bundle(root)
    results = json.loads(compiled["results.json"])
    assert results["member_runs"] == 36
    assert results["member_launches"] == 38
    assert results["technical_replacements"] == 1
    assert results["scorer_contexts"] == 36


def test_bundle_rejects_hash_tamper_extra_file_and_posthoc_override(sealed_bundle: Path, tmp_path: Path) -> None:
    for mutation in ("hash", "extra", "override"):
        clone = tmp_path / mutation
        shutil.copytree(sealed_bundle, clone)
        if mutation == "hash":
            target = next((clone / "trigger-traces").glob("*.json"))
            target.write_bytes(target.read_bytes() + b" ")
            match = "bundle hash mismatch"
        elif mutation == "extra":
            (clone / "unbound.json").write_text("{}", encoding="utf-8")
            match = "closure mismatch"
        else:
            adjudication = clone / "adjudication.json"
            adjudication.write_text('{"overrides":[{"field":"strong_reuse"}]}', encoding="utf-8")
            manifest = _json(clone / "manifest.json")
            manifest["files"]["adjudication.json"] = bytes_sha256(adjudication.read_bytes())  # type: ignore[index]
            (clone / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            match = "post-hoc"
        with pytest.raises(KnowledgePrecheckV3Error, match=match):
            compile_evidence_bundle(clone)


def test_trigger_metrics_cannot_be_injected_through_score(sealed_bundle: Path, tmp_path: Path) -> None:
    clone = tmp_path / "score-injection"
    shutil.copytree(sealed_bundle, clone)
    score_path = next((clone / "scores").glob("*.json"))
    score = _json(score_path)
    score["false_f3_expansion"] = 0
    score_path.write_text(json.dumps(score, sort_keys=True), encoding="utf-8")
    manifest = _json(clone / "manifest.json")
    relative = str(score_path.relative_to(clone))
    manifest["files"][relative] = bytes_sha256(score_path.read_bytes())  # type: ignore[index]
    (clone / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(KnowledgePrecheckV3Error, match="score fields"):
        compile_evidence_bundle(clone)


def test_controller_trace_cannot_diverge_from_raw_member_response(sealed_bundle: Path, tmp_path: Path) -> None:
    clone = tmp_path / "raw-trigger-binding"
    shutil.copytree(sealed_bundle, clone)
    raw_path = next((clone / "member-trigger-responses").glob("*.json"))
    raw = _json(raw_path)
    trace = _json(clone / "trigger-traces" / f"{raw['attempt_id']}.json")
    response = json.loads(raw["raw_response_utf8"])
    response["triggered"] = True
    response["trigger_family"] = trace["family"]
    response["positive_condition_codes"] = ["forged-positive"]
    raw_text = json.dumps(response, ensure_ascii=False)
    raw["raw_response_utf8"] = raw_text
    raw["response_sha256"] = bytes_sha256(raw_text.encode())
    _write(raw_path, raw)
    _refresh_manifest_digests(clone, raw_path)
    with pytest.raises(KnowledgePrecheckV3Error, match="differs from the raw member"):
        compile_evidence_bundle(clone)


@pytest.mark.parametrize("mutation", ["identity", "strong-reuse", "correct-non-use"])
def test_scores_cannot_contradict_identity_or_mechanical_evidence(
    sealed_bundle: Path,
    tmp_path: Path,
    mutation: str,
) -> None:
    clone = tmp_path / mutation
    shutil.copytree(sealed_bundle, clone)
    outputs = [_json(path) for path in (clone / "model-outputs").glob("*.json")]
    pair_id = "A1" if mutation != "correct-non-use" else "A4"
    target = next(output for output in outputs if output["pair_id"] == pair_id)
    score_path = clone / "scores" / f"{target['attempt_id']}.json"
    score = _json(score_path)
    if mutation == "identity":
        score["scorer_runtime_name"] = "synthetic-scorer"
        match = "identity"
    elif mutation == "strong-reuse":
        score["action_changed"] = True
        score["strong_reuse"] = True
        match = "strong reuse"
    else:
        score["knowledge_adjusted_first_legal_action_correct"] = False
        score["correct_non_use"] = True
        match = "correct non-use"
    _write(score_path, score)
    changed_paths = [score_path]
    if mutation != "identity":
        raw_path = clone / "scorer-responses" / f"{target['attempt_id']}.json"
        raw = _json(raw_path)
        response = {
            field: score[field]
            for field in (
                "condition_blind_attested",
                "knowledge_adjusted_first_legal_action_correct",
                "action_changed",
                "strong_reuse",
                "correct_non_use",
                "scoring_notes",
            )
        }
        raw_text = json.dumps(response, ensure_ascii=False)
        raw["raw_response_utf8"] = raw_text
        raw["response_sha256"] = bytes_sha256(raw_text.encode())
        _write(raw_path, raw)
        changed_paths.append(raw_path)
    _refresh_manifest_digests(clone, *changed_paths)
    with pytest.raises(KnowledgePrecheckV3Error, match=match):
        compile_evidence_bundle(clone)


def test_task_source_refs_and_raw_source_observations_are_semantically_bound(
    sealed_bundle: Path,
    tmp_path: Path,
) -> None:
    source_ref_clone = tmp_path / "source-ref"
    shutil.copytree(sealed_bundle, source_ref_clone)
    protocol_path = source_ref_clone / "protocol.json"
    protocol = _json(protocol_path)
    protocol["tasks"][0]["source_refs"][0]["content_fingerprint"] = "a" * 64  # type: ignore[index]
    _write(protocol_path, protocol)
    _refresh_manifest_digests(source_ref_clone, protocol_path)
    with pytest.raises(KnowledgePrecheckV3Error, match="source refs"):
        compile_evidence_bundle(source_ref_clone)

    observation_clone = tmp_path / "source-observation"
    shutil.copytree(sealed_bundle, observation_clone)
    observation_path = observation_clone / "source-observations" / "adr-f2.request.json"
    observation = _json(observation_path)
    observation["arguments"]["fact_type_keys"] = ["pitfall"]  # type: ignore[index]
    _write(observation_path, observation)
    snapshot_path = observation_clone / "source-snapshot.json"
    snapshot = _json(snapshot_path)
    snapshot["observation_file_sha256"]["adr-f2.request.json"] = bytes_sha256(  # type: ignore[index]
        observation_path.read_bytes()
    )
    _write(snapshot_path, snapshot)
    protocol_path = observation_clone / "protocol.json"
    protocol = _json(protocol_path)
    protocol["source_snapshot"]["content_sha256"] = canonical_sha256(snapshot)  # type: ignore[index]
    _write(protocol_path, protocol)
    _refresh_manifest_digests(observation_clone, observation_path, snapshot_path, protocol_path)
    with pytest.raises(KnowledgePrecheckV3Error, match="source F2 request"):
        compile_evidence_bundle(observation_clone)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("member-ceiling", "member launch ceiling"),
        ("member-timeout", "member run exceeded"),
        ("nontechnical-replacement", "nontechnical exclusion"),
        ("scorer-sequence", "scorer ledger sequence"),
    ],
)
def test_attempt_ledger_limits_fail_closed(
    sealed_bundle: Path,
    tmp_path: Path,
    mutation: str,
    match: str,
) -> None:
    clone = tmp_path / mutation
    shutil.copytree(sealed_bundle, clone)
    ledger_path = clone / "attempt-ledger.json"
    ledger = _json(ledger_path)
    if mutation == "member-ceiling":
        ledger["process_launches"] = 43
    elif mutation == "member-timeout":
        started = datetime.fromisoformat(ledger["launches"][0]["started_at"].replace("Z", "+00:00"))
        ledger["launches"][0]["finished_at"] = (started + timedelta(seconds=601)).astimezone(UTC).isoformat()
    elif mutation == "nontechnical-replacement":
        ledger["pair_attempts"] = 19
        ledger["technical_replacements"] = [
            {
                "pair_id": "A1",
                "exclusion_code": "semantic-failure",
                "excluded_attempt_ids": ["attempt-a", "attempt-b"],
            }
        ]
    else:
        ledger["scorer_runs"][0]["sequence"] = 2
    _write(ledger_path, ledger)
    _refresh_manifest_digests(clone, ledger_path)
    with pytest.raises(KnowledgePrecheckV3Error, match=match):
        compile_evidence_bundle(clone)


def test_blind_packet_leak_and_duplicate_scorer_context_fail_closed(sealed_bundle: Path, tmp_path: Path) -> None:
    leak_clone = tmp_path / "blind-leak"
    shutil.copytree(sealed_bundle, leak_clone)
    blind_path = next((leak_clone / "blind-packets").glob("*.json"))
    blind = _json(blind_path)
    blind["condition"] = "l1-specific"
    _write(blind_path, blind)
    _refresh_manifest_digests(leak_clone, blind_path)
    with pytest.raises(KnowledgePrecheckV3Error, match="condition-blind"):
        compile_evidence_bundle(leak_clone)

    scorer_clone = tmp_path / "duplicate-scorer"
    shutil.copytree(sealed_bundle, scorer_clone)
    score_paths = sorted((scorer_clone / "scores").glob("*.json"))[:2]
    left, right = [_json(path) for path in score_paths]
    right["fresh_scorer_context_id_hash"] = left["fresh_scorer_context_id_hash"]
    _write(score_paths[1], right)
    _refresh_manifest_digests(scorer_clone, score_paths[1])
    with pytest.raises(KnowledgePrecheckV3Error, match="fresh scorer contexts"):
        compile_evidence_bundle(scorer_clone)
