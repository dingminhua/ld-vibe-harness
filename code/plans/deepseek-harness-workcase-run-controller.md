# WorkCase 运行主控计划：Subagent 审核与 same-AI 兜底

## 当前边界

- Controller 负责读取 WorkCase、消费 Gate 1 授权、推进 item、形成结果并处置 Reviewer 反馈。
- Subagent 是唯一独立审核方式；Reviewer 必须只读，不修改文件、事实或状态。
- Subagent 的执行模型由宿主决定；LDVH 不维护模型目录、选择、映射或持久路由策略。
- 每次需要审核时，Controller 必须在自身当前会话完整发现工具，并实际尝试创建 Subagent。
- 只有 Controller 自身的工具发现和创建结果可以判断能力；Subagent 对 Controller 能力的结论不能作为证据。

## 无法创建 Subagent

Controller 实际无法创建 Subagent 时：

1. 保存 Controller 自身的工具发现和实际创建失败证据；
2. 向 Human 明确披露将切换为同一 AI 只读 Reviewer 视角，以及该方法不具环境独立性的保证差距；
3. 告知后直接执行，不请求确认、不等待回复、不增加 Human Gate；
4. 在 WorkCase review 中记录 `actual_method=same-ai-switched-role-read-only`、`capability_evidence`、`assurance_gap`、`human_disclosure_summary` 与 `human_disclosed_at`。

## 连续执行

Gate 1 后，Controller 按当前指纹依次完成 item 检查点、Controller 自检、完整结果投影、实际结果审核、反馈处置、关闭提案和 Gate 2。除 closed、真实 blocked、持续 unresolved 或 Gate 2 waiting 外，不以阶段汇报中断 Controller-owned 执行链。

## 验证

- 活动 WorkCase 的 review 方法只允许 `subagent-read-only` 或满足披露字段的 `same-ai-switched-role-read-only`。
- 历史 closed WorkCase 保持原文、旧枚举和旧引用可读，不回写历史。
- 规则、Python、Web、Helper 与事实完整性检查共同验证当前合同。
