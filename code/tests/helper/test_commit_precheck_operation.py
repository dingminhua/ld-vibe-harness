from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from conftest import assert_common_response

from ldvh.commits import git_adapter
from ldvh.helper import rule_source
from ldvh.helper.service import handle_request
from ldvh.hooks.commit_msg import CommitMsgGateResult, run_commit_msg_gate


def _git(project: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _memoize_rule_repository_inspection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse the unchanged LDVH rule source once per test across both entrypoints."""

    real_inspect = rule_source.inspect_repository
    inspect_cache: dict[Path, object] = {}

    def memoized_inspect(repository_root: Path):
        if repository_root not in inspect_cache:
            inspect_cache[repository_root] = real_inspect(repository_root)
        return inspect_cache[repository_root]

    monkeypatch.setattr(rule_source, "inspect_repository", memoized_inspect)


def _fixture(tmp_path: Path, *, staged: bool = True) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
                "product_description: Git commit precheck tests.",
                "projects:",
                "  - id: sample",
                f"    path: {project}",
                "    name: Sample",
                "    description: Test project.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (project / "change.txt").write_text("candidate\n", encoding="utf-8")
    if staged:
        _git(project, "add", "change.txt")
    return workspace, project


def _payload(workspace: Path, project: Path, message: str) -> str:
    signed = _signed(message) if message else message
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "message": signed,
            },
        }
    )


def _state(project: Path) -> tuple[bytes, bytes]:
    return (
        _git(project, "status", "--porcelain=v2", "-z"),
        _git(project, "ls-files", "--stage", "-z"),
    )


def _gate(workspace: Path, project: Path, message: str) -> CommitMsgGateResult:
    message_file = workspace / "COMMIT_EDITMSG"
    message_file.write_text(_signed(message) if message else message, encoding="utf-8")
    return run_commit_msg_gate(
        workspace_root=str(workspace),
        worktree=str(project),
        message_file=str(message_file),
    )


def _signed(message: str) -> str:
    return (
        message
        + "\n\n关键变更:\n- 覆盖当前提交预检测试变化"
        + "\n\nLDVH-Product-Name: Cindy\nLDVH-Model-Name: gpt-5.6-luna\nLDVH-Agent-Runtime-Name: pytest"
    )


def _trae_signed(message: str) -> str:
    return (
        message
        + "\n\n关键变更:\n- 由 Trae 提交其它环境已完成的事实写入"
        + "\n\nLDVH-Product-Name: Trae\nLDVH-Model-Name: claude-4.1\nLDVH-Agent-Runtime-Name: pytest"
    )


def _helper_issues_as_gate_diagnostics(response: dict[str, object]) -> tuple[str, ...]:
    result = response["result"]
    assert isinstance(result, dict)
    issues = result["issues"]
    assert isinstance(issues, list)
    return tuple(f"validation/{item['code']}: {item['message']}" for item in issues)


def test_helper_precheck_and_native_gate_share_one_bound_result(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    message = "test: 验证提交机械预检"
    before = _state(project)

    helper = handle_request("call", "precheck-git-commit", _payload(workspace, project, message))
    gate = _gate(workspace, project, message)

    response = helper.response
    assert helper.exit_code == 0
    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["result"]["mechanical_outcome"] == gate.outcome == "passed"
    assert response["result"]["issues"] == []
    assert response["result"]["candidate"]["paths"] == ["change.txt"]
    assert response["result"]["candidate"]["snapshot_identity"] == gate.snapshot_identity
    assert response["result"]["contract"]["source_fingerprint"] == gate.source_fingerprint
    assert response["result"]["semantic_checks_required"]
    assert response["scope"]["governance_resolution"]["scope_status"] == "governed_single"
    assert response["changes"] == []
    assert _state(project) == before


def test_single_path_without_minimum_body_fails_identically_in_helper_and_native_gate(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    message = (
            "test: 验证单文件最低正文\n\nLDVH-Product-Name: Cindy\n"
            "LDVH-Model-Name: gpt-5.6-luna\nLDVH-Agent-Runtime-Name: pytest"
    )
    payload = json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {"workspace_root": str(workspace), "message": message},
        }
    )
    message_file = workspace / "COMMIT_EDITMSG"
    message_file.write_text(message, encoding="utf-8")

    helper = handle_request("call", "precheck-git-commit", payload)
    gate = run_commit_msg_gate(
        workspace_root=str(workspace),
        worktree=str(project),
        message_file=str(message_file),
    )

    assert helper.exit_code == 0
    assert helper.response["result"]["mechanical_outcome"] == gate.outcome == "failed"
    assert {item["code"] for item in helper.response["result"]["issues"]} == {
        "body_required",
        "key_changes_required",
    }
    assert _helper_issues_as_gate_diagnostics(helper.response) == gate.issues
    assert helper.response["result"]["candidate"]["snapshot_identity"] == gate.snapshot_identity
    assert helper.response["result"]["contract"]["source_fingerprint"] == gate.source_fingerprint


def test_mechanical_failure_is_a_completed_read_not_helper_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _memoize_rule_repository_inspection(monkeypatch)
    workspace, project = _fixture(tmp_path)
    message = "not a valid commit message"
    result = handle_request(
        "call",
        "precheck-git-commit",
        _payload(workspace, project, message),
    )
    gate = _gate(workspace, project, message)

    assert result.exit_code == 0
    assert result.response["outcome"] == "ok"
    assert result.response["result"]["mechanical_outcome"] == gate.outcome == "failed"
    assert {item["code"] for item in result.response["result"]["issues"]} == {"header_invalid"}
    assert _helper_issues_as_gate_diagnostics(result.response) == gate.issues
    assert result.response["result"]["candidate"]["snapshot_identity"] == gate.snapshot_identity
    assert result.response["result"]["contract"]["source_fingerprint"] == gate.source_fingerprint
    assert result.response["scope"]["requested"] == result.response["scope"]["completed"]
    assert result.response["scope"]["not_completed"] == []


def test_empty_message_reaches_the_shared_validator(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    result = handle_request("call", "precheck-git-commit", _payload(workspace, project, ""))

    assert result.exit_code == 0
    assert result.response["outcome"] == "ok"
    assert result.response["result"]["mechanical_outcome"] == "failed"
    assert {item["code"] for item in result.response["result"]["issues"]} == {"message_empty"}


def test_empty_candidate_is_a_completed_unverifiable_mechanical_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _memoize_rule_repository_inspection(monkeypatch)
    workspace, project = _fixture(tmp_path, staged=False)
    message = "test: 验证空候选"
    result = handle_request(
        "call",
        "precheck-git-commit",
        _payload(workspace, project, message),
    )
    gate = _gate(workspace, project, message)

    assert result.exit_code == 0
    assert result.response["outcome"] == "ok"
    assert result.response["result"]["mechanical_outcome"] == gate.outcome == "unverifiable"
    assert result.response["result"]["candidate"]["paths"] == []
    assert {item["code"] for item in result.response["result"]["issues"]} == {"candidate_paths_empty"}
    assert _helper_issues_as_gate_diagnostics(result.response) == gate.issues
    assert result.response["result"]["candidate"]["snapshot_identity"] == gate.snapshot_identity
    assert result.response["result"]["contract"]["source_fingerprint"] == gate.source_fingerprint


def test_linked_worktree_uses_its_own_index_through_both_entrypoints(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _git(
        project,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "test: 建立链接工作树基线",
    )
    linked = workspace / "linked"
    _git(project, "worktree", "add", "-qb", "linked-precheck", str(linked))
    (linked / "linked.txt").write_text("linked\n", encoding="utf-8")
    _git(linked, "add", "linked.txt")
    message = "test: 验证链接工作树预检"

    helper = handle_request("call", "precheck-git-commit", _payload(workspace, linked, message))
    gate = _gate(workspace, linked, message)

    assert helper.exit_code == 0
    assert helper.response["result"]["mechanical_outcome"] == gate.outcome == "passed"
    assert helper.response["result"]["candidate"]["git_worktree_root"] == str(linked.resolve())
    assert helper.response["result"]["candidate"]["paths"] == ["linked.txt"]
    assert helper.response["result"]["candidate"]["snapshot_identity"] == gate.snapshot_identity
    assert _git(project, "diff", "--cached", "--name-only") == b""


def test_observation_drift_remains_an_unavailable_helper_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    original = git_adapter._candidate_paths

    def drift(worktree: Path):
        (worktree / "drift.txt").write_text("drift\n", encoding="utf-8")
        _git(worktree, "add", "drift.txt")
        return original(worktree)

    monkeypatch.setattr(git_adapter, "_candidate_paths", drift)
    result = handle_request(
        "call",
        "precheck-git-commit",
        _payload(workspace, project, "test: 验证候选漂移"),
    )

    assert result.exit_code == 5
    assert result.response["outcome"] == "unavailable"
    assert result.response["result"] is None
    assert any(
        item["details"].get("stage") == "candidate" and item["details"].get("code") == "drift"
        for item in result.response["diagnostics"]
    )


def test_git_read_failure_remains_an_unavailable_helper_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)

    def fail_git_read(
        _worktree: Path,
        _arguments: tuple[str, ...],
        *,
        index_file: Path | None = None,
    ) -> git_adapter.CommitCandidateObservationIssue:
        del index_file
        return git_adapter.CommitCandidateObservationIssue("git_process", "denied")

    monkeypatch.setattr(git_adapter, "_run_git", fail_git_read)
    result = handle_request(
        "call",
        "precheck-git-commit",
        _payload(workspace, project, "test: 验证 Git 读取失败"),
    )

    assert result.exit_code == 5
    assert result.response["outcome"] == "unavailable"
    assert result.response["result"] is None
    assert any(
        item["details"].get("stage") == "candidate" and item["details"].get("code") == "git_process"
        for item in result.response["diagnostics"]
    )


def test_capabilities_separates_callable_operation_from_failed_candidate(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    result = handle_request(
        "capabilities",
        "precheck-git-commit",
        _payload(workspace, project, "invalid"),
    )

    assert result.exit_code == 0
    operation = result.response["result"]["operations"][0]
    assert operation["availability"] == "available_for_request"
    assert operation["required_inputs"] == ["work_object_locators", "arguments.message"]
    assert operation["optional_inputs"] == ["arguments.workspace_root"]


def test_helper_does_not_accept_an_index_file_or_multiple_targets(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    unknown_argument = json.loads(_payload(workspace, project, "test: 验证输入边界"))
    unknown_argument["arguments"]["index_file"] = "/tmp/another-index"
    multiple_targets = json.loads(_payload(workspace, project, "test: 验证输入边界"))
    multiple_targets["work_object_locators"].append(str(project))

    unknown = handle_request("call", "precheck-git-commit", json.dumps(unknown_argument))
    multiple = handle_request("call", "precheck-git-commit", json.dumps(multiple_targets))

    assert unknown.exit_code == multiple.exit_code == 2
    assert unknown.response["outcome"] == multiple.response["outcome"] == "invalid_request"
    assert any("index_file" in item["summary"] for item in unknown.response["gaps"])
    assert any("恰有一个" in item["summary"] for item in multiple.response["gaps"])


def test_helper_ignores_ambient_git_index_redirection(tmp_path: Path, monkeypatch) -> None:
    workspace, project = _fixture(tmp_path)
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "untrusted-index"))

    result = handle_request(
        "call",
        "precheck-git-commit",
        _payload(workspace, project, "test: 验证环境隔离"),
    )

    assert result.exit_code == 0
    assert result.response["result"]["mechanical_outcome"] == "passed"
    assert result.response["result"]["candidate"]["paths"] == ["change.txt"]


def test_non_governed_target_is_unavailable_not_a_false_mechanical_result(tmp_path: Path) -> None:
    workspace, _ = _fixture(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    _git(other, "init", "-q")
    (other / "change.txt").write_text("candidate\n", encoding="utf-8")
    _git(other, "add", "change.txt")

    result = handle_request(
        "call",
        "precheck-git-commit",
        _payload(workspace, other, "test: 验证非管辖项目"),
    )

    assert result.exit_code == 5
    assert result.response["outcome"] == "unavailable"
    assert result.response["result"] is None
    assert result.response["scope"]["completed"] == []
    assert result.response["scope"]["not_completed"]


# -- specs 03 §9.9 staged fact-candidate layer, both entrypoints ------------

_FACT_PATH = "ldvh-base/sparks/spark-0001.yaml"
_VALID_SPARK = (
    "title: 测试火花\n"
    "intent: 验证提交边界事实候选机械校验\n"
    "status: open\n"
    "priority: P1\n"
    "summary: 测试摘要\n"
    "object_id: spark-0001\n"
    "fact_type_key: spark\n"
    "created_at: '2026-07-01T00:00:00+08:00'\n"
    "updated_at: '2026-07-01T00:00:00+08:00'\n"
    "change_log:\n"
    "  - signature:\n"
    "      product_name: Cindy\n"
    "      model_name: gpt-5.6-luna\n"
    "      agent_runtime_name: pytest\n"
    "    at: '2026-07-01T00:00:00+08:00'\n"
    "    summary: 建立测试火花\n"
)


def _stage_fact(project: Path, content: str, path: str = _FACT_PATH) -> None:
    target = project / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    _git(project, "add", path)


def test_invalid_staged_fact_candidate_blocks_both_entrypoints(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _stage_fact(project, "title: 只有标题\n")
    _git(project, "reset", "-q", "change.txt")
    message = "test: 验证非法事实候选拦截"

    helper = handle_request("call", "precheck-git-commit", _payload(workspace, project, message))
    gate = _gate(workspace, project, message)

    assert helper.exit_code == 0
    assert helper.response["outcome"] == "ok"
    assert helper.response["result"]["mechanical_outcome"] == gate.outcome == "failed"
    codes = {item["code"] for item in helper.response["result"]["issues"]}
    assert codes == {"fact_candidate_invalid"}
    assert all(_FACT_PATH in item["message"] for item in helper.response["result"]["issues"])
    assert _helper_issues_as_gate_diagnostics(helper.response) == gate.issues


def test_valid_staged_fact_candidate_passes_both_entrypoints(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _stage_fact(project, _VALID_SPARK)
    _git(project, "reset", "-q", "change.txt")
    message = "test: 验证合法事实候选通过"

    helper = handle_request("call", "precheck-git-commit", _payload(workspace, project, message))
    gate = _gate(workspace, project, message)

    assert helper.exit_code == 0
    assert helper.response["result"]["mechanical_outcome"] == gate.outcome == "passed"
    assert helper.response["result"]["issues"] == []
    assert helper.response["result"]["candidate"]["paths"] == [_FACT_PATH]


def test_workbuddy_fact_passes_helper_and_gate_when_trae_executes_commit(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workbuddy_fact = (
        _VALID_SPARK.replace("product_name: Cindy", "product_name: WorkBuddy")
        .replace("model_name: gpt-5.6-luna", "model_name: hy3")
    )
    _stage_fact(project, workbuddy_fact)
    _git(project, "reset", "-q", "change.txt")
    message = _trae_signed("test: 验证跨环境事实提交")
    payload = json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {"workspace_root": str(workspace), "message": message},
        }
    )
    message_file = workspace / "COMMIT_EDITMSG"
    message_file.write_text(message, encoding="utf-8")

    helper = handle_request("call", "precheck-git-commit", payload)
    gate = run_commit_msg_gate(
        workspace_root=str(workspace),
        worktree=str(project),
        message_file=str(message_file),
    )

    assert helper.exit_code == 0
    assert helper.response["result"]["mechanical_outcome"] == gate.outcome == "passed"
    assert helper.response["result"]["issues"] == []
    assert helper.response["result"]["candidate"]["paths"] == [_FACT_PATH]


def test_illegal_object_id_filename_blocks_both_entrypoints(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _stage_fact(project, _VALID_SPARK, path="ldvh-base/sparks/not-a-spark.yaml")
    _git(project, "reset", "-q", "change.txt")
    message = "test: 验证非法 object_id 拦截"

    helper = handle_request("call", "precheck-git-commit", _payload(workspace, project, message))
    gate = _gate(workspace, project, message)

    assert helper.exit_code == 0
    assert helper.response["result"]["mechanical_outcome"] == gate.outcome == "failed"
    codes = {item["code"] for item in helper.response["result"]["issues"]}
    assert codes == {"fact_object_id_invalid"}
    assert _helper_issues_as_gate_diagnostics(helper.response) == gate.issues


def test_no_fact_candidate_means_no_schema_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ldvh.commits import precheck as commit_precheck

    workspace, project = _fixture(tmp_path)
    monkeypatch.setattr(
        commit_precheck,
        "project_fact_schemas",
        lambda *args, **kwargs: pytest.fail("无事实候选不得形成事实 Schema 投影"),
    )
    message = "test: 验证零事实候选惰性"

    helper = handle_request("call", "precheck-git-commit", _payload(workspace, project, message))
    gate = _gate(workspace, project, message)

    assert helper.exit_code == 0
    assert helper.response["result"]["mechanical_outcome"] == gate.outcome == "passed"
    assert helper.response["result"]["issues"] == []
