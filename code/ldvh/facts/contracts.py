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
    initial_statuses: frozenset[str]
    statuses: frozenset[str]
    relation_keys: frozenset[str]

    def canonical_path(self, object_id: str) -> str:
        return f"{self.directory}/{object_id}{self.suffix}"


def _layout(
    fact_type_key: str,
    plural: str,
    *,
    suffix: str = ".yaml",
    initial_statuses: tuple[str, ...],
    statuses: tuple[str, ...],
    relation_keys: tuple[str, ...],
) -> FactTypeLayout:
    return FactTypeLayout(
        fact_type_key=fact_type_key,
        directory=f"ldvh-base/{plural}",
        suffix=suffix,
        carrier="markdown" if suffix == ".md" else "yaml",
        object_id_pattern=re.compile(rf"{re.escape(fact_type_key)}-[0-9]{{4,}}\Z"),
        initial_statuses=frozenset(initial_statuses),
        statuses=frozenset(statuses),
        relation_keys=frozenset(relation_keys),
    )


LAYOUTS = {
    "spark": _layout(
        "spark",
        "sparks",
        initial_statuses=("open",),
        statuses=("open", "routed", "implemented", "discarded"),
        relation_keys=("routed-to", "related-to"),
    ),
    "workcase": _layout(
        "workcase",
        "workcases",
        initial_statuses=("open",),
        statuses=("open", "blocked", "closed"),
        relation_keys=("depends-on", "routed-to"),
    ),
    "adr": _layout(
        "adr",
        "adrs",
        initial_statuses=("active",),
        statuses=("active", "retired"),
        relation_keys=(),
    ),
    "pitfall": _layout(
        "pitfall",
        "pitfalls",
        initial_statuses=("active",),
        statuses=("active", "retired"),
        relation_keys=(),
    ),
    "study": _layout(
        "study",
        "studies",
        suffix=".md",
        initial_statuses=("active",),
        statuses=("active", "retired"),
        relation_keys=("inspired-by", "informs"),
    ),
}


TERMINAL_COMMON = frozenset({"disposition_summary"})

__all__ = ["LAYOUTS", "TERMINAL_COMMON", "FactTypeLayout"]
