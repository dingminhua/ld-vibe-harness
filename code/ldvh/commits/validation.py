"""Side-effect-free mechanical validation for the 03 Git commit contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.facts.content import validate_fact_content
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.schema import FactSchema

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
    # The Git adapter supplies the corresponding HEAD after it binds the Index.
    # Keeping both images lets the Gate prove that a fact's new trace entry is
    # the one signed by this commit, rather than merely schema-valid YAML.
    head_data: bytes | None = None
    head_exists: bool | None = None
    head_observation_issue: str | None = None



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
    if trailers.get("Signer-Type"):
        issues.append(_issue("signer_type_retired", "footer 禁止已退役的 Signer-Type trailer"))
    return issues



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
    return unavailable, failures


def _fact_trace_issues(
    value: CommitValidationInput,
    trailers: dict[str, list[str]],
) -> tuple[list[CommitValidationIssue], list[CommitValidationIssue]]:
    """Bind every staged single-file fact event to this commit's footer.

    The commit validator is deliberately fail-closed when the before image is
    unavailable: an after image alone cannot establish which log entry is the
    event introduced by this candidate.
    """

    unavailable: list[CommitValidationIssue] = []
    failures: list[CommitValidationIssue] = []
    schemas = {schema.fact_type_key: schema for schema in value.fact_schemas}
    expected = {
        "session_id": trailers.get("Session-ID", [""])[0],
        "agent_id": trailers.get("Agent-ID", [""])[0],
        "host_environment": trailers.get("Host-Environment", [""])[0],
    }
    for candidate in value.fact_candidates:
        if candidate.object_id is None or candidate.data is None or candidate.observation_issue is not None:
            continue  # The fact layer already records the primary observation failure.
        schema = schemas.get(candidate.fact_type_key)
        layout = LAYOUTS.get(candidate.fact_type_key)
        if schema is None or layout is None:
            continue
        after_checked = validate_fact_content(layout, schema, candidate.object_id, candidate.data)
        if after_checked.check_status != "mechanically_valid" or after_checked.fields is None:
            continue
        if candidate.head_exists is None:
            unavailable.append(_issue("fact_trace_unverifiable", f"无法确认事实 HEAD before-image: {candidate.path}"))
            continue
        before_fields: dict[str, object] | None = None
        if candidate.head_exists:
            if candidate.head_observation_issue is not None or candidate.head_data is None:
                unavailable.append(
                    _issue(
                        "fact_trace_unverifiable",
                        f"事实 HEAD before-image 无法可信读取: {candidate.path}: "
                        f"{candidate.head_observation_issue or 'missing blob'}",
                    )
                )
                continue
            before_checked = validate_fact_content(layout, schema, candidate.object_id, candidate.head_data)
            if before_checked.check_status != "mechanically_valid" or before_checked.fields is None:
                unavailable.append(
                    _issue("fact_trace_unverifiable", f"事实 HEAD before-image 不可机械消费: {candidate.path}")
                )
                continue
            before_fields = before_checked.fields
        after_log = after_checked.fields.get("change_log")
        before_log = None if before_fields is None else before_fields.get("change_log")
        if not isinstance(after_log, list):
            failures.append(_issue("fact_trace_missing", f"事实候选缺少可校验 change_log: {candidate.path}"))
            continue
        if before_fields is None:
            # A fact may be created and then legitimately progressed several
            # times before its first Git commit.  All of that uncommitted
            # history belongs to this candidate, so bind every entry to the
            # commit footer instead of incorrectly requiring one entry.
            appended = after_log
        elif isinstance(before_log, list) and after_log[: len(before_log)] == before_log:
            appended = after_log[len(before_log) :]
        else:
            failures.append(
                _issue("fact_trace_transition_invalid", f"事实流水前后像不能确定唯一新增事件: {candidate.path}")
            )
            continue
        if not appended or not all(isinstance(entry, dict) for entry in appended):
            requirement = "至少含一条初始流水" if before_fields is None else "恰新增一条流水"
            failures.append(_issue("fact_trace_append_invalid", f"事实候选必须{requirement}: {candidate.path}"))
            continue
        if any(
            {
                "session_id": entry.get("session_id"),
                "agent_id": entry.get("signature", {}).get("agent_id")
                if isinstance(entry.get("signature"), dict)
                else None,
                "host_environment": entry.get("signature", {}).get("host_environment")
                if isinstance(entry.get("signature"), dict)
                else None,
            }
            != expected
            for entry in appended
        ):
            failures.append(
                _issue(
                    "fact_trace_signature_mismatch",
                    f"事实新增流水与提交 footer 的 Session-ID/Agent-ID/Host-Environment 不一致: {candidate.path}",
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
            signature_issues = _signature_trailer_issues(lines[1:])
            failures.extend(signature_issues)
            if not signature_issues:
                trace_unavailable, trace_failures = _fact_trace_issues(value, _footer_trailers(lines[1:]))
                unavailable.extend(trace_unavailable)
                failures.extend(trace_failures)
    # A mechanically invalid after-image remains a failure even when a separate
    # candidate cannot be observed completely.  The Gate must preserve the
    # decisive rejection rather than downgrade it to an observation gap.
    outcome: Literal["passed", "failed", "unverifiable"] = (
        "failed" if failures or fact_failures else "unverifiable" if unavailable else "passed"
    )
    return CommitValidationResult(
        outcome,
        tuple(unavailable + failures + fact_failures),
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
