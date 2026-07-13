from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.validation import validate_fact_object
from ldvh.specs.repository import inspect_repository

PROJECT_ROOT = Path(__file__).resolve().parents[3]
V3 = PROJECT_ROOT / "archive" / "v3" / "ldvh-base"


def _yaml(path: Path) -> dict[str, object]:
    loader = YAML(typ="safe")
    loaded = loader.load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def test_v3_study_urls_preserve_titles_and_purpose_without_restoring_urls_field(
    current_specs_repository: Path,
) -> None:
    source = V3 / "studies" / "study-0011-codex-worktree-subagent-thread-practices.md"
    text = source.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    loaded = _yaml_text(frontmatter)
    urls = loaded["urls"]

    assert isinstance(urls, list) and len(urls) == 14
    assert all(isinstance(item, dict) and {"ref", "title", "summary"} <= set(item) for item in urls)
    dispositions = [
        {
            "ref": item["ref"],
            "ref_target": "source_refs/evidence_refs[].locator",
            "title_target": "Markdown link display text",
            "summary_target": "输入、方法与观察边界/关键发现/结论与限制",
            "disposition": "mapped",
        }
        for item in urls
        if isinstance(item, dict)
    ]
    assert len(dispositions) == len(urls)
    assert all(record["disposition"] == "mapped" and all(record.values()) for record in dispositions)
    study_fields = {
        field.path
        for field in project_fact_schemas(inspect_repository(current_specs_repository))["study"].direct_fields
    }
    assert "urls" not in study_fields
    assert {"source_refs", "evidence_refs", "research_question", "abstract"} <= study_fields


def _yaml_text(text: str) -> dict[str, object]:
    loader = YAML(typ="safe")
    loaded = loader.load(text)
    assert isinstance(loaded, dict)
    return loaded


def test_v3_workcase_execution_items_require_split_or_plan_not_field_restoration(
    current_specs_repository: Path,
) -> None:
    loaded = _yaml(V3 / "workcases" / "workcase-0001-runtime-entry-user-input-contract.yaml")
    orchestration = loaded["orchestration"]
    assert isinstance(orchestration, dict)
    execution_items = orchestration["execution_items"]
    assert isinstance(execution_items, list) and len(execution_items) == 4
    dispositions = [
        {
            "legacy_item_id": item["id"],
            "stable_intent_target": "goal/scope/success_criteria",
            "execution_target": "future action template or child WorkCase",
            "result_target": "validation_summary/evidence_refs/history",
            "disposition": "split-or-plan",
        }
        for item in execution_items
        if isinstance(item, dict)
    ]
    assert len(dispositions) == len(execution_items)
    assert all(record["disposition"] == "split-or-plan" and all(record.values()) for record in dispositions)
    workcase_fields = {
        field.path
        for field in project_fact_schemas(inspect_repository(current_specs_repository))["workcase"].direct_fields
    }
    assert {"orchestration", "execution_items"}.isdisjoint(workcase_fields)
    assert {"goal", "scope", "success_criteria", "validation_summary"} <= workcase_fields


def test_v3_pitfall_tags_are_content_recall_inputs_not_v4_fields(current_specs_repository: Path) -> None:
    first = _yaml(V3 / "pitfalls" / "pitfall-0001-workcase-closure-tail-routing.yaml")
    second = _yaml(V3 / "pitfalls" / "pitfall-0002-codex-hook-protocol-adapter-boundary.yaml")
    assert isinstance(first["tags"], list) and len(first["tags"]) == 4
    assert isinstance(second["tags"], list) and len(second["tags"]) == 8
    tag_dispositions = [
        {
            "tag": tag,
            "disposition": "history-only-index-hint",
            "current_semantic_targets": (
                "title/symptoms/trigger_conditions/root_cause/resolution/avoidance/applicability"
            ),
        }
        for source in (first, second)
        for tag in source["tags"]
    ]
    assert len(tag_dispositions) == 12
    assert all(record["tag"] and record["current_semantic_targets"] for record in tag_dispositions)
    pitfall_fields = {
        field.path
        for field in project_fact_schemas(inspect_repository(current_specs_repository))["pitfall"].direct_fields
    }
    assert "tags" not in pitfall_fields
    assert {
        "symptoms",
        "trigger_conditions",
        "root_cause",
        "resolution",
        "avoidance",
        "applicability",
    } <= pitfall_fields


def test_v3_spark_long_evolution_is_rejected_instead_of_expanding_v4_schema(
    current_specs_repository: Path,
) -> None:
    source = V3 / "sparks" / "spark-0039-v3-sidecar-action-guide-compiler.yaml"
    parsed = parse_yaml_object(source.read_text(encoding="utf-8"))
    assert parsed.fields is not None
    assert isinstance(parsed.fields["evolution"], list) and len(parsed.fields["evolution"]) == 22
    dispositions = [
        {
            "legacy_index": index,
            "disposition": "compress-split-or-history",
            "automatic_migration": False,
        }
        for index, _ in enumerate(parsed.fields["evolution"])
    ]
    assert len(dispositions) == 22
    assert all(record["automatic_migration"] is False for record in dispositions)

    schema = project_fact_schemas(inspect_repository(current_specs_repository))["spark"]
    issues = validate_fact_object("spark", parsed.fields, schema)

    assert any(issue.field_path == "evolution" and "8" in issue.summary for issue in issues)
    assert any(issue.field_path == "created_at" for issue in issues)
