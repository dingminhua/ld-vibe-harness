from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.helper.operation_runtime import OperationExecutionContext, OperationRequestError
from ldvh.helper.operations.specification_content_operation import SPECIFICATION_CONTENT_IMPLEMENTATION
from ldvh.helper.requests import CommonRequest
from ldvh.specs.repository import inspect_repository


def _request(key: str) -> CommonRequest:
    return CommonRequest(
        task=None,
        work_object_locators=(),
        arguments={"selections": [{"responsibility_key": key, "heading_path": None}]},
        requested_disclosure="L4",
        observed_context={},
        authorization_reference=(),
    )


def test_availability_maps_completed_and_rejected_without_expanding_shared_interface(
    current_specs_repository: Path,
) -> None:
    context = OperationExecutionContext(cwd=current_specs_repository)
    available_repository = inspect_repository(current_specs_repository)
    available = SPECIFICATION_CONTENT_IMPLEMENTATION.check_availability(
        _request("ldvh-root"),
        available_repository,
        context,
    )

    web = current_specs_repository / "specs/08-Web 呈现与交互规范.md"
    web.write_text(
        web.read_text(encoding="utf-8").replace('    - "ldvh-root"', '    - "missing-basis"', 1),
        encoding="utf-8",
    )
    rejected_repository = inspect_repository(current_specs_repository)
    rejected = SPECIFICATION_CONTENT_IMPLEMENTATION.check_availability(
        _request("web-presentation-interaction"),
        rejected_repository,
        context,
    )

    assert available.availability == "available_for_request"
    assert available.available_scope == ({"responsibility_key": "ldvh-root", "heading_path": None},)
    assert available.unavailable_scope == ()
    assert rejected.availability == "unavailable_for_request"
    assert rejected.available_scope == ()
    assert rejected.unavailable_scope == ({"responsibility_key": "web-presentation-interaction", "heading_path": None},)
    assert any("Stop Conditions" in gap["summary"] for gap in rejected.gaps)


def test_availability_preserves_invalid_exact_selection_as_request_error(current_specs_repository: Path) -> None:
    web = current_specs_repository / "specs/08-Web 呈现与交互规范.md"
    web.write_text(
        web.read_text(encoding="utf-8").replace('status: "active"', 'status: "retired"', 1), encoding="utf-8"
    )
    repository = inspect_repository(current_specs_repository)

    with pytest.raises(OperationRequestError) as raised:
        SPECIFICATION_CONTENT_IMPLEMENTATION.check_availability(
            _request("web-presentation-interaction"),
            repository,
            OperationExecutionContext(cwd=current_specs_repository),
        )

    assert "active 载体集合中精确匹配" in raised.value.problems[0]
