"""Shared pure validation core for fact-object content bytes.

This is the single mechanical core consumed both by the Working-Tree read
path (``ldvh.facts.repository``) and by the commit-candidate staged-content
layer (specs 03 §9.9).  It performs the byte budget, UTF-8 decoding, carrier
parsing, schema validation, object_id identity check and content fingerprint
exactly once; callers supply the bytes from their own observation boundary.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Literal

from ldvh.facts.carriers.study_markdown import parse_study_markdown
from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import FactTypeLayout
from ldvh.facts.models import FactIssue
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import validate_fact_object

MAX_FACT_BYTES = 4 * 1024 * 1024
ContentCheckStatus = Literal["mechanically_valid", "invalid", "unavailable"]


@dataclass(frozen=True, slots=True)
class FactContentValidation:
    """Mechanical outcome for one fact-object content payload."""

    check_status: ContentCheckStatus
    fields: dict[str, Any] | None
    body: str | None
    issues: tuple[FactIssue, ...]
    content_fingerprint: str | None
    raw_text: str | None
    raw_byte_count: int | None


def validate_fact_content(
    layout: FactTypeLayout,
    schema: FactSchema,
    object_id: str,
    data: bytes,
    *,
    max_bytes: int = MAX_FACT_BYTES,
) -> FactContentValidation:
    """Validate raw content bytes against the same core as the read path.

    The function is pure: it never touches Git, the filesystem or the clock.
    ``object_id`` is the identity parsed from the candidate file name.
    """

    effective_max_bytes = min(MAX_FACT_BYTES, max_bytes)
    if len(data) > effective_max_bytes:
        return FactContentValidation(
            "unavailable",
            None,
            None,
            (FactIssue("parse", f"事实对象载体超过 {effective_max_bytes} bytes 读取预算"),),
            None,
            None,
            len(data),
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return FactContentValidation(
            "invalid",
            None,
            None,
            (FactIssue("parse", "事实对象无法作为 UTF-8 普通文件读取"),),
            None,
            None,
            len(data),
        )

    parsed = parse_study_markdown(text) if layout.carrier == "markdown" else parse_yaml_object(text)
    if parsed.fields is None or parsed.issues:
        return FactContentValidation(
            "invalid",
            parsed.fields,
            parsed.body,
            tuple(parsed.issues),
            None,
            text,
            len(data),
        )

    issues = list(validate_fact_object(layout.fact_type_key, parsed.fields, schema))
    if parsed.fields.get("object_id") != object_id:
        issues.append(FactIssue("identity", "object_id 与请求引用及文件名不一致", "object_id"))
    status: ContentCheckStatus = "invalid" if issues else "mechanically_valid"
    fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return FactContentValidation(
        status,
        parsed.fields,
        parsed.body,
        tuple(issues),
        fingerprint,
        text,
        len(data),
    )


__all__ = ["ContentCheckStatus", "FactContentValidation", "MAX_FACT_BYTES", "validate_fact_content"]
