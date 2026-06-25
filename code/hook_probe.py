#!/usr/bin/env python3
"""
LDVH Hook Probe — 跨环境最小 Hook 探针。

只读采集环境 Hook 事件 payload，不执行 LDVH 业务逻辑，不写用户项目事实源。
用途：在 Codex / WorkBuddy / Trae 等不同环境中采集真实 Hook 证据，
供后续 LDVH adapter 设计使用。

用法（环境 Hook 配置中调用）:
    python3 hook_probe.py --event <event_name> --evidence-dir <dir>

或通过 stdin 接收 JSON payload（WorkBuddy / Codex 风格）:
    echo '{"hook_event_name":"SessionStart",...}' | python3 hook_probe.py --evidence-dir <dir>

输出:
    在 --evidence-dir 下按时间戳创建子目录，写入:
      fingerprint.json   — 环境指纹
      stdin.json         — 原始 stdin payload
      argv.txt           — 命令行参数
      env.txt            — 相关环境变量
      cwd.txt            — 当前工作目录
      exit_code.txt      — 退出码
      summary.json       — 结构化摘要

退出码:
    0   — 探针正常完成（不阻断）
    2   — 探针自身错误（如 --evidence-dir 缺失）
"""

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

PROBE_VERSION = "0.1.0"


def collect_fingerprint() -> dict:
    """采集环境指纹：不执行 LDVH 业务逻辑，不写用户项目。"""
    return {
        "probe_version": PROBE_VERSION,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "hostname": platform.node(),
        "environ_prefixes": {
            "CODEBUDDY": any(k for k in os.environ if k.startswith("CODEBUDDY")),
            "WORKBUDDY": any(k for k in os.environ if k.startswith("WORKBUDDY")),
            "TRAE": any(k for k in os.environ if k.startswith("TRAE")),
            "CODEX": any(k for k in os.environ if k.startswith("CODEX")),
            "LDVH": any(k for k in os.environ if k.startswith("LDVH")),
        },
        "has_stdin": not sys.stdin.isatty() if hasattr(sys.stdin, "isatty") else None,
    }


def read_stdin() :
    """尝试从 stdin 读取 JSON payload。不是 tty 时读取；是 tty 时返回 None。"""
    try:
        if hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
            return None
        raw = sys.stdin.read()
        if not raw.strip():
            return None
        return {
            "raw": raw,
            "parsed": json.loads(raw) if raw.strip().startswith("{") else None,
            "parse_error": None,
        }
    except json.JSONDecodeError as e:
        return {"raw": raw if "raw" in dir() else "", "parsed": None, "parse_error": str(e)}
    except Exception as e:
        return {"raw": "", "parsed": None, "parse_error": str(e)}


def collect_env() -> dict:
    """采集相关环境变量，不泄露敏感信息。"""
    relevant_prefixes = [
        "CODEBUDDY", "WORKBUDDY", "TRAE", "CODEX",
        "LDVH", "HOME", "USER", "SHELL", "PATH",
        "PYTHON", "VIRTUAL_ENV", "NODE",
    ]
    env = {}
    for k, v in sorted(os.environ.items()):
        for prefix in relevant_prefixes:
            if k.upper().startswith(prefix):
                env[k] = v
                break
    return env


def write_evidence(evidence_dir: Path, event: str, fingerprint: dict,
                   stdin_data, args: list[str],
                   env_data: dict, cwd: str, exit_code: int) -> dict:
    """写入 evidence 子目录，不写用户项目，不修改外部环境。"""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = evidence_dir / f"{ts}_{event}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # 环境指纹
    (run_dir / "fingerprint.json").write_text(
        json.dumps(fingerprint, indent=2, ensure_ascii=False, default=str))

    # 命令行参数
    (run_dir / "argv.txt").write_text("\n".join(args))

    # stdin payload
    if stdin_data is not None:
        (run_dir / "stdin.json").write_text(
            json.dumps(stdin_data, indent=2, ensure_ascii=False, default=str))
    else:
        (run_dir / "stdin.json").write_text('{"note": "no stdin (tty)"}')

    # 环境变量
    (run_dir / "env.txt").write_text(
        json.dumps(env_data, indent=2, ensure_ascii=False))

    # cwd
    (run_dir / "cwd.txt").write_text(cwd)

    # exit code
    (run_dir / "exit_code.txt").write_text(str(exit_code))

    summary = {
        "probe_version": PROBE_VERSION,
        "event": event,
        "timestamp_utc": fingerprint["timestamp_utc"],
        "run_dir": str(run_dir),
        "exit_code": exit_code,
        "fingerprint": fingerprint,
        "has_stdin": stdin_data is not None,
        "stdin_parsed": stdin_data.get("parsed") is not None if stdin_data else False,
        "stdin_parse_error": stdin_data.get("parse_error") if stdin_data else None,
        "env_key_count": len(env_data),
        "note": "LDVH Hook Probe v{} — 只读采集，未执行 LDVH 业务逻辑".format(PROBE_VERSION),
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str))

    return summary


def main():
    parser = argparse.ArgumentParser(description="LDVH Hook Probe — 跨环境最小探针")
    parser.add_argument("--event", default="unknown", help="环境 Hook 事件名（如 SessionStart）")
    parser.add_argument("--evidence-dir", required=True, help="evidence 输出目录（不存在则创建）")
    parser.add_argument("--exit-code", type=int, default=0, help="探针返回值（0=正常，2=错误）")
    args, unknown = parser.parse_known_args()

    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    try:
        fingerprint = collect_fingerprint()
        stdin_data = read_stdin()
        env_data = collect_env()
        cwd = os.getcwd()

        summary = write_evidence(
            evidence_dir=evidence_dir,
            event=args.event,
            fingerprint=fingerprint,
            stdin_data=stdin_data,
            args=sys.argv,
            env_data=env_data,
            cwd=cwd,
            exit_code=args.exit_code,
        )

        # 输出摘要到 stdout（供环境消费）
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        sys.exit(args.exit_code)

    except Exception as e:
        error_summary = {
            "probe_version": PROBE_VERSION,
            "error": str(e),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(error_summary, indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
