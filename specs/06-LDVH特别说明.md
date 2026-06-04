# LDVH 特别说明

> 创建日期：2026-06-04
> 定位：定义 LDVH 规范体系中的特别说明，补充 11 未覆盖的 Human Gate 豁免条件
> 适用范围：所有接入 LD Vibe Harness 且运行于 Trae 平台的项目
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/11-LDVH-Trae-Solo-环境规范.md`

---

---
## 1. 本文解决的问题

本文定义 LDVH 规范体系中需要特别声明的 Human Gate 豁免条件。11 定义了 Human Gate 的触发场景和设计规范，本文补充 11 未覆盖的豁免规则。

---

## 2. 与 00 总纲的关系

00 §5.3 定义人类确认闭环，11 定义通过 AskUserQuestion 实现 Human Gate 的技术路径。本文承接 00 和 11，明确特定操作不需要触发 Human Gate 的豁免条件。

---

## 3. Human Gate 豁免条件

删除 `.md`、`.yaml`、`.py` 文件时，不需要触发 Human Gate。

---

## 4. 机制落地关系

| 关联机制 | 关联实体 | 关系类型 | 触发条件 |
|---|---|---|---|
| Rules | `../.trae/rules/ldvh-l0-rules.md` | L0 工作区规则引用 | 本文的 Human Gate 豁免条件变化时 |

---

## 5. Human Gate 与检查要求

修改本文 Human Gate 豁免条件时，应评估 Human Gate 并同步更新 L0 工作区规则。

---

## 6. 待补齐事项

（无）
