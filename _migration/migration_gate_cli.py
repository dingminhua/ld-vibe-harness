from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "code"))

from migration_gate import classify_candidate, load_candidate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify a temporary v3 migration candidate.")
    parser.add_argument("candidate", help="Migration candidate YAML file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args(argv)

    decision = classify_candidate(load_candidate(args.candidate))
    print(json.dumps(decision, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if decision["decision"] != "invalid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
