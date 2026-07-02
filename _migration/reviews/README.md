# Historical Migration Review Records

This directory stores historical migration gate evidence.

The current V3 mainline no longer uses a formal review hash gate. These records are retained only as historical migration evidence.

Review records are not spec facts. They cannot define rules, override Markdown specs, approve Human Gate, or replace Code diagnostics.

Before stage 11G, every formal spec or attachment addition, migration, or modification after the bootstrap set used:

```text
_migration/reviews/{object_id}-formal-review.yaml
```

Historical records were expected to show:

1. v2 to v3 mapping evidence exists.
2. Code verification command passed.
3. Subagent review passed with no unresolved blockers.
4. The review was bound to the target Markdown file hash at that migration point.
5. Non-blocking warnings, if any, have a follow-up disposition.

Do not add new current rules, value explanations, action guide fields, or rewritten spec summaries in a review record. Use these files as historical receipts only.

Formal specs tests no longer read review receipt directories. This directory remains only for historical traceability and migration evidence.
