# LDVH specs-v2 candidate area

```yaml
v2_candidate_area:
  status: candidate_non_authoritative
  canonical_path: specs-v2/README.md
  active_fact_source: specs/
  purpose: "承载 LDVH specs v2 的计划、候选结构、知识地图结构构件和逐篇迁移占位"
  prohibition:
    - "不得把本文或 specs-v2 下任何文件解释为 active 正式规范"
    - "不得从 specs-v2 直接替代 specs/、ldvh-base/、Git commit records 或管辖项目配置"
    - "不得在未经过逐篇 Human 核对前迁入正式规范正文"
```

## 1. 定位

`specs-v2/` 是 LDVH 规范体系重构的候选区。当前唯一 active 正式规范事实源仍是 `specs/`。

本目录只用于：

1. 保存 v2 计划；
2. 固化候选文件结构；
3. 设计知识地图结构构件；
4. 记录 v1 到 v2 的迁移覆盖关系；
5. 承载 v1 机制理解门禁；
6. 承载待逐篇核对的占位文件。

## 2. 使用规则

AI 读取本目录时，应先读取 `PLAN.md`。任何 v2 文件在未经过 Human 单篇核对、迁入、校验和切换前，都只能作为候选材料。

涉及执行、修改 active 规范、处理事实对象、判断事实源或执行行动编排时，仍必须回到 `specs/`、`ldvh-base/`、Git commit records 和对应 active 入口。

## 3. 当前内容

| 路径 | 用途 | 状态 |
|---|---|---|
| `PLAN.md` | v2 目标、原则、阶段和实施边界 | candidate |
| `V1-UNDERSTANDING-GATE.md` | v1 机制性契约理解门禁 | candidate_gate |
| `MIGRATION-MAP.md` | v1 到 v2 的迁移覆盖清单 | empty_stub |
| `00-11` 候选主干 | 候选主规范结构；00 已形成确认基线，其余仍需逐篇核对 | candidate / candidate_notes / empty_stub |
| `{父编号}.Att.{两位序号}-{名称}.md` | 根目录平铺附件、注册表、矩阵和知识地图结构构件候选 | candidate / empty_stub |
| `20-29-事实模型/` | 具体事实模型迁移候选区 | empty_stub |
| `30-59-行动编排/` | 具体行动编排迁移候选区 | empty_stub |
