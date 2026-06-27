from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_migration" / "code"))

from spec_bloat_scan import scan_specs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan LDVH Markdown specs for repeated structure.")
    parser.add_argument("specs_root", help="Path to specs directory")
    args = parser.parse_args()
    print(json.dumps(scan_specs(args.specs_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
