"""Read-only full-project mechanical integrity check for fact objects.

This module deliberately reuses the same schema projection, canonical
discovery, and relation validation path used by fact-object reads.  It reports
whether that path can consume the complete current fact library; it does not
classify dialogue intent or write any fact object.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.facts.candidate_discovery import FactCandidateSnapshot, discover_fact_candidates
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import project_fact_schemas
from ldvh.specs.repository import inspect_repository
from ldvh.testing.working_tree_capture import GovernedWorktreeBoundary, resolve_capture_boundary

IntegrityStatus = Literal["complete", "partial", "unavailable"]


@dataclass(frozen=True, slots=True)
class FactIntegrityReport:
    """A content-free, machine-readable observation of current fact readability."""

    status: IntegrityStatus
    workspace: Path
    boundary: GovernedWorktreeBoundary | None
    object_count: int
    problems: tuple[dict[str, object], ...]

    def to_json(self) -> dict[str, object]:
        return {
            "status": self.status,
            "workspace": str(self.workspace),
            "boundary": None if self.boundary is None else self.boundary.to_json(),
            "object_count": self.object_count,
            "problems": list(self.problems),
        }


def _issue_json(read: FactReadResult) -> list[dict[str, object]]:
    return [
        {"category": issue.category, "field_path": issue.field_path, "summary": issue.summary}
        for issue in read.issues
    ]


def assess_fact_snapshot(snapshot: FactCandidateSnapshot) -> tuple[IntegrityStatus, tuple[dict[str, object], ...]]:
    """Classify a completed discovery snapshot without reading or writing files."""

    problems = list(snapshot.structural_problems)
    unavailable = not snapshot.complete
    for fact_type_key, object_id in snapshot.keys:
        read = snapshot.index.cache.get((fact_type_key, object_id))
        if read is None:
            unavailable = True
            problems.append(
                {
                    "fact_type_key": fact_type_key,
                    "canonical_path": LAYOUTS[fact_type_key].canonical_path(object_id),
                    "check_status": "unavailable",
                    "issues": [
                        {
                            "category": "location",
                            "field_path": None,
                            "summary": "canonical 事实对象未产生读取结果",
                        }
                    ],
                }
            )
            continue
        if read.check_status == "mechanically_valid":
            continue
        if read.check_status == "unavailable":
            unavailable = True
        problems.append(
            {
                "fact_type_key": fact_type_key,
                "canonical_path": read.canonical_path,
                "check_status": read.check_status,
                "issues": _issue_json(read),
            }
        )
    if unavailable:
        return "unavailable", tuple(problems)
    return ("partial" if problems else "complete"), tuple(problems)


def check_fact_integrity(workspace: Path) -> FactIntegrityReport:
    """Inspect one governed worktree using only the established read path."""

    resolved_workspace = workspace.resolve()
    boundary_resolution = resolve_capture_boundary(resolved_workspace)
    boundary = boundary_resolution.boundary
    if boundary is None:
        return FactIntegrityReport(
            "unavailable",
            resolved_workspace,
            None,
            0,
            tuple({"stage": "boundary", **diagnostic.to_json()} for diagnostic in boundary_resolution.diagnostics),
        )
    repository = inspect_repository(boundary.git_worktree_root)
    schemas = project_fact_schemas(repository)
    if not repository.implemented_checks_complete or set(schemas) != set(LAYOUTS):
        return FactIntegrityReport(
            "unavailable",
            resolved_workspace,
            boundary,
            0,
            (
                {
                    "stage": "rule-source",
                    "summary": "当前规则源无法完整投影五类事实对象 Schema",
                    "implemented_checks_complete": repository.implemented_checks_complete,
                    "schema_fact_type_keys": sorted(schemas),
                },
            ),
        )
    snapshot = discover_fact_candidates(
        boundary.git_worktree_root,
        boundary.governed_project_id,
        boundary.git_common_dir,
        schemas,
    )
    status, problems = assess_fact_snapshot(snapshot)
    return FactIntegrityReport(status, resolved_workspace, boundary, len(snapshot.keys), problems)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check current fact-object mechanical integrity without writes")
    parser.add_argument("--workspace", type=Path, required=True, help="absolute governed Git worktree root")
    return parser


def main(arguments: list[str] | None = None) -> int:
    namespace = _parser().parse_args(arguments)
    if not namespace.workspace.is_absolute():
        _parser().error("--workspace must be an absolute path")
    report = check_fact_integrity(namespace.workspace)
    print(json.dumps(report.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if report.status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
