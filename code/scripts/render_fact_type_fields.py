"""Render the current fact-type field composition as a derived Markdown view."""

from __future__ import annotations

import argparse
from pathlib import Path

from ldvh.specs.fact_type_projection import project_fact_type_fields, render_fact_type_field_projection
from ldvh.specs.field_registry import ADMISSION_AUDIT_PATH, inspect_field_registry
from ldvh.specs.markdown import parse_markdown
from ldvh.specs.repository import inspect_repository


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", nargs="?", default=".")
    args = parser.parse_args()
    repository_root = Path(args.repository).resolve()
    repository = inspect_repository(repository_root)
    if repository.issues:
        for issue in repository.issues:
            print(f"ERROR: {issue.summary}")
        return 1
    audit = parse_markdown(repository_root / ADMISSION_AUDIT_PATH, ADMISSION_AUDIT_PATH).document
    inspection = inspect_field_registry(
        repository.active_documents_passing_implemented_checks,
        admission_audit=audit,
    )
    if inspection.issues:
        for issue in inspection.issues:
            print(f"ERROR: {issue.summary}")
        return 1
    print(render_fact_type_field_projection(project_fact_type_fields(inspection)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
