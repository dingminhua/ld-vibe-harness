# LDVH 环境 Hook 接入表述审计

> 审计时间：2026-07-31（Asia/Shanghai）
> 审计对象：当前 Git Working Tree 中的 LDVH 正式规则源、canonical Skill、发行接入面、相关 Code 命名与根级 `docs/`
> 内容来源签名：AI agent（`agent_id: codex`，`host_environment: Codex Desktop`）
> 定位：FileAsset 准入试点的 AI 生成样本；当前只是 `docs/` 下的临时报告，不是规则源、事实对象或环境接入成立证据

---

## 一、审计问题与结论

审计问题：**当前 LDVH 是否已经不再把“环境 Hook、插件或 adapter”表述为 LDVH 的环境接入形态？**

结论分为两层：

1. **对当前正式规则源和 canonical 接入设计，答案是“是”。** 当前规则明确规定薄 Skill 是目标 AI 环境中的默认且唯一接入形态，直接 Helper 调用仍可使用，唯一不经 Skill/Helper 链的自动入口是原生 Git `commit-msg` Git Gate；环境 Hook、插件或 adapter 不属于 LDVH 接入面。
2. **对整个仓库的全部文字和当前外部运行环境，答案不能写成“已经完全没有”。** 根级 `docs/` 仍保存多份历史环境报告，其中明确推荐或记录 Plugin SessionStart Hook；`work-context-core` 仍接受带 `hook_event_name` 的原生环境事件对象；当前会话也由环境侧以 `SessionStart/resume` 形式交付过工作上下文。这些内容不改变正式接入形态，但说明不能把“规则已移除该形态”扩大为“没有 Hook 字样、没有环境侧 Hook，或所有历史说明都已清理”。

因此，当前可以准确表述为：

> 当前 LDVH 正式规则源和发行接入面不定义、不收纳也不维护环境 Hook、插件或 adapter 接入层；目标环境只能通过其自身机制递达 canonical 薄 Skill，或直接调用既有 CLI。原生 Git Hook 只承接 Git Gate，不属于 AI 环境 Hook。

当前不能准确表述为：

> LDVH 仓库和所有运行环境已经没有任何 Hook、插件、adapter 或相关历史说明。

---

## 二、审计范围与方法

### 2.1 已检查范围

- `specs/00-理念与构成.md` 的环境接入上位边界；
- `specs/09-环境接入规范.md` 的职责、唯一接入单元和 Git Gate 边界；
- `specs/attachments/09.Att.01-环境接入面.md` 的当前发行入口与环境侧实现边界；
- canonical `skill/SKILL.md` 与 `README.md`；
- `pyproject.toml`、`code/ldvh/work_context.py`、`code/ldvh/hooks/` 及仓库内环境 manifest/adapter 候选；
- 根级 `docs/` 中包含 SessionStart、SubagentStart、环境 Hook 或插件接入表述的临时材料；
- 本次对 `ldvh-work-context` 的直接调用结果。

### 2.2 未检查范围

- 用户目录、Codex/Claude Code/ZCode/TRAE/WorkBuddy 等目标环境当前真实配置；
- 已安装在 LDVH 仓库之外的插件、Hook、adapter 或其启用状态；
- cold start、subagent start 等目标环境真实事件是否仍会触发；
- Git Gate 的真实 commit allow/block 行为。

这些范围需要目标环境特定的安装与真实事件验证；本报告不把当前会话注入、历史报告或核心直调扩大为外部环境状态结论。

### 2.3 实际执行的方法

1. 通过 Helper `read-specification-content` 精确读取 `environment-integration` 的“职责边界”“唯一接入单元：薄 Skill”，以及 `environment-integration-surface` 的“当前入口”“环境侧实现边界”；结果为 `outcome: ok`。
2. 回读当前 Working Tree 的上位规范、09、09.Att.01、canonical Skill 和 README。
3. 扫描正式来源、Code、发行入口和 `docs/` 中的 `Hook`、`SessionStart`、`SubagentStart`、`plugin`、`adapter` 表述。
4. 排除 `.venv/`、Web dependencies 和 build 副本后，检查仓库是否包含目标 AI 环境的 `hooks.json`、`plugin.json` 或环境 adapter。
5. 使用当前绝对 Helper 路径直接调用一次 `ldvh-work-context`，输入 `SessionStart/startup`；返回 `contract: ldvh-work-context/1`、`outcome: ok`、`facts: not_requested`。该结果只证明核心直调，不证明任何环境 Hook 已接入。

---

## 三、正式规则源审计

### 3.1 上位架构已经排除其它环境接入形态

`specs/00-理念与构成.md` §8.2 当前规定：薄 Skill 是目标 AI 开发环境中的默认且唯一接入形态；除薄 Skill与 Git Gate 外，LDVH 不设其它环境接入形态。

这一定义把 AI 主动路由与原生 Git 事件机械把关分开，不为环境 Hook、插件或 adapter 保留第三种 LDVH 接入层。

### 3.2 09 明确声明“接入面无此层”

`specs/09-环境接入规范.md` 当前至少在以下位置重复形成同一边界：

- 文件状态说明：本文不定义环境 Hook、插件或 adapter 接入形态；
- §3 职责边界：环境 Hook、插件或 adapter 接入形态不属于本文责任，LDVH 接入面无此层；
- §5.1：目标环境没有技能机制时仍可直接调用 Helper，但不得改投环境 Hook、插件或 adapter；
- Stop Conditions：准备为任何环境新建环境 Hook、插件或 adapter 接入层时必须暂停。

这些不是“尚未实现”的状态描述，而是当前正式架构边界。

### 3.3 发行接入面没有登记环境 Hook/插件入口

`specs/attachments/09.Att.01-环境接入面.md` 当前登记的入口是：

- Helper CLI；
- canonical Skill 与图标资产；
- `ldvh-work-context`；
- `ldvh-context-recovery`；
- Git Gate 与 Git Hook manager；
- doctor。

附件末尾进一步明确：LDVH 接入面不存在环境 Hook、插件或 adapter 层，本仓库不收纳、不维护任何具体 AI 环境的环境侧实现；需要新增环境 manifest、启动脚本或薄 adapter 时，应在目标环境自己的仓库建立独立 Code 计划。

### 3.4 canonical Skill 已经环境中性

当前 `skill/SKILL.md`：

- 不出现 `Hook`、`SessionStart`、`SubagentStart`、插件或 adapter 表述；
- 不断言任何环境的自动加载、触发或递达状态；
- 只要求会话开始、恢复或压缩后经当前入口取得规则引导。

因此，旧报告所批评的“Skill 写死某环境没有 SessionStart 自动注入插件”在当前 canonical Skill 中已经不存在。

---

## 四、仍然存在但不构成正式环境 Hook 接入层的内容

### 4.1 `work-context-core` 的事件形状

`09.Att.01` 当前仍规定 `ldvh-work-context` 可以消费原生环境事件实际提供的对象，并要求 `hook_event_name` 为 `SessionStart` 或 `SubagentStart`。Code 也保留该输入合同。

这说明核心可以被环境侧机制调用，但不证明 LDVH 仓库提供或维护了该环境侧机制。当前规则把 manifest、启动脚本或薄 adapter 留在目标环境自己的仓库。

不过，同一入口行使用“adapter 如实传递”字样，而附件后文又说 LDVH 接入面不存在 adapter 层，存在轻微术语风险。较准确的理解是“外部环境侧调用方”，不是 LDVH 内建 adapter；若正式来源下次修改，可考虑改用该表达减少误读。

### 4.2 `code/ldvh/hooks/` 命名

当前 Python 包路径仍包含 `ldvh.hooks.context_recovery` 和 `ldvh.hooks.commit_msg`：

- `commit_msg` 对应 Git Hook/Git Gate，属于当前正式允许的原生 Git 入口；
- `context_recovery` 的实现正文声明为 environment-neutral bounded context recovery，console 入口为 `ldvh-context-recovery`，不是厂商环境 Hook adapter。

包名是历史或实现组织命名，不能反向建立环境 Hook 接入语义；但它是术语残留，单看路径可能造成误解。

### 4.3 图标文件名中的 `plugin`

`icons/` 中仍存在 `ldvh-plugin-icon-*` 文件名。当前 09 与接入面把这些文件作为环境中性的 Skill 图标资产使用，不把名称解释为插件接入层。文件名仍属于可见的历史命名残留。

---

## 五、临时 `docs/` 中仍有相反说法

根级 `docs/` 当前仍包含多份 2026-07-30 环境分析材料。例如：

- `docs/跨环境接入分析汇总报告-2026-07-30.md` 把“插件证据触发”列为维持方向；
- `docs/Codex Desktop 环境 接入LDVH.md` 建议保留 Codex 插件 Hook 自动触发层；
- `docs/LDVH 接入 ZCode 环境分析报告.md` 把 Plugin SessionStart Hook 写为已经接入；
- Claude Code、Codex-Cindy、WorkBuddy 等报告仍讨论未来或现存环境 Hook/adapter。

这些内容与当前正式设计不是同一时间切片。09 已明确规定根级 `docs/` 是临时说明材料，不得成为 doctor、环境接入、能力可用性、Git Gate、发行或实现验证的输入或成立条件。因此：

- 它们不能推翻当前正式规则；
- 但 Human 或 AI 直接搜索仓库时仍可能读到并产生错误当前印象；
- FileAsset 只会稳定保存这些原始历史材料，不会自动把旧结论更新成当前事实；消费对象仍需明确它们的时间、用途和已被当前规则取代的范围。

---

## 六、审计判定

| 判定对象 | 结果 | 可证明范围 |
|---|---|---|
| 当前上位架构是否把环境 Hook/插件/adapter 定义为 LDVH 接入形态 | 否 | 当前 Working Tree 的 00 §8.2 |
| 当前 09 是否允许无 Skill 环境改投环境 Hook/插件/adapter | 否 | 当前 Working Tree 的 09 §3、§5.1 与 Stop Conditions |
| 当前发行接入面是否登记环境 Hook/插件/adapter | 否 | 当前 Working Tree 的 09.Att.01 |
| canonical Skill 是否仍声称某环境有或没有 SessionStart 插件 | 否 | 当前 `skill/SKILL.md` 字节内容 |
| LDVH 仓库是否收纳目标 AI 环境的 hook/plugin manifest | 本次扫描未发现 | 排除依赖、build 副本后的当前仓库文件集合；不证明用户目录或目标环境仓库不存在 |
| `ldvh-work-context` 是否仍接受 Hook 风格事件字段 | 是 | 本次核心直调与当前入口合同；不证明环境真实触发 |
| 根级 `docs/` 是否仍存在环境 Hook/插件接入说法 | 是 | 本次列出的临时报告范围 |
| 当前外部目标环境是否仍安装或触发 LDVH Hook | 未验证 | 本审计未读取目标环境配置，也未执行 cold start |

最终判定：**“当前 LDVH 正式设计已经没有环境 Hook 接入层”成立；“当前仓库、历史材料和外部环境已经完全没有 Hook 接入说法或实现”不成立。**

---

## 七、后续建议

1. 正式规范暂不因本审计自动修改；当前架构结论已经清楚。
2. 将根级 `docs/` 的旧环境报告作为 FileAsset 试点非常合适：它们具有保留原始时间切片的价值，但不应继续作为当前规则或接入状态消费。
3. 在 FileAsset 的消费对象中说明用途，例如“2026-07-30 接入方案历史输入，当前环境 Hook 方向已由 00/09 取代”，而不是改写原始 payload。
4. 若要清理歧义，后续另行评估：`work-context-core` 行中的 `adapter` 用词、`code/ldvh/hooks/context_recovery.py` 包路径，以及 `ldvh-plugin-icon-*` 文件名。这些属于术语/实现整理，不影响本次正式架构判定，也未经本报告授权修改。
