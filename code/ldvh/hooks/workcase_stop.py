"""Project-level Claude Code/Cindy Stop gate for a precisely bound WorkCase.

The Stop hook is intentionally narrow: it only acts when the current session
carries an explicit ``LDVH_WORKCASE_STOP_BINDING`` env binding pointing at one
current WorkCase, and only then mechanically blocks a Stop whose fresh
projection is Controller-owned.  Missing binding, unreadable input, a Helper
failure or any exception fail open (``continue``).  ``stop_hook_active`` in the
Stop event always yields, so the gate cannot loop.  The gate never guesses a
WorkCase from the unique open candidate and never writes a fact.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.facts.contracts import LAYOUTS

BINDING_ENV = "LDVH_WORKCASE_STOP_BINDING"
SESSION_ENV = "CLAUDE_CODE_SESSION_ID"
_BINDING_DIRECTORY = ".ldvh-stop-bindings"
CHECK_OPERATION = "check-workcase-handoff"
Decision = Literal["continue", "block"]


class WorkCaseStopHookError(ValueError):
    """The Stop event could not be interpreted as a valid LDVH Stop input."""


@dataclass(frozen=True, slots=True)
class StopInput:
    """The subset of a Claude Code Stop event the gate consumes."""

    stop_hook_active: bool
    session_id: str | None
    cwd: str | None


@dataclass(frozen=True, slots=True)
class WorkCaseBinding:
    """Explicit current WorkCase identity; no guessing is ever performed."""

    governed_project_id: str
    object_id: str

    @classmethod
    def from_json(cls, value: object) -> WorkCaseBinding | None:
        if not isinstance(value, dict):
            return None
        governed_project_id = value.get("governed_project_id")
        fact_type_key = value.get("fact_type_key")
        object_id = value.get("object_id")
        if (
            not isinstance(governed_project_id, str)
            or not governed_project_id
            or fact_type_key != "workcase"
            or not isinstance(object_id, str)
            or LAYOUTS["workcase"].object_id_pattern.fullmatch(object_id) is None
        ):
            return None
        return cls(governed_project_id, object_id)

    def to_json(self) -> dict[str, str]:
        return {
            "governed_project_id": self.governed_project_id,
            "fact_type_key": "workcase",
            "object_id": self.object_id,
        }


@dataclass(frozen=True, slots=True)
class HandoffVerdict:
    """The read-only Helper verdict for the bound WorkCase snapshot."""

    handoff_allowed: bool
    handoff_reason: str | None
    next_required_control_step: str | None


@dataclass(frozen=True, slots=True)
class HookDecision:
    decision: Decision
    reason: str | None = None

    def to_json(self) -> dict[str, str | None]:
        payload: dict[str, str | None] = {"decision": self.decision}
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


def parse_stop_input(raw: str) -> StopInput:
    """Parse the host Stop JSON event into the consumed subset."""
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise WorkCaseStopHookError(f"Stop stdin is not valid UTF-8 JSON: {error}") from error
    if not isinstance(payload, dict):
        raise WorkCaseStopHookError("Stop event must be a JSON object")
    stop_hook_active = payload.get("stop_hook_active")
    if not isinstance(stop_hook_active, bool):
        raise WorkCaseStopHookError("stop_hook_active must be a boolean")
    session_id = payload.get("session_id")
    cwd = payload.get("cwd")
    return StopInput(
        stop_hook_active,
        session_id if isinstance(session_id, str) else None,
        cwd if isinstance(cwd, str) else None,
    )


def parse_binding(raw: str | None) -> WorkCaseBinding | None:
    """Parse the explicit binding env value; malformed binding fails open."""
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        return None
    return WorkCaseBinding.from_json(value)


def binding_path(repository_root: Path, session_id: str | None) -> Path | None:
    """Return the ignored per-session binding path for an exact session id."""
    allowed_characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    if not isinstance(session_id, str) or not session_id or any(
        character not in allowed_characters for character in session_id
    ):
        return None
    return repository_root / _BINDING_DIRECTORY / f"{session_id}.json"


def read_session_binding(repository_root: Path, session_id: str | None) -> WorkCaseBinding | None:
    """Read one explicitly written session binding; missing or malformed fails open."""
    path = binding_path(repository_root, session_id)
    if path is None:
        return None
    try:
        return parse_binding(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return None


def decide(
    stop_input: StopInput,
    binding: WorkCaseBinding | None,
    verdict: HandoffVerdict | None,
) -> HookDecision:
    """Map one Stop event to a decision under the source-defined exit set."""
    if stop_input.stop_hook_active:
        return HookDecision("continue")
    if binding is None or verdict is None:
        return HookDecision("continue")
    if verdict.handoff_allowed:
        return HookDecision("continue")
    reason = "LDVH 交还门：当前绑定 WorkCase 处于 Controller-owned 阶段，不允许 Stop 交还"
    if verdict.next_required_control_step:
        reason += f"；请继续下一控制步骤 {verdict.next_required_control_step}"
    return HookDecision("block", reason)


def make_cli_runner(
    repository_root: Path,
    *,
    launcher: str | None = None,
    timeout: int = 10,
) -> Callable[[WorkCaseBinding, str | None], HandoffVerdict]:
    """Return a runner that calls the source Helper CLI for the bound WorkCase."""
    launcher_path = Path(launcher) if launcher else repository_root / "ldvh"

    def invoke(binding: WorkCaseBinding, cwd: str | None) -> HandoffVerdict:
        payload = json.dumps({"arguments": {"fact_ref": binding.to_json()}})
        completed = subprocess.run(
            [sys.executable, str(launcher_path), "call", CHECK_OPERATION],
            input=payload,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=True,
            timeout=timeout,
        )
        response = json.loads(completed.stdout)
        result = response.get("result")
        if response.get("outcome") != "ok" or not isinstance(result, dict):
            raise WorkCaseStopHookError(f"check-workcase-handoff outcome={response.get('outcome')}")
        handoff_allowed = result.get("handoff_allowed")
        if not isinstance(handoff_allowed, bool):
            raise WorkCaseStopHookError("check-workcase-handoff returned no boolean handoff_allowed")
        return HandoffVerdict(
            handoff_allowed,
            result.get("handoff_reason"),
            result.get("next_required_control_step"),
        )

    return invoke


def evaluate(
    stop_input: StopInput,
    binding: WorkCaseBinding | None,
    invoke_check: Callable[[WorkCaseBinding, str | None], HandoffVerdict],
) -> HookDecision:
    """Evaluate one Stop event; every failure path fails open to continue."""
    if stop_input.stop_hook_active:
        return HookDecision("continue")
    if binding is None:
        return HookDecision("continue")
    try:
        verdict = invoke_check(binding, stop_input.cwd)
    except Exception:  # noqa: BLE001 - any Helper failure must fail open
        return HookDecision("continue")
    return decide(stop_input, binding, verdict)


def main(arguments: list[str] | None = None, *, stdin: str | None = None, env: dict[str, str] | None = None) -> int:
    """Run the Stop gate; print a JSON decision and always exit 0 (fail open)."""
    del arguments
    environment = os.environ if env is None else env
    raw = sys.stdin.read() if stdin is None else stdin
    try:
        stop_input = parse_stop_input(raw)
    except WorkCaseStopHookError:
        sys.stdout.write(json.dumps({"decision": "continue"}))
        return 0
    repository_root = Path(__file__).resolve().parents[3]
    binding = parse_binding(environment.get(BINDING_ENV))
    if binding is None:
        binding = read_session_binding(repository_root, stop_input.session_id)
    decision = evaluate(stop_input, binding, make_cli_runner(repository_root))
    sys.stdout.write(json.dumps(decision.to_json()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
