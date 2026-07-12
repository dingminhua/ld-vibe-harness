"""Parse the source-defined inputs for specification candidate reads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ldvh.helper.requests import CommonRequest

DisclosureLevel = Literal["L0", "L1", "L2"]

# These names mirror the current source contract for capability discovery.  They
# are checked against specification-model-foundation §9.4 by the contract tests.
REQUIRED_INPUTS: tuple[str, ...] = ()
OPTIONAL_INPUTS: tuple[str, ...] = (
    "arguments.responsibility_keys",
    "requested_disclosure",
)

_ARGUMENT_FIELDS = frozenset({"responsibility_keys"})


@dataclass(frozen=True, slots=True)
class SpecificationCandidateRequest:
    responsibility_keys: tuple[str, ...]
    disclosure: DisclosureLevel


@dataclass(frozen=True, slots=True)
class SpecificationCandidateRequestParseResult:
    request: SpecificationCandidateRequest | None
    problems: tuple[str, ...]


def parse_specification_candidate_request(
    request: CommonRequest,
) -> SpecificationCandidateRequestParseResult:
    """Validate and normalize the operation-specific portion of a common request."""

    problems: list[str] = []
    unknown_fields = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown_fields:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown_fields)}")

    raw_keys = request.arguments.get("responsibility_keys", [])
    responsibility_keys: tuple[str, ...] = ()
    if not isinstance(raw_keys, list):
        problems.append("arguments.responsibility_keys 必须是 array")
    else:
        valid_keys: list[str] = []
        for index, key in enumerate(raw_keys):
            if not isinstance(key, str) or not key:
                problems.append(f"arguments.responsibility_keys[{index}] 必须是非空 string")
            else:
                valid_keys.append(key)
        if len(valid_keys) != len(set(valid_keys)):
            problems.append("arguments.responsibility_keys 的成员不得重复")
        responsibility_keys = tuple(valid_keys)

    raw_disclosure = request.requested_disclosure
    disclosure: DisclosureLevel = "L0"
    if raw_disclosure is None:
        disclosure = "L0"
    elif isinstance(raw_disclosure, str) and raw_disclosure in {"L0", "L1", "L2"}:
        disclosure = raw_disclosure
    elif isinstance(raw_disclosure, str) and raw_disclosure in {"L3", "L4"}:
        problems.append(f"requested_disclosure={raw_disclosure} 不受本操作支持；只允许 L0、L1、L2 或 null")
    else:
        # CommonRequest normally reaches this parser only after common validation.
        # Keep this boundary total for direct internal callers without broadening it.
        problems.append("requested_disclosure 只允许 L0、L1、L2 或 null")

    if problems:
        return SpecificationCandidateRequestParseResult(None, tuple(problems))
    return SpecificationCandidateRequestParseResult(
        SpecificationCandidateRequest(
            responsibility_keys=responsibility_keys,
            disclosure=disclosure,
        ),
        (),
    )
