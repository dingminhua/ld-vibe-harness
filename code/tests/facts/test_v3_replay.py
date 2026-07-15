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


def test_v3_spark_long_evolution_does_not_expand_the_v4_eight_item_limit(
    current_specs_repository: Path,
) -> None:
    source = V3 / "sparks" / "spark-0039-v3-sidecar-action-guide-compiler.yaml"
    parsed = parse_yaml_object(source.read_text(encoding="utf-8"))
    assert parsed.fields is not None
    evolution = parsed.fields["evolution"]
    assert isinstance(evolution, list) and len(evolution) == 22

    schema = project_fact_schemas(inspect_repository(current_specs_repository))["spark"]
    at_limit_issues = validate_fact_object("spark", {**parsed.fields, "evolution": evolution[:8]}, schema)
    over_limit_issues = validate_fact_object("spark", {**parsed.fields, "evolution": evolution[:9]}, schema)

    assert all(issue.field_path != "evolution" for issue in at_limit_issues)
    assert any(issue.field_path == "evolution" for issue in over_limit_issues)
