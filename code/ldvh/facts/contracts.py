"""Implementation adapters derived from the current fact-type sources.

Field membership is never listed here: it is projected from 05.Att.01 and the
type binding tables.  These adapters only connect source-defined carriers and
machine-checkable type constraints to filesystem and validator behavior.
"""

from __future__ import annotations

import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.filesystem import is_link_or_reparse

# Specs 21 §5: "活跃" 语义下的 open / blocked 工作态集合。
# 单一事实真源在 specs/21；此处仅镜像闭集供实现引用。
ACTIVE_STATUSES = frozenset({"open", "blocked"})
IGNORED_FACT_TYPE_ROOT_BASENAMES = frozenset({".DS_Store"})


def is_ignored_fact_type_root_entry(path: Path) -> bool:
    """Return whether a direct type-root entry is source-defined platform metadata."""

    if path.name not in IGNORED_FACT_TYPE_ROOT_BASENAMES:
        return False
    observed = path.lstat()
    return stat.S_ISREG(observed.st_mode) and not is_link_or_reparse(observed)


@dataclass(frozen=True, slots=True)
class FactTypeLayout:
    fact_type_key: str
    directory: str
    carrier: Literal["yaml", "markdown"]
    suffix: str
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
        carrier="markdown" if suffix == ".md" else "yaml",
        suffix=suffix,
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
        relation_keys=("depends-on", "routed-to", "contributed-to", "related-to"),
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
        initial_statuses=("draft",),
        statuses=("draft", "active", "discarded"),
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


WRITABLE_FACT_TYPE_KEYS = frozenset({"spark", "workcase", "adr", "pitfall", "study"})


TERMINAL_COMMON = frozenset({"disposition_summary"})

__all__ = [
    "ACTIVE_STATUSES",
    "IGNORED_FACT_TYPE_ROOT_BASENAMES",
    "LAYOUTS",
    "TERMINAL_COMMON",
    "WRITABLE_FACT_TYPE_KEYS",
    "FactTypeLayout",
    "is_ignored_fact_type_root_entry",
]
