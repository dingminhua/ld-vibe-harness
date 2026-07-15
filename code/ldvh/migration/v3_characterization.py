"""Deterministic, decision-free characterization of the frozen V3 fact sources.

The artifact produced here is not a semantic migration ledger.  It records
only reproducible source shapes and keeps every V4 decision explicitly
undecided.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from ldvh.migration.v3_baseline import SNAPSHOT_COMMIT, SNAPSHOT_TREE, verify_v3_baseline

ARTIFACT_KIND = "v3-source-characterization"
BASELINE_RELATIVE_PATH = "migration/v3-facts/baseline.json"
CHARACTERIZATION_RELATIVE_PATH = "migration/v3-facts/source-characterization.json"
_FACT_ID = re.compile(r"(spark|workcase|study|pitfall|adr)-[0-9]{4,}\Z")
_FACT_ID_SEARCH = re.compile(r"(spark|workcase|study|pitfall|adr)-[0-9]{4,}")
_DATE_ONLY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_OFFSET_DATETIME = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z"
)
_NAIVE_DATETIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?\Z")
_URL = re.compile(r"https?://", re.IGNORECASE)
_REFERENCE_NAMES = {
    "resolved_to",
    "source_objects",
    "source_sparks",
    "related_workcases",
    "related_adrs",
    "related_studies",
    "related_sparks",
    "related_pitfalls",
    "related_docs",
    "related_rules",
    "workflow_ref",
    "raw_output_ref",
}
_ENTRY_KEYS = {
    "source_key",
    "source_sha256",
    "top_level_fields",
    "structure_counts",
    "time_observations",
    "reference_observations",
    "content_regions",
    "status_observation",
    "exact_title_collision_source_keys",
    "review_state",
    "target_identity",
    "target_type",
    "target_status",
    "split_merge",
}


@dataclass(frozen=True, slots=True)
class CharacterizationIssue:
    code: str
    summary: str
    source_key: str | None = None


@dataclass(frozen=True, slots=True)
class CharacterizationVerification:
    entry_count: int
    issues: tuple[CharacterizationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def _pointer_segment(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _join_pointer(parent: str, segment: str | int) -> str:
    encoded = str(segment) if isinstance(segment, int) else _pointer_segment(segment)
    return f"{parent}/{encoded}" if parent else f"/{encoded}"


def _json_kind(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "mapping"
    return "unrecognized"


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"legacy value is not JSON-compatible: {exc}") from exc


def _value_digest(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _empty(value: object) -> bool:
    return value == "" or value == [] or value == {}


def _walk(value: object, pointer: str = "", depth: int = 0):
    yield pointer, value, depth
    if isinstance(value, dict):
        for key in sorted(value):
            if not isinstance(key, str):
                raise ValueError("legacy mapping has a non-string key")
            yield from _walk(value[key], _join_pointer(pointer, key), depth + 1)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, _join_pointer(pointer, index), depth + 1)


def _time_key(name: str) -> bool:
    return name in {"created", "updated", "at"} or name.endswith("_at")


def _time_classification(value: object) -> tuple[str, list[str]]:
    if value is None:
        return "null", ["null-time-value"]
    if not isinstance(value, str):
        return "unrecognized", ["non-string-time-value"]
    if value == "":
        return "empty_string", ["empty-time-value"]
    if _DATE_ONLY.fullmatch(value):
        return "date_only", ["date-only-no-timezone"]
    if _OFFSET_DATETIME.fullmatch(value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "unrecognized", ["unrecognized-time-value"]
        if parsed.tzinfo is not None:
            return "offset_datetime", []
    if _NAIVE_DATETIME.fullmatch(value):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return "unrecognized", ["unrecognized-time-value"]
        if parsed.tzinfo is None:
            return "naive_datetime", ["missing-timezone"]
    return "unrecognized", ["unrecognized-time-value"]


def _is_reference_key(key: str, ancestors: tuple[str, ...]) -> bool:
    return (
        key.endswith("_refs")
        or key.endswith("_ref")
        or key.startswith("related_")
        or key in _REFERENCE_NAMES
        or (key == "ref" and "urls" in ancestors)
    )


def _reference_leaves(value: object, pointer: str):
    kind = _json_kind(value)
    if value is None or _empty(value) or kind not in {"mapping", "array"}:
        yield pointer, value
        return
    if isinstance(value, dict):
        for key in sorted(value):
            if not isinstance(key, str):
                raise ValueError("legacy reference mapping has a non-string key")
            yield from _reference_leaves(value[key], _join_pointer(pointer, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _reference_leaves(item, _join_pointer(pointer, index))


def _reference_classification(value: object) -> tuple[str, str | None]:
    if value is None:
        return "null", None
    if _empty(value):
        return "empty", None
    if not isinstance(value, str):
        return "opaque", None
    exact = _FACT_ID.fullmatch(value)
    if exact is not None:
        return "exact_fact_id", value
    if _URL.match(value):
        return "url", None
    embedded = _FACT_ID_SEARCH.search(value)
    if embedded is not None and ("/" in value or value.endswith((".md", ".yaml", ".yml"))):
        return "fact_path", embedded.group(0)
    if "/" in value or value.endswith((".md", ".yaml", ".yml")):
        return "document_path", None
    if "::" in value or "§" in value:
        return "rule_ref", None
    return "opaque", embedded.group(0) if embedded is not None else None


def _parse_source(path: Path, carrier: str) -> tuple[dict[str, Any], str | None]:
    text = path.read_text(encoding="utf-8")
    yaml_text = text
    body: str | None = None
    if carrier == "markdown":
        if not text.startswith("---\n"):
            raise ValueError(f"Study has no opening frontmatter: {path}")
        parts = text.split("---", 2)
        if len(parts) != 3:
            raise ValueError(f"Study has no closing frontmatter: {path}")
        yaml_text = parts[1]
        body = parts[2]
    loader = YAML(typ="safe")
    loaded = loader.load(yaml_text)
    if not isinstance(loaded, dict) or any(not isinstance(key, str) for key in loaded):
        raise ValueError(f"legacy frontmatter is not a string-keyed mapping: {path}")
    _canonical_json_bytes(loaded)
    return loaded, body


def _structure_counts(fields: dict[str, Any], body: str | None) -> dict[str, Any]:
    counts = Counter()
    maximum_depth = 0
    for _, value, depth in _walk(fields):
        kind = _json_kind(value)
        if kind == "mapping":
            counts["mapping"] += 1
        elif kind == "array":
            counts["array"] += 1
        elif kind == "null":
            counts["null"] += 1
        else:
            counts["scalar"] += 1
        maximum_depth = max(maximum_depth, depth)
    result: dict[str, Any] = {
        "mapping_node_count": counts["mapping"],
        "array_node_count": counts["array"],
        "scalar_node_count": counts["scalar"],
        "null_node_count": counts["null"],
        "maximum_depth": maximum_depth,
    }
    if body is not None:
        headings = re.findall(r"^(#{1,2})[ \t]+.+$", body, flags=re.MULTILINE)
        result["study_body"] = {
            "byte_count": len(body.encode("utf-8")),
            "character_count": len(body),
            "h1_count": headings.count("#"),
            "h2_count": headings.count("##"),
        }
    return result


def _study_regions(body: str) -> list[dict[str, Any]]:
    regions = [
        {
            "locator": "study-body",
            "legacy_structural_role": "study-body",
            "byte_count": len(body.encode("utf-8")),
            "character_count": len(body),
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        }
    ]
    matches = list(re.finditer(r"^(#{1,2})[ \t]+(.+)$", body, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        section = body[match.start() : end]
        line = body.count("\n", 0, match.start()) + 1
        level = len(match.group(1))
        regions.append(
            {
                "locator": f"study-body:H{level}:line-{line}",
                "legacy_structural_role": f"study-body-h{level}-section",
                "byte_count": len(section.encode("utf-8")),
                "character_count": len(section),
                "sha256": hashlib.sha256(section.encode("utf-8")).hexdigest(),
                "heading_text_sha256": hashlib.sha256(match.group(2).encode("utf-8")).hexdigest(),
            }
        )
    return regions


def _status_risks(source_type: str, status: str) -> list[str]:
    if source_type == "spark":
        return {
            "pending": ["v3-pending-not-v4-open"],
            "resolved": ["historical-terminal-review-required", "v3-resolved-not-v4-routed"],
            "discarded": ["historical-terminal-review-required", "v3-discarded-needs-current-exit-basis"],
        }.get(status, ["unknown-v3-status"])
    if source_type == "workcase":
        if status == "closed":
            return ["historical-terminal-review-required", "v3-closed-not-v4-closed"]
        return ["v3-workcase-phase-not-v4-phase"]
    if status == "active":
        return ["v3-active-not-automatically-current"]
    return ["unknown-v3-status"]


def _reference_observations(
    fields: dict[str, Any],
    source_key: str,
    baseline_keys: dict[str, str],
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []

    def visit(value: object, pointer: str, ancestors: tuple[str, ...]) -> None:
        if isinstance(value, dict):
            for key in sorted(value):
                if not isinstance(key, str):
                    raise ValueError("legacy mapping has a non-string key")
                child = value[key]
                child_pointer = _join_pointer(pointer, key)
                if _is_reference_key(key, ancestors):
                    for leaf_pointer, raw_value in _reference_leaves(child, child_pointer):
                        syntactic_class, candidate_id = _reference_classification(raw_value)
                        resolved = baseline_keys.get(candidate_id or "")
                        risk_codes: list[str] = []
                        if candidate_id is not None and resolved is None:
                            risk_codes.append("legacy-fact-target-not-in-baseline")
                        if resolved == source_key:
                            risk_codes.append("legacy-self-reference-candidate")
                        observation = {
                            "pointer": leaf_pointer,
                            "raw_kind": _json_kind(raw_value),
                            "raw_value_sha256": _value_digest(raw_value),
                            "raw_value_byte_count": len(_canonical_json_bytes(raw_value)),
                            "legacy_field_role": key,
                            "syntactic_class": syntactic_class,
                            "risk_codes": risk_codes,
                            "v4_relation_decision": "undecided",
                        }
                        if resolved is not None:
                            observation["resolved_baseline_source_key"] = resolved
                        observations.append(observation)
                else:
                    visit(child, child_pointer, (*ancestors, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, _join_pointer(pointer, index), ancestors)

    visit(fields, "", ())
    target_counts = Counter(
        observation.get("resolved_baseline_source_key")
        for observation in observations
        if observation.get("resolved_baseline_source_key") is not None
    )
    for observation in observations:
        target = observation.get("resolved_baseline_source_key")
        if target is not None and target_counts[target] > 1:
            observation["risk_codes"].append("duplicate-legacy-target-reference")
    observations.sort(key=lambda item: (item["pointer"], item["legacy_field_role"]))
    return observations


def _time_observations(fields: dict[str, Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []

    def visit(value: object, pointer: str) -> None:
        if isinstance(value, dict):
            for key in sorted(value):
                if not isinstance(key, str):
                    raise ValueError("legacy mapping has a non-string key")
                child = value[key]
                child_pointer = _join_pointer(pointer, key)
                if _time_key(key):
                    classification, risk_codes = _time_classification(child)
                    observations.append(
                        {
                            "pointer": child_pointer,
                            "raw_kind": _json_kind(child),
                            "raw_value_sha256": _value_digest(child),
                            "raw_value_byte_count": len(_canonical_json_bytes(child)),
                            "classification": classification,
                            "risk_codes": risk_codes,
                        }
                    )
                visit(child, child_pointer)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, _join_pointer(pointer, index))

    visit(fields, "")
    observations.sort(key=lambda item: item["pointer"])
    return observations


def _top_level_fields(fields: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source_pointer": _join_pointer("", key),
            "value_kind": _json_kind(fields[key]),
            "empty": _empty(fields[key]),
            "value_sha256": _value_digest(fields[key]),
        }
        for key in sorted(fields)
    ]


def _frontmatter_region(fields: dict[str, Any]) -> dict[str, Any]:
    canonical = _canonical_json_bytes(fields)
    return {
        "locator": "frontmatter",
        "legacy_structural_role": "frontmatter",
        "byte_count": len(canonical),
        "character_count": len(canonical.decode("utf-8")),
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }


def build_v3_source_characterization(repository_root: Path) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    baseline_path = repository_root / BASELINE_RELATIVE_PATH
    baseline_verification = verify_v3_baseline(repository_root, baseline_path)
    if not baseline_verification.valid:
        detail = "; ".join(issue.summary for issue in baseline_verification.issues)
        raise ValueError(f"V3 baseline is not valid: {detail}")
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes.decode("utf-8"))
    baseline_entries = baseline["entries"]
    baseline_keys = {entry["source_id"]: entry["source_key"] for entry in baseline_entries}
    parsed: list[tuple[dict[str, Any], dict[str, Any], str | None]] = []
    titles: dict[str, list[str]] = defaultdict(list)
    for baseline_entry in baseline_entries:
        fields, body = _parse_source(repository_root / baseline_entry["source_path"], baseline_entry["carrier"])
        if fields.get("id") != baseline_entry["source_id"]:
            raise ValueError(f"baseline/source id mismatch: {baseline_entry['source_key']}")
        parsed.append((baseline_entry, fields, body))
        title = fields.get("title")
        if isinstance(title, str):
            titles[title.strip()].append(baseline_entry["source_key"])

    entries: list[dict[str, Any]] = []
    for baseline_entry, fields, body in parsed:
        source_key = baseline_entry["source_key"]
        time_observations = _time_observations(fields)
        reference_observations = _reference_observations(fields, source_key, baseline_keys)
        content_regions = [_frontmatter_region(fields)]
        if body is not None:
            content_regions.extend(_study_regions(body))
        title = fields.get("title")
        collisions = (
            sorted(key for key in titles.get(title.strip(), []) if key != source_key) if isinstance(title, str) else []
        )
        entries.append(
            {
                "source_key": source_key,
                "source_sha256": baseline_entry["sha256"],
                "top_level_fields": _top_level_fields(fields),
                "structure_counts": _structure_counts(fields, body),
                "time_observations": time_observations,
                "reference_observations": reference_observations,
                "content_regions": content_regions,
                "status_observation": {
                    "source_type": baseline_entry["source_type"],
                    "source_status": baseline_entry["source_status"],
                    "mapping_rule": "no_mechanical_v4_mapping",
                    "risk_codes": _status_risks(baseline_entry["source_type"], baseline_entry["source_status"]),
                },
                "exact_title_collision_source_keys": collisions,
                "review_state": "not_started",
                "target_identity": "undecided",
                "target_type": "undecided",
                "target_status": "undecided",
                "split_merge": "undecided",
            }
        )
    entries.sort(key=lambda item: item["source_key"])
    time_classes = Counter(
        observation["classification"] for entry in entries for observation in entry["time_observations"]
    )
    reference_classes = Counter(
        observation["syntactic_class"] for entry in entries for observation in entry["reference_observations"]
    )
    observation_counts = {
        "top_level_field_count": sum(len(entry["top_level_fields"]) for entry in entries),
        "time_observation_count": sum(len(entry["time_observations"]) for entry in entries),
        "time_classification_counts": dict(sorted(time_classes.items())),
        "reference_observation_count": sum(len(entry["reference_observations"]) for entry in entries),
        "reference_classification_counts": dict(sorted(reference_classes.items())),
        "content_region_count": sum(len(entry["content_regions"]) for entry in entries),
        "exact_title_collision_pair_count": sum(len(entry["exact_title_collision_source_keys"]) for entry in entries)
        // 2,
    }
    return {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "baseline_binding": {
            "manifest_path": BASELINE_RELATIVE_PATH,
            "manifest_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
            "snapshot_commit": SNAPSHOT_COMMIT,
            "snapshot_tree": SNAPSHOT_TREE,
        },
        "entries": entries,
        "summary": {
            "entry_count": len(entries),
            "source_type_counts": baseline["expected_counts"],
            "source_status_counts": baseline["expected_statuses"],
            "mechanical_observation_counts": observation_counts,
            "semantic_reviewed_count": 0,
            "target_decided_count": 0,
        },
    }


def render_v3_source_characterization(repository_root: Path) -> str:
    return (
        json.dumps(build_v3_source_characterization(repository_root), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    )


def _fixed_decisions(entry: dict[str, Any]) -> bool:
    return (
        entry.get("review_state") == "not_started"
        and entry.get("target_identity") == "undecided"
        and entry.get("target_type") == "undecided"
        and entry.get("target_status") == "undecided"
        and entry.get("split_merge") == "undecided"
        and all(
            observation.get("v4_relation_decision") == "undecided"
            for observation in entry.get("reference_observations", [])
            if isinstance(observation, dict)
        )
    )


def verify_v3_source_characterization(
    repository_root: Path,
    artifact_path: Path,
) -> CharacterizationVerification:
    repository_root = repository_root.resolve()
    try:
        if artifact_path.is_symlink():
            raise ValueError("characterization artifact must not be a symbolic link")
        if not artifact_path.is_file():
            raise ValueError("characterization artifact must be a regular file")
        raw = artifact_path.read_bytes()
        text = raw.decode("utf-8")

        def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        loaded = json.loads(text, object_pairs_hook=unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return CharacterizationVerification(
            0,
            (CharacterizationIssue("artifact", f"cannot read characterization: {exc}"),),
        )
    issues: list[CharacterizationIssue] = []
    if not isinstance(loaded, dict):
        return CharacterizationVerification(
            0,
            (CharacterizationIssue("artifact", "characterization must be an object"),),
        )
    if set(loaded) != {"schema_version", "artifact_kind", "baseline_binding", "entries", "summary"}:
        issues.append(CharacterizationIssue("artifact", "top-level fields do not match the closed schema"))
    if loaded.get("schema_version") != 1 or loaded.get("artifact_kind") != ARTIFACT_KIND:
        issues.append(CharacterizationIssue("artifact", "schema_version or artifact_kind is invalid"))
    canonical = json.dumps(loaded, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if raw != canonical:
        issues.append(CharacterizationIssue("artifact", "bytes are not canonical JSON with one final LF"))
    entries = loaded.get("entries")
    entry_count = len(entries) if isinstance(entries, list) else 0
    if not isinstance(entries, list):
        issues.append(CharacterizationIssue("artifact", "entries must be an array"))
    else:
        keys = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or set(entry) != _ENTRY_KEYS:
                issues.append(CharacterizationIssue("entry", f"entry {index} has unknown or missing fields"))
                continue
            source_key = entry.get("source_key")
            if isinstance(source_key, str):
                keys.append(source_key)
            if not _fixed_decisions(entry):
                issues.append(
                    CharacterizationIssue(
                        "decision",
                        "semantic, target, split/merge, and V4 relation decisions must remain unstarted/undecided",
                        source_key if isinstance(source_key, str) else None,
                    )
                )
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            issues.append(CharacterizationIssue("coverage", "source keys must be sorted and unique"))
    summary = loaded.get("summary")
    if (
        not isinstance(summary, dict)
        or summary.get("semantic_reviewed_count") != 0
        or summary.get("target_decided_count") != 0
    ):
        issues.append(CharacterizationIssue("decision", "summary decision counts must both remain zero"))
    try:
        generated = build_v3_source_characterization(repository_root)
    except (OSError, ValueError) as exc:
        issues.append(CharacterizationIssue("source", str(exc)))
    else:
        if loaded != generated:
            issues.append(CharacterizationIssue("drift", "artifact differs from deterministic frozen-source rebuild"))
    return CharacterizationVerification(entry_count, tuple(issues))


__all__ = [
    "CharacterizationIssue",
    "CharacterizationVerification",
    "build_v3_source_characterization",
    "render_v3_source_characterization",
    "verify_v3_source_characterization",
]
