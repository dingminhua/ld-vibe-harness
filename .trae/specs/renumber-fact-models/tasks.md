# Tasks

- [x] Task 1: 重命名 Task 相关 specs 文件（31 → 27）
  - [x] SubTask 1.1: `git mv specs/31-Task-任务.md specs/27-Task-任务.md`
  - [x] SubTask 1.2: `git mv specs/31.01-Rules.md specs/27.01-Rules.md`
  - [x] SubTask 1.3: `git mv specs/31.02-Skill.md specs/27.02-Skill.md`
  - [x] SubTask 1.4: `git mv specs/31.03-Agent.md specs/27.03-Agent.md`
  - [x] SubTask 1.5: `git mv specs/31.04-Tools.md specs/27.04-Tools.md`
  - [x] SubTask 1.6: `git mv specs/31.05-Web.md specs/27.05-Web.md`
  - [x] SubTask 1.7: `git mv specs/31.06-Contract.md specs/27.06-Contract.md`

- [x] Task 2: 重命名 Evidence 相关 specs 文件（28 → 29）
  - [x] SubTask 2.1: `git mv specs/28-Evidence-验证证据.md specs/29-Evidence-验证证据.md`
  - [x] SubTask 2.2: `git mv specs/28.01-Rules.md specs/29.01-Rules.md`
  - [x] SubTask 2.3: `git mv specs/28.02-Skill.md specs/29.02-Skill.md`
  - [x] SubTask 2.4: `git mv specs/28.03-Agent.md specs/29.03-Agent.md`
  - [x] SubTask 2.5: `git mv specs/28.04-Tools.md specs/29.04-Tools.md`
  - [x] SubTask 2.6: `git mv specs/28.05-Web.md specs/29.05-Web.md`
  - [x] SubTask 2.7: `git mv specs/28.06-Contract.md specs/29.06-Contract.md`

- [x] Task 3: 更新 Task 主规范和子文档内部引用（31 → 27）
  - [x] SubTask 3.1: 更新 `specs/27-Task-任务.md` 中所有 `31` 引用为 `27`
  - [x] SubTask 3.2: 更新 `specs/27.01-Rules.md` 中 `31` 引用为 `27`
  - [x] SubTask 3.3: 更新 `specs/27.02-Skill.md` 中 `31` 引用为 `27`
  - [x] SubTask 3.4: 更新 `specs/27.03-Agent.md` 中 `31` 引用为 `27`
  - [x] SubTask 3.5: 更新 `specs/27.04-Tools.md` 中 `31` 引用为 `27`
  - [x] SubTask 3.6: 更新 `specs/27.05-Web.md` 中 `31` 引用为 `27`
  - [x] SubTask 3.7: 更新 `specs/27.06-Contract.md` 中 `31` 引用为 `27`

- [x] Task 4: 更新 Evidence 主规范和子文档内部引用（28 → 29）
  - [x] SubTask 4.1: 更新 `specs/29-Evidence-验证证据.md` 中所有 `28` 引用为 `29`
  - [x] SubTask 4.2: 更新 `specs/29.01-Rules.md` 中 `28` 引用为 `29`
  - [x] SubTask 4.3: 更新 `specs/29.02-Skill.md` 中 `28` 引用为 `29`
  - [x] SubTask 4.4: 更新 `specs/29.03-Agent.md` 中 `28` 引用为 `29`
  - [x] SubTask 4.5: 更新 `specs/29.04-Tools.md` 中 `28` 引用为 `29`
  - [x] SubTask 4.6: 更新 `specs/29.05-Web.md` 中 `28` 引用为 `29`
  - [x] SubTask 4.7: 更新 `specs/29.06-Contract.md` 中 `28` 引用为 `29`

- [x] Task 5: 更新 Task 主规范中对 Evidence 的交叉引用（28 → 29）
  - `specs/27-Task-任务.md` 中引用 `specs/28-Evidence-验证证据.md` 的地方已改为 `specs/29-Evidence-验证证据.md`

- [x] Task 6: 更新索引文档 `specs/20-事实模型集合索引.md`
  - [x] SubTask 6.1: 文档清单表中 27/28/29/31 行的编号、文档名和说明
  - [x] SubTask 6.2: 已落地事实模型表中 Task 和 Evidence 的编号
  - [x] SubTask 6.3: 高优先级待落地事实模型表中 TaskSet 的编号
  - [x] SubTask 6.4: 暂作字段概念表中 Risk 的编号
  - [x] SubTask 6.5: 对象关系表中所有编号引用
  - [x] SubTask 6.6: 删除/降级清单中编号引用
  - [x] SubTask 6.7: 待补齐事项中编号引用

- [x] Task 7: 更新 evals 文档中的交叉引用
  - [x] SubTask 7.1: `specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md` 中 27/28/29/31 引用
  - [x] SubTask 7.2: `specs/evals/14-Gstack照搬进入Trae环境可行性评估.md` 中 28/31 引用
  - [x] SubTask 7.3: `specs/evals/15-LDVH对Trae-Plan与Spec功能的利用评估.md` 中 28/31 引用
  - [x] SubTask 7.4: `specs/evals/16-specs-v2内容价值评估.md` 中 31 引用

- [x] Task 8: 更新 ldvh-base README 和 Skill 文档
  - [x] SubTask 8.1: `ldvh-base/evidence/README.md` 中 28 → 29
  - [x] SubTask 8.2: `ldvh-base/tasks/README.md` 中 31 → 27
  - [x] SubTask 8.3: `.trae/skills/ldvh-close/SKILL.md` 中 31 → 27、28 → 29
  - [x] SubTask 8.4: `.trae/skills/ldvh-intake/SKILL.md` 中 31 → 27

- [x] Task 9: 运行文档检查验证
  - [x] SubTask 9.1: `python3 tools/check_03_specs_doc_standard.py` — 未引入新错误
  - [x] SubTask 9.2: `python3 tools/check_03_01_specs_docs.py` — 通过
  - [x] SubTask 9.3: `python3 tools/check_03_specs_references.py` — 通过

# Task Dependencies

- Task 1 和 Task 2 可并行执行（文件重命名）
- Task 3 和 Task 4 依赖 Task 1 和 Task 2 完成后才能编辑文件内容
- Task 5 依赖 Task 3 和 Task 4（需要知道新文件路径）
- Task 6、7、8 依赖 Task 1-5 完成后才能更新交叉引用
- Task 9 依赖所有其他 Task 完成后才能验证
