# LDVH

This branch is a clean v3 root. It does not inherit v2 files by default.

Current formal scope:

- `specs/`: Markdown rule authority.
- `code/`: deterministic parsers, validators, and generators after explicit need.
- `tests/`: regression checks.
- `rules/`, `hooks/`, `skills/`, `ldvh-base/`: reserved for later whole-line migration.
- `_migration/`: temporary evidence and prototypes, not formal authority.

Current principle:

One Markdown spec is the single rule fact source. Human, AI, and Code share that source through stable structure and explicit references; they do not get separate fact sources.

Attachments are allowed only as subordinate content referenced by the body, such as tables, figures, field closures, enums, or reusable machine contracts. Attachments must not carry parent rules, core doctrine, action flows, Human Gate, fact-source boundaries, migration process, or long explanatory prose.

Do not reintroduce `specs/core/`, formal `specs/schemas/`, or 01 structural attachments unless a later explicit decision changes this rule.
