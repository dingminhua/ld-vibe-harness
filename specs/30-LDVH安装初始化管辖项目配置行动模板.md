# LDVH安装初始化管辖项目配置行动模板

```yaml
ldvh_spec:
  spec_id: "30"
  spec_kind: "action_template_spec"
  title: "LDVH安装初始化管辖项目配置行动模板"
  status: "active"
  authority: "active"
  canonical_path: "specs/30-LDVH安装初始化管辖项目配置行动模板.md"
  parent_spec: "specs/06-行动模板基础规范.md"
  relation: "action_template_member"
  positioning: "定义 LDVH 安装、初始化、管辖项目配置、环境插件方案检查和用户告知清单的首个正式行动模板"
  scope: "安装 LDVH、接入 LDVH、初始化 LDVH、选择管辖项目配置位置、登记管辖项目、检查旧插件旧路径、交还验证与回滚信息"
  basis:
    - "specs/00-理念与构成.md"
    - "specs/01-保障与衔接.md"
    - "specs/02-AI行为规范.md"
    - "specs/03-事实源与Git溯源规范.md"
    - "specs/04-Specs基础规范.md"
    - "specs/06-行动模板基础规范.md"
  related_specs:
    - "specs/07-Code确定性执行规范.md"
    - "specs/09-测试与验证规范.md"
    - "specs/10-管辖项目配置规范.md"
  migration_sources:
    - "v2:specs/33-ldvh-install-action-LDVH安装行动编排.md"
    - "v2:specs/32-environment-entry-adaptation-环境入口落地与适配检查.md"
  code_consumption:
    - "ldvh_spec_metadata"
    - "ldvh_install_initialization_action_template"
    - "install_wizard_state_machine"
    - "install_user_disclosure_checklist"
    - "environment_plugin_install_boundary"
    - "governed_project_config_location_gate"
    - "install_verification_handoff"
    - "stop_conditions"
  role_sections:
    value_judgment: "1. 价值判断"
    authority_basis: "2. 权威依据"
    jurisdiction_boundary: "3. 归口边界"
    scope: "4. 适用范围"
    rule_body:
      - "5. 模板定位与来源"
      - "6. 用户告知清单"
      - "7. 安装向导状态机"
      - "8. Context、Scenario、Gate 与交还"
    assurance_measures: "9. 保障措施"
    verification_method: "10. 验证方法"
    human_gate: "11. Human Gate"
    stop_conditions: "12. Stop Conditions"
    next_queries: "13. 待补齐事项"
```

> 文件状态：active；本文是 V3 第一个独立正式行动模板，吸收 V2 `33-ldvh-install-action` 的安装、初始化、首次管辖项目配置和验收交还闭环。本文不安装环境插件，不直接写入用户环境 Hook 系统文件，不声明任何环境入口 integrated，不恢复 Rules / Skill 顶层机制。

## 1. 价值判断

本文存在的价值，是把 LDVH 安装、初始化和管辖项目配置这类高影响行动沉淀成可复用模板，让 AI 在执行前能稳定说明写入位置、影响范围、验证方式和回滚路径，减少遗漏告知、误装入口、误判 integrated 或绕过 Human Gate 的风险。

该模板主要服务 V1、V2、V3、V4、V5、V6、V7 和 V8：它让 AI 快速定位安装与配置入口，理解写入对象和环境边界，正确判断受管项目、环境入口和 integrated 状态，按固定 Gate 稳定执行，在高影响写入、配置位置选择或风险接受前等待 Human 确认，执行指定验证，按格式回写配置和残留风险，并用范式交互向 Human 呈现待确认事项。安装和初始化会改变环境入口、配置位置或受管项目边界；如果没有模板，AI 容易把“方案存在”“样例包存在”“旧插件存在”误写成“已部署”或“已接管”，也容易把系统检查结果当成用户决策、把后置缺口放进主选项，或在最终确认前边问边写。

## 2. 权威依据

本文承接 `specs/06-行动模板基础规范.md` 的 Context、Scenario、Gate、执行、验证、回写和交还结构。

本文承接 `specs/01-保障与衔接.md` 的环境入口、Hook 分类、插件 / 扩展包安装口径和 integrated 声明边界；承接 `specs/10-管辖项目配置规范.md` 的配置事实源和 target-first 解析边界；承接 `specs/07-Code确定性执行规范.md` 和 `specs/09-测试与验证规范.md` 的实现域与验证边界。

本文受 V3 01 的环境入口边界约束，也受 V3 01、06、10 的共同约束：01 管环境入口、06 管行动模板结构、10 管管辖项目配置契约。本文不声明 integrated；只有真实自动触发、失败可阻断、安装状态可复现、回滚方式明确且验证证据齐备时，才可由对应环境入口规则判断是否 integrated。

若本文与 01、06、10 或 Human Gate 冲突，应回到上位规范和 Human Gate，不得由本模板自行覆盖。

## 3. 归口边界

本文归口定义 LDVH 安装、初始化和管辖项目配置行动的步骤组织、用户告知清单、Gate、验证和交还。

本文不归口定义环境入口状态闭集、Hook 安装实现、插件 manifest schema、管辖项目配置字段、Code 命令细节、Web 页面、测试框架或真实用户环境配置。环境入口边界归 01，Code 实现实践归 07 和 `code/docs/`，管辖项目配置契约归 10，验证声明归 09。

本文可以组织“先告知、再确认、再执行、再验证、再交还”的行动顺序，但不得把行动步骤写成环境入口安装授权、配置事实源契约、Code 实现细节或 integrated 状态证明。

## 4. 适用范围

本文适用于：

1. 用户要求安装 LDVH、接入 LDVH 或初始化 LDVH；
2. 用户要求配置、生成或迁移 `LDVH-GOVERNED-PROJECTS.yaml`；
3. 用户要求把项目登记为管辖项目，或检查某项目是否已被 LDVH 管辖；
4. 用户要求检查安装是否生效、修复旧插件、旧路径或 stale V2 path；
5. 后续真实安装、升级、禁用、卸载环境插件或 Git hook shim 前的 Human Gate 准备。

用户只是询问概念、职责或边界时，只回答 01、06、10 和本文边界，不写入配置、不安装插件、不修改 Hook。

## 5. 模板定位与来源

本文是 06 之后的第一个独立正式行动模板，编号为 `30`。它不是 06 父规范的正文示范，也不是 Code 实现域文档；它是可被 AI 直接引用的行动模板成员。

本文吸收 V2 `33-ldvh-install-action` 的安装、初始化、首次管辖项目配置和验收交还能力。V2 `32-environment-entry-adaptation` 的动态投影、部署检查和插件边界只能作为后续增强输入，不能让本文复制 32 全文、恢复 Rules/Skill 顶层机制或越过 Human Gate。

当前只迁入最小闭环：安装入口发现、安装方式判断、初始化检查、目标工作区确认、管辖项目登记、用户告知清单、验证、回写和交还。真实环境插件安装、完整部署自动化、用户级配置解析、项目内配置迁移和批量项目接入仍需单独 Human Gate。

## 6. 用户告知清单

安装、部署、初始化、配置或卸载前，本模板必须先形成用户告知清单，并把清单交给 Human 确认。

告知清单至少包括：

1. 要安装、生成、修改、覆盖、禁用、卸载或删除的对象；
2. 写入位置及其级别：用户级、工作区级、项目级、Git 本地目录、插件 cache、仓库内样例或只读检查；
3. 受影响项目、不受影响项目、跨项目范围和混合非管辖 target 风险；
4. 会接入哪些 Git hook shim、环境 Hook、plugin lifecycle event、manual entrypoint 或 repo instruction；
5. 是否需要创建或检查管辖项目根下的 `ldvh-base/` 事实源目录，以及每个子目录的用途；
6. 哪些事件可能阻断，哪些只是 diagnostic，哪些仍是 manual-ready 或 deferred；
7. 旧插件、旧路径、旧配置、stale V2 path、历史 trust 或旧 Hook 的处理方式；
8. 验证命令、预期结果、不可验证范围和失败处理；
9. 回滚或卸载入口，以及卸载后如何确认环境不再自动触发 LDVH；
10. 当前仍未 integrated 的能力；
11. 残留风险、source_refs 和下一步 Human Gate。

管辖项目事实源目录告知必须说明：

| 目录 | 用途 | 创建边界 |
|---|---|---|
| `ldvh-base/workcases/` | 存放 WorkCase 工作项实例，用来追踪目标、推进状态、验证证据和关闭证据。 | 只创建目录不创建工作项，不替代行动模板或 Human Gate。 |
| `ldvh-base/adrs/` | 存放 ADR 决策实例，用来记录已确认决策、取舍依据和影响。 | 只创建目录不表示已有决策，不替代 specs 正文。 |
| `ldvh-base/pitfalls/` | 存放 Pitfall 踩坑经验实例，用来沉淀已验证的问题、根因、解决方式和规避策略。 | 只创建目录不替代未解决问题或测试失败记录。 |
| `ldvh-base/sparks/` | 存放 Spark 火花实例，用来记录待分流想法、候选发现和问题线索。 | 只创建目录不替代 WorkCase、ADR、Study 或聊天上下文。 |
| `ldvh-base/studies/` | 存放 Study 稳定研究报告实例，用来沉淀被提升后的研究结论。 | 只创建目录不替代临时调研材料、外部资料原文或未经吸收的研究过程。 |

临时调研材料、外部资料或第三方参考不是本模板要求创建的固定目录；只有被提升为稳定事实的研究报告进入 `ldvh-base/studies/`。

缺少用户告知清单时，不得安装、部署、初始化、写入配置、声明接入或要求 Human 验收。告知清单不是授权本身；授权只能来自 Human Gate。

## 7. 安装向导状态机

安装、接入、初始化或配置管辖项目时，AI 必须使用安装向导状态机组织 Human-facing 交互。安装向导不是测试模式；它是正常安装流程。是否执行只由最终确认决定。

安装向导固定为五步：

| 步骤 | 名称 | 作用 | 写入边界 |
|---|---|---|---|
| 1/5 | 流程概览 | 展示完整流程，确认 LDVH 本体路径和目标工作区路径 | 不写入 |
| 2/5 | 安装前检查 | 只读检查当前项目、目标工作区配置、事实源目录、环境入口、旧插件和旧路径状态 | 不写入 |
| 3/5 | 安装选项 | 只收集真正需要 Human 决定的安装选项；配置位置不作为选项 | 不写入 |
| 4/5 | 安装方案预览 | 汇总检查结果、Human 选择、将执行动作、后置项、验证方式和回滚方式 | 不写入 |
| 5/5 | 最终确认 | Human 选择执行、不执行或返回修改；只有选择执行后才可写入 | 确认执行后才可写入 |

每次向 Human 展示安装向导时，应使用流程状态表表达当前位置和已完成决策。状态表至少包含空标记列、步骤、名称、决策 / 结果四列。当前步骤使用箭头标记，已完成事项在“决策 / 结果”列写入简短结果，尚未发生的步骤保持空白，不写“待进行 / 待选择 / 待确认”等噪音状态。

示例形态：

|  | 步骤 | 名称 | 决策 / 结果 |
|---|---|---|---|
| ➜ | 1/5 | 流程概览 |  |
|  | 2/5 | 安装前检查 |  |
|  | 3/5 | 安装选项 |  |
|  | 4/5 | 安装方案预览 |  |
|  | 5/5 | 最终确认 |  |

安装前检查只能输出系统已检查事实，不得把事实伪装成 Human 选项。目录已存在、配置已存在、项目内配置不受支持、当前实现不支持用户级配置目录、旧插件未授权处理、外部 Hook 未授权处理等，都应写入检查结果或后置项；不得继续询问 Human 是否创建已存在目录，或把项目内配置、用户级配置目录放进主选项。

安装入口发现必须先从 LDVH 本体读取本文。目标工作区没有 LDVH 文件时，AI 可以执行有限、只读、有证据的 bootstrap discovery：依次检查当前对话或进程已知 LDVH root、`LDVH_ROOT` / `LDVH_HOME` 环境变量、已安装插件 / Hook / wrapper 中记录的 LDVH root、当前 cwd 向上的 `specs/30-LDVH安装初始化管辖项目配置行动模板.md` 与 `code/specs_validate.py` 组合、常见工作区父目录的有限深度搜索；找到候选后必须展示候选路径和证据，多个候选必须让 Human 选择，找不到时必须要求 Human 提供 LDVH 本体路径，不得要求目标工作区已经存在 `specs/30`。

安装选项只包含当前可执行且需要 Human 取舍的决策。`LDVH-GOVERNED-PROJECTS.yaml` 的配置位置不是选项，只能是目标工作区根目录；项目根目录、用户级目录和 LDVH 本体目录都不是支持位置。AI 必须用表格展示 LDVH 本体路径、目标工作区根目录、配置文件完整路径、含义、限制和建议。项目内已存在 `LDVH-GOVERNED-PROJECTS.yaml` 时，只能记录为 legacy / conflict，并要求 Human 先删除、迁移或明确保留其中一个；不得把它作为主选项。

安装方案预览必须合并所有 Human Gate：写入对象、写入位置、将执行动作、不会执行的事项、后置项、验证命令、失败处理和回滚方式都必须在此步展示。若目标工作区根目录到目标项目路径链上已经存在项目内 `LDVH-GOVERNED-PROJECTS.yaml`，安装方案预览必须报告配置层级冲突，并要求先删除、迁移或明确保留其中一个配置文件；不得继续进入执行。最终确认前，AI 只能只读检查、展示结果和收集选择，不得写入配置、创建目录、安装插件、修改 Hook、修改用户环境或声明 integrated。

最终确认必须给出至少三类选择：执行、不执行、返回修改。Human 选择不执行时，AI 必须停止在方案预览或最终确认状态，不得写入；Human 选择返回修改时，AI 必须回到安装选项；只有 Human 选择执行后，AI 才能按方案执行已确认的仓库内动作。

## 8. Context、Scenario、Gate 与交还

| 结构 | 最小要求 |
|---|---|
| Context | 读取用户目标、目标环境、LDVH 本体路径、目标工作区根目录、管辖项目候选、目标工作区根目录下的 `LDVH-GOVERNED-PROJECTS.yaml`、管辖项目根下 `ldvh-base/` 和 `workcases/adrs/pitfalls/sparks/studies` 事实源目录状态、环境入口审计结果、source_refs，并回指 `specs/01-保障与衔接.md`、`specs/06-行动模板基础规范.md`、`specs/10-管辖项目配置规范.md`、`specs/07-Code确定性执行规范.md`、`specs/09-测试与验证规范.md` 和 `code/docs/01-Git-Commit-and-Hook-Practice.md`。 |
| Scenario | 用户要求安装 LDVH、接入 LDVH、初始化 LDVH、配置管辖项目、把项目登记为管辖项目、检查安装是否生效或修复旧插件 / 旧路径时适用；用户只是询问概念或规则时，只回答 01/06/10 边界，不写入配置、不安装插件、不修改 Hook。 |
| Gate | 写入、覆盖、删除或迁移环境入口，安装、升级、禁用或卸载 LDVH 插件 / 扩展包，创建或修改目标工作区根目录下的 `LDVH-GOVERNED-PROJECTS.yaml`，创建、删除、迁移或重命名管辖项目 `ldvh-base/` 及事实源子目录，确认 LDVH 本体路径和目标工作区根目录，处理配置层级冲突，声明环境入口 integrated，目标环境 Hook 能力不明，多项目或混合非管辖 target，缺少用户告知清单，或缺少安装方案预览和最终确认，均必须暂停或进入 Human Gate。 |
| 执行 | 先用有限、只读、有证据的 bootstrap discovery 找到 LDVH 本体并从本体读取本文；bootstrap discovery 必须检查 `LDVH_ROOT` / `LDVH_HOME`、插件 / Hook / wrapper 候选并展示候选路径和证据；再按 01 判断目标环境入口类型和接入状态；支持 Hook 的环境只生成或检查对应 LDVH 插件 / 扩展包 / package 方案，不直接写入环境 Hook 系统文件；执行安装、部署、初始化、配置或卸载前必须先交付用户告知清单和安装方案预览，明示写入对象、写入位置级别、影响范围、Hook / lifecycle event、阻断与 diagnostic 边界、旧插件 / stale V2 path 处理、验证方式、回滚或卸载入口、未 integrated 能力、管辖项目 `ldvh-base/` 及 `workcases/adrs/pitfalls/sparks/studies` 目录用途、残留风险和下一步 Human Gate；不支持 Hook 或 Hook 未接入时只作为 repo instruction、manual entrypoint 或外部 adapter 候选处理，不恢复 Rules 顶层机制；配置生成位置固定为目标工作区根目录；必须展示 LDVH 本体路径、目标工作区根目录和配置文件完整路径；项目根目录、用户级目录和 LDVH 本体目录不得作为主选项；必须用 10 的配置层级检查确认目标工作区根目录到目标项目路径链上只有一个 active `LDVH-GOVERNED-PROJECTS.yaml`；目标项目内已存在配置时，必须阻断并提示先删除、迁移或明确保留其中一个；随后按 10 登记单一管辖项目、补充 Git common-dir 身份线索，检查或建议创建管辖项目事实源目录，并用 target-first resolver 验证。 |
| 验证 | 使用 `environment_status.py`、`environment_entry_audit.py`、`specs_validate.py governed-projects`、target-first resolution、管辖项目 `ldvh-base/` 目录回读、必要的 runtime adapter 手动入口和 09 验证声明字段记录验证目标、验证入口、输入范围、关键输出、结论、残留风险和证据回指；只有真实自动触发、失败可阻断、安装状态可复现时，才可声明对应环境入口 integrated。 |
| 回写 | 安装和初始化检查输出默认是过程输出；配置写入必须落在 Human 确认的 `LDVH-GOVERNED-PROJECTS.yaml` 并受 10 字段契约约束；事实源目录创建只建立 `ldvh-base/` 入口和五类对象目录，不创建事实实例、不替代字段 schema；旧插件、旧路径、用户级配置目录候选、环境适配缺口或长期风险按 03/05/09 分流到 Spark、ADR、Pitfall、WorkCase、实现域文档或 Git commit records，不得把 runtime receipt、环境观察或聊天结论写成事实源。 |
| 交还 | 交还安装方式、配置位置选择、管辖项目 ID、目标路径、Git common-dir 线索、`ldvh-base/` 及五个事实源子目录状态、环境入口状态、integrated / manual_ready / deferred / removed_top_level 结论、用户告知清单及 Human 确认状态、验证摘要、回滚或卸载入口、残留风险、下一步 Human Gate、source_refs 和未完成分流；阻断时交还阻断原因、缺少证据、缺少告知项和建议的下一步。 |

## 9. 保障措施

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 安装向导状态机要求 | 安装交互必须使用五步状态机，流程表只记录当前箭头和已完成决策 / 结果，最终确认前不得写入 | 本文、06、09 | 安装治理 | 安装、接入、初始化或配置管辖项目时 |
| 告知清单要求 | 安装、部署、初始化、配置或卸载前必须形成用户告知清单并交给 Human 确认 | 本文、01、06、09 | 安装治理 | 涉及写入、入口、配置或卸载时 |
| 环境入口边界要求 | 插件、扩展包、Hook 或 manual entrypoint 只能作为入口承载，不得声明未验证 integrated | 本文、01、Code audit | 环境治理 | 检查或改变环境入口时 |
| 工作区配置 Gate 要求 | 生成或修改管辖项目配置前必须确认 LDVH 本体路径、目标工作区根目录和配置文件完整路径；配置位置固定为目标工作区根目录 | 本文、10、Human Gate | 配置治理 | 创建或迁移 `LDVH-GOVERNED-PROJECTS.yaml` 时 |
| 事实源目录告知要求 | 首次启用管辖项目时必须说明 `ldvh-base/` 及五个子目录用途 | 本文、10、20-24 | 事实源治理 | 创建或检查管辖项目事实源目录时 |
| 验证交还要求 | 完成声明前必须交还验证摘要、回滚或卸载入口和残留风险 | 本文、09 | 验证治理 | 声称安装、初始化或配置完成时 |

## 10. 验证方法

验证本文规则时应检查：

| 检查类别 | 检查内容 | 不满足时 |
|---|---|---|
| 向导检查 | 是否使用五步安装向导、当前步骤箭头、决策 / 结果列、安装方案预览和最终确认；是否把检查事实、用户决策和后置项分开 | 不得执行写入或要求 Human 验收 |
| 清单检查 | 是否在安装、部署、初始化、配置或卸载前列出用户告知清单 | 不得执行写入或要求 Human 验收 |
| Gate 检查 | 是否识别配置位置、环境入口、插件安装、integrated 声明和多项目 target 的 Human Gate | 暂停并交还 Human |
| 环境检查 | 是否使用环境状态、入口审计或等价验证区分 integrated / manual_ready / deferred / removed_top_level | 不得声明环境已接入 |
| 配置检查 | 是否按 10 解析和验证管辖项目配置，并确认配置固定在目标工作区根目录，且展示 LDVH 本体路径、目标工作区根目录和配置文件完整路径 | 不得声明管辖项目配置已生效 |
| 配置层级检查 | 是否检查目标工作区根目录到目标项目路径链上已有项目内配置 | 不得继续执行工作区安装 |
| 事实源目录检查 | 是否回读管辖项目 `ldvh-base/` 及五个子目录状态，并说明每个目录用途 | 不得声明管辖项目事实源初始化完成 |
| 回滚检查 | 是否说明回滚或卸载入口，并验证卸载后不再自动触发 LDVH | 不得声明部署闭环完整 |

## 11. Human Gate

以下情况必须进入 Human Gate：

1. 安装、升级、禁用、卸载或迁移 LDVH 插件 / 扩展包 / package；
2. 写入、覆盖、删除或迁移环境入口、Hook、plugin lifecycle event 或 repo instruction；
3. 创建、修改、迁移目标工作区根目录下的 `LDVH-GOVERNED-PROJECTS.yaml`，或确认 LDVH 本体路径 / 目标工作区根目录；
4. 创建、删除、迁移或重命名管辖项目 `ldvh-base/` 及事实源子目录；
5. 删除、迁移、合并、覆盖或保留同一路径链上的多个 `LDVH-GOVERNED-PROJECTS.yaml`；
6. 接受用户级配置目录后置缺口或其它当前 Code 不支持的配置候选；
7. 声称环境入口 integrated、接受阻断行为、接受残留风险、确认安装方案预览、选择执行 / 不执行 / 返回修改或要求 Human 验收；
8. 多项目、跨项目或混合非管辖 target 的安装、配置或验证范围不清。

## 12. Stop Conditions

出现以下情况时，AI 必须暂停：

1. 目标环境、写入对象、写入位置级别或影响范围不清；
2. 缺少安装向导状态表、用户告知清单、安装方案预览或最终确认，或这些内容未交给 Human 确认；
3. 插件、Hook、repo instruction、旧路径或历史 trust 被写成 integrated 证明；
4. LDVH 本体路径、目标工作区根目录或目标工作区配置文件完整路径不清；
5. 目标项目内已有 `LDVH-GOVERNED-PROJECTS.yaml` 尚未删除、迁移或明确保留；
6. 管辖项目 `ldvh-base/` 目录用途、写入影响或 Human Gate 状态未说明，或系统已检查事实被重新包装成 Human 选项；
7. Code、环境审计或工具输出正在替代 Human Gate、事实源或完成判断；
8. 验证、回滚或卸载路径不可复现，却要求声明安装部署完成。

## 13. 待补齐事项

1. 本模板用于真实安装、升级、禁用、卸载或迁移 LDVH 插件 / 扩展包 / package 前，必须重新生成用户告知清单并进入 Human Gate；
2. 用户级配置目录和项目内配置不是本模板支持的主位置；如已存在，只能作为 legacy / conflict 或后置缺口处理；
3. 本模板当前只承接最小安装、初始化、管辖项目配置和事实源目录初始化闭环；若要扩展到批量管辖项目配置、跨项目安装或完整卸载记录，必须先修订本文并重新进入 Human Gate；
4. 本模板声明安装、升级或卸载完成前，需要 Code 实现域提供可复现的 status、正反例和 rollback 证据；
5. 本模板不得登记 Git 提交、WorkCase 推进或其它 31+ 行动模板候选的迁入判断；跨模板候选筛选统一回到 `specs/06-行动模板基础规范.md`。
