#!/usr/bin/env python3
"""Render or verify the immutable V3 fact migration baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "code"))

from ldvh.migration.v3_baseline import render_v3_baseline, verify_v3_baseline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPOSITORY_ROOT / "migration" / "v3-facts" / "baseline.json",
    )
    parser.add_argument("--render", action="store_true", help="print the canonical manifest without writing files")
    args = parser.parse_args()
    if args.render:
        sys.stdout.write(render_v3_baseline(REPOSITORY_ROOT))
        return 0
    result = verify_v3_baseline(REPOSITORY_ROOT, args.manifest)
    print(
        json.dumps(
            {
                "valid": result.valid,
                "entry_count": result.entry_count,
                "issues": [
                    {"code": issue.code, "summary": issue.summary, "source_path": issue.source_path}
                    for issue in result.issues
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
