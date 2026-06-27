from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_v3_starts_from_markdown_specs_only() -> None:
    assert (ROOT / "specs" / "00-LDVH-v3理念与价值标准.md").exists()
    assert (ROOT / "specs" / "01-规范体系基础规范.md").exists()


def test_no_parallel_authority_layers() -> None:
    assert not (ROOT / "specs" / "core").exists()
    assert not (ROOT / "specs" / "schemas").exists()


def test_01_does_not_authorize_structural_attachments() -> None:
    attachments = sorted((ROOT / "specs" / "attachments").glob("01.Att.*.md"))
    assert attachments == []

    spec_01 = (ROOT / "specs" / "01-规范体系基础规范.md").read_text(encoding="utf-8")
    assert "related_specs: []" in spec_01
    assert "附件只是正文的附属内容" in spec_01


def test_formal_specs_keep_v3_identity_blocks() -> None:
    for path in [
        ROOT / "specs" / "00-LDVH-v3理念与价值标准.md",
        ROOT / "specs" / "01-规范体系基础规范.md",
    ]:
        raw = path.read_text(encoding="utf-8")
        assert re.search(r"```yaml\nv3_spec:", raw), path
        assert f'canonical_path: "{path.relative_to(ROOT)}"' in raw
