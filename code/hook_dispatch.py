#!/usr/bin/env python3
"""LDVH unified hook dispatcher.

This runner keeps hook business rules in LDVH-owned assets and Code validators.
Environment adapters may call this dispatcher, but must not duplicate rules.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = PROJECT_ROOT / "hooks" / "ldvh-hooks.yaml"


def load_registry(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise RuntimeError(f"读取 Hook registry 失败: {exc}") from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(f"解析 Hook registry 失败: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Hook registry 顶层必须是 YAML object")
    return data


def hooks_for_event(registry: dict[str, Any], event: str) -> list[dict[str, Any]]:
    hooks = registry.get("hooks", [])
    if not isinstance(hooks, list):
        raise RuntimeError("Hook registry 的 hooks 字段必须是 list")
    matched = []
    for hook in hooks:
        if not isinstance(hook, dict):
            continue
        if hook.get("event") == event and hook.get("status", "active") == "active":
            matched.append(hook)
    return matched


def render_arg(value: str, context: dict[str, str]) -> str:
    rendered = value
    for key, replacement in context.items():
        rendered = rendered.replace("{" + key + "}", replacement)
    if "{" in rendered or "}" in rendered:
        raise RuntimeError(f"Hook command 包含未知占位符: {value}")
    return rendered


def render_command(raw_command: Any, context: dict[str, str]) -> list[str]:
    if not isinstance(raw_command, list) or not raw_command:
        raise RuntimeError("Hook command 必须是非空 list")
    command = []
    for part in raw_command:
        if not isinstance(part, str):
            raise RuntimeError("Hook command 的每个参数都必须是 string")
        command.append(render_arg(part, context))
    return command


def run_event(event: str, registry_path: Path, context: dict[str, str], dry_run: bool = False) -> int:
    registry = load_registry(registry_path)
    matched = hooks_for_event(registry, event)
    if not matched:
        print(f"未找到 active Hook event: {event}", file=sys.stderr)
        return 2

    exit_code = 0
    for hook in matched:
        hook_id = hook.get("id", "<unknown>")
        command = render_command(hook.get("command"), context)
        print(f"LDVH Hook {hook_id}: {' '.join(command)}")
        if dry_run:
            continue
        result = subprocess.run(command, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            exit_code = result.returncode
            if hook.get("blocking", True):
                break
    return exit_code


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run LDVH registered hooks through a unified dispatcher.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run active hooks for an event.")
    run_parser.add_argument("event", help="Hook event id, for example git.commit-msg.")
    run_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Hook registry YAML path.")
    run_parser.add_argument("--message-file", type=Path, default=None, help="Commit message file path for git.commit-msg.")
    run_parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")

    args = parser.parse_args(argv)
    if args.command == "run":
        context: dict[str, str] = {}
        if args.message_file is not None:
            context["message_file"] = str(args.message_file)
        try:
            return run_event(args.event, args.registry, context, dry_run=args.dry_run)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    return 2


if __name__ == "__main__":
    sys.exit(main())
