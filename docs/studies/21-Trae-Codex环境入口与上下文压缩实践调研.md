# Trae / Codex 环境入口与上下文压缩实践调研

> 创建日期：2026-06-14
> 定位：Trae / Codex 环境入口、Rules / AGENTS 薄引用、上下文压缩与恢复实践的参考调研
> 调研边界：不直接构成强制规则；正式规则应进入 `specs/04.03-环境入口适配与部署规范.md` 或其他对应规范后才生效
> 执行效力：研究材料，可为后续环境适配规范、Code 检查、Rules、AGENTS、Hook、Command 或人工降级方案提供候选输入
> 当前范围：Trae CN、Trae 国际版、Codex App / Codex CLI

---

## 1. 本文解决的问题

本文记录 Trae / Codex 环境入口与上下文压缩相关的调研结论，重点回答：

1. Rules 环境部署前应如何发现 Trae CN、Trae 国际版和 Codex 环境入口；
2. Trae 与 Codex 的薄引用内容是否需要区分；
3. Trae 上下文压缩后应如何恢复 LDVH 规则和事实上下文；
4. Codex 是否存在类似上下文压缩或上下文恢复的官方最佳实践；
5. 哪些内容可以作为后续 04.03 吸收候选，哪些内容只能作为待实测或人工提醒。

本文只保存研究材料。后续 AI 不得把本文当作 specs 上位依据、正式规范引用或稳定结论来源。

---

## 2. 结论摘要

| 主题 | 当前结论 | 证据状态 | 后续去向 |
|---|---|---|---|
| Trae CN 用户级 Rules 入口 | 用户确认应使用 `.trae-cn/user_rules/ldvh_rules.md`，文件中只放薄引用内容 | Human 确认；本机加载行为待实测 | 04.03 候选吸收 |
| Trae 国际版用户级 Rules 入口 | 用户确认应使用 `.trae/rules/ldvh_rules.md`，文件中只放薄引用内容 | Human 确认；本机加载行为待实测 | 04.03 候选吸收 |
| Codex 用户级入口 | Codex 官方最佳实践明确 `AGENTS.md` 可作为 durable guidance，并支持全局、仓库级、子目录级分层 | 官方资料确认；本机路径和 App 行为待实测 | 04.03 候选吸收 |
| Trae 上下文压缩 | 搜索结果显示 Trae / Trae SOLO 存在上下文压缩能力，但官方可引用资料不足；应按 Human 已知能力和实测处理 | 外部资料和 Human 经验，需谨慎 | 作为待实测候选，不直接写成强规则 |
| Codex 上下文压缩 | Codex 官方最佳实践提到 `/compact`，并说明 Codex 会自动 compact 长对话 | 官方资料确认 | 04.03 候选吸收 |
| 压缩后恢复 | Trae / Codex 都不应依赖聊天记忆或压缩摘要作为长期事实源，应回到薄引用、LDVH Rules 资产和 Git 文件事实源 | LDVH 原则 + Codex 官方资料 + Trae 候选实践 | 04.03 候选吸收 |

---

## 3. 环境入口发现流程候选

Rules 环境入口部署前，不应直接写入文件。候选流程如下：

1. 只检查三类用户级环境入口：Trae CN、Trae 国际版、Codex；
2. Trae CN 检查用户主目录下 `.trae-cn/` 与 `.trae-cn/user_rules/ldvh_rules.md`；
3. Trae 国际版检查用户主目录下 `.trae/` 与 `.trae/rules/ldvh_rules.md`；
4. Codex 检查用户主目录下 `.codex/` 与 AGENTS 入口候选；
5. 若三类环境入口均未发现，应提示用户当前没有发现可部署环境入口；
6. 若发现一个或多个环境入口，应由 Human 多选确认安装到哪些环境；
7. 不默认全选，不静默写入，不记录长期“已写入本机入口”状态。

该流程属于 04.03 候选吸收内容。实际写入前仍需按当前机器检查路径、文件内容和权限。

---

## 4. Trae 薄引用候选模板

Trae 的薄引用内容应使用 Trae Rules 语境，不应复用 Codex AGENTS 语境。薄引用正文只保留入口指向和必要的压缩后重读提示；部署约束、禁止声明、事实源边界和 Human Gate 要求不应混入薄引用正文。

候选模板如下：

```markdown
# LDVH AI 入口引用

读取并遵守：

<LDVH_RULES_ENTRY>

发生上下文压缩、会话恢复或规则重新加载后，重新读取上述 LDVH AI 入口。
```

候选边界：

1. Trae CN 目标文件为 `.trae-cn/user_rules/ldvh_rules.md`；
2. Trae 国际版目标文件为 `.trae/rules/ldvh_rules.md`；
3. 规范或研究材料中的模板使用 `<LDVH_RULES_ENTRY>` 变量；实际部署时替换为当前机器真实绝对路径；
4. 薄引用正文只放入口指向、压缩后重读提示和起止标记；
5. 不复制 specs 正文、不维护第二事实源、不声明环境完整支持等内容属于部署约束，不属于薄引用正文。

---

## 5. Codex 薄引用候选模板

Codex 官方最佳实践将 `AGENTS.md` 描述为自动进入上下文的 durable guidance，并建议保持简短、准确、可执行。Codex 薄引用应使用 AGENTS / instructions 语境，优先追加到用户级 AGENTS 的 LDVH 管理段，不覆盖用户已有内容。薄引用正文只保留入口指向和必要的 compact 后重读提示；AGENTS 简洁性、覆盖策略、事实源边界和禁止声明不应混入薄引用正文。

候选模板如下：

```markdown
## LDVH AI 入口引用

读取并遵守：

<LDVH_RULES_ENTRY>

发生 `/compact`、自动上下文压缩、线程恢复或上下文恢复后，重新读取上述 LDVH AI 入口。
```

候选边界：

1. Codex AGENTS 入口不是 LDVH Rules 资产；
2. 不应覆盖用户已有 AGENTS 内容；
3. AGENTS 主入口应保持简短，复杂内容应引用任务专属 Markdown 文件；
4. 规范或研究材料中的模板使用 `<LDVH_RULES_ENTRY>` 变量；实际部署时替换为当前机器真实绝对路径；
5. 薄引用正文只放入口指向、compact 后重读提示和起止标记；
6. 不复制 specs 正文、不维护第二事实源、不覆盖用户已有 AGENTS 内容、不声明环境完整支持等内容属于部署约束，不属于薄引用正文。

---

## 6. Trae 上下文压缩调研

联网搜索结果显示，Trae / Trae SOLO 相关资料中存在“上下文压缩”能力描述，典型说法是：对长对话中已有上下文进行总结或压缩，以降低上下文窗口压力、减少“失忆”和响应变慢风险。搜索结果还提到 Trae SOLO 对话框中可找到压缩上下文功能。

但是，本轮未找到足够稳定的 Trae 官方文档页面可作为正式规范依据。因此，Trae 上下文压缩只能作为候选适配经验保存：

1. 可以在 Trae 薄引用中提醒压缩后重新读取 LDVH AI 入口；
2. 从 Git 文件事实源、Task、Memo、ADR、Pitfall、Change 或 Human 当前输入恢复上下文属于部署与恢复要求，不应混入薄引用正文；
3. 不应声明 Trae 提供可编程的 `PreCompact` 或 `PostCompact` Hook；
4. 不应把压缩摘要、聊天记忆或模型内部记忆当作长期事实源。

候选来源包括：

1. CSDN 文章《Trae编辑器中的“上下文压缩”(Context Compression)是什么?》；
2. 今日头条文章《TRAE SOLO 中国版，正式发布!》中关于上下文压缩的介绍；
3. 今日头条文章《Trae solo 健忘?试下上下文压缩!》中关于对话框压缩上下文的描述；
4. Human 已确认 Trae 存在上下文压缩相关规则，需要 LDVH 薄引用应用该规则。

这些来源只作为研究材料，不作为 specs 上位依据。

---

## 7. Codex 上下文压缩与 AGENTS 最佳实践调研

OpenAI Codex 官方 best practices 页面给出了较稳定的结论：

1. `AGENTS.md` 是给 agent 的 open-format README，会自动进入上下文；
2. `AGENTS.md` 适合记录仓库布局、运行方式、测试命令、工程约定、约束、完成标准；
3. 可以有 global `AGENTS.md`、repo-level `AGENTS.md` 和子目录级 `AGENTS.md`，更靠近当前目录的说明优先；
4. `AGENTS.md` 应保持实用、简短、准确，避免堆满模糊规则；
5. 如果 `AGENTS.md` 变大，应保持主文件简洁，并引用任务专属 Markdown 文件；
6. Codex CLI / App 提供 `/compact`，当线程变长时可压缩早期上下文；Codex 也会自动 compact conversations；
7. 应保持一个 thread 对应一个 coherent unit of work，必要时 fork；
8. 不应把一个项目的所有工作都堆入同一 thread，避免上下文膨胀和质量下降。

这些结论可以作为 04.03 后续吸收候选。吸收时应避免把官方资料路径写成 specs 上位依据，而应把稳定规则改写成 LDVH 自身规范条款。

官方来源：

- OpenAI Developers：Codex best practices，`https://developers.openai.com/codex/learn/best-practices`

---

## 8. 后续吸收候选

建议后续由 Human 人工提醒，再决定是否吸收到 `specs/04.03-环境入口适配与部署规范.md`：

1. Rules 环境入口部署前的三类环境发现流程；
2. 未发现环境入口时停止部署并提示用户；
3. 多环境发现时通过多选确认安装目标；
4. Trae CN 用户级 Rules 入口 `.trae-cn/user_rules/ldvh_rules.md`；
5. Trae 与 Codex 薄引用模板分离；
6. Trae 国际版用户级 Rules 入口 `.trae/rules/ldvh_rules.md`；
7. Trae 压缩后重新读取 LDVH Rules 资产；
8. Git 文件事实源、Task、Memo、ADR、Pitfall、Change 或 Human 当前输入恢复上下文属于部署与恢复要求，不属于薄引用正文；
9. Codex AGENTS 保持简短、准确、可执行；
10. Codex `/compact`、自动 compact 和 thread / fork 最佳实践；
11. 不记录长期“已写入本机入口”状态。

---

## 9. 禁止声明

1. 不得声明本文是 specs 上位依据；
2. 不得声明本文中的候选模板已经正式生效；
3. 不得声明 Trae CN、Trae 国际版或 Codex 当前机器已经部署成功；
4. 不得声明 Trae 国际版 Rules 入口路径已经确认；
5. 不得声明 Codex App 当前版本一定读取用户级 AGENTS，除非完成本机实测；
6. 不得把 Trae 压缩摘要、Codex compact 摘要、聊天记忆或 Hook 输出当作长期事实源；
7. 不得因为本文存在而跳过 Human Gate。
