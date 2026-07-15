from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ldvh.helper.responses import common_response
from ldvh.helper.source_refs import (
    GeneratedSourceReference,
    RuleReferenceBinder,
    generated_source_reference,
    reset_reference_binder,
    set_reference_binder,
)
from ldvh.specs.repository import inspect_repository
from ldvh.specs.source import RuleSourceIdentity


def test_generated_reference_copy_keeps_the_internal_marker() -> None:
    reference = generated_source_reference("rule", "specs/01-规范模型基础规范.md")
    assert isinstance(reference, GeneratedSourceReference)
    assert isinstance(reference.copy(), GeneratedSourceReference)
    assert isinstance(copy.copy(reference), GeneratedSourceReference)
    assert isinstance(copy.deepcopy(reference), GeneratedSourceReference)


def test_rule_binder_projects_exact_view_identity(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    reference = generated_source_reference("rule", "specification-model-foundation::6.4 安装规则快照")
    working = RuleReferenceBinder(repository.source_identity, repository.parsed_documents).bind(reference)
    installed_identity = RuleSourceIdentity(
        "installed_release_snapshot",
        distribution="ld-vibe-harness",
        version="0.1.0",
        snapshot_sha256="a" * 64,
    )
    installed = RuleReferenceBinder(installed_identity, repository.parsed_documents).bind(reference)
    assert "version" not in working
    assert working["details"]["rule_source_view"] == "working_tree"
    assert "distribution" not in working["details"]
    assert installed["version"] == "0.1.0"
    assert installed["details"]["distribution"] == "ld-vibe-harness"
    assert installed["details"]["snapshot_sha256"] == "a" * 64
    assert "git_worktree_root" not in installed["details"]


def test_binder_rejects_prebound_identity(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    reference = generated_source_reference("rule", "specs/01-规范模型基础规范.md", git_worktree_root="/fake")
    with pytest.raises(ValueError, match="conflicting"):
        RuleReferenceBinder(repository.source_identity, repository.parsed_documents).bind(reference)


def test_projection_does_not_rebind_caller_rule_dict(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    assert repository.source_identity is not None
    caller = {"kind": "rule", "locator": "caller-sentinel", "details": {"owner": "caller"}}
    generated = generated_source_reference("rule", "specs/01-规范模型基础规范.md")
    token = set_reference_binder(RuleReferenceBinder(repository.source_identity, repository.parsed_documents))
    try:
        result = common_response(
            request_kind="capabilities",
            operation_key=None,
            outcome="ok",
            summary="test",
            sources=[caller, generated],
        )
    finally:
        reset_reference_binder(token)
    assert result.response["sources"][0] == caller
    assert result.response["sources"][1]["details"]["rule_source_view"] == "working_tree"


def test_generated_references_are_omitted_when_source_identity_is_unavailable() -> None:
    generated = generated_source_reference("rule", "specification-model-foundation::6.4 安装规则快照")

    result = common_response(
        request_kind="capabilities",
        operation_key=None,
        outcome="invalid_request",
        summary="test",
        sources=[generated],
        gaps=[{"summary": "identity unavailable", "scope": [], "source_refs": [generated.copy()]}],
    )

    assert result.response["sources"] == []
    assert result.response["gaps"][0]["source_refs"] == []
