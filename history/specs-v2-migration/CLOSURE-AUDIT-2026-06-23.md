# v2 迁移收口审计 2026-06-23

```yaml
migration_closure_audit:
  status: recorded
  date: "2026-06-23"
  active_fact_source: "specs/"
  source_materials:
    - "/Users/dmh2002/poker_hud_projects/LDVH-AI服务度与00价值观符合度评估报告.md"
    - "/Users/dmh2002/poker_hud_projects/LDVH-V1-V10价值判断修改完善建议.md"
  purpose: "把工作区外部评估材料吸收为 v2 active 后的收口核对项"
  source_of_truth: false
  write_policy: "本文只记录审计项，不直接修改 00、01 或其它 active specs 规则。"
```

## 1. 文件性质

本文是 `history/specs-v2-migration/` 下的迁移收口审计记录，不是 active 正式规范、规范保障要求、行动编排成员、Code 命令契约或 Web 实现计划。

本文吸收工作区根目录两份评估文档中的可核对内容，目的是把外部过程输出转为可追踪的迁移收口事项。两份来源文档本身不进入 active 事实源；其中结论必须经过本文分级、当前仓库事实核验和后续必要 Human Gate 后，才能进入对应规范、Code 文档、Web 文档、事实对象或行动编排候选计划。

## 2. 当前核验结论

| 核验项 | 当前观察 | 收口判断 |
|---|---|---|
| v2 active 状态 | `history/specs-v2-migration/ACTIVATION-STATUS-2026-06-23.md` 已记录 v2 active 切换完成；当前 `python3 code/specs_validate.py v2-check --fail-on-diagnostics --format text` 通过且 diagnostics 为 0 | 本文不重开 active 切换，只处理切换后的收口项 |
| `specs-v2/` 残留 | 仓库根目录 `specs-v2/` 仅剩 `.DS_Store`，已清理 | 无需吸收为规范内容 |
| Code YAML 依赖 | 当前环境 `python3` 可 import `yaml`；`pyproject.toml` 已声明 `PyYAML` | “依赖未文档化”不应直接写成已确认缺陷；应核对 README 或 Code 文档是否需要补充安装说明 |
| `specs/README.md` | 当前仓库不存在 `specs/README.md`；多个规范保障要求把它列为入口可见机制之一 | 需要确认是补入口文件，还是把保障机制统一改为 `specs/01-规范体系基础规范.md`、知识地图输入和 Rules 入口 |
| 30-59 行动编排成员 | 当前无 active 30-59 成员主文件；03 明确成员应由 v2 保障需求生成候选计划 | 不阻塞 v2 active，但应进入行动编排候选计划阶段 |
| Web Confirm UI | 05 保留契约和回归线，Web 后置状态已在 activation status 中声明 | 不阻塞 v2 active；应进入 Web 后置计划 |
| 运行时扩展触发 | Rules 入口已存在；Hook/Agent 等能力仍以登记、候选或环境适配为主 | 不阻塞 v2 active；应由 06 后续适配和 Code 检查逐项承接 |

## 3. 可吸收内容分级

| 等级 | 来源判断 | 归属 | 处理方式 |
|---|---|---|---|
| A | `specs/README.md` 入口资产缺失可能削弱 V1 | 01 / 06 / 运行时入口 | 必须核对；二选一：补 `specs/README.md` 作为薄入口，或修改相关保障机制不再引用该文件 |
| A | Code 依赖与本地可运行性影响 V6 | 04 / 08 / README / Code docs | 核对现有 `pyproject.toml`、README 和 Code docs；若入口层缺安装说明，应补文档，不改变规范技术栈边界 |
| B | Web Confirm UI 未实现影响 V9 | 05 / Web / 08 | 切换后继续完善；不作为 specs active 切换阻塞项 |
| B | 行动编排 30-59 空导致 V4 执行路径仍依赖入口和人工降级 | 03 / 01.Att.07 / 30-59 候选计划 | 后续由各规范保障需求生成候选计划；不得直接迁移 v1 30/41/42/43/44 |
| B | 运行时扩展“被触发/被执行”能力仍不完整 | 06 / Rules / Skills / Agents / Hooks | 后续按固定运行时扩展登记、环境适配和部署检查推进 |
| C | V 项适用阶段说明 | 00 | 不直接修改 00；如需落地，必须先进入 Human Gate 评估 |
| C | V5 / V8 否决权重 | 00 / 01 | 判断方向可作为审计参考；直接写入 00 或改变准入作用前必须 Human Gate |
| C | 新增 V11 或重定义 V3/V4/V10 | 00 | 暂不建议；当前不进入迁移收口实施项 |

## 4. 切换后必须优先核对

### 4.1 `specs/README.md` 入口口径

当前 `specs/01-规范体系基础规范.md` 以及 20-24 成员规范的保障要求中，多处把 `specs/README.md` 作为入口可见机制之一。仓库实际不存在该文件。

后续只能选择以下一种口径：

1. 创建 `specs/README.md`，作为极薄规范入口，只指向 00、01、Rules 入口和 `v2-check`，不复制规范正文；
2. 修改相关保障要求，把入口可见机制收敛为 01 当前目录登记、知识地图输入、Rules 入口和 `python3 code/specs_validate.py v2-check --format text`。

在完成该核对前，不得把 `specs/README.md` 当作已经存在的入口资产。

### 4.2 Code 运行依赖入口说明

当前 `pyproject.toml` 已声明 `PyYAML`，当前本地 `python3` 可 import `yaml`。因此外部评估中的“系统 python 缺 yaml”不是当前仓库内已复现缺陷。

但 README 和 Code 文档仍需核对是否足以让 AI 在新环境中完成 V6 强制验证：

1. 是否说明 Python 依赖安装方式；
2. 是否说明 `npm run test:code` 与 `python3 code/specs_validate.py v2-check --fail-on-diagnostics --format text` 的关系；
3. 是否说明工具不可用时回到 Git 文件事实源和人工降级检查；
4. 是否避免把具体技术栈写成 04 规范义务。

## 5. 需要 Human Gate 后才能改 00 的事项

两份外部材料中关于 V1-V10 的建议，不应直接进入 00。以下事项若要写入 `specs/00-LDVH理念与价值标准.md`，必须先准备 Human Gate：

| 事项 | 触发原因 | 当前处理 |
|---|---|---|
| V 项适用阶段说明 | 可能改变 V1-V10 的准入理解和运行时评估边界 | 暂作候选审计项 |
| V5 / V8 否决权重 | 可能改变 V 项权重和准入作用 | 暂作候选审计项 |
| 修订 §6 或 §7 的价值判断表述 | 影响 00 最高价值锚点 | 暂不实施 |

当前建议是：先用现有 V1-V10 做收口审计，不在本阶段修改 00。

## 6. 后续执行建议

| 顺序 | 动作 | 输出 |
|---|---|---|
| 1 | 核对并处理 `specs/README.md` 入口口径 | 极薄入口文件，或保障要求引用修正 |
| 2 | 核对 README / Code docs 的依赖安装与验证入口说明 | README 或 `code/docs/` 更新 |
| 3 | 把 30-59 行动编排缺口整理为候选计划输入 | 行动编排候选计划，不直接迁移 v1 流程 |
| 4 | 把 Web Confirm UI 与 Web 后置实现纳入 Web 差距审计 | Web 后置计划或 WorkCase |
| 5 | 对 V 项适用阶段和 V5/V8 权重准备 Human Gate 选项 | 仅在用户确认后修改 00 |

## 7. 当前不执行事项

1. 不直接修改 00 的 V1-V10；
2. 不把两份工作区外部评估文档整体复制进 specs；
3. 不把 Web Confirm UI、30-59 行动编排成员或完整知识地图运行时作为 v2 active 切换阻塞项；
4. 不把外部评估中未经当前仓库复现的问题写成已确认缺陷；
5. 不从历史 v1 流程直接创建 30-59 active 行动编排成员。
