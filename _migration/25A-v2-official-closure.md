# 25A V2 正式关闭记录

文件状态：official closure record。本文记录 Human 对 V3 正式启动、V2 关闭为历史来源的确认，以及本轮关闭验证和后置清单。本文不授权新增自动入口、Web 通用写入、外部项目 Hook 安装、`_migration` 归档、V2 Rules / Skill 顶层机制恢复或知识地图恢复。

## 关闭确认

关闭日期：2026-07-02。

Human 确认来源：当前对话中 Human 明确要求“按你的计划推进吧，一直到 v2 正式关闭”。

关闭结论：

1. V3 正式启动为当前 LDVH 日常主线；
2. V2 关闭为历史来源、迁移审计依据和对照材料；
3. V2 不再作为当前 LDVH 的日常规则入口；
4. V2 历史仓库、迁移材料、mapping evidence 和 source refs 不因关闭而删除；
5. 后置能力继续按 V3 规范、迁移记录和 Human Gate 推进。

## 关闭依据

1. `README.md`
2. `specs/00-理念与构成.md`
3. `specs/01-保障与衔接.md`
4. `specs/03-事实源与Git溯源规范.md`
5. `specs/04-Specs基础规范.md`
6. `specs/05-事实模型基础规范.md`
7. `specs/06-行动模板基础规范.md`
8. `specs/08-Web信息同步规范.md`
9. `specs/09-测试与验证规范.md`
10. `specs/10-安装与配置规范.md`
11. `_migration/12-19-v3-post-mainline-work-plan.md`
12. `_migration/23A-v2-close-v3-start-assessment.md`
13. `_migration/24A-user-local-ldvh-config-candidate.md`

## 条件核对

| 条件 | 结果 | 说明 |
|---|---|---|
| Human 明确确认 V3 启动、V2 关闭 | 已满足 | 本轮 Human 明确要求推进直到 V2 正式关闭 |
| README 和当前规范入口指向 V3 | 已满足 | README 顶部已声明 V2 关闭，`specs/` 当前 active 主线均为 V3 |
| `specs_validate.py all --fail-on-diagnostics` | 已满足 | 2026-07-02 本轮执行通过，diagnostics: 0 |
| `code/test_runner.py smoke` | 已满足 | 2026-07-02 本轮执行通过，formal specs hash tests 9 passed |
| 当前 worktree `git.commit-msg` Hook 状态可检查 | 已满足 | `core.hooksPath=hooks`，active hook 存在、可执行、managed，installed: True |
| 未跟踪或未归口材料完成分流 | 已满足 | 本轮新增 24A 用户级配置候选和本文，均归口 `_migration` 并将随本记录提交 |
| 后置清单写明且不作为启动阻断 | 已满足 | 见本文“关闭后的后置清单” |

## V3 启动后的主线口径

1. `specs/` 是当前规则源；
2. `ldvh-base/` 是当前事实对象实例位置；
3. `code/` 承接确定性解析、校验、诊断、commit gate 和测试入口；
4. `web/` 按 08 独立读取 V3 Git 文件事实源，不依赖 Code 输出作为主数据源；
5. `reviews/formal/` 是正式 specs review hash gate 收据位置；
6. `_migration` 继续作为历史迁移证据、mapping evidence、迁移测试和迁移工具承载区，不作为日常规则源或事实源。

## 关闭后的后置清单

以下事项不阻断 V2 关闭，也不得因关闭而被写成已完成能力：

1. `session_start`、`pre_tool_use`、`completion_claim` 仍为 manual-ready，不是 integrated 自动入口；
2. 除当前 worktree 的 `git.commit-msg` 外，外部受管项目 Hook 未自动安装；
3. 外部受管项目 Hook 安装 / 卸载必须继续走 `code/governed_hook_adapter.py` 和显式 Human Gate；
4. Spark quick create 仍是当前唯一正式 Web 写入；通用 Web 写入、完整 Confirm UI 和 WorkCase Web 状态推进继续后置；
5. `_migration` 仍保留，归档或删除必须先替代 mapping evidence、迁移测试和 source refs，再经 Human Gate；
6. V2 Rules / Skill 顶层机制不恢复，只作为 legacy 来源、repo instruction、manual entrypoint 或外部包装候选；
7. 知识地图不作为 V3 正式概念恢复，导航能力由 Action Guide / 行动指南方向承接；
8. 用户级 LDVH 配置目录仍是 `_migration/24A-user-local-ldvh-config-candidate.md` 中的候选记录，待 Spark 可用后再转入正式讨论。

后续队列整理见 `_migration/26A-v3-post-closure-work-queue.md`。该队列只整理优先级、触发条件和停止边界，不授权任何后置能力生效。

## 验证记录

本轮关闭验证于 2026-07-02 执行：

1. `python3 code/specs_validate.py all --format text --fail-on-diagnostics`
   - 结果：通过；
   - specs: 16；
   - attachments: 16；
   - fact_instances: 77；
   - governed_projects: 1；
   - diagnostics: 0。
2. `python3 code/test_runner.py smoke`
   - 结果：通过；
   - specs validator: ok；
   - formal specs hash tests: 9 passed。
3. `python3 code/install_git_hooks.py status`
   - 结果：可检查且已安装；
   - `core.hooksPath`: `hooks`；
   - active hook: `hooks/commit-msg`；
   - active hook exists: True；
   - active hook executable: True；
   - active hook managed: True；
   - installed: True。
4. `python3 code/environment_status.py --format text`
   - 结果：符合当前环境边界；
   - `environment_integrated`: partial；
   - `automated_entrypoints`: `git.commit-msg`；
   - manual entries available: true；
   - session_start、pre_tool_use、completion_claim 和 runtime_adapter 仍为 manual / external adapter-ready，不是 integrated。

## 关闭结论

Human 确认、README 入口更新、后置清单明确和关闭验证均已完成。V2 正式关闭为历史来源。后续 LDVH 日常规则判断、事实维护、提交校验和 Web 数据读取均以 V3 为准。
