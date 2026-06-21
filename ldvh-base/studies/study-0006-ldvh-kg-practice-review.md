---
id: study-0006
type: study
title: LDVH 知识图谱建设的最新实践与落地评估
status: active
created: '2026-06-20T09:20:00+08:00'
updated: '2026-06-20T10:05:00+08:00'
user_intent: |
  评估“LDVH 是否可直接按现有基础设施建设知识图谱，并给出当前可执行的落地路径”，
  同时结合 2025-2026 的行业实践形成稳健建议。
summary: |
  结合近阶段外部实践，LDVH 已具备图谱化输入基础（结构化对象事实源、标准化 ID、引用关系、提交追溯）；
  但要获得持续可用的知识图谱能力，还需补齐实时图谱投影、关系语义、关系一致性校验与关系查询闭环。
conclusion: |
  LDVH 适合走“先在内生事实源上做轻量图谱化，再逐步接入图检索能力”的路线。
  第 1 阶段目标应是：稳定运行时实体/关系提取器 + 关系一致性校验 + 依赖链/阻塞链可查询视图。
  第 2 阶段目标应是：将图状态纳入 40-43 审核触发与 WorkCase 关闭 Gate。
  第 3 阶段目标应是：结合图增强检索与审核建议，形成图谱驱动的可解释 AI 辅助能力。
  明确边界：图节点、边、元数据和校验结果只能按 CLI/API 请求从当前 code、specs、ldvh-base 与 Git 工作区实时生成，不得落盘为派生事实源，不得使用长期缓存或外部图数据库作为事实缓存。
urls:
- ref: https://neo4j.com/blog/genai/introducing-document-intelligence-from-documents-to-a-knowledge-graph-right-inside-aura/
  title: Neo4j Document Intelligence（从文档构建知识图谱）
  summary: 指出文档数据占比高且向量检索难以表达关系，支撑了 LDVH 优先用内部对象事实源做图谱化的思路。
- ref: https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-neptune-supports-byokg-rag-toolkit/
  title: Neptune BYOKG for GraphRAG
  summary: 提供“已建图谱可直接接入 GraphRAG”模式，提示 LDVH 可后续采用图 + 向量混合检索。
- ref: https://neo4j.com/docs/cypher-manual/current/schema/
  title: Neo4j Schema
  summary: 强调在无模式可演进前提下，对稳定部分使用图类型/约束，支持“核心关系固定 + 关系演进扩展”。
- ref: https://neo4j.com/blog/knowledge-graph/how-to-build-knowledge-graph/
  title: How to Build a Knowledge Graph in 7 Steps
  summary: 提供“建模-导入-测试-维护”闭环，支持 LDVH 将图谱建设按阶段化执行并验收。
related_sparks:
- spark-0016
related_workcases: []
related_adrs: []
related_pitfalls: []
related_docs:
- specs/05.01-字段定义与语义规范.md
- specs/05.02-字段内容与格式规范.md
- specs/05.03-字段注册与消费规范.md
- specs/21-WorkCase-工作项.md
- specs/20-Spark-火花.md
- specs/42-specs-audit-规范审核.md
archive_reason: null
---

# LDVH 知识图谱建设的最新实践与落地评估

## 研究问题

1. LDVH 是否已经具备可建设知识图谱的基础？
2. 结合 2025-2026 的行业实践，LDVH 应优先补齐哪些图谱化能力？
3. 建议如何与当前 40-43 审核链路与工作项闭环对齐？

## 输入与边界

本研究基于 2025-2026 的公开实践文章与 LDVH 当前事实源资产；时间点为 2026-06-20。

输入边界：
- 只覆盖 LDVH 项目对象层（WorkCase/Spark/ADR/Pitfall/Study/WorkCase）之间关系治理；
- 不直接评估外部图数据库选型的托管成本、运维资源或组织预算；
- 不替代 `docs/studies` 中临时资料，仅吸收可复用、可引用的结论。
- 图谱输出只能作为运行时投影和当次诊断结果；不得写入 `entities.json`、`edges.json`、`graph-metadata.json` 等派生文件，不得维护长期缓存。

## 关键发现

### 1) LDVH 基础条件已到位

LDVH 已具备知识图谱建设的输入条件：

- 结构化对象事实源（WorkCase/Spark/ADR/Pitfall/Study/WorkCase）；
- 标准化 ID 与跨对象关联字段；
- fact_cli 检索与 Git 提交追溯链路。

这意味着可以先在现有体系上做图谱化，不必先构建新资产。

### 2) 当前缺口在于“建模治理”而非“数据采集”

目前更缺少的不是“能否存图”，而是

- 关系语义标准化（`references/depends_on/blocked_by/triggers` 等）;
- 悬挂引用与变更一致性校验；
- 基于当前 code 与事实源即时生成的关系投影；
- 漂移告警机制；
- LLM 可直接消费的关系查询视图。

### 3) 近期实践对 LDVH 的对应启示明确

外部实践都在强调：

- 图谱优于纯向量用于多跳关系推理；
- 有现成图谱时优先接入图检索而非推倒式重建；
- 在稳定模型上建立显式约束，在演进部分保留扩展弹性。

与 LDVH 的匹配点是：先定义最小关系 schema，再以只读运行时投影提供查询和校验，把检查与触发闭环接到工作流程与 Human Gate。

## 建议

### 阶段 1（P1）：最小运行时图谱投影与校验闭环

- 构建统一对象抽取器：每次 CLI/API 调用时读取当前 `ldvh-base`、相关 specs/code 路径和 Git 工作区，返回内存中的 `nodes`、`edges`、`issues`。
- 增加关系一致性校验：缺失目标、重复边、非法边类型、反向关系不一致、路径漂移和时间戳缺失告警。
- 输出只允许进入 stdout、HTTP response 或当次审核报告正文；不得写入长期 JSON、SQLite、外部图数据库或 Web 本地缓存。
- Web API 应显式使用无缓存语义，例如返回 `Cache-Control: no-store`，前端不得用 localStorage/sessionStorage 保存图谱状态。

### 阶段 2（P1）：关系语义与查询入口

- 定义 LDVH 核心关系语义与最小字段映射；
- 提供查询：邻接、阻塞链、证据链、收敛链；
- 支持将关系问题映射到 WorkCase 审核与关闭前检查点。
- 查询入口应包含正向邻接、反向邻接、对象影响面、Spark 分流链、WorkCase 输入/证据链和已失效引用列表。

### 阶段 3（P2）：与 40-43 与提交链路打通

- 在工作对象变更/关闭前触发关系完整性检查；
- 对 40-43 输出加入图状态字段，作为可读可追溯的触发输入；
- 输出与提交记录的关联证据链。
- 所有图状态字段都应是当次检查结果的描述，不得成为新的手写维护字段或缓存事实源。

## 后续分流

- 将本 Study 的阶段化建议分流为 WorkCase，优先推进 `P1` 的运行时抽取器与校验器。
- 在 41/42/43 的可触发清单中补上“图谱关系一致性检查”作为明确触发条件。
- 形成一套可复用的关系视图查询模板（对象级依赖闭包、阻塞链、resolved 路径、证据链）。
- WorkCase 创建前应明确禁止缓存：验收标准必须包含“不落盘派生图谱文件、不引入长期缓存、不把外部图数据库作为事实源”的检查项。
