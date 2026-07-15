"""Render the current fact-type field composition as a derived Markdown view."""

from __future__ import annotations

import argparse
from pathlib import Path

from ldvh.specs.fact_type_projection import project_fact_type_fields, render_fact_type_field_projection
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
    inspection = repository.field_registry
    if inspection is None:
        print("ERROR: field registry inspection is unavailable")
        return 1
    if inspection.issues:
        for issue in inspection.issues:
            print(f"ERROR: {issue.summary}")
        return 1
    print(render_fact_type_field_projection(project_fact_type_fields(inspection)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
