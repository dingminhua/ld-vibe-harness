from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import tempfile
from typing import Any


DEFAULT_TTL_SECONDS = 30 * 60
CACHE_SCHEMA_VERSION = 1
REQUIRED_ACK_EVENT = "acknowledge_read_plan"
DISABLE_VALUES = {"0", "false", "no", "off"}
ALLOWED_CACHE_KEYS = {
    "schema_version",
    "event",
    "session_id",
    "workspace_root",
    "workspace_hash",
    "trigger_source",
    "acknowledged_paths",
    "created_at",
    "expires_at",
    "boundary",
}


@dataclass(frozen=True)
class RuntimeCacheResult:
    status: str
    path: str
    acknowledged_paths: list[str]
    reason: str = ""
    expires_at: str = ""


def runtime_cache_enabled() -> bool:
    return os.environ.get("LDVH_RUNTIME_CACHE", "").strip().lower() not in DISABLE_VALUES


def _uid_text() -> str:
    if hasattr(os, "getuid"):
        return str(os.getuid())
    return os.environ.get("USERNAME") or os.environ.get("USER") or "user"


def runtime_cache_dir() -> Path:
    override = os.environ.get("LDVH_RUNTIME_CACHE_DIR", "").strip()
    if override:
        return Path(override).expanduser()

    system = platform.system().lower()
    if system == "darwin":
        return Path(os.environ.get("TMPDIR") or tempfile.gettempdir()) / "ldvh-codex-hook" / "receipts"
    if system == "windows":
        return Path(tempfile.gettempdir()) / "LDVH" / "CodexHook" / "receipts"

    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
    if xdg_runtime:
        return Path(xdg_runtime) / "ldvh" / "codex-hook" / "receipts"

    xdg_cache = os.environ.get("XDG_CACHE_HOME", "").strip()
    if xdg_cache:
        return Path(xdg_cache) / "ldvh" / "codex-hook" / "receipts"
    return Path.home() / ".cache" / "ldvh" / "codex-hook" / "receipts"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def workspace_hash(root: Path) -> str:
    return hashlib.sha256(root.resolve(strict=False).as_posix().encode("utf-8")).hexdigest()[:16]


def receipt_cache_path(root: Path, session_id: str) -> Path:
    safe_session = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]
    return runtime_cache_dir() / f"ack-{workspace_hash(root)}-{safe_session}.json"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _safe_resolve(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _cache_dir_boundary_error(root: Path, cache_dir: Path) -> str:
    resolved_root = _safe_resolve(root)
    resolved_cache = _safe_resolve(cache_dir)
    if resolved_cache == resolved_root or _is_relative_to(resolved_cache, resolved_root):
        return "runtime cache directory must not be inside the LDVH repo"
    return ""


def _ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(path, 0o700)


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        fd = os.open(path.as_posix(), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _load_cache_payload(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _unlink_quietly(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def cleanup_runtime_cache(now: datetime | None = None) -> int:
    base = runtime_cache_dir()
    if not base.exists():
        return 0
    current = now or _utc_now()
    removed = 0
    for path in base.glob("ack-*.json"):
        payload = _load_cache_payload(path)
        if payload is None:
            _unlink_quietly(path)
            removed += 1
            continue
        expires = _parse_iso(str(payload.get("expires_at", "")))
        if expires is None or expires <= current:
            _unlink_quietly(path)
            removed += 1
    return removed


def write_ack_receipt(
    root: Path,
    *,
    session_id: str,
    acknowledged_paths: list[str],
    trigger_source: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> RuntimeCacheResult:
    if not runtime_cache_enabled():
        return RuntimeCacheResult("disabled", "", [], "LDVH_RUNTIME_CACHE disabled")
    if not session_id.strip():
        return RuntimeCacheResult("skipped", "", [], "session_id missing")
    if not acknowledged_paths:
        return RuntimeCacheResult("skipped", "", [], "acknowledged_paths empty")

    base = runtime_cache_dir()
    boundary_error = _cache_dir_boundary_error(root, base)
    if boundary_error:
        return RuntimeCacheResult("blocked", _safe_resolve(base).as_posix(), [], boundary_error)
    _ensure_private_dir(base)
    cleanup_runtime_cache()

    now = _utc_now()
    safe_ttl = max(1, min(int(ttl_seconds), DEFAULT_TTL_SECONDS))
    expires_at = now + timedelta(seconds=safe_ttl)
    target = receipt_cache_path(root, session_id)
    payload = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "event": REQUIRED_ACK_EVENT,
        "session_id": session_id,
        "workspace_root": root.resolve(strict=False).as_posix(),
        "workspace_hash": workspace_hash(root),
        "trigger_source": trigger_source,
        "acknowledged_paths": acknowledged_paths,
        "created_at": _iso(now),
        "expires_at": _iso(expires_at),
        "boundary": "runtime receipt cache 是短期过程回执，不是事实源、授权、验证结论或 Human Gate。",
    }

    fd, tmp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=base.as_posix(), text=True)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if os.name != "nt":
            os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, target)
        _fsync_directory(base)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
    return RuntimeCacheResult("written", target.as_posix(), acknowledged_paths, expires_at=_iso(expires_at))


def read_ack_receipt(root: Path, *, session_id: str) -> RuntimeCacheResult:
    if not runtime_cache_enabled():
        return RuntimeCacheResult("disabled", "", [], "LDVH_RUNTIME_CACHE disabled")
    if not session_id.strip():
        return RuntimeCacheResult("miss", "", [], "session_id missing")

    base = runtime_cache_dir()
    boundary_error = _cache_dir_boundary_error(root, base)
    if boundary_error:
        return RuntimeCacheResult("blocked", _safe_resolve(base).as_posix(), [], boundary_error)

    cleanup_runtime_cache()
    path = receipt_cache_path(root, session_id)
    if not path.is_file():
        return RuntimeCacheResult("miss", path.as_posix(), [], "receipt missing")
    payload = _load_cache_payload(path)
    if payload is None:
        _unlink_quietly(path)
        return RuntimeCacheResult("invalid", path.as_posix(), [], "receipt payload invalid")

    def invalid(reason: str) -> RuntimeCacheResult:
        _unlink_quietly(path)
        return RuntimeCacheResult("invalid", path.as_posix(), [], reason)

    if set(payload) - ALLOWED_CACHE_KEYS:
        return invalid("unknown fields")
    if payload.get("schema_version") != CACHE_SCHEMA_VERSION:
        return invalid("schema_version mismatch")
    if payload.get("event") != REQUIRED_ACK_EVENT:
        return invalid("event mismatch")
    if payload.get("session_id") != session_id:
        return invalid("session_id mismatch")
    if payload.get("workspace_hash") != workspace_hash(root):
        return invalid("workspace mismatch")
    if payload.get("workspace_root") != root.resolve(strict=False).as_posix():
        return invalid("workspace_root mismatch")
    if _parse_iso(str(payload.get("created_at", ""))) is None:
        return invalid("created_at invalid")
    if not str(payload.get("boundary", "")).strip():
        return invalid("boundary missing")

    expires = _parse_iso(str(payload.get("expires_at", "")))
    if expires is None or expires <= _utc_now():
        try:
            path.unlink()
        except OSError:
            pass
        return RuntimeCacheResult("expired", path.as_posix(), [], "receipt expired")

    raw_acknowledged_paths = payload.get("acknowledged_paths")
    if not isinstance(raw_acknowledged_paths, list):
        return invalid("acknowledged_paths invalid")
    acknowledged_paths = [str(item) for item in raw_acknowledged_paths if str(item).strip()]
    if not acknowledged_paths:
        return invalid("acknowledged_paths empty")
    return RuntimeCacheResult("hit", path.as_posix(), acknowledged_paths, expires_at=str(payload.get("expires_at", "")))
