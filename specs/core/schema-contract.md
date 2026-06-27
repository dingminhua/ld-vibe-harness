# Schema Contract Core

This core spec defines the role of `specs/schemas/`.

## Authority

`specs/schemas/` is the machine-readable contract layer authorized by `specs/core/`. A schema may describe valid structure for Code, but it is not an independent fact source and not a parent rule by itself.

## Rules

- Every schema must be traceable to a core spec or another active spec authorized by core specs.
- Schemas define parseable shape, required fields, enums, and validation boundaries.
- Schemas must not introduce new rule meaning that is absent from their authorizing spec.
- Code may consume schemas but does not own them.
- Fixtures may exercise schemas but cannot define schema authority.

## Stop Conditions

- Stop if a schema adds behavior not present in an authorizing spec.
- Stop if Code relies on a schema with no spec authority reference.
- Stop if fixtures are treated as examples that silently expand the contract.
