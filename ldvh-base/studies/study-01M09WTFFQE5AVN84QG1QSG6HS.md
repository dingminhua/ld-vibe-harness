---
title: dynamic-ui 内联可视化技能能力与跨环境可用性评估
status: active
report_kind: technical_assessment
research_question: 对 TRAE 内建 dynamic-ui 内联可视化技能（SKILL.md、5 场景、16 模板、视觉 token 契约与渲染契约），它提供了哪些能力？这些内容资产与渲染机制能否被移植或复用到其它环境（其它宿主、IDE、自研运行时）？
abstract: 对 TRAE 内建 dynamic-ui 内联可视化技能做技术评估：单入口 SKILL.md + 5 个场景（data-visualization、architecture-and-flow、comparison-and-decision、mechanism-explanation、micro-interaction）+ 16 个 ready 模板（templates/manifest.json）+ 一套紧凑 CSS token（tokens/visual-tokens.md）+ 一个渲染工具 PureShowWidget，形成『风格→内容→脚本』的流式内联可视化契约。关键发现：内容资产（场景、模板、token、渲染规则）高度环境解耦、可整体复用；widget_code 自含 token、主题由宿主注入 data-widget-theme、脚本只从白名单 CDN 加载、DOM 全部限定在根节点内，因此唯一硬依赖是宿主是否提供 PureShowWidget 同构的内联沙箱渲染能力。限制：该沙箱运行时能力（PureShowWidget、主题注入、sendPrompt、CDN 白名单、禁 position:fixed 等）只在当前 TRAE 宿主得到确认，未在 LDVH 或其它自研环境实测。建议：复用时优先迁移内容层与渲染契约，再按目标宿主能力评估是否自建同构沙箱，无需在 LDVH 内重复实现完整渲染器。
research_intent: 项目需要判断 TRAE 内建 dynamic-ui 技能能否在其它环境（自研工具、其它 IDE 插件、无该技能的宿主）中复用，避免重复开发内联可视化能力，并为选择『内容层迁移』还是『与宿主共建运行时沙箱』提供依据。
recommendation_summary: dynamic-ui 的内容资产（5 场景、16 模板、token 契约、渲染规则）可整体迁移并在任何提供同构内联渲染沙箱的环境复用；硬依赖只有宿主侧 PureShowWidget 类渲染器与 data-widget-theme 主题注入。后续在需要复用时先评估目标宿主是否已有等价渲染能力：有则只迁内容层，无则与宿主共建沙箱或自建最小实现；当前无需在 LDVH 内自行实现完整渲染器。
input_refs:
- kind: skill
  locator: /Users/dmh2002/.trae-cn/builtin/global/skills/dynamic-ui/SKILL.md
  observed_at: '2026-08-18T07:35:44Z'
- kind: skill
  locator: /Users/dmh2002/.trae-cn/builtin/global/skills/dynamic-ui/templates/manifest.json
  observed_at: '2026-08-18T07:35:44Z'
- kind: skill
  locator: /Users/dmh2002/.trae-cn/builtin/global/skills/dynamic-ui/tokens/visual-tokens.md
  observed_at: '2026-08-18T07:35:44Z'
- kind: specification
  locator: specs/24-Study-研究报告.md
  version: b1d1489d
  observed_at: '2026-08-18T07:35:44Z'
change_log:
- at: '2026-08-18T07:36:51.989225Z'
  summary: 受控创建 technical_assessment：评估 TRAE 内建 dynamic-ui 内联可视化技能的能力组成与跨环境可用性，形成内容层可复用、运行时沙箱为硬依赖的评估结论。
  signature:
    product_name: TraeCode
    model_name: deepseek-v4-flash
object_uid: 01a013cd-3df7-7155-baa0-97806f981a39
object_id: study-01M09WTFFQE5AVN84QG1QSG6HS
fact_type_key: study
created_at: '2026-08-18T07:36:51.989225Z'
updated_at: '2026-08-18T07:36:51.989225Z'
---

## 研究问题

当前项目需要为内联可视化能力选择复用路径：TRAE 内建了 dynamic-ui 技能，项目可能需要在其它环境（自研工具、其它 IDE 插件、无该技能的宿主）中提供同等的图表/架构图/交互 demo 能力。

本报告回答的具体问题：对 dynamic-ui 技能（SKILL.md、scenes/、tokens/、templates/），它提供了哪些能力？其内容资产与渲染机制能否被移植或复用到其它环境？哪些是可整体复用的内容，哪些是宿主专属的运行时硬依赖？

## 输入与边界

本评估的输入来源与分工如下：

| 来源 | 用途 | 限制 |
|---|---|---|
| `dynamic-ui/SKILL.md` | 能力边界、Tool Contract、Rendering Contract、场景路由与视觉设计规则 | 只评估其声明的契约，不验证宿主实现是否符合 |
| `dynamic-ui/templates/manifest.json` | 16 个 ready 模板清单（chart/comparison/diagram 三类） | 未逐一展开每个模板的 widget-code.html 细节 |
| `dynamic-ui/tokens/visual-tokens.md` | 颜色/间距/圆角/字体 token 契约 | 只抽取 token 闭集与主题注入方式 |
| `specs/24-Study-研究报告.md` | Study 类型定义、正文骨架与验证要求 | 作为本对象的形式依据 |

观察时点：2026-08-18（评估基于当前工作树中上述技能文件的当次内容）。

未覆盖范围：未在其它宿主/运行时中实测渲染；未读取每个模板的完整 widget-code.html；未评估技能更新版本差异；未验证 PureShowWidget、主题注入、sendPrompt 等运行时能力在 TRAE 之外是否存在。

## 关键发现

### 发现 1：dynamic-ui 由『单入口 + 场景 + 模板 + token + 渲染工具』五部分构成

dynamic-ui 的目录结构为：SKILL.md（唯一入口）+ `scenes/`（5 个场景文件）+ `templates/`（16 个 ready 模板，每模板含 template.md/widget-code.html/fixture.json）+ `tokens/visual-tokens.md`（CSS token 定义）。

能力路径：先判断是否需要内联可视化，再按意图路由到 5 个场景之一，场景再补充模板选择（templates/manifest.json 中 16 个 ready 模板按 intent 映射），最后调用 PureShowWidget 渲染。

对后续项目工作的直接影响：这给出了『可视化能力 = 场景路由 + 模板库 + token 契约 + 渲染器』的组成模型，是评估任何内联可视化复用方案时的拆解框架。

### 发现 2：渲染契约高度环境解耦，widget_code 自含 token 与主题

Rendering Contract 要求：widget_code 内自含 token 定义（首段 `<style>` 顶部）、主题由宿主注入 `:root[data-widget-theme="light"|"dark"]`、脚本只从白名单 CDN（cdnjs/ esm.sh/ jsdelivr/ unpkg）加载、DOM 查询全部限定在根节点（`data-dynamic-ui-widget`）内、禁 position:fixed 与全局选择器。

这些规则使生成的 widget_code 是自足的 HTML/SVG 片段，不依赖宿主 CSS；只要宿主提供同构沙箱即可原样呈现。

对后续项目工作的直接影响：内容层（场景、模板、token、渲染规则）可视为可移植资产，移植成本主要由『宿主是否已有等价渲染沙箱』决定。

### 发现 3：可复用性分两层——内容层可整体迁移，运行时为硬依赖

- 内容层（可整体复用）：5 个场景指南、16 个模板（template.md + widget-code.html + fixture.json）、token 契约、SVG 几何规则、复杂性预算、视觉设计原则——这些是纯内容/指南，可复制到任何提供内联渲染的环境。
- 运行时层（硬依赖）：PureShowWidget 渲染工具、`data-widget-theme` 主题注入、`window.sendPrompt`、白名单 CDN 沙箱、无 position:fixed 的宿主约束——这些属于当前 TRAE 宿主的运行时能力，其它环境是否具备需逐项核对。

限制说明：本评估只基于技能文件的契约声明，未在其它环境实测渲染；因此『运行时为硬依赖』的结论是契约层判断，不是跨环境实测结论。

对后续项目工作的直接影响：若在其它环境复用，应先回答『目标宿主是否已有等价内联渲染沙箱』，再决定只迁内容层还是需要共建运行时。

## 建议

1. **内容层迁移（低成本、可立即做）**：把 `scenes/`、`templates/`、`tokens/visual-tokens.md` 与 SKILL.md 的渲染规则文档迁移到目标环境，作为内联可视化生成的规范依据。适用条件：目标环境只要内容指南、已有或准备实现同构渲染沙箱。风险：没有等价沙箱时内容层无法直接呈现。验收：目标环境能按场景+模板生成并渲染同构 widget_code。

2. **运行时能力核对（前置判断）**：复用时先逐项核对目标宿主是否具备 PureShowWidget 类渲染、`data-widget-theme` 注入、白名单 CDN 加载、无 position:fixed 约束。适用条件：任何移植场景。风险：逐项核对成本随宿主差异增大。验收：核对清单全部通过或明确缺口。

3. **无需在 LDVH 内重复实现完整渲染器（当前）**：本项目暂无独立渲染沙箱需求；直接复用 TRAE 宿主已提供的 dynamic-ui 即可，不立项自研。适用条件：仅在当前 TRAE 宿主内使用内联可视化。风险：离开该宿主后内容层无运行时承接。验收：当前会话能正常调用 PureShowWidget 渲染。

以上均为评估方向，不构成已决定行动。

## 后续分流

| 建议 | 承接方向 | 判断标准 |
|---|---|---|
| 内容层迁移 | 仅在需要把 dynamic-ui 能力带出当前宿主时，派生 Spark 评估迁移范围 | 出现『必须在无 dynamic-ui 的宿主中提供同等内联可视化』的真实需求时立项；否则保持无需对象化 |
| 运行时能力核对 | 作为内容层迁移的必经前置，可并入同一 Spark | 目标宿主不确定时先做核对清单；确认缺运行时则评估共建或自建最小沙箱 |
| 无需自研渲染器 | 无需对象化 | 只要当前 TRAE 宿主持续可用且满足内联可视化需求，持续无需对象化；一旦确认现有宿主能力不满足，再重新评估 |

### 后续监测

- 若 dynamic-ui 技能内容发生实质版本变化，或项目确认需要在其它宿主/运行时提供同等可视化能力，再更新本评估。
- 本报告不建立遥测、Dashboard 或告警。
