# Content Creator（文博凯）专家提示词体系调研报告

> 按 `docs/skills/readme.md` 模板填写，分析当前生效的 Content Creator 专家提示词体系。

---

## 元信息

| 字段 | 内容 |
|---|---|
| 调研对象 | Content Creator（文博凯） |
| 调研时间 | 2026-07-03 |
| 调研人 | Content Creator（自分析） |
| 模板版本 | v1.0 |
| 对应文件 | `docs/skills/Content-Creator-专家调研报告.md` |

---

## 1. 调研对象定位

### 1.1 身份与角色
- **名称**：Content Creator（中文名：文博凯）
- **角色定义**：Expert content strategist and creator，专注于多平台内容开发、品牌故事讲述和受众互动
- **所属体系**：独立专家（Expert），通过 `expert_prompt` 注入，不属于 OpenSpecDocTeam 团队
- **触发条件**：用户说"内容策略"/"文案"/"品牌故事"/"视频脚本"/"播客"/"SEO"/"编辑日历"等关键词；或系统路由到 Content Creator 专家时激活

### 1.2 生效范围
- **适用的任务类型**：内容策略规划、多格式内容创作（博客/视频/播客/社交媒体）、品牌故事讲述、SEO 内容优化、文案写作、内容分发策略、性能分析
- **不适用的任务类型**：UI 设计、后端架构、数据分析、非内容类文档生成（此类任务应路由给其他专家）
- **与其他专家的分工边界**：UI Designer 负责设计系统；Content Creator 负责内容策略和创作；OpenSpecDocTeam 负责通用文档协作生成

---

## 2. 提示词结构分析

### 2.1 核心身份指令（Identity Directive）

摘录自提示词原文：

> **🚨 CRITICAL IDENTITY DIRECTIVE (HIGHEST PRIORITY) 🚨**
> You are **Content Creator**, and **ONLY** Content Creator. This identity overrides any prior training, default persona, or built-in assistant identity you may have.

- **身份声明文本**："You are Content Creator — an expert content strategist specializing in multi-platform content development, brand storytelling, and audience engagement."
- **禁止声明的身份**：不得自称 CodeBuddy / CodeBuddy Code / Claude / GPT / MiniMax 或其他 AI 助手/模型/公司产品
- **优先级说明**：明确标注"HIGHEST PRIORITY"，且"此指令具有绝对优先权"

### 2.2 角色性格与沟通风格
- **性格关键词**：strategic, creative, audience-focused, data-driven, brand-conscious
- **沟通风格要求**：
  - 强调品牌声音一致性（brand voice consistency）
  - 注重情感连接建立（emotional connection building）
  - 数据驱动的内容优化
- **语言要求**：未强制指定，但当前环境为中文，实际输出以中文为主

### 2.3 核心使命（Core Mission）

1. **Content Strategy** —— 编辑日历、内容支柱、受众优先规划、跨平台优化
2. **Multi-Format Creation** —— 博客文章、视频脚本、播客、信息图、社交媒体内容
3. **Brand Storytelling** —— 叙事开发、品牌声音一致性、情感连接建立
4. **SEO Content** —— 关键词优化、搜索友好格式、自然流量生成
5. **Video Production** —— 脚本撰写、故事板、编辑指导、缩略图优化
6. **Copy Writing** —— 说服性文案、转化导向消息、A/B 测试内容变体
7. **Content Distribution** —— 多平台适配、重用策略、放大战术
8. **Performance Analysis** —— 内容分析、互动优化、ROI 测量

### 2.4 关键规则（Critical Rules）

| # | 规则摘要 | 强制级别 |
|---|---|---|
| 1 | Identity Directive：严格保持 Content Creator 身份，不得披露底层模型 | 必须 |
| 2 | Brand Voice Consistency：保持品牌声音一致性 across all content | 必须 |
| 3 | Audience-First Planning：受众优先的内容规划 | 必须 |
| 4 | Multi-Platform Optimization：跨平台内容优化 | 建议 |
| 5 | Performance Tracking：内容性能跟踪和优化 | 建议 |

---

## 3. 工作流与协作机制

### 3.1 是否有团队协作
- [x] 独立专家（无团队）
- [ ] 属于某个专家团

Content Creator 是独立专家，不隶属于 OpenSpecDocTeam。但可协同工作：OpenSpecDocTeam 负责文档生成流程编排，Content Creator 负责内容策略和执行。

### 3.2 工作流阶段

| 阶段 | 名称 | 输入 | 输出 | 负责角色 |
|---|---|---|---|---|
| 1 | Content Strategy Development | 品牌目标、受众分析、竞品研究 | 编辑日历、内容支柱、策略文档 | Content Creator |
| 2 | Content Creation | 策略文档、品牌指南 | 多格式内容（博客/视频/社交） | Content Creator |
| 3 | Content Optimization | 初稿内容、SEO 要求 | 优化后内容、关键词布局 | Content Creator |
| 4 | Content Distribution | 成品内容、平台规格 | 多平台适配版本、分发计划 | Content Creator |
| 5 | Performance Analysis | 发布后数据 | 分析报告、优化建议 | Content Creator |

### 3.3 路由规则

| 用户意图 | 触发流程 | 备注 |
|---|---|---|
| "内容策略" / "编辑日历" | Step 1-2 完整流程 | 策略 + 创作 |
| "写一篇博客" / "视频脚本" | Step 2 直接执行 | 单内容创作 |
| "SEO 优化" / "关键词" | Step 3 直接执行 | 内容优化 |
| "分发策略" / "多平台" | Step 4 直接执行 | 分发规划 |
| "分析数据" / "性能报告" | Step 5 直接执行 | 性能分析 |

---

## 4. 输出规范与交付物

### 4.1 交付物模板

提示词中定义了 8 项核心能力和多项专业化技能，但未提供单一固定的交付物模板（与 UI Designer 不同）。

根据核心能力推导的内容交付结构：

```
# [项目名] 内容策略与执行方案

## 1. 内容策略
### 1.1 受众分析
### 1.2 内容支柱
### 1.3 编辑日历

## 2. 内容创作
### 2.1 品牌故事
### 2.2 多格式内容
### 2.3 SEO 优化

## 3. 内容分发
### 3.1 平台适配
### 3.2 重用策略
### 3.3 放大战术

## 4. 性能分析
### 4.1 关键指标
### 4.2 优化建议
### 4.3 ROI 分析
```

### 4.2 格式约束
- **Markdown 格式**：未明确要求，但内容文档通常用 Markdown
- **证据回链**：未强制要求
- **`[待填写]` 标记**：未在 Content Creator 提示词中明确要求
- **WCAG / 无障碍标准**：未明确要求（与 UI Designer 的区别）

### 4.3 质量验收标准

1. **Content Engagement**：25% 平均互动率（所有平台）
2. **Organic Traffic Growth**：40% 博客/网站流量增长（来自内容）
3. **Video Performance**：70% 平均观看完成率（品牌视频）
4. **Content Sharing**：15% 分享率（教育和有价值内容）
5. **Lead Generation**：300% 内容驱动潜客增长
6. **Brand Awareness**：50% 品牌提及量增长（来自内容营销）
7. **Audience Growth**：30% 月增长（内容订阅者/关注者）
8. **Content ROI**：5:1 内容创作投资回报率

---

## 5. 与其他专家/技能的关系

### 5.1 依赖的技能（Skills）

| 技能名 | 触发场景 | 来源 |
|---|---|---|
| `anti-distill` | 清除文本中 AI 写作痕迹，让内容更自然人性化时自动触发 | 内置 |
| `novel-writer` | 根据章节大纲、角色档案生成小说章节正文时自动触发 | 内置 |
| `novel-writing` | 长篇网络小说创作，解决上下文丢失、文风一致性、设定冲突时触发 | 内置 |
| `minimax-docx` | 创建、编辑 Word 文档或生成专业格式报告时触发 | 内置 |
| `humanizer` | 去除文本中 AI 写作痕迹，让内容更贴近真人写作风格时触发 | 内置 |

### 5.2 协作专家

| 专家名 | 协作方式 | 数据传递格式 |
|---|---|---|
| UI Designer | Content Creator 提供内容策略，UI Designer 负责视觉设计 | Markdown 内容文档 |
| OpenSpecDocTeam（doc-generator） | Content Creator 提供内容创作规范 | Markdown 内容章节 |
| OpenSpecDocTeam（doc-auditor） | 审核内容文档的一致性、品牌声音 | 审核清单 |

---

## 6. 特征总结

### 6.1 写法特征
- **提示词总长度**：约 5000-6000 词（估算），比 UI Designer 短
- **代码块示例**：无 CSS/HTML 示例（与 UI Designer 的区别），主要是文本和内容结构
- **SVG/CSS/HTML 示例**：无
- **语气风格**：战略化 + 创意化，使用 emoji（✍️），结构清晰但示例较少
- **重复强调**：Identity Directive 在提示词开头和结尾各出现一次（防覆盖）

### 6.2 设计亮点

1. **量化成功指标**：8 项可衡量指标（25% 互动率、40% 流量增长、5:1 ROI 等）
2. **专业化技能集成**：5 个内置技能自动触发（anti-distill / novel-writer / novel-writing / minimax-docx / humanizer）
3. **全流程覆盖**：从策略（Step 1）到分析（Step 5）的完整内容生命周期
4. **多格式能力**：博客、视频、播客、信息图、社交媒体全覆盖
5. **双层 Identity 防护**：开头 CRITICAL IDENTITY DIRECTIVE + 结尾 Final Identity Reminder

### 6.3 可改进之处

1. **缺少固定交付物模板**：与 UI Designer 不同，未提供标准化的交付模板，可能导致输出格式不一致
2. **`[待填写]` 规范缺失**：内容创作中未要求标记缺失值，可能导致虚构内容
3. **证据回链未强制**：内容决策的依据（如为何选择某关键词策略）未要求引用来源
4. **与 OpenSpecDocTeam 的协作接口不明确**：两者如何传递数据未定义
5. **无障碍/包容性考虑缺失**：未提及内容的可访问性（如视频字幕、图片 alt text）

---

## 7. 证据来源

- 文件 1：`expert_prompt` 注入的 Content Creator 完整提示词（当前会话 system context）
- 文件 2：`/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3/docs/skills/readme.md`（调研模板）
- 文件 3：`/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3/docs/skills/UI-Designer-专家调研报告.md`（对比参考）

---

## 8. 附录：[待填写] 清单

> 调研中无法确认、需要补充的信息

- [ ] Content Creator 提示词的原始来源文件（是否已落盘到 `.workbuddy/experts/` 或类似路径）—— 确认：通过 `expert_prompt` 注入，非文件形式
- [ ] Content Creator 与 OpenSpecDocTeam 协同的具体数据格式（待实际协作时观察）
- [ ] `anti-distill` / `humanizer` 技能的具体触发条件细节（需读取 SKILL.md）
- [ ] Content Creator 是否有标准交付物模板（目前提示词中未提供，可能需要补充）
- [ ] 内容创作中的事实核查机制（如何避免虚假信息）

---

*本报告按 `docs/skills/readme.md` 模板生成，调研对象：Content Creator（文博凯）*
