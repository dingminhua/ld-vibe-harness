from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import HELPER_EXECUTABLE

from ldvh.hooks import context_recovery

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
WORKCASE_FIXTURE = REPOSITORY_ROOT / "code/tests/fixtures/context_recovery/workcase-0007.yaml"


def _git_repository(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True, capture_output=True)
    return path


def _workspace(tmp_path: Path, *, project_count: int = 1, with_workcase: bool = False) -> tuple[Path, list[Path]]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    projects = [_git_repository(tmp_path / f"project-{index}") for index in range(project_count)]
    if with_workcase and projects:
        target = projects[0] / "ldvh-base/workcases/workcase-0007.yaml"
        target.parent.mkdir(parents=True)
        shutil.copyfile(WORKCASE_FIXTURE, target)
    lines = [
        "product_name: Test",
        "product_description: Test workspace.",
        "projects:" if projects else "projects: []",
    ]
    for index, project in enumerate(projects):
        lines.extend(
            [
                f"  - id: sample-{index}",
                f"    path: {project}",
                f"    name: Sample {index}",
                "    description: Test project.",
            ]
        )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text("\n".join([*lines, ""]), encoding="utf-8")
    return workspace, projects


def _raw_helper(tmp_path: Path, name: str, body: str) -> Path:
    script = tmp_path / f"{name}.py"
    script.write_text(body, encoding="utf-8")
    if sys.platform == "win32":
        helper = tmp_path / f"{name}.cmd"
        helper.write_text(f'@"{sys.executable}" -X utf8 "{script}" %*\r\n', encoding="utf-8")
    else:
        helper = tmp_path / name
        helper.write_text(f"#!{sys.executable}\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
        helper.chmod(0o755)
    return helper


def _recover(
    helper: Path,
    workspace: Path,
    locator: Path,
    helper_cwd: Path,
    *,
    current_ref: dict[str, str] | None = None,
) -> dict[str, Any]:
    return context_recovery.recover_context(
        helper_executable=str(helper),
        workspace_root=str(workspace),
        work_object_locator=str(locator),
        helper_cwd=str(helper_cwd),
        current_workcase_ref=current_ref,
    )


def _recorded_recovery(
    monkeypatch: pytest.MonkeyPatch,
    helper: Path,
    workspace: Path,
    locator: Path,
    helper_cwd: Path,
    *,
    current_ref: dict[str, str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actual_run = subprocess.run
    calls: list[dict[str, Any]] = []

    def record(*arguments: Any, **keywords: Any) -> subprocess.CompletedProcess[str]:
        calls.append(
            {
                "argv": list(arguments[0]),
                "cwd": str(keywords["cwd"]),
                "input": json.loads(keywords["input"]),
                "timeout": keywords["timeout"],
            }
        )
        return actual_run(*arguments, **keywords)

    monkeypatch.setattr(context_recovery.subprocess, "run", record)
    projection = _recover(helper, workspace, locator, helper_cwd, current_ref=current_ref)
    return projection, calls


def test_governed_recovery_returns_bounded_projection_and_expands_sole_candidate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, projects = _workspace(tmp_path, with_workcase=True)
    locator = projects[0] / "task.md"
    locator.write_text("task\n", encoding="utf-8")
    helper_cwd = tmp_path / "environment-cwd"
    helper_cwd.mkdir()

    projection, calls = _recorded_recovery(monkeypatch, HELPER_EXECUTABLE, workspace, locator, helper_cwd)

    assert projection["contract"] == "ldvh-context-recovery/1"
    assert projection["project_binding"]["status"] == "bound"
    assert projection["project_binding"]["reason"] == "governed_single"
    assert projection["project_binding"]["project"]["git_worktree_root"] == str(projects[0])
    assert projection["workcase_binding"]["status"] == "unresolved"
    assert projection["workcase_binding"]["reason"] == "sole_mechanical_candidate"
    assert projection["workcase"]["fact_ref"]["object_id"] == "workcase-0007"
    assert [item["item_id"] for item in projection["active_items"]] == ["item-02"]
    assert [call["argv"][1:] for call in calls] == [
        ["call", "resolve-governance-scope"],
        ["call", "find-fact-object-candidates"],
        ["call", "read-fact-objects"],
    ]
    assert all(call["cwd"] == str(helper_cwd) for call in calls)
    assert calls[1]["input"]["arguments"]["page_size"] == 100
    assert calls[1]["input"]["work_object_locators"] == [str(projects[0])]
    assert "current_workcase_ref" not in calls[1]["input"]["arguments"]
    assert projection["delivery_coverage"]["status"] == "complete"


def test_exact_current_workcase_ref_is_the_only_current_binding_input(tmp_path: Path) -> None:
    workspace, projects = _workspace(tmp_path, with_workcase=True)
    current_ref = {
        "governed_project_id": "sample-0",
        "fact_type_key": "workcase",
        "object_id": "workcase-0007",
    }

    projection = _recover(HELPER_EXECUTABLE, workspace, projects[0], projects[0], current_ref=current_ref)

    assert projection["workcase_binding"] == {
        "status": "bound",
        "reason": "exact_current_workcase_ref",
        "selected_ref": current_ref,
        "helper_coverage": {"status": "complete", "pages_read": 1, "total_matching": 1},
        "candidates": projection["workcase_binding"]["candidates"],
    }
    assert projection["workcase"]["fact_ref"] == current_ref


def test_workspace_root_remains_non_governed_but_can_bind_one_registered_candidate(tmp_path: Path) -> None:
    workspace, projects = _workspace(tmp_path, with_workcase=True)

    projection = _recover(HELPER_EXECUTABLE, workspace, workspace, workspace)

    assert projection["project_binding"]["status"] == "bound"
    assert projection["project_binding"]["reason"] == "sole_registered_project_candidate"
    assert projection["project_binding"]["project"]["git_worktree_root"] == str(projects[0])
    governance = projection["operations"][0]
    assert governance["operation_key"] == "resolve-governance-scope"
    assert projection["delivery_coverage"]["status"] == "incomplete"
    assert projection["delivery_coverage"]["project_candidates"]["omitted"] == 0
    assert projection["delivery_coverage"]["required_f1_cards"]["omitted"] == 1
    assert projection["workcase_binding"]["status"] == "unresolved"
    assert projection["workcase_binding"]["reason"] == "delivery_incomplete"
    assert context_recovery._projection_size(projection) <= context_recovery.WORKSPACE_PROJECTION_BUDGET_BYTES


def test_delivery_budget_hard_fallback_never_returns_an_oversized_projection() -> None:
    long_summary = "diagnostic-" + ("x" * 3_000)
    source_locator = "/rules/" + ("s" * 700)
    projection: dict[str, Any] = {
        "contract": "ldvh-context-recovery/1",
        "project_binding": {
            "status": "unresolved",
            "reason": "registered_project_choice_unresolved",
            "project": None,
            "candidates": [],
        },
        "workcase_binding": {
            "status": "unresolved",
            "reason": "project_unresolved",
            "selected_ref": None,
            "candidates": [],
        },
        "delivery_coverage": {"status": "complete"},
        "operations": [
            {
                "operation_key": "resolve-governance-scope",
                "outcome": "partial",
                "completed_scope_count": 1,
                "not_completed_scope_count": 1,
                "source_locators": [source_locator],
                "gap_summaries": [long_summary],
                "diagnostic_summaries": [long_summary],
            }
        ],
        "adr_cards": [],
        "active_items": [],
        "expand": [
            {
                "operation_key": "resolve-governance-scope",
                "request": {
                    "work_object_locators": ["/workspace/" + ("w" * 500)],
                    "arguments": {"workspace_root": "/workspace"},
                    "response_profile": "compact",
                },
            }
        ],
        "diagnostics": [{"code": "helper_partial", "summary": long_summary}],
    }

    context_recovery._fit_delivery_budget(projection, 4_000)

    assert context_recovery._projection_size(projection) <= 4_000
    assert projection["delivery_coverage"]["status"] == "incomplete"
    assert projection["operations"][0]["operation_key"] == "resolve-governance-scope"
    assert projection["operations"][0]["outcome"] == "partial"
    assert projection["operations"][0]["completed_scope_count"] == 1
    assert projection["operations"][0]["not_completed_scope_count"] == 1
    assert projection["operations"][0]["source_locators"] == [source_locator]
    assert projection["diagnostics"] == [
        {
            "code": "delivery_budget_exceeded",
            "summary": "Recovery projection used its hard byte-budget fallback",
        }
    ]


@pytest.mark.parametrize("project_count", [0, 2])
def test_workspace_root_with_zero_or_multiple_candidates_stays_unresolved(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    project_count: int,
) -> None:
    workspace, _ = _workspace(tmp_path, project_count=project_count)

    projection, calls = _recorded_recovery(monkeypatch, HELPER_EXECUTABLE, workspace, workspace, workspace)

    assert projection["project_binding"]["status"] == "unresolved"
    assert len(projection["project_binding"]["candidates"]) == project_count
    assert [call["argv"][1:] for call in calls] == [["call", "resolve-governance-scope"]]


def _response(operation: str, *, outcome: str = "ok", result: Any = None) -> dict[str, Any]:
    return {
        "contract": "ldvh-helper-cli/2",
        "request_kind": "call",
        "operation_key": operation,
        "outcome": outcome,
        "result": result,
        "scope": {"completed": [], "not_completed": []},
        "sources": [],
        "gaps": [],
        "diagnostics": [],
    }


def _governance_response(project: Path) -> dict[str, Any]:
    project_value = {
        "governed_project_id": "sample-0",
        "registered_project_path": str(project),
        "git_worktree_root": str(project),
        "git_common_dir": str(project / ".git"),
        "source_refs": [{"kind": "test", "locator": str(project)}],
    }
    return _response(
        "resolve-governance-scope",
        result={
            "config_status": "valid",
            "scope_status": "governed_single",
            "registered_project_candidates": [project_value],
            "object_resolutions": [{"status": "governed", **project_value}],
        },
    )


def _card(object_id: str) -> dict[str, Any]:
    return {
        "fact_ref": {
            "governed_project_id": "sample-0",
            "fact_type_key": "workcase",
            "object_id": object_id,
        },
        "card_layer": "F1",
        "fields": {"object_id": object_id, "status": "open", "summary": object_id},
        "source_refs": [{"kind": "test", "locator": object_id}],
    }


def _f1_response(project: Path, *, offset: int, next_cursor: str | None, object_id: str) -> dict[str, Any]:
    return _response(
        "find-fact-object-candidates",
        result={
            "recovery_manifest": {
                "governed_project_id": "sample-0",
                "git_worktree_root": str(project),
                "git_common_dir": str(project / ".git"),
                "schema_fingerprint": "schema",
                "object_set_fingerprint": "objects",
                "current_workcase_ref": None,
            },
            "cards": [_card(object_id)],
            "coverage": {
                "status": "complete",
                "total_matching": 2,
                "returned": 1,
                "offset": offset,
                "next_cursor": next_cursor,
                "object_set_fingerprint": "objects",
            },
        },
    )


def test_recovery_consumes_every_f1_cursor_and_preserves_query_continuity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, projects = _workspace(tmp_path)
    responses = iter(
        [
            _governance_response(projects[0]),
            _f1_response(projects[0], offset=0, next_cursor="next", object_id="workcase-0001"),
            _f1_response(projects[0], offset=1, next_cursor=None, object_id="workcase-0002"),
        ]
    )
    requests: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        requests.append(kwargs["request"])
        return 0, next(responses)

    monkeypatch.setattr(context_recovery, "_run_helper", fake_run)

    projection = _recover(HELPER_EXECUTABLE, workspace, projects[0], projects[0])

    assert projection["workcase_binding"]["helper_coverage"] == {
        "status": "complete",
        "pages_read": 2,
        "total_matching": 2,
    }
    assert [card["fact_ref"]["object_id"] for card in projection["workcase_binding"]["candidates"]] == [
        "workcase-0001",
        "workcase-0002",
    ]
    assert requests[1]["arguments"].get("cursor") is None
    assert requests[2]["arguments"]["cursor"] == "next"


def test_page_budget_keeps_coverage_and_binding_unresolved(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, projects = _workspace(tmp_path)
    responses = iter(
        [
            _governance_response(projects[0]),
            _f1_response(projects[0], offset=0, next_cursor="next", object_id="workcase-0001"),
        ]
    )
    monkeypatch.setattr(context_recovery, "MAX_F1_PAGES", 1)
    monkeypatch.setattr(context_recovery, "_run_helper", lambda *args, **kwargs: (0, next(responses)))

    projection = _recover(HELPER_EXECUTABLE, workspace, projects[0], projects[0])

    assert projection["project_binding"]["status"] == "bound"
    assert projection["workcase_binding"]["status"] == "unresolved"
    assert projection["workcase_binding"]["helper_coverage"]["status"] == "incomplete"
    assert projection["diagnostics"] == [
        {"code": "resource_budget_exceeded", "summary": "F1 page budget exceeded"}
    ]


def test_partial_f1_keeps_helper_and_delivery_coverage_incomplete(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, projects = _workspace(tmp_path)
    responses = iter(
        [
            _governance_response(projects[0]),
            _response("find-fact-object-candidates", outcome="partial"),
        ]
    )
    monkeypatch.setattr(context_recovery, "_run_helper", lambda *args, **kwargs: (0, next(responses)))

    projection = _recover(HELPER_EXECUTABLE, workspace, projects[0], projects[0])

    assert projection["project_binding"]["status"] == "bound"
    assert projection["workcase_binding"]["helper_coverage"]["status"] == "incomplete"
    assert projection["workcase_binding"]["status"] == "unresolved"
    assert projection["delivery_coverage"]["status"] == "incomplete"
    assert projection["operations"][-1]["outcome"] == "partial"


def test_governance_timeout_returns_an_unresolved_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, projects = _workspace(tmp_path)

    def timeout(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        raise subprocess.TimeoutExpired("ldvh", kwargs["timeout"])

    monkeypatch.setattr(context_recovery, "_run_helper", timeout)

    projection = _recover(HELPER_EXECUTABLE, workspace, projects[0], projects[0])

    assert projection["project_binding"]["status"] == "unresolved"
    assert projection["delivery_coverage"]["status"] == "incomplete"
    assert projection["diagnostics"][0]["code"] == "resource_budget_exceeded"


@pytest.mark.parametrize(
    ("name", "body", "error_type", "expected"),
    [
        ("invalid-utf8-helper", "import sys\nsys.stdout.buffer.write(b'\\xff')\n", UnicodeDecodeError, "decode"),
        (
            "stderr-only-helper",
            'import sys\nsys.stderr.write(\'{"outcome": "ok"}\\n\')\n',
            context_recovery.ContextRecoveryError,
            "did not return one JSON response",
        ),
        (
            "invalid-contract",
            "\n".join(
                [
                    "import json",
                    "import sys",
                    "print(json.dumps({",
                    "    'contract': 'ldvh-helper-cli/future',",
                    "    'request_kind': sys.argv[1],",
                    "    'operation_key': sys.argv[2],",
                    "    'outcome': 'ok',",
                    "}))",
                ]
            )
            + "\n",
            context_recovery.ContextRecoveryError,
            "response contract",
        ),
    ],
)
def test_recovery_rejects_unfaithful_helper_transport_or_identity(
    tmp_path: Path,
    name: str,
    body: str,
    error_type: type[Exception],
    expected: str,
) -> None:
    workspace, projects = _workspace(tmp_path)

    with pytest.raises(error_type) as captured:
        _recover(_raw_helper(tmp_path, name, body), workspace, projects[0], projects[0])

    assert expected in str(captured.value)


def test_runner_executes_packaged_core_and_returns_one_projection(tmp_path: Path) -> None:
    workspace, projects = _workspace(tmp_path, with_workcase=True)
    decoy = tmp_path / "decoy-cwd"
    decoy.mkdir()
    environment = os.environ.copy()
    source_path = str(REPOSITORY_ROOT / "code")
    environment["PYTHONPATH"] = source_path + os.pathsep + environment.get("PYTHONPATH", "")

    completed = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "ldvh.hooks.context_recovery",
            "--helper-executable",
            str(HELPER_EXECUTABLE),
            "--workspace-root",
            str(workspace),
            "--work-object-locator",
            str(projects[0]),
            "--helper-cwd",
            str(decoy),
        ],
        cwd=decoy,
        input="",
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        env=environment,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    projection = json.loads(completed.stdout)
    assert projection["contract"] == "ldvh-context-recovery/1"
    assert [item["operation_key"] for item in projection["operations"]] == [
        "resolve-governance-scope",
        "find-fact-object-candidates",
        "read-fact-objects",
    ]
