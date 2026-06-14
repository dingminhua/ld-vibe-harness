import json
from .common import checker, write_md

def test_runtime_projection_reports_missing_authority_and_spec_ref(tmp_path, monkeypatch):
    docs_specs = tmp_path / "specs"
    (tmp_path / "rules").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "FORMAL_SPECS_DIR", docs_specs)
    projection = write_md(
        tmp_path / "rules" / "LDVH-AI-ENTRY.md",
        """
# Runtime Projection

无权威来源引用
""",
    )
    missing_ref_projection = write_md(
        tmp_path / "runtime-missing-ref.md",
        """
# Runtime Projection

规范来源：`specs/99-Missing.md`
""",
    )

    report = checker.runtime_projection_report_build([str(projection), str(missing_ref_projection)])

    assert report["summary"]["status"] == "open"
    assert report["metadata"]["checked_file_count"] == 2
    assert {item["code"] for item in report["issues"]} == {
        "RUNTIME_PROJECTION_AUTHORITY_MISSING",
        "RUNTIME_PROJECTION_SPEC_REF_MISSING",
    }


def test_runtime_projection_reports_copied_formal_body(tmp_path, monkeypatch):
    docs_specs = tmp_path / "specs"
    (tmp_path / "rules").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "FORMAL_SPECS_DIR", docs_specs)
    write_md(
        docs_specs / "04.02-Test.md",
        """
# Runtime Source

这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第一行。
这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第二行。
这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第三行。
""",
    )
    projection = write_md(
        tmp_path / "rules" / "LDVH-AI-ENTRY.md",
        """
# Runtime Projection

规范来源：`specs/04.02-Test.md`

这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第一行。
这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第二行。
这是一段足够长的正式规范正文，用于触发运行投影复制正文风险检查第三行。
""",
    )

    report = checker.runtime_projection_report_build([str(projection)])

    assert report["summary"]["status"] == "degraded"
    assert report["issues"][0]["code"] == "RUNTIME_PROJECTION_BODY_COPIED"


def test_runtime_projection_cli_outputs_json(tmp_path, monkeypatch, capsys):
    docs_specs = tmp_path / "specs"
    (tmp_path / "rules").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checker, "FORMAL_SPECS_DIR", docs_specs)
    write_md(
        docs_specs / "04.02-Test.md",
        """
# Runtime Source
""",
    )
    projection = write_md(
        tmp_path / "rules" / "LDVH-AI-ENTRY.md",
        """
# Runtime Projection

规范来源：`specs/04.02-Test.md`
""",
    )

    exit_code = checker.main(["runtime-projection", str(projection), "--format", "json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["metadata"]["report"] == "runtime-projection"
    assert payload["summary"]["status"] == "closed"

