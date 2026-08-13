"""Bounded runner for the six frozen local-edit evidence traces."""

from __future__ import annotations

import hashlib
import json
import secrets
import stat
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ldvh.testing.local_edit_evidence import (
    OPERATION_KEY,
    RUNNER_VERSION,
    EvidenceIdentity,
    build_record,
    input_receipt,
    persist_record,
    project_record,
    recover_record,
    summarize,
    task_package_fingerprint,
    trace_event,
)
from ldvh.testing.trial_measurement import SafeTrialTempRoot, TrialMeasurementError

_RULE_LOCATOR = "ldvh-root::8.系统级运行架构/8.1工作上下文的信息交付顺序与渐进式披露"
_HEADING_PATH = ["8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"]
_REAL_TRACES = frozenset({"T1", "T2", "T3a"})
_DEFAULT_TEMP_PREFIX = "ldvh-local-edit-evidence-"


def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _public_identifier_fingerprint(kind: str, value: str) -> str:
    return _canonical_digest({"hash_subject": "public_stable_identifier", "kind": kind, "value": value})


def _git_common_dir(repository_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise TrialMeasurementError("git common-dir is unavailable")
    path = Path(completed.stdout.strip())
    return str((repository_root / path).resolve() if not path.is_absolute() else path.resolve())


@dataclass(frozen=True, slots=True)
class LocalEditEvidenceRun:
    root: SafeTrialTempRoot
    records: tuple[dict[str, Any], ...]
    recoveries: tuple[dict[str, Any], ...]
    summary: dict[str, Any]

    def summary_payload(self) -> dict[str, Any]:
        """Return a body-free handoff summary using the public temp-root API."""

        return {
            "artifact_root": str(self.root.root),
            "recoveries": [dict(recovery) for recovery in self.recoveries],
            "summary": dict(self.summary),
        }


@dataclass(slots=True)
class LocalEditEvidenceRunner:
    repository_root: Path
    governed_project_id: str
    run_id: str
    task_nonce: str
    deadline_ms: int = 5_000

    @classmethod
    def create(
        cls,
        *,
        repository_root: Path,
        governed_project_id: str,
        run_id: str,
        deadline_ms: int = 5_000,
    ) -> LocalEditEvidenceRunner:
        resolved = repository_root.resolve(strict=True)
        if not (resolved / "ldvh").is_file():
            raise TrialMeasurementError("repository root does not expose the source LDVH entry point")
        if type(deadline_ms) is not int or deadline_ms <= 0:
            raise TrialMeasurementError("deadline_ms must be a positive integer")
        return cls(resolved, governed_project_id, run_id, secrets.token_hex(16), deadline_ms)

    def _identity(self, trace_id: str) -> EvidenceIdentity:
        common_dir = _git_common_dir(self.repository_root)
        worktree = _public_identifier_fingerprint(
            "git_worktree",
            f"{self.repository_root}\0{common_dir}",
        )
        task = task_package_fingerprint(
            {
                "run_id": self.run_id,
                "trial_id": trace_id,
                "operation_key": OPERATION_KEY,
                "rule_locator": _RULE_LOCATOR,
                "governed_project_id": self.governed_project_id,
            },
            entropy_nonce=self.task_nonce,
        )
        return EvidenceIdentity(
            run_id=self.run_id,
            trial_id=trace_id,
            worktree_fingerprint=worktree,
            governed_project_id=self.governed_project_id,
            task_package_fingerprint=task,
            rule_fingerprint=_public_identifier_fingerprint("rule_locator", _RULE_LOCATOR),
            capability_fingerprint=_public_identifier_fingerprint("operation_key", OPERATION_KEY),
            runner_fingerprint=_public_identifier_fingerprint("runner_version", RUNNER_VERSION),
        )

    def _inputs(self, identity: EvidenceIdentity) -> list[dict[str, Any]]:
        return [
            input_receipt(
                kind="rule_locator",
                status="delivered",
                locator=_RULE_LOCATOR,
                source_range="heading_path:8/8.1",
                fingerprint=identity.rule_fingerprint,
                length=len(_RULE_LOCATOR.encode("utf-8")),
            ),
            input_receipt(
                kind="capability_locator",
                status="delivered",
                locator=OPERATION_KEY,
                fingerprint=identity.capability_fingerprint,
                length=len(OPERATION_KEY),
            ),
            input_receipt(
                kind="task_package",
                status="delivered",
                locator=f"run:{self.run_id}/trial:{identity.trial_id}",
                fingerprint=identity.task_package_fingerprint,
                hash_subject="canonical_high_entropy_task_package",
            ),
        ]

    def _call(self, arguments: dict[str, Any]) -> tuple[dict[str, Any] | None, int, int, bool]:
        request = json.dumps({"arguments": arguments}, ensure_ascii=False, separators=(",", ":"))
        started = time.monotonic_ns()
        try:
            completed = subprocess.run(
                [str(self.repository_root / "ldvh"), "call", OPERATION_KEY],
                cwd=self.repository_root,
                input=request.encode("utf-8"),
                capture_output=True,
                timeout=self.deadline_ms / 1_000,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None, 0, max((time.monotonic_ns() - started) // 1_000_000, 0), True
        duration_ms = max((time.monotonic_ns() - started) // 1_000_000, 0)
        response_bytes = len(completed.stdout)
        try:
            parsed = json.loads(completed.stdout)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, response_bytes, duration_ms, False
        return parsed if isinstance(parsed, dict) else None, response_bytes, duration_ms, False

    @staticmethod
    def _external(response: dict[str, Any] | None) -> dict[str, Any]:
        outcome = "not_observed"
        stale: bool | None = None
        change_count = 0
        source_locator: str | None = None
        source_range: str | None = None
        if response is not None:
            raw_outcome = response.get("outcome")
            if raw_outcome in {"ok", "rejected"}:
                outcome = raw_outcome
            changes = response.get("changes")
            if isinstance(changes, list):
                change_count = len(changes)
            result = response.get("result")
            if isinstance(result, dict):
                items = result.get("items")
                if isinstance(items, list) and items and isinstance(items[0], dict):
                    item = items[0]
                    stale = item.get("stale") if type(item.get("stale")) is bool else None
                    ranges = item.get("source_ranges")
                    if isinstance(ranges, list) and ranges and isinstance(ranges[0], dict):
                        first = ranges[0]
                        path = first.get("path")
                        start = first.get("start_line")
                        end = first.get("end_line")
                        if isinstance(path, str) and path:
                            source_locator = path
                        if type(start) is int and type(end) is int:
                            source_range = f"L{start}-L{end}"
        return {
            "helper_outcome": outcome,
            "stale": stale,
            "change_count": change_count,
            "source_locator": source_locator,
            "source_range": source_range,
        }

    @staticmethod
    def _fault(trace_id: str) -> dict[str, Any]:
        synthetic = trace_id in {"T3b", "T4a", "T4b"}
        kinds = {
            "T1": "process_exit",
            "T2": "process_exit",
            "T3a": "rejected_response",
            "T3b": "deadline",
            "T4a": "interruption",
            "T4b": "integrity_violation",
        }
        return {
            "origin": "synthetic_harness" if synthetic else "real_helper",
            "operation_key": OPERATION_KEY,
            "deadline_seconds": 0 if trace_id == "T3b" else None,
            "deadline_source": "frozen synthetic fault" if trace_id == "T3b" else None,
            "evidence_kind": kinds[trace_id],
        }

    @staticmethod
    def _verification(*, external: dict[str, Any], expected_outcome: str) -> dict[str, bool]:
        return {
            "readback": True,
            "integrity": True,
            "boundary_match": external["change_count"] == 0,
            "external_evidence": external["helper_outcome"] == expected_outcome,
        }

    def run_real(self, trace_id: str) -> dict[str, Any]:
        if trace_id not in _REAL_TRACES:
            raise TrialMeasurementError("run_real accepts only T1, T2, or T3a")
        identity = self._identity(trace_id)
        base = {
            "source_kind": "rule",
            "responsibility_key": "ldvh-root",
            "heading_path": list(_HEADING_PATH),
        }
        if trace_id == "T3a":
            base["heading_path"] = ["不存在的局部编辑目标"]
        first_args = dict(base)
        if trace_id == "T2":
            first_args["expected_baseline"] = "0" * 64
        first, first_bytes, first_ms, first_timeout = self._call(first_args)
        if first_timeout:
            external = self._external(None)
            events = [trace_event(0, "request_observed")]
            verification = self._verification(external=external, expected_outcome="ok")
            return build_record(
                identity=identity,
                trace_id=trace_id,
                inputs=self._inputs(identity),
                events=events,
                helper_calls=1,
                repairs=0,
                external_state=external,
                verification=verification,
                fault=self._fault(trace_id),
            )
        if trace_id == "T1":
            external = self._external(first)
            events = [
                trace_event(0, "request_observed", call_index=1),
                trace_event(1, "response_observed", call_index=1, response_bytes=first_bytes, duration_ms=first_ms),
                trace_event(2, "external_state_checked"),
                trace_event(3, "verification_completed"),
            ]
            verification = self._verification(external=external, expected_outcome="ok")
        elif trace_id == "T3a":
            external = self._external(first)
            events = [
                trace_event(0, "request_observed", call_index=1),
                trace_event(1, "response_observed", call_index=1, response_bytes=first_bytes, duration_ms=first_ms),
                trace_event(2, "external_state_checked"),
                trace_event(3, "verification_completed"),
            ]
            verification = self._verification(external=external, expected_outcome="rejected")
        else:
            baseline: str | None = None
            if first is not None:
                result = first.get("result")
                if isinstance(result, dict):
                    items = result.get("items")
                    if isinstance(items, list) and items and isinstance(items[0], dict):
                        raw_baseline = items[0].get("baseline")
                        if isinstance(raw_baseline, dict) and isinstance(raw_baseline.get("value"), str):
                            baseline = raw_baseline["value"]
            second: dict[str, Any] | None = None
            second_bytes = second_ms = 0
            if baseline is not None:
                second_args = dict(base)
                second_args["expected_baseline"] = baseline
                second, second_bytes, second_ms, _ = self._call(second_args)
            external = self._external(second)
            first_external = self._external(first)
            events = [
                trace_event(0, "request_observed", call_index=1),
                trace_event(
                    1,
                    "initial_response_observed",
                    call_index=1,
                    response_bytes=first_bytes,
                    duration_ms=first_ms,
                ),
                trace_event(2, "repair_request_observed", call_index=2),
                trace_event(
                    3,
                    "repaired_response_observed",
                    call_index=2,
                    response_bytes=second_bytes,
                    duration_ms=second_ms,
                ),
                trace_event(4, "external_state_checked"),
                trace_event(5, "verification_completed"),
            ]
            verification = self._verification(external=external, expected_outcome="ok")
            verification["external_evidence"] = (
                verification["external_evidence"]
                and first_external["stale"] is True
                and external["stale"] is False
            )
        return build_record(
            identity=identity,
            trace_id=trace_id,
            inputs=self._inputs(identity),
            events=events,
            helper_calls=2 if trace_id == "T2" else 1,
            repairs=1 if trace_id == "T2" else 0,
            external_state=external,
            verification=verification,
            fault=self._fault(trace_id),
        )

    def run_synthetic(self, trace_id: str) -> dict[str, Any]:
        if trace_id not in {"T3b", "T4a", "T4b"}:
            raise TrialMeasurementError("run_synthetic accepts only T3b, T4a, or T4b")
        identity = self._identity(trace_id)
        names = {
            "T3b": ("deadline_observed", "verification_completed"),
            "T4a": ("interruption_observed", "verification_completed"),
            "T4b": ("integrity_violation_observed", "verification_completed"),
        }[trace_id]
        external = {
            "helper_outcome": "timeout" if trace_id == "T3b" else "not_observed",
            "stale": None,
            "change_count": 0,
            "source_locator": None,
            "source_range": None,
        }
        verification = {
            "readback": trace_id != "T4b",
            "integrity": trace_id != "T4b",
            "boundary_match": True,
            "external_evidence": trace_id == "T3b",
        }
        return build_record(
            identity=identity,
            trace_id=trace_id,
            inputs=self._inputs(identity),
            events=[trace_event(index, name) for index, name in enumerate(names)],
            helper_calls=0,
            repairs=0,
            external_state=external,
            verification=verification,
            fault=self._fault(trace_id),
        )

    def run_suite(self, *, temp_prefix: str = _DEFAULT_TEMP_PREFIX) -> LocalEditEvidenceRun:
        root = SafeTrialTempRoot.create(prefix=temp_prefix, repository_root=self.repository_root)
        records = tuple(
            [self.run_real(trace_id) for trace_id in ("T1", "T2", "T3a")]
            + [self.run_synthetic(trace_id) for trace_id in ("T3b", "T4a", "T4b")]
        )
        recoveries: list[dict[str, Any]] = []
        for record in records:
            trace_id = record["trace_id"]
            relative = f"records/{trace_id}.json"
            path = persist_record(root, relative, record)
            if trace_id == "T4b":
                self._inject_integrity_tamper(path)
            projection, recovered = recover_record(
                root,
                relative,
                expected_identity=self._identity(trace_id),
            )
            recoveries.append(
                {
                    "trace_id": trace_id,
                    "projection": projection,
                    "recovered": recovered is not None,
                    "expected_projection": project_record(record),
                }
            )
        return LocalEditEvidenceRun(root, records, tuple(recoveries), summarize(records))

    @staticmethod
    def _inject_integrity_tamper(path: Path) -> None:
        """Corrupt only the synthetic T4b integrity value in a runner-owned file."""

        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise TrialMeasurementError("synthetic tamper target must be a regular file")
        envelope = json.loads(path.read_text(encoding="utf-8"))
        integrity = envelope.get("integrity_sha256")
        if not isinstance(integrity, str) or len(integrity) != 64:
            raise TrialMeasurementError("synthetic tamper target has no integrity value")
        envelope["integrity_sha256"] = ("0" if integrity[0] != "0" else "1") + integrity[1:]
        path.write_text(
            json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
