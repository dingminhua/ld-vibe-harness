# LDVH 对 ECC 运行系统机制的暂停自研与学习评估

> 创建日期：2026-06-10
> 定位：LDVH 对 ECC 运行系统工程化机制的内部调研与阶段性行动判断
> 调研边界：不直接构成强制规则
> 执行效力：无；结论需进入正式 specs、ADR、Task、Code、Web 或运行投影后才成为稳定执行依据
> 来源：ECC 本地源码、LDVH 既有 ECC 借鉴评估、LDVH 04/41/42 系列规范与当前对话评估
> 相关参考：`docs/refs/07-LDVH对ECC-Claude-Code插件的借鉴评估.md`、`docs/research/18-LDVH推进评估与候选事项总览.md`

---

## 1. 本文解决的问题

本文记录一次针对 ECC 与 LDVH 的阶段性对照判断：哪些方向 LDVH 不应继续凭空自研，而应立即暂停、先学习 ECC 的成熟机制；哪些方向属于 LDVH 的核心差异化能力，不应因为 ECC 的运行系统成熟度而停掉。

本文只作为内部调研，不替代正式规范、ADR 或 Task。若后续需要执行，应分流到对应事实源或工作对象。

---

## 2. 总判断

LDVH 不应暂停事实源治理、工作模型、工作流程、Human Gate 和规范边界这条主线。

但 LDVH 应立即暂停若干运行系统工程化方向的独立自研，先学习 ECC 的成熟结构。

两者关系可以概括为：

```text
LDVH 继续做治理内核；
ECC 作为运行系统工程样板来学习；
学习机制，不复制内容库；
由 LDVH 的事实源治理体系接管吸收结果。
```

ECC 的优势集中在跨 Harness 分发、选择性安装、统一 CLI、运行审计、状态工具、Skills / Commands / Rules 资产组织。LDVH 的优势集中在 Git 文件事实源、工作对象、规范边界、Human Gate、受控写入和事实回写。

因此，LDVH 当前真正需要停下来的不是治理主线，而是“自己先造一套运行系统”的冲动。

---

## 3. 必须暂停自研、先学习 ECC 的事项

### 3.1 暂停自研安装或落地画像体系

ECC 已经形成 `components / modules / profiles` 三层 manifest 思路，用于描述用户可理解能力包、真实文件模块、目标平台、依赖、成本、稳定性和默认安装策略。

LDVH 当前虽然已经有 04.02 环境适配与运行投影规范、42 LDVH落地与检查流程，但运行投影漂移检查 Code、运行投影索引、现场检查证据和降级记录结构化仍在待补齐状态。

当前建议：

1. 暂停 LDVH 自研安装画像、安装 profile 或类似机制；
2. 先抽象 ECC manifest 的字段、层级和解析方式；
3. 再设计 LDVH manifest schema 草案；
4. LDVH manifest 只描述运行投影、事实源边界、验证命令、Human Gate 和降级方式，不复制 ECC 内容资产。

### 3.2 暂停直接做 apply 或自动落地工具

ECC 的 `install-plan.js` 明确提供不修改目标的计划能力，先输出选择性安装计划，再由 apply 工具执行写入。

LDVH 的 42 已经要求先检查当前事实源和环境，输出缺口；经 Human 授权后逐项落地；完成后复检。这个方向与 ECC 的 plan / apply 分离高度一致。

当前建议：

1. 暂停直接实现 `ldvh landing apply`；
2. 先设计 `ldvh landing plan --json` 输出合同；
3. 输出字段可包括 `scope`、`facts_read`、`gaps`、`proposed_actions`、`writes_required`、`human_gate`、`validation_plan`；
4. apply 必须等 plan 合同、Human Gate、验证命令和回写边界稳定后再做。

### 3.3 暂停继续新增零散 CLI 脚本

ECC 已经把 install、plan、catalog、doctor、repair、status、sessions、work-items、loop-status 等能力统一到 `ecc <command>` 门面。

LDVH 当前已有 `specs_validate.py`、`fact_cli.py`、`fact_validate.py`、`commit_validate.py` 等工具，但入口仍偏分散，AI 需要记住多个脚本和参数。

当前建议：

1. 暂停新增散装脚本入口；
2. 先设计 `ldvh <domain> <action>` 命令树；
3. 把现有 Python 工具包装进稳定命令门面；
4. 为每个命令定义输入参数、输出 JSON 合同、exit code、可回写位置和不得回写边界。

### 3.4 暂停自研状态面板和健康检查口径

ECC 的 status 能聚合 readiness、active sessions、skill-run health、install health、pending governance events 和 work items 等交接快照。

LDVH 42 明确当前环境确认、检查发现、缺口清单和复检结论默认只进入当前报告；报告不是长期状态事实源。需要长期保留的稳定事实必须另行进入对应 Git 文件事实源。

当前建议：

1. 暂停直接做 LDVH 状态面板或健康检查口径；
2. 先学习 ECC 如何区分本地状态快照、exit code、修复建议和权威事实源；
3. 再定义 LDVH status 的边界：哪些只是过程快照，哪些必须回写 Task、Memo、ADR、平台清单、规范或 Code；
4. Web 或 Dashboard 只能消费已定义合同，不应自行发明状态口径。

### 3.5 暂停为各平台拍脑袋创建运行投影

ECC 已经有多平台目录表面与分发经验，覆盖 Claude、Codex、Cursor、Gemini、OpenCode、Zed 等执行环境。

LDVH 04.02 已明确运行投影不是最终事实源，平台入口、项目规则、工作区配置或等价入口只应作为薄引用或环境适配结果，不得替代正式规范。

当前建议：

1. 暂停为单个平台直接创建入口、Hook、Skill、Agent 或项目级 AI 指令；
2. 先整理 ECC 各平台表面；
3. 建立 ECC 平台表面到 LDVH 薄入口、运行投影、降级方式、Human Gate 的映射矩阵；
4. 所有持久运行投影创建都必须现场确认平台、权限、Human 授权和验证方式。

### 3.6 暂停大规模自建 Skills / Commands / Rules 内容库

ECC 的 Rules / Skills / Commands 资产规模很大，并且已经形成 Rules 定标准、Skills 给做法、Commands 做入口兼容和自动化调用的分层。

LDVH 不应被 ECC 的资产数量牵引，直接复制或重建大量内容库。直接复制会增加上下文负担、制造事实源边界冲突、扩大运行投影漂移风险，并可能绕过 Human Gate、Task 状态机和工作对象字段契约。

当前建议：

1. 暂停大规模自建 LDVH Skill / Command / Rule 内容库；
2. 先学习 ECC 的目录分层、注册表、命令到工具合同、规则与技能边界；
3. 第三方 Skill 只作为候选能力来源，进入 LDVH 后必须经过非 LDVH 来源内容治理；
4. LDVH 自建 Skill 应优先服务事实源读取、工作对象流转、Human Gate、验证闭环和回写分流，而不是泛化替代 ECC 的通用开发资产。

---

## 4. 不应暂停的 LDVH 主线

### 4.1 不暂停事实源边界治理

LDVH 的关键价值在于明确区分正式规范、管辖项目配置、AI 统一入口运行投影、平台适配清单、管辖项目文档、工作对象实例、Code 实现、Web 展示和 Git diff 证据。

ECC 的机制可以作为候选输入，但不能反向污染 LDVH 的事实源体系。任何稳定结论必须进入对应权威位置，而不是停留在工具输出、聊天记录、Web 页面状态或运行投影中。

### 4.2 不暂停 Human Gate 与受控写入

LDVH 对配置、入口、平台清单、Code、Web、运行投影、状态关闭、高影响判断等事项已有 Human Gate 要求。

ECC 的自动安装、修复和更新能力只能被 LDVH 以 dry-run、plan、授权、apply、verify 的方式吸收。不能因为 ECC 的自动化成熟，就降低 LDVH 对受控写入和事实回写的要求。

### 4.3 不暂停工作模型和治理语义

ADR、Intent、Memo、Pitfall、Task 等结构化事实对象是 LDVH 的差异化能力。

ECC 的 sessions、work-items、skills、commands 可以作为运行系统参考，但不应替代 LDVH 的工作模型。LDVH 后续可以学习 ECC 的状态聚合和 CLI 组织方式，但工作对象语义、状态流转和关闭证据仍应由 LDVH 自身规范控制。

---

## 5. 建议学习顺序

### 5.1 第一优先级：Manifest

先学习 ECC 如何把能力拆成 component、module、profile，再映射到 LDVH 的运行投影、事实源边界、验证命令、Human Gate 和降级方式。

该阶段只形成 schema 草案和字段说明，不做实际安装器。

### 5.2 第二优先级：Plan / Apply / Verify

先设计只读 `ldvh landing plan --json`，让 42 的检查流程具备机器可消费的计划输出。

apply 和 verify 后置，避免在事实源边界、Human Gate 和回写合同不稳定时引入自动写入风险。

### 5.3 第三优先级：统一 CLI

冻结散装脚本增长，把现有工具收敛到统一命令树和输出合同。CLI 的首要目标不是多功能，而是降低 AI 发现成本、稳定输出结构、明确 exit code 和回写边界。

### 5.4 第四优先级：Status / Doctor / Repair

先定义状态快照与事实源之间的边界，再考虑健康检查、修复建议、Web 状态展示或自动 repair。

LDVH status 不应成为新的事实源，只应作为聚合视图和分流入口。

### 5.5 第五优先级：跨平台投影

先做 ECC 平台表面到 LDVH 环境适配映射的矩阵，不直接创建平台入口或项目级规则。

只有当平台清单、Human Gate、验证方式和降级策略明确后，才考虑生成或维护持久运行投影。

---

## 6. 后续可分流事项

以下事项若继续推进，应进入对应事实源，而不是停留在本文：

| 候选事项 | 建议去向 | 说明 |
|---|---|---|
| LDVH manifest schema 草案 | ADR 或 Task | 决定是否引入 manifest 层，以及字段边界 |
| `ldvh landing plan --json` 合同 | Task、Code、tests | 先做只读计划输出，不做 apply |
| 统一 CLI 命令树 | ADR、Task、Code | 收敛现有工具入口与输出合同 |
| status / doctor / repair 边界 | ADR、Task、Web docs | 先定义快照、诊断、修复建议与事实源回写边界 |
| ECC 平台表面映射矩阵 | docs/refs 或 research | 作为 04.02 和平台适配清单的输入材料 |
| 第三方 Skill 接管策略 | docs/specs/11、11.01 或 Task | 与非 LDVH 来源内容治理合并判断 |

---

## 7. 阶段性结论

LDVH 当前应停下来的，是未经 ECC 学习就独立自研运行系统工程化能力。

LDVH 当前不应停下来的，是用事实源、规范、工作模型、工作流程、Code、Web 和 Human Gate 驾驭 AI 工程闭环的核心路线。

最合理的推进方式是：

```text
先把 ECC 作为运行系统工程样板拆解；
再把可用机制转译为 LDVH 的 manifest、plan、CLI、status 和平台投影候选；
最后由 LDVH 的事实源治理、Human Gate 和验证闭环决定是否吸收。
```
