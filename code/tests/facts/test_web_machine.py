from __future__ import annotations

from ldvh.facts import web_machine
from ldvh.facts.web_machine import MachineRequestError


def test_web_machine_only_exposes_read_operations() -> None:
    assert web_machine._OPERATIONS == frozenset({"list-sparks", "read-spark"})


def test_web_machine_rejects_removed_create_operation() -> None:
    request = {
        "protocol_version": 1,
        "operation": "create-spark",
        "scope": {},
        "arguments": {},
    }
    try:
        web_machine._request_parts(request)
    except MachineRequestError as exc:
        assert "not supported" in str(exc)
    else:
        raise AssertionError("create-spark must not remain supported")
