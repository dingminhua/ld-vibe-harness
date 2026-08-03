from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from ldvh.commits.candidate_index import prepare_commit_candidate
from ldvh.commits.contract_source import ATTACHMENT_KEY, CommitContractProjection, project_commit_contract
from ldvh.commits.execution import CallerCommitApproval, execute_prepared_commit
from ldvh.git_hooks import commit_msg
from ldvh.git_hooks.commit_msg import (
    CommitMsgHookStatus,
    bootstrap_commit_msg_hook,
    inspect_commit_msg_hook,
    install_commit_msg_hook,
    render_commit_msg_hook,
    uninstall_commit_msg_hook,
)
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.governance.resolver import resolve_governance_scope
from ldvh.specs.repository import inspect_repository

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in (
        "GIT_COMMON_DIR",
        "GIT_CONFIG_COUNT",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_WORK_TREE",
    ):
        environment.pop(key, None)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "LDVH Test",
            "GIT_AUTHOR_EMAIL": "ldvh@example.invalid",
            "GIT_COMMITTER_NAME": "LDVH Test",
            "GIT_COMMITTER_EMAIL": "ldvh@example.invalid",
        }
    )
    return environment


def test_hook_git_environment_uses_shared_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "attacker.gitconfig")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "attacker-system.gitconfig")

    environment = commit_msg._installation_environment()

    assert environment["GIT_CONFIG_GLOBAL"] == os.devnull
    assert environment["GIT_CONFIG_NOSYSTEM"] == "1"
    assert "GIT_CONFIG_SYSTEM" not in environment


def _git(path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", "-C", str(path), *arguments),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        env=_environment(),
    )


def _checked_git(path: Path, *arguments: str) -> str:
    completed = _git(path, *arguments)
    assert completed.returncode == 0, (arguments, completed.stdout, completed.stderr)
    return completed.stdout


def _signed(message: str) -> str:
    return message + "\n\nSession-ID: test-session\nSigner-Type: ai-agent\nAgent-ID: test-agent\nHost-Environment: test-environment"


def _managed_project(tmp_path: Path, *, governed: bool = True) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _checked_git(project, "init", "-q")
    _checked_git(project, "config", "user.name", "LDVH Test")
    _checked_git(project, "config", "user.email", "ldvh@example.invalid")
    (project / "initial.txt").write_text("initial\n", encoding="utf-8")
    _checked_git(project, "add", "initial.txt")
    _checked_git(project, "commit", "-qm", "initial")
    projects = (
        (
            "projects:",
            "  - id: sample",
            f"    path: {project}",
            "    name: Sample",
            "    description: Temporary governed project.",
        )
        if governed
        else ("projects: []",)
    )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            (
                "product_name: Native Hook Tests",
                "product_description: Isolated native Git lifecycle tests.",
                *projects,
                "",
            )
        ),
        encoding="utf-8",
    )
    return workspace, project


def _runner(tmp_path: Path) -> Path:
    runner = tmp_path / "ldvh-git-commit-msg"
    runner.parent.mkdir(parents=True, exist_ok=True)
    source = shlex.quote(str(REPOSITORY_ROOT / "code"))
    executable = shlex.quote(sys.executable)
    runner.write_text(
        "\n".join(
            (
                "#!/bin/sh",
                f"PYTHONPATH={source}${{PYTHONPATH:+:$PYTHONPATH}}",
                "export PYTHONPATH",
                f'exec {executable} -X utf8 -m ldvh.hooks.commit_msg "$@"',
                "",
            )
        ),
        encoding="utf-8",
    )
    runner.chmod(0o755)
    return runner


def _install(tmp_path: Path, workspace: Path, project: Path) -> Path:
    runner = _runner(tmp_path)
    installed = install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )
    assert installed.state == "managed", installed
    assert installed.hook_path is not None
    return Path(installed.hook_path)


def _stage_active_file_asset(project: Path) -> tuple[str, str]:
    payload = b"objective audit bytes\n"
    directory = project / "ldvh-base/file-assets/file-asset-0001"
    directory.mkdir(parents=True)
    manifest_path = "ldvh-base/file-assets/file-asset-0001/file-asset.yaml"
    payload_path = "ldvh-base/file-assets/file-asset-0001/payload"
    (project / manifest_path).write_text(
        "".join(
            (
                "object_id: file-asset-0001\n",
                "fact_type_key: file-asset\n",
                "title: 审计文件\n",
                'created_at: "2026-07-31T10:00:00+08:00"\n',
                'updated_at: "2026-07-31T10:00:00+08:00"\n',
                "status: active\n",
                "filename: audit.bin\n",
                "media_type: application/octet-stream\n",
                f"size_bytes: {len(payload)}\n",
                f"content_sha256: {hashlib.sha256(payload).hexdigest()}\n",
                "signature:\n",
                "  signer_type: human\n",
            )
        ),
        encoding="utf-8",
    )
    (project / payload_path).write_bytes(payload)
    _checked_git(project, "add", manifest_path, payload_path)
    return manifest_path, payload_path


def _stage_deleted_file_asset(project: Path, manifest_path: str, payload_path: str, blob_oid: str) -> None:
    commit = _checked_git(project, "rev-parse", "HEAD").strip()
    payload = b"objective audit bytes\n"
    (project / manifest_path).write_text(
        "".join(
            (
                "object_id: file-asset-0001\n",
                "fact_type_key: file-asset\n",
                "title: 审计文件\n",
                'created_at: "2026-07-31T10:00:00+08:00"\n',
                'updated_at: "2026-08-01T10:00:00+08:00"\n',
                "status: deleted\n",
                "filename: audit.bin\n",
                "media_type: application/octet-stream\n",
                f"size_bytes: {len(payload)}\n",
                f"content_sha256: {hashlib.sha256(payload).hexdigest()}\n",
                "signature:\n",
                "  signer_type: human\n",
                "disposition_summary: Human 确认不再保留当前 payload。\n",
                'deleted_at: "2026-08-01T10:00:00+08:00"\n',
                "recovery:\n",
                f"  commit: {commit}\n",
                f"  path: {payload_path}\n",
                f"  blob_oid: {blob_oid}\n",
            )
        ),
        encoding="utf-8",
    )
    (project / payload_path).unlink(missing_ok=True)
    _checked_git(project, "add", "-A", str(Path(manifest_path).parent))


def _write_native_hook(project: Path, workspace: Path, runner: Path) -> Path:
    hook = project / ".git" / "hooks" / "commit-msg"
    hook.write_text(
        render_commit_msg_hook(commit_msg_runner=runner, workspace_root=workspace),
        encoding="utf-8",
    )
    hook.chmod(0o755)
    return hook


def _contract() -> CommitContractProjection:
    inspected = inspect_repository(REPOSITORY_ROOT)
    document = inspected.document_passing_implemented_checks_by_key("source-of-truth-traceability")
    assert document is not None
    attachment = inspected.document_passing_implemented_checks_by_key(ATTACHMENT_KEY)
    assert attachment is not None
    projected = project_commit_contract(document, attachment)
    assert projected.projection is not None, projected.issues
    return projected.projection


def test_native_commit_msg_hook_blocks_invalid_message_and_allows_valid_message(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path)
    hooks_config_before = _git(project, "config", "--get-all", "core.hooksPath")
    hook = _install(tmp_path, workspace, project)

    assert hook.is_file()
    assert os.access(hook, os.X_OK)
    hooks_config_after = _git(project, "config", "--get-all", "core.hooksPath")
    assert (hooks_config_after.returncode, hooks_config_after.stdout, hooks_config_after.stderr) == (
        hooks_config_before.returncode,
        hooks_config_before.stdout,
        hooks_config_before.stderr,
    )

    (project / "change.txt").write_text("change\n", encoding="utf-8")
    _checked_git(project, "add", "change.txt")
    before = _checked_git(project, "rev-parse", "HEAD").strip()
    rejected = _git(project, "commit", "-m", "docs: invalid")

    assert rejected.returncode != 0
    assert "description_cjk_missing" in rejected.stderr
    assert _checked_git(project, "rev-parse", "HEAD").strip() == before
    assert _checked_git(project, "diff", "--cached", "--name-only") == "change.txt\n"

    accepted = _git(project, "commit", "-m", _signed("docs: 增加提交校验"))

    assert accepted.returncode == 0, accepted.stderr
    assert _checked_git(project, "rev-parse", "HEAD").strip() != before
    assert _checked_git(project, "log", "-1", "--format=%B") == _signed("docs: 增加提交校验") + "\n\n"


def test_native_commit_msg_hook_blocks_forged_safe_delete_then_allows_exact_tombstone(
    tmp_path: Path,
) -> None:
    workspace, project = _managed_project(tmp_path)
    _install(tmp_path, workspace, project)
    manifest_path, payload_path = _stage_active_file_asset(project)
    active_commit = _git(
        project,
        "commit",
        "-m",
        _signed("test(file-asset): 建立安全删除基线\n\n关键变更:\n- 提交完整 active 载体"),
    )
    assert active_commit.returncode == 0, active_commit.stderr
    expected_blob = _checked_git(project, "rev-parse", f"HEAD:{payload_path}").strip()

    _stage_deleted_file_asset(project, manifest_path, payload_path, "f" * len(expected_blob))
    before = _checked_git(project, "rev-parse", "HEAD").strip()
    blocked = _git(
        project,
        "commit",
        "-m",
        _signed("test(file-asset): 拦截伪造恢复锚点\n\n关键变更:\n- 暂存伪造 deleted tombstone"),
    )

    assert blocked.returncode != 0
    assert "file_asset_delete_recovery_mismatch" in blocked.stderr
    assert _checked_git(project, "rev-parse", "HEAD").strip() == before

    _stage_deleted_file_asset(project, manifest_path, payload_path, expected_blob)
    allowed = _git(
        project,
        "commit",
        "-m",
        _signed("test(file-asset): 提交安全删除墓碑\n\n关键变更:\n- 提交精确 deleted tombstone"),
    )

    assert allowed.returncode == 0, allowed.stderr
    assert _checked_git(project, "rev-parse", "HEAD").strip() != before
    assert not (project / payload_path).exists()
    assert "status: deleted" in (project / manifest_path).read_text(encoding="utf-8")


def test_native_hook_observes_the_temporary_index_used_by_internal_commit_execution(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path)
    _install(tmp_path, workspace, project)
    (project / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    governance_run = resolve_governance_scope(
        (ScopeDescriptor(0, str(project), LocatorSource.EXPLICIT_LOCATOR),),
        base=project,
        explicit_workspace_root=workspace,
    )
    assert governance_run.result is not None
    candidate = prepare_commit_candidate(
        locator=str(project),
        base=project,
        message=_signed("feat: 增加临时候选提交"),
        selected_paths=("candidate.txt",),
        contract=_contract(),
        governance=governance_run.result,
    )
    assert candidate.outcome == "prepared", candidate.issues
    assert candidate.candidate is not None

    result = execute_prepared_commit(
        candidate=candidate.candidate,
        contract=_contract(),
        governance=governance_run.result,
        approval=CallerCommitApproval(True, True, True),
    )

    assert result.outcome == "created", result.issues
    assert result.actual_paths == ("candidate.txt",)


def test_native_hook_fails_closed_when_the_actual_worktree_is_not_governed(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path, governed=False)
    runner = _runner(tmp_path)
    blocked = install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert blocked.state == "conflict"
    assert "governed_single" in blocked.detail
    assert not (project / ".git" / "hooks" / "commit-msg").exists()

    _write_native_hook(project, workspace, runner)
    (project / "change.txt").write_text("change\n", encoding="utf-8")
    _checked_git(project, "add", "change.txt")
    before = _checked_git(project, "rev-parse", "HEAD").strip()

    rejected = _git(project, "commit", "-m", "docs: 增加提交校验")

    assert rejected.returncode != 0
    assert "governance" in rejected.stderr
    assert _checked_git(project, "rev-parse", "HEAD").strip() == before


def test_install_preserves_user_or_non_worktree_scoped_hook_assets(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path / "user-hook")
    runner = _runner(tmp_path)
    user_hook = project / ".git" / "hooks" / "commit-msg"
    original = b"#!/bin/sh\necho user hook >&2\n"
    user_hook.write_bytes(original)
    user_hook.chmod(0o755)

    conflict = install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert conflict.state == "conflict"
    assert user_hook.read_bytes() == original

    owned_workspace, owned_project = _managed_project(tmp_path / "changed-owned-hook")
    owned_hook = _install(tmp_path, owned_workspace, owned_project)
    changed = owned_hook.read_bytes() + b"# user changed this file\n"
    owned_hook.write_bytes(changed)
    modified = install_commit_msg_hook(
        worktree=str(owned_project),
        workspace_root=str(owned_workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert modified.state == "conflict"
    assert owned_hook.read_bytes() == changed

    configured_workspace, configured_project = _managed_project(tmp_path / "configured-hooks")
    configured_directory = configured_project / ".githooks"
    configured_directory.mkdir()
    _checked_git(configured_project, "config", "core.hooksPath", ".githooks")
    configured_before = _git(configured_project, "config", "--get-all", "core.hooksPath")
    configured = install_commit_msg_hook(
        worktree=str(configured_project),
        workspace_root=str(configured_workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert configured.state == "conflict"
    assert not (configured_directory / "commit-msg").exists()
    configured_after = _git(configured_project, "config", "--get-all", "core.hooksPath")
    assert (configured_after.returncode, configured_after.stdout, configured_after.stderr) == (
        configured_before.returncode,
        configured_before.stdout,
        configured_before.stderr,
    )

    external_workspace, external_project = _managed_project(tmp_path / "external-hooks")
    external_directory = tmp_path / "outside-worktree-hooks"
    external_directory.mkdir()
    _checked_git(external_project, "config", "extensions.worktreeConfig", "true")
    _checked_git(external_project, "config", "--worktree", "core.hooksPath", str(external_directory))
    external = install_commit_msg_hook(
        worktree=str(external_project),
        workspace_root=str(external_workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert external.state == "conflict"
    assert not (external_directory / "commit-msg").exists()


def test_install_accepts_an_effective_worktree_local_hooks_path(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path)
    runner = _runner(tmp_path)
    _checked_git(project, "config", "extensions.worktreeConfig", "true")
    _checked_git(project, "config", "--worktree", "core.hooksPath", ".githooks")
    configured_before = _git(project, "config", "--show-origin", "--show-scope", "--get", "core.hooksPath")

    installed = install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert installed.state == "managed", installed
    assert installed.hook_path == str(project / ".githooks" / "commit-msg")
    assert (project / ".githooks" / "commit-msg").is_file()
    configured_after = _git(project, "config", "--show-origin", "--show-scope", "--get", "core.hooksPath")
    assert (configured_after.returncode, configured_after.stdout, configured_after.stderr) == (
        configured_before.returncode,
        configured_before.stdout,
        configured_before.stderr,
    )

    (project / "worktree-local-change.txt").write_text("change\n", encoding="utf-8")
    _checked_git(project, "add", "worktree-local-change.txt")
    rejected = _git(project, "commit", "-m", "docs: invalid")

    assert rejected.returncode != 0
    assert "description_cjk_missing" in rejected.stderr


def test_bootstrap_uses_one_worktree_local_path_and_its_wrapper_disappears_with_the_worktree(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path)
    runner = _runner(tmp_path)
    linked = tmp_path / "linked"
    _checked_git(main, "branch", "linked")
    _checked_git(main, "worktree", "add", "-q", str(linked), "linked")

    unavailable = bootstrap_commit_msg_hook(
        worktree=str(linked),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert unavailable.state == "unavailable"
    assert "extensions.worktreeConfig" in unavailable.detail
    assert _git(linked, "config", "--get", "core.hooksPath").returncode == 1

    _checked_git(main, "config", "extensions.worktreeConfig", "yes")
    installed = bootstrap_commit_msg_hook(
        worktree=str(linked),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    hook = linked / ".githooks-v4" / "commit-msg"
    assert installed.state == "managed", installed
    assert installed.hook_path == str(hook)
    assert hook.is_file()
    assert _git(linked, "config", "--show-origin", "--show-scope", "--get", "core.hooksPath").stdout.endswith(
        "\t.githooks-v4\n"
    )
    assert not (main / ".git" / "hooks" / "commit-msg").exists()

    (linked / "worktree-bootstrap-change.txt").write_text("change\n", encoding="utf-8")
    _checked_git(linked, "add", "worktree-bootstrap-change.txt")
    before = _checked_git(linked, "rev-parse", "HEAD").strip()
    rejected = _git(linked, "commit", "-m", "docs: invalid")

    assert rejected.returncode != 0
    assert "description_cjk_missing" in rejected.stderr
    assert _checked_git(linked, "rev-parse", "HEAD").strip() == before

    removed = uninstall_commit_msg_hook(
        worktree=str(linked),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert removed.state == "absent", removed
    assert "remains unchanged" in removed.detail
    assert not hook.exists()
    assert _git(linked, "config", "--get", "core.hooksPath").stdout == ".githooks-v4\n"

    reinstalled = bootstrap_commit_msg_hook(
        worktree=str(linked),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )
    assert reinstalled.state == "managed", reinstalled
    assert hook.is_file()

    _checked_git(main, "worktree", "remove", "--force", str(linked))

    assert not hook.exists()


def test_bootstrap_does_not_shadow_an_existing_shared_hook(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path)
    runner = _runner(tmp_path)
    _checked_git(main, "config", "extensions.worktreeConfig", "true")
    linked = tmp_path / "linked"
    _checked_git(main, "branch", "linked")
    _checked_git(main, "worktree", "add", "-q", str(linked), "linked")
    shared_hook = main / ".git" / "hooks" / "pre-commit"
    shared_contents = b"#!/bin/sh\necho user hook >&2\n"
    shared_hook.write_bytes(shared_contents)
    shared_hook.chmod(0o755)

    blocked = bootstrap_commit_msg_hook(
        worktree=str(linked),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert blocked.state == "conflict"
    assert "shadowed" in blocked.detail
    assert shared_hook.read_bytes() == shared_contents
    assert _git(linked, "config", "--get", "core.hooksPath").returncode == 1
    assert not (linked / ".githooks-v4").exists()


def test_bootstrap_validates_the_runner_before_changing_worktree_configuration(tmp_path: Path) -> None:
    workspace, main = _managed_project(tmp_path)
    _checked_git(main, "config", "extensions.worktreeConfig", "yes")
    linked = tmp_path / "linked"
    _checked_git(main, "branch", "linked")
    _checked_git(main, "worktree", "add", "-q", str(linked), "linked")

    unavailable = bootstrap_commit_msg_hook(
        worktree=str(linked),
        workspace_root=str(workspace),
        commit_msg_runner=str(tmp_path / "missing-runner"),
        human_gate_confirmed=True,
    )

    assert unavailable.state == "unavailable"
    assert _git(linked, "config", "--get", "core.hooksPath").returncode == 1
    assert not (linked / ".githooks-v4").exists()


def test_bootstrap_rolls_back_configuration_and_wrapper_after_post_activation_failure(
    tmp_path: Path, monkeypatch
) -> None:
    workspace, main = _managed_project(tmp_path)
    runner = _runner(tmp_path)
    _checked_git(main, "config", "extensions.worktreeConfig", "on")
    linked = tmp_path / "linked"
    _checked_git(main, "branch", "linked")
    _checked_git(main, "worktree", "add", "-q", str(linked), "linked")
    hook = linked / ".githooks-v4" / "commit-msg"

    def _post_activation_failure(**_kwargs) -> CommitMsgHookStatus:
        assert _git(linked, "config", "--get", "core.hooksPath").stdout == ".githooks-v4\n"
        assert hook.is_file()
        return CommitMsgHookStatus(
            "conflict", "simulated post-activation failure", str(linked), str(hook.parent), str(hook)
        )

    monkeypatch.setattr("ldvh.git_hooks.commit_msg.install_commit_msg_hook", _post_activation_failure)

    unavailable = bootstrap_commit_msg_hook(
        worktree=str(linked),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert unavailable.state == "unavailable"
    assert "simulated post-activation failure" in unavailable.detail
    assert _git(linked, "config", "--get", "core.hooksPath").returncode == 1
    assert not hook.exists()


def test_managed_hook_binding_prevents_cross_environment_replacement_or_removal(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path)
    runner_a = _runner(tmp_path / "environment-a")
    runner_b = _runner(tmp_path / "environment-b")
    workspace_b = tmp_path / "environment-b-workspace"
    workspace_b.mkdir()
    (workspace_b / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            (
                "product_name: Native Hook Tests",
                "product_description: Isolated native Git lifecycle tests.",
                "projects:",
                "  - id: sample",
                f"    path: {project}",
                "    name: Sample",
                "    description: Temporary governed project.",
                "",
            )
        ),
        encoding="utf-8",
    )
    installed = install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner_a),
        human_gate_confirmed=True,
    )

    assert installed.state == "managed", installed
    assert installed.hook_path is not None
    hook = Path(installed.hook_path)
    contents = hook.read_bytes()
    replacement = install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner_b),
        human_gate_confirmed=True,
    )
    removal = uninstall_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner_b),
        human_gate_confirmed=True,
    )
    workspace_replacement = install_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace_b),
        commit_msg_runner=str(runner_a),
        human_gate_confirmed=True,
    )
    workspace_removal = uninstall_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace_b),
        commit_msg_runner=str(runner_a),
        human_gate_confirmed=True,
    )

    assert replacement.state == "conflict"
    assert removal.state == "conflict"
    assert workspace_replacement.state == "conflict"
    assert workspace_removal.state == "conflict"
    assert hook.read_bytes() == contents
    removed = uninstall_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner_a),
        human_gate_confirmed=True,
    )
    assert removed.state == "absent", removed


def test_uninstall_requires_human_gate_and_only_removes_owned_hook(tmp_path: Path) -> None:
    workspace, project = _managed_project(tmp_path)
    hook = _install(tmp_path, workspace, project)
    runner = _runner(tmp_path)
    pre_commit = project / ".git" / "hooks" / "pre-commit"
    pre_commit_contents = b"#!/bin/sh\nexit 0\n"
    pre_commit.write_bytes(pre_commit_contents)
    pre_commit.chmod(0o755)
    hooks_config_before = _git(project, "config", "--get-all", "core.hooksPath")

    blocked = uninstall_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=False,
    )

    assert blocked.state == "unavailable"
    assert hook.is_file()

    removed = uninstall_commit_msg_hook(
        worktree=str(project),
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )

    assert removed.state == "absent", removed
    assert not hook.exists()
    assert pre_commit.read_bytes() == pre_commit_contents
    hooks_config_after = _git(project, "config", "--get-all", "core.hooksPath")
    assert (hooks_config_after.returncode, hooks_config_after.stdout, hooks_config_after.stderr) == (
        hooks_config_before.returncode,
        hooks_config_before.stdout,
        hooks_config_before.stderr,
    )
    assert inspect_commit_msg_hook(worktree=str(project)).state == "absent"
