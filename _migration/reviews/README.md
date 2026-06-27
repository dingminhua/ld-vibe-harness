# Migration Review Records

This directory stores temporary migration gate evidence.

Review records are not spec facts. They cannot define rules, override Markdown specs, approve Human Gate, or replace Code diagnostics.

For every migrated spec or attachment after the bootstrap set, create:

```text
_migration/reviews/{object_id}-migration-review.yaml
```

The record must show:

1. v2 to v3 mapping evidence exists.
2. Code verification command passed.
3. Subagent review passed with no unresolved blockers.
4. The review is bound to the target Markdown file hash.

Do not put migrated rules, value explanations, action guide fields, or rewritten spec summaries in a review record. Use it as a receipt only.

Formal tests fail when a migrated spec lacks this review gate.
