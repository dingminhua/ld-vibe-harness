"""Side-effect-free mechanical validation for the 03 Git commit contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.facts.content import validate_fact_content
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.schema import FactSchema

_HEADER = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z]+)\))?(?P<breaking>!)?: (?P<description>.+)$")
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_FIXED_HEADINGS = ("动机:", "关键变更:", "影响边界:", "验证结论:", "风险与后续:")
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
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
        body = "\n".join(body_lines).rstrip() or None
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
                if not _heading_has_list(body_lines, "关键变更:"):
                    failures.append(_issue("key_changes_required", "body 必须含关键变更列表"))
                if breaking and not _heading_has_list(body_lines, "影响边界:"):
                    failures.append(_issue("impact_boundary_required", "使用 ! 时必须含影响边界列表"))
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
    "validate_commit",
]
