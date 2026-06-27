# Migration Review Records

This directory stores temporary migration gate evidence.

Review records are not spec facts. They cannot define rules, override Markdown specs, approve Human Gate, or replace Code diagnostics.

For every formal spec or attachment addition, migration, or modification after the bootstrap set, create:

```text
_migration/reviews/{object_id}-formal-review.yaml
```

The record must show:

1. v2 to v3 mapping evidence exists.
2. Code verification command passed.
3. Subagent review passed with no unresolved blockers.
4. The review is bound to the target Markdown file hash.
5. Non-blocking warnings, if any, have a follow-up disposition.

Do not put migrated rules, value explanations, action guide fields, or rewritten spec summaries in a review record. Use it as a receipt only.

Formal tests fail when a formal object lacks this review gate, has a stale target hash, or leaves warnings without disposition.
