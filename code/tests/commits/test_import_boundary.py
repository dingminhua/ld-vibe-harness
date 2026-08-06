"""Mechanical import boundary for the commit path (specs 03 §9.9, workcase-0022).

The commit chain (``ldvh.commits`` / ``ldvh.hooks`` / ``ldvh.git_hooks``) must
never pull in whole-repository scanning modules; full scans live only behind
their own first-class entry (``ldvh.testing.fact_integrity`` and any Helper
operation registered for it in specs 05).  This test parses module sources
with ``ast`` so the boundary is judged mechanically, not by review.
"""

from __future__ import annotations

import ast
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "ldvh"
_COMMIT_CHAIN_DIRS = ("commits", "hooks", "git_hooks")
_FULL_SCAN_PREFIXES = ("ldvh.testing.fact_integrity",)


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.append(node.module)
    return tuple(names)


def _chain_modules() -> tuple[Path, ...]:
    modules: list[Path] = []
    for directory in _COMMIT_CHAIN_DIRS:
        modules.extend(
            sorted(
                (root / name).resolve()
                for root, _, files in _PACKAGE_ROOT.joinpath(directory).walk()
                for name in files
                if name.endswith(".py")
            )
        )
    return tuple(modules)


def test_commit_chain_never_imports_full_scan_modules() -> None:
    violations: list[str] = []
    for module in _chain_modules():
        for imported in _imports(module):
            if any(imported == prefix or imported.startswith(f"{prefix}.") for prefix in _FULL_SCAN_PREFIXES):
                violations.append(f"{module.relative_to(_PACKAGE_ROOT)} imports {imported}")

    assert violations == [], f"提交链路不得引入全库扫描模块: {violations}"


def test_full_scan_entry_exists_outside_commit_chain() -> None:
    assert (_PACKAGE_ROOT / "testing" / "fact_integrity.py").is_file()
