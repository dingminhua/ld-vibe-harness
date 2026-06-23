# LD Vibe Harness

让 Vibe Coding 更高效、更稳定、更可控

LD Vibe Harness 是面向 Vibe Coding 的工程化驾驭框架，由 LaoDing 基于实践沉淀而来。它用规范体系明确边界和价值判断，用事实模型承载稳定工作事实，用行动编排约束 AI 的读取、判断、执行、暂停和回写，用 Code 提供确定性解析、校验、聚合和反馈，用 Web 帮助 Human 看见状态、风险、证据和待确认事项，用运行时扩展接入不同 AI 协作环境的入口、规则、流程、Agent、Hook 和工具能力——让人的自然语言意图转化为可规划、可执行、可验证、可沉淀的 AI 工程闭环。

## 核心能力

| 构成要素 | 作用 |
|---|---|
| 规范体系 | 定义上位原则、边界、价值判断、身份契约和读取入口 |
| 事实模型 | 承载目标、工作项、决策、经验、研究和证据等稳定工作事实 |
| 行动编排 | 约束 AI 的上下文读取、工作规划、执行推进、验证关闭和风险暂停 |
| Code | 提供解析、索引、聚合、校验、诊断、测试和受控写入前检查 |
| Web | 面向 Human 展示状态、风险、证据、待确认事项和受控交互 |
| 运行时扩展 | 承接 Rules、Skills、Agents、Hooks 与环境适配，使 LDVH 能被看见、触发和执行 |

## 当前权威入口

当前 `specs/` 是 LDVH 的 active 正式规范事实源。`history/specs-v1/` 只作为历史追溯、迁移审计和价值提取输入，不再作为默认规范入口。

AI 维护 LDVH 产品资产时，先读取 `rules/LDVH-MAINTAINER-ENTRY.md`；处理管辖项目工作对象时，先读取 `rules/LDVH-WORKSPACE-ENTRY.md`。Code 默认以 `active_specs` 消费当前 `specs/`，`v2-check` 只是 active specs 诊断和只读知识地图预览入口，不替代规范原文、Human Gate 或完整测试。

## 闭环流转

```text
人的自然语言意图
→ 通过规范体系、事实模型、行动编排、Code、Web 和运行时扩展
→ 转化为可规划、可执行、可验证、可沉淀的 AI 工程闭环
```

## 依赖安装

Code 检查依赖 Python 3.9+ 和 `PyYAML`；测试依赖 `pytest`。依赖声明见 `pyproject.toml`。

```bash
python3 -m pip install -e '.[test]'
```

Web 依赖位于 `web/` 工作区：

```bash
npm --prefix web install
```

## Web 启动

LDVH Web 位于 `web/` 目录，用于查看和操作 LDVH 事实对象展示面板。

```bash
npm run web:restart
```

启动后访问：

- 前端：http://localhost:5173
- 后端：http://localhost:3001

如果端口被占用，使用项目自带脚本自动清理并重启：

```bash
npm run web:restart
```

Web 页面开发先阅读：

1. `web/docs/10-Web开发现状与设计语言基线.md`
2. `web/docs/01-全局设计约束.md`
3. 当前页面对应文档，例如 ObjectList、ObjectDetail 或 Changelog。

当前设计语言以提交、研究、决策、火花、经验五个已完善模块为基线。后续页面改造应优先复用它们的列表卡片、详情身份头部、正文节点、关联行、复制语义和右侧扩展阅读语言。

## 检查入口

仓库根目录提供统一工程入口；测试仍统一放在根级 `tests/` 下。

```bash
npm run check
npm run test:code
npm run test:web:api
npm run specs:check
python3 code/specs_validate.py v2-check --fail-on-diagnostics --format text
```

`npm run test:code` 是 Code 侧完整验证入口；`v2-check` 是 active specs 诊断和只读知识地图预览入口，不替代完整测试、Web 回归或 Human Gate。

如果 Code 工具在当前环境不可用，不能把工具输出缺失解释为规范通过；应回到 Git 文件事实源、对应 `specs/` 原文、Rules 入口和人工降级检查。

## 资料目录边界

`docs/studies/` 是 LDVH 自身项目的内部研究资料区，只用于临时承载方案分析、评估材料和吸收候选。

`docs/sources/` 是 LDVH 自身项目的外部信源资料区，只用于临时承载外部资料、引用副本、摘要和第三方参考。

这两个目录不承载正式规范依据。已被采纳的稳定结论应以 `specs/`、`ldvh-base/`、`code/`、`web/` 或对应权威事实源为准；未被采纳、不再需要或尚未吸收的资料不作为当前入口保留。

## 项目状态

当前处于 v0.x 早期开发阶段，随时可能变更，不承诺稳定。

## License

Copyright 2026 LaoDing. Licensed under the [Apache License 2.0](LICENSE).
