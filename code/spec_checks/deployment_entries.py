"""LDVH deployment entry asset checks."""

from pathlib import Path

from .common import Issue


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT_ENTRIES_AI_ENTRY_PATH = "rules/LDVH-AI-ENTRY.md"
DEPLOYMENT_ENTRIES_SPEC_PATH = "specs/04.02-LDVH能力资产与落地保障规范.md"
DEPLOYMENT_ENTRIES_REQUIRED_ASSETS = {
    "Rules": "rules/LDVH-AI-ENTRY.md",
    "Skill": "skills/ldvh-spec-change-check/SKILL.md",
    "Agent": "agents/ldvh-spec-semantic-review.md",
    "Hook": "hooks/ldvh-lifecycle-check.md",
}
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


def deployment_entries_check(root=None):
    root = Path(root) if root is not None else PROJECT_ROOT
    spec_path = root / DEPLOYMENT_ENTRIES_SPEC_PATH
    ai_entry_path = root / DEPLOYMENT_ENTRIES_AI_ENTRY_PATH
    issues = []

    if not spec_path.exists():
        issues.append(Issue(spec_path, 1, f"缺少 LDVH 能力资产定义规范: {DEPLOYMENT_ENTRIES_SPEC_PATH}", code="DEPLOYMENT_ENTRIES_SPEC_MISSING"))
        spec_text = ""
    else:
        spec_text = spec_path.read_text(encoding="utf-8")

    for entry_type, expected_path in DEPLOYMENT_ENTRIES_REQUIRED_ASSETS.items():
        if spec_text and entry_type not in spec_text:
            issues.append(Issue(spec_path, 1, f"LDVH 能力资产定义缺少必备资产类型: {entry_type}", code="DEPLOYMENT_ENTRIES_REQUIRED_TYPE_MISSING"))
        if spec_text and expected_path not in spec_text:
            issues.append(Issue(spec_path, 1, f"LDVH 能力资产定义缺少必备资产路径: {expected_path}", code="DEPLOYMENT_ENTRIES_REQUIRED_ASSET_MISMATCH"))
        if not (root / expected_path).exists():
            issues.append(Issue(root / expected_path, 1, f"缺少必备 LDVH 能力资产: {expected_path}", code="DEPLOYMENT_ENTRIES_REQUIRED_ASSET_MISSING"))

    fixed_asset_section = deployment_entries_fixed_asset_section(spec_text)
    for forbidden_type in DEPLOYMENT_ENTRIES_FORBIDDEN_TYPES:
        forbidden_pattern = f"| {forbidden_type} |"
        if fixed_asset_section and forbidden_pattern in fixed_asset_section:
            issues.append(Issue(spec_path, 1, f"不得将支撑能力写成 Rules、Skill、Agent、Hook 同级文本能力资产类型: {forbidden_type}", code="DEPLOYMENT_ENTRIES_FORBIDDEN_TYPE"))

    if not ai_entry_path.exists():
        issues.append(Issue(ai_entry_path, 1, f"缺少 Rules 统一入口: {DEPLOYMENT_ENTRIES_AI_ENTRY_PATH}", code="DEPLOYMENT_ENTRIES_AI_ENTRY_MISSING"))
    else:
        ai_entry_text = ai_entry_path.read_text(encoding="utf-8")
        if DEPLOYMENT_ENTRIES_SPEC_PATH not in ai_entry_text:
            issues.append(Issue(ai_entry_path, 1, f"Rules 统一入口未引用 LDVH 能力资产定义规范: {DEPLOYMENT_ENTRIES_SPEC_PATH}", code="DEPLOYMENT_ENTRIES_AI_ENTRY_REF_MISSING"))

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
