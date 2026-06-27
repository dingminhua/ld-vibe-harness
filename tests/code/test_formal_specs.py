from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_v3_starts_from_markdown_specs_only() -> None:
    assert (ROOT / "specs" / "00-LDVH-v3理念与价值标准.md").exists()
    assert (ROOT / "specs" / "01-规范体系基础规范.md").exists()


def test_no_parallel_authority_layers() -> None:
    assert not (ROOT / "specs" / "core").exists()
    assert not (ROOT / "specs" / "schemas").exists()


def test_01_only_authorizes_subordinate_table_attachments() -> None:
    attachments = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "specs" / "attachments").glob("01.Att.*.md")
    )
    assert attachments == [
        "specs/attachments/01.Att.01-规范身份字段表.md",
        "specs/attachments/01.Att.02-规范信息角色表.md",
        "specs/attachments/01.Att.03-引用关系类型表.md",
        "specs/attachments/01.Att.04-保障要求字段表.md",
        "specs/attachments/01.Att.05-附件身份字段表.md",
    ]

    spec_01 = (ROOT / "specs" / "01-规范体系基础规范.md").read_text(encoding="utf-8")
    assert "附件只是正文的附属内容" in spec_01
    assert "信息角色不是固定章节模板" in spec_01
    assert "未触发时不得要求空章节" in spec_01
    assert "验证与证据" in spec_01
    assert "不要求展开测试计划" in spec_01

    forbidden_body_level_terms = [
        "## 上位依据",
        "## 行动流程",
        "## Human Gate",
        "## 事实源边界",
        "## 迁移过程",
    ]
    for rel_path in attachments:
        raw = (ROOT / rel_path).read_text(encoding="utf-8")
        match = re.search(r"```yaml\n(.*?)\n```", raw, re.S)
        assert match, rel_path
        metadata = yaml.safe_load(match.group(1))["v3_attachment"]
        assert "authority" not in metadata, rel_path
        assert metadata["relation"] == "authorizes_attachment", rel_path
        assert f'canonical_path: "{rel_path}"' in raw
        for term in forbidden_body_level_terms:
            assert term not in raw, rel_path


def test_formal_specs_keep_v3_identity_blocks() -> None:
    for path in [
        ROOT / "specs" / "00-LDVH-v3理念与价值标准.md",
        ROOT / "specs" / "01-规范体系基础规范.md",
    ]:
        raw = path.read_text(encoding="utf-8")
        assert re.search(r"```yaml\nv3_spec:", raw), path
        assert f'canonical_path: "{path.relative_to(ROOT)}"' in raw
