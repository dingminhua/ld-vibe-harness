"""Generate the Web data contract from the Python presentation table."""

from __future__ import annotations

from pathlib import Path

from ldvh.facts.workcase_presentation import render_typescript_contract


def main() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    target = repository_root / "web" / "shared" / "workcasePresentationContract.generated.ts"
    target.write_text(render_typescript_contract(), encoding="utf-8")


if __name__ == "__main__":
    main()
