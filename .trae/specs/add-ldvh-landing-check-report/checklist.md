# Checklist

- [x] Spec states read-only project-local scope and user-level directory safety boundary
- [x] Spec states `ldvh-landing-check` must consume existing governed-projects, landing-report, runtime-projection, human-gate, fact, and spec checks
- [x] Report distinguishes open, degraded, and closed checks
- [x] Report includes remaining gaps with source area and suggested writeback
- [x] Tests cover governed-projects, fact/spec validation, subreport consumption, and CLI output
- [x] task-0061 records implementation evidence and remaining gaps without closing 41/42 prematurely
- [x] Validation commands pass
- [x] Commit includes only related files and excludes LDVH-GOVERNED / old `.trae` deletion handling / user-level directory writes
