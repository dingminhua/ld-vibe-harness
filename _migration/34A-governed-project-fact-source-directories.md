# 34A 管辖项目事实源目录用途补强

文件状态：migration evidence。本文记录 V3 对管辖项目首次配置中 `ldvh-base/` 事实源目录用途的补强；它不创建目录，不修改管辖项目配置，不安装 Hook，也不声明任何环境入口已 integrated。

## 背景

Human 指出：被管辖项目需要创建 `ldvh-base/`，并且 AI 必须向用户说明这些目录做什么用。复核 V2 后确认该要求成立：

1. V2 事实模型基础规范说明事实实例承载于 `ldvh-base/`；
2. V2 事实归属矩阵把 WorkCase、ADR、Pitfall、Spark 和 Study 实例归到 `ldvh-base/`；
3. V2 Code 的 fact CLI / validator 使用 `ldvh-base/workcases/`、`ldvh-base/adrs/`、`ldvh-base/pitfalls/`、`ldvh-base/sparks/` 和 `ldvh-base/studies/`；
4. V2 曾有项目临时材料候选口径；V3 不保留对应目录概念，不把它写成管辖项目初始化目录。

## 本阶段处理

本阶段同步：

1. `specs/10-管辖项目配置规范.md`：补充管辖项目 `ldvh-base/` 五个子目录的用途、不得替代边界、Human Gate 和验证要求；
2. `specs/30-LDVH安装初始化管辖项目配置行动模板.md`：把事实源目录用途纳入用户告知清单、Context、Gate、执行、验证、回写和交还；
3. `code/ldvh_specs.py`：让 specs validator 消费 `ldvh-base/` 五个子目录和用途说明，防止后续再次漏写；
4. `specs/attachments/03.Att.01-Commit-Message契约字段表.md` 与 `specs/24-Study-研究报告.md`：取消旧项目材料目录 scope 和 Study 临时材料边界口径；
5. `reviews/formal/03.Att.01-formal-review.yaml`、`reviews/formal/10-formal-review.yaml`、`reviews/formal/24-formal-review.yaml` 与 `reviews/formal/30-formal-review.yaml`：同步 hash 和验证记录。

## 目录用途

| 目录 | 用途 | 边界 |
|---|---|---|
| `ldvh-base/workcases/` | WorkCase 工作项实例 | 不替代行动模板或 Human Gate |
| `ldvh-base/adrs/` | ADR 决策实例 | 不替代 specs 正文或未确认讨论 |
| `ldvh-base/pitfalls/` | Pitfall 踩坑经验实例 | 不替代未解决问题或测试失败缓存 |
| `ldvh-base/sparks/` | Spark 火花实例 | 不替代 WorkCase、ADR、Study 或聊天上下文 |
| `ldvh-base/studies/` | Study 稳定研究报告实例 | 不替代临时调研材料、研究过程或外部原文 |

## 边界

本阶段不做：

1. 不创建或修改任何真实管辖项目目录；
2. 不创建或修改 `LDVH-GOVERNED-PROJECTS.yaml`；
3. 不创建事实对象实例；
4. 不安装、升级、禁用或卸载任何 Hook、插件或环境入口；
5. 不声明 Web 写入、环境入口或管辖项目事实源已经完整启用。

## 验证

本阶段使用 targeted validation：

```bash
python3 code/specs_validate.py all --format text --fail-on-diagnostics
python3 -m pytest tests/code/test_formal_specs.py -q
git diff --check
```

这些验证只证明 specs 边界和 formal review hash gate 成立，不证明任何真实管辖项目目录已经创建。
