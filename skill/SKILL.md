---
name: ldvh
description: 当工作涉及 LDVH（LD Vibe Harness）管辖项目时使用——包括创建、更新或读取事实对象（Spark、WorkCase、ADR、Pitfall、Study），修订规范，执行受控提交，环境接入与验证，或需要取得 LDVH 规则引导与行动模板时。本技能只负责把会话路由到 LDVH CLI；全部规则、模板与事实权威由 CLI 从当前规则源现取。
---

# LDVH 接入（薄路由）

LDVH 让长期项目"判断有据、行动可续、结果可验"。本文件不含规则内容。
权威只有一个：LDVH CLI 从当前规则源现取的结果。

## 职责（只有三件）

1. **身份**：当前项目可能受 LDVH 管辖。落入 LDVH 领域的事项（事实写入、规范
   修订、受控提交、环境接入）必须走 LDVH 流程，不得直写受管文件。

2. **规则引导**：会话开始、恢复或上下文压缩后继续时，取得当次规则引导：
   - 首选：运行 `ldvh-work-context`（规则引导入口）；
   - 其不可用或返回 `unavailable` 时：用 `ldvh call read-specification-content`
     精确读取根规范 `ldvh-root` 的 §8.1 与 §8.2，并如实报告使用了降级路径。
   该引导只交付规则，不恢复项目事实（facts 恒为 `not_requested`）。

3. **行动模板**：动手落入 LDVH 领域前，先
   `ldvh call read-action-template-candidates` 定位，再
   `ldvh call read-action-template-content` 读取当次适用模板，照模板执行。
   不得凭记忆或本文件假设模板清单与内容。

## 禁止

- 不复制规则正文、规范章节、模板正文或事实 Schema 到本文件或会话产物；
- 不写死模板清单、Helper 操作清单、信封字段、参数或机器绝对路径——一律现取；
- 不断言任何环境的自动加载、触发或递达状态；
- 不把 `partial`、`unavailable`、未验证写成成功、生效或已保障。

## CLI 定位与调用

以入口名调用：`ldvh`、`ldvh-work-context`、`ldvh-doctor`。
入口不在 PATH 时，使用发行环境（如项目 `.venv/bin/`）下的同名入口；仍不可得
时如实交还"CLI 不可定位"，不猜路径。调用信封与参数以 `ldvh capabilities`
及 Helper 服务规范（04）的当次内容为准。

## 如实报告

区分并报告：**已验证**（当次实际跑通并有输出）、**未验证**（需要真实会话或
真实事件才能证明的，如自动加载）、**不支持**（权威资料或范围匹配观察肯定证明
无此能力）。不要把"文件存在""技能已启用"或"shell 直调成功"写成"已接入"。
