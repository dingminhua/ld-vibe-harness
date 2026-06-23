# v2 active 切换状态记录 2026-06-23

```yaml
activation_status:
  status: recorded
  date: "2026-06-23"
  active_fact_source_after_switch: specs/
  rollback_tag: pre-v2-activation-2026-06-23
  human_gate:
    approved: true
    source: "用户确认：我们有git的没有大问题，全部同意，按你计划推进"
```

## 1. 记录目的

本文记录 v2 active 切换已经完成的阶段、明确后置的阶段和后续价值提取计划。

本文是迁移历史记录，不是 active 正式规范，不替代 `specs/`、`ldvh-base/`、Code 输出或 Web 展示。

## 2. 已完成阶段

| 阶段 | 状态 | 追溯 |
|---|---|---|
| 切换前冻结记录 | 已完成 | `1e86135 docs(specs): 记录 v2 active 切换冻结点` |
| v1 `specs/` 历史化 | 已完成 | `8936b9b docs(specs): 切换 v2 为 active 规范目录` |
| v2 正式规范进入 active `specs/` | 已完成 | `8936b9b docs(specs): 切换 v2 为 active 规范目录` |
| Code 默认检查切换到 active `specs/` | 已完成 | `75bc913 code(specs): 切换默认检查到 v2 active 规范` |
| Rules / Skill / Hook 入口切换 | 已完成 | `2a80e73 fix(code): 对齐运行时扩展登记检查` |
| Agents | 无 active 固定 Agent，暂无切换动作 | `specs/attachments/06.Att.02-固定运行时扩展登记表.md` |
| Web | 明确后置 | 本文 §3 |

## 3. Web 后置状态

Web 暂不接入 v2 active 工作流。

后续只有在 05 的 DTO/API、页面映射、Confirm UI、轻写入白名单、提交记录展示、缓存同步和知识地图展示契约完成实现核对后，才能单独切换 Web 默认入口并执行 Web 回归。

在 Web 切换前：

1. Web 不作为 v2 active 切换完成的阻塞项；
2. Web 不得声明已经完整消费 v2 active 规范；
3. Web 既有展示、缓存或页面状态不得替代 active `specs/`、Code 检查或 Git 文件事实源；
4. Web 切换必须单独提交，并按 05 与 08 验证。

## 4. 历史记录价值提取计划

切换前事实源和 v1 历史记录不自动继承为新的 active 事实源。

后续价值提取按以下顺序推进：

| 顺序 | 动作 | 输出 |
|---|---|---|
| 1 | 建立历史来源清单 | v1 specs、旧工作对象、docs/studies、docs/sources、迁移过程记录和相关 commit 范围 |
| 2 | 识别仍有价值内容 | 需求、决策、证据、经验、风险、未完成事项和长期上下文 |
| 3 | 判定 v2 归属 | Spark、WorkCase、ADR、Pitfall、Study、规范缺口或行动编排候选 |
| 4 | 重写为 v2 事实 | 按 02 与 20-29 字段契约创建或更新新事实源 |
| 5 | 保留来源追溯 | 记录历史路径、对象 ID、commit hash 或章节来源 |
| 6 | 运行 Code 检查 | 校验字段、状态、引用、事实源边界和 Git 追溯 |
| 7 | Human Gate | 对高影响事实、争议事实、关闭判断和长期经验进行确认 |

完成价值提取前，不得宣称旧事实源已经被完整吸收。

## 5. 当前完成判断

截至本文记录时，v2 active 切换的规范目录、Code 默认检查、Rules、Skill 和 Hook 入口已切换完成。

后续工作不再按 v1 规范直接迁移行动编排或事实源状态；应先基于 v2 active 规范提出需求，再建立新事实源、行动编排候选、Web 接入和知识地图运行时能力。

## 6. 已执行验证

| 命令 | 结果 |
|---|---|
| `python3 code/specs_validate.py deployment-entries` | 通过 |
| `python3 code/specs_validate.py v2-check --fail-on-diagnostics --format text` | 通过；diagnostics 0；review_hints 0 |
| `python3 code/specs_validate.py all --fail-on-diagnostics` | 通过；diagnostics 0；review_hints 0 |
| `python3 -m pytest tests/code/specs_validate_checks/test_deployment_entries.py -q` | 8 passed |
| `python3 -m pytest tests/code/specs_validate_checks/test_ldvh_assurance.py tests/code/specs_validate_checks/test_web_validate.py -q` | 13 passed |
| `npm run test:code` | 283 passed；specs:check 通过 |
| `git diff --check` | 通过 |

## 7. 待办

1. 旧 Code 文档和部分旧检查器测试夹具仍保留 v1 术语，应在 Code 文档清理阶段单独处理；
2. commit validator 文案仍引用 v1 `specs/10-Git提交规范.md`，应在 Git 解析和 commit validator v2 化阶段单独处理；
3. Web v2 接入需要按 05 与 08 单独规划；
4. 历史记录价值提取需要先建立清单，再按 v2 事实模型重写进入新事实源。
