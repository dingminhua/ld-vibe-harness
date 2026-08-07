from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.diagnostics import SourceLocation
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    bind_operation_implementations,
    implementation_contract_diagnostics,
)
from ldvh.helper.operation_sources import OperationDeclarationCandidate, OperationSourceInspection
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection


def _declaration(operation_key: str = "read-source") -> OperationDeclarationCandidate:
    return OperationDeclarationCandidate(
        operation_key=operation_key,
        summary="Read one source",
        effect="read",
        arguments_contract="source-one::输入字段",
        result_contract="source-one::结果字段",
        source_key="source-one",
        source=SourceLocation("specs/source-one.md", 20, "Helper 公开操作"),
    )


def _inspection(*declarations: OperationDeclarationCandidate) -> OperationSourceInspection:
    return OperationSourceInspection(declarations, (), (), (), ())


def _implementation() -> OperationImplementation:
    return OperationImplementation(
        required_inputs=("arguments.source_key",),
        optional_inputs=("requested_disclosure",),
        evidence=(source_reference("implementation", "ldvh.test.fake"),),
        check_availability=lambda _request, _repository, _context: AvailabilityEvaluation("available_for_request"),
        call=lambda _request, _repository, _context: OperationExecution("ok", "fake completed"),
    )


def test_source_without_implementation_remains_public_but_unbound() -> None:
    runtime = bind_operation_implementations(_inspection(_declaration()), {})

    assert tuple(runtime.by_key()) == ("read-source",)
    assert runtime.by_key()["read-source"].implementation is None
    assert runtime.undeclared_implementation_keys == ()


def test_implementation_without_source_does_not_gain_public_identity() -> None:
    runtime = bind_operation_implementations(_inspection(), {"internal-only": _implementation()})

    assert runtime.operations == ()
    assert runtime.undeclared_implementation_keys == ("internal-only",)
    diagnostics = implementation_contract_diagnostics(runtime)
    assert diagnostics[0]["details"]["implementation_key"] == "internal-only"
    assert "未进入公开操作清单" in diagnostics[0]["summary"]


def test_source_and_implementation_are_bound_by_exact_key() -> None:
    implementation = _implementation()

    runtime = bind_operation_implementations(_inspection(_declaration()), {"read-source": implementation})

    assert runtime.by_key()["read-source"].implementation is implementation


@pytest.mark.parametrize(
    ("required", "optional"),
    [(("same",), ("same",)), (("",), ()), (("one", "one"), ())],
)
def test_implementation_rejects_invalid_input_metadata(
    required: tuple[str, ...],
    optional: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError):
        OperationImplementation(
            required_inputs=required,
            optional_inputs=optional,
            evidence=(source_reference("implementation", "ldvh.test.fake"),),
            check_availability=lambda _request, _repository, _context: AvailabilityEvaluation("available_for_request"),
            call=lambda _request, _repository, _context: OperationExecution("ok", "fake completed"),
        )


def test_fake_handlers_receive_validated_request_and_repository(tmp_path: Path) -> None:
    observed: list[tuple[CommonRequest, RepositoryInspection, OperationExecutionContext]] = []

    def call(
        request: CommonRequest,
        repository: RepositoryInspection,
        context: OperationExecutionContext,
    ) -> OperationExecution:
        observed.append((request, repository, context))
        return OperationExecution("ok", "fake completed")

    implementation = OperationImplementation(
        required_inputs=(),
        optional_inputs=(),
        evidence=(source_reference("implementation", "ldvh.test.fake"),),
        check_availability=lambda _request, _repository, _context: AvailabilityEvaluation("available_for_request"),
        call=call,
    )
    repository = RepositoryInspection(tmp_path, (), (), (), (), (), (), (), (), True)
    request = CommonRequest(None, (), {}, None, {}, ())

    context = OperationExecutionContext(cwd=tmp_path)
    implementation.call(request, repository, context)

    assert observed == [(request, repository, context)]
