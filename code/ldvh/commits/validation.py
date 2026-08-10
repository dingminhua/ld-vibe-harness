"""Side-effect-free mechanical validation for the 03 Git commit contract."""

from __future__ import annotations

import fnmatch
import hashlib
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.facts.content import validate_fact_content
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import _WORKBENCH_TOKEN_SPLIT, _is_host_product_concatenation

_HEADER = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z]+(?:-[a-z]+)*)\))?(?P<breaking>!)?: (?P<description>.+)$")
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_FIXED_HEADINGS = ("动机:", "关键变更:", "影响边界:", "验证结论:", "风险与后续:")
_HEADING_LIKE = re.compile(r"^[^\s].*:\s*$")
_TRAILER = re.compile(r"(?P<name>[A-Za-z][A-Za-z-]*): (?P<value>.*)\Z")
_REQUIRED_TRAILERS = ("Session-ID", "Model-ID", "Workbench-Name")
_LEGACY_REPAIR_FIELD = re.compile(
    r"^change_log\[(?P<index>[0-9]+)\]\.signature\.(?P<field>"
    r"agent_id|model_id|agent_workbench|host_environment|host_name)$"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MODEL_PRODUCT_ALIASES = frozenset(
    {"codex", "claude-code", "workbuddy", "workbuddy-ai", "deepseek", "glm", "gpt", "claude", "kimi", "k3"}
)
_WORKBENCH_SYSTEM_SUFFIX = re.compile(r"\s*\([^()]+\)\s*\Z")
_SPEC_PATH_RE = re.compile(r"^specs/[0-9]+-.*\.md$")
_PLATFORM_AFFECTED_GLOBS = (
    "code/ldvh/filesystem.py",
    "code/ldvh/governance/git.py",
    "code/ldvh/testing/test_runs.py",
    "code/ldvh/git_hooks/**",
    "code/ldvh/hooks/**",
    "ldvh",
)
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
    # Keeping both images lets the Gate distinguish newly appended trace entries
    # from read-only legacy history without coupling either to the commit signer.
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
    spec_candidate_statuses: dict[str, str] | None = None
    spec_activated_paths: tuple[str, ...] | None = None
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


def _body_structure_issues(
    body_lines: list[str],
    *,
    require_minimum_body: bool,
    require_impact_boundary: bool,
) -> list[CommitValidationIssue]:
    issues: list[CommitValidationIssue] = []
    positions = {
        heading: [index for index, line in enumerate(body_lines) if line == heading] for heading in _FIXED_HEADINGS
    }
    unknown_positions = [
        index
        for index, line in enumerate(body_lines)
        if line not in _FIXED_HEADINGS and _HEADING_LIKE.fullmatch(line) is not None
    ]
    for index in unknown_positions:
        issues.append(_issue("body_heading_unknown", f"body 包含未知小标题: {body_lines[index]}"))

    boundaries = sorted([index for indexes in positions.values() for index in indexes] + unknown_positions)

    def section_lines(heading: str) -> list[str] | None:
        indexes = positions[heading]
        if len(indexes) != 1:
            return None
        start = indexes[0] + 1
        end = next((index for index in boundaries if index >= start), len(body_lines))
        return body_lines[start:end]

    for heading, indexes in positions.items():
        if len(indexes) > 1:
            issues.append(_issue("body_heading_duplicate", f"body 小标题必须唯一: {heading}"))
            continue
        section = section_lines(heading)
        if section is not None and not any(line.strip() for line in section):
            issues.append(_issue("body_heading_empty", f"body 小标题不得为空: {heading}"))

    def has_nonempty_list(heading: str) -> bool:
        section = section_lines(heading)
        return section is not None and any(line.startswith("- ") and line[2:].strip() for line in section)

    if require_minimum_body and not has_nonempty_list("关键变更:"):
        issues.append(
            _issue(
                "key_changes_required",
                "所有提交的 body 必须含唯一 `关键变更:`，其下至少一个从行首开始的非空 `- ` 列表项",
            )
        )
    if require_impact_boundary and not has_nonempty_list("影响边界:"):
        issues.append(
            _issue(
                "impact_boundary_required",
                "使用 ! 时 body 必须含唯一 `影响边界:`，其下至少一个从行首开始的非空 `- ` 列表项",
            )
        )
    return issues


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
        if not values or any(not value.strip() for value in values):
            issues.append(_issue("signature_trailer_missing", f"footer 必须含一个非空 {name}: trailer"))
        elif len(values) != 1:
            issues.append(_issue("signature_trailer_multiple", f"footer 的 {name}: 必须恰好声明一次"))
        if name == "Model-ID" and any(value.strip().lower() in _MODEL_PRODUCT_ALIASES for value in values):
            issues.append(_issue("signature_model_alias", "footer 的 Model-ID 不得使用已知裸产品别名"))
        elif name == "Model-ID" and any(_is_host_product_concatenation(value) for value in values):
            issues.append(_issue("signature_model_host_product", "footer 的 Model-ID 不得拼接宿主产品名"))
        if name == "Model-ID" and any(value.strip() != value.strip().lower() for value in values):
            issues.append(_issue("signature_model_case", "footer 的 Model-ID 必须全小写"))
        elif name == "Workbench-Name" and any(_WORKBENCH_SYSTEM_SUFFIX.search(value) for value in values):
            issues.append(_issue("signature_host_suffix", "footer 的 Workbench-Name 不得包含括号系统后缀"))
        if name == "Workbench-Name" and any(
            _WORKBENCH_TOKEN_SPLIT.search(value.strip()) for value in values
        ):
            issues.append(
                _issue(
                    "signature_workbench_compound",
                    "footer 的 Workbench-Name 必须为单 token（不使用空格、连字符或斜杠分隔），"
                    "不得使用复合名如 claude-code-mcp 或 Claude Code",
                )
            )
    if trailers.get("Agent-ID") or trailers.get("Host-Environment"):
        issues.append(
            _issue(
                "legacy_signature_trailer_retired",
                "footer 已禁止 Agent-ID/Host-Environment trailer；新提交必须使用 Model-ID/Workbench-Name",
            )
        )
    if trailers.get("Signer-Type"):
        issues.append(_issue("signer_type_retired", "footer 禁止已退役的 Signer-Type trailer"))
    return issues


_VALID_PLATFORM_AFFECTED = frozenset({"macos", "windows", "both", "unaffected"})
_VALID_PLATFORM_VERIFIED = frozenset({"macos", "windows", "both", "none"})


def _platform_affected_issues(
    paths: tuple[str, ...],
    trailers: dict[str, list[str]],
) -> list[CommitValidationIssue]:
    """Check whether the commit touches platform-affecting code.

    Mechanical glob matching determines whether the Index contains files
    inside the platform-related surface.  If it does, the commit message
    must declare ``Platform-Affected`` and ``Platform-Verified`` trailers
    so reviewers and CI can determine whether cross-platform re-verification
    is needed.  Semantic judgment (whether the change actually changes
    behaviour on another platform) is left to AI/Human review.
    """
    issues: list[CommitValidationIssue] = []
    matched = set()
    for path in paths:
        pure = PurePosixPath(path)
        for pattern in _PLATFORM_AFFECTED_GLOBS:
            if fnmatch.fnmatch(str(pure), pattern):
                matched.add(str(pure))
    if not matched:
        return issues

    affected = trailers.get("Platform-Affected", [])
    verified = trailers.get("Platform-Verified", [])

    if not affected or not any(value.strip() for value in affected):
        issues.append(
            _issue(
                "platform_trailer_required",
                "改动触及平台相关面，footer 必须含非空 Platform-Affected: trailer "
                f"(允许值: {', '.join(sorted(_VALID_PLATFORM_AFFECTED))})",
            )
        )
    else:
        for value in affected:
            val = value.strip().lower()
            if val not in _VALID_PLATFORM_AFFECTED:
                issues.append(
                    _issue(
                        "platform_trailer_invalid",
                        f"Platform-Affected 值无效: {value!r}，允许值: {', '.join(sorted(_VALID_PLATFORM_AFFECTED))}",
                    )
                )

    if not verified or not any(value.strip() for value in verified):
        issues.append(
            _issue(
                "platform_trailer_required",
                "改动触及平台相关面，footer 必须含非空 Platform-Verified: trailer "
                f"(允许值: {', '.join(sorted(_VALID_PLATFORM_VERIFIED))})",
            )
        )
    else:
        for value in verified:
            val = value.strip().lower()
            if val not in _VALID_PLATFORM_VERIFIED:
                issues.append(
                    _issue(
                        "platform_trailer_invalid",
                        f"Platform-Verified 值无效: {value!r}，允许值: {', '.join(sorted(_VALID_PLATFORM_VERIFIED))}",
                    )
                )

    diagnostics = ", ".join(sorted(matched))

    # When trailers are valid, the check passes without issues.
    # Only emit the surface-touched diagnostic when there are actual trailer
    # failures, so the user knows why the check fired.
    if not issues:
        return issues

    issues.append(
        _issue(
            "platform_surface_touched",
            f"本次提交触及平台相关面文件: {diagnostics}",
        )
    )
    return issues


def _human_gate_trailer_issues(
    lines: list[str],
    candidate_paths: tuple[str, ...],
    fact_candidates: tuple[StagedFactCandidate, ...],
    spec_statuses: dict[str, str] | None,
    spec_activated_paths: tuple[str, ...] | None = None,
) -> list[CommitValidationIssue]:
    """Fail-closed mechanical block for new or activated independent spec docs.

    Per 00 §10.1 第 12 条 and 03 §13 第 9 条, a commit that adds a new
    independent spec document (``specs/<id>-*.md``), or activates an existing one
    (flips its ``status`` to ``active``), must carry a non-empty ``Human-Gate:``
    footer trailer recording the Human decision; otherwise the Git Gate fails
    closed.  Fact objects (Spark/WorkCase/ADR/Pitfall/Study) also live under
    ``specs/<id>-*.md`` but are excluded here: they are validated through the
    fact-trace layer instead and are never spec candidates.
    """

    issues: list[CommitValidationIssue] = []
    # Legacy callers and older tests that supply neither a staged status map nor
    # an activation set skip this check. The real Git Gate flow (git_adapter)
    # always supplies ``spec_candidate_statuses`` and ``spec_activated_paths``;
    # when both are absent we cannot tell a new/activated spec from a plain
    # modification, so we do not fail closed here. Fail-closed behaviour applies
    # when a status map is supplied but a candidate path is missing from it.
    if spec_statuses is None and not spec_activated_paths:
        return issues
    fact_paths = {candidate.path for candidate in fact_candidates}
    activates = set(spec_activated_paths or ())
    requires_gate = False
    for path in candidate_paths:
        if path in fact_paths:
            continue
        if not _SPEC_PATH_RE.match(path):
            continue
        status = spec_statuses.get(path) if spec_statuses else None
        is_new = False
        if spec_statuses is not None:
            # status "A" (added) or "C" (copied) means a new file; when the
            # staged status is missing from a supplied map the validator fails
            # closed and still requires the trailer, because it is side-effect
            # free and cannot read HEAD itself.
            if status is None:
                is_new = True
            elif status.startswith(("A", "C")):
                is_new = True
        if is_new or path in activates:
            requires_gate = True
            break
    if not requires_gate:
        return issues
    trailers = _footer_trailers(lines)
    values = trailers.get("Human-Gate", [])
    if not values or any(not value.strip() for value in values):
        issues.append(
            _issue(
                "human_gate_trailer_missing",
                "提交新增或激活独立 spec 文档（specs/<id>-*.md），footer 必须含非空 Human-Gate: "
                "trailer 指向 Human 决定；否则 Git Gate 机械阻断",
            )
        )
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
) -> tuple[list[CommitValidationIssue], list[CommitValidationIssue]]:
    """Validate the staged fact's append-only trace independently of commit signing.

    The commit validator is deliberately fail-closed when the before image is
    unavailable: an after image alone cannot distinguish newly written entries
    from read-only legacy history.
    """

    unavailable: list[CommitValidationIssue] = []
    failures: list[CommitValidationIssue] = []
    schemas = {schema.fact_type_key: schema for schema in value.fact_schemas}
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
        legacy_repair_metadata: dict[str, object] | None = None
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
                if before_checked.fields is None:
                    unavailable.append(
                        _issue("fact_trace_unverifiable", f"事实 HEAD before-image 不可机械消费: {candidate.path}")
                    )
                    continue
                legacy_repair_metadata, legacy_repair_issues = _legacy_invalid_signature_repair_metadata(
                    value.message,
                    candidate,
                    before_checked.issues,
                )
                if legacy_repair_issues:
                    failures.extend(legacy_repair_issues)
                    continue
                if legacy_repair_metadata is None:
                    unavailable.append(
                        _issue("fact_trace_unverifiable", f"事实 HEAD before-image 不可机械消费: {candidate.path}")
                    )
                    continue
                if len(value.fact_candidates) != 1:
                    failures.append(
                        _issue(
                            "legacy_signature_repair_object_scope_invalid",
                            "legacy 修复提交必须只包含一个指定事实对象",
                        )
                    )
                    continue
                before_fields = before_checked.fields
            else:
                before_fields = before_checked.fields
            if before_fields is None:
                unavailable.append(
                    _issue("fact_trace_unverifiable", f"事实 HEAD before-image 不可机械消费: {candidate.path}")
                )
                continue
        after_log = after_checked.fields.get("change_log")
        before_log = None if before_fields is None else before_fields.get("change_log")
        if not isinstance(after_log, list):
            failures.append(_issue("fact_trace_missing", f"事实候选缺少可校验 change_log: {candidate.path}"))
            continue
        if before_fields is None:
            # A fact may be created and then legitimately progressed several
            # times before its first Git commit.  All of that uncommitted
            # history belongs to this candidate, so validate every entry as a
            # newly written trace rather than incorrectly requiring one entry.
            appended = after_log
        elif isinstance(before_log, list) and after_log[: len(before_log)] == before_log:
            appended = after_log[len(before_log) :]
        elif before_log is None:
            # Legacy migration: the HEAD snapshot predates the change-log
            # mechanism and has no history.  The first trusted entry was
            # established by the controlled migration operation, so the whole
            # current log is the event introduced by this candidate.
            appended = after_log
        elif legacy_repair_metadata is not None:
            # The narrow legacy exception may consume several already-created
            # repair audit entries, but only after the footer names every
            # signature diff exactly.  The dedicated transition checker below
            # rejects any non-audit or non-signature change.
            appended = after_log[len(before_log) :]
        elif _is_historical_signature_repair_transition(before_log, after_log):
            # Historical signature repair is a controlled exception to the
            # append-only comparison: the old signature values may change, but
            # the object body and every non-signature field must remain equal,
            # and exactly one canonical repair audit entry must be appended.
            appended = [after_log[-1]]
        else:
            failures.append(
                _issue("fact_trace_transition_invalid", f"事实流水前后像不能确定唯一新增事件: {candidate.path}")
            )
            continue
        if legacy_repair_metadata is not None:
            failures.extend(
                _legacy_invalid_signature_repair_transition_issues(
                    candidate,
                    before_fields,
                    after_checked.fields,
                    legacy_repair_metadata,
                )
            )
            if failures and failures[-1].code.startswith("legacy_signature_repair_"):
                continue
        if not appended or not all(isinstance(entry, dict) for entry in appended):
            requirement = "至少含一条初始流水" if before_fields is None else "恰新增一条流水"
            failures.append(_issue("fact_trace_append_invalid", f"事实候选必须{requirement}: {candidate.path}"))
            continue
        if any(
            isinstance(entry.get("signature"), dict)
            and set(entry["signature"])
            in ({"agent_id", "host_environment"}, {"model_id", "host_name"})
            for entry in appended
        ):
            failures.append(
                _issue(
                    "legacy_signature_write_retired",
                    "事实新增流水不得使用 agent_id/host_environment 或 model_id/host_name 历史形状；"
                    f"新写入必须使用 model_id/agent_workbench: {candidate.path}",
                )
            )
            continue
    return unavailable, failures


def _legacy_invalid_signature_repair_metadata(
    message: str | None,
    candidate: StagedFactCandidate,
    before_issues: tuple[object, ...],
) -> tuple[dict[str, object] | None, list[CommitValidationIssue]]:
    """Parse the deliberately narrow commit exception for invalid legacy before-images."""

    if message is None or candidate.head_data is None or candidate.object_id is None:
        return None, []
    signature_issues = [
        issue
        for issue in before_issues
        if getattr(issue, "field_path", None) is not None
        and _LEGACY_REPAIR_FIELD.fullmatch(getattr(issue, "field_path")) is not None
        and "单 token" in getattr(issue, "summary", "")
    ]
    if len(signature_issues) != len(before_issues) or not signature_issues:
        return None, []
    _, lines = _normalize_message(message)
    trailers = _footer_trailers(lines[1:])
    names = (
        "Legacy-Repair-Object",
        "Legacy-Repair-Fingerprint",
        "Legacy-Repair-Field",
        "Legacy-Repair-Old",
        "Legacy-Repair-New",
        "Human-Gate",
    )
    if any(name.startswith("Legacy-Repair-") for name in trailers):
        missing = [name for name in names if name not in trailers]
        if missing:
            return None, [
                _issue("legacy_signature_repair_metadata_missing", f"legacy 修复缺少受控元数据: {', '.join(missing)}")
            ]
    else:
        return None, []
    issues: list[CommitValidationIssue] = []
    if trailers["Legacy-Repair-Object"] != [candidate.object_id]:
        issues.append(_issue("legacy_signature_repair_object_mismatch", "legacy 修复对象必须精确匹配唯一事实候选"))
    fingerprint = trailers["Legacy-Repair-Fingerprint"]
    if len(fingerprint) != 1 or _SHA256.fullmatch(fingerprint[0]) is None:
        issues.append(_issue("legacy_signature_repair_fingerprint_invalid", "legacy 修复必须提供一个小写 SHA-256 指纹"))
    elif fingerprint[0] != hashlib.sha256(candidate.head_data).hexdigest():
        issues.append(_issue("legacy_signature_repair_fingerprint_mismatch", "legacy 修复指纹不匹配 HEAD before-image"))
    fields = trailers["Legacy-Repair-Field"]
    olds = trailers["Legacy-Repair-Old"]
    news = trailers["Legacy-Repair-New"]
    if not fields or len(fields) != len(olds) or len(fields) != len(news):
        issues.append(_issue("legacy_signature_repair_fields_mismatch", "legacy 修复的 Field、Old、New 必须按条目一一对应"))
    if len(trailers["Human-Gate"]) != 1 or not trailers["Human-Gate"][0].strip():
        issues.append(_issue("legacy_signature_repair_human_gate_missing", "legacy 修复必须带非空 Human-Gate 授权"))
    repairs: list[tuple[int, str, str, str]] = []
    for field, old, new in zip(fields, olds, news):
        match = _LEGACY_REPAIR_FIELD.fullmatch(field)
        field_name = None if match is None else match.group("field")
        if (
            match is None
            or field_name is None
            or not old
            or not new
            or (field_name == "agent_workbench" and _WORKBENCH_TOKEN_SPLIT.search(new.strip()))
        ):
            issues.append(_issue("legacy_signature_repair_field_invalid", "legacy 修复字段必须是允许署名字段的精确索引和值"))
            continue
        repairs.append((int(match.group("index")), field_name, old, new))
    if len({(index, field) for index, field, _, _ in repairs}) != len(repairs):
        issues.append(_issue("legacy_signature_repair_field_duplicate", "legacy 修复索引不得重复"))
    if issues:
        return None, issues
    return {"repairs": tuple(repairs)}, []


def _legacy_invalid_signature_repair_transition_issues(
    candidate: StagedFactCandidate,
    before_fields: dict[str, object],
    after_fields: dict[str, object],
    metadata: dict[str, object],
) -> list[CommitValidationIssue]:
    """Enforce exact object, signature-only semantic diff and one audit append."""

    before_log = before_fields.get("change_log")
    after_log = after_fields.get("change_log")
    repairs = metadata["repairs"]
    assert isinstance(before_log, list) and isinstance(after_log, list)
    assert isinstance(repairs, tuple)
    issues: list[CommitValidationIssue] = []
    if len(after_log) <= len(before_log):
        issues.append(_issue("legacy_signature_repair_transition_invalid", f"legacy 修复必须追加至少一条受控历史署名审计流水: {candidate.path}"))
        return issues
    appended = after_log[len(before_log) :]
    if not all(_is_canonical_signature_repair_audit(entry) for entry in appended):
        issues.append(_issue("legacy_signature_repair_transition_invalid", f"legacy 修复只能追加 canonical 署名审计流水: {candidate.path}"))
        return issues
    if not all(isinstance(entry, dict) for entry in before_log + appended):
        issues.append(_issue("legacy_signature_repair_transition_invalid", f"legacy 修复流水必须保持对象条目: {candidate.path}"))
        return issues
    for before, after in zip(before_log, after_log[: len(before_log)]):
        assert isinstance(before, dict) and isinstance(after, dict)
        if {key: value for key, value in before.items() if key != "signature"} != {
            key: value for key, value in after.items() if key != "signature"
        }:
            issues.append(_issue("legacy_signature_repair_non_signature_change", f"legacy 修复历史条目除署名外不得有其它差异: {candidate.path}"))
            break
    if {key: value for key, value in before_fields.items() if key not in {"change_log", "updated_at"}} != {
        key: value for key, value in after_fields.items() if key not in {"change_log", "updated_at"}
    }:
        issues.append(_issue("legacy_signature_repair_non_signature_change", f"legacy 修复除署名与 updated_at 外不得有其它差异: {candidate.path}"))
    audit = after_log[-1]
    if not isinstance(audit, dict) or audit.get("at") != after_fields.get("updated_at"):
        issues.append(_issue("legacy_signature_repair_audit_time_invalid", "legacy 修复审计流水 at 必须等于 after.updated_at"))
    expected = {(index, field, old, new) for index, field, old, new in repairs}
    actual: set[tuple[int, str, object, object]] = set()
    for index, (before, after) in enumerate(zip(before_log, after_log[:-1])):
        if not isinstance(before, dict) or not isinstance(after, dict):
            continue
        before_signature = before.get("signature")
        after_signature = after.get("signature")
        if isinstance(before_signature, dict) and isinstance(after_signature, dict):
            for key in set(before_signature) | set(after_signature):
                if before_signature.get(key) != after_signature.get(key):
                    actual.add((index, key, before_signature.get(key), after_signature.get(key)))
    if actual != expected:
        issues.append(_issue("legacy_signature_repair_fields_mismatch", "legacy 修复声明的旧值/新值必须与实际全部署名差异完全一致"))
    return issues


def _is_canonical_signature_repair_audit(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    summary = entry.get("summary")
    signature = entry.get("signature")
    return (
        isinstance(summary, str)
        and summary.startswith("受控更正历史 change_log 中的 agent_workbench 格式；修复项为")
        and "原始错误值已由本次更正覆盖并保留本条修复记录。" in summary
        and isinstance(signature, dict)
        and set(signature) == {"model_id", "agent_workbench"}
    )


def _is_historical_signature_repair_transition(
    before_log: list[object], after_log: list[object]
) -> bool:
    """Recognize one controlled historical-signature repair event.

    The repair operation updates signature values in existing entries and
    appends one canonical audit entry.  This shape is distinct from ordinary
    fact updates and is safe to accept mechanically only when all other fields
    remain unchanged.
    """

    if len(after_log) != len(before_log) + 1:
        return False
    audit = after_log[-1]
    if not isinstance(audit, dict):
        return False
    summary = audit.get("summary")
    signature = audit.get("signature")
    if (
        not isinstance(summary, str)
        or not summary.startswith("受控更正历史 change_log 中的 agent_workbench 格式；修复项为")
        or "原始错误值已由本次更正覆盖并保留本条修复记录。" not in summary
        or not isinstance(signature, dict)
        or set(signature) != {"model_id", "agent_workbench"}
    ):
        return False

    changed_signature = False
    for before, after in zip(before_log, after_log[:-1]):
        if not isinstance(before, dict) or not isinstance(after, dict):
            return False
        before_rest = {key: value for key, value in before.items() if key != "signature"}
        after_rest = {key: value for key, value in after.items() if key != "signature"}
        if before_rest != after_rest:
            return False
        before_signature = before.get("signature")
        after_signature = after.get("signature")
        if not isinstance(before_signature, dict) or not isinstance(after_signature, dict):
            return False
        shape_changed = (
            (
                set(before_signature) == {"agent_id", "host_environment"}
                and set(after_signature) == {"model_id", "agent_workbench"}
            )
            or (
                set(before_signature) == {"model_id", "host_name"}
                and set(after_signature) == {"model_id", "agent_workbench"}
            )
        )
        if set(before_signature) != set(after_signature) and not shape_changed:
            return False
        if set(before_signature) - {"agent_id", "model_id", "agent_workbench", "host_environment", "host_name"}:
            return False
        changed_signature = changed_signature or before_signature != after_signature
    return changed_signature


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
    body_lines: list[str] = []
    content_body_lines: list[str] = []
    match: re.Match[str] | None = None
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
            description = match.group("description")
            if commit_type not in contract.type_tokens:
                failures.append(_issue("type_unknown", f"未知 type: {commit_type}"))
            if scope is not None and scope not in contract.scope_tokens:
                failures.append(_issue("scope_unknown", f"未知 scope: {scope}"))
            if _CJK.search(description) is None:
                failures.append(_issue("description_cjk_missing", "description 至少需要一个 CJK 字符"))
            if description.endswith(("。", ".")):
                failures.append(_issue("description_period", "description 不使用句号结尾"))
    if lines and normalized:
        minimum_body_required = "all-commits-minimum-body" in contract.mechanical_triggers
        impact_boundary_required = (
            match is not None
            and match.group("breaking") is not None
            and "breaking-marker" in contract.mechanical_triggers
        )
        if minimum_body_required and body is None:
            failures.append(_issue("body_required", "所有受管辖提交都必须具有最低 body"))
        failures.extend(
            _body_structure_issues(
                content_body_lines,
                require_minimum_body=minimum_body_required,
                require_impact_boundary=impact_boundary_required,
            )
        )
        signature_issues = _signature_trailer_issues(body_lines)
        failures.extend(signature_issues)
        if not signature_issues:
            trace_unavailable, trace_failures = _fact_trace_issues(value)
            unavailable.extend(trace_unavailable)
            failures.extend(trace_failures)
        failures.extend(
            _human_gate_trailer_issues(
                body_lines,
                value.candidate_paths,
                value.fact_candidates,
                value.spec_candidate_statuses,
                value.spec_activated_paths,
            )
        )
        failures.extend(_platform_affected_issues(value.candidate_paths, _footer_trailers(body_lines)))
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
