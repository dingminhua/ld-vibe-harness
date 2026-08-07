from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

import ldvh.governance.resolver as resolver_module
from ldvh.governance.configuration import CONFIGURATION_FILENAME, ConfigurationAccessError
from ldvh.governance.git import GitIdentityResolution, PathObservation, TechnicalFailure
from ldvh.governance.models import ConfigStatus, GovernedVia, LocatorSource, ObjectStatus, ScopeDescriptor, ScopeStatus
from ldvh.governance.resolver import TechnicalOutcome, resolve_governance_scope


def _git(path: Path, *arguments: str) -> str:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "LDVH Test",
            "GIT_AUTHOR_EMAIL": "ldvh@example.invalid",
            "GIT_COMMITTER_NAME": "LDVH Test",
            "GIT_COMMITTER_EMAIL": "ldvh@example.invalid",
        }
    )
    completed = subprocess.run(
        ["git", "-C", str(path), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return completed.stdout.strip()


def _repository(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    (path / "tracked.txt").write_text("initial\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-qm", "initial")
    return path


def _configuration(root: Path, projects: list[tuple[str, Path]], *, body: str | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if body is None:
        entries = "\n".join(f"  - id: {project_id}\n    path: {path}" for project_id, path in projects)
        body = f"product_name: Test\nproduct_description: Test workspace\nprojects:\n{entries}\n"
    source = root / CONFIGURATION_FILENAME
    source.write_text(body, encoding="utf-8")
    return source


def _scope(*locators: str) -> tuple[ScopeDescriptor, ...]:
    return tuple(
        ScopeDescriptor(index, locator, LocatorSource.EXPLICIT_LOCATOR) for index, locator in enumerate(locators)
    )


def test_discovers_external_configuration_from_upper_workspace_cwd(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repository = _repository(workspace / "project")
    source = _configuration(workspace, [("project", repository)])

    run = resolve_governance_scope(_scope("project/tracked.txt"), base=workspace)

    assert run.result is not None
    assert run.result.config_path == str(source.resolve())
    assert run.result.scope_status is ScopeStatus.GOVERNED_SINGLE
    item = run.result.object_resolutions[0]
    assert item.status is ObjectStatus.GOVERNED
    assert item.governed_via is GovernedVia.PATH
    assert item.git_worktree_root == str(repository.resolve())
    assert [candidate.governed_project_id for candidate in run.result.registered_project_candidates] == ["project"]
    candidate = run.result.registered_project_candidates[0]
    assert candidate.registered_project_path == str(repository.resolve())
    assert candidate.git_worktree_root == str(repository.resolve())
    assert {source["kind"] for source in candidate.source_refs} == {
        "governed_projects_configuration",
        "registered_project_git_identity",
    }
    config_source = next(source for source in run.sources if source["kind"] == "governed_projects_configuration")
    assert {basis["kind"] for basis in config_source["details"]["discovery_bases"]} == {"path"}


def test_unsupported_windows_explicit_workspace_fails_before_locator_or_configuration_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resolver_module, "windows_path_problem", lambda _path: "UNC is unsupported")
    monkeypatch.setattr(
        resolver_module,
        "resolve_git_identity",
        lambda *args, **kwargs: pytest.fail("unsupported workspace must fail before Git identity"),
    )
    monkeypatch.setattr(
        resolver_module,
        "read_governed_projects_configuration",
        lambda *args, **kwargs: pytest.fail("unsupported workspace must fail before configuration access"),
    )

    run = resolve_governance_scope(
        _scope(str(tmp_path / "local-object")),
        base=tmp_path,
        explicit_workspace_root=Path(r"\\server\share\workspace"),
    )

    assert run.result is None
    assert run.technical_non_completions[0].stage == "configuration_discovery"


def test_upper_workspace_cwd_is_an_object_not_a_guessed_child_project(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repository = _repository(workspace / "project")
    _configuration(workspace, [("project", repository)])
    requested = (ScopeDescriptor(0, str(workspace), LocatorSource.CWD),)

    run = resolve_governance_scope(requested, base=workspace)

    assert run.result is not None
    assert run.result.scope_status is ScopeStatus.NON_GOVERNED
    assert run.result.object_resolutions[0].status is ObjectStatus.NOT_GOVERNED
    assert run.result.object_resolutions[0].governed_project_id is None
    assert [candidate.governed_project_id for candidate in run.result.registered_project_candidates] == ["project"]


def test_linked_worktree_uses_nearest_parent_configuration_then_common_dir_match(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    main = _repository(workspace / "main")
    linked = workspace / "linked"
    _git(main, "worktree", "add", "-qb", "linked-test", str(linked))
    outer = _configuration(workspace, [("ldvh", main)])

    run = resolve_governance_scope(_scope(str(linked / "tracked.txt")), base=tmp_path)

    assert run.result is not None
    assert run.result.config_path == str(outer.resolve())
    item = run.result.object_resolutions[0]
    assert item.status is ObjectStatus.GOVERNED
    assert item.governed_via is GovernedVia.GIT_COMMON_DIR
    assert item.registered_project_path == str(main.resolve())
    assert item.git_worktree_root == str(linked.resolve())
    config_sources = [source for source in run.sources if source["kind"] == "governed_projects_configuration"]
    assert len(config_sources) == 1
    assert {basis["kind"] for basis in config_sources[0]["details"]["discovery_bases"]} == {"path"}
    registered_sources = [source for source in run.sources if source["kind"] == "registered_project_git_identity"]
    assert len(registered_sources) == 1
    assert registered_sources[0]["locator"] == str(main.resolve())
    assert registered_sources[0]["details"]["git_common_dir"] == item.git_common_dir
    assert any(source["kind"] == "registered_project_git_identity" for source in item.identity_evidence)


def test_nearest_valid_unregistered_configuration_fails_closed_without_climbing(tmp_path: Path) -> None:
    outer = tmp_path / "outer"
    inner = outer / "inner"
    repository = _repository(inner / "repository")
    outer_source = _configuration(outer, [("repository", repository)])
    inner_source = _configuration(
        inner,
        [],
        body="product_name: Test\nproduct_description: Test workspace\nprojects: []\n",
    )

    run = resolve_governance_scope(_scope(str(repository / "tracked.txt")), base=tmp_path)

    assert run.result is not None
    assert run.result.config_status is ConfigStatus.VALID
    assert run.result.config_path == str(inner_source.resolve())
    assert run.result.scope_status is ScopeStatus.NON_GOVERNED
    assert run.result.object_resolutions[0].status is ObjectStatus.NOT_GOVERNED
    assert str(outer_source.resolve()) not in [source["locator"] for source in run.sources]


def test_nearest_invalid_configuration_stops_before_outer_configuration(tmp_path: Path) -> None:
    outer = tmp_path / "outer"
    inner = outer / "inner"
    repository = _repository(inner / "repository")
    _configuration(outer, [("repository", repository)])
    inner_source = _configuration(inner, [], body="product_name: [\n")

    run = resolve_governance_scope(_scope(str(repository / "tracked.txt")), base=tmp_path)

    assert run.result is not None
    assert run.result.config_status is ConfigStatus.INVALID
    assert run.result.config_path == str(inner_source.resolve())
    assert run.result.scope_status is ScopeStatus.SCOPE_UNKNOWN


def test_single_worktree_automatic_discovery_reports_missing_without_common_dir_fallback(tmp_path: Path) -> None:
    main = _repository(tmp_path / "main")
    linked = tmp_path / "external" / "linked"
    linked.parent.mkdir()
    _git(main, "worktree", "add", "-qb", "linked-test", str(linked))

    run = resolve_governance_scope(_scope(str(linked / "tracked.txt")), base=tmp_path)

    assert run.result is not None
    assert run.result.config_status is ConfigStatus.MISSING
    assert run.result.scope_status is ScopeStatus.SCOPE_UNKNOWN


def test_single_worktree_skips_its_root_configuration_before_selecting_parent(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repository = _repository(workspace / "repository")
    outer = _configuration(workspace, [("repository", repository)])
    _configuration(repository, [], body="not: a governed projects configuration\n")

    run = resolve_governance_scope(_scope(str(repository / "tracked.txt")), base=tmp_path)

    assert run.result is not None
    assert run.result.config_path == str(outer.resolve())
    assert run.result.object_resolutions[0].status is ObjectStatus.GOVERNED


def test_single_worktree_skips_an_independently_nested_ancestor_repository_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outer = _repository(workspace / "outer")
    child = _repository(outer / "child")
    source = _configuration(workspace, [("child", child)])
    _configuration(outer, [], body="not: a governed projects configuration\n")

    run = resolve_governance_scope(_scope(str(child / "tracked.txt")), base=tmp_path)

    assert run.result is not None
    assert run.result.config_path == str(source.resolve())
    assert run.result.object_resolutions[0].status is ObjectStatus.GOVERNED


def test_single_worktree_starts_at_the_actual_root_not_a_locator_child(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repository = _repository(workspace / "repository")
    source = _configuration(workspace, [("repository", repository)])
    nested = repository / "nested"
    nested.mkdir()
    _configuration(nested, [], body="product_name: [\n")
    target = nested / "new-file.txt"

    run = resolve_governance_scope(_scope(str(target)), base=tmp_path)

    assert run.result is not None
    assert run.result.config_path == str(source.resolve())
    assert run.result.object_resolutions[0].status is ObjectStatus.GOVERNED


def test_main_and_linked_inputs_are_preserved_and_aggregate_to_one_project(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    main = _repository(workspace / "main")
    linked = tmp_path / "linked"
    _git(main, "worktree", "add", "-qb", "linked-test", str(linked))
    _configuration(workspace, [("ldvh", main)])

    run = resolve_governance_scope(
        _scope(str(main / "tracked.txt"), str(linked / "tracked.txt"), str(linked / "tracked.txt")),
        base=workspace,
    )

    assert run.result is not None
    assert run.result.scope_status is ScopeStatus.GOVERNED_SINGLE
    assert [item.locator_index for item in run.result.object_resolutions] == [0, 1, 2]
    assert [item.governed_via for item in run.result.object_resolutions] == [
        GovernedVia.PATH,
        GovernedVia.GIT_COMMON_DIR,
        GovernedVia.GIT_COMMON_DIR,
    ]
    assert run.completed_scope == run.requested_scope
    assert run.not_completed_scope == ()


def test_independent_clone_with_same_source_is_not_governed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    registered = _repository(workspace / "registered")
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "-q", str(registered), str(clone))
    _configuration(workspace, [("registered", registered)])

    run = resolve_governance_scope(
        _scope(str(clone / "tracked.txt")),
        base=tmp_path,
        explicit_workspace_root=workspace,
    )

    assert run.result is not None
    item = run.result.object_resolutions[0]
    assert item.status is ObjectStatus.NOT_GOVERNED
    assert item.git_common_dir != str((registered / ".git").resolve())


def test_parent_path_does_not_cross_a_submodule_git_boundary(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    child_source = _repository(tmp_path / "child-source")
    parent = _repository(workspace / "parent")
    _git(parent, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(child_source), "vendor/child")
    child = parent / "vendor" / "child"
    outer = _configuration(workspace, [("parent", parent)])
    common_dir = Path(_git(child, "rev-parse", "--git-common-dir"))
    if not common_dir.is_absolute():
        common_dir = child / common_dir
    metadata_candidate = common_dir.resolve().parent / CONFIGURATION_FILENAME
    metadata_candidate.write_text("not: a workspace configuration\n", encoding="utf-8")
    _configuration(parent, [], body="also: project-local, not workspace configuration\n")

    run = resolve_governance_scope(_scope(str(child / "tracked.txt")), base=workspace)

    assert run.result is not None
    assert run.result.config_path == str(outer.resolve())
    item = run.result.object_resolutions[0]
    assert item.status is ObjectStatus.NOT_GOVERNED
    assert item.git_worktree_root == str(child.resolve())


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        ("missing", ConfigStatus.MISSING),
        ("invalid", ConfigStatus.INVALID),
    ],
)
def test_complete_non_valid_configuration_returns_unknown_domain_results(
    tmp_path: Path,
    setup: str,
    expected: ConfigStatus,
) -> None:
    workspace = tmp_path / "workspace"
    repository = _repository(workspace / "repository")
    if setup == "invalid":
        _configuration(workspace, [], body="product_name: [\n")

    run = resolve_governance_scope(
        _scope(str(repository / "tracked.txt")),
        base=workspace,
        explicit_workspace_root=workspace,
    )

    assert run.result is not None
    assert run.result.config_status is expected
    assert run.result.scope_status is ScopeStatus.SCOPE_UNKNOWN
    assert run.result.object_resolutions[0].status is ObjectStatus.UNKNOWN
    assert run.result.registered_project_candidates == ()
    assert run.completed_scope == run.requested_scope
    assert run.technical_non_completions == ()


def test_automatic_discovery_conflict_is_a_complete_unknown_domain_result(tmp_path: Path) -> None:
    first_workspace = tmp_path / "first-workspace"
    second_workspace = tmp_path / "second-workspace"
    first = _repository(first_workspace / "first")
    second = _repository(second_workspace / "second")
    _configuration(first_workspace, [("first", first)])
    _configuration(second_workspace, [("second", second)])

    run = resolve_governance_scope(
        _scope(str(first / "tracked.txt"), str(second / "tracked.txt")),
        base=tmp_path,
    )

    assert run.result is not None
    assert run.result.config_status is ConfigStatus.CONFLICT
    assert all(item.status is ObjectStatus.UNKNOWN for item in run.result.object_resolutions)
    assert run.result.registered_project_candidates == ()
    assert len([source for source in run.sources if source["kind"] == "governed_projects_configuration"]) == 2


def test_registration_must_be_an_actual_worktree_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repository = _repository(workspace / "repository")
    _configuration(workspace, [("nested", repository / "nested")])
    (repository / "nested").mkdir()

    run = resolve_governance_scope(
        _scope(str(repository / "tracked.txt")),
        base=workspace,
        explicit_workspace_root=workspace,
    )

    assert run.result is not None
    assert run.result.config_status is ConfigStatus.INVALID
    assert run.result.object_resolutions[0].status is ObjectStatus.UNKNOWN
    assert run.result.registered_project_candidates == ()
    assert any("actual Git worktree root" in item.summary for item in run.diagnostics)


def test_registration_common_dirs_must_be_unique(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    main = _repository(workspace / "main")
    linked = workspace / "linked"
    _git(main, "worktree", "add", "-qb", "linked-test", str(linked))
    _configuration(workspace, [("main", main), ("linked", linked)])

    run = resolve_governance_scope(
        _scope(str(main / "tracked.txt")),
        base=workspace,
        explicit_workspace_root=workspace,
    )

    assert run.result is not None
    assert run.result.config_status is ConfigStatus.INVALID
    assert run.result.registered_project_candidates == ()
    assert any("common directories" in item.summary for item in run.diagnostics)


def test_mixed_and_multiple_project_aggregation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    first = _repository(workspace / "first")
    second = _repository(workspace / "second")
    plain = workspace / "plain"
    plain.mkdir()
    _configuration(workspace, [("first", first), ("second", second)])

    multiple = resolve_governance_scope(
        _scope(str(first / "tracked.txt"), str(second / "tracked.txt")),
        base=workspace,
        explicit_workspace_root=workspace,
    )
    mixed = resolve_governance_scope(
        _scope(str(first / "tracked.txt"), str(plain)),
        base=workspace,
        explicit_workspace_root=workspace,
    )

    assert multiple.result is not None
    assert multiple.result.scope_status is ScopeStatus.MULTIPLE_GOVERNED_PROJECTS
    assert [candidate.governed_project_id for candidate in multiple.result.registered_project_candidates] == [
        "first",
        "second",
    ]
    assert mixed.result is not None
    assert mixed.result.scope_status is ScopeStatus.MIXED_SCOPE


def test_explicit_root_allows_partial_completion_for_one_git_dependency_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    repository = _repository(workspace / "repository")
    _configuration(workspace, [("repository", repository)])
    original = resolver_module.resolve_git_identity

    def selective_failure(locator: str, *, base: str | Path) -> GitIdentityResolution:
        if locator != "broken":
            return original(locator, base=base)
        absolute = (Path(base) / locator).absolute()
        return GitIdentityResolution(
            status="technical_failure",
            path=PathObservation(locator, str(base), absolute, None, None, False, False),
            failure=TechnicalFailure("git_dependency", "Git executable is unavailable", "raw secret detail"),
        )

    monkeypatch.setattr(resolver_module, "resolve_git_identity", selective_failure)
    run = resolve_governance_scope(
        _scope(str(repository / "tracked.txt"), "broken"),
        base=workspace,
        explicit_workspace_root=workspace,
    )

    assert run.result is not None
    assert [item.locator_index for item in run.result.object_resolutions] == [0]
    assert run.completed_scope == (run.requested_scope[0],)
    assert run.not_completed_scope == (run.requested_scope[1],)
    assert run.technical_non_completions[0].outcome is TechnicalOutcome.UNAVAILABLE
    assert "raw secret detail" not in repr(run.diagnostics)
    assert "raw secret detail" not in repr(run.gaps)


@pytest.mark.parametrize(
    ("configuration_case", "expected_status"),
    [("missing", ConfigStatus.MISSING), ("invalid_project", ConfigStatus.INVALID)],
)
def test_non_valid_configuration_does_not_hide_a_locator_technical_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    configuration_case: str,
    expected_status: ConfigStatus,
) -> None:
    workspace = tmp_path / "workspace"
    repository = _repository(workspace / "repository")
    if configuration_case == "invalid_project":
        nested = repository / "nested"
        nested.mkdir()
        _configuration(workspace, [("repository", nested)])
    original = resolver_module.resolve_git_identity

    def selective_failure(locator: str, *, base: str | Path) -> GitIdentityResolution:
        if locator != "broken":
            return original(locator, base=base)
        absolute = (Path(base) / locator).absolute()
        return GitIdentityResolution(
            status="technical_failure",
            path=PathObservation(locator, str(base), absolute, None, None, False, False),
            failure=TechnicalFailure("git_dependency", "Git executable is unavailable", "raw secret detail"),
        )

    monkeypatch.setattr(resolver_module, "resolve_git_identity", selective_failure)
    run = resolve_governance_scope(
        _scope(str(repository / "tracked.txt"), "broken"),
        base=workspace,
        explicit_workspace_root=workspace,
    )

    assert run.result is not None
    assert run.result.config_status is expected_status
    assert [item.locator_index for item in run.result.object_resolutions] == [0]
    assert run.result.object_resolutions[0].status is ObjectStatus.UNKNOWN
    assert run.completed_scope == (run.requested_scope[0],)
    assert run.not_completed_scope == (run.requested_scope[1],)
    assert run.technical_non_completions[0].outcome is TechnicalOutcome.UNAVAILABLE
    assert "raw secret detail" not in repr(run.diagnostics)


def test_missing_configuration_with_only_a_technical_failure_has_no_domain_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    def fail(locator: str, *, base: str | Path) -> GitIdentityResolution:
        absolute = (Path(base) / locator).absolute()
        return GitIdentityResolution(
            status="technical_failure",
            path=PathObservation(locator, str(base), absolute, None, None, False, False),
            failure=TechnicalFailure("git_dependency", "Git executable is unavailable", "raw secret detail"),
        )

    monkeypatch.setattr(resolver_module, "resolve_git_identity", fail)
    run = resolve_governance_scope(
        _scope("broken"),
        base=workspace,
        explicit_workspace_root=workspace,
    )

    assert run.result is None
    assert run.completed_scope == ()
    assert run.not_completed_scope == run.requested_scope
    assert run.technical_non_completions[0].outcome is TechnicalOutcome.UNAVAILABLE


def test_configuration_read_failure_has_no_domain_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    repository = _repository(workspace / "repository")
    _configuration(workspace, [("repository", repository)])

    def fail(**_: object) -> None:
        raise ConfigurationAccessError("raw configuration error")

    monkeypatch.setattr(resolver_module, "read_governed_projects_configuration", fail)
    run = resolve_governance_scope(
        _scope(str(repository)),
        base=workspace,
        explicit_workspace_root=workspace,
    )

    assert run.result is None
    assert run.completed_scope == ()
    assert run.not_completed_scope == run.requested_scope
    assert run.technical_non_completions[0].outcome is TechnicalOutcome.ERROR
    assert "raw configuration error" not in repr(run.diagnostics)


def test_sources_are_timestamped_and_domain_result_cannot_cross_read_worktree_content(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    main = _repository(workspace / "main")
    linked = tmp_path / "linked"
    _git(main, "worktree", "add", "-qb", "linked-test", str(linked))
    _configuration(workspace, [("ldvh", main)])
    (main / "only-main.txt").write_text("main\n", encoding="utf-8")
    (linked / "only-linked.txt").write_text("linked\n", encoding="utf-8")

    run = resolve_governance_scope(
        _scope(str(linked / "only-linked.txt")),
        base=linked,
        explicit_workspace_root=workspace,
    )

    assert run.result is not None
    serialized = run.result.to_json()
    assert "only-main" not in repr(serialized)
    assert serialized["object_resolutions"][0]["git_worktree_root"] == str(linked.resolve())
    assert all(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}", source["observed_at"])
        for source in run.sources
    )
    with pytest.raises(TypeError):
        run.sources[0]["kind"] = "changed"  # type: ignore[index]
