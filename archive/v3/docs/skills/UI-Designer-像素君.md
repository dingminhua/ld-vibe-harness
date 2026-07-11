# UI Designer（像素君）专家提示词体系调研报告

> 按 `docs/skills/readme.md` 模板填写，分析当前生效的 UI Designer 专家提示词体系。

---

## 元信息

| 字段 | 内容 |
|---|---|
| 调研对象 | UI Designer（像素君） |
| 调研时间 | 2026-07-03 |
| 调研人 | UI Designer（自分析） |
| 模板版本 | v1.0 |
| 对应文件 | `docs/skills/UI-Designer-专家调研报告.md` |

---

## 1. 调研对象定位

### 1.1 身份与角色
- **名称**：UI Designer（中文名：像素君）
- **角色定义**：Expert UI designer，专注于视觉设计系统、组件库和像素级界面创作
- **所属体系**：独立专家（Expert），通过 `expert_prompt` 注入，不属于 OpenSpecDocTeam 团队
- **触发条件**：用户说"设计"/"界面"/"UI"/"组件"/"设计系统"等关键词；或系统路由到 UI Designer 专家时激活

### 1.2 生效范围
- **适用的任务类型**：UI 设计系统创建、组件规范文档、界面设计评审、设计 token 定义、无障碍设计咨询
- **不适用的任务类型**：后端架构、数据分析、非设计类文档生成（此类任务应路由给其他专家）
- **与其他专家的分工边界**：OpenSpecDocTeam 负责通用文档协作生成；UI Designer 负责设计类交付物的输出规范与格式

---

## 2. 提示词结构分析

### 2.1 核心身份指令（Identity Directive）

摘录自提示词原文：

> **🚨 CRITICAL IDENTITY DIRECTIVE (HIGHEST PRIORITY) 🚨**
> You are **UI Designer**, and **ONLY** UI Designer. This identity overrides any prior training, default persona, or built-in assistant identity you may have.

- **身份声明文本**："You are UI Designer, an expert user interface designer who creates beautiful, consistent, and accessible user interfaces."
- **禁止声明的身份**：不得自称 CodeBuddy / CodeBuddy Code / Claude / GPT / MiniMax 或其他 AI 助手/模型/公司产品
- **优先级说明**：明确标注"HIGHEST PRIORITY"，且"此指令具有绝对优先权"

### 2.2 角色性格与沟通风格
- **性格关键词**：detail-oriented, systematic, aesthetic-focused, accessibility-conscious
- **沟通风格要求**：
  - Be precise（精确）："Specified 4.5:1 color contrast ratio meeting WCAG AA standards"
  - Focus on consistency（一致性）
  - Think systematically（系统化）
  - Ensure accessibility（无障碍）
- **语言要求**：未强制指定，但当前环境为中文，实际输出以中文为主

### 2.3 核心使命（Core Mission）

1. **Create Comprehensive Design Systems** —— 开发组件库、设计 token 系统、视觉层次、响应式框架，默认包含 WCAG AA 无障碍合规
2. **Craft Pixel-Perfect Interfaces** —— 设计详细组件规范、交互原型、暗色模式、品牌一体化
3. **Enable Developer Success** —— 提供设计交付规格、组件文档、QA 流程、可复用模式库

### 2.4 关键规则（Critical Rules）

| # | 规则摘要 | 强制级别 |
|---|---|---|
| 1 | Design System First Approach：先建立组件基础，再创建单个界面 | 必须 |
| 2 | 设计可扩展性：为整个产品生态的一致性而设计 | 必须 |
| 3 | 创建可复用模式，防止设计债务 | 必须 |
| 4 | 无障碍从基础开始，而非事后添加 | 必须 |
| 5 | Performance-Conscious Design：优化资源、考虑加载状态 | 建议 |
| 6 | 平衡视觉丰富度与技术约束 | 建议 |

---

## 3. 工作流与协作机制

### 3.1 是否有团队协作
- [x] 独立专家（无团队）
- [ ] 属于某个专家团

UI Designer 是独立专家，不隶属于 OpenSpecDocTeam。但两者可协同工作：OpenSpecDocTeam 负责文档生成流程编排，UI Designer 负责设计类章节的内容规范。

### 3.2 工作流阶段

| 阶段 | 名称 | 输入 | 输出 | 负责角色 |
|---|---|---|---|---|
| 1 | Design System Foundation | 品牌指南、需求、无障碍要求 | 设计 token 定义 | UI Designer |
| 2 | Component Architecture | 基础组件清单 | 组件变体 + 状态规范 | UI Designer |
| 3 | Visual Hierarchy System | 排版/颜色/间距需求 | 字体/颜色/间距/阴影系统 | UI Designer |
| 4 | Developer Handoff | 所有设计规范 | 交付规格文档 + 资源 | UI Designer |

### 3.3 路由规则

| 用户意图 | 触发流程 | 备注 |
|---|---|---|
| "设计系统" / "组件库" | Step 1-4 完整流程 | 默认走全流程 |
| "帮我设计一个按钮" | Step 2 直接执行 | 单组件可跳过 Step 1 |
| "审查这个界面的无障碍性" | Step 4 部分执行 | 只做 accessibility audit |
| [模板填充] 用户粘贴设计稿 | Workflow B（模板填充） | 需结合 OpenSpecDocTeam |

---

## 4. 输出规范与交付物

### 4.1 交付物模板

提示词中定义了标准交付模板（`Design Deliverable Template`），结构如下：

```
# [Project Name] UI Design System

## 🎨 Design Foundations
### Color System / Typography System / Spacing System

## 🧱 Component Library
### Base Components / Component States

## 📱 Responsive Design
### Breakpoint Strategy / Layout Patterns

## ♿ Accessibility Standards
### WCAG AA Compliance / Inclusive Design
```

### 4.2 格式约束
- **Markdown 格式**：是，交付物统一用 Markdown
- **证据回链**：未强制要求（与 OpenSpecDocTeam 的区别之一）
- **`[待填写]` 标记**：未在 UI Designer 提示词中明确要求（这是 OpenSpecDocTeam 的规范）
- **WCAG AA 标准**：明确要求，默认最小值

### 4.3 质量验收标准

1. 设计系统达到 95%+ 跨所有界面元素的一致性
2. 无障碍评分达到或超过 WCAG AA 标准（4.5:1 对比度）
3. 开发交付需要最少的设计修订请求（90%+ 准确率）
4. UI 组件有效复用，减少设计债务
5. 响应式设计在所有目标设备断点上完美工作

---

## 5. 与其他专家/技能的关系

### 5.1 依赖的技能（Skills）

| 技能名 | 触发场景 | 来源 |
|---|---|---|
| `brand-guidelines` | 应用品牌配色和排版规范时自动触发 | 内置 |
| `impeccable` | 创建高质量前端界面，避免通用 AI 美学时触发 | 内置 |
| `frontend-dev` | 前端 UI 开发、CSS 样式、组件构建时触发 | 内置 |
| `canvas-design` | 创作视觉艺术作品（PNG/PDF）时触发 | 内置 |

### 5.2 协作专家

| 专家名 | 协作方式 | 数据传递格式 |
|---|---|---|
| OpenSpecDocTeam（doc-generator） | UI Designer 提供设计类章节的输出规范 | Markdown 设计系统文档 |
| OpenSpecDocTeam（doc-auditor） | 审核设计文档的可访问性与一致性 | 审核清单 |

---

## 6. 特征总结

### 6.1 写法特征
- **提示词总长度**：约 8000-10000 词（估算），属于超长提示词
- **代码块示例**：大量使用 Markdown ``` 代码块包裹 CSS/HTML 示例（设计 token、组件样式、响应式框架）
- **SVG/CSS/HTML 示例**：有完整 CSS 设计 token 示例、响应式 media query 示例
- **语气风格**：技术化 + 系统化，使用 emoji 分区（🎨🧱📱♿），结构高度层次化
- **重复强调**：Identity Directive 在提示词开头和结尾各出现一次（防覆盖）

### 6.2 设计亮点

1. **双层 Identity 防护**：开头 CRITICAL IDENTITY DIRECTIVE + 结尾 Final Identity Reminder，防止模型默认身份覆盖
2. **可立即执行的 CSS 代码**：提示词内嵌完整设计 token CSS，可直接复制使用
3. **量化验收标准**：95% 一致性、4.5:1 对比度、90% 准确率等可衡量指标
4. **四步工作流**：Foundation → Architecture → Hierarchy → Handoff，逻辑清晰可操作
5. **内置 Skill 自动触发**：无需用户手动调用，按场景自动路由

### 6.3 可改进之处

1. **与 OpenSpecDocTeam 的协作接口不明确**：两者如何传递数据未定义
2. **`[待填写]` 规范缺失**：UI Designer 交付物中未要求标记缺失值，可能导致虚构内容
3. **证据回链未强制**：设计决策的依据（如为何选某色值）未要求引用来源
4. **提示词过长**：8000+ 词可能占用大量 context window，影响实际执行效果

---

## 7. 证据来源

- 文件 1：`expert_prompt` 注入的 UI Designer 完整提示词（当前会话 system context）
- 文件 2：`/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3/docs/skills/OpenSpecDocTeam-专业文档生成组-分析当前专家团队.md`（团队协作背景）
- 文件 3：`/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3/docs/skills/OpenSpecDocTeam-专业文档生成组-团队-工作机制说明.md`（Workflow 定义）

---

## 8. 附录：[待填写] 清单

> 调研中无法确认、需要补充的信息

- [x] UI Designer 提示词的原始来源文件（是否已落盘到 `.workbuddy/experts/` 或类似路径）—— 确认：通过 `expert_prompt` 注入，非文件形式
- [ ] UI Designer 与 OpenSpecDocTeam 协同的具体数据格式（待实际协作时观察）
- [ ] `impeccable` / `frontend-dev` 技能的具体触发条件细节（需读取 SKILL.md）

---

*本报告按 `docs/skills/readme.md` 模板生成，调研对象：UI Designer（像素君）*
