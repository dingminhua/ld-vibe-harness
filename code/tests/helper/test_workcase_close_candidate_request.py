from __future__ import annotations

from pathlib import Path

from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.workcase_close_candidate_request import (
    parse_workcase_close_candidate_request,
)
from ldvh.helper.requests import CommonRequest


def _request(arguments: dict[str, object], **overrides: object) -> CommonRequest:
    values = {
        "task": None,
        "work_object_locators": (),
        "arguments": arguments,
        "requested_disclosure": None,
        "observed_context": {},
        "authorization_reference": (),
    }
    values.update(overrides)
    return CommonRequest(**values)  # type: ignore[arg-type]


def _ref() -> dict[str, str]:
    return {
        "governed_project_id": "sample",
        "fact_type_key": "workcase",
        "object_id": "workcase-0047",
    }


def test_candidate_request_accepts_only_one_workcase_ref_and_common_location() -> None:
    parsed = parse_workcase_close_candidate_request(
        _request({"fact_ref": _ref(), "workspace_root": "/workspace"}),
        OperationExecutionContext(Path("/project")),
    )

    assert parsed.problems == ()
    assert parsed.request is not None
    assert parsed.request.fact_ref.to_json() == _ref()
    assert parsed.request.workspace_root == Path("/workspace")
    assert parsed.request.base == Path("/project")


def test_candidate_request_rejects_write_and_second_projection_inputs() -> None:
    parsed = parse_workcase_close_candidate_request(
        _request(
            {
                "fact_ref": _ref(),
                "expected_content_fingerprint": "a" * 64,
                "fact_object": {"status": "closed"},
                "route_target_fingerprints": [],
            },
            authorization_reference=({"kind": "human", "locator": "turn:1"},),
        ),
        OperationExecutionContext(Path("/project")),
    )

    assert parsed.request is None
    joined = "\n".join(parsed.problems)
    assert "arguments 包含未知字段" in joined
    assert "authorization_reference 对本只读操作必须为空" in joined


def test_candidate_request_rejects_non_workcase_and_unknown_ref_members() -> None:
    reference = _ref()
    reference["fact_type_key"] = "spark"
    reference["extra"] = "forged"

    parsed = parse_workcase_close_candidate_request(
        _request({"fact_ref": reference}),
        OperationExecutionContext(Path("/project")),
    )

    assert parsed.request is None
    assert any("未知字段" in problem for problem in parsed.problems)
    assert any("必须精确为 workcase" in problem for problem in parsed.problems)
