# WC-E prepare-update deterministic fixture replay

## Frozen execution

- Tasks: **12**; strategy records: **24**.
- Evidence class: **deterministic isolated fixture integration**.
- Fact types: `adr, pitfall, spark, study, workcase`.
- Branches: `invalid-signature, no-op, positive, stale`.
- All expected outcomes met: **true**.
- All failing branches zero-write: **true**.

## Mechanical interaction counts

| Discovery mode | Strategy | Tasks | Helper calls/task | Shell invocations | Request chars total | Caller transformations total |
|---|---|---:|---:|---:|---:|---:|
| minimal | known-contract | 7 | 2.0 | 0 | 12153 | 35 |
| minimal | prepare | 7 | 2.0 | 0 | 12132 | 21 |
| cold | known-contract | 5 | 3.0 | 0 | 9347 | 30 |
| cold | prepare | 5 | 2.0 | 0 | 9322 | 15 |

The minimal known-contract comparison is **parity only**: `2.0 → 2.0` Helper calls/task. The cold-discovery comparison is `3.0 → 2.0`, one mechanical Helper call fewer because the source-defined prepare operation removes the separate capabilities-discovery call in this frozen setup. Helper calls and shell invocations are separate metrics; strategy shell invocations were zero.

Isolation terminology: each task-strategy member uses a fresh temporary Git repository and that repository's initial working tree. It does not exercise a linked worktree and is not evidence from the current project repository.

Caller transformations count frozen, strategy-specific named workflow steps. A counted step is not a normalized unit of work or cognitive effort, so cross-strategy totals are descriptive fixture observations only.

## Evidence boundary

Host receipt, tokens, cache use, wall latency, and queue latency were unavailable and are not recorded as zero. Results retain labels, hashes, counts, booleans, and aggregates only; no raw request, full fact, signature, authorization, path, session, transcript, or secret is retained.

This is deterministic isolated-fixture integration evidence only. It is not real-task or representative evidence, does not establish host delivery, and supports no causal or broad service-quality conclusion.

Protocol SHA-256: `c7e6a246e914bc239391ec12241848136d174284e952ef82f0dff27900e748f7`.
Task package SHA-256: `ea4b59327e34f37dc47dda9e48666d9d18abdd1a2b84f2a7bd9978dda9756684`.
