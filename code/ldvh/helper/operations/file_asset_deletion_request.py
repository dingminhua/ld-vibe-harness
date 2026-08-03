"""Parse source-defined delete-file-asset requests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactReference
from ldvh.governance.models import ScopeDescriptor, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

REQUIRED_INPUTS = (
    "work_object_locators",
    "arguments.fact_ref",
    "arguments.expected_content_fingerprint",
    "arguments.deletion_summary",
    "arguments.change_log_entry",
    "authorization_reference",
)
OPTIONAL_INPUTS = ("arguments.workspace_root",)
_ARGUMENT_FIELDS = frozenset(
    {"workspace_root", "fact_ref", "expected_content_fingerprint", "deletion_summary", "change_log_entry"}
)
_FACT_REF_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class FileAssetDeletionRequest:
    locator: str
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    fact_ref: FactReference
    expected_content_fingerprint: str
    deletion_summary: str
    change_log_entry: dict[str, object]
    authorization_reference: tuple[dict[str, object], ...]
    base: Path


@dataclass(frozen=True, slots=True)
class FileAssetDeletionParseResult:
    request: FileAssetDeletionRequest | None
    problems: tuple[str, ...]


def parse_file_asset_deletion_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> FileAssetDeletionParseResult:
    problems: list[str] = []
    if not context.cwd.is_absolute():
        problems.append("Helper 进程实际 cwd 必须是绝对路径")
    if len(request.work_object_locators) != 1:
        problems.append("work_object_locators 必须恰有一个目标路径 string")
        locator = ""
    else:
        raw_locator = request.work_object_locators[0]
        if not isinstance(raw_locator, str) or not raw_locator.strip():
            problems.append("work_object_locators[0] 必须是非空路径 string")
            locator = ""
        else:
            locator = raw_locator

    unknown = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")
    workspace_root: Path | None = None
    raw_workspace = request.arguments.get("workspace_root")
    if raw_workspace is not None:
        if not isinstance(raw_workspace, str) or not raw_workspace or not Path(raw_workspace).is_absolute():
            problems.append("arguments.workspace_root 出现时必须为非空绝对路径 string")
        else:
            workspace_root = Path(raw_workspace)

    fact_ref: FactReference | None = None
    raw_ref = request.arguments.get("fact_ref")
    if not isinstance(raw_ref, dict):
        problems.append("arguments.fact_ref 必须是 object")
    else:
        unknown_ref = sorted(set(raw_ref) - _FACT_REF_FIELDS)
        if unknown_ref:
            problems.append(f"arguments.fact_ref 包含未知字段: {', '.join(unknown_ref)}")
        values: dict[str, str] = {}
        for name in sorted(_FACT_REF_FIELDS):
            value = raw_ref.get(name)
            if not isinstance(value, str) or not value:
                problems.append(f"arguments.fact_ref.{name} 必须是非空 string")
            else:
                values[name] = value
        if len(values) == len(_FACT_REF_FIELDS):
            if values["fact_type_key"] != "file-asset":
                problems.append("arguments.fact_ref.fact_type_key 必须是 file-asset")
            elif LAYOUTS["file-asset"].object_id_pattern.fullmatch(values["object_id"]) is None:
                problems.append("arguments.fact_ref.object_id 与 FileAsset 身份格式不一致")
            else:
                fact_ref = FactReference(
                    values["governed_project_id"],
                    values["fact_type_key"],
                    values["object_id"],
                )

    fingerprint = request.arguments.get("expected_content_fingerprint")
    if not isinstance(fingerprint, str) or _FINGERPRINT.fullmatch(fingerprint) is None:
        problems.append("arguments.expected_content_fingerprint 必须是 64 位小写十六进制 string")
    summary = request.arguments.get("deletion_summary")
    if not isinstance(summary, str) or not summary.strip():
        problems.append("arguments.deletion_summary 必须是非空 string")
    change_log_entry = request.arguments.get("change_log_entry")
    if not isinstance(change_log_entry, dict):
        problems.append("arguments.change_log_entry 必须是 object")
    if not request.authorization_reference:
        problems.append("authorization_reference 必须非空并回指当前 Human 删除决定或准确授权")
    if request.observed_context:
        problems.append("observed_context 对 FileAsset 安全删除必须为空 object")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对 FileAsset 安全删除必须为 null 或省略")
    if problems:
        return FileAssetDeletionParseResult(None, tuple(problems))

    assert fact_ref is not None and isinstance(fingerprint, str) and isinstance(summary, str)
    assert isinstance(change_log_entry, dict)
    return FileAssetDeletionParseResult(
        FileAssetDeletionRequest(
            locator,
            workspace_root,
            explicit_scope((locator,)),
            fact_ref,
            fingerprint,
            summary,
            change_log_entry,
            request.authorization_reference,
            context.cwd,
        ),
        (),
    )


__all__ = [
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "FileAssetDeletionParseResult",
    "FileAssetDeletionRequest",
    "parse_file_asset_deletion_request",
]
