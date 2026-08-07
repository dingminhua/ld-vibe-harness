# WorkCase 投影规范到 Python 的精确漂移合同

## 覆盖与起点

本规划覆盖 `workcase-0046` 批准的测试侧增量：以当前
`specs/21-WorkCase-工作项.md` §9.3 的非 blocked 六列表为唯一语义输入，验证其
Markdown 载体语法和值映射与
`code/ldvh/facts/workcase_presentation.py` 的 `PHASE_PRESENTATION`、
`CLOSED_PRESENTATION` 精确一致。

实现起点为 commit `2d5a38c54609ac0827719453e5a8e5b9759dd68a`。closed
`workcase-0045` 曾把空值输入错误冻结为裸 `null`，因此没有交付测试；本增量以
§9.3 当前真实的 inline-code `` `null` `` 重新建立合同。既有 `spark-0040`、
未跟踪 `workcase-0036` 至 `workcase-0039`、聚焦页和截图属于其它工作，不得修改、
暂存或提交。

## 实现目标与明确排除

本增量只交付：

- 在测试侧唯一定位 §9.3 的非 blocked 基表；
- 严格检查六列表头、分隔行、7 个 open 行、1 个 closed 行和 inline-code 语法；
- 把表格解析结果直接与 Python 两个公开常量全等比较；
- 通过基于实际表文本的 mutation 负测证明结构和取值漂移会失败。

明确排除：

- 不修改 Specs、production Python、Helper、Schema、Web、生成器或 generated
  TypeScript；
- 不在运行时读取 Markdown；
- 不重建 blocked overlay、Gate 2 禁语、unresolved、phase transition 或第二张
  phase 映射；
- 不把测试通过解释为领域语义天然正确或 AI 将来一定遵从。

## 模块责任

### `code/tests/specs/test_workcase_presentation_source_contract.py`

唯一新增测试文件。它只在测试进程内：

1. 读取当前 §9.3 源文本并定位唯一 H3；
2. 从 H3 范围内定位唯一精确表头和连续 Markdown 表；
3. 校验表头、分隔行、行数、行顺序和单元格语法；
4. 将 inline-code 定界符去除，仅允许 `progress_step` 的 token `null` 转为
   Python `None`；
5. 直接比较解析所得 open/closed 映射与 Python 常量；
6. 对从当前规范抽取的表文本实施 mutation，并断言同一解析/比较入口拒绝。

测试 helper 不进入 production，不由其它模块导入。mutation 不维护一份手写的期望
phase 表；期望 phase 顺序和值来自 Python 常量与实际抽取结果之间的直接比较。

### 既有运行时与生成链

`workcase_presentation.py` 继续是唯一运行时维护点，不因本增量暴露新接口。
`code/tests/facts/test_workcase_presentation.py` 的
`test_generated_web_contract_matches_python_renderer` 继续证明 Python renderer 到
generated TypeScript 的字节一致性；本增量不修改该链。

## 严格解析合同

源表必须满足：

- H3 标题精确为 `### 9.3 当前快照确定性呈现投影` 且只出现一次；
- 表头精确为当前六列，分隔行精确为六个 `---`；
- 数据行恰为 8 行，并与 Python 常量的 7 个 phase 插入顺序及 closed 行一致；
- open 首列精确为 inline-code `open`、分隔文本 `/`、inline-code phase token；
- closed 首列精确为 inline-code `closed`、分隔文本 `/`、普通文本 `phase 省略`；
- 其余五列各自只能包含一个 inline-code token；
- `null` 只允许出现在 `progress_step`，且源文本必须是 inline-code `` `null` ``；
- 未知 token、裸 `null`、缺/增/重复/乱序行、列序变化和任一映射值漂移都失败。

## 依赖与调用方向

允许方向固定为：

```text
specs/21 §9.3 当前表
  -> 测试侧严格抽取与规范化
       -> 与 PHASE_PRESENTATION / CLOSED_PRESENTATION 直接全等比较

Python renderer
  -> 既有 generated TypeScript 字节一致性测试
```

禁止 production 导入测试 parser、测试生成 Python 常量、Python 反向改写 Specs，或
mutation 通过手写第二张期望映射判断结果。

## 失败与诊断

- H3、表头或表范围不唯一：报告定位或结构错误，不猜测另一张表；
- 单元格格式错误：报告具体行列及所需 inline-code 形状；
- `null` 位置或载体错误：区分裸 token、非 `progress_step` 位置和合法 `None` 转换；
- 映射不同：报告规范解析结果与 Python 常量差异；
- 测试需要 production/Specs/Web 变化才能成立：停止该实现，不扩大白名单。

## 风险与验证映射

| 风险 | 检查 |
|---|---|
| 再次把裸 `null` 当成权威输入 | 正向断言 inline-code `` `null` ``，mutation 把它改成裸 `null` 并要求失败 |
| 测试自身成为第二张 phase 表 | 期望值只由实际表解析结果与 Python 常量直接全等比较；人工 diff 审查 |
| 表的缺行、增行、重复或乱序静默通过 | 结构 mutation 负矩阵 |
| 表头、列序或首列语法漂移 | 精确表头、分隔行和 status/phase parser 负测 |
| 未知 token 或值漂移 | inline-code token 校验及 Python 全等比较 mutation |
| 重复实现 blocked/Gate 2/unresolved | 路径白名单和新测试源码审查；复用既有 presentation/controller tests |
| Python/TypeScript 漂移 | 既有 `test_generated_web_contract_matches_python_renderer` |
| 混入其它 dirty | Index、name-status、受保护路径哈希和提交范围回读 |

目标验证包括新 source-contract test、既有 WorkCase presentation 与 Controller
continuation tests、`git diff --check`、路径白名单、WorkCase 精确回读、全库事实
完整性和独立只读结果复核。失败只撤回本案两个计划文件和唯一新测试文件，不触碰
其它 Working Tree 内容。
