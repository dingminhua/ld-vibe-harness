from __future__ import annotations

from ldvh.signature import parse_signature


def test_signature_keeps_product_and_normalizes_model() -> None:
    signature, problems = parse_signature(
        {
            "product_name": "Cindy",
            "model_name": "GLM-5.2",
        }
    )

    assert problems == ()
    assert signature is not None
    assert signature.as_dict() == {
        "product_name": "Cindy",
        "model_name": "glm-5.2",
    }


def test_signature_discards_trailing_model_bracket_annotations() -> None:
    signature, problems = parse_signature(
        {
            "product_name": "WorkBuddy",
            "model_name": "DeepSeek-V4-Flash[1m][fallback]",
        }
    )

    assert problems == ()
    assert signature is not None
    assert signature.model_name == "deepseek-v4-flash"


def test_signature_rejects_a_model_name_that_becomes_empty_after_annotation_removal() -> None:
    signature, problems = parse_signature(
        {
            "product_name": "WorkBuddy",
            "model_name": "[1m]",
        }
    )

    assert signature is None
    assert problems == ("LDVH 署名.model_name 归一后不得为空",)


def test_signature_rejects_missing_product_name() -> None:
    signature, problems = parse_signature(
        {
            "product_name": None,
            "model_name": "glm-5.2",
        }
    )

    assert signature is None
    assert "LDVH 署名.product_name 必须是非空 string（不可观察时必须停止并报告）" in problems


def test_signature_rejects_missing_model_name() -> None:
    signature, problems = parse_signature(
        {
            "product_name": "WorkBuddy",
            "model_name": None,
        }
    )

    assert signature is None
    assert "LDVH 署名.model_name 必须是非空 string（不可观察时必须停止并报告）" in problems


def test_signature_rejects_an_empty_snapshot() -> None:
    signature, problems = parse_signature({"product_name": None, "model_name": None})
    assert signature is None
    assert problems == (
        "LDVH 署名.product_name 必须是非空 string（不可观察时必须停止并报告）",
        "LDVH 署名.model_name 必须是非空 string（不可观察时必须停止并报告）",
    )


def test_signature_rejects_agent_runtime_name_as_unknown_field() -> None:
    """agent_runtime_name 已退役：新写入不得携带该字段。"""

    signature, problems = parse_signature(
        {
            "product_name": "Cindy",
            "model_name": "glm-5.2",
            "agent_runtime_name": "codex-cli",
        }
    )
    assert signature is None
    assert "LDVH 署名包含未知字段: agent_runtime_name" in problems


def test_signature_allows_product_names_that_match_known_runtime_display_names() -> None:
    """产品显示名合法值不受运行时概念影响。"""

    for product in ("Claude Code", "claude-code", "Codex CLI", "codex_cli", "codex"):
        signature, problems = parse_signature(
            {"product_name": product, "model_name": "glm-5.2"}
        )
        assert problems == (), (product, problems)
        assert signature is not None
        assert signature.product_name == product


def test_signature_is_parse_boundary_and_does_not_reuse_previous_snapshots() -> None:
    """parse_signature 是唯一归一边界；每次写入前必须重新取得快照。"""

    snapshot_a, _ = parse_signature(
        {"product_name": "WorkBuddy", "model_name": "deepseek-v4"}
    )
    snapshot_b, _ = parse_signature(
        {"product_name": "WorkBuddy", "model_name": "deepseek-v4"}
    )
    assert snapshot_a is not None and snapshot_b is not None
    assert snapshot_a.as_dict() == snapshot_b.as_dict()

    # 语义：同一快照解析结果确定可重复，但契约要求每次动作携带当次快照，
    # 不因重复解析结果相同而允许沿用作先前动作的采集值。
    signature, problems = parse_signature({"product_name": None, "model_name": None})
    assert signature is None