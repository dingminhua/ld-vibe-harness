# V3 正式 specs 吸收索引

> 文件状态：temporary migration index。本文只记录 V2/旧 specs/现有迁移材料进入 V3 正式 `03/05/06/07/08/09` 的吸收判断，不授权正式规则、Code 行为、Hook 安装、提交门禁、Web 行为、Human Gate 或环境支持声明。正式规则仍以 `specs/` 正文为准。

## 1. 索引定位

本文用于把 V2 来源、现有 `_migration/inventory`、第 5 阶段吸收清单和 V3 编号决策转成后续正式 specs 的迁移依据。

本文不复制 V2 正文，不恢复 V2 的六类构成要素，不恢复 Skill 顶层机制，也不把 Hook、Rules、知识地图、Web 状态、测试输出或迁移清单升级为事实源。

吸收顺序遵守：

1. 先确认来源和 V3 归口；
2. 再写正式 specs；
3. 再补 Code 可消费结构和 tests；
4. 最后才考虑 adapter、dispatcher、commit gate、Hook、Web 或行动模板实现。

## 2. 正式 specs 吸收索引

| V3 编号 | 正式规范 | 主要吸收来源 | 应吸收内容 | 不直接吸收内容 | 首批 Code/tests 关注点 |
|---|---|---|---|---|---|
| 03 | 事实源与 Git 追溯规范 | V2 `07-事实源边界与Git追溯规范.md`、`07.Att.01` 至 `07.Att.12`、`31-git-commit-action` 中的提交证据边界 | Git 可追踪文件作为用户事实源；非事实源排除；过程输出、receipt、evidence、diagnostic 的回写边界；Git commit records 的追溯性质；commit message 契约的上位边界 | Git 提交流程步骤、commit hook 实现、Web 提交记录页面、知识地图派生展示、历史提交列表手写维护 | commit 契约可解析性、非事实源边界、completion evidence 回指、提交前 read_plan 消费证据 |
| 05 | 事实模型基础规范 | V2 `02-事实模型基础规范.md`、20-24 事实模型成员、`02.Att.*`、`v2-03-work-object-responsibility-map.yaml`、spec-bloat fact member scan | 事实模型/事实实例边界；事实对象准入；字段契约、状态、证据、关系的共同规则；warning/follow-up/evidence/next_queries 的稳定承接位置；成员模板的上位要求 | Spark/WorkCase/ADR/Pitfall/Study 的完整字段表、完整状态机、旧 TaskPlan/Task/SubTask 兼容、具体实例迁移 | 对象身份、事实实例不得定义规则、成员模板骨架、过程证据分流到对象或 specs |
| 06 | 行动模板基础规范 | V2 `03-行动编排规范.md`、30/31/32/34/35/36 行动成员、`v2-04-orchestration-responsibility-map.yaml`、stage-5 checklist | Context、Scenario、Gate、执行、验证、回写、缺口分流的行动模板基本结构；主控 AI 与能力输出交还边界；Git 提交、Rules 同步、环境适配等作为模板或候选的归口 | V2 30-59 成员全文、Skill 顶层身份、具体 Hook/Rules 安装、完整流程目录、行动模板替代 Human Gate | 模板 read_plan、Gate 分流、能力输出不得成为事实源、行动完成声明需要验证证据 |
| 07 | Code 确定性执行规范 | V2 `04-Code确定性执行规范.md`、`04.Att.*`、V2 `06` 中 dispatcher/adapter/payload 边界、现有 `code/specs_validate.py` 与 `code/ldvh_specs.py` | Code 读取、解析、校验、聚合、诊断、投影、preflight、runtime facade、stdout-only receipt、payload/adapter/dispatcher 的实现边界；Code 不授权、不替代 AI/Human/事实源 | 具体技术栈细节、Hook 安装、用户环境写入、Web API 细节、测试治理本体、未进入正式 specs 的候选规则 | validator 覆盖、诊断等级、unknown event、read_plan evidence、target 分类、environment_integrated=false |
| 08 | Web 信息同步规范 | V2 `05-Web信息同步规范.md`、`05.Att.*`、Web 回归材料 | Web 作为 Human-facing 派生展示；状态、风险、证据、待确认事项、提交记录、诊断和验证状态展示边界；Web 状态不成为事实源；受控轻写入必须回写并验证 | 具体页面设计、API 实现、缓存实现、旧知识地图展示细节、未授权的通用写入、Web 作为项目管理看板优先 | DTO/source_refs、Confirm UI 不替代 Human Gate、Web cache 不替代事实源、轻写入白名单测试 |
| 09 | 测试与验证规范 | V2 `08-测试基础规范.md`、`08.Att.*`、现有 `tests/code` 和 `_migration/tests` | 自动化测试、命令校验、等价验证、Human 验收、回归验证的分层；验证声明字段；测试证据边界；失败阻断；同步触发；测试不得反向定义规则 | 具体测试框架绑定、测试输出长期落盘、fixture 当事实源、用测试通过替代 Human Gate、Web/Hook 未实现时的虚假覆盖 | `python3 -m pytest tests/code`、`specs_validate all`、runtime/preflight/action-guide 负例、review hash gate |

## 3. 只能留在 `_migration` 的内容

以下内容当前只能作为迁移证据或历史材料，不进入正式 specs 正文：

1. V2 全量目录清单、阶段计划、扫描报告和一次性审查结论；
2. V2 的 30-59 成员全文、20-24 成员完整字段表和完整状态机；
3. V2 `06` 的 Rules/Skills/Agents/Hooks 类型体系作为顶层构成要素的表达；
4. Skill 文件本身、Skill 调用事实、环境安装状态、Hook registry 存在性；
5. Web 页面截图、缓存状态、派生知识地图视图和本机环境观察；
6. 测试原始输出、coverage、trace、临时报告和迁移 fixture；
7. 旧编号、旧路径、旧 active 状态和历史兼容判断。

这些内容若有长期价值，必须先按 03/05/06/07/08/09 归口转写为正式规则、Code 输入、tests 或事实对象，不得整段搬入。

## 4. 应转为 Code 或 tests 的内容

以下内容不应写成正式 specs 规则正文的长表，应由 Code 或 tests 承接：

| 内容 | 承接位置 | 原因 |
|---|---|---|
| spec/attachment identity 一致性、canonical_path 和 role_sections 检查 | `code/ldvh_specs.py`、`tests/code` | 机械可验证，手写清单容易过期 |
| read_plan、source_refs、impact_summary 和 next_queries 派生 | Code 输出 | 应从 Markdown identity、章节和引用派生，不形成第二事实源 |
| runtime event 闭集、未知 event、acknowledged paths 和 completion evidence 负例 | Code/tests | 属于确定性执行和验证门禁 |
| commit message 正反例、body 条件、type/scope 解析 | Code/tests | 正式 specs 只定义契约，解析和负例由测试覆盖 |
| Web DTO/API 正反例、缓存边界和受控轻写入回归 | Web/tests | 不应把实现细节写成规则正文 |
| migration gate、bloat scan、Markdown extractor 原型 | `_migration/tests` 或后续正式 Code/tests | 当前只证明迁移方向，不授权正式行为 |

## 5. 编号与术语核对

当前 V3 正式编号采用：

1. `00` 理念与构成；
2. `01` 保障与衔接；
3. `02` AI 行为规范；
4. `03` 事实源与 Git 追溯规范；
5. `04` Specs 基础规范；
6. `05` 事实模型基础规范；
7. `06` 行动模板基础规范；
8. `07` Code 确定性执行规范；
9. `08` Web 信息同步规范；
10. `09` 测试与验证规范。

V3 术语使用：

| V2 术语 | V3 处理 |
|---|---|
| 行动编排 | 改为行动模板；旧行动成员作为模板或候选吸收 |
| 运行时扩展 | 不作为第六构成要素；上位语义由 01 承接，具体实现边界分流到 07/09/06 |
| Skill | 不作为 V3 顶层机制；转为行动模板步骤、Action Guide 提示或外部环境包装候选 |
| 知识地图 | 作为 Code 派生导航能力或 Action Guide 输入，不作为事实源 |
| 最终事实源/单一事实源 | 在 V3 统一表达为用户事实源和 Git 可追踪文件事实源 |

## 6. Stop Conditions

出现以下情况时暂停并回到正式 specs 或 Human Gate：

1. 新增正式 spec 没有明确减少的 AI 负担、事实源边界或验证方式；
2. V2 内容被整段复制，导致 V3 恢复旧目录权威或第二事实源；
3. Runtime、Skill、Hook、Rules 或 Web 状态被写成独立构成要素；
4. Code、tests、review 或子 Agent 输出替代正式规则、Human Gate 或完成声明；
5. 03/05/06/07/08/09 与 00、01、02、04 的上位边界冲突；
6. 新增正式 specs 后没有同步 Code 解析、review 收据和 tests。
