# LDVH Web Architecture

> 当前身份：本文记录既有 V3 Web 的实现架构，不是 V4 规范或完整适配结论。V4 当前实施入口见 [`V4-工作推进总纲.md`](../../docs/v4-architecture/V4-工作推进总纲.md)。正文中的 V3 事实对象、`ldvh-base/` 和旧 Specs 说明只能作为历史实现线索。

## 1. Positioning

LDVH Web is the Human-facing surface for Git-backed LDVH fact objects. It does not replace specs, Code validation, YAML fact sources, Study Markdown fact sources, or Git commit records.

Web tests belong to the Web implementation and are kept under `web/tests/`. They may verify integration among:

- `ldvh-base/` YAML fact objects and Study Markdown fact objects
- `code/` deterministic Python tools
- `web/api/` Express routes
- `web/src/` React views
- `specs/` field and workflow contracts

## 2. Runtime Layout

```text
ld-vibe-harness/
  package.json        # root command entry
  pyproject.toml      # Python tool/test metadata
  code/               # deterministic Python tools
  specs/              # formal specs
  ldvh-base/          # dogfood fact objects
  web/
    package.json      # Web Node package
    api/              # Express API
    src/              # React app
    tests/            # Web-owned tests
```

## 3. Dependency Ownership

The Web Node dependency owner is `web/package.json`.

Web TypeScript tests live in `web/tests/` and resolve their dependencies from `web/package.json`. They should not rely on implicit shell globals such as `NODE_PATH`. The repository root does not provide a shared `tests/` directory.

## 4. Command Entry

Use `web/` for focused Web checks:

```bash
npm run check
npm run test:web:api
npm run build
```

Run these commands after `cd web`.

## 5. Fact Reading Boundary

`web/api/services/facts.ts` may read YAML directly for read-only Web presentation.

`web/api/services/pytools.ts` calls Python tools when the API needs deterministic validation or Code-derived reports.

When a field contract changes, update specs, Python validation, Web-native readers, Web views, and tests together.

## 6. Specs Metadata Boundary

Specs document metadata uses the top-level `ldvh_doc` contract defined by `specs/03-文档基础规范.md` and `specs/03.01-规范文档规范.md`.

Specs root Markdown files must not duplicate `ldvh_doc` document metadata in an ordinary `> field: value` / `> 字段：值` header.

Current Web views do not treat specs metadata as editable object state. If Web later displays specs metadata in Project Files, Reading Panel, validation pages, or a dedicated specs viewer, the source must be the Git file itself or a Code-derived read-only API result. Web may display `ldvh_doc` fields and Code diagnostics, but must not invent, persist, migrate, or backfill `ldvh_doc` fields, and must not duplicate `ldvh_member` member facts such as `spec_id`, `collection_status`, `canonical_path`, or anchor fields into ordinary header metadata.
