"""Bind source-declared Helper operations to explicit Code implementations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

from ldvh.helper.operation_sources import OperationDeclarationCandidate, OperationSourceInspection
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import diagnostic
from ldvh.specs.repository import RepositoryInspection

Availability = Literal[
    "unavailable_for_request",
    "partially_available",
    "available_for_request",
]
Outcome = Literal["ok", "no_change", "partial", "rejected", "unavailable", "invalid_request", "error"]


class OperationRequestError(ValueError):
    """A source-defined operation rejected its domain request without executing it."""

    def __init__(
        self,
        problems: tuple[str, ...],
        *,
        sources: tuple[dict[str, Any], ...] = (),
    ) -> None:
        super().__init__("operation request does not satisfy its domain contract")
        self.problems = problems
        self.sources = sources


@dataclass(frozen=True, slots=True)
class OperationExecutionContext:
    """Process observations captured once at the Helper service boundary."""

    cwd: Path
    event_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())


@dataclass(frozen=True, slots=True)
class AvailabilityEvaluation:
    availability: Availability
    available_scope: tuple[object, ...] = ()
    unavailable_scope: tuple[object, ...] = ()
    gaps: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class OperationExecution:
    outcome: Outcome
    summary: str
    result: dict[str, Any] | None = None
    requested_scope: tuple[object, ...] = ()
    completed_scope: tuple[object, ...] = ()
    not_completed_scope: tuple[object, ...] = ()
    governance_resolution: dict[str, Any] | None = None
    sources: tuple[dict[str, Any], ...] = ()
    disclosure: dict[str, Any] | None = None
    gaps: tuple[dict[str, Any], ...] = ()
    changes: tuple[dict[str, Any], ...] = ()
    verification: tuple[dict[str, Any], ...] = ()
    diagnostics: tuple[dict[str, Any], ...] = ()
    follow_up: dict[str, Any] | None = None


AvailabilityHandler = Callable[[CommonRequest, RepositoryInspection, OperationExecutionContext], AvailabilityEvaluation]
CallHandler = Callable[[CommonRequest, RepositoryInspection, OperationExecutionContext], OperationExecution]
_INPUT_EXAMPLE_FIELDS = frozenset({"summary", "arguments_fragment", "source_refs", "composition_note"})


@dataclass(frozen=True, slots=True)
class OperationImplementation:
    """Code-side implementation metadata; it does not grant a public identity."""

    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...]
    evidence: tuple[dict[str, Any], ...]
    check_availability: AvailabilityHandler
    call: CallHandler
    input_examples: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if not self.evidence:
            raise ValueError("an operation implementation requires reviewable evidence")
        fields = (*self.required_inputs, *self.optional_inputs)
        if any(not isinstance(field, str) or not field for field in fields):
            raise ValueError("operation input names must be non-empty strings")
        if len(set(fields)) != len(fields):
            raise ValueError("operation input names must be unique")
        for example in self.input_examples:
            if not isinstance(example, Mapping) or set(example) != _INPUT_EXAMPLE_FIELDS:
                raise ValueError("operation input examples must use the closed common field set")
            if any(
                not isinstance(example[field], str) or not example[field].strip()
                for field in ("summary", "composition_note")
            ):
                raise ValueError("operation input example text fields must be non-empty strings")
            if not isinstance(example["arguments_fragment"], Mapping):
                raise ValueError("operation input example arguments_fragment must be an object")
            source_refs = example["source_refs"]
            if (
                not isinstance(source_refs, tuple)
                or not source_refs
                or any(not isinstance(source, Mapping) for source in source_refs)
            ):
                raise ValueError("operation input examples require source references")


@dataclass(frozen=True, slots=True)
class BoundOperation:
    declaration: OperationDeclarationCandidate
    implementation: OperationImplementation | None


@dataclass(frozen=True, slots=True)
class OperationRuntime:
    """The intersection of current source declarations and implementation bindings."""

    operations: tuple[BoundOperation, ...]
    undeclared_implementation_keys: tuple[str, ...]

    def by_key(self) -> Mapping[str, BoundOperation]:
        return MappingProxyType({operation.declaration.operation_key: operation for operation in self.operations})


def bind_operation_implementations(
    inspection: OperationSourceInspection,
    implementations: Mapping[str, OperationImplementation],
) -> OperationRuntime:
    """Bind implementations without allowing the mapping to create public operations."""

    declarations = {declaration.operation_key: declaration for declaration in inspection.candidate_declarations}
    operations = tuple(
        BoundOperation(declaration, implementations.get(operation_key))
        for operation_key, declaration in sorted(declarations.items())
    )
    undeclared = tuple(sorted(set(implementations) - set(declarations)))
    return OperationRuntime(operations=operations, undeclared_implementation_keys=undeclared)


def implementation_contract_diagnostics(runtime: OperationRuntime) -> list[dict[str, Any]]:
    """Report bindings that have Code but no source-defined public identity."""

    return [
        diagnostic(
            "发现没有当前来源声明的内部操作实现；该实现未进入公开操作清单",
            implementation_key=operation_key,
        )
        for operation_key in runtime.undeclared_implementation_keys
    ]


def implementation_error_execution(
    operation: BoundOperation,
    error: Exception,
) -> OperationExecution:
    """Convert an unexpected implementation exception to a bounded service result."""

    operation_key = operation.declaration.operation_key
    sources = () if operation.implementation is None else operation.implementation.evidence
    return OperationExecution(
        outcome="error",
        summary="公开操作实现发生异常，无法形成可信结果",
        requested_scope=(operation_key,),
        not_completed_scope=(operation_key,),
        sources=sources,
        diagnostics=(
            diagnostic(
                "公开操作实现异常",
                operation_key=operation_key,
                exception_type=type(error).__name__,
            ),
        ),
    )
