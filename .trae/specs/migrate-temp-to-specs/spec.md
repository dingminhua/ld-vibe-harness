# temp 目录文档迁入 specs 规范 Spec

## Why

`temp/` 目录下有 20 份 LDVH 规范文档（核心基础规范 10 份、生产对象规范 2 份、行动模型规范 8 份），使用的是旧编号体系（03-07、10-11、40-41），需要按 `specs/01-LDVH目录说明.md` 定义的编号分区重新编号后迁入 `specs/`，同时更新所有内部交叉引用、现有 specs 文档中的"规划中"标记和 L0/L1 规则文件中的引用。

## What Changes

- 将 20 份 temp 文档按编号映射重命名后移入 `specs/`
- 更新迁移文档内部所有旧编号引用为新编号
- 更新现有 specs 文档（00、01、02、03）中"规划中的"标记
- 更新 L0 工作区规则和 L1 项目规则中的旧编号引用
- 删除 `temp/` 目录

## Impact

- Affected specs: 00 总纲、01 目录说明、02 术语规范、03 文档规范、L0 工作区规则、L1 项目规则
- Affected code: `.trae/rules/ldvh-l0-rules.md`、`.trae/rules/ldvh-l1-rules.md`

## ADDED Requirements

### Requirement: 文件编号重命名与迁移

系统 SHALL 将 temp 目录下 20 份文档按以下映射重命名并移入 specs/：

| temp 文件 | specs 文件 |
|---|---|
| `03-事实源边界与承载规范.md` | `10-事实源边界与承载规范.md` |
| `04-LDVH-AI协作规范.md` | `11-LDVH-AI协作规范.md` |
| `04.01-Rules机制规范.md` | `11.01-Rules机制规范.md` |
| `04.02-Skill机制规范.md` | `11.02-Skill机制规范.md` |
| `04.03-Agent机制规范.md` | `11.03-Agent机制规范.md` |
| `05-LDVH工具基础规范.md` | `12-LDVH工具基础规范.md` |
| `05.01-Tools辅助规范.md` | `12.01-Tools辅助规范.md` |
| `05.02-Web展示规范.md` | `12.02-Web展示规范.md` |
| `06-LDVH生产对象基础规范.md` | `13-LDVH生产对象基础规范.md` |
| `07-LDVH行动模型基础规范.md` | `14-LDVH行动模型基础规范.md` |
| `10-生产对象集合索引.md` | `20-生产对象集合索引.md` |
| `11-ADR-决策记录.md` | `21-ADR-决策记录.md` |
| `40-行动模型集合索引.md` | `50-行动模型集合索引.md` |
| `41-multi-role-thinking-多角色思考.md` | `51-multi-role-thinking-多角色思考.md` |
| `41.01-Rules.md` | `51.01-Rules.md` |
| `41.02-Skill.md` | `51.02-Skill.md` |
| `41.03-Agent.md` | `51.03-Agent.md` |
| `41.04-Tools.md` | `51.04-Tools.md` |
| `41.05-Web.md` | `51.05-Web.md` |
| `41.06-Contract.md` | `51.06-Contract.md` |

#### Scenario: 文件迁移成功

- **WHEN** 所有 20 份文档按映射表重命名并移入 specs/
- **THEN** specs/ 目录包含 00-03 基础规范 + 10-14 核心基础规范 + 20-21 生产对象规范 + 50-51 行动模型规范

### Requirement: 迁移文档内部引用更新

系统 SHALL 更新迁移文档中所有旧编号引用。引用替换规则如下：

**文件路径引用替换：**

| 旧引用 | 新引用 |
|---|---|
| `specs/01-specs文档结构与术语规范.md` | `specs/03-Specs文档规范.md` |
| `specs/02-LDVH目录说明.md` | `specs/01-LDVH目录说明.md` |
| `specs/03-事实源边界与承载规范.md` | `specs/10-事实源边界与承载规范.md` |
| `specs/04-LDVH-AI协作规范.md` | `specs/11-LDVH-AI协作规范.md` |
| `specs/04.01-Rules机制规范.md` | `specs/11.01-Rules机制规范.md` |
| `specs/04.02-Skill机制规范.md` | `specs/11.02-Skill机制规范.md` |
| `specs/04.03-Agent机制规范.md` | `specs/11.03-Agent机制规范.md` |
| `specs/05-LDVH工具基础规范.md` | `specs/12-LDVH工具基础规范.md` |
| `specs/05.01-Tools辅助规范.md` | `specs/12.01-Tools辅助规范.md` |
| `specs/05.02-Web展示规范.md` | `specs/12.02-Web展示规范.md` |
| `specs/06-LDVH生产对象基础规范.md` | `specs/13-LDVH生产对象基础规范.md` |
| `specs/07-LDVH行动模型基础规范.md` | `specs/14-LDVH行动模型基础规范.md` |
| `specs/10-生产对象集合索引.md` | `specs/20-生产对象集合索引.md` |
| `specs/11-ADR-决策记录.md` | `specs/21-ADR-决策记录.md` |
| `specs/40-行动模型集合索引.md` | `specs/50-行动模型集合索引.md` |
| `specs/41-multi-role-thinking-多角色思考.md` | `specs/51-multi-role-thinking-多角色思考.md` |
| `specs/41.01-Rules.md` | `specs/51.01-Rules.md` |
| `specs/41.02-Skill.md` | `specs/51.02-Skill.md` |
| `specs/41.03-Agent.md` | `specs/51.03-Agent.md` |
| `specs/41.04-Tools.md` | `specs/51.04-Tools.md` |
| `specs/41.05-Web.md` | `specs/51.05-Web.md` |
| `specs/41.06-Contract.md` | `specs/51.06-Contract.md` |

**编号区间引用替换：**

| 旧引用 | 新引用 |
|---|---|
| `10-39`（生产对象区间） | `20-49` |
| `11-39`（具体生产对象） | `21-49` |
| `23-39`（预留生产对象） | `33-49` |
| `40-69`（行动模型区间） | `50-79` |
| `41-69`（具体行动规范） | `51-79` |
| `51-69`（预留行动） | `61-79` |

**系列和章节引用替换：**

| 旧引用 | 新引用 |
|---|---|
| `04 系列` | `11 系列` |
| `05 系列` | `12 系列` |
| `06 §` | `13 §` |
| `07 §` | `14 §` |
| `06-LDVH生产对象基础规范` | `13-LDVH生产对象基础规范` |
| `07-LDVH行动模型基础规范` | `14-LDVH行动模型基础规范` |
| `04-LDVH-AI协作规范` | `11-LDVH-AI协作规范` |
| `05-LDVH工具基础规范` | `12-LDVH工具基础规范` |
| `04.01` | `11.01` |
| `04.02` | `11.02` |
| `04.03` | `11.03` |
| `05.01` | `12.01` |
| `05.02` | `12.02` |
| `10-39 Harness 生产对象规范` | `20-49 LDVH 生产对象规范` |
| `40-69 Harness 行动模型规范` | `50-79 LDVH 行动模型规范` |

**特殊替换（04.01-Rules机制规范.md 中的规范层树形结构）：**

| 旧内容 | 新内容 |
|---|---|
| `01-07 基础规范` | `01-03 基础规范` + `10-19 核心基础规范` |
| `10-39 生产对象规范` | `20-49 生产对象规范` |
| `40-69 行动模型规范` | `50-79 行动模型规范` |

**特殊替换（事实源边界与承载规范中的典型事实归属表）：**

该表中 `specs/03` → `specs/10`、`specs/04` → `specs/11`、`specs/05` → `specs/12`、`specs/06` → `specs/13`、`specs/07` → `specs/14`、`specs/10-39` → `specs/20-49`、`specs/40-69` → `specs/50-79`。

#### Scenario: 引用更新完整

- **WHEN** 所有迁移文档的内部引用已按替换规则更新
- **THEN** 迁移文档中不存在旧编号引用，所有引用指向 specs/ 中正确的文件路径和编号区间

### Requirement: 现有 specs 文档更新

系统 SHALL 更新现有 specs 文档（00、01、02、03）中的引用：

1. 00 总纲：移除 `specs/10-事实源边界与承载规范.md`、`specs/11-LDVH-AI协作规范.md`、`specs/12-LDVH工具基础规范.md`、`specs/13-LDVH生产对象基础规范.md`、`specs/14-LDVH行动模型基础规范.md` 引用前的"规划中的"标记；更新待补齐事项
2. 01 目录说明：移除"规划中的"标记
3. 02 术语规范：无需变更（已使用正确编号）
4. 03 文档规范：移除"规划中的"标记

#### Scenario: 现有文档引用一致

- **WHEN** 现有 specs 文档中的"规划中的"标记已移除
- **THEN** 00-03 中对 10-14、20、50 的引用不再标注"规划中的"

### Requirement: L0/L1 规则文件更新

系统 SHALL 更新规则文件中的旧编号引用：

1. L0 工作区规则（`.trae/rules/ldvh-l0-rules.md`）：`ld-vibe-harness/specs/41-multi-role-thinking-多角色思考.md` → `ld-vibe-harness/specs/51-multi-role-thinking-多角色思考.md`；`ld-vibe-harness/specs/41-Contract.md` → `ld-vibe-harness/specs/51.06-Contract.md`；压缩保护行 `ldvh-多角色思考见41` → `ldvh-多角色思考见51`
2. L1 项目规则（`.trae/rules/ldvh-l1-rules.md`）：无需变更（已使用正确编号区间 10-19、20-49、50-79）

#### Scenario: 规则文件引用一致

- **WHEN** L0 规则文件中的旧编号引用已更新
- **THEN** L0 规则文件中不存在对 41 的引用，所有引用指向 51

### Requirement: temp 目录清理

系统 SHALL 在所有文档迁移和引用更新完成后删除 `temp/` 目录。

#### Scenario: temp 目录已清理

- **WHEN** 所有迁移工作完成
- **THEN** `temp/` 目录不再存在
