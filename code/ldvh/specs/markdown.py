"""Minimal Markdown structure parsing for LDVH specification sources.

This module deliberately stops at source structure.  It does not decide whether
a document is a current rule source, interpret YAML, or apply domain rules.
"""

from __future__ import annotations

import os
import re
import stat
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from ldvh.diagnostics import Issue, SourceLocation

_ATX_HEADING = re.compile(r" {0,3}(?P<marks>#{1,6})(?:[ \t]+(?P<title>.*?))?[ \t]*$")
_SETEXT_UNDERLINE = re.compile(r" {0,3}(?P<marks>=+|-+)[ \t]*$")
_FENCE_OPEN = re.compile(r"(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
_TABLE_DELIMITER = re.compile(r":?-{3,}:?")


@dataclass(frozen=True, slots=True)
class Heading:
    """An H2 or H3 found outside fenced code blocks."""

    level: int
    title: str
    line: int


@dataclass(frozen=True, slots=True)
class MarkdownTable:
    """A GFM-style table with source-exact cells after minimal unwrapping."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    line: int


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    """The source structure needed by higher-level LDVH parsers."""

    relative_path: str
    raw_lines: tuple[str, ...]
    h1: str | None
    h1_line: int | None
    yaml_text: str | None
    yaml_line: int | None
    headings: tuple[Heading, ...]

    @property
    def path(self) -> str:
        """Compatibility shorthand for the repository-relative path."""

        return self.relative_path

    @property
    def lines(self) -> tuple[str, ...]:
        """Compatibility shorthand for raw source lines."""

        return self.raw_lines

    @property
    def h1_title(self) -> str | None:
        """The parsed first-line H1 title, if valid."""

        return self.h1

    @property
    def yaml_block_text(self) -> str | None:
        """The identity block contents without either code fence."""

        return self.yaml_text

    @property
    def yaml_block_line(self) -> int | None:
        """The one-based line of the identity block's opening fence."""

        return self.yaml_line

    @property
    def yaml_content_line(self) -> int | None:
        """The one-based line on which YAML content starts."""

        return None if self.yaml_line is None else self.yaml_line + 1

    def find_headings(self, title: str, *, level: int | None = None) -> tuple[Heading, ...]:
        """Return every exact title match, preserving source order."""

        return tuple(
            heading for heading in self.headings if heading.title == title and (level is None or heading.level == level)
        )

    def find_heading(self, title: str, *, level: int | None = None) -> Heading | None:
        """Return the first exact title match, if any.

        Callers that require uniqueness must use :meth:`find_headings` and
        diagnose multiple matches themselves.
        """

        matches = self.find_headings(title, level=level)
        return matches[0] if matches else None

    def table_after(self, heading: Heading) -> MarkdownTable | None:
        """Parse a table immediately after a heading and optional blank lines."""

        return parse_table_after_heading(self, heading)

    def table_after_heading(self, title: str, *, level: int | None = None) -> MarkdownTable | None:
        """Parse the table after the first exact heading match, if present."""

        heading = self.find_heading(title, level=level)
        return None if heading is None else self.table_after(heading)


@dataclass(frozen=True, slots=True)
class MarkdownResult:
    """A parsed document plus source-locatable structural issues."""

    document: MarkdownDocument
    issues: tuple[Issue, ...]

    def __iter__(self) -> Iterator[object]:
        """Allow ``document, issues = parse_markdown(...)`` unpacking."""

        yield self.document
        yield self.issues


def parse_markdown(path: str | Path, relative_path: str | Path) -> MarkdownResult:
    """Read and minimally parse an LDVH Markdown candidate.

    Only the fixed first-line H1, fixed-position YAML identity fence, headings,
    and strict table source structure are in scope.  Rule-source qualification
    and all semantic checks belong to higher-level modules.
    """

    source_path = Path(relative_path).as_posix()
    try:
        raw_lines = _read_regular_file_without_symlinks(Path(path), Path(source_path))
    except UnicodeError as error:
        document = MarkdownDocument(source_path, (), None, None, None, None, ())
        issue = Issue(
            summary="Markdown source could not be read as UTF-8",
            location=SourceLocation(source_path),
            cause=str(error),
        )
        return MarkdownResult(document, (issue,))
    except OSError as error:
        document = MarkdownDocument(source_path, (), None, None, None, None, ())
        issue = Issue(
            summary="Markdown source could not be read safely from its current path",
            location=SourceLocation(source_path),
            cause=str(error),
        )
        return MarkdownResult(document, (issue,))

    issues: list[Issue] = []
    first_heading = _parse_heading(raw_lines[0]) if raw_lines else None
    if first_heading is None or first_heading[0] != 1:
        h1 = None
        h1_line = None
        issues.append(
            Issue(
                summary="Markdown file must start with an H1 heading on line 1",
                location=SourceLocation(source_path, line=1),
            )
        )
    else:
        h1 = first_heading[1]
        h1_line = 1

    yaml_text: str | None = None
    yaml_line: int | None = None
    identity_fence = _FENCE_OPEN.fullmatch(raw_lines[2]) if len(raw_lines) >= 3 else None
    identity_info = identity_fence.group("info").strip() if identity_fence is not None else None
    if len(raw_lines) < 3 or raw_lines[1].strip() or identity_info != "yaml":
        problem_line = 2 if len(raw_lines) < 2 or (len(raw_lines) >= 2 and raw_lines[1].strip()) else 3
        issues.append(
            Issue(
                summary="YAML identity fence must follow the H1 after exactly one blank line",
                location=SourceLocation(source_path, line=problem_line),
            )
        )
    else:
        yaml_line = 3
        opening_marks = identity_fence.group("fence")
        closing_index = next(
            (
                index
                for index in range(3, len(raw_lines))
                if _is_fence_close(raw_lines[index], opening_marks[0], len(opening_marks))
            ),
            None,
        )
        if closing_index is None:
            yaml_text = "\n".join(raw_lines[3:])
            issues.append(
                Issue(
                    summary="YAML identity fence is not closed",
                    location=SourceLocation(source_path, line=3),
                )
            )
        else:
            yaml_text = "\n".join(raw_lines[3:closing_index])

    headings: list[Heading] = []
    open_fence: tuple[str, int] | None = None
    for index, line in enumerate(raw_lines):
        line_number = index + 1
        if open_fence is not None:
            marker, minimum_length = open_fence
            if _is_fence_close(line, marker, minimum_length):
                open_fence = None
            continue

        fence = _FENCE_OPEN.fullmatch(line)
        if fence is not None:
            marks = fence.group("fence")
            open_fence = (marks[0], len(marks))
            continue

        parsed = _parse_heading(line)
        if parsed is None:
            continue
        level, title = parsed
        if level == 1 and line_number != 1:
            issues.append(
                Issue(
                    summary="Markdown file may contain only the first-line H1 heading",
                    location=SourceLocation(source_path, line=line_number, heading=title),
                )
            )
        elif level in (2, 3):
            headings.append(Heading(level, title, line_number))

    for heading in _find_setext_headings(raw_lines):
        issues.append(
            Issue(
                summary=f"Setext H{heading.level} headings are not allowed; use ATX headings",
                location=SourceLocation(source_path, line=heading.line, heading=heading.title),
            )
        )

    document = MarkdownDocument(
        relative_path=source_path,
        raw_lines=raw_lines,
        h1=h1,
        h1_line=h1_line,
        yaml_text=yaml_text,
        yaml_line=yaml_line,
        headings=tuple(headings),
    )
    return MarkdownResult(document, tuple(issues))


def _read_regular_file_without_symlinks(path: Path, relative_path: Path) -> tuple[str, ...]:
    """Read one repository-relative file without following any path-component symlink."""

    invalid_component = any(part in {"", ".", ".."} for part in relative_path.parts)
    if relative_path.is_absolute() or not relative_path.parts or invalid_component:
        raise OSError("source path must be a normalized repository-relative path")

    absolute_path = path.absolute()
    repository_root = absolute_path
    for _ in relative_path.parts:
        repository_root = repository_root.parent
    if repository_root / relative_path != absolute_path:
        raise OSError("source path does not match its repository-relative path")

    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if no_follow is None or directory_flag is None:
        raise OSError("safe no-follow file opening is unavailable on this platform")

    directory_fd = os.open(repository_root, os.O_RDONLY | directory_flag | no_follow)
    try:
        for component in relative_path.parts[:-1]:
            next_fd = os.open(component, os.O_RDONLY | directory_flag | no_follow, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd

        file_fd = os.open(relative_path.parts[-1], os.O_RDONLY | no_follow, dir_fd=directory_fd)
        try:
            before_read = os.fstat(file_fd)
            if not stat.S_ISREG(before_read.st_mode):
                raise OSError("source path is not a regular file")
            with os.fdopen(file_fd, "r", encoding="utf-8") as source:
                file_fd = -1
                text = source.read()
                after_read = os.fstat(source.fileno())
                observed_before = (
                    before_read.st_dev,
                    before_read.st_ino,
                    before_read.st_nlink,
                    before_read.st_size,
                    before_read.st_mtime_ns,
                    before_read.st_ctime_ns,
                )
                observed_after = (
                    after_read.st_dev,
                    after_read.st_ino,
                    after_read.st_nlink,
                    after_read.st_size,
                    after_read.st_mtime_ns,
                    after_read.st_ctime_ns,
                )
                if observed_before != observed_after:
                    raise OSError("source file changed while it was being read")
                return tuple(text.splitlines())
        finally:
            if file_fd >= 0:
                os.close(file_fd)
    finally:
        os.close(directory_fd)


def find_headings(document: MarkdownDocument, title: str, *, level: int | None = None) -> tuple[Heading, ...]:
    """Return every exact heading match from ``document``."""

    return document.find_headings(title, level=level)


def find_setext_headings(document: MarkdownDocument) -> tuple[Heading, ...]:
    """Return Setext H1/H2 headings found outside fenced code blocks."""

    return _find_setext_headings(document.raw_lines)


def parse_table_after_heading(document: MarkdownDocument, heading: Heading) -> MarkdownTable | None:
    """Parse the GFM table immediately following ``heading``.

    Blank lines are allowed between the heading and table.  Any other content
    means the table is not adjacent and produces ``None``.  Body row cell counts
    are preserved exactly so a contract-specific caller can diagnose them.
    """

    fenced_lines = _fenced_line_numbers(document.raw_lines)
    if heading.line in fenced_lines:
        return None

    index = heading.line
    while index < len(document.raw_lines) and not document.raw_lines[index].strip():
        index += 1
    if index + 1 >= len(document.raw_lines):
        return None
    if index + 1 in fenced_lines or index + 2 in fenced_lines:
        return None

    headers, header_separators = _split_table_row(document.raw_lines[index])
    delimiters, delimiter_separators = _split_table_row(document.raw_lines[index + 1])
    if not headers or not delimiters:
        return None
    if header_separators == 0 and delimiter_separators == 0:
        return None
    if len(headers) != len(delimiters) or any(_TABLE_DELIMITER.fullmatch(cell) is None for cell in delimiters):
        return None

    rows: list[tuple[str, ...]] = []
    row_index = index + 2
    while row_index < len(document.raw_lines):
        line = document.raw_lines[row_index]
        if (
            row_index + 1 in fenced_lines
            or not line.strip()
            or _parse_heading(line) is not None
            or _FENCE_OPEN.fullmatch(line) is not None
        ):
            break
        cells, separators = _split_table_row(line)
        if separators == 0:
            break
        rows.append(cells)
        row_index += 1

    return MarkdownTable(headers=headers, rows=tuple(rows), line=index + 1)


def _parse_heading(line: str) -> tuple[int, str] | None:
    match = _ATX_HEADING.fullmatch(line)
    if match is None:
        return None
    title = match.group("title") or ""
    title = re.sub(r"[ \t]+#+[ \t]*$", "", title).strip()
    return len(match.group("marks")), title


def _find_setext_headings(raw_lines: tuple[str, ...]) -> tuple[Heading, ...]:
    fenced_lines = _fenced_line_numbers(raw_lines)
    headings: list[Heading] = []
    for underline_index in range(1, len(raw_lines)):
        underline_line = underline_index + 1
        title_line = underline_index
        if underline_line in fenced_lines or title_line in fenced_lines:
            continue

        match = _SETEXT_UNDERLINE.fullmatch(raw_lines[underline_index])
        title = raw_lines[underline_index - 1].strip()
        if match is None or not title or _parse_heading(raw_lines[underline_index - 1]) is not None:
            continue

        level = 1 if match.group("marks").startswith("=") else 2
        headings.append(Heading(level=level, title=title, line=title_line))
    return tuple(headings)


def _fenced_line_numbers(raw_lines: tuple[str, ...]) -> frozenset[int]:
    fenced: set[int] = set()
    open_fence: tuple[str, int] | None = None
    for index, line in enumerate(raw_lines, start=1):
        if open_fence is not None:
            fenced.add(index)
            marker, minimum_length = open_fence
            if _is_fence_close(line, marker, minimum_length):
                open_fence = None
            continue

        fence = _FENCE_OPEN.fullmatch(line)
        if fence is None:
            continue
        marks = fence.group("fence")
        open_fence = (marks[0], len(marks))
        fenced.add(index)
    return frozenset(fenced)


def _is_fence_close(line: str, marker: str, minimum_length: int) -> bool:
    return re.fullmatch(rf" {{0,3}}{re.escape(marker)}{{{minimum_length},}}[ \t]*", line) is not None


def _split_table_row(line: str) -> tuple[tuple[str, ...], int]:
    source = line.strip()
    cells: list[str] = []
    current: list[str] = []
    separators = 0

    for character in source:
        if character == "|":
            backslashes = 0
            for existing in reversed(current):
                if existing != "\\":
                    break
                backslashes += 1
            if backslashes % 2:
                current.pop()
                current.append("|")
                continue
            cells.append("".join(current))
            current = []
            separators += 1
        else:
            current.append(character)
    cells.append("".join(current))

    if source.startswith("|"):
        cells.pop(0)
    if source.endswith("|") and not _ends_with_escaped_pipe(source):
        cells.pop()

    return tuple(_unwrap_table_cell(cell) for cell in cells), separators


def _ends_with_escaped_pipe(source: str) -> bool:
    if not source.endswith("|"):
        return False
    backslashes = 0
    for character in reversed(source[:-1]):
        if character != "\\":
            break
        backslashes += 1
    return backslashes % 2 == 1


def _unwrap_table_cell(cell: str) -> str:
    value = cell.strip()
    if not value.startswith("`"):
        return value

    opening_length = len(value) - len(value.lstrip("`"))
    closing_length = len(value) - len(value.rstrip("`"))
    if opening_length != closing_length or len(value) < opening_length * 2:
        return value

    fence = "`" * opening_length
    body = value[opening_length:-closing_length]
    return body if fence not in body else value
