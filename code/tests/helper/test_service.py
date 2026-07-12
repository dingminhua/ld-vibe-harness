from __future__ import annotations

from pathlib import Path

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.helper.operation_sources import OperationSourceInspection
from ldvh.helper.rule_source import RuleSourceResult
from ldvh.helper.service import handle_request
from ldvh.specs.repository import RepositoryInspection


def test_rule_source_location_gap_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: RuleSourceResult(None, None, "没有共置规则源"),
    )

    result = handle_request("capabilities", None, "")

    assert result.exit_code == 5
    assert result.response["outcome"] == "unavailable"
    assert result.response["gaps"][0]["summary"] == "没有共置规则源"


def test_repository_problem_is_not_rewritten_as_empty_discovery(monkeypatch, tmp_path: Path) -> None:
    issue = Issue("规则源检查失败", SourceLocation("specs/broken.md"), affected=("broken",))
    repository = RepositoryInspection(
        repository_root=tmp_path,
        candidates=(),
        parsed_documents=(),
        active_documents_passing_implemented_checks=(),
        projections=(),
        issues=(issue,),
        incomplete_scope=("broken",),
        unchecked_conditions=(),
        basis_reachability_overlaps=(),
        implemented_checks_complete=False,
    )
    operations = OperationSourceInspection((), (), (), ())
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: RuleSourceResult(repository, operations, None),
    )

    result = handle_request("capabilities", None, "")

    assert result.exit_code == 5
    assert result.response["outcome"] == "unavailable"
    assert result.response["result"] is None
    assert result.response["scope"]["not_completed"] == ["broken"]
    assert result.response["diagnostics"][0]["details"]["issues"] == ["规则源检查失败"]
