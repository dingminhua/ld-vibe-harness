"""Read and discover the current governed-projects configuration.

This module deliberately owns no Git behavior.  Callers resolve Git worktree
and common-dir facts and pass only the resulting search boundaries here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ruamel.yaml import YAML

from ldvh.governance.git import windows_path_problem
from ldvh.governance.models import ConfigStatus

CONFIGURATION_FILENAME = "LDVH-GOVERNED-PROJECTS.yaml"

_REQUIRED_ROOT_FIELDS = frozenset({"product_name", "product_description", "projects"})
_OPTIONAL_ROOT_FIELDS = frozenset({"default_project_id"})
_ROOT_FIELDS = _REQUIRED_ROOT_FIELDS | _OPTIONAL_ROOT_FIELDS
_PROJECT_REQUIRED_FIELDS = frozenset({"id", "path"})
_PROJECT_OPTIONAL_FIELDS = frozenset({"name", "description"})
_PROJECT_FIELDS = _PROJECT_REQUIRED_FIELDS | _PROJECT_OPTIONAL_FIELDS

DiscoveryKind = Literal["explicit_workspace_root", "path", "git.common_dir_parent"]


ConfigurationStatus = ConfigStatus


class ConfigurationAccessError(OSError):
    """The selected current file could not be read to completion."""


@dataclass(frozen=True, slots=True)
class ConfigurationDiagnostic:
    """A local, source-bound configuration problem."""

    summary: str
    path: Path | None = None
    field: str | None = None
    cause: str | None = None


@dataclass(frozen=True, slots=True)
class ConfigurationSearchBasis:
    """One caller-supplied basis used during configuration discovery."""

    kind: DiscoveryKind
    start: Path


@dataclass(frozen=True, slots=True)
class DiscoveredConfiguration:
    """One unique configuration path with every basis that found it."""

    path: Path
    bases: tuple[ConfigurationSearchBasis, ...]


@dataclass(frozen=True, slots=True)
class GovernedProjectRegistration:
    """One project entry after path normalization."""

    project_id: str
    path: Path
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class GovernedProjectsConfiguration:
    """A valid current Working Tree configuration."""

    product_name: str
    product_description: str
    default_project_id: str | None
    projects: tuple[GovernedProjectRegistration, ...]
    workspace_root: Path
    source_path: Path


@dataclass(frozen=True, slots=True)
class ConfigurationReadResult:
    """The complete immutable discovery and parsing result."""

    status: ConfigurationStatus
    workspace_root: Path | None
    config_path: Path | None
    configuration: GovernedProjectsConfiguration | None
    search_bases: tuple[ConfigurationSearchBasis, ...]
    discovered: tuple[DiscoveredConfiguration, ...]
    diagnostics: tuple[ConfigurationDiagnostic, ...]


def _real_absolute(path: Path) -> Path:
    return path.resolve(strict=False)


def _search_boundary(path: Path) -> Path:
    absolute = _real_absolute(path)
    return absolute.parent if absolute.is_file() else absolute


def _ancestors(start: Path) -> tuple[Path, ...]:
    boundary = _search_boundary(start)
    return (boundary, *boundary.parents)


def _discover(
    *,
    explicit_workspace_root: Path | None,
    path_search_starts: Sequence[Path],
    common_dir_parent_search_starts: Sequence[Path],
    excluded_worktree_roots: Sequence[Path],
    nearest_ancestor_only: bool,
) -> tuple[
    tuple[ConfigurationSearchBasis, ...],
    tuple[DiscoveredConfiguration, ...],
    Path | None,
]:
    if explicit_workspace_root is not None:
        root = _real_absolute(explicit_workspace_root)
        basis = ConfigurationSearchBasis("explicit_workspace_root", root)
        candidate = root / CONFIGURATION_FILENAME
        if not candidate.is_file():
            return (basis,), (), root
        discovered = DiscoveredConfiguration(_real_absolute(candidate), (basis,))
        return (basis,), (discovered,), root

    if nearest_ancestor_only:
        if len(path_search_starts) != 1 or common_dir_parent_search_starts:
            raise ValueError("nearest ancestor discovery requires exactly one path start and no common-dir start")
        basis = ConfigurationSearchBasis("path", _search_boundary(path_search_starts[0]))
        excluded = {_real_absolute(root) for root in excluded_worktree_roots}
        for directory in _ancestors(basis.start):
            candidate = directory / CONFIGURATION_FILENAME
            if not candidate.is_file() or _real_absolute(directory) in excluded:
                continue
            discovered = DiscoveredConfiguration(_real_absolute(candidate), (basis,))
            return (basis,), (discovered,), None
        return (basis,), (), None

    bases = tuple(ConfigurationSearchBasis("path", _search_boundary(start)) for start in path_search_starts) + tuple(
        ConfigurationSearchBasis("git.common_dir_parent", _search_boundary(start))
        for start in common_dir_parent_search_starts
    )
    excluded = {_real_absolute(root) for root in excluded_worktree_roots}
    found: dict[Path, list[ConfigurationSearchBasis]] = {}

    for basis in bases:
        for directory in _ancestors(basis.start):
            candidate = directory / CONFIGURATION_FILENAME
            if not candidate.is_file() or _real_absolute(directory) in excluded:
                continue
            real_candidate = _real_absolute(candidate)
            candidate_bases = found.setdefault(real_candidate, [])
            if basis not in candidate_bases:
                candidate_bases.append(basis)

    discovered = tuple(
        DiscoveredConfiguration(path, tuple(candidate_bases))
        for path, candidate_bases in sorted(found.items(), key=lambda item: str(item[0]))
    )
    return bases, discovered, None


def _diagnostic(
    summary: str,
    source_path: Path,
    *,
    field: str | None = None,
    cause: str | None = None,
) -> ConfigurationDiagnostic:
    return ConfigurationDiagnostic(summary=summary, path=source_path, field=field, cause=cause)


def _non_empty_string(
    value: object,
    field: str,
    source_path: Path,
    diagnostics: list[ConfigurationDiagnostic],
) -> str | None:
    if not isinstance(value, str) or not value.strip():
        diagnostics.append(_diagnostic(f"字段 {field!r} 必须是非空字符串", source_path, field=field))
        return None
    return value


def _parse_configuration(
    source_path: Path,
    workspace_root: Path,
    *,
    platform_name: str | None = None,
) -> tuple[GovernedProjectsConfiguration | None, tuple[ConfigurationDiagnostic, ...]]:
    diagnostics: list[ConfigurationDiagnostic] = []
    yaml = YAML(typ="safe")
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False

    try:
        text = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationAccessError(f"无法读取当前管辖项目配置 {source_path}: {exc}") from exc
    except UnicodeError as exc:
        return None, (_diagnostic("管辖项目配置必须是有效 UTF-8 文本", source_path, cause=str(exc)),)

    try:
        loaded = yaml.load(text)
    except Exception as exc:  # ruamel exposes several parser/scanner exception types
        return None, (_diagnostic("管辖项目配置无法按 YAML 1.2 唯一解析", source_path, cause=str(exc)),)

    if not isinstance(loaded, Mapping):
        return None, (_diagnostic("管辖项目配置根必须是映射", source_path),)

    actual_root_fields = set(loaded)
    if not _REQUIRED_ROOT_FIELDS.issubset(actual_root_fields) or actual_root_fields - _ROOT_FIELDS:
        missing = sorted(_REQUIRED_ROOT_FIELDS - actual_root_fields, key=str)
        unknown = sorted(actual_root_fields - _ROOT_FIELDS, key=str)
        if missing:
            diagnostics.append(_diagnostic(f"配置根缺少字段: {missing!r}", source_path))
        if unknown:
            diagnostics.append(_diagnostic(f"配置根包含未知字段: {unknown!r}", source_path))

    product_name = _non_empty_string(loaded.get("product_name"), "product_name", source_path, diagnostics)
    product_description = _non_empty_string(
        loaded.get("product_description"), "product_description", source_path, diagnostics
    )
    raw_projects = loaded.get("projects")
    if not isinstance(raw_projects, list):
        diagnostics.append(_diagnostic("字段 'projects' 必须是列表", source_path, field="projects"))
        raw_projects = []

    projects: list[GovernedProjectRegistration] = []
    ids: set[str] = set()
    normalized_paths: set[Path] = set()
    for index, raw_project in enumerate(raw_projects):
        project_field = f"projects[{index}]"
        if not isinstance(raw_project, Mapping):
            diagnostics.append(_diagnostic(f"{project_field} 必须是映射", source_path, field=project_field))
            continue

        actual_project_fields = set(raw_project)
        missing = sorted(_PROJECT_REQUIRED_FIELDS - actual_project_fields, key=str)
        unknown = sorted(actual_project_fields - _PROJECT_FIELDS, key=str)
        if missing:
            diagnostics.append(_diagnostic(f"{project_field} 缺少字段: {missing!r}", source_path, field=project_field))
        if unknown:
            diagnostics.append(
                _diagnostic(f"{project_field} 包含未知字段: {unknown!r}", source_path, field=project_field)
            )

        project_id = _non_empty_string(raw_project.get("id"), f"{project_field}.id", source_path, diagnostics)
        raw_path = _non_empty_string(raw_project.get("path"), f"{project_field}.path", source_path, diagnostics)
        name = None
        if "name" in raw_project:
            name = _non_empty_string(raw_project.get("name"), f"{project_field}.name", source_path, diagnostics)
        description = None
        if "description" in raw_project:
            description = _non_empty_string(
                raw_project.get("description"),
                f"{project_field}.description",
                source_path,
                diagnostics,
            )

        if project_id is not None:
            if project_id in ids:
                diagnostics.append(
                    _diagnostic(
                        f"管辖项目 id {project_id!r} 必须在全配置唯一",
                        source_path,
                        field=f"{project_field}.id",
                    )
                )
            ids.add(project_id)

        normalized_path = None
        if raw_path is not None:
            path_problem = windows_path_problem(raw_path, platform_name=platform_name)
            if path_problem is not None:
                diagnostics.append(
                    _diagnostic(
                        f"{project_field}.path 在 Windows 上不受支持",
                        source_path,
                        field=f"{project_field}.path",
                        cause=path_problem,
                    )
                )
            else:
                candidate_path = Path(raw_path)
                if not candidate_path.is_absolute():
                    candidate_path = workspace_root / candidate_path
                normalized_path = _real_absolute(candidate_path)
                if normalized_path in normalized_paths:
                    diagnostics.append(
                        _diagnostic(
                            f"规范化项目路径 {str(normalized_path)!r} 必须在全配置唯一",
                            source_path,
                            field=f"{project_field}.path",
                        )
                    )
                normalized_paths.add(normalized_path)

        if project_id is not None and normalized_path is not None:
            projects.append(
                GovernedProjectRegistration(
                    project_id=project_id,
                    path=normalized_path,
                    name=name,
                    description=description,
                )
            )

    default_project_id = None
    if "default_project_id" in loaded:
        default_project_id = _non_empty_string(
            loaded.get("default_project_id"), "default_project_id", source_path, diagnostics
        )
        if not raw_projects:
            diagnostics.append(
                _diagnostic("projects 为空时不得设置 default_project_id", source_path, field="default_project_id")
            )
        elif default_project_id is not None and default_project_id not in ids:
            diagnostics.append(
                _diagnostic(
                    "default_project_id 必须引用已登记项目的 id",
                    source_path,
                    field="default_project_id",
                )
            )

    if diagnostics or product_name is None or product_description is None:
        return None, tuple(diagnostics)
    return (
        GovernedProjectsConfiguration(
            product_name=product_name,
            product_description=product_description,
            default_project_id=default_project_id,
            projects=tuple(projects),
            workspace_root=workspace_root,
            source_path=source_path,
        ),
        (),
    )


def read_governed_projects_configuration(
    *,
    explicit_workspace_root: Path | None = None,
    path_search_starts: Sequence[Path] = (),
    common_dir_parent_search_starts: Sequence[Path] = (),
    excluded_worktree_roots: Sequence[Path] = (),
    nearest_ancestor_only: bool = False,
    platform_name: str | None = None,
) -> ConfigurationReadResult:
    """Discover and parse the current configuration without running Git.

    Automatic discovery normally treats the supplied starts as directory
    boundaries.  ``nearest_ancestor_only`` instead accepts one path start and
    stops at the first eligible configuration on that one ancestor chain.
    The caller is responsible for deriving the search boundary and the set of
    Git worktree roots whose repository-local configuration files must not
    participate in automatic discovery.
    """

    inputs: list[tuple[str, Path]] = []
    if explicit_workspace_root is not None:
        inputs.append(("explicit_workspace_root", explicit_workspace_root))
    inputs.extend(("path", path) for path in path_search_starts)
    inputs.extend(("git.common_dir_parent", path) for path in common_dir_parent_search_starts)
    inputs.extend(("excluded_worktree_root", path) for path in excluded_worktree_roots)
    for kind, path in inputs:
        path_problem = windows_path_problem(path, platform_name=platform_name)
        if path_problem is None:
            continue
        root = Path(explicit_workspace_root) if explicit_workspace_root is not None else None
        search_bases: list[ConfigurationSearchBasis] = []
        if root is not None:
            search_bases.append(ConfigurationSearchBasis("explicit_workspace_root", root))
        search_bases.extend(ConfigurationSearchBasis("path", path) for path in path_search_starts)
        search_bases.extend(
            ConfigurationSearchBasis("git.common_dir_parent", path) for path in common_dir_parent_search_starts
        )
        return ConfigurationReadResult(
            status=ConfigurationStatus.INVALID,
            workspace_root=root,
            config_path=None,
            configuration=None,
            search_bases=tuple(search_bases),
            discovered=(),
            diagnostics=(
                ConfigurationDiagnostic(
                    summary=f"配置发现路径 {kind!r} 在 Windows 上不受支持",
                    path=Path(path),
                    cause=path_problem,
                ),
            ),
        )

    bases, discovered, selected_root = _discover(
        explicit_workspace_root=explicit_workspace_root,
        path_search_starts=path_search_starts,
        common_dir_parent_search_starts=common_dir_parent_search_starts,
        excluded_worktree_roots=excluded_worktree_roots,
        nearest_ancestor_only=nearest_ancestor_only,
    )
    if not discovered:
        return ConfigurationReadResult(
            status=ConfigurationStatus.MISSING,
            workspace_root=selected_root,
            config_path=None,
            configuration=None,
            search_bases=bases,
            discovered=(),
            diagnostics=(),
        )
    if len(discovered) > 1:
        return ConfigurationReadResult(
            status=ConfigurationStatus.CONFLICT,
            workspace_root=None,
            config_path=None,
            configuration=None,
            search_bases=bases,
            discovered=discovered,
            diagnostics=(
                ConfigurationDiagnostic(
                    summary="自动发现到多个不同的管辖项目配置，不能静默选择",
                ),
            ),
        )

    source_path = discovered[0].path
    workspace_root = selected_root if selected_root is not None else source_path.parent
    configuration, diagnostics = _parse_configuration(
        source_path,
        workspace_root,
        platform_name=platform_name,
    )
    return ConfigurationReadResult(
        status=ConfigurationStatus.VALID if configuration is not None else ConfigurationStatus.INVALID,
        workspace_root=workspace_root,
        config_path=source_path,
        configuration=configuration,
        search_bases=bases,
        discovered=discovered,
        diagnostics=diagnostics,
    )
