from dataclasses import replace

from ldvh.diagnostics import SourceLocation
from ldvh.specs.graph import validate_graph
from ldvh.specs.identity import FormalDocument
from ldvh.specs.markdown import MarkdownDocument
from ldvh.specs.projection import project_l0_l2


def _markdown(path: str, title: str) -> MarkdownDocument:
    return MarkdownDocument(path, (f"# {title}",), title, 1, "", 3, ())


def _spec(
    key: str,
    spec_id: str,
    *,
    status: str = "active",
    basis: tuple[str, ...] = ("ldvh-root",),
    parent: str | None = "ldvh-root",
    attachments: tuple[str, ...] = (),
    supersedes: tuple[str, ...] = (),
) -> FormalDocument:
    if key == "ldvh-root":
        return FormalDocument(
            "root",
            key,
            "00",
            "Root",
            status,
            "specs/00-Root.md",
            "root",
            "root scope",
            (),
            None,
            None,
            (),
            supersedes,
            _markdown("specs/00-Root.md", "Root"),
        )
    path = f"specs/{spec_id}-{key}.md"
    return FormalDocument(
        "spec",
        key,
        spec_id,
        key,
        status,
        path,
        f"{key} positioning",
        f"{key} scope",
        basis,
        parent,
        "refines" if parent else None,
        attachments,
        supersedes,
        _markdown(path, key),
    )


def _attachment(
    key: str,
    attachment_id: str,
    *,
    status: str = "active",
    supersedes: tuple[str, ...] = (),
) -> FormalDocument:
    path = f"specs/attachments/{attachment_id}-{key}.md"
    return FormalDocument(
        "attachment",
        key,
        attachment_id,
        key,
        status,
        path,
        f"{key} positioning",
        None,
        (),
        None,
        None,
        (),
        supersedes,
        _markdown(path, key),
    )


def test_missing_basis_blocks_only_the_member_and_dependents() -> None:
    root = _spec("ldvh-root", "00")
    broken = _spec("broken", "10", basis=("missing",))
    dependent = _spec("dependent", "11", basis=("broken",))
    independent = _spec("independent", "12")

    result = validate_graph((root, broken, dependent, independent))

    assert {document.key for document in result.active_documents_passing_implemented_checks} == {
        "ldvh-root",
        "independent",
    }
    assert result.incomplete_keys == ("broken", "dependent")
    assert any("basis 目标" in issue.summary for issue in result.issues)


def test_basis_and_parent_cycles_are_blocking() -> None:
    root = _spec("ldvh-root", "00")
    first = _spec("first", "10", basis=("second",), parent="second")
    second = _spec("second", "11", basis=("first",), parent="first")

    result = validate_graph((root, first, second))

    assert {document.key for document in result.active_documents_passing_implemented_checks} == {"ldvh-root"}
    assert sum("循环" in issue.summary for issue in result.issues) >= 4


def test_attachment_requires_one_matching_active_parent() -> None:
    root = _spec("ldvh-root", "00")
    parent = _spec("parent", "10", attachments=("fields",))
    fields = _attachment("fields", "10.Att.01")

    valid = validate_graph((root, parent, fields))
    invalid = validate_graph((root, parent, _attachment("fields", "11.Att.01")))

    assert valid.attachment_parents == (("fields", "parent"),)
    assert {document.key for document in valid.active_documents_passing_implemented_checks} == {
        "ldvh-root",
        "parent",
        "fields",
    }
    assert any("父规范编号" in issue.summary for issue in invalid.issues)


def test_supersedes_requires_same_type_retired_target_and_enters_l2() -> None:
    root = _spec("ldvh-root", "00")
    old = _spec("old", "10", status="retired")
    new = _spec("new", "11", supersedes=("old",))
    new = replace(
        new,
        field_locations={"supersedes": SourceLocation(new.canonical_path, 21)},
    )

    graph = validate_graph((root, old, new))
    projections = project_l0_l2(graph)

    new_l2 = next(item for item in projections if item.key == "new" and item.layer == "L2")
    assert new_l2.content["supersedes"] == ({"key": "old", "path": old.canonical_path},)
    assert new_l2.source_references["supersedes"] == (SourceLocation(new.canonical_path, 21),)
    assert graph.issues == ()


def test_projection_preserves_field_sources_and_relation_key_path_mappings() -> None:
    root = _spec("ldvh-root", "00")
    parent = _spec("parent", "10", attachments=("fields",))
    parent = replace(
        parent,
        field_locations={
            "spec_key": SourceLocation(parent.canonical_path, 5),
            "basis": SourceLocation(parent.canonical_path, 15),
            "parent_spec": SourceLocation(parent.canonical_path, 11),
            "relation": SourceLocation(parent.canonical_path, 12),
            "authorized_attachments": SourceLocation(parent.canonical_path, 17),
        },
    )
    fields = _attachment("fields", "10.Att.01")

    projections = project_l0_l2(validate_graph((root, parent, fields)))
    parent_l0 = next(item for item in projections if item.key == "parent" and item.layer == "L0")
    parent_l2 = next(item for item in projections if item.key == "parent" and item.layer == "L2")
    fields_l2 = next(item for item in projections if item.key == "fields" and item.layer == "L2")

    assert parent_l0.source_references["key"] == (SourceLocation(parent.canonical_path, 5),)
    assert parent_l2.content["basis"] == ({"key": "ldvh-root", "path": root.canonical_path},)
    assert parent_l2.content["parent_spec"] == {"key": "ldvh-root", "path": root.canonical_path}
    assert parent_l2.content["authorized_attachments"] == ({"key": "fields", "path": fields.canonical_path},)
    assert fields_l2.content["parent_spec"] == {"key": "parent", "path": parent.canonical_path}
    assert fields_l2.source_references["parent_spec"] == (SourceLocation(parent.canonical_path, 17),)


def test_reachability_overlap_is_reported_for_semantic_necessity_review() -> None:
    root = _spec("ldvh-root", "00")
    middle = _spec("middle", "10")
    leaf = _spec("leaf", "11", basis=("ldvh-root", "middle"))

    result = validate_graph((root, middle, leaf))

    assert result.issues == ()
    assert "leaf" not in result.incomplete_keys
    assert result.basis_reachability_overlaps[0].spec_key == "leaf"
    assert result.basis_reachability_overlaps[0].direct_basis == "ldvh-root"
    assert {item.layer for item in project_l0_l2(result)} == {"L0", "L1", "L2"}


def test_duplicate_keys_and_ids_are_reported_without_cycle_lookup_failure() -> None:
    root = _spec("ldvh-root", "00")
    first = _spec("duplicate", "10", supersedes=("duplicate",))
    second = _spec("duplicate", "11", supersedes=("duplicate",))
    same_id = _spec("same-id", "10")

    result = validate_graph((root, first, second, same_id))

    assert any("职责标识符" in issue.summary for issue in result.issues)
    assert any("规范编号" in issue.summary for issue in result.issues)
    assert "duplicate" in result.incomplete_keys
    assert "same-id" in result.incomplete_keys


def test_self_relations_and_multiple_attachment_authorizers_are_blocking() -> None:
    root = _spec("ldvh-root", "00")
    self_related = _spec("self-related", "10", basis=("self-related",), parent="self-related")
    first_parent = _spec("first-parent", "11", attachments=("fields",))
    second_parent = _spec("second-parent", "12", attachments=("fields",))
    fields = _attachment("fields", "11.Att.01")

    result = validate_graph((root, self_related, first_parent, second_parent, fields))

    assert any("不得自指" in issue.summary for issue in result.issues)
    assert any("只能由一个" in issue.summary for issue in result.issues)
    assert {"self-related", "fields"}.issubset(result.incomplete_keys)


def test_supersedes_rejects_active_wrong_type_duplicate_and_cycles() -> None:
    root = _spec("ldvh-root", "00")
    active_old = _spec("active-old", "10")
    wrong_type = _attachment("wrong-type", "10.Att.01", status="retired")
    first = _spec("first", "11", status="retired", supersedes=("second", "second"))
    second = _spec("second", "12", status="retired", supersedes=("first",))
    replacement = _spec("replacement", "13", supersedes=("active-old", "wrong-type"))

    result = validate_graph((root, active_old, wrong_type, first, second, replacement))

    summaries = [issue.summary for issue in result.issues]
    assert any("supersedes 不得包含重复" in summary for summary in summaries)
    assert any("supersedes 关系形成循环" in summary for summary in summaries)
    assert any("缺失或类型错误" in summary for summary in summaries)
    assert any("在当前 Working Tree 为 retired" in summary for summary in summaries)
