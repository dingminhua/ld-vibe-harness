# LDVH 生产对象实例编辑规则

> 层级：L2 场景规则
> 适用项目：ld-vibe-harness
> 生效方式：globs — 编辑 ldvh-base/ 下 YAML 文件时生效

## 字段契约

编辑生产对象实例时，字段必须符合对应对象规范定义的字段契约。依据 `specs/13-LDVH生产对象基础规范.md` §6.3。

## 状态机

状态流转必须合法。终态不可重开，如需重新处理必须新建对象。依据 `specs/13-LDVH生产对象基础规范.md` §6.2。

## 状态变更先于执行

执行对象相关操作时，必须先更新事实源中的对象状态，再执行操作。依据 `specs/13-LDVH生产对象基础规范.md` §6.2。

## Human Gate

创建、更新或删除关键对象实例时，应评估是否需要触发 Human Gate。依据 `specs/13-LDVH生产对象基础规范.md` §8.1。

## 引用完整性

引用其他对象的字段应确保引用的对象存在且有效。依据 `specs/13-LDVH生产对象基础规范.md` §6.3。

## ADR 约束

编辑 `ldvh-base/adrs/` 下 YAML 文件时：

1. 应检查 ADR 准入条件，判断是否满足创建 ADR 的条件（依据 `specs/21-ADR-决策记录.md` §3.3）；
2. ADR 状态流转必须合法，终态不可重开（依据 `specs/21-ADR-决策记录.md` §5.2）；
3. `proposed → accepted`、`accepted → deprecated`、`accepted → superseded` 必须触发 Human Gate（依据 `specs/21-ADR-决策记录.md` §7.1）；
4. 不得将 `proposed` 状态 ADR 作为执行依据。
