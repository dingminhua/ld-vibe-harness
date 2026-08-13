from __future__ import annotations

import json
from pathlib import Path

import pytest

from ldvh.testing.rule_read_contract import (
    CLAIM_BOUNDARY,
    ContextEntry,
    assess_output,
    bind_variant,
    blind_score_payload,
    build_contract,
    execution_payload,
    freeze_task,
    persist_integrity_envelope,
    recover_integrity_envelope,
    summarize_aggregate,
)
from ldvh.testing.trial_measurement import SafeTrialTempRoot, TrialMeasurementError
from ldvh.testing.working_tree_evidence import canonical_sha256

_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64


def _contract():
    return build_contract(
        (
            ContextEntry("helper-entry", "required", "specs/04#helper-entry", _SHA_A, "always"),
            ContextEntry("selection-shape", "required", "specs/01#selection-shape", _SHA_B, "always"),
            ContextEntry("conditional-repair", "conditional", "specs/04#repair", _SHA_C, "on invalid request"),
            ContextEntry("git-commit-fields", "excluded", "specs/30#commit-fields", _SHA_A, "never for rule read"),
        ),
        invalidation_conditions=("source fingerprint changes", "operation contract changes"),
    )


def _task():
    return freeze_task(
        task_id="task-root-guidance",
        human_goal="Read the exact LDVH root guidance section.",
        responsibility_key="ldvh-root",
        heading_path=("8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"),
        disclosure="L3",
        source_locator="specs/00-理念与构成.md#L213-L224",
        source_sha256=_SHA_A,
        expected_outcome="ok",
        expected_completed_scope=(("ldvh-root", ("8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露")),),
        expected_part_sha256=(_SHA_B, _SHA_C),
    )


def _record(**updates):
    value = {
        "task_sha256": _task().task_sha256,
        "variant": "full_contract",
        "output_sha256": _SHA_A,
        "objective_status": "passed",
        "independent_scores": ["pass", "pass"],
        "calls": 1,
        "repairs": 0,
        "latency_ms": 5,
        "failure_reason": None,
    }
    value.update(updates)
    return value


def test_contract_is_closed_unique_and_deterministic() -> None:
    first = _contract()
    second = _contract()

    assert first.contract_sha256 == second.contract_sha256
    assert {entry.kind for entry in first.entries} == {"required", "conditional", "excluded"}

    with pytest.raises(TrialMeasurementError, match="unique"):
        build_contract(
            (
                ContextEntry("same", "required", "a", _SHA_A, "always"),
                ContextEntry("same", "excluded", "b", _SHA_B, "never"),
            ),
            invalidation_conditions=("changed",),
        )


@pytest.mark.parametrize(
    "entries",
    (
        (ContextEntry("required", "required", "a", _SHA_A, "always"),),
        (
            ContextEntry("required", "unknown", "a", _SHA_A, "always"),
            ContextEntry("excluded", "excluded", "b", _SHA_B, "never"),
        ),
        (
            ContextEntry("required", "required", "a", _SHA_A, "always", ("required",)),
            ContextEntry("excluded", "excluded", "b", _SHA_B, "never"),
        ),
    ),
)
def test_contract_rejects_missing_kinds_unknown_kinds_and_self_alternatives(entries) -> None:
    with pytest.raises(TrialMeasurementError):
        build_contract(entries, invalidation_conditions=("changed",))


def test_task_rejects_non_l3_and_empty_scope_identity() -> None:
    with pytest.raises(TrialMeasurementError, match="exact L3"):
        freeze_task(
            task_id="task",
            human_goal="goal",
            responsibility_key="key",
            heading_path=(),
            disclosure="L4",
            source_locator="specs/00",
            source_sha256=_SHA_A,
            expected_outcome="ok",
            expected_completed_scope=(("key", ("heading",)),),
            expected_part_sha256=(_SHA_B,),
        )


def test_variants_bind_only_context_deltas() -> None:
    contract = _contract()
    task = _task()
    full = bind_variant(contract, task, variant="full_contract", condition_key="condition-01")
    removed = bind_variant(
        contract,
        task,
        variant="required_removed",
        condition_key="condition-02",
        removed_entry_id="selection-shape",
    )
    added = bind_variant(
        contract,
        task,
        variant="irrelevant_added",
        condition_key="condition-03",
        added_entry_id="git-commit-fields",
    )

    assert full.task_sha256 == removed.task_sha256 == added.task_sha256
    assert full.contract_sha256 == removed.contract_sha256 == added.contract_sha256
    assert "selection-shape" in full.context_entry_ids and "selection-shape" not in removed.context_entry_ids
    assert "git-commit-fields" not in full.context_entry_ids and "git-commit-fields" in added.context_entry_ids
    assert len({full.envelope_sha256, removed.envelope_sha256, added.envelope_sha256}) == 3


@pytest.mark.parametrize(
    ("variant", "removed", "added"),
    (
        ("full_contract", "helper-entry", None),
        ("required_removed", None, None),
        ("required_removed", "git-commit-fields", None),
        ("irrelevant_added", None, "helper-entry"),
    ),
)
def test_invalid_context_deltas_fail_closed(variant: str, removed: str | None, added: str | None) -> None:
    with pytest.raises(TrialMeasurementError):
        bind_variant(
            _contract(),
            _task(),
            variant=variant,
            condition_key="condition-x",
            removed_entry_id=removed,
            added_entry_id=added,
        )


def test_condition_key_is_not_exposed_to_execution_or_scorer() -> None:
    envelope = bind_variant(_contract(), _task(), variant="full_contract", condition_key="secret-condition")
    execution = execution_payload(envelope, _task())
    score = blind_score_payload(_task(), output_sha256=_SHA_A, objective_checks={"outcome": True})

    assert "secret-condition" not in json.dumps(execution)
    assert "secret-condition" not in json.dumps(score)
    assert "variant" not in execution
    assert "variant" not in score


def test_execution_payload_rejects_a_different_task() -> None:
    envelope = bind_variant(_contract(), _task(), variant="full_contract", condition_key="condition")
    other = freeze_task(
        task_id="other-task",
        human_goal="Read another section.",
        responsibility_key="ldvh-root",
        heading_path=("8. 系统级运行架构",),
        disclosure="L3",
        source_locator="specs/00#L205-L240",
        source_sha256=_SHA_A,
        expected_outcome="ok",
        expected_completed_scope=(("ldvh-root", ("8. 系统级运行架构",)),),
        expected_part_sha256=(_SHA_B,),
    )
    with pytest.raises(TrialMeasurementError, match="does not bind"):
        execution_payload(envelope, other)


def test_objective_rubric_uses_hashes_and_closed_structure() -> None:
    task = _task()
    output = {
        "outcome": "ok",
        "completed_scope": [
            {
                "responsibility_key": "ldvh-root",
                "heading_path": ["8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"],
            }
        ],
        "part_sha256": [_SHA_B, _SHA_C],
        "source_locator": "specs/00-理念与构成.md#L213-L224",
        "actual_disclosure": "L3",
    }

    assessment = assess_output(task, output)
    assert assessment.status == "passed"
    assert all(assessment.checks.values())
    assert assessment.output_sha256 == canonical_sha256(output)

    output["part_sha256"] = [_SHA_C]
    assert assess_output(task, output).status == "failed"


def test_sensitive_material_cannot_enter_assessment_or_aggregate() -> None:
    with pytest.raises(TrialMeasurementError, match="sensitive"):
        assess_output(_task(), {"raw_prompt": "do not retain"})
    with pytest.raises(TrialMeasurementError, match="sensitive"):
        summarize_aggregate([_record(raw_response="do not retain")])


def test_aggregate_requires_two_agreeing_scores_and_keeps_claim_boundary() -> None:
    observed = summarize_aggregate([_record()])
    assert observed["method_status"] == "observed"
    assert observed["records"][0]["agreement"] is True
    assert observed["evidence_levels"]["host-received"] == "unavailable"
    assert observed["evidence_levels"]["causal-effect"] == "not_established"
    assert observed["claim_boundary"] == CLAIM_BOUNDARY
    assert "does not prove" in observed["claim_boundary"]

    inconclusive = summarize_aggregate([_record(independent_scores=["pass", "fail"])])
    assert inconclusive["method_status"] == "inconclusive"
    assert inconclusive["records"][0]["agreement"] is False


@pytest.mark.parametrize("scores", ([], ["pass"], ["pass", "unknown"]))
def test_aggregate_rejects_insufficient_or_unknown_scores(scores: list[str]) -> None:
    with pytest.raises(TrialMeasurementError, match="independent scores"):
        summarize_aggregate([_record(independent_scores=scores)])


@pytest.mark.parametrize(
    "updates",
    (
        {"objective_status": "pass"},
        {"variant": "unknown"},
        {"calls": -1},
        {"repairs": True},
        {"latency_ms": "fast"},
        {"failure_reason": []},
    ),
)
def test_aggregate_rejects_malformed_measurements(updates) -> None:
    with pytest.raises(TrialMeasurementError):
        summarize_aggregate([_record(**updates)])


def test_integrity_envelope_recovers_and_tamper_is_inconclusive(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    root = SafeTrialTempRoot.create(prefix="ldvh-rule-read-test-", repository_root=repository)
    try:
        persist_integrity_envelope(root, "aggregate.json", {"contract": "aggregate", "count": 1})
        status, record = recover_integrity_envelope(root, "aggregate.json")
        assert status == "observed"
        assert record == {"contract": "aggregate", "count": 1}

        artifact = root.root / "aggregate.json"
        envelope = json.loads(artifact.read_text(encoding="utf-8"))
        envelope["record"]["count"] = 2
        artifact.write_text(json.dumps(envelope), encoding="utf-8")
        status, record = recover_integrity_envelope(root, "aggregate.json")
        assert status == "inconclusive"
        assert record is None

        root.write_json(
            "sensitive.json",
            {
                "record": {"raw_prompt": "not permitted"},
                "integrity_sha256": canonical_sha256({"raw_prompt": "not permitted"}),
            },
        )
        assert recover_integrity_envelope(root, "sensitive.json") == ("inconclusive", None)
    finally:
        for path in sorted(root.root.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            else:
                path.rmdir()
        root.root.rmdir()


def test_safe_temp_root_rejects_escape(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    root = SafeTrialTempRoot.create(prefix="ldvh-rule-read-test-", repository_root=repository)
    try:
        with pytest.raises(TrialMeasurementError, match="traversal-free"):
            root.write_json("../escape.json", {"x": 1})
        with pytest.raises(TrialMeasurementError, match="newly created"):
            root.write_json("result.json", {"x": 1})
            root.write_json("result.json", {"x": 2})
    finally:
        for path in sorted(root.root.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            else:
                path.rmdir()
        root.root.rmdir()
