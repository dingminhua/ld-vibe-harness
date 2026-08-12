"""Explicit Code implementations for source-declared Helper operations."""

from __future__ import annotations

from types import MappingProxyType

from ldvh.helper.operation_runtime import OperationImplementation
from ldvh.helper.operations.action_template_operation import (
    ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION,
    ACTION_TEMPLATE_CONTENT_IMPLEMENTATION,
)
from ldvh.helper.operations.action_template_operation import (
    CANDIDATE_OPERATION_KEY as ACTION_TEMPLATE_CANDIDATE_OPERATION_KEY,
)
from ldvh.helper.operations.action_template_operation import (
    CONTENT_OPERATION_KEY as ACTION_TEMPLATE_CONTENT_OPERATION_KEY,
)
from ldvh.helper.operations.check_current_governed_sources_operation import (
    CHECK_CURRENT_GOVERNED_SOURCES_IMPLEMENTATION,
)
from ldvh.helper.operations.check_current_governed_sources_operation import (
    OPERATION_KEY as CHECK_CURRENT_GOVERNED_SOURCES_OPERATION_KEY,
)
from ldvh.helper.operations.commit_precheck_operation import COMMIT_PRECHECK_IMPLEMENTATION
from ldvh.helper.operations.commit_precheck_operation import OPERATION_KEY as COMMIT_PRECHECK_OPERATION_KEY
from ldvh.helper.operations.fact_candidate_operation import FACT_CANDIDATE_IMPLEMENTATION
from ldvh.helper.operations.fact_candidate_operation import OPERATION_KEY as FACT_CANDIDATE_OPERATION_KEY
from ldvh.helper.operations.fact_creation_operation import (
    CREATE_FACT_OBJECT_IMPLEMENTATION,
    CREATE_OPERATION_KEY,
    PREPARE_FACT_DRAFT_IMPLEMENTATION,
    PREPARE_OPERATION_KEY,
)
from ldvh.helper.operations.fact_integrity_operation import FACT_INTEGRITY_IMPLEMENTATION
from ldvh.helper.operations.fact_integrity_operation import OPERATION_KEY as FACT_INTEGRITY_OPERATION_KEY
from ldvh.helper.operations.fact_object_operation import FACT_OBJECT_IMPLEMENTATION
from ldvh.helper.operations.fact_object_operation import OPERATION_KEY as FACT_OBJECT_OPERATION_KEY
from ldvh.helper.operations.fact_update_operation import FACT_UPDATE_IMPLEMENTATION
from ldvh.helper.operations.fact_update_operation import OPERATION_KEY as FACT_UPDATE_OPERATION_KEY
from ldvh.helper.operations.governance_scope_operation import (
    GOVERNANCE_SCOPE_IMPLEMENTATION,
)
from ldvh.helper.operations.governance_scope_operation import (
    OPERATION_KEY as GOVERNANCE_SCOPE_OPERATION_KEY,
)
from ldvh.helper.operations.legacy_routed_spark_migration_operation import (
    MIGRATION_IMPLEMENTATION as LEGACY_ROUTED_SPARK_MIGRATION_IMPLEMENTATION,
)
from ldvh.helper.operations.legacy_routed_spark_migration_operation import (
    OPERATION_KEY as LEGACY_ROUTED_SPARK_MIGRATION_OPERATION_KEY,
)
from ldvh.helper.operations.local_edit_operation import LOCAL_EDIT_IMPLEMENTATION
from ldvh.helper.operations.local_edit_operation import OPERATION_KEY as LOCAL_EDIT_OPERATION_KEY
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
from ldvh.helper.operations.specification_context_operation import (
    OPERATION_KEY as SPECIFICATION_CONTEXT_OPERATION_KEY,
)
from ldvh.helper.operations.specification_context_operation import (
    SPECIFICATION_CONTEXT_IMPLEMENTATION,
)
from ldvh.helper.operations.workcase_close_candidate_operation import (
    OPERATION_KEY as WORKCASE_CLOSE_CANDIDATE_OPERATION_KEY,
)
from ldvh.helper.operations.workcase_close_candidate_operation import (
    WORKCASE_CLOSE_CANDIDATE_IMPLEMENTATION,
)
from ldvh.helper.operations.workcase_update_operation import (
    BEGIN_TERMINATION_OPERATION_KEY,
    BEGIN_WORKCASE_TERMINATION_IMPLEMENTATION,
    CLOSE_OPERATION_KEY,
    CLOSE_WORKCASE_IMPLEMENTATION,
    COMPLETE_TERMINATION_OPERATION_KEY,
    COMPLETE_WORKCASE_TERMINATION_IMPLEMENTATION,
    CORRECT_CLOSED_OPERATION_KEY,
    CORRECT_CLOSED_WORKCASE_IMPLEMENTATION,
    RECOVER_INVALID_OPERATION_KEY,
    RECOVER_INVALID_WORKCASE_IMPLEMENTATION,
    UPDATE_OPERATION_KEY,
    UPDATE_WORKCASE_IMPLEMENTATION,
)

IMPLEMENTATIONS = MappingProxyType[str, OperationImplementation](
    {
        ACTION_TEMPLATE_CANDIDATE_OPERATION_KEY: ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION,
        ACTION_TEMPLATE_CONTENT_OPERATION_KEY: ACTION_TEMPLATE_CONTENT_IMPLEMENTATION,
        COMMIT_PRECHECK_OPERATION_KEY: COMMIT_PRECHECK_IMPLEMENTATION,
        CHECK_CURRENT_GOVERNED_SOURCES_OPERATION_KEY: CHECK_CURRENT_GOVERNED_SOURCES_IMPLEMENTATION,
        CREATE_OPERATION_KEY: CREATE_FACT_OBJECT_IMPLEMENTATION,
        FACT_CANDIDATE_OPERATION_KEY: FACT_CANDIDATE_IMPLEMENTATION,
        FACT_INTEGRITY_OPERATION_KEY: FACT_INTEGRITY_IMPLEMENTATION,
        FACT_OBJECT_OPERATION_KEY: FACT_OBJECT_IMPLEMENTATION,
        FACT_UPDATE_OPERATION_KEY: FACT_UPDATE_IMPLEMENTATION,
        LEGACY_ROUTED_SPARK_MIGRATION_OPERATION_KEY: LEGACY_ROUTED_SPARK_MIGRATION_IMPLEMENTATION,
        LOCAL_EDIT_OPERATION_KEY: LOCAL_EDIT_IMPLEMENTATION,
        GOVERNANCE_SCOPE_OPERATION_KEY: GOVERNANCE_SCOPE_IMPLEMENTATION,
        PREPARE_OPERATION_KEY: PREPARE_FACT_DRAFT_IMPLEMENTATION,
        SPECIFICATION_CANDIDATE_OPERATION_KEY: SPECIFICATION_CANDIDATE_IMPLEMENTATION,
        SPECIFICATION_CONTENT_OPERATION_KEY: SPECIFICATION_CONTENT_IMPLEMENTATION,
        SPECIFICATION_CONTEXT_OPERATION_KEY: SPECIFICATION_CONTEXT_IMPLEMENTATION,
        CLOSE_OPERATION_KEY: CLOSE_WORKCASE_IMPLEMENTATION,
        BEGIN_TERMINATION_OPERATION_KEY: BEGIN_WORKCASE_TERMINATION_IMPLEMENTATION,
        COMPLETE_TERMINATION_OPERATION_KEY: COMPLETE_WORKCASE_TERMINATION_IMPLEMENTATION,
        CORRECT_CLOSED_OPERATION_KEY: CORRECT_CLOSED_WORKCASE_IMPLEMENTATION,
        RECOVER_INVALID_OPERATION_KEY: RECOVER_INVALID_WORKCASE_IMPLEMENTATION,
        UPDATE_OPERATION_KEY: UPDATE_WORKCASE_IMPLEMENTATION,
        WORKCASE_CLOSE_CANDIDATE_OPERATION_KEY: WORKCASE_CLOSE_CANDIDATE_IMPLEMENTATION,
    }
)

__all__ = ["IMPLEMENTATIONS"]
