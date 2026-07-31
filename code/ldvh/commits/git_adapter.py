"""Read-only Git adapter for binding a real Index snapshot to commit validation."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.commits.contract_source import CommitContractProjection
from ldvh.commits.validation import (
    CommitValidationInput,
    StagedFactCandidate,
    StagedFileAssetCandidate,
)
from ldvh.facts.content import MAX_FACT_BYTES
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.file_asset import DEFAULT_MANIFEST_BUDGET, DEFAULT_PAYLOAD_BUDGET
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
    file_asset_candidates: tuple[StagedFileAssetCandidate, ...] = ()


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
    head_result = _run_git(worktree, ("rev-parse", "--verify", "-q", "HEAD^{tree}"))
    if isinstance(head_result, CommitCandidateObservationIssue):
        return "", b"", head_result
    if head_result.returncode == 0:
        head = head_result.stdout.strip() + b"\0"
    elif head_result.returncode == 1 and not head_result.stdout and not head_result.stderr:
        head = _UNBORN_HEAD
    else:
        details = (head_result.stderr or head_result.stdout).decode("utf-8", errors="replace").strip()
        return "", b"", _issue("git_process", f"Git HEAD tree read failed: {details or head_result.returncode}")
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

    file_asset_layout = LAYOUTS["file-asset"]
    file_asset_prefix = f"{file_asset_layout.directory}/"
    if path == file_asset_layout.directory:
        return "file-asset", None
    if path.startswith(file_asset_prefix):
        remainder = path[len(file_asset_prefix) :]
        object_id, separator, _member_path = remainder.partition("/")
        if (
            not separator
            or not object_id
            or file_asset_layout.object_id_pattern.fullmatch(object_id) is None
        ):
            return "file-asset", None
        return "file-asset", object_id

    for layout in LAYOUTS.values():
        if layout.carrier == "file-asset-directory":
            continue
        prefix = f"{layout.directory}/"
        assert layout.suffix is not None
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


def _head_file_asset_paths(
    worktree: Path,
    *,
    index_file: Path | None = None,
) -> tuple[tuple[str, ...], CommitCandidateObservationIssue | None]:
    head = _run_git(worktree, ("rev-parse", "--verify", "-q", "HEAD^{tree}"), index_file=index_file)
    if isinstance(head, CommitCandidateObservationIssue):
        return (), head
    if head.returncode == 1 and not head.stdout and not head.stderr:
        return (), None
    if head.returncode != 0:
        details = (head.stderr or head.stdout).decode("utf-8", errors="replace").strip()
        return (), _issue("git_process", f"Git HEAD tree read failed: {details or head.returncode}")
    observed = _successful(
        _run_git(
            worktree,
            ("ls-tree", "-r", "--name-only", "-z", "HEAD", "--", LAYOUTS["file-asset"].directory),
            index_file=index_file,
        ),
        "HEAD FileAsset tree",
    )
    if isinstance(observed, CommitCandidateObservationIssue):
        return (), observed
    try:
        return tuple(path for path in observed.decode("utf-8").split("\0") if path), None
    except UnicodeDecodeError:
        return (), _issue("git_output", "Git HEAD FileAsset listing is not valid UTF-8")


def _fact_candidates(
    worktree: Path,
    paths: tuple[str, ...],
    index: bytes,
    *,
    index_file: Path | None = None,
) -> tuple[
    tuple[StagedFactCandidate, ...],
    tuple[StagedFileAssetCandidate, ...],
    CommitCandidateObservationIssue | None,
]:
    """Observe single-file blobs and aggregate complete FileAsset after-images."""

    classified = [(path, _classify_fact_path(path)) for path in paths]
    if not any(target is not None for _, target in classified):
        return (), (), None
    mapping, failure = _index_blob_map(index)
    if failure is not None:
        return (), (), failure
    candidates: list[StagedFactCandidate] = []
    file_asset_paths: dict[str, list[str]] = {}
    malformed_file_asset_paths: list[str] = []
    for path, target in classified:
        if target is None:
            continue
        fact_type_key, object_id = target
        if fact_type_key == "file-asset":
            if object_id is None:
                malformed_file_asset_paths.append(path)
            else:
                file_asset_paths.setdefault(object_id, []).append(path)
            continue
        entries = mapping.get(path)
        if entries is None:
            continue
        if object_id is None:
            candidates.append(StagedFactCandidate(path, fact_type_key, None, None, None))
            continue
        if len(entries) != 1 or entries[0].stage != "0":
            candidates.append(
                StagedFactCandidate(path, fact_type_key, object_id, None, "暂存路径包含未解决的 Index stage")
            )
            continue
        data, problem = _read_staged_blob(worktree, entries[0].oid, index_file=index_file)
        candidates.append(StagedFactCandidate(path, fact_type_key, object_id, data, problem))

    file_assets: list[StagedFileAssetCandidate] = []
    if malformed_file_asset_paths:
        file_assets.append(
            StagedFileAssetCandidate(
                None,
                tuple(sorted(malformed_file_asset_paths)),
                (),
                None,
                None,
                False,
                validation_issue="路径未形成合法 FileAsset 对象目录和固定成员",
            )
        )
    if file_asset_paths:
        head_paths, failure = _head_file_asset_paths(worktree, index_file=index_file)
        if failure is not None:
            return (), (), failure
        layout = LAYOUTS["file-asset"]
        for object_id, changed_paths in sorted(file_asset_paths.items()):
            object_prefix = f"{layout.canonical_path(object_id)}/"
            after_paths = sorted(path for path in mapping if path.startswith(object_prefix))
            member_names = tuple(path[len(object_prefix) :] for path in after_paths)
            observation_problems: list[str] = []
            validation_problems: list[str] = []
            manifest_data: bytes | None = None
            payload_data: bytes | None = None
            for path, member_name in zip(after_paths, member_names, strict=True):
                entries = mapping[path]
                if len(entries) != 1 or entries[0].stage != "0":
                    observation_problems.append(f"{member_name} 包含未解决的 Index stage")
                    continue
                entry = entries[0]
                if entry.mode not in {"100644", "100755"}:
                    validation_problems.append(f"{member_name} 不是 Git regular-file mode")
                    continue
                if member_name == "file-asset.yaml":
                    manifest_data, problem = _read_staged_blob(
                        worktree,
                        entry.oid,
                        index_file=index_file,
                        max_bytes=DEFAULT_MANIFEST_BUDGET,
                    )
                    if problem is not None:
                        observation_problems.append(f"file-asset.yaml: {problem}")
                elif member_name == "payload":
                    payload_data, problem = _read_staged_blob(
                        worktree,
                        entry.oid,
                        index_file=index_file,
                        max_bytes=DEFAULT_PAYLOAD_BUDGET,
                    )
                    if problem is not None:
                        observation_problems.append(f"payload: {problem}")
            file_assets.append(
                StagedFileAssetCandidate(
                    object_id,
                    tuple(sorted(changed_paths)),
                    member_names,
                    manifest_data,
                    payload_data,
                    any(path.startswith(object_prefix) for path in head_paths),
                    "; ".join(observation_problems) or None,
                    "; ".join(validation_problems) or None,
                )
            )
    return tuple(candidates), tuple(file_assets), None


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
    fact_candidates, file_asset_candidates, failure = _fact_candidates(
        worktree,
        paths,
        index_before,
        index_file=index_file,
    )
    if failure is not None:
        return CommitCandidateObservation("unverifiable", None, (failure,), paths, snapshot_before)
    snapshot_after, _, failure = _snapshot(worktree, index_file=index_file)
    if failure is not None:
        return CommitCandidateObservation("unverifiable", None, (failure,), paths, snapshot_before)
    if snapshot_before != snapshot_after:
        issue = _issue("drift", "Index or HEAD changed while the candidate was being observed")
        return CommitCandidateObservation("drifted", None, (issue,), paths, snapshot_after)

    value = CommitValidationInput(
        message=message,
        candidate_paths=paths,
        git_worktree_root=str(worktree),
        governance_status=governance.scope_status.value,
        governance_identity=_governance_identity(governance),
        snapshot_identity=snapshot_after,
        source_path=contract.source_path,
        source_fingerprint=contract.content_fingerprint,
        fact_candidates=fact_candidates,
        file_asset_candidates=file_asset_candidates,
    )
    return CommitCandidateObservation(
        "observed",
        value,
        (),
        paths,
        snapshot_after,
        fact_candidates,
        file_asset_candidates,
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
