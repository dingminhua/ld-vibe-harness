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
