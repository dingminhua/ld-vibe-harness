---
id: study-0007
type: study
title: Web 颜色体系治理专项（规范10）
status: active
created: '2026-06-20T14:10:00+08:00'
updated: '2026-06-20T14:10:00+08:00'
user_intent: |
  在不影响 Web 第一阶段功能交付前提下，建立颜色使用的分阶段治理方案，
  并明确规范10约束与执行顺序，使颜色语义可追溯、可审计。
summary: |
  将颜色问题收束为四个 study：阶段一冻结、阶段二语义审计、阶段三硬编码清单收敛、阶段四 token 健康回归。
  第一阶段仅记录偏差，不做大改；第二阶段起专项处理。
conclusion: |
  建议按“严格语义 + 分阶段”实施。
  先维持现状功能交付，待第一阶段结束后执行统一清理与映射收口。
  通过单点映射与 token 健康检查，避免颜色语义在组件层扩散。
related_memos:
  - memo-0018
related_workareas: []
related_workplans: []
related_adrs: []
related_pitfalls: []
related_docs:
  - web/docs/01-全局设计约束.md
  - web/docs/11-Web测试实现规范.md
archive_reason:

# 研究内容

## 阶段划分

### 1）阶段一：第一阶段执行冻结（done）
- 目的：保证 Web 第一阶段功能交付不受颜色重构打断。
- 范围：
  - 继续功能推进。
  - 不做大规模颜色迁移。
  - 不在组件层新增硬编码业务语义颜色。
- 验收：第一阶段交付完成且不引入额外颜色语义风险。

### 2）阶段二：语义审计与统一（pending）
- 目的：核对分类、生命周期、流程、信号语义边界。
- 范围：
  - category 映射。
  - status 生命周期语义映射。
  - executionFlow 八态映射。
  - signals 优先级/重要性语义映射。
- 验收：新增颜色不在组件层新增业务语义类。

### 3）阶段三：硬编码与例外清单收敛（pending）
- 目的：清理非主题颜色，建立受控例外机制。
- 范围：
  - 汇总现有 bg-white / text-white / 特殊色示例。
  - 建立例外清单：用途、范围、审批理由、复检日期。
  - 逐步替换为 token 或语义映射。
- 验收：新增提交无裸色值语义新增。

### 4）阶段四：token 健康与质量门（pending）
- 目的：修复 token 健康问题并接入回归门。
- 范围：
  - 处理悬空 token（例如 text-tertiary）。
  - light/dark 一致性与可读性回归检查。
  - 建立 PR 颜色审查规则。
- 验收：无悬空 token，语义映射一致通过。

## 规范10（执行条款）

1. 任何新增颜色只能来源于 ldvh 主题 token 或已存在语义映射 key。
2. 禁止新增裸露十六进制色值（#RRGGBB）。
3. 禁止新增 tailwind 语义色类直接表达业务语义。
4. 同一语义必须单点定义。
5. 分类色仅来自 category 映射。
6. 生命周期状态色仅来自 status 映射。
7. 流程态颜色仅来自 executionFlow 映射。
8. signals/优先级/重要性颜色仅来自 signal 映射。
9. 禁止悬空 token 使用。
10. 所有受控例外必须有理由、最小影响范围与复检时间。
