#!/usr/bin/env python3
"""Bootstrap LDVH Code Python dependencies in a fresh environment."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_REQUIRES = (3, 9)
INSTALL_PACKAGES = ("PyYAML", "pytest")
REQUIRED_MODULES = {
    "yaml": "PyYAML",
    "pytest": "pytest",
}


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def missing_packages() -> list[str]:
    missing = []
    for module_name, package_name in REQUIRED_MODULES.items():
        if not module_available(module_name):
            missing.append(package_name)
    return missing


def ensure_python_version() -> bool:
    if sys.version_info >= PYTHON_REQUIRES:
        return True
    required = ".".join(str(part) for part in PYTHON_REQUIRES)
    current = ".".join(str(part) for part in sys.version_info[:3])
    print(f"Python {required}+ is required for LDVH Code; current: {current}", file=sys.stderr)
    return False


def run_install() -> int:
    command = [sys.executable, "-m", "pip", "install", *INSTALL_PACKAGES]
    print("Installing LDVH Code dependencies:")
    print("  " + " ".join(command))
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if result.returncode != 0:
        print(
            "Install failed. Manual fallback: python3 -m pip install PyYAML pytest",
            file=sys.stderr,
        )
    return result.returncode


def report_status() -> int:
    missing = missing_packages()
    if not missing:
        print("LDVH Code Python dependencies are available: PyYAML, pytest")
        return 0
    print("Missing LDVH Code Python packages: " + ", ".join(missing), file=sys.stderr)
    print("Run: python3 code/bootstrap_code.py", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install or check LDVH Code Python dependencies."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check dependency availability; do not install.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not ensure_python_version():
        return 2

    if args.check_only:
        return report_status()

    if missing_packages():
        install_status = run_install()
        if install_status != 0:
            return install_status

    return report_status()


if __name__ == "__main__":
    raise SystemExit(main())
