# Spec System Core

This core spec establishes the v3 specification system.

The initial `specs/core/` set is created by an explicit v3 project decision. It is not created by a YAML instance, a schema, generated Code, or an Action Guide.

## Authority Order

1. Human project decision establishes the first core specs.
2. `specs/core/` defines stable rule authority.
3. `specs/schemas/` defines machine-readable contracts authorized by core specs.
4. YAML instances and formatted sources express authorized machine-readable facts or rules.
5. Deterministic Code validates and compiles authorized inputs.
6. Action Guides are generated navigation outputs for AI action.

## Rules

- Core specs are the long-term parent layer for v3 rules.
- Schemas cannot authorize themselves.
- YAML instances cannot define their own parent authority.
- Code cannot invent, promote, or expand rule authority.
- Action Guides cannot become facts or rules unless a core spec authorizes that promotion path.
- The initial project decision is not a reusable extension mechanism. After the core specs exist, new specs must follow the rules in `specs/core/spec-system.md` and related core specs.

## Stop Conditions

- Stop if a schema, YAML instance, generated index, or Action Guide is treated as the first authority for a rule.
- Stop if a new core spec is added without an explicit source reference to the authorizing project decision or an existing core-spec amendment rule.
- Stop if a bootstrap-like file is added as a normal numbered spec.
