from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.validation import (
    CommitValidationInput,
    StagedFactCandidate,
    _human_gate_trailer_issues,
    _platform_affected_issues,
    validate_commit,
)
from ldvh.facts.schema import FactSchema, ProjectedField


@pytest.fixture
def contract() -> CommitContractProjection:
    return CommitContractProjection(
        type_tokens=("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"),
        scope_tokens=("specs", "docs", "rules", "runtime", "code", "web", "tests", "config"),
        mechanical_triggers=("all-commits-minimum-body", "breaking-marker"),
        source_key="source-of-truth-traceability",
        source_path="specs/03-事实源与信息溯源规范.md",
        observed_at="2026-07-15T00:00:00+08:00",
        content_fingerprint="a" * 64,
    )


def _input(contract: CommitContractProjection, **changes: object) -> CommitValidationInput:
    values: dict[str, object] = {
        "message": (
            "docs(specs): 明确提交契约\n\n"
            "关键变更:\n- 明确测试中的提交契约\n\n"
            "Session-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy"
        ),
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
    if "\n关键变更:" not in message:
        message += "\n\n关键变更:\n- 覆盖当前测试变化"
    return message + "\n\nSession-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy"


def test_new_spec_without_human_gate_trailer_fails(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(
            contract,
            candidate_paths=("specs/10-新规范.md",),
            spec_candidate_statuses={"specs/10-新规范.md": "A"},
        ),
    )
    assert result.outcome == "failed"
    assert "human_gate_trailer_missing" in _codes(result)


def test_new_spec_with_empty_human_gate_trailer_fails(contract: CommitContractProjection) -> None:
    message = (
        "docs(specs): 新增规范文档\n\n"
        "关键变更:\n- 新增独立 spec 文档\n\n"
        "Session-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy\n"
        "Human-Gate: "
    )
    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            candidate_paths=("specs/10-新规范.md",),
            spec_candidate_statuses={"specs/10-新规范.md": "A"},
        ),
    )
    assert result.outcome == "failed"
    assert "human_gate_trailer_missing" in _codes(result)


def test_new_spec_with_human_gate_trailer_passes(contract: CommitContractProjection) -> None:
    message = (
        "docs(specs): 新增规范文档\n\n"
        "关键变更:\n- 新增独立 spec 文档\n\n"
        "Session-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy\n"
        "Human-Gate: authorized-by-human-20260806"
    )
    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            candidate_paths=("specs/10-新规范.md",),
            spec_candidate_statuses={"specs/10-新规范.md": "A"},
        ),
    )
    assert result.outcome == "passed"


def test_existing_spec_modified_without_human_gate_trailer_passes(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(
            contract,
            candidate_paths=("specs/01-规范模型基础规范.md",),
            spec_candidate_statuses={"specs/01-规范模型基础规范.md": "M"},
        ),
    )
    assert result.outcome == "passed"


def test_fact_object_path_excluded_from_spec_block() -> None:
    fact = StagedFactCandidate(
        path="specs/20-Spark-火花.md",
        fact_type_key="spark",
        object_id="spark-0001",
        data=b"x",
        observation_issue=None,
    )
    # A fact object staged as added must NOT be treated as a new spec document.
    issues = _human_gate_trailer_issues(
        ["x"],
        ("specs/20-Spark-火花.md",),
        (fact,),
        {"specs/20-Spark-火花.md": "A"},
    )
    assert issues == []


def test_unknown_spec_status_fails_closed(contract: CommitContractProjection) -> None:
    # When a status map is supplied but the candidate path is missing from it
    # (staged status unknown despite a map being provided), the validator
    # fails closed and still requires the Human-Gate trailer.
    result = validate_commit(
        contract,
        _input(
            contract,
            candidate_paths=("specs/10-新规范.md",),
            spec_candidate_statuses={},
        ),
    )
    assert result.outcome == "failed"
    assert "human_gate_trailer_missing" in _codes(result)


def test_activate_existing_spec_without_human_gate_trailer_fails(contract: CommitContractProjection) -> None:
    # Activating an existing spec (status flip to active) is a Human Gate event
    # and must carry the Human-Gate trailer, even though the git status is M.
    result = validate_commit(
        contract,
        _input(
            contract,
            candidate_paths=("specs/09-环境接入规范.md",),
            spec_candidate_statuses={"specs/09-环境接入规范.md": "M"},
            spec_activated_paths=("specs/09-环境接入规范.md",),
        ),
    )
    assert result.outcome == "failed"
    assert "human_gate_trailer_missing" in _codes(result)


def test_activate_existing_spec_with_human_gate_trailer_passes(contract: CommitContractProjection) -> None:
    message = (
        "docs(specs): 激活独立规范文档\n\n"
        "关键变更:\n- 将 status 转为 active\n\n"
        "Session-ID: test-session\nModel-ID: test-agent\nWorkbench-Name: test-environment\n"
        "Human-Gate: authorized-by-human-20260806"
    )
    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            candidate_paths=("specs/09-环境接入规范.md",),
            spec_candidate_statuses={"specs/09-环境接入规范.md": "M"},
            spec_activated_paths=("specs/09-环境接入规范.md",),
        ),
    )
    assert result.outcome == "passed"


def test_activate_fact_object_path_excluded(contract: CommitContractProjection) -> None:
    # A fact object (e.g. Spark) flipped to active must NOT be treated as a
    # spec activation requiring a Human-Gate trailer.
    fact = StagedFactCandidate(
        path="specs/20-Spark-火花.md",
        fact_type_key="spark",
        object_id="spark-0001",
        data=b"x",
        observation_issue=None,
    )
    issues = _human_gate_trailer_issues(
        ["x"],
        ("specs/20-Spark-火花.md",),
        (fact,),
        {"specs/20-Spark-火花.md": "M"},
        ("specs/20-Spark-火花.md",),
    )
    assert issues == []


def test_single_path_minimum_body_passes_mechanical_layer(contract: CommitContractProjection) -> None:
    result = validate_commit(contract, _input(contract))

    assert result.outcome == "passed"
    assert "主要目的与拆分" in result.semantic_checks_required


def test_crlf_and_leading_comments_are_normalized(contract: CommitContractProjection) -> None:
    message = (
        "# template\r\n\r\ndocs(specs): 明确提交契约\r\n\r\n"
        "关键变更:\r\n- 明确换行归一化\r\n\r\n"
        "Session-ID: test\r\nModel-ID: gpt-5.6-luna\r\nWorkbench-Name: Cindy\r\n"
    )

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


def test_invalid_header_still_reports_independent_body_and_footer_failures(
    contract: CommitContractProjection,
) -> None:
    result = validate_commit(contract, _input(contract, message="broken"))

    assert {
        "header_invalid",
        "body_required",
        "key_changes_required",
        "signature_trailer_missing",
    } <= _codes(result)


def test_every_commit_requires_key_changes_list(contract: CommitContractProjection) -> None:
    missing = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs: 更新说明\n\nSession-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy"
            ),
        ),
    )
    valid = validate_commit(
        contract,
        _input(
            contract,
            candidate_paths=("a.md", "b.md"),
            message=_signed("docs: 更新两份说明\n\n关键变更:\n- 同步规则与示例"),
        ),
    )

    assert missing.outcome == "failed"
    assert {"body_required", "key_changes_required"} <= _codes(missing)
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


def test_breaking_without_body_reports_all_minimum_structure_failures(
    contract: CommitContractProjection,
) -> None:
    result = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "feat!: 调整公开契约\n\n"
                "Session-ID: test-session\n"
                "Model-ID: gpt-5.6-luna\n"
                "Workbench-Name: Cindy"
            ),
        ),
    )

    assert {
        "body_required",
        "key_changes_required",
        "impact_boundary_required",
    } <= _codes(result)


def test_revert_requires_body(contract: CommitContractProjection) -> None:
    result = validate_commit(contract, _input(contract, message="revert: 撤销错误变化"))

    assert result.outcome == "failed"
    assert "body_required" in _codes(result)


@pytest.mark.parametrize(
    ("message", "codes"),
    [
        (
            "docs: 重复小标题\n\n关键变更:\n- 第一项\n\n关键变更:\n- 第二项",
            {"body_heading_duplicate", "key_changes_required"},
        ),
        ("docs: 空小标题\n\n动机:\n\n关键变更:\n- 有效变化", {"body_heading_empty"}),
        ("docs: 未知小标题\n\n关键变更:\n备注:\n- 不得跨标题归属", {"body_heading_unknown", "key_changes_required"}),
        ("docs: 空列表项\n\n关键变更:\n-   ", {"key_changes_required"}),
    ],
)
def test_body_heading_and_list_boundaries_fail_closed(
    contract: CommitContractProjection,
    message: str,
    codes: set[str],
) -> None:
    result = validate_commit(contract, _input(contract, message=_signed(message)))

    assert result.outcome == "failed"
    assert codes <= _codes(result)


def test_body_after_trailers_is_not_accepted_as_minimum_body(contract: CommitContractProjection) -> None:
    message = (
        "docs: 错误放置正文\n\n"
        "Session-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy\n\n"
        "关键变更:\n- trailers 之后的正文无效"
    )

    result = validate_commit(contract, _input(contract, message=message))

    assert result.outcome == "failed"
    assert "signature_trailer_missing" in _codes(result)


def test_signature_footer_requires_session_and_two_signature_fields(contract: CommitContractProjection) -> None:
    result = validate_commit(contract, _input(contract, message="docs: 增加署名"))

    assert result.outcome == "failed"
    assert "signature_trailer_missing" in _codes(result)

    with_retired_legacy_trailer = validate_commit(
        contract,
        _input(
            contract,
            message="docs: 增加署名\n\nSession-ID: test\nSigner-Type: person\nModel-ID: a\nWorkbench-Name: b",
        ),
    )
    assert with_retired_legacy_trailer.outcome == "failed"
    assert "signer_type_retired" in _codes(with_retired_legacy_trailer)


def test_new_signature_trailers_are_canonical_footer(contract: CommitContractProjection) -> None:
    """新三元组 footer 直接通过。"""

    result = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 明确提交契约\n\n"
                "关键变更:\n- 明确测试中的提交契约\n\n"
                "Session-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy"
            ),
        ),
    )

    assert result.outcome == "passed", [f"{issue.code}: {issue.message}" for issue in result.issues]


def test_new_signature_footer_tripwires_reject_alias_and_os_suffix(
    contract: CommitContractProjection,
) -> None:
    """新 footer 的 Model-ID 裸产品别名与 Workbench-Name 括号系统后缀被机械拒绝。"""

    alias = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 明确提交契约\n\n"
                "关键变更:\n- 明确测试中的提交契约\n\n"
                "Session-ID: test-session\nModel-ID: codex\nWorkbench-Name: Cindy"
            ),
        ),
    )
    assert alias.outcome == "failed"
    assert "signature_model_alias" in _codes(alias)

    suffix = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 明确提交契约\n\n"
                "关键变更:\n- 明确测试中的提交契约\n\n"
                "Session-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy (macOS)"
            ),
        ),
    )
    assert suffix.outcome == "failed"
    assert "signature_host_suffix" in _codes(suffix)

    spliced = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 明确提交契约\n\n"
                "关键变更:\n- 明确测试中的提交契约\n\n"
                "Session-ID: test-session\nModel-ID: workbuddy-hy3\nWorkbench-Name: Cindy"
            ),
        ),
    )
    assert spliced.outcome == "failed"
    assert "signature_model_host_product" in _codes(spliced)


def test_partial_new_signature_footer_requires_both_new_trailers(
    contract: CommitContractProjection,
) -> None:
    """只声明一个新 trailer 时必须补齐新三元组，不回退到旧集合。"""

    result = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 明确提交契约\n\n"
                "关键变更:\n- 明确测试中的提交契约\n\n"
                "Session-ID: test-session\nModel-ID: gpt-5.6-luna"
            ),
        ),
    )

    assert result.outcome == "failed"
    assert "signature_trailer_missing" in _codes(result)


def test_missing_signature_footer_messages_point_at_new_trailers(
    contract: CommitContractProjection,
) -> None:
    """新旧 trailer 全缺时，缺失引导指向 Model-ID/Workbench-Name 而非旧名称。"""

    result = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 明确提交契约\n\n"
                "关键变更:\n- 明确测试中的提交契约\n\n"
                "Session-ID: test-session"
            ),
        ),
    )

    assert result.outcome == "failed"
    messages = [issue.message for issue in result.issues if issue.code == "signature_trailer_missing"]
    assert any("非空 Model-ID" in message for message in messages)
    assert any("非空 Workbench-Name" in message for message in messages)
    assert not any("非空 Agent-ID" in message or "非空 Host-Environment" in message for message in messages)


def test_legacy_signature_footer_is_rejected_after_write_path_cancellation(
    contract: CommitContractProjection,
) -> None:
    """旧 trailer 写入路径取消后，即使不涉及事实流水也必须拒绝。"""

    result = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 旧署名拒绝\n\n"
                "关键变更:\n- 验证旧 trailer 已取消\n\n"
                "Session-ID: test-session\nAgent-ID: test-agent\nHost-Environment: test-environment"
            ),
        ),
    )

    assert result.outcome == "failed"
    assert "legacy_signature_trailer_retired" in _codes(result)


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
            field("change_log.signature.model_id"),
            field("change_log.signature.agent_workbench"),
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
    "      model_id: gpt-5.6-luna\n"
    "      agent_workbench: Cindy\n"
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


def _spark_schema_new_signature() -> FactSchema:
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
            field("change_log.signature.model_id"),
            field("change_log.signature.agent_workbench"),
            field("change_log.session_id"),
            field("change_log.at"),
            field("change_log.summary"),
        ),
    )


_NEW_SHAPE_SPARK = _VALID_SPARK
_LEGACY_SHAPE_SPARK = _VALID_SPARK.replace(
    b"      model_id: gpt-5.6-luna\n      agent_workbench: Cindy\n",
    b"      agent_id: test-agent\n      host_environment: test-environment\n",
)


def test_new_shape_fact_binding_accepts_declared_new_footer(
    contract: CommitContractProjection,
) -> None:
    """新形状流水与新 footer 的集合绑定成立即通过。"""

    message = (
        "docs(specs): 新形状提交\n\n"
        "关键变更:\n"
        "- 覆盖新形状受控写会话\n\n"
        "Session-ID: test-session\n"
        "Model-ID: gpt-5.6-luna\n"
        "Workbench-Name: Cindy"
    )

    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            fact_candidates=(_fact_candidate(data=_NEW_SHAPE_SPARK, head_exists=False),),
            fact_schemas=(_spark_schema_new_signature(),),
        ),
    )

    assert result.outcome == "passed", [f"{issue.code}: {issue.message}" for issue in result.issues]


def test_new_shape_fact_binding_rejects_undeclared_model(
    contract: CommitContractProjection,
) -> None:
    """新形状流水的 model_id 未被新 footer 声明：拒绝。"""

    result = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 未声明模型\n\n"
                "关键变更:\n- 验证 footer 集合绑定\n\n"
                "Session-ID: test-session\n"
                "Model-ID: other-model\n"
                "Workbench-Name: Cindy"
            ),
            fact_candidates=(_fact_candidate(data=_NEW_SHAPE_SPARK, head_exists=False),),
            fact_schemas=(_spark_schema_new_signature(),),
        ),
    )

    assert result.outcome == "failed"
    assert "fact_trace_signature_mismatch" in _codes(result)


def test_new_footer_does_not_bind_legacy_shape_entries(
    contract: CommitContractProjection,
) -> None:
    """新 footer 不为旧形状流水背书：混合形状提交按绑定失败拒绝。"""

    message = (
        "docs(specs): 混合形状提交\n\n"
        "关键变更:\n"
        "- 覆盖混合形状流水\n\n"
        "Session-ID: test-session\n"
        "Model-ID: gpt-5.6-luna\n"
        "Workbench-Name: Cindy"
    )

    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            fact_candidates=(_fact_candidate(data=_LEGACY_SHAPE_SPARK, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "failed"
    assert "legacy_signature_write_retired" in _codes(result)


def test_legacy_shape_change_log_is_rejected_even_with_legacy_footer(
    contract: CommitContractProjection,
) -> None:
    """旧形状流水与旧 footer 一并出现时，旧写入路径仍机械拒绝。"""

    message = (
        "docs(specs): 拒绝旧形状流水\n\n"
        "关键变更:\n"
        "- 验证旧签名写入路径已取消\n\n"
        "Session-ID: test-session\n"
        "Agent-ID: test-agent\n"
        "Host-Environment: test-environment"
    )
    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            fact_candidates=(_fact_candidate(data=_LEGACY_SHAPE_SPARK, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "failed"
    assert "legacy_signature_trailer_retired" in _codes(result)


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
    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: gpt-5.6-luna\n"
            "      agent_workbench: Cindy\n"
            "    session_id: test-session\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: 补充测试火花\n"
        ).encode()
    )

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
    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: gpt-5.6-luna\n"
            "      agent_workbench: Cindy\n"
            "    session_id: another-session\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: 补充测试火花\n"
        ).encode()
    )

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
        "      model_id: gpt-5.6-luna\n"
        "      agent_workbench: Cindy\n"
        "    session_id: test-session\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: Human授权兼容旧数据：建立可信流水起点\n"
    ).encode()

    result = validate_commit(
        contract,
        _input(
            contract,
            fact_candidates=(_fact_candidate(data=data, head_exists=True, head_data=head_data),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    print("L3:", [(i.code, i.message) for i in result.issues])
    assert result.outcome == "passed"


def test_new_fact_multiple_sessions_match_multiple_footer_session_ids(
    contract: CommitContractProjection,
) -> None:
    """新对象多条 change_log 分属多个 session：footer 声明全部 Session-ID 即通过。"""

    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: gpt-5.6-luna\n"
            "      agent_workbench: Cindy\n"
            "    session_id: test-session-2\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: 第二个受控写会话\n"
        ).encode()
    )
    message = (
        "docs(specs): 多会话提交\n\n"
        "关键变更:\n"
        "- 覆盖多个受控写会话\n\n"
        "Session-ID: test-session\n"
        "Session-ID: test-session-2\n"
        "Model-ID: gpt-5.6-luna\n"
        "Workbench-Name: Cindy"
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

    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: test-agent\n"
            "      agent_workbench: test-environment\n"
            "    session_id: ghost-session\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: 未声明会话\n"
        ).encode()
    )

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


def test_new_fact_multiple_agents_match_multiple_footer_model_ids(
    contract: CommitContractProjection,
) -> None:
    """新对象跨多模型/宿主流水：footer 声明全部新三元组值即通过。"""

    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: another-model\n"
            "      agent_workbench: Other Host\n"
            "    session_id: test-session-2\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: 第二个执行者\n"
        ).encode()
    )
    message = (
        "docs(specs): 多执行者提交\n\n"
        "关键变更:\n"
        "- 覆盖多个执行者流水\n\n"
        "Session-ID: test-session\n"
        "Session-ID: test-session-2\n"
        "Model-ID: gpt-5.6-luna\n"
        "Model-ID: another-model\n"
        "Workbench-Name: Cindy\n"
        "Workbench-Name: Other Host"
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

    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: ghost-agent\n"
            "      agent_workbench: ghost-env\n"
            "    session_id: test-session-2\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: 未声明执行者\n"
        ).encode()
    )
    message = (
        "docs(specs): 未声明执行者\n\n"
        "Session-ID: test-session\n"
        "Session-ID: test-session-2\n"
        "Model-ID: test-agent\n"
        "Workbench-Name: test-environment"
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
    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: another-model\n"
            "      agent_workbench: Other Host\n"
            "    session_id: test-session-2\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: Human授权兼容旧数据：第二个执行者迁移\n"
        ).encode()
    )
    message = (
        "docs(specs): 多执行者迁移提交\n\n"
        "关键变更:\n"
        "- 迁移多个执行者的遗留流水\n\n"
        "Session-ID: test-session\n"
        "Session-ID: test-session-2\n"
        "Model-ID: gpt-5.6-luna\n"
        "Model-ID: another-model\n"
        "Workbench-Name: Cindy\n"
        "Workbench-Name: Other Host"
    )

    result = validate_commit(
        contract,
        _input(
            contract,
            message=message,
            fact_candidates=(_fact_candidate(data=data, head_exists=True, head_data=head_data),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "passed"


# -- platform-related surface (L1 path matching + L2 trailer) -----------------


def test_platform_affected_positive_path_match() -> None:
    paths = ("code/ldvh/filesystem.py",)
    trailers: dict[str, list[str]] = {}
    issues = _platform_affected_issues(paths, trailers)
    codes = {i.code for i in issues}
    assert "platform_surface_touched" in codes
    assert "platform_trailer_required" in codes


def test_platform_affected_negative_path_no_match() -> None:
    paths = ("code/ldvh/something_else.py",)
    trailers: dict[str, list[str]] = {}
    issues = _platform_affected_issues(paths, trailers)
    assert issues == []


def test_platform_affected_with_valid_trailers() -> None:
    paths = ("code/ldvh/filesystem.py",)
    trailers = {"Platform-Affected": ["macos"], "Platform-Verified": ["macos"]}
    issues = _platform_affected_issues(paths, trailers)
    # With valid trailers, no issues are emitted (the check passes silently).
    assert issues == []


def test_platform_affected_invalid_trailer_value() -> None:
    paths = ("code/ldvh/filesystem.py",)
    trailers = {"Platform-Affected": ["invalid"], "Platform-Verified": ["none"]}
    issues = _platform_affected_issues(paths, trailers)
    codes = {i.code for i in issues}
    assert "platform_trailer_invalid" in codes
    assert "platform_surface_touched" in codes


def test_platform_affected_glob_directory() -> None:
    paths = ("code/ldvh/git_hooks/commit_msg.py",)
    trailers: dict[str, list[str]] = {}
    issues = _platform_affected_issues(paths, trailers)
    codes = {i.code for i in issues}
    assert "platform_surface_touched" in codes


def test_platform_affected_glob_hooks_dir() -> None:
    paths = ("code/ldvh/hooks/commit_msg.py",)
    trailers: dict[str, list[str]] = {}
    issues = _platform_affected_issues(paths, trailers)
    codes = {i.code for i in issues}
    assert "platform_surface_touched" in codes


def test_platform_affected_glob_launcher() -> None:
    paths = ("ldvh",)
    trailers: dict[str, list[str]] = {}
    issues = _platform_affected_issues(paths, trailers)
    codes = {i.code for i in issues}
    assert "platform_surface_touched" in codes


def test_platform_affected_glob_multiple_matches() -> None:
    paths = ("code/ldvh/filesystem.py", "code/ldvh/governance/git.py", "code/tests/other.py")
    trailers: dict[str, list[str]] = {}
    issues = _platform_affected_issues(paths, trailers)
    codes = {i.code for i in issues}
    assert "platform_surface_touched" in codes
    matched = [i for i in issues if i.code == "platform_surface_touched"]
    assert matched
    assert "code/ldvh/filesystem.py" in matched[0].message
    assert "code/ldvh/governance/git.py" in matched[0].message
    assert "code/tests/other.py" not in matched[0].message


def test_platform_affected_verified_missing() -> None:
    paths = ("code/ldvh/filesystem.py",)
    trailers = {"Platform-Affected": ["macos"]}
    issues = _platform_affected_issues(paths, trailers)
    codes = {i.code for i in issues}
    assert "platform_trailer_required" in codes


def test_platform_affected_affected_missing() -> None:
    paths = ("code/ldvh/filesystem.py",)
    trailers = {"Platform-Verified": ["macos"]}
    issues = _platform_affected_issues(paths, trailers)
    codes = {i.code for i in issues}
    assert "platform_trailer_required" in codes


def test_platform_affected_all_valid_values() -> None:
    for val in ("macos", "windows", "both", "unaffected"):
        paths = ("code/ldvh/filesystem.py",)
        trailers = {"Platform-Affected": [val], "Platform-Verified": ["none"]}
        issues = _platform_affected_issues(paths, trailers)
        assert not any(i.code == "platform_trailer_invalid" for i in issues)


def test_platform_affected_all_verified_values() -> None:
    for val in ("macos", "windows", "both", "none"):
        paths = ("code/ldvh/filesystem.py",)
        trailers = {"Platform-Affected": ["unaffected"], "Platform-Verified": [val]}
        issues = _platform_affected_issues(paths, trailers)
        assert not any(i.code == "platform_trailer_invalid" for i in issues)


def test_platform_affected_integration_through_validate_commit(
    contract: CommitContractProjection,
) -> None:
    """Platform surface paths without trailer declarations -> Git Gate fails."""
    message = (
        "docs(specs): 修改文件系统抽象层\n\n"
        "关键变更:\n- 调整锁实现\n\n"
        "Session-ID: test-session\nModel-ID: test-agent\nWorkbench-Name: test-environment"
    )
    result = validate_commit(
        contract,
        _input(contract, message=message, candidate_paths=("code/ldvh/filesystem.py",)),
    )
    assert result.outcome == "failed"
    assert "platform_trailer_required" in {i.code for i in result.issues}


def test_platform_affected_integration_with_trailers_passes(
    contract: CommitContractProjection,
) -> None:
    """Platform surface paths with valid trailer declarations -> Git Gate passes."""
    message = (
        "docs(specs): 修改文件系统抽象层\n\n"
        "关键变更:\n- 调整锁实现\n\n"
        "Session-ID: test-session\nModel-ID: test-agent\nWorkbench-Name: test-environment\n"
        "Platform-Affected: macos\nPlatform-Verified: macos"
    )
    result = validate_commit(
        contract,
        _input(contract, message=message, candidate_paths=("code/ldvh/filesystem.py",)),
    )
    assert result.outcome == "passed"


def test_platform_affected_integration_non_platform_path_passes(
    contract: CommitContractProjection,
) -> None:
    """Non-platform paths without trailer declarations -> Git Gate passes."""
    message = (
        "docs(specs): 改规范\n\n"
        "关键变更:\n- 修改说明\n\n"
        "Session-ID: test-session\nModel-ID: test-agent\nWorkbench-Name: test-environment"
    )
    result = validate_commit(
        contract,
        _input(contract, message=message, candidate_paths=("code/some_other.py",)),
    )
    assert result.outcome == "passed"
