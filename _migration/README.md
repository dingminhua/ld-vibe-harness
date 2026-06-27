# LDVH v3 Migration Workspace

This directory is transitional migration scaffolding.

It is not part of the stable v3 product surface:

- `_migration/schemas/` is not `specs/schemas/`.
- `_migration/code/` is not formal `code/`.
- `_migration/fixtures/` is not formal `tests/fixtures/`.
- `_migration/tests/` is not the permanent v3 test suite.

Use this directory only to classify v2 material before it enters v3. A migration
decision can say whether a source should be migrated, deferred, rejected, or
converted into schema/code/tests instead of copied as another fact source.

Delete this whole directory when:

- the first v3 migration batch is complete;
- stable v3 migration rules exist;
- migration decisions are represented by permanent specs, schemas, or tests;
- no active work depends on transitional classification fixtures.

Do not import `_migration` modules from stable v3 code.

Inventory files under `_migration/inventory/` are temporary review aids. They
may list v2 specs, attachments, and suggested migration actions, but they do
not authorize v3 specs, schemas, Code behavior, or Action Guides.
