"""Side-effect-free mechanical validation for the 03 Git commit contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.facts.content import validate_fact_content
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.file_asset import validate_file_asset_snapshot
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import parse_rfc3339

_HEADER = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z]+(?:-[a-z]+)*)\))?(?P<breaking>!)?: (?P<description>.+)$"
)
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_FIXED_HEADINGS = ("动机:", "关键变更:", "影响边界:", "验证结论:", "风险与后续:")
_TRAILER = re.compile(r"(?P<name>[A-Za-z][A-Za-z-]*): (?P<value>.*)\Z")
_REQUIRED_TRAILERS = ("Session-ID", "Agent-ID", "Host-Environment")
SEMANTIC_CHECKS_REQUIRED = (
    "主要目的与拆分",
    "简体中文语义与 description 真实性",
    "高影响分类",
    "breaking 必要性",
    "body 充分性",
    "验证结论与风险真实性",
)


@dataclass(frozen=True, slots=True)
class StagedFactCandidate:
    """One staged candidate inside a fact layout, observed per specs 03 §9.9.

    ``object_id`` is ``None`` when the file name cannot parse into a legal
    object_id; ``data`` carries the staged blob bytes read by the observation
    layer from the bound Index; ``observation_issue`` records why the staged
    content could not be observed.
    """

    path: str
    fact_type_key: str
    object_id: str | None
    data: bytes | None
    observation_issue: str | None
    file_asset_targets: tuple[StagedFileAssetTarget, ...] = ()
    file_asset_target_scan_issue: str | None = None


@dataclass(frozen=True, slots=True)
class StagedFileAssetTarget:
    """One FileAsset after-image read from the same bound Index as a WorkCase."""

    object_id: str
    member_names: tuple[str, ...]
    manifest_data: bytes | None
    payload_data: bytes | None
    observation_issue: str | None = None


@dataclass(frozen=True, slots=True)
class StagedFileAssetCandidate:
    """One complete staged FileAsset directory after-image."""

    object_id: str | None
    paths: tuple[str, ...]
    member_names: tuple[str, ...]
    manifest_data: bytes | None
    payload_data: bytes | None
    head_exists: bool | None
    observation_issue: str | None = None
    validation_issue: str | None = None
    head_commit: str | None = None
    head_member_names: tuple[str, ...] = ()
    head_manifest_data: bytes | None = None
    head_payload_data: bytes | None = None
    head_payload_oid: str | None = None
    incoming_workcases: tuple[StagedFactCandidate, ...] = ()
    incoming_scan_issue: str | None = None


@dataclass(frozen=True, slots=True)
class CommitValidationInput:
    message: str | None
    candidate_paths: tuple[str, ...] | None
    git_worktree_root: str | None
    governance_status: str | None
    governance_identity: str | None
    snapshot_identity: str | None
    source_path: str | None
    source_fingerprint: str | None
    fact_candidates: tuple[StagedFactCandidate, ...] = ()
    file_asset_candidates: tuple[StagedFileAssetCandidate, ...] = ()
    fact_schemas: tuple[FactSchema, ...] = ()


@dataclass(frozen=True, slots=True)
class CommitValidationIssue:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class CommitValidationResult:
    outcome: Literal["passed", "failed", "unverifiable"]
    issues: tuple[CommitValidationIssue, ...]
    normalized_message: str | None
    header: str | None
    body: str | None
    source_path: str
    source_fingerprint: str
    semantic_checks_required: tuple[str, ...]


def _issue(code: str, message: str) -> CommitValidationIssue:
    return CommitValidationIssue(code, message)


def _normalize_message(message: str) -> tuple[str, list[str]]:
    normalized = message.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    while lines and (not lines[0].strip() or lines[0].startswith("#")):
        lines.pop(0)
    return "\n".join(lines).rstrip(), lines


def _path_issues(paths: tuple[str, ...]) -> list[CommitValidationIssue]:
    issues: list[CommitValidationIssue] = []
    if not paths:
        return [_issue("candidate_paths_empty", "完整候选路径不能为空")]
    if len(set(paths)) != len(paths):
        issues.append(_issue("candidate_paths_duplicate", "候选路径不得重复"))
    for path in paths:
        parts = path.split("/")
        if not path or path.startswith("/") or "\\" in path or any(part in {"", ".", ".."} for part in parts):
            issues.append(_issue("candidate_path_invalid", f"候选路径不是规范化 worktree 相对路径: {path!r}"))
    return issues


def _heading_has_list(body_lines: list[str], heading: str) -> bool:
    positions = [index for index, line in enumerate(body_lines) if line == heading]
    if len(positions) != 1:
        return False
    start = positions[0] + 1
    for line in body_lines[start:]:
        if line in _FIXED_HEADINGS or re.fullmatch(r"[A-Za-z-]+:\s*.*", line):
            break
        if line.startswith("- ") and line[2:].strip():
            return True
    return False


def _footer_trailer_start(lines: list[str]) -> int | None:
    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    start = end
    while start > 0 and _TRAILER.fullmatch(lines[start - 1]) is not None:
        start -= 1
    if start == end or (start > 0 and lines[start - 1].strip()):
        return None
    return start


def _footer_trailers(lines: list[str]) -> dict[str, list[str]]:
    """Read the final contiguous Git-trailer block, without treating body text as a footer."""

    start = _footer_trailer_start(lines)
    if start is None:
        return {}
    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    trailers: dict[str, list[str]] = {}
    for line in lines[start:end]:
        match = _TRAILER.fullmatch(line)
        assert match is not None
        trailers.setdefault(match.group("name"), []).append(match.group("value"))
    return trailers


def _signature_trailer_issues(lines: list[str]) -> list[CommitValidationIssue]:
    trailers = _footer_trailers(lines)
    issues: list[CommitValidationIssue] = []
    for name in _REQUIRED_TRAILERS:
        values = trailers.get(name, [])
        if len(values) != 1 or not values[0].strip():
            issues.append(_issue("signature_trailer_missing", f"footer 必须恰含一个非空 {name}: trailer"))
    return issues


def _workcase_file_asset_target_issues(
    candidate: StagedFactCandidate,
    fields: dict[str, object],
    schema: FactSchema | None,
) -> tuple[list[CommitValidationIssue], list[CommitValidationIssue]]:
    unavailable: list[CommitValidationIssue] = []
    failures: list[CommitValidationIssue] = []
    relations = fields.get("relations")
    target_ids: list[str] = []
    for relation in relations if isinstance(relations, list) else []:
        if not isinstance(relation, dict) or relation.get("relation_key") != "has-file-asset":
            continue
        target = relation.get("target")
        if (
            isinstance(target, dict)
            and target.get("fact_type_key") == "file-asset"
            and isinstance(target.get("object_id"), str)
        ):
            target_ids.append(target["object_id"])
    if not target_ids:
        return unavailable, failures
    if candidate.file_asset_target_scan_issue is not None:
        unavailable.append(
            _issue(
                "file_asset_target_scan_unverifiable",
                f"WorkCase FileAsset target Index 扫描未完成: {candidate.path}: "
                f"{candidate.file_asset_target_scan_issue}",
            )
        )
        return unavailable, failures
    if schema is None:
        unavailable.append(
            _issue(
                "fact_schema_unavailable",
                f"FileAsset Schema 投影未形成，无法校验 WorkCase target: {candidate.path}",
            )
        )
        return unavailable, failures
    targets = {target.object_id: target for target in candidate.file_asset_targets}
    for object_id in sorted(set(target_ids)):
        target = targets.get(object_id)
        if target is None:
            failures.append(
                _issue(
                    "file_asset_target_not_active",
                    f"WorkCase has-file-asset target 在 Index after-image 中不存在: {object_id}",
                )
            )
            continue
        if target.observation_issue is not None:
            unavailable.append(
                _issue(
                    "file_asset_target_unverifiable",
                    f"WorkCase has-file-asset target 无法可信观察: {object_id}: "
                    f"{target.observation_issue}",
                )
            )
            continue
        snapshot = validate_file_asset_snapshot(
            schema,
            object_id,
            target.manifest_data,
            target.payload_data,
            member_names=target.member_names,
        )
        if snapshot.check_status == "unavailable":
            unavailable.append(
                _issue(
                    "file_asset_target_unverifiable",
                    f"WorkCase has-file-asset target 无法完成机械校验: {object_id}",
                )
            )
        elif (
            snapshot.check_status != "mechanically_valid"
            or snapshot.fields is None
            or snapshot.fields.get("status") != "active"
            or snapshot.current_bytes_confirmed is not True
        ):
            failures.append(
                _issue(
                    "file_asset_target_not_active",
                    f"WorkCase has-file-asset target 必须是 Index 中完整有效的 active FileAsset: {object_id}",
                )
            )
    return unavailable, failures


def _fact_layer(
    value: CommitValidationInput,
) -> tuple[list[CommitValidationIssue], list[CommitValidationIssue]]:
    """Validate staged fact candidates through the single shared content core.

    Returns ``(unavailable, failures)``: observation or schema-projection gaps
    make the layer unverifiable, mechanically invalid content fails it.  The
    function performs no I/O; schemas and blob bytes are caller-supplied.
    """

    unavailable: list[CommitValidationIssue] = []
    failures: list[CommitValidationIssue] = []
    schemas = {schema.fact_type_key: schema for schema in value.fact_schemas}
    for candidate in value.fact_candidates:
        if candidate.object_id is None:
            failures.append(
                _issue("fact_object_id_invalid", f"事实候选文件名不能解析为合法 object_id: {candidate.path}")
            )
            continue
        if candidate.observation_issue is not None or candidate.data is None:
            detail = candidate.observation_issue or "暂存内容缺失"
            unavailable.append(
                _issue("fact_candidate_unverifiable", f"事实候选暂存内容无法可信观察: {candidate.path}: {detail}")
            )
            continue
        schema = schemas.get(candidate.fact_type_key)
        layout = LAYOUTS.get(candidate.fact_type_key)
        if schema is None or layout is None:
            unavailable.append(
                _issue("fact_schema_unavailable", f"事实 Schema 投影未形成，无法校验候选: {candidate.path}")
            )
            continue
        result = validate_fact_content(layout, schema, candidate.object_id, candidate.data)
        if result.check_status == "unavailable":
            unavailable.extend(
                _issue("fact_candidate_unverifiable", f"事实候选无法完成机械校验: {candidate.path}: {item.summary}")
                for item in result.issues
            )
            continue
        if result.check_status == "invalid":
            failures.extend(
                _issue(
                    "fact_candidate_invalid",
                    f"事实候选机械无效: {candidate.path}: [{item.category}] {item.summary}"
                    + (f"（{item.field_path}）" if item.field_path else ""),
                )
                for item in result.issues
            )
            continue
        if candidate.fact_type_key == "workcase" and result.fields is not None:
            target_unavailable, target_failures = _workcase_file_asset_target_issues(
                candidate,
                result.fields,
                schemas.get("file-asset"),
            )
            unavailable.extend(target_unavailable)
            failures.extend(target_failures)
    file_asset_schema = schemas.get("file-asset")
    for candidate in value.file_asset_candidates:
        rendered_paths = ", ".join(candidate.paths) or "ldvh-base/file-assets"
        if candidate.object_id is None:
            failures.append(
                _issue("fact_object_id_invalid", f"FileAsset 暂存路径不能解析为合法对象目录: {rendered_paths}")
            )
            continue
        if candidate.observation_issue is not None or candidate.head_exists is None:
            detail = candidate.observation_issue or "不能确认 HEAD 中是否已有该 FileAsset"
            unavailable.append(
                _issue(
                    "fact_candidate_unverifiable",
                    f"FileAsset Index after-image 无法可信观察: {candidate.object_id}: {detail}",
                )
            )
            continue
        if candidate.validation_issue is not None:
            failures.append(
                _issue(
                    "fact_candidate_invalid",
                    f"FileAsset Index after-image 机械无效: {candidate.object_id}: {candidate.validation_issue}",
                )
            )
            continue
        if file_asset_schema is None:
            unavailable.append(
                _issue("fact_schema_unavailable", f"FileAsset Schema 投影未形成: {candidate.object_id}")
            )
            continue
        snapshot = validate_file_asset_snapshot(
            file_asset_schema,
            candidate.object_id,
            candidate.manifest_data,
            candidate.payload_data,
            member_names=candidate.member_names,
        )
        if snapshot.check_status == "unavailable":
            unavailable.extend(
                _issue(
                    "fact_candidate_unverifiable",
                    f"FileAsset 新建 after-image 无法完成机械校验: {candidate.object_id}: {item.summary}",
                )
                for item in snapshot.issues
            )
        elif snapshot.check_status == "invalid":
            failures.extend(
                _issue(
                    "fact_candidate_invalid",
                    f"FileAsset 新建 after-image 机械无效: {candidate.object_id}: [{item.category}] {item.summary}"
                    + (f"（{item.field_path}）" if item.field_path else ""),
                )
                for item in snapshot.issues
            )
        elif not candidate.head_exists and (
            snapshot.fields is None or snapshot.fields.get("status") != "active"
        ):
            failures.append(
                _issue("fact_candidate_invalid", f"新建 FileAsset 初始 status 必须是 active: {candidate.object_id}")
            )
        elif candidate.head_exists:
            if snapshot.fields is None or snapshot.fields.get("status") != "deleted":
                failures.append(
                    _issue(
                        "file_asset_lifecycle_write_unavailable",
                        f"既有 FileAsset 只允许形成完整 active→deleted tombstone: {candidate.object_id}",
                    )
                )
                continue
            if (
                candidate.head_commit is None
                or candidate.head_manifest_data is None
                or candidate.head_payload_data is None
                or candidate.head_payload_oid is None
            ):
                unavailable.append(
                    _issue(
                        "fact_candidate_unverifiable",
                        f"FileAsset HEAD active before-image 无法完整观察: {candidate.object_id}",
                    )
                )
                continue
            head_snapshot = validate_file_asset_snapshot(
                file_asset_schema,
                candidate.object_id,
                candidate.head_manifest_data,
                candidate.head_payload_data,
                member_names=candidate.head_member_names,
            )
            if (
                head_snapshot.check_status != "mechanically_valid"
                or head_snapshot.fields is None
                or head_snapshot.fields.get("status") != "active"
                or head_snapshot.current_bytes_confirmed is not True
            ):
                failures.append(
                    _issue(
                        "file_asset_delete_before_invalid",
                        f"FileAsset 删除 before 必须是 HEAD 中完整有效的 active carrier: {candidate.object_id}",
                    )
                )
                continue
            before = head_snapshot.fields
            after = snapshot.fields
            preserved = {
                "object_id",
                "fact_type_key",
                "title",
                "created_at",
                "filename",
                "media_type",
                "size_bytes",
                "content_sha256",
                "signature",
            }
            changed = sorted(name for name in preserved if before.get(name) != after.get(name))
            if changed:
                failures.append(
                    _issue(
                        "file_asset_delete_metadata_changed",
                        f"FileAsset 删除必须保留原 metadata: {candidate.object_id}: {', '.join(changed)}",
                    )
                )
            before_updated = parse_rfc3339(before.get("updated_at"))
            after_updated = parse_rfc3339(after.get("updated_at"))
            if before_updated is None or after_updated is None or after_updated <= before_updated:
                failures.append(
                    _issue(
                        "file_asset_delete_time_invalid",
                        f"FileAsset deleted_at/updated_at 必须晚于 active before: {candidate.object_id}",
                    )
                )
            expected_path = f"ldvh-base/file-assets/{candidate.object_id}/payload"
            recovery = after.get("recovery")
            if not isinstance(recovery, dict) or recovery != {
                "commit": candidate.head_commit,
                "path": expected_path,
                "blob_oid": candidate.head_payload_oid,
            }:
                failures.append(
                    _issue(
                        "file_asset_delete_recovery_mismatch",
                        f"FileAsset deleted recovery 必须精确回指 HEAD payload blob: {candidate.object_id}",
                    )
                )
            if candidate.incoming_scan_issue is not None:
                unavailable.append(
                    _issue(
                        "file_asset_incoming_scan_unverifiable",
                        f"FileAsset 删除无法完成 Index WorkCase 入向扫描: {candidate.incoming_scan_issue}",
                    )
                )
                continue
            workcase_schema = schemas.get("workcase")
            if workcase_schema is None:
                unavailable.append(
                    _issue(
                        "fact_schema_unavailable",
                        f"WorkCase Schema 投影未形成，无法证明 FileAsset 零入向引用: {candidate.object_id}",
                    )
                )
                continue
            for workcase in candidate.incoming_workcases:
                assert workcase.object_id is not None and workcase.data is not None
                checked = validate_fact_content(
                    LAYOUTS["workcase"],
                    workcase_schema,
                    workcase.object_id,
                    workcase.data,
                )
                if checked.check_status != "mechanically_valid" or checked.fields is None:
                    unavailable.append(
                        _issue(
                            "file_asset_incoming_scan_unverifiable",
                            f"Index WorkCase 无法作为零引用证明读取: {workcase.path}",
                        )
                    )
                    continue
                relations = checked.fields.get("relations")
                for relation in relations if isinstance(relations, list) else []:
                    if not isinstance(relation, dict) or relation.get("relation_key") != "has-file-asset":
                        continue
                    target = relation.get("target")
                    if not isinstance(target, dict):
                        continue
                    if (
                        target.get("fact_type_key") == "file-asset"
                        and target.get("object_id") == candidate.object_id
                    ):
                        failures.append(
                            _issue(
                                "file_asset_incoming_reference",
                                f"FileAsset 仍被 Index WorkCase 引用: {candidate.object_id} <- {workcase.object_id}",
                            )
                        )
    return unavailable, failures


def validate_commit(contract: CommitContractProjection, value: CommitValidationInput) -> CommitValidationResult:
    """Validate only the deterministic subset; never reads Git or the filesystem."""

    unavailable: list[CommitValidationIssue] = []
    required = {
        "message": value.message,
        "candidate_paths": value.candidate_paths,
        "git_worktree_root": value.git_worktree_root,
        "governance_status": value.governance_status,
        "governance_identity": value.governance_identity,
        "snapshot_identity": value.snapshot_identity,
        "source_path": value.source_path,
        "source_fingerprint": value.source_fingerprint,
    }
    for field, field_value in required.items():
        if field_value is None or (field != "message" and field_value == ""):
            unavailable.append(_issue("input_missing", f"缺少必需输入: {field}"))
    if value.governance_status is not None and value.governance_status != "governed_single":
        unavailable.append(_issue("governance_unverifiable", "提交契约只校验 governed_single 目标"))
    if value.source_path is not None and value.source_path != contract.source_path:
        unavailable.append(_issue("source_path_mismatch", "输入来源路径与契约投影不一致"))
    if value.source_fingerprint is not None and value.source_fingerprint != contract.content_fingerprint:
        unavailable.append(_issue("source_fingerprint_mismatch", "输入来源指纹与契约投影不一致"))
    if value.candidate_paths is not None:
        unavailable.extend(_path_issues(value.candidate_paths))
    fact_unavailable, fact_failures = _fact_layer(value)
    unavailable.extend(fact_unavailable)
    if unavailable:
        return CommitValidationResult(
            "unverifiable",
            tuple(unavailable),
            None,
            None,
            None,
            contract.source_path,
            contract.content_fingerprint,
            SEMANTIC_CHECKS_REQUIRED,
        )

    assert value.message is not None and value.candidate_paths is not None
    normalized, lines = _normalize_message(value.message)
    failures: list[CommitValidationIssue] = []
    if not lines or not normalized:
        failures.append(_issue("message_empty", "完整 message 清理后不能为空"))
        header = None
        body = None
    else:
        header = lines[0]
        body_lines = lines[1:]
        footer_start = _footer_trailer_start(body_lines)
        content_body_lines = body_lines if footer_start is None else body_lines[:footer_start]
        while content_body_lines and not content_body_lines[-1].strip():
            content_body_lines.pop()
        while content_body_lines and not content_body_lines[0].strip():
            content_body_lines.pop(0)
        body = "\n".join(content_body_lines).rstrip() or None
        match = _HEADER.fullmatch(header)
        if match is None:
            failures.append(_issue("header_invalid", "header 不符合 type[(scope)][!]: 简体中文描述"))
        else:
            commit_type = match.group("type")
            scope = match.group("scope")
            breaking = match.group("breaking") is not None
            description = match.group("description")
            if commit_type not in contract.type_tokens:
                failures.append(_issue("type_unknown", f"未知 type: {commit_type}"))
            if scope is not None and scope not in contract.scope_tokens:
                failures.append(_issue("scope_unknown", f"未知 scope: {scope}"))
            if _CJK.search(description) is None:
                failures.append(_issue("description_cjk_missing", "description 至少需要一个 CJK 字符"))
            if description.endswith(("。", ".")):
                failures.append(_issue("description_period", "description 不使用句号结尾"))
            body_required = len(value.candidate_paths) >= 2 or breaking or commit_type == "revert"
            if body_required and body is None:
                failures.append(_issue("body_required", "当前机械 trigger 要求 body"))
            if body is not None:
                if not _heading_has_list(content_body_lines, "关键变更:"):
                    failures.append(_issue("key_changes_required", "body 必须含关键变更列表"))
                if breaking and not _heading_has_list(content_body_lines, "影响边界:"):
                    failures.append(_issue("impact_boundary_required", "使用 ! 时必须含影响边界列表"))
            failures.extend(_signature_trailer_issues(lines[1:]))
    outcome: Literal["passed", "failed", "unverifiable"] = "failed" if failures or fact_failures else "passed"
    return CommitValidationResult(
        outcome,
        tuple(failures + fact_failures),
        normalized,
        header,
        body,
        contract.source_path,
        contract.content_fingerprint,
        SEMANTIC_CHECKS_REQUIRED,
    )


__all__ = [
    "CommitValidationInput",
    "CommitValidationIssue",
    "CommitValidationResult",
    "SEMANTIC_CHECKS_REQUIRED",
    "StagedFactCandidate",
    "StagedFileAssetCandidate",
    "validate_commit",
]
