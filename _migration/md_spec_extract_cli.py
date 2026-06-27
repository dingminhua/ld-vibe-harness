from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_migration" / "code"))

from md_spec_extractor import extract_action_source, extract_markdown_spec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract navigation structure from an LDVH Markdown spec.")
    parser.add_argument("source", help="Markdown spec path")
    parser.add_argument(
        "--action-source",
        action="store_true",
        help="Output a formatted source that can compile into an Action Guide.",
    )
    args = parser.parse_args()

    payload = (
        extract_action_source(args.source)
        if args.action_source
        else extract_markdown_spec(args.source)
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
