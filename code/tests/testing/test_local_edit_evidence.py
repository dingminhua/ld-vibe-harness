from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from ldvh.testing.local_edit_evidence import (
    EVIDENCE_SCHEMA_VERSION,
    OPERATION_KEY,
    EvidenceIdentity,
    build_record,
    input_receipt,
    persist_record,
    project_record,
    recover_record,
    summarize,
    task_package_fingerprint,
    trace_event,
    validate_record,
)
from ldvh.testing.local_edit_evidence_runner import LocalEditEvidenceRunner
from ldvh.testing.trial_measurement import SafeTrialTempRoot, TrialMeasurementError


def _identity(trace_id: str = "T1") -> EvidenceIdentity:
    return EvidenceIdentity(
        run_id="run-1",
        trial_id=trace_id,
        worktree_fingerprint="1" * 64,
        governed_project_id="ldvh",
        task_package_fingerprint="2" * 64,
        rule_fingerprint="3" * 64,
        capability_fingerprint="4" * 64,
        runner_fingerprint="5" * 64,
    )


def _inputs() -> list[dict[str, object]]:
    return [
        input_receipt(
            kind="rule_locator",
            status="delivered",
            locator="ldvh-root::8/8.1",
            source_range="L213-L224",
            fingerprint="3" * 64,
            length=17,
        ),
        input_receipt(
            kind="capability_locator",
            status="delivered",
            locator=OPERATION_KEY,
            fingerprint="4" * 64,
        ),
        input_receipt(
            kind="task_package",
            status="delivered",
            locator="run:run-1/trial:T1",
            fingerprint="2" * 64,
            hash_subject="canonical_high_entropy_task_package",
        ),
    ]


def _external(outcome: str, *, stale: bool | None = False) -> dict[str, object]:
    return {
        "helper_outcome": outcome,
        "stale": stale,
        "change_count": 0,
        "source_locator": "specs/00-理念与构成.md" if outcome == "ok" else None,
        "source_range": "L213-L224" if outcome == "ok" else None,
    }


def _verification(value: bool = True) -> dict[str, bool]:
    return {
        "readback": value,
        "integrity": value,
        "boundary_match": value,
        "external_evidence": value,
    }


def _fault(trace_id: str) -> dict[str, object]:
    synthetic = trace_id in {"T3b", "T4a", "T4b"}
    return {
        "origin": "synthetic_harness" if synthetic else "real_helper",
        "operation_key": OPERATION_KEY,
        "deadline_seconds": 0 if trace_id == "T3b" else None,
        "deadline_source": "frozen synthetic fault" if trace_id == "T3b" else None,
        "evidence_kind": {
            "T1": "process_exit",
            "T2": "process_exit",
            "T3a": "rejected_response",
            "T3b": "deadline",
            "T4a": "interruption",
            "T4b": "integrity_violation",
        }[trace_id],
    }


def _record(trace_id: str = "T1") -> dict[str, object]:
    names = {
        "T1": ("request_observed", "response_observed", "external_state_checked", "verification_completed"),
        "T2": (
            "request_observed",
            "initial_response_observed",
            "repair_request_observed",
            "repaired_response_observed",
            "external_state_checked",
            "verification_completed",
        ),
        "T3a": ("request_observed", "response_observed", "external_state_checked", "verification_completed"),
        "T3b": ("deadline_observed", "verification_completed"),
        "T4a": ("interruption_observed", "verification_completed"),
        "T4b": ("integrity_violation_observed", "verification_completed"),
    }[trace_id]
    calls = {"T1": 1, "T2": 2, "T3a": 1, "T3b": 0, "T4a": 0, "T4b": 0}[trace_id]
    outcome = {"T3a": "rejected", "T3b": "timeout"}.get(trace_id, "ok")
    inputs = _inputs()
    inputs[-1]["locator"] = f"run:run-1/trial:{trace_id}"
    return build_record(
        identity=_identity(trace_id),
        trace_id=trace_id,
        inputs=inputs,
        events=[
            trace_event(index, name, response_bytes=10 if "helper" in name else None)
            for index, name in enumerate(names)
        ],
        helper_calls=calls,
        repairs=1 if trace_id == "T2" else 0,
        external_state=_external(outcome, stale=False if trace_id in {"T1", "T2"} else None),
        verification=_verification(trace_id not in {"T4a", "T4b"}),
        fault=_fault(trace_id),
    )


@pytest.mark.parametrize(
    ("trace_id", "expected"),
    (
        ("T1", "observed"),
        ("T2", "observed"),
        ("T3a", "failed"),
        ("T3b", "timeout"),
        ("T4a", "inconclusive"),
        ("T4b", "inconclusive"),
    ),
)
def test_frozen_trace_projection(trace_id: str, expected: str) -> None:
    record = _record(trace_id)

    assert project_record(record) == expected


def test_partial_trace_is_valid_evidence_but_projects_inconclusive() -> None:
    record = _record("T2")
    record["events"] = record["events"][:2]
    record["helper_calls"] = 1
    record["repairs"] = 0

    validate_record(record)
    assert project_record(record) == "inconclusive"


@pytest.mark.parametrize(
    "bad_events",
    (("request_observed", "external_state_checked"), ("request_observed", "request_observed")),
)
def test_missing_duplicate_or_out_of_order_events_fail_closed(bad_events: tuple[str, ...]) -> None:
    record = _record()
    record["events"] = [trace_event(index, name) for index, name in enumerate(bad_events)]

    assert project_record(record) == "inconclusive"


def test_calls_and_single_repair_cannot_cross_frozen_cap() -> None:
    record = _record("T2")
    record["helper_calls"] = 3

    with pytest.raises(TrialMeasurementError, match="crossed"):
        validate_record(record)


@pytest.mark.parametrize(
    ("trace_id", "bad_kind"),
    (
        ("T1", "rejected_response"),
        ("T3a", "process_exit"),
        ("T3b", "interruption"),
        ("T4a", "integrity_violation"),
        ("T4b", "deadline"),
    ),
)
def test_fault_evidence_kind_is_trace_bound(trace_id: str, bad_kind: str) -> None:
    record = _record(trace_id)
    record["fault"]["evidence_kind"] = bad_kind

    with pytest.raises(TrialMeasurementError, match="require"):
        validate_record(record)


def test_deadline_fields_are_closed_to_deadline_evidence() -> None:
    real = _record("T1")
    real["fault"]["deadline_seconds"] = 1
    real["fault"]["deadline_source"] = "test"
    with pytest.raises(TrialMeasurementError, match="only allowed"):
        validate_record(real)

    timeout = _record("T3b")
    timeout["fault"]["deadline_seconds"] = None
    with pytest.raises(TrialMeasurementError, match="requires"):
        validate_record(timeout)


def test_unavailable_input_takes_priority_over_terminal_event() -> None:
    record = _record()
    record["inputs"][0] = input_receipt(
        kind="rule_locator",
        status="unavailable",
        locator="ldvh-root::8/8.1",
        unavailable_reason="host delivery is not observable",
    )

    assert project_record(record) == "inconclusive"


@pytest.mark.parametrize(
    "subject",
    ("fact_body", "candidate_before", "candidate_after", "candidate_diff", "helper_response", "full_prompt"),
)
def test_sensitive_hash_subjects_are_rejected(subject: str) -> None:
    with pytest.raises(TrialMeasurementError, match="hash_subject"):
        input_receipt(
            kind="rule_locator",
            status="delivered",
            locator="rule",
            fingerprint="a" * 64,
            hash_subject=subject,
        )


def test_task_package_requires_entropy_and_rejects_body_keys() -> None:
    with pytest.raises(TrialMeasurementError, match="128 bits"):
        task_package_fingerprint({"trace_id": "T1"}, entropy_nonce="abcd")
    with pytest.raises(TrialMeasurementError, match="forbidden"):
        task_package_fingerprint({"candidate_diff": "secret"}, entropy_nonce="a" * 32)

    observed = task_package_fingerprint({"trace_id": "T1"}, entropy_nonce="a" * 32)
    assert len(observed) == 64


def test_identity_mismatch_and_unknown_version_are_inconclusive() -> None:
    record = _record()
    mismatched = _identity()
    mismatched = EvidenceIdentity(
        run_id=mismatched.run_id,
        trial_id=mismatched.trial_id,
        worktree_fingerprint="f" * 64,
        governed_project_id=mismatched.governed_project_id,
        task_package_fingerprint=mismatched.task_package_fingerprint,
        rule_fingerprint=mismatched.rule_fingerprint,
        capability_fingerprint=mismatched.capability_fingerprint,
        runner_fingerprint=mismatched.runner_fingerprint,
    )
    assert project_record(record, expected_identity=mismatched) == "inconclusive"

    record["schema_version"] = "ldvh-local-edit-evidence/unknown"
    assert project_record(record) == "inconclusive"


def test_persist_recover_and_tamper_detection(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    root = SafeTrialTempRoot.create(repository_root=repository)
    try:
        record = _record()
        path = persist_record(root, "records/T1.json", record)

        projection, recovered = recover_record(root, "records/T1.json", expected_identity=_identity())
        assert projection == "observed"
        assert recovered == record

        envelope = json.loads(path.read_text(encoding="utf-8"))
        envelope["record"]["external_state"]["change_count"] = 1
        path.write_text(json.dumps(envelope), encoding="utf-8")

        assert recover_record(root, "records/T1.json", expected_identity=_identity()) == ("inconclusive", None)
    finally:
        shutil.rmtree(root.root)


def test_unknown_and_half_migrated_envelopes_are_not_repaired(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    root = SafeTrialTempRoot.create(repository_root=repository)
    try:
        record = _record()
        record["schema_version"] = "ldvh-local-edit-evidence/0"
        digest = hashlib.sha256(
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        root.write_json(
            "records/old.json",
            {
                "envelope_version": EVIDENCE_SCHEMA_VERSION,
                "record": record,
                "integrity_sha256": digest,
            },
        )

        assert recover_record(root, "records/old.json", expected_identity=_identity()) == ("inconclusive", None)
        assert record["schema_version"] == "ldvh-local-edit-evidence/0"
    finally:
        shutil.rmtree(root.root)


def test_safe_temp_reader_rejects_missing_and_symlink(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    root = SafeTrialTempRoot.create(repository_root=repository)
    try:
        with pytest.raises(TrialMeasurementError, match="missing"):
            root.read_json("missing.json")
        target = root.root / "target.json"
        target.write_text("{}", encoding="utf-8")
        (root.root / "link.json").symlink_to(target)
        with pytest.raises(TrialMeasurementError, match="regular"):
            root.read_json("link.json")
    finally:
        shutil.rmtree(root.root)


def test_synthetic_runner_never_invokes_helper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "ldvh").write_text("entry", encoding="utf-8")
    runner = LocalEditEvidenceRunner.create(
        repository_root=tmp_path,
        governed_project_id="ldvh",
        run_id="run-1",
    )
    monkeypatch.setattr(LocalEditEvidenceRunner, "_identity", lambda _self, trace_id: _identity(trace_id))

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("synthetic trace invoked the Helper")

    monkeypatch.setattr(LocalEditEvidenceRunner, "_call", forbidden)
    timeout = runner.run_synthetic("T3b")

    assert project_record(timeout) == "timeout"
    assert timeout["fault"]["origin"] == "synthetic_harness"
    assert timeout["helper_calls"] == 0


def test_summary_is_limited_to_protocol_observations() -> None:
    result = summarize([_record("T1"), _record("T3a"), _record("T4a")])

    assert result["record_count"] == 3
    assert result["helper_calls"] == 2
    assert result["projection_counts"] == {"failed": 1, "inconclusive": 1, "observed": 1, "timeout": 0}
    assert "no correctness" in result["claim_boundary"]


def test_run_suite_uses_generic_prefix_and_body_free_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "ldvh").write_text("entry", encoding="utf-8")
    runner = LocalEditEvidenceRunner.create(
        repository_root=tmp_path,
        governed_project_id="ldvh",
        run_id="run-1",
    )
    monkeypatch.setattr(LocalEditEvidenceRunner, "_identity", lambda _self, trace_id: _identity(trace_id))
    monkeypatch.setattr(LocalEditEvidenceRunner, "run_real", lambda _self, trace_id: _record(trace_id))
    monkeypatch.setattr(LocalEditEvidenceRunner, "run_synthetic", lambda _self, trace_id: _record(trace_id))

    run = runner.run_suite()
    try:
        payload = run.summary_payload()

        assert run.root.root.name.startswith("ldvh-local-edit-evidence-")
        assert payload["artifact_root"] == str(run.root.root)
        assert payload["summary"]["record_count"] == 6
        assert len(payload["recoveries"]) == 6
        assert "records" not in payload
    finally:
        shutil.rmtree(run.root.root)


def test_run_suite_accepts_explicit_temp_prefix_without_helper_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "ldvh").write_text("entry", encoding="utf-8")
    runner = LocalEditEvidenceRunner.create(
        repository_root=tmp_path,
        governed_project_id="ldvh",
        run_id="run-1",
    )
    monkeypatch.setattr(LocalEditEvidenceRunner, "_identity", lambda _self, trace_id: _identity(trace_id))
    monkeypatch.setattr(LocalEditEvidenceRunner, "run_real", lambda _self, trace_id: _record(trace_id))
    monkeypatch.setattr(LocalEditEvidenceRunner, "run_synthetic", lambda _self, trace_id: _record(trace_id))

    run = runner.run_suite(temp_prefix="ldvh-custom-evidence-")
    try:
        assert run.root.root.name.startswith("ldvh-custom-evidence-")
    finally:
        shutil.rmtree(run.root.root)
