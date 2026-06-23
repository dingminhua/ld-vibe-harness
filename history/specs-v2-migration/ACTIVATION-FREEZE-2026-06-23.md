# v2 active 切换冻结记录 2026-06-23

```yaml
activation_freeze:
  status: recorded
  date: "2026-06-23"
  active_fact_source_before_switch: specs/
  activation_plan: specs-v2/V2-ACTIVATION-PLAN.md
  rollback_tag: pre-v2-activation-2026-06-23
  human_gate:
    approved: true
    source: "用户确认：我们有git的没有大问题，全部同意，按你计划推进"
```

## 1. 记录目的

本文记录 v2 active 切换前的冻结状态、Human Gate 和检查结果。

本文不是正式规范，不替代 `specs/` 或 `specs-v2/`，不作为事实模型实例。

## 2. Human Gate

Human 已确认按 `specs-v2/V2-ACTIVATION-PLAN.md` 推进 v2 active 切换。

本次确认允许继续进入以下阶段：

1. 归档 v1 `specs/`；
2. 建立新 active `specs/`；
3. 规范化 v2 文件身份、路径和引用；
4. 后续按计划切换 Code、Rules、Skills、Agents、Hooks 和 Web 入口。

## 3. 切换前检查

切换前已执行：

| 命令 | 结果 |
|---|---|
| `python3 code/specs_validate.py v2-check --fail-on-diagnostics --format text` | 通过；diagnostics 0；review_hints 0 |
| `python3 code/specs_validate.py all --fail-on-diagnostics` | 通过；diagnostics 0；存在 v1 44 既有 info 级 review hint，不阻塞 |

## 4. 回滚锚点

已创建本地 Git tag：

```text
pre-v2-activation-2026-06-23
```

后续每个切换阶段仍应拆分提交；如阶段失败，应优先通过普通 Git 提交反向修改恢复，不使用破坏性命令。
