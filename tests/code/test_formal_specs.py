from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_OBJECT_IDS = {
    "00",
    "01",
    "01.Att.01",
    "01.Att.02",
    "01.Att.03",
    "01.Att.04",
    "01.Att.05",
}

REVIEW_TOP_LEVEL_KEYS = {
    "target_spec",
    "target_sha256",
    "change_type",
    "mapping_evidence",
    "code_verification",
    "subagent_review",
    "warnings",
}
REVIEW_NESTED_KEYS = {
    "mapping_evidence": {"path"},
    "code_verification": {"command", "passed", "receipt"},
    "subagent_review": {"agent_id", "reviewer", "verdict", "receipt", "unresolved_blockers"},
}
REVIEW_CHANGE_TYPES = {"migration", "modification", "addition"}
WARNING_KEYS = {"code", "source_ref", "message", "disposition", "follow_up", "report_required"}


def _first_yaml_block(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\n(.*?)\n```", raw, re.S)
    assert match, path
    return yaml.safe_load(match.group(1))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _formal_markdown_files() -> list[Path]:
    return sorted(
        path
        for path in (ROOT / "specs").glob("**/*.md")
        if path.name != ".gitkeep"
    )


def _formal_object_id_and_metadata(path: Path) -> tuple[str, dict]:
    metadata = _first_yaml_block(path)
    if "v3_spec" in metadata:
        spec = metadata["v3_spec"]
        return spec["spec_id"], spec
    if "v3_attachment" in metadata:
        attachment = metadata["v3_attachment"]
        return attachment["attachment_id"], attachment
    raise AssertionError(f"{path} missing v3_spec or v3_attachment identity block")


def test_v3_starts_from_markdown_specs_only() -> None:
    assert (ROOT / "specs" / "00-LDVH-v3理念与价值标准.md").exists()
    assert (ROOT / "specs" / "01-Specs基础规范.md").exists()


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

    spec_01 = (ROOT / "specs" / "01-Specs基础规范.md").read_text(encoding="utf-8")
    assert "附件只是正文的附属内容" in spec_01
    assert "信息角色不是固定章节模板" in spec_01
    assert "未触发时不得要求空章节" in spec_01
    assert "验证与证据" in spec_01
    assert "不要求展开测试计划" in spec_01
    assert "02 不建立成员规范骨架" in spec_01
    assert "本段只定义 formal review、Code 诊断和迁移准入中的 warning 收据口径" in spec_01
    assert "当前 Code 硬门已经覆盖" in spec_01
    assert "后续 Code 应逐步检查" in spec_01

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
        ROOT / "specs" / "01-Specs基础规范.md",
    ]:
        raw = path.read_text(encoding="utf-8")
        assert re.search(r"```yaml\nv3_spec:", raw), path
        assert f'canonical_path: "{path.relative_to(ROOT)}"' in raw


def test_formal_objects_have_unique_ids_and_real_paths() -> None:
    seen_ids: set[str] = set()
    for path in _formal_markdown_files():
        object_id, metadata = _formal_object_id_and_metadata(path)
        assert object_id not in seen_ids, object_id
        seen_ids.add(object_id)
        assert metadata["canonical_path"] == path.relative_to(ROOT).as_posix(), path


def test_review_receipts_stay_narrow() -> None:
    for path in sorted((ROOT / "_migration" / "reviews").glob("*-formal-review.yaml")):
        if path.name == "template-formal-review.yaml":
            continue
        review = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert set(review) == REVIEW_TOP_LEVEL_KEYS, path
        for key, allowed_keys in REVIEW_NESTED_KEYS.items():
            assert set(review[key]) == allowed_keys, path
        assert review["change_type"] in REVIEW_CHANGE_TYPES, path
        assert isinstance(review["warnings"], list), path
        for warning in review["warnings"]:
            assert set(warning) == WARNING_KEYS, path
            assert warning["code"], path
            assert warning["source_ref"], path
            assert warning["message"], path
            assert warning["disposition"], path
            assert warning["follow_up"], path
            assert warning["report_required"] is True, path


def test_formal_specs_and_attachments_require_code_and_subagent_review_gate() -> None:
    for path in _formal_markdown_files():
        object_id, metadata = _formal_object_id_and_metadata(path)
        if object_id in BOOTSTRAP_OBJECT_IDS:
            continue

        review_path = ROOT / "_migration" / "reviews" / f"{object_id}-formal-review.yaml"
        assert review_path.exists(), f"{path} missing migration review gate {review_path}"
        review = yaml.safe_load(review_path.read_text(encoding="utf-8"))
        assert set(review) == REVIEW_TOP_LEVEL_KEYS, review_path
        assert review["change_type"] in REVIEW_CHANGE_TYPES, review_path
        assert review["target_spec"] == metadata["canonical_path"]
        assert review["target_sha256"] == _sha256(path), review_path

        mapping_path = ROOT / review["mapping_evidence"]["path"]
        assert mapping_path.exists(), review_path
        assert mapping_path.relative_to(ROOT).as_posix().startswith("_migration/"), review_path

        assert review["code_verification"]["passed"] is True, review_path
        assert review["code_verification"]["command"], review_path
        assert review["code_verification"]["receipt"], review_path
        assert review["subagent_review"]["agent_id"], review_path
        assert review["subagent_review"]["verdict"] == "pass", review_path
        assert review["subagent_review"]["receipt"], review_path
        assert review["subagent_review"]["unresolved_blockers"] == [], review_path
        for warning in review["warnings"]:
            assert set(warning) == WARNING_KEYS, review_path
            assert warning["disposition"], review_path
            assert warning["follow_up"], review_path
            assert warning["report_required"] is True, review_path
