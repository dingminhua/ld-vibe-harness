# WC-D knowledge-precheck paired experiment

## Frozen sample

- Retained pairs: **12**; member calls: **24**.
- Technical pair replacements: **0**.
- Control-first / treatment-first: **6 / 6**.
- State-changing Helper calls: **0**.
- Host receipt: **unavailable**.

## Paired knowledge-quality estimates

Treatment minus control; positive favors the source-bound precheck package.

| Metric | Mean difference | Bootstrap 95% CI | Exact sign-flip p |
|---|---:|---:|---:|
| `answer_correct` | 0.166667 | [-0.166667, 0.500000] | 0.625000 |
| `applicability_correct` | 0.083333 | [0.000000, 0.250000] | 1.000000 |
| `selection_correct` | 0.666667 | [0.416667, 0.916667] | 0.007812 |
| `non_use_correct` | 0.000000 | [-0.250000, 0.250000] | 1.000000 |
| `duplicate_avoidance_correct` | 0.166667 | [0.000000, 0.416667] | 0.500000 |
| `first_action_correct` | 0.250000 | [-0.083333, 0.583333] | 0.375000 |

`selection_correct` was nominally higher for the combined source-identity-plus-content package in this 
selected frozen corpus (mean +0.666667; exact sign-flip p=0.0078125). Source identity availability, 
source content, and precheck instruction are inseparable in this contrast. Six quality metrics were 
examined and no multiple-comparison adjustment was applied. The overall answer, applicability, 
non-use, duplicate-avoidance, and first-action estimates remain compatible with null or mixed task 
effects at this sample size.

## Added observable cost

| Metric | Mean difference | Bootstrap 95% CI | Exact sign-flip p |
|---|---:|---:|---:|
| `fact_read_count` | 0.000000 | [0.000000, 0.000000] | 1.000000 |
| `candidate_expansion_count` | 2.000000 | [2.000000, 2.000000] | 0.000488 |
| `prompt_chars` | 194.750000 | [184.000000, 205.250000] | 0.000488 |
| `packet_chars` | 230.750000 | [220.000000, 241.250000] | 0.000488 |
| `material_chars` | 230.750000 | [220.000000, 241.250000] | 0.000488 |
| `response_chars` | 56.333333 | [27.083333, 85.166667] | 0.004883 |

Input/output/cache usage and wall/queue latency were not exposed by the retained native-subagent 
boundary and are recorded as `unavailable`, not zero. `fact_read_count=0` means trial agents made no 
fact calls; treatment received two LDVH-prepared F3 material cards per task. Candidate expansion and 
character counts are behavior/cost measures, not proof of knowledge value.

## Blind scoring and limitations

- One full scorer failed before returning any score. Three disjoint family scorers supplied the first 
  perspective; a separate scorer supplied the preregistered second perspective for ambiguity cases.
- Seven disputed metric fields were resolved only against the frozen gold and are retained in the 
  structured adjudication ledger; no condition or pair counterpart was disclosed to scorers.
- The derived-field replay test recomputes hashes, analysis, and report from the existing result plus 
  protocol. It is not a source-complete records-only reconstruction of scorer provenance, so the 
  original reproducibility criterion is not satisfied.
- The control packet was source-free but structurally matched, so this estimates the combined 
  source-bound package, not separate F2, F3, instruction, or card effects.
- The corpus is twelve selected LDVH tasks and is not a random sample of all project work.

## Evidence boundary and residual decision

The protocol and cards are **ldvh-prepared** and were **harness-delivered**. Provider/host receipt is 
**unavailable**. The nominal selection score was higher under a package that uniquely exposed source 
identities and content; this is not by itself demonstrated knowledge or reuse improvement. Other 
quality effects are null or mixed and the package adds material/context cost. 
This report does not claim broad causal benefit, does not close the service-quality Spark, does not 
establish HV4 generally, and provides no Phase3/MCP or product-change authorization.

Records SHA-256: `98653684a1b2b7873878447f982ea0360ca76f24387b2031540d57547f44a472`.
