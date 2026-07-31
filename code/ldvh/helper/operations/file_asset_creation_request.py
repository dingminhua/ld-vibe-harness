"""Parse source-defined FileAsset intake and controlled creation requests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.governance.models import ScopeDescriptor, explicit_scope
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.requests import CommonRequest

PREPARE_REQUIRED_INPUTS = (
    "work_object_locators",
    "arguments.governed_project_id",
    "arguments.source_path",
)
PREPARE_OPTIONAL_INPUTS = ("arguments.workspace_root",)
CREATE_REQUIRED_INPUTS = (
    "work_object_locators",
    "arguments.intake_basis",
    "arguments.fact_object",
)
CREATE_OPTIONAL_INPUTS = ("arguments.workspace_root", "authorization_reference")

_PREPARE_FIELDS = frozenset({"workspace_root", "governed_project_id", "source_path"})
_CREATE_FIELDS = frozenset({"workspace_root", "intake_basis", "fact_object"})
_BASIS_FIELDS = frozenset(
    {
        "governed_project_id",
        "candidate_object_id",
        "schema_fingerprint",
        "worktree_fingerprint",
        "source_path",
        "source_size_bytes",
        "source_content_sha256",
        "source_fingerprint",
    }
)
_FACT_OBJECT_FIELDS = frozenset({"title", "filename", "media_type", "signature"})
_FINGERPRINT_FIELDS = frozenset(
    {"schema_fingerprint", "worktree_fingerprint", "source_content_sha256", "source_fingerprint"}
)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


@dataclass(frozen=True, slots=True)
class FileAssetIntakeBasis:
    governed_project_id: str
    candidate_object_id: str
    schema_fingerprint: str
    worktree_fingerprint: str
    source_path: str
    source_size_bytes: int
    source_content_sha256: str
    source_fingerprint: str

    def to_json(self) -> dict[str, Any]:
        return {
            "governed_project_id": self.governed_project_id,
            "candidate_object_id": self.candidate_object_id,
            "schema_fingerprint": self.schema_fingerprint,
            "worktree_fingerprint": self.worktree_fingerprint,
            "source_path": self.source_path,
            "source_size_bytes": self.source_size_bytes,
            "source_content_sha256": self.source_content_sha256,
            "source_fingerprint": self.source_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class FileAssetIntakeRequest:
    locator: str
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    governed_project_id: str
    source_path: Path
    base: Path


@dataclass(frozen=True, slots=True)
class FileAssetCreateRequest:
    locator: str
    workspace_root: Path | None
    governance_scope: tuple[ScopeDescriptor, ...]
    intake_basis: FileAssetIntakeBasis
    fact_object: dict[str, Any]
    authorization_reference: tuple[dict[str, Any], ...]
    base: Path


@dataclass(frozen=True, slots=True)
class FileAssetCreationParseResult:
    request: FileAssetIntakeRequest | FileAssetCreateRequest | None
    problems: tuple[str, ...]


def _common(
    request: CommonRequest,
    context: OperationExecutionContext,
    allowed_fields: frozenset[str],
) -> tuple[list[str], str, Path | None, tuple[ScopeDescriptor, ...]]:
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
    unknown = sorted(set(request.arguments) - allowed_fields)
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")
    workspace_root: Path | None = None
    raw_workspace = request.arguments.get("workspace_root")
    if raw_workspace is not None:
        if not isinstance(raw_workspace, str) or not raw_workspace.strip() or not Path(raw_workspace).is_absolute():
            problems.append("arguments.workspace_root 出现时必须为非空绝对路径 string")
        else:
            workspace_root = Path(raw_workspace)
    if request.observed_context:
        problems.append("observed_context 对 FileAsset 摄取与创建操作必须为空 object")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 对 FileAsset 摄取与创建操作必须为 null 或省略")
    scope = explicit_scope((locator,)) if locator else ()
    return problems, locator, workspace_root, scope


def parse_file_asset_intake_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> FileAssetCreationParseResult:
    problems, locator, workspace_root, scope = _common(request, context, _PREPARE_FIELDS)
    project_id = request.arguments.get("governed_project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        problems.append("arguments.governed_project_id 必须是非空 string")
    raw_source = request.arguments.get("source_path")
    if not isinstance(raw_source, str) or not raw_source.strip() or not Path(raw_source).is_absolute():
        problems.append("arguments.source_path 必须是非空绝对路径 string")
        source_path = Path(".")
    else:
        source_path = Path(raw_source)
    if request.authorization_reference:
        problems.append("authorization_reference 对无副作用 FileAsset 摄取准备必须为空 array")
    if problems:
        return FileAssetCreationParseResult(None, tuple(problems))
    assert isinstance(project_id, str)
    return FileAssetCreationParseResult(
        FileAssetIntakeRequest(
            locator,
            workspace_root,
            scope,
            project_id,
            source_path,
            context.cwd,
        ),
        (),
    )


def parse_file_asset_create_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> FileAssetCreationParseResult:
    problems, locator, workspace_root, scope = _common(request, context, _CREATE_FIELDS)
    raw_basis = request.arguments.get("intake_basis")
    basis: FileAssetIntakeBasis | None = None
    if not isinstance(raw_basis, dict):
        problems.append("arguments.intake_basis 必须是 object")
    else:
        unknown = sorted(set(raw_basis) - _BASIS_FIELDS)
        if unknown:
            problems.append(f"arguments.intake_basis 包含未知字段: {', '.join(unknown)}")
        text_values: dict[str, str] = {}
        for field in sorted(_BASIS_FIELDS - {"source_size_bytes"}):
            value = raw_basis.get(field)
            if not isinstance(value, str) or not value:
                problems.append(f"arguments.intake_basis.{field} 必须是非空 string")
            else:
                text_values[field] = value
        raw_size = raw_basis.get("source_size_bytes")
        if not isinstance(raw_size, int) or isinstance(raw_size, bool) or raw_size < 0:
            problems.append("arguments.intake_basis.source_size_bytes 必须是非负 integer")
        if len(text_values) == len(_BASIS_FIELDS) - 1 and isinstance(raw_size, int) and not isinstance(raw_size, bool):
            if LAYOUTS["file-asset"].object_id_pattern.fullmatch(text_values["candidate_object_id"]) is None:
                problems.append("arguments.intake_basis.candidate_object_id 与 FileAsset 身份格式不一致")
            elif not Path(text_values["source_path"]).is_absolute():
                problems.append("arguments.intake_basis.source_path 必须是绝对路径")
            elif invalid_fingerprints := sorted(
                field for field in _FINGERPRINT_FIELDS if not _is_sha256(text_values[field])
            ):
                problems.append(
                    "arguments.intake_basis 下列字段必须是 64 位小写十六进制 SHA-256: "
                    + ", ".join(invalid_fingerprints)
                )
            else:
                basis = FileAssetIntakeBasis(source_size_bytes=raw_size, **text_values)
    raw_fact = request.arguments.get("fact_object")
    fact_object: dict[str, Any] = {}
    if not isinstance(raw_fact, dict):
        problems.append("arguments.fact_object 必须是 object")
    else:
        unknown = sorted(set(raw_fact) - _FACT_OBJECT_FIELDS)
        missing = sorted(_FACT_OBJECT_FIELDS - set(raw_fact))
        if unknown:
            problems.append(f"arguments.fact_object 包含未知字段: {', '.join(unknown)}")
        if missing:
            problems.append(f"arguments.fact_object 缺少必填字段: {', '.join(missing)}")
        fact_object = dict(raw_fact)
    if problems:
        return FileAssetCreationParseResult(None, tuple(problems))
    assert basis is not None
    return FileAssetCreationParseResult(
        FileAssetCreateRequest(
            locator,
            workspace_root,
            scope,
            basis,
            fact_object,
            request.authorization_reference,
            context.cwd,
        ),
        (),
    )


__all__ = [
    "CREATE_OPTIONAL_INPUTS",
    "CREATE_REQUIRED_INPUTS",
    "PREPARE_OPTIONAL_INPUTS",
    "PREPARE_REQUIRED_INPUTS",
    "FileAssetCreateRequest",
    "FileAssetCreationParseResult",
    "FileAssetIntakeBasis",
    "FileAssetIntakeRequest",
    "parse_file_asset_create_request",
    "parse_file_asset_intake_request",
]
