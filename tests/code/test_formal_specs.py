from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
LEGACY_FIXED_HEAD_SECTIONS = [
    "价值判断",
    "权威依据",
    "归口边界",
    "适用范围",
]
TARGET_FIXED_HEAD_SECTIONS = [
    "价值判断",
    "规范依据",
    "职责边界",
    "适用范围",
]
LEGACY_FIXED_TAIL_SECTIONS = [
    "保障措施",
    "验证方法",
    "Human Gate",
    "Stop Conditions",
    "待补齐事项",
]
TARGET_FIXED_TAIL_SECTIONS = [
    "验证要求",
    "Human Gate",
    "Stop Conditions",
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


def _first_yaml_block(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\n(.*?)\n```", raw, re.S)
    assert match, path
    return yaml.safe_load(match.group(1))


def _formal_markdown_files() -> list[Path]:
    return sorted(
        path
        for path in (ROOT / "specs").glob("**/*.md")
        if path.name != ".gitkeep"
    )


def _spec_markdown_files(*, include_root: bool) -> list[Path]:
    paths = sorted((ROOT / "specs").glob("*.md"))
    if include_root:
        return paths
    return [path for path in paths if not path.name.startswith("00-")]


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
    assert (ROOT / "specs" / "04-规范体系基础规范.md").exists()
    assert (ROOT / "specs" / "05-事实模型基础规范.md").exists()
    assert (ROOT / "specs" / "06-行动模板基础规范.md").exists()
    assert (ROOT / "specs" / "07-Code确定性执行规范.md").exists()
    assert (ROOT / "specs" / "08-Web信息同步规范.md").exists()
    assert (ROOT / "specs" / "09-测试与验证规范.md").exists()
    assert (ROOT / "specs" / "10-安装与配置规范.md").exists()
    assert (ROOT / "specs" / "20-Spark-火花.md").exists()
    assert (ROOT / "specs" / "21-WorkCase-工作项.md").exists()
    assert (ROOT / "specs" / "22-ADR-决策.md").exists()
    assert (ROOT / "specs" / "23-Pitfall-踩坑经验.md").exists()
    assert (ROOT / "specs" / "24-Study-研究报告.md").exists()
    assert (ROOT / "specs" / "30-安装配置与验证行动模板.md").exists()
    assert not (ROOT / "specs" / "31-环境Hook接入后验收行动模板.md").exists()


def test_no_parallel_authority_layers() -> None:
    assert not (ROOT / "specs" / "core").exists()
    assert not (ROOT / "specs" / "schemas").exists()


def test_attachments_stay_subordinate_tables_or_enums() -> None:
    attachments = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "specs" / "attachments").glob("*.md")
    )
    assert attachments

    spec_04 = (ROOT / "specs" / "04-规范体系基础规范.md").read_text(encoding="utf-8")
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
    for path in _spec_markdown_files(include_root=True):
        raw = path.read_text(encoding="utf-8")
        assert re.search(r"```yaml\nldvh_spec:", raw), path
        assert f'canonical_path: "{path.relative_to(ROOT)}"' in raw


def test_root_spec_keeps_root_tail_entries() -> None:
    path = ROOT / "specs" / "00-理念与构成.md"
    titles = _normalized_h2_titles(path.read_text(encoding="utf-8"))
    assert titles[-len(TARGET_FIXED_TAIL_SECTIONS):] == TARGET_FIXED_TAIL_SECTIONS


def test_non_root_specs_keep_legacy_or_target_head_and_tail_entries() -> None:
    for path in _spec_markdown_files(include_root=False):
        raw = path.read_text(encoding="utf-8")
        titles = _normalized_h2_titles(raw)
        legacy = (
            titles[:len(LEGACY_FIXED_HEAD_SECTIONS)] == LEGACY_FIXED_HEAD_SECTIONS
            and titles[-len(LEGACY_FIXED_TAIL_SECTIONS):] == LEGACY_FIXED_TAIL_SECTIONS
        )
        target = (
            titles[:len(TARGET_FIXED_HEAD_SECTIONS)] == TARGET_FIXED_HEAD_SECTIONS
            and titles[-len(TARGET_FIXED_TAIL_SECTIONS):] == TARGET_FIXED_TAIL_SECTIONS
        )
        assert legacy or target, path
        fixed_count = (
            len(LEGACY_FIXED_HEAD_SECTIONS) + len(LEGACY_FIXED_TAIL_SECTIONS)
            if legacy
            else len(TARGET_FIXED_HEAD_SECTIONS) + len(TARGET_FIXED_TAIL_SECTIONS)
        )
        assert len(titles) > fixed_count, path


def test_role_sections_point_to_existing_h2_entries() -> None:
    for path in _spec_markdown_files(include_root=False):
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
