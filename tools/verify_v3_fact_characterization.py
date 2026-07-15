#!/usr/bin/env python3
"""Render or verify the decision-free V3 source characterization."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "code"))

from ldvh.migration.v3_characterization import (  # noqa: E402
    render_v3_source_characterization,
    verify_v3_source_characterization,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifact",
        type=Path,
        default=REPOSITORY_ROOT / "migration" / "v3-facts" / "source-characterization.json",
    )
    parser.add_argument("--render", action="store_true", help="print canonical JSON without writing files")
    args = parser.parse_args()
    if args.render:
        sys.stdout.write(render_v3_source_characterization(REPOSITORY_ROOT))
        return 0
    result = verify_v3_source_characterization(REPOSITORY_ROOT, args.artifact)
    print(
        json.dumps(
            {
                "valid": result.valid,
                "entry_count": result.entry_count,
                "issues": [
                    {"code": issue.code, "summary": issue.summary, "source_key": issue.source_key}
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
