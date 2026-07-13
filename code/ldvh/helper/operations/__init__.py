"""Explicit Code implementations for source-declared Helper operations."""

from __future__ import annotations

from types import MappingProxyType

from ldvh.helper.operation_runtime import OperationImplementation
from ldvh.helper.operations.fact_object_operation import FACT_OBJECT_IMPLEMENTATION
from ldvh.helper.operations.fact_object_operation import OPERATION_KEY as FACT_OBJECT_OPERATION_KEY
from ldvh.helper.operations.governance_scope_operation import (
    GOVERNANCE_SCOPE_IMPLEMENTATION,
)
from ldvh.helper.operations.governance_scope_operation import (
    OPERATION_KEY as GOVERNANCE_SCOPE_OPERATION_KEY,
)
from ldvh.helper.operations.specification_candidate_operation import (
    OPERATION_KEY as SPECIFICATION_CANDIDATE_OPERATION_KEY,
)
from ldvh.helper.operations.specification_candidate_operation import (
    SPECIFICATION_CANDIDATE_IMPLEMENTATION,
)
from ldvh.helper.operations.specification_content_operation import (
    OPERATION_KEY as SPECIFICATION_CONTENT_OPERATION_KEY,
)
from ldvh.helper.operations.specification_content_operation import (
    SPECIFICATION_CONTENT_IMPLEMENTATION,
)

IMPLEMENTATIONS = MappingProxyType[str, OperationImplementation](
    {
        FACT_OBJECT_OPERATION_KEY: FACT_OBJECT_IMPLEMENTATION,
        GOVERNANCE_SCOPE_OPERATION_KEY: GOVERNANCE_SCOPE_IMPLEMENTATION,
        SPECIFICATION_CANDIDATE_OPERATION_KEY: SPECIFICATION_CANDIDATE_IMPLEMENTATION,
        SPECIFICATION_CONTENT_OPERATION_KEY: SPECIFICATION_CONTENT_IMPLEMENTATION,
    }
)

__all__ = ["IMPLEMENTATIONS"]
