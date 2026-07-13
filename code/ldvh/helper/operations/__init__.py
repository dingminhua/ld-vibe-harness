"""Explicit Code implementations for source-declared Helper operations."""

from __future__ import annotations

from types import MappingProxyType

from ldvh.helper.operation_runtime import OperationImplementation
from ldvh.helper.operations.specification_candidate_operation import (
    OPERATION_KEY as SPECIFICATION_CANDIDATE_OPERATION_KEY,
)
from ldvh.helper.operations.specification_candidate_operation import (
    SPECIFICATION_CANDIDATE_IMPLEMENTATION,
)

IMPLEMENTATIONS = MappingProxyType[str, OperationImplementation](
    {
        SPECIFICATION_CANDIDATE_OPERATION_KEY: SPECIFICATION_CANDIDATE_IMPLEMENTATION,
    }
)

__all__ = ["IMPLEMENTATIONS"]
