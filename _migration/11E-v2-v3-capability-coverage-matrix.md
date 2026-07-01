# 11E V2 到 V3 能力覆盖矩阵

阶段：11E

目的：把审计中提到的能力缺口放入同一张覆盖矩阵，区分已迁入、转归口、后置和废弃。

| V2 能力 / 资产 | V3 承接 | 当前状态 | 说明 |
|---|---|---|---|
| 构成要素体系 | `00` | 已迁入 | 五类构成作为正式骨架；保障与衔接层不作为第六类 |
| AI 行为保障 | `02`、`01.Att.01`、`01.Att.02`、Code read_plan | 已迁入 | session/pre-tool/completion 自动触发仍按 01 §6 后置 |
| Commit message 契约 | `03.Att.01`、commit gate、`hooks/commit-msg` | 已迁入 | 当前唯一 integrated 自动入口 |
| 事实对象模型 | `05`、`20`-`24`、`ldvh-base/`、tests | 已迁入 | 真实 Spark/WorkCase/ADR/Pitfall/Study 已落 V3 |
| Web 展示和 facts API | `08`、`web/`、`tests/web` | 已迁入 | Web 独立读取 facts，不使用 Code 输出作为主数据源 |
| 受管项目接入 | `10`、`LDVH-GOVERNED-PROJECTS.yaml`、resolver | 已迁入 | 目标判定是静态能力，不等于外部项目 Hook 已启用 |
| 环境入口分类与状态 | `01`、`01.Att.03-06`、`environment_status`、`environment_entry_audit` | 已迁入 | 自动入口与 manual-ready 明确分开 |
| Rules 顶层机制 | `01`、`04.Att.06`、`06` | 废弃顶层机制 | 只保留 legacy / repo instruction / 外部包装候选 |
| Skill 顶层机制 | `01`、`04.Att.06`、`06` | 废弃顶层机制 | 可吸收为行动模板步骤或外部包装候选 |
| 知识地图 | `06` Action Guide 口径 | 废弃术语 | legacy_alias，不保留独立事实层 |
| WorkCase 创建 / 关闭行动模板 | `06`、`21`、11F | 最小后置 | 当前不建立正式非提交模板 |
| Hook 安装部署检查 | `01.Att.06`、`install_git_hooks`、`governed_hook_adapter` | 部分迁入 | 当前只覆盖当前 worktree commit-msg 和外部受管项目 adapter-ready，不代表外部项目已安装 |
| V2 06 环境附件族 | `01`、`01.Att.03-06`、环境审计 Code | 转归口 | 未逐字迁入，按能力表和边界迁入 |
| `_migration/reviews` hash gate | `reviews/formal` | 已迁出 | `_migration/reviews` 仅保留历史材料 |

## 结论

V2 主体内容已进入 V3 主线或明确废弃 / 后置。仍未完成的不是“未分类迁移”，而是有进入条件的后置能力，主要集中在非提交行动模板、外部环境自动 Hook、稳定 receipt 存储和通用 Web 写入。
