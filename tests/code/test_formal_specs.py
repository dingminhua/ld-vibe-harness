from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
FORMAL_REVIEW_DIR = ROOT / "reviews" / "formal"
BOOTSTRAP_OBJECT_IDS = {
    "00",
    "01",
    "01.Att.01",
    "01.Att.02",
    "02",
    "04",
    "04.Att.01",
    "04.Att.02",
    "04.Att.03",
    "04.Att.04",
    "04.Att.05",
}
FIXED_HEAD_SECTIONS = [
    "价值判断",
    "权威依据",
    "归口边界",
    "适用范围",
]
FIXED_TAIL_SECTIONS = [
    "保障措施",
    "验证方法",
    "Human Gate",
    "Stop Conditions",
    "待补齐事项",
]
FORBIDDEN_ATTACHMENT_HEADINGS = [
    "## 上位依据",
    "## 行动流程",
    "## Human Gate",
    "## 事实源边界",
    "## 迁移过程",
]
RULE_LIKE_ATTACHMENT_TERMS = [
    "必须",
    "不得",
    "应当",
    "需要",
    "Human Gate",
    "事实源",
    "行动流程",
    "验证",
    "回写",
    "触发",
    "阻断",
]

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
    if "ldvh_spec" in metadata:
        spec = metadata["ldvh_spec"]
        return spec["spec_id"], spec
    if "ldvh_attachment" in metadata:
        attachment = metadata["ldvh_attachment"]
        return attachment["attachment_id"], attachment
    raise AssertionError(f"{path} missing ldvh_spec or ldvh_attachment identity block")


def _attachment_body_lines_after_identity(raw: str) -> list[tuple[int, str]]:
    fence = re.search(r"```yaml\n.*?\n```", raw, re.S)
    assert fence, raw[:80]
    start_line = raw[: fence.end()].count("\n") + 1
    body = raw[fence.end() :].splitlines()
    return [(start_line + index, line) for index, line in enumerate(body, start=1)]


def _is_allowed_attachment_body_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("> 文件状态："):
        return True
    if stripped.startswith("|"):
        return True
    if re.fullmatch(r"[\w`./ -]+[：:]", stripped):
        return True
    return False


def _normalized_h2_titles(raw: str) -> list[str]:
    titles: list[str] = []
    for match in re.finditer(r"^##\s+(.+?)\s*$", raw, re.M):
        title = match.group(1).strip()
        titles.append(re.sub(r"^\d+[.、]\s*", "", title))
    return titles


def _h2_titles(raw: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"^##\s+(.+?)\s*$", raw, re.M)]


def test_ldvh_starts_from_markdown_specs_only() -> None:
    assert (ROOT / "specs" / "00-理念与构成.md").exists()
    assert (ROOT / "specs" / "01-保障与衔接.md").exists()
    assert (ROOT / "specs" / "02-AI行为规范.md").exists()
    assert (ROOT / "specs" / "03-事实源与Git溯源规范.md").exists()
    assert (ROOT / "specs" / "04-Specs基础规范.md").exists()
    assert (ROOT / "specs" / "05-事实模型基础规范.md").exists()
    assert (ROOT / "specs" / "06-行动模板基础规范.md").exists()
    assert (ROOT / "specs" / "07-Code确定性执行规范.md").exists()
    assert (ROOT / "specs" / "08-Web信息同步规范.md").exists()
    assert (ROOT / "specs" / "09-测试与验证规范.md").exists()
    assert (ROOT / "specs" / "10-管辖项目配置规范.md").exists()
    assert (ROOT / "specs" / "20-Spark-火花.md").exists()
    assert (ROOT / "specs" / "21-WorkCase-工作项.md").exists()
    assert (ROOT / "specs" / "22-ADR-决策.md").exists()
    assert (ROOT / "specs" / "23-Pitfall-踩坑经验.md").exists()
    assert (ROOT / "specs" / "24-Study-研究报告.md").exists()


def test_no_parallel_authority_layers() -> None:
    assert not (ROOT / "specs" / "core").exists()
    assert not (ROOT / "specs" / "schemas").exists()


def test_attachments_stay_subordinate_tables_or_enums() -> None:
    attachments = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "specs" / "attachments").glob("*.md")
    )
    assert attachments == [
        "specs/attachments/01.Att.01-保障消费时机表.md",
        "specs/attachments/01.Att.02-保障机制承接矩阵.md",
        "specs/attachments/01.Att.03-环境入口类型表.md",
        "specs/attachments/01.Att.04-环境接入状态表.md",
        "specs/attachments/01.Att.05-runtime-payload字段表.md",
        "specs/attachments/01.Att.06-环境安装回滚检查表.md",
        "specs/attachments/03.Att.01-Commit-Message契约字段表.md",
        "specs/attachments/04.Att.01-规范身份字段表.md",
        "specs/attachments/04.Att.02-规范信息角色表.md",
        "specs/attachments/04.Att.03-引用关系类型表.md",
        "specs/attachments/04.Att.04-保障要求字段表.md",
        "specs/attachments/04.Att.05-附件身份字段表.md",
        "specs/attachments/04.Att.06-术语表.md",
        "specs/attachments/05.Att.01-字段注册表结构.md",
        "specs/attachments/09.Att.01-验证声明字段表.md",
        "specs/attachments/10.Att.01-管辖项目配置字段表.md",
    ]

    spec_04 = (ROOT / "specs" / "04-Specs基础规范.md").read_text(encoding="utf-8")
    assert "附件只是正文授权的附属内容" in spec_04
    assert "附件不得承载上位原则、核心规则、行动流程、Human Gate" in spec_04

    for rel_path in attachments:
        raw = (ROOT / rel_path).read_text(encoding="utf-8")
        match = re.search(r"```yaml\n(.*?)\n```", raw, re.S)
        assert match, rel_path
        metadata = yaml.safe_load(match.group(1))["ldvh_attachment"]
        assert "authority" not in metadata, rel_path
        assert metadata["relation"] == "authorizes_attachment", rel_path
        assert f'canonical_path: "{rel_path}"' in raw
        for term in FORBIDDEN_ATTACHMENT_HEADINGS:
            assert term not in raw, rel_path
        for line_number, line in _attachment_body_lines_after_identity(raw):
            assert _is_allowed_attachment_body_line(line), f"{rel_path}:{line_number}: {line}"
            if line.strip() and not line.lstrip().startswith((">", "|")):
                for term in RULE_LIKE_ATTACHMENT_TERMS:
                    assert term not in line, f"{rel_path}:{line_number}: {line}"


def test_formal_specs_keep_ldvh_identity_blocks() -> None:
    for path in [
        ROOT / "specs" / "00-理念与构成.md",
        ROOT / "specs" / "01-保障与衔接.md",
        ROOT / "specs" / "02-AI行为规范.md",
        ROOT / "specs" / "03-事实源与Git溯源规范.md",
        ROOT / "specs" / "04-Specs基础规范.md",
        ROOT / "specs" / "05-事实模型基础规范.md",
        ROOT / "specs" / "06-行动模板基础规范.md",
        ROOT / "specs" / "07-Code确定性执行规范.md",
        ROOT / "specs" / "08-Web信息同步规范.md",
        ROOT / "specs" / "09-测试与验证规范.md",
        ROOT / "specs" / "10-管辖项目配置规范.md",
        ROOT / "specs" / "20-Spark-火花.md",
        ROOT / "specs" / "21-WorkCase-工作项.md",
        ROOT / "specs" / "22-ADR-决策.md",
        ROOT / "specs" / "23-Pitfall-踩坑经验.md",
        ROOT / "specs" / "24-Study-研究报告.md",
    ]:
        raw = path.read_text(encoding="utf-8")
        assert re.search(r"```yaml\nldvh_spec:", raw), path
        assert f'canonical_path: "{path.relative_to(ROOT)}"' in raw


def test_non_root_specs_keep_fixed_head_and_tail_entries() -> None:
    for path in [
        ROOT / "specs" / "01-保障与衔接.md",
        ROOT / "specs" / "02-AI行为规范.md",
        ROOT / "specs" / "03-事实源与Git溯源规范.md",
        ROOT / "specs" / "04-Specs基础规范.md",
        ROOT / "specs" / "05-事实模型基础规范.md",
        ROOT / "specs" / "06-行动模板基础规范.md",
        ROOT / "specs" / "07-Code确定性执行规范.md",
        ROOT / "specs" / "08-Web信息同步规范.md",
        ROOT / "specs" / "09-测试与验证规范.md",
        ROOT / "specs" / "10-管辖项目配置规范.md",
        ROOT / "specs" / "20-Spark-火花.md",
        ROOT / "specs" / "21-WorkCase-工作项.md",
        ROOT / "specs" / "22-ADR-决策.md",
        ROOT / "specs" / "23-Pitfall-踩坑经验.md",
        ROOT / "specs" / "24-Study-研究报告.md",
    ]:
        raw = path.read_text(encoding="utf-8")
        titles = _normalized_h2_titles(raw)
        assert titles[: len(FIXED_HEAD_SECTIONS)] == FIXED_HEAD_SECTIONS, path
        assert titles[-len(FIXED_TAIL_SECTIONS) :] == FIXED_TAIL_SECTIONS, path
        assert len(titles) > len(FIXED_HEAD_SECTIONS) + len(FIXED_TAIL_SECTIONS), path


def test_role_sections_point_to_existing_h2_entries() -> None:
    for path in [
        ROOT / "specs" / "01-保障与衔接.md",
        ROOT / "specs" / "02-AI行为规范.md",
        ROOT / "specs" / "03-事实源与Git溯源规范.md",
        ROOT / "specs" / "04-Specs基础规范.md",
        ROOT / "specs" / "05-事实模型基础规范.md",
        ROOT / "specs" / "06-行动模板基础规范.md",
        ROOT / "specs" / "07-Code确定性执行规范.md",
        ROOT / "specs" / "08-Web信息同步规范.md",
        ROOT / "specs" / "09-测试与验证规范.md",
        ROOT / "specs" / "10-管辖项目配置规范.md",
        ROOT / "specs" / "20-Spark-火花.md",
        ROOT / "specs" / "21-WorkCase-工作项.md",
        ROOT / "specs" / "22-ADR-决策.md",
        ROOT / "specs" / "23-Pitfall-踩坑经验.md",
        ROOT / "specs" / "24-Study-研究报告.md",
    ]:
        raw = path.read_text(encoding="utf-8")
        metadata = _first_yaml_block(path)["ldvh_spec"]
        role_sections = metadata["role_sections"]
        assert "local_rules" not in role_sections, path
        assert "rule_body" in role_sections, path
        h2_titles = set(_h2_titles(raw))
        for value in role_sections.values():
            values = value if isinstance(value, list) else [value]
            for title in values:
                assert title in h2_titles, f"{path}: {title}"


def test_formal_objects_have_unique_ids_and_real_paths() -> None:
    seen_ids: set[str] = set()
    for path in _formal_markdown_files():
        object_id, metadata = _formal_object_id_and_metadata(path)
        assert object_id not in seen_ids, object_id
        seen_ids.add(object_id)
        assert metadata["canonical_path"] == path.relative_to(ROOT).as_posix(), path


def test_review_receipts_stay_narrow() -> None:
    for path in sorted(FORMAL_REVIEW_DIR.glob("*-formal-review.yaml")):
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

        review_path = FORMAL_REVIEW_DIR / f"{object_id}-formal-review.yaml"
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
