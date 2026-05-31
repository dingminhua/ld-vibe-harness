#!/usr/bin/env python3
"""ADR Index Tool - 动态生成 ADR 索引供 AI 使用

依据 specs/12.01-Tools辅助规范.md，属于 Tools 辅助层能力实现。
不生成实际索引文件，运行时动态生成索引结果返回。

用法:
    python3 adr_index.py [command] [options]

命令:
    list                列出所有 ADR 摘要
    search <keyword>    按关键词搜索 ADR
    status <status>     按状态筛选 ADR (proposed/accepted/deprecated/superseded)
    show <adr_id>       显示单个 ADR 详情
    stats               显示 ADR 状态统计
    related <spec>       显示与指定 specs 文件关联的 ADR
"""

import sys
import os
import glob
import yaml
from pathlib import Path
from datetime import datetime


ADRS_DIR = Path(__file__).resolve().parent.parent.parent / "ldvh-base" / "adrs"


def load_adr(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            return None
        data["_file"] = filepath.name
        data["_path"] = str(filepath)
        return data
    except Exception:
        return None


def load_all_adrs():
    if not ADRS_DIR.exists():
        return []
    adrs = []
    for filepath in sorted(ADRS_DIR.glob("adr-*.yaml")):
        adr = load_adr(filepath)
        if adr:
            adrs.append(adr)
    return adrs


def fmt_date(val):
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    return str(val) if val else "N/A"


def cmd_list(adrs):
    if not adrs:
        print("暂无 ADR 记录。")
        return
    print(f"{'ID':<12} {'状态':<14} {'标题':<40} {'创建日期'}")
    print("-" * 85)
    for adr in adrs:
        adr_id = adr.get("adr_id", adr.get("_file", "N/A"))
        status = adr.get("status", "N/A")
        title = adr.get("title", "N/A")
        if len(title) > 38:
            title = title[:36] + ".."
        created = fmt_date(adr.get("created"))
        print(f"{adr_id:<12} {status:<14} {title:<40} {created}")


def cmd_search(adrs, keyword):
    keyword_lower = keyword.lower()
    matched = []
    for adr in adrs:
        searchable = " ".join([
            str(adr.get("title", "")),
            str(adr.get("context", "")),
            str(adr.get("decision", "")),
            str(adr.get("consequences", "")),
            str(adr.get("adr_id", "")),
        ]).lower()
        if keyword_lower in searchable:
            matched.append(adr)
    if not matched:
        print(f"未找到包含 '{keyword}' 的 ADR。")
        return
    print(f"找到 {len(matched)} 个匹配的 ADR：\n")
    cmd_list(matched)


def cmd_status(adrs, status):
    matched = [a for a in adrs if a.get("status") == status]
    if not matched:
        print(f"未找到状态为 '{status}' 的 ADR。")
        return
    print(f"状态为 '{status}' 的 ADR 共 {len(matched)} 个：\n")
    cmd_list(matched)


def cmd_show(adrs, adr_id):
    for adr in adrs:
        if adr.get("adr_id") == adr_id or adr.get("_file", "").startswith(f"adr-{adr_id}"):
            print(f"文件: {adr['_file']}")
            print(f"路径: {adr['_path']}")
            print(f"ID: {adr.get('adr_id', 'N/A')}")
            print(f"标题: {adr.get('title', 'N/A')}")
            print(f"状态: {adr.get('status', 'N/A')}")
            print(f"创建: {fmt_date(adr.get('created'))}")
            print(f"更新: {fmt_date(adr.get('updated'))}")
            print(f"\n背景:\n{adr.get('context', 'N/A')}")
            print(f"\n决策:\n{adr.get('decision', 'N/A')}")
            print(f"\n影响:\n{adr.get('consequences', 'N/A')}")
            affects = adr.get("affects", [])
            if affects:
                print(f"\n影响文件:")
                for a in affects:
                    print(f"  - {a}")
            related = adr.get("related_rules", [])
            if related:
                print(f"\n关联规范:")
                for r in related:
                    print(f"  - {r}")
            superseded_by = adr.get("superseded_by")
            if superseded_by:
                print(f"\n被推翻: {superseded_by}")
            supersedes = adr.get("supersedes")
            if supersedes:
                print(f"\n推翻: {supersedes}")
            return
    print(f"未找到 ADR: {adr_id}")


def cmd_stats(adrs):
    status_counts = {}
    for adr in adrs:
        s = adr.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
    print(f"ADR 总数: {len(adrs)}")
    print()
    for status in ["proposed", "accepted", "deprecated", "superseded"]:
        count = status_counts.get(status, 0)
        print(f"  {status}: {count}")
    other = sum(v for k, v in status_counts.items() if k not in ["proposed", "accepted", "deprecated", "superseded"])
    if other:
        print(f"  其他: {other}")


def cmd_related(adrs, spec_path):
    matched = []
    for adr in adrs:
        affects = adr.get("affects", [])
        related_rules = adr.get("related_rules", [])
        all_refs = [str(r) for r in affects + related_rules]
        if any(spec_path in ref for ref in all_refs):
            matched.append(adr)
    if not matched:
        print(f"未找到与 '{spec_path}' 关联的 ADR。")
        return
    print(f"与 '{spec_path}' 关联的 ADR 共 {len(matched)} 个：\n")
    cmd_list(matched)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]
    adrs = load_all_adrs()

    if command == "list":
        cmd_list(adrs)
    elif command == "search":
        if len(sys.argv) < 3:
            print("用法: python3 adr_index.py search <keyword>")
            sys.exit(1)
        cmd_search(adrs, sys.argv[2])
    elif command == "status":
        if len(sys.argv) < 3:
            print("用法: python3 adr_index.py status <proposed|accepted|deprecated|superseded>")
            sys.exit(1)
        cmd_status(adrs, sys.argv[2])
    elif command == "show":
        if len(sys.argv) < 3:
            print("用法: python3 adr_index.py show <adr_id>")
            sys.exit(1)
        cmd_show(adrs, sys.argv[2])
    elif command == "stats":
        cmd_stats(adrs)
    elif command == "related":
        if len(sys.argv) < 3:
            print("用法: python3 adr_index.py related <spec_path>")
            sys.exit(1)
        cmd_related(adrs, sys.argv[2])
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
