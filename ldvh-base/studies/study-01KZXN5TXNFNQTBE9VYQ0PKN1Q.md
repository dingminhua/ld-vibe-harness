---
title: 技能登记字段调研：各环境技能安装/登记要求与 LDVH 填值分工
status: active
urls:
- ref: https://agentskills.io/specification
  title: Agent Skills Specification — agentskills.io
  summary: 支持：通用 frontmatter 字段闭集权威——name/description 必填及约束（≤64 小写连字符、须与父目录同名；≤1024 字符），license/compatibility(≤500)/metadata/allowed-tools 可选，未识别字段被运行时忽略；三级渐进披露。限制：不覆盖各环境私有扩展与市场列表字段；页面未标注版本日期。2026-07-31 经搜索服务读取。
- ref: https://docs.trae.cn/ide_skills
  title: 技能（Skill）— TRAE IDE 官方文档
  summary: 支持：Trae 技能目录（项目 .trae/skills/、全局 ~/.trae-cn/skills）、手动创建表单三字段（技能名称/描述/指令）、SKILL.md 或 zip 导入自动填充、面板启用开关与 skill-config.json、.agents/skills/ 目录支持。限制：面向中国版 IDE；表单字段随版本可能变化。2026-07-31 经搜索服务读取。
- ref: https://docs.trae.cn/cli_skills
  title: 技能 — TRAE CLI 官方文档
  summary: 支持：CLI 侧目录（~/.traecli/skills、项目 .traecli/skills/）、兼容读取 IDE 两目录、CLI 不支持中文技能名。限制：不含表单与启用机制细节。2026-07-31 经搜索服务读取。
- ref: https://www.thepromptindex.com/claude-code-skills-vs-openai-codex-skills.html
  title: 'Claude Code Skills vs OpenAI Codex Skills: SKILL.md Comparison 2026'
  summary: 支持：Claude（~/.claude/skills、.claude/skills，/skill 调用，allowed-tools 等私有 frontmatter）与 Codex（.agents/skills、$HOME/.agents/skills，$skill 调用，agents/openai.yaml sidecar 承载 UI/策略/MCP 依赖）对比与互迁。限制：非官方一手文档（权威度未评级），Codex 目录另有 ~/.codex/skills 与 .codex/skills 说法（agensi.io，B 级），接入时须以 OpenAI 当前官方文档复核。2026-07-31 经搜索服务读取。
research_question: 各目标 AI 环境安装或登记一项技能时要求提供哪些字段信息，LDVH 薄 Skill 每个字段的规范填值与其权威来源分别是什么？
abstract: 本轮读取 Agent Skills 开放规范与 Trae、Codex、Claude 四方资料，结合 Kimi Work 既有实证（study-0018），梳理技能安装/登记字段：开放标准仅 name/description 必填，license/compatibility/metadata 可选；Trae 创建表单为技能名称/描述/指令三字段并支持导入自动填充；Codex 与 Claude 以目录放置加 frontmatter 为主，私有扩展分别走 agents/openai.yaml 与 Claude 专属 frontmatter；市场卡片的图标与厂商名属提交侧元数据。LDVH 填值分工：name/description/指令正文照抄 skill/SKILL.md 当次内容；license=MIT 与作者=LD Vibe Harness 现取 LICENSE 版权行；版本现取 pyproject（当前 0.1.0）；仓库 URL 现取 git remote origin；图标素材现取 icons/。关键限制：Codex 技能目录存在两种二手说法未读官方一手文档；各环境表单随版本变化，接入时须复核。
research_intent: 用户将携 LDVH 薄 Skill 前往 Trae、Claude、Codex 等环境接入，要求把各环境技能登记所需字段提前调研并备好填值，使接入方照表填写即可，避免逐环境临时摸索。本研究提供字段级准备清单与照抄/现取/不预填的分工，支撑 README 一句话接入流程在任意环境的可复制，并防止接入方为凑字段而改写 canonical SKILL.md 内容。
recommendation_summary: 接入任一新环境时先按 33 复核该环境当前官方技能资料，再按分工填值：name、description、指令正文一律照抄 skill/SKILL.md 当次内容（表单自动填充不一致时以 canonical 为准修正）；license、作者、版本、仓库 URL、图标素材按各自权威来源现取；环境私有扩展字段（agents/openai.yaml、Claude 专属 frontmatter 等）首次接入一律不预填，确有需要时在目标环境侧沉淀。SKILL.md frontmatter 维持 name/description 两字段不增补（增补引入版本漂移与重部署负担）。技能市场上架属另一议题，届时另起 Study。
object_id: study-01KZXN5TXNFNQTBE9VYQ0PKN1Q
object_uid: 019ffb52-ebb5-7d6f-a5b9-3bf5c169d437
fact_type_key: study
created_at: '2026-07-31T19:51:27.592577+08:00'
updated_at: '2026-08-16T21:42:45.620720Z'
action_relevance: 在目标环境中部署或登记 LDVH 技能时，按当次环境官方资料逐字段填写，不预填或猜测厂商专有字段
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:04:00.951627Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: 2026-08-16T21:30:34.415045Z
---

## 研究问题

当前项目为什么需要这轮研究：用户将携 LDVH 薄 Skill 前往 Trae、Claude、Codex 等环境接入，要求把各环境安装或登记技能时要求填写的字段提前调研、备好填值，使接入方照表执行，支撑 README 一句话接入流程的跨环境可复制。

本对象实际回答的外部问题：各目标 AI 环境安装或登记一项技能时要求提供哪些字段信息；LDVH 薄 Skill 每个字段的规范填值与其权威来源。

## 输入与边界

外部资料四份（2026-07-31 经搜索服务读取，逐条支持/限制见 urls）：

- Agent Skills 开放规范（agentskills.io）：通用 frontmatter 字段闭集与约束的权威。
- TRAE IDE 技能官方文档：目录、创建表单字段、导入与启用机制。
- TRAE CLI 技能官方文档：CLI 侧目录与命名限制。
- Codex 与 Claude Code 技能对比资料（非官方一手）：两环境目录、调用方式与私有扩展位；Codex 目录存在 `~/.codex/skills/` 与 `.agents/skills/` 两种并存说法。

Kimi Work 侧结论沿用 study-0018 本机实证：frontmatter 字段仅 name/description/license/metadata 类；无图标配置面，全部技能渲染为字母头像。

LDVH 本地权威来源：`skill/SKILL.md`（name 与 description 的 canonical）、`LICENSE`（MIT，版权行 "LD Vibe Harness"）、`pyproject.toml`（name 与 version 0.1.0）、`git remote origin`（github.com/dingminhua/ld-vibe-harness）、`icons/`（12 个尺寸 PNG 与源图）。

未覆盖范围：各环境技能市场的提交后台实际表单字段；Windows 侧路径细节；云端 Agent 形态；未来版本变化。

## 关键发现

1. 开放标准只要求两个字段。`name`（≤64 字符，小写字母数字与连字符，须与父目录同名）与 `description`（≤1024 字符，说明做什么与何时用）必填；`license`、`compatibility`（≤500 字符）、`metadata`（author/version 等键值映射）、`allowed-tools`（实验性）可选，不识别的运行时忽略未知字段。LDVH 当次合规性实测：name=ldvh（4 字符、合法字符集）、description 313 字符、frontmatter 无尖括号、正文约 1650 字符。对项目工作的直接影响：SKILL.md frontmatter 维持 name/description 两字段即可跨环境流通，增补可选字段反而引入版本漂移与重部署负担，不加。

2. 分环境登记面快照（观察时点 2026-07-31）：

| 环境 | 技能目录 | 登记方式与要求字段 | 调用方式 |
|---|---|---|---|
| Kimi Work | 运行时托管技能目录 | 无独立登记表单；登记内容即 SKILL.md frontmatter；经技能管理开关启用；无图标机制（study-0018） | 斜杠调用与描述匹配自动触发 |
| Trae IDE | 项目 `.trae/skills/`、全局 `~/.trae-cn/skills`（Windows `%userprofile%/.trae-cn/skills`） | 手动创建表单三字段：技能名称、描述、指令；或上传 SKILL.md/zip 由 Trae 自动填充三字段后可修改；面板开关启用 | 描述匹配自动调用，可显式点名 |
| Trae CLI | `~/.traecli/skills`、项目 `.traecli/skills/` | 目录放置；不支持中文技能名 | 兼容读取 IDE 两个目录 |
| Codex | `~/.codex/skills/` 与 `.codex/skills/`（另有 `.agents/skills/` 与 `$HOME/.agents/skills/` 一说） | 目录放置加 frontmatter；UI 显示数据、隐式调用策略与 MCP 依赖等私有元数据走 `agents/openai.yaml` sidecar | `$技能名` 显式调用或描述匹配 |
| Claude Code | `~/.claude/skills/`、`.claude/skills/` | 目录放置加 frontmatter；allowed-tools、argument-hint、disable-model-invocation 等私有控制走 Claude 专属 frontmatter | `/技能名` 或描述匹配自动加载 |

3. LDVH 填值分工。照抄类：技能名称、描述、指令正文一律取 `skill/SKILL.md` frontmatter 与正文的当次内容，不重述不改写（部署件逐字节一致契约不变）。现取类：license 为 MIT、作者署名为 LD Vibe Harness，均看 `LICENSE` 版权行；版本看 `pyproject.toml` `[project] version`（当前 0.1.0）；仓库 URL 看 `git remote origin`；图标素材看 `icons/`（环境确有图标机制时）。不预填类：Codex `agents/openai.yaml`、Claude 专属 frontmatter 等厂商私有字段，首次接入一律不预填，确有需要时在目标环境自己的仓库沉淀。

4. 市场列表字段属提交侧元数据。技能市场卡片上的图标、"by 厂商"署名、一句话标语（如支付宝技能卡）由市场上架提交时提供，不是本地安装/登记字段；LDVH 的对应素材（icons/ 多尺寸、LICENSE 署名、pyproject description）已就绪，上架研究届时另行启动。

## 建议

接入任一新环境时：先按 33 复核该环境当前官方技能资料（目录、表单、启用机制），再按本报告"照抄/现取/不预填"分工填值；name 与 description 永远以 `skill/SKILL.md` 当次内容为准，环境表单的自动填充结果若与其不一致，以 canonical 为准修正。接入报告引用本研究作为字段依据；各环境复核结论各归其接入报告，不回写本对象。

## 后续分流

| 事项 | 承载方向 | 触发信号 |
|---|---|---|
| Trae 环境接入 | 复用本报告 Trae 行并复核官方文档，结论归当次接入报告 | Trae 接入任务启动 |
| Codex 技能目录两说 | 接入时读 OpenAI 官方一手文档定夺，不凭二手资料落安装路径 | Codex 接入任务启动 |
| 技能市场上架 | 另起 Study（提交字段、审核要求、图标规格） | 上架进入议题 |
| 环境登记字段变化 | 更正本对象或新建 Study | 官方文档更新或接入实测不符 |
