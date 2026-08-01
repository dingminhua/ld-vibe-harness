---
name: ldvh
description: 项目待办/工作项/进展、技术决策/决策记录、踩坑经验、调研/研究报告、项目议题/火花、规范修订、受控提交、环境接入时使用——这些是 LDVH（LD Vibe Harness）管辖事项，对应事实对象 WorkCase、ADR、Pitfall、Study、Spark 的创建、更新与读取，或需要取得 LDVH 规则引导与行动模板时。本技能只负责把会话路由到 LDVH CLI；全部规则、模板与事实权威由 CLI 从当前规则源现取。
---

# LDVH 接入（薄路由）

LDVH 让长期项目"判断有据、行动可续、结果可验"。本文件不承载规则正文；固定能力边界只作路由提示。
权威只有一个：LDVH CLI 从当前规则源现取的结果。

## 职责（只有三件）

1. **身份**：当前项目可能受 LDVH 管辖。落入 LDVH 领域的事项（事实写入、规范
   修订、受控提交、环境接入）必须走 LDVH 流程，不得直写受管文件。

2. **规则引导**：会话开始、恢复或上下文压缩后继续时，取得当次规则引导：
   - 首选：运行 `ldvh-work-context`（规则引导入口）。它不是 Helper 操作，
     `ldvh capabilities` 不提供其调用信封；调用前先经
     `ldvh call read-specification-content` 精确读取环境接入面附件
     （`environment-integration-surface`）的 `work-context-core` 行当次内容，
     按该契约构造调用，不猜事件形状与参数；
   - 其不可用或返回 `unavailable` 时：用 `ldvh call read-specification-content`
     精确读取根规范 `ldvh-root` 的 §8.1 与 §8.2，并如实报告使用了降级路径。
   该引导只交付规则，不恢复项目事实（facts 恒为 `not_requested`）。

3. **行动模板**：动手落入 LDVH 领域前，先
   `ldvh call read-action-template-candidates` 定位，再
   `ldvh call read-action-template-content` 读取当次适用模板，照模板执行。
   不得凭记忆或本文件假设模板清单与内容。

## 能力边界（非职责）

下列三句只作能力边界路由提示，不增加第四项职责，不代替 CLI 当次现取的权威来源与实际验证：

薄 Skill 对事实写入的保护仅为劝告级：它只能将 AI 路由到 Helper 与行动模板，不能在模型之外机械阻断对 `ldvh-base/` 的直写。

Git Gate 的每一安装实例只覆盖一个实际 Git worktree 中真正触发该 Gate 的 Git 事件；其它 worktree、clone，以及未触发或绕过该 Gate 的行动不在其覆盖范围。

机械检查能够发现来源已定义的机械不合格，不能据此判断事实内容的语义真实性；即使 Schema 合法，语义污染风险仍然存在，未提交污染窗口只能压缩、不能消除。

## 禁止

- 不复制规则正文、规范章节、模板正文或事实 Schema 到本文件或会话产物；
- 不写死模板清单、Helper 操作清单、信封字段、参数或机器绝对路径——一律现取；
- 不断言任何环境的自动加载、触发或递达状态；
- 不把 `partial`、`unavailable`、未验证写成成功、生效或已保障。

## CLI 定位与调用

以入口名调用：`ldvh`、`ldvh-work-context`、`ldvh-doctor`。
入口不在 PATH 时，使用发行环境（如项目 `.venv/bin/`）下的同名入口；仍不可得
时如实交还"CLI 不可定位"，不猜路径。`ldvh` 的 Helper 操作信封与参数以
`ldvh capabilities` 及 Helper 服务规范（04）的当次内容为准；
`ldvh-work-context`、`ldvh-doctor` 等独立入口的信封不经 capabilities
提供，以环境接入面附件（`environment-integration-surface`）对应入口行的
当次内容为准。

需要 `governed_project_id` 时，从当前目录向其父目录逐级向上查找
`LDVH-GOVERNED-PROJECTS.yaml`（管辖配置）读取项目 `id`；不得用目录名或仓库名
猜测。操作参数不确定时，先以
最小请求试调一次并读响应 `gaps`/`diagnostics` 中的契约问题，或经
`ldvh call read-specification-content` 精确读取 04 及其授权附件的字段表；
不得反复盲猜参数。

## 如实报告

区分并报告：**已验证**（当次实际跑通并有输出）、**未验证**（需要真实会话或
真实事件才能证明的，如自动加载）、**不支持**（权威资料或范围匹配观察肯定证明
无此能力）。不要把"文件存在""技能已启用"或"shell 直调成功"写成"已接入"。
