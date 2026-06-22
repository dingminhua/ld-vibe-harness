# LDVH specs-v2 写作区入口

```yaml
v2_draft_area:
  status: "draft_non_authoritative"
  canonical_path: "specs-v2/README.md"
  active_fact_source: "specs/"
  purpose: "说明 specs-v2 写作区的当前范围、读取顺序、执行约定和未处理边界"
  prohibition:
    - "不得把本文或 specs-v2 下任何文件解释为 active 正式规范"
    - "不得把 specs-v2 目录结构解释为 v2 已完成规范目录"
    - "不得从 specs-v2 直接替代 specs/、ldvh-base/、Git commit records 或管辖项目配置"
    - "不得在未经 Human 单篇核对前迁入或宣称迁移完成"
```

## 1. 定位

`specs-v2/` 是 LDVH 规范体系重构的未 active 写作区。当前唯一 active 正式规范事实源仍是 `specs/`。

本文只作为写作区入口，帮助 AI 判断当前哪些 v2 文件已经进入核对范围、哪些内容仍只是未处理材料。正式规则仍以 active `specs/` 为准；v2 写作基线以当前已核对的 00 和 01 为准。

本文不定义正式规范规则。目录、编号、附件、身份块、Human Gate、规范写作执行顺序和知识地图输入等约束，应由 `01-规范体系基础规范.md` 及其授权附件承接。

当前执行顺序以 `PLAN.md` 为准：先完整迁移 v2，再通过 Human Gate 让 v1 退出 active 历史并使 v2 成为正式规范；切换前事实源进入历史记录后，再提取仍有价值的内容转入新的事实源；知识地图运行时能力排在上述事项之后。

## 2. 当前已处理范围

当前 v2 规范目录只登记已经进入核对范围的规范和成员草案：

| 路径 | 定位 | 状态 |
|---|---|---|
| `00-LDVH理念与价值标准.md` | v2 最高理念锚点、AI 第一服务对象、六类构成要素、事实源底层原则和 V1-V10 价值判断 | draft，未 active |
| `01-规范体系基础规范.md` | v2 规范体系、规范身份、必要章节、上位依据、构成要素归属与价值判断、权威归口、引用纪律、附件规则和迁移治理边界 | draft，未 active |
| `02-事实模型基础规范.md` | v2 事实模型、事实实例、字段契约、字段内容格式、字段注册授权、具体事实模型成员规则和事实实例证据边界 | draft，未 active |
| `03-行动编排规范.md` | v2 行动编排通用规则、成员机制、Context、Scenario、Gate、主控调度、过程输出、保障要求接管和 30-59 成员治理 | draft，未 active |
| `04-Code确定性执行规范.md` | v2 Code 需求准入、确定性解析、校验、聚合、诊断、知识地图投影、受控写入前检查和生命周期维护 | draft，未 active |
| `05-Web信息同步规范.md` | v2 Web Human-facing 派生展示、同源读取、受控轻写入白名单、Confirm UI、提交记录展示和 Web 回归线 | draft，未 active |
| `06-运行时扩展规范.md` | v2 运行时扩展、Rules/Skills/Agents/Hooks 承载物、能力保障链路、薄引用、环境适配和适配检查边界 | draft，未 active |
| `07-事实源边界与Git追溯规范.md` | v2 最终事实源、单一事实源、过程输出回写、Git commit records 和 commit message 契约 | draft，未 active |
| `08-测试基础规范.md` | v2 测试治理、验证声明、测试实现归属、证据边界、失败阻断和跨构成要素测试协作 | draft，未 active |
| `20-Spark-火花.md` | v2 Spark 事实模型成员草案，承载尚未计划化但有保留价值信息的准入、状态、字段、分流和事实源边界 | draft，未 active |
| `21-WorkCase-工作项.md` | v2 WorkCase 事实模型成员草案，承载工作项准入、状态、执行编排、证据、关闭和事实源边界 | draft，未 active |
| `22-ADR-决策.md` | v2 ADR 事实模型成员草案，承载决策准入、状态、字段、后果、规范吸收和事实源边界 | draft，未 active |
| `23-Pitfall-踩坑经验.md` | v2 Pitfall 事实模型成员草案，承载踩坑经验准入、状态、字段、标签、经验吸收和事实源边界 | draft，未 active |
| `24-Study-研究报告.md` | v2 Study 事实模型成员草案，承载研究报告准入、状态、frontmatter、正文骨架、来源和事实源边界 | draft，未 active |

当前已处理附件如下。附件文件统一放在 `attachments/`；附件随父规范核对，不作为独立根规范：

| 路径 | 定位 | 状态 |
|---|---|---|
| `attachments/01.Att.01-知识地图关系类型表.md` | 承载 01 授权的知识地图关系类型、方向、来源结构、禁止误用和 Code 消费类别提示 | draft，未 active |
| `attachments/01.Att.02-术语表.md` | 承载 01 授权的术语条目、推荐表达、术语边界和术语辅助核对表 | draft，未 active |
| `attachments/01.Att.03-规范保障要求类型表.md` | 承载 01 授权的保障要求类型闭集、类型说明、声明写法和保障声明辅助核对表 | draft，未 active |
| `attachments/01.Att.04-规范身份字段表.md` | 承载 01 授权的 `v2_spec` 字段表、规范身份状态闭集和 active 身份块能力提示 | draft，未 active |
| `attachments/01.Att.05-附件身份字段表.md` | 承载 01 授权的 `v2_attachment` 字段表和附件身份状态闭集 | draft，未 active |
| `attachments/01.Att.06-身份一致性辅助核对表.md` | 承载 01 授权的规范身份与附件身份一致性辅助核对表 | draft，未 active |
| `attachments/01.Att.07-行动编排接管建议矩阵.md` | 承载 01 授权的行动编排接管建议矩阵和接管建议辅助核对表 | draft，未 active |
| `attachments/01.Att.08-规范表达清单.md` | 承载 01 授权的不推荐表达、替代写法、中文定语规则和表达辅助核对信息 | draft，未 active |
| `attachments/02.Att.01-字段注册表.md` | 承载 02 授权的字段注册表结构、注册列闭集、字段生命周期、废弃/别名/替代关系和消费元数据 | draft，未 active |
| `attachments/02.Att.02-成员身份字段表.md` | 承载 02 授权的成员身份字段表和成员字段闭集辅助说明 | draft，未 active |
| `attachments/02.Att.03-成员主文件骨架模板.md` | 承载 02 授权的成员主文件专属骨架模板 | draft，未 active |
| `attachments/02.Att.04-成员一致性辅助核对表.md` | 承载 02 授权的成员一致性辅助核对表 | draft，未 active |
| `attachments/02.Att.05-成员双读映射矩阵.md` | 承载 02 授权的 active `ldvh_member` 与 v2 `v2_fact_model_member` 双读映射矩阵 | draft，未 active |
| `attachments/02.Att.06-字段矩阵诊断表.md` | 承载 02 授权的字段 x 模型矩阵诊断目标、判断标准和辅助核对表 | draft，未 active |
| `attachments/02.Att.07-清退登记表.md` | 承载 02 授权的清退登记条目，包括已清退对象、旧入口和废弃字段 | draft，未 active |
| `attachments/03.Att.01-成员身份字段表.md` | 承载 03 授权的成员身份字段表和成员字段闭集辅助说明 | draft，未 active |
| `attachments/03.Att.02-成员主文件骨架模板.md` | 承载 03 授权的成员主文件专属骨架模板 | draft，未 active |
| `attachments/03.Att.03-成员一致性辅助核对表.md` | 承载 03 授权的成员一致性辅助核对表 | draft，未 active |
| `attachments/04.Att.01-Code需求记录字段表.md` | 承载 04 授权的 Code 需求记录字段表 | draft，未 active |
| `attachments/04.Att.02-Code命令入口表.md` | 承载 04 授权的 Code 命令入口表 | draft，未 active |
| `attachments/04.Att.03-Code结构化输出Schema表.md` | 承载 04 授权的 Code 通用结构化输出字段 | draft，未 active |
| `attachments/04.Att.04-Code诊断码表.md` | 承载 04 授权的 Code 诊断字段和等级 | draft，未 active |
| `attachments/04.Att.05-知识地图输入范围表.md` | 承载 04 授权的知识地图输入范围 | draft，未 active |
| `attachments/04.Att.06-知识地图投影Schema表.md` | 承载 04 授权的知识地图目标投影 Schema | draft，未 active |
| `attachments/04.Att.07-受控写入前检查矩阵.md` | 承载 04 授权的受控写入 preflight 检查矩阵 | draft，未 active |
| `attachments/04.Att.08-v1-v2-Code消费双读映射矩阵.md` | 承载 04 授权的 v1-v2 Code 消费双读映射 | draft，未 active |
| `attachments/04.Att.09-Code回归入口表.md` | 承载 04 授权的 Code 回归入口表 | draft，未 active |
| `attachments/04.Att.10-Code参考实现文档边界清单.md` | 承载 04 授权的 Code 参考实现文档边界 | draft，未 active |
| `attachments/05.Att.01-DTO与API契约表.md` | 承载 05 授权的 Web DTO 与 API 契约 | draft，未 active |
| `attachments/05.Att.02-页面与API映射矩阵.md` | 承载 05 授权的页面、API 与来源关系 | draft，未 active |
| `attachments/05.Att.03-轻写入白名单表.md` | 承载 05 授权的受控轻写入白名单和禁止接口 | draft，未 active |
| `attachments/05.Att.04-Confirm-UI字段表.md` | 承载 05 授权的 Confirm UI 最小展示和记录字段 | draft，未 active |
| `attachments/05.Att.05-Gate与Validate阶段边界矩阵.md` | 承载 05 授权的 Gate/Validate 阶段边界 | draft，未 active |
| `attachments/05.Att.06-Human-facing态势语义表.md` | 承载 05 授权的 Human-facing 派生态势原因语义 | draft，未 active |
| `attachments/05.Att.07-提交记录展示矩阵.md` | 承载 05 授权的 Changelog 和对象详情提交展示 | draft，未 active |
| `attachments/05.Att.08-缓存与同步状态矩阵.md` | 承载 05 授权的缓存、同步、降级和冲突展示状态 | draft，未 active |
| `attachments/05.Att.09-Web回归矩阵.md` | 承载 05 授权的 Web API、页面、Confirm UI 和轻写入回归优先级 | draft，未 active |
| `attachments/05.Att.10-Web差距审计模板.md` | 承载 05 授权的 Web AI 只读差距审计模板 | draft，未 active |
| `attachments/05.Att.11-Web能力删除核对表.md` | 承载 05 授权的 Web 页面、API 或能力删除前核对项 | draft，未 active |
| `attachments/06.Att.01-运行时扩展自描述字段表.md` | 承载 06 授权的运行时扩展自描述字段表 | draft，未 active |
| `attachments/06.Att.02-固定运行时扩展登记表.md` | 承载 06 授权的当前固定运行时扩展基线登记 | draft，未 active |
| `attachments/06.Att.03-承载物类型边界矩阵.md` | 承载 06 授权的 Rules、Skills、Agents、Hooks 类型边界 | draft，未 active |
| `attachments/06.Att.04-承载物最佳实践核对表.md` | 承载 06 授权的运行时扩展承载物最佳实践核对表 | draft，未 active |
| `attachments/06.Att.05-保障要求承载矩阵.md` | 承载 06 授权的保障要求到承载方向的默认矩阵 | draft，未 active |
| `attachments/06.Att.06-能力缺口分流核对表.md` | 承载 06 授权的能力缺口分流核对表 | draft，未 active |
| `attachments/06.Att.07-环境适配字段表.md` | 承载 06 授权的环境适配字段表 | draft，未 active |
| `attachments/06.Att.08-适配状态表.md` | 承载 06 授权的适配状态闭集 | draft，未 active |
| `attachments/06.Att.09-薄引用模板.md` | 承载 06 授权的薄引用模板 | draft，未 active |
| `attachments/06.Att.10-部署检查核对表.md` | 承载 06 授权的部署检查核对表 | draft，未 active |
| `attachments/06.Att.11-Codex环境入口候选矩阵.md` | 承载 06 授权的 Codex 环境入口候选矩阵 | draft，未 active |
| `attachments/06.Att.12-CodexHook事件候选矩阵.md` | 承载 06 授权的 Codex Hook 事件候选矩阵 | draft，未 active |
| `attachments/06.Att.13-非Codex自助适配核对表.md` | 承载 06 授权的非 Codex 自助适配核对表 | draft，未 active |
| `attachments/06.Att.14-权威资产副本分层核对表.md` | 承载 06 授权的权威资产与部署副本分层核对表 | draft，未 active |
| `attachments/07.Att.01-事实归属矩阵.md` | 承载 07 授权的典型事实类型与权威位置矩阵 | draft，未 active |
| `attachments/07.Att.02-Commit-Type枚举表.md` | 承载 07 授权的 commit type 严格闭集 | draft，未 active |
| `attachments/07.Att.03-Commit-Scope推荐表.md` | 承载 07 授权的 commit scope 推荐值 | draft，未 active |
| `attachments/07.Att.04-Commit-Body必填条件表.md` | 承载 07 授权的 commit body 必填条件和正文质量标准 | draft，未 active |
| `attachments/07.Att.05-Commit-Message样例集.md` | 承载 07 授权的 commit message 写法样例 | draft，未 active |
| `attachments/07.Att.06-过程输出回写核对表.md` | 承载 07 授权的过程输出回写辅助核对表 | draft，未 active |
| `attachments/07.Att.07-Git提交留痕范围表.md` | 承载 07 授权的 Git 提交留痕适用范围 | draft，未 active |
| `attachments/07.Att.08-Commit-Message字段表.md` | 承载 07 授权的 commit message 字段契约 | draft，未 active |
| `attachments/07.Att.09-关联提交派生优先级表.md` | 承载 07 授权的关联提交派生优先级 | draft，未 active |
| `attachments/07.Att.10-事实源读取策略核对表.md` | 承载 07 授权的事实源查询、定位和读取粒度核对表 | draft，未 active |
| `attachments/07.Att.11-非事实源排除清单.md` | 承载 07 授权的非事实源排除清单 | draft，未 active |
| `attachments/07.Att.12-事实承载介质选择表.md` | 承载 07 授权的事实承载介质选择表 | draft，未 active |
| `attachments/08.Att.01-测试归属矩阵.md` | 承载 08 授权的测试要求、实现细则和测试实现归属矩阵 | draft，未 active |
| `attachments/08.Att.02-验证声明字段表.md` | 承载 08 授权的验证声明字段和完整验证声明条件 | draft，未 active |
| `attachments/08.Att.03-测试证据边界清单.md` | 承载 08 授权的测试证据、诊断线索和事实源排除边界 | draft，未 active |
| `attachments/08.Att.04-同步触发矩阵.md` | 承载 08 授权的变化类型到测试同步检查方向映射 | draft，未 active |
| `attachments/08.Att.05-Code完整验证入口表.md` | 承载 08 授权的 LDVH Code 当前完整验证入口和降级说明 | draft，未 active |
| `attachments/08.Att.06-Web回归入口表.md` | 承载 08 授权的 LDVH Web 当前回归入口和优先级 | draft，未 active |
| `attachments/08.Att.07-失败阻断核对表.md` | 承载 08 授权的不得关闭、不得验收或不得声称完成的阻断条件 | draft，未 active |
| `attachments/08.Att.08-等价验证适用表.md` | 承载 08 授权的等价验证适用条件、最低说明和禁止写法 | draft，未 active |
| `attachments/21.Att.01-orchestration字段契约表.md` | 承载 21 授权的 WorkCase orchestration 长字段表、枚举和条件 | draft，未 active |

20-29 与 30-59 是成员编号段，成员主文件放在 `specs-v2/` 根目录；不得创建同名编号子目录作为成员写作区。

除上表外，`specs-v2/` 中其它文件、目录、编号草案或占位内容，都不得被解释为已经处理、已经确认、已经迁移或已经进入 v2 规范目录。后续每完成一篇规范、附件或成员草案的单篇核对，再把它加入本文当前已处理范围。

## 3. 写作前执行约定

AI 在继续写任何 v2 规范前，必须执行以下约定：

1. 先读取当前 active 入口和本文，再读取 v2 00、v2 01 及相关附件；
2. 不把尚未单篇核对的未来编号、文件名、目录草案或占位文件写成既成事实；
3. 迁移旧 v1 子文档时，先判断主体规则是否应回并主规范，长表、注册表、矩阵、模板、示例或清单是否应拆为附件；
4. 写入前先回到 active v1 原文，确认真实职责、事实源边界、引用关系、保障要求和 Code 消费入口；
5. 写入前判断目标规范的上位依据、构成要素归属、正向价值判断和逆向价值判断；
6. 发现会改变 00 最高锚点、01 治理规则、编号、附件授权、身份块、状态闭集、上位依据、构成要素归属、价值判断或 Human Gate 的事项时，先暂停并等待 Human 确认；
7. 修改完成后，检查是否同步影响当前目录、上位依据、构成要素归属、价值判断、附件授权、待补齐事项、知识地图输入和后续 Code 检查缺口。
8. 不得因为 Code 已具备 v2 只读检查能力，就提前推进知识地图运行时能力、管辖项目图谱、Git history 图谱或 Web 图谱展示。

## 4. 写入位置分工

以下内容应写入或补强到 `01-规范体系基础规范.md`，而不是只停留在 README：

1. 当前 v2 目录登记规则；
2. 编号、附件命名和已处理范围登记规则；
3. 旧 v1 子文档迁移为主规范正文、附件、独立根规范或暂不迁移的判断规则；
4. 正式规范必要章节，尤其是 `上位依据` 和 `构成要素归属与价值判断`；
5. `v2_spec`、`v2_attachment`、身份字段和状态闭集；
6. 规范保障要求的字段、类型、消费边界和行动编排接管边界；
7. Human Gate 中“必须暂停并等待 Human 确认”和“应评估 Human Gate”的区分；
8. 规范写作与修改执行顺序；
9. 知识地图只作为派生机制的输入、关系和回指边界。

以下内容不应提前写入为已成立规则：

1. 后续未处理规范的最终编号和文件名；
2. 尚未单篇核对的事实模型、行动编排、Code、Web、运行时扩展或事实源细则；
3. 尚未读取 active 原文确认的旧规则迁移结论；
4. 仅来自讨论、计划、工具输出或草案目录的规范结论。
