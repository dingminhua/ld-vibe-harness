#!/usr/bin/env python3
"""LDVH 最小统一 CLI 入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import fact_cli
import fact_validate
import specs_validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_VERSION = "ldvh-cli/v1"


def build_status() -> dict:
    return {
        "metadata": {
            "tool": "tools/ldvh_cli.py",
            "contract_version": CONTRACT_VERSION,
            "source_of_truth": False,
        },
        "summary": {
            "status": "ready",
            "exit_code_contract": "0=success, 1=validation failure, 2=usage/input failure",
        },
        "commands": {
            "status": "输出统一 CLI 能力和 exit code 合同。",
            "landing plan": "包装 specs_validate.py landing-plan。",
            "landing apply": "包装 specs_validate.py landing-apply，要求 --plan 边界。",
            "landing repair": "包装 specs_validate.py landing-repair，要求 --plan 边界。",
            "landing verify": "包装 specs_validate.py landing-verify。",
            "landing review": "包装 specs_validate.py web-validate。",
            "facts list/show/search/stats": "包装 fact_cli.py 只读事实查询。",
            "facts validate": "包装 fact_validate.py。",
            "specs validate": "包装 specs_validate.py all。",
        },
        "write_guards": {
            "plan_required": ["landing apply", "landing repair"],
            "human_gate_source": "landing-plan/v1 human_gate.authorized and records",
            "boundary_source": "landing-plan/v1 write_targets",
        },
    }


def print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_status_text(payload: dict) -> None:
    print("LDVH CLI")
    print(f"合同版本: {payload['metadata']['contract_version']}")
    print(f"状态: {payload['summary']['status']}")
    print(f"Exit Code: {payload['summary']['exit_code_contract']}")
    print("命令树:")
    for command, description in payload["commands"].items():
        print(f"- {command}: {description}")


def cmd_status(args: argparse.Namespace) -> int:
    payload = build_status()
    if args.format == "json":
        print_json(payload)
    else:
        print_status_text(payload)
    return 0


def cmd_landing(args: argparse.Namespace) -> int:
    if args.landing_command == "plan":
        return specs_validate.landing_plan_main(args.workspace_root, args.format)
    if args.landing_command == "apply":
        return specs_validate.landing_apply_main(args.plan, args.patch, not args.write, args.format)
    if args.landing_command == "repair":
        return specs_validate.landing_repair_main(args.plan, args.patch, args.execute, args.format)
    if args.landing_command == "verify":
        return specs_validate.landing_verify_main(args.workspace_root, args.format)
    if args.landing_command == "review":
        return specs_validate.web_validate_main(args.workspace_root, args.format)
    return 2


def cmd_facts(args: argparse.Namespace) -> int:
    if args.facts_command == "list":
        return fact_cli.cmd_list(args)
    if args.facts_command == "show":
        return fact_cli.cmd_show(args)
    if args.facts_command == "search":
        return fact_cli.cmd_search(args)
    if args.facts_command == "stats":
        return fact_cli.cmd_stats(args)
    if args.facts_command == "validate":
        files, input_issues = fact_validate.collect_yaml_files(args.paths)
        issues = list(input_issues)
        has_input_parse_type_error = bool(input_issues)
        for path in files:
            file_issues, is_input_parse_type_error = fact_validate.validate_file(path)
            issues.extend(file_issues)
            has_input_parse_type_error = has_input_parse_type_error or is_input_parse_type_error
        error_count = sum(1 for issue in issues if issue.level == "error")
        if args.format == "json":
            fact_validate.print_json_result(fact_validate.build_tool_result(Path(",".join(args.paths)), len(files), issues))
        else:
            fact_validate.print_text_result(len(files), issues)
        if has_input_parse_type_error:
            return 2
        if error_count:
            return 1
        return 0
    return 2


def cmd_specs(args: argparse.Namespace) -> int:
    if args.specs_command == "validate":
        forwarded_args = [
            "all",
            *args.paths,
            "--root",
            args.root,
            "--specs-dir",
            args.specs_dir,
        ]
        if args.out:
            forwarded_args.extend(["--out", args.out])
        if args.fail_on_diagnostics:
            forwarded_args.append("--fail-on-diagnostics")
        return specs_validate.main(forwarded_args)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LDVH 最小统一 CLI：status、landing、facts、specs。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="输出统一 CLI 能力状态")
    status_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")

    landing_parser = subparsers.add_parser("landing", help="包装受控落地执行闭环能力")
    landing_subparsers = landing_parser.add_subparsers(dest="landing_command", required=True)
    landing_plan_parser = landing_subparsers.add_parser("plan", help="生成 landing-plan/v1 只读计划")
    landing_plan_parser.add_argument("--workspace-root", default=str(PROJECT_ROOT), help="工作区根目录，默认项目根")
    landing_plan_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")
    landing_apply_parser = landing_subparsers.add_parser("apply", help="执行 landing-plan 授权范围内的最小写入")
    landing_apply_parser.add_argument("--plan", required=True, help="landing-plan/v1 JSON 文件")
    landing_apply_parser.add_argument("--patch", required=True, help="target -> content JSON 文件，或包含 writes 对象的 JSON 文件")
    landing_apply_parser.add_argument("--write", action="store_true", help="执行真实写入；默认只 dry-run")
    landing_apply_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")
    landing_repair_parser = landing_subparsers.add_parser("repair", help="生成或执行授权范围内的最小候选修复")
    landing_repair_parser.add_argument("--plan", required=True, help="landing-plan/v1 JSON 文件")
    landing_repair_parser.add_argument("--patch", required=True, help="target -> content JSON 文件，或包含 repairs 对象的 JSON 文件")
    landing_repair_parser.add_argument("--execute", action="store_true", help="执行真实修复；默认只输出候选修复")
    landing_repair_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")
    landing_verify_parser = landing_subparsers.add_parser("verify", help="聚合验证结果并输出 review_needed 证据")
    landing_verify_parser.add_argument("--workspace-root", default=str(PROJECT_ROOT), help="工作区根目录，默认项目根")
    landing_verify_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")
    landing_review_parser = landing_subparsers.add_parser("review", help="生成 Web Validate 只读审核合同")
    landing_review_parser.add_argument("--workspace-root", default=str(PROJECT_ROOT), help="工作区根目录，默认项目根")
    landing_review_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")

    facts_parser = subparsers.add_parser("facts", help="包装事实模型能力")
    facts_subparsers = facts_parser.add_subparsers(dest="facts_command", required=True)
    facts_list_parser = facts_subparsers.add_parser("list", help="列出事实对象摘要")
    facts_list_parser.add_argument("object_type", choices=sorted(fact_cli.OBJECT_TYPES), help="对象类型")
    facts_list_parser.add_argument("--status", default=None, help="按状态过滤")
    facts_list_parser.add_argument("--base-dir", default=".", help="项目根目录，默认当前目录")
    facts_list_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")
    facts_show_parser = facts_subparsers.add_parser("show", help="查看事实对象详情")
    facts_show_parser.add_argument("target", help="YAML 文件路径或对象 ID")
    facts_show_parser.add_argument("--base-dir", default=".", help="项目根目录，默认当前目录")
    facts_show_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")
    facts_search_parser = facts_subparsers.add_parser("search", help="按关键词搜索事实对象")
    facts_search_parser.add_argument("keyword", help="搜索关键词")
    facts_search_parser.add_argument("--type", default=None, dest="type", help="限定对象类型，默认搜索所有类型")
    facts_search_parser.add_argument("--base-dir", default=".", help="项目根目录，默认当前目录")
    facts_stats_parser = facts_subparsers.add_parser("stats", help="统计对象状态分布")
    facts_stats_parser.add_argument("--type", default=None, dest="type", help="限定对象类型，默认统计所有类型")
    facts_stats_parser.add_argument("--base-dir", default=".", help="项目根目录，默认当前目录")
    facts_validate_parser = facts_subparsers.add_parser("validate", help="校验事实模型 YAML")
    facts_validate_parser.add_argument("paths", nargs="+", help="一个或多个 .yaml 文件或目录")
    facts_validate_parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")

    specs_parser = subparsers.add_parser("specs", help="包装 specs 校验能力")
    specs_subparsers = specs_parser.add_subparsers(dest="specs_command", required=True)
    specs_validate_parser = specs_subparsers.add_parser("validate", help="运行 specs 综合校验")
    specs_validate_parser.add_argument("paths", nargs="*", default=["docs/specs"], help="要检查的 Markdown 文件或目录")
    specs_validate_parser.add_argument("--root", default=str(PROJECT_ROOT), help="项目根目录")
    specs_validate_parser.add_argument("--specs-dir", default="docs/specs", help="索引生成使用的规范目录")
    specs_validate_parser.add_argument("--out", default=None, help="索引输出目录")
    specs_validate_parser.add_argument("--fail-on-diagnostics", action="store_true", help="存在 index 诊断时返回非零")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv == ["--help"]:
        parser.print_help()
        return 0
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    if args.command == "status":
        return cmd_status(args)
    if args.command == "landing":
        return cmd_landing(args)
    if args.command == "facts":
        return cmd_facts(args)
    if args.command == "specs":
        return cmd_specs(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
