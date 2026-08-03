from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.validation import (
    CommitValidationInput,
    StagedFactCandidate,
    StagedFileAssetCandidate,
    validate_commit,
)
from ldvh.facts.schema import FactSchema, ProjectedField


@pytest.fixture
def contract() -> CommitContractProjection:
    return CommitContractProjection(
        type_tokens=("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"),
        scope_tokens=("specs", "docs", "rules", "runtime", "code", "web", "tests", "config", "file-asset"),
        mechanical_triggers=("multiple-paths", "breaking-marker", "revert-type"),
        source_key="source-of-truth-traceability",
        source_path="specs/03-事实源与信息溯源规范.md",
        observed_at="2026-07-15T00:00:00+08:00",
        content_fingerprint="a" * 64,
    )


def _input(contract: CommitContractProjection, **changes: object) -> CommitValidationInput:
    values: dict[str, object] = {
        "message": "docs(specs): 明确提交契约\n\nSession-ID: test-session\nSigner-Type: ai-agent\nAgent-ID: test-agent\nHost-Environment: test-environment",
        "candidate_paths": ("specs/03.md",),
        "git_worktree_root": "/workspace/project",
        "governance_status": "governed_single",
        "governance_identity": "project:ldvh",
        "snapshot_identity": "sha256:snapshot",
        "source_path": contract.source_path,
        "source_fingerprint": contract.content_fingerprint,
    }
    values.update(changes)
    return CommitValidationInput(**values)  # type: ignore[arg-type]


def _codes(result: object) -> set[str]:
    return {issue.code for issue in result.issues}  # type: ignore[attr-defined]


def _signed(message: str) -> str:
    return message + "\n\nSession-ID: test-session\nSigner-Type: ai-agent\nAgent-ID: test-agent\nHost-Environment: test-environment"


def test_single_path_valid_header_passes_mechanical_layer(contract: CommitContractProjection) -> None:
    result = validate_commit(contract, _input(contract))

    assert result.outcome == "passed"
    assert "主要目的与拆分" in result.semantic_checks_required


def test_hyphenated_registered_scope_passes_mechanical_layer(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
            _input(contract, message=_signed("feat(file-asset): 激活文件资产事实对象")),
    )

    assert result.outcome == "passed"
    assert result.header == "feat(file-asset): 激活文件资产事实对象"


def test_crlf_and_leading_comments_are_normalized(contract: CommitContractProjection) -> None:
    message = "# template\r\n\r\ndocs(specs): 明确提交契约\r\n\r\nSession-ID: test\r\nSigner-Type: ai-agent\r\nAgent-ID: test\r\nHost-Environment: test\r\n"

    result = validate_commit(contract, _input(contract, message=message))

    assert result.outcome == "passed"
    assert result.header == "docs(specs): 明确提交契约"


def test_empty_message_is_a_mechanical_failure_not_a_missing_input(
    contract: CommitContractProjection,
) -> None:
    result = validate_commit(contract, _input(contract, message=""))

    assert result.outcome == "failed"
    assert "message_empty" in _codes(result)


@pytest.mark.parametrize(
    ("message", "code"),
    [
        ("unknown: 中文描述", "type_unknown"),
        ("docs(api): 中文描述", "scope_unknown"),
        ("docs: English only", "description_cjk_missing"),
        ("docs: 中文描述。", "description_period"),
        ("docs : 中文描述", "header_invalid"),
    ],
)
def test_header_failures(contract: CommitContractProjection, message: str, code: str) -> None:
    result = validate_commit(contract, _input(contract, message=message))

    assert result.outcome == "failed"
    assert code in _codes(result)


def test_multiple_paths_require_key_changes_list(contract: CommitContractProjection) -> None:
    missing = validate_commit(contract, _input(contract, candidate_paths=("a.md", "b.md")))
    valid = validate_commit(
        contract,
        _input(
            contract,
            candidate_paths=("a.md", "b.md"),
                message=_signed("docs: 更新两份说明\n\n关键变更:\n- 同步规则与示例"),
        ),
    )

    assert missing.outcome == "failed" and "body_required" in _codes(missing)
    assert valid.outcome == "passed"


def test_breaking_requires_body_and_impact_boundary(contract: CommitContractProjection) -> None:
    message = "feat!: 调整公开契约\n\n关键变更:\n- 调整字段"
    result = validate_commit(contract, _input(contract, message=message))

    assert result.outcome == "failed"
    assert "impact_boundary_required" in _codes(result)

    valid = validate_commit(
        contract,
            _input(contract, message=_signed(message + "\n\n影响边界:\n- 旧消费者需要迁移")),
    )
    assert valid.outcome == "passed"


def test_revert_requires_body(contract: CommitContractProjection) -> None:
    result = validate_commit(contract, _input(contract, message="revert: 撤销错误变化"))

    assert result.outcome == "failed"
    assert "body_required" in _codes(result)


def test_signature_footer_requires_session_and_ai_three_fields(contract: CommitContractProjection) -> None:
    result = validate_commit(contract, _input(contract, message="docs: 增加署名"))

    assert result.outcome == "failed"
    assert "signature_trailer_missing" in _codes(result)

    invalid = validate_commit(
        contract,
        _input(
            contract,
            message="docs: 增加署名\n\nSession-ID: test\nSigner-Type: person\nAgent-ID: a\nHost-Environment: b",
        ),
    )
    assert invalid.outcome == "failed"
    assert "signer_type_invalid" in _codes(invalid)


@pytest.mark.parametrize(
    "changes",
    [
        {"candidate_paths": ()},
        {"candidate_paths": ("a", "a")},
        {"candidate_paths": ("../a",)},
        {"candidate_paths": ("/a",)},
        {"candidate_paths": ("a\\b",)},
        {"governance_status": "scope_unknown"},
        {"source_fingerprint": "b" * 64},
        {"snapshot_identity": None},
    ],
)
def test_incomplete_or_untrusted_inputs_are_unverifiable(
    contract: CommitContractProjection,
    changes: dict[str, object],
) -> None:
    result = validate_commit(contract, _input(contract, **changes))

    assert result.outcome == "unverifiable"


def test_validator_does_not_read_git_or_filesystem(contract: CommitContractProjection, tmp_path: Path) -> None:
    missing_worktree = tmp_path / "does-not-exist"

    result = validate_commit(contract, _input(contract, git_worktree_root=str(missing_worktree)))

    assert result.outcome == "passed"


# -- specs 03 §9.9 staged fact-candidate layer -----------------------------


def _spark_schema() -> FactSchema:
    def field(path: str, presence: str = "required") -> ProjectedField:
        return ProjectedField(path, "string", presence, None, "test-registry")

    return FactSchema(
        "spark",
        (
            field("object_id"),
            field("fact_type_key"),
            field("title"),
            field("status"),
            field("priority"),
            field("created_at"),
            field("updated_at"),
            field("summary", "conditional"),
        ),
    )


def _file_asset_schema() -> FactSchema:
    def field(
        path: str,
        json_type: str = "string",
        presence: str = "required",
        structure: str | None = None,
    ) -> ProjectedField:
        return ProjectedField(path, json_type, presence, structure, "test-registry")

    return FactSchema(
        "file-asset",
        (
            field("object_id"),
            field("fact_type_key"),
            field("title"),
            field("created_at"),
            field("updated_at"),
            field("status"),
            field("filename"),
            field("media_type"),
            field("size_bytes", "integer"),
            field("content_sha256"),
            field("signature", "object", structure="file-asset-signature"),
            field("signature.signer_type"),
            field("signature.agent_id", presence="conditional"),
            field("signature.host_environment", presence="conditional"),
            field("disposition_summary", presence="conditional"),
        ),
    )


def _file_asset_candidate(
    *,
    object_id: str = "file-asset-0001",
    payload: bytes = b"objective bytes\n",
    head_exists: bool | None = False,
    member_names: tuple[str, ...] = ("file-asset.yaml", "payload"),
    observation_issue: str | None = None,
) -> StagedFileAssetCandidate:
    import hashlib

    manifest = (
        f"object_id: {object_id}\n"
        "fact_type_key: file-asset\n"
        "title: 审计文件\n"
        'created_at: "2026-07-31T10:00:00+08:00"\n'
        'updated_at: "2026-07-31T10:00:00+08:00"\n'
        "status: active\n"
        "filename: audit.bin\n"
        "media_type: application/octet-stream\n"
        f"size_bytes: {len(payload)}\n"
        f"content_sha256: {hashlib.sha256(payload).hexdigest()}\n"
        "signature:\n"
        "  signer_type: human\n"
    ).encode()
    return StagedFileAssetCandidate(
        object_id,
        tuple(f"ldvh-base/file-assets/{object_id}/{name}" for name in member_names),
        member_names,
        manifest if "file-asset.yaml" in member_names else None,
        payload if "payload" in member_names else None,
        head_exists,
        observation_issue,
    )


_VALID_SPARK = (
    "object_id: spark-0001\n"
    "fact_type_key: spark\n"
    "title: 测试火花\n"
    "status: open\n"
    "priority: P1\n"
    "created_at: 2026-07-01T00:00:00+08:00\n"
    "updated_at: 2026-07-01T00:00:00+08:00\n"
).encode()


def _fact_candidate(**changes: object) -> StagedFactCandidate:
    values: dict[str, object] = {
        "path": "ldvh-base/sparks/spark-0001.yaml",
        "fact_type_key": "spark",
        "object_id": "spark-0001",
        "data": _VALID_SPARK,
        "observation_issue": None,
    }
    values.update(changes)
    return StagedFactCandidate(**values)  # type: ignore[arg-type]


def test_invalid_staged_fact_candidate_fails_with_path_precise_diagnostics(
    contract: CommitContractProjection,
) -> None:
    candidate = _fact_candidate(data="title: 只有标题\n".encode())

    result = validate_commit(
        contract,
        _input(contract, fact_candidates=(candidate,), fact_schemas=(_spark_schema(),)),
    )

    assert result.outcome == "failed"
    assert "fact_candidate_invalid" in _codes(result)
    assert all(candidate.path in issue.message for issue in result.issues)
    assert any("缺少必填字段" in issue.message for issue in result.issues)


def test_valid_staged_fact_candidate_passes(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(contract, fact_candidates=(_fact_candidate(),), fact_schemas=(_spark_schema(),)),
    )

    assert result.outcome == "passed"
    assert result.issues == ()


def test_illegal_object_id_filename_fails_without_reading_blob(
    contract: CommitContractProjection,
) -> None:
    candidate = _fact_candidate(path="ldvh-base/sparks/not-a-spark.yaml", object_id=None, data=None)

    result = validate_commit(
        contract,
        _input(contract, fact_candidates=(candidate,), fact_schemas=(_spark_schema(),)),
    )

    assert result.outcome == "failed"
    assert _codes(result) == {"fact_object_id_invalid"}
    assert candidate.path in result.issues[0].message


def test_fact_candidate_observation_gap_is_unverifiable(contract: CommitContractProjection) -> None:
    candidate = _fact_candidate(data=None, observation_issue="Git staged blob read failed")

    result = validate_commit(
        contract,
        _input(contract, fact_candidates=(candidate,), fact_schemas=(_spark_schema(),)),
    )

    assert result.outcome == "unverifiable"
    assert "fact_candidate_unverifiable" in _codes(result)


def test_complete_valid_new_file_asset_after_image_passes(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(
            contract,
            file_asset_candidates=(_file_asset_candidate(),),
            fact_schemas=(_file_asset_schema(),),
        ),
    )

    assert result.outcome == "passed"


def test_incomplete_new_file_asset_after_image_fails(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(
            contract,
            file_asset_candidates=(_file_asset_candidate(member_names=("payload",)),),
            fact_schemas=(_file_asset_schema(),),
        ),
    )

    assert result.outcome == "failed"
    assert _codes(result) == {"fact_candidate_invalid"}


def test_existing_file_asset_lifecycle_write_fails(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(
            contract,
            file_asset_candidates=(_file_asset_candidate(head_exists=True),),
            fact_schemas=(_file_asset_schema(),),
        ),
    )

    assert result.outcome == "failed"
    assert _codes(result) == {"file_asset_lifecycle_write_unavailable"}


def test_file_asset_after_image_observation_gap_is_unverifiable(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(
            contract,
            file_asset_candidates=(_file_asset_candidate(observation_issue="blob read failed"),),
            fact_schemas=(_file_asset_schema(),),
        ),
    )

    assert result.outcome == "unverifiable"
    assert _codes(result) == {"fact_candidate_unverifiable"}


def test_missing_fact_schema_projection_is_unverifiable(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(contract, fact_candidates=(_fact_candidate(),), fact_schemas=()),
    )

    assert result.outcome == "unverifiable"
    assert _codes(result) == {"fact_schema_unavailable"}


def test_object_id_identity_mismatch_fails(contract: CommitContractProjection) -> None:
    mismatched = _VALID_SPARK.replace(b"spark-0001", b"spark-0002")
    candidate = _fact_candidate(data=mismatched)

    result = validate_commit(
        contract,
        _input(contract, fact_candidates=(candidate,), fact_schemas=(_spark_schema(),)),
    )

    assert result.outcome == "failed"
    assert "fact_candidate_invalid" in _codes(result)
    assert any("object_id" in issue.message and "不一致" in issue.message for issue in result.issues)
