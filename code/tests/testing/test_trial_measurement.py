from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from ldvh.testing.trial_measurement import (
    TRIAL_SCHEMA_VERSION,
    ContractClaim,
    HelperResponseEvent,
    SafeTrialTempRoot,
    TrialMeasurementCollector,
    TrialMeasurementError,
    build_prompt_card,
    parse_trial_record,
    synthetic_trial,
    validate_trial_record,
)


def _collector() -> TrialMeasurementCollector:
    return TrialMeasurementCollector(
        trial_id="trial-01",
        task_package_hash="a" * 64,
        condition="candidate",
        runner_fingerprint="runner-1",
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
    assert record["first_legal"] is True
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
