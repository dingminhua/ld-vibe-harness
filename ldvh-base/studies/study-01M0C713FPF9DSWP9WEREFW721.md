---
title: Hook 对 LDVH 生产过程的实际价值——四视角综合分析
status: active
report_kind: external_research
research_intent: 从 ADR/Pitfall 强制召回、WorkCase 状态机编排、Git Gate 署名可追溯、Skill 路由与上下文注入四个视角，系统评估宿主 Hook 机制对 LDVH（管理软件生产过程的 harness）的实际价值边界，回应"hook 注入上下文可替代 skill"的质疑。
research_question: Hook 机制对 LDVH 的生产过程保障（ADR/Pitfall 召回、WorkCase 状态机、Git Gate 署名、Skill 路由）有哪些实际性的帮助？Hook 与 Skill 的关系是什么？跨七个产品接入时 Hook 的正确定位与边界在哪里？
abstract: 通过四个协同视角综合分析：①ADR/Pitfall 召回——Hook 能把"召回义务的机械半边"（全量 fetch + 库快照时效）变成硬门，但语义半边（边界触达判断、适用性评估、是否真遵从）永远只能 AI 判；②WorkCase 状态机——Stop gate 把"合法退出集"从"模型应遵守的规则"变为"模型不能跨越的构造性边界"，无此护栏的产品只能靠自律，而自律恰在最长的 Controller-owned 链上最脆弱；③Git Gate——寄生在 Git 原生 commit-msg 契约上，与宿主 Harness 解耦，故跨所有产品零适配；④Skill 路由——"hook 注入 skill 内容"是范畴错误，真实 Stop hook 不注入任何上下文，它是"会话能否结束"的机械闸门，与 Skill 语义路由正交互补。结论：Hook = 生产过程层的机械事件闸门，保障"过程不变量"（署名、交还检查点、召回时效），不路由业务、不注入规则、不替代 Skill。
recommendation_summary: Hook 在 LDVH 架构中的正确定位是"生产过程资产的机械事件闸门"：应保障 Git 事件署名确定性检查（Git Gate）和精确绑定 WorkCase 的 Stop 交还闸门（Stop gate），二者都是过程不变量；不应试图替代薄 Skill 的语义路由、不应承载规则正文、不应把"全量注入系统提示"当方案（违反 §8.1 渐进披露）。跨产品接入策略为：Git Gate + Skill 路由（零 hook 适配）为最小接入层，Stop gate 按环境能力渐进增强。增强方向是把同一只读投影逻辑前移到工具调用前（PreToolUse）与会话起点（自动绑定），保持单真相源与跨产品可移植。
object_id: study-01M0C713FPF9DSWP9WEREFW721
object_uid: 01a01870-8df6-7a5b-9e59-3c761cfe1c41
fact_type_key: study
created_at: '2026-08-19T06:00:00+08:00'
updated_at: '2026-08-19T06:00:00+08:00'
urls:
- ref: https://github.com/yhlooo/dsh-bridges
  title: yhlooo/dsh-bridges
  summary: DSH 第三方插件，将 Claude Code/Codex/Pi/Gemini CLI/Cursor 的 Hooks 桥接到 DSH，无需迁移。
- ref: https://github.com/earendil-works/pi
  title: Pi Agent Harness 源码仓库
  summary: Pi 的 TypeScript 扩展系统源码，含完整生命周期事件定义（tool_call/agent_end/session_shutdown 等）。
change_log:
- signature:
    product_name: Cindy
    model_name: kimi-k3
  at: '2026-08-19T06:00:00+08:00'
  summary: 初次创建 Study，综合四视角（ADR/Pitfall 召回、WorkCase 编排、Git Gate 署名、Skill 路由）分析 Hook 对 LDVH 的实际价值
---

## 研究问题

Hook 机制对 LDVH 的生产过程保障（ADR/Pitfall 召回、WorkCase 状态机、Git Gate 署名、Skill 路由）有哪些实际性的帮助？Hook 与 Skill 的关系是什么？跨七个产品（Claude Code、Codex、Pi、Cindy、DSH、Trae、WorkBuddy）接入时 Hook 的正确定位与边界在哪里？

## 输入与边界

- 范围：宿主 Hook 机制对 LDVH 四类生产过程资产的保障价值
- 不覆盖：模型能力评测、UI 体验、非 hook 的扩展机制细节、具体代码实现
- 证据来源：仓库内 specs/00、09、21、22、23、34、36、37 及附件；code/ldvh/git_hooks/commit_msg.py、code/ldvh/commits/validation.py、code/ldvh/hooks/workcase_stop.py、code/ldvh/helper/operations/check_workcase_handoff_operation.py 等源码；协同 Worker 四视角分析报告（2026-08-19）
- 时间：2026-08-19

## 关键发现

### 视角一：ADR/Pitfall 强制召回——Hook 保障"召回义务的机械半边"

**证据**：specs/22 §7.1、specs/23 §7、specs/36 §4-5、specs/37 §4-5、code/ldvh/helper/operations/fact_candidate_operation.py、code/ldvh/facts/candidate_discovery.py

**核心结论**：召回义务分两半——

- **机械半边（可程序化）**：经 Helper 取得全部 `active` ADR 的 F1 卡 + 全部 `active` Pitfall 的 F2 候选卡（两个 op 已存在，分页必须披露 active 数量/已读/未读/cursor/指纹）。这一步不依赖 AI 判断"是否需要"。
- **语义半边（只能 AI 判）**：决策边界触达判断（看 decision_question 与 applicability）、F3 全文展开与适用性评估、命中时输出声明。spec 22 §7.1 明写"对象被召回不表示根因已重现、不表示规避已授权"。

**Hook 能做什么**：
1. SessionStart 对等事件（Claude Code→UserPromptSubmit；Cindy 无压缩事件）触发两条召回 op + 写 `.ldvh-recall-state/<session_id>.json` 时效标记（含 object_set_fingerprint）。把"AI 连 fetch 都没调"变成硬触发。
2. Stop hook 查标记文件存在性 + 比对标记指纹与当前 live 库指纹，拦"未召回/已过期"（落实 specs/36 §8#9 禁止把会话开始本身当作召回已完成）。

**Hook 不能做什么**：语义遵从（边界触达、适用、声明）验不了。Stop hook 只能可靠 block"召回未执行/已过期"，不应 block"没发标记"（会误杀合规会话）。

**设计原则**：新增读-only 标记文件 + 两个 hook（SessionStart 拉卡写标记、Stop 比指纹拦缺失/stale），fail-open 照搬现有 WorkCase 门。

**可靠性差异**：hook 抬的是地板（保证召回被启动、库快照新鲜），不抬天花板（不保证 AI 用对用准）。上下文压缩后重新召回——Claude Code 有 PreCompact/PostCompact 可挂，Cindy 无压缩事件故仍靠 AI 自律，是相对盲区。

### 视角二：WorkCase 状态机——Stop gate 把"应遵守"变为"不能跨越"

**证据**：code/ldvh/hooks/workcase_stop.py、code/ldvh/helper/operations/check_workcase_handoff_operation.py、specs/21 §6/§9.3.1、specs/34 §5.2-5.4、specs/09 §5.7-5.9

**状态机基线**：
- phase 闭集：human_plan_confirming → plan_revising/executing/controller_checking → independent_reviewing/closure_preparing → human_closure_confirming → closed。Gate 1、Gate 2 两道 Human Gate。
- Controller-owned 收敛链是连续链（34 §5.2/5.4）；handoff 判定闭集：handoff_allowed 仅 open/human_closure_confirming(gate2_waiting) → true，其余一律 controller_owned → false。
- 合法退出四态（34 §5.4）：closed / 真实 blocked / unresolved 读取缺口 / gate2_waiting。其余里程碑（item terminal、Reviewer 返回、一次 commit、进入 closure_preparing）**全部不是**合法交还点。

**Stop gate 的确切作用**：消费宿主 Stop 事件，对精确绑定（不猜测）的当前 WorkCase 调 check-workcase-handoff，当 handoff_allowed=false(controller_owned) 时 block 并附 next_required_control_step。它保障的纪律 = 在进程边界上机械实现 §5.4 合法退出集，封堵"确认是否继续/里程碑汇报/节奏确认"等话术交还。

**关键设计属性**（代码实证）：精确绑定（禁猜测唯一 open 候选）、fail-open（无绑定/异常/超时→continue）、防循环（stop_hook_active→放行）、纯只读（不写事实/不推进 phase）。

**无 Stop gate 的失败模式**：纪律退化为提示层自律。具体：提前交还"确认是否继续"、里程碑当出口、节奏确认、会话结束漂移（idle/关页把 mid-chain 外部化）、长链疲劳（恰最需纪律处自律最弱）、善意错投影（自认 gate2_waiting）。结论：保障强度从机械（不可忽略）降为建议（须被记住+自执行）。

**PreToolUse 可行性**：能做调用前 phase/授权校验（例：human_closure_confirming 阻断 Edit/Write 载体、closed 后阻断写入、阻断绕过受控路径的裸 git commit）。但最强强制已在 Helper 写层（非法转换 code 层即拒），PreToolUse 增量是宿主侧对非 Helper 工具与绕过受控路径的前置预筛，必须同样精确绑定+fail-open+防循环。

**对比本质**：Stop gate 把退出集从 discipline-by-consent 变为 discipline-by-construction。

**增强优先级**：B(会话起自动建立绑定) > F(单一真相源，锁进 A 实现，PreToolUse 复用同一 check-workcase-handoff CLI) > A(PreToolUse 合法操作预检) > E(合法出口清理绑) > G(多产品可移植)。C/D 锦上添花。

### 视角三：Git Gate——寄生 Git 原生契约，故跨产品零适配

**证据**：code/ldvh/git_hooks/commit_msg.py、code/ldvh/commits/validation.py、code/ldvh/commits/git_adapter.py、code/ldvh/commits/signature.py、specs/09 §5.5/§5.7/§5.9

**零适配根因**：Git Gate 部署在 Git common-dir 的 commit-msg hook 上（code/ldvh/git_hooks/commit_msg.py 管理 common-dir Hook 边界）。它是 Git 原生机制，不依赖任何宿主 Harness 的 hook 系统。任何产品只要"真的调系统 git 做 commit"，common-dir hook 就会触发——与 Claude Code/Codex/Pi/Cindy/DSH/Trae/WorkBuddy 的宿主实现解耦。

**6 条硬前提**：P1 真调系统 git（非自研库）；P2 无 --no-verify；P3 系统 git 无重定向（core.hooksPath 未指向别处）；P4 显式署名不注入（AI 必须自己写 LDVH-Product-Name/LDVH-Model-Name，不靠 hook 自动补）；P5 真实 worktree（非内存仓库）；P6 Human Gate + governed_single（提交契约只校验 governed_single 目标，validation.py:912）。

**会静默绕过的宿主**：高危——纯 Web 后端提交（不经系统 git）、自研 git 库（JGit/go-git/libgit2 不触发 common-dir hook）；中危——--no-verify、core.hooksPath 重定向、plumbing 流水线（git commit-tree 跳过 hook）；低危——标准 CLI/IDE（默认触发）。

**PreToolUse 的正确角色**：能注入署名但不应注入（违反 P4 显式署名不注入、且会形成第二规则源）。正确角色是"缺失即阻塞"的防御纵深——在 AI 跑 git commit 前检查"是否已含合法署名/关键变更区块"，缺失则 block 让其补；且必须复用同一核心（validation.py 的确定性检查），不重实现。

**三层可靠性模型**：L1 Git 原生（权威 fail-closed 锚点）> L2 宿主 PreToolUse（防御纵深，可 fail-open）> L3 AI 自律（Skill/行动模板，降摩擦）。增强建议：① 部署校验自动化（ldvh check 集成 hook 状态）；② PreToolUse 复用同一 validation 核心；③ 纯 Web 宿主必须显式核验 git 路径；④ 署名不可 hook 注入（保持 P4）；⑤ 多产品统一 common-dir 部署文档。

### 视角四：Skill 路由与上下文注入——"hook 注入 skill"是范畴错误

**证据**：specs/00 §7/§8.1/§8.2/§10/§11、skill/SKILL.md、code/ldvh/hooks/workcase_stop.py

**Owner 质疑精确重述**："通过 hook 把 skill 内容注入上下文，skill 就不需要了；skill 路由无非语义决策何时启动；全量注入上下文与路由信息一样；大量 skill 是业务，ldvh 管理整个生产过程。"

**质疑对的部分**：在"上下文投递"被动层面二者重叠（都是信息进入 AI 上下文的载体）；skill 路由本质是语义决策（Owner 说得对）；若只比较"路由信息"这一小块，hook 注入与 skill 指针文本接近。

**质疑错的部分（关键纠正）**：
1. **把 Stop hook 当"上下文注入器"是类别错误**。真实 Stop hook（workcase_stop.py）不注入任何上下文——它读显式绑定、调 check-workcase-handoff、必要时 block，是"会话能否结束"的机械闸门，fail-open，不写事实/不推 phase/不替代语义判断。
2. **"注入的内容也是路由信息所以一样"——错在忽略分层**。LDVH 显式分路由层（skill，极薄指针）与权威层（Helper CLI/规范源，规则正文不进上下文常驻）。注入路由指针 ≠ 交付规则库。
3. **"对话开始就注入全部规则"是 §8.1 明确反模式**：进入会话 ≠ 灌入全量规则。理由：上下文过载→漂移；静态注入会 stale（规范源会变，skill 指令"每次现取"）；机械注入无法做"当前任务是否需要"的语义判断。

**Hook 与 Skill 正交且互补**：

| 维度 | Hook（Stop/Git Gate） | 薄 Skill |
|---|---|---|
| 触发 | 机械事件（会话 Stop、git commit） | AI 语义选中（任务落入 LDVH 领域） |
| 能做什么 | 闸门 block/continue；Git Gate 确定性检查 | 指针：路由到 CLI、引导取规则 |
| 有语义理解吗 | 无 | 有（判断事项归不归 LDVH） |
| 注入内容吗 | Stop hook 不注入 | 仅指针文本，不承载规则正文 |
| 保护对象 | 生产过程资产（交还不跳过检查点、commit 带署名） | 业务路由（把业务工作导向权威源） |

删除 skill → 丧失路由，AI 可能绕过 CLI 直写；删除 Stop hook → 丧失交还闸门，AI 可在 mid-Controller-owned 直接结束回合。二者都不可删，不能互替。

**对 Hook 设计的启示**：Hook 应保障生产过程资产（署名、交还检查点、召回时效），不介入业务技能（具体怎么写代码是 skill→CLI 语义层）；不替代薄 Skill 语义路由；不承载规则正文（只跑源已定义的确定性检查）；不把全量注入当方案。

## 建议

1. **Hook 在 LDVH 中的正确定位**：生产过程层的机械事件闸门，保障"过程不变量"（Git 署名、WorkCase 交还检查点、ADR/Pitfall 召回时效），不路由业务、不注入规则、不替代 Skill。
2. **跨产品接入两层策略**：Git Gate + Skill 路由（零 hook 适配）为最小接入层覆盖全部产品；Stop gate 按环境能力渐进增强（Claude Code 原生 → Codex 原生 → Pi TS 扩展 → DSH 经 dsh-bridges → Cindy soft-warning → 其余靠 AI 自律）。
3. **Stop gate 增强优先级**：B(会话起自动绑定) > F(单一真相源锁进 PreToolUse) > A(PreToolUse 预检) > E(出口清绑) > G(多产品可移植)。
4. **ADR/Pitfall 召回增强**：新增 `.ldvh-recall-state/<sid>.json` 标记 + SessionStart 拉卡写标记 + Stop 比指纹拦缺失/stale，fail-open。
5. **Git Gate 不可 hook 注入署名**：保持 P4 显式署名不注入；PreToolUse 只做"缺失即阻塞"防御纵深，复用 validation.py 同一核心。
6. **Skill 路由必须保留**：Hook 与 Skill 正交互补，删除任一都会破坏生产过程的不同保障维度。

## 后续分流

- Pi 扩展实现：编写 .pi/extensions/ldvh-stop.ts 桥接 tool_call/agent_end 到 check-workcase-handoff
- dsh-bridges 实际验证：在 DSH 环境安装 dsh-bridges 验证 Stop gate 桥接效果
- recall-state 标记实现：落地 .ldvh-recall-state/ 与 SessionStart/Stop hook 的比对逻辑
- Cindy 压缩事件盲区：确认 Cindy 是否有等价于 PreCompact 的事件，否则召回刷新仍靠 AI 自律
- 纯 Web 宿主 Git Gate：为不经系统 git 的宿主设计显式 git 路径核验方案
- 本综合分析可作为 09.Att 新附件（Hook 价值定位）的输入
