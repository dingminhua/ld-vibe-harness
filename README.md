# LDVH

This branch is a clean v3 root. It does not inherit v2 files by default.

Content enters this tree only when it has a v3 role:

- `specs/`: rule authority.
- `specs/schemas/`: machine-readable contracts authorized by specs.
- `code/`: deterministic, read-only compilers and validators.
- `tests/`: regression checks.
- `tests/fixtures/`: test materials, not rule sources.
- `rules/`, `hooks/`, `skills/`: runtime-facing assets after explicit migration.
- `ldvh-base/`: real fact objects after explicit migration.

The current first slice proves the action-guide path:

formatted LDVH source -> deterministic Code -> task-scoped action guide.
