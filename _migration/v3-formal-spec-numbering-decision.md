# V3 正式 specs 编号决策

> 文件状态：temporary migration decision。本文记录 V3 正式 specs 编号与归口决策，作为重编号迁移和后续 V2 吸收的依据；它不替代 `specs/` 正文规则，也不授权 Code、Hook、环境入口或 Human Gate 行为。

## 1. 决策结论

V3 正式 specs 采用以下目标编号：

| 编号 | 目标规范 | 状态 |
|---|---|---|
| 00 | 理念与构成 | 已存在 |
| 01 | 保障与衔接 | 已存在 |
| 02 | AI行为规范 | 由当前 `03-AI行为规范.md` 重编号 |
| 03 | 事实源与 Git 溯源规范 | 后续吸收 V2 07 |
| 04 | Specs 基础规范 | 由当前 `02-Specs基础规范.md` 重编号 |
| 05 | 事实模型基础规范 | 后续吸收 V2 02 |
| 06 | 行动模板基础规范 | 后续吸收 V2 03，并承接 30/31/32 为模板或候选 |
| 07 | Code 确定性执行规范 | 后续吸收 V2 04，并承接 validator、adapter、dispatcher 实现边界 |
| 08 | Web 信息同步规范 | 后续吸收 V2 05 |
| 09 | 测试与验证规范 | 后续吸收 V2 08 |

## 2. 决策理由

该编号把 V3 规范分成三段：

1. `00-03` 是全局上位层：理念与构成、保障与衔接、AI 行为、事实源与 Git 溯源；
2. `04-08` 连续对应 00 定义的五类构成要素：规范体系、事实模型、行动模板、Code、Web；
3. `09` 是测试与验证治理层，不作为第六类构成要素。

AI 行为规范放在 `02`，是因为 LDVH 以 AI 执行者为第一服务对象，AI 行为约束应先于具体构成要素实践出现。

Specs 基础规范放在 `04`，是因为它归属五类构成要素中的“规范体系”，应和 `05-08` 共同形成构成要素规范段。

事实源与 Git 溯源放在 `03`，是因为事实源边界和 Git 溯源是所有构成要素共同遵守的底层原则，且 commit 契约需要早于行动模板、Code validator、Web 展示和测试治理。

## 3. Runtime 与环境入口归口

V3 不恢复 V2 `06-运行时扩展规范.md` 作为独立主规范。

Runtime Protocol、环境入口、canonical event、trigger source 和不得声称环境已完整生效的上位语义已经由 `01-保障与衔接.md` 承接。V2 06 中可迁移但更具体的内容，应按性质分流：

| V2 内容 | V3 归口 |
|---|---|
| 环境入口、Runtime Protocol、canonical event、trigger source 上位语义 | 01 保障与衔接 |
| payload schema、dispatcher、adapter、validator 输出契约 | 07 Code 确定性执行规范 |
| Hook 映射、环境安装检查、payload_present 烟测 | 07 Code、09 测试与验证，必要时作为环境适配实现材料 |
| Rules 同步审查、Git 提交行动、环境适配流程 | 06 行动模板基础规范下的模板或候选 |
| Skill 工作流能力 | 转换为行动模板步骤、Action Guide 提示或外部环境包装候选，不作为 V3 顶层机制 |

## 4. 执行要求

当前重编号迁移只处理已经存在的正式 specs：

1. `specs/03-AI行为规范.md` -> `specs/02-AI行为规范.md`；
2. `specs/02-Specs基础规范.md` -> `specs/04-Specs基础规范.md`；
3. `specs/attachments/02.Att.*` -> `specs/attachments/04.Att.*`；
4. 同步 identity block、canonical_path、parent_spec、basis、related_specs、正文引用、Code 常量、tests 和迁移计划引用；
5. 不创建空壳 `03/05/06/07/08/09` 正式 specs；这些文件只有在对应 V2 内容完成吸收、归口和测试闭环后，才能进入正式 `specs/`。后续若创建这些文件，必须具备规则本体、保障措施、验证方法、Human Gate、Stop Conditions 和 review 证据。

## 5. 停止条件

出现以下情况时暂停并回到 Human Gate 或正式 specs：

1. 重编号导致 00/01 最高锚点、保障与衔接层或五类构成要素含义被改写；
2. Code、测试或迁移材料仍消费旧 `02-Specs` / `03-AI` 路径并造成双事实源；
3. 新编号被用于创建无内容、无 Code 消费方或无测试闭环的空壳正式 spec；
4. Runtime 或环境入口被从 01 上位语义中拆出并形成第二规则源。
