# LDVH 下一阶段推进方向：受控落地执行闭环

> 创建日期：2026-06-11
> 定位：整合 18、19、20 号历史调研文档 与后续讨论后的 LDVH 下一阶段方向文档
> 性质：内部调研与推进方向文档，不直接构成正式规范或实施承诺
> 执行效力：无；稳定结论需进入正式 specs、ADR、Task、Code、Web、测试、运行投影或最佳实践后才具备对应效力
> 来源：18、19、20 号历史调研文档、2026-06-11 关于安装、自动执行、CLI、长期状态源与平台映射的讨论；跨环境相关事项已收敛到 `docs/research/22-LDVH跨环境能力复用与薄投影落地计划.md`
> 上位依据：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`docs/specs/04-规范落地与环境适配基础规范.md`、`docs/specs/04.02-环境适配与运行投影规范.md`、`docs/specs/04.03-环境能力清单与投射规范.md`、`docs/specs/04.06-环境能力清单规范.md`、`docs/specs/06-工作流程基础规范.md`、`docs/specs/07-Code实现规范.md`、`docs/specs/08-Web信息同步规范.md`、`docs/specs/09-事实源边界与承载规范.md`、`docs/specs/10-运行闭环测试规范.md`、`docs/specs/20-工作模型集合索引.md`、`docs/specs/21-ADR-决策.md`、`docs/specs/26-Task-任务.md`、`docs/specs/40-工作流程集合索引.md`、`docs/specs/41-landing-orchestration-规范落地统筹.md`、`docs/specs/42-ldvh-landing-check-LDVH落地与检查.md`

---

## 1. 本文解决的问题

本文用于替代后续主要参考中的 18、19、20 号历史调研文档，集中回答 LDVH 下一阶段到底应该优先做什么。

此前 18、19、20 三份文档分别回答了不同问题：

| 文档 | 主要问题 | 保留价值 | 需要修正或合并的点 |
|---|---|---|---|
| 18 | LDVH 当前推进评估、缺口清单、候选事项分流 | 明确 AI 执行者需求、已完成项、缺口和候选承接 | 对 apply / repair、CLI、平台映射的优先级偏保守 |
| 19 | LDVH 应向 ECC 学习哪些运行系统机制 | 提炼 manifest、plan/apply/verify、CLI、status/doctor、平台投影、资产分层 | 仍偏向先只读诊断，未充分处理安装/落地初始化不可缺位的问题 |
| 20 | 深入说明 LDVH 应学习 ECC 的组织方法而非内容规模 | 明确学方法、不学安装器、不学资产库、不建第二事实源 | “先做自动 apply / repair”被列为不该做，需改为“不做无授权自动 apply / repair，但要做受控自动执行” |

本文的核心修正是：

```text
不要安装器，但必须有安装/落地流程。
不要无授权自动 apply / repair，但必须有 Human 授权后的自动执行、自动修复和审核链路。
不要把测试放到实现之后补票；受控执行必须测试先行，先定义失败条件、成功条件、正反样例和验证命令。
不要一口气做大而全 CLI，但必须逐步建设面向 AI 的最小统一入口。
不要长期第二状态源，但必须有可回指 Git 文件事实源的状态视图和审核队列。
不要把跨环境相关事项展开在受控执行闭环文档中；相关计划由 22 承接。
```

本文后续如被采纳，应作为 18、19、20 删除前的主要吸收文档。删除 18、19、20 前，应确认本文已经保留必要结论、来源和边界说明。

---

## 2. 当前总判断

LDVH 当前不应继续只停留在“能检查、能诊断、能展示”的阶段，而应进入“能受控执行、修复、验证、审核并回写”的阶段。

下一阶段主线应从：

```text
只读诊断闭环
```

升级为：

```text
受控落地执行闭环
```

更完整地说：

```text
Read Entry
→ Landing Plan
→ Test Design
→ Human Approve
→ Auto Apply / Repair
→ Verify
→ Review Needed
→ Web / AI Review
→ Close / Writeback
→ Recheck
```

这条链路是 LDVH 当前最需要补齐的核心运行能力。它不是 ECC 式安装器，不引入安装状态库，不复制 ECC 的 profile、executor、repair store 或跨环境分发系统；但它承认一个现实问题：如果没有“安装/落地初始化/接入/补齐”这一步，LDVH 后续 Code、Web、CLI、Human Gate 和自动化都无法稳定推进。跨环境相关事项由 `docs/research/22-LDVH跨环境能力复用与薄投影落地计划.md` 单独承接。

---

## 3. 基础原则修正

### 3.1 不要安装器，但要落地安装流程

LDVH 不应建设独立 installer product。

不需要的是：

1. ECC 式安装器；
2. 可配置 profile 选择器；
3. 独立安装 executor；
4. 安装状态持久化数据库；
5. 跨环境自动分发系统；
6. 一次性复制大量第三方 Rules、Skills、Commands、Agents。

但 LDVH 必须建设的是：

1. clone 或接入后的最小初始化检查；
2. 当前平台、入口、事实源、工作对象和规范状态识别；
3. 落地计划生成；
4. Human Gate 授权；
5. 自动补齐和自动修复；
6. 自动验证；
7. 待审核状态；
8. Web 或 AI 审核；
9. 事实源回写；
10. 复检。

因此准确表述应是：

```text
LDVH 不需要 installer，但需要 landing workflow。
```

### 3.2 不要无授权自动修复，但要受控自动 apply / repair

此前文档中“先不做 apply / repair”的表述需要修正。

LDVH 真正不能接受的是：

1. 无计划直接写入；
2. 无 Human Gate 自动修复；
3. 自动关闭缺口；
4. 自动改变 Task、ADR、规范或运行投影状态；
5. 用工具输出替代验证证据；
6. 用 repair 结果替代 Human 审核。

LDVH 应建设的是：

```text
Plan 只读
→ Human Gate 授权
→ Auto Apply / Repair 自动执行
→ Verify 自动验证
→ Review Needed 待审核
→ Web / AI Review 审核
→ Close / Writeback 回写
→ Recheck 复检
```

这意味着自动执行不是问题，自动授权才是问题。Human Gate 的职责不是让人手工完成所有改动，而是让 Human 决定是否允许 AI/Code 在明确边界内自动执行。

### 3.3 不要把测试放到实现之后补票，要测试先行

受控落地执行闭环如果只强调 apply / repair，很容易滑向“先改了再说”的模式。LDVH 下一阶段必须把测试先行写入执行链路：任何新的 apply、repair、verify、CLI、Web 审核或事实源回写能力，在进入实现前都应先明确它要证明什么、失败时如何暴露、通过后留下什么证据。

本文所说的测试先行不等于所有场景都机械套用经典 TDD，也不要求所有判断都先写自动化测试代码；它要求的是可验证先行：

1. 先明确规则来源、成功条件和失败条件；
2. 先定义正例、反例和边界样例；
3. 先确定自动化测试、校验命令或等价验证方式；
4. 修复已知 bug 时，优先先补能复现失败的测试或最小复现样例；
5. 无法先写自动化测试时，必须说明原因、等价验证方式和残留风险；
6. 未完成验证设计的 apply / repair 不应进入自动执行阶段。

因此，受控落地执行链路应从：

```text
plan → approve → apply/repair → verify
```

进一步收紧为：

```text
plan → test design → approve → apply/repair → verify → review
```

测试先行要服务的不是测试形式，而是防止 AI 在没有失败条件、没有验收标准、没有可复现证据的情况下自动修改、自动修复或宣称完成。

### 3.4 不要大而全 CLI，但要最小统一 CLI

LDVH 不应一次性设计庞大的命令树，也不应绕开现有 `tools/` 重造一套产品化 CLI。

但 LDVH 应尽早形成面向 AI 的最小统一入口，降低 AI 记忆多个脚本和参数的负担。

建议方向是先包装高频能力：

```text
ldvh status
ldvh landing plan
ldvh landing apply
ldvh landing repair
ldvh landing verify
ldvh landing review
ldvh facts list/show/search/stats
ldvh specs index/validate
```

CLI 的首要定位不是产品门面，而是 Code 构成要素的稳定运行入口。每个命令都必须有输入、输出、exit code、事实源回指、写入边界、Human Gate 条件和验证方式。

### 3.5 不要长期第二状态源，但要派生状态视图

长期状态源是指脱离 Git 文件事实源、却开始承载权威状态的机制，例如：

1. `.local/ldvh-state.json`；
2. SQLite 或 Web 数据库；
3. 安装状态 registry；
4. repair history store；
5. session store；
6. Web 内部状态表。

如果这些状态开始决定“哪个缺口已关闭、哪个 Human Gate 已通过、哪个 Task 已完成、哪个规范已落地”，而 Git 文件事实源没有对应记录，它们就会成为第二事实源。

LDVH 可以拥有：

1. 临时运行缓存；
2. CLI 派生输出；
3. Web 派生视图；
4. status / audit / doctor 报告；
5. review queue 派生队列；
6. landing plan 过程输出。

但它们必须满足：

```text
可回指 Git 文件事实源；不替代 Task、ADR、specs、Human Gate 记录或验证证据；稳定结论必须回写权威事实源。
```

### 3.6 跨环境相关事项由 22 单独承接

跨环境相关事项不在本文展开，统一见 `docs/research/22-LDVH跨环境能力复用与薄投影落地计划.md`。

---

## 4. 当前现状与缺口

### 4.1 已有基础

截至 2026-06-11，LDVH 已经具备以下基础：

| 领域 | 当前状态 |
|---|---|
| 总纲 | 00 已明确五类构成要素、事实源原则、V1-V10 价值标准 |
| 入口 | `LDVH-AI-ENTRY.md` 已形成最小启动顺序、场景路由、查询命令和 STOP 点 |
| 工作模型 | ADR、Change、Pitfall、Intent、Memo、Task 已成为 active 工作模型 |
| 工作流程 | 41 规范落地统筹、42 LDVH落地与检查、44 多角色思考已 active |
| Code | `landing-report`、`landing-plan`、`runtime-projection`、`human-gate-report`、`ldvh-landing-check`、`web-validate` 已有基础 |
| Web | Dashboard、ObjectList、ObjectDetail、Validate、Changelog、ReadingPanel 等已有基础 |
| Human Gate | 最小证据结构已进入 06、08、21、26、41，Code 已能检查记录块 |
| 运行投影 | 04.06 §6 已吸收 target adapter 分层思想 |

### 4.2 仍然卡住的地方

当前关键问题不是“没有规范”，而是运行闭环没有打通。

主要缺口包括：

| 缺口 | 影响 | 下一步方向 |
|---|---|---|
| landing-report / landing-plan 仍偏诊断 | 能列缺口，但还不能充分承接验证证据、工作对象证据和 Human Gate 记录 | 增强证据接入和缺口承接关系 |
| apply / repair 链路缺失 | 计划后不能自动补齐和修复，导致检查结果无法推动执行 | 建立 Human 授权后的自动执行与自动修复 |
| verify / review 状态不够明确 | 执行后如何进入待审核、谁审核、怎么回写不稳定 | 引入 review_needed 和审核证据链 |
| Web Validate 仍偏展示 | Human 能看见摘要，但确认、审核、证据导出和回写链路未闭环 | 升级为检查与审核闭环面 |
| CLI 入口分散 | AI 仍需记住多个 Python 工具和参数 | 建设最小统一 CLI |
| 跨环境事项需要独立收敛 | 如果继续放在本文，受控执行闭环主线会被稀释 | 不在本文处理，统一由 22 承接 |
| 长期状态源边界需要持续防护 | Web、CLI、缓存容易滑向第二事实源 | 明确所有状态视图必须回指 Git 文件事实源 |

---

## 5. LDVH 受控落地执行闭环

### 5.1 总流程

LDVH 下一阶段应围绕以下流程推进：

```text
Read Entry
→ Landing Plan
→ Test Design
→ Human Approve
→ Auto Apply / Repair
→ Verify
→ Review Needed
→ Web / AI Review
→ Close / Writeback
→ Recheck
```

### 5.2 阶段职责

| 阶段 | 职责 | 主要承接 | 写入边界 |
|---|---|---|---|
| Read Entry | 识别当前项目、入口、平台、事实源、管辖关系和任务场景 | AI 入口、Code 查询 | 只读 |
| Landing Plan | 生成范围、事实源、缺口、建议动作、Human Gate、验证和回写目标 | 41、42、Code | 只读 |
| Test Design | 在授权和实现前定义成功条件、失败条件、正反样例、边界样例、测试命令或等价验证方式 | 07、10、tests、Code、Task | 只读，形成测试设计或测试用例需按事实源边界回写 |
| Human Approve | Human 确认执行范围、风险、目标文件、授权方式和验证方案 | AskUserQuestion、Web、手工确认 | 写入授权记录或当前会话证据 |
| Auto Apply / Repair | 在授权边界内自动补齐文件、修复结构、生成记录或执行工具 | Code、AI、CLI | 只写 plan 中允许目标 |
| Verify | 执行测试、校验、复检和结果聚合 | Code、tests、CLI | 通常只读，必要时写验证产物需授权 |
| Review Needed | 将执行结果转入待审核状态 | Task、Web、派生队列 | 稳定状态应回 Task 或对应事实源 |
| Web / AI Review | Human 通过 Web 审核，或通知 AI 基于证据审核 | Web、AI、Human Gate | 审核结论需可追溯 |
| Close / Writeback | 通过后回写 Task、ADR、Memo、Pitfall、specs、Code 或 Web 文档 | 对应事实源 | 需符合模型状态机和 Human Gate |
| Recheck | 复跑 42、fact/spec 校验和相关测试 | Code、CLI | 只读 |

### 5.3 最小验收标准

第一轮闭环至少应满足：

1. 能生成 landing plan；
2. plan 能列出要读、要改、要验证、要回写的对象；
3. plan 能明确是否需要 Human Gate；
4. 在 Human 授权和自动执行前，能定义成功条件、失败条件、正反样例、边界样例、测试命令或等价验证方式；
5. 修复已知问题时，能优先补出失败复现测试或最小复现样例；
6. Human 能确认执行边界和验证方案；
7. 授权后能自动执行一个安全、可回滚、可验证的补齐或修复；
8. 执行后能自动验证；
9. 结果能进入 review_needed；
10. Web 或 AI 能展示审核材料；
11. Human 审核结论能留下最小证据；
12. 稳定结果能回写 Git 文件事实源；
13. 复跑 42 或相关校验能消费结果。

---

## 6. 自动 apply / repair 的边界

### 6.1 可以自动执行的内容

Human Gate 授权后，可以自动执行：

1. 创建缺失但明确授权的薄入口；
2. 修复格式、路径引用、表结构等机械性问题；
3. 生成 plan 中列明的 Task、Memo、ADR proposed 草案或 Human Gate 记录；
4. 更新明确授权的 Web 文档或 Code 合同；
5. 执行已列明的校验命令；
6. 将验证结果写入指定事实源或待审核产物；
7. 将任务转入 review_needed。

### 6.2 不得自动执行的内容

即使存在 repair 建议，也不得自动执行：

1. 未经 Human Gate 的高影响事实源写入；
2. 自动接受、废弃、替代 ADR；
3. 自动关闭 Task 或宣称验收完成；
4. 自动修改正式规范核心决策；
5. 自动 push、release、merge；
6. 自动创建长期状态源；
7. 自动将 Web、CLI、缓存输出升格为事实源；
8. 自动绕过失败验证。

### 6.3 repair 的正确定位

repair 不是“修完即完成”，而是：

```text
在授权范围内自动执行候选修复，并把结果送入验证和审核。
```

repair 完成后的默认状态应是：

```text
review_needed
```

而不是：

```text
closed
```

---

## 7. 最小 CLI 路线

### 7.1 CLI 的定位

LDVH CLI 是 AI 应用的稳定入口，不是安装器，也不是第二事实源。

它的价值是：

1. 降低 AI 发现成本；
2. 统一输出合同；
3. 稳定 exit code；
4. 让 Web、AI、CI 或 Hook 可以消费同一组 Code 能力；
5. 支撑 plan、apply、repair、verify、review、status 的闭环。

### 7.2 建议最小命令

第一阶段建议聚焦：

```text
ldvh status
ldvh landing plan
ldvh landing apply
ldvh landing repair
ldvh landing verify
ldvh landing review
ldvh facts stats
ldvh facts list
ldvh facts show
ldvh specs validate
```

底层可以先包装现有 `tools/specs_validate.py`、`tools/fact_cli.py`、`tools/fact_validate.py`，不急于重写。

### 7.3 命令合同

每个命令至少定义：

| 字段 | 要求 |
|---|---|
| trigger | 何时由 AI、Human、Web、Hook 或 CI 调用 |
| input | 参数、默认范围、路径和模式 |
| source_of_truth | 必须读取哪些 Git 文件事实源 |
| output | 人读文本和机器可读 JSON |
| exit_code | 成功、失败、发现缺口、需要 Human Gate、验证失败等 |
| write_policy | 默认只读；写入命令必须显式声明目标和授权 |
| human_gate | 何时必须暂停并确认 |
| validation | 命令自身如何测试 |
| writeback_targets | 稳定结论应回写位置 |

---

## 8. Web 的下一阶段定位

### 8.1 Web 不只是展示面

Web 当前已有 Validate 摘要展示能力，但下一阶段应承担 Human-facing 检查与审核闭环面。

Web 的重点不是开放式编辑后台，而是：

1. 展示 landing plan；
2. 展示 proposed actions；
3. 展示 Human Gate 待确认事项；
4. 展示自动 apply / repair 结果；
5. 展示验证结果；
6. 展示 review_needed 队列；
7. 支持 Human 审核；
8. 导出或回写 Human Gate 最小证据；
9. 提示下一轮验证命令；
10. 回指 Git 文件事实源。

### 8.2 Web 不应做什么

Web 不应先做：

1. 开放式 YAML 编辑后台；
2. 任意字段写入；
3. 绕过 Code 校验的写入；
4. 替代 Human 判断；
5. 替代 Git 文件事实源；
6. 自动关闭 Task 或 ADR；
7. 保存不可回指事实源的长期状态。

### 8.3 Review Needed 队列

Web 可以呈现 review_needed 队列，但队列本身应是派生视图或回指事实源状态。

review_needed 的来源可以包括：

1. Task 状态；
2. landing apply / repair 结果；
3. Human Gate 待确认项；
4. 验证失败后的人工判断项；
5. ADR proposed 待决策项；
6. Web 受控回写待确认项。

---

## 9. 跨环境事项衔接

跨环境相关事项不再作为本文的展开内容，统一由 `docs/research/22-LDVH跨环境能力复用与薄投影落地计划.md` 承接。

---

## 10. 下一阶段优先级

### 10.1 P0：受控落地执行闭环

P0 不是继续写更多抽象文档，而是打通最小链路：

```text
plan → test design → approve → apply/repair → verify → review_needed → review → writeback → recheck
```

P0 子项：

1. 明确 landing plan 输出合同中的写入边界、Human Gate、验证和回写字段；
2. 在每个 apply / repair 实现前，先定义成功条件、失败条件、正反样例和测试命令；
3. 实现最小 landing apply；
4. 实现最小 landing repair；
5. 实现 landing verify；
6. 定义 review_needed 的承载方式；
7. 让 Web Validate 或新检查面展示待审核项；
8. 让 Human Gate 证据能导出或回写；
9. 复跑 42 消费结果。

### 10.2 P1：最小统一 CLI

P1 目标是让 AI 不再记忆多个 Python 脚本。

P1 子项：

1. 包装 status；
2. 包装 landing plan；
3. 包装 landing apply / repair / verify；
4. 包装 facts 查询；
5. 包装 specs 校验；
6. 统一 JSON 输出和 exit code。

### 10.3 P1：Web 检查与审核面

Web 应从展示面升级为检查和审核面。

P1 子项：

1. 展示 plan；
2. 展示 proposed actions；
3. 展示 apply / repair 结果；
4. 展示验证结果；
5. 展示 review_needed；
6. 支持审核结论生成；
7. 支持 Human Gate 最小证据导出或受控回写。

### 10.4 暂缓项

继续暂缓：

1. ECC 式安装器；
2. profile 选择器；
3. 长期状态数据库；
4. 多平台自动分发；
5. 大规模 Skill / Agent / Rules 资产库；
6. 自动 push / release / merge；
7. Web 开放式任意编辑后台。

---

## 11. 需要进入 ADR 或 Task 的事项

本文是 research，不具备正式决策效力。以下事项建议后续进入 ADR 或 Task。

### 11.1 建议进入 ADR

建议创建 proposed ADR：

```text
LDVH 采用受控落地执行链路而非独立安装器
```

ADR 应记录的决策：

1. LDVH 不建设 ECC 式 installer；
2. LDVH 必须建设 landing workflow；
3. 自动 apply / repair 允许存在，但必须在 Human Gate 授权后执行；
4. repair 完成后默认进入 review_needed，不自动 closed；
5. Web/CLI/status 只能作为派生视图，不能成为第二事实源；
6. 最小统一 CLI 是 AI 应用入口，不是安装器；
7. 受控落地执行链路必须测试先行：在 apply / repair 实现前先定义成功条件、失败条件、正反样例和验证方式；
8. 跨环境相关决策由 22 号文档单独承接。

### 11.2 建议进入 Task

建议创建 Task：

```text
打通 LDVH 受控落地执行闭环
```

验收标准：

1. landing plan 能列明读、写、验证、Human Gate 和回写目标；
2. 在 Human 授权和自动执行前，能定义成功条件、失败条件、正反样例和测试命令；
3. 修复已知问题时，能优先补出失败复现测试或最小复现样例；
4. Human 能确认执行边界和验证方案；
5. apply / repair 能在授权边界内自动执行；
6. verify 能自动复检；
7. 执行结果进入 review_needed；
8. Web 能展示待审核项和证据；
9. Human 审核结果能回写；
10. 42 能消费回写结果；
11. 不引入第二事实源。

---

## 12. 18、19、20 删除前处理建议

如果未来删除 18、19、20，应先完成以下检查：

1. 18 中的当前状态、已完成项、候选事项和缺口是否已被本文、正式规范、Task 或 Code 吸收；
2. 19 中的 ECC 六类机制是否已被本文保留；
3. 20 中的“学方法、不学内容；学结构、不学规模；学组织、不学实现；学约束、不学功能”是否已被本文保留；
4. 20 中 ECC 预处理素材索引是否仍需保留在 refs 或另建索引；
5. 涉及正式规范、ADR、Task、Code、Web 的稳定结论是否已经写入对应权威位置；
6. 删除后是否会造成路径引用断裂；
7. 是否需要用 Task 记录删除原因和验证结果。

18、19、20 删除后，本文仍不自动成为正式规范。它只是新的主要 research 参考。稳定执行依据仍需进入 specs、ADR、Task、Code、Web 或运行投影。

---

## 13. 阶段性结论

LDVH 下一阶段的关键不是继续证明“应该只读诊断”，也不是复制 ECC 的安装器、CLI、状态库或资产库，而是建设自己的受控落地执行闭环。

最终方向可以概括为：

```text
以 AI 执行者为第一服务对象，
以 Git 文件为最终事实源，
以 Human Gate 划定授权边界，
以测试先行防止无验证自动执行，
以 Code 执行自动 apply / repair / verify，
以 Web 承接 Human 审核和证据回写，
以 Task / ADR / specs 承载稳定结论，
以最小 CLI 降低 AI 使用成本。
```

一句话结论：

```text
LDVH 不做安装器，但必须打通受控落地执行链路；不做无授权自动修复，但必须支持授权后的自动 apply / repair；不做第二事实源，但必须让状态、审核和验证可见、可追溯、可复检；不做无验证自动执行，但必须在实现前先定义失败条件、成功条件和验证方式。
```
