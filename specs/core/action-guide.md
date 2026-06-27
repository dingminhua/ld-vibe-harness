# Action Guide Core

This core spec defines the v3 Action Guide.

## Purpose

An Action Guide is a generated navigation output that helps AI act on a task. It organizes the relationships, reading plan, impact judgment, stop conditions, and next queries needed for action.

The quality target is not merely lightweight. An Action Guide should be progressive, sufficient, back-referenceable, and stoppable.

## Rules

- Action Guides are generated from formatted sources and specs-authorized schemas by deterministic Code.
- Action Guides are task navigation outputs, not rule sources or fact sources.
- Every relationship, read-plan item, impact item, stop condition, and next query must remain traceable to source references.
- Action Guides may reduce reading burden by sequencing reads, but they must preserve the ability to return to sources.
- Limited, deprecated, candidate, or archived sources may produce inspection-only guides.

## Stop Conditions

- Stop if an Action Guide is used as authority instead of navigation.
- Stop if an Action Guide omits the source references needed to verify an action-relevant statement.
- Stop if a generated guide claims approval, permission, or unblock status.
