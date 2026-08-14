from __future__ import annotations

import json

import pytest

from ldvh.testing.equivalence_retrial import (
    EQUIVALENCE_RETRIAL_VERSION,
    VARIANTS,
    CarrierDeclaration,
    ExecutorResult,
    TrialEnvelope,
    TrialMeasurementError,
    assess_trial,
    build_trial_envelope,
    persist_batch_artifacts,
    run_trial,
    summarize_batch,
    validate_executor_result,
)
from ldvh.testing.trial_measurement import SafeTrialTempRoot


def _carrier() -> CarrierDeclaration:
    return CarrierDeclaration(
        provider="aixforge",
        model="glm-5.2",
        runner_identity="retrial-runner-1",
        tool_entry="ldvh",
    )


def _envelope(variant: str = "full_contract", sample_index: int = 0) -> TrialEnvelope:
    return build_trial_envelope(
        trial_id=f"trial-{sample_index}",
        task_id="task-01",
        variant=variant,
        condition_key=variant,
        sample_index=sample_index,
        task_package_hash="a" * 64,
        contract_sha256="1f4fc351bbee0017133485fee614d5af1ef3ed12c95184ea4307a1ec7bbe16fe",
        carrier=_carrier(),
        payload={"task": f"read rule for sample {sample_index}"},
    )


def _event_lines(*, multi_model: bool = False, unpaired: bool = False) -> tuple[str, ...]:
    lines = [
        json.dumps(
            {
                "type": "request/header",
                "seq": 11,
                "data": {
                    "header": {"config": {"provider": "aixforge", "model": "glm-5.2"}},
                    "reason": "initial",
                },
            },
            ensure_ascii=False,
        ),
        json.dumps({"type": "turn/start", "data": {"turn": 1}}, ensure_ascii=False),
        json.dumps({"type": "step/start", "data": {"turn": 1, "step": 1}}, ensure_ascii=False),
        json.dumps({"type": "tool/call", "data": {"name": "read", "turn": 1, "step": 1}}, ensure_ascii=False),
        json.dumps({"type": "tool/result", "data": {"content": "opaque"}}, ensure_ascii=False),
        json.dumps({"type": "step/end", "data": {"turn": 1, "step": 1}}, ensure_ascii=False),
        json.dumps({"type": "turn/end", "data": {"turn": 1}}, ensure_ascii=False),
    ]
    if multi_model:
        lines.insert(
            1,
            json.dumps(
                {
                    "type": "request/header",
                    "seq": 99,
                    "data": {
                        "header": {"config": {"provider": "deepseek-official", "model": "deepseek-v4-flash"}},
                        "reason": "change",
                    },
                },
                ensure_ascii=False,
            ),
        )
    if unpaired:
        lines.pop()  # drop turn/end -> unpaired turn
    return tuple(lines)


def _success_executor(multi_model: bool = False, unpaired: bool = False):
    def execute(envelope: TrialEnvelope) -> ExecutorResult:
        return ExecutorResult(
            output_sha256="c" * 64,
            event_lines=_event_lines(multi_model=multi_model, unpaired=unpaired),
            duration_seconds=0.5,
            outcome="success",
        )

    return execute


def test_envelope_freezes_variant_and_fingerprint() -> None:
    envelope = _envelope(variant="required_removed", sample_index=1)
    assert envelope.variant == "required_removed"
    assert envelope.condition_key == "required_removed"
    assert len(envelope.envelope_sha256) == 64
    with pytest.raises(TrialMeasurementError, match="variant"):
        build_trial_envelope(
            trial_id="t",
            task_id="task",
            variant="not-a-variant",
            condition_key="x",
            sample_index=0,
            task_package_hash="a" * 64,
            contract_sha256="b" * 64,
            carrier=_carrier(),
            payload={"x": 1},
        )


def test_run_trial_comparable_is_gated_through_session_comparability() -> None:
    record = run_trial(envelope=_envelope(), executor=_success_executor())
    assert record.comparability.verdict == "comparable"
    assert record.pairing_ok is True
    assert record.carrier_entry == ("aixforge", "glm-5.2")
    assert record.event_lines_sha256 != ""


def test_run_trial_multi_model_is_not_comparable() -> None:
    record = run_trial(envelope=_envelope(), executor=_success_executor(multi_model=True))
    assert record.comparability.verdict == "not_comparable"
    assert any("multi-model" in reason for reason in record.comparability.reasons)


def test_run_trial_unpaired_is_not_comparable() -> None:
    record = run_trial(envelope=_envelope(), executor=_success_executor(unpaired=True))
    assert record.comparability.verdict == "not_comparable"
    assert record.pairing_ok is False


def test_validate_executor_result_fail_closed() -> None:
    with pytest.raises(TrialMeasurementError, match="outcome"):
        validate_executor_result(
            ExecutorResult(output_sha256="a" * 64, event_lines=("{}",), duration_seconds=0.1, outcome="bogus")
        )
    with pytest.raises(TrialMeasurementError, match="failure"):
        validate_executor_result(
            ExecutorResult(output_sha256="a" * 64, event_lines=("{}",), duration_seconds=0.1, outcome="timeout")
        )


def test_run_trial_rejects_malformed_event_line() -> None:
    def bad_executor(envelope: TrialEnvelope) -> ExecutorResult:
        return ExecutorResult(
            output_sha256="a" * 64,
            event_lines=('{"unfinished":',),
            duration_seconds=0.1,
            outcome="success",
        )

    with pytest.raises(TrialMeasurementError, match="valid JSON"):
        run_trial(envelope=_envelope(), executor=bad_executor)


def test_assess_trial_consumes_machine_record_only() -> None:
    record = run_trial(envelope=_envelope(), executor=_success_executor())
    rubric = {
        "check-comparable": lambda r: r.comparability.verdict == "comparable",
        "check-paired": lambda r: r.pairing_ok is True,
        "check-sha256": lambda r: len(r.output_sha256) == 64,
    }
    assessment = assess_trial(record, rubric)
    assert assessment.status == "satisfied"
    assert len(assessment.checks) == 3


def test_assess_trial_not_satisfied_when_gate_rejects() -> None:
    record = run_trial(envelope=_envelope(), executor=_success_executor(multi_model=True))
    rubric = {"check-comparable": lambda r: r.comparability.verdict == "comparable"}
    assessment = assess_trial(record, rubric)
    assert assessment.status == "not_satisfied"


def test_summarize_batch_requires_single_carrier() -> None:
    records = [
        run_trial(envelope=_envelope(sample_index=0), executor=_success_executor()),
        run_trial(envelope=_envelope(sample_index=1), executor=_success_executor()),
    ]
    assessments = [assess_trial(record, {"c": lambda r: True}) for record in records]
    summary = summarize_batch(records, assessments)
    assert summary.trials == 2
    assert summary.comparable_count == 2
    assert summary.satisfied_count == 2
    assert summary.payload()["claim_boundary"]


def test_summarize_batch_mixed_verdicts() -> None:
    records = [
        run_trial(envelope=_envelope(sample_index=0), executor=_success_executor()),
        run_trial(envelope=_envelope(sample_index=1), executor=_success_executor(multi_model=True)),
        run_trial(envelope=_envelope(sample_index=2), executor=_success_executor(unpaired=True)),
    ]
    assessments = [assess_trial(record, {"c": lambda r: True}) for record in records]
    summary = summarize_batch(records, assessments)
    assert summary.comparable_count == 1
    assert summary.not_comparable_count == 2
    assert summary.inconclusive_count == 0
    assert summary.verdict_counts["not_comparable"] == 2


def test_summarize_batch_rejects_mixed_carriers() -> None:
    record = run_trial(envelope=_envelope(), executor=_success_executor())
    assessment = assess_trial(record, {"c": lambda r: True})

    class OtherCarrierRecord:  # minimal stand-in with a different carrier tuple
        carrier_fingerprint = "other"
        carrier_entry = ("other", "other")
        comparability = record.comparability
        outcome = "success"

    with pytest.raises(TrialMeasurementError, match="carrier"):
        summarize_batch([record, OtherCarrierRecord()], [assessment, assessment])


def test_persist_batch_artifacts_writes_structural_aggregates(tmp_path) -> None:  # type: ignore[no-untyped-def]
    root = SafeTrialTempRoot.create(prefix="ldvh-retrial-test-", repository_root=tmp_path)
    records = [run_trial(envelope=_envelope(sample_index=0), executor=_success_executor())]
    assessments = [assess_trial(record, {"c": lambda r: True}) for record in records]
    summary = summarize_batch(records, assessments)
    paths = persist_batch_artifacts(root, records=records, assessments=assessments, summary=summary)
    assert all(path.exists() for path in paths)
    payload = root.read_json("records/trials.json")
    assert "opaque" not in json.dumps(payload, ensure_ascii=False)
    summary_payload = root.read_json("records/summary.json")
    assert summary_payload["claim_boundary"]


def test_summarize_batch_rejects_empty() -> None:
    with pytest.raises(TrialMeasurementError, match="at least one"):
        summarize_batch([], [])


def test_schema_version_is_stable() -> None:
    assert EQUIVALENCE_RETRIAL_VERSION == "ldvh-equivalence-retrial/1"
    assert VARIANTS == ("full_contract", "required_removed", "irrelevant_added")
