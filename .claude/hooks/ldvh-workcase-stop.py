#!/usr/bin/env python3
"""Thin project-level Stop hook wrapper for the LDVH WorkCase gate.

Delegates to the importable implementation so the gate logic stays testable.
Reads the host Stop JSON from stdin and prints a JSON decision on stdout.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_VENV_PYTHON = _REPOSITORY_ROOT / ".venv" / "bin" / "python"
if sys.version_info < (3, 11) and _VENV_PYTHON.is_file():
    import os

    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON), str(Path(__file__).resolve())])

_CODE_ROOT = _REPOSITORY_ROOT / "code"
if str(_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(_CODE_ROOT))

from ldvh.hooks.workcase_stop import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
