"""Read-only Git adapter for binding a real Index snapshot to commit validation."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.validation import (
    _SPEC_PATH_RE,
    CommitValidationInput,
    StagedFactCandidate,
)
from ldvh.facts.content import MAX_FACT_BYTES
from ldvh.facts.contracts import LAYOUTS
from ldvh.governance.git import isolated_git_environment, resolve_git_identity, windows_path_problem
from ldvh.governance.models import GovernanceScopeResult, ObjectStatus, ScopeStatus

_GIT_TIMEOUT_SECONDS = 10
_UNBORN_HEAD = b"UNBORN\0"
ObservationStage = Literal["governance", "identity", "git_process", "git_output", "candidate", "drift"]


@dataclass(frozen=True, slots=True)
class CommitCandidateObservationIssue:
    stage: ObservationStage
    message: str


@dataclass(frozen=True, slots=True)
class CommitCandidateObservation:
    outcome: Literal["observed", "unverifiable", "drifted"]
    validation_input: CommitValidationInput | None
    issues: tuple[CommitCandidateObservationIssue, ...]
    candidate_paths: tuple[str, ...]
    snapshot_identity: str | None
    fact_candidates: tuple[StagedFactCandidate, ...] = ()


@dataclass(frozen=True, slots=True)
class _GitResult:
    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True, slots=True)
class _IndexEntry:
    mode: str
    oid: str
    stage: str


def _issue(stage: ObservationStage, message: str) -> CommitCandidateObservationIssue:
    return CommitCandidateObservationIssue(stage, message)


def _run_git(
    worktree: Path,
    arguments: tuple[str, ...],
    *,
    index_file: Path | None = None,
) -> _GitResult | CommitCandidateObservationIssue:
    path_problem = windows_path_problem(worktree)
    if path_problem is None and index_file is not None:
        path_problem = windows_path_problem(index_file)
    if path_problem is not None:
        return _issue("git_process", f"Git path is unsupported on Windows: {path_problem}")
    environment = isolated_git_environment()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    if index_file is not None:
        environment["GIT_INDEX_FILE"] = str(index_file)
    try:
        completed = subprocess.run(
            ("git", "--no-optional-locks", "-C", str(worktree), *arguments),
            check=False,
            capture_output=True,
            env=environment,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        return _issue("git_process", f"Git executable is unavailable: {error}")
    except OSError as error:
        return _issue("git_process", f"Git process could not be started: {error}")
    except subprocess.TimeoutExpired:
        return _issue("git_process", f"Git read exceeded {_GIT_TIMEOUT_SECONDS} seconds")
    return _GitResult(completed.returncode, completed.stdout, completed.stderr)


def _successful(
    result: _GitResult | CommitCandidateObservationIssue,
    stage: str,
) -> bytes | CommitCandidateObservationIssue:
    if isinstance(result, CommitCandidateObservationIssue):
        return result
    if result.returncode != 0:
        details = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        return _issue("git_process", f"Git {stage} read failed: {details or result.returncode}")
    return result.stdout


def _snapshot(
    worktree: Path,
    *,
    index_file: Path | None = None,
) -> tuple[str, bytes, CommitCandidateObservationIssue | None]:
    head_result = _run_git(worktree, ("rev-parse", "--verify", "-q", "HEAD^{commit}"))
    if isinstance(head_result, CommitCandidateObservationIssue):
        return "", b"", head_result
    if head_result.returncode == 0:
        head = head_result.stdout.strip() + b"\0"
    elif head_result.returncode == 1 and not head_result.stdout and not head_result.stderr:
        head = _UNBORN_HEAD
    else:
        details = (head_result.stderr or head_result.stdout).decode("utf-8", errors="replace").strip()
        return "", b"", _issue("git_process", f"Git HEAD commit read failed: {details or head_result.returncode}")
    index = _successful(
        _run_git(worktree, ("ls-files", "--stage", "-z"), index_file=index_file),
        "Index",
    )
    if isinstance(index, CommitCandidateObservationIssue):
        return "", b"", index
    return f"sha256:{hashlib.sha256(head + index).hexdigest()}", index, None


def _index_blob_map(
    index: bytes,
) -> tuple[dict[str, tuple[_IndexEntry, ...]], CommitCandidateObservationIssue | None]:
    """Parse ``ls-files --stage -z`` bytes without discarding mode or conflict stages."""

    try:
        entries = index.decode("utf-8").split("\0")
    except UnicodeDecodeError:
        return {}, _issue("git_output", "Git Index listing is not valid UTF-8")
    mutable: dict[str, list[_IndexEntry]] = {}
    for entry in entries:
        if not entry:
            continue
        meta, separator, path = entry.partition("\t")
        if not separator or not path:
            return {}, _issue("git_output", "Git returned malformed Index stage listing")
        parts = meta.split(" ")
        if len(parts) != 3 or not all(parts):
            return {}, _issue("git_output", "Git returned malformed Index stage metadata")
        mutable.setdefault(path, []).append(_IndexEntry(parts[0], parts[1], parts[2]))
    return {path: tuple(entries) for path, entries in mutable.items()}, None


def _classify_fact_path(path: str) -> tuple[str, str | None] | None:
    """Return ``(fact_type_key, object_id|None)`` for an in-layout path.

    ``object_id`` is ``None`` when the file name cannot parse into the layout's
    legal object_id shape; paths outside every fact layout return ``None``.
    """

    for layout in LAYOUTS.values():
        prefix = f"{layout.directory}/"
        if not path.startswith(prefix) or not path.endswith(layout.suffix):
            continue
        object_id = path[len(prefix) : -len(layout.suffix)]
        if not object_id or "/" in object_id:
            return None
        if layout.object_id_pattern.fullmatch(object_id) is None:
            return layout.fact_type_key, None
        return layout.fact_type_key, object_id
    return None


def _read_staged_blob(
    worktree: Path,
    oid: str,
    *,
    index_file: Path | None = None,
    max_bytes: int = MAX_FACT_BYTES,
) -> tuple[bytes | None, str | None]:
    """Read one content-addressed blob from the bound Index observation."""

    size = _successful(
        _run_git(worktree, ("cat-file", "-s", oid), index_file=index_file),
        "staged blob size",
    )
    if isinstance(size, CommitCandidateObservationIssue):
        return None, size.message
    try:
        byte_count = int(size.strip())
    except ValueError:
        return None, "Git returned a non-numeric staged blob size"
    if byte_count > max_bytes:
        return None, f"暂存内容超过 {max_bytes} bytes 读取预算"
    content = _successful(
        _run_git(worktree, ("cat-file", "blob", oid), index_file=index_file),
        "staged blob",
    )
    if isinstance(content, CommitCandidateObservationIssue):
        return None, content.message
    return content, None


def _head_blob(
    worktree: Path,
    path: str,
    *,
    index_file: Path | None = None,
    max_bytes: int,
) -> tuple[bytes | None, str | None, str | None]:
    listing = _successful(
        _run_git(worktree, ("ls-tree", "-z", "HEAD", "--", path), index_file=index_file),
        "HEAD blob listing",
    )
    if isinstance(listing, CommitCandidateObservationIssue):
        return None, None, listing.message
    entries = tuple(item for item in listing.split(b"\0") if item)
    if not entries:
        # An unborn HEAD or a newly created fact has no before image.  This is
        # observable, not an adapter failure; callers keep the explicit
        # ``head_exists`` bit instead of guessing from a missing blob.
        return None, None, None
    if len(entries) != 1:
        return None, None, "HEAD path did not resolve to exactly one entry"
    meta, separator, observed_path = entries[0].partition(b"\t")
    parts = meta.split(b" ")
    if separator != b"\t" or len(parts) != 3 or parts[0] not in {b"100644", b"100755"} or parts[1] != b"blob":
        return None, None, "HEAD path is not a Git regular-file blob"
    try:
        decoded_path = observed_path.decode("utf-8")
        oid = parts[2].decode("ascii")
    except UnicodeDecodeError:
        return None, None, "HEAD path or object id is not decodable"
    if decoded_path != path:
        return None, None, "HEAD blob path identity changed"
    data, problem = _read_staged_blob(worktree, oid, index_file=index_file, max_bytes=max_bytes)
    return data, oid, problem


def read_head_regular_file(
    worktree: Path,
    path: str,
    *,
    max_bytes: int = MAX_FACT_BYTES,
) -> tuple[bytes | None, str | None, str | None]:
    """Read one regular-file blob from HEAD without consulting the Index."""

    return _head_blob(worktree, path, max_bytes=max_bytes)


def _fact_candidates(
    worktree: Path,
    paths: tuple[str, ...],
    index: bytes,
    *,
    index_file: Path | None = None,
) -> tuple[tuple[StagedFactCandidate, ...], CommitCandidateObservationIssue | None]:
    """Observe all staged single-file fact candidates from the bound Index."""

    classified = [(path, _classify_fact_path(path)) for path in paths]
    if not any(target is not None for _, target in classified):
        return (), None
    mapping, failure = _index_blob_map(index)
    if failure is not None:
        return (), failure
    candidates: list[StagedFactCandidate] = []
    for path, target in classified:
        if target is None:
            continue
        fact_type_key, object_id = target
        entries = mapping.get(path)
        if entries is None:
            continue
        if object_id is None:
            candidates.append(StagedFactCandidate(path, fact_type_key, None, None, None))
            continue
        if len(entries) != 1 or entries[0].stage != "0":
            candidates.append(
                StagedFactCandidate(
                    path,
                    fact_type_key,
                    object_id,
                    None,
                    "暂存路径包含未解决的 Index stage",
                )
            )
            continue
        data, problem = _read_staged_blob(worktree, entries[0].oid, index_file=index_file)
        head_data, head_oid, head_problem = _head_blob(
            worktree,
            path,
            index_file=index_file,
            max_bytes=MAX_FACT_BYTES,
        )
        candidates.append(
            StagedFactCandidate(
                path,
                fact_type_key,
                object_id,
                data,
                problem,
                head_data=head_data,
                head_exists=head_oid is not None,
                head_observation_issue=head_problem,
            )
        )
    return tuple(candidates), None


def _candidate_paths(
    worktree: Path,
    *,
    index_file: Path | None = None,
) -> tuple[tuple[str, ...], CommitCandidateObservationIssue | None]:
    output = _successful(
        _run_git(
            worktree,
            ("diff", "--cached", "--name-status", "-z", "--find-renames", "--find-copies", "--no-ext-diff"),
            index_file=index_file,
        ),
        "staged candidate",
    )
    if isinstance(output, CommitCandidateObservationIssue):
        return (), output
    return _parse_name_status(output)


def _parse_name_status(output: bytes) -> tuple[tuple[str, ...], CommitCandidateObservationIssue | None]:
    try:
        tokens = output.decode("utf-8").split("\0")
    except UnicodeDecodeError:
        return (), _issue("git_output", "Git candidate paths are not valid UTF-8")
    if tokens and tokens[-1] == "":
        tokens.pop()
    paths: list[str] = []
    seen_paths: set[str] = set()
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        if not status or index + path_count > len(tokens):
            return (), _issue("git_output", "Git returned malformed staged name-status output")
        observed = tokens[index : index + path_count]
        if any(not path for path in observed):
            return (), _issue("git_output", "Git returned an empty staged path")
        for path in observed:
            if path not in seen_paths:
                paths.append(path)
                seen_paths.add(path)
        index += path_count
    return tuple(paths), None


def _candidate_status_map(
    worktree: Path,
    *,
    index_file: Path | None = None,
) -> tuple[dict[str, str], CommitCandidateObservationIssue | None]:
    """Map each staged path to its git name-status (A/M/R/C/D...).

    Used by the Human Gate enforcement to distinguish a newly added spec
    document from an edit to an existing one, without the side-effect-free
    validator reading Git itself.
    """

    output = _successful(
        _run_git(
            worktree,
            ("diff", "--cached", "--name-status", "-z", "--find-renames", "--find-copies", "--no-ext-diff"),
            index_file=index_file,
        ),
        "staged candidate status",
    )
    if isinstance(output, CommitCandidateObservationIssue):
        return {}, output
    return _parse_name_status_map(output), None


def _parse_name_status_map(output: bytes) -> dict[str, str]:
    try:
        tokens = output.decode("utf-8").split("\0")
    except UnicodeDecodeError:
        return {}
    if tokens and tokens[-1] == "":
        tokens.pop()
    status_map: dict[str, str] = {}
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        if not status or index + path_count > len(tokens):
            return {}
        observed = tokens[index : index + path_count]
        index += path_count
        # For renames/copies the last path is the path now staged.
        resulting = observed[-1]
        status_map.setdefault(resulting, status)
    return status_map


def _parse_front_matter_status(text: bytes) -> str | None:
    """Extract the ``status`` field from a spec's YAML front matter."""
    try:
        decoded = text.decode("utf-8")
    except UnicodeDecodeError:
        return None
    match = re.search(r"```yaml\s*\n(.*?)```", decoded, re.DOTALL)
    block = match.group(1) if match else decoded
    status_match = re.search(r"^\s*status:\s*[\"']?([^\"'\n]+)[\"']?", block, re.MULTILINE)
    if not status_match:
        return None
    return status_match.group(1).strip().lower()


def _detect_activations(
    worktree: Path,
    paths: tuple[str, ...],
    fact_paths: set[str],
    *,
    index_file: Path | None = None,
) -> tuple[tuple[str, ...], CommitCandidateObservationIssue | None]:
    """Return spec paths whose ``status`` is being flipped to ``active``.

    Per 00 §10.1 第 12 条 and 03 §13 第 9 条, activating an existing independent
    spec document (flipping its ``status`` to ``active``) is a Human Gate event
    and must carry a ``Human-Gate:`` trailer, just like adding a new spec. This
    compares the staged blob (index) against HEAD for each non-fact spec path.

    A flip from any non-``active`` status (including a status absent from HEAD)
    to ``active`` is reported. A spec that is not yet in HEAD is a new file and
    is handled by the new-spec status check instead, so it is not reported here.
    If the staged blob cannot be read, the path is reported fail-closed.
    """

    activations: list[str] = []
    failure: CommitCandidateObservationIssue | None = None
    for path in paths:
        if path in fact_paths:
            continue
        if not _SPEC_PATH_RE.match(path):
            continue
        staged = _successful(_run_git(worktree, ("show", f":{path}"), index_file=index_file), "staged spec status")
        if isinstance(staged, CommitCandidateObservationIssue):
            failure = staged
            activations.append(path)
            continue
        staged_status = _parse_front_matter_status(staged)
        head = _successful(_run_git(worktree, ("show", f"HEAD:{path}"), index_file=index_file), "head spec status")
        if isinstance(head, CommitCandidateObservationIssue):
            # Not in HEAD (new file) or unreadable: activation does not apply
            # here, and a genuine read failure is already captured above for the
            # staged side; skip rather than misreport.
            continue
        head_status = _parse_front_matter_status(head)
        if staged_status == "active" and head_status != "active":
            activations.append(path)
    return tuple(activations), failure


def _governance_identity(governance: GovernanceScopeResult) -> str:
    encoded = json.dumps(governance.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _observe_index(
    *,
    worktree: Path,
    message: str | None,
    contract: CommitContractProjection,
    governance: GovernanceScopeResult,
    index_file: Path | None = None,
) -> CommitCandidateObservation:
    snapshot_before, index_before, failure = _snapshot(worktree, index_file=index_file)
    if failure is not None:
        return CommitCandidateObservation("unverifiable", None, (failure,), (), None)
    paths, failure = (
        _candidate_paths(worktree) if index_file is None else _candidate_paths(worktree, index_file=index_file)
    )
    if failure is not None:
        return CommitCandidateObservation("unverifiable", None, (failure,), (), snapshot_before)
    status_map, status_failure = (
        _candidate_status_map(worktree)
        if index_file is None
        else _candidate_status_map(worktree, index_file=index_file)
    )
    if status_failure is not None:
        status_map = {}
    fact_candidates, failure = _fact_candidates(
        worktree,
        paths,
        index_before,
        index_file=index_file,
    )
    if failure is not None:
        return CommitCandidateObservation("unverifiable", None, (failure,), paths, snapshot_before)
    fact_paths = {candidate.path for candidate in fact_candidates}
    activations, _ = _detect_activations(worktree, paths, fact_paths, index_file=index_file)
    snapshot_after, _, failure = _snapshot(worktree, index_file=index_file)
    if failure is not None:
        return CommitCandidateObservation("unverifiable", None, (failure,), paths, snapshot_before)
    if snapshot_before != snapshot_after:
        issue = _issue("drift", "Index or HEAD changed while the candidate was being observed")
        return CommitCandidateObservation("drifted", None, (issue,), paths, snapshot_after)

    value = CommitValidationInput(
        message=message,
        candidate_paths=paths,
        spec_candidate_statuses=status_map,
        spec_activated_paths=activations,
        git_worktree_root=str(worktree),
        governance_status=governance.scope_status.value,
        governance_identity=_governance_identity(governance),
        snapshot_identity=snapshot_after,
        source_path=contract.source_path,
        source_fingerprint=contract.content_fingerprint,
        fact_candidates=fact_candidates,
    )
    return CommitCandidateObservation(
        "observed",
        value,
        (),
        paths,
        snapshot_after,
        fact_candidates,
    )


def observe_commit_candidate(
    *,
    locator: str,
    base: str | Path,
    message: str | None,
    contract: CommitContractProjection,
    governance: GovernanceScopeResult,
    index_file: Path | None = None,
) -> CommitCandidateObservation:
    """Observe one real governed worktree without modifying Git or project files.

    ``index_file`` is only for a caller that already received the active Index
    path from Git itself (for example, a native ``commit-msg`` hook or the
    internal temporary-index commit executor). It is never taken from ambient
    process state here.
    """

    if governance.scope_status is not ScopeStatus.GOVERNED_SINGLE or len(governance.object_resolutions) != 1:
        issue = _issue("governance", "Adapter requires one governed_single object resolution")
        return CommitCandidateObservation("unverifiable", None, (issue,), (), None)
    resolution = governance.object_resolutions[0]
    if resolution.status is not ObjectStatus.GOVERNED or resolution.git_worktree_root is None:
        issue = _issue("governance", "Governance result does not identify one governed worktree")
        return CommitCandidateObservation("unverifiable", None, (issue,), (), None)
    path_problem = windows_path_problem(resolution.git_worktree_root)
    if path_problem is not None:
        issue = _issue("identity", f"Governance worktree path is unsupported on Windows: {path_problem}")
        return CommitCandidateObservation("unverifiable", None, (issue,), (), None)

    git_identity = resolve_git_identity(locator, base=base)
    if git_identity.status != "git_worktree" or git_identity.identity is None:
        detail = git_identity.failure.summary if git_identity.failure is not None else git_identity.non_worktree_reason
        issue = _issue("identity", f"Target Git worktree identity is unavailable: {detail}")
        return CommitCandidateObservation("unverifiable", None, (issue,), (), None)
    worktree = git_identity.identity.worktree_root
    if worktree != Path(resolution.git_worktree_root).resolve():
        issue = _issue("governance", "Observed worktree does not match the governance result")
        return CommitCandidateObservation("unverifiable", None, (issue,), (), None)

    return _observe_index(
        worktree=worktree,
        message=message,
        contract=contract,
        governance=governance,
        index_file=index_file,
    )


__all__ = ["CommitCandidateObservation", "CommitCandidateObservationIssue", "observe_commit_candidate"]
