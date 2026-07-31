from __future__ import annotations

from pathlib import Path

from ldvh.specs.fact_type_projection import project_fact_type_fields, render_fact_type_field_projection
from ldvh.specs.field_registry import inspect_field_registry
from ldvh.specs.repository import inspect_repository


def test_current_fact_type_field_projection_is_complete_and_derived(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    inspection = inspect_field_registry(repository.active_documents_passing_implemented_checks)

    items = project_fact_type_fields(inspection)
    rendered = render_fact_type_field_projection(items)

    assert inspection.complete is True
    assert {item.fact_type_key for item in items} == {
        "spark",
        "workcase",
        "adr",
        "pitfall",
        "study",
        "file-asset",
    }
    assert len(items) > 83
    assert "不是规则源、字段定义或独立 Schema 权威" in rendered
    assert "| `object_id` | `object-id` | `string` | `required` |" in rendered
    assert "| `evolution` | `evolution` | `array` | `conditional` | `spark-evolution-entry` |" in rendered
    assert "| `evolution[].at` | `evolution-at` | `string` | `required` |" in rendered
    assert "| `relations[].target.object_id` | `relation-target-object-id` | `string` | `required` |" in rendered
    assert "| `signature.agent_id` | `file-asset-signature-agent-id` | `string` | `conditional` |" in rendered
