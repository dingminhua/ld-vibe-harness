"""Inject the product-neutral LDVH signature into new commit footers.

The product integration supplies one JSON snapshot through ``LDVH_SIGNATURE``.
LDVH deliberately does not discover product, model, or runtime information
itself: it only validates and transports that snapshot to the commit contract.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from ldvh.signature import parse_signature

_SIGNATURE_TRAILER_NAMES = (
    "LDVH-Product-Name",
    "LDVH-Model-Name",
    "LDVH-Agent-Runtime-Name",
)
_RETIRED_TRAILER_NAMES = (
    "Session-ID",
    "Model-ID",
    "Workbench-Name",
    "Agent-ID",
    "Host-Environment",
    "Signer-Type",
)
_TRAILER_RE = re.compile(r"^(?P<name>[A-Za-z][A-Za-z-]*): (?P<value>.*)\Z")


def _is_signature_trailer(line: str) -> bool:
    match = _TRAILER_RE.match(line)
    return match is not None and match.group("name") in (*_SIGNATURE_TRAILER_NAMES, *_RETIRED_TRAILER_NAMES)


def _strip_signature_trailers(lines: list[str]) -> list[str]:
    """Strip only the contiguous signature trailer suffix."""

    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    start = end
    while start > 0 and _is_signature_trailer(lines[start - 1]):
        start -= 1
    if start == end:
        return lines
    result = lines[:start]
    while result and not result[-1].strip():
        result.pop()
    return result


def _environment_signature() -> tuple[dict[str, str], tuple[str, ...]]:
    """Read the sole cross-product transport value, without fallback inference."""

    raw = os.environ.get("LDVH_SIGNATURE")
    if raw is None or not raw.strip():
        return {}, ()
    try:
        supplied = json.loads(raw)
    except json.JSONDecodeError:
        return {}, ("LDVH_SIGNATURE 不是有效 JSON object",)
    signature, problems = parse_signature(supplied)
    if problems or signature is None:
        return {}, problems
    values = signature.as_dict()
    names = {
        "LDVH-Product-Name": values["product_name"],
        "LDVH-Model-Name": values["model_name"],
        "LDVH-Agent-Runtime-Name": values["agent_runtime_name"],
    }
    return {name: value for name, value in names.items() if value is not None}, ()


def inject_environment_signature(message: str) -> str:
    """Replace any self-reported or retired signature trailers with the snapshot."""

    env_signature, _ = _environment_signature()
    lines = _strip_signature_trailers(message.split("\n"))
    while lines and not lines[-1].strip():
        lines.pop()
    if not env_signature:
        return "\n".join(lines)
    if not lines:
        lines = [""]
    lines.append("")
    for name in _SIGNATURE_TRAILER_NAMES:
        value = env_signature.get(name)
        if value:
            lines.append(f"{name}: {value}")
    return "\n".join(lines)


def run_prepare_commit_msg(message_file: str) -> str | None:
    path = Path(message_file)
    try:
        path.resolve(strict=True)
    except OSError as error:
        return f"message file could not be resolved: {error}"
    if not path.is_file():
        return "message file does not identify a regular file"
    try:
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return f"message file could not be read as UTF-8: {error}"
    transformed = inject_environment_signature(original)
    if transformed == original:
        return None
    try:
        path.write_text(transformed, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError) as error:
        return f"message file could not be written: {error}"
    return None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inject an LDVH signature snapshot into a commit message")
    parser.add_argument("--message-file", required=True)
    return parser


def main(arguments: list[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    error = run_prepare_commit_msg(parsed.message_file)
    if error is not None:
        sys.stderr.write(f"LDVH prepare-commit-msg: {error}\n")
        return 0
    signature, problems = _environment_signature()
    if signature:
        sys.stderr.write("LDVH prepare-commit-msg: injected LDVH signature from environment\n")
    elif problems:
        sys.stderr.write(f"LDVH prepare-commit-msg: {'；'.join(problems)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
