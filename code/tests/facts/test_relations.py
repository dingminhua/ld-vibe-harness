from __future__ import annotations

from ldvh.facts.relations import _target_condition, _target_has_readable_title, _workcase_residual_mapping_issues


def test_spark_routed_to_rejects_study_but_accepts_other_stable_fact_types() -> None:
    assert not _target_condition("spark", "routed-to", "study", "active")
    assert not _target_condition("spark", "routed-to", "spark", "open")
    assert _target_condition("spark", "routed-to", "workcase", "open")


def test_spark_routed_to_requires_a_nonempty_current_target_title() -> None:
    assert _target_has_readable_title("spark", "routed-to", {"title": "Helper 事实对象机械结构校验闭环"})
    assert not _target_has_readable_title("spark", "routed-to", {"title": "  "})
    assert _target_has_readable_title("spark", "related-to", {})


def _current_workcase_relations() -> dict[str, object]:
    return {
        "workcase_profile": "control-contract-v1",
        "residual_responsibilities": [
            {
                "residual_id": "residual-01",
                "summary": "A downstream responsibility remains",
                "disposition": "routed",
            }
        ],
        "relations": [
            {
                "relation_key": "routed-to",
                "target": {
                    "governed_project_id": "sample",
                    "fact_type_key": "workcase",
                    "object_id": "workcase-0002",
                },
                "responsibility_ids": ["residual-01"],
            }
        ],
    }


def test_current_routed_residual_has_an_explicit_valid_mapping() -> None:
    assert _workcase_residual_mapping_issues(_current_workcase_relations()) == []


def test_current_routed_residual_rejects_missing_unknown_and_non_routed_mappings() -> None:
    missing = _current_workcase_relations()
    relations = missing["relations"]
    assert isinstance(relations, list) and isinstance(relations[0], dict)
    relations[0].pop("responsibility_ids")
    issues = _workcase_residual_mapping_issues(missing)
    assert any("必须显式映射" in issue.summary for issue in issues)
    assert any("至少一条" in issue.summary for issue in issues)

    accepted = _current_workcase_relations()
    residuals = accepted["residual_responsibilities"]
    assert isinstance(residuals, list) and isinstance(residuals[0], dict)
    residuals[0]["disposition"] = "accepted_stop"
    issues = _workcase_residual_mapping_issues(accepted)
    assert any("只能映射" in issue.summary for issue in issues)

    wrong_relation = _current_workcase_relations()
    relations = wrong_relation["relations"]
    assert isinstance(relations, list) and isinstance(relations[0], dict)
    relations[0]["relation_key"] = "depends-on"
    issues = _workcase_residual_mapping_issues(wrong_relation)
    assert any("只有 routed-to" in issue.summary for issue in issues)


def test_legacy_workcase_does_not_require_current_residual_mapping_contract() -> None:
    fields = _current_workcase_relations()
    fields.pop("workcase_profile")
    assert _workcase_residual_mapping_issues(fields) == []
