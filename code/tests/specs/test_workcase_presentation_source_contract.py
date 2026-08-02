from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from ldvh.facts.workcase_presentation import CLOSED_PRESENTATION, PHASE_PRESENTATION

ROOT = Path(__file__).resolve().parents[3]
WORKCASE_SPEC = ROOT / "specs/21-WorkCase-工作项.md"
SECTION_HEADING = "### 9.3 当前快照确定性呈现投影"
PROJECTION_KEYS = (
    "lifecycle_position",
    "handoff_narrative_key",
    "next_required_control_step",
    "progress_group",
    "progress_step",
)
HEADER_CELLS = (
    "当前 `status` / `phase`",
    *(f"`{key}`" for key in PROJECTION_KEYS),
)
HEADER = "| " + " | ".join(HEADER_CELLS) + " |"
SEPARATOR = "|" + "|".join("---" for _ in HEADER_CELLS) + "|"
INLINE_TOKEN = re.compile(r"^`([a-z][a-z0-9_]*)`$")
OPEN_POSITION = re.compile(r"^`open` / `([a-z][a-z0-9_]*)`$")
CLOSED_POSITION = "`closed` / phase 省略"


def _source() -> str:
    return WORKCASE_SPEC.read_text(encoding="utf-8")


def _section_lines(source: str) -> list[str]:
    lines = source.splitlines()
    positions = [index for index, line in enumerate(lines) if line == SECTION_HEADING]
    if len(positions) != 1:
        raise ValueError(f"expected one {SECTION_HEADING!r}, found {len(positions)}")
    start = positions[0] + 1
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return lines[start:end]


def _table_lines(source: str) -> list[str]:
    section = _section_lines(source)
    header_positions = [index for index, line in enumerate(section) if line == HEADER]
    if len(header_positions) != 1:
        raise ValueError(f"expected one exact presentation table header, found {len(header_positions)}")
    start = header_positions[0]
    table: list[str] = []
    for line in section[start:]:
        if not line.startswith("|"):
            break
        table.append(line)
    return table


def _cells(line: str) -> list[str]:
    if not line.startswith("|") or not line.endswith("|"):
        raise ValueError(f"malformed Markdown row: {line!r}")
    cells = [cell.strip() for cell in line[1:-1].split("|")]
    if len(cells) != len(HEADER_CELLS):
        raise ValueError(f"expected six cells, found {len(cells)}: {line!r}")
    return cells


def _projection(cells: list[str]) -> dict[str, str | None]:
    projection: dict[str, str | None] = {}
    for key, cell in zip(PROJECTION_KEYS, cells, strict=True):
        match = INLINE_TOKEN.fullmatch(cell)
        if match is None:
            raise ValueError(f"{key} must be one inline-code token: {cell!r}")
        token = match.group(1)
        if token == "null":
            if key != "progress_step":
                raise ValueError(f"null is only valid for progress_step, found in {key}")
            projection[key] = None
        else:
            projection[key] = token
    return projection


def _parse_contract(source: str) -> tuple[dict[str, dict[str, str | None]], dict[str, str | None]]:
    table = _table_lines(source)
    if len(table) < 2 or table[0] != HEADER or table[1] != SEPARATOR:
        raise ValueError("presentation table header or separator drifted")

    rows = table[2:]
    if len(set(rows)) != len(rows):
        raise ValueError("presentation table contains a duplicate data row")
    if len(rows) != len(PHASE_PRESENTATION) + 1:
        raise ValueError(f"expected eight presentation rows, found {len(rows)}")

    open_rows: dict[str, dict[str, str | None]] = {}
    closed: dict[str, str | None] | None = None
    observed_positions: list[str] = []
    for index, row in enumerate(rows):
        cells = _cells(row)
        position = cells[0]
        observed_positions.append(position)
        if index < len(PHASE_PRESENTATION):
            match = OPEN_POSITION.fullmatch(position)
            if match is None:
                raise ValueError(f"open row has malformed status/phase cell: {position!r}")
            phase = match.group(1)
            if phase in open_rows:
                raise ValueError(f"duplicate open phase: {phase}")
            open_rows[phase] = _projection(cells[1:])
        else:
            if position != CLOSED_POSITION:
                raise ValueError(f"closed row has malformed status/phase cell: {position!r}")
            closed = _projection(cells[1:])

    expected_positions = [f"`open` / `{phase}`" for phase in PHASE_PRESENTATION]
    expected_positions.append(CLOSED_POSITION)
    if observed_positions != expected_positions:
        raise ValueError("presentation rows are missing, extra, or out of order")
    assert closed is not None
    return open_rows, closed


def _assert_contract(source: str) -> None:
    open_rows, closed = _parse_contract(source)
    assert open_rows == PHASE_PRESENTATION
    assert closed == CLOSED_PRESENTATION


def _replace_table(source: str, transform: Callable[[list[str]], list[str]]) -> str:
    original = _table_lines(source)
    mutated = transform(list(original))
    block = "\n".join(original)
    assert source.count(block) == 1
    return source.replace(block, "\n".join(mutated), 1)


def _missing_row(source: str) -> str:
    return _replace_table(source, lambda lines: [*lines[:2], *lines[3:]])


def _extra_row(source: str) -> str:
    def transform(lines: list[str]) -> list[str]:
        extra = lines[2].replace("`human_plan_confirming`", "`unexpected_phase`", 1)
        return [*lines[:-1], extra, lines[-1]]

    return _replace_table(source, transform)


def _duplicate_row(source: str) -> str:
    return _replace_table(source, lambda lines: [*lines[:-1], lines[2], lines[-1]])


def _rows_out_of_order(source: str) -> str:
    def transform(lines: list[str]) -> list[str]:
        lines[2], lines[3] = lines[3], lines[2]
        return lines

    return _replace_table(source, transform)


def _header_columns_out_of_order(source: str) -> str:
    def transform(lines: list[str]) -> list[str]:
        cells = _cells(lines[0])
        cells[1], cells[2] = cells[2], cells[1]
        lines[0] = "| " + " | ".join(cells) + " |"
        return lines

    return _replace_table(source, transform)


def _malformed_status_phase(source: str) -> str:
    return _replace_table(source, lambda lines: [*lines[:2], lines[2].replace("`open` / `", "`open`/`", 1), *lines[3:]])


def _bare_null(source: str) -> str:
    return _replace_table(source, lambda lines: [line.replace("`null`", "null", 1) for line in lines])


def _unknown_inline_token(source: str) -> str:
    return _replace_table(
        source,
        lambda lines: [line.replace("`gate1_waiting`", "`unknown_contract_token`", 1) for line in lines],
    )


def _known_token_in_wrong_cell(source: str) -> str:
    return _replace_table(
        source,
        lambda lines: [line.replace("`gate1_waiting`", "`closed`", 1) for line in lines],
    )


def test_spec_table_exactly_matches_python_presentation_constants() -> None:
    _assert_contract(_source())


@pytest.mark.parametrize(
    "mutation",
    [
        _missing_row,
        _extra_row,
        _duplicate_row,
        _rows_out_of_order,
        _header_columns_out_of_order,
        _malformed_status_phase,
        _bare_null,
        _unknown_inline_token,
        _known_token_in_wrong_cell,
    ],
    ids=lambda mutation: mutation.__name__.removeprefix("_"),
)
def test_spec_table_mutations_fail_the_same_contract_path(mutation: Callable[[str], str]) -> None:
    with pytest.raises((AssertionError, ValueError)):
        _assert_contract(mutation(_source()))
