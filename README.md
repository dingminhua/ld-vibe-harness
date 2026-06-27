# LDVH

This branch is a clean v3 root. It does not inherit v2 files by default.

Content enters this tree only when it has a v3 role:

- `specs/`: rule authority.
- `specs/core/`: parent rule authority established by the v3 project decision.
- `specs/schemas/`: machine-readable contracts authorized by specs.
- `code/`: deterministic, read-only compilers and validators.
- `tests/`: regression checks.
- `tests/fixtures/`: test materials, not rule sources.
- `rules/`, `hooks/`, `skills/`: runtime-facing assets after explicit migration.
- `ldvh-base/`: real fact objects after explicit migration.

The current first slice proves the action-guide path:

formatted LDVH source -> deterministic Code -> task-scoped action guide.

The v3 authority chain is:

project decision -> `specs/core/` -> Markdown specs + `specs/schemas/` -> deterministic Code -> Action Guide.

Stable constraints:

- Preserve the original LDVH specs document system when migrating spec bodies.
- Do not replace spec bodies with YAML.
- Do not invent new topical specs directories such as `specs/runtime/`, `specs/facts/`, `specs/action/`, or `specs/git/` unless a later explicit decision changes the document system.
- Use `specs/core/` only for the small parent layer needed by v3.
- Prefer direct Code parsing of stable Markdown structures over manually maintained per-spec YAML.
- Use YAML for schemas, temporary migration aids, generated debug output, or explicitly authorized machine artifacts, not as the first authority for specs.
