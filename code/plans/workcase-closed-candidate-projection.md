# WorkCase 关闭候选只读投影实现规划

## 1. 目标与权威边界

本规划承接 `workcase-0047`。`specs/21-WorkCase-工作项.md` 继续唯一负责 WorkCase closed 白名单、proposal 到 terminal 的精确映射、Human Gate 与关闭事务语义；Code 只把该确定性映射实现为一份纯投影，并由关闭校验和只读 Helper 操作共同消费。规划、实现、测试和机械校验目录均不得成为第二规则源。

`prepare-closed-workcase-candidate` 只读取当前 Working Tree 中一个完整、mechanically valid 且 `phase=human_closure_confirming` 的 WorkCase，返回当次 source fingerprint、排除托管身份与时间字段的完整 closed `fact_object` 候选，以及 proposal 已保存的 route target 三元组与 fingerprint 映射基础。结果不表示 Human 已批准、目标仍有效、关闭技术前提已满足或工作已完成。

## 2. 模块责任与依赖

依赖保持单向：21 规则合同 → `facts.workcase_update` 纯投影 → 关闭校验与 Helper adapter → service/CLI。事实层不得导入 Helper。

| 模块 | 责任 | 明确不负责 |
|---|---|---|
| `facts.workcase_update` | 从完整 Gate2 before 确定性形成非托管 closed 候选；关闭映射校验消费同一投影 | 管辖解析、授权判断、目标读取、CAS、写入 |
| `workcase_close_candidate_request` | 解析单一 WorkCase 稳定引用、可选 workspace root 与 locator，并拒绝共同请求越界字段 | 读取事实、生成候选 |
| `workcase_close_candidate_operation` | 解析管辖边界，只读取 source WorkCase，检查候选资格，返回候选与 proposal 已保存的映射基础 | 读取 route targets、入向依赖、决定关闭或写入任何载体 |
| `workcase_update` 关闭事务 | 继续执行 source 重读、fingerprint CAS、route target 重读与指纹比较、入向依赖、关系图、原子替换和回读 | 复制造候选映射 |

## 3. 投影合同

纯投影输入是已经满足当前 WorkCase snapshot 合同、含完整 `closure_proposal` 的 `human_closure_confirming` before。输出排除 `object_id`、`fact_type_key`、`created_at`、`updated_at`，并完整包含：`status=closed`；逐值保留的 title、goal、scope、成功标准定义/结果、result summary、validation summary 与条件 urls；proposal 映射的 closure outcome、disposition、accepted-stop residuals、spark suggestions 和去重 routed-to；以及 before 原样保留的 contributed-to、has-file-asset、related-to。

条件数组没有成员时省略。proposal route targets 按稳定三元组排序去重；before 的保留关系按解析值复制。投影不携带 proposal target fingerprint，因为 fingerprint 只是只读操作结果中的 mapping basis 和真实关闭事务的再校验输入，不属于 closed fact object。

关闭校验继续保留数组无语义顺序的既有边界：residual 按 `residual_id` 比较，关系按稳定身份集合比较；但期望值必须来自同一纯投影，不再另写一套 proposal 映射。

## 4. Helper 请求、结果与失败

领域参数只允许 `fact_ref` 与可选 `workspace_root`；`fact_ref.fact_type_key` 固定为 `workcase`。共同 `observed_context`、`authorization_reference` 与 `requested_disclosure` 必须为空。操作 effect 固定为 `read`。

成功结果返回 `actual_ref`、`canonical_path`、`carrier`、`source_content_fingerprint`、`fact_object` 和 `mapping_basis.proposal_route_targets[]`。每项 mapping basis 只复制 proposal 中当时保存的 `target` 与 `content_fingerprint`；不读取目标，不报告其当前状态。source fingerprint 变化后，旧候选不能作为真实 close 的 CAS 输入，调用方必须重新读取并重新形成候选。

管辖或读取技术边界无法形成时返回 `unavailable`；source 缺失、无效、blocked、closed、非 Gate2 phase 或 proposal 不完整时返回 `rejected`，全部零写入。响应不得生成关闭叙述、授权结论、Gate2 决定或“已准备好关闭”。

## 5. 验证

测试覆盖纯投影的完整字段映射、条件字段省略、route 去重、保留关系和关闭校验同源；请求字段闭集；只读操作成功、错误 phase/status、invalid/unavailable、source fingerprint 绑定、不读取 target、旧 fingerprint 失效语义；公开操作发现、service/CLI、发行快照和机械校验目录一致性。

聚焦测试通过后运行 Ruff 与 full-v4。实现不得修改 Web、Schema、00/04/05、行动模板、其它事实对象或未获授权路径，不 push 或创建 PR。
