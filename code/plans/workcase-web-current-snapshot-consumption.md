# WorkCase Web 当前快照投影最终消费

## 覆盖与依据

本规划承接 `workcase-0043` 已批准的 Web 增量：在 `workcase-current-snapshot-presentation/1` 已由 Python 唯一维护点和生成合同交付的基础上，使 Web API 下游、列表、详情、认知中心、阅读面板和共享进度轨道只消费绑定当前载体指纹的 resolved `current_snapshot_projection`。`specs/21-WorkCase-工作项.md` 继续唯一负责 `status + phase` 和投影语义，`specs/08-Web 呈现与交互规范.md` 负责页面消费边界；本规划只分配 Code 责任，不定义领域规则。

创建基线为 commit `9e901278b4f6049f4a82a18106d4ef15fffa155d`。`spark-0040` 与 `workcase-0036` 至 `workcase-0039` 是其它工作的既有未提交内容，本增量不得修改、暂存或提交。`workcase-0043` 只经 WorkCase 专属 Helper 更新。

## 目标与不变量

- API 读取边界可以继续用 raw `status + phase + source_content_fingerprint` 调用 `deriveWorkCasePresentationProjection` 形成 source-bound 投影；raw 字段也可以作为事实原值显示。
- 投影形成后，页面、DTO、聚合、Gate inbox、阻塞覆盖和轨道不得再从 raw `status/phase` 重建进展结论。
- `plan_confirmation`、`progressing`、`closure_confirmation`、`closed` 继续作为与 lifecycle position 不同的四类 Web 浏览分组。
- unresolved、错误或缺失指纹时不回退到 raw 字段；下游显示不可判定或从相应集合排除，并保留读取问题。
- `next_required_control_step` 只在详情显示为本地化只读提示；不形成按钮、自动执行、写回、授权、能力、优先级或完成判断，未知 key 不原样泄漏。
- 不修改 Python、Helper、Specs、生成器、`workcasePresentationContract.generated.ts` 或 WorkCase YAML 投影字段。

## 审计矩阵

| 层次 | 允许 | 必须退出 |
|---|---|---|
| source-bound formation | `facts.ts` / `cognition.ts` 在持有实际载体指纹处调用 `deriveWorkCasePresentationProjection` | 无指纹的 `projectWorkCaseCard` 和 raw progress facade |
| API/DTO | 原样传递 resolved projection，并从它复制兼容 `progress_group/progress_step` | 从 raw phase/status 形成 Gate、active group、blocked overlay 或进度步骤 |
| 页面 | 消费 `lifecycle_position`、`progress_group`、`progress_step`、`blocking_overlay`、`next_required_control_step` | ObjectDetail header、共享轨道和 Card 从 phase/status 重新推导 |
| 原始事实阅读 | 原样显示 `status`、`phase`、waiting/blocking 等事实字段 | 把这些原值解释成派生浏览分组或下一动作 |

## 模块责任与调用方向

### Shared facade 与 API

- `web/shared/workcaseStatus.ts` 保留 source-bound `deriveWorkCasePresentationProjection`、resolved 类型守卫、四分组/四步骤显示顺序和类型；删除 `WorkCaseProgressProjection`、`getWorkCaseProgressProjection`、`getWorkCaseProgressGroup`、`getWorkCaseProgressStep`、`deriveWorkCaseProgressProjection`。
- `web/api/services/facts.ts` 只保留 `projectCurrentWorkCaseCard`。Card 形状直接读取 resolved projection；无指纹 legacy `projectWorkCaseCard` 退出。
- `web/api/routes/objects.ts` 继续从 resolved projection形成列表兼容字段和按 `progress_group` 统计/筛选，不从 raw 字段补造。
- `web/api/routes/cognition.ts` 允许在直接持有 `LocalFactItem.source_content_fingerprint` 的 commit-hotspot 路径形成投影；其余 inbox、active、recent activity 和 DTO 构造只消费 resolved projection。Gate inbox 使用 `handoff_narrative_key` 且要求 `blocking_overlay=false`，active 使用 `progress_group=progressing`，不以 raw status/phase 决定派生类别。

### 页面、类型与本地化

- `WorkCaseProgressTrack` 接收 `lifecyclePosition`、`progressGroup`、`progressStep`；`plan_revising` 的轨迹外提示来自 `lifecycle_position`，不得接收 phase。
- `ObjectList`、`CognitionCenter` 将同源投影字段传给 Card/轨道；blocked 视觉只消费 projection 的 `blocking_overlay`，raw status 仍留作事实字段。
- `ObjectDetail` 与 `PanelContent` 的 header 只在 resolved projection 下显示 `progress_group`，否则显示 `unknown`；不再调用 raw projector。
- `WorkCaseReadingLayout` 从详情 DTO 的 resolved projection驱动轨道，并呈现本地化 `next_required_control_step` 只读行；unresolved/unknown 显示不可判定且不输出原始 key。
- `workcaseDetailProjection.ts` 只做字段存在性分组，可投影当前快照呈现字段，但不定义 phase 映射。
- `utils/api.ts` 为列表、详情和 Cognition DTO 提供 source-bound projection 成员；页面不自行发明兼容类型。
- `locales.ts` 维护当前合同稳定 next-step keys 的中英文显示和 unknown 文案，不维护 phase 映射。

允许的方向：

```text
current carrier bytes + raw status/phase
  -> Web API source-bound formation
     -> resolved current_snapshot_projection
        -> compatible API fields / aggregations / page props / localized read-only hint
```

禁止页面、DTO 或聚合反向调用 raw phase facade，也禁止 i18n、tests 或 docs 建立第二张 phase 表。

## 诊断、回滚与边界

- projection 缺失、unresolved、指纹不合法或合同身份不匹配时，下游不猜测；列表/认知聚合保留可定位 issue，详情显示不可判定。
- 只删除本案 legacy 出口及其直接正向测试；若发现未列路径仍是生产消费者，停止受影响 item，不扩大白名单。
- 回滚按白名单文件恢复本案变化；不得修改生成合同或 Specs 来迁就页面。
- 本地 commit 按语义交付单位形成，检查点写回与 commit 粒度解耦；不 push、不建 PR。

## 验证映射

| 风险 | 验证 |
|---|---|
| legacy facade 仍可被生产消费 | 全白名单符号搜索；契约测试断言 legacy exports/imports 消失 |
| unresolved 回退 raw status/phase | detail/list/cognition 缺失、错误指纹与 unresolved 负测 |
| blocked 误入 Human Gate | Gate inbox 断言 `blocking_overlay=true` 时排除；active/详情按投影显示阻塞 |
| 四类浏览分组被删或与 lifecycle 混同 | 列表统计/筛选、Cognition、shared 顺序和文档合同测试 |
| 轨道仍从 phase 重建 | 组件 source-contract 和页面契约测试；props 不再含 `phase` |
| next step 变成行动入口或泄漏 unknown key | 全稳定 key 本地化、unknown 文案、无按钮/handler/source key 负测 |
| DTO/页面类型漂移 | `npm run check` 与 `npm run build` |
| dirty 工作被夹带 | `git status`、路径白名单、基线 SHA-256 和提交候选回读 |

目标验证包括列名 Web API tests、资源允许时全量 Web API tests、`npm run check`、`npm run build`、legacy symbol 搜索、`git diff --check`、WorkCase 精确回读、`check-fact-integrity` 和独立只读结果复核。测试通过只证明受测 Code/文档行为，不证明真实浏览器的所有交互、Human 授权或 WorkCase 完成。
