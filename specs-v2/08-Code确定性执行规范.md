# Code确定性执行规范

```yaml
v2_candidate_doc:
  doc_id: "08"
  status: candidate_notes
  authority: none_until_human_approved
  planned_domain: "Code 只读解析、校验、知识地图、受控写入边界"
  source_candidate: "specs/07-Code确定性执行实现规范.md"
```

> 候选状态：本文是 v2 候选记录文件，不承载正式规范正文。正式 Code 规则仍以 v1 `07` 和 active Code 实现为准。

## 1. 定位

v2 第一阶段只建设 Code v2 的只读解析、迁移覆盖诊断和知识地图投影能力，不做受控写入。

Code v2 不应试图一次替换 v1 Code。它应先提供兼容、诊断和投影层。

## 2. 兼容底线

Code v2 至少应保留或提供迁移映射：

1. v1 `ldvh_doc` 元信息；
2. v1 `ldvh_member` 成员自描述；
3. v1 `规范保障要求`、`Human Gate 与检查要求`、`待补齐事项` 等章节锚点；
4. v1 字段注册表列名和枚举；
5. v1 事实模型对象类型、目录、状态、字段和 DTO；
6. v1 workflow member、`assurance_takeover`、`capability_assets`；
7. v1 Web Spark 创建白名单和 WorkCase orchestration 展示字段；
8. v1 测试命令和回归测试入口。

## 3. 知识地图输出边界

知识地图输出应是运行时只读投影，包括 nodes、edges、diagnostics 和 source refs。

Code v2 不得：

1. 落盘知识地图缓存；
2. 把派生图谱输出写成事实源；
3. 用知识地图反向维护管辖项目配置；
4. 默认接管用户 docs；
5. 省略 project namespace 生成跨项目裸节点 ID。

## 4. 待核对事项

1. v2 Code 命令入口；
2. 知识地图 nodes / edges / diagnostics 输出边界；
3. v1-v2 迁移覆盖检查；
4. 不落盘缓存和不替代事实源的规则；
5. v1 Code/Web/Test 契约的兼容策略。
