# Superpowers 深度调研：TDD 强制、工程纪律与 LDVH 借鉴

> 创建日期：2026-06-05
> 定位：对 Superpowers 项目的代码级深度调研，覆盖核心理念、TDD 强制机制、人工确认环节、测试流程、子代理架构及对 LDVH 的借鉴价值
> 调研边界：不直接构成强制规则；结论进入正式规范或 ADR 后才成为稳定执行依据
> 代码调研来源：`/Users/dmh2002/trae_projects/superpowers`（完整代码库）
> 上位参考：`specs/evals/21-LDVH全盘确认与核心吸收建议.md`

---

## 1. 本文解决的问题

本文沉淀对 Superpowers 项目的深度调研结论，作为 LDVH 在工程纪律、TDD 强制、子代理架构和反合理化机制方面的决策参考：

1. Superpowers 的核心理念与 TDD 强制机制——理解"铁律级"约束如何设计
2. 完整 Skill 体系与工作流——理解可组合 Skill 如何编排端到端开发流程
3. 人工确认环节——理解 Superpowers 的 Human Gate 分布和设计逻辑
4. 测试流程与反模式——理解 TDD 循环、验证铁律和测试反模式体系
5. 子代理驱动开发——理解控制器-工作者模式的两阶段审查架构
6. 对 LDVH 的可借鉴之处——理解哪些机制可直接吸收、哪些需要适配

---

## 2. 项目概述与定位

### 2.1 基本信息

- **作者**：obra（独立开发者）
- **定位**：面向 AI 编码代理的完整软件开发方法论
- **核心载体**：Claude Code Skill 包 + CLAUDE.md 初始指令
- **协议**：开源
- **GitHub Star**：约 6.2 万

### 2.2 与 Gstack 的定位差异

| 维度 | Superpowers | Gstack |
|------|-------------|--------|
| 核心隐喻 | 工程纪律 | 虚拟团队 |
| 第一价值 | 正确性 | 速度 |
| TDD | 铁律级强制 | 建议级 |
| 人类角色 | "人类伙伴"（对等协作） | "用户"（被服务者） |
| 审查模式 | 两阶段强制审查 | 单次可选审查 |
| 代理架构 | 子代理驱动 + 新鲜实例 | 单代理 + 可选 OpenClaw |

### 2.3 四大哲学支柱

1. **测试驱动开发** — 永远先写测试
2. **系统性优于临时性** — 流程优于猜测
3. **复杂度消减** — 简洁为首要目标
4. **证据优于断言** — 验证后再宣告成功

---

## 3. 核心理念与 TDD 强制机制

### 3.1 TDD 铁律（The Iron Law）

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

**违反后果——删除代码，从头开始：**

- 先写代码再写测试？删除代码，从测试开始
- **不得**保留代码作为"参考"
- **不得**在写测试时"适配"已有代码
- **不得**查看已写的代码
- 删除就是删除，无例外

**"违反规则的字面意思就是违反规则的精神"**——这句话直接切断了"我遵循精神但不遵循形式"的合理化路径。

### 3.2 验证铁律

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

**门控函数（Gate Function）：**

1. 识别：什么命令能证明这个声明？
2. 运行：执行完整命令（全新、完整）
3. 阅读：完整输出，检查退出码，计算失败数
4. 验证：输出是否确认声明？
5. 只有此时：才能做出声明

**红旗——立即停止：**

- 使用"应该"、"可能"、"看起来"
- 在验证前表达满意（"太好了！"、"完美！"、"完成！"）
- 即将提交/推送/PR 但未验证
- 信任代理成功报告

### 3.3 调试铁律

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

**3+ 修复失败规则**：同一 bug 修复失败 3 次以上 → 停止修复 → 与人类伙伴讨论架构问题。

### 3.4 Skill 铁律

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

编写 Skill 就是将 TDD 应用于过程文档：先观察无 Skill 时代理的违规行为（RED），再写 Skill 使代理合规（GREEN），最后堵住漏洞同时保持合规（REFACTOR）。

### 3.5 TDD 例外条件

仅限抛弃式原型、生成代码、配置文件，且**必须询问人类伙伴**获得许可。

### 3.6 合理化反驳表

Superpowers 列出了 11 种常见借口及反驳：

| 借口 | 反驳 |
|------|------|
| "太简单不需要测试" | 简单的代码也有 bug |
| "这只是重构" | 重构需要测试保护 |
| "TDD 太慢了" | 调试时间远超写测试时间 |
| "我会回头补测试" | 你不会的 |
| "TDD 是教条主义" | 随意性才是真正的教条 |
| ... | ... |

---

## 4. 完整 Skill 清单与工作流

### 4.1 Skill 总览

| Skill | 触发条件 | 核心职责 |
|-------|---------|---------|
| brainstorming | 任何创造性工作之前 | 探索→提问→方案→设计文档→自审→用户审阅 |
| writing-plans | 有 spec 的多步骤任务 | 范围检查→文件映射→任务编写→自审→执行选择 |
| subagent-driven-development | 在当前会话执行实现计划 | 控制器→实现子代理→规格审查→质量审查→循环 |
| executing-plans | 在单独会话执行实现计划 | 加载→审查→逐任务执行→完成分支 |
| test-driven-development | 实现功能或修复 bug 前 | RED→验证 RED→GREEN→验证 GREEN→REFACTOR |
| verification-before-completion | 即将声称完成时 | 识别验证命令→运行→阅读输出→确认 |
| requesting-code-review | 完成任务或合并前 | 获取 SHA→分派审查子代理→按反馈行动 |
| receiving-code-review | 收到审查反馈时 | 阅读→理解→验证→评估→响应→实现 |
| finishing-a-development-branch | 实现完成，决定如何集成 | 验证测试→检测环境→呈现选项→执行→清理 |
| dispatching-parallel-agents | 2+ 独立任务 | 识别域→创建任务→并行分派→审查集成 |
| systematic-debugging | 遇到 bug 或测试失败 | 根因调查→模式分析→假设测试→实现修复 |
| using-git-worktrees | 需要隔离的功能工作 | 检测→创建 worktree→项目设置→验证基线 |
| writing-skills | 创建或编辑 Skill | TDD 映射→压力场景→写 Skill→验证合规 |
| using-superpowers | 开始任何对话时 | Skill 路由→优先级判断→调用 |

### 4.2 核心工作流

```
brainstorming → writing-plans → subagent-driven-development → finishing-a-development-branch
                                    ↓
                        test-driven-development（每个任务内）
                        verification-before-completion（每个声明前）
                        requesting-code-review（每个任务后）
```

### 4.3 子代理驱动开发详解

**架构**：控制器-工作者模式

- **控制器（主会话）**：读取计划、提取任务、分派子代理、协调审查
- **实现子代理**：每任务一个新实例，隔离上下文，不继承会话历史
- **规格审查子代理**：独立读取代码，不信任实现者报告
- **代码质量审查子代理**：在规格合规后进行

**两阶段审查顺序不可逆**：规格合规 → 代码质量（不可跳过或反转）

**模型选择策略**：

| 任务类型 | 模型选择 |
|---------|---------|
| 机械实现（1-2 文件，完整 spec） | 便宜模型 |
| 集成和判断（多文件协调） | 标准模型 |
| 架构/设计/审查 | 最强模型 |

**子代理状态**：

| 状态 | 含义 | 处理 |
|------|------|------|
| DONE | 完成 | 进入规格审查 |
| DONE_WITH_CONCERNS | 完成但有疑虑 | 先读关切再继续 |
| NEEDS_CONTEXT | 缺少信息 | 提供上下文重新分派 |
| BLOCKED | 无法完成 | 评估后可能升级给人类 |

**连续执行原则**：不在任务间暂停检查，除非 BLOCKED、真正歧义或全部完成。

---

## 5. 人工确认环节完整清单

| 序号 | 环节 | Skill | 确认类型 | 说明 |
|------|------|-------|---------|------|
| 1 | 设计分段审批 | brainstorming | 逐段确认 | 每个设计分段后获取批准 |
| 2 | 视觉伴侣同意 | brainstorming | 同意/拒绝 | 独立消息，不与其他内容混合 |
| 3 | 书面 Spec 审阅 | brainstorming | 审阅确认 | 用户审阅 spec 文件后才能继续 |
| 4 | TDD 例外请求 | test-driven-development | 人类许可 | 抛弃式原型等例外需人类伙伴同意 |
| 5 | Worktree 创建同意 | using-git-worktrees | 同意/拒绝 | "是否设置隔离 worktree？" |
| 6 | 基线测试失败处理 | using-git-worktrees | 继续/调查 | 测试失败时是否继续 |
| 7 | 执行方式选择 | writing-plans | 二选一 | 子代理驱动 vs 内联执行 |
| 8 | 计划关切 | executing-plans | 讨论后继续 | 对计划有疑问时先讨论 |
| 9 | 阻塞升级 | subagent-driven-development | 人类介入 | 计划本身有问题时升级 |
| 10 | 分支完成选项 | finishing-a-development-branch | 四选一/三选一 | 合并/PR/保留/丢弃 |
| 11 | 丢弃确认 | finishing-a-development-branch | 输入 "discard" | 必须精确输入确认 |
| 12 | 代码审查推回 | receiving-code-review | 与人类讨论 | 架构级冲突时停止讨论 |
| 13 | 3+ 修复失败 | systematic-debugging | 架构讨论 | 质疑架构，与人类伙伴讨论 |
| 14 | PR 提交前 | CLAUDE.md | 完整 diff 审阅 | 人类必须审阅完整 diff |

**设计特点**：

1. **确认点服务于纪律而非偏好**：与 Gstack 的"偏好选择型"确认不同，Superpowers 的确认点服务于工程纪律
2. **反合理化设计**：每个铁律都有合理化反驳表和红旗清单
3. **升级路径明确**：阻塞 → 上下文补充 → 更强模型 → 拆分 → 升级人类
4. **"人类伙伴"定位**：人类是对等协作者，不是被服务者

---

## 6. 测试流程详解

### 6.1 TDD 循环

**严格顺序**：RED → 验证 RED → GREEN → 验证 GREEN → REFACTOR → 验证 GREEN → 下一个 RED

**每步必须运行命令验证**：

- RED 阶段：运行测试 — 确认测试失败（非错误）
- GREEN 阶段：运行测试 — 确认测试通过且其他测试仍通过
- REFACTOR 后：再次验证全绿

### 6.2 测试反模式（5 种）

| 反模式 | 问题 | 修复 |
|--------|------|------|
| 测试 Mock 行为 | 验证 mock 存在而非组件工作 | 测试真实组件或取消 mock |
| 生产类中添加测试专用方法 | 污染生产代码，危险 | 移到测试工具类 |
| 不理解依赖就 Mock | Mock 破坏测试逻辑 | 先理解依赖链，最小化 mock |
| 不完整 Mock | 隐藏结构假设，静默失败 | 镜像真实 API 完整结构 |
| 集成测试作为事后补充 | 测试是实现的组成部分 | TDD 循环 |

**三条铁律**：

1. 永远不测试 mock 行为
2. 永远不在生产类中添加测试专用方法
3. 永远不在不理解依赖的情况下 mock

### 6.3 回归测试验证

```
写测试 → 运行(通过) → 撤销修复 → 运行(必须失败) → 恢复 → 运行(通过)
```

### 6.4 集成测试框架

- 使用真实 Claude Code 会话运行
- 解析 `.jsonl` 会话记录验证行为
- 包含 token 使用分析
- 测试运行时间 10-30 分钟

---

## 7. 安全护栏与工程纪律

### 7.1 安全护栏

| 护栏 | 位置 | 机制 |
|------|------|------|
| 不在 main/master 上直接实现 | subagent-driven-development | 显式用户同意例外 |
| Worktree 来源检查 | finishing-a-development-branch | 仅清理 Superpowers 创建的 worktree |
| .gitignore 验证 | using-git-worktrees | 创建 worktree 前必须验证目录被忽略 |
| 子模块误判防护 | using-git-worktrees | `git rev-parse --show-superproject-working-tree` |
| PR 人类审阅 | CLAUDE.md | 人类必须审阅完整 diff |
| 代理身份披露 | CLAUDE.md | 必须披露模型、工具、版本、插件 |
| 丢弃确认 | finishing-a-development-branch | 必须输入 "discard" |

### 7.2 反合理化体系

Superpowers 的独特之处在于**系统性地对抗 AI 代理的合理化倾向**：

- **"违反字面就是违反精神"** — 切断"我遵循精神"的借口
- **合理化反驳表** — 每种常见借口配对应现实
- **红旗清单** — 自检清单，出现任何一条就停止重来
- **"删除就是删除"** — 不保留、不参考、不适配
- **Skill 测试中的压力场景** — 故意施加时间压力、沉没成本、权威压力测试 Skill 的抗合理化能力

### 7.3 CSO 关键发现

Superpowers 发现：**描述中总结工作流会导致 Claude 走捷径跳过 Skill 正文**。因此：

- Skill 描述只写触发条件，不写流程
- 避免让 AI 通过描述就能"跳过"读取完整规则

---

## 8. 对 LDVH 的可借鉴之处

### 8.1 高度契合点

| LDVH 需求 | Superpowers 实践 | 借鉴价值 |
|-----------|-----------------|---------|
| Human Gate | 14 个人工确认点 | Superpowers 的确认点更细粒度，可参考其"何时必须暂停"的判断标准 |
| 可审计性 | 每步验证、git SHA 追踪、会话记录 | 两阶段审查 + 审查循环提供了可追溯的质量链 |
| 状态机 | 子代理四状态 | 可参考为 LDVH Task 状态机的子状态设计 |
| 事实源 | 设计文档 → 计划文档 → git 提交链 | Superpowers 的文档链与 LDVH 的 Intent → Task → Memo 链异曲同工 |

### 8.2 具体可借鉴机制

**1. 反合理化体系 → 强化 LDVH 状态机守卫**

LDVH 已有"不得绕过对象状态机"的禁令，但缺少对 AI 合理化倾向的系统性对抗。可借鉴：

- 为每条禁令添加合理化反驳表
- 添加红旗自检清单
- "违反字面就是违反精神"原则写入规则

**2. 两阶段审查 → LDVH Task 验证流程**

LDVH 的 `verifying` → `review_needed` 状态流转可借鉴 Superpowers 的两阶段审查：

- 第一阶段：规格合规（是否做了该做的事）
- 第二阶段：质量合规（是否做好了该做的事）
- 审查发现问题 → 修复 → 重新审查（循环直到通过）

**3. 验证铁律 → LDVH Task 关闭条件**

LDVH 的 `closure_evidence` 要求可借鉴 verification-before-completion：

- 关闭 Task 前必须运行验证命令
- 必须看到完整输出
- "应该通过"不等于"通过"
- 代理报告"成功"不等于成功

**4. 子代理驱动开发 → LDVH 子任务执行**

LDVH 的"子任务不得再创建子任务"规则与 Superpowers 的单层子代理架构一致。可进一步借鉴：

- 子代理不继承会话上下文（控制器构建精确上下文）
- 子代理状态报告标准化
- 阻塞升级路径（上下文问题 → 更强模型 → 拆分 → 升级人类）

**5. Skill TDD → LDVH 规范验证**

Superpowers 用子代理压力场景测试 Skill 的抗合理化能力。LDVH 可借鉴：

- 用压力场景测试规则是否被 AI 遵守
- 先观察无规则时的违规行为，再针对性写规则
- 持续发现新的合理化路径并堵住

**6. CSO 设计原则 → LDVH Skill/规则描述**

Superpowers 发现描述中包含流程摘要会导致 AI 走捷径。LDVH 的 Skill 描述应：

- 只写触发条件，不写流程
- 避免让 AI 通过描述就能"跳过"读取完整规则

**7. 连续执行 + 阻塞升级 → LDVH 执行效率**

Superpowers 的"不在任务间暂停，除非阻塞"原则可优化 LDVH 的执行效率：

- 非关键节点连续执行
- 仅在 Human Gate 要求时暂停
- 阻塞时提供结构化升级路径

**8. 3+ 修复失败 → 架构质疑**

LDVH 可借鉴此模式：当同一 Task 反复修复失败时，不是继续尝试修复，而是停下来质疑设计/架构决策，与人类讨论。

### 8.3 需要注意的差异

| 维度 | Superpowers | LDVH | 适配注意 |
|------|-------------|------|---------|
| 领域 | 通用软件开发 | Vibe Coding 治理 | LDVH 更侧重治理而非实现 |
| 事实源 | 文件系统 + Git | YAML 事实实例 + Git | LDVH 需要更严格的事实实例编辑入口 |
| 状态持久化 | 会话级 | 跨会话持久化 | LDVH 的状态机需要跨会话一致性 |
| 人类角色 | "伙伴"（对等协作） | "Gate"（审批守卫） | LDVH 的 Human Gate 更偏向审批而非协作 |
| 规范来源 | Skill 文档 | specs/ 规范体系 | LDVH 有更正式的规范层级和契约 |

### 8.4 不应照搬的

1. **TDD 铁律的绝对化**：LDVH 是治理框架而非开发方法论，TDD 强制度应根据项目规模调整
2. **会话级状态**：Superpowers 的状态不跨会话持久化，LDVH 需要跨会话的状态机
3. **子代理新鲜实例模式**：LDVH 在 Trae Solo 中受限于终端数量，不能无限创建子代理
4. **连续执行不暂停**：LDVH 的 Human Gate 是治理纪律，不能为了效率跳过

---

## 9. 来源

### 9.1 代码来源

- `/Users/dmh2002/trae_projects/superpowers/README.md`
- `/Users/dmh2002/trae_projects/superpowers/src/CLAUDE.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/test-driven-development/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/subagent-driven-development/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/writing-plans/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/executing-plans/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/verification-before-completion/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/requesting-code-review/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/receiving-code-review/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/finishing-a-development-branch/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/dispatching-parallel-agents/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/systematic-debugging/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/brainstorming/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/using-git-worktrees/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/writing-skills/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/skills/using-superpowers/SKILL.md`
- `/Users/dmh2002/trae_projects/superpowers/src/skills/test-driven-development/testing-anti-patterns.md`
- `/Users/dmh2002/trae_projects/superpowers/src/docs/testing.md`
- `/Users/dmh2002/trae_projects/superpowers/src/hooks/session-start`

### 9.2 内部参考

- `specs/evals/21-LDVH全盘确认与核心吸收建议.md`
- `specs/evals/16-Gstack深度调研-人工确认-测试流程-使用说明与LDVH对比.md`
