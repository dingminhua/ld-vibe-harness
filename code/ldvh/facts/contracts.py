"""Implementation adapters derived from the five current fact-type sources.

Field membership is never listed here: it is projected from 05.Att.01 and the
type binding tables.  These adapters only connect source-defined carriers and
machine-checkable type constraints to filesystem and validator behavior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FactTypeLayout:
    fact_type_key: str
    directory: str
    suffix: str
    carrier: str
    object_id_pattern: re.Pattern[str]
    statuses: frozenset[str]
    relation_keys: frozenset[str]

    def canonical_path(self, object_id: str) -> str:
        return f"{self.directory}/{object_id}{self.suffix}"


def _layout(
    fact_type_key: str,
    plural: str,
    *,
    suffix: str = ".yaml",
    statuses: tuple[str, ...],
    relation_keys: tuple[str, ...],
) -> FactTypeLayout:
    return FactTypeLayout(
        fact_type_key=fact_type_key,
        directory=f"facts/{plural}",
        suffix=suffix,
        carrier="markdown" if suffix == ".md" else "yaml",
        object_id_pattern=re.compile(rf"{re.escape(fact_type_key)}-[0-9]{{4,}}\Z"),
        statuses=frozenset(statuses),
        relation_keys=frozenset(relation_keys),
    )


LAYOUTS = {
    "spark": _layout(
        "spark",
        "sparks",
        statuses=("open", "routed", "discarded"),
        relation_keys=("routed-to", "related-to", "supersedes"),
    ),
    "workcase": _layout(
        "workcase",
        "workcases",
        statuses=("open", "blocked", "closed"),
        relation_keys=("depends-on", "routed-to", "supersedes"),
    ),
    "adr": _layout(
        "adr",
        "adrs",
        statuses=("active", "superseded", "retired"),
        relation_keys=("supersedes",),
    ),
    "pitfall": _layout(
        "pitfall",
        "pitfalls",
        statuses=("active", "superseded", "retired"),
        relation_keys=("supersedes",),
    ),
    "study": _layout(
        "study",
        "studies",
        suffix=".md",
        statuses=("active", "superseded", "retired"),
        relation_keys=("supersedes",),
    ),
}


TERMINAL_COMMON = frozenset({"disposition_summary", "closed_at", "evidence_refs"})

__all__ = ["LAYOUTS", "TERMINAL_COMMON", "FactTypeLayout"]
