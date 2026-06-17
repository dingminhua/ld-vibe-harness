# LDVH Web Architecture

## 1. Positioning

LDVH Web is the Human-facing surface for Git-backed LDVH fact objects. It does not replace specs, Code validation, YAML fact sources, Study Markdown fact sources, or Git-backed Change records.

The repository intentionally keeps system tests under the root `tests/` directory because Web behavior often verifies the integration among:

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
  tests/              # cross-layer tests
  web/
    package.json      # Web Node package
    api/              # Express API
    src/              # React app
```

## 3. Dependency Ownership

The Web Node dependency owner is `web/package.json`.

Root-level TypeScript tests may live in `tests/web/`, but when they need Web runtime dependencies they must resolve those dependencies from `web/package.json` or execute through the Web package scripts. They should not rely on implicit shell globals such as `NODE_PATH`.

## 4. Command Entry

Use the repository root for product-level checks:

```bash
npm run check
npm run test:web:api
npm run specs:check
npm run web:restart
```

Use `web/` directly only for focused Web development:

```bash
cd web
npm run dev
npm run build
```

## 5. Fact Reading Boundary

`web/api/services/facts.ts` may read YAML directly for read-only Web presentation.

`web/api/services/pytools.ts` calls Python tools when the API needs deterministic validation or Code-derived reports.

When a field contract changes, update specs, Python validation, Web-native readers, Web views, and tests together.
