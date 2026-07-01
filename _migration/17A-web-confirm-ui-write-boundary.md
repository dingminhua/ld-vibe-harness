# 17A Web Confirm UI 与通用写入边界

文件状态：阶段 17 记录。本文只记录 Web Confirm UI、受控轻写入和通用写入的当前边界，不授权新增 Web 写入、Human Gate 自动完成、WorkCase 状态推进或外部环境 Hook。

## 读取依据

1. `specs/00-理念与构成.md`
2. `specs/01-保障与衔接.md`
3. `specs/02-AI行为规范.md`
4. `specs/08-Web信息同步规范.md`
5. `specs/09-测试与验证规范.md`
6. `web/api/routes/sparks.ts`
7. `tests/web/api/sparks.test.ts`
8. `web/docs/11-Web测试实现规范.md`

## 当前事实

当前 Web 已有的正式写入能力只有 Spark quick create：

1. 写入对象只限 Spark；
2. 写入位置只限 `ldvh-base/sparks/`；
3. 初始状态固定为 `pending`；
4. `source` 固定为 `web`；
5. 写入后重新读取 YAML 并验证必要字段；
6. API response 返回 `source_refs`；
7. `tests/web/api/sparks.test.ts` 覆盖创建、字段校验、文件冲突和写后校验失败。

当前 Web 没有启用以下能力：

1. 通用事实对象写入；
2. WorkCase 状态推进写入；
3. ADR、Pitfall、Study 的 Web 创建或状态改写；
4. 完整 Confirm UI；
5. Confirm UI 自动生成 Human Gate 完成记录；
6. Web 写入替代 AI 定性、验证声明或 Human 明示决定。

## 阶段判断

阶段 17 不直接实现通用写入。理由：

1. `08` 已把 Web 写入和 Confirm UI 变化列为 Human Gate 触发点；
2. `13A` 的 WorkCase 最小行动模板只授权 `manual_equivalent_execution`，并明确不启用 Web 写入或完整 Confirm UI；
3. 当前 Web API 写入白名单只覆盖 Spark quick create，且已有 tests/web API contract 保护；
4. 若在本阶段扩展为通用写入，会改变事实源回写能力、Human 可见状态和授权语义。

因此，阶段 17 的完成口径是记录边界、校正 Web 测试实现文档的上位规范引用，并确认现有 Spark 写入白名单仍可验证。

## 后置条件

后续若要启用完整 Confirm UI 或通用 Web 写入，至少需要先满足：

1. Human Gate 明确授权新增或扩大 Web 写入范围；
2. 在 Web 实现域中定义 Confirm UI 组件、页面或 API 的最小展示合同；
3. Confirm UI 至少呈现对象、影响范围、事实源或证据、验证状态、风险、替代方案、回写位置、失败处理、取消/后置路径和残余风险；
4. 每一种新增写入都必须有对象类型、字段白名单、状态闭集、回写位置、source_refs、写后校验和失败回滚口径；
5. tests/web 增加正例、负例、错误态、只读边界和写后验证测试；
6. Web 写入不得消费 Code 输出作为主数据源，不得把页面状态当作事实源；
7. Confirm UI 不得自动替代 Human Gate、验收通过、授权执行或风险接受。

## 结果

阶段 17A 完成后：

1. Web 继续保持同源独立读取；
2. Spark quick create 仍是唯一正式 Web 写入；
3. 通用 Web 写入继续后置；
4. 完整 Confirm UI 继续后置；
5. WorkCase 状态推进仍由 `06` 的最小手动行动模板和 `21` 的状态/证据边界承接；
6. 本阶段不改变 specs 正文、不新增 Web API、不新增事实对象类型、不安装 Hook。
