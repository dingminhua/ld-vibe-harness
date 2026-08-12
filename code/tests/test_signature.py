from __future__ import annotations

from ldvh.signature import parse_signature


def test_signature_keeps_product_and_normalizes_model_and_runtime() -> None:
    signature, problems = parse_signature(
        {
            "product_name": "Cindy",
            "model_name": "GLM-5.2",
            "agent_runtime_name": "Codex CLI",
        }
    )

    assert problems == ()
    assert signature is not None
    assert signature.as_dict() == {
        "product_name": "Cindy",
        "model_name": "glm-5.2",
        "agent_runtime_name": "codex-cli",
    }


def test_signature_discards_trailing_model_bracket_annotations() -> None:
    signature, problems = parse_signature(
        {
            "product_name": "WorkBuddy",
            "model_name": "DeepSeek-V4-Flash[1m][fallback]",
            "agent_runtime_name": None,
        }
    )

    assert problems == ()
    assert signature is not None
    assert signature.model_name == "deepseek-v4-flash"


def test_signature_rejects_a_model_name_that_becomes_empty_after_annotation_removal() -> None:
    signature, problems = parse_signature(
        {
            "product_name": None,
            "model_name": "[1m]",
            "agent_runtime_name": None,
        }
    )

    assert signature is None
    assert problems == ("LDVH 署名.model_name 归一后不得为空",)


def test_signature_allows_individual_nulls_but_rejects_an_empty_snapshot() -> None:
    signature, problems = parse_signature(
        {
            "product_name": "WorkBuddy",
            "model_name": None,
            "agent_runtime_name": None,
        }
    )
    assert problems == ()
    assert signature is not None

    signature, problems = parse_signature({"product_name": None, "model_name": None, "agent_runtime_name": None})
    assert signature is None
    assert problems == ("LDVH 署名三项均不可得，新的受控写入必须停止",)


def test_signature_null_means_undeclared_not_confirmed_unavailable() -> None:
    """历史 null 表示未声明/未知，不是确认不可得；不得解释为负面证据。"""

    signature, problems = parse_signature({"product_name": None, "model_name": "glm-5.2", "agent_runtime_name": None})
    assert problems == ()
    assert signature is not None
    assert signature.product_name is None
    assert signature.agent_runtime_name is None


def test_signature_is_parse_boundary_and_does_not_reuse_previous_snapshots() -> None:
    """parse_signature 是唯一归一边界；每次写入前必须重新取得快照。"""

    snapshot_a, _ = parse_signature(
        {"product_name": "WorkBuddy", "model_name": "deepseek-v4", "agent_runtime_name": "codex-cli"}
    )
    snapshot_b, _ = parse_signature(
        {"product_name": "WorkBuddy", "model_name": "deepseek-v4", "agent_runtime_name": "codex-cli"}
    )
    assert snapshot_a is not None and snapshot_b is not None
    assert snapshot_a.as_dict() == snapshot_b.as_dict()

    # 语义：同一快照解析结果确定可重复，但契约要求每次动作携带当次快照，
    # 不因重复解析结果相同而允许沿用作先前动作的采集值。
    signature, problems = parse_signature({"product_name": None, "model_name": None, "agent_runtime_name": None})
    assert signature is None
    assert problems == ("LDVH 署名三项均不可得，新的受控写入必须停止",)
