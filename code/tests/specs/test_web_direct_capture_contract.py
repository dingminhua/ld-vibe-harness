from __future__ import annotations

import base64
import hashlib
import json
import unicodedata
from pathlib import Path

import pytest

from ldvh.helper.operation_sources import inspect_operation_sources
from ldvh.specs.action_templates import inspect_action_template_sources
from ldvh.specs.field_registry import inspect_field_registry
from ldvh.specs.markdown import parse_markdown
from ldvh.specs.repository import inspect_repository

ADMISSION_AUDIT_PATH = "docs/v4-architecture/active/V4-五类型全局归并封闭记录.md"
WHITE_SPACE = frozenset(
    [
        *range(0x0009, 0x000E),
        0x0020,
        0x0085,
        0x00A0,
        0x1680,
        *range(0x2000, 0x200B),
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
    ]
)
ASCII_DIGEST = "5626348cede47a57cdb59910a5b23e11013c5508554b1998ba92bcd4ab18ec69"
ASCII_BASE64 = "eyJwcmlvcml0eSI6IlAzIiwic3VtbWFyeSI6IkJldGEiLCJ0aXRsZSI6IkFscGhhIn0="
UNICODE_DIGEST = "e3208211e97f642d5bb5e363cd5ea64c68c7f872c6aca294edca6ccc60d491ef"
UNICODE_BASE64 = (
    "eyJwcmlvcml0eSI6IlAyIiwic3VtbWFyeSI6IuS4reKAqOaWhyBcIui3r+W+hFxcXCJcblx1MDAwMfCfmIAi"
    "LCJ0aXRsZSI6IkNhZsOpIFwiQS9CXCIifQ=="
)


def _trim_nfc(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    if any(0xD800 <= ord(character) <= 0xDFFF for character in normalized):
        raise ValueError("unpaired surrogate")
    start = 0
    end = len(normalized)
    while start < end and ord(normalized[start]) in WHITE_SPACE:
        start += 1
    while end > start and ord(normalized[end - 1]) in WHITE_SPACE:
        end -= 1
    return normalized[start:end]


def _canonical(title: str, description: str, priority: str) -> bytes:
    if priority not in {"P0", "P1", "P2", "P3"}:
        raise ValueError("invalid priority")
    payload = {
        "title": _trim_nfc(title),
        "summary": _trim_nfc(description),
        "priority": priority,
    }
    if not payload["title"] or not payload["summary"]:
        raise ValueError("empty normalized content")
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _section(source: str, heading: str, next_heading: str) -> str:
    return source.split(heading, 1)[1].split(next_heading, 1)[0]


def test_canonical_vectors_freeze_unicode_json_digest_and_standard_base64() -> None:
    ascii_payload = _canonical("  Alpha  ", "  Beta  ", "P3")
    assert ascii_payload == b'{"priority":"P3","summary":"Beta","title":"Alpha"}'
    assert hashlib.sha256(ascii_payload).hexdigest() == ASCII_DIGEST
    assert base64.b64encode(ascii_payload).decode("ascii") == ASCII_BASE64

    unicode_payload = _canonical(
        '\u2003Cafe\u0301 "A/B"\u00a0',
        '\u3000中\u2028文 "路径\\"\n\u0001😀\u00a0',
        "P2",
    )
    assert b"Cafe" not in unicode_payload
    assert "Café" in unicode_payload.decode("utf-8")
    assert "\u2028" in unicode_payload.decode("utf-8")
    assert b"\\u2028" not in unicode_payload
    assert b"\\u0001" in unicode_payload
    assert hashlib.sha256(unicode_payload).hexdigest() == UNICODE_DIGEST
    encoded = base64.b64encode(unicode_payload).decode("ascii")
    assert encoded == UNICODE_BASE64
    assert base64.b64encode(base64.b64decode(encoded, validate=True)).decode("ascii") == encoded
    assert hashlib.sha256(unicode_payload + b"tampered").hexdigest() != UNICODE_DIGEST


def test_canonicalization_rejects_feff_only_unpaired_surrogate_and_priority_repair() -> None:
    assert _trim_nfc("\ufeffAlpha\ufeff") == "\ufeffAlpha\ufeff"
    with pytest.raises(ValueError, match="unpaired surrogate"):
        _canonical("Alpha\ud800", "Beta", "P3")
    with pytest.raises(ValueError, match="invalid priority"):
        _canonical("Alpha", "Beta", "p3")
    with pytest.raises(ValueError, match="empty"):
        _canonical("\u3000\u00a0", "Beta", "P3")


def test_web_source_owns_capture_contract_without_changing_foundation_sources(
    current_specs_repository: Path,
) -> None:
    web = (current_specs_repository / "specs/08-Web 呈现与交互规范.md").read_text(encoding="utf-8")
    spark = (current_specs_repository / "specs/20-Spark-火花.md").read_text(encoding="utf-8")
    template = (current_specs_repository / "specs/31-事实对象判定与受控创建行动模板.md").read_text(encoding="utf-8")

    inspection = inspect_repository(current_specs_repository)
    web_document = inspection.document_passing_implemented_checks_by_key("web-presentation-interaction")
    assert web_document is not None
    assert {"fact-model-foundation", "spark-fact-type"} <= set(web_document.basis)
    assert inspection.issues == ()

    assert "kind: web-direct-capture" in web
    assert "data:application/json;base64,<payload>" in web
    assert "sha256:<64 位小写十六进制>" in web
    assert "bare `web-capture://sha256/<digest>`" in web
    assert "RFC 4648 standard Base64 alphabet" in web
    assert "U+FEFF" in web
    assert ASCII_DIGEST in web and ASCII_BASE64 in web
    assert UNICODE_DIGEST in web and UNICODE_BASE64 in web
    assert "Vercel/其它远程部署均拒绝且零写入" in web
    assert "4 MiB" in web and "分配事实 ID 或创建 allocator 状态之前" in web
    assert "创建前与首次写后回读时" in web
    assert "不要求历史 payload 永远等于当前对象快照" in web

    assert "Web direct capture 来源、精确重复与语义协调" in spark
    assert "Web direct capture carve-out" in template
    for path in (
        "specs/03-事实源与信息溯源规范.md",
        "specs/04-Helper CLI 服务规范.md",
        "specs/05-事实模型基础规范.md",
        "specs/attachments/05.Att.01-事实对象统一字段登记.md",
    ):
        assert "web-direct-capture" not in (current_specs_repository / path).read_text(encoding="utf-8")


def test_duplicate_and_reconciliation_rules_are_narrow_and_fail_closed(
    current_specs_repository: Path,
) -> None:
    spark = (current_specs_repository / "specs/20-Spark-火花.md").read_text(encoding="utf-8")
    direct = _section(
        spark,
        "### Web direct capture 来源、精确重复与语义协调",
        "### 主动召回与消费时机",
    )
    template = (current_specs_repository / "specs/31-事实对象判定与受控创建行动模板.md").read_text(encoding="utf-8")
    carve_out = _section(template, "### 5.6 Web direct capture carve-out", "## 6. 验证要求")

    assert all(status in direct for status in ("`open`", "`routed`", "`discarded`"))
    assert "非 2xx `exact_duplicate`" in direct
    assert "`governed_project_id`、`fact_type_key`、`object_id`" in direct
    assert "多个精确匹配" in direct and "coverage 超限" in direct and "fail closed" in direct
    assert "duplicate 按不同事实对象而不是 source-ref 条目计数" in direct
    assert "必须先验证对象中的全部 `web-direct-capture` source ref" in direct
    assert "无论是否已有该来源都从当前 `title/summary/priority`" in direct
    assert "不得以当前字段 identity 掩盖来源异常" in direct
    assert "终态只使用已验证历史 identity" in direct
    assert "后续扫描不要求历史 capture 永远等于" in direct
    assert "不得自动更新、重开、创建替代对象" in direct
    assert "可分页 Spark F2 reconciliation opportunity" in direct
    assert "按需展开 F3" in direct
    assert "不进入 F1" in direct
    assert "不自动合并" in direct
    assert "fact-object-lifecycle-change" in direct

    assert "不调用 Helper CLI" in carve_out
    assert "不改变二者要求 AI 已完成对象化" in carve_out
    assert "不适用于 WorkCase、ADR、Pitfall、Study" in carve_out
    assert "更新、处置、迁移、Git commit、远程或多用户部署" in carve_out


def test_direct_capture_adds_no_helper_operation_template_or_fact_field(
    current_specs_repository: Path,
) -> None:
    inspection = inspect_repository(current_specs_repository)
    operations = inspect_operation_sources(inspection)
    templates = inspect_action_template_sources(inspection)
    fields = inspect_field_registry(
        inspection.active_documents_passing_implemented_checks,
        admission_audit=parse_markdown(
            current_specs_repository / ADMISSION_AUDIT_PATH,
            ADMISSION_AUDIT_PATH,
        ).document,
    )

    assert len(operations.candidate_declarations) == 10
    assert all(
        "web" not in declaration.template_key and "capture" not in declaration.template_key
        for declaration in templates.candidate_declarations
    )
    assert all(
        declaration.source.path != "specs/08-Web 呈现与交互规范.md" for declaration in templates.candidate_declarations
    )
    assert len(fields.registrations) == 81
    assert operations.issues == ()
    assert templates.issues == ()
    assert fields.complete is True
