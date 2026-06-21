#!/usr/bin/env python3
"""批量修补 ldvh-base YAML 文件：将长文本字段转为 YAML 块标量 | 格式。不改变内容，只改写法。"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


# 05.02 工作模型字段内容与格式规范：长文本字段定义
LONG_TEXT_FIELDS = {
    "workarea": {"description", "scope", "constraints", "archive_reason"},
    "workcase": {"description", "success_criteria", "verification_evidence", "closure_evidence"},
    "adr": {"context", "decision", "consequences"},
    "pitfall": {"symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"},
    "spark": {"description", "source_detail", "discard_reason"},
    "study": {"summary", "source_detail", "conclusion", "archive_reason"},
}


class LiteralStr(str):
    """强制 yaml.dump 使用块标量 | 的字符串类型。"""
    pass


def literal_str_representer(dumper: yaml.Dumper, data: LiteralStr) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")


yaml.add_representer(LiteralStr, literal_str_representer)


def fix_file(path: Path) -> bool:
    """修补单个文件，返回是否做了修改。"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        return False

    obj_type = data.get("type")
    if obj_type not in LONG_TEXT_FIELDS:
        return False

    fields = LONG_TEXT_FIELDS[obj_type]
    changed = False

    for field in fields:
        value = data.get(field)
        if not isinstance(value, str) or not value:
            continue
        # 只修补包含换行或冒号的长文本
        if "\n" not in value and ": " not in value:
            continue
        # 转为 LiteralStr 强制块标量
        data[field] = LiteralStr(value)
        changed = True

    if not changed:
        return False

    new_content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False, width=1000)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def main() -> int:
    base_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ldvh-base")
    fixed = 0
    for yaml_file in sorted(base_dir.rglob("*.yaml")):
        if fix_file(yaml_file):
            print(f"已修补: {yaml_file}")
            fixed += 1
    print(f"\n共修补 {fixed} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
