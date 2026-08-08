from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from ldvh.testing.trial_measurement import (
    TRIAL_SCHEMA_VERSION,
    ContractClaim,
    FrozenTrialTask,
    HelperResponseEvent,
    RunnerOwnedTrialAdapter,
    SafeTrialTempRoot,
    TrialMeasurementCollector,
    TrialMeasurementError,
    build_prompt_card,
    freeze_trial_protocol,
    parse_trial_record,
    persist_trial_artifacts,
    synthetic_trial,
    validate_trial_record,
    verify_nonleakage_protocol,
)


def _collector() -> TrialMeasurementCollector:
    return TrialMeasurementCollector(
        trial_id="trial-01",
        task_id="task-01",
        task_package_hash="a" * 64,
        condition="candidate",
        runner_fingerprint="runner-1",
        runner_identity="synthetic-runner",
        worker_envelope_sha256="b" * 64,
        rule_fingerprint="rule-1",
        capability_fingerprint="capability-1",
    )


def test_collector_captures_successful_and_failed_raw_response_bytes() -> None:
    record = synthetic_trial(
        _collector,
        [
            HelperResponseEvent("discovery", "正常", True),
            HelperResponseEvent("target", b"failed response", False),
            HelperResponseEvent("repair", "ok", True),
        ],
        outcome="failure",
        correct=False,
        failure="target rejected",
        estimated_tokens=None,
        unavailable_reason="Helper exposes no token accounting",
    )
    assert record["schema_version"] == TRIAL_SCHEMA_VERSION
    assert record["response_bytes"] == len("正常".encode()) + len(b"failed response") + len(b"ok")
    assert record["total_calls"] == 3
    assert record["invalid_requests"] == 1
    assert record["first_legal"] is False
    assert record["estimated_tokens"] is None
    assert record["unavailable_reason"]


def test_collector_records_timeout_and_uses_monotonic_duration() -> None:
    collector = _collector()
    collector.observe(HelperResponseEvent("target", "response", True))
    record = collector.finalize(
        outcome="timeout",
        correct=None,
        failure="deadline exceeded",
        estimated_tokens=None,
        unavailable_reason="Helper exposes no token accounting",
    )
    assert record["timed_out"] is True
    assert record["duration_seconds"] >= 0
    assert record["first_legal"] is True


@pytest.mark.parametrize(
    "mutator",
    [
        lambda record: record.pop("response_bytes"),
        lambda record: record.__setitem__("unexpected", True),
        lambda record: record.__setitem__("invalid_requests", "zero"),
        lambda record: record.__setitem__("estimated_tokens", 0) or record.__setitem__("unavailable_reason", "missing"),
    ],
)
def test_schema_rejects_missing_extra_malformed_and_zero_token_substitution(mutator) -> None:  # type: ignore[no-untyped-def]
    record = synthetic_trial(
        _collector,
        [],
        outcome="success",
        correct=True,
        estimated_tokens=None,
        unavailable_reason="not provided",
    )
    mutator(record)
    with pytest.raises(TrialMeasurementError):
        validate_trial_record(record)


def test_schema_rejects_malformed_json() -> None:
    with pytest.raises(TrialMeasurementError, match="valid JSON"):
        parse_trial_record('{"unfinished":')


def test_schema_rejects_missing_or_malformed_transcript_hash() -> None:
    record = synthetic_trial(
        _collector,
        [HelperResponseEvent("target", "response", True)],
        outcome="success",
        correct=True,
        estimated_tokens=None,
        unavailable_reason="not provided",
    )
    record.pop("transcript_sha256")
    with pytest.raises(TrialMeasurementError, match="closed"):
        validate_trial_record(record)


def test_prompt_card_requires_current_verified_source() -> None:
    source = "text_match is available in the fact candidate query."
    sources = {"helper capabilities": source}
    card = build_prompt_card(
        [
            ContractClaim(
                statement="text_match is available in the fact candidate query.",
                source_ref="helper capabilities",
                source_fingerprint=hashlib.sha256(source.encode()).hexdigest(),
            )
        ],
        read_current_source=sources.__getitem__,
    )
    assert card["claims"][0]["source_ref"] == "helper capabilities"
    with pytest.raises(TrialMeasurementError, match="supported"):
        build_prompt_card(
            [
                ContractClaim(
                    statement="unsupported claim",
                    source_ref="helper capabilities",
                    source_fingerprint=hashlib.sha256(source.encode()).hexdigest(),
                )
            ],
            read_current_source=sources.__getitem__,
        )
    with pytest.raises(TrialMeasurementError, match="fingerprint"):
        build_prompt_card(
            [
                ContractClaim(
                    statement=source,
                    source_ref="helper capabilities",
                    source_fingerprint="0" * 64,
                )
            ],
            read_current_source=sources.__getitem__,
        )


def test_temp_root_writes_only_new_files_beneath_its_own_identity(tmp_path: Path) -> None:
    root = SafeTrialTempRoot.create(prefix="ldvh-test-", repository_root=tmp_path)
    output = root.write_json("results/trial.json", {"ok": True})
    assert output.parent.parent == root.root
    assert output.read_text(encoding="utf-8") == '{"ok":true}\n'
    with pytest.raises(TrialMeasurementError, match="newly created"):
        root.write_json("results/trial.json", {"ok": False})


@pytest.mark.parametrize("path", ["../escape.json", "/tmp/escape.json", "nested/../../escape.json"])
def test_temp_root_rejects_traversal_and_absolute_paths(tmp_path: Path, path: str) -> None:
    root = SafeTrialTempRoot.create(prefix="ldvh-test-", repository_root=tmp_path)
    with pytest.raises(TrialMeasurementError, match="relative path"):
        root.write_json(path, {"ok": True})


def test_temp_root_rejects_symlink_escape_and_identity_drift(tmp_path: Path) -> None:
    root = SafeTrialTempRoot.create(prefix="ldvh-test-", repository_root=tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root.root / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(TrialMeasurementError):
        root.write_json("link/escape.json", {"ok": True})

    original = root.root
    replacement = original.with_name(f"{original.name}-replacement")
    original.rename(replacement)
    original.mkdir()
    with pytest.raises(TrialMeasurementError, match="identity changed"):
        root.write_json("trial.json", {"ok": True})


def test_temp_root_rejects_repository_local_mkdtemp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    created = tmp_path / "ldvh-trial-inside-repository"
    created.mkdir()
    monkeypatch.setattr("ldvh.testing.trial_measurement.tempfile.mkdtemp", lambda **_kwargs: str(created))
    with pytest.raises(TrialMeasurementError, match="inside the repository"):
        SafeTrialTempRoot.create(repository_root=tmp_path)


def test_temp_root_rejects_non_runner_parent_and_realpath_drift(tmp_path: Path) -> None:
    root = SafeTrialTempRoot.create(prefix="ldvh-test-", repository_root=tmp_path)
    foreign = root.root / "foreign"
    foreign.mkdir()
    with pytest.raises(TrialMeasurementError, match="not created by this runner"):
        root.write_json("foreign/trial.json", {"ok": True})

    root._resolved_root = root.root / "different"  # noqa: SLF001 - exercise fail-closed drift branch.
    with pytest.raises(TrialMeasurementError, match="realpath drifted"):
        root.write_json("trial.json", {"ok": True})


def test_temp_root_rejects_symlink_swap_before_exclusive_write(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = SafeTrialTempRoot.create(prefix="ldvh-test-", repository_root=tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    original_open = os.open

    def swap_then_open(path: str | Path, flags: int, mode: int = 0o777) -> int:
        Path(path).symlink_to(outside / "escape.json")
        return original_open(path, flags, mode)

    monkeypatch.setattr("ldvh.testing.trial_measurement.os.open", swap_then_open)
    with pytest.raises(TrialMeasurementError, match="exclusive creation"):
        root.write_json("trial.json", {"ok": True})
    assert not (outside / "escape.json").exists()
    assert not (root.root / "trial.json").exists()


def test_freeze_protocol_binds_tasks_cards_fingerprints_and_scope(tmp_path: Path) -> None:
    source = "text_match is available in the fact candidate query."
    protocol = freeze_trial_protocol(
        repository_root=tmp_path,
        tasks=[
            FrozenTrialTask(
                task_id=f"task-{index:02d}",
                prompt=f"Complete task {index}.",
                gold_rubric={"expected": f"answer-{index}"},
            )
            for index in range(1, 13)
        ],
        baseline_prompt="Use only the supplied task.",
        candidate_claims=[
            ContractClaim(
                statement=source,
                source_ref="helper capabilities",
                source_fingerprint=hashlib.sha256(source.encode()).hexdigest(),
            )
        ],
        read_current_source={"helper capabilities": source}.__getitem__,
        allowed_operations=["find-fact-object-candidates", "read-fact-objects"],
        environment_metadata={"model": "test", "permissions": "test-only"},
        environment_fingerprints={"helper": "a" * 64, "rule": "b" * 64},
        seed=7,
    )
    payload = json.loads(protocol.protocol_path.read_text(encoding="utf-8"))
    assert payload["task_count"] == 12
    assert len(payload["trial_order"]) == 24
    assert payload["preflight"]["status"] == "passed"
    assert payload["preflight"]["candidate_base_prompt_hash"] == payload["baseline_prompt_hash"]
    assert not protocol.root.root.is_relative_to(tmp_path)


def test_preflight_rejects_target_contract_leak_in_common_task_or_gold() -> None:
    source = "Use text_match={text, field_paths} for this candidate query."
    candidate_card = build_prompt_card(
        [ContractClaim(source, "capabilities", hashlib.sha256(source.encode()).hexdigest())],
        read_current_source={"capabilities": source}.__getitem__,
    )
    tasks = [FrozenTrialTask("task-01", "Use text_match to find the answer.", {"expected": "ok"})]
    with pytest.raises(TrialMeasurementError, match="leaks protected contract term"):
        verify_nonleakage_protocol(
            tasks=tasks,
            baseline_prompt="Complete the supplied objective.",
            candidate_base_prompt="Complete the supplied objective.",
            candidate_card=candidate_card,
        )
    with pytest.raises(TrialMeasurementError, match="leaks protected contract term"):
        verify_nonleakage_protocol(
            tasks=[FrozenTrialTask("task-01", "Complete the supplied objective.", {"field_paths": "x"})],
            baseline_prompt="Complete the supplied objective.",
            candidate_base_prompt="Complete the supplied objective.",
            candidate_card=candidate_card,
        )


def test_preflight_rejects_condition_difference_or_condition_labeled_gold() -> None:
    source = "Use text_match={text, field_paths} for this candidate query."
    candidate_card = build_prompt_card(
        [ContractClaim(source, "capabilities", hashlib.sha256(source.encode()).hexdigest())],
        read_current_source={"capabilities": source}.__getitem__,
    )
    tasks = [FrozenTrialTask("task-01", "Complete the supplied objective.", {"expected": "ok"})]
    with pytest.raises(TrialMeasurementError, match="base prompts must be identical"):
        verify_nonleakage_protocol(
            tasks=tasks,
            baseline_prompt="baseline objective",
            candidate_base_prompt="candidate objective",
            candidate_card=candidate_card,
        )
    with pytest.raises(TrialMeasurementError, match="condition-blind"):
        verify_nonleakage_protocol(
            tasks=[FrozenTrialTask("task-01", "Complete the supplied objective.", {"expected_condition": "candidate"})],
            baseline_prompt="Complete the supplied objective.",
            candidate_base_prompt="Complete the supplied objective.",
            candidate_card=candidate_card,
        )


def test_freeze_protocol_rejects_non_twelve_task_packages(tmp_path: Path) -> None:
    with pytest.raises(TrialMeasurementError, match="exactly twelve"):
        freeze_trial_protocol(
            repository_root=tmp_path,
            tasks=[],
            baseline_prompt="baseline",
            candidate_claims=[
                ContractClaim("x", "source", hashlib.sha256(b"x").hexdigest()),
            ],
            read_current_source={"source": "x"}.__getitem__,
            allowed_operations=["read-fact-objects"],
            environment_metadata={"model": "test"},
            environment_fingerprints={"helper": "a"},
            seed=1,
        )


def test_persisted_transcript_must_match_record_hash(tmp_path: Path) -> None:
    source = "text_match is available in the fact candidate query."
    protocol = freeze_trial_protocol(
        repository_root=tmp_path,
        tasks=[
            FrozenTrialTask(f"task-{index:02d}", f"task {index}", {"expected": index})
            for index in range(1, 13)
        ],
        baseline_prompt="baseline",
        candidate_claims=[ContractClaim(source, "source", hashlib.sha256(source.encode()).hexdigest())],
        read_current_source={"source": source}.__getitem__,
        allowed_operations=["read-fact-objects"],
        environment_metadata={"model": "test"},
        environment_fingerprints={"helper": "a"},
        seed=1,
    )
    collector = _collector()
    event = HelperResponseEvent("target", "response", True)
    collector.observe(event)
    record = collector.finalize(
        outcome="success", correct=True, estimated_tokens=None, unavailable_reason="not provided"
    )
    envelope = protocol.worker_envelopes[("task-01", "candidate")]
    record["worker_envelope_sha256"] = envelope.envelope_sha256
    record["runner_identity"] = "synthetic-runner"
    record["runner_fingerprint"] = hashlib.sha256(
        f"synthetic-runner\0{envelope.envelope_sha256}".encode()
    ).hexdigest()
    record_path, transcript_path = persist_trial_artifacts(protocol, record=record, transcript=[event])
    assert record_path.exists()
    assert transcript_path.exists()
    with pytest.raises(TrialMeasurementError, match="transcript hash"):
        persist_trial_artifacts(protocol, record=record, transcript=[])


def test_runner_owned_adapter_isolates_envelopes_and_records_actual_dispatch() -> None:
    source = "Use text_match={text, field_paths} for this candidate query."
    fingerprints = {
        "candidate_rule_source": hashlib.sha256(source.encode()).hexdigest(),
        "capability_source": hashlib.sha256(source.encode()).hexdigest(),
    }
    tasks = [
        FrozenTrialTask(f"task-{index:02d}", f"Complete objective {index}.", {"expected": index})
        for index in range(1, 13)
    ]
    protocol = freeze_trial_protocol(
        repository_root=Path.cwd(),
        tasks=tasks,
        baseline_prompt="Complete the supplied objective.",
        candidate_claims=[ContractClaim(source, "source", hashlib.sha256(source.encode()).hexdigest())],
        read_current_source={"source": source}.__getitem__,
        allowed_operations=["capabilities", "find-fact-object-candidates"],
        environment_metadata={"model": "test", "permissions": "test-only"},
        environment_fingerprints=fingerprints,
        seed=7,
    )
    adapter = RunnerOwnedTrialAdapter(
        protocol=protocol,
        read_current_source={"source": source}.__getitem__,
        operation_categories={"capabilities": "discovery", "find-fact-object-candidates": "target"},
        runner_identity="runner-1",
        environment_readers={name: (lambda source=source: source.encode()) for name in fingerprints},
    )
    baseline = adapter.start_trial(task_id="task-01", condition="baseline", trial_id="trial-01")
    candidate = adapter.start_trial(task_id="task-01", condition="candidate", trial_id="trial-02")
    assert "candidate_card" not in baseline.envelope.payload
    assert "candidate_card" in candidate.envelope.payload
    assert "gold" not in baseline.envelope.payload
    assert str(protocol.root.root) not in json.dumps(candidate.envelope.payload, ensure_ascii=False)

    response = baseline.invoke(
        "find-fact-object-candidates",
        b'{"request":"actual"}',
        dispatch=lambda operation, request: b'{"outcome":"ok"}',
    )
    assert response == b'{"outcome":"ok"}'
    record, transcript = baseline.finalize(
        outcome="success", correct=True, estimated_tokens=None, unavailable_reason="not provided"
    )
    assert record["first_legal"] is True
    assert transcript[0].raw_request == b'{"request":"actual"}'
    record_path, transcript_path = persist_trial_artifacts(protocol, record=record, transcript=transcript)
    assert record_path.exists()
    assert transcript_path.exists()
    with pytest.raises(TrialMeasurementError, match="allowlist"):
        baseline.invoke("read-fact-objects", b"{}", dispatch=lambda _operation, _request: b"{}")


def test_runner_owned_adapter_rejects_source_drift_before_trial() -> None:
    source = "Use text_match={text, field_paths} for this candidate query."
    sources = {"source": source}
    fingerprints = {
        "candidate_rule_source": hashlib.sha256(source.encode()).hexdigest(),
        "capability_source": hashlib.sha256(source.encode()).hexdigest(),
    }
    tasks = [
        FrozenTrialTask(f"task-{index:02d}", f"Complete objective {index}.", {"expected": index})
        for index in range(1, 13)
    ]
    protocol = freeze_trial_protocol(
        repository_root=Path.cwd(),
        tasks=tasks,
        baseline_prompt="Complete the supplied objective.",
        candidate_claims=[ContractClaim(source, "source", hashlib.sha256(source.encode()).hexdigest())],
        read_current_source=sources.__getitem__,
        allowed_operations=["find-fact-object-candidates"],
        environment_metadata={"model": "test", "permissions": "test-only"},
        environment_fingerprints=fingerprints,
        seed=7,
    )
    sources["source"] = "drifted"
    adapter = RunnerOwnedTrialAdapter(
        protocol=protocol,
        read_current_source=sources.__getitem__,
        operation_categories={"find-fact-object-candidates": "target"},
        runner_identity="runner-1",
        environment_readers={name: (lambda source=source: source.encode()) for name in fingerprints},
    )
    with pytest.raises(TrialMeasurementError, match="fingerprint"):
        adapter.start_trial(task_id="task-01", condition="baseline", trial_id="trial-01")


def test_runner_owned_adapter_rejects_any_frozen_environment_drift() -> None:
    source = "Use text_match={text, field_paths} for this candidate query."
    entrypoint = b"frozen entrypoint"
    fingerprints = {
        "candidate_rule_source": hashlib.sha256(source.encode()).hexdigest(),
        "capability_source": hashlib.sha256(source.encode()).hexdigest(),
        "helper_entrypoint": hashlib.sha256(entrypoint).hexdigest(),
    }
    protocol = freeze_trial_protocol(
        repository_root=Path.cwd(),
        tasks=[
            FrozenTrialTask(f"task-{index:02d}", f"Complete objective {index}.", {"expected": index})
            for index in range(1, 13)
        ],
        baseline_prompt="Complete the supplied objective.",
        candidate_claims=[ContractClaim(source, "source", hashlib.sha256(source.encode()).hexdigest())],
        read_current_source={"source": source}.__getitem__,
        allowed_operations=["find-fact-object-candidates"],
        environment_metadata={"model": "test", "permissions": "test-only"},
        environment_fingerprints=fingerprints,
        seed=7,
    )
    adapter = RunnerOwnedTrialAdapter(
        protocol=protocol,
        read_current_source={"source": source}.__getitem__,
        operation_categories={"find-fact-object-candidates": "target"},
        runner_identity="runner-1",
        environment_readers={
            "candidate_rule_source": lambda: source.encode(),
            "capability_source": lambda: source.encode(),
            "helper_entrypoint": lambda: b"drifted entrypoint",
        },
    )
    with pytest.raises(TrialMeasurementError, match="helper_entrypoint"):
        adapter.start_trial(task_id="task-01", condition="baseline", trial_id="trial-01")
