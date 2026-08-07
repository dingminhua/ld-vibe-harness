from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ldvh.governance.models import (
    ConfigStatus,
    GovernanceScopeResult,
    GovernedVia,
    LocatorSource,
    ObjectResolution,
    ObjectStatus,
    RegisteredProjectCandidate,
    ScopeDescriptor,
    ScopeStatus,
    aggregate_scope_status,
    cwd_scope,
    explicit_scope,
    helper_scope,
)

SOURCE = ({"kind": "observation", "locator": "/workspace/object", "details": {"view": "Working Tree"}},)


def resolution(
    index: int,
    status: ObjectStatus,
    *,
    locator: str | None = None,
    project_id: str | None = None,
) -> ObjectResolution:
    governed = status is ObjectStatus.GOVERNED
    return ObjectResolution(
        locator_index=index,
        locator=locator or f"object-{index}",
        resolved_identity=f"/workspace/object-{index}",
        identity_evidence=SOURCE if status is not ObjectStatus.UNKNOWN else (),
        source=LocatorSource.EXPLICIT_LOCATOR,
        status=status,
        governed_project_id=project_id if governed else None,
        registered_project_path=f"/workspace/{project_id}" if governed else None,
        governed_via=GovernedVia.PATH if governed else None,
        git_worktree_root=f"/workspace/object-{index}",
        git_common_dir="/workspace/repository/.git",
        source_refs=SOURCE,
        unknown_reason="identity evidence is insufficient" if status is ObjectStatus.UNKNOWN else None,
    )


def candidate(project_id: str) -> RegisteredProjectCandidate:
    return RegisteredProjectCandidate(
        governed_project_id=project_id,
        registered_project_path=f"/workspace/{project_id}",
        git_worktree_root=f"/workspace/{project_id}",
        git_common_dir=f"/workspace/{project_id}/.git",
        source_refs=SOURCE,
    )


@pytest.mark.parametrize(
    ("items", "expected"),
    [
        ((), ScopeStatus.SCOPE_UNKNOWN),
        ((resolution(0, ObjectStatus.GOVERNED, project_id="one"),), ScopeStatus.GOVERNED_SINGLE),
        (
            (
                resolution(0, ObjectStatus.GOVERNED, project_id="one"),
                resolution(1, ObjectStatus.GOVERNED, project_id="two"),
            ),
            ScopeStatus.MULTIPLE_GOVERNED_PROJECTS,
        ),
        ((resolution(0, ObjectStatus.NOT_GOVERNED),), ScopeStatus.NON_GOVERNED),
        ((resolution(0, ObjectStatus.UNKNOWN),), ScopeStatus.SCOPE_UNKNOWN),
        (
            (resolution(0, ObjectStatus.NOT_GOVERNED), resolution(1, ObjectStatus.UNKNOWN)),
            ScopeStatus.MIXED_SCOPE,
        ),
    ],
)
def test_aggregate_scope_status_is_deterministic(items, expected: ScopeStatus) -> None:
    assert aggregate_scope_status(items) is expected


def test_result_serializes_exact_attachment_field_closure_and_sorts_by_index() -> None:
    second = resolution(1, ObjectStatus.NOT_GOVERNED)
    first = resolution(0, ObjectStatus.GOVERNED, project_id="ldvh")
    result = GovernanceScopeResult(
        workspace_root="/workspace",
        config_path="/workspace/LDVH-GOVERNED-PROJECTS.yaml",
        config_status=ConfigStatus.VALID,
        object_resolutions=(second, first),
        source_refs=SOURCE,
        registered_project_candidates=(candidate("zeta"), candidate("alpha")),
    )

    serialized = result.to_json()

    assert set(serialized) == {
        "workspace_root",
        "config_path",
        "config_status",
        "scope_status",
        "object_resolutions",
        "registered_project_candidates",
        "source_refs",
    }
    assert serialized["scope_status"] == "mixed_scope"
    assert [item["locator_index"] for item in serialized["object_resolutions"]] == [0, 1]
    assert [item["governed_project_id"] for item in serialized["registered_project_candidates"]] == [
        "alpha",
        "zeta",
    ]
    assert set(serialized["registered_project_candidates"][0]) == {
        "governed_project_id",
        "registered_project_path",
        "git_worktree_root",
        "git_common_dir",
        "source_refs",
    }
    assert set(serialized["object_resolutions"][0]) == {
        "locator_index",
        "locator",
        "resolved_identity",
        "identity_evidence",
        "source",
        "status",
        "governed_project_id",
        "registered_project_path",
        "governed_via",
        "git_worktree_root",
        "git_common_dir",
        "source_refs",
        "unknown_reason",
    }


def test_models_are_immutable_including_nested_source_references() -> None:
    item = resolution(0, ObjectStatus.GOVERNED, project_id="ldvh")

    with pytest.raises(FrozenInstanceError):
        item.locator = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        item.source_refs[0]["locator"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        item.source_refs[0]["details"]["view"] = "changed"  # type: ignore[index]


def test_non_valid_configuration_only_supports_unknown_domain_results() -> None:
    with pytest.raises(ValueError, match="non-valid configuration"):
        GovernanceScopeResult(
            workspace_root="/workspace",
            config_path=None,
            config_status=ConfigStatus.MISSING,
            object_resolutions=(resolution(0, ObjectStatus.NOT_GOVERNED),),
            source_refs=SOURCE,
        )

    with pytest.raises(ValueError, match="cannot expose registered project candidates"):
        GovernanceScopeResult(
            workspace_root="/workspace",
            config_path=None,
            config_status=ConfigStatus.MISSING,
            object_resolutions=(resolution(0, ObjectStatus.UNKNOWN),),
            source_refs=SOURCE,
            registered_project_candidates=(candidate("ldvh"),),
        )


def test_registered_project_candidates_reject_duplicate_identity_keys() -> None:
    duplicate_common_dir = RegisteredProjectCandidate(
        governed_project_id="second",
        registered_project_path="/workspace/second",
        git_worktree_root="/workspace/second",
        git_common_dir="/workspace/first/.git",
        source_refs=SOURCE,
    )

    with pytest.raises(ValueError, match="unique git_common_dir"):
        GovernanceScopeResult(
            workspace_root="/workspace",
            config_path="/workspace/LDVH-GOVERNED-PROJECTS.yaml",
            config_status=ConfigStatus.VALID,
            object_resolutions=(resolution(0, ObjectStatus.NOT_GOVERNED),),
            source_refs=SOURCE,
            registered_project_candidates=(candidate("first"), duplicate_common_dir),
        )


def test_result_rejects_relative_paths() -> None:
    with pytest.raises(ValueError, match="workspace_root"):
        GovernanceScopeResult(
            workspace_root="relative",
            config_path=None,
            config_status=ConfigStatus.MISSING,
            object_resolutions=(resolution(0, ObjectStatus.UNKNOWN),),
            source_refs=SOURCE,
        )


def test_object_status_invariants_prevent_internally_conflicting_results() -> None:
    with pytest.raises(ValueError, match="unknown resolution requires unknown_reason"):
        ObjectResolution(
            locator_index=0,
            locator="object",
            resolved_identity=None,
            identity_evidence=(),
            source=LocatorSource.CWD,
            status=ObjectStatus.UNKNOWN,
            governed_project_id=None,
            registered_project_path=None,
            governed_via=None,
            git_worktree_root=None,
            git_common_dir=None,
            source_refs=SOURCE,
            unknown_reason=None,
        )


def test_scope_mapping_preserves_duplicate_locator_inputs_and_partial_completion() -> None:
    requested = explicit_scope(("same", "same", "other"))
    mapped = helper_scope(requested, (requested[0], requested[2]))

    assert mapped == {
        "requested": [
            {"locator_index": 0, "locator": "same", "source": "explicit_locator"},
            {"locator_index": 1, "locator": "same", "source": "explicit_locator"},
            {"locator_index": 2, "locator": "other", "source": "explicit_locator"},
        ],
        "completed": [
            {"locator_index": 0, "locator": "same", "source": "explicit_locator"},
            {"locator_index": 2, "locator": "other", "source": "explicit_locator"},
        ],
        "not_completed": [
            {"locator_index": 1, "locator": "same", "source": "explicit_locator"},
        ],
    }


def test_cwd_scope_is_the_single_index_zero_fallback() -> None:
    assert cwd_scope("/workspace") == (ScopeDescriptor(0, "/workspace", LocatorSource.CWD),)


def test_completed_scope_comes_directly_from_completed_object_resolutions() -> None:
    result = GovernanceScopeResult(
        workspace_root="/workspace",
        config_path=None,
        config_status=ConfigStatus.MISSING,
        object_resolutions=(resolution(1, ObjectStatus.UNKNOWN), resolution(0, ObjectStatus.UNKNOWN)),
        source_refs=SOURCE,
    )

    assert result.completed_scope == (
        ScopeDescriptor(0, "object-0", LocatorSource.EXPLICIT_LOCATOR),
        ScopeDescriptor(1, "object-1", LocatorSource.EXPLICIT_LOCATOR),
    )
    assert result.scope_status is ScopeStatus.SCOPE_UNKNOWN


def test_scope_mapping_rejects_a_completed_descriptor_that_changed_the_request() -> None:
    requested = explicit_scope(("one",))
    changed = ScopeDescriptor(0, "different", LocatorSource.EXPLICIT_LOCATOR)

    with pytest.raises(ValueError, match="must equal"):
        helper_scope(requested, (changed,))
