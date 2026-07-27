from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.governance import configuration
from ldvh.governance.configuration import (
    CONFIGURATION_FILENAME,
    ConfigurationAccessError,
    ConfigurationStatus,
    read_governed_projects_configuration,
)


def _write_configuration(root: Path, body: str | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / CONFIGURATION_FILENAME
    path.write_text(
        body
        or """product_name: LDVH workspace
product_description: Test workspace
projects:
  - id: ldvh
    path: projects/ldvh
    name: LDVH
    description: Harness project
""",
        encoding="utf-8",
    )
    return path


def test_explicit_workspace_root_reads_only_its_current_file(tmp_path: Path) -> None:
    outer = tmp_path / "workspace"
    selected = outer / "selected"
    _write_configuration(outer)
    source = _write_configuration(selected)

    first = read_governed_projects_configuration(explicit_workspace_root=selected)
    source.write_text(source.read_text(encoding="utf-8").replace("LDVH workspace", "Current bytes"), encoding="utf-8")
    second = read_governed_projects_configuration(explicit_workspace_root=selected)

    assert first.status is ConfigurationStatus.VALID
    assert first.configuration is not None
    assert first.configuration.product_name == "LDVH workspace"
    assert second.configuration is not None
    assert second.configuration.product_name == "Current bytes"
    assert second.config_path == source.resolve()
    assert second.workspace_root == selected.resolve()
    assert second.discovered[0].bases == second.search_bases


def test_explicit_workspace_root_reports_missing_without_searching_parents(tmp_path: Path) -> None:
    outer = tmp_path / "workspace"
    selected = outer / "selected"
    selected.mkdir(parents=True)
    _write_configuration(outer)

    result = read_governed_projects_configuration(explicit_workspace_root=selected)

    assert result.status is ConfigurationStatus.MISSING
    assert result.workspace_root == selected.resolve()
    assert result.config_path is None
    assert result.discovered == ()


def test_unsupported_windows_workspace_fails_before_file_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as context:
        context.setattr(Path, "is_file", lambda _self: pytest.fail("unsupported workspace must not be observed"))
        result = read_governed_projects_configuration(
            explicit_workspace_root=Path(r"\\server\share\workspace"),
            platform_name="nt",
        )

    assert result.status is ConfigurationStatus.INVALID
    assert result.configuration is None
    assert result.diagnostics and "Windows" in result.diagnostics[0].summary


@pytest.mark.parametrize("project_path", (r"\\server\share\project", r"C:relative\project"))
def test_unsupported_windows_project_path_is_rejected_before_resolve(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    project_path: str,
) -> None:
    workspace = tmp_path / "workspace"
    source = _write_configuration(
        workspace,
        f"""product_name: Workspace
product_description: Test
projects:
  - id: project
    path: '{project_path}'
""",
    )
    monkeypatch.setattr(
        configuration,
        "_real_absolute",
        lambda _path: pytest.fail("unsupported project path must not be resolved"),
    )

    parsed, diagnostics = configuration._parse_configuration(source, workspace, platform_name="nt")

    assert parsed is None
    assert diagnostics and diagnostics[0].field == "projects[0].path"
    assert diagnostics[0].cause is not None


def test_relative_project_paths_use_the_configuration_workspace_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_configuration(workspace)

    result = read_governed_projects_configuration(path_search_starts=(workspace / "projects" / "ldvh",))

    assert result.status is ConfigurationStatus.VALID
    assert result.configuration is not None
    assert result.configuration.projects[0].path == (workspace / "projects" / "ldvh").resolve()


def test_absolute_project_path_keeps_its_actual_meaning(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project = tmp_path / "elsewhere" / "project"
    _write_configuration(
        workspace,
        f"""product_name: Workspace
product_description: Test
projects:
  - id: project
    path: {project}
""",
    )

    result = read_governed_projects_configuration(path_search_starts=(workspace,))

    assert result.configuration is not None
    assert result.configuration.projects[0].path == project.resolve()


def test_default_project_id_must_reference_a_registered_project(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_configuration(
        workspace,
        """product_name: Workspace
product_description: Test
default_project_id: project
projects:
  - id: project
    path: project
""",
    )

    valid = read_governed_projects_configuration(explicit_workspace_root=workspace)
    assert valid.configuration is not None
    assert valid.configuration.default_project_id == "project"

    _write_configuration(
        workspace,
        """product_name: Workspace
product_description: Test
default_project_id: missing
projects:
  - id: project
    path: project
""",
    )
    invalid = read_governed_projects_configuration(explicit_workspace_root=workspace)
    assert invalid.status is ConfigurationStatus.INVALID
    assert any(diagnostic.field == "default_project_id" for diagnostic in invalid.diagnostics)


@pytest.mark.parametrize(
    "body, expected_summary",
    [
        ("product_name: [", "YAML 1.2"),
        (
            """product_name: one
product_name: two
product_description: test
projects: []
""",
            "YAML 1.2",
        ),
        (
            """product_name: test
product_description: test
projects: []
extra: false
""",
            "未知字段",
        ),
        (
            """product_name: test
product_description: test
projects:
  - id: one
    path: one
    branch: main
""",
            "未知字段",
        ),
        (
            """product_name: test
product_description: test
projects: nope
""",
            "必须是列表",
        ),
        (
            """product_name: test
product_description: test
projects:
  - id: one
""",
            "缺少字段",
        ),
        (
            """product_name: test
product_description: test
projects:
  - id: one
    path: one
  - id: one
    path: two
""",
            "id 'one' 必须在全配置唯一",
        ),
        (
            """product_name: test
product_description: test
projects:
  - id: one
    path: same
  - id: two
    path: nested/../same
""",
            "规范化项目路径",
        ),
    ],
)
def test_invalid_configuration_is_reported_without_partial_configuration(
    tmp_path: Path,
    body: str,
    expected_summary: str,
) -> None:
    workspace = tmp_path / "workspace"
    _write_configuration(workspace, body)

    result = read_governed_projects_configuration(explicit_workspace_root=workspace)

    assert result.status is ConfigurationStatus.INVALID
    assert result.configuration is None
    assert result.config_path == (workspace / CONFIGURATION_FILENAME).resolve()
    assert any(expected_summary in diagnostic.summary for diagnostic in result.diagnostics)


def test_same_configuration_found_from_path_and_common_dir_basis_is_not_a_conflict(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    common_dir_parent = workspace / "repository"
    project.mkdir(parents=True)
    common_dir_parent.mkdir()
    source = _write_configuration(workspace)

    result = read_governed_projects_configuration(
        path_search_starts=(project,),
        common_dir_parent_search_starts=(common_dir_parent,),
    )

    assert result.status is ConfigurationStatus.VALID
    assert result.config_path == source.resolve()
    assert len(result.discovered) == 1
    assert {basis.kind for basis in result.discovered[0].bases} == {"path", "git.common_dir_parent"}


def test_different_real_configuration_paths_report_conflict_even_if_content_matches(tmp_path: Path) -> None:
    first_workspace = tmp_path / "first"
    second_workspace = tmp_path / "second"
    first = _write_configuration(first_workspace)
    second = _write_configuration(second_workspace)

    result = read_governed_projects_configuration(
        path_search_starts=(first_workspace,),
        common_dir_parent_search_starts=(second_workspace,),
    )

    assert result.status is ConfigurationStatus.CONFLICT
    assert result.workspace_root is None
    assert result.config_path is None
    assert result.configuration is None
    assert {candidate.path for candidate in result.discovered} == {first.resolve(), second.resolve()}


def test_symlinked_configuration_is_deduplicated_by_real_absolute_path(tmp_path: Path) -> None:
    source_workspace = tmp_path / "source"
    linked_workspace = tmp_path / "linked"
    source = _write_configuration(source_workspace)
    linked_workspace.mkdir()
    (linked_workspace / CONFIGURATION_FILENAME).symlink_to(source)

    result = read_governed_projects_configuration(
        path_search_starts=(source_workspace,),
        common_dir_parent_search_starts=(linked_workspace,),
    )

    assert result.status is ConfigurationStatus.VALID
    assert len(result.discovered) == 1
    assert result.config_path == source.resolve()
    assert len(result.discovered[0].bases) == 2


def test_automatic_discovery_skips_worktree_root_file_and_continues_upward(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    worktree = workspace / "project"
    nested = worktree / "code" / "feature"
    outer = _write_configuration(workspace)
    _write_configuration(worktree, "not: an accepted configuration\n")
    nested.mkdir(parents=True)

    result = read_governed_projects_configuration(
        path_search_starts=(nested,),
        excluded_worktree_roots=(worktree,),
    )

    assert result.status is ConfigurationStatus.VALID
    assert result.config_path == outer.resolve()
    assert {candidate.path for candidate in result.discovered} == {outer.resolve()}


def test_worktree_root_file_is_allowed_when_root_is_explicitly_selected(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    worktree = workspace / "project"
    _write_configuration(workspace)
    local = _write_configuration(worktree)

    result = read_governed_projects_configuration(
        explicit_workspace_root=worktree,
        excluded_worktree_roots=(worktree,),
    )

    assert result.status is ConfigurationStatus.VALID
    assert result.config_path == local.resolve()


def test_empty_projects_list_is_valid(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_configuration(
        workspace,
        """product_name: Empty workspace
product_description: No registered projects
projects: []
""",
    )

    result = read_governed_projects_configuration(explicit_workspace_root=workspace)

    assert result.status is ConfigurationStatus.VALID
    assert result.configuration is not None
    assert result.configuration.projects == ()


def test_io_failure_is_not_misreported_as_an_invalid_domain_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    source = _write_configuration(workspace)
    original_read_text = Path.read_text

    def fail_selected_file(path: Path, *args, **kwargs):
        if path == source.resolve():
            raise PermissionError("not readable")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_selected_file)

    with pytest.raises(ConfigurationAccessError, match="无法读取当前管辖项目配置"):
        read_governed_projects_configuration(explicit_workspace_root=workspace)


def test_non_utf8_current_file_is_invalid_configuration(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    source = _write_configuration(workspace)
    source.write_bytes(b"\xff\xfe")

    result = read_governed_projects_configuration(explicit_workspace_root=workspace)

    assert result.status is ConfigurationStatus.INVALID
    assert result.configuration is None
    assert any("UTF-8" in diagnostic.summary for diagnostic in result.diagnostics)
