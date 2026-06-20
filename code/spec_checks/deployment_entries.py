"""LDVH deployment entry asset checks."""

from pathlib import Path

import yaml

from .common import Issue


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT_ENTRIES_AI_ENTRY_PATHS = [
    "rules/LDVH-WORKSPACE-ENTRY.md",
    "rules/LDVH-MAINTAINER-ENTRY.md",
]
DEPLOYMENT_ENTRIES_AI_ENTRY_PATH = DEPLOYMENT_ENTRIES_AI_ENTRY_PATHS[0]
DEPLOYMENT_ENTRIES_SPEC_PATH = "specs/04.02-LDVH能力资产与落地保障规范.md"
DEPLOYMENT_ENTRIES_REQUIRED_ASSETS = {
    "Rules": [
        "rules/LDVH-WORKSPACE-ENTRY.md",
        "rules/LDVH-MAINTAINER-ENTRY.md",
    ],
    "Hook": [
        "hooks/ldvh-hooks.yaml",
    ],
}
DEPLOYMENT_ENTRIES_REQUIRED_ASSET_METADATA = {
    "rules/LDVH-WORKSPACE-ENTRY.md": {
        "id": "ldvh-workspace-entry",
        "type": "rule",
        "status": "active",
        "canonical_path": "rules/LDVH-WORKSPACE-ENTRY.md",
    },
    "rules/LDVH-MAINTAINER-ENTRY.md": {
        "id": "ldvh-maintainer-entry",
        "type": "rule",
        "status": "active",
        "canonical_path": "rules/LDVH-MAINTAINER-ENTRY.md",
    },
    "hooks/ldvh-hooks.yaml": {
        "id": "ldvh-hook-registry",
        "type": "hook",
        "status": "active",
        "canonical_path": "hooks/ldvh-hooks.yaml",
    },
}
DEPLOYMENT_ENTRIES_REQUIRED_METADATA_FIELDS = [
    "id",
    "type",
    "status",
    "canonical_path",
    "source_specs",
    "consumption_scenarios",
    "inputs",
    "outputs",
    "handoff",
    "verification",
    "sync_triggers",
    "deprecation",
]
DEPLOYMENT_ENTRIES_FORBIDDEN_TYPES = {"Code", "Web", "CLI", "MCP", "Command", "CI", "文档"}


def deployment_entries_fixed_asset_section(text):
    marker = "## 2. LDVH 能力资产"
    start = text.find(marker)
    if start < 0:
        return ""
    lines = text[start:].splitlines()
    section = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            in_table = True
            section.append(line)
            continue
        if in_table:
            break
        section.append(line)
    return "\n".join(section)


def deployment_entries_asset_metadata(text):
    def normalize_metadata_line(line):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            uncommented = stripped[1:]
            if uncommented.startswith(" "):
                uncommented = uncommented[1:]
            return uncommented
        return line

    in_yaml = False
    block_lines = []
    for line in text.splitlines():
        normalized_line = normalize_metadata_line(line)
        stripped = normalized_line.strip()
        if not in_yaml and stripped in {"```yaml", "```yml"}:
            in_yaml = True
            block_lines = []
            continue
        if in_yaml and stripped == "```":
            try:
                data = yaml.safe_load("\n".join(block_lines)) or {}
            except yaml.YAMLError:
                return None
            if isinstance(data, dict) and isinstance(data.get("ldvh_asset"), dict):
                return data["ldvh_asset"]
            in_yaml = False
            block_lines = []
            continue
        if in_yaml:
            block_lines.append(normalized_line)
    return None


def deployment_entries_check_asset_metadata(root, asset_path_raw):
    asset_path = root / asset_path_raw
    if not asset_path.exists():
        return []

    issues = []
    text = asset_path.read_text(encoding="utf-8")
    metadata = None
    if asset_path.suffix in {".yaml", ".yml"}:
        try:
            data = yaml.safe_load(text) or {}
        except yaml.YAMLError:
            data = {}
        if isinstance(data, dict) and isinstance(data.get("ldvh_asset"), dict):
            metadata = data["ldvh_asset"]
    if metadata is None:
        metadata = deployment_entries_asset_metadata(text)
    if metadata is None:
        issues.append(Issue(asset_path, 1, f"固定能力资产缺少 ldvh_asset 自登记元信息: {asset_path_raw}", code="DEPLOYMENT_ENTRIES_ASSET_METADATA_MISSING"))
        return issues

    for field in DEPLOYMENT_ENTRIES_REQUIRED_METADATA_FIELDS:
        value = metadata.get(field)
        if value in (None, "", []):
            issues.append(Issue(asset_path, 1, f"固定能力资产登记缺少字段 {field}: {asset_path_raw}", code="DEPLOYMENT_ENTRIES_ASSET_METADATA_FIELD_MISSING"))

    expected = DEPLOYMENT_ENTRIES_REQUIRED_ASSET_METADATA.get(asset_path_raw, {})
    for field, expected_value in expected.items():
        if metadata.get(field) != expected_value:
            issues.append(Issue(asset_path, 1, f"固定能力资产登记字段 {field} 应为 {expected_value}: {asset_path_raw}", code="DEPLOYMENT_ENTRIES_ASSET_METADATA_MISMATCH"))

    return issues


def deployment_entries_check(root=None):
    root = Path(root) if root is not None else PROJECT_ROOT
    spec_path = root / DEPLOYMENT_ENTRIES_SPEC_PATH
    issues = []

    if not spec_path.exists():
        issues.append(Issue(spec_path, 1, f"缺少 LDVH 能力资产定义规范: {DEPLOYMENT_ENTRIES_SPEC_PATH}", code="DEPLOYMENT_ENTRIES_SPEC_MISSING"))
        spec_text = ""
    else:
        spec_text = spec_path.read_text(encoding="utf-8")

    for entry_type, expected_paths in DEPLOYMENT_ENTRIES_REQUIRED_ASSETS.items():
        if isinstance(expected_paths, str):
            expected_paths = [expected_paths]
        if spec_text and entry_type not in spec_text:
            issues.append(Issue(spec_path, 1, f"LDVH 能力资产定义缺少必备资产类型: {entry_type}", code="DEPLOYMENT_ENTRIES_REQUIRED_TYPE_MISSING"))
        for expected_path in expected_paths:
            if spec_text and expected_path not in spec_text:
                issues.append(Issue(spec_path, 1, f"LDVH 能力资产定义缺少必备资产路径: {expected_path}", code="DEPLOYMENT_ENTRIES_REQUIRED_ASSET_MISMATCH"))
            if not (root / expected_path).exists():
                issues.append(Issue(root / expected_path, 1, f"缺少必备 LDVH 能力资产: {expected_path}", code="DEPLOYMENT_ENTRIES_REQUIRED_ASSET_MISSING"))
            issues.extend(deployment_entries_check_asset_metadata(root, expected_path))

    fixed_asset_section = deployment_entries_fixed_asset_section(spec_text)
    for forbidden_type in DEPLOYMENT_ENTRIES_FORBIDDEN_TYPES:
        forbidden_pattern = f"| {forbidden_type} |"
        if fixed_asset_section and forbidden_pattern in fixed_asset_section:
            issues.append(Issue(spec_path, 1, f"不得将支撑能力写成 Rules、Skill、Agent、Hook 同级文本能力资产类型: {forbidden_type}", code="DEPLOYMENT_ENTRIES_FORBIDDEN_TYPE"))

    for ai_entry_path_raw in DEPLOYMENT_ENTRIES_AI_ENTRY_PATHS:
        ai_entry_path = root / ai_entry_path_raw
        if not ai_entry_path.exists():
            issues.append(Issue(ai_entry_path, 1, f"缺少 Rules 入口: {ai_entry_path_raw}", code="DEPLOYMENT_ENTRIES_AI_ENTRY_MISSING"))
            continue
        ai_entry_text = ai_entry_path.read_text(encoding="utf-8")
        if DEPLOYMENT_ENTRIES_SPEC_PATH not in ai_entry_text:
            issues.append(Issue(ai_entry_path, 1, f"Rules 入口未引用 LDVH 能力资产定义规范: {DEPLOYMENT_ENTRIES_SPEC_PATH}", code="DEPLOYMENT_ENTRIES_AI_ENTRY_REF_MISSING"))

    return issues


def deployment_entries_main(root=None):
    issues = deployment_entries_check(root)
    if issues:
        print(f"LDVH 能力资产检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("LDVH 能力资产检查通过。")
    return 0
