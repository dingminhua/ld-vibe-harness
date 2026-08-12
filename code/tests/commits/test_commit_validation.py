from __future__ import annotations

import re
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
        type_tokens=(
            "feat",
            "fix",
            "docs",
            "style",
            "refactor",
            "perf",
            "test",
            "build",
            "ci",
            "chore",
            "merge",
            "revert",
        ),
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
            "LDVH-Product-Name: Cindy\nLDVH-Model-Name: gpt-5.6-luna\nLDVH-Agent-Runtime-Name: codex-cli"
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
    message = values.get("message")
    if isinstance(message, str):
        values["message"] = _modernize_signature(message)
    return CommitValidationInput(**values)  # type: ignore[arg-type]


def _codes(result: object) -> set[str]:
    return {issue.code for issue in result.issues}  # type: ignore[attr-defined]


def _signed(message: str) -> str:
    if "\n关键变更:" not in message:
        message += "\n\n关键变更:\n- 覆盖当前测试变化"
    return message + "\n\nLDVH-Product-Name: Cindy\nLDVH-Model-Name: gpt-5.6-luna\nLDVH-Agent-Runtime-Name: codex-cli"


def _modernize_signature(message: str) -> str:
    """Keep broad commit tests focused on their subject, not retired fixtures."""

    cindy_old = "Session-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy"
    cindy_new = "LDVH-Product-Name: Cindy\nLDVH-Model-Name: gpt-5.6-luna\nLDVH-Agent-Runtime-Name: codex-cli"
    trae_old = "Session-ID: trae-commit-session\nModel-ID: claude-4.1\nWorkbench-Name: Trae"
    trae_new = "LDVH-Product-Name: TraeCode\nLDVH-Model-Name: claude-4.1"
    test_old = "Session-ID: test-session\nModel-ID: test-agent\nWorkbench-Name: Test"
    test_new = "LDVH-Product-Name: Test\nLDVH-Model-Name: test-agent\nLDVH-Agent-Runtime-Name: test-runtime"
    return (
        message.replace(cindy_old, cindy_new)
        .replace(trae_old, trae_new)
        .replace(test_old, test_new)
    )


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
        "Session-ID: test-session\nModel-ID: test-agent\nWorkbench-Name: Test\n"
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


def test_explicit_merge_commit_message_passes_the_same_contract(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(
            contract,
            message=_signed("merge: 合入已审阅的规则分支\n\n关键变更:\n- 将规则分支整合到当前历史线"),
        ),
    )

    assert result.outcome == "passed"


def test_automatic_git_merge_message_still_fails_without_body_or_signature(contract: CommitContractProjection) -> None:
    result = validate_commit(contract, _input(contract, message="Merge branch 'reviewed-rules'"))

    assert result.outcome == "failed"
    assert {"header_invalid", "body_required", "key_changes_required", "signature_trailer_missing"} <= _codes(result)


def test_crlf_and_leading_comments_are_normalized(contract: CommitContractProjection) -> None:
    message = (
        "# template\r\n\r\ndocs(specs): 明确提交契约\r\n\r\n"
        "关键变更:\r\n- 明确换行归一化\r\n\r\n"
            "LDVH-Product-Name: Cindy\r\nLDVH-Model-Name: gpt-5.6-luna\r\nLDVH-Agent-Runtime-Name: codex-cli\r\n"
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
    assert "legacy_signature_trailer_retired" in _codes(with_retired_legacy_trailer)


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


def test_signature_trailers_must_use_the_shared_normalized_values(contract: CommitContractProjection) -> None:
    result = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs: 规范署名 trailer\n\n关键变更:\n- 拒绝未归一的模型与运行时名称\n\n"
                "LDVH-Product-Name: Cindy\nLDVH-Model-Name: DeepSeek-V4-Flash[1m]\n"
                "LDVH-Agent-Runtime-Name: Codex CLI"
            ),
        ),
    )

    assert result.outcome == "failed"
    assert "signature_trailer_not_normalized" in _codes(result)


@pytest.mark.parametrize(
    ("duplicate_trailer", "duplicate_value"),
    [
        ("Session-ID", "another-session"),
        ("Model-ID", "another-model"),
        ("Workbench-Name", "Trae"),
    ],
)
def test_commit_signature_rejects_multiple_values_for_one_current_environment_field(
    contract: CommitContractProjection,
    duplicate_trailer: str,
    duplicate_value: str,
) -> None:
    message = (
        "docs(specs): 拒绝多环境提交签名\n\n"
        "关键变更:\n- 提交只声明实际执行的当前环境\n\n"
        "Session-ID: test-session\n"
        "Model-ID: gpt-5.6-luna\n"
        "Workbench-Name: Cindy\n"
        f"{duplicate_trailer}: {duplicate_value}"
    )

    result = validate_commit(contract, _input(contract, message=message))

    assert result.outcome == "failed"
    assert "legacy_signature_trailer_retired" in _codes(result)


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
    assert "legacy_signature_trailer_retired" in _codes(alias)

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
    assert "signature_trailer_not_normalized" in _codes(suffix)

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
    assert "legacy_signature_trailer_retired" in _codes(spliced)

    compound = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 明确提交契约\n\n"
                "关键变更:\n- 明确测试中的提交契约\n\n"
                "Session-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: claude-code-mcp"
            ),
        ),
    )
    assert compound.outcome == "failed"
    assert "legacy_signature_trailer_retired" in _codes(compound)


def test_signature_footer_rejects_model_family_workbench(contract: CommitContractProjection) -> None:
    """footer 的 Workbench-Name 不得是模型族 token（如 Gpt）。"""

    bad = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 提交署名\n\n"
                "关键变更:\n- 工作台名不得是模型族 token\n\n"
                "Session-ID: test-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Gpt"
            ),
        ),
    )
    assert bad.outcome == "failed"
    assert "legacy_signature_trailer_retired" in _codes(bad)

    # 旧 Workbench-Name 不再是新提交形状；不再按其内容重新解释。
    for wb in ("Workbuddy", "Cindy", "Claude"):
        ok = validate_commit(
            contract,
            _input(
                contract,
                message=(
                    "docs(specs): 提交署名\n\n"
                    "关键变更:\n- 合法工作台名\n\n"
                    f"LDVH-Product-Name: {wb}\nLDVH-Model-Name: gpt-5.6-luna"
                ),
            ),
        )
        assert ok.outcome == "passed", (wb, [f"{i.code}: {i.message}" for i in ok.issues])


def test_signature_footer_rejects_placeholder_session_id(contract: CommitContractProjection) -> None:
    """footer 的 Session-ID 不得为占位符（如 current-session）。"""

    bad = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 提交署名\n\n"
                "关键变更:\n- 会话标识不得为占位符\n\n"
                "Session-ID: current-session\nModel-ID: gpt-5.6-luna\nWorkbench-Name: Cindy"
            ),
        ),
    )
    assert bad.outcome == "failed"
    assert "legacy_signature_trailer_retired" in _codes(bad)

    # Session-ID 已退出新提交合同，不再按其取值区分合法性。
    for sid in ("test-session", "trae-commit-session", "fde0af60-4736-4d2d-b2eb-d0be116e163a"):
        ok = validate_commit(
            contract,
            _input(
                contract,
                message=(
                    "docs(specs): 提交署名\n\n"
                    "关键变更:\n- 合法会话标识\n\n"
                    f"LDVH-Product-Name: Cindy\nLDVH-Model-Name: gpt-5.6-luna\n"
                    f"LDVH-Agent-Runtime-Name: runtime-{sid}"
                ),
            ),
        )
        assert ok.outcome == "passed", (sid, [f"{i.code}: {i.message}" for i in ok.issues])


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
    assert any("LDVH 三字段署名" in message for message in messages)
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
            field("change_log.signature.product_name"),
            field("change_log.signature.model_name"),
            field("change_log.signature.agent_runtime_name"),
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
    "      product_name: Cindy\n"
    "      model_name: gpt-5.6-luna\n"
    "      agent_runtime_name: codex-cli\n"
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
    data = values.get("data")
    if isinstance(data, bytes) and data != _LEGACY_SHAPE_SPARK:
        values["data"] = _current_signature_fixture(data)
    return StagedFactCandidate(**values)  # type: ignore[arg-type]


def _current_signature_fixture(data: bytes) -> bytes:
    """Migrate generic success fixtures, while explicit legacy cases stay explicit."""

    return re.sub(
        rb"(?m)^(?P<indent>\s+)model_id: (?P<model>[^\n]+)\n"
        rb"(?P=indent)agent_workbench: (?P<product>[^\n]+)\n(?:\s+session_id: [^\n]+\n)?",
        lambda match: (
            match.group("indent")
            + b"product_name: "
            + match.group("product")
            + b"\n"
            + match.group("indent")
            + b"model_name: "
            + match.group("model")
            + b"\n"
            + match.group("indent")
            + b"agent_runtime_name: test-runtime\n"
        ),
        data,
    )


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
            field("change_log.signature.product_name"),
            field("change_log.signature.model_name"),
            field("change_log.signature.agent_runtime_name"),
            field("change_log.at"),
            field("change_log.summary"),
        ),
    )


_NEW_SHAPE_SPARK = _VALID_SPARK
_LEGACY_SHAPE_SPARK = _VALID_SPARK.replace(
    b"      product_name: Cindy\n      model_name: gpt-5.6-luna\n      agent_runtime_name: codex-cli\n",
    b"      agent_id: test-agent\n      host_environment: test-environment\n",
)


def test_new_shape_fact_trace_passes_with_same_commit_environment(
    contract: CommitContractProjection,
) -> None:
    """新形状流水与提交环境相同时依然通过。"""

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


def test_workbuddy_fact_trace_passes_when_trae_executes_commit(
    contract: CommitContractProjection,
) -> None:
    """WorkBuddy/Cindy 写入的流水不会覆盖 Trae 实际提交签名。"""

    result = validate_commit(
        contract,
        _input(
            contract,
            message=(
                "docs(specs): 跨环境提交\n\n"
                "关键变更:\n- 保留写入流水并由 Trae 提交\n\n"
                "Session-ID: trae-commit-session\n"
                "Model-ID: claude-4.1\n"
                "Workbench-Name: Trae"
            ),
            fact_candidates=(_fact_candidate(data=_NEW_SHAPE_SPARK, head_exists=False),),
            fact_schemas=(_spark_schema_new_signature(),),
        ),
    )

    assert result.outcome == "passed", [f"{issue.code}: {issue.message}" for issue in result.issues]


def test_new_footer_does_not_bind_legacy_shape_entries(
    contract: CommitContractProjection,
) -> None:
    """新 footer 不会使本次新写的旧形状流水变成合法。"""

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


def test_new_fact_change_log_session_is_independent_from_commit_session(
    contract: CommitContractProjection,
) -> None:
    different_writer_session = _VALID_SPARK.replace(b"session_id: test-session", b"session_id: another-session")
    result = validate_commit(
        contract,
        _input(
            contract,
            fact_candidates=(_fact_candidate(data=different_writer_session, head_exists=False),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "passed", [f"{issue.code}: {issue.message}" for issue in result.issues]


def test_new_fact_with_multiple_precommit_change_logs_keeps_writer_history(
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


def test_new_fact_multiple_writer_sessions_do_not_expand_commit_signature(
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

    assert result.outcome == "passed", [f"{issue.code}: {issue.message}" for issue in result.issues]


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


def test_first_real_update_three_field_log_passes_when_head_has_no_history(
    contract: CommitContractProjection,
) -> None:
    """HEAD 无 change_log、Working Tree 建立一条当前三字段首写流水：本次提交事件。"""

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
        "      product_name: Cindy\n"
        "      model_name: gpt-5.6-luna\n"
        "      agent_runtime_name: claude-code\n"
        "    at: 2026-07-01T01:00:00+08:00\n"
        "    summary: 首次真实更新建立流水；此前历史未恢复。\n"
    ).encode()

    result = validate_commit(
        contract,
        _input(
            contract,
            fact_candidates=(_fact_candidate(data=data, head_exists=True, head_data=head_data),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "passed"
    assert "fact_trace_append_invalid" not in _codes(result)
    assert "legacy_signature_write_retired" not in _codes(result)


def test_first_real_update_rejects_deleted_committed_history(
    contract: CommitContractProjection,
) -> None:
    """HEAD 已有 change_log 而 Working Tree 删除了它：不能以首写名义恢复历史。"""

    head_data = _VALID_SPARK
    data = _VALID_SPARK.split(b"change_log:\n")[0]

    result = validate_commit(
        contract,
        _input(
            contract,
            fact_candidates=(_fact_candidate(data=data, head_exists=True, head_data=head_data),),
            fact_schemas=(_spark_schema(),),
        ),
    )

    assert result.outcome == "failed"
    # Working Tree 删除了全部流水：候选缺失可校验 change_log 而 fail closed。
    assert "fact_trace_missing" in _codes(result)


def test_new_fact_multiple_writer_sessions_use_one_trae_commit_session(
    contract: CommitContractProjection,
) -> None:
    """多个写入会话保留自身流水，footer 只声明当次 Trae 提交会话。"""

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
        "- 保留多个受控写会话并由 Trae 提交\n\n"
        "Session-ID: trae-commit-session\n"
        "Model-ID: claude-4.1\n"
        "Workbench-Name: Trae"
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


def test_new_fact_writer_session_need_not_be_declared_by_commit_footer(
    contract: CommitContractProjection,
) -> None:
    """新对象流水保留写入会话，不写入提交 footer。"""

    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: test-agent\n"
            "      agent_workbench: Test\n"
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

    assert result.outcome == "passed", [f"{issue.code}: {issue.message}" for issue in result.issues]


def test_new_fact_multiple_writers_use_one_trae_commit_signature(
    contract: CommitContractProjection,
) -> None:
    """新对象跨多模型/宿主写入后，footer 只声明当次 Trae 提交环境。"""

    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: another-model\n"
            "      agent_workbench: Other\n"
            "    session_id: test-session-2\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: 第二个执行者\n"
        ).encode()
    )
    message = (
        "docs(specs): 多执行者提交\n\n"
        "关键变更:\n"
        "- 保留多个执行者流水并由 Trae 提交\n\n"
        "Session-ID: trae-commit-session\n"
        "Model-ID: claude-4.1\n"
        "Workbench-Name: Trae"
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


def test_new_fact_writer_environment_need_not_be_declared_by_commit_footer(
    contract: CommitContractProjection,
) -> None:
    """新对象流水保留写入环境，不要求提交环境相同。"""

    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: ghost-agent\n"
            "      agent_workbench: Ghost\n"
            "    session_id: test-session-2\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: 未声明执行者\n"
        ).encode()
    )
    message = (
        "docs(specs): 未声明执行者\n\n"
        "关键变更:\n- 保留写入环境并由 Trae 提交\n\n"
        "Session-ID: trae-commit-session\n"
        "Model-ID: claude-4.1\n"
        "Workbench-Name: Trae"
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

    assert result.outcome == "passed", [f"{issue.code}: {issue.message}" for issue in result.issues]


def test_legacy_migration_multiple_writers_uses_one_commit_signature(
    contract: CommitContractProjection,
) -> None:
    """legacy 迁移对象跨多写入者时，footer 仍只声明当次提交环境。"""

    head_data = _VALID_SPARK.split(b"change_log:\n")[0]
    data = (
        _VALID_SPARK.replace(
            b"updated_at: 2026-07-01T00:00:00+08:00",
            b"updated_at: 2026-07-01T01:00:00+08:00",
        )
        + (
            "  - signature:\n"
            "      model_id: another-model\n"
            "      agent_workbench: Other\n"
            "    session_id: test-session-2\n"
            "    at: 2026-07-01T01:00:00+08:00\n"
            "    summary: Human授权兼容旧数据：第二个执行者迁移\n"
        ).encode()
    )
    message = (
        "docs(specs): 多执行者迁移提交\n\n"
        "关键变更:\n"
        "- 迁移多个写入者的遗留流水并由 Trae 提交\n\n"
        "Session-ID: trae-commit-session\n"
        "Model-ID: claude-4.1\n"
        "Workbench-Name: Trae"
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
        "Session-ID: test-session\nModel-ID: test-agent\nWorkbench-Name: Test"
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
        "Session-ID: test-session\nModel-ID: test-agent\nWorkbench-Name: Test\n"
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
        "Session-ID: test-session\nModel-ID: test-agent\nWorkbench-Name: Test"
    )
    result = validate_commit(
        contract,
        _input(contract, message=message, candidate_paths=("code/some_other.py",)),
    )
    assert result.outcome == "passed"
