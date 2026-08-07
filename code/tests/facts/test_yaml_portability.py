"""Verify all YAML fact files can be parsed by both PyYAML and js-yaml.

The Python backend uses PyYAML/ruamel.yaml; the Web frontend uses js-yaml.
These parsers handle edge cases (e.g. unescaped quotes in double-quoted strings)
differently.  A file that parses in one may fail in the other.

This test runs js-yaml on every .yaml file under ldvh-base/ to catch
cross-parser incompatibilities before they reach the Web UI.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LDVH_BASE = PROJECT_ROOT / "ldvh-base"
SCRIPT = Path(__file__).resolve().parent / "_check_yaml.js"
NODE_PATH = str(PROJECT_ROOT / "web" / "node_modules")

_NODE = shutil.which("node")


def test_all_yaml_files_parse_in_js_yaml() -> None:
    """Every .yaml file under ldvh-base/ must parse without error in js-yaml."""
    assert SCRIPT.is_file(), f"js-yaml check script not found at {SCRIPT}"
    assert LDVH_BASE.is_dir(), f"ldvh-base not found at {LDVH_BASE}"
    assert _NODE is not None, "node is required for this test"

    env = {**os.environ, "NODE_PATH": NODE_PATH}
    completed = subprocess.run(
        [_NODE, str(SCRIPT), str(LDVH_BASE)],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )

    if completed.returncode != 0:
        detail = completed.stdout + completed.stderr
        raise AssertionError(
            f"One or more YAML files failed js-yaml parsing:\n{detail}"
        )
