# Formal review ledger

本目录承载正式 specs 和附件的 review hash gate 收据。

规则：

1. 每个非 bootstrap formal object 使用 `{object_id}-formal-review.yaml`；
2. `target_spec` 必须指向 `specs/` 下的正式规范或附件；
3. `target_sha256` 必须等于当前文件内容 hash；
4. `mapping_evidence.path` 可以回指 `_migration/` 历史材料，但 review gate 本身不依赖 `_migration/reviews/`；
5. review 收据只证明审核和验证发生过，不授权、放行、验收或替代 Human Gate。
