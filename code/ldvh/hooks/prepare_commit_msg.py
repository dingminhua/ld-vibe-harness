"""Environment-injected footer signatures for ``prepare-commit-msg``.

The calling environment (e.g. WorkBuddy) knows the actual model, workbench
and session identity.  When those values are available as environment
variables, this module strips any AI-self-reported signature trailers from
the commit message and appends the environment-provided values instead.

This is the commit-footer analogue of ``observed_context`` injection for
fact-write ``change_log`` signatures: the trusted source is the environment,
not the model's self-report.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SIGNATURE_TRAILER_NAMES = ("Session-ID", "Model-ID", "Workbench-Name")
_TRAILER_RE = re.compile(r"^(?P<name>[A-Za-z][A-Za-z-]*): (?P<value>.*)\Z")

# Environment variable fallback chains — first non-empty value wins.
# LDVH_* are the canonical names; CODEBUDDY_* / CLAUDE_* / CLIENT_INFO_* are
# the actual variables WorkBuddy sets in the AI's shell subprocess.
_ENV_SESSION_ID = ("LDVH_SESSION_ID", "CODEBUDDY_SESSION_ID", "CLAUDE_SESSION_ID")
_ENV_MODEL_ID = ("LDVH_MODEL_ID",)  # no fallback: current env does not expose model identity
_ENV_WORKBENCH_NAME = ("LDVH_WORKBENCH_NAME", "CLIENT_INFO_PRODUCT_NAME")


def _is_signature_trailer(line: str) -> bool:
    match = _TRAILER_RE.match(line)
    return match is not None and match.group("name") in _SIGNATURE_TRAILER_NAMES


def _strip_signature_trailers(lines: list[str]) -> list[str]:
    """Remove trailing blank lines, then strip signature trailers from the end."""

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


def _environment_signature() -> dict[str, str]:
    """Read signature values from environment variables.

    Returns a dict with keys from ``_SIGNATURE_TRAILER_NAMES``.  Only keys
    whose env var is set and non-empty are included.  When a key has a
    fallback chain, the first non-empty value wins.
    """

    import os

    mapping = {
        "Session-ID": _ENV_SESSION_ID,
        "Model-ID": _ENV_MODEL_ID,
        "Workbench-Name": _ENV_WORKBENCH_NAME,
    }
    result: dict[str, str] = {}
    for name, env_keys in mapping.items():
        for key in env_keys:
            value = os.environ.get(key)
            if isinstance(value, str) and value.strip():
                result[name] = value.strip()
                break
    return result


def _parse_existing_trailers(lines: list[str]) -> dict[str, str]:
    """Read signature trailers from the end of the message."""

    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    start = end
    while start > 0 and _is_signature_trailer(lines[start - 1]):
        start -= 1
    if start == end:
        return {}
    result: dict[str, str] = {}
    for line in lines[start:end]:
        match = _TRAILER_RE.match(line)
        assert match is not None
        result[match.group("name")] = match.group("value")
    return result


def inject_environment_signature(message: str) -> str:
    """Override AI-reported trailers with environment-provided values.

    Only fields whose env var is available are overridden; fields without
    env values retain the AI-reported value (or remain absent).  When no
    env vars are set at all, the message is returned unchanged.
    """

    env_signature = _environment_signature()
    if not env_signature:
        return message
    lines = message.split("\n")
    existing = _parse_existing_trailers(lines)
    # Merge: env values override existing AI values; existing AI values
    # are kept for fields where env has no value.
    merged: dict[str, str] = {}
    for name in _SIGNATURE_TRAILER_NAMES:
        if name in env_signature:
            merged[name] = env_signature[name]
        elif name in existing:
            merged[name] = existing[name]
    if not merged:
        return message
    # Strip all existing signature trailers, then append merged set.
    lines = _strip_signature_trailers(lines)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        lines = [""]
    lines.append("")
    for name in _SIGNATURE_TRAILER_NAMES:
        value = merged.get(name)
        if value:
            lines.append(f"{name}: {value}")
    return "\n".join(lines)


def run_prepare_commit_msg(message_file: str) -> str | None:
    """Read, transform and overwrite the commit message file in place.

    Returns ``None`` on success, or an error message string on failure.
    """

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
    parser = argparse.ArgumentParser(
        description="Inject environment-provided signature trailers into a commit message"
    )
    parser.add_argument("--message-file", required=True)
    return parser


def main(arguments: list[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    error = run_prepare_commit_msg(parsed.message_file)
    if error is not None:
        sys.stderr.write(f"LDVH prepare-commit-msg: {error}\n")
        return 0
    env = _environment_signature()
    if env:
        sys.stderr.write(
            f"LDVH prepare-commit-msg: injected {', '.join(sorted(env))} from environment\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
