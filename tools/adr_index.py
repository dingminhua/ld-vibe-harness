#!/usr/bin/env python3
"""ADR Index Tool - 动态生成 ADR 索引供 AI 使用

依据 specs/12.01-Tools辅助规范.md，属于 Tools 辅助层能力实现。
读取命令不生成实际索引文件，运行时动态生成索引结果返回。
写入命令必须携带显式 Human Gate 确认参数，仅执行已授权、可机械化、可校验的写入。

用法:
    python3 adr_index.py [command] [options]

命令:
    list                列出所有 ADR 摘要
    search <keyword>    按关键词搜索 ADR
    status <status>     按状态筛选 ADR (proposed/accepted/deprecated/superseded/rejected)
    show <adr_id>       显示单个 ADR 详情
    stats               显示 ADR 状态统计
    validate            校验所有 ADR 实例的字段完整性与状态合法性
    related <spec>       显示与指定 specs 文件关联的 ADR
    next-id             计算下一个 ADR ID
    draft               生成 ADR YAML 草案并输出到 stdout
    create              经授权后创建 ADR YAML
    transition          经授权后执行 ADR 状态流转
    link-rule           经授权后更新 ADR related_rules
    deprecate           经授权后废弃 ADR
    supersede           经授权后创建替代 ADR 并更新旧 ADR
"""

import argparse
import sys
import re
import yaml
from pathlib import Path
from datetime import datetime


ADRS_DIR = Path(__file__).resolve().parent.parent / "ldvh-base" / "adrs"
CHANGES_DIR = Path(__file__).resolve().parent.parent / "ldvh-base" / "changes"
VALID_STATUSES = {"proposed", "accepted", "deprecated", "superseded", "rejected"}
TERMINAL_STATUSES = {"deprecated", "superseded", "rejected"}
ALLOWED_TRANSITIONS = {
    "proposed": {"accepted", "rejected"},
    "accepted": {"deprecated", "superseded"},
    "deprecated": set(),
    "superseded": set(),
    "rejected": set(),
}
REQUIRED_FIELDS = ["id", "type", "title", "status", "created", "updated", "date", "context", "decision", "consequences"]
LIST_FIELDS = {"affects", "related_objects", "related_rules"}
FILENAME_PATTERN = re.compile(r"^adr-\d{4}-.+\.yaml$")
ID_PATTERN = re.compile(r"^adr-(\d{4})$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ToolError(Exception):
    pass


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


def today():
    return datetime.now().strftime("%Y-%m-%d")


def parse_list(values):
    if not values:
        return []
    items = []
    for value in values:
        for item in str(value).split(","):
            item = item.strip()
            if item:
                items.append(item)
    return items


def ensure_authorized(args):
    if not getattr(args, "human_gate_confirmed", False):
        raise ToolError("写入被拒绝：缺少 --human-gate-confirmed。Tools 不生成授权，必须由 Human Gate 先确认。")
    if not getattr(args, "confirmed_by", None):
        raise ToolError("写入被拒绝：缺少 --confirmed-by。")
    if not getattr(args, "confirmation_context", None):
        raise ToolError("写入被拒绝：缺少 --confirmation-context。")


def clean_runtime_fields(adr):
    return {k: v for k, v in adr.items() if not k.startswith("_")}


def adr_number(adr_id):
    match = ID_PATTERN.match(str(adr_id))
    if not match:
        return None
    return int(match.group(1))


def next_adr_id(adrs):
    max_num = 0
    for adr in adrs:
        num = adr_number(adr.get("id", ""))
        if num and num > max_num:
            max_num = num
    return f"adr-{max_num + 1:04d}"


def adr_path(adr_id, slug):
    if not ID_PATTERN.match(adr_id):
        raise ToolError(f"ADR ID 不合法: {adr_id}")
    if not SLUG_PATTERN.match(slug):
        raise ToolError("slug 不合法：必须使用小写英文、数字和短横线，例如 use-yaml-for-adr。")
    return ADRS_DIR / f"{adr_id}-{slug}.yaml"


def find_adr(adrs, adr_id):
    for adr in adrs:
        if adr.get("id") == adr_id:
            return adr
    raise ToolError(f"未找到 ADR: {adr_id}")


def validate_adr_data(adr, file_name):
    issues = []
    for field in REQUIRED_FIELDS:
        if not adr.get(field):
            issues.append(f"必填字段缺失: {field}")
    status = adr.get("status", "")
    if status and status not in VALID_STATUSES:
        issues.append(f"状态不合法: {status}，合法值: {', '.join(sorted(VALID_STATUSES))}")
    if status == "superseded" and not adr.get("superseded_by"):
        issues.append("状态为 superseded 时 superseded_by 为必填")
    if status != "superseded" and adr.get("superseded_by"):
        issues.append("仅 status 为 superseded 时允许填写 superseded_by")
    adr_type = adr.get("type", "")
    if adr_type and adr_type != "adr":
        issues.append(f"type 字段应为 adr，实际为: {adr_type}")
    adr_id = adr.get("id", "")
    if adr_id and not ID_PATTERN.match(str(adr_id)):
        issues.append(f"id 字段不匹配 adr-{{NNNN}} 格式: {adr_id}")
    if not FILENAME_PATTERN.match(file_name):
        issues.append(f"文件命名不匹配 adr-{{NNNN}}-*.yaml 格式: {file_name}")
    if adr_id and FILENAME_PATTERN.match(file_name) and not file_name.startswith(f"{adr_id}-"):
        issues.append(f"文件名编号与 id 不一致: {file_name} / {adr_id}")
    for field in LIST_FIELDS:
        if field in adr and adr.get(field) is None:
            issues.append(f"{field} 不得为 null")
        if field in adr and adr.get(field) is not None and not isinstance(adr.get(field), list):
            issues.append(f"{field} 必须为列表")
    return issues


def ensure_valid_adr(adr, file_name):
    issues = validate_adr_data(adr, file_name)
    if issues:
        raise ToolError("写入前校验失败：\n" + "\n".join(f"  - {issue}" for issue in issues))


def dump_yaml(data):
    ordered = {}
    for field in [
        "id", "type", "title", "status", "created", "updated", "date", "context", "decision", "consequences",
        "alternatives", "affects", "related_objects", "related_rules", "superseded_by",
    ]:
        if field in data:
            ordered[field] = data[field]
    for key, value in data.items():
        if key not in ordered and not key.startswith("_"):
            ordered[key] = value
    return yaml.safe_dump(ordered, allow_unicode=True, sort_keys=False)


def write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(data), encoding="utf-8")


def build_adr(args, adr_id):
    date_value = args.date or today()
    data = {
        "id": adr_id,
        "type": "adr",
        "title": args.title,
        "status": "proposed",
        "created": date_value,
        "updated": date_value,
        "date": date_value,
        "context": args.context,
        "decision": args.decision,
        "consequences": args.consequences,
        "affects": parse_list(getattr(args, "affects", [])),
        "related_objects": parse_list(getattr(args, "related_objects", [])),
        "related_rules": parse_list(getattr(args, "related_rules", [])),
    }
    if getattr(args, "alternatives", None):
        data["alternatives"] = args.alternatives
    return data


def change_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def write_change(title, context, decision, consequences, affects, confirmed_by, confirmation_context):
    CHANGES_DIR.mkdir(parents=True, exist_ok=True)
    path = CHANGES_DIR / f"{change_id()}.yaml"
    counter = 1
    while path.exists():
        path = CHANGES_DIR / f"{change_id()}-{counter}.yaml"
        counter += 1
    date_value = today()
    data = {
        "type": "change",
        "title": title,
        "author": "tool:adr_index.py",
        "status": "done",
        "created": date_value,
        "updated": date_value,
        "context": context,
        "decision": decision,
        "consequences": consequences,
        "affects": affects,
        "human_gate": {
            "required": True,
            "confirmed_by": confirmed_by,
            "confirmation_context": confirmation_context,
        },
    }
    write_yaml(path, data)
    return path


def maybe_write_change(args, title, context, decision, consequences, affects):
    if not getattr(args, "write_change", False):
        return None
    return write_change(title, context, decision, consequences, affects, args.confirmed_by, args.confirmation_context)


def transition_allowed(current, target):
    return target in ALLOWED_TRANSITIONS.get(current, set())


def update_adr_file(adr, updates):
    path = Path(adr["_path"])
    data = clean_runtime_fields(adr)
    data.update(updates)
    ensure_valid_adr(data, path.name)
    write_yaml(path, data)
    return path


def cmd_list(adrs):
    if not adrs:
        print("暂无 ADR 记录。")
        return
    print(f"{'ID':<12} {'状态':<14} {'标题':<40} {'创建日期'}")
    print("-" * 85)
    for adr in adrs:
        adr_id = adr.get("id", adr.get("_file", "N/A"))
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
            str(adr.get("id", "")),
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
        if adr.get("id") == adr_id or adr.get("_file", "").startswith(f"adr-{adr_id}"):
            print(f"文件: {adr['_file']}")
            print(f"路径: {adr['_path']}")
            print(f"ID: {adr.get('id', 'N/A')}")
            print(f"类型: {adr.get('type', 'N/A')}")
            print(f"标题: {adr.get('title', 'N/A')}")
            print(f"状态: {adr.get('status', 'N/A')}")
            print(f"决策日期: {fmt_date(adr.get('date'))}")
            print(f"创建: {fmt_date(adr.get('created'))}")
            print(f"更新: {fmt_date(adr.get('updated'))}")
            print(f"\n背景:\n{adr.get('context', 'N/A')}")
            print(f"\n决策:\n{adr.get('decision', 'N/A')}")
            print(f"\n影响:\n{adr.get('consequences', 'N/A')}")
            alternatives = adr.get("alternatives")
            if alternatives:
                print(f"\n替代方案:")
                if isinstance(alternatives, list):
                    for alt in alternatives:
                        print(f"  - {alt}")
                else:
                    print(f"  {alternatives}")
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
            return
    print(f"未找到 ADR: {adr_id}")


def cmd_stats(adrs):
    status_counts = {}
    for adr in adrs:
        s = adr.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
    print(f"ADR 总数: {len(adrs)}")
    print()
    for status in ["proposed", "accepted", "deprecated", "superseded", "rejected"]:
        count = status_counts.get(status, 0)
        print(f"  {status}: {count}")
    other = sum(v for k, v in status_counts.items() if k not in ["proposed", "accepted", "deprecated", "superseded", "rejected"])
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


def cmd_validate(adrs):
    if not adrs:
        print("暂无 ADR 记录，跳过校验。")
        return
    total = len(adrs)
    passed = 0
    failed = 0
    for adr in adrs:
        file_name = adr.get("_file", "N/A")
        issues = validate_adr_data(adr, file_name)
        if issues:
            failed += 1
            print(f"[不合规] {file_name}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            passed += 1
    print()
    print(f"校验依据: specs/21.06-Contract.md §八字段契约")
    print(f"校验对象: {total} 个 ADR 实例")
    print(f"校验结果: 通过 {passed}，不合规 {failed}")


def cmd_next_id(adrs):
    print(next_adr_id(adrs))


def cmd_draft(args, adrs):
    adr_id = args.id or next_adr_id(adrs)
    data = build_adr(args, adr_id)
    file_name = f"{adr_id}-{args.slug}.yaml"
    ensure_valid_adr(data, file_name)
    print(dump_yaml(data), end="")


def cmd_create(args, adrs):
    ensure_authorized(args)
    adr_id = args.id or next_adr_id(adrs)
    data = build_adr(args, adr_id)
    path = adr_path(adr_id, args.slug)
    if path.exists():
        raise ToolError(f"写入被拒绝：目标文件已存在 {path}")
    ensure_valid_adr(data, path.name)
    write_yaml(path, data)
    change_path = maybe_write_change(
        args,
        f"创建 ADR {adr_id}",
        args.confirmation_context,
        f"创建 ADR: {data['title']}",
        "ADR 实例已创建为 proposed，后续 accepted 仍需单独 Human Gate。",
        [str(path.relative_to(path.parents[2])) if len(path.parents) > 2 else str(path)],
    )
    print(f"已创建 ADR: {path}")
    if change_path:
        print(f"已创建 Change: {change_path}")


def cmd_transition(args, adrs):
    ensure_authorized(args)
    adr = find_adr(adrs, args.adr_id)
    current = adr.get("status")
    target = args.status
    if current in TERMINAL_STATUSES:
        raise ToolError(f"状态流转被拒绝：{current} 为终态，不得重开。")
    if not transition_allowed(current, target):
        raise ToolError(f"状态流转被拒绝：{current} → {target} 非法。")
    updates = {"status": target, "updated": today()}
    if target == "superseded":
        if not args.superseded_by:
            raise ToolError("状态流转被拒绝：accepted → superseded 必须提供 --superseded-by。")
        updates["superseded_by"] = args.superseded_by
    path = update_adr_file(adr, updates)
    change_path = maybe_write_change(
        args,
        f"更新 ADR 状态 {args.adr_id}",
        args.confirmation_context,
        f"ADR 状态从 {current} 变更为 {target}。",
        "状态流转已写入 ADR YAML，终态 ADR 不得重开。",
        [str(path)],
    )
    print(f"已更新 ADR 状态: {args.adr_id} {current} → {target}")
    if change_path:
        print(f"已创建 Change: {change_path}")


def cmd_link_rule(args, adrs):
    ensure_authorized(args)
    adr = find_adr(adrs, args.adr_id)
    rules = adr.get("related_rules") or []
    if not isinstance(rules, list):
        raise ToolError("related_rules 当前不是列表，拒绝写入。")
    changed = False
    for rule in parse_list(args.rule):
        if rule not in rules:
            rules.append(rule)
            changed = True
    if not changed:
        print("related_rules 无变化。")
        return
    path = update_adr_file(adr, {"related_rules": rules, "updated": today()})
    change_path = maybe_write_change(
        args,
        f"更新 ADR 关联规则 {args.adr_id}",
        args.confirmation_context,
        f"更新 ADR {args.adr_id} 的 related_rules。",
        "ADR 关联规则字段已回写。",
        [str(path)],
    )
    print(f"已更新 related_rules: {args.adr_id}")
    if change_path:
        print(f"已创建 Change: {change_path}")


def cmd_deprecate(args, adrs):
    ensure_authorized(args)
    adr = find_adr(adrs, args.adr_id)
    current = adr.get("status")
    if not transition_allowed(current, "deprecated"):
        raise ToolError(f"废弃被拒绝：{current} → deprecated 非法。")
    context = str(adr.get("context", ""))
    consequences = str(adr.get("consequences", ""))
    addition = f"废弃原因：{args.reason}"
    target_field = args.reason_field
    updates = {"status": "deprecated", "updated": today()}
    if target_field == "context":
        updates["context"] = f"{context}\n\n{addition}" if context else addition
    else:
        updates["consequences"] = f"{consequences}\n\n{addition}" if consequences else addition
    path = update_adr_file(adr, updates)
    change_path = maybe_write_change(
        args,
        f"废弃 ADR {args.adr_id}",
        args.confirmation_context,
        f"ADR {args.adr_id} 状态变更为 deprecated。",
        args.reason,
        [str(path)],
    )
    print(f"已废弃 ADR: {args.adr_id}")
    if change_path:
        print(f"已创建 Change: {change_path}")


def cmd_supersede(args, adrs):
    ensure_authorized(args)
    old_adr = find_adr(adrs, args.old_adr_id)
    old_status = old_adr.get("status")
    if not transition_allowed(old_status, "superseded"):
        raise ToolError(f"推翻被拒绝：{old_status} → superseded 非法。")
    new_id = args.id or next_adr_id(adrs)
    new_adr = build_adr(args, new_id)
    related_objects = new_adr.get("related_objects", [])
    if args.old_adr_id not in related_objects:
        related_objects.append(args.old_adr_id)
    new_adr["related_objects"] = related_objects
    new_path = adr_path(new_id, args.slug)
    if new_path.exists():
        raise ToolError(f"写入被拒绝：目标文件已存在 {new_path}")
    ensure_valid_adr(new_adr, new_path.name)
    write_yaml(new_path, new_adr)
    old_path = update_adr_file(old_adr, {"status": "superseded", "superseded_by": new_id, "updated": today()})
    change_path = maybe_write_change(
        args,
        f"推翻 ADR {args.old_adr_id}",
        args.confirmation_context,
        f"创建替代 ADR {new_id}，并将 {args.old_adr_id} 标记为 superseded。",
        "旧 ADR 已保留历史，新 ADR 以 proposed 状态承接重新决策。",
        [str(old_path), str(new_path)],
    )
    print(f"已创建替代 ADR: {new_path}")
    print(f"已更新旧 ADR: {args.old_adr_id} → superseded_by {new_id}")
    if change_path:
        print(f"已创建 Change: {change_path}")


def add_authorization_args(parser):
    parser.add_argument("--human-gate-confirmed", action="store_true")
    parser.add_argument("--confirmed-by")
    parser.add_argument("--confirmation-context")
    parser.add_argument("--write-change", action="store_true")


def add_adr_content_args(parser):
    parser.add_argument("--id")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--decision", required=True)
    parser.add_argument("--consequences", required=True)
    parser.add_argument("--date")
    parser.add_argument("--alternatives")
    parser.add_argument("--affects", action="append")
    parser.add_argument("--related-objects", action="append")
    parser.add_argument("--related-rules", action="append")


def build_parser():
    parser = argparse.ArgumentParser(description="ADR Tools")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list")
    search = sub.add_parser("search")
    search.add_argument("keyword")
    status = sub.add_parser("status")
    status.add_argument("status")
    show = sub.add_parser("show")
    show.add_argument("adr_id")
    sub.add_parser("stats")
    sub.add_parser("validate")
    related = sub.add_parser("related")
    related.add_argument("spec_path")
    sub.add_parser("next-id")
    draft = sub.add_parser("draft")
    add_adr_content_args(draft)
    create = sub.add_parser("create")
    add_adr_content_args(create)
    add_authorization_args(create)
    transition = sub.add_parser("transition")
    transition.add_argument("adr_id")
    transition.add_argument("status", choices=sorted(VALID_STATUSES))
    transition.add_argument("--superseded-by")
    add_authorization_args(transition)
    link_rule = sub.add_parser("link-rule")
    link_rule.add_argument("adr_id")
    link_rule.add_argument("--rule", action="append", required=True)
    add_authorization_args(link_rule)
    deprecate = sub.add_parser("deprecate")
    deprecate.add_argument("adr_id")
    deprecate.add_argument("--reason", required=True)
    deprecate.add_argument("--reason-field", choices=["context", "consequences"], default="consequences")
    add_authorization_args(deprecate)
    supersede = sub.add_parser("supersede")
    supersede.add_argument("old_adr_id")
    add_adr_content_args(supersede)
    add_authorization_args(supersede)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(0)
    adrs = load_all_adrs()
    try:
        if args.command == "list":
            cmd_list(adrs)
        elif args.command == "search":
            cmd_search(adrs, args.keyword)
        elif args.command == "status":
            cmd_status(adrs, args.status)
        elif args.command == "show":
            cmd_show(adrs, args.adr_id)
        elif args.command == "stats":
            cmd_stats(adrs)
        elif args.command == "validate":
            cmd_validate(adrs)
        elif args.command == "related":
            cmd_related(adrs, args.spec_path)
        elif args.command == "next-id":
            cmd_next_id(adrs)
        elif args.command == "draft":
            cmd_draft(args, adrs)
        elif args.command == "create":
            cmd_create(args, adrs)
        elif args.command == "transition":
            cmd_transition(args, adrs)
        elif args.command == "link-rule":
            cmd_link_rule(args, adrs)
        elif args.command == "deprecate":
            cmd_deprecate(args, adrs)
        elif args.command == "supersede":
            cmd_supersede(args, adrs)
        else:
            raise ToolError(f"未知命令: {args.command}")
    except ToolError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
