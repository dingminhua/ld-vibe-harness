# LD Vibe Harness

让 Vibe Coding 更高效、更稳定、更可控

LD Vibe Harness 是面向 Vibe Coding 的工程化驾驭框架，由 LaoDing 基于 Trae Solo 开发实践。它以约束体系划定边界，以事实源沉淀记忆，以工具链连接能力，以工作流驱动执行，以任务治理守住交付，以可视化工具桥接信息——让人的自然语言意图通过规则、事实源、工具链和工作流，转化为可规划、可执行、可验证、可沉淀的 AI 工程闭环，让 Vibe Coding 更高效、更稳定、更可控。

## 核心能力

| 能力 | 作用 |
|---|---|
| 约束体系 | 划定边界：规则、规范、安全红线 |
| 事实源 | 沉淀记忆：Git 文件事实源，不依赖模型记忆 |
| 工具链 | 连接能力：文件读写、Shell、Git、浏览器、API |
| 工作流 | 驱动执行：Skill、任务拆分、执行循环、验证闭环 |
| 工作计划治理 | 守住交付：WorkPlan 状态机、Review Gate、Human Gate |
| 可视化工具 | 桥接信息：AI 优先的结构化信息，人可读可操作 |

## 闭环流转

```text
人的自然语言意图
→ 通过规则、事实源、工具链和工作流
→ 转化为可规划、可执行、可验证、可沉淀的 AI 工程闭环
```

## Web 启动

LDVH Web 位于 `web/` 目录，用于查看和操作 LDVH 事实对象展示面板。

```bash
npm --prefix web install
npm run web:restart
```

启动后访问：

- 前端：http://localhost:5173
- 后端：http://localhost:3001

如果端口被占用，使用项目自带脚本自动清理并重启：

```bash
npm run web:restart
```

## 检查入口

仓库根目录提供统一工程入口；测试仍统一放在根级 `tests/` 下。

```bash
npm run check
npm run test:web:api
npm run specs:check
```

## 项目状态

当前处于 v0.x 早期开发阶段，随时可能变更，不承诺稳定。

## License

Copyright 2026 LaoDing. Licensed under the [Apache License 2.0](LICENSE).
