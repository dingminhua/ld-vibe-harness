from __future__ import annotations

import ast
from pathlib import Path

import ldvh
from ldvh.helper.rule_source import inspect_colocated_rule_source
from ldvh.rule_source import inspect_colocated_rule_repository


def test_shared_rule_source_has_no_helper_dependency() -> None:
    source = Path(__file__).resolve().parents[1] / "ldvh/rule_source.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not any(name == "ldvh.helper" or name.startswith("ldvh.helper.") for name in imported)


def test_helper_and_shared_callers_observe_the_same_verified_repository() -> None:
    assert ldvh.__file__ is not None
    shared = inspect_colocated_rule_repository(Path(ldvh.__file__))
    helper = inspect_colocated_rule_source(Path(ldvh.__file__))

    assert shared.problem is None
    assert helper.problem is None
    assert shared.repository is not None and helper.repository is not None
    assert shared.repository.source_identity == helper.repository.source_identity
