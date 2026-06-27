# Code Determinism Core

This core spec defines deterministic Code boundaries for LDVH v3.

## Purpose

Code exists to execute explicit, reviewable operations over authorized inputs. Code should reduce AI burden by parsing, validating, projecting, and reporting deterministic results.

## Deterministic Inputs

Allowed inputs include formatted source files, specs-authorized schemas, explicit CLI arguments, explicit runtime payloads, filesystem paths, Git identity and branch facts, object status fields, and closed enum fields.

Disallowed inputs include unstated user intent, conversational memory as authority, inferred Human Gate approval, and candidate rules treated as active authority.

## Deterministic Outputs

Allowed outputs include validation results, diagnostics, derived indexes, task-scoped Action Guides, read plans, impact judgments, stop conditions, and next queries.

Disallowed outputs include fact source replacements, Human Gate approval, hidden write authorization, and action-state words such as allowed, approved, or unblocked when they imply approval.

## Rules

- Every trusted output must be derived from explicit files, schemas, CLI arguments, payloads, Git facts, or closed enum fields.
- Every action-relevant read, stop, impact, or next-query item must remain back-referenceable to a source reference.
- Generated indexes, Action Guides, checklists, and diagnostics must not become stable facts unless a separate rule authority promotes them.
- Repeatable checklists, read routes, and impact views should be generated from schemas and tests instead of copied as parallel prose.
- Parsing, validation, projection, and diagnostics are read-only unless a separate write authority and Human Gate explicitly apply.
- Runtime, hook, dispatcher, and commit/write strategy changes require separate confirmation.

## Stop Conditions

- Stop when a required input lacks source references.
- Stop when a rule requires natural-language inference instead of explicit fields or enums.
- Stop before changing Runtime, hook, dispatcher, or write/commit strategy without separate confirmation.
- Stop when a candidate source is used as an active authority.
