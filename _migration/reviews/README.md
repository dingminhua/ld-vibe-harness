# Historical Migration Review Records

This directory stores historical migration gate evidence.

Current formal review hash gate records live in `reviews/formal/`.

Review records are not spec facts. They cannot define rules, override Markdown specs, approve Human Gate, or replace Code diagnostics.

Before stage 11G, every formal spec or attachment addition, migration, or modification after the bootstrap set used:

```text
_migration/reviews/{object_id}-formal-review.yaml
```

After stage 11G, create and update:

```text
reviews/formal/{object_id}-formal-review.yaml
```

The record must show:

1. v2 to v3 mapping evidence exists.
2. Code verification command passed.
3. Subagent review passed with no unresolved blockers.
4. The review is bound to the target Markdown file hash.
5. Non-blocking warnings, if any, have a follow-up disposition.

Do not put migrated rules, value explanations, action guide fields, or rewritten spec summaries in a review record. Use it as a receipt only.

Formal tests now read `reviews/formal/`. This directory remains only for historical traceability and mapping evidence.
