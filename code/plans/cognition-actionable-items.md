# Cognition 行动事项收录与完整 Card

## 覆盖与依据

本规划承接 `workcase-0044` 已批准增量，只修复 Cognition Center 中 WorkCase / Pitfall 行动事项对既有“待决定事项”和“推进中事项”两个模块的收录与正文呈现。`specs/21-WorkCase-工作项.md` 和 `workcase-current-snapshot-presentation/1` 继续负责 WorkCase 状态与投影语义；本规划只分配 Web Code 责任，不定义 phase 映射、Gate、授权或完成判断。

创建基线为 commit `a6de69c49884ed10a5e654aca0c864c7cde64c2b`。`spark-0040`、`workcase-0036` 至 `workcase-0039` 及 `file-asset-0002` 是范围外未提交内容，不得修改、暂存或提交；`workcase-0044` 只经 WorkCase 专属 Helper 更新。

## 目标与不变量

- 只消费 source-bound、`resolution=resolved` 的 `current_snapshot_projection`；unresolved 不从 raw `status/phase`、`waiting_on`、`blocking_summary` 或 AI 文案回退。
- `progress_group=plan_confirmation/closure_confirmation` 的 open/blocked WorkCase 进入待决定事项；其中 `blocking_overlay=true` 使用 `blocked_resolution`，不生成 Gate waiting 或批准/关闭提示。
- `progress_group=progressing` 的 open/blocked WorkCase只进入推进中事项；blocked 继续以阻塞覆盖层呈现。
- 每个 resolved open/blocked WorkCase 恰好进入一个行动模块；不新增第三个行动模块，不修改近期动态、Spark 健康和近期提交热点关系。
- Pitfall `status=draft` 继续进入待决定事项，并复用对象列表的普通 Pitfall Card 内容；`active/discarded` 不进入待确认。
- 不修改 Specs、Python、Helper、生成合同、事实字段合同或任何 Pitfall 事实，不持久化 `progress_group`、`inboxKind` 等派生判断。

## 收录矩阵

| 对象快照 | 待决定事项 | 推进中事项 | 呈现 |
|---|---:|---:|---|
| resolved WorkCase，plan/closure group，未阻塞 | 是 | 否 | `plan_confirmation` / `closure_confirmation` |
| resolved WorkCase，plan/closure group，阻塞 | 是 | 否 | `blocked_resolution`，显示当前位置与阻塞事实，不显示 Gate 文案 |
| resolved WorkCase，progressing group，open/blocked | 否 | 是 | 既有 progressing Card；blocked 保留阻塞覆盖 |
| unresolved WorkCase | 否 | 否 | API issue / 页面降级，不猜测归属 |
| Pitfall draft | 是 | 否 | `pitfall_confirmation` + 共享普通 Pitfall Card |
| Pitfall active/discarded | 否 | 否 | 不属于待确认收录 |

## 模块责任与调用方向

- `web/api/routes/cognition.ts` 只从 resolved projection 的 `progress_group`、`blocking_overlay` 与 `handoff_narrative_key` 形成唯一行动归属。`progress_group` 决定模块；`handoff_narrative_key` 只证明真实 Gate 类型；blocked Human-position 形成 `blocked_resolution`，不伪造 Gate。
- `web/src/utils/api.ts` 提供闭集 inbox kind 与 WorkCase/Pitfall DTO；页面不解析自由文本补类型。
- `web/src/pages/CognitionCenter.tsx` 保持既有两个行动模块，增加 blocked-resolution 标签/正文，并把 Pitfall draft 交给共享 Card 内容。
- `web/src/pages/ObjectList.tsx` 导出并复用普通 `PitfallCardContent`；对 draft/active 呈现 `symptoms`、`trigger_conditions`、`resolution`、`avoidance`、`validation_summary`、`applicability` 中可读字段，discarded 保持终态说明。
- `web/src/i18n/locales.ts` 只提供 `blocked_resolution` 和 Pitfall 字段显示文案，不维护 phase 表。
- `web/docs/02-CognitionCenter.md` 与直接相关契约测试固定上述消费边界。

允许方向：

```text
current carrier -> source-bound WorkCase projection -> progress_group module membership
                                           + blocking_overlay presentation kind
Pitfall field-level fact card -----------------------> shared PitfallCardContent
```

## 诊断、回滚与边界

- resolved 投影缺失、身份/指纹错误或未知 group 时，不进入两个行动模块，并保留 collection issue；禁止 raw fallback。
- Pitfall 字段级异常继续由已有 `field_issues` / `unparsed_structures` 呈现；Card 不因跳过坏字段而宣称对象完整。
- 若实现需要修改未授权生产路径、其它 Cognition 模块或事实合同，停止受影响 item，不扩大白名单。
- 回滚只恢复本案白名单文件；不得以 legacy projector、第二张 phase 表或测试事实兜底。

## 验证映射

| 风险 | 验证 |
|---|---|
| blocked Human-position 被遗漏或误称 Gate | API fixture 覆盖 plan/closure blocked，断言 `blocked_resolution` 且无 Gate handoff 文案 |
| WorkCase 重复进入两个模块 | resolved group 矩阵与当前对象集合断言唯一归属 |
| unresolved 从 raw 字段回退 | missing/wrong fingerprint 与 unresolved 负测；source 搜索禁止 fallback |
| Pitfall draft 只有标题无正文 | 共享组件 source contract + fixture 覆盖六个判断字段和坏字段降级 |
| active/discarded Pitfall 误入待确认 | API status 负测 |
| 类型、计数、复制摘要或文档漂移 | TypeScript check、build、i18n/type/docs contract |
| 其它 Cognition 模块被改动 | 路径/diff 审计与现有全量 API tests |
| 当前页面行为不符合事实 | 本地 API 与浏览器核验当前 WorkCase；Pitfall draft 仅使用 fixture，不声称 live 验证 |
| 范围外 dirty 被夹带 | SHA-256、`git status`、Index 白名单、提交候选回读 |

目标验证包括列名契约测试、全量 Web API tests、`npm run check`、`npm run build`、`git diff --check`、当前 WorkCase API/浏览器核验、Pitfall draft fixture、WorkCase 精确回读、`check-fact-integrity` 与独立只读结果复核。浏览器当前事实结果与 fixture 结果分别记录；测试或构建通过不扩大为所有未来交互保证。
