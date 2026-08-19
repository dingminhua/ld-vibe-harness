"""Source-complete v7 knowledge-activation fixed-mechanism helpers.

v7 is a two-phase experiment on the LDVH knowledge-activation trigger
boundaries:

- Phase 1 evaluates and freezes the Study recall mechanism as
  "related-to relationship navigation + F2 index visibility + F3 on-demand
  progressive reading, no trigger decision".  When the evaluation passes the
  mechanism is frozen as a normative baseline with regression guards (contract
  tests, relationship-graph integrity, behavior-snapshot replay, standard
  pytest auto-discovery); Study research then stops.
- Phase 2 evaluates per-family differentiated triggering for ADR/Pitfall
  (ADR = signal hit + light exclusion; Pitfall = signal + symptom/risk
  anchor), repairing the v6 trigger-precision <-> activation-quality
  trade-off so both metrics meet their thresholds at once.

This module owns the v7 protocol closed-set validation and (later) the
phase-2 differentiated gateway primitives.  It reuses the frozen v6 task/gold
set read-only and never writes production F2 projection.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ldvh.testing.helper_interaction_factorial import paired_estimate  # noqa: F401 (reused by trial)
from ldvh.testing.knowledge_precheck_v2 import (
    KnowledgePrecheckV2Error,
    bytes_sha256,
    logical_line_count,
)
from ldvh.testing.knowledge_precheck_v3 import (
    ALLOWED_KNOWLEDGE_OPERATIONS,
    CASE_KINDS,
    MAX_MEMBER_LAUNCHES,
    MAX_PAIR_ATTEMPTS,
    MAX_REPLACEMENTS,
    MAX_SCORER_CONTEXTS,
    POLICY_MAX_BYTES,
    POLICY_MAX_LINES,
    RETAINED_PAIR_TARGET,
    RUN_TIMEOUT_SECONDS,
    TASK_FAMILIES,
    TECHNICAL_EXCLUSION_CODES,
    TOTAL_TIMEOUT_SECONDS,
)

SCHEMA_VERSION = "ldvh-knowledge-precheck-v7/1"
EVIDENCE_SCHEMA_VERSION = "ldvh-knowledge-precheck-v7-evidence/1"
CONDITIONS = ("calibration-baseline", "calibration-enhanced")
STUDY_FIXED_MECHANISM = (
    "no-trigger + related-to relationship navigation + F2 index visibility + "
    "F3 on-demand progressive reading"
)
_ADR_PER_FAMILY_THRESHOLDS = {
    "adr_missed_detection": 2,
    "adr_correct_activation": "3/3",
}
_PITFALL_PER_FAMILY_THRESHOLDS = {
    "trigger_correct": "4/6",
    "unnecessary_f2": 2,
}
_OVERALL_THRESHOLDS = {
    "trigger_correct": 12,
    "unnecessary_f2": 6,
    "correct_activation_rate": "6/9",
}
_PROTOCOL_POLICY_FIELDS = frozenset({"content", "bytes", "lines", "sha256"})
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def _hex64(value: object, code: str, problems: list[str]) -> None:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        problems.append(code)


def _one_line(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_v7_protocol(protocol: Mapping[str, Any]) -> tuple[str, ...]:
    """Return stable v7 protocol problem codes; an empty tuple means valid."""
    problems: list[str] = []
    if protocol.get("schema_version") != SCHEMA_VERSION:
        problems.append("schema-version")
    if protocol.get("conditions") != list(CONDITIONS):
        problems.append("conditions")
    if protocol.get("allowed_knowledge_operations") != list(ALLOWED_KNOWLEDGE_OPERATIONS):
        problems.append("allowed-knowledge-operations")
    if protocol.get("ceilings") != {
        "retained_pair_target": RETAINED_PAIR_TARGET,
        "maximum_pair_attempts": MAX_PAIR_ATTEMPTS,
        "maximum_replacements": MAX_REPLACEMENTS,
        "maximum_member_launches": MAX_MEMBER_LAUNCHES,
        "maximum_scorer_contexts": MAX_SCORER_CONTEXTS,
        "run_timeout_seconds": RUN_TIMEOUT_SECONDS,
        "total_timeout_seconds": TOTAL_TIMEOUT_SECONDS,
        "same_arm_retries": 0,
    }:
        problems.append("ceilings")

    phases = protocol.get("phases")
    expected_phases = {"phase1_study_evaluation", "phase2_adr_pitfall_differentiation"}
    if not isinstance(phases, Mapping) or set(phases) != expected_phases:
        problems.append("phases")
    else:
        if not isinstance(phases.get("phase1_study_evaluation"), Mapping):
            problems.append("phase1")
        else:
            phase1_metrics = phases["phase1_study_evaluation"].get("metrics")
            if not isinstance(phase1_metrics, Mapping) or set(phase1_metrics) != {
                "study_discovery_rate",
                "study_application_rate",
                "study_interference_rate",
            }:
                problems.append("phase1-metrics")
        if not isinstance(phases.get("phase2_adr_pitfall_differentiation"), Mapping):
            problems.append("phase2")

    policies = protocol.get("policies")
    if not isinstance(policies, Mapping) or set(policies) != set(CONDITIONS):
        problems.append("policies")
    else:
        for condition in CONDITIONS:
            policy = policies.get(condition)
            if not isinstance(policy, Mapping) or set(policy) != _PROTOCOL_POLICY_FIELDS:
                problems.append(f"policy-fields:{condition}")
                continue
            content = policy.get("content")
            if not isinstance(content, str) or not content.strip():
                problems.append(f"policy-content:{condition}")
                continue
            measured_bytes = len(content.encode("utf-8"))
            measured_lines = logical_line_count(content)
            if policy.get("bytes") != measured_bytes or policy.get("lines") != measured_lines:
                problems.append(f"policy-measurement:{condition}")
            if policy.get("sha256") != bytes_sha256(content.encode("utf-8")):
                problems.append(f"policy-hash:{condition}")
            if measured_bytes > POLICY_MAX_BYTES or measured_lines > POLICY_MAX_LINES:
                problems.append(f"policy-capacity:{condition}")

    tasks = protocol.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != RETAINED_PAIR_TARGET:
        problems.append("task-count")
        tasks = []
    pair_ids: list[str] = []
    family_case_counts: Counter[tuple[object, object]] = Counter()
    for index, task in enumerate(tasks):
        if not isinstance(task, Mapping):
            problems.append(f"task-shape:{index}")
            continue
        family = task.get("family")
        case_kind = task.get("case_kind")
        if family not in TASK_FAMILIES or case_kind not in CASE_KINDS:
            problems.append(f"task-fields:{index}")
            continue
        family_case_counts[(family, case_kind)] += 1
        pair_id = task.get("pair_id")
        if not (isinstance(pair_id, str) and pair_id.strip()):
            problems.append(f"task-pair-id:{index}")
        else:
            pair_ids.append(str(pair_id))
        gold = task.get("gold")
        if not isinstance(gold, Mapping):
            problems.append(f"task-gold:{index}")
            continue
        if gold.get("expected_f2_family") is not None and gold.get("expected_f2_family") not in TASK_FAMILIES:
            problems.append(f"gold-f2-family:{index}")
        if not isinstance(gold.get("expected_f2_trigger"), bool):
            problems.append(f"gold-f2-trigger:{index}")
        if not isinstance(gold.get("expected_f3_allow_set"), list):
            problems.append(f"gold-f3-allow:{index}")
    if len(pair_ids) != len(set(pair_ids)):
        problems.append("task-pair-id-dup")
    for family in TASK_FAMILIES:
        if family_case_counts[(family, "exact-positive")] != 2:
            problems.append(f"family-case-balance:{family}")
        for kind in CASE_KINDS:
            if kind == "exact-positive":
                continue
            if family_case_counts[(family, kind)] != 1:
                problems.append(f"family-case-balance:{family}:{kind}")

    thresholds = protocol.get("adoption_thresholds")
    if not isinstance(thresholds, Mapping) or not thresholds:
        problems.append("adoption-thresholds")

    edge_rules = protocol.get("edge_case_rules")
    if not isinstance(edge_rules, Mapping) or not edge_rules:
        problems.append("edge-case-rules")

    return tuple(problems)


def read_frozen_protocol(path: Path) -> dict[str, Any]:
    """Load and validate the frozen v7 protocol, failing closed on drift."""
    protocol = json.loads(path.read_text(encoding="utf-8"))
    problems = validate_v7_protocol(protocol)
    if problems:
        raise KnowledgePrecheckV2Error("v7 protocol closed-set invalid: " + ", ".join(problems))
    return protocol


# --- v7 per-family differentiated trigger decision ---------------------------
#
# v7 phase 2 evaluates per-family trigger boundaries on the frozen v6 task/gold
# set.  The gateway trigger decision is mechanism-driven (not a free model
# judgment): each family applies its own differentiated rule, and Study is a
# fixed no-trigger mechanism.  These helpers are pure and deterministically
# testable; the experiment wires them to the frozen protocol policy texts.

_V7_TRIGGER_RESPONSE_FIELDS = frozenset(
    {
        "triggered",
        "trigger_family",
        "positive_condition_codes",
        "veto_condition_codes",
    }
)


class KnowledgePrecheckV7Error(ValueError):
    """A v7 protocol/gateway invariant is violated."""


def _one_line(value: object, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KnowledgePrecheckV7Error(f"{code} must be a non-empty string")
    return value


def _closed_mapping(value: Mapping[str, Any], fields: frozenset[str], label: str) -> None:
    if set(value) != fields:
        raise KnowledgePrecheckV7Error(f"{label} fields are not closed")


def validate_v7_trigger_response(response: Mapping[str, Any], family: str) -> None:
    """Validate one v7 trigger response against the family's closed shape."""
    _closed_mapping(response, _V7_TRIGGER_RESPONSE_FIELDS, "member trigger response")
    triggered = response.get("triggered")
    if type(triggered) is not bool:
        raise KnowledgePrecheckV7Error("triggered must be boolean")
    trigger_family = response.get("trigger_family")
    if (triggered and trigger_family != family) or (not triggered and trigger_family is not None):
        raise KnowledgePrecheckV7Error("trigger family is inconsistent")
    positives = _unique_strings(response.get("positive_condition_codes"), "positive_condition_codes")
    vetoes = _unique_strings(response.get("veto_condition_codes"), "veto_condition_codes")
    if triggered and (not positives or vetoes):
        raise KnowledgePrecheckV7Error("a positive trigger needs reasons and no veto")
    if not triggered and positives and not vetoes:
        raise KnowledgePrecheckV7Error("a vetoed positive signal must name a veto")


def _unique_strings(value: object, code: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise KnowledgePrecheckV7Error(f"{code} must be an array")
    if not all(isinstance(item, str) and item for item in value):
        raise KnowledgePrecheckV7Error(f"{code} must be non-empty strings")
    if len(set(value)) != len(value):
        raise KnowledgePrecheckV7Error(f"{code} must not repeat")
    return tuple(value)


# Family-level trigger signal keywords (frozen from the v5/v6 signal words).
_ADR_SIGNAL_WORDS = (
    "架构", "模型", "接口", "运行时", "规则", "规范", "契约", "决策", "边界",
    "spec", "contract", "decision", "architecture", "interface", "runtime",
    "术语", "标识", "验收", "cas", "中文", "诊断", "字段", "分流", "顺序", "变更",
)
_PITFALL_SIGNAL_WORDS = (
    "症状", "失败", "报错", "异常", "故障", "风险", "排查", "安装", "hook",
    "网络", "配置", "超时", "symptom", "failure", "error", "risk", "install",
    "config", "timeout", "未加载", "契约", "入口", "参数", "目录", "调用",
)


def _signal_hit(family: str, text: str) -> bool:
    if family == "study":
        return False  # Study is a fixed no-trigger mechanism; no signal decision.
    lowered = text.lower()
    words = _ADR_SIGNAL_WORDS if family == "adr" else _PITFALL_SIGNAL_WORDS
    return any(word in lowered for word in words)


def _adr_light_exclusion(text: str) -> tuple[bool, tuple[str, ...]]:
    """ADR light exclusion: only suppress pure-fixture / pure-implementation /
    historical-ADR-not-current-authority.  Never suppress a future-interface
    change with no concrete decision (f2-no-f3 stays triggered)."""
    exclusions: list[str] = []
    if ("只有测试 fixture" in text or ("fixture" in text and "断言旧行为" in text)) and ("规则缺口" not in text):
        exclusions.append("pure-fixture-deviation")
    elif ("实现符合" in text) and ("规则缺口" not in text and "改 Specs" not in text):
        exclusions.append("pure-implementation-deviation")
    if (
        "历史 ADR" in text or "历史决策" in text or "套用旧决定" in text
    ) and ("当前契约" in text or "当前规则" in text):
        exclusions.append("historical-adr-not-current-authority")
    return bool(exclusions), tuple(exclusions)


def _pitfall_symptom_risk_anchor(text: str) -> tuple[bool, tuple[str, ...]]:
    """Pitfall anchor: an OBSERVED symptom (already happening, needs
    troubleshooting) OR a RISK-EXECUTION step (an operation that will be
    performed and has known pitfalls).  Pure hypothetical future adoption with
    no current executable step does not anchor.  Explicit negation of symptoms
    (\"没有...症状\" / \"无...症状\") or of risk operations (\"没有技能安装...\")
    suppresses the corresponding anchor."""
    anchors: list[str] = []
    observed_negated = ("没有" in text or "无" in text) and "症状" in text
    observed_symptom_words = (
        "报错", "失败", "超时", "missing", "配置缺失", "config missing", "返回", "run failed", "异常",
    )
    if not observed_negated and any(word in text for word in observed_symptom_words):
        anchors.append("observed-symptom")
    risk_negated = "没有" in text and any(
        word in text for word in ("技能安装", "安装", "Hook", "环境接入", "接入")
    )
    if not risk_negated and any(
        word in text
        for word in ("安装", "调用", "配置", "部署", "接入", "迁移", "install", "invoke", "deploy", "retry")
    ):
        anchors.append("risk-execution")
    if "尚未" in text and "未来" in text:
        return False, ()
    if observed_negated and "没有" in text:
        # 显式否定症状且无当前执行动作（如 P4：只有 Controller 契约与测试核对）
        if not anchors:
            return False, ()
    return bool(anchors), tuple(anchors)


def evaluate_v7_trigger(
    family: str,
    user_task: str,
    condition: str,
) -> dict[str, Any]:
    """Evaluate one v7 trigger decision deterministically.

    calibration-baseline follows the v5 wide-trigger recall-first policy
    (signal word hit, no veto).  calibration-enhanced applies the per-family
    differentiated boundary; Study is always a fixed no-trigger mechanism.
    Returns a closed v7 trigger response.
    """
    if family not in TASK_FAMILIES:
        raise KnowledgePrecheckV7Error(f"unknown family: {family}")
    if condition not in CONDITIONS:
        raise KnowledgePrecheckV7Error(f"unknown condition: {condition}")

    if family == "study":
        return {
            "triggered": False,
            "trigger_family": None,
            "positive_condition_codes": [],
            "veto_condition_codes": [],
        }

    if condition == "calibration-baseline":
        triggered = _signal_hit(family, user_task)
        return {
            "triggered": triggered,
            "trigger_family": family if triggered else None,
            "positive_condition_codes": ["signal-hit"] if triggered else [],
            "veto_condition_codes": [],
        }

    # calibration-enhanced: per-family differentiated boundary.
    signal = _signal_hit(family, user_task)
    if not signal:
        return {
            "triggered": False,
            "trigger_family": None,
            "positive_condition_codes": [],
            "veto_condition_codes": [],
        }
    if family == "adr":
        excluded, codes = _adr_light_exclusion(user_task)
        if excluded:
            return {
                "triggered": False,
                "trigger_family": None,
                "positive_condition_codes": ["signal-hit"],
                "veto_condition_codes": list(codes),
            }
        return {
            "triggered": True,
            "trigger_family": family,
            "positive_condition_codes": ["signal-hit"],
            "veto_condition_codes": [],
        }
    # pitfall
    anchored, codes = _pitfall_symptom_risk_anchor(user_task)
    if not anchored:
        return {
            "triggered": False,
            "trigger_family": None,
            "positive_condition_codes": ["signal-hit"],
            "veto_condition_codes": ["no-symptom-risk-anchor"],
        }
    return {
        "triggered": True,
        "trigger_family": family,
        "positive_condition_codes": ["signal-hit", *codes],
        "veto_condition_codes": [],
    }


def build_v7_trigger_trace(
    response: Mapping[str, Any],
    packet: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    """Build and validate a v7 trigger trace bound to one packet."""
    validate_v7_trigger_response(response, str(packet["family"]))
    trace = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "attempt_id": packet["attempt_id"],
        "pair_id": packet["pair_id"],
        "condition": packet.get("condition"),
        "family": packet["family"],
        **response,
    }
    if protocol is not None and trace.get("condition") not in CONDITIONS:
        raise KnowledgePrecheckV7Error("trigger trace condition is not frozen")
    validate_v7_trigger_response({field: trace[field] for field in _V7_TRIGGER_RESPONSE_FIELDS}, str(packet["family"]))
    return trace


__all__ = [
    "ALLOWED_KNOWLEDGE_OPERATIONS",
    "CASE_KINDS",
    "CONDITIONS",
    "EVIDENCE_SCHEMA_VERSION",
    "KnowledgePrecheckV7Error",
    "MAX_MEMBER_LAUNCHES",
    "MAX_PAIR_ATTEMPTS",
    "MAX_REPLACEMENTS",
    "MAX_SCORER_CONTEXTS",
    "RETAINED_PAIR_TARGET",
    "RUN_TIMEOUT_SECONDS",
    "SCHEMA_VERSION",
    "STUDY_FIXED_MECHANISM",
    "TASK_FAMILIES",
    "TECHNICAL_EXCLUSION_CODES",
    "TOTAL_TIMEOUT_SECONDS",
    "build_v7_trigger_trace",
    "evaluate_v7_trigger",
    "read_frozen_protocol",
    "validate_v7_trigger_response",
    "validate_v7_protocol",
]
