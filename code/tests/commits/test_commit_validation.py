from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.validation import (
    CommitValidationInput,
    StagedFactCandidate,
    validate_commit,
)
from ldvh.facts.schema import FactSchema, ProjectedField


@pytest.fixture
def contract() -> CommitContractProjection:
    return CommitContractProjection(
        type_tokens=("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"),
        scope_tokens=("specs", "docs", "rules", "runtime", "code", "web", "tests", "config"),
        mechanical_triggers=("multiple-paths", "breaking-marker", "revert-type"),
        source_key="source-of-truth-traceability",
        source_path="specs/03-事实源与信息溯源规范.md",
        observed_at="2026-07-15T00:00:00+08:00",
        content_fingerprint="a" * 64,
    )


def _input(contract: CommitContractProjection, **changes: object) -> CommitValidationInput:
    values: dict[str, object] = {
        "message": "docs(specs): 明确提交契约\n\nSession-ID: test-session\nAgent-ID: test-agent\nHost-Environment: test-environment",
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
    return message + "\n\nSession-ID: test-session\nAgent-ID: test-agent\nHost-Environment: test-environment"


def test_single_path_valid_header_passes_mechanical_layer(contract: CommitContractProjection) -> None:
    result = validate_commit(contract, _input(contract))

    assert result.outcome == "passed"
    assert "主要目的与拆分" in result.semantic_checks_required


def test_crlf_and_leading_comments_are_normalized(contract: CommitContractProjection) -> None:
    message = "# template\r\n\r\ndocs(specs): 明确提交契约\r\n\r\nSession-ID: test\r\nAgent-ID: test\r\nHost-Environment: test\r\n"

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


def test_signature_footer_requires_session_and_two_signature_fields(contract: CommitContractProjection) -> None:
    result = validate_commit(contract, _input(contract, message="docs: 增加署名"))

    assert result.outcome == "failed"
    assert "signature_trailer_missing" in _codes(result)

    with_retired_legacy_trailer = validate_commit(
        contract,
        _input(
            contract,
            message="docs: 增加署名\n\nSession-ID: test\nSigner-Type: person\nAgent-ID: a\nHost-Environment: b",
        ),
    )
    assert with_retired_legacy_trailer.outcome == "failed"
    assert "signer_type_retired" in _codes(with_retired_legacy_trailer)


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
    def field(path: str, json_type: str = "string", presence: str = "required") -> ProjectedField:
        return ProjectedField(path, json_type, presence, None, "test-registry")

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
            field("summary", presence="conditional"),
            field("change_log", "array", presence="conditional"),
            field("change_log.signature", "object"),
            field("change_log.signature.agent_id"),
            field("change_log.signature.host_environment"),
            field("change_log.session_id"),
            field("change_log.at"),
            field("change_log.summary"),
        ),
    )


_VALID_SPARK = (
    "object_id: spark-0001\n"
    "fact_type_key: spark\n"
    "title: 测试火花\n"
    "status: open\n"
    "priority: P1\n"
    "created_at: 2026-07-01T00:00:00+08:00\n"
    "updated_at: 2026-07-01T00:00:00+08:00\n"
    "change_log:\n"
    "  - signature:\n"
    "      agent_id: test-agent\n"
    "      host_environment: test-environment\n"
    "    session_id: test-session\n"
    "    at: 2026-07-01T00:00:00+08:00\n"
    "    summary: 建立测试火花\n"
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
    candidate = _fact_candidate(head_exists=False)
    result = validate_commit(
        contract,
        _input(contract, fact_candidates=(candidate,), fact_schemas=(_spark_schema(),)),
    )

    assert result.outcome == "passed"
    assert result.issues == ()


def test_new_fact_change_log_must_match_commit_footer(contract: CommitContractProjection) -> None:
    mismatched = _VALID_SPARK.replace(b"session_id: test-session", b"session_id: another-session")
    result = validate_commit(
        contract,
        _input(
            contract,
            fact_candidates=(_fact_candidate(data=mismatched, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "failed"
    assert "fact_trace_signature_mismatch" in _codes(result)


def test_new_fact_with_multiple_precommit_change_logs_matches_commit_footer(
    contract: CommitContractProjection,
) -> None:
    data = _VALID_SPARK.replace(
        b"updated_at: 2026-07-01T00:00:00+08:00",
        b"updated_at: 2026-07-01T01:00:00+08:00",
    ) + (
        "  - signature:\n"
        "      agent_id: test-agent\n"
        "      host_environment: test-environment\n"
        "    session_id: test-session\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: 补充测试火花\n"
    ).encode()

    result = validate_commit(
        contract,
        _input(
            contract,
            fact_candidates=(_fact_candidate(data=data, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "passed"


def test_new_fact_rejects_any_precommit_change_log_not_matching_footer(
    contract: CommitContractProjection,
) -> None:
    data = _VALID_SPARK.replace(
        b"updated_at: 2026-07-01T00:00:00+08:00",
        b"updated_at: 2026-07-01T01:00:00+08:00",
    ) + (
        "  - signature:\n"
        "      agent_id: test-agent\n"
        "      host_environment: test-environment\n"
        "    session_id: another-session\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: 补充测试火花\n"
    ).encode()

    result = validate_commit(
        contract,
        _input(
            contract,
            fact_candidates=(_fact_candidate(data=data, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "failed"
    assert "fact_trace_signature_mismatch" in _codes(result)


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


def test_invalid_fact_is_not_downgraded_by_another_candidate_trace_gap(
    contract: CommitContractProjection,
) -> None:
    invalid = _fact_candidate(data=b"title: malformed\n")
    trace_gap = _fact_candidate(
        path="ldvh-base/sparks/spark-0002.yaml",
        object_id="spark-0002",
        data=_VALID_SPARK.replace(b"spark-0001", b"spark-0002"),
        head_exists=True,
    )

    result = validate_commit(
        contract,
        _input(contract, fact_candidates=(invalid, trace_gap), fact_schemas=(_spark_schema(),)),
    )

    assert result.outcome == "failed"
    assert "fact_candidate_invalid" in _codes(result)
    assert "fact_trace_unverifiable" in _codes(result)


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


def test_legacy_migration_change_log_passes_when_head_has_no_history(
    contract: CommitContractProjection,
) -> None:
    """HEAD 存在但无 change_log 的 legacy 迁移对象：首条迁移流水视为本次提交事件。"""

    # HEAD 快照：机制落地前的对象，无 change_log（保留全部必填字段）
    head_data = _VALID_SPARK.split(b"change_log:\n")[0]
    data = (
        "object_id: spark-0001\n"
        "fact_type_key: spark\n"
        "title: 测试火花\n"
        "status: open\n"
        "priority: P1\n"
        "created_at: 2026-07-01T00:00:00+08:00\n"
        "updated_at: 2026-07-01T01:00:00+08:00\n"
        "change_log:\n"
        "  - signature:\n"
        "      agent_id: test-agent\n"
        "      host_environment: test-environment\n"
        "    session_id: test-session\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: Human授权兼容旧数据：建立可信流水起点\n"
    ).encode()

    result = validate_commit(
        contract,
        _input(
            contract,
            fact_candidates=(
                _fact_candidate(data=data, head_exists=True, head_data=head_data),
            ),
            fact_schemas=(_spark_schema(),),
        ),
    )

    print("L3:", [(i.code, i.message) for i in result.issues])
    assert result.outcome == "passed"


def test_new_fact_multiple_sessions_match_multiple_footer_session_ids(
    contract: CommitContractProjection,
) -> None:
    """新对象多条 change_log 分属多个 session：footer 声明全部 Session-ID 即通过。"""

    data = _VALID_SPARK.replace(
        b"updated_at: 2026-07-01T00:00:00+08:00",
        b"updated_at: 2026-07-01T01:00:00+08:00",
    ) + (
        "  - signature:\n"
        "      agent_id: test-agent\n"
        "      host_environment: test-environment\n"
        "    session_id: test-session-2\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: 第二个受控写会话\n"
    ).encode()
    message = (
        "docs(specs): 多会话提交\n\n"
        "Session-ID: test-session\n"
        "Session-ID: test-session-2\n"
        "Agent-ID: test-agent\n"
        "Host-Environment: test-environment"
    )

    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            fact_candidates=(_fact_candidate(data=data, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "passed"


def test_new_fact_multiple_sessions_reject_unlisted_session(
    contract: CommitContractProjection,
) -> None:
    """新对象 change_log 的 session 未在 footer 声明：拒绝。"""

    data = _VALID_SPARK.replace(
        b"updated_at: 2026-07-01T00:00:00+08:00",
        b"updated_at: 2026-07-01T01:00:00+08:00",
    ) + (
        "  - signature:\n"
        "      agent_id: test-agent\n"
        "      host_environment: test-environment\n"
        "    session_id: ghost-session\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: 未声明会话\n"
    ).encode()

    result = validate_commit(
        contract,
        _input(
            contract,
            fact_candidates=(_fact_candidate(data=data, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "failed"
    assert "fact_trace_signature_mismatch" in _codes(result)


def test_new_fact_multiple_agents_match_multiple_footer_agent_ids(
    contract: CommitContractProjection,
) -> None:
    """新对象跨多 agent 流水：footer 声明全部 Agent-ID/Host-Environment 即通过。"""

    data = _VALID_SPARK.replace(
        b"updated_at: 2026-07-01T00:00:00+08:00",
        b"updated_at: 2026-07-01T01:00:00+08:00",
    ) + (
        "  - signature:\n"
        "      agent_id: another-agent\n"
        "      host_environment: another-env\n"
        "    session_id: test-session-2\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: 第二个执行者\n"
    ).encode()
    message = (
        "docs(specs): 多执行者提交\n\n"
        "Session-ID: test-session\n"
        "Session-ID: test-session-2\n"
        "Agent-ID: test-agent\n"
        "Agent-ID: another-agent\n"
        "Host-Environment: test-environment\n"
        "Host-Environment: another-env"
    )

    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            fact_candidates=(_fact_candidate(data=data, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "passed"


def test_new_fact_multiple_agents_reject_undeclared_agent(
    contract: CommitContractProjection,
) -> None:
    """新对象流水 agent 未在 footer 声明：拒绝。"""

    data = _VALID_SPARK.replace(
        b"updated_at: 2026-07-01T00:00:00+08:00",
        b"updated_at: 2026-07-01T01:00:00+08:00",
    ) + (
        "  - signature:\n"
        "      agent_id: ghost-agent\n"
        "      host_environment: ghost-env\n"
        "    session_id: test-session-2\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: 未声明执行者\n"
    ).encode()
    message = (
        "docs(specs): 未声明执行者\n\n"
        "Session-ID: test-session\n"
        "Session-ID: test-session-2\n"
        "Agent-ID: test-agent\n"
        "Host-Environment: test-environment"
    )

    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            fact_candidates=(_fact_candidate(data=data, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "failed"
    assert "fact_trace_signature_mismatch" in _codes(result)


def test_legacy_migration_multiple_agents_passes(
    contract: CommitContractProjection,
) -> None:
    """legacy 迁移对象跨多 agent：HEAD 无 change_log，footer 声明全部签名即通过。"""

    head_data = _VALID_SPARK.split(b"change_log:\n")[0]
    data = _VALID_SPARK.replace(
        b"updated_at: 2026-07-01T00:00:00+08:00",
        b"updated_at: 2026-07-01T01:00:00+08:00",
    ) + (
        "  - signature:\n"
        "      agent_id: another-agent\n"
        "      host_environment: another-env\n"
        "    session_id: test-session-2\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: Human授权兼容旧数据：第二个执行者迁移\n"
    ).encode()
    message = (
        "docs(specs): 多执行者迁移提交\n\n"
        "Session-ID: test-session\n"
        "Session-ID: test-session-2\n"
        "Agent-ID: test-agent\n"
        "Agent-ID: another-agent\n"
        "Host-Environment: test-environment\n"
        "Host-Environment: another-env"
    )

    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            fact_candidates=(
                _fact_candidate(data=data, head_exists=True, head_data=head_data),
            ),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "passed"
