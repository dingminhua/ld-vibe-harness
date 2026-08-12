"""HEAD-based legacy detection for the first controlled update log entry.

An existing fact object without a top-level ``change_log`` may establish its
first entry during an otherwise-legal real update only when the committed
before-image genuinely predates the change-log mechanism.  A Working Tree
without ``change_log`` cannot by itself prove that: the same bytes also result
from deleting a committed log.  This module therefore reads the same-path HEAD
regular file and mechanically validates it, so Code can fail closed instead of
guessing history.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from ldvh.commits.git_adapter import read_head_regular_file
from ldvh.facts.content import validate_fact_content
from ldvh.facts.contracts import FactTypeLayout
from ldvh.facts.schema import FactSchema

HeadChangeLogState = Literal["absent", "present", "unavailable"]


def head_change_log_state(
    worktree_root: Path,
    layout: FactTypeLayout,
    schema: FactSchema,
    object_id: str,
) -> HeadChangeLogState:
    """Decide whether the committed same-path fact genuinely lacks a log.

    ``absent`` means HEAD resolves to a mechanically valid same-identity fact
    whose top-level fields contain no ``change_log``.  ``present`` means HEAD
    carries a ``change_log`` (so a Working Tree without one is a deletion, not a
    legacy baseline).  ``unavailable`` means the HEAD path is missing, is not a
    Git regular-file blob, cannot be read, is mechanically invalid, or cannot be
    consumed under the current type schema; all such states fail closed.
    """

    data, _oid, problem = read_head_regular_file(
        worktree_root,
        layout.canonical_path(object_id),
    )
    if data is None or problem is not None:
        return "unavailable"
    validated = validate_fact_content(layout, schema, object_id, data)
    if validated.check_status != "mechanically_valid" or validated.fields is None:
        return "unavailable"
    return "present" if "change_log" in validated.fields else "absent"


__all__ = ["HeadChangeLogState", "head_change_log_state"]
